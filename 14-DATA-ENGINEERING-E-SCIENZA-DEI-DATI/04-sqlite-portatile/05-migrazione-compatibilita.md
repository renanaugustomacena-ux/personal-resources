# SQLite: Migrazione, Compatibilità e Interoperabilità

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
1. Migration da Altri Database
2. SQLite Compatibility
3. Data Import/Export
4. Cross-Platform Considerations
5. Version Migration
6. Schema Migration
7. Data Transformation
8. Compatibility Layers
9. Interoperability Patterns

---

## 1. Migration da Altri Database

### 1.1 Da MySQL/MariaDB a SQLite

```sql
-- Creare dump MySQL
mysqldump -u root -p mydb > mydb.sql

-- Convertire con script
-- 1. Rimuovere auto_increment e usare autoincrement
-- 2. Convertire ENGINE=InnoDB a SQLite
-- 3. Rimuoveri FOREIGN KEY constraints

-- Esempio trasformazione:
-- MySQL:
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE
);

-- SQLite:
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT(100),
    email TEXT(255) UNIQUE
);
```

### 1.2 Da PostgreSQL a SQLite

```sql
-- Differenze chiave:
-- PostgreSQL: SERIAL -> SQLite: INTEGER PRIMARY KEY AUTOINCREMENT
-- PostgreSQL: TEXT -> SQLite: TEXT
-- PostgreSQL: BOOLEAN -> SQLite: INTEGER (0/1)
-- PostgreSQL: TIMESTAMP -> SQLite: TEXT (ISO8601)
-- PostgreSQL: JSONB -> SQLite: TEXT (JSON)
-- PostgreSQL: ARRAY -> SQLite: TEXT (comma-separated)

-- Convertire dump:
-- pg_dump -h localhost -U user dbname > dump.sql

-- Modifiche necessarie:
-- 1. Rimuovere CAST(...::type)
-- 2. Convertire array syntax
-- 3. Modificare serial columns
-- 4. Sostituire array_agg con group_concat
```

### 1.3 Da Oracle a SQLite

```sql
-- Oracle -> SQLite mappings:
-- NUMBER -> REAL o INTEGER
-- VARCHAR2 -> TEXT
-- CLOB -> TEXT
-- DATE -> TEXT
-- BLOB -> BLOB
-- SEQUENCE -> AUTOINCREMENT
-- ROWNUM -> LIMIT
-- CONNECT BY -> WITH RECURSIVE

-- PL/SQL -> Application logic
-- SQLite non supporta stored procedures
```

### 1.4 Migration Automatizzata

```python
import re

def mysql_to_sqlite(sql):
    """Convert MySQL dump to SQLite compatible"""
    # Remove ENGINE, CHARSET, COLLATE
    sql = re.sub(r'\s+ENGINE=\w+', '', sql)
    sql = re.sub(r'\s+CHARSET=\w+', '', sql)
    sql = re.sub(r'\s+COLLATE=\w+', '', sql)
    
    # Convert AUTO_INCREMENT
    sql = sql.replace('AUTO_INCREMENT', 'AUTOINCREMENT')
    
    # Convert backticks to quotes
    sql = sql.replace('`', '"')
    
    # Convert LIMIT
    sql = re.sub(r'LIMIT\s+(\d+),\s*(\d+)', r'LIMIT \2 OFFSET \1', sql)
    
    return sql

# Usage
with open('mysql_dump.sql') as f:
    sqlite_sql = mysql_to_sqlite(f.read())
    
with open('sqlite_import.sql', 'w') as f:
    f.write(sqlite_sql)
```

---

## 2. SQLite Compatibility

### 2.1 SQL Standard Compliance

```sql
-- SQLite supporta:
-- - SELECT con tutte le clausole
-- - INSERT, UPDATE, DELETE
-- - CREATE TABLE/INDEX/VIEW
-- - JOINs (INNER, LEFT, RIGHT, CROSS)
-- - Subqueries
-- - CTEs (SQLite 3.8.3+)
-- - Window Functions (SQLite 3.25+)
-- - Recursive CTEs

-- Non supporta:
-- - ALTER TABLE (solo RENAME e ADD COLUMN da 3.35.0)
-- - FOREIGN KEY enforcement (default OFF, abilitare con PRAGMA foreign_keys)
-- - CHECK constraints (da 3.37+)
-- - GRANT/REVOKE
-- - Multiple schemas
-- - Triggers with OR REPLACE
```

### 2.2 Feature Detection

```sql
-- Verificare versione SQLite
SELECT sqlite_version();

