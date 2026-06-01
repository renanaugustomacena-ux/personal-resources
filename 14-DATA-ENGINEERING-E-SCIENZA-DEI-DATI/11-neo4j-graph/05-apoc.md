# Neo4j — APOC: Awesome Procedures on Cypher

## What is APOC

APOC (Awesome Procedures on Cypher) is the most widely used extension library for Neo4j, maintained by Neo4j Inc. It adds hundreds of procedures and functions that extend Cypher for operations that are either impossible or impractical in standard Cypher: dynamic node/relationship creation, import/export from external systems, batch processing, graph refactoring, triggers, virtual graphs, and utility functions for strings, collections, and JSON manipulation.

APOC is split into two packages:

- **APOC Core**: Ships with Neo4j and includes safe, commonly used procedures
- **APOC Extended**: Separate download, includes procedures that require `unrestricted` permissions (JDBC, triggers, custom procedures)

### Installation

```bash
# Docker: enable APOC via environment variable
docker run \
    -e NEO4J_PLUGINS='["apoc"]' \
    -e NEO4J_dbms_security_procedures_unrestricted=apoc.* \
    neo4j:5-enterprise

# Manual installation: download the JAR matching your Neo4j version
wget https://github.com/neo4j/apoc/releases/download/5.26.0/apoc-5.26.0-core.jar
cp apoc-5.26.0-core.jar /var/lib/neo4j/plugins/

# For APOC Extended (JDBC, triggers, etc.)
wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/5.26.0/apoc-5.26.0-extended.jar
cp apoc-5.26.0-extended.jar /var/lib/neo4j/plugins/
```

```properties
# neo4j.conf — required for unrestricted APOC procedures
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.allowlist=apoc.*

# For APOC Extended with file access
apoc.import.file.enabled=true
apoc.export.file.enabled=true
apoc.import.file.use_neo4j_config=true
```

### Verifying Installation

```cypher
// List all installed APOC procedures
CALL apoc.help("apoc") YIELD name, text
RETURN name, text LIMIT 20;

// Check APOC version
RETURN apoc.version();

// Search for specific functionality
CALL apoc.help("json") YIELD name, text
RETURN name, text;
```

---

## Import and Export

### apoc.load.json — Import from JSON/HTTP

The most versatile import procedure. Loads JSON from local files, HTTP endpoints, or REST APIs.

```cypher
// Import from local JSON file
CALL apoc.load.json("file:///data/users.json") YIELD value AS row
MERGE (u:User {id: row.id})
SET u.name = row.name, u.email = row.email;

// Import from HTTP URL
CALL apoc.load.json("https://api.example.com/users?limit=1000") YIELD value AS user
MERGE (u:User {id: user.id})
SET u += user;

// JSON Lines format (one JSON object per line — common in streaming/log data)
CALL apoc.load.json("file:///events.jsonl") YIELD value AS event
CREATE (e:Event)
SET e = event;

// With HTTP authentication headers
CALL apoc.load.jsonParams(
    "https://api.example.com/data",
    {Authorization: "Bearer " + $token},
    null
) YIELD value;

// POST request with JSON body
CALL apoc.load.jsonParams(
    "https://api.example.com/graphql",
    {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + $token
    },
    '{"query": "{ users { id name email } }"}'
) YIELD value
UNWIND value.data.users AS user
MERGE (u:User {id: user.id})
SET u.name = user.name, u.email = user.email;

// Nested JSON: access deep structures
CALL apoc.load.json("file:///complex.json") YIELD value
UNWIND value.results AS result
UNWIND result.addresses AS addr
MERGE (p:Person {id: result.id})
MERGE (a:Address {street: addr.street, city: addr.city})
MERGE (p)-[:LIVES_AT]->(a);
```

**Pagination pattern for REST APIs:**

```cypher
// Load paginated API results
UNWIND range(0, 9) AS page
CALL apoc.load.jsonParams(
    "https://api.example.com/users?page=" + page + "&size=100",
    {Authorization: "Bearer " + $token},
    null
) YIELD value
UNWIND value.content AS user
MERGE (u:User {id: user.id})
SET u.name = user.name;
```

### apoc.load.csv — CSV Import with More Control than LOAD CSV

```cypher
// Basic CSV import
CALL apoc.load.csv("file:///data/products.csv", {
    header: true,
    sep: ",",
    quoteChar: '"',
    nullValues: ["", "N/A", "null"]
}) YIELD map AS row
MERGE (p:Product {sku: row.sku})
SET p.name = row.name,
    p.price = toFloat(row.price),
    p.category = row.category;

// CSV with custom mapping
CALL apoc.load.csv("file:///data/edges.csv", {
    header: true,
    mapping: {
        source_id: {type: "long"},
        target_id: {type: "long"},
        weight: {type: "float"}
    }
}) YIELD map AS row
MATCH (a:Node {id: row.source_id}), (b:Node {id: row.target_id})
MERGE (a)-[:CONNECTED_TO {weight: row.weight}]->(b);
```

### apoc.load.jdbc — Import from Relational Databases

Requires APOC Extended and a JDBC driver in the plugins directory.

```cypher
// PostgreSQL import
CALL apoc.load.jdbc(
    "jdbc:postgresql://pg-host:5432/mydb?user=admin&password=secret",
    "SELECT id, name, email FROM customers WHERE created_at > now() - interval '7 days'"
) YIELD row
MERGE (c:Customer {id: toInteger(row.id)})
SET c.name = row.name, c.email = row.email;

// MySQL import with parameterized query
CALL apoc.load.jdbc(
    "jdbc:mysql://mysql-host:3306/ecommerce",
    "SELECT order_id, customer_id, total, status FROM orders WHERE status = ?",
    ["pending"]
) YIELD row
MERGE (o:Order {id: row.order_id})
SET o.total = row.total, o.status = row.status
WITH o, row
MATCH (c:Customer {id: row.customer_id})
MERGE (c)-[:PLACED]->(o);

// Using a named JDBC connection (defined in apoc.conf)
// apoc.jdbc.mydb.url=jdbc:postgresql://host:5432/db?user=x&password=y
CALL apoc.load.jdbc("mydb", "SELECT * FROM products") YIELD row
MERGE (p:Product {id: row.id})
SET p.name = row.name;
```

### apoc.export — Export the Graph

