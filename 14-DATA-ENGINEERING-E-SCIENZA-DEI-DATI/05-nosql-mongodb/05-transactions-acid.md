# MongoDB: Transactions e ACID

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
1. Transaction Fundamentals
2. Multi-Document Transactions
3. Transaction Options
4. Retry Logic
5. Isolation Levels
6. Transaction Limits
7. Common Patterns
8. Performance Considerations

---

## 1. Transaction Fundamentals

### 1.1 Transaction vs Single Document ACID

```javascript
// Single document is atomic (since MongoDB 3.0)
// This update is all-or-nothing:
db.orders.updateOne(
  { _id: 1 },
  { $inc: { quantity: -1 }, $set: { updated: true } }
)

// Multi-document transactions allow ACID across multiple operations
const session = db.getMongo().startSession()

session.withTransaction(() => {
  const db = session.getDatabase("shop")
  
  // Decrements inventory
  db.inventory.updateOne(
    { sku: "WIDGET-001" },
    { $inc: { stock: -1 } }
  )
  
  // Creates order - both succeed or both fail
  db.orders.insertOne({
    sku: "WIDGET-001",
    status: "pending"
  })
})

session.endSession()
```

### 1.2 Transaction Support by Version

```javascript
// MongoDB 4.0: Replica set transactions
// MongoDB 4.2: Sharded cluster transactions
// MongoDB 5.0+: Multi-warehouse transactions

// Requirements:
// - Replica set (or sharded cluster)
// - WiredTiger storage engine
// - No view or $where in transaction
```

---

## 2. Multi-Document Transactions

### 2.1 Basic Transaction Pattern

```javascript
// Start session and transaction
const session = db.getMongo().startSession()

// Execute with automatic retry
session.withTransaction(() => {
  const db = session.getDatabase("shop")
  
  // Multiple operations
  const inventory = db.inventory
  const orders = db.orders
  
  // Operation 1: Update inventory
  const result = inventory.updateOne(
    { sku: "WIDGET-001", stock: { $gt: 0 } },
    { $inc: { stock: -1 } }
  )
  
  if (result.modifiedCount === 0) {
    throw new Error("Out of stock")
  }
  
  // Operation 2: Create order
  orders.insertOne({
    sku: "WIDGET-001",
    quantity: 1,
    status: "confirmed"
  })
  
  return "success"
})

session.endSession()

// Manual transaction (for more control)
const session = db.getMongo().startSession()
try {
  session.startTransaction({
    readConcern: { level: "snapshot" },
    writeConcern: { w: "majority" }
  })
  
  const db = session.getDatabase("shop")
  db.collection.updateOne(...)
  db.anotherCollection.insertOne(...)
  
  session.commitTransaction()
} catch (e) {
  session.abortTransaction()
  throw e
} finally {
  session.endSession()
}
```

### 2.2 Transaction Across Collections

```javascript
// Transaction accessing multiple databases
const session = db.getMongo().startSession()

session.withTransaction(() => {
  const shop = session.getDatabase("shop")
  const analytics = session.getDatabase("analytics")
  
  // Update inventory in shop database
  shop.inventory.updateOne(
    { sku: "WIDGET-001" },
    { $inc: { stock: -1 } }
  )
  
  // Record analytics event in separate database
  analytics.events.insertOne({
    type: "purchase",
    sku: "WIDGET-001",
    timestamp: new Date()
  })
})

session.endSession()
```

---

## 3. Transaction Options

### 3.1 Read Concern

```javascript
// Read concern levels:
// - local (default): Read from primary
// - majority: Read acknowledged by majority
// - snapshot: Serializable snapshot (only in transactions)
// - available: For read preference secondary, may return stale data

session.startTransaction({
  readConcern: { level: "snapshot" }
})

// Or at start
session.startTransaction({
  readConcern: { level: "majority" },
  writeConcern: { w: "majority" }
})
```

### 3.2 Write Concern

```javascript
// Write concern in transactions
session.startTransaction({
  writeConcern: { w: "majority" }
})

// Note: wtimeout applies to transaction commit
session.startTransaction({
  writeConcern: { w: "majority", wtimeout: 10000 }
})
```

### 3.3 Max Transaction Lock Timeout

```javascript
// Configure lock timeout per transaction
// Default: unlimited

session.startTransaction({
  maxTransactionLockRequestTimeoutMillis: 5000
})

// If transaction holds lock longer than this, it may be killed
```

---

## 4. Retry Logic

### 4.1 Automatic Retry with withTransaction

```javascript
// withTransaction handles retry automatically for:
// - Transient transaction errors
// - Lock conflicts

session.withTransaction({
  maxCommitTimeMS: 30000  // max time for commit
}, () => {
  // Your operations here
})
```

### 4.2 Manual Retry Pattern

```javascript
// For more control over retry behavior
async function runTransactionWithRetry(txnFunc) {
  const maxRetries = 3
  let retryCount = 0
  
  while (retryCount < maxRetries) {
    const session = db.getMongo().startSession()
    try {
      session.startTransaction()
      const result = await txnFunc(session)
      await session.commitTransaction()
      return result
    } catch (error) {
      retryCount++
      if (error.hasErrorLabel("TransientTransactionError") && 
          retryCount < maxRetries) {
        console.log(`Retry ${retryCount}: ${error.message}`)
        await new Promise(r => setTimeout(r, 1000 * retryCount))
      } else if (error.hasErrorLabel("UnknownTransactionCommitResult")) {
        // Commit may have succeeded, verify
        // Check state or query for side effects
      } else {
        throw error
      }
    } finally {
      session.endSession()
    }
  }
}
```

