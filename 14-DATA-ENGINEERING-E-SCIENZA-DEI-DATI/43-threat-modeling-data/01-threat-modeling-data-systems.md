# Threat Modeling for Data Systems and Data Pipelines

## Table of Contents

1. [Threat Modeling Frameworks](#1-threat-modeling-frameworks)
2. [Data Flow Diagrams for Data Systems](#2-data-flow-diagrams-for-data-systems)
3. [STRIDE Applied to Databases](#3-stride-applied-to-databases)
4. [STRIDE Applied to Data Pipelines](#4-stride-applied-to-data-pipelines)
5. [Data-Specific Threat Categories](#5-data-specific-threat-categories)
6. [Cloud Data Architecture Threats](#6-cloud-data-architecture-threats)
7. [Risk Assessment and Prioritization](#7-risk-assessment-and-prioritization)
8. [Mitigation Strategies](#8-mitigation-strategies)
9. [Threat Modeling Integration in SDLC](#9-threat-modeling-integration-in-sdlc)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Threat Modeling Frameworks

Threat modeling is the structured process of identifying, categorizing, and prioritizing potential threats to a system. For data systems specifically, threat modeling determines what adversaries want (your data), how they might get it, and what controls prevent them. From a penetration tester's perspective, the threat model is the blueprint that dictates what to test and where to focus offensive efforts.

### 1.1 STRIDE

Developed at Microsoft in 1999 by Loren Kohnfelder and Praerit Garg, STRIDE maps six categories of threats to corresponding security properties:

| Threat | Violated Property | Data System Example |
|--------|-------------------|---------------------|
| **S**poofing | Authentication | Forged Kafka producer identity |
| **T**ampering | Integrity | Modified records in transit between pipeline stages |
| **R**epudiation | Non-repudiation | Deleted audit logs after unauthorized data access |
| **I**nformation Disclosure | Confidentiality | Exposed S3 bucket with PII |
| **D**enial of Service | Availability | Resource exhaustion on database connection pool |
| **E**levation of Privilege | Authorization | Read-only analyst gains write access to production tables |

**When to use STRIDE:** General-purpose threat identification for any data system. Best when the team needs a structured checklist approach. Works at any abstraction level — from a single database to an entire data lake architecture.

**STRIDE-per-element:** Apply STRIDE to each element in a Data Flow Diagram:
- External entities → Spoofing, Repudiation
- Data flows → Tampering, Information Disclosure, DoS
- Data stores → Tampering, Information Disclosure, DoS, Repudiation
- Processes → All six categories

### 1.2 PASTA (Process for Attack Simulation and Threat Analysis)

PASTA is a seven-stage risk-centric methodology that aligns business objectives with technical requirements:

**Stage 1: Define Objectives**
- Identify business criticality of the data system
- Define compliance requirements (GDPR, HIPAA, PCI-DSS data handling)
- Establish risk appetite for data loss vs. data unavailability

**Stage 2: Define Technical Scope**
- Inventory all data stores, pipelines, APIs, and integration points
- Map technology stack (database engines, orchestrators, message brokers)
- Document data classification levels

**Stage 3: Application Decomposition**
- Create DFDs specific to data flows
- Identify trust boundaries between ingestion, processing, and serving layers
- Map data lineage and transformation points

**Stage 4: Threat Analysis**
- Research known threats against specific technologies in the stack
- Correlate CVEs with deployed versions
- Analyze threat intelligence for data-theft campaigns targeting your industry

**Stage 5: Vulnerability Analysis**
- Scan for misconfigurations in data infrastructure
- Review access control policies and their enforcement
- Identify gaps between intended and actual data flow paths

**Stage 6: Attack Modeling**
- Build attack trees for high-value data assets
- Simulate attack paths from external entry to data exfiltration
- Model insider threat scenarios (privileged data engineers, compromised service accounts)

**Stage 7: Risk and Impact Analysis**
- Quantify business impact of each attack scenario
- Prioritize mitigations based on risk reduction per dollar
- Generate residual risk documentation

**When to use PASTA:** Complex data architectures where business risk alignment matters. Ideal for organizations with mature security programs that need to justify security investments to leadership. The seven stages map well to data governance frameworks.

### 1.3 LINDDUN (Privacy-Focused)

LINDDUN addresses privacy threats specifically — critical for data systems handling PII:

| Category | Privacy Concern | Data System Example |
|----------|----------------|---------------------|
| **L**inkability | Associating data items with each other | Joining anonymized datasets to re-identify individuals |
| **I**dentifiability | Determining subject identity | Insufficient pseudonymization in data warehouse |
| **N**on-repudiation | Inability to deny an action | Immutable audit logs exposing user behavior patterns |
| **D**etectability | Determining existence of data | Metadata leaking existence of sensitive records |
| **D**isclosure of information | Unauthorized data exposure | Query results revealing more than authorized |
| **U**nawareness | Data processed without subject knowledge | Shadow data copies in dev/test environments |
| **N**on-compliance | Violation of regulations | Data retention beyond GDPR-mandated periods |

**When to use LINDDUN:** Any data system processing personal data. Essential for data lakes that aggregate PII from multiple sources. Use alongside STRIDE — LINDDUN does not replace security threat modeling but augments it with privacy considerations. Required when preparing for GDPR/CCPA compliance assessments.

**Data system specifics:**
- Data warehouses aggregating customer behavior across services create linkability risks
- ETL pipelines that copy data without proper consent tracking create unawareness threats
- Analytics systems that allow ad-hoc queries can enable inference-based identifiability
- Data retention policies not enforced at the storage layer lead to non-compliance

### 1.4 VAST (Visual, Agile, and Simple Threat Modeling)

VAST was designed to scale threat modeling across large organizations by providing two model types:

**Application Threat Model (ATM):**
- Process-flow diagram based
- Developer-centric
- Targets individual data pipeline components (a specific Spark job, a single API endpoint)

**Operational Threat Model (OTM):**
- Infrastructure-centric
- Operations/platform team focused
- Covers deployment topology, network segments, cloud configurations

**When to use VAST:** Organizations with many data teams shipping independently. VAST scales because it integrates into existing agile workflows — each sprint that modifies the data architecture triggers a lightweight threat model update. Best for organizations running DataOps or platform engineering models where data infrastructure changes frequently.

**Key advantage for data systems:** VAST separates the concerns of "is this Spark job secure?" (ATM, owned by data engineers) from "is the cluster hosting it secure?" (OTM, owned by platform/infra team). This maps to the shared responsibility model in cloud data architectures.

### 1.5 Attack Trees

Attack trees decompose a high-level adversary goal into sub-goals using AND/OR nodes:

```
Root Goal: Exfiltrate customer PII from data warehouse
├── OR: Direct database access
│   ├── AND: Obtain credentials + Bypass network controls
│   │   ├── OR: Phish DBA
│   │   ├── OR: Extract from config management
│   │   └── OR: Exploit credential rotation gap
│   └── AND: Exploit SQL injection + Escalate privileges
├── OR: Intercept data in transit
│   ├── OR: Compromise message broker (Kafka)
│   ├── OR: MITM on internal network
│   └── OR: Tap unencrypted replication stream
├── OR: Access backup/archive
│   ├── OR: Misconfigured S3 bucket
│   ├── OR: Compromised backup service account
│   └── OR: Physical access to tape storage
└── OR: Abuse legitimate access
    ├── OR: Insider with over-provisioned access
    ├── OR: Compromised analytics service account
    └── OR: Query API without proper row-level security
```

**When to use attack trees:** Deep analysis of specific high-value targets. Ideal for databases containing crown-jewel data. From a pentest perspective, attack trees define the scope and test plan — each leaf node becomes a test case.

**Quantification:** Assign values to leaf nodes:
- Cost to attacker (time, money, expertise)
- Probability of success
- Detectability (likelihood of triggering alerts)

Roll up values using AND (multiply probabilities, sum costs) and OR (take minimum cost path) to identify the cheapest/easiest attack path — this is what a rational adversary chooses first.

### 1.6 OCTAVE (Operationally Critical Threat, Asset, and Vulnerability Evaluation)

OCTAVE is asset-driven rather than technology-driven, developed by CERT/CC at Carnegie Mellon:

**Phase 1: Build Asset-Based Threat Profiles**
- Identify critical data assets (customer database, financial records, model training data)
- Define security requirements for each asset
- Identify threats to each asset from organizational context

**Phase 2: Identify Infrastructure Vulnerabilities**
- Map data assets to technology components
- Assess vulnerabilities in each component
- Evaluate existing controls

**Phase 3: Develop Security Strategy**
- Analyze risk based on asset criticality
- Develop protection strategies
- Create mitigation plans prioritized by asset value

**When to use OCTAVE:** Organization-wide data governance initiatives. OCTAVE works best when you need to answer "what data is most critical and how well is it protected?" rather than "what can go wrong with this specific pipeline?" Pairs well with data classification programs and data catalog initiatives.

### 1.7 Framework Selection Matrix

| Criterion | STRIDE | PASTA | LINDDUN | VAST | Attack Trees | OCTAVE |
|-----------|--------|-------|---------|------|--------------|--------|
| Ease of adoption | High | Low | Medium | Medium | Medium | Low |
| Scalability | Medium | Low | Medium | High | Low | Medium |
| Privacy focus | Low | Medium | High | Low | Low | Medium |
| Business alignment | Low | High | Low | Medium | Low | High |
| Pentest planning | High | Medium | Low | Medium | High | Low |
| Agile compatibility | Medium | Low | Medium | High | Low | Low |
| Data system fit | High | High | High (PII) | Medium | High | Medium |

**Practical recommendation:** Start with STRIDE-per-element on your DFD for systematic coverage. Layer LINDDUN if you handle PII. Use attack trees for your highest-value data assets. Adopt PASTA when you need risk quantification for executive communication.

---

## 2. Data Flow Diagrams (DFD) for Data Systems

### 2.1 DFD Fundamentals

Data Flow Diagrams are the foundation of threat modeling — you cannot threat model what you cannot visualize. DFDs for data systems differ from traditional application DFDs because data is both the asset being protected and the thing flowing through the system.

**Core elements:**

| Symbol | Element | Data System Examples |
|--------|---------|---------------------|
| Rectangle | External Entity | Source databases, third-party APIs, SaaS data feeds, end users, upstream services |
| Rounded rectangle / Circle | Process | ETL jobs, Spark transformations, Flink operators, dbt models, ML inference |
| Parallel lines / Cylinder | Data Store | Databases, data lakes, object storage, message queues (when persistent), caches |
| Arrow | Data Flow | API calls, file transfers, streaming messages, replication streams, query results |
| Dashed line | Trust Boundary | Network segments, cloud accounts, organizational boundaries, security zones |

### 2.2 DFD Levels

**Context Diagram (Level 0):**
Shows the entire data system as a single process with external entities:

```
[Source Systems] --> (Data Platform) --> [Consumers]
                                     --> [Regulatory Bodies]
[Third-Party Feeds] -->
[Internal Applications] -->
```

Purpose: Establish scope. Everything inside the single process bubble is in-scope for threat modeling. Everything outside is an external entity whose behavior you cannot control but must account for.

**Level 1 DFD:**
Decomposes the data platform into major subsystems:

```
[Source Systems] --> (Ingestion Layer) --> [Raw Data Lake]
[Raw Data Lake] --> (Transformation Layer) --> [Curated Data Warehouse]
[Curated Data Warehouse] --> (Serving Layer) --> [Consumers]
[All Components] --> (Orchestration/Metadata) --> [Monitoring]
```

Purpose: Identify trust boundaries between layers and data classification transitions. The raw-to-curated boundary is critical — raw data has unknown integrity; curated data is trusted.

**Level 2 DFD:**
Decomposes individual subsystems with full detail:

```
Ingestion Layer Detail:
[Postgres CDC] --> (Debezium) --> [Kafka Raw Topic]
[REST API] --> (API Gateway) --> (Validation Service) --> [Kafka Raw Topic]
[SFTP Drop] --> (File Watcher) --> (Schema Validator) --> [Kafka Raw Topic]
[Kafka Raw Topic] --> (Schema Registry Validation) --> [Kafka Validated Topic]
```

Purpose: Identify specific technology-level threats. Each component can now be STRIDE-analyzed individually.

### 2.3 Trust Boundaries in Data Architectures

Trust boundaries represent transitions between different security domains. In data systems, these commonly occur at:

**Network boundaries:**
- Public internet ↔ DMZ (API ingestion endpoints)
- DMZ ↔ Internal network (data processing zone)
- Internal network ↔ Database network (restricted data stores)
- On-premises ↔ Cloud (hybrid data architectures)

**Organizational boundaries:**
- Source team ↔ Data platform team (data contracts)
- Data platform ↔ Consumer teams (access policies)
- Your organization ↔ Third-party data providers
- Production ↔ Development/staging environments

**Data classification boundaries:**
- Public data zone ↔ Internal data zone
- Internal zone ↔ Confidential/PII zone
- Confidential zone ↔ Restricted/secrets zone

**Privilege boundaries:**
- Read-only access ↔ Read-write access
- Row-level filtered ↔ Unfiltered access
- Aggregated/anonymized ↔ Raw/identified data

**Critical principle:** Every trust boundary crossing must be threat-modeled. Data crossing a boundary must be validated, authenticated, and authorized at the receiving side. Never assume upstream systems have validated data — validate at ingestion.

### 2.4 DFD for ETL/ELT Pipelines

ETL pipelines have specific DFD characteristics:

```
Trust Boundary: Source Network
┌─────────────────────────────────────┐
│ [OLTP Database]                      │
│ [Application Logs]                   │
│ [Third-Party API]                    │
└─────────────────────────────────────┘
          │ (CDC / API Pull / File Drop)
          ▼
Trust Boundary: Ingestion Zone
┌─────────────────────────────────────┐
│ (Connector/Extractor)                │
│ (Schema Validation)                  │
│ [Landing Zone / Raw Storage]         │
└─────────────────────────────────────┘
          │ (Raw events/files)
          ▼
Trust Boundary: Processing Zone
┌─────────────────────────────────────┐
│ (Transformation Engine)              │
│ (Quality Checks)                     │
│ (Enrichment/Joins)                   │
│ [Staging Tables]                     │
└─────────────────────────────────────┘
          │ (Validated, transformed data)
          ▼
Trust Boundary: Serving Zone
┌─────────────────────────────────────┐
│ [Data Warehouse / Marts]             │
│ (Access Control Layer)               │
│ (Query Engine)                       │
└─────────────────────────────────────┘
          │ (Query results)
          ▼
Trust Boundary: Consumer Network
┌─────────────────────────────────────┐
│ [BI Tools]                           │
│ [ML Feature Store]                   │
│ [Application APIs]                   │
└─────────────────────────────────────┘
```

### 2.5 DFD for Streaming Architectures

Streaming architectures have additional complexity due to continuous data flow:

```
[Producers] --> (Message Broker Cluster) --> (Stream Processors) --> [Sinks]
                     │                            │
                     ▼                            ▼
              [Topic Storage]              [State Stores]
                     │
                     ▼
              (Consumer Groups) --> [Downstream Services]
```

Key differences from batch:
- Data flows are continuous, not discrete jobs
- State management introduces additional data stores
- Exactly-once semantics require coordination protocols
- Backpressure mechanisms become attack surfaces (overwhelm and bypass)

### 2.6 Diagramming Tools

**OWASP Threat Dragon:**
- Open source, web-based
- Built-in STRIDE-per-element support
- JSON-based threat model files (version-controllable)
- Generates threat lists from diagram elements automatically
- Limited but improving data-system-specific templates

**Microsoft Threat Modeling Tool (TMT):**
- Windows-only desktop application
- Mature template system with Azure-specific data service stencils
- Generates threats automatically based on element types and data flows
- Templates for Azure Data Factory, Cosmos DB, SQL Database
- Custom templates possible for on-prem data stacks

**draw.io / diagrams.net:**
- General-purpose but highly flexible
- Threat modeling template libraries available
- Good for custom data architecture diagrams
- No automated threat generation (manual process)
- Exports to multiple formats, integrates with Confluence/GitHub

**Threagile:**
- YAML-based threat model definition
- Generates DFDs and risk reports programmatically
- CI/CD integration via Docker container
- Technology-agnostic but requires manual threat rule definition
- Good for infrastructure-as-code teams

**pytm:**
- Python library for defining threat models as code
- Generates DFDs, STRIDE analysis, and reports
- Excellent for data engineering teams already using Python
- Version-controllable threat models
- Custom rules engine for data-specific threats

---

## 3. STRIDE Applied to Databases

### 3.1 Spoofing (Authentication Bypass)

**Threat:** An attacker assumes the identity of a legitimate database user or service account.

**Attack vectors:**

1. **Credential theft:**
   - Hardcoded credentials in pipeline code, configuration files, or environment variables accessible to unauthorized users
   - Credentials in version control history (even after rotation, git history retains them)
   - Memory dumps from application servers revealing connection strings
   - Credential stuffing against database authentication endpoints

2. **Authentication bypass:**
   - Default credentials left unchanged (postgres/postgres, sa/sa, root with no password)
   - Trust-based authentication misconfigurations (pg_hba.conf with `trust` method)
   - Certificate validation disabled in TLS connections
   - Exploiting authentication protocol weaknesses (older PostgreSQL md5 vs. scram-sha-256)

3. **Token/session hijacking:**
   - Stealing connection pool tokens
   - Replaying authentication tokens from network captures
   - Exploiting connection pooler (PgBouncer) session sharing

**PostgreSQL-specific spoofing threats:**
- `pg_hba.conf` configured with overly permissive host ranges (0.0.0.0/0 trust)
- PAM module misconfiguration allowing authentication bypass
- LDAP injection in LDAP-authenticated PostgreSQL deployments
- Replication slot credentials providing full cluster access

### 3.2 Tampering (Data Integrity Attacks)

**Threat:** Unauthorized modification of data at rest, in transit, or during processing.

**Attack vectors:**

1. **SQL injection:**
   - Classic SQL injection in application queries
   - Second-order SQL injection (stored payload triggers later)
   - Injection through ETL pipeline parameters
   - Template injection in dynamically generated queries (dbt Jinja templates)

2. **Direct data modification:**
   - Compromised service account executing UPDATE/DELETE
   - Trigger manipulation to alter data silently during normal operations
   - Extension exploitation (malicious PostgreSQL extensions)
   - Physical/logical replication manipulation (corrupting replica to affect failover)

3. **Schema tampering:**
   - Unauthorized DDL changes altering column types (silently truncating data)
   - Function/procedure replacement with malicious versions
   - View modification to filter or alter results
   - Index manipulation to degrade query performance or influence query plans

**PostgreSQL-specific tampering:**
- Modification of `pg_catalog` system tables
- Abuse of `SECURITY DEFINER` functions to execute with elevated privileges
- Exploitation of writable Common Table Expressions (CTEs) for data modification
- Logical decoding plugin manipulation to alter replication stream

### 3.3 Repudiation (Audit Evasion)

**Threat:** An attacker performs malicious actions and erases or prevents evidence of those actions.

**Attack vectors:**

1. **Log manipulation:**
   - Truncating or deleting PostgreSQL log files
   - Modifying `pg_audit` extension configuration to reduce logging
   - Changing `log_statement` setting to suppress query logging
   - Exploiting log rotation to cause evidence loss

2. **Transaction forgery:**
   - Using `RESET` or `SET ROLE` to obfuscate acting user
   - Executing through connection pooler that logs only pool user (not actual user)
   - Exploiting `SET SESSION AUTHORIZATION` after initial authentication

3. **Audit trail circumvention:**
   - Disabling audit triggers before malicious operations
   - Using `pg_bypass_rls` to avoid row-level security without logging
   - Manipulating `xact_start` and transaction metadata
   - Direct file-system manipulation of WAL segments

**PostgreSQL-specific repudiation:**
- Alter system to change `logging_collector` dynamically
- Exploit superuser access to modify `pg_stat_statements` data
- Manipulate `track_activities` to hide current queries from `pg_stat_activity`

### 3.4 Information Disclosure (Data Leaks)

**Threat:** Unauthorized access to data, metadata, or system information.

**Attack vectors:**

1. **Direct data exposure:**
   - Over-permissive GRANT statements exposing tables to unauthorized roles
   - Missing row-level security allowing cross-tenant data access
   - View definitions leaking through `information_schema`
   - Backup files stored without encryption

2. **Inference attacks:**
   - Aggregation queries revealing individual records (group size = 1)
   - Timing-based inference (query response time reveals record existence)
   - Error message information leakage (column names, table structure)
   - Statistical inference through repeated queries with different parameters

3. **Side-channel leaks:**
   - `pg_stat_statements` revealing query patterns and parameters
   - `pg_stat_user_tables` exposing access patterns
   - WAL files containing full data changes in plaintext
   - Shared memory inspection revealing query buffers

**PostgreSQL-specific disclosure:**
- `COPY TO` exploited to write data to attacker-accessible filesystem locations
- Foreign Data Wrappers (FDW) configured to exfiltrate data to external servers
- `dblink` extension enabling cross-database data access
- `pg_read_file` and `pg_ls_dir` exposing filesystem contents

### 3.5 Denial of Service (Availability Attacks)

**Threat:** Making the database unavailable or degrading its performance to unusable levels.

**Attack vectors:**

1. **Resource exhaustion:**
   - Connection pool exhaustion through slow queries or connection leaking
   - Memory exhaustion via large `work_mem` allocations in parallel queries
   - Disk exhaustion through uncontrolled table/index bloat or TOAST expansion
   - CPU saturation through expensive query plans (nested loop on large tables)

2. **Lock contention:**
   - Long-running transactions holding `ACCESS EXCLUSIVE` locks
   - Deadlock induction through carefully crafted concurrent operations
   - Advisory lock exhaustion
   - Autovacuum blocking through transaction ID wraparound approach

3. **Replication disruption:**
   - WAL generation flooding overwhelming standby replication
   - Replication slot retention causing WAL accumulation until disk full
   - Network partitioning between primary and replicas
   - Corrupting replication origin data

**PostgreSQL-specific DoS:**
- Transaction ID wraparound forcing emergency autovacuum (freezes writes)
- `pg_terminate_backend` abuse by over-privileged users
- Extension crash bugs taking down the entire cluster
- Recursive CTE without termination condition

### 3.6 Elevation of Privilege (Authorization Bypass)

**Threat:** Gaining higher permissions than intended.

**Attack vectors:**

1. **Role escalation:**
   - Exploiting `CREATEROLE` privilege to create superuser roles
   - Inheriting permissions through role membership chains
   - Exploiting `SECURITY DEFINER` functions that execute as owner
   - Manipulating `search_path` to hijack function calls

2. **Privilege abuse:**
   - `pg_execute_server_program` granting OS command execution
   - `pg_read_server_files` / `pg_write_server_files` providing filesystem access
   - Extension loading providing arbitrary code execution
   - Custom C functions in shared libraries

3. **Configuration exploitation:**
   - Modifying `postgresql.conf` via SQL (`ALTER SYSTEM`)
   - Loading malicious shared libraries via `shared_preload_libraries`
   - Exploiting `pg_hba.conf` reload race conditions
   - Abusing `pg_signal_backend` for process manipulation

**PostgreSQL full example threat model:**

```
Asset: PostgreSQL 16 cluster with customer PII
Deployment: AWS RDS Multi-AZ
Access: Application via connection pooler, analysts via SQL client

STRIDE Assessment:
┌────────────────┬────────────────────────────────────────────────┐
│ S - Spoofing   │ RDS IAM auth disabled; uses md5 passwords      │
│                │ Connection pooler obscures actual user identity │
│                │ Service account credentials in Parameter Store  │
├────────────────┼────────────────────────────────────────────────┤
│ T - Tampering  │ Application has INSERT/UPDATE on PII tables     │
│                │ No data checksums enabled (data_checksums=off)  │
│                │ dbt models run as privileged transformation user│
├────────────────┼────────────────────────────────────────────────┤
│ R - Repudiation│ pgAudit not installed; only basic logging       │
│                │ Connection pooler logs only pool user            │
│                │ CloudWatch logs retention = 7 days only         │
├────────────────┼────────────────────────────────────────────────┤
│ I - Disclosure │ Analysts have SELECT on all schemas             │
│                │ No RLS; multi-tenant data in shared tables      │
│                │ Automated backups accessible to broad IAM role  │
├────────────────┼────────────────────────────────────────────────┤
│ D - DoS        │ No connection limits per user/role              │
│                │ No statement timeout configured                 │
│                │ No query kill automation for runaway queries    │
├────────────────┼────────────────────────────────────────────────┤
│ E - Elevation  │ Application role inherits from admin role       │
│                │ search_path not locked per session              │
│                │ Analysts can create functions in public schema  │
└────────────────┴────────────────────────────────────────────────┘
```

---

## 4. STRIDE Applied to Data Pipelines

### 4.1 Threats at Each Pipeline Stage

**Ingestion Stage:**
- S: Spoofed data sources sending malicious or fabricated data
- T: Data modified between source and landing zone (MITM on CDC stream)
- R: No provenance tracking for ingested records (cannot prove source)
- I: Credentials for source systems exposed in connector configuration
- D: Source system overload from aggressive extraction queries
- E: Connector service account with excessive source system privileges

**Transformation Stage:**
- S: Unauthorized job execution masquerading as scheduled pipeline
- T: Transformation logic modification (altered dbt model, compromised UDF)
- R: No lineage tracking between input and output datasets
- I: Intermediate results stored unencrypted in temporary storage
- D: Resource exhaustion in compute cluster from malicious workloads
- E: Transformation job running with production-write access when only read needed

**Load Stage:**
- S: Impersonation of the loading process to inject unauthorized data
- T: Data corruption during write (schema mismatch, encoding errors weaponized)
- R: Loaded data cannot be traced back to transformation that produced it
- I: Load process reveals schema/structure of target system through error messages
- D: Bulk load overwhelming target system (lock contention, WAL explosion)
- E: Load account with DDL privileges enabling schema modification

**Serving Stage:**
- S: Impersonating authorized consumers to access restricted data products
- T: Query result modification (e.g., through compromised materialized views)
- R: No query audit trail for data access patterns
- I: Over-exposed data through insufficient column/row filtering
- D: Query amplification attacks through expensive analytical queries
- E: Self-service query tools allowing privilege escalation via SQL

### 4.2 Kafka Threats

Apache Kafka is central to modern streaming data architectures, making it a high-value target:

**Message Forgery (Spoofing/Tampering):**
- Producers without SASL authentication can publish to any topic
- Message headers can be forged (no integrity verification by default)
- Schema Registry bypass — publishing messages that violate schemas
- Idempotent producer keys can be hijacked to overwrite legitimate messages

**Topic Hijacking (Elevation/Tampering):**
- Auto-topic creation allowing attackers to create topics matching expected names
- Topic ACL misconfiguration granting broad WRITE access
- Compacted topics manipulated to delete legitimate records via tombstones
- Topic configuration alteration (reducing retention to cause data loss)

**Consumer Group Manipulation (DoS/Spoofing):**
- Joining a consumer group to steal partition assignments from legitimate consumers
- Committing false offsets to cause data skipping or reprocessing
- Consumer group ID squatting preventing legitimate service startup
- Static membership impersonation to hijack partition assignments

**Kafka-specific attack chains:**
```
Attack: Silent data exfiltration via Kafka
1. Gain network access to Kafka cluster (internal network compromise)
2. Create consumer group with topic READ access (if ACLs are permissive)
3. Subscribe to sensitive topics from beginning offset
4. Exfiltrate historical data through consumer
5. Cover tracks by deleting consumer group offsets

Attack: Data poisoning via Kafka
1. Obtain producer credentials (leaked in config/env)
2. Produce malformed messages to input topics
3. Downstream consumers process poisoned data
4. Data corruption propagates through pipeline
5. Detection delayed if no schema validation at consumer
```

**Kafka hardening requirements identified through threat model:**
- SASL/SCRAM or mTLS for all client authentication
- ACLs enforced at topic level (separate READ/WRITE/DESCRIBE)
- Schema Registry with FULL_TRANSITIVE compatibility and producer validation
- Disable auto-topic creation in production
- Enable audit logging for all administrative operations
- Network segmentation between Kafka and untrusted networks

### 4.3 Airflow Threats

Apache Airflow orchestrates data pipelines and holds the keys to the kingdom:

**DAG Injection (Tampering/Elevation):**
- DAG files stored in writable git repositories — commit access = code execution
- DAG serialization vulnerabilities allowing Python code injection
- Custom operators with arbitrary code execution capabilities
- DAG file parsing executing Python at import time (not just at execution)
- Template rendering (Jinja) vulnerabilities in dynamic task parameters

**Connection Credential Exposure (Information Disclosure):**
- Airflow metadata database stores connection credentials (encrypted, but key accessible)
- `airflow connections get` CLI exposing credentials to authorized CLI users
- Fernet key extraction from airflow.cfg granting access to all stored secrets
- Web UI exposing connection details to users with connection-view permission
- Extra fields in connections storing sensitive data in non-standard locations

**Worker Compromise (All STRIDE categories):**
- Celery/Kubernetes workers executing arbitrary task code
- Worker pods with mounted service accounts having broad cluster access
- Shared executor model — tasks from different DAGs share runtime environment
- Worker environment variables leaking credentials between tasks
- Container escape from worker to host node

**Airflow-specific attack chains:**
```
Attack: Pipeline manipulation via Airflow
1. Obtain Airflow web UI access (weak auth, RBAC misconfiguration)
2. Modify DAG variable to alter transformation logic
3. Trigger DAG run with manipulated parameters
4. Pipeline executes modified logic on production data
5. Results appear normal but contain attacker-controlled modifications

Attack: Lateral movement via Airflow connections
1. Compromise Airflow worker (malicious task code)
2. Access Airflow metadata database (worker has connection details)
3. Extract Fernet key from configuration
4. Decrypt all stored connections (databases, cloud accounts, APIs)
5. Use credentials for lateral movement to data systems
```

### 4.4 Spark Threats

Apache Spark processes massive datasets and presents unique threat surfaces:

**Executor Manipulation (Tampering/Elevation):**
- Malicious UDFs executing arbitrary code on executors
- Executor-to-driver communication interception
- Spark history server exposing job configurations and environment variables
- Dynamic resource allocation exploitation — requesting excessive executors
- Custom data sources with embedded malicious code

**Shuffle Data Interception (Information Disclosure):**
- Shuffle data transferred between executors in plaintext by default
- External shuffle service accessing disk-persisted shuffle files
- Spill-to-disk writing unencrypted intermediate data to local storage
- Broadcast variables containing sensitive data distributed to all executors

**Spark-specific threats in data pipelines:**
- Job submission API without authentication (spark-submit to cluster)
- Notebook environments (Jupyter/Zeppelin) with Spark context and broad access
- Delta Lake / Iceberg table manipulation through direct filesystem access
- Spark SQL catalog exploitation — accessing metadata for unauthorized tables
- Driver log files containing query plans with sensitive filter values

**Spark cluster threat model:**
```
Trust Boundaries:
- Client network → Spark cluster network
- Driver → Executor communication
- Executor → Storage layer
- Spark → Metastore (Hive/Glue/Unity Catalog)

High-priority threats:
1. Unauthorized job submission → arbitrary code execution on cluster
2. Shuffle interception → data exposure for join operations on PII
3. History server → credential/config exposure from completed jobs
4. Catalog bypass → direct storage access circumventing access controls
```

---

## 5. Data-Specific Threat Categories

### 5.1 Data Poisoning

Data poisoning introduces malicious data designed to corrupt downstream processes:

**Training Data Manipulation:**
- Injecting adversarial examples into ML training datasets
- Label flipping to degrade model accuracy on targeted inputs
- Backdoor injection — embedding trigger patterns that cause specific model behaviors
- Gradual drift injection — slowly shifting data distribution to degrade model over time

**Business Data Poisoning:**
- Fabricating transactions to influence business metrics and decisions
- Injecting false sensor readings in IoT data pipelines
- Manipulating feature store data to affect real-time ML serving
- Corrupting reference data (lookup tables, configuration data) used in transformations

**Detection challenges:**
- Poisoned data often appears statistically normal in isolation
- Effects manifest downstream, far from injection point
- Volume-based attacks hide in normal data variance
- Slow-drip poisoning stays within statistical control limits

**Pipeline points vulnerable to poisoning:**
- Ingestion from untrusted sources without validation
- User-generated content pipelines
- Web scraping pipelines without content verification
- IoT/sensor data without device attestation
- Third-party data feeds without integrity checks

### 5.2 Data Exfiltration

Data exfiltration extracts data from the organization without authorization:

**Bulk Extraction:**
- Unauthorized `SELECT *` or `COPY TO` operations on large tables
- Database dump commands (pg_dump) by compromised accounts
- Export functionality abuse in BI/analytics tools
- API pagination abuse for large-scale data retrieval
- Replication stream tapping for continuous data access

**Slow-Drip Exfiltration:**
- Small queries over time that collectively extract entire datasets
- DNS exfiltration encoding data in DNS queries from data systems
- Steganographic embedding of data in normal query results
- Abusing allowed outbound connections (HTTPS to attacker-controlled endpoint)
- Timing-channel exfiltration through query response time modulation

**Pipeline-specific exfiltration vectors:**
- Adding unauthorized sinks to pipeline configurations
- Modifying transformation logic to copy data to secondary storage
- Exploiting pipeline error handling to redirect data to error queues monitored by attacker
- Abusing data lineage/catalog systems that store sample data
- Cloud storage replication to attacker-controlled accounts

### 5.3 Data Corruption

Data corruption degrades data quality, potentially undetected:

**Silent Data Loss:**
- Schema changes causing implicit data truncation
- Character encoding mismatches silently corrupting text fields
- Timezone handling errors corrupting temporal data
- Numeric overflow/underflow in transformation calculations
- NULL handling inconsistencies between pipeline stages

**Schema Drift:**
- Upstream schema changes breaking downstream consumers
- Undetected column additions/removals affecting JOIN operations
- Data type changes causing implicit casting and precision loss
- Schema evolution without backward compatibility
- Metadata desynchronization between catalog and actual storage

**Weaponized corruption:**
- Deliberately introducing subtle errors in financial data
- Corrupting audit trails to undermine forensic capabilities
- Modifying historical data to alter trend analyses
- Breaking referential integrity to compromise downstream aggregations

### 5.4 Data Inference (Statistical Attacks)

**Membership Inference:**
- Determining whether a specific record exists in a dataset
- Exploiting aggregate queries with small group sizes
- Differencing attacks between versions of published statistics
- Model output analysis revealing training data membership

**Model Inversion:**
- Reconstructing input features from model outputs
- Exploiting confidence scores to infer sensitive attributes
- API-based extraction of training data through carefully crafted queries
- Gradient-based reconstruction attacks on ML models

**Linkage Attacks:**
- Combining anonymized datasets with public data for re-identification
- Exploiting quasi-identifiers (age + zip + gender) for uniqueness
- Temporal correlation enabling record linkage across datasets
- Network/graph analysis revealing identities in social data

**Database-specific inference:**
- Aggregate function exploitation (COUNT/SUM/AVG on small groups)
- Query-based inference (if WHERE condition returns 0 rows → individual data revealed)
- Error-based inference (constraint violations revealing data existence)
- Timing-based inference (index scan vs sequential scan revealing data patterns)

### 5.5 Supply Chain Threats

**Malicious Data Sources:**
- Compromised third-party data providers injecting malicious data
- Supply chain attacks on data connector libraries (malicious package updates)
- Man-in-the-middle between data provider and ingestion endpoint
- Trojanized data feeds that appear legitimate but contain embedded threats

**Compromised Connectors:**
- Backdoored database connectors (JDBC/ODBC drivers)
- Supply chain attacks on ETL tool plugins (Airbyte connectors, Fivetran)
- Malicious Python packages in data processing dependencies
- Compromised container images for pipeline workers

**Infrastructure supply chain:**
- Malicious AMIs/container images for data infrastructure
- Compromised Terraform/CloudFormation modules for data services
- Backdoored Helm charts for data platform components
- Poisoned package mirrors used during build processes

---

## 6. Cloud Data Architecture Threats

### 6.1 S3 Bucket Misconfiguration

S3 (and equivalent object storage) misconfigurations remain one of the most common and impactful cloud data threats:

**Public access:**
- Bucket policy allowing `s3:GetObject` to principal `*`
- ACL granting `READ` to `AllUsers` or `AuthenticatedUsers`
- Static website hosting enabled on buckets containing sensitive data
- CloudFront/CDN origin configured to expose entire bucket

**Cross-account leakage:**
- Bucket policies with overly broad principal specifications (wildcarded account IDs)
- VPC endpoint policies not restricting S3 access to intended buckets
- Replication rules copying data to less-secure accounts
- Pre-signed URLs with excessively long expiration

**Data exposure through metadata:**
- Object listing enabled revealing file names with sensitive information
- Object tags containing classification data visible to unauthorized parties
- Bucket inventory files stored in accessible locations
- S3 access logs revealing data access patterns

**Object storage attack chain:**
```
1. Enumerate buckets (DNS brute-force, certificate transparency logs)
2. Test public access (GET bucket, list objects)
3. Check authenticated access (AWS credentials from other compromise)
4. Exploit overly permissive bucket policies
5. Access data objects, prioritizing known-sensitive paths
6. Establish persistence via bucket notification to attacker's Lambda
```

### 6.2 IAM Over-Permission

IAM misconfigurations are the most dangerous cloud data threat because they multiply the impact of any other compromise:

**Overly broad data access:**
- `s3:*` on `Resource: *` for data pipeline roles
- Database admin roles assigned to application service accounts
- `glue:*` permissions allowing catalog manipulation
- Analytics roles with `athena:*` enabling queries across all data

**Privilege escalation paths:**
- IAM roles that can modify their own policies
- `iam:PassRole` allowing assumption of more powerful roles
- Service-linked role exploitation for cross-service access
- Lambda execution roles with broader access than the function needs

**Service account sprawl:**
- Shared service accounts across multiple pipelines
- Service accounts with access to both production and development data
- Long-lived access keys without rotation
- Service accounts without MFA enforcement for human-interactive use

### 6.3 Cross-Account Access Abuse

**Legitimate patterns exploited:**
- Cross-account roles for data sharing exploited via confused deputy
- Resource-based policies with external account access persisting after relationship ends
- AWS Organizations SCP gaps allowing member account abuse
- Shared VPC endpoints providing unintended cross-account data access

**Data lake specific:**
- Lake Formation permissions granting cross-account catalog access
- Glue Data Catalog resources shared beyond intended scope
- Cross-account KMS key policies enabling decryption by unauthorized accounts
- S3 bucket policies with conditions that can be manipulated

### 6.4 Data Lake Poisoning

**Attack surface unique to data lakes:**
- Permissive write access to raw zones enabling injection of malicious files
- Absence of schema enforcement at ingestion (schema-on-read vulnerability)
- Partition manipulation — injecting data into unexpected partitions
- Metadata manipulation — altering Glue/Hive catalog entries to point to attacker-controlled data
- Table format exploitation (Delta Lake transaction log manipulation, Iceberg manifest poisoning)

**Impact amplification:**
- Poisoned raw data propagates through all downstream transformations
- Historical queries affected if data lake stores immutable history (time travel poisoned)
- ML model training on poisoned lake data affects production predictions
- Data lineage makes poisoning discoverable but not automatically preventable

### 6.5 Serverless Injection

**Lambda/Cloud Function threats in data pipelines:**
- Event injection — crafting S3 events, Kinesis records, or SQS messages to trigger malicious execution
- Dependency confusion — malicious packages in Lambda layers
- Environment variable access — Lambda execution environment leaking secrets
- Temporary credential abuse — Lambda role credentials accessible during execution window
- Cold start exploitation — initialization code executing with different permissions than runtime

**Step Functions / workflow threats:**
- State machine definition manipulation to alter pipeline flow
- Input/output processing exploitation to bypass validation
- Parallel state manipulation to execute unauthorized branches
- Retry mechanism abuse to amplify operations

### 6.6 Shared Responsibility Model Gaps

| Layer | Cloud Provider Responsibility | Customer Responsibility | Common Gap |
|-------|-------------------------------|------------------------|------------|
| Physical infrastructure | Hardware, facilities, networking | None | N/A |
| Managed service availability | Service uptime, patching | Configuration, access control | Customer assumes provider handles auth |
| Data encryption | Encryption in transit (default) | Encryption at rest, key management | Data written to unencrypted storage |
| Network security | VPC isolation, DDoS protection | Security groups, NACLs, endpoint policies | Overly permissive security groups |
| Data classification | None | Identifying, classifying, protecting data | No classification applied to lake data |
| Backup/recovery | Service-level backup (if configured) | Backup strategy, testing, cross-region | Backups not tested, single-region |
| Access management | IAM service operation | Policy definition, least privilege | Over-permissive policies, no review |
| Audit/compliance | Service logs (CloudTrail, etc.) | Log analysis, alerting, compliance mapping | Logs collected but not analyzed |

### 6.7 Metadata Service Exploitation (IMDS Attacks)

**Instance Metadata Service (IMDS) on data workers:**

IMDS v1 is vulnerable to SSRF — any service running on an EC2 instance (or ECS task on EC2) that can make HTTP requests can reach `169.254.169.254`:

**Attack scenario on data workers:**
```
1. Inject crafted data into pipeline that triggers URL fetch (many ETL tools have this)
2. URL points to http://169.254.169.254/latest/meta-data/iam/security-credentials/
3. Worker fetches URL as part of "data processing"
4. Response contains temporary IAM credentials for the worker's role
5. Credentials exfiltrated via normal data flow (written to output, logged in error)
6. Attacker uses credentials for broader AWS access
```

**Why data systems are especially vulnerable:**
- Data pipelines frequently fetch URLs as part of ingestion
- ETL tools often process user-supplied configurations including URLs
- Notebook environments allow arbitrary HTTP requests
- Many data tools don't implement IMDSv2 (hop-count protection)

**Mitigation requirements:**
- Enforce IMDSv2 (HttpTokens=required) on all data processing instances
- Set hop limit to 1 for containerized workloads
- Never allow pipeline-processed data to trigger arbitrary HTTP fetches
- Use VPC endpoints instead of NAT for AWS service access from data workers

---

## 7. Risk Assessment and Prioritization

### 7.1 DREAD Scoring

DREAD provides a simple 1-10 scoring for each dimension:

| Dimension | Data System Scoring Criteria |
|-----------|------------------------------|
| **D**amage | Volume and sensitivity of affected data (PII = high, public metadata = low) |
| **R**eproducibility | Can the attack be repeated? (Misconfiguration = always reproducible = 10) |
| **E**xploitability | Skill/tools required (public exploit = 10, novel research = 1) |
| **A**ffected Users | Number of data subjects impacted (all customers = 10, internal = 3) |
| **D**iscoverability | How easily found? (Shodan-visible = 10, requires internal access = 3) |

**Example DREAD for "S3 bucket with PII publicly accessible":**
- Damage: 9 (full PII exposure, regulatory fines)
- Reproducibility: 10 (misconfiguration is static)
- Exploitability: 10 (browser-accessible, no tools needed)
- Affected Users: 10 (all customers)
- Discoverability: 8 (bucket enumeration tools exist, certificate transparency)
- **Score: 47/50 — Critical**

**Example DREAD for "Spark shuffle data interception":**
- Damage: 6 (partial data from specific job only)
- Reproducibility: 7 (requires network position + active job)
- Exploitability: 4 (requires internal network access + timing)
- Affected Users: 5 (depends on data being processed)
- Discoverability: 3 (requires internal knowledge of cluster architecture)
- **Score: 25/50 — Medium**

### 7.2 CVSS for Data Systems

CVSS v3.1 base metrics applied to data infrastructure:

**Attack Vector (AV):**
- Network (N): Data API exposed to internet, public database endpoint
- Adjacent (A): Requires same network segment as data cluster
- Local (L): Requires shell on data processing node
- Physical (P): Physical access to storage media

**Attack Complexity (AC):**
- Low (L): Misconfiguration exploitable without special conditions
- High (H): Requires specific pipeline state, timing, or race condition

**Privileges Required (PR):**
- None (N): No authentication needed
- Low (L): Authenticated user with basic data access
- High (H): Privileged operator/admin access needed

**User Interaction (UI):**
- None (N): Fully automated exploitation
- Required (R): Needs victim action (e.g., clicking malicious report link)

**Impact metrics for data systems:**
- Confidentiality: Based on data classification level exposed
- Integrity: Based on whether data can be trusted after attack
- Availability: Based on data freshness SLA impact

### 7.3 Risk Matrices for Data Systems

**Likelihood factors specific to data systems:**

| Factor | Low (1-3) | Medium (4-6) | High (7-9) |
|--------|-----------|--------------|------------|
| Exposure | Internal-only system | VPN-accessible | Internet-facing |
| Data value | Public/non-sensitive | Internal/business | PII/financial/regulated |
| Attacker motivation | No known targeting | Industry-wide campaigns | Active targeting of org |
| Existing controls | Defense-in-depth | Some controls | Minimal security |
| Complexity | Requires chained exploits | Single vulnerability | Configuration error |

**Impact factors:**

| Factor | Low (1-3) | Medium (4-6) | High (7-9) |
|--------|-----------|--------------|------------|
| Data volume | <1000 records | 1K-1M records | >1M records |
| Sensitivity | Public metadata | Internal business | PII/PHI/financial |
| Regulatory exposure | None | Contractual (SLA) | GDPR/HIPAA/PCI |
| Business disruption | Single report delayed | Pipeline SLA miss | Production data loss |
| Recovery complexity | Automated recovery | Manual restore <4h | Requires rebuild >24h |

**Risk score = Likelihood × Impact**

| | Impact Low (1-3) | Impact Med (4-6) | Impact High (7-9) |
|---|---|---|---|
| **Likelihood High (7-9)** | Medium (7-27) | High (28-54) | Critical (49-81) |
| **Likelihood Med (4-6)** | Low (4-18) | Medium (16-36) | High (28-54) |
| **Likelihood Low (1-3)** | Informational (1-9) | Low (4-18) | Medium (7-27) |

### 7.4 Risk Appetite Definition

Data system risk appetite must account for:

**Data tiering:**
- Tier 1 (Crown jewels): Zero tolerance for unauthorized access. Customer PII, financial records, credentials. Accept significant cost for protection.
- Tier 2 (Sensitive business): Low tolerance for unauthorized access. Business metrics, internal analytics, employee data. Accept moderate cost.
- Tier 3 (Internal): Moderate tolerance. Aggregated metrics, non-sensitive configurations. Protect with standard controls.
- Tier 4 (Public): High tolerance for exposure. Published data, public APIs, marketing materials. Minimal security investment.

**Risk appetite statements for data leadership:**
- "We accept no more than X hours of data unavailability per quarter"
- "We invest up to Y% of data platform budget in security controls"
- "PII exposure of more than Z records triggers mandatory incident response"
- "We will not operate data systems without encryption at rest for Tier 1/2 data"

### 7.5 Threat Prioritization with Business Context

Not all threats are equal. Prioritization requires business context:

**Priority factors:**
1. Regulatory penalty exposure (GDPR: up to 4% annual revenue)
2. Customer trust impact (breach notification requirements)
3. Competitive intelligence exposure (proprietary algorithms, business data)
4. Operational continuity (revenue-impacting data pipelines)
5. Recovery cost and time (rebuild vs. restore)

**Prioritization framework:**
```
Priority Score = Base Risk Score × Business Multiplier

Business Multipliers:
- Regulatory data (PII, PHI, PCI): ×2.0
- Revenue-critical pipeline: ×1.5
- Customer-facing data product: ×1.5
- No detective control exists: ×1.3
- Exploit publicly known: ×1.5
- Previously exploited in industry: ×1.8
```

### 7.6 Cost-Benefit Analysis of Mitigations

Every mitigation has a cost. Threat modeling justifies security investments:

**Annual Loss Expectancy (ALE):**
```
ALE = Single Loss Expectancy (SLE) × Annual Rate of Occurrence (ARO)

Example: Database breach
SLE = $5M (regulatory fines + notification + reputation + forensics)
ARO = 0.1 (10% chance per year based on industry data)
ALE = $500K

If encryption at rest + access controls + monitoring costs $200K/year:
ROI = ($500K - $200K) / $200K = 150%
→ Investment justified
```

**Mitigation efficiency ranking:**
- Configuration hardening: Low cost, medium risk reduction (do first)
- Access control refinement: Low cost, high risk reduction (do first)
- Encryption: Medium cost, high risk reduction (high priority)
- Network segmentation: Medium cost, medium risk reduction (scheduled)
- Advanced monitoring: High cost, medium risk reduction (justified for Tier 1)
- Zero trust architecture: High cost, high risk reduction (multi-year initiative)

---

## 8. Mitigation Strategies

### 8.1 Defense-in-Depth for Data Layers

Defense-in-depth ensures no single control failure exposes data:

```
Layer 1: Network Controls
├── VPC segmentation (data processing, storage, serving in separate subnets)
├── Security groups restricted to minimum required flows
├── Private endpoints for all data services (no public internet access)
└── Network monitoring and anomaly detection

Layer 2: Authentication & Identity
├── Strong authentication for all data service access (mTLS, SASL, IAM)
├── Service mesh with identity-aware routing
├── Short-lived credentials with automatic rotation
└── Centralized identity provider integration

Layer 3: Authorization & Access Control
├── Least privilege at every level (table, column, row)
├── Attribute-based policies for dynamic access decisions
├── Data masking and tokenization for sensitive fields
└── Just-in-time access for privileged operations

Layer 4: Data Protection
├── Encryption at rest (AES-256, KMS-managed keys)
├── Encryption in transit (TLS 1.3, mTLS between services)
├── Data classification enforcement at storage layer
└── Backup encryption with separate key management

Layer 5: Monitoring & Detection
├── Query pattern anomaly detection
├── Data access audit logging (immutable, centralized)
├── Volume-based alerts (unusual data movement)
└── Behavioral analytics for user/service accounts

Layer 6: Response & Recovery
├── Automated incident response playbooks
├── Data backup and point-in-time recovery tested quarterly
├── Breach notification workflow automation
└── Forensic capture capability (network, logs, memory)
```

### 8.2 Zero Trust Data Architecture

Zero trust for data systems means: never trust, always verify — even for internal services.

**Principles applied to data:**
1. Verify explicitly: Every data access request authenticated and authorized regardless of network location
2. Least privilege access: Grant minimum necessary data access for minimum necessary time
3. Assume breach: Design systems assuming any component may be compromised

**Implementation patterns:**

**Identity-aware data access:**
- Every data request carries caller identity (not just "the Spark cluster wants data")
- Service-to-service authentication via mTLS or workload identity
- Human access via short-lived tokens with MFA
- No ambient authority — network location does not grant access

**Microsegmented data stores:**
- Each data product has independent access policies
- Cross-product access requires explicit grants
- No shared database accounts across pipelines
- Storage-level isolation (separate encryption keys per data classification)

**Continuous verification:**
- Session re-authentication for long-running data jobs
- Behavioral scoring for ongoing access (unusual query patterns revoke access)
- Real-time policy evaluation (not cached decisions)
- Posture-based access (device health, user risk score)

### 8.3 Encryption Boundaries

**Encryption at rest:**
- All data stores encrypted with service-managed or customer-managed keys (CMK)
- Separate KMS keys per data classification tier
- Key rotation policy (annual for data keys, automatic for DEKs via envelope encryption)
- Encryption of temporary/intermediate data (Spark scratch space, sort buffers)

**Encryption in transit:**
- TLS 1.3 for all data flows between components
- mTLS between pipeline services (client certificate authentication)
- Kafka: SSL/TLS for inter-broker and client communication
- Database connections: require SSL, verify server certificate

**Encryption in use (emerging):**
- Confidential computing for sensitive transformations
- Homomorphic encryption for analytics on encrypted data (limited applicability)
- Secure enclaves for key management operations
- Tokenization as practical alternative for high-sensitivity fields

**Key management architecture:**
```
┌─────────────────────────────────────┐
│ Root of Trust (HSM/CloudHSM)        │
├─────────────────────────────────────┤
│ Master Key (never exported)         │
├─────────────────────────────────────┤
│ KMS Key (per-service/per-env)       │
├─────────────────────────────────────┤
│ Data Encryption Key (per-object)    │
└─────────────────────────────────────┘

Envelope Encryption:
DEK encrypts data → KEK encrypts DEK → Master Key protects KEK
Only encrypted DEK stored alongside data
```

### 8.4 Access Control Models

**RBAC (Role-Based Access Control):**
```
Roles for data systems:
- data_engineer: CREATE/ALTER on staging schemas, SELECT on raw
- data_analyst: SELECT on curated schemas, no access to raw PII
- data_scientist: SELECT on feature store, WRITE to experiment schemas
- data_admin: ALL PRIVILEGES (break-glass with audit trail)
- pipeline_service: INSERT on target tables, SELECT on source

Hierarchy:
data_admin → data_engineer → data_analyst (inherits read access)
```

**ABAC (Attribute-Based Access Control):**
```
Policy: Allow access IF
- user.department == resource.data_domain
- user.clearance_level >= resource.classification
- request.time IN user.working_hours
- resource.region IN user.authorized_regions
- data.sensitivity_category NOT IN user.restricted_categories

Example:
User{role=analyst, dept=marketing, clearance=internal}
accessing Table{domain=marketing, classification=internal, region=EU}
→ ALLOW (all attributes match)

User{role=analyst, dept=marketing, clearance=internal}
accessing Table{domain=finance, classification=confidential, region=EU}
→ DENY (department mismatch + insufficient clearance)
```

**PBAC (Policy-Based Access Control):**
```
Centralized policy engine (OPA, Cedar, Oso):

package data.access

allow {
    input.action == "SELECT"
    input.resource.type == "table"
    input.resource.schema == "curated"
    input.subject.roles[_] == "analyst"
    not contains_pii(input.resource)
}

allow {
    input.action == "SELECT"
    input.resource.type == "table"
    contains_pii(input.resource)
    input.subject.has_pii_training == true
    input.subject.purpose IN input.resource.allowed_purposes
}
```

### 8.5 Input Validation at Ingestion

**Schema enforcement:**
- Validate all incoming data against registered schemas before accepting
- Reject records that violate schema (strict mode) or quarantine them
- Version schemas and enforce compatibility (backward/forward/full)
- Use schema registries (Confluent Schema Registry, AWS Glue Schema Registry)

**Content validation:**
- Range checks on numeric fields
- Pattern matching on string fields (email, phone, identifier formats)
- Referential integrity checks against known-good reference data
- Cardinality checks (expected number of records per batch)
- Temporal validation (timestamps within reasonable bounds)

**Structural validation:**
- File format verification (magic bytes, not just extension)
- Compression format validation before decompression
- Maximum record/field size limits (prevent resource exhaustion)
- Encoding verification (UTF-8 validation, no invalid byte sequences)
- Nested structure depth limits (prevent parser stack overflow)

### 8.6 Schema Enforcement

**Schema Registry patterns:**
```
Producer → Schema Registry (validate) → Kafka → Consumer
                                                    ↓
                                           Schema Registry (validate)

Compatibility modes:
- BACKWARD: New schema can read old data
- FORWARD: Old schema can read new data
- FULL: Both backward and forward compatible
- NONE: No compatibility checking (dangerous for data pipelines)

Recommendation: Use FULL_TRANSITIVE for data pipelines
(transitive = compatible with ALL previous versions, not just immediately prior)
```

**Data contract enforcement:**
- Define data contracts between producer and consumer teams
- Contracts specify schema, SLAs, quality expectations, and ownership
- Automated contract testing in CI/CD (schema changes require contract update)
- Breaking changes require version bump and consumer notification

### 8.7 Data Integrity Checksums

**Record-level integrity:**
- Hash individual records at source, verify at each pipeline stage
- Use HMAC (not plain hash) when tamper-detection is the goal
- Store checksums in separate metadata channel (not in data flow)
- SHA-256 minimum; avoid MD5/SHA-1 for integrity purposes

**Dataset-level integrity:**
- Batch manifests with record counts, checksums, and metadata
- Merkle trees for large datasets (verify subsets without full scan)
- Great Expectations or similar for statistical integrity assertions
- Row count reconciliation between pipeline stages

**End-to-end integrity:**
```
Source → Ingestion: Record HMAC + batch manifest
Ingestion → Transform: Verify manifest, produce new manifest
Transform → Load: Verify manifest, reconcile counts
Load → Serve: Verify loaded matches transformed

Any discrepancy → Alert + quarantine + investigate
Never silently drop or modify data without trace
```

### 8.8 Monitoring and Detection Controls

**Data access monitoring:**
- Log all data access (who, what, when, how much, from where)
- Baseline normal access patterns per user/service
- Alert on deviations (unusual volume, unusual tables, unusual hours)
- Correlate data access with business events (is this query justified?)

**Pipeline integrity monitoring:**
- Data quality metrics per pipeline stage (freshness, completeness, distribution)
- Schema change detection and alerting
- Transformation output validation (statistical tests on output distributions)
- Job execution anomaly detection (duration, resource usage, output volume)

**Threat detection rules:**
```
RULE: Bulk data access
IF query_result_rows > baseline_p99
AND user_type NOT IN [etl_service, batch_report]
THEN alert(severity=HIGH, type=potential_exfiltration)

RULE: Access pattern change
IF user accesses table NOT IN user_usual_tables
AND table.classification >= CONFIDENTIAL
THEN alert(severity=MEDIUM, type=anomalous_access)

RULE: Off-hours data access
IF access_time NOT IN business_hours
AND user_type == HUMAN
AND table.classification >= INTERNAL
THEN alert(severity=LOW, type=unusual_timing)

RULE: Data movement volume
IF egress_bytes > daily_baseline * 3
THEN alert(severity=HIGH, type=potential_exfiltration)
```

---

## 9. Threat Modeling Integration in SDLC

### 9.1 Threat Modeling in Agile Sprints

**When to trigger threat modeling:**
- New data source integration
- New pipeline component or transformation
- Access pattern changes (new consumers, new query paths)
- Infrastructure changes (new cloud service, network modification)
- Data classification changes (new PII field, new regulatory requirement)

**Lightweight sprint integration:**

```
Sprint Planning:
├── Review story cards for data architecture changes
├── Flag stories that cross trust boundaries
└── Allocate threat modeling time (1-2 hours per flagged story)

During Sprint:
├── Developer creates/updates DFD for changed components
├── Apply STRIDE to new/modified elements
├── Document threats in same tool as story (Jira, Linear)
└── Accept/mitigate/transfer each identified threat

Sprint Review:
├── Review new threats identified
├── Validate mitigations implemented
└── Update risk register if residual risk changed
```

**Minimum viable threat model for a sprint story:**
```
Story: "Add customer address data from CRM to data warehouse"

DFD Change: New data flow from CRM API → Ingestion → Warehouse

STRIDE Quick Assessment:
- S: CRM API authentication (API key in secret manager ✓)
- T: Data modified in transit (TLS ✓, but no end-to-end checksum ✗)
- R: Who approved adding this PII? (Data governance approval ✓)
- I: Address data is PII (Column-level access control needed ✗)
- D: CRM API rate limits (Backoff/retry implemented ✓)
- E: Ingestion service gets CRM access (least privilege verified ✓)

Action items:
1. Add checksum validation at ingestion (T)
2. Implement column-level masking for non-authorized roles (I)
```

### 9.2 Automation Tools

**pytm (Python Threat Modeling):**
```python
from pytm import TM, Server, Dataflow, Boundary, Lambda, DataStore

tm = TM("Data Pipeline Threat Model")
tm.description = "Streaming pipeline: Kafka → Flink → PostgreSQL"

# Define boundaries
internet = Boundary("Internet")
dmz = Boundary("DMZ")
processing = Boundary("Processing Zone")
data_zone = Boundary("Data Zone")

# Define elements
kafka = Server("Kafka Cluster")
kafka.inBoundary = processing
kafka.protocol = "SASL_SSL"
kafka.authenticatesSource = True

flink = Server("Flink Cluster")
flink.inBoundary = processing
flink.sanitizesInput = True

postgres = DataStore("PostgreSQL")
postgres.inBoundary = data_zone
postgres.isEncryptedAtRest = True
postgres.hasAccessControl = True

# Define flows
stream = Dataflow(kafka, flink, "Process stream")
stream.protocol = "TLS"
stream.isEncrypted = True

persist = Dataflow(flink, postgres, "Write results")
persist.protocol = "TLS"
persist.isEncrypted = True

# Generate threats
tm.process()
```

**Threagile (YAML-based):**
```yaml
title: Data Lake Architecture
technical_assets:
  kafka-cluster:
    type: process
    technology: message-broker
    encryption: transparent
    authentication: credentials
    multi_tenant: true
    communication_links:
      produces-to-raw-topic:
        target: s3-raw-zone
        protocol: https
        authentication: token
        
  s3-raw-zone:
    type: datastore
    technology: object-storage
    encryption: transparent
    data_assets_stored:
      - raw-customer-data
    
data_assets:
  raw-customer-data:
    classification: confidential
    quantity: many
    
trust_boundaries:
  processing-zone:
    type: network-cloud-provider
    technical_assets_inside:
      - kafka-cluster
      - flink-processor
  storage-zone:
    type: network-cloud-provider
    technical_assets_inside:
      - s3-raw-zone
      - postgres-warehouse
```

**IriusRisk:**
- Commercial threat modeling platform
- Library of threat patterns for common architectures
- Integrates with Jira, Azure DevOps for threat tracking
- Pre-built component libraries including data services (Kafka, Spark, databases)
- Generates countermeasures and testing requirements automatically
- Compliance mapping (NIST, ISO 27001, SOC 2)

### 9.3 CI/CD Integration for Threat Model Validation

**Automated checks in pipeline:**
```yaml
# GitHub Actions example
name: Threat Model Validation
on:
  pull_request:
    paths:
      - 'infrastructure/**'
      - 'pipeline/**'
      - 'src/connectors/**'

jobs:
  threat-model-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Threagile
        run: |
          docker run --rm -v $(pwd):/app threagile/threagile \
            -model /app/threat-model.yaml \
            -output /app/reports
      
      - name: Check for unmitigated HIGH/CRITICAL risks
        run: |
          python scripts/check_risks.py reports/risks.json \
            --max-severity MEDIUM \
            --fail-on-unaccepted
      
      - name: Verify threat model freshness
        run: |
          python scripts/check_freshness.py threat-model.yaml \
            --max-age-days 90 \
            --changed-files "${{ github.event.pull_request.changed_files }}"
```

**Pre-commit hooks:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if data architecture files changed
ARCH_FILES=$(git diff --cached --name-only | grep -E '(pipeline|infrastructure|schema)/')

if [ -n "$ARCH_FILES" ]; then
  # Verify threat model updated
  TM_UPDATED=$(git diff --cached --name-only | grep 'threat-model')
  if [ -z "$TM_UPDATED" ]; then
    echo "WARNING: Architecture files changed but threat model not updated."
    echo "Changed files: $ARCH_FILES"
    echo "Run: make threat-model-review"
  fi
fi
```

### 9.4 Threat Model as Living Document

**Version control:**
- Store threat models alongside code (same repo or dedicated security repo)
- Use machine-readable formats (YAML, JSON) over documents
- Track changes via git history — who added/removed threats and why
- Tag threat model versions to releases

**Review triggers (mandatory re-evaluation):**
- New data source added (new trust boundary crossing)
- Architecture change (new component, changed data flow)
- Security incident (validate model covered the attack vector)
- Compliance requirement change (new regulation, audit finding)
- Technology upgrade (new database version, new Kafka version)
- Access pattern change (new consumer team, new use case)
- Quarterly scheduled review (even without changes)

**Metrics to track:**
- Number of identified threats vs. mitigated threats
- Mean time from threat identification to mitigation
- Percentage of architecture changes with corresponding threat model updates
- Residual risk trend over time
- Threat model coverage (percentage of data flows modeled)

### 9.5 Organizational Integration

**RACI for threat modeling in data teams:**

| Activity | Data Engineer | Security Engineer | Data Platform Lead | CISO |
|----------|:---:|:---:|:---:|:---:|
| Create/update DFDs | R | C | A | I |
| Identify threats (STRIDE) | R | R | A | I |
| Risk assessment | C | R | A | I |
| Mitigation design | R | R | A | I |
| Mitigation implementation | R | C | A | I |
| Risk acceptance | I | C | R | A |
| Annual review | C | R | A | I |

R=Responsible, A=Accountable, C=Consulted, I=Informed

**Training requirements:**
- All data engineers: DFD creation, basic STRIDE (4-hour workshop)
- Data platform leads: Full threat modeling methodology, risk assessment (2-day training)
- Security engineers: Data-specific threats, cloud data architecture patterns (ongoing)
- New hire onboarding: Include threat model review for their team's systems

---

## 10. Lab Exercises

### 10.1 Lab: Complete Threat Model for Streaming Data Pipeline

**Architecture:**
```
[IoT Sensors] → (MQTT Broker) → (Kafka Connect) → [Kafka Topics]
[Kafka Topics] → (Apache Flink) → [PostgreSQL Timeseries]
[PostgreSQL] → (REST API) → [Dashboard Application]
[Kafka Topics] → (Kafka Connect) → [S3 Archive]
```

**Exercise steps:**

**Step 1: Create Level 2 DFD**

Draw the complete DFD with all trust boundaries:
```
Trust Boundary 1: Edge Network (IoT)
├── [IoT Sensors] (External Entity)
└── Data Flow: MQTT publish (sensor_id, timestamp, readings)

Trust Boundary 2: Ingestion Zone
├── (MQTT Broker - Mosquitto)
├── (Kafka Connect MQTT Source)
├── [Kafka Raw Topic: iot.raw.readings]
└── (Schema Registry - Avro validation)

Trust Boundary 3: Processing Zone
├── (Flink Job: Windowed Aggregation)
├── (Flink Job: Anomaly Detection)
├── [Flink State Store (RocksDB)]
└── [Kafka Processed Topic: iot.processed.aggregates]

Trust Boundary 4: Storage Zone
├── [PostgreSQL TimescaleDB]
├── [S3 Raw Archive]
└── (Kafka Connect S3 Sink)

Trust Boundary 5: Serving Zone
├── (REST API - FastAPI)
├── (Authentication - OAuth2)
└── [Redis Cache]

Trust Boundary 6: Consumer Network
└── [Dashboard Application] (External Entity)
```

**Step 2: STRIDE per element**

| Element | S | T | R | I | D | E |
|---------|---|---|---|---|---|---|
| IoT Sensors | Device impersonation | Reading manipulation | No device audit log | Readings in plaintext | Flood messages | N/A (external) |
| MQTT Broker | Unauthenticated connect | Topic injection | No connection audit | Wildcard subscribe | Connection flood | Admin access |
| Kafka Connect | Config injection | Connector manipulation | Connector logs incomplete | Credential in config | Connector crash | Plugin loading |
| Kafka Topics | Producer spoofing | Message tampering | Offset manipulation | Unauthorized consume | Partition flood | ACL bypass |
| Flink Jobs | Job submission spoof | UDF manipulation | No job audit | State store exposure | Resource exhaustion | Checkpoint access |
| PostgreSQL | Auth bypass | SQL injection | Log deletion | Query disclosure | Lock exhaustion | Role escalation |
| REST API | Token forgery | Response manipulation | No request audit | Over-fetching | Rate limit bypass | JWT claim abuse |
| S3 Archive | Assumed role abuse | Object modification | Access log disabled | Bucket listing | Storage exhaustion | Policy misconfiguration |

**Step 3: Prioritize threats**

Top 5 threats by risk score (Likelihood × Impact):
1. **IoT device impersonation** (L:8, I:7 = 56): No device certificates, any MQTT client can publish
2. **Kafka unauthorized consume** (L:7, I:8 = 56): If ACLs misconfigured, full data access
3. **PostgreSQL credential exposure** (L:6, I:9 = 54): Connection strings in Kafka Connect config
4. **S3 bucket policy** (L:5, I:9 = 45): Historical data with PII in archive
5. **Flink state store exposure** (L:6, I:6 = 36): RocksDB on disk without encryption

**Step 4: Mitigation plan**

| Threat | Mitigation | Priority | Effort |
|--------|-----------|----------|--------|
| Device impersonation | mTLS with device certificates + device registry | P1 | High |
| Kafka unauthorized access | SASL/SCRAM + per-topic ACLs + network isolation | P1 | Medium |
| Credential exposure | External secret manager (Vault) + short-lived tokens | P1 | Medium |
| S3 misconfiguration | Block public access + CMK encryption + access logging | P1 | Low |
| State store exposure | Encrypted EBS + Flink checkpoint encryption | P2 | Low |

### 10.2 Lab: STRIDE Worksheet for Data Warehouse

**Target:** Enterprise data warehouse (Snowflake/BigQuery/Redshift equivalent)

**Architecture components:**
- Ingestion: Multiple ELT pipelines loading from 12 source systems
- Storage: Multi-layer warehouse (raw/staging/curated/mart)
- Compute: Separate compute clusters for ETL, analytics, ML
- Access: 200+ users across 8 departments, 15 service accounts
- Governance: Data catalog, column-level masking, audit logging

**STRIDE Worksheet:**

```
┌─────────────────────────────────────────────────────────────────────┐
│ ELEMENT: Ingestion Pipeline (dbt + Airflow)                          │
├─────────────────────────────────────────────────────────────────────┤
│ SPOOFING                                                             │
│ □ Can an unauthorized process trigger pipeline execution?            │
│   → Airflow RBAC review: who can trigger DAGs?                      │
│ □ Can source system identity be spoofed?                            │
│   → Verify mTLS/VPN for source connections                         │
│ □ Can pipeline credentials be reused by another process?            │
│   → Check credential isolation between DAGs                        │
├─────────────────────────────────────────────────────────────────────┤
│ TAMPERING                                                            │
│ □ Can dbt model logic be modified without review?                   │
│   → Git branch protection, required approvals                      │
│ □ Can data be modified between extraction and loading?              │
│   → End-to-end checksums per batch                                 │
│ □ Can pipeline parameters be manipulated to alter behavior?         │
│   → Airflow variable/connection access control                     │
├─────────────────────────────────────────────────────────────────────┤
│ REPUDIATION                                                          │
│ □ Can pipeline execution be performed without audit trail?          │
│   → Verify Airflow audit logging is immutable                      │
│ □ Can data modifications be attributed to specific pipeline runs?   │
│   → Metadata tracking: run_id in all loaded records                │
│ □ Can pipeline errors be hidden?                                    │
│   → Alerting on silent failures (no rows loaded)                   │
├─────────────────────────────────────────────────────────────────────┤
│ INFORMATION DISCLOSURE                                               │
│ □ Can pipeline logs expose sensitive data values?                   │
│   → Log sanitization, no PII in error messages                     │
│ □ Can intermediate data be accessed by unauthorized users?          │
│   → Staging schema access restricted to pipeline service account   │
│ □ Can pipeline configuration reveal architecture details?           │
│   → Connection strings, schema names in version control?           │
├─────────────────────────────────────────────────────────────────────┤
│ DENIAL OF SERVICE                                                    │
│ □ Can a single pipeline monopolize warehouse compute?               │
│   → Resource monitors, per-pipeline compute limits                 │
│ □ Can pipeline failure cascade to other pipelines?                  │
│   → Dependency isolation, circuit breakers                         │
│ □ Can source system unavailability block all downstream?            │
│   → Retry policies, stale data handling                            │
├─────────────────────────────────────────────────────────────────────┤
│ ELEVATION OF PRIVILEGE                                               │
│ □ Can pipeline service account perform operations beyond its need?  │
│   → Review: does it have DDL? Does it have cross-schema access?    │
│ □ Can dbt model execution elevate privileges via warehouse features?│
│   → Check for SECURITY DEFINER equivalent in warehouse             │
│ □ Can pipeline config changes grant broader access?                 │
│   → IaC review for access policy changes in pipeline code          │
└─────────────────────────────────────────────────────────────────────┘
```

Repeat for elements: Warehouse Storage Layer, Query/Compute Layer, Access Control Layer, Monitoring/Governance Layer, External Consumer Access.

### 10.3 Lab: Attack Tree for Database Exfiltration

**Root goal: Exfiltrate 10M+ customer records from production PostgreSQL**

```
Goal: Exfiltrate Customer PII (10M+ records)
│
├── [OR] Path 1: Direct Database Access
│   ├── [AND] 1a: Network Access + Valid Credentials
│   │   ├── [OR] Get Network Access
│   │   │   ├── Compromise VPN (cost: $$$, skill: high, detect: medium)
│   │   │   ├── Compromise bastion host (cost: $$, skill: high, detect: medium)
│   │   │   ├── Cloud metadata exploitation (cost: $, skill: medium, detect: low)
│   │   │   └── Insider with network access (cost: $, skill: low, detect: low)
│   │   └── [OR] Get Credentials
│   │       ├── Extract from config management (cost: $, skill: medium, detect: low)
│   │       ├── Memory dump of application server (cost: $$, skill: high, detect: medium)
│   │       ├── Phish DBA/engineer (cost: $, skill: medium, detect: medium)
│   │       ├── Credential in git history (cost: $, skill: low, detect: none)
│   │       └── Brute force weak password (cost: $, skill: low, detect: high)
│   │
│   └── [AND] 1b: Exploit Vulnerability + Bypass Auth
│       ├── [OR] Find exploitable vulnerability
│       │   ├── Unpatched PostgreSQL CVE (cost: $, skill: medium, detect: varies)
│       │   ├── Application SQL injection to database (cost: $, skill: medium, detect: medium)
│       │   └── Extension vulnerability (cost: $$, skill: high, detect: low)
│       └── Bypass network controls
│           ├── SQL injection provides direct access (no network bypass needed)
│           └── SSRF from internal service to database port
│
├── [OR] Path 2: Through Data Pipeline
│   ├── [AND] 2a: Modify Pipeline to Exfiltrate
│   │   ├── [OR] Get Pipeline Control
│   │   │   ├── Airflow web UI access (cost: $, skill: low, detect: medium)
│   │   │   ├── Git repo write access (cost: $, skill: medium, detect: low)
│   │   │   └── CI/CD pipeline injection (cost: $$, skill: medium, detect: low)
│   │   └── Add exfiltration step
│   │       ├── New DAG task: COPY TO external (cost: $, skill: low, detect: medium)
│   │       ├── Modified transform: duplicate to attacker sink (cost: $, skill: medium, detect: low)
│   │       └── New Kafka consumer to attacker endpoint (cost: $, skill: medium, detect: low)
│   │
│   └── [AND] 2b: Tap Existing Data Flow
│       ├── Network capture on replication stream (cost: $$, skill: high, detect: low)
│       ├── Compromise Kafka and consume from beginning (cost: $$, skill: medium, detect: medium)
│       └── Access pipeline temporary storage (cost: $, skill: medium, detect: low)
│
├── [OR] Path 3: Through Backup/Archive
│   ├── Access cloud storage backup (cost: $, skill: medium, detect: low)
│   ├── Intercept backup transfer (cost: $$, skill: high, detect: low)
│   ├── Restore backup to attacker-controlled server (cost: $, skill: medium, detect: medium)
│   └── Snapshot sharing exploit (cost: $, skill: medium, detect: low)
│
└── [OR] Path 4: Through Legitimate Access Abuse
    ├── Over-privileged analyst account (cost: $, skill: low, detect: low)
    ├── BI tool export without DLP (cost: $, skill: low, detect: low)
    ├── API pagination abuse (cost: $, skill: low, detect: medium)
    └── Compromised service account with SELECT * (cost: $, skill: medium, detect: low)

CHEAPEST PATH ANALYSIS:
Path 4 (Legitimate Access Abuse) → Over-privileged analyst + BI tool export
Total cost: $, Skill: Low, Detectability: Low
→ This is where pentest should focus FIRST

HIGHEST IMPACT PATH:
Path 1a (Direct Database) → Credential from git history + insider network
Total cost: $, Skill: Low, Detectability: None/Low
→ This is the most dangerous realistic scenario
```

**Pentest planning from attack tree:**
1. Phase 1: Test Path 4 — verify access controls, DLP, export limitations
2. Phase 2: Test Path 3 — check backup accessibility, encryption enforcement
3. Phase 3: Test Path 2 — verify pipeline integrity, separation of duties
4. Phase 4: Test Path 1 — attempt credential discovery, network exploitation

### 10.4 Lab: Risk Register for Cloud Data Lake

**Context:** Organization operates a multi-cloud data lake (AWS S3 + Snowflake) with 50TB of data including customer PII, financial records, and proprietary ML features.

**Risk Register:**

| ID | Threat | STRIDE | Likelihood | Impact | Risk Score | Mitigation | Residual Risk | Owner | Status |
|----|--------|--------|-----------|--------|------------|-----------|---------------|-------|--------|
| R-001 | S3 bucket public exposure | I | Medium (5) | Critical (9) | 45 | Block Public Access at org level, automated scanning | Low (2×9=18) | Platform | Mitigated |
| R-002 | IAM over-permission for data roles | E | High (8) | High (7) | 56 | Quarterly access review, automated least-privilege scoring | Medium (4×7=28) | Security | In Progress |
| R-003 | Snowflake credential in code | S | Medium (6) | Critical (9) | 54 | Secret scanning in CI, key rotation automation | Low (2×9=18) | DevOps | Mitigated |
| R-004 | Cross-account data access | I, E | Medium (5) | High (8) | 40 | Organization policies (SCP), explicit deny on cross-account | Low (2×8=16) | Platform | Mitigated |
| R-005 | Data lake poisoning via ingestion | T | Medium (6) | High (7) | 42 | Schema validation, anomaly detection on ingested data | Medium (3×7=21) | Data Eng | In Progress |
| R-006 | ML feature store manipulation | T | Low (4) | Critical (9) | 36 | Feature versioning, immutable storage, integrity checks | Low (2×9=18) | ML Ops | Planned |
| R-007 | Insider exfiltration via analytics | I | High (7) | High (8) | 56 | DLP controls, query volume alerting, column masking | Medium (4×8=32) | Security | In Progress |
| R-008 | Pipeline credential exposure in logs | I | High (7) | High (7) | 49 | Log sanitization, structured logging, no PII in errors | Medium (3×7=21) | Data Eng | In Progress |
| R-009 | Unencrypted data in transit | I, T | Medium (5) | High (8) | 40 | Enforce TLS everywhere, mTLS for service-to-service | Low (2×8=16) | Platform | Mitigated |
| R-010 | Backup data without encryption | I | Medium (5) | Critical (9) | 45 | CMK encryption mandatory, backup policy audit | Low (1×9=9) | Platform | Mitigated |
| R-011 | IMDS exploitation on data workers | S, I, E | Medium (6) | High (8) | 48 | IMDSv2 enforced, hop limit=1, VPC endpoints | Low (2×8=16) | Platform | Mitigated |
| R-012 | Third-party connector supply chain | T, E | Low (3) | High (8) | 24 | Dependency scanning, pinned versions, integrity verification | Low (2×8=16) | Data Eng | Planned |
| R-013 | Data retention violation (GDPR) | LINDDUN-N | High (7) | High (8) | 56 | Automated retention enforcement, deletion verification | Medium (4×8=32) | Governance | In Progress |
| R-014 | Kafka consumer group hijacking | S, D | Medium (5) | Medium (6) | 30 | SASL auth, ACLs, consumer group monitoring | Low (2×6=12) | Platform | Mitigated |
| R-015 | Snowflake account takeover | S, E | Low (3) | Critical (9) | 27 | MFA enforced, network policies, session monitoring | Low (1×9=9) | Security | Mitigated |

**Risk trend analysis:**

```
Quarter | Total Risk Score | Critical Risks | Mitigated | In Progress | Planned |
Q1 2025 | 590              | 5              | 3         | 6           | 6       |
Q2 2025 | 486              | 4              | 7         | 5           | 3       |
Q3 2025 | 352              | 2              | 10        | 4           | 1       |
Q4 2025 | 280 (target)     | 0              | 13        | 2           | 0       |
```

**Review schedule:**
- Monthly: Review all IN PROGRESS mitigations, update status
- Quarterly: Full risk register review, re-score after mitigations
- On-demand: New data source, architecture change, security incident
- Annual: Complete threat model refresh with new STRIDE analysis

**Acceptance criteria for risk closure:**
- Mitigation implemented and verified (not just planned)
- Residual risk score below threshold (varies by risk appetite tier)
- Detection capability operational (can we see if it happens?)
- Recovery procedure documented and tested
- No compensating control dependencies on single points of failure

---

## Summary: Threat Modeling as Pentest Blueprint

From an ethical hacker's perspective, threat models are offensive roadmaps:

1. **DFDs reveal attack surface** — every trust boundary crossing is a potential entry point
2. **STRIDE identifies vulnerability classes** — tells you what to look for at each component
3. **Attack trees define test plans** — leaf nodes become specific test cases
4. **Risk registers prioritize effort** — highest risk items get tested first
5. **Mitigations define bypass objectives** — your job is to prove they work or find gaps

The threat model answers the pentester's fundamental questions:
- Where is the valuable data? (Asset identification)
- How does data flow between components? (DFD analysis)
- What are the weakest links? (Risk prioritization)
- What defenses exist? (Mitigation review → bypass targets)
- What would detection look like? (Stealth planning)

A data system without a threat model is a data system that has not been systematically evaluated for risk. The threat model is not a document that sits on a shelf — it is the living specification of how your data architecture responds to adversarial pressure. Update it when architecture changes, validate it through testing, and use it to prioritize both defensive investments and offensive assessments.
