# Cassandra: Use Cases

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [x] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Time Series
2. IoT and Sensor Data
3. Messaging and Chat
4. Recommendation Engines
5. User Activity Tracking and Audit Logs
6. E-Commerce Product Catalog and Inventory
7. Geospatial and Location Data
8. Content Management and Personalization
9. Financial Services and Fraud Detection
10. Gaming Leaderboards and Player State
11. Data Modeling Best Practices
12. Anti-Patterns and When NOT to Use Cassandra
13. Operational Considerations per Use Case
14. Cassandra 4.x/5.x Features by Use Case
15. Troubleshooting
16. FAQ

---

## 1. Time Series

Time-series data is one of Cassandra's strongest use cases due to its write-optimized storage engine (LSM trees), natural time-based clustering, and TimeWindowCompactionStrategy (TWCS).

### 1.1 Data Model

```sql
-- Metrics storage with time bucketing
-- Partition key: (metric_name, bucket) prevents unbounded partition growth
-- Clustering key: timestamp for time-ordered retrieval
CREATE TABLE metrics (
    metric_name text,
    bucket text,            -- e.g., '2026-05-22' (daily bucket)
    ts timestamp,
    value double,
    tags map<text, text>,
    PRIMARY KEY ((metric_name, bucket), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND COMPACTION = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
  }
  AND default_time_to_live = 7776000;  -- 90-day TTL (auto-expiry)

-- Query: last hour of CPU metrics
SELECT ts, value FROM metrics
WHERE metric_name = 'cpu_usage'
  AND bucket = '2026-05-22'
  AND ts >= '2026-05-22T10:00:00Z'
  AND ts <= '2026-05-22T11:00:00Z';
```

### 1.2 Bucketing Strategy

```sql
-- Hourly buckets for high-frequency data (>1000 writes/sec per metric)
-- Partition key includes hour to cap partition size
CREATE TABLE metrics_hf (
    metric_name text,
    bucket_hour text,       -- e.g., '2026-05-22-14'
    ts timestamp,
    value double,
    PRIMARY KEY ((metric_name, bucket_hour), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

-- Daily buckets for low-frequency data (<100 writes/sec per metric)
-- Simpler partition key, larger but manageable partitions
CREATE TABLE metrics_lf (
    metric_name text,
    bucket_day text,        -- e.g., '2026-05-22'
    ts timestamp,
    value double,
    PRIMARY KEY ((metric_name, bucket_day), ts)
) WITH CLUSTERING ORDER BY (ts DESC);
```

### 1.3 Why TWCS for Time Series

```sql
-- TimeWindowCompactionStrategy groups SSTables by time window.
-- When all data in a window expires (via TTL), the entire SSTable is dropped
-- WITHOUT compaction I/O -- just a file delete.

-- Configuration:
-- compaction_window_unit: MINUTES, HOURS, DAYS
-- compaction_window_size: integer
-- Rule of thumb: window = TTL / 20 to TTL / 30

ALTER TABLE metrics WITH COMPACTION = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'HOURS',
    'compaction_window_size': 1
};

-- WARNING: TWCS assumes writes go to the CURRENT time window.
-- Out-of-order writes (late-arriving data) create SSTables in older windows
-- and can prevent efficient compaction.
```

### 1.4 Aggregation Patterns

```sql
-- Pre-aggregated rollups: store hourly/daily summaries
CREATE TABLE metrics_hourly (
    metric_name text,
    bucket_day text,
    hour int,
    min_value double,
    max_value double,
    avg_value double,
    count counter,
    PRIMARY KEY ((metric_name, bucket_day), hour)
);

-- Application-side aggregation writes raw + rollup in a batch:
BEGIN BATCH
  INSERT INTO metrics (metric_name, bucket, ts, value)
  VALUES ('cpu', '2026-05-22', '2026-05-22T14:30:00Z', 72.5);
  UPDATE metrics_hourly SET count = count + 1
  WHERE metric_name = 'cpu' AND bucket_day = '2026-05-22' AND hour = 14;
APPLY BATCH;
```

### 1.5 nodetool Commands for Time Series

```bash
# Check partition sizes (large partitions indicate bad bucketing)
nodetool tablestats mykeyspace.metrics | grep -E "Compacted|partition"

# Monitor TWCS compaction progress
nodetool compactionstats

# Check tombstone ratio (high ratio = inefficient deletes)
nodetool tablestats mykeyspace.metrics | grep "tombstones"

# Force compaction of expired SSTables
nodetool compact mykeyspace metrics
```

---

## 2. IoT and Sensor Data

IoT workloads are characterized by massive write throughput, append-only semantics, and high cardinality of device IDs.

