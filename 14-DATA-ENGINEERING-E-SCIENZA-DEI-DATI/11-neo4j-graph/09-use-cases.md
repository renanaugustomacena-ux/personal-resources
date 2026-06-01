# Neo4j — Casi d'Uso e Pattern Applicativi

## Rilevamento di Frodi Finanziarie

Il fraud detection è uno dei casi d'uso più potenti per i graph database. I pattern fraudolenti emergono come connessioni inaspettate nel grafo che sarebbero invisibili in un database relazionale.

### Modello del Grafo

```cypher
// Schema
(:Account {id: "ACC001", type: "checking", opened: date("2023-01-15")}),
(:Person {id: "P001", name: "Mario Rossi", ssn: "RSSMRO80A01H501A"}),
(:Device {fingerprint: "abc123", type: "mobile", os: "iOS"}),
(:IP {address: "192.168.1.1", country: "IT"}),
(:Transaction {id: "TXN-456", amount: 5000.00, timestamp: datetime(), type: "wire"}),
(:Merchant {id: "MRC-001", name: "Unknown Shop", category: "retail"})

// Relazioni
(:Person)-[:OWNS]->(:Account)
(:Account)-[:INITIATED]->(:Transaction)
(:Transaction)-[:TO]->(:Account)
(:Person)-[:USED]->(:Device)
(:Device)-[:FROM_IP]->(:IP)
(:Transaction)-[:AT]->(:Merchant)
```

### Query di Rilevamento

```cypher
// Pattern 1: Primo Grado — Account condiviso tra più identità
MATCH (a:Account)<-[:OWNS]-(p1:Person), (a)<-[:OWNS]-(p2:Person)
WHERE p1 <> p2
RETURN a.id AS shared_account, p1.name, p2.name;

// Pattern 2: Cerchi di Frode — Transazioni circolari tra N account
MATCH path = (start:Account)-[:INITIATED]->(:Transaction)-[:TO*1..5]->(start)
WHERE length(path) > 2
RETURN path, length(path) AS cycle_length
ORDER BY cycle_length;

// Pattern 3: Device Condiviso tra Utenti Non Correlati
MATCH (p1:Person)-[:USED]->(d:Device)<-[:USED]-(p2:Person)
WHERE p1 <> p2
  AND NOT (p1)-[:RELATED_TO]-(p2)
WITH p1, p2, d, count(*) AS shared_sessions
WHERE shared_sessions > 3
RETURN p1.name, p2.name, d.fingerprint, shared_sessions
ORDER BY shared_sessions DESC;

// Pattern 4: Score di Rischio basato su Grafo
MATCH (acc:Account {id: $account_id})
WITH acc,
    size((acc)<-[:OWNS]-(:Person)-[:OWNS]->(:Account)-[:INITIATED]->(:Transaction {flagged: true})) AS flagged_connections,
    size((acc)-[:INITIATED]->(:Transaction)) AS total_transactions,
    size((acc)<-[:OWNS]-(:Person)-[:USED]->(:Device)<-[:USED]-(:Person {blacklisted: true})) AS blacklist_connections
RETURN
    acc.id,
    flagged_connections * 10 + blacklist_connections * 50 AS risk_score,
    flagged_connections,
    blacklist_connections,
    total_transactions;
```

---

## Knowledge Graph Aziendale

### Schema

```cypher
// Entità
(:Employee {id: "E001", name: "Alice", email: "alice@corp.com", department: "Engineering"})
(:Skill {name: "Python", category: "Programming"})
(:Project {id: "P001", name: "DataPlatform", status: "active", deadline: date("2024-06-30")})
(:Team {name: "DataEng", size: 8})
(:Document {id: "DOC-001", title: "Architecture Design", type: "spec"})

// Relazioni
(:Employee)-[:HAS_SKILL {level: "expert", certified: true}]->(:Skill)
(:Employee)-[:WORKS_ON {role: "Lead", since: date("2023-01-01")}]->(:Project)
(:Employee)-[:MEMBER_OF]->(:Team)
(:Employee)-[:AUTHORED]->(:Document)
(:Document)-[:REFERENCES]->(:Document)
(:Project)-[:REQUIRES]->(:Skill)
(:Employee)-[:REPORTS_TO]->(:Employee)
```

### Query Analitiche

