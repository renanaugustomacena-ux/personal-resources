# Database Migrations — Migrazione dei Dati

## DDL vs DML Migrations

Le **schema migrations** (DDL) cambiano la struttura — tabelle, colonne, indici. Le **data migrations** (DML) trasformano i dati: backfill di nuove colonne, normalizzazione di strutture, de-duplicazione, trasformazione di formati.

La differenza pratica è che le data migrations:
- Possono essere **molto più lente** (devono processare ogni riga)
- Creano **maggior pressione sull'I/O** e sulle repliche (replication lag)
- Hanno **semantica di rollback diversa** (i dati vecchi potrebbero non essere recuperabili)
- Richiedono **strategie di batching** per evitare lock e timeout

---

## Backfill di Nuove Colonne

### Backfill Naïve (da non usare in produzione)

```sql
-- SBAGLIATO su tabelle grandi: un unico UPDATE lockante
UPDATE users SET display_name = full_name;
-- Su 10M righe: potenziale lock di minuti, replication lag enorme
```

### Backfill a Batch con Cursor

```sql
-- PostgreSQL: backfill in batch usando un cursore dichiarativo
DO $$
DECLARE
    batch_size INT := 5000;
    last_id BIGINT := 0;
    max_id BIGINT;
    rows_updated INT;
BEGIN
    SELECT COALESCE(MAX(id), 0) INTO max_id FROM users;
    RAISE NOTICE 'Processing % rows total', max_id;

    LOOP
        UPDATE users
        SET display_name = full_name
        WHERE id > last_id
          AND id <= last_id + batch_size
          AND display_name IS NULL;

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        last_id := last_id + batch_size;

        RAISE NOTICE 'Processed up to id %, % rows updated', last_id, rows_updated;

        -- Pausa per ridurre replication lag
        PERFORM pg_sleep(0.05);

        EXIT WHEN last_id >= max_id;
    END LOOP;

    RAISE NOTICE 'Backfill completed';
END;
$$;
```

### Backfill da Python con apoc.periodic.iterate

```python
import psycopg2
import time
from tqdm import tqdm

def backfill_display_name(conn_string: str, batch_size: int = 10000) -> int:
    """Backfill display_name from full_name in batches."""
    conn = psycopg2.connect(conn_string)
    total_updated = 0

    with conn.cursor() as cur:
        cur.execute("SELECT MIN(id), MAX(id) FROM users WHERE display_name IS NULL")
        min_id, max_id = cur.fetchone()

    if min_id is None:
        print("No rows to backfill")
        return 0

    with tqdm(total=max_id - min_id, desc="Backfill display_name") as pbar:
        last_id = min_id - 1
        while last_id < max_id:
            with conn:  # autocommit per batch
                with conn.cursor() as cur:
                    cur.execute("""
                        WITH batch AS (
                            SELECT id FROM users
                            WHERE id > %s
                              AND id <= %s
                              AND display_name IS NULL
                        )
                        UPDATE users u
                        SET display_name = u.full_name
                        FROM batch
                        WHERE u.id = batch.id
                    """, (last_id, last_id + batch_size))

                    total_updated += cur.rowcount

            last_id += batch_size
            pbar.update(batch_size)
            time.sleep(0.05)  # reduce replication lag

    conn.close()
    print(f"Backfill complete: {total_updated} rows updated")
    return total_updated
```

---

## Normalizzazione: Spostamento Dati tra Tabelle

```sql
-- Scenario: normalizza colonne JSON in tabella relazionale separata

-- Struttura originale:
-- orders (id, user_id, items_json TEXT)
-- items_json: '[{"sku": "ABC", "qty": 2, "price": 50.00}, ...]'

-- Struttura target:
-- order_items (id, order_id, sku, quantity, unit_price)

-- Migrazione V20__normalize_order_items.sql
CREATE TABLE IF NOT EXISTS order_items (
    id         BIGSERIAL PRIMARY KEY,
    order_id   BIGINT NOT NULL REFERENCES orders(id),
    sku        VARCHAR(100) NOT NULL,
    quantity   INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    migrated   BOOLEAN DEFAULT FALSE  -- flag per idempotenza
);

-- Estrai e inserisci con jsonb_array_elements
INSERT INTO order_items (order_id, sku, quantity, unit_price)
SELECT
    o.id as order_id,
    item->>'sku' as sku,
    (item->>'qty')::int as quantity,
    (item->>'price')::decimal(10,2) as unit_price
FROM orders o
CROSS JOIN jsonb_array_elements(o.items_json::jsonb) AS item
WHERE NOT EXISTS (
    SELECT 1 FROM order_items oi WHERE oi.order_id = o.id
)
  AND o.items_json IS NOT NULL
  AND o.items_json != '[]';
```

