# Domain 31 — Detection Engineering and SOC Architecture at Scale

## Chapter 31A — SIEM/SOAR Pipeline Design, Detection-as-Code, and Threat Intelligence Operationalization

> **Scope:** Log pipeline architecture for conglomerate-scale environments — ingestion, normalization, enrichment, storage, and query tiers · Data engineering fundamentals for security telemetry — schema design, field normalization (ECS, OCSF, CIM), timestamp standardization, deduplication · SIEM architecture patterns — centralized vs. federated, hot/warm/cold tiering, query performance at petabyte scale · Detection-as-Code — Sigma rule language internals, YARA-L, SPL/KQL comparison, detection lifecycle management, CI/CD for detections, unit testing, alert tuning · SOAR design patterns — playbook architecture, enrichment orchestration, automated response actions, human-in-the-loop decision points · Threat intelligence operationalization — STIX/TAXII, indicator lifecycle management, TI platform integration, diamond model application, attribution confidence calibration · Alert triage optimization — alert fatigue quantification, precision/recall tradeoffs, alert prioritization frameworks, SOC analyst workflow design · Detection coverage mapping to MITRE ATT&CK — gap analysis, coverage scoring, purple team validation

---

## 1. Log Pipeline Architecture at Conglomerate Scale

A conglomerate defending thousands of subsidiary companies faces a data engineering problem before it faces a detection problem. The telemetry volume from endpoints, network devices, identity systems, cloud platforms, and applications across thousands of entities produces data rates measured in terabytes per day. The detection pipeline must ingest, normalize, enrich, store, and query this data with sufficient performance to detect attacks within the dwell-time window (industry median: 10 days for externally discovered compromises, per Mandiant M-Trends).

### 1.1 Ingestion Tier

The ingestion tier receives raw telemetry from heterogeneous sources and delivers it to the normalization layer. At scale, this tier must handle sustained throughput of hundreds of thousands of events per second (EPS) with burst capacity for incident-related spikes.

**Transport protocols:** Syslog (UDP/TCP/TLS) remains the dominant transport for network infrastructure (firewalls, routers, switches, proxies). Modern endpoint agents (CrowdStrike Falcon, Microsoft Defender for Endpoint, SentinelOne) use proprietary HTTPS-based transports to their cloud backends, with detection events forwarded to the SIEM via API integrations or streaming connectors. Cloud platform logs (AWS CloudTrail, Azure Activity Log, GCP Audit Log) are delivered via cloud-native mechanisms: S3 bucket subscriptions, Event Hub, or Pub/Sub. Application logs use structured formats (JSON over HTTPS, or message queue protocols like Kafka, AMQP, or MQTT).

**Message queue architecture:** A message queue (Apache Kafka is the de facto standard for security pipelines at scale) decouples producers (log sources) from consumers (normalization, enrichment, and storage services). Kafka topics are partitioned by log source type (endpoint telemetry, network flow, authentication events, cloud audit) to enable independent scaling of consumption pipelines. The queue provides backpressure handling (if the downstream SIEM cannot keep up, events buffer in Kafka rather than being dropped), replay capability (events can be re-consumed from a configurable retention window, typically 7–30 days, enabling pipeline reprocessing after schema changes or normalization bug fixes), and fan-out (multiple consumers can read the same topic independently—the SIEM, a threat hunting data lake, and a compliance archive can all consume from the same Kafka stream).

**Windows Event Forwarding (WEF).** WEF is a native Windows mechanism for centralized event collection. The collector (Windows Event Collector service, `wecsvc`) receives events pushed by forwarders (all domain-joined Windows endpoints via WinRM). Configuration via GPO:

```
Computer Configuration → Policies → Administrative Templates → Windows Components →
  Event Forwarding → Configure target Subscription Manager
  → Server=http://collector.domain.local:5985/wsman/SubscriptionManager/WEC

# Collector-side: create subscription
wecutil cs subscription.xml
```

Subscription XML defines which events to collect:
```xml
<QueryList>
  <Query Id="0" Path="Security">
    <Select Path="Security">*[System[(EventID=4624 or EventID=4625 or EventID=4648
      or EventID=4662 or EventID=4768 or EventID=4769 or EventID=5136)]]</Select>
  </Query>
  <Query Id="1" Path="Microsoft-Windows-Sysmon/Operational">
    <Select Path="Microsoft-Windows-Sysmon/Operational">*</Select>
  </Query>
  <Query Id="2" Path="Microsoft-Windows-PowerShell/Operational">
    <Select Path="Microsoft-Windows-PowerShell/Operational">*[System[(EventID=4104)]]</Select>
  </Query>
</QueryList>
```

WEF advantages: no agent installation required (native to Windows), GPO-managed, source-side filtering reduces network bandwidth. Limitations: WinRM transport overhead, maximum ~10,000 endpoints per collector (scale-out via multiple collectors), no built-in queuing (events are dropped if the collector is unavailable).

**Collection agents comparison:**

| Agent | Protocol | Strengths | Weaknesses |
|-------|----------|-----------|------------|
| Elastic Agent / Filebeat | Custom (Elastic protocol) | Deep Elastic integration, Fleet-managed, rich module ecosystem | Elastic-ecosystem dependency |
| Fluent Bit | Syslog, HTTP, Kafka, S3 | Extremely lightweight (~1MB), high throughput, plugin ecosystem | Limited parsing capabilities vs. Logstash |
| Vector (Datadog) | Syslog, HTTP, Kafka, S3 | Rust-based (fast, safe), built-in transforms, observability-first | Younger ecosystem, fewer security-specific parsers |
| Cribl Edge | Any (universal receiver) | Routing, filtering, masking, format conversion in-stream | Commercial licensing at scale |
| NXLog | Windows Events, Syslog, files | Native Windows event collection, efficient binary format | Commercial for enterprise features |

**Data loss prevention in the pipeline:** At every stage of the ingestion pipeline, events can be lost: network connectivity interruptions between log sources and collectors, message queue capacity exhaustion, normalization pipeline crashes, and SIEM indexing failures. Comprehensive pipeline monitoring must track: event throughput at each pipeline stage (detecting drops between stages), queue depth and lag (identifying backpressure before it causes data loss), and end-to-end latency (measuring the time from event generation to SIEM indexability).

Pipeline health monitoring — Splunk SPL example:
```spl
| tstats count WHERE index=* by index, _time span=5m
| streamstats window=12 avg(count) as avg_count by index
| eval deviation = abs(count - avg_count) / avg_count * 100
| where deviation > 50
| table _time, index, count, avg_count, deviation
```

Pipeline health monitoring — KQL (Sentinel):
```kql
Usage
| where TimeGenerated > ago(1h)
| summarize IngestionVolume = sum(Quantity) by bin(TimeGenerated, 5m), DataType
| serialize
| extend PrevVolume = prev(IngestionVolume)
| extend DropPercent = iff(PrevVolume > 0, (PrevVolume - IngestionVolume) / PrevVolume * 100, 0)
| where DropPercent > 50
```

Pipeline health dashboards should alert on anomalies in any of these metrics, treating telemetry gaps as security incidents—because an attacker who can suppress logging has achieved a significant tactical advantage.

### 1.2 Normalization and Schema Design

Raw logs from heterogeneous sources use incompatible field names, timestamp formats, and data structures. A Windows Security Event log uses `TargetUserName` and `LogonType`; a Linux PAM log uses `user` and `type`; an AWS CloudTrail event uses `userIdentity.userName` and `eventName`. Detection rules written against raw field names are source-specific and non-portable. Normalization maps source-specific fields to a common schema, enabling detection rules that operate across all log sources.

**Common schemas:**

The Elastic Common Schema (ECS) defines a hierarchical field namespace: `source.ip`, `destination.port`, `user.name`, `process.name`, `file.path`, `event.action`, `event.category`, `event.outcome`. ECS has become a practical industry standard, adopted by Elastic Security and influencing other platforms. Its strength is comprehensive coverage of security-relevant event types with well-defined field semantics.

The Open Cybersecurity Schema Framework (OCSF), developed by a consortium including AWS, Splunk, IBM, and others, defines event classes (Process Activity, Network Activity, Authentication, etc.) with standardized attributes. OCSF represents a vendor-neutral effort to create a universal security telemetry schema. It uses a numbered class system (Class 1001 = File Activity, Class 3002 = DNS Activity, Class 4001 = Security Finding) with mandatory base attributes (time, severity, type_uid) and class-specific attributes.

Splunk's Common Information Model (CIM) defines data models (Authentication, Network Traffic, Endpoint, etc.) with standardized field names. CIM has been Splunk's normalization approach since its early days and is deeply integrated with Splunk's data model acceleration feature.

**Field mapping example — authentication event across sources:**

| Native Field (Windows) | Native Field (Linux PAM) | Native Field (CloudTrail) | ECS Normalized | OCSF Normalized |
|------------------------|-------------------------|--------------------------|-----------------|-----------------|
| `TargetUserName` | `user` | `userIdentity.userName` | `user.name` | `user.name` |
| `LogonType` | `type` | `eventName` | `event.action` | `activity_name` |
| `IpAddress` | `rhost` | `sourceIPAddress` | `source.ip` | `src_endpoint.ip` |
| `WorkstationName` | `hostname` | `userIdentity.arn` | `source.domain` | `src_endpoint.hostname` |
| `Status` / `SubStatus` | `acct` (success/fail) | `errorCode` | `event.outcome` | `status` |

**Schema selection and mapping:** The conglomerate should select a single primary schema and maintain mapping tables from each log source's native field names to the common schema. This mapping is implemented in the normalization pipeline (typically a Logstash filter, Cribl pipeline, or custom stream processor). The mapping process must handle: field name translation, data type coercion (ensuring IP addresses are stored as IP types, not strings), timestamp normalization (converting all timestamps to UTC in ISO 8601 format with nanosecond precision), and enrichment field injection (adding computed fields like `event.risk_score` or `geo.country` based on source data).

Logstash normalization pipeline example:
```ruby
filter {
  if [type] == "wineventlog" and [event_id] == 4624 {
    mutate {
      rename => {
        "TargetUserName" => "[user][name]"
        "IpAddress"      => "[source][ip]"
        "LogonType"      => "[event][code]"
      }
      add_field => {
        "[event][category]" => "authentication"
        "[event][action]"   => "logon"
        "[event][outcome]"  => "success"
      }
    }
    geoip { source => "[source][ip]" target => "[source][geo]" }
  }
}
```

### 1.3 Enrichment Pipeline

Raw normalized events are valuable but insufficient for efficient detection and triage. Enrichment adds contextual data that transforms isolated events into actionable intelligence:

**Asset enrichment:** Map IP addresses, hostnames, and user accounts to asset inventory records. An authentication event from `10.45.2.100` becomes meaningful when enriched with the asset record identifying that IP as "FINSERVER-03, SQL Server, Finance Department, Subsidiary: ACME Corp, Criticality: High." This enrichment enables alert prioritization based on asset criticality and ownership-based routing for triage.

**Threat intelligence enrichment:** Match IOCs (IP addresses, domain names, file hashes, URLs) in events against threat intelligence feeds. This enrichment occurs in the streaming pipeline (not at query time) to enable real-time alerting on known-malicious indicators. The enrichment pipeline maintains a lookup table (typically implemented as a Redis or Elasticsearch index) containing active IOCs, and each event is matched against this table.

Splunk TI enrichment example (lookup-based):
```spl
index=proxy sourcetype=squid
| lookup threat_intel_ip indicator AS dest_ip OUTPUT threat_name, confidence, source_feed
| where isnotnull(threat_name)
| table _time, src_ip, dest_ip, url, threat_name, confidence, source_feed
```

KQL TI enrichment via Sentinel TI connector:
```kql
ThreatIntelligenceIndicator
| where Active == true and ExpirationDateTime > now()
| join kind=inner (
    CommonSecurityLog
    | where TimeGenerated > ago(1h)
    | where isnotempty(DestinationIP)
) on $left.NetworkIP == $right.DestinationIP
| project TimeGenerated, DestinationIP, ThreatType, ConfidenceScore,
    Description, SourceSystem, DeviceAction
```

**Geolocation and ASN enrichment:** Map source and destination IP addresses to geographic coordinates, country codes, and Autonomous System Numbers using MaxMind GeoIP or similar databases. This enables geographic anomaly detection (authentication from a country where the organization has no employees) and network reputation scoring (traffic to ASNs associated with bulletproof hosting).

**User and entity behavior baseline enrichment:** Annotate events with historical behavioral context. An authentication event for a user who has never authenticated from that IP subnet, at that time of day, or to that service is more significant than a routine authentication. This enrichment requires maintaining behavioral baselines (typically in a UEBA system or a separate analytics database) and injecting deviation scores into events at enrichment time.

**Enrichment pipeline architecture:** At conglomerate scale, enrichment must be implemented as a streaming operation (processing events as they flow through the pipeline) rather than a batch operation. Stream processing frameworks (Apache Flink, Kafka Streams, or Cribl Stream) execute enrichment logic against events in transit, adding TI matches, asset context, and geolocation data before the event reaches the SIEM's storage tier. The enrichment pipeline must handle graceful degradation: if the threat intelligence lookup service is temporarily unavailable, events should still flow to the SIEM unenriched rather than being dropped or delayed. A dead-letter queue captures unenriched events for retroactive enrichment when the lookup service recovers.

### 1.4 Storage Architecture: Hot, Warm, and Cold Tiers

Security data has different access patterns over its lifecycle. Recent data (last 24–72 hours) requires sub-second query latency for active incident response. Data from the past 30–90 days supports threat hunting and investigation workflows that tolerate multi-second query times. Data beyond 90 days is retained for compliance and forensic purposes and can tolerate query times measured in minutes.

**Hot tier:** High-performance storage (SSDs, NVMe) holding the most recent data (1–7 days). Optimized for high-frequency, low-latency queries generated by real-time detection rules.

**Warm tier:** Cost-optimized storage (HDDs, object storage with caching) holding 30–90 days of data. Query latency is higher (seconds to tens of seconds) but acceptable for interactive analysis.

**Cold tier:** Archive storage (S3, Azure Blob, GCS) holding data for the compliance retention period (typically 1–7 years). Formats optimized for storage efficiency (Parquet, ORC) are preferred over query-optimized formats.

Elasticsearch ILM policy example:
```json
{
  "policy": {
    "phases": {
      "hot":  { "min_age": "0ms",  "actions": { "rollover": { "max_size": "50gb", "max_age": "1d" }}},
      "warm": { "min_age": "3d",   "actions": { "shrink": { "number_of_shards": 1 }, "forcemerge": { "max_num_segments": 1 }}},
      "cold": { "min_age": "30d",  "actions": { "searchable_snapshot": { "snapshot_repository": "s3_repo" }}},
      "delete":{ "min_age": "365d","actions": { "delete": {} }}
    }
  }
}
```

**Cost optimization at conglomerate scale:** At petabyte scale, storage cost dominates the SIEM budget. Strategies include: selective ingestion (not all log sources need full-fidelity ingestion; verbose debug logs can be sampled or filtered), field reduction (stripping non-security-relevant fields during normalization), compression (columnar formats like Parquet achieve 10–20x compression for structured log data), and tiered retention.

### 1.5 SIEM Platform Architecture Comparison

| Platform | Query Language | Licensing Model | Strengths | Limitations |
|----------|---------------|-----------------|-----------|-------------|
| **Splunk Enterprise Security** | SPL | Daily ingestion volume (GB/day) | Mature content ecosystem (ESCU), extensive app marketplace, mature SOAR (Splunk SOAR) | Cost at petabyte scale, vendor lock-in |
| **Elastic Security** | KQL, EQL, ES\|QL | Compute resources (nodes/RAM) | Cost-effective at high volume, ECS schema, sequence detection via EQL | Operational complexity, cluster management |
| **Google SecOps (Chronicle)** | YARA-L 2.0 | Fixed-rate (not volume-based) | Unlimited storage, VirusTotal/Mandiant integration, UDM schema | Google ecosystem lock-in |
| **Microsoft Sentinel** | KQL (Kusto) | Data ingestion to Log Analytics | Deep Microsoft ecosystem integration, entity mapping, Fusion ML | Performance on complex cross-workspace queries |
| **Security Data Lake** (Snowflake/Databricks/Amazon Security Lake) | SQL / Spark | Storage + compute | Maximum flexibility, Parquet/OCSF, any-tool analysis | Requires building detection/alerting/case management |

---

## 2. Detection-as-Code

Detection-as-Code (DaC) applies software engineering practices—version control, code review, automated testing, CI/CD pipelines—to detection rule management. This approach is essential at conglomerate scale, where detection libraries contain thousands of rules that must be maintained, tuned, tested, and deployed across multiple SIEM platforms.

### 2.1 Sigma: The Universal Detection Language — Deep Dive

Sigma is an open-source, vendor-neutral detection rule format that describes detection logic in YAML. Sigma rules are compiled (transpiled) to platform-specific query languages using the `pySigma` library and platform-specific backends.

**Sigma rule anatomy — complete reference:**