```cypher
// Trova esperti di una skill per un progetto
MATCH (project:Project {id: "P001"})-[:REQUIRES]->(skill:Skill)
MATCH (expert:Employee)-[r:HAS_SKILL {level: "expert"}]->(skill)
WHERE NOT (expert)-[:WORKS_ON]->(project)  -- non già nel progetto
RETURN expert.name, skill.name, r.certified
ORDER BY skill.name, expert.name;

// Organigramma: riporta fino a 5 livelli sopra
MATCH path = (emp:Employee {name: "Alice"})-[:REPORTS_TO*1..5]->(manager:Employee)
WHERE NOT (manager)-[:REPORTS_TO]->()  -- manager senza superiore = CEO
RETURN [node IN nodes(path) | node.name] AS chain;

// Trova collo di bottiglia: chi ha più skill uniche e quanti progetti ne dipendono
MATCH (emp:Employee)-[:HAS_SKILL]->(skill:Skill)<-[:REQUIRES]-(project:Project)
WITH emp, skill, count(project) AS projects_depending
WITH emp, sum(projects_depending) AS criticality
ORDER BY criticality DESC
LIMIT 10
MATCH (emp)-[:HAS_SKILL]->(s)
RETURN emp.name, criticality, collect(s.name) AS skills;
```

---

## Raccomandazioni: Sistema E-Commerce

```cypher
// Collaborative Filtering: "Users like you also bought"
MATCH (user:User {id: $user_id})-[:PURCHASED]->(p:Product)
WITH user, collect(p) AS user_products

MATCH (user)-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(similar:User)
WHERE NOT (user)-[:PURCHASED]->(similar)
WITH user, similar, count(p) AS overlap
WHERE overlap >= 2
ORDER BY overlap DESC
LIMIT 20

MATCH (similar)-[:PURCHASED]->(rec:Product)
WHERE NOT rec IN user_products
  AND NOT (user)-[:VIEWED]->(rec)
WITH rec, count(distinct similar) AS supporters, collect(similar.id)[..3] AS example_users
WHERE supporters >= 2
RETURN rec.name, rec.price, supporters
ORDER BY supporters DESC
LIMIT 10;

// Content-based: prodotti simili per categoria e tag
MATCH (p:Product {id: $product_id})-[:IN_CATEGORY]->(cat:Category)
MATCH (p)-[:HAS_TAG]->(tag:Tag)
WITH p, collect(cat) AS categories, collect(tag) AS tags

MATCH (similar:Product)-[:IN_CATEGORY]->(cat:Category)
WHERE cat IN categories AND similar <> p
MATCH (similar)-[:HAS_TAG]->(tag:Tag)
WHERE tag IN tags
WITH similar, count(cat) AS cat_overlap, count(tag) AS tag_overlap
RETURN similar.name, similar.price,
       cat_overlap + tag_overlap * 2 AS similarity_score
ORDER BY similarity_score DESC
LIMIT 10;
```

---

## Gestione delle Dipendenze: Analisi di Impatto IT

```cypher
// Schema infrastruttura
(:Service {name: "order-service", criticality: "high"}),
(:Service {name: "payment-service", criticality: "critical"}),
(:Database {name: "orders-db", type: "postgresql"}),
(:Server {hostname: "db-primary", role: "master"}),
(:Datacenter {name: "DC-Milano"})

(:Service)-[:DEPENDS_ON {latency_ms: 50, required: true}]->(:Service)
(:Service)-[:READS_FROM]->(:Database)
(:Database)-[:RUNS_ON]->(:Server)
(:Server)-[:LOCATED_IN]->(:Datacenter)

// Analisi di impatto: se "payment-service" va down, cosa viene impattato?
MATCH (failed:Service {name: "payment-service"})<-[:DEPENDS_ON*]-(affected)
RETURN DISTINCT affected.name AS impacted_service,
       affected.criticality,
       length(shortestPath((affected)-[:DEPENDS_ON*]->(failed))) AS hops
ORDER BY hops, affected.criticality DESC;

// Trova single points of failure (servizi senza dipendenze ridondanti)
MATCH (s:Service)-[:DEPENDS_ON]->(dep:Service)
WITH dep, count(DISTINCT s) AS dependent_count
WHERE dependent_count > 2
  AND NOT (dep)-[:FAILOVER_TO]->(:Service)
RETURN dep.name AS spof, dep.criticality, dependent_count
ORDER BY dependent_count DESC;
```

---

## Social Network Analysis

```cypher
// Proietta un sottografo per analisi GDS
CALL gds.graph.project.cypher(
    'social',
    'MATCH (p:Person) RETURN id(p) AS id, p.name AS name',
    'MATCH (a:Person)-[r:KNOWS]->(b:Person)
     RETURN id(a) AS source, id(b) AS target, r.weight AS weight'
) YIELD graphName, nodeCount, relationshipCount;

// Trova le community (gruppi sociali naturali)
CALL gds.louvain.stream('social')
YIELD nodeId, communityId
WITH communityId, collect(gds.util.asNode(nodeId).name) AS members
WHERE size(members) > 3
RETURN communityId, members
ORDER BY size(members) DESC
LIMIT 5;

// Identifica gli influencer (alto PageRank + alto betweenness)
CALL gds.pageRank.stream('social')
YIELD nodeId, score AS pr_score
WITH gds.util.asNode(nodeId) AS person, pr_score

CALL gds.betweenness.stream('social')
YIELD nodeId, score AS bc_score
WHERE gds.util.asNode(nodeId) = person

RETURN person.name, pr_score, bc_score,
       pr_score + bc_score AS influence_score
ORDER BY influence_score DESC
LIMIT 20;
```

