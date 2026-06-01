# Neo4j — Best Practices e Anti-Pattern

## Best Practices per la Modellazione

### 1. Guidare il Modello dalle Query

Prima di definire nodi, relazioni e proprietà, rispondere a: "Quali domande deve rispondere questo grafo?"

```cypher
// Query di esempio che guidano il modello:
// "Chi sono gli esperti di Python nel team Milano?"
// "Quali progetti potrebbero essere ritardati per mancanza di skill?"
// "Chi conosce sia Alice che Bob?"

// Il modello deve permettere queste query in modo efficiente
// SENZA richiedere scan completi del grafo
```

### 2. Indici su Proprietà di Lookup Frequente

```cypher
// Ogni volta che usi MATCH con WHERE p.email = "...", ci vuole un indice
CREATE INDEX person_email FOR (p:Person) ON (p.email);
CREATE INDEX person_id FOR (p:Person) ON (p.id);
CREATE INDEX event_timestamp FOR (e:Event) ON (e.timestamp);

// Verifica indici usati
EXPLAIN MATCH (p:Person {email: "alice@example.com"}) RETURN p;
// Deve mostrare NodeIndexSeek, non NodeByLabelScan
```

### 3. MERGE Idempotente con Constraint

```cypher
// Prima: constraint per garantire unicità
CREATE CONSTRAINT person_email_unique FOR (p:Person) REQUIRE p.email IS UNIQUE;

// Poi: MERGE idempotente
MERGE (p:Person {email: $email})
ON CREATE SET p.name = $name, p.created_at = datetime()
ON MATCH SET p.last_seen = datetime();
// Mai CREATE se c'è rischio di duplicati
```

### 4. Evitare Super-Nodi

```cypher
// PROBLEMA: Country con 10M relazioni LIVES_IN
(:Person)-[:LIVES_IN]->(:Country {code: "IT"})

// SOLUZIONE A: proprietà invece di relazione
(:Person {country: "IT"})  -- query: WHERE p.country = "IT"

// SOLUZIONE B: intermediario per bilanciare il fan-out
(:Person)-[:LIVES_IN]->(:City {name: "Milano"})-[:IN_COUNTRY]->(:Country)
// Query sulla città: pochi nodi. Query sul paese: traversal a 2 hop ma fan-out ridotto per city
```

---

## Anti-Pattern da Evitare

### Anti-Pattern 1: Label Generico con Proprietà Type

```cypher
// SBAGLIATO: tipo di entità come proprietà
(:Entity {type: "Person", name: "Alice"})
(:Entity {type: "Company", name: "TechCorp"})

// CORRETTO: label semantico
(:Person {name: "Alice"})
(:Company {name: "TechCorp"})
// Il label è indicizzato nativamente, la proprietà type no
```

### Anti-Pattern 2: Relazioni con Nome Troppo Generico

```cypher
// SBAGLIATO: tipo di relazione in una proprietà
(:Person)-[:RELATED_TO {relationship: "works_for"}]->(:Company)

// CORRETTO: tipo specifico
(:Person)-[:WORKS_FOR]->(:Company)
// Il pattern matching su tipo è O(1), su proprietà è O(degree)
```

### Anti-Pattern 3: Variable-Length Senza Limite

```cypher
// SBAGLIATO: può esplorare l'intero grafo
MATCH (a)-[:KNOWS*]->(b) WHERE b.name = "Bob" RETURN a;

// CORRETTO: limite ragionevole
MATCH (a)-[:KNOWS*1..6]->(b) WHERE b.name = "Bob" RETURN a;
```

### Anti-Pattern 4: Cartesian Product Accidentale

```cypher
// SBAGLIATO: due MATCH separati = prodotto cartesiano
MATCH (a:Person {name: "Alice"})
MATCH (b:Person {name: "Bob"})
RETURN a, b;  -- O(n_alice * n_bob) se non ci sono filtri

// CORRETTO: combinare in un unico pattern quando c'è una relazione
MATCH (a:Person {name: "Alice"})-[:KNOWS]-(b:Person {name: "Bob"})
RETURN a, b;
```

### Anti-Pattern 5: Nodo con Troppe Proprietà

