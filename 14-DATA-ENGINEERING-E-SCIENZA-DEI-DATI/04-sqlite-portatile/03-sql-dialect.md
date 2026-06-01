# SQLite SQL Dialect e Advanced Queries

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
1. SQL Dialect Overview
2. SELECT Advanced
3. JOIN Operations
4. Subqueries
5. Window Functions
6. CTEs
7. Aggregation
8. JSON Support
9. Full-Text Search
10. Advanced Patterns

---

## 1. SQL Dialect Overview

### 1.1 SQLite SQL Features

SQLite supporta la maggioranza dello standard SQL con alcune differenze:

```sql
-- Supported:
-- SELECT, INSERT, UPDATE, DELETE
-- CREATE TABLE, INDEX, VIEW
-- JOINs, subqueries, CTEs
-- Window functions (SQLite 3.25+)
-- Recursive queries

-- Different/limited:
-- No FOREIGN KEY enforcement by default
-- No ALTER TABLE ADD COLUMN (rename + copy)
-- Limited ALTER TABLE (rename, add index)
-- No CHECK constraints (before 3.37)
-- No GRANT/REVOKE (embedded DB)
```

### 1.2 Type Affinity System

SQLite utilizza un sistema di type affinity dove i tipi dichiarati sono convertiti in uno dei 5 tipi base:

```sql
-- Type affinity mapping:
-- INTEGER: INTEGER, INT, TINYINT, SMALLINT, MEDIUMINT, BIGINT, UNSIGNED BIG INT
-- REAL: REAL, DOUBLE, FLOAT, NUMERIC, DECIMAL
-- TEXT: TEXT, VARCHAR, CHARACTER, VARCHAR, VARYING CHARACTER, NCHAR, NATIVE CHARACTER, CLOB
-- BLOB: BLOB, NONE
-- (no affinity): Everything else

CREATE TABLE type_test (
    -- Questi saranno interpretati come INTEGER
    my_int INTEGER,
    my_bigint BIGINT,
    
    -- TEXT affinity
    my_text TEXT,
    my_varchar VARCHAR(100),
    
    -- REAL affinity
    my_real REAL,
    my_numeric NUMERIC,
    
    -- BLOB affinity
    my_blob BLOB,
    
    -- No affinity - stored as NULL if can't be converted
    my_anything ANYTHING
);

-- Insert con type flexibility
INSERT INTO type_test VALUES (
    42,                -- Integer
    999999999999,     -- Big integer
    'Hello World',     -- Text
    'Some string',    -- Varchar 
    3.14159,          -- Real
    42.5,             -- Numeric
    X'48656C6C6F',    -- Blob (hex)
    'anything here'   -- No affinity
);
```

### 1.3 Type Affinity Behavior

```sql
-- Comportamento dell'affinity:
-- SQLite cerca di memorizzare il valore nel tipo indicato

-- Se il valore è "42", viene memorizzato:
-- - come INTEGER se la colonna ha affinity INTEGER
-- - come TEXT se la colonna ha affinity TEXT

-- Esempio pratico:
CREATE TABLE affinity_test (
    int_col INTEGER,
    text_col TEXT,
    real_col REAL
);

INSERT INTO affinity_test VALUES ('42', '42', '42');

SELECT 
    int_col, typeof(int_col),  -- 42, integer
    text_col, typeof(text_col),-- 42, text  
    real_col, typeof(real_col) -- 42.0, real
FROM affinity_test;
```

### 1.4 Strict Typing Mode (SQLite 3.37+)

```sql
-- SQLite 3.37+ supporta strict typing
CREATE TABLE strict_test (
    id INTEGER,
    name TEXT STRICT,
    price REAL STRICT
) STRICT;

-- In STRICT mode:
-- - TEXT columns solo TEXT
-- - INTEGER columns solo INTEGER  
-- - REAL columns solo REAL
-- - NULL allowed in any column
-- - BLOB columns solo BLOB

-- Trying to insert wrong type raises error
INSERT INTO strict_test VALUES (1, 42, 3.14);  -- Error: name should be TEXT
```

### 1.5 Type Conversion Functions

```sql
-- CAST per conversione esplicita
SELECT 
    CAST('42' AS INTEGER),      -- 42
    CAST(42 AS TEXT),           -- '42'
    CAST('3.14' AS REAL),       -- 3.14
    CAST(42 AS BLOB),           -- X'2A'
    CAST(X'2A' AS INTEGER);     -- 42

-- typeof() per vedere il tipo
SELECT typeof(42),              -- integer
       typeof('42'),            -- text
       typeof(42.0),            -- real
       typeof(X'00'),          -- blob
       typeof(NULL);           -- null

-- Gruppo e coalesce
SELECT COALESCE(NULL, NULL, 'default'),  -- 'default'
       NULLIF(5, 5),                      -- NULL
       IFNULL(NULL, 'replacement'),       -- 'replacement'
       IIF(1 > 0, 'yes', 'no');           -- 'yes'
```

---

## 2. SELECT Advanced

### 2.1 CASE Expressions

```sql
-- Simple CASE
SELECT 
    name,
    CASE status
        WHEN 'active' THEN 'Active'
        WHEN 'inactive' THEN 'Inactive'
        ELSE 'Unknown'
    END as status_text
FROM users;

-- Searched CASE
SELECT 
    name,
    CASE 
        WHEN price > 100 THEN 'Premium'
        WHEN price > 50 THEN 'Standard'
        ELSE 'Budget'
    END as category
FROM products;

-- CASE in WHERE
SELECT * FROM orders
WHERE CASE 
    WHEN status = 'pending' AND created_at < datetime('now', '-7 days') 
    THEN 1
    WHEN status = 'cancelled' 
    THEN 1
    ELSE 0
END = 1;

-- CASE per pivot
SELECT 
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
FROM orders;
```