I graph database brillano in questi scenari perché trasformano query che richiederebbero JOIN multipli e ricorsivi in RDBMS in semplici traversal su strutture dati native — con performance che crescono con il grado locale dei nodi, non con la dimensione totale del dataset.

---

## Identity Resolution and Master Data Management

### Entity Resolution across Data Sources

```cypher
// Schema: multiple source records for the same real-world entity
(:RawRecord {source: "CRM", name: "Mario Rossi", email: "mario.rossi@email.com"}),
(:RawRecord {source: "ERP", name: "M. Rossi", email: "mrossi@company.com"}),
(:RawRecord {source: "HR", name: "Mario Rossi", employee_id: "E1234"}),
(:MasterEntity {golden_id: "ME-001", name: "Mario Rossi"})

(:RawRecord)-[:MATCHED_TO {confidence: 0.95, method: "email_domain"}]->(:MasterEntity)

// Fuzzy matching with APOC text similarity
MATCH (a:RawRecord), (b:RawRecord)
WHERE a <> b AND a.source <> b.source
WITH a, b, apoc.text.jaroWinklerDistance(a.name, b.name) AS name_sim
WHERE name_sim > 0.85
MERGE (me:MasterEntity {golden_id: apoc.create.uuid()})
MERGE (a)-[:MATCHED_TO {confidence: name_sim, method: "name_jw"}]->(me)
MERGE (b)-[:MATCHED_TO {confidence: name_sim, method: "name_jw"}]->(me);

// Query: find all source records for a master entity
MATCH (me:MasterEntity {golden_id: $id})<-[m:MATCHED_TO]-(raw:RawRecord)
RETURN raw.source, raw.name, raw.email, m.confidence, m.method
ORDER BY m.confidence DESC;
```

---

## Supply Chain and Logistics

```cypher
// Schema
(:Warehouse {id: "WH-01", location: point({latitude: 45.46, longitude: 9.19}), capacity: 50000}),
(:Product {sku: "SKU-A1", name: "Widget Alpha", weight_kg: 2.5}),
(:Supplier {id: "SUP-01", name: "ComponentCo", country: "DE"}),
(:Route {id: "R-001", mode: "truck"}),
(:Order {id: "ORD-5001", status: "pending", due_date: date("2024-03-15")})

(:Supplier)-[:SUPPLIES {lead_time_days: 14, unit_cost: 12.50}]->(:Product)
(:Warehouse)-[:STOCKS {quantity: 3000, last_restock: date()}]->(:Product)
(:Warehouse)-[:CONNECTED_TO {distance_km: 580, cost_per_kg: 0.15}]->(:Warehouse)
(:Order)-[:REQUIRES {quantity: 500}]->(:Product)
(:Order)-[:SHIPS_FROM]->(:Warehouse)

// Find cheapest supply chain for an order
MATCH (o:Order {id: "ORD-5001"})-[:REQUIRES]->(p:Product)
MATCH (s:Supplier)-[supply:SUPPLIES]->(p)
MATCH (wh:Warehouse)-[stock:STOCKS]->(p)
WHERE stock.quantity >= 500
WITH o, p, s, supply, wh, stock,
     supply.unit_cost * 500 AS material_cost
ORDER BY material_cost ASC
LIMIT 5
RETURN s.name, wh.id, material_cost, supply.lead_time_days, stock.quantity;

// Disruption analysis: if supplier SUP-01 goes offline, which orders are affected?
MATCH (s:Supplier {id: "SUP-01"})-[:SUPPLIES]->(p:Product)<-[:REQUIRES]-(o:Order)
WHERE o.status IN ["pending", "confirmed"]
  AND NOT EXISTS {
      MATCH (alt:Supplier)-[:SUPPLIES]->(p) WHERE alt <> s
  }
RETURN o.id, p.sku, o.due_date
ORDER BY o.due_date;
```

---

## Healthcare and Clinical Pathways

