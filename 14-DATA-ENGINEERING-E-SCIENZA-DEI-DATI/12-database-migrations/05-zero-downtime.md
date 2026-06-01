# Database Migrations — Zero-Downtime Migrations

## The Downtime Problem

A traditional migration requires: stop the application, apply the migration, restart the
application. For systems with 99.9% uptime SLAs or higher, this maintenance window is
unacceptable. For systems serving global traffic across time zones, there is no "low-traffic
window" — every minute of downtime costs revenue and trust.

**Zero-downtime migrations** (ZDM) solve this by allowing the database to transition from
one schema state to another while the application continues serving traffic. The application
and the database are never simultaneously at incompatible versions.

---

## Prerequisites for Zero-Downtime Migrations

### 1. Rolling Deployment

The application must support rolling deployment: multiple instances running simultaneously,
with some on version N and others on version N+1.

```
Before deploy:
  App v1 ─────────────── DB v1
  App v1 ─────────────── 

During deploy:
  App v1 ─────────────── DB v2 (migration applied)
  App v2 ─────────────── 

After deploy:
  App v2 ─────────────── DB v2
  App v2 ─────────────── 
```

### 2. Backward Compatibility

The code at version v1 must work with the database at version v2 during the transition.
This constraint drives all ZDM design decisions.

### 3. Health Checks

The application must have health checks that detect schema mismatches. If an instance
cannot operate against the current schema, it should fail its health check and be replaced.

### 4. Lock Awareness

All migrations must set `lock_timeout` to prevent indefinite blocking. A migration that
waits for a lock is equivalent to downtime for any query that needs the same lock.

### 5. Replication Awareness

Large DML operations must be batched to avoid replication lag spikes that degrade read
performance on replicas.

---

## Safe and Unsafe Operations

### Safe Operations (No Special Handling Required)

These operations complete quickly and do not break backward compatibility:

```sql
-- 1. Create a new table
CREATE TABLE IF NOT EXISTS feature_logs (
    id         BIGSERIAL PRIMARY KEY,
    feature    VARCHAR(100) NOT NULL,
    user_id    BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Add a nullable column without a default
ALTER TABLE users ADD COLUMN profile_photo_url TEXT;

-- 3. Add a column with a non-volatile default (PostgreSQL 11+)
-- This is O(1) — the default is stored in catalog metadata, not per row.
ALTER TABLE orders ADD COLUMN processing_fee DECIMAL(10,2) DEFAULT 0.00;

-- 4. Create an index with CONCURRENTLY (PostgreSQL)
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_orders_user ON orders(user_id);

-- 5. Add a CHECK constraint with NOT VALID
ALTER TABLE orders ADD CONSTRAINT chk_amount_positive
    CHECK (amount > 0) NOT VALID;

-- 6. Create a new view
CREATE OR REPLACE VIEW active_users AS
SELECT * FROM users WHERE status = 'active';
```

### Unsafe Operations (Require Expand-and-Contract)

These operations break backward compatibility or require locks that affect running queries:

```sql
-- 1. DROP COLUMN: old code still references it
ALTER TABLE users DROP COLUMN legacy_field;  -- breaks App v1

-- 2. NOT NULL on existing column: old code may not populate it
ALTER TABLE orders ALTER COLUMN notes SET NOT NULL;  -- breaks v1

-- 3. RENAME COLUMN: old code uses the old name
ALTER TABLE users RENAME COLUMN full_name TO display_name;  -- breaks v1

-- 4. Restrictive type change: may fail on existing data
ALTER TABLE orders ALTER COLUMN amount TYPE INTEGER;  -- breaks if decimals exist

-- 5. DROP TABLE: old code may still query it
DROP TABLE old_sessions;  -- breaks v1

-- 6. Add a required FK: old code may not populate it
ALTER TABLE orders ADD COLUMN customer_id BIGINT NOT NULL
    REFERENCES customers(id);  -- breaks v1
```

---

## Online DDL Mechanics

Understanding how each database engine handles DDL internally is critical for predicting
lock behavior and timing.

### PostgreSQL DDL Internals

PostgreSQL DDL operations acquire different lock levels:

