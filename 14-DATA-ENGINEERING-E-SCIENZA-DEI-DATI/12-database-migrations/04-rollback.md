# Database Migrations — Rollback and Error Handling

## Rollback Philosophy

A rollback is conceptually simple — apply the inverse set of operations — but practically
complex for several reasons:

1. **Data loss**: a migration that inserted or updated data may not be reversible without
   losing information.
2. **Lock duration**: the rollback must be fast enough not to extend the outage window.
3. **Application dependencies**: production code may already depend on the new schema.
4. **Partial state**: if the migration failed mid-way, the database may be in an
   inconsistent state.
5. **Replication**: the rollback must propagate cleanly to all replicas.

**Fundamental principle**: design migrations for rollback from the start. Rollback is not
an afterthought — it is a first-class design requirement, equal in importance to the
forward migration.

---

## Rollback vs Roll-Forward: Decision Framework

When a migration causes problems in production, the first decision is: do you roll back
(undo the change) or roll forward (fix the problem with a new migration)?

### When to Roll Back

- The migration itself is the root cause of the problem.
- The undo script is tested and ready.
- The rollback can be completed within the incident SLA.
- No data has been written to the new schema by the application yet.
- The old application version is still deployable.

### When to Roll Forward

- The migration is correct, but the application code has a bug.
- Rolling back would lose data that users have already created.
- The rollback would take longer than fixing the issue.
- The new schema is already in use by multiple services.
- The rollback script does not exist or is untested.

### Decision Matrix

```
                        Data written to    No data written
                        new schema?        to new schema?

Undo script exists      Roll forward       Roll back
and is tested           (usually safer)    (fast, clean)

Undo script does        Roll forward       Roll forward
not exist               (fix and deploy)   (write undo first)
```

### Time Pressure

In an incident, the first 15 minutes are critical. If the rollback is ready and tested,
execute it immediately. If it is not, spend those 15 minutes on triage, not on writing
an untested rollback script under pressure.

---

## Automatic Rollback: Transactional DDL

On databases with transactional DDL (PostgreSQL, SQL Server), a failed migration is
automatically rolled back by the transaction mechanism.

```sql
-- PostgreSQL: everything in one transaction
BEGIN;

CREATE TABLE order_metadata (
    order_id    BIGINT REFERENCES orders(id),
    key         VARCHAR(100) NOT NULL,
    value       TEXT,
    PRIMARY KEY (order_id, key)
);

CREATE INDEX idx_order_metadata_key ON order_metadata(key);

ALTER TABLE orders ADD COLUMN metadata_migrated BOOLEAN DEFAULT FALSE;

-- If any statement fails, ALL previous statements in this
-- transaction are automatically rolled back.
COMMIT;
```

### PostgreSQL: What Gets Rolled Back

| Operation | Rolled back on failure? |
|-----------|------------------------|
| `CREATE TABLE` | Yes |
| `ALTER TABLE` | Yes |
| `CREATE INDEX` | Yes |
| `DROP TABLE` | Yes |
| `INSERT/UPDATE/DELETE` | Yes |
| `CREATE INDEX CONCURRENTLY` | No (cannot run in transaction) |
| `ALTER TYPE ... ADD VALUE` | No (enum value addition) |

### MySQL: No Automatic Rollback for DDL

Every DDL statement in MySQL implicitly commits any active transaction. This means:

```sql
-- MySQL: NO transactional DDL
ALTER TABLE users ADD COLUMN bio TEXT;         -- auto-committed
ALTER TABLE users ADD COLUMN avatar_url TEXT;  -- fails (e.g., syntax error)
-- Result: bio exists, avatar_url does not. Partial state.
-- There is no automatic rollback.
```

**Consequence**: MySQL migrations must be designed for manual rollback. Each DDL statement
needs its own undo counterpart.

---

## Manual Rollback: Undo Scripts

The most reliable rollback method is writing an explicit undo script for every migration.

### Example: Forward and Undo Pair

```sql
-- V7__add_premium_features.sql (forward)
ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN premium_since TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN premium_expires TIMESTAMPTZ;

CREATE TABLE premium_benefits (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_benefits (
    user_id    BIGINT REFERENCES users(id),
    benefit_id INT REFERENCES premium_benefits(id),
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, benefit_id)
);
```