```cypher
// Schema
(:Patient {id: "PT-001", name: "Maria", dob: date("1985-03-20"), blood_type: "A+"}),
(:Condition {icd10: "J06.9", name: "Acute upper respiratory infection"}),
(:Medication {name: "Amoxicillin", atc_code: "J01CA04"}),
(:Procedure {code: "87.41", name: "CT scan of chest"}),
(:Encounter {id: "ENC-001", date: date("2024-01-15"), type: "outpatient"}),
(:Provider {npi: "1234567890", name: "Dr. Bianchi", specialty: "Internal Medicine"})

(:Patient)-[:HAS_CONDITION {onset: date(), status: "active"}]->(:Condition)
(:Encounter)-[:FOR_PATIENT]->(:Patient)
(:Encounter)-[:DIAGNOSED]->(:Condition)
(:Encounter)-[:PRESCRIBED]->(:Medication)
(:Encounter)-[:PERFORMED]->(:Procedure)
(:Encounter)-[:BY_PROVIDER]->(:Provider)
(:Medication)-[:INTERACTS_WITH {severity: "major"}]->(:Medication)
(:Medication)-[:TREATS]->(:Condition)

// Drug interaction check before prescribing
MATCH (pt:Patient {id: $patientId})<-[:FOR_PATIENT]-(:Encounter)-[:PRESCRIBED]->(current:Medication)
WITH pt, collect(current) AS current_meds
MATCH (new:Medication {name: $newMed})
UNWIND current_meds AS med
MATCH (med)-[interaction:INTERACTS_WITH]-(new)
RETURN med.name AS current_medication, new.name AS proposed_medication,
       interaction.severity, interaction.description;

// Clinical pathway: most common treatment sequence for a condition
MATCH (c:Condition {icd10: "J06.9"})<-[:DIAGNOSED]-(enc:Encounter)
MATCH (enc)-[:PRESCRIBED]->(med:Medication)
WITH med.name AS medication, count(*) AS frequency
ORDER BY frequency DESC
LIMIT 10
RETURN medication, frequency;

// Patient similarity: find patients with similar condition profiles
MATCH (pt:Patient {id: $patientId})-[:HAS_CONDITION]->(c:Condition)
WITH pt, collect(c) AS patient_conditions
MATCH (similar:Patient)-[:HAS_CONDITION]->(c:Condition)
WHERE similar <> pt AND c IN patient_conditions
WITH similar, count(c) AS shared_conditions, size(patient_conditions) AS total
WHERE shared_conditions >= total * 0.5
RETURN similar.id, shared_conditions, total
ORDER BY shared_conditions DESC LIMIT 10;
```

---

## Network and Telecom Infrastructure

```cypher
// Schema
(:Router {id: "R-NYC-01", location: "New York", model: "Cisco ASR 9000"}),
(:Switch {id: "SW-NYC-01", location: "New York", ports: 48}),
(:Fiber {id: "F-001", capacity_gbps: 100, length_km: 850}),
(:VPN {id: "VPN-001", customer: "CorpA", sla_latency_ms: 50}),
(:Datacenter {id: "DC-NYC", location: "New York", tier: 4})

(:Router)-[:CONNECTED_VIA {interface: "Te0/0/0", bandwidth_gbps: 10}]->(:Fiber)
(:Fiber)-[:CONNECTS_TO {interface: "Te0/0/1"}]->(:Router)
(:VPN)-[:TRAVERSES]->(:Router)
(:Router)-[:HOUSED_IN]->(:Datacenter)

// Network path analysis: find all paths between two routers
MATCH (src:Router {id: "R-NYC-01"}), (dst:Router {id: "R-LON-01"})
MATCH path = shortestPath((src)-[:CONNECTED_VIA|CONNECTS_TO*]-(dst))
RETURN [n IN nodes(path) WHERE n:Router | n.id] AS router_path,
       length(path) AS hops;

// Impact analysis: if router R-CHI-01 fails, which VPNs lose connectivity?
MATCH (failed:Router {id: "R-CHI-01"})
MATCH (vpn:VPN)-[:TRAVERSES]->(failed)
RETURN vpn.id, vpn.customer, vpn.sla_latency_ms;

// Find single points of failure in the backbone
MATCH (r:Router)
WHERE size((r)-[:CONNECTED_VIA]->()) <= 1  // only one uplink
  AND size((r)<-[:TRAVERSES]-(:VPN)) > 0   // carries VPN traffic
RETURN r.id, r.location,
       size((r)<-[:TRAVERSES]-(:VPN)) AS vpns_at_risk;

// Capacity planning: which links are over 80% utilized?
MATCH (a:Router)-[c:CONNECTED_VIA]->(f:Fiber)-[:CONNECTS_TO]->(b:Router)
WHERE c.current_utilization_gbps > f.capacity_gbps * 0.8
RETURN a.id, b.id, f.id,
       c.current_utilization_gbps, f.capacity_gbps,
       round(c.current_utilization_gbps / f.capacity_gbps * 100, 1) AS utilization_pct;
```

---

## Access Control and Compliance (IAM Graph)

