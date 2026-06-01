# Neo4j — Strumenti, Driver e Integrazioni

## Neo4j Browser e Bloom

### Neo4j Browser

Interfaccia web su `http://localhost:7474`. Strumento principale per sviluppo e debugging.

Feature chiave:
- Editor Cypher con syntax highlighting e autocompletion
- Visualizzazione grafica del risultato delle query (grafo interattivo)
- Plan visualizer per EXPLAIN/PROFILE
- Guide interattive (`:guide intro`)
- Multi-statement execution (`;` separatore)

```cypher
// Comandi speciali nel Browser
:server status          -- stato connessione
:server connect         -- cambia connessione
:history                -- storico query
:clear                  -- pulisce la console
:play movies            -- esempio interattivo
:help                   -- aiuto

// Parametri (stile REPL)
:param userId => 1001
MATCH (p:Person {id: $userId}) RETURN p;
```

### Neo4j Bloom

Strumento di data exploration visuale no-code. Permette a utenti non tecnici di navigare il grafo, creare pattern di ricerca e condividere perspettive.

---

## Driver: Python

```python
from neo4j import GraphDatabase, basic_auth, AsyncGraphDatabase
import asyncio

# Driver sincrono
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=basic_auth("neo4j", "password"),
    max_connection_pool_size=50,
    connection_timeout=30.0,
    max_retry_time=15.0,
    initial_retry_delay=1.0,
    retry_delay_multiplier=2.0,
    keep_alive=True,
    encrypted=False,   # True per bolt+s://
)

# Transazione esplicita (per write atomica multi-statement)
def create_user_with_company(tx, user_data, company_name):
    tx.run(
        "MERGE (c:Company {name: $name})",
        name=company_name
    )
    result = tx.run(
        "MERGE (p:Person {email: $email}) "
        "ON CREATE SET p += $props "
        "WITH p "
        "MATCH (c:Company {name: $company}) "
        "MERGE (p)-[:WORKS_AT]->(c) "
        "RETURN p",
        email=user_data["email"],
        props=user_data,
        company=company_name
    )
    return result.single()

with driver.session(database="neo4j") as session:
    record = session.execute_write(create_user_with_company,
                                   {"email": "alice@example.com", "name": "Alice"},
                                   "TechCorp")
    print(record["p"]["name"])

# Driver asincrono
async def async_query():
    async with AsyncGraphDatabase.driver("bolt://localhost:7687",
                                         auth=("neo4j", "password")) as driver:
        async with driver.session() as session:
            result = await session.run("MATCH (p:Person) RETURN p.name LIMIT 5")
            async for record in result:
                print(record["p.name"])

asyncio.run(async_query())
```

### Pydantic + Neo4j

```python
from pydantic import BaseModel
from datetime import date
from typing import Optional

class PersonNode(BaseModel):
    id: int
    name: str
    email: str
    age: int
    country: str = "IT"
    created_at: Optional[date] = None

def upsert_person(driver, person: PersonNode) -> PersonNode:
    with driver.session() as session:
        result = session.run(
            """
            MERGE (p:Person {id: $id})
            ON CREATE SET p += $props, p.created_at = date()
            ON MATCH  SET p += $props
            RETURN p
            """,
            id=person.id,
            props=person.model_dump(exclude={"id"})
        )
        record = result.single()
        return PersonNode(**record["p"])
```

---

## Driver: Java

```java
import org.neo4j.driver.*;
import org.neo4j.driver.summary.ResultSummary;

public class Neo4jExample {
    private final Driver driver;

    public Neo4jExample(String uri, String user, String password) {
        driver = GraphDatabase.driver(uri, AuthTokens.basic(user, password),
            Config.builder()
                .withMaxConnectionPoolSize(50)
                .withConnectionTimeout(30, TimeUnit.SECONDS)
                .withEncryption()
                .build()
        );
    }

    public void createPerson(String name, int age) {
        try (Session session = driver.session()) {
            session.executeWrite(tx -> {
                tx.run("MERGE (p:Person {name: $name}) SET p.age = $age",
                    Values.parameters("name", name, "age", age));
                return null;
            });
        }
    }

    // Reactive API (per applicazioni reactive)
    public Flux<String> findFriends(String personName) {
        return Flux.using(
            () -> driver.rxSession(),
            session -> session.run(
                "MATCH ({name: $name})-[:KNOWS]->(f) RETURN f.name",
                Values.parameters("name", personName)
            ).records(),
            RxSession::close
        ).map(record -> record.get("f.name").asString());
    }
}
```