### 2.2 DISTINCT ON

```sql
-- SQLite doesn't have DISTINCT ON
-- Use subquery with ROW_NUMBER
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY id) as rn
    FROM products
) WHERE rn = 1;

-- Alternative: GROUP BY with MAX
SELECT p.*
FROM products p
JOIN (
    SELECT category, MIN(id) as min_id
    FROM products
    GROUP BY category
) sub ON p.id = sub.min_id;
```

### 2.3 LIMIT e OFFSET

```sql
-- Pagination
SELECT * FROM users 
ORDER BY name 
LIMIT 10 OFFSET 20;

-- Alternative keyset pagination
SELECT * FROM users 
WHERE id > 20 
ORDER BY id 
LIMIT 10;

-- Cursor-based pagination (more efficient)
-- First page:
SELECT * FROM posts ORDER BY created_at DESC LIMIT 20;
-- Next page (use last cursor):
SELECT * FROM posts 
WHERE created_at < '2024-01-15 10:30:00' 
ORDER BY created_at DESC 
LIMIT 20;

-- LIMIT con espressioni
-- Numero dinamico di righe
SET @page_size = 10;
SELECT * FROM users LIMIT @page_size;

-- Offset con calcoli
SELECT * FROM users 
LIMIT 10 OFFSET (SELECT COUNT(*) / 10 FROM users) * 10;
```

### 2.4 EXPLAIN e Query Analysis

```sql
-- Explain semplice
EXPLAIN QUERY PLAN 
SELECT * FROM users WHERE email = 'test@example.com';

-- Explain con ANALYZE (esegue la query)
EXPLAIN QUERY PLAN 
SELECT * FROM orders 
JOIN customers ON orders.customer_id = customers.id
WHERE customers.country = 'USA';

-- Output tipico:
-- SCAN TABLE orders
-- SEARCH TABLE customers USING INDEX idx_customer_id (id=?)
-- B-tree, Using covering index, etc.

-- Verificare uso indici
PRAGMA index_list(orders);
PRAGMA index_info(idx_orders_customer);
PRAGMA query_planner;
```

### 2.5 Materialization e Subquery

```sql
-- Subquery materializzata vs correlata
-- Materialized (una sola esecuzione):
SELECT * FROM (
    SELECT * FROM large_table WHERE status = 'active'
) sub;

-- Correlated (eseguita per ogni riga):
SELECT * FROM products p
WHERE price > (
    SELECT AVG(price) FROM products 
    WHERE category_id = p.category_id
);

-- FORzar e materialization con CTE:
WITH avg_price AS (
    SELECT category_id, AVG(price) as avg FROM products GROUP BY category_id
)
SELECT p.*, a.avg
FROM products p
JOIN avg_price a ON p.category_id = a.category_id;
```

### 2.6 Dynamic SQL Patterns

```sql
-- Query con condizioni dinamiche
-- Costruire WHERE clause based su parametri

-- Pattern: Search con filtri opzionali
-- In application code:
-- query = "SELECT * FROM products WHERE 1=1"
-- if (category) query += " AND category_id = " + category
-- if (min_price) query += " AND price >= " + min_price

-- Con parametri:
SELECT * FROM products
WHERE 1 = 1
  AND (? IS NULL OR category_id = ?)
  AND (? IS NULL OR price >= ?);

-- Usando COALESCE per parametri opzionali
SELECT * FROM products
WHERE category_id = COALESCE(@category_id, category_id)
  AND price >= COALESCE(@min_price, 0);

-- ORDER BY dinamico
SELECT * FROM products
ORDER BY 
    CASE WHEN @sort = 'price' THEN price END,
    CASE WHEN @sort = 'name' THEN name END,
    CASE WHEN @sort = 'date' THEN created_at END;
```

---

## 3. JOIN Operations

### 3.1 JOIN Types

```sql
-- INNER JOIN
SELECT * FROM orders o
INNER JOIN customers c ON o.customer_id = c.id;

-- LEFT JOIN
SELECT * FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id;

-- CROSS JOIN
SELECT * FROM colors, sizes;
SELECT * FROM colors CROSS JOIN sizes;

-- Self JOIN
SELECT a.name as employee, b.name as manager
FROM employees a
LEFT JOIN employees b ON a.manager_id = b.id;

-- RIGHT JOIN - non supportato direttamente
-- Emulare con LEFT JOIN
SELECT c.*, o.*
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id;
```

### 3.2 Multiple JOINs

```sql
SELECT 
    o.id,
    c.name as customer,
    p.name as product,
    oi.quantity,
    oi.unit_price
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'completed';

-- JOIN con condizioni multiple
SELECT *
FROM table_a a
JOIN table_b b 
    ON a.id = b.a_id 
   AND b.status = 'active'
   AND b.deleted_at IS NULL;
```

### 3.3 JOIN con aggregazioni

```sql
-- LEFT JOIN con aggregazione
SELECT 
    c.id,
    c.name,
    COUNT(o.id) as order_count,
    SUM(o.total) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id;

-- JOIN con subquery
SELECT 
    c.name,
    latest_order.order_date,
    latest_order.total
FROM customers c
LEFT JOIN (
    SELECT customer_id, order_date, total,
           ROW_NUMBER() OVER (PARTITION BY customer_id 
                              ORDER BY order_date DESC) as rn
    FROM orders
) latest_order ON c.id = latest_order.customer_id 
               AND latest_order.rn = 1;
```

### 3.4 Lateral JOIN (SQLite 3.30+)