```cypher
// Schema
(:User {id: "U001", name: "Alice", department: "Engineering"}),
(:Role {name: "developer", level: "standard"}),
(:Permission {action: "read", resource: "production-db"}),
(:Resource {id: "production-db", type: "database", classification: "restricted"}),
(:Policy {id: "POL-001", name: "PCI-DSS Access Control", status: "active"})

(:User)-[:HAS_ROLE {granted_by: "admin", since: date()}]->(:Role)
(:Role)-[:GRANTS]->(:Permission)
(:Permission)-[:ON_RESOURCE]->(:Resource)
(:Policy)-[:GOVERNS]->(:Resource)

// Effective permissions for a user (transitive through roles)
MATCH (u:User {id: "U001"})-[:HAS_ROLE]->(role:Role)-[:GRANTS]->(perm:Permission)-[:ON_RESOURCE]->(res:Resource)
RETURN res.id AS resource, collect(DISTINCT perm.action) AS actions;

// Separation of Duties: find users with conflicting roles
MATCH (u:User)-[:HAS_ROLE]->(r1:Role)-[:GRANTS]->(:Permission {action: "approve"})-[:ON_RESOURCE]->(res:Resource)
MATCH (u)-[:HAS_ROLE]->(r2:Role)-[:GRANTS]->(:Permission {action: "submit"})-[:ON_RESOURCE]->(res)
WHERE r1 <> r2
RETURN u.name, res.id, r1.name AS approve_role, r2.name AS submit_role;

// Compliance check: which users can access restricted resources without PCI-DSS training?
MATCH (u:User)-[:HAS_ROLE]->(:Role)-[:GRANTS]->(:Permission)-[:ON_RESOURCE]->(r:Resource {classification: "restricted"})
WHERE NOT (u)-[:COMPLETED]->(:Training {certification: "PCI-DSS"})
RETURN u.name, u.department, collect(DISTINCT r.id) AS accessible_restricted_resources;

// Access path visualization: how does user X reach resource Y?
MATCH path = (u:User {id: $userId})-[:HAS_ROLE]->(:Role)-[:GRANTS]->(:Permission)-[:ON_RESOURCE]->(r:Resource {id: $resourceId})
RETURN path;
```

---

## Real-Time Event Processing

```cypher
// Schema: event stream ingested into graph for correlation
(:Event {id: "EVT-001", type: "login", timestamp: datetime(), source: "web"}),
(:Event {id: "EVT-002", type: "api_call", endpoint: "/users", method: "GET"}),
(:Session {id: "SESS-001", started: datetime(), user_agent: "Chrome/120"}),
(:Alert {id: "ALT-001", severity: "high", rule: "brute_force_detected"})

(:Event)-[:IN_SESSION]->(:Session)
(:Event)-[:NEXT]->(:Event)  // temporal chain
(:Event)-[:TRIGGERED]->(:Alert)
(:Session)-[:BY_USER]->(:User)

// Detect brute force: >5 failed logins in 5 minutes from same IP
MATCH (e:Event {type: "login_failed"})-[:IN_SESSION]->(s:Session)
WHERE e.timestamp > datetime() - duration('PT5M')
WITH s.ip_address AS ip, count(e) AS failures, collect(e.timestamp) AS times
WHERE failures > 5
RETURN ip, failures, times[0] AS first_attempt, times[-1] AS last_attempt;

// Correlate events across sessions for a user
MATCH (u:User {id: $userId})<-[:BY_USER]-(:Session)<-[:IN_SESSION]-(e:Event)
WHERE e.timestamp > datetime() - duration('PT1H')
WITH e ORDER BY e.timestamp
RETURN e.type, e.timestamp, e.source, e.details
LIMIT 100;
```

---

## Troubleshooting

### 1. Fraud Detection Query Too Slow

**Symptom**: Cycle detection `MATCH path = (start)-[:INITIATED]->()-[:TO*1..5]->(start)` takes minutes.

**Fix**: Add index on Transaction.flagged, limit starting accounts, and use `PROFILE`:
```cypher
PROFILE
MATCH (start:Account {flagged: true})
MATCH path = (start)-[:INITIATED]->(:Transaction)-[:TO*1..4]->(start)
RETURN path LIMIT 100;
```

### 2. Knowledge Graph Returns Stale Data

**Symptom**: Recently added skills/roles not appearing in queries.

**Root cause**: Caching in the application layer or read-from-replica lag.

**Fix**: Use bookmarks for write-then-read patterns, or query the leader directly for time-sensitive reads.

### 3. Recommendation Engine Returns Same Results

**Symptom**: Collaborative filtering always recommends the same popular items.

**Fix**: Add diversity by penalizing popular items:
```cypher
MATCH (similar)-[:PURCHASED]->(rec:Product)
WHERE NOT rec IN user_products
WITH rec, count(DISTINCT similar) AS supporters,
     size((rec)<-[:PURCHASED]-()) AS total_purchases
RETURN rec.name, supporters,
       supporters * 1.0 / (total_purchases + 1) AS novelty_score
ORDER BY novelty_score DESC LIMIT 10;
```

### 4. Dependency Graph Impact Analysis Misses Indirect Dependencies

**Symptom**: Only direct dependents found, not transitive ones.

**Fix**: Use variable-length traversal with depth limit:
```cypher
MATCH (failed:Service {name: $serviceName})<-[:DEPENDS_ON*1..10]-(affected)
RETURN DISTINCT affected.name, affected.criticality;
```