---

## Spring Data Neo4j

```java
@Node("Person")
public class Person {
    @Id @GeneratedValue
    private Long id;

    @Property("name")
    private String name;

    @Property("email")
    private String email;

    @Relationship(type = "KNOWS", direction = Relationship.Direction.OUTGOING)
    private List<Person> friends = new ArrayList<>();

    @Relationship(type = "WORKS_AT")
    private Company company;
}

@Repository
public interface PersonRepository extends Neo4jRepository<Person, Long> {
    Optional<Person> findByEmail(String email);

    @Query("MATCH (p:Person {name: $name})-[:KNOWS*1..3]->(friend:Person) " +
           "RETURN DISTINCT friend")
    List<Person> findFriendsWithinDistance(@Param("name") String name);

    @Query("MATCH (p:Person)-[:KNOWS]->(f:Person) " +
           "WITH p, count(f) AS friends " +
           "WHERE friends >= $minFriends " +
           "RETURN p")
    List<Person> findWellConnected(@Param("minFriends") int minFriends);
}
```

---

## neo4j-admin: CLI di Gestione

```bash
# Informazioni sul database
neo4j-admin database info --database=neo4j

# Import massivo da CSV (database deve essere OFFLINE)
neo4j-admin database import full \
    --database=neo4j \
    --nodes=Person="people_header.csv,people.csv" \
    --nodes=Company="companies.csv" \
    --relationships=KNOWS="friendships.csv" \
    --delimiter=, \
    --array-delimiter=| \
    --skip-bad-relationships=true \
    --skip-duplicate-nodes=true \
    --verbose

# Formato dei file CSV per import massivo
# people_header.csv: id:ID(Person),name,age:int,email
# companies.csv: companyId:ID(Company),name,:LABEL
# friendships.csv: :START_ID(Person),:END_ID(Person),since:date

# Verifica consistenza del database
neo4j-admin database check --database=neo4j --verbose

# Memory recommendation
neo4j-admin server memory-recommendation \
    --database=neo4j \
    --memory=32g
# Output: heap e pagecache consigliati per 32 GB RAM
```

---

## Integrazione con Kafka (neo4j-streams)

```properties
# neo4j.conf con neo4j-streams plugin
streams.sink.enabled=true
streams.sink.topic.pattern.node.person-events=(:Person{*})
streams.sink.topic.pattern.relationship.knows-events=(:Person)-[:KNOWS]->(:Person)
streams.source.enabled=true
streams.source.topic.nodes=neo4j.nodes
streams.source.topic.relationships=neo4j.relationships
kafka.bootstrap.servers=kafka1:9092,kafka2:9092
kafka.group.id=neo4j-streams-consumer
```

---

## Integrazione con Spark (GraphFrames / Neo4j Connector)

```python
from pyspark.sql import SparkSession
from graphframes import GraphFrame

spark = SparkSession.builder \
    .config("spark.jars.packages",
            "neo4j-contrib:neo4j-connector-apache-spark_2.12:5.2.0_for_spark_3") \
    .getOrCreate()

# Lettura nodi
persons_df = spark.read.format("org.neo4j.spark.DataSource") \
    .option("url", "bolt://localhost:7687") \
    .option("authentication.type", "basic") \
    .option("authentication.basic.username", "neo4j") \
    .option("authentication.basic.password", "password") \
    .option("labels", ":Person") \
    .load()

# Lettura relazioni
knows_df = spark.read.format("org.neo4j.spark.DataSource") \
    .option("relationship", "KNOWS") \
    .option("relationship.source.labels", ":Person") \
    .option("relationship.target.labels", ":Person") \
    .load()

# Analisi con GraphFrames
gf = GraphFrame(
    persons_df.select("<id>".alias("id"), "name"),
    knows_df.select("<source.id>".alias("src"), "<target.id>".alias("dst"))
)

# PageRank via Spark
pagerank = gf.pageRank(resetProbability=0.15, maxIter=10)
pagerank.vertices.orderBy("pagerank", ascending=False).show(10)
```