| Operation | Lock Level | Concurrent DML? | Concurrent SELECT? |
|-----------|-----------|-----------------|-------------------|
| `CREATE TABLE` | ShareLock on schema | Yes | Yes |
| `ALTER TABLE ADD COLUMN` | AccessExclusiveLock | No | No |
| `ALTER TABLE ADD COLUMN DEFAULT` (PG 11+) | AccessExclusiveLock (brief) | Blocked briefly | Blocked briefly |
| `CREATE INDEX` | ShareLock | No writes | Yes |
| `CREATE INDEX CONCURRENTLY` | ShareUpdateExclusiveLock | Yes | Yes |
| `ALTER TABLE DROP COLUMN` | AccessExclusiveLock | No | No |
| `ALTER TABLE ADD CONSTRAINT` | ShareRowExclusiveLock | No writes | Yes |
| `ALTER TABLE ADD CONSTRAINT NOT VALID` | ShareUpdateExclusiveLock | Yes | Yes |
| `ALTER TABLE VALIDATE CONSTRAINT` | ShareUpdateExclusiveLock | Yes | Yes |
| `VACUUM` | ShareUpdateExclusiveLock | Yes | Yes |

**Key insight**: the AccessExclusiveLock blocks everything, but on PG 11+ the lock
duration for `ADD COLUMN DEFAULT` is a brief metadata update, not a full table rewrite.

The lock is acquired after waiting in the lock queue. If a long-running transaction holds
a conflicting lock, the DDL waits — and every new query that needs the same table also
waits behind the DDL. This can cascade into a full application stall.

**Prevention**: always set `lock_timeout`:

```sql
SET lock_timeout = '3s';
-- If the lock cannot be acquired within 3 seconds, the statement aborts
-- rather than waiting indefinitely and blocking all other queries.
ALTER TABLE users ADD COLUMN display_name TEXT;
```

### PostgreSQL: ADD COLUMN Deep Dive

```sql
-- PG < 11: ADD COLUMN with DEFAULT rewrites the entire table.
-- On a 100M-row table, this takes minutes to hours, holding
-- AccessExclusiveLock the entire time. Effectively downtime.

-- PG 11+: ADD COLUMN with non-volatile DEFAULT is O(1).
-- The default value is stored in pg_attrdef (catalog).
-- Existing rows do not need to be rewritten.
-- The lock is held only for the brief catalog update.

ALTER TABLE events ADD COLUMN processed BOOLEAN DEFAULT FALSE;
-- On PG 11+: instant, even on a 10B-row table.
-- On PG < 11: full table rewrite. Use the 4-step pattern instead.

-- "Volatile" defaults that trigger a rewrite even on PG 11+:
-- DEFAULT NOW()   -- volatile function
-- DEFAULT random() -- volatile function
-- To avoid: use DEFAULT CURRENT_TIMESTAMP (non-volatile in PG 12+)
-- or add the column without a default, then set the default separately.
```

### InnoDB Online DDL (MySQL 8.0+)

MySQL 8.0 introduced Online DDL with three algorithms:

```sql
-- INSTANT: metadata-only change, O(1). Fastest.
ALTER TABLE users ADD COLUMN bio TEXT, ALGORITHM=INSTANT;
-- Supported for: ADD COLUMN (at the end), DROP COLUMN (8.0.29+),
-- RENAME COLUMN, change default, extend VARCHAR.

-- INPLACE: modifies the table in-place without a full copy.
ALTER TABLE users ADD INDEX idx_email (email), ALGORITHM=INPLACE, LOCK=NONE;
-- Supported for: ADD INDEX, DROP INDEX, ADD COLUMN (some cases).
-- LOCK=NONE allows concurrent DML.

-- COPY: creates a new table, copies data, swaps. Slowest.
ALTER TABLE users MODIFY COLUMN name VARCHAR(500), ALGORITHM=COPY;
-- Used when INSTANT and INPLACE are not supported.
-- Blocks concurrent DML unless LOCK=NONE is possible.
```

```sql
-- Check which algorithm MySQL will use:
ALTER TABLE users ADD COLUMN bio TEXT, ALGORITHM=INSTANT;
-- If INSTANT is not supported, MySQL returns an error.
-- Then try INPLACE, then COPY.
```

### SQL Server Online Operations

