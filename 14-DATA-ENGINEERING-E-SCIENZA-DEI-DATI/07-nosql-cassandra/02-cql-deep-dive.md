# Cassandra: CQL Deep Dive

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-05  
> Versione: 1.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. CQL Fundamentals
2. Data Types
3. CRUD Operations
4. Queries and Filtering
5. Collections
6. User-Defined Types
7. Functions
8. Batch Operations

---

## 1. CQL Fundamentals

### 1.1 Connection

```bash
# Connect to Cassandra
cqlsh localhost 9042

# With authentication
cqlsh -u username -p password

# Connect to specific keyspace
cqlsh -k mykeyspace
```

### 1.2 Keyspace Operations

```sql
-- Create keyspace
CREATE KEYSPACE myapp
WITH REPLICATION = {
  'class': 'SimpleStrategy',
  'replication_factor': 3
}
AND DURABLE_WRITES = true;

-- Use keyspace
USE myapp;

-- List keyspaces
DESCRIBE KEYSPACES;

-- Alter keyspace
ALTER KEYSPACE myapp
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'dc1': 3
};
```

### 1.3 Table Operations

```sql
-- Create table
CREATE TABLE users (
    user_id uuid PRIMARY KEY,
    username text,
    email text,
    age int,
    created_at timestamp,
    updated_at timestamp
) WITH comment = 'User directory'
  AND default_time_to_live = 2592000;  -- 30 days

-- Create table with options
CREATE TABLE events (
    partition_key text,
    clustering_key timeuuid,
    event_data text,
    PRIMARY KEY (partition_key, clustering_key)
) WITH CLUSTERING ORDER BY (clustering_key DESC)
  AND COMPACTION = {'class': 'TimeWindowCompactionStrategy'}
  AND COMMENT = 'Time-series events';

-- List tables
DESCRIBE TABLES;

-- Describe table
DESCRIBE TABLE users;
```

---

## 2. Data Types

### 2.1 Native Types

```sql
-- Native types
text          -- UTF-8 string
varchar       -- alias for text
ascii         -- ASCII string
int           -- 32-bit signed
bigint        -- 64-bit signed
smallint      -- 16-bit signed
tinyint       -- 8-bit signed
float         -- 32-bit float
double        -- 64-bit float
decimal       -- arbitrary precision
boolean       -- true/false
uuid          -- type 1 or 4 UUID
timeuuid      -- type 1 UUID (timestamp-based)
timestamp     -- milliseconds since epoch
date          -- date (no time)
time          -- time (no date)
blob          -- arbitrary bytes
varint        -- arbitrary precision integer
```

### 2.2 Collections

```sql
-- Set
CREATE TABLE tags (
    id uuid PRIMARY KEY,
    name text,
    tags set<text>
);

INSERT INTO tags (id, name, tags) 
VALUES (uuid(), 'test', {'tag1', 'tag2', 'tag3'});

-- List
CREATE TABLE events (
    id uuid PRIMARY KEY,
    name text,
    attendees list<text>
);

INSERT INTO events (id, name, attendees)
VALUES (uuid(), 'conference', ['Alice', 'Bob', 'Charlie']);

-- Map
CREATE TABLE user_prefs (
    user_id uuid PRIMARY KEY,
    preferences map<text, text>
);

INSERT INTO user_prefs (user_id, preferences)
VALUES (uuid(), {'theme': 'dark', 'lang': 'en'});
```

---

## 3. CRUD Operations

### 3.1 INSERT

```sql
-- Basic insert
INSERT INTO users (user_id, username, email, age)
VALUES (uuid(), 'john', 'john@example.com', 30);

-- Insert with TTL (seconds)
INSERT INTO users (user_id, username, email)
VALUES (uuid(), 'tempuser', 'temp@example.com')
USING TTL 3600;  -- 1 hour

-- Insert with timestamp
INSERT INTO users (user_id, username, created_at)
VALUES (uuid(), 'john', toTimestamp(now()))
USING TIMESTAMP 1700000000000000;
```

### 3.2 SELECT

```sql
-- Basic select
SELECT * FROM users;

-- Select specific columns
SELECT user_id, username, email FROM users;

-- Where clause (partition key only)
SELECT * FROM users WHERE user_id = ?

-- Limit results
SELECT * FROM users LIMIT 100;

-- Order by (requires clustering key)
SELECT * FROM events 
WHERE partition_key = '2024-01'
ORDER BY clustering_key DESC
LIMIT 50;
```

### 3.3 UPDATE

```sql
-- Basic update
UPDATE users 
SET email = 'newemail@example.com', age = 31
WHERE user_id = ?

-- Update with TTL
UPDATE users SET email = 'temp@test.com'
WHERE user_id = ?
USING TTL 300;

-- Increment/Decrement counter
CREATE TABLE page_views (
    page_id text PRIMARY KEY,
    views counter
);

UPDATE page_views SET views = views + 1 
WHERE page_id = '/home';
```

### 3.4 DELETE

```sql
-- Delete row
DELETE FROM users WHERE user_id = ?;

-- Delete specific columns
UPDATE users SET email = null WHERE user_id = ?;

-- Delete from collection
UPDATE tags SET tags = tags - {'tag1'} WHERE id = ?;

DELETE tags FROM tags WHERE id = ?;

-- Delete with TTL
DELETE FROM users WHERE user_id = ?
USING TTL 0;  -- Remove TTL from row
```