```yaml
title: Suspicious LSASS Access via comsvcs.dll MiniDump     # Required. Short.
id: a642964e-bead-4bed-8910-1bb4d63e3b4d                    # Required. UUIDv4.
related:                                                     # Optional. Links.
    - id: <other-rule-uuid>
      type: derived | obsoletes | merged | renamed | similar
status: stable                         # experimental → test → stable
description: |                          # Multi-line description
    Detects use of comsvcs.dll MiniDump export to dump LSASS memory.
    This is a LOLBin technique requiring no external tools.
references:
    - https://attack.mitre.org/techniques/T1003/001/
    - https://lolbas-project.github.io/#/LOLBins/Comsvcs
author: Detection Engineering Team
date: 2024/01/15
modified: 2024/06/01
tags:
    - attack.credential_access
    - attack.t1003.001                  # MITRE ATT&CK sub-technique
    - cve.2024.0001                     # CVE tag if applicable
logsource:
    category: process_creation          # Abstract category
    product: windows                    # Product filter
    # service: sysmon                   # Optional: specific service
detection:
    selection_cmdline:
        CommandLine|contains|all:       # AND — all must match
            - 'comsvcs'
            - 'MiniDump'
        CommandLine|contains:           # OR — any can match
            - 'full'
            - '#24'
    selection_image:
        Image|endswith: '\rundll32.exe'
    filter_legitimate:
        ParentImage|endswith:
            - '\svchost.exe'
            - '\services.exe'
    condition: (selection_cmdline and selection_image) and not filter_legitimate
fields:                                 # Fields to include in output
    - CommandLine
    - ParentImage
    - User
    - Computer
falsepositives:
    - Legitimate memory dump for debugging by system administrators
level: critical                         # informational | low | medium | high | critical
```

**Sigma modifiers — complete reference:**

| Modifier | Behavior | Example |
|----------|----------|---------|
| `contains` | Substring match | `CommandLine\|contains: 'mimikatz'` |
| `startswith` | Prefix match | `Image\|startswith: 'C:\Temp\'` |
| `endswith` | Suffix match | `Image\|endswith: '\cmd.exe'` |
| `all` | All values must match (AND) | `CommandLine\|contains\|all: ['sekurlsa', 'logonpasswords']` |
| `re` | Regular expression | `CommandLine\|re: '(?i)invoke-mimikatz'` |
| `base64` | Match base64-encoded value | `CommandLine\|base64: 'IEX'` — matches `SUVY` |
| `base64offset` | Match base64 at any offset (0,1,2) | `CommandLine\|base64offset: 'IEX'` — matches `SUVY`, `lFW`, `JRV` |
| `utf16le` | Match UTF-16LE encoded | Combined with base64 for PowerShell encoded commands |
| `utf16` | Alias for utf16le | |
| `wide` | Alias for utf16le | |
| `cidr` | CIDR range match | `DestinationIp\|cidr: '10.0.0.0/8'` |
| `gt`, `gte`, `lt`, `lte` | Numeric comparison | `EventID\|gte: 4600` |
| `windash` | Match both `-` and `/` prefixes | `CommandLine\|windash\|contains: '-enc'` matches `-enc` and `/enc` |
| `expand` | Expand environment variables | `TargetFilename\|expand: '%APPDATA%\*.exe'` |
| `fieldref` | Compare field to another field | `TargetUserName\|fieldref: SubjectUserName` |

**Sigma correlation rules (multi-event detections):**

Sigma specification supports correlation rules for detecting patterns across multiple events. These are defined with `type: correlation`:

```yaml
title: Brute Force Followed by Successful Logon
id: bf-then-success-001
type: event_count
rules:
    failed_logon:
        title: Failed Logon Attempt
        logsource:
            product: windows
            service: security
        detection:
            selection:
                EventID: 4625
            condition: selection
group-by:
    - TargetUserName
    - IpAddress
timespan: 5m
condition:
    gte: 10              # 10+ failed logons in 5 minutes
---
title: Brute Force Success Correlation
type: temporal
rules:
    - bf-then-success-001            # Reference the event_count rule above
    - successful_logon:
        logsource:
            product: windows
            service: security
        detection:
            selection:
                EventID: 4624
                LogonType: 10        # RDP
            condition: selection
group-by:
    - TargetUserName
timespan: 15m
ordered: true
```

**sigma-cli conversion examples:**

```bash
# Install sigma-cli with backends
pip install sigma-cli pySigma-backend-splunk pySigma-backend-elasticsearch \
    pySigma-backend-microsoft365defender pySigma-pipeline-sysmon \
    pySigma-pipeline-windows

# Convert single rule to Splunk SPL
sigma convert -t splunk -p sysmon rules/credential_access/lsass_dump.yml

# Convert to Elastic EQL
sigma convert -t elasticsearch -f eql -p ecs_windows rules/credential_access/lsass_dump.yml

# Convert to Microsoft Sentinel KQL
sigma convert -t microsoft365defender rules/credential_access/lsass_dump.yml

# Batch convert all rules to all backends
sigma convert -t splunk -p sysmon -r rules/ -o splunk_rules/

# Validate rules
sigma check rules/
```

**Conversion output comparison for LSASS comsvcs dump rule:**

Splunk SPL:
```spl
index=sysmon EventCode=1 Image="*\\rundll32.exe"
    (CommandLine="*comsvcs*" AND CommandLine="*MiniDump*")
    AND (CommandLine="*full*" OR CommandLine="*#24*")
    NOT (ParentImage="*\\svchost.exe" OR ParentImage="*\\services.exe")
| table _time, Computer, User, CommandLine, ParentImage
```

Elastic KQL:
```
process.executable:*\\rundll32.exe AND process.command_line:(*comsvcs* AND *MiniDump*)
    AND process.command_line:(*full* OR *#24*)
    AND NOT process.parent.executable:(*\\svchost.exe OR *\\services.exe)
```

Microsoft Sentinel KQL:
```kql
DeviceProcessEvents
| where FileName =~ "rundll32.exe"
| where ProcessCommandLine has_all ("comsvcs", "MiniDump")
| where ProcessCommandLine has_any ("full", "#24")
| where InitiatingProcessFileName !in~ ("svchost.exe", "services.exe")
| project Timestamp, DeviceName, AccountName, ProcessCommandLine,
    InitiatingProcessFileName
```

### 2.2 Detection Language Comparison: SPL, KQL, EQL, and YARA-L

Beyond Sigma, detection engineers must understand the native query languages of their SIEM platforms, because complex detections often require platform-specific capabilities that Sigma's abstraction layer cannot fully represent.

**Splunk SPL — advanced detection patterns:**

Threshold-based detection (brute force):
```spl
index=wineventlog EventCode=4625
| stats count as failed_attempts, values(TargetUserName) as users,
    dc(TargetUserName) as unique_users by src_ip
| where failed_attempts > 20 AND unique_users > 5
| lookup geo_ip ip AS src_ip OUTPUT country, city
| table src_ip, failed_attempts, unique_users, users, country, city
```

Statistical baseline anomaly (unusual process execution):
```spl
index=sysmon EventCode=1
| stats count by Computer, Image
| eventstats avg(count) as avg_count, stdev(count) as stdev_count by Image
| eval zscore = (count - avg_count) / stdev_count
| where zscore > 3
| sort -zscore
```

SPL subsearch for multi-stage correlation:
```spl
index=sysmon EventCode=1 Image="*\\mimikatz.exe" OR CommandLine="*sekurlsa*"
| rename Computer as compromised_host
| join compromised_host type=inner
    [search index=wineventlog EventCode=4624 LogonType=3
     | rename TargetUserName as lateral_user, Computer as compromised_host
     | where _time > relative_time(now(), "-1h")]
| table _time, compromised_host, lateral_user, Image, CommandLine
```

**KQL — advanced detection patterns:**

Multi-table join for process-network correlation:
```kql
let SuspiciousProcesses = DeviceProcessEvents
    | where Timestamp > ago(1h)
    | where FileName in~ ("powershell.exe", "cmd.exe", "wscript.exe")
    | where ProcessCommandLine has_any ("downloadstring", "invoke-webrequest",
        "certutil", "bitsadmin")
    | project DeviceId, ProcessId = ProcessId, Timestamp, ProcessCommandLine;
SuspiciousProcesses
| join kind=inner (
    DeviceNetworkEvents
    | where Timestamp > ago(1h)
    | where RemotePort in (80, 443, 8080, 8443)
    | where RemoteIPType == "Public"
) on DeviceId, $left.ProcessId == $right.InitiatingProcessId
| project Timestamp, DeviceName, ProcessCommandLine, RemoteIP, RemotePort, RemoteUrl
```

Time-series anomaly detection:
```kql
SecurityEvent
| where EventID == 4624 and LogonType == 10
| summarize LoginCount = count() by TargetUserName, bin(TimeGenerated, 1h)
| make-series LoginSeries = sum(LoginCount) on TimeGenerated step 1h by TargetUserName
| extend (anomalies, score, baseline) = series_decompose_anomalies(LoginSeries, 2.5)
| mv-expand TimeGenerated to typeof(datetime), LoginSeries to typeof(long),
    anomalies to typeof(int), score to typeof(double)
| where anomalies == 1
```

**EQL — sequence detection (Elastic):**

Multi-step attack detection (credential dump → lateral movement):
```
sequence by host.name with maxspan=30m
  [process where event.type == "start" and
    (process.name == "mimikatz.exe" or
     process.command_line like~ "*sekurlsa*" or
     (process.name == "rundll32.exe" and process.command_line like~ "*comsvcs*MiniDump*"))]
  [authentication where event.outcome == "success" and
    source.ip != "127.0.0.1" and
    winlog.logon.type == "Network"]
  [process where event.type == "start" and
    process.name in ("psexec.exe", "wmic.exe", "schtasks.exe")]
```

Parent-child process anomaly:
```
sequence by process.entity_id
  [process where event.type == "start" and process.name == "winword.exe"]
  [process where event.type == "start" and
    process.parent.name == "winword.exe" and
    process.name in ("cmd.exe", "powershell.exe", "wscript.exe", "mshta.exe")]
```

**YARA-L 2.0 — Chronicle multi-event correlation:**

```
rule credential_dump_lateral_movement {
  meta:
    author = "Detection Engineering"
    description = "Credential dump tool followed by lateral movement"
    severity = "CRITICAL"
    mitre_attack = "T1003, T1021"

  events:
    // Event 1: Credential dumping tool execution
    $cred_dump.metadata.event_type = "PROCESS_LAUNCH"
    (
      $cred_dump.target.process.file.full_path = /mimikatz/ nocase or
      $cred_dump.target.process.command_line = /sekurlsa/ nocase or
      ($cred_dump.target.process.file.full_path = /rundll32/ nocase and
       $cred_dump.target.process.command_line = /comsvcs.*MiniDump/ nocase)
    )
    $cred_dump.principal.hostname = $hostname

    // Event 2: Network logon from same host within 30 minutes
    $lateral.metadata.event_type = "USER_LOGIN"
    $lateral.extensions.auth.type = "NETWORK"
    $lateral.principal.ip = $src_ip
    $lateral.target.hostname != $hostname

  match:
    $hostname over 30m

  condition:
    $cred_dump and $lateral
}
```

### 2.3 Detection CI/CD Pipeline

A mature Detection-as-Code pipeline implements the following workflow:

**Repository structure:**
```
detection-rules/
├── rules/
│   ├── credential_access/
│   │   ├── lsass_dump_comsvcs.yml
│   │   ├── kerberoasting.yml
│   │   └── dcsync.yml
│   ├── lateral_movement/
│   ├── persistence/
│   ├── exfiltration/
│   └── ...
├── tests/
│   ├── credential_access/
│   │   ├── lsass_dump_comsvcs_positive.json   # Events that should trigger
│   │   └── lsass_dump_comsvcs_negative.json   # Events that should NOT trigger
│   └── ...
├── pipelines/
│   ├── splunk_pipeline.yml
│   ├── elastic_pipeline.yml
│   └── sentinel_pipeline.yml
├── .github/
│   └── workflows/
│       └── detection-ci.yml
└── TUNING.md
```

**GitHub Actions CI/CD pipeline:**
```yaml
name: Detection Rule CI/CD
on:
  pull_request:
    paths: ['rules/**']
  push:
    branches: [main]
    paths: ['rules/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install sigma-cli pySigma-backend-splunk pySigma-backend-elasticsearch
      - name: Sigma syntax validation
        run: sigma check rules/
      - name: Compile to all backends
        run: |
          sigma convert -t splunk -p sysmon -r rules/ -o /tmp/splunk/ 2>&1 | tee compile.log
          sigma convert -t elasticsearch -p ecs_windows -r rules/ -o /tmp/elastic/ 2>&1 | tee -a compile.log
          if grep -q "ERROR" compile.log; then exit 1; fi

  test:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Unit test rules against Mordor/EVTX datasets
        run: |
          # Run compiled rules against positive test events
          python scripts/test_detections.py --rules rules/ --tests tests/ --report report.json
      - name: Upload test report
        uses: actions/upload-artifact@v4
        with: { name: test-report, path: report.json }

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Splunk
        run: python scripts/deploy_splunk.py --rules /tmp/splunk/ --target $SPLUNK_URL
      - name: Deploy to Elastic
        run: python scripts/deploy_elastic.py --rules /tmp/elastic/ --target $ELASTIC_URL
```

**Unit testing for detections:** Each detection rule should include test cases: positive tests (synthetic log events that should trigger the rule) and negative tests (benign events that should not trigger). Frameworks like `sigma-test` and custom harnesses that replay events through a test SIEM instance enable this automation. The Mordor project (now known as Security Datasets) and EVTX-ATTACK-SAMPLES provide real attack telemetry datasets that can serve as positive test data.

**Alert tuning as a continuous process:** Tuning is not a one-time activity—it is a continuous feedback loop. Each false positive reported by a SOC analyst should be tracked as a tuning ticket. Each exclusion added to a rule narrows its detection scope, potentially creating a blind spot. Periodically reviewing exclusions against the current threat landscape ensures that exclusions added for benign software that has since been replaced or updated are removed, restoring the rule's original detection scope.

---

## 3. SOAR Architecture and Playbook Design

Security Orchestration, Automation, and Response (SOAR) platforms automate repetitive SOC workflows, reducing analyst workload and improving response consistency. At conglomerate scale, SOAR is essential because manual triage of hundreds of thousands of daily alerts is physically impossible.

### 3.1 SOAR Integration Architecture

The SOAR platform sits between the SIEM (which generates alerts) and the response ecosystem (ticketing systems, identity providers, endpoint management platforms, firewalls, email gateways). Key integrations:

| Integration Target | Query Actions | Response Actions | Safeguards |
|-------------------|---------------|------------------|------------|
| **Active Directory / Entra ID** | User attributes, group memberships, recent logon activity | Disable account, force password reset, revoke sessions, remove from groups | Never auto-disable executive accounts; require dual-approval for privileged accounts |
| **EDR** (CrowdStrike, Defender, SentinelOne) | Process tree, file hashes, network connections, host timeline | Isolate host, kill process, collect forensic package, push IOC blocklist | Rate-limit isolations; auto-undo if not confirmed within SLA |
| **Firewall / Proxy** | Current block/allow lists | Block IP/domain, add to sinkhole | Verify target is not CDN/cloud-provider shared IP; require TI corroboration |
| **Email Gateway** | Search for message by IOC | Quarantine message, purge from all inboxes | Log all purge actions; never auto-purge without at least 2 IOC matches |
| **TI Platforms** (MISP, VirusTotal, Shodan, GreyNoise, AbuseIPDB) | Reputation lookup, indicator enrichment | Push new IOCs to feeds | N/A (read-only enrichment) |
| **Ticketing** (ServiceNow, Jira) | Query existing tickets | Create incident ticket, update status, assign owner | Auto-create only for confirmed alerts; suppress duplicate ticket creation |

### 3.2 Playbook Design Patterns

**Enrichment-first playbook — phishing triage (detailed):**

```
TRIGGER: Alert from email gateway — suspected phishing

STEP 1: Extract IOCs
  → Parse sender address, sender domain, reply-to, subject, URLs, attachments
  → Hash attachments (SHA256)

STEP 2: Enrich IOCs (parallel)
  → VirusTotal: check URL reputation, file hash reputation
  → AbuseIPDB: check sender IP reputation
  → GreyNoise: check if sender IP is known scanner/benign
  → Shodan: check sender IP for open services/hosting indicators
  → Internal TI: check against internal IOC database
  → WHOIS: check sender domain registration age (< 30 days = suspicious)

STEP 3: Compute risk score
  → Score = Σ(indicator_scores) × sender_domain_age_factor × recipient_criticality
  → If score > HIGH_THRESHOLD → auto-quarantine, escalate to Tier 2
  → If MEDIUM < score < HIGH → present to Tier 1 with enrichment
  → If score < MEDIUM → auto-close with documentation

STEP 4: Containment (if score > HIGH)
  → Quarantine email across all recipient inboxes (Exchange/M365 API)
  → Block sender domain at email gateway
  → Block extracted URLs at web proxy
  → Search SIEM for other recipients who clicked URLs
  → If attachment was opened → isolate host via EDR

STEP 5: Documentation
  → Create ticket with full enrichment, timeline, and actions taken
  → Notify affected users with tailored phishing awareness message
```

