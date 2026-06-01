# Neo4j — Modellazione dei Dati per Grafi

## Principi Fondamentali della Modellazione a Grafo

La modellazione di un graph database differisce radicalmente dalla modellazione relazionale. Non si parte dall'entità, ma dalle **domande che il sistema deve rispondere** — le query guidano il modello, non il contrario.

**Processo di modellazione**:
1. Definire i casi d'uso e le query più critiche
2. Identificare le entità principali → **nodi**
3. Identificare le connessioni tra entità → **relazioni**
4. Decidere quali attributi appartengono ai nodi e quali alle relazioni
5. Valutare quando usare nodi intermedi (reification) invece di relazioni dirette

---

## Regole di Modellazione

### Nodi vs Relazioni vs Proprietà

**Un'entità diventa un nodo** quando:
- Ha molte proprietà
- È connessa a più altre entità
- Deve essere trovata per se stessa (lookup diretto)
- Ha relazioni proprie con altre entità

**Un'entità diventa una relazione** quando:
- Descrive una connessione tra due nodi
- Ha senso solo nel contesto di due entità connesse
- È binaria (non si connette a più di due nodi contemporaneamente)

**Un'entità diventa una proprietà** quando:
- È un semplice attributo scalare
- Non ha connessioni proprie
- Non verrà mai cercata per se stessa

### Esempio: Ordine in un E-Commerce

```cypher
// SBAGLIATO: troppe proprietà sulle relazioni
(:Customer)-[:PLACED {
    order_id: 123,
    date: date("2024-01-15"),
    total: 299.99,
    payment_method: "credit_card",
    shipping_address: "Via Roma 1",
    items: [...]
}]->(:Product)

// CORRETTO: l'ordine è un nodo (ha molte proprietà, è connesso a più entità)
(:Customer)-[:PLACED]->(:Order {
    id: 123,
    date: date("2024-01-15"),
    total: 299.99,
    status: "shipped"
})-[:CONTAINS {quantity: 2, unit_price: 149.99}]->(:Product {
    sku: "LAPTOP-001",
    name: "Laptop Pro"
}),
(:Order)-[:PAID_WITH {
    transaction_id: "tx-456",
    amount: 299.99
}]->(:PaymentMethod {type: "credit_card", last4: "1234"}),
(:Order)-[:SHIPS_TO]->(:Address {street: "Via Roma 1", city: "Milano"})
```

---

## Pattern di Modellazione Comuni

### Pattern 1: Relazione Temporale (SCD Type 2 su Grafo)

Per tracciare lo storico delle relazioni nel tempo:

```cypher
// Semplice (solo relazione corrente)
(:Employee)-[:WORKS_AT {since: date("2021-01-01")}]->(:Company)

// Con storico (ogni cambio di posizione è tracciato)
(:Employee)-[:HAD_ROLE {from: date("2019-01-01"), to: date("2021-01-01")}]->(:Role {title: "Junior Developer"})
(:Employee)-[:HAD_ROLE {from: date("2021-01-01"), to: null}]->(:Role {title: "Senior Developer"})

// Query per ruolo corrente
MATCH (e:Employee {name: "Alice"})-[r:HAD_ROLE]->(role:Role)
WHERE r.to IS NULL
RETURN role.title AS current_role;

// Query per ruolo a una data specifica
MATCH (e:Employee {name: "Alice"})-[r:HAD_ROLE]->(role:Role)
WHERE r.from <= date("2020-06-15") AND (r.to IS NULL OR r.to > date("2020-06-15"))
RETURN role.title;
```

### Pattern 2: Grafo Bipartito (User-Item per Recommendation)