```sql
-- Lateral JOIN: subquery che referenzia righe precedenti
-- Utile per top-N per group

SELECT c.name, o.*
FROM customers c
LEFT JOIN LATERAL (
    SELECT * FROM orders 
    WHERE customer_id = c.id
    ORDER BY order_date DESC
    LIMIT 5
) o ON 1=1;

-- Equivalente a: per ogni cliente, prendi i suoi ultimi 5 ordini

-- Lateral JOIN per calcoli cumulativi
SELECT 
    d.date,
    d.sales,
    (SELECT SUM(sales) FROM daily_sales 
     WHERE date <= d.date) as running_total
FROM daily_sales d;
```

### 3.5 Join Ordering

```sql
-- SQLite optimizer sceglie join order
-- Ma possiamo influenzare con hints

-- Force join order (non sempre supportato)
SELECT /*+ ORDERED */
    o.id, c.name, p.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id;

-- Hint per usare specifico index
SELECT * FROM orders INDEXED BY idx_orders_customer
WHERE customer_id = 1;

-- Verificare piano di query
EXPLAIN QUERY PLAN 
SELECT o.*, c.*
FROM orders o
JOIN customers c ON o.customer_id = c.id;
```

---

## 4. Subqueries

### 4.1 Scalar Subquery

```sql
-- Subquery in SELECT
SELECT 
    name,
    (SELECT COUNT(*) FROM orders WHERE customer_id = c.id) as order_count
FROM customers c;

-- Subquery che ritorna NULL
-- In alcuni DB errore, SQLite ritorna NULL
SELECT 
    (SELECT max(price) FROM products WHERE category_id = 999) as max_price;
    -- Returns NULL (no matching category)

-- Subquery con aggregazione
SELECT 
    p.*,
    (SELECT COUNT(*) FROM order_items WHERE product_id = p.id) as times_ordered
FROM products p;
```

### 4.2 Subquery in WHERE

```sql
-- IN subquery
SELECT * FROM products
WHERE category_id IN (
    SELECT id FROM categories WHERE active = 1
);

-- NOT IN (attenzione a NULLs)
SELECT * FROM products
WHERE category_id NOT IN (
    SELECT id FROM categories WHERE active = 1
);
-- Se subquery ritorna NULL, NOT IN fallisce!

-- EXISTS
SELECT * FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);

-- NOT EXISTS
SELECT * FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);

-- IN con tuple
SELECT * FROM orders
WHERE (customer_id, status) IN (
    SELECT id, 'pending' FROM customers WHERE vip = 1
);
```

### 4.3 Correlated Subqueries

```sql
-- Subquery referencing outer query
SELECT * FROM products p
WHERE price > (
    SELECT AVG(price) FROM products 
    WHERE category_id = p.category_id
);

-- Subquery nella SET clause di UPDATE
UPDATE products
SET stock = stock - 1
WHERE id IN (
    SELECT product_id FROM order_items
    WHERE order_id = 123
);

-- Subquery con GROUP BY
SELECT *
FROM employees e
WHERE salary > (
    SELECT AVG(salary) 
    FROM employees 
    WHERE department_id = e.department_id
);
```

### 4.4 Subquery Flattening

SQLite spesso appiattisce le subquery in join per efficienza:

```sql
-- Questa subquery viene "flattened":
SELECT * FROM products p
WHERE category_id IN (SELECT id FROM categories);

-- Diventa:
SELECT p.* FROM products p
JOIN categories c ON p.category_id = c.id;

-- Controllare con EXPLAIN:
EXPLAIN QUERY PLAN 
SELECT * FROM products p
WHERE category_id = (
    SELECT id FROM categories LIMIT 1
);

-- Vediamo se c'è subquery o join nel piano
```

### 4.5 Subquery nella FROM

```sql
-- Subquery come derived table
SELECT * FROM (
    SELECT category, AVG(price) as avg_price
    FROM products
    GROUP BY category
) sub
WHERE avg_price > 50;

-- Multiple subqueries in FROM
SELECT 
    sub1.category,
    sub1.avg_price,
    sub2.total_products
FROM (
    SELECT category, AVG(price) as avg_price
    FROM products
    GROUP BY category
) sub1
JOIN (
    SELECT category, COUNT(*) as total_products
    FROM products
    GROUP BY category
) sub2 ON sub1.category = sub2.category;
```

---

## 5. Window Functions

### 5.1 Window Function Types (SQLite 3.25+)

```sql
-- Aggregate over window
SELECT 
    name,
    price,
    AVG(price) OVER () as avg_price
FROM products;

-- ROW_NUMBER
SELECT 
    name,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) as rank
FROM products;

-- RANK and DENSE_RANK
SELECT 
    name,
    price,
    RANK() OVER (ORDER BY price DESC) as rank,
    DENSE_RANK() OVER (ORDER BY price DESC) as dense_rank
FROM products;

-- LAG and LEAD
SELECT 
    name,
    price,
    LAG(price) OVER (ORDER BY price) as prev_price,
    LEAD(price) OVER (ORDER BY price) as next_price
FROM products;

-- FIRST_VALUE, LAST_VALUE
SELECT 
    name,
    price,
    FIRST_VALUE(name) OVER (ORDER BY price) as cheapest_product,
    LAST_VALUE(name) OVER (ORDER BY price) as most_expensive
FROM products;

-- NTH_VALUE (SQLite 3.25+)
SELECT 
    name,
    price,
    NTH_VALUE(price, 3) OVER (ORDER BY price) as third_price
FROM products;
```

### 5.2 PARTITION BY

```sql
-- Partition by category
SELECT 
    name,
    category,
    price,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) as rank
FROM products;

-- Multiple partitions
SELECT 
    name,
    category,
    region,
    price,
    ROW_NUMBER() OVER (PARTITION BY category, region ORDER BY price DESC) as rank
FROM products;

-- Partition con aggregati
SELECT 
    name,
    category,
    price,
    AVG(price) OVER (PARTITION BY category) as category_avg,
    price - AVG(price) OVER (PARTITION BY category) as diff_from_avg
FROM products;
```