### 5. Social Network Community Detection Takes Hours

**Symptom**: GDS Louvain on 100M node graph does not finish.

**Fix**: Use Label Propagation instead (faster, near-linear time). Or filter the projection to the relevant subgraph first.

### 6. Drug Interaction Check Returns False Negatives

**Symptom**: Known interactions not found.

**Root cause**: Interaction data incomplete or directionality wrong.

**Fix**: Always use undirected match for interactions:
```cypher
MATCH (med)-[:INTERACTS_WITH]-(new)  // no arrow = either direction
```

### 7. IAM Query Returns Overly Broad Permissions

**Symptom**: Users appear to have more permissions than intended.

**Fix**: Check for inherited permissions through group/role hierarchies. Add DENY rules for explicit exclusions.

### 8. Supply Chain Query Performance Degrades with Graph Size

**Symptom**: Queries that worked at 10K nodes crawl at 1M.

**Fix**: Add composite indexes on frequently filtered properties, use `LIMIT` early, start traversal from the most selective node.

### 9. Event Correlation Misses Cross-Session Patterns

**Symptom**: Brute force from same IP across different sessions not detected.

**Fix**: Correlate on IP property rather than session relationship:
```cypher
MATCH (e:Event {type: "login_failed"})
WHERE e.timestamp > datetime() - duration('PT5M')
WITH e.source_ip AS ip, count(e) AS failures
WHERE failures > 5
RETURN ip, failures;
```

### 10. Master Data Entity Resolution Creates Too Many False Matches

**Symptom**: Unrelated people merged into same master entity.

**Fix**: Use multi-attribute matching with threshold:
```cypher
WITH a, b,
     apoc.text.jaroWinklerDistance(a.name, b.name) AS name_sim,
     CASE WHEN a.email = b.email THEN 1.0 ELSE 0.0 END AS email_match,
     CASE WHEN a.phone = b.phone THEN 1.0 ELSE 0.0 END AS phone_match
WITH a, b, (name_sim * 0.4 + email_match * 0.4 + phone_match * 0.2) AS composite_score
WHERE composite_score > 0.8
// Only merge above composite threshold
```

---

## FAQ

### 1. Which use case benefits most from a graph database?

Any domain where relationships are as important as entities: fraud detection, recommendation engines, knowledge graphs, network infrastructure, access control. The common thread is that queries traverse connections rather than joining tables.

### 2. Can Neo4j handle time-series data?

Not optimally. Neo4j can store temporal data (events, timelines) but lacks columnar compression and time-bucketing that dedicated time-series databases provide. Use Neo4j for temporal relationships (event chains, causality), not for high-volume metric storage.

### 3. How do I integrate Neo4j with an existing RDBMS?

Common patterns: (1) ETL periodic sync from RDBMS to Neo4j for analytics, (2) APOC JDBC for real-time lookups, (3) CDC (Change Data Capture) with Kafka for streaming updates, (4) Neo4j ETL tool for one-time migration.

### 4. What is the maximum graph size Neo4j can handle?

Neo4j Enterprise can handle billions of nodes and relationships. The practical limit depends on hardware: RAM for working set, SSD for store files, network for cluster communication. Single-server deployments commonly run 1-10 billion relationships.

### 5. Should I use Neo4j or a relational database for my project?

Use Neo4j when: queries involve variable-depth traversals, data is highly connected, schema evolves frequently, pattern matching is core to the application. Use RDBMS when: data is tabular, transactions are mostly CRUD on individual records, strong consistency is paramount, team has RDBMS expertise.

### 6. How does Neo4j handle GDPR data deletion?

Use `DETACH DELETE` to remove nodes and all their relationships. For large-scale deletion, use `apoc.periodic.iterate` to batch the operation. Remember to also delete from backups if required by the GDPR request.

### 7. Can I run graph algorithms on real-time data?

GDS projections are snapshots — they do not update when the underlying graph changes. For near-real-time analytics, re-project periodically (e.g., every 5 minutes) or use streaming algorithms that process incoming edges incrementally.

### 8. How do I model hierarchical data (org chart, category tree)?

Use a self-referential relationship: `(:Category)-[:CHILD_OF]->(:Category)`. Query with variable-length patterns: `MATCH (root:Category {name: "Root"})<-[:CHILD_OF*]-(descendant)`. For deep hierarchies (1000+ levels), consider a materialized path property as a complement.

### 9. What is the difference between Neo4j Community and Enterprise?

Community: single database, no clustering, no RBAC, no encryption at rest, limited monitoring. Enterprise: multi-database, Causal Clustering, fine-grained RBAC, TDE, hot backup, online index creation, Prometheus metrics.

### 10. Can I use Neo4j for vector search (embeddings)?

Neo4j 5.11+ supports vector indexes natively. Store embeddings as float arrays and create a vector index for similarity search. This enables hybrid queries combining graph traversal with vector similarity — useful for RAG (Retrieval-Augmented Generation) and semantic search.

