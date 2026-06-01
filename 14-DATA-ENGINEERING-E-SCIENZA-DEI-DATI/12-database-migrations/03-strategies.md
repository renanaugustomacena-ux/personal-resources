# Database Migrations — Migration Strategies

## Why Strategy Matters

A migration strategy is the plan for how you transform a database from state A to state B
while the system continues to operate. The choice of strategy determines whether the change
is invisible to users, causes a brief outage, or creates a multi-day incident.

There is no universal strategy. The right choice depends on:

- **Table size**: 1K rows vs 1B rows require fundamentally different approaches.
- **Database engine**: PostgreSQL's transactional DDL vs MySQL's implicit commit.
- **Uptime SLA**: 99.9% (8.7h/year downtime) vs 99.99% (52 min/year).
- **Replication topology**: single-primary vs multi-primary.
- **Change type**: additive (new column) vs destructive (rename, drop, type change).

This chapter covers the major strategies, when to use each, and how to implement them
with production-grade SQL and tooling.

---

## Expand-and-Contract (Parallel Change)

The **expand-and-contract** pattern (also called parallel change, or branch-by-abstraction
for schemas) is the foundational strategy for backward-compatible migrations. Every other
zero-downtime technique is a specialization of this pattern.

### The Three Phases

```
Phase 1: EXPAND     — Add the new structure alongside the old.
Phase 2: MIGRATE    — Backfill data, update code to read/write both.
Phase 3: CONTRACT   — Remove the old structure after all code uses the new.
```

### Phase 1: Expand

The expand phase is purely additive. No existing column is modified or removed.
The old code continues to work without any change.

```sql
-- Scenario: rename column "full_name" to "display_name"
-- Migration V10: add the new column, keep the old

ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Trigger to keep both columns in sync during the transition
CREATE OR REPLACE FUNCTION sync_display_name()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        IF NEW.full_name IS NOT NULL AND NEW.display_name IS NULL THEN
            NEW.display_name = NEW.full_name;
        END IF;
        IF NEW.display_name IS NOT NULL AND NEW.full_name IS NULL THEN
            NEW.full_name = NEW.display_name;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_display_name
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION sync_display_name();
```

**Key properties**:
- Old code sees `full_name` and continues to work.
- New code can start using `display_name`.
- The trigger ensures data consistency during the transition.

### Phase 2: Migrate (Backfill)

Populate the new column with existing data. This is the most operationally risky phase
because it involves DML on potentially large tables.

```sql
-- Migration V11: backfill display_name from full_name
-- Batched to avoid long-running transactions and replication lag

DO $$
DECLARE
    batch_size INT := 10000;
    last_id BIGINT := 0;
    max_id BIGINT;
    rows_affected BIGINT;
BEGIN
    SELECT MAX(id) INTO max_id FROM users;
    IF max_id IS NULL THEN RETURN; END IF;

    WHILE last_id < max_id LOOP
        UPDATE users
        SET display_name = full_name
        WHERE id > last_id
          AND id <= last_id + batch_size
          AND display_name IS NULL
          AND full_name IS NOT NULL;

        GET DIAGNOSTICS rows_affected = ROW_COUNT;
        last_id := last_id + batch_size;

        -- Log progress every 100K rows
        IF last_id % 100000 = 0 THEN
            RAISE NOTICE 'Backfilled to id %, rows this batch: %',
                last_id, rows_affected;
        END IF;

        PERFORM pg_sleep(0.1);  -- yield CPU and let replicas catch up
    END LOOP;
END;
$$;

-- After backfill is complete and verified, add NOT NULL
ALTER TABLE users ALTER COLUMN display_name SET NOT NULL;
```

**During this phase**, the application code is updated:

```python
# Application code: dual-write during migration
class UserRepository:
    def update_name(self, user_id: int, name: str):
        self.db.execute(
            "UPDATE users SET full_name = %s, display_name = %s WHERE id = %s",
            (name, name, user_id)
        )

    def get_display_name(self, user_id: int) -> str:
        row = self.db.query_one(
            "SELECT display_name, full_name FROM users WHERE id = %s",
            (user_id,)
        )
        # Prefer new column, fall back to old
        return row["display_name"] or row["full_name"] or ""
```