```sql
-- Online index operations (Enterprise Edition):
CREATE INDEX idx_users_email ON dbo.Users(Email) WITH (ONLINE = ON);
-- Allows concurrent DML during index creation.

-- Online ALTER COLUMN (SQL Server 2016+):
ALTER TABLE dbo.Users ALTER COLUMN Email NVARCHAR(500);
-- Most ALTER COLUMN operations are online by default.

-- Schema switches for zero-downtime DDL:
-- SQL Server supports ALTER TABLE ... SWITCH for partition swaps.
```

---

## Adding Columns Safely

### Nullable Column (Always Safe)

```sql
SET lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN notes TEXT;
-- Lock held: brief (catalog update only).
-- Old code: ignores the column. No breakage.
-- New code: reads/writes notes.
```

### Column with Default (PostgreSQL 11+)

```sql
SET lock_timeout = '3s';
ALTER TABLE orders ADD COLUMN priority INT DEFAULT 0;
-- PG 11+: O(1), instant.
-- Old code: SELECT * returns priority=0 for existing rows. Safe.
-- New code: writes explicit priority values.
```

### Column with Default (Pre-PG-11 or MySQL without INSTANT)

```sql
-- Step 1: Add nullable column (instant)
ALTER TABLE orders ADD COLUMN priority INT;

-- Step 2: Set default for new rows
ALTER TABLE orders ALTER COLUMN priority SET DEFAULT 0;

-- Step 3: Backfill existing rows in batches (separate migration)
DO $$
DECLARE batch INT := 10000; last_id BIGINT := 0; max_id BIGINT;
BEGIN
  SELECT MAX(id) INTO max_id FROM orders;
  WHILE last_id < max_id LOOP
    UPDATE orders SET priority = 0
    WHERE id > last_id AND id <= last_id + batch AND priority IS NULL;
    last_id := last_id + batch;
    PERFORM pg_sleep(0.05);
  END LOOP;
END; $$;

-- Step 4: Add NOT NULL constraint (after backfill verified)
ALTER TABLE orders ALTER COLUMN priority SET NOT NULL;
```

---

## Renaming Columns and Tables

Renaming is the most operationally complex zero-downtime operation because the old code
uses the old name and the new code uses the new name.

### Renaming a Column (6-Phase Process)

```sql
-- Scenario: rename "email_address" to "email"

-- PHASE 1 (Migration V20): Add new column
SET lock_timeout = '3s';
ALTER TABLE users ADD COLUMN email VARCHAR(255);

-- PHASE 2 (Migration V21): Backfill
UPDATE users SET email = email_address WHERE email IS NULL;

-- PHASE 3 (Code v2): Dual-write
-- INSERT INTO users (email_address, email) VALUES ($1, $1)
-- UPDATE users SET email_address = $1, email = $1

-- PHASE 4 (Code v3): Read from new column only
-- SELECT email FROM users (not email_address)

-- PHASE 5: Verify no instances of v2 or earlier are running

-- PHASE 6 (Migration V22): Drop old column
SET lock_timeout = '3s';
ALTER TABLE users DROP COLUMN email_address;
```

### Renaming a Table

```sql
-- Scenario: rename "user_profiles" to "profiles"

-- PHASE 1 (Migration V30): Create view with old name
ALTER TABLE user_profiles RENAME TO profiles;
CREATE VIEW user_profiles AS SELECT * FROM profiles;

-- Old code: SELECT * FROM user_profiles  -- works (hits the view)
-- New code: SELECT * FROM profiles       -- works (hits the table)

-- PHASE 2 (Code v2): All code uses "profiles"

-- PHASE 3 (Migration V31): Drop the view
DROP VIEW user_profiles;
```

**Limitation**: the view approach does not work for INSERT/UPDATE/DELETE if the view
is not updatable. For complex tables, use an INSTEAD OF trigger on the view.

---

## Adding Constraints Safely

### NOT NULL Constraint

Adding NOT NULL directly acquires AccessExclusiveLock and scans the entire table to
verify no NULLs exist. On large tables, this blocks for seconds to minutes.

