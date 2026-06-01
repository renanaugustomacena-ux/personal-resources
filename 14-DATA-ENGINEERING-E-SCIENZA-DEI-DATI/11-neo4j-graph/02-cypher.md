# Neo4j — Cypher Query Language

## Fondamenti di Cypher

Cypher è il linguaggio dichiarativo di Neo4j per interrogare e manipolare grafi. La sua sintassi usa pattern ASCII-art per rappresentare nodi e relazioni, rendendo le query leggibili anche da chi non conosce il linguaggio.

### Sintassi di Base

```cypher
// Nodo: parentesi tonde con label e proprietà
(n:Person {name: "Alice", age: 30})

// Relazione: frecce con parentesi quadre per il tipo
(a)-[:KNOWS]->(b)                     // relazione diretta a → b
(a)-[:KNOWS]-(b)                      // relazione non diretta
(a)-[r:KNOWS {since: date("2020-01-01")}]->(b)  // con proprietà sulla relazione
(a)-[:KNOWS|FOLLOWS]->(b)             // tipo OR: KNOWS o FOLLOWS

// Pattern di lunghezza variabile
(a)-[:KNOWS*1..3]->(b)                // tra 1 e 3 hop di KNOWS
(a)-[:KNOWS*]->(b)                    // qualsiasi numero di hop (costoso!)
```

---

## MATCH: Pattern Matching

```cypher
// Trova tutte le persone
MATCH (p:Person)
RETURN p.name, p.age
ORDER BY p.age DESC
LIMIT 10;

// Trova le amicizie
MATCH (a:Person)-[:KNOWS]->(b:Person)
RETURN a.name AS person, b.name AS friend;

// Pattern più complesso: amici di amici (escludendo se stesso)
MATCH (me:Person {name: "Alice"})-[:KNOWS*2..2]-(fof:Person)
WHERE NOT (me)-[:KNOWS]-(fof) AND fof <> me
RETURN DISTINCT fof.name, fof.age
ORDER BY fof.name;

// Percorso completo
MATCH path = (a:Person {name: "Alice"})-[:KNOWS*1..4]-(b:Person {name: "Bob"})
RETURN path, length(path) as hops
ORDER BY hops
LIMIT 1;

// OPTIONAL MATCH: come LEFT JOIN
MATCH (p:Person)
OPTIONAL MATCH (p)-[:OWNS]->(c:Company)
RETURN p.name, c.name AS company  -- c.name = null se non ha azienda
```

---

## WHERE: Filtri

```cypher
// Filtri su proprietà
MATCH (p:Person)
WHERE p.age >= 25 AND p.age <= 40
  AND p.country IN ["IT", "DE", "FR"]
  AND p.name STARTS WITH "M"
  AND p.email IS NOT NULL
RETURN p;

// Filtri su relazioni e nodi connessi
MATCH (p:Person)
WHERE EXISTS {
    MATCH (p)-[:KNOWS]->(friend:Person)
    WHERE friend.age > 30
}
RETURN p.name;

// Pattern predicato (da Neo4j 4.x)
MATCH (p:Person)
WHERE (p)-[:WORKS_AT]->(:Company {industry: "Tech"})
  AND NOT (p)-[:BLOCKED]->()
RETURN p.name;
```

---

## CREATE, MERGE, SET, DELETE

### CREATE: Creazione di Nodi e Relazioni

```cypher
// Crea un nodo
CREATE (p:Person {name: "Carlo", age: 35, country: "IT"})
RETURN p;

// Crea una relazione tra nodi esistenti
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
CREATE (a)-[:KNOWS {since: date()}]->(b);

// Crea un pattern completo
CREATE (alice:Person {name: "Alice"})-[:KNOWS {since: date("2020-01-01")}]->(bob:Person {name: "Bob"})
-[:WORKS_AT {role: "Dev"}]->(company:Company {name: "TechCorp"});
```

### MERGE: Upsert su Grafo

MERGE controlla se il pattern esiste; se non esiste, lo crea. È fondamentale per importazioni idempotenti.