Graph databases fundamentally change how you model and query connected data. Each use case above demonstrates a pattern where the graph structure — nodes, relationships, and traversals — provides insights that would be prohibitively expensive or architecturally complex to achieve with relational or document databases.

---

## Genealogy and Family Trees

```cypher
// Schema
(:Person {name: "Giovanni", birth_year: 1950, gender: "M"}),
(:Person {name: "Maria", birth_year: 1953, gender: "F"})

(:Person)-[:PARENT_OF]->(:Person)
(:Person)-[:MARRIED_TO {year: 1975}]->(:Person)

// Find all ancestors (up to 10 generations)
MATCH (p:Person {name: $name})<-[:PARENT_OF*1..10]-(ancestor:Person)
RETURN ancestor.name, ancestor.birth_year,
       length(shortestPath((p)<-[:PARENT_OF*]-(ancestor))) AS generation;

// Find common ancestors of two people
MATCH (a:Person {name: "Alice"})<-[:PARENT_OF*1..10]-(ancestor:Person)
WITH a, collect(ancestor) AS a_ancestors
MATCH (b:Person {name: "Bob"})<-[:PARENT_OF*1..10]-(ancestor:Person)
WHERE ancestor IN a_ancestors
RETURN ancestor.name, ancestor.birth_year
ORDER BY ancestor.birth_year DESC LIMIT 5;

// Count descendants
MATCH (p:Person {name: "Giovanni"})-[:PARENT_OF*1..5]->(desc:Person)
RETURN count(DISTINCT desc) AS total_descendants;

// Siblings (share at least one parent)
MATCH (p:Person {name: "Alice"})<-[:PARENT_OF]-(parent:Person)-[:PARENT_OF]->(sibling:Person)
WHERE sibling <> p
RETURN DISTINCT sibling.name;
```

---

## Content Management and Knowledge Base

```cypher
// Schema
(:Article {id: "ART-001", title: "Graph Databases Intro", slug: "graph-db-intro",
           status: "published", created_at: datetime(), word_count: 2500}),
(:Author {id: "AUTH-001", name: "Alice", bio: "Graph enthusiast"}),
(:Tag {name: "neo4j"}),
(:Category {name: "Databases", slug: "databases"}),
(:Comment {id: "CMT-001", body: "Great article!", created_at: datetime()})

(:Author)-[:WROTE {published_at: datetime()}]->(:Article)
(:Article)-[:TAGGED]->(:Tag)
(:Article)-[:IN_CATEGORY]->(:Category)
(:Article)-[:REFERENCES]->(:Article)
(:Comment)-[:ON]->(:Article)
(:Comment)-[:BY_USER]->(:User)
(:Article)-[:NEXT_IN_SERIES]->(:Article)

// Related articles (share tags or references)
MATCH (a:Article {id: $articleId})-[:TAGGED]->(tag:Tag)<-[:TAGGED]-(related:Article)
WHERE related <> a AND related.status = "published"
WITH related, count(tag) AS shared_tags
ORDER BY shared_tags DESC LIMIT 5
RETURN related.title, related.slug, shared_tags;

// Author impact: articles, total views, comment engagement
MATCH (auth:Author {id: $authorId})-[:WROTE]->(a:Article)
OPTIONAL MATCH (a)<-[:ON]-(c:Comment)
WITH auth, count(DISTINCT a) AS articles, 
     sum(a.view_count) AS total_views,
     count(c) AS total_comments
RETURN auth.name, articles, total_views, total_comments,
       round(total_comments * 1.0 / articles, 1) AS avg_comments_per_article;

// Content graph: article dependency order (for learning paths)
MATCH path = (start:Article {id: "ART-001"})-[:REFERENCES*0..5]->(dep:Article)
RETURN [n IN nodes(path) | n.title] AS reading_order;
```

---

## Geospatial Analysis

```cypher
// Store locations as Neo4j point types
CREATE (r:Restaurant {
    name: "Trattoria Milano",
    location: point({latitude: 45.4642, longitude: 9.1900}),
    cuisine: "Italian",
    rating: 4.5
});

// Create point index for spatial queries
CREATE POINT INDEX FOR (r:Restaurant) ON (r.location);

// Find restaurants within 2km of a point
WITH point({latitude: 45.465, longitude: 9.185}) AS myLocation
MATCH (r:Restaurant)
WHERE point.distance(r.location, myLocation) < 2000  // meters
RETURN r.name, r.cuisine, r.rating,
       round(point.distance(r.location, myLocation)) AS distance_m
ORDER BY distance_m;

// Delivery zone analysis: which restaurants serve a customer area?
MATCH (r:Restaurant), (c:Customer {id: $customerId})
WHERE point.distance(r.location, c.location) <= r.delivery_radius_m
RETURN r.name, r.cuisine, r.rating
ORDER BY r.rating DESC;

// Route optimization between delivery stops (using Dijkstra on distance)
MATCH (origin:Address {id: "A001"})
MATCH (stop:DeliveryStop {route_id: "ROUTE-01"})
WITH origin, stop, point.distance(origin.location, stop.location) AS dist
ORDER BY dist
RETURN stop.address, dist;
```

