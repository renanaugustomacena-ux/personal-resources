---
corso: "Cybersecurity Masterclass"
fase: "Domain 24 — Digital Forensics and Incident Response"
modulo: "24.2"
titolo: "Cloud Forensics, Container Incident Response, and Enterprise IR Playbooks"
versione: "AWS CloudTrail Lake / Azure Monitor 2025 / GCP Audit Logs v2 / Velociraptor 0.76 / Falco 0.39"
livello: "Advanced"
prerequisiti:
  - "Domain 24 Chapter 24A (disk/memory forensics, timeline analysis, IR lifecycle)"
  - "Domain 10 Chapter 10A (cloud provider security architecture, IAM, CloudTrail basics)"
  - "Domain 10 Chapter 10B (container and Kubernetes security fundamentals)"
  - "Working familiarity with at least one major cloud provider CLI"
  - "Basic container operations (Docker build/run/inspect)"
obiettivi:
  - "Perform cloud-native forensic analysis across AWS, Azure, and GCP using CloudTrail, Activity Logs, and Cloud Audit Logs to reconstruct attacker timelines"
  - "Acquire and analyze EC2/Azure VM/GCE disk and memory evidence using EBS snapshots, managed-disk exports, and SSM/LiME remote collection"
  - "Investigate container and Kubernetes incidents through API server audit logs, runtime filesystem capture, and Falco alert correlation"
  - "Execute enterprise IR playbooks for ransomware, BEC, cloud account compromise, supply chain compromise, and insider threat scenarios"
  - "Apply proper cloud evidence handling procedures including chain of custody, ISO 27037 compliance, CLOUD Act jurisdiction analysis, and forensic report writing"
tag: [security, dfir, cloud-forensics, aws, azure, gcp, kubernetes, container-forensics, incident-response, enterprise-ir]
---

# Domain 24, Chapter 24B — Cloud Forensics, Container Incident Response, and Enterprise IR Playbooks

> **After completing this module, the student will be able to:**
>
> 1. Perform cloud-native forensic analysis across AWS, Azure, and GCP using CloudTrail, Activity Logs, and Cloud Audit Logs to reconstruct attacker timelines.
> 2. Acquire and analyze EC2/Azure VM/GCE disk and memory evidence using EBS snapshots, managed-disk exports, and SSM/LiME remote collection.
> 3. Investigate container and Kubernetes incidents through API server audit logs, runtime filesystem capture, and Falco alert correlation.
> 4. Execute enterprise IR playbooks for ransomware, BEC, cloud account compromise, supply chain compromise, and insider threat scenarios.
> 5. Apply proper cloud evidence handling procedures including chain of custody, ISO 27037 compliance, CLOUD Act jurisdiction analysis, and forensic report writing.

> **Scope.** Cloud-native forensics across AWS, Azure, and GCP: CloudTrail deep analysis (event structure, management vs data vs Insights events, cross-account trail aggregation, CloudTrail Lake SQL), GuardDuty finding types and Security Hub integration, VPC Flow Logs V5 forensics and data-exfiltration detection, EC2 disk/memory acquisition via EBS snapshots and SSM/Nitro, S3 object-level logging and bucket policy forensics, Lambda log and X-Ray analysis, IAM credential forensics and access-timeline reconstruction. Azure Activity/Sign-in/Audit Logs, Entra ID forensics (risky sign-ins, Conditional Access evaluation), NSG Flow Logs, Key Vault diagnostics, Microsoft 365 Unified Audit Log and eDiscovery, Azure VM disk acquisition. GCP Cloud Audit Logs (Admin Activity, Data Access, System Event, Policy Denied), Access Transparency, GKE audit logging, Workspace audit logs, persistent disk forensic export. Container and Kubernetes forensics: image layer analysis, runtime filesystem/memory capture, API server audit logs, etcd analysis, RBAC audit, Falco correlation, container-escape artifact recovery, serverless investigation. Enterprise IR playbooks: ransomware, BEC, cloud account compromise, supply chain compromise, insider threat. Enterprise threat hunting: hypothesis-driven operations, persistence/lateral-movement/exfiltration/credential-access hunts, hunt automation. Evidence handling: chain of custody, ISO 27037, cloud evidence jurisdiction (CLOUD Act, MLAT), expert witness preparation, forensic report writing.

**Audience.** Incident responders, SOC analysts (Tier II and III), cloud security engineers, forensic examiners, and DFIR team leads operating in hybrid-cloud and container-orchestrated environments. The chapter assumes working familiarity with at least one major cloud provider's console and CLI, basic container operations (Docker build/run/inspect), and the IR lifecycle models discussed in Chapter 24A.

**Prerequisites.** Domain 24 Chapter 24A (disk/memory forensics, timeline analysis, log analysis fundamentals, PICERL/NIST IR workflows, Velociraptor/GRR/osquery, threat-hunting foundations). Domain 10 Chapter 10A (cloud provider security architecture — IAM, IMDS, S3/Blob/GCS policy models, CloudTrail/Azure Monitor/GCP Audit Log basics). Domain 10 Chapter 10B (container and Kubernetes security — namespaces, cgroups, seccomp, pod security contexts, container escape techniques).

---

## 1. AWS forensics deep dive

### 1.1 CloudTrail event structure and analysis

Chapter 24A §3.4 introduced CloudTrail as the record of every AWS API call. This section examines the internal structure of CloudTrail events and the advanced analysis techniques that distinguish competent AWS forensics from superficial log review. Every CloudTrail event is a JSON object with a standardized set of fields. The `eventVersion` field (currently `1.09` for most events) determines the schema. The `userIdentity` block is the single most forensically significant element: it contains the `type` (Root, IAMUser, AssumedRole, FederatedUser, AWSAccount, AWSService), the `principalId` (unique identifier of the calling principal), the `arn` of the caller, the `accountId`, and — critically for assumed-role sessions — the `sessionContext` sub-block, which records the `sessionIssuer` (the role that was assumed), the `attributes` (creation time, MFA authentication status), and any `sourceIdentity` or `sessionPolicy` constraints. When investigating a compromise, reconstructing the full identity chain from `sessionContext` is essential: an attacker who assumes a role through a chain of AssumeRole calls leaves a trail where each event's `userIdentity.sessionContext.sessionIssuer.arn` points to the previous link.

The `eventSource` field identifies the AWS service that processed the request (e.g., `ec2.amazonaws.com`, `s3.amazonaws.com`, `iam.amazonaws.com`). The `eventName` is the specific API action (`RunInstances`, `PutObject`, `CreateUser`). The `sourceIPAddress` reveals the origin of the call — for calls from within AWS services, this may be the service's internal IP or the string `AWS Internal`, but for calls from compromised credentials used externally, this is the attacker's IP address (or their proxy/VPN endpoint). The `userAgent` field often reveals tooling: `aws-cli/2.x`, `boto3/1.x`, `console.amazonaws.com` (web console), `AWSServiceRoleForOrganizations` (service-linked role), or unusual user agents like `python-requests/2.31.0` (indicating programmatic access outside official SDKs).

The `requestParameters` and `responseElements` fields contain the full API request and response payloads. For `RunInstances`, the `requestParameters` include the AMI ID, instance type, security groups, key pair name, IAM instance profile, and user data (base64-encoded startup script — a common persistence vector). For `CreateUser` or `AttachUserPolicy`, these fields reveal exactly what the attacker created or modified. The `errorCode` and `errorMessage` fields are equally important: a stream of `AccessDenied` errors followed by a successful call reveals privilege-escalation reconnaissance.

**Management events versus data events versus Insights.** CloudTrail categorizes events into three tiers. Management events (enabled by default) capture control-plane operations: creating, modifying, or deleting AWS resources (`CreateBucket`, `RunInstances`, `PutBucketPolicy`, `CreateUser`, `AttachRolePolicy`). These are the bread-and-butter of incident investigation — they reveal what infrastructure the attacker touched. Data events capture data-plane operations: `GetObject` and `PutObject` on S3, `Invoke` on Lambda, `GetItem`/`PutItem` on DynamoDB. Data events are disabled by default because of their volume (a busy S3 bucket generates millions of data events per day). For forensic investigations involving data exfiltration or Lambda abuse, the investigator must verify that data event logging was enabled on the relevant resources before the incident — if it was not, those operations are invisible. Insights events are generated by CloudTrail Insights, which uses machine-learning baselines to detect unusual API activity patterns: a sudden spike in `TerminateInstances` calls, an abnormal burst of `GetSecretValue` requests, or an unusual `RunInstances` pattern outside normal deployment windows. Insights events provide anomaly-detection signals but should be correlated with raw management and data events for confirmation.

**Cross-account trail aggregation.** In an AWS Organizations environment, a single organization trail can capture CloudTrail events from all member accounts into a centralized S3 bucket owned by the security account. The trail is created from the management account with `--is-organization-trail` and applies to all current and future member accounts. This centralization is essential for incident response: an attacker who compromises one account and pivots to another via cross-account role assumption generates events in both accounts' CloudTrail logs, and the investigator needs the unified view to reconstruct the lateral-movement chain. The organization trail configuration should enable management events for all regions (even regions the organization does not actively use — attacker-created resources in unused regions are a common evasion technique) and data events for critical S3 buckets and Lambda functions.

**CloudTrail Lake SQL queries.** CloudTrail Lake provides a managed query engine for CloudTrail events, allowing SQL-based analysis without exporting logs to a separate analytics platform. Events are stored in an event data store with a configurable retention period (up to seven years). The query syntax uses standard SQL with CloudTrail-specific field paths. Forensic queries include: identifying all API calls from a compromised access key — `SELECT eventTime, eventName, sourceIPAddress, userAgent FROM event_data_store WHERE userIdentity.accessKeyId = 'AKIA...' ORDER BY eventTime`; finding all IAM changes in a time window — `SELECT eventTime, eventName, requestParameters FROM event_data_store WHERE eventSource = 'iam.amazonaws.com' AND eventTime BETWEEN '2026-05-01' AND '2026-05-08'`; detecting credential usage from anomalous source IPs — `SELECT DISTINCT sourceIPAddress, userIdentity.arn, COUNT(*) as callCount FROM event_data_store WHERE userIdentity.type = 'AssumedRole' GROUP BY sourceIPAddress, userIdentity.arn ORDER BY callCount DESC`. CloudTrail Lake eliminates the need to build custom Athena tables or ingest CloudTrail JSON into Splunk for ad-hoc forensic queries, though its per-query pricing model makes it expensive for large-scale continuous hunting.

### 1.2 GuardDuty findings and Security Hub integration

**GuardDuty** is AWS's managed threat-detection service. It consumes CloudTrail management and data events (for S3), VPC Flow Logs, DNS query logs, EKS audit logs, and (optionally) EC2 runtime monitoring data to generate security findings. Each finding has a `type` field that categorizes the threat. Understanding GuardDuty finding types is essential for triage during incident response. Key finding categories include: `Recon:EC2/PortProbeUnprotectedPort` (an instance port was probed from an external IP), `UnauthorizedAccess:IAMUser/MaliciousIPCaller.Custom` (API calls from an IP on a custom threat list), `Exfiltration:S3/AnomalousBehavior` (anomalous S3 data access patterns suggesting exfiltration), `CryptoCurrency:EC2/BitcoinTool.B!DNS` (an EC2 instance queried a cryptocurrency-mining domain), `Persistence:IAMUser/AnomalousBehavior` (anomalous IAM activity suggesting persistence creation), `PrivilegeEscalation:IAMUser/AnomalousBehavior` (anomalous policy attachment suggesting privilege escalation), and `Execution:Runtime/NewBinaryExecuted` (a new binary not part of the original AMI was executed — EC2 runtime monitoring finding).

Each finding includes a `severity` (numeric 0-10 and categorical Low/Medium/High), the `resource` affected (instance ID, access key, S3 bucket), the `service` details (including the `action` that triggered the finding — network connection details, API call details, or DNS query details), and `evidence` (including the `threatIntelligenceDetails` if the finding was triggered by a known-bad IP or domain). During an incident, the investigator should query GuardDuty findings for the affected account and region using `aws guardduty list-findings --detector-id <id> --finding-criteria '{"Criterion":{"resource.instanceDetails.instanceId":{"Eq":["i-0abc123"]}}}'` and then retrieve full finding details with `aws guardduty get-findings`.

**Security Hub** aggregates findings from GuardDuty, Inspector, Macie, IAM Access Analyzer, Firewall Manager, and third-party tools into a single pane. Findings are normalized to the AWS Security Finding Format (ASFF). During incident response, Security Hub provides the consolidated view: a compromised EC2 instance might have GuardDuty findings for outbound C2 traffic, Inspector findings for the unpatched vulnerability the attacker exploited, and Macie findings for the sensitive data the instance accessed. Security Hub also supports cross-account aggregation through a delegated administrator account — the security team receives findings from all member accounts without needing individual console access.

### 1.3 VPC Flow Logs forensics

VPC Flow Logs capture network traffic metadata (not packet payloads) for VPC network interfaces. The V5 log format adds fields critical for forensic analysis: `vpc-id`, `subnet-id`, `instance-id`, `pkt-srcaddr`, `pkt-dstaddr` (the packet-level addresses, which differ from the interface-level `srcaddr`/`dstaddr` in NAT scenarios), `flow-direction` (ingress or egress), `traffic-path` (identifying whether traffic traversed a NAT gateway, VPN gateway, transit gateway, or went directly through an internet gateway), and `tcp-flags` (a bitmask of TCP flags observed in the flow — SYN, SYN-ACK, FIN, RST). The `tcp-flags` field is particularly valuable: SYN-only flows (value 2) without corresponding SYN-ACK indicate connection attempts to closed or blocked ports (scanning), while established flows with only FIN or RST may indicate abruptly terminated C2 connections.

**Data-exfiltration detection via flow-volume analysis.** The primary forensic technique for detecting data exfiltration through VPC Flow Logs is analyzing egress volume anomalies. Each flow record includes `bytes` (total bytes transferred in the flow) and `packets`. By aggregating egress bytes per source instance over time windows and comparing against the instance's historical baseline, the investigator identifies anomalous outbound transfers. A database server that normally sends fewer than 100 MB per hour suddenly transmitting 50 GB to an external IP in a short window is a strong exfiltration signal. The investigator can query flow logs stored in CloudWatch Logs Insights: `stats sum(bytes) as totalBytes by srcAddr, dstAddr, dstPort | filter direction = 'egress' | sort totalBytes desc | limit 50` or, if exported to S3 and queried via Athena, use standard SQL aggregation over the Parquet-format flow logs. Port analysis adds context: exfiltration over port 443 (HTTPS) blends with legitimate traffic, while exfiltration over port 53 (DNS tunneling) or unusual high ports is more distinctive. Correlating flow-log timestamps with CloudTrail API events (e.g., a `GetObject` call on S3 at the same time as a large egress flow) strengthens the exfiltration narrative.

### 1.4 EC2 forensics

**EBS snapshot acquisition.** The standard method for acquiring an EC2 instance's disk for forensic analysis is creating an EBS snapshot. The investigator calls `aws ec2 create-snapshot --volume-id vol-0abc123 --description "Forensic acquisition - incident 2026-05-08"` on each volume attached to the instance. Snapshots are point-in-time, crash-consistent copies. The snapshot is then shared with the forensics account (if analysis is conducted in a separate account for isolation) via `aws ec2 modify-snapshot-attribute --snapshot-id snap-0abc --attribute createVolumePermission --operation-type add --user-ids 123456789012`. In the forensics account, the snapshot is used to create a new volume (`aws ec2 create-volume --snapshot-id snap-0abc --availability-zone us-east-1a`), which is attached to a forensic workstation EC2 instance as a secondary device. The forensic examiner then mounts the volume read-only (`mount -o ro,noatime,noexec /dev/xvdf1 /mnt/evidence`) and applies standard disk-forensics techniques from Chapter 24A §1. The EBS snapshot should be encrypted with a forensics-specific KMS key and the source volume's state preserved (do not terminate the instance or delete the volume until the investigation concludes).

**Memory acquisition.** EC2 instances running on the Nitro hypervisor do not provide native memory-dump capabilities through the hypervisor (unlike VMware's `.vmem` files). Memory acquisition options include: deploying LiME via SSM Run Command (`aws ssm send-command --instance-ids i-0abc --document-name AWS-RunShellScript --parameters 'commands=["insmod /tmp/lime.ko path=/tmp/mem.lime format=lime"]'`) on Linux instances — this requires the LiME kernel module pre-compiled for the instance's kernel version or compiled on-the-fly from kernel headers; using WinPmem via SSM on Windows instances; or leveraging an EDR agent's memory-dump capability if one is deployed. The investigator must be aware that connecting to the instance to acquire memory modifies the system state (loading the LiME module creates a new kernel module entry, the SSM agent processes consume memory, network connections are established to the SSM endpoint). Documenting these forensic artifacts (the investigator's own footprints) is part of proper evidence handling.

**AMI analysis.** An attacker who has established persistence may create a custom AMI from a compromised instance — this AMI can be used to launch new instances with built-in backdoors. The investigator should query for recently created AMIs in the compromised account: `aws ec2 describe-images --owners self --query 'Images[?CreationDate>=`2026-05-01`]'`. Each AMI's block device mapping reveals the EBS snapshots that compose the image; these snapshots can be independently mounted and analyzed. Additionally, the attacker may have shared AMIs to external accounts (`aws ec2 describe-image-attribute --image-id ami-0abc --attribute launchPermission`) — identifying these shared AMIs is critical for understanding whether the compromise has propagated to other AWS accounts.

**Instance metadata service exploitation evidence.** When an attacker exploits SSRF to steal credentials from IMDS (Domain 10 Chapter 10A §1.2), the evidence appears in multiple locations: CloudTrail logs show API calls using the instance's role credentials from a `sourceIPAddress` that is not the instance's own IP (the attacker using stolen credentials externally); VPC Flow Logs may show the SSRF request chain (the web application making internal requests to `169.254.169.254`); and application logs on the instance may contain the SSRF payload in HTTP request parameters. The investigator should search CloudTrail for all events where the `userIdentity.arn` matches the instance's role and the `sourceIPAddress` does not match the instance's private or public IP — this pattern is the canonical indicator of IMDS credential theft.

### 1.5 S3 forensics

**S3 server access logging** records every request to a bucket in a target logging bucket. Each log entry includes: the bucket owner, the bucket name, the request time, the remote IP, the requester (IAM principal ARN or `-` for anonymous), the operation (`REST.GET.OBJECT`, `REST.PUT.OBJECT`, `REST.DELETE.OBJECT`), the key (object path), the HTTP status, the error code, bytes sent, object size, total time, and the user agent. S3 server access logs have best-effort delivery — some records may be delayed or missing. For reliable forensics, object-level CloudTrail data events are preferred, as they provide structured JSON with full `userIdentity` details and are delivered through the standard CloudTrail pipeline.

**Bucket policy analysis for forensics.** During a data-breach investigation involving S3, the investigator must analyze both the current bucket policy and its modification history. CloudTrail records every `PutBucketPolicy` and `DeleteBucketPolicy` call, including the full policy document in `requestParameters.bucketPolicy`. By querying CloudTrail for `eventName = 'PutBucketPolicy' AND requestParameters.bucketName = 'target-bucket'`, the investigator can reconstruct the timeline of policy changes — identifying when the attacker opened the bucket to external access or granted cross-account permissions. The `PutBucketAcl` event similarly reveals ACL modifications. AWS Config, if enabled, provides point-in-time snapshots of bucket configurations (versioning, encryption, public access settings, policies) that support this historical reconstruction.

**Data exfiltration via S3.** Attackers exfiltrate data through S3 in several ways: downloading objects to an external location (visible in data events as `GetObject` calls from external IPs), copying objects to an attacker-controlled bucket in another account (`s3:ReplicateObject` or `aws s3 cp` calls with a cross-account destination — visible in CloudTrail as API calls from the compromised account specifying a destination bucket ARN in another account), or modifying bucket replication rules to continuously replicate new objects to an external bucket (`PutBucketReplication` event). The investigator should check for cross-region replication configurations, S3 batch operations, and presigned URL generation (`GetObject` with `X-Amz-SignedHeaders` in the request — presigned URLs allow unauthenticated access to objects for a limited time and are a common exfiltration vector that bypasses bucket policies).

### 1.6 Lambda forensics

Lambda functions execute in ephemeral environments that are destroyed after inactivity, making traditional disk and memory forensics impossible. Investigation relies entirely on log analysis. Each Lambda invocation writes structured log entries to CloudWatch Logs in a log group named `/aws/lambda/<function-name>`. The log stream is identified by the date and a unique execution-environment ID. Entries include the `START` record (request ID, version), any `console.log` or `print()` output from the function code, and the `END`/`REPORT` records (duration, billed duration, memory used, init duration for cold starts).

**Cold-start timing analysis.** The `REPORT` record's `Init Duration` field appears only on cold starts (when a new execution environment is created). A pattern of frequent cold starts outside normal deployment windows may indicate function-code updates by an attacker (each code update invalidates existing warm environments). Correlating cold-start timestamps with CloudTrail `UpdateFunctionCode20150331v2` events identifies attacker modifications. The function's code history can be reconstructed through versioning (if the function uses published versions or aliases) or through CloudTrail `GetFunction` events that include the `CodeSha256` in the response — comparing code hashes across time reveals unauthorized changes.

**X-Ray traces.** AWS X-Ray provides distributed tracing for Lambda functions, recording the full request path: the trigger source, the Lambda execution, and any downstream calls (DynamoDB queries, S3 operations, HTTP requests to external endpoints). During investigation, X-Ray traces reveal what external services a compromised Lambda function contacted — identifying C2 endpoints or data-exfiltration destinations. X-Ray traces are queried via the X-Ray console or API using filter expressions: `service("my-function") AND annotation.status = "error"`.

### 1.7 IAM forensics

**Credential report analysis.** The IAM credential report (`aws iam generate-credential-report` followed by `aws iam get-credential-report`) provides a CSV snapshot of all IAM users and their credential status: password enabled/last used/last rotated, access keys (key1 and key2) active/last used/last rotated, MFA enabled, and ARN. During incident response, the credential report reveals: users with access keys that have never been rotated (stale keys are high-value targets), users with MFA disabled (vulnerable to credential-stuffing attacks), users with multiple active access keys (one may be attacker-created), and users whose credentials were last used from unusual source IPs or services.

**Access Advisor.** The IAM Access Advisor for each user, role, and policy shows the last time each service was accessed and from which region. During investigation, Access Advisor reveals services that were accessed for the first time during the incident window — an IAM role that has never accessed `lambda.amazonaws.com` before but suddenly invoked Lambda functions is suspicious. Access Advisor data complements CloudTrail analysis by providing a service-level summary view.

**CloudTrail-based access timeline.** The investigator reconstructs a complete timeline of a compromised principal's actions by querying CloudTrail for all events matching the principal's ARN or access key ID, ordered chronologically. This timeline reveals: the initial access (the first API call from a new source IP, indicating credential compromise), reconnaissance activities (calls to `DescribeInstances`, `ListBuckets`, `GetCallerIdentity`, `ListUsers`, `ListRoles`), privilege escalation (calls to `AttachUserPolicy`, `CreatePolicyVersion`, `PutRolePolicy`, `CreateLoginProfile`), persistence creation (calls to `CreateUser`, `CreateAccessKey`, `CreateRole`, `UpdateFunctionCode`), data access (calls to `GetObject`, `GetSecretValue`, `Decrypt`), and lateral movement (calls to `AssumeRole` targeting cross-account roles).

**Key age and rotation analysis.** Access keys older than 90 days are a compliance concern; keys older than a year are a security liability. During incident response, the investigator should enumerate all access keys with `aws iam list-access-keys --user-name <user>` and check each key's creation date and last-used information with `aws iam get-access-key-last-used --access-key-id AKIA...`. Keys created during the incident window that were not created through normal provisioning workflows are likely attacker-created persistence mechanisms. The response procedure for a compromised key is to first deactivate the key (`aws iam update-access-key --access-key-id AKIA... --status Inactive`) — deactivation rather than deletion preserves the key's metadata for forensic analysis while preventing further use. Deletion (`aws iam delete-access-key`) removes the key entirely and should only be done after the investigation has concluded.

### 1.8 AWS Organizations and cross-account investigation

Multi-account environments require coordinating investigation across account boundaries. The security account (typically a dedicated account with read-only cross-account roles into all member accounts) serves as the investigation hub. The investigator assumes roles into each affected account using `aws sts assume-role --role-arn arn:aws:iam::MEMBER_ACCOUNT:role/IncidentResponseRole --role-session-name forensics-2026-05-08`. Each assumed-role session generates its own CloudTrail event, creating an audit trail of the investigation itself.