```sql
-- U7__add_premium_features.sql (undo)
DROP TABLE IF EXISTS user_benefits;
DROP TABLE IF EXISTS premium_benefits;
ALTER TABLE users DROP COLUMN IF EXISTS premium_expires;
ALTER TABLE users DROP COLUMN IF EXISTS premium_since;
ALTER TABLE users DROP COLUMN IF EXISTS is_premium;
```

### Undo Script Design Rules

1. **Reverse order**: undo operations should be in the reverse order of the forward
   migration. Drop child tables before parent tables. Drop columns in reverse order.

2. **Idempotent**: use `IF EXISTS` / `IF NOT EXISTS` so the undo can be safely re-run.

3. **Tested**: the undo script must be tested in CI. Apply forward, apply undo, verify
   the schema matches the pre-migration state.

4. **Complete**: if the forward migration creates a table, adds columns, creates indexes,
   and inserts seed data, the undo must reverse all of those.

### Tool-Specific Undo Mechanisms

**Flyway (Teams/Enterprise)**:
```sql
-- U7__add_premium_features.sql
-- Flyway Teams supports undo migrations with U prefix
-- flyway undo  ->  applies the latest undo migration
```

**Alembic**:
```python
def upgrade():
    op.add_column('users', sa.Column('is_premium', sa.Boolean()))
    op.create_table('premium_benefits', ...)
    op.create_table('user_benefits', ...)

def downgrade():
    op.drop_table('user_benefits')
    op.drop_table('premium_benefits')
    op.drop_column('users', 'is_premium')
```

**Liquibase**:
```yaml
changeSet:
  id: add-premium-features
  author: team-billing
  changes:
    - addColumn:
        tableName: users
        columns:
          - column:
              name: is_premium
              type: BOOLEAN
              defaultValueBoolean: false
  rollback:
    - dropColumn:
        tableName: users
        columnName: is_premium
```

**Django**:
```python
# Django auto-generates reversible operations for most changes.
# RunSQL requires explicit reverse_sql:
class Migration(migrations.Migration):
    operations = [
        migrations.RunSQL(
            sql="CREATE TABLE premium_benefits (...);",
            reverse_sql="DROP TABLE IF EXISTS premium_benefits;"
        ),
    ]
```

---

## Data-Preserving Rollbacks

The hardest rollback problem: what happens to data written to the new schema after the
migration was applied?

### Pattern 1: Backup Table Before Rollback

```sql
-- Scenario: added a "tier" column, users have been writing to it for 2 hours.
-- Need to roll back, but want to preserve the tier data for re-migration.

-- Step 1: Backup the data before rollback
CREATE TABLE IF NOT EXISTS _rollback_backup_user_tiers AS
SELECT id, tier, updated_at FROM users WHERE tier IS NOT NULL;

-- Step 2: Execute the rollback
ALTER TABLE users DROP COLUMN IF EXISTS tier;

-- Step 3: When ready to re-migrate, restore from backup
ALTER TABLE users ADD COLUMN tier VARCHAR(20);
UPDATE users u
SET tier = b.tier
FROM _rollback_backup_user_tiers b
WHERE u.id = b.id;

-- Step 4: Clean up backup table
DROP TABLE IF EXISTS _rollback_backup_user_tiers;
```

### Pattern 2: Soft Rollback with Feature Flag

Instead of physically rolling back the schema, disable the code that uses the new feature.

```python
USE_NEW_SCHEMA = os.getenv("USE_NEW_SCHEMA", "false") == "true"

def get_user_tier(user_id: int) -> str:
    if USE_NEW_SCHEMA:
        return db.query_one(
            "SELECT tier FROM users WHERE id = %s", (user_id,)
        )["tier"]
    else:
        # Fallback to old logic
        sub = db.query_one(
            "SELECT subscription_active FROM users WHERE id = %s",
            (user_id,)
        )
        return "premium" if sub["subscription_active"] else "free"
```

**Rollback**: set `USE_NEW_SCHEMA=false`. No schema change, no data loss, instant.