```cypher
// Export entire graph as Cypher statements (reproducible backup)
CALL apoc.export.cypher.all("backup.cypher", {
    format: "cypher-shell",
    useOptimizations: {type: "UNWIND_BATCH", unwindBatchSize: 1000}
});

// Export a subgraph via query
CALL apoc.export.cypher.query(
    "MATCH path = (:Person)-[:KNOWS*1..2]-(:Person {name: 'Alice'}) RETURN path",
    "alice_network.cypher",
    {format: "cypher-shell"}
);

// Export to JSON
CALL apoc.export.json.all("export.json", {batchSize: 10000});

// Export to JSON with specific query
CALL apoc.export.json.query(
    "MATCH (p:Person)-[r:KNOWS]->(f:Person) RETURN p, r, f",
    "knows_network.json",
    {jsonFormat: "JSON_LINES"}
);

// Export to GraphML (compatible with Gephi, yEd, and other visualization tools)
CALL apoc.export.graphml.all("export.graphml", {storeNodeIds: true});

// Export to CSV
CALL apoc.export.csv.all("nodes.csv", "rels.csv", {});

// Export specific nodes/relationships to CSV
CALL apoc.export.csv.query(
    "MATCH (p:Person) RETURN p.name AS name, p.age AS age, p.email AS email",
    "people.csv",
    {}
);
```

**Export format comparison:**

| Format | Use Case | Tool Compatibility |
|--------|----------|-------------------|
| Cypher | Backup, migration between Neo4j instances | neo4j-shell, cypher-shell |
| JSON | Integration with other systems, APIs | Universal |
| JSON Lines | Streaming, large datasets | Spark, Kafka, log processors |
| GraphML | Visualization, academic tools | Gephi, yEd, NetworkX |
| CSV | Spreadsheets, SQL databases | Universal |

---

## Graph Manipulation

### apoc.create — Dynamic Creation

Standard Cypher requires labels and relationship types to be literals — you cannot use a variable. APOC removes this limitation.

```cypher
// Create node with dynamic label (impossible in standard Cypher)
WITH "Person" AS label_name, {name: "Alice", age: 30} AS props
CALL apoc.create.node([label_name], props) YIELD node
RETURN node;

// Create node with multiple dynamic labels
WITH ["Person", "Employee", "Engineer"] AS labels
CALL apoc.create.node(labels, {name: "Bob", dept: "Engineering"}) YIELD node
RETURN node;

// Create relationship with dynamic type
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
WITH a, b, "KNOWS" AS rel_type
CALL apoc.create.relationship(a, rel_type, {since: date()}, b) YIELD rel
RETURN rel;

// Dynamically add labels to existing nodes
MATCH (p:Person {name: "Alice"})
CALL apoc.create.addLabels(p, ["VIP", "Verified"]) YIELD node
RETURN node;

// Remove labels dynamically
MATCH (p:Person {name: "Alice"})
CALL apoc.create.removeLabels(p, ["VIP"]) YIELD node
RETURN node;

// Set properties from a map (dynamic property names)
MATCH (p:Person {name: "Alice"})
CALL apoc.create.setProperties(p, ["score", "tier"], [95, "gold"]) YIELD node
RETURN node;
```

### apoc.refactor — Graph Restructuring

Refactoring procedures modify the graph structure without losing data. Essential for schema evolution, data cleaning, and migration.

```cypher
// Merge duplicate nodes (unifies properties and relationships)
MATCH (p:Person {email: "alice@example.com"})
WITH collect(p) AS duplicates
WHERE size(duplicates) > 1
CALL apoc.refactor.mergeNodes(duplicates, {
    properties: "discard",    // "discard", "overwrite", or "combine"
    mergeRels: true           // re-attach relationships to surviving node
}) YIELD node
RETURN node;

// mergeNodes property strategies:
// "discard"   — keep first node's properties, discard others
// "overwrite" — last node's properties win
// "combine"   — merge into arrays (e.g., {email: ["a@x.com", "b@x.com"]})

// Merge relationships between same node pairs
MATCH (a:Person)-[r:KNOWS]->(b:Person)
WITH a, b, collect(r) AS rels
WHERE size(rels) > 1
CALL apoc.refactor.mergeRelationships(rels, {properties: "combine"})
YIELD rel
RETURN rel;

// Rename a label across the entire graph
CALL apoc.refactor.rename.label("OldLabel", "NewLabel");

// Rename a relationship type
CALL apoc.refactor.rename.type("OLD_REL", "NEW_REL");

// Rename a property on all nodes with a specific label
CALL apoc.refactor.rename.nodeProperty("phone_number", "phone", ["Person"]);

// Rename a relationship property
CALL apoc.refactor.rename.typeProperty("OLD_PROP", "NEW_PROP", ["KNOWS"]);

// Convert a property to a node (normalization)
// e.g., Person.city -> Person-[:LIVES_IN]->City
MATCH (p:Person) WHERE p.city IS NOT NULL
WITH p, p.city AS city_name
MERGE (c:City {name: city_name})
MERGE (p)-[:LIVES_IN]->(c)
REMOVE p.city;

// Invert relationship direction
MATCH (a:Person)-[r:REPORTS_TO]->(b:Person)
CALL apoc.refactor.invert(r)
YIELD input, output
RETURN input, output;

// Extract a node from a relationship
// Before: (Person)-[r:WORKED_AT {company: "ACME", from: 2020, to: 2023}]->(Role)
// After:  (Person)-[:HAD]->(Employment)-[:AT]->(Company)
MATCH (p:Person)-[r:WORKED_AT]->(role:Role)
CALL apoc.refactor.extractNode(r, ["Employment"], "HAD", "FOR")
YIELD input, output
RETURN output;

// Collapse a node into a relationship
// Before: (A)-[:REL1]->(intermediate)-[:REL2]->(B)
// After:  (A)-[:CONNECTS_TO]->(B)
MATCH (a)-[:REL1]->(mid:Intermediate)-[:REL2]->(b)
CALL apoc.refactor.collapseNode([mid], "CONNECTS_TO")
YIELD input, output
RETURN output;
```

### apoc.refactor — Categorize and Classify

```cypher
// Categorize nodes by a property value (create category nodes automatically)
CALL apoc.refactor.categorize(
    "department",           // property to categorize on
    "BELONGS_TO",          // relationship type to create
    true,                  // outgoing direction
    "Department",          // label for category nodes
    "name",               // property on category node for the value
    ["Employee"]           // labels to process
);
// Before: (:Employee {department: "Engineering"})
// After:  (:Employee)-[:BELONGS_TO]->(:Department {name: "Engineering"})
```

---

## Batch Operations (Periodic Procedures)

### apoc.periodic.iterate — The Batch Processing Workhorse

The single most important APOC procedure for production use. It processes large datasets in batches, committing each batch independently to avoid memory exhaustion.