---

## 5. Isolation Levels

### 5.1 Transaction Isolation

```javascript
// With readConcern: "snapshot" (serializable)
// Transaction sees consistent snapshot at start

session.startTransaction({ readConcern: { level: "snapshot" } })

// Reads within transaction see same data
// Even if concurrent operations modify data

// Without snapshot:
// - readConcern: "local" may see uncommitted changes

// Example isolation demonstration
// Terminal 1:
const s1 = db.getMongo().startSession()
s1.startTransaction()
db.orders.findOne({ _id: 1 })  // Returns: { _id: 1, total: 100 }

// Terminal 2 (concurrent):
db.orders.updateOne({ _id: 1 }, { $set: { total: 200 } })

// Terminal 1 (within transaction):
// Still sees: { _id: 1, total: 100 } due to snapshot isolation
```

### 5.2 Read Your Own Writes

```javascript
// By default, transactions don't see own uncommitted writes
// Use $dbPointer or read after write within transaction

session.startTransaction()

// Write
db.users.updateOne(
  { _id: 1 },
  { $set: { status: "active" } }
)

// Read back (need to use same session or re-read after commit)
const user = db.users.findOne({ _id: 1 })

// Or use readConcern after commit
session.commitTransaction()
db.users.findOne({ _id: 1 })  // Now sees new value
```

---

## 6. Transaction Limits

### 6.1 Size and Duration Limits

```javascript
// Transaction size limits:
// - Max document size: 16MB
// - No limit on number of operations, but memory is bounded

// Duration limits:
// - No hard limit, but default lock timeout: unlimited
// - Slow transactions affect cluster performance
// - Consider long-running operations carefully

// Best practice: Keep transactions short
// Avoid:
// - User interaction within transaction
// - Network calls
// - Large batch operations
```

### 6.2 Unsupported Operations

```javascript
// Cannot use in transactions:
// - Bulk operations (bulk.find.*)
// - $out / $merge aggregation stages
// - Creating indexes (db.collection.createIndex)
// - Drop collection (db.collection.drop)
// - Rename collection (db.collection.renameCollection)
// - Operations on system collections

// Cannot use on views:
db.getSiblingDB("admin").runCommand({
  collMod: "myView",
  viewPipeline: [...]
})  // Error: view not supported in transaction
```

### 6.3 Operations That Cause Transaction Abort

```javascript
// Operations that abort transaction:
// - Duplicate key errors (unique index violation)
// - Write conflicts
// - Memory exceeded
// - Lock timeout

// Handle with retry
```

---

## 7. Common Patterns

### 7.1 Order Processing Pattern

```javascript
async function processOrder(orderId, items) {
  const session = db.getMongo().startSession()
  
  try {
    return await session.withTransaction(async () => {
      const shop = session.getDatabase("shop")
      const inventory = shop.inventory
      const orders = shop.orders
      
      // Verify and reserve inventory
      for (const item of items) {
        const result = await inventory.updateOne(
          { 
            sku: item.sku, 
            stock: { $gte: item.quantity }
          },
          { $inc: { stock: -item.quantity } }
        )
        
        if (result.modifiedCount === 0) {
          throw new Error(`Insufficient stock for ${item.sku}`)
        }
      }
      
      // Create order
      const order = {
        orderId,
        items,
        status: "confirmed",
        createdAt: new Date()
      }
      
      await orders.insertOne(order)
      
      return order
    })
  } finally {
    session.endSession()
  }
}
```

### 7.2 Transfer Pattern

```javascript
async function transferFunds(fromAccount, toAccount, amount) {
  const session = db.getMongo().startSession()
  
  return session.withTransaction(async () => {
    const db = session.getDatabase("bank")
    
    // Debit source account
    const debitResult = db.accounts.updateOne(
      { 
        _id: fromAccount, 
        balance: { $gte: amount }
      },
      { $inc: { balance: -amount } }
    )
    
    if (debitResult.modifiedCount === 0) {
      throw new Error("Insufficient funds")
    }
    
    // Credit destination account
    db.accounts.updateOne(
      { _id: toAccount },
      { $inc: { balance: amount } }
    )
    
    // Record transaction
    db.transactions.insertOne({
      from: fromAccount,
      to: toAccount,
      amount,
      timestamp: new Date()
    })
  })
}
```

---

## 8. Performance Considerations

### 8.1 Transaction Performance Tips

```javascript
// 1. Keep transactions short
// - Batch operations before transaction
// - Remove user interaction from transaction

// 2. Use appropriate read concerns
// - snapshot for strong consistency
// - local when eventual is okay

// 3. Index design
// - Ensure transactions can use indexes
// - Avoid large scans within transaction

// 4. Connection pooling
// - Configure connection pool for transaction workers
// - Avoid connection exhaustion
```

### 8.2 Monitoring Transactions

```javascript
// Current operations with transaction info
db.currentOp({ "transaction": { $exists: true } })

// Transaction statistics
db.getSiblingDB("admin").serverStatus().transactions

// Check locks
db.getSiblingDB("admin").db.currentOp().inLock

// Explain transaction
db.adminCommand({
  explain: {
    find: "orders",
    filter: { status: "pending" },
    readConcern: { level: "snapshot" },
    sid: session.getSessionId()
  }
})
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*