### Pattern 3: Reversible Data Transformation

When a migration transforms data (not just schema), design it so the transformation is
reversible.

```sql
-- Forward: merge first_name + last_name into full_name
-- V20__merge_names.sql

-- Step 1: Create the combined column
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Step 2: Backfill (preserving original data in existing columns)
UPDATE users SET full_name = first_name || ' ' || last_name;

-- DO NOT drop first_name and last_name yet!
-- The original data is the rollback mechanism.

-- U20__merge_names.sql (undo)
-- Simply drop the new column. Original data is intact.
ALTER TABLE users DROP COLUMN IF EXISTS full_name;
```

**Rule**: never destroy source data in the same migration that creates derived data.
Always keep the source until the derived data is verified and the contract phase is reached.

### Pattern 4: Event Sourcing for Critical Data

For critical data transformations, use an event log to make the transformation fully
reversible.

```sql
-- Before the migration, capture the state
CREATE TABLE migration_events (
    id          BIGSERIAL PRIMARY KEY,
    migration   VARCHAR(100) NOT NULL,
    table_name  VARCHAR(100) NOT NULL,
    row_id      BIGINT NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    applied_at  TIMESTAMPTZ DEFAULT NOW()
);

-- During the migration, log every change
INSERT INTO migration_events (migration, table_name, row_id, column_name,
                              old_value, new_value)
SELECT 'V20', 'users', id, 'status',
       status, 'active'
FROM users
WHERE status = 'enabled';

UPDATE users SET status = 'active' WHERE status = 'enabled';

-- Rollback: restore from the event log
UPDATE users u
SET status = me.old_value
FROM migration_events me
WHERE me.migration = 'V20'
  AND me.table_name = 'users'
  AND me.column_name = 'status'
  AND me.row_id = u.id;

DELETE FROM migration_events WHERE migration = 'V20';
```

---

## Handling Migrations That Fail Mid-Way

### Diagnosis

```sql
-- Flyway: check for failed migrations
SELECT version, description, state, installed_on, execution_time
FROM flyway_schema_history
WHERE success = false
ORDER BY installed_rank DESC;

-- PostgreSQL: check for orphaned transactions
SELECT pid, state, query_start, query, wait_event_type
FROM pg_stat_activity
WHERE state != 'idle' AND query LIKE '%migration%';

-- Check for blocked locks
SELECT
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query,
    now() - blocked.query_start AS wait_duration
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked ON blocked.pid = blocked_locks.pid
JOIN pg_locks blocking_locks
    ON blocking_locks.transactionid = blocked_locks.transactionid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_stat_activity blocking ON blocking.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

### Recovery by Database Type

**PostgreSQL** (transactional DDL):
```bash
# The failed migration was rolled back automatically by the transaction.
# Fix the migration script and re-apply.
flyway repair  # removes the FAILED entry from history
flyway migrate  # re-applies the fixed migration
```

**MySQL** (no transactional DDL):
```bash
# Partial state exists. Assess what was applied:
mysql -e "SHOW CREATE TABLE users\G"
# Compare against expected state.

# If the partially-applied state is broken:
# 1. Write a cleanup script to undo what was partially applied.
# 2. Run the cleanup.
# 3. Repair the migration history.
flyway repair
# 4. Fix the migration and re-apply.
flyway migrate
```

**Liquibase**:
```bash
# Mark the failed changeset as ran (if partial state is acceptable)
liquibase markNextChangeSetRan

# Or rollback to the previous changeset
liquibase rollbackCount 1

# Or rollback to a specific tag
liquibase rollback --tag=pre_v7
```

### Partial State Recovery Checklist

1. Identify which statements in the migration executed successfully.
2. Compare the actual schema against the expected pre-migration schema.
3. Compare the actual schema against the expected post-migration schema.
4. Write a recovery script that brings the database to one consistent state (either
   fully pre-migration or fully post-migration).
5. Test the recovery script on a copy of the database.
6. Apply the recovery script.
7. Repair the migration history table.

---

## Rollback Automation

### Emergency Rollback Script

```bash
#!/bin/bash
# emergency_rollback.sh
# Execute in case of post-migration incident.

set -euo pipefail