---

## De-duplicazione

```sql
-- Rimuove duplicati mantenendo il record più recente per email
WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at DESC) AS rn
    FROM users
),
duplicates AS (
    SELECT id FROM ranked WHERE rn > 1
)
DELETE FROM users
WHERE id IN (SELECT id FROM duplicates);

-- Con backup prima del delete
CREATE TABLE users_dedup_backup AS
SELECT * FROM users
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at DESC) AS rn
        FROM users
    ) ranked WHERE rn > 1
);

-- Poi il delete
DELETE FROM users WHERE id IN (SELECT id FROM users_dedup_backup);
```

---

## Migrazione Inter-Database (ETL come Migration)

Quando si migra da un database legacy a uno nuovo:

```python
import sqlalchemy as sa
import pandas as pd
from typing import Iterator
import logging

logger = logging.getLogger(__name__)

def migrate_table(
    source_engine: sa.Engine,
    target_engine: sa.Engine,
    source_query: str,
    target_table: str,
    transform_fn=None,
    chunk_size: int = 10000
) -> int:
    """Migra dati da sorgente a destinazione con trasformazione opzionale."""

    total_rows = 0

    with source_engine.connect() as src:
        # Conta le righe per la progress bar
        count_query = f"SELECT COUNT(*) FROM ({source_query}) sub"
        total = src.execute(sa.text(count_query)).scalar()
        logger.info(f"Migrating {total} rows from {source_query[:50]}...")

        # Legge a chunk
        reader = pd.read_sql(source_query, src, chunksize=chunk_size)
        for i, chunk in enumerate(reader):
            if transform_fn:
                chunk = transform_fn(chunk)

            # Scrive nel target
            with target_engine.begin() as tgt:
                chunk.to_sql(
                    target_table,
                    tgt,
                    if_exists="append",
                    index=False,
                    method="multi"
                )

            total_rows += len(chunk)
            logger.info(f"  Migrated batch {i+1}: {total_rows}/{total} rows")

    return total_rows


# Utilizzo con trasformazione
def transform_users(df: pd.DataFrame) -> pd.DataFrame:
    # Rinomina colonne
    df = df.rename(columns={"full_name": "display_name", "phone_number": "phone"})
    # Normalizza email
    df["email"] = df["email"].str.lower().str.strip()
    # Gestisci NULL
    df["display_name"] = df["display_name"].fillna("Unknown")
    return df

source = sa.create_engine("mysql://user:pass@old-db/legacy")
target = sa.create_engine("postgresql://user:pass@new-db/production")

rows = migrate_table(
    source,
    target,
    "SELECT id, full_name, email, phone_number, created_at FROM users",
    "users",
    transform_fn=transform_users,
    chunk_size=50_000
)
print(f"Migration complete: {rows} rows migrated")
```

---

## Verifica dell'Integrità Post-Migrazione

```sql
-- Reconciliazione: verifica che il count sia uguale
SELECT
    (SELECT count(*) FROM source_db.users) as source_count,
    (SELECT count(*) FROM users) as target_count,
    (SELECT count(*) FROM source_db.users) =
    (SELECT count(*) FROM users) as counts_match;

-- Checksum di tutti i valori (campione statistico per tabelle enormi)
SELECT
    count(*) as rows,
    sum(hashtext(email)) as email_checksum,
    sum(hashtext(display_name)) as name_checksum,
    max(created_at) as latest_record
FROM users;

-- Cross-check specifico
SELECT u1.id, u1.email, u2.email
FROM source_db.users u1
FULL OUTER JOIN users u2 ON u1.id = u2.id
WHERE u1.email <> u2.email OR u1.id IS NULL OR u2.id IS NULL
LIMIT 100;
```

Le data migrations richiedono pianificazione più attenta delle schema migrations per via della mole di dati e dei potenziali effetti sulle repliche e sui lock. Il pattern backfill-in-batch è la soluzione universale per evitare problemi di performance in produzione.

---

## Adaptive Throttling for Backfills

### Replication-Lag-Aware Backfill

The most production-safe approach monitors replication lag and automatically throttles:

```python
import psycopg2
import time
import logging

logger = logging.getLogger(__name__)

class AdaptiveBackfill:
    """Backfill that adapts speed based on replication lag."""

    def __init__(
        self,
        primary_dsn: str,
        batch_size: int = 5000,
        max_lag_seconds: float = 5.0,
        min_sleep: float = 0.01,
        max_sleep: float = 10.0,
    ):
        self.primary_dsn = primary_dsn
        self.batch_size = batch_size
        self.max_lag = max_lag_seconds
        self.min_sleep = min_sleep
        self.max_sleep = max_sleep

    def get_replication_lag(self, conn) -> float:
        """Get maximum replication lag across all replicas."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(
                    MAX(EXTRACT(EPOCH FROM replay_lag)), 0
                ) FROM pg_stat_replication
            """)
            return cur.fetchone()[0]

    def run(self, table: str, set_clause: str, where_clause: str):
        conn = psycopg2.connect(self.primary_dsn)
        conn.autocommit = True
        sleep_time = self.min_sleep
        total_updated = 0

        with conn.cursor() as cur:
            cur.execute(f"SELECT MIN(id), MAX(id) FROM {table} WHERE {where_clause}")
            min_id, max_id = cur.fetchone()

        if min_id is None:
            logger.info("No rows to backfill")
            return 0

        last_id = min_id - 1
        while last_id < max_id:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE {table} SET {set_clause}
                    WHERE id > %s AND id <= %s AND {where_clause}
                """, (last_id, last_id + self.batch_size))
                rows = cur.rowcount
                total_updated += rows

            last_id += self.batch_size

            # Check lag and adapt
            lag = self.get_replication_lag(conn)
            if lag > self.max_lag:
                sleep_time = min(sleep_time * 2, self.max_sleep)
                logger.warning(
                    f"Lag {lag:.1f}s > {self.max_lag}s, "
                    f"slowing to {sleep_time:.2f}s sleep"
                )
            elif lag < self.max_lag / 2:
                sleep_time = max(sleep_time / 2, self.min_sleep)

            if total_updated % 100000 == 0:
                logger.info(
                    f"Progress: {total_updated} rows updated, "
                    f"lag: {lag:.1f}s, sleep: {sleep_time:.2f}s"
                )

            time.sleep(sleep_time)

        conn.close()
        logger.info(f"Backfill complete: {total_updated} rows")
        return total_updated


# Usage
backfill = AdaptiveBackfill(
    primary_dsn="host=primary dbname=myapp user=migrator",
    batch_size=10000,
    max_lag_seconds=3.0,
)
backfill.run(
    table="users",
    set_clause="display_name = full_name",
    where_clause="display_name IS NULL",
)
```

---

## Data Transformation Patterns

### Column Split

```sql
-- Split "address" into "street", "city", "state", "zip"
-- Phase 1: Add new columns
ALTER TABLE customers ADD COLUMN street TEXT;
ALTER TABLE customers ADD COLUMN city VARCHAR(100);
ALTER TABLE customers ADD COLUMN state VARCHAR(2);
ALTER TABLE customers ADD COLUMN zip VARCHAR(10);

-- Phase 2: Parse and backfill
-- Assuming address format: "123 Main St, Springfield, IL 62701"
UPDATE customers
SET
    street = split_part(address, ',', 1),
    city = trim(split_part(split_part(address, ',', 2), ',', 1)),
    state = trim(split_part(split_part(address, ',', 3), ' ', 1)),
    zip = trim(split_part(split_part(address, ',', 3), ' ', 2))
WHERE address IS NOT NULL AND street IS NULL;
```

### Format Conversion

```sql
-- Convert phone numbers from various formats to E.164
-- "555-1234" → "+15551234"
-- "(555) 123-4567" → "+15551234567"
-- "1-555-123-4567" → "+15551234567"

UPDATE customers
SET phone_e164 = '+1' || regexp_replace(phone, '[^0-9]', '', 'g')
WHERE phone IS NOT NULL
  AND phone_e164 IS NULL
  AND length(regexp_replace(phone, '[^0-9]', '', 'g')) IN (7, 10, 11);
```

### Currency Conversion (Dollars to Cents)

```sql
-- Phase 1: Add cents column
ALTER TABLE orders ADD COLUMN amount_cents BIGINT;

-- Phase 2: Backfill
UPDATE orders
SET amount_cents = (amount * 100)::bigint
WHERE amount_cents IS NULL AND amount IS NOT NULL;

-- Phase 3: Verify precision
SELECT count(*)
FROM orders
WHERE amount_cents IS NOT NULL
  AND abs(amount_cents - amount * 100) > 0;
-- Expected: 0 rows (no precision loss)

-- Phase 4: Contract (after code migration)
ALTER TABLE orders DROP COLUMN amount;
ALTER TABLE orders RENAME COLUMN amount_cents TO amount;
```