```cypher
// MERGE con ON CREATE e ON MATCH
MERGE (p:Person {email: "alice@example.com"})
ON CREATE SET
    p.name = "Alice",
    p.age = 30,
    p.created_at = datetime()
ON MATCH SET
    p.last_seen = datetime();

// MERGE su relazione (richiede di specificare i nodi prima)
MERGE (a:Person {id: 1})
MERGE (b:Person {id: 2})
MERGE (a)-[r:KNOWS]->(b)
ON CREATE SET r.since = date(), r.weight = 1.0
ON MATCH SET r.weight = r.weight + 0.1;
```

**Attenzione**: MERGE su nodi senza property constraints può creare duplicati. Sempre aggiungere un indice/constraint sull'identità prima.

### SET e REMOVE: Aggiornamento Proprietà

```cypher
// Aggiorna proprietà
MATCH (p:Person {name: "Alice"})
SET p.age = 31,
    p.updated_at = datetime(),
    p += {country: "IT", verified: true}  // += mergia senza cancellare proprietà esistenti
RETURN p;

// Aggiunge un label
MATCH (p:Person {name: "Alice"})
SET p:Employee  -- aggiunge il label Employee mantenendo Person

// Rimuove una proprietà
MATCH (p:Person {name: "Alice"})
REMOVE p.verified;

// Rimuove un label
MATCH (p:Person:Employee {name: "Alice"})
REMOVE p:Employee;
```

### DELETE e DETACH DELETE

```cypher
// DELETE: elimina nodo solo se non ha relazioni
MATCH (p:Person {name: "Carlo"})
DELETE p;

// DETACH DELETE: elimina nodo e tutte le sue relazioni
MATCH (p:Person {name: "Carlo"})
DETACH DELETE p;

// Elimina solo la relazione
MATCH (a:Person {name: "Alice"})-[r:KNOWS]->(b:Person {name: "Bob"})
DELETE r;
```

---

## Aggregazioni e Funzioni

```cypher
// Aggregazioni standard
MATCH (p:Person)-[:KNOWS]->(friend)
RETURN p.name,
       count(friend) AS friend_count,
       avg(friend.age) AS avg_friend_age,
       collect(friend.name) AS friends_list,
       min(friend.age) AS youngest_friend

ORDER BY friend_count DESC
LIMIT 10;

// Distinct
MATCH (p:Person)-[:KNOWS]->(friend)
RETURN count(DISTINCT friend) AS unique_friends_total;

// Filtro su aggregazione (HAVING equivalente)
MATCH (p:Person)-[:KNOWS]->(friend)
WITH p, count(friend) AS friends
WHERE friends > 5
RETURN p.name, friends;
```

### Funzioni di Stringa, Numeriche e Temporali

```cypher
RETURN
    toUpper("alice"),           -- "ALICE"
    toLower("ALICE"),           -- "alice"
    trim("  hello  "),          -- "hello"
    substring("hello", 0, 3),   -- "hel"
    split("a,b,c", ","),        -- ["a", "b", "c"]
    size("hello"),              -- 5
    replace("hello", "l", "r"), -- "herro"
    left("hello", 3),           -- "hel"
    right("hello", 3),          -- "llo"
    toString(42),               -- "42"
    toInteger("42"),            -- 42
    toFloat("3.14"),            -- 3.14
    abs(-5),                    -- 5
    ceil(3.2),                  -- 4.0
    floor(3.9),                 -- 3.0
    round(3.567, 2),            -- 3.57
    sqrt(16),                   -- 4.0
    date() - duration("P30D"),  -- data di 30 giorni fa
    datetime().epochMillis;     -- timestamp corrente ms
```

---

## WITH: Pipeline di Query

`WITH` permette di concatenare parti di query, passando risultati intermedi.

```cypher
// Multi-step: find, aggregate, filter, return
MATCH (p:Person)-[:KNOWS]->(friend:Person)
WITH p, count(friend) AS degree
WHERE degree > 3
WITH p, degree
ORDER BY degree DESC
LIMIT 5
MATCH (p)-[:WORKS_AT]->(company)
RETURN p.name, degree, company.name;
```

---

## UNWIND: Expand di Liste