MIGRATION_VERSION="${1:?Usage: $0 <version_number>}"
DB_URL="${DATABASE_URL:?DATABASE_URL not set}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
UNDO_DIR="migrations/undo"

echo "[$TIMESTAMP] Starting emergency rollback of V${MIGRATION_VERSION}"

# 1. Verify the undo script exists
UNDO_SCRIPT=$(ls ${UNDO_DIR}/U${MIGRATION_VERSION}__*.sql 2>/dev/null || true)
if [ -z "$UNDO_SCRIPT" ]; then
    echo "ERROR: No undo script found for V${MIGRATION_VERSION}"
    echo "Manual intervention required."
    echo "Check: ${UNDO_DIR}/U${MIGRATION_VERSION}__*.sql"
    exit 1
fi

echo "Found undo script: $UNDO_SCRIPT"

# 2. Backup current schema before rollback
BACKUP_FILE="/tmp/pre_rollback_schema_${TIMESTAMP}.sql"
pg_dump "$DB_URL" --schema-only -f "$BACKUP_FILE"
echo "Schema backup: $BACKUP_FILE"

# 3. Execute the undo script
echo "Executing undo script..."
psql "$DB_URL" -f "$UNDO_SCRIPT" -v ON_ERROR_STOP=1 2>&1 | tee \
    "/var/log/migrations/rollback_${TIMESTAMP}.log"

# 4. Update the migration history table
psql "$DB_URL" -c "
    DELETE FROM flyway_schema_history
    WHERE version = '${MIGRATION_VERSION}';
"

