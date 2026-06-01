# MongoDB: Performance Tuning e Optimisation

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
1. Query Optimization
2. Index Optimization
3. Memory Management
4. Storage Engine
5. Connection Management
6. Profiling
7. Performance Patterns
8. Troubleshooting

---

## 1. Query Optimization

### 1.1 Explain and Query Plans

```javascript
// Basic explain
db.orders.explain().find({ status: "completed" })

// Execution stats
db.orders.explain("executionStats").find({ status: "completed" })

// All plans execution (for complex queries)
db.orders.explain("allPlansExecution").find({ 
  customer_id: 123, 
  date: { $gte: "2024-01-01" }
})

// Understanding output:
// - stage: The operation stage (COLLSCAN, IXSCAN, FETCH, etc.)
// - indexName: Which index used
// - documentsExamined: How many docs scanned
// - documentsReturned: How many returned
// - executionTimeMillis: Total execution time
```

### 1.2 Query Patterns

```javascript
// ❌ BAD: Using $where (slow, no index)
db.users.find({ $where: "this.field > 100" })

// ✅ GOOD: Use regular operators
db.users.find({ field: { $gt: 100 } })

// ❌ BAD: Implicit $and
db.users.find({ field1: 1, field2: 2 })  // Two separate fields

// ✅ GOOD: Explicit $and for same field
db.users.find({ 
  $and: [
    { field: { $gt: 10 } },
    { field: { $lt: 100 } }
  ]
})

// ❌ BAD: Using regex at start
db.users.find({ email: { $regex: "^john" } })

// ✅ GOOD: Use index prefix (if possible)
// Or use text search

// ✅ GOOD: Use projection to reduce data
db.orders.find(
  { status: "completed" },
  { order_id: 1, total: 1, customer: 1 }
)
```

### 1.3 Covered Queries

```javascript
// Query that only uses index (no document access)
// Requirements:
// - Query fields all in index
// - Projection includes only indexed fields
// - No array or object fields in projection

// Create covering index
db.users.createIndex({ email: 1, name: 1 })

// This query is covered
db.users.find(
  { email: "john@example.com" },
  { email: 1, name: 1, _id: 0 }
)

// Verify in explain:
// "indexOnly": true
// "indexName": "email_1_name_1"
```

---

## 2. Index Optimization

### 2.1 Index Types Selection

```javascript
// Single field index
db.users.createIndex({ email: 1 })

// Compound index - order matters!
db.orders.createIndex({ status: 1, created_at: -1 })

// When to use what:
// - Queries with equality first: { status: "x" } -> (status, created_at)
// - Queries with range first: { price: { $gt: 10 } } -> (price, name) NOT (name, price)

// Multi-key index (automatic for arrays)
db.products.createIndex({ tags: 1 })

// Partial index - smaller, more efficient
db.orders.createIndex(
  { status: 1, created_at: -1 },
  { partialFilterExpression: { status: { $in: ["completed", "pending"] } } }
)
```

### 2.2 Index Management

```javascript
// List indexes
db.collection.getIndexes()

// Check index usage
db.collection.aggregate([{ $indexStats: {} }])

// Remove unused index
db.collection.dropIndex("email_1")

// Hide index (test without dropping)
db.collection.hideIndex("email_1")
db.collection.unhideIndex("email_1")

// Rebuild index (rarely needed)
db.collection.reIndex()
```

### 2.3 Index Performance

```javascript
// Index selectivity
// - High selectivity: few documents match -> good for index
// - Low selectivity: many documents match -> full scan may be faster

// Compound index for compound queries
// Query: { status: "active", category: "electronics" }
// Index: { status: 1, category: 1 } - GOOD
// Index: { category: 1, status: 1 } - BAD (can't use status prefix)

// Partial indexes for active data
db.orders.createIndex(
  { customer_id: 1 },
  { partialFilterExpression: { status: { $ne: "cancelled" } } }
)
```

---

## 3. Memory Management

### 3.1 WiredTiger Cache

```javascript
// Default cache size: 50% of RAM - 1GB

// Check current cache usage
db.serverStatus().wiredTiger.cache

// Configure cache size (in mongod.conf)
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4

// Cache hit ratio (should be > 80%)
db.serverStatus().wiredTiger.cache["bytes read into cache"]
db.serverStatus().wiredTiger.cache["bytes written from cache"]
```

### 3.2 Memory for Queries

