# MongoDB: Architettura, Data Model e Design Patterns

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
1. MongoDB Overview
2. Document Structure
3. Collection Design
4. Schema Design Patterns
5. Indexing Fundamentals
6. Aggregation Framework
7. Replication
8. Sharding
9. Transactions
10. Performance Tuning
11. Security

---

## 1. MongoDB Overview

### 1.1 What is MongoDB

MongoDB è un document database open-source che memorizza dati in documenti simili a JSON (BSON). Offre alta scalabilità e flessibilità.

**Key Features**:
- Document-oriented (no fixed schema)
- High performance
- Horizontal scalability via sharding
- Rich query language
- Aggregation framework
- Geospatial support

MongoDB appartiene alla categoria dei database NoSQL (Not Only SQL), distinguendosi dai database relazionali tradizionali per il suo modello di dati flessibile e la capacità di scalare orizzontalmente.

### 1.2 MongoDB vs SQL

| SQL | MongoDB |
|-----|---------|
| Table | Collection |
| Row | Document |
| Column | Field |
| JOIN | $lookup / embedding |
| Primary Key | _id field |
| Index | Index |
| Schema (CREATE TABLE) | Dynamic (no schema required) |

### 1.3 Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                      MongoDB Cluster                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │
│  │   mongos    │   │   mongos    │   │   mongos    │      │
│  │  (Router)   │   │  (Router)   │   │  (Router)   │      │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│  ┌─────────────────────────┼─────────────────────────┐      │
│  │              Config Server                      │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │      │
│  │  │  shard1  │  │  shard2  │  │  shard3  │       │      │
│  │  │(primary) │  │(primary) │  │(primary) │       │      │
│  │  │ + sec    │  │ + sec    │  │ + sec    │       │      │
│  │  └──────────┘  └──────────┘  └──────────┘       │      │
│  └─────────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Componenti principali:**
- **mongos**: Router che gestisce le richieste dai client
- **mongod**: Processo del database server
- **Config Server**: Mantiene metadata del cluster
- **Shard**: Partizione dei dati

### 1.4 Use Cases

```javascript
// Applicazioni ideali per MongoDB:
// - Content Management
// - Real-time analytics
// - IoT data storage
// - Mobile apps
// - E-commerce catalogs
// - User profiles

// Esempi di utilizzo:
// - Catalogo prodotti con attributi variabili
// - Profili utente con campi dinamici
// - Session storage
// - Log aggregation
```

---

## 2. Document Structure

### 2.1 BSON Types

MongoDB utilizza BSON (Binary JSON) per memorizzare i documenti. BSON estende JSON con tipi binari aggiuntivi:

```javascript
// BSON Data Types:

// String (UTF-8)
{ "name": "John Doe" }

// Integer 32-bit
{ "age": NumberInt(30) }

// Integer 64-bit
{ "views": NumberLong(9999999999) }

// Double (64-bit IEEE 754)
{ "price": 19.99 }

// Boolean
{ "active": true }

// Date (UTC)
{ "created_at": new Date("2024-01-15T10:30:00Z") }

// Null
{ "deleted_at": null }

// Array
{ "tags": ["news", "tech", "database"] }

// Embedded Document
{ 
  "address": { 
    "street": "123 Main St",
    "city": "New York",
    "zip": "10001",
    "country": "USA"
  }
}

// ObjectId (unique identifier)
{ "_id": ObjectId("507f1f77bcf86cd799439011") }

// Binary Data
{ "attachment": BinData(0, "base64encoded...") }

// Decimal128 (precise decimal)
{ "amount": NumberDecimal("100.25") }

// Timestamp
{ "ts": Timestamp(1234567890, 1) }

// Regular Expression
{ "pattern": /^[a-z]+$/i }

// JavaScript Code
{ "validator": Code("function() { return true; }") }

// Symbol (deprecated)
```

### 2.2 ObjectId Structure