### 2.1 Data Model

```sql
-- Sensor readings with composite partition key
-- (sensor_id, day) caps partition at ~86400 rows for 1-second resolution
CREATE TABLE sensor_readings (
    sensor_id text,
    day text,               -- '2026-05-22'
    ts timestamp,
    temperature double,
    humidity double,
    pressure double,
    battery_pct int,
    metadata map<text, text>,
    PRIMARY KEY ((sensor_id, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND COMPACTION = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
  }
  AND default_time_to_live = 2592000;  -- 30 days

-- Latest state per sensor (materialized view or separate table)
CREATE TABLE sensor_latest (
    sensor_id text PRIMARY KEY,
    last_reading timestamp,
    temperature double,
    humidity double,
    status text
);
```

### 2.2 High-Throughput Write Optimization

```yaml
# cassandra.yaml for IoT write-heavy workloads
# Increase memtable space (delays flushes, batches more writes)
memtable_heap_space_in_mb: 4096
memtable_offheap_space_in_mb: 2048

# Increase commitlog throughput
commitlog_sync: periodic
commitlog_sync_period_in_ms: 10000
commitlog_total_space_in_mb: 2048

# Increase concurrent writes
concurrent_writes: 64

# Disable row cache (write-heavy, rarely re-read)
# row_cache_size_in_mb: 0
```

### 2.3 Device Registry

```sql
-- Device metadata table
CREATE TABLE devices (
    device_id text PRIMARY KEY,
    device_type text,
    firmware_version text,
    location text,
    registered_at timestamp,
    tags set<text>,
    config map<text, text>
);

-- Lookup by type (SAI index, Cassandra 5.0+)
CREATE INDEX ON devices (device_type) USING 'sai';

-- Query devices by type
SELECT * FROM devices WHERE device_type = 'temperature_sensor';
```

### 2.4 Alerting and Threshold Table

```sql
-- Store threshold violations as they happen
CREATE TABLE sensor_alerts (
    sensor_id text,
    alert_date text,
    alert_time timestamp,
    alert_type text,         -- 'HIGH_TEMP', 'LOW_BATTERY', etc.
    value double,
    threshold double,
    acknowledged boolean,
    PRIMARY KEY ((sensor_id, alert_date), alert_time)
) WITH CLUSTERING ORDER BY (alert_time DESC)
  AND default_time_to_live = 7776000;  -- 90 days
```

---

## 3. Messaging and Chat

Cassandra excels at messaging due to its fast writes, natural time-ordering via clustering columns, and partition-per-conversation model.

### 3.1 Data Model

```sql
-- Messages per conversation thread
CREATE TABLE messages (
    conversation_id text,
    message_id timeuuid,
    sender_id text,
    body text,
    media_url text,
    message_type text,       -- 'text', 'image', 'file'
    edited boolean,
    deleted boolean,
    PRIMARY KEY (conversation_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);

-- User's conversation inbox (most recent conversations first)
CREATE TABLE user_inbox (
    user_id text,
    last_activity timestamp,
    conversation_id text,
    last_message_preview text,
    unread_count int,
    PRIMARY KEY (user_id, last_activity, conversation_id)
) WITH CLUSTERING ORDER BY (last_activity DESC);

-- Read receipts
CREATE TABLE read_receipts (
    conversation_id text,
    user_id text,
    last_read_message_id timeuuid,
    read_at timestamp,
    PRIMARY KEY (conversation_id, user_id)
);
```

### 3.2 Pagination

```sql
-- Page 1: most recent 50 messages
SELECT * FROM messages
WHERE conversation_id = 'conv_12345'
LIMIT 50;

-- Page 2: messages older than the last one from page 1
SELECT * FROM messages
WHERE conversation_id = 'conv_12345'
  AND message_id < minTimeuuid('2026-05-22T10:00:00Z')
LIMIT 50;

-- Efficient: uses clustering order, no full-table scan.
```

### 3.3 Message Search (Cassandra 5.0 + SAI)

```sql
-- Storage Attached Index for message search
CREATE INDEX ON messages (body) USING 'sai'
WITH OPTIONS = {'mode': 'CONTAINS'};

-- Search within a conversation
SELECT * FROM messages
WHERE conversation_id = 'conv_12345'
  AND body LIKE '%meeting%';

-- NOTE: SAI text search is basic substring matching.
-- For full-text search, use Elasticsearch or Solr alongside Cassandra.
```

---

## 4. Recommendation Engines

### 4.1 User-Item Interaction Model