---

## Cybersecurity Threat Intelligence

```cypher
// Schema
(:Indicator {type: "ip", value: "203.0.113.42", first_seen: datetime(), confidence: 0.95}),
(:Indicator {type: "domain", value: "evil.example.com"}),
(:Indicator {type: "file_hash", value: "abc123def456", hash_type: "sha256"}),
(:ThreatActor {name: "APT-29", aliases: ["Cozy Bear", "HAMMERTOSS"]}),
(:Malware {name: "SunburstBackdoor", family: "Sunburst"}),
(:Campaign {name: "SolarWinds Attack", start_date: date("2020-03-01")}),
(:Vulnerability {cve: "CVE-2024-0001", cvss: 9.8, product: "ExampleSoft"})

(:ThreatActor)-[:USES]->(:Malware)
(:Malware)-[:COMMUNICATES_WITH]->(:Indicator)
(:Campaign)-[:ATTRIBUTED_TO]->(:ThreatActor)
(:Campaign)-[:USES_TOOL]->(:Malware)
(:Campaign)-[:EXPLOITS]->(:Vulnerability)
(:Indicator)-[:RELATED_TO]->(:Indicator)

// Threat hunting: given a suspicious IP, find related indicators and campaigns
MATCH (ioc:Indicator {value: $suspiciousIp})
MATCH (ioc)-[:RELATED_TO*1..3]-(related:Indicator)
OPTIONAL MATCH (related)<-[:COMMUNICATES_WITH]-(:Malware)<-[:USES_TOOL]-(c:Campaign)
RETURN related.type, related.value, related.confidence,
       collect(DISTINCT c.name) AS campaigns;

// Attack surface mapping: which vulnerabilities affect our stack?
MATCH (v:Vulnerability)-[:AFFECTS]->(sw:Software)
WHERE sw.name IN $our_stack
RETURN v.cve, v.cvss, sw.name, v.patch_available
ORDER BY v.cvss DESC;

// MITRE ATT&CK mapping
MATCH (ta:ThreatActor {name: "APT-29"})-[:USES]->(tool)-[:IMPLEMENTS]->(technique:AttackTechnique)
RETURN technique.tactic, technique.technique_id, technique.name, tool.name
ORDER BY technique.tactic;
```

---

## Additional FAQ

### 11. How do I model multi-tenant data in a single graph?

Option 1: Separate databases per tenant (cleanest isolation). Option 2: Tenant label on all nodes with sub-graph security: `(:Person:TenantA {name: "Alice"})` — then DENY TRAVERSE on other tenants' labels.

### 12. Can Neo4j replace Elasticsearch for search?

No. Neo4j full-text indexes use Lucene internally but lack Elasticsearch's inverted index optimizations, aggregation framework, relevance scoring, and horizontal scaling for search. Use Neo4j full-text for graph-context search, Elasticsearch for general search.

### 13. How do I handle schema evolution?

Neo4j is schema-optional. Add new properties and labels without migration. For breaking changes (renaming properties, changing types), use `apoc.refactor` procedures to migrate data in batches.

### 14. What is the latency for a typical graph traversal?

Single-hop traversal with index lookup: <1ms. 3-hop variable-length with filtering: 1-10ms. Full graph analytics (PageRank on 10M nodes): seconds to minutes via GDS. These numbers assume warm page cache.


### 15. How do I model versioned documents in a graph?

Use a chain of version nodes:
```cypher
(:Document {id: "DOC-001"})-[:CURRENT_VERSION]->(v3:Version {number: 3, content: "..."})
(v3)-[:PREVIOUS]->(v2:Version {number: 2})
(v2)-[:PREVIOUS]->(v1:Version {number: 1})
```
Query the current version via `:CURRENT_VERSION`, or traverse `:PREVIOUS` for history. This avoids copying the entire document tree for each version.

### 16. Can I combine graph queries with full-text search?

Yes. Create a full-text index and chain it with graph traversal:
```cypher
CALL db.index.fulltext.queryNodes("article_ft", "graph database performance")
YIELD node AS article, score
MATCH (article)<-[:WROTE]-(author:Author)
RETURN article.title, score, author.name
ORDER BY score DESC LIMIT 10;
```

### 17. What are the best graph patterns for real-time recommendations?

Combine collaborative filtering (users who bought X also bought Y) with content similarity (shared tags/categories) and social signals (friends' purchases). Weight each signal and use a scoring function. Pre-compute heavy scores with GDS and store as properties for sub-millisecond reads.