```javascript
// ObjectId è un 12-byte identifier:
// [0-3] timestamp (4 bytes)
// [4-6] machine identifier (3 bytes)
// [7-8] process ID (2 bytes)
// [9-11] counter (3 bytes)

ObjectId("507f1f77bcf86cd799439011")
// 507f1f77 = timestamp (seconds since epoch)
// bcf86cd7 = machine ID
// 99439011 = PID + counter

// Metodi utili su ObjectId:
new ObjectId().getTimestamp()  // Data di creazione
new ObjectId().toString()       // String representation
ObjectId.isValid("...")         // Validazione
```

### 2.3 _id Field

Il campo _id è obbligatorio per ogni documento:

```javascript
// Automaticamente generato se non specificato
{ "_id": ObjectId("507f1f77bcf86cd799439011") }

// _id personalizzato (stringa)
{ "_id": "user-12345", "name": "John" }

// _id personalizzato (numero)
{ "_id": 1001, "name": "John" }

// _id personalizzato (UUID)
{ "_id": UUID("550e8400-e29b-41d4-a716-446655440000") }

// Note:
// - Deve essere unico all'interno della collection
// - Non può essere un array
// - Non può contenere più di un documento con lo stesso valore
```

### 2.4 Nested Documents

```javascript
// Documento con struttura nidificata
{
  "_id": 1,
  "name": "Order #1001",
  "customer": {
    "id": 101,
    "name": "John Doe",
    "email": "john@example.com",
    "shipping": {
      "address": "123 Main St",
      "city": "New York",
      "zip": "10001"
    }
  },
  "items": [
    {
      "sku": "WIDGET-001",
      "name": "Widget Pro",
      "quantity": 2,
      "price": 29.99
    },
    {
      "sku": "GADGET-002",
      "name": "Gadget Plus",
      "quantity": 1,
      "price": 49.99
    }
  ],
  "total": 109.97,
  "created_at": new Date("2024-01-15")
}
```

---

## 3. Collection Design

### 3.1 Collection Concepts

```javascript
// Collection è un gruppo di documenti
// Non ha schema fisso (schema flessibile)

// Creare collection
db.createCollection("users")

// Creare capped collection (preallocata, FIFO)
db.createCollection("logs", { 
  capped: true, 
  size: 10000000,  // 10MB max
  max: 10000        // o 10000 documenti
})

// Capped collection properties:
// - Non può essere sharded
// - Non supporta $out in aggregation
// - Non supporta remove con query
```

### 3.2 Collection Operations

```javascript
// List collections
db.getCollectionNames()

// Rename collection
db.users.renameCollection("customers")

// Drop collection
db.users.drop()

// Stats
db.users.stats()
db.users.dataSize()      // dimensione dati
db.users.storageSize()   // spazio allocato
db.users.totalSize()     // dimensione totale (index + data)
db.users.totalIndexSize() // spazio indici

// Validate (check integrity)
db.users.validate()
```

---

## 4. Schema Design Patterns

### 4.1 Embedding Patterns

L'embedding memorizza dati correlati nello stesso documento:

```javascript
// One-to-One: Embedded
{
  "_id": 1,
  "username": "johndoe",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Software engineer",
    "avatar_url": "/images/john.jpg"
  }
}

// One-to-Few: Embedded
{
  "_id": 1,
  "name": "Order #1001",
  "customer_id": 101,
  "items": [
    { "sku": "W001", "qty": 2 },
    { "sku": "W002", "qty": 1 },
    { "sku": "G001", "qty": 3 }
  ],
  "created_at": new Date()
}

// When to Embed:
// ✓ Dati acceduti insieme frequentemente
// ✓ Relazione one-to-few (1-100 items)
// ✓ Dati che non cambiano indipendentemente
// ✓ Dati che non superano 16MB per documento
```

### 4.2 Referencing Patterns

Il referencing usa riferimenti tra documenti:

```javascript
// Ordini che referenziano Clienti
// orders collection
{
  "_id": 1,
  "customer_id": ObjectId("507f1f77bcf86cd799439011"),
  "total": 150.00,
  "status": "completed"
}

// customers collection
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "Acme Corp",
  "email": "orders@acme.com"
}

// With array of references
{
  "_id": 1,
  "customer_id": 101,
  "item_ids": [1, 2, 3]
}

// Reference Items
db.items.find({ "_id": { $in: [1, 2, 3] } })

// When to Reference:
// - Relazioni many-to-many
// - Dati che cambiano frequentemente
// - Documenti che crescono molto
// - Dati acceduti indipendentemente
```

### 4.3 Anti-Patterns

```javascript
// ❌ EVITARE: Massive Array
{
  "_id": 1,
  "events": [
    // Milioni di eventi!
  ]
}

// ❌ EVITARE: Unbounded Growth
{
  "_id": 1,
  "logs": []  // Cresce all'infinito
}

// ❌ EVITARE: Referenze join-intensive
// Troppi $lookup per query comune
// Meglio embed per dati acceduti insieme
```

### 4.4 Design Guidelines Summary

| Pattern | Use When | Example |
|---------|-----------|---------|
| **Embedding** | Dati acceduti insieme, one-to-few | User + Profile |
| **Referencing** | Many-to-many, dati variabili | Products + Reviews |
| **Subset** | Array grandi parzialmente usati | Post + Comments (ultimi 10) |
| **Bucket** | Time-series data | Daily events |

```javascript
// Subset Pattern
{
  "_id": 1,
  "title": "My Blog Post",
  "content": "...",
  "recent_comments": [
    // Solo ultimi 10 commenti
    { "text": "Great post!", "date": ... }
  ],
  "total_comments": 150
}

// Bucket Pattern (time-series)
{
  "_id": "2024-01-15",
  "date": "2024-01-15",
  "events": [
    { "time": "10:00", "event": "..." },
    // Centinaia di eventi del giorno
  ]
}
```

---

## 5. Indexing Fundamentals

### 5.1 Index Types

```javascript
// Single Field Index
db.users.createIndex({ "email": 1 })
db.users.createIndex({ "age": -1 })  // descending

// Compound Index (order matters!)
db.orders.createIndex({ "status": 1, "created_at": -1 })

// Unique Index
db.users.createIndex({ "email": 1 }, { unique: true })

// Compound Unique Index
db.orders.createIndex(
  { "customer_id": 1, "order_number": 1 },
  { unique: true }
)

// Multi-key Index (automatico per array)
db.products.createIndex({ "tags": 1 })

// Text Index (per ricerca full-text)
db.articles.createIndex({ "content": "text", "title": "text" })

// Hashed Index (per sharding)
db.users.createIndex({ "_id": "hashed" })

// Geospatial Index
db.places.createIndex({ "location": "2dsphere" })

// Wildcard Index (MongoDB 4.2+)
db.products.createIndex({ "specs.$**": 1 })
```

### 5.2 Index Options

```javascript
// TTL Index (auto-delete dopo expiration)
db.sessions.createIndex(
  { "last_activity": 1 },
  { expireAfterSeconds: 3600 }
)

// Partial Index (solo subset)
db.orders.createIndex(
  { "customer_id": 1 },
  { 
    partialFilterExpression: { 
      "status": { $in: ["pending", "processing"] } 
    }
  }
)

// Case Insensitive Index
db.users.createIndex(
  { "username": 1 },
  { 
    collation: { 
      locale: "en", 
      strength: 2  // case-insensitive 
    } 
  }
)

// Sparse Index (solo documenti con campo)
db.users.createIndex(
  { "phone": 1 },
  { sparse: true }
)

// Covering Index (include fields in index)
db.users.createIndex({ "email": 1, "name": 1 })

// Hide Index (for testing/drop)
db.users.hideIndex("email_1")
```