### JSON Schema Evolution

```sql
-- Evolve JSONB column from v1 to v2 schema
-- v1: {"name": "John", "addr": "123 Main"}
-- v2: {"name": "John", "address": {"street": "123 Main", "city": null}}

UPDATE customers
SET profile = jsonb_set(
    jsonb_set(
        profile - 'addr',
        '{address}',
        jsonb_build_object(
            'street', profile->>'addr',
            'city', null
        )
    ),
    '{schema_version}',
    '"2"'
)
WHERE profile->>'addr' IS NOT NULL
  AND profile->'address' IS NULL;
```

---

## Large-Scale Data Migration Orchestration

For tables with billions of rows, a migration may take days. Use a job-based approach:

```python
import psycopg2
import time
from datetime import datetime, timezone

class MigrationJob:
    """Persistent, resumable data migration job."""

    def __init__(self, dsn: str, job_name: str):
        self.dsn = dsn
        self.job_name = job_name

    def init_tracking(self):
        """Create tracking table if not exists."""
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS _migration_jobs (
                    job_name     VARCHAR(100) PRIMARY KEY,
                    last_id      BIGINT DEFAULT 0,
                    total_rows   BIGINT DEFAULT 0,
                    started_at   TIMESTAMPTZ DEFAULT now(),
                    updated_at   TIMESTAMPTZ DEFAULT now(),
                    completed_at TIMESTAMPTZ,
                    status       VARCHAR(20) DEFAULT 'running'
                )
            """)
            cur.execute("""
                INSERT INTO _migration_jobs (job_name)
                VALUES (%s)
                ON CONFLICT (job_name) DO NOTHING
            """, (self.job_name,))
        conn.close()

    def get_checkpoint(self) -> int:
        """Resume from last successful batch."""
        conn = psycopg2.connect(self.dsn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT last_id FROM _migration_jobs WHERE job_name = %s",
                (self.job_name,)
            )
            row = cur.fetchone()
        conn.close()
        return row[0] if row else 0

    def save_checkpoint(self, last_id: int, total_rows: int):
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE _migration_jobs
                SET last_id = %s, total_rows = %s, updated_at = now()
                WHERE job_name = %s
            """, (last_id, total_rows, self.job_name))
        conn.close()

    def mark_complete(self, total_rows: int):
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE _migration_jobs
                SET status = 'completed', completed_at = now(), total_rows = %s
                WHERE job_name = %s
            """, (total_rows, self.job_name))
        conn.close()
```

---

## Troubleshooting

### 1. Backfill Causes OOM on the Database Server

**Symptom**: PostgreSQL runs out of memory during a large UPDATE statement.

**Cause**: A single UPDATE touching millions of rows creates a massive transaction that cannot fit in `shared_buffers` and `work_mem`.

**Fix**: Use batched updates with explicit transaction boundaries per batch. Each batch commits independently, releasing memory.

### 2. JSON Parsing Fails on Malformed Data

**Symptom**: `ERROR: invalid input syntax for type json` during a JSONB migration.

**Cause**: Some rows contain malformed JSON (truncated, invalid characters, or empty strings instead of NULL).

**Fix**: Filter out bad data first: `WHERE items_json IS NOT NULL AND items_json != '' AND items_json::jsonb IS NOT NULL`. Or use a TRY/CATCH pattern in PL/pgSQL to skip bad rows and log them.

### 3. De-duplication Deletes Wrong Records

**Symptom**: After de-duplication, the wrong version of a record is kept (older instead of newer, or vice versa).

**Cause**: The `ORDER BY` in the window function does not match the business definition of "correct" record.

**Fix**: Verify the ranking criteria with the business team. Always create a backup table before deleting. Validate the de-duplication result before committing.

### 4. Cross-Database Migration Has Character Encoding Issues

**Symptom**: Non-ASCII characters (accents, CJK, emoji) are corrupted after migration from MySQL to PostgreSQL.

**Cause**: MySQL's `utf8` is actually `utf8mb3` (3-byte UTF-8, no emoji support). PostgreSQL uses full UTF-8.

**Fix**: Ensure the source query uses `CONVERT(column USING utf8mb4)` for MySQL. Verify target PostgreSQL encoding is `UTF8`. Test with a sample of non-ASCII data before full migration.

