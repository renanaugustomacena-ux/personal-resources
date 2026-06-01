# MariaDB Galera Cluster

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
1. Galera Overview e Concepts
2. Cluster Setup Completo
3. Node Management
4. HA e Failover
5. Load Balancing
6. Monitoring e Troubleshooting
7. Performance Tuning

---

## 1. Galera Overview e Concepts

### 1.1 What is Galera

**Galera Cluster** fornisce synchronous multi-master replication per MariaDB e MySQL. È la soluzione enterprise per alta disponibilità.

**Caratteristiche fondamentali**:
- **Multi-master**: write su qualsiasi nodo
- **Synchronous**: nessun lag di replica
- **Zero slave lag**: transaction garantita su tutti i nodi
- **Automatic failover**: automatico senza intervento
- **Read scalability**: letture da qualsiasi nodo
- **Causal consistency**: garanzia di ordine causale

### 1.2 How It Works

```
[App] → [Write to Node A] → [Certification] → [Apply on all nodes]
                              ↓
                      Global Transaction ID
```

**Certification-based replication**:
1. Transaction viene eseguita localmente sul nodo scrivente
2. Prima del commit, il certifier verifica conflitti potenziali
3. Se pass, transaction viene applicata su tutti i nodi
4. Se fail, transaction viene aborted su tutti i nodi

**Benefici**:
- Nessun dato perso (sync)
- Nessun lag (sync)
- Letture locali veloci (non deve cercare master)

### 1.3 Galera vs Traditional Replication

| Aspetto | Traditional Async | Galera Sync |
|---------|------------------|-------------|
| Data consistency | eventuale | immediata |
| Lag | variabile | zero |
| Writes | solo master | multi-master |
| Failover | manuale/automatico | automatico |
| Complexity | bassa | media |

---

## 2. Cluster Setup Completo

### 2.1 Prerequisites

```bash
# Install MariaDB server + galera
apt install mariadb-server mariadb-client galera-4

# Per Percona XtraDB Cluster
apt install percona-xtradb-cluster

# Verificare componenti
dpkg -l | grep -E 'mysql|galera'
```

### 2.2 Configuration Files

```ini
# /etc/mysql/mariadb.conf.d/galera.cnf

[mysqld]
# Basic
bind-address = 0.0.0.0
port = 3306

# Galera Configuration
wsrep_on = ON
wsrep_provider = /usr/lib/galera/libgalera_smm.so
wsrep_cluster_name = "my_cluster"
wsrep_cluster_address = "gcomm://node1,node2,node3"

# Node specific
wsrep_node_name = "node1"
wsrep_node_address = "192.168.1.1"

# Required settings
binlog_format = ROW
default_storage_engine = InnoDB
innodb_autoinc_lock_mode = 2
innodb_doublewrite = 1

# Performance
innodb_flush_log_at_trx_commit = 1

# Security (optional)
wsrep_provider_options = "socket.ssl_key=/etc/mysql/ssl/server-key.pem;socket.ssl_cert=/etc/mysql/ssl/server-cert.pem;socket.ssl_ca=/etc/mysql/ssl/ca.pem"
```

### 2.3 First Node Bootstrap

```bash
# First node - bootstrap mode
service mysql start --wsrep-new-cluster

# Verificare
mysql -u root -e "SHOW STATUS LIKE 'wsrep_cluster_size'"
# Should return 1
```

### 2.4 Adding Subsequent Nodes

```bash
# Subsequent nodes - normal start
service mysql start
```

### 2.5 Verify Cluster

```sql
-- Status cluster completo
SHOW STATUS LIKE 'wsrep%';

-- Cluster size (should be number of nodes)
SHOW STATUS LIKE 'wsrep_cluster_size';

-- Cluster status (Primary/Non-Primary)
SHOW STATUS LIKE 'wsrep_cluster_status';

-- Node status
SHOW STATUS LIKE 'wsrep_local_state';

-- Connected members
SHOW STATUS LIKE 'wsrep_incoming_addresses';
```

**Node states**:
- `JOINING`: nodo sta joining
- `JOINED`: syncing con cluster
- `SYNCED`: completamente sincronizzato
- `DONOR`: dando stato a nuovo nodo

---

## 3. Node Management

### 3.1 Add Node

```bash
# New node: same config with cluster address
# Just start mysql - joins automatically
service mysql start
```

### 3.2 Remove Node Gracefully

```sql
-- Metodo 1: shutdown sul nodo
systemctl stop mysql
# Rimosso automaticamente dal cluster

-- Metodo 2: leave via SQL
SET GLOBAL wsrep_cluster_address = 'gcomm://node1,node2';
-- Then restart mysql
```