### Phase 3: Contract

Remove the old structure after all application instances use the new one.

```sql
-- Migration V12: remove old column and sync trigger
-- Only after verifying that no code references full_name

DROP TRIGGER IF EXISTS trg_sync_display_name ON users;
DROP FUNCTION IF EXISTS sync_display_name();
ALTER TABLE users DROP COLUMN IF EXISTS full_name;
```

### Timeline

```
Week 1: Deploy V10 (expand). Old code still works.
Week 1: Deploy application v2 (reads display_name, writes both).
Week 1: Deploy V11 (backfill). Run batched update.
Week 2: Verify all instances are on v2. Remove old code paths.
Week 2: Deploy V12 (contract). Drop old column.
```

The key insight: each phase can be independently deployed, tested, and rolled back.
If the backfill causes problems, you can stop it without affecting the running application.

---

## Shadow Writes (Dual-Write Pattern)

Shadow writes extend the expand-and-contract pattern to entire tables or databases. The
application writes to both the old and new location simultaneously.

### Use Cases

- Migrating from one table structure to another.
- Migrating from one database engine to another.
- Replacing a legacy system with a new one.

### Implementation

```python
class OrderRepository:
    """Dual-write to old and new table during migration."""

    def __init__(self, db, shadow_enabled: bool = False):
        self.db = db
        self.shadow_enabled = shadow_enabled

    def create_order(self, order: Order) -> int:
        # Always write to the old table (source of truth)
        order_id = self.db.execute(
            "INSERT INTO orders (user_id, amount, status) "
            "VALUES (%s, %s, %s) RETURNING id",
            (order.user_id, order.amount, order.status)
        ).scalar()

        # Shadow write to the new table
        if self.shadow_enabled:
            try:
                self.db.execute(
                    "INSERT INTO orders_v2 (id, user_id, amount_cents, "
                    "status, created_at) "
                    "VALUES (%s, %s, %s, %s, NOW())",
                    (order_id, order.user_id,
                     int(order.amount * 100),  # convert to cents
                     order.status)
                )
            except Exception as e:
                # Shadow write failure must NOT fail the primary write
                logger.error(f"Shadow write failed for order {order_id}: {e}")
                metrics.increment("shadow_write.failure")

        return order_id

    def get_order(self, order_id: int) -> Order:
        # Read from old table (source of truth during migration)
        return self.db.query_one(
            "SELECT * FROM orders WHERE id = %s", (order_id,)
        )
```

### Verification: Shadow Read Comparison

```python
def verify_shadow_consistency(db, sample_size: int = 1000):
    """Compare old and new tables to detect shadow write drift."""
    mismatches = []
    ids = db.query(
        "SELECT id FROM orders ORDER BY RANDOM() LIMIT %s",
        (sample_size,)
    )

    for row in ids:
        old = db.query_one("SELECT * FROM orders WHERE id = %s", (row["id"],))
        new = db.query_one("SELECT * FROM orders_v2 WHERE id = %s", (row["id"],))

        if new is None:
            mismatches.append({"id": row["id"], "type": "missing_in_new"})
        elif int(old["amount"] * 100) != new["amount_cents"]:
            mismatches.append({
                "id": row["id"],
                "type": "amount_mismatch",
                "old": old["amount"],
                "new": new["amount_cents"],
            })

    return mismatches
```

### Cutover

Once the shadow comparison shows 100% consistency over a sustained period:

1. Switch reads to the new table.
2. Keep dual-writes for safety.
3. After a cool-down period, stop writing to the old table.
4. Archive or drop the old table.

---

## Dual-Read Pattern

The inverse of shadow writes: read from both old and new sources, compare, and use
the new source only when it is verified correct.