**How it works:**
1. The first (outer) statement generates data — a stream of rows
2. The second (inner) statement processes each row
3. Rows are grouped into batches of `batchSize`
4. Each batch is committed as a separate transaction

```cypher
// Update all Person nodes in batches of 10,000
CALL apoc.periodic.iterate(
    "MATCH (p:Person) RETURN p",
    "SET p.processed = true, p.updated_at = datetime()",
    {batchSize: 10000, parallel: false, iterateList: true}
) YIELD batches, total, timeTaken, committedOperations, failedOperations;

// Batch import from CSV
CALL apoc.periodic.iterate(
    "CALL apoc.load.csv('file:///large.csv', {header: true}) YIELD map AS row RETURN row",
    "MERGE (p:Person {id: toInteger(row.id)})
     SET p.name = row.name, p.email = row.email",
    {batchSize: 5000, parallel: false}
) YIELD batches, total;

// Mass deletion without OOM (critical for large datasets)
CALL apoc.periodic.iterate(
    "MATCH (n:TempNode) RETURN n",
    "DETACH DELETE n",
    {batchSize: 10000}
) YIELD batches, total;

// Create relationships in batch
CALL apoc.periodic.iterate(
    "MATCH (a:Person), (b:Person)
     WHERE a.department = b.department AND a <> b AND NOT (a)-[:COLLEAGUE]-(b)
     RETURN a, b",
    "CREATE (a)-[:COLLEAGUE {since: date()}]->(b)",
    {batchSize: 5000, parallel: false}
) YIELD batches, total, timeTaken;

// Parallel execution (use with caution — only for independent operations)
CALL apoc.periodic.iterate(
    "MATCH (p:Person) RETURN p",
    "SET p.normalized_name = apoc.text.clean(p.name)",
    {batchSize: 10000, parallel: true, concurrency: 4}
) YIELD batches, total, timeTaken;
```

**Parallel execution pitfalls:**
- `parallel: true` processes multiple batches concurrently
- Safe ONLY when batches do not modify the same nodes/relationships
- Unsafe for MERGE operations (can create duplicates under concurrency)
- Safe for SET on independent nodes (each node in exactly one batch)
- Default `parallel: false` is always safe

### apoc.periodic.commit — Loop Until Done

Executes a statement repeatedly until it returns 0 updates. Useful for migrations where you process a subset each iteration.

```cypher
// Migrate all unmigrated nodes, 10,000 at a time
CALL apoc.periodic.commit(
    "MATCH (p:Person) WHERE p.migrated IS NULL
     WITH p LIMIT 10000
     SET p.migrated = true
     RETURN count(*)",
    {}
) YIELD updates, executions, runtime;

// Gradually delete old data
CALL apoc.periodic.commit(
    "MATCH (e:Event) WHERE e.created < datetime() - duration('P90D')
     WITH e LIMIT 5000
     DETACH DELETE e
     RETURN count(*)",
    {}
) YIELD updates, executions, runtime;
```

### apoc.periodic.countdown — Scheduled Execution

```cypher
// Run a cleanup every 60 seconds (only while the session is active)
CALL apoc.periodic.countdown("cleanup-job",
    "MATCH (n:TempNode) WHERE n.expires < datetime()
     DETACH DELETE n RETURN count(*) AS deleted",
    60
);

// Cancel a scheduled job
CALL apoc.periodic.cancel("cleanup-job");

// List running periodic jobs
CALL apoc.periodic.list();
```

---

## Triggers (APOC Extended)

Triggers execute automatically when data changes. They are the Neo4j equivalent of database triggers in RDBMS.

```cypher
// Trigger: set updated_at on any node modification
CALL apoc.trigger.add(
    "set-updated-timestamp",
    "UNWIND $assignedNodeProperties AS prop
     WITH prop.node AS n
     SET n.updated_at = datetime()",
    {phase: "before"}
);

// Trigger: maintain a counter on relationship creation
CALL apoc.trigger.add(
    "count-relationships",
    "UNWIND $createdRelationships AS r
     WITH r
     WHERE type(r) = 'KNOWS'
     SET startNode(r).knows_count = coalesce(startNode(r).knows_count, 0) + 1",
    {phase: "after"}
);

// Trigger: prevent deletion of protected nodes
CALL apoc.trigger.add(
    "protect-critical-nodes",
    "UNWIND $deletedNodes AS n
     WITH n WHERE n:Protected
     CALL apoc.util.validate(true, 'Cannot delete protected node: %s', [n.name])
     RETURN n",
    {phase: "before"}
);

// List all triggers
CALL apoc.trigger.list();

// Remove a trigger
CALL apoc.trigger.remove("set-updated-timestamp");

// Pause/resume triggers
CALL apoc.trigger.pause("count-relationships");
CALL apoc.trigger.resume("count-relationships");
```

**Trigger phases:**
- `before`: Executes before the transaction commits. Can modify data or abort the transaction.
- `after`: Executes after the commit. Cannot modify the committed data.
- `rollback`: Executes if the transaction rolls back.

**Available trigger variables:**
- `$assignedNodeProperties` — properties set on nodes
- `$assignedRelationshipProperties` — properties set on relationships
- `$createdNodes` — newly created nodes
- `$createdRelationships` — newly created relationships
- `$deletedNodes` — deleted nodes
- `$deletedRelationships` — deleted relationships
- `$removedNodeProperties` — properties removed from nodes
- `$assignedLabels` — labels added to nodes
- `$removedLabels` — labels removed from nodes

---

## Virtual Nodes and Relationships

Virtual nodes and relationships exist only in the query result — they are not persisted in the database. Useful for building aggregated views, previewing refactoring, or returning computed graph structures.

```cypher
// Create a virtual node
CALL apoc.create.vNode(["Summary"], {
    type: "department_overview",
    count: 42,
    avg_salary: 75000
}) YIELD node AS virtual_summary
RETURN virtual_summary;

// Create virtual relationships between real nodes and virtual nodes
MATCH (dept:Department)
WITH dept, size((dept)<-[:BELONGS_TO]-()) AS emp_count
CALL apoc.create.vNode(["DeptStats"], {
    name: dept.name, employees: emp_count
}) YIELD node AS stats
CALL apoc.create.vRelationship(dept, "HAS_STATS", {}, stats) YIELD rel
RETURN dept, rel, stats;

// Virtual graph from aggregation (for visualization)
MATCH (a:Person)-[:BELONGS_TO]->(d1:Department),
      (b:Person)-[:BELONGS_TO]->(d2:Department),
      (a)-[:KNOWS]->(b)
WHERE d1 <> d2
WITH d1, d2, count(*) AS cross_connections
CALL apoc.create.vRelationship(d1, "INTERACTS_WITH", {
    connections: cross_connections
}, d2) YIELD rel
RETURN d1, rel, d2;
```