Cross-account attack paths are reconstructed by correlating CloudTrail events across accounts. The attacker's lateral movement from Account A to Account B appears as an `AssumeRole` event in Account B's CloudTrail, where the `userIdentity.arn` references Account A's principal and the `sourceIPAddress` is either Account A's resource IP or `AWS Internal` (for service-to-service calls). The investigator maps the complete lateral-movement graph by querying each account's CloudTrail for `AssumeRole` events where the source principal belongs to another account in the organization.

AWS Organizations SCPs (Domain 10 Chapter 10A §1.6) may have been modified by an attacker who gained access to the management account — `PutOrganizationsPolicy` events in the management account's CloudTrail reveal SCP changes that weakened security controls. The investigator should verify the current SCP state against the known-good configuration and review all SCP modifications during the incident window.

### 1.9 Automated CloudTrail forensic analysis

The following Python script uses boto3 to pull all CloudTrail events associated with a specific access key within a time range and outputs a forensic timeline CSV. This is the first tool an investigator should run when a key compromise is confirmed.

```python
#!/usr/bin/env python3
"""CloudTrail forensic timeline extractor for a compromised access key."""
import boto3, csv, json, sys
from datetime import datetime, timezone

def extract_timeline(access_key_id: str, start: str, end: str, region: str = "us-east-1"):
    client = boto3.client("cloudtrail", region_name=region)
    paginator = client.get_paginator("lookup_events")
    rows = []
    page_iter = paginator.paginate(
        LookupAttributes=[
            {"AttributeKey": "AccessKeyId", "AttributeValue": access_key_id}
        ],
        StartTime=datetime.fromisoformat(start).replace(tzinfo=timezone.utc),
        EndTime=datetime.fromisoformat(end).replace(tzinfo=timezone.utc),
    )
    for page in page_iter:
        for event in page["Events"]:
            detail = json.loads(event["CloudTrailEvent"])
            rows.append({
                "timestamp": event["EventTime"].isoformat(),
                "event_name": event.get("EventName", ""),
                "event_source": detail.get("eventSource", ""),
                "source_ip": detail.get("sourceIPAddress", ""),
                "user_agent": detail.get("userAgent", ""),
                "error_code": detail.get("errorCode", ""),
                "request_params": json.dumps(detail.get("requestParameters", {})),
                "resources": json.dumps(event.get("Resources", [])),
            })
    rows.sort(key=lambda r: r["timestamp"])
    out = f"timeline_{access_key_id}.csv"
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[+] Wrote {len(rows)} events to {out}")
    return rows

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: ct_timeline.py <AKIA...> <start-iso> <end-iso>")
    extract_timeline(sys.argv[1], sys.argv[2], sys.argv[3])
```

**GuardDuty finding export and enrichment.** The investigator exports GuardDuty findings for triage using the following CLI sequence:

```bash
# Get the detector ID for the current region
DETECTOR=$(aws guardduty list-detectors --query 'DetectorIds[0]' --output text)

# List all HIGH/CRITICAL findings from the incident window
FINDING_IDS=$(aws guardduty list-findings \
  --detector-id "$DETECTOR" \
  --finding-criteria '{
    "Criterion": {
      "severity": {"Gte": 7},
      "updatedAt": {"GreaterThanOrEqual": 1746057600000}
    }
  }' --query 'FindingIds' --output json)

# Retrieve full finding details with evidence blocks
aws guardduty get-findings \
  --detector-id "$DETECTOR" \
  --finding-ids "$FINDING_IDS" \
  --sort-criteria '{"AttributeName":"severity","OrderBy":"DESC"}' \
  | jq '.Findings[] | {type, severity: .Severity, resource: .Resource, service: .Service.Action}'
```

**Athena SQL queries for VPC Flow Log analysis.** When flow logs are exported to S3 in Parquet format and catalogued in a Glue table, Athena enables SQL-based forensic analysis at scale.

```sql
-- Top talkers: identify instances with highest outbound volume in the incident window
SELECT srcaddr, dstaddr, dstport, SUM(bytes) AS total_bytes, COUNT(*) AS flow_count
FROM vpc_flow_logs
WHERE flow_direction = 'egress'
  AND start >= TIMESTAMP '2026-05-01 00:00:00'
  AND start <= TIMESTAMP '2026-05-08 23:59:59'
GROUP BY srcaddr, dstaddr, dstport
ORDER BY total_bytes DESC
LIMIT 50;

-- Exfiltration detection: single source sending > 1 GB outbound to non-RFC1918 destinations
SELECT srcaddr, dstaddr, SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE flow_direction = 'egress'
  AND NOT (dstaddr LIKE '10.%' OR dstaddr LIKE '172.%' OR dstaddr LIKE '192.168.%')
  AND start >= TIMESTAMP '2026-05-01 00:00:00'
GROUP BY srcaddr, dstaddr
HAVING SUM(bytes) > 1073741824
ORDER BY total_bytes DESC;

-- Port scan detection: source connecting to > 25 unique destination ports on a single target
SELECT srcaddr, dstaddr, COUNT(DISTINCT dstport) AS unique_ports, MIN(start) AS first_seen
FROM vpc_flow_logs
WHERE action = 'REJECT'
  AND start >= TIMESTAMP '2026-05-01 00:00:00'
GROUP BY srcaddr, dstaddr
HAVING COUNT(DISTINCT dstport) > 25
ORDER BY unique_ports DESC;
```

**SSM Run Command for fleet-wide live-response evidence collection.** When an incident affects multiple EC2 instances, SSM Run Command collects volatile evidence at scale before disk acquisition.

```bash
# Collect running processes, network connections, and open files from all tagged IR targets
aws ssm send-command \
  --targets 'Key=tag:IR-Scope,Values=incident-2026-05-08' \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=[
    "echo \"=== HOSTNAME ===\"; hostname",
    "echo \"=== TIMESTAMP ===\"; date -u +%Y-%m-%dT%H:%M:%SZ",
    "echo \"=== PROCESSES ===\"; ps auxww",
    "echo \"=== NETWORK ===\"; ss -tulnp",
    "echo \"=== CONNECTIONS ===\"; ss -tnp state established",
    "echo \"=== OPEN FILES ===\"; lsof -nP +L1 2>/dev/null | head -200",
    "echo \"=== CRONTABS ===\"; for u in $(cut -f1 -d: /etc/passwd); do crontab -l -u $u 2>/dev/null && echo \"--- $u ---\"; done",
    "echo \"=== LOADED MODULES ===\"; lsmod",
    "echo \"=== DOCKER PS ===\"; docker ps --no-trunc 2>/dev/null || true"
  ]' \
  --output-s3-bucket-name "forensic-evidence-2026" \
  --output-s3-key-prefix "ssm-collection" \
  --timeout-seconds 120 \
  --comment "IR live-response collection 2026-05-08"
```

**AWS Config advanced queries for resource-state timeline reconstruction.** AWS Config records configuration changes for supported resources. Advanced queries use SQL syntax against the Config aggregator.

```sql
-- All configuration changes to IAM roles during incident window
SELECT resourceId, resourceName, configurationItemCaptureTime, configuration
FROM configurationItems
WHERE resourceType = 'AWS::IAM::Role'
  AND configurationItemCaptureTime BETWEEN '2026-05-01T00:00:00Z' AND '2026-05-08T23:59:59Z'
ORDER BY configurationItemCaptureTime;

-- Security group modifications (rule additions that opened ports)
SELECT resourceId, resourceName, configurationItemCaptureTime,
       relationships, configuration
FROM configurationItems
WHERE resourceType = 'AWS::EC2::SecurityGroup'
  AND configurationItemStatus = 'OK'
  AND configurationItemCaptureTime >= '2026-05-01T00:00:00Z';
```

### 1.10 AWS detection rules and artifact mapping

**Sigma rule — IAM access key creation from unusual IP.** Detects `CreateAccessKey` calls from source IPs outside the organization's known CIDR ranges, a strong indicator of credential abuse.

```yaml
title: AWS IAM Access Key Created from Unusual Source IP
id: a4c3e8f1-7b2d-4e9a-b6c1-3d5f8e2a9b7c
status: stable
description: Detects creation of IAM access keys from IPs not in corporate CIDR ranges
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventSource: iam.amazonaws.com
    eventName: CreateAccessKey
  filter_known_ips:
    sourceIPAddress|cidr:
      - '10.0.0.0/8'
      - '172.16.0.0/12'
      - '192.168.0.0/16'
      - '203.0.113.0/24'        # Replace with org CIDRs
  condition: selection and not filter_known_ips
level: high
tags:
  - attack.persistence
  - attack.t1098.001
falsepositives:
  - Administrators working from non-VPN locations
  - CI/CD systems with dynamic IPs (should be tagged in filter)
```

**Sigma rule — S3 bucket policy loosened to public access.**

```yaml
title: AWS S3 Bucket Policy Changed to Allow Public Access
id: b5d4f9a2-8c3e-4f0b-a7d2-4e6g9f3b0c8d
status: stable
description: Detects PutBucketPolicy where the new policy contains Principal * or public access
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventSource: s3.amazonaws.com
    eventName:
      - PutBucketPolicy
      - PutBucketAcl
  keywords_in_params:
    requestParameters|contains:
      - '"Principal":"*"'
      - '"Principal":{"AWS":"*"}'
      - 'public-read'
      - 'public-read-write'
  condition: selection and keywords_in_params
level: critical
tags:
  - attack.exfiltration
  - attack.t1537
```

**Sigma rule — Lambda function code update outside deployment pipeline.**

```yaml
title: AWS Lambda Function Code Updated Outside CI/CD
id: c6e5a0b3-9d4f-4a1c-b8e3-5f7h0g4c1d9e
status: experimental
description: Detects UpdateFunctionCode from user agents other than the known CI/CD pipeline
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventSource: lambda.amazonaws.com
    eventName: UpdateFunctionCode20150331v2
  filter_cicd:
    userAgent|startswith:
      - 'aws-codepipeline'
      - 'AWSCodeBuild'
      - 'github-actions'
  filter_service:
    userIdentity.invokedBy: '*.amazonaws.com'
  condition: selection and not filter_cicd and not filter_service
level: high
tags:
  - attack.persistence
  - attack.t1525
```

**AWS detection artifacts table.** The following maps common attack techniques to their AWS-specific telemetry sources and key fields for detection.

| ATT&CK Technique | AWS Telemetry Source | Key Event / Field | Detection Signal |
|---|---|---|---|
| T1078.004 — Cloud Accounts | CloudTrail | `ConsoleLogin`, `sourceIPAddress` | Login from anomalous geo or impossible-travel IP |
| T1098.001 — Additional Cloud Credentials | CloudTrail | `CreateAccessKey`, `userIdentity` | Key created for a user by a different principal |
| T1537 — Transfer to Cloud Account | CloudTrail + S3 data events | `PutBucketReplication`, `CopyObject` | Replication to bucket in external account |
| T1580 — Cloud Infrastructure Discovery | CloudTrail | `DescribeInstances`, `ListBuckets`, rapid succession | Burst of Describe/List calls within 60 seconds |
| T1578.002 — Create Cloud Instance | CloudTrail | `RunInstances`, `requestParameters.instanceType` | Instance launched in unused region or unusual type |
| T1525 — Implant Container Image | CloudTrail + ECR | `PutImage`, `UpdateFunctionCode` | Image push or function update outside CI/CD |
| T1190 — Exploit Public-Facing App | GuardDuty + VPC Flow Logs | `Recon:EC2/PortProbeUnprotectedPort` | Inbound probe followed by successful connection |
| T1552.005 — Cloud Instance Metadata | CloudTrail | Role cred usage where `sourceIPAddress` != instance IP | IMDS credential theft and external use |

---

## 2. Azure forensics deep dive

### 2.1 Azure Activity Log, Sign-in Logs, and Audit Logs

Azure's logging architecture separates operations into three primary log categories. The **Azure Activity Log** (formerly the operational log) records management-plane operations on Azure resources: creating, modifying, or deleting VMs, storage accounts, network security groups, and all other Azure Resource Manager operations. Each Activity Log entry includes the `caller` (the UPN or service principal ID), the `operationName` (e.g., `Microsoft.Compute/virtualMachines/write`), the `status` (Succeeded, Failed, Started), the `correlationId` (linking related operations), the `claims` (JWT claims of the caller including IP address, authentication method, and tenant ID), and the `properties` (the resource-specific details of the operation). Activity Log retention is 90 days in the Azure portal by default; for forensic purposes, logs should be exported to a Log Analytics workspace (allowing KQL queries over extended retention) or to a Storage Account (for archival).

**Azure AD (Entra ID) Sign-in Logs** record every authentication event. Each sign-in log entry contains: the `userPrincipalName`, the `appDisplayName` (the application the user signed into), the `ipAddress`, the `location` (city, state, country derived from IP geolocation), the `clientAppUsed` (browser, mobile app, legacy protocol), the `conditionalAccessStatus` (whether Conditional Access policies were applied and their result — success, failure, not applied), the `riskState` and `riskDetail` (from Azure AD Identity Protection), the `mfaDetail` (whether MFA was satisfied and by which method), and the `deviceDetail` (OS, browser, device compliance status). Forensic analysis of sign-in logs focuses on: identifying the initial compromise (a sign-in from an unusual IP or country, a sign-in using a legacy protocol that bypasses MFA like IMAP or SMTP), mapping the attacker's session persistence (repeated sign-ins using the same refresh token — visible through the `correlationId` and `authenticationProcessingDetails`), and detecting consent-grant attacks (sign-ins to malicious OAuth applications).

**Azure AD Audit Logs** record directory changes: user creation, group membership modification, application registration, service principal credential addition, role assignment, and Conditional Access policy changes. Each audit log entry includes the `activityDisplayName`, the `initiatedBy` (user or service principal), the `targetResources` (the objects that were modified), and the `additionalDetails`. During incident response, audit logs reveal: attacker-created users or service principals, permission escalation through role assignments, Conditional Access policy modifications (weakening MFA requirements), and OAuth application consent grants that provide the attacker with persistent access tokens.

### 2.2 Entra ID forensics

**Sign-in anomaly analysis.** Azure AD Identity Protection generates risk detections for anomalous sign-in behavior: `Unfamiliar sign-in properties` (sign-in from a new location or device), `Atypical travel` (impossible-travel detection — sign-ins from geographically distant locations within a short time), `Anomalous Token` (token characteristics suggesting token theft or replay), `Token Issuer Anomaly` (token issued by an unexpected issuer — indicating federation compromise), `Malicious IP address` (sign-in from a known-malicious IP), and `Password Spray` (multiple failed sign-in attempts across many accounts from the same IP). During investigation, the investigator queries risk detections via the Microsoft Graph API: `GET https://graph.microsoft.com/v1.0/identityProtection/riskDetections?$filter=userId eq '{userId}'` to retrieve all risk events for a specific user. The `riskDetail` field indicates whether the risk was confirmed by an admin, dismissed, or auto-remediated.

**Conditional Access evaluation logs.** Each sign-in log entry includes a `conditionalAccessPolicies` array listing every Conditional Access policy that was evaluated, its `displayName`, its `result` (success, failure, notApplied, unknownFutureValue), and the `conditions` that were matched or unmatched. During incident response, analyzing Conditional Access evaluation reveals: whether the attacker bypassed MFA by using a trusted location, a compliant device, or a legacy authentication protocol; whether the attacker's sign-in triggered a policy that was set to report-only mode rather than enforce; and whether the attacker modified a Conditional Access policy (visible in audit logs) to create an exception for their access path.