Gli strumenti e le integrazioni di Neo4j coprono il ciclo completo di sviluppo — dal browser per l'esplorazione interattiva, ai driver per le applicazioni, fino a Spark per l'analisi su scala.

---

## Neo4j Desktop

Desktop application for development environments. Bundles Neo4j server, Browser, and Bloom in a single installer.

Key features:
- One-click database creation and management
- Plugin marketplace (APOC, GDS, Graph Apps)
- Multiple project/database management
- Database import/export via GUI
- Graph App ecosystem (Halin monitoring, GraphQL Architect, etc.)

```bash
# Install on Linux (AppImage)
wget https://neo4j.com/artifact.php?name=neo4j-desktop-offline-1.5.9-x86_64.AppImage
chmod +x neo4j-desktop-*.AppImage
./neo4j-desktop-*.AppImage

# Install on macOS (dmg)
# Download from https://neo4j.com/download/
open neo4j-desktop-*.dmg
```

---

## Cypher Shell (CLI Client)

```bash
# Connect to local instance
cypher-shell -u neo4j -p password

# Connect to remote with TLS
cypher-shell -a bolt+s://remote-host:7687 -u neo4j -p password

# Execute query non-interactively
cypher-shell -u neo4j -p password \
    "MATCH (p:Person) RETURN p.name LIMIT 5"

# Execute file
cypher-shell -u neo4j -p password < import-script.cypher

# Output format (plain, verbose, or auto)
cypher-shell -u neo4j -p password --format plain \
    "MATCH (p:Person) RETURN p.name, p.email"

# Connect to specific database
cypher-shell -u neo4j -p password -d analytics

# With parameters
cypher-shell -u neo4j -p password \
    -P "name => 'Alice'" \
    "MATCH (p:Person {name: \$name}) RETURN p"
```

### Scripting with Cypher Shell

```bash
#!/bin/bash
# Automated data quality check
RESULT=$(cypher-shell -u neo4j -p "$NEO4J_PASSWORD" --format plain \
    "MATCH (p:Person) WHERE p.email IS NULL RETURN count(p) AS orphans")

ORPHAN_COUNT=$(echo "$RESULT" | tail -1)
if [ "$ORPHAN_COUNT" -gt 0 ]; then
    echo "WARNING: $ORPHAN_COUNT Person nodes without email"
    # Send alert
fi
```

---

## Driver: JavaScript / TypeScript

```typescript
import neo4j, { Driver, Session, ManagedTransaction } from 'neo4j-driver';

const driver: Driver = neo4j.driver(
    'bolt://localhost:7687',
    neo4j.auth.basic('neo4j', 'password'),
    {
        maxConnectionPoolSize: 50,
        connectionAcquisitionTimeout: 60000,
        maxTransactionRetryTime: 30000,
        logging: neo4j.logging.console('warn'),
        encrypted: false,
    }
);

// Managed transaction (auto-retry on transient errors)
async function findPerson(name: string) {
    const session: Session = driver.session({ database: 'neo4j' });
    try {
        const result = await session.executeRead(
            async (tx: ManagedTransaction) => {
                const res = await tx.run(
                    'MATCH (p:Person {name: $name})-[:KNOWS]->(friend) RETURN friend.name AS friendName',
                    { name }
                );
                return res.records.map(r => r.get('friendName'));
            }
        );
        return result;
    } finally {
        await session.close();
    }
}

// Write transaction
async function createPerson(name: string, email: string) {
    const session = driver.session({ database: 'neo4j' });
    try {
        await session.executeWrite(async (tx) => {
            await tx.run(
                'MERGE (p:Person {email: $email}) ON CREATE SET p.name = $name, p.created = datetime()',
                { name, email }
            );
        });
    } finally {
        await session.close();
    }
}

// Cleanup on shutdown
process.on('SIGTERM', async () => {
    await driver.close();
});
```

