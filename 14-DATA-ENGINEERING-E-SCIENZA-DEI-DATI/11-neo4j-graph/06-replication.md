# Neo4j — Cluster, Replica e Alta Disponibilità

## Modalità di Deployment

### Standalone (Development/Test)

Singolo server, nessuna replica. Adatto solo per sviluppo locale o ambienti non critici.

```bash
# neo4j.conf per standalone
server.default_listen_address=0.0.0.0
dbms.mode=SINGLE
```

### Causal Cluster (Produzione, Enterprise)

Il **Causal Cluster** è la modalità HA enterprise di Neo4j. Basato sul protocollo **Raft** per il consenso, garantisce:

- **Alta disponibilità**: tolleranza ai failure di nodi
- **Causal consistency**: le letture possono essere garantite causalmente consistenti con le scritture precedenti
- **Scalabilità delle letture**: replica la lettura su più nodi

### Topologia del Cluster

```
┌─────────────────────────────────────┐
│           Causal Cluster            │
│                                     │
│  Core Members (Primary):           │
│  ┌──────┐ ┌──────┐ ┌──────┐       │
│  │Core 1│ │Core 2│ │Core 3│       │
│  │Leader│ │Follow│ │Follow│       │
│  └──────┘ └──────┘ └──────┘       │
│       ↑ Raft consensus              │
│                                     │
│  Read Replicas (Secondary):        │
│  ┌──────┐ ┌──────┐                │
│  │  RR1 │ │  RR2 │  ← solo lettura│
│  └──────┘ └──────┘                │
└─────────────────────────────────────┘
```

**Core Members**: partecipano al consenso Raft. Minimo 3 per tollerare 1 failure, 5 per tollerare 2 failure.

**Read Replicas**: non partecipano al consenso. Ricevono le transazioni dal leader, servono solo query di lettura. Scalabili orizzontalmente.

---

## Configurazione del Cluster

```properties
# neo4j.conf su tutti i nodi core

# Ruolo del nodo
dbms.mode=CORE

# Discovery: come i nodi si trovano
causal_clustering.discovery_type=LIST
causal_clustering.initial_discovery_members=core1:5000,core2:5000,core3:5000

# Porte interne del cluster
causal_clustering.discovery_listen_address=:5000
causal_clustering.transaction_listen_address=:6000
causal_clustering.raft_listen_address=:7000

# Numero minimo di core per formare un cluster
causal_clustering.minimum_core_cluster_size_at_formation=3
causal_clustering.minimum_core_cluster_size_at_runtime=3

# Timeout Raft
causal_clustering.leader_election_timeout=7s
causal_clustering.raft_log_rotation_size=250m
```

```properties
# Per i Read Replicas
dbms.mode=READ_REPLICA
causal_clustering.discovery_type=LIST
causal_clustering.initial_discovery_members=core1:5000,core2:5000,core3:5000
causal_clustering.transaction_listen_address=:6000
```

---

## Causal Consistency e Bookmarks

Il **bookmark** è il meccanismo che permette la causal consistency: dopo una write, il client riceve un bookmark che può passare alla read successiva. Il cluster garantisce che la read veda le scritture fino a quel bookmark.

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "neo4j://cluster-lb:7687",
    auth=("neo4j", "password")
)

# Scrittura che ritorna un bookmark
with driver.session(database="neo4j") as session:
    result = session.run(
        "CREATE (p:Person {id: $id, name: $name}) RETURN p",
        id=1001, name="Alice"
    )
    result.consume()
    # Il bookmark è disponibile dopo il consume
    bookmark = session.last_bookmark()

# Lettura causalmente consistente: usa il bookmark
with driver.session(
    database="neo4j",
    bookmarks=[bookmark]
) as session:
    result = session.run(
        "MATCH (p:Person {id: $id}) RETURN p.name",
        id=1001
    )
    # Garantito di vedere la write precedente
    for record in result:
        print(record["p.name"])
```

---

## Routing delle Query nel Cluster

Il driver Neo4j gestisce automaticamente il routing:

- **Scritture** → sempre al nodo **Leader**
- **Letture** → distribuite su Core + Read Replicas

```python
# Sessione di scrittura (va sempre al leader)
with driver.session(
    database="neo4j",
    default_access_mode=neo4j.WRITE_ACCESS
) as session:
    session.run("CREATE (p:Person {name: 'Alice'})")

# Sessione di lettura (può andare su qualsiasi nodo)
with driver.session(
    database="neo4j",
    default_access_mode=neo4j.READ_ACCESS
) as session:
    result = session.run("MATCH (p:Person) RETURN p.name LIMIT 10")
```

In Cypher, si può specificare esplicitamente il routing con il pragma:

```cypher
/*ROUTING route: {writers: [], readers: ["neo4j://replica1:7687"]}*/
MATCH (p:Person) RETURN p LIMIT 100;
```

---

## Monitoraggio del Cluster

```cypher
// Stato del cluster (da eseguire sul Leader)
CALL dbms.cluster.overview() YIELD id, addresses, role, groups, database
RETURN *;

// Database status su ogni nodo
SHOW DATABASES YIELD name, role, requestedStatus, currentStatus, statusMessage;

// Log delle transazioni Raft
CALL dbms.cluster.raftMessages() YIELD ...;
```

```bash
# Stato via neo4j-admin
neo4j-admin server report

# Health check via HTTP
curl -u neo4j:password http://localhost:7474/db/neo4j/cluster/status
```

---

## Backup e Ripristino

### Backup Online (neo4j-admin)

```bash
# Backup completo mentre il DB è in esecuzione
neo4j-admin database backup \
    --to-path=/backup/neo4j/ \
    --database=neo4j \
    --from=localhost:6362 \
    --verbose

# Backup differenziale (incrementale dall'ultimo backup completo)
neo4j-admin database backup \
    --to-path=/backup/neo4j/ \
    --database=neo4j \
    --from=localhost:6362 \
    --include-metadata=all \
    --keep-failed=false

# Backup a S3 (con AWS CLI disponibile)
neo4j-admin database backup \
    --to-path=s3://my-bucket/neo4j-backups/ \
    --database=neo4j \
    --from=localhost:6362
```

### Ripristino

```bash
# Il ripristino richiede che il database sia fermato (o offline)
neo4j-admin server stop

neo4j-admin database restore \
    --from-path=/backup/neo4j/ \
    --database=neo4j \
    --overwrite-destination=true

neo4j-admin server start
```

### Dump e Load (per migrazioni)

```bash
# Dump (crea un archivio del database)
neo4j-admin database dump --database=neo4j --to-path=/tmp/dump/

# Load (importa da dump)
neo4j-admin database load --database=neo4j --from-path=/tmp/dump/ --overwrite-destination=true
```

---

## Neo4j Aura: Managed Cloud

Neo4j Aura è il servizio managed su GCP con replica automatica e backup gestito.

```python
# Connessione ad Aura (stessa API del driver)
driver = GraphDatabase.driver(
    "neo4j+s://xxxxxxxx.databases.neo4j.io",  # bolt+ssc per versioni vecchie
    auth=("neo4j", "your-aura-password")
)
```

L'alta disponibilità in Neo4j Enterprise con Causal Clustering è trasparente al codice applicativo grazie al driver che gestisce autonomamente il routing verso il Leader o le repliche. La causal consistency tramite bookmark risolve il problema di read-your-writes in un sistema distribuito.

---

## Raft Consensus — Deep Dive

### How Raft Works in Neo4j

Raft ensures all Core members agree on the same sequence of committed transactions. The protocol has three states for each Core member:

| State | Role |
|-------|------|
| **Leader** | Accepts writes, replicates to followers via AppendEntries |
| **Follower** | Receives replicated entries, votes in elections |
| **Candidate** | Requests votes when leader times out |

```
Normal operation (steady state):
Client → Leader: WRITE tx
Leader → Followers: AppendEntries(tx)
Followers → Leader: ACK
Leader commits when majority ACK (quorum = N/2 + 1)
Leader → Client: SUCCESS + bookmark

Election (leader failure):
Follower timeout → becomes Candidate
Candidate → all Cores: RequestVote
If majority votes → becomes Leader
New Leader → Followers: AppendEntries (catch up)
```

### Quorum Table

| Cores | Quorum | Tolerated Failures |
|-------|--------|--------------------|
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

Odd numbers preferred — even numbers waste a node without increasing fault tolerance. For example, 4 cores still only tolerates 1 failure (quorum = 3), same as 3 cores.

### Raft Log Management

```properties
# neo4j.conf — tune Raft log behavior
causal_clustering.raft_log_rotation_size=250m
causal_clustering.raft_log_pruning_strategy=keep_all  # or: 1g size, 7 days
causal_clustering.raft_log_reader_pool_size=8

# Catchup protocol for followers that fell behind
causal_clustering.catchup_batch_size=64
causal_clustering.pull_interval=1s
causal_clustering.log_shipping_max_lag=256
```

When a follower falls too far behind the leader's Raft log, it triggers a **store copy** instead of replaying individual transactions — a full snapshot transfer.

---

## Multi-Database Clustering

Neo4j 5+ supports multiple databases within a single DBMS. Each database has independent topology:

```cypher
// Create database with specific topology
CREATE DATABASE analytics
    TOPOLOGY 3 PRIMARIES 2 SECONDARIES;

// Alter topology
ALTER DATABASE analytics
    SET TOPOLOGY 5 PRIMARIES 3 SECONDARIES;

// Show database placement
SHOW DATABASE analytics YIELD name, address, role, writer, currentStatus;
```

### Database-Level Routing

```properties
# Route specific databases to specific servers
server.databases.default_to_server_group=group1
# Server groups are assigned per server:
server.groups=group1,analytics-tier
```

```cypher
// Pin a database to a server group
ALTER DATABASE analytics
    SET ACCESS READ WRITE
    SET TOPOLOGY 3 PRIMARIES 2 SECONDARIES
    OPTIONS {primaryServerGroups: ['analytics-tier']};
```

---

## Cross-Datacenter Deployment

### Active-Passive with Disaster Recovery

```
DC-Primary (Milano)          DC-DR (Roma)
┌────────────────┐           ┌────────────────┐
│ Core1 (Leader) │──Raft───→│ Core4 (Follow)  │
│ Core2 (Follow) │──Raft───→│ Core5 (Follow)  │
│ Core3 (Follow) │           │                 │
│ RR1, RR2       │           │ RR3             │
└────────────────┘           └────────────────┘
```

```properties
# Core in DC-Primary
server.groups=dc-milano
causal_clustering.server_groups_to_route_against=dc-milano

# Core in DC-DR
server.groups=dc-roma
causal_clustering.refuse_to_be_leader=true  # never becomes leader in normal ops

# Clients in Milano route reads to Milano replicas first
```

### Server Groups for Locality

```properties
# core1.conf (Milano)
server.groups=milano

# core4.conf (Roma)
server.groups=roma

# Read replica in Roma
server.groups=roma
causal_clustering.server_policies.roma=groups(roma)->min(1)
```

```python
# Python driver with server-side routing policy
driver = GraphDatabase.driver(
    "neo4j://cluster-lb:7687",
    auth=("neo4j", "password"),
)

# The policy name matches the server-side configuration
with driver.session(
    database="neo4j",
    default_access_mode=neo4j.READ_ACCESS,
    # Prefer read replicas in our datacenter
    bookmark_manager=neo4j.GraphDatabase.bookmark_manager()
) as session:
    result = session.run("MATCH (p:Person) RETURN p.name LIMIT 10")
```

---

## Rolling Upgrade Procedure

Upgrading a Neo4j cluster without downtime:

```bash
# Step 1: Backup from the leader
neo4j-admin database backup --database=neo4j --to-path=/backup/pre-upgrade/

# Step 2: Upgrade read replicas first (one at a time)
# On each read replica:
systemctl stop neo4j
# Replace binaries with new version
dpkg -i neo4j-enterprise-5.x.x_all.deb  # or equivalent
neo4j-admin server migrate
systemctl start neo4j
# Verify health before moving to next replica
curl -u neo4j:password http://rr1:7474/db/neo4j/cluster/status

# Step 3: Upgrade follower cores (one at a time)
# On each follower core:
systemctl stop neo4j
dpkg -i neo4j-enterprise-5.x.x_all.deb
neo4j-admin server migrate
systemctl start neo4j
# Wait for it to rejoin cluster and sync

# Step 4: Upgrade the leader last
# The cluster will elect a new leader from the upgraded followers
systemctl stop neo4j  # triggers election
dpkg -i neo4j-enterprise-5.x.x_all.deb
neo4j-admin server migrate
systemctl start neo4j

# Step 5: Verify full cluster health
cypher-shell -u neo4j -p password "CALL dbms.cluster.overview()"
```

---

## Kubernetes Deployment (Neo4j Helm Chart)

```yaml
# values.yaml for Neo4j Helm chart
neo4j:
  name: my-cluster
  edition: enterprise
  password: "strongPassword123!"
  
  # Core servers
  core:
    numberOfServers: 3
    resources:
      requests:
        cpu: "2"
        memory: "8Gi"
      limits:
        cpu: "4"
        memory: "16Gi"
    persistentVolume:
      size: 100Gi
      storageClass: ssd
    config:
      server.memory.pagecache.size: "4g"
      server.memory.heap.max_size: "4g"

  # Read replicas
  readReplica:
    numberOfServers: 2
    resources:
      requests:
        cpu: "1"
        memory: "4Gi"
    persistentVolume:
      size: 100Gi

  # Service configuration
  services:
    neo4j:
      type: ClusterIP
      port: 7687
```

```bash
# Deploy
helm install neo4j neo4j/neo4j-cluster -f values.yaml -n neo4j

# Scale read replicas
helm upgrade neo4j neo4j/neo4j-cluster \
    --set readReplica.numberOfServers=4 -n neo4j

# Check pods
kubectl get pods -n neo4j -l app.kubernetes.io/name=neo4j
```

---

## Docker Compose — 3-Node Cluster

```yaml
# docker-compose.yml
services:
  core1:
    image: neo4j:5-enterprise
    hostname: core1
    environment:
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4J_AUTH=neo4j/password
      - NEO4J_EDITION=enterprise
      - NEO4J_dbms_mode=CORE
      - NEO4J_causal__clustering_discovery__type=LIST
      - NEO4J_causal__clustering_initial__discovery__members=core1:5000,core2:5000,core3:5000
      - NEO4J_causal__clustering_minimum__core__cluster__size__at__formation=3
      - NEO4J_server_memory_pagecache_size=1g
      - NEO4J_server_memory_heap_max__size=1g
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - core1-data:/data
    networks:
      - neo4j-cluster

  core2:
    image: neo4j:5-enterprise
    hostname: core2
    environment:
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4J_AUTH=neo4j/password
      - NEO4J_EDITION=enterprise
      - NEO4J_dbms_mode=CORE
      - NEO4J_causal__clustering_discovery__type=LIST
      - NEO4J_causal__clustering_initial__discovery__members=core1:5000,core2:5000,core3:5000
      - NEO4J_causal__clustering_minimum__core__cluster__size__at__formation=3
    ports:
      - "7475:7474"
      - "7688:7687"
    volumes:
      - core2-data:/data
    networks:
      - neo4j-cluster

  core3:
    image: neo4j:5-enterprise
    hostname: core3
    environment:
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4J_AUTH=neo4j/password
      - NEO4J_EDITION=enterprise
      - NEO4J_dbms_mode=CORE
      - NEO4J_causal__clustering_discovery__type=LIST
      - NEO4J_causal__clustering_initial__discovery__members=core1:5000,core2:5000,core3:5000
      - NEO4J_causal__clustering_minimum__core__cluster__size__at__formation=3
    ports:
      - "7476:7474"
      - "7689:7687"
    volumes:
      - core3-data:/data
    networks:
      - neo4j-cluster

  read-replica1:
    image: neo4j:5-enterprise
    hostname: rr1
    environment:
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4J_AUTH=neo4j/password
      - NEO4J_EDITION=enterprise
      - NEO4J_dbms_mode=READ_REPLICA
      - NEO4J_causal__clustering_discovery__type=LIST
      - NEO4J_causal__clustering_initial__discovery__members=core1:5000,core2:5000,core3:5000
    ports:
      - "7477:7474"
      - "7690:7687"
    volumes:
      - rr1-data:/data
    networks:
      - neo4j-cluster
    depends_on:
      - core1
      - core2
      - core3

volumes:
  core1-data:
  core2-data:
  core3-data:
  rr1-data:

networks:
  neo4j-cluster:
    driver: bridge
```

---

## Monitoring Cluster Health

### Prometheus Metrics for Cluster

```properties
# neo4j.conf — expose cluster metrics
server.metrics.enabled=true
server.metrics.prometheus.enabled=true
server.metrics.prometheus.endpoint=localhost:2004

# Key cluster metrics to monitor:
# neo4j_causal_clustering_core_append_index     — Raft log progress
# neo4j_causal_clustering_core_commit_index     — committed entries
# neo4j_causal_clustering_core_is_leader        — 1 if this node is leader
# neo4j_causal_clustering_core_in_flight_cache_total_bytes
# neo4j_causal_clustering_core_message_processing_delay
```

### Health Check Endpoints

```bash
# Cluster member status
curl -s http://core1:7474/db/neo4j/cluster/available | jq .
# Returns: {"status": "available"}

# Writable check (leader only)
curl -s http://core1:7474/db/neo4j/cluster/writable | jq .

# Read-only check (any member)
curl -s http://rr1:7474/db/neo4j/cluster/read-only | jq .
```

### Alerting Rules (Prometheus)

```yaml
groups:
  - name: neo4j-cluster
    rules:
      - alert: Neo4jNoLeader
        expr: sum(neo4j_causal_clustering_core_is_leader) == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "No leader elected in Neo4j cluster"

      - alert: Neo4jReplicationLag
        expr: >
          neo4j_causal_clustering_core_append_index -
          neo4j_causal_clustering_core_commit_index > 1000
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Neo4j Raft replication lag exceeds 1000 entries"

      - alert: Neo4jClusterMemberDown
        expr: up{job="neo4j"} == 0
        for: 1m
        labels:
          severity: critical
```

---

## Troubleshooting

### 1. Cluster Fails to Form at Startup

**Symptom**: Cores start but never elect a leader, logs show "Waiting for other members".

**Fix**: Ensure all cores can reach each other on discovery port (5000) and all are listed in `initial_discovery_members`. Check firewalls and DNS resolution:
```bash
# From core1, verify connectivity to core2 and core3
nc -zv core2 5000
nc -zv core3 5000
```

### 2. Leader Election Storm (Frequent Leader Changes)

**Symptom**: Leader keeps changing every few seconds.

**Root cause**: Network instability or GC pauses exceeding election timeout.

**Fix**:
```properties
# Increase election timeout
causal_clustering.leader_election_timeout=15s
# Tune JVM to reduce GC pauses
server.memory.heap.initial_size=4g
server.memory.heap.max_size=4g
# Use G1GC with max pause target
server.jvm.additional=-XX:MaxGCPauseMillis=200
```

### 3. Read Replica Cannot Catch Up

**Symptom**: Read replica shows "CATCHING_UP" status indefinitely.

**Fix**: The replica may need a full store copy. Check disk space and network bandwidth:
```bash
# Check store size on leader
neo4j-admin database info --database=neo4j
# Ensure replica has enough disk for the full store
df -h /var/lib/neo4j/data
```

### 4. Split-Brain Scenario

**Symptom**: Two partitions both think they have a leader.

**Reality**: With Raft, true split-brain is prevented by quorum requirement. The minority partition's "leader" cannot commit writes (no quorum). However, stale reads from the minority partition are possible.

**Mitigation**: Use bookmarks for all reads that must be consistent.

### 5. Bookmark Not Honored

**Symptom**: Read after write returns stale data despite passing bookmark.

**Root cause**: Read session uses a different database, or bookmark was lost between requests.

**Fix**: Ensure bookmark is passed correctly and database name matches:
```python
# Verify bookmark is propagated
with driver.session(database="neo4j") as write_session:
    write_session.run("CREATE (p:Person {name: 'Test'})")
    write_session.close()
    bm = write_session.last_bookmarks()

with driver.session(database="neo4j", bookmarks=bm) as read_session:
    result = read_session.run("MATCH (p:Person {name: 'Test'}) RETURN p")
```

### 6. Backup Fails with "Database Not Found"

**Symptom**: `neo4j-admin database backup` returns database not found.

**Fix**: Ensure backup port is open and backup is enabled:
```properties
# neo4j.conf
server.backup.enabled=true
server.backup.listen_address=0.0.0.0:6362
```

### 7. Restore Fails with Version Mismatch

**Symptom**: Cannot restore backup from different Neo4j version.

**Fix**: Use `neo4j-admin database migrate` to upgrade the backup before restoring:
```bash
neo4j-admin database migrate --database=neo4j --from-path=/backup/old-version/
```

### 8. Cluster Members Show Different Data Counts

**Symptom**: `MATCH (n) RETURN count(n)` returns different values on different cores.

**Root cause**: Query hitting a follower before it replicated the latest transactions.

**Fix**: Use bookmarks or query the leader explicitly. Check replication lag metrics.

### 9. Cannot Add New Core to Running Cluster

**Symptom**: New core joins but stays in "CATCHING_UP" or fails to join.

**Fix**: Ensure the new core has the same `initial_discovery_members` and that the cluster has capacity. Check that `minimum_core_cluster_size_at_runtime` allows the current count.

### 10. Performance Drops After Adding Read Replicas

**Symptom**: Write throughput decreases after adding more replicas.

**Root cause**: More replicas = more replication overhead on the leader.

**Fix**: Read replicas do not participate in quorum and should not affect write commit latency. Check if replicas are consuming excessive bandwidth. Limit `causal_clustering.pull_interval` if needed:
```properties
causal_clustering.pull_interval=2s  # default 1s, increase if bandwidth constrained
```

---

## FAQ

### 1. What is the minimum cluster size for production?

3 Core members is the minimum for fault tolerance (tolerates 1 failure). For critical production, 5 cores (tolerates 2 failures) with 2+ read replicas is recommended.

### 2. Can Core members be in different datacenters?

Yes, but Raft consensus requires majority quorum for every write. Cross-DC latency directly adds to write latency. Keep quorum-forming cores in the same DC, and use remote cores for DR with `refuse_to_be_leader=true`.

### 3. What happens when the leader dies?

Followers detect the missing heartbeat after `leader_election_timeout` (default 7s), then trigger an election. A new leader is elected within seconds. During election, writes are blocked but reads from replicas continue.

### 4. Can I read from the leader?

Yes. The leader serves both reads and writes. However, routing reads to replicas reduces load on the leader, improving write throughput.

### 5. How does the driver handle failover?

The Neo4j driver maintains a routing table that lists the current leader and available readers. When the leader fails, the driver refreshes the routing table and retries the transaction on the new leader. This is transparent to the application.

### 6. What is the difference between Core and Read Replica?

Cores participate in Raft consensus and can be elected leader. Read Replicas only pull committed transactions and serve reads. Cores require fast, low-latency networking between them. Read Replicas can be geographically distributed.

### 7. Can I do zero-downtime upgrades?

Yes, via rolling upgrade. Upgrade read replicas first, then followers, then the leader last. The cluster remains available throughout. Ensure all nodes run compatible versions during the rolling window.

### 8. How do I size persistent volumes for Kubernetes?

Rule of thumb: 3x the expected data size. Neo4j stores data files, transaction logs, and Raft logs. Monitor disk usage and expand PVCs proactively. Use SSD-backed storage classes for production.

### 9. Should I use Neo4j Aura or self-managed cluster?

Aura: lower operational overhead, automatic backups, scaling, patches. Use for teams without dedicated DBA. Self-managed: full control over configuration, placement, network, cost optimization. Use when you need multi-DC, custom tuning, or specific compliance requirements.

### 10. How do I test disaster recovery?

Schedule regular DR drills:
1. Backup the current state
2. Simulate leader failure (stop the leader container)
3. Verify automatic failover completes within SLA
4. Verify all reads continue working
5. Restart the old leader and verify it re-joins as follower
6. Test full cluster restore from backup to a separate environment

Neo4j clustering provides transparent high availability and read scaling through Raft-based consensus, causal consistency via bookmarks, and horizontal read scaling through read replicas. The driver handles all routing and failover logic, making the cluster topology invisible to application code.