```python
class UserService:
    """Read from both old and new data source, compare."""

    def __init__(self, old_repo, new_repo, use_new: bool = False):
        self.old_repo = old_repo
        self.new_repo = new_repo
        self.use_new = use_new

    def get_user(self, user_id: int) -> User:
        old_result = self.old_repo.get(user_id)

        if self.use_new:
            new_result = self.new_repo.get(user_id)

            # Compare for correctness monitoring
            if old_result != new_result:
                logger.warning(
                    f"Dual-read mismatch for user {user_id}: "
                    f"old={old_result}, new={new_result}"
                )
                metrics.increment("dual_read.mismatch")
                # Return old until mismatch rate is zero
                return old_result

            return new_result

        return old_result
```

This pattern is useful when migrating complex read paths — analytics queries, search
indexes, denormalized views — where correctness must be verified before cutover.

---

## Blue-Green Database

The blue-green pattern, common for application deployments, can be adapted for databases.
Two complete database environments exist simultaneously; traffic is switched from one
to the other.

### Architecture

```
                    ┌─────────────┐
   Load Balancer ──>│   App (v1)  │──> DB Blue (current)
                    └─────────────┘
                    ┌─────────────┐
   (standby)       │   App (v2)  │──> DB Green (new schema)
                    └─────────────┘
```

### Implementation Steps

1. **Replicate** Blue to Green (physical replication or logical).
2. **Apply migrations** to Green only.
3. **Deploy** App v2 against Green.
4. **Validate** Green with synthetic traffic or a canary.
5. **Switch** the load balancer from Blue to Green.
6. **Keep Blue** alive for rollback.

### Limitations

- Requires double the database infrastructure.
- Data written to Blue after the snapshot is lost unless you use continuous replication.
- Continuous replication + schema changes on Green = complex logical replication setup.
- Not practical for databases > 1TB without significant infrastructure investment.

### When to Use

- Major version upgrades (PostgreSQL 14 to 16).
- Engine migrations (MySQL to PostgreSQL).
- Schema changes so large they cannot be done incrementally.

---

## Strangler Fig for Databases

The strangler fig pattern — from Martin Fowler — replaces a system incrementally rather
than all at once. Applied to databases, it means migrating one table or domain at a time
from the old schema to the new.

### Process

```
Phase 1: Both old and new tables exist
  ┌──────────┐     ┌──────────┐
  │ Old Table │     │ New Table│
  │ (active)  │     │ (empty)  │
  └──────────┘     └──────────┘

Phase 2: Dual-write to both, read from old
  ┌──────────┐     ┌──────────┐
  │ Old Table │<-w->│ New Table│
  │ (read)    │     │ (write)  │
  └──────────┘     └──────────┘

Phase 3: Read from new, dual-write continues
  ┌──────────┐     ┌──────────┐
  │ Old Table │  w->│ New Table│
  │ (write)   │     │ (read)   │
  └──────────┘     └──────────┘

Phase 4: Old table retired
  ┌──────────┐     ┌──────────┐
  │ Old Table │     │ New Table│
  │ (archive) │     │ (active) │
  └──────────┘     └──────────┘
```

### SQL Example: Normalizing a Denormalized Table

```sql
-- Old structure: orders with embedded customer data (denormalized)
-- orders (id, customer_name, customer_email, amount, status)

-- New structure: normalized
-- customers (id, name, email)
-- orders_v2 (id, customer_id, amount, status)

-- Phase 1: Create new tables
CREATE TABLE customers (
    id         BIGSERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    email      VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders_v2 (
    id          BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    amount      NUMERIC(12,2) NOT NULL,
    status      VARCHAR(20) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Phase 2: Backfill customers from orders
INSERT INTO customers (name, email)
SELECT DISTINCT customer_name, customer_email
FROM orders
WHERE customer_email IS NOT NULL
ON CONFLICT (email) DO NOTHING;

-- Phase 3: Backfill orders_v2
INSERT INTO orders_v2 (id, customer_id, amount, status, created_at)
SELECT o.id, c.id, o.amount, o.status, o.created_at
FROM orders o
JOIN customers c ON c.email = o.customer_email;

-- Phase 4: Application code switches to new tables
-- Phase 5: Old table archived and eventually dropped
```

### Key Advantage

Each domain (customers, orders, products) can be migrated independently, on its own
timeline, with its own rollback plan. A failure in migrating orders does not affect
the already-migrated customers table.

