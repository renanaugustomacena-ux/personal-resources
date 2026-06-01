# MongoDB: Replication e Sharding

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
1. Replica Set Fundamentals
2. Replica Set Configuration
3. Read Preferences
4. Write Concerns
5. Failover e Election
6. Sharding Architecture
7. Shard Key Selection
8. Chunk Management
9. Zone-Based Sharding
10. Production Considerations

---

## 1. Replica Set Fundamentals

### 1.1 Architecture Overview

```javascript
// Replica Set Components:
// Primary: Write operations, read (default)
// Secondary: Replicate from primary, read (eventual consistency)
// Arbiter: Voting only, no data

// Data flow:
/*
  Client -> Primary (write) -> oplog
           \                 /
            -> Secondaries -> apply oplog
*/
```

### 1.2 Oplog (Operation Log)

```javascript
// Oplog is a capped collection in local database
// Contains all write operations for replication

// Check oplog size
db.getSiblingDB("local").oplog.rs.find().sort({ts: -1}).limit(1)

// Oplog sizing (automatic in 4.4+)
// Manual: db.adminCommand({ replSetResizeOplog: 1, size: 16384 })
```

---

## 2. Replica Set Configuration

### 2.1 Initial Configuration

```javascript
// Initialize replica set
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})

// Add arbiter
rs.addArb("mongo3:27017")

// Add member
rs.add("mongo4:27017")

// Remove member
rs.remove("mongo4:27017")
```

### 2.2 Member Configuration Options

```javascript
// Priority (0 = never become primary)
{
  _id: 1,
  host: "mongo2:27017",
  priority: 2  // Higher than primary (default 1)
}

// Hidden member (not visible to clients)
{
  _id: 2,
  host: "mongo3:27017",
  hidden: true,
  priority: 0
}

// Slave delay (delayed replication)
{
  _id: 3,
  host: "mongo4:27017",
  slaveDelay: 3600,  // 1 hour behind
  priority: 0
}

// Build indexes (default true)
{
  _id: 4,
  host: "mongo5:27017",
  buildIndexes: true
}
```

### 2.3 Reconfiguration

```javascript
// Reconfig with new settings
rs.reconfig({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017", priority: 2 },
    { _id: 1, host: "mongo2:27017", priority: 1 },
    { _id: 2, host: "mongo3:27017", priority: 0, hidden: true }
  ]
})

// Force reconfig (for recovery)
rs.reconfig(configuration, { force: true })
```

---

## 3. Read Preferences

### 3.1 Read Preference Modes

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
```

### 3.2 Tag-Based Read Preference

```javascript
// Set tags on members
cfg = rs.conf()
cfg.members[0].tags = { "region": "us-east", "storage": "ssd" }
cfg.members[1].tags = { "region": "us-west", "storage": "hdd" }
cfg.members[2].tags = { "region": "eu", "storage": "ssd" }
rs.reconfig(cfg)

// Use tags in read preference
db.collection.find(
  { active: true },
  { readPreference: { 
    mode: "secondary", 
    tags: [{ "region": "us-east" }] 
  }}
)

// Multiple tags (AND)
{ readPreference: { 
  mode: "secondary", 
  tags: [{ "region": "us-east", "storage": "ssd" }] 
}}
```

---

## 4. Write Concerns

### 4.1 Write Concern Levels

```javascript
// w: 0 - No acknowledgment (fastest)
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: 0 } })

// w: 1 - Primary acknowledgment (default)
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: 1 } })

// w: majority - Majority of members
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: "majority" } })

// w: all - All members
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: "all" } })

// w: <tag> - Members with specific tag
db.collection.insertOne({ doc: "test" }, { writeConcern: { w: "us-east" } })
```

### 4.2 Journal and Timeout

```javascript
// j: true - Wait for journal
db.collection.insertOne(
  { doc: "test" }, 
  { writeConcern: { w: 1, j: true } }
)

// wtimeout: Timeout in milliseconds
db.collection.insertOne(
  { doc: "test" }, 
  { writeConcern: { w: "majority", wtimeout: 5000 } }
)

// Combined
db.collection.updateMany(
  { status: "pending" },
  { $set: { processed: true } },
  { writeConcern: { w: "majority", j: true, wtimeout: 10000 } }
)
```

---

## 5. Failover e Election

### 5.1 Election Process

```javascript
// Trigger election manually
rs.stepDown()
rs.stepDown(60)  // seconds to wait

// Check status
rs.status()

// Fields in status:
// - state: PRIMARY, SECONDARY, RECOVERING, etc.
// - health: 1 = up, 0 = down
// - optime: last operation applied
// - electionTime: when became primary
```

### 5.2 Election Configuration

```javascript
// Configuration options for elections
cfg = rs.conf()
cfg.settings = {
  electionTimeoutMillis: 10000,  // 10 seconds (default)
  heartbeatTimeoutSecs: 10,    // 10 seconds (default)
  catchUpTimeoutMillis: 300000  // 5 minutes
}
rs.reconfig(cfg)