```cypher
// Unwind espande una lista in righe separate
WITH [1, 2, 3, 4, 5] AS numbers
UNWIND numbers AS n
RETURN n * n AS squared;

// Pattern comune per import da lista di oggetti
WITH [
    {name: "Alice", age: 30},
    {name: "Bob", age: 25}
] AS people
UNWIND people AS person
MERGE (p:Person {name: person.name})
SET p.age = person.age;

// Con LOAD CSV
LOAD CSV WITH HEADERS FROM 'file:///users.csv' AS row
UNWIND split(row.tags, '|') AS tag
MERGE (t:Tag {name: tag})
MERGE (p:Person {id: toInteger(row.id)})
MERGE (p)-[:HAS_TAG]->(t);
```

---

## LOAD CSV: Importazione Dati

```cypher
// Import base da CSV locale
LOAD CSV WITH HEADERS FROM 'file:///people.csv' AS row
MERGE (p:Person {id: toInteger(row.id)})
SET p.name = row.name,
    p.age = toInteger(row.age),
    p.email = row.email;

// Import con batch (CALL IN TRANSACTIONS per file grandi)
LOAD CSV WITH HEADERS FROM 'file:///large_file.csv' AS row
CALL {
    WITH row
    MERGE (p:Person {id: toInteger(row.id)})
    SET p.name = row.name
} IN TRANSACTIONS OF 1000 ROWS;

// Import relazioni
LOAD CSV WITH HEADERS FROM 'file:///friendships.csv' AS row
MATCH (a:Person {id: toInteger(row.from_id)})
MATCH (b:Person {id: toInteger(row.to_id)})
MERGE (a)-[:KNOWS {since: date(row.since)}]->(b);
```

---

## Spiegazione delle Query: EXPLAIN e PROFILE

```cypher
// EXPLAIN: mostra il piano di esecuzione senza eseguire la query
EXPLAIN MATCH (p:Person {name: "Alice"})-[:KNOWS]->(friend)
RETURN friend.name;
-- Output: piano con operatori (NodeIndexSeek, Expand, Filter, etc.)

// PROFILE: esegue la query e mostra le statistiche reali
PROFILE MATCH (p:Person)-[:KNOWS*1..3]->(other:Person)
WHERE p.name = "Alice"
RETURN DISTINCT other.name;
-- Mostra: db hits, rows per operatore, elapsed time
```

**Operatori chiave nel piano di esecuzione**:

| Operatore | Significato |
|-----------|-------------|
| `NodeIndexSeek` | Usa un indice per trovare il nodo | 
| `NodeByLabelScan` | Scansiona tutti i nodi di un label (costoso) |
| `Expand(All)` | Segue tutte le relazioni di un tipo |
| `Filter` | Applica predicato WHERE |
| `VarLengthExpand` | Traversal a profondità variabile |
| `NodeHashJoin` | Join tramite hash su ID nodo |
| `EagerAggregation` | Aggregazione in memoria |

Un piano ottimale mostra `NodeIndexSeek` all'inizio, non `NodeByLabelScan`.

Cypher è il linguaggio più espressivo tra i query language per grafi, bilanciando leggibilità e potenza espressiva per pattern di attraversamento complessi.

---

## Subqueries: CALL {} and CALL IN TRANSACTIONS

### CALL {} Subquery (Neo4j 4.x+)

Subqueries allow composing complex queries from independent parts, each with its own scope.

```cypher
// Correlated subquery: for each person, find their top 3 friends by connection strength
MATCH (p:Person)
CALL {
    WITH p
    MATCH (p)-[r:KNOWS]->(friend:Person)
    RETURN friend, r.weight AS strength
    ORDER BY strength DESC
    LIMIT 3
}
RETURN p.name, friend.name, strength;

// UNION in subquery: combine different relationship types
MATCH (p:Person {name: "Alice"})
CALL {
    WITH p
    MATCH (p)-[:KNOWS]->(contact) RETURN contact, "friend" AS type
    UNION
    WITH p
    MATCH (p)-[:WORKS_WITH]->(contact) RETURN contact, "colleague" AS type
}
RETURN contact.name, type;

// EXISTS subquery for filtering (Neo4j 5.x)
MATCH (p:Person)
WHERE EXISTS {
    MATCH (p)-[:WORKS_AT]->(c:Company)
    WHERE c.industry = "Finance"
    AND (p)-[:HAS_SKILL]->(:Skill {name: "Python"})
}
RETURN p.name, p.email;

// COUNT subquery
MATCH (p:Person)
WHERE COUNT {
    MATCH (p)-[:KNOWS]->()
} > 10
RETURN p.name AS popular_person;
```