### 5. Backfill Takes Longer Than Expected

**Symptom**: Estimated 2-hour backfill takes 12+ hours.

**Cause**: Index maintenance on the updated columns, trigger overhead, or autovacuum competing for I/O.

**Fix**: Temporarily drop non-essential indexes on the target column, re-create them after backfill. Disable triggers if they are not needed during backfill. Tune `autovacuum_naptime` and `maintenance_work_mem`.

### 6. Integrity Verification Shows Mismatched Counts

**Symptom**: Source has 10M rows but target has 9,998,450 after migration.

**Cause**: Rows with NULL primary keys, duplicate keys that violate unique constraints, or rows skipped by the WHERE clause in the migration query.

**Fix**: Identify missing rows: `SELECT id FROM source EXCEPT SELECT id FROM target`. Check for constraint violations in the migration log. Re-migrate the missing rows.

### 7. Data Migration Causes Disk Space Exhaustion

**Symptom**: Database runs out of disk during a large INSERT INTO ... SELECT operation.

**Cause**: The INSERT creates new rows (doubling data), plus WAL logs, plus the old rows are not yet vacuumed.

**Fix**: Monitor disk usage during migration. Use smaller batches with VACUUM between them. Estimate required space: at least 2x the table size for a full copy + WAL.

### 8. Foreign Key Violations During Normalization

**Symptom**: `ERROR: insert or update on table "order_items" violates foreign key constraint` during data normalization.

**Cause**: Some `order_id` values in the JSON data reference orders that have been deleted or do not exist.

**Fix**: Clean up orphan references before the FK constraint is applied: `DELETE FROM order_items WHERE order_id NOT IN (SELECT id FROM orders)`. Or add the FK as `NOT VALID` first and clean up afterward.

### 9. Pandas to_sql is Extremely Slow

**Symptom**: `chunk.to_sql()` takes minutes per batch of 10K rows.

**Cause**: Default pandas `to_sql` uses individual INSERT statements. Without `method="multi"` or a COPY-based approach, it is prohibitively slow.

**Fix**: Use `method="multi"` for batch INSERTs. For maximum performance, use `COPY` directly via psycopg2: `copy_from(StringIO(csv_data), table)`. Or use `pgloader` for bulk transfers.

### 10. Backfill Interferes with Application Queries

**Symptom**: Application response time degrades during backfill. Users see timeouts.

**Cause**: Backfill batches hold row-level locks that conflict with application queries on the same rows.

**Fix**: Run backfill during off-peak hours. Reduce batch size. Add `SKIP LOCKED` if applicable. Monitor `pg_stat_activity` for lock contention during backfill.

---

## FAQ

### 1. Should data migrations live in the same migration files as schema migrations?

No. Separate them. Schema migrations are fast and safe (DDL). Data migrations are slow and risky (DML). Keeping them separate allows independent execution, different timeout settings, and clear rollback semantics.

### 2. How do I handle data migration rollback for destructive transformations?

Always create a backup table before the transformation: `CREATE TABLE _backup_original AS SELECT * FROM target WHERE condition`. On rollback, restore from the backup. Set a retention policy (e.g., keep backup for 30 days).

### 3. What batch size should I use for backfills?

Start with 5,000-10,000 rows per batch. Monitor replication lag and I/O. If lag stays under 2 seconds, increase the batch size. If lag spikes, reduce it. The optimal size depends on row width, index count, and hardware.

### 4. How do I backfill a column with data from another service?

Use an external backfill script (Python, Go) that queries the external service and updates the database in batches. Never call external services from within a SQL migration — it creates a dependency that makes the migration non-reproducible.

### 5. Can I use COPY instead of INSERT for large data migrations?

Yes, and you should. PostgreSQL COPY is 5-10x faster than batched INSERTs for bulk loading. Export source data to CSV, transfer the file, and use `COPY target_table FROM '/path/to/file.csv' WITH CSV HEADER`. For cross-database migrations, use `pg_dump | psql` or `pgloader`.

### 6. How do I verify data integrity after migrating between database engines?

Compare checksums at multiple levels: row counts per table, column-level checksums (`SUM(hashtext(column))`), and spot-check random samples. Use a reconciliation script that runs after migration and reports discrepancies.

### 7. Should data migrations be idempotent?

Absolutely. A data migration may need to be re-run after a partial failure. Use WHERE clauses that skip already-migrated rows: `WHERE new_column IS NULL` or `WHERE NOT EXISTS (SELECT 1 FROM target WHERE target.id = source.id)`.

