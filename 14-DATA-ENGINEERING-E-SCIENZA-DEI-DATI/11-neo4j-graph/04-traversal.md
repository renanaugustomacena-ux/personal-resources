# Neo4j — Graph Traversal and Pathfinding Algorithms

## Foundations of Graph Traversal

Graph traversal is the process of visiting nodes in a graph by following relationships. Unlike relational databases where you execute joins across tables, graph databases traverse pointer-like connections between nodes stored adjacently on disk. This is called **index-free adjacency** — the cost of traversal depends on the local neighborhood size, not the total graph size.

Two fundamental traversal strategies underpin every graph algorithm:

### Breadth-First Search (BFS)

BFS explores all neighbors at the current depth before moving to nodes at the next depth level. It uses a queue (FIFO) internally.

**Properties:**
- Finds the shortest path in unweighted graphs (guaranteed)
- Memory usage grows with the breadth of the graph at each level
- Explores level by level — depth 1, then depth 2, then depth 3

**When to use BFS:**
- Shortest path queries (unweighted)
- Finding all nodes within N hops
- Social network "degrees of separation"
- Impact analysis (what is affected within N steps)

```cypher
// BFS behavior: shortestPath in Cypher uses BFS under the hood
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
MATCH path = shortestPath((a)-[:KNOWS*..10]-(b))
RETURN path, length(path) AS hops;
```

### Depth-First Search (DFS)

DFS explores as far as possible along each branch before backtracking. It uses a stack (LIFO) internally.

**Properties:**
- Does NOT guarantee shortest path
- Memory usage is proportional to the maximum depth
- Can get trapped in deep branches on infinite or very deep graphs without depth limits

**When to use DFS:**
- Finding any path between two nodes (not necessarily shortest)
- Cycle detection
- Topological sorting
- Exhaustive exploration (listing all paths)

```cypher
// DFS-like behavior: variable-length patterns without shortestPath
// Cypher's planner may use DFS internally for pattern matching
MATCH path = (a:Person {name: "Alice"})-[:KNOWS*1..5]->(b:Person {name: "Bob"})
RETURN path
LIMIT 1;
```

### BFS vs DFS — Decision Matrix

| Criterion | BFS | DFS |
|-----------|-----|-----|
| Shortest path guarantee | Yes (unweighted) | No |
| Memory usage | O(branching_factor^depth) | O(max_depth) |
| Best for wide/shallow graphs | Yes | No |
| Best for deep/narrow graphs | No | Yes |
| Cycle handling | Naturally avoids revisiting | Needs visited-set |
| Cypher default for shortestPath | Yes | No |

---

## Shortest Path in Cypher

### shortestPath — Single Shortest Path

The `shortestPath()` function returns a single shortest path between two nodes using BFS. It is the most commonly used pathfinding function in Cypher.

```cypher
// Basic shortest path between two named nodes
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
MATCH path = shortestPath((a)-[:KNOWS*..10]-(b))
RETURN path, length(path) AS hops;
```

**Key behaviors:**
- Uses BFS — guaranteed shortest in terms of hop count
- The `*..10` sets a maximum depth — always set this to avoid unbounded exploration
- Returns NULL if no path exists
- Undirected by default (no arrow) — add `->` for directed traversal

```cypher
// Directed shortest path
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
MATCH path = shortestPath((a)-[:KNOWS*..10]->(b))
RETURN path, length(path) AS hops;

// With multiple relationship types
MATCH path = shortestPath(
    (a:Person {name: "Alice"})-[:KNOWS|WORKS_WITH*..8]-(b:Person {name: "Bob"})
)
RETURN path;

// Shortest path with WHERE predicate on intermediate nodes
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
MATCH path = shortestPath((a)-[:KNOWS*..10]-(b))
WHERE ALL(n IN nodes(path) WHERE n.active = true)
RETURN path;
```

**Important:** The `WHERE` clause after `shortestPath` is evaluated AFTER the path is found. This means if the shortest path contains a node with `active = false`, the entire path is discarded — it does not find the next shortest path that passes the filter. If you need filtered pathfinding, use APOC path expanders instead.

### allShortestPaths — All Paths of Minimum Length

When multiple paths of the same minimum length exist, `allShortestPaths()` returns all of them.

```cypher
// All shortest paths between two nodes
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
MATCH path = allShortestPaths((a)-[:KNOWS*]-(b))
RETURN path, length(path) AS hops
LIMIT 5;

// Count how many shortest paths exist
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
MATCH path = allShortestPaths((a)-[:KNOWS*..6]-(b))
RETURN count(path) AS number_of_shortest_paths, length(path) AS path_length;

// Extract nodes on all shortest paths (useful for impact analysis)
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
MATCH path = allShortestPaths((a)-[:KNOWS*]-(b))
UNWIND nodes(path) AS n
RETURN DISTINCT n.name AS people_on_shortest_paths;
```

### When shortestPath vs allShortestPaths

| Scenario | Function |
|----------|----------|
| Navigation / routing | `shortestPath` |
| Redundancy analysis | `allShortestPaths` |
| Identifying bottleneck nodes | `allShortestPaths` |
| Performance-sensitive queries | `shortestPath` (cheaper) |

---

## Variable-Length Patterns

Variable-length patterns let you match paths of varying lengths without calling a named algorithm. They are the workhorse of Cypher graph traversal.

### Syntax

```cypher
// Match paths of exactly 3 hops
MATCH (a)-[:KNOWS*3]->(b) RETURN a, b;

// Match paths of 1 to 4 hops
MATCH (a)-[:KNOWS*1..4]->(b) RETURN a, b;

// Match paths of 2 or more hops (unbounded upper limit — dangerous)
MATCH (a)-[:KNOWS*2..]->(b) RETURN a, b;

// Match paths of any length (extremely dangerous on production data)
MATCH (a)-[:KNOWS*]->(b) RETURN a, b;
```

**Always set an upper bound.** An unbounded variable-length pattern on a dense graph can explode combinatorially and crash the database.

### Extracting Path Information

```cypher
// Get all nodes and relationships along a path
MATCH path = (a:Person {name: "Alice"})-[:KNOWS*1..4]->(b:Person)
RETURN
    [n IN nodes(path) | n.name] AS people_chain,
    length(path) AS hops,
    relationships(path) AS rels;

// Filter paths by intermediate node properties
MATCH path = (a:Person)-[:KNOWS*1..5]->(b:Person)
WHERE a.name = "Alice"
  AND ALL(n IN nodes(path) WHERE n.department = "Engineering")
RETURN path;

// Find paths that pass through a specific node
MATCH path = (a:Person {name: "Alice"})-[:KNOWS*1..6]->(b:Person {name: "Dave"})
WHERE ANY(n IN nodes(path) WHERE n.name = "Charlie")
RETURN path;
```

### Path Predicates — ALL, ANY, NONE, SINGLE

```cypher
// ALL: every node on the path must satisfy the condition
MATCH path = (a)-[:KNOWS*1..5]->(b)
WHERE ALL(n IN nodes(path) WHERE n.active = true)
RETURN path;

// ANY: at least one node on the path satisfies the condition
MATCH path = (a)-[:KNOWS*1..5]->(b)
WHERE ANY(n IN nodes(path) WHERE n.role = "manager")
RETURN path;

// NONE: no node on the path satisfies the condition
MATCH path = (a)-[:KNOWS*1..5]->(b)
WHERE NONE(n IN nodes(path) WHERE n.blacklisted = true)
RETURN path;

// SINGLE: exactly one node on the path satisfies the condition
MATCH path = (a)-[:KNOWS*1..5]->(b)
WHERE SINGLE(n IN nodes(path) WHERE n.role = "team_lead")
RETURN path;
```

---

## Weighted Shortest Path — Dijkstra and A*

### Dijkstra with APOC

Dijkstra's algorithm finds the shortest path in a weighted graph. Unlike BFS (which counts hops), Dijkstra considers numeric weights on relationships.

```cypher
// Weighted shortest path using APOC
MATCH (a:City {name: "Milano"}), (b:City {name: "Roma"})
CALL apoc.algo.dijkstra(a, b, "CONNECTED_TO", "distance")
YIELD path, weight
RETURN path, weight AS total_distance;

// With direction (default is both directions)
MATCH (a:City {name: "Milano"}), (b:City {name: "Palermo"})
CALL apoc.algo.dijkstra(a, b, "ROAD>", "distance_km")
YIELD path, weight
RETURN
    [n IN nodes(path) | n.name] AS route,
    weight AS total_km;
```

The `>` after the relationship type enforces direction. Without it, APOC treats the relationship as undirected.

### Dijkstra with GDS (Graph Data Science Library)

The GDS library requires projecting the graph into memory first, then running the algorithm on the projection. This is more performant for repeated queries.

```cypher
// Step 1: Project the road network into memory
CALL gds.graph.project(
    'road-network',
    'City',
    {
        ROAD: {
            orientation: 'NATURAL',
            properties: ['distance_km']
        }
    }
) YIELD graphName, nodeCount, relationshipCount;

// Step 2: Run Dijkstra on the projection
MATCH (source:City {name: "Milano"}), (target:City {name: "Palermo"})
CALL gds.shortestPath.dijkstra.stream('road-network', {
    sourceNode: source,
    targetNode: target,
    relationshipWeightProperty: 'distance_km'
})
YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
RETURN
    gds.util.asNode(sourceNode).name AS from,
    gds.util.asNode(targetNode).name AS to,
    totalCost AS km,
    [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS route;

// Step 3: Clean up the projection when done
CALL gds.graph.drop('road-network');
```

### A* Algorithm

A* is Dijkstra with a heuristic function that estimates the remaining distance. It is faster than Dijkstra when you have geographic coordinates because the heuristic prunes unpromising branches.

```cypher
// A* requires latitude/longitude properties on nodes
// Heuristic: haversine distance to target
MATCH (source:City {name: "Milano"}), (target:City {name: "Napoli"})
CALL gds.shortestPath.astar.stream('road-network', {
    sourceNode: source,
    targetNode: target,
    relationshipWeightProperty: 'distance_km',
    latitudeProperty: 'lat',
    longitudeProperty: 'lon'
})
YIELD totalCost, nodeIds
RETURN
    totalCost AS km,
    [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS route;
```

### Dijkstra vs A* — When to Use Each

| Criterion | Dijkstra | A* |
|-----------|----------|-----|
| Requires heuristic | No | Yes (lat/lon or similar) |
| Guaranteed optimal | Yes | Yes (with admissible heuristic) |
| Performance | Explores all directions equally | Prunes directions away from target |
| Best for | Abstract networks, non-geographic | Geographic routing |
| Works without coordinates | Yes | No |

### Single-Source Shortest Path (SSSP)

Find the shortest path from one node to ALL other nodes, not just a specific target.

```cypher
// Dijkstra single-source: shortest path from Milano to every other city
MATCH (source:City {name: "Milano"})
CALL gds.allShortestPaths.dijkstra.stream('road-network', {
    sourceNode: source,
    relationshipWeightProperty: 'distance_km'
})
YIELD targetNode, totalCost, nodeIds
RETURN
    gds.util.asNode(targetNode).name AS destination,
    totalCost AS km,
    size(nodeIds) - 1 AS hops
ORDER BY km;
```

### Yen's K-Shortest Paths

When you need not just the shortest path but the top K alternatives (for routing redundancy, for instance):

```cypher
MATCH (source:City {name: "Milano"}), (target:City {name: "Roma"})
CALL gds.shortestPath.yens.stream('road-network', {
    sourceNode: source,
    targetNode: target,
    relationshipWeightProperty: 'distance_km',
    k: 3
})
YIELD index, totalCost, nodeIds
RETURN
    index AS rank,
    totalCost AS km,
    [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS route
ORDER BY rank;
```

---

## APOC Path Expanders

APOC path expanders give you fine-grained control over traversal that Cypher's built-in `shortestPath` and variable-length patterns cannot provide. They are essential when you need to filter nodes or relationships during traversal (not after).

### apoc.path.expandConfig — The Swiss Army Knife

```cypher
// Basic expansion from a starting node
MATCH (start:Person {name: "Alice"})
CALL apoc.path.expandConfig(start, {
    relationshipFilter: "KNOWS|WORKS_WITH",
    labelFilter: "+Person",
    minLevel: 1,
    maxLevel: 4,
    uniqueness: "NODE_GLOBAL",
    limit: 100
})
YIELD path
RETURN path;
```

**Configuration parameters explained:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `relationshipFilter` | Which relationships to traverse | `"KNOWS>|WORKS_WITH"` |
| `labelFilter` | Which nodes to include/exclude | `"+Person|/Admin"` |
| `minLevel` | Minimum depth | `1` |
| `maxLevel` | Maximum depth | `5` |
| `uniqueness` | How to handle revisiting | `"NODE_GLOBAL"` |
| `limit` | Max number of result paths | `100` |
| `bfs` | Use BFS (true) or DFS (false) | `true` |
| `terminatorNodes` | Stop traversal at these nodes | list of nodes |
| `endNodes` | Only return paths ending at these | list of nodes |

### Label Filter Syntax

The label filter uses prefixes to control behavior:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `+` | Whitelist — only traverse through nodes with this label | `+Person` |
| `-` | Blacklist — never traverse through nodes with this label | `-Bot` |
| `/` | Terminator — stop traversal at this label (include in result) | `/Admin` |
| `>` | End node filter — only return paths ending at this label | `>Customer` |

```cypher
// Expand through Person nodes only, stop at Admin nodes
MATCH (start:Person {name: "Alice"})
CALL apoc.path.expandConfig(start, {
    relationshipFilter: "KNOWS",
    labelFilter: "+Person|/Admin",
    maxLevel: 6
})
YIELD path
RETURN path;

// Find all Customer nodes reachable through Person nodes
MATCH (start:Person {name: "Alice"})
CALL apoc.path.expandConfig(start, {
    relationshipFilter: "KNOWS|MANAGES",
    labelFilter: "+Person|>Customer",
    maxLevel: 5
})
YIELD path
RETURN last(nodes(path)) AS customer;
```

### Relationship Filter Syntax

```cypher
// Outgoing KNOWS only
"KNOWS>"

// Incoming REPORTS_TO only
"<REPORTS_TO"

// Both directions for KNOWS, outgoing for MANAGES
"KNOWS|MANAGES>"

// Any relationship type (no filter)
""
```

### Uniqueness Modes

Uniqueness controls how the expander handles cycles and revisits:

| Mode | Description | Use Case |
|------|-------------|----------|
| `RELATIONSHIP_GLOBAL` | Each relationship traversed once globally | Default, safest |
| `NODE_GLOBAL` | Each node visited once globally | Social network expansion |
| `NODE_PATH` | Each node visited once per path | Finding all paths (allows node reuse across paths) |
| `RELATIONSHIP_PATH` | Each relationship used once per path | Finding all paths |
| `NONE` | No uniqueness constraint | Danger — can infinite loop |

```cypher
// Find all distinct paths (allow same node in different paths)
MATCH (start:Person {name: "Alice"})
CALL apoc.path.expandConfig(start, {
    relationshipFilter: "KNOWS",
    maxLevel: 3,
    uniqueness: "NODE_PATH"
})
YIELD path
RETURN path;
```

### apoc.path.subgraphNodes and subgraphAll

These are convenience wrappers around `expandConfig` for common patterns.

```cypher
// Get all nodes reachable within 3 hops
MATCH (start:Person {name: "Alice"})
CALL apoc.path.subgraphNodes(start, {
    relationshipFilter: "KNOWS",
    maxLevel: 3
})
YIELD node
RETURN node.name;

// Get the full subgraph (nodes + relationships)
MATCH (start:Person {name: "Alice"})
CALL apoc.path.subgraphAll(start, {
    relationshipFilter: "KNOWS|WORKS_WITH",
    maxLevel: 4
})
YIELD nodes, relationships
RETURN size(nodes) AS node_count, size(relationships) AS rel_count;

// Spanning tree (subgraph without cycles)
MATCH (start:Person {name: "Alice"})
CALL apoc.path.spanningTree(start, {
    relationshipFilter: "KNOWS",
    maxLevel: 5
})
YIELD path
RETURN path;
```

---

## Graph Data Science (GDS) Library

GDS is the official Neo4j library for analytical graph algorithms. It operates on an **in-memory projected graph** — a separate copy of the relevant subgraph optimized for algorithm execution. This projection is the central entry point for all analytical algorithms.

### Creating a Graph Projection

```cypher
// Project a subset of the graph into memory for analysis
CALL gds.graph.project(
    'social-graph',
    ['Person'],
    {
        KNOWS: {
            orientation: 'UNDIRECTED',
            properties: ['weight']
        }
    }
) YIELD graphName, nodeCount, relationshipCount;

// Projection with multiple relationship types
CALL gds.graph.project(
    'work-network',
    ['Person', 'Department'],
    {
        WORKS_WITH: { orientation: 'UNDIRECTED' },
        BELONGS_TO: { orientation: 'NATURAL' }
    }
) YIELD graphName, nodeCount, relationshipCount;

// List all projections
CALL gds.graph.list()
YIELD graphName, nodeCount, relationshipCount, memoryUsage;

// Drop a projection when done
CALL gds.graph.drop('social-graph');

// Estimate memory before projecting (important for large graphs)
CALL gds.graph.project.estimate(
    ['Person'],
    { KNOWS: { orientation: 'UNDIRECTED' } }
)
YIELD requiredMemory, bytesMin, bytesMax;
```

### Cypher-Based Projection (Flexible but Slower)

When the native projection syntax is insufficient (complex filters, computed properties):

```cypher
CALL gds.graph.project.cypher(
    'filtered-social',
    'MATCH (p:Person) WHERE p.active = true RETURN id(p) AS id, p.name AS name',
    'MATCH (a:Person)-[r:KNOWS]->(b:Person)
     WHERE a.active = true AND b.active = true
     RETURN id(a) AS source, id(b) AS target, r.weight AS weight'
) YIELD graphName, nodeCount, relationshipCount;
```

### GDS Execution Modes

Every GDS algorithm supports four execution modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `.stream()` | Returns results as a stream | Ad-hoc analysis, exploration |
| `.stats()` | Returns aggregate statistics | Quick quality check |
| `.mutate()` | Writes results to the in-memory projection | Pipeline: chain algorithms |
| `.write()` | Writes results back to the Neo4j database | Persist results for queries |

```cypher
// Stream: returns results row by row
CALL gds.pageRank.stream('social-graph') YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name, score
ORDER BY score DESC LIMIT 10;

// Stats: just the summary
CALL gds.pageRank.stats('social-graph')
YIELD ranIterations, didConverge, preProcessingMillis, computeMillis;

// Mutate: add to in-memory projection (for chaining with another algorithm)
CALL gds.pageRank.mutate('social-graph', { mutateProperty: 'pagerank' })
YIELD nodePropertiesWritten;

// Write: persist to the database
CALL gds.pageRank.write('social-graph', { writeProperty: 'pagerank' })
YIELD nodePropertiesWritten;
```

---

## PageRank — Node Importance

PageRank measures the importance of a node based on the number and quality of nodes pointing to it. Originally designed by Google for web page ranking. A node is important if it is linked to by other important nodes.

**Algorithm:**
1. Initialize all nodes with equal rank (1/N)
2. Iteratively: each node distributes its rank equally across its outgoing relationships
3. Apply a damping factor (typically 0.85) — with 15% probability, jump to a random node
4. Repeat until convergence or max iterations reached

```cypher
// PageRank on a social graph
CALL gds.pageRank.stream('social-graph', {
    maxIterations: 20,
    dampingFactor: 0.85
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS person, score
ORDER BY score DESC
LIMIT 10;

// Write PageRank as a property on nodes
CALL gds.pageRank.write('social-graph', {
    maxIterations: 20,
    dampingFactor: 0.85,
    writeProperty: 'pagerank'
})
YIELD nodePropertiesWritten, ranIterations, didConverge;

// Verify the written property
MATCH (p:Person)
RETURN p.name, p.pagerank
ORDER BY p.pagerank DESC
LIMIT 10;

// Personalized PageRank (biased toward a specific node)
MATCH (focus:Person {name: "Alice"})
CALL gds.pageRank.stream('social-graph', {
    maxIterations: 20,
    dampingFactor: 0.85,
    sourceNodes: [focus]
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS person, score
ORDER BY score DESC
LIMIT 10;
```

**Interpreting PageRank scores:**
- Higher score = more "important" or "influential" in the network
- A node with many incoming connections from high-PR nodes ranks higher than one with many connections from low-PR nodes
- The damping factor (0.85) models the probability of following a link vs jumping randomly
- Convergence tolerance can be set with `tolerance: 0.0001`

### Weighted PageRank

```cypher
// Project with relationship weights
CALL gds.graph.project(
    'weighted-social',
    'Person',
    {
        KNOWS: {
            orientation: 'NATURAL',
            properties: ['interaction_count']
        }
    }
);

// Weighted PageRank — nodes connected by high-weight relationships
// transfer more rank
CALL gds.pageRank.stream('weighted-social', {
    maxIterations: 20,
    dampingFactor: 0.85,
    relationshipWeightProperty: 'interaction_count'
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name, score
ORDER BY score DESC
LIMIT 10;
```

---

## Centrality Algorithms

Centrality algorithms identify the most important nodes in a network. Different centrality measures capture different notions of "importance."

### Betweenness Centrality

Measures how often a node lies on the shortest path between two other nodes. Nodes with high betweenness are "bridges" or "brokers" — their removal would disconnect parts of the network.

```cypher
CALL gds.betweenness.stream('social-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS person, score AS betweenness
ORDER BY betweenness DESC
LIMIT 10;

// Write betweenness to nodes
CALL gds.betweenness.write('social-graph', {
    writeProperty: 'betweenness'
})
YIELD nodePropertiesWritten, centralityDistribution;

// Sampled betweenness (faster for large graphs, approximate)
CALL gds.betweenness.stream('social-graph', {
    samplingSize: 100,
    samplingSeed: 42
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name, score
ORDER BY score DESC
LIMIT 10;
```

**Real-world use:** In a corporate network, high-betweenness employees are critical connectors. If they leave, information flow between teams degrades. In supply chains, high-betweenness nodes are single points of failure.

### Closeness Centrality

Measures how quickly a node can reach all other nodes. A node with high closeness is "central" in the network — it has short average distance to everyone else.

```cypher
CALL gds.closeness.stream('social-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS person, score AS closeness
ORDER BY closeness DESC
LIMIT 10;

// Harmonic centrality (handles disconnected graphs better than closeness)
CALL gds.closeness.stream('social-graph', {
    useWassermanFaust: true
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name, score
ORDER BY score DESC
LIMIT 10;
```

**Closeness vs Betweenness:**
- Closeness = "who can spread information fastest" (epidemic model)
- Betweenness = "who controls information flow" (gatekeeper model)

### Degree Centrality

The simplest centrality metric — counts the number of direct connections.

```cypher
CALL gds.degree.stream('social-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS person, score AS degree
ORDER BY degree DESC
LIMIT 10;

// Weighted degree (sum of relationship weights instead of count)
CALL gds.degree.stream('weighted-social', {
    relationshipWeightProperty: 'interaction_count'
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name, score AS weighted_degree
ORDER BY weighted_degree DESC
LIMIT 10;
```

### Eigenvector Centrality

Similar to PageRank but without the damping factor. A node is important if its neighbors are important. More sensitive to the network structure than degree centrality.

```cypher
CALL gds.eigenvector.stream('social-graph', {
    maxIterations: 20
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name, score
ORDER BY score DESC
LIMIT 10;
```

### Comparing Centrality Measures

```cypher
// Run all centrality algorithms and compare
CALL gds.pageRank.mutate('social-graph', { mutateProperty: 'pr' });
CALL gds.betweenness.mutate('social-graph', { mutateProperty: 'bc' });
CALL gds.degree.mutate('social-graph', { mutateProperty: 'deg' });

// Stream the combined results
CALL gds.graph.nodeProperty.stream('social-graph', 'pr')
YIELD nodeId, propertyValue AS pagerank
WITH nodeId, pagerank
CALL gds.graph.nodeProperty.stream('social-graph', 'bc')
YIELD nodeId AS nid2, propertyValue AS betweenness
WHERE nid2 = nodeId
WITH nodeId, pagerank, betweenness
CALL gds.graph.nodeProperty.stream('social-graph', 'deg')
YIELD nodeId AS nid3, propertyValue AS degree
WHERE nid3 = nodeId
RETURN
    gds.util.asNode(nodeId).name AS person,
    pagerank, betweenness, degree
ORDER BY pagerank DESC
LIMIT 20;
```

---

## Community Detection

Community detection algorithms identify groups of densely connected nodes — clusters or communities within the graph.

### Louvain — Hierarchical Clustering

Louvain is the most widely used community detection algorithm. It optimizes modularity iteratively and produces hierarchical community structure.

**Algorithm:**
1. Assign each node to its own community
2. For each node, check if moving it to a neighbor's community increases modularity
3. If yes, move it. Repeat until no more improvements
4. Collapse communities into super-nodes and repeat from step 2
5. The result is a hierarchical tree of communities

```cypher
// Stream community assignments
CALL gds.louvain.stream('social-graph')
YIELD nodeId, communityId, intermediateCommunityIds
RETURN
    gds.util.asNode(nodeId).name AS person,
    communityId
ORDER BY communityId, person;

// Statistics — check clustering quality
CALL gds.louvain.stats('social-graph')
YIELD communityCount, modularity, modularities;

// Write communities to nodes
CALL gds.louvain.write('social-graph', {
    writeProperty: 'community'
})
YIELD communityCount, modularity;

// Weighted Louvain (considers relationship weights)
CALL gds.louvain.stream('weighted-social', {
    relationshipWeightProperty: 'interaction_count'
})
YIELD nodeId, communityId
RETURN communityId, collect(gds.util.asNode(nodeId).name) AS members
ORDER BY size(members) DESC;

// Seeded Louvain (start with known community assignments)
CALL gds.louvain.stream('social-graph', {
    seedProperty: 'department_id'
})
YIELD nodeId, communityId
RETURN communityId, collect(gds.util.asNode(nodeId).name) AS members;
```

**Modularity:** A value between -0.5 and 1.0. Higher = better separation between communities. Values above 0.3 typically indicate meaningful community structure.

### Label Propagation — Fast Community Detection

Label Propagation is faster than Louvain but less stable (results can vary between runs). Each node adopts the label of the majority of its neighbors.

```cypher
CALL gds.labelPropagation.stream('social-graph', {
    maxIterations: 10
})
YIELD nodeId, communityId
RETURN communityId, collect(gds.util.asNode(nodeId).name) AS members
ORDER BY size(members) DESC
LIMIT 10;

// With seed labels (semi-supervised)
CALL gds.labelPropagation.stream('social-graph', {
    maxIterations: 10,
    seedProperty: 'known_group'
})
YIELD nodeId, communityId
RETURN communityId, collect(gds.util.asNode(nodeId).name) AS members;
```

### Weakly Connected Components (WCC)

Finds disconnected subgraphs. Two nodes are in the same component if there is any path between them (ignoring relationship direction).

```cypher
CALL gds.wcc.stream('social-graph')
YIELD nodeId, componentId
WITH componentId, collect(gds.util.asNode(nodeId).name) AS members
RETURN componentId, members, size(members) AS size
ORDER BY size DESC;

// Use WCC to find isolated clusters
CALL gds.wcc.stats('social-graph')
YIELD componentCount, componentDistribution;
```

**WCC is a prerequisite check:** Run WCC before other algorithms to verify the graph is connected. Many algorithms (closeness, betweenness) produce misleading results on disconnected graphs.

### Strongly Connected Components (SCC)

For directed graphs: two nodes are in the same SCC if there is a directed path from A to B AND from B to A.

```cypher
CALL gds.scc.stream('social-graph')
YIELD nodeId, componentId
WITH componentId, collect(gds.util.asNode(nodeId).name) AS members
WHERE size(members) > 1
RETURN componentId, members, size(members) AS size
ORDER BY size DESC;
```

### Triangle Count and Clustering Coefficient

Triangles are the building block of community structure. The clustering coefficient measures how likely a node's neighbors are to be connected to each other.

```cypher
// Count triangles per node
CALL gds.triangleCount.stream('social-graph')
YIELD nodeId, triangleCount
RETURN gds.util.asNode(nodeId).name, triangleCount
ORDER BY triangleCount DESC
LIMIT 10;

// Local clustering coefficient
CALL gds.localClusteringCoefficient.stream('social-graph')
YIELD nodeId, localClusteringCoefficient
RETURN gds.util.asNode(nodeId).name, localClusteringCoefficient
ORDER BY localClusteringCoefficient DESC
LIMIT 10;

// Global stats
CALL gds.triangleCount.stats('social-graph')
YIELD globalTriangleCount, nodeCount;
```

### Louvain vs Label Propagation — When to Use Each

| Criterion | Louvain | Label Propagation |
|-----------|---------|-------------------|
| Quality | Higher (modularity optimized) | Lower (majority voting) |
| Speed | Slower | Faster |
| Deterministic | Yes (for same input) | No (order-dependent) |
| Hierarchical | Yes (intermediate communities) | No |
| Best for | Analysis, reporting | Real-time, large graphs |

---

## Node Similarity and Link Prediction

### Jaccard Similarity (Node Similarity)

Measures similarity between two nodes based on shared neighbors. Jaccard coefficient = |intersection| / |union| of neighbor sets.

```cypher
CALL gds.nodeSimilarity.stream('social-graph', {
    topK: 5,
    similarityCutoff: 0.3
})
YIELD node1, node2, similarity
RETURN
    gds.util.asNode(node1).name AS person1,
    gds.util.asNode(node2).name AS person2,
    similarity
ORDER BY similarity DESC
LIMIT 20;

// Write similarity relationships to the graph
CALL gds.nodeSimilarity.write('social-graph', {
    topK: 3,
    similarityCutoff: 0.4,
    writeRelationshipType: 'SIMILAR_TO',
    writeProperty: 'score'
})
YIELD nodesCompared, relationshipsWritten;
```

### Overlap Similarity

Instead of Jaccard (intersection/union), Overlap coefficient = intersection / min(|A|, |B|). Better when one set is much larger than the other.

```cypher
CALL gds.nodeSimilarity.stream('social-graph', {
    topK: 5,
    similarityMetric: 'OVERLAP'
})
YIELD node1, node2, similarity
RETURN
    gds.util.asNode(node1).name,
    gds.util.asNode(node2).name,
    similarity
ORDER BY similarity DESC;
```

### Link Prediction — Common Neighbors

Link prediction estimates the probability that a relationship will form between two unconnected nodes.

```cypher
// Common neighbors score
MATCH (a:Person {name: "Alice"})
MATCH (b:Person)
WHERE b.name <> "Alice" AND NOT (a)-[:KNOWS]-(b)
WITH a, b,
     gds.alpha.linkprediction.commonNeighbors(a, b) AS cn,
     gds.alpha.linkprediction.adamicAdar(a, b, {relationshipQuery: "KNOWS"}) AS aa,
     gds.alpha.linkprediction.preferentialAttachment(a, b, {relationshipQuery: "KNOWS"}) AS pa
RETURN b.name, cn, aa, pa
ORDER BY aa DESC
LIMIT 10;
```

**Link prediction metrics explained:**

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Common Neighbors | count(shared neighbors) | More shared friends = more likely to connect |
| Adamic-Adar | sum(1 / log(degree(shared))) | Weighs rare shared connections higher |
| Preferential Attachment | degree(A) * degree(B) | Popular nodes attract more connections |
| Resource Allocation | sum(1 / degree(shared)) | Similar to Adamic-Adar but more aggressive |

---

## Cypher Query Optimization for Traversal

### Always Bound Variable-Length Patterns

```cypher
// SLOW: unbounded variable-length — exponential explosion on dense graphs
MATCH (a)-[:KNOWS*]->(b:Person {name: "Bob"})
RETURN a.name;

// FAST: bounded depth
MATCH (a)-[:KNOWS*1..4]->(b:Person {name: "Bob"})
RETURN a.name;
```

### Filter Before Traversal

```cypher
// SLOW: traverse first, filter after
MATCH (p:Person)-[:KNOWS*1..3]->(friend:Person)
WHERE p.department = "Engineering"
RETURN p.name, friend.name;

// FAST: filter anchor node first, then traverse
MATCH (p:Person {department: "Engineering"})
WITH p
MATCH (p)-[:KNOWS*1..3]->(friend:Person)
RETURN p.name, friend.name;
```

### Handle Super-Nodes

Super-nodes (nodes with thousands+ of relationships) cause traversal explosion. Pre-filter them.

```cypher
// SLOW: traversing through a super-node with 100k relationships
MATCH (a:Person)-[:KNOWS]->(friend:Person)
RETURN a.name, friend.name;

// FAST: filter out super-nodes
MATCH (p:Person)
WHERE size((p)-[:KNOWS]->()) > 5 AND size((p)-[:KNOWS]->()) < 1000
WITH p
MATCH (p)-[:KNOWS]->(friend:Person)
RETURN p.name, friend.name;
```

### Use DISTINCT to Reduce Backtracking

```cypher
// Without DISTINCT: generates path permutations, many duplicate pairs
MATCH (a:Person)-[:KNOWS*2..3]->(b:Person)
RETURN a.name, b.name;

// With DISTINCT: one result per (a, b) pair
MATCH (a:Person)-[:KNOWS*2..3]->(b:Person)
RETURN DISTINCT a.name, b.name;
```

### Profile and Explain

```cypher
// EXPLAIN: shows the query plan without executing
EXPLAIN MATCH path = shortestPath(
    (a:Person {name: "Alice"})-[:KNOWS*..10]-(b:Person {name: "Bob"})
)
RETURN path;

// PROFILE: executes and shows actual row counts and db hits
PROFILE MATCH path = shortestPath(
    (a:Person {name: "Alice"})-[:KNOWS*..10]-(b:Person {name: "Bob"})
)
RETURN path;
```

**Key metrics in PROFILE output:**
- `Rows`: actual rows produced by each operator
- `DbHits`: number of database operations (lower = better)
- `EstimatedRows`: planner's estimate — if far from actual Rows, statistics may be stale

```cypher
// Refresh statistics if estimates are off
CALL db.stats.collect("GRAPH COUNTS");
```

### Index-Backed Traversal

Ensure your anchor nodes use indexes for fast lookup before traversal.

```cypher
// Create indexes on properties used as traversal starting points
CREATE INDEX person_name FOR (p:Person) ON (p.name);
CREATE INDEX person_department FOR (p:Person) ON (p.department);

// Verify index usage
EXPLAIN MATCH (p:Person {name: "Alice"})-[:KNOWS*1..3]->(friend)
RETURN friend.name;
// The plan should show NodeIndexSeek, not NodeByLabelScan
```

---

## Troubleshooting

### Problem: shortestPath returns NULL

**Cause:** No path exists between the two nodes within the depth limit.

**Diagnosis:**
```cypher
// Check if both nodes exist
MATCH (a:Person {name: "Alice"}) RETURN count(a);
MATCH (b:Person {name: "Bob"}) RETURN count(b);

// Check if they are in the same connected component
CALL gds.wcc.stream('social-graph')
YIELD nodeId, componentId
WITH gds.util.asNode(nodeId) AS node, componentId
WHERE node.name IN ["Alice", "Bob"]
RETURN node.name, componentId;
// If different componentId values, no path exists
```

**Fix:** Increase the depth limit or verify the relationship types are correct.

### Problem: Variable-length query times out or runs out of memory

**Cause:** Unbounded or too-deep traversal on a dense graph.

**Fixes:**
1. Add an upper bound: `*..5` instead of `*`
2. Filter super-nodes (degree > threshold)
3. Use APOC path expanders with `limit` parameter
4. Project a subgraph with GDS and run algorithms there

### Problem: GDS graph projection fails with OutOfMemoryError

**Cause:** The projected graph does not fit in heap memory.

**Fixes:**
1. Estimate memory first: `CALL gds.graph.project.estimate(...)`
2. Increase heap: `server.memory.heap.initial_size=4g` and `server.memory.heap.max_size=4g`
3. Project fewer node labels or relationship types
4. Use Cypher projection with filters to reduce size

### Problem: PageRank does not converge

**Cause:** The graph structure prevents convergence (e.g., dangling nodes with no outgoing edges, or very strong hubs).

**Fixes:**
1. Increase `maxIterations` (try 50-100)
2. Increase `tolerance` (try 0.001 instead of 0.0001)
3. Check for disconnected components — PageRank on disconnected components can behave unexpectedly

### Problem: Community detection returns too many or too few communities

**Cause:** Parameters or algorithm choice mismatch with the graph structure.

**Fixes:**
- Too many communities (fragmented): Lower the `resolution` parameter in Louvain (< 1.0)
- Too few communities (lumped): Increase the `resolution` parameter (> 1.0)
- Try Label Propagation or Leiden algorithm as alternatives
- Check if the graph has natural community structure using modularity score

```cypher
// Louvain with resolution parameter
CALL gds.louvain.stream('social-graph', {
    resolution: 0.5   // lower = fewer, larger communities
})
YIELD nodeId, communityId
RETURN communityId, count(*) AS size
ORDER BY size DESC;
```

---

## Q&A

**Q1: When should I use shortestPath vs Dijkstra vs A*?**

Use `shortestPath()` when you care about hop count (fewest relationships). Use Dijkstra when relationships have weights (distance, cost, time) and you want the minimum total weight. Use A* when you have geographic coordinates and want Dijkstra's optimality with better performance.

**Q2: Why does GDS require a graph projection? Why not run algorithms directly on the database?**

The projection creates an in-memory representation optimized for analytical algorithms — compressed adjacency lists, no transaction overhead, no locking. Running algorithms directly on the transactional store would be orders of magnitude slower and would block OLTP operations.

**Q3: Can I run GDS algorithms on a subset of the graph?**

Yes. Use the native projection with specific labels and relationship types, or use Cypher projection with WHERE clauses to filter nodes and relationships.

**Q4: What is the difference between WCC and SCC?**

WCC (Weakly Connected Components) treats all relationships as undirected — if any path exists between A and B, they are in the same component. SCC (Strongly Connected Components) requires a directed path from A to B AND from B to A.

**Q5: How do I choose between Louvain and Label Propagation?**

Louvain produces higher quality results (modularity-optimized) but is slower. Label Propagation is faster but non-deterministic. Use Louvain for analysis and reporting; use Label Propagation for real-time or very large graphs where approximate results are acceptable.

**Q6: What does the damping factor in PageRank do?**

The damping factor (default 0.85) models a "random surfer" who follows links 85% of the time and jumps to a random node 15% of the time. Lower damping = more random jumping = scores converge faster but capture less graph structure. Higher damping = more link-following = captures more structure but converges slower.

**Q7: How do APOC path expanders differ from Cypher's shortestPath?**

APOC expanders filter nodes and relationships DURING traversal. Cypher's `WHERE` on `shortestPath` filters AFTER the path is found. This means APOC can find the shortest path through only certain node types, while Cypher will discard the path if any node fails the filter (without trying alternative paths).

**Q8: What is the maximum practical depth for variable-length patterns?**

Depends on the graph's average degree. For a graph with average degree 5, depth 6 means exploring up to 5^6 = 15,625 nodes. Beyond depth 10, most queries become impractical without APOC expanders with limits. Rule of thumb: stay under 10 for interactive queries.

**Q9: Can I run centrality algorithms on directed graphs?**

Yes. Project the graph with `orientation: 'NATURAL'` (directed) or `'REVERSE'` (reversed direction). The choice matters — PageRank on outgoing vs incoming relationships gives different results. Betweenness considers direction by default.

**Q10: How do I handle disconnected graphs in centrality analysis?**

Run WCC first to identify components. Then either analyze each component separately, or use algorithms that handle disconnection gracefully (Harmonic Centrality instead of Closeness, for example).

**Q11: What is the computational complexity of these algorithms?**

| Algorithm | Time Complexity | Notes |
|-----------|----------------|-------|
| BFS/DFS | O(V + E) | Linear, very efficient |
| Dijkstra | O((V + E) log V) | With priority queue |
| PageRank | O(iterations * E) | Typically 20-50 iterations |
| Betweenness | O(V * E) | Expensive on large graphs |
| Louvain | O(E) per pass | Multiple passes, typically fast |
| WCC | O(V + E) | Linear |
| Node Similarity | O(V^2 * avg_degree) | Can be expensive |

**Q12: Can I chain multiple GDS algorithms in a pipeline?**

Yes. Use `.mutate()` mode to add results to the in-memory projection, then run the next algorithm. For example: run WCC first to tag components, then run PageRank within the largest component.

**Q13: How does Neo4j handle cycles during traversal?**

Cypher's `shortestPath` and `allShortestPaths` automatically avoid revisiting nodes. Variable-length patterns (`*1..5`) do not revisit the same relationship in a single path but can revisit nodes via different relationships. APOC expanders let you control this explicitly via the `uniqueness` parameter — `NODE_GLOBAL` prevents revisiting any node, `RELATIONSHIP_GLOBAL` prevents reusing any relationship.

**Q14: What happens if I project a very large graph with GDS?**

GDS stores the projection in JVM heap memory. A graph with 100M nodes and 1B relationships might require 20-50 GB of heap. Always run `gds.graph.project.estimate()` first. If the graph is too large, filter during projection (fewer labels, fewer relationship types), or use the GDS Arrow interface for out-of-heap storage in GDS Enterprise.

**Q15: Can I use traversal algorithms for real-time queries in a production application?**

`shortestPath` and bounded variable-length patterns are production-safe with proper indexes and depth limits. GDS algorithms are analytical — they require a projection step that takes seconds to minutes, making them unsuitable for sub-millisecond latency requirements. Pre-compute GDS results with `.write()` mode and query the written properties for real-time access.

**Q16: How do I find the diameter of a graph?**

The diameter is the longest shortest path between any two nodes. There is no single-call function for this. Approximate it by running SSSP from several random nodes and taking the maximum `totalCost`. For exact computation on small graphs, run all-pairs shortest paths and find the max.

**Q17: What is the difference between `gds.graph.project` and `gds.graph.project.cypher`?**

Native projection (`gds.graph.project`) reads directly from the Neo4j store and is fast but limited to label/relationship-type filtering. Cypher projection (`gds.graph.project.cypher`) executes arbitrary Cypher queries to define nodes and relationships — slower but supports computed properties, complex filters, and virtual relationships. Use native projection unless you need Cypher's flexibility.

**Q18: How does Personalized PageRank differ from standard PageRank?**

Standard PageRank distributes random jumps uniformly across all nodes. Personalized PageRank biases random jumps toward a specific set of source nodes. The result reflects "importance from the perspective of the source nodes" rather than global importance. Useful for recommendations: "what is important to this user" vs "what is globally important."

**Q19: When should I use Triangle Count vs Louvain for community analysis?**

They answer different questions. Triangle Count tells you how tightly knit each node's local neighborhood is (clustering coefficient). Louvain partitions the entire graph into communities. Use Triangle Count when you need a per-node metric of local density. Use Louvain when you need to assign every node to a group. They complement each other — run both and correlate: nodes with high clustering coefficient inside a Louvain community are core members; nodes with low clustering coefficient at community boundaries are peripheral.

**Q20: How do I handle multi-relational graphs in GDS?**

Project multiple relationship types and either treat them as one combined type or analyze them separately. For combined analysis, project all types into one projection:

```cypher
CALL gds.graph.project('multi-rel', 'Person', {
    KNOWS: { orientation: 'UNDIRECTED' },
    WORKS_WITH: { orientation: 'UNDIRECTED' },
    REPORTS_TO: { orientation: 'NATURAL' }
});
```

For separate analysis, create multiple projections — one per relationship type — and compare the results. A node that ranks high across multiple relationship networks is robustly important regardless of how you define "connection."

---

## Exercises

### Exercise 1 — Basic Shortest Path (Beginner)

Create a small social network of 10 people with KNOWS relationships. Find the shortest path between two people who are not directly connected. Verify that the path is indeed the shortest by checking all possible paths manually.

```cypher
// Setup
CREATE (a:Person {name: "Alice"}),
       (b:Person {name: "Bob"}),
       (c:Person {name: "Charlie"}),
       (d:Person {name: "Dave"}),
       (e:Person {name: "Eve"}),
       (f:Person {name: "Frank"}),
       (g:Person {name: "Grace"}),
       (h:Person {name: "Heidi"}),
       (i:Person {name: "Ivan"}),
       (j:Person {name: "Judy"})
CREATE (a)-[:KNOWS]->(b), (a)-[:KNOWS]->(c),
       (b)-[:KNOWS]->(d), (c)-[:KNOWS]->(d),
       (d)-[:KNOWS]->(e), (e)-[:KNOWS]->(f),
       (f)-[:KNOWS]->(g), (g)-[:KNOWS]->(h),
       (h)-[:KNOWS]->(i), (i)-[:KNOWS]->(j),
       (c)-[:KNOWS]->(f);

// Task: Find shortest path from Alice to Judy
// Expected: Alice -> C -> F -> G -> H -> I -> Judy (6 hops)
// vs Alice -> B -> D -> E -> F -> G -> H -> I -> Judy (8 hops)
```

### Exercise 2 — PageRank Analysis (Intermediate)

Given a citation network where papers cite other papers, find the top 10 most influential papers using PageRank. Compare the results with simple degree centrality. Explain any differences.

```cypher
// Setup: Create a citation network
CREATE (p1:Paper {title: "Seminal Work", year: 2000}),
       (p2:Paper {title: "Follow-up A", year: 2005}),
       (p3:Paper {title: "Follow-up B", year: 2006}),
       (p4:Paper {title: "Synthesis", year: 2010}),
       (p5:Paper {title: "Application", year: 2012}),
       (p6:Paper {title: "Extension", year: 2015}),
       (p7:Paper {title: "Survey", year: 2018}),
       (p8:Paper {title: "Critique", year: 2019}),
       (p9:Paper {title: "New Direction", year: 2020}),
       (p10:Paper {title: "Recent Work", year: 2023})
CREATE (p2)-[:CITES]->(p1), (p3)-[:CITES]->(p1),
       (p4)-[:CITES]->(p2), (p4)-[:CITES]->(p3), (p4)-[:CITES]->(p1),
       (p5)-[:CITES]->(p4), (p5)-[:CITES]->(p1),
       (p6)-[:CITES]->(p4), (p6)-[:CITES]->(p5),
       (p7)-[:CITES]->(p1), (p7)-[:CITES]->(p4), (p7)-[:CITES]->(p5), (p7)-[:CITES]->(p6),
       (p8)-[:CITES]->(p1), (p8)-[:CITES]->(p7),
       (p9)-[:CITES]->(p4), (p9)-[:CITES]->(p8),
       (p10)-[:CITES]->(p9), (p10)-[:CITES]->(p7);

// Tasks:
// 1. Project the citation graph
// 2. Run PageRank
// 3. Run degree centrality
// 4. Compare: which paper is ranked differently by the two methods and why?
```

### Exercise 3 — Community Detection (Intermediate)

Build a network of 30+ people across 3 departments. Add intra-department connections (dense) and inter-department connections (sparse). Run Louvain and verify it recovers the department structure. Experiment with the resolution parameter.

### Exercise 4 — APOC Path Expander (Advanced)

In a supply chain graph with Supplier, Warehouse, and Retailer nodes connected by SHIPS_TO relationships, find all paths from a specific Supplier to all Retailers that pass through at least one Warehouse, avoiding any node flagged as `quarantined = true`. Use APOC path expanders with label filters.

### Exercise 5 — Full GDS Pipeline (Advanced)

Build a complete analysis pipeline:
1. Project a social network graph
2. Run WCC to verify connectivity
3. Run PageRank to find influential nodes
4. Run Louvain to detect communities
5. Run Node Similarity to find potential new connections
6. Write all results back to the database
7. Query the database to find "bridge" people: high betweenness centrality who belong to different communities than their most similar nodes

### Exercise 6 — Weighted Pathfinding (Advanced)

Create a transportation network with cities connected by roads (weight: distance_km) and flights (weight: time_hours). Find the shortest path by distance using Dijkstra. Then find the fastest path (by time). Compare the routes — they should differ because flights skip geographic distance but have fixed time.

```cypher
// Setup: Transportation network
CREATE (mil:City {name: "Milano", lat: 45.46, lon: 9.19}),
       (rom:City {name: "Roma", lat: 41.90, lon: 12.49}),
       (nap:City {name: "Napoli", lat: 40.85, lon: 14.27}),
       (fir:City {name: "Firenze", lat: 43.77, lon: 11.25}),
       (ven:City {name: "Venezia", lat: 45.44, lon: 12.32}),
       (pal:City {name: "Palermo", lat: 38.12, lon: 13.36}),
       (bol:City {name: "Bologna", lat: 44.49, lon: 11.34})
CREATE (mil)-[:ROAD {distance_km: 305, time_hours: 3.5}]->(bol),
       (bol)-[:ROAD {distance_km: 105, time_hours: 1.5}]->(fir),
       (fir)-[:ROAD {distance_km: 275, time_hours: 3.0}]->(rom),
       (rom)-[:ROAD {distance_km: 225, time_hours: 2.5}]->(nap),
       (mil)-[:ROAD {distance_km: 270, time_hours: 3.0}]->(ven),
       (mil)-[:FLIGHT {distance_km: 880, time_hours: 1.25}]->(pal),
       (rom)-[:FLIGHT {distance_km: 430, time_hours: 1.0}]->(pal),
       (nap)-[:ROAD {distance_km: 660, time_hours: 8.0}]->(pal);

// Tasks:
// 1. Project the graph with distance_km as weight
// 2. Find shortest path by distance from Milano to Palermo
// 3. Re-project with time_hours as weight
// 4. Find fastest path from Milano to Palermo
// 5. Compare: the distance-optimal route goes by road, the time-optimal route flies
```

### Exercise 7 — Link Prediction Evaluation (Expert)

Split a social network temporally: use connections formed before 2023 as the training graph, and connections formed in 2023 as the test set. Run link prediction (Common Neighbors, Adamic-Adar) on the training graph. Evaluate precision@10: of the top 10 predicted links, how many actually appeared in the test set?

```cypher
// Setup: Social network with temporal relationships
CREATE (a:Person {name: "Alice"}), (b:Person {name: "Bob"}),
       (c:Person {name: "Charlie"}), (d:Person {name: "Dave"}),
       (e:Person {name: "Eve"}), (f:Person {name: "Frank"}),
       (g:Person {name: "Grace"}), (h:Person {name: "Heidi"})
// Training edges (before 2023)
CREATE (a)-[:KNOWS {since: date("2020-01-01")}]->(b),
       (a)-[:KNOWS {since: date("2021-06-01")}]->(c),
       (b)-[:KNOWS {since: date("2020-03-01")}]->(c),
       (b)-[:KNOWS {since: date("2021-01-01")}]->(d),
       (c)-[:KNOWS {since: date("2022-01-01")}]->(e),
       (d)-[:KNOWS {since: date("2022-06-01")}]->(e),
       (e)-[:KNOWS {since: date("2022-09-01")}]->(f),
       (f)-[:KNOWS {since: date("2021-01-01")}]->(g),
       (g)-[:KNOWS {since: date("2022-01-01")}]->(h)
// Test edges (2023 — these are the links to predict)
CREATE (a)-[:KNOWS {since: date("2023-03-01")}]->(d),
       (c)-[:KNOWS {since: date("2023-05-01")}]->(d),
       (b)-[:KNOWS {since: date("2023-08-01")}]->(e);

// Tasks:
// 1. Project only pre-2023 relationships
// 2. Run Adamic-Adar link prediction for all non-connected pairs
// 3. Rank by prediction score
// 4. Check how many of the top 10 predictions appear in the 2023 test set
// 5. Calculate precision@10
```

### Exercise 8 — Real-Time Fraud Ring Detection (Expert)

Build a transaction graph where accounts make transfers. Implement a query that finds circular money flows (A -> B -> C -> A) completing within 24 hours, where the total transferred exceeds a threshold. This simulates a basic money laundering detection pattern.

```cypher
// Setup hint: Use datetime properties on Transaction nodes
// and variable-length patterns with time-window filtering.
// Chain APOC path expanders with terminatorNodes set to the
// starting account to detect cycles.
```

---

## Real-World Scenario: Multi-Algorithm Pipeline for Influence Analysis

A complete worked example showing how to combine multiple algorithms in a single analysis session:

```cypher
// 1. Create the graph projection
CALL gds.graph.project('influence-analysis', 'Person',
    { KNOWS: { orientation: 'UNDIRECTED', properties: ['weight'] } }
);

// 2. Check connectivity
CALL gds.wcc.stats('influence-analysis')
YIELD componentCount;
// Assert componentCount = 1 (single connected component)

// 3. Run PageRank
CALL gds.pageRank.mutate('influence-analysis', {
    maxIterations: 20, dampingFactor: 0.85, mutateProperty: 'pr'
});

// 4. Run betweenness
CALL gds.betweenness.mutate('influence-analysis', {
    mutateProperty: 'bc'
});

// 5. Run Louvain community detection
CALL gds.louvain.mutate('influence-analysis', {
    mutateProperty: 'community'
});

// 6. Write all results to the database in one go
CALL gds.graph.nodeProperties.write('influence-analysis',
    ['pr', 'bc', 'community']
);

// 7. Query for bridge influencers:
//    high PageRank + high betweenness + connects multiple communities
MATCH (p:Person)
WHERE p.pr > 0.5 AND p.bc > 10
WITH p
MATCH (p)-[:KNOWS]-(neighbor:Person)
WITH p, collect(DISTINCT neighbor.community) AS neighbor_communities
WHERE size(neighbor_communities) > 1
RETURN p.name, p.pr, p.bc, p.community,
       neighbor_communities,
       size(neighbor_communities) AS communities_bridged
ORDER BY communities_bridged DESC, p.pr DESC;

// 8. Clean up
CALL gds.graph.drop('influence-analysis');
```

This pipeline identifies people who are simultaneously influential (high PageRank), act as information brokers (high betweenness), and connect multiple communities — the most strategically valuable nodes in any organizational network.

---

## Summary

GDS algorithms operate on in-memory projected graphs, separate from the production graph, allowing computationally intensive analysis without impacting operational queries. The projection is the central entry point for all Neo4j analytical algorithms. Key takeaways:

- **shortestPath** uses BFS and is optimal for unweighted graphs
- **Dijkstra/A*** handle weighted graphs; A* needs geographic coordinates
- **APOC path expanders** filter during traversal, not after — essential for complex traversal logic
- **PageRank** measures importance through incoming connections from other important nodes
- **Betweenness** identifies bridges; **Closeness** identifies central spreaders
- **Louvain** is the go-to community detection; **WCC** is the prerequisite connectivity check
- **Node Similarity** and **Link Prediction** enable recommendation and connection suggestion
- Always bound variable-length patterns, filter before traversal, and profile your queries
- Use `.mutate()` to chain algorithms in a pipeline; use `.write()` to persist results for production queries
- Run WCC as a prerequisite before any centrality or community algorithm to verify graph connectivity