```cypher
// SBAGLIATO: tutto in un nodo
(:Person {
    name: ..., email: ..., age: ...,
    address_street: ..., address_city: ..., address_country: ...,
    company_name: ..., company_role: ..., company_since: ...,
    skill_1: ..., skill_2: ..., skill_3: ...
})

// CORRETTO: modella come grafo
(:Person {name: ..., email: ..., age: ...})
    -[:LIVES_AT]->(:Address {street: ..., city: ..., country: ...})
(:Person)-[:WORKS_AT {role: ..., since: ...}]->(:Company {name: ...})
(:Person)-[:HAS_SKILL]->(:Skill {name: ...})
```

---

## Performance Tuning

### Page Cache

```properties
# Regola: abbastanza page cache per contenere il "working set" frequente
# Working set = nodi e relazioni più acceduti
server.memory.pagecache.size=16g   # 50% della RAM disponibile

# Heap per query in memoria
server.memory.heap.initial_size=4g
server.memory.heap.max_size=8g     # max 16-32 GB, oltre non aiuta
```

### Query Optimization

```cypher
// Inizia sempre dal nodo più selettivo (indice)
// SBAGLIATO: inizia da un label ampio
MATCH (a:Person)-[:KNOWS]->(b:Person {email: "alice@example.com"})
RETURN a.name;  -- scansiona tutti i Person, poi filtra su email

// CORRETTO: inizia dall'entità con l'indice
MATCH (b:Person {email: "alice@example.com"})<-[:KNOWS]-(a:Person)
RETURN a.name;  -- usa l'indice su email, poi traversa

// Usa LIMIT presto nella pipeline
MATCH (p:Person)-[:KNOWS]->(friend)
WITH p, count(friend) AS friends
ORDER BY friends DESC
LIMIT 10  -- limita PRIMA di fare altri match
MATCH (p)-[:WORKS_AT]->(company)
RETURN p.name, friends, company.name;
```

### Profiling e Slow Query Log

```cypher
// Profilazione esplicita
PROFILE MATCH (p:Person {email: "alice@example.com"})-[:KNOWS*1..3]->(friend)
RETURN DISTINCT friend.name;
// Controlla: db hits per operatore, rows prodotte, tempo

// EXPLAIN per vedere il piano senza eseguire
EXPLAIN MATCH (p:Person {name: "Alice"})-[:KNOWS]->(f)
RETURN f.name;
```

---

## Checklist pre-Produzione

### Modello

- [ ] Constraint di unicità su tutte le chiavi di business
- [ ] Indici su proprietà usate nelle clausole WHERE
- [ ] Nessun super-nodo (degree > 100k) senza strategia di mitigazione
- [ ] Tipi di relazione specifici, non generici
- [ ] Schema documentato con esempi di query target

### Performance

- [ ] `server.memory.pagecache.size` ≥ 50% RAM disponibile
- [ ] Query lente identificate con slow query log
- [ ] EXPLAIN su query critiche: nessun `NodeByLabelScan` non necessario
- [ ] Nessun `MATCH ()-[:REL*]->()` senza limite di profondità

### Operativo

- [ ] Backup giornaliero con `neo4j-admin database backup`
- [ ] Cluster con ≥3 Core Members per tolleranza ai failure
- [ ] Security log abilitato
- [ ] Utenti con ruoli minimi necessari
- [ ] APOC installato per import/export e operazioni batch

### Sviluppo

- [ ] Nessun `DETACH DELETE` su label con molti nodi senza batch
- [ ] `apoc.periodic.iterate` per operazioni su milioni di nodi
- [ ] Parametri Cypher invece di interpolazione stringhe
- [ ] Connection pool configurato nel driver (non creare driver per ogni richiesta)

Neo4j eccelle quando il modello abbraccia la natura a grafo dei dati — connessioni ricche, traversal a profondità variabile, pattern matching su strutture complesse. La performance degrada quando si tenta di usarlo come database relazionale con JOIN.

---

## Data Loading Best Practices

### Bulk Import Strategy

```bash
# For initial load (millions of nodes): use neo4j-admin import
# Database MUST be offline
neo4j stop

neo4j-admin database import full \
    --database=neo4j \
    --nodes=Person="person_header.csv,person_data_*.csv" \
    --nodes=Company="company_header.csv,company_data.csv" \
    --relationships=KNOWS="knows_header.csv,knows_data_*.csv" \
    --relationships=WORKS_AT="works_header.csv,works_data.csv" \
    --skip-bad-relationships=true \
    --skip-duplicate-nodes=true \
    --high-io=true \
    --threads=$(nproc)

neo4j start
```

