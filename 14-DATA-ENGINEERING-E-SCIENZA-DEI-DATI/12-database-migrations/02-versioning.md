# Database Migrations — Versioning e Strumenti

## Flyway: Il Tool Più Diffuso per JVM

Flyway è lo strumento di riferimento per migrazioni su JVM (Java, Kotlin, Scala). Supporta anche Python e Go tramite CLI. Il modello è semplice: script SQL o Java ordinati per versione, applicati una volta sola.

### Convenzione di Nomenclatura

```
V{version}__{description}.sql        ← versioned migration (applicata una volta)
R__{description}.sql                 ← repeatable migration (rieseguita se cambia il checksum)
U{version}__{description}.sql        ← undo migration (Flyway Teams)

Esempi:
V1__create_schema.sql
V2__add_users_table.sql
V1.1__add_email_index.sql            ← versionamento decimale supportato
V20240115113000__add_notes_column.sql ← timestamp come versione
R__create_views.sql                  ← repeatable: view aggiornata ad ogni run se modificata
```

### Configurazione

```properties
# flyway.conf
flyway.url=jdbc:postgresql://localhost:5432/mydb
flyway.user=flyway_user
flyway.password=${FLYWAY_PASSWORD}
flyway.schemas=public,audit
flyway.locations=filesystem:migrations/,classpath:db/migration
flyway.table=flyway_schema_history
flyway.baselineOnMigrate=false
flyway.validateOnMigrate=true
flyway.outOfOrder=false
flyway.mixed=false
flyway.encoding=UTF-8
flyway.placeholderPrefix=$[
flyway.placeholderSuffix=]
flyway.placeholders.environment=production
```

### Integrazione Spring Boot

```java
// application.properties
spring.flyway.enabled=true
spring.flyway.locations=classpath:db/migration
spring.flyway.baseline-on-migrate=false
spring.flyway.validate-on-migrate=true
spring.flyway.out-of-order=false
```

```java
// Migrazione Java (per logica complessa)
// V5__data_transformation.java
@Component
public class V5__data_transformation implements JavaMigration {
    @Override
    public MigrationVersion getVersion() {
        return MigrationVersion.fromVersion("5");
    }

    @Override
    public String getDescription() {
        return "Complex data transformation";
    }

    @Override
    public void migrate(Context context) throws Exception {
        try (Statement stmt = context.getConnection().createStatement()) {
            ResultSet rs = stmt.executeQuery(
                "SELECT id, legacy_data FROM users WHERE legacy_data IS NOT NULL"
            );
            while (rs.next()) {
                long id = rs.getLong("id");
                String legacy = rs.getString("legacy_data");
                String transformed = transformData(legacy);
                try (PreparedStatement update = context.getConnection().prepareStatement(
                    "UPDATE users SET new_data = ? WHERE id = ?"
                )) {
                    update.setString(1, transformed);
                    update.setLong(2, id);
                    update.executeUpdate();
                }
            }
        }
    }

    private String transformData(String legacy) {
        // logica di trasformazione
        return legacy.toUpperCase();
    }
}
```

### Comandi CLI

```bash
# Applica tutte le migrazioni pendenti
flyway migrate

# Verifica stato migrazioni
flyway info
# Output:
# +-----------+---------+------------------+------+---------------------+---------+
# | Category  | Version | Description      | Type | Installed On        | State   |
# +-----------+---------+------------------+------+---------------------+---------+
# | Versioned | 1       | create schema    | SQL  | 2024-01-10 10:00:00 | Success |
# | Versioned | 2       | add users        | SQL  | 2024-01-11 09:30:00 | Success |
# | Versioned | 3       | add email index  | SQL  |                     | Pending |

# Valida checksum degli script già applicati
flyway validate

# Repair: aggiorna checksum dopo modifica accidentale di script già applicato
flyway repair

# Baseline: marca lo stato attuale come V1 (per DB esistenti senza storia)
flyway baseline --flyway.baselineVersion=5 --flyway.baselineDescription="Existing schema"

# Undo (Flyway Teams)
flyway undo

# Clean (ATTENZIONE: elimina tutto il database — solo per development)
flyway clean
```