### 5.3 Window Frame

```sql
-- Frame: ROWS BETWEEN
-- Ultime 2 righe (incluso current)
SELECT 
    name,
    order_date,
    amount,
    SUM(amount) OVER (
        ORDER BY order_date 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) as rolling_sum_3
FROM orders;

-- Tutte le righe precedenti
SELECT 
    name,
    price,
    SUM(price) OVER (
        ORDER BY price 
        ROWS UNBOUNDED PRECEDING
    ) as cumulative_price
FROM products;

-- RANGE BETWEEN (per valori uguali)
SELECT 
    name,
    price,
    SUM(price) OVER (
        ORDER BY price 
        RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as range_cumulative
FROM products;

-- Following rows
SELECT 
    name,
    price,
    AVG(price) OVER (
        ORDER BY price 
        ROWS BETWEEN CURRENT ROW AND 2 FOLLOWING
    ) as next_2_avg
FROM products;
```

### 5.4 Named Windows

```sql
-- Definire window una volta e riutilizzarlo
SELECT 
    name,
    price,
    AVG(price) OVER w as avg_price,
    COUNT(*) OVER w as count,
    RANK() OVER w as rank
FROM products
WINDOW w AS (ORDER BY price);

-- Window con partition
SELECT 
    name,
    category,
    price,
    AVG(price) OVER w as cat_avg,
    COUNT(*) OVER w as cat_count
FROM products
WINDOW w AS (PARTITION BY category ORDER BY price);
```

### 5.5 Window Functions in Practice

```sql
-- Percentile calculation
SELECT 
    name,
    price,
    ROUND(
        (CAST(ROW_NUMBER() OVER (ORDER BY price) AS REAL) / 
         COUNT(*) OVER ()) * 100, 1
    ) as percentile
FROM products
ORDER BY price;

-- Running difference
SELECT 
    date,
    amount,
    amount - LAG(amount) OVER (ORDER BY date) as diff
FROM transactions;

-- Top N per group con window function
SELECT * FROM (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) as rn
    FROM products
) ranked
WHERE rn <= 3;

-- Moving average (7-day)
SELECT 
    date,
    value,
    AVG(value) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as ma_7
FROM metrics;
```

---

## 6. CTEs (Common Table Expressions)

### 6.1 Basic CTE

```sql
-- Simple CTE
WITH active_customers AS (
    SELECT * FROM customers WHERE status = 'active'
)
SELECT * FROM active_customers WHERE country = 'USA';

-- CTE con aggregazione
WITH category_stats AS (
    SELECT 
        category_id,
        COUNT(*) as cnt,
        AVG(price) as avg_price
    FROM products
    GROUP BY category_id
)
SELECT 
    c.name,
    cs.cnt,
    cs.avg_price
FROM categories c
JOIN category_stats cs ON c.id = cs.category_id;
```

### 6.2 Multiple CTEs

```sql
-- Multiple CTEs
WITH 
    us_customers AS (
        SELECT * FROM customers WHERE country = 'USA'
    ),
    recent_orders AS (
        SELECT * FROM orders WHERE date > '2024-01-01'
    ),
    us_orders AS (
        SELECT * FROM recent_orders WHERE customer_id IN (
            SELECT id FROM us_customers
        )
    )
SELECT 
    c.name,
    COUNT(o.id) as order_count,
    SUM(o.total) as total_spent
FROM us_customers c
LEFT JOIN us_orders o ON c.id = o.customer_id
GROUP BY c.id;
```

### 6.3 Recursive CTE

```sql
-- Hierarchical data
WITH RECURSIVE org_tree AS (
    -- Base case
    SELECT id, name, manager_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case
    SELECT e.id, e.name, e.manager_id, ot.level + 1
    FROM employees e
    JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT * FROM org_tree;

-- Tree traversal con path
WITH RECURSIVE path_tree AS (
    SELECT id, name, parent_id, name as path, 1 as level
    FROM categories
    WHERE parent_id IS NULL
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, 
           pt.path || ' > ' || c.name,
           pt.level + 1
    FROM categories c
    JOIN path_tree pt ON c.parent_id = pt.id
)
SELECT * FROM path_tree ORDER BY path;

-- Find all descendants
WITH RECURSIVE descendants AS (
    SELECT id, name, parent_id, 0 as depth
    FROM categories WHERE id = 1
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, d.depth + 1
    FROM categories c
    JOIN descendants d ON c.parent_id = d.id
)
SELECT * FROM descendants;
```

### 6.4 CTE per Analytics

```sql
-- Running totals con CTE
WITH daily_sales AS (
    SELECT date, SUM(amount) as daily_total
    FROM orders
    GROUP BY date
),
running AS (
    SELECT 
        date,
        daily_total,
        (SELECT SUM(daily_total) 
         FROM daily_sales d2 
         WHERE d2.date <= d1.date) as running_total
    FROM daily_sales d1
)
SELECT * FROM running;

-- Percentile con CTE
WITH ranked AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY price) as rn,
        COUNT(*) OVER () as total
    FROM products
)
SELECT 
    name,
    price,
    ROUND((rn * 100.0 / total), 1) as percentile
FROM ranked;
```

### 6.5 CTE per Data Transformation

