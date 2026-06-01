# Cassandra: Data Modeling

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
1. Modeling Principles
2. Primary Key Design
3. Query-First Approach
4. Denormalization
5. Common Patterns
6. Anti-Patterns
7. Time Series
8. Aggregation

---

## 1. Modeling Principles

### 1.1 Query-Driven Design

```sql
-- Start from queries, not entities
-- Query 1: Get user by ID
CREATE TABLE users_by_id (
    user_id uuid PRIMARY KEY,
    username text,
    email text,
    created_at timestamp
);

-- Query 2: Get user by email
CREATE TABLE users_by_email (
    email text PRIMARY KEY,
    user_id uuid,
    username text
);

-- Query 3: List users by age range
CREATE TABLE users_by_age (
    age int,
    user_id uuid,
    username text,
    PRIMARY KEY (age, user_id)
);
```

### 1.2 Partition Design

```sql
-- Target: 10MB-100MB per partition
-- Avoid: partitions > 100MB

-- Good: user_id as partition key
CREATE TABLE user_data (
    user_id uuid PRIMARY KEY,
    data text
);

-- Bad: date as partition key (too many rows)
CREATE TABLE events_by_date (
    date text,
    event_id timeuuid,
    data text,
    PRIMARY KEY (date, event_id)
);

-- Better: composite partition key
CREATE TABLE events_by_month_day (
    year_month text,
    day int,
    event_id timeuuid,
    data text,
    PRIMARY KEY ((year_month, day), event_id)
);
```

---

## 2. Primary Key Design

### 2.1 Simple Primary Key

```sql
-- Single column partition key
CREATE TABLE products (
    product_id uuid PRIMARY KEY,
    name text,
    price decimal
);
```

### 2.2 Composite Partition Key

```sql
-- Partition by organization and type
CREATE TABLE documents (
    org_id uuid,
    doc_type text,
    doc_id uuid,
    content text,
    PRIMARY KEY ((org_id, doc_type), doc_id)
) WITH CLUSTERING ORDER BY (doc_id DESC);

-- Query: SELECT * FROM documents WHERE org_id = ? AND doc_type = 'pdf';
```

### 2.3 Clustering Columns

```sql
-- Multiple clustering keys (ordered)
CREATE TABLE timeline (
    user_id uuid,
    post_id timeuuid,
    content text,
    likes int,
    PRIMARY KEY (user_id, post_id)
) WITH CLUSTERING ORDER BY (post_id DESC);

-- Query: Get latest posts for user
SELECT * FROM timeline WHERE user_id = ? ORDER BY post_id DESC LIMIT 20;
```

---

## 3. Query-First Approach

### 3.1 From Queries to Tables

```sql
-- Query: Get user orders
-- Step 1: Identify access pattern
-- "Show me all orders for user X, sorted by date"

-- Step 2: Design table
CREATE TABLE orders_by_user (
    user_id uuid,
    order_date timestamp,
    order_id uuid,
    total decimal,
    status text,
    PRIMARY KEY (user_id, order_date, order_id)
) WITH CLUSTERING ORDER BY (order_date DESC);

-- Query: Get recent orders
SELECT * FROM orders_by_user 
WHERE user_id = ? 
ORDER BY order_date DESC 
LIMIT 10;
```

### 3.2 Multiple Query Patterns

```sql
-- Pattern 1: Orders by user
CREATE TABLE orders_by_user (
    user_id uuid,
    order_date timestamp,
    order_id uuid,
    PRIMARY KEY (user_id, order_date, order_id)
);

-- Pattern 2: Orders by date (for batch processing)
CREATE TABLE orders_by_date (
    order_date timestamp,
    order_id uuid,
    user_id uuid,
    total decimal,
    PRIMARY KEY (order_date, order_id)
);

-- Pattern 3: Order details by order ID
CREATE TABLE orders_by_id (
    order_id uuid PRIMARY KEY,
    user_id uuid,
    total decimal,
    created_at timestamp
);
```

---

## 4. Denormalization

### 4.1 Materialized Views

```sql
-- Create materialized view
CREATE MATERIALIZED VIEW users_by_email AS
SELECT * FROM users_by_id
WHERE email IS NOT NULL
PRIMARY KEY (email, user_id);

-- Query via view
SELECT * FROM users_by_email WHERE email = 'john@test.com';

-- Automatic sync with base table
INSERT INTO users_by_id (user_id, username, email)
VALUES (uuid(), 'john', 'john@test.com');
-- Automatically appears in users_by_email
```