---

## Feature Flags for Gradual Migrations

Feature flags allow you to activate new schema behavior progressively, independent of
deployment.

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_feature_flags():
    return {
        "use_display_name": os.getenv("FF_USE_DISPLAY_NAME", "false") == "true",
        "write_to_new_column": os.getenv("FF_WRITE_DISPLAY_NAME", "false") == "true",
    }

class UserRepository:
    def get_user_display(self, user: dict) -> str:
        flags = get_feature_flags()
        if flags["use_display_name"] and user.get("display_name"):
            return user["display_name"]
        return user.get("full_name", "")

    def update_user_name(self, user_id: int, name: str):
        flags = get_feature_flags()
        if flags["write_to_new_column"]:
            # Dual-write during transition
            self.db.execute(
                "UPDATE users SET display_name = %s, full_name = %s "
                "WHERE id = %s",
                (name, name, user_id)
            )
        else:
            self.db.execute(
                "UPDATE users SET full_name = %s WHERE id = %s",
                (name, user_id)
            )
```

### Rollback via Feature Flag

Instead of a database rollback, set `FF_USE_DISPLAY_NAME=false` and
`FF_WRITE_DISPLAY_NAME=false`. The application immediately reverts to the old behavior
without any schema change. The new column remains in place but is unused.

This is called a **soft rollback** — the schema is unchanged, only the code path is
switched. It is dramatically faster and safer than a schema rollback.

### Percentage-Based Rollout

```python
import hashlib

def is_enabled(flag_name: str, user_id: int, percentage: int) -> bool:
    """Deterministic percentage-based flag evaluation."""
    hash_input = f"{flag_name}:{user_id}".encode()
    hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16) % 100
    return hash_value < percentage

# 10% of users get the new behavior
if is_enabled("use_display_name", user.id, percentage=10):
    display = user.display_name
else:
    display = user.full_name
```

---

## Large Table Migrations

Modifying columns or adding indexes on tables with billions of rows is one of the most
challenging operations in production databases.

### ADD COLUMN with DEFAULT

```sql
-- PostgreSQL 11+: ADD COLUMN with non-volatile DEFAULT is O(1)
-- The default is stored in pg_catalog, not materialized in each row.
ALTER TABLE events ADD COLUMN processed BOOLEAN DEFAULT FALSE;
-- Instant, even on a 1B-row table.

-- PostgreSQL < 11: full table rewrite with ACCESS EXCLUSIVE lock.
-- Split into steps:
ALTER TABLE events ADD COLUMN processed BOOLEAN;              -- step 1: nullable
UPDATE events SET processed = FALSE WHERE processed IS NULL;  -- step 2: backfill
ALTER TABLE events ALTER COLUMN processed SET DEFAULT FALSE;  -- step 3: default
ALTER TABLE events ALTER COLUMN processed SET NOT NULL;       -- step 4: constraint

-- MySQL: ADD COLUMN behavior depends on the operation.
-- Many operations support ALGORITHM=INPLACE, LOCK=NONE in MySQL 8.0+:
ALTER TABLE events ADD COLUMN processed BOOLEAN DEFAULT FALSE,
    ALGORITHM=INPLACE, LOCK=NONE;
-- If not supported, use gh-ost or pt-online-schema-change.
```

### Index Creation Without Locks

```sql
-- PostgreSQL: CONCURRENTLY avoids blocking reads and writes.
-- It takes longer (two table scans) and cannot run inside a transaction.
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_events_user_date ON events(user_id, event_date DESC);

-- Monitor progress:
SELECT phase, blocks_done, blocks_total,
       round(blocks_done::numeric / nullif(blocks_total, 0) * 100, 2) AS pct
FROM pg_stat_progress_create_index
WHERE relid = 'events'::regclass;

-- If CONCURRENTLY is interrupted, an INVALID index remains:
SELECT indexname, pg_index.indisvalid
FROM pg_indexes
JOIN pg_class ON pg_class.relname = pg_indexes.indexname
JOIN pg_index ON pg_index.indexrelid = pg_class.oid
WHERE tablename = 'events' AND NOT pg_index.indisvalid;