```cypher
// Nodi
(:User {id: 1001, name: "Alice"})
(:Movie {id: 500, title: "Inception", year: 2010, genre: ["Sci-Fi", "Thriller"]})

// Interazioni come relazioni con peso
(:User)-[:WATCHED {timestamp: datetime(), rating: 4.5, completed: true}]->(:Movie)
(:User)-[:LIKED]->(:Movie)
(:User)-[:ADDED_TO_WATCHLIST {added_at: datetime()}]->(:Movie)

// Collaborative filtering query
MATCH (user:User {id: 1001})-[:LIKED]->(movie:Movie)<-[:LIKED]-(similar_user:User)
WHERE similar_user.id <> user.id
WITH similar_user, count(movie) AS shared_likes
ORDER BY shared_likes DESC
LIMIT 10
MATCH (similar_user)-[:LIKED]->(recommendation:Movie)
WHERE NOT (user)-[:LIKED|WATCHED]->(recommendation)
RETURN recommendation.title, count(*) AS score
ORDER BY score DESC
LIMIT 5;
```

### Pattern 3: Knowledge Graph con Tipi di Relazione Diversificati

```cypher
// Ontologia: Person può avere relazioni diverse con Organization
(:Person)-[:CEO_OF {since: date("2020-01-01")}]->(:Organization)
(:Person)-[:BOARD_MEMBER_OF {role: "Chairman"}]->(:Organization)
(:Person)-[:FOUNDED]->(:Organization {founded: date("2015-06-01")})
(:Person)-[:INVESTED_IN {amount: 500000, round: "Series A"}]->(:Organization)

// Query: chi ha multipli tipi di relazione con la stessa organizzazione?
MATCH (p:Person)-[r]->(o:Organization {name: "TechCorp"})
WITH p, o, collect(type(r)) AS roles
WHERE size(roles) > 1
RETURN p.name, roles;
```

### Pattern 4: Grafo Gerarchico (Albero di Categorie)

```cypher
// Categoria con auto-relazione gerarchica
CREATE (root:Category {id: 1, name: "Electronics"})
CREATE (laptops:Category {id: 2, name: "Laptops"})
CREATE (gaming:Category {id: 3, name: "Gaming Laptops"})
CREATE (root)-[:HAS_SUBCATEGORY]->(laptops)
CREATE (laptops)-[:HAS_SUBCATEGORY]->(gaming)

// Trova tutti i discendenti di una categoria (qualsiasi profondità)
MATCH (root:Category {name: "Electronics"})-[:HAS_SUBCATEGORY*]->(child:Category)
RETURN child.name, length(path) as depth
ORDER BY depth;

// Breadcrumb: percorso dalla radice a una categoria
MATCH path = (root:Category)-[:HAS_SUBCATEGORY*]->(target:Category {name: "Gaming Laptops"})
WHERE NOT ()-[:HAS_SUBCATEGORY]->(root)  -- root non ha genitori
RETURN [node IN nodes(path) | node.name] AS breadcrumb;
```

### Pattern 5: Reification (Hyper-Edge)

Quando una relazione deve connettersi a più di due entità, si usa un nodo intermedio (reification):

```cypher
// PROBLEMA: una transazione coinvolge sender, receiver, e una valuta
// Non si può modellare come relazione binaria

// SOLUZIONE: nodo Transaction come reification
(:Account {id: "ACC001"})-[:SENT]->(tx:Transaction {
    id: "TXN-456",
    amount: 1000.00,
    timestamp: datetime(),
    type: "wire_transfer"
})-[:RECEIVED_BY]->(:Account {id: "ACC002"}),
(tx)-[:IN_CURRENCY]->(:Currency {code: "EUR"}),
(tx)-[:FLAGGED_BY]->(:FraudAlert {reason: "unusual amount", score: 0.92})
```

---

## Indici e Vincoli

