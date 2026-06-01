# Security Monitoring for Data Infrastructure and Databases

## Table of Contents

1. [Database Activity Monitoring (DAM)](#1-database-activity-monitoring-dam)
2. [Log Collection and Aggregation](#2-log-collection-and-aggregation)
3. [SIEM Rules for Data Threats](#3-siem-rules-for-data-threats)
4. [User Behavior Analytics (UBA) for Data](#4-user-behavior-analytics-uba-for-data)
5. [Data Pipeline Monitoring](#5-data-pipeline-monitoring)
6. [Cloud Database Monitoring](#6-cloud-database-monitoring)
7. [Real-Time Alerting and Response](#7-real-time-alerting-and-response)
8. [Threat Hunting in Data Systems](#8-threat-hunting-in-data-systems)
9. [Metrics and KPIs](#9-metrics-and-kpis)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Database Activity Monitoring (DAM)

### 1.1 Architecture Models

Database Activity Monitoring (DAM) provides continuous surveillance of database transactions, enforcing security policies and generating audit trails independent of native database logging. Three primary architectural approaches exist, each with distinct tradeoffs for visibility, performance overhead, and tamper resistance.

#### Agent-Based Monitoring

Agent-based DAM deploys lightweight software agents directly on database servers. These agents intercept queries at the operating system level by hooking into shared memory segments, intercepting system calls, or parsing local audit logs in real time.

**Architecture:**

```
┌─────────────────────────────────────────────┐
│            Database Server                   │
│  ┌──────────┐    ┌──────────────────────┐   │
│  │ DB Engine │◄──►│ DAM Agent (kernel/   │   │
│  │           │    │ userspace hook)      │   │
│  └──────────┘    └──────────┬───────────┘   │
│                              │               │
└──────────────────────────────┼───────────────┘
                               │ Encrypted channel
                               ▼
                    ┌──────────────────────┐
                    │  DAM Management      │
                    │  Console / SIEM      │
                    └──────────────────────┘
```

**Advantages:**
- Captures local connections (socket, shared memory) invisible to network sniffers
- Sees decrypted traffic regardless of TLS configuration
- Can capture OS-level context (process ID, parent process, user mapping)
- Works in encrypted-at-rest environments without key access

**Disadvantages:**
- Performance overhead (typically 2-5% CPU, can spike during bulk operations)
- Requires deployment and maintenance on every database server
- Agent crashes can impact database availability depending on integration depth
- Kernel-mode agents introduce stability risk and require root/SYSTEM privileges

**Evasion considerations:** An attacker with root access can disable or tamper with the agent. Defense-in-depth requires agent integrity monitoring (file integrity monitoring on agent binaries, heartbeat monitoring from the management console, and OS-level protection via mandatory access controls like SELinux/AppArmor).

#### Network Sniffing (Passive Monitoring)

Network-based DAM captures database protocol traffic via port mirroring (SPAN), network TAPs, or inline proxies. The system decodes database wire protocols (TDS for SQL Server, TNS for Oracle, PostgreSQL wire protocol, MySQL client protocol) to extract queries, responses, and metadata.

**Architecture:**

```
┌────────┐         ┌──────────────┐         ┌───────────┐
│ Client │────────►│  Network     │────────►│ Database  │
│        │◄────────│  TAP/SPAN    │◄────────│ Server    │
└────────┘         └──────┬───────┘         └───────────┘
                          │ Mirror port
                          ▼
                   ┌──────────────┐
                   │ DAM Appliance│
                   │ (Protocol    │
                   │  Decoder)    │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ SIEM / Alert │
                   │ Console      │
                   └──────────────┘
```

**Advantages:**
- Zero performance impact on the database server
- No software deployment on production systems
- Tamper-resistant (separate infrastructure from monitored system)
- Captures all network-based connections including application pool queries

**Disadvantages:**
- Cannot see local/socket connections (common for application servers co-located with databases)
- TLS encryption blinds the sniffer unless TLS termination is upstream or keys are shared
- High-bandwidth environments may drop packets without adequate capture hardware
- Cannot correlate to OS-level identity (only sees database authentication)

**Evasion considerations:** Attackers using local connections (Unix domain sockets, shared memory IPC, localhost connections) bypass network monitoring entirely. TLS with certificate pinning prevents passive decryption. Stored procedures that execute dynamically constructed SQL may appear benign at the network layer while performing malicious operations internally.

#### Native Audit Facilities

Every major RDBMS includes built-in audit logging capabilities. These produce audit records within the database engine itself, using the database's own understanding of operations.

**PostgreSQL:** `pgAudit` extension provides detailed session and object audit logging beyond the basic `log_statement` parameter.

**MySQL:** Enterprise Audit Plugin (commercial) or `audit_log` (MariaDB), plus the open-source `server_audit` plugin for MariaDB.

**SQL Server:** SQL Server Audit (file-based XEL targets), Extended Events, C2 Audit Mode, and Common Criteria compliance mode.

**Oracle:** Unified Audit (12c+), Fine-Grained Auditing (FGA), and traditional audit trail.

**MongoDB:** Native audit log (Enterprise) writing JSON-formatted audit events.

**Advantages:**
- Deepest visibility into database internals (sees operations invisible to network/OS layers)
- Understands execution context (effective permissions, row-level access, view expansion)
- No additional infrastructure for basic deployment
- Captures all access paths without exception

**Disadvantages:**
- Performance impact on the database engine (5-15% for comprehensive auditing)
- Audit logs stored locally are vulnerable to tampering by DBAs
- Each engine has different formats, requiring normalization for centralized monitoring
- Storage growth can be substantial (audit logs often exceed data volume in write-heavy systems)

**Evasion considerations:** DBAs with sufficient privileges can disable auditing, truncate audit tables, or modify audit configurations. Critical defense: ship audit logs off-server in real time (sub-second) and alert on audit configuration changes. Separation of duties ensures no single account can both access data AND modify audit settings.

### 1.2 Commercial DAM Solutions

#### Imperva SecureSphere (now Imperva Data Security)

Imperva SecureSphere combines agent-based and network monitoring with a centralized management console. Key capabilities:

- **Discovery and classification:** Automatically discovers database instances, classifies sensitive data (PII, PCI, PHI) using regex and ML patterns
- **Real-time policy enforcement:** Can block queries in inline mode (acting as a database firewall)
- **User rights management:** Maps effective permissions and identifies excessive privileges
- **Compliance reporting:** Pre-built templates for PCI DSS (Req 10), HIPAA, SOX, GDPR
- **Dynamic profiling:** Learns normal query patterns and alerts on deviations

Deployment architecture typically uses a combination of DAM gateways (network monitoring) and DAM agents, reporting to a central MX management server. Scales to thousands of database instances via a hierarchical gateway topology.

#### IBM Guardium (IBM Security Guardium Data Protection)

IBM Guardium focuses on enterprise-scale database activity monitoring with strong compliance automation:

- **S-TAP agents:** Lightweight Software TAP agents installed on database servers, capturing traffic at the OS level with minimal overhead (claimed <5%)
- **Collector appliances:** Dedicated hardware or virtual appliances that receive, analyze, and store audit data
- **Central Manager:** Aggregates data from multiple collectors, provides unified policy management
- **Vulnerability Assessment:** Scans database configurations against CIS benchmarks and vendor hardening guides
- **Entitlement Reports:** Maps user privileges across heterogeneous database environments
- **Data-level access control:** Fine-grained policies based on user, SQL operation, object, time, and connection source
- **Outlier detection:** Built-in UBA capabilities for identifying anomalous database access patterns

Guardium supports 20+ database platforms and can monitor big data environments (Hadoop, MongoDB, Cassandra) alongside traditional RDBMS.

#### Oracle Audit Vault and Database Firewall (AVDF)

Oracle AVDF integrates native audit collection with network-based SQL traffic analysis:

- **Audit Vault Server:** Consolidates audit data from Oracle, SQL Server, MySQL, PostgreSQL, and OS audit trails (Linux auditd, Windows Event Log)
- **Database Firewall:** Inline SQL analysis with whitelist/blacklist enforcement. Parses SQL grammar to detect injection patterns, policy violations, and anomalous queries
- **Stored Procedure Auditing:** Tracks execution of stored procedures including dynamic SQL within them
- **Oracle-specific deep integration:** Leverages Oracle's Unified Audit, Real Application Security, and Database Vault for layered defense
- **High Availability:** Active-passive failover for the Audit Vault Server, resilient audit trail collection

### 1.3 Open-Source DAM Alternatives

#### pgAudit + ELK Stack

For PostgreSQL environments, pgAudit provides detailed audit logging that feeds into an ELK (Elasticsearch, Logstash, Kibana) or OpenSearch stack:

**pgAudit configuration** (`postgresql.conf`):

```ini
shared_preload_libraries = 'pgaudit'
pgaudit.log = 'all'
pgaudit.log_catalog = on
pgaudit.log_client = on
pgaudit.log_parameter = on
pgaudit.log_relation = on
pgaudit.log_statement_once = off
pgaudit.role = 'auditor'
```

**Granular object-level auditing** (per-table monitoring):

```sql
-- Create audit role
CREATE ROLE auditor NOLOGIN;

-- Grant audit monitoring on sensitive tables
GRANT SELECT, INSERT, UPDATE, DELETE ON customers TO auditor;
GRANT SELECT ON financial_transactions TO auditor;

-- pgAudit will now log all access to these tables by any user
```

**Filebeat configuration** for shipping PostgreSQL logs:

```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/postgresql/postgresql-*.log
    multiline.pattern: '^\d{4}-\d{2}-\d{2}'
    multiline.negate: true
    multiline.match: after
    fields:
      log_type: postgresql_audit
    processors:
      - dissect:
          tokenizer: "%{timestamp} %{timezone} [%{pid}] %{user}@%{database} %{level}:  %{message}"
          field: "message"
          target_prefix: "pg"

output.elasticsearch:
  hosts: ["https://elasticsearch:9200"]
  index: "pgaudit-%{+yyyy.MM.dd}"
  ssl.certificate_authorities: ["/etc/pki/ca.pem"]
```

#### MySQL Enterprise Audit + Wazuh

Wazuh provides host-based intrusion detection with native MySQL audit log parsing:

**MySQL Audit Plugin configuration** (`my.cnf`):

```ini
[mysqld]
plugin-load-add = audit_log.so
audit_log_format = JSON
audit_log_policy = ALL
audit_log_rotate_on_size = 100M
audit_log_file = /var/log/mysql/audit.log
audit_log_include_accounts = ''
audit_log_exclude_accounts = 'healthcheck@localhost'
```

**Wazuh decoder** for MySQL audit JSON:

```xml
<decoder name="mysql-audit">
  <program_name>mysql-audit</program_name>
  <prematch type="pcre2">"class":\s*"</prematch>
</decoder>

<decoder name="mysql-audit-fields">
  <parent>mysql-audit</parent>
  <regex type="pcre2">"account":\s*\{\s*"user":\s*"(\S+)",\s*"host":\s*"(\S+)"</regex>
  <order>user, srcip</order>
</decoder>
```

**Wazuh rules** for MySQL security events:

```xml
<group name="mysql-audit,">
  <rule id="100200" level="10">
    <decoded_as>mysql-audit</decoded_as>
    <field name="class">connection</field>
    <field name="status">1045</field>
    <description>MySQL: Authentication failure</description>
  </rule>

  <rule id="100201" level="12">
    <decoded_as>mysql-audit</decoded_as>
    <field name="class">general</field>
    <match>GRANT ALL</match>
    <description>MySQL: GRANT ALL PRIVILEGES issued</description>
  </rule>

  <rule id="100202" level="14" frequency="5" timeframe="60">
    <if_matched_sid>100200</if_matched_sid>
    <same_source_ip/>
    <description>MySQL: Brute force authentication attack</description>
  </rule>
</group>
```

### 1.4 Monitoring Scope

A comprehensive DAM deployment must cover these SQL operation categories:

| Category | Operations | Security Relevance |
|----------|-----------|-------------------|
| **DDL** | CREATE, ALTER, DROP, TRUNCATE, RENAME | Schema modification, data destruction |
| **DML** | SELECT, INSERT, UPDATE, DELETE, MERGE | Data access, modification, exfiltration |
| **DCL** | GRANT, REVOKE, DENY | Privilege escalation, access provisioning |
| **TCL** | COMMIT, ROLLBACK, SAVEPOINT | Transaction manipulation |
| **Authentication** | Login success/failure, password changes | Credential attacks, account compromise |
| **Administrative** | BACKUP, RESTORE, SHUTDOWN, REPLICATION | Data theft via backup, service disruption |
| **Configuration** | Parameter changes, plugin loading | Security control bypass |

---

## 2. Log Collection and Aggregation

### 2.1 Database Log Types by Engine

#### PostgreSQL Logging

PostgreSQL produces multiple log streams, each serving different monitoring purposes:

**pg_log (standard error log):**
- Controlled by `log_destination` (stderr, csvlog, syslog, jsonlog in PG15+)
- `log_statement = 'all'` captures every SQL statement (heavy, use selectively in production)
- `log_min_duration_statement = 1000` logs queries exceeding 1 second (performance + anomaly detection)
- `log_connections = on` and `log_disconnections = on` for session tracking
- `log_line_prefix` should include `%t %p %u %d %h` (timestamp, PID, user, database, host)

**csvlog format** (structured, machine-parseable):
```
log_destination = 'csvlog'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_file_mode = 0600
log_rotation_age = 1h
log_rotation_size = 100MB
```

CSV columns: `log_time, user_name, database_name, process_id, connection_from, session_id, session_line_num, command_tag, session_start_time, virtual_transaction_id, transaction_id, error_severity, sql_state_code, message, detail, hint, internal_query, internal_query_pos, context, query, query_pos, location, application_name, backend_type, leader_pid, query_id`

**pgAudit log entries** (appended to standard log with `AUDIT:` prefix):
```
2024-03-15 10:23:45.123 UTC [12345] user1@production AUDIT: SESSION,1,1,READ,SELECT,TABLE,public.customers,"SELECT * FROM customers WHERE id = 42",<not logged>
```

**pg_stat_statements** (query performance statistics, useful for baseline building):
```sql
SELECT userid, dbid, query, calls, total_exec_time, rows,
       shared_blks_hit, shared_blks_read
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 50;
```

#### MySQL Logging

MySQL provides several log types with distinct security monitoring value:

**Error Log:** Server startup/shutdown, critical errors, aborted connections. Essential for detecting service disruption attacks and connection anomalies.

**General Query Log:** Records every client connection and SQL statement. Extremely verbose; use selectively or only during incident investigation.
```ini
general_log = ON
general_log_file = /var/log/mysql/general.log
```

**Slow Query Log:** Queries exceeding `long_query_time`. Security use: detecting data exfiltration via large scans.
```ini
slow_query_log = ON
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
log_queries_not_using_indexes = ON
```

**Binary Log (binlog):** Records all data modification statements in replication-ready format. Critical for forensic reconstruction of data changes.
```ini
log_bin = /var/log/mysql/binlog
binlog_format = ROW
binlog_row_image = FULL
expire_logs_days = 30
```

**Audit Log (Enterprise or Plugin):** Structured audit trail with filtering capabilities. JSON format preferred for SIEM ingestion.

#### SQL Server Logging

**Error Log:** Stored in `ERRORLOG` files (cycled on restart, configurable rotation). Contains authentication failures, severity 16+ errors, and configuration changes.

**Extended Events (XEL files):** The modern, low-overhead event collection system:
```sql
CREATE EVENT SESSION [SecurityAudit] ON SERVER
ADD EVENT sqlserver.login_failed(
    ACTION(sqlserver.client_hostname, sqlserver.client_app_name, sqlserver.server_principal_name)
),
ADD EVENT sqlserver.database_permission_change(
    ACTION(sqlserver.server_principal_name, sqlserver.database_name)
),
ADD EVENT sqlserver.schema_object_access_group(
    ACTION(sqlserver.server_principal_name, sqlserver.database_name, sqlserver.sql_text)
    WHERE sqlserver.database_name = N'Production'
)
ADD TARGET package0.event_file(
    SET filename = N'/var/opt/mssql/audit/security_audit.xel',
    max_file_size = 100,
    max_rollover_files = 10
)
WITH (MAX_DISPATCH_LATENCY = 5 SECONDS, TRACK_CAUSALITY = ON);
```

**SQL Server Audit:** Built on Extended Events, provides GRANT/REVOKE/DENY tracking, object access auditing, and compliance-oriented output.

#### MongoDB Logging

**Profiler (performance/query logging):**
```javascript
db.setProfilingLevel(2, { slowms: 100 }); // Level 2 = all operations
// Documents written to system.profile collection
db.system.profile.find({ op: "query", ns: "production.customers" }).sort({ ts: -1 });
```

**Audit Log (Enterprise):**
```yaml
# mongod.conf
auditLog:
  destination: file
  format: JSON
  path: /var/log/mongodb/audit.json
  filter: '{ atype: { $in: ["authenticate", "createUser", "dropDatabase", "createCollection", "dropCollection", "authCheck"] } }'
```

Audit events include: `authenticate`, `createUser`, `dropUser`, `updateUser`, `grantRolesToUser`, `revokeRolesFromUser`, `createDatabase`, `dropDatabase`, `createCollection`, `dropCollection`, `authCheck` (every authorization check).

### 2.2 Log Shipping Methods

#### Syslog (rsyslog/syslog-ng)

Traditional approach for Unix-based systems. Databases that support syslog output (PostgreSQL's `log_destination = 'syslog'`) can ship directly:

```
# rsyslog.conf - Forward PostgreSQL logs to central SIEM
local0.*    @@siem.internal:514    # TCP
local0.*    @siem.internal:514     # UDP (unreliable, avoid)

# TLS-encrypted syslog (rsyslog with gtls module)
$DefaultNetstreamDriver gtls
$ActionSendStreamDriverMode 1
$ActionSendStreamDriverAuthMode x509/name
local0.*    @@(o)siem.internal:6514
```

#### Filebeat

Elastic's lightweight log shipper with native support for many database log formats:

```yaml
filebeat.inputs:
  - type: filestream
    id: postgresql-audit
    paths:
      - /var/log/postgresql/postgresql-*.csv
    parsers:
      - multiline:
          type: pattern
          pattern: '^\d{4}-\d{2}-\d{2}'
          negate: true
          match: after
    processors:
      - decode_csv_fields:
          fields:
            message: ['timestamp','user','database','pid','connection_from',
                      'session_id','line_num','command_tag','session_start',
                      'virtual_txn','txn_id','severity','sqlstate','message',
                      'detail','hint','internal_query','internal_pos',
                      'context','query','query_pos','location','app_name']
          separator: ","
          trim_leading_space: true

  - type: filestream
    id: mysql-audit
    paths:
      - /var/log/mysql/audit.log
    parsers:
      - ndjson:
          target: "mysql_audit"
          add_error_key: true

output.elasticsearch:
  hosts: ["https://es-cluster:9200"]
  indices:
    - index: "db-audit-pg-%{+yyyy.MM.dd}"
      when.equals:
        fields.log_type: "postgresql"
    - index: "db-audit-mysql-%{+yyyy.MM.dd}"
      when.equals:
        fields.log_type: "mysql"
```

#### Fluentd

Fluentd provides plugin-based log collection with strong filtering and routing:

```xml
<source>
  @type tail
  path /var/log/postgresql/postgresql-*.log
  pos_file /var/run/fluentd/pg_audit.pos
  tag db.postgresql.audit
  <parse>
    @type regexp
    expression /^(?<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \w+) \[(?<pid>\d+)\] (?<user>\S+)@(?<database>\S+) (?<severity>\w+):\s+(?<message>.*)/
    time_key timestamp
    time_format %Y-%m-%d %H:%M:%S.%L %Z
  </parse>
</source>

<filter db.postgresql.audit>
  @type grep
  <regexp>
    key message
    pattern /AUDIT:/
  </regexp>
</filter>

<match db.**>
  @type elasticsearch
  host elasticsearch.internal
  port 9200
  index_name db-audit
  type_name _doc
  <buffer>
    @type file
    path /var/log/fluentd/buffer/db-audit
    flush_interval 5s
    retry_max_interval 30
    chunk_limit_size 8M
  </buffer>
</match>
```

#### Vector (by Datadog, open-source)

Vector is a high-performance observability pipeline written in Rust, suitable for high-volume database log shipping:

```toml
[sources.pg_audit]
type = "file"
include = ["/var/log/postgresql/postgresql-*.csv"]
read_from = "beginning"
fingerprint.strategy = "device_and_inode"

[transforms.parse_pg_csv]
type = "remap"
inputs = ["pg_audit"]
source = '''
. = parse_csv!(.message)
.timestamp = parse_timestamp!(.timestamp, format: "%Y-%m-%d %H:%M:%S.%3f %Z")
.severity = to_string!(.severity)
.is_audit = contains(to_string!(.message), "AUDIT:")
'''

[transforms.filter_security]
type = "filter"
inputs = ["parse_pg_csv"]
condition = '.is_audit == true || .severity == "ERROR" || .severity == "FATAL"'

[sinks.elasticsearch]
type = "elasticsearch"
inputs = ["filter_security"]
endpoints = ["https://elasticsearch:9200"]
bulk.index = "db-audit-{{ .database }}-%Y-%m-%d"
tls.ca_file = "/etc/pki/ca.pem"
auth.strategy = "basic"
auth.user = "vector"
auth.password = "${ES_PASSWORD}"
```

### 2.3 Centralization Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Database Fleet                                   │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │PostgreSQL │  │  MySQL   │  │SQL Server │  │ MongoDB  │              │
│  │+ pgAudit  │  │+ Audit   │  │+ XEvents  │  │+ Audit   │              │
│  └─────┬────┘  └────┬─────┘  └────┬──────┘  └────┬─────┘              │
│        │             │              │              │                      │
│  ┌─────▼────┐  ┌────▼─────┐  ┌────▼──────┐  ┌────▼─────┐              │
│  │ Filebeat  │  │ Filebeat │  │ Filebeat  │  │ Filebeat │              │
│  │ Agent     │  │ Agent    │  │ Agent     │  │ Agent    │              │
│  └─────┬────┘  └────┬─────┘  └────┬──────┘  └────┬─────┘              │
└────────┼─────────────┼──────────────┼──────────────┼────────────────────┘
         │             │              │              │
         └─────────────┼──────────────┼──────────────┘
                       │              │
                       ▼              ▼
              ┌─────────────────────────────┐
              │     Kafka / Redis Streams    │   ← Buffer layer
              │     (message queue)          │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌──────────────┐ ┌────────────┐ ┌────────────┐
    │Elasticsearch │ │  Splunk    │ │ S3/GCS     │
    │ (Hot/Warm)   │ │  Indexers  │ │ (Cold/     │
    │              │ │            │ │  Archive)  │
    └──────────────┘ └────────────┘ └────────────┘
```

### 2.4 Retention Strategies

| Tier | Storage | Retention | Use Case |
|------|---------|-----------|----------|
| Hot | Elasticsearch/Splunk (SSD) | 7-30 days | Active investigation, real-time alerting |
| Warm | Elasticsearch (HDD) | 30-90 days | Incident response, compliance queries |
| Cold | Object storage (S3/GCS) | 1-7 years | Regulatory compliance (PCI: 1yr, HIPAA: 6yr, SOX: 7yr) |
| Frozen | Glacier/Archive | 7+ years | Legal hold, regulatory investigation |

**Immutability controls:** Use WORM (Write Once Read Many) storage for compliance. S3 Object Lock, Azure Immutable Blob Storage, or GCS retention policies ensure logs cannot be tampered with post-collection.

---

## 3. SIEM Rules for Data Threats

### 3.1 Mass Data Retrieval Detection

**Sigma Rule:**

```yaml
title: Mass Data Retrieval from Database
id: 8a3b2c1d-4e5f-6789-abcd-ef0123456789
status: experimental
description: Detects queries returning an abnormally large number of rows
logsource:
  product: postgresql
  service: pgaudit
detection:
  selection:
    event_type: 'AUDIT'
    command_tag: 'SELECT'
  filter_rows:
    rows_returned|gte: 10000
  filter_normal_etl:
    user_name|contains:
      - 'etl_'
      - 'reporting_'
      - 'airflow'
  condition: selection and filter_rows and not filter_normal_etl
level: high
tags:
  - attack.collection
  - attack.t1005
  - attack.exfiltration
  - attack.t1048
```

**Splunk SPL:**

```spl
index=db_audit sourcetype=pgaudit command_tag=SELECT rows_returned>10000
| where NOT match(user_name, "^(etl_|reporting_|airflow)")
| stats count as query_count, sum(rows_returned) as total_rows,
        values(query) as queries by user_name, database_name, src_ip
| where total_rows > 100000 OR query_count > 20
| sort -total_rows
```

### 3.2 Schema Modification Detection

**Sigma Rule:**

```yaml
title: Unauthorized Schema Modification
id: 9b4c3d2e-5f60-7890-bcde-f01234567890
status: stable
description: Detects DDL operations by non-DBA users or outside maintenance windows
logsource:
  product: database
  service: audit
detection:
  selection_ddl:
    command_tag|contains:
      - 'CREATE'
      - 'ALTER'
      - 'DROP'
      - 'TRUNCATE'
  filter_authorized:
    user_name|contains:
      - 'dba_'
      - 'migration_'
      - 'liquibase'
      - 'flyway'
  filter_maintenance_window:
    timestamp|gte: '02:00:00'
    timestamp|lte: '06:00:00'
  condition: selection_ddl and not (filter_authorized or filter_maintenance_window)
level: critical
```

**Splunk SPL:**

```spl
index=db_audit (command_tag=CREATE OR command_tag=ALTER OR command_tag=DROP OR command_tag=TRUNCATE)
| where NOT match(user_name, "(dba_|migration_|liquibase|flyway)")
| eval hour=strftime(_time, "%H")
| where NOT (hour >= 2 AND hour <= 6)
| table _time, user_name, database_name, command_tag, query, src_ip
| sort -_time
```

### 3.3 Privilege Escalation Detection

**Sigma Rule:**

```yaml
title: Database Privilege Escalation
id: ac5d4e3f-6071-8901-cdef-012345678901
status: stable
description: Detects GRANT operations that assign elevated privileges
logsource:
  product: database
  service: audit
detection:
  selection_grant:
    command_tag: 'GRANT'
  selection_dangerous_privs:
    query|contains:
      - 'ALL PRIVILEGES'
      - 'SUPERUSER'
      - 'CREATEROLE'
      - 'CREATEDB'
      - 'pg_execute_server_program'
      - 'pg_read_server_files'
      - 'pg_write_server_files'
      - 'WITH GRANT OPTION'
      - 'DBA'
      - 'SYSADMIN'
      - 'SECURITYADMIN'
  condition: selection_grant and selection_dangerous_privs
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1078.004
```

**Splunk SPL:**

```spl
index=db_audit command_tag=GRANT
| where match(query, "(?i)(ALL PRIVILEGES|SUPERUSER|CREATEROLE|SYSADMIN|SECURITYADMIN|WITH GRANT OPTION|pg_execute_server_program|pg_read_server_files)")
| eval risk_score = case(
    match(query, "(?i)SUPERUSER|SYSADMIN"), 100,
    match(query, "(?i)ALL PRIVILEGES"), 90,
    match(query, "(?i)pg_execute_server_program|pg_read_server_files"), 85,
    match(query, "(?i)WITH GRANT OPTION"), 80,
    1=1, 70
)
| table _time, user_name, query, database_name, src_ip, risk_score
| sort -risk_score
```

### 3.4 Brute Force Authentication Detection

**Sigma Rule:**

```yaml
title: Database Brute Force Authentication
id: bd6e5f40-7182-9012-def0-123456789012
status: stable
description: Detects multiple authentication failures from a single source
logsource:
  product: database
  service: auth
detection:
  selection:
    event_type: 'authentication_failure'
  condition: selection | count() by src_ip > 10
  timeframe: 5m
level: high
tags:
  - attack.credential_access
  - attack.t1110.001
```

**Splunk SPL:**

```spl
index=db_audit (event_type=authentication_failure OR error_severity=FATAL sqlstate=28P01)
| bin _time span=5m
| stats count as failures, dc(user_name) as targeted_users,
        values(user_name) as attempted_users by src_ip, _time, database_name
| where failures > 10
| eval severity = case(
    failures > 50 AND targeted_users > 5, "critical",
    failures > 20, "high",
    1=1, "medium"
)
| sort -failures
```

### 3.5 Impossible Travel Detection

**Splunk SPL:**

```spl
index=db_audit event_type=authentication_success
| iplocation src_ip
| sort user_name, _time
| streamstats current=f window=1 last(City) as prev_city, last(lat) as prev_lat,
              last(lon) as prev_lon, last(_time) as prev_time by user_name
| eval distance_km = round(3959 * acos(sin(lat*pi()/180) * sin(prev_lat*pi()/180) +
       cos(lat*pi()/180) * cos(prev_lat*pi()/180) * cos((lon-prev_lon)*pi()/180)) * 1.609, 0)
| eval time_diff_hours = round((_time - prev_time) / 3600, 2)
| eval max_speed_kmh = if(time_diff_hours > 0, distance_km / time_diff_hours, 0)
| where max_speed_kmh > 900 AND distance_km > 500
| table _time, user_name, prev_city, City, distance_km, time_diff_hours, max_speed_kmh, src_ip
```

### 3.6 Off-Hours Access Detection

**Sigma Rule:**

```yaml
title: Database Access Outside Business Hours
id: ce7f6051-8293-0123-ef01-234567890123
status: experimental
description: Detects database access outside defined business hours for non-service accounts
logsource:
  product: database
  service: audit
detection:
  selection:
    event_type: 'session_start'
  filter_service_accounts:
    user_name|contains:
      - 'svc_'
      - 'app_'
      - 'etl_'
      - 'monitoring_'
  filter_business_hours:
    timestamp|gte: '08:00:00'
    timestamp|lte: '20:00:00'
  condition: selection and not filter_service_accounts and not filter_business_hours
level: medium
```

**Splunk SPL:**

```spl
index=db_audit event_type=session_start
| where NOT match(user_name, "^(svc_|app_|etl_|monitoring_|cron_)")
| eval hour = tonumber(strftime(_time, "%H")), dow = tonumber(strftime(_time, "%w"))
| where (hour < 8 OR hour > 20) OR (dow == 0 OR dow == 6)
| eval access_type = case(
    dow == 0 OR dow == 6, "weekend",
    hour < 6 OR hour > 22, "late_night",
    1=1, "off_hours"
)
| stats count by user_name, database_name, access_type, src_ip
| where count > 3
| sort -count
```

### 3.7 New User Creation Detection

**Splunk SPL:**

```spl
index=db_audit (command_tag="CREATE ROLE" OR command_tag="CREATE USER" OR command_tag="CREATE LOGIN")
| eval is_authorized_creator = if(match(user_name, "(dba_|admin_|iam_sync)"), 1, 0)
| eval has_dangerous_privs = if(match(query, "(?i)(SUPERUSER|CREATEDB|CREATEROLE|LOGIN|SYSADMIN)"), 1, 0)
| where is_authorized_creator == 0 OR has_dangerous_privs == 1
| table _time, user_name, query, database_name, src_ip, is_authorized_creator, has_dangerous_privs
| sort -_time
```

### 3.8 Backup Export Anomaly Detection

**Splunk SPL:**

```spl
index=db_audit (command_tag="COPY" OR query="*pg_dump*" OR query="*mysqldump*" OR
               query="*BACKUP DATABASE*" OR query="*INTO OUTFILE*" OR
               query="*INTO DUMPFILE*" OR command_tag="BACKUP")
| where NOT match(user_name, "(backup_|dba_|scheduled_)")
| eval hour = tonumber(strftime(_time, "%H"))
| eval risk_score = case(
    match(query, "(?i)INTO OUTFILE|INTO DUMPFILE|COPY.*TO"), 90,
    hour < 6 OR hour > 22, 80,
    match(query, "(?i)pg_dump|mysqldump"), 70,
    1=1, 50
)
| where risk_score >= 70
| table _time, user_name, query, database_name, src_ip, risk_score
| sort -risk_score
```

---

## 4. User Behavior Analytics (UBA) for Data

### 4.1 Baseline Establishment

Effective UBA requires a comprehensive behavioral baseline built from 30-90 days of normal operation. The baseline captures multiple dimensions of user activity:

**Query Pattern Profiling:**

| Dimension | Baseline Metrics | Anomaly Threshold |
|-----------|-----------------|-------------------|
| Query volume | Queries/hour per user | >3 standard deviations from mean |
| Data volume | Rows accessed/hour | >2 standard deviations |
| Table access | Distinct tables accessed per session | New table not accessed in 30 days |
| Query complexity | Average query length, JOIN count | Sudden increase in complexity |
| Time-of-day | Activity distribution by hour | Activity in previously dormant hours |
| Session duration | Average session length | >3x normal duration |
| Error rate | Authentication failures, permission denials | Sudden spike in errors |

**Baseline SQL for PostgreSQL** (collecting metrics into a profiling table):

```sql
-- Create baseline statistics table
CREATE TABLE security.user_baseline AS
SELECT
    usename AS user_name,
    date_trunc('hour', query_start) AS hour_bucket,
    count(*) AS query_count,
    count(DISTINCT datname) AS db_count,
    avg(length(query)) AS avg_query_length,
    sum(CASE WHEN state = 'active' THEN 1 ELSE 0 END) AS active_queries,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY extract(epoch FROM now() - query_start)) AS p95_duration
FROM pg_stat_activity
WHERE state != 'idle'
  AND backend_type = 'client backend'
  AND query_start > now() - interval '30 days'
GROUP BY usename, date_trunc('hour', query_start);

-- Statistical summary per user
CREATE VIEW security.user_profile AS
SELECT
    user_name,
    avg(query_count) AS avg_queries_per_hour,
    stddev(query_count) AS stddev_queries_per_hour,
    avg(avg_query_length) AS avg_query_length,
    stddev(avg_query_length) AS stddev_query_length,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY query_count) AS p99_query_count
FROM security.user_baseline
GROUP BY user_name;
```

### 4.2 Anomaly Detection Algorithms

#### Statistical Methods

**Z-Score Detection:**

For each user activity metric, compute the Z-score against their historical baseline:

```python
import numpy as np
from scipy import stats

def detect_anomaly_zscore(current_value, historical_values, threshold=3.0):
    """
    Detect anomaly using Z-score method.
    Returns (is_anomalous, z_score, p_value)
    """
    mean = np.mean(historical_values)
    std = np.std(historical_values)

    if std == 0:
        return current_value != mean, float('inf') if current_value != mean else 0, 0

    z_score = (current_value - mean) / std
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    return abs(z_score) > threshold, z_score, p_value
```

**Exponential Weighted Moving Average (EWMA):**

Adapts to gradual behavioral changes while detecting sudden shifts:

```python
def ewma_anomaly_detection(time_series, span=7, threshold_multiplier=3):
    """
    EWMA-based anomaly detection.
    Adapts baseline over time while detecting sudden deviations.
    """
    ewma = time_series.ewm(span=span).mean()
    ewma_std = time_series.ewm(span=span).std()

    upper_bound = ewma + (threshold_multiplier * ewma_std)
    lower_bound = ewma - (threshold_multiplier * ewma_std)

    anomalies = (time_series > upper_bound) | (time_series < lower_bound)
    return anomalies, upper_bound, lower_bound
```

#### Machine Learning Methods

**Isolation Forest** (unsupervised anomaly detection):

```python
from sklearn.ensemble import IsolationForest
import pandas as pd

def train_user_anomaly_model(user_features_df):
    """
    Train Isolation Forest model on user behavior features.
    Features: query_count, rows_accessed, distinct_tables, avg_query_length,
              hour_of_day, session_duration, error_count
    """
    model = IsolationForest(
        n_estimators=100,
        contamination=0.01,  # Expect 1% anomalous behavior
        max_samples='auto',
        random_state=42
    )

    feature_columns = [
        'query_count', 'rows_accessed', 'distinct_tables',
        'avg_query_length', 'hour_of_day', 'session_duration', 'error_count'
    ]

    model.fit(user_features_df[feature_columns])
    return model

def score_current_behavior(model, current_features):
    """
    Score current user behavior. Returns anomaly score (-1 = anomalous, 1 = normal).
    """
    prediction = model.predict(current_features.reshape(1, -1))
    score = model.decision_function(current_features.reshape(1, -1))
    return prediction[0], score[0]
```

**LSTM Autoencoder** (sequence-based anomaly detection for query patterns):

Captures temporal dependencies in user behavior sequences. High reconstruction error indicates anomalous behavior patterns that deviate from learned sequences.

### 4.3 Peer Group Analysis

Users with similar roles should exhibit similar database access patterns. Peer group analysis identifies outliers within role-based cohorts:

```sql
-- Define peer groups based on granted roles
CREATE VIEW security.peer_groups AS
SELECT
    r.rolname AS user_name,
    array_agg(DISTINCT m.rolname ORDER BY m.rolname) AS role_memberships,
    md5(array_to_string(array_agg(DISTINCT m.rolname ORDER BY m.rolname), ',')) AS peer_group_id
FROM pg_roles r
JOIN pg_auth_members am ON r.oid = am.member
JOIN pg_roles m ON am.roleid = m.oid
WHERE r.rolcanlogin = true
GROUP BY r.rolname;

-- Compare user activity to peer group
CREATE VIEW security.peer_comparison AS
SELECT
    ub.user_name,
    pg.peer_group_id,
    ub.query_count,
    peer_avg.avg_query_count AS peer_avg_queries,
    (ub.query_count - peer_avg.avg_query_count) / NULLIF(peer_avg.stddev_query_count, 0) AS deviation_from_peers
FROM security.user_baseline ub
JOIN security.peer_groups pg ON ub.user_name = pg.user_name
JOIN (
    SELECT peer_group_id, avg(query_count) AS avg_query_count,
           stddev(query_count) AS stddev_query_count
    FROM security.user_baseline ub2
    JOIN security.peer_groups pg2 ON ub2.user_name = pg2.user_name
    GROUP BY peer_group_id
) peer_avg ON pg.peer_group_id = peer_avg.peer_group_id;
```

### 4.4 Risk Scoring Models

Composite risk scores combine multiple behavioral signals:

```python
def calculate_user_risk_score(user_activity):
    """
    Multi-factor risk scoring for database user behavior.
    Returns score 0-100 (0 = no risk, 100 = critical threat).
    """
    weights = {
        'volume_anomaly': 0.20,      # Abnormal data access volume
        'time_anomaly': 0.15,        # Off-hours access
        'new_objects': 0.15,         # Accessing new tables/schemas
        'privilege_changes': 0.20,   # Recent privilege modifications
        'error_spike': 0.10,         # Authentication/authorization errors
        'peer_deviation': 0.10,      # Deviation from peer group
        'geographic_anomaly': 0.10   # New source IP/location
    }

    scores = {}
    scores['volume_anomaly'] = min(100, max(0,
        (user_activity.rows_accessed - user_activity.baseline_mean) /
        max(user_activity.baseline_std, 1) * 33))

    scores['time_anomaly'] = 100 if user_activity.is_off_hours and \
        not user_activity.has_off_hours_history else 0

    scores['new_objects'] = min(100,
        user_activity.new_tables_accessed * 20)

    scores['privilege_changes'] = 100 if user_activity.recent_grant else 0

    scores['error_spike'] = min(100,
        user_activity.error_count / max(user_activity.baseline_error_rate, 0.1) * 25)

    scores['peer_deviation'] = min(100, max(0,
        user_activity.peer_z_score * 33))

    scores['geographic_anomaly'] = 80 if user_activity.new_source_ip else 0

    composite_score = sum(
        scores[factor] * weight
        for factor, weight in weights.items()
    )

    return min(100, composite_score), scores
```

### 4.5 Alert Fatigue Management

UBA systems notoriously produce high false-positive rates. Strategies to manage alert fatigue:

1. **Tiered alerting:** Only alert on composite scores above threshold (e.g., >70 = immediate, 50-70 = daily digest, <50 = weekly report)
2. **Contextual suppression:** Suppress alerts during known maintenance windows, ETL schedules, or after planned deployments
3. **Feedback loops:** Analysts mark alerts as true/false positive; model retrains on feedback
4. **Alert aggregation:** Group related anomalies into a single incident (e.g., same user, same session, multiple signals)
5. **Decay scoring:** Risk scores decay over time without reinforcing signals; prevents permanent flagging from one-time anomalies

---

## 5. Data Pipeline Monitoring

### 5.1 Airflow Task Security Monitoring

Apache Airflow orchestrates data pipelines and represents a high-value target for attackers (access to credentials, data movement control, code execution).

**Security-relevant Airflow monitoring points:**

```python
# Custom Airflow security monitoring plugin
from airflow.plugins_manager import AirflowPlugin
from airflow.listeners import hookimpl
from airflow import settings
import json
import logging

security_logger = logging.getLogger('airflow.security_audit')

@hookimpl
def on_task_instance_running(previous_state, task_instance, session):
    """Monitor task executions for security-relevant patterns."""
    audit_event = {
        'event': 'task_started',
        'dag_id': task_instance.dag_id,
        'task_id': task_instance.task_id,
        'execution_date': str(task_instance.execution_date),
        'operator': task_instance.operator,
        'executor_config': str(task_instance.executor_config),
        'queue': task_instance.queue,
        'pool': task_instance.pool,
    }

    # Flag high-risk operators
    high_risk_operators = ['BashOperator', 'PythonOperator', 'SSHOperator',
                           'DockerOperator', 'KubernetesPodOperator']
    if task_instance.operator in high_risk_operators:
        audit_event['risk_level'] = 'elevated'

    security_logger.info(json.dumps(audit_event))

@hookimpl
def on_dag_run_failed(dag_run, msg):
    """Alert on unexpected DAG failures (potential tampering)."""
    audit_event = {
        'event': 'dag_run_failed',
        'dag_id': dag_run.dag_id,
        'run_id': dag_run.run_id,
        'failure_reason': msg,
    }
    security_logger.warning(json.dumps(audit_event))
```

**Critical Airflow security events to monitor:**
- DAG file modifications (new DAGs, altered existing DAGs)
- Connection/Variable access patterns (credential retrieval)
- BashOperator/PythonOperator executing unexpected commands
- DAG schedule changes (attackers may alter schedules to exfiltrate during off-hours)
- Pool/Queue modifications (lateral movement between environments)
- RBAC role assignments and permission changes
- API token creation and usage

### 5.2 Kafka Consumer Lag as Security Signal

Abnormal Kafka consumer lag patterns can indicate security events:

**Sudden lag spike on specific topics:**
- Consumer application compromised (processing halted)
- Data pipeline poisoning (malformed messages causing consumer crashes)
- Denial of service against downstream processors

**Consumer lag drops to zero unexpectedly:**
- Unauthorized consumer draining topic data (exfiltration)
- Topic deletion/recreation (evidence destruction)

**Monitoring with Prometheus + Grafana:**

```yaml
# Prometheus alerting rules for Kafka security anomalies
groups:
  - name: kafka_security
    rules:
      - alert: UnexpectedConsumerGroupActive
        expr: |
          kafka_consumergroup_lag > 0
          AND ON(consumergroup) (
            kafka_consumergroup_members
            != kafka_consumergroup_members offset 1h
          )
        for: 5m
        labels:
          severity: warning
          team: security
        annotations:
          summary: "New consumer joined group {{ $labels.consumergroup }}"

      - alert: KafkaTopicDataDrain
        expr: |
          rate(kafka_topic_partition_current_offset[5m]) > 10000
          AND kafka_consumergroup_lag == 0
          AND hour() < 6
        for: 10m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Possible data exfiltration - topic {{ $labels.topic }} being drained off-hours"

      - alert: KafkaUnauthorizedTopicAccess
        expr: |
          increase(kafka_server_brokertopicmetrics_messagesin_total{topic=~".*sensitive.*|.*pii.*|.*financial.*"}[5m]) > 0
          AND ON(topic) kafka_acl_unauthorized_access_total > 0
        labels:
          severity: critical
```

### 5.3 Spark Job Anomaly Detection

Security monitoring for Spark processing clusters:

- **Unexpected executor spawning:** New Spark applications launching outside scheduled windows
- **Data locality anomalies:** Spark jobs reading from unexpected storage paths (data staging for exfiltration)
- **Resource hijacking:** Cryptomining or unauthorized workloads consuming cluster resources
- **Library injection:** Unexpected JAR files or Python packages in Spark runtime
- **Output path monitoring:** Spark jobs writing to external/unauthorized destinations

```python
# Spark event listener for security monitoring
# Deployed via spark.extraListeners configuration
from pyspark import SparkContext
from pyspark.listener import SparkListener, TaskEnd, ApplicationEnd

class SecuritySparkListener(SparkListener):
    def onApplicationStart(self, applicationStart):
        # Log application metadata for audit
        audit = {
            'event': 'spark_app_start',
            'app_name': applicationStart.appName,
            'app_id': applicationStart.appId,
            'timestamp': applicationStart.time,
            'user': applicationStart.sparkUser,
        }
        self.emit_security_event(audit)

    def onJobStart(self, jobStart):
        # Check for unauthorized data sources in job
        for stage in jobStart.stageInfos:
            for rdd in stage.rddInfos:
                if self._is_sensitive_path(rdd.name):
                    self.emit_security_event({
                        'event': 'sensitive_data_access',
                        'job_id': jobStart.jobId,
                        'rdd': rdd.name,
                        'risk': 'high'
                    })
```

### 5.4 dbt Model Execution Monitoring

dbt (data build tool) transforms data within the warehouse. Security monitoring focuses on:

- **Model modification tracking:** Changes to transformation logic (data manipulation/corruption)
- **Source freshness anomalies:** Upstream data staleness indicating pipeline compromise
- **Unexpected full refreshes:** Incremental models running full refresh (resource abuse or data destruction)
- **Custom schema targets:** Models materializing to unauthorized schemas

```yaml
# dbt project monitoring via on-run-end hook
# models/hooks/security_audit.sql
{% macro security_audit_log() %}
  {% set results = results | selectattr("status", "equalto", "error") | list %}
  {% if results | length > 0 %}
    {% do log("SECURITY_AUDIT: " ~ results | length ~ " model failures detected", info=true) %}
    {% for result in results %}
      {% do log("SECURITY_AUDIT: Failed model: " ~ result.node.unique_id ~ " | Error: " ~ result.message, info=true) %}
    {% endfor %}
  {% endif %}

  {# Detect unexpected schema changes #}
  {% set schema_changes = run_results | selectattr("adapter_response.schema_changed", "equalto", true) | list %}
  {% if schema_changes | length > 0 %}
    {% do log("SECURITY_ALERT: Schema changes detected in " ~ schema_changes | length ~ " models", info=true) %}
  {% endif %}
{% endmacro %}
```

### 5.5 Data Volume Anomaly Detection (Exfiltration Signal)

Track data volumes flowing through pipelines to detect exfiltration:

```sql
-- Track daily data volumes per pipeline/table
CREATE TABLE security.data_volume_tracking AS
SELECT
    current_date AS tracking_date,
    schemaname,
    tablename,
    n_tup_ins AS rows_inserted,
    n_tup_upd AS rows_updated,
    n_tup_del AS rows_deleted,
    pg_total_relation_size(schemaname || '.' || tablename) AS table_size_bytes
FROM pg_stat_user_tables;

-- Detect anomalous volume changes
SELECT
    t.tablename,
    t.rows_inserted AS today_inserts,
    avg(h.rows_inserted) AS avg_daily_inserts,
    (t.rows_inserted - avg(h.rows_inserted)) / NULLIF(stddev(h.rows_inserted), 0) AS z_score
FROM security.data_volume_tracking t
JOIN security.data_volume_tracking h
    ON t.tablename = h.tablename
    AND h.tracking_date BETWEEN current_date - 30 AND current_date - 1
WHERE t.tracking_date = current_date
GROUP BY t.tablename, t.rows_inserted
HAVING abs((t.rows_inserted - avg(h.rows_inserted)) / NULLIF(stddev(h.rows_inserted), 0)) > 3;
```

---

## 6. Cloud Database Monitoring

### 6.1 AWS Database Security Monitoring

#### CloudTrail Data Events for RDS

CloudTrail data events capture API calls to RDS instances at the database engine level (when enabled). Management events capture infrastructure changes.

```json
{
  "eventSource": "rds.amazonaws.com",
  "eventName": "ModifyDBInstance",
  "requestParameters": {
    "dBInstanceIdentifier": "production-db",
    "publiclyAccessible": true,
    "masterUserPassword": "***"
  }
}
```

**Critical CloudTrail events for RDS:**
- `ModifyDBInstance` with `publiclyAccessible: true` (exposure)
- `ModifyDBCluster` security group changes (network exposure)
- `CreateDBSnapshot` / `CopyDBSnapshot` to external accounts (data theft)
- `RestoreDBInstanceFromDBSnapshot` in unauthorized region (data staging)
- `ModifyDBParameterGroup` changing audit settings (detection evasion)
- `DeleteDBInstance` with `SkipFinalSnapshot: true` (evidence destruction)

**AWS Config Rules for continuous compliance:**

```json
{
  "ConfigRuleName": "rds-instance-public-access-check",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "RDS_INSTANCE_PUBLIC_ACCESS_CHECK"
  },
  "Scope": {
    "ComplianceResourceTypes": ["AWS::RDS::DBInstance"]
  }
}
```

#### RDS Enhanced Monitoring + Performance Insights

Enhanced Monitoring provides OS-level metrics at 1-second granularity. Security use cases:
- CPU spikes correlating with cryptomining
- Network throughput anomalies (data exfiltration)
- Process list monitoring (unexpected processes on underlying host)

#### GuardDuty for RDS

Amazon GuardDuty RDS Protection (launched 2023) analyzes RDS login activity:
- `CredentialAccess:RDS/AnomalousBehavior` - Anomalous login patterns
- `CredentialAccess:RDS/MaliciousIPCaller` - Login from known malicious IPs
- `Discovery:RDS/MaliciousIPCaller` - Database discovery from threat IPs

### 6.2 GCP Database Security Monitoring

#### Cloud Audit Logs

GCP separates audit logs into categories:

- **Admin Activity Logs:** Always enabled. Captures CREATE, DELETE, UPDATE operations on Cloud SQL instances.
- **Data Access Logs:** Must be explicitly enabled (cost implications). Captures read operations and data queries.
- **System Event Logs:** Google-initiated actions.

```bash
# Enable Data Access audit logs for Cloud SQL
gcloud projects get-iam-policy PROJECT_ID --format=json | jq '.auditConfigs += [{
  "service": "cloudsql.googleapis.com",
  "auditLogConfigs": [
    {"logType": "ADMIN_READ"},
    {"logType": "DATA_WRITE"},
    {"logType": "DATA_READ"}
  ]
}]' | gcloud projects set-iam-policy PROJECT_ID /dev/stdin
```

#### Security Command Center (SCC)

SCC provides centralized security findings for Cloud SQL:
- Public IP exposure detection
- Overly permissive authorized networks
- SSL not enforced
- No automatic backups
- Database flags with security implications (e.g., `log_connections` disabled)

**Custom SCC findings via Security Health Analytics:**

```yaml
# Terraform for SCC notification config
resource "google_scc_notification_config" "sql_security" {
  config_id    = "cloud-sql-security-alerts"
  organization = var.org_id
  description  = "Cloud SQL security finding notifications"
  pubsub_topic = google_pubsub_topic.security_alerts.id

  streaming_config {
    filter = "category=\"SQL_PUBLIC_IP\" OR category=\"SQL_NO_ROOT_PASSWORD\" OR category=\"SQL_WEAK_ROOT_PASSWORD\""
  }
}
```

### 6.3 Azure Database Security Monitoring

#### Microsoft Defender for SQL

Defender for SQL provides:
- **SQL Advanced Threat Protection (ATP):** ML-based threat detection
  - SQL injection detection (anomalous query patterns)
  - Brute force attack detection
  - Anomalous data access patterns
  - Anomalous database access from unusual locations/applications
- **Vulnerability Assessment:** CIS-based configuration scanning
- **Data Discovery and Classification:** Automatic sensitive data identification

**ATP Alert types:**
- `SQL.VM_BruteForce`
- `SQL.VM_PotentialSQLInjection`
- `SQL.VM_SuspiciousActivity`
- `SQL.DB_DataExfiltration.Rule`
- `SQL.DB_HarmfulApplication`
- `SQL.DB_PrincipalAnomaly`

#### Azure Diagnostic Settings

```bash
# Enable all diagnostic categories for Azure SQL
az monitor diagnostic-settings create \
  --name "security-monitoring" \
  --resource "/subscriptions/.../Microsoft.Sql/servers/prod-server/databases/prod-db" \
  --workspace "/subscriptions/.../Microsoft.OperationalInsights/workspaces/security-workspace" \
  --logs '[
    {"category": "SQLSecurityAuditEvents", "enabled": true, "retentionPolicy": {"days": 365, "enabled": true}},
    {"category": "SQLInsights", "enabled": true},
    {"category": "AutomaticTuning", "enabled": true},
    {"category": "QueryStoreRuntimeStatistics", "enabled": true},
    {"category": "Errors", "enabled": true},
    {"category": "DatabaseWaitStatistics", "enabled": true}
  ]'
```

#### Azure Monitor KQL Queries

```kql
// Detect brute force attacks on Azure SQL
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.SQL"
| where Category == "SQLSecurityAuditEvents"
| where action_name_s == "DATABASE AUTHENTICATION FAILED"
| summarize FailureCount = count(), TargetUsers = dcount(server_principal_name_s)
    by bin(TimeGenerated, 5m), client_ip_s, Resource
| where FailureCount > 10
| project TimeGenerated, client_ip_s, FailureCount, TargetUsers, Resource

// Detect privilege escalation
AzureDiagnostics
| where Category == "SQLSecurityAuditEvents"
| where action_name_s in ("ALTER ROLE", "ADD MEMBER", "GRANT")
| where statement_s contains "db_owner" or statement_s contains "sysadmin"
| project TimeGenerated, server_principal_name_s, statement_s, client_ip_s
```

### 6.4 Cross-Cloud SIEM Aggregation

For organizations with multi-cloud database deployments, aggregating logs into a single SIEM:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│     AWS      │    │     GCP      │    │    Azure     │
│              │    │              │    │              │
│ CloudTrail   │    │ Audit Logs   │    │ Diagnostic   │
│ CloudWatch   │    │ → Pub/Sub    │    │ Settings     │
│ → S3 → SQS  │    │ → Cloud      │    │ → Event Hub  │
│              │    │   Functions  │    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼───────┐
                    │  SIEM        │
                    │  (Splunk /   │
                    │   Sentinel / │
                    │   Elastic)   │
                    └──────────────┘
```

**Normalization challenges:**
- Different timestamp formats (ISO 8601 variants)
- Different user identity formats (ARN vs email vs service principal)
- Different event naming (ModifyDBInstance vs cloudsql.instances.update vs Microsoft.Sql/servers/write)
- Different severity scales

Use OCSF (Open Cybersecurity Schema Framework) or ECS (Elastic Common Schema) for normalization.

---

## 7. Real-Time Alerting and Response

### 7.1 Alert Routing and Escalation

**Tiered alerting architecture:**

| Severity | Response Time | Channel | Escalation |
|----------|--------------|---------|------------|
| P1 (Critical) | < 5 minutes | PagerDuty (wake) + Slack #incidents | Auto-escalate to CISO if unacked in 15m |
| P2 (High) | < 30 minutes | PagerDuty (urgent) + Slack #security | Escalate to on-call lead if unacked in 1h |
| P3 (Medium) | < 4 hours | Slack #security-alerts | Daily review in security standup |
| P4 (Low) | < 24 hours | Email digest + JIRA ticket | Weekly triage |

**PagerDuty integration configuration:**

```yaml
# Alert routing via PagerDuty Events API v2
pagerduty_integration:
  routing_rules:
    - condition: "severity == 'critical' AND category == 'data_exfiltration'"
      service_key: "PROD_DB_SECURITY_ONCALL"
      urgency: "high"
      escalation_policy: "database_security_critical"

    - condition: "severity == 'high' AND category == 'privilege_escalation'"
      service_key: "PROD_DB_SECURITY_ONCALL"
      urgency: "high"
      escalation_policy: "database_security_standard"

    - condition: "severity == 'medium'"
      service_key: "SECURITY_TRIAGE"
      urgency: "low"
      escalation_policy: "security_triage_standard"

  alert_grouping:
    type: "intelligent"
    time_window: 300  # Group related alerts within 5 minutes
    fields: ["user_name", "database_name", "src_ip"]
```

### 7.2 Automated Response Actions

#### Connection Killing

Immediately terminate suspicious sessions:

```sql
-- PostgreSQL: Kill session by PID
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE usename = 'compromised_user'
  AND pid != pg_backend_pid();

-- MySQL: Kill connection
SELECT CONCAT('KILL CONNECTION ', id, ';')
FROM information_schema.processlist
WHERE user = 'compromised_user';

-- SQL Server: Kill session
DECLARE @spid INT;
DECLARE kill_cursor CURSOR FOR
    SELECT session_id FROM sys.dm_exec_sessions
    WHERE login_name = 'compromised_user';
OPEN kill_cursor;
FETCH NEXT FROM kill_cursor INTO @spid;
WHILE @@FETCH_STATUS = 0
BEGIN
    EXEC('KILL ' + @spid);
    FETCH NEXT FROM kill_cursor INTO @spid;
END;
CLOSE kill_cursor;
DEALLOCATE kill_cursor;
```

#### Account Locking

```sql
-- PostgreSQL: Lock user account
ALTER ROLE compromised_user NOLOGIN;

-- MySQL: Lock account
ALTER USER 'compromised_user'@'%' ACCOUNT LOCK;

-- SQL Server: Disable login
ALTER LOGIN [compromised_user] DISABLE;
```

#### Network Isolation

```bash
# AWS: Modify security group to isolate RDS instance
aws ec2 revoke-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --ip-permissions '[{"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]'

# Replace with restricted access
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --ip-permissions '[{"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "IpRanges": [{"CidrIp": "10.0.100.0/24", "Description": "IR team only"}]}]'

# GCP: Update authorized networks
gcloud sql instances patch prod-db \
  --authorized-networks="10.0.100.0/24" \
  --quiet
```

### 7.3 SOAR Playbooks for Database Incidents

**Playbook: Database Brute Force Response**

```yaml
playbook:
  name: "Database Brute Force Automated Response"
  trigger:
    alert_type: "brute_force_database"
    threshold: "20 failures in 5 minutes from single IP"

  steps:
    - id: enrich_ip
      action: threat_intelligence_lookup
      input:
        ip: "{{ alert.src_ip }}"
      output: ip_reputation

    - id: check_legitimate
      action: cmdb_lookup
      input:
        ip: "{{ alert.src_ip }}"
      output: is_known_asset

    - id: decision
      type: condition
      conditions:
        - if: "{{ ip_reputation.score > 70 OR NOT is_known_asset }}"
          goto: block_ip
        - if: "{{ ip_reputation.score <= 70 AND is_known_asset }}"
          goto: notify_team

    - id: block_ip
      action: firewall_block
      input:
        ip: "{{ alert.src_ip }}"
        duration: "24h"
        rule_comment: "Auto-blocked: DB brute force from {{ alert.src_ip }}"

    - id: lock_targeted_accounts
      action: database_account_lock
      input:
        accounts: "{{ alert.targeted_accounts }}"
        database: "{{ alert.database_name }}"
      condition: "{{ alert.any_success == true }}"

    - id: create_incident
      action: create_jira_ticket
      input:
        project: "SEC"
        type: "Incident"
        priority: "{{ 'Critical' if alert.any_success else 'High' }}"
        summary: "Database brute force: {{ alert.src_ip }} → {{ alert.database_name }}"
        description: |
          Automated response executed:
          - IP blocked: {{ alert.src_ip }}
          - Attempts: {{ alert.failure_count }}
          - Targeted accounts: {{ alert.targeted_accounts }}
          - Successful auth after failures: {{ alert.any_success }}

    - id: notify_team
      action: slack_message
      input:
        channel: "#db-security-incidents"
        message: |
          :rotating_light: Database brute force detected
          Source: {{ alert.src_ip }} ({{ ip_reputation.country }})
          Target: {{ alert.database_name }}
          Failures: {{ alert.failure_count }}
          Compromised: {{ alert.any_success }}
          Ticket: {{ create_incident.ticket_url }}
```

### 7.4 Alert Tuning and Threshold Optimization

**Adaptive thresholds using historical data:**

```python
def calculate_adaptive_threshold(metric_history, sensitivity='medium'):
    """
    Calculate adaptive alerting threshold based on historical patterns.
    Uses day-of-week and hour-of-day seasonality.
    """
    sensitivities = {
        'low': 4.0,      # Few alerts, may miss threats
        'medium': 3.0,   # Balanced
        'high': 2.0,     # More alerts, higher detection rate
        'critical': 1.5  # High alert volume, minimal misses
    }

    multiplier = sensitivities.get(sensitivity, 3.0)

    # Group by day-of-week and hour for seasonal baselines
    grouped = metric_history.groupby([
        metric_history.index.dayofweek,
        metric_history.index.hour
    ])

    seasonal_mean = grouped.transform('mean')
    seasonal_std = grouped.transform('std')

    upper_threshold = seasonal_mean + (multiplier * seasonal_std)
    lower_threshold = seasonal_mean - (multiplier * seasonal_std)

    return upper_threshold, lower_threshold
```

**Threshold review cadence:**
- Weekly: Review false positive rate, adjust noisy rules
- Monthly: Analyze detection coverage gaps, add new rules
- Quarterly: Full threshold recalibration against 90-day baseline
- After incidents: Validate detection worked, add rules for missed indicators

---

## 8. Threat Hunting in Data Systems

### 8.1 Hypothesis-Driven Hunting for Data Environments

Threat hunting in database environments requires domain-specific hypotheses that account for the unique characteristics of data systems:

**Hypothesis framework:**

| # | Hypothesis | Data Sources | Hunting Query |
|---|-----------|-------------|---------------|
| H1 | Attacker is using service account credentials to access production data | DAM logs, auth logs | Service accounts with interactive sessions, new source IPs |
| H2 | Insider is staging data for exfiltration via temporary tables | Query logs, schema changes | CTAS/SELECT INTO operations to non-standard schemas |
| H3 | Lateral movement via database links/linked servers | Linked server logs, distributed queries | Cross-server queries to new targets |
| H4 | Credential harvesting from database-stored secrets | Query logs filtering on config/secret tables | SELECT on tables containing connection strings/passwords |
| H5 | Attacker modifying audit trail to cover tracks | Audit config changes, log gaps | Gaps in sequential audit IDs, audit table truncation |

### 8.2 Hunting for Lateral Movement via Databases

Databases frequently serve as pivot points for lateral movement because they maintain connections to multiple systems:

**PostgreSQL Foreign Data Wrappers (FDW):**
```sql
-- Hunt for new or modified foreign servers
SELECT srvname, srvowner::regrole, srvoptions, srvacl
FROM pg_foreign_server
WHERE srvname NOT IN (SELECT srvname FROM security.known_foreign_servers);

-- Hunt for FDW queries to unusual targets
SELECT * FROM pg_stat_activity
WHERE query LIKE '%foreign_table%' OR query LIKE '%dblink%'
  AND usename NOT IN ('etl_user', 'replication_user');
```

**SQL Server Linked Servers:**
```sql
-- Hunt for linked server usage
SELECT
    s.name AS linked_server,
    s.data_source AS target,
    s.provider,
    l.uses_self_credential,
    l.remote_name
FROM sys.servers s
LEFT JOIN sys.linked_logins l ON s.server_id = l.server_id
WHERE s.is_linked = 1;

-- Recent distributed queries
SELECT
    session_id,
    login_name,
    text AS query_text,
    start_time
FROM sys.dm_exec_sessions s
CROSS APPLY sys.dm_exec_sql_text(most_recent_sql_handle) t
WHERE text LIKE '%OPENQUERY%' OR text LIKE '%EXEC%AT%'
ORDER BY start_time DESC;
```

**MySQL federated tables and replication channels:**
```sql
-- Check for unauthorized replication channels
SELECT * FROM performance_schema.replication_connection_configuration
WHERE CHANNEL_NAME NOT IN ('group_replication_recovery', 'known_replica');

-- Federated table access
SELECT TABLE_SCHEMA, TABLE_NAME, ENGINE, CREATE_OPTIONS
FROM information_schema.TABLES
WHERE ENGINE = 'FEDERATED';
```

### 8.3 Detecting Living-off-the-Land via Database Native Tools

Attackers abuse built-in database capabilities for command execution, file access, and network communication:

#### SQL Server: xp_cmdshell and Beyond

```sql
-- Hunt for xp_cmdshell enablement
SELECT name, value_in_use
FROM sys.configurations
WHERE name = 'xp_cmdshell';

-- Hunt for OLE Automation usage (alternative to xp_cmdshell)
SELECT
    session_id, text, start_time, login_name
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE text LIKE '%sp_OACreate%' OR text LIKE '%sp_OAMethod%'
   OR text LIKE '%xp_cmdshell%' OR text LIKE '%xp_regread%'
   OR text LIKE '%OPENROWSET%BULK%';

-- CLR assembly execution (managed code in SQL Server)
SELECT
    a.name AS assembly_name,
    a.permission_set_desc,
    a.create_date,
    af.name AS file_name
FROM sys.assemblies a
JOIN sys.assembly_files af ON a.assembly_id = af.assembly_id
WHERE a.permission_set_desc IN ('UNSAFE_ACCESS', 'EXTERNAL_ACCESS')
  AND a.is_user_defined = 1;
```

#### PostgreSQL: COPY PROGRAM and Extensions

```sql
-- Hunt for COPY PROGRAM usage (executes OS commands)
-- This appears in pgAudit logs; hunt in centralized logs:
-- grep "COPY.*PROGRAM" /var/log/postgresql/postgresql-*.log

-- Hunt for suspicious extension installations
SELECT extname, extversion, extnamespace::regnamespace
FROM pg_extension
WHERE extname NOT IN ('plpgsql', 'pgcrypto', 'uuid-ossp', 'pgaudit', 'pg_stat_statements');

-- Large object manipulation (file read/write via database)
SELECT loid, pageno FROM pg_largeobject LIMIT 10;
-- Correlate with: SELECT lo_export(loid, '/tmp/exfiltrated_data');

-- Untrusted language functions (arbitrary code execution)
SELECT p.proname, l.lanname, p.prosrc
FROM pg_proc p
JOIN pg_language l ON p.prolang = l.oid
WHERE l.lanname IN ('plpythonu', 'plperlu', 'plsh')
  AND p.pronamespace != 'pg_catalog'::regnamespace;
```

#### MySQL: User-Defined Functions (UDF)

```sql
-- Hunt for UDF installations (shared library loading)
SELECT * FROM mysql.func;

-- Check for suspicious shared libraries
SELECT dl FROM mysql.func WHERE dl NOT IN ('');

-- INTO OUTFILE / INTO DUMPFILE (file write capability)
-- Hunt in general/audit log for:
-- SELECT ... INTO OUTFILE '/path/to/file'
-- SELECT ... INTO DUMPFILE '/path/to/file'

-- LOAD_FILE() usage (file read)
-- Hunt for: SELECT LOAD_FILE('/etc/passwd')
```

### 8.4 Hunting for Data Staging

Attackers preparing data for exfiltration often stage it in temporary locations before extracting:

```sql
-- PostgreSQL: Hunt for suspicious CTAS operations
-- In audit logs, look for:
SELECT query, usename, query_start
FROM pg_stat_activity
WHERE query ~* 'CREATE\s+(TEMP\s+)?TABLE\s+.*\s+AS\s+SELECT'
   OR query ~* 'SELECT\s+.*\s+INTO\s+(TEMP\s+)?'
   OR query ~* 'COPY\s+.*\s+TO\s+'
ORDER BY query_start DESC;

-- Hunt for temporary tables with sensitive data patterns
SELECT schemaname, tablename, n_live_tup
FROM pg_stat_user_tables
WHERE schemaname = 'pg_temp_%'
   OR tablename LIKE '%export%'
   OR tablename LIKE '%dump%'
   OR tablename LIKE '%extract%'
   OR tablename LIKE '%staging%';

-- SQL Server: Hunt for bulk export operations
SELECT
    s.login_name,
    s.host_name,
    t.text AS query,
    s.last_request_start_time
FROM sys.dm_exec_sessions s
CROSS APPLY sys.dm_exec_sql_text(s.most_recent_sql_handle) t
WHERE t.text LIKE '%BCP%'
   OR t.text LIKE '%BULK INSERT%'
   OR t.text LIKE '%OPENROWSET%'
   OR t.text LIKE '%INTO OUTFILE%'
   OR t.text LIKE '%xp_cmdshell%bcp%';
```

### 8.5 Detecting Slow Exfiltration

Low-and-slow data theft designed to stay under volume-based thresholds:

**Detection strategy:** Track cumulative data access over extended periods, not just per-query volume.

```sql
-- PostgreSQL: Cumulative access tracking over 7 days
WITH daily_access AS (
    SELECT
        user_name,
        date_trunc('day', event_timestamp) AS access_date,
        sum(rows_returned) AS daily_rows,
        count(DISTINCT table_name) AS tables_accessed
    FROM security.audit_log
    WHERE event_timestamp > now() - interval '7 days'
      AND command_tag = 'SELECT'
    GROUP BY user_name, date_trunc('day', event_timestamp)
)
SELECT
    user_name,
    sum(daily_rows) AS total_rows_7d,
    avg(daily_rows) AS avg_daily_rows,
    max(daily_rows) AS max_daily_rows,
    count(DISTINCT access_date) AS active_days,
    sum(tables_accessed) AS total_tables
FROM daily_access
GROUP BY user_name
HAVING sum(daily_rows) > 1000000  -- More than 1M rows in 7 days
   AND max(daily_rows) < 50000    -- But never more than 50K in a single day
ORDER BY total_rows_7d DESC;
```

**Splunk correlation for slow exfil detection:**

```spl
index=db_audit command_tag=SELECT user_name=*
| bin _time span=1d
| stats sum(rows_returned) as daily_rows, dc(table_name) as tables by user_name, _time
| streamstats window=7 sum(daily_rows) as rolling_7d_rows by user_name
| where rolling_7d_rows > 1000000 AND daily_rows < 50000
| stats latest(rolling_7d_rows) as total_7d,
        sparkline(daily_rows) as trend,
        latest(tables) as recent_tables by user_name
| sort -total_7d
```

---

## 9. Metrics and KPIs

### 9.1 Security Metrics for Data Infrastructure

#### Detection Metrics

| Metric | Definition | Target | Measurement Method |
|--------|-----------|--------|-------------------|
| **MTTD** (Mean Time to Detect) | Average time between threat occurrence and detection | < 1 hour for critical, < 24h for high | Timestamp of first indicator vs. alert timestamp |
| **MTTR** (Mean Time to Respond) | Average time between detection and containment | < 15 min for critical, < 4h for high | Alert timestamp vs. containment action timestamp |
| **False Positive Rate** | Percentage of alerts that are not true threats | < 20% for critical rules, < 40% overall | Analyst disposition of alerts |
| **Detection Coverage** | Percentage of MITRE ATT&CK techniques with detection rules | > 80% for data-specific techniques | Rule mapping against ATT&CK matrix |
| **Alert Volume** | Total alerts per day/week | Sustainable for team size | Alert count trending |
| **Escalation Rate** | Percentage of alerts requiring human review | Decreasing trend | Automated vs. manual resolution |

#### Operational Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| Log Ingestion Latency | Time from event to indexed/searchable | < 30 seconds (hot tier) |
| Log Completeness | Percentage of expected logs received | > 99.9% |
| Rule Effectiveness | True positive rate per detection rule | > 60% (retire rules below 20%) |
| Audit Coverage | Percentage of databases with active monitoring | 100% production, 100% staging |
| Baseline Currency | Age of behavioral baseline models | < 30 days |
| Playbook Execution Success | Automated response completion rate | > 95% |

### 9.2 Grafana Dashboard Templates

**Database Security Overview Dashboard:**

```json
{
  "dashboard": {
    "title": "Database Security Monitoring",
    "panels": [
      {
        "title": "Authentication Failures (24h)",
        "type": "stat",
        "targets": [{
          "expr": "sum(increase(db_auth_failures_total[24h]))",
          "legendFormat": "Total Failures"
        }],
        "thresholds": {
          "steps": [
            {"value": 0, "color": "green"},
            {"value": 50, "color": "yellow"},
            {"value": 200, "color": "red"}
          ]
        }
      },
      {
        "title": "Privilege Escalation Events",
        "type": "timeseries",
        "targets": [{
          "expr": "sum(rate(db_privilege_changes_total[5m])) by (database, operation)",
          "legendFormat": "{{database}} - {{operation}}"
        }]
      },
      {
        "title": "Data Access Volume Anomalies",
        "type": "timeseries",
        "targets": [
          {
            "expr": "db_rows_accessed_total",
            "legendFormat": "Actual"
          },
          {
            "expr": "db_rows_accessed_baseline + (3 * db_rows_accessed_stddev)",
            "legendFormat": "Upper Threshold (3σ)"
          }
        ]
      },
      {
        "title": "Active Incidents by Severity",
        "type": "piechart",
        "targets": [{
          "expr": "count(db_security_incidents_active) by (severity)"
        }]
      },
      {
        "title": "Detection Coverage by Category",
        "type": "barchart",
        "targets": [{
          "expr": "db_detection_rules_active / db_detection_rules_required * 100",
          "legendFormat": "{{category}}"
        }]
      },
      {
        "title": "MTTD/MTTR Trend",
        "type": "timeseries",
        "targets": [
          {
            "expr": "avg_over_time(db_incident_mttd_minutes[7d])",
            "legendFormat": "MTTD (7d avg)"
          },
          {
            "expr": "avg_over_time(db_incident_mttr_minutes[7d])",
            "legendFormat": "MTTR (7d avg)"
          }
        ]
      }
    ]
  }
}
```

### 9.3 Maturity Model for Database Security Monitoring

| Level | Name | Characteristics | Capabilities |
|-------|------|----------------|-------------|
| **1** | Initial | Ad-hoc, reactive | Native logs only, no centralization, manual review |
| **2** | Developing | Basic monitoring | Centralized log collection, basic SIEM rules (auth failures), manual response |
| **3** | Defined | Standardized processes | DAM deployed, defined detection rules (10+), documented response playbooks, quarterly reviews |
| **4** | Managed | Measured and controlled | UBA operational, automated response for common scenarios, metrics-driven, <1h MTTD for critical threats |
| **5** | Optimizing | Continuously improving | Proactive threat hunting, ML-based detection, SOAR fully integrated, <15min MTTD, continuous red team validation |

**Maturity assessment checklist:**

```
Level 1 → 2:
□ All production databases shipping logs to central location
□ At least 5 basic detection rules active
□ On-call rotation for database security alerts
□ Authentication failure alerting operational

Level 2 → 3:
□ DAM solution deployed on all production databases
□ 20+ detection rules covering MITRE ATT&CK data techniques
□ Documented incident response playbooks for top 5 scenarios
□ Monthly false positive review and rule tuning
□ Baseline established for normal access patterns

Level 3 → 4:
□ UBA operational with peer group analysis
□ Automated response for brute force, account lockout
□ MTTD < 1 hour for critical threats (measured)
□ Coverage gap analysis completed and addressed
□ Integration with CMDB for context enrichment
□ Quarterly tabletop exercises for database incidents

Level 4 → 5:
□ Regular threat hunting campaigns (monthly)
□ SOAR playbooks for top 10 incident types
□ ML models in production for anomaly detection
□ Red team validates detection capabilities quarterly
□ Continuous attack simulation (purple team)
□ Sub-15-minute MTTD for critical threats
□ Predictive analytics for emerging threats
```

### 9.4 Coverage Gap Analysis

Map detection capabilities against the MITRE ATT&CK framework for databases:

| Technique | ID | Detection Rule Exists | Automated Response | Validated by Red Team |
|-----------|----|----------------------|-------------------|----------------------|
| Brute Force | T1110 | Yes | Yes (account lock) | Yes |
| Valid Accounts | T1078 | Partial (UBA) | No | No |
| Data from Local System | T1005 | Yes (mass retrieval) | Yes (alert) | Yes |
| Exfiltration Over C2 | T1041 | Partial (volume) | No | No |
| Account Manipulation | T1098 | Yes (GRANT monitoring) | Yes (alert + revert) | Yes |
| System Information Discovery | T1082 | Partial | No | No |
| Permission Groups Discovery | T1069 | Yes | No | No |
| Data Staged | T1074 | Yes (temp table monitoring) | No | No |
| Indicator Removal | T1070 | Yes (audit config changes) | Yes (alert) | Yes |
| Exploitation of DB Application | T1190 | Partial (SQLi patterns) | Yes (WAF block) | Yes |

---

## 10. Lab Exercises

### Lab 1: Deploy pgAudit + Filebeat + Elasticsearch + Kibana Monitoring Stack

**Objective:** Build a complete database security monitoring pipeline from scratch.

**Environment Setup (Docker Compose):**

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: lab_password_change_me
      POSTGRES_DB: production_sim
    volumes:
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
      - pg_logs:/var/log/postgresql
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    ports:
      - "5432:5432"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=elastic_lab_password
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=kibana_system
      - ELASTICSEARCH_PASSWORD=kibana_lab_password
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.12.0
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - pg_logs:/var/log/postgresql:ro
    depends_on:
      - elasticsearch
      - postgres

volumes:
  pg_logs:
  es_data:
```

**PostgreSQL configuration** (`postgres/postgresql.conf`):

```ini
# Logging configuration
log_destination = 'csvlog'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_file_mode = 0640
log_rotation_age = 1h
log_rotation_size = 50MB
log_min_messages = warning
log_min_error_statement = error
log_connections = on
log_disconnections = on
log_duration = off
log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '
log_statement = 'ddl'

# pgAudit configuration
shared_preload_libraries = 'pgaudit'
pgaudit.log = 'all'
pgaudit.log_catalog = off
pgaudit.log_client = on
pgaudit.log_level = 'log'
pgaudit.log_parameter = on
pgaudit.log_relation = on
pgaudit.log_statement_once = off
pgaudit.role = 'auditor'
```

**Initialization script** (`postgres/init.sql`):

```sql
-- Create audit role
CREATE ROLE auditor NOLOGIN;

-- Create test schema simulating production
CREATE SCHEMA banking;

CREATE TABLE banking.customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150),
    ssn VARCHAR(11),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE banking.accounts (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES banking.customers(id),
    account_number VARCHAR(20),
    balance DECIMAL(15,2),
    account_type VARCHAR(20)
);

CREATE TABLE banking.transactions (
    id SERIAL PRIMARY KEY,
    account_id INT REFERENCES banking.accounts(id),
    amount DECIMAL(15,2),
    transaction_type VARCHAR(20),
    timestamp TIMESTAMP DEFAULT now()
);

-- Grant audit monitoring on sensitive tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA banking TO auditor;

-- Create application users with different privilege levels
CREATE ROLE app_user LOGIN PASSWORD 'app_password';
CREATE ROLE analyst LOGIN PASSWORD 'analyst_password';
CREATE ROLE dba_user LOGIN PASSWORD 'dba_password' SUPERUSER;

GRANT USAGE ON SCHEMA banking TO app_user, analyst;
GRANT SELECT, INSERT, UPDATE ON banking.customers, banking.accounts, banking.transactions TO app_user;
GRANT SELECT ON ALL TABLES IN SCHEMA banking TO analyst;

-- Insert sample data
INSERT INTO banking.customers (name, email, ssn) VALUES
    ('Alice Johnson', 'alice@example.com', '123-45-6789'),
    ('Bob Smith', 'bob@example.com', '987-65-4321'),
    ('Charlie Brown', 'charlie@example.com', '456-78-9012');

INSERT INTO banking.accounts (customer_id, account_number, balance, account_type) VALUES
    (1, 'ACC-001-CHECKING', 15000.00, 'checking'),
    (1, 'ACC-001-SAVINGS', 50000.00, 'savings'),
    (2, 'ACC-002-CHECKING', 8500.00, 'checking'),
    (3, 'ACC-003-CHECKING', 3200.00, 'checking');

INSERT INTO banking.transactions (account_id, amount, transaction_type) VALUES
    (1, -500.00, 'withdrawal'),
    (1, 2000.00, 'deposit'),
    (2, -100.00, 'withdrawal'),
    (3, 1500.00, 'deposit');
```

**Filebeat configuration** (`filebeat/filebeat.yml`):

```yaml
filebeat.inputs:
  - type: filestream
    id: pg-csvlog
    paths:
      - /var/log/postgresql/postgresql-*.csv
    parsers:
      - multiline:
          type: pattern
          pattern: '^\d{4}-\d{2}-\d{2}'
          negate: true
          match: after

processors:
  - decode_csv_fields:
      fields:
        message: ['log_time','user_name','database_name','process_id',
                  'connection_from','session_id','session_line_num',
                  'command_tag','session_start_time','virtual_transaction_id',
                  'transaction_id','error_severity','sql_state_code',
                  'message','detail','hint','internal_query',
                  'internal_query_pos','context','query','query_pos',
                  'location','application_name','backend_type','leader_pid','query_id']
      separator: ","
      trim_leading_space: true
      fail_on_error: false
  - add_fields:
      target: ''
      fields:
        environment: "lab"
        source_type: "postgresql_audit"

output.elasticsearch:
  hosts: ["http://elasticsearch:9200"]
  username: "elastic"
  password: "elastic_lab_password"
  index: "pgaudit-%{+yyyy.MM.dd}"

setup.kibana:
  host: "http://kibana:5601"
```

**Lab Tasks:**

1. Deploy the stack: `docker compose up -d`
2. Generate audit events by running queries as different users
3. Verify logs appear in Elasticsearch: `curl -u elastic:elastic_lab_password http://localhost:9200/pgaudit-*/_count`
4. Create Kibana index pattern for `pgaudit-*`
5. Build a dashboard showing: auth failures over time, queries by user, DDL events, high-row-count queries
6. Simulate an attack (brute force, privilege escalation, data exfiltration) and verify detection

### Lab 2: Create 10 SIEM Detection Rules for Common Database Attacks

**Objective:** Write and validate detection rules for the top 10 database attack patterns.

**Rules to implement:**

| # | Attack | Detection Logic | Validation Method |
|---|--------|----------------|-------------------|
| 1 | Brute force login | >10 auth failures from single IP in 5 min | Run `pgbench` with wrong password |
| 2 | Successful login after brute force | Auth success preceded by >5 failures | Script: fail 5x then succeed |
| 3 | Mass data retrieval | SELECT returning >10,000 rows by non-ETL user | `SELECT * FROM large_table` |
| 4 | Privilege escalation | GRANT with SUPERUSER/ALL PRIVILEGES | `GRANT ALL PRIVILEGES ON...` |
| 5 | Schema destruction | DROP TABLE/DATABASE outside maintenance | `DROP TABLE important_data` |
| 6 | Off-hours access | Human user login between 22:00-06:00 | Connect during off-hours |
| 7 | New source IP | Login from IP not seen in 30 days | Connect from new container |
| 8 | Audit tampering | Changes to pgaudit configuration | `ALTER SYSTEM SET pgaudit.log = 'none'` |
| 9 | Data export | COPY TO or pg_dump execution | `COPY table TO '/tmp/export.csv'` |
| 10 | SQL injection pattern | Queries with UNION SELECT, OR 1=1, comment sequences | Inject via app connection |

**Example rule implementation (Elasticsearch query DSL):**

```json
{
  "rule_name": "Database Brute Force Authentication",
  "description": "Detects 10+ authentication failures from a single source within 5 minutes",
  "risk_score": 75,
  "severity": "high",
  "query": {
    "bool": {
      "must": [
        { "match": { "error_severity": "FATAL" } },
        { "match": { "sql_state_code": "28P01" } }
      ]
    }
  },
  "aggregation": {
    "by_source": {
      "terms": { "field": "connection_from.keyword", "min_doc_count": 10 },
      "aggs": {
        "time_window": {
          "date_histogram": { "field": "@timestamp", "fixed_interval": "5m" },
          "aggs": {
            "failure_count": { "value_count": { "field": "_id" } },
            "alert_filter": {
              "bucket_selector": {
                "buckets_path": { "count": "failure_count" },
                "script": "params.count >= 10"
              }
            }
          }
        }
      }
    }
  },
  "schedule": { "interval": "1m" },
  "actions": {
    "slack_notification": {
      "webhook_url": "https://hooks.slack.com/...",
      "message": "ALERT: Database brute force from {{ctx.payload.source_ip}} - {{ctx.payload.failures}} failures"
    }
  }
}
```

### Lab 3: Build a UBA Baseline and Detect Anomalous Queries

**Objective:** Establish behavioral baselines and detect deviations using statistical methods.

**Phase 1: Generate Normal Baseline (30 simulated days)**

```python
#!/usr/bin/env python3
"""
Generate simulated normal database activity for UBA baseline training.
Run this script to populate 30 days of baseline behavior.
"""
import psycopg2
import random
import time
from datetime import datetime, timedelta

USERS = {
    'app_user': {
        'tables': ['banking.customers', 'banking.accounts', 'banking.transactions'],
        'queries_per_hour': (50, 200),
        'rows_per_query': (1, 100),
        'active_hours': (8, 20),
    },
    'analyst': {
        'tables': ['banking.customers', 'banking.accounts'],
        'queries_per_hour': (10, 50),
        'rows_per_query': (1, 500),
        'active_hours': (9, 18),
    }
}

def simulate_normal_day(conn, user, profile, day_offset):
    """Simulate one day of normal database activity."""
    cur = conn.cursor()
    start_hour, end_hour = profile['active_hours']
    min_queries, max_queries = profile['queries_per_hour']

    for hour in range(start_hour, end_hour):
        num_queries = random.randint(min_queries, max_queries)
        for _ in range(num_queries):
            table = random.choice(profile['tables'])
            limit = random.randint(*profile['rows_per_query'])
            query = f"SELECT * FROM {table} LIMIT {limit}"
            try:
                cur.execute(query)
                cur.fetchall()
            except Exception:
                pass
    cur.close()

def main():
    conn = psycopg2.connect(
        host='localhost', port=5432,
        dbname='production_sim', user='app_user', password='app_password'
    )
    conn.autocommit = True

    for day in range(30):
        for user, profile in USERS.items():
            simulate_normal_day(conn, user, profile, day)
        print(f"Simulated day {day + 1}/30")

    conn.close()

if __name__ == '__main__':
    main()
```

**Phase 2: Detect Anomalies**

```python
#!/usr/bin/env python3
"""
UBA anomaly detection engine for database activity.
Compares current activity against established baseline.
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class UserActivity:
    user_name: str
    query_count: int
    rows_accessed: int
    distinct_tables: int
    hour_of_day: int
    error_count: int
    new_tables: List[str]

@dataclass
class BaselineStats:
    mean_queries: float
    std_queries: float
    mean_rows: float
    std_rows: float
    known_tables: set
    active_hours: set
    mean_errors: float
    std_errors: float

def detect_anomalies(activity: UserActivity, baseline: BaselineStats) -> List[dict]:
    """Detect anomalies in current user activity vs baseline."""
    anomalies = []

    # Query volume anomaly
    if baseline.std_queries > 0:
        query_zscore = (activity.query_count - baseline.mean_queries) / baseline.std_queries
        if abs(query_zscore) > 3:
            anomalies.append({
                'type': 'query_volume',
                'severity': 'high' if abs(query_zscore) > 5 else 'medium',
                'z_score': query_zscore,
                'detail': f"Query count {activity.query_count} vs baseline mean {baseline.mean_queries:.0f}"
            })

    # Data volume anomaly
    if baseline.std_rows > 0:
        rows_zscore = (activity.rows_accessed - baseline.mean_rows) / baseline.std_rows
        if rows_zscore > 3:  # Only flag high (exfiltration signal)
            anomalies.append({
                'type': 'data_volume',
                'severity': 'critical' if rows_zscore > 5 else 'high',
                'z_score': rows_zscore,
                'detail': f"Rows accessed {activity.rows_accessed} vs baseline mean {baseline.mean_rows:.0f}"
            })

    # Time anomaly
    if activity.hour_of_day not in baseline.active_hours:
        anomalies.append({
            'type': 'off_hours_access',
            'severity': 'medium',
            'detail': f"Access at hour {activity.hour_of_day}, normal hours: {sorted(baseline.active_hours)}"
        })

    # New table access
    new_tables = set(activity.new_tables) - baseline.known_tables
    if new_tables:
        anomalies.append({
            'type': 'new_table_access',
            'severity': 'high' if len(new_tables) > 3 else 'medium',
            'detail': f"First-time access to tables: {new_tables}"
        })

    # Error spike
    if baseline.std_errors > 0:
        error_zscore = (activity.error_count - baseline.mean_errors) / baseline.std_errors
        if error_zscore > 3:
            anomalies.append({
                'type': 'error_spike',
                'severity': 'high',
                'z_score': error_zscore,
                'detail': f"Error count {activity.error_count} vs baseline mean {baseline.mean_errors:.0f}"
            })

    return anomalies

# Example usage
baseline = BaselineStats(
    mean_queries=125, std_queries=40,
    mean_rows=2500, std_rows=800,
    known_tables={'banking.customers', 'banking.accounts', 'banking.transactions'},
    active_hours=set(range(8, 20)),
    mean_errors=2, std_errors=1.5
)

# Simulate anomalous activity
anomalous_activity = UserActivity(
    user_name='analyst',
    query_count=500,          # 9.4 sigma above mean
    rows_accessed=50000,      # 59 sigma above mean
    distinct_tables=8,
    hour_of_day=3,            # 3 AM
    error_count=15,           # 8.7 sigma above mean
    new_tables=['banking.audit_log', 'pg_catalog.pg_shadow', 'banking.internal_config']
)

results = detect_anomalies(anomalous_activity, baseline)
for anomaly in results:
    print(f"[{anomaly['severity'].upper()}] {anomaly['type']}: {anomaly['detail']}")
```

### Lab 4: Implement Automated Response to Brute Force Attacks

**Objective:** Build an automated detection-and-response pipeline that detects brute force attacks and executes containment actions.

**Architecture:**

```
PostgreSQL (pgAudit logs)
    → Filebeat
    → Elasticsearch
    → ElastAlert2 (detection)
    → Response Script (containment)
    → Slack + JIRA (notification)
```

**ElastAlert2 rule** (`rules/db_brute_force.yaml`):

```yaml
name: "Database Brute Force Detection"
type: frequency
index: pgaudit-*
num_events: 10
timeframe:
  minutes: 5
query_key: "connection_from.keyword"
filter:
  - term:
      error_severity: "FATAL"
  - term:
      sql_state_code: "28P01"

alert:
  - command
  - slack

command:
  - "/opt/security/respond_brute_force.sh"
  - "--source-ip"
  - "%(connection_from)s"
  - "--target-db"
  - "%(database_name)s"
  - "--failure-count"
  - "%(num_hits)s"

slack:
  slack_webhook_url: "https://hooks.slack.com/services/..."
  slack_channel_override: "#db-security-alerts"
  slack_username_override: "DB Security Bot"
  slack_msg_color: "danger"
  slack_title: "Database Brute Force Detected"
  slack_text: |
    *Source IP:* %(connection_from)s
    *Target Database:* %(database_name)s
    *Failure Count:* %(num_hits)s in 5 minutes
    *Targeted Users:* %(user_name)s

alert_text: |
  Database brute force attack detected.
  Source: {0}
  Database: {1}
  Failures: {2}
alert_text_args:
  - connection_from
  - database_name
  - num_hits
```

**Automated response script** (`/opt/security/respond_brute_force.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

# Parse arguments
SOURCE_IP=""
TARGET_DB=""
FAILURE_COUNT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --source-ip) SOURCE_IP="$2"; shift 2 ;;
        --target-db) TARGET_DB="$2"; shift 2 ;;
        --failure-count) FAILURE_COUNT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

LOG_FILE="/var/log/security/brute_force_response.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

log() {
    echo "${TIMESTAMP} | $1" >> "${LOG_FILE}"
}

log "INCIDENT: Brute force detected from ${SOURCE_IP} against ${TARGET_DB} (${FAILURE_COUNT} failures)"

# Step 1: Block IP via iptables (immediate containment)
if ! iptables -C INPUT -s "${SOURCE_IP}" -p tcp --dport 5432 -j DROP 2>/dev/null; then
    iptables -I INPUT -s "${SOURCE_IP}" -p tcp --dport 5432 -j DROP \
        -m comment --comment "Auto-blocked: brute force ${TIMESTAMP}"
    log "ACTION: Blocked ${SOURCE_IP} via iptables"
fi

# Step 2: Kill active connections from this IP
PGPASSWORD="${PGPASSWORD:-}" psql -h localhost -U postgres -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE client_addr = '${SOURCE_IP}'::inet
      AND pid != pg_backend_pid();
" 2>/dev/null && log "ACTION: Terminated active connections from ${SOURCE_IP}"

# Step 3: If failure count is extreme (>50), lock targeted accounts
if [[ "${FAILURE_COUNT}" -gt 50 ]]; then
    # Extract targeted usernames from recent failures (requires ES query)
    TARGETED_USERS=$(curl -s "http://localhost:9200/pgaudit-*/_search" \
        -H 'Content-Type: application/json' \
        -d "{
            \"size\": 0,
            \"query\": {
                \"bool\": {
                    \"must\": [
                        {\"term\": {\"connection_from.keyword\": \"${SOURCE_IP}\"}},
                        {\"term\": {\"sql_state_code\": \"28P01\"}},
                        {\"range\": {\"@timestamp\": {\"gte\": \"now-10m\"}}}
                    ]
                }
            },
            \"aggs\": {
                \"users\": {\"terms\": {\"field\": \"user_name.keyword\"}}
            }
        }" | jq -r '.aggregations.users.buckets[].key')

    for user in ${TARGETED_USERS}; do
        if [[ "${user}" != "postgres" && "${user}" != "replication" ]]; then
            PGPASSWORD="${PGPASSWORD:-}" psql -h localhost -U postgres -d postgres -c \
                "ALTER ROLE \"${user}\" NOLOGIN;" 2>/dev/null
            log "ACTION: Locked account ${user} (extreme brute force)"
        fi
    done
fi

# Step 4: Create JIRA incident ticket
if command -v jira &>/dev/null; then
    jira issue create \
        --project SEC \
        --type Incident \
        --priority High \
        --summary "Database brute force: ${SOURCE_IP} → ${TARGET_DB}" \
        --body "Automated response executed at ${TIMESTAMP}.
Source IP: ${SOURCE_IP}
Target: ${TARGET_DB}
Failures: ${FAILURE_COUNT}
Actions taken: IP blocked, connections killed$([ "${FAILURE_COUNT}" -gt 50 ] && echo ', accounts locked')" \
        2>/dev/null && log "ACTION: JIRA ticket created"
fi

# Step 5: Schedule IP unblock after 24 hours
echo "iptables -D INPUT -s ${SOURCE_IP} -p tcp --dport 5432 -j DROP 2>/dev/null" | \
    at now + 24 hours 2>/dev/null && log "SCHEDULED: IP unblock in 24 hours"

log "COMPLETE: Brute force response for ${SOURCE_IP} finished"
```

**Validation steps:**

1. Start the monitoring stack
2. Run a simulated brute force attack:
   ```bash
   for i in $(seq 1 20); do
       PGPASSWORD=wrong_password psql -h localhost -U analyst -d production_sim -c "SELECT 1" 2>/dev/null
   done
   ```
3. Verify the alert fires in ElastAlert2 logs
4. Confirm the IP is blocked: `iptables -L INPUT -n | grep <attacker_ip>`
5. Confirm active connections were terminated
6. Verify Slack notification received
7. Check response log: `cat /var/log/security/brute_force_response.log`
8. Verify the IP is automatically unblocked after 24 hours (or test with shorter `at` duration)

---

## Summary

Security monitoring for data infrastructure demands a layered approach combining database-native audit capabilities, network-level visibility, centralized log aggregation, behavioral analytics, and automated response. The critical success factors are:

1. **Complete audit coverage** — no database should operate without monitoring, regardless of environment
2. **Real-time log shipping** — audit logs must leave the database server within seconds to prevent tampering
3. **Contextual detection** — rules must account for legitimate patterns (ETL, maintenance windows) to avoid alert fatigue
4. **Automated response** — sub-minute containment for critical threats (brute force, active exfiltration)
5. **Continuous validation** — red team exercises confirm detection capabilities work against real attack techniques

From an offensive perspective, understanding these monitoring capabilities reveals the attacker's constraint landscape: which activities generate alerts, which paths remain blind, and which evasion techniques bypass specific architectural choices. Every architectural decision (agent vs. network, native vs. external) creates both visibility and gaps — the competent attacker maps these gaps; the competent defender closes them through defense-in-depth.