-- Drop the invalid index and retry:
DROP INDEX CONCURRENTLY IF EXISTS idx_events_user_date;
```

### Progressive Partitioning (Migrating to a Partitioned Table)

```sql
-- Step 1: Create new partitioned table
CREATE TABLE events_partitioned (
    id         BIGSERIAL,
    event_date DATE NOT NULL,
    user_id    BIGINT,
    event      TEXT,
    PRIMARY KEY (id, event_date)
) PARTITION BY RANGE (event_date);

-- Step 2: Create partitions for historical periods
CREATE TABLE events_2024_01 PARTITION OF events_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE events_2024_02 PARTITION OF events_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Step 3: Copy data in batches (without locking the original table)
INSERT INTO events_partitioned (id, event_date, user_id, event)
SELECT id, event_date, user_id, event
FROM events
WHERE event_date >= '2024-01-01' AND event_date < '2024-02-01';

-- Step 4: Application writes to both tables during transition (dual-write)
-- Step 5: Rename and switchover
BEGIN;
  ALTER TABLE events RENAME TO events_old;
  ALTER TABLE events_partitioned RENAME TO events;
COMMIT;

-- Step 6: Drop old table after verification period
```

---

## Online Schema Change Tools for MySQL

MySQL lacks PostgreSQL's transactional DDL and many of its online DDL capabilities.
Tools like **gh-ost** and **pt-online-schema-change** fill this gap.

### gh-ost (GitHub Online Schema Transmogrifier)

```bash
gh-ost \
    --user="root" \
    --password="secret" \
    --host="mysql-master:3306" \
    --database="myapp" \
    --table="users" \
    --alter="ADD COLUMN display_name VARCHAR(255) NULL AFTER full_name" \
    --chunk-size=1000 \
    --max-load="Threads_running=25" \
    --critical-load="Threads_running=50" \
    --ok-to-drop-table \
    --initially-drop-ghost-table \
    --execute
```

**How gh-ost works**:

1. Creates a ghost table (`_users_gho`) with the new schema.
2. Copies data from the original table to the ghost in chunks.
3. Reads the MySQL binary log to capture writes that happen during the copy.
4. Applies those writes to the ghost table in real-time.
5. Performs a rapid atomic rename: `users` becomes `_users_del`, `_users_gho` becomes `users`.

**Advantages over pt-online-schema-change**:
- Does not use triggers (triggers cause contention on high-write tables).
- Reads from the binary log instead, which is asynchronous.
- Can be paused, throttled, and resumed.
- Supports postponing or canceling the cutover.

### pt-online-schema-change (Percona Toolkit)

```bash
pt-online-schema-change \
    --alter "ADD COLUMN display_name VARCHAR(255) NULL" \
    --host=mysql-master \
    --user=root \
    --password=secret \
    D=myapp,t=users \
    --chunk-size=1000 \
    --max-lag=5 \
    --check-interval=1 \
    --execute
```

**How pt-osc works**:

1. Creates a shadow table with the new schema.
2. Installs three triggers (INSERT, UPDATE, DELETE) on the original table.
3. Copies data in chunks.
4. Triggers propagate ongoing writes to the shadow table.
5. Atomic rename at the end.

**Disadvantage**: triggers add overhead to every write during the migration. On
high-write tables (>1K writes/sec), this can cause noticeable latency increase.

### pg_repack for PostgreSQL

pg_repack reorganizes tables and indexes without holding exclusive locks for extended
periods. Useful for:

- Removing bloat after large deletes.
- Reordering rows by a specific column (CLUSTER without locking).
- Rebuilding indexes.

```bash
# Install the extension
CREATE EXTENSION pg_repack;

# Repack a specific table (removes bloat)
pg_repack --no-superuser-check -d mydb -t events

# Repack all tables in a database
pg_repack --no-superuser-check -d mydb