```sql
-- Step 1: Backfill NULLs (separate migration, batched)
UPDATE users SET phone = 'unknown' WHERE phone IS NULL;

-- Step 2: Add CHECK constraint as NOT VALID (instant, no table scan)
ALTER TABLE users ADD CONSTRAINT chk_phone_not_null
    CHECK (phone IS NOT NULL) NOT VALID;
-- NOT VALID: validates new rows only, does not scan existing rows.

-- Step 3: Validate the constraint (background, does not block DML)
ALTER TABLE users VALIDATE CONSTRAINT chk_phone_not_null;
-- VALIDATE scans the table but holds only ShareUpdateExclusiveLock,
-- which allows concurrent reads and writes.

-- Step 4: Convert to column-level NOT NULL (now safe, PG trusts the CHECK)
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;
ALTER TABLE users DROP CONSTRAINT chk_phone_not_null;
```

### Foreign Key Constraint

```sql
-- Direct ADD FOREIGN KEY scans the entire referencing table while holding
-- ShareRowExclusiveLock. On large tables, this blocks writes for minutes.

-- Step 1: Add FK with NOT VALID (instant, no scan)
SET lock_timeout = '3s';
ALTER TABLE orders ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers(id) NOT VALID;

-- Step 2: Validate (background scan, concurrent DML allowed)
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_customer;
```

### UNIQUE Constraint

```sql
-- Adding UNIQUE directly creates an index while holding AccessExclusiveLock.
-- Use CONCURRENTLY instead:

-- Step 1: Create unique index CONCURRENTLY
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
    idx_users_email_unique ON users(email);

-- Step 2: Add the constraint using the existing index
ALTER TABLE users ADD CONSTRAINT uq_users_email
    UNIQUE USING INDEX idx_users_email_unique;
```

---

## Index Creation

### PostgreSQL: CONCURRENTLY

```sql
-- Standard CREATE INDEX: holds ShareLock, blocks writes until complete.
-- On a 500M-row table, this can take 30+ minutes of write blocking.

-- CREATE INDEX CONCURRENTLY: allows concurrent reads AND writes.
-- Takes longer (two table scans) but does not block DML.
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_events_user_date ON events(user_id, event_date DESC);

-- Monitoring progress:
SELECT phase, blocks_done, blocks_total,
       round(blocks_done::numeric / nullif(blocks_total, 0) * 100, 2) AS pct,
       tuples_done, tuples_total
FROM pg_stat_progress_create_index;

-- CONCURRENTLY limitations:
-- 1. Cannot run inside a transaction block.
-- 2. If interrupted, leaves an INVALID index that must be dropped.
-- 3. Takes roughly 2x the time of a standard CREATE INDEX.
-- 4. Requires two table scans instead of one.
```

### Handling Failed CONCURRENTLY

```sql
-- Check for invalid indexes
SELECT indexrelid::regclass AS index_name,
       indrelid::regclass AS table_name
FROM pg_index
WHERE NOT indisvalid;

-- Drop the invalid index and retry
DROP INDEX CONCURRENTLY IF EXISTS idx_events_user_date;
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_events_user_date ON events(user_id, event_date DESC);
```

### MySQL: Online Index Creation

```sql
-- MySQL 8.0+: most index operations support INPLACE + LOCK=NONE
ALTER TABLE events ADD INDEX idx_events_user (user_id),
    ALGORITHM=INPLACE, LOCK=NONE;
-- Allows concurrent DML during index creation.

-- For operations that do not support INPLACE:
-- Use gh-ost to create the index as part of a table restructure.
```

---

## Enum Changes

PostgreSQL enums are notoriously difficult to modify in a zero-downtime way.

### Adding an Enum Value

```sql
-- Adding a value is safe but has a transaction restriction:
-- ALTER TYPE ... ADD VALUE cannot run inside a transaction in PG < 12.
-- In PG 12+, it can run in a transaction if it is the only statement.

ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'refunded';
-- This is a metadata-only change. Instant.

-- Flyway: set flyway.mixed=true for non-transactional operations.
-- Or use a separate migration file for each enum change.
```

### Removing or Renaming an Enum Value

PostgreSQL does not support removing or renaming enum values directly.
You must create a new type and migrate.