```sql
-- User-item interactions with score ranking
CREATE TABLE user_items (
    user_id text,
    score double,
    item_id text,
    interaction_type text,   -- 'view', 'purchase', 'rate'
    timestamp timeuuid,
    PRIMARY KEY (user_id, score, item_id)
) WITH CLUSTERING ORDER BY (score DESC, item_id ASC);

-- Top-N recommendations for a user
SELECT item_id, score FROM user_items
WHERE user_id = 'user_42'
LIMIT 20;
```

### 4.2 Collaborative Filtering Support Tables

```sql
-- Item-to-item similarity matrix
CREATE TABLE item_similarity (
    item_id text,
    similar_item_id text,
    similarity_score double,
    PRIMARY KEY (item_id, similarity_score, similar_item_id)
) WITH CLUSTERING ORDER BY (similarity_score DESC, similar_item_id ASC);

-- User feature vectors (for ML model input)
CREATE TABLE user_features (
    user_id text PRIMARY KEY,
    feature_vector list<double>,
    last_computed timestamp,
    model_version text
);
```

### 4.3 Real-Time Event Stream

```sql
-- Capture user events for recommendation pipeline
CREATE TABLE user_events (
    user_id text,
    event_day text,
    event_time timeuuid,
    event_type text,
    item_id text,
    event_data map<text, text>,
    PRIMARY KEY ((user_id, event_day), event_time)
) WITH CLUSTERING ORDER BY (event_time DESC)
  AND default_time_to_live = 604800;  -- 7 days for recent activity
```

---

## 5. User Activity Tracking and Audit Logs

### 5.1 Activity Timeline

```sql
-- User activity feed
CREATE TABLE user_activity (
    user_id text,
    activity_month text,     -- '2026-05'
    activity_time timeuuid,
    activity_type text,
    description text,
    ip_address text,
    user_agent text,
    metadata map<text, text>,
    PRIMARY KEY ((user_id, activity_month), activity_time)
) WITH CLUSTERING ORDER BY (activity_time DESC)
  AND COMPACTION = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
  }
  AND default_time_to_live = 31536000;  -- 1 year
```

### 5.2 Compliance Audit Log

```sql
-- Immutable audit log (append-only, no updates/deletes)
CREATE TABLE audit_log (
    partition_key text,       -- e.g., 'audit_2026-05-22'
    event_id timeuuid,
    actor text,
    action text,
    resource_type text,
    resource_id text,
    old_value text,
    new_value text,
    source_ip text,
    PRIMARY KEY (partition_key, event_id)
) WITH CLUSTERING ORDER BY (event_id ASC)
  AND COMPACTION = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
  }
  AND gc_grace_seconds = 0;   -- no tombstones needed for append-only
```

### 5.3 Cassandra 4.0 Native Audit Logging

```yaml
# cassandra.yaml (Cassandra 4.0+)
# Built-in audit logging without external tools
audit_logging_options:
  enabled: true
  logger:
    - class_name: BinAuditLogger
  included_keyspaces: ecommerce,user_data
  excluded_keyspaces: system,system_schema
  included_categories: QUERY,DML,DDL,AUTH
  # Categories: QUERY, DML, DDL, DCL, AUTH, PREPARE, ERROR
```

---

## 6. E-Commerce Product Catalog and Inventory

### 6.1 Product Catalog

```sql
-- Products with denormalized category info
CREATE TABLE products (
    product_id uuid PRIMARY KEY,
    name text,
    description text,
    category text,
    subcategory text,
    price decimal,
    currency text,
    images list<text>,
    attributes map<text, text>,
    tags set<text>,
    created_at timestamp,
    updated_at timestamp,
    active boolean
);

-- Products by category (query-driven table)
CREATE TABLE products_by_category (
    category text,
    subcategory text,
    product_id uuid,
    name text,
    price decimal,
    PRIMARY KEY ((category), subcategory, product_id)
);

-- Price range queries (Cassandra 5.0 SAI)
CREATE INDEX ON products (price) USING 'sai';
SELECT * FROM products WHERE price >= 10.00 AND price <= 50.00;
```

### 6.2 Inventory Tracking

```sql
-- Inventory with lightweight transactions for stock control
CREATE TABLE inventory (
    product_id uuid,
    warehouse_id text,
    quantity int,
    reserved int,
    last_updated timestamp,
    PRIMARY KEY (product_id, warehouse_id)
);

-- Atomic stock decrement with LWT
UPDATE inventory
SET quantity = quantity - 1, last_updated = toTimestamp(now())
WHERE product_id = ? AND warehouse_id = 'wh-east'
IF quantity > 0;
-- Returns [applied]=true if successful, false if stock was 0.
```

### 6.3 Shopping Cart