```cypher
// Indice su proprietà (lookup veloce)
CREATE INDEX person_name FOR (p:Person) ON (p.name);
CREATE INDEX person_email FOR (p:Person) ON (p.email);

// Indice composto
CREATE INDEX order_idx FOR (o:Order) ON (o.customer_id, o.status);

// Fulltext index (per ricerca testuale)
CREATE FULLTEXT INDEX product_search FOR (n:Product) ON EACH [n.name, n.description];
CALL db.index.fulltext.queryNodes("product_search", "wireless keyboard") YIELD node, score
RETURN node.name, score ORDER BY score DESC;

// UNIQUE constraint (implica indice)
CREATE CONSTRAINT person_email_unique FOR (p:Person) REQUIRE p.email IS UNIQUE;
CREATE CONSTRAINT order_id_unique FOR (o:Order) REQUIRE o.id IS UNIQUE;

// Mandatory property constraint (Enterprise)
CREATE CONSTRAINT person_name_mandatory FOR (p:Person) REQUIRE p.name IS NOT NULL;

// Node key constraint (chiave composita, Enterprise)
CREATE CONSTRAINT person_id_key FOR (p:Person) REQUIRE (p.first_name, p.last_name) IS NODE KEY;

// Visualizza indici e constraints
SHOW INDEXES;
SHOW CONSTRAINTS;
```

---

## Evoluzione del Schema

Neo4j è schema-optional — si può aggiungere proprietà e label senza ALTER TABLE. Ma una strategia di evoluzione è necessaria in produzione.

```cypher
// Aggiunta di una nuova proprietà a tutti i nodi di un tipo
MATCH (p:Person)
WHERE p.is_verified IS NULL
SET p.is_verified = false;

// Rinomina una proprietà (non esiste ALTER COLUMN — va fatto in due step)
MATCH (p:Person)
WHERE p.phone_number IS NOT NULL
SET p.phone = p.phone_number
REMOVE p.phone_number;

// Split di un label in due
MATCH (n:User)
WHERE n.user_type = "admin"
SET n:Admin
REMOVE n:User;

MATCH (n:User)
WHERE n.user_type = "customer"
SET n:Customer
REMOVE n:User;

// Migrazione di relazioni: rinominare un tipo di relazione
MATCH (a)-[r:OLD_REL_TYPE]->(b)
CREATE (a)-[:NEW_REL_TYPE]->(b)
DELETE r;
```

---

## Anti-Pattern nella Modellazione

### 1. Super-Nodi (Dense Nodes)

Un nodo con milioni di relazioni — es. un nodo `Country` connesso a tutti gli utenti di quel paese — crea colli di bottiglia nelle traversal.

```cypher
// SBAGLIATO: super-nodo Country con milioni di LIVES_IN
(:User)-[:LIVES_IN]->(:Country {code: "IT"})  -- 10M utenti in Italia

// CORRETTO per analytics: proprietà sul nodo
(:User {country: "IT"})  -- query con WHERE p.country = "IT"
// CORRETTO per navigazione: sharding del super-nodo
(:User)-[:LIVES_IN]->(:City)-[:IN_COUNTRY]->(:Country)
```

### 2. Proprietà Liste vs Nodi Separati

```cypher
// SBAGLIATO: lista di tag come proprietà stringa
(:Article {tags: "neo4j,graph,database"})

// CORRETTO: tag come nodi separati (permettono query su tag)
(:Article)-[:HAS_TAG]->(:Tag {name: "neo4j"})
(:Article)-[:HAS_TAG]->(:Tag {name: "graph"})

// Query: trova articoli con gli stessi tag
MATCH (a:Article)-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(b:Article)
WHERE a <> b
RETURN a.title, b.title, count(t) AS shared_tags
ORDER BY shared_tags DESC;
```

### 3. Tipo di Relazione Generico

```cypher
// SBAGLIATO: tipo di relazione generico con proprietà type
(:Person)-[:RELATED_TO {type: "FRIEND"}]->(:Person)
(:Person)-[:RELATED_TO {type: "COLLEAGUE"}]->(:Person)

// CORRETTO: tipi di relazione specifici (ClickHouse li memorizza diversamente,
// le query usano il pattern matching sull'arco invece del filtro sulle proprietà)
(:Person)-[:FRIEND_OF]->(:Person)
(:Person)-[:COLLEAGUE_OF]->(:Person)
```

Una modellazione corretta in Neo4j riduce drammaticamente la complessità delle query e migliora le performance del traversal — il pattern matching su tipi di relazione specifici è molto più efficiente del filtraggio su proprietà.

---

## Advanced Modeling Patterns

### Pattern 6: Event Sourcing on Graphs

