# SQLite: Testing e Debugging

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Testing Strategies
2. Unit Testing
3. Integration Testing
4. Debugging Techniques
5. Performance Profiling
6. Memory Debugging
7. Corruption Detection
8. Logging
9. Benchmarking
10. CI/CD Integration

---

## 1. Testing Strategies

### 1.1 Test Database Setup

```python
import sqlite3
import unittest
import tempfile
import os

class TestDatabase:
    """Setup/teardown per test database"""
    
    @classmethod
    def setUpClass(cls):
        """Crea database temporaneo per ogni test class"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, 'test.db')
        
    def setUp(self):
        """Setup prima di ogni test"""
        self.conn = sqlite3.connect(self.db_path)
        self._create_schema()
        
    def _create_schema(self):
        """Crea schema per test"""
        self.conn.executescript('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE
            );
            
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            
            CREATE INDEX idx_posts_user ON posts(user_id);
        ''')
        self.conn.commit()
        
    def tearDown(self):
        """Cleanup dopo ogni test"""
        self.conn.close()
        
    @classmethod
    def tearDownClass(cls):
        """Rimuovi file temporanei"""
        import shutil
        shutil.rmtree(cls.temp_dir)
```

### 1.2 In-Memory Testing

```python
class InMemoryTestCase(unittest.TestCase):
    """Base class per test con database in-memory"""
    
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        
    def tearDown(self):
        self.conn.close()
        
    def _setup_schema(self):
        """Setup schema in subclass"""
        pass
        
class UserRepositoryTest(InMemoryTestCase):
    def setUp(self):
        super().setUp()
        self._setup_schema()
        self.repo = UserRepository(self.conn)
        
    def test_insert_user(self):
        user_id = self.repo.insert(name='John', email='john@test.com')
        self.assertIsNotNone(user_id)
        self.assertGreater(user_id, 0)
        
    def test_get_user(self):
        user_id = self.repo.insert(name='John', email='john@test.com')
        user = self.repo.get_by_id(user_id)
        
        self.assertIsNotNone(user)
        self.assertEqual(user['name'], 'John')
```

### 1.3 Test Data Fixtures

```python
class TestFixtures:
    """Fixture utilities per test"""
    
    @staticmethod
    def create_users(conn, count=10):
        """Creates test users"""
        users = []
        for i in range(count):
            conn.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                (f"User {i}", f"user{i}@test.com")
            )
            users.append({'id': i+1, 'name': f"User {i}", 'email': f"user{i}@test.com"})
        
        conn.commit()
        return users
        
    @staticmethod
    def create_posts(conn, user_id, count=5):
        """Creates test posts for a user"""
        posts = []
        for i in range(count):
            conn.execute(
                "INSERT INTO posts (user_id, title) VALUES (?, ?)",
                (user_id, f"Post {i}")
            )
            posts.append({'id': i+1, 'user_id': user_id, 'title': f"Post {i}"})
        
        conn.commit()
        return posts
        
    @staticmethod
    def create_relationships(conn):
        """Creates complex test data"""
        TestFixtures.create_users(conn, 5)
        
        # Add posts for each user
        for user_id in range(1, 6):
            TestFixtures.create_posts(conn, user_id, 3)
```

---

## 2. Unit Testing

### 2.1 Repository Testing

```python
class UserRepositoryTest(unittest.TestCase):
    
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self._setup_schema()
        self.repo = UserRepository(self.conn)
        
    def _setup_schema(self):
        self.conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE
            )
        ''')
        
    def test_insert_returns_id(self):
        user_id = self.repo.insert(name='John', email='john@test.com')
        self.assertIsInstance(user_id, int)
        
    def test_insert_duplicate_email_fails(self):
        self.repo.insert(name='John', email='john@test.com')
        
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.insert(name='Jane', email='john@test.com')
            
    def test_get_all_returns_all_users(self):
        self.repo.insert(name='John', email='john@test.com')
        self.repo.insert(name='Jane', email='jane@test.com')
        
        users = self.repo.get_all()
        self.assertEqual(len(users), 2)
        
    def test_get_by_id_returns_user(self):
        user_id = self.repo.insert(name='John', email='john@test.com')
        
        user = self.repo.get_by_id(user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user['name'], 'John')
        
    def test_get_by_id_returns_none_for_missing(self):
        user = self.repo.get_by_id(999)
        self.assertIsNone(user)
        
    def test_update_modifies_user(self):
        user_id = self.repo.insert(name='John', email='john@test.com')
        
        self.repo.update(user_id, name='John Updated')
        
        user = self.repo.get_by_id(user_id)
        self.assertEqual(user['name'], 'John Updated')
        
    def test_delete_removes_user(self):
        user_id = self.repo.insert(name='John', email='john@test.com')
        
        self.repo.delete(user_id)
        
        user = self.repo.get_by_id(user_id)
        self.assertIsNone(user)
        
    def test_search_finds_matching_users(self):
        self.repo.insert(name='John Doe', email='john@test.com')
        self.repo.insert(name='Jane Doe', email='jane@test.com')
        
        results = self.repo.search('John')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'John Doe')
```

### 2.2 Service Layer Testing

```python
class UserServiceTest(unittest.TestCase):
    """Test service layer business logic"""
    
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.repo = UserRepository(self.conn)
        self.service = UserService(self.repo)
        
    def test_register_user_creates_user(self):
        user = self.service.register_user(
            name='John',
            email='john@test.com'
        )
        
        self.assertIsNotNone(user['id'])
        self.assertEqual(user['name'], 'John')
        
    def test_register_invalid_email_fails(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.register_user(
                name='John',
                email='invalid-email'
            )
        
        self.assertIn('email', str(ctx.exception))
        
    def test_register_short_name_fails(self):
        with self.assertRaises(ValueError):
            self.service.register_user(
                name='J',
                email='john@test.com'
            )
            
    def test_get_user_stats_returns_counts(self):
        self.repo.insert(name='User1', email='u1@test.com')
        self.repo.insert(name='User2', email='u2@test.com')
        
        stats = self.service.get_user_stats()
        
        self.assertEqual(stats['total_users'], 2)
        
    def test_deactivate_user_sets_inactive(self):
        user_id = self.repo.insert(name='John', email='john@test.com')
        
        self.service.deactivate_user(user_id)
        
        user = self.repo.get_by_id(user_id)
        # Check that user is marked inactive
        self.assertIsNotNone(user['deactivated_at'])
```

### 2.3 Query Testing

```python
class QueryTest(unittest.TestCase):
    """Test SQL queries directly"""
    
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self._create_test_data()
        
    def _create_test_data(self):
        self.conn.executescript('''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                total REAL,
                status TEXT,
                created_at TEXT
            );
            
            INSERT INTO orders (customer_id, total, status, created_at) VALUES
                (1, 100.00, 'completed', '2024-01-01'),
                (1, 50.00, 'pending', '2024-01-02'),
                (2, 75.00, 'completed', '2024-01-01'),
                (2, 200.00, 'completed', '2024-01-03');
        ''')
        self.conn.commit()
        
    def test_order_totals_by_customer(self):
        cursor = self.conn.execute('''
            SELECT customer_id, SUM(total) as total
            FROM orders
            GROUP BY customer_id
        ''')
        
        results = {row[0]: row[1] for row in cursor}
        
        self.assertEqual(results[1], 150.00)
        self.assertEqual(results[2], 275.00)
        
    def test_pending_order_count(self):
        cursor = self.conn.execute('''
            SELECT COUNT(*) FROM orders WHERE status = 'pending'
        ''')
        
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
    def test_join_customers_orders(self):
        cursor = self.conn.execute('''
            SELECT o.id, o.total, c.name as customer
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
        ''')
        
        results = list(cursor)
        self.assertGreater(len(results), 0)
```

---

## 3. Integration Testing

### 3.1 Multi-Component Testing

```python
class IntegrationTestCase(unittest.TestCase):
    """Test full application workflow"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'app.db')
        self.app = App(self.db_path)
        
    def tearDown(self):
        self.app.close()
        shutil.rmtree(self.temp_dir)
        
    def test_complete_order_workflow(self):
        # 1. Create user
        user = self.app.users.create(name='John', email='john@test.com')
        
        # 2. Create order
        order = self.app.orders.create(
            user_id=user['id'],
            items=[{'product': 'Widget', 'price': 10.00}]
        )
        
        # 3. Process order
        self.app.orders.process(order['id'])
        
        # 4. Verify order status
        updated_order = self.app.orders.get(order['id'])
        self.assertEqual(updated_order['status'], 'processed')
        
        # 5. Verify user stats
        stats = self.app.users.get_stats(user['id'])
        self.assertEqual(stats['total_orders'], 1)
```

### 3.2 Transaction Testing

```python
class TransactionTest(unittest.TestCase):
    """Test transaction behavior"""
    
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        
    def test_commit_persists_changes(self):
        self.conn.execute("CREATE TABLE test (id INTEGER)")
        self.conn.execute("BEGIN")
        self.conn.execute("INSERT INTO test VALUES (1)")
        self.conn.execute("COMMIT")
        
        cursor = self.conn.execute("SELECT * FROM test")
        self.assertEqual(len(list(cursor)), 1)
        
    def test_rollback_reverts_changes(self):
        self.conn.execute("CREATE TABLE test (id INTEGER)")
        self.conn.execute("INSERT INTO test VALUES (1)")
        self.conn.execute("BEGIN")
        self.conn.execute("INSERT INTO test VALUES (2)")
        self.conn.execute("ROLLBACK")
        
        cursor = self.conn.execute("SELECT * FROM test")
        results = list(cursor)
        
        # Only row 1 should exist
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 1)
        
    def test_partial_failure_rolls_back(self):
        self.conn.executescript('''
            CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance REAL);
            INSERT INTO accounts VALUES (1, 100), (2, 100);
        ''')
        
        with self.assertRaises(Exception):
            self.conn.executescript('''
                BEGIN;
                UPDATE accounts SET balance = balance - 50 WHERE id = 1;
                -- Invalid operation that will fail
                UPDATE accounts SET balance = balance + 50 WHERE id = 999;
                COMMIT;
            ''')
        
        # Verify original values
        cursor = self.conn.execute("SELECT id, balance FROM accounts ORDER BY id")
        results = list(cursor)
        self.assertEqual(results[0][1], 100)
        self.assertEqual(results[1][1], 100)
```

### 3.3 Foreign Key Testing

```python
class ForeignKeyTest(unittest.TestCase):
    """Test foreign key constraints"""
    
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute("PRAGMA foreign_keys = ON")
        
    def test_parent_delete_cascades(self):
        self.conn.executescript('''
            CREATE TABLE parent (id INTEGER PRIMARY KEY);
            CREATE TABLE child (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER REFERENCES parent(id) ON DELETE CASCADE
            );
            INSERT INTO parent VALUES (1);
            INSERT INTO child VALUES (1, 1);
        ''')
        
        self.conn.execute("DELETE FROM parent WHERE id = 1")
        
        cursor = self.conn.execute("SELECT * FROM child")
        self.assertEqual(len(list(cursor)), 0)
        
    def test_parent_delete_set_null(self):
        self.conn.executescript('''
            CREATE TABLE parent (id INTEGER PRIMARY KEY);
            CREATE TABLE child (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER REFERENCES parent(id) ON DELETE SET NULL
            );
            INSERT INTO parent VALUES (1);
            INSERT INTO child VALUES (1, 1);
        ''')
        
        self.conn.execute("DELETE FROM parent WHERE id = 1")
        
        cursor = self.conn.execute("SELECT parent_id FROM child")
        row = cursor.fetchone()
        self.assertIsNone(row[0])
        
    def test_violation_prevents_insert(self):
        self.conn.executescript('''
            CREATE TABLE parent (id INTEGER PRIMARY KEY);
            CREATE TABLE child (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER REFERENCES parent(id)
            );
            INSERT INTO parent VALUES (1);
        ''')
        
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO child VALUES (1, 999)")
```

---

## 4. Debugging Techniques

### 4.1 EXPLAIN and EXPLAIN QUERY PLAN

```python
def debug_query(conn, query, params=None):
    """Debug query using EXPLAIN"""
    
    # Explain query plan
    plan = conn.execute(f"EXPLAIN QUERY PLAN {query}", params or [])
    print("Query Plan:")
    for row in plan:
        print(f"  {row}")
    
    # Explain (detailed)
    explained = conn.execute(f"EXPLAIN {query}", params or [])
    print("\nExplained:")
    for row in explained:
        print(f"  {row}")

# Usage
debug_query(conn, "SELECT * FROM users WHERE email = ?", ('john@test.com',))

# Output example:
# Query Plan:
#   SEARCH TABLE users USING INDEX idx_email (email=?)
# vs
#   SCAN TABLE users
```

### 4.2 Trace SQL Operations

```python
import sqlite3
import time

class TracingCursor(sqlite3.Cursor):
    """Cursor that traces all operations"""
    
    def execute(self, sql, parameters=None):
        start = time.time()
        result = super().execute(sql, parameters or [])
        elapsed = time.time() - start
        
        if elapsed > 0.1:  # Log slow queries
            print(f"SLOW QUERY ({elapsed:.3f}s): {sql[:100]}...")
            
        return result
        
    def executemany(self, sql, seq_of_parameters):
        start = time.time()
        result = super().executemany(sql, seq_of_parameters)
        elapsed = time.time() - start
        
        print(f"BATCH ({len(seq_of_parameters)} rows, {elapsed:.3f}s): {sql[:50]}...")
        
        return result

# Use tracing cursor
conn = sqlite3.connect('mydb.sqlite')
conn.set_trace_callback(print)
# Or use custom cursor
conn.execute("PRAGMA trace = 1")
```

### 4.3 Debug PRAGMA

```python
def debug_database(conn):
    """Print database statistics for debugging"""
    
    print("=== Database Statistics ===")
    
    # Page info
    result = conn.execute("PRAGMA page_count")
    print(f"Pages: {result.fetchone()[0]}")
    
    result = conn.execute("PRAGMA page_size")
    print(f"Page size: {result.fetchone()[0]}")
    
    result = conn.execute("PRAGMA freelist_count")
    print(f"Free pages: {result.fetchone()[0]}")
    
    # Schema
    print("\n=== Tables ===")
    cursor = conn.execute(
        "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'index') ORDER BY type, name"
    )
    for row in cursor:
        print(f"  {row[1]}: {row[0]}")
        
    # Index info
    print("\n=== Indexes ===")
    for table in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        indexes = conn.execute(f"PRAGMA index_list({table[0]})")
        for idx in indexes:
            print(f"  {table[0]}: {idx}")
            
    # Table info
    print("\n=== Table Details ===")
    for table in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        info = conn.execute(f"PRAGMA table_info({table[0]})")
        print(f"\n{table[0]}:")
        for col in info:
            print(f"  {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}")
```

---

## 5. Performance Profiling

### 5.1 Query Performance

```python
import time

class QueryProfiler:
    """Profile query performance"""
    
    def __init__(self, conn):
        self.conn = conn
        self.stats = []
        
    def profile(self, query, params=None, iterations=1):
        """Profile a query"""
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            result = self.conn.execute(query, params or []).fetchall()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        self.stats.append({
            'query': query[:100],
            'avg': avg_time,
            'min': min_time,
            'max': max_time,
            'rows': len(result)
        })
        
        print(f"Query: {query[:50]}...")
        print(f"  Avg: {avg_time*1000:.2f}ms, Min: {min_time*1000:.2f}ms, Max: {max_time*1000:.2f}ms")
        
        return result
        
    def report(self):
        """Print performance report"""
        print("\n=== Query Performance Report ===")
        print(f"{'Query':<50} {'Avg ms':<10} {'Rows':<6}")
        print("-" * 70)
        
        for stat in sorted(self.stats, key=lambda x: x['avg'], reverse=True):
            print(f"{stat['query']:<50} {stat['avg']*1000:>6.2f}  {stat['rows']:<6}")

# Usage
profiler = QueryProfiler(conn)
profiler.profile("SELECT * FROM users WHERE id > ?", (1000,), 10)
profiler.profile("SELECT * FROM users WHERE email = ?", ('test@test.com',), 10)
profiler.report()
```

### 5.2 Index Analysis

```python
def analyze_indexes(conn):
    """Analyze index usage and effectiveness"""
    
    print("=== Index Analysis ===\n")
    
    # Get all tables
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    
    for (table,) in tables:
        print(f"\nTable: {table}")
        
        # Get table size
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  Rows: {count}")
        
        # Get indexes
        indexes = conn.execute(f"PRAGMA index_list({table})").fetchall()
        print(f"  Indexes: {len(indexes)}")
        
        for idx in indexes:
            print(f"    - {idx[2]} (unique: {idx[1]})")
            
            # Get index columns
            info = conn.execute(f"PRAGMA index_info({idx[1]})").fetchall()
            cols = [i[2] for i in info]
            print(f"      Columns: {', '.join(cols)}")
            
        # Analyze query plan for common patterns
        # Check if queries could use indexes
```

---

## 6. Memory Debugging

### 6.1 Memory Profiling

```python
import gc
import sys

def get_memory_usage():
    """Get current memory usage"""
    return sys.getsizeof(gc.get_objects())

class MemoryProfiler:
    """Profile memory usage of database operations"""
    
    def __init__(self, conn):
        self.conn = conn
        self.snapshots = []
        
    def snapshot(self, label):
        """Take memory snapshot"""
        import tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            
        current, peak = tracemalloc.get_traced_memory()
        self.snapshots.append({
            'label': label,
            'current': current,
            'peak': peak
        })
        
    def report(self):
        """Print memory report"""
        print("=== Memory Report ===")
        for snap in self.snapshots:
            print(f"{snap['label']}: {snap['current']/1024:.1f}KB current, {snap['peak']/1024:.1f}KB peak")
            
        if len(self.snapshots) > 1:
            delta = self.snapshots[-1]['current'] - self.snapshots[0]['current']
            print(f"\nDelta: {delta/1024:.1f}KB")
```

### 6.2 Large Result Handling

```python
# Avoid loading all results into memory
def iterate_results(conn, query, batch_size=1000):
    """Iterate results in batches to avoid memory issues"""
    
    conn.execute(query)
    while True:
        rows = conn.fetchmany(batch_size)
        if not rows:
            break
        for row in rows:
            yield row
            
# Usage
for row in iterate_results(conn, "SELECT * FROM large_table"):
    process(row)
    
# Or use limit/offset for manual batching
def batch_query(conn, table, batch_size=1000):
    offset = 0
    while True:
        rows = conn.execute(
            f"SELECT * FROM {table} LIMIT {batch_size} OFFSET {offset}"
        ).fetchall()
        
        if not rows:
            break
            
        for row in rows:
            yield row
            
        offset += batch_size
```

---

## 7. Corruption Detection

### 7.1 Integrity Check

```python
def check_database_integrity(conn):
    """Run integrity checks on database"""
    
    print("=== Integrity Check ===")
    
    # Quick check
    result = conn.execute("PRAGMA quick_check").fetchone()
    print(f"Quick check: {result[0]}")
    
    # Full check
    result = conn.execute("PRAGMA integrity_check").fetchone()
    print(f"Full check: {result[0]}")
    
    if result[0] != 'ok':
        # Get detailed errors
        errors = conn.execute("PRAGMA integrity_check(10)").fetchall()
        for error in errors:
            print(f"  Error: {error[0]}")
            
    # Foreign key check
    result = conn.execute("PRAGMA foreign_key_check").fetchall()
    if result:
        print("Foreign key violations:")
        for error in result:
            print(f"  {error}")
            
    return result[0] == 'ok'
```

### 7.2 Recovery Strategies

```python
def recover_database(db_path):
    """Attempt database recovery"""
    
    import shutil
    
    print(f"Attempting recovery for {db_path}")
    
    # 1. Create backup
    backup_path = db_path + ".corrupted"
    shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    
    try:
        # 2. Run integrity check
        result = conn.execute("PRAGMA integrity_check").fetchone()
        print(f"Integrity: {result[0]}")
        
        if result[0] != 'ok':
            # 3. Export data to SQL
            with open(db_path + ".sql", 'w') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
                    
            print("Exported SQL dump")
            
            # 4. Try to recover via export/import
            conn.close()
            
            # Create new database
            new_db_path = db_path + ".new"
            new_conn = sqlite3.connect(new_db_path)
            
            with open(db_path + ".sql", 'r') as f:
                new_conn.executescript(f.read())
                
            new_conn.close()
            
            # Replace old with new
            shutil.move(db_path, backup_path)
            shutil.move(new_db_path, db_path)
            
            print("Recovery complete")
            
    except Exception as e:
        print(f"Recovery failed: {e}")
        
    finally:
        conn.close()
```

---

## 8. Logging

### 8.1 SQLite Logging

```sql
-- Enable various logging

-- Query logging via debug trace
PRAGMA temp_store = FILE;

-- Database lock debugging
PRAGMA locking_mode = NORMAL;

-- For SQLite CLI:
-- .timer on
-- Show execution time for each query

-- .explain on
-- Show query plan in human-readable format
```

### 8.2 Application Logging

```python
import logging
import sqlite3
from datetime import datetime

class LoggingConnection:
    """Connection wrapper that logs all operations"""
    
    def __init__(self, connection):
        self._conn = connection
        self.logger = logging.getLogger('sqlite')
        
    def execute(self, sql, params=None):
        self.logger.debug(f"Executing: {sql[:100]}...")
        start = time.time()
        
        result = self._conn.execute(sql, params or [])
        
        elapsed = time.time() - start
        self.logger.debug(f"Completed in {elapsed:.3f}s")
        
        return result
        
    def __getattr__(self, attr):
        return getattr(self._conn, attr)
        
# Usage
logging.basicConfig(level=logging.DEBUG)
conn = LoggingConnection(sqlite3.connect('mydb.sqlite'))
```

---

## 9. Benchmarking

### 9.1 Benchmark Suite

```python
import time
import random

class Benchmark:
    """Benchmark SQLite operations"""
    
    def __init__(self, conn):
        self.conn = conn
        self.results = {}
        
    def bench(self, name, fn, iterations=100):
        """Run benchmark"""
        times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            fn()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            
        avg = sum(times) / len(times)
        min_t = min(times)
        max_t = max(times)
        
        self.results[name] = {
            'avg': avg,
            'min': min_t,
            'max': max_t,
            'ops': iterations
        }
        
        print(f"{name}: {avg*1000:.2f}ms avg ({min_t*1000:.2f}-{max_t*1000:.2f}ms)")
        
    def report(self):
        """Print final report"""
        print("\n=== Benchmark Results ===")
        for name, result in sorted(self.results.items(), key=lambda x: x[1]['avg']):
            print(f"{name}: {result['avg']*1000:.2f}ms")

# Run benchmarks
bench = Benchmark(conn)

# Insert benchmark
data = [{'id': i, 'name': f'User{i}'} for i in range(1000)]

def insert_bench():
    for d in data[:100]:
        conn.execute("INSERT INTO users (name) VALUES (?)", (d['name'],))

bench.bench("Single inserts", insert_bench, 10)

# Batch insert
def batch_insert():
    conn.executemany("INSERT INTO users (name) VALUES (?)", 
                     [(f"User{i}",) for i in range(100)])

bench.bench("Batch insert", batch_insert, 10)

# Query benchmarks
bench.bench("Full scan", lambda: conn.execute("SELECT * FROM users").fetchall(), 100)
bench.bench("Indexed query", lambda: conn.execute("SELECT * FROM users WHERE id = 500").fetchall(), 100)

bench.report()
```

---

## 10. CI/CD Integration

### 10.1 Test Configuration

```yaml
# .github/workflows/test.yml
name: SQLite Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Run tests
        run: |
          pip install pytest pytest-cov
          pytest tests/ --cov=src --cov-report=xml
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 10.2 Docker Test Environment

```dockerfile
# Dockerfile for testing
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["pytest", "tests/"]
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*