### 5.3 Index Management

```javascript
// List indexes
db.users.getIndexes()

// Drop index
db.users.dropIndex("email_1")
db.users.dropIndexes()  // except _id

// Rebuild index
db.users.reIndex()

// Rename index
db.collection.renameIndex("old_index_name", "new_index_name")

// Index statistics
db.users.aggregate([
  { $indexStats: {} }
])

// Check index usage
db.users.find({ "email": "test@example.com" }).explain()
```

---

## 6. Aggregation Framework

### 6.1 Pipeline Stages

```javascript
// $match - Filter documents
db.orders.aggregate([
  { $match: { status: "completed" } }
])

// $project - Reshape documents
db.orders.aggregate([
  { $project: { 
    customer_id: 1, 
    total: 1,
    year: { $year: "$created_at" }
  }}
])

// $group - Aggregate
db.orders.aggregate([
  { $group: {
    _id: "$customer_id",
    total_spent: { $sum: "$total" },
    order_count: { $sum: 1 }
  }}
])

// $sort - Sort results
db.orders.aggregate([
  { $sort: { total: -1, created_at: -1 } }
])

// $limit - Limit results
db.orders.aggregate([
  { $limit: 10 }
])

// $skip - Skip documents
db.orders.aggregate([
  { $skip: 100 },
  { $limit: 10 }
])

// $unwind - Deconstruct array
db.orders.aggregate([
  { $unwind: "$items" }
])

// $lookup - Join collections
db.orders.aggregate([
  { $lookup: {
    from: "products",
    localField: "items.product_id",
    foreignField: "_id",
    as: "product_details"
  }}
])

// $facet - Multiple pipelines
db.products.aggregate([
  { $facet: {
    byCategory: [{ $group: { _id: "$category", count: { $sum: 1 } } }],
    byPrice: [{ $bucket: { groupBy: "$price", boundaries: [0, 50, 100, Infinity] } }]
  }}
])
```

### 6.2 Aggregation Operators

```javascript
// Arithmetic
{ $add: ["$price", "$tax"] }
{ $subtract: ["$total", "$discount"] }
{ $multiply: ["$quantity", "$price"] }
{ $divide: ["$total", "$count"] }
{ $mod: ["$total", 3] }
{ $abs: "$value" }

// String
{ $toUpper: "$name" }
{ $toLower: "$email" }
{ $substr: ["$name", 0, 5] }
{ $concat: ["$first_name", " ", "$last_name"] }
{ $trim: { input: "  hello  ", chars: " " } }
{ $split: { string: "a,b,c", separator: "," } }
{ $regexFind: { input: "$text", regex: "pattern" } }

// Array
{ $size: "$tags" }
{ $slice: "$items", 0, 5 }
{ $filter: { input: "$items", as: "item", cond: { $gt: ["$$item.price", 10] } } }
{ $map: { input: "$items", as: "item", in: { $multiply: ["$$item.price", 1.1] } } }
{ $in: ["$status", ["active", "pending"]] }
{ $anyElementTrue: "$array_field" }

// Date
{ $year: "$created_at" }
{ $month: "$created_at" }
{ $dayOfMonth: "$created_at" }
{ $dayOfWeek: "$created_at" }
{ $hour: "$created_at" }
{ $minute: "$created_at" }
{ $second: "$created_at" }
{ $dateToString: { format: "%Y-%m-%d", date: "$created_at" } }
{ $dateFromString: { dateString: "2024-01-15" } }

// Conditional
{ $cond: { if: { $gte: ["$qty", 10] }, then: "bulk", else: "regular" } }
{ $ifNull: ["$field", "default" ] }
{ $switch: { branches: [ { case: { $eq: ["$type", "a"] }, then: 1 } ], default: 0 } }

// Object
{ $objectToArray: "$specs" }
{ $arrayToObject: "$pairs" }
{ $mergeObjects: ["$address", { "new_field": "value" }] }
```