Store events as nodes on a timeline chain, enabling temporal queries and audit trails.

```cypher
// Event chain per entity
(:Account {id: "ACC001"})
  -[:HAS_EVENT]->(e1:Event {type: "opened", ts: datetime("2024-01-01T10:00:00Z")})
  -[:NEXT]->(e2:Event {type: "deposited", ts: datetime("2024-01-02T14:00:00Z"), amount: 5000})
  -[:NEXT]->(e3:Event {type: "withdrawn", ts: datetime("2024-01-15T09:00:00Z"), amount: 1000})

// Query: reconstruct account state at a specific time
MATCH (a:Account {id: "ACC001"})-[:HAS_EVENT]->(start:Event)
MATCH path = (start)-[:NEXT*0..]->(event:Event)
WHERE event.ts <= datetime("2024-01-10T00:00:00Z")
WITH a, collect(event) AS events
RETURN a.id,
    reduce(balance = 0.0, e IN events |
        CASE e.type
            WHEN "deposited" THEN balance + COALESCE(e.amount, 0)
            WHEN "withdrawn" THEN balance - COALESCE(e.amount, 0)
            ELSE balance
        END
    ) AS balance_at_date;
```

### Pattern 7: Multi-Tenancy with Label Isolation

```cypher
// Each tenant gets a label prefix
(:TenantA_User {id: 1, name: "Alice"})
(:TenantB_User {id: 1, name: "Bob"})

// Or use a shared label with tenant property + index
CREATE INDEX user_tenant FOR (u:User) ON (u.tenant_id);

(:User {tenant_id: "A", id: 1, name: "Alice"})
(:User {tenant_id: "B", id: 1, name: "Bob"})

// Tenant-scoped query
MATCH (u:User {tenant_id: $tenantId})-[:KNOWS]->(friend:User {tenant_id: $tenantId})
RETURN u.name, friend.name;
```

### Pattern 8: Versioned Schema with Migration Nodes

```cypher
// Track schema changes as nodes in the graph itself
CREATE (v:SchemaMigration {
    version: 3,
    description: "Add email_verified property to Person",
    applied_at: datetime(),
    script: "MATCH (p:Person) WHERE p.email_verified IS NULL SET p.email_verified = false"
});

// Query: find applied and pending migrations
MATCH (m:SchemaMigration)
RETURN m.version, m.description, m.applied_at
ORDER BY m.version;
```

### Pattern 9: Weighted Multi-Graph for Recommendation Scoring

```cypher
// Multiple relationship types between the same pair, each contributing to a score
(:User)-[:VIEWED {count: 5, last: datetime()}]->(:Product)
(:User)-[:ADDED_TO_CART {count: 2}]->(:Product)
(:User)-[:PURCHASED {count: 1, amount: 49.99}]->(:Product)

// Composite affinity score
MATCH (u:User {id: $userId})-[r]->(p:Product)
WITH u, p,
    sum(CASE type(r)
        WHEN "VIEWED" THEN r.count * 1
        WHEN "ADDED_TO_CART" THEN r.count * 5
        WHEN "PURCHASED" THEN r.count * 10
        ELSE 0
    END) AS affinity_score
RETURN p.name, affinity_score
ORDER BY affinity_score DESC
LIMIT 20;
```

---

## Schema Design Decision Framework

### Decision Tree for Node vs Relationship vs Property

```
Does the concept have its own identity?
├── YES → Is it connected to multiple other entities?
│         ├── YES → Make it a NODE
│         └── NO  → Could still be a node, but consider if property suffices
└── NO  → Is it a connection between two entities?
          ├── YES → Does it have more than 2-3 attributes?
          │         ├── YES → Consider REIFICATION (intermediate node)
          │         └── NO  → Make it a RELATIONSHIP
          └── NO  → Make it a PROPERTY
```

### Cardinality Analysis Before Modeling

```cypher
// Estimate cardinalities before choosing model
// This helps predict super-node problems
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
WITH c, count(p) AS employee_count
RETURN c.name, employee_count
ORDER BY employee_count DESC
LIMIT 10;
// If top companies have >100K employees, the WORKS_AT relationship creates super-nodes
// Consider: (Person)-[:WORKS_AT]->(Department)-[:PART_OF]->(Company)
```

