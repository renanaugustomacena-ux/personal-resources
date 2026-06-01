# SQLite: Best Practices e Produzione

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
1. Configuration Best Practices
2. Schema Design
3. Performance Optimization
4. Security Best Practices
5. Backup and Recovery
6. Monitoring
7. Deployment
8. Troubleshooting
9. Anti-Patterns
10. Production Checklist

---

## 1. Configuration Best Practices

### 1.1 Essential PRAGMAs

```sql
-- WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Normal synchronous for balance of speed/safety
PRAGMA synchronous = NORMAL;

-- Cache size (negative = KB, positive = pages)
PRAGMA cache_size = -4000;  -- 4MB

-- Temp store in memory
PRAGMA temp_store = MEMORY;

-- Memory-mapped I/O (adjust based on workload)
-- Read-heavy: larger
PRAGMA mmap_size = 268435456;  -- 256MB
-- Write-heavy: disable
PRAGMA mmap_size = 0;

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Recursive triggers
PRAGMA recursive_triggers = ON;
```

### 1.2 Connection Settings

```sql
-- Timeout for locked database (seconds)
PRAGMA busy_timeout = 5000;

-- Read uncommitted isolation level
-- Use only if needed (can get dirty reads)
PRAGMA read_uncommitted = 0;

-- Locking mode
-- NORMAL: release locks between transactions
-- EXCLUSIVE: hold locks
PRAGMA locking_mode = NORMAL;

-- Query only mode
PRAGMA query_only = OFF;
```

### 1.3 Performance Tuning

```sql
-- Optimize automatically (run periodically)
PRAGMA optimize;

-- Auto-checkpoint interval (default 1000)
PRAGMA wal_autocheckpoint = 1000;

-- Page size (set at database creation)
-- Default 4096 is fine for most cases
PRAGMA page_size = 4096;
```

---

## 2. Schema Design

### 2.1 Table Design

```sql
-- Primary keys: use INTEGER PRIMARY KEY AUTOINCREMENT
-- or INTEGER PRIMARY KEY for custom IDs

CREATE TABLE users (
    id INTEGER PRIMARY KEY,  -- or AUTOINCREMENT
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Avoid NULL when possible
-- Use DEFAULT for optional fields
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL DEFAULT 0,
    description TEXT,
    deleted_at TEXT  -- Soft delete
);

-- Use appropriate types
-- INTEGER for IDs, booleans, counts
-- REAL for money, measurements
-- TEXT for strings, dates (ISO8601)
-- BLOB for binary data
```

### 2.2 Index Design

```sql
-- Index foreign keys
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- Index frequently queried columns
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_price ON products(price);

-- Composite index for multi-column WHERE
CREATE INDEX idx_orders_status_date ON orders(status, order_date DESC);

-- Partial index for subset queries
CREATE INDEX idx_active_orders ON orders(order_date) 
WHERE status = 'active';

-- Covering index for SELECT
CREATE INDEX idx_user_email ON users(email, name)
WHERE id IS NOT NULL;
-- Now: SELECT email, name FROM users WHERE email = ?
-- avoids table lookup
```

### 2.3 Constraints

```sql
-- Use NOT NULL
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);

-- Use UNIQUE
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE
);

-- Foreign keys (enable first!)
PRAGMA foreign_keys = ON;

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    total REAL NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
        ON DELETE CASCADE  -- or RESTRICT, SET NULL
);

-- Check constraints (SQLite 3.37+)
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    price REAL CHECK(price >= 0),
    quantity INTEGER CHECK(quantity >= 0)
);
```

---

## 3. Performance Optimization

### 3.1 Query Optimization

```sql
-- Use EXPLAIN QUERY PLAN
EXPLAIN QUERY PLAN 
SELECT * FROM users WHERE email = 'john@example.com';

-- Avoid SELECT *
SELECT id, name, email FROM users;  -- Only needed columns

-- Use LIMIT for large result sets
SELECT * FROM large_table LIMIT 100;

-- Keyset pagination (efficient)
SELECT * FROM users WHERE id > ? ORDER BY id LIMIT 100;

-- Batch operations
INSERT INTO users (name) VALUES ('A'), ('B'), ('C');

-- Use transactions for bulk operations
BEGIN;
INSERT INTO logs VALUES ...;
INSERT INTO logs VALUES ...;
COMMIT;
```

### 3.2 Index Usage