### CALL {} IN TRANSACTIONS: Batch Processing

For operations that affect millions of nodes, `CALL IN TRANSACTIONS` breaks the work into smaller transactions to avoid memory exhaustion.

```cypher
// Update millions of nodes in batches of 10,000
MATCH (p:Person)
WHERE p.status IS NULL
CALL {
    WITH p
    SET p.status = "active",
        p.updated_at = datetime()
} IN TRANSACTIONS OF 10000 ROWS;

// Delete old events in batches (avoids OOM)
MATCH (e:Event)
WHERE e.timestamp < datetime() - duration("P365D")
CALL {
    WITH e
    DETACH DELETE e
} IN TRANSACTIONS OF 5000 ROWS;

// Import and transform data in batches
LOAD CSV WITH HEADERS FROM 'file:///massive_import.csv' AS row
CALL {
    WITH row
    MERGE (p:Person {id: toInteger(row.id)})
    ON CREATE SET p.name = row.name, p.email = row.email
    WITH p, row
    MERGE (c:Company {name: row.company})
    MERGE (p)-[:WORKS_AT {since: date(row.start_date)}]->(c)
} IN TRANSACTIONS OF 2000 ROWS
RETURN count(*) AS imported;
```

---

## Pattern Comprehensions and List Comprehensions

```cypher
// Pattern comprehension: inline query that returns a list
MATCH (p:Person {name: "Alice"})
RETURN p.name,
    [(p)-[:KNOWS]->(friend) | friend.name] AS friend_names,
    [(p)-[:WORKS_AT]->(c) | c.name] AS companies,
    [(p)-[:HAS_SKILL]->(s) WHERE s.category = "Programming" | s.name] AS programming_skills;

// List comprehension with transformation
WITH ["Alice", "Bob", "Charlie", "Dave"] AS names
RETURN [name IN names WHERE size(name) > 3 | toUpper(name)] AS long_names;
-- Result: ["ALICE", "CHARLIE", "DAVE"]

// Nested pattern comprehension for hierarchical data
MATCH (dept:Department)
RETURN dept.name,
    [(dept)<-[:MEMBER_OF]-(emp:Employee) |
        {
            name: emp.name,
            skills: [(emp)-[:HAS_SKILL]->(s) | s.name]
        }
    ] AS team_members;
```

---

## Map Projections

```cypher
// Map projection: extract specific properties from nodes
MATCH (p:Person {name: "Alice"})-[:KNOWS]->(friend)
RETURN p {.name, .email, .age} AS person,
       friend {.name, .email, friendCount: size((friend)-[:KNOWS]->())} AS friend_info;

// Dynamic property access
MATCH (n)
WHERE labels(n) = ["Person"]
WITH n, keys(n) AS props
RETURN n.name, [prop IN props WHERE prop STARTS WITH "addr" | n[prop]] AS addresses;
```

---

## FOREACH: Side Effects in Lists

```cypher
// Set a property on all nodes in a path
MATCH path = (a:Person {name: "Alice"})-[:KNOWS*1..3]->(b:Person {name: "Dave"})
FOREACH (node IN nodes(path) | SET node.on_path = true);

// Create relationships from a list of pairs
WITH [{from: "Alice", to: "Bob"}, {from: "Bob", to: "Charlie"}] AS connections
FOREACH (conn IN connections |
    MERGE (a:Person {name: conn.from})
    MERGE (b:Person {name: conn.to})
    MERGE (a)-[:KNOWS]->(b)
);
```

---

## CASE Expressions

```cypher
// Simple CASE
MATCH (p:Person)
RETURN p.name,
    CASE p.country
        WHEN "IT" THEN "Italy"
        WHEN "DE" THEN "Germany"
        WHEN "FR" THEN "France"
        ELSE "Other"
    END AS country_name;

// Generic CASE with conditions
MATCH (p:Person)-[:KNOWS]->(friend)
WITH p, count(friend) AS friends
RETURN p.name,
    CASE
        WHEN friends >= 50 THEN "influencer"
        WHEN friends >= 20 THEN "connector"
        WHEN friends >= 5  THEN "social"
        ELSE "introvert"
    END AS social_tier,
    friends;
```