```sql
-- Pivot con CTE
WITH base AS (
    SELECT 
        category,
        status,
        COUNT(*) as cnt
    FROM products
    GROUP BY category, status
),
pivoted AS (
    SELECT category,
        SUM(CASE WHEN status = 'active' THEN cnt ELSE 0 END) as active,
        SUM(CASE WHEN status = 'inactive' THEN cnt ELSE 0 END) as inactive,
        SUM(CASE WHEN status = 'discontinued' THEN cnt ELSE 0 END) as discontinued
    FROM base
    GROUP BY category
)
SELECT * FROM pivoted;

-- Unpivot (da column-based a row-based)
WITH expanded AS (
    SELECT category, 
           'active' as status, active as count 
    FROM pivoted WHERE active > 0
    UNION ALL
    SELECT category, 'inactive', inactive FROM pivoted WHERE inactive > 0
    UNION ALL
    SELECT category, 'discontinued', discontinued FROM pivoted WHERE discontinued > 0
)
SELECT * FROM expanded ORDER BY category;
```

---

## 7. Aggregation

### 7.1 Aggregate Functions

```sql
-- Standard aggregates
SELECT 
    COUNT(*) as total,
    SUM(price) as total_price,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products;

-- GROUP_CONCAT
SELECT category, GROUP_CONCAT(name) as products
FROM products
GROUP BY category;

-- GROUP_CONCAT con separator
SELECT category, GROUP_CONCAT(name, ', ') as products
FROM products
GROUP BY category;

-- GROUP_CONCAT con ORDER
SELECT category, GROUP_CONCAT(name ORDER BY price DESC) as products
FROM products
GROUP BY category;

-- DISTINCT aggregate
SELECT 
    COUNT(DISTINCT category_id) as unique_categories,
    SUM(DISTINCT price) as sum_of_unique_prices
FROM products;
```

### 7.2 GROUP BY

```sql
-- Basic GROUP BY
SELECT 
    category,
    COUNT(*) as count,
    AVG(price) as avg_price
FROM products
GROUP BY category;

-- GROUP BY multiple columns
SELECT 
    category,
    status,
    COUNT(*) as count,
    SUM(stock) as total_stock
FROM products
GROUP BY category, status;

-- HAVING
SELECT 
    category,
    COUNT(*) as count
FROM products
GROUP BY category
HAVING COUNT(*) > 5;

-- HAVING con subquery
SELECT 
    category,
    AVG(price) as avg_price
FROM products
GROUP BY category
HAVING AVG(price) > (
    SELECT AVG(price) FROM products
) / 2;
```

### 7.3 FILTER Clause (SQLite 3.30+)

```sql
-- FILTER per condizioni aggregate
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'active') as active_count,
    SUM(price) FILTER (WHERE category = 'electronics') as electronics_sum,
    AVG(price) FILTER (WHERE stock > 0) as avg_available_price
FROM products;

-- Equivalente a CASE in aggregate
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count
FROM products;
```

### 7.4 Aggregate con NULL handling

```sql
-- AVG ignora NULL
-- SUM ignora NULL
SELECT AVG(price), SUM(price) FROM products;

-- Aggregare ignorando zeri
SELECT 
    AVG(CASE WHEN price > 0 THEN price ELSE NULL END) as avg_nonzero
FROM products;

-- COUNT ignora NULL nella colonna specificata
-- Ma COUNT(*) conta tutte le righe
SELECT 
    COUNT(*) as all_rows,
    COUNT(price) as rows_with_price
FROM products;
```

---

## 8. JSON Support

### 8.1 JSON Functions (SQLite 3.38+)

```sql
-- Create JSON
SELECT JSON('{"a": 1, "b": 2}');

-- Extract values
SELECT JSON_EXTRACT('{"a":1,"b":2}', '$.a');  -- 1
SELECT JSON_EXTRACT('{"a":1,"b":2}', '$.b');  -- 2

-- Paths
SELECT JSON_EXTRACT('{"a":[1,2,3]}', '$.a[0]');  -- 1

-- Modify JSON
SELECT JSON_SET('{"a":1}', '$.b', 2);  -- {"a":1,"b":2}
SELECT JSON_INSERT('{"a":1}', '$.b', 2);  -- {"a":1,"b":2}
SELECT JSON_REMOVE('{"a":1,"b":2}', '$.b');  -- {"a":1}

-- Array operations
SELECT JSON_ARRAY(1, 2, 3);  -- [1,2,3]
SELECT JSON_EXTRACT('[1,2,3]', '$[0]');  -- 1
SELECT JSON_EACH('[1,2,3]');  -- table-valued function
```

### 8.2 JSON in Tables

```sql
-- JSON column
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    data TEXT  -- JSON stored as text
);

-- Query JSON
SELECT * FROM events 
WHERE JSON_EXTRACT(data, '$.type') = 'click';

-- Index JSON (virtual column)
CREATE TABLE events2 (
    id INTEGER PRIMARY KEY,
    data TEXT,
    event_type TEXT GENERATED ALWAYS AS (JSON_EXTRACT(data, '$.type'))
);

CREATE INDEX idx_events_type ON events2(event_type);

-- JSON con multiple fields
CREATE TABLE logs (
    id INTEGER PRIMARY KEY,
    payload TEXT,
    level TEXT GENERATED ALWAYS AS (JSON_EXTRACT(payload, '$.level')),
    message TEXT GENERATED ALWAYS AS (JSON_EXTRACT(payload, '$.message')),
    timestamp TEXT GENERATED ALWAYS AS (JSON_EXTRACT(payload, '$.timestamp'))
);

CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
```

### 8.3 JSON Table-Valued Functions

```sql
-- JSON_EACH per iterare
SELECT * FROM JSON_EACH('{"a":1,"b":2}');
-- key, value, type

-- JSON_TREE per struttura completa
SELECT * FROM JSON_TREE('{"a":[1,2,3]}');

-- Estrarre tabella da JSON array
SELECT * FROM JSON_EACH('[{"id":1,"name":"John"},{"id":2,"name":"Jane"}]');

-- Usare in query
WITH json_data AS (
    SELECT JSON_EACH('[1,2,3,4,5]') as item
)
SELECT item.value FROM json_data;

-- Estrai array come rows
CREATE TABLE orders (
    id INTEGER,
    items TEXT  -- JSON array
);

SELECT 
    o.id,
    j.value as item
FROM orders o, JSON_EACH(o.items, '$') as j;
```