```sql
-- Step 1: Create new enum type
CREATE TYPE order_status_new AS ENUM (
    'pending', 'processing', 'completed', 'refunded'
    -- removed 'cancelled', renamed 'done' to 'completed'
);

-- Step 2: Convert the column
ALTER TABLE orders ALTER COLUMN status
    TYPE order_status_new
    USING CASE
        WHEN status::text = 'done' THEN 'completed'::order_status_new
        WHEN status::text = 'cancelled' THEN 'refunded'::order_status_new
        ELSE status::text::order_status_new
    END;

-- Step 3: Drop old type
DROP TYPE order_status;

-- Step 4: Rename new type
ALTER TYPE order_status_new RENAME TO order_status;
```

**Zero-downtime approach**: use a VARCHAR column instead of an enum, with a CHECK
constraint for validation. This avoids the enum type migration problem entirely.

```sql
-- Instead of: status order_status
-- Use:
status VARCHAR(20) CHECK (status IN ('pending', 'processing', 'completed', 'refunded'))
-- Adding a new value: update the CHECK constraint.
-- Removing a value: update the CHECK constraint.
-- No type migration needed.
```

---

## Large Data Backfills

Backfilling data in a new column on a large table is the most operationally risky part
of a zero-downtime migration.

### Batched Backfill with Progress Tracking

```sql
DO $$
DECLARE
    batch_size INT := 5000;
    total_updated BIGINT := 0;
    batch_updated INT;
    start_time TIMESTAMPTZ := NOW();
BEGIN
    LOOP
        -- Use a CTE to limit the update scope
        WITH batch AS (
            SELECT id FROM events
            WHERE processed IS NULL
            ORDER BY id
            LIMIT batch_size
        )
        UPDATE events e
        SET processed = FALSE
        FROM batch b
        WHERE e.id = b.id;

        GET DIAGNOSTICS batch_updated = ROW_COUNT;
        total_updated := total_updated + batch_updated;

        EXIT WHEN batch_updated = 0;

        -- Progress log
        IF total_updated % 100000 = 0 THEN
            RAISE NOTICE '% rows updated in %',
                total_updated,
                age(NOW(), start_time);
        END IF;

        -- Yield to other queries and let replicas catch up
        PERFORM pg_sleep(0.05);
    END LOOP;

    RAISE NOTICE 'Backfill complete: % rows in %',
        total_updated, age(NOW(), start_time);
END;
$$;
```

### Backfill with Replication Lag Monitoring

```python
import psycopg2
import time

def backfill_with_lag_control(
    primary_conn_str: str,
    batch_size: int = 5000,
    max_lag_seconds: float = 30.0,
    sleep_between_batches: float = 0.05,
):
    conn = psycopg2.connect(primary_conn_str)
    conn.autocommit = True
    total = 0

    while True:
        # Check replication lag before each batch
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MAX(EXTRACT(EPOCH FROM replay_lag))
                FROM pg_stat_replication
            """)
            lag = cur.fetchone()[0] or 0

        if lag > max_lag_seconds:
            print(f"Replication lag {lag:.1f}s > {max_lag_seconds}s. Pausing...")
            time.sleep(5)
            continue

        # Execute batch
        with conn.cursor() as cur:
            cur.execute("""
                WITH batch AS (
                    SELECT id FROM events
                    WHERE processed IS NULL
                    ORDER BY id
                    LIMIT %s
                )
                UPDATE events e SET processed = FALSE
                FROM batch b WHERE e.id = b.id
            """, (batch_size,))
            affected = cur.rowcount

        if affected == 0:
            break

        total += affected
        if total % 100000 == 0:
            print(f"Updated {total} rows, lag: {lag:.1f}s")

        time.sleep(sleep_between_batches)

    print(f"Backfill complete: {total} rows")
```

---

## Foreign Key Additions

Adding a foreign key constraint to an existing large table is one of the most dangerous
zero-downtime operations because the validation scan holds a lock that blocks writes.

```sql
-- UNSAFE: Direct ADD FOREIGN KEY
-- Scans the entire child table while holding ShareRowExclusiveLock.
-- On a 100M-row orders table, this blocks writes for minutes.
ALTER TABLE orders ADD FOREIGN KEY (customer_id) REFERENCES customers(id);

-- SAFE: Two-phase approach
-- Phase 1: Add constraint as NOT VALID (instant, no scan)
SET lock_timeout = '3s';
ALTER TABLE orders ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id) REFERENCES customers(id) NOT VALID;
-- NOT VALID: enforces the constraint for new rows only.
-- Old rows are not validated. Instant.

-- Phase 2: Validate (background scan, allows concurrent DML)
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_customer;
-- This scans the table to verify all existing rows satisfy the FK.
-- But it holds ShareUpdateExclusiveLock, which allows concurrent DML.
-- Duration: proportional to table size, but non-blocking.
```