### Virtual Graphs for Previewing Refactoring

```cypher
// Preview what a merge would look like without executing it
MATCH (p1:Person {email: "alice@old.com"}), (p2:Person {email: "alice@new.com"})
CALL apoc.create.vNode(labels(p1), apoc.map.merge(p1{.*}, p2{.*})) YIELD node AS merged
RETURN merged;
// Inspect the virtual node — if it looks correct, run the actual merge
```

---

## Utility Functions

### JSON and Map Operations

```cypher
// Parse JSON string to map
WITH '{"name": "Alice", "tags": ["neo4j", "graph"]}' AS json_str
RETURN apoc.convert.fromJsonMap(json_str) AS parsed;

// Parse JSON array
WITH '[1, 2, 3, 4]' AS json_str
RETURN apoc.convert.fromJsonList(json_str) AS list;

// Convert to JSON string
RETURN apoc.convert.toJson({name: "Alice", age: 30}) AS json;

// Flatten nested maps
WITH {person: {name: "Alice"}, address: {city: "Milano"}} AS nested
RETURN apoc.map.flatten(nested, ".") AS flat;
// Result: {person.name: "Alice", address.city: "Milano"}

// Merge maps (second map wins on conflicts)
RETURN apoc.map.merge({a: 1, b: 2}, {b: 3, c: 4}) AS merged;
// Result: {a: 1, b: 3, c: 4}

// Subset of a map (select specific keys)
RETURN apoc.map.submap({a: 1, b: 2, c: 3}, ["a", "c"]) AS subset;
// Result: {a: 1, c: 3}

// Remove keys from a map
RETURN apoc.map.removeKeys({a: 1, b: 2, c: 3}, ["b"]) AS cleaned;
// Result: {a: 1, c: 3}

// Set nested key
RETURN apoc.map.setKey({a: 1}, "b", 2) AS updated;
// Result: {a: 1, b: 2}

// Group a list of maps by a key
WITH [{name: "Alice", dept: "Eng"}, {name: "Bob", dept: "Eng"},
      {name: "Charlie", dept: "Sales"}] AS people
RETURN apoc.map.groupBy(people, "dept") AS grouped;
```

### Collection and Array Operations

```cypher
// Flatten nested lists
RETURN apoc.coll.flatten([[1, 2], [3, 4], [5]]) AS flat;
// Result: [1, 2, 3, 4, 5]

// Deduplicate
RETURN apoc.coll.toSet([1, 2, 2, 3, 3]) AS unique;
// Result: [1, 2, 3]

// Set operations
RETURN apoc.coll.intersection([1, 2, 3], [2, 3, 4]) AS inter,
       apoc.coll.subtract([1, 2, 3], [2, 3]) AS diff,
       apoc.coll.union([1, 2, 3], [2, 3, 4]) AS combined;
// inter: [2, 3], diff: [1], combined: [1, 2, 3, 4]

// Random and shuffle
RETURN apoc.coll.randomItem([1, 2, 3, 4, 5]) AS random_pick,
       apoc.coll.shuffle([1, 2, 3, 4, 5]) AS shuffled;

// Partition a list into chunks
RETURN apoc.coll.partition([1, 2, 3, 4, 5, 6, 7], 3) AS chunks;
// Result: [[1, 2, 3], [4, 5, 6], [7]]

// Sort with custom comparator
RETURN apoc.coll.sort([3, 1, 4, 1, 5, 9]) AS sorted;
// Result: [1, 1, 3, 4, 5, 9]

// Zip two lists into pairs
RETURN apoc.coll.zip(["a", "b", "c"], [1, 2, 3]) AS zipped;
// Result: [["a", 1], ["b", 2], ["c", 3]]

// Check containment
RETURN apoc.coll.contains([1, 2, 3], 2) AS has_two,
       apoc.coll.containsAll([1, 2, 3], [2, 3]) AS has_both;

// Frequencies (count occurrences)
RETURN apoc.coll.frequencies(["a", "b", "a", "c", "a", "b"]) AS freq;
// Result: [{item: "a", count: 3}, {item: "b", count: 2}, {item: "c", count: 1}]

// Pairs (sliding window of size 2)
RETURN apoc.coll.pairs([1, 2, 3, 4]) AS pairs;
// Result: [[1, 2], [2, 3], [3, 4], [null, null]]
```

### String Operations

```cypher
// Case transformations
RETURN apoc.text.camelCase("hello world") AS camel,        // "helloWorld"
       apoc.text.snakeCase("HelloWorld") AS snake,          // "hello_world"
       apoc.text.upperCamelCase("hello world") AS pascal,   // "HelloWorld"
       apoc.text.slug("Hello World!", "-") AS slug;         // "Hello-World"

// Regex operations
RETURN apoc.text.regexGroups(
    "2024-01-15",
    "(\\d{4})-(\\d{2})-(\\d{2})"
) AS groups;
// Result: [["2024-01-15", "2024", "01", "15"]]

// String similarity metrics
RETURN apoc.text.levenshteinDistance("kitten", "sitting") AS levenshtein,
       apoc.text.jaroWinklerDistance("Mario", "Maria") AS jaro_winkler,
       apoc.text.sorensenDiceSimilarity("night", "nacht") AS sorensen;
// levenshtein: 3, jaro_winkler: ~0.93, sorensen: ~0.25

// Fuzzy matching (useful for deduplication)
RETURN apoc.text.fuzzyMatch("John Smith", "Jon Smyth") AS is_similar;

// String cleaning
RETURN apoc.text.clean("  Hello   World  ") AS cleaned,
       apoc.text.capitalize("hello world") AS capitalized,
       apoc.text.decapitalize("Hello") AS decap;

// Left-pad (useful for formatting IDs)
RETURN apoc.text.lpad("42", 10, "0") AS padded;
// Result: "0000000042"

// Join with separator
RETURN apoc.text.join(["one", "two", "three"], ", ") AS joined;
// Result: "one, two, three"

// Replace with regex
RETURN apoc.text.replace("Hello 123 World 456", "\\d+", "#") AS replaced;
// Result: "Hello # World #"
```

### Number and Conversion Utilities