### 6.3 Aggregation Performance

```javascript
// $match all'inizio del pipeline (filtra presto)
db.orders.aggregate([
  { $match: { status: "completed", date: { $gt: "2024-01-01" } } },
  { $group: { _id: "$customer_id", total: { $sum: "$total" } } }
])

// $project finale per ridurre dimensione
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $group: { _id: "$customer_id", total: { $sum: "$total" } } },
  { $project: { _id: 0, customer: "$_id", total: 1 } }
])

// Usare $limit prima di operazioni pesanti
db.orders.aggregate([
  { $sort: { date: -1 } },
  { $limit: 100 },
  { $group: { ... } }
])

// $lookup con pipeline ottimizzato
db.orders.aggregate([
  { $lookup: {
    from: "products",
    pipeline: [
      { $match: { active: true } },
      { $project: { name: 1, price: 1 } }
    ],
    as: "products"
  }}
])
```

---

## 7. Replication

### 7.1 Replica Set Architecture

```javascript
// Replica Set Components:
// - Primary: riceve write operations
// - Secondary: replicano dal primary
// - Arbiter: solo voting, no data

// Configurazione iniziale
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017", arbiterOnly: true }
  ]
})

// Aggiungere member
rs.add("mongo4:27017")

// Aggiungere arbiter
rs.addArb("mongo5:27017")

// Rimuovere member
rs.remove("mongo4:27017")

// Reconfigurare
rs.reconfig({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017", priority: 2 },
    { _id: 1, host: "mongo2:27017", priority: 1 },
    { _id: 2, host: "mongo3:27017", priority: 0 }  // hidden
  ]
})
```

### 7.2 Read Preferences

```javascript
// primary (default) - solo primary
db.collection.find({}, { readPreference: "primary" })

// secondary - random secondary
db.collection.find({}, { readPreference: "secondary" })

// secondaryPreferred - secondary se disponibile, altrimenti primary
db.collection.find({}, { readPreference: "secondaryPreferred" })

// primaryPreferred - primary se disponibile, altrimenti secondary
db.collection.find({}, { readPreference: "primaryPreferred" })

// nearest - nodo con minor latenza
db.collection.find({}, { readPreference: "nearest" })

// Con tag sets
db.collection.find(
  { status: "active" },
  { readPreference: { mode: "secondary", tags: [{ "region": "us-east" }] } }
)
```

### 7.3 Write Concerns

```javascript
// w: 0 - No acknowledgment (fastest)
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: 0 } })

// w: 1 - Acknowledgment from primary (default)
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: 1 } })

// w: "majority" - Acknowledgment from majority
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: "majority" } })

// w: "all" - All members
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: "all" } })

// j: true - Acknowledge journaling
db.collection.insertOne({ doc: "test" }, { writeConcern: { j: true } })

// wtimeout: Timeout per write concern
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: "majority", wtimeout: 5000 } })
```

### 7.4 Failover Behavior

```javascript
// Automatic failover: 10-30 secondi
// Primary down -> election -> secondary becomes primary

// Heartbeat: ogni 2 secondi
// Election: se non riceve heartbeat per 10 secondi

// Trigger manual election:
rs.stepDown()
rs.stepDown(60)  // seconds to wait before accepting new primary

// Check replica set status
rs.status()
rs.isMaster()
db.adminCommand({ replSetGetStatus: 1 })
```

---

## 8. Sharding

### 8.1 Shard Key Selection

