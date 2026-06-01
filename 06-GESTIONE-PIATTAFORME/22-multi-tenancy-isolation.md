---
corso: "Gestione Piattaforme e DevOps"
fase: "7 — Architetture Avanzate"
modulo: 22
titolo: "Multi-Tenancy Isolation"
versione: "Kubernetes 1.30; vCluster 0.20; OPA/Gatekeeper v3; PostgreSQL 16 RLS; Terraform 1.x"
livello: "Avanzato"
prerequisiti: ["05-kubernetes", "13-sicurezza-piattaforme", "11-database-management"]
obiettivi:
  - "Confrontare i modelli silo, pool e bridge per architetture multi-tenant"
  - "Implementare tenant isolation in Kubernetes con namespace, NetworkPolicy e vCluster"
  - "Configurare Row-Level Security in PostgreSQL per isolamento dati a livello di riga"
  - "Progettare tenant onboarding automatizzato con Terraform e IAM session tag"
  - "Prevenire noisy neighbor e blast radius con ResourceQuota, fair queuing e cell-based architecture"
tag: [multi-tenancy, isolation, vcluster, rls, noisy-neighbor, cell-architecture, opa, gatekeeper, saas]
---

# Multi-Tenancy Isolation

> **Modulo 22** · **Aggiornamento:** 2026-05-24
> **Riferimenti:** AWS Well-Architected SaaS Lens; Kubernetes Multi-Tenancy SIG; PostgreSQL RLS; OPA/Gatekeeper v3; Terraform 1.x; NIST SP 800-53 AC-4.

> **Obiettivi di apprendimento**
>
> Al completamento di questo modulo sarai in grado di:
> 1. Confrontare i modelli silo, pool e bridge per architetture multi-tenant.
> 2. Implementare tenant isolation in Kubernetes con namespace, NetworkPolicy e vCluster.
> 3. Configurare Row-Level Security in PostgreSQL per isolamento dati a livello di riga.
> 4. Progettare tenant onboarding automatizzato con Terraform e IAM session tag.
> 5. Prevenire noisy neighbor e blast radius con ResourceQuota, fair queuing e cell-based architecture.

---

## Sommario

