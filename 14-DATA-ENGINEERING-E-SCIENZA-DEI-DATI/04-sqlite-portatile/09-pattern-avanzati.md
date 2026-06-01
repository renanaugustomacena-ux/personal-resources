# SQLite: Pattern e Ricette Avanzate

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
1. Advanced Queries
2. Data Processing Patterns
3. Caching Strategies
4. Event Sourcing
5. CQRS Pattern
6. Graph Algorithms
7. Time Series
8. Full-Text Search Patterns
9. Spatial Data
10. Data Warehouse Patterns

---

## 1. Advanced Queries

### 1.1 Recursive Tree Traversal

```sql
-- Navigare struttura gerarchica
WITH RECURSIVE org_tree AS (
    -- Base case: root nodes
    SELECT id, name, manager_id, 1 as level, 
           CAST(name AS TEXT) as path
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case
    SELECT e.id, e.name, e.manager_id, ot.level + 1,
           ot.path || ' > ' || e.name
    FROM employees e
    JOIN org_tree ot ON e.manager_id = ot.id
    WHERE ot.level < 10  -- Prevent infinite loops
)
SELECT * FROM org_tree ORDER BY level, name;
```

### 1.2 Top-N per Group

```sql
-- Top 3 prodotti per categoria
WITH ranked AS (
    SELECT 
        p.*,
        c.name as category_name,
        ROW_NUMBER() OVER (
            PARTITION BY p.category_id 
            ORDER BY p.price DESC
        ) as rank
    FROM products p
    JOIN categories c ON p.category_id = c.id
)
SELECT * FROM ranked WHERE rank <= 3;

-- Alternative con subquery
SELECT p1.*
FROM products p1
WHERE (
    SELECT COUNT(DISTINCT p2.price)
    FROM products p2
    WHERE p2.category_id = p1.category_id
       AND p2.price > p1.price
) < 3
ORDER BY p1.category_id, p1.price DESC;
```

### 1.3 Running Totals e Moving Averages

```sql
-- Running total
SELECT 
    date,
    amount,
    (SELECT SUM(amount) 
     FROM transactions t2 
     WHERE t2.date <= t1.date) as running_total
FROM transactions t1
ORDER BY date;

-- Moving average 7 giorni
SELECT 
    date,
    amount,
    AVG(amount) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as ma_7
FROM transactions
ORDER BY date;

-- Percent change from previous
SELECT 
    date,
    amount,
    amount - LAG(amount) OVER (ORDER BY date) as change,
    ROUND(
        (amount - LAG(amount) OVER (ORDER BY date)) * 100.0 / NULLIF(LAG(amount) OVER (ORDER BY date), 0),
        2
    ) as pct_change
FROM transactions;
```

### 1.4 Weighted Queries

```sql
-- Ricerca con weighted scoring
WITH relevance AS (
    SELECT 
        id,
        title,
        content,
        (
            CASE WHEN title LIKE '%python%' THEN 10 ELSE 0 END +
            CASE WHEN content LIKE '%python%' THEN 3 ELSE 0 END +
            CASE WHEN tags LIKE '%python%' THEN 5 ELSE 0 END +
            CASE WHEN author = 'expert' THEN 8 ELSE 0 END
        ) as score
    FROM articles
)
SELECT * FROM relevance
WHERE score > 0
ORDER BY score DESC;
```

---

## 2. Data Processing Patterns

### 2.1 ETL Pipeline con CTE

```sql
-- Extract, Transform, Load pattern
WITH source_data AS (
    -- Extract
    SELECT 
        id,
        name,
        email,
        created_at
    FROM raw_import
),
cleaned AS (
    -- Transform
    SELECT 
        id,
        UPPER(TRIM(name)) as name,
        LOWER(email) as email,
        DATE(created_at) as created_date
    FROM source_data
),
deduplicated AS (
    -- Deduplicate
    SELECT 
        name,
        email,
        MIN(created_date) as first_seen
    FROM cleaned
    GROUP BY name, email
    HAVING COUNT(*) = 1
)
-- Load
INSERT INTO users (name, email, registered_at)
SELECT name, email, first_seen
FROM deduplicated;
```