# Reorder rows by a specific index
pg_repack --no-superuser-check -d mydb -t events -o event_date
```

---

## Cross-Database Migration

When migrating from one database engine to another (MySQL to PostgreSQL, Oracle to PostgreSQL).

### Type Mapping

| MySQL | PostgreSQL | Notes |
|-------|-----------|-------|
| `TINYINT(1)` | `BOOLEAN` | MySQL uses TINYINT as boolean |
| `INT AUTO_INCREMENT` | `SERIAL` or `GENERATED ALWAYS AS IDENTITY` | |
| `DATETIME` | `TIMESTAMP` | No timezone in MySQL DATETIME |
| `ENUM('a','b','c')` | `VARCHAR(N) + CHECK` or `CREATE TYPE` | PG enums are types |
| `TEXT` | `TEXT` | Same |
| `BLOB` | `BYTEA` | Different encoding |
| `DOUBLE` | `DOUBLE PRECISION` | Same underlying IEEE 754 |
| `JSON` | `JSONB` | PG JSONB is binary, indexable |

### Migration Script

```python
import sqlalchemy as sa
from sqlalchemy import MetaData

def migrate_mysql_to_postgres(source_url: str, target_url: str):
    source_engine = sa.create_engine(source_url)
    target_engine = sa.create_engine(target_url)

    source_meta = MetaData()
    source_meta.reflect(bind=source_engine)

    # Phase 1: Create schema with type adaptations
    for table_name, table in source_meta.tables.items():
        adapted_columns = []
        for col in table.columns:
            adapted_type = adapt_mysql_type(col.type)
            adapted_columns.append(
                sa.Column(col.name, adapted_type, nullable=col.nullable)
            )
        new_table = sa.Table(table_name, MetaData(), *adapted_columns)
        new_table.create(target_engine, checkfirst=True)

    # Phase 2: Copy data in chunks
    chunk_size = 10000
    for table_name in source_meta.tables:
        offset = 0
        while True:
            with source_engine.connect() as src:
                rows = src.execute(
                    sa.text(f"SELECT * FROM {table_name} "
                            f"LIMIT {chunk_size} OFFSET {offset}")
                ).mappings().all()
            if not rows:
                break
            with target_engine.begin() as tgt:
                tgt.execute(
                    sa.insert(sa.table(table_name)),
                    [dict(r) for r in rows]
                )
            offset += chunk_size

def adapt_mysql_type(mysql_type):
    """Map MySQL types to PostgreSQL equivalents."""
    type_str = str(mysql_type)
    if 'TINYINT' in type_str and '(1)' in type_str:
        return sa.Boolean()
    if 'DATETIME' in type_str:
        return sa.DateTime(timezone=True)
    if 'BLOB' in type_str:
        return sa.LargeBinary()
    return mysql_type
```

---

## Strategy Selection Matrix

| Change Type | Small Table (<1M) | Medium (1M-100M) | Large (>100M) |
|-------------|-------------------|-------------------|---------------|
| Add nullable column | Direct ALTER | Direct ALTER | Direct ALTER (PG 11+: instant) |
| Add column with DEFAULT | Direct ALTER | Direct ALTER | Direct ALTER (PG 11+), gh-ost (MySQL) |
| Add NOT NULL constraint | Direct ALTER | Expand-contract | Expand-contract + batched backfill |
| Drop column | Direct ALTER | Expand-contract | Expand-contract (2 deploy cycles) |
| Rename column | Direct ALTER | Expand-contract | Expand-contract (3+ deploy cycles) |
| Change column type | Direct ALTER | Expand-contract | Expand-contract + shadow column |
| Add index | Direct CREATE | CONCURRENTLY (PG) | CONCURRENTLY (PG), gh-ost (MySQL) |
| Add foreign key | Direct ALTER | NOT VALID + VALIDATE | NOT VALID + VALIDATE (PG) |
| Table restructure | Direct ALTER | Strangler fig | Strangler fig + shadow writes |
| Engine migration | Blue-green | Blue-green + CDC | Blue-green + CDC + shadow reads |

---

## Real-World Scenarios

### Scenario 1: E-Commerce Platform Column Rename at Scale

A 200M-row `products` table needs to rename `price` to `price_cents` and change
from `DECIMAL(10,2)` to `BIGINT`. The platform handles 5K writes/sec during peak hours.

**Strategy**: Expand-and-contract with shadow writes.

```
Timeline:
  Day 1: V30 — ADD COLUMN price_cents BIGINT + sync trigger
  Day 1: Deploy app v2 — dual-write (price + price_cents)
  Day 1-3: V31 — batched backfill (price_cents = price * 100)
  Day 4: Deploy app v3 — read from price_cents, still dual-write
  Day 5: Run reconciliation (compare price * 100 vs price_cents)
  Day 7: Deploy app v4 — stop writing to price
  Day 8: V32 — DROP COLUMN price, DROP trigger
