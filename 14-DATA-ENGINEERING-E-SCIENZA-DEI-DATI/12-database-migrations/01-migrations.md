# Database Migrations — Fundamentals and Principles

## What Is a Database Migration

A **database migration** (or schema migration) is a controlled, versioned change to the schema
or data of a database. The term covers both structural changes (DDL — Data Definition Language)
and data transformations (DML — Data Manipulation Language).

The core problem: application source code lives in version control, but the database schema does
not — unless you impose a migration system on top of it. Without that system, the gap between
the schema the code expects and the schema that actually exists widens with every commit, every
environment, every developer.

A migration system is the disciplined answer to that gap. It turns ad-hoc DDL scripts executed
over SSH into a deterministic, auditable, repeatable pipeline.

---

## Why Migrations Matter

### The World Without Migrations

```
Developer A: "I added the email column to users last Tuesday."
Developer B: "My local dev DB does not have it. Tests pass on my machine."
QA:          "Staging has the column but no index on it."
DevOps:      "Production still runs the schema from three releases ago."
DBA:         "Someone ran an ALTER TABLE manually on prod. No record of it anywhere."
```

Every team that has operated without migrations has lived this conversation.

### The World With Migrations

```
git pull → flyway migrate → DB schema matches the code version
CI pipeline → tests run against the correct schema, every time
Deployment → migration applied automatically before the app starts
Rollback → inverse migration restores the previous schema
Audit → full history of every structural change, who authored it, when it was applied
```

Migrations are the invisible infrastructure that makes everything above possible.

### Concrete Business Value

1. **Reproducibility.** Any environment (dev, staging, QA, production) can be built from
   scratch by running the full migration chain. No tribal knowledge required.
2. **Collaboration.** Multiple developers can make schema changes on separate branches.
   The migration tool detects ordering conflicts at merge time, not at deploy time.
3. **Auditability.** Every schema change is a file in version control with an author, a
   timestamp, a review trail, and an immutable checksum.
4. **Automation.** CI/CD pipelines can validate migrations before they reach production.
   No human needs to paste SQL into a terminal.
5. **Safety.** Rollback scripts, lock timeouts, and idempotency guards turn schema changes
   from high-risk ceremonies into routine deployments.

---

## Components of a Migration System

Every migration system — regardless of tool — has three components.

### 1. Migration Scripts

Files (SQL or code) that describe the change. They are numbered sequentially or stamped
with a timestamp.

```sql
-- V1__create_users.sql
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- V2__add_user_profile.sql
ALTER TABLE users ADD COLUMN first_name VARCHAR(100);
ALTER TABLE users ADD COLUMN last_name  VARCHAR(100);
ALTER TABLE users ADD COLUMN avatar_url TEXT;

-- V3__add_users_index.sql
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_created ON users(created_at DESC);
```

### 2. Version-Tracking Table

The tool records which migrations have been applied inside the database itself.

```sql
-- Flyway uses flyway_schema_history
-- Liquibase uses databasechangelog
-- Alembic uses alembic_version
-- Django uses django_migrations

SELECT * FROM flyway_schema_history ORDER BY installed_rank;
-- installed_rank | version | description     | type | script              | checksum | success
-- 1              | 1       | create users     | SQL  | V1__create_users    | 12345678 | true
-- 2              | 2       | add user profile | SQL  | V2__add_user...     | 23456789 | true
-- 3              | 3       | add users index  | SQL  | V3__add_users_index | 34567890 | true
```

The table is the source of truth for "what has been applied." The migration tool reads it,
compares it against the files on disk, and applies anything new.

### 3. Migration Runner

The executable (CLI or library) that:

1. Connects to the database.
2. Reads the version-tracking table to determine the current state.
3. Scans the migration directory for scripts not yet applied.
4. Applies them in order, inside a transaction where the database supports it.
5. Records the result (version, checksum, success flag, execution time).
6. Aborts on failure, leaving the database in a known state.

---

## Migration vs Schema Drift

**Schema drift** is what happens when the actual database schema diverges from what the
application code or migration scripts expect. Common causes:

| Cause | Example |
|-------|---------|
| Manual DDL | DBA runs `ALTER TABLE` directly on production |
| Partial migration | MySQL migration fails mid-way, no transactional DDL |
| Skipped migration | A migration was applied in staging but never in production |
| Tool bypass | A developer creates a table via ORM without generating a migration |
| Shadow changes | A monitoring tool installs its own tables or extensions |

### Detecting Drift

```bash
# Dump the expected schema (from migrations)
flyway clean && flyway migrate  # on a disposable DB
pg_dump --schema-only ci_db > expected_schema.sql

# Dump the actual schema
pg_dump --schema-only prod_db > actual_schema.sql

# Compare
diff expected_schema.sql actual_schema.sql
```

Tools like **Atlas**, **Skeema**, and **pgModeler** can compute a semantic diff that
understands column types, indexes, and constraints — rather than doing a raw text diff.

### Preventing Drift

1. **Never run DDL manually in production.** All changes go through the migration pipeline.
2. **CI gate.** Compare the schema produced by migrations against a committed snapshot.
3. **Read-only production credentials.** Application code uses a role that cannot run DDL.
   Migrations use a separate, audited role.
4. **Drift detection cron.** Schedule a weekly or daily comparison between the expected
   schema and the actual production schema. Alert on differences.

---

## Types of Migrations

### DDL Migrations (Schema)

Structural changes to tables, columns, indexes, constraints, types.

```sql
-- Additive (safe, backward-compatible)
ALTER TABLE orders ADD COLUMN notes TEXT;
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE TABLE order_items (...);

-- Destructive (requires transition period)
ALTER TABLE orders DROP COLUMN legacy_status;
DROP TABLE old_sessions;
ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(512);

-- Reorganizational (may require locks or special strategies)
ALTER TABLE events RENAME COLUMN ts TO event_time;
ALTER TABLE users ADD CONSTRAINT fk_org
    FOREIGN KEY (org_id) REFERENCES organizations(id);
```