1. [Idee guida](#idee-guida)
2. [Multi-tenancy architecture patterns](#multi-tenancy-architecture-patterns)
3. [Isolation levels taxonomy](#isolation-levels-taxonomy)
4. [Tenant isolation in AWS](#tenant-isolation-in-aws)
5. [Tenant isolation in Kubernetes](#tenant-isolation-in-kubernetes)
6. [Database isolation strategies](#database-isolation-strategies)
7. [Noisy neighbor prevention](#noisy-neighbor-prevention)
8. [Tenant routing and identification](#tenant-routing-and-identification)
9. [Blast radius containment](#blast-radius-containment)
10. [Cross-tenant security testing](#cross-tenant-security-testing)
11. [Compliance and data residency per tenant](#compliance-and-data-residency-per-tenant)
12. [Cost allocation per tenant](#cost-allocation-per-tenant)
13. [Tenant lifecycle management](#tenant-lifecycle-management)
14. [Kubernetes multi-tenancy avanzata — vCluster, Capsule, Loft](#kubernetes-multi-tenancy-avanzata--vcluster-capsule-loft)
15. [Database multi-tenancy patterns avanzati](#database-multi-tenancy-patterns-avanzati)
16. [Network isolation avanzata](#network-isolation-avanzata)
17. [Resource quotas e limit ranges — strategie avanzate](#resource-quotas-e-limit-ranges--strategie-avanzate)
18. [Tenant onboarding automation](#tenant-onboarding-automation)
19. [Noisy neighbor prevention — strategie avanzate](#noisy-neighbor-prevention--strategie-avanzate)
20. [Data isolation e compliance GDPR per-tenant](#data-isolation-e-compliance-gdpr-per-tenant)
21. [Cost allocation per tenant — strategie avanzate](#cost-allocation-per-tenant--strategie-avanzate)
22. [Monitoring e observability per tenant](#monitoring-e-observability-per-tenant)
23. [Multi-tenant CI/CD](#multi-tenant-cicd)
24. [Security boundaries e blast radius](#security-boundaries-e-blast-radius)
25. [Multi-tenant SaaS architecture patterns](#multi-tenant-saas-architecture-patterns)
26. [Modelli](#modelli)
27. [Esercizi](#esercizi)
28. [Troubleshooting — 20 problemi](#troubleshooting--20-problemi)
29. [FAQ — 20 domande e risposte](#faq--20-domande-e-risposte)
30. [Letture](#letture)
31. [Glossario](#glossario)

---

## Idee guida

1. **Soft multi-tenancy (namespace + RBAC + NetworkPolicy) vs hard (separate cluster).**
2. **Resource quota per namespace mandatory.** Without quotas, noisy-neighbor effects are inevitable.
3. **NetworkPolicy default-DENY between namespaces.**
4. **Sandbox runtime (gVisor, Kata) for strong isolation.**
5. **Virtual cluster (vCluster) or Kamaji for control plane separation.**
6. **Isolation is a spectrum, not a binary.** Every architecture trades cost for blast-radius reduction; the right point depends on regulatory, contractual, and risk requirements.
7. **Tenant identity must be unforgeable.** Derive tenant context from cryptographic claims (JWT, mTLS), never from client-supplied headers alone.
8. **Test isolation the way attackers break it.** Penetration tests must include cross-tenant access attempts, not just functional correctness.

---

## Multi-tenancy architecture patterns

Three canonical patterns dominate SaaS architecture. Most production systems combine elements from more than one.

### Pattern 1 — Silo (dedicated resources per tenant)

```
┌─────────────────────────────────────────────────┐
│                  SILO MODEL                     │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Tenant A │  │ Tenant B │  │ Tenant C │      │
│  │          │  │          │  │          │      │
│  │ Compute  │  │ Compute  │  │ Compute  │      │
│  │ Database │  │ Database │  │ Database │      │
│  │ Network  │  │ Network  │  │ Network  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                 │
│  Shared: management plane, billing, monitoring  │
└─────────────────────────────────────────────────┘
```

**Characteristics:**

- Each tenant gets dedicated compute, storage, and network resources.
- Blast radius is minimal — one tenant's failure cannot impact another.
- Cost scales linearly with tenant count; significant per-tenant fixed overhead.
- Onboarding requires provisioning a full stack (slower).
- Compliance isolation is strong — data residency trivial to satisfy.

**When to use:**

- Regulated industries (healthcare, finance, government).
- Enterprise customers with contractual isolation requirements.
- Workloads where a breach in one tenant must never affect others.
- Customers willing to pay a premium for dedicated infrastructure.

**Terraform — silo account per tenant via AWS Organizations:**

```hcl
# modules/tenant-account/main.tf

variable "tenant_id" {
  type        = string
  description = "Unique tenant identifier (e.g., acme-corp)"
}

variable "tenant_email" {
  type        = string
  description = "Root email for the tenant's AWS account"
}

variable "tenant_ou_id" {
  type        = string
  description = "Organizational Unit to place the account in"
}

resource "aws_organizations_account" "tenant" {
  name      = "tenant-${var.tenant_id}"
  email     = var.tenant_email
  parent_id = var.tenant_ou_id

  role_name = "TenantAdminRole"

  tags = {
    TenantId    = var.tenant_id
    Environment = "production"
    ManagedBy   = "terraform"
    CostCenter  = "tenant-${var.tenant_id}"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_organizations_policy_attachment" "tenant_scp" {
  policy_id = var.tenant_scp_id
  target_id = aws_organizations_account.tenant.id
}

output "account_id" {
  value = aws_organizations_account.tenant.id
}
```

### Pattern 2 — Pool (shared resources, logical separation)

```
┌──────────────────────────────────────────────┐
│                 POOL MODEL                   │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │         Shared Compute Cluster          │ │
│  │                                         │ │
│  │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐  │ │
│  │  │ A │ │ B │ │ C │ │ A │ │ D │ │ B │  │ │
│  │  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘  │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │        Shared Database (RLS)            │ │
│  │  tenant_id column on every table        │ │
│  └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

**Characteristics:**

- All tenants share compute, database, and network resources.
- Tenant separation is enforced through application-level logic (tenant_id columns, RLS).
- Cost-efficient — infrastructure cost is amortized across all tenants.
- Onboarding is fast — create a row, not a stack.
- Blast radius is large — a bug in tenant filtering leaks data across tenants.
- Noisy-neighbor risk is highest.

**When to use:**

- High-volume, low-margin SaaS (thousands of small tenants).
- Self-service onboarding with instant provisioning.
- Workloads where regulatory isolation is not required.
- Early-stage startups optimizing for speed and cost.

### Pattern 3 — Bridge (tiered isolation)

```
┌──────────────────────────────────────────────────────┐
│                   BRIDGE MODEL                       │
│                                                      │
│  Tier 1 (Enterprise)     Tier 2 (Pro)   Tier 3 (Free)│
│  ┌──────────┐           ┌──────────┐   ┌──────────┐ │
│  │ Dedicated │           │ Shared   │   │ Shared   │ │
│  │ Cluster   │           │ Namespace│   │ Namespace│ │
│  │ Dedicated │           │ Shared   │   │ Shared   │ │
│  │ Database  │           │ Schema   │   │ RLS      │ │
│  └──────────┘           └──────────┘   └──────────┘ │
│                                                      │
│  Common: API gateway, identity, billing, monitoring  │
└──────────────────────────────────────────────────────┘
```

**Characteristics:**

- Different tenant tiers receive different isolation levels.
- Premium tenants get silo-like resources; free/basic tenants share pool resources.
- Balances cost efficiency with isolation guarantees.
- Requires routing logic that is tier-aware.
- Most common pattern in mature SaaS products.

**When to use:**

- SaaS with differentiated pricing tiers.
- Products serving both enterprise and SMB customers.
- Gradual migration from pool to silo as customers upgrade.

### Comparison matrix

| Dimension | Silo | Pool | Bridge |
|---|---|---|---|
| Blast radius | Minimal | Large | Tier-dependent |
| Cost per tenant | High | Low | Medium |
| Onboarding speed | Minutes–hours | Seconds | Tier-dependent |
| Noisy neighbor risk | None | High | Tier-dependent |
| Compliance ease | Easy | Hard | Tier-dependent |
| Operational complexity | High (many stacks) | Low (one stack) | Medium |
| Data residency | Trivial | Complex | Tier-dependent |
| Customization | Full | Limited | Tier-dependent |

---

## Isolation levels taxonomy

Isolation exists at multiple layers. Production systems stack these for defense in depth.

### Level 1 — Account isolation

Strongest boundary available in cloud providers. Each tenant gets its own cloud account.

```
AWS Organization
├── Management Account
├── Security Account (centralized logs, GuardDuty)
├── OU: Production Tenants
│   ├── Account: tenant-acme-corp (111111111111)
│   ├── Account: tenant-globex    (222222222222)
│   └── Account: tenant-initech  (333333333333)
└── OU: Shared Services
    ├── Account: networking       (444444444444)
    └── Account: monitoring       (555555555555)
```

Account boundaries enforce:
- IAM policy isolation (policies cannot reference cross-account resources by default).
- Service quotas are per-account (natural noisy-neighbor protection).
- CloudTrail and billing are per-account.
- VPC networks are per-account (no shared default network).

### Level 2 — VPC isolation

Tenants share an account but get dedicated VPCs with no peering.

```hcl
# Dedicated VPC per tenant within a shared account

resource "aws_vpc" "tenant" {
  cidr_block           = var.tenant_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name     = "vpc-${var.tenant_id}"
    TenantId = var.tenant_id
  }
}

# No VPC peering to other tenant VPCs — isolation by default
# Transit Gateway attachment only to shared-services VPC

resource "aws_ec2_transit_gateway_vpc_attachment" "shared_services" {
  transit_gateway_id = var.transit_gateway_id
  vpc_id             = aws_vpc.tenant.id
  subnet_ids         = aws_subnet.tenant_private[*].id

  tags = {
    Name     = "tgw-attach-${var.tenant_id}"
    TenantId = var.tenant_id
  }
}

# Transit Gateway route table prevents tenant-to-tenant routing
resource "aws_ec2_transit_gateway_route_table_association" "tenant" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.shared_services.id
  transit_gateway_route_table_id = var.tenant_route_table_id
}
```

### Level 3 — Namespace isolation (Kubernetes)

Tenants share a cluster but are isolated by namespace, RBAC, NetworkPolicy, and ResourceQuota.

### Level 4 — Process isolation

Tenants share a host but run in separate processes with distinct UIDs, cgroups, and seccomp profiles.

### Level 5 — Data isolation

Tenants share compute but data is separated through database-level mechanisms (schemas, RLS, encryption).

### Choosing isolation levels

```
┌─────────────────────────────────────────────────┐
│  DECISION TREE: ISOLATION LEVEL                 │
│                                                 │
│  Regulatory mandate for separate infra?         │
│   ├── YES → Account isolation (Silo)            │
│   └── NO                                        │
│       Contractual SLA for dedicated compute?     │
│        ├── YES → VPC isolation                   │
│        └── NO                                    │
│            Need network-level separation?        │
│             ├── YES → Namespace + NetworkPolicy  │
│             └── NO                               │
│                 Need data separation?             │
│                  ├── YES → Schema/RLS isolation  │
│                  └── NO → Shared pool (RLS min)  │
└─────────────────────────────────────────────────┘
```

---

## Tenant isolation in AWS

### AWS Organizations structure

```hcl
# Root organization with tenant OUs

resource "aws_organizations_organization" "root" {
  aws_service_access_principals = [
    "sso.amazonaws.com",
    "cloudtrail.amazonaws.com",
    "config.amazonaws.com",
    "guardduty.amazonaws.com",
  ]

  feature_set = "ALL"

  enabled_policy_types = [
    "SERVICE_CONTROL_POLICY",
    "TAG_POLICY",
  ]
}

resource "aws_organizations_organizational_unit" "production_tenants" {
  name      = "ProductionTenants"
  parent_id = aws_organizations_organization.root.roots[0].id
}

resource "aws_organizations_organizational_unit" "enterprise_tenants" {
  name      = "EnterpriseTenants"
  parent_id = aws_organizations_organizational_unit.production_tenants.id
}

resource "aws_organizations_organizational_unit" "standard_tenants" {
  name      = "StandardTenants"
  parent_id = aws_organizations_organizational_unit.production_tenants.id
}
```

### Service Control Policies (SCPs)

SCPs set the maximum permissions boundary for an entire account. They are the strongest guardrail in AWS.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRegionOutsideAllowed",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "eu-west-1",
            "eu-central-1"
          ]
        },
        "ArnNotLike": {
          "aws:PrincipalARN": "arn:aws:iam::*:role/OrganizationAdmin"
        }
      }
    },
    {
      "Sid": "DenyLeaveOrganization",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    },
    {
      "Sid": "DenyCloudTrailModification",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail",
        "cloudtrail:UpdateTrail"
      ],
      "Resource": "*",
      "Condition": {
        "ArnNotLike": {
          "aws:PrincipalARN": "arn:aws:iam::*:role/SecurityAdmin"
        }
      }
    },
    {
      "Sid": "DenyS3PublicAccess",
      "Effect": "Deny",
      "Action": [
        "s3:PutBucketPublicAccessBlock",
        "s3:PutAccountPublicAccessBlock"
      ],
      "Resource": "*",
      "Condition": {
        "ArnNotLike": {
          "aws:PrincipalARN": "arn:aws:iam::*:role/SecurityAdmin"
        }
      }
    },
    {
      "Sid": "RequireTenantTagging",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "rds:CreateDBInstance",
        "s3:CreateBucket",
        "lambda:CreateFunction"
      ],
      "Resource": "*",
      "Condition": {
        "Null": {
          "aws:RequestTag/TenantId": "true"
        }
      }
    }
  ]
}
```

### IAM permissions boundaries

Permissions boundaries cap the maximum permissions a role can have, even if the role's policy grants more.

```hcl
# Permissions boundary for tenant-scoped roles

resource "aws_iam_policy" "tenant_boundary" {
  name        = "TenantPermissionBoundary-${var.tenant_id}"
  description = "Maximum permissions for tenant ${var.tenant_id}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowOwnResources"
        Effect = "Allow"
        Action = [
          "s3:*",
          "dynamodb:*",
          "sqs:*",
          "sns:*",
          "lambda:*",
          "logs:*",
        ]
        Resource = "arn:aws:*:*:${data.aws_caller_identity.current.account_id}:*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/TenantId" = var.tenant_id
          }
        }
      },
      {
        Sid      = "DenyAccessToOtherTenants"
        Effect   = "Deny"
        Action   = "*"
        Resource = "*"
        Condition = {
          StringNotEquals = {
            "aws:ResourceTag/TenantId" = var.tenant_id
          }
          Null = {
            "aws:ResourceTag/TenantId" = "false"
          }
        }
      },
      {
        Sid    = "DenyDangerousActions"
        Effect = "Deny"
        Action = [
          "iam:CreateUser",
          "iam:CreateRole",
          "iam:DeleteRole",
          "organizations:*",
          "account:*",
        ]
        Resource = "*"
      }
    ]
  })
}

# Apply boundary to all tenant roles
resource "aws_iam_role" "tenant_app" {
  name                 = "TenantApp-${var.tenant_id}"
  permissions_boundary = aws_iam_policy.tenant_boundary.arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:RequestTag/TenantId" = var.tenant_id
          }
        }
      }
    ]
  })

  tags = {
    TenantId = var.tenant_id
  }
}
```

### Dynamic policy generation with session tags

```python
# Lambda: generate scoped credentials for tenant context

import boto3
import json

sts = boto3.client("sts")

def get_tenant_credentials(tenant_id: str, session_name: str) -> dict:
    """
    Assume a role with session tags that scope all API calls
    to a specific tenant's resources.
    """
    response = sts.assume_role(
        RoleArn="arn:aws:iam::123456789012:role/TenantScopedRole",
        RoleSessionName=session_name,
        Tags=[
            {"Key": "TenantId", "Value": tenant_id},
            {"Key": "SessionOrigin", "Value": "tenant-api"},
        ],
        TransitiveTagKeys=["TenantId"],
        DurationSeconds=3600,
    )

    return {
        "access_key": response["Credentials"]["AccessKeyId"],
        "secret_key": response["Credentials"]["SecretAccessKey"],
        "session_token": response["Credentials"]["SessionToken"],
        "expiration": response["Credentials"]["Expiration"].isoformat(),
    }
```

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ScopeToDynamoDBTenantData",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/AppData",
      "Condition": {
        "ForAllValues:StringEquals": {
          "dynamodb:LeadingKeys": ["${aws:PrincipalTag/TenantId}"]
        }
      }
    }
  ]
}
```

---

## Tenant isolation in Kubernetes

### Namespace per tenant

The most common Kubernetes multi-tenancy pattern. Each tenant gets a dedicated namespace with RBAC, NetworkPolicy, ResourceQuota, and LimitRange.

```yaml
# namespace.yaml — tenant namespace with labels
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-acme
  labels:
    tenant: acme
    tier: enterprise
    cost-center: acme-corp
  annotations:
    scheduler.alpha.kubernetes.io/node-selector: "tenant-pool=shared"
```

### RBAC per tenant

```yaml
# rbac.yaml — tenant-scoped roles
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: tenant-acme
  name: tenant-developer
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps", "secrets", "persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets", "statefulsets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["batch"]
    resources: ["jobs", "cronjobs"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  # Deny: no namespace-level resources, no cluster-scoped resources
  # Deny: no access to nodes, persistent volumes, cluster roles

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: tenant-acme
  name: tenant-developer-binding
subjects:
  - kind: Group
    name: "tenant-acme-devs"
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: tenant-developer
  apiGroup: rbac.authorization.k8s.io
```

### Network policies — default deny + selective allow

```yaml
# network-policy-deny-all.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: tenant-acme
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress

---
# network-policy-allow-internal.yaml
# Allow pods within the same tenant namespace to communicate
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: tenant-acme
  name: allow-same-namespace
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector: {}
  egress:
    - to:
        - podSelector: {}

---
# network-policy-allow-dns.yaml
# Allow DNS resolution (required for service discovery)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: tenant-acme
  name: allow-dns
spec:
  podSelector: {}
  policyTypes:
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

---
# network-policy-allow-ingress.yaml
# Allow traffic from the ingress controller namespace only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  namespace: tenant-acme
  name: allow-ingress-controller
spec:
  podSelector:
    matchLabels:
      app: tenant-acme-api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-system
      ports:
        - protocol: TCP
          port: 8080
```

### Resource quotas

```yaml
# resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  namespace: tenant-acme
  name: tenant-quota
spec:
  hard:
    requests.cpu: "8"
    requests.memory: "16Gi"
    limits.cpu: "16"
    limits.memory: "32Gi"
    pods: "50"
    services: "10"
    services.loadbalancers: "2"
    persistentvolumeclaims: "10"
    requests.storage: "100Gi"
    configmaps: "20"
    secrets: "20"
    count/deployments.apps: "20"
    count/statefulsets.apps: "5"
    count/jobs.batch: "10"
    count/cronjobs.batch: "5"

---
# limit-range.yaml — defaults for pods without explicit resource specs
apiVersion: v1
kind: LimitRange
metadata:
  namespace: tenant-acme
  name: tenant-limits
spec:
  limits:
    - type: Container
      default:
        cpu: "500m"
        memory: "512Mi"
      defaultRequest:
        cpu: "100m"
        memory: "128Mi"
      max:
        cpu: "4"
        memory: "8Gi"
      min:
        cpu: "50m"
        memory: "64Mi"
    - type: PersistentVolumeClaim
      max:
        storage: "50Gi"
      min:
        storage: "1Gi"
```

### OPA/Gatekeeper policies

```yaml
# constraint-template: require tenant label
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredtenantlabel
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredTenantLabel
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labelKey:
              type: string
              description: "The label key that must be present"
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredtenantlabel

        violation[{"msg": msg}] {
          not input.review.object.metadata.labels[input.parameters.labelKey]
          msg := sprintf("Missing required label: %v", [input.parameters.labelKey])
        }

---
# constraint: enforce tenant label on all pods
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredTenantLabel
metadata:
  name: require-tenant-label
spec:
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
      - ingress-system
      - monitoring
  parameters:
    labelKey: tenant

---
# constraint-template: prevent cross-namespace references
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblockexternalnameservice
spec:
  crd:
    spec:
      names:
        kind: K8sBlockExternalNameService
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sblockexternalnameservice

        violation[{"msg": msg}] {
          input.review.object.kind == "Service"
          input.review.object.spec.type == "ExternalName"
          msg := "ExternalName services are blocked in tenant namespaces to prevent cross-tenant DNS aliasing"
        }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockExternalNameService
metadata:
  name: block-externalname
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Service"]
    excludedNamespaces:
      - kube-system

---
# constraint-template: restrict image registries per tenant
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sallowedregistries
spec:
  crd:
    spec:
      names:
        kind: K8sAllowedRegistries
      validation:
        openAPIV3Schema:
          type: object
          properties:
            registries:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sallowedregistries

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not startswith_any(container.image, input.parameters.registries)
          msg := sprintf("Image %v is not from an allowed registry. Allowed: %v", [container.image, input.parameters.registries])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.initContainers[_]
          not startswith_any(container.image, input.parameters.registries)
          msg := sprintf("Init container image %v is not from an allowed registry", [container.image])
        }

        startswith_any(str, prefixes) {
          startswith(str, prefixes[_])
        }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRegistries
metadata:
  name: tenant-acme-registries
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces:
      - tenant-acme
  parameters:
    registries:
      - "123456789012.dkr.ecr.eu-west-1.amazonaws.com/acme/"
      - "docker.io/library/"
```

### Pod Security Standards

```yaml
# Enforce restricted pod security standard per tenant namespace
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-acme
  labels:
    tenant: acme
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Sandbox runtimes for strong isolation

```yaml
# RuntimeClass for gVisor
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
scheduling:
  nodeSelector:
    runtime: gvisor

---
# RuntimeClass for Kata Containers
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata-qemu
scheduling:
  nodeSelector:
    runtime: kata
overhead:
  podFixed:
    memory: "160Mi"
    cpu: "250m"

---
# Deploy tenant workload with gVisor runtime
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: tenant-acme
  name: api-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
      tenant: acme
  template:
    metadata:
      labels:
        app: api-server
        tenant: acme
    spec:
      runtimeClassName: gvisor
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: api
          image: 123456789012.dkr.ecr.eu-west-1.amazonaws.com/acme/api:v2.1.0
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
```

### Virtual clusters (vCluster)

```yaml
# vcluster.yaml — dedicated virtual cluster per tenant
apiVersion: v1
kind: Namespace
metadata:
  name: vcluster-tenant-acme
  labels:
    tenant: acme

---
# Helm values for vCluster
# helm install tenant-acme vcluster/vcluster -n vcluster-tenant-acme -f values.yaml
#
# values.yaml:
# syncer:
#   extraArgs:
#     - --tls-san=tenant-acme.saas.example.com
# sync:
#   ingresses:
#     enabled: true
#   persistentvolumes:
#     enabled: true
#   storageclasses:
#     enabled: false
# isolation:
#   enabled: true
#   namespace: null
#   podSecurityStandard: restricted
#   resourceQuota:
#     enabled: true
#     quota:
#       requests.cpu: "10"
#       requests.memory: "20Gi"
#       limits.cpu: "20"
#       limits.memory: "40Gi"
#       pods: "100"
#   limitRange:
#     enabled: true
#     default:
#       cpu: "500m"
#       memory: "512Mi"
#     defaultRequest:
#       cpu: "100m"
#       memory: "128Mi"
#   networkPolicy:
#     enabled: true
```

---

## Database isolation strategies

### Strategy 1 — Database per tenant

Each tenant gets a dedicated database instance or cluster.

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │ PostgreSQL   │  │ PostgreSQL   │
│ tenant_acme  │  │ tenant_globex│  │ tenant_init  │
│              │  │              │  │              │
│ All tables   │  │ All tables   │  │ All tables   │
│ dedicated    │  │ dedicated    │  │ dedicated    │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Terraform — RDS per tenant:**

```hcl
resource "aws_db_instance" "tenant" {
  identifier     = "db-${var.tenant_id}"
  engine         = "postgres"
  engine_version = "16.2"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true
  kms_key_id            = var.tenant_kms_key_arn

  db_name  = "app"
  username = "tenant_admin"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.tenant_db.id]
  db_subnet_group_name   = aws_db_subnet_group.tenant.name

  backup_retention_period = 7
  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "db-${var.tenant_id}-final"

  performance_insights_enabled = true

  tags = {
    TenantId   = var.tenant_id
    CostCenter = "tenant-${var.tenant_id}"
  }
}
```

**Pros:** Strongest data isolation. Easy backup/restore per tenant. No cross-tenant query risk.
**Cons:** High cost. Connection management at scale is complex. Schema migrations must be applied N times.

### Strategy 2 — Schema per tenant

Shared database instance, but each tenant gets a dedicated schema (PostgreSQL) or database within the instance (MySQL).

```sql
-- Create schema per tenant
CREATE SCHEMA tenant_acme AUTHORIZATION app_user;
CREATE SCHEMA tenant_globex AUTHORIZATION app_user;

-- Each schema has its own copy of all tables
CREATE TABLE tenant_acme.orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id  BIGINT NOT NULL,
    quantity    INT NOT NULL CHECK (quantity > 0),
    total_cents BIGINT NOT NULL CHECK (total_cents >= 0),
    status      TEXT NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tenant_globex.orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id  BIGINT NOT NULL,
    quantity    INT NOT NULL CHECK (quantity > 0),
    total_cents BIGINT NOT NULL CHECK (total_cents >= 0),
    status      TEXT NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Set search_path at connection time based on tenant context
-- Application sets: SET search_path TO tenant_acme, public;

-- Restrict cross-schema access
REVOKE ALL ON SCHEMA tenant_acme FROM PUBLIC;
REVOKE ALL ON SCHEMA tenant_globex FROM PUBLIC;
GRANT USAGE ON SCHEMA tenant_acme TO role_tenant_acme;
GRANT USAGE ON SCHEMA tenant_globex TO role_tenant_globex;
```

**Connection routing:**

```python
# middleware.py — set schema based on tenant context
import psycopg

def get_tenant_connection(tenant_id: str) -> psycopg.Connection:
    """Return a connection with search_path set to the tenant's schema."""
    conn = psycopg.connect(conninfo=DATABASE_URL)

    # Use parameterized identifier to prevent SQL injection
    # psycopg3 supports sql.Identifier for safe schema names
    from psycopg import sql
    conn.execute(
        sql.SQL("SET search_path TO {schema}, public").format(
            schema=sql.Identifier(f"tenant_{tenant_id}")
        )
    )
    return conn
```

**Pros:** Good isolation with shared infrastructure cost. Tenant data is physically separate.
**Cons:** Schema migrations must target all schemas. Connection pools may need per-schema routing.

### Strategy 3 — Row-Level Security (RLS)

Shared database, shared tables, tenant_id column on every row. PostgreSQL RLS policies enforce access.

```sql
-- Enable RLS on all tenant-scoped tables
-- Step 1: Add tenant_id column to every table

CREATE TABLE orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    product_id  BIGINT NOT NULL,
    quantity    INT NOT NULL CHECK (quantity > 0),
    total_cents BIGINT NOT NULL CHECK (total_cents >= 0),
    status      TEXT NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Step 2: Create index on tenant_id (critical for performance)
CREATE INDEX idx_orders_tenant_id ON orders (tenant_id);

-- Composite index for common queries
CREATE INDEX idx_orders_tenant_status ON orders (tenant_id, status);

-- Step 3: Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Force RLS even for table owners (important!)
ALTER TABLE orders FORCE ROW LEVEL SECURITY;

-- Step 4: Create RLS policies
CREATE POLICY tenant_isolation ON orders
    USING (tenant_id = current_setting('app.current_tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

-- Step 5: Create a function to set tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', p_tenant_id, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 6: Apply to all tenant tables
-- Repeat for: products, users, invoices, audit_logs, etc.

CREATE TABLE products (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    name        TEXT NOT NULL,
    price_cents BIGINT NOT NULL CHECK (price_cents >= 0),
    active      BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON products
    USING (tenant_id = current_setting('app.current_tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

CREATE INDEX idx_products_tenant_id ON products (tenant_id);
```

**Application-level RLS integration:**

```python
# rls_middleware.py — set tenant context on every request

from contextlib import contextmanager
from typing import Generator
import psycopg
from psycopg import sql

DATABASE_URL = "postgresql://app_user:***@db:5432/saas"

@contextmanager
def tenant_connection(tenant_id: str) -> Generator[psycopg.Connection, None, None]:
    """
    Context manager that ensures every query within runs
    scoped to the specified tenant via RLS.
    """
    if not tenant_id or not tenant_id.isalnum():
        raise ValueError(f"Invalid tenant_id: {tenant_id}")

    conn = psycopg.connect(conninfo=DATABASE_URL)
    try:
        conn.execute(
            "SELECT set_tenant_context(%s)",
            (tenant_id,)
        )
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        # Reset tenant context before returning to pool
        conn.execute("RESET app.current_tenant_id")
        conn.close()

# Usage in request handler
def get_orders(tenant_id: str) -> list[dict]:
    with tenant_connection(tenant_id) as conn:
        # RLS automatically filters — no WHERE tenant_id needed
        rows = conn.execute("SELECT id, status, total_cents FROM orders").fetchall()
        return [{"id": r[0], "status": r[1], "total": r[2]} for r in rows]
```

**Verifying RLS works:**

```sql
-- Test: set tenant context and query
SET app.current_tenant_id = 'acme';
SELECT count(*) FROM orders;  -- Only acme's orders

SET app.current_tenant_id = 'globex';
SELECT count(*) FROM orders;  -- Only globex's orders

-- Test: attempt to insert for wrong tenant
SET app.current_tenant_id = 'acme';
INSERT INTO orders (tenant_id, product_id, quantity, total_cents)
VALUES ('globex', 1, 1, 1000);
-- ERROR: new row violates row-level security policy

-- Test: superuser bypass check
-- FORCE ROW LEVEL SECURITY ensures even owner is filtered
SET ROLE app_user;
SET app.current_tenant_id = 'acme';
SELECT count(*) FROM orders;  -- Only acme's
```

### Comparison of database strategies

| Dimension | Database per tenant | Schema per tenant | RLS (shared table) |
|---|---|---|---|
| Data isolation | Physical | Logical | Row-level |
| Cross-tenant risk | None | Low | Medium (policy bugs) |
| Cost | High | Medium | Low |
| Max tenants | ~100s | ~1,000s | ~100,000s |
| Migration complexity | N migrations | N migrations | 1 migration |
| Backup granularity | Per tenant | Per tenant (pg_dump -n) | Table-level |
| Query performance | No contention | Minimal contention | Needs tenant_id indexes |
| Connection pooling | N pools | 1 pool + SET search_path | 1 pool + SET config |

---

## Noisy neighbor prevention

Noisy neighbor is the #1 operational problem in pool-model multi-tenancy. One tenant's excessive resource usage degrades all others.

### Resource limits in Kubernetes

```yaml
# Priority classes for tenant tiers
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-enterprise
value: 1000
globalDefault: false
description: "Enterprise tenant — highest priority"

---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-standard
value: 500
globalDefault: false
description: "Standard tenant — normal priority"

---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-free
value: 100
globalDefault: false
description: "Free tenant — lowest priority, preemptible"
preemptionPolicy: PreemptLowerPriority
```

### API rate limiting per tenant

```python
# rate_limiter.py — token bucket per tenant using Redis

import time
import redis

class TenantRateLimiter:
    """
    Token bucket rate limiter scoped per tenant.
    Prevents any single tenant from overwhelming shared API resources.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.tier_limits = {
            "enterprise": {"requests_per_second": 1000, "burst": 2000},
            "pro":        {"requests_per_second": 100,  "burst": 200},
            "free":       {"requests_per_second": 10,   "burst": 20},
        }

    def is_allowed(self, tenant_id: str, tier: str) -> bool:
        """Check if the tenant has remaining capacity."""
        config = self.tier_limits.get(tier, self.tier_limits["free"])
        key = f"ratelimit:{tenant_id}"
        now = time.time()

        pipe = self.redis.pipeline()
        pipe.get(key)
        pipe.ttl(key)
        result = pipe.execute()

        tokens = float(result[0] or config["burst"])
        ttl = int(result[1] or 0)

        if tokens <= 0:
            return False

        # Consume one token
        pipe = self.redis.pipeline()
        pipe.decr(key)
        if ttl <= 0:
            pipe.expire(key, 1)  # Reset every second
        pipe.execute()
        return True

    def get_remaining(self, tenant_id: str, tier: str) -> int:
        """Return remaining tokens for rate limit headers."""
        key = f"ratelimit:{tenant_id}"
        tokens = self.redis.get(key)
        config = self.tier_limits.get(tier, self.tier_limits["free"])
        return int(tokens) if tokens else config["burst"]
```

### Fair queuing for background jobs

```python
# fair_queue.py — weighted fair queue per tenant

import heapq
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class TenantJob:
    virtual_finish_time: float
    tenant_id: str = field(compare=False)
    job: Any = field(compare=False)

class WeightedFairQueue:
    """
    Ensures no single tenant can monopolize background job processing.
    Each tenant has a weight (based on tier); higher weight = more throughput.
    """

    def __init__(self):
        self.heap: list[TenantJob] = []
        self.tenant_virtual_time: dict[str, float] = {}
        self.weights = {
            "enterprise": 10,
            "pro": 5,
            "free": 1,
        }

    def enqueue(self, tenant_id: str, tier: str, job: Any) -> None:
        weight = self.weights.get(tier, 1)
        current_vt = self.tenant_virtual_time.get(tenant_id, 0.0)
        finish_time = current_vt + (1.0 / weight)
        self.tenant_virtual_time[tenant_id] = finish_time
        heapq.heappush(self.heap, TenantJob(finish_time, tenant_id, job))

    def dequeue(self) -> TenantJob | None:
        if not self.heap:
            return None
        return heapq.heappop(self.heap)
```

### Database connection limits per tenant

```sql
-- PostgreSQL: limit connections per tenant role
ALTER ROLE role_tenant_acme CONNECTION LIMIT 20;
ALTER ROLE role_tenant_globex CONNECTION LIMIT 10;
ALTER ROLE role_tenant_free CONNECTION LIMIT 3;

-- Monitor connections per tenant
SELECT usename, count(*)
FROM pg_stat_activity
WHERE state = 'active'
GROUP BY usename
ORDER BY count DESC;
```

### Throttling at the infrastructure layer

```hcl
# AWS API Gateway — per-tenant usage plans

resource "aws_api_gateway_usage_plan" "enterprise" {
  name = "enterprise-tier"

  throttle_settings {
    rate_limit  = 1000  # requests per second
    burst_limit = 2000
  }

  quota_settings {
    limit  = 1000000
    period = "MONTH"
  }

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }
}

resource "aws_api_gateway_usage_plan" "free" {
  name = "free-tier"

  throttle_settings {
    rate_limit  = 10
    burst_limit = 20
  }

  quota_settings {
    limit  = 10000
    period = "MONTH"
  }

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.prod.stage_name
  }
}

resource "aws_api_gateway_api_key" "tenant" {
  name    = "key-${var.tenant_id}"
  enabled = true
}

resource "aws_api_gateway_usage_plan_key" "tenant" {
  key_id        = aws_api_gateway_api_key.tenant.id
  key_type      = "API_KEY"
  usage_plan_id = var.tenant_tier == "enterprise" ? aws_api_gateway_usage_plan.enterprise.id : aws_api_gateway_usage_plan.free.id
}
```

---

## Tenant routing and identification

Every request must be mapped to a tenant early in the processing pipeline. The tenant identifier must be unforgeable.

### Method 1 — Subdomain routing

```
acme.saas.example.com     → tenant_id = acme
globex.saas.example.com   → tenant_id = globex
```

```python
# subdomain_resolver.py

from urllib.parse import urlparse

MAIN_DOMAIN = "saas.example.com"

def resolve_tenant_from_host(host: str) -> str | None:
    """
    Extract tenant identifier from subdomain.
    Returns None if the host is the main domain or invalid.
    """
    host = host.lower().split(":")[0]  # strip port

    if not host.endswith(f".{MAIN_DOMAIN}"):
        return None

    subdomain = host[: -(len(MAIN_DOMAIN) + 1)]

    # Validate: alphanumeric + hyphens, no leading/trailing hyphen
    if not subdomain or not subdomain.replace("-", "").isalnum():
        return None
    if subdomain.startswith("-") or subdomain.endswith("-"):
        return None

    return subdomain
```

**Kubernetes Ingress for subdomain routing:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  namespace: ingress-system
  name: tenant-wildcard
  annotations:
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  rules:
    - host: "*.saas.example.com"
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: tenant-router
                port:
                  number: 80
  tls:
    - hosts:
        - "*.saas.example.com"
      secretName: wildcard-saas-tls
```

### Method 2 — Header-based routing

```
GET /api/orders HTTP/1.1
Host: api.example.com
X-Tenant-Id: acme
Authorization: Bearer <token>
```

**Warning:** The `X-Tenant-Id` header is client-supplied and forgeable. Always validate against the authenticated identity.

```python
# header_resolver.py

def resolve_tenant_from_request(headers: dict, jwt_claims: dict) -> str:
    """
    Resolve tenant from header but VERIFY against JWT claims.
    The header is a hint; the JWT is the authority.
    """
    header_tenant = headers.get("X-Tenant-Id", "").strip().lower()
    jwt_tenant = jwt_claims.get("tenant_id", "").strip().lower()

    if not jwt_tenant:
        raise AuthError("JWT missing tenant_id claim")

    if header_tenant and header_tenant != jwt_tenant:
        raise AuthError(
            f"Tenant mismatch: header={header_tenant} jwt={jwt_tenant}"
        )

    return jwt_tenant
```

### Method 3 — JWT claim extraction

The most secure method. Tenant identity is embedded in the JWT by the identity provider and signed.

```json
{
  "sub": "user-12345",
  "email": "alice@acme.com",
  "tenant_id": "acme",
  "tenant_tier": "enterprise",
  "permissions": ["read:orders", "write:orders"],
  "iss": "https://auth.example.com",
  "aud": "https://api.example.com",
  "iat": 1748000000,
  "exp": 1748003600
}
```

```python
# jwt_tenant_resolver.py

import jwt

PUBLIC_KEY = open("/etc/secrets/jwt-public-key.pem").read()
EXPECTED_ISSUER = "https://auth.example.com"
EXPECTED_AUDIENCE = "https://api.example.com"

def resolve_tenant_from_jwt(token: str) -> dict:
    """
    Decode and validate JWT, extract tenant context.
    Returns dict with tenant_id and tenant_tier.
    """
    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=EXPECTED_ISSUER,
            audience=EXPECTED_AUDIENCE,
        )
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {e}")

    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise AuthError("Missing tenant_id claim in JWT")

    return {
        "tenant_id": tenant_id,
        "tenant_tier": payload.get("tenant_tier", "free"),
        "user_id": payload["sub"],
        "permissions": payload.get("permissions", []),
    }
```

### Method 4 — Path-based routing

```
https://api.example.com/tenants/acme/orders
https://api.example.com/tenants/globex/orders
```

Less common. Works for internal APIs but adds tenant_id to every URL path, which can leak in logs and referrers.

### Comparison of routing methods

| Method | Security | Complexity | Wildcard TLS | Log leakage risk |
|---|---|---|---|---|
| Subdomain | Medium | Medium (DNS + TLS) | Required | Low |
| Header | Low (forgeable) | Low | No | Low |
| JWT claim | High (signed) | Low | No | None |
| Path-based | Medium | Low | No | High |

**Recommendation:** Use JWT claims as the authoritative source. Subdomain or header can be a routing hint validated against the JWT.

---

## Blast radius containment

Blast radius = the maximum scope of impact when something goes wrong. Multi-tenancy design is fundamentally about minimizing blast radius.

### Failure domains

```
┌────────────────────────────────────────────────────────┐
│                 BLAST RADIUS LEVELS                    │
│                                                        │
│  Level 1: Single request failure                       │
│  ├── Impact: one user, one operation                   │
│  └── Containment: retry, circuit breaker               │
│                                                        │
│  Level 2: Single tenant failure                        │
│  ├── Impact: all users of one tenant                   │
│  └── Containment: tenant isolation, bulkhead            │
│                                                        │
│  Level 3: Shared service failure                       │
│  ├── Impact: all tenants using that service             │
│  └── Containment: redundancy, failover                  │
│                                                        │
│  Level 4: Infrastructure failure                       │
│  ├── Impact: all tenants in that region/AZ              │
│  └── Containment: multi-AZ, multi-region                │
│                                                        │
│  Level 5: Control plane failure                        │
│  ├── Impact: all tenants globally                       │
│  └── Containment: independent control planes            │
└────────────────────────────────────────────────────────┘
```

### Bulkhead pattern

Partition shared resources so that failure in one partition does not cascade.

```python
# bulkhead.py — thread pool per tenant tier

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any

class TenantBulkhead:
    """
    Separate thread pools per tenant tier.
    A free-tier tenant exhausting their pool cannot affect enterprise tenants.
    """

    def __init__(self):
        self.pools = {
            "enterprise": ThreadPoolExecutor(
                max_workers=50, thread_name_prefix="enterprise"
            ),
            "pro": ThreadPoolExecutor(
                max_workers=20, thread_name_prefix="pro"
            ),
            "free": ThreadPoolExecutor(
                max_workers=5, thread_name_prefix="free"
            ),
        }

    def submit(self, tier: str, fn: Callable, *args: Any) -> Any:
        pool = self.pools.get(tier, self.pools["free"])
        return pool.submit(fn, *args)

    def shutdown(self) -> None:
        for pool in self.pools.values():
            pool.shutdown(wait=True)
```

### Cell-based architecture

Divide infrastructure into independent cells, each serving a subset of tenants. Failures are cell-scoped.

```
┌───────────────────────────────────────────────┐
│               CELL ARCHITECTURE               │
│                                               │
│  Cell 1 (eu-west-1a)   Cell 2 (eu-west-1b)   │
│  ┌─────────────────┐   ┌─────────────────┐   │
│  │ Tenants A, B, C │   │ Tenants D, E, F │   │
│  │ App servers ×3  │   │ App servers ×3  │   │
│  │ DB replica      │   │ DB replica      │   │
│  │ Cache cluster   │   │ Cache cluster   │   │
│  └─────────────────┘   └─────────────────┘   │
│                                               │
│  Cell Router (stateless, multi-AZ)            │
│  Maps tenant → cell; handles cell failover    │
└───────────────────────────────────────────────┘
```

```hcl
# cell_routing.tf — Route53 weighted routing for cell-based architecture

resource "aws_route53_record" "cell_router" {
  for_each = var.cells

  zone_id = var.zone_id
  name    = "api.saas.example.com"
  type    = "A"

  alias {
    name                   = each.value.alb_dns_name
    zone_id                = each.value.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier = each.key
  weighted_routing_policy {
    weight = each.value.weight
  }
}
```

---

## Cross-tenant security testing

### Automated isolation verification

```python
# test_tenant_isolation.py — pytest suite for cross-tenant security

import pytest
import httpx

BASE_URL = "https://api.saas.example.com"

@pytest.fixture
def tenant_a_token():
    """Authenticate as tenant-acme user."""
    resp = httpx.post(f"{BASE_URL}/auth/token", json={
        "grant_type": "client_credentials",
        "client_id": "test-acme",
        "client_secret": "***",
    })
    return resp.json()["access_token"]

@pytest.fixture
def tenant_b_token():
    """Authenticate as tenant-globex user."""
    resp = httpx.post(f"{BASE_URL}/auth/token", json={
        "grant_type": "client_credentials",
        "client_id": "test-globex",
        "client_secret": "***",
    })
    return resp.json()["access_token"]

class TestCrossTenantIsolation:
    """
    These tests verify that tenant A cannot access tenant B's data
    through any API endpoint.
    """

    def test_tenant_a_cannot_list_tenant_b_orders(
        self, tenant_a_token, tenant_b_token
    ):
        # Create an order as tenant B
        resp = httpx.post(
            f"{BASE_URL}/api/orders",
            headers={"Authorization": f"Bearer {tenant_b_token}"},
            json={"product_id": 1, "quantity": 1},
        )
        assert resp.status_code == 201
        order_id = resp.json()["id"]

        # Attempt to read it as tenant A
        resp = httpx.get(
            f"{BASE_URL}/api/orders/{order_id}",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
        )
        assert resp.status_code in (403, 404), \
            f"Cross-tenant access succeeded! Got {resp.status_code}"

    def test_tenant_a_cannot_enumerate_tenant_b_orders(
        self, tenant_a_token
    ):
        resp = httpx.get(
            f"{BASE_URL}/api/orders",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
        )
        assert resp.status_code == 200
        for order in resp.json()["data"]:
            assert order["tenant_id"] == "acme", \
                f"Data leak: order {order['id']} belongs to {order['tenant_id']}"

    def test_tenant_header_spoofing_blocked(self, tenant_a_token):
        """Attempt to override tenant via header while authenticated as A."""
        resp = httpx.get(
            f"{BASE_URL}/api/orders",
            headers={
                "Authorization": f"Bearer {tenant_a_token}",
                "X-Tenant-Id": "globex",  # spoofed
            },
        )
        # Should either reject or ignore the spoofed header
        if resp.status_code == 200:
            for order in resp.json()["data"]:
                assert order["tenant_id"] == "acme", \
                    "Header spoofing bypassed tenant isolation!"

    def test_sql_injection_does_not_bypass_rls(self, tenant_a_token):
        """Attempt SQL injection in filter parameters."""
        resp = httpx.get(
            f"{BASE_URL}/api/orders",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
            params={"status": "' OR tenant_id='globex' --"},
        )
        if resp.status_code == 200:
            for order in resp.json()["data"]:
                assert order["tenant_id"] == "acme", \
                    "SQL injection bypassed tenant isolation!"

    def test_path_traversal_tenant_id(self, tenant_a_token):
        """Attempt path traversal in tenant-scoped URLs."""
        resp = httpx.get(
            f"{BASE_URL}/api/tenants/../tenants/globex/orders",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
        )
        assert resp.status_code in (400, 403, 404)

    def test_idor_via_direct_resource_id(
        self, tenant_a_token, tenant_b_token
    ):
        """Create resource as B, access by ID as A (IDOR)."""
        # Create as B
        resp = httpx.post(
            f"{BASE_URL}/api/documents",
            headers={"Authorization": f"Bearer {tenant_b_token}"},
            json={"title": "Secret Doc", "content": "Confidential"},
        )
        assert resp.status_code == 201
        doc_id = resp.json()["id"]

        # Access as A
        resp = httpx.get(
            f"{BASE_URL}/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
        )
        assert resp.status_code in (403, 404), \
            f"IDOR vulnerability: tenant A accessed tenant B's document {doc_id}"
```

### Database isolation verification

```sql
-- Verify RLS is enabled on all tenant tables
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('orders', 'products', 'users', 'invoices', 'documents')
ORDER BY tablename;

-- Expected: rowsecurity = true for all

-- Verify no policies are missing
SELECT
    schemaname,
    tablename,
    policyname,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename;

-- Verify FORCE ROW LEVEL SECURITY is set
SELECT
    relname,
    relrowsecurity,
    relforcerowsecurity
FROM pg_class
WHERE relname IN ('orders', 'products', 'users', 'invoices', 'documents');

-- Expected: both relrowsecurity and relforcerowsecurity = true
```

---

## Compliance and data residency per tenant

### Data residency requirements

Different tenants may require data to reside in specific geographic regions due to GDPR, data sovereignty laws, or contractual obligations.

```
┌──────────────────────────────────────────────────┐
│           DATA RESIDENCY ARCHITECTURE            │
│                                                  │
│  Tenant: acme-eu        Region: eu-west-1        │
│  Tenant: acme-us        Region: us-east-1        │
│  Tenant: globex-ap      Region: ap-southeast-1   │
│                                                  │
│  Routing layer reads tenant → region mapping     │
│  and directs all data operations to the correct  │
│  regional deployment.                            │
└──────────────────────────────────────────────────┘
```

```hcl
# data_residency.tf — tenant-to-region mapping

variable "tenant_regions" {
  type = map(object({
    primary_region   = string
    backup_region    = string
    compliance_level = string  # "gdpr", "hipaa", "standard"
  }))
  default = {
    "acme-eu" = {
      primary_region   = "eu-west-1"
      backup_region    = "eu-central-1"
      compliance_level = "gdpr"
    }
    "acme-us" = {
      primary_region   = "us-east-1"
      backup_region    = "us-west-2"
      compliance_level = "hipaa"
    }
    "globex-ap" = {
      primary_region   = "ap-southeast-1"
      backup_region    = "ap-northeast-1"
      compliance_level = "standard"
    }
  }
}

# S3 bucket per region with replication only within allowed regions
resource "aws_s3_bucket" "tenant_data" {
  for_each = var.tenant_regions

  bucket   = "saas-data-${each.key}-${each.value.primary_region}"
  provider = aws.by_region[each.value.primary_region]

  tags = {
    TenantId        = each.key
    DataResidency   = each.value.primary_region
    ComplianceLevel = each.value.compliance_level
  }
}

# KMS key per region — data encrypted with region-local key
resource "aws_kms_key" "tenant_data" {
  for_each = var.tenant_regions

  description         = "Encryption key for tenant ${each.key}"
  enable_key_rotation = true
  provider            = aws.by_region[each.value.primary_region]

  tags = {
    TenantId = each.key
  }
}
```

### Per-tenant encryption keys

```hcl
# tenant_encryption.tf — per-tenant KMS keys for envelope encryption

resource "aws_kms_key" "tenant" {
  description             = "Tenant ${var.tenant_id} data encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  customer_master_key_spec = "SYMMETRIC_DEFAULT"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TenantKeyAdmin"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/KeyAdmin"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "TenantAppAccess"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.tenant_app.arn
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:GenerateDataKeyWithoutPlaintext",
          "kms:DescribeKey",
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    TenantId = var.tenant_id
  }
}

resource "aws_kms_alias" "tenant" {
  name          = "alias/tenant-${var.tenant_id}"
  target_key_id = aws_kms_key.tenant.key_id
}
```

### GDPR compliance automation

```sql
-- Data deletion for tenant offboarding (GDPR right to erasure)
-- Run as admin role, not tenant role (RLS would prevent seeing data)

BEGIN;

-- Verify tenant exists
SELECT count(*) FROM tenants WHERE id = 'acme-eu';

-- Delete in dependency order
DELETE FROM audit_logs WHERE tenant_id = 'acme-eu';
DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE tenant_id = 'acme-eu');
DELETE FROM orders WHERE tenant_id = 'acme-eu';
DELETE FROM documents WHERE tenant_id = 'acme-eu';
DELETE FROM users WHERE tenant_id = 'acme-eu';
DELETE FROM products WHERE tenant_id = 'acme-eu';

-- Remove tenant record last
DELETE FROM tenants WHERE id = 'acme-eu';

-- Verify complete deletion
SELECT 'orders' AS table_name, count(*) FROM orders WHERE tenant_id = 'acme-eu'
UNION ALL
SELECT 'users', count(*) FROM users WHERE tenant_id = 'acme-eu'
UNION ALL
SELECT 'products', count(*) FROM products WHERE tenant_id = 'acme-eu';

COMMIT;
```

---

## Cost allocation per tenant

### Tagging strategy

```hcl
# tag_policy.tf — enforce cost-allocation tags via AWS Organizations

resource "aws_organizations_policy" "tag_policy" {
  name    = "mandatory-tenant-tags"
  type    = "TAG_POLICY"
  content = jsonencode({
    tags = {
      TenantId = {
        tag_key = {
          "@@assign" = "TenantId"
        }
        enforced_for = {
          "@@assign" = [
            "ec2:instance",
            "ec2:volume",
            "rds:db",
            "s3:bucket",
            "lambda:function",
            "elasticloadbalancing:loadbalancer",
            "elasticache:cluster",
          ]
        }
      }
      CostCenter = {
        tag_key = {
          "@@assign" = "CostCenter"
        }
        enforced_for = {
          "@@assign" = [
            "ec2:instance",
            "rds:db",
            "s3:bucket",
          ]
        }
      }
    }
  })
}

resource "aws_organizations_policy_attachment" "tag_policy" {
  policy_id = aws_organizations_policy.tag_policy.id
  target_id = aws_organizations_organizational_unit.production_tenants.id
}
```

### Showback and chargeback

```python
# cost_allocator.py — generate per-tenant cost reports

import boto3
from datetime import datetime, timedelta
from typing import Any

ce_client = boto3.client("ce")

def get_tenant_costs(
    tenant_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Query AWS Cost Explorer for costs attributed to a specific tenant.
    """
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    response = ce_client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="DAILY",
        Metrics=["BlendedCost", "UsageQuantity"],
        Filter={
            "Tags": {
                "Key": "TenantId",
                "Values": [tenant_id],
                "MatchOptions": ["EQUALS"],
            }
        },
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"},
        ],
    )

    total = 0.0
    by_service: dict[str, float] = {}

    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            service = group["Keys"][0]
            amount = float(group["Metrics"]["BlendedCost"]["Amount"])
            by_service[service] = by_service.get(service, 0.0) + amount
            total += amount

    return {
        "tenant_id": tenant_id,
        "period": {"start": start_date, "end": end_date},
        "total_cost_usd": round(total, 2),
        "by_service": {k: round(v, 2) for k, v in sorted(
            by_service.items(), key=lambda x: -x[1]
        )},
    }
```

### Kubernetes cost allocation with labels

```yaml
# Kubecost deployment for per-tenant cost visibility
# kubecost reads pod labels to attribute costs

apiVersion: v1
kind: Pod
metadata:
  namespace: tenant-acme
  labels:
    app: api-server
    tenant: acme
    tier: enterprise
    cost-center: acme-corp
  annotations:
    kubecost.com/tenant: "acme"
spec:
  containers:
    - name: api
      image: registry.example.com/api:v2.1.0
      resources:
        requests:
          cpu: "200m"
          memory: "256Mi"
        limits:
          cpu: "1"
          memory: "1Gi"
```

---

## Tenant lifecycle management

### Onboarding workflow

```
┌──────────────────────────────────────────────────┐
│            TENANT ONBOARDING PIPELINE            │
│                                                  │
│  1. Signup → Create tenant record in control DB  │
│  2. Validate → KYC, payment method, domain       │
│  3. Provision → Tier-appropriate infrastructure   │
│     ├── Free: Create RLS row + namespace          │
│     ├── Pro: Create schema + namespace + quotas   │
│     └── Enterprise: Create account + VPC + DB     │
│  4. Configure → DNS, TLS, secrets, IAM            │
│  5. Seed → Initial data, admin user, defaults     │
│  6. Verify → Smoke tests, connectivity checks     │
│  7. Notify → Welcome email, API keys              │
└──────────────────────────────────────────────────┘
```

```python
# tenant_provisioner.py — orchestrate tenant onboarding

from enum import Enum
from dataclasses import dataclass

class TenantTier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class TenantConfig:
    tenant_id: str
    tier: TenantTier
    region: str
    domain: str | None  # custom domain for enterprise
    admin_email: str

class TenantProvisioner:
    """Orchestrates the provisioning pipeline for new tenants."""

    def provision(self, config: TenantConfig) -> dict:
        steps = [
            ("create_tenant_record", self._create_record),
            ("provision_database", self._provision_db),
            ("provision_compute", self._provision_compute),
            ("configure_networking", self._configure_network),
            ("create_admin_user", self._create_admin),
            ("seed_initial_data", self._seed_data),
            ("run_smoke_tests", self._smoke_test),
            ("send_welcome", self._send_welcome),
        ]

        results = {}
        for step_name, step_fn in steps:
            try:
                results[step_name] = step_fn(config)
            except Exception as e:
                # Rollback completed steps in reverse order
                self._rollback(config, list(results.keys()))
                raise ProvisioningError(
                    f"Failed at step {step_name}: {e}"
                ) from e

        return results

    def _provision_db(self, config: TenantConfig) -> dict:
        match config.tier:
            case TenantTier.FREE:
                return self._create_rls_tenant(config.tenant_id)
            case TenantTier.PRO:
                return self._create_schema(config.tenant_id)
            case TenantTier.ENTERPRISE:
                return self._create_dedicated_db(config.tenant_id, config.region)

    def _provision_compute(self, config: TenantConfig) -> dict:
        match config.tier:
            case TenantTier.FREE:
                return self._create_namespace(
                    config.tenant_id, cpu="2", memory="4Gi", pods="10"
                )
            case TenantTier.PRO:
                return self._create_namespace(
                    config.tenant_id, cpu="8", memory="16Gi", pods="50"
                )
            case TenantTier.ENTERPRISE:
                return self._create_dedicated_cluster(
                    config.tenant_id, config.region
                )

    # ... remaining methods implement each provisioning step
```

### Offboarding and data deletion

```python
# tenant_offboarder.py — safe tenant removal

class TenantOffboarder:
    """
    Handles tenant removal with data retention compliance.
    GDPR requires complete deletion within 30 days of request.
    """

    def offboard(self, tenant_id: str, reason: str) -> dict:
        # Step 1: Disable tenant (no new requests)
        self._disable_tenant(tenant_id)

        # Step 2: Export data for customer (if requested)
        export_url = self._export_tenant_data(tenant_id)

        # Step 3: Wait for retention period (configurable)
        self._schedule_deletion(tenant_id, delay_days=30)

        # Step 4: Log the offboarding event
        self._audit_log(tenant_id, reason)

        return {
            "tenant_id": tenant_id,
            "status": "disabled",
            "export_url": export_url,
            "scheduled_deletion": "30 days",
        }

    def execute_deletion(self, tenant_id: str) -> None:
        """Called by scheduler after retention period expires."""
        # Delete in reverse dependency order
        self._delete_compute_resources(tenant_id)
        self._delete_database(tenant_id)
        self._delete_storage(tenant_id)
        self._delete_secrets(tenant_id)
        self._delete_iam_resources(tenant_id)
        self._delete_dns_records(tenant_id)
        self._delete_tenant_record(tenant_id)

        # Verify no orphaned resources remain
        orphans = self._scan_for_orphans(tenant_id)
        if orphans:
            raise OrphanedResourceError(
                f"Found {len(orphans)} orphaned resources for tenant {tenant_id}"
            )
```

### Tenant migration between tiers

```python
# tenant_migrator.py — upgrade/downgrade tenant tier

class TenantMigrator:
    """Handles tier changes with zero-downtime migration."""

    def upgrade(self, tenant_id: str, from_tier: str, to_tier: str) -> dict:
        if from_tier == "free" and to_tier == "pro":
            return self._free_to_pro(tenant_id)
        elif from_tier == "pro" and to_tier == "enterprise":
            return self._pro_to_enterprise(tenant_id)
        else:
            raise ValueError(f"Unsupported migration path: {from_tier} → {to_tier}")

    def _free_to_pro(self, tenant_id: str) -> dict:
        """
        Migrate from shared RLS to dedicated schema.
        1. Create new schema
        2. Copy data from shared tables (filtered by tenant_id)
        3. Update routing to point to new schema
        4. Delete RLS rows from shared tables
        """
        steps = {
            "create_schema": self._create_schema(tenant_id),
            "copy_data": self._copy_rls_to_schema(tenant_id),
            "update_routing": self._update_routing(tenant_id, "schema"),
            "verify_data": self._verify_data_integrity(tenant_id),
            "cleanup_rls": self._delete_rls_rows(tenant_id),
            "update_quotas": self._update_resource_quotas(tenant_id, "pro"),
        }
        return steps
```

---

## Kubernetes multi-tenancy avanzata — deep dive

### Namespace design patterns per SaaS

Il namespace è la primitiva fondamentale della multi-tenancy Kubernetes, ma il design superficiale — un namespace per tenant senza ulteriore struttura — genera rapidamente debito operativo. In ambienti SaaS maturi con centinaia di tenant, il pattern che scala meglio combina una gerarchia logica con automazione dichiarativa.

**Pattern gerarchico con prefissi:**

```
# Struttura namespace per tenant con separazione ambiente
tenant-acme-prod          # Workload di produzione
tenant-acme-staging       # Staging isolato per preview
tenant-acme-jobs          # Background jobs e cron
tenant-globex-prod
tenant-globex-staging
tenant-globex-jobs
```

Ogni tenant riceve un set predefinito di namespace con naming convention standardizzata. L'automazione di onboarding crea tutti i namespace simultaneamente con labels coerenti.

**Namespace labels standard per orchestrazione:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-acme-prod
  labels:
    tenant.saas.io/id: acme
    tenant.saas.io/tier: enterprise
    tenant.saas.io/environment: production
    tenant.saas.io/cost-center: CC-ACME-2024
    tenant.saas.io/data-residency: eu-west-1
    tenant.saas.io/onboarded: "2025-03-15"
    pod-security.kubernetes.io/enforce: restricted
  annotations:
    tenant.saas.io/owner-email: admin@acme.com
    tenant.saas.io/contract-expiry: "2027-03-14"
    tenant.saas.io/max-namespaces: "5"
```

Queste labels alimentano il routing delle NetworkPolicy, i filtri Prometheus, le query di costo Kubecost e le policy OPA/Kyverno senza bisogno di database di configurazione esterni.

### Capsule — tenant come risorsa CRD

Capsule è un progetto CNCF sandbox che introduce il concetto di Tenant come Custom Resource Definition. A differenza del semplice namespace, un Tenant Capsule raggruppa più namespace sotto un singolo owner, applicando policy, quote e limitazioni a livello aggregato.

```yaml
# Capsule Tenant CRD
apiVersion: capsule.clastix.io/v1beta2
kind: Tenant
metadata:
  name: acme-corp
spec:
  owners:
    - name: acme-admin
      kind: User
    - name: acme-devops
      kind: Group
  namespaceOptions:
    quota: 5                    # Massimo 5 namespace per tenant
    additionalMetadata:
      labels:
        tenant.saas.io/id: acme
        cost-center: CC-ACME
      annotations:
        scheduler.alpha.kubernetes.io/node-selector: "pool=shared"
  networkPolicies:
    items:
      - policyTypes:
          - Ingress
          - Egress
        egress:
          - to:
              - namespaceSelector:
                  matchLabels:
                    capsule.clastix.io/tenant: acme-corp
          - to:
              - namespaceSelector:
                  matchLabels:
                    kubernetes.io/metadata.name: kube-system
            ports:
              - protocol: UDP
                port: 53
        ingress:
          - from:
              - namespaceSelector:
                  matchLabels:
                    capsule.clastix.io/tenant: acme-corp
        podSelector: {}
  resourceQuotas:
    scope: Tenant              # Quota aggregata su tutti i namespace
    items:
      - hard:
          requests.cpu: "16"
          requests.memory: "32Gi"
          limits.cpu: "32"
          limits.memory: "64Gi"
          pods: "100"
          services: "20"
          persistentvolumeclaims: "20"
  limitRanges:
    items:
      - limits:
          - type: Container
            default:
              cpu: "500m"
              memory: "512Mi"
            defaultRequest:
              cpu: "100m"
              memory: "128Mi"
            max:
              cpu: "4"
              memory: "8Gi"
  storageClasses:
    allowed:
      - gp3-encrypted
      - io2-encrypted
    allowedRegex: "^(gp3|io2)-encrypted$"
  ingressOptions:
    hostnameCollisionScope: Tenant
    allowedHostnames:
      allowedRegex: "^.*\\.acme\\.saas\\.example\\.com$"
  containerRegistries:
    allowed:
      - "123456789012.dkr.ecr.eu-west-1.amazonaws.com/acme/"
    allowedRegex: "^123456789012\\.dkr\\.ecr\\..*\\.amazonaws\\.com/acme/"
```

Il vantaggio chiave di Capsule rispetto alla gestione manuale dei namespace è la **quota aggregata a livello tenant**: la somma delle risorse consumate in tutti i namespace del tenant non può superare il limite definito nel Tenant CRD. Con le ResourceQuota standard Kubernetes, i limiti si applicano per namespace — un tenant con 5 namespace potrebbe consumare 5× la quota prevista.

**Capsule vs namespace manuale — confronto:**

| Dimensione | Namespace manuale | Capsule |
|---|---|---|
| Quota risorse | Per namespace | Aggregata per tenant |
| Multi-namespace per tenant | Gestione manuale | Automatica con policy |
| Network isolation | NetworkPolicy manuale per namespace | NetworkPolicy template nel Tenant CRD |
| RBAC | RoleBinding manuale per namespace | Owner automatici su tutti i namespace |
| Ingress hostname control | Nessuno (rischio collisione) | Regex hostname per tenant |
| Container registry restriction | OPA/Kyverno separato | Integrato nel Tenant CRD |
| Complessità operativa | Alta con >50 tenant | Bassa, scalabile a migliaia |

### Loft e piattaforme di gestione multi-tenancy

Loft Labs (gli stessi creatori di vCluster) offre una piattaforma di gestione che combina vCluster, space management e self-service per team di piattaforma. Il modello di Loft si posiziona come layer di orchestrazione:

**Concetti chiave di Loft:**

- **Spaces:** Namespace gestiti con template predefiniti, sleep mode automatico e auto-deletion dopo inattività.
- **Virtual Clusters:** vCluster provisionati on-demand con lifecycle management, backup e upgrade automatico.
- **Sleep Mode:** I virtual cluster inattivi vengono sospesi automaticamente, riducendo il consumo di risorse del 60-80% per ambienti di sviluppo e staging.
- **Quotas a livello team:** Limiti aggregati su quanti space e virtual cluster un team può creare, con accounting separato.
- **Audit logging:** Ogni azione di provisioning, accesso e modifica viene registrata con tenant context per compliance.

Il caso d'uso più forte per Loft è nei team di piattaforma che servono developer interni: ogni team riceve un portale self-service per creare ambienti effimeri senza ticket o attesa, ma con guardrail enforced centralmente.

### vCluster — architettura interna e configurazione avanzata

vCluster esegue un control plane Kubernetes completo (API server, controller manager, scheduler, etcd/SQLite) dentro un namespace del cluster host. I workload definiti nel virtual cluster vengono sincronizzati come pod reali nel namespace host tramite un componente chiamato **syncer**.

**Architettura di sync:**

```
┌─────────────────────────────────────────────────────┐
│                  HOST CLUSTER                        │
│                                                      │
│  Namespace: vcluster-tenant-acme                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │           vCluster Control Plane                │ │
│  │                                                 │ │
│  │  ┌──────────┐ ┌────────────────┐ ┌───────────┐ │ │
│  │  │kube-api  │ │controller-mgr  │ │  etcd /   │ │ │
│  │  │server    │ │                │ │  SQLite   │ │ │
│  │  └──────────┘ └────────────────┘ └───────────┘ │ │
│  │                                                 │ │
│  │  ┌──────────────────────────────────────────┐   │ │
│  │  │              SYNCER                       │   │ │
│  │  │  Virtual Pod → Real Pod nel namespace     │   │ │
│  │  │  Virtual Service → Real Service           │   │ │
│  │  │  Virtual Ingress → Real Ingress           │   │ │
│  │  │  Virtual PVC → Real PVC                   │   │ │
│  │  └──────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  Pod reali (sincronizzati dal syncer):               │
│  ┌──────┐ ┌──────┐ ┌──────┐                         │
│  │pod-1 │ │pod-2 │ │pod-3 │  ← label: vCluster=acme │
│  └──────┘ └──────┘ └──────┘                         │
└─────────────────────────────────────────────────────┘
```

**Configurazione avanzata vCluster 0.20+ con isolamento rinforzato:**

```yaml
# vcluster-values.yaml per tenant enterprise
controlPlane:
  distro: k8s                # k8s, k3s, k0s
  backingStore:
    etcd:
      embedded:
        enabled: true        # etcd embedded per persistenza forte
  coredns:
    embedded: true           # CoreDNS dedicato per il virtual cluster
  statefulSet:
    resources:
      requests:
        cpu: "200m"
        memory: "256Mi"
      limits:
        cpu: "1"
        memory: "1Gi"

sync:
  toHost:
    ingresses:
      enabled: true
    persistentVolumes:
      enabled: true
    storageClasses:
      enabled: false         # Usa le storage class dell'host
    priorityClasses:
      enabled: false
  fromHost:
    nodes:
      enabled: true
      selector:
        labels:
          pool: shared
    storageClasses:
      enabled: true
      selector:
        labels:
          tier: standard

networking:
  replicateServices:
    fromHost:
      - from: ingress-system/ingress-nginx
        to: ingress-nginx
    toHost: []

policies:
  resourceQuota:
    enabled: true
    quota:
      requests.cpu: "10"
      requests.memory: "20Gi"
      limits.cpu: "20"
      limits.memory: "40Gi"
      pods: "100"
      services: "20"
      persistentvolumeclaims: "15"
  limitRange:
    enabled: true
    default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
  networkPolicy:
    enabled: true            # Default deny tra vCluster e host
  podSecurityStandard: restricted

exportKubeConfig:
  context: tenant-acme
  server: https://tenant-acme.saas.example.com

telemetry:
  enabled: false
```

**Overhead tipico per vCluster:**

| Risorsa | Minimo | Consigliato |
|---|---|---|
| CPU | 200m | 500m–1 core |
| Memoria | 256Mi | 512Mi–1Gi |
| Storage (etcd) | 1Gi | 5–10Gi |
| Tempo di avvio | 10–30 secondi | — |

Con k3s come distro interna (invece di k8s), l'overhead si riduce del ~40% perché k3s usa SQLite al posto di etcd e ha un binary unificato.

---

## Database multi-tenancy patterns — approfondimento

### Pattern ibrido — sharding per tenant con routing dinamico

Il pattern ibrido combina i vantaggi di schema-per-tenant e RLS, partizionando i tenant su shard database basati su volume, tier o requisiti di compliance. Ogni shard contiene decine o centinaia di tenant con RLS attivo.

```
┌────────────────────────────────────────────────────────┐
│             HYBRID DATABASE ARCHITECTURE               │
│                                                        │
│  Shard 1 (EU — GDPR)       Shard 2 (US)              │
│  ┌──────────────────┐      ┌──────────────────┐       │
│  │ PostgreSQL 16    │      │ PostgreSQL 16    │       │
│  │                  │      │                  │       │
│  │ Tenants: 200     │      │ Tenants: 300     │       │
│  │ RLS attivo       │      │ RLS attivo       │       │
│  │ Region: eu-west-1│      │ Region: us-east-1│       │
│  └──────────────────┘      └──────────────────┘       │
│                                                        │
│  Shard 3 (Enterprise)       Shard 4 (AP)              │
│  ┌──────────────────┐      ┌──────────────────┐       │
│  │ PostgreSQL 16    │      │ PostgreSQL 16    │       │
│  │                  │      │                  │       │
│  │ Tenants: 5       │      │ Tenants: 150     │       │
│  │ Schema-per-tenant│      │ RLS attivo       │       │
│  │ Dedicated compute│      │ Region: ap-se-1  │       │
│  └──────────────────┘      └──────────────────┘       │
│                                                        │
│  Routing Service (tenant → shard mapping in Redis)     │
└────────────────────────────────────────────────────────┘
```

**Routing service per shard resolution:**

```python
# shard_router.py — risoluzione shard per tenant

import redis
from dataclasses import dataclass

@dataclass(frozen=True)
class ShardConfig:
    host: str
    port: int
    database: str
    isolation_mode: str   # "rls" | "schema" | "dedicated"
    region: str

class TenantShardRouter:
    """
    Risolve il database shard corretto per ogni tenant.
    Il mapping tenant → shard è cachato in Redis
    con fallback su database di configurazione.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minuti

    def resolve(self, tenant_id: str) -> ShardConfig:
        cache_key = f"shard:{tenant_id}"
        cached = self.redis.hgetall(cache_key)

        if cached:
            return ShardConfig(
                host=cached[b"host"].decode(),
                port=int(cached[b"port"]),
                database=cached[b"database"].decode(),
                isolation_mode=cached[b"isolation_mode"].decode(),
                region=cached[b"region"].decode(),
            )

        # Fallback: query control database
        config = self._query_control_db(tenant_id)

        # Cache the result
        self.redis.hset(cache_key, mapping={
            "host": config.host,
            "port": str(config.port),
            "database": config.database,
            "isolation_mode": config.isolation_mode,
            "region": config.region,
        })
        self.redis.expire(cache_key, self.cache_ttl)

        return config

    def _query_control_db(self, tenant_id: str) -> ShardConfig:
        """Query the control plane database for shard assignment."""
        # Implementazione: SELECT shard_host, shard_port, ...
        # FROM tenant_shard_mapping WHERE tenant_id = %s
        raise NotImplementedError
```

### Database serverless per tenant — pattern emergente

Pattern emergente nel 2024-2025: database serverless con branch-per-tenant. Piattaforme come Neon (PostgreSQL serverless) permettono di creare un branch PostgreSQL per ogni tenant in millisecondi, con compute e storage dedicati ma schema condiviso dalla base.

**Vantaggi del branch-per-tenant:**

- Provisioning istantaneo (< 1 secondo per nuovo tenant).
- Isolamento fisico dei dati senza il costo di un'istanza RDS dedicata.
- Backup e point-in-time recovery per singolo tenant nativi.
- Scale-to-zero per tenant inattivi (costo zero quando non in uso).
- Schema migrations applicate al branch base, propagate automaticamente.

**Trade-off:**

- Vendor lock-in verso il provider serverless.
- Latenza cold start per tenant inattivi (wake-up 200-500ms).
- Meno controllo su configurazione PostgreSQL avanzata.
- Non ancora adatto per workload ad alta frequenza di write transazionale.

### Migrazioni schema in ambienti multi-tenant

La gestione delle migrazioni è uno dei problemi operativi più sottovalutati nella multi-tenancy database. Con centinaia di schema o database dedicati, una singola migrazione diventa N operazioni parallele, ognuna delle quali può fallire indipendentemente.

**Strategia di migrazione robusta:**

```python
# migration_orchestrator.py — migrazione multi-tenant parallela

import asyncio
from dataclasses import dataclass
from enum import Enum

class MigrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class TenantMigrationResult:
    tenant_id: str
    status: MigrationStatus
    duration_ms: int
    error: str | None = None

class MultiTenantMigrationOrchestrator:
    """
    Esegue migrazioni DDL su tutti i tenant con:
    - Parallelismo controllato (max N tenant simultanei)
    - Retry con backoff esponenziale
    - Rollback per-tenant senza impattare altri
    - Report di stato granulare
    """

    def __init__(self, max_concurrent: int = 10, max_retries: int = 3):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_migration(
        self,
        migration_sql: str,
        rollback_sql: str,
        tenant_ids: list[str],
    ) -> list[TenantMigrationResult]:
        tasks = [
            self._migrate_tenant(tenant_id, migration_sql, rollback_sql)
            for tenant_id in tenant_ids
        ]
        return await asyncio.gather(*tasks)

    async def _migrate_tenant(
        self,
        tenant_id: str,
        migration_sql: str,
        rollback_sql: str,
    ) -> TenantMigrationResult:
        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    start = asyncio.get_event_loop().time()
                    await self._apply_migration(tenant_id, migration_sql)
                    elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                    return TenantMigrationResult(
                        tenant_id=tenant_id,
                        status=MigrationStatus.SUCCESS,
                        duration_ms=elapsed,
                    )
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        await self._apply_rollback(tenant_id, rollback_sql)
                        return TenantMigrationResult(
                            tenant_id=tenant_id,
                            status=MigrationStatus.ROLLED_BACK,
                            duration_ms=0,
                            error=str(e),
                        )
                    await asyncio.sleep(2 ** attempt)

    # ... implementazione di _apply_migration e _apply_rollback
```

**Regole per migrazioni multi-tenant sicure:**

1. **Ogni migrazione deve essere idempotente:** usare `IF NOT EXISTS`, `IF EXISTS`, `CREATE OR REPLACE`.
2. **Ogni migrazione deve avere un rollback testato:** il rollback viene eseguito automaticamente se la migrazione fallisce.
3. **Migrazioni non-breaking first:** separare le migrazioni in additive (aggiunta colonna, indice) e breaking (rimozione colonna, cambio tipo). Applicare prima le additive.
4. **Canary migration:** applicare prima a un sottoinsieme di tenant (5%), verificare, poi procedere con il restante 95%.
5. **Lock tracking:** monitorare `pg_locks` durante le migrazioni per evitare deadlock su tabelle condivise.

---

## Network isolation avanzata

### Cilium per multi-tenancy — L3/L4/L7

Cilium utilizza eBPF per implementare network policy ad alte prestazioni con visibilità L7. A differenza delle NetworkPolicy standard Kubernetes (solo L3/L4), Cilium aggiunge filtraggio a livello HTTP, gRPC e Kafka, con identity-aware enforcement basato su service account anziché indirizzo IP.

```yaml
# CiliumNetworkPolicy — isolation L7 per tenant
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  namespace: tenant-acme
  name: tenant-api-l7-policy
spec:
  endpointSelector:
    matchLabels:
      app: api-server
      tenant: acme
  ingress:
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: ingress-system
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
              - method: "DELETE"
                path: "/api/v1/orders/[0-9]+"
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: monitoring
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
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: tenant-acme
      toPorts:
        - ports:
            - port: "5432"
              protocol: TCP
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: ANY
    - toCIDR:
        - 0.0.0.0/0
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
```

**Hubble per osservabilità di rete per tenant:**

Hubble, il componente di osservabilità di Cilium, fornisce visibilità in tempo reale sui flow di rete tra pod. Per la multi-tenancy, Hubble permette di filtrare i flow per namespace (e quindi per tenant) e di generare alert su traffico anomalo cross-tenant.

```bash
# Osservare flow di rete per un tenant specifico
hubble observe --namespace tenant-acme --verdict DROPPED
hubble observe --namespace tenant-acme --to-namespace tenant-globex  # Traffico cross-tenant (dovrebbe essere vuoto)

# Metriche di rete per tenant
hubble observe --namespace tenant-acme -o jsonpb | \
  jq '{src: .source.namespace, dst: .destination.namespace, verdict: .verdict}'
```

### Service mesh per-tenant isolation

Un service mesh come Istio o Linkerd aggiunge un layer di isolation L7 con mTLS automatico, authorization policy e traffic management per tenant.

**Istio AuthorizationPolicy per isolation tra tenant:**

```yaml
# Deny all cross-namespace traffic by default
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  namespace: istio-system
  name: deny-cross-tenant
spec:
  action: DENY
  rules:
    - from:
        - source:
            notNamespaces:
              - "{{ .Release.Namespace }}"
      to:
        - operation:
            methods: ["*"]
      when:
        - key: source.namespace
          notValues:
            - ingress-system
            - monitoring
            - istio-system

---
# Allow specific cross-namespace access for shared services
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  namespace: tenant-acme
  name: allow-ingress-to-tenant
spec:
  action: ALLOW
  rules:
    - from:
        - source:
            namespaces: ["ingress-system"]
            principals: ["cluster.local/ns/ingress-system/sa/ingress-nginx"]
      to:
        - operation:
            ports: ["8080"]
```

**Traffic management per tenant con Istio:**

```yaml
# VirtualService con routing per tenant basato su header
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  namespace: istio-system
  name: tenant-routing
spec:
  hosts:
    - "api.saas.example.com"
  gateways:
    - saas-gateway
  http:
    - match:
        - headers:
            x-tenant-tier:
              exact: enterprise
      route:
        - destination:
            host: api-server.tenant-enterprise.svc.cluster.local
            port:
              number: 8080
      timeout: 30s
      retries:
        attempts: 3
    - match:
        - headers:
            x-tenant-tier:
              exact: free
      route:
        - destination:
            host: api-server.tenant-free-pool.svc.cluster.local
            port:
              number: 8080
      timeout: 10s
      retries:
        attempts: 1
```

---

## Resource quotas e limit ranges — strategie avanzate

### Quota tiering automatizzato

Le ResourceQuota statiche diventano rapidamente obsolete quando i tenant crescono. Un controller personalizzato che monitora l'utilizzo e aggiusta le quote automaticamente previene sia il sotto-provisioning che il sovra-provisioning.

```python
# quota_autoscaler.py — aggiustamento automatico quote per tenant

from dataclasses import dataclass
from kubernetes import client, config

@dataclass
class QuotaAdjustment:
    tenant_id: str
    namespace: str
    current_cpu: str
    recommended_cpu: str
    current_memory: str
    recommended_memory: str
    reason: str

class TenantQuotaAutoscaler:
    """
    Monitora l'utilizzo risorse per tenant e raccomanda
    aggiustamenti di quota basati su:
    - Media utilizzo ultimi 7 giorni
    - Picco utilizzo ultimi 30 giorni
    - Tier del tenant (budget massimo per tier)
    - Headroom configurabile (20% sopra il picco)
    """

    TIER_CEILINGS = {
        "enterprise": {"cpu": "64", "memory": "128Gi", "pods": "500"},
        "pro":        {"cpu": "16", "memory": "32Gi",  "pods": "100"},
        "free":       {"cpu": "4",  "memory": "8Gi",   "pods": "20"},
    }

    HEADROOM_FACTOR = 1.2  # 20% sopra il picco osservato

    def analyze(self, tenant_id: str, tier: str) -> QuotaAdjustment | None:
        current_usage = self._get_current_usage(tenant_id)
        peak_usage = self._get_peak_usage(tenant_id, days=30)
        current_quota = self._get_current_quota(tenant_id)
        ceiling = self.TIER_CEILINGS[tier]

        recommended_cpu = min(
            float(peak_usage["cpu"]) * self.HEADROOM_FACTOR,
            float(ceiling["cpu"]),
        )
        recommended_memory = min(
            float(peak_usage["memory_gi"]) * self.HEADROOM_FACTOR,
            float(ceiling["memory"].rstrip("Gi")),
        )

        if self._needs_adjustment(current_quota, recommended_cpu, recommended_memory):
            return QuotaAdjustment(
                tenant_id=tenant_id,
                namespace=f"tenant-{tenant_id}",
                current_cpu=current_quota["cpu"],
                recommended_cpu=f"{recommended_cpu:.1f}",
                current_memory=current_quota["memory"],
                recommended_memory=f"{recommended_memory:.0f}Gi",
                reason=f"Peak 30d: CPU={peak_usage['cpu']}, Mem={peak_usage['memory_gi']}Gi",
            )
        return None
```

### Priority e preemption per tenant tier

La combinazione di PriorityClass e preemption garantisce che i tenant enterprise mantengano le risorse anche sotto pressione, mentre i tenant free vengono degradati per primi.

```yaml
# Configurazione completa priority per tier
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-critical
value: 10000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Workload critici enterprise — mai preempted"

---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-enterprise
value: 5000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Enterprise — preempt solo free/standard"

---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-standard
value: 1000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Standard — preempt solo free"

---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: tenant-free
value: 100
globalDefault: false
preemptionPolicy: Never
description: "Free — mai preempt altri, primo a essere evicted"
```

---

## Tenant onboarding automation

### Pipeline GitOps per provisioning tenant

L'approccio più maturo per l'onboarding tenant utilizza GitOps: la creazione di un nuovo tenant corrisponde a un commit in un repository di configurazione, che viene riconciliato automaticamente da ArgoCD o Flux.

```
┌──────────────────────────────────────────────────────────┐
│          GITOPS TENANT ONBOARDING PIPELINE                │
│                                                           │
│  1. API Signup → genera tenant config                     │
│  2. Commit → push YAML in repo tenant-configs             │
│  3. ArgoCD/Flux → riconcilia risorse Kubernetes           │
│  4. Crossplane/Terraform → provisiona infra cloud         │
│  5. Smoke tests → verifica connettività e isolamento      │
│  6. Webhook → notifica il tenant che l'ambiente è pronto  │
└──────────────────────────────────────────────────────────┘
```

**Struttura del repository GitOps per tenant:**

```
tenant-configs/
├── base/
│   ├── namespace.yaml
│   ├── resource-quota.yaml
│   ├── limit-range.yaml
│   ├── network-policies/
│   │   ├── default-deny.yaml
│   │   ├── allow-dns.yaml
│   │   └── allow-ingress.yaml
│   ├── rbac/
│   │   ├── role.yaml
│   │   └── rolebinding.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── free/
│   │   ├── quota-patch.yaml
│   │   └── kustomization.yaml
│   ├── pro/
│   │   ├── quota-patch.yaml
│   │   └── kustomization.yaml
│   └── enterprise/
│       ├── quota-patch.yaml
│       ├── vcluster-values.yaml
│       └── kustomization.yaml
└── tenants/
    ├── acme/
    │   ├── kustomization.yaml     # refs: overlays/enterprise
    │   └── tenant-config.yaml
    ├── globex/
    │   ├── kustomization.yaml     # refs: overlays/pro
    │   └── tenant-config.yaml
    └── initech/
        ├── kustomization.yaml     # refs: overlays/free
        └── tenant-config.yaml
```

**ArgoCD ApplicationSet per tenant dinamici:**

```yaml
# argocd-applicationset.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: tenant-apps
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/org/tenant-configs.git
        revision: main
        directories:
          - path: tenants/*
  template:
    metadata:
      name: "tenant-{{path.basename}}"
    spec:
      project: tenants
      source:
        repoURL: https://github.com/org/tenant-configs.git
        targetRevision: main
        path: "{{path}}"
      destination:
        server: https://kubernetes.default.svc
        namespace: "tenant-{{path.basename}}"
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
          - PruneLast=true
```

Ogni nuovo tenant aggiunto come directory nel repository viene automaticamente rilevato dall'ApplicationSet e riconciliato, creando tutte le risorse Kubernetes necessarie senza intervento manuale.

---

## Noisy neighbor prevention — strategie avanzate

### Memory balloon e OOM priority

Il noisy neighbor più insidioso è quello che consuma memoria progressivamente fino a provocare OOM (Out of Memory) kills a cascata. La strategia di difesa combina LimitRange con OOM score adjustment.

```yaml
# Pod con OOM score adjustment per proteggere workload critici
apiVersion: v1
kind: Pod
metadata:
  namespace: tenant-acme
  name: critical-api
  annotations:
    # Kubernetes assegna OOM score basato su:
    # - Guaranteed (requests == limits): score -997 (ultimo a essere killed)
    # - Burstable: score proporzionale al rapporto requests/limits
    # - BestEffort (no requests/limits): score 1000 (primo a essere killed)
spec:
  containers:
    - name: api
      image: registry.example.com/api:v2.1.0
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "500m"         # requests == limits → Guaranteed QoS
          memory: "1Gi"       # Non verrà mai OOM-killed prima di BestEffort/Burstable
```

**Regola operativa:** i workload enterprise devono avere QoS class Guaranteed (requests == limits). I workload free possono essere Burstable. Nessun workload tenant dovrebbe mai essere BestEffort.

### I/O throttling per tenant

Il noisy neighbor su I/O è spesso ignorato. Un tenant che esegue bulk writes su un PersistentVolume condiviso può saturare la bandwidth IOPS dell'intera storage class.

**Mitigazione con StorageClass dedicate per tier:**

```yaml
# StorageClass con IOPS limitate per tier free
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-free-tier
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"              # IOPS baseline per free tier
  throughput: "125"          # MiB/s baseline
  encrypted: "true"
  fsType: ext4

---
# StorageClass con IOPS elevate per enterprise
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io2-enterprise-tier
provisioner: ebs.csi.aws.com
parameters:
  type: io2
  iops: "10000"
  encrypted: "true"
  fsType: ext4
```

---

## Data isolation e compliance GDPR per-tenant

### Requisiti GDPR specifici per multi-tenancy

Il GDPR (Regolamento UE 2016/679) non prescrive un'architettura di isolamento specifica, ma impone requisiti outcome-based che hanno implicazioni architetturali dirette:

1. **Articolo 17 — Diritto alla cancellazione:** devi poter identificare, estrarre e cancellare tutti i dati personali di un tenant su richiesta. Con RLS in shared tables, questo richiede query di cancellazione accurate con verifica post-operazione. Con database-per-tenant, è sufficiente un DROP DATABASE.

2. **Articolo 20 — Portabilità dei dati:** devi poter esportare tutti i dati di un tenant in formato strutturato e machine-readable. Con schema-per-tenant, un `pg_dump -n tenant_schema` soddisfa il requisito. Con RLS, serve un export filtrato per tenant_id su ogni tabella.

3. **Articolo 32 — Misure tecniche appropriate:** la crittografia per-tenant con chiavi KMS dedicate è considerata best practice. La rotazione delle chiavi deve essere indipendente per tenant.

4. **Articolo 33 — Notifica data breach:** in caso di breach, devi poter determinare esattamente quali tenant sono stati impattati. L'audit logging con tenant context è prerequisito.

**Automazione right-to-erasure per tenant:**

```python
# gdpr_erasure.py — cancellazione certificata per tenant

import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass

@dataclass
class ErasureReport:
    tenant_id: str
    timestamp_utc: str
    tables_processed: list[str]
    rows_deleted: dict[str, int]
    verification_hash: str
    compliant: bool

class GDPRErasureEngine:
    """
    Esegue cancellazione GDPR-compliant per un tenant con:
    - Audit trail immutabile della cancellazione
    - Verifica post-cancellazione che nessun dato residuo esista
    - Hash crittografico del report per integrità
    """

    TENANT_TABLES = [
        "audit_logs", "order_items", "orders",
        "documents", "users", "products",
        "invoices", "payments", "sessions",
    ]

    def execute_erasure(self, tenant_id: str) -> ErasureReport:
        timestamp = datetime.now(timezone.utc).isoformat()
        rows_deleted = {}

        # Pre-cancellazione: conta record per tabella
        for table in self.TENANT_TABLES:
            count_before = self._count_rows(table, tenant_id)
            rows_deleted[table] = count_before

        # Esecuzione cancellazione in transazione
        self._delete_tenant_data(tenant_id)

        # Post-cancellazione: verifica zero residui
        compliant = True
        for table in self.TENANT_TABLES:
            count_after = self._count_rows(table, tenant_id)
            if count_after > 0:
                compliant = False

        # Genera hash del report per integrità
        report_content = f"{tenant_id}|{timestamp}|{rows_deleted}|{compliant}"
        verification_hash = hashlib.sha256(report_content.encode()).hexdigest()

        report = ErasureReport(
            tenant_id=tenant_id,
            timestamp_utc=timestamp,
            tables_processed=self.TENANT_TABLES,
            rows_deleted=rows_deleted,
            verification_hash=verification_hash,
            compliant=compliant,
        )

        # Registra il report nell'audit log immutabile (append-only)
        self._log_erasure_report(report)

        return report
```

### Crittografia per-tenant con envelope encryption

Ogni tenant utilizza una chiave KMS dedicata. I dati vengono crittografati con una data key generata dalla chiave KMS del tenant (envelope encryption). La compromissione di una chiave impatta solo quel tenant.

```
┌──────────────────────────────────────────────────┐
│          ENVELOPE ENCRYPTION PER-TENANT          │
│                                                  │
│  KMS Key (tenant-acme)                           │
│  └── genera Data Key (plaintext + encrypted)     │
│       └── Data Key plaintext crittografa i dati  │
│       └── Data Key encrypted salvato con i dati  │
│       └── Data Key plaintext scartato dalla RAM  │
│                                                  │
│  Decrypt flow:                                   │
│  1. Leggi Data Key encrypted dal record          │
│  2. Chiedi a KMS di decrittare la Data Key       │
│     (KMS verifica IAM policy per tenant)         │
│  3. Usa Data Key plaintext per decrittare dati   │
│  4. Scarta Data Key plaintext dalla RAM          │
└──────────────────────────────────────────────────┘
```

---

## Cost allocation per tenant — strategie avanzate

### Costi condivisi e unità di allocazione

In un modello pool, molte risorse sono condivise e non direttamente attribuibili a un singolo tenant. La strategia di allocazione richiede tre categorie:

1. **Costi diretti:** risorse taggabili con TenantId (database dedicato, namespace CPU/memory, storage dedicato).
2. **Costi condivisi proporzionali:** risorse condivise allocate in proporzione all'utilizzo (API gateway, load balancer, shared cache).
3. **Costi piattaforma:** infrastruttura del control plane ripartita equamente o per tier (Kubernetes control plane, monitoring, CI/CD, team di piattaforma).

```python
# cost_model.py — modello di costo per tenant

from dataclasses import dataclass

@dataclass
class TenantCostBreakdown:
    tenant_id: str
    tier: str
    direct_costs_usd: float        # Risorse dedicate
    proportional_costs_usd: float  # Quota proporzionale shared
    platform_costs_usd: float      # Quota fissa piattaforma
    total_usd: float

class TenantCostModel:
    """
    Calcola il costo totale per tenant combinando:
    - Costi diretti (da tag AWS / label Kubernetes)
    - Costi proporzionali (da metriche di utilizzo)
    - Costi piattaforma (fisso per tier)
    """

    PLATFORM_COST_PER_TIER = {
        "enterprise": 500.00,   # Quota fissa piattaforma
        "pro": 100.00,
        "free": 25.00,
    }

    def calculate(
        self,
        tenant_id: str,
        tier: str,
        direct_costs: float,
        usage_ratio: float,       # Proporzione utilizzo risorse condivise
        total_shared_costs: float,
    ) -> TenantCostBreakdown:
        proportional = total_shared_costs * usage_ratio
        platform = self.PLATFORM_COST_PER_TIER.get(tier, 25.0)

        return TenantCostBreakdown(
            tenant_id=tenant_id,
            tier=tier,
            direct_costs_usd=round(direct_costs, 2),
            proportional_costs_usd=round(proportional, 2),
            platform_costs_usd=platform,
            total_usd=round(direct_costs + proportional + platform, 2),
        )
```

### FinOps per-tenant dashboard

```yaml
# Grafana dashboard provisioning per tenant cost visibility
# Datasource: Kubecost API + AWS Cost Explorer

# Prometheus recording rules per tenant CPU/memory cost
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: tenant-cost-rules
  namespace: monitoring
spec:
  groups:
    - name: tenant-costs
      interval: 5m
      rules:
        - record: tenant:container_cpu_usage_seconds:rate5m
          expr: |
            sum by (namespace) (
              rate(container_cpu_usage_seconds_total{
                namespace=~"tenant-.*"
              }[5m])
            )
        - record: tenant:container_memory_usage_bytes:avg5m
          expr: |
            sum by (namespace) (
              avg_over_time(container_memory_working_set_bytes{
                namespace=~"tenant-.*"
              }[5m])
            )
        - record: tenant:estimated_hourly_cost_usd
          expr: |
            (tenant:container_cpu_usage_seconds:rate5m * 0.0325)  # $/core/hour
            +
            (tenant:container_memory_usage_bytes:avg5m / 1073741824 * 0.0045)  # $/GiB/hour
```

---

## Monitoring e observability per tenant

### Stack di osservabilità multi-tenant

In un ambiente multi-tenant, le metriche, i log e le trace devono essere isolate per tenant per evitare data leakage e permettere troubleshooting mirato. Lo stack tipico utilizza label/header tenant su ogni segnale.

**Architettura observability multi-tenant:**

```
┌──────────────────────────────────────────────────────────┐
│          MULTI-TENANT OBSERVABILITY STACK                 │
│                                                           │
│  Metrics (Prometheus/Thanos)                              │
│  ├── Label: tenant_id su ogni metrica                     │
│  ├── Recording rules aggregate per tenant                 │
│  └── Alert rules con tenant context                       │
│                                                           │
│  Logs (Loki)                                              │
│  ├── Header X-Scope-OrgID = tenant_id                     │
│  ├── Isolamento nativo per tenant (multi-tenancy Loki)    │
│  └── Retention policy configurabile per tenant            │
│                                                           │
│  Traces (Tempo/Jaeger)                                    │
│  ├── Attributo tenant.id su ogni span                     │
│  ├── Sampling rate configurabile per tier                 │
│  └── Trace duration alerts per tenant                     │
│                                                           │
│  Dashboards (Grafana)                                     │
│  ├── Org separate per tenant enterprise                   │
│  ├── Dashboard template con variabile $tenant_id          │
│  └── RBAC: ogni tenant vede solo i propri dati            │
└──────────────────────────────────────────────────────────┘
```

**Prometheus relabeling per tenant context:**

```yaml
# ServiceMonitor con tenant label injection
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: tenant-app-metrics
  namespace: monitoring
spec:
  namespaceSelector:
    matchNames:
      - tenant-acme
      - tenant-globex
  selector:
    matchLabels:
      app.kubernetes.io/monitored: "true"
  endpoints:
    - port: metrics
      interval: 30s
      relabelings:
        - sourceLabels: [__meta_kubernetes_namespace]
          regex: "tenant-(.*)"
          targetLabel: tenant_id
          replacement: "$1"
        - sourceLabels: [__meta_kubernetes_pod_label_tier]
          targetLabel: tenant_tier
```

**Alert per-tenant con soglie differenziate:**

```yaml
# PrometheusRule con alert per tenant
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: tenant-alerts
  namespace: monitoring
spec:
  groups:
    - name: tenant-sla-alerts
      rules:
        - alert: TenantHighErrorRate
          expr: |
            (
              sum by (tenant_id) (
                rate(http_requests_total{status=~"5..", namespace=~"tenant-.*"}[5m])
              )
              /
              sum by (tenant_id) (
                rate(http_requests_total{namespace=~"tenant-.*"}[5m])
              )
            ) > 0.01
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Tenant {{ $labels.tenant_id }} error rate > 1%"
            runbook: "https://runbooks.internal/tenant-error-rate"

        - alert: TenantHighLatency
          expr: |
            histogram_quantile(0.99,
              sum by (tenant_id, le) (
                rate(http_request_duration_seconds_bucket{namespace=~"tenant-.*"}[5m])
              )
            ) > 2.0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Tenant {{ $labels.tenant_id }} P99 latency > 2s"
```

---

## Multi-tenant CI/CD

### Isolation delle pipeline per tenant

In un ambiente SaaS multi-tenant, le pipeline CI/CD devono garantire che il codice, i secret e gli artefatti di un tenant non siano accessibili da un altro. Il pattern architetturale più sicuro separa le pipeline in tre livelli:

1. **Pipeline piattaforma (shared):** build dell'applicazione SaaS core, tests, deploy dell'infrastruttura comune. Nessun dato tenant-specific.

2. **Pipeline tenant config (per-tenant):** applica configurazioni, feature flags, customizzazioni per tenant singolo. Accede solo ai secret del proprio tenant.

3. **Pipeline tenant infra (per-tenant enterprise):** provisiona risorse dedicate per tenant enterprise (database, VPC, cluster). Accede solo alle credenziali del proprio tenant.

**Isolation dei secret per tenant nella CI/CD:**

```yaml
# GitHub Actions — secret scoping per tenant
name: Deploy Tenant Config
on:
  push:
    paths:
      - 'tenants/*/config.yaml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        tenant: [acme, globex, initech]
    environment: tenant-${{ matrix.tenant }}   # Environment separato per tenant
    steps:
      - uses: actions/checkout@v4
      - name: Deploy tenant config
        env:
          # Ogni environment ha i propri secret — non accessibili cross-tenant
          TENANT_DB_URL: ${{ secrets.DB_URL }}
          TENANT_API_KEY: ${{ secrets.API_KEY }}
        run: |
          ./scripts/deploy-tenant-config.sh ${{ matrix.tenant }}
```

**Artefatti build isolati per tenant:**

```yaml
# Evitare che artefatti di build di un tenant contaminino un altro
# Ogni tenant ha il proprio path nel registry di container
# 123456789012.dkr.ecr.eu-west-1.amazonaws.com/acme/api:v2.1.0
# 123456789012.dkr.ecr.eu-west-1.amazonaws.com/globex/api:v2.1.0

# ECR repository policy per isolation
# Ogni tenant ha accesso solo al proprio prefisso nel registry
```

### Test di isolation nella CI/CD

Ogni pipeline di deploy deve includere test automatici di cross-tenant isolation come gate prima del merge:

```bash
#!/bin/bash
# ci-isolation-test.sh — eseguito in ogni pipeline di deploy

set -euo pipefail

echo "=== Test di isolamento cross-tenant ==="

# 1. Verifica che RLS sia attivo su tutte le tabelle tenant
psql "$DB_URL" -c "
  SELECT tablename, rowsecurity, relforcerowsecurity
  FROM pg_tables t
  JOIN pg_class c ON c.relname = t.tablename
  WHERE schemaname = 'public'
    AND tablename IN ('orders','products','users','invoices')
    AND (NOT rowsecurity OR NOT relforcerowsecurity)
" | grep -q "0 rows" || { echo "FAIL: RLS mancante"; exit 1; }

# 2. Verifica NetworkPolicy default-deny in ogni namespace tenant
for ns in $(kubectl get ns -l tenant.saas.io/id -o name); do
  np_count=$(kubectl get networkpolicy -n "${ns##*/}" --no-headers 2>/dev/null | wc -l)
  if [ "$np_count" -lt 1 ]; then
    echo "FAIL: Namespace ${ns##*/} senza NetworkPolicy"
    exit 1
  fi
done

# 3. Verifica ResourceQuota in ogni namespace tenant
for ns in $(kubectl get ns -l tenant.saas.io/id -o name); do
  rq_count=$(kubectl get resourcequota -n "${ns##*/}" --no-headers 2>/dev/null | wc -l)
  if [ "$rq_count" -lt 1 ]; then
    echo "FAIL: Namespace ${ns##*/} senza ResourceQuota"
    exit 1
  fi
done

echo "=== Tutti i test di isolamento superati ==="
```

---

## Security boundaries e blast radius

### Defense in depth per multi-tenancy

La sicurezza multi-tenant non si basa su un singolo meccanismo ma su strati sovrapposti. La compromissione di uno strato non deve consentire accesso cross-tenant.

```
┌──────────────────────────────────────────────────────────┐
│          DEFENSE IN DEPTH — MULTI-TENANT                  │
│                                                           │
│  Layer 1: Identity & Authentication                       │
│  ├── JWT con tenant_id firmato dall'IdP                   │
│  ├── mTLS tra servizi (service mesh)                      │
│  └── API key scoping per tenant                           │
│                                                           │
│  Layer 2: Authorization                                   │
│  ├── RBAC Kubernetes per namespace                        │
│  ├── IAM permissions boundary per tenant                  │
│  ├── OPA/Kyverno admission control                        │
│  └── Application-level tenant context validation          │
│                                                           │
│  Layer 3: Network                                         │
│  ├── NetworkPolicy default-deny cross-namespace           │
│  ├── Cilium L7 policy per HTTP path                       │
│  ├── Service mesh AuthorizationPolicy                     │
│  └── VPC isolation (per silo/enterprise)                  │
│                                                           │
│  Layer 4: Data                                            │
│  ├── RLS / schema separation / database-per-tenant        │
│  ├── Per-tenant KMS encryption keys                       │
│  ├── Backup isolation per tenant                          │
│  └── Audit log con tenant context                         │
│                                                           │
│  Layer 5: Compute                                         │
│  ├── ResourceQuota / LimitRange per namespace             │
│  ├── Pod Security Standards (restricted)                  │
│  ├── Sandbox runtime (gVisor/Kata) per workload untrusted │
│  └── Seccomp profiles personalizzati                      │
│                                                           │
│  Layer 6: Observability & Detection                       │
│  ├── Falco per runtime threat detection                   │
│  ├── Cross-tenant access alerts                           │
│  ├── Canary tenant per leak detection                     │
│  └── Audit trail immutabile                               │
└──────────────────────────────────────────────────────────┘
```

### Vulnerability: CVE-2024-10976 e RLS bypass

Nel 2024, CVE-2024-10976 ha dimostrato che le policy RLS di PostgreSQL potevano fallire in specifiche condizioni di connection pooling, permettendo a query di un tenant di restituire righe appartenenti a un altro tenant. Questa vulnerabilità evidenzia perché RLS da solo non è sufficiente.

**Mitigazioni:**

1. Aggiornare PostgreSQL alla versione patchata (16.6+, 15.10+, 14.15+).
2. Aggiungere validazione a livello applicativo del tenant_id su ogni risultato di query.
3. Usare `SET LOCAL` (transaction-scoped) invece di `SET` (session-scoped) per il tenant context.
4. Implementare test di isolation automatici che verificano cross-tenant leakage dopo ogni deploy.
5. Monitorare con canary tenant: un tenant di test con dati noti che viene periodicamente interrogato per verificare che non compaiano dati di altri tenant.

### Threat model per multi-tenant SaaS

| Threat | Attack Vector | Mitigazione |
|---|---|---|
| Cross-tenant data leak | Bug in query filter, RLS bypass | RLS + application filter + canary test |
| Tenant impersonation | JWT forgery, header spoofing | Firma JWT crittografica, validazione server-side |
| Noisy neighbor DoS | CPU/memory exhaustion | ResourceQuota, rate limiting, PriorityClass |
| Privilege escalation | Container escape, kernel exploit | gVisor/Kata, PodSecurityStandard restricted |
| Lateral movement | Network access tra namespace | NetworkPolicy deny, Cilium L7, service mesh |
| Supply chain attack | Immagine container compromessa | Registry whitelist OPA, image signing, SBoM |
| Insider threat | Admin accesso a dati tenant | Break-glass audit, per-tenant encryption |
| Data exfiltration | Egress non controllato | NetworkPolicy egress deny, proxy egress |

---

## Multi-tenant SaaS architecture patterns

### Pattern 1 — Control plane / data plane separation

Il pattern architetturale fondamentale per SaaS multi-tenant separa il control plane (gestione tenant, billing, monitoring) dal data plane (workload dei tenant). Il control plane è singleton; il data plane è replicato per tenant o tier.

```
┌────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                        │
│          (singleton, shared, always running)             │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │ Identity │ │ Billing  │ │ Tenant   │ │ Monitoring│ │
│  │ Provider │ │ Service  │ │ Registry │ │ & Alerts  │ │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘ │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ Config   │ │ Feature  │ │ Onboard  │               │
│  │ Service  │ │ Flags    │ │ Pipeline │               │
│  └──────────┘ └──────────┘ └──────────┘               │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                     DATA PLANE                          │
│          (replicated per tenant/tier/cell)               │
│                                                         │
│  Cell EU-1            Cell US-1           Cell AP-1     │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│  │ Tenants A-M  │    │ Tenants N-Z  │    │ Tenants AP ││
│  │ App Servers  │    │ App Servers  │    │ App Servers││
│  │ Database     │    │ Database     │    │ Database   ││
│  │ Cache        │    │ Cache        │    │ Cache      ││
│  └──────────────┘    └──────────────┘    └────────────┘│
└────────────────────────────────────────────────────────┘
```

### Pattern 2 — Sidecar per tenant context injection

Un pattern operativo efficace utilizza un sidecar container o init container per iniettare il tenant context in ogni pod, garantendo che ogni richiesta sia sempre associata al tenant corretto indipendentemente dal codice applicativo.

```yaml
# Sidecar per tenant context injection via envoy proxy
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: tenant-acme
  name: api-with-tenant-sidecar
spec:
  template:
    spec:
      containers:
        - name: app
          image: registry.example.com/api:v2.1.0
          ports:
            - containerPort: 8080
          env:
            - name: TENANT_ID
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
        - name: tenant-proxy
          image: registry.example.com/tenant-proxy:v1.0.0
          ports:
            - containerPort: 8443
          env:
            - name: UPSTREAM_PORT
              value: "8080"
            - name: TENANT_ID
              valueFrom:
                fieldRef:
                  fieldPath: metadata.labels['tenant']
          # Il proxy:
          # 1. Valida il JWT e estrae tenant_id
          # 2. Verifica che il tenant_id del JWT corrisponda al namespace
          # 3. Inietta header X-Verified-Tenant-Id
          # 4. Rifiuta richieste con tenant mismatch
```

### Pattern 3 — Feature flags per-tenant

Le customizzazioni per-tenant vengono gestite tramite feature flags piuttosto che branch di codice separati, mantenendo un singolo codebase con comportamento configurabile.

```python
# tenant_features.py — feature flag resolution per tenant

from dataclasses import dataclass, field

@dataclass(frozen=True)
class TenantFeatureSet:
    tenant_id: str
    tier: str
    features: dict[str, bool] = field(default_factory=dict)
    limits: dict[str, int] = field(default_factory=dict)
    ui_config: dict[str, str] = field(default_factory=dict)

# Configurazione feature per tier con override per tenant
DEFAULT_FEATURES = {
    "free": {
        "features": {
            "advanced_analytics": False,
            "custom_domain": False,
            "api_access": True,
            "webhook_integrations": False,
            "sso": False,
            "audit_log": False,
        },
        "limits": {
            "max_users": 5,
            "max_api_calls_per_day": 1000,
            "max_storage_gb": 1,
            "max_projects": 3,
        },
    },
    "pro": {
        "features": {
            "advanced_analytics": True,
            "custom_domain": True,
            "api_access": True,
            "webhook_integrations": True,
            "sso": False,
            "audit_log": True,
        },
        "limits": {
            "max_users": 50,
            "max_api_calls_per_day": 50000,
            "max_storage_gb": 50,
            "max_projects": 50,
        },
    },
    "enterprise": {
        "features": {
            "advanced_analytics": True,
            "custom_domain": True,
            "api_access": True,
            "webhook_integrations": True,
            "sso": True,
            "audit_log": True,
        },
        "limits": {
            "max_users": -1,          # Illimitato
            "max_api_calls_per_day": -1,
            "max_storage_gb": 1000,
            "max_projects": -1,
        },
    },
}
```

---

## Modelli

| Modello | Isolation | Cost | Use case |
|---|---|---|---|
| Single namespace | low | low | dev/test |
| Multi-namespace | medium | low | mid-tier SaaS |
| Multi-cluster | high | high | mission-critical |
| Virtual cluster | medium-high | medium | dev environments |
| Capsule tenant | medium | low | SaaS con >100 tenant |
| Cilium + service mesh | medium-high | medium | compliance-heavy |
| Cell-based + shard | high | medium-high | large-scale SaaS |

---

## Esercizi

1. **Lab — Namespace isolation.** Create Tenant-A + Tenant-B namespaces with ResourceQuota; apply NetworkPolicy deny cross-namespace; verify with `kubectl exec` curl tests between pods.

2. **Lab — RLS implementation.** Set up a PostgreSQL database with `tenant_id` column, enable RLS, create policies, verify that setting different `app.current_tenant_id` values filters correctly, and attempt to insert rows for the wrong tenant.

3. **Lab — OPA/Gatekeeper.** Deploy Gatekeeper, create a ConstraintTemplate that requires a `tenant` label on all pods, deploy a pod without the label and verify it is rejected, then deploy with the label and verify it is accepted.

4. **Lab — Cross-tenant penetration test.** Use the `test_tenant_isolation.py` test suite. Extend it with IDOR tests for additional endpoints, header spoofing, and path traversal attacks.

5. **Lab — Noisy neighbor simulation.** Deploy a CPU-intensive workload in one tenant namespace, observe impact on co-located tenants, then apply ResourceQuota and LimitRange and verify containment.

6. **Lab — Cost allocation.** Tag all resources in a test environment with `TenantId`, query AWS Cost Explorer (or Kubecost) to generate per-tenant cost reports.

7. **Stretch — vCluster.** Set up vCluster on a shared Kubernetes cluster; tenant gets a separate control plane. Deploy workloads inside the virtual cluster and verify isolation from the host cluster.

8. **Stretch — Cell-based architecture.** Design a cell routing layer that maps tenants to cells. Simulate a cell failure and verify that tenants in other cells are unaffected.

9. **Stretch — Tenant migration.** Implement the `_free_to_pro` migration path: copy data from RLS shared tables to a dedicated schema, update routing, verify data integrity, clean up.

---

## Troubleshooting — 20 problemi

### 1. Cross-tenant data leak in API responses

**Symptoms:** Tenant A sees Tenant B's data in list endpoints.

**Root causes:**
- Missing `WHERE tenant_id = ...` clause in a query.
- RLS policy not enabled on a newly created table.
- Application bypassing RLS by using a superuser connection.

**Fix:**
```sql
-- Verify RLS is enabled
SELECT relname, relrowsecurity, relforcerowsecurity
FROM pg_class WHERE relname = 'new_table';

-- Enable if missing
ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;
ALTER TABLE new_table FORCE ROW LEVEL SECURITY;

-- Add policy
CREATE POLICY tenant_isolation ON new_table
    USING (tenant_id = current_setting('app.current_tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));
```

### 2. Noisy neighbor causes latency spikes for all tenants

**Symptoms:** P99 latency increases across all tenants; one tenant's pods consume disproportionate CPU/memory.

**Fix:**
```yaml
# Apply stricter ResourceQuota to the offending tenant
apiVersion: v1
kind: ResourceQuota
metadata:
  namespace: tenant-noisy
  name: emergency-quota
spec:
  hard:
    limits.cpu: "4"
    limits.memory: "8Gi"
    pods: "10"
```

### 3. Tenant cannot reach services after NetworkPolicy applied

**Symptoms:** All cross-namespace traffic blocked, including DNS and ingress.

**Fix:** Ensure DNS and ingress egress rules exist alongside the default-deny. See the NetworkPolicy examples above — `allow-dns` and `allow-ingress-controller` must accompany `default-deny-all`.

### 4. RLS bypass via connection pooling

**Symptoms:** Tenant context from a previous request leaks to the next request through a connection pool.

**Root cause:** Connection pool reuses connections without resetting `app.current_tenant_id`.

**Fix:**
```python
# Always reset tenant context when returning connection to pool
@contextmanager
def tenant_connection(tenant_id: str):
    conn = pool.getconn()
    try:
        conn.execute("SELECT set_tenant_context(%s)", (tenant_id,))
        yield conn
        conn.commit()
    finally:
        conn.execute("RESET app.current_tenant_id")
        pool.putconn(conn)
```

### 5. Gatekeeper constraint not enforcing on existing resources

**Symptoms:** Constraint deployed but pre-existing pods without required labels continue running.

**Root cause:** Gatekeeper only enforces on admission (create/update), not on existing resources.

**Fix:** Use `gatekeeper audit` to find violations, then remediate:
```bash
kubectl get k8srequiredtenantlabel require-tenant-label -o json | jq '.status.violations'
```

### 6. Tenant subdomain DNS resolution fails

**Symptoms:** New tenant's subdomain returns NXDOMAIN.

**Fix:** Verify wildcard DNS record exists and TLS certificate covers `*.saas.example.com`. Check that the ingress controller is configured to handle wildcard hosts.

### 7. Tenant-scoped IAM role cannot access its own resources

**Symptoms:** `AccessDenied` errors even for correctly tagged resources.

**Root cause:** Permissions boundary is too restrictive, or resource tags do not match the session tag condition.

**Fix:** Check that `aws:ResourceTag/TenantId` matches `aws:PrincipalTag/TenantId` and that the permissions boundary allows the specific API actions.

### 8. Schema migration fails for one tenant

**Symptoms:** Migration tool errors on one tenant's schema but succeeds on others.

**Root cause:** Tenant schema has custom modifications, or previous migration was partially applied.

**Fix:** Run migrations idempotently. Use `IF NOT EXISTS` for DDL. Track migration state per schema:
```sql
SELECT * FROM tenant_acme.schema_migrations ORDER BY version DESC LIMIT 5;
```

### 9. Resource quota prevents legitimate scaling

**Symptoms:** HPA cannot scale pods because ResourceQuota limit is reached.

**Fix:** Review quota values against actual usage patterns. Increase quota for growing tenants:
```bash
kubectl patch resourcequota tenant-quota -n tenant-acme \
  --type merge -p '{"spec":{"hard":{"pods":"100","limits.cpu":"32"}}}'
```

### 10. JWT tenant claim is missing after identity provider update

**Symptoms:** Tenant resolution fails with "Missing tenant_id claim" after an IdP configuration change.

**Fix:** Verify that the IdP token customization includes the `tenant_id` claim. Check the IdP admin console for claim mapping rules. Test with `jwt.io` to inspect the token payload.

### 11. Cross-tenant network traffic detected in flow logs

**Symptoms:** VPC flow logs show traffic between tenant VPCs that should be isolated.

**Root cause:** Transit Gateway route table allows tenant-to-tenant routing, or security group rules are too permissive.

**Fix:** Audit Transit Gateway route tables — tenant attachments should only route to shared-services, not to each other. Remove cross-tenant security group references.

### 12. Cost allocation shows "untagged" resources consuming 30% of budget

**Symptoms:** Cost Explorer shows large untagged spend that cannot be attributed to any tenant.

**Fix:** Enable the SCP that denies resource creation without `TenantId` tag. Retroactively tag existing resources using AWS Tag Editor. Set up AWS Config rules to detect untagged resources.

### 13. Tenant data appears in wrong region (data residency violation)

**Symptoms:** EU tenant's data found in a US-region S3 bucket or database.

**Root cause:** Application routing did not enforce region constraint, or a batch job used the global endpoint.

**Fix:** Add region enforcement at the application layer. Use S3 bucket policies that deny `PutObject` from non-allowed regions. Audit CloudTrail for cross-region API calls filtered by tenant tag.

### 14. Sandbox runtime (gVisor) causes application crashes

**Symptoms:** Application works with default `runc` but crashes with gVisor. Syscall errors in logs.

**Root cause:** gVisor does not support all Linux syscalls. The application uses an unsupported syscall.

**Fix:** Check gVisor compatibility list. Profile the application's syscall usage with `strace`. Consider Kata Containers (full kernel) for broader syscall compatibility.

### 15. Connection pool exhaustion in schema-per-tenant model

**Symptoms:** "Too many connections" errors as tenant count grows.

**Root cause:** Each tenant requires a separate `search_path` setting, which reduces connection sharing.

**Fix:** Use `SET LOCAL search_path` (transaction-scoped) instead of `SET search_path` (session-scoped), enabling better connection reuse. Consider PgBouncer in transaction mode.

### 16. Tenant onboarding fails at compute provisioning step

**Symptoms:** Namespace creation succeeds but pod scheduling fails.

**Root cause:** Cluster has insufficient capacity; node auto-scaler has not yet provisioned new nodes; or the tenant's PriorityClass is too low to preempt.

**Fix:** Check node capacity: `kubectl describe nodes | grep -A5 "Allocated resources"`. Verify cluster autoscaler is healthy. Increase the PriorityClass if the tenant tier warrants it.

### 17. Audit logs missing tenant context

**Symptoms:** Security audit finds log entries without `tenant_id`, making forensic analysis impossible.

**Fix:** Add tenant context to structured logging at the middleware level:
```python
import structlog

logger = structlog.get_logger()

# In middleware, bind tenant to logger context
logger = logger.bind(tenant_id=resolved_tenant_id, tenant_tier=tier)
```

### 18. Tenant API key rotation breaks integrations

**Symptoms:** After rotating an API key, the tenant's webhook and CI/CD integrations fail.

**Fix:** Implement dual-key rotation: issue a new key while keeping the old key active for a grace period (e.g., 24 hours). Notify the tenant before the old key is deactivated.

### 19. OPA policy update causes mass pod rejection

**Symptoms:** After updating a Gatekeeper constraint, all new pod deployments are rejected cluster-wide.

**Fix:** Use `dryrun` enforcement action first, then audit, then `deny`:
```yaml
spec:
  enforcementAction: dryrun  # Start here
  # enforcementAction: warn  # Then move to warn
  # enforcementAction: deny  # Finally enforce
```

### 20. Tenant backup restoration overwrites another tenant's data

**Symptoms:** Restoring a tenant's database backup in a shared environment clobbers other tenants' data.

**Root cause:** Backup was a full-database backup in a schema-per-tenant model, and the restore was not scoped.

**Fix:** Use schema-scoped backups and restores:
```bash
# Backup single tenant schema
pg_dump -n tenant_acme -Fc dbname > tenant_acme_backup.dump

# Restore single tenant schema (drop and recreate only that schema)
pg_restore -n tenant_acme --clean --if-exists -d dbname tenant_acme_backup.dump
```

---

## FAQ — 20 domande e risposte

### 1. When should I choose silo over pool?

When regulatory, contractual, or security requirements mandate physical resource separation. Also when a single tenant's blast radius must not affect others — for example, government or healthcare workloads. The higher per-tenant cost is justified by reduced risk.

### 2. Is RLS sufficient for data isolation?

For most SaaS applications serving non-regulated workloads, yes. PostgreSQL RLS is well-tested and performant with proper indexing. However, RLS is application-layer enforcement — a misconfigured connection (e.g., superuser without FORCE RLS) bypasses it entirely. Use it as one layer in defense-in-depth, not the only layer.

### 3. How many tenants can a single Kubernetes cluster support?

Depends on cluster size, tenant resource requirements, and isolation model. With namespace-per-tenant: hundreds to low thousands of namespaces are practical with sufficient nodes. With vCluster: dozens to hundreds per host cluster. Key bottleneck is the Kubernetes API server — each namespace adds watch overhead.

### 4. Should I use database-per-tenant or schema-per-tenant?

Database-per-tenant gives the strongest isolation and simplest backup/restore but highest cost. Schema-per-tenant is a practical middle ground for up to ~1,000 tenants. Beyond that, RLS with shared tables scales better. Match to your tenant count, compliance requirements, and operational budget.

### 5. How do I prevent one tenant from consuming all database connections?

Use PostgreSQL `CONNECTION LIMIT` per role, a connection pooler like PgBouncer, and application-level connection quotas per tenant. Monitor with `pg_stat_activity` grouped by role.

### 6. What is the blast radius of a pool-model failure?

In the worst case: all tenants. A bug in the application's tenant filtering logic, a database crash, or a shared-service outage affects every tenant on the platform. Mitigate with bulkheading (separate pools per tier), cell-based architecture, and automated cross-tenant testing.

### 7. How do I handle tenant-specific customizations?

Use a configuration layer that maps tenant_id to feature flags, custom branding, and overridden defaults. Store tenant config in a key-value store or database table — not in application code. For compute-level customization (custom containers), use the bridge model.

### 8. How do I implement per-tenant rate limiting?

Use a token bucket or sliding window algorithm keyed by tenant_id. Store rate limit state in Redis or a similar low-latency store. Different tiers get different limits. Return `429 Too Many Requests` with `Retry-After` header. See the `TenantRateLimiter` example above.

### 9. Can I use Kubernetes NetworkPolicy alone for tenant isolation?

NetworkPolicy provides L3/L4 isolation (IP + port) but not L7 (HTTP path, headers). It prevents cross-namespace network traffic, which is the most important boundary. For L7 isolation (e.g., path-based routing), use a service mesh (Istio, Linkerd) on top.

### 10. How do I handle DNS for thousands of tenant subdomains?

Use a wildcard DNS record (`*.saas.example.com → load balancer`) with a wildcard TLS certificate. For tenants with custom domains, use a certificate manager that handles dynamic TLS provisioning (e.g., cert-manager with Let's Encrypt).

### 11. What happens to shared services (auth, billing) in a silo model?

Shared services remain centralized. The silo model isolates the data plane (compute, database, storage) while keeping the control plane (auth, billing, monitoring, management) shared. Cross-account access to shared services uses IAM roles, VPC endpoints, or API gateways.

### 12. How do I do schema migrations across all tenant schemas?

Use a migration runner that iterates over all tenant schemas:
```bash
for schema in $(psql -At -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'"); do
  psql -c "SET search_path TO ${schema}; \i migration_042.sql"
done
```
Run migrations idempotently (IF NOT EXISTS / IF EXISTS). Consider parallel execution for large tenant counts, with rollback capability per schema.

### 13. How do I test that my RLS policies are correct?

Three levels: (1) Unit tests that set different tenant contexts and verify query results. (2) Integration tests that attempt cross-tenant access patterns (IDOR, SQL injection, privilege escalation). (3) Automated audit that checks `pg_policies` and `pg_class` for missing RLS on tenant tables.

### 14. What is the cost overhead of silo vs pool?

Rough guidelines: silo costs 3-10x more per tenant than pool, depending on the minimum resource stack per tenant. A dedicated RDS `db.t4g.micro` + a Fargate task + a VPC costs ~$50-100/month per tenant regardless of usage. In pool, the marginal cost of adding a tenant is near zero (a database row and a namespace).

### 15. How do I ensure compliance data residency per tenant?

Map each tenant to a primary and backup region in a routing table. Enforce at multiple layers: (1) Application routing directs API calls to the correct regional deployment. (2) S3 bucket policies deny access from non-allowed regions. (3) Database replication is configured only within allowed regions. (4) SCP restricts the tenant's account to allowed regions.

### 16. Can I mix isolation levels within one product?

Yes — this is the bridge model. Free tenants share a pool (RLS + shared namespace), pro tenants get dedicated schemas and namespaces, enterprise tenants get dedicated accounts or clusters. The routing layer must be tier-aware to direct each tenant to the correct infrastructure.

### 17. How do I monitor cross-tenant leakage in production?

Deploy canary tenants (test tenants with known data). Periodically query APIs as canary tenants and verify that only expected data is returned. Alert on any foreign tenant_id in responses. Add tenant_id to all structured logs and audit for mismatches.

### 18. What is the difference between vCluster and a real cluster?

vCluster runs a virtual Kubernetes control plane (API server, controller manager, etcd) inside a namespace of a host cluster. Tenants interact with their virtual API server and see an isolated cluster. Under the hood, pods are synced to the host cluster as regular pods. Isolation is stronger than plain namespaces but weaker than separate physical clusters. Overhead is ~0.5 CPU + 1 GB memory per virtual cluster.

### 19. Should I encrypt data per tenant or use a shared key?

Use per-tenant KMS keys for envelope encryption. This enables: (1) Per-tenant key rotation without affecting others. (2) Tenant-specific key policies (e.g., BYOK for enterprise). (3) Cryptographic isolation — even if one key is compromised, other tenants' data remains encrypted. (4) Compliance auditability — key access logs are per tenant.

### 20. How do I handle tenant-specific SLAs?

Encode SLA commitments in the tenant configuration: uptime target, response time target, support response time. Use these to drive: (1) PriorityClass in Kubernetes (higher priority = less likely to be preempted). (2) Rate limits (higher SLA = higher limits). (3) Redundancy (enterprise gets multi-AZ; free gets single AZ). (4) Monitoring alerts (tighter thresholds for higher-SLA tenants).

---

## Letture

- Kubernetes — Multi-tenancy. https://kubernetes.io/docs/concepts/security/multi-tenancy/
- vCluster. https://www.vcluster.com/
- Kamaji. https://kamaji.clastix.io/
- AWS SaaS Lens — Well-Architected Framework. https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html
- AWS Multi-Tenant SaaS Reference Architecture. https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html
- PostgreSQL Row-Level Security. https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- OPA Gatekeeper. https://open-policy-agent.github.io/gatekeeper/
- gVisor. https://gvisor.dev/docs/
- Kata Containers. https://katacontainers.io/
- Kubernetes Network Policies. https://kubernetes.io/docs/concepts/services-networking/network-policies/
- NIST SP 800-53 AC-4 — Information Flow Enforcement. https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- Kubecost — Kubernetes Cost Monitoring. https://www.kubecost.com/
- Cell-Based Architecture (AWS). https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|---|---|---|
| [05-kubernetes](05-kubernetes.md) | Kubernetes | Namespace, ResourceQuota, NetworkPolicy e RBAC sono le primitive K8s per tenant isolation |
| [13-sicurezza-piattaforme](13-sicurezza-piattaforme.md) | Sicurezza delle Piattaforme | Zero trust, network segmentation e policy enforcement proteggono i confini tra tenant |
| [11-database-management](11-database-management.md) | Database Management | Row-Level Security, schema separation e database-per-tenant sono strategie di data isolation |
| [21-finops-cost-governance](21-finops-cost-governance.md) | FinOps + Cost Governance | Chargeback e showback per tenant richiedono tagging e cost allocation granulare |
| [01-cloud-aws](01-cloud-aws.md) | Cloud AWS | AWS Organizations, SCP, session tag e permissions boundary per isolation a livello account |
| [09-service-mesh](09-service-mesh.md) | Service Mesh | mTLS e authorization policy del service mesh aggiungono isolation L7 tra servizi tenant |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Soft multi-tenancy** | Namespace + RBAC isolation within a shared cluster. |
| **Hard multi-tenancy** | Separate cluster or account per tenant. |
| **ResourceQuota** | Kubernetes object that limits aggregate resource consumption per namespace. |
| **NetworkPolicy** | Kubernetes L3/L4 firewall rules controlling pod-to-pod traffic. |
| **vCluster** | Virtual Kubernetes cluster running inside a host cluster namespace. |
| **Kata Containers** | VM-isolated container runtime providing hardware-level isolation. |
| **gVisor** | User-space kernel sandbox that intercepts and virtualizes syscalls. |
| **Silo model** | Multi-tenancy pattern where each tenant gets dedicated infrastructure resources. |
| **Pool model** | Multi-tenancy pattern where all tenants share infrastructure, separated by application logic. |
| **Bridge model** | Multi-tenancy pattern offering tiered isolation based on customer tier. |
| **Row-Level Security (RLS)** | PostgreSQL feature that filters table rows based on policy rules applied per connection. |
| **Noisy neighbor** | Problem where one tenant's resource usage degrades performance for other tenants on shared infrastructure. |
| **Blast radius** | The maximum scope of impact when a failure, breach, or misconfiguration occurs. |
| **Bulkhead** | Isolation pattern that partitions resources to prevent failure cascade across partitions. |
| **Cell-based architecture** | Infrastructure design where tenants are grouped into independent failure domains (cells). |
| **Permissions boundary** | AWS IAM feature that sets the maximum permissions a role can grant, regardless of its policies. |
| **Service Control Policy (SCP)** | AWS Organizations policy that sets maximum permissions for all accounts in an OU. |
| **Session tag** | AWS STS tag passed at role assumption time, used to scope API calls to specific resources. |
| **Tenant context** | The resolved tenant identity (ID, tier, region) associated with the current request. |
| **Fair queuing** | Scheduling algorithm that allocates shared resources proportionally across competing tenants. |
| **Data residency** | Requirement that data must be stored and processed within specific geographic boundaries. |
| **Envelope encryption** | Pattern where data is encrypted with a data key, and the data key is encrypted with a master key. |
| **IDOR** | Insecure Direct Object Reference — vulnerability where access control does not verify resource ownership. |
| **OPA/Gatekeeper** | Open Policy Agent framework for Kubernetes admission control using Rego policies. |
| **Token bucket** | Rate limiting algorithm that accumulates tokens at a fixed rate and consumes one per request. |
| **Showback** | Practice of showing each team or tenant their infrastructure costs without billing them directly. |
| **Chargeback** | Practice of billing each team or tenant for their actual infrastructure consumption. |
| **Tenant onboarding** | The automated pipeline for provisioning infrastructure and configuration for a new tenant. |
| **Capsule** | Kubernetes multi-tenancy operator che partiziona un singolo cluster in tenant isolati tramite CRD Tenant. |
| **Loft** | Piattaforma di multi-tenancy Kubernetes che combina virtual cluster, sleep mode e self-service per i team. |
| **Cilium** | CNI plugin basato su eBPF per Kubernetes, capace di network policy L3/L4/L7 e osservabilità avanzata. |
| **CiliumNetworkPolicy** | CRD Cilium che estende le NetworkPolicy standard con regole L7 (HTTP path/method) e DNS-aware. |
| **Hubble** | Componente di osservabilità di Cilium che fornisce flow visibility in tempo reale per il traffico di rete. |
| **Syncer** | Componente di vCluster che sincronizza risorse tra il virtual cluster e il namespace host. |
| **Shard** | Partizionamento orizzontale di dati o infrastruttura dove ogni frammento serve un sottoinsieme di tenant. |
| **Branch-per-tenant** | Pattern database serverless dove ogni tenant ottiene un branch isolato (es. Neon), con copy-on-write. |
| **Control plane / data plane** | Separazione architetturale dove il control plane gestisce configurazione e routing, il data plane esegue il workload per-tenant. |
| **Sidecar injection** | Pattern dove un container ausiliario viene iniettato nel pod per aggiungere contesto tenant alle richieste. |
| **Feature flags per-tenant** | Meccanismo che abilita o disabilita funzionalità specifiche in base al tenant e al suo tier di servizio. |
| **CVE-2024-10976** | Vulnerabilità PostgreSQL dove le policy RLS potevano essere bypassate attraverso subquery in specifiche condizioni. |
| **PriorityClass** | Risorsa Kubernetes che assegna priorità ai pod, influenzando scheduling e preemption. |
| **LimitRange** | Risorsa Kubernetes che impone limiti di risorse predefiniti e massimi per container in un namespace. |
| **ApplicationSet** | CRD di ArgoCD che genera automaticamente Application da template, usato per provisioning GitOps per-tenant. |
| **Kustomize overlay** | Meccanismo di personalizzazione Kubernetes che applica patch specifiche per-tenant sopra una base comune. |
| **X-Scope-OrgID** | Header HTTP usato da Loki, Mimir e Tempo per identificare il tenant e garantire isolamento delle query. |
| **Recording rule** | Regola Prometheus che pre-calcola metriche aggregate, riducendo il costo di query in tempo reale. |
| **Kubecost** | Strumento open-source per cost allocation Kubernetes, con breakdown per namespace, label e tenant. |
| **Tenant offboarding** | The process of disabling, exporting, and deleting a tenant's resources and data. |