### Incremental Load via Cypher

```cypher
// UNWIND batch pattern — 10-50x faster than individual statements
:param batch => [{name: "Alice", email: "alice@ex.com"}, {name: "Bob", email: "bob@ex.com"}, ...]

UNWIND $batch AS row
MERGE (p:Person {email: row.email})
ON CREATE SET p.name = row.name, p.created = datetime()
ON MATCH SET p.last_seen = datetime();

// For relationships — always MATCH endpoints first, then MERGE relationship
UNWIND $rels AS rel
MATCH (a:Person {email: rel.from_email})
MATCH (b:Person {email: rel.to_email})
MERGE (a)-[:KNOWS {since: date(rel.since)}]->(b);
```

### Load Performance Tips

| Technique | Impact | When to Use |
|-----------|--------|-------------|
| UNWIND batch | 10-50x speedup | Any multi-row insert |
| Constraint before MERGE | 100x speedup | Always |
| USING PERIODIC COMMIT (LOAD CSV) | Prevents OOM | CSV > 100K rows |
| neo4j-admin import | Fastest possible | Initial load, DB offline OK |
| apoc.periodic.iterate | Batched online | Millions of updates |
| Disable indexes during load, recreate after | 2-3x faster | Large bulk loads |

---

## Transaction Design

### Keep Transactions Small

```cypher
// WRONG: one massive transaction
LOAD CSV WITH HEADERS FROM 'file:///big.csv' AS row
CREATE (p:Person) SET p = row;
// This loads everything in one transaction — OOM if file is large

// CORRECT: auto-commit with CALL IN TRANSACTIONS (Neo4j 5+)
LOAD CSV WITH HEADERS FROM 'file:///big.csv' AS row
CALL {
    WITH row
    CREATE (p:Person) SET p = row
} IN TRANSACTIONS OF 5000 ROWS;
```

### Read vs Write Transaction Separation

```python
# Use explicit read/write modes — driver routes appropriately in cluster
with driver.session(database="neo4j") as session:
    # Read: routed to any replica
    result = session.execute_read(lambda tx: tx.run(
        "MATCH (p:Person {name: $name}) RETURN p", name="Alice"
    ).single())

    # Write: always routed to leader
    session.execute_write(lambda tx: tx.run(
        "MATCH (p:Person {name: $name}) SET p.last_seen = datetime()", name="Alice"
    ))
```

---

## Schema Design Patterns

### Hyperedge Pattern

When a relationship involves more than two participants:

```cypher
// Example: a meeting involves multiple people, a room, and a time
// Cannot model as a simple relationship between two nodes

// Solution: reify the event as a node
CREATE (m:Meeting {
    id: "MTG-001",
    title: "Sprint Planning",
    start: datetime("2024-01-15T10:00:00"),
    duration: duration("PT1H")
})
CREATE (m)<-[:ATTENDS {role: "facilitator"}]-(alice:Person {name: "Alice"})
CREATE (m)<-[:ATTENDS {role: "participant"}]-(bob:Person {name: "Bob"})
CREATE (m)-[:IN_ROOM]->(r:Room {name: "Conf-A"})
CREATE (m)-[:ON_TOPIC]->(t:Topic {name: "Q1 Roadmap"});
```

### Singleton Pattern for Configuration

```cypher
// Global configuration node
MERGE (config:AppConfig {key: "global"})
SET config.max_retries = 3,
    config.timeout_ms = 5000,
    config.feature_flags = ["dark_mode", "new_ui"];

// Read config
MATCH (config:AppConfig {key: "global"})
RETURN config.max_retries, config.timeout_ms;
```

### Linked List for Ordered Data