### DML Migrations (Data)

Transformations of existing data: backfills, normalizations, enum mapping.

```sql
-- Backfill a new column
UPDATE users
SET full_name = first_name || ' ' || last_name
WHERE full_name IS NULL;

-- Normalize: move data from denormalized to normalized structure
INSERT INTO user_emails (user_id, email, is_primary)
SELECT id, email, true FROM users WHERE email IS NOT NULL;

-- Remap enum values
UPDATE orders SET status = 'completed' WHERE status = 'done';
UPDATE orders SET status = 'cancelled' WHERE status = 'cancel';
```

### Mixed Migrations (DDL + DML)

These combine structure and data changes. They are common in the expand-and-contract
pattern (covered in `03-strategies.md`).

```sql
-- Expand phase: add new column + backfill
ALTER TABLE users ADD COLUMN email_new VARCHAR(512);
UPDATE users SET email_new = email;
ALTER TABLE users ALTER COLUMN email_new SET NOT NULL;
-- The old column will be dropped in a later migration (contract phase)
```

**Guideline**: keep DDL and DML in separate migration files whenever possible. DDL is
typically fast and transactional. DML can be slow, generates replication lag, and is
harder to reverse. Separate files allow independent timing and rollback.

---

## Migration File Anatomy

A well-structured migration file contains several elements beyond the raw SQL.

```sql
-- =============================================================================
-- Migration: V25__create_notification_preferences.sql
-- Author:    team-comms
-- Date:      2025-03-15
-- Purpose:   Per-user notification channel preferences
-- Depends:   users table (V1)
-- Rollback:  U25__create_notification_preferences.sql
-- =============================================================================

-- Safety: prevent the migration from hanging indefinitely
SET statement_timeout = '60s';
SET lock_timeout = '5s';

-- Pre-flight check: ensure the prerequisite table exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'users'
  ) THEN
    RAISE EXCEPTION 'Prerequisite table "users" does not exist.';
  END IF;
END;
$$;

-- Main migration
CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id       BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel       VARCHAR(20) NOT NULL
                  CHECK (channel IN ('email', 'sms', 'push', 'webhook')),
    enabled       BOOLEAN NOT NULL DEFAULT TRUE,
    frequency     VARCHAR(20) NOT NULL DEFAULT 'immediate'
                  CHECK (frequency IN ('immediate', 'hourly', 'daily', 'weekly')),
    quiet_start   TIME,
    quiet_end     TIME,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, channel)
);

CREATE INDEX IF NOT EXISTS idx_notif_pref_channel
    ON notification_preferences(channel)
    WHERE enabled = TRUE;

COMMENT ON TABLE notification_preferences IS
    'Per-user notification delivery preferences by channel';
```

Key elements:

1. **Header comment** with author, date, purpose, dependencies, and rollback reference.
2. **Timeouts** (`statement_timeout`, `lock_timeout`) to prevent indefinite hangs.
3. **Pre-flight checks** to fail fast if prerequisites are missing.
4. **Idempotent DDL** (`IF NOT EXISTS`, `IF EXISTS`) so reruns are safe.
5. **Comments on objects** for documentation that lives inside the database catalog.

---

## Version Tracking: The schema_migrations Table

The version-tracking table is the single source of truth for migration state. Different
tools use different table structures, but they all store the same core information.

### Flyway: `flyway_schema_history`

```sql
CREATE TABLE flyway_schema_history (
    installed_rank  INT NOT NULL,
    version         VARCHAR(50),           -- "1", "2", "20240115103000"
    description     VARCHAR(200) NOT NULL,
    type            VARCHAR(20) NOT NULL,  -- SQL, JDBC, SPRING_JDBC
    script          VARCHAR(1000) NOT NULL,
    checksum        INT,                   -- CRC32 of file content
    installed_by    VARCHAR(100) NOT NULL,
    installed_on    TIMESTAMP DEFAULT NOW(),
    execution_time  INT NOT NULL,          -- milliseconds
    success         BOOLEAN NOT NULL
);
```

### Liquibase: `databasechangelog`

```sql
CREATE TABLE databasechangelog (
    id              VARCHAR(255) NOT NULL,
    author          VARCHAR(255) NOT NULL,
    filename        VARCHAR(255) NOT NULL,
    dateexecuted    TIMESTAMP NOT NULL,
    orderexecuted   INT NOT NULL,
    exectype        VARCHAR(10) NOT NULL,  -- EXECUTED, FAILED, SKIPPED, RERAN, MARK_RAN
    md5sum          VARCHAR(35),
    description     VARCHAR(255),
    comments        VARCHAR(255),
    tag             VARCHAR(255),
    liquibase       VARCHAR(20),
    contexts        VARCHAR(255),
    labels          VARCHAR(255),
    deployment_id   VARCHAR(10)
);
```

### Alembic: `alembic_version`

```sql
-- Alembic uses a minimal table
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL
);
-- Only one row, pointing to the current head revision
-- SELECT version_num FROM alembic_version;
-- Result: 'a1b2c3d4e5f6'
```

### Django: `django_migrations`

```sql
CREATE TABLE django_migrations (
    id      SERIAL PRIMARY KEY,
    app     VARCHAR(255) NOT NULL,
    name    VARCHAR(255) NOT NULL,
    applied TIMESTAMP NOT NULL DEFAULT NOW()
);
-- One row per applied migration, scoped by app
-- SELECT * FROM django_migrations WHERE app = 'orders';
```

### Checksum Verification

Most tools compute a checksum of each migration file at the time of application and store it.
On subsequent runs, the tool recomputes the checksum of already-applied files and compares.