```

### Scenario 2: Emergency Migration After Security Incident

A security audit reveals that PII (email addresses) is stored unencrypted. The migration
must encrypt the email column in-place, on a 50M-row `users` table, without downtime.

**Strategy**: Expand-and-contract with encrypted shadow column.

```sql
-- V40: Add encrypted column
ALTER TABLE users ADD COLUMN email_encrypted BYTEA;

-- V41: Backfill (application-level encryption, not in SQL)
-- Run as a batch job:
-- for each user in batches:
--   encrypted = encrypt(user.email, key)
--   UPDATE users SET email_encrypted = $1 WHERE id = $2

-- V42: After backfill and code switch, drop plaintext column
ALTER TABLE users DROP COLUMN email;
ALTER TABLE users RENAME COLUMN email_encrypted TO email;
```

### Scenario 3: Sharding Preparation

A monolithic PostgreSQL database needs to be prepared for sharding. The first step is
adding a `shard_key` column to all tables and backfilling it.

**Strategy**: Expand-and-contract across all tables, sequentially.

```sql
-- Migration per table (repeated for each table):
ALTER TABLE orders ADD COLUMN shard_key INT;
-- Backfill: shard_key = user_id % num_shards
UPDATE orders SET shard_key = user_id % 16
WHERE shard_key IS NULL;
-- After backfill:
ALTER TABLE orders ALTER COLUMN shard_key SET NOT NULL;
CREATE INDEX CONCURRENTLY idx_orders_shard ON orders(shard_key);
```

---

## Troubleshooting

### 1. Backfill causes replication lag

**Cause**: Unbatched UPDATE generates massive WAL.

**Fix**: Reduce batch size, increase sleep between batches:

```sql
-- Monitor lag during backfill
SELECT application_name,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS bytes_behind,
       replay_lag
FROM pg_stat_replication;
```

### 2. gh-ost fails with "table already exists"

**Cause**: Previous run interrupted without cleanup.

**Fix**: Use `--initially-drop-ghost-table`, or manual cleanup:

```sql
DROP TABLE IF EXISTS myapp._users_gho;
DROP TABLE IF EXISTS myapp._users_ghc;
DROP TABLE IF EXISTS myapp._users_del;
```

### 3. Orphaned sync trigger after contract phase skipped

**Fix**: List and drop orphaned triggers:

```sql
SELECT trigger_name, event_object_table
FROM information_schema.triggers
WHERE trigger_schema = 'public' AND trigger_name LIKE 'trg_sync_%';
-- DROP TRIGGER IF EXISTS trg_sync_display_name ON users;
```

### 4. Dual-write data inconsistency

**Cause**: Shadow write failed silently or writes arrived out of order.

**Fix**: Run reconciliation:

```sql
SELECT o.id FROM orders o
LEFT JOIN orders_v2 n ON n.id = o.id
WHERE n.id IS NULL;
```

### 5. Feature flag rollback fails

**Cause**: Data written in new format, old code cannot read it.

**Fix**: Always dual-write in both old and new format during migration.

### 6. CONCURRENTLY leaves INVALID index

**Fix**: Drop and retry:
```sql
DROP INDEX CONCURRENTLY IF EXISTS idx_events_user_date;
CREATE INDEX CONCURRENTLY IF NOT EXISTS
    idx_events_user_date ON events(user_id, event_date DESC);