---

## Liquibase: Formato XML/YAML/JSON/SQL

Liquibase usa il concetto di **changelog** e **changeset**. Ogni changeset è identificato da ID + author e può essere scritto in XML, YAML, JSON o SQL nativo.

### Changelog in YAML

```yaml
# db/changelog/db.changelog-master.yaml
databaseChangeLog:
  - include:
      file: db/changelog/001-initial-schema.yaml
  - include:
      file: db/changelog/002-add-users.yaml
  - include:
      file: db/changelog/003-add-indexes.yaml
```

```yaml
# db/changelog/002-add-users.yaml
databaseChangeLog:
  - changeSet:
      id: add-users-table
      author: alice
      changes:
        - createTable:
            tableName: users
            columns:
              - column:
                  name: id
                  type: BIGSERIAL
                  constraints:
                    primaryKey: true
                    nullable: false
              - column:
                  name: email
                  type: VARCHAR(255)
                  constraints:
                    nullable: false
                    unique: true
              - column:
                  name: created_at
                  type: TIMESTAMPTZ
                  defaultValueComputed: NOW()
      rollback:
        - dropTable:
            tableName: users

  - changeSet:
      id: add-users-index
      author: alice
      changes:
        - createIndex:
            indexName: idx_users_email
            tableName: users
            columns:
              - column:
                  name: email
      rollback:
        - dropIndex:
            indexName: idx_users_email
            tableName: users
```

### Liquibase con SQL nativo

```yaml
- changeSet:
    id: complex-migration
    author: bob
    changes:
      - sql:
          sql: |
            ALTER TABLE orders ADD COLUMN processing_fee DECIMAL(10, 2);
            UPDATE orders SET processing_fee = amount * 0.02;
            ALTER TABLE orders ALTER COLUMN processing_fee SET NOT NULL;
    rollback:
      - sql:
          sql: ALTER TABLE orders DROP COLUMN processing_fee;
```

### Comandi Liquibase

```bash
# Apply pending changesets
liquibase update

# Dry run: genera l'SQL senza eseguirlo
liquibase updateSQL

# Status
liquibase status --verbose

# Tag lo stato corrente (per rollback selettivo)
liquibase tag --tag v1.5.0

# Rollback al tag
liquibase rollback --tag v1.5.0

# Rollback di N changeset
liquibase rollbackCount 3

# Generate changelog da DB esistente
liquibase generateChangeLog --changelogFile existing-schema.yaml
```

---

## Alembic: Python e SQLAlchemy

```bash
pip install alembic sqlalchemy
alembic init alembic/
```

```python
# alembic/env.py
from sqlalchemy import create_engine, pool
from alembic import context
import os

def run_migrations_online():
    connectable = create_engine(
        os.environ["DATABASE_URL"],
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
```

```python
# alembic/versions/001_create_users.py
"""create users table

Revision ID: 001abc123def
Revises:
Create Date: 2024-01-15 10:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = '001abc123def'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
```

```bash
# Crea nuova migrazione
alembic revision --autogenerate -m "add users table"
# --autogenerate: confronta SQLAlchemy models con DB attuale e genera il diff

# Applica migrations
alembic upgrade head
alembic upgrade +2       # applica le prossime 2

# Rollback
alembic downgrade -1
alembic downgrade base   # rollback completo

# Status
alembic current
alembic history --verbose
```

---

## Confronto tra Tool

| Feature | Flyway | Liquibase | Alembic |
|---------|--------|-----------|---------|
| Linguaggio | JVM + CLI | JVM + CLI | Python |
| Formato | SQL, Java | XML, YAML, JSON, SQL | Python |
| Autogeneration | No | Parziale | Sì (da SQLAlchemy) |
| Rollback | Teams only | Sì (built-in) | Sì |
| Lock distribuito | Sì | Sì | Sì |
| Repeatable | Sì | No (logica custom) | No |
| Community | Grande | Grande | Grande (Python) |
| Cloud native | Flyway Desktop | HubDB Cloud | — |