-- Verificare feature disponibili
PRAGMA compile_options;

-- Esempi output:
-- ENABLE_FTS5
-- ENABLE_JSON1
-- ENABLE_RTREE
-- ENABLE_STAT4

-- Feature availability check in code
def has_fts5(conn):
    result = conn.execute(
        "PRAGMA compile_options"
    ).fetchall()
    return any('FTS5' in str(r) for r in result)
```

### 2.3 Version Compatibility

```sql
-- SQLite version history:
-- 3.35.0 (2021-03-12): ADD COLUMN, UPSERT, CAST from SELECT
-- 3.33.0 (2020-05-22): Enhanced PRAGMA, COPY command
-- 3.31.0 (2020-01-27): Generated columns, TRUNCATE
-- 3.28.0 (2019-04-08): Enhanced window functions
-- 3.25.0 (2017-09-29): Window functions, RENAME COLUMN
-- 3.24.0 (2018-06-04): UPSERT, recursive CTEs enhancement
-- 3.20.0 (2017-08-01): JSON1 extension
-- 3.18.0 (2017-03-03): FTS5 tokens

-- Verificare feature compatibilità
-- In Python:
import sqlite3

def get_sqlite_version():
    return sqlite3.sqlite_version

def supports_feature(conn, feature):
    """Check if feature is supported"""
    if feature == 'upsert':
        return sqlite3.sqlite_version >= '3.24.0'
    elif feature == 'window':
        return sqlite3.sqlite_version >= '3.25.0'
    elif feature == 'generated_columns':
        return sqlite3.sqlite_version >= '3.31.0'
    elif feature == 'add_column':
        return sqlite3.sqlite_version >= '3.35.0'
    return True
```

### 2.4 Cross-Version Compatibility

```python
# Compatibilità all'indietro
# SQLite è altamente compatibile

# Best practice: non usare feature nuove se devi supportare versioni vecchie