```sql
-- Per-user shopping cart
CREATE TABLE shopping_cart (
    user_id text,
    product_id uuid,
    quantity int,
    added_at timestamp,
    price_at_add decimal,
    PRIMARY KEY (user_id, product_id)
);

-- Cart operations
-- Add item:
INSERT INTO shopping_cart (user_id, product_id, quantity, added_at, price_at_add)
VALUES ('user_42', 550e8400-e29b-41d4-a716-446655440000, 2, toTimestamp(now()), 29.99);

-- Remove item:
DELETE FROM shopping_cart WHERE user_id = 'user_42' AND product_id = ?;

-- Get full cart:
SELECT * FROM shopping_cart WHERE user_id = 'user_42';
```

---

## 7. Geospatial and Location Data

### 7.1 Geohash-Based Location Model

```sql
-- Store locations using geohash prefix as partition key
-- Geohash precision 5 = ~5km grid cell
CREATE TABLE locations (
    geohash_prefix text,     -- first 5 chars of geohash
    geohash_full text,       -- full precision geohash
    entity_id text,
    entity_type text,
    latitude double,
    longitude double,
    name text,
    metadata map<text, text>,
    PRIMARY KEY (geohash_prefix, geohash_full, entity_id)
);

-- Find all entities near a point:
-- 1. Compute geohash of target point (e.g., 'u33dc')
-- 2. Query the 9 neighboring geohash cells (center + 8 neighbors)
SELECT * FROM locations WHERE geohash_prefix = 'u33dc';
SELECT * FROM locations WHERE geohash_prefix = 'u33dd';
-- ... (repeat for all 9 cells)
```

### 7.2 Real-Time Location Tracking

```sql
-- Fleet / ride-share vehicle tracking
CREATE TABLE vehicle_positions (
    vehicle_id text,
    position_date text,
    ts timestamp,
    latitude double,
    longitude double,
    speed double,
    heading int,
    PRIMARY KEY ((vehicle_id, position_date), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND default_time_to_live = 86400;  -- 24 hours of history

-- Latest position per vehicle
CREATE TABLE vehicle_latest_position (
    vehicle_id text PRIMARY KEY,
    latitude double,
    longitude double,
    speed double,
    last_update timestamp
);
```

---

## 8. Content Management and Personalization

### 8.1 Content Storage

```sql
-- CMS content entries
CREATE TABLE content (
    content_id uuid PRIMARY KEY,
    title text,
    body text,
    author text,
    content_type text,       -- 'article', 'video', 'podcast'
    status text,             -- 'draft', 'published', 'archived'
    tags set<text>,
    published_at timestamp,
    metadata map<text, text>
);

-- Content by tag (for tag-based browsing)
CREATE TABLE content_by_tag (
    tag text,
    published_at timestamp,
    content_id uuid,
    title text,
    PRIMARY KEY (tag, published_at, content_id)
) WITH CLUSTERING ORDER BY (published_at DESC);
```

### 8.2 User Personalization

```sql
-- Per-user preferences and feature flags
CREATE TABLE user_preferences (
    user_id text PRIMARY KEY,
    theme text,
    language text,
    notification_settings map<text, boolean>,
    feature_flags set<text>,
    last_updated timestamp
);

-- Personalized content feed
CREATE TABLE user_feed (
    user_id text,
    feed_date text,
    published_at timestamp,
    content_id uuid,
    title text,
    relevance_score double,
    PRIMARY KEY ((user_id, feed_date), relevance_score, content_id)
) WITH CLUSTERING ORDER BY (relevance_score DESC, content_id ASC)
  AND default_time_to_live = 604800;  -- 7-day feed
```

---

## 9. Financial Services and Fraud Detection

### 9.1 Transaction Ledger

```sql
-- Financial transaction log (append-only, high compliance requirements)
CREATE TABLE transactions (
    account_id text,
    tx_month text,
    tx_time timeuuid,
    tx_type text,            -- 'debit', 'credit', 'transfer'
    amount decimal,
    currency text,
    counterparty text,
    reference text,
    status text,
    PRIMARY KEY ((account_id, tx_month), tx_time)
) WITH CLUSTERING ORDER BY (tx_time DESC)
  AND COMPACTION = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
  };

-- Account balance (use LWT for atomic updates)
CREATE TABLE account_balances (
    account_id text PRIMARY KEY,
    balance decimal,
    currency text,
    last_tx_time timeuuid
);

-- Atomic balance update
UPDATE account_balances
SET balance = ?, last_tx_time = ?
WHERE account_id = ?
IF balance = ?;   -- Optimistic concurrency via LWT
```

### 9.2 Fraud Detection Event Stream

