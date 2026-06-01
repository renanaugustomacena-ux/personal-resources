# MongoDB: Operations e Monitoring

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
1. Server Operations
2. Database Operations
3. Collection Operations
4. Index Operations
5. Backup and Restore
6. Monitoring Tools
7. Performance Monitoring
8. Maintenance

---

## 1. Server Operations

### 1.1 Server Commands

```javascript
// Server status
db.adminCommand({ serverStatus: 1 })

// Build info
db.adminCommand({ buildInfo: 1 })

// Get log
db.adminCommand({ getLog: "startupWarnings" })

// Current operations
db.currentOp()
db.currentOp({ allUsers: true })

// Kill operation
db.adminCommand({ killOp: <opId> })

// Shutdown server (must be admin)
db.adminCommand({ shutdown: 1 })
```

### 1.2 Server Configuration

```javascript
// Get parameter
db.adminCommand({ getParameter: 1, parameter: "logLevel" })

// Set parameter
db.adminCommand({ setParameter: 1, logLevel: 2 })

// Set cache size (WiredTiger)
db.adminCommand({ setParameter: 1, wiredTigerConcurrentWriteTransactions: 128 })
```

---

## 2. Database Operations

### 2.1 Database Commands

```javascript
// List databases
db.adminCommand({ listDatabases: 1 })

// Get current database stats
db.stats()

// Drop database
db.dropDatabase()

// Rename database (clone then drop)
db.adminCommand({ copydb: 1, fromhost: "source", fromdb: "sourceDB", todb: "targetDB" })
```

### 2.2 Database Profiling

```javascript
// Get profiling status
db.getProfilingStatus()

// Set profiling level
// 0 = off, 1 = slow queries, 2 = all
db.setProfilingLevel(1, { slowms: 100 })

// Query profiler
db.system.profile.find().sort({ millis: -1 }).limit(10)
```

---

## 3. Collection Operations

### 3.1 Collection Commands

```javascript
// List collections
db.getCollectionNames()

// Create collection
db.createCollection("users")
db.createCollection("logs", { capped: true, size: 10000000 })

// Collection stats
db.collection.stats()
db.collection.stats({ scale: 1024 })  // in KB

// Rename collection
db.collection.renameCollection("new_name")

// Drop collection
db.collection.drop()

// Validate collection
db.collection.validate({ full: true })
```

### 3.2 Collection Management

```javascript
// Compact collection (WiredTiger)
db.runCommand({ compact: "collection_name" })

// Empty collection (faster than drop)
db.collection.remove({})

// Get storage size
db.collection.storageSize()

// Total index size
db.collection.totalIndexSize()
```

---

## 4. Index Operations

### 4.1 Index Commands

```javascript
// List indexes
db.collection.getIndexes()

// Create index
db.collection.createIndex({ field: 1 })
db.collection.createIndex({ field1: 1, field2: -1 }, { unique: true })

// Drop index
db.collection.dropIndex("index_name")
db.collection.dropIndexes()  // except _id

// Rebuild index
db.collection.reIndex()

// Hide index (MongoDB 4.4+)
db.collection.hideIndex("index_name")
db.collection.unhideIndex("index_name")
```

### 4.2 Index Statistics

```javascript
// Index usage stats
db.collection.aggregate([{ $indexStats: {} }])

// Index size
db.collection.indexStats()
```

---

## 5. Backup and Restore

### 5.1 mongodump/mongorestore

```javascript
// Backup entire database
mongodump --uri="mongodb://localhost:27017" --out=/backup

// Backup specific database
mongodump --uri="mongodb://localhost:27017" --db=mydb --out=/backup

// Backup specific collection
mongodump --uri="mongodb://localhost:27017" --db=mydb --collection=users

// Restore
mongorestore --uri="mongodb://localhost:27017" /backup

// Restore to different name
mongorestore --uri="mongodb://localhost:27017" --nsInclude="mydb.users" --nsTo="newdb.users" /backup
```

### 5.2 Point-in-Time Recovery

```javascript
// Use oplog for point-in-time recovery

// Get oplog time range
db.getSiblingDB("local").oplog.rs.find().sort({ ts: -1 }).limit(1)

// Backup with oplog
mongodump --uri="mongodb://localhost:27017" --oplog --out=/backup

// Restore to specific time
// Use --pointInTimeRecovery with timestamp
```

### 5.3 Cluster Backup

```javascript
// Sharded cluster backup
// 1. Stop balancer
sh.stopBalancer()

// 2. Backup config
mongodump --uri="mongodb://config1:27017,config2:27017"

// 3. Backup each shard
mongodump --uri="mongodb://shard1:27017"
mongodump --uri="mongodb://shard2:27017"

// 4. Start balancer
sh.startBalancer()
```

---

## 6. Monitoring Tools

### 6.1 MongoDB Tools

```javascript
// mongostat - quick status
// mongostat --uri="mongodb://localhost:27017" 1

// mongotop - collection-level time
// mongotop --uri="mongodb://localhost:27017" 1
```

### 6.2 Built-in Monitoring

```javascript
// ServerStatus key metrics
db.adminCommand({ serverStatus: 1 })

// Connections
db.adminCommand({ serverStatus: 1 }).connections

// Memory
db.adminCommand({ serverStatus: 1 }).mem

// WiredTiger cache
db.adminCommand({ serverStatus: 1 }).wiredTiger.cache

// Operations
db.adminCommand({ serverStatus: 1 }).opcounters
```

---

## 7. Performance Monitoring

### 7.1 Key Metrics

```javascript
// Connection usage
db.adminCommand({ serverStatus: 1 }).connections.current

// Cache hit ratio
const cache = db.adminCommand({ serverStatus: 1 }).wiredTiger.cache
const hitRatio = (cache["bytes read into cache"] - cache["cache overflow score"]) / 
                 cache["bytes read into cache"]

// Operations per second
db.adminCommand({ serverStatus: 1 }).opcounters

// Document metrics
db.adminCommand({ serverStatus: 1 }).document

// Queue lengths
db.adminCommand({ serverStatus: 1 }).globalLock.currentQueue
```

### 7.2 Slow Query Monitoring

```javascript
// Enable profiler for slow queries
db.setProfilingLevel(1, { slowms: 100 })

// Analyze slow queries
db.system.profile.find({ millis: { $gt: 1000 } })
  .sort({ ts: -1 })
  .limit(10)
  .forEach(printjson)
```

---

## 8. Maintenance

### 8.1 Regular Maintenance Tasks

```javascript
// Compact collection (reclaim space)
db.runCommand({ compact: "collection_name" })

// Repair database (if corruption)
db.repairDatabase()

// Validate collection
db.collection.validate({ full: true })

// Clean up orphaned data (sharded)
db.getSiblingDB("admin").runCommand({ cleanupOrphaned: "db.collection" })
```

### 8.2 Space Reclamation

```javascript
// Use compact to reclaim space after deletions
// For replica sets, do on each member

// compact is blocking, use with care
// Consider scheduling during maintenance window
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*