```cypher
// Create ordered chain
CREATE (h:ListHead {name: "task_queue"})
CREATE (t1:Task {name: "Task A", priority: 1})
CREATE (t2:Task {name: "Task B", priority: 2})
CREATE (t3:Task {name: "Task C", priority: 3})
CREATE (h)-[:FIRST]->(t1)-[:NEXT]->(t2)-[:NEXT]->(t3);

// Insert into middle of chain
MATCH (prev:Task {name: "Task A"})-[old:NEXT]->(next:Task)
CREATE (new:Task {name: "Task A.5", priority: 1.5})
CREATE (prev)-[:NEXT]->(new)
CREATE (new)-[:NEXT]->(next)
DELETE old;

// Traverse in order
MATCH (h:ListHead {name: "task_queue"})-[:FIRST]->(first:Task)
MATCH path = (first)-[:NEXT*0..]->(task:Task)
RETURN [n IN nodes(path) | n.name] AS ordered_tasks;
```

---

## Memory Tuning Deep Dive

### Memory Architecture

```
┌────────────────────────────────────────────────┐
│                System RAM                       │
│                                                │
│  ┌──────────────┐  ┌─────────────────────────┐ │
│  │   JVM Heap   │  │     Page Cache           │ │
│  │   (queries,  │  │  (store files,           │ │
│  │   transactions│  │   graph data,            │ │
│  │   GC)        │  │   indexes)               │ │
│  │   4-16 GB    │  │   50%+ of RAM            │ │
│  └──────────────┘  └─────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐  │
│  │           OS File System Cache            │  │
│  │        (remaining RAM, managed by OS)     │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

### Sizing Guidelines

```properties
# Step 1: Calculate store size
# Run: neo4j-admin database info --database=neo4j
# Note: totalStoreSize

# Step 2: Page cache = max(totalStoreSize, 50% of RAM)
# If store fits entirely in page cache, all reads are from memory
server.memory.pagecache.size=16g

# Step 3: Heap = 4-16 GB (rarely need more)
# Small heap = frequent GC but short pauses
# Large heap = infrequent GC but longer pauses
server.memory.heap.initial_size=8g
server.memory.heap.max_size=8g  # set initial = max to avoid resizing

# Step 4: Leave 1-2 GB for OS
# Total: page_cache + heap + OS ≤ total RAM

# Step 5: Use neo4j-admin recommendation
neo4j-admin server memory-recommendation --database=neo4j --memory=64g
```

### JVM Garbage Collection Tuning

```properties
# neo4j.conf — GC tuning
server.jvm.additional=-XX:+UseG1GC
server.jvm.additional=-XX:MaxGCPauseMillis=200
server.jvm.additional=-XX:G1HeapRegionSize=16m
server.jvm.additional=-XX:+ParallelRefProcEnabled
server.jvm.additional=-XX:InitiatingHeapOccupancyPercent=45

# GC logging for diagnostics
server.jvm.additional=-Xlog:gc*,gc+ref=debug,gc+phases=debug:file=/var/log/neo4j/gc.log:time,pid,tags:filecount=5,filesize=50m
```

---

## Query Optimization Patterns

### Use PROFILE Not EXPLAIN

```cypher
// EXPLAIN shows plan but does not execute — does not reveal actual row counts
EXPLAIN MATCH (p:Person {name: "Alice"})-[:KNOWS]->(f) RETURN f;

// PROFILE executes and shows actual stats — use this for real optimization
PROFILE MATCH (p:Person {name: "Alice"})-[:KNOWS]->(f) RETURN f;
// Check: db hits, rows, estimated vs actual, operator type
```

### Key Operators to Watch

| Operator | Meaning | Concern |
|----------|---------|---------|
| NodeByLabelScan | Scans ALL nodes with label | Add index on filtered property |
| AllNodesScan | Scans EVERY node in DB | Add label and/or index |
| CartesianProduct | Cross join of two patterns | Ensure patterns are connected |
| Eager | Materializes full result in memory | Can cause OOM on large results |
| Filter | Post-scan filtering | Move filter to index |

### Composable Index Patterns

```cypher
// Range index (default, B-tree) — equality, range, prefix, existence
CREATE INDEX FOR (p:Person) ON (p.email);
CREATE INDEX FOR (p:Person) ON (p.age);

// Composite index — multi-property queries
CREATE INDEX FOR (p:Person) ON (p.country, p.city);
// Used for: WHERE p.country = "IT" AND p.city = "Milano"
// Also used for: WHERE p.country = "IT" (prefix)
// NOT used for: WHERE p.city = "Milano" (non-prefix)