### 2.2 Pivot/Unpivot

```sql
-- Pivot: rows to columns
SELECT 
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
FROM orders;

-- Dynamic pivot (requires dynamic SQL in application)
```

### 2.3 Batch Processing

```sql
-- Process in batches
WITH batch AS (
    SELECT 
        rowid as rn,
        id,
        data
    FROM large_table
    WHERE processed = 0
    LIMIT 1000
)
UPDATE large_table
SET processed = 1, processed_at = CURRENT_TIMESTAMP
WHERE id IN (SELECT id FROM batch);

-- Repeat until no rows affected
-- Use in loop in application
```

### 2.4 Merge Pattern

```sql
-- Upsert/Merge pattern
INSERT INTO target_table (id, name, value, updated_at)
SELECT id, name, value, CURRENT_TIMESTAMP
FROM staging_table
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    value = excluded.value,
    updated_at = excluded.updated_at
WHERE target_table.value != excluded.value
   OR target_table.name != excluded.name;
```

---

## 3. Caching Strategies

### 3.1 Materialized Views

```sql
-- Create cache table
CREATE TABLE IF NOT EXISTS user_stats_cache (
    user_id INTEGER PRIMARY KEY,
    total_orders INTEGER DEFAULT 0,
    total_spent REAL DEFAULT 0,
    last_order_date TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Update cache
INSERT OR REPLACE INTO user_stats_cache (user_id, total_orders, total_spent, last_order_date, updated_at)
SELECT 
    user_id,
    COUNT(*) as total_orders,
    SUM(total) as total_spent,
    MAX(order_date) as last_order_date,
    CURRENT_TIMESTAMP
FROM orders
GROUP BY user_id;

-- Use cache in queries
SELECT u.*, us.total_orders, us.total_spent
FROM users u
LEFT JOIN user_stats_cache us ON u.id = us.user_id;
```

### 3.2 Cache Invalidation

```sql
-- Trigger-based cache invalidation
CREATE TRIGGER update_user_stats_cache
AFTER INSERT OR UPDATE ON orders
BEGIN
    DELETE FROM user_stats_cache 
    WHERE user_id = NEW.user_id;
END;

-- Scheduled refresh
-- Run periodically: UPDATE user_stats_cache...
PRAGMA cache_size = -8000;
```

### 3.3 Query Cache

```sql
-- Frequently accessed data cache
CREATE TABLE query_cache (
    cache_key TEXT PRIMARY KEY,
    result_json TEXT,
    expires_at TEXT
);

-- Check cache before query
SELECT result_json 
FROM query_cache 
WHERE cache_key = ? 
  AND expires_at > CURRENT_TIMESTAMP;

-- Store result in cache
INSERT INTO query_cache (cache_key, result_json, expires_at)
VALUES (?, ?, datetime('now', '+5 minutes'));
```

---

## 4. Event Sourcing

### 4.1 Event Store

```sql
-- Event store table
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregate_id TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT NOT NULL,  -- JSON
    metadata TEXT,              -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL
);

-- Append event
INSERT INTO events (aggregate_id, aggregate_type, event_type, event_data, version)
VALUES (
    'user-123',
    'User',
    'UserCreated',
    '{"name": "John", "email": "john@test.com"}',
    1
);
```

### 4.2 Projection