---

## Index Strategy Deep Dive

### Range Index vs Fulltext Index vs Point Index

| Index Type | Created With | Best For |
|-----------|-------------|----------|
| Range (B-tree) | `CREATE INDEX ... ON (n.prop)` | Exact match, range queries, STARTS WITH |
| Composite | `CREATE INDEX ... ON (n.prop1, n.prop2)` | Multi-property lookup |
| Fulltext (Lucene) | `CREATE FULLTEXT INDEX ...` | Natural language search, fuzzy match |
| Point (R-tree) | `CREATE POINT INDEX ...` | Spatial queries, distance, bounding box |
| Text | `CREATE TEXT INDEX ...` | String comparison, CONTAINS, ENDS WITH |
| Token Lookup | Auto-created | Label and relationship type lookup |

```cypher
// Text index for CONTAINS and ENDS WITH (Neo4j 5.x)
CREATE TEXT INDEX person_name_text FOR (p:Person) ON (p.name);

// Now this query uses the text index:
MATCH (p:Person) WHERE p.name CONTAINS "rossi" RETURN p;
MATCH (p:Person) WHERE p.name ENDS WITH "@gmail.com" RETURN p;

// Vector index for similarity search (Neo4j 5.11+)
CREATE VECTOR INDEX movie_embedding FOR (m:Movie) ON (m.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 256,
        `vector.similarity_function`: 'cosine'
    }
};

// Query: find movies similar to a target movie by embedding
MATCH (target:Movie {title: "Inception"})
CALL db.index.vector.queryNodes("movie_embedding", 10, target.embedding)
YIELD node AS similar, score
RETURN similar.title, score
ORDER BY score DESC;
```

### Index Monitoring and Maintenance

```cypher
// List all indexes with status
SHOW INDEXES
YIELD name, type, entityType, labelsOrTypes, properties, state, populationPercent
ORDER BY type, name;

// Drop an index
DROP INDEX person_name IF EXISTS;

// Check index usage in query plan
PROFILE MATCH (p:Person {email: "alice@example.com"}) RETURN p;
// Look for NodeIndexSeek in the plan — confirms index is used

// Analyze index selectivity (helps planner make better choices)
CALL db.stats.collect("GRAPH COUNTS");
```

---

## Troubleshooting Data Modeling Issues

### Problem 1: Super-Node Causing Slow Traversal

**Symptoms**: queries traversing through a popular node (e.g., `:Country {code: "US"}`) take seconds.

**Solution**: decompose the super-node into a hierarchy:
```cypher
// Instead of: (User)-[:LIVES_IN]->(Country)
// Use:        (User)-[:LIVES_IN]->(City)-[:IN_STATE]->(State)-[:IN_COUNTRY]->(Country)
```

### Problem 2: Circular Dependencies in MERGE

**Symptoms**: `MERGE` creates duplicate nodes when the identity properties are ambiguous.

**Solution**: always MERGE on a unique constraint, then SET additional properties.

### Problem 3: Property vs Node for Tags

**Symptoms**: filtering by tag requires scanning all nodes and parsing string arrays.

**Solution**: model tags as separate nodes connected by `:HAS_TAG` relationships:
```cypher
// Bad:  (:Article {tags: ["neo4j", "graph"]})
// Good: (:Article)-[:HAS_TAG]->(:Tag {name: "neo4j"})
```

### Problem 4: Time-Based Queries are Slow

**Solution**: create composite indexes on `(entity, timestamp DESC)` and use range predicates.

### Problem 5: Model Too Normalized (Too Many Hops)

**Symptoms**: simple queries require 5+ hops because every concept is a separate node.

**Solution**: denormalize properties that are only needed for display (not for traversal or filtering).

### Problem 6: Relationship Properties Growing Unbounded

**Symptoms**: relationship properties accumulate history (e.g., `interaction_history: [...]`).

**Solution**: use event nodes linked by `:NEXT` chain instead of array properties on relationships.

