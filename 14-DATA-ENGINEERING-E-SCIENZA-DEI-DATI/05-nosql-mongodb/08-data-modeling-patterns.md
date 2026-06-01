# MongoDB: Data Modeling Patterns

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
1. Relational to Document
2. One-to-One Patterns
3. One-to-Many Patterns
4. Many-to-Many Patterns
5. Tree Structures
6. Time Series
7. Polymorphic Patterns
8. Anti-Patterns

---

## 1. Relational to Document

### 1.1 Schema Conversion Strategy

```javascript
// SQL Table -> MongoDB Collection

// SQL:
/*
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(255) UNIQUE,
  created_at TIMESTAMP
);

CREATE TABLE orders (
  id INT PRIMARY KEY,
  user_id INT REFERENCES users(id),
  total DECIMAL(10,2),
  status VARCHAR(20),
  created_at TIMESTAMP
);
*/

// MongoDB:
db.users.insertMany([
  { _id: 1, name: "John", email: "john@test.com", created_at: new Date() },
  { _id: 2, name: "Jane", email: "jane@test.com", created_at: new Date() }
])

db.orders.insertMany([
  { _id: 101, user_id: 1, total: 150.00, status: "completed", created_at: new Date() },
  { _id: 102, user_id: 1, total: 75.00, status: "pending", created_at: new Date() }
])
```

### 1.2 Join Strategies

```javascript
// Option 1: Manual lookup
const user = db.users.findOne({ _id: 1 })
const orders = db.orders.find({ user_id: user._id }).toArray()

// Option 2: $lookup aggregation
db.users.aggregate([
  { $match: { _id: 1 } },
  { $lookup: {
    from: "orders",
    localField: "_id",
    foreignField: "user_id",
    as: "orders"
  }}
])

// Option 3: Embed (if frequently accessed together)
{
  _id: 1,
  name: "John",
  orders: [
    { _id: 101, total: 150.00, status: "completed" },
    { _id: 102, total: 75.00, status: "pending" }
  ]
}
```

---

## 2. One-to-One Patterns

### 2.1 Embedded Pattern

```javascript
// Embedded for frequently accessed together data
{
  _id: 1,
  name: "John Doe",
  email: "john@example.com",
  profile: {
    bio: "Software engineer",
    avatar: "https://example.com/avatar.jpg",
    website: "https://john.dev"
  }
}

// When to embed:
// - Data accessed together
// - User always views profile with user
// - Profile is small (< few KB)
```

### 2.2 Reference Pattern

```javascript
// Separate collection when:
// - Data is large
// - Rarely accessed together
// - May be updated independently

db.users.insertOne({
  _id: 1,
  name: "John"
})

db.profiles.insertOne({
  _id: 1,
  user_id: 1,
  bio: "Very long bio...",
  history: [/* large array */]
})
```

---

## 3. One-to-Many Patterns

### 3.1 One-to-Few (Embedding)

```javascript
// Embed when < 100 items typically
{
  _id: 1,
  name: "Order #1001",
  items: [
    { sku: "W001", qty: 2 },
    { sku: "G001", qty: 1 }
  ],
  created_at: new Date()
}

// Query all items in order - no lookup needed
db.orders.findOne({ _id: 1 })
```

### 3.2 One-to-Many (Reference)

```javascript
// Reference when many items or unbounded
// Orders collection
{
  _id: 1,
  customer_id: 101,
  created_at: new Date()
}

// Order Items collection
db.order_items.insertMany([
  { order_id: 1, sku: "W001", qty: 2 },
  { order_id: 1, sku: "G001", qty: 1 },
  { order_id: 1, sku: "W002", qty: 3 }
])

// $lookup to get items with order
db.orders.aggregate([
  { $match: { _id: 1 } },
  { $lookup: {
    from: "order_items",
    localField: "_id",
    foreignField: "order_id",
    as: "items"
  }}
])
```

### 3.3 Subset Pattern

```javascript
// Store recent items, reference archive
{
  _id: 1,
  customer_id: 101,
  recent_items: [
    { sku: "W001", qty: 2 },
    { sku: "G001", qty: 1 }
  ],
  item_count: 156  // Total items
}

// Query recent items directly
db.orders.findOne({ _id: 1 }).recent_items

// Query historical via reference
db.order_items.find({ order_id: 1 }).limit(50)
```

---

## 4. Many-to-Many Patterns

### 4.1 Document References

```javascript
// Students collection
{ _id: 1, name: "Alice", enrolled_course_ids: [101, 102] }
{ _id: 2, name: "Bob", enrolled_course_ids: [102] }

// Courses collection
{ _id: 101, name: "Math 101" }
{ _id: 102, name: "Physics 101" }

// Get student's courses with $lookup
db.students.aggregate([
  { $match: { _id: 1 } },
  { $unwind: "$enrolled_course_ids" },
  { $lookup: {
    from: "courses",
    localField: "enrolled_course_ids",
    foreignField: "_id",
    as: "courses"
  }},
  { $unwind: "$courses" },
  { $group: {
    _id: "$_id",
    name: { $first: "$name" },
    courses: { $push: "$courses.name" }
  }}
])
```

