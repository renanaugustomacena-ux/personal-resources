# Audit Trails, Database Logging, and Data Forensics

## 1. Audit Trail Architecture

### 1.1 Fundamental Principles

An audit trail is a chronological record of system activities that provides documentary evidence of the sequence of activities affecting a specific operation, procedure, or event. From a security perspective, audit trails serve dual purposes: they are the primary evidence source during incident response and forensic investigations, and they are simultaneously high-value targets for attackers seeking to cover their tracks.

The core architectural principles for robust audit trails:

- **Immutability** — once written, audit records must never be modified or deleted
- **Completeness** — capture sufficient context to reconstruct the full sequence of events
- **Timeliness** — record events as close to real-time as possible
- **Integrity** — provide cryptographic guarantees that logs have not been tampered with
- **Availability** — ensure audit data survives system failures, attacks, and operational errors

### 1.2 Immutable Audit Logs

Immutable audit logs enforce a fundamental constraint: data can only be appended, never updated or deleted. This property is achieved through a combination of architectural patterns and storage mechanisms.

**Append-Only Storage Patterns:**

```sql
-- PostgreSQL: Enforce append-only via trigger
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_id        UUID NOT NULL,
    actor_type      VARCHAR(50) NOT NULL,  -- 'user', 'service', 'system'
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(100) NOT NULL,
    resource_id     TEXT NOT NULL,
    old_value       JSONB,
    new_value       JSONB,
    metadata        JSONB,
    ip_address      INET,
    session_id      UUID,
    correlation_id  UUID,
    hash_chain      BYTEA NOT NULL
);

-- Prevent UPDATE and DELETE
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log records cannot be modified or deleted';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_no_update
    BEFORE UPDATE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER audit_no_delete
    BEFORE DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- Revoke direct modification privileges
REVOKE UPDATE, DELETE ON audit_log FROM PUBLIC;
REVOKE UPDATE, DELETE ON audit_log FROM app_user;
```

**Considerations from an attacker's perspective:** Triggers can be disabled by superusers (`ALTER TABLE audit_log DISABLE TRIGGER ALL`). Defense in depth requires multiple layers: trigger-based protection, role-based access controls, row-level security, and external log forwarding. A sophisticated attacker with superuser access can bypass any single database-level control.

### 1.3 Write-Ahead Logs (WAL)

Write-ahead logging is the fundamental mechanism databases use to ensure durability and atomicity. Every modification is first written to a sequential log before being applied to data pages. This property makes WAL an invaluable audit source.

**PostgreSQL WAL Architecture:**

```
Transaction → WAL Buffer → WAL Segment Files → Checkpoint → Data Pages
                              ↓
                    Archived WAL (for PITR and audit)
```

WAL records contain:
- Transaction ID (XID)
- Relation (table) OID
- Block number and offset
- Before-image and after-image of modified tuples
- Commit/abort records with timestamps

**Configuring WAL for audit purposes:**

```ini
# postgresql.conf
wal_level = logical          # Maximum detail (includes row-level changes)
archive_mode = on
archive_command = 'cp %p /secure/wal_archive/%f'
max_wal_senders = 10
wal_keep_size = 10GB         # Retain WAL for streaming replication and audit
```

**MySQL Binary Log equivalent:**

```ini
# my.cnf
server-id = 1
log_bin = /var/log/mysql/binlog
binlog_format = ROW          # Row-based for complete before/after images
binlog_row_image = FULL      # Capture all columns, not just changed ones
expire_logs_days = 90
max_binlog_size = 1G
```

### 1.4 Event Sourcing for Audit

Event sourcing stores the complete history of state changes as a sequence of immutable events rather than storing only the current state. This pattern naturally produces a complete audit trail.

**Event Store Schema:**

```sql
CREATE TABLE event_store (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type  VARCHAR(100) NOT NULL,
    aggregate_id    UUID NOT NULL,
    event_type      VARCHAR(200) NOT NULL,
    event_version   INTEGER NOT NULL,
    event_data      JSONB NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID NOT NULL,
    sequence_number BIGSERIAL NOT NULL,
    UNIQUE (aggregate_id, event_version)
);

CREATE INDEX idx_event_store_aggregate ON event_store(aggregate_type, aggregate_id, event_version);
CREATE INDEX idx_event_store_created ON event_store(created_at);
CREATE INDEX idx_event_store_type ON event_store(event_type);
```

**Example event stream for a financial record:**

```json
[
  {
    "event_type": "AccountCreated",
    "event_version": 1,
    "event_data": {"account_id": "acc-001", "owner": "user-42", "currency": "EUR"},
    "metadata": {"ip": "192.168.1.100", "user_agent": "...", "correlation_id": "req-abc"}
  },
  {
    "event_type": "FundsDeposited",
    "event_version": 2,
    "event_data": {"amount": 10000, "source": "wire_transfer", "reference": "WT-2024-001"},
    "metadata": {"ip": "192.168.1.100", "approved_by": "user-99"}
  },
  {
    "event_type": "FundsWithdrawn",
    "event_version": 3,
    "event_data": {"amount": 3000, "destination": "external_account", "reference": "WD-2024-015"},
    "metadata": {"ip": "10.0.0.55", "approved_by": "user-99", "risk_score": 0.12}
  }
]
```

### 1.5 Temporal Databases

Temporal tables maintain the full history of data changes with system-managed validity periods, providing built-in audit capabilities.

**PostgreSQL Temporal Tables (using temporal_tables extension or manual implementation):**

```sql
-- Main table (current state)
CREATE TABLE employees (
    id          UUID PRIMARY KEY,
    name        TEXT NOT NULL,
    department  TEXT NOT NULL,
    salary      NUMERIC(12,2) NOT NULL,
    valid_from  TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to    TIMESTAMPTZ NOT NULL DEFAULT 'infinity'
);

-- History table (automatically populated)
CREATE TABLE employees_history (
    LIKE employees INCLUDING ALL,
    modified_by UUID,
    modification_type VARCHAR(10)  -- INSERT, UPDATE, DELETE
);

-- Versioning trigger
CREATE OR REPLACE FUNCTION versioning_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.valid_from IS NULL THEN
            NEW.valid_from = now();
        END IF;
        OLD.valid_to = NEW.valid_from;
        INSERT INTO employees_history VALUES (OLD.*, current_setting('app.current_user_id')::UUID, 'UPDATE');
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        OLD.valid_to = now();
        INSERT INTO employees_history VALUES (OLD.*, current_setting('app.current_user_id')::UUID, 'DELETE');
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

**SQL Server System-Versioned Temporal Tables (native support since SQL Server 2016):**

```sql
CREATE TABLE employees (
    id              UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    name            NVARCHAR(200) NOT NULL,
    department      NVARCHAR(100) NOT NULL,
    salary          DECIMAL(12,2) NOT NULL,
    -- System-versioning columns
    SysStartTime    DATETIME2 GENERATED ALWAYS AS ROW START NOT NULL,
    SysEndTime      DATETIME2 GENERATED ALWAYS AS ROW END NOT NULL,
    PERIOD FOR SYSTEM_TIME (SysStartTime, SysEndTime)
) WITH (SYSTEM_VERSIONING = ON (HISTORY_TABLE = dbo.employees_history));

-- Query historical state at a specific point in time
SELECT * FROM employees
FOR SYSTEM_TIME AS OF '2024-06-15 14:30:00';

-- Query all changes within a time range
SELECT * FROM employees
FOR SYSTEM_TIME BETWEEN '2024-06-01' AND '2024-06-30';
```

### 1.6 Log Chain Integrity

Hash chaining creates a tamper-evident sequence where each log entry includes a cryptographic hash of the previous entry, making any modification or deletion detectable.

**Hash Chain Implementation:**

```python
import hashlib
import json
from datetime import datetime, timezone

class AuditChain:
    """Append-only audit log with hash chain integrity."""
    
    def __init__(self, hash_algorithm='sha256'):
        self.algorithm = hash_algorithm
        self.previous_hash = b'\x00' * 32  # Genesis block
    
    def compute_entry_hash(self, entry: dict, previous_hash: bytes) -> bytes:
        """Compute hash of an audit entry including the previous hash."""
        canonical = json.dumps(entry, sort_keys=True, default=str)
        payload = previous_hash + canonical.encode('utf-8')
        return hashlib.new(self.algorithm, payload).digest()
    
    def append(self, event_data: dict, actor: str) -> dict:
        """Append an entry to the audit chain."""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'actor': actor,
            'data': event_data,
            'previous_hash': self.previous_hash.hex(),
        }
        entry_hash = self.compute_entry_hash(entry, self.previous_hash)
        entry['hash'] = entry_hash.hex()
        self.previous_hash = entry_hash
        return entry
    
    def verify_chain(self, entries: list) -> tuple[bool, int]:
        """Verify integrity of the entire chain. Returns (valid, break_index)."""
        previous_hash = b'\x00' * 32
        for i, entry in enumerate(entries):
            stored_hash = bytes.fromhex(entry['hash'])
            verify_entry = {k: v for k, v in entry.items() if k != 'hash'}
            computed_hash = self.compute_entry_hash(verify_entry, previous_hash)
            if computed_hash != stored_hash:
                return False, i
            previous_hash = stored_hash
        return True, -1
```

**Merkle Tree for Batch Verification:**

Merkle trees allow efficient verification of large audit log segments without requiring linear traversal of the entire chain.

```python
import hashlib
from typing import List

class AuditMerkleTree:
    """Merkle tree for batch audit log integrity verification."""
    
    def __init__(self, entries: List[bytes]):
        self.leaves = [self._hash_leaf(e) for e in entries]
        self.tree = self._build_tree(self.leaves)
    
    def _hash_leaf(self, data: bytes) -> bytes:
        return hashlib.sha256(b'\x00' + data).digest()
    
    def _hash_node(self, left: bytes, right: bytes) -> bytes:
        return hashlib.sha256(b'\x01' + left + right).digest()
    
    def _build_tree(self, leaves: List[bytes]) -> List[List[bytes]]:
        if not leaves:
            return [[]]
        tree = [leaves]
        current_level = leaves
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                next_level.append(self._hash_node(left, right))
            tree.append(next_level)
            current_level = next_level
        return tree
    
    @property
    def root(self) -> bytes:
        return self.tree[-1][0] if self.tree and self.tree[-1] else b''
    
    def get_proof(self, index: int) -> List[tuple]:
        """Generate a Merkle proof for the entry at the given index."""
        proof = []
        for level in self.tree[:-1]:
            sibling_index = index ^ 1
            if sibling_index < len(level):
                direction = 'right' if index % 2 == 0 else 'left'
                proof.append((direction, level[sibling_index]))
            index //= 2
        return proof
```

---

## 2. Database Native Auditing

### 2.1 PostgreSQL Auditing

**pgaudit Extension:**

pgaudit provides detailed session and object audit logging through the PostgreSQL logging facility. It generates audit entries for DDL and DML operations with fine-grained control.

```ini
# postgresql.conf
shared_preload_libraries = 'pgaudit'

# Session-level audit logging
pgaudit.log = 'ddl, role, write, read'
pgaudit.log_catalog = off
pgaudit.log_parameter = on
pgaudit.log_statement_once = off
pgaudit.log_level = log

# Object-level audit logging (requires role-based configuration)
pgaudit.role = 'auditor'
```

**Configuring object-level auditing:**

```sql
-- Create the auditor role
CREATE ROLE auditor NOLOGIN;

-- Grant the auditor role SELECT on sensitive tables
GRANT SELECT ON customers, transactions, credentials TO auditor;

-- Any query by any user on these tables now generates audit entries
-- because pgaudit checks if the 'auditor' role has relevant grants
```

**pgaudit log output format:**

```
AUDIT: SESSION,1,1,DDL,CREATE TABLE,TABLE,public.sensitive_data,
  "CREATE TABLE sensitive_data (id serial, ssn text, ...)"
AUDIT: SESSION,2,1,WRITE,INSERT,TABLE,public.sensitive_data,
  "INSERT INTO sensitive_data (ssn) VALUES ($1)",<'123-45-6789'>
AUDIT: OBJECT,3,1,READ,SELECT,TABLE,public.customers,
  "SELECT * FROM customers WHERE id = $1",<42>