```sql
-- Real-time fraud scoring events
CREATE TABLE fraud_events (
    event_partition text,    -- 'fraud_2026-05-22-14' (hourly)
    event_id timeuuid,
    account_id text,
    event_type text,
    risk_score double,
    features map<text, double>,
    decision text,           -- 'ALLOW', 'BLOCK', 'REVIEW'
    model_version text,
    PRIMARY KEY (event_partition, event_id)
) WITH CLUSTERING ORDER BY (event_id DESC)
  AND default_time_to_live = 7776000;  -- 90 days
```

---

## 10. Gaming Leaderboards and Player State

### 10.1 Leaderboard

```sql
-- Global leaderboard (top scores)
CREATE TABLE leaderboard (
    game_id text,
    score_bucket int,        -- e.g., 0-999, 1000-1999 (prevents hot partition)
    score bigint,
    player_id text,
    player_name text,
    achieved_at timestamp,
    PRIMARY KEY ((game_id, score_bucket), score, player_id)
) WITH CLUSTERING ORDER BY (score DESC, player_id ASC);

-- Top 100 players (query top bucket first, then next)
SELECT player_name, score FROM leaderboard
WHERE game_id = 'battle_royale' AND score_bucket = 9000
LIMIT 100;
```

### 10.2 Player State

```sql
-- Player game state (save/load pattern)
CREATE TABLE player_state (
    player_id text,
    game_id text,
    save_slot int,
    state_data blob,         -- serialized game state
    saved_at timestamp,
    checksum text,
    PRIMARY KEY ((player_id, game_id), save_slot)
);

-- Player inventory
CREATE TABLE player_inventory (
    player_id text,
    item_id text,
    item_type text,
    quantity int,
    acquired_at timestamp,
    metadata map<text, text>,
    PRIMARY KEY (player_id, item_type, item_id)
);
```

---

## 11. Data Modeling Best Practices

### 11.1 Partition Key Design

```sql
-- GOOD: bounded partition (time-bucketed)
PRIMARY KEY ((sensor_id, day), ts)
-- Each partition has at most 86400 rows (1/sec), ~10-50 MB

-- BAD: unbounded partition
PRIMARY KEY (sensor_id, ts)
-- Partition grows forever; eventually hits multi-GB and causes OOM

-- Target partition size: 10-100 MB, max 100K-200K rows
-- Check with: nodetool tablestats keyspace.table
```

### 11.2 Denormalization Rules

```
Rule 1: Model tables around queries, not entities.
Rule 2: Duplicate data across tables to avoid JOINs (JOINs do not exist in CQL).
Rule 3: Accept write amplification (write to N tables) for read efficiency.
Rule 4: Use batch statements (LOGGED or UNLOGGED) to keep denormalized tables consistent.
Rule 5: Prefer static columns over separate lookup tables when data changes rarely.
```

### 11.3 TTL Strategy

```sql
-- Set TTL at INSERT time
INSERT INTO metrics (metric_name, bucket, ts, value)
VALUES ('cpu', '2026-05-22', toTimestamp(now()), 85.2)
USING TTL 2592000;   -- 30 days

-- Set default TTL on table
ALTER TABLE metrics WITH default_time_to_live = 2592000;

-- Update TTL on existing row (resets the clock)
UPDATE metrics USING TTL 2592000
SET value = 85.2
WHERE metric_name = 'cpu' AND bucket = '2026-05-22' AND ts = ?;

-- WARNING: TTL=0 means "no expiry," not "expire immediately."
-- To expire immediately, DELETE the row.
```

### 11.4 Counter Tables

```sql
-- Counters for real-time analytics
CREATE TABLE page_view_counts (
    page_url text,
    count_date text,
    view_count counter,
    unique_visitor_count counter,
    PRIMARY KEY (page_url, count_date)
);

-- Increment counters
UPDATE page_view_counts
SET view_count = view_count + 1
WHERE page_url = '/products' AND count_date = '2026-05-22';

-- Counter limitations:
-- 1. Cannot INSERT; only UPDATE with increment/decrement.
-- 2. Counter columns cannot be mixed with non-counter columns
--    (except the primary key).
-- 3. No TTL on counter tables.
-- 4. Counter values may diverge temporarily across replicas.
```

---

## 12. Anti-Patterns and When NOT to Use Cassandra

### 12.1 When NOT to Use Cassandra

