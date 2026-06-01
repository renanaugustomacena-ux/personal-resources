# Database Migrations — Testing delle Migrazioni

## Perché Testare le Migrazioni

Le migrazioni sono codice — codice che modifica una struttura dati condivisa e spesso contenente dati reali. Un errore in una migrazione può causare:

- **Perdita di dati irreversibile** (DROP COLUMN con dati, UPDATE con WHERE errata)
- **Downtime inatteso** (ALTER TABLE con lock, migration timeout)
- **Inconsistenza dati** (backfill parziale, trigger mal configurato)
- **Rollback impossibile** (dati trasformati senza possibilità di inversione)

I test delle migrazioni si dividono in tre categorie: verifica di correttezza (lo schema risultante è quello atteso), verifica di compatibilità (il codice funziona con il nuovo schema), e verifica di performance (la migrazione rispetta i tempi accettabili in produzione).

---

## Test di Correttezza dello Schema

### Snapshot Testing con pg_dump

```bash
#!/bin/bash
# test_schema.sh - verifica che la migrazione produca lo schema atteso

# Applica le migrazioni su un DB di test
flyway -url="jdbc:postgresql://localhost/test_db" migrate

# Esporta lo schema risultante
pg_dump test_db --schema-only --no-owner --no-privileges \
    | sed '/^--/d' | sed '/^$/d' \
    > actual_schema.sql

# Confronta con lo schema atteso (baseline)
if diff expected_schema.sql actual_schema.sql; then
    echo "PASS: Schema matches expected"
else
    echo "FAIL: Schema differs from expected"
    diff expected_schema.sql actual_schema.sql
    exit 1
fi
```

### Test con psycopg2/SQLAlchemy

```python
# tests/test_migrations.py
import pytest
from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command

@pytest.fixture(scope="module")
def migrated_db():
    """Database con tutte le migrazioni applicate."""
    engine = create_engine("postgresql://postgres:password@localhost/test_migrations")
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))

    # Applica tutte le migrazioni
    command.upgrade(alembic_cfg, "head")

    yield engine

    # Cleanup: rollback di tutte le migrazioni
    command.downgrade(alembic_cfg, "base")
    engine.dispose()


def test_users_table_exists(migrated_db):
    inspector = inspect(migrated_db)
    assert "users" in inspector.get_table_names()


def test_users_columns(migrated_db):
    inspector = inspect(migrated_db)
    columns = {col["name"]: col for col in inspector.get_columns("users")}

    assert "id" in columns
    assert "email" in columns
    assert columns["email"]["nullable"] == False
    assert "created_at" in columns


def test_users_indexes(migrated_db):
    inspector = inspect(migrated_db)
    indexes = {idx["name"]: idx for idx in inspector.get_indexes("users")}

    assert "idx_users_email" in indexes
    assert indexes["idx_users_email"]["unique"] == True


def test_users_constraints(migrated_db):
    inspector = inspect(migrated_db)
    unique_constraints = inspector.get_unique_constraints("users")
    constraint_names = [c["name"] for c in unique_constraints]
    assert "users_email_key" in constraint_names


def test_data_migration_backfill(migrated_db):
    """Verifica che il backfill dei dati sia avvenuto correttamente."""
    with migrated_db.connect() as conn:
        # Inserisce dati con il vecchio schema
        conn.execute(text("INSERT INTO users (full_name) VALUES ('Mario Rossi')"))
        conn.commit()

        # Verifica che il backfill abbia popolato il nuovo campo
        result = conn.execute(text(
            "SELECT display_name FROM users WHERE full_name = 'Mario Rossi'"
        )).fetchone()

        assert result is not None
        assert result[0] == "Mario Rossi"
```

---

## Test di Rollback