### 4.2 Array of References

```javascript
// Products with supplier references
{
  _id: 1,
  name: "Widget",
  supplier_ids: [100, 101, 102]
}

// Suppliers
{ _id: 100, name: "Supplier A" }
{ _id: 101, name: "Supplier B" }

// Get all suppliers for a product
db.products.aggregate([
  { $match: { _id: 1 } },
  { $lookup: {
    from: "suppliers",
    localField: "supplier_ids",
    foreignField: "_id",
    as: "suppliers"
  }}
])
```

---

## 5. Tree Structures

### 5.1 Parent Reference

```javascript
// Category as tree
db.categories.insertMany([
  { _id: "electronics", parent_id: null, name: "Electronics" },
  { _id: "phones", parent_id: "electronics", name: "Phones" },
  { _id: "laptops", parent_id: "electronics", name: "Laptops" },
  { _id: "smartphones", parent_id: "phones", name: "Smartphones" }
])

// Find parent
db.categories.findOne({ _id: "smartphones" }).parent_id

// Find children
db.categories.find({ parent_id: "phones" })
```

### 5.2 Materialized Path

```javascript
// Store full path
db.categories.insertMany([
  { _id: "electronics", path: "electronics", name: "Electronics" },
  { _id: "phones", path: "electronics.phones", name: "Phones" },
  { _id: "smartphones", path: "electronics.phones.smartphones", name: "Smartphones" }
])

// Find descendants of electronics
db.categories.find({ path: /^electronics\./ })

// Find ancestors of smartphone
db.categories.find({ path: { $regex: /^\.electronics\.phones\.smartphones$/ } })
```

### 5.3 Recursive with $graphLookup

```javascript
// Use $graphLookup for recursive hierarchy
db.categories.aggregate([
  { $match: { _id: "smartphones" } },
  { $graphLookup: {
    from: "categories",
    startWith: "$parent_id",
    connectFromField: "parent_id",
    connectToField: "_id",
    as: "ancestors"
  }}
])
```

---

## 6. Time Series Patterns

### 6.1 Time Series Collections (MongoDB 5.0+)

```javascript
// Create time-series collection
db.createCollection("sensor_readings", {
  timeseries: {
    timeField: "timestamp",
    metaField: "sensor_id",
    granularity: "hours"
  }
})

// Insert readings
db.sensor_readings.insertOne({
  sensor_id: "sensor-001",
  timestamp: new Date(),
  temperature: 22.5,
  humidity: 65
})

// Automatic partitioning for efficient queries
// Automatic bucket by time
```

### 6.2 Bucket Pattern (Pre-5.0)

```javascript
// Bucket by hour
{
  _id: "2024-01-15T10",
  sensor_id: "sensor-001",
  start: new Date("2024-01-15T10:00:00Z"),
  end: new Date("2024-01-15T10:59:59Z"),
  readings: [
    { time: ISODate("2024-01-15T10:15:00Z"), temp: 22.3 },
    { time: ISODate("2024-01-15T10:30:00Z"), temp: 22.5 }
  ],
  count: 2,
  min_temp: 22.3,
  max_temp: 22.5,
  avg_temp: 22.4
}

// Aggregate by bucket
db.sensor_readings.aggregate([
  { $group: {
    _id: { sensor_id: "$sensor_id", hour: { $hour: "$timestamp" } },
    count: { $sum: 1 }
  }}
])
```

---

## 7. Polymorphic Patterns

### 7.1 Single Collection Different Types

```javascript
// Store different "types" in one collection
db.documents.insertMany([
  {
    _id: 1,
    type: "invoice",
    invoice_number: "INV-001",
    amount: 150.00,
    due_date: new Date()
  },
  {
    _id: 2,
    type: "contract",
    contract_id: "CONTRACT-001",
    parties: ["Company A", "Company B"],
    signed: true
  },
  {
    _id: 3,
    type: "letter",
    recipient: "John Doe",
    body: "Hello..."
  }
])

// Query by type
db.documents.find({ type: "invoice" })

// Project type-specific fields
db.documents.aggregate([
  { $match: { type: "invoice" } },
  { $project: {
    invoice_number: 1,
    amount: 1,
    type: 1
  }}
])
```

---

## 8. Anti-Patterns

### 8.1 Massive Arrays

```javascript
// ❌ BAD: Unbounded array growth
{
  _id: 1,
  events: [
    // Grows infinitely
  ]
}

// ✅ GOOD: Use bucket or reference
{
  _id: "2024-01-15",
  date: new Date("2024-01-15"),
  events: [{...}, {...}]  // Limited per day
}
```

### 8.2 Over-Normalization

```javascript
// ❌ BAD: Too much referencing
// Each field in separate collection
{ _id: 1, name_id: 1, email_id: 2, address_id: 3 }

// ✅ GOOD: Embed related data
{ _id: 1, name: "John", email: "john@test.com", address: {...} }
```

### 8.3 Gold plating

```javascript
// ❌ BAD: Creating complex structures before needed
// Only use when real access pattern emerges
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*