```cypher
// Number formatting
RETURN apoc.number.format(12345.6789, "#,##0.00") AS formatted;
// Result: "12,345.68"

// Parse number from string
RETURN apoc.number.parseInt("1,234", "#,###") AS parsed;
// Result: 1234

// Convert between types
RETURN apoc.convert.toFloat("3.14") AS float_val,
       apoc.convert.toInteger("42") AS int_val,
       apoc.convert.toBoolean("true") AS bool_val,
       apoc.convert.toString(42) AS str_val;

// Convert node/relationship to map
MATCH (p:Person {name: "Alice"})
RETURN apoc.convert.toMap(p) AS node_as_map;

// Convert list of nodes to list of maps
MATCH (p:Person)
WITH collect(p) AS people
RETURN apoc.convert.toList(people) AS people_list;
```

### Hash and Checksum Functions

```cypher
// Generate hashes (useful for deduplication, checksums)
RETURN apoc.util.md5(["Alice", "alice@example.com"]) AS md5_hash,
       apoc.util.sha1(["Alice", "alice@example.com"]) AS sha1_hash,
       apoc.util.sha256(["Alice", "alice@example.com"]) AS sha256_hash;

// Hash a node's properties for change detection
MATCH (p:Person {name: "Alice"})
RETURN apoc.util.md5([p.name, p.email, toString(p.age)]) AS content_hash;

// UUID generation
RETURN apoc.create.uuid() AS uuid;
// Result: "550e8400-e29b-41d4-a716-446655440000"
```

### Date and Time Utilities

```cypher
// Format dates
RETURN apoc.date.format(datetime().epochMillis, "ms", "yyyy-MM-dd HH:mm:ss") AS formatted;

// Parse date strings
RETURN apoc.date.parse("2024-01-15 10:30:00", "ms", "yyyy-MM-dd HH:mm:ss") AS epoch_ms;

// Date arithmetic
RETURN apoc.date.add(datetime().epochMillis, "ms", 7, "d") AS next_week_epoch;

// Convert between formats
WITH "15/01/2024" AS eu_date
RETURN apoc.date.convertFormat(eu_date, "dd/MM/yyyy", "yyyy-MM-dd") AS iso_date;
```

---

## Integration with External Databases

### JDBC Connections

```cypher
// Direct connection to PostgreSQL
CALL apoc.load.jdbc(
    "jdbc:postgresql://pg-host:5432/mydb?user=admin&password=secret",
    "SELECT id, name, email FROM customers WHERE created_at > now() - interval '7 days'"
) YIELD row
MERGE (c:Customer {id: toInteger(row.id)})
SET c.name = row.name, c.email = row.email;

// Named JDBC connections (configure in apoc.conf for security)
// apoc.jdbc.production.url=jdbc:postgresql://host:5432/db?user=x&password=y
CALL apoc.load.jdbc("production", "SELECT * FROM orders LIMIT 100") YIELD row
RETURN row;

// Write back to RDBMS
CALL apoc.load.jdbcUpdate(
    "jdbc:postgresql://pg-host:5432/mydb?user=admin&password=secret",
    "UPDATE customers SET neo4j_id = ? WHERE id = ?",
    [node_id, customer_id]
);
```

### HTTP REST Calls

```cypher
// GET request
CALL apoc.load.jsonParams(
    "https://api.external.com/enrich",
    {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + apoc.static.get("api.token")
    },
    null
) YIELD value AS enriched
RETURN enriched;

// POST request with body
CALL apoc.load.jsonParams(
    "https://api.external.com/score",
    {
        "Content-Type": "application/json",
        "X-API-Key": $apiKey
    },
    apoc.convert.toJson({user_id: p.id, features: p.features})
) YIELD value
RETURN value.risk_score;
```

### Elasticsearch Integration

```cypher
// Index Neo4j data to Elasticsearch
MATCH (p:Person)
WITH collect({id: p.id, name: p.name, department: p.department}) AS docs
CALL apoc.es.put("es-host:9200", "people", "_doc", null, docs, {}) YIELD value
RETURN value;

// Search Elasticsearch and enrich Neo4j
CALL apoc.es.query("es-host:9200", "people", "_search", null, {
    query: {match: {name: "Alice"}}
}) YIELD value
UNWIND value.hits.hits AS hit
MATCH (p:Person {id: hit._source.id})
SET p.es_score = hit._score;
```

---

## apoc.meta — Graph Introspection

```cypher
// Full graph schema (labels, relationship types, properties)
CALL apoc.meta.schema() YIELD value
RETURN value;

// Graph statistics
CALL apoc.meta.stats() YIELD labelCount, relTypeCount, propertyKeyCount,
     nodeCount, relCount, labels, relTypes, relTypesCount;

// Sample the graph (useful for large databases — avoids full scan)
CALL apoc.meta.graph({sample: 1000}) YIELD nodes, relationships;

// Data model as a graph (meta-graph)
CALL apoc.meta.subGraph({labels: ["Person", "Company"], rels: ["WORKS_AT"]})
YIELD nodes, relationships;

// Node type distribution
CALL apoc.meta.nodeTypeProperties() YIELD nodeType, propertyName, propertyTypes
RETURN nodeType, propertyName, propertyTypes;

// Relationship type properties
CALL apoc.meta.relTypeProperties() YIELD relType, propertyName, propertyTypes
RETURN relType, propertyName, propertyTypes;
```

---

## apoc.do — Conditional Execution

APOC provides conditional execution that Cypher lacks natively.

```cypher
// Execute different Cypher based on a condition
WITH true AS is_premium
CALL apoc.do.when(
    is_premium,
    "MATCH (u:User {id: $userId}) SET u.tier = 'premium' RETURN u",
    "MATCH (u:User {id: $userId}) SET u.tier = 'standard' RETURN u",
    {userId: 1001}
) YIELD value
RETURN value;

// Switch/case
WITH "admin" AS role
CALL apoc.do.case([
    role = "admin",   "RETURN 'full access' AS level",
    role = "editor",  "RETURN 'write access' AS level",
    role = "viewer",  "RETURN 'read access' AS level"
], "RETURN 'no access' AS level", {})
YIELD value
RETURN value.level;
```

---

## apoc.nodes and apoc.rels — Node and Relationship Utilities

```cypher
// Get node by internal ID (useful when ID is stored externally)
CALL apoc.nodes.get([1, 2, 3]) YIELD node
RETURN node;

// Check if a node exists
RETURN apoc.nodes.isDense(node) AS is_dense;
// Returns true if the node has many relationships (stored differently internally)

// Get connected nodes (all neighbors)
MATCH (p:Person {name: "Alice"})
CALL apoc.nodes.connected(p, "KNOWS") YIELD node
RETURN node.name;

// Get relationship between two specific nodes
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
RETURN apoc.nodes.relationship(a, b, "KNOWS") AS rel;

// Collapse redundant intermediate nodes
MATCH (a:Person)-[:BELONGS_TO]->(d:Department)-[:PART_OF]->(div:Division)
RETURN apoc.nodes.collapse([d], ["BELONGS_TO", "PART_OF"]) AS collapsed;
```