---

## 4. Queries and Filtering

### 4.1 ALLOW FILTERING

```sql
-- Non-primary key filtering (not recommended for production)
SELECT * FROM users 
WHERE age > 25 
ALLOW FILTERING;

-- Should use indexed columns
CREATE INDEX ON users(age);
SELECT * FROM users WHERE age > 25;
```

### 4.2 IN Queries

```sql
-- IN on partition key
SELECT * FROM users 
WHERE user_id IN (uuid1, uuid2, uuid3);

-- IN on clustering key
SELECT * FROM events 
WHERE partition_key = '2024-01' 
AND clustering_key IN (uuid1, uuid2);
```

### 4.3 Range Queries

```sql
-- Range on clustering key
SELECT * FROM events 
WHERE partition_key = '2024-01' 
AND clustering_key > uuid1 
AND clustering_key < uuid2;

-- Time range
SELECT * FROM metrics 
WHERE service = 'api' 
AND timestamp >= toTimestamp('2024-01-01')
AND timestamp <= toTimestamp('2024-01-02');
```

---

## 5. Collections

### 5.1 Set Operations

```sql
-- Add to set
UPDATE tags SET tags = tags + {'newtag'} WHERE id = ?;

-- Remove from set
UPDATE tags SET tags = tags - {'oldtag'} WHERE id = ?;

-- Check membership
SELECT * FROM tags WHERE id = ? AND tags CONTAINS 'important';
```

### 5.2 List Operations

```sql
-- Append/prepend
UPDATE events SET attendees = attendees + ['Dave'] WHERE id = ?;
UPDATE events SET attendees = ['NewFirst'] + attendees WHERE id = ?;

-- Set by index
UPDATE events SET attendees[0] = 'Alice' WHERE id = ?;

-- Remove by value
UPDATE events SET attendees = attendees - ['Bob'] WHERE id = ?;
```

### 5.3 Map Operations

```sql
-- Update single key
UPDATE user_prefs SET preferences['theme'] = 'light' WHERE user_id = ?;

-- Add multiple keys
UPDATE user_prefs SET preferences = preferences + {'key1': 'val1', 'key2': 'val2'} 
WHERE user_id = ?;

-- Delete key
DELETE preferences['old_key'] FROM user_prefs WHERE user_id = ?;
```

---

## 6. User-Defined Types

```sql
-- Create UDT
CREATE TYPE address (
    street text,
    city text,
    state text,
    zip text,
    country text
);

CREATE TYPE phone (
    country_code int,
    number text
);

-- Use UDT in table
CREATE TABLE users (
    user_id uuid PRIMARY KEY,
    name text,
    home_address address,
    mobile_phone phone,
    work_phone phone
);

-- Insert UDT
INSERT INTO users (user_id, name, home_address)
VALUES (
    uuid(), 
    'John', 
    {street: '123 Main St', city: 'NYC', state: 'NY', zip: '10001', country: 'USA'}
);

-- Access UDT fields
SELECT name, home_address.street, home_address.city FROM users;
```

---

## 7. Functions

### 7.1 Built-in Functions

```sql
-- Type conversion
SELECT toDate(created_at) FROM users;
SELECT toTimestamp('2024-01-01') FROM events;
SELECT dateOf(now()) FROM events;

-- String functions
SELECT blobAsAscii(asciiBlob) FROM data;
SELECT asciiAsBlob('text') FROM data;
SELECT dateOf(now()) FROM events;

-- Aggregate functions (in SELECT)
SELECT COUNT(*) FROM users;
SELECT COUNT(1) FROM users;
SELECT MAX(age) FROM users;
SELECT MIN(age) FROM users;
SELECT AVG(age) FROM users;
SELECT SUM(price) FROM orders;

-- Function in WHERE
SELECT * FROM users WHERE age > 0 ALLOW FILTERING;
```

### 7.2 UDF (User-Defined Functions)

```sql
-- Create UDF
CREATE FUNCTION ifnull(input text, default_val text)
RETURNS text
LANGUAGE java
AS 'if (input == null) return default_val; return input;';

-- Use UDF
SELECT ifnull(email, 'no-email') FROM users;
```

---

## 8. Batch Operations

### 8.1 Logged Batch

```sql
BEGIN BATCH
    INSERT INTO users (user_id, name) VALUES (uuid(), 'Alice');
    INSERT INTO user_prefs (user_id, preferences) 
    VALUES (uuid(), {'theme': 'dark'});
    UPDATE users SET email = 'alice@test.com' WHERE user_id = ?;
APPLY BATCH;
```

### 8.2 Unlogged Batch

```sql
BEGIN UNLOGGED BATCH
    UPDATE page_views SET views = views + 1 WHERE page_id = '/home';
    UPDATE page_views SET views = views + 1 WHERE page_id = '/about';
APPLY BATCH;
```

### 8.3 Counter Batch

```sql
BEGIN COUNTER BATCH
    UPDATE page_views SET views = views + 1 WHERE page_id = '/home';
    UPDATE page_views SET views = views + 1 WHERE page_id = '/products';
APPLY BATCH;
```

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*