```sql
-- Build read model from events
CREATE TABLE user_projection AS
SELECT 
    aggregate_id as user_id,
    event_data ->>'$.name' as name,
    event_data ->>'$.email' as email,
    MIN(created_at) as created_at
FROM events
WHERE aggregate_type = 'User' AND event_type = 'UserCreated'
GROUP BY aggregate_id;

-- Update projection with new events
INSERT OR REPLACE INTO user_projection
SELECT 
    aggregate_id as user_id,
    COALESCE(
        (SELECT ep.name FROM events ep 
         WHERE ep.aggregate_id = e.aggregate_id 
           AND ep.event_type = 'UserCreated' 
         ORDER BY ep.created_at DESC LIMIT 1),
        (SELECT ep.name FROM events ep 
         WHERE ep.aggregate_id = e.aggregate_id 
           AND ep.event_type = 'UserUpdated' 
         ORDER BY ep.created_at DESC LIMIT 1)
    ) as name,
    ...
FROM events e
WHERE e.aggregate_type = 'User';
```

### 4.3 Rebuild Projection

```python
def rebuild_projection(db_path, aggregate_type):
    """Rebuild entire projection from event store"""
    conn = sqlite3.connect(db_path)
    
    # Clear projection
    conn.execute(f"DELETE FROM {aggregate_type}_projection")
    
    # Get all events for this aggregate
    events = conn.execute("""
        SELECT * FROM events 
        WHERE aggregate_type = ?
        ORDER BY created_at, version
    """, (aggregate_type,)).fetchall()
    
    # Replay events in order
    state = {}
    for event in events:
        state = apply_event(state, event)
        
        # Store state at each step
        conn.execute(f"""
            INSERT OR REPLACE INTO {aggregate_type}_projection
            VALUES (?, ?)
        """, (event['aggregate_id'], json.dumps(state)))
    
    conn.commit()
    conn.close()
```

---

## 5. CQRS Pattern

### 5.1 Command Model (Write)

```sql
-- Commands table (append-only)
CREATE TABLE commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    payload TEXT NOT NULL,  -- JSON
    user_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'  -- pending, processed, failed
);

-- Process command
INSERT INTO commands (command_type, aggregate_id, payload, user_id)
VALUES ('CreateUser', 'user-new', '{"name": "John", "email": "john@test.com"}', 'user-1');

-- Process in application
-- 1. Read pending command
-- 2. Validate
-- 3. Apply to aggregate
-- 4. Store events
-- 5. Mark command as processed
```

### 5.2 Query Model (Read)

```sql
-- Optimized read tables
CREATE TABLE user_read_model (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    created_at TEXT,
    updated_at TEXT,
    version INTEGER
);

-- Update read model from events
CREATE TRIGGER update_user_read_model
AFTER INSERT ON events
FOR EACH ROW
WHEN NEW.aggregate_type = 'User'
BEGIN
    INSERT OR REPLACE INTO user_read_model
    SELECT 
        aggregate_id,
        JSON_EXTRACT(event_data, '$.name'),
        JSON_EXTRACT(event_data, '$.email'),
        created_at,
        created_at,
        version
    FROM events
    WHERE aggregate_id = NEW.aggregate_id
    ORDER BY created_at DESC, version DESC
    LIMIT 1;
END;
```

---

## 6. Graph Algorithms

### 6.1 Adjacency List Queries

```sql
-- Find all friends of a user (1st degree)
SELECT friend_id FROM friendships 
WHERE user_id = 123;

-- Find friends of friends (2nd degree)
SELECT DISTINCT f2.friend_id
FROM friendships f1
JOIN friendships f2 ON f1.friend_id = f2.user_id
WHERE f1.user_id = 123
  AND f2.friend_id != 123;

-- Find all connections up to N degrees
WITH RECURSIVE friends AS (
    SELECT user_id, friend_id, 1 as degree
    FROM friendships
    WHERE user_id = 123
    
    UNION ALL
    
    SELECT f.user_id, f.friend_id, fr.degree + 1
    FROM friendships f
    JOIN friends fr ON f.user_id = fr.friend_id
    WHERE fr.degree < 3
)
SELECT DISTINCT friend_id, MIN(degree) as degree
FROM friends
WHERE friend_id != 123
GROUP BY friend_id
ORDER BY degree;
```

