# MySQL/MariaDB Sharding

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: draft

## Skip list
- [ ] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Sharding Concepts
2. Sharding Architecture
3. Sharding Keys
4. Application-Level Sharding
5. Vitess e Alternative
6. Sharding Patterns
7. Rebalancing

---

## 1. Sharding Concepts

### 1.1 What is Sharding

**Sharding** è una tecnica per partizionare i dati su multiple database server. Ogni shard contiene un sottoinsieme dei dati, permettendo di scalare orizzontalmente. È l'evoluzione naturale quando un singolo database non riesce più a gestire il carico.

**Quando serve sharding**:
- Dataset troppo grande per un singolo server (tipicamente >1TB)
- Write throughput supera capacità single server (>1000 writes/sec)
- Necessità di geographical distribution (latency per utenti in diverse aree)
- Compliance (data residency in diverse giurisdizioni)
- Costo: singolo server Enterprise costerebbe troppo

**Vantaggi dello sharding**:
- **Scalabilità lineare**: ogni shard aggiunge capacità proporzionale
- **Performance prevedibili**: query su shard sono veloci
- **Isolation dei problemi**: un shard che performance è isolato
- **Cost-effective**: usa server commodity invece di hardware Enterprise

**Svantaggi dello sharding**:
- **Complessità architetturale**: gestire multiple database
- **Cross-shard queries costose**: richiedono aggregazione
- **Rebalancing difficile**: aggiungere/shiftare shard è complesso
- **Operational overhead**: backup, monitoring, upgrade multipli
- **Transaction limits**: transactions non possono coprire shard multipli

### 1.2 Sharding vs Partitioning

**Table Partitioning** (MySQL/MariaDB):
- Una tabella, multiple partitions sullo stesso server
- Gestito nativamente dal database
- SQL standard funziona
- Non fornisce scalabilità (tutto sullo stesso server)

**Sharding**:
- Multiple server, ogni shard ha subset dei dati
- Gestione a livello applicativo o middleware
- Richiede routing delle queries
- Fornisce scalabilità reale

**Confronto**:
| Caratteristica | Partitioning | Sharding |
|----------------|--------------|----------|
| Scalabilità | No | Sì (orizzontale) |
| Server multipli | No | Sì |
| Cross-partition query | Semplice | Complessa |
| Routing | Nativo | Esterno |
| Rebalancing | Semplice | Complesso |

**Esempio di quando usare cosa**:
- Table partitioning: tabelle con 100GB che beneficiano di partition pruning
- Sharding: applicazione con milioni di utenti, tabelle da 10TB+

### 1.3 Sharding Terminology

**Shard**: Singolo database che contiene un sottoinsieme dei dati.

**Shard Key**: Colonna o set di colonne usate per determinare a quale shard appartiene un record.

**Shard Router**: Componente che indirizza le queries allo shard corretto.

**Shard Catalog**: Metadata che mappa shard keys a shard locations.

**Data Distribution**:
- **Even distribution**: ogni shard ha approssimativamente stessa dimensione
- **Skewed distribution**: alcuni shard più grandi (hot spots)

---

## 2. Sharding Architecture

### 2.1 Shard Architecture Patterns

**Horizontal Sharding (Data Split)**:
```
                 [Router/Proxy]
                        │
        +--------------+--------------+
        |              |              |
    [Shard 1]     [Shard 2]      [Shard 3]
   users A-G     users H-P     users Q-Z
```
Ogni shard contiene subset delle righe basato sullo shard key.

**Vertical Sharding (Feature Split)**:
```
                 [Router]
                        │
     +----------+------+------+
     |          |             |
[Users DB] [Orders DB] [Products DB]
```
Ogni shard contiene diverse tabelle intere. Utile per tabelle con accesso patterns diversi.

**Hybrid**:
```
                 [Router]
                        │
        +--------------+--------------+
        |              |              |
    [Shard 1]     [Shard 2]      [Shard 3]
  (users A-I)  (users J-R)    (users S-Z)
      +             +              +
   +-------+    +-------+      +-------+
   |orders |    |orders |      |orders |
   |products|   |products     |products
```
Combina horizontal e vertical per massima flessibilità.

### 2.2 Components