### apoc.path — Utility Path Functions

```cypher
// Get all elements from a path as a flat list
MATCH path = (a:Person)-[:KNOWS*1..3]->(b:Person)
RETURN apoc.path.elements(path) AS all_elements;

// Slice a path (get sub-path)
MATCH path = (a:Person)-[:KNOWS*1..5]->(b:Person)
RETURN apoc.path.slice(path, 0, 3) AS first_three_hops;

// Create a path from nodes and relationships
MATCH (a:Person {name: "Alice"})-[r:KNOWS]->(b:Person {name: "Bob"})
RETURN apoc.path.create(a, [r]) AS constructed_path;
```

### apoc.schema — Schema Management

```cypher
// Create index dynamically
CALL apoc.schema.assert(
    {Person: ["name", "email"]},    // indexes
    {Person: ["id"]}                // unique constraints
);

// List all constraints
CALL apoc.schema.nodes() YIELD name, label, properties, type
RETURN *;

// List all indexes with usage statistics
CALL apoc.schema.nodes() YIELD name, label, properties, status
RETURN *;

// Drop all indexes and constraints (dangerous — development only)
CALL apoc.schema.assert({}, {}, true);
```

### apoc.warmup — Cache Warming

```cypher
// Pre-load the entire graph into page cache on startup
CALL apoc.warmup.run(true, true, true);
// Parameters: (loadProperties, loadDynamicProperties, loadIndexes)

// Warm up specific types
CALL apoc.warmup.run(true, false, true);
// Load properties and indexes, skip dynamic properties
```

---

## apoc.cypher — Dynamic Cypher Execution

Run Cypher statements built at runtime. Use with care — dynamic Cypher bypasses compile-time checks and can introduce injection risks if inputs are not parameterized.

```cypher
// Run a dynamically constructed query
WITH "MATCH (p:Person) WHERE p.name = $name RETURN p" AS query
CALL apoc.cypher.run(query, {name: "Alice"}) YIELD value
RETURN value;

// Run multiple statements
CALL apoc.cypher.runMany(
    "CREATE (a:Test {id: 1}); CREATE (b:Test {id: 2}); MATCH (a:Test), (b:Test) WHERE a.id=1 AND b.id=2 CREATE (a)-[:LINK]->(b);",
    {}
) YIELD result
RETURN result;

// Run a read-only query (safer — prevents accidental writes)
CALL apoc.cypher.runFirstColumnMany(
    "MATCH (p:Person) RETURN p.name",
    {}
) YIELD value
RETURN value;
```

---

## apoc.lock — Explicit Locking

When you need to prevent concurrent modification of specific nodes:

```cypher
// Acquire a write lock on specific nodes before modification
MATCH (a:Account {id: "ACC001"}), (b:Account {id: "ACC002"})
CALL apoc.lock.nodes([a, b])
// Now modify with guaranteed exclusive access
SET a.balance = a.balance - 100,
    b.balance = b.balance + 100;
```

---

## Troubleshooting

### Problem: apoc.load.json returns empty or null

**Causes:**
1. File path is incorrect (missing `file:///` prefix)
2. File access is disabled in config
3. JSON is malformed

**Diagnosis and fix:**
```properties
# Verify these settings in neo4j.conf
apoc.import.file.enabled=true
apoc.import.file.use_neo4j_config=true
# Files must be in the Neo4j import directory (default: /var/lib/neo4j/import/)
```

```cypher
// Test with a minimal JSON
CALL apoc.load.json("file:///test.json") YIELD value RETURN value LIMIT 1;
// If this fails, the file path or config is wrong
```

### Problem: apoc.periodic.iterate fails silently

**Causes:**
1. Inner statement has a Cypher syntax error (errors are swallowed per-batch)
2. Deadlocks from `parallel: true` on overlapping data

**Diagnosis:**
```cypher
// Check failedOperations in the result
CALL apoc.periodic.iterate(
    "MATCH (p:Person) RETURN p",
    "SET p.x = 1",
    {batchSize: 1000, parallel: false}
) YIELD batches, total, failedOperations, failedBatches, errorMessages
RETURN *;
// If failedOperations > 0, check errorMessages
```

**Fix:** Test the inner statement independently first:
```cypher
// Run the inner statement on a single row to verify syntax
MATCH (p:Person) WITH p LIMIT 1
SET p.x = 1
RETURN p;
```

### Problem: JDBC connection fails

**Causes:**
1. JDBC driver JAR not in plugins directory
2. Wrong connection string format
3. Firewall blocking the connection

**Fix:**
```bash
# Download the JDBC driver and place it in the plugins directory
# For PostgreSQL:
wget https://jdbc.postgresql.org/download/postgresql-42.7.1.jar
cp postgresql-42.7.1.jar /var/lib/neo4j/plugins/
# Restart Neo4j
```

### Problem: Trigger causes performance degradation

**Cause:** Trigger runs on every write operation, even unrelated ones.

**Fix:** Make trigger conditions more specific:
```cypher
// Bad: runs on ALL node property changes
"UNWIND $assignedNodeProperties AS prop SET prop.node.updated_at = datetime()"

// Better: only runs on Person nodes
"UNWIND $assignedNodeProperties AS prop
 WITH prop WHERE prop.node:Person
 SET prop.node.updated_at = datetime()"
```

### Problem: apoc.refactor.mergeNodes loses data

**Cause:** Using `properties: "discard"` drops properties from non-surviving nodes.

**Fix:** Use `properties: "combine"` to merge properties into arrays, or pre-process manually:
```cypher
// Preview before merging
MATCH (p:Person {email: "alice@example.com"})
RETURN p.name, p.phone, p.address, id(p)
ORDER BY id(p);
// Verify which properties exist on each duplicate, then choose the strategy
```

### Problem: apoc.export writes an empty file

**Cause:** Export is disabled in config, or the query matches no data.

**Fix:**
```properties
# Verify in neo4j.conf
apoc.export.file.enabled=true
```
```cypher
// Test the query that feeds the export
MATCH (p:Person) RETURN count(p);
// If 0, the export has nothing to write
```

---

## Q&A

**Q1: What is the difference between APOC Core and APOC Extended?**

