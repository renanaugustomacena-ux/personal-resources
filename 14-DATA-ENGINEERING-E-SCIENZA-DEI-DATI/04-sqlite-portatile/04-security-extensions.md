# SQLite: Security, Extensions e Sviluppo Avanzato

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Security Model
2. Encryption and Secure Storage
3. Access Control
4. SQL Injection Prevention
5. Extensions System
6. Virtual Tables
7. Custom Functions
8. Custom Aggregates
9. Application Development
10. Performance e Best Practices

---

## 1. Security Model

### 1.1 SQLite Security Overview

SQLite è un database embedded senza auth nativa. La sicurezza è gestita a livello filesystem:

```sql
-- No built-in user authentication
-- No GRANT/REVOKE system
-- File permissions control access

-- Database file should have:
-- - Owner: application user
-- - Mode: 0600 (read/write owner only)
```

### 1.2 Security Architecture

```c
// SQLite security model:
// 1. File system level: owner/permissions
// 2. Application level: access control logic
// 3. Optional: encryption layer (SQLCipher)

// Non ha concetti di:
// - Users
// - Roles
// - GRANT/REVOKE
// - Row-level security
// - Column-level security
```

### 1.3 Threat Model

```sql
-- SQLite è progettato per:
-- - Accesso locale (single-user)
-- - Applicazioni trusted
-- - dati non sensibili per default

-- NON è progettato per:
-- - Multi-user con auth
-- - Hostile environments
-- - Network-facing databases
-- - Regulatory compliance (HIPAA, PCI, etc.)
```

### 1.4 File Permissions Best Practices

```bash
# Ownership
chown appuser:appgroup mydatabase.db
chown appuser:appgroup mydatabase.db-wal
chown appuser:appgroup mydatabase.db-shm

# Permissions - owner only
chmod 600 mydatabase.db
chmod 600 mydatabase.db-wal
chmod 600 mydatabase.db-shm

# Directory permissions
chmod 700 /path/to/database/
# Prevents listing contents by other users

# Read-only database
chmod 400 mydatabase.db
```

### 1.5 Directory Security

```bash
# Database directory should be protected
ls -la /var/lib/myapp/
# drwx------ 2 appuser appgroup 4096 May  4 10:00 mydb.db
# drwx------ 2 appuser appgroup 4096 May  4 10:00 mydb.db-wal
# drwx------ 2 appuser appgroup 4096 May  4 10:00 mydb.db-shm

# App directory
chmod 755 /var/www/myapp/  # web server can read
# But database in subdirectory with 700
```

---

## 2. Encryption and Secure Storage

### 2.1 SQLCipher Overview

SQLCipher è una build di SQLite con crittografia AES-256:

```c
// Compilare SQLite con SQLCipher
// https://www.zetetic.net/sqlcipher/

// Open encrypted database
sqlite3_open("encrypted.db", &db);

// Set key
sqlite3_key(db, "your-encryption-key", key_len);

// Or via PRAGMA
PRAGMA key = 'encryption_key';
```

### 2.2 SQLCipher in Practice

```python
# Python con sqlcipher
import sqlite3

# Connection con SQLCipher
conn = sqlite3.connect('encrypted.db')
conn.execute("PRAGMA key = 'my-secret-key'")

# Verify encryption is working
conn.execute("SELECT count(*) FROM sqlite_master")

# Attach encrypted database
conn.execute("ATTACH DATABASE 'other.db' AS encrypted KEY 'key2'")

# Detach
conn.execute("DETACH DATABASE encrypted")
```

### 2.3 Encryption Key Management

```python
# NON-hardcode keys in source!
# BAD:
key = "my-secret-key"  # NEVER DO THIS

# GOOD: Environment variables
import os
key = os.environ.get('DB_ENCRYPTION_KEY')
if not key:
    raise ValueError("DB_ENCRYPTION_KEY not set")

# GOOD: Key derivation from password
import hashlib
import base64
def derive_key(password: str, salt: bytes) -> str:
    """Derive encryption key from password"""
    key = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode(), 
        salt, 
        100000,
        dklen=32
    )
    return base64.b64encode(key).decode()

# GOOD: Key management service
# Use AWS KMS, HashiCorp Vault, etc.
```