### Problem 7: Mixed Read/Write Contention on Hot Nodes

**Solution**: use read replicas for read queries, direct writes to the leader only.

### Problem 8: Schema Drift Between Environments

**Solution**: maintain migration scripts as Cypher files, version them in git, apply with `CALL {} IN TRANSACTIONS`.

### Problem 9: Labels Growing Without Bound

**Symptoms**: hundreds of labels created dynamically (one per tenant, one per date).

**Solution**: use properties for dynamic classification, not labels. Labels should represent stable domain concepts.

### Problem 10: APOC refactor.mergeNodes Losing Data

**Solution**: specify `properties: "combine"` to merge property maps instead of discarding.

---

## FAQ

**Q1: How many labels can a node have?**
A: A node can have any number of labels. However, each additional label adds overhead in the label store and the label scan store. Keep it under 10 labels per node for optimal performance.

**Q2: Should I use properties on relationships or intermediate nodes?**
A: Use properties on relationships for 2-3 scalar attributes (weight, timestamp, score). Use intermediate nodes (reification) when the "relationship" has its own identity, connects to more than two entities, or has more than 3-4 attributes.

**Q3: How do I model many-to-many relationships?**
A: In a graph, many-to-many is natural: just create relationships between the relevant nodes. No junction table is needed. If the relationship has significant attributes, consider reification.

**Q4: What happens if I add a property that doesn't exist on all nodes?**
A: Neo4j is schema-optional. Nodes with missing properties return NULL for those properties. This is expected behavior. Use `WHERE prop IS NOT NULL` to filter.

**Q5: Should I use separate databases for different domains?**
A: Use separate databases (Enterprise) when domains have zero overlap, different security requirements, or independent lifecycle. Use labels and relationship types within a single database when domains are interconnected.

**Q6: How do I handle versioning of graph data?**
A: Options: (a) temporal properties (`valid_from`, `valid_to`) on relationships, (b) event sourcing with event chains, (c) separate version nodes linked by `:NEXT_VERSION`. Choice depends on query patterns.

**Q7: Is there a limit on property value size?**
A: String properties can be up to 2 GB. Arrays can hold up to 2^31 elements. However, large properties degrade traversal performance. Keep properties small and model large data as separate nodes.

**Q8: How do I model inheritance?**
A: Use multiple labels: `(:Employee:Person)`, `(:Manager:Employee:Person)`. Query with the most specific label for type-specific queries.

**Q9: Can relationships have labels?**
A: Relationships have a single TYPE (not a label). Types are semantically equivalent to a single label. You cannot add multiple types to a relationship.

**Q10: How do I migrate from a star schema to a graph model?**
A: Fact tables become relationship nodes (reification), dimension tables become nodes, foreign keys become relationships. Start with the most important queries and model backward from them.

A well-designed graph model makes complex traversal queries simple and fast — the investment in modeling pays for itself in query clarity and performance over the life of the project.

---

## Polymorphic Relationships and Union Types

### Modeling Heterogeneous Targets

When a relationship can point to different node types, use multiple relationship types or a common label:

```cypher
// Approach 1: Different relationship types per target
(:User)-[:LIKES_POST]->(:Post)
(:User)-[:LIKES_COMMENT]->(:Comment)
(:User)-[:LIKES_PHOTO]->(:Photo)

// Approach 2: Common label + specific label (preferred for traversal)
(:Post:Content {type: "post"})
(:Comment:Content {type: "comment"})
(:Photo:Content {type: "photo"})
(:User)-[:LIKES]->(:Content)

// Query all liked content regardless of type
MATCH (u:User {id: $userId})-[:LIKES]->(c:Content)
RETURN c, labels(c) AS types
ORDER BY c.created_at DESC;

// Query only photos
MATCH (u:User {id: $userId})-[:LIKES]->(p:Photo)
RETURN p;
```

### Inheritance Hierarchies