// Full-text index — text search with Lucene
CREATE FULLTEXT INDEX person_ft FOR (p:Person) ON EACH [p.name, p.bio];
CALL db.index.fulltext.queryNodes("person_ft", "Alice engineer") YIELD node, score;

// Point index — geospatial queries
CREATE POINT INDEX FOR (p:Person) ON (p.location);
MATCH (p:Person) WHERE point.distance(p.location, point({latitude: 45.46, longitude: 9.19})) < 10000
RETURN p.name;

// Vector index (Neo4j 5.11+) — similarity search
CREATE VECTOR INDEX person_embedding FOR (p:Person) ON (p.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 128, `vector.similarity_function`: 'cosine'}};
```

---

## Naming Conventions

### Labels

```
PascalCase, singular noun:
Person, Company, Project, AuditLog, CacheEntry

Multi-word: PascalCase without underscore:
FinancialTransaction, UserSession, AccessPolicy

Avoid: lowercase, plural, abbreviations
NO: person, People, Persons, fin_txn, usr
```

### Relationship Types

```
UPPER_SNAKE_CASE, verb or verb phrase:
KNOWS, WORKS_AT, HAS_SKILL, DEPENDS_ON, REPORTED_BY

Direction should read naturally left-to-right:
(:Person)-[:WORKS_AT]->(:Company)   ✓
(:Company)-[:EMPLOYS]->(:Person)    ✓ (both valid, choose based on query patterns)

Avoid: CamelCase, generic names
NO: worksAt, RelatedTo, LINK, CONNECTION
```

### Properties

```
camelCase:
name, email, createdAt, lastModified, isActive, phoneNumber

Avoid: snake_case in properties (Neo4j convention is camelCase)
Avoid: abbreviated or ambiguous names
NO: nm, eml, ts, flg
```

---

## Troubleshooting

### 1. Database Starts but Immediately Stops

**Symptom**: neo4j start succeeds but process exits after seconds.

**Fix**: Check logs for OOM or port conflict:
```bash
tail -100 /var/log/neo4j/neo4j.log
# Common causes:
# - Heap size exceeds available RAM
# - Page cache + heap > system RAM
# - Port 7687 or 7474 already in use
ss -tlnp | grep -E '7687|7474'
```

### 2. Page Cache Hit Ratio Below 95%

**Symptom**: Queries slow, high disk I/O.

**Fix**: Increase page cache or identify the hot working set:
```cypher
// Check page cache metrics
CALL dbms.queryJmx("org.neo4j:instance=kernel#0,name=Page cache")
YIELD name, attributes
RETURN name, attributes;
```

### 3. "Transaction has been terminated" Error

**Symptom**: Long-running query killed mid-execution.

**Root cause**: Transaction timeout exceeded.

**Fix**:
```properties
# neo4j.conf — increase timeout for analytics queries
db.transaction.timeout=300s  # default 0 (no timeout)
# Or per-query in the driver:
session.run("MATCH ...", timeout=120)
```

### 4. MERGE Creates Duplicates Despite Constraint

**Symptom**: Duplicate nodes created in concurrent writes.

**Root cause**: Constraint not created, or MERGE property does not match constraint property.

**Fix**:
```cypher
// Verify constraint exists
SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties;
// Ensure MERGE uses the exact constrained property
MERGE (p:Person {email: $email})  // email MUST be the constrained property
```

### 5. Eager Operator Causing OOM

**Symptom**: Query fails with OutOfMemoryError, PROFILE shows Eager operator.

**Fix**: Rewrite query to avoid Eager. Common triggers: ORDER BY after MATCH without LIMIT, UNWIND + CREATE in same query:
```cypher
// PROBLEMATIC: Eager triggered
MATCH (p:Person)
CREATE (p)-[:CHECKED_AT]->(t:Timestamp {time: datetime()})

