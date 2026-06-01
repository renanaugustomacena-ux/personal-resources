# MongoDB: Migration e Integrations

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
1. SQL to MongoDB Migration
2. Application Migration Patterns
3. Schema Migration
4. Data Migration Strategies
5. Integration Patterns
6. Change Data Capture
7. Migration Tools

---

## 1. SQL to MongoDB Migration

### 1.1 Migration Process

```javascript
// Phase 1: Analysis
// - Map SQL schema to MongoDB collections
// - Identify relationships
// - Decide embedding vs referencing

// Phase 2: Create schema
// Create MongoDB collections based on mapping
db.createCollection("users")
db.createCollection("orders")
db.createCollection("order_items")

// Phase 3: Data transformation
// Convert SQL data to document format
const users = sqlQuery("SELECT * FROM users")
db.users.insertMany(users.map(u => ({
  _id: u.id,
  name: u.name,
  email: u.email,
  created_at: u.created_at
})))
```

### 1.2 SQL to MongoDB Mapping

```javascript
// SQL JOIN -> $lookup
// Original SQL:
/*
SELECT u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed'
*/

// MongoDB:
db.users.aggregate([
  { $lookup: {
    from: "orders",
    localField: "_id",
    foreignField: "user_id",
    as: "orders"
  }},
  { $unwind: "$orders" },
  { $match: { "orders.status": "completed" } },
  { $project: { name: 1, total: "$orders.total" } }
])
```

### 1.3 Data Type Mapping

```javascript
// SQL Types -> BSON Types
// INT -> NumberInt
// BIGINT -> NumberLong
// VARCHAR -> String
// TEXT -> String
// DATE -> Date
// DATETIME -> Date
// DECIMAL -> NumberDecimal
// BLOB -> BinData
// BOOLEAN -> Boolean

// Handle decimal precision
{ amount: NumberDecimal("100.25") }
```

---

## 2. Application Migration Patterns

### 2.1 Driver Migration

```javascript
// From SQL to MongoDB driver

// Before (SQL)
db.query("SELECT * FROM users WHERE id = ?", [userId])

// After (MongoDB)
db.collection.findOne({ _id: userId })

// Batch insert
db.collection.insertMany(documents)
```

### 2.2 ORM/ODM Migration

```javascript
// Mongoose (Node.js)
// Define schema
const UserSchema = new Schema({
  name: String,
  email: { type: String, unique: true },
  created: { type: Date, default: Date.now }
})

// Use like normal MongoDB
const user = await User.findOne({ email })
```

### 2.3 Aggregation Migration

```javascript
// SQL GROUP BY -> MongoDB $group
// SQL: SELECT status, COUNT(*) FROM orders GROUP BY status

// MongoDB:
db.orders.aggregate([
  { $group: { _id: "$status", count: { $sum: 1 } } }
])

// SQL: SELECT status, AVG(total) FROM orders GROUP BY status

// MongoDB:
db.orders.aggregate([
  { $group: { _id: "$status", avg: { $avg: "$total" } } }
])
```

---

## 3. Schema Migration

### 3.1 Additive Changes

```javascript
// Add new field (backward compatible)
db.collection.updateMany(
  {},
  { $set: { new_field: "default" } },
  { upsert: false }
)

// Add new field with conditional
db.collection.updateMany(
  { status: "active" },
  { $set: { activation_date: new Date() } }
)

// Add nested field
db.collection.updateMany(
  {},
  { $set: { "profile.settings.notifications": true } }
)
```

### 3.2 Rename Fields

```javascript
// Rename with aggregation pipeline (MongoDB 4.2+)
db.collection.updateMany(
  {},
  [
    { $set: { new_name: "$old_name" } },
    { $unset: "$old_name" }
  ]
)

// Verify rename
db.collection.find({}, { new_name: 1 })
```

### 3.3 Type Changes

```javascript
// Change field type - use aggregation
db.collection.aggregate([
  { $project: {
    numeric_field: { $toInt: "$string_field" },
    other_fields: "$$ROOT"
  }},
  { $out: "collection_copy" }
])
```

---

## 4. Data Migration Strategies