---

## Temporal Functions Deep Dive

```cypher
// Create temporal values
RETURN
    date("2026-01-15"),
    time("14:30:00+01:00"),
    localtime("14:30:00"),
    datetime("2026-01-15T14:30:00+01:00"),
    localdatetime("2026-01-15T14:30:00");

// Temporal arithmetic
RETURN
    date() + duration("P30D") AS thirty_days_later,
    datetime() - duration("PT2H30M") AS two_and_half_hours_ago,
    date("2026-12-31") - date("2026-01-01") AS days_in_2026;

// Duration components
WITH duration.between(date("2020-01-01"), date("2026-05-22")) AS d
RETURN d.years, d.months, d.days;

// Temporal truncation
RETURN
    date.truncate("month", date()) AS first_of_month,
    date.truncate("year", date()) AS first_of_year,
    datetime.truncate("hour", datetime()) AS start_of_hour;

// Filter by temporal range
MATCH (e:Event)
WHERE e.created_at >= datetime("2026-01-01T00:00:00Z")
  AND e.created_at <  datetime("2026-02-01T00:00:00Z")
RETURN e.type, count(*) AS count
ORDER BY count DESC;
```

---

## Index Hints and Query Tuning

```cypher
// Force use of a specific index (rarely needed, planner usually gets it right)
MATCH (p:Person)
USING INDEX p:Person(email)
WHERE p.email = "alice@example.com"
RETURN p;

// Force a label scan (override index when you know it's a bad choice)
MATCH (p:Person)
USING SCAN p:Person
WHERE p.age > 65
RETURN p.name, p.age;

// Join hint (force hash join instead of nested loop)
MATCH (a:Person)-[:KNOWS]->(b:Person)
USING JOIN ON b
WHERE a.country = "IT" AND b.country = "DE"
RETURN a.name, b.name;
```

---

## Troubleshooting Cypher Queries

### Problem 1: Query Hangs on Large Variable-Length Pattern

**Cause**: `MATCH (a)-[:KNOWS*]->(b)` without upper bound explores exponentially.

**Fix**: always add upper bound: `[:KNOWS*1..6]`.

### Problem 2: MERGE Creates Duplicates

**Cause**: MERGE without a constraint checks all properties. If any property differs, a new node is created.

**Fix**: MERGE on the identity property only, then SET other properties:
```cypher
MERGE (p:Person {email: $email})
ON CREATE SET p.name = $name, p.age = $age;
```

### Problem 3: LOAD CSV Runs Out of Memory

**Fix**: use `CALL {} IN TRANSACTIONS OF 1000 ROWS` to process in batches.

### Problem 4: Cartesian Product Warning

**Cause**: two unconnected MATCH clauses produce a cross join.

**Fix**: connect the patterns or use WITH to pipeline results.

### Problem 5: Query Returns Paths Instead of Distinct Nodes

**Fix**: wrap in `DISTINCT` or restructure to avoid path enumeration.

### Problem 6: "Type mismatch: expected Node but was String"

**Cause**: comparing a node to a property value instead of using dot notation.

**Fix**: use `n.name = "Alice"` not `n = "Alice"`.

### Problem 7: PROFILE Shows High db_hits on Expand(All)

**Cause**: traversing a super-node with millions of relationships.

**Fix**: filter by relationship type, add degree pre-check: `WHERE size((n)-[:TYPE]->()) < 1000`.

### Problem 8: Slow UNWIND on Large Lists

**Fix**: break list into smaller chunks with `apoc.coll.partition` or process in `CALL {} IN TRANSACTIONS`.

### Problem 9: Index Not Used Despite Existing Index

**Cause**: property comparison uses function (e.g., `toLower(p.name) = "alice"`).

**Fix**: store normalized values, or use case-insensitive fulltext index.

### Problem 10: "Variable `x` not defined" Error in WITH Pipeline

**Cause**: WITH only passes forward the columns explicitly listed.

**Fix**: include all needed variables in the WITH clause.

---

## FAQ

**Q1: What is the difference between `CREATE` and `MERGE`?**
A: `CREATE` always creates new nodes/relationships regardless of existing data. `MERGE` checks if the pattern exists first — if yes, it matches the existing data; if no, it creates. Use `MERGE` for idempotent imports.