### 6.2 Shortest Path

```sql
-- Find shortest path between two nodes
WITH RECURSIVE path AS (
    -- Start
    SELECT 
        123 as start_id,
        456 as end_id,
        friend_id as current,
        friend_id as path,
        1 as steps
    FROM friendships
    WHERE user_id = 123
    
    UNION ALL
    
    -- Continue
    SELECT 
        p.start_id,
        p.end_id,
        f.friend_id,
        p.path || '->' || f.friend_id,
        p.steps + 1
    FROM path p
    JOIN friendships f ON f.user_id = p.current
    WHERE p.steps < 10  -- Max steps
      AND f.friend_id != p.start_id  -- Avoid cycles
)
SELECT path, steps
FROM path
WHERE current = end_id
ORDER BY steps
LIMIT 1;
```

### 6.3 Common Connections

```sql
-- Find mutual friends
SELECT f2.friend_id
FROM friendships f1
JOIN friendships f2 ON f1.friend_id = f2.user_id
WHERE f1.user_id = 123
  AND f2.friend_id IN (
    SELECT friend_id FROM friendships WHERE user_id = 456
  )
  AND f2.friend_id NOT IN (123, 456);
```

---

## 7. Time Series

### 7.1 Time Series Storage

```sql
-- Time series table
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    timestamp TEXT NOT NULL,
    tags TEXT  -- JSON
);

-- Index for time-based queries
CREATE INDEX idx_metrics_time ON metrics(timestamp);
CREATE INDEX idx_metrics_name_time ON metrics(metric_name, timestamp);
```

### 7.2 Aggregation

```sql
-- Daily aggregation
SELECT 
    metric_name,
    DATE(timestamp) as date,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    SUM(value) as total,
    COUNT(*) as samples
FROM metrics
WHERE timestamp >= '2024-01-01'
GROUP BY metric_name, DATE(timestamp);

-- Hourly for specific date
SELECT 
    metric_name,
    strftime('%H', timestamp) as hour,
    AVG(value) as avg_value
FROM metrics
WHERE metric_name = 'temperature'
  AND DATE(timestamp) = '2024-01-15'
GROUP BY hour;
```

### 7.3 Downsampling

```sql
-- Downsample: keep first reading per hour
WITH hourly AS (
    SELECT 
        metric_name,
        timestamp,
        value,
        ROW_NUMBER() OVER (
            PARTITION BY metric_name, strftime('%Y-%m-%d %H', timestamp)
            ORDER BY timestamp
        ) as rn
    FROM metrics
)
DELETE FROM metrics
WHERE id IN (
    SELECT id FROM hourly WHERE rn > 1
);
```

---

## 8. Full-Text Search Patterns

### 8.1 Advanced FTS Queries

```sql
-- Boolean search
SELECT * FROM articles
WHERE articles MATCH 'python AND (database OR sql) NOT java';

-- Proximity search (words within distance)
SELECT * FROM docs
WHERE docs MATCH '"machine learning" NEAR/5 neural';

-- Column-specific search
SELECT * FROM articles
WHERE title MATCH 'sqlite' 
  AND content MATCH 'database';

-- Fuzzy search (using trigram)
CREATE VIRTUAL TABLE docs USING fts5(content, tokenize='trigram');
SELECT * FROM docs WHERE docs MATCH 'data~';
```

### 8.2 FTS with Ranking

```sql
-- BM25 ranking
SELECT *, bm25(articles) as rank
FROM articles
WHERE articles MATCH 'database sqlite'
ORDER BY rank;

-- Combine with filters
SELECT *, bm25(articles) as rank
FROM articles
WHERE articles MATCH 'sql'
  AND category = 'tutorial'
ORDER BY rank;

-- Custom ranking
SELECT 
    *,
    bm25(articles) * (
        CASE WHEN category = 'tutorial' THEN 0.5 ELSE 1.0 END
    ) as adjusted_rank
FROM articles
WHERE articles MATCH 'sqlite'
ORDER BY adjusted_rank;
```