- **Match**: the file has not been modified since it was applied. Safe.
- **Mismatch**: someone edited an already-applied migration. The tool aborts.

This guards against a dangerous class of errors: modifying a migration that was already
applied to production, which creates silent schema drift.

---

## Version-Based vs State-Based Migration

Two fundamentally different philosophies for managing schema evolution.

### Version-Based (Imperative)

Each migration is an incremental script. The database state is the sum of all applied
migrations.

```
V1 → V2 → V3 → V4 (current state)
```

Tools: **Flyway**, **Liquibase**, **Alembic**, **Django migrations**, **golang-migrate**.

**Strengths**:
- Precise control over execution order.
- Full audit trail of every change.
- Natural fit for CI/CD pipelines.
- Explicit handling of data transformations.

**Weaknesses**:
- Cannot recreate the schema "from scratch" without running all migrations.
- Migration count grows linearly with project age.
- Merge conflicts on version numbers in multi-branch workflows.

### State-Based (Declarative)

You define the desired end state of the schema. The tool computes a diff against the
current state and generates the migration automatically.

```sql
-- Desired state file: schema.sql
CREATE TABLE users (
    id    BIGSERIAL PRIMARY KEY,
    email VARCHAR(512) UNIQUE NOT NULL  -- changed from 255 to 512
);

-- Tool auto-generates:
-- ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(512);
```

Tools: **Atlas**, **Skeema**, **Liquibase (with diffChangeLog)**, **PgSync**.

**Strengths**:
- Schema file is the source of truth — readable and diffable.
- Less boilerplate: no hand-written ALTER statements.
- Natural fit for infrastructure-as-code workflows.

**Weaknesses**:
- Auto-generated diffs can be imprecise for complex changes (column renames vs
  drop-and-recreate, partial indexes, check constraints).
- Less control over data transformations — the tool generates DDL, not DML.
- Harder to handle non-trivial refactors that require intermediate states.

### Choosing Between Them

| Factor | Version-Based | State-Based |
|--------|--------------|-------------|
| Data transformations | Native | Requires manual additions |
| Audit trail | Complete | Less granular |
| ORM integration | Strong (Alembic, Django) | Weaker |
| Learning curve | Low | Medium |
| Schema readability | Must run all migrations | Single file |
| Complex refactors | Manual but precise | Auto-diff may fail |
| Team size > 10 | Higher merge conflict risk | Lower conflict risk |

Many teams use a hybrid: state-based for schema definition, version-based for data
migrations and complex DDL that the auto-diff cannot handle.

---

## Forward-Only vs Reversible Migrations

### Forward-Only

Every migration has only an `up` direction. There is no `down` / `undo` script. If
something goes wrong, you write a new migration to fix it.

```sql
-- V10__add_column.sql (forward only)
ALTER TABLE orders ADD COLUMN notes TEXT;
-- If this was wrong, V11 fixes it:
-- V11__drop_notes.sql
-- ALTER TABLE orders DROP COLUMN notes;
```

**When to use**: simple projects, small teams, databases where rollback is rare or where
roll-forward is always preferred.

### Reversible (Bidirectional)

Every migration has both `up` and `down` directions.

```sql
-- V10__add_column.sql (up)
ALTER TABLE orders ADD COLUMN notes TEXT;

-- U10__add_column.sql (down / undo)
ALTER TABLE orders DROP COLUMN notes;
```

```python
# Alembic: both directions in one file
def upgrade():
    op.add_column('orders', sa.Column('notes', sa.Text()))

def downgrade():
    op.drop_column('orders', 'notes')
```

**When to use**: production systems with SLA requirements, teams that need fast rollback,
regulated industries where rollback is a compliance requirement.

### The Irreversibility Problem

Some operations are inherently irreversible:

| Operation | Why It Cannot Be Reversed |
|-----------|--------------------------|
| `DROP TABLE` | Data is gone |
| `DROP COLUMN` | Column data is gone |
| `UPDATE` (overwrite) | Original values are gone |
| `DELETE` | Rows are gone |
| `TRUNCATE` | All rows are gone |
| Type narrowing (`VARCHAR(255) → VARCHAR(50)`) | Truncated data is gone |

For these, the "down" migration must be designed up front — typically by backing up data
before the destructive operation. See `04-rollback.md` for patterns.

---

## Idempotent Migrations

An idempotent migration can be executed multiple times without side effects. This is
critical for recovery from partial failures, especially on databases without transactional
DDL (MySQL, Oracle).

```sql
-- NOT idempotent: fails if the table already exists
CREATE TABLE users (...);

-- Idempotent
CREATE TABLE IF NOT EXISTS users (...);

-- NOT idempotent: fails if the column already exists
ALTER TABLE users ADD COLUMN url TEXT;

-- Idempotent (PostgreSQL)
ALTER TABLE users ADD COLUMN IF NOT EXISTS url TEXT;

-- NOT idempotent: fails if the index already exists
CREATE INDEX idx_users_email ON users(email);

-- Idempotent
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- Or for CONCURRENTLY:
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
```

### MySQL Idempotency (No IF NOT EXISTS for ALTER TABLE)

MySQL does not support `ADD COLUMN IF NOT EXISTS` in standard syntax. Workaround:

```sql
-- MySQL: check information_schema before ALTER
SET @col_exists = (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'users'
      AND column_name = 'url'
);
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE users ADD COLUMN url TEXT',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
```