```javascript
// Range-based Sharding
// Documenti con shard key simile vanno nello stesso shard
sh.shardCollection("mydb.orders", { "customer_id": 1 })

// Pros:
// - Efficiente per range queries
// - Ordine naturale
// Cons:
// - Hot spots su shard key frequente

// Hashed Sharding
// Distribuisce uniformemente
sh.shardCollection("mydb.users", { "_id": "hashed" })

// Pros:
// - Distribuzione uniforme
// Cons:
// - Non efficiente per range queries
// - Non supporta covered queries

// Compound Sharding
// Shard key composito
sh.shardCollection("mydb.orders", { "region": 1, "customer_id": "hashed" })

// Best practices:
// - Shard key ad alta cardinalità
// - Usare campo frecuentemente in query
// - Evitare monotonically increasing values (ObjectId)
```

### 8.2 Sharding Commands

```javascript
// Enable sharding su database
sh.enableSharding("mydb")

// Shard collection
sh.shardCollection("mydb.orders", { "customer_id": 1 })

// Add shard
sh.addShard("rs2/mongo4:27017,mongo5:27017")

// Remove shard (drain)
db.adminCommand({ removeShard: "shard0002" })

// Check shard distribution
db.orders.getShardDistribution()

// Check status
sh.status()

// Refine collection shard
sh.updateZoneKeyRange(
  "mydb.coll",
  { "region": "US" },
  { "region": "US" }
)

// Tag aware sharding
sh.addTagRange(
  "mydb.orders",
  { "region": "US" },
  { "region": "US" },
  "USShard"
)

sh.addShardTag("shard0000", "USShard")
```

### 8.3 Chunk Management

```javascript
// Split chunk
db.adminCommand({
  split: "mydb.orders",
  find: { "customer_id": 500 }
})

// Move chunk
db.adminCommand({
  moveChunk: "mydb.orders",
  find: { "customer_id": 500 },
  to: "shard001"
})

// Check chunks
db.getSiblingDB("config").chunks.find({ ns: "mydb.orders" })

// Merge chunks
db.adminCommand({
  mergeChunks: "mydb.orders",
  bounds: [
    { "customer_id": MinKey },
    { "customer_id": 1000 }
  ]
})
```

---

## 9. Transactions

### 9.1 Transaction Fundamentals

```javascript
// MongoDB 4.0+ supports multi-document ACID transactions

// Start session
const session = db.getMongo().startSession()

// Transaction con callback
session.withTransaction(() => {
  const db = session.getDatabase("shop")
  
  // Operation 1: Decrement inventory
  db.inventory.updateOne(
    { "sku": "WIDGET-001" },
    { $inc: { "stock": -1 } }
  )
  
  // Operation 2: Insert order
  db.orders.insertOne({
    "sku": "WIDGET-001",
    "quantity": 1,
    "status": "pending"
  })
  
  // Operation 3: Update customer
  db.customers.updateOne(
    { "_id": 101 },
    { $inc: { "order_count": 1 } }
  )
})

session.endSession()

// Manual transaction
const session = db.getMongo().startSession()
session.startTransaction({ readConcern: "snapshot", writeConcern: "majority" })

try {
  const db = session.getDatabase("shop")
  db.orders.insertOne({ ... })
  session.commitTransaction()
} catch (e) {
  session.abortTransaction()
  throw e
} finally {
  session.endSession()
}
```

### 9.2 Transaction Options

```javascript
// Read concern
session.startTransaction({ readConcern: { level: "snapshot" } })
session.startTransaction({ readConcern: { level: "linearizable" } })

// Write concern
session.startTransaction({ writeConcern: { w: "majority" } })

// Retry on transient error (automatico in withTransaction)
session.withTransaction({
  // Retry settings
  maxTransactionLockRequestTimeoutMillis: 5000,
  readPreference: { mode: "primary" }
})

// Check transaction status
db.adminCommand({ serverStatus: 1 }).transactions
```

---

## 10. Performance Tuning

### 10.1 Query Optimization