### 8.3 Search Highlighting

```sql
-- Highlight matches
SELECT 
    id,
    title,
    highlight(articles, 0, '<mark>', '</mark>') as highlighted_title,
    snippet(articles, 1, '<mark>', '</mark>', '...', 30) as snippet
FROM articles
WHERE articles MATCH 'database'
ORDER BY rank;
```

---

## 9. Spatial Data

### 9.1 Spatial Queries

```sql
-- Create spatial index
CREATE VIRTUAL TABLE locations USING rtree(
    id,
    min_lat, max_lat,
    min_lon, max_lon
);

-- Find points in bounding box
SELECT * FROM locations
WHERE min_lat >= 40.0 AND max_lat <= 41.0
  AND min_lon >= -75.0 AND max_lon <= -74.0;

-- Find points within radius (approximate)
SELECT * FROM locations
WHERE min_lat >= 40.7 - 0.1 AND max_lat <= 40.7 + 0.1
  AND min_lon >= -74.0 - 0.1 AND max_lon <= -74.0 + 0.1;
```

### 9.2 Distance Calculation

```sql
-- Haversine distance in km
WITH point AS (SELECT ? as lat, ? as lon)
SELECT 
    id,
    (6371 * acos(
        cos(point.lat * 0.0174533) * cos(lat * 0.0174533) *
        cos((lon * 0.0174533) - (point.lon * 0.0174533)) +
        sin(point.lat * 0.0174533) * sin(lat * 0.0174533)
    )) as distance_km
FROM locations, point
ORDER BY distance_km
LIMIT 10;
```

---

## 10. Data Warehouse Patterns

### 10.1 Fact Table

```sql
-- Sales fact table
CREATE TABLE fact_sales (
    id INTEGER PRIMARY KEY,
    date_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    customer_key INTEGER NOT NULL,
    store_key INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    revenue REAL NOT NULL,
    cost REAL NOT NULL,
    FOREIGN KEY (date_key) REFERENCES dim_date(id),
    FOREIGN KEY (product_key) REFERENCES dim_product(id),
    FOREIGN KEY (customer_key) REFERENCES dim_customer(id),
    FOREIGN KEY (store_key) REFERENCES dim_store(id)
);

-- Index for common queries
CREATE INDEX idx_fact_sales_date ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_product ON fact_sales(product_key);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_key);
```

### 10.2 Dimension Tables

```sql
-- Slowly Changing Dimension (Type 2)
CREATE TABLE dim_product (
    id INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL,
    name TEXT,
    category TEXT,
    effective_from TEXT,
    effective_to TEXT,
    is_current INTEGER DEFAULT 1,
    
    UNIQUE(product_id, effective_from)
);

-- Get current version
SELECT * FROM dim_product 
WHERE product_id = ? AND is_current = 1;

-- Historical query
SELECT * FROM dim_product 
WHERE product_id = ? 
  AND effective_from <= '2024-06-15' 
  AND (effective_to IS NULL OR effective_to > '2024-06-15');
```

### 10.3 Star Schema Queries

```sql
-- Simple star query
SELECT 
    d.year,
    p.category,
    SUM(f.revenue) as total_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.id
JOIN dim_product p ON f.product_key = p.id
WHERE d.year = 2024
GROUP BY d.year, p.category;

-- With multiple dimensions
SELECT 
    d.year,
    d.quarter,
    p.category,
    c.region,
    s.store_name,
    SUM(f.revenue) as revenue,
    SUM(f.quantity) as units,
    SUM(f.revenue - f.cost) as profit
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.id
JOIN dim_product p ON f.product_key = p.id
JOIN dim_customer c ON f.customer_key = c.id
JOIN dim_store s ON f.store_key = s.id
GROUP BY d.year, d.quarter, p.category, c.region, s.store_name;
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*