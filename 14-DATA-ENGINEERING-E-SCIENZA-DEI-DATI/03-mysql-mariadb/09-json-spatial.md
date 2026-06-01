# MySQL/MariaDB JSON, Full-Text, Spatial

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: draft

## Skip list
- [ ] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. JSON Data Type
2. JSON Functions
3. Full-Text Search
4. Spatial Data
5. GIS Functions
6. JSON Performance
7. Full-Text Advanced

---

## 1. JSON Data Type

### 1.1 Creating JSON Columns

MySQL and MariaDB provide native JSON support:

```sql
-- JSON column
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert JSON
INSERT INTO events (data) VALUES 
('{"type": "click", "url": "/home", "user_id": 123}'),
('{"type": "view", "product_id": 456, "price": 99.99}'),
('{"type": "purchase", "items": [1, 2, 3], "total": 150.00}');

-- View JSON
SELECT * FROM events;
```

### 1.2 JSON Validation

```sql
-- JSON_VALID returns 1 for valid JSON
SELECT JSON_VALID('{"key": "value"}');  -- 1
SELECT JSON_VALID('invalid');  -- 0

-- Check in constraints
CREATE TABLE users (
    id INT PRIMARY KEY,
    preferences JSON NOT NULL,
    CONSTRAINT preferences_check CHECK (JSON_VALID(preferences))
);
```

---

## 2. JSON Functions

### 2.1 Value Extraction

```sql
-- Extract value with ->
SELECT data->>'$.type' AS event_type FROM events;
SELECT data->'$.product.price' AS price FROM events;

-- JSON path notation
-- $ = root
-- . = object member
-- [] = array element
-- ** = wildcard

-- Nested extraction
SELECT data->>'$.user.profile.name' AS name FROM events;
```

### 2.2 JSON Modification Functions

```sql
-- JSON_INSERT: insert without overwriting
UPDATE events 
SET data = JSON_INSERT(data, '$.timestamp', NOW())
WHERE id = 1;

-- JSON_SET: insert or update
UPDATE events 
SET data = JSON_SET(data, '$.type', 'purchase', '$.processed', true)
WHERE id = 1;

-- JSON_REPLACE: replace only existing keys
UPDATE events 
SET data = JSON_REPLACE(data, '$.type', 'click')
WHERE id = 1;

-- JSON_REMOVE: delete keys
UPDATE events 
SET data = JSON_REMOVE(data, '$.user_id')
WHERE id = 1;

-- JSON_ARRAY_APPEND: add to array
UPDATE events 
SET data = JSON_ARRAY_APPEND(data, '$.tags', 'new_tag')
WHERE id = 1;

-- JSON_ARRAY_INSERT: insert in array
UPDATE events 
SET data = JSON_ARRAY_INSERT(data, '$.tags[0]', 'first_tag')
WHERE id = 1;
```

### 2.3 JSON Search Functions

```sql
-- JSON_CONTAINS: check if value exists
SELECT * FROM events 
WHERE JSON_CONTAINS(data, '"click"', '$.type');

-- JSON_SEARCH: find string
SELECT * FROM events 
WHERE JSON_SEARCH(data, 'one', 'home') IS NOT NULL;

-- Search options:
-- 'one': first occurrence
-- 'all': all occurrences

-- JSON_KEYS: get top-level keys
SELECT JSON_KEYS(data) FROM events;

-- JSON_LENGTH: count elements
SELECT JSON_LENGTH(data), JSON_LENGTH(data, '$.items') FROM events;
```

---

## 3. Full-Text Search

### 3.1 Creating Full-Text Index

```sql
-- MySQL/MariaDB InnoDB
CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    content TEXT,
    FULLTEXT (title, content)
) ENGINE=InnoDB;

-- Add index to existing table
ALTER TABLE articles ADD FULLTEXT(title, content);

-- Single column index
CREATE FULLTEXT INDEX idx_title ON articles(title);
```

### 3.2 Search Modes

```sql
-- Natural Language Mode (default)
SELECT * FROM articles 
WHERE MATCH(title, content) AGAINST('database' IN NATURAL LANGUAGE MODE);

-- Boolean Mode
SELECT * FROM articles 
WHERE MATCH(title, content) AGAINST('+mysql -postgresql' IN BOOLEAN MODE);

-- Query Expansion
SELECT * FROM articles 
WHERE MATCH(title, content) AGAINST('data' WITH QUERY EXPANSION);
```