```javascript
// Explain query
db.orders.explain().find({ "customer_id": 101 })
db.orders.explain("executionStats").find({ "customer_id": 101 })

// Covered queries (index only, no document fetch)
db.users.find(
  { "email": "john@example.com" },
  { "_id": 0, "email": 1 }
)

// Projection to reduce data
db.orders.find({}, { "items": 0 })  // exclude items
db.orders.find({}, { "customer_id": 1, "total": 1, "status": 1 })

// Use hint to force index
db.orders.find({ "customer_id": 101, "status": "completed" })
  .hint({ "customer_id": 1, "status": 1 })

// Limit e skip per pagination
db.orders.find().sort({ "created_at": -1 }).skip(100).limit(20)

// Keyset pagination (più efficiente di skip)
db.orders.find({ "_id": { $gt: lastSeenId } })
  .sort({ "_id": 1 })
  .limit(20)
```

### 10.2 Profiling

```javascript
// Set profiling level (0=off, 1=slow, 2=all)
db.setProfilingLevel(1, { slowms: 100 })

// Query profiler data
db.system.profile.find().sort({ millis: -1 }).limit(10)

// Show top operations
db.adminCommand({
  top: 1
})

// Current operations
db.currentOp({ allUsers: true })

// Kill long running operation
db.adminCommand({
  killOp: true,
  op: 12345678
})
```

### 10.3 Monitoring Commands

```javascript
// Server status
db.serverStatus()

// Database stats
db.stats()

// Collection stats
db.orders.stats()
db.orders.stats({ scale: 1024 * 1024 })  // MB

// Index stats
db.orders.aggregate([{ $indexStats: {} }])

// Connection info
db.adminCommand({ connectionStatus: 1 })

// Storage engine info
db.adminCommand({ serverStatus: 1 }).storageEngine
```

---

## 11. Security

### 11.1 Authentication

```javascript
// Create user con ruoli
db.createUser({
  user: "admin",
  pwd: passwordPrompt(),
  roles: [
    { role: "root", db: "admin" },
    { role: "readWriteAnyDatabase", db: "admin" }
  ]
})

// Create user con specifiche permissions
db.createUser({
  user: "appuser",
  pwd: "password123",
  roles: [
    { role: "readWrite", db: "mydb" },
    { role: "dbAdmin", db: "mydb" }
  ]
})

// Authenticate
db.auth("username", "password")

// LDAP Authentication (enterprise)
db.adminCommand({
  setParameter: 1,
  authenticationMechanisms: "PLAIN"
})
```

### 11.2 Role-Based Access Control

```javascript
// Built-in roles:
/*
  - read: read collections
  - readWrite: read and write collections
  - dbAdmin: admin collections
  - userAdmin: manage users/roles
  - clusterAdmin: manage cluster
  - backup: backup/restore
  - restore: restore
  - readAnyDatabase: read all
  - readWriteAnyDatabase: read/write all
  - userAdminAnyDatabase: manage users all
  - dbAdminAnyDatabase: admin all
  - root: all permissions
*/

// Create custom role
db.createRole({
  role: "analytics_reader",
  privileges: [
    { 
      resource: { db: "analytics", collection: "reports" }, 
      actions: ["find", "aggregate"] 
    },
    { 
      resource: { db: "analytics", collection: "metrics" }, 
      actions: ["find"] 
    }
  ],
  roles: []
})

// Assign role to user
db.grantRolesToUser("appuser", ["analytics_reader"])

// Revoke role
db.revokeRolesFromUser("appuser", ["analytics_reader"])

// List user roles
db.getUser("username").roles
```

### 11.3 Network Security

```javascript
// In mongod.conf:
/*
net:
  port: 27017
  bindIp: 127.0.0.1,10.0.0.1
  wireObjectCheck: true
  ipv6: false
*/

// TLS/SSL configuration
/*
net:
  tls:
    mode: requireTLS
    certificateKeyFile: /path/to/keyfile
    CAFile: /path/to/ca
    allowConnectionsWithoutCertificates: false
*/

// Rate limiting
security:
  javascriptEnabled: false  // disable server-side JS
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*