```cypher
// Model inheritance with multiple labels
CREATE (e:Person:Employee:Manager {name: "Alice", department: "Engineering"});
CREATE (c:Person:Employee:Contractor {name: "Bob", agency: "TechStaff"});

// Query at any level of the hierarchy
MATCH (p:Person) RETURN p;          // All people
MATCH (e:Employee) RETURN e;        // All employees (managers + contractors)
MATCH (m:Manager) RETURN m;         // Only managers

// Index at the right level
CREATE INDEX FOR (e:Employee) ON (e.employeeId);
CREATE INDEX FOR (p:Person) ON (p.email);
```

---

## Temporal Modeling Patterns

### Bitemporal Data

Track both "when it happened" and "when we recorded it":

```cypher
// Bitemporal relationship
(:Employee)-[:WORKS_AT {
    valid_from: date("2023-01-15"),
    valid_to: date("2024-06-30"),
    recorded_at: datetime("2023-01-10T09:00:00Z"),
    recorded_by: "HR_SYSTEM"
}]->(:Company)

// Query: who worked at TechCorp as of 2023-06-01?
MATCH (e:Employee)-[r:WORKS_AT]->(c:Company {name: "TechCorp"})
WHERE r.valid_from <= date("2023-06-01")
  AND (r.valid_to IS NULL OR r.valid_to >= date("2023-06-01"))
RETURN e.name, r.valid_from, r.valid_to;

// Query: what did we know about assignments on 2023-03-01?
MATCH (e:Employee)-[r:WORKS_AT]->(c:Company)
WHERE r.recorded_at <= datetime("2023-03-01T00:00:00Z")
RETURN e.name, c.name, r.valid_from, r.valid_to;
```

### Event Chain Pattern

```cypher
// Linked list of events for an entity
(:Account)-[:LATEST_EVENT]->(e1:Event {type: "withdrawal", amount: 500})
(e1)-[:PREVIOUS]->(e2:Event {type: "deposit", amount: 1000})
(e2)-[:PREVIOUS]->(e3:Event {type: "account_opened"})

// Get last N events
MATCH (a:Account {id: $accountId})-[:LATEST_EVENT]->(e:Event)
MATCH path = (e)-[:PREVIOUS*0..9]->(older:Event)
RETURN nodes(path) AS events;

// Find event patterns (withdrawal after large deposit)
MATCH (a:Account)-[:LATEST_EVENT]->()-[:PREVIOUS*0..]->(w:Event {type: "withdrawal"})
      -[:PREVIOUS]->(d:Event {type: "deposit"})
WHERE w.amount > 5000 AND d.amount > 10000
  AND duration.between(d.timestamp, w.timestamp).hours < 24
RETURN a.id, d.amount AS deposited, w.amount AS withdrawn;
```

---

## Graph Refactoring Strategies

### Extract Node from Property

```cypher
// Before: city stored as property
MATCH (p:Person) WHERE p.city IS NOT NULL
WITH DISTINCT p.city AS cityName
MERGE (c:City {name: cityName});

// Create relationships
MATCH (p:Person), (c:City {name: p.city})
MERGE (p)-[:LIVES_IN]->(c);

// Remove old property (batch to avoid memory issues)
CALL apoc.periodic.iterate(
    'MATCH (p:Person) WHERE p.city IS NOT NULL RETURN p',
    'REMOVE p.city',
    {batchSize: 10000}
);
```

### Collapse Node into Property

```cypher
// When a node adds no traversal value, collapse it
// Before: (:Person)-[:HAS_STATUS]->(:Status {name: "active"})
// After:  (:Person {status: "active"})

MATCH (p:Person)-[:HAS_STATUS]->(s:Status)
SET p.status = s.name;

// Clean up
MATCH (s:Status)
WHERE NOT ()-[:HAS_STATUS]->(s)  // no remaining references
DETACH DELETE s;
```

### Split Relationship into Intermediate Node

```cypher
// Before: direct relationship with many properties
// (:Person)-[:PURCHASED {date, price, quantity, discount, payment_method, shipping}]->(:Product)

// After: intermediate Order node
MATCH (p:Person)-[r:PURCHASED]->(prod:Product)
CREATE (o:Order {
    date: r.date,
    price: r.price,
    quantity: r.quantity,
    discount: r.discount,
    payment_method: r.payment_method,
    shipping: r.shipping
})
CREATE (p)-[:PLACED]->(o)
CREATE (o)-[:CONTAINS]->(prod)
DELETE r;
```