| Scenario | Why Not Cassandra | Better Alternative |
|----------|-------------------|--------------------|
| Complex JOINs across entities | No JOIN support; denormalization required | PostgreSQL, MySQL |
| Ad-hoc analytics / aggregations | No GROUP BY across partitions; full scans are expensive | ClickHouse, BigQuery, Spark |
| Small datasets (< 10 GB) | Operational overhead not justified | PostgreSQL, SQLite |
| Strong ACID transactions | LWT is limited and slow; no multi-row transactions | PostgreSQL, CockroachDB |
| Graph traversal | No graph model | Neo4j, Amazon Neptune |
| Full-text search | No built-in FTS engine | Elasticsearch, Solr |
| Frequently updated single rows | Each update is a write (new cell version); high tombstone churn | Redis, PostgreSQL |

### 12.2 Common Anti-Patterns

```sql
-- ANTI-PATTERN 1: Using ALLOW FILTERING
SELECT * FROM users WHERE age > 25 ALLOW FILTERING;
-- This scans every partition on every node. Never use in production.

-- ANTI-PATTERN 2: Using secondary indexes on high-cardinality columns
CREATE INDEX ON users (user_id);
-- Secondary indexes perform poorly on high-cardinality columns.
-- Use SAI (Cassandra 5.0+) or create a dedicated query table.

-- ANTI-PATTERN 3: Large partitions
-- Storing years of data per user without time bucketing
PRIMARY KEY (user_id, event_time)   -- grows unbounded

-- ANTI-PATTERN 4: Queue-like patterns (DELETE after read)
-- Produces massive tombstone buildup, degrading read performance.
-- Use Kafka or RabbitMQ for queues.

-- ANTI-PATTERN 5: Using Cassandra as a cache
-- Cassandra writes to commitlog + memtable; slower than Redis.
-- Use Redis for caching, Cassandra for persistence.

-- ANTI-PATTERN 6: Batch statements as performance optimization
-- LOGGED BATCH adds coordination overhead. Use batches ONLY for
-- atomicity across denormalized tables, not for bulk loading.
-- For bulk loading, use concurrent async writes or sstableloader.
```

---

## 13. Operational Considerations per Use Case

### 13.1 Compaction Strategy Selection

| Use Case | Recommended Strategy | Why |
|----------|---------------------|-----|
| Time series / IoT | `TimeWindowCompactionStrategy` | Efficient TTL expiry; drop whole SSTables |
| Read-heavy / general | `LeveledCompactionStrategy` | Consistent read latency; fewer SSTables to check |
| Write-heavy / batch | `SizeTieredCompactionStrategy` | Lowest write amplification |
| Mixed (Cassandra 5.0) | `UnifiedCompactionStrategy` | Auto-adapts to workload |

### 13.2 Consistency Level Selection by Use Case

| Use Case | Write CL | Read CL | Notes |
|----------|----------|---------|-------|
| Metrics / logging | `ONE` | `ONE` | Losing a few data points is acceptable |
| Messaging | `LOCAL_QUORUM` | `LOCAL_QUORUM` | Users expect consistent message delivery |
| Financial | `LOCAL_QUORUM` | `LOCAL_QUORUM` | Strong consistency within DC |
| Inventory (stock) | `LOCAL_SERIAL` (LWT) | `LOCAL_QUORUM` | Prevent overselling |
| Analytics feed | `ONE` | `ONE` | Staleness acceptable for feed data |

### 13.3 Monitoring per Use Case

```bash
# Time series: watch compaction queue (TWCS should be lightweight)
nodetool compactionstats

# Messaging: watch partition sizes (large conversations)
nodetool tablestats ecommerce.messages | grep "Compacted partition"

# IoT: watch write latency (high throughput must stay <10ms p99)
nodetool proxyhistograms

# Financial: watch LWT contention
nodetool tpstats | grep -i "cas"
```

---

## 14. Cassandra 4.x/5.x Features by Use Case

### 14.1 Cassandra 4.0 Features

```yaml
# Virtual tables: monitor system state via CQL (no JMX needed)
# Useful for all use cases.
# SELECT * FROM system_views.sstable_tasks;
# SELECT * FROM system_views.clients;

# Audit logging: built-in audit trail
# Essential for financial, compliance, and healthcare use cases.
audit_logging_options:
  enabled: true
  logger:
    - class_name: BinAuditLogger
  included_categories: QUERY,DML,DDL,AUTH

# Zero-Copy Streaming: 5x faster streaming
# Benefits IoT and time-series during node bootstraps.

# Transient replication (experimental):
# Reduces storage for read-heavy analytics replicas.
```

### 14.2 Cassandra 5.0 Features