---

## Driver: Go

```go
package main

import (
    "context"
    "fmt"
    "github.com/neo4j/neo4j-go-driver/v5/neo4j"
)

func main() {
    ctx := context.Background()
    driver, err := neo4j.NewDriverWithContext(
        "bolt://localhost:7687",
        neo4j.BasicAuth("neo4j", "password", ""),
    )
    if err != nil {
        panic(err)
    }
    defer driver.Close(ctx)

    // Verify connectivity
    err = driver.VerifyConnectivity(ctx)
    if err != nil {
        panic(err)
    }

    // Read transaction
    session := driver.NewSession(ctx, neo4j.SessionConfig{DatabaseName: "neo4j"})
    defer session.Close(ctx)

    friends, err := neo4j.ExecuteRead(ctx, session,
        func(tx neo4j.ManagedTransaction) ([]string, error) {
            result, err := tx.Run(ctx,
                "MATCH (p:Person {name: $name})-[:KNOWS]->(f) RETURN f.name AS name",
                map[string]any{"name": "Alice"},
            )
            if err != nil {
                return nil, err
            }

            var names []string
            for result.Next(ctx) {
                names = append(names, result.Record().Values[0].(string))
            }
            return names, result.Err()
        },
    )
    if err != nil {
        panic(err)
    }
    fmt.Println("Friends:", friends)
}
```

---

## GraphQL Integration (Neo4j GraphQL Library)

```typescript
import { Neo4jGraphQL } from '@neo4j/graphql';
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import neo4j from 'neo4j-driver';

const typeDefs = `#graphql
    type Person {
        name: String!
        email: String! @unique
        age: Int
        knows: [Person!]! @relationship(type: "KNOWS", direction: OUT)
        worksAt: Company @relationship(type: "WORKS_AT", direction: OUT)
    }

    type Company {
        name: String! @unique
        employees: [Person!]! @relationship(type: "WORKS_AT", direction: IN)
    }
`;

const driver = neo4j.driver(
    'bolt://localhost:7687',
    neo4j.auth.basic('neo4j', 'password')
);

const neoSchema = new Neo4jGraphQL({ typeDefs, driver });
const server = new ApolloServer({
    schema: await neoSchema.getSchema(),
});

const { url } = await startStandaloneServer(server, {
    context: async ({ req }) => ({ req }),
    listen: { port: 4000 },
});
console.log(`GraphQL server at ${url}`);
```

```graphql
# Auto-generated queries and mutations
query {
    people(where: { name: "Alice" }) {
        name
        email
        knows {
            name
        }
        worksAt {
            name
        }
    }
}

mutation {
    createPeople(input: [{
        name: "Bob"
        email: "bob@example.com"
        age: 32
        worksAt: { connect: { where: { node: { name: "TechCorp" }}}}
    }]) {
        people {
            name
            email
        }
    }
}
```

---

## Halin: Cluster Monitoring GUI

```bash
# Install as Graph App in Neo4j Desktop
# Or run standalone
npx halin
# Opens at http://localhost:3000

# Provides:
# - Real-time cluster member status
# - JVM memory, GC, thread pools
# - Page cache hit ratio
# - Store file sizes
# - Active queries and transactions
# - Configuration diff across cluster members
```

---

## Neo4j ETL Tool

```bash
# Migrate from RDBMS to Neo4j
neo4j-etl export \
    --rdbms:url jdbc:postgresql://pg:5432/mydb \
    --rdbms:user postgres \
    --rdbms:password secret \
    --destination /tmp/neo4j-import/ \
    --mapping-file /tmp/mapping.json \
    --force

# Generated mapping maps tables to nodes, FK to relationships
# Review and customize mapping.json before final import

neo4j-admin database import full \
    --database=neo4j \
    --nodes=Person="/tmp/neo4j-import/person.csv" \
    --relationships=KNOWS="/tmp/neo4j-import/knows.csv"
```

---