### 2.4 SQLCipher Performance

```sql
-- Performance impact:
-- - ~5-15% slower on writes
-- - ~5-10% slower on reads
-- - Memory usage slightly higher

-- Benchmark:
PRAGMA cipher_page_size = 4096;
PRAGMA kdf_iter = 256000;
PRAGMA cipher_hmac_algorithm = HMAC_SHA512;
PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;
```

### 2.5 Alternative Encryption

```sql
-- Transparent Data Encryption (TDE) at OS level
-- Linux: dm-crypt/LUKS
-- macOS: FileVault
-- Windows: BitLocker

-- Filesystem encryption
-- ZFS encryption
-- APFS encryption

-- Application-level encryption
-- Encrypt specific columns
SELECT hex(encrypt(credit_card, key)) FROM customers;
-- Store encrypted blobs
```

### 2.6 Data at Rest Verification

```sql
-- Verify encryption
PRAGMA cipher_provider;

-- Check if database is encrypted
-- Can't easily tell from file
-- Use: sqlite3_encryption_status(db)

-- Integrity check
PRAGMA integrity_check;
```

---

## 3. Access Control

### 3.1 Application-Level Security

```python
# Python: validate all input
def get_user(user_id):
    if not isinstance(user_id, int):
        raise ValueError("Invalid user ID")
    if user_id < 1 or user_id > 999999999:
        raise ValueError("User ID out of range")
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()
```

### 3.2 Read-Only Database

```sql
-- Open in read-only mode
PRAGMA query_only = ON;

-- Check if readonly
PRAGMA query_only;  -- returns 1 if readonly

-- In code
conn.execute("PRAGMA query_only = ON");
```

### 3.3 Multi-Tenant Isolation

```sql
-- Isolation by tenant column
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    ...
);

-- Always filter by tenant
SELECT * FROM orders WHERE tenant_id = ?;

-- View per tenant
CREATE VIEW my_orders AS
SELECT * FROM orders WHERE tenant_id = current_tenant_id;
```

### 3.4 Role-Based Access (Application Layer)

```python
class User:
    def __init__(self, roles):
        self.roles = roles
    
    def can_read(self, table):
        return 'read' in self.roles.get(table, [])
    
    def can_write(self, table):
        return 'write' in self.roles.get(table, [])

# Usage
def query(user, sql, params):
    if not user.can_read('orders'):
        raise PermissionError("Cannot read orders")
    return cursor.execute(sql, params)
```

### 3.5 Audit Logging

```sql
-- Create audit trail
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    action TEXT,  -- SELECT, INSERT, UPDATE, DELETE
    table_name TEXT,
    record_id INTEGER,
    old_data TEXT,
    new_data TEXT,
    ip_address TEXT
);

-- Trigger per INSERT
CREATE TRIGGER audit_orders_insert AFTER INSERT ON orders
BEGIN
    INSERT INTO audit_log (user_id, action, table_name, record_id, new_data)
    VALUES (current_user_id, 'INSERT', 'orders', NEW.id, json(NEW));
END;

-- Trigger per UPDATE
CREATE TRIGGER audit_orders_update AFTER UPDATE ON orders
BEGIN
    INSERT INTO audit_log (user_id, action, table_name, record_id, old_data, new_data)
    VALUES (current_user_id, 'UPDATE', 'orders', OLD.id, json(OLD), json(NEW));
END;
```

---

## 4. SQL Injection Prevention

### 4.1 Parameterized Queries

```python
# WRONG - SQL injection vulnerable
user_input = "'; DROP TABLE users; --"
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")

# CORRECT - parameterized
user_input = "'; DROP TABLE users; --"
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))
# Output: SELECT * FROM users WHERE name = ?
# Parameter bound as literal string, not executed

# Multiple parameters
cursor.execute(
    "SELECT * FROM users WHERE name = ? AND status = ?",
    (user_input, 'active')
)
```