**Auto-remediation playbooks:** For high-confidence, low-risk response actions, playbooks execute remediation automatically without human approval. Examples: blocking a known-malicious hash across all endpoints, quarantining a phishing email across all inboxes, disabling an account that triggered an impossible-travel alert with high-confidence TI enrichment. Auto-remediation requires strict guardrails: whitelisting exceptions (never auto-block executive accounts), rate limiting (never auto-remediate more than N incidents per hour without human approval), and audit logging (every automated action is logged and reviewable).

**Human-in-the-loop playbooks:** For ambiguous or high-impact actions, playbooks present enriched context to an analyst and request a decision. The playbook automates the enrichment and presents options (escalate, remediate, close as false positive) through the SOAR's case management interface or via Slack/Teams integration.

**Escalation playbooks:** When automated triage determines that an alert exceeds the SOC's authority or capability (e.g., confirmed compromise of a critical production system, or an alert matching a nation-state TTP pattern), the playbook escalates to an incident response team with a pre-formatted briefing package.

### 3.3 Multi-Subsidiary SOAR Challenges

In a conglomerate model, SOAR automation must navigate organizational boundaries. Automated containment actions in Subsidiary A's environment require authorization from Subsidiary A's security team, not just the central SOC. Multi-tenancy in the SOAR platform ensures that analysts from one subsidiary cannot view or act on another subsidiary's alerts unless cross-subsidiary permission is explicitly granted.

Playbook libraries should be structured in layers: a core library of universal playbooks (applicable to all subsidiaries), a sector-specific layer (financial sector regulatory requirements, healthcare HIPAA incident handling), and a subsidiary-specific layer (custom integrations, unique business processes, specific escalation contacts).

---

## 4. Threat Intelligence Operationalization

Threat intelligence is only valuable if it influences detection, response, and architectural decisions.

### 4.1 Intelligence Lifecycle

Direction (what questions does the security team need answered?) → Collection (gathering raw data from feeds, reports, incident findings, OSINT) → Processing (normalizing, deduplicating, and validating collected data) → Analysis (synthesizing processed data into assessments and judgments) → Dissemination (delivering finished intelligence to consumers in actionable formats) → Feedback (consumers report whether intelligence was useful, closing the loop).

The TI team maintains a Priority Intelligence Requirements (PIR) document for each subsidiary (or subsidiary cluster) that guides collection and analysis priorities.

### 4.2 STIX and TAXII

**STIX 2.1** defines object types: Threat Actor, Intrusion Set, Campaign, Attack Pattern, Malware, Tool, Indicator, Vulnerability, Observed Data. Each object has defined properties and relationships. STIX Patterning Language examples:

```
# File hash indicator
[file:hashes.'SHA-256' = 'abc123...def456']

# Network indicator — IP + port
[network-traffic:dst_ref.type = 'ipv4-addr' AND
 network-traffic:dst_ref.value = '203.0.113.42' AND
 network-traffic:dst_port = 443]

# Process indicator — command line pattern
[process:command_line MATCHES '^.*sekurlsa::logonpasswords.*$']

# Compound indicator — file dropped then network connection
([file:name = 'payload.dll'] AND [network-traffic:dst_ref.value = '198.51.100.1'])
```

**TAXII 2.1** provides transport mechanisms. Most TI platforms (MISP, OpenCTI, ThreatConnect, Anomali) support STIX/TAXII for both feed consumption and intelligence sharing.

TAXII API interaction:
```bash
# Discover TAXII server
curl -H "Accept: application/taxii+json;version=2.1" \
  https://taxii.example.com/taxii2/

# List collections
curl -H "Accept: application/taxii+json;version=2.1" \
  https://taxii.example.com/taxii2/collections/

# Get STIX objects from a collection (with time filter)
curl -H "Accept: application/stix+json;version=2.1" \
  "https://taxii.example.com/taxii2/collections/{id}/objects/?added_after=2024-01-01T00:00:00Z"
```

### 4.3 Indicator Lifecycle Management

IOCs have a limited useful lifetime. An IP address used for C2 today may be reassigned to a legitimate user tomorrow.

| Indicator Type | Active Lifetime | Expiration Rationale |
|---------------|-----------------|---------------------|
| IP address | 30–90 days | IP reassignment risk; dynamic infrastructure |
| Domain name | 6–12 months | Domain ownership more stable; attacker re-registration |
| File hash (SHA-256) | Indefinite | Permanent identifier of specific sample |
| URL path | 30–90 days | Infrastructure rotation; path changes |
| Certificate fingerprint | Until expiry + 30d | Certificate revocation/renewal |
| JA3/JA3S hash | 6–12 months | TLS library updates change fingerprints |

**Enrichment sources per indicator type:**

| Source | IP | Domain | Hash | URL |
|--------|-----|--------|------|-----|
| VirusTotal | ✓ | ✓ | ✓ | ✓ |
| AbuseIPDB | ✓ | | | |
| GreyNoise | ✓ | | | |
| Shodan | ✓ | | | |
| PassiveTotal / RiskIQ | ✓ | ✓ | | |
| URLhaus | | | | ✓ |
| MalwareBazaar | | | ✓ | |
| Censys | ✓ | ✓ | | |

### 4.4 Intelligence-Driven Detection

The most valuable intelligence application is driving detection development. A direct pipeline from intelligence production to detection deployment:

TI report → Extraction of TTPs and IOCs → Mapping to MITRE ATT&CK techniques → Detection rule development targeting the specific technique implementation → Sigma rule creation → CI/CD deployment → Production detection.

The key distinction is between IOC-based detection (matching specific indicators, which has limited shelf life) and TTP-based detection (matching behavioral patterns, which persists across campaigns). A mature TI-to-detection pipeline prioritizes TTP-based detection while maintaining IOC feeds as a supplementary layer.

### 4.5 Diamond Model Application

The Diamond Model of Intrusion Analysis provides a structured framework for analyzing and correlating threat intelligence across four vertices: **Adversary** (who), **Infrastructure** (where/how they operate), **Capability** (what tools they use), and **Victim** (who they target). Each intrusion event is modeled as a diamond connecting these four vertices.

Pivot-based threat hunting starting from a single C2 IP:

```
C2 IP (Infrastructure)
  ├── Passive DNS → other domains resolving to this IP
  ├── Certificate Transparency → certificates associated with this IP
  ├── GreyNoise/Shodan → open ports, services, hosting provider
  │
  ├─→ Capability → malware families communicating with this infrastructure
  │     ├── Sandbox reports (Any.Run, Joe Sandbox, Hybrid Analysis)
  │     ├── MalwareBazaar → related samples
  │     └── MITRE ATT&CK mapping → TTPs
  │
  ├─→ Adversary → threat actor attribution
  │     ├── TI platform enrichment
  │     ├── Reporting correlation
  │     └── ISAC sharing
  │
  └─→ Victim → other targeted organizations
        ├── ISAC sharing
        └── TI feed correlation
```

### 4.6 Attribution Confidence Calibration

Attribution—identifying which threat actor or group is responsible for observed activity—requires careful confidence calibration using standardized intelligence language:

| Confidence Level | Evidence Required | Operational Response |
|-----------------|-------------------|---------------------|
| **Low** | Single IOC overlap with known actor infrastructure; circumstantial TTP similarity | Enhanced monitoring on related indicators |
| **Moderate** | TTP overlap + infrastructure overlap; plausible but with alternative explanations | Proactive threat hunting for related TTPs across environment |
| **High** | TTP + infrastructure + capability overlap; corroborated by external intelligence sources | Executive notification; potential law enforcement engagement |

Overconfident attribution is dangerous because it can drive inappropriate response. Underconfident attribution may result in treating sophisticated threats as routine incidents.

---

## 5. Detection Coverage Mapping and Gap Analysis

### 5.1 MITRE ATT&CK Coverage Mapping

Detection coverage mapping involves tagging each detection rule with the ATT&CK techniques it addresses (using the Sigma `tags` field), then visualizing coverage as a heat map across the ATT&CK matrix. Gaps represent blind spots where an adversary using those techniques would operate undetected.

**Coverage scoring per technique:**

| Factor | Weight | Scoring |
|--------|--------|---------|
| Number of detection rules | 20% | 0 rules = 0, 1 rule = 0.5, 2+ rules = 1.0 |
| Detection fidelity | 30% | High precision/low FP = 1.0, medium = 0.5, noisy = 0.2 |
| Telemetry availability | 30% | Required logs collected from 100% hosts = 1.0, partial = proportional |
| Validation status | 20% | Purple-team validated = 1.0, untested = 0.3 |

**Critical log source → ATT&CK technique coverage matrix:**

| Log Source | Techniques Enabled | Coverage If Missing |
|------------|-------------------|---------------------|
| Sysmon Event ID 1 (Process Create) | T1059 (Scripting), T1218 (Signed Binary Proxy), T1036 (Masquerading), T1053 (Scheduled Task), T1569 (System Services) | Lose ~40% of execution/persistence detection |
| Sysmon Event ID 10 (Process Access) | T1003 (Credential Dumping), T1055 (Process Injection) | Lose LSASS access detection, injection detection |
| Sysmon Event ID 3 (Network Connection) | T1071 (Application Layer Protocol), T1571 (Non-Standard Port) | Lose process→network correlation |
| PowerShell 4104 (Script Block) | T1059.001 (PowerShell), T1027 (Obfuscated Files) | Lose PowerShell attack visibility |
| Security 4624/4625 (Logon) | T1078 (Valid Accounts), T1110 (Brute Force), T1021 (Remote Services) | Lose authentication-based detection |
| Security 4662 (Directory Access) | T1003.006 (DCSync), Chapter 14A attacks | Lose AD-specific attack detection |
| DNS query logs | T1071.004 (DNS C2), T1568 (Dynamic Resolution), T1483 (DGA) | Lose DNS-based C2 detection |
| Network flow / firewall logs | T1048 (Exfiltration), T1572 (Protocol Tunneling) | Lose network anomaly detection |

**ATT&CK Navigator automation:** The Navigator accepts JSON layer files that can be generated programmatically from the detection rule repository's ATT&CK tags:

```python
import json
from collections import defaultdict

def generate_navigator_layer(rules_dir):
    technique_scores = defaultdict(float)
    for rule in load_sigma_rules(rules_dir):
        for tag in rule.get('tags', []):
            if tag.startswith('attack.t'):
                technique_id = tag.replace('attack.', '').upper()
                technique_scores[technique_id] += 1.0

    techniques = [
        {"techniqueID": tid, "score": min(score, 4), "color": score_to_color(score)}
        for tid, score in technique_scores.items()
    ]
    return {
        "name": "Detection Coverage",
        "versions": {"attack": "14", "navigator": "4.9", "layer": "4.5"},
        "domain": "enterprise-attack",
        "techniques": techniques
    }
```

### 5.2 Purple Team Validation

Detection rules must be validated against realistic adversary simulations.

**Atomic Red Team integration:**
```powershell
# Install
Install-Module -Name invoke-atomicredteam -Scope CurrentUser
Install-AtomicRedTeam -getAtomics

# Execute specific technique test
Invoke-AtomicTest T1003.001 -TestNumbers 1  # LSASS dump via comsvcs.dll

# Execute and validate detection fired
Invoke-AtomicTest T1003.001 -TestNumbers 1 -CheckPrereqs
# → Analyst verifies Sigma rule "lsass_dump_comsvcs" triggered in SIEM

# Cleanup
Invoke-AtomicTest T1003.001 -TestNumbers 1 -Cleanup
```

**Breach and Attack Simulation (BAS)** platforms (AttackIQ, SafeBreach, Picus Security) automate adversary emulation across the environment by deploying lightweight agents that continuously execute attack simulations against production systems. BAS platforms run simulations at scheduled intervals, automatically validate that detection rules trigger, and produce coverage reports that track detection effectiveness over time. This continuous validation catches detection regressions before an actual attacker exploits the blind spot.

---

## 6. Log Source Prioritization and Data Engineering

### 6.1 Critical Log Sources by Detection Category

**Tier 1 — Must-have telemetry (critical for basic detection):**

| Source | Event IDs / Types | Detection Value | Ingestion Cost |
|--------|------------------|-----------------|----------------|
| Endpoint process creation | Sysmon 1, Win Security 4688, EDR process events | Enables ~40% of post-compromise detection | Medium (high volume but structured) |
| Authentication events | Win 4624/4625/4634/4648, Linux PAM, cloud sign-in | Credential abuse, lateral movement, impossible travel | Medium |
| DNS query logs | DNS server query log, Sysmon 22, EDR DNS | DNS C2, DGA detection, IOC matching | High (very high volume) |
| Network flow | NetFlow/IPFIX, firewall connection logs | Lateral movement, exfiltration, network anomaly | High |

**Tier 2 — High-value telemetry (required for advanced detection):**

Sysmon Events 3 (network connections by process), 7 (DLL load), 8 (CreateRemoteThread), 10 (ProcessAccess), 11 (FileCreate), 12/13/14 (Registry), 17/18 (Named Pipe), 22 (DNS Query). PowerShell Script Block Logging (Event ID 4104). Cloud audit logs (CloudTrail, Azure Activity Log, GCP Audit Log). Email gateway logs.

**Tier 3 — Supplementary telemetry:** Full packet capture or rich network metadata (Zeek/Bro logs). Application-specific logs. File integrity monitoring (FIM) logs.

**Recommended Sysmon configuration** (balancing coverage and volume):
```xml
<Sysmon schemaversion="4.90">
  <EventFiltering>
    <ProcessCreate onmatch="exclude">
      <Image condition="is">C:\Windows\System32\svchost.exe</Image>
      <!-- Exclude high-volume benign processes — add selectively -->
    </ProcessCreate>
    <NetworkConnect onmatch="include">
      <DestinationPort condition="is">445</DestinationPort>
      <DestinationPort condition="is">135</DestinationPort>
      <DestinationPort condition="is">3389</DestinationPort>
      <Initiated condition="is">true</Initiated>
    </NetworkConnect>
    <ProcessAccess onmatch="include">
      <TargetImage condition="is">C:\Windows\System32\lsass.exe</TargetImage>
    </ProcessAccess>
    <CreateRemoteThread onmatch="include" />
    <FileCreate onmatch="include">
      <TargetFilename condition="contains">\Startup\</TargetFilename>
      <TargetFilename condition="contains">\Tasks\</TargetFilename>
    </FileCreate>
    <RegistryEvent onmatch="include">
      <TargetObject condition="contains">CurrentVersion\Run</TargetObject>
      <TargetObject condition="contains">CurrentVersion\Services</TargetObject>
    </RegistryEvent>
    <PipeEvent onmatch="include" />
    <DnsQuery onmatch="include" />
  </EventFiltering>
</Sysmon>
```

### 6.2 Data Quality Assurance

Detection effectiveness depends on data quality. Data quality monitoring should include:

```spl
# Splunk — detect field population anomalies
index=sysmon EventCode=1
| stats count, count(eval(isnotnull(CommandLine))) as has_cmdline,
    count(eval(isnotnull(ParentImage))) as has_parent by sourcetype
| eval cmdline_pct = round(has_cmdline/count*100, 2)
| eval parent_pct = round(has_parent/count*100, 2)
| where cmdline_pct < 95 OR parent_pct < 95
```

```kql
// Sentinel — detect ingestion latency
SecurityEvent
| where TimeGenerated > ago(1h)
| extend IngestionDelay = datetime_diff('second', ingestion_time(), TimeGenerated)
| summarize AvgDelay = avg(IngestionDelay), P95Delay = percentile(IngestionDelay, 95),
    MaxDelay = max(IngestionDelay) by Computer, bin(TimeGenerated, 5m)
| where P95Delay > 300
```

---

## 7. Alert Triage Optimization and SOC Metrics

### 7.1 Alert Fatigue Quantification

Alert fatigue—the degradation of analyst attention and response quality due to excessive alert volume—is the most significant operational risk facing security operations teams.

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Alerts per analyst per 8h shift | 20–30 meaningful alerts | > 50 = degraded triage quality |
| False positive rate per rule | < 50% | > 90% = tune or disable |
| Mean time to triage (MTTT) | < 15 min (high sev), < 60 min (medium) | > 2x target = capacity issue |
| Alert close rate without action | < 30% | > 60% = noisy rules or miscalibrated severity |
| Alert-to-incident ratio | 1:20 to 1:50 | > 1:100 = predominantly noise |

### 7.2 Precision-Recall Tradeoffs

| Rule Type | Precision | Recall | Use Case |
|-----------|-----------|--------|----------|
| High-precision, low-recall | High (>90%) | Low | Auto-remediation playbooks — low false activation risk |
| Balanced | Medium (50-90%) | Medium | Enrichment-first playbooks — analyst triage with context |
| Low-precision, high-recall | Low (<50%) | High | Threat hunting feeds — catch-all for investigation |

Alert prioritization composite score:
```
Priority = RuleConfidence × AssetCriticality × TIEnrichmentScore × TemporalNovelty

Where:
  RuleConfidence ∈ [0.0, 1.0] — based on rule's historical TP rate
  AssetCriticality ∈ [0.5, 2.0] — from asset inventory (test=0.5, prod DB=2.0)
  TIEnrichmentScore ∈ [1.0, 3.0] — 1.0=no TI match, 3.0=high-confidence APT IOC
  TemporalNovelty ∈ [0.3, 1.0] — 1.0=first occurrence, 0.3=100th occurrence this week
```