**Raccomandazione per scelta**:
- **Java/Spring Boot**: Flyway (semplicità) o Liquibase (più funzionalità)
- **Python/FastAPI/Django**: Alembic (con SQLAlchemy) o Django migrations (built-in)
- **Multi-DB con formato neutro**: Liquibase
- **Schema-as-code (state-based)**: Atlas (Go, open source)

Il versioning delle migrazioni è il fondamento della gestione evolutiva del database. La disciplina di un singolo commit per migrazione, con script idempotenti e rollback definiti, elimina la classe di problemi di "schema drift" che affligge le applicazioni mature.

---

## Advanced Flyway Configuration

### Multi-Schema Migrations

Flyway supports migrating multiple schemas within one database. Schemas are created in order if they do not exist.

```properties
# flyway.conf — multi-schema
flyway.schemas=public,auth,billing,analytics
flyway.defaultSchema=public
flyway.createSchemas=true
```

Each migration script can explicitly target a schema:

```sql
-- V10__billing_schema_tables.sql
SET search_path TO billing;

CREATE TABLE invoices (
    id          BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    amount      DECIMAL(12,2) NOT NULL,
    currency    CHAR(3) DEFAULT 'USD',
    issued_at   TIMESTAMPTZ DEFAULT now(),
    paid_at     TIMESTAMPTZ
);

CREATE TABLE line_items (
    id         BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT REFERENCES invoices(id),
    product    VARCHAR(200) NOT NULL,
    quantity   INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(12,2) NOT NULL
);

SET search_path TO public;
```

### Callback Hooks

Flyway supports lifecycle callbacks that fire before/after key events:

```java
// Custom callback: block migrations during peak hours
public class PeakHourGuard implements Callback {
    @Override
    public boolean supports(Event event, Context context) {
        return event == Event.BEFORE_MIGRATE;
    }

    @Override
    public boolean canHandleInTransaction(Event event, Context context) {
        return false;
    }

    @Override
    public void handle(Event event, Context context) {
        int hour = LocalTime.now().getHour();
        if (hour >= 9 && hour <= 17) {
            throw new FlywayException(
                "Migrations blocked during business hours (09:00-17:00). "
                + "Current hour: " + hour
            );
        }
    }
}
```

Available callback events:

| Event | Fires When |
|-------|-----------|
| `BEFORE_MIGRATE` | Before any migration starts |
| `AFTER_MIGRATE` | After all migrations complete |
| `BEFORE_EACH_MIGRATE` | Before each individual migration |
| `AFTER_EACH_MIGRATE` | After each individual migration |
| `BEFORE_VALIDATE` | Before validation |
| `AFTER_VALIDATE` | After validation |
| `BEFORE_CLEAN` | Before `flyway clean` |
| `AFTER_REPAIR` | After `flyway repair` |

SQL-based callbacks (place in migrations directory):

```sql
-- beforeMigrate.sql — runs before every flyway migrate
SET lock_timeout = '5s';
SET statement_timeout = '600s';
SELECT pg_advisory_lock(12345);

-- afterMigrate.sql — runs after every flyway migrate
ANALYZE;
SELECT pg_advisory_unlock(12345);
```

### Flyway with Docker and Kubernetes

```yaml
# docker-compose.yml — Flyway as init container
services:
  flyway:
    image: flyway/flyway:10
    command: migrate
    volumes:
      - ./migrations:/flyway/sql
    environment:
      FLYWAY_URL: jdbc:postgresql://postgres:5432/app
      FLYWAY_USER: app_migrator
      FLYWAY_PASSWORD_FILE: /run/secrets/db_password
      FLYWAY_BASELINE_ON_MIGRATE: "false"
      FLYWAY_VALIDATE_ON_MIGRATE: "true"
    depends_on:
      postgres:
        condition: service_healthy
```