---

## Migration Orchestration

### Deployment Pipeline for Zero-Downtime

```
Commit --> CI
            |-- Unit tests
            |-- Migration dry run (--dry-run or --sql)
            |-- Migration safety check (linter, lock analysis)
            |-- Build docker image

Deploy --> Staging
            |-- Apply migrations
            |-- Smoke tests
            |-- Performance regression test

Deploy --> Production
            |-- Apply migrations BEFORE code deploy
            |   (DB v2 must be backward-compatible with App v1)
            |-- Rolling deploy App v2
            |   (5-10 min: both v1 and v2 running against DB v2)
            |-- Post-deploy smoke tests
            |-- Monitor error rate, latency, replication lag for 30 min
```

### Lock Monitoring During Migration

```sql
-- Real-time lock monitoring during migration
SELECT
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query,
    now() - blocked.query_start AS wait_duration
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked ON blocked.pid = blocked_locks.pid
JOIN pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.relation = blocked_locks.relation
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_stat_activity blocking ON blocking.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted
  AND blocked.query LIKE '%ALTER TABLE%'
ORDER BY wait_duration DESC;
```

### Retry Pattern for Lock Acquisition

```bash
#!/bin/bash
# retry_migration.sh: retry ALTER TABLE with short lock_timeout

MAX_RETRIES=10
RETRY_DELAY=5

for i in $(seq 1 $MAX_RETRIES); do
    echo "Attempt $i/$MAX_RETRIES"
    psql "$DATABASE_URL" -c "
        SET lock_timeout = '3s';
        ALTER TABLE orders ADD COLUMN notes TEXT;
    " 2>&1

    if [ $? -eq 0 ]; then
        echo "Migration succeeded on attempt $i"
        exit 0
    fi

    echo "Lock not acquired. Waiting ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done

echo "Migration failed after $MAX_RETRIES attempts."
exit 1
```

---

## MySQL Zero-Downtime with gh-ost

For MySQL, most ALTER TABLE operations that cannot use ALGORITHM=INSTANT require an
external tool.

```bash
gh-ost \
    --host=mysql-primary \
    --database=myapp \
    --table=orders \
    --alter="ADD COLUMN notes TEXT NULL, ADD INDEX idx_created (created_at)" \
    --chunk-size=2000 \
    --throttle-control-replicas="mysql-replica:3306" \
    --max-load="Threads_running=30" \
    --critical-load="Threads_running=80" \
    --default-retries=3 \
    --panic-flag-file=/tmp/gh-ost.panic \
    --ok-to-drop-table \
    --execute \
    2>&1 | tee /var/log/gh-ost-migration.log

# To pause: touch /tmp/gh-ost.throttle
# To abort: touch /tmp/gh-ost.panic
# To monitor: gh-ost --status
```

---

## Real-World Scenarios

### Scenario 1: Adding a Required Column to a 500M-Row Table

A SaaS platform needs to add `tenant_id BIGINT NOT NULL` to a 500M-row `events` table.

```
Week 1:
  V30: ALTER TABLE events ADD COLUMN tenant_id BIGINT;  -- nullable, instant
  Deploy app v2: writes tenant_id on new inserts

Week 1-2:
  V31: Batched backfill (tenant_id from projects join)
  Monitor: replication lag, disk I/O, query latency
  
Week 3:
  V32: CREATE INDEX CONCURRENTLY idx_events_tenant ON events(tenant_id);
  
Week 3:
  V33: ALTER TABLE events ADD CONSTRAINT chk_tenant_not_null
       CHECK (tenant_id IS NOT NULL) NOT VALID;
  V34: ALTER TABLE events VALIDATE CONSTRAINT chk_tenant_not_null;
  V35: ALTER TABLE events ALTER COLUMN tenant_id SET NOT NULL;
       ALTER TABLE events DROP CONSTRAINT chk_tenant_not_null;
  
Week 4:
  V36: ALTER TABLE events ADD CONSTRAINT fk_events_tenant
       FOREIGN KEY (tenant_id) REFERENCES tenants(id) NOT VALID;
  V37: ALTER TABLE events VALIDATE CONSTRAINT fk_events_tenant;
```