```sql
-- Storage Attached Indexes (SAI): efficient secondary indexes
-- Replaces legacy secondary indexes for all use cases
CREATE INDEX ON products (category) USING 'sai';
CREATE INDEX ON products (price) USING 'sai';

-- Multi-column SAI queries (no ALLOW FILTERING needed)
SELECT * FROM products
WHERE category = 'electronics' AND price < 100.00;

-- Unified Compaction Strategy (UCS): auto-tuning compaction
CREATE TABLE events (
    id uuid PRIMARY KEY,
    data text
) WITH compaction = {'class': 'UnifiedCompactionStrategy'};

-- Accord protocol: replaces Paxos for LWT
-- Lower latency for financial transaction use cases
-- Automatic; no query syntax change. IF-based queries use Accord.

-- Vector search (5.0 preview): store and query embeddings
-- For recommendation engines and ML use cases
CREATE TABLE item_embeddings (
    item_id text PRIMARY KEY,
    embedding vector<float, 768>
);
CREATE INDEX ON item_embeddings (embedding) USING 'sai';
-- SELECT * FROM item_embeddings ORDER BY embedding ANN OF [0.1, 0.2, ...] LIMIT 10;
```

### 14.3 Guardrails (4.1+)

```yaml
# cassandra.yaml
# Cluster-wide guardrails prevent operational mistakes
guardrails:
  partition_size_warn_threshold: 100MiB
  partition_size_fail_threshold: 500MiB
  columns_per_table_warn_threshold: 200
  columns_per_table_fail_threshold: 500
  page_size_warn_threshold: 5000
  page_size_fail_threshold: 10000
  in_select_cartesian_product_warn_threshold: 25
  in_select_cartesian_product_fail_threshold: 100
  tables_warn_threshold: 150
  tables_fail_threshold: 250
```

---

## 15. Troubleshooting

### 15.1 Hot Partition

**Symptom**: one node under much higher load than others; latency spikes on reads/writes.

**Cause**: a single partition key receives disproportionate traffic (e.g., a popular user, a "global" counter).

**Fix**:
```sql
-- Add a bucketing component to the partition key
-- Before (hot):
PRIMARY KEY (popular_user_id, ts)

-- After (distributed):
PRIMARY KEY ((popular_user_id, bucket), ts)
-- Application hashes or round-robins across N buckets
```

### 15.2 Large Partitions Causing OOM

**Symptom**: `java.lang.OutOfMemoryError` during reads or compaction.

**Cause**: partition exceeds hundreds of MB because time bucketing was not applied.

**Fix**:
```bash
# Identify large partitions
nodetool tablestats keyspace.table | grep "Compacted partition maximum"

# Redesign the table with time-bucketed partition keys
# Migrate data using COPY or sstableloader
```

### 15.3 Tombstone Overwhelm

**Symptom**: reads become increasingly slow; GC pressure rises.

**Cause**: queue-like patterns (INSERT then DELETE) create massive tombstone buildup.

**Fix**:
```bash
# Check tombstone count
nodetool tablestats keyspace.table | grep "tombstones"

# Reduce gc_grace_seconds if repair runs more frequently
ALTER TABLE keyspace.table WITH gc_grace_seconds = 259200;  -- 3 days

# Run compaction to purge tombstones
nodetool compact keyspace table
```

### 15.4 ALLOW FILTERING Causing Full Scan

**Symptom**: query takes minutes and times out.

**Fix**: never use `ALLOW FILTERING` in production. Create a dedicated query table or use SAI indexes (5.0+).

### 15.5 Counter Inconsistency

**Symptom**: counter values differ across replicas.

**Fix**:
```bash
# Run repair to reconcile counters
nodetool repair -full keyspace counter_table

# Counters are eventually consistent. Repair resolves divergence.
```

### 15.6 LWT Contention (Timeout)

**Symptom**: `CasWriteTimeoutException` on IF-based queries.

**Cause**: too many concurrent LWT operations on the same partition.

**Fix**:
```sql
-- Reduce contention by using a finer partition key
-- Shard the contended resource across multiple partitions

-- Increase CAS timeout (cassandra.yaml)
-- cas_contention_timeout: 5000  (ms)
```

### 15.7 Write Latency Spikes During Compaction

**Symptom**: p99 write latency increases periodically.

**Fix**:
```yaml
# cassandra.yaml
# Throttle compaction throughput
compaction_throughput_mb_per_sec: 64   # default 64, reduce to 32 if I/O constrained

# Use separate disks for commitlog and data
commitlog_directory: /ssd1/commitlog
data_file_directories:
  - /ssd2/data
```

### 15.8 TTL Not Expiring Data

**Symptom**: data with TTL persists beyond expected expiry.

**Cause**: TTL expiry happens during compaction, not in real-time. Until compaction runs, expired data may still appear in reads (Cassandra filters it at read time) but occupies disk space.

**Fix**:
```bash
# Force compaction to reclaim disk space
nodetool compact keyspace table

# Verify TWCS is configured correctly for time-series tables
nodetool tablestats keyspace.table
```