### 8. How do I estimate the duration of a data migration?

Run the migration on a staging database with production-scale data. Measure time per batch and extrapolate. Account for 1.5x-2x overhead in production due to concurrent traffic. For cross-database migrations, measure network transfer time separately.

### 9. What is the safest way to delete large amounts of data?

Delete in batches with explicit limits: `DELETE FROM old_data WHERE created_at < '2020-01-01' LIMIT 10000`. Commit after each batch. Monitor disk space and replication lag. Consider partitioning followed by `DROP TABLE` of old partitions for massive deletes.

### 10. How do I handle data migrations in a multi-tenant system?

Migrate tenant by tenant, not all at once. This limits blast radius: if one tenant's migration fails, others are unaffected. Use a tracking table per tenant to record progress. Parallelize across tenants for speed but throttle to avoid saturating the database.

### 11. How do I handle NULL values during data type conversion?

Define a default for NULLs explicitly. For example, when converting a nullable `VARCHAR` amount to a `DECIMAL`, decide whether NULL means 0.00 or should remain NULL. Document the business rule. Never let implicit conversions handle NULLs silently.

### 12. What is the best tool for cross-database data migration?

For one-time bulk transfers, `pgloader` (MySQL/SQLite to PostgreSQL) or `ora2pg` (Oracle to PostgreSQL) are purpose-built and handle type mapping automatically. For ongoing synchronization, use CDC tools (Debezium, Maxwell, AWS DMS). For custom transformations, write a Python/Go script with batch processing.

---

## Data Migration Monitoring Dashboard

Key metrics to track during a running data migration:

```sql
-- Monitoring queries to run periodically during backfill

-- 1. Progress
SELECT
    last_id,
    total_rows,
    round(last_id::numeric / NULLIF((SELECT max(id) FROM users), 0) * 100, 2) AS pct_complete,
    updated_at,
    age(now(), started_at) AS elapsed
FROM _migration_jobs
WHERE job_name = 'backfill_display_name';

-- 2. Replication lag
SELECT
    client_addr AS replica,
    state,
    round(EXTRACT(EPOCH FROM replay_lag)::numeric, 1) AS lag_seconds
FROM pg_stat_replication;

-- 3. Lock contention
SELECT
    relation::regclass AS table_name,
    mode,
    count(*) AS waiting_queries,
    max(age(now(), a.query_start)) AS max_wait
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE NOT l.granted
GROUP BY relation, mode
ORDER BY max_wait DESC;

-- 4. Table bloat (from dead tuples during update)
SELECT
    relname,
    n_live_tup,
    n_dead_tup,
    round(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) AS dead_pct,
    last_autovacuum
FROM pg_stat_user_tables
WHERE relname = 'users';

-- 5. WAL generation rate
SELECT
    pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') / (1024*1024*1024) AS total_wal_gb,
    pg_size_pretty(pg_wal_lsn_diff(
        pg_current_wal_lsn(),
        (SELECT replay_lsn FROM pg_stat_replication LIMIT 1)
    )) AS wal_behind_replica;
```

### Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Replication lag | > 5s | > 30s | Pause backfill |
| Dead tuple ratio | > 20% | > 50% | Manual VACUUM |
| Lock wait time | > 10s | > 60s | Kill blocking query |
| Disk usage | > 80% | > 90% | Stop migration, expand disk |
| WAL behind replica | > 1GB | > 5GB | Pause backfill |
| Migration ETA | > 2x estimate | > 5x estimate | Investigate, optimize batch size |

### Post-Migration Cleanup

```sql
-- After a large data migration, clean up:

-- 1. Vacuum the affected tables
VACUUM (VERBOSE, ANALYZE) users;
VACUUM (VERBOSE, ANALYZE) orders;

-- 2. Reindex if indexes became bloated
REINDEX INDEX CONCURRENTLY idx_users_email;

-- 3. Update statistics
ANALYZE users;
ANALYZE orders;

-- 4. Drop backup tables (after retention period)
DROP TABLE IF EXISTS _backup_user_tiers;
DROP TABLE IF EXISTS users_dedup_backup;

-- 5. Drop tracking tables
DROP TABLE IF EXISTS _migration_jobs;

-- 6. Check table size before and after to verify no bloat remains
SELECT
    pg_size_pretty(pg_total_relation_size('users')) AS users_size,
    pg_size_pretty(pg_total_relation_size('orders')) AS orders_size;
```