### 7.3 SOC Analyst Workflow Design

Each alert presentation should follow a consistent structure:
1. **What** — detection rule name, severity, ATT&CK technique
2. **Where** — affected host, user, subsidiary, asset criticality
3. **When** — timeline of matched events
4. **Why** — TI enrichment results, historical context, risk score
5. **Next** — playbook-recommended investigation steps and response options

Analyst tiers:

| Tier | Scope | SLA | Escalation Trigger |
|------|-------|-----|-------------------|
| **T1** | Enrichment-first alerts, straightforward triage (TP→escalate, FP→tune, benign TP→close) | 15 min (critical), 60 min (high) | Cannot resolve within SLA; attack chain detected |
| **T2** | Complex investigations, cross-source hunting, containment recommendations | 4h (critical), 24h (high) | Confirmed incident requiring coordinated response |
| **T3 / IR** | Confirmed incidents, forensic analysis, executive communication, threat hunting | Per IR SLA | Regulatory notification threshold |

---

## 8. Detection Evasion and Counter-Evasion

Attackers actively work to evade detection. Understanding evasion techniques is essential for building resilient detections.

### 8.1 Log Tampering and Suppression

**Event log clearing:**
```
# Windows — clear Security log
wevtutil cl Security

# Detection: Event ID 1102 (Security log cleared) — always logged even when the log is cleared
# Event ID 104 (System log cleared)
```

Sigma rule:
```yaml
title: Security Event Log Cleared
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 1102
  condition: selection
level: critical
```

**Selective event deletion.** Tools like `Invoke-Phant0m` and `Danderspritz` (NSA toolset) can kill the Event Log Service's threads, stopping logging without generating Event ID 1102. `EvtMuteHook` hooks `NtTraceEvent` to selectively suppress specific events while allowing others through.

**Detection of log suppression:** Monitor for gaps in log sequences. Security events have incrementing Record IDs; a gap in the sequence indicates deleted events:

```kql
SecurityEvent
| where TimeGenerated > ago(1h)
| serialize
| extend PrevRecordId = prev(EventRecordId)
| extend Gap = EventRecordId - PrevRecordId
| where Gap > 1
| project TimeGenerated, Computer, EventRecordId, PrevRecordId, Gap
```

**Counter-evasion:** Forward logs to a remote collector in real-time (SIEM ingestion should be near-real-time, so tampered logs on the host do not affect already-ingested events). Use Windows Event Forwarding or agent-based collection with in-memory buffering. Enable `AuditPolicy` → `Audit log has been cleared` subcategory.

### 8.2 Timestamp Manipulation

