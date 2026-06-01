# Strumenti per la Replica e l'Alta Disponibilità

L'ecosistema degli strumenti per la replica e l'HA dei database è vasto. Questa sezione cataloga i principali tool per PostgreSQL e MySQL, con configurazioni pratiche e casi d'uso specifici.

## PostgreSQL: Strumenti HA

### Patroni

Patroni è lo standard de facto per l'HA di PostgreSQL in ambienti Kubernetes e bare-metal. Il suo punto di forza è l'integrazione con i DCS (Distributed Configuration Store) esistenti, che evita l'introduzione di ulteriori componenti infrastrutturali quando etcd o Consul sono già presenti.

```bash
# Installazione
pip install patroni[etcd3]

# Struttura dei file di configurazione
/etc/patroni/
├── patroni.yml         # configurazione principale
└── patroni.env         # variabili d'ambiente (credenziali)

# Avvio come servizio systemd
# /etc/systemd/system/patroni.service
[Unit]
Description=Patroni High Availability PostgreSQL
After=network.target

[Service]
Type=simple
EnvironmentFile=/etc/patroni/patroni.env
ExecStart=/usr/local/bin/patroni /etc/patroni/patroni.yml
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
User=postgres
Group=postgres
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# Comandi operativi frequenti
patronictl -c /etc/patroni/patroni.yml list              # stato cluster
patronictl -c /etc/patroni/patroni.yml history           # storia dei failover
patronictl -c /etc/patroni/patroni.yml switchover        # switchover pianificato
patronictl -c /etc/patroni/patroni.yml failover          # failover forzato
patronictl -c /etc/patroni/patroni.yml reinit node2      # re-inizializzare un nodo
patronictl -c /etc/patroni/patroni.yml edit-config       # modificare la configurazione DCS
patronictl -c /etc/patroni/patroni.yml pause             # pausare il cluster (manutenzione)
patronictl -c /etc/patroni/patroni.yml resume            # riprendere il cluster
```

```yaml
# Configurazione Patroni avanzata con etcd3 TLS e Consul fallback
scope: production-pg
name: node1

etcd3:
  hosts: etcd1:2379,etcd2:2379,etcd3:2379
  protocol: https
  cacert: /etc/ssl/certs/etcd-ca.crt
  cert: /etc/ssl/certs/etcd-client.crt
  key: /etc/ssl/private/etcd-client.key

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576    # 1MB
    master_start_timeout: 300
    synchronous_mode: true              # replica sincrona richiesta
    synchronous_mode_strict: false      # degradare ad asincrono se necessario
    postgresql:
      use_pg_rewind: true
      use_slots: true
      parameters:
        wal_level: logical              # logical permette anche logical replication
        hot_standby: "on"
        max_wal_senders: 10
        max_replication_slots: 10
        wal_log_hints: "on"
        track_commit_timestamp: "on"   # necessario per alcuni conflict resolver
        archive_mode: "on"
        archive_command: 'pgbackrest --stanza=main archive-push %p'
        archive_timeout: 60
      pg_hba:
        - host replication replicator 192.168.0.0/24 md5
        - host all all 0.0.0.0/0 md5

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 192.168.1.10:5432
  data_dir: /var/lib/postgresql/15/data
  bin_dir: /usr/lib/postgresql/15/bin
  pgpass: /var/lib/postgresql/.pgpass

  parameters:
    shared_buffers: 8GB
    effective_cache_size: 24GB
    work_mem: 64MB
    maintenance_work_mem: 2GB
    max_connections: 200
    random_page_cost: 1.1              # SSD

  callbacks:
    on_start: /etc/patroni/callbacks/on_start.sh
    on_stop: /etc/patroni/callbacks/on_stop.sh
    on_restart: /etc/patroni/callbacks/on_restart.sh
    on_role_change: /etc/patroni/callbacks/on_role_change.sh
    # on_role_change è il callback più importante:
    # viene chiamato con "master" o "replica" come argomento
    # Usato per aggiornare DNS, VIP, o notifiche

watchdog:
  mode: required     # il watchdog è obbligatorio (maggiore sicurezza)
  device: /dev/watchdog
  safety_margin: 5
```

### Repmgr

Repmgr (Replication Manager) è una soluzione più semplice di Patroni. Non richiede un DCS esterno: utilizza una tabella nel database stesso per tracciare la topologia. È adatto per cluster semplici (2-3 nodi) dove la semplicità è prioritaria rispetto alle feature avanzate.

```bash
# Installazione
apt-get install postgresql-15-repmgr

# /etc/repmgr/15/repmgr.conf - nodo primario
node_id=1
node_name='node1'
conninfo='host=node1.example.com user=repmgr dbname=repmgr connect_timeout=2'
data_directory='/var/lib/postgresql/15/main'

# Configurazione failover automatico (repmgrd)
failover='automatic'
promote_command='/usr/bin/repmgr standby promote -f /etc/repmgr/15/repmgr.conf --log-to-file'
follow_command='/usr/bin/repmgr standby follow -f /etc/repmgr/15/repmgr.conf --log-to-file --upstream-node-id=%n'

reconnect_attempts=6
reconnect_interval=10
primary_visibility_consensus=true   # protegge dallo split-brain usando la visibilità dei nodi
failover_validation_command='/etc/repmgr/15/failover-validation.sh %n %a'
```

```bash
# Operazioni repmgr

# Registrare il nodo primario
repmgr -f /etc/repmgr/15/repmgr.conf primary register

# Clonare e registrare uno standby
repmgr -h node1.example.com -U repmgr -d repmgr \
  -f /etc/repmgr/15/repmgr.conf standby clone
repmgr -f /etc/repmgr/15/repmgr.conf standby register

# Visualizzare la topologia del cluster
repmgr -f /etc/repmgr/15/repmgr.conf cluster show
# ID | Name  | Role    | Status    | Upstream | Location | Priority | TL | Connection string
# 1  | node1 | primary | * running |          | default  | 100      | 1  | host=node1...
# 2  | node2 | standby |   running | node1    | default  | 100      | 1  | host=node2...

# Switchover (graceful)
repmgr -f /etc/repmgr/15/repmgr.conf standby switchover

# Avviare il demone di monitoraggio per failover automatico
repmgrd -f /etc/repmgr/15/repmgr.conf -d --no-pid-file
```

### PgBouncer

PgBouncer è un connection pooler leggero per PostgreSQL. Riduce il costo di apertura di nuove connessioni (specialmente utile con applicazioni che aprono molte connessioni brevi) e mantiene un pool di connessioni persistenti verso PostgreSQL.

```ini
# /etc/pgbouncer/pgbouncer.ini

[databases]
# Tutte le connessioni al database "myapp" vengono poolate
myapp = host=127.0.0.1 port=5432 dbname=myapp pool_size=20

# Wildcard: qualsiasi database su questo host
* = host=primary.example.com port=5432

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool mode:
# session: una connessione poolata per tutta la durata della sessione
# transaction: una connessione poolata per transazione (più efficiente, ma incompatibile con prepared statements e LISTEN/NOTIFY)
# statement: una connessione per statement (raramente usato)
pool_mode = transaction

# Configurazione del pool
max_client_conn = 1000     # massimo connessioni client
default_pool_size = 20     # connessioni verso PostgreSQL per database/utente
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3

# Timeouts
server_lifetime = 3600
server_idle_timeout = 600
client_idle_timeout = 0
client_login_timeout = 60

# Logging
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid
admin_users = pgbouncer_admin

# Con Patroni: routing automatico
# HAProxy gestisce il failover; PgBouncer pooling delle connessioni
# Topologia: App → PgBouncer → HAProxy → PostgreSQL (primary/replicas)
```

```bash
# Gestione PgBouncer via console admin
psql -p 6432 -U pgbouncer_admin pgbouncer

-- Statistiche per database
SHOW DATABASES;
-- database | host | port | pool_size | reserve_pool | pool_mode | cl_active | cl_waiting

-- Statistiche per pool
SHOW POOLS;

-- Statistiche globali
SHOW STATS;

-- Clients e server connessi
SHOW CLIENTS;
SHOW SERVERS;

-- Pause (per manutenzione)
PAUSE myapp;     -- aspetta il completamento delle transazioni in corso
RESUME myapp;

-- Kill connessioni
KILL myapp;      -- termina immediatamente tutte le connessioni

-- Ricaricare la configurazione
RELOAD;
```

## MySQL: Strumenti HA

### ProxySQL (dettaglio avanzato)

ProxySQL offre funzionalità avanzate oltre al semplice routing: query caching, query mirroring (per testing), multiplexing delle connessioni, e circuit breaker.

```sql
-- Configurazione avanzata ProxySQL

-- Definire gli hostgroup con pesi diversi per load balancing
INSERT INTO mysql_servers (hostgroup_id, hostname, port, weight, max_connections, comment) VALUES
  (0, 'mysql-primary.example.com', 3306, 1, 200, 'Primary - writes'),
  (1, 'mysql-replica1.example.com', 3306, 100, 500, 'Replica 1 - reads'),
  (1, 'mysql-replica2.example.com', 3306, 50, 500, 'Replica 2 - reads (fallback)');

-- Configurare i gruppi di replica (per MySQL Group Replication o InnoDB Cluster)
INSERT INTO mysql_group_replication_hostgroups (
  writer_hostgroup,
  backup_writer_hostgroup,
  reader_hostgroup,
  offline_hostgroup,
  active,
  max_writers,
  writer_is_also_reader,
  max_transactions_behind
) VALUES (0, 2, 1, 9, 1, 1, 0, 100);

-- Query caching
INSERT INTO mysql_query_rules (rule_id, active, match_pattern, cache_ttl, apply) VALUES
  (10, 1, '^SELECT .* FROM products WHERE', 60000, 1);  -- cache 60s

-- Query mirroring (esegui query su un secondo cluster silenziosamente)
INSERT INTO mysql_query_rules (rule_id, active, match_pattern, mirror_hostgroup, apply) VALUES
  (20, 1, '^SELECT', 10, 0);  -- mirror in hostgroup 10 (staging)

-- Circuit breaker: blocca query se il lag replica è troppo alto
UPDATE mysql_servers SET max_replication_lag=30
WHERE hostgroup_id=1;  -- blocca la replica se lag > 30s

-- Applicare e salvare
LOAD MYSQL SERVERS TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
LOAD MYSQL QUERY RULES TO RUNTIME;
SAVE MYSQL QUERY RULES TO DISK;
```

### Orchestrator (configurazione completa)

```bash
# Orchestrator supporta diverse topologie MySQL

# MySQL GTID-based replication
# In my.cnf su tutti i nodi:
[mysqld]
server-id = 1            # unico per ogni nodo
log_bin = /var/lib/mysql/mysql-bin
binlog_format = ROW
gtid_mode = ON
enforce_gtid_consistency = ON
log_replica_updates = ON  # necessario per cascading replication

# Orchestrator con Raft (HA per Orchestrator stesso)
# orchestrator.conf.json
{
  "RaftEnabled": true,
  "RaftDataDir": "/var/lib/orchestrator",
  "RaftBind": "192.168.1.30",
  "RaftNodes": ["192.168.1.30", "192.168.1.31", "192.168.1.32"],
  
  "BackendDB": "mysql",
  "MySQLOrchestratorHost": "127.0.0.1",
  "MySQLOrchestratorPort": 3306,
  "MySQLOrchestratorDatabase": "orchestrator",
  
  "ReasonableReplicationLagSeconds": 10,
  "AuditLogFile": "/var/log/orchestrator/audit.log",
  
  "RecoveryPeriodBlockSeconds": 3600,
  
  "PreGracefulTakeoverProcesses": [
    "echo 'Pre-graceful takeover on {failureCluster}' >> /tmp/orchestrator.log"
  ],
  "PostMasterFailoverProcesses": [
    "/usr/local/bin/update-dns.sh {successorHost}",
    "/usr/local/bin/notify-pagerduty.sh {failureCluster} {successorHost}"
  ]
}
```

### Vitess: Sharding MySQL

Vitess è un sistema di sharding e HA per MySQL sviluppato da YouTube/Google. È lo strato di routing che permette a MySQL di scalare orizzontalmente.

```yaml
# vitess/vttablet-config.yaml
# VTTablet: agente che gira su ogni nodo MySQL
db_host: localhost
db_port: 3306
db_app_user: vt_app
db_app_password: password
db_allprivs_user: vt_allprivs
db_dba_user: vt_dba
db_repl_user: vt_repl
db_filtered_user: vt_filtered

# Topologia degli shard
keyspace: commerce
shard: -80          # questo tablet gestisce le chiavi 0x00-0x80
tablet_type: replica  # primary, replica, rdonly

# Vtgate: router che riceve le query e le indirizza agli shard corretti
vtgate_config:
  cell: us-east
  cells_to_watch: us-east,us-west
  tablet_types_to_wait: PRIMARY,REPLICA
  
# Schema vindex (sharding key)
vschema:
  commerce:
    sharded: true
    vindexes:
      hash:
        type: hash
    tables:
      orders:
        column_vindexes:
          - column: customer_id
            name: hash         # distribuire le righe per hash di customer_id
      customers:
        column_vindexes:
          - column: id
            name: hash
```

## Strumenti di Monitoraggio della Replica

### check_postgres

```bash
# Script Nagios/Icinga per monitoraggio replica PostgreSQL
check_postgres.pl --action=hot_standby_delay \
  --host=replica.example.com \
  --port=5432 \
  --warning=30 \    # warning se lag > 30 secondi
  --critical=120 \  # critical se lag > 120 secondi
  --datadir=/var/lib/postgresql/data

# Monitorare la presenza di slot che trattengono WAL
check_postgres.pl --action=replication_slots \
  --host=primary.example.com \
  --warning=500MB \
  --critical=2GB
```

### pt-heartbeat (MySQL replication lag)

```bash
# Percona Toolkit: heartbeat per misurare il lag di replica in modo accurato
# (superiore a SHOW REPLICA STATUS che può essere impreciso)

# Sul primario: inserire record heartbeat ogni secondo
pt-heartbeat \
  --host=mysql-primary.example.com \
  --user=pt_heartbeat \
  --password=password \
  --database=pt_heartbeat_db \
  --update \
  --interval=1 \
  --daemonize \
  --pid=/var/run/pt-heartbeat.pid

# Sulla replica: misurare il lag
pt-heartbeat \
  --host=mysql-replica.example.com \
  --user=pt_heartbeat \
  --password=password \
  --database=pt_heartbeat_db \
  --monitor \
  --master-server-id=1

# Output:
# 0.00s [  0.00s,  0.00s,  0.00s ]   (ultimo, media 1m, 5m, 15m)
```

### pg_activity

```bash
# Monitor interattivo per PostgreSQL (simile a top)
pg_activity -h localhost -p 5432 -U postgres

# Mostra: connessioni attive, query in esecuzione, lock wait, replication lag
# Utile durante manutenzione e debugging

# Installazione
pip install pg_activity
```

## Tabella Comparativa Strumenti PostgreSQL HA

| Strumento | Tipo | DCS richiesto | Complessità | Feature principali |
|-----------|------|---------------|-------------|---------------------|
| Patroni | HA/Failover | Sì (etcd/Consul/ZK) | Alta | Auto-failover, pg_rewind, watchdog, Kubernetes |
| Repmgr | HA/Failover | No | Media | Auto-failover, clone standby, monitoring |
| pg_auto_failover | HA/Failover | No (built-in) | Bassa | 2-nodi, semplice, Microsoft-supported |
| Stolon | HA/Failover | Sì (etcd/Consul) | Alta | Cloud-native, Kubernetes-first |
| PgBouncer | Connection Pooling | No | Bassa | Session/transaction/statement mode |
| Pgpool-II | Pooling + HA | No | Alta | Load balancing, query cache, watchdog |
| HAProxy | Load Balancer | No | Bassa | TCP routing, health check |

## Tabella Comparativa Strumenti MySQL HA

| Strumento | Tipo | Feature principali |
|-----------|------|--------------------|
| Orchestrator | Topology + HA | Discovery, auto-failover, GTID, multi-topology |
| ProxySQL | Proxy + HA | Query routing, caching, multiplexing, circuit breaker |
| MySQL Router | Proxy | Semplice, integrato con InnoDB Cluster |
| MHA | HA | Semplice failover, deprecating in favore di Orchestrator |
| Vitess | Sharding + HA | YouTube-scale, Kubernetes-native |
| MaxScale | Proxy + HA | Enterprise (MariaDB), strong filtering |