### 4.2 Parameter Types

```sql
-- Bind con cast esplicito
SELECT * FROM users WHERE id = CAST(? AS INTEGER);
SELECT * FROM products WHERE price = CAST(? AS REAL);

-- Date handling
SELECT * FROM orders WHERE date >= CAST(? AS TEXT);
-- Or use SQLite date functions
cursor.execute(
    "SELECT * FROM orders WHERE date >= date(?)",
    (date_string,)
)
```

### 4.3 Input Validation

```sql
-- Whitelist allowed values
SELECT * FROM status 
WHERE value IN ('active', 'inactive', 'pending');

-- Use CASE per forzare valori
SELECT * FROM orders
WHERE status = CASE 
    WHEN ? IN ('active','pending','completed') THEN ?
    ELSE 'unknown'
END;

-- Length limits
SELECT * FROM users 
WHERE name = substr(?, 1, 100);  -- truncate to 100 chars

-- Sanitize for LIKE
-- Escape special characters
def sanitize_like(s):
    return s.replace('%', r'\%').replace('_', r'\_')

cursor.execute(
    "SELECT * FROM users WHERE name LIKE ? || '%'",
    (sanitize_like(prefix),)
)
```

### 4.4 String Concatenation Patterns

```sql
-- EVITARE:
-- "SELECT * FROM " + table_name  -- table name injection!

-- Se table name dinamico necessario:
def safe_table_name(name):
    allowed = {'users', 'orders', 'products'}
    if name not in allowed:
        raise ValueError(f"Invalid table: {name}")
    return name

-- NEVER concatenate user input into SQL
-- Use parameterized for data, whitelist for identifiers
```

### 4.5 Injection Detection

```python
# Log potential injection attempts
import logging

def execute_safe(sql, params):
    suspicious = ['DROP', 'DELETE FROM', 'TRUNCATE', '--', ';--']
    sql_upper = sql.upper()
    for pattern in suspicious:
        if pattern in sql_upper:
            logging.warning(
                f"Potential SQL injection: {sql[:100]}"
            )
    return cursor.execute(sql, params)
```

---

## 5. Extensions System

### 5.1 Load Extension

```sql
-- Load extension
.load extension_name

-- On Linux/Unix
.load /usr/lib/sqlite3/pcre.so

-- On Windows
.load pcre

-- Check loaded extensions
PRAGMA compile_options;
```

### 5.2 Extension Types

```sql
-- Compile-time extensions
-- Runtime loaded:
-- - .so (Linux)
-- - .dll (Windows)
-- - .dylib (macOS)

-- Extensions included:
-- - FTS5 (full-text search)
-- - JSON1 (JSON)
-- - RTREE (spatial)
-- - STAT4 (statistics)
-- - CSV (CSV file import)
-- - Math (math functions)
```

### 5.3 Extension Security

```sql
-- ! SECURITY WARNING !
-- Loading extensions can be dangerous

-- Disable extension loading in production
PRAGMA trusted_schema = 0;

-- Check if extensions are loaded
PRAGMA extension_list;

-- Only load verified extensions
```

### 5.4 Built-in Extensions

```sql
-- FTS5 - Full-text search
PRAGMA compile_options LIKE '%FTS%';

-- JSON
PRAGMA compile_options LIKE '%JSON%';

-- RTREE (spatial index)
PRAGMA compile_options LIKE '%RTREE%';

-- Enable at compile time:
-- -DSQLITE_ENABLE_FTS5
-- -DSQLITE_ENABLE_JSON1
-- -DSQLITE_ENABLE_RTREE
```

### 5.5 Loading Extensions in Code

```python
# Python: load extension
conn = sqlite3.connect('db.sqlite')

# Load extension
conn.enable_load_extension(True)
conn.load_extension('my_extension')

# Or: load from path
conn.load_extension('/usr/lib/sqlite3/pcre.so')

# Disable loading
conn.enable_load_extension(False)
```