### 4.2 Manual Denormalization

```sql
-- Application maintains sync
CREATE TABLE user_orders_count (
    user_id uuid PRIMARY KEY,
    order_count counter
);

-- Update counters on order insert
BEGIN BATCH
    INSERT INTO orders_by_user (...) VALUES (...);
    UPDATE user_orders_count SET order_count = order_count + 1 
    WHERE user_id = ?;
APPLY BATCH;
```

---

## 5. Common Patterns

### 5.1 One-to-Many

```sql
-- User has many orders: embed or link?
-- Option 1: Link (separate table)
CREATE TABLE orders (
    order_id uuid PRIMARY KEY,
    user_id uuid,
    total decimal
);

-- Option 2: Embed (if small, fixed number)
CREATE TABLE user_with_orders (
    user_id uuid PRIMARY KEY,
    order_ids list<uuid>  -- limited size
);
```

### 5.2 Many-to-Many

```sql
-- Students and Courses
CREATE TABLE student_courses (
    student_id uuid,
    course_id uuid,
    enrolled_at timestamp,
    PRIMARY KEY (student_id, course_id)
);

CREATE TABLE course_students (
    course_id uuid,
    student_id uuid,
    enrolled_at timestamp,
    PRIMARY KEY (course_id, student_id)
);
```

### 5.3 Queue/Stack

```sql
-- Append-only log
CREATE TABLE event_log (
    partition_key text,
    event_id timeuuid,
    event_data text,
    PRIMARY KEY (partition_key, event_id)
) WITH CLUSTERING ORDER BY (event_id DESC);

-- Query recent events
SELECT * FROM event_log 
WHERE partition_key = 'daily' 
ORDER BY event_id DESC 
LIMIT 100;
```

---

## 6. Anti-Patterns

### 6.1 Wide Rows

```sql
-- Bad: Unbounded rows
CREATE TABLE user_events (
    user_id uuid,
    event_id timeuuid,
    data text,
    PRIMARY KEY (user_id, event_id)
);

-- Risk: User with millions of events = huge partition

-- Solution: Bucket by time
CREATE TABLE user_events_2024_01 (
    user_id uuid,
    event_id timeuuid,
    data text,
    PRIMARY KEY ((user_id, '2024-01'), event_id)
);
```

### 6.2 Full Table Scans

```sql
-- Don't do this:
SELECT * FROM large_table ALLOW FILTERING;

-- Use partition keys or create specific tables
CREATE TABLE latest_events (
    bucket int,
    event_id timeuuid,
    data text,
    PRIMARY KEY (bucket, event_id)
) WITH CLUSTERING ORDER BY (event_id DESC);
```

---

## 7. Time Series

### 7.1 Time Bucketing

```sql
-- Bucket by day
CREATE TABLE metrics_daily (
    metric_name text,
    date text,  -- '2024-01-15'
    timestamp timeuuid,
    value double,
    PRIMARY KEY ((metric_name, date), timestamp)
);

-- Query: Get day's metrics
SELECT * FROM metrics_daily 
WHERE metric_name = 'cpu' AND date = '2024-01-15';
```

### 7.2 Compact Storage

```sql
-- Time series optimization
CREATE TABLE sensor_readings (
    sensor_id text,
    day text,
    minute int,
    reading_time timeuuid,
    value double,
    PRIMARY KEY ((sensor_id, day), minute, reading_time)
) WITH COMPACTION = {'class': 'TimeWindowCompactionStrategy'}
  AND default_time_to_live = 7776000;  -- 90 days
```

---

## 8. Aggregation

### 8.1 Counters

```sql
-- Pre-aggregate with counters
CREATE TABLE hourly_visits (
    page text,
    hour timestamp,
    visits counter,
    PRIMARY KEY (page, hour)
);

UPDATE hourly_visits SET visits = visits + 1 
WHERE page = '/home' AND hour = toTimestamp('2024-01-15 14:00');
```

### 8.2 Summary Tables

```sql
-- Materialized aggregates
CREATE TABLE daily_sales_summary (
    date text,
    total_orders int,
    total_revenue decimal,
    PRIMARY KEY (date)
);

-- Update via batch
BEGIN BATCH
    INSERT INTO orders (...) VALUES (...);
    UPDATE daily_sales_summary 
    SET total_orders = total_orders + 1, 
        total_revenue = total_revenue + ? 
    WHERE date = ?;
APPLY BATCH;
```

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*