```

### 7. Partitioning cutover causes brief outage

**Cause**: RENAME TABLE takes an ACCESS EXCLUSIVE lock, which queues behind active
transactions.

**Fix**: Set `lock_timeout = '3s'` and retry during a low-traffic window:

```sql
SET lock_timeout = '3s';
BEGIN;
  ALTER TABLE events RENAME TO events_old;
  ALTER TABLE events_partitioned RENAME TO events;
COMMIT;
-- If this times out, retry in the next low-traffic window.
```

---

## Frequently Asked Questions

### 1. When should I use expand-and-contract vs direct ALTER?

If the change is additive (new column, new table) and does not modify or remove existing
structures, a direct ALTER is safe. If the change modifies or removes something the current
code depends on, use expand-and-contract.

### 2. How long should the dual-write phase last?

At minimum: until all application instances are on the new version. Add 1-2 weeks for
monitoring and rollback safety.

### 3. Can gh-ost read from a replica instead of the primary?

Yes. Use `--migrate-on-replica` to read the binary log from a replica, reducing primary
load.

### 4. What if the backfill takes longer than the maintenance window?

Run it as a separate, resumable batch job. Use a marker column (`backfill_done BOOLEAN`)
to track progress. The backfill does not require downtime.

### 5. How do I handle FK constraints during expand-and-contract?

Add the FK with `NOT VALID`, then `VALIDATE CONSTRAINT` after backfill:

```sql
ALTER TABLE orders ADD CONSTRAINT fk_orders_customer
    FOREIGN KEY (customer_id_new) REFERENCES customers(id) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_customer;
```

### 6. What is the difference between gh-ost and pt-online-schema-change?

gh-ost reads the binary log (no triggers, lower overhead). pt-osc uses triggers
(simpler setup, higher write overhead). Prefer gh-ost for high-write tables.

### 7. Can I combine multiple strategies in one migration project?

Yes. A large engine migration might use blue-green for the infrastructure, strangler fig
for individual tables, expand-and-contract for column-level changes, and feature flags
for application-level rollback. Strategies are composable.

---

## Exercises

### Exercise 1 (Beginner): Identify the Strategy

For each scenario, name the appropriate migration strategy:

1. Adding a `bio TEXT` column to a 100-row table.
2. Renaming `email_address` to `email` on a 50M-row table, 99.99% uptime SLA.
3. Migrating from MySQL to PostgreSQL (200 tables).
4. Splitting a denormalized `orders` table into `orders` + `order_items`.
5. Adding an index to a 500M-row table on PostgreSQL.

### Exercise 2 (Intermediate): Expand-and-Contract Plan

Change `price` from `DECIMAL(10,2)` to `BIGINT` (cents) on a 20M-row `products` table.
Write: expand migration, sync trigger, batched backfill, contract migration, and
application code changes at each phase.

### Exercise 3 (Intermediate): Shadow Write Design

Design shadow writes for migrating from `legacy_users` (id, full_name, email, phone,
address) to `users_v2` (id, first_name, last_name, email, phone_e164, address_json).
Include: shadow write function, reconciliation query, cutover plan.

### Exercise 4 (Advanced): gh-ost Deployment Script

Write a production script that: validates table size and replication lag, runs gh-ost
with throttling, monitors progress, pauses on lag threshold, sends alerts, cleans up.

### Exercise 5 (Advanced): Multi-Table Strangler Fig

Plan a strangler fig migration for: `users` (50M), `orders` (200M), `products` (500K),
`order_items` (800M), `audit_log` (2B). Define: order, dependencies, dual-write,
cutover sequence, rollback per table.

---

## Key Takeaways

1. **Expand-and-contract is the default strategy** for any non-additive schema change in a
   zero-downtime environment.
2. **Shadow writes** verify correctness before cutover. Never cut over without them.
3. **Feature flags** make rollback instant — flip a flag instead of rolling back schema.
4. **Batch everything** on large tables. Unbatched DML is the number one cause of migration
   incidents.
5. **Online DDL tools** (gh-ost, pt-osc) are essential for MySQL. PostgreSQL has most
   capabilities built in.
6. **Strategy depends on table size**, not change complexity. A simple column rename on a
   1B-row table is harder than a full restructure on a 1K-row table.

The right migration strategy turns a high-risk database change into a routine deployment.