Attackers use `timestomp` (Cobalt Strike, Metasploit) to modify file creation/modification timestamps to blend malicious files with legitimate system files. `$STANDARD_INFORMATION` timestamps are modifiable from user mode; `$FILE_NAME` timestamps (stored in the MFT's `$FILE_NAME` attribute) are only modifiable from kernel mode.

**Detection:** Compare `$SI` and `$FN` timestamps. A file where `$SI` creation time is older than `$FN` creation time has been timestomped (the user-visible `$SI` was set backward, but the MFT `$FN` timestamp reflects the actual file creation). Sysmon Event ID 2 (FileCreateTime changed) detects explicit `SetFileTime` calls.

```yaml
title: File Creation Time Modified — Timestomping
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 2
  filter_legitimate:
    Image|endswith:
      - '\explorer.exe'
      - '\msiexec.exe'
  condition: selection and not filter_legitimate
level: medium
```

### 8.3 Living-off-the-Land (LOLBin) Evasion

LOLBins are legitimate signed binaries (part of the OS or trusted software) that can be abused for malicious purposes. They evade process-name-based detections because the process is legitimate — the malice is in the arguments and context.

**Detection approach:** Command-line analysis (not just process name), parent-child process relationships, and behavioral context.

Key LOLBin detections:

```yaml
# certutil.exe used for download
title: Certutil Download — LOLBin Abuse
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\certutil.exe'
    CommandLine|contains:
      - '-urlcache'
      - '-split'
      - '-f '
      - 'http'
  condition: selection
level: high

---
# mshta.exe executing script
title: MSHTA Script Execution
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\mshta.exe'
    CommandLine|contains:
      - 'javascript:'
      - 'vbscript:'
      - 'http'
  condition: selection
level: high

---
# regsvr32.exe scrobj.dll (Squiblydoo)
title: Regsvr32 Scriptlet Execution
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\regsvr32.exe'
    CommandLine|contains:
      - '/i:http'
      - '/i:ftp'
      - 'scrobj.dll'
  condition: selection
level: high
```

### 8.4 Encrypted C2 and Network Evasion

Encrypted C2 channels (HTTPS, DNS-over-HTTPS) evade content-based network inspection. Detection must rely on behavioral indicators rather than payload inspection:

**Beacon interval analysis:**
```spl
# Splunk — detect periodic beaconing
index=firewall src_ip=* dest_ip=*
| bin _time span=1m
| stats count by src_ip, dest_ip, _time
| streamstats current=f window=60 avg(count) as avg, stdev(count) as stdev by src_ip, dest_ip
| eval coefficient_of_variation = stdev / avg
| where coefficient_of_variation < 0.3 AND avg > 0
| stats count as beacon_minutes, avg(avg) as avg_connections by src_ip, dest_ip
| where beacon_minutes > 30
```

**JA3/JA4 fingerprint anomalies:**
```spl
# Splunk — detect unknown JA3 fingerprints
index=zeek sourcetype=zeek_ssl
| lookup known_ja3 ja3 OUTPUT application, expected
| where isnull(application)
| stats count, values(server_name) as sni, dc(server_name) as unique_sni
    by src_ip, ja3
| where count > 10
```

**DNS tunneling detection:**
```yaml
# Sigma rule for DNS tunneling indicators
title: Potential DNS Tunneling — High Entropy Queries
logsource:
  category: dns_query
detection:
  selection:
    query_length|gte: 50
  condition: selection | count(query) by src_ip > 100 within 10m
level: medium
```

Suricata rule:
```
alert dns $HOME_NET any -> any 53 (msg:"DNS Tunneling - Excessive TXT Queries";
  dns.query; content:"."; offset:30;
  threshold: type both, track by_src, count 50, seconds 300;
  classtype:bad-unknown; sid:1000001; rev:1;)
```

### 8.5 Anti-Forensics Summary

| Evasion Technique | Detection Method | Counter-Evasion |
|-------------------|-----------------|-----------------|
| Event log clearing | Event ID 1102/104 | Remote log forwarding (already ingested) |
| Selective event suppression | Record ID gap analysis, Event Log Service thread monitoring | Kernel-level ETW consumers, `Microsoft-Windows-Threat-Intelligence` provider |
| Timestomping | Sysmon Event ID 2, `$SI` vs `$FN` timestamp comparison | MFT analysis, NTFS journal ($UsnJrnl) |
| LOLBin execution | Command-line analysis, parent-child context | Behavioral detections, not process-name-based |
| Encrypted C2 | JA3/JA4, beacon interval analysis, DNS entropy | TLS inspection (where policy allows), behavioral network analysis |
| Sysmon config bypass | Disabling Sysmon driver, unloading filter | Monitor Sysmon service status, driver load events, use multiple telemetry sources |
| AMSI/ETW patching | Integrity monitoring of `amsi.dll`/`ntdll.dll` `.text` sections | Kernel-level telemetry (not dependent on user-mode hooks) |

---

## 9. Threat Hunting

Threat hunting is the proactive, hypothesis-driven search for adversary activity that current automated detections may miss. Unlike detection (automated, reactive), hunting is manual, proactive, and exploratory.

### 9.1 Hypothesis-Driven Hunting Methodology

Each hunt starts with a hypothesis derived from threat intelligence, incident retrospectives, or gap analysis:

```
Hypothesis: "APT group X targets our industry using DLL search-order hijacking
             via signed Microsoft binaries. Our current detections may not cover
             the specific DLL names they use."

Data sources: Sysmon Event ID 7 (Image Loaded), process creation with DLL paths
Hunt query: Search for unsigned DLLs loaded from unusual paths by signed binaries
Expected result: Either confirm no activity (document coverage) or identify
                 suspicious DLL loads requiring investigation
```

### 9.2 Hunting Query Patterns

**Frequency analysis (rare process execution):**
```spl
# Splunk — find processes executed on fewer than 3 hosts in 30 days
index=sysmon EventCode=1
| stats dc(Computer) as host_count, values(Computer) as hosts,
    values(User) as users, latest(CommandLine) as last_cmdline by Image
| where host_count < 3
| sort host_count
```

```kql
// Sentinel — same hunt
DeviceProcessEvents
| where Timestamp > ago(30d)
| summarize HostCount = dcount(DeviceName), Hosts = make_set(DeviceName, 5),
    Users = make_set(AccountName, 5),
    LastCmdLine = arg_max(Timestamp, ProcessCommandLine) by FileName
| where HostCount < 3
| sort by HostCount asc
```

**Data stacking (outlier detection):**
```spl
# Splunk — stack analysis of outbound connections by destination
index=firewall action=allowed direction=outbound
| stats sum(bytes_out) as total_bytes, count as conn_count,
    dc(src_ip) as unique_sources by dest_ip
| eventstats avg(total_bytes) as avg_bytes, stdev(total_bytes) as stdev_bytes
| eval zscore = (total_bytes - avg_bytes) / stdev_bytes
| where zscore > 3
| lookup geo_ip ip AS dest_ip OUTPUT country, asn_org
| table dest_ip, total_bytes, conn_count, unique_sources, zscore, country, asn_org
```

**Long-tail analysis (first-seen detection):**
```kql
// Sentinel — processes seen for the first time in the last 24 hours
let baseline = DeviceProcessEvents
    | where Timestamp between (ago(30d) .. ago(1d))
    | distinct FileName;
DeviceProcessEvents
| where Timestamp > ago(1d)
| where FileName !in (baseline)
| project Timestamp, DeviceName, FileName, ProcessCommandLine, AccountName
```

**DLL search-order hijacking hunt:**
```kql
DeviceImageLoadEvents
| where Timestamp > ago(7d)
| where not(FolderPath startswith "C:\\Windows\\System32" or
            FolderPath startswith "C:\\Windows\\SysWOW64" or
            FolderPath startswith "C:\\Program Files")
| where not(IsSigned)
| join kind=inner (
    DeviceProcessEvents
    | where InitiatingProcessIntegrityLevel in ("High", "System")
    | project DeviceId, InitiatingProcessId = ProcessId, InitiatingProcessFileName = FileName
) on DeviceId, $left.InitiatingProcessId == $right.InitiatingProcessId
| project Timestamp, DeviceName, FileName, FolderPath, InitiatingProcessFileName,
    SHA256 = SHA256
```

---

## 10. Detection Engineering Team Structure and Metrics

### 10.1 Role Differentiation

| Role | Responsibilities | Capacity Allocation |
|------|-----------------|---------------------|
| **Detection Engineer** | Write/maintain Sigma rules, manage CI/CD pipeline, gap analysis | 40% new rules, 30% maintenance/tuning, 30% validation |
| **Threat Hunter** | Proactive hypothesis-driven hunts, findings → detection development | 60% hunting, 20% detection development, 20% TI collaboration |
| **Detection Engineering Lead** | Prioritization, sprint planning, metrics reporting, stakeholder communication | 30% technical (rule review), 70% management |

### 10.2 Detection Metrics and Reporting

**Coverage metrics:**

| Metric | Definition | Target |
|--------|-----------|--------|
| ATT&CK coverage % | Techniques with ≥1 validated detection / total techniques | > 60% of high-priority techniques |
| Defense-in-depth coverage | Techniques with ≥2 independent detections | > 30% of high-priority techniques |
| Telemetry coverage | Required log sources collected from all endpoints | > 95% for Tier 1 sources |

**Effectiveness metrics:**

| Metric | Definition | Target |
|--------|-----------|--------|
| MTTD (Mean Time to Detect) | First detectable event → first alert | < 15 min for automated detections |
| MTTR (Mean Time to Respond) | First alert → containment action | < 4h for critical, < 24h for high |
| True positive rate (per rule) | TP / (TP + FP) | > 50% per rule (average across library) |
| Purple team detection rate | Simulated attacks detected / simulated attacks executed | > 80% |

**Operational metrics:**

| Metric | Definition | Review Cadence |
|--------|-----------|----------------|
| Rules in production | Total active detection rules | Monthly |
| Rules added/modified/retired | Change velocity | Monthly |
| Mean rule age | Average time since last rule review | Quarterly (target: < 6 months) |
| False positive rate by category | FP rate grouped by ATT&CK tactic | Monthly |

These metrics should be reported to security leadership monthly and used to prioritize detection engineering investments.

---

## 11. Advanced Detection Rule Development

The detection-as-code pipeline described in §2 provides the infrastructure for rule lifecycle management. This section focuses on the engineering discipline of writing high-fidelity detection rules: Sigma best practices for cross-backend portability, correlation rule patterns for multi-event attack chains, systematic false positive management, and validation beyond basic syntax checking.

### 11.1 Sigma Rule Writing Best Practices

**Field mapping and logsource abstraction.** A well-written Sigma rule is backend-agnostic — it compiles correctly against Splunk, Elastic, Sentinel, Chronicle, and QRadar without modification. This portability depends on correct use of Sigma's abstraction layers.

The `logsource` block defines which data the rule targets in an abstract manner. The pySigma backend pipelines (e.g., `sysmon`, `ecs_windows`, `splunk_windows`) handle mapping logsource categories to concrete index names and field names in each SIEM:

```yaml
# GOOD: Portable logsource abstraction
logsource:
  category: process_creation
  product: windows

# BAD: Backend-specific field names in logsource
logsource:
  product: windows
  service: sysmon
  # This locks the rule to Sysmon — if the backend uses
  # Windows Security 4688 or EDR process events, it won't map
```

Field selection determines whether a rule compiles cleanly across backends. Use Sigma's standard field names and rely on the processing pipeline for backend translation:

| Sigma Standard Field | Sysmon Field | Windows Security 4688 | ECS Field | CIM Field |
|---------------------|-------------|----------------------|-----------|-----------|
| `Image` | `Image` | `NewProcessName` | `process.executable` | `process` |
| `CommandLine` | `CommandLine` | `CommandLine` | `process.command_line` | `process_command` |
| `ParentImage` | `ParentImage` | `ParentProcessName` | `process.parent.executable` | `parent_process` |
| `User` | `User` | `SubjectUserName` | `user.name` | `user` |
| `TargetFilename` | `TargetFilename` | N/A | `file.path` | `file_path` |
| `DestinationIp` | `DestinationIp` | N/A | `destination.ip` | `dest_ip` |
| `SourceIp` | `SourceIp` | N/A | `source.ip` | `src_ip` |
| `Hashes` | `Hashes` | N/A | `process.hash.*` | `file_hash` |

**Modifier usage for resilient matching.** Sigma modifiers (`|contains`, `|endswith`, `|startswith`, `|re`, `|cidr`, `|all`) provide matching semantics that survive field value variations across environments:

```yaml
detection:
  selection:
    Image|endswith:
      - '\rundll32.exe'     # Matches regardless of full path
    CommandLine|contains|all:
      - 'comsvcs'
      - 'MiniDump'          # Both strings must be present
    CommandLine|re: '(?i).*sekurlsa::logonpasswords.*'
  filter_known:
    ParentImage|endswith:
      - '\svchost.exe'
      - '\services.exe'
    CommandLine|contains:
      - 'DllRegisterServer'  # Legitimate rundll32 registration
  condition: selection and not filter_known
```

**Correlation rules.** Sigma 1.1+ introduces native correlation rules that express relationships between events. These are essential for detecting multi-step attacks that no single event reveals:

Temporal correlation — two events occurring within a time window:

```yaml
# Credential access followed by lateral movement on same host
name: credential_dump_then_lateral_movement
type: event_count
rules:
  credential_access:
    title: Credential Access Tool Execution
    logsource:
      category: process_creation
      product: windows
    detection:
      selection:
        Image|endswith:
          - '\mimikatz.exe'
          - '\procdump.exe'
        CommandLine|contains:
          - 'sekurlsa'
          - 'lsass'
      condition: selection
  lateral_movement:
    title: Remote Service Execution
    logsource:
      category: process_creation
      product: windows
    detection:
      selection:
        Image|endswith:
          - '\psexec.exe'
          - '\wmic.exe'
        CommandLine|contains:
          - '\\\\' # UNC path to remote host
      condition: selection
group-by:
  - ComputerName
timespan: 30m
condition: credential_access and lateral_movement
level: critical
```

Value-count correlation — threshold-based aggregation:

```yaml
# Brute-force detection: >20 failed logons from same source in 5 minutes
name: brute_force_logon_attempts
type: event_count
rules:
  failed_logon:
    title: Failed Logon Attempt
    logsource:
      product: windows
      service: security
    detection:
      selection:
        EventID: 4625
      condition: selection
group-by:
  - IpAddress
timespan: 5m
condition: failed_logon >= 20
level: high
```

### 11.2 Sigma HQ Contribution Workflow and Quality Checklist

Sigma HQ is the community-maintained rule repository serving as the de facto standard for detection signatures. Contributing rules upstream improves the community's collective defense posture and subjects the organization's detections to external peer review.

**Contribution workflow:**

```bash
# Fork and clone the SigmaHQ/sigma repository
gh repo fork SigmaHQ/sigma --clone

# Create a feature branch per rule or rule set
git checkout -b rules/credential-access/kerberoasting-rc4-downgrade

# Place rule in correct directory per ATT&CK tactic
# rules/windows/process_creation/
# rules/windows/builtin/security/
# rules/linux/process_creation/
# rules/cloud/aws/
# rules/network/

# Validate before committing
sigma check rules/windows/process_creation/proc_creation_win_kerberoasting_rc4.yml

# Run sigma test to verify rule compiles across backends
sigma convert -t splunk -p sysmon rules/windows/process_creation/proc_creation_win_kerberoasting_rc4.yml
sigma convert -t elasticsearch -p ecs_windows rules/windows/process_creation/proc_creation_win_kerberoasting_rc4.yml
sigma convert -t kusto -p microsoft365defender rules/windows/process_creation/proc_creation_win_kerberoasting_rc4.yml

# Submit PR with attack simulation evidence
gh pr create --title "Add Kerberoasting RC4 downgrade detection" \
  --body "## Detection\nDetects RC4 ticket requests ...\n## Validation\nTested with Rubeus kerberoast /rc4opsec"
```

**Sigma HQ quality checklist (mandatory before submission):**

| Criterion | Requirement | Common Failure |
|-----------|-------------|----------------|
| `title` | Descriptive, unique, < 100 chars | Too generic ("Suspicious PowerShell") |
| `id` | UUIDv4, globally unique | Reused or missing |
| `status` | `experimental` for new rules | Submitting as `stable` without community validation |
| `description` | Explain what the rule detects and why it is suspicious | Missing or copy-pasted from title |
| `references` | Link to threat report, blog, or ATT&CK technique page | No references |
| `author` | Real name or handle | Missing |
| `date` | YYYY/MM/DD of creation | Wrong format |
| `tags` | ATT&CK technique IDs as `attack.tXXXX.YYY` | Missing technique mapping |
| `logsource` | Use standard categories, not backend-specific service names | Hardcoded Sysmon service |
| `detection` | No backend-specific syntax in field names or values | Using Splunk field names |
| `falsepositives` | Document known FP scenarios | Empty or "Unknown" |
| `level` | Justified severity (informational/low/medium/high/critical) | Inflated severity |

### 11.3 Detection Logic Testing and Validation

The §5.2 pipeline (Atomic Red Team, BAS platforms) validates whether a detection fires in production. This section addresses the engineering-level testing that happens before deployment: unit tests against synthetic and captured event data, integration tests against test SIEM instances, and adversary simulation platforms that generate comprehensive technique coverage.

**MITRE Caldera for automated adversary simulation:**

```bash
# Deploy Caldera server
git clone https://github.com/mitre/caldera.git --recursive
cd caldera
pip install -r requirements.txt
python server.py --insecure --build

# Caldera provides adversary profiles that chain techniques:
# "Advanced Persistent Threat" profile executes:
#   T1059.001 (PowerShell) → T1003.001 (LSASS dump) →
#   T1021.002 (SMB lateral movement) → T1048 (Exfiltration over C2)

# Deploy agent on test endpoint
# (from Caldera web UI: download Sandcat agent for target OS)

# Run operation against deployed agents
# Select adversary profile → Select agent group → Execute
# Caldera logs all technique execution timestamps for detection validation

# Export operation results for correlation with SIEM alerts
curl -X POST http://caldera:8888/api/v2/operations \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{"name":"Detection Validation Q1","adversary":{"adversary_id":"abc123"},"planner":{"id":"atomic"},"source":{"id":"basic"}}'
```

**DetectionLab for isolated validation environments:**

DetectionLab provides a pre-built lab environment (Windows DC, Windows workstation, Splunk/ELK, osquery, Sysmon) specifically designed for detection development and testing. The environment includes pre-configured log forwarding so that rule authors can execute attack techniques and immediately validate detection coverage.

```bash
# Deploy DetectionLab with Vagrant
git clone https://github.com/clong/DetectionLab.git
cd DetectionLab/Vagrant
vagrant up

# Environment provides:
# - DC (win2016):       Active Directory, GPO, WEF collector
# - WIN10:              Domain-joined workstation, Sysmon, osquery
# - logger (ubuntu):    Splunk, Fleet (osquery manager)
# - All logs forwarded to Splunk instance at https://logger:8000

# Test a detection rule:
# 1. Write Sigma rule
# 2. Compile to SPL: sigma convert -t splunk -p sysmon rule.yml
# 3. Execute technique on WIN10 (e.g., Invoke-Mimikatz)
# 4. Verify compiled SPL query returns the expected event in Splunk
# 5. Add positive/negative test events to CI test suite
```

**Structured test case format for CI/CD integration:**

```yaml
# tests/credential_access/test_lsass_access_via_procdump.yml
rule: rules/windows/sysmon/sysmon_lsass_access_procdump.yml
positive_tests:
  - description: "Procdump targeting lsass.exe"
    event:
      EventID: 10
      SourceImage: 'C:\Tools\procdump64.exe'
      TargetImage: 'C:\Windows\System32\lsass.exe'
      GrantedAccess: '0x1FFFFF'
      CallTrace: '|C:\Windows\SYSTEM32\ntdll.dll+9C4F4|'
    expected: match
  - description: "Unsigned binary accessing LSASS with full access"
    event:
      EventID: 10
      SourceImage: 'C:\Users\attacker\payload.exe'
      TargetImage: 'C:\Windows\System32\lsass.exe'
      GrantedAccess: '0x1FFFFF'
    expected: match
negative_tests:
  - description: "LSASS accessed by Windows Defender (legitimate)"
    event:
      EventID: 10
      SourceImage: 'C:\ProgramData\Microsoft\Windows Defender\Platform\4.18.2301.6-0\MsMpEng.exe'
      TargetImage: 'C:\Windows\System32\lsass.exe'
      GrantedAccess: '0x1400'
    expected: no_match
  - description: "Procdump targeting non-LSASS process"
    event:
      EventID: 10
      SourceImage: 'C:\Tools\procdump64.exe'
      TargetImage: 'C:\Windows\System32\svchost.exe'
      GrantedAccess: '0x1FFFFF'
    expected: no_match
```

### 11.4 False Positive Management

False positives are the primary threat to SOC effectiveness. A rule generating even 5 FPs per day across a conglomerate with hundreds of rules creates thousands of wasted analyst-hours monthly. Systematic FP management treats false positive reduction as an engineering discipline rather than an ad-hoc tuning exercise.

**Exception architecture.** Rather than embedding exceptions directly in detection rules (which obscures the original detection intent), maintain exceptions as separate overlay files that are merged at compilation time:

```yaml
# rules/windows/process_creation/proc_creation_win_susp_powershell_download.yml
# (core rule — no environment-specific exceptions)
title: Suspicious PowerShell Download Cradle
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    Image|endswith: '\powershell.exe'
    CommandLine|contains:
      - 'downloadstring'
      - 'invoke-webrequest'
      - 'wget '
      - 'curl '
      - 'Net.WebClient'
      - 'Start-BitsTransfer'
  condition: selection
level: medium
```

```yaml
# exceptions/acme-corp/proc_creation_win_susp_powershell_download.yml
# (environment-specific exceptions — separate file, version-controlled)
rule_id: "a]b12c34-..."
exceptions:
  - name: "SCCM software distribution"
    added: 2025-01-15
    added_by: "detection-eng-team"
    justification: "SCCM client uses PowerShell download cradles for patch deployment"
    review_date: 2025-07-15
    filter:
      ParentImage|endswith: '\ccmexec.exe'
  - name: "Chocolatey package manager"
    added: 2025-02-20
    added_by: "detection-eng-team"
    justification: "Chocolatey install scripts use Invoke-WebRequest"
    review_date: 2025-08-20
    filter:
      CommandLine|contains: 'chocolatey.org'
      ParentImage|endswith: '\choco.exe'
```

The CI/CD pipeline merges exceptions into compiled rules at deployment time. Exception files carry `review_date` fields — a scheduled job flags exceptions past their review date for re-evaluation.

**Allowlisting strategies by scope:**

| Strategy | Scope | Risk | Use When |
|----------|-------|------|----------|
| Process path allowlist | Specific binary executing the detected behavior | Medium — attackers can hijack/spoof paths | Known software with stable installation paths |
| Hash allowlist | Exact binary version | Low — binary-specific, no spoofing | Fixed-version software (not auto-updating) |
| Parent-child allowlist | Specific parent process spawning detected child | Medium — depends on parent integrity | Known workflows (SCCM→PowerShell, Jenkins→cmd) |
| User/service account allowlist | Specific user or service account | High — credential compromise bypasses | Service accounts with narrow function |
| Network destination allowlist | Specific IP/domain/CIDR | Medium-High — CDN IPs are shared | Known SaaS/vendor endpoints |
| Time-window allowlist | Suppress during known maintenance windows | Medium — attacker could time operations | Scheduled patching, backup jobs |
| Composite allowlist | Combination of above (AND logic) | Lower — multiple factors must match | Strongest exceptions |

**FP tracking metrics (tracked per rule in the detection engineering database):**

| Metric | Formula | Target | Action Threshold |
|--------|---------|--------|-----------------|
| FP rate | FP / (TP + FP) over 30 days | < 50% | > 70% → mandatory tuning sprint |
| FP volume | Raw FP count per rule per week | < 10/week | > 50/week → disable or emergency tune |
| Exception count | Number of active exceptions per rule | < 5 | > 10 → consider rule redesign |
| Exception age | Days since last exception review | < 180 days | > 180 → flagged for review |
| Tuning cycle time | Time from FP report to exception deployed | < 48h | > 1 week → process improvement |

### 11.5 Multi-Event Correlation Patterns for Attack Scenarios

The following patterns detect specific attack chains that require correlating multiple events across log sources. Each pattern is provided in SPL, KQL, and YARA-L to demonstrate cross-platform implementation.

**Scenario 1: Kerberoasting with RC4 downgrade → service account abuse**

The attacker requests Kerberos service tickets with RC4 encryption (weaker, crackable offline), then uses the cracked service account credential to access resources.

SPL:
```spl
index=wineventlog EventCode=4769 TicketEncryptionType=0x17
| stats count as tgs_requests, dc(ServiceName) as unique_services,
    values(ServiceName) as services by TargetUserName, IpAddress
| where tgs_requests > 5 AND unique_services > 3
| rename TargetUserName as requesting_user, IpAddress as src_ip
| join src_ip type=left
    [search index=wineventlog EventCode=4624 LogonType=3
     | where Account_Name IN ("svc_*", "service_*", "app_*")
     | rename Account_Name as service_account, Computer as target_host
     | stats earliest(_time) as first_service_logon, values(target_host) as targets
         by IpAddress, service_account
     | rename IpAddress as src_ip]
| where isnotnull(service_account)
| eval time_delta = first_service_logon - _time
| where time_delta > 0 AND time_delta < 86400
| table requesting_user, src_ip, tgs_requests, unique_services, services,
    service_account, targets, time_delta
```

KQL:
```kql
let KerberoastActivity = SecurityEvent
    | where EventID == 4769 and TicketEncryptionType == "0x17"
    | summarize TGSRequests = count(), UniqueServices = dcount(ServiceName),
        Services = make_set(ServiceName, 20)
        by RequestingUser = TargetUserName, SourceIP = IpAddress
    | where TGSRequests > 5 and UniqueServices > 3;
let ServiceAccountLogons = SecurityEvent
    | where EventID == 4624 and LogonType == 3
    | where TargetUserName matches regex @"^(svc_|service_|app_)"
    | summarize FirstLogon = min(TimeGenerated), Targets = make_set(Computer, 10)
        by SourceIP = IpAddress, ServiceAccount = TargetUserName;
KerberoastActivity
| join kind=inner ServiceAccountLogons on SourceIP
| where FirstLogon > TGSRequests
| project RequestingUser, SourceIP, TGSRequests, UniqueServices,
    ServiceAccount, Targets, TimeDelta = datetime_diff('minute', FirstLogon, TGSRequests)
```

YARA-L:
```
rule kerberoasting_followed_by_service_account_abuse {
  meta:
    author = "Detection Engineering"
    description = "Kerberoasting (RC4 TGS requests) followed by service account logon"
    severity = "HIGH"
    mitre_attack = "T1558.003, T1078.002"

  events:
    // RC4 Kerberos service ticket request
    $tgs.metadata.event_type = "NETWORK_CONNECTION"
    $tgs.metadata.product_event_type = "4769"
    $tgs.security_result.detection_fields["TicketEncryptionType"] = "0x17"
    $tgs.principal.user.userid = $requesting_user
    $tgs.principal.ip = $src_ip

    // Subsequent network logon with service account
    $logon.metadata.event_type = "USER_LOGIN"
    $logon.metadata.product_event_type = "4624"
    $logon.extensions.auth.type = "NETWORK"
    $logon.target.user.userid = $service_account
    $logon.principal.ip = $src_ip

  match:
    $src_ip over 24h

  condition:
    #tgs > 5 and #logon > 0
    and re.regex($service_account, `^(svc_|service_|app_)`)
    and $tgs.metadata.event_timestamp.seconds <
        $logon.metadata.event_timestamp.seconds
}
```

**Scenario 2: Phishing → Macro execution → C2 beacon establishment**

A user opens a phishing attachment, a macro spawns a child process, which establishes an outbound network connection to an external IP.

SPL:
```spl
index=sysmon EventCode=1
    (ParentImage="*\\WINWORD.EXE" OR ParentImage="*\\EXCEL.EXE" OR ParentImage="*\\POWERPNT.EXE")
    (Image="*\\cmd.exe" OR Image="*\\powershell.exe" OR Image="*\\wscript.exe"
     OR Image="*\\mshta.exe" OR Image="*\\rundll32.exe")
| rename Computer as host, ProcessId as child_pid, Image as child_process,
    CommandLine as child_cmdline, ParentImage as office_app
| join host child_pid type=inner
    [search index=sysmon EventCode=3 DestinationIsIpv6=false
     | where NOT cidrmatch("10.0.0.0/8", DestinationIp)
         AND NOT cidrmatch("172.16.0.0/12", DestinationIp)
         AND NOT cidrmatch("192.168.0.0/16", DestinationIp)
     | rename Computer as host, ProcessId as child_pid, DestinationIp as c2_ip,
         DestinationPort as c2_port]
| table _time, host, office_app, child_process, child_cmdline, c2_ip, c2_port
| lookup threat_intel_ip indicator AS c2_ip OUTPUT threat_name
```

KQL:
```kql
let OfficeChildProcesses = DeviceProcessEvents
    | where Timestamp > ago(1h)
    | where InitiatingProcessFileName in~ ("winword.exe", "excel.exe", "powerpnt.exe")
    | where FileName in~ ("cmd.exe", "powershell.exe", "wscript.exe",
        "mshta.exe", "rundll32.exe", "cscript.exe")
    | project DeviceId, Timestamp, DeviceName, OfficeApp = InitiatingProcessFileName,
        ChildProcess = FileName, ChildPID = ProcessId,
        CommandLine = ProcessCommandLine;
OfficeChildProcesses
| join kind=inner (
    DeviceNetworkEvents
    | where Timestamp > ago(1h)
    | where RemoteIPType == "Public"
    | where ActionType == "ConnectionSuccess"
    | project DeviceId, NetTimestamp = Timestamp, InitiatingProcessId,
        RemoteIP, RemotePort, RemoteUrl
) on DeviceId, $left.ChildPID == $right.InitiatingProcessId
| where NetTimestamp >= Timestamp
| project Timestamp, DeviceName, OfficeApp, ChildProcess, CommandLine,
    RemoteIP, RemotePort, RemoteUrl
```

**Scenario 3: Privilege escalation via scheduled task creation by low-privilege user**

A non-admin user creates a scheduled task running as SYSTEM — a common privilege escalation vector.

SPL:
```spl
index=wineventlog EventCode=4698
| where NOT match(SubjectUserName, "^(SYSTEM|LOCAL SERVICE|NETWORK SERVICE)$")
| spath input=TaskContent output=task_action path=Actions.Exec.Command
| spath input=TaskContent output=task_principal path=Principals.Principal.UserId
| where task_principal="S-1-5-18" OR task_principal="SYSTEM"
| lookup admin_users user AS SubjectUserName OUTPUT is_admin
| where is_admin!="true"
| table _time, Computer, SubjectUserName, TaskName, task_action, task_principal
```

KQL:
```kql
SecurityEvent
| where EventID == 4698
| where SubjectUserName !in~ ("SYSTEM", "LOCAL SERVICE", "NETWORK SERVICE")
| extend TaskXml = parse_xml(EventData)
| extend TaskAction = tostring(TaskXml.Actions.Exec.Command)
| extend TaskRunAs = tostring(TaskXml.Principals.Principal.UserId)
| where TaskRunAs in~ ("S-1-5-18", "SYSTEM", "NT AUTHORITY\\SYSTEM")
| join kind=leftanti (
    IdentityInfo
    | where AssignedRoles has "Admin"
    | project AccountName
) on $left.SubjectUserName == $right.AccountName
| project TimeGenerated, Computer, SubjectUserName, TaskName, TaskAction, TaskRunAs
```

**Scenario 4: Data staging and exfiltration via archive creation followed by large outbound transfer**

An attacker stages data by creating archives (rar, 7z, zip) of sensitive directories, then exfiltrates via a large outbound connection.

SPL:
```spl
index=sysmon EventCode=1
    (Image="*\\rar.exe" OR Image="*\\7z.exe" OR Image="*\\zip.exe"
     OR (Image="*\\powershell.exe" AND CommandLine="*Compress-Archive*"))
| rename Computer as host, User as staging_user
| eval archive_time=_time
| join host type=inner
    [search index=firewall action=allowed direction=outbound bytes_out>104857600
     | where NOT cidrmatch("10.0.0.0/8", dest_ip)
     | rename src_ip as host_ip
     | lookup asset_inventory ip AS host_ip OUTPUT hostname as host
     | eval exfil_time=_time
     | stats max(bytes_out) as max_bytes, sum(bytes_out) as total_bytes,
         values(dest_ip) as dest_ips by host, exfil_time]
| where exfil_time > archive_time AND (exfil_time - archive_time) < 7200
| eval total_mb = round(total_bytes/1048576, 2)
| table archive_time, exfil_time, host, staging_user, Image, CommandLine,
    total_mb, dest_ips
```

KQL:
```kql
let ArchiveCreation = DeviceProcessEvents
    | where Timestamp > ago(4h)
    | where FileName in~ ("rar.exe", "7z.exe", "zip.exe")
        or (FileName =~ "powershell.exe" and ProcessCommandLine has "Compress-Archive")
    | project DeviceId, ArchiveTime = Timestamp, DeviceName,
        AccountName, ArchiveCmd = ProcessCommandLine;
let LargeOutbound = DeviceNetworkEvents
    | where Timestamp > ago(4h)
    | where RemoteIPType == "Public"
    | where ActionType == "ConnectionSuccess"
    | summarize TotalBytesSent = sum(SentBytes),
        DestIPs = make_set(RemoteIP, 10)
        by DeviceId, bin(Timestamp, 15m)
    | where TotalBytesSent > 104857600;  // 100 MB
ArchiveCreation
| join kind=inner LargeOutbound on DeviceId
| where Timestamp > ArchiveTime and datetime_diff('hour', Timestamp, ArchiveTime) < 2
| extend TotalMB = round(TotalBytesSent / 1048576.0, 2)
| project ArchiveTime, DeviceName, AccountName, ArchiveCmd, TotalMB, DestIPs
```

---

## 12. SIEM Platform Deep Dive

Conglomerate-scale detection engineering requires deep knowledge of the specific SIEM platform's capabilities, optimization techniques, and limitations. This section provides platform-specific guidance for the six major enterprise SIEMs.

### 12.1 Splunk Enterprise Security

**Index architecture.** Splunk stores data in indexes — logical containers that control retention, access, and search performance. For conglomerate-scale deployments:

```
# Index design by data domain
indexes:
  - name: ep_process          # Endpoint process events (Sysmon 1, EDR)
    maxDataSize: auto_high_volume
    frozenTimePeriodInSecs: 7776000    # 90 days
    homePath: $SPLUNK_DB/ep_process/db
    coldPath: $SPLUNK_DB/ep_process/colddb
    thawedPath: $SPLUNK_DB/ep_process/thaweddb

  - name: ep_network           # Endpoint network events (Sysmon 3, EDR)
    frozenTimePeriodInSecs: 2592000    # 30 days (high volume, shorter retention)

  - name: auth_events          # Authentication (4624/4625/4768/4769)
    frozenTimePeriodInSecs: 31536000   # 365 days

  - name: cloud_audit          # AWS CloudTrail, Azure Activity, GCP Audit
    frozenTimePeriodInSecs: 31536000

  - name: network_flow         # Firewall, proxy, NetFlow
    frozenTimePeriodInSecs: 7776000

  - name: threat_intel         # TI feed indicators (small volume, long retention)
    frozenTimePeriodInSecs: 63072000   # 2 years
```

**Search optimization.** Splunk search performance degrades rapidly with inefficient queries at petabyte scale. The critical optimization techniques:

`tstats` — accelerated search against indexed fields and data models. Orders of magnitude faster than raw `search` because it reads only tsidx files (bloom filters and metadata), not raw event data:

```spl
# BAD: Raw search scanning all events (minutes at scale)
index=ep_process sourcetype=sysmon EventCode=1
| stats count by Image

# GOOD: tstats against the Endpoint data model (seconds at scale)
| tstats count from datamodel=Endpoint.Processes
    where Processes.action_type=allowed
    by Processes.process_name
| rename "Processes.*" as *
```

**Data models and acceleration.** Splunk Common Information Model (CIM) data models normalize events from multiple sourcetypes into a unified schema. Accelerating a data model pre-computes summary data, enabling `tstats` queries:

```
# Accelerate the Endpoint data model
# Settings → Data Models → Endpoint → Edit Acceleration
# Summary Range: 90 days
# Rebuild required after sourcetype mapping changes

# Verify acceleration status
| rest /services/admin/summarization
| where search_name="*Endpoint*"
| table search_name, is_inprogress, access_count, access_time, size_bytes
```

**Summary indexing** for expensive recurring queries:

```spl
# Scheduled search that pre-computes auth failure rates every 15 minutes
# and writes results to a summary index
index=auth_events EventCode=4625
| stats count as failure_count by src_ip, TargetUserName, Computer
| where failure_count > 5
| collect index=summary_auth_failures marker="auth_failures_15m"

# Detection rule queries the summary instead of raw auth events
index=summary_auth_failures search_name="auth_failures_15m"
| where failure_count > 20
| lookup geo_ip ip AS src_ip OUTPUT country
```

**ES correlation search design.** Splunk Enterprise Security correlation searches are the primary detection mechanism. Design principles:

```spl
# Correlation search: Potential credential stuffing across subsidiaries
# Runs every 15 minutes, lookback 30 minutes (overlap for completeness)
| tstats summariesonly=true count as failure_count
    from datamodel=Authentication
    where Authentication.action=failure
    by Authentication.src, Authentication.user, Authentication.dest,
       _time span=15m
| rename "Authentication.*" as *
| stats sum(failure_count) as total_failures,
    dc(user) as unique_users, dc(dest) as unique_targets
    by src
| where total_failures > 50 AND unique_users > 10 AND unique_targets > 3
| lookup asset_lookup ip AS src OUTPUT asset_owner, subsidiary, criticality
| sendalert notable param.search_name="Credential Stuffing - Multi-Target"
    param.severity="high"
    param.security_domain="access"
    param.drilldown_search="index=auth_events src=$src$ EventCode=4625 earliest=-30m"
```

### 12.2 Elastic Security

**ECS (Elastic Common Schema).** ECS is Elastic's normalization schema, designed for consistency across log sources. All Elastic Security detection rules operate on ECS-mapped fields:

Key ECS field categories for detection:
```
event.category:  [authentication, process, network, file, registry, iam]
event.action:    [logon, process_created, connection_attempted, file_created]
event.outcome:   [success, failure, unknown]
process.name, process.executable, process.command_line, process.pid
process.parent.name, process.parent.executable, process.parent.pid
user.name, user.domain, user.id
source.ip, source.port, destination.ip, destination.port
host.name, host.os.type, host.os.platform
file.path, file.name, file.hash.sha256
registry.path, registry.data.strings
```

**Detection rules engine.** Elastic Security supports multiple rule types:

Custom query rules (KQL or ECS-based):
```json
{
  "name": "Suspicious PowerShell Download Activity",
  "rule_id": "custom-ps-download-001",
  "type": "query",
  "query": "process.name:\"powershell.exe\" and process.command_line:(*downloadstring* or *invoke-webrequest* or *Net.WebClient* or *Start-BitsTransfer*)",
  "language": "kuery",
  "index": ["winlogbeat-*", "logs-endpoint.events.*"],
  "severity": "medium",
  "risk_score": 47,
  "tags": ["attack.execution", "attack.t1059.001"],
  "threat": [{
    "framework": "MITRE ATT&CK",
    "tactic": { "id": "TA0002", "name": "Execution" },
    "technique": [{ "id": "T1059.001", "name": "PowerShell" }]
  }]
}
```

EQL sequence rules for multi-step detection:
```json
{
  "name": "Office Application Spawning Shell with Network Activity",
  "type": "eql",
  "query": "sequence by host.name with maxspan=2m [process where event.type == \"start\" and process.parent.name in (\"winword.exe\", \"excel.exe\") and process.name in (\"cmd.exe\", \"powershell.exe\", \"wscript.exe\")] [network where event.type == \"start\" and destination.ip != \"127.0.0.1\" and not cidrmatch(destination.ip, \"10.0.0.0/8\", \"172.16.0.0/12\", \"192.168.0.0/16\")]",
  "language": "eql"
}
```

**ML anomaly detection jobs.** Elastic Security includes pre-built and custom ML jobs for behavioral analytics:

```json
{
  "job_id": "auth_rare_user_logon_location",
  "description": "Detect authentication from unusual source IPs per user",
  "analysis_config": {
    "bucket_span": "15m",
    "detectors": [{
      "function": "rare",
      "by_field_name": "source.ip",
      "partition_field_name": "user.name"
    }],
    "influencers": ["user.name", "source.ip", "host.name"]
  },
  "data_description": { "time_field": "@timestamp" },
  "datafeed_config": {
    "indices": ["winlogbeat-*"],
    "query": {
      "bool": {
        "filter": [
          { "term": { "event.category": "authentication" } },
          { "term": { "event.outcome": "success" } }
        ]
      }
    }
  }
}
```

**Timeline investigation.** The Elastic Security Timeline provides a visual investigation workspace. Analysts construct ad-hoc queries and drag events into timeline entries to build attack narratives. Timeline templates linked to detection rules pre-populate investigation queries, reducing time-to-context during triage.

### 12.3 Microsoft Sentinel

**KQL optimization for cost and performance.** Sentinel charges per GB ingested and per query compute. Efficient KQL is a direct cost control:

```kql
// BAD: Scans entire SecurityEvent table
SecurityEvent
| where EventID == 4625
| summarize count() by TargetUserName

// GOOD: Time-bound, specific table, column pruning
SecurityEvent
| where TimeGenerated > ago(1h)
| where EventID == 4625
| project TimeGenerated, TargetUserName, IpAddress, Computer
| summarize FailureCount = count() by TargetUserName
| where FailureCount > 20
```

Optimization techniques:
- `where` filters as early as possible (time filter first, then specific columns)
- `project` immediately after `where` to limit columns scanned
- Avoid `*` in `make-set()` or `make-list()` — specify max elements
- Use `has` instead of `contains` for indexed string matching
- Use `in~` instead of chained `or` for case-insensitive membership tests
- Replace `join` with `lookup` for enrichment from small reference tables

**Analytics rules vs. hunting queries.** Sentinel distinguishes between scheduled analytics rules (automated detection, creates incidents) and hunting queries (manual, on-demand, no automatic incident creation). Design guidelines:

| Aspect | Analytics Rule | Hunting Query |
|--------|---------------|---------------|
| Execution | Scheduled (5m–24h intervals) | Manual or scheduled bookmark |
| Output | Creates incident + entities | Returns results for analyst review |
| Complexity budget | < 10s execution time | Can be expensive (minutes) |
| FP tolerance | Low — every trigger creates work | Higher — analyst filters manually |
| Use case | Known-bad patterns, validated detections | Exploratory analysis, hypothesis testing |

**Fusion detections.** Sentinel's Fusion engine correlates low-fidelity signals across multiple data sources to surface multi-stage attacks that no single detection rule would catch. Fusion operates as a ML-based correlation engine, combining alerts from different providers (Defender for Endpoint, Defender for Identity, Defender for Cloud Apps, Azure AD Identity Protection) into composite incidents. Fusion is not user-configurable — Microsoft maintains the correlation logic. The detection engineering team's role is ensuring all relevant data connectors feed into Sentinel so Fusion has complete signal coverage.

**Lighthouse multi-tenant management.** For conglomerates managing multiple Azure tenants (one per subsidiary), Azure Lighthouse enables centralized Sentinel operations across tenants without requiring separate authentication:

```
# Architecture:
# Managing Tenant (SOC)
#   └── Lighthouse delegation from Subsidiary-A tenant
#   └── Lighthouse delegation from Subsidiary-B tenant
#   └── Lighthouse delegation from Subsidiary-C tenant
#
# SOC analysts in the managing tenant can:
#   - View incidents across all subsidiary Sentinel workspaces
#   - Run hunting queries across workspaces
#   - Deploy analytics rules centrally via ARM templates or Terraform
#   - Manage playbook execution across tenants

# Cross-workspace query from managing tenant:
union
  workspace("subsidiary-a-sentinel").SecurityEvent,
  workspace("subsidiary-b-sentinel").SecurityEvent,
  workspace("subsidiary-c-sentinel").SecurityEvent
| where TimeGenerated > ago(1h)
| where EventID == 4625
| summarize FailureCount = count() by TenantId, TargetUserName
| where FailureCount > 50
```

### 12.4 Google Chronicle / SecOps

**YARA-L rule engine.** Chronicle uses YARA-L 2.0 as its native detection language. YARA-L is purpose-built for multi-event correlation over the Unified Data Model (UDM):

```
rule impossible_travel_authentication {
  meta:
    author = "Detection Engineering"
    description = "Same user authenticates from geographically distant locations within short timeframe"
    severity = "HIGH"
    mitre_attack = "T1078"

  events:
    $login1.metadata.event_type = "USER_LOGIN"
    $login1.security_result.action = "ALLOW"
    $login1.target.user.userid = $user
    $login1.principal.ip_geo_artifact.location.country_or_region = $country1

    $login2.metadata.event_type = "USER_LOGIN"
    $login2.security_result.action = "ALLOW"
    $login2.target.user.userid = $user
    $login2.principal.ip_geo_artifact.location.country_or_region = $country2

  match:
    $user over 2h

  condition:
    $login1 and $login2
    and $country1 != $country2
    and $login1.metadata.event_timestamp.seconds <
        $login2.metadata.event_timestamp.seconds
}
```

**UDM schema.** Chronicle normalizes all ingested data into UDM, which provides consistent field paths regardless of the original log source:

| UDM Field Path | Description | Source Mapping Example |
|----------------|-------------|-----------------------|
| `metadata.event_type` | Event classification | `USER_LOGIN`, `PROCESS_LAUNCH`, `NETWORK_CONNECTION` |
| `principal.*` | Entity initiating the action | Source user, source IP, source host |
| `target.*` | Entity receiving the action | Destination host, target user, target file |
| `src.*` | Network source | Source IP/port |
| `security_result.*` | Security verdict | Allow/block, detection name, severity |
| `about.*` | Additional entities referenced | File hashes, URLs, registry keys |

**Entity graph.** Chronicle constructs a graph of entities (users, hosts, IPs, domains, files) and their relationships derived from all ingested events. This graph enables pivot-based investigation: starting from a single suspicious IP, analysts traverse the graph to discover all users who connected to it, all hosts those users logged into, and all processes those hosts executed — without writing sequential queries.

**Retroactive detection.** Chronicle stores raw logs for 12 months (standard) and runs new detection rules retroactively against historical data. When the detection engineering team writes a rule for a newly disclosed technique, Chronicle automatically evaluates it against all stored data, surfacing past incidents that would have been caught. This eliminates the "detection gap window" between technique disclosure and rule deployment.

### 12.5 IBM QRadar

**AQL (Ariel Query Language).** QRadar uses AQL for ad-hoc queries and custom rule expressions:

```sql
-- Failed logon attempts from external IPs
SELECT sourceip, username, COUNT(*) as attempt_count,
       MIN(starttime) as first_attempt, MAX(starttime) as last_attempt
FROM events
WHERE qid = 5000044  -- Authentication failure
  AND INCIDR('10.0.0.0/8', sourceip) = FALSE
  AND INCIDR('172.16.0.0/12', sourceip) = FALSE
  AND INCIDR('192.168.0.0/16', sourceip) = FALSE
  AND starttime > NOW() - 3600000  -- last hour (ms)
GROUP BY sourceip, username
HAVING COUNT(*) > 20
ORDER BY attempt_count DESC
```

**Offense management.** QRadar's offense system groups related events into offenses (analogous to incidents). Offenses are created by rules, and multiple rules can contribute to the same offense (offense chaining). This reduces alert volume by consolidating related detections:

```
# Rule: Brute force followed by successful logon
Rule type: Event rule (with offense creation)
Test group:
  AND when the event QID is one of [5000044] (Auth Failure)
  AND when at least 20 events are seen with the same [Source IP]
      in 5 minutes
Then:
  Create offense
  Offense index: Source IP
  Offense name: "Brute Force from {Source IP}"

# Linked rule: Successful logon after brute force offense
Rule type: Event rule (linked to existing offense)
Test group:
  AND when the event QID is one of [5000001] (Auth Success)
  AND when the source IP is part of an active offense
Then:
  Add to offense
  Set offense severity to 9 (critical)
  Annotate: "Successful logon after brute force — possible compromise"
```

**Reference sets.** QRadar reference sets are in-memory lookup tables used in rules for dynamic allowlisting, blocklisting, and enrichment:

```bash
# Create reference set for known admin workstations
/opt/qradar/bin/ReferenceSetUtil.sh create admin_workstations ALN

# Populate from asset database
/opt/qradar/bin/ReferenceSetUtil.sh add admin_workstations "WS-ADMIN-01"
/opt/qradar/bin/ReferenceSetUtil.sh add admin_workstations "WS-ADMIN-02"

# Use in rules:
# "when Source Asset Name is NOT contained in any of [admin_workstations]"
# This excludes known admin workstations from privilege escalation detections

# Reference set API management
curl -X POST "https://qradar/api/reference_data/sets" \
  -H "SEC: $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"blocked_ips","element_type":"IP","timeout_type":"LAST_SEEN","time_to_live":"2592000"}'
```

**Custom log source parsing.** QRadar uses DSM (Device Support Module) extensions to parse non-standard log formats:

```xml
<!-- Custom DSM for internal application logs -->
<device>
  <name>InternalApp</name>
  <log_source_type_id>4001</log_source_type_id>
  <parsing_order>1</parsing_order>
  <pattern>
    <match>
      <regex>(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+(\w+)\s+\[(\w+)\]\s+user=(\S+)\s+action=(\S+)\s+resource=(\S+)\s+result=(\S+)</regex>
      <capture_group name="DeviceTime">1</capture_group>
      <capture_group name="Severity">2</capture_group>
      <capture_group name="EventCategory">3</capture_group>
      <capture_group name="Username">4</capture_group>
      <capture_group name="EventName">5</capture_group>
      <capture_group name="ObjectName">6</capture_group>
      <capture_group name="EventOutcome">7</capture_group>
    </match>
  </pattern>
</device>
```

### 12.6 SIEM Platform Comparison Matrix

| Capability | Splunk ES | Elastic Security | Microsoft Sentinel | Google Chronicle | IBM QRadar |
|-----------|-----------|-----------------|-------------------|-----------------|-----------|
| **Cost model** | License per GB ingested/day | Self-managed: infra cost; Cloud: per-node + storage | Per GB ingested + per GB analyzed | Per-user (flat rate, unlimited ingestion) | Per-EPS or per-flow license |
| **Optimal scale** | 1–50 TB/day | 500 GB–10 TB/day (self-managed) | Cloud-native, elastic | 1–100+ TB/day (Google infrastructure) | 500 GB–5 TB/day |
| **Data volume handling** | SmartStore (S3 cache tiering), federated search | ILM (hot/warm/cold/frozen), cross-cluster search | Log Analytics workspace, basic/analytics tiers, ADX integration | Petabyte-native, 12-month hot retention | Data gateway, Disconnected Log Collector |
| **Normalization** | CIM (Common Information Model) + Technology Add-ons | ECS (Elastic Common Schema) + Beats/Agent | ASIM (Advanced SIEM Information Model) | UDM (Unified Data Model) + parsers | DSM (Device Support Modules) |
| **Detection language** | SPL, MLTK | KQL (Kibana), EQL (sequences), ES|QL | KQL, Fusion ML | YARA-L 2.0 | AQL, rule builder UI |
| **Correlation capability** | SPL subsearch, join, transaction | EQL sequence, threshold rules | Analytics rules, Fusion multi-signal | YARA-L multi-event, outcome-based | Offense chaining, flow rules |
| **ML/behavioral** | MLTK (external toolkit), UBA premium | Built-in ML anomaly jobs, entity analytics | Fusion ML (Microsoft-managed), UEBA | Behavioral analytics (Google-managed) | UBA (add-on), anomaly detection |
| **Hunting support** | Excellent (SPL flexibility, lookups, subsearch) | Good (EQL, KQL, Lucene, runtime fields) | Good (KQL, notebooks, bookmarks) | Excellent (retroactive rules, entity graph) | Moderate (AQL, reference sets) |
| **SOAR integration** | Splunk SOAR (native) | Elastic Agent response actions, third-party | Logic Apps, Sentinel Playbooks (native) | Chronicle SOAR (native) | QRadar SOAR (formerly Resilient) |
| **Multi-tenancy** | Splunk Cloud multi-tenant, search head clustering | Spaces, cross-cluster replication | Lighthouse, workspace-level isolation | Multi-tenant native | Domain-based segmentation |
| **Strengths** | SPL flexibility, mature ecosystem, huge TA library | Open-source core, EQL sequences, self-hosted option | Azure-native integration, Fusion correlation, Lighthouse | Unlimited ingestion pricing, retroactive detection, Google-scale | Offense chaining, network flow analysis |
| **Weaknesses** | Cost at scale (GB-based pricing), complex admin | Self-managed complexity, ML requires tuning | KQL learning curve, vendor lock-in to Azure | Limited customization, Google ecosystem dependency | Aging UI, complex upgrades, limited community |

**Selection criteria by conglomerate profile:**

| Profile | Recommended Primary | Rationale |
|---------|-------------------|-----------|
| Microsoft-centric estate (Azure AD, M365, Defender suite) | Microsoft Sentinel | Native data connector integration, Fusion correlation across Microsoft stack, Lighthouse for multi-tenant |
| Google Cloud / Chrome Enterprise | Google Chronicle | UDM alignment with GCP logs, retroactive detection, flat pricing at scale |
| Multi-cloud, cost-sensitive at high volume | Splunk (SmartStore + S3) or Chronicle | SmartStore reduces storage cost; Chronicle flat pricing eliminates volume anxiety |
| Small-medium enterprise, budget-constrained | Elastic Security (self-managed) | Open-source core, no license cost for detection rules engine |
| Regulated industry requiring on-premises SIEM | QRadar or Splunk Enterprise | On-premises deployment, compliance certifications, offline operation |

---

## 13. SOC Automation and Orchestration

The SOAR integration architecture and playbook design patterns in §3 establish the conceptual framework. This section provides implementation-level detail: concrete playbook code, API integration patterns for major SOAR platforms, ChatOps integration for SOC communication, and version-controlled playbook management.

### 13.1 SOAR Playbook Implementation Patterns

**Enrichment-first pattern (implementation).** The enrichment-first playbook (conceptual flow in §3.2) automates the context-gathering phase. Here is the implementation using Cortex XSOAR's YAML-based playbook definition:

```yaml
# xsoar-playbook: Phishing Triage - Enrichment First
id: phishing_triage_enrichment
version: 1
name: Phishing Triage - Enrichment First
starttaskid: "0"
tasks:
  "0":
    id: "0"
    taskid: extract_iocs
    type: regular
    task:
      script: ExtractIndicators
      args:
        text: ${incident.details}
    nexttasks:
      '#none#': ["1", "2", "3", "4"]
  "1":
    id: "1"
    taskid: vt_url_check
    type: regular
    task:
      script: VirusTotal|||url
      args:
        url: ${ExtractIndicators.URL}
    nexttasks:
      '#none#': ["5"]
  "2":
    id: "2"
    taskid: vt_hash_check
    type: regular
    task:
      script: VirusTotal|||file
      args:
        file: ${ExtractIndicators.File.SHA256}
    nexttasks:
      '#none#': ["5"]
  "3":
    id: "3"
    taskid: abuseipdb_check
    type: regular
    task:
      script: AbuseIPDB|||ip
      args:
        ip: ${ExtractIndicators.IP}
    nexttasks:
      '#none#': ["5"]
  "4":
    id: "4"
    taskid: whois_domain
    type: regular
    task:
      script: Whois|||domain
      args:
        domain: ${ExtractIndicators.Domain}
    nexttasks:
      '#none#': ["5"]
  "5":
    id: "5"
    taskid: score_and_decide
    type: condition
    task:
      script: CalculateRiskScore
      args:
        vt_url_score: ${VirusTotal.URL.Positives}
        vt_hash_score: ${VirusTotal.File.Positives}
        abuseipdb_score: ${AbuseIPDB.IP.AbuseConfidenceScore}
        domain_age_days: ${Whois.Domain.AgeDays}
    conditions:
      - label: "malicious"
        condition:
          - - operator: greaterThan
              left: { value: ${CalculateRiskScore.score} }
              right: { value: 70 }
        nexttaskid: "6"
      - label: "suspicious"
        condition:
          - - operator: greaterThan
              left: { value: ${CalculateRiskScore.score} }
              right: { value: 30 }
        nexttaskid: "7"
      - label: "benign"
        nexttaskid: "8"
  "6":
    id: "6"
    taskid: auto_respond_malicious
    type: playbook
    task:
      playbookId: phishing_containment
      # Quarantine email → block sender domain → block IOCs on firewall
      # → notify user → create incident ticket
  "7":
    id: "7"
    taskid: escalate_suspicious
    type: regular
    task:
      script: AssignToAnalyst
      args:
        tier: "T1"
        sla_minutes: 30
  "8":
    id: "8"
    taskid: close_benign
    type: regular
    task:
      script: CloseInvestigation
      args:
        reason: "Benign - automated enrichment found no indicators"
```

**Containment-first pattern: endpoint isolation playbook.**

This playbook prioritizes immediate containment (isolating the compromised endpoint) before enrichment, appropriate for high-confidence detections like confirmed ransomware or active C2.

```python
# Tines story: Endpoint Isolation Playbook
# Trigger: SIEM alert with severity=critical and category=malware

def endpoint_isolation_playbook(alert):
    """Containment-first: isolate immediately, then investigate."""

    host = alert['host_name']
    host_ip = alert['host_ip']
    alert_id = alert['alert_id']
    analyst_group = alert['assigned_group']

    # Step 1: Immediate containment via EDR API
    isolation_result = crowdstrike_api.contain_host(
        hostname=host,
        comment=f"Auto-isolated: alert {alert_id}"
    )

    if not isolation_result['success']:
        # Fallback: network-level isolation via firewall
        firewall_api.block_host(
            ip=host_ip,
            rule_name=f"emergency-isolate-{alert_id}",
            duration_hours=24
        )
        escalate_to_tier3(alert_id, "EDR isolation failed, firewall block applied")

    # Step 2: Create incident ticket
    ticket = servicenow_api.create_incident(
        short_description=f"Endpoint isolated: {host} - {alert['rule_name']}",
        description=build_incident_description(alert),
        urgency=1,
        impact=1,
        assignment_group=analyst_group,
        correlation_id=alert_id
    )

    # Step 3: Notify stakeholders
    slack_api.post_message(
        channel="#soc-incidents",
        text=f":rotating_light: *Endpoint Isolated*\n"
             f"Host: `{host}` ({host_ip})\n"
             f"Alert: {alert['rule_name']}\n"
             f"Ticket: {ticket['number']}\n"
             f"Isolated via: {'EDR' if isolation_result['success'] else 'Firewall'}"
    )

    # Step 4: Collect forensic data (post-isolation)
    crowdstrike_api.rtr_session(
        hostname=host,
        commands=[
            "runscript -CloudFile=CollectTriagePackage",
            "get C:\\Windows\\System32\\winevt\\Logs\\Security.evtx",
            "get C:\\Windows\\System32\\winevt\\Logs\\Microsoft-Windows-Sysmon%4Operational.evtx"
        ],
        output_path=f"/cases/{alert_id}/forensics/"
    )

    # Step 5: Manager notification for asset owner
    asset = cmdb_api.get_asset(hostname=host)
    email_api.send(
        to=asset['owner_email'],
        cc=asset['manager_email'],
        subject=f"Security Incident: Your device {host} has been isolated",
        body=render_template('endpoint_isolation_notice.html', alert=alert, ticket=ticket)
    )

    # Step 6: Auto-undo safeguard — if not confirmed in 4 hours, release
    schedule_task(
        delay_hours=4,
        task=check_isolation_confirmation,
        args={'alert_id': alert_id, 'host': host}
    )

    return {'ticket': ticket['number'], 'isolated': True}
```

**Identity compromise response playbook.**

```python
# Shuffle workflow: Identity Compromise Response
# Trigger: Alert for impossible travel, credential stuffing success, or MFA bypass

def identity_compromise_playbook(alert):
    """Immediate account lockdown followed by forensic audit."""

    username = alert['target_user']
    alert_id = alert['alert_id']

    # Step 1: Disable account (Azure AD / on-premises AD)
    if is_cloud_user(username):
        msgraph_api.disable_user(username)
        msgraph_api.revoke_all_sessions(username)
    else:
        ldap_api.disable_account(username)
        ldap_api.expire_password(username)

    # Step 2: Revoke active sessions across all SSO-integrated apps
    okta_api.clear_user_sessions(username)

    # Step 3: Revoke OAuth tokens and app passwords
    msgraph_api.revoke_app_passwords(username)
    msgraph_api.revoke_oauth_grants(username)

    # Step 4: Audit recent activity (30-day lookback)
    activity_report = {
        'logon_history': sentinel_api.query(f"""
            SigninLogs
            | where TimeGenerated > ago(30d)
            | where UserPrincipalName == '{username}'
            | project TimeGenerated, IPAddress, Location, AppDisplayName,
                      ResultType, ConditionalAccessStatus
            | order by TimeGenerated desc
        """),
        'mailbox_rules': msgraph_api.get_mailbox_rules(username),
        'inbox_forwarding': msgraph_api.get_inbox_forwarding(username),
        'mfa_changes': sentinel_api.query(f"""
            AuditLogs
            | where TimeGenerated > ago(30d)
            | where TargetResources has '{username}'
            | where OperationName has_any ('Update user', 'Reset password',
                'Register security info', 'Delete security info')
            | project TimeGenerated, OperationName, InitiatedBy, Result
        """),
        'file_access': msgraph_api.get_recent_file_activity(username, days=7)
    }

    # Step 5: Check for persistence mechanisms
    suspicious_rules = [r for r in activity_report['mailbox_rules']
                        if r.get('ForwardTo') or r.get('RedirectTo')
                        or r.get('DeleteMessage')]
    if suspicious_rules:
        for rule in suspicious_rules:
            msgraph_api.delete_mailbox_rule(username, rule['Id'])

    if activity_report['inbox_forwarding']:
        msgraph_api.remove_inbox_forwarding(username)

    # Step 6: Generate incident report and create ticket
    ticket = servicenow_api.create_incident(
        short_description=f"Identity compromise: {username}",
        description=render_incident_report(alert, activity_report),
        urgency=1,
        assignment_group="Identity Security"
    )

    # Step 7: Notify user's manager for credential reset coordination
    manager = msgraph_api.get_manager(username)
    teams_api.send_message(
        user=manager['userPrincipalName'],
        text=f"Your team member {username}'s account has been disabled "
             f"due to a security incident. IT Security will coordinate "
             f"credential reset. Ticket: {ticket['number']}"
    )

    return {
        'ticket': ticket['number'],
        'account_disabled': True,
        'sessions_revoked': True,
        'suspicious_rules_removed': len(suspicious_rules),
        'activity_report': activity_report
    }
```

### 13.2 ChatOps Integration for SOC

ChatOps bridges SOAR automation with analyst communication, enabling real-time alerting, investigation commands, and response actions directly from Slack or Microsoft Teams.

**Slack integration architecture:**

```python
# Slack bot for SOC operations
# Inbound: SOAR → Slack (alert notifications, status updates)
# Outbound: Slack → SOAR (analyst commands, response approvals)

# Alert notification with interactive buttons
def send_alert_to_slack(alert):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text",
                     "text": f"[{alert['severity'].upper()}] {alert['rule_name']}"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Host:* `{alert['host']}`"},
                {"type": "mrkdwn", "text": f"*User:* `{alert['user']}`"},
                {"type": "mrkdwn", "text": f"*ATT&CK:* {alert['mitre_technique']}"},
                {"type": "mrkdwn", "text": f"*Time:* {alert['timestamp']}"},
                {"type": "mrkdwn", "text": f"*Ticket:* {alert['ticket_url']}"},
                {"type": "mrkdwn", "text": f"*Risk Score:* {alert['risk_score']}/100"}
            ]
        },
        {
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "Acknowledge"},
                 "action_id": "ack_alert", "value": alert['id']},
                {"type": "button", "text": {"type": "plain_text", "text": "Isolate Host"},
                 "action_id": "isolate_host", "value": alert['host'],
                 "style": "danger",
                 "confirm": {"title": {"type": "plain_text", "text": "Confirm isolation"},
                            "text": {"type": "plain_text",
                                     "text": f"Isolate {alert['host']}? This blocks all network access."},
                            "confirm": {"type": "plain_text", "text": "Isolate"},
                            "deny": {"type": "plain_text", "text": "Cancel"}}},
                {"type": "button", "text": {"type": "plain_text", "text": "False Positive"},
                 "action_id": "mark_fp", "value": alert['id']}
            ]
        }
    ]
    slack_client.chat_postMessage(channel="#soc-alerts", blocks=blocks)
```

**Slash commands for analyst operations:**

```
/soc lookup ip 203.0.113.45
  → Returns: VirusTotal score, AbuseIPDB confidence, GreyNoise classification,
    Shodan open ports, internal TI match status

/soc lookup hash e3b0c44298fc1c149afbf4c8996fb924
  → Returns: VirusTotal detections, sandbox reports, MITRE ATT&CK mapping

/soc isolate WIN-FINANCE-03
  → Triggers: EDR isolation → ticket creation → manager notification
  → Requires: Confirmation button click in Slack

/soc block-ioc 203.0.113.45 --type ip --duration 30d --reason "C2 callback"
  → Pushes: IOC to firewall blocklist, EDR blocklist, and SIEM watchlist

/soc status incident INC0012345
  → Returns: Current assignee, status, timeline, related alerts, containment actions

/soc hunt "process.name:powershell.exe AND process.command_line:*encodedcommand*" --last 24h
  → Runs: SIEM hunt query, returns top 20 results in thread
```

### 13.3 Runbook-as-Code: Version-Controlled Playbooks

Treating SOAR playbooks as code enables the same engineering practices applied to detection rules: version control, peer review, automated testing, and CI/CD deployment.

**Repository structure:**

```
soar-playbooks/
├── playbooks/
│   ├── phishing/
│   │   ├── phishing_triage.yml
│   │   ├── phishing_containment.yml
│   │   └── tests/
│   │       ├── test_phishing_triage.py
│   │       └── fixtures/
│   │           ├── malicious_email.json
│   │           └── benign_email.json
│   ├── endpoint/
│   │   ├── endpoint_isolation.yml
│   │   ├── malware_remediation.yml
│   │   └── tests/
│   ├── identity/
│   │   ├── account_compromise.yml
│   │   ├── mfa_bypass_response.yml
│   │   └── tests/
│   └── network/
│       ├── c2_containment.yml
│       └── tests/
├── integrations/
│   ├── crowdstrike.py
│   ├── sentinel.py
│   ├── servicenow.py
│   └── slack.py
├── shared/
│   ├── enrichment.py
│   ├── risk_scoring.py
│   └── notification.py
├── .github/
│   └── workflows/
│       └── soar-ci.yml
└── deploy/
    ├── xsoar_deploy.py
    └── tines_deploy.py
```

**CI/CD pipeline for playbook deployment:**

```yaml
# .github/workflows/soar-ci.yml
name: SOAR Playbook CI/CD
on:
  push:
    paths: ['playbooks/**', 'integrations/**', 'shared/**']
  pull_request:
    paths: ['playbooks/**', 'integrations/**', 'shared/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements-dev.txt
      - name: YAML lint playbooks
        run: yamllint playbooks/
      - name: Validate playbook schema
        run: python scripts/validate_playbooks.py playbooks/
      - name: Type check integrations
        run: mypy integrations/ shared/

  test:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements-dev.txt
      - name: Run playbook unit tests
        run: pytest playbooks/ -v --tb=short
      - name: Run integration mock tests
        run: pytest integrations/ -v --tb=short -m "not live"

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to XSOAR
        run: python deploy/xsoar_deploy.py --server $XSOAR_URL --api-key $XSOAR_KEY
        env:
          XSOAR_URL: ${{ secrets.XSOAR_URL }}
          XSOAR_KEY: ${{ secrets.XSOAR_KEY }}
```

---

## 14. Metrics, Maturity, and Program Management

Sections §7 and §10.2 define the operational KPIs (MTTD, MTTR, alert-to-incident ratio, coverage percentages) and the team structure for detection engineering. This section addresses program-level maturity assessment, the operational cadence that drives continuous improvement, purple team integration as a feedback loop, and cost optimization for sustainable telemetry management.

### 14.1 Detection Maturity Model

Maturity assessment provides a structured framework for measuring the detection engineering program's current capability and defining a roadmap toward advanced capabilities.

| Level | Name | Capabilities | Telemetry | Detection Approach | Validation |
|-------|------|-------------|-----------|-------------------|------------|
| **0** | **Minimal** | Default vendor alerts, no custom rules, no tuning | Default SIEM data sources only | Out-of-the-box vendor rules, unmodified | None — no testing of detection efficacy |
| **1** | **Reactive** | Custom Sigma rules for known IOCs and specific incidents, basic tuning | Tier 1 log sources (§6) collected from >80% of endpoints | IOC-based detection, signature matching, basic threshold rules | Ad-hoc manual testing after rule deployment |
| **2** | **Procedural** | Detection-as-Code with CI/CD pipeline (§2), systematic tuning, exception management (§11.4) | Tier 1 + Tier 2 log sources, >95% collection coverage | Behavioral detection (command-line analysis, parent-child correlation), multi-event rules | Scheduled Atomic Red Team validation per technique, positive/negative test cases in CI |
| **3** | **Behavioral** | ML-based anomaly detection, UEBA integration, TI-driven detection development, ATT&CK coverage >60% of high-priority techniques | Full telemetry stack including cloud, identity, network flow, email | Behavioral analytics, statistical anomaly detection, entity risk scoring, correlation rules | Continuous BAS platform validation, automated regression testing, purple team exercises quarterly |
| **4** | **Proactive** | Dedicated threat hunting team, detection rules derived from hunt findings, predictive analytics, offensive security feedback loop, ATT&CK coverage >80% | Complete telemetry with custom instrumentation for emerging attack surfaces | Threat-intelligence-driven proactive rule development, hunt-derived detections, ML models trained on organization-specific baselines | Continuous purple team operations, red team findings drive detection sprints, detection gap SLA (<72h from gap identification to rule deployment) |

**Maturity assessment process:** Evaluate each dimension independently (telemetry coverage, detection methodology, validation rigor, operational process, team capability) and score 0–4. The overall maturity level is the minimum across all dimensions — a program cannot claim Level 3 if any dimension is below Level 3. Assessment should be performed annually with quarterly progress reviews.

### 14.2 Detection Engineering Sprint Cadence

Detection engineering operates on a cadence that balances proactive coverage expansion with reactive tuning and validation demands.

**Weekly rhythm:**

| Day | Activity | Owner |
|-----|----------|-------|
| Monday | Sprint planning: review detection backlog, prioritize new rules from TI reports, hunt findings, and gap analysis | Detection Engineering Lead |
| Tuesday–Thursday | Rule development, testing, and deployment via CI/CD pipeline | Detection Engineers |
| Thursday | FP review: process tuning tickets from SOC analysts, deploy exception updates | Detection Engineers |
| Friday | Rule release: merge approved rules to main branch, deploy to production, update coverage tracking | Detection Engineering Lead |

**Monthly rhythm:**

| Activity | Description | Output |
|----------|-------------|--------|
| Coverage review | Regenerate ATT&CK coverage heatmap, compare against previous month | Updated Navigator layer, gap list |
| Rule health audit | Identify rules with 0 triggers (possible telemetry gap or dead rule), rules with >70% FP rate, rules with expired exceptions | Tune/retire/redesign list |
| TI-to-detection pipeline review | Review TI reports from the past month, verify detection coverage for reported TTPs | New rule development backlog items |
| Metrics report | Compile metrics from §7 and §10.2, report to security leadership | Monthly detection engineering dashboard |

**Quarterly rhythm:**

| Activity | Description | Output |
|----------|-------------|--------|
| Gap assessment | Comprehensive ATT&CK gap analysis considering new techniques added by MITRE, changes in organizational risk profile, new subsidiaries onboarded | Prioritized gap remediation plan |
| Purple team exercise | Structured adversary simulation targeting identified gaps (§14.3) | Validated detections, new detection requirements |
| Maturity assessment | Score program against maturity model (§14.1) | Maturity scorecard, improvement roadmap |
| Detection library cleanup | Retire deprecated rules, consolidate overlapping rules, update metadata (references, severity, tags) | Leaner, higher-fidelity rule library |

### 14.3 Purple Team Integration Cycle

Purple teaming is not a point-in-time event — it is a continuous feedback loop between offensive simulation and defensive detection. The cycle integrates with the detection engineering sprint cadence:

```
┌─────────────────────────────────────────────────────────┐
│                  PURPLE TEAM CYCLE                       │
│                                                         │
│  1. SCOPE                                               │
│     ├── Select ATT&CK techniques from gap analysis      │
│     ├── Prioritize by organizational threat model        │
│     └── Define success criteria per technique            │
│                                                         │
│  2. SIMULATE                                            │
│     ├── Red team executes techniques in production       │
│     │   (with safeguards: time-boxed, documented,        │
│     │    rollback plan for each action)                  │
│     ├── Use Caldera/ART for repeatable automation        │
│     └── Log all execution timestamps and parameters      │
│                                                         │
│  3. EVALUATE                                            │
│     ├── Blue team reviews SIEM for detection triggers    │
│     ├── For each technique: detected / partial / missed  │
│     ├── Root-cause missed detections:                    │
│     │   ├── Missing telemetry (log source not collected) │
│     │   ├── Missing rule (no detection written)          │
│     │   ├── Rule logic error (rule exists but didn't     │
│     │   │   fire due to field mapping or threshold)      │
│     │   └── Evasion (technique variant not covered)      │
│     └── Document findings per technique                  │
│                                                         │
│  4. DEVELOP                                             │
│     ├── Write new Sigma rules for missed techniques      │
│     ├── Fix existing rules that failed to trigger        │
│     ├── Request new telemetry for coverage gaps          │
│     └── Add positive test cases from simulation data     │
│                                                         │
│  5. VALIDATE                                            │
│     ├── Re-run simulation for previously missed          │
│     │   techniques after rule deployment                 │
│     ├── Confirm detection triggers correctly             │
│     ├── Verify no regression in existing detections      │
│     └── Update ATT&CK coverage heatmap                  │
│                                                         │
│  6. REGRESS                                             │
│     ├── Add simulation to BAS platform for continuous    │
│     │   regression testing                               │
│     ├── Alert on detection regression (rule disabled,    │
│     │   telemetry stopped, or rule logic broken)         │
│     └── Feed back into next cycle's scope                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Detection gap SLA.** Mature detection engineering programs commit to a gap remediation SLA:

| Gap Source | SLA to Deployed Detection | Escalation |
|-----------|--------------------------|------------|
| Purple team exercise (missed technique) | 72 hours | Detection Engineering Lead if >72h |
| Active incident (attack technique without detection) | 24 hours | CISO if >24h |
| TI report (new technique by threat actor targeting org's sector) | 5 business days | Monthly review if backlog exceeds 10 items |
| Quarterly gap assessment | Next sprint cycle | Quarterly maturity review |

### 14.4 MITRE ATT&CK Coverage Heatmap Generation and Maintenance

The heatmap (introduced conceptually in §5.1) requires systematic maintenance as a living artifact. The generation pipeline in §5.1 produces the initial layer; the maintenance process ensures accuracy over time:

```bash
# Automated monthly heatmap regeneration
# Runs as a scheduled CI job on the 1st of each month

#!/usr/bin/env bash
set -euo pipefail

RULES_DIR="rules/"
OUTPUT_DIR="coverage/"
MONTH=$(date +%Y-%m)

# Step 1: Generate current coverage from rule tags
python scripts/generate_navigator_layer.py \
  --rules-dir "$RULES_DIR" \
  --output "$OUTPUT_DIR/coverage_${MONTH}.json" \
  --attack-version "15.1"

# Step 2: Generate validated-only coverage (rules with passing tests)
python scripts/generate_navigator_layer.py \
  --rules-dir "$RULES_DIR" \
  --output "$OUTPUT_DIR/validated_${MONTH}.json" \
  --attack-version "15.1" \
  --require-passing-tests

# Step 3: Generate delta from previous month
python scripts/coverage_delta.py \
  --current "$OUTPUT_DIR/coverage_${MONTH}.json" \
  --previous "$OUTPUT_DIR/coverage_$(date -d '1 month ago' +%Y-%m).json" \
  --output "$OUTPUT_DIR/delta_${MONTH}.json"

# Step 4: Publish to internal wiki and Slack
python scripts/publish_coverage.py \
  --layer "$OUTPUT_DIR/coverage_${MONTH}.json" \
  --delta "$OUTPUT_DIR/delta_${MONTH}.json" \
  --slack-channel "#detection-engineering" \
  --wiki-page "Detection Coverage - ${MONTH}"
```

### 14.5 Cost Optimization and Data Lifecycle Management

At conglomerate scale, SIEM cost is a significant budget line item. Log volume management directly impacts both detection capability and operational cost.

**Volume analysis and optimization:**

```spl
# Splunk: Identify top cost drivers by sourcetype
index=_internal source=*license_usage.log type=Usage
| stats sum(b) as bytes by st
| eval GB = round(bytes/1073741824, 2)
| sort -GB
| head 20
| table st, GB
```

```spl
# Splunk: Identify verbose log sources with low detection value
index=* earliest=-7d
| stats count as event_count, dc(sourcetype) as sourcetypes by index
| join index [
    | rest /services/saved/searches
    | where is_scheduled=1
    | rex field=search "index=(?<searched_index>\w+)"
    | stats count as rule_references by searched_index
    | rename searched_index as index]
| eval events_per_rule = event_count / max(rule_references, 1)
| where events_per_rule > 1000000
| table index, event_count, rule_references, events_per_rule
| sort -events_per_rule
```

**Tiering strategy by detection value:**

| Tier | Retention | Storage | Log Sources | Cost Optimization |
|------|-----------|---------|-------------|-------------------|
| **Hot** (0–7 days) | SSD/NVMe | High-performance indexes | All ingested data | None — detection requires full fidelity |
| **Warm** (7–90 days) | HDD/object-store cache | Cost-optimized indexes | All ingested data (compressed) | Enable Splunk SmartStore / Elastic frozen tier for auto-tiering |
| **Cold** (90 days–1 year) | Object storage (S3/GCS/Azure Blob) | Parquet/ORC format | All data for hunting and forensics | Aggressive compression, columnar format for efficient query |
| **Archive** (1–7 years) | Glacier/Archive storage | Compliance-only retention | Regulatory-required logs only | Minimal cost; restore on demand (hours) |

**Data reduction techniques (applied before ingestion):**

| Technique | Volume Reduction | Detection Impact | When to Apply |
|-----------|-----------------|------------------|---------------|
| Field filtering (remove non-essential fields) | 20–40% | Low — remove verbose metadata fields, keep detection-relevant fields | High-volume sources (DNS, proxy, firewall) |
| Event filtering (drop known-benign events at source) | 30–60% | Medium — risk of filtering future-relevant events | Only with documented allowlists reviewed quarterly |
| Aggregation (roll up repeated events into counts) | 50–80% | High — loses individual event detail | Only for statistical detections (not forensic use cases) |
| Sampling (ingest 1-in-N events) | Proportional to N | Very High — misses low-frequency attack signals | Never for security detection; acceptable for capacity planning metrics only |
| Route to data lake instead of SIEM | 0% SIEM ingestion | Varies — depends on data lake query capability | High-volume, low-detection-value sources that may be needed for hunting |

**Retention policy decision framework:**

```
For each log source:
  1. Is it required by regulation? (PCI: 1 year, HIPAA: 6 years, SOX: 7 years)
     → Retain for regulatory minimum in archive tier
  2. Is it referenced by active detection rules?
     → Retain in hot/warm tier for rule lookback window + 30 days buffer
  3. Is it used for threat hunting?
     → Retain in cold tier for hunting lookback window (typically 90–365 days)
  4. Is it used only for forensic investigation?
     → Retain in cold tier for mean time to discovery + investigation duration
       (industry average: 10 days discovery + 30 days investigation = 40 days minimum)
  5. None of the above?
     → Evaluate dropping from ingestion entirely (redirect to data lake if needed)
```

---

## Cross-References

- **Domain 9 Chapter 9A** — Network protocol fundamentals underlying network security monitoring and log generation
- **Domain 14 Chapter 14A** — Active Directory attack techniques — the attack behaviors that detection rules must identify; Sigma rules in that chapter are operationalized through the CI/CD pipeline described here
- **Domain 11 Chapter 11A** — Malware injection and C2 — the YARA rules and Sysmon detections referenced here are detailed at the technique level in Chapter 11A
- **Domain 11 Chapter 11B** — EDR evasion (ETW patching, AMSI bypass, NTDLL unhooking) — the counter-evasion approaches in §8 address these techniques
- **Domain 27 Chapter 27C** — Detection engineering fundamentals and SecOps — complementary chapter focusing on endpoint-level detection architecture
- **Domain 29 Chapter 29A** — Ransomware kill chain — detection requirements mapped to each phase of the ransomware deployment chain
- **Domain 30 Chapter 30A** — C2 framework detection — network and host detection signatures for major C2 frameworks
- **Domain 30 Chapter 30B** — Credential theft detection — authentication and directory monitoring requirements for credential attack detection
- **Domain 31 Chapter 31B** — Runtime security (eBPF, auditd) and zero trust architecture — the complementary defensive technologies that generate the telemetry consumed by these pipelines and enforce the architectural controls that reduce attack surface