MariaDB does support `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

---

## Transactional DDL

Whether DDL statements run inside a transaction varies by database engine.

| Database | Transactional DDL | Behavior on Failure |
|----------|------------------|---------------------|
| **PostgreSQL** | Yes | All DDL in the transaction is rolled back |
| **SQL Server** | Yes (in explicit transactions) | Rolled back within the transaction |
| **SQLite** | Yes | Rolled back |
| **MySQL / MariaDB (InnoDB)** | No | Each DDL auto-commits; partial state on failure |
| **Oracle** | No | Implicit COMMIT before and after each DDL |
| **CockroachDB** | Yes | Rolled back |
| **YugabyteDB** | Depends on operation | Some DDL is transactional |

### PostgreSQL: Transactional DDL in Practice

```sql
BEGIN;
  CREATE TABLE foo (id INT);
  ALTER TABLE foo ADD COLUMN name TEXT;
  -- If this fails, both CREATE and ALTER are rolled back:
  CREATE INDEX idx_foo_name ON foo(name);
COMMIT;
```

**Exception**: `CREATE INDEX CONCURRENTLY` cannot run inside a transaction. It must be
the only statement in its migration file.

```sql
-- Must be outside a transaction block
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_foo_name ON foo(name);
```

### MySQL: No Transactional DDL

```sql
-- Every DDL statement implicitly commits any active transaction.
-- This means partial failures leave the database in an intermediate state.

-- Example: migration with two ALTERs
ALTER TABLE users ADD COLUMN bio TEXT;        -- succeeds, auto-committed
ALTER TABLE users ADD COLUMN avatar_url TEXT;  -- fails (e.g., duplicate column)
-- Result: bio column exists, avatar_url does not. Partial state.
```

This is why idempotency is even more important on MySQL. If a migration fails halfway,
you need to be able to re-run it safely after fixing the issue.

### SQL Server: Explicit Transactions

```sql
BEGIN TRANSACTION;
  ALTER TABLE dbo.Users ADD PhoneNumber NVARCHAR(20);
  CREATE INDEX idx_users_phone ON dbo.Users(PhoneNumber);
COMMIT;
-- If either fails, both are rolled back.
```

### Oracle: Implicit COMMIT

```sql
-- Every DDL statement issues an implicit COMMIT before and after execution.
-- Cannot roll back DDL operations.

-- Edition-Based Redefinition (EBR) for safe schema evolution:
CREATE EDITION v2;
ALTER SESSION SET EDITION = v2;
ALTER TABLE users ADD (display_name VARCHAR2(255));
-- Old sessions continue using the previous edition.
```

---

## Migration Testing

Migrations must be tested before they reach production. The testing strategy mirrors the
application testing pyramid: unit → integration → staging → production.

### Level 1: Local Validation

```bash
# Reset local DB and apply all migrations from scratch
flyway clean && flyway migrate

# Or with Alembic
alembic downgrade base && alembic upgrade head

# Verify schema matches expectations
pg_dump --schema-only mydb_dev > /tmp/schema_after.sql
diff /tmp/schema_before.sql /tmp/schema_after.sql
```

### Level 2: CI Pipeline

```yaml
# .github/workflows/migration-ci.yml
name: Migration CI

on:
  pull_request:
    paths:
      - 'db/migrations/**'

jobs:
  validate-migration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: ci_db
          POSTGRES_PASSWORD: ci_pass
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - name: Apply all migrations
        run: flyway -url=jdbc:postgresql://localhost/ci_db migrate

      - name: Validate schema snapshot
        run: |
          pg_dump --schema-only -h localhost -U postgres ci_db \
            | sed '/^--/d' | sed '/^$/d' > actual_schema.sql
          diff expected_schema.sql actual_schema.sql

      - name: Test rollback
        run: |
          flyway -url=jdbc:postgresql://localhost/ci_db undo || true
          flyway -url=jdbc:postgresql://localhost/ci_db migrate

      - name: Check migration naming convention
        run: |
          for f in db/migrations/V*.sql; do
            if ! echo "$f" | grep -qE 'V[0-9]+__[a-z_]+\.sql'; then
              echo "ERROR: $f does not follow naming convention"
              exit 1
            fi
          done

      - name: Lint SQL
        run: |
          pip install sqlfluff
          sqlfluff lint db/migrations/ --dialect postgres
```

### Level 3: Staging with Production-Scale Data

Run the migration against a staging database that mirrors production data volume and shape.
This catches:

- Performance issues (long-running ALTERs on large tables).
- Lock contention.
- Constraint violations from data that exists in production but not in dev.
- Replication lag spikes.

### Level 4: Production Dry Run

Some tools support a dry-run or preview mode:

```bash
# Flyway: info shows pending migrations without applying
flyway info -url="$PROD_DB_URL"

# Atlas: plan shows the computed diff
atlas schema apply --url "$PROD_DB_URL" --dry-run

# Alembic: SQL mode outputs the SQL without executing
alembic upgrade head --sql > migration_preview.sql
```

---

## Migration Lifecycle in Detail

### Phase 1: Development

The developer creates a migration script locally, triggered by a model change or feature
requirement.

### Phase 2: Local Validation

Run migrations from scratch, verify schema, test rollback.

### Phase 3: Code Review

The migration script is included in the same PR as the code that uses the new schema.
Reviewers check:

- Is the migration backward-compatible with the currently deployed code?
- Does it have an undo script?
- Are lock timeouts set?
- Are large tables handled with batching or CONCURRENTLY?
- Is the migration idempotent where possible?

### Phase 4: CI Pipeline

Automated: apply all migrations on a fresh database, validate schema, test rollback,
lint SQL syntax.

### Phase 5: Staging Deployment

Against production-scale data. Measure execution time, lock duration, replication lag.

### Phase 6: Production Deployment

```bash
#!/bin/bash
# deploy-production.sh
set -euo pipefail

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$TIMESTAMP] Starting production migration"

# 1. Pre-flight checks
PENDING=$(flyway info -url="$PROD_DB_URL" | grep -c "Pending" || true)
echo "Pending migrations: $PENDING"
if [ "$PENDING" -eq 0 ]; then
  echo "No pending migrations. Skipping."
  exit 0
fi