def safe_create_index(conn):
    """Create index with version check"""
    version = conn.execute("SELECT sqlite_version()").fetchone()[0]
    
    # Generated columns from 3.31.0
    if version >= '3.31.0':
        conn.execute("""
            CREATE TABLE IF NOT EXISTS new_table (
                id INTEGER PRIMARY KEY,
                data TEXT,
                generated TEXT GENERATED ALWAYS AS (data || '_gen')
            )
        """)
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS new_table (
                id INTEGER PRIMARY KEY,
                data TEXT,
                generated TEXT
            )
        """)
```

---

## 3. Data Import/Export

### 3.1 Import da CSV

```sql
-- Metodo 1: CSV virtual table (richiede estensione csv)
CREATE VIRTUAL TABLE temp_data USING csv(
    filename='data.csv',
    header=TRUE,
    delimiter=','
);

-- Copiare in tabella reale
INSERT INTO real_table SELECT * FROM temp_data;

-- Metodo 2: Import mode
-- In sqlite3 CLI:
-- .mode csv
-- .import data.csv table_name
```

### 3.2 Import da JSON

```sql
-- Import JSON array
-- Via Python
import sqlite3
import json

with open('data.json') as f:
    data = json.load(f)

conn = sqlite3.connect('db.sqlite')
cursor = conn.cursor()

for item in data:
    cursor.execute(
        "INSERT INTO table (col1, col2) VALUES (?, ?)",
        (item['col1'], item['col2'])
    )

conn.commit()

-- Oppure con JSON each
CREATE VIRTUAL TABLE json_data USING json_each(?);
-- Bind JSON string and query
```

### 3.3 Export a CSV

```sql
-- Metodo 1: CLI
-- .mode csv
-- .output data.csv
-- SELECT * FROM table;
-- .output stdout

-- Metodo 2: Python
def export_to_csv(conn, table_name, filename):
    cursor = conn.execute(f"SELECT * FROM {table_name}")
    
    with open(filename, 'w', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow([desc[0] for desc in cursor.description])
        writer.writerows(cursor.fetchall())
```

### 3.4 Export a SQL Dump

```sql
-- Dump completo
-- .dump

-- Dump schema
-- .schema

-- Dump singola tabella
-- .schema table_name

-- Backup in SQL format
-- .output backup.sql
-- .dump
-- .output stdout
```

### 3.5 Import da XML

```python
import xml.etree.ElementTree as ET

def import_xml(db_path, xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    conn = sqlite3.connect(db_path)
    
    for item in root.findall('.//record'):
        data = {child.tag: child.text for child in item}
        conn.execute(
            "INSERT INTO table (cols) VALUES (:data)",
            data
        )
    
    conn.commit()
    conn.close()
```

---

## 4. Cross-Platform Considerations

### 4.1 File Path Handling

```python
import os
import platform

def get_db_path(db_name):
    """Cross-platform database path"""
    system = platform.system()
    
    if system == 'Windows':
        base = os.path.join(os.environ['APPDATA'], 'MyApp')
    elif system == 'Darwin':  # macOS
        base = os.path.expanduser('~/Library/Application Support/MyApp')
    else:  # Linux
        base = os.path.join(os.environ.get('XDG_DATA_HOME', 
                           os.path.expanduser('~/.local/share')), 
                           'MyApp')
    
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, db_name)

# Usage
db_path = get_db_path('mydb.sqlite')
conn = sqlite3.connect(db_path)
```

### 4.2 Endianness

```sql
-- SQLite è little-endian by default
-- Ma i file sono portabili tra architetture diverse
-- Il database si adatta automaticamente

-- Verificare endianness
PRAGMA page_size;  -- funziona su tutte le piattaforme
```

### 4.3 Unicode Handling

```sql
-- SQLite gestisce UTF-8 nativamente
-- Supporta UTF-8, UTF-16, UTF-16le, UTF-16be

-- Impostare encoding
PRAGMA encoding;  -- ritorna UTF-8 default

-- Creare database con specifico encoding
-- Non possibile modificare dopo creazione

-- Verificare caratteri
SELECT 'Caffè', length('Caffè'), length(CAST('Caffè' AS BLOB));
```

### 4.4 Portability Considerations

```python
# Best practices per portabilità:

# 1. Usa percorsi relativi quando possibile
db_path = os.path.join(os.path.dirname(__file__), 'data', 'app.db')

# 2. Gestisci percorsi con os.path
db_path = os.path.join('data', 'app.db')  # works on all OS

# 3. Non hardcodare separatori
# Use os.path.join() not string concatenation

# 4. Testa su tutte le piattaforme target
```

---

## 5. Version Migration

### 5.1 Database Schema Version

```sql
-- Tenere traccia della versione schema
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Inserire versione iniziale
INSERT INTO schema_version (version, description) 
VALUES (1, 'Initial schema');

-- Dopo migration
INSERT INTO schema_version (version, description)
VALUES (2, 'Added user_email column');
```

### 5.2 Migration Scripts

```python
class DatabaseMigration:
    def __init__(self, conn):
        self.conn = conn
        self.migrations = {}
    
    def register(self, version, description, upgrade_fn):
        self.migrations[version] = (description, upgrade_fn)
    
    def migrate_to_latest(self):
        current = self.get_current_version()
        
        for version in sorted(self.migrations.keys()):
            if version > current:
                desc, upgrade_fn = self.migrations[version]
                print(f"Migrating to v{version}: {desc}")
                upgrade_fn(self.conn)
                self.set_version(version)
    
    def get_current_version(self):
        try:
            result = self.conn.execute(
                "SELECT MAX(version) FROM schema_version"
            ).fetchone()
            return result[0] or 0
        except:
            return 0
    
    def set_version(self, version):
        self.conn.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (version,)
        )
        self.conn.commit()

# Usage
migrations = DatabaseMigration(conn)

migrations.register(2, "Add email column", lambda db: 
    db.execute("ALTER TABLE users ADD COLUMN email TEXT"))

migrations.register(3, "Create indexes", lambda db:
    db.execute("CREATE INDEX idx_users_email ON users(email)"))

migrations.migrate_to_latest()
```

### 5.3 Rollback Strategy

```sql
-- Tenere migration history per rollback
CREATE TABLE schema_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL,
    description TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    direction TEXT DEFAULT 'up',  -- 'up' or 'down'
    checksum TEXT  -- SHA256 of migration script
);

-- Per rollback:
-- 1. Trovare ultima migration
-- 2. Eseguire downgrade script
-- 3. Marcare come rolled back
```

---

## 6. Schema Migration

### 6.1 Add Column

```sql
-- Da SQLite 3.35.0+ (2021):
ALTER TABLE users ADD COLUMN email TEXT;

-- Prima di 3.35.0: ricreare tabella
PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

CREATE TABLE users_new (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,  -- nuova colonna
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users_new (id, name, created_at)
SELECT id, name, created_at FROM users;

DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

-- Abilitare foreign keys
PRAGMA foreign_keys=ON;

COMMIT;
```

### 6.2 Rename Table

```sql
-- Rename supportato
ALTER TABLE old_name RENAME TO new_name;

-- Verificare che non ci siano view/trigger che referenziano
SELECT name, type FROM sqlite_master 
WHERE sql LIKE '%old_name%';
```

### 6.3 Drop Column

```sql
-- Da SQLite 3.35.0+:
ALTER TABLE users DROP COLUMN old_column;

-- Prima: ricreare tabella senza la colonna
```

### 6.4 Migration with Data

```python
def migrate_with_data(old_table, new_schema, transform_fn):
    """Migration con trasformazione dati"""
    # 1. Creare nuova tabella
    conn.execute(new_schema)
    
    # 2. Leggere dati dalla vecchia tabella
    for row in conn.execute(f"SELECT * FROM {old_table}"):
        # 3. Trasformare
        new_row = transform_fn(row)
        # 4. Inserire
        conn.execute(f"INSERT INTO new_table VALUES (?, ...)", new_row)
    
    # 5. Rimuovere vecchia tabella
    conn.execute(f"DROP TABLE {old_table}")
    
    # 6. Rinominare
    conn.execute("ALTER TABLE new_table RENAME TO " + old_table)
```

---

## 7. Data Transformation

### 7.1 Type Conversion

```sql
-- Convertire tipi
SELECT 
    CAST(price AS INTEGER) as int_price,
    CAST(name AS REAL) as real_name,  -- non ha senso
    CAST(date_string AS DATE) as date
FROM products;

-- Convertire stringhe
SELECT 
    substr(code, 1, 3) as prefix,
    CAST(substr(code, 4) AS INTEGER) as number_part
FROM products;
```

### 7.2 Data Normalization

```sql
-- Normalizzare testo
SELECT 
    LOWER(TRIM(name)) as normalized_name,
    LOWER(email) as normalized_email,
    REPLACE(phone, ' ', '') as clean_phone
FROM customers;

-- Date normalization
SELECT 
    date(created_at) as date_only,
    time(created_at) as time_only,
    datetime(created_at, 'localtime') as local_time
FROM orders;
```

### 7.3 Data Denormalization

```sql
-- Da normalizzato a denormalizzato
SELECT 
    o.id,
    c.name || ' (' || c.email || ')' as customer_info,
    GROUP_CONCAT(p.name, ', ') as products
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
GROUP BY o.id;
```

### 7.4 Complex Transformations

```python
def transform_data(conn, source_table, dest_table):
    """Trasformazione complessa"""
    # Estrarre e trasformare
    for row in conn.execute(f"SELECT * FROM {source_table}"):
        transformed = {
            'id': row['id'],
            'name': row['name'].upper() if row['name'] else None,
            'status': 'active' if row['is_active'] else 'inactive',
            'computed': row['value'] * 1.1 if row['value'] else 0,
            'metadata': json.dumps({
                'source': source_table,
                'original_id': row['id'],
                'transformed_at': datetime.now().isoformat()
            })
        }
        
        conn.execute(
            f"INSERT INTO {dest_table} VALUES (:id, :name, :status, :computed, :metadata)",
            transformed
        )
    
    conn.commit()
```

---

## 8. Compatibility Layers

### 8.1 PostgreSQL Compatibility

```python
# Pattern per emulare funzioni PostgreSQL
class PostgreSQLCompat:
    def __init__(self, conn):
        self.conn = conn
        self._install_functions()
    
    def _install_functions(self):
        # NOW()
        self.conn.create_function("now", 0, lambda: 
            datetime.now().isoformat())
        
        # GENERATE_SERIES
        def generate_series(start, stop, step=1):
            return list(range(start, stop+1, step))
        self.conn.create_function("generate_series", -1, generate_series)
        
        # ARRAY_AGG
        # Custom aggregate
        
        # TO_CHAR
        def to_char(value, format_str):
            # Simplified implementation
            return str(value)
        self.conn.create_function("to_char", 2, to_char)
```

### 8.2 MySQL Compatibility

```python
class MySQLCompat:
    def __init__(self, conn):
        self.conn = conn
        self._install_functions()
    
    def _install_functions(self):
        # LAST_INSERT_ID
        self.conn.execute("CREATE TABLE IF NOT EXISTS _last_insert_id (id INTEGER)")
        
        # GROUP_CONCAT
        # (already built-in as GROUP_CONCAT)
        
        # IFNULL
        self.conn.create_function("IFNULL", 2, lambda x, y: x if x else y)
        
        # DATE_ADD
        def date_add(date_str, interval_str):
            # Simple implementation
            return date_str
        self.conn.create_function("DATE_ADD", 2, date_add)
```

### 8.3 SQL Server Compatibility

```python
class SQLServerCompat:
    def __init__(self, conn):
        self.conn = conn
        self._install_functions()
    
    def _install_functions(self):
        # GETDATE()
        self.conn.create_function("GETDATE", 0, lambda:
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # ISNULL
        self.conn.create_function("ISNULL", 2, lambda x, y: x if x else y)
        
        # DATEPART
        def datepart(part, date_str):
            from datetime import datetime
            d = datetime.fromisoformat(date_str)
            if part == 'year':
                return d.year
            elif part == 'month':
                return d.month
            elif part == 'day':
                return d.day
            return None
        self.conn.create_function("DATEPART", 2, datepart)
```

---

## 9. Interoperability Patterns

### 9.1 Multiple Database Connection

```python
# Connessione a SQLite + altri database
import sqlite3
import psycopg2  # PostgreSQL
import pymysql   # MySQL

class MultiDB:
    def __init__(self):
        self.connections = {}
    
    def connect_sqlite(self, path):
        self.connections['sqlite'] = sqlite3.connect(path)
    
    def connect_postgres(self, **kwargs):
        self.connections['postgres'] = psycopg2.connect(**kwargs)
    
    def connect_mysql(self, **kwargs):
        self.connections['mysql'] = pymysql.connect(**kwargs)
    
    def query_from(self, db_name, sql, params=None):
        conn = self.connections[db_name]
        return conn.execute(sql, params or [])
    
    def close_all(self):
        for conn in self.connections.values():
            conn.close()
```

### 9.2 Data Sync Between Databases

```python
def sync_sqlite_to_postgres(sqlite_conn, pg_conn, table):
    """Sincronizza tabella da SQLite a PostgreSQL"""
    # Leggere da SQLite
    rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
    
    # Inserire in PostgreSQL
    columns = [desc[0] for desc in sqlite_conn.description]
    placeholders = ','.join(['%s'] * len(columns))
    
    for row in rows:
        pg_conn.execute(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
            row
        )
    
    pg_conn.commit()
```

### 9.3 Federation Pattern

```sql
-- Accesso a database remoti via attaccamento
-- SQLite supporta solo database locali
-- Ma si può simulare con shell/URL virtual tables

-- Per database remoti, usare extentions:
-- - httpfs per accesso HTTP
-- - filelist per accesso file system

-- Pattern: cache locale di dati remoti
CREATE TABLE cached_remote_data (
    id INTEGER PRIMARY KEY,
    remote_id TEXT,
    data TEXT,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Refresh cache
INSERT OR REPLACE INTO cached_remote_data
SELECT id, remote_id, data, CURRENT_TIMESTAMP
FROM (
    SELECT ... -- fetch from remote
);
```

### 9.4 Export/Import Pipeline

```python
class DataPipeline:
    def __init__(self):
        self.steps = []
    
    def add_step(self, name, transform_fn):
        self.steps.append((name, transform_fn))
    
    def execute(self, data):
        result = data
        for name, transform_fn in self.steps:
            print(f"Executing: {name}")
            result = transform_fn(result)
        return result

# Usage
pipeline = DataPipeline()

pipeline.add_step("extract", lambda: 
    sqlite_conn.execute("SELECT * FROM source").fetchall())

pipeline.add_step("transform", lambda rows:
    [{'id': r[0], 'name': r[1].upper()} for r in rows])

pipeline.add_step("load", lambda rows:
    [postgres_conn.execute("INSERT INTO dest VALUES (?, ?)", (r['id'], r['name'])) 
     for r in rows])

pipeline.execute()
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*