### 4.1 Batch Migration

```javascript
// Migrate in batches to avoid memory issues
async function migrateCollection(sourceCollection, targetCollection) {
  const batchSize = 1000
  let lastId = null
  
  while (true) {
    const query = lastId 
      ? { _id: { $gt: lastId } } 
      : {}
    
    const batch = await sourceCollection.find(query)
      .sort({ _id: 1 })
      .limit(batchSize)
      .toArray()
    
    if (batch.length === 0) break
    
    // Transform data
    const transformed = batch.map(transformDoc)
    
    // Insert
    await targetCollection.insertMany(transformed)
    
    lastId = batch[batch.length - 1]._id
    console.log(`Migrated ${batch.length} documents`)
  }
}
```

### 4.2 Dual-Write Pattern

```javascript
// Write to both systems during migration
async function dualWrite(data) {
  // Write to SQL (old system)
  await sqlDb.insert("orders", data)
  
  // Write to MongoDB (new system)
  await mongoDb.collection("orders").insertOne(data)
  
  // Verify consistency
}
```

### 4.3 Shadow Migration

```javascript
// Write to both, read from new
async function shadowWrite(data) {
  // Write to both systems
  await sqlDb.insert("orders", data)
  await mongoDb.collection("orders").insertOne(data)
  
  // Only read from new
  const result = await mongoDb.collection("orders").findOne(...)
  return result
}
```

---

## 5. Integration Patterns

### 5.1 REST API Integration

```javascript
// Express + MongoDB example
const express = require('express')
const { MongoClient } = require('mongodb')

const app = express()
const client = new MongoClient("mongodb://localhost:27017")

app.get('/api/users', async (req, res) => {
  const users = await client.db("app").collection("users").find().toArray()
  res.json(users)
})

app.listen(3000)
```

### 5.2 Event-Driven Integration

```javascript
// Publish events on data changes
const changeStream = db.collection("orders").watch()

changeStream.on("change", (change) => {
  // Publish to message queue
  if (change.operationType === "insert") {
    messageQueue.publish("order_created", change.fullDocument)
  }
})
```

### 5.3 CDC (Change Data Capture)

```javascript
// Use oplog for CDC
const oplog = db.getSiblingDB("local").oplog.rs

// Tail oplog for changes
const cursor = oplog.find({ ts: { $gt: lastTimestamp } }).tailable()

while (cursor.hasNext()) {
  const doc = await cursor.next()
  processChange(doc)
}
```

---

## 6. Change Data Capture

### 6.1 MongoDB Change Streams

```javascript
// Listen to all changes in collection
const changeStream = db.collection.watch()

changeStream.on("change", (change) => {
  console.log("Operation:", change.operationType)
  console.log("Document:", change.fullDocument)
})

// Filter specific operations
const changeStream = db.collection.watch([
  { $match: { operationType: { $in: ["insert", "update"] } } }
])

// Full pipeline in change stream
const changeStream = db.collection.watch([
  { $match: { "fullDocument.status": "completed" } },
  { $project: { _id: 1, status: 1 } }
])
```

### 6.2 Kafka Integration

```javascript
// Use Kafka Connect for MongoDB
// Configuration:
/*
{
  "name": "mongo-source",
  "config": {
    "connector.class": "com.mongodb.kafka.connect.MongoSourceConnector",
    "mongo.uri": "mongodb://localhost:27017",
    "database": "mydb",
    "collection": "orders",
    "topic.prefix": "mongodb"
  }
}
*/
```

---

## 7. Migration Tools

### 7.1 Atlas Data Migration

```javascript
// Use MongoDB Atlas migration service
// - Import from SQL databases
// - Import from other MongoDB clusters
// - Visual schema mapping
```

### 7.2 mongodump/mongorestore

```javascript
// Export from source
mongodump --uri="mongodb://source:27017" --db=mydb --out=/migration

// Import to target
mongorestore --uri="mongodb://target:27017" --db=mydb /migration/mydb
```

### 7.3 Professional Services

```javascript
// Atlas Schema Validation
// MongoDB Compass Schema Analysis
// mongomapper for Ruby
// Doctrine ODM for PHP
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*