# 2. Schema backup
pg_dump "$PROD_DB_URL" --schema-only \
  -f "/backup/pre_deploy_schema_${TIMESTAMP}.sql"

# 3. Apply with timeout
timeout 600 flyway migrate -url="$PROD_DB_URL" \
  2>&1 | tee "/var/log/migrations/${TIMESTAMP}.log"

# 4. Post-migration verification
flyway info -url="$PROD_DB_URL" | tail -5
echo "[$TIMESTAMP] Migration complete"
```

---

## Migration Numbering Strategies

### Sequential Integer Versioning

```
V1__initial_schema.sql
V2__add_users.sql
V3__add_orders.sql
```

**Pros**: Simple, easy to read, clear ordering.
**Cons**: Merge conflicts when two developers create the same version on different branches.

### Timestamp-Based Versioning

```
V20240115103000__add_users.sql
V20240116140530__add_orders.sql
```

**Pros**: No merge conflicts (timestamps are unique), natural chronological ordering.
**Cons**: Harder to read, long filenames.

### Hybrid: Branch-Aware Versioning

```
V100__feature_auth_create_sessions.sql
V101__feature_auth_add_session_tokens.sql
V200__feature_billing_create_invoices.sql
V201__feature_billing_add_line_items.sql
```

**Pros**: Grouped by feature, reduces conflicts.
**Cons**: Requires team coordination on version ranges.

### Tool-Specific Approaches

```python
# Alembic uses random hex revision IDs with parent pointers
# revision = 'a1b2c3d4e5f6'
# down_revision = '9f8e7d6c5b4a'
# This creates a DAG (directed acyclic graph) of migrations
# Supports branching and merging natively

# Django migrations also use a DAG with dependencies
# class Migration(migrations.Migration):
#     dependencies = [
#         ('auth', '0012_alter_user_first_name_max_length'),
#         ('orders', '0003_add_notes'),
#     ]
```

---

## Migration Dependency Management

When multiple teams work on the same database, migration ordering becomes a dependency
management problem.

### Alembic: DAG-Based Dependencies

```python
# migrations/versions/001_base.py
revision = '001'
down_revision = None

# migrations/versions/002_auth.py
revision = '002'
down_revision = '001'

# migrations/versions/003_billing.py
revision = '003'
down_revision = '001'  # branches from 001, parallel to 002

# migrations/versions/004_merge.py (merge point)
revision = '004'
down_revision = ('002', '003')  # merge two branches
```

### Liquibase: Preconditions and Include Ordering

```yaml
databaseChangeLog:
  - includeAll:
      path: db/changelog/
      relativeToChangelogFile: true
      # Files sorted alphabetically: naming matters

  - changeSet:
      id: add-payments-table
      author: team-billing
      preConditions:
        - onFail: MARK_RAN
        - tableExists:
            tableName: orders
      changes:
        - createTable:
            tableName: payments
            columns:
              - column:
                  name: id
                  type: BIGSERIAL
                  constraints:
                    primaryKey: true
              - column:
                  name: order_id
                  type: BIGINT
                  constraints:
                    foreignKeyName: fk_payments_orders
                    references: orders(id)
```

### Django: Multi-App Dependencies

```python
class Migration(migrations.Migration):
    dependencies = [
        ('users', '0005_add_profile'),
        ('orders', '0003_add_line_items'),
    ]
    operations = [
        migrations.AddField(
            model_name='order',
            name='owner',
            field=models.ForeignKey(
                to='users.Profile',
                on_delete=models.CASCADE,
            ),
        ),
    ]
```

---

## Squashing Migrations

Over time, a project accumulates hundreds of migration scripts. Squashing combines them
into a single baseline migration.

```bash
# Step 1: Dump the current schema as the new baseline
pg_dump --schema-only mydb > V1__baseline.sql

# Step 2: Archive old migrations
mkdir -p migrations/archive/
mv migrations/V*.sql migrations/archive/

# Step 3: Place the baseline
mv V1__baseline.sql migrations/

# Step 4: Set Flyway baseline to skip V1 on existing databases
flyway baseline -baselineVersion=1 \
  -baselineDescription="Squashed baseline"

# Step 5: New migrations continue from V2
```

```python
# Alembic: squash with a new baseline revision
# 1. Create a new migration representing the full schema
alembic revision --autogenerate -m "squashed baseline"

# 2. Replace upgrade() with the full schema creation
def upgrade():
    op.create_table('users', ...)
    op.create_table('orders', ...)
    # ...

def downgrade():
    op.drop_table('orders')
    op.drop_table('users')

# 3. Update alembic_version to point to the new revision
# 4. Archive old revision files
```

**When to squash**:
- More than 200 migration files.
- Fresh environment setup takes longer than 5 minutes.
- Migration history is no longer relevant (all environments past a certain version).

**When NOT to squash**:
- Multiple environments are at different migration versions.
- Audit requirements mandate full history retention.
- Active rollback references exist to old migrations.

---

## Database-Specific DDL Behavior

### PostgreSQL

```sql
-- Transactional DDL: YES
BEGIN;
  CREATE TABLE foo (id INT);
  ALTER TABLE foo ADD COLUMN name TEXT;
COMMIT;

-- CREATE INDEX CONCURRENTLY: cannot run inside a transaction
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_foo_name ON foo(name);

-- ADD COLUMN with DEFAULT on PG 11+: O(1), no table rewrite
ALTER TABLE large_table ADD COLUMN status TEXT DEFAULT 'active';
-- On PG < 11: full table rewrite with ACCESS EXCLUSIVE lock
```

### MySQL / MariaDB

```sql
-- Transactional DDL: NO
-- Every DDL auto-commits. Partial failures leave intermediate state.