```yaml
# Kubernetes init container pattern
apiVersion: batch/v1
kind: Job
metadata:
  name: flyway-migrate
  annotations:
    argocd.argoproj.io/hook: PreSync
spec:
  template:
    spec:
      containers:
        - name: flyway
          image: flyway/flyway:10
          args: ["migrate"]
          envFrom:
            - secretRef:
                name: db-credentials
          volumeMounts:
            - name: migrations
              mountPath: /flyway/sql
      volumes:
        - name: migrations
          configMap:
            name: migration-scripts
      restartPolicy: Never
  backoffLimit: 3
```

---

## Advanced Liquibase Configuration

### Preconditions

Liquibase preconditions let you guard changesets so they only run when conditions are met:

```yaml
databaseChangeLog:
  - changeSet:
      id: add-fulltext-index
      author: bob
      preConditions:
        - onFail: MARK_RAN
        - dbms:
            type: postgresql
        - tableExists:
            tableName: articles
        - columnExists:
            tableName: articles
            columnName: body
      changes:
        - sql:
            sql: |
              CREATE INDEX idx_articles_body_gin
              ON articles USING gin(to_tsvector('english', body));

  - changeSet:
      id: add-column-if-missing
      author: alice
      preConditions:
        - onFail: MARK_RAN
        - not:
            - columnExists:
                tableName: users
                columnName: phone
      changes:
        - addColumn:
            tableName: users
            columns:
              - column:
                  name: phone
                  type: VARCHAR(20)
```

### Changelog Inclusion Strategies

```yaml
# Master changelog with conditional includes
databaseChangeLog:
  # Always included
  - include:
      file: db/changelog/core/schema.yaml
  
  # Include all files in directory (sorted alphabetically)
  - includeAll:
      path: db/changelog/features/
      relativeToChangelogFile: true
  
  # Conditional on context
  - include:
      file: db/changelog/seed/test-data.yaml
      context: development,test
```

### Liquibase Diff and Snapshot

```bash
# Compare two databases
liquibase diff \
    --referenceUrl="jdbc:postgresql://localhost/staging" \
    --referenceUsername=admin \
    --referencePassword=secret \
    --url="jdbc:postgresql://localhost/production" \
    --username=admin \
    --password=secret

# Generate changelog from diff
liquibase diffChangeLog \
    --referenceUrl="jdbc:postgresql://localhost/staging" \
    --url="jdbc:postgresql://localhost/production" \
    --changelogFile=drift-fix.yaml

# Snapshot current database state
liquibase snapshot --snapshotFormat=json > db-snapshot.json
```

---

## Advanced Alembic Configuration

### Multi-Database Alembic

```python
# alembic/env.py — multi-database support
from alembic import context
import os

def run_migrations_online():
    engines = {
        "main": create_engine(os.environ["MAIN_DB_URL"]),
        "analytics": create_engine(os.environ["ANALYTICS_DB_URL"]),
    }

    for name, engine in engines.items():
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=metadata_map[name],
                version_table=f"alembic_version_{name}",
            )
            with context.begin_transaction():
                context.run_migrations()
```

### Alembic Branch Management

When multiple developers create migrations concurrently, Alembic handles this through branch merging:

```bash
# Developer A creates migration
alembic revision --autogenerate -m "add orders table"
# Creates: abc123 (down_revision = head_xyz)

# Developer B creates migration (same parent)
alembic revision --autogenerate -m "add products table"
# Creates: def456 (down_revision = head_xyz)

# After both merge to main, Alembic detects two heads
alembic heads
# abc123 (head)
# def456 (head)

# Create merge revision
alembic merge abc123 def456 -m "merge orders and products"
# Creates: merge_789 (down_revision = (abc123, def456))

alembic upgrade head
```

### Alembic Autogenerate Customization