APOC Core ships with Neo4j and includes safe procedures that do not need elevated permissions — JSON loading, text utilities, collection operations, graph refactoring. APOC Extended requires separate installation and `unrestricted` permissions — includes JDBC, triggers, Elasticsearch integration, and procedures that access external resources.

**Q2: Is apoc.periodic.iterate safe to run on production?**

Yes, with `parallel: false`. It commits in batches, so a failure in one batch does not roll back previous batches. Use it for migrations, cleanups, and bulk updates. With `parallel: true`, ensure batches operate on completely independent data.

**Q3: Can I use APOC for ETL pipelines?**

Yes. Combine `apoc.load.jdbc` (source) with `apoc.periodic.iterate` (batch processing) and `apoc.export.*` (target). For large-scale ETL, consider neo4j-admin import or Apache Spark + Neo4j connector instead.

**Q4: How do triggers compare to application-level event handlers?**

Triggers execute inside the database transaction — they are guaranteed to run (or abort the transaction). Application handlers run outside the transaction and can fail silently. Use triggers for invariants that must always hold (audit trails, cascading updates). Use application handlers for non-critical side effects (notifications, caching).

**Q5: Can virtual nodes and relationships be persisted?**

No. Virtual nodes/relationships exist only in the query result set. They are not stored in the database. To persist them, use CREATE/MERGE with the same properties.

**Q6: How do I handle large JSON files that do not fit in memory?**

Use JSON Lines format (one object per line) with `apoc.load.json`. Each line is processed independently, so memory usage is proportional to a single object, not the entire file. For very large files, combine with `apoc.periodic.iterate`.

**Q7: What happens if apoc.periodic.iterate encounters an error in one batch?**

The failed batch is rolled back, but previous successful batches remain committed. The procedure continues processing remaining batches. Check `failedOperations` and `errorMessages` in the return value.

**Q8: Can I use APOC to call a GraphQL API?**

Yes. Use `apoc.load.jsonParams` with a POST request containing the GraphQL query as the body. Parse the response using APOC JSON functions.

**Q9: How do I prevent duplicate imports when using apoc.load.json?**

Use MERGE instead of CREATE in the inner statement. MERGE checks for existing nodes/relationships before creating. Combine with a unique constraint on the key property for atomicity.

**Q10: What is the performance overhead of triggers?**

Triggers add latency to every write transaction that matches their condition. A trigger that runs on all node property changes will slow down every SET operation. Keep trigger logic minimal and filter aggressively on labels/types.

**Q11: Can APOC work with Neo4j Aura (managed cloud)?**

APOC Core is available on Aura. APOC Extended is not available because Aura does not allow custom plugins. Functions like `apoc.load.jdbc` and triggers are not available on Aura.

**Q12: How do I schedule periodic data synchronization from a relational database?**

Use `apoc.periodic.repeat` (APOC Extended) to run a JDBC import on a schedule, or use an external scheduler (cron, Airflow) that executes a Cypher script via `cypher-shell`.

**Q13: Is there a risk of Cypher injection when using apoc.cypher.run?**

Yes. If you build query strings by concatenating user input, injection is possible. Always use parameters (`$param`) instead of string concatenation. `apoc.cypher.run(query, {param: value})` is safe as long as the query string itself is not built from untrusted input.

**Q14: Can I use APOC to migrate from one Neo4j version to another?**

Yes. Export the graph from the source with `apoc.export.cypher.all` using `cypher-shell` format. Import into the target with `cypher-shell < backup.cypher`. This handles cross-version migration where `neo4j-admin dump/load` may not be compatible.

---

## Real-World Scenario: Data Migration from PostgreSQL to Neo4j

A complete worked example of migrating a relational database to a graph database using APOC.

```cypher
// Step 1: Import customers from PostgreSQL
CALL apoc.periodic.iterate(
    "CALL apoc.load.jdbc('production-pg',
        'SELECT id, name, email, phone, created_at FROM customers') YIELD row RETURN row",
    "MERGE (c:Customer {id: row.id})
     SET c.name = row.name,
         c.email = row.email,
         c.phone = row.phone,
         c.created_at = datetime(row.created_at)",
    {batchSize: 5000, parallel: false}
) YIELD batches, total, timeTaken
RETURN 'Customers imported: ' + total;

// Step 2: Import products
CALL apoc.periodic.iterate(
    "CALL apoc.load.jdbc('production-pg',
        'SELECT id, name, category, price FROM products') YIELD row RETURN row",
    "MERGE (p:Product {id: row.id})
     SET p.name = row.name,
         p.category = row.category,
         p.price = toFloat(row.price)",
    {batchSize: 5000, parallel: false}
) YIELD total
RETURN 'Products imported: ' + total;

// Step 3: Import orders and create relationships
CALL apoc.periodic.iterate(
    "CALL apoc.load.jdbc('production-pg',
        'SELECT o.id AS order_id, o.customer_id, o.order_date, o.total,
                oi.product_id, oi.quantity, oi.unit_price
         FROM orders o JOIN order_items oi ON o.id = oi.order_id') YIELD row RETURN row",
    "MERGE (o:Order {id: row.order_id})
     SET o.order_date = datetime(row.order_date), o.total = toFloat(row.total)
     WITH o, row
     MATCH (c:Customer {id: row.customer_id})
     MERGE (c)-[:PLACED]->(o)
     WITH o, row
     MATCH (p:Product {id: row.product_id})
     MERGE (o)-[:CONTAINS {quantity: row.quantity, unit_price: toFloat(row.unit_price)}]->(p)",
    {batchSize: 2000, parallel: false}
) YIELD total, timeTaken
RETURN 'Order items imported: ' + total + ' in ' + timeTaken + 'ms';

// Step 4: Post-migration validation
CALL apoc.meta.stats() YIELD nodeCount, relCount, labels
RETURN nodeCount, relCount, labels;

// Step 5: Export a verification report
CALL apoc.export.csv.query(
    "MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
     RETURN c.name AS customer, o.id AS order, p.name AS product, o.total AS total
     LIMIT 100",
    "migration_verification.csv",
    {}
);
```

## Real-World Scenario: Entity Resolution with Fuzzy Matching

Deduplicating records that refer to the same real-world entity but have slightly different data.