---

## Model Validation and Testing

### Schema Assertions with Cypher

```cypher
// Validate: every Employee has exactly one department
MATCH (e:Employee)
WHERE size((e)-[:MEMBER_OF]->(:Department)) <> 1
RETURN e.name AS orphan_or_multi_dept, 
       size((e)-[:MEMBER_OF]->(:Department)) AS dept_count;
// Expected: 0 rows

// Validate: no circular REPORTS_TO
MATCH path = (e:Employee)-[:REPORTS_TO*1..20]->(e)
RETURN e.name, length(path) AS cycle_length;
// Expected: 0 rows

// Validate: all required properties present
MATCH (p:Person)
WHERE p.email IS NULL OR p.name IS NULL
RETURN p AS incomplete_person;
// Expected: 0 rows

// Property type validation (Neo4j 5.9+)
CREATE CONSTRAINT person_email_type FOR (p:Person) REQUIRE p.email IS :: STRING;
CREATE CONSTRAINT event_timestamp_type FOR (e:Event) REQUIRE e.timestamp IS :: ZONED DATETIME;
```

### Data Quality Queries

```cypher
// Find duplicate nodes that should be merged
MATCH (p1:Person), (p2:Person)
WHERE p1.email = p2.email AND id(p1) < id(p2)
RETURN p1.name, p2.name, p1.email AS duplicate_email;

// Find disconnected nodes (potential data quality issue)
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n) AS node_type, count(n) AS disconnected_count
ORDER BY disconnected_count DESC;

// Relationship consistency check
MATCH (e:Employee)-[r:WORKS_AT]->(c:Company)
WHERE r.since > date() OR r.since < date("1900-01-01")
RETURN e.name, c.name, r.since AS suspicious_date;
```

---

## Additional Troubleshooting

### 11. Slow MERGE on Large Datasets

**Symptom**: MERGE taking minutes for batch upserts.

**Root cause**: Missing unique constraint on the MERGE property. Without it, Neo4j scans all nodes with that label.

```cypher
// Fix: always create constraint before MERGE
CREATE CONSTRAINT FOR (p:Person) REQUIRE p.email IS UNIQUE;

// Then MERGE uses index lookup — O(log n) instead of O(n)
MERGE (p:Person {email: $email})
ON CREATE SET p.name = $name;
```

### 12. Relationship Direction Confusion

**Symptom**: Query returns 0 results despite data existing.

```cypher
// Debug: check actual direction
MATCH (a)-[r]->(b)
WHERE type(r) = "KNOWS" AND a.name = "Alice"
RETURN a.name, type(r), b.name;

// If direction is reversed, either fix data or query bidirectionally
MATCH (a:Person {name: "Alice"})-[:KNOWS]-(b:Person)  // no arrow = either direction
RETURN b.name;
```

---

## Additional FAQ

### 11. How many labels should a node have?

Typically 1-3. One primary label for the entity type, optional secondary labels for role or state. Avoid using labels as tags — that creates too many label combinations for the planner. Use properties or connected nodes for tags.

### 12. When should I use composite indexes?

When queries always filter on multiple properties together. Example: `WHERE p.country = "IT" AND p.age > 30` benefits from `CREATE INDEX FOR (p:Person) ON (p.country, p.age)`. If queries sometimes use just one property, create individual indexes instead.

### 13. How do I handle many-to-many with attributes?

Use an intermediate node when the relationship has rich data or its own identity. Example: an Enrollment node between Student and Course captures grade, semester, status. If only one or two properties, keep them on the relationship.

### 14. What is the maximum recommended property size?

Neo4j stores properties in fixed-size records. Strings over ~120 bytes spill into dynamic stores, which is fine but slower for full scans. Avoid storing large blobs (images, documents) as properties — store a reference/URL instead.