-- Online DDL (MySQL 8.0+): some operations support ALGORITHM=INPLACE
ALTER TABLE users ADD COLUMN bio TEXT, ALGORITHM=INPLACE, LOCK=NONE;
-- Not all operations support INPLACE — check the MySQL docs per operation.

-- For unsupported operations: use gh-ost or pt-online-schema-change
```

### SQL Server

```sql
-- Transactional DDL: YES (within explicit transactions)
BEGIN TRANSACTION;
  ALTER TABLE dbo.Users ADD PhoneNumber NVARCHAR(20);
  CREATE INDEX idx_users_phone ON dbo.Users(PhoneNumber);
COMMIT;

-- Online index operations
CREATE INDEX idx_users_email ON dbo.Users(Email) WITH (ONLINE = ON);
```

### Oracle

```sql
-- Transactional DDL: NO
-- Every DDL issues implicit COMMIT before and after.

-- Edition-Based Redefinition (EBR)
CREATE EDITION v2;
ALTER SESSION SET EDITION = v2;
ALTER TABLE users ADD (display_name VARCHAR2(255));
```

---

## Compatibility with Application Code Versions

In continuous deployment systems, the code and the database are deployed at different
times. The migration must be compatible with **both the old and the new** code version
during the transition.

```
T1: DB v1, App v1  (everything in sync)
T2: DB v2, App v1  (migration applied, old app still running)
T3: DB v2, App v2  (deployment complete)
```

The database at v2 must continue to work with App v1 during phase T2.

**Rule**: never drop columns or tables until all application instances have been updated
to the version that no longer uses them.

This principle is the foundation of zero-downtime migrations (covered in `05-zero-downtime.md`)
and the expand-and-contract pattern (covered in `03-strategies.md`).

---

## Repeatable vs Versioned Migrations

### Versioned Migrations (V prefix in Flyway)

Applied once, tracked by version number, ordered.

```sql
-- V5__add_orders_table.sql
-- Applied once and never again.
CREATE TABLE orders (...);
```

### Repeatable Migrations (R prefix in Flyway)

Re-applied whenever their checksum changes. Used for database objects that are
redefined in place: views, functions, stored procedures, triggers.

```sql
-- R__create_user_stats_view.sql
-- Re-applied every time the file content changes.
CREATE OR REPLACE VIEW user_stats AS
SELECT
    user_id,
    COUNT(*) AS order_count,
    SUM(amount) AS total_spent
FROM orders
GROUP BY user_id;
```

**Execution order**: Flyway runs all pending versioned migrations first, then all
repeatable migrations whose checksum has changed.

### Liquibase Equivalent

```yaml
- changeSet:
    id: create-user-stats-view
    author: analytics
    runOnChange: true   # re-run when the changeset content changes
    changes:
      - createView:
          viewName: user_stats
          replaceIfExists: true
          selectBody: |
            SELECT user_id, COUNT(*) AS order_count, SUM(amount) AS total_spent
            FROM orders GROUP BY user_id
```

---

## Troubleshooting

### 1. "Relation already exists"

**Cause**: Partial application (crash mid-execution on MySQL), or manual DDL outside the
migration system.

**Fix**: Use `IF NOT EXISTS`. If already applied, repair the history table.

```bash
flyway repair && flyway migrate
# or
liquibase markNextChangeSetRan
```

### 2. Checksum Mismatch

**Cause**: Someone edited an already-applied migration file.

**Fix**: Never edit applied migrations. If already done:

```bash
flyway repair        # recalculates checksums
liquibase clearCheckSums
```

### 3. Migration Hangs Waiting for Lock

**Cause**: Another session holds an ACCESS EXCLUSIVE lock or a long-running transaction.

**Fix**:

```sql
-- Find the blocker
SELECT pid, state, query, now() - query_start AS duration
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- Terminate the blocker (with care)
SELECT pg_terminate_backend(<blocking_pid>);

-- Always set lock_timeout in migrations
SET lock_timeout = '5s';
```

### 4. Out-of-Order Migration Detected

**Cause**: A lower-version migration was committed after a higher version was applied
(common in branching workflows).

**Fix**:

```properties
# Flyway: allow out-of-order execution
flyway.outOfOrder=true
# Use with caution: only when migrations are truly independent

# Alembic: create a merge revision
alembic merge heads -m "merge branches"
```

### 5. Migration Timeout on Large Table ALTER

**Cause**: ALTER TABLE on a multi-million row table exceeds statement_timeout.

**Fix**: Use online DDL tools for MySQL (gh-ost, pt-online-schema-change) or
CONCURRENTLY for PostgreSQL indexes. Split into schema change + batched backfill.

### 6. Flyway Baseline Conflict

**Cause**: Running Flyway on a database with existing tables but no flyway_schema_history.

**Fix**:

```bash
flyway baseline -baselineVersion=10 \
  -baselineDescription="Existing production schema"
# Subsequent flyway migrate will only apply V11+
```

### 7. Alembic Autogenerate Misses Changes

**Cause**: Autogenerate only detects changes that SQLAlchemy models can express. It misses
CHECK constraints, partial indexes, triggers, functions.

**Fix**: Always review autogenerated migrations. Add missed changes manually:

```python
def upgrade():
    # Autogenerated
    op.add_column('users', sa.Column('status', sa.String(20)))
    # Manually added
    op.create_check_constraint(
        'ck_users_status', 'users',
        "status IN ('active', 'suspended', 'deleted')"
    )
```

### 8. Django Circular Dependency

**Cause**: Two apps reference each other's models in migrations.

**Fix**: Use `RunSQL` to break the cycle:

```python
class Migration(migrations.Migration):
    dependencies = [('app_a', '0005_add_table')]
    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE app_b_model ADD CONSTRAINT fk "
                "FOREIGN KEY (ref_id) REFERENCES app_a_model(id);",
            reverse_sql="ALTER TABLE app_b_model DROP CONSTRAINT fk;"
        ),
    ]
