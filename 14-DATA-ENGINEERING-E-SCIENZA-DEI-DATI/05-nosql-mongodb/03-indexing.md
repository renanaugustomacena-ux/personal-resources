# MongoDB indexing e Query Optimization

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
1. Index Types
2. Index Creation
3. Query Optimization
4. Covered Queries
5. Partial Indexes
6. Text Indexes
7. Geospatial Indexes
8. Index Management

---

## 1. Index Types

### 1.1 Single Field Index

```javascript
// Basic ascending index
db.users.createIndex({ "email": 1 })

// Descending index
db.users.createIndex({ "birth_date": -1 })
```

### 1.2 Compound Index

```javascript
// Compound index - order matters!
db.orders.createIndex({ "customer_id": 1, "created_at": -1 })

// Use for:
// - Queries matching both fields
// - Queries matching first field only
// - Sort by first field or both
```

### 1.3 Multi-Key Index

```javascript
// Index on array field
db.products.createIndex({ "tags": 1 })

// For: { "tags": ["electronics", "sale"] }
// Creates index entry for each array element
```

---

## 2. Index Creation

### 2.1 Basic Creation

```javascript
// Create index
db.collection.createIndex({ "field": 1 })

// Unique index
db.users.createIndex({ "email": 1 }, { unique: true })

// Background creation
db.large_collection.createIndex({ "field": 1 }, { background: true })
```

### 2.2 Index Options

```javascript
// TTL index (auto-delete after time)
db.logs.createIndex(
  { "created_at": 1 },
  { expireAfterSeconds: 3600 }
)

// Sparse index (indexes only documents with field)
db.orders.createIndex(
  { "shipped_at": 1 },
  { sparse: true }
)

// Case-insensitive index
db.users.createIndex(
  { "name": "text" },
  { default_language: "english" }
)
```

---

## 3. Query Optimization

### 3.1 Use EXPLAIN

```javascript
// Analyze query plan
db.orders.explain().find({ "customer_id": 101 })

// Verbose mode
db.orders.explain("queryPlanner").find({ "status": "completed" })
```

### 3.2 Query Patterns

```javascript
// Good: Use indexed fields
db.users.find({ "email": "john@example.com" })

// Avoid: Use functions on indexed fields
db.users.find({ "lower(email)": "john@example.com" })

// Good: Range on indexed field
db.orders.find({ "amount": { $gt: 100 } })

// Good: Sort on indexed field
db.orders.find({ "status": "completed" }).sort({ "created_at": -1 })
```

---

## 4. Covered Queries

```javascript
// Query uses only indexed fields
db.users.find(
  { "email": "john@example.com" },
  { "_id": 0, "email": 1 }
)

// Explain shows IXSCAN without FETCH
```

---

## 5. Partial Indexes

### 5.1 Conditional Index

```javascript
// Index only completed orders
db.orders.createIndex(
  { "customer_id": 1 },
  { 
    partialFilterExpression: { "status": "completed" }
  }
)
```

---

## 6. Text Indexes

### 6.1 Text Search

```javascript
// Create text index
db.articles.createIndex({ "content": "text", "title": "text" })

// Search
db.articles.find({ $text: { $search: "database" } })

// Phrase search
db.articles.find({ $text: { $search: "\"full text search\"" } })

// Sort by relevance
db.articles.find(
  { $text: { $search: "mongodb" } },
  { score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } })
```

---

## 7. Geospatial Indexes

### 7.1 2dsphere

```javascript
// Location data
{
  "name": "Store NYC",
  "location": { "type": "Point", "coordinates": [-74.006, 40.7128] }
}

db.stores.createIndex({ "location": "2dsphere" })

// Find nearby
db.stores.find({
  location: {
    $near: {
      $geometry: { "type": "Point", "coordinates": [-73.98, 40.75] },
      $maxDistance: 5000
    }
  }
})
```

---

## 8. Index Management

### 8.1 Index Operations

```javascript
// List indexes
db.collection.getIndexes()

// Drop index
db.collection.dropIndex("email_1")

// Rebuild index
db.collection.reIndex()
```

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*