```python
# alembic/env.py — filter what autogenerate detects
def include_object(object, name, type_, reflected, compare_to):
    # Skip system tables
    if type_ == "table" and name.startswith("pg_"):
        return False
    # Skip specific schemas
    if hasattr(object, "schema") and object.schema == "information_schema":
        return False
    return True

def run_migrations_online():
    ...
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        include_object=include_object,
        compare_type=True,         # detect column type changes
        compare_server_default=True,  # detect default changes
    )
```

---

## Version Numbering Strategies

### Sequential Versioning

```
V1__initial_schema.sql
V2__add_users.sql
V3__add_orders.sql
V4__add_user_index.sql
```

Pros: Simple, clear ordering. Cons: Conflicts when two developers create V4 simultaneously.

### Timestamp-Based Versioning

```
V20240115103000__initial_schema.sql
V20240116140500__add_users.sql
V20240117091200__add_orders.sql
```

Pros: No conflicts between developers. Cons: Harder to read ordering at a glance, and potential timezone issues if developers do not standardize on UTC.

### Hybrid Versioning (Recommended for Teams)

```
V2024.01.001__initial_schema.sql
V2024.01.002__add_users.sql
V2024.02.001__add_orders.sql
V2024.02.002__add_user_index.sql
```

Pros: Year-month prefix gives chronological context, sequential suffix within each month avoids conflicts in small teams.

### Branched Versioning

Some teams prefix with the ticket or feature ID:

```
V20240115_PROJ123__add_premium_tier.sql
V20240116_PROJ456__add_analytics_events.sql
```

This ties each migration to its originating ticket for traceability.

---

## Schema History Tables Internals

### Flyway Schema History

```sql
-- Flyway creates and manages this table
SELECT * FROM flyway_schema_history ORDER BY installed_rank;

-- Columns:
-- installed_rank  INT         — execution order
-- version         VARCHAR(50) — version string (e.g., "3")
-- description     VARCHAR(200)
-- type            VARCHAR(20) — SQL, JDBC, SPRING_JDBC
-- script          VARCHAR(1000)
-- checksum        INT         — CRC32 of the script content
-- installed_by    VARCHAR(100)
-- installed_on    TIMESTAMP
-- execution_time  INT         — milliseconds
-- success         BOOLEAN

-- Detect failed migrations
SELECT version, description, execution_time, success
FROM flyway_schema_history
WHERE success = false;
```

### Liquibase DATABASECHANGELOG

```sql
-- Liquibase tracking table
SELECT * FROM databasechangelog ORDER BY dateexecuted;

-- Columns:
-- id             VARCHAR(255) — changeset id
-- author         VARCHAR(255) — changeset author
-- filename       VARCHAR(255) — changelog file
-- dateexecuted   TIMESTAMP
-- orderexecuted  INT
-- exectype       VARCHAR(10) — EXECUTED, FAILED, SKIPPED, RERAN, MARK_RAN
-- md5sum         VARCHAR(35) — MD5 of changeset content
-- description    VARCHAR(255)
-- comments       VARCHAR(255)
-- tag            VARCHAR(255)
-- liquibase      VARCHAR(20) — Liquibase version used
-- contexts       VARCHAR(255)
-- labels         VARCHAR(255)
-- deployment_id  VARCHAR(10)
```

### Alembic Version Table

```sql
-- Alembic uses a simple single-row table
SELECT * FROM alembic_version;
-- version_num VARCHAR(32) — current revision hash

-- To check full migration history, use CLI:
-- alembic history --verbose
```

---

## CI/CD Integration Patterns

### Pre-Merge Validation Pipeline