# 5. Verify the rollback
CURRENT_VERSION=$(psql "$DB_URL" -t -c "
    SELECT MAX(version::int) FROM flyway_schema_history WHERE success = true;
")
echo "[$TIMESTAMP] Rollback complete."
echo "Current schema version: $CURRENT_VERSION"
echo "Verify application health before proceeding."
```

### CI Pipeline for Rollback Testing

```yaml
# .github/workflows/migration-rollback-test.yml
name: Migration Rollback Test

on:
  pull_request:
    paths:
      - 'db/migrations/**'

jobs:
  test-rollback:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Apply all migrations
        run: flyway -url=jdbc:postgresql://localhost/test_db migrate

      - name: Capture post-migration schema
        run: |
          pg_dump --schema-only -h localhost -U postgres test_db \
            > post_migration_schema.sql

      - name: Apply undo for latest migration
        run: |
          LATEST=$(ls db/migrations/undo/U*.sql | sort -V | tail -1)
          psql postgresql://postgres:test@localhost/test_db \
            -f "$LATEST" -v ON_ERROR_STOP=1

      - name: Re-apply latest migration
        run: flyway -url=jdbc:postgresql://localhost/test_db migrate

      - name: Verify schema matches post-migration
        run: |
          pg_dump --schema-only -h localhost -U postgres test_db \
            > re_applied_schema.sql
          diff post_migration_schema.sql re_applied_schema.sql
```

---

## Circuit Breaker for Production Migrations

A deployment pipeline with automatic rollback on failure.

```yaml
# .github/workflows/deploy.yml
- name: Run migrations with circuit breaker
  run: |
    # 1. Pre-migration schema backup
    pg_dump $DATABASE_URL --schema-only -f pre_migration_schema.sql

    # 2. Apply migrations with timeout
    timeout 300 flyway migrate -url="$DATABASE_URL" || {
        echo "Migration failed or timed out"

        # 3. Auto-rollback if undo script available
        LATEST_VERSION=$(flyway info -url="$DATABASE_URL" \
            | grep "Pending\|Failed" | head -1 | awk '{print $2}')
        UNDO_SCRIPT="migrations/undo/U${LATEST_VERSION}__*.sql"

        if ls $UNDO_SCRIPT 1>/dev/null 2>&1; then
            echo "Executing automatic rollback..."
            psql "$DATABASE_URL" -f $UNDO_SCRIPT
            flyway repair -url="$DATABASE_URL"
        else
            echo "No undo script found. Manual intervention required."
        fi
        exit 1
    }

    # 4. Post-migration smoke test
    python scripts/post_migration_smoke_test.py || {
        echo "Smoke test failed after migration"
        flyway undo -url="$DATABASE_URL"
        exit 1
    }

    echo "Migration and smoke test successful"
```

### Smoke Test Design

```python
#!/usr/bin/env python3
"""Post-migration smoke test."""

import sys
import psycopg2

def run_smoke_tests(conn_str: str) -> bool:
    conn = psycopg2.connect(conn_str)
    failures = []

    with conn.cursor() as cur:
        # Test 1: All expected tables exist
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = {row[0] for row in cur.fetchall()}
        expected = {'users', 'orders', 'products', 'order_items'}
        missing = expected - tables
        if missing:
            failures.append(f"Missing tables: {missing}")

        # Test 2: Critical columns exist
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'email';
        """)
        if cur.fetchone() is None:
            failures.append("users.email column missing")

        # Test 3: No invalid indexes
        cur.execute("""
            SELECT indexrelid::regclass FROM pg_index
            WHERE NOT indisvalid;
        """)
        invalid = cur.fetchall()
        if invalid:
            failures.append(f"Invalid indexes: {invalid}")

        # Test 4: Basic read succeeds
        cur.execute("SELECT COUNT(*) FROM users;")
        count = cur.fetchone()[0]
        if count == 0:
            failures.append("users table is empty")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return False

    print("All smoke tests passed.")
    return True

if __name__ == "__main__":
    import os
    success = run_smoke_tests(os.environ["DATABASE_URL"])
    sys.exit(0 if success else 1)
```

---

## Point-in-Time Recovery (PITR) Integration

When rollback scripts are insufficient (corrupted data, large-scale data loss), PITR
provides a nuclear option: restore the database to a specific point in time.

### PostgreSQL PITR with WAL Archiving

```bash
# postgresql.conf: enable WAL archiving
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
# Or to S3:
# archive_command = 'aws s3 cp %p s3://my-wal-archive/%f'
```

```bash
# Recovery: restore to a specific timestamp
# 1. Stop the database
pg_ctl stop -D /var/lib/postgresql/data

# 2. Replace data directory with the base backup
rm -rf /var/lib/postgresql/data/*
tar xzf /backups/base_backup_20250520.tar.gz \
    -C /var/lib/postgresql/data/

# 3. Create recovery configuration (PG >= 12)
cat > /var/lib/postgresql/data/postgresql.auto.conf << 'CONF'
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2025-05-20 14:30:00 UTC'
recovery_target_action = 'promote'
CONF

# 4. Create recovery signal file
touch /var/lib/postgresql/data/recovery.signal

# 5. Start the database - it replays WAL up to the target time
pg_ctl start -D /var/lib/postgresql/data
```

### PITR Decision Criteria

| Scenario | Use Undo Script | Use PITR |
|----------|----------------|----------|
| Schema change broke the app | Yes | No |
| Data corruption from bad UPDATE | Maybe | Yes |
| Accidental DROP TABLE | No | Yes |
| Accidental DELETE without WHERE | No | Yes |
| Migration applied but not needed | Yes | No |
| Multiple migrations need reversal | Maybe | Maybe |
| Need to recover to exact moment | No | Yes |

### PITR Limitations

- PITR restores the **entire database** to a point in time. You cannot selectively
  restore one table while keeping others current.
- All data written after the recovery target time is lost.
- Requires continuous WAL archiving to be configured **before** the incident.
- Recovery time depends on the volume of WAL to replay.

---

## Canary Migrations

A canary migration applies the change to a subset of the data first, validates the
result, and then applies it to the rest.

### Row-Level Canary

```sql
-- Step 1: Apply the transformation to a small subset
UPDATE users
SET tier = CASE
    WHEN subscription_active THEN 'premium'
    ELSE 'free'
END
WHERE id BETWEEN 1 AND 1000;  -- canary: first 1000 users

-- Step 2: Validate the canary
SELECT tier, COUNT(*) FROM users
WHERE id BETWEEN 1 AND 1000
GROUP BY tier;

-- Step 3: Run application smoke tests against canary users

-- Step 4: If validation passes, apply to the rest
UPDATE users
SET tier = CASE
    WHEN subscription_active THEN 'premium'
    ELSE 'free'
END
WHERE id > 1000 AND tier IS NULL;
```

### Shard-Level Canary

```python
def canary_migration(db, total_shards: int = 16, canary_shards: int = 2):
    """Apply migration to canary shards first, then the rest."""

    # Phase 1: Apply to canary shards
    for shard in range(canary_shards):
        db.execute(
            "UPDATE orders SET status_v2 = map_status(status) "
            "WHERE shard_key = %s AND status_v2 IS NULL",
            (shard,)
        )
        logger.info(f"Canary shard {shard} migrated")

    # Phase 2: Validate canary shards
    mismatches = db.query(
        "SELECT COUNT(*) FROM orders "
        "WHERE shard_key < %s AND status_v2 != map_status(status)",
        (canary_shards,)
    ).scalar()

    if mismatches > 0:
        logger.error(f"Canary failed: {mismatches} mismatches")
        db.execute(
            "UPDATE orders SET status_v2 = NULL WHERE shard_key < %s",
            (canary_shards,)
        )
        raise MigrationError("Canary validation failed")

    # Phase 3: Apply to remaining shards
    for shard in range(canary_shards, total_shards):
        db.execute(
            "UPDATE orders SET status_v2 = map_status(status) "
            "WHERE shard_key = %s AND status_v2 IS NULL",
            (shard,)
        )
        logger.info(f"Shard {shard} migrated")
```

---

## Rollback Plan Documentation

Every migration going to production must have a documented rollback plan.

### Template

```markdown
## Migration V15: Add customer_segments table

**Forward**: Creates customer_segments table with FK to customers.
**Undo Script**: U15__add_customer_segments.sql (tested in CI)
**Data Impact**: No existing data modified. New table only.
**Estimated Forward Duration**: ~30s
**Estimated Rollback Duration**: ~5s (DROP TABLE)
**Lock Impact**: CREATE TABLE does not lock existing tables.
**Backward Compatibility**: App v1 does not reference this table. Safe.
**Rollback Trigger**: If smoke tests fail after deployment.
**Data Loss on Rollback**: None (new table, no user data yet).
**Deployment Dependencies**: Code v2.4.0 must deploy BEFORE this migration.
**Monitoring**: Watch error rate, p99, replication lag for 30 min.
```

### Template for Destructive Migrations

```markdown
## Migration V20: Drop legacy_status column from orders

**Forward**: Drops the legacy_status column (unused since v2.1.0).
**Undo Script**: U20 (recreates column, backfill from backup required)
**Data Impact**: IRREVERSIBLE data loss. Column data deleted permanently.
**Pre-Migration Backup**:
  - Schema: /backup/orders_v19_20250520.sql
  - Data: /backup/legacy_status_values_20250520.csv
**Estimated Forward Duration**: ~2s (DROP COLUMN on PG 11+)
**Estimated Rollback Duration**: ~4 hours (recreate + backfill)
**Rollback Trigger**: Only if critical functionality depends on legacy_status.
```

---

## Multi-Migration Rollback

When a deployment includes multiple migrations and you need to roll back all of them.

### Sequential Rollback

```bash
#!/bin/bash
# rollback_to_version.sh

TARGET_VERSION="${1:?Usage: $0 <target_version>}"
DB_URL="${DATABASE_URL:?DATABASE_URL not set}"

CURRENT_VERSION=$(psql "$DB_URL" -t -c "
    SELECT MAX(version::int) FROM flyway_schema_history
    WHERE success = true;
")

echo "Rolling back from V${CURRENT_VERSION} to V${TARGET_VERSION}"

for v in $(seq "$CURRENT_VERSION" -1 $((TARGET_VERSION + 1))); do
    UNDO_SCRIPT=$(ls migrations/undo/U${v}__*.sql 2>/dev/null || true)
    if [ -z "$UNDO_SCRIPT" ]; then
        echo "ERROR: No undo script for V${v}. Cannot continue."
        exit 1
    fi

    echo "Rolling back V${v}..."
    psql "$DB_URL" -f "$UNDO_SCRIPT" -v ON_ERROR_STOP=1

    psql "$DB_URL" -c "
        DELETE FROM flyway_schema_history WHERE version = '${v}';
    "
done

echo "Rollback complete. Current version: V${TARGET_VERSION}"
```

### Alembic Multi-Step Rollback

```bash
# Downgrade to a specific revision
alembic downgrade a1b2c3d4

# Downgrade by N steps
alembic downgrade -3

# Downgrade to base (undo all migrations)
alembic downgrade base
```

### Liquibase Rollback by Tag

```bash
# Tag the current state before deployment
liquibase tag --tag=pre-release-2.5

# Deploy migrations
liquibase update

# If something goes wrong, rollback to the tag
liquibase rollback --tag=pre-release-2.5
```

---

## Real-World Scenarios

### Scenario 1: The Backfill That Corrupted Data

A migration backfills `full_name` by concatenating `first_name` and `last_name`.
But the concatenation does not handle NULL values correctly.

```sql
-- The buggy migration:
UPDATE users SET full_name = first_name || ' ' || last_name;
-- If first_name is NULL: full_name = NULL (SQL NULL propagation)
-- Expected: "John Smith", got: NULL for users with only first_name
```

**Recovery**:

```sql
UPDATE users
SET full_name = COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')
WHERE full_name IS NULL
   OR full_name != COALESCE(first_name, '') || ' ' || COALESCE(last_name, '');

UPDATE users SET full_name = TRIM(full_name);
```

### Scenario 2: Rollback Lost a Weekend of User Data

A migration adds `preferences JSONB`. Users write preferences for 48 hours. A bug in
unrelated code triggers a rollback. The rollback drops the column — 48 hours of user
preferences are lost.

**Lesson**: always backup new-column data before rollback.

```sql
CREATE TABLE _rollback_backup_preferences AS
SELECT id, preferences FROM users WHERE preferences IS NOT NULL;
-- Then proceed with rollback.
```

### Scenario 3: The Production Rollback Race Condition

V10 and V11 deployed together. V11 depends on V10. Rolling back V11 is correct, but
the team accidentally rolls back V10 too, breaking V11's undo script.

**Prevention**: specify exact target version. Never use "rollback latest" blindly.

### Scenario 4: MySQL Partial State After Crash

A MySQL migration with three ALTER statements crashes after the second. The first two
are auto-committed. The database is in an intermediate state.

**Recovery**:

```bash
# 1. Identify what was applied
mysql -e "DESCRIBE users;"

# 2. Write cleanup script
# 3. Apply cleanup, repair history, re-migrate
flyway repair && flyway migrate
```

---

## Troubleshooting

### 1. Rollback script fails with "column does not exist"

**Cause**: Forward migration was partially applied.

**Fix**: Make undo idempotent: `ALTER TABLE users DROP COLUMN IF EXISTS new_col;`

### 2. Rollback hangs waiting for lock

**Cause**: Active transactions using the table.

**Fix**: `SET lock_timeout = '5s';` and retry.

### 3. Data backup too large to store

**Fix**: Compress or use external storage:
```bash
psql "$DB_URL" -c \
  "COPY (SELECT id, preferences FROM users) TO STDOUT" \
  | gzip > /backup/preferences.csv.gz
```

### 4. Rollback leaves orphaned objects

**Fix**: Query for orphaned triggers, functions, sequences:
```sql
SELECT proname FROM pg_proc WHERE proname LIKE 'sync_%';
SELECT tgname, tgrelid::regclass FROM pg_trigger WHERE tgname LIKE 'trg_%';
```

### 5. Multi-migration rollback breaks dependency order

**Fix**: Always rollback in reverse order: latest first.

### 6. Flyway undo not available in Community Edition

**Fix**: Maintain undo scripts as standalone SQL files. Execute with `psql`, then
manually update `flyway_schema_history`.

### 7. Alembic downgrade fails on merge revision

**Cause**: Downgrading past a merge point requires choosing a branch.

**Fix**: Specify the exact target revision:
```bash
alembic downgrade <specific_revision_before_merge>
```

### 8. Rollback causes replication lag

**Cause**: DROP TABLE or large UPDATE generates significant WAL.

**Fix**: For large data operations, batch the rollback:
```sql
-- Instead of: DELETE FROM migration_events WHERE migration = 'V20';
-- Use batched delete:
DO $$
BEGIN
  LOOP
    DELETE FROM migration_events
    WHERE ctid IN (
      SELECT ctid FROM migration_events
      WHERE migration = 'V20'
      LIMIT 10000
    );
    EXIT WHEN NOT FOUND;
    PERFORM pg_sleep(0.1);
  END LOOP;
END;
$$;
```

---

## Frequently Asked Questions

### 1. Should every migration have an undo script?

For production systems: yes. For early-stage projects: optional, but recommended for
destructive changes (DROP, ALTER TYPE).

### 2. How do I test the undo script?

In CI: apply forward, capture schema, apply undo, re-apply forward, compare schemas.

### 3. What if the undo script causes data loss?

Document it in the rollback plan. If unacceptable, use a soft rollback (feature flag).

### 4. How quickly should I be able to roll back?

Target: under 5 minutes for schema-only rollbacks. Data-heavy rollbacks may take
longer — document the expected duration.

### 5. Can I roll back a NOT NULL constraint?

Yes: `ALTER TABLE users ALTER COLUMN email DROP NOT NULL;`

### 6. Should I use PITR instead of undo scripts?

PITR is a last resort. It restores the entire database, losing all post-recovery data.
Use it only for catastrophic failures.

### 7. What about rollback in microservices?

Each service rolls back independently. Coordinate via API contracts.

### 8. What if other services depend on the migrated schema?

You cannot roll back. The only option is roll-forward.

### 9. How do I handle rollback of enum changes?

PostgreSQL does not support removing enum values. Rollback requires creating a new type:
```sql
ALTER TYPE status RENAME TO status_old;
CREATE TYPE status AS ENUM ('active', 'inactive');
ALTER TABLE orders ALTER COLUMN status TYPE status USING status::text::status;
DROP TYPE status_old;
```

### 10. What is the safest rollback strategy overall?

Soft rollback via feature flags. No schema change, no data loss, instant switch. Reserve
schema rollback for cases where the schema itself is the problem.

---

## Exercises

### Exercise 1 (Beginner): Write an Undo Script

Given this forward migration:

```sql
-- V5__add_orders_table.sql
CREATE TABLE orders (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id),
    amount     DECIMAL(10,2) NOT NULL,
    status     VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
```

Write the complete undo script (U5).

### Exercise 2 (Intermediate): Data-Preserving Rollback

A migration merges the `addresses` table into `users.address_json JSONB`. Design a
rollback that preserves all address data. Include: backup step, undo script, data
restoration.

### Exercise 3 (Intermediate): Rollback Decision Scenario

V15 (adds `preferences` column) and V16 (adds `settings` table) deployed together.
After 4 hours, users report the settings page is slow — V16 is missing an index.

Options: rollback both, rollback V16 only, or roll forward with V17 (add index).
For each: steps, time, risks, data impact. Which do you recommend?

### Exercise 4 (Advanced): Circuit Breaker Pipeline

Design a CI/CD pipeline with: backup, migration with timeout, auto-rollback on failure,
smoke tests, auto-rollback on test failure, alerts, manual approval gate.

### Exercise 5 (Advanced): PITR Recovery Plan

A PostgreSQL database (200GB, WAL to S3, daily backups at 02:00 UTC) had an accidental
`DELETE FROM orders` at 14:30 UTC. Design: recovery steps, estimated time, data loss
assessment, verification plan, prevention measures.

---

## Key Takeaways

1. **Rollback is a design requirement**, not an afterthought.
2. **Every migration needs an undo script**, tested in CI.
3. **Roll-forward is often safer** than rollback when data has been written.
4. **Soft rollback via feature flags** is faster and safer than schema rollback.
5. **Never destroy source data** in the same migration that creates derived data.
6. **Document the rollback plan** for every production migration.
7. **Test rollback in CI**: apply, undo, re-apply, compare schemas.
8. **PITR is the nuclear option** — use it only for catastrophic failures.
9. **Time pressure kills**: if the rollback is not ready, triage first.
10. **Backup before rollback**: always capture new-column data before dropping it.