---

## 6. Virtual Tables

### 6.1 Virtual Table Overview

Virtual tables sono tabelle la cui implementazione è definita da un modulo:

```sql
-- FTS5 virtual table
CREATE VIRTUAL TABLE articles USING fts5(title, content);

-- RTREE for spatial
CREATE VIRTUAL TABLE points USING rtree(id, x, y);

-- JSON extension
CREATE VIRTUAL TABLE json USING json_each('[]');

-- CSV virtual table (requires extension)
CREATE VIRTUAL TABLE data USING csv(filename='data.csv');
```

### 6.2 FTS5 Virtual Table

```sql
-- Create FTS5 table with options
CREATE VIRTUAL TABLE search_index USING fts5(
    title,
    content,
    author,
    tokenize='porter',  -- stemming
    content='',         -- content table
    tokenize='unicode61',
    prefix='2 3 4 5',   -- prefix indexes
    columnsize=0        -- don't store size
);

-- Insert data
INSERT INTO search_index (title, content, author)
VALUES ('SQLite Tutorial', 'Learn to use SQLite', 'John');

-- Search
SELECT * FROM search_index WHERE search_index MATCH 'SQLite';

-- Rebuild
INSERT INTO search_index(search_index) VALUES('rebuild');

-- Optimize
INSERT INTO search_index(search_index) VALUES('optimize');
```

### 6.3 RTREE Virtual Table

```sql
-- Spatial index
CREATE VIRTUAL TABLE locations USING rtree(
    id,
    min_x, max_x,
    min_y, max_y,
    min_z, max_z
);

-- Insert spatial data
INSERT INTO locations VALUES (
    1,          -- id
    40.7, 40.8, -- lat min, max  
    -74.0, -73.9 -- lon min, max
);

-- Query with containment
SELECT * FROM locations 
WHERE min_x >= 40.75 AND max_x <= 40.85
  AND min_y >= -74.0 AND max_y <= -73.8;

-- Query with overlap
SELECT * FROM locations 
WHERE max_x >= 40.75 AND min_x <= 40.85
  AND max_y >= -74.0 AND min_y <= -73.8;
```

### 6.4 JSON Virtual Table

```sql
-- Parse JSON array to table
SELECT * FROM JSON_EACH('[1,2,3]');
-- key | value | type
-- 0     1       integer
-- 1     2       integer
-- 2     3       integer

-- Parse JSON object
SELECT * FROM JSON_EACH('{"a":1,"b":2}');
-- key | value | type
-- a      1      integer
-- b      2      integer

-- Recursive (JSON_TREE)
SELECT * FROM JSON_TREE('{"a":[1,2,3]}');
-- node | type | key | value | atom | parent | path
```

### 6.5 Module Examples

```sql
-- URL table (requires extension)
CREATE VIRTUAL TABLE remote USING http('http://example.com/data');

-- File-based virtual table
CREATE VIRTUAL TABLE csv_data USING csv(
    filename='data.csv',
    header=TRUE,
    columns=3
);

-- Geopoly for polygons (requires extension)
CREATE VIRTUAL TABLE areas USING geopoly(
    id,
    name,
    coords
);
```

### 6.6 Custom Virtual Tables

```c
// Create custom virtual table in C
// Implement xCreate, xConnect, xBestIndex, xFilter, etc.
// Example: read from network, API, etc.

// Python: use sqlite3.create_module()
```

---

## 7. Custom Functions

### 7.1 Create Function in C

```c
// SQLite create function
sqlite3_create_function(
    db, 
    "my_function",    // function name
    1,                // number of arguments
    SQLITE_UTF8,     // encoding
    NULL,            // user data
    my_func,         // function implementation
    NULL,            // step function
    NULL             // finalize function
);

// Simple function
void my_func(sqlite3_context *ctx, int argc, sqlite3_value **argv) {
    const char *str = (const char*)sqlite3_value_text(argv[0]);
    // Process string
    sqlite3_result_text(ctx, result, -1, SQLITE_TRANSIENT);
}
```