Total: 8 migrations over 4 weeks. Each individually deployable and rollback-safe.

### Scenario 2: Changing a Column Type Under Load

An `orders.amount DECIMAL(10,2)` column needs to become `BIGINT` (storing cents).
The table has 200M rows and handles 3K writes/sec during peak.

```sql
-- Phase 1: Add shadow column
ALTER TABLE orders ADD COLUMN amount_cents BIGINT;

-- Phase 2: Sync trigger
CREATE OR REPLACE FUNCTION sync_amount_cents()
RETURNS TRIGGER AS $$
BEGIN
    NEW.amount_cents = (NEW.amount * 100)::BIGINT;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_amount
    BEFORE INSERT OR UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION sync_amount_cents();

-- Phase 3: Batched backfill (separate migration)
-- Phase 4: App reads from amount_cents, writes to both
-- Phase 5: Drop old column, trigger, function
```

### Scenario 3: The Lock Queue Cascade

A developer runs `ALTER TABLE orders ADD COLUMN` during peak hours. A long-running
analytics query holds a ShareLock on `orders`. The ALTER waits for AccessExclusiveLock.
Every new SELECT and INSERT also waits, queued behind the ALTER.

Within 30 seconds, the connection pool is exhausted. The application returns 503 errors.

**Prevention**:
```sql
-- Always set lock_timeout
SET lock_timeout = '3s';
-- The ALTER will abort after 3 seconds if it cannot acquire the lock,
-- instead of waiting and cascading the blockage.
```

**Recovery**:
```sql
-- Terminate the blocking analytics query
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE query LIKE '%SELECT%FROM orders%'
  AND state = 'active'
  AND now() - query_start > interval '1 minute';
```

---

## Troubleshooting

### 1. ALTER TABLE hangs despite lock_timeout

**Cause**: `lock_timeout` only applies to the lock acquisition, not to the DDL operation
itself. If the lock is acquired but the operation (e.g., table rewrite) takes long,
`statement_timeout` is the relevant setting.

**Fix**: Set both:
```sql
SET lock_timeout = '3s';
SET statement_timeout = '300s';
```

### 2. CONCURRENTLY index build fails repeatedly

**Cause**: Long-running transactions prevent the second phase of the concurrent build.

**Fix**: Identify and terminate long transactions:
```sql
SELECT pid, now() - xact_start AS duration, query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY duration DESC;
```

### 3. NOT VALID constraint not enforced for new rows

**Cause**: This is expected behavior. NOT VALID means "do not validate existing rows"
but it DOES enforce the constraint for new inserts and updates. If new rows violate it,
those operations will fail.

**Fix**: Not a bug. Verify by inserting a violating row (it should fail).

### 4. Enum ADD VALUE breaks Flyway transaction

**Cause**: `ALTER TYPE ... ADD VALUE` cannot run in a transaction on PG < 12.

**Fix**: Set `flyway.mixed=true` or put enum changes in their own migration file.

### 5. Backfill causes autovacuum delay

**Cause**: The batched UPDATE generates dead tuples. If batches run faster than
autovacuum can clean them, table bloat grows.

**Fix**: Increase autovacuum aggressiveness for the target table:
```sql
ALTER TABLE events SET (
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.005
);
```

### 6. MySQL ALGORITHM=INSTANT not available for operation

**Cause**: Not all operations support INSTANT. Check MySQL docs for the specific
operation.

**Fix**: Fall back to INPLACE, then to gh-ost:
```sql
-- Try INSTANT first
ALTER TABLE users ADD COLUMN bio TEXT, ALGORITHM=INSTANT;
-- If error: try INPLACE
ALTER TABLE users ADD COLUMN bio TEXT, ALGORITHM=INPLACE, LOCK=NONE;
-- If error: use gh-ost
```

---

## Frequently Asked Questions

### 1. Is every ALTER TABLE a risk?