```sql
-- Create appropriate indexes
-- For WHERE column = value
CREATE INDEX idx ON table(column);

-- For ORDER BY column
CREATE INDEX idx ON table(column);  -- Index covers ORDER BY

-- For range queries
CREATE INDEX idx ON table(date_column);

-- For composite queries
CREATE INDEX idx ON table(a, b, c);

-- Index column order matters!
-- For WHERE a = ? AND b = ?
-- Use (a, b), not (b, a)

-- Don't index:
-- - Low-cardinality columns (few unique values)
-- - Columns rarely used in WHERE/JOIN/ORDER BY
-- - Frequently updated columns (write penalty)
```

### 3.3 Application Optimization

```python
# Use connection pooling
import sqlite3

# Reuse statements
stmt = conn.prepare("SELECT * FROM users WHERE id = ?")
for user_id in user_ids:
    result = stmt.bind(user_id).execute()

# Use executemany for bulk
conn.executemany(
    "INSERT INTO users (name) VALUES (?)",
    [(name,) for name in names]
)

# Close connections when done
# Use context manager
with sqlite3.connect('db.sqlite') as conn:
    pass  # auto-closes
```

---

## 4. Security Best Practices

### 4.1 File Security

```bash
# Set file permissions
chmod 600 mydatabase.db
chmod 600 mydatabase.db-wal
chmod 600 mydatabase.db-shm

# Owner should be application user
chown appuser:appgroup mydatabase.db
```

### 4.2 Input Security

```python
# ALWAYS use parameterized queries
# BAD
query = f"SELECT * FROM users WHERE name = '{name}'"

# GOOD
query = "SELECT * FROM users WHERE name = ?"
cursor.execute(query, (name,))

# Validate input types
def get_user(user_id):
    if not isinstance(user_id, int):
        raise ValueError("Invalid ID")
    return cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### 4.3 Encryption

```python
# Use SQLCipher for encryption
import sqlite3
conn = sqlite3.connect('encrypted.db')
conn.execute("PRAGMA key = 'your-encryption-key'")

# Or use OS-level encryption
# - BitLocker (Windows)
# - FileVault (macOS)
# - dm-crypt (Linux)
```

### 4.4 Read-Only Mode

```python
# Open in read-only mode
conn = sqlite3.connect('file:db.sqlite?mode=ro', uri=True)

# Or PRAGMA
conn.execute("PRAGMA query_only = ON")
```

---

## 5. Backup and Recovery

### 5.1 Backup Methods

```python
# Online backup with API
import sqlite3

def backup_database(source_path, dest_path):
    source = sqlite3.connect(source_path)
    dest = sqlite3.connect(dest_path)
    
    backup = sqlite3_backup_init(dest, "main", source, "main")
    sqlite3_backup_step(backup, -1)  # All pages
    sqlite3_backup_finish(backup)
    
    source.close()
    dest.close()

# File copy (with checkpoint first)
import shutil