**Risky user and risky sign-in reports.** The risky-users report aggregates all risk detections for each user into a composite risk level (Low, Medium, High). The investigator should query `GET https://graph.microsoft.com/v1.0/identityProtection/riskyUsers?$filter=riskLevel eq 'high'` to identify all high-risk users in the tenant. For each risky user, the risk history (`GET .../riskyUsers/{id}/history`) provides the chronological sequence of risk events, showing how the risk escalated over time. Users that were never flagged as risky but are known-compromised indicate a gap in Identity Protection coverage — the investigator should determine why the detection failed (was the attacker using a residential proxy that didn't trigger IP-based detections? was the initial compromise via token theft rather than credential stuffing?).

### 2.3 Azure NSG Flow Logs and network forensics

Azure Network Security Group (NSG) Flow Logs capture traffic metadata for network interfaces subject to NSG rules. Version 2 flow logs include: the flow tuple (source IP, destination IP, source port, destination port, protocol), the flow state (B for begin, C for continuing, E for end), the flow direction (inbound or outbound), the decision (Allow or Deny), the bytes sent source-to-destination, the bytes sent destination-to-source, and the packets in each direction. Flow logs are stored in Azure Storage Account blobs as JSON files organized by time window (one-minute or five-minute intervals).

Forensic analysis of NSG Flow Logs parallels VPC Flow Log analysis in AWS (§1.3): aggregating egress volume by destination to detect data exfiltration, identifying connections to known-malicious IPs (correlating with threat-intelligence feeds from Domain 25 Chapter 25A §1), analyzing denied flows to identify scanning activity (a high volume of denied inbound connections from the same source IP indicates port scanning), and correlating flow timestamps with other log sources to build the network activity timeline. Azure Traffic Analytics (built on top of NSG Flow Logs) provides pre-computed analytics including geo-mapping of traffic origins, traffic patterns between subnets, and open-port analysis.

### 2.4 Azure Storage and Key Vault forensics

**Azure Storage analytics logging** records every request to a storage account (blobs, files, queues, tables). The log includes: the operation type (`GetBlob`, `PutBlob`, `DeleteBlob`, `ListBlobs`), the authentication type (account key, SAS token, Azure AD, anonymous), the requester's IP address, the object URL, the HTTP status code, and the server latency. During a data-breach investigation, storage analytics logs reveal which objects were accessed, by whom, and when. SAS token abuse is a particular concern: a SAS token with overly broad permissions (full account access, no IP restriction, long expiry) provides persistent, credential-independent access to storage data. The investigator should enumerate all active SAS tokens (checking storage account access policies and any SAS tokens embedded in application configurations) and revoke compromised tokens by rotating the storage account keys (which invalidates all SAS tokens derived from those keys).

**Azure Key Vault diagnostics logging** records every operation on secrets, keys, and certificates: `SecretGet`, `SecretSet`, `SecretList`, `KeySign`, `KeyDecrypt`, `CertificateGet`. Each log entry includes the `callerIpAddress`, the `identity` (the Azure AD principal that authenticated to Key Vault), and the `resultType` (Success or Failure). During incident response, Key Vault diagnostic logs reveal: whether the attacker accessed secrets (API keys, database connection strings, certificates), which specific secrets were retrieved, and whether the attacker's access attempts were blocked by Key Vault access policies. An attacker who compromises a service principal with Key Vault access can exfiltrate all secrets in the vault — the diagnostic logs are the primary evidence source for scoping this exposure.

### 2.5 Microsoft 365 forensics

**Unified Audit Log (UAL).** The UAL is the single most important log source for Microsoft 365 incident response. It records events across Exchange Online, SharePoint Online, OneDrive, Teams, Azure AD, Power Platform, and other M365 services. The UAL is queried through the Microsoft Purview compliance portal or via PowerShell: `Search-UnifiedAuditLog -StartDate "2026-05-01" -EndDate "2026-05-08" -UserIds "compromised@domain.com" -ResultSize 5000`. Key event types for BEC investigation include: `MailboxLogin` (mailbox access events), `Set-Mailbox` (mailbox setting changes — forwarding rules, delegates), `New-InboxRule` (inbox rule creation — attackers create rules to hide emails or forward messages), `Add-MailboxPermission` (delegate access grants), `Set-OwaMailboxPolicy` (OWA setting changes), and `FileAccessed`/`FileDownloaded` (SharePoint/OneDrive file access). The UAL's `AuditData` field is a JSON blob containing event-specific details: the `ClientIPAddress`, the `UserAgent`, the `LogonType` (Owner, Delegate, Admin), and operation-specific parameters.

**Mailbox audit logging.** Exchange Online mailbox auditing (enabled by default since 2019) captures owner, delegate, and admin actions on mailboxes. Audited operations include `MessageBind` (message accessed), `FolderBind` (folder accessed), `SendAs` (message sent using the mailbox's identity), `HardDelete` (message permanently deleted), and `MoveToDeletedItems`. During a BEC investigation, the investigator searches for `SendAs` events (the attacker sending emails as the compromised user), `HardDelete` events (the attacker deleting evidence of their activity from the mailbox), and `UpdateInboxRules` events (the attacker creating forwarding rules to redirect incoming emails to an external address).

**eDiscovery and Content Search.** Microsoft Purview eDiscovery allows the investigator to search across all M365 content (email, files, Teams messages, Yammer conversations) for specific keywords, senders, recipients, date ranges, or file types. Content Search is the foundational tool; eDiscovery (Standard) adds legal holds and case management; eDiscovery (Premium) adds advanced analytics (threading, near-duplicate detection, relevance scoring). During incident response, eDiscovery preserves evidence (legal hold prevents content deletion by users or retention policies) and enables comprehensive content review (searching for all emails containing wire-transfer instructions, all files shared with external domains, or all Teams messages mentioning specific projects that may have been compromised).

### 2.6 Azure VM disk acquisition

Azure VM disk acquisition follows a parallel process to EC2 EBS snapshot acquisition (§1.4). For managed disks, the investigator creates a snapshot: `az snapshot create --resource-group forensics-rg --source /subscriptions/.../disks/compromised-os-disk --name forensic-snap-2026-05-08`. The snapshot is then exported to a VHD file by generating a SAS URI: `az snapshot grant-access --resource-group forensics-rg --name forensic-snap-2026-05-08 --duration-in-seconds 3600 --access-level Read`, which returns a URL for downloading the VHD. The VHD can be downloaded to an on-premises forensic workstation or attached to a forensic VM in Azure. For large disks, the incremental snapshot feature reduces transfer time by capturing only changed blocks since the last snapshot. The examiner mounts the VHD (on Linux: `qemu-nbd --connect=/dev/nbd0 forensic-snap.vhd` followed by `mount -o ro,noatime /dev/nbd0p1 /mnt/evidence`) and applies disk forensics procedures from Chapter 24A §1. Microsoft Defender for Cloud alerts and incidents should be reviewed in parallel — Defender for Cloud generates alerts for suspicious activities on Azure VMs (lateral movement, suspicious process execution, cryptocurrency mining, anomalous sign-in to the VM) that correlate with the forensic findings from disk analysis.

### 2.7 KQL forensic queries for Azure log analysis

**Azure Activity Log — resource deletion and modification timeline.** Kusto Query Language (KQL) against a Log Analytics workspace provides the primary forensic query interface for Azure.

```kql
// Activity Log: all write/delete operations by a compromised principal in incident window
AzureActivity
| where TimeGenerated between (datetime(2026-05-01) .. datetime(2026-05-08))
| where Caller =~ "compromised-user@contoso.com" or Caller =~ "app-id-guid"
| where OperationNameValue has_any ("write", "delete", "action")
| project TimeGenerated, OperationNameValue, ResourceGroup, Resource,
          ActivityStatusValue, CallerIpAddress, Properties_d
| sort by TimeGenerated asc
```

**Sign-in Log — anomalous authentication forensics.**

```kql
// All sign-ins for compromised account with risk and MFA details
SigninLogs
| where TimeGenerated between (datetime(2026-05-01) .. datetime(2026-05-08))
| where UserPrincipalName =~ "compromised-user@contoso.com"
| extend City = tostring(LocationDetails.city),
         Country = tostring(LocationDetails.countryOrRegion),
         CA_Result = tostring(ConditionalAccessPolicies[0].result)
| project TimeGenerated, AppDisplayName, IPAddress, City, Country,
          ClientAppUsed, RiskLevelDuringSignIn, MfaDetail, CA_Result,
          DeviceDetail, Status
| sort by TimeGenerated asc

// Impossible-travel detection: sign-ins from > 500km apart within 60 minutes
let threshold_minutes = 60;
SigninLogs
| where ResultType == 0
| project TimeGenerated, UserPrincipalName, IPAddress,
          Lat = toreal(LocationDetails.geoCoordinates.latitude),
          Lon = toreal(LocationDetails.geoCoordinates.longitude)
| sort by UserPrincipalName, TimeGenerated asc
| extend PrevTime = prev(TimeGenerated), PrevLat = prev(Lat), PrevLon = prev(Lon),
         PrevUser = prev(UserPrincipalName)
| where UserPrincipalName == PrevUser
| extend TimeDiffMin = datetime_diff('minute', TimeGenerated, PrevTime)
| where TimeDiffMin <= threshold_minutes and TimeDiffMin > 0
| extend DistKm = geo_distance_2points(Lon, Lat, PrevLon, PrevLat) / 1000
| where DistKm > 500
| project TimeGenerated, UserPrincipalName, IPAddress, DistKm, TimeDiffMin
```

**Audit Log — directory changes by attacker.**

```kql
// Entra ID audit events: role assignments, app registrations, credential additions
AuditLogs
| where TimeGenerated between (datetime(2026-05-01) .. datetime(2026-05-08))
| where InitiatedBy has "compromised-user@contoso.com"
      or InitiatedBy has "compromised-app-id"
| project TimeGenerated, OperationName, Category,
          TargetResources, AdditionalDetails, Result
| sort by TimeGenerated asc
```

### 2.8 Microsoft Graph API PowerShell for Entra ID forensics

The following PowerShell examples use the Microsoft Graph API to enumerate risky users, anomalous sign-ins, and malicious OAuth applications.

```powershell
# Connect to Graph with required scopes
Connect-MgGraph -Scopes "IdentityRiskEvent.Read.All","Directory.Read.All",`
    "Application.Read.All","AuditLog.Read.All"

# --- Risky users enumeration ---
$riskyUsers = Get-MgRiskyUser -Filter "riskLevel eq 'high'" -All
$riskyUsers | Select-Object UserPrincipalName, RiskLevel, RiskState,
    RiskLastUpdatedDateTime | Export-Csv -Path risky_users.csv -NoTypeInformation

# --- Sign-in anomalies for a specific user ---
$userId = (Get-MgUser -Filter "userPrincipalName eq 'compromised@contoso.com'").Id
$signIns = Get-MgAuditLogSignIn -Filter "userId eq '$userId'" `
    -Top 500 -OrderBy "createdDateTime desc"
$signIns | Select-Object CreatedDateTime, AppDisplayName, IpAddress,
    @{N='City';E={$_.Location.City}}, @{N='Country';E={$_.Location.CountryOrRegion}},
    ClientAppUsed, RiskLevelDuringSignIn, MfaDetail | Export-Csv sign_ins.csv -NoTypeInformation

# --- OAuth app enumeration: non-Microsoft service principals with delegated permissions ---
$spns = Get-MgServicePrincipal -Filter "tags/any(t:t eq 'WindowsAzureActiveDirectoryIntegratedApp')" -All
$suspiciousApps = $spns | Where-Object {
    $_.PublisherName -notin @('Microsoft','Microsoft Services','Microsoft Accounts')
}
foreach ($app in $suspiciousApps) {
    $grants = Get-MgServicePrincipalOauth2PermissionGrant -ServicePrincipalId $app.Id
    if ($grants) {
        [PSCustomObject]@{
            DisplayName  = $app.DisplayName
            AppId        = $app.AppId
            Publisher     = $app.PublisherName
            Permissions  = ($grants | ForEach-Object { $_.Scope }) -join "; "
            ConsentType  = ($grants | ForEach-Object { $_.ConsentType }) -join "; "
        }
    }
} | Export-Csv oauth_apps_audit.csv -NoTypeInformation
```

### 2.9 Unified Audit Log PowerShell for BEC investigation

The following script automates the critical BEC triage checks: inbox rules, forwarding, delegate access, and transport rules — all in one pass.

```powershell
# Requires Exchange Online Management module
Connect-ExchangeOnline -UserPrincipalName admin@contoso.com

$target = "compromised@contoso.com"

# --- Inbox rules (attacker persistence) ---
$rules = Get-InboxRule -Mailbox $target
$rules | Where-Object { $_.ForwardTo -or $_.ForwardAsAttachmentTo -or
    $_.RedirectTo -or $_.DeleteMessage -eq $true } |
    Select-Object Name, Enabled, ForwardTo, ForwardAsAttachmentTo,
        RedirectTo, DeleteMessage, MarkAsRead, MoveToFolder |
    Export-Csv "bec_inbox_rules_$target.csv" -NoTypeInformation

# --- Mailbox forwarding configuration ---
Get-Mailbox $target | Select-Object ForwardingAddress,
    ForwardingSmtpAddress, DeliverToMailboxAndForward

# --- Delegate / full-access permissions ---
Get-MailboxPermission $target |
    Where-Object { $_.AccessRights -match 'FullAccess' -and
        $_.User -ne 'NT AUTHORITY\SELF' } |
    Select-Object User, AccessRights

# --- Send-As permissions ---
Get-RecipientPermission $target |
    Where-Object { $_.Trustee -ne 'NT AUTHORITY\SELF' } |
    Select-Object Trustee, AccessRights

# --- UAL search for mail-related attacker activity ---
Search-UnifiedAuditLog -StartDate "2026-05-01" -EndDate "2026-05-08" `
    -UserIds $target -RecordType ExchangeItem `
    -Operations "New-InboxRule","Set-InboxRule","Set-Mailbox",`
        "Add-MailboxPermission","Set-OwaMailboxPolicy" `
    -ResultSize 5000 |
    Select-Object CreationDate, Operations, AuditData |
    Export-Csv "bec_ual_exchange_$target.csv" -NoTypeInformation
```

### 2.10 Azure-specific Sigma detection rules

**Sigma rule — Azure AD credential compromise via legacy authentication.**

```yaml
title: Azure AD Sign-in via Legacy Authentication Protocol
id: d7f6b1c4-0e5a-4b2d-c9f4-6a8i1h5d2e0f
status: stable
description: Detects sign-ins using legacy protocols (IMAP, SMTP, POP3) that bypass MFA
logsource:
  product: azure
  service: signinlogs
detection:
  selection:
    ResultType: 0
    ClientAppUsed|contains:
      - 'IMAP'
      - 'SMTP'
      - 'POP3'
      - 'Authenticated SMTP'
      - 'Other clients'
  condition: selection
level: high
tags:
  - attack.initial_access
  - attack.t1078.004
```

**Sigma rule — Conditional Access policy modification.**

```yaml
title: Azure Conditional Access Policy Modified or Deleted
id: e8g7c2d5-1f6b-4c3e-d0a5-7b9j2i6e3f1a
status: stable
description: Detects changes to Conditional Access policies that may weaken security posture
logsource:
  product: azure
  service: auditlogs
detection:
  selection:
    OperationName:
      - 'Update conditional access policy'
      - 'Delete conditional access policy'
  condition: selection
level: high
tags:
  - attack.defense_evasion
  - attack.t1562.001
```

**Sigma rule — OAuth consent grant attack (illicit app consent).**

```yaml
title: Azure AD OAuth Consent Grant to High-Risk Permissions
id: f9h8d3e6-2a7c-4d4f-e1b6-8c0k3j7f4a2b
status: stable
description: Detects OAuth consent grants that include mail or directory read/write permissions
logsource:
  product: azure
  service: auditlogs
detection:
  selection:
    OperationName: 'Consent to application'
  high_risk_scope:
    TargetResources|contains:
      - 'Mail.Read'
      - 'Mail.ReadWrite'
      - 'Mail.Send'
      - 'Files.ReadWrite.All'
      - 'Directory.ReadWrite.All'
      - 'User.ReadWrite.All'
  condition: selection and high_risk_scope
level: critical
tags:
  - attack.persistence
  - attack.t1098.003
falsepositives:
  - Legitimate enterprise applications during onboarding
```

---

## 3. GCP forensics deep dive

### 3.1 Cloud Audit Logs

GCP's audit-logging architecture categorizes events into four log types. **Admin Activity logs** are always enabled and record configuration changes to GCP resources: creating or deleting VMs, modifying IAM policies, changing firewall rules, and updating Kubernetes cluster configurations. These are the equivalent of AWS CloudTrail management events and Azure Activity Log entries. **Data Access logs** record data-plane operations: reading data from Cloud Storage, querying BigQuery tables, accessing Spanner rows, or reading secrets from Secret Manager. Data Access logs are disabled by default (due to volume and cost) and must be enabled per-service or per-project. During incident response, the investigator must immediately verify Data Access log configuration — if these logs were not enabled for the affected services before the incident, the attacker's data-access activities are unrecoverable. **System Event logs** are generated by GCP itself rather than by user actions: live migration of VM instances, automatic scaling events, and maintenance notifications. **Policy Denied logs** record requests that were denied by VPC Service Controls, organization policies, or IAM deny policies — these logs reveal the attacker's failed access attempts and the security boundaries that constrained their movement.

Each audit log entry follows the `AuditLog` protobuf schema, containing the `serviceName` (e.g., `compute.googleapis.com`), the `methodName` (e.g., `v1.compute.instances.insert`), the `authenticationInfo` (the principal's email and `serviceAccountDelegationInfo` for delegated calls), the `authorizationInfo` (the resource and permission that was checked), the `requestMetadata` (caller's IP address and user agent), and the `request`/`response` payloads. Audit logs are written to Cloud Logging and can be queried using the Logs Explorer with filter expressions: `resource.type="gce_instance" AND protoPayload.methodName="v1.compute.instances.insert" AND timestamp >= "2026-05-01T00:00:00Z"`. For large-scale forensic analysis, logs can be exported to BigQuery via a log sink, enabling SQL-based analysis: `SELECT protopayload_auditlog.authenticationInfo.principalEmail, protopayload_auditlog.methodName, timestamp FROM project_logs.cloudaudit_googleapis_com_activity WHERE protopayload_auditlog.authenticationInfo.principalEmail = 'compromised@project.iam.gserviceaccount.com' ORDER BY timestamp`.

### 3.2 VPC Flow Logs and Access Transparency

GCP VPC Flow Logs capture network traffic metadata for VM instances within VPC subnets. Each flow record includes: source and destination IP, source and destination port, protocol, bytes sent, packets sent, and TCP flags. Flow logs are configured per-subnet with adjustable sampling rate (0.0 to 1.0 — forensic analysis requires 1.0 for complete capture, though this increases cost and storage). Flow logs are written to Cloud Logging and can be exported to BigQuery for SQL analysis or to Cloud Storage for long-term retention.

**Access Transparency logs** are a GCP-unique feature: they record accesses by Google personnel to customer data. These logs contain the `accessApproval` status (whether the access was approved by the customer via Access Approval), the `reason` for access (customer support ticket, Google-initiated review), and the resources accessed. Access Transparency is relevant to incident investigations where insider threat from the cloud provider is a concern (rare but addressed in compliance requirements) or when investigating whether a Google support interaction inadvertently exposed sensitive data.

### 3.3 GKE audit logging

Google Kubernetes Engine extends GCP's audit logging to the Kubernetes API server. GKE audit logs record every Kubernetes API request: pod creation, deployment updates, ConfigMap modifications, secret reads, RBAC changes, and `kubectl exec` sessions. These logs are written to Cloud Logging with the resource type `k8s_cluster`. The log entry's `protoPayload.authenticationInfo` identifies the caller (a GCP IAM principal, a Kubernetes service account, or an anonymous request), and the `protoPayload.request` and `protoPayload.response` contain the full Kubernetes API request and response objects.

Forensic analysis of GKE audit logs focuses on: identifying unauthorized `kubectl exec` sessions (an attacker who gains access to a developer's kubeconfig or a service account token can exec into running pods), detecting RBAC modifications (creation of ClusterRoleBindings that grant cluster-admin to unexpected subjects), identifying unauthorized pod creation (an attacker deploying a privileged pod for container escape — Domain 10 Chapter 10B §2), and detecting secret access (reads of Kubernetes secrets containing database credentials, API keys, or TLS certificates). GKE audit logs complement GCP-level audit logs: a complete investigation traces the attacker's path from GCP IAM compromise through GKE access to in-cluster lateral movement.

### 3.4 BigQuery, Cloud Storage, and Workspace audit analysis

**BigQuery audit logs** record dataset creation, table queries, data exports, and IAM policy changes. The `protoPayload.serviceData.jobQueryRequest.query` field contains the actual SQL query text for query jobs — revealing exactly what data the attacker queried. The `protoPayload.serviceData.jobQueryResponse.totalBytesProcessed` reveals the volume of data scanned. During a data-breach investigation, BigQuery audit logs show which tables the attacker queried and how much data was processed — even if the query results were viewed only in the console and not exported.

**Cloud Storage access logs** record object-level operations (reads, writes, deletes) and can be enabled through Data Access audit logs. The logs include the object path, the caller identity, the operation, and the response code. For Cloud Storage buckets containing sensitive data, the investigator should analyze all `storage.objects.get` events during the incident window to determine the scope of data exposure.

**Google Workspace audit logs** cover Gmail, Drive, Admin console, Groups, and other Workspace services. Gmail audit logs record message send, receive, and access events (but not message content without Vault holds). Drive audit logs record file creation, sharing, download, and permission changes — critical for investigating data exfiltration through Drive sharing (changing a file's sharing to "Anyone with the link" generates an audit event). Admin audit logs record administrative actions: user creation, role assignment, security setting changes, and OAuth app approvals. These logs are accessed through the Workspace Admin console's reporting section or via the Reports API: `GET https://admin.googleapis.com/admin/reports/v1/activity/users/all/applications/drive?eventName=change_document_visibility`. The investigator correlates Workspace audit logs with GCP audit logs when the compromised identity has access to both environments (common in organizations using Google Cloud with Workspace).

### 3.5 Forensic disk image acquisition in GCP

GCP persistent disk forensic acquisition follows the snapshot-and-export pattern. The investigator creates a snapshot: `gcloud compute disks snapshot compromised-disk --snapshot-names=forensic-2026-05-08 --zone=us-central1-a`. The snapshot is then exported as a GCE disk image: `gcloud compute images create forensic-image-2026-05-08 --source-snapshot=forensic-2026-05-08`. For off-cloud analysis, the image is exported to a Cloud Storage bucket in raw or vmdk format: `gcloud compute images export --destination-uri gs://forensics-bucket/forensic-2026-05-08.tar.gz --image forensic-image-2026-05-08`. The exported image can be downloaded to an on-premises forensic workstation for analysis with standard tools. Alternatively, the snapshot can be used to create a new disk in a forensics project and attached to a forensic VM for in-cloud analysis, maintaining the same read-only mount precautions as in the AWS and Azure processes described above.

### 3.6 GCP forensic CLI commands and BigQuery analysis

**Audit log export and disk snapshot via `gcloud`.** The following commands form the standard GCP forensic acquisition sequence.

```bash
# Export Admin Activity audit logs for the incident window to a GCS bucket
gcloud logging read \
  'logName="projects/my-project/logs/cloudaudit.googleapis.com%2Factivity"
   AND timestamp>="2026-05-01T00:00:00Z"
   AND timestamp<="2026-05-08T23:59:59Z"' \
  --project=my-project --format=json > /tmp/gcp_admin_activity.json

# Export Data Access logs for a specific service account
gcloud logging read \
  'logName="projects/my-project/logs/cloudaudit.googleapis.com%2Fdata_access"
   AND protoPayload.authenticationInfo.principalEmail="compromised-sa@my-project.iam.gserviceaccount.com"' \
  --project=my-project --format=json --limit=10000 > /tmp/gcp_data_access.json

# Create forensic disk snapshot
gcloud compute disks snapshot compromised-disk \
  --snapshot-names=forensic-snap-2026-05-08 \
  --zone=us-central1-a \
  --storage-location=us-central1 \
  --labels=case=IR-2026-05-08,handler=forensics

# Export disk image for offline analysis
gcloud compute images create forensic-image-2026-05-08 \
  --source-snapshot=forensic-snap-2026-05-08
gcloud compute images export \
  --destination-uri=gs://forensics-evidence/IR-2026-05-08/disk.tar.gz \
  --image=forensic-image-2026-05-08 --export-format=raw
```

**BigQuery forensic queries for Cloud Audit Logs.** When audit logs are routed to BigQuery via a log sink, SQL analysis scales to billions of events.

```sql
-- Full timeline for a compromised service account
SELECT
  timestamp,
  protopayload_auditlog.methodName AS method,
  protopayload_auditlog.resourceName AS resource,
  protopayload_auditlog.authenticationInfo.principalEmail AS principal,
  protopayload_auditlog.requestMetadata.callerIp AS source_ip,
  protopayload_auditlog.requestMetadata.callerSuppliedUserAgent AS user_agent,
  protopayload_auditlog.status.code AS status_code
FROM `my-project.audit_logs.cloudaudit_googleapis_com_activity_*`
WHERE protopayload_auditlog.authenticationInfo.principalEmail =
      'compromised-sa@my-project.iam.gserviceaccount.com'
  AND _TABLE_SUFFIX BETWEEN '20260501' AND '20260508'
ORDER BY timestamp;

-- IAM policy changes: detect privilege escalation
SELECT timestamp,
  protopayload_auditlog.methodName,
  protopayload_auditlog.resourceName,
  protopayload_auditlog.serviceData
FROM `my-project.audit_logs.cloudaudit_googleapis_com_activity_*`
WHERE protopayload_auditlog.methodName IN (
  'google.iam.admin.v1.SetIamPolicy',
  'SetIamPolicy'
)
  AND _TABLE_SUFFIX BETWEEN '20260501' AND '20260508'
ORDER BY timestamp;
```

**GKE forensic kubectl commands.** These commands collect runtime evidence from a GKE cluster during an active incident.

```bash
# All pods in all namespaces with security context details
kubectl get pods -A -o json | jq '.items[] | {
  namespace: .metadata.namespace,
  name: .metadata.name,
  nodeName: .spec.nodeName,
  hostPID: .spec.hostPID,
  hostNetwork: .spec.hostNetwork,
  privileged: (.spec.containers[].securityContext.privileged // false),
  image: .spec.containers[].image,
  created: .metadata.creationTimestamp
}' | jq -s 'sort_by(.created)'

# Exec sessions in audit logs (GKE writes to Cloud Logging)
gcloud logging read \
  'resource.type="k8s_cluster"
   AND protoPayload.methodName="io.k8s.core.v1.pods.exec.create"
   AND timestamp>="2026-05-01T00:00:00Z"' \
  --project=my-project --format=json --limit=500

# Secrets accessed during incident window
gcloud logging read \
  'resource.type="k8s_cluster"
   AND protoPayload.methodName="io.k8s.core.v1.secrets.get"
   AND timestamp>="2026-05-01T00:00:00Z"' \
  --project=my-project --format=json --limit=500
```

**Sigma rule — GCP service account key creation outside Terraform/CI.**

```yaml
title: GCP Service Account Key Created Outside IaC Pipeline
id: a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d
status: experimental
description: Detects CreateServiceAccountKey from user agents other than Terraform or known CI
logsource:
  product: gcp
  service: gcp.audit
detection:
  selection:
    protoPayload.methodName: google.iam.admin.v1.CreateServiceAccountKey
  filter_iac:
    protoPayload.requestMetadata.callerSuppliedUserAgent|contains:
      - 'Terraform'
      - 'google-cloud-sdk gcloud'
      - 'CloudBuild'
  condition: selection and not filter_iac
level: high
tags:
  - attack.persistence
  - attack.t1098.001
```

---

## 4. Container and Kubernetes forensics

### 4.1 Container image forensics

A container image is a layered filesystem. Each layer corresponds to a Dockerfile instruction (or a committed container state). Forensic analysis of container images begins with **layer analysis**: extracting and examining each layer individually to understand what was added, modified, or deleted at each build step. The `docker save <image> | tar -xf -` command exports the image as a tar archive containing the layer directories, the `manifest.json` (layer ordering and metadata), and the configuration JSON (which records the Dockerfile history). Each layer is itself a tar archive of the filesystem changes introduced by that instruction.

**Dockerfile reconstruction.** The image configuration's `history` array records the Dockerfile command that produced each layer (e.g., `RUN apt-get install -y curl`, `COPY app.py /app/`, `ENV API_KEY=...`). The `docker history <image>` command displays this history in human-readable format. An attacker who has modified an image (injecting a backdoor, adding a reverse shell, planting malicious dependencies) leaves traces in the layer history — unless they squashed the image (combining all layers into one) to obscure the modification. Comparing the running image's layer digests against the known-good image in the registry (using `docker inspect` and comparing the `RootFS.Layers` SHA256 digests) detects unauthorized modifications.

**Secrets in image layers.** A common security failure is embedding secrets (API keys, database passwords, SSH private keys) in image layers during the build process. Even if a subsequent layer deletes the secret file, the earlier layer still contains it — container images are append-only, and layer deletion does not remove data from previous layers. Tools like `truffleHog` and `ggshield` scan image layers for secrets. During incident response, analyzing all layers for secrets reveals potential credential exposure: a leaked database password in a container image layer means that password must be rotated immediately, regardless of whether the image was public or private.

**Image provenance and integrity.** Cosign (part of the Sigstore project) provides image signing and verification. Images signed with `cosign sign <image>` have an associated signature stored in the OCI registry. Verification with `cosign verify <image> --key <public-key>` confirms that the image has not been tampered with since signing. During incident response, verifying image signatures distinguishes between authorized images (signed by the CI/CD pipeline's key) and unauthorized images (unsigned or signed by an unknown key). The Sigstore transparency log (Rekor) provides a tamper-evident record of all signing operations, supporting supply-chain forensics (Domain 19 Chapter 19B §3).

### 4.2 Runtime container forensics

A running container's filesystem is an ephemeral overlay (OverlayFS in most container runtimes) on top of the read-only image layers. When a container is stopped, the overlay (the upper directory containing all runtime modifications) is typically deleted. Forensic preservation of a running container's state requires action before the container is terminated.

**Capturing the container filesystem.** The `docker export <container> > container_fs.tar` command exports the current merged filesystem (image layers plus overlay modifications) as a tar archive. The `docker diff <container>` command lists all files that were added (`A`), changed (`C`), or deleted (`D`) in the container's overlay relative to the image — this is the delta between the clean image and the current state, revealing attacker modifications. For containers running in Kubernetes, `kubectl cp <pod>:<path> <local-path>` copies individual files, but full filesystem preservation requires accessing the container's overlay directory on the node (typically at `/var/lib/docker/overlay2/<id>/diff/` or `/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/<id>/fs/`) or using `docker export` on the node.

**Memory dump from containers.** Container processes share the host kernel and are isolated only through namespaces and cgroups — they do not have separate physical memory. Memory acquisition for a containerized process requires: identifying the process's PID on the host (via `docker inspect --format '{{.State.Pid}}' <container>` or `crictl inspect <containerID>`), then dumping that process's memory using `gcore <pid>` (creates an ELF core dump), `/proc/<pid>/mem` direct read, or a full host memory dump via LiME (from which the container's processes can be extracted using Volatility 3 with namespace-aware analysis). The process-specific approach using `gcore` is less invasive than a full memory dump and captures the process's virtual address space including heap, stack, and mapped libraries.

**Process analysis within namespaces and cgroups.** Container isolation means that `ps` inside the container shows only the container's processes (PID namespace isolation), and network tools inside the container see only the container's network stack (network namespace isolation). The investigator must analyze processes from the host perspective: `nsenter --target <pid> --pid --mount --net ps aux` enters the container's namespaces to see its view, while `ls /proc/<pid>/ns/` on the host reveals the namespace memberships. Cgroup analysis (`cat /proc/<pid>/cgroup` and examining the cgroup directories in `/sys/fs/cgroup/`) reveals resource limits and accounting data — unexpected cgroup memberships may indicate container escape (a process that started in a container's cgroup hierarchy but moved to the host's cgroup is evidence of a breakout).

### 4.3 Kubernetes forensics

**API server audit logs.** The Kubernetes API server can be configured to log every request at different verbosity levels: `None` (no logging), `Metadata` (log request metadata — user, resource, verb, timestamp — but not request/response bodies), `Request` (log metadata plus request body), and `RequestResponse` (log metadata, request body, and response body). The audit policy defines which requests are logged at which level. Forensic analysis requires at minimum `Metadata` level for all resources and `Request` level for sensitive resources (secrets, RBAC bindings, pods with privileged security contexts). Audit log entries include: the `user.username` (the authenticated identity), `user.groups` (the groups the identity belongs to), `verb` (get, list, create, update, delete, patch, watch), `objectRef` (the resource kind, namespace, and name), `sourceIPs` (the client's IP — the node IP for kubelet requests, the user's IP for kubectl requests), and `responseStatus.code`.

**etcd analysis.** Kubernetes stores all cluster state in etcd — a distributed key-value store. Direct etcd analysis is a powerful forensic technique for recovering deleted or modified cluster state. Accessing etcd requires the etcd client certificates (stored on control-plane nodes, typically at `/etc/kubernetes/pki/etcd/`). Using `etcdctl --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key get /registry/secrets/<namespace>/<secret-name>` retrieves the raw stored state of a Kubernetes secret (base64-encoded but not encrypted at rest unless encryption-at-rest is configured). The `etcdctl get --prefix /registry/` command dumps the entire cluster state. Historical state can be recovered from etcd snapshots (if periodic snapshots are configured) or from etcd's write-ahead log (WAL) files. An attacker who modified RBAC bindings, created backdoor pods, or exfiltrated secrets leaves artifacts in etcd that persist until garbage collection — even if the Kubernetes resources were subsequently deleted.

**Pod security context analysis.** Kubernetes pods run with a security context that defines privilege and access-control settings. During investigation, the investigator examines pod specifications for: `privileged: true` (the container runs without isolation from the host kernel — a prerequisite for many container-escape techniques from Domain 10 Chapter 10B §2), `hostPID: true` (the container shares the host's PID namespace — it can see and signal all host processes), `hostNetwork: true` (the container shares the host's network namespace — it can access all host network interfaces), `hostPath` volume mounts (particularly mounts of `/`, `/etc`, `/var/run/docker.sock`, or `/proc` — these provide direct host filesystem access), and `runAsUser: 0` (running as root inside the container). Pods created with these dangerous configurations during the incident window are strong indicators of attacker activity.

**RBAC audit.** The investigator enumerates all ClusterRoleBindings and RoleBindings to identify overprivileged subjects: `kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name == "cluster-admin") | .subjects'` reveals all identities with cluster-admin privileges. Recently created RoleBindings (compare against the last known-good state or filter by creation timestamp) that grant elevated permissions to unexpected subjects (a new service account, a user not in the platform team, or the `system:anonymous` group) are evidence of privilege escalation. The `kubectl auth can-i --list --as=system:serviceaccount:default:compromised-sa` command reveals all permissions granted to a specific service account, mapping the blast radius of a compromised token.

**Service account token analysis.** Kubernetes service account tokens are JWTs signed by the API server's private key. Each pod automatically receives a token mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token` (unless `automountServiceAccountToken: false` is set). An attacker who compromises a pod obtains the service account token and can make API requests with the service account's permissions. The token's claims include the service account name, namespace, and expiration (for bound service account tokens in Kubernetes 1.21+). The investigator should decode the token (`echo <token> | base64 -d | jq .` for the payload section) and check its permissions against the RBAC configuration. Tokens that were used from unexpected source IPs (visible in API server audit logs where the `sourceIPs` field does not match the pod's node IP) indicate that the token was exfiltrated and used externally.

**kubectl exec forensics.** The `kubectl exec` command creates an interactive session inside a running container. API server audit logs record `exec` requests as `create` operations on the `pods/exec` subresource. The audit log entry includes the `user.username` (who initiated the exec), the `objectRef.name` (the target pod), the `objectRef.namespace`, and (at `Request` level) the `requestObject` containing the `command` array (the command executed inside the pod). During investigation, the analyst queries audit logs for all `pods/exec` events: `grep -r '"resource":"pods","subresource":"exec"' /var/log/kubernetes/audit/` or the equivalent Cloud Logging query in GKE (§3.3). Each exec session is a potential interactive-access event — correlating exec timestamps with other forensic artifacts (file modifications inside the container, process creation, network connections) builds the attacker's activity timeline within the cluster.

**Falco alert correlation.** **Falco** is the de facto runtime-security tool for Kubernetes. It monitors system calls from kernel space (via eBPF probes or the Falco kernel module) and generates alerts based on rules that define suspicious behavior: shell spawned in a container, sensitive file read (`/etc/shadow`, `/etc/passwd`, `/proc/1/environ`), outbound network connection from unexpected containers, binary executed that was not part of the original image, process namespace change (potential container escape), and privileged container started. Falco alerts provide the contextual bridge between infrastructure-level forensics (container filesystem, Kubernetes audit logs) and host-level process forensics (what the attacker actually did inside the container). During incident response, Falco alerts are correlated chronologically with Kubernetes audit logs and container filesystem changes to construct the full attack narrative: API server audit log shows an exec session at `T+0`, Falco alerts show a shell spawn at `T+1` and a sensitive file read at `T+2`, and the container filesystem diff shows new files at `T+3`.

### 4.4 Container escape evidence

Container-escape attacks break the isolation boundary between the container and the host. Forensic evidence of container escape includes artifacts at both the container level and the host level. **Namespace breakout artifacts** include: processes that originated in a container's PID namespace but are now running in the host's PID namespace (visible in `/proc/<pid>/status` where `NSpid` shows multiple PID namespace entries), files created on the host filesystem from a container process (the file's ownership and SELinux context may reveal the container origin), and `/proc/<pid>/root` symlinks that point to the host root filesystem rather than the container's overlay root.

**Namespace breakout via runc.** CVE-2019-5736 (runc container escape via `/proc/self/exe` overwrite — CVSS 8.6, CWE-78) allowed a malicious container to overwrite the host runc binary by exploiting a file-descriptor race condition during container execution. Forensic evidence of this attack includes: modification timestamps on the host's runc binary (`/usr/bin/runc` or `/usr/sbin/runc`) that do not match the installed package version, unexpected open file descriptors in `/proc/<pid>/fd` pointing to the runc binary from within container processes, and anomalous `execve` system calls in auditd logs where the runc binary was invoked with unexpected arguments. CVE-2020-15257 (containerd host-networking escape — CVSS 5.2, CWE-669) allowed containers running with `--net=host` to access the containerd shim's abstract Unix domain socket and escalate to host-level code execution. Evidence includes unexpected connections to abstract sockets (`@/containerd-shim/...`) visible in `ss -x` output and unusual process parentage where container processes spawn children outside the container's cgroup hierarchy.

**Cgroup escape traces.** CVE-2022-0185 (heap overflow in `legacy_parse_param` leading to cgroup escape — CVSS 8.4, CWE-787) and related cgroup-based escapes leave traces in cgroup hierarchies: the `release_agent` mechanism (an attacker writes a command to the cgroup's `release_agent` file and triggers it by emptying the cgroup) leaves the attacker's command in the cgroup configuration and the command's output/effects on the host. The investigator checks `/sys/fs/cgroup/*/release_agent` and the `notify_on_release` flag for unexpected configurations. The `devices.allow` cgroup configuration, if modified to permit access to host block devices (writing `a *:* rwm` to `/sys/fs/cgroup/devices/docker/<id>/devices.allow`), enables the container to mount host disks — the forensic evidence is the modified `devices.allow` file and any mount points created from within the container.

**Privileged container exploitation evidence.** A privileged container (`--privileged` flag or `privileged: true` in Kubernetes security context) has full access to all host devices, all kernel capabilities, and the host's cgroup filesystem. Evidence of exploitation includes: host device mounts created from within the container (`mount /dev/sda1 /mnt` output in the container's shell history or Falco alerts), kernel module loads initiated from the container (`insmod` calls visible in the host's `dmesg` and `auditd` logs originating from the container's process), and network namespace manipulation (the container's processes appear in the host's network namespace after escape). The detailed taxonomy of container-escape techniques is covered in Domain 10 Chapter 10B §2; this section focuses on the forensic artifacts those techniques produce.

### 4.5 Serverless forensics

Serverless functions (AWS Lambda, Google Cloud Functions, Azure Functions) present the most constrained forensic environment: the investigator has no access to the underlying compute infrastructure, no ability to acquire disk images or memory dumps, and no persistent filesystem to examine. Investigation is exclusively log-based.

For AWS Lambda, the investigator works with CloudWatch Logs (function output), CloudTrail data events (`Invoke` calls showing who triggered the function, from what IP, with what payload), and X-Ray traces (downstream calls made by the function). For Google Cloud Functions, Cloud Audit Logs record function deployment and invocation events, and function logs are written to Cloud Logging. For Azure Functions, invocation logs are written to Application Insights, management events appear in the Activity Log, and Function App diagnostic logs capture runtime behavior. The common investigation pattern across all three platforms is: reconstruct the function's invocation timeline from audit logs, analyze function output logs for evidence of malicious activity (exfiltrated data in log output, error messages from failed exploitation attempts, unexpected external network calls), and compare the function's current code against the known-good version (using version control or cloud-native versioning — Lambda aliases and versions, Cloud Functions revisions, Azure Functions deployment slots).

### 4.6 Container forensic collection script

The following script captures comprehensive forensic evidence from a running container before it is terminated. It must be executed on the container host with root access.

```bash
#!/usr/bin/env bash
# container_forensics.sh — Capture forensic state from a live container
set -euo pipefail

CONTAINER_ID="${1:?Usage: $0 <container-id-or-name>}"
EVIDENCE_DIR="/forensics/$(date -u +%Y%m%dT%H%M%SZ)_${CONTAINER_ID:0:12}"
mkdir -p "$EVIDENCE_DIR"

echo "[*] Collecting forensic evidence for container $CONTAINER_ID"

# 1. Container metadata
docker inspect "$CONTAINER_ID" > "$EVIDENCE_DIR/inspect.json"

# 2. Process list (from host PID namespace for full visibility)
HOST_PID=$(docker inspect --format '{{.State.Pid}}' "$CONTAINER_ID")
nsenter --target "$HOST_PID" --pid --mount ps auxww > "$EVIDENCE_DIR/processes.txt"

# 3. Network connections
nsenter --target "$HOST_PID" --pid --net ss -tulnp > "$EVIDENCE_DIR/listeners.txt"
nsenter --target "$HOST_PID" --pid --net ss -tnp state established > "$EVIDENCE_DIR/connections.txt"

# 4. Environment variables (may contain secrets — handle as sensitive)
cat "/proc/$HOST_PID/environ" | tr '\0' '\n' > "$EVIDENCE_DIR/environ.txt"

# 5. Filesystem diff (attacker modifications vs image baseline)
docker diff "$CONTAINER_ID" > "$EVIDENCE_DIR/fs_diff.txt"

# 6. Full filesystem export
docker export "$CONTAINER_ID" > "$EVIDENCE_DIR/filesystem.tar"

# 7. Container logs
docker logs "$CONTAINER_ID" --timestamps > "$EVIDENCE_DIR/stdout.log" 2> "$EVIDENCE_DIR/stderr.log"

# 8. Cgroup info (detect escape artifacts)
cat "/proc/$HOST_PID/cgroup" > "$EVIDENCE_DIR/cgroup.txt"

# 9. Namespace memberships
ls -la "/proc/$HOST_PID/ns/" > "$EVIDENCE_DIR/namespaces.txt"

# 10. Hash everything
cd "$EVIDENCE_DIR" && sha256sum * > SHA256SUMS.txt
echo "[+] Evidence collected in $EVIDENCE_DIR"
```

### 4.7 Falco rules for runtime threat detection

The following Falco rules detect critical container runtime threats. Deploy as `/etc/falco/rules.d/ir-rules.yaml`.

```yaml
# --- Container escape detection ---
- rule: Container Escape via nsenter or chroot
  desc: Detects attempts to break out of container namespaces
  condition: >
    spawned_process and container and
    (proc.name in (nsenter, chroot, unshare) or
     proc.cmdline contains "/proc/1/root" or
     proc.cmdline contains "/proc/1/ns")
  output: >
    Container escape attempt (user=%user.name command=%proc.cmdline
    container=%container.name image=%container.image.repository)
  priority: CRITICAL
  tags: [container, escape, mitre_privilege_escalation]

# --- Crypto mining detection ---
- rule: Cryptocurrency Mining Binary Executed
  desc: Detects known crypto miner process names and arguments
  condition: >
    spawned_process and container and
    (proc.name in (xmrig, minerd, minergate, cpuminer, cgminer, bfgminer) or
     proc.cmdline contains "stratum+tcp://" or
     proc.cmdline contains "stratum+ssl://" or
     proc.cmdline contains "--donate-level")
  output: >
    Crypto mining detected (user=%user.name command=%proc.cmdline
    container=%container.name image=%container.image.repository)
  priority: CRITICAL
  tags: [container, cryptomining, mitre_resource_hijacking]

# --- Reverse shell detection ---
- rule: Reverse Shell in Container
  desc: Detects reverse shell patterns from within a container
  condition: >
    spawned_process and container and
    ((proc.cmdline contains "/dev/tcp/" and proc.cmdline contains "bash") or
     (proc.name = "nc" and proc.cmdline contains "-e") or
     (proc.name = "python" and proc.cmdline contains "socket" and proc.cmdline contains "subprocess") or
     (proc.name = "perl" and proc.cmdline contains "Socket"))
  output: >
    Reverse shell detected (user=%user.name command=%proc.cmdline
    container=%container.name pid=%proc.pid)
  priority: CRITICAL
  tags: [container, reverse_shell, mitre_execution]

# --- Sensitive mount detection ---
- rule: Container Started with Sensitive Host Mount
  desc: Detects containers mounting sensitive host paths
  condition: >
    container and evt.type = container and
    (container.mounts contains "/var/run/docker.sock" or
     container.mounts contains "/var/run/containerd" or
     container.mounts contains "/etc/kubernetes" or
     container.mounts contains "/proc" or
     container.mounts startswith "/")
  output: >
    Sensitive host mount detected (container=%container.name
    image=%container.image.repository mounts=%container.mounts)
  priority: HIGH
  tags: [container, sensitive_mount, mitre_privilege_escalation]
```

### 4.8 Kubernetes RBAC audit and etcd forensic extraction

**RBAC audit script — enumerate overprivileged service accounts and detect dangerous bindings.**

```bash
#!/usr/bin/env bash
# k8s_rbac_audit.sh — Identify overprivileged service accounts
set -euo pipefail

echo "=== Cluster-Admin Bindings ==="
kubectl get clusterrolebindings -o json | jq -r '
  .items[] | select(.roleRef.name == "cluster-admin") |
  "BINDING: \(.metadata.name)  SUBJECTS: \(
    [.subjects[]? | "\(.kind)/\(.namespace // "cluster")/\(.name)"] | join(", ")
  )"'

echo -e "\n=== Wildcard Verb ClusterRoles (full resource access) ==="
kubectl get clusterroles -o json | jq -r '
  .items[] | select(.rules[]? | .verbs[]? == "*") |
  "ROLE: \(.metadata.name)  RESOURCES: \(
    [.rules[] | select(.verbs[]? == "*") | .resources[]?] | unique | join(", ")
  )"'

echo -e "\n=== Service Accounts with Secret Access ==="
kubectl get clusterrolebindings rolebindings -A -o json 2>/dev/null | jq -r '
  .items[] | select(.subjects[]?.kind == "ServiceAccount") |
  "NS: \(.subjects[0].namespace)  SA: \(.subjects[0].name)  ROLE: \(.roleRef.name)"'

echo -e "\n=== Anonymous or Unauthenticated Bindings ==="
kubectl get clusterrolebindings -o json | jq -r '
  .items[] | select(.subjects[]? |
    .name == "system:anonymous" or .name == "system:unauthenticated") |
  "BINDING: \(.metadata.name)  ROLE: \(.roleRef.name)"'
```

**etcd forensic extraction with working examples.** These commands extract cluster state directly from etcd for forensic analysis of deleted or modified resources.

```bash
# Set etcd connection environment
export ETCDCTL_API=3
ETCD_ARGS="--endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key"

# Snapshot etcd for forensic preservation (before any recovery)
etcdctl $ETCD_ARGS snapshot save /forensics/etcd-snapshot-$(date -u +%Y%m%dT%H%M%SZ).db

# List all secrets (reveals attacker-created secrets)
etcdctl $ETCD_ARGS get /registry/secrets --prefix --keys-only

# Retrieve a specific secret's raw value
etcdctl $ETCD_ARGS get /registry/secrets/kube-system/compromised-secret --print-value-only | \
  python3 -c "import sys; data=sys.stdin.buffer.read(); print(data)"

# List all ClusterRoleBindings (detect attacker-created RBAC)
etcdctl $ETCD_ARGS get /registry/clusterrolebindings --prefix --keys-only

# List all pods (including attacker-created backdoor pods)
etcdctl $ETCD_ARGS get /registry/pods --prefix --keys-only | grep -v "kube-system"
```

**Container image scanning for incident triage.** During an active incident, scanning affected images identifies known vulnerabilities the attacker may have exploited.

```bash
# Trivy: scan a suspicious container image for CVEs
trivy image --severity HIGH,CRITICAL --format json \
  --output trivy-scan-$(date -u +%Y%m%dT%H%M%SZ).json \
  suspicious-image:latest

# Grype: alternative scanner with SBOM output
grype suspicious-image:latest -o json > grype-scan.json

# Check for specific container escape CVEs
trivy image --severity CRITICAL \
  --vuln-type os \
  --format table \
  suspicious-image:latest | grep -E "CVE-2019-5736|CVE-2020-15257|CVE-2022-0185"
```

**Container escape CVE detection artifacts summary.** The following table maps documented container escape CVEs to their specific forensic artifacts, beyond the general discussion in §4.4.

| CVE | Component | CVSS | CWE | Detection Artifact |
|---|---|---|---|---|
| CVE-2019-5736 | runc | 8.6 | CWE-78 | Modified `/usr/bin/runc` binary (timestamp/hash mismatch vs package), `/proc/*/fd` pointing to runc from container PID namespace |
| CVE-2020-15257 | containerd | 5.2 | CWE-669 | Abstract Unix socket connections `@/containerd-shim/*` from `--net=host` container, child processes outside container cgroup |
| CVE-2022-0185 | kernel (fsconfig) | 8.4 | CWE-787 | Modified `release_agent` in cgroup hierarchy, `notify_on_release=1` on unexpected cgroups, `devices.allow` set to `a *:* rwm` |
| CVE-2024-21626 | runc (1.1.11) | 8.6 | CWE-403 | Leaked file descriptors in `/proc/self/fd/*` pointing outside container rootfs, working directory set to host path |

---

## 5. Enterprise IR playbooks

### 5.1 Ransomware IR playbook

Ransomware incidents follow a predictable lifecycle that the IR team must interrupt at the optimal point. The playbook begins with **detection**: ransomware may be detected by EDR alerting on mass file encryption (unusual entropy changes, rapid file extension modifications), by users reporting encrypted files, by ransom notes appearing on desktops, by SIEM detecting communication with known ransomware C2 infrastructure (Domain 11 Chapter 11A §5 covers C2 detection), or by monitoring for Volume Shadow Copy deletion (`vssadmin delete shadows /all /quiet` — a hallmark of ransomware preparation that Sysmon Event ID 1 and Windows Security Event 4688 capture in command-line logging).

**Scoping** determines the blast radius: how many systems are encrypted, what data is affected, whether backup systems are compromised, and whether the attacker has maintained persistent access beyond the ransomware payload. The scoping phase requires immediate deployment of EDR queries across all endpoints (searching for ransomware-associated file extensions, ransom notes, known ransomware process names and hashes), network-level analysis (identifying C2 communication patterns in firewall and proxy logs, examining DNS query logs for known ransomware domains), and AD analysis (querying for recent account creations, group membership changes, and Kerberos anomalies — the attacker often compromises domain admin credentials before deploying ransomware, as described in Domain 14 Chapter 14A §3).

**Containment strategy — isolate versus monitor.** The fundamental containment decision is whether to immediately isolate affected systems (cutting network access to prevent further encryption spread but losing visibility into attacker activity) or to continue monitoring while implementing selective controls (maintaining visibility but risking further damage). The decision depends on: the encryption's current velocity (if encryption is actively spreading, immediate isolation is necessary), whether the attacker is still actively operating (live C2 sessions indicate ongoing threat-actor presence — monitoring may reveal the full scope of compromise), and the organization's risk tolerance. The recommended approach is a hybrid: immediately isolate systems where encryption is actively running (network isolation via EDR, firewall rules, or physical disconnection), while maintaining monitored access to systems that are not yet affected (deploying enhanced monitoring and containment measures without tipping off the attacker). Credential rotation must happen concurrently — the attacker's domain admin credentials must be invalidated before they can use them to deploy ransomware to unaffected systems.

**Credential rotation.** Ransomware operators typically hold domain administrator credentials (obtained via Kerberoasting, DCSync, LSASS dumping — Domain 14 Chapter 14A §3 covers these techniques). The IR team must reset: the `krbtgt` password (twice, with a 12-hour interval, to invalidate all existing Kerberos tickets — the double reset ensures both `krbtgt` password versions in AD are refreshed), all domain administrator passwords, all service account passwords, and all local administrator passwords (via LAPS or manual rotation). This credential rotation must happen rapidly and comprehensively — a single overlooked service account with domain admin privileges allows the attacker to re-compromise the environment.

**Backup integrity verification.** Before planning recovery, the IR team must verify that backup systems are intact. Ransomware operators increasingly target backup infrastructure: deleting Veeam backups, encrypting backup storage, compromising the backup admin account, and destroying offline/tape backups if accessible. The verification includes: checking the backup catalog for completeness (are recent backups present?), performing test restores of critical systems from backup (do the restored systems function correctly, and are they free of malware?), verifying that the backup infrastructure itself is not compromised (the backup server may have been the initial entry point or may contain attacker persistence), and checking air-gapped or immutable backup copies (these are the most reliable recovery source).

**Decryptor availability check.** Before considering negotiation, the IR team should check whether a free decryptor is available. Resources include the No More Ransom project (nomoreransom.org), vendor decryptor releases (Emsisoft, Kaspersky, and Bitdefender have released free decryptors for many ransomware families), and direct identification of the ransomware variant (using the ransom note, encrypted-file extension, and ID Ransomware at id-ransomware.malwarehunterteam.com). Some ransomware variants have implementation flaws that make decryption possible without paying the ransom — but using a decryptor does not address the underlying compromise; the attacker's access must still be eradicated.

**Negotiation considerations.** Ransom negotiation is a business decision, not a technical decision. The IR team provides the technical inputs (scope of damage, backup availability, recovery time estimates), while executive leadership, legal counsel, and (in some jurisdictions) regulatory bodies make the payment decision. Key technical inputs include: the estimated recovery time with and without payment, the reliability of the ransomware operator's decryption tools (some operators provide functional decryptors, others do not — threat-intelligence data on the specific operator's track record is relevant, drawing on Domain 25 Chapter 25A), the risk of re-extortion (some operators exfiltrate data before encrypting and threaten to publish it regardless of payment), and the regulatory implications (OFAC sanctions may prohibit payment to certain threat actors, and some jurisdictions require reporting ransom payments).

**Recovery sequence.** Recovery proceeds in a specific order: restore the identity infrastructure first (Active Directory domain controllers from known-good backups or clean rebuilds — a compromised DC re-compromises everything restored after it), then restore critical infrastructure services (DNS, DHCP, network management), then restore business-critical applications (in order of business priority), and finally restore user workstations. Each restored system should be hardened before reconnection: patched to current levels, local admin passwords rotated, endpoint protection verified, and monitoring enhanced.

**Post-incident hardening.** The lessons-learned phase should produce concrete hardening actions: implementing network segmentation to limit lateral movement, deploying EDR with ransomware-specific detections, implementing LAPS for local administrator passwords, enabling Protected Users group for domain admins, configuring backup immutability (WORM storage for backup repositories), and establishing regular tabletop exercises for ransomware scenarios.

**Sigma rules for ransomware precursor detection.** These rules detect the preparatory activities that precede ransomware deployment, providing an early-warning window.

```yaml
title: Volume Shadow Copy Deletion via vssadmin or wmic
id: 1a2b3c4d-5e6f-7a8b-9c0d-e1f2a3b4c5d6
status: stable
description: Detects VSS deletion commands used by ransomware before encryption
logsource:
  category: process_creation
  product: windows
detection:
  selection_vss:
    CommandLine|contains|all:
      - 'vssadmin'
      - 'delete'
      - 'shadows'
  selection_wmic:
    CommandLine|contains|all:
      - 'wmic'
      - 'shadowcopy'
      - 'delete'
  selection_ps:
    CommandLine|contains: 'Get-WmiObject Win32_ShadowCopy | ForEach-Object {$_.Delete()}'
  selection_bcdedit:
    CommandLine|contains|all:
      - 'bcdedit'
      - 'recoveryenabled'
      - 'no'
  condition: selection_vss or selection_wmic or selection_ps or selection_bcdedit
level: critical
tags:
  - attack.impact
  - attack.t1490
```

**Velociraptor VQL for ransomware impact assessment.** These hunts detect encrypted files and ransom notes across the fleet.

```sql
-- Hunt for files with known ransomware extensions added in the last 7 days
SELECT FullPath, Size, Mtime, Btime
FROM glob(globs="C:/Users/**/*.*")
WHERE FullPath =~ "\.(encrypted|locked|crypt|enc|WNCRY|cerber|locky|zepto|zzzzz|aaa|abc|xyz)$"
  AND Mtime > timestamp(epoch=now() - 7 * 86400)
LIMIT 10000

-- Hunt for ransom notes across all endpoints
SELECT FullPath, Size, Mtime, read_file(filename=FullPath, length=512) AS Preview
FROM glob(globs="C:/{Users,}/**/{README,RECOVER,DECRYPT,HOW_TO,RESTORE,HELP}*{.txt,.html,.hta}")
WHERE Size > 0 AND Size < 1048576
  AND Mtime > timestamp(epoch=now() - 7 * 86400)
```

### 5.2 BEC IR playbook

Business Email Compromise (BEC) investigations focus on the mailbox as the primary artifact. The playbook begins with **compromised mailbox investigation**: the investigator accesses the Unified Audit Log (§2.5) and mailbox audit logs to reconstruct the attacker's activity. The first task is identifying the initial compromise method — phishing (search for inbound emails with malicious links or attachments preceding the first anomalous sign-in), credential stuffing (sign-in logs showing failed attempts followed by a successful attempt from the same IP), or OAuth token theft (Azure AD audit logs showing consent grants to malicious applications).

**Mail flow rules and forwarding rules.** Attackers establish persistence in BEC by creating inbox rules that redirect or hide specific emails. The investigator checks: Outlook inbox rules (via Exchange Online PowerShell: `Get-InboxRule -Mailbox compromised@domain.com | Select Name, Description, Enabled, ForwardTo, ForwardAsAttachmentTo, RedirectTo, DeleteMessage, MarkAsRead`), transport rules created at the organization level (`Get-TransportRule | Where-Object {$_.State -eq 'Enabled'} | Select Name, Conditions, Actions`), mailbox forwarding settings (`Get-Mailbox compromised@domain.com | Select ForwardingAddress, ForwardingSmtpAddress, DeliverToMailboxAndForward`), and delegate access grants (`Get-MailboxPermission compromised@domain.com | Where-Object {$_.AccessRights -match 'FullAccess'}`). Attackers commonly create rules that move emails from specific senders (such as finance or legal departments) to the RSS Feeds or Deleted Items folder and mark them as read, hiding the emails from the legitimate user while the attacker reads them via the forwarding address.

**OAuth app audit.** Modern BEC increasingly uses OAuth consent-grant attacks: the attacker tricks the user into consenting to a malicious Azure AD application that requests Mail.Read, Mail.Send, and MailboxSettings.ReadWrite permissions. The malicious app then accesses the mailbox using the delegated permissions — without needing the user's password. The investigator audits OAuth applications: `Get-AzureADServicePrincipal | Where-Object {$_.PublisherName -notin @('Microsoft','Microsoft Services')} | Select DisplayName, AppId, ReplyUrls` identifies non-Microsoft service principals, and the Azure AD audit logs show consent grant events. Each suspicious application's permissions are reviewed and, if malicious, the consent is revoked and the application deleted.

**Financial impact assessment.** BEC frequently targets financial transactions: the attacker monitors email conversations between the victim and vendors/clients, then inserts themselves into the conversation (spoofing the vendor's email or using the compromised mailbox directly) to redirect wire transfers to attacker-controlled accounts. The investigator must: identify all financial conversations the attacker accessed (searching mailbox content for wire-transfer instructions, invoice numbers, banking details), determine whether any fraudulent transactions were initiated (coordinating with the finance department to verify recent payments against known vendor accounts), and initiate the fund-recovery process (contacting the receiving bank's fraud department — time is critical, as funds in mule accounts are moved quickly). The FBI's IC3 and the receiving bank should be notified within 24 to 72 hours for the best chance of fund recovery.

**Law enforcement coordination.** BEC investigations frequently involve law enforcement because of the financial crime element. The IR team should preserve all evidence in forensically sound formats (export Unified Audit Log entries, mailbox content, and sign-in logs as immutable records), prepare a timeline of the attacker's activities (from initial compromise to financial impact), and coordinate with the organization's legal counsel on reporting obligations (many jurisdictions require reporting financial fraud to law enforcement and data breaches to regulators).

### 5.3 Cloud account compromise playbook

When an IAM access key or service principal credential is compromised, the response must address both the immediate credential and the potential blast radius. The playbook begins with **key disable versus delete.** The compromised key should be deactivated immediately (`aws iam update-access-key --status Inactive` for AWS, disabling the service principal credential in Azure AD, disabling the service account key in GCP) — deactivation stops the attacker from using the credential while preserving the key's metadata for forensic analysis (creation date, creator, last-used information). Deletion should be deferred until the investigation concludes, because deleted credentials cannot be retrospectively analyzed.

**CloudTrail/audit-log analysis for blast radius.** Using the techniques from §1.7 (IAM forensics), the investigator reconstructs the complete timeline of the compromised credential's usage. The blast-radius analysis answers: what resources did the attacker access? what resources did the attacker create or modify? what other credentials did the attacker obtain? did the attacker establish persistence?

**Resource inventory for persistence mechanisms.** Cloud attackers establish persistence through multiple mechanisms that must be systematically enumerated and eradicated. In AWS, persistence mechanisms include: newly created IAM users and access keys (`aws iam list-users --query 'Users[?CreateDate>=`2026-05-01`]'`), newly created IAM roles with trust policies allowing external accounts, Lambda functions with backdoor code (`aws lambda list-functions` and inspecting each function's code), EC2 instances launched by the attacker (running C2 infrastructure or cryptominers), modified Lambda function code (legitimate functions with injected backdoor endpoints), SNS topics and SQS queues configured to forward data to attacker-controlled destinations, and cross-account role trust policies modified to allow the attacker's AWS account. Each persistence mechanism must be identified through systematic resource enumeration and CloudTrail analysis, then eradicated. The investigator should use AWS Config or a CSPM tool to compare the current resource state against the known-good baseline.

**Cross-account access investigation.** If the compromised credential had cross-account role-assumption capabilities (§1.8), the investigation must extend to all accounts the credential could reach. The investigator queries CloudTrail in each target account for AssumeRole events from the compromised principal, then conducts the same blast-radius and persistence analysis within each affected account. This cascading investigation can be extensive in large organizations with hundreds of interconnected AWS accounts.

**Automated credential rotation script.** The following script deactivates the compromised key, creates a replacement, and rotates associated secrets in AWS Secrets Manager — all with audit logging.

```bash
#!/usr/bin/env bash
# aws_cred_rotate.sh — Emergency credential rotation for compromised access key
set -euo pipefail

COMPROMISED_KEY="${1:?Usage: $0 <access-key-id> <username>}"
USERNAME="${2}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TIMESTAMP] Deactivating compromised key $COMPROMISED_KEY for user $USERNAME"
aws iam update-access-key \
  --access-key-id "$COMPROMISED_KEY" \
  --user-name "$USERNAME" \
  --status Inactive

echo "[$TIMESTAMP] Creating replacement access key"
NEW_KEY_JSON=$(aws iam create-access-key --user-name "$USERNAME" --output json)
NEW_KEY_ID=$(echo "$NEW_KEY_JSON" | jq -r '.AccessKey.AccessKeyId')
echo "[$TIMESTAMP] New key created: $NEW_KEY_ID"

# Rotate any Secrets Manager secrets that reference the old key
echo "[$TIMESTAMP] Scanning Secrets Manager for secrets referencing $COMPROMISED_KEY"
for secret_id in $(aws secretsmanager list-secrets --query 'SecretList[].Name' --output text); do
  secret_val=$(aws secretsmanager get-secret-value --secret-id "$secret_id" \
    --query 'SecretString' --output text 2>/dev/null || true)
  if echo "$secret_val" | grep -q "$COMPROMISED_KEY"; then
    echo "[$TIMESTAMP] FOUND: Secret '$secret_id' contains compromised key — rotating"
    updated_val=$(echo "$secret_val" | sed "s/$COMPROMISED_KEY/$NEW_KEY_ID/g")
    aws secretsmanager update-secret --secret-id "$secret_id" --secret-string "$updated_val"
  fi
done

echo "[$TIMESTAMP] Credential rotation complete. New key: $NEW_KEY_ID"
echo "[$TIMESTAMP] IMPORTANT: Update application configs referencing old key manually."
echo "[$TIMESTAMP] Old key $COMPROMISED_KEY is INACTIVE (preserved for forensics)."
```

### 5.4 Supply chain compromise playbook

Supply chain incidents (Domain 19 Chapter 19B covers the offensive taxonomy) require coordination between the affected organization, the compromised vendor, and the broader community. The playbook begins with **vendor notification**: the IR team contacts the vendor's security team through a verified channel (not email, which may be compromised) to inform them of the suspected compromise and request information about the incident's scope, timeline, and affected products.

**Indicator sharing.** The IR team extracts indicators of compromise (IOCs) from the affected systems — file hashes, C2 domains, IP addresses, network signatures, YARA rules — and shares them with: the vendor (for their investigation), industry ISACs (for peer warning), the organization's threat-intelligence platform (for internal detection — Domain 25 Chapter 25A), and relevant government agencies (CISA in the US, NCSC in the UK, ANSSI in France). IOC sharing should be structured (STIX format via TAXII feeds) and timely (within hours, not days).

**Dependency audit.** The IR team inventories all instances of the compromised component in the organization's environment: which systems run the affected software version? which build pipelines incorporate the compromised dependency? are there transitive dependencies (libraries that depend on the compromised library)? Software Bill of Materials (SBOM) tools — Syft, SPDX, CycloneDX — support this inventory. Each affected system is assessed for evidence of compromise: was the malicious payload activated? did it communicate with C2? did it exfiltrate data?

**Build pipeline integrity verification.** If the supply chain compromise targeted the organization's build pipeline (rather than an upstream vendor), the investigation must determine: whether build artifacts (compiled binaries, container images, deployment packages) were modified, whether build-system credentials were compromised (CI/CD secrets, signing keys, registry credentials), and whether the attacker established persistent access to the build infrastructure (backdoored build scripts, modified CI/CD configurations, compromised build agents). The IR team compares build outputs against known-good hashes, reviews CI/CD configuration changes in version control, and verifies the integrity of signing keys and certificates.

**YARA rules for known supply chain malware families.** These rules detect artifacts from documented supply chain compromises. Chapter 24A covers Cobalt Strike, Mimikatz, and Meterpreter; the rules below target supply-chain-specific implants.

```yara
rule SUNBURST_SolarWinds_Backdoor {
  meta:
    description = "Detects SUNBURST backdoor (SolarWinds Orion supply chain - 2020)"
    reference   = "CVE-2020-10148"
    severity    = "critical"
  strings:
    $api1 = "avsvmcloud.com" ascii wide
    $api2 = ".appsync-api.eu-west-1.avsvmcloud.com" ascii
    $cls1 = "OrionImprovementBusinessLayer" ascii
    $cls2 = "SolarWinds.Orion.Core.BusinessLayer" ascii
    $dga  = { 0F B6 ?? 83 ?? 61 00 00 00 [2-8] 83 ?? 1A }
  condition:
    uint16(0) == 0x5A4D and (any of ($api*) or all of ($cls*) or $dga)
}

rule XZ_Utils_Backdoor_Artifacts {
  meta:
    description = "Detects XZ Utils backdoor artifacts (CVE-2024-3094)"
    severity    = "critical"
  strings:
    $payload = { F3 0F 1E FA 55 48 89 E5 41 57 41 56 41 55 41 54 }
    $path1   = "liblzma.so.5" ascii
    $test1   = "bad-3-corrupt_lzma2.xz" ascii
    $build   = "build-to-host.m4" ascii
  condition:
    ($payload and $path1) or (all of ($test*, $build))
}

rule ThreeCX_DesktopApp_Trojanized {
  meta:
    description = "Detects trojanized 3CX Desktop App (supply chain - 2023)"
    severity    = "critical"
  strings:
    $icon_dll = "ffmpeg.dll" ascii wide
    $loader   = "d3dcompiler_47.dll" ascii wide
    $rc4_key  = "3jB(2bsG#@c7" ascii
    $gh_ico   = "raw.githubusercontent.com/IconStorages/images" ascii
  condition:
    uint16(0) == 0x5A4D and ($rc4_key or $gh_ico or (all of ($icon_dll, $loader)))
}
```

### 5.5 Insider threat playbook

Insider threat incidents require the most careful procedural handling because they involve employees, legal constraints, and potential criminal prosecution. The playbook begins with **legal coordination**: the IR team engages legal counsel before any investigation activity that could implicate an employee. Legal counsel advises on: employee privacy rights (which vary by jurisdiction), acceptable investigation techniques (monitoring, device seizure, account access), evidence-preservation requirements for potential litigation, and reporting obligations.

**Evidence preservation.** Evidence in insider threat cases must meet a higher standard of forensic integrity because it may be presented in court. The investigator preserves: the employee's workstation (forensic image per Chapter 24A §4.3), the employee's email (eDiscovery legal hold per §2.5), the employee's file access logs (DLP alerts, file-access audit logs, cloud storage access logs), the employee's network activity (proxy logs, VPN logs, firewall logs), and the employee's physical access logs (badge-reader logs, CCTV footage). Each piece of evidence must be handled with documented chain of custody (§7.1).

**UBA and DLP alert correlation.** User and Entity Behavior Analytics (UEBA) systems generate risk scores based on anomalous behavior patterns: unusual working hours, large data downloads, access to resources outside the employee's normal pattern, use of USB storage devices, and email to personal addresses with attachments. Data Loss Prevention (DLP) systems generate alerts when sensitive data is exfiltrated through monitored channels: email, web uploads, cloud storage, removable media, and printing. The investigator correlates UEBA risk-score escalations with DLP alerts to build the narrative: the employee's risk score increased over a two-week period as they began accessing databases outside their role, culminating in a DLP alert for a large export of customer records to personal email.

**HR integration.** The insider threat investigation ultimately intersects with HR processes: employee interviews, performance documentation, potential suspension or termination, and (in cases involving criminal activity) referral to law enforcement. The IR team provides HR with the technical evidence (sanitized to remove investigation methods that should remain confidential) and coordinates the timing of HR actions with evidence-preservation requirements — the employee should not be alerted to the investigation before all evidence is preserved.

---

## 6. Threat hunting in enterprise environments

### 6.1 Hypothesis-driven hunting

Chapter 24A §4.5 introduced hypothesis-driven hunting and ATT&CK-based hunt matrices. This section expands on the operational execution of enterprise hunt programs. A hunt hypothesis is a testable statement about adversary behavior in the environment: "An attacker may have established persistence via WMI event subscriptions on domain-joined Windows servers" (ATT&CK T1546.003). The hypothesis is generated from: current threat intelligence (a threat group targeting the organization's sector uses WMI persistence — Domain 25 Chapter 25A provides the intelligence), recent red-team findings (the organization's red team successfully used WMI persistence during a recent engagement), gap analysis (the organization's detection coverage has no rule for WMI event subscription creation), or peer sharing (another organization in the same ISAC reported WMI-based persistence in a recent incident).

**Data source selection.** Each hunt hypothesis requires specific data sources. For WMI event subscription hunting, the data sources include: Sysmon Event ID 19 (WmiEventFilter activity — records the creation of WMI event filters), Event ID 20 (WmiEventConsumer activity — records the creation of event consumers), Event ID 21 (WmiEventConsumerToFilter activity — records the binding of a consumer to a filter), Windows Event Log Microsoft-Windows-WMI-Activity/Operational (Event IDs 5857-5861 — records WMI provider load, subscription creation, and execution), and the WMI repository database (`OBJECTS.DATA` file at `C:\Windows\System32\wbem\Repository\`) which can be parsed offline for persistent subscriptions. The investigator must verify data-source availability before executing the hunt — if Sysmon is not deployed or WMI operational logging is not enabled, the hunt cannot proceed, and the finding is a detection-gap recommendation.

**Hunt execution.** The hunt query for WMI persistence using Sysmon data in a SIEM (Domain 27 Chapter 27A §2 covers SIEM architecture): `EventID:21 AND Consumer:"CommandLineEventConsumer"` identifies active WMI event subscription bindings that execute commands. The analyst reviews each result for legitimacy: known management tools (SCCM, monitoring agents) that use WMI subscriptions are excluded, leaving potentially malicious subscriptions for manual review. The analyst examines the consumer's command line, the filter's trigger condition (which events cause the consumer to fire), and the subscription's creation timestamp to determine whether it is malicious.

**Finding documentation.** Hunt findings are documented regardless of whether malicious activity was discovered. A null finding ("no evidence of WMI persistence was found") is still valuable — it establishes a detection baseline and demonstrates due diligence. A positive finding triggers the incident-response process from §5. All hunts are documented in the hunt log with: the hypothesis, the data sources queried, the query syntax, the number of results, the analysis conclusions, and any recommendations (new detection rules, data-source gaps to fill, hardening actions).

### 6.2 Proactive hunt operations

Mature threat-hunting programs operate three modes of hunting. **Scheduled hunts** are recurring hunts executed on a fixed cadence (weekly, biweekly, or monthly) based on a hunt calendar. The calendar is derived from the ATT&CK-mapped detection-coverage matrix: techniques with low detection coverage are prioritized for scheduled hunts. Each hunt is assigned to a hunter, who executes the hunt queries, analyzes results, and documents findings. **Ad-hoc hunts** are triggered by threat-intelligence inputs: a new CVE affecting a deployed technology (the hunt searches for exploitation evidence), a published report on a threat group targeting the sector (the hunt searches for the group's known TTPs), or an indicator shared by a peer organization. Ad-hoc hunts are time-sensitive and take priority over scheduled hunts. **Hunt-as-a-service** is a model where the threat-hunting team provides hunting capabilities to business units or subsidiaries on request — a business unit concerned about a specific threat can request a targeted hunt.

### 6.3 Specific hunt examples

**Hunting for persistence mechanisms.** Persistence is the most fruitful hunting ground because attackers must establish some form of persistence to maintain access across system reboots and credential rotations. The enterprise hunter systematically searches for each persistence mechanism: **Scheduled tasks** (ATT&CK T1053.005) — query `schtasks /query /fo CSV /v` across all endpoints via Velociraptor or osquery (`SELECT * FROM scheduled_tasks WHERE action LIKE '%cmd%' OR action LIKE '%powershell%' OR action LIKE '%wscript%' OR action LIKE '%mshta%'`), identifying tasks with suspicious actions (executing scripts from temporary directories, connecting to external URLs, running encoded PowerShell commands). **Services** (T1543.003) — `SELECT name, path_name, start_type, status FROM services WHERE path_name LIKE '%temp%' OR path_name LIKE '%appdata%' OR path_name NOT LIKE 'C:\\Windows%'` identifies services running from unusual paths. **Registry run keys** (T1547.001) — query `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`, `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, and the equivalent RunOnce keys across all endpoints, comparing against a baseline of known-good entries. **WMI subscriptions** (T1546.003) — as described in §6.1. **Startup folders** — enumerate `C:\Users\*\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\` and `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\` across endpoints.

**Hunting for lateral movement.** Lateral movement hunting examines network protocols and authentication events. **SMB** (T1021.002) — analyze Sysmon Event ID 3 (NetworkConnect) for outbound connections to port 445, correlating with Windows Security Event 4624 (Type 3 — network logon) on the destination host. Large numbers of SMB connections from a single source to many destinations in a short time indicate scanning or automated lateral movement. **WMI** (T1047) — Event ID 1 (ProcessCreate) for `wmiprvse.exe` spawning unexpected child processes on remote hosts, indicating remote WMI command execution. **PsExec** (T1569.002) — Event ID 7045 (new service installed) with service names matching PsExec's default naming pattern (`PSEXESVC`), or custom service names with suspicious binaries. **RDP** (T1021.001) — Windows Security Event 4624 (Type 10 — RemoteInteractive) from unusual source IPs or at unusual times. **WinRM** (T1021.006) — Event ID 4624 (Type 3) combined with PowerShell ScriptBlock logging (Event ID 4104) showing `Invoke-Command`, `Enter-PSSession`, or `New-PSSession` targeting remote hosts.

**Hunting for data exfiltration.** Exfiltration hunting requires combining network telemetry with endpoint activity. **DNS tunneling** (T1048.003) — analyze DNS query logs (Sysmon Event ID 22 or DNS server query logs) for queries with unusually long subdomain labels (DNS tunneling encodes data in the subdomain: `dGhpcyBpcyBhIHRlc3Q.evil.com`), high query volumes to a single domain (hundreds or thousands of queries per hour to the same domain), and queries for uncommon record types (TXT, NULL, CNAME responses with large payloads). **HTTP/S covert channels** (T1071.001) — proxy log analysis for connections with unusual characteristics: high upload-to-download ratio (normal browsing downloads more than it uploads), regular beaconing intervals (connections at consistent intervals — 60 seconds, 5 minutes — visible in statistical analysis of connection timing), connections to newly-registered or low-reputation domains, and large POST requests to unusual endpoints. **Cloud storage egress** — CASB logs or proxy logs showing uploads to personal cloud storage services (Dropbox, Google Drive, OneDrive personal, Mega) from corporate endpoints, particularly uploading archive files (`.zip`, `.7z`, `.rar`) or uploading volumes that exceed the user's historical baseline.

**Hunting for credential access.** Credential-theft hunting focuses on the techniques described in Domain 14 Chapter 14A §3 and Domain 30 Chapter 30B. **LSASS access patterns** (T1003.001) — Sysmon Event ID 10 (ProcessAccess) where `TargetImage` is `lsass.exe` and `GrantedAccess` includes `0x1010` (PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION) or `0x1FFFFF` (PROCESS_ALL_ACCESS). The `SourceImage` field reveals the tool performing the dump — common tools include `procdump.exe`, `rundll32.exe` (for comsvcs.dll MiniDump), `taskmgr.exe` (right-click → Create dump file), and custom tools masquerading as legitimate processes. **Kerberoasting traffic** (T1558.003) — Windows Security Event 4769 (Kerberos Service Ticket Request) where the `TicketEncryptionType` is `0x17` (RC4) rather than AES, the `ServiceName` targets a user account (not a machine account — machine accounts' SPNs are not useful for Kerberoasting), and the requesting account makes an unusual number of service-ticket requests in a short period. **DCSync replication** (T1003.006) — Windows Security Event 4662 where the `Properties` field includes the GUID for `DS-Replication-Get-Changes-All` (`{1131f6ad-9c07-11d1-f79f-00c04fc2dcd2}`) and the `Account Name` is not a domain controller machine account. This detection identifies any non-DC account performing directory replication — the hallmark of a DCSync attack using Mimikatz or Impacket's secretsdump.

### 6.4 Hunt automation

Enterprise-scale hunting requires automation to cover the breadth of the environment efficiently. **Velociraptor hunts** deploy VQL queries to all endpoints simultaneously: the hunt is defined as a VQL artifact (`SELECT * FROM Artifact.Windows.System.TaskScheduler() WHERE Command =~ 'powershell|cmd|wscript'`), scheduled against all clients (or a targeted label group), and results are collected in the Velociraptor server for centralized analysis. Hunts can be scheduled to run recurringly (implementing the scheduled-hunt model from §6.2).

**osquery scheduled queries** run at defined intervals on all endpoints. A scheduled query pack for persistence hunting includes: queries for scheduled tasks, services, registry run keys, WMI subscriptions, startup folder contents, cron jobs (Linux), and LaunchAgents/LaunchDaemons (macOS). Results are streamed to a log-aggregation platform (Domain 27 Chapter 27A) for centralized analysis. The differential-results feature (osquery reports only changes since the last run) reduces data volume and highlights new persistence mechanisms.

**Jupyter notebooks for hunt analysis** provide interactive, reproducible analysis environments. A hunt notebook imports data from the SIEM (via API), performs statistical analysis (baseline comparison, anomaly detection, clustering), visualizes results (timeline plots, network graphs, frequency distributions), and documents the analysis methodology. Notebooks are version-controlled and shared among the hunt team, building an institutional knowledge base of hunt techniques. Libraries such as `msticpy` (Microsoft's Threat Intelligence Python Security Tools) provide pre-built functions for common IR and hunting tasks: process-tree visualization, IP geolocation enrichment, threat-intelligence lookups, and timeline generation.

### 6.5 Cloud persistence hunt package

**Hypothesis.** An attacker who compromised cloud credentials has established persistence mechanisms (new IAM users, access keys, Lambda backdoors, OAuth apps) that survive credential rotation.

**Data sources.** AWS CloudTrail (management events), Azure Audit Logs, GCP Admin Activity logs.

**Queries.**

```sql
-- CloudTrail (Athena): IAM persistence indicators in the last 30 days
SELECT eventTime, eventName, userIdentity.arn AS actor,
       sourceIPAddress, requestParameters
FROM cloudtrail_logs
WHERE eventName IN ('CreateUser','CreateAccessKey','CreateRole','PutRolePolicy',
                    'CreateLoginProfile','AttachUserPolicy','UpdateAssumeRolePolicy')
  AND eventTime > date_add('day', -30, current_timestamp)
ORDER BY eventTime;
```

```kql
// Azure: service principal credential additions and app consent grants
AuditLogs
| where TimeGenerated > ago(30d)
| where OperationName in ("Add service principal credentials",
    "Consent to application", "Add app role assignment to service principal",
    "Add owner to application")
| project TimeGenerated, OperationName, InitiatedBy, TargetResources
| sort by TimeGenerated asc
```

```sql
-- BigQuery (GCP): service account key creation and IAM bindings
SELECT timestamp, protopayload_auditlog.methodName,
       protopayload_auditlog.authenticationInfo.principalEmail,
       protopayload_auditlog.requestMetadata.callerIp
FROM `project.audit_logs.cloudaudit_googleapis_com_activity_*`
WHERE protopayload_auditlog.methodName IN (
  'google.iam.admin.v1.CreateServiceAccountKey',
  'SetIamPolicy')
  AND _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
ORDER BY timestamp;
```

**Escalation criteria.** Any IAM entity creation or permission grant that cannot be attributed to a known provisioning workflow (Terraform state, CI/CD pipeline service account, approved change ticket) triggers a full incident investigation per §5.3.

### 6.6 Container escape hunt package

**Hypothesis.** An attacker has escaped container isolation and is operating on the host node or has deployed privileged pods for lateral movement.

**Falco rules** (deployed per §4.7). **K8s audit log queries:**

```bash
# Privileged pods created in the last 7 days (outside kube-system)
kubectl get pods -A -o json | jq '[.items[] |
  select(.spec.containers[].securityContext.privileged == true) |
  select(.metadata.namespace != "kube-system") |
  {ns: .metadata.namespace, name: .metadata.name,
   created: .metadata.creationTimestamp, node: .spec.nodeName}]'

# ClusterRoleBindings created in the last 7 days
kubectl get clusterrolebindings -o json | jq '[.items[] |
  select(.metadata.creationTimestamp > "2026-05-01T00:00:00Z") |
  {name: .metadata.name, role: .roleRef.name,
   subjects: [.subjects[]? | "\(.kind)/\(.name)"],
   created: .metadata.creationTimestamp}]'
```

**Response procedures.** Confirmed container escape triggers: (1) cordon and drain the affected node, (2) capture node memory and disk per §4.6, (3) rotate all service account tokens on the node, (4) audit all pods that were co-scheduled on the node for compromise indicators.

### 6.7 Hunt metrics and tracking

Effective hunt programs track KPIs to measure program maturity and value delivery.

| Metric | Description | Target |
|---|---|---|
| Hunts completed / quarter | Total scheduled + ad-hoc hunts executed | >= 12 |
| Mean time to hunt (MTTH) | Time from intelligence receipt to hunt execution | < 48 hours |
| True-positive rate | Hunts that produced confirmed findings | 10-25% |
| Detection coverage delta | New ATT&CK techniques covered post-hunt | +5% / quarter |
| Hunts producing new rules | Hunts that resulted in new Sigma/YARA detection rules | >= 30% |
| Dwell time reduction | Reduction in attacker dwell time attributed to hunting | Measurable QoQ decrease |

---

## 7. Evidence handling and legal considerations

### 7.1 Chain of custody documentation

Chain of custody is the documented chronological history of evidence from the moment of collection through analysis, storage, and potential presentation in court. Every evidence transfer (from the compromised system to the forensic workstation, from the analyst to the lab, from the lab to legal counsel) must be recorded with: the date and time of transfer (UTC, ISO 8601 format), the transferring party (name, role, organization), the receiving party (name, role, organization), the evidence description (including make, model, serial number for physical devices, or filename, hash, and size for digital evidence), the purpose of transfer, and the condition of the evidence at transfer. A break in the chain of custody (an undocumented gap in the evidence's handling history) can render evidence inadmissible in legal proceedings.

For digital evidence, integrity is maintained through cryptographic hashing. At the time of acquisition, the examiner computes a hash of the evidence (SHA-256 is the current standard; MD5 alone is insufficient due to collision vulnerabilities, though it is sometimes recorded alongside SHA-256 for backward compatibility). The hash is recorded in the chain-of-custody document and verified at every subsequent stage. If the hash changes, the evidence has been modified — intentionally or accidentally — and its integrity is compromised. Forensic imaging tools (dd with hashing via dcfldd/dc3dd, FTK Imager, Guymager) compute hashes during acquisition and verify them upon completion. The examiner should also hash the forensic image after transfer to the analysis workstation to verify that the transfer did not corrupt the data.

### 7.2 Forensic imaging standards

**ISO 27037** (Guidelines for identification, collection, acquisition and preservation of digital evidence) provides the international standard for digital-evidence handling. It defines the roles (Digital Evidence First Responder, Digital Evidence Specialist, Digital Evidence Analyst, Digital Evidence Examiner), the principles (minimizing modification, documenting all actions, maintaining chain of custody), and the procedures for acquiring evidence from: computers (powered-on and powered-off), mobile devices, network devices, and CCTV systems. ISO 27037 emphasizes that the acquisition process must be repeatable (another examiner following the same procedure should produce the same result) and auditable (every step is documented).

**NIST SP 800-86** (Guide to Integrating Forensic Techniques into Incident Response) provides the US government's guidance on forensic procedures within the IR lifecycle. It covers: data collection (preserving volatile and non-volatile data), examination (extracting relevant data from the collected evidence), analysis (interpreting the extracted data to identify artifacts of interest), and reporting (documenting the methods, findings, and conclusions). NIST SP 800-86 emphasizes the importance of using validated tools (tools whose output has been verified against known data sets) and documenting the tool versions used in each analysis.

### 7.3 Cloud evidence challenges

Cloud environments introduce fundamental challenges to traditional forensic principles. **Multi-tenancy** means that the organization's data resides on shared infrastructure — the forensic examiner cannot acquire the physical hardware (doing so would affect other tenants). Evidence acquisition is limited to the logical resources the organization controls: VM disk snapshots, log exports, database dumps, and API-retrieved metadata. The examiner cannot verify the integrity of the underlying hardware or hypervisor — they must trust the cloud provider's attestation (and contractual commitments) that the logical evidence has not been tampered with at the infrastructure level.

**Jurisdiction** creates complex legal questions. Data stored in a cloud region is subject to the laws of the country where that region is physically located. An organization headquartered in Germany using AWS `us-east-1` has data in the United States, subject to US legal processes (including law enforcement requests). If the same organization uses a multi-region deployment, its data may be simultaneously subject to the laws of multiple countries. The investigator must coordinate with legal counsel to determine: which country's laws govern the evidence, which country's courts may compel disclosure, and whether cross-border data transfer is permissible under applicable privacy regulations (GDPR, CCPA, PDPA).

**Data sovereignty** compounds the jurisdiction issue. Some regulations require that certain data types (personal data of citizens, health records, financial records) remain within the country's borders. A forensic investigation that requires exporting cloud evidence to an analysis lab in another country may violate data-sovereignty requirements. The investigator may need to conduct analysis within the same cloud region where the evidence resides, using a forensic workstation VM deployed in that region.

**Provider cooperation.** When the investigation requires evidence that the organization cannot access directly (hypervisor logs, physical infrastructure data, logs from other tenants that interacted with the compromised resources), the organization must request the cloud provider's cooperation. In the United States, the **CLOUD Act** (Clarifying Lawful Overseas Use of Data Act, 2018) allows US law enforcement to compel US-based cloud providers (AWS, Azure, GCP) to produce data stored anywhere in the world, and allows bilateral executive agreements between the US and foreign governments for reciprocal data access. Outside of law enforcement contexts, the organization's ability to obtain provider-held evidence depends on the contractual relationship (enterprise agreements may include forensic-support provisions) and the provider's policies. **Mutual Legal Assistance Treaties (MLATs)** provide the traditional mechanism for cross-border evidence requests between governments, though the MLAT process is slow (months to years) and is being supplemented by CLOUD Act bilateral agreements.

### 7.4 Expert witness preparation

When forensic findings may be presented in legal proceedings (criminal prosecution, civil litigation, regulatory enforcement), the forensic examiner must be prepared to testify as an expert witness. Preparation includes: reviewing all evidence and analysis notes before testimony (the examiner may not have access to the original evidence during testimony and must rely on reports and notes), understanding the legal standards for expert testimony in the relevant jurisdiction (in the US, the Daubert standard requires that expert testimony be based on sufficient facts or data, be the product of reliable principles and methods, and that the expert have reliably applied those principles and methods to the facts of the case), preparing to explain technical concepts to non-technical audiences (judges and juries require accessible explanations of filesystem forensics, memory analysis, and log interpretation without oversimplification that misrepresents the evidence), and anticipating cross-examination challenges (defense counsel will challenge the examiner's methodology, tool validation, chain of custody, and conclusions).

The examiner should maintain a record of: their qualifications (education, certifications such as GIAC GCFE, GCFA, GCIH, EnCE, CCE, training, and experience), the tools used and their validation status (has the tool been tested against known data sets? has the tool been accepted by other courts?), the methodology followed (referencing ISO 27037, NIST SP 800-86, or other recognized standards), and all deviations from standard procedure (with explanations of why the deviation was necessary and how it did not compromise the evidence).

### 7.5 Evidence admissibility requirements

Digital evidence must meet admissibility requirements that vary by jurisdiction but generally include: **authenticity** (the evidence is what it purports to be — established through chain of custody, hash verification, and examiner testimony), **reliability** (the evidence was collected and analyzed using reliable methods — established through tool validation, adherence to standards, and methodology documentation), **relevance** (the evidence is pertinent to the matter at hand — established by the attorney offering the evidence), and **completeness** (the evidence has not been selectively presented in a misleading way — the opposing party may request disclosure of all evidence, not just favorable portions).

In cloud-forensics cases, admissibility challenges are heightened. Defense counsel may argue that: the cloud provider's infrastructure could have been compromised (undermining evidence integrity), the logs produced by the cloud provider are hearsay (records generated by automated systems, not by human observation — though most jurisdictions have business-records exceptions that cover automated logs), the multi-tenancy environment makes it impossible to attribute actions to the defendant with certainty (other tenants could have generated the observed activity), and the chain of custody is broken because the evidence passed through the cloud provider's systems (the provider, not the examiner, controlled the evidence's storage and access). The forensic examiner's report must proactively address these challenges by documenting: the evidence-acquisition methodology (API calls used, timestamps, account used), the hash values computed at acquisition and verified at analysis, the cloud provider's service-level commitments regarding log integrity and access controls, and any limitations of the analysis (data that was not available, log gaps, ambiguities in attribution).

### 7.6 Forensic report writing

The forensic report is the primary deliverable of a forensic examination. It must be written for multiple audiences: the technical audience (IR team members, SOC analysts) who need precise technical details to take action, the executive audience (CISO, board, legal counsel) who need a business-impact summary, and potentially the legal audience (courts, regulators) who need a clear, defensible narrative supported by evidence.

A well-structured forensic report includes: an **executive summary** (one to two pages summarizing the incident, key findings, and recommendations — written last, after the detailed analysis is complete), a **scope and methodology** section (what evidence was examined, what tools were used with version numbers, what standards were followed, and what limitations exist), a **timeline** (a chronological narrative of the incident from initial compromise through detection, referencing specific evidence for each event — the timestamp, the log source, the event content, and the forensic significance), a **findings** section (organized by topic — initial access, persistence, lateral movement, data access, data exfiltration — each finding supported by specific evidence citations with hash references to the source evidence files), an **impact assessment** (what data was compromised, what systems were affected, what business operations were disrupted, and the estimated cost), a **recommendations** section (specific, actionable steps to prevent recurrence — not generic advice, but targeted hardening measures based on the attack path observed), and **appendices** (evidence inventory, hash values, tool output, raw log excerpts, and chain-of-custody forms). The report's technical accuracy must be verified before release — an incorrect hash, a misidentified process, or a wrong timestamp can undermine the entire report's credibility.

### 7.7 Chain of custody template

Every evidence item must be documented using a structured template. The following fields are mandatory for each entry in the chain-of-custody log.

| Field | Description | Example |
|---|---|---|
| Evidence ID | Unique identifier per case | IR-2026-05-08-EV-001 |
| Description | Type, source, content summary | EBS snapshot of vol-0abc123 (compromised web server OS disk) |
| Source System | Hostname, IP, cloud resource ARN | arn:aws:ec2:us-east-1:123456789012:volume/vol-0abc123 |
| Collected By | Name, role, organization | Jane Doe, Senior IR Analyst, SOC |
| Collection Time | UTC ISO 8601 | 2026-05-08T14:23:00Z |
| Collection Method | Tool, command, procedure | `aws ec2 create-snapshot --volume-id vol-0abc123` |
| Hash (SHA-256) | Integrity hash at collection | a1b2c3d4e5f6... (64 hex chars) |
| Storage Location | Physical or cloud path | s3://forensic-evidence-2026/IR-2026-05-08/snap-0abc.raw |
| Transfer Log | Each transfer: from, to, time, purpose | 2026-05-08T15:00Z: Jane Doe -> Forensic Lab (analysis) |
| Access Log | Each access: who, when, purpose | 2026-05-08T16:30Z: John Smith, disk mounting for timeline analysis |

### 7.8 Cloud evidence hash verification and immutable storage

**Hash verification for cloud evidence.** Cloud evidence requires hash verification at acquisition and at every subsequent access.

```bash
# AWS: verify S3 object integrity via ETag (MD5 for single-part uploads)
aws s3api head-object --bucket forensic-evidence-2026 \
  --key IR-2026-05-08/snapshot.raw \
  --query '{ETag: ETag, ContentLength: ContentLength, LastModified: LastModified}'

# Compute and record SHA-256 for EBS snapshot exported to raw image
sha256sum /forensics/IR-2026-05-08/snapshot.raw | tee -a /forensics/IR-2026-05-08/SHA256SUMS.txt

# Azure: verify blob integrity via Content-MD5 header
az storage blob show --container-name evidence --name forensic-snap.vhd \
  --account-name forensicsstorage \
  --query '{contentMd5: properties.contentSettings.contentMd5, lastModified: properties.lastModified}'

# GCP: verify Cloud Storage object integrity via CRC32C/MD5
gsutil stat gs://forensics-evidence/IR-2026-05-08/disk.raw
```

**Immutable evidence storage.** Cloud-native immutability features prevent evidence tampering — even by administrators with full access.

```bash
# AWS S3 Object Lock: create a bucket with immutable evidence retention
aws s3api create-bucket --bucket forensic-evidence-immutable \
  --object-lock-enabled-for-object-lock
aws s3api put-object-lock-configuration --bucket forensic-evidence-immutable \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {"DefaultRetention": {"Mode": "COMPLIANCE", "Days": 2555}}
  }'
# Upload evidence with Object Lock (cannot be deleted/overwritten for 7 years)
aws s3api put-object --bucket forensic-evidence-immutable \
  --key "IR-2026-05-08/snapshot.raw" --body /forensics/snapshot.raw \
  --object-lock-mode COMPLIANCE \
  --object-lock-retain-until-date "2033-05-08T00:00:00Z"

# Azure Immutable Blob Storage: set time-based retention policy
az storage container immutability-policy create \
  --resource-group forensics-rg \
  --account-name forensicsstorage \
  --container-name evidence \
  --period 2555
az storage container immutability-policy lock \
  --resource-group forensics-rg \
  --account-name forensicsstorage \
  --container-name evidence
```

**Legal hold automation for M365 eDiscovery.** The following PowerShell creates a legal hold to preserve all mailbox and OneDrive content for a compromised user.

```powershell
# Requires Security & Compliance PowerShell module
Connect-IPPSSession -UserPrincipalName admin@contoso.com

# Create an eDiscovery case
$caseName = "IR-2026-05-08-BEC"
New-ComplianceCase -Name $caseName -Description "BEC investigation 2026-05-08"

# Create a hold policy within the case
New-CaseHoldPolicy -Name "${caseName}-Hold" -Case $caseName `
  -ExchangeLocation "compromised@contoso.com" `
  -SharePointLocation "https://contoso-my.sharepoint.com/personal/compromised_contoso_com" `
  -Comment "Legal hold for IR - all content preserved"

# Create a hold rule (preserve all content, no date filter)
New-CaseHoldRule -Name "${caseName}-HoldRule" `
  -Policy "${caseName}-Hold" `
  -ContentMatchQuery "*"

# Verify hold is active
Get-CaseHoldPolicy -Identity "${caseName}-Hold" | Select-Object Name, Enabled, DistributionStatus
```

---

## 8. Cloud-native detection engineering

Cloud environments produce audit telemetry in provider-specific formats (CloudTrail JSON, Azure Activity Log JSON, GCP AuditLog protobuf-over-JSON) that require purpose-built detection rules. The Sigma rules and YARA rules in this section target attack patterns unique to or most impactful in cloud and container environments. They complement the host-centric detections in Chapter 24A §4.5 and the runtime Falco rules in §4.7 above.

### 8.1 Sigma rules for cloud audit events

Each rule below follows Sigma specification 2.0 and targets a normalized cloud audit log source. Deploy through the detection-engineering pipeline described in Domain 27 Chapter 27A, converting to the backend query language of the organization's SIEM (Splunk SPL, Elastic KQL, Microsoft Sentinel KQL, or Chronicle YARA-L).

**Rule 1 — CloudTrail logging disabled or stopped.**

An attacker's first action after gaining IAM access is often to disable CloudTrail to eliminate the audit trail. CVE-2024-28056 (AWS Amplify IAM role assumption issue — CVSS 9.8, CWE-863) demonstrated how misconfigured trust policies can yield credentials that are then used to tamper with logging infrastructure.

```yaml
title: CloudTrail Trail Stopped or Deleted
id: 7f3a8b2c-1d4e-5f6a-b7c8-9d0e1f2a3b4c
status: stable
description: >
  Detects StopLogging, DeleteTrail, or UpdateTrail calls that reduce
  visibility. Immediate SOC escalation required.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection_stop:
    eventName:
      - StopLogging
      - DeleteTrail
  selection_update:
    eventName: UpdateTrail
    requestParameters.isMultiRegionTrail: false
  condition: selection_stop or selection_update
falsepositives:
  - Legitimate trail reconfiguration during account migration (verify change ticket)
level: critical
tags:
  - attack.defense_evasion
  - attack.t1562.008
```

**Rule 2 — IAM privilege escalation chain.**

Detects the creation or attachment of permissive policies that grant administrator-level access. This pattern is characteristic of the Pacu AWS exploitation framework's `iam__privesc_scan` module.

```yaml
title: IAM Privilege Escalation via Policy Attachment
id: 2e9d7c6b-5a4f-3e2d-1c0b-a9f8e7d6c5b4
status: stable
description: >
  Detects attachment of AdministratorAccess, IAMFullAccess, or custom
  policies with * resource and * action to users or roles.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection_attach:
    eventName:
      - AttachUserPolicy
      - AttachRolePolicy
      - PutUserPolicy
      - PutRolePolicy
      - CreatePolicyVersion
  filter_managed_admin:
    requestParameters.policyArn|contains:
      - 'arn:aws:iam::aws:policy/AdministratorAccess'
      - 'arn:aws:iam::aws:policy/IAMFullAccess'
      - 'arn:aws:iam::aws:policy/PowerUserAccess'
  filter_inline_star:
    requestParameters.policyDocument|contains|all:
      - '"Effect":"Allow"'
      - '"Action":"*"'
      - '"Resource":"*"'
  condition: selection_attach and (filter_managed_admin or filter_inline_star)
falsepositives:
  - Break-glass procedure with approved change ticket
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1098.001
```

**Rule 3 — Cross-account role assumption from untrusted account.**

Detects `AssumeRole` events where the calling account is not part of the AWS Organization. An attacker who has modified a role's trust policy to permit external access triggers this pattern.

```yaml
title: Cross-Account AssumeRole from Non-Organization Account
id: 4a1b2c3d-8e7f-6a5b-4c3d-2e1f0a9b8c7d
status: experimental
description: >
  Flags AssumeRole calls where the requesting account ID is not in the
  known organization account list. Requires org_accounts lookup table.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventName: AssumeRole
    errorCode: ''
  filter_internal:
    userIdentity.accountId|expand: '%org_accounts%'
  condition: selection and not filter_internal
falsepositives:
  - Trusted third-party vendor accounts (maintain allowlist)
  - AWS service-linked roles (sourceIPAddress = AWS Internal)
level: high
tags:
  - attack.lateral_movement
  - attack.t1078.004
```

**Rule 4 — Container escape indicators in Kubernetes audit logs.**

Detects API server events that indicate privilege escalation within a cluster: creation of privileged pods outside the `kube-system` namespace, binding to `cluster-admin`, or mounting sensitive host paths.

```yaml
title: Kubernetes Privileged Pod or Host Mount Creation
id: 5b2c3d4e-9f0a-7b6c-5d4e-3f2a1b0c9d8e
status: experimental
description: >
  Detects creation of pods with privileged securityContext, hostPID,
  hostNetwork, or hostPath mounts of /, /etc, /var/run/docker.sock
  outside kube-system namespace.
logsource:
  product: kubernetes
  service: audit
detection:
  selection_create:
    verb: create
    objectRef.resource: pods
  filter_namespace:
    objectRef.namespace: kube-system
  selection_privileged:
    requestObject.spec.containers[*].securityContext.privileged: true
  selection_hostpid:
    requestObject.spec.hostPID: true
  selection_hostnet:
    requestObject.spec.hostNetwork: true
  selection_hostpath:
    requestObject.spec.volumes[*].hostPath.path|startswith:
      - '/'
      - '/etc'
      - '/var/run/docker.sock'
      - '/proc'
  condition: >
    selection_create and not filter_namespace and
    (selection_privileged or selection_hostpid or selection_hostnet or selection_hostpath)
falsepositives:
  - Legitimate monitoring DaemonSets (Datadog, Prometheus Node Exporter)
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1611
```

**Rule 5 — Serverless function code injection.**

Detects Lambda function code updates or new function creation from principals that are not the CI/CD pipeline service role. An attacker injects backdoor code into an existing function to persist access (the function executes attacker code on every invocation) or exfiltrate data from the function's environment.

```yaml
title: Lambda Function Code Modified Outside CI/CD Pipeline
id: 6c3d4e5f-0a1b-8c7d-6e5f-4a3b2c1d0e9f
status: experimental
description: >
  Detects UpdateFunctionCode or CreateFunction where the caller is not
  the known CI/CD deployment role. Requires cicd_roles lookup.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventName:
      - UpdateFunctionCode20150331v2
      - CreateFunction20150331
  filter_cicd:
    userIdentity.arn|expand: '%cicd_roles%'
  condition: selection and not filter_cicd
falsepositives:
  - Emergency hotfix by authorized developer (verify change ticket)
level: high
tags:
  - attack.persistence
  - attack.t1525
```

**Rule 6 — Cloud storage bulk exfiltration.**

Detects anomalous volumes of `GetObject` calls from a single principal within a short window. Calibrate the threshold to the environment's normal S3 read patterns.

```yaml
title: S3 Bulk Object Download Anomaly
id: 7d4e5f6a-1b2c-9d8e-7f6a-5b4c3d2e1f0a
status: experimental
description: >
  Alerts when a single IAM principal downloads more than 500 objects
  from a bucket within a 15-minute window. Threshold tunable.
logsource:
  product: aws
  service: cloudtrail
  category: data_event
detection:
  selection:
    eventName: GetObject
  timeframe: 15m
  condition: selection | count(requestParameters.key) by userIdentity.arn > 500
falsepositives:
  - ETL pipelines, backup jobs (allowlist by role ARN)
level: high
tags:
  - attack.exfiltration
  - attack.t1530
```

**Rule 7 — Identity federation abuse (SAML/OIDC token forging indicators).**

Detects suspicious patterns around federated identity usage: `AssumeRoleWithSAML` or `AssumeRoleWithWebIdentity` from source IPs that differ from the organization's IdP, or federation calls that set unusually long session durations. Golden SAML attacks (ATT&CK T1606.002), as executed in the SolarWinds SUNBURST campaign, forge SAML assertions to assume any role without authenticating to the IdP.

```yaml
title: Federated AssumeRole from Non-IdP Source IP
id: 8e5f6a7b-2c3d-0e9f-8a7b-6c5d4e3f2a1b
status: experimental
description: >
  Detects AssumeRoleWithSAML or AssumeRoleWithWebIdentity from source
  IPs outside the known IdP CIDR ranges. Requires idp_cidrs lookup.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventName:
      - AssumeRoleWithSAML
      - AssumeRoleWithWebIdentity
  filter_idp:
    sourceIPAddress|cidr:
      - '%idp_cidrs%'
  condition: selection and not filter_idp
falsepositives:
  - IdP failover to secondary DC with different egress IP
level: critical
tags:
  - attack.credential_access
  - attack.t1606.002
```

**Rule 8 — Azure Key Vault mass secret retrieval.**

Detects a principal retrieving an anomalous number of secrets from Azure Key Vault in a short window, indicating credential harvesting after initial access.

```yaml
title: Azure Key Vault Bulk Secret Retrieval
id: 9f6a7b8c-3d4e-1f0a-9b8c-7d6e5f4a3b2c
status: experimental
description: >
  Alerts when a single caller retrieves more than 20 secrets from a
  Key Vault within a 10-minute window.
logsource:
  product: azure
  service: keyvault
detection:
  selection:
    OperationName: SecretGet
    ResultType: Success
  timeframe: 10m
  condition: selection | count(ResultDescription) by identity.claim.appid > 20
falsepositives:
  - Application startup loading configuration secrets (allowlist by appId)
level: high
tags:
  - attack.credential_access
  - attack.t1552.004
```

### 8.2 Cloud-specific YARA rules

**YARA Rule — Crypto miner payloads in container images.**

Container images pulled from public registries or compromised private registries may contain embedded cryptocurrency miners. This rule detects XMRig and common Monero mining indicators in container layer tarballs or exported container filesystems.

```yara
rule Cloud_Container_CryptoMiner {
  meta:
    description = "Detects crypto mining binaries and configs in container images"
    severity    = "critical"
    target      = "Container image layers, exported container filesystems"
  strings:
    $xmrig_banner = "XMRig" ascii wide
    $xmrig_cfg1   = "\"algo\"" ascii
    $xmrig_cfg2   = "\"pools\"" ascii
    $xmrig_cfg3   = "\"url\"" ascii
    $stratum1     = "stratum+tcp://" ascii
    $stratum2     = "stratum+ssl://" ascii
    $stratum3     = "stratum+tls://" ascii
    $monero_addr  = /4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}/ ascii
    $pool_domain1 = "pool.minexmr.com" ascii
    $pool_domain2 = "xmrpool.eu" ascii
    $pool_domain3 = "pool.supportxmr.com" ascii
    $pool_domain4 = "monerohash.com" ascii
    $donate_lvl   = "--donate-level" ascii
    $elf_miner    = { 7F 45 4C 46 [0-64] 63 70 75 6D 69 6E 65 72 }
  condition:
    (uint32(0) == 0x464C457F or uint16(0) == 0x5A4D) and
    (
      ($xmrig_banner and 2 of ($xmrig_cfg*)) or
      any of ($stratum*) or
      $monero_addr or
      2 of ($pool_domain*) or
      ($donate_lvl) or
      $elf_miner
    )
}
```

**YARA Rule — Webshell in serverless deployment packages.**

Serverless deployment packages (Lambda ZIP files, Cloud Function source archives) may contain injected webshell code that provides the attacker with remote command execution on each function invocation. This rule targets PHP, Python, and Node.js webshell patterns within ZIP archives.

```yara
rule Serverless_Webshell_Payload {
  meta:
    description = "Detects webshell patterns in serverless deployment packages"
    severity    = "critical"
    target      = "Lambda ZIP packages, Cloud Function archives"
  strings:
    $py_exec1   = "exec(base64.b64decode(" ascii
    $py_exec2   = "__import__('os').popen(" ascii
    $py_exec3   = "subprocess.Popen(request" ascii
    $py_exec4   = "eval(compile(" ascii
    $node_exec1 = "child_process.exec(event" ascii
    $node_exec2 = "require('child_process').execSync(" ascii
    $node_exec3 = "Buffer.from(event.body,'base64')" ascii
    $php_exec1  = "eval($_" ascii
    $php_exec2  = "system($_GET" ascii
    $php_exec3  = "passthru($_REQUEST" ascii
    $generic1   = /eval\s*\(\s*base64_decode\s*\(/ ascii
    $generic2   = "fromCharCode" ascii
    $b64_cmd    = { 63 6D 51 67 [0-32] 7C 20 62 61 73 68 }
  condition:
    (
      uint32(0) == 0x04034B50 or   // ZIP magic (deployment package)
      uint16(0) == 0x8B1F or       // gzip (Cloud Functions)
      true                         // scan extracted files directly
    ) and
    (
      2 of ($py_exec*) or
      2 of ($node_exec*) or
      2 of ($php_exec*) or
      any of ($generic*) or
      $b64_cmd
    )
}
```

### 8.3 Multi-cloud detection event normalization

Effective multi-cloud detection requires normalizing provider-specific audit events into a unified schema. Without normalization, analysts must maintain separate rule sets per cloud, tripling operational overhead and creating coverage gaps during cross-cloud incidents.

**Unified Cloud Audit Event schema.** The following fields form the minimum viable normalized schema for detection engineering across AWS, Azure, and GCP. The schema is aligned with the Open Cybersecurity Schema Framework (OCSF) v1.1 and Elastic Common Schema (ECS) v8.x.

| Unified Field | AWS CloudTrail | Azure Activity Log | GCP Audit Log |
|---|---|---|---|
| `timestamp` | `eventTime` | `time` | `timestamp` |
| `cloud.provider` | `"aws"` | `"azure"` | `"gcp"` |
| `cloud.account.id` | `recipientAccountId` | `subscriptionId` | `resource.labels.project_id` |
| `cloud.region` | `awsRegion` | `location` | `resource.labels.location` |
| `actor.id` | `userIdentity.arn` | `caller` | `protoPayload.authenticationInfo.principalEmail` |
| `actor.type` | `userIdentity.type` | `claims.appid` / `claims.upn` | `protoPayload.authenticationInfo.serviceAccountKeyName` |
| `source.ip` | `sourceIPAddress` | `callerIpAddress` | `protoPayload.requestMetadata.callerIp` |
| `source.user_agent` | `userAgent` | `httpRequest.clientRequestId` | `protoPayload.requestMetadata.callerSuppliedUserAgent` |
| `action.name` | `eventName` | `operationName` | `protoPayload.methodName` |
| `action.service` | `eventSource` | `resourceProviderName` | `protoPayload.serviceName` |
| `action.outcome` | `errorCode` (null = success) | `resultType` | `protoPayload.status.code` (0 = success) |
| `resource.type` | derived from `eventSource` | `resourceType` | `resource.type` |
| `resource.id` | from `requestParameters` / `responseElements` | `resourceId` | `protoPayload.resourceName` |

**Normalization pipeline example (Python).** The following function normalizes a CloudTrail event to the unified schema. Equivalent functions for Azure and GCP follow the same pattern, mapping provider fields to unified fields.

```python
from datetime import datetime
from typing import Any

def normalize_cloudtrail(event: dict[str, Any]) -> dict[str, Any]:
    """Normalize a CloudTrail event to the unified cloud audit schema."""
    user_id = event.get("userIdentity", {})
    return {
        "timestamp": event["eventTime"],
        "cloud": {
            "provider": "aws",
            "account": {"id": event.get("recipientAccountId", "")},
            "region": event.get("awsRegion", ""),
        },
        "actor": {
            "id": user_id.get("arn", ""),
            "type": user_id.get("type", ""),
        },
        "source": {
            "ip": event.get("sourceIPAddress", ""),
            "user_agent": event.get("userAgent", ""),
        },
        "action": {
            "name": event["eventName"],
            "service": event.get("eventSource", ""),
            "outcome": "failure" if event.get("errorCode") else "success",
        },
        "resource": {
            "type": event.get("eventSource", "").split(".")[0],
            "id": _extract_resource_id(event),
        },
    }

def _extract_resource_id(event: dict[str, Any]) -> str:
    """Best-effort resource ID extraction from request/response."""
    resp = event.get("responseElements") or {}
    req = event.get("requestParameters") or {}
    for key in ("instanceId", "bucketName", "functionName", "userName",
                "roleName", "groupName", "volumeId", "snapshotId"):
        for source in (resp, req):
            if key in source:
                return str(source[key])
    return ""
```

Once events from all three providers are normalized, a single Sigma rule can target the unified schema. The Sigma `logsource.product` is set to `cloud_unified`, and the detection fields reference the unified schema — eliminating the need for per-provider rule variants.

---

## 9. Advanced cloud IR scenarios

### 9.1 Compromised CI/CD pipeline response

A compromised CI/CD pipeline is a supply-chain incident (§5.4 covers the broader taxonomy) with cloud-specific forensic requirements. The Codecov bash uploader compromise (2021) and the CircleCI secret exfiltration incident (January 2023) demonstrated how attackers leverage CI/CD pipelines to harvest secrets and inject malicious build artifacts.

**Artifact integrity verification.** The first response action is determining whether build outputs have been tampered with. For container images, compare the digest of every image pushed during the compromise window against a rebuild from known-good source:

```bash
# List all images pushed to ECR during the compromise window
aws ecr describe-images --repository-name app-service \
  --query 'imageDetails[?imagePushedAt>=`2026-05-01T00:00:00`] | sort_by(@, &imagePushedAt)' \
  --output table

# Rebuild from known-good commit and compare digests
git checkout <last-known-good-commit>
docker build --no-cache -t app-service:verify .
VERIFY_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' app-service:verify)
echo "Verification digest: $VERIFY_DIGEST"
# Compare against the ECR digest — mismatch indicates tampering
```

For Lambda deployment packages, compare `CodeSha256` across function versions:

```bash
# List all versions with code hashes
aws lambda list-versions-by-function --function-name my-function \
  --query 'Versions[].{Version:Version, CodeSha256:CodeSha256, Modified:LastModified}' \
  --output table
```

**Secret rotation post-CI/CD compromise.** Every secret accessible to the pipeline must be rotated — CI/CD systems typically have access to deployment credentials, database connection strings, API keys, and signing certificates. Enumerate secrets from the CI/CD platform's environment variable configuration and secret stores:

```bash
# GitHub Actions: audit repository secrets (requires admin token)
gh api repos/{owner}/{repo}/actions/secrets --jq '.secrets[].name'

# AWS Secrets Manager: list and tag secrets requiring rotation
aws secretsmanager list-secrets \
  --query 'SecretList[].{Name:Name, LastRotated:LastRotatedDate}' \
  --output table
```

**Build system forensics.** Examine CI/CD execution logs for the compromise window, focusing on: modified workflow files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`), unexpected environment variable access, network connections to external endpoints during builds, and injected build steps. In GitHub Actions, the workflow run API provides full execution logs:

```bash
# Download workflow run logs for analysis
gh run view <run-id> --log > /forensics/cicd/run-<run-id>.log
# Search for exfiltration indicators
grep -E '(curl|wget|nc |ncat|python.*http|base64.*decode)' \
  /forensics/cicd/run-<run-id>.log
```

### 9.2 Cloud ransomware response

Cloud ransomware differs fundamentally from endpoint ransomware: instead of encrypting local files with a symmetric key, the attacker leverages cloud-native encryption mechanisms. In AWS, this manifests as re-encrypting S3 objects or EBS volumes with an attacker-controlled KMS key, then deleting the original KMS key or denying the victim access to it.

**Encrypted S3 bucket response.** When an attacker uses `CopyObject` with `--sse-kms-key-id` pointing to their own key and then deletes the original objects (or the originals' KMS key grant), the response procedure is:

```bash
# 1. Identify the attacker's KMS key from CloudTrail
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CopyObject \
  --start-time 2026-05-01T00:00:00Z \
  --query 'Events[].CloudTrailEvent' --output text | \
  python3 -c "import sys,json; [print(json.loads(l).get('requestParameters',{}).get('x-amz-server-side-encryption-aws-kms-key-id','')) for l in sys.stdin]" | \
  sort -u

# 2. Check KMS key policy for the attacker's key
aws kms describe-key --key-id <attacker-key-id>
aws kms get-key-policy --key-id <attacker-key-id> --policy-name default

# 3. Attempt recovery: if versioning was enabled, restore previous versions
aws s3api list-object-versions --bucket compromised-bucket \
  --query 'Versions[?IsLatest==`false`].{Key:Key,VersionId:VersionId}' --output json
```

**KMS key policy analysis.** The attacker may have modified the KMS key policy to remove the victim's access or scheduled the key for deletion. CloudTrail events to review: `PutKeyPolicy`, `ScheduleKeyDeletion`, `DisableKey`, `CreateGrant` (granting the attacker's account access), and `RetireGrant` (removing the victim's grants). If the key is scheduled for deletion, `aws kms cancel-key-deletion --key-id <key-id>` can recover it within the waiting period (minimum 7 days).

**Snapshot-based recovery.** If EBS volumes were re-encrypted, recovery depends on whether snapshots exist with the original encryption. List available snapshots:

```bash
aws ec2 describe-snapshots --owner-ids self \
  --filters "Name=volume-id,Values=vol-compromised" \
  --query 'Snapshots[].{Id:SnapshotId,Time:StartTime,Encrypted:Encrypted,KmsKeyId:KmsKeyId}' \
  --output table
```

Snapshots encrypted with the organization's KMS key (not the attacker's) can be restored. AWS Backup vaults with vault lock (WORM) provide ransomware-resistant recovery points.

### 9.3 Insider threat in cloud environments

Cloud insider threats leverage legitimate access to exfiltrate data or sabotage infrastructure in ways that blend with normal operations. Detection requires behavioral baselines and cross-signal correlation.

**IAM activity pattern analysis.** Baseline each principal's API call patterns (services accessed, time-of-day, source IP ranges) over a 30-day window. Deviation detection uses CloudTrail Lake or Athena:

```sql
-- Athena: identify services a principal accessed for the first time in the last 7 days
WITH historical AS (
  SELECT DISTINCT useridentity.arn AS principal, eventsource
  FROM cloudtrail_logs
  WHERE eventtime BETWEEN date_add('day', -37, now()) AND date_add('day', -7, now())
),
recent AS (
  SELECT DISTINCT useridentity.arn AS principal, eventsource
  FROM cloudtrail_logs
  WHERE eventtime > date_add('day', -7, now())
)
SELECT r.principal, r.eventsource AS new_service
FROM recent r
LEFT JOIN historical h ON r.principal = h.principal AND r.eventsource = h.eventsource
WHERE h.eventsource IS NULL
ORDER BY r.principal;
```

**Data exfiltration detection via VPC Flow Logs.** An insider staging data for exfiltration may increase egress volume gradually to avoid threshold-based alerts. Statistical analysis of per-principal egress trends over 30-day windows detects ramp-up patterns. Combine Flow Log volume data with CloudTrail `GetObject`/`Query` events to attribute network egress to specific data-access operations.

**SaaS audit trails.** Insider activity often spans cloud IaaS and SaaS platforms simultaneously. Correlate AWS/Azure/GCP audit events with:

- **Microsoft 365 Unified Audit Log**: `Search-UnifiedAuditLog -Operations FileDownloaded,FileAccessed,MailItemsAccessed` for bulk document or email access.
- **Google Workspace**: Admin SDK Reports API `activities.list` for Drive file downloads, Gmail delegated access, and Admin Console changes.
- **Salesforce**: Event Monitoring `EventLogFile` records for `Login`, `Report`, `ReportExport`, and `BulkApiResult` events — a user exporting all customer records via Bulk API is a high-severity indicator.

### 9.4 SaaS breach response

SaaS platform compromises require response procedures that operate entirely through the platform's administrative APIs — the organization has no access to the underlying infrastructure.

**OAuth token revocation.** When a malicious OAuth application has been consented to, revoke all tokens and remove the application:

```powershell
# Azure AD / Entra ID: revoke consent and remove the malicious app
$appId = "malicious-app-client-id"
$sp = Get-AzureADServicePrincipal -Filter "AppId eq '$appId'"

# Revoke all OAuth2 permission grants
Get-AzureADServicePrincipalOAuth2PermissionGrant -ObjectId $sp.ObjectId |
  Remove-AzureADOAuth2PermissionGrant

# Remove delegated and application permission assignments
Get-AzureADServiceAppRoleAssignment -ObjectId $sp.ObjectId |
  Remove-AzureADServiceAppRoleAssignment -ObjectId $sp.ObjectId

# Delete the service principal
Remove-AzureADServicePrincipal -ObjectId $sp.ObjectId
```

```bash
# Google Workspace: revoke third-party app tokens for a user
# Requires Directory API admin access
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://admin.googleapis.com/admin/directory/v1/users/compromised@example.com/tokens" | \
  jq -r '.items[].clientId' | while read client_id; do
    curl -s -X DELETE -H "Authorization: Bearer $ADMIN_TOKEN" \
      "https://admin.googleapis.com/admin/directory/v1/users/compromised@example.com/tokens/$client_id"
    echo "Revoked token for app: $client_id"
done
```

**M365 audit log analysis for BEC.** Beyond the procedures in §5.2, programmatic audit-log analysis scales to large tenant investigations:

```powershell
# Extract all mail-forwarding rule changes in the last 30 days
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-30) -EndDate (Get-Date) `
  -Operations "Set-Mailbox","New-InboxRule","Set-InboxRule","UpdateInboxRules" `
  -ResultSize 5000 |
  Select-Object CreationDate, UserIds, Operations, AuditData |
  Export-Csv -Path /forensics/m365_forwarding_rules.csv -NoTypeInformation
```

### 9.5 Multi-cloud incident coordination

When an incident spans multiple cloud providers (common in organizations using AWS for compute, Azure for identity via Entra ID, and GCP for data analytics), coordination challenges multiply.

**Evidence preservation across providers.** Issue evidence-collection commands to all affected providers in parallel to minimize the window between detection and preservation:

```bash
#!/usr/bin/env bash
# multi_cloud_preserve.sh — Parallel evidence preservation across providers
set -euo pipefail
INCIDENT_ID="${1:?Usage: $0 <incident-id>}"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVIDENCE_BASE="/forensics/${INCIDENT_ID}"
mkdir -p "$EVIDENCE_BASE"/{aws,azure,gcp}

# AWS: snapshot compromised volumes + export CloudTrail
aws ec2 create-snapshot --volume-id vol-compromised \
  --description "IR-${INCIDENT_ID}" \
  --tag-specifications "ResourceType=snapshot,Tags=[{Key=Incident,Value=${INCIDENT_ID}}]" \
  > "$EVIDENCE_BASE/aws/snapshot.json" &

aws cloudtrail lookup-events --start-time 2026-05-01T00:00:00Z \
  --max-results 1000 --output json \
  > "$EVIDENCE_BASE/aws/cloudtrail_events.json" &

# Azure: export Activity Log + capture disk snapshot
az monitor activity-log list --start-time 2026-05-01T00:00:00Z \
  --output json > "$EVIDENCE_BASE/azure/activity_log.json" &

az snapshot create --resource-group forensics-rg \
  --name "ir-${INCIDENT_ID}-${TIMESTAMP}" \
  --source /subscriptions/.../disks/compromised-disk \
  > "$EVIDENCE_BASE/azure/snapshot.json" &

# GCP: export audit logs + snapshot disk
gcloud logging read \
  'logName="projects/my-project/logs/cloudaudit.googleapis.com%2Factivity"
   AND timestamp>="2026-05-01T00:00:00Z"' \
  --format=json --limit=5000 \
  > "$EVIDENCE_BASE/gcp/audit_logs.json" &

gcloud compute disks snapshot compromised-disk \
  --snapshot-names="ir-${INCIDENT_ID}-${TIMESTAMP}" \
  --zone=us-central1-a &

wait
echo "[+] Evidence preserved across all providers in $EVIDENCE_BASE"

# Hash all evidence files
find "$EVIDENCE_BASE" -type f ! -name SHA256SUMS.txt -exec sha256sum {} + \
  > "$EVIDENCE_BASE/SHA256SUMS.txt"
```

**Timeline synchronization.** AWS uses UTC for all CloudTrail timestamps. Azure Activity Logs use UTC. GCP Audit Logs use UTC with RFC 3339 formatting. Despite all three using UTC, timestamp precision varies: CloudTrail provides second-level precision, Azure provides millisecond precision, and GCP provides microsecond precision. The normalized timeline must account for clock drift between provider log-ingestion pipelines (typically <2 seconds but occasionally larger during provider-side delays). When correlating events across providers, use a ±5 second correlation window for related actions.

---

## 10. Cloud forensics automation

### 10.1 Automated evidence collection

Manual evidence collection during a cloud incident is slow (minutes per resource), error-prone (missing volumes, wrong regions), and poorly documented (ad-hoc commands without audit trail). Automated collection triggered by detection alerts reduces response time from minutes to seconds.

**AWS Lambda auto-snapshot on GuardDuty finding.** The following Lambda function, triggered by GuardDuty findings via EventBridge, automatically snapshots all EBS volumes attached to a flagged EC2 instance.

```python
"""Auto-snapshot Lambda triggered by GuardDuty EC2 findings via EventBridge."""
import boto3
import json
import os
from datetime import datetime, timezone

ec2 = boto3.client("ec2")
sns = boto3.client("sns")
FORENSIC_TOPIC = os.environ["FORENSIC_SNS_TOPIC"]
FORENSIC_KMS_KEY = os.environ["FORENSIC_KMS_KEY_ID"]

def handler(event: dict, context) -> dict:
    detail = event["detail"]
    finding_type = detail["type"]
    severity = detail["severity"]

    # Only act on HIGH/CRITICAL findings for EC2 instances
    if severity < 7.0:
        return {"status": "skipped", "reason": f"severity {severity} below threshold"}

    instance_id = (
        detail.get("resource", {})
        .get("instanceDetails", {})
        .get("instanceId")
    )
    if not instance_id:
        return {"status": "skipped", "reason": "no instance ID in finding"}

    # Get all volumes attached to the instance
    reservations = ec2.describe_instances(InstanceIds=[instance_id])
    volumes = []
    for r in reservations["Reservations"]:
        for inst in r["Instances"]:
            for bdm in inst.get("BlockDeviceMappings", []):
                vol_id = bdm["Ebs"]["VolumeId"]
                volumes.append(vol_id)

    # Snapshot each volume with forensic metadata
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshots = []
    for vol_id in volumes:
        snap = ec2.create_snapshot(
            VolumeId=vol_id,
            Description=f"Auto-forensic: {finding_type} on {instance_id}",
            TagSpecifications=[{
                "ResourceType": "snapshot",
                "Tags": [
                    {"Key": "ForensicCapture", "Value": "true"},
                    {"Key": "SourceInstance", "Value": instance_id},
                    {"Key": "FindingType", "Value": finding_type},
                    {"Key": "CaptureTime", "Value": timestamp},
                ],
            }],
        )
        snapshots.append(snap["SnapshotId"])

    # Notify IR team
    sns.publish(
        TopicArn=FORENSIC_TOPIC,
        Subject=f"[IR] Auto-snapshot: {instance_id}",
        Message=json.dumps({
            "instance_id": instance_id,
            "finding_type": finding_type,
            "severity": severity,
            "snapshots": snapshots,
            "timestamp": timestamp,
        }, indent=2),
    )
    return {"status": "captured", "snapshots": snapshots}
```

**Azure Function for automatic disk snapshot.** The equivalent automation in Azure, triggered by Microsoft Defender for Cloud alerts via Event Grid:

```bash
# Deploy via Azure CLI — the function triggers on Defender alerts
az functionapp create --resource-group forensics-rg \
  --consumption-plan-location eastus \
  --runtime python --runtime-version 3.11 \
  --functions-version 4 \
  --name forensic-auto-capture \
  --storage-account forensicsstorage

# Event Grid subscription for Defender alerts
az eventgrid event-subscription create \
  --name forensic-trigger \
  --source-resource-id "/subscriptions/<sub-id>/resourceGroups/<rg>" \
  --endpoint "/subscriptions/<sub-id>/resourceGroups/forensics-rg/providers/Microsoft.Web/sites/forensic-auto-capture/functions/auto-snapshot" \
  --included-event-types "Microsoft.Security.AlertCreated"
```

### 10.2 Forensic pipeline automation

A mature cloud IR program builds an automated forensic pipeline that receives evidence (snapshots, log exports) and produces analysis-ready artifacts without manual intervention.

**Pipeline stages:**

1. **Ingest** — Evidence arrives in a dedicated forensic S3 bucket / Azure Blob container / GCS bucket (immutable storage, §7.8).
2. **Mount** — An EC2/VM forensic workstation automatically mounts the snapshot as a read-only volume.
3. **Extract** — Automated tools extract forensic artifacts: filesystem timeline (using `plaso`/log2timeline), browser artifacts, SSH keys, cron jobs, systemd services, bash history, and container overlay diffs.
4. **Analyze** — Extracted artifacts are indexed into an Elasticsearch/OpenSearch cluster for interactive investigation. YARA scans run against the filesystem. Sigma rules run against extracted log files.
5. **Report** — Automated report generation produces a preliminary findings document with timeline, IOCs, and YARA/Sigma hits.

```bash
# Example: automated plaso timeline generation from a forensic EBS snapshot
# Run on a forensic workstation EC2 instance

SNAP_ID="snap-0abc123"
EVIDENCE_VOL=$(aws ec2 create-volume --snapshot-id "$SNAP_ID" \
  --availability-zone us-east-1a --volume-type gp3 --query 'VolumeId' --output text)
aws ec2 wait volume-available --volume-ids "$EVIDENCE_VOL"

INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
DEVICE="/dev/xvdf"
aws ec2 attach-volume --volume-id "$EVIDENCE_VOL" --instance-id "$INSTANCE_ID" \
  --device "$DEVICE"
sleep 10  # wait for device attachment

mkdir -p /mnt/evidence
mount -o ro,noatime,noexec "${DEVICE}1" /mnt/evidence

# Generate Plaso timeline
log2timeline.py --storage-file /forensics/timeline.plaso /mnt/evidence
psort.py -o l2tcsv -w /forensics/timeline.csv /forensics/timeline.plaso

# YARA scan
yara -r /forensics/rules/cloud_ir.yar /mnt/evidence > /forensics/yara_hits.txt

echo "[+] Automated extraction complete"
```

### 10.3 SOAR integration for cloud IR

Security Orchestration, Automation, and Response (SOAR) platforms coordinate multi-step incident response workflows. A cloud IR playbook in a SOAR platform (Cortex XSOAR, Splunk SOAR, Tines, Shuffle) chains the containment, evidence-collection, analysis, and remediation steps into an automated workflow with human decision gates at critical points.

**SOAR playbook structure for cloud account compromise:**

1. **Trigger** — SIEM alert or GuardDuty finding for suspicious IAM activity.
2. **Enrich** — Automated lookups: `GetCallerIdentity` for the compromised principal, CloudTrail query for recent activity, threat-intelligence lookup on source IPs.
3. **Contain** — Automated actions with human approval gate: deactivate access keys, attach a deny-all IAM policy to the compromised user/role, revoke active sessions (`aws sts revoke-sessions`-equivalent by updating role's trust policy with a date condition).
4. **Collect** — Trigger the automated evidence-collection Lambda (§10.1), export CloudTrail events for the compromise window, snapshot affected resources.
5. **Analyze** — Run automated analysis pipeline (§10.2), generate preliminary timeline, execute YARA and Sigma scans.
6. **Remediate** — After analyst review: delete attacker-created persistence (users, keys, roles, Lambda functions), restore modified resources from known-good state, rotate all potentially compromised credentials.
7. **Close** — Generate incident report, update threat-intelligence platform with new IOCs, create detection-rule improvements, conduct lessons-learned review.

```yaml
# Pseudocode SOAR playbook definition (Tines-style)
---
name: Cloud Account Compromise Response
trigger:
  type: webhook
  source: guardduty_eventbridge
steps:
  - name: enrich_principal
    action: aws_cli
    command: >
      aws cloudtrail lookup-events
      --lookup-attributes AttributeKey=AccessKeyId,AttributeValue={{trigger.access_key_id}}
      --start-time {{trigger.event_time | date_add: -24h}}
      --max-results 500

  - name: contain_decision
    action: human_approval
    message: "Deactivate key {{trigger.access_key_id}}? Activity summary attached."
    timeout: 15m
    default: approve

  - name: deactivate_key
    action: aws_cli
    condition: contain_decision.approved
    command: >
      aws iam update-access-key
      --access-key-id {{trigger.access_key_id}}
      --status Inactive
      --user-name {{enrich_principal.username}}

  - name: collect_evidence
    action: invoke_lambda
    function: forensic-auto-capture
    payload:
      instance_id: "{{enrich_principal.instance_id}}"
      incident_id: "{{trigger.incident_id}}"

  - name: notify_ir_team
    action: slack_message
    channel: "#incident-response"
    message: >
      Cloud account compromise detected.
      Principal: {{enrich_principal.arn}}
      Key deactivated: {{trigger.access_key_id}}
      Evidence collection: in progress
```

### 10.4 Infrastructure as Code for forensic readiness

Deploying forensic infrastructure manually during an incident wastes critical response time. Pre-deploying forensic roles, logging configurations, and evidence-storage buckets through IaC ensures readiness.

**Terraform module for AWS forensic readiness:**

```hcl
# modules/forensic-readiness/main.tf

resource "aws_s3_bucket" "evidence" {
  bucket        = "forensic-evidence-${var.account_id}"
  force_destroy = false

  tags = {
    Purpose = "Forensic evidence storage"
    ManagedBy = "terraform"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = var.retention_days  # default 2555 (7 years)
    }
  }
}

resource "aws_s3_bucket_versioning" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_iam_role" "ir_responder" {
  name = "IncidentResponseRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = var.security_account_arn }
      Action    = "sts:AssumeRole"
      Condition = {
        Bool = { "aws:MultiFactorAuthPresent" = "true" }
      }
    }]
  })
}