### 8.4 JSON Operations

```sql
-- Valid JSON
SELECT JSON_VALID('{"a":1}');  -- 1
SELECT JSON_VALID('not json');  -- 0

-- JSON type
SELECT JSON_TYPE('{"a":1}', '$.a');  -- integer
SELECT JSON_TYPE('[1,2]', '$[0]');  -- integer
SELECT JSON_TYPE('null', '$');  -- null

-- JSON patch
SELECT JSON_PATCH(
    '{"a":1,"b":2}',
    '{"b":3,"c":4}'
);  -- {"a":1,"b":3,"c":4}

-- JSON stringify
SELECT JSON('{"a":1}');  -- '{"a":1}'
```

### 8.5 Complex JSON Queries

```sql
-- Nested JSON extraction
SELECT 
    JSON_EXTRACT(data, '$.user.profile.name') as name,
    JSON_EXTRACT(data, '$.orders[0].total') as first_order
FROM events;

-- JSON con WHERE
SELECT * FROM events
WHERE JSON_EXTRACT(data, '$.type') = 'purchase'
  AND JSON_EXTRACT(data, '$.amount') > 100;

-- Aggregare JSON array
SELECT 
    JSON_GROUP_ARRAY(name) as names
FROM users;
-- Ritorna: '["John","Jane","Bob"]'

-- JSON_OBJECT
SELECT 
    JSON_OBJECT('name', name, 'age', age) as json_data
FROM users;
```

---

## 9. Full-Text Search

### 9.1 FTS5 Basics

```sql
-- Create FTS5 virtual table
CREATE VIRTUAL TABLE articles USING fts5(
    title,
    content,
    tokenize='porter'
);

-- Insert data
INSERT INTO articles (title, content) VALUES
    ('SQLite Tutorial', 'Learn SQLite database...'),
    ('FTS5 Search', 'Full-text search in SQLite...');

-- Search
SELECT * FROM articles 
WHERE articles MATCH 'SQLite';

-- Search in specific column
SELECT * FROM articles 
WHERE title MATCH 'SQLite';

-- Match boolean
SELECT * FROM articles 
WHERE articles MATCH 'SQLite AND database';
```

### 9.2 FTS5 Options

```sql
-- Trigram tokenizer (SQLite 3.31+)
CREATE VIRTUAL TABLE docs USING fts5(
    content,
    tokenize='trigram'
);

-- Unicode61 tokenizer (better international)
CREATE VIRTUAL TABLE docs_unicode USING fts5(
    content,
    tokenize='unicode61'
);

-- With stopwords
CREATE VIRTUAL TABLE docs_stop USING fts5(
    content,
    tokenize='porter',
    stopwords='english'
);

-- Prefix indexes
CREATE VIRTUAL TABLE docs_prefix USING fts5(
    content,
    prefix='2 3 4 5'  -- prefix lengths
);
```

### 9.3 FTS5 Search Features

```sql
-- Highlight results
SELECT highlight(title, 0, '<b>', '</b>') as title,
       snippet(content, 0, '<b>', '</b>', '...', 20) as content
FROM articles 
WHERE articles MATCH 'database';

-- Snippet options
-- snippet(text, col, start, end, ellipsis, max_tokens)

-- BM25 ranking (default)
SELECT *, bm25(articles) as rank
FROM articles
WHERE articles MATCH 'SQLite'
ORDER BY rank;

-- Custom ranking
SELECT *, bm25(articles, 1.0, 1.0, 1.0) as rank
FROM articles
WHERE articles MATCH 'query';

-- Query with expansion
SELECT * FROM articles
WHERE articles MATCH 'SQLite*';  -- prefix search
```

### 9.4 FTS5 Maintenance

```sql
-- Rebuild FTS index
INSERT INTO articles(articles) VALUES('rebuild');

-- Optimize FTS
INSERT INTO articles(articles) VALUES('optimize');

-- Check integrity
INSERT INTO articles(articles) VALUES('integrity-check');

-- Get FTS info
PRAGMA index_info(articles);

-- Delete all from FTS keeping structure
DELETE FROM articles;

-- Recover from corruption
-- Use .recover command in CLI
-- Or rebuild programmatically
```

### 9.5 Advanced FTS5 Patterns

```sql
-- Phrase search
SELECT * FROM articles WHERE articles MATCH '"full text search"';

-- Column filter in query
SELECT * FROM articles 
WHERE articles MATCH 'title:SQLite AND content:database';

-- NOT operator
SELECT * FROM articles 
WHERE articles MATCH 'SQLite NOT oracle';

-- OR with grouping
SELECT * FROM articles 
WHERE articles MATCH '(SQLite OR MySQL) AND database';

-- Use with regular columns
SELECT a.*, f.rank
FROM articles a
JOIN (
    SELECT rowid, bm25(articles) as rank
    FROM articles
    WHERE articles MATCH 'SQLite'
    ORDER BY rank
    LIMIT 10
) f ON a.rowid = f.rowid;
```

### 9.6 FTS5 Triggers

```sql
-- Sync FTS with main table
CREATE TRIGGER articles_ai AFTER INSERT ON real_articles BEGIN
    INSERT INTO articles(rowid, title, content) 
    VALUES (new.id, new.title, new.content);
END;

CREATE TRIGGER articles_ad AFTER DELETE ON real_articles BEGIN
    DELETE FROM articles WHERE rowid = old.id;
END;

CREATE TRIGGER articles_au AFTER UPDATE ON real_articles BEGIN
    DELETE FROM articles WHERE rowid = old.id;
    INSERT INTO articles(rowid, title, content) 
    VALUES (new.id, new.title, new.content);
END;
```