```

**pg_stat_statements for query pattern analysis:**

```sql
-- Enable the extension
CREATE EXTENSION pg_stat_statements;

-- Query the most expensive queries (potential data exfiltration)
SELECT
    queryid,
    query,
    calls,
    total_exec_time,
    rows,
    mean_exec_time
FROM pg_stat_statements
WHERE rows > 10000  -- Bulk data access
ORDER BY rows DESC
LIMIT 20;

-- Identify unusual query patterns
SELECT
    queryid,
    query,
    calls,
    rows / NULLIF(calls, 0) AS avg_rows_per_call
FROM pg_stat_statements
WHERE query ILIKE '%SELECT%FROM%customers%'
  AND rows / NULLIF(calls, 0) > 1000
ORDER BY calls DESC;
```

**log_statement configuration:**

```ini
# postgresql.conf - Granular logging
log_statement = 'mod'           # Log DDL + DML (not pure SELECT)
log_min_duration_statement = 0  # Log all statements with duration
log_line_prefix = '%t [%p-%l] %q%u@%d '
log_connections = on
log_disconnections = on
log_duration = on
log_lock_waits = on
log_checkpoints = on
```

### 2.2 MySQL Auditing

**Enterprise Audit Plugin:**

```sql
-- Install the audit plugin
INSTALL PLUGIN audit_log SONAME 'audit_log.so';

-- Configure filtering
SET GLOBAL audit_log_policy = 'ALL';         -- LOGINS, QUERIES, ALL, NONE
SET GLOBAL audit_log_format = 'JSON';        -- NEW, OLD, JSON
SET GLOBAL audit_log_strategy = 'ASYNCHRONOUS';
SET GLOBAL audit_log_rotate_on_size = 1073741824;  -- 1GB rotation

-- Filter by user
SELECT audit_log_filter_set_filter('log_all', '{"filter": {"log": true}}');
SELECT audit_log_filter_set_user('%', 'log_all');

-- Filter for specific events only
SELECT audit_log_filter_set_filter('ddl_only', '{
  "filter": {
    "class": [
      {"name": "general", "event": [{"name": "status", "log": {"field": {"name": "general_command.str", "value": "Query"}}}}],
      {"name": "table_access"}
    ]
  }
}');
```

**General Query Log and Slow Query Log:**

```ini
# my.cnf
general_log = ON
general_log_file = /var/log/mysql/general.log

slow_query_log = ON
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
log_queries_not_using_indexes = ON
log_slow_admin_statements = ON
```

### 2.3 SQL Server Auditing

**SQL Server Audit (Enterprise feature):**

```sql
-- Create a server audit
CREATE SERVER AUDIT DataAccessAudit
TO FILE (
    FILEPATH = 'E:\AuditLogs\',
    MAXSIZE = 1 GB,
    MAX_ROLLOVER_FILES = 100,
    RESERVE_DISK_SPACE = OFF
)
WITH (
    QUEUE_DELAY = 1000,
    ON_FAILURE = CONTINUE
);

-- Create a database audit specification
CREATE DATABASE AUDIT SPECIFICATION SensitiveDataAudit
FOR SERVER AUDIT DataAccessAudit
ADD (SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo BY public),
ADD (EXECUTE ON SCHEMA::dbo BY public),
ADD (SCHEMA_OBJECT_CHANGE_GROUP),
ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP);

ALTER SERVER AUDIT DataAccessAudit WITH (STATE = ON);
ALTER DATABASE AUDIT SPECIFICATION SensitiveDataAudit WITH (STATE = ON);

-- Query the audit log
SELECT
    event_time,
    action_id,
    succeeded,
    server_principal_name,
    database_name,
    schema_name,
    object_name,
    statement
FROM sys.fn_get_audit_file('E:\AuditLogs\*.sqlaudit', DEFAULT, DEFAULT)
WHERE event_time > DATEADD(hour, -24, GETUTCDATE())
ORDER BY event_time DESC;
```

**Change Data Capture (CDC):**

```sql
-- Enable CDC on the database
EXEC sys.sp_cdc_enable_db;

-- Enable CDC on a specific table
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name = N'customers',
    @role_name = N'cdc_reader',
    @supports_net_changes = 1;

-- Query change data
DECLARE @from_lsn binary(10) = sys.fn_cdc_get_min_lsn('dbo_customers');
DECLARE @to_lsn binary(10) = sys.fn_cdc_get_max_lsn();

SELECT
    __$operation,  -- 1=delete, 2=insert, 3=before-update, 4=after-update
    __$update_mask,
    *
FROM cdc.fn_cdc_get_all_changes_dbo_customers(@from_lsn, @to_lsn, N'all update old');
```

### 2.4 Oracle Unified Audit

```sql
-- Create a unified audit policy
CREATE AUDIT POLICY sensitive_data_access
    ACTIONS SELECT ON hr.employees,
            INSERT ON hr.employees,
            UPDATE ON hr.employees,
            DELETE ON hr.employees,
            SELECT ON finance.transactions
    WHEN 'SYS_CONTEXT(''USERENV'', ''SESSION_USER'') NOT IN (''AUDIT_ADMIN'')'
    EVALUATE PER SESSION;

-- Enable the policy
AUDIT POLICY sensitive_data_access;

-- Fine-Grained Auditing (FGA) for column-level access
BEGIN
    DBMS_FGA.ADD_POLICY(
        object_schema   => 'HR',
        object_name     => 'EMPLOYEES',
        policy_name     => 'SALARY_ACCESS',
        audit_column    => 'SALARY,SSN,BANK_ACCOUNT',
        audit_condition => 'SYS_CONTEXT(''USERENV'',''SESSION_USER'') != ''HR_ADMIN''',
        handler_schema  => 'SECURITY',
        handler_module  => 'ALERT_PKG.NOTIFY_SENSITIVE_ACCESS',
        enable          => TRUE,
        statement_types => 'SELECT,UPDATE'
    );
END;
/

-- Query the unified audit trail
SELECT
    event_timestamp,
    dbusername,
    action_name,
    object_schema,
    object_name,
    sql_text,
    client_program_name,
    os_username,
    userhost
FROM unified_audit_trail
WHERE event_timestamp > SYSTIMESTAMP - INTERVAL '24' HOUR
ORDER BY event_timestamp DESC;
```

### 2.5 MongoDB Auditing

```yaml
# mongod.conf
auditLog:
  destination: file
  format: JSON
  path: /var/log/mongodb/audit.json
  filter: '{
    atype: {
      $in: [
        "authenticate", "createUser", "dropUser",
        "createDatabase", "dropDatabase",
        "createCollection", "dropCollection",
        "insert", "update", "delete",
        "find", "getMore"
      ]
    }
  }'

setParameter:
  auditAuthorizationSuccess: true
```

**Change Streams for real-time audit:**

```javascript
const pipeline = [
  {
    $match: {
      'operationType': { $in: ['insert', 'update', 'delete', 'replace'] },
      'ns.coll': { $in: ['customers', 'transactions', 'credentials'] }
    }
  }
];

const changeStream = db.collection('customers').watch(pipeline, {
  fullDocument: 'updateLookup',
  fullDocumentBeforeChange: 'whenAvailable'
});

changeStream.on('change', (event) => {
  const auditEntry = {
    timestamp: new Date(),
    operation: event.operationType,
    collection: event.ns.coll,
    documentId: event.documentKey._id,
    before: event.fullDocumentBeforeChange,
    after: event.fullDocument,
    clusterTime: event.clusterTime
  };
  auditCollection.insertOne(auditEntry);
});
```

---

## 3. Application-Level Audit Logging

### 3.1 Audit Table Design Patterns

**Pattern 1: Before/After with Diff**

```sql
CREATE TABLE entity_audit (
    audit_id        BIGSERIAL PRIMARY KEY,
    entity_type     VARCHAR(100) NOT NULL,
    entity_id       TEXT NOT NULL,
    action          VARCHAR(20) NOT NULL,  -- CREATE, UPDATE, DELETE, READ
    actor_id        UUID NOT NULL,
    actor_type      VARCHAR(50) NOT NULL,
    performed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- State capture
    before_state    JSONB,
    after_state     JSONB,
    changed_fields  TEXT[],
    -- Context
    correlation_id  UUID,
    request_id      UUID,
    source_ip       INET,
    user_agent      TEXT,
    service_name    VARCHAR(100),
    -- Integrity
    entry_hash      BYTEA NOT NULL,
    previous_hash   BYTEA NOT NULL
);

-- Partition by month for performance
CREATE TABLE entity_audit_2024_07 PARTITION OF entity_audit
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

-- Indexes for common queries
CREATE INDEX idx_audit_entity ON entity_audit(entity_type, entity_id, performed_at DESC);
CREATE INDEX idx_audit_actor ON entity_audit(actor_id, performed_at DESC);
CREATE INDEX idx_audit_correlation ON entity_audit(correlation_id);
CREATE INDEX idx_audit_time ON entity_audit(performed_at DESC);
```

**Pattern 2: Column-Level Change Tracking**

```sql
CREATE TABLE field_audit (
    id              BIGSERIAL PRIMARY KEY,
    entity_type     VARCHAR(100) NOT NULL,
    entity_id       TEXT NOT NULL,
    field_name      VARCHAR(200) NOT NULL,
    old_value       TEXT,
    new_value       TEXT,
    change_type     VARCHAR(10) NOT NULL,  -- SET, UNSET, APPEND, REMOVE
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    changed_by      UUID NOT NULL,
    transaction_id  UUID NOT NULL  -- Groups multiple field changes
);

CREATE INDEX idx_field_audit_entity ON field_audit(entity_type, entity_id, changed_at DESC);
CREATE INDEX idx_field_audit_txn ON field_audit(transaction_id);
```

### 3.2 Trigger-Based vs Application-Based Capture

**Trigger-Based Approach (PostgreSQL):**

```sql
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    audit_row JSONB;
    changed_cols TEXT[] := '{}';
    col_name TEXT;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- Identify changed columns
        FOR col_name IN SELECT column_name FROM information_schema.columns
            WHERE table_schema = TG_TABLE_SCHEMA AND table_name = TG_TABLE_NAME
        LOOP
            EXECUTE format('SELECT ($1).%I IS DISTINCT FROM ($2).%I', col_name, col_name)
                INTO STRICT audit_row
                USING NEW, OLD;
            IF audit_row::boolean THEN
                changed_cols := array_append(changed_cols, col_name);
            END IF;
        END LOOP;
    END IF;

    INSERT INTO entity_audit (
        entity_type, entity_id, action,
        actor_id, actor_type,
        before_state, after_state, changed_fields,
        correlation_id, source_ip, service_name,
        entry_hash, previous_hash
    ) VALUES (
        TG_TABLE_NAME,
        CASE TG_OP
            WHEN 'DELETE' THEN (OLD).id::TEXT
            ELSE (NEW).id::TEXT
        END,
        TG_OP,
        COALESCE(current_setting('app.current_user_id', true)::UUID, '00000000-0000-0000-0000-000000000000'),
        COALESCE(current_setting('app.actor_type', true), 'system'),
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) END,
        changed_cols,
        current_setting('app.correlation_id', true)::UUID,
        current_setting('app.source_ip', true)::INET,
        current_setting('app.service_name', true),
        -- Hash computation (simplified)
        sha256(convert_to(to_jsonb(NEW)::TEXT, 'UTF8')),
        '\x00'::BYTEA
    );

    RETURN CASE TG_OP WHEN 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply to sensitive tables
CREATE TRIGGER audit_customers
    AFTER INSERT OR UPDATE OR DELETE ON customers
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

**Trade-offs:**

| Aspect | Trigger-Based | Application-Based |
|--------|--------------|-------------------|
| Completeness | Captures ALL changes including direct SQL | Only captures changes through application |
| Performance | Adds latency to every write operation | Can be async (queue-based) |
| Context | Limited to DB session variables | Full request context (user, IP, headers) |
| Bypass risk | DBA can disable triggers | Developers can forget to audit |
| Schema coupling | Tightly coupled to table structure | Can evolve independently |
| Testability | Requires database for testing | Can unit test audit logic |

**Recommendation:** Use both. Triggers provide a safety net for direct database access, while application-level auditing captures rich context. Discrepancies between the two signal potential unauthorized direct database access.