```yaml
# .github/workflows/migration-validation.yml
name: Migration Validation

on: pull_request

jobs:
  validate:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: validation_db
          POSTGRES_PASSWORD: ci_password
        ports: ["5432:5432"]
        options: --health-cmd pg_isready --health-interval 5s

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # full history for diff

      - name: Detect new migration files
        id: detect
        run: |
          NEW_MIGRATIONS=$(git diff --name-only origin/main...HEAD -- 'migrations/*.sql')
          echo "files=$NEW_MIGRATIONS" >> $GITHUB_OUTPUT
          echo "Found migrations: $NEW_MIGRATIONS"

      - name: Check migration naming convention
        run: |
          for f in ${{ steps.detect.outputs.files }}; do
            basename=$(basename "$f")
            if ! [[ "$basename" =~ ^V[0-9]+__[a-z_]+\.sql$ ]]; then
              echo "ERROR: $basename does not follow naming convention V{n}__{description}.sql"
              exit 1
            fi
          done

      - name: Run forward migrations
        run: flyway -url=jdbc:postgresql://localhost/validation_db migrate

      - name: Validate schema snapshot
        run: |
          pg_dump validation_db --schema-only --no-owner > actual.sql
          diff expected_schema.sql actual.sql

      - name: Test rollback
        run: flyway -url=jdbc:postgresql://localhost/validation_db undo

      - name: Re-apply (idempotency check)
        run: flyway -url=jdbc:postgresql://localhost/validation_db migrate
```

### Migration Linting

```bash
#!/bin/bash
# lint_migrations.sh — catches common mistakes before CI

set -euo pipefail

for file in migrations/V*.sql; do
  echo "Linting: $file"

  # Check for DROP without IF EXISTS
  if grep -qiP '^\s*DROP\s+(TABLE|INDEX|COLUMN)\s+(?!IF)' "$file"; then
    echo "  WARNING: DROP without IF EXISTS in $file"
  fi

  # Check for missing lock_timeout
  if grep -qi 'ALTER TABLE' "$file" && ! grep -qi 'lock_timeout' "$file"; then
    echo "  WARNING: ALTER TABLE without lock_timeout in $file"
  fi

  # Check for UPDATE without WHERE
  if grep -qiP '^\s*UPDATE\s+\w+\s+SET\s+' "$file" && ! grep -qi 'WHERE' "$file"; then
    echo "  ERROR: UPDATE without WHERE clause in $file"
    exit 1
  fi

  # Check for CREATE INDEX without CONCURRENTLY (PostgreSQL)
  if grep -qiP '^\s*CREATE\s+INDEX\s+(?!CONCURRENTLY)' "$file"; then
    echo "  WARNING: CREATE INDEX without CONCURRENTLY in $file"
  fi
done

echo "Linting complete"
```

---

## Troubleshooting

### 1. Checksum Mismatch After Script Modification

**Symptom**: `FlywayValidateException: Validate failed: Migration checksum mismatch`

**Cause**: A migration script was edited after it was applied to the database. Flyway stores a CRC32 checksum of each script at application time.

**Fix**: If the edit was intentional and the change is compatible, run `flyway repair` to update the stored checksum. If the edit was accidental, revert the file to its original content. Never repair in production without verifying what changed.

### 2. Out-of-Order Migration Rejected

**Symptom**: Migration V5 exists but V4 was added later and is rejected as pending.

**Cause**: `flyway.outOfOrder` is `false` (default). Flyway refuses to apply a migration with a lower version than the latest applied.

**Fix**: Set `flyway.outOfOrder=true` temporarily or permanently. Alternatively, renumber the script to a version higher than the latest applied.

### 3. Liquibase Lock Table Stuck

**Symptom**: `Waiting for changelog lock... Liquibase Update Failed: Could not acquire change log lock.`

**Cause**: A previous Liquibase run crashed or was killed without releasing the lock. The `DATABASECHANGELOGLOCK` table still has `LOCKED=true`.

**Fix**:
```bash
liquibase releaseLocks
# Or manually:
# UPDATE databasechangeloglock SET locked = false, lockgranted = NULL, lockedby = NULL WHERE id = 1;
```

### 4. Alembic Multiple Heads Detected

**Symptom**: `alembic.util.CommandError: Multiple head revisions are present`

**Cause**: Two or more developers created migrations from the same parent revision without merging.

**Fix**: Run `alembic merge <rev1> <rev2> -m "merge message"` to create an explicit merge point, then `alembic upgrade head`.

### 5. Migration Timeout on Large Table ALTER

**Symptom**: Migration hangs or times out on `ALTER TABLE` for a table with hundreds of millions of rows.

**Cause**: The DDL statement requires a table rewrite (MySQL for most ALTERs, PostgreSQL for type changes) or is blocked by a long-running transaction holding a conflicting lock.

**Fix**: For MySQL, use gh-ost or pt-online-schema-change instead of raw ALTER. For PostgreSQL, set `lock_timeout` to a short value, terminate blocking queries, and retry. For type changes, use the expand-contract pattern.

### 6. Flyway Fails to Connect During Kubernetes Startup

**Symptom**: Flyway init container exits with connection refused errors even though PostgreSQL pod is running.

**Cause**: Kubernetes readiness probes pass before PostgreSQL is actually accepting connections, or DNS for the service is not yet resolved.

**Fix**: Add a retry wrapper:
```bash
#!/bin/bash
MAX_RETRIES=30
RETRY=0
until flyway migrate 2>/dev/null || [ $RETRY -eq $MAX_RETRIES ]; do
  echo "Waiting for database... attempt $((RETRY+1))/$MAX_RETRIES"
  sleep 2
  RETRY=$((RETRY+1))
done
[ $RETRY -eq $MAX_RETRIES ] && echo "FATAL: Could not connect" && exit 1
```

### 7. Repeatable Migration Runs Every Time

**Symptom**: A Flyway repeatable migration (`R__create_views.sql`) re-executes on every `flyway migrate` even when nothing changed.

**Cause**: The file has trailing whitespace changes, different line endings (CRLF vs LF), or the encoding does not match `flyway.encoding`. Any byte-level change alters the checksum.

**Fix**: Normalize line endings to LF, ensure consistent encoding (UTF-8), and strip trailing whitespace. Use `.editorconfig` or a pre-commit hook.

### 8. Django Migration Circular Dependency

**Symptom**: `django.db.migrations.exceptions.CircularDependencyError`

**Cause**: Two Django apps have migrations that depend on each other.

**Fix**: Break the cycle by splitting the offending migration into two: one that creates the table without the FK, and a second that adds the FK using `RunSQL` or a separate `AddField` operation.

### 9. Alembic Autogenerate Misses Changes

**Symptom**: `alembic revision --autogenerate` produces an empty migration even though the model changed.

**Cause**: The `target_metadata` in `env.py` does not import the module where the model is defined, or the model uses a different `Base` than what is configured.

**Fix**: Ensure all model modules are imported before `target_metadata` is read. Add explicit imports in `env.py` or use a central `models/__init__.py` that re-exports everything.

### 10. Partial Migration Failure on MySQL (Non-Transactional DDL)

**Symptom**: Migration script with multiple ALTER TABLE statements fails midway, leaving the database in an inconsistent state.

**Cause**: MySQL commits each DDL statement immediately and does not support transactional DDL rollback.

**Fix**: Split each DDL into its own migration file so each is independently trackable. Write corresponding undo scripts. Before applying, take a schema-only dump as a checkpoint. Consider using gh-ost for large-table ALTERs.

### 11. Schema Drift Between Environments

**Symptom**: Migrations pass in CI but fail in staging or production. The schema does not match.

**Cause**: Manual DDL was applied directly to the production database outside the migration tool. The migration tool sees the schema history as up-to-date but the actual schema differs.

**Fix**: Run `liquibase diff` or `atlas schema diff` to detect drift. Create a corrective migration that reconciles the live schema with the expected state. Institute a policy: never apply DDL outside the migration tool.

### 12. Flyway Baseline Conflict

**Symptom**: `FlywayException: Found non-empty schema(s) "public" but no schema history table.`

**Cause**: Running Flyway on an existing database that was not previously managed by Flyway.

**Fix**: Run `flyway baseline` to mark the current state as version 1 (or the appropriate version). All migrations up to and including the baseline version are then skipped.

---

## FAQ

### 1. Should I use sequential or timestamp-based version numbers?

For solo developers or very small teams, sequential works fine. For larger teams where multiple developers create migrations concurrently, timestamp-based (or date-prefixed) eliminates merge conflicts. The key is consistency within a project.

### 2. Can I switch migration tools mid-project (e.g., Flyway to Liquibase)?

Yes, but it requires effort. Export the current schema, create a baseline changelog for the new tool, and mark all existing migrations as already applied. The critical step is ensuring the new tool's tracking table accurately reflects the current state. Never run both tools simultaneously.

### 3. How do I handle migrations in a monorepo with multiple services sharing one database?

Options: (a) Use a single shared migration directory with a naming convention that prefixes service name (e.g., `V20240115_billing__add_invoices.sql`). (b) Use separate schemas per service with independent migration sets. (c) Use Liquibase contexts or labels to partition changesets by service. Option (b) is cleanest for service isolation.

### 4. What is the difference between `flyway repair` and `flyway clean`?

`repair` updates checksums and removes failed migration entries from the history table without touching the database schema. `clean` drops all objects in the configured schemas, completely wiping the database. Never run `clean` in production.

### 5. How should I version stored procedures and views?

Use repeatable migrations. In Flyway, `R__create_user_views.sql` re-applies whenever its checksum changes. In Liquibase, use `runOnChange: true`. In Alembic, call `op.execute()` with `CREATE OR REPLACE` statements. Keep procedure/view definitions in dedicated files separate from table migrations.

### 6. Is Alembic autogenerate safe for production?

Autogenerate is a starting point, not a final product. Always review the generated migration before applying. Autogenerate cannot detect: renamed columns (it sees a drop + add), changes to CHECK constraints, data migrations, or custom types. Treat it as a diff suggestion that needs human validation.

### 7. How do I roll back a Flyway Community edition migration (no undo support)?

Write manual undo scripts and execute them via `psql` or another runner. Update `flyway_schema_history` to delete the migration entry. Consider upgrading to Flyway Teams if rollbacks are frequent, or switch to Liquibase or Alembic which include built-in rollback.

### 8. What happens if two instances of my application run migrations simultaneously?

Flyway, Liquibase, and Alembic all implement distributed locking. Flyway uses `pg_advisory_lock` (PostgreSQL) or `SELECT FOR UPDATE` on its history table. Liquibase uses `DATABASECHANGELOGLOCK`. Alembic uses `SELECT FOR UPDATE` on `alembic_version`. The second instance waits until the first releases the lock.

### 9. Should migration scripts be committed alongside application code or in a separate repository?

Same repository, almost always. Migrations and application code evolve together. Separating them introduces coordination overhead and increases the chance of deploying code that references a schema that does not exist yet (or vice versa). Only separate if a regulatory requirement demands it.

### 10. How do I handle database-specific SQL across PostgreSQL, MySQL, and SQL Server?

Liquibase abstracts this with its XML/YAML DSL and `dbms` preconditions. For Flyway, use separate locations per database type (`classpath:db/postgresql`, `classpath:db/mysql`). For Alembic, use `op.get_bind().dialect.name` to branch on the current database engine.

### 11. What is the recommended maximum size for a single migration file?

Keep each migration to a single logical change, typically under 100 lines of SQL. If a migration requires 500+ lines, it probably conflates multiple changes (table creation + backfill + index creation). Split into separate migration files for independent rollback and clearer history.

### 12. How do I safely delete old migration files to reduce clutter?

Squash old migrations into a single baseline: dump the schema at a known version, create a new `V1__baseline.sql` from the dump, delete all migrations up to that version, and run `flyway baseline` on all environments. Only do this when all environments (dev, staging, production) are at or past the squash point.

### 13. Can I use Flyway with NoSQL databases?

Flyway is designed for relational databases. For MongoDB, use `mongosh` scripts with a custom runner or tools like `migrate-mongo`. For DynamoDB, use CloudFormation or Terraform for schema management. The concept of versioned migrations still applies; only the tooling changes.