```cypher
// Step 1: Find potential duplicates using fuzzy string matching
MATCH (p1:Person), (p2:Person)
WHERE id(p1) < id(p2)
  AND apoc.text.jaroWinklerDistance(p1.name, p2.name) > 0.9
  AND (p1.email = p2.email
       OR apoc.text.levenshteinDistance(p1.phone, p2.phone) < 3)
WITH p1, p2,
     apoc.text.jaroWinklerDistance(p1.name, p2.name) AS name_sim,
     CASE WHEN p1.email = p2.email THEN 1.0 ELSE 0.0 END AS email_match
WHERE name_sim * 0.4 + email_match * 0.6 > 0.7
RETURN p1.name, p2.name, name_sim, email_match
ORDER BY name_sim DESC;

// Step 2: Preview merges with virtual nodes
MATCH (p1:Person), (p2:Person)
WHERE id(p1) < id(p2)
  AND p1.email = p2.email
  AND apoc.text.jaroWinklerDistance(p1.name, p2.name) > 0.9
WITH p1, p2
CALL apoc.create.vNode(
    labels(p1),
    apoc.map.merge(p1{.*}, {
        alt_name: p2.name,
        alt_phone: p2.phone,
        merge_candidate: true
    })
) YIELD node AS preview
RETURN preview;

// Step 3: Execute merges after review
CALL apoc.periodic.iterate(
    "MATCH (p1:Person), (p2:Person)
     WHERE id(p1) < id(p2) AND p1.email = p2.email
       AND apoc.text.jaroWinklerDistance(p1.name, p2.name) > 0.9
     RETURN p1, p2",
    "WITH [p1, p2] AS pair
     CALL apoc.refactor.mergeNodes(pair, {properties: 'combine', mergeRels: true})
     YIELD node RETURN node",
    {batchSize: 100, parallel: false}
) YIELD total
RETURN 'Merged ' + total + ' duplicate pairs';
```

## Real-World Scenario: API-Driven Graph Enrichment

Enriching graph data by calling external APIs and writing results back.

```cypher
// Enrich company nodes with data from an external API
CALL apoc.periodic.iterate(
    "MATCH (c:Company) WHERE c.enriched IS NULL RETURN c",
    "CALL apoc.load.jsonParams(
        'https://api.enrichment.com/v2/company?domain=' + c.domain,
        {Authorization: 'Bearer ' + apoc.static.get('enrichment.api.key')},
        null
    ) YIELD value AS data
    SET c.industry = data.industry,
        c.employee_count = data.employees,
        c.founded_year = data.founded,
        c.enriched = true",
    {batchSize: 10, parallel: false}
) YIELD total, failedOperations
RETURN total, failedOperations;
```

---

## Exercises

### Exercise 1 — JSON Import Pipeline (Beginner)

Write a Cypher script that imports a JSON file containing an array of users, each with nested address objects. Create Person nodes, Address nodes, and LIVES_AT relationships. Use MERGE to make the import idempotent.

### Exercise 2 — Batch Cleanup (Beginner)

You have 5 million nodes labeled `:TempSession` that need to be deleted. Write a batch deletion using `apoc.periodic.iterate` that processes 10,000 nodes per batch. Monitor the progress by checking the return values.

### Exercise 3 — Graph Refactoring (Intermediate)

A graph has duplicate Person nodes identified by matching email addresses. Write a procedure that: (1) finds all duplicates, (2) previews the merge using virtual nodes, (3) executes the merge with property strategy "combine". Verify no relationships were lost.

### Exercise 4 — JDBC Synchronization (Intermediate)

Build a synchronization pipeline that: (1) reads new customers from PostgreSQL (created in the last 24 hours), (2) creates/updates Customer nodes in Neo4j, (3) creates PURCHASED relationships based on an orders table. Use named JDBC connections and batch processing.

### Exercise 5 — Trigger-Based Audit Trail (Advanced)

Implement a trigger that creates an AuditLog node whenever a Person node's properties are modified. The AuditLog should capture: the property that changed, the old value, the new value, and a timestamp. Test by updating several Person nodes and querying the audit trail.

### Exercise 6 — Dynamic Graph Builder (Advanced)

Build a procedure that reads a CSV file where each row specifies: source_label, source_id, relationship_type, target_label, target_id, and optional properties as JSON. Use `apoc.create.node` and `apoc.create.relationship` to dynamically construct the graph. This simulates a generic graph loader that does not require a fixed schema.

### Exercise 7 — Full ETL Pipeline (Expert)

Design and implement a complete ETL pipeline that: (1) reads data from a PostgreSQL database via JDBC, (2) enriches it by calling an external REST API, (3) creates a graph with multiple node types and relationship types, (4) exports the result as GraphML for visualization in Gephi. Use `apoc.periodic.iterate` for batch processing and error handling.

### Exercise 8 — Schema Migration (Expert)

You need to migrate a graph schema from flat properties to a normalized model:
- Before: `(:Person {name, city, country, company_name, job_title})`
- After: `(:Person)-[:LIVES_IN]->(:City)-[:IN_COUNTRY]->(:Country)` and `(:Person)-[:WORKS_AT {title}]->(:Company)`

Write a migration script using `apoc.refactor.categorize`, `apoc.periodic.iterate`, and verify the migration did not lose any data by comparing node and relationship counts before and after.

```cypher
// Hint: Migration sequence
// 1. Count existing data (pre-migration snapshot)
// 2. Extract City nodes from person.city property
// 3. Extract Country nodes from person.country property
// 4. Create City-[:IN_COUNTRY]->Country relationships
// 5. Extract Company nodes from person.company_name
// 6. Create Person-[:WORKS_AT]->Company relationships (preserve job_title)
// 7. Remove migrated properties from Person nodes
// 8. Verify counts match expected post-migration state
```

---

## Summary

APOC transforms Cypher from a query language into a full-fledged framework for managing the graph lifecycle — import, transformation, export, monitoring, and integration. Key capabilities:

- **Import/Export**: JSON, CSV, JDBC, GraphML — from files, HTTP APIs, and databases
- **Batch Processing**: `apoc.periodic.iterate` for memory-safe processing of millions of nodes
- **Refactoring**: Merge duplicates, rename labels/types/properties, extract/collapse nodes
- **Triggers**: Database-level event handlers for audit trails and cascading updates
- **Virtual Graphs**: Preview operations and build computed views without persisting
- **Utilities**: JSON/Map manipulation, string similarity, collection operations, date formatting
- **Conditional Execution**: `apoc.do.when` and `apoc.do.case` for branching logic in Cypher
- **Dynamic Cypher**: `apoc.cypher.run` for runtime-constructed queries (use parameters to avoid injection)
- **Introspection**: `apoc.meta.*` for schema discovery and graph statistics

APOC is indispensable for any production Neo4j deployment. The batch processing capabilities alone justify its installation.