```

### 9. Replication Lag Spikes During Migration

**Cause**: Large UPDATE/INSERT generates massive WAL, causing replicas to fall behind.

**Fix**: Batch large DML with pauses:

```sql
DO $$
DECLARE
  batch INT := 5000;
  affected INT;
BEGIN
  LOOP
    UPDATE users SET migrated = TRUE
    WHERE id IN (
      SELECT id FROM users WHERE migrated IS NULL LIMIT batch
    );
    GET DIAGNOSTICS affected = ROW_COUNT;
    EXIT WHEN affected = 0;
    PERFORM pg_sleep(0.1);  -- let replicas catch up
  END LOOP;
END;
$$;
```

### 10. Migration Passes in CI but Fails in Production

**Cause**: Production data triggers constraint violations or type mismatches not present
in the test dataset.

**Fix**: Test against anonymized production dumps. Add pre-migration validation:

```sql
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM orders WHERE email IS NULL LIMIT 1) THEN
    RAISE EXCEPTION
      'Cannot apply: orders.email has NULL values. Run backfill first.';
  END IF;
END;
$$;
```

### 11. Multiple Flyway Instances Conflict

**Cause**: Multiple application instances run migrations simultaneously at startup.

**Fix**: Only one instance should run migrations. Use a deployment hook or init container:

```yaml
# Kubernetes: init container for migrations
initContainers:
  - name: db-migrate
    image: flyway/flyway:10
    command: ["flyway", "migrate"]
    env:
      - name: FLYWAY_URL
        valueFrom:
          secretKeyRef:
            name: db-credentials
            key: url
```

### 12. Liquibase Rollback Misunderstanding

**Cause**: Confusion about how `rollback --tag` works.

**Fix**: Liquibase `rollback --tag` executes the rollback section of each changeset
applied after the tag. It does not re-apply changesets. Ensure every changeset has a
proper rollback block.

### 13. PostgreSQL Enum Changes

Adding a value to an enum type cannot be done inside a transaction:

```sql
-- Must be outside a transaction
ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'refunded';
```

Removing or renaming enum values requires creating a new type:

```sql
ALTER TYPE order_status RENAME TO order_status_old;
CREATE TYPE order_status AS ENUM ('pending', 'completed', 'refunded');
ALTER TABLE orders ALTER COLUMN status
    TYPE order_status USING status::text::order_status;
DROP TYPE order_status_old;
```

---

## Frequently Asked Questions (FAQ)

### 1. Which migration tool should I use?

- **Flyway**: simplicity, JVM-based stack, plain SQL migrations.
- **Liquibase**: cross-database portability (XML/YAML), conditional execution, enterprise.
- **Alembic**: Python/SQLAlchemy ecosystem, autogenerate from models.
- **Django migrations**: Django projects (use built-in, not Alembic).
- **golang-migrate**: Go projects, lightweight, SQL files.
- **Atlas**: declarative/state-based, modern, good for infrastructure-as-code workflows.
- **Prisma Migrate**: Node.js/TypeScript with Prisma ORM.

### 2. Can I modify a migration that has already been applied?

No. Once applied to any environment, treat it as immutable. Create a new corrective
migration. Use `flyway repair` or `liquibase clearCheckSums` only as a last resort —
it breaks the audit trail.

### 3. How do I handle migrations in a microservices architecture?

Each service owns its own database and migration history. Never share a migration tool
across service boundaries. Cross-service schema coordination happens at the API contract
level, not the database level.

### 4. Should migrations run at application startup?

Separate step (CI/CD pipeline or init container). Startup migration causes race
conditions with multiple instances. The exception: small single-instance applications.

### 5. How do I migrate a database that was never under migration control?

Baseline it: dump the current schema as V1, set the tool's baseline to V1, write
future changes as V2+.

```bash
flyway baseline -baselineVersion=1
# or
alembic stamp head
```

### 6. What about branch-based development?

Use timestamp-based versioning to avoid collisions. Alembic's DAG handles branches
natively with `alembic merge heads`. For Flyway, enable `outOfOrder=true` in dev.

### 7. What is expand-and-contract?

A three-phase approach for backward-compatible changes: expand (add new structure),
migrate (backfill data, update code), contract (remove old structure). See
`03-strategies.md` for full coverage.

### 8. How do I estimate migration duration for production?

Run against staging with production-scale data:

```sql
-- Check table size before migration
SELECT pg_size_pretty(pg_total_relation_size('orders'));

-- Monitor during migration
SELECT pid, wait_event_type, state, query
FROM pg_stat_activity
WHERE query LIKE '%ALTER TABLE orders%';
```

Rules of thumb:
- Schema-only changes on PG 11+ (`ADD COLUMN DEFAULT`): O(1).
- Data migrations: linear with row count.
- `CREATE INDEX CONCURRENTLY`: ~2x sequential scan time.

### 9. Should I separate schema and data migrations?

Yes. Schema (DDL) is fast and transactional. Data (DML) can be slow and generates
replication lag. Separate files allow independent timing and rollback.

### 10. How do I handle migration failures in production?

1. Check the history table for FAILED entries.
2. Examine database logs for the exact error.
3. If transactional DDL (PostgreSQL): fully rolled back. Fix and re-apply.
4. If no transactional DDL (MySQL): manually assess partial state, fix, then repair.
5. Always have a pre-migration schema backup.

---

## Real-World Scenarios

### Scenario 1: The 500-Million-Row Backfill

A SaaS platform needs to add a `tenant_id` column to a 500M-row `events` table and
backfill it from a join with the `projects` table.

```sql
-- Phase 1: Add nullable column (instant on PG 11+)
ALTER TABLE events ADD COLUMN tenant_id BIGINT;