No. On PostgreSQL 11+, adding a nullable column or a column with a non-volatile default
is O(1) and safe. The risk comes from operations that rewrite the table (type changes,
NOT NULL on PG < 11) or scan it (VALIDATE CONSTRAINT, CREATE INDEX without CONCURRENTLY).

### 2. Can I add a column and set NOT NULL in one statement?

Not safely. The combined operation requires a table scan while holding AccessExclusiveLock.
Split it: add column, backfill, add NOT NULL.

### 3. How do I measure the lock duration of an ALTER?

```sql
SET lock_timeout = '0';  -- disable timeout for measurement
\timing on
ALTER TABLE orders ADD COLUMN test_col TEXT;
ALTER TABLE orders DROP COLUMN test_col;
\timing off
```

### 4. What is the maximum safe migration duration?

There is no universal answer. It depends on your `lock_timeout`, transaction volume,
and connection pool size. As a guideline: any DDL that holds AccessExclusiveLock should
complete within 1 second. Any background operation (VALIDATE, CONCURRENTLY) can take
hours without issue.

### 5. How do I handle views that depend on renamed columns?

Drop and recreate the view:
```sql
DROP VIEW IF EXISTS user_summary;
-- Rename the column
ALTER TABLE users RENAME COLUMN email_address TO email;
-- Recreate the view with the new column name
CREATE VIEW user_summary AS SELECT id, email FROM users;
```

---

## Exercises

### Exercise 1 (Beginner): Classify Operations

Classify each operation as SAFE or UNSAFE for zero-downtime:
1. `CREATE TABLE logs (...)`
2. `ALTER TABLE users DROP COLUMN legacy`
3. `ALTER TABLE orders ADD COLUMN notes TEXT`
4. `ALTER TABLE users RENAME COLUMN name TO display_name`
5. `CREATE INDEX CONCURRENTLY idx_orders ON orders(user_id)`
6. `ALTER TABLE orders ALTER COLUMN amount TYPE BIGINT`

### Exercise 2 (Intermediate): NOT NULL Migration Plan

Design a zero-downtime plan to add `NOT NULL` to `orders.customer_email` (currently
nullable, 50M rows, 5% are NULL). Include all migrations and application code changes.

### Exercise 3 (Intermediate): Column Type Change

Change `users.age INT` to `users.age SMALLINT` on a 10M-row table without downtime.
Consider: what happens if some values exceed SMALLINT range? Include validation.

### Exercise 4 (Advanced): Full Rename Plan

Rename the `user_profiles` table to `profiles` and rename `user_profiles.user_email`
to `profiles.email`. The table has 30M rows and is referenced by 5 foreign keys from
other tables. Design the complete zero-downtime plan with all migrations.

### Exercise 5 (Advanced): Lock Analysis

Given this migration on a table with 100M rows:

```sql
ALTER TABLE events ADD COLUMN category VARCHAR(50) DEFAULT 'general';
CREATE INDEX idx_events_category ON events(category);
ALTER TABLE events ADD CONSTRAINT fk_events_user
    FOREIGN KEY (user_id) REFERENCES users(id);
```

1. What lock does each operation take?
2. Which operations block concurrent DML?
3. How long will each operation take (estimate)?
4. Rewrite this migration for zero-downtime.

---

## Key Takeaways

1. **Backward compatibility is the non-negotiable rule.** DB v2 must work with App v1.
2. **Set lock_timeout on every DDL statement.** 3-5 seconds is a good default.
3. **Use CONCURRENTLY for indexes**, NOT VALID + VALIDATE for constraints.
4. **Add columns with defaults** on PG 11+ — it is O(1).
5. **Never rename directly.** Use the expand-and-contract pattern over multiple deploys.
6. **Batch all data backfills.** Monitor replication lag between batches.
7. **Separate DDL and DML** into different migration files.
8. **Use gh-ost or pt-osc** for MySQL operations that do not support ALGORITHM=INSTANT.
9. **Monitor locks in real-time** during migration execution.
10. **Test with production-scale data.** A 5-second migration on dev can take 5 hours
    on production.

Zero-downtime migrations are the differentiator between teams that deploy with anxiety
and teams that deploy with confidence. The fundamental requirement is that every migration
is designed for backward compatibility.