### 15.9 Schema Disagreement After Table Creation

**Symptom**: `SchemaDisagreementException` when creating tables in rapid succession.

**Fix**:
```bash
# Wait for schema agreement between DDL statements
nodetool describecluster | grep "Schema versions"

# In application code, add a delay between DDL operations
# or poll for schema agreement before proceeding.
```

### 15.10 Batch Too Large

**Symptom**: `BatchTooLargeException` when using LOGGED BATCH.

**Fix**:
```yaml
# cassandra.yaml
batch_size_warn_threshold_in_kb: 64     # warn above 64 KB
batch_size_fail_threshold_in_kb: 640    # fail above 640 KB

# Batches are NOT for bulk loading. They are for atomic writes
# to denormalized tables. Use async concurrent writes for bulk loads.
```

---

## 16. FAQ

### Q1: What is the ideal partition size?

Target 10-100 MB per partition, with a maximum of 100K-200K rows. Use `nodetool tablestats` to check `Compacted partition maximum bytes`. Partitions above 100 MB trigger warnings; above 256 MB causes operational problems.

### Q2: How do I choose between STCS, LCS, TWCS, and UCS?

- **STCS**: write-heavy, batch-load workloads with infrequent reads.
- **LCS**: read-heavy workloads needing consistent read latency.
- **TWCS**: time-series data with TTL (most efficient for expiring data).
- **UCS** (5.0+): general-purpose; auto-adapts. Best choice for new deployments on Cassandra 5.0.

### Q3: Should I use materialized views?

Avoid materialized views. They are officially discouraged (experimental in 4.x, deprecated in 5.x) due to consistency bugs and operational complexity. Maintain denormalized tables manually with application-level writes or LOGGED BATCH.

### Q4: How do I handle many-to-many relationships?

Create two tables: one partitioned by entity A, one by entity B. Write to both on every relationship change. Example: user_follows (partition by follower), user_followers (partition by followed).

### Q5: Can Cassandra handle full-text search?

Not natively. SAI (5.0+) supports basic substring matching with `LIKE`. For full-text search with ranking, stemming, and fuzzy matching, use Elasticsearch or Solr alongside Cassandra.

### Q6: What is the maximum column count per table?

Cassandra does not enforce a hard column limit, but the guardrails framework (4.1+) can set warn/fail thresholds. Practically, tables with > 200 columns become unwieldy. Schema-less patterns using `map<text, text>` or UDTs are often better.

### Q7: How do I bulk-load data into Cassandra?

Use `sstableloader` for the fastest bulk loads. It writes SSTables directly without going through the write path. For smaller loads, use `COPY FROM` in cqlsh or the DataStax Bulk Loader (dsbulk).

```bash
# sstableloader example
sstableloader -d 10.0.1.1 /path/to/sstables/keyspace/table/

# dsbulk example
dsbulk load -url data.csv -k ecommerce -t products -h 10.0.1.1
```

### Q8: How do counters work internally?

Counter cells store deltas, not absolute values. Each replica independently accumulates deltas. Reads merge deltas from all replicas to compute the total. This is why counters can temporarily diverge -- repair reconciles them.

### Q9: Can I use Cassandra for a job queue?

This is a well-known anti-pattern. Each dequeue (DELETE) creates a tombstone. Over time, tombstones accumulate and degrade read performance catastrophically. Use Kafka, RabbitMQ, or Redis Streams for queues.

### Q10: How do I migrate from relational to Cassandra?

1. Identify your queries (not your entities).
2. Design one Cassandra table per query pattern.
3. Accept denormalization and write amplification.
4. Use `sstableloader` or `dsbulk` for initial data migration.
5. Run the relational and Cassandra systems in parallel during transition.

### Q11: What is the recommended replication factor for each use case?

- **Messaging / financial**: RF=3 minimum (LOCAL_QUORUM reads/writes).
- **Time series / metrics**: RF=2 acceptable if data can be re-ingested; RF=3 standard.
- **IoT**: RF=3 for production; RF=2 for cost-sensitive edge deployments.
- **Analytics**: RF=2 if source-of-truth exists elsewhere; RF=3 otherwise.

### Q12: How does Cassandra 5.0 vector search compare to dedicated vector databases?

Cassandra 5.0 SAI vector search is designed for co-located vector + metadata queries, not as a replacement for dedicated vector DBs like Pinecone or Milvus. Use it when: (a) you already have data in Cassandra, (b) your vector dimensions are moderate (< 1024), and (c) you need transactional consistency between vectors and metadata. For large-scale ANN search (millions of high-dimensional vectors), dedicated vector databases are more performant.

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*