---

## 10. Advanced Patterns

### 10.1 Upsert (INSERT OR REPLACE)

```sql
-- SQLite 3.24+
INSERT INTO users (id, name, email)
VALUES (1, 'John', 'john@example.com')
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    email = excluded.email;

-- ON CONFLICT DO NOTHING
INSERT INTO products (id, name)
VALUES (1, 'Widget')
ON CONFLICT(id) DO NOTHING;

-- ON CONFLICT with CHECK constraint
INSERT INTO inventory (product_id, quantity)
VALUES (1, 10)
ON CONFLICT(product_id) DO UPDATE SET
    quantity = quantity + excluded.quantity;

-- Multiple ON CONFLICT (SQLite 3.24+)
INSERT INTO items (sku, name, price, updated_at)
VALUES ('ABC123', 'Product', 9.99, CURRENT_TIMESTAMP)
ON CONFLICT(sku) DO UPDATE SET
    name = excluded.name,
    price = excluded.price,
    updated_at = excluded.updated_at
WHERE items.updated_at < excluded.updated_at;
```

### 10.2 Returning Clause

```sql
-- Get inserted/updated values
INSERT INTO users (name, email)
VALUES ('Jane', 'jane@example.com')
RETURNING id, name;

DELETE FROM users 
WHERE status = 'inactive'
RETURNING id, name, email;

UPDATE products 
SET stock = stock - 1
WHERE id = 1
RETURNING id, stock;

-- Use in subquery
WITH new_user AS (
    INSERT INTO users (name, email)
    VALUES ('New User', 'new@example.com')
    RETURNING id
)
INSERT INTO user_profiles (user_id, created_at)
SELECT id, CURRENT_TIMESTAMP
FROM new_user;

-- Multiple rows
INSERT INTO audit_log (action, created_at)
VALUES 
    ('action1', CURRENT_TIMESTAMP),
    ('action2', CURRENT_TIMESTAMP)
RETURNING *;
```

### 10.3 Row Value Comparisons

```sql
-- Row values in IN
SELECT * FROM orders
WHERE (status, region) IN (('pending', 'US'), ('active', 'EU'));

-- Row values in BETWEEN
SELECT * FROM products
WHERE (min_price, max_price) BETWEEN (10, 20) AND (50, 100);

-- Row value comparison
SELECT * FROM products
WHERE (category, price) = (SELECT category, AVG(price) FROM products);
```

### 10.4 PRAGMA per Query

```sql
-- Query con PRAGMA
PRAGMA table_info(products);
PRAGMA index_list(products);
PRAGMA index_info(idx_products_category);

-- Foreign keys
PRAGMA foreign_key_list(products);

-- Table schema
PRAGMA schema(products);

-- Quick query stats
PRAGMA query_only = 1;  -- Read-only mode
PRAGMA cache_size = -4000;  -- 4MB cache
```

### 10.5 Common Patterns

```sql
-- Batch insert
INSERT INTO products (name, price) VALUES 
    ('Product A', 10.00),
    ('Product B', 20.00),
    ('Product C', 30.00);

-- Upsert pattern completo
INSERT INTO stats (date, views, clicks)
VALUES ('2024-01-01', 100, 10)
ON CONFLICT(date) DO UPDATE SET
    views = stats.views + excluded.views,
    clicks = stats.clicks + excluded.clicks
RETURNING *;

-- Conditional insert
INSERT INTO logs (level, message)
SELECT 'ERROR', 'Something failed'
WHERE (SELECT COUNT(*) FROM logs WHERE level = 'ERROR') < 1000;
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*

---

## 2. SELECT Advanced

### 2.1 CASE Expressions

```sql
-- Simple CASE
SELECT 
    name,
    CASE status
        WHEN 'active' THEN 'Active'
        WHEN 'inactive' THEN 'Inactive'
        ELSE 'Unknown'
    END as status_text
FROM users;

-- Searched CASE
SELECT 
    name,
    CASE 
        WHEN price > 100 THEN 'Premium'
        WHEN price > 50 THEN 'Standard'
        ELSE 'Budget'
    END as category
FROM products;
```

### 2.2 DISTINCT ON

```sql
-- SQLite doesn't have DISTINCT ON
-- Use subquery with ROW_NUMBER
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY id) as rn
    FROM products
) WHERE rn = 1;
```

### 2.3 LIMIT e OFFSET

```sql
-- Pagination
SELECT * FROM users 
ORDER BY name 
LIMIT 10 OFFSET 20;

-- Alternative keyset pagination
SELECT * FROM users 
WHERE id > 20 
ORDER BY id 
LIMIT 10;
```

---

## 3. JOIN Operations

### 3.1 JOIN Types

```sql
-- INNER JOIN
SELECT * FROM orders o
INNER JOIN customers c ON o.customer_id = c.id;

-- LEFT JOIN
SELECT * FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id;

-- CROSS JOIN
SELECT * FROM colors, sizes;

-- Self JOIN
SELECT a.name as employee, b.name as manager
FROM employees a
LEFT JOIN employees b ON a.manager_id = b.id;
```

### 3.2 Multiple JOINs

```sql
SELECT 
    o.id,
    c.name as customer,
    p.name as product,
    oi.quantity
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'completed';
```

---

## 4. Subqueries

### 4.1 Scalar Subquery

```sql
-- Subquery in SELECT
SELECT 
    name,
    (SELECT COUNT(*) FROM orders WHERE customer_id = c.id) as order_count
FROM customers c;
```

### 4.2 Subquery in WHERE

```sql
-- IN subquery
SELECT * FROM products
WHERE category_id IN (
    SELECT id FROM categories WHERE active = 1
);