**Shard Gateway/Router**:
- Direziona queries allo shard corretto
- Può essere: MySQL Proxy, ProxySQL, application logic, Vitess
- Può fare: connection pooling, query routing, load balancing

**Shard Catalog**:
- Mappa shard key a shard location
- Può essere:
  - **Distributed**: application caches metadata
  - **Centralized**: database lookups per routing
- Deve essere highly available

**Shard Servers**:
- Ogni server contiene subset dei dati
- Può essere:
  - Single instance
  - Master-slave replication
  - Galera cluster
- Each shard can have its own replication setup

### 2.3 Topologies

**Direct Connection**:
```
[App Server] → [Shard 1]
[App Server] → [Shard 2]
[App Server] → [Shard 3]
```
Ogni app server ha connections a tutti gli shard. Routing nell'applicazione.

**Proxy-Based**:
```
[App Server] → [Proxy] → [Shards]
```
Proxy centralizzato gestisce routing e connection pooling.

**Tiered**:
```
[App] → [Router Layer] → [Shard Group 1]
                            → [Shard Group 2]
                            → [Shard Group 3]
```
Per scale molto grandi, più livelli di routing.

---

## 2. Sharding Architecture

### 2.1 Shard Architecture Patterns

**Horizontal Sharding (Data Split)**:
```
                 [Router/Proxy]
                        |
        +--------------+--------------+
        |              |              |
    [Shard 1]     [Shard 2]      [Shard 3]
   users A-G     users H-P     users Q-Z
```

**Vertical Sharding (Feature Split)**:
```
                 [Router]
                        |
     +----------+------+------+
     |          |             |
[Users DB] [Orders DB] [Products DB]
```

**Hybrid**:
- Combina horizontal e vertical
- Primo split per 功能 (users, orders), poi horizontal per ogni 功能

### 2.2 Components

**Shard Gateway/Router**:
- Direziona queries allo shard corretto
- MySQL Proxy, Vitess, application logic

**Shard Catalog**:
- Mappa shard key a shard location
- Può essere distributed o centralizzato

**Shard Servers**:
- Ogni server contiene subset dei dati
- Può essere replica set

---

## 3. Sharding Keys

### 3.1 Choosing Shard Key

Il **shard key** è la colonna (o combination di colonne) che determina come i dati sono distribuiti tra gli shard. È la decisione più critica nello sharding.

**Criteri per buon shard key**:
1. **Uniform distribution**: i dati sono distribuiti equamente
2. **Query locality**: la maggioranza delle queries riguarda un singolo shard
3. **Bilanciamento reads/writes**: non ci sono hot spots
4. **Stability**: non cambia frequentemente
5. **Cardinality**: abbastanza valori unici per distribuire

**Considerazioni**:
- Queries che usano lo shard key sono efficienti
- Queries senza shard key richiedono scatter-gather (lento)
- Hot spots causano problemi di performance

### 3.2 Types of Shard Keys

**Range-Based**:
```sql
-- Esempio: user_id range
Shard 1: user_id 0-9999999
Shard 2: user_id 10000000-19999999
Shard 3: user_id 20000000-29999999

-- Vantaggi:
-- - Semplice da implementare
-- - Range queries efficienti
-- - Ordered data locality

-- Svantaggi:
-- - Hot spots (nuovi utenti shard 1)
-- - Skewed distribution se distribuzione non uniforme
```

```python
def get_shard_by_range(user_id):
    if user_id < 10000000:
        return 0
    elif user_id < 20000000:
        return 1
    else:
        return 2
```

**Hash-Based**:
```sql
-- Esempio: hash(user_id) % num_shards
shard_id = hash(user_id) % 4
-- Distribuisce uniformly basato su hash

-- Vantaggi:
-- - Distribuzione uniforme
-- - No hot spots

-- Svantaggi:
-- - No range queries efficienti
-- - Dati non ordinati logicamente
-- - Richiede same hash function su tutti gli shard
```

```python
import hashlib

def get_shard_hash(user_id, num_shards):
    hash_value = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
    return hash_value % num_shards

# Alternative più semplice
def get_shard_simple(user_id):
    return user_id % 4  # se user_id è distribuito uniformemente
```