def file_backup(db_path, backup_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()
    
    shutil.copy2(db_path, backup_path)
    shutil.copy2(db_path + "-wal", backup_path + "-wal")
```

### 5.2 Recovery

```python
def recover_from_backup(backup_path, target_path):
    import shutil
    
    # Close current connection if open
    # Replace database
    shutil.copy2(backup_path, target_path)
    
    # Verify
    conn = sqlite3.connect(target_path)
    result = conn.execute("PRAGMA integrity_check").fetchone()
    conn.close()
    
    return result[0] == 'ok'
```

---

## 6. Monitoring

### 6.1 Database Statistics

```sql
-- Database size
SELECT 
    page_count * page_size / 1024 / 1024 as size_mb,
    page_size
FROM pragma_page_count(), pragma_page_size();

-- Table size
SELECT 
    name,
    page_count * page_size / 1024 as size_kb
FROM pragma_page_count(), pragma_master
WHERE type = 'table';

-- Index size
SELECT 
    name,
    idx_scan,
    idx_rows_read,
    table_scan
FROM pragma_index_list(table_name);

-- Query statistics
SELECT 
    sql,
    count,
    total_time,
    avg_time
FROM sqlite_stat1
ORDER BY count DESC;
```

### 6.2 Application Monitoring

```python
import time
import logging

class QueryMonitor:
    def __init__(self, logger):
        self.logger = logger
        
    def execute(self, query, params=None):
        start = time.time()
        try:
            result = cursor.execute(query, params or [])
            elapsed = time.time() - start
            
            if elapsed > 0.1:  # Log slow queries
                self.logger.warning(f"Slow query: {query[:50]}... took {elapsed:.3f}s")
                
            return result
        except Exception as e:
            self.logger.error(f"Query failed: {query[:50]}... Error: {e}")
            raise
```

---

## 7. Deployment

### 7.1 Environment Setup

```python
# Initialize database on startup
def init_database(db_path):
    conn = sqlite3.connect(db_path)
    
    # Enable WAL
    conn.execute("PRAGMA journal_mode = WAL")
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Create schema
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    conn.commit()
    conn.close()
```

### 7.2 Docker

```dockerfile
# Dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY app/ /app/

CMD ["python", "app.py"]
```

---

## 8. Troubleshooting

### 8.1 Common Issues

```sql
-- Database is locked
-- Solution: Use busy_timeout, use WAL mode

-- Slow queries
-- Solution: Add indexes, optimize queries

-- Database corruption
-- Solution: Restore from backup, run integrity_check

-- Out of disk space
-- Solution: VACUUM to reclaim space

-- Memory issues
-- Solution: Use LIMIT, iterate instead of fetchall
```

### 8.2 Debugging Steps

```python
def diagnose_slow_queries(conn):
    # 1. Check for missing indexes
    # 2. Check query plan
    # 3. Check table statistics
    
    # Enable timing
    conn.execute("PRAGMA timing = ON")
    
    # Run queries with timing
    
    # Check for full table scans
    # EXPLAIN QUERY PLAN
    
def diagnose_database(conn):
    # Check integrity
    result = conn.execute("PRAGMA integrity_check").fetchone()
    
    # Check page stats
    pages = conn.execute("PRAGMA page_count").fetchone()[0]
    freelist = conn.execute("PRAGMA freelist_count").fetchone()[0]
    
    print(f"Total pages: {pages}, Free: {freelist}")
    
    # Check for fragmentation
    # VACUUM if needed
```

---

## 9. Anti-Patterns

### 9.1 Don't Do This

```sql
-- Don't use SELECT * in production
SELECT * FROM users;  -- Specify columns

-- Don't use OFFSET for pagination
-- Use keyset pagination instead
-- BAD:
SELECT * FROM users LIMIT 10 OFFSET 100000;
-- GOOD:
SELECT * FROM users WHERE id > 100000 LIMIT 10;

-- Don't create too many indexes
-- Each index slows down writes

-- Don't store large blobs in SQLite
-- Use file system, store paths in DB

-- Don't use triggers for everything
-- They're harder to debug and maintain

-- Don't ignore WAL mode
-- It's better for concurrency
```

### 9.2 Common Mistakes

```python
# Not closing connections
conn = sqlite3.connect('db.sqlite')
# ... use ...
# conn.close()  # Missing!

# Not using transactions
for item in items:
    conn.execute("INSERT INTO ...");  # Each is a transaction!
# Use:
conn.execute("BEGIN")
for item in items:
    conn.execute("INSERT INTO ...")
conn.execute("COMMIT")

# Not handling exceptions
try:
    conn.execute("...")
except sqlite3.Error as e:
    pass  # Silent ignore!

# Using string formatting for queries
sql = f"SELECT * FROM {table_name}"  # SQL injection risk!
```

---

## 10. Production Checklist

### 10.1 Pre-Deployment

- [ ] Enable WAL mode
- [ ] Set appropriate PRAGMAs (cache_size, busy_timeout)
- [ ] Create necessary indexes
- [ ] Enable foreign keys
- [ ] Test with production data volume
- [ ] Set up backup strategy
- [ ] Configure monitoring

### 10.2 Security

- [ ] Set file permissions (600)
- [ ] Use parameterized queries everywhere
- [ ] Enable encryption if needed
- [ ] Use read-only mode for reporting
- [ ] No secrets in code

### 10.3 Performance

- [ ] Run EXPLAIN on critical queries
- [ ] Add missing indexes
- [ ] Optimize WAL checkpoint
- [ ] Set appropriate cache size
- [ ] Monitor slow queries

### 10.4 Operations

- [ ] Set up automated backups
- [ ] Test backup restore
- [ ] Monitor disk space
- [ ] Set up alerts for errors
- [ ] Schedule VACUUM if needed

### 10.5 Monitoring

- [ ] Track query performance
- [ ] Monitor database size
- [ ] Monitor disk usage
- [ ] Set up error logging

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*