// Heartbeat interval
cfg.settings.heartbeatIntervalMillis = 2000  // 2 seconds
```

---

## 6. Sharding Architecture

### 6.1 Cluster Components

```javascript
// Sharding Components:
// - mongos: Router, stateless
// - Config Servers: Metadata (3 needed for production)
// - Shards: Data storage (replica sets)

/*
    Client
       |
    mongos (Router)
       |
  +----+----+
  |         |
Shard1   Shard2
(RS)      (RS)
*/
```

### 6.2 Shard Types

```javascript
// Shard (could be single server or replica set)
// Config servers must be replica set (MongoDB 3.4+)

// Initialize shard replica set
rs.initiate({ _id: "shard1", members: [...] })

// Add shard to cluster
sh.addShard("rs/shard1 mongo1:27017,mongo2:27017")

// Check shard status
sh.status()
db.getSiblingDB("config").shards.find()
```

---

## 7. Shard Key Selection

### 7.1 Shard Key Types

```javascript
// Range-based Sharding
// Documenti con shard key simile -> stesso shard
sh.shardCollection("mydb.orders", { "customer_id": 1 })

// Pros:
// - Efficient range queries
// - Natural ordering
// Cons:
// - Hot spots if key is monotonic

// Hashed Sharding
// Hash del campo -> distribuzione uniforme
sh.shardCollection("mydb.users", { "_id": "hashed" })

// Pros:
// - Even distribution
// - No hot spots
// Cons:
// - Cannot do efficient range queries

// Compound Sharding
sh.shardCollection("mydb.orders", { "region": 1, "customer_id": "hashed" })

// Chained prefix
// { "region": 1, "status": 1 } can use both:
// - Queries on region
// - Queries on region + status
// - Cannot efficiently query on status alone
```

### 7.2 Best Practices

```javascript
// Ideal shard key:
// - High cardinality (many distinct values)
// - Frequently used in queries
// - Not monotonically increasing
// - Even distribution of writes

// Good examples:
// - User ID for user-centric data
// - Timestamp for time-series (with hashed)
// - Composite of category + hashed ID

// Avoid:
// - Single low-cardinality values
// - Monotonically increasing (ObjectId default)
// - Frequently updated fields
```

---

## 8. Chunk Management

### 8.1 Chunk Operations

```javascript
// Split chunk manually
db.adminCommand({
  split: "mydb.orders",
  find: { "customer_id": 500 }
})

// Move chunk to another shard
db.adminCommand({
  moveChunk: "mydb.orders",
  find: { "customer_id": 500 },
  to: "shard0001"
})

// Check chunk distribution
db.getSiblingDB("config").chunks.find({ ns: "mydb.orders" }).count()

// Check shard distribution
db.orders.getShardDistribution()

// Merge chunks
db.adminCommand({
  mergeChunks: "mydb.orders",
  bounds: [
    { "customer_id": MinKey },
    { "customer_id": 1000 }
  ]
})
```

### 8.2 Chunk Size

```javascript
// Default chunk size: 64MB
// MongoDB automatically splits when chunk exceeds limit

// Can adjust (not recommended to change):
db.adminCommand({
  setParameter: 1,
  chunksplitTimeoutMS: 600000
})

// Manual split for better distribution
// Split based on data distribution, not default chunk size
```

---

## 9. Zone-Based Sharding

### 9.1 Zone Configuration

```javascript
// Add tag range to collection
sh.addTagRange(
  "mydb.orders",
  { "region": "US" },
  { "region": "US" },
  "USShard"
)

sh.addTagRange(
  "mydb.orders",
  { "region": "EU" },
  { "region": "EU" },
  "EUShard"
)

// Add shard to zone
sh.addShardTag("shard0000", "USShard")
sh.addShardTag("shard0001", "EUShard")

// Remove tag range
sh.removeTagRange(
  "mydb.orders",
  { "region": "US" },
  { "region": "US" }
)
```

### 9.2 Use Cases

```javascript
// Geographic distribution
// - US users -> US shard
// - EU users -> EU shard

// Data retention
// - Recent data -> hot storage
// - Archive data -> cold storage

// Tenant isolation
// - Tenant A -> dedicated shard
// - Tenant B -> dedicated shard
```

---

## 10. Production Considerations

### 10.1 Monitoring

```javascript
// Replica set health
rs.status()

// Replication lag
db.getSiblingDB("admin").runCommand({ replSetGetHealth: 1 })

// Check oplog time
db.getSiblingDB("local").oplog.rs.find().sort({ts: -1}).limit(1)
// Calculate: (oldest - newest) / 1000 / 60 = minutes

// Shard balance
sh.getBalancerState()
db.getSiblingDB("config").chunks.count()
```

### 10.2 Troubleshooting

```javascript
// Member down
// - Check network connectivity
// - Check logs
// - Check disk space

// High replication lag
// - Check network
// - Check disk I/O
// - Check oplog size

// Chunk migration stuck
// - Check network
// - Check shard memory
// - Check chunk size
```

---

*Questo documento fa parte del modulo 05 "NoSQL MongoDB" della Data Encyclopedia.*