**Directory-Based (Lookup)**:
```sql
-- Lookup table per mapping
-- shard_id = lookup(user_id)

-- Tabella di lookup:
-- user_id | shard_id
-- 1       | 0
-- 2       | 1
-- 3       | 2

-- Vantaggi:
-- - Massima flessibilità
-- - Shard assignment dinamico
-- - Può bilanciare manualmente

-- Svantaggi:
-- - Lookup overhead
-- - Single point of failure (catalog)
-- - Complexità di gestione
```

```python
# Directory-based con caching
class DirectoryRouter:
    def __init__(self):
        self.cache = {}
        self.db = {}  # lookup table
    
    def get_shard(self, user_id):
        if user_id in self.cache:
            return self.cache[user_id]
        
        shard_id = self.db.lookup(user_id)
        self.cache[user_id] = shard_id
        return shard_id
```

**Composite Key**:
```sql
-- Combinare più colonne
-- shard = hash(user_id + tenant_id) % shards

-- Utile per multi-tenant applications
```

```python
def get_shard_composite(user_id, tenant_id):
    combined = f"{tenant_id}:{user_id}"
    return hash(combined) % 4

# Esempio: per assicurare che dati di uno tenant siano sullo stesso shard
def get_shard_tenant(tenant_id):
    return tenant_id % 4
```

### 3.3 Examples per Use Case

**Sharding by User ID** (e-commerce):
```python
# Per applicazioni B2C
# Ogni utente ha i propri dati (orders, cart, etc)
def get_shard(user_id, num_shards=4):
    return user_id % num_shards
# Query per utente specifico: shard lookup
# Query "my orders": lookup preciso
# Query "all orders last month": scatter-gather
```

**Sharding by Date** (timeseries):
```python
# Per dati di logging, analytics
def get_shard(created_at, num_shards=4):
    year_month = created_at.strftime("%Y%m")
    return int(year_month) % num_shards

# Vantaggi:
# - Dati recenti su shard caldo (ottimizzato)
# - Vecchi dati su shard freddo
# - Easy cleanup (drop old shard)
```

**Sharding by Region** (geografico):
```python
# Per compliance o latency
def get_shard(user_region, num_shards=4):
    region_to_shard = {
        'US': 0,
        'EU': 1,
        'APAC': 2,
        'OTHER': 3
    }
    return region_to_shard.get(user_region, 3)
```

**Composite per Multi-Tenant**:
```python
# SaaS con isolation
def get_shard(tenant_id):
    return tenant_id % 16
# Tutti i dati di un tenant sullo stesso shard
# Semplifica query, garantisce isolation
```

---

## 4. Application-Level Sharding

### 4.1 Implement Sharding in Application

Implementare sharding direttamente nell'applicazione dà massimo controllo.

**Pattern: Database Router**:
```python
import os
import pymysql
from contextlib import contextmanager

class ShardRouter:
    def __init__(self, num_shards=4):
        self.num_shards = num_shards
        self.connections = {}
        
        # Config per ogni shard
        self.shard_configs = [
            {'host': 'shard0.db.local', 'port': 3306},
            {'host': 'shard1.db.local', 'port': 3306},
            {'host': 'shard2.db.local', 'port': 3306},
            {'host': 'shard3.db.local', 'port': 3306},
        ]
    
    def get_shard(self, user_id):
        return user_id % self.num_shards
    
    @contextmanager
    def get_connection(self, user_id):
        shard_id = self.get_shard(user_id)
        
        if shard_id not in self.connections:
            config = self.shard_configs[shard_id]
            self.connections[shard_id] = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user='app',
                password='password',
                database='mydb'
            )
        
        conn = self.connections[shard_id]
        try:
            yield conn
        finally:
            conn.commit()

router = ShardRouter(4)

# Usage
def get_user(user_id):
    with router.get_connection(user_id) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()

def create_order(user_id, order_data):
    with router.get_connection(user_id) as conn:
        with conn.cursor() as cursor:
            # Must use same shard as user (same connection)
            cursor.execute(
                "INSERT INTO orders (user_id, data) VALUES (%s, %s)",
                (user_id, order_data)
            )
            return cursor.lastrowid
```

### 4.2 Routing Patterns

**Lookup-based**:
- Shard catalog centralizzato
- Ogni query lookup prima
- Più flessibile, overhead di lookup

```python
class LookupRouter:
    def __init__(self):
        # Cache lookup table
        self.cache = {}
        self.catalog = {}  # loaded from database
    
    def get_shard(self, key):
        if key in self.cache:
            return self.cache[key]
        
        if key in self.catalog:
            shard = self.catalog[key]
            self.cache[key] = shard
            return shard
        
        raise KeyError(f"Unknown key: {key}")
```

**Algorithm-based**:
- Funzione deterministica senza lookup
- Più veloce, meno flessibile

```python
class AlgorithmRouter:
    def get_shard(self, user_id):
        # Nessun lookup, solo calcolo
        return hash(user_id) % 4
```

**Hybrid**:
- Algoritmo per common cases
- Lookup per edge cases o resharding

```python
class HybridRouter:
    def get_shard(self, key):
        # Common case: algorithm
        if key.startswith('user_'):
            user_id = int(key.split('_')[1])
            return user_id % 4
        
        # Edge case: lookup
        return self.lookup(key)
```

### 4.3 Cross-Shard Queries

**Problema fondamentale**:
```sql
-- Query che tocca multiple shard
SELECT * FROM orders 
WHERE created_at > '2024-01-01' 
ORDER BY amount DESC;
-- Richiede dati da tutti gli shard!
```

**Soluzioni**:

**1. Scatter-Gather**:
```python
def query_all_shards(sql, params=None):
    results = []
    errors = []
    
    for conn in all_shard_connections:
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            results.extend(cursor.fetchall())
        except Exception as e:
            errors.append(str(e))
    
    if errors:
        raise Exception(f"Shard errors: {errors}")
    
    return results

def aggregate_all_shards():
    # Example: get total orders
    total = 0
    for conn in all_shard_connections:
        cursor.execute("SELECT COUNT(*) FROM orders")
        total += cursor.fetchone()[0]
    return total
```

**2. Denormalization**:
- Copiare dati necessari su ogni shard
- Increased storage, simplified queries
- Richiede sincronizzazione

```sql
-- Esempio: copiare summary su ogni shard
-- Tabella globale (replicated)
CREATE TABLE global_stats (
    shard_id INT,
    total_orders INT,
    last_updated TIMESTAMP
);

-- Update su ogni insert
-- Application handles sync
```

**3. Separate Aggregator**:
- Usare sistema separato per aggregazioni
- Elastic Search, ClickHouse, data warehouse

```python
# Inviare dati anche a Elasticsearch
def create_order(user_id, data):
    # Save to MySQL shard
    save_to_mysql(user_id, data)
    
    # Save to ES for analytics
    save_to_elasticsearch({
        'user_id': user_id,
        'data': data,
        'timestamp': now()
    })
    
    # Queries aggregazione via ES
def get_order_stats():
    return es_query("SELECT COUNT(*), AVG(amount) FROM orders")
```

**4. Application-level Join**:
```python
def get_user_orders_with_products(user_id):
    # Get user (single shard)
    user = get_from_mysql(f"SELECT * FROM users WHERE id = {user_id}")
    
    # Get orders (single shard - same as user)
    orders = get_from_mysql(f"SELECT * FROM orders WHERE user_id = {user_id}")
    
    # Get products (may need multiple shards)
    products = {}
    for order in orders:
        product = get_from_mysql(
            f"SELECT * FROM products WHERE id = {order['product_id']}",
            shard=product_id % 4
        )
        products[product['id']] = product
    
    return combine_user_orders_products(user, orders, products)
```

### 4.4 Transaction Handling

**Problema**: Transazioni che toccano multiple shard non sono supportate.

**Soluzioni**:

**1. Avoid cross-shard transactions**:
```python
def process_order(order):
    # Tutte le operazioni sullo stesso shard
    with shard_connection(order['user_id']) as conn:
        conn.execute("INSERT INTO orders ...", ...)
        conn.execute("UPDATE inventory ...", ...)
        conn.execute("UPDATE user_balance ...", ...)
        conn.commit()
```

**2. Two-phase commit** (sconsigliato):
```python
# Prepare phase su tutti gli shard
for shard in involved_shards:
    shard.execute("PREPARE TRANSACTION 'order_123'")

# Commit phase
for shard in involved_shards:
    try:
        shard.execute("COMMIT PREPARED 'order_123'")
    except:
        # Rollback others
        for other in involved_shards:
            other.execute("ROLLBACK PREPARED 'order_123'")
```

**3. Saga Pattern**:
```python
def order_processing(order):
    try:
        # Step 1: Reserve inventory
        reserve_inventory(order)  # single shard
        
        # Step 2: Create order
        create_order(order)  # single shard
        
        # Step 3: Charge payment
        charge_payment(order)  # separate service
        
    except PaymentFailed:
        # Compensating transactions
        release_inventory(order)
        cancel_order(order)
```

---

## 5. Vitess e Alternative

### 5.1 Vitess Overview

**Vitess** è un database clustering system per MySQL sviluppato da YouTube (ora open source sottoPlanet Labs). È la soluzione enterprise-grade per sharding MySQL.

**Features principali**:
- **Horizontal scaling**: sharding automatico
- **Connection pooling**: migliaia di connessioni
- **Query rewriting**: ottimizzazione automatica
- **Automatic failover**: alta disponibilità
- **Caching**: risultati query cache
- **Rewriting**: aggregazioni push-down

**Chi usa Vitess**:
- YouTube (creatori originali)
- Slack
- GitHub
- Zendesk
- Square

### 5.2 Vitess Architecture

```
                         [App Client]
                               │
                               v
                        [VTGate] (Router)
                               │
          +--------------------+--------------------+
          |                    |                    |
     [VTTablet]          [VTTablet]          [VTTablet]
    (shard-0)           (shard-1)           (shard-2)
          |                    |                    |
          +--------------------+--------------------+
                               │
                        [Topology]
                      (etcd/consul)
```

**Components**:

**VTGate**:
- SQL router - accetta connessioni MySQL
- Routing basato su VSchema
- Connection pooling
- Failover automatico

```bash
# Start VTGate
vtgate -topo_implementation etcd2 \
  -etcd_global_server_address localhost:2379 \
  -service_map 'vtgate' \
  -cell my_cell
```

**VTTablet**:
- Sidecar process accanto a MySQL
- Gestisce replica, backup, health
- Register con topology

```bash
# Start VTTablet
vttablet -topo_implementation etcd2 \
  -etcd_global_server_address localhost:2379 \
  -cell my_cell \
  -keyspace mykeyspace \
  -shard 0 \
  -tablet_hostname tablet-0 \
  -init_keyspace mykeyspace \
  -init_shard 0
```

**VSchema**:
- Metadata che definisce sharding
- Analogo a schema SQL + routing info

```json
{
  "sharded": true,
  "vindexes": {
    "hash": {
      "type": "hash"
    }
  },
  "tables": {
    "orders": {
      "column_vindexes": [
        {
          "column": "customer_id",
          "name": "hash"
        }
      ]
    }
  }
}
```

### 5.3 Vitess Sharding

```yaml
# vtorc config per sharding
topo_implementation: etcd2
etcd:
  - file: /tmp/vt_etcd.json

cell: local
keyspaces:
  - name: commerce
    shards:
      - name: "-80"
        dbname: commerce
        tablet:
          type: replica
      - name: "80-"
        dbname: commerce
        tablet:
          type: replica
```

**Key Range Sharding**:
```sql
-- Vitess usa key ranges
-- Shard 0: keyspace_id < 0x80
-- Shard 1: keyspace_id >= 0x80

-- Definire VSchema
vtctlclient ApplyVSchema -vschema='{
  "sharded": true,
  "vindexes": {
    "hash": {"type": "hash"}
  },
  "tables": {
    "orders": {
      "column_vindexes": [{"column": "customer_id", "name": "hash"}]
    }
  }
}' keyspace commerce
```

**Resize Operations**:
```bash
# Split shard
vtctlclient SplitShard -keyspace=commerce -source_shard=0 -destination_shards='0-0x80,0x80-'

# Move shard
vtctlclient MoveTables -keyspace=commerce -source_shard=0 -destination_keyspace=commerce -destination_shard=1
```

### 5.4 Vitess vs Alternatives

| Feature | Vitess | ProxySQL | Application |
|---------|--------|----------|-------------|
| Sharding | Sì | No | Custom |
| Failover | Auto | Sì | Custom |
| Pooling | Sì | Sì | Custom |
| Query rewrite | Sì | Limitato | Custom |
| Complexity | Alta | Media | Bassa |

**Vitess**:
- Pro: Production proven, feature complete
- Contro: Complesso, steep learning curve, resource intensive

**ProxySQL**:
- Pro: Leggero, buono per pooling, routing semplice
- Contro: Non fa sharding reale

**Citus** (PostgreSQL):
- Se puoi usare PostgreSQL, Citus è eccellente

### 5.5 ProxySQL for Sharding-Like

ProxySQL può fare query routing basato su rules:

```ini
# proxysql.cnf
mysql_query_rules:
  - rule_id: 1
    active: 1
    match_pattern: "^SELECT .* FROM orders WHERE customer_id = ([0-9]+)"
    destination_hostgroup: 10
    apply: 1

  - rule_id: 2
    active: 1
    match_pattern: "^SELECT .* FROM orders WHERE customer_id = ([0-9]+)"
    replace_pattern: "SELECT * FROM orders WHERE customer_id = \\1 AND customer_id % 4 = 0"
    apply: 1

  - rule_id: 10
    match_pattern: ".*"
    destination_hostgroup: 20
```

---

## 6. Sharding Patterns

### 6.1 Tenant-Based Sharding (SaaS)

Pattern comune per applicazioni multi-tenant:

```python
def get_tenant_id():
    # From JWT, header, subdomain, etc.
    return current_user.tenant_id

def get_shard(tenant_id, num_shards=16):
    # Consistent hashing o modulo semplice
    return hash(tenant_id) % num_shards
```

**Benefits**:
- Isolation completo tra tenant
- Compliance (data residency per tenant)
- Capacity planning per tenant
- Simple per-tenant queries

**Implementation**:
```python
class TenantRouter:
    def get_connection(self, tenant_id):
        shard = self.get_shard(tenant_id)
        return self.shard_connections[shard]
    
    def execute_tenant_query(self, tenant_id, sql, params=None):
        conn = self.get_connection(tenant_id)
        # Set tenant context
        conn.execute("SET @current_tenant = %s", (tenant_id,))
        return conn.execute(sql, params)
```

### 6.2 Time-Based Sharding

Per timeseries o log data:

```python
def get_shard(timestamp, num_shards=4):
    # Shard basato su anno-mese
    year_month = timestamp.strftime("%Y%m")
    return int(year_month) % num_shards
```

**Retention management**:
```sql
-- Archiviare vecchi shard
ALTER TABLE events ATTACH PARTITION p202301;

-- Per dati molto vecchi
-- Drop intero shard
DROP TABLE events PARTITION p202001;

-- In MariaDB/MySQL
ALTER TABLE events TRUNCATE PARTITION p202001;
```

**Cleanup script**:
```python
def cleanup_old_data(months_to_keep=24):
    current = datetime.now()
    for month in range(months_to_keep, 120):  # 10 anni
        target_date = current - timedelta(days=month*30)
        if should_archive(target_date):
            archive_to_cold_storage(target_date)
            drop_partition(target_date)
```

### 6.3 Sharding with ProxySQL

ProxySQL può fare sharding rule-based:

```ini
# /etc/haproxy/haproxy.cfg - haproxy example

listen mysql_cluster
    bind 10.0.0.100:3306
    mode tcp
    option tcpka
    balance roundrobin
    
    # Health check
    option mysql-check user health_user
    
    server db1 10.0.0.1:3306 check inter 2000 rise 2 fall 3
    server db2 10.0.0.2:3306 check inter 2000 rise 2 fall 3
    server db3 10.0.0.3:3306 check inter 2000 rise 2 fall 3
    server db4 10.0.0.4:3306 check inter 2000 rise 2 fall 3
```

**ProxySQL rules**:
```sql
-- Routing basato su regex
INSERT INTO mysql_query_rules
(rule_id, active, match_pattern, destination_hostgroup, apply)
VALUES
(1, 1, '^SELECT.*FROM orders WHERE customer_id = ([0-9]+)$', 10, 1),
(2, 1, '^SELECT.*FROM orders WHERE region = ', 20, 1),
(3, 1, '^INSERT.*orders', 10, 1);
```

---

## 7. Rebalancing

### 7.1 When to Rebalance

**Trigger per rebalancing**:
- Shard troppo pieno (>80% capacity)
- Un shard diventa hot spot
- Nuovi server aggiunti
- Skew distribution scoperto

### 7.2 Rebalancing Process

**Processo**:
```python
def rebalance_shard(source_shard, target_shard):
    # 1. Stop writes sullo shard source
    disable_writes(source_shard)
    
    # 2. Dump dati per range
    dump_data(source_shard, range_to_move)
    
    # 3. Import nel target
    import_data(target_shard, dump_file)
    
    # 4. Update routing metadata
    update_routing(source_key_range, target_shard)
    
    # 5. Verify data
    verify_consistency(source_shard, target_shard)
    
    # 6. Resume writes (now going to both)
    # Eventually cleanup source
```

**Online rebalancing** (Vitess-style):
- Copy data mentre writes continuano
- Apply changes durante copia
- Cutover atomico
- Più complesso ma zero downtime

### 7.3 Virtual Shards

Per ridurre rebalancing complexity:

```python
# Virtual shards -> physical shards mapping
# 100 virtual shards -> 4 physical shards
# Rebalancing: change mapping, no data movement

VIRTUAL_SHARD_COUNT = 100
PHYSICAL_SHARD_COUNT = 4

def virtual_to_physical(virtual_id):
    return virtual_id % PHYSICAL_SHARD_COUNT
```

---

## 8. Best Practices

### 8.1 Design Guidelines

**Start without sharding**:
- Progettare per database singolo
- Aggiungere sharding solo quando necessario

**Choose shard key wisely**:
- Testare con production-like data
- Considerare growth patterns

**Plan for cross-shard**:
- Sapere quali queries cross-shard
- Design application per minimizzarle

### 8.2 Monitoring

**Metrics da monitorare**:
```python
# Per ogni shard:
- Query latency
- Connection count
- Storage usage
- Replication lag
- CPU/Memory

# Globally:
- Cross-shard query rate
- Shard distribution uniformity
- Hot spot detection
```

---

## 7. Sharding Patterns

### 7.1 Tenant-Based Sharding (SaaS)

Pattern comune per applicazioni multi-tenant:

```python
def get_tenant_id():
    # From JWT, header, subdomain, etc.
    return current_user.tenant_id

def get_shard(tenant_id):
    # Consistent hashing o lookup
    return hash(tenant_id) % num_shards
```

**Benefici**:
- Isolation completo tra tenant
- Compliance (data residency)
- Capacity planning per tenant

### 7.2 Time-Based Sharding

Per timeseries o log data:

```python
def get_shard(timestamp):
    year_month = timestamp.strftime("%Y-%m")
    return int(hash(year_month)) % num_shards
```

**Pattern di retention**:
```sql
-- Archiviare vecchi shard
ALTER TABLE events ATTACH PARTITION p202301;
-- oppure drop completamente
DROP TABLE events PARTITION p202001;
```

### 7.3 Sharding with ProxySQL

**ProxySQL** può fare sharding rule-based:

```ini
# proxysql.cnf
mysql_query_rules:
  - rule_id: 1
    active: 1
    match_pattern: "^SELECT .* FROM orders WHERE user_id"
    destination_hostgroup: 10
    apply: 1
  
  - rule_id: 2
    match_pattern: "^SELECT .* FROM orders WHERE user_id"
    replace_pattern: "SELECT .* FROM orders WHERE user_id = ?"

  - rule_id: 3
    match_pattern: ".*"
    destination_hostgroup: 20
```

### 7.4 Rebalancing

**Quando rebalance**:
- Shard troppo pieno
- Un shard diventa hot spot
- Nuovi server aggiunti

**Processo**:
1. Stop writes sullo shard
2. Dump dati
3. Import nel nuovo shard
4. Update routing metadata
5. Verify
6. Resume writes

**Online rebalancing** (Vitess-style):
- Copy data mentre writes continuano
- Apply changes durante copia
- Cutover atomico

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*