### 3.3 Hibernate Envers (Java)

```java
@Entity
@Audited
@Table(name = "customers")
public class Customer {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @NotAudited  // Exclude from audit (e.g., cached computed fields)
    private String searchIndex;

    private String name;
    private String email;

    @Audited(withModifiedFlag = true)  // Track which fields changed
    private String address;

    @Audited(targetAuditMode = RelationTargetAuditMode.NOT_AUDITED)
    @ManyToOne
    private Department department;
}

// Custom revision entity to capture additional context
@Entity
@RevisionEntity(CustomRevisionListener.class)
@Table(name = "audit_revisions")
public class CustomRevisionEntity extends DefaultRevisionEntity {
    private String userId;
    private String ipAddress;
    private String correlationId;
    private String serviceName;
}

public class CustomRevisionListener implements RevisionListener {
    @Override
    public void newRevision(Object revisionEntity) {
        CustomRevisionEntity rev = (CustomRevisionEntity) revisionEntity;
        SecurityContext ctx = SecurityContextHolder.getContext();
        rev.setUserId(ctx.getAuthentication().getName());
        rev.setIpAddress(RequestContextHolder.currentRequestAttributes()
            .getAttribute("client_ip", RequestAttributes.SCOPE_REQUEST).toString());
        rev.setCorrelationId(MDC.get("correlationId"));
    }
}

// Querying audit history
AuditReader reader = AuditReaderFactory.get(entityManager);

// Get all revisions of an entity
List<Number> revisions = reader.getRevisions(Customer.class, customerId);

// Get entity state at a specific revision
Customer historicalState = reader.find(Customer.class, customerId, revisionNumber);

// Query for changes to a specific property
List<Object[]> results = reader.createQuery()
    .forRevisionsOfEntity(Customer.class, false, true)
    .add(AuditEntity.id().eq(customerId))
    .add(AuditEntity.property("email").hasChanged())
    .getResultList();
```

### 3.4 Django Audit Log (Python)

```python
# settings.py
INSTALLED_APPS = [
    'auditlog',
    ...
]

MIDDLEWARE = [
    'auditlog.middleware.AuditlogMiddleware',
    ...
]

AUDITLOG_INCLUDE_ALL_MODELS = False  # Explicit registration preferred

# models.py
from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField

class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    ssn = models.CharField(max_length=11)  # Sensitive
    
    history = AuditlogHistoryField()
    
    class Meta:
        ordering = ['-id']

# Register with field exclusions (never audit the raw SSN value)
auditlog.register(
    Customer,
    exclude_fields=['ssn'],
    mask_fields=['email'],  # Custom: mask in audit display
)

# Custom serializer for complex audit needs
from auditlog.diff import model_instance_diff

class EnhancedAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set additional context available to audit entries
        set_actor = request.user if request.user.is_authenticated else None
        with auditlog_context(
            actor=set_actor,
            remote_addr=self._get_client_ip(request),
            additional_data={
                'correlation_id': request.META.get('HTTP_X_CORRELATION_ID'),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'service': 'customer-api',
            }
        ):
            response = self.get_response(request)
        return response
```

### 3.5 Microservices Audit Schema and Correlation

In distributed systems, a single user action triggers events across multiple services. Correlation IDs thread audit entries together.

```json
{
  "$schema": "https://company.internal/schemas/audit-event-v2.json",
  "event_id": "evt_01HYX3KM7P9Q2R4S5T6U7V8W9X",
  "event_type": "customer.payment.processed",
  "event_version": "2.1",
  "timestamp": "2024-07-15T14:23:45.123456Z",
  "source": {
    "service": "payment-service",
    "instance": "payment-service-7b8c9d-4xk2p",
    "version": "3.2.1",
    "environment": "production"
  },
  "actor": {
    "type": "user",
    "id": "usr_01HYX3KM7P9Q2R4S5T",
    "email_hash": "sha256:a1b2c3...",
    "roles": ["customer"],
    "session_id": "ses_01HYX3KM7P9Q"
  },
  "context": {
    "correlation_id": "cor_01HYX3KM7P9Q2R4S5T6U",
    "causation_id": "evt_01HYX3KM7P9Q2R4S5T6U7V8W9W",
    "trace_id": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    "span_id": "00f067aa0ba902b7",
    "request_id": "req_01HYX3KM7P9Q2R4"
  },
  "resource": {
    "type": "payment",
    "id": "pay_01HYX3KM7P9Q2R",
    "parent_type": "order",
    "parent_id": "ord_01HYX3KM7P9Q"
  },
  "action": {
    "type": "PROCESS",
    "result": "SUCCESS",
    "duration_ms": 234
  },
  "changes": {
    "before": {"status": "pending", "amount": null},
    "after": {"status": "completed", "amount": 9999},
    "diff": [
      {"op": "replace", "path": "/status", "value": "completed"},
      {"op": "add", "path": "/amount", "value": 9999}
    ]
  },
  "metadata": {
    "ip_address": "198.51.100.42",
    "geo": {"country": "DE", "region": "BY"},
    "risk_score": 0.08
  }
}
```

**Correlation across services:**

```
User clicks "Pay" →
  [API Gateway] correlation_id=cor_ABC, request_id=req_001
    → [Order Service] correlation_id=cor_ABC, causation_id=evt_order_created
      → [Payment Service] correlation_id=cor_ABC, causation_id=evt_payment_initiated
        → [Fraud Service] correlation_id=cor_ABC, causation_id=evt_fraud_check
      → [Notification Service] correlation_id=cor_ABC, causation_id=evt_payment_completed
    → [Inventory Service] correlation_id=cor_ABC, causation_id=evt_order_confirmed
```

All events sharing `correlation_id=cor_ABC` can be reconstructed into a complete timeline of the user action.

---

## 4. Log Integrity and Tamper Detection

### 4.1 Cryptographic Signing of Log Entries

**HMAC-Based Signing:**

```python
import hmac
import hashlib
import json
from typing import Optional

class SignedAuditLogger:
    """Audit logger with HMAC integrity verification."""
    
    def __init__(self, signing_key: bytes):
        # Key should come from HSM or secrets manager, never hardcoded
        self._key = signing_key
    
    def sign_entry(self, entry: dict) -> dict:
        """Add HMAC signature to an audit entry."""
        canonical = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            self._key,
            canonical.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return {**entry, '_signature': signature, '_algorithm': 'hmac-sha256'}
    
    def verify_entry(self, signed_entry: dict) -> bool:
        """Verify the HMAC signature of an audit entry."""
        signature = signed_entry.pop('_signature', None)
        signed_entry.pop('_algorithm', None)
        if not signature:
            return False
        canonical = json.dumps(signed_entry, sort_keys=True, separators=(',', ':'))
        expected = hmac.new(
            self._key,
            canonical.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
```

**Digital Signature Approach (asymmetric, for non-repudiation):**

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
import base64