### 3.3 Force Remove Node

```sql
-- Se nodo non raggiungibile
-- Dal nodo primario:
SET GLOBAL wsrep_cluster_view = 'uuid:position,node1,node2';
-- Rimuove node3 dal view
```

### 3.4 Cluster Recovery

```bash
# When majority lost - need to bootstrap
# Choose node with most advanced state

# Stop all nodes
systemctl stop mysql

# Bootstrap from chosen node
service mysql start --wsrep-new-cluster

# Other nodes rejoins
systemctl start mysql
```

---

## 4. HA e Failover

### 4.1 Automatic Failover

Galera handles failover automatically:

```
[Write to Node A]
      ↓
[Node A fails]
      ↓
[App retries to Node B or C]
      ↓
[Node B or C accepts write]
```

**Process**:
- Nodo designato come donore per recovery
- Others continuano a funzionare
- Automatic state transfer

### 4.2 Split Brain Prevention

**Quorum Calculation**:
```
Default: majority = total_nodes / 2 + 1

3 nodes: majority = 2 (survive 1 failure)
5 nodes: majority = 3 (survive 2 failures)
```

**Problem with 2 nodes**:
```
2 nodes: majority = 2 (no majority if 1 fails!)
```

**Solution: Add arbiter (garb)**:
```bash
# Install garb
apt install mariadb-galera-arbiter

# Start arbiter
garbd -a gcomm://node1,node2 \
      -g my_cluster \
      -d /var/log/garb.log \
      --option 'socket.ssl_ca=/etc/ssl/certs/ca-certificates.crt'
```

### 4.3 Automatic Weight

```sql
-- Control node weight
SET GLOBAL wsrep_node_weight = 2;

-- Higher weight = more likely to be primary
-- Useful for ensuring preferred primary
```

---

## 5. Load Balancing

### 5.1 HAProxy Integration

```ini
# /etc/haproxy/haproxy.cfg

frontend mysql-front
    bind 10.0.0.100:3306
    mode tcp
    default_backend mysql-back

backend mysql-back
    mode tcp
    balance roundrobin
    option tcpka
    option mysql-check user haproxy
    
    server node1 10.0.0.1:3306 check inter 2000 rise 2 fall 3
    server node2 10.0.0.2:3306 check inter 2000 rise 2 fall 3
    server node3 10.0.0.3:3306 check inter 2000 rise 2 fall 3
```

**Create health check user**:
```sql
CREATE USER 'haproxy'@'%' IDENTIFIED BY '';
-- Empty password for haproxy check
```

### 5.2 MaxScale (MariaDB)

```ini
# /etc/maxscale.cnf

[server1]
type=server
address=10.0.0.1
port=3306
protocol=MySQLBackend

[server2]
type=server
address=10.0.0.2
port=3306
protocol=MySQLBackend

[Galera-Monitor]
type=monitor
module=galeramon
servers=server1,server2
user=maxscale
passwd=password
monitor_interval=1000

[Read-Write-Service]
type=service
router=readwritesplit
servers=server1,server2

[Read-Write-Listener]
type=listener
service=Read-Write-Service
protocol=MySQLClient
port=3306
```

---

## 6. Monitoring e Troubleshooting

### 6.1 Key Status Variables

```sql
-- Cluster health
SHOW STATUS LIKE 'wsrep_cluster_size';
SHOW STATUS LIKE 'wsrep_cluster_status';
SHOW STATUS LIKE 'wsrep_cluster_conf_id';

-- Node health
SHOW STATUS LIKE 'wsrep_local_state';
SHOW STATUS LIKE 'wsrep_local_state_comment';
SHOW STATUS LIKE 'wsrep_ready';

-- Replication status
SHOW STATUS LIKE 'wsrep_flow_control_paused';
SHOW STATUS LIKE 'wsrep_replicated_bytes';
SHOW STATUS LIKE 'wsrep_received_bytes';

-- Conflicts
SHOW STATUS LIKE 'wsrep_conflict_count';
SHOW STATUS LIKE 'wsrep_local_bf_aborts';
```

### 6.2 Common Issues

**Node not joining**:
```sql
-- Check network
ping node1

-- Check firewall
iptables -L

-- Check credentials
SHOW VARIABLES LIKE 'wsrep_provider_options';
```

**Flow control paused**:
```sql
-- Shows nodes are behind
SHOW STATUS LIKE 'wsrep_flow_control_paused';

-- Increase flow control threshold
SET GLOBAL wsrep_max_ws_rows = 131072;
SET GLOBAL wsrep_max_ws_size = 2G;
```

---

## 7. Performance Tuning

### 7.1 Optimize for Write Throughput

```ini
# /etc/mysql/mariadb.conf.d/galera.cnf

[mysqld]
# Larger writesets
wsrep_max_ws_size = 2G

# Flow control
wsrep_flow_control_mode = DISABLED  # for speed, less safe
wsrep_slave_throttle_ratio = 0

# Parallel apply
wsrep_slave_ threads = 4

# InnoDB
innodb_flush_log_at_trx_commit = 2  # safer with Galera
innodb_log_file_size = 1G
```

### 7.2 Network Optimization

```ini
# Increase network buffer
wsrep_provider_options = "gcache.size=1G;gcache.recover=yes"
```

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*
[Write to Node A] → [Certification] → [Apply all nodes]
                      ↓
              Global Transaction ID
```

**Certification-based replication**:
- Transaction applicata localmente
- Prima del commit, certifier verifica conflitti
- Se pass, transaction applicata su tutti nodi

---

## 2. Cluster Setup

### 2.1 Prerequisites

```bash
# Install MariaDB server + galera
apt install mariadb-server mariadb-client galera-4

# oppure Percona XtraDB Cluster
apt install percona-xtradb-cluster
```

### 2.2 Configuration

```ini
# /etc/mysql/mariadb.conf.d/galera.cnf
[mysqld]
# Cluster
wsrep_on = ON
wsrep_provider = /usr/lib/galera/libgalera_smm.so
wsrep_cluster_name = my_cluster
wsrep_cluster_address = gcomm://node1,node2,node3

# Node specific
wsrep_node_name = node1
wsrep_node_address = 192.168.1.1

# Replication
binlog_format = ROW
default_storage_engine = InnoDB
innodb_autoinc_lock_mode = 2

# Security
wsrep_provider_options = "socket.ssl_key=/etc/mysql/ssl/server-key.pem;socket.ssl_cert=/etc/mysql/ssl/server-cert.pem;socket.ssl_ca=/etc/mysql/ssl/ca.pem"
```

### 2.3 Bootstrap First Node

```bash
# First node - bootstrap
service mysql start --wsrep-new-cluster

# Subsequent nodes
service mysql start
```

### 2.4 Verify Cluster

```sql
-- Status cluster
SHOW STATUS LIKE 'wsrep%';

-- Cluster size
SHOW STATUS LIKE 'wsrep_cluster_size';

-- Connected nodes
SHOW STATUS LIKE 'wsrep_cluster_status';

-- Node status
SHOW STATUS LIKE 'wsrep_local_state';
```

---

## 3. Node Management

### 3.1 Add Node

```bash
# Configure new node with cluster address
# Start MariaDB
service mysql start

# Node joins automatically via gcomm://
```

### 3.2 Remove Node

```sql
-- Graceful remove
SET GLOBAL wsrep_cluster_address = 'gcomm://node1,node2';
-- Restart node
```

### 3.3 Cluster Recovery

```bash
# If majority lost, need to bootstrap
# Choose node with most advanced state
# Stop all nodes
# Bootstrap from that node
service mysql start --wsrep-new-cluster

# Other nodes rejoin
service mysql start
```

---

## 4. HA e Failover

### 4.1 Automatic Failover

Galera handles failover automatically:

```
[Write to Node A]
      ↓
[Node A fails]
      ↓
[App retries to Node B or C]
      ↓
[Node B or C accepts write]
```

### 4.2 Split Brain Prevention

```ini
# Quorum calcolo
# Default: majority = total_nodes / 2 + 1
# 3 nodes: majority = 2
# 4 nodes: majority = 3
```

**With 2 nodes**: Problem! No majority possible.

**Solution**: Add arbiter
```bash
# Install garb (arbiter)
apt install mariadb-galera-arbiter
garbd -a gcomm://node1,node2 -g my_cluster -d /var/log/garb.log
```

---

## 5. Load Balancing

### 5.1 HAProxy Integration

```ini
# /etc/haproxy/haproxy.cfg
listen mariadb
    bind 10.0.0.100:3306
    mode tcp
    option tcpka
    balance roundrobin
    server node1 10.0.0.1:3306 check
    server node2 10.0.0.2:3306 check
    server node3 10.0.0.3:3306 check
```

### 5.2 MaxScale (MariaDB)

```ini
# MariaDB MaxScale
[server1]
address=10.0.0.1
port=3306

[server2]
address=10.0.0.2
port=3306

[Galera-Service]
type=service
router=galeramon
servers=server1,server2
```

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*