-- EXISTS
SELECT * FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);
```

### 4.3 Correlated Subqueries

```sql
-- Subquery referencing outer query
SELECT * FROM products p
WHERE price > (
    SELECT AVG(price) FROM products 
    WHERE category_id = p.category_id
);
```

---

## 5. Window Functions

### 5.1 Window Function Types (SQLite 3.25+)

```sql
-- Aggregate over window
SELECT 
    name,
    price,
    AVG(price) OVER () as avg_price
FROM products;

-- ROW_NUMBER
SELECT 
    name,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) as rank
FROM products;

-- RANK and DENSE_RANK
SELECT 
    name,
    price,
    RANK() OVER (ORDER BY price DESC) as rank,
    DENSE_RANK() OVER (ORDER BY price DESC) as dense_rank
FROM products;

-- LAG and LEAD
SELECT 
    name,
    price,
    LAG(price) OVER (ORDER BY price) as prev_price,
    LEAD(price) OVER (ORDER BY price) as next_price
FROM products;
```

### 5.2 PARTITION BY

```sql
-- Partition by category
SELECT 
    name,
    category,
    price,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) as rank
FROM products;
```

---

## 6. CTEs (Common Table Expressions)

### 6.1 Basic CTE

```sql
-- Simple CTE
WITH active_customers AS (
    SELECT * FROM customers WHERE status = 'active'
)
SELECT * FROM active_customers WHERE country = 'USA';
```

### 6.2 Multiple CTEs

```sql
-- Multiple CTEs
WITH 
    us_customers AS (
        SELECT * FROM customers WHERE country = 'USA'
    ),
    recent_orders AS (
        SELECT * FROM orders WHERE date > '2024-01-01'
    )
SELECT 
    c.name,
    COUNT(o.id) as order_count
FROM us_customers c
LEFT JOIN recent_orders o ON c.id = o.customer_id
GROUP BY c.id;
```

### 6.3 Recursive CTE

```sql
-- Hierarchical data
WITH RECURSIVE org_tree AS (
    -- Base case
    SELECT id, name, manager_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case
    SELECT e.id, e.name, e.manager_id, ot.level + 1
    FROM employees e
    JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT * FROM org_tree;
```

---

## 7. Aggregation

### 7.1 Aggregate Functions

```sql
-- Standard aggregates
SELECT 
    COUNT(*) as total,
    SUM(price) as total_price,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products;

-- GROUP_CONCAT
SELECT category, GROUP_CONCAT(name) as products
FROM products
GROUP BY category;
```

### 7.2 GROUP BY

```sql
-- Basic GROUP BY
SELECT 
    category,
    COUNT(*) as count,
    AVG(price) as avg_price
FROM products
GROUP BY category;

-- HAVING
SELECT 
    category,
    COUNT(*) as count
FROM products
GROUP BY category
HAVING COUNT(*) > 5;
```

---

## 8. JSON Support

### 8.1 JSON Functions (SQLite 3.38+)

```sql
-- Create JSON
SELECT JSON('{"a": 1, "b": 2}');

-- Extract values
SELECT JSON_EXTRACT('{"a":1,"b":2}', '$.a');  -- 1
SELECT JSON_EXTRACT('{"a":1,"b":2}', '$.b');  -- 2

-- Paths
SELECT JSON_EXTRACT('{"a":[1,2,3]}', '$.a[0]');  -- 1

-- Modify JSON
SELECT JSON_SET('{"a":1}', '$.b', 2);  -- {"a":1,"b":2}
SELECT JSON_INSERT('{"a":1}', '$.b', 2);  -- {"a":1,"b":2}
SELECT JSON_REMOVE('{"a":1,"b":2}', '$.b');  -- {"a":1}
```

### 8.2 JSON in Tables

```sql
-- JSON column
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    data TEXT  -- JSON stored as text
);

-- Query JSON
SELECT * FROM events 
WHERE JSON_EXTRACT(data, '$.type') = 'click';

-- Index JSON (virtual column)
CREATE TABLE events2 (
    id INTEGER PRIMARY KEY,
    data TEXT,
    event_type TEXT GENERATED ALWAYS AS (JSON_EXTRACT(data, '$.type'))
);

CREATE INDEX idx_events_type ON events2(event_type);
```

---

## 9. Full-Text Search

### 9.1 FTS5

```sql
-- Create FTS5 virtual table
CREATE VIRTUAL TABLE articles USING fts5(
    title,
    content,
    tokenize='porter'
);

-- Insert data
INSERT INTO articles (title, content) VALUES
    ('SQLite Tutorial', 'Learn SQLite database...'),
    ('FTS5 Search', 'Full-text search in SQLite...');

-- Search
SELECT * FROM articles 
WHERE articles MATCH 'SQLite';
```

### 9.2 FTS5 Options

```sql
-- Trigram tokenizer
CREATE VIRTUAL TABLE docs USING fts5(
    content,
    tokenize='trigram'
);

-- Highlight results
SELECT highlight(title, 0, '<b>', '</b>') as title,
       snippet(content, 0, '<b>', '</b>', '...', 20) as content
FROM articles 
WHERE articles MATCH 'database';
```

---

## 10. Advanced Patterns

### 10.1 Upsert (INSERT OR REPLACE)

```sql
-- SQLite 3.24+
INSERT INTO users (id, name, email)
VALUES (1, 'John', 'john@example.com')
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    email = excluded.email;
```

### 10.2 Returning Clause

```sql
-- Get inserted/updated values
INSERT INTO users (name, email)
VALUES ('Jane', 'jane@example.com')
RETURNING id, name;

DELETE FROM users 
WHERE status = 'inactive'
RETURNING *;
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*