-- Phase 2: Batched backfill (separate migration, takes hours)
DO $$
DECLARE
  batch_size INT := 10000;
  last_id BIGINT := 0;
  max_id BIGINT;
  rows_updated BIGINT := 0;
BEGIN
  SELECT MAX(id) INTO max_id FROM events;
  RAISE NOTICE 'Backfilling % rows', max_id;

  WHILE last_id < max_id LOOP
    UPDATE events e
    SET tenant_id = p.tenant_id
    FROM projects p
    WHERE e.project_id = p.id
      AND e.id > last_id
      AND e.id <= last_id + batch_size
      AND e.tenant_id IS NULL;

    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    last_id := last_id + batch_size;

    IF last_id % 1000000 = 0 THEN
      RAISE NOTICE 'Progress: %/% (%.1f%%)',
        last_id, max_id, (last_id::float / max_id * 100);
    END IF;

    PERFORM pg_sleep(0.05);  -- yield to other queries
  END LOOP;
END;
$$;

-- Phase 3: Add NOT NULL (after backfill is verified complete)
ALTER TABLE events ALTER COLUMN tenant_id SET NOT NULL;

-- Phase 4: Add index (separate migration)
CREATE INDEX CONCURRENTLY idx_events_tenant ON events(tenant_id);

-- Phase 5: Add FK (separate migration)
ALTER TABLE events ADD CONSTRAINT fk_events_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants(id);
```

### Scenario 2: The Accidental Production ALTER

A developer runs `ALTER TABLE orders DROP COLUMN legacy_field` directly on production
without going through the migration pipeline.

**Consequence**: the migration tool thinks the column still exists. The next migration
that references `legacy_field` will fail. Schema drift is now real.

**Recovery**:

```bash
# 1. Detect the drift
pg_dump --schema-only prod_db > actual.sql
flyway clean && flyway migrate  # on a throwaway DB
pg_dump --schema-only throwaway_db > expected.sql
diff actual.sql expected.sql

# 2. Create a migration that matches the current state
# V99__align_with_manual_change.sql
# ALTER TABLE orders DROP COLUMN IF EXISTS legacy_field;

# 3. Apply and repair
flyway repair
flyway migrate
```

### Scenario 3: Multi-Timezone Team Migration Conflict

Teams in UTC+1 and UTC-8 both create migration V42 on separate branches. Both merge
to main within minutes of each other.

**Prevention**: use timestamp-based versioning.
**Recovery**: CI catches the duplicate version. One team renames their migration.

---

## Exercises

### Exercise 1 (Beginner): Write Your First Migration

Write a Flyway migration that:
1. Creates a `products` table with `id`, `name`, `price`, `category`, `created_at`.
2. Creates an index on `category`.
3. Is idempotent.

**Expected output**: A single SQL file following the naming convention.

### Exercise 2 (Beginner): Identify the Problems

This migration has three problems. Find them:

```sql
-- V5__update_users.sql
ALTER TABLE users ADD COLUMN role VARCHAR(20);
UPDATE users SET role = 'admin' WHERE is_admin = true;
UPDATE users SET role = 'user' WHERE is_admin = false;
ALTER TABLE users DROP COLUMN is_admin;
ALTER TABLE users ALTER COLUMN role SET NOT NULL;
```

**Hints**: backward compatibility, atomicity, single responsibility.

### Exercise 3 (Intermediate): Design a Reversible Migration

You need to rename the `email_address` column to `email` on the `customers` table
(10M rows). Write:
1. The forward migration(s).
2. The undo migration(s).
3. The application code changes needed at each phase.

Consider zero-downtime and backward compatibility.

### Exercise 4 (Intermediate): CI Pipeline Design

Design a CI workflow (GitHub Actions YAML) that:
1. Spins up a PostgreSQL 16 container.
2. Applies all migrations.
3. Validates the resulting schema against a committed snapshot.
4. Tests the rollback of the last migration.
5. Lints the SQL with sqlfluff.
6. Checks naming conventions.

### Exercise 5 (Advanced): Cross-Database Migration Strategy

Your company is migrating from MySQL 5.7 to PostgreSQL 16. The application uses
100+ tables and serves 10K requests/second. Design:
1. The data migration strategy.
2. How to handle type differences (TINYINT(1), ENUM, AUTO_INCREMENT).
3. The cutover plan.
4. The rollback plan.

### Exercise 6 (Advanced): Migration Dependency Graph

Given 4 teams (auth, billing, notifications, analytics) working on the same database:
1. Design a migration dependency management strategy.
2. Handle the case where analytics needs a table from billing that billing has not
   yet created.
3. Prevent circular dependencies.
4. Design the CI gate that validates dependency correctness.

### Exercise 7 (Advanced): Production Migration Runbook

Write a production migration runbook for a PostgreSQL database with:
- 500M rows in the largest table
- 3 read replicas
- 99.99% uptime SLA
- Multi-region deployment

Cover: pre-migration checks, execution steps, monitoring during migration,
rollback triggers, post-migration validation.

---

## Key Takeaways

1. **Migrations are code.** Version them, review them, test them, lint them.
2. **Immutability.** Never edit an applied migration. Create a new one.
3. **Backward compatibility.** Every migration must work with both the old and new code.
4. **Idempotency.** Use `IF NOT EXISTS` / `IF EXISTS` everywhere possible.
5. **Separation.** Keep DDL and DML in separate migration files.
6. **Timeouts.** Always set `lock_timeout` and `statement_timeout`.
7. **Testing.** Validate against production-scale data, not just empty databases.
8. **Reversibility.** Write undo scripts up front, not when you need them.
9. **Automation.** Migrations run in CI/CD, not via manual SSH.
10. **One responsibility.** Each migration does one thing.

The migration system is the contract between your code and your database. Treat it with
the same rigor as production code — review, test, version, document — and your schema
will evolve with confidence instead of fear.