**Boolean operators**:
- `+`: must contain
- `-`: must not contain
- `*`: wildcard
- `"`: phrase

---

## 4. Spatial Data

### 4.1 Creating Spatial Columns

```sql
-- Point
CREATE TABLE locations (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    position POINT NOT NULL SRID 0,
    SPATIAL INDEX(position)
);

-- Insert point
INSERT INTO locations (name, position) VALUES 
('Office', ST_GeomFromText('POINT(10 20)', 0)),
('Warehouse', ST_GeomFromText('POINT(30 40)', 0));

-- With SRID (4326 = WGS84)
INSERT INTO locations (name, position) VALUES
('GPS Point', ST_GeomFromText('POINT(40.7128 -74.0060)', 4326));
```

### 4.2 Geometry Types

```sql
-- LineString
CREATE TABLE routes (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    path LINESTRING NOT NULL SRID 0,
    SPATIAL INDEX(path)
);

INSERT INTO routes (name, path) VALUES
('Route A', ST_GeomFromText('LINESTRING(0 0, 10 10, 20 15)', 0));

-- Polygon
CREATE TABLE areas (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    boundary POLYGON NOT NULL SRID 0,
    SPATIAL INDEX(boundary)
);

INSERT INTO areas (name, boundary) VALUES
('Zone 1', ST_GeomFromText('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))', 0));

-- MultiPoint, MultiLineString, MultiPolygon
CREATE TABLE complexes (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    shape MULTIPOLYGON
);
```

---

## 5. GIS Functions

### 5.1 Distance Calculations

```sql
-- Cartesian distance
SELECT ST_Distance(
    ST_GeomFromText('POINT(10 20)', 0),
    ST_GeomFromText('POINT(30 40)', 0)
) AS distance;

-- Geography distance (meters)
SELECT ST_Distance(
    ST_GeomFromText('POINT(-74.0060 40.7128)', 4326)::GEOGRAPHY,
    ST_GeomFromText('POINT(-73.9352 40.7306)', 4326)::GEOGRAPHY
) AS distance_meters;

-- Haversine approximation
SELECT ST_Distance_Sphere(
    ST_GeomFromText('POINT(-74.0060 40.7128)', 4326),
    ST_GeomFromText('POINT(-73.9352 40.7306)', 4326)
) AS distance_meters;
```

### 5.2 Spatial Relationships

```sql
-- Contains
SELECT * FROM areas 
WHERE ST_Contains(
    boundary, 
    ST_GeomFromText('POINT(5 5)', 0)
);

-- Within
SELECT * FROM locations 
WHERE ST_Within(
    position,
    ST_GeomFromText('POLYGON((0 0, 20 0, 20 20, 0 20, 0 0))', 0)
);

-- Intersects
SELECT * FROM routes r1, routes r2
WHERE ST_Intersects(r1.path, r2.path);

-- Distance within
SELECT * FROM locations 
WHERE ST_DWithin(
    position,
    ST_GeomFromText('POINT(10 20)', 0),
    5  -- distance units
);
```

---

## 6. JSON Performance

### 6.1 JSON Indexing

MySQL 8.0+ supports generated columns:

```sql
-- Create virtual column for indexing
ALTER TABLE events 
ADD COLUMN event_type VARCHAR(50) 
GENERATED ALWAYS AS (JSON_UNQUOTE(data->>'$.type')) STORED;

CREATE INDEX idx_event_type ON events(event_type);

-- Query using index
SELECT * FROM events WHERE event_type = 'click';
```

### 6.2 JSON Optimization Tips

```sql
-- Avoid deep nesting in queries
-- Prefer flat JSON structures

-- Use virtual columns for frequently queried paths

-- Limit JSON size (keep under 1MB per row)

-- Consider normalization for complex data
```

---

## 7. Full-Text Advanced

### 7.1 Stopwords

```sql
-- View default stopwords
SELECT * FROM information_schema.INNODB_FT_DEFAULT_STOPWORD;

-- Custom stopwords
CREATE TABLE my_stopwords (
    value VARCHAR(30)
) ENGINE=InnoDB;

SET GLOBAL innodb_ft_server_stopword_table = 'mydb/my_stopwords';
```

### 7.2 Configuration

```sql
-- Minimum word length
SET GLOBAL innodb_ft_min_token_size = 3;
SET GLOBAL ft_min_word_len = 3;

-- Maximum word length
SET GLOBAL innodb_ft_max_token_size = 84;

-- Rebuild index after changes
OPTIMIZE TABLE articles;
```

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*