**Q2: Can I use parameters in Cypher?**
A: Yes. Use `$paramName` syntax: `MATCH (p:Person {name: $name})`. Parameters prevent Cypher injection and enable query plan caching.

**Q3: How do I do a "GROUP BY" in Cypher?**
A: Cypher does implicit grouping: any non-aggregated column in RETURN becomes a grouping key. `RETURN p.country, count(*) AS total` groups by country.

**Q4: What is the difference between `=` and `=~` in WHERE?**
A: `=` is exact equality. `=~` is regex match: `WHERE p.email =~ '.*@example\\.com'`.

**Q5: How do I handle NULL values in Cypher?**
A: Cypher follows SQL's three-valued logic. Use `IS NULL`, `IS NOT NULL`, `COALESCE(expr, default)`. NULL comparisons return NULL (not false).

**Q6: Can I call stored procedures from Cypher?**
A: Yes. `CALL db.index.fulltext.queryNodes("idx", "search term") YIELD node, score`. Procedures are Java code registered in the Neo4j process.

**Q7: How do I paginate results?**
A: Use `ORDER BY ... SKIP $offset LIMIT $pageSize`. For deep pagination (SKIP > 10000), use cursor-based pagination with a WHERE clause on an indexed property.

**Q8: What is `WITH` vs `RETURN`?**
A: `WITH` passes data to the next query part (like a pipeline stage). `RETURN` terminates the query and sends results to the client. `WITH` enables filtering on aggregated values (equivalent to SQL's HAVING).

**Q9: How do I convert between data types?**
A: `toString(42)`, `toInteger("42")`, `toFloat("3.14")`, `toBoolean("true")`, `date("2026-01-15")`, `datetime()`.

**Q10: Can I write conditional logic (IF/ELSE) in Cypher?**
A: Use `CASE WHEN ... THEN ... ELSE ... END` expressions. For conditional execution of entire clauses, use `FOREACH` with `CASE` or `apoc.do.when()`.

Cypher is the most expressive graph query language available, balancing readability with traversal power for patterns ranging from simple lookups to complex multi-hop analytical queries.

---

## Advanced Pattern Matching Techniques

### Quantified Path Patterns (Neo4j 5.9+)

Quantified path patterns extend variable-length relationships to include inline filtering at each step.

```cypher
// Find paths where every intermediate node is active
MATCH (start:Person {name: "Alice"})
      (()-[:KNOWS]->(mid:Person WHERE mid.is_active = true)){1,5}
      (end:Person {name: "Bob"})
RETURN start, end;

// Shortest path with inline predicate on each node
MATCH p = SHORTEST 1 (a:City {name: "Milano"})-[:ROAD]->{1,10}(b:City {name: "Roma"})
RETURN p, length(p);
```

### Named Paths and Path Functions

```cypher
// Assign a path to a variable and extract components
MATCH path = (a:Person {name: "Alice"})-[:KNOWS*1..4]->(b:Person {name: "Dave"})
RETURN
    path,
    nodes(path) AS all_nodes,
    relationships(path) AS all_rels,
    length(path) AS hops,
    [n IN nodes(path) | n.name] AS names_on_path;

// Collect all paths and analyze them
MATCH path = allShortestPaths((a:Person {name: "Alice"})-[:KNOWS*]-(b:Person {name: "Eve"}))
WITH path, length(path) AS hops
RETURN hops, count(path) AS num_paths, collect([n IN nodes(path) | n.name]) AS paths;
```

### Multiple Relationship Types with Direction

```cypher
// Match any of several relationship types in either direction
MATCH (a:Person {name: "Alice"})-[r:KNOWS|FOLLOWS|WORKS_WITH]-(b:Person)
RETURN type(r) AS relationship_type, b.name
ORDER BY relationship_type, b.name;

// Directional mix within variable-length
MATCH path = (a:Person)-[:MANAGES|REPORTS_TO*1..5]->(ceo:Person)
WHERE NOT (ceo)-[:REPORTS_TO]->()
RETURN [n IN nodes(path) | n.name] AS chain;
```

---

## Cypher Execution Model: How Queries are Processed

Understanding how the Cypher planner works helps write faster queries.

```
Query String
    ↓
Parsing        → AST (Abstract Syntax Tree)
    ↓
Semantic Analysis → validate names, types, scope
    ↓
Planning       → generate candidate logical plans
    ↓
Cost Estimation → estimate cardinality × cost for each plan
    ↓
Selected Plan  → lowest estimated cost
    ↓
Execution      → volcano/pull model, pipelining
    ↓
Results        → stream to client
```

**Plan caching**: Cypher caches execution plans based on the query string template (with parameters abstracted). This is why parameterized queries (`$name` instead of `"Alice"`) are faster after the first execution — the plan is reused.

```properties
# neo4j.conf — planner cache settings
db.query_cache_size=1000         # number of cached plans
server.memory.query_cache.per_db_cache_num_entries=1000
```

### Inspecting Query Plans in Detail

```cypher
// EXPLAIN shows the plan without executing
EXPLAIN
MATCH (p:Person {email: "test@example.com"})-[:KNOWS*1..3]->(friend)
WHERE friend.country = "IT"
RETURN DISTINCT friend.name;

// Key plan operators to understand:
// NodeIndexSeek         → best: uses index, O(log n)
// NodeByLabelScan       → worst: full scan of all nodes with label
// DirectedAllRelsScan   → scans all relationships (expensive)
// Expand(All)           → follows all rels of a type from a node
// VarLengthExpand       → variable-length path exploration
// Filter                → applies WHERE predicate post-scan
// Distinct              → removes duplicates (hash-based)
// ProduceResults        → formats output for client
// EagerAggregation      → materializes all input before aggregating
// NodeHashJoin          → joins two pipelines by hashing node IDs

// PROFILE provides actual execution statistics
PROFILE
MATCH (p:Person {name: "Alice"})-[:KNOWS]->(friend)-[:WORKS_AT]->(company)
RETURN friend.name, company.name;
// Check: "Rows" (actual cardinality) vs "EstimatedRows" (planner estimate)
// Large gaps indicate stale statistics → run ANALYZE on the database
```

### Forcing Plan Re-evaluation

```cypher
// Clear the query cache (useful after major data changes)
CALL db.clearQueryCaches();

// Update statistics for better cost estimates
CALL db.stats.collect("GRAPH COUNTS");
```

---

## String Pattern Matching

```cypher
// STARTS WITH, ENDS WITH, CONTAINS (index-supported for STARTS WITH)
MATCH (p:Person)
WHERE p.name STARTS WITH "Mar"      -- uses index range scan if indexed
RETURN p.name;

// Regular expressions with =~
MATCH (p:Person)
WHERE p.email =~ '.*@(gmail|yahoo)\\.com'
RETURN p.name, p.email;

// Case-insensitive search
MATCH (p:Person)
WHERE toLower(p.name) = toLower($searchTerm)
RETURN p;
-- Note: this CANNOT use a standard index. Use a fulltext index instead:
-- CREATE FULLTEXT INDEX person_name_ft FOR (p:Person) ON EACH [p.name];
-- CALL db.index.fulltext.queryNodes("person_name_ft", "alice") YIELD node, score;
```

---

## Working with Spatial Data

```cypher
// Create nodes with point properties
CREATE (c:City {
    name: "Milano",
    location: point({longitude: 9.1900, latitude: 45.4642})
});

// Distance calculation between two points
MATCH (a:City {name: "Milano"}), (b:City {name: "Roma"})
RETURN point.distance(a.location, b.location) / 1000 AS km;
-- Returns: ~477.8 km (geodesic distance)

// Spatial index for radius queries
CREATE POINT INDEX city_location FOR (c:City) ON (c.location);

// Find all cities within 100 km of a point
MATCH (c:City)
WHERE point.distance(c.location, point({longitude: 9.19, latitude: 45.46})) < 100000
RETURN c.name, point.distance(c.location, point({longitude: 9.19, latitude: 45.46})) / 1000 AS distance_km
ORDER BY distance_km;

// Bounding box query
MATCH (c:City)
WHERE point.withinBBox(c.location,
    point({longitude: 8.0, latitude: 44.0}),   -- southwest corner
    point({longitude: 12.0, latitude: 46.5}))  -- northeast corner
RETURN c.name;
```