### 7.2 Python Custom Function

```python
# SQLite in Python
import sqlite3
import hashlib

def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()

conn = sqlite3.connect('db.sqlite')

# Register functions
conn.create_function("md5", 1, md5_hash)
conn.create_function("sha256", 1, sha256)

# Use in queries
cursor.execute("SELECT md5('hello')")
cursor.execute("SELECT sha256(password) FROM users WHERE id = ?", (user_id,))

# Function with multiple args
def regex_match(pattern, text):
    import re
    return 1 if re.search(pattern, text) else 0

conn.create_function("REGEXP", 2, regex_match)

# Use: SELECT * FROM data WHERE REGEXP('pattern', text)
```

### 7.3 Custom Functions with Types

```python
# Function with specific type handling
def parse_date(date_str):
    from datetime import datetime
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None

conn.create_function("PARSE_DATE", 1, parse_date, deterministic=True)

# Deterministic functions can be used in indexes
```

### 7.4 Aggregate Functions (User-Defined)

```python
# Aggregate function in Python
import sqlite3

class Median:
    def __init__(self):
        self.values = []
    
    def step(self, value):
        if value is not None:
            self.values.append(value)
    
    def finalize(self):
        if not self.values:
            return None
        sorted_vals = sorted(self.values)
        n = len(sorted_vals)
        if n % 2 == 0:
            return (sorted_vals[n//2-1] + sorted_vals[n//2]) / 2
        else:
            return sorted_vals[n//2]

conn.create_aggregate("median", 1, Median)

# Use
cursor.execute("SELECT median(price) FROM products")

# More complex aggregate
class Mode:
    def __init__(self):
        self.counts = {}
    
    def step(self, value):
        if value is not None:
            self.counts[value] = self.counts.get(value, 0) + 1
    
    def finalize(self):
        if not self.counts:
            return None
        return max(self.counts.items(), key=lambda x: x[1])[0]

conn.create_aggregate("mode", 1, Mode)
```

### 7.5 Window Functions (User-Defined)

```python
# Window function in Python (SQLite 3.38+)
def running_sum(values):
    total = 0
    for v in values:
        total += v if v else 0
        yield total

# Register as window function
conn.create_window_function("running_sum", 1, running_sum, None)
```

### 7.6 Advanced Custom Functions

```python
# Function returning multiple values (table-valued)
def split_text(text, delimiter=','):
    for part in text.split(delimiter):
        yield (part.strip(),)

# Create table function
conn.create_function("split", -1, split_text, deterministic=True)

# Use as table-valued function
# SELECT * FROM split('a,b,c', ',')

# More complex: JSON generator
def to_json(rows):
    import json
    return json.dumps(rows)

conn.create_function("TO_JSON", 1, to_json)
```

---

## 8. Custom Aggregates

### 8.1 Custom Aggregate in C

```c
// Aggregate function structure
typedef struct {
    int sum;
    int count;
} SumCtx;

// Step function
static void sumStep(sqlite3_context *ctx, int argc, sqlite3_value **argv) {
    SumCtx *data = sqlite3_aggregate_context(ctx, sizeof(SumCtx));
    if (data) {
        if (sqlite3_value_type(argv[0]) != SQLITE_NULL) {
            data->sum += sqlite3_value_int(argv[0]);
            data->count++;
        }
    }
}

// Final function
static void sumFinal(sqlite3_context *ctx) {
    SumCtx *data = sqlite3_aggregate_context(ctx, sizeof(SumCtx));
    if (data && data->count > 0) {
        sqlite3_result_double(ctx, (double)data->sum / data->count);
    } else {
        sqlite3_result_null(ctx);
    }
}

// Register
sqlite3_create_function(db, "avg_manual", 1, SQLITE_UTF8, NULL, NULL, sumStep, sumFinal);
```

### 8.2 Python Custom Aggregates

```python
# Standard aggregate
class SumAggregate:
    def __init__(self):
        self.total = 0
    
    def step(self, value):
        if value is not None:
            self.total += value
    
    def finalize(self):
        return self.total

conn.create_aggregate("sum_custom", 1, SumAggregate)

# More complex: standard deviation
class StdDev:
    def __init__(self):
        self.values = []
    
    def step(self, value):
        if value is not None:
            self.values.append(value)
    
    def finalize(self):
        if len(self.values) < 2:
            return None
        mean = sum(self.values) / len(self.values)
        variance = sum((x - mean)**2 for x in self.values) / len(self.values)
        return variance ** 0.5

conn.create_aggregate("stddev", 1, StdDev)

# Use
cursor.execute("SELECT stddev(price) FROM products")
```

### 8.3 String Aggregates

```python
# Custom GROUP_CONCAT
class GroupConcatDistinct:
    def __init__(self):
        self.seen = set()
        self.result = []
    
    def step(self, value, separator=','):
        if value is not None and value not in self.seen:
            self.seen.add(value)
            self.result.append(str(value))
    
    def finalize(self, separator=','):
        return separator.join(self.result)

conn.create_aggregate("group_concat_distinct", -1, GroupConcatDistinct)

# Use: SELECT group_concat_distinct(name, ' | ') FROM users
```

### 8.4 Statistical Aggregates

```python
import math

class Percentile:
    def __init__(self):
        self.values = []
    
    def step(self, value, percentile=50):
        if value is not None:
            self.values.append(value)
    
    def finalize(self, percentile=50):
        if not self.values:
            return None
        sorted_vals = sorted(self.values)
        n = len(sorted_vals)
        k = (percentile / 100) * (n - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1

conn.create_aggregate("percentile", 2, Percentile)

# Use: SELECT percentile(price, 25), percentile(price, 50), percentile(price, 75) FROM products
```

---

## 9. Application Development

### 9.1 Connection Management

```python
# Best practice: context manager
import sqlite3

with sqlite3.connect('mydb.sqlite') as conn:
    # Auto-commit on successful exit
    # Auto-rollback on exception
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()

# With settings
with sqlite3.connect(
    'mydb.sqlite',
    timeout=30,           # wait for lock
    isolation_level=None, # autocommit
    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
) as conn:
    pass
```

### 9.2 Connection Pooling

```python
# Simple connection pool
import sqlite3
import threading

class ConnectionPool:
    def __init__(self, db_path, pool_size=5):
        self.db_path = db_path
        self.pool = []
        self.lock = threading.Lock()
        
        # Pre-create connections
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            self.pool.append(conn)
    
    def get_connection(self):
        with self.lock:
            if self.pool:
                return self.pool.pop()
            return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def return_connection(self, conn):
        with self.lock:
            if len(self.pool) < 5:
                self.pool.append(conn)
            else:
                conn.close()

# Usage
pool = ConnectionPool('mydb.sqlite')
conn = pool.get_connection()
try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
finally:
    pool.return_connection(conn)
```

### 9.3 Transaction Management

```python
# Explicit transactions
conn = sqlite3.connect('mydb.sqlite')
try:
    cursor = conn.cursor()
    cursor.execute("BEGIN")
    cursor.execute("INSERT INTO orders ...")
    cursor.execute("INSERT INTO order_items ...")
    cursor.execute("COMMIT")
except Exception as e:
    cursor.execute("ROLLBACK")
    raise e

# With savepoints
conn.execute("BEGIN")
try:
    conn.execute("INSERT INTO log ...")
    # ...
    conn.execute("COMMIT")
except:
    conn.execute("ROLLBACK TO SAVEPOINT")
    raise
```

### 9.4 Error Handling

```sql
-- SQLite error codes
-- SQLITE_OK = 0
-- SQLITE_ERROR = 1
-- SQLITE_BUSY = 5
-- SQLITE_LOCKED = 6
-- SQLITE_NOMEM = 7
-- SQLITE_READONLY = 8
-- SQLITE_CANTOPEN = 14
-- SQLITE_CONSTRAINT = 19

-- Handle specific errors
try:
    cursor.execute("INSERT INTO ...")
except sqlite3.IntegrityError as e:
    # Constraint violation
    print(f"Constraint error: {e}")
except sqlite3.OperationalError as e:
    # Lock, I/O errors
    print(f"Operational error: {e}")
```