```python
def test_rollback_restores_state(migrated_db):
    """Verifica che l'undo della migrazione ripristini lo stato precedente."""
    inspector = inspect(migrated_db)
    alembic_cfg = Config("alembic.ini")

    # Stato prima della migrazione
    tables_before_upgrade = set(inspector.get_table_names())

    # Applica la migrazione V15
    command.upgrade(alembic_cfg, "15abc123")

    # Verifica che la nuova tabella esista
    tables_after_upgrade = set(inspect(migrated_db).get_table_names())
    assert "customer_segments" in tables_after_upgrade

    # Rollback
    command.downgrade(alembic_cfg, "14def456")

    # Verifica che lo stato sia tornato come prima
    tables_after_rollback = set(inspect(migrated_db).get_table_names())
    assert "customer_segments" not in tables_after_rollback
    assert tables_after_rollback == tables_before_upgrade


def test_rollback_preserves_existing_data(migrated_db):
    """Verifica che il rollback non tocchi dati preesistenti."""
    with migrated_db.connect() as conn:
        # Inserisce dati prima della migrazione
        conn.execute(text("INSERT INTO orders (amount, status) VALUES (100.00, 'pending')"))
        conn.commit()
        original_count = conn.execute(text("SELECT count(*) FROM orders")).scalar()

    # Applica migrazione che aggiunge una colonna
    command.upgrade(alembic_cfg, "head")

    # Rollback
    command.downgrade(alembic_cfg, "-1")

    with migrated_db.connect() as conn:
        new_count = conn.execute(text("SELECT count(*) FROM orders")).scalar()
        assert new_count == original_count, "Rollback should not delete existing rows"
```

---

## Test di Performance: Timing delle Migrazioni

```python
import time
import subprocess

def test_migration_performance(migrated_db, benchmark_data):
    """Verifica che la migrazione rispetti i limiti di tempo su dataset realistici."""

    # Inserisce dati di benchmark (dimensione simile a produzione)
    with migrated_db.connect() as conn:
        conn.execute(text("""
            INSERT INTO orders (user_id, amount, created_at)
            SELECT
                (random() * 100000)::bigint,
                (random() * 1000)::decimal(10,2),
                now() - (random() * 365)::int * interval '1 day'
            FROM generate_series(1, 1000000)
        """))
        conn.commit()

    # Misura il tempo della migrazione
    start = time.time()

    result = subprocess.run(
        ["flyway", "migrate", f"-url=jdbc:postgresql://localhost/{TEST_DB}"],
        capture_output=True,
        text=True,
        timeout=300
    )

    duration = time.time() - start

    assert result.returncode == 0, f"Migration failed: {result.stderr}"
    assert duration < 60, f"Migration took {duration:.1f}s, expected < 60s on 1M rows"
```

---

## Test di Compatibilità Backward

```python
def test_backward_compatibility(migrated_db):
    """Verifica che il codice v1 funzioni con DB v2 durante il rolling deploy."""
    from app.legacy_v1.repository import UserRepositoryV1
    from app.v2.repository import UserRepositoryV2

    # Applica migrazione DB v2
    command.upgrade(alembic_cfg, "head")

    # Crea utente con codice v2
    repo_v2 = UserRepositoryV2(migrated_db)
    user_id = repo_v2.create_user(email="test@example.com", display_name="Test User")

    # Verifica che il codice v1 possa ancora leggere l'utente
    repo_v1 = UserRepositoryV1(migrated_db)
    user = repo_v1.get_user(user_id)

    assert user is not None
    assert user["email"] == "test@example.com"
    # v1 usa full_name, che deve essere ancora disponibile
    assert user["full_name"] == "Test User"  # copiato da display_name tramite trigger
```

---

## CI/CD Pipeline per Migrazioni

```yaml
# .github/workflows/migration-tests.yml
name: Migration Tests

on: [push, pull_request]

jobs:
  test-migrations:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s

    steps:
      - uses: actions/checkout@v4

      - name: Test migrations forward
        run: flyway -url=jdbc:postgresql://localhost/test_db -user=postgres -password=testpass migrate

      - name: Validate schema
        run: python tests/validate_schema.py

      - name: Test backward compatibility
        run: pytest tests/test_migrations.py -v

      - name: Test rollback
        run: flyway -url=jdbc:postgresql://localhost/test_db -user=postgres -password=testpass undo

      - name: Verify clean rollback
        run: python tests/verify_rollback.py

      - name: Re-apply and test idempotency
        run: |
          flyway -url=jdbc:postgresql://localhost/test_db migrate
          flyway -url=jdbc:postgresql://localhost/test_db migrate  # second run: no-op
```

---

## Checklist di Test per Ogni Migrazione

Prima di mergiare una PR con una nuova migrazione:

- [ ] Lo script forward viene eseguito senza errori su DB pulito
- [ ] Lo script forward è idempotente (riesecuzione no-op o graceful)
- [ ] Lo schema risultante corrisponde allo snapshot atteso
- [ ] Lo script undo ripristina lo stato precedente
- [ ] Il rollback non causa perdita di dati preesistenti
- [ ] La migrazione rispetta il tempo limite su dataset di dimensione produzione
- [ ] Il codice v(N-1) funziona con il DB al nuovo schema (backward compat)
- [ ] Non ci sono lock che bloccherebbero le query applicative per più di `lock_timeout`
- [ ] I backfill su tabelle grandi usano batch per evitare replication lag eccessivo

Il testing delle migrazioni non è optional per sistemi in produzione — è la differenza tra un deployment che dura 2 minuti e uno che richiede un incident di 2 ore.

---

## Test Fixtures and Data Factories

### Deterministic Test Data

Avoid `random()` in test data generation — non-deterministic data makes test failures hard to reproduce.

```python
import factory
from datetime import datetime, timezone

class UserFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    email = factory.LazyAttribute(lambda o: f"user{o.id}@test.example.com")
    full_name = factory.Faker("name", locale="en_US")
    created_at = factory.LazyFunction(lambda: datetime(2024, 1, 1, tzinfo=timezone.utc))


class OrderFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.SubFactory(UserFactory)
    amount = factory.Iterator([10.00, 25.50, 99.99, 150.00, 500.00])
    status = factory.Iterator(["pending", "processing", "shipped", "delivered"])


def seed_test_data(engine, users: int = 100, orders_per_user: int = 5):
    """Seed deterministic test data for migration testing."""
    with engine.begin() as conn:
        for i in range(users):
            user = UserFactory(id=i + 1)
            conn.execute(text(
                "INSERT INTO users (id, email, full_name, created_at) "
                "VALUES (:id, :email, :full_name, :created_at)"
            ), user)

            for j in range(orders_per_user):
                order = OrderFactory(user_id=user["id"])
                conn.execute(text(
                    "INSERT INTO orders (user_id, amount, status) "
                    "VALUES (:user_id, :amount, :status)"
                ), order)
```

### Production-Scale Test Data

For performance testing, generate data at production scale using PostgreSQL's `generate_series`:

```sql
-- Generate 10M users (takes ~2 minutes on modern hardware)
INSERT INTO users (email, full_name, created_at)
SELECT
    'user' || n || '@perf-test.example.com',
    'User ' || n,
    '2020-01-01'::timestamptz + (n * interval '1 second')
FROM generate_series(1, 10000000) AS n;

-- Generate 50M orders
INSERT INTO orders (user_id, amount, status, created_at)
SELECT
    (random() * 10000000 + 1)::bigint,
    (random() * 999 + 1)::decimal(10,2),
    (ARRAY['pending','processing','shipped','delivered'])[floor(random()*4+1)::int],
    '2022-01-01'::timestamptz + (n * interval '100 milliseconds')
FROM generate_series(1, 50000000) AS n;

-- Analyze tables to update statistics
ANALYZE users;
ANALYZE orders;
```

---

## Migration Lint Testing

Automated checks that catch common mistakes before a migration reaches CI:

```python
# tests/test_migration_lint.py
import re
import glob
import pytest

MIGRATION_DIR = "migrations/"

def get_migration_files():
    return sorted(glob.glob(f"{MIGRATION_DIR}/V*.sql"))

@pytest.mark.parametrize("filepath", get_migration_files())
class TestMigrationLint:
    def test_has_lock_timeout(self, filepath):
        """ALTER TABLE statements must set lock_timeout."""
        content = open(filepath).read()
        if re.search(r'ALTER\s+TABLE', content, re.IGNORECASE):
            assert re.search(r'lock_timeout', content, re.IGNORECASE), \
                f"{filepath}: ALTER TABLE without lock_timeout"

    def test_no_drop_without_if_exists(self, filepath):
        """DROP statements must use IF EXISTS."""
        content = open(filepath).read()
        drops = re.findall(r'DROP\s+(TABLE|INDEX|COLUMN|FUNCTION|TRIGGER)\s+(?!IF)', 
                           content, re.IGNORECASE)
        assert len(drops) == 0, \
            f"{filepath}: DROP without IF EXISTS: {drops}"

    def test_no_update_without_where(self, filepath):
        """UPDATE statements must have a WHERE clause."""
        content = open(filepath).read()
        # Find UPDATE ... SET ... without WHERE
        updates = re.findall(
            r'UPDATE\s+\w+\s+SET\s+[^;]+(?<!WHERE\s+[^;]+);', 
            content, re.IGNORECASE | re.DOTALL
        )
        for u in updates:
            assert 'WHERE' in u.upper(), \
                f"{filepath}: UPDATE without WHERE clause"

    def test_index_uses_concurrently(self, filepath):
        """CREATE INDEX should use CONCURRENTLY for PostgreSQL."""
        content = open(filepath).read()
        # Skip if CREATE UNIQUE INDEX (sometimes cannot be concurrent)
        indexes = re.findall(
            r'CREATE\s+INDEX\s+(?!CONCURRENTLY)', 
            content, re.IGNORECASE
        )
        if indexes:
            pytest.warn(f"{filepath}: CREATE INDEX without CONCURRENTLY")

    def test_has_undo_script(self, filepath):
        """Every forward migration should have a corresponding undo."""
        version = re.search(r'V(\d+)__', filepath)
        if version:
            undo = f"{MIGRATION_DIR}/undo/U{version.group(1)}__*.sql"
            assert glob.glob(undo), \
                f"{filepath}: No undo script found (expected {undo})"

    def test_file_size_reasonable(self, filepath):
        """Migration files should not be excessively long."""
        lines = open(filepath).readlines()
        assert len(lines) < 200, \
            f"{filepath}: {len(lines)} lines — consider splitting"

    def test_no_hardcoded_credentials(self, filepath):
        """No passwords or tokens in migration files."""
        content = open(filepath).read()
        suspicious = re.findall(
            r"(password|secret|token|api_key)\s*=\s*'[^']+'",
            content, re.IGNORECASE
        )
        assert len(suspicious) == 0, \
            f"{filepath}: Hardcoded credential detected: {suspicious}"
```

---

## Testing Migration Idempotency

```python
def test_migration_idempotency(migrated_db):
    """Running migrations twice should produce the same result."""
    alembic_cfg = Config("alembic.ini")

    # First run
    command.upgrade(alembic_cfg, "head")
    schema_first = dump_schema(migrated_db)

    # Downgrade all
    command.downgrade(alembic_cfg, "base")

    # Second run
    command.upgrade(alembic_cfg, "head")
    schema_second = dump_schema(migrated_db)

    assert schema_first == schema_second, \
        "Schema differs between first and second migration run"


def dump_schema(engine) -> str:
    """Export schema as normalized text for comparison."""
    result = subprocess.run(
        ["pg_dump", "--schema-only", "--no-owner", "--no-privileges",
         "--no-comments", str(engine.url)],
        capture_output=True, text=True
    )
    # Normalize: remove timestamps, sort statements
    lines = sorted(line for line in result.stdout.splitlines()
                   if not line.startswith("--") and line.strip())
    return "\n".join(lines)
```

---

## Integration Testing with Testcontainers

For tests that need a real database without external dependencies:

```python
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres():
    """Spin up a real PostgreSQL instance for migration testing."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture
def db_engine(postgres):
    """Create a SQLAlchemy engine connected to the test container."""
    engine = create_engine(postgres.get_connection_url())
    yield engine
    engine.dispose()

def test_full_migration_cycle(db_engine):
    """Test the complete lifecycle: upgrade → verify → downgrade → verify."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", str(db_engine.url))

    # Upgrade
    command.upgrade(alembic_cfg, "head")

    inspector = inspect(db_engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "orders" in tables

    # Downgrade
    command.downgrade(alembic_cfg, "base")

    inspector = inspect(db_engine)
    tables = inspector.get_table_names()
    assert "users" not in tables
    assert "orders" not in tables
```

### Docker Compose for Multi-Database Testing

```yaml
# docker-compose.test.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test_db
      POSTGRES_PASSWORD: testpass
    ports: ["5432:5432"]
    healthcheck:
      test: pg_isready -U postgres
      interval: 5s

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: test_db
      MYSQL_ROOT_PASSWORD: testpass
    ports: ["3306:3306"]
    healthcheck:
      test: mysqladmin ping -h localhost
      interval: 5s

  migration-tests:
    build:
      context: .
      dockerfile: Dockerfile.test
    depends_on:
      postgres:
        condition: service_healthy
      mysql:
        condition: service_healthy
    environment:
      PG_URL: postgresql://postgres:testpass@postgres/test_db
      MYSQL_URL: mysql://root:testpass@mysql/test_db
    command: pytest tests/test_migrations.py -v --tb=short
```

---

## Testing Lock Behavior

```python
import threading
import time

def test_migration_does_not_block_reads(migrated_db):
    """Verify that the migration does not block SELECT queries."""
    read_blocked = threading.Event()
    read_completed = threading.Event()

    def reader():
        """Continuously read from the table during migration."""
        conn = migrated_db.connect()
        try:
            for _ in range(20):
                result = conn.execute(text("SELECT count(*) FROM users"))
                result.scalar()
                time.sleep(0.5)
            read_completed.set()
        except Exception as e:
            read_blocked.set()
            raise e
        finally:
            conn.close()

    # Start reader thread
    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    # Apply migration while reader is active
    time.sleep(1)  # let reader start
    command.upgrade(alembic_cfg, "head")

    reader_thread.join(timeout=15)

    assert read_completed.is_set(), "Reader thread did not complete"
    assert not read_blocked.is_set(), "Reader was blocked during migration"
```

---

## Troubleshooting

### 1. Test Database Has Stale State Between Runs

**Symptom**: Tests pass individually but fail when run as a suite. Schema objects from previous tests persist.

**Cause**: The test fixture does not reset the database between tests, or a test modifies the database without cleanup.

**Fix**: Use `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` as a teardown step. Or use separate databases per test module with `CREATE DATABASE` and `DROP DATABASE` in fixtures.

### 2. Schema Snapshot Test Fails Due to Ordering

**Symptom**: `diff expected_schema.sql actual_schema.sql` shows differences even though the schema is functionally identical.

**Cause**: `pg_dump` does not guarantee deterministic ordering of columns, constraints, or index definitions across runs.

**Fix**: Normalize both files before comparison: sort lines, strip comments, remove blank lines, and ignore whitespace differences. Use `pg_dump --no-comments` and pipe through `sort`.

### 3. Testcontainer Startup Timeout

**Symptom**: `TimeoutError: Container did not start within 30 seconds.`

**Cause**: Docker pull for the database image is slow, or the container health check threshold is too short.

**Fix**: Pre-pull the Docker image in CI (`docker pull postgres:16-alpine`). Increase the `timeout` parameter on the container fixture.

### 4. Migration Performance Test Gives Inconsistent Results

**Symptom**: The same migration takes 10s in one run and 45s in another.

**Cause**: Shared CI runners have variable I/O performance. Or the test data volume varies between runs.

**Fix**: Use deterministic data generation (not `random()`). Run performance tests on dedicated runners with consistent hardware. Use relative thresholds (e.g., "within 2x of baseline") rather than absolute.

### 5. Rollback Test Passes But Production Rollback Fails

**Symptom**: `test_rollback_restores_state` passes in CI but the actual rollback in production fails.

**Cause**: The test database has trivial data. Production has edge cases: NULLs in unexpected places, referential integrity violations, or data volumes that cause timeouts.

**Fix**: Seed test databases with production-like data including edge cases. Test rollbacks on a staging environment with a recent production dump.

### 6. Backward Compatibility Test Does Not Catch Real Issues

**Symptom**: The backward compat test passes but the v1 code fails in production during rolling deploy.

**Cause**: The test only checks SELECT queries but the v1 code also does INSERT/UPDATE that fail with the new schema (new NOT NULL constraint, removed default, etc.).

**Fix**: Test all CRUD operations in backward compatibility tests, not just reads. Include v1 INSERT, UPDATE, and DELETE queries in the test.

### 7. CI Migration Test Fails with Permission Errors

**Symptom**: `ERROR: permission denied to create extension "uuid-ossp"`

**Cause**: The test database user is not a superuser. Extensions require superuser or the `pg_execute_server_program` role.

**Fix**: Run CI with `POSTGRES_USER=postgres` (superuser) or pre-install required extensions in the Docker image. For production, use `SECURITY DEFINER` functions or request the DBA to install extensions.

### 8. Lock Behavior Test Has False Positives

**Symptom**: `test_migration_does_not_block_reads` passes even for known-blocking migrations.

**Cause**: The test uses a small table with no concurrent transactions, so the lock is acquired and released instantly.

**Fix**: Seed the table with enough data that DDL takes measurable time. Add a long-running transaction in a separate thread to simulate real contention.

### 9. Alembic Autogenerate Test Detects Phantom Differences

**Symptom**: `alembic check` reports pending migrations even though the schema matches the models.

**Cause**: Alembic's autogenerate comparison has known gaps: it may not detect certain constraint names, server defaults, or computed columns accurately.

**Fix**: Use `include_object` and `compare_type` configuration in `env.py`. Maintain a whitelist of known false positives. Periodically verify with `pg_dump` comparison.

### 10. Test Passes Locally But Fails in CI Due to PostgreSQL Version Mismatch

**Symptom**: Local tests pass on PostgreSQL 16 but CI runs PostgreSQL 14, and the migration uses a PG 16 feature.

**Cause**: Newer PostgreSQL versions support additional DDL syntax (e.g., `GENERATED ALWAYS` improvements, `MERGE` statement).

**Fix**: Pin the PostgreSQL version in CI to match production. Use the same Docker image tag everywhere. Add a version check at the start of migration tests.

---

## FAQ

### 1. Should I test migrations in a separate test suite or alongside application tests?

Separate suite. Migration tests need a specific database lifecycle (create → migrate → verify → rollback → cleanup) that conflicts with the application test lifecycle. Run them as a separate CI job.

### 2. How do I generate a schema snapshot baseline?

Run all migrations on a clean database, then export with `pg_dump --schema-only --no-owner --no-privileges > expected_schema.sql`. Commit this file. Update it whenever a new migration is added. Automate this update in CI.

### 3. Is it worth testing every migration's rollback, or just the latest?

Test every migration's rollback. A migration from 6 months ago that was never rollback-tested is a liability. Include rollback testing as part of the CI pipeline for every PR that adds a migration.

### 4. How do I test a data migration on production-scale data without a production dump?

Use synthetic data at the same scale. Generate with `generate_series` (PostgreSQL) or a data factory. Include edge cases: NULLs, maximum-length strings, boundary dates, unicode characters, and duplicate values.

### 5. Can I use SQLite for migration testing to avoid PostgreSQL dependency?

No. SQLite has fundamentally different DDL behavior (no ALTER COLUMN, no concurrent operations, different type system). Migration tests must run against the same database engine as production. Use Testcontainers or Docker Compose.

### 6. How do I test that a migration is backward-compatible?

Run the migration, then execute the previous code version's test suite against the migrated database. If any tests fail, the migration breaks backward compatibility.

### 7. How often should I update the schema snapshot baseline?

Every time a new migration is added. Automate it: after a successful migration test run, regenerate the snapshot and commit it. Fail CI if the snapshot is stale.

### 8. What is the right timeout for migration performance tests?

Measure migration duration on a staging database with production-scale data. Set the test timeout to 2x that measurement. If the migration takes 30s in staging, set the performance test threshold to 60s. Review thresholds quarterly as data grows.

### 9. How do I test migrations that use environment-specific SQL (e.g., Liquibase contexts)?

Run the test suite once per context. Example: run with `--contexts=production` and verify production-specific indexes exist. Run again with `--contexts=development` and verify dev-only seed data was applied.

### 10. Should migration tests run on every PR or only on main?

On every PR that modifies migration files. Use path-based CI triggers: `on: push: paths: ['migrations/**']`. Full regression tests (all migrations from base to head) should also run nightly or weekly.

### 11. How do I test migrations that involve external services (e.g., backfilling data from an API)?

Mock the external service in tests. The migration test should verify the schema change and the data transformation logic independently. For the external data fetch, use a separate integration test with recorded fixtures (VCR/cassette pattern). Never call external APIs from a migration test.

### 12. How do I validate that my migration does not increase query plan costs?

Run `EXPLAIN ANALYZE` on critical queries before and after the migration in the test database. Compare row estimates, actual execution times, and plan types. Flag if a query switches from index scan to sequential scan, or if execution time increases by more than 2x.

```python
def test_migration_does_not_degrade_query_performance(migrated_db):
    """Verify critical queries do not regress after migration."""
    critical_queries = [
        "SELECT * FROM users WHERE email = 'test@example.com'",
        "SELECT count(*) FROM orders WHERE user_id = 42",
        "SELECT * FROM orders WHERE created_at > now() - interval '7 days' ORDER BY created_at",
    ]

    for query in critical_queries:
        with migrated_db.connect() as conn:
            plan = conn.execute(text(f"EXPLAIN (ANALYZE, FORMAT JSON) {query}")).scalar()
            execution_time = plan[0]["Execution Time"]
            plan_type = plan[0]["Plan"]["Node Type"]

            assert execution_time < 100, \
                f"Query too slow ({execution_time}ms): {query[:50]}..."
            assert plan_type != "Seq Scan" or "small table" in query, \
                f"Unexpected Seq Scan for: {query[:50]}..."
```

### 13. What is the best strategy for testing migrations on a database with triggers and stored procedures?

Test them explicitly. After migration, verify that triggers still fire correctly and stored procedures still return expected results. Include trigger-dependent tests in your migration test suite. If the migration modifies a table with triggers, test both the direct DML path and the trigger-mediated path.

---

## Continuous Migration Testing Strategy

A mature migration testing strategy operates at three levels:

| Level | What | When | Duration |
|-------|------|------|----------|
| PR-level | Lint + forward + rollback on empty DB | Every PR | ~1 min |
| Integration | Full lifecycle on seeded DB + backward compat | Every merge to main | ~5 min |
| Regression | All migrations from base → head on production-scale data | Nightly/weekly | ~30 min |

### Nightly Regression Test

```yaml
# .github/workflows/nightly-migration-regression.yml
name: Nightly Migration Regression

on:
  schedule:
    - cron: '0 3 * * *'   # 03:00 UTC daily

jobs:
  regression:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: regression_db
          POSTGRES_PASSWORD: testpass
        ports: ["5432:5432"]
        options: --health-cmd pg_isready --health-interval 5s --shm-size 1g

    steps:
      - uses: actions/checkout@v4

      - name: Generate production-scale test data
        run: |
          PGPASSWORD=testpass psql -h localhost -U postgres -d regression_db -f tests/fixtures/generate_10m_rows.sql

      - name: Apply all migrations from base to head
        run: flyway -url=jdbc:postgresql://localhost/regression_db migrate
        timeout-minutes: 30

      - name: Measure migration timing
        run: |
          PGPASSWORD=testpass psql -h localhost -U postgres -d regression_db -tAc "
            SELECT version, description, execution_time
            FROM flyway_schema_history
            ORDER BY installed_rank;"

      - name: Run full rollback sequence
        run: |
          while flyway -url=jdbc:postgresql://localhost/regression_db undo 2>/dev/null; do
            echo 'Rolled back one migration'
          done

      - name: Re-apply all migrations (idempotency)
        run: flyway -url=jdbc:postgresql://localhost/regression_db migrate

      - name: Schema snapshot comparison
        run: |
          PGPASSWORD=testpass pg_dump -h localhost -U postgres --schema-only regression_db > schema.sql
          diff tests/fixtures/expected_schema.sql schema.sql
```

This three-level strategy catches different classes of bugs: linting catches syntax and convention issues, integration catches logic errors, and regression catches performance degradation and cross-migration interactions that only surface with real data volumes.