## Troubleshooting

### 1. Neo4j Browser Cannot Connect

**Symptom**: Browser loads but "Server not available" error.

**Fix**:
```bash
# Check if Neo4j is running
systemctl status neo4j
# Check Bolt port is listening
ss -tlnp | grep 7687
# Check logs
tail -50 /var/log/neo4j/neo4j.log
```

Verify `server.bolt.listen_address` is not restricted to localhost when Browser is remote.

### 2. Python Driver "ServiceUnavailable" Error

**Symptom**: `neo4j.exceptions.ServiceUnavailable: Failed to establish connection`.

**Fix**: Check URI scheme matches TLS config:
```python
# No TLS
driver = GraphDatabase.driver("bolt://host:7687", ...)
# With TLS
driver = GraphDatabase.driver("bolt+s://host:7687", ...)
# Self-signed TLS
driver = GraphDatabase.driver("bolt+ssc://host:7687", ...)
```

### 3. Connection Pool Exhaustion

**Symptom**: `ClientError: Unable to acquire connection from pool within configured timeout`.

**Fix**: Sessions are leaking. Always close sessions in finally/with:
```python
# WRONG — session leaks on exception
session = driver.session()
result = session.run("...")
# session.close() never called if run() throws

# CORRECT
with driver.session() as session:
    result = session.run("...")
```

Also increase pool size if legitimate concurrency is high:
```python
driver = GraphDatabase.driver(uri, auth=auth, max_connection_pool_size=100)
```

### 4. Slow Bulk Import via Driver

**Symptom**: Inserting millions of rows takes hours.

**Fix**: Use `UNWIND` with batched parameters instead of individual statements:
```python
# SLOW: one tx per row
for row in data:
    session.run("CREATE (p:Person {name: $name})", name=row["name"])

# FAST: batched UNWIND
BATCH_SIZE = 5000
for i in range(0, len(data), BATCH_SIZE):
    batch = data[i:i+BATCH_SIZE]
    session.run(
        "UNWIND $rows AS row CREATE (p:Person) SET p = row",
        rows=batch
    )
```

### 5. GraphQL Schema Generation Fails

**Symptom**: `Neo4jGraphQL.getSchema()` throws validation errors.

**Fix**: Ensure `@relationship` directives match actual graph structure. The `type` must match the relationship type exactly (case-sensitive, UPPER_SNAKE convention).

### 6. neo4j-admin import Rejects CSV

**Symptom**: "Missing header" or "Too many columns" errors.

**Fix**: Verify header format matches Neo4j import requirements:
```csv
# Correct node header
:ID(Person),name,email,age:int,:LABEL
# Correct relationship header
:START_ID(Person),:END_ID(Person),since:date,:TYPE
```

### 7. Driver Creates Too Many Connections

**Symptom**: "Too many open files" or connection count grows unbounded.

**Fix**: Create ONE driver instance per application, not per request:
```python
# WRONG — creates driver per request
def handle_request():
    driver = GraphDatabase.driver(uri, auth=auth)
    session = driver.session()
    # ...

# CORRECT — global driver, sessions per request
driver = GraphDatabase.driver(uri, auth=auth)

def handle_request():
    with driver.session() as session:
        # ...
```

### 8. APOC Not Available in Aura

**Symptom**: `apoc.load.jdbc` not found on Aura.

**Fix**: Aura includes APOC Core only. Extended procedures (JDBC, spatial, NLP) are not available. Use Aura's built-in import tools or pre-process data before loading.

### 9. Cypher Shell Hangs on Large Result Sets

**Symptom**: `cypher-shell` freezes when returning millions of rows.

**Fix**: Always use `LIMIT` or pipe output to file:
```bash
cypher-shell -u neo4j -p password --format plain \
    "MATCH (p:Person) RETURN p.name LIMIT 100" > output.txt
```

### 10. Spring Data Neo4j N+1 Query Problem

**Symptom**: Loading an entity with relationships triggers separate queries per relationship.

**Fix**: Use `@Query` with explicit Cypher to fetch the full subgraph in one query:
```java
@Query("MATCH (p:Person {id: $id})-[:KNOWS]->(f:Person) " +
       "OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company) " +
       "RETURN p, collect(f) AS friends, c")
Person findWithRelationships(@Param("id") Long id);
```

---

## FAQ

### 1. Which driver should I use for my language?

Use the official Neo4j driver for your language (Python, Java, JavaScript/TypeScript, Go, .NET). These are maintained by Neo4j and support all features including routing, transactions, and bookmarks. Community drivers exist for Rust, Ruby, PHP, and others but may lag behind on features.

### 2. Can I use Neo4j with REST API instead of a driver?

Neo4j has an HTTP API, but the Bolt protocol (used by drivers) is significantly faster — binary protocol, streaming results, connection pooling, automatic failover. Use the HTTP API only for simple scripting or when a driver is not available.

### 3. What is the Neo4j GraphQL Library vs Cypher-GraphQL?

The `@neo4j/graphql` library auto-generates Cypher from GraphQL type definitions. You define types with `@relationship` directives and get CRUD operations, filtering, sorting, and pagination automatically. No manual resolver writing for standard operations.

### 4. How do I monitor Neo4j in production?

Use the Prometheus metrics endpoint (`server.metrics.prometheus.enabled=true`) with Grafana dashboards. Key metrics: page cache hit ratio, transaction commit rate, JVM heap usage, Bolt connection count, query execution time. Neo4j provides official Grafana dashboard templates.

### 5. Can I use ORM-style mapping with Neo4j?

Spring Data Neo4j provides JPA-like annotations for Java. For Python, use `neomodel` or manual Pydantic mapping. For JavaScript, the GraphQL library provides schema-first mapping. Pure Cypher is often more efficient than ORM abstractions for complex graph queries.

### 6. How do I handle connection retries?

The official drivers handle transient error retries automatically when using `executeRead`/`executeWrite`. Configure retry behavior:
```python
driver = GraphDatabase.driver(uri, auth=auth,
    max_transaction_retry_time=30.0,  # seconds
    initial_retry_delay=1.0,
    retry_delay_multiplier=2.0
)
```

### 7. What is the Bolt protocol?

Bolt is Neo4j's custom binary protocol for database communication. It supports connection pooling, streaming results, routing in clusters, and typed values. Bolt v5 (Neo4j 5+) adds improved type system and notification support.

### 8. Can I embed Neo4j in my application?

Neo4j embedded mode (Java only) runs the database within your JVM process. Use it for unit testing or single-user desktop applications. For server applications, always use the client-server architecture with the Bolt driver.

### 9. How do I version-control Cypher migrations?

Use tools like `neo4j-migrations` (Java), `graphaware/neo4j-migrations` (CLI), or custom scripts with version tracking:
```cypher
// Track applied migrations
CREATE CONSTRAINT FOR (m:Migration) REQUIRE m.version IS UNIQUE;
MERGE (m:Migration {version: "001"})
ON CREATE SET m.applied_at = datetime(), m.description = "Initial schema";
```

### 10. What is the maximum number of concurrent connections?

Default Bolt thread pool is 400 connections. Tune with `server.bolt.thread_pool_max_size`. Each connection uses ~64KB of memory. For 1000 concurrent connections, budget ~64MB just for connection overhead plus JVM thread stacks.

Neo4j's tooling ecosystem spans interactive development (Browser, Desktop, Bloom), programmatic access (drivers in 5+ languages), operational management (neo4j-admin, Cypher Shell), and integration layers (GraphQL, ETL, Kafka connectors) — providing comprehensive coverage for every stage of the graph database lifecycle.

### Performance Comparison of Access Methods

| Method | Latency | Throughput | Best For |
|--------|---------|------------|----------|
| Bolt driver | ~1ms | 10K+ qps | Application backends |
| HTTP API | ~5ms | 2K qps | Simple scripts, REST clients |
| Cypher Shell | ~10ms | Batch | Admin scripts, migrations |
| GraphQL | ~15ms | 5K qps | API layer with auto-generated queries |
| Browser | ~50ms | Interactive | Development, exploration |