class AsymmetricAuditSigner:
    """Digital signature for audit entries — provides non-repudiation."""
    
    def __init__(self, private_key_path: str):
        with open(private_key_path, 'rb') as f:
            self._private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
        self._public_key = self._private_key.public_key()
    
    def sign(self, entry: dict) -> str:
        canonical = json.dumps(entry, sort_keys=True, separators=(',', ':')).encode()
        signature = self._private_key.sign(
            canonical,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('ascii')
    
    def verify(self, entry: dict, signature_b64: str, public_key) -> bool:
        canonical = json.dumps(entry, sort_keys=True, separators=(',', ':')).encode()
        signature = base64.b64decode(signature_b64)
        try:
            public_key.verify(
                signature, canonical,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
```

### 4.2 Blockchain-Inspired Audit Logs

While full blockchain consensus is overkill for most audit systems, the data structure principles provide strong tamper evidence:

```python
import time
import hashlib
import json

class AuditBlock:
    """A block in the audit chain containing multiple entries."""
    
    def __init__(self, index: int, entries: list, previous_hash: str):
        self.index = index
        self.timestamp = time.time()
        self.entries = entries
        self.previous_hash = previous_hash
        self.nonce = 0  # Optional: proof-of-work for additional tamper cost
        self.hash = self.compute_hash()
    
    def compute_hash(self) -> str:
        block_data = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'entries': self.entries,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()


class AuditBlockchain:
    """Blockchain-structured audit log with periodic checkpointing."""
    
    def __init__(self, block_size: int = 100):
        self.chain = [self._create_genesis_block()]
        self.pending_entries = []
        self.block_size = block_size
    
    def _create_genesis_block(self) -> AuditBlock:
        return AuditBlock(0, [{'event': 'chain_initialized'}], '0' * 64)
    
    def add_entry(self, entry: dict) -> None:
        self.pending_entries.append(entry)
        if len(self.pending_entries) >= self.block_size:
            self._seal_block()
    
    def _seal_block(self) -> AuditBlock:
        previous = self.chain[-1]
        block = AuditBlock(
            index=len(self.chain),
            entries=self.pending_entries.copy(),
            previous_hash=previous.hash
        )
        self.chain.append(block)
        self.pending_entries = []
        return block
    
    def verify_integrity(self) -> tuple[bool, int]:
        """Verify the entire chain. Returns (valid, first_broken_index)."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            if current.hash != current.compute_hash():
                return False, i
            if current.previous_hash != previous.hash:
                return False, i
        return True, -1
```

### 4.3 AWS CloudTrail Log File Integrity Validation

CloudTrail provides built-in digest files that enable validation of log file integrity:

```bash
# Validate CloudTrail log integrity
aws cloudtrail validate-logs \
    --trail-arn arn:aws:cloudtrail:eu-west-1:123456789012:trail/production-trail \
    --start-time "2024-07-01T00:00:00Z" \
    --end-time "2024-07-15T23:59:59Z" \
    --verbose

# CloudTrail digest file structure (simplified):
# {
#   "digestStartTime": "2024-07-15T14:00:00Z",
#   "digestEndTime": "2024-07-15T15:00:00Z",
#   "digestS3Bucket": "company-cloudtrail-logs",
#   "digestS3Object": "AWSLogs/.../digest.json.gz",
#   "previousDigestHashValue": "sha256:abcdef...",
#   "previousDigestS3Object": "AWSLogs/.../previous_digest.json.gz",
#   "logFiles": [
#     {
#       "s3Object": "AWSLogs/.../trail.json.gz",
#       "hashValue": "sha256:123456...",
#       "hashAlgorithm": "SHA-256"
#     }
#   ],
#   "digestPublicKeyFingerprint": "ab12cd34..."
# }
```

### 4.4 Immutable Storage

**AWS S3 Object Lock:**

```python
import boto3

s3 = boto3.client('s3')

# Enable Object Lock on bucket (must be set at creation)
# Governance mode: can be overridden with special permissions
# Compliance mode: CANNOT be overridden by anyone, including root account

def store_audit_log_immutable(bucket: str, key: str, data: bytes, retention_days: int):
    """Store audit log with compliance-mode object lock."""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ObjectLockMode='COMPLIANCE',
        ObjectLockRetainUntilDate=datetime.utcnow() + timedelta(days=retention_days),
        ContentType='application/json',
        ServerSideEncryption='aws:kms',
        SSEKMSKeyId='alias/audit-log-key'
    )

# Legal hold (indefinite retention for litigation)
def apply_legal_hold(bucket: str, key: str):
    s3.put_object_legal_hold(
        Bucket=bucket,
        Key=key,
        LegalHold={'Status': 'ON'}
    )
```

**Azure Immutable Blob Storage:**

```bash
# Set time-based immutability policy on container
az storage container immutability-policy create \
    --account-name auditlogs \
    --container-name compliance-logs \
    --period 2555  # 7 years in days

# Lock the policy (irreversible — cannot be decreased or removed)
az storage container immutability-policy lock \
    --account-name auditlogs \
    --container-name compliance-logs \
    --if-match "etag-value"
```

---

## 5. SIEM Integration for Data Systems

### 5.1 Structured Logging Formats

**JSON Structured Logging (preferred for modern SIEM):**

```json
{
  "@timestamp": "2024-07-15T14:23:45.123Z",
  "event.kind": "event",
  "event.category": ["database"],
  "event.type": ["access"],
  "event.action": "select",
  "event.outcome": "success",
  "event.duration": 234000000,
  "source.ip": "10.0.1.42",
  "source.port": 54321,
  "user.name": "app_service_account",
  "user.id": "usr_01HYX3KM7P9Q",
  "database.name": "production_customers",
  "database.type": "postgresql",
  "database.instance": "pg-primary-01",
  "db.statement": "SELECT id, name, email FROM customers WHERE region = $1",
  "db.rows_affected": 15234,
  "db.operation": "SELECT",
  "labels.correlation_id": "cor_01HYX3KM7P9Q",
  "labels.risk_level": "high",
  "labels.data_classification": "PII"
}
```

**Common Event Format (CEF) for legacy SIEM:**

```
CEF:0|CompanyDB|AuditSystem|2.0|DB_SELECT|Bulk Data Access|7|
  src=10.0.1.42 suser=app_service_account
  cs1Label=Database cs1=production_customers
  cs2Label=Query cs2=SELECT id, name, email FROM customers
  cn1Label=RowsReturned cn1=15234
  cs3Label=CorrelationId cs3=cor_01HYX3KM7P9Q
  rt=Jul 15 2024 14:23:45
```

### 5.2 Database Audit to SIEM Pipeline

**Filebeat configuration for PostgreSQL audit logs:**

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/postgresql/postgresql-*-main.log
    multiline:
      pattern: '^\d{4}-\d{2}-\d{2}'
      negate: true
      match: after
    fields:
      source_type: postgresql_audit
      environment: production
      cluster: pg-primary

  - type: log
    enabled: true
    paths:
      - /var/log/postgresql/pgaudit.log
    json.keys_under_root: true
    json.add_error_key: true
    fields:
      source_type: pgaudit
      environment: production

processors:
  - dissect:
      tokenizer: '%{timestamp} [%{pid}-%{line_num}] %{user}@%{database} %{message}'
      field: message
      target_prefix: pg
      when:
        has_fields: ['pg']

  - script:
      lang: javascript
      source: |
        function process(event) {
          var msg = event.Get("message");
          if (msg && msg.includes("AUDIT:")) {
            var parts = msg.split(",");
            event.Put("audit.type", parts[0].replace("AUDIT: ", ""));
            event.Put("audit.statement_id", parts[1]);
            event.Put("audit.substatement_id", parts[2]);
            event.Put("audit.class", parts[3]);
            event.Put("audit.command", parts[4]);
            event.Put("audit.object_type", parts[5]);
            event.Put("audit.object_name", parts[6]);
            event.Put("audit.statement", parts.slice(7).join(","));
          }
        }

output.elasticsearch:
  hosts: ["https://es-cluster:9200"]
  index: "db-audit-%{+yyyy.MM.dd}"
  ssl.certificate_authorities: ["/etc/pki/ca.pem"]
  ssl.certificate: "/etc/pki/filebeat.pem"
  ssl.key: "/etc/pki/filebeat-key.pem"
```

### 5.3 Real-Time Alerting Rules

**Elasticsearch Watcher / Kibana Rules:**

```json
{
  "trigger": {
    "schedule": {"interval": "1m"}
  },
  "input": {
    "search": {
      "request": {
        "indices": ["db-audit-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {"range": {"@timestamp": {"gte": "now-5m"}}},
                {"term": {"audit.command": "SELECT"}},
                {"range": {"db.rows_affected": {"gte": 10000}}}
              ],
              "must_not": [
                {"terms": {"user.name": ["etl_service", "analytics_readonly"]}}
              ]
            }
          },
          "aggs": {
            "by_user": {
              "terms": {"field": "user.name", "size": 10},
              "aggs": {
                "total_rows": {"sum": {"field": "db.rows_affected"}}
              }
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": {"ctx.payload.hits.total.value": {"gte": 1}}
  },
  "actions": {
    "alert_security": {
      "webhook": {
        "method": "POST",
        "url": "https://siem.internal/api/alert",
        "body": "{{#toJson}}ctx.payload{{/toJson}}"
      }
    }
  }
}
```

**Splunk SPL correlation rules:**

```spl
| Index=db_audit sourcetype=pgaudit
| where audit_command="SELECT" AND rows_returned > 5000
| stats count as query_count, sum(rows_returned) as total_rows by user, src_ip, database
| where total_rows > 100000 OR query_count > 50
| lookup known_etl_accounts user OUTPUT is_etl
| where is_etl!="true"
| eval severity=case(
    total_rows > 1000000, "critical",
    total_rows > 500000, "high",
    total_rows > 100000, "medium",
    1=1, "low"
  )
| sendalert data_exfiltration_detected
```

### 5.4 Detection Rules for Data Exfiltration

```yaml
# Sigma rule format (SIEM-agnostic)
title: Potential Database Exfiltration - Bulk SELECT
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Detects bulk data retrieval from sensitive tables outside normal ETL windows
author: Security Engineering
date: 2024/07/15
references:
  - https://attack.mitre.org/techniques/T1530/
logsource:
  product: postgresql
  service: pgaudit
detection:
  selection:
    audit.command: SELECT
    audit.object_name:
      - customers
      - transactions
      - credentials
      - payment_methods
  filter_etl:
    user.name:
      - etl_service
      - analytics_readonly
      - backup_service
  filter_hours:
    # Normal ETL window: 02:00-05:00 UTC
    "@timestamp|time": "02:00-05:00"
  condition: selection AND NOT filter_etl AND NOT filter_hours
  timeframe: 5m
  count:
    field: db.rows_affected
    gt: 10000
level: high
tags:
  - attack.exfiltration
  - attack.t1530
falsepositives:
  - Legitimate ad-hoc analytics queries
  - Incident response investigations
  - Data migration activities
```

**Privilege Escalation Detection:**

```yaml
title: Database Privilege Escalation Attempt
detection:
  selection_grant:
    audit.command:
      - GRANT
      - ALTER ROLE
      - CREATE ROLE
    audit.class: ROLE
  selection_schema:
    audit.command:
      - ALTER TABLE
      - DROP TABLE
      - TRUNCATE
    audit.class: DDL
  filter_admin:
    user.name:
      - dba_admin
      - terraform_service
  condition: (selection_grant OR selection_schema) AND NOT filter_admin
level: critical
```

---

## 6. Forensic Analysis of Database Activity

### 6.1 Query Log Analysis for Breach Investigation

When investigating a suspected data breach, the forensic analyst must reconstruct the complete timeline of database activity. The methodology:

**Phase 1: Scope the Investigation Window**

```sql
-- Identify the earliest suspicious activity
-- Look for unusual access patterns in pg_stat_statements
SELECT
    userid,
    queryid,
    query,
    calls,
    rows,
    min_exec_time,
    max_exec_time,
    mean_exec_time
FROM pg_stat_statements
WHERE query ~* '(COPY|pg_dump|SELECT.*INTO|UNION.*SELECT)'
  AND rows > 1000
ORDER BY rows DESC;

-- Check for connection anomalies
SELECT
    usename,
    client_addr,
    application_name,
    backend_start,
    state,
    query
FROM pg_stat_activity
WHERE backend_start > '2024-07-01'
  AND client_addr NOT IN (SELECT ip FROM known_application_servers);
```

**Phase 2: Reconstruct Activity Timeline**

```bash
#!/bin/bash
# Extract and correlate events from multiple log sources

# PostgreSQL connection logs
grep "connection authorized" /var/log/postgresql/postgresql-16-main.log \
    | awk '{print $1, $2, $NF}' \
    | sort -k1,2 > /forensics/case-001/pg_connections.txt

# pgaudit entries for the suspect user
grep "AUDIT:" /var/log/postgresql/postgresql-16-main.log \
    | grep "suspect_user" \
    | sort > /forensics/case-001/pg_audit_suspect.txt

# Correlate with application access logs
grep "suspect_user\|suspect_session_id" /var/log/app/access.log \
    | sort -t' ' -k4 > /forensics/case-001/app_access.txt

# Build unified timeline
paste -d'|' /forensics/case-001/pg_connections.txt \
    /forensics/case-001/pg_audit_suspect.txt \
    | sort -t'|' -k1 > /forensics/case-001/unified_timeline.txt
```

### 6.2 Identifying Data Exfiltration Patterns

Common exfiltration indicators in database audit logs:

1. **Enumeration Queries** — sequential ID scanning (`WHERE id > X LIMIT Y` repeated with increasing X)
2. **Schema Reconnaissance** — queries against `information_schema`, `pg_catalog` from application accounts
3. **Bulk Export** — `COPY TO`, `SELECT INTO OUTFILE`, unusually high row counts
4. **Column Targeting** — queries specifically selecting PII columns (SSN, email, credit card)
5. **Off-Hours Activity** — database access outside normal business/ETL hours
6. **New Client IPs** — connections from previously unseen IP addresses
7. **Privilege Escalation Chain** — GRANT statements followed by sensitive data access

```sql
-- Forensic query: Detect enumeration pattern
WITH sequential_queries AS (
    SELECT
        user_name,
        query,
        rows_returned,
        query_time,
        LAG(query_time) OVER (PARTITION BY user_name ORDER BY query_time) AS prev_query_time,
        LAG(rows_returned) OVER (PARTITION BY user_name ORDER BY query_time) AS prev_rows
    FROM audit_log
    WHERE query ILIKE '%SELECT%FROM%customers%'
      AND query_time BETWEEN '2024-07-10' AND '2024-07-15'
)
SELECT *
FROM sequential_queries
WHERE query_time - prev_query_time < INTERVAL '5 seconds'
  AND rows_returned > 100
ORDER BY query_time;
```

### 6.3 Transaction Log Forensics

**PostgreSQL WAL Analysis with pg_waldump:**

```bash
# Decode WAL segments to find modifications to a specific table
pg_waldump /var/lib/postgresql/16/main/pg_wal/000000010000000100000042 \
    --relation=16384/16389 \  # Database OID / Table OID
    --start=0/42000000 \
    --end=0/43000000 \
    --rmgr=Heap

# Output shows individual tuple operations:
# rmgr: Heap    len (rec/tot): 54/150, tx: 12345, lsn: 0/42001A30
#   HOT_UPDATE off 5 xmax 12345 flags 0x00 ; new off 6 xmax 0 flags 0x00
#   blkref #0: rel 1663/16384/16389 blk 42 FPW

# Find which transaction modified specific data
pg_waldump /var/lib/postgresql/16/main/pg_wal/* \
    --start=0/40000000 \
    2>/dev/null | grep "tx: 12345" | head -50
```

**MySQL Binlog Analysis with mysqlbinlog:**

```bash
# Decode binary log for a specific time range
mysqlbinlog \
    --start-datetime="2024-07-10 02:00:00" \
    --end-datetime="2024-07-10 06:00:00" \
    --database=production \
    --verbose \
    /var/log/mysql/binlog.000042

# Extract specific table operations
mysqlbinlog --verbose /var/log/mysql/binlog.000042 \
    | grep -A5 "### UPDATE.*customers" \
    | head -200

# Row-based binlog shows before/after images:
# ### UPDATE `production`.`customers`
# ### WHERE
# ###   @1=42          /* INT meta=0 nullable=0 */
# ###   @2='John Doe'  /* VARCHAR(200) meta=200 nullable=0 */
# ###   @3='john@example.com' /* VARCHAR(255) meta=255 nullable=0 */
# ### SET
# ###   @1=42
# ###   @2='John Doe'
# ###   @3='attacker@evil.com'  /* <-- EMAIL CHANGED */
```

### 6.4 Deleted Data Recovery from WAL

```bash
# PostgreSQL: Recover deleted rows from WAL
# Step 1: Identify the LSN range around the deletion
pg_waldump /var/lib/postgresql/16/main/pg_wal/* \
    --rmgr=Heap \
    --start=0/50000000 \
    2>/dev/null | grep "DELETE" | grep "rel 1663/16384/16389"

# Step 2: Use pg_filedump to examine heap pages
pg_filedump -D int,varchar,varchar,timestamp \
    /var/lib/postgresql/16/main/base/16384/16389 \
    | grep "DEAD" | head -20

# Step 3: Point-in-time recovery to just before deletion
# (requires continuous WAL archiving)
cat > /tmp/recovery.conf << 'EOF'
restore_command = 'cp /secure/wal_archive/%f %p'
recovery_target_time = '2024-07-10 01:59:00+00'
recovery_target_action = 'pause'
EOF

# Step 4: Start recovery instance and extract data
pg_ctl -D /forensics/recovery_instance start
psql -h /forensics/recovery_instance -c \
    "COPY (SELECT * FROM customers WHERE id IN (42,43,44)) TO '/forensics/recovered_data.csv' CSV HEADER;"
```

### 6.5 Forensic Evidence Preservation

```bash
#!/bin/bash
# Evidence collection script — maintain chain of custody
CASE_ID="INC-2024-0715"
EVIDENCE_DIR="/forensics/cases/${CASE_ID}"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

mkdir -p "${EVIDENCE_DIR}/raw" "${EVIDENCE_DIR}/hashes"

# Collect with integrity hash
collect_evidence() {
    local source="$1"
    local label="$2"
    local dest="${EVIDENCE_DIR}/raw/${label}_${TIMESTAMP}"
    
    cp -p "$source" "$dest"
    sha256sum "$dest" > "${EVIDENCE_DIR}/hashes/${label}_${TIMESTAMP}.sha256"
    
    echo "${TIMESTAMP}|COLLECTED|${label}|$(sha256sum "$dest" | cut -d' ' -f1)|$(whoami)" \
        >> "${EVIDENCE_DIR}/chain_of_custody.log"
}

# Collect database logs
collect_evidence "/var/log/postgresql/postgresql-16-main.log" "pg_main_log"
collect_evidence "/var/log/postgresql/pgaudit.log" "pgaudit_log"

# Collect WAL segments (if authorized)
for wal in /var/lib/postgresql/16/main/pg_wal/0000000100000001*; do
    collect_evidence "$wal" "wal_$(basename $wal)"
done

# Collect application logs
collect_evidence "/var/log/app/access.log" "app_access"
collect_evidence "/var/log/app/auth.log" "app_auth"

# Sign the custody log
gpg --detach-sign --armor "${EVIDENCE_DIR}/chain_of_custody.log"
```

---

## 7. Compliance Requirements for Audit

### 7.1 SOX Section 302/404 — Financial Data Audit Trails

The Sarbanes-Oxley Act (SOX) requires publicly traded companies to maintain internal controls over financial reporting. Sections 302 and 404 mandate:

**Section 302 Requirements:**
- Officers must certify the accuracy of financial statements
- Internal controls must be evaluated for effectiveness
- Material changes to internal controls must be disclosed

**Section 404 Requirements:**
- Annual assessment of internal controls over financial reporting (ICFR)
- External auditor attestation of management's assessment
- Evidence of control effectiveness through audit trails

**Database audit requirements for SOX compliance:**

```sql
-- SOX-compliant audit configuration for financial databases
-- Requirement: Track ALL modifications to financial data with who/when/what

-- Mandatory audit coverage:
-- 1. All INSERT/UPDATE/DELETE on financial tables
-- 2. All access to chart of accounts, journal entries, GL
-- 3. Schema modifications (DDL)
-- 4. User privilege changes
-- 5. Application configuration changes

-- Retention: Minimum 7 years (SOX does not specify exactly,
-- but statute of limitations + audit cycle typically requires 7 years)

-- Example: Financial journal entry audit
CREATE TABLE gl_journal_entries (
    entry_id        BIGSERIAL PRIMARY KEY,
    fiscal_year     INTEGER NOT NULL,
    period          INTEGER NOT NULL,
    account_code    VARCHAR(20) NOT NULL,
    debit_amount    NUMERIC(18,2),
    credit_amount   NUMERIC(18,2),
    description     TEXT,
    posted_by       UUID NOT NULL,
    posted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_by     UUID,
    approved_at     TIMESTAMPTZ,
    -- SOX requires dual control for material entries
    CONSTRAINT dual_approval CHECK (
        (debit_amount + credit_amount < 10000) OR approved_by IS NOT NULL
    )
);

-- Audit trigger captures pre/post state with SOX-required fields
-- See Section 3.2 for implementation
```

### 7.2 HIPAA Audit Controls — Section 164.312(b)

HIPAA (Health Insurance Portability and Accountability Act) Technical Safeguard §164.312(b) states:

> "Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information (ePHI)."

**Required audit capabilities:**

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| User identification | Unique user ID for all ePHI access | `actor_id` in every audit entry |
| Access monitoring | Log all access to ePHI | pgaudit on all PHI tables |
| Login monitoring | Track successful and failed login attempts | Connection logging + auth failure alerts |
| Integrity controls | Protect audit logs from tampering | Hash chains + immutable storage |
| Review procedures | Regular review of audit log activity | Weekly automated reports + manual review |

**HIPAA minimum retention: 6 years from creation date or last effective date.**

```sql
-- HIPAA-compliant audit view for ePHI access reporting
CREATE VIEW hipaa_access_report AS
SELECT
    a.performed_at AS access_time,
    a.actor_id,
    u.username,
    u.role,
    a.action,
    a.entity_type AS resource_type,
    a.entity_id AS record_id,
    a.source_ip,
    a.metadata->>'reason' AS access_reason,
    a.metadata->>'patient_consent' AS consent_status
FROM entity_audit a
JOIN users u ON u.id = a.actor_id
WHERE a.entity_type IN ('patient_record', 'medical_history', 'prescription', 'lab_result')
ORDER BY a.performed_at DESC;

-- Emergency access ("break the glass") audit
CREATE TABLE break_glass_access (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL,
    patient_id      UUID NOT NULL,
    reason          TEXT NOT NULL,
    accessed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    supervisor_notified BOOLEAN NOT NULL DEFAULT true,
    review_status   VARCHAR(20) DEFAULT 'pending',
    reviewed_by     UUID,
    reviewed_at     TIMESTAMPTZ
);
```

### 7.3 PCI-DSS Requirement 10 — Tracking and Monitoring

PCI-DSS Requirement 10 mandates tracking and monitoring all access to network resources and cardholder data:

**10.1** — Implement audit trails linking all access to system components to each individual user
**10.2** — Implement automated audit trails for:
- Individual user access to cardholder data
- Actions taken by any individual with root/admin privileges
- Access to all audit trails
- Invalid logical access attempts
- Use of identification and authentication mechanisms
- Initialization, stopping, or pausing of audit logs
- Creation and deletion of system-level objects

**10.3** — Record at least: user identification, type of event, date/time, success/failure, origination, identity/name of affected data/resource

**10.5** — Secure audit trails so they cannot be altered:
- Limit viewing of audit trails to those with job-related need
- Protect audit trail files from unauthorized modifications
- Promptly back up audit trail files to a centralized log server
- Write logs for external-facing technologies onto a secure, centralized, internal log server

**10.7** — Retain audit trail history for at least 12 months, with at least 3 months immediately available for analysis

```sql
-- PCI-DSS compliant cardholder data access audit
-- Note: Cardholder data (PAN, CVV, expiration) should be tokenized/encrypted at rest.
-- Audit logs must NEVER contain actual cardholder data.

CREATE TABLE pci_access_audit (
    audit_id        BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id         VARCHAR(100) NOT NULL,    -- 10.3.1: User identification
    event_type      VARCHAR(50) NOT NULL,     -- 10.3.2: Type of event
    success         BOOLEAN NOT NULL,         -- 10.3.4: Success or failure
    source_ip       INET NOT NULL,            -- 10.3.5: Origination
    resource_type   VARCHAR(100) NOT NULL,    -- 10.3.6: Affected resource
    resource_id     TEXT NOT NULL,
    -- Additional context
    card_token      VARCHAR(64),              -- Token reference, NEVER actual PAN
    action_detail   TEXT,
    system_component VARCHAR(100) NOT NULL
);

-- Partition with retention policy (10.7: 12 months minimum)
-- Immediate access: last 3 months
-- Archive: remaining 9 months
```

### 7.4 GDPR Article 30 — Records of Processing Activities

GDPR Article 30 requires controllers to maintain records of processing activities including:
- Purpose of processing
- Categories of data subjects and personal data
- Recipients to whom data is disclosed
- Transfers to third countries
- Retention periods
- Technical and organizational security measures

```sql
-- GDPR processing activity log
CREATE TABLE gdpr_processing_log (
    id                  BIGSERIAL PRIMARY KEY,
    processing_time     TIMESTAMPTZ NOT NULL DEFAULT now(),
    controller_id       VARCHAR(100) NOT NULL,
    processor_id        VARCHAR(100),
    -- Article 30(1) required fields
    purpose             TEXT NOT NULL,
    legal_basis         VARCHAR(50) NOT NULL,  -- consent, contract, legal_obligation, etc.
    data_subject_category VARCHAR(100) NOT NULL,
    personal_data_categories TEXT[] NOT NULL,
    recipient_categories TEXT[],
    third_country_transfers JSONB,
    retention_period    INTERVAL,
    -- Technical measures reference
    security_measures   TEXT[],
    -- Data subject rights
    data_subject_id_hash VARCHAR(64),  -- SHA-256 of data subject identifier
    action_type         VARCHAR(50) NOT NULL  -- collect, process, share, delete, export
);

-- Right to erasure (Article 17) audit
CREATE TABLE gdpr_erasure_log (
    id              BIGSERIAL PRIMARY KEY,
    request_time    TIMESTAMPTZ NOT NULL,
    completed_time  TIMESTAMPTZ,
    data_subject_hash VARCHAR(64) NOT NULL,
    systems_affected TEXT[] NOT NULL,
    data_categories_erased TEXT[] NOT NULL,
    verification_method VARCHAR(50) NOT NULL,
    performed_by    UUID NOT NULL,
    exceptions      TEXT,  -- Legitimate reasons for partial erasure
    certificate_hash VARCHAR(64)  -- Hash of erasure certificate
);
```

### 7.5 Retention Requirements Summary

| Regulation | Minimum Retention | Notes |
|-----------|-------------------|-------|
| SOX | 7 years | Financial records and audit working papers |
| HIPAA | 6 years | From creation or last effective date |
| PCI-DSS | 12 months | 3 months immediately available |
| GDPR | As long as necessary | Must justify retention period |
| GLBA | 5 years | Financial institution customer records |
| SEC Rule 17a-4 | 6 years | Broker-dealer records |
| FERPA | 5 years | Educational records audit |
| FedRAMP | 90 days online, 1 year archived | Federal systems |

---

## 8. Real-Time Monitoring and Alerting

### 8.1 Database Activity Monitoring (DAM)

Database Activity Monitoring tools provide real-time visibility into all database activity, independent of native audit mechanisms. This independence is critical because native audit can be disabled by privileged users.

**Architecture:**

```
                    ┌─────────────────────────────────────┐
                    │        DAM Management Console       │
                    │   (Policy, Alerts, Reports, SIEM)   │
                    └───────────────┬─────────────────────┘
                                    │
                    ┌───────────────┴─────────────────────┐
                    │         DAM Analysis Engine          │
                    │  (Pattern matching, ML, baselines)   │
                    └───────────────┬─────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
     ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐
     │  Network Tap /   │  │   Agent-Based   │  │   Native Audit  │
     │  Span Port       │  │   Collection    │  │   Log Ingestion │
     │  (Passive)       │  │   (On-host)     │  │   (Pull/Push)   │
     └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
              │                     │                     │
     ┌────────┴─────────────────────┴─────────────────────┴────────┐
     │                     Database Server                          │
     └─────────────────────────────────────────────────────────────┘
```

**Commercial tools:** Imperva SecureSphere/Data Security, IBM Guardium, Oracle Audit Vault, McAfee Database Security.

**Open-source alternatives:**

- **pgBadger** — PostgreSQL log analyzer with detailed reports
- **Percona PMM** — MySQL/PostgreSQL monitoring with query analytics
- **Wazuh** — SIEM with database audit log collection
- **GoAudit** — Linux audit framework with database rule sets
- **Apache Metron** — Real-time big data security framework

### 8.2 Real-Time Query Analysis

```python
# Real-time query anomaly detection using statistical baselines

import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta

class QueryAnomalyDetector:
    """Detects anomalous database query patterns in real-time."""
    
    def __init__(self, baseline_window_hours: int = 168):  # 1 week
        self.baseline_window = timedelta(hours=baseline_window_hours)
        self.user_baselines = defaultdict(lambda: {
            'query_counts': [],
            'row_counts': [],
            'tables_accessed': set(),
            'access_hours': set(),
            'avg_query_rate': 0.0,
            'std_query_rate': 0.0,
        })
    
    def update_baseline(self, user_id: str, metrics: dict):
        """Update the rolling baseline for a user."""
        baseline = self.user_baselines[user_id]
        baseline['query_counts'].append(metrics['query_count'])
        baseline['row_counts'].append(metrics['rows_returned'])
        baseline['tables_accessed'].add(metrics['table_name'])
        baseline['access_hours'].add(metrics['hour_of_day'])
        
        # Keep only recent window
        max_samples = self.baseline_window.total_seconds() / 60  # per-minute samples
        if len(baseline['query_counts']) > max_samples:
            baseline['query_counts'] = baseline['query_counts'][-int(max_samples):]
            baseline['row_counts'] = baseline['row_counts'][-int(max_samples):]
        
        # Recalculate statistics
        if len(baseline['query_counts']) > 30:
            baseline['avg_query_rate'] = np.mean(baseline['query_counts'])
            baseline['std_query_rate'] = np.std(baseline['query_counts'])
    
    def analyze_event(self, event: dict) -> list:
        """Analyze a query event for anomalies. Returns list of findings."""
        alerts = []
        user_id = event['user_id']
        baseline = self.user_baselines[user_id]
        
        # Anomaly 1: Volume spike (>3 standard deviations)
        if baseline['std_query_rate'] > 0:
            z_score = (event['rows_returned'] - np.mean(baseline['row_counts'])) / np.std(baseline['row_counts'])
            if z_score > 3:
                alerts.append({
                    'type': 'VOLUME_ANOMALY',
                    'severity': 'HIGH',
                    'detail': f'Row count {event["rows_returned"]} is {z_score:.1f} std devs above baseline',
                    'user_id': user_id,
                    'z_score': z_score
                })
        
        # Anomaly 2: New table access
        if event['table_name'] not in baseline['tables_accessed']:
            alerts.append({
                'type': 'NEW_TABLE_ACCESS',
                'severity': 'MEDIUM',
                'detail': f'First-time access to table {event["table_name"]}',
                'user_id': user_id
            })
        
        # Anomaly 3: Off-hours access
        hour = event['timestamp'].hour
        if hour not in baseline['access_hours'] and len(baseline['access_hours']) > 5:
            alerts.append({
                'type': 'OFF_HOURS_ACCESS',
                'severity': 'MEDIUM',
                'detail': f'Access at {hour}:00 UTC, outside normal pattern',
                'user_id': user_id
            })
        
        # Anomaly 4: Sensitive column access
        sensitive_patterns = ['ssn', 'credit_card', 'password', 'secret', 'token', 'salary']
        accessed_columns = event.get('columns_accessed', [])
        sensitive_hits = [c for c in accessed_columns if any(p in c.lower() for p in sensitive_patterns)]
        if sensitive_hits:
            alerts.append({
                'type': 'SENSITIVE_DATA_ACCESS',
                'severity': 'HIGH',
                'detail': f'Sensitive columns accessed: {sensitive_hits}',
                'user_id': user_id
            })
        
        return alerts
```

### 8.3 Automated Response Actions

```yaml
# Response playbook configuration
response_policies:
  - name: bulk_data_access_response
    trigger:
      type: VOLUME_ANOMALY
      severity: [HIGH, CRITICAL]
      min_confidence: 0.85
    actions:
      - type: alert
        channels: [security-team-slack, soc-pagerduty]
        template: bulk_access_alert
      - type: log_enrichment
        description: "Gather additional context about the session"
        queries:
          - "SELECT * FROM pg_stat_activity WHERE usename = '{user}'"
          - "SELECT * FROM active_sessions WHERE user_id = '{user_id}'"
      - type: conditional_block
        condition: "rows_returned > 1000000 AND NOT is_etl_account"
        action: terminate_session
        requires_approval: true
        approval_timeout: 300  # seconds

  - name: privilege_escalation_response
    trigger:
      type: PRIVILEGE_CHANGE
      severity: [CRITICAL]
    actions:
      - type: immediate_alert
        channels: [security-team-slack, soc-pagerduty, ciso-sms]
      - type: snapshot
        description: "Capture current database state"
        action: "pg_dump --schema-only > /forensics/snapshots/{timestamp}_schema.sql"
      - type: block
        description: "Revoke newly granted privileges pending review"
        action: "REVOKE {granted_privilege} FROM {grantee}"
        requires_approval: false  # Auto-respond for privilege escalation
```

---

## 9. Cloud Database Auditing

### 9.1 AWS RDS/Aurora Auditing

**RDS PostgreSQL with pgaudit:**

```bash
# Create custom parameter group with pgaudit
aws rds create-db-parameter-group \
    --db-parameter-group-name audit-pg16 \
    --db-parameter-group-family postgres16 \
    --description "PostgreSQL 16 with pgaudit"

aws rds modify-db-parameter-group \
    --db-parameter-group-name audit-pg16 \
    --parameters \
        "ParameterName=shared_preload_libraries,ParameterValue=pgaudit,ApplyMethod=pending-reboot" \
        "ParameterName=pgaudit.log,ParameterValue=ddl+role+write,ApplyMethod=immediate" \
        "ParameterName=pgaudit.log_parameter,ParameterValue=1,ApplyMethod=immediate" \
        "ParameterName=pgaudit.role,ParameterValue=rds_pgaudit,ApplyMethod=immediate"
```

**CloudWatch Logs integration:**

```bash
# Enable audit log export to CloudWatch
aws rds modify-db-instance \
    --db-instance-identifier production-pg \
    --cloudwatch-logs-export-configuration \
        EnableLogTypes=["postgresql","upgrade"]

# Create metric filter for bulk access detection
aws logs put-metric-filter \
    --log-group-name "/aws/rds/instance/production-pg/postgresql" \
    --filter-name "BulkDataAccess" \
    --filter-pattern '[timestamp, pid, user, db, msg = "*AUDIT*", ..., rows > 10000]' \
    --metric-transformations \
        metricName=BulkDataAccessCount,metricNamespace=DatabaseAudit,metricValue=1

# CloudWatch alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "DB-BulkAccess-Alert" \
    --metric-name BulkDataAccessCount \
    --namespace DatabaseAudit \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --alarm-actions "arn:aws:sns:eu-west-1:123456789012:security-alerts"
```

**CloudTrail for RDS API operations:**

```json
{
  "eventSource": "rds.amazonaws.com",
  "eventName": "ModifyDBInstance",
  "userIdentity": {
    "type": "AssumedRole",
    "arn": "arn:aws:sts::123456789012:assumed-role/DBA-Role/session-name"
  },
  "requestParameters": {
    "dBInstanceIdentifier": "production-pg",
    "masterUserPassword": "****"
  },
  "responseElements": {
    "dBInstanceIdentifier": "production-pg",
    "dBInstanceStatus": "modifying"
  }
}
```

### 9.2 GCP Cloud SQL Auditing

```bash
# Enable Cloud SQL audit logging
gcloud sql instances patch production-pg \
    --database-flags=\
cloudsql.enable_pgaudit=on,\
pgaudit.log=all,\
log_connections=on,\
log_disconnections=on,\
log_min_duration_statement=0

# Configure Data Access audit logs (IAM level)
gcloud projects get-iam-policy PROJECT_ID --format=json | jq '
.auditConfigs += [{
  "service": "cloudsql.googleapis.com",
  "auditLogConfigs": [
    {"logType": "ADMIN_READ"},
    {"logType": "DATA_READ"},
    {"logType": "DATA_WRITE"}
  ]
}]' | gcloud projects set-iam-policy PROJECT_ID /dev/stdin

# Query audit logs via gcloud
gcloud logging read '
  resource.type="cloudsql_database" AND
  protoPayload.methodName="cloudsql.instances.query" AND
  protoPayload.request.body:"SELECT" AND
  severity>=WARNING
' --limit=50 --format=json
```

### 9.3 Azure SQL Auditing

```bash
# Enable Azure SQL auditing
az sql server audit-policy update \
    --resource-group production-rg \
    --server production-sql \
    --state Enabled \
    --storage-account auditlogstorage \
    --retention-days 365 \
    --storage-key-type StorageAccessKey

# Enable Microsoft Defender for SQL
az sql server advanced-threat-protection-setting update \
    --resource-group production-rg \
    --server production-sql \
    --state Enabled

# Configure diagnostic settings for Log Analytics
az monitor diagnostic-settings create \
    --resource "/subscriptions/{sub}/resourceGroups/production-rg/providers/Microsoft.Sql/servers/production-sql/databases/production-db" \
    --name "SQLAuditToLogAnalytics" \
    --workspace "/subscriptions/{sub}/resourceGroups/monitoring-rg/providers/Microsoft.OperationalInsights/workspaces/soc-workspace" \
    --logs '[
        {"category": "SQLSecurityAuditEvents", "enabled": true, "retentionPolicy": {"days": 365, "enabled": true}},
        {"category": "DevOpsOperationsAudit", "enabled": true, "retentionPolicy": {"days": 365, "enabled": true}}
    ]'
```

**KQL query for Azure SQL audit analysis:**

```kql
// Detect potential data exfiltration
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.SQL"
| where Category == "SQLSecurityAuditEvents"
| where action_name_s == "SELECT"
| where affected_rows_d > 10000
| where server_principal_name_s !in ("etl_service", "analytics_ro")
| summarize TotalRows=sum(affected_rows_d), QueryCount=count()
    by server_principal_name_s, database_name_s, bin(TimeGenerated, 5m)
| where TotalRows > 100000
| order by TotalRows desc
```

### 9.4 BigQuery Audit Logs

```sql
-- Query BigQuery audit logs from INFORMATION_SCHEMA
SELECT
  creation_time,
  user_email,
  job_type,
  statement_type,
  query,
  total_bytes_processed,
  total_bytes_billed,
  destination_table.table_id,
  referenced_tables
FROM `project.region-eu`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND statement_type = 'SELECT'
  AND total_bytes_processed > 10737418240  -- > 10 GB
ORDER BY total_bytes_processed DESC;

-- Export audit logs to BigQuery for long-term analysis
-- (via Cloud Logging sink)
-- gcloud logging sinks create bq-audit-sink \
--   bigquery.googleapis.com/projects/PROJECT/datasets/audit_logs \
--   --log-filter='resource.type="bigquery_resource"'
```

### 9.5 DynamoDB Streams for Audit

```python
import boto3
import json

dynamodb = boto3.client('dynamodb')
streams = boto3.client('dynamodbstreams')

# Enable streams on the table
dynamodb.update_table(
    TableName='customers',
    StreamSpecification={
        'StreamEnabled': True,
        'StreamViewType': 'NEW_AND_OLD_IMAGES'  # Capture before and after
    }
)

# Lambda function to process stream events into audit log
def lambda_handler(event, context):
    for record in event['Records']:
        audit_entry = {
            'event_id': record['eventID'],
            'event_name': record['eventName'],  # INSERT, MODIFY, REMOVE
            'event_time': record['dynamodb']['ApproximateCreationDateTime'],
            'table_name': record['eventSourceARN'].split('/')[1],
            'keys': record['dynamodb']['Keys'],
            'old_image': record['dynamodb'].get('OldImage'),
            'new_image': record['dynamodb'].get('NewImage'),
            'sequence_number': record['dynamodb']['SequenceNumber'],
            'size_bytes': record['dynamodb']['SizeBytes'],
            'source_ip': record.get('userIdentity', {}).get('principalId', 'unknown'),
        }
        
        # Forward to audit storage (S3 with Object Lock)
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket='audit-logs-immutable',
            Key=f'dynamodb/{audit_entry["table_name"]}/{audit_entry["event_time"]}/{audit_entry["event_id"]}.json',
            Body=json.dumps(audit_entry),
            ObjectLockMode='COMPLIANCE',
            ObjectLockRetainUntilDate=datetime(2031, 7, 15)  # 7 year retention
        )
```

---

## 10. Lab Exercises

### Lab 1: pgaudit with Hash-Chained Integrity Verification

**Objective:** Deploy pgaudit on PostgreSQL 16, capture audit events, and implement a hash-chain verification system that detects any tampering with historical audit records.

**Prerequisites:**
- PostgreSQL 16 with pgaudit extension installed
- Python 3.11+ with `psycopg[binary]` and `cryptography`
- Access to create extensions and modify postgresql.conf

**Step 1: Configure pgaudit**

```bash
# Add to postgresql.conf (or ALTER SYSTEM for dynamic config)
sudo -u postgres psql -c "
    ALTER SYSTEM SET shared_preload_libraries = 'pgaudit';
    ALTER SYSTEM SET pgaudit.log = 'write, ddl, role';
    ALTER SYSTEM SET pgaudit.log_parameter = 'on';
    ALTER SYSTEM SET pgaudit.log_relation = 'on';
    ALTER SYSTEM SET pgaudit.log_statement_once = 'off';
"
sudo systemctl restart postgresql

# Create the audit infrastructure
sudo -u postgres psql << 'SQL'
CREATE EXTENSION IF NOT EXISTS pgaudit;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Audit chain table
CREATE TABLE audit_chain (
    id              BIGSERIAL PRIMARY KEY,
    event_time      TIMESTAMPTZ NOT NULL DEFAULT now(),
    session_id      TEXT NOT NULL,
    user_name       TEXT NOT NULL,
    database_name   TEXT NOT NULL,
    command_tag     TEXT NOT NULL,
    object_type     TEXT,
    object_name     TEXT,
    statement       TEXT NOT NULL,
    parameters      TEXT[],
    rows_affected   BIGINT DEFAULT 0,
    -- Integrity fields
    entry_hash      TEXT NOT NULL,
    previous_hash   TEXT NOT NULL,
    chain_position  BIGINT NOT NULL
);

CREATE INDEX idx_audit_chain_time ON audit_chain(event_time DESC);
CREATE INDEX idx_audit_chain_user ON audit_chain(user_name, event_time DESC);
CREATE INDEX idx_audit_chain_object ON audit_chain(object_name, event_time DESC);

-- Immutability enforcement
CREATE OR REPLACE FUNCTION prevent_audit_chain_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'SECURITY VIOLATION: Audit chain records are immutable. '
                    'Attempt logged and reported.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_chain_immutable_update
    BEFORE UPDATE ON audit_chain FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_chain_modification();

CREATE TRIGGER audit_chain_immutable_delete
    BEFORE DELETE ON audit_chain FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_chain_modification();
SQL
```

**Step 2: Hash chain insertion function**

```sql
CREATE OR REPLACE FUNCTION insert_audit_chain_entry(
    p_session_id TEXT,
    p_user_name TEXT,
    p_database_name TEXT,
    p_command_tag TEXT,
    p_object_type TEXT,
    p_object_name TEXT,
    p_statement TEXT,
    p_parameters TEXT[],
    p_rows_affected BIGINT
) RETURNS BIGINT AS $$
DECLARE
    v_previous_hash TEXT;
    v_chain_position BIGINT;
    v_entry_hash TEXT;
    v_canonical TEXT;
    v_new_id BIGINT;
BEGIN
    -- Get the previous hash (or genesis hash for first entry)
    SELECT entry_hash, chain_position
    INTO v_previous_hash, v_chain_position
    FROM audit_chain
    ORDER BY id DESC
    LIMIT 1
    FOR UPDATE;  -- Lock to prevent concurrent chain breaks
    
    IF v_previous_hash IS NULL THEN
        v_previous_hash := encode(sha256('GENESIS_BLOCK'::bytea), 'hex');
        v_chain_position := 0;
    END IF;
    
    v_chain_position := v_chain_position + 1;
    
    -- Build canonical representation for hashing
    v_canonical := json_build_object(
        'position', v_chain_position,
        'time', now()::text,
        'session', p_session_id,
        'user', p_user_name,
        'db', p_database_name,
        'command', p_command_tag,
        'object', p_object_name,
        'statement', p_statement,
        'previous_hash', v_previous_hash
    )::text;
    
    -- Compute entry hash (SHA-256 of canonical + previous hash)
    v_entry_hash := encode(
        sha256((v_previous_hash || v_canonical)::bytea),
        'hex'
    );
    
    INSERT INTO audit_chain (
        event_time, session_id, user_name, database_name,
        command_tag, object_type, object_name, statement,
        parameters, rows_affected, entry_hash, previous_hash, chain_position
    ) VALUES (
        now(), p_session_id, p_user_name, p_database_name,
        p_command_tag, p_object_type, p_object_name, p_statement,
        p_parameters, p_rows_affected, v_entry_hash, v_previous_hash, v_chain_position
    ) RETURNING id INTO v_new_id;
    
    RETURN v_new_id;
END;
$$ LANGUAGE plpgsql;
```

**Step 3: Verification script**

```python
#!/usr/bin/env python3
"""Verify the integrity of the pgaudit hash chain."""

import hashlib
import json
import sys
import psycopg

def verify_audit_chain(conninfo: str) -> tuple[bool, int, str]:
    """
    Verify the audit chain integrity.
    Returns: (is_valid, break_position, detail_message)
    """
    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, event_time, session_id, user_name, database_name,
                       command_tag, object_name, statement,
                       entry_hash, previous_hash, chain_position
                FROM audit_chain
                ORDER BY id ASC
            """)
            
            expected_previous = hashlib.sha256(b'GENESIS_BLOCK').hexdigest()
            
            for row in cur:
                (row_id, event_time, session_id, user_name, db_name,
                 command_tag, object_name, statement,
                 stored_hash, stored_prev_hash, position) = row
                
                # Verify chain linkage
                if stored_prev_hash != expected_previous:
                    return (False, position,
                            f"Chain break at position {position} (id={row_id}): "
                            f"stored previous_hash={stored_prev_hash[:16]}... "
                            f"expected={expected_previous[:16]}...")
                
                # Recompute hash
                canonical = json.dumps({
                    'position': position,
                    'time': str(event_time),
                    'session': session_id,
                    'user': user_name,
                    'db': db_name,
                    'command': command_tag,
                    'object': object_name,
                    'statement': statement,
                    'previous_hash': stored_prev_hash
                })
                
                computed_hash = hashlib.sha256(
                    (stored_prev_hash + canonical).encode()
                ).hexdigest()
                
                if computed_hash != stored_hash:
                    return (False, position,
                            f"Hash mismatch at position {position} (id={row_id}): "
                            f"stored={stored_hash[:16]}... computed={computed_hash[:16]}...")
                
                expected_previous = stored_hash
            
            return (True, -1, f"Chain verified: {position} entries, integrity intact.")


if __name__ == '__main__':
    conninfo = sys.argv[1] if len(sys.argv) > 1 else "dbname=auditlab"
    valid, pos, msg = verify_audit_chain(conninfo)
    print(f"{'PASS' if valid else 'FAIL'}: {msg}")
    sys.exit(0 if valid else 1)
```

---

### Lab 2: Complete Audit Pipeline (PostgreSQL to Elasticsearch to Kibana)

**Objective:** Build an end-to-end audit pipeline that captures PostgreSQL audit events, ships them through Filebeat, indexes in Elasticsearch, and presents dashboards in Kibana.

**Architecture:**

```
PostgreSQL (pgaudit) → CSV log → Filebeat → Elasticsearch → Kibana
                                                ↓
                                         Alert Rules → Slack/PagerDuty
```

**Step 1: PostgreSQL CSV logging configuration**

```ini
# postgresql.conf
log_destination = 'csvlog'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d.csv'
log_rotation_age = 1d
log_rotation_size = 0
log_min_messages = warning
log_min_error_statement = error
log_statement = 'mod'
log_line_prefix = ''  # CSV format handles fields
```

**Step 2: Filebeat configuration**

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    id: pgaudit-csv
    enabled: true
    paths:
      - /var/log/postgresql/postgresql-*.csv
    fields:
      pipeline: pgaudit
      environment: lab
    processors:
      - dissect:
          tokenizer: '%{log_time},%{user_name},%{database_name},%{process_id},%{connection_from},%{session_id},%{session_line_num},%{command_tag},%{session_start_time},%{virtual_transaction_id},%{transaction_id},%{error_severity},%{sql_state_code},%{message},%{detail},%{hint},%{internal_query},%{internal_query_pos},%{context},%{query},%{query_pos},%{location},%{application_name},%{backend_type}'
          field: message
          target_prefix: pg

      - script:
          lang: javascript
          source: |
            function process(event) {
              var msg = event.Get("pg.message");
              if (msg && msg.startsWith("AUDIT:")) {
                event.Put("is_audit", true);
                var parts = msg.substring(7).split(",");
                event.Put("audit.type", parts[0].trim());
                event.Put("audit.statement_id", parts[1]);
                event.Put("audit.substatement_id", parts[2]);
                event.Put("audit.class", parts[3]);
                event.Put("audit.command", parts[4]);
                event.Put("audit.object_type", parts[5]);
                event.Put("audit.object_name", parts[6]);
                if (parts.length > 7) {
                  event.Put("audit.statement", parts.slice(7).join(",").replace(/^"|"$/g, ''));
                }
              }
            }

      - drop_event:
          when:
            not:
              has_fields: ['is_audit']

output.elasticsearch:
  hosts: ["https://localhost:9200"]
  index: "pgaudit-%{+yyyy.MM.dd}"
  ssl:
    certificate_authorities: ["/etc/pki/elasticsearch/ca.pem"]
    certificate: "/etc/pki/filebeat/cert.pem"
    key: "/etc/pki/filebeat/key.pem"

setup.template:
  name: "pgaudit"
  pattern: "pgaudit-*"
  settings:
    index.number_of_shards: 2
    index.number_of_replicas: 1
```

**Step 3: Elasticsearch index template**

```json
{
  "index_patterns": ["pgaudit-*"],
  "template": {
    "settings": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "index.lifecycle.name": "audit-retention-policy"
    },
    "mappings": {
      "properties": {
        "@timestamp": {"type": "date"},
        "pg.user_name": {"type": "keyword"},
        "pg.database_name": {"type": "keyword"},
        "pg.connection_from": {"type": "ip"},
        "pg.application_name": {"type": "keyword"},
        "audit.type": {"type": "keyword"},
        "audit.class": {"type": "keyword"},
        "audit.command": {"type": "keyword"},
        "audit.object_type": {"type": "keyword"},
        "audit.object_name": {"type": "keyword"},
        "audit.statement": {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 2048}}},
        "fields.environment": {"type": "keyword"}
      }
    }
  }
}
```

**Step 4: Kibana dashboard (saved object export)**

Key visualizations to build:
1. **Audit Event Timeline** — Line chart of events over time, split by audit.class
2. **Top Users by Activity** — Bar chart of pg.user_name with event count
3. **Command Distribution** — Pie chart of audit.command values
4. **Sensitive Table Access** — Data table filtered to known sensitive table names
5. **Failed Operations** — Count of error_severity = ERROR events
6. **Geographic Access Map** — If connection IPs are external, map them
7. **Alert Panel** — Saved search showing HIGH severity detections

---

### Lab 3: Forensic Investigation of a Simulated Data Breach

**Objective:** Using only audit logs and WAL data, investigate a simulated data breach scenario where an attacker compromised a service account and exfiltrated customer PII.

**Scenario Setup:**

```sql
-- Run this to create the breach scenario (do not look at this during investigation)
-- The "attacker" will:
-- 1. Connect using a compromised service account
-- 2. Perform reconnaissance (query information_schema)
-- 3. Escalate privileges (GRANT to self)
-- 4. Exfiltrate data (bulk SELECT)
-- 5. Cover tracks (attempt to modify audit logs)

-- Setup script (run as admin, then hand off to investigator)
CREATE DATABASE breach_lab;
\c breach_lab

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT,
    ssn TEXT,
    credit_card TEXT,
    address TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Insert 100k dummy records
INSERT INTO customers (name, email, ssn, credit_card, address)
SELECT
    'Customer_' || i,
    'customer' || i || '@example.com',
    lpad((random() * 999999999)::int::text, 9, '0'),
    lpad((random() * 9999999999999999)::bigint::text, 16, '0'),
    i || ' Main Street, City ' || (i % 50)
FROM generate_series(1, 100000) i;

-- Simulate attack (run with timestamps spread over realistic window)
-- Phase 1: Reconnaissance
SET ROLE compromised_svc;
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public';

-- Phase 2: Privilege escalation
GRANT SELECT ON ALL TABLES IN SCHEMA public TO compromised_svc;

-- Phase 3: Data exfiltration
COPY (SELECT id, name, email, ssn, credit_card FROM customers) TO '/tmp/exfil.csv';

-- Phase 4: Cover tracks (will fail due to immutability controls)
DELETE FROM audit_chain WHERE user_name = 'compromised_svc';
```

**Investigation Procedure:**

```bash
#!/bin/bash
# Forensic investigation playbook

echo "=== PHASE 1: Identify the compromise window ==="
echo "Query audit logs for the compromised service account"

psql breach_lab << 'SQL'
-- When did the account first appear doing unusual things?
SELECT
    event_time,
    command_tag,
    object_name,
    LEFT(statement, 100) as stmt_preview,
    chain_position
FROM audit_chain
WHERE user_name = 'compromised_svc'
ORDER BY event_time ASC
LIMIT 50;
SQL

echo ""
echo "=== PHASE 2: Identify reconnaissance activity ==="
psql breach_lab << 'SQL'
SELECT event_time, statement
FROM audit_chain
WHERE user_name = 'compromised_svc'
  AND (statement ILIKE '%information_schema%'
       OR statement ILIKE '%pg_catalog%'
       OR statement ILIKE '%pg_tables%');
SQL

echo ""
echo "=== PHASE 3: Identify privilege escalation ==="
psql breach_lab << 'SQL'
SELECT event_time, command_tag, statement
FROM audit_chain
WHERE command_tag IN ('GRANT', 'ALTER ROLE', 'CREATE ROLE')
  AND event_time BETWEEN '2024-07-10' AND '2024-07-15'
ORDER BY event_time;
SQL

echo ""
echo "=== PHASE 4: Quantify data exfiltration ==="
psql breach_lab << 'SQL'
SELECT
    event_time,
    command_tag,
    rows_affected,
    LEFT(statement, 200) as statement_preview
FROM audit_chain
WHERE user_name = 'compromised_svc'
  AND (command_tag IN ('COPY', 'SELECT INTO')
       OR rows_affected > 1000)
ORDER BY event_time;
SQL

echo ""
echo "=== PHASE 5: Detect cover-up attempts ==="
psql breach_lab << 'SQL'
SELECT event_time, command_tag, statement, 
       CASE WHEN statement ILIKE '%audit%' THEN 'AUDIT_TAMPERING_ATTEMPT' END as flag
FROM audit_chain
WHERE user_name = 'compromised_svc'
  AND (command_tag IN ('DELETE', 'UPDATE', 'TRUNCATE')
       OR statement ILIKE '%audit%');
SQL

echo ""
echo "=== PHASE 6: Verify chain integrity ==="
python3 verify_audit_chain.py "dbname=breach_lab"
```

**Expected Deliverable:** A forensic report containing:
- Precise timeline of the attack (UTC timestamps)
- Attack vector identification (how the service account was used)
- Scope of data accessed (tables, columns, row counts)
- Evidence of tampering attempts
- Hash chain verification results
- Recommendations for prevention

---

### Lab 4: SIEM Detection Rules for Database Exfiltration

**Objective:** Create and test a comprehensive set of SIEM detection rules that identify database exfiltration patterns with minimal false positives.

**Step 1: Define detection logic**

```yaml
# detection_rules.yml
rules:
  - id: DB-EX-001
    name: "Bulk Data Export via COPY Command"
    description: "Detects use of COPY TO for data export outside ETL windows"
    mitre_attack: T1048.003
    severity: HIGH
    logic:
      query: |
        audit.command == "COPY" AND
        audit.statement MATCHES "COPY.*TO.*" AND
        NOT user_name IN (approved_etl_accounts) AND
        NOT (hour_of_day BETWEEN 2 AND 5)
    response: alert_and_block
    
  - id: DB-EX-002
    name: "Sequential Table Enumeration"
    description: "Detects systematic reading of multiple tables in sequence"
    mitre_attack: T1530
    severity: MEDIUM
    logic:
      query: |
        audit.command == "SELECT" AND
        COUNT(DISTINCT audit.object_name) > 5
        WITHIN 10 MINUTES
        GROUP BY user_name
    response: alert
    
  - id: DB-EX-003
    name: "Information Schema Reconnaissance"
    description: "Non-admin user querying database metadata"
    mitre_attack: T1592.004
    severity: MEDIUM
    logic:
      query: |
        audit.statement MATCHES ".*(information_schema|pg_catalog|sys\.(tables|columns)).*" AND
        NOT user_name IN (admin_accounts) AND
        NOT application_name IN (approved_tools)
    response: alert
    
  - id: DB-EX-004
    name: "Privilege Escalation via GRANT"
    description: "Unexpected GRANT statement from non-DBA account"
    mitre_attack: T1078.004
    severity: CRITICAL
    logic:
      query: |
        audit.command IN ("GRANT", "ALTER ROLE") AND
        NOT user_name IN (dba_accounts)
    response: alert_and_block_immediate
    
  - id: DB-EX-005
    name: "Audit Log Tampering Attempt"
    description: "Any attempt to modify audit tables"
    mitre_attack: T1070.002
    severity: CRITICAL
    logic:
      query: |
        (audit.command IN ("DELETE", "UPDATE", "TRUNCATE", "DROP") AND
         audit.object_name MATCHES ".*audit.*") OR
        (audit.statement MATCHES ".*(DISABLE TRIGGER|ALTER TABLE.*audit).*")
    response: alert_and_isolate
```

**Step 2: Testing framework**

```python
#!/usr/bin/env python3
"""Test framework for SIEM detection rules against simulated attack patterns."""

import json
from dataclasses import dataclass
from typing import List

@dataclass
class AuditEvent:
    timestamp: str
    user_name: str
    command: str
    object_name: str
    statement: str
    rows_affected: int = 0
    application_name: str = ""

@dataclass
class DetectionResult:
    rule_id: str
    triggered: bool
    events_matched: int
    false_positive: bool
    detail: str

def test_rule_DB_EX_001(events: List[AuditEvent]) -> DetectionResult:
    """Test: Bulk Data Export via COPY Command"""
    matches = [
        e for e in events
        if e.command == "COPY"
        and "TO" in e.statement.upper()
        and e.user_name not in APPROVED_ETL_ACCOUNTS
    ]
    return DetectionResult(
        rule_id="DB-EX-001",
        triggered=len(matches) > 0,
        events_matched=len(matches),
        false_positive=False,
        detail=f"Found {len(matches)} COPY TO events from non-ETL accounts"
    )

# Simulated attack scenarios for testing
SCENARIOS = {
    "legitimate_etl": [
        AuditEvent("2024-07-15T03:00:00Z", "etl_service", "COPY",
                   "customers", "COPY customers TO '/data/export.csv'", 100000,
                   "apache-airflow"),
    ],
    "attacker_exfil": [
        AuditEvent("2024-07-15T14:30:00Z", "app_service", "SELECT",
                   "information_schema.columns",
                   "SELECT * FROM information_schema.columns WHERE table_schema='public'",
                   45),
        AuditEvent("2024-07-15T14:31:00Z", "app_service", "COPY",
                   "customers",
                   "COPY (SELECT ssn, credit_card FROM customers) TO '/tmp/out.csv'",
                   100000),
    ],
    "false_positive_analytics": [
        AuditEvent("2024-07-15T10:00:00Z", "analytics_user", "SELECT",
                   "customers", "SELECT COUNT(*) FROM customers GROUP BY region",
                   50, "metabase"),
    ],
}

# Run tests
for scenario_name, events in SCENARIOS.items():
    result = test_rule_DB_EX_001(events)
    expected_trigger = scenario_name == "attacker_exfil"
    status = "PASS" if result.triggered == expected_trigger else "FAIL"
    print(f"[{status}] Scenario '{scenario_name}': rule={result.rule_id}, "
          f"triggered={result.triggered}, expected={expected_trigger}")
```

**Step 3: Elasticsearch alert rule deployment**

```bash
# Deploy detection rules as Elasticsearch watchers
for rule_file in /etc/siem/rules/DB-EX-*.json; do
    rule_id=$(jq -r '.id' "$rule_file")
    curl -s -X PUT "https://elasticsearch:9200/_watcher/watch/${rule_id}" \
        -H "Content-Type: application/json" \
        --cert /etc/pki/siem/cert.pem \
        --key /etc/pki/siem/key.pem \
        -d @"$rule_file"
    echo "Deployed rule: ${rule_id}"
done

# Verify all rules are active
curl -s "https://elasticsearch:9200/_watcher/stats" \
    --cert /etc/pki/siem/cert.pem \
    --key /etc/pki/siem/key.pem | jq '.stats[].watcher_state'
```

---

## Attacker's Perspective: Audit Evasion Techniques

Understanding how attackers attempt to evade audit controls is essential for designing resilient systems. These techniques are documented for defensive purposes.

### Common Evasion Strategies

1. **Log Truncation/Deletion** — Direct modification of log files or audit tables. Mitigated by immutable storage and remote log forwarding.

2. **Trigger Disabling** — `ALTER TABLE audit_log DISABLE TRIGGER ALL` requires superuser access. Mitigated by monitoring DDL on audit tables and immediate alerts on trigger state changes.

3. **Session Variable Manipulation** — Setting `log_statement = 'none'` for the current session. Mitigated by not allowing users to override server-level settings (`ALTER ROLE ... SET log_statement` should be restricted).

4. **Timestamp Manipulation** — Changing system clock to confuse timeline analysis. Mitigated by NTP enforcement, multiple independent time sources, and correlation with external logs.

5. **Log Injection** — Injecting fake entries to obscure real activity. Mitigated by hash chains (injected entries break the chain) and authenticated logging.

6. **Living off the Land** — Using legitimate tools (pg_dump, psql COPY) that appear normal. Mitigated by behavioral baselines and anomaly detection.

7. **Slow Exfiltration** — Extracting data in small batches over long periods to stay below alerting thresholds. Mitigated by cumulative volume tracking per user/account and periodic access reviews.

8. **WAL Manipulation** — On compromised hosts, directly modifying WAL segments. Mitigated by streaming replication to secure standbys and WAL archiving to immutable storage.

### Defense Recommendations

- **Assume compromise** — Design audit systems assuming the attacker has superuser database access.
- **External verification** — Always forward logs to systems the database admin cannot access.
- **Separation of duties** — The DBA role should never have access to audit log storage.
- **Multiple independent channels** — Network taps, agent-based collection, AND native audit should all agree. Discrepancies indicate tampering.
- **Alert on absence** — Missing audit entries (gaps in sequence numbers or time) are as suspicious as malicious entries.
- **Canary queries** — Insert known patterns at known times; verify they appear in SIEM. Absence proves log suppression.

---

## Summary

Audit trail architecture is the backbone of both compliance and incident response. The key principles:

1. **Defense in depth** — No single audit mechanism is sufficient. Layer database-native auditing, application-level logging, WAL archiving, and external SIEM integration.

2. **Immutability is non-negotiable** — Use hash chains, cryptographic signatures, and immutable storage. Every modification must be detectable.

3. **Assume adversarial conditions** — Design audit systems to withstand an attacker with elevated privileges. External forwarding and multi-channel capture prevent total log destruction.

4. **Compliance drives retention** — Know your regulatory requirements (SOX 7yr, HIPAA 6yr, PCI-DSS 1yr) and implement automated lifecycle management.

5. **Real-time detection complements forensics** — Audit logs serve both post-incident analysis and real-time threat detection. Build for both use cases.

6. **Test your audit pipeline** — Regularly verify that events flow end-to-end, that hash chains remain intact, and that detection rules fire correctly. An untested audit system provides false assurance.

The labs in this document provide hands-on experience with production-grade audit architectures. Complete them in sequence: infrastructure (Lab 1), pipeline (Lab 2), investigation (Lab 3), detection (Lab 4). Each builds on the previous.