resource "aws_iam_role_policy" "ir_responder" {
  name = "IRResponderPolicy"
  role = aws_iam_role.ir_responder.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadOnlyForensics"
        Effect   = "Allow"
        Action   = [
          "ec2:DescribeInstances", "ec2:DescribeVolumes",
          "ec2:DescribeSnapshots", "ec2:CreateSnapshot",
          "ec2:CopySnapshot",
          "cloudtrail:LookupEvents", "cloudtrail:GetTrailStatus",
          "guardduty:ListFindings", "guardduty:GetFindings",
          "iam:ListUsers", "iam:ListAccessKeys",
          "iam:GetAccessKeyLastUsed", "iam:GetCredentialReport",
          "iam:GenerateCredentialReport",
          "s3:GetObject", "s3:ListBucket",
          "logs:FilterLogEvents", "logs:GetLogEvents",
          "lambda:GetFunction", "lambda:ListVersionsByFunction",
        ]
        Resource = "*"
      },
      {
        Sid      = "EvidenceStorage"
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.evidence.arn}/*"
      },
      {
        Sid      = "ContainmentActions"
        Effect   = "Allow"
        Action   = [
          "iam:UpdateAccessKey",
          "iam:PutUserPolicy",
          "ec2:ModifyInstanceAttribute",
          "ec2:CreateSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress",
        ]
        Resource = "*"
        Condition = {
          StringEquals = { "aws:RequestTag/Purpose" = "IncidentResponse" }
        }
      }
    ]
  })
}

resource "aws_cloudwatch_event_rule" "guardduty_high" {
  name        = "guardduty-high-severity"
  description = "Route high-severity GuardDuty findings to forensic Lambda"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail      = { severity = [{ numeric = [">=", 7.0] }] }
  })
}

resource "aws_cloudwatch_event_target" "forensic_lambda" {
  rule      = aws_cloudwatch_event_rule.guardduty_high.name
  target_id = "forensic-auto-capture"
  arn       = var.forensic_lambda_arn
}

variable "account_id" { type = string }
variable "security_account_arn" { type = string }
variable "retention_days" { type = number; default = 2555 }
variable "forensic_lambda_arn" { type = string }
```

---

## 11. Cloud security posture and forensic readiness

### 11.1 Logging architecture for forensic readiness

Forensic readiness begins with ensuring that the logs needed for investigation exist, are complete, and are retained long enough to cover the typical attacker dwell time (median 16 days per CrowdStrike 2025 Global Threat Report, but advanced persistent threats dwell for months).

**What to log (minimum):**

| Provider | Log Source | Forensic Value | Minimum Retention |
|---|---|---|---|
| AWS | CloudTrail management events (all regions) | Control-plane audit trail | 1 year (CloudTrail Lake) or S3 lifecycle |
| AWS | CloudTrail data events (S3, Lambda) | Data-access forensics | 90 days minimum, 1 year for regulated data |
| AWS | VPC Flow Logs (V5, all VPCs) | Network forensics, exfiltration detection | 90 days |
| AWS | GuardDuty findings | Threat-detection baseline | Retained by GuardDuty (90 days default, archive to S3) |
| Azure | Activity Log | Control-plane audit trail | 1 year (export to Log Analytics / Storage) |
| Azure | Entra ID Sign-in + Audit Logs | Identity forensics | 1 year (Entra P2 retains 30 days; export for longer) |
| Azure | NSG Flow Logs | Network forensics | 90 days |
| Azure | Key Vault Diagnostics | Secret-access forensics | 1 year |
| GCP | Admin Activity audit logs | Control-plane audit trail | 400 days (default, free) |
| GCP | Data Access audit logs | Data-access forensics | 30 days default — **increase via custom retention** |
| GCP | VPC Flow Logs | Network forensics | 30 days default — export to Cloud Storage |
| K8s | API server audit logs (Metadata+Request) | Cluster-level forensics | 90 days minimum |

**Retention-period rationale.** One year for control-plane logs covers the tail of long-dwell intrusions and satisfies most compliance frameworks (SOC 2 Type II, ISO 27001 Annex A.12.4, PCI DSS Requirement 10.7, FedRAMP AU-11). Ninety days for high-volume data-plane logs balances storage cost against forensic utility. GCP Data Access logs require explicit enablement and custom retention configuration — the 30-day default is forensically inadequate for most organizations.

### 11.2 Evidence preservation automation

Cloud-native immutability features (introduced in §7.8) should be deployed proactively as part of the logging architecture, not configured after an incident.

**S3 Object Lock for CloudTrail logs.**

```bash
# Create a dedicated trail-log bucket with Object Lock
aws s3api create-bucket --bucket cloudtrail-immutable-${ACCOUNT_ID} \
  --object-lock-enabled-for-object-lock --region us-east-1

aws s3api put-object-lock-configuration \
  --bucket cloudtrail-immutable-${ACCOUNT_ID} \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Days": 365
      }
    }
  }'

# Point the organization trail to this bucket
aws cloudtrail update-trail --name org-trail \
  --s3-bucket-name cloudtrail-immutable-${ACCOUNT_ID}
```

**Azure immutable storage for diagnostic logs.**

```bash
az storage account create --name auditimmutable${RANDOM_SUFFIX} \
  --resource-group logging-rg --location eastus \
  --sku Standard_LRS --kind StorageV2

az storage container create --name audit-logs \
  --account-name auditimmutable${RANDOM_SUFFIX}

az storage container immutability-policy create \
  --resource-group logging-rg \
  --account-name auditimmutable${RANDOM_SUFFIX} \
  --container-name audit-logs \
  --period 365

az storage container immutability-policy lock \
  --resource-group logging-rg \
  --account-name auditimmutable${RANDOM_SUFFIX} \
  --container-name audit-logs
```

**GCP retention policies for audit logs exported to Cloud Storage.**

```bash
# Create a bucket with a 365-day retention policy (locked = irreversible)
gsutil mb -l us-central1 gs://audit-logs-immutable-${PROJECT_ID}
gsutil retention set 365d gs://audit-logs-immutable-${PROJECT_ID}
gsutil retention lock gs://audit-logs-immutable-${PROJECT_ID}

# Create a log sink to export audit logs to this bucket
gcloud logging sinks create audit-export \
  "storage.googleapis.com/audit-logs-immutable-${PROJECT_ID}" \
  --log-filter='logName:"cloudaudit.googleapis.com"' \
  --project=${PROJECT_ID}
```

### 11.3 Forensic readiness maturity model

Organizations should assess their cloud forensic readiness against a maturity model to identify gaps before an incident occurs.

| Level | Capability | Indicators |
|---|---|---|
| **1 — Ad Hoc** | No pre-planned forensic capability | Logs at provider defaults, no evidence-storage buckets, no IR roles, manual collection only |
| **2 — Reactive** | Basic logging enabled, manual collection | CloudTrail/Activity Log enabled, some Flow Logs, evidence collected manually during incidents, no automation |
| **3 — Defined** | Documented forensic procedures | Written IR playbooks, dedicated evidence buckets, IR roles pre-deployed, log retention policies defined and enforced |
| **4 — Managed** | Automated evidence collection | GuardDuty/Defender triggers automated snapshots, SOAR playbooks for common scenarios, forensic pipeline extracts artifacts automatically, immutable evidence storage |
| **5 — Optimized** | Continuous improvement, cross-cloud | Multi-cloud normalized detection, automated forensic pipeline across all providers, forensic readiness metrics tracked, regular tabletop exercises validate procedures, detection coverage mapped to ATT&CK Cloud matrix |

### 11.4 Cross-cloud evidence chain of custody

Multi-cloud incidents require a chain-of-custody process that spans provider boundaries. Each evidence item must document: the cloud provider and region of origin, the API call used for acquisition (with exact CLI command and timestamp), the account and principal that performed the acquisition, the hash computed at acquisition, and the storage location (which may differ from the origin provider — e.g., GCP disk snapshot exported and stored in AWS S3 for centralized analysis).

**Cross-cloud evidence registry.** Maintain a centralized evidence registry (a structured JSON or database table, not a spreadsheet) that records every evidence item across all providers:

```json
{
  "evidence_id": "IR-2026-05-08-EV-014",
  "incident_id": "IR-2026-05-08",
  "cloud_provider": "gcp",
  "cloud_project": "prod-analytics-12345",
  "cloud_region": "us-central1",
  "resource_type": "persistent_disk_snapshot",
  "resource_id": "projects/prod-analytics-12345/global/snapshots/ir-snap-20260508",
  "acquisition_command": "gcloud compute disks snapshot analytics-db --snapshot-names=ir-snap-20260508 --zone=us-central1-a",
  "acquisition_time": "2026-05-08T14:45:22Z",
  "acquisition_principal": "ir-responder@security-project.iam.gserviceaccount.com",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "storage_location": "gs://forensics-evidence-12345/IR-2026-05-08/analytics-db-snap.raw",
  "storage_immutable": true,
  "retention_until": "2033-05-08T00:00:00Z",
  "transfer_log": [
    {
      "from": "ir-responder@security-project.iam.gserviceaccount.com",
      "to": "forensic-analyst@security-project.iam.gserviceaccount.com",
      "time": "2026-05-08T16:00:00Z",
      "purpose": "Timeline analysis"
    }
  ]
}
```

### 11.5 Regulatory compliance mapping for forensic requirements

Compliance frameworks impose specific forensic-readiness requirements that map to the capabilities described in this chapter.

| Requirement | SOC 2 (CC7.2-CC7.4) | ISO 27001 (A.12.4, A.16.1) | FedRAMP (AU, IR, SI) | PCI DSS v4.0 (Req 10, 12.10) |
|---|---|---|---|---|
| Audit log retention | >= 1 year | Risk-based (typically 1 year) | >= 1 year online, 3 years total | >= 1 year, 3 months immediately available |
| Log integrity | Tamper-evidence required | Tamper protection (A.12.4.2) | AU-9: Protection of audit info | 10.3.2: Detect tampering |
| Incident response plan | Required with testing | A.16.1.1: IR management procedure | IR-1 through IR-8 | 12.10.1: IR plan, annual test |
| Evidence preservation | Forensic artifacts retained | A.16.1.7: Collection of evidence | IR-4(1): Automated IR support | 12.10.5: Alert monitoring |
| Log monitoring | Real-time alerting required | A.12.4.1: Event logging | SI-4: Information system monitoring | 10.6.1: Review daily |
| Cross-provider logging | Implied by scope | A.15.1: Supplier relationships | CA-3: Third-party connections | 12.8: Service provider management |

**Compliance automation.** Map each compliance requirement to a specific technical control:

- **Audit log retention >= 1 year**: S3 Object Lock (§11.2), Azure immutable storage (§11.2), GCP retention lock (§11.2).
- **Log integrity / tamper-evidence**: CloudTrail log file validation (`--enable-log-file-validation`), Azure immutability policy lock, GCP bucket retention lock.
- **IR plan with testing**: SOAR playbooks (§10.3) provide automated IR plan execution; tabletop exercises validate playbook coverage.
- **Evidence preservation**: Automated evidence collection (§10.1) triggered by alerts ensures timely preservation. Immutable storage prevents post-collection tampering.
- **Real-time alerting**: GuardDuty + EventBridge (§1.2), Defender for Cloud alerts (§2.3), GCP Security Command Center findings (§3.2) — all feed detection rules from §8.

---

## 12. Cross-references

**To Domain 10 (cloud and containers).** The cloud forensics procedures in §1 through §3 build on the cloud-security architecture described in Domain 10 Chapter 10A (IAM, IMDS, S3/GCS/Blob security models, CloudTrail/Audit Log fundamentals). The container and Kubernetes forensics in §4 extend the container-security concepts from Domain 10 Chapter 10B (namespaces, cgroups, seccomp, pod security contexts). Container-escape evidence collection (§4.4) directly references the escape techniques catalogued in Domain 10 Chapter 10B §2.

**To Domain 11 (malware analysis).** The ransomware IR playbook (§5.1) depends on the ransomware analysis techniques from Domain 11 Chapter 11A §5 for variant identification and C2 infrastructure mapping. GuardDuty findings (§1.2) and Falco alerts (§4.3) detect the malware behaviors described in Domain 11 Chapter 11A (injection, process hollowing, C2 beaconing).

**To Domain 14 (Active Directory).** The credential-access hunting techniques (§6.3) detect the AD attack paths from Domain 14 Chapter 14A §3: DCSync (Event 4662), Kerberoasting (Event 4769 with RC4 encryption), and LSASS credential dumping (Sysmon Event 10). The ransomware playbook's credential-rotation procedures (§5.1) address the domain-admin compromise scenarios from Domain 14 Chapter 14A.

**To Domain 19 (supply chain).** The supply chain compromise playbook (§5.4) implements the incident-response procedures for the supply chain attack vectors described in Domain 19 Chapter 19B. Container image provenance verification (§4.1) with Cosign and Sigstore addresses the build-pipeline integrity concerns from Domain 19 Chapter 19B §3. The CI/CD pipeline compromise response (§9.1) extends the supply chain IR procedures with cloud-specific artifact verification and secret rotation.

**To Domain 25 (threat intelligence).** Hypothesis-driven hunting (§6.1) consumes threat intelligence from Domain 25 Chapter 25A to generate hunt hypotheses and prioritize techniques. The ransomware playbook (§5.1) uses threat-intelligence data on ransomware operator reliability and decryptor availability from Domain 25.

**To Domain 27 (defense and detection).** Hunt automation (§6.4) integrates with the SIEM architecture from Domain 27 Chapter 27A §2 for centralized log query and alert management. Sigma rules referenced in Chapter 24A §4.5 are deployed through the detection-engineering pipeline described in Domain 27 Chapter 27A. The cloud-native Sigma rules in §8.1 follow the same deployment pipeline but target cloud audit log sources. SOAR integration (§10.3) connects the automated IR workflows to the SOAR platforms described in Domain 27 Chapter 27A §4.

**To Chapter 24A (DFIR foundations).** The cloud-native detection rules in §8 complement the host-centric Sigma and YARA rules from Chapter 24A §4.5. The forensic pipeline automation in §10.2 uses the same artifact-extraction tools (plaso, Volatility, YARA) described in Chapter 24A §1-§2 but orchestrated through cloud-native automation. The evidence handling procedures in §7 extend the forensic imaging standards from Chapter 24A §4.3 to cloud environments.

**To compliance and governance.** The forensic readiness maturity model (§11.3) and compliance mapping (§11.5) connect forensic capabilities to organizational governance requirements. SOC 2 CC7.2-CC7.4 mandate IR testing and evidence preservation capabilities that are implemented through the automation described in §10 and the logging architecture in §11.1.

---

## Exercises

1. **AWS CloudTrail forensic timeline reconstruction.** Given a simulated AWS account compromise (provided access key ID and time window), use the Python `boto3` CloudTrail `lookup_events` paginator to extract all API calls for the compromised key. Export to CSV, identify the reconnaissance phase (`Describe*`/`List*` calls), the privilege-escalation phase (`AttachUserPolicy`/`CreateAccessKey`), and the data-access phase (`GetObject`/`GetSecretValue`). Correlate with VPC Flow Logs via Athena to identify data-exfiltration volume.

2. **Azure VM disk acquisition and BEC investigation.** Create a snapshot of a compromised Azure VM's managed disk using `az snapshot create`. Export the snapshot as a VHD via SAS URI, mount read-only on a forensic workstation using `qemu-nbd`, and extract the `NTUSER.DAT` registry hive. Separately, use `Search-UnifiedAuditLog` in PowerShell to search for `New-InboxRule`, `Set-Mailbox`, and `Add-MailboxPermission` events for the compromised user, identifying attacker-created forwarding rules and delegate access.

3. **GKE Kubernetes incident response.** In a GKE cluster with audit logging enabled, investigate a simulated container-escape incident. Query Cloud Logging for `k8s_cluster` resource-type audit events showing `kubectl exec` sessions, RBAC modifications (`ClusterRoleBinding` creation), and privileged pod deployments. Correlate with Falco alerts for `container.privileged=true` and `syscall=setns`. Document the attacker's path from initial pod access through node-level privilege escalation.

4. **Ransomware IR playbook execution.** In a lab environment with three Windows VMs (domain controller, file server, workstation) and simulated ransomware indicators, execute the full ransomware IR playbook: (a) contain via Velociraptor quarantine artifact, (b) scope via fleet-wide hash hunt, (c) collect evidence via KAPE triage, (d) identify persistence mechanisms via registry and scheduled-task analysis, (e) document the attack timeline from initial access through encryption, and (f) draft a post-incident lessons-learned report.

5. **Cloud evidence chain-of-custody documentation.** For a simulated multi-cloud investigation spanning AWS and Azure, create a complete chain-of-custody package: document all evidence items (EBS snapshots, CloudTrail exports, Azure Activity Log exports, memory dumps) with SHA-256 hashes, acquisition timestamps in UTC ISO 8601 format, examiner identity, and storage locations. Evaluate CLOUD Act and MLAT implications for evidence stored in EU-region Azure data centers accessed by a US-based investigation team.

---

## Readings and References

- NIST SP 800-86 — *Guide to Integrating Forensic Techniques into Incident Response*. <https://csrc.nist.gov/pubs/sp/800/86/final> (retrieved: 2026-05-29)
- NIST SP 800-61 Rev. 2 — *Computer Security Incident Handling Guide*. <https://csrc.nist.gov/pubs/sp/800/61/r2/final> (retrieved: 2026-05-29)
- ISO/IEC 27037:2012 — *Guidelines for identification, collection, acquisition and preservation of digital evidence*. <https://www.iso.org/standard/44381.html> (retrieved: 2026-05-29)
- AWS CloudTrail documentation — event reference and Lake SQL. <https://docs.aws.amazon.com/cloudtrail/> (retrieved: 2026-05-29)
- Microsoft Learn — Azure forensics and incident response. <https://learn.microsoft.com/en-us/azure/security/fundamentals/cyber-services> (retrieved: 2026-05-29)
- GCP Cloud Audit Logs documentation. <https://cloud.google.com/logging/docs/audit> (retrieved: 2026-05-29)
- Velociraptor documentation — cloud and container artifacts. <https://docs.velociraptor.app/> (retrieved: 2026-05-29)
- Falco — cloud-native runtime security. <https://falco.org/docs/> (retrieved: 2026-05-29)
- CISA — *Cloud Security Technical Reference Architecture*. <https://www.cisa.gov/cloud-security-technical-reference-architecture> (retrieved: 2026-05-29)
- The CLOUD Act (Clarifying Lawful Overseas Use of Data Act), 18 U.S.C. § 2713. <https://www.congress.gov/bill/115th-congress/house-bill/4943> (retrieved: 2026-05-29)

---

## Cross-Reference Matrix

| Domain / Chapter | Relationship to This Chapter | Key Linked Sections |
|---|---|---|
| Domain 10 — Cloud & Containers | Cloud-security architecture (IAM, IMDS, S3 policies) and container security (namespaces, cgroups, escape techniques) | §1–§3, §4 |
| Domain 11 — Malware Analysis | Ransomware variant identification, C2 infrastructure mapping for IR playbooks | §5.1, §6.3 |
| Domain 14 — Active Directory | Credential-access detection (DCSync, Kerberoasting, LSASS dumping) in enterprise IR | §6.3, §5.1 |
| Domain 19 — Supply Chain | Supply chain compromise playbook, container image provenance verification (Cosign, Sigstore) | §5.4, §4.1 |
| Domain 24A — DFIR Foundations | Host-level disk/memory forensics, Plaso timelines, YARA/Sigma rules complementing cloud detections | §8, §10.2 |
| Domain 25 — Threat Intelligence | Hypothesis-driven hunting consumes TI; ransomware playbook uses TI on operator reliability | §6.1, §5.1 |

---

## Glossary

- **Activity Log (Azure):** Management-plane audit log recording all Azure Resource Manager operations with caller identity, operation name, status, and correlation ID.
- **ASFF (AWS Security Finding Format):** Standardized JSON schema used by AWS Security Hub to normalize findings from GuardDuty, Inspector, Macie, and third-party tools.
- **Chain of custody:** Documented record of evidence handling from acquisition through presentation, including timestamps, handler identity, hash values, and storage locations.
- **CLOUD Act:** US federal law (2018) enabling US law enforcement to compel US-based cloud providers to produce data regardless of where the data is physically stored.
- **CloudTrail Lake:** AWS managed query engine providing SQL-based analysis of CloudTrail events with configurable retention up to seven years.
- **EBS snapshot:** Point-in-time, crash-consistent copy of an EC2 volume used as the primary disk-acquisition method in AWS forensics.
- **Falco:** Open-source cloud-native runtime security tool that detects anomalous syscall behavior in containers and Kubernetes pods.
- **GuardDuty:** AWS managed threat-detection service consuming CloudTrail, VPC Flow Logs, DNS logs, and EKS audit logs to generate security findings.
- **ISO 27037:** International standard providing guidelines for identification, collection, acquisition, and preservation of digital evidence.
- **KQL (Kusto Query Language):** Query language used in Azure Log Analytics workspaces and Microsoft Sentinel for forensic log analysis.
- **MLAT (Mutual Legal Assistance Treaty):** Bilateral agreement between countries for exchanging evidence in criminal investigations, relevant when cloud data is stored in foreign jurisdictions.
- **NSG Flow Logs:** Azure Network Security Group traffic metadata logs capturing source/destination tuples, bytes, packets, and allow/deny decisions.
- **Unified Audit Log (UAL):** Microsoft 365 centralized audit log recording events across Exchange Online, SharePoint, OneDrive, Teams, and Azure AD.
- **VPC Flow Logs:** AWS network traffic metadata logs capturing IP tuples, ports, protocols, bytes, packets, TCP flags, and traffic path information.