```javascript
// Default memory limit per aggregation stage: 100MB

// Use allowDiskUse for large operations
db.orders.aggregate([
  { $group: { _id: "$customer", total: { $sum: "$total" } } }
], { allowDiskUse: true })

// Or use $bucketAuto for automatic memory management
db.orders.aggregate([
  { $bucketAuto: {
    groupBy: "$total",
    buckets: 5,
    output: { count: { $sum: 1 } }
  }}
])
```

---

## 4. Storage Engine

### 4.1 WiredTiger Configuration

```javascript
// Compression settings
// Default: snappy compression

// Check current settings
db.adminCommand({ getLog: "startupWarnings" })

// Configure compression (in mongod.conf)
storage:
  wiredTiger:
    engineConfig:
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true
```

### 4.2 Directory for Data

```javascript
// Specify data directory
storage:
  dbPath: /data/db

// Separate journal directory (for performance)
storage:
  journal:
    enabled: true
    directory: /journal
```

---

## 5. Connection Management

### 5.1 Connection Pool

```javascript
// Default pool size: 100 connections
// Configurable in connection string
const client = new MongoClient("mongodb://localhost:27017", {
  maxPoolSize: 100,
  minPoolSize: 10,
  maxIdleTimeMS: 30000
})

// Monitor connection usage
db.serverStatus().connections
// current, available, totalCreated
```

### 5.2 Connection Best Practices

```javascript
// 1. Use connection pools
// 2. Close connections properly
// 3. Use connection strings for config
// 4. Handle connection errors with retry
// 5. Use authenticated connections in production
```

---

## 6. Profiling

### 6.1 Profiler Configuration

```javascript
// Set profiling level
// 0: Off
// 1: Slow queries (>100ms)
// 2: All queries

db.setProfilingLevel(1, { slowms: 100 })

// Query profiler data
db.system.profile.find().sort({ millis: -1 }).limit(10)

// Get profiler status
db.getProfilingStatus()
```

### 6.2 Slow Query Analysis

```javascript
// Find slow queries
db.system.profile.find({ millis: { $gt: 1000 } }).sort({ ts: -1 })

// Analyze specific query pattern
db.system.profile.aggregate([
  { $group: {
    _id: { ns: "$ns", pattern: "$query" },
    count: { $sum: 1 },
    avgTime: { $avg: "$millis" }
  }},
  { $sort: { avgTime: -1 } },
  { $limit: 20 }
])
```

---

## 7. Performance Patterns

### 7.1 Pagination

```javascript
// ❌ BAD: Skip-based (slow for large offsets)
db.orders.find().sort({ _id: 1 }).skip(10000).limit(20)

// ✅ GOOD: Keyset pagination
// Store last seen ID from previous page
const lastId = previousPageLastId

db.orders.find({ _id: { $gt: lastId } })
  .sort({ _id: 1 })
  .limit(20)

// For date-based pagination
db.orders.find({ created: { $lt: lastDate } })
  .sort({ created: -1 })
  .limit(20)
```

### 7.2 Bulk Operations

```javascript
// Bulk write operations
const bulk = db.collection.initializeOrderedBulkOp()

// Insert many
bulk.insert({ doc: 1 })
bulk.insert({ doc: 2 })
// ... up to 1000
bulk.execute()

// Update many at once
bulk = db.collection.initializeBulkOp()
bulk.find({ status: "pending" }).update({ $set: { status: "processed" } })
bulk.execute()

// Parallel bulk (unordered)
bulk = db.collection.initializeUnorderedBulkOp()
```

---

## 8. Troubleshooting

### 8.1 Common Performance Issues

```javascript
// 1. Full collection scan
// - Solution: Create appropriate indexes

// 2. High memory usage
// - Solution: Use allowDiskUse, reduce working set

// 3. Connection exhaustion
// - Solution: Check connection pool, close connections

// 4. Slow aggregation
// - Solution: Add $match early, use indexes, reduce data

// 5. Lock contention
// - Solution: Use transactions only when needed, reduce write conflicts
```

### 8.2 Diagnostic Commands

```javascript
// Server status
db.serverStatus()

// Collection stats
db.collection.stats()

// Index stats
db.collection.aggregate([{ $indexStats: {} }])

// Current operations
db.currentOp({ allUsers: true })

// Top operations
db.adminCommand({ top: 1 })

// Check locks
db.adminCommand({ serverStatus: 1 }).locks
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*