// FIX: Use CALL {} IN TRANSACTIONS
MATCH (p:Person)
CALL {
    WITH p
    CREATE (p)-[:CHECKED_AT]->(t:Timestamp {time: datetime()})
} IN TRANSACTIONS OF 5000 ROWS;
```

### 6. Index Not Used Despite Existing

**Symptom**: PROFILE shows NodeByLabelScan even though index exists.

**Fix**: Check if the property value in WHERE clause matches the indexed property exactly. Type mismatch (string vs integer) bypasses index:
```cypher
// Index on (p:Person).id where id is INTEGER
// WRONG: string comparison — index not used
MATCH (p:Person) WHERE p.id = "123" RETURN p;
// CORRECT: integer comparison — index used
MATCH (p:Person) WHERE p.id = 123 RETURN p;
```

### 7. LOAD CSV Fails on Large Files

**Symptom**: OOM or timeout with CSV over 1M rows.

**Fix**: Use `CALL {} IN TRANSACTIONS`:
```cypher
LOAD CSV WITH HEADERS FROM 'file:///large.csv' AS row
CALL {
    WITH row
    MERGE (p:Person {id: toInteger(row.id)})
    SET p.name = row.name
} IN TRANSACTIONS OF 10000 ROWS;
```

### 8. Property Value Too Large

**Symptom**: Error when storing very long string or large array.

**Fix**: Neo4j supports properties up to ~2GB but performance degrades. Store large content externally and reference by URL/ID:
```cypher
// Instead of storing document content
// CREATE (d:Document {content: "... 10MB text ..."})
// Store a reference
CREATE (d:Document {content_url: "s3://bucket/doc-001.txt", size_bytes: 10485760})
```

### 9. Hot Backup Takes Too Long

**Symptom**: Backup duration exceeds maintenance window.

**Fix**: Use incremental backups and run backup from a read replica:
```bash
# Run backup from read replica to avoid impacting leader
neo4j-admin database backup \
    --from=read-replica-host:6362 \
    --database=neo4j \
    --to-path=/backup/
```

### 10. Migration Between Neo4j Versions Fails

**Symptom**: Database does not start after version upgrade.

**Fix**: Run migration tool before starting:
```bash
neo4j-admin database migrate --database=neo4j
# Then start normally
neo4j start
```

---

## FAQ

### 1. What is the difference between CREATE and MERGE?

CREATE always creates a new node/relationship. MERGE finds an existing match or creates if not found. Always use MERGE with a unique constraint to prevent duplicates. CREATE is only safe when you are certain the entity does not exist.

### 2. When should I use relationship properties vs intermediate nodes?

Use relationship properties for 1-3 simple attributes (weight, since, role). Use intermediate nodes when the "relationship" has its own identity, many properties, or relationships to other entities (e.g., an Order between Buyer and Product).

### 3. How often should I rebuild indexes?

Neo4j indexes are maintained automatically. No manual rebuild needed. However, after large bulk imports (neo4j-admin import), indexes are created during the import process. For LOAD CSV imports, create indexes before the import for MERGE performance.

### 4. What is the ideal number of labels per node?

1-3 labels. One primary type label (Person, Company) and optionally 1-2 secondary labels for role, state, or access control (Active, PII, Archived). More than 3 labels increases query planning complexity without proportional benefit.

### 5. Should I normalize or denormalize in a graph?

Graphs are already "normalized" by nature — entities are nodes, relationships are explicit. Denormalize (add redundant properties) only when queries need it and the data rarely changes. Example: storing `company_name` on Person to avoid a traversal in a very hot path.

### 6. How do I handle time zones in temporal properties?

Use `ZONED DATETIME` for absolute timestamps (event occurred at this UTC moment) and `LOCAL DATETIME` for business time (appointment is at 10:00 local time). Store timezone-aware values whenever the temporal context matters.

### 7. What is the cost of adding a new index?

Index creation on an existing database with data triggers a background population phase. During this phase, writes to the indexed property may be slightly slower. On a database with 100M nodes, index population takes seconds to minutes. No downtime required.

### 8. How do I monitor slow queries in production?

Enable the query log:
```properties
db.logs.query.enabled=INFO
db.logs.query.threshold=1000ms  # log queries slower than 1s
```
Parse the log with ELK/Splunk to identify patterns. Use `PROFILE` on the worst offenders to find optimization opportunities.

### 9. Can I use Neo4j for OLAP workloads?

Neo4j is primarily OLTP (low-latency transactional queries). For OLAP (bulk analytics over the full graph), use GDS projections which operate in memory. For very large analytical workloads, consider exporting graph data to Spark/Presto or using Neo4j Fabric for federated queries.

### 10. What is the recommended backup strategy?

Daily full backup + continuous transaction log archiving. Test restores monthly. For critical systems: backup from a dedicated read replica to avoid impacting the leader, with automated verification that the backup is restorable.

Neo4j performs best when the data model embraces graph-native patterns — rich connections, variable-depth traversals, and pattern matching on complex structures. Performance degrades when graph databases are treated as relational databases with JOINs. Design the model from the queries, not from the tables.

---

## Operational Practices

### Monitoring Checklist (Production)

```bash
# Key metrics to track continuously:

# 1. Page cache hit ratio (target: >98%)
curl -s http://localhost:2004/metrics | grep page_cache_hits

# 2. Transaction throughput (commits/sec)
curl -s http://localhost:2004/metrics | grep transaction_committed

# 3. Active transactions (detect leaks)
curl -s http://localhost:2004/metrics | grep transaction_active

# 4. Bolt connection pool usage
curl -s http://localhost:2004/metrics | grep bolt_connections

# 5. JVM heap usage and GC pause time
curl -s http://localhost:2004/metrics | grep jvm_gc

# 6. Store file sizes (detect unexpected growth)
neo4j-admin database info --database=neo4j

# 7. Disk IOPS and latency
iostat -xz 5 | grep -E 'sda|nvme'
```

### Capacity Planning Formula

```
Required RAM = page_cache + heap + OS_overhead
  page_cache  = totalStoreSize * 1.1  (10% buffer for growth)
  heap        = min(16 GB, concurrent_queries * avg_query_memory)
  OS_overhead = 2 GB

Required Disk = totalStoreSize * 3  (data + tx logs + backups)
  Use NVMe SSD for production

Required Cores = max(4, concurrent_queries / 10)
  Neo4j is I/O bound more than CPU bound
  GDS algorithms are CPU-intensive — add cores for analytics
```

### Automated Health Check Script

```bash
#!/bin/bash
# neo4j-healthcheck.sh
HOST="localhost:7474"
USER="neo4j"
PASS="$NEO4J_PASSWORD"

# Check HTTP endpoint
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$HOST")
if [ "$HTTP_STATUS" != "200" ]; then
    echo "CRITICAL: Neo4j HTTP endpoint returned $HTTP_STATUS"
    exit 2
fi

# Check database status
DB_STATUS=$(cypher-shell -u "$USER" -p "$PASS" --format plain \
    "SHOW DATABASE neo4j YIELD currentStatus RETURN currentStatus" 2>/dev/null | tail -1)
if [ "$DB_STATUS" != "online" ]; then
    echo "CRITICAL: Database status is $DB_STATUS"
    exit 2
fi

# Check slow queries (any query running > 60s)
SLOW=$(cypher-shell -u "$USER" -p "$PASS" --format plain \
    "SHOW TRANSACTIONS YIELD elapsedTime, currentQuery
     WHERE elapsedTime > duration('PT60S')
     RETURN count(*) AS slow_count" 2>/dev/null | tail -1)
if [ "$SLOW" -gt 0 ]; then
    echo "WARNING: $SLOW queries running longer than 60 seconds"
    exit 1
fi

echo "OK: Neo4j healthy"
exit 0
```

### Log Rotation and Retention

```properties
# neo4j.conf
db.logs.query.rotation.size=100m
db.logs.query.rotation.keep_number=10

dbms.logs.security.rotation.size=50m
dbms.logs.security.rotation.keep_number=30

server.logs.gc.rotation.size=50m
server.logs.gc.rotation.keep_number=5
```

---

## Additional Troubleshooting

### 11. Thread Deadlock in Concurrent Writes

**Symptom**: Multiple transactions hang, neo4j.log shows deadlock detection.

**Fix**: Order lock acquisition consistently. When writing to multiple nodes, always acquire locks in a deterministic order (e.g., by node ID):
```cypher
MATCH (a:Account {id: $fromId}), (b:Account {id: $toId})
// Order by ID to prevent deadlock
WITH a, b ORDER BY id(a)
SET a.balance = a.balance - $amount
SET b.balance = b.balance + $amount;
```

### 12. Schema Introspection Returns Empty

**Symptom**: `CALL db.schema.visualization()` returns empty graph.

**Root cause**: No data in the database, or user lacks read permissions.

**Fix**: Schema visualization requires actual data to infer the schema. Use `CALL apoc.meta.schema()` as an alternative that works with any dataset.