### 9.5 Type Handling

```python
# Custom type converters
import sqlite3
from datetime import datetime, date

def parse_date(s):
    if s:
        return datetime.strptime(s, '%Y-%m-%d').date()
    return None

def adapt_date(d):
    return d.strftime('%Y-%m-%d')

sqlite3.register_adapter(date, adapt_date)
sqlite3.register_converter('DATE', parse_date)

# Detect types
conn = sqlite3.connect(
    'mydb.sqlite',
    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
)
```

### 9.6 Thread Safety

```sql
-- Thread-safe mode
-- SQLite in serialized mode by default
-- One connection per thread recommended
-- Use connection pool for multi-threaded

-- Thread-local connections
import threading

local = threading.local()

def get_db():
    if not hasattr(local, 'db'):
        local.db = sqlite3.connect('mydb.sqlite')
    return local.db

# In threaded application:
# Each thread gets its own connection automatically
```

---

## 10. Performance e Best Practices

### 10.1 Query Optimization

```sql
-- Use EXPLAIN QUERY PLAN
EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = ?;

-- Create indexes for WHERE clauses
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_date ON orders(order_date);

-- Use covering indexes
CREATE INDEX idx_users_name_email ON users(name, email);
-- Then: SELECT name, email FROM users WHERE name = 'John'

-- Use PRAGMA optimize periodically
PRAGMA optimize;

-- Vacuum to reclaim space
VACUUM;
```

### 10.2 PRAGMA Settings for Performance

```sql
-- Cache
PRAGMA cache_size = -4000;  -- 4MB
PRAGMA page_size = 4096;

-- Synchronous
PRAGMA synchronous = NORMAL;  -- balance speed/safety

-- Journal mode
PRAGMA journal_mode = WAL;

-- Memory
PRAGMA temp_store = MEMORY;

-- mmap
PRAGMA mmap_size = 268435456;  -- 256MB
```

### 10.3 Best Practices Summary

```python
# BEST PRACTICES CHECKLIST:

# 1. Use parameterized queries
cursor.execute("SELECT * FROM users WHERE id = ?", (id,))

# 2. Use context managers
with sqlite3.connect('db.sqlite') as conn:
    ...

# 3. Use WAL mode
conn.execute("PRAGMA journal_mode = WAL")

# 4. Create appropriate indexes
CREATE INDEX idx ON table(col);

# 5. Use appropriate data types
-- Use INTEGER for IDs, REAL for decimals, TEXT for strings

# 6. Close connections
-- Use context manager or explicit close()

# 7. Handle errors appropriately
try:
    cursor.execute(...)
except sqlite3.Error as e:
    log.error(f"Database error: {e}")

# 8. Use transactions for multiple operations
with conn:
    cursor.execute("INSERT ...")
    cursor.execute("UPDATE ...")

# 9. Don't store sensitive data in plaintext
-- Use encryption (SQLCipher)
-- Encrypt specific columns

# 10. Regular maintenance
conn.execute("PRAGMA optimize")
conn.execute("VACUUM")
```

### 10.4 Security Checklist

```sql
-- SECURITY CHECKLIST:

-- 1. File permissions
chmod 600 database.db

-- 2. Use encryption for sensitive data
PRAGMA key = 'key';

-- 3. Use parameterized queries
-- NO string formatting!

-- 4. Validate input
-- Whitelist allowed values
-- Use CAST for types

-- 5. Disable extensions if not needed
PRAGMA trusted_schema = 0;

-- 6. Read-only mode when appropriate
PRAGMA query_only = ON;

-- 7. Audit logging for sensitive operations

-- 8. Keep SQLite updated
-- Security patches in new versions
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*