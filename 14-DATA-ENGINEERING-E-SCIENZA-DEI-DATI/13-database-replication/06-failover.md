# Failover e Alta Disponibilità nella Replica

Il failover è la procedura con cui un sistema di database passa automaticamente o manualmente da un nodo primario non più disponibile a un nodo secondario (standby/replica), ripristinando la capacità di accettare scritture. La qualità del failover determina l'RTO (Recovery Time Objective) del sistema e l'entità della perdita dati potenziale (RPO). Un failover mal gestito può portare a split-brain (due nodi che si credono entrambi primari), corruzione dei dati, o perdita permanente di transazioni.

## Tipologie di Failover

### Failover Manuale

Il failover manuale richiede intervento umano esplicito. È appropriato quando:
- La causa della failure del primario è ambigua (potrebbe essere un problema di rete temporaneo)
- Non si vuole rischiare un failover per un'interruzione breve
- Il sistema non ha monitoraggio automatico affidabile

```bash
# PostgreSQL: failover manuale con pg_ctl promote
# Sul server standby (futuro primario)
pg_ctl promote -D /var/lib/postgresql/data

# Verifica che lo standby sia diventato primario
psql -c "SELECT pg_is_in_recovery();"
# Deve restituire 'f' (false = non in recovery = è primario)

# Alternativa con touch file (metodo legacy)
touch /tmp/postgresql.trigger.5432
# Il file configurato in recovery.conf come trigger_file
```

```bash
# MySQL: failover manuale con GTID
# 1. Sul vecchio primario (se accessibile) eseguire FLUSH LOGS
mysql -u root -p -e "FLUSH LOGS;"

# 2. Sul replica prescelto, interrompere la replica
mysql -u root -p -e "STOP REPLICA;"

# 3. Verificare che tutti i binlog siano stati applicati
mysql -u root -p -e "SHOW REPLICA STATUS\G" | grep -E "Exec_Master_Log_Pos|Read_Master_Log_Pos"

# 4. Promuovere il replica a primario
mysql -u root -p -e "RESET REPLICA ALL;"

# 5. Aggiornare gli altri replica per puntare al nuovo primario
mysql -u root -p -e "
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='nuovo-primario',
  SOURCE_PORT=3306,
  SOURCE_USER='replicatore',
  SOURCE_PASSWORD='password',
  SOURCE_AUTO_POSITION=1;
START REPLICA;
"
```

### Failover Automatico

Il failover automatico non richiede intervento umano. Un agente esterno monitora costantemente il primario e, al rilevamento di un guasto, orchestra la promozione di uno standby. Il rischio principale è lo **split-brain**: se il primario è temporaneamente irraggiungibile ma ancora operativo, avere due nodi che credono di essere primari simultaneamente porta a divergenza dei dati.

La protezione contro lo split-brain si ottiene con:
1. **Fencing (STONITH - Shoot The Other Node In The Head)**: il vecchio primario viene spento fisicamente o isolato dalla rete prima che il nuovo primario accetti scritture
2. **Quorum**: il failover avviene solo se una maggioranza di nodi ha confermato che il primario è irraggiungibile
3. **Lease-based locking**: il primario mantiene un lease su un sistema esterno (etcd, ZooKeeper); se non rinnova il lease, non può accettare scritture

## Patroni: Alta Disponibilità PostgreSQL

Patroni è il tool di HA più maturo per PostgreSQL. Usa etcd, Consul, o ZooKeeper come DCS (Distributed Configuration Store) per il coordinamento e la protezione contro split-brain.

### Architettura Patroni

```
┌─────────────────────────────────────────────────────────┐
│                    DCS (etcd cluster)                   │
│    /patroni/cluster-name/leader    → node1             │
│    /patroni/cluster-name/members/node1 → {...}         │
│    /patroni/cluster-name/members/node2 → {...}         │
└──────────────────────┬──────────────────────────────────┘
                       │ heartbeat + leader election
           ┌───────────┴───────────┐
           ▼                       ▼
    ┌─────────────┐         ┌─────────────┐
    │   node1     │         │   node2     │
    │  (primary)  │ WAL →   │  (standby)  │
    │  Patroni    │ stream  │  Patroni    │
    │  PostgreSQL │         │  PostgreSQL │
    └─────────────┘         └─────────────┘
           │                       │
           └───────────┬───────────┘
                       ▼
                ┌─────────────┐
                │   HAProxy   │
                │  (router)   │
                │ 5432→primary│
                │ 5433→any    │
                └─────────────┘
```

### Configurazione Patroni

```yaml
# /etc/patroni/patroni.yml - node1
scope: postgres-cluster
namespace: /patroni/
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 192.168.1.10:8008

etcd3:
  hosts: 192.168.1.20:2379,192.168.1.21:2379,192.168.1.22:2379

bootstrap:
  dcs:
    ttl: 30                          # lease TTL in secondi
    loop_wait: 10                    # intervallo heartbeat
    retry_timeout: 10
    maximum_lag_on_failover: 1048576 # 1MB: max lag accettabile per candidatura
    master_start_timeout: 300
    synchronous_mode: false          # true = replica sincrona obbligatoria
    postgresql:
      use_pg_rewind: true
      use_slots: true
      parameters:
        wal_level: replica
        hot_standby: "on"
        max_wal_senders: 10
        max_replication_slots: 10
        wal_log_hints: "on"          # necessario per pg_rewind
        archive_mode: "on"
        archive_command: 'cp %p /wal-archive/%f'

  initdb:
    - encoding: UTF8
    - data-checksums                 # necessario per pg_rewind

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 192.168.1.10:5432
  data_dir: /var/lib/postgresql/data
  bin_dir: /usr/lib/postgresql/15/bin
  pgpass: /tmp/pgpass0

  authentication:
    replication:
      username: replicator
      password: replicator_password
    superuser:
      username: postgres
      password: postgres_password

  parameters:
    unix_socket_directories: '/var/run/postgresql'

tags:
  nofailover: false    # questo nodo può diventare primario
  noloadbalance: false # questo nodo accetta connessioni di lettura
  clonefrom: false
  nosync: false
```

### Operazioni Patroni

```bash
# Stato del cluster
patronictl -c /etc/patroni/patroni.yml list

# Output tipico:
# + Cluster: postgres-cluster (7234567890) +---------+----+-----------+
# | Member | Host           | Role    | State   | TL | Lag in MB |
# +--------+----------------+---------+---------+----+-----------+
# | node1  | 192.168.1.10   | Leader  | running |  1 |           |
# | node2  | 192.168.1.11   | Replica | running |  1 |       0.0 |
# +--------+----------------+---------+---------+----+-----------+

# Failover manuale (switchover pianificato)
patronictl -c /etc/patroni/patroni.yml switchover postgres-cluster \
  --master node1 \
  --candidate node2 \
  --scheduled now

# Failover forzato (quando il primario non risponde)
patronictl -c /etc/patroni/patroni.yml failover postgres-cluster \
  --master node1 \
  --candidate node2 \
  --force

# Reinserire il vecchio primario come standby dopo failover
# Patroni gestisce automaticamente pg_rewind per riconciliare WAL divergenti
# pg_rewind recupera le transazioni non replicate e allinea lo standby

# Controllare la salute tramite API REST
curl http://192.168.1.10:8008/health
# {"state":"running","postmaster_start_time":"...","role":"master",...}

curl http://192.168.1.11:8008/replica
# Restituisce 200 se il nodo è in standby, 503 altrimenti (utile per HAProxy health check)

# Pausa/Resume del cluster (es. durante manutenzione)
patronictl -c /etc/patroni/patroni.yml pause postgres-cluster
patronictl -c /etc/patroni/patroni.yml resume postgres-cluster
```

### HAProxy con Patroni

```
# /etc/haproxy/haproxy.cfg
global
    maxconn 100

defaults
    log global
    mode tcp
    retries 2
    timeout client 30m
    timeout connect 4s
    timeout server 30m
    timeout check 5s

listen stats
    mode http
    bind *:7000
    stats enable
    stats uri /

frontend postgres_primary
    bind *:5432
    default_backend postgres_primary_backend

backend postgres_primary_backend
    option httpchk
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server node1 192.168.1.10:5432 maxconn 100 check port 8008
    server node2 192.168.1.11:5432 maxconn 100 check port 8008

frontend postgres_replica
    bind *:5433
    default_backend postgres_replica_backend

backend postgres_replica_backend
    option httpchk
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    # L'API /replica restituisce 200 solo sui nodi standby
    server node1 192.168.1.10:5432 maxconn 100 check port 8008 check-ssl-crt-inv ssl verify none
    server node2 192.168.1.11:5432 maxconn 100 check port 8008

# Nota: HAProxy usa /health per il primario (200 solo su leader)
# e /replica per le repliche (200 solo su standby)
```

## pg_auto_failover

pg_auto_failover è una soluzione più semplice di Patroni per cluster PostgreSQL a due nodi (primario + un standby). È sviluppata da Citus/Microsoft e non richiede un DCS esterno (etcd/ZooKeeper).

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Monitor    │     │   Primary   │     │  Secondary  │
│  (pg nodo)  │◄────│  (pg nodo)  │────►│  (pg nodo)  │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

Il Monitor è esso stesso un nodo PostgreSQL con l'estensione `pgautofailover`. Tiene traccia dello stato di tutti i nodi e decide quando e come eseguire il failover.

```bash
# Inizializzare il monitor
pg_autoctl create monitor \
  --pgdata /var/lib/postgresql/monitor \
  --pgport 5400 \
  --hostname monitor.example.com \
  --auth trust

# Creare il nodo primario
pg_autoctl create postgres \
  --pgdata /var/lib/postgresql/data \
  --pgport 5432 \
  --hostname node1.example.com \
  --monitor postgresql://autoctl_node@monitor.example.com:5400/pg_auto_failover \
  --auth trust \
  --run

# Creare il nodo secondario
pg_autoctl create postgres \
  --pgdata /var/lib/postgresql/data \
  --pgport 5432 \
  --hostname node2.example.com \
  --monitor postgresql://autoctl_node@monitor.example.com:5400/pg_auto_failover \
  --auth trust \
  --run

# Stato del cluster
pg_autoctl show state \
  --monitor postgresql://autoctl_node@monitor.example.com:5400/pg_auto_failover

# Switchover manuale
pg_autoctl perform switchover \
  --monitor postgresql://autoctl_node@monitor.example.com:5400/pg_auto_failover
```

## MySQL: Orchestrator e MHA

### Orchestrator

Orchestrator è uno strumento di topology discovery, visualization, e automated failover per MySQL/MariaDB. Supporta topologie complesse (multi-livello, multi-master).

```bash
# Installazione e configurazione base
# /etc/orchestrator/orchestrator.conf.json
{
  "MySQLTopologyUser": "orchestrator",
  "MySQLTopologyPassword": "orchestrator_pass",
  "MySQLTopologyCredentialsConfigFile": "",
  "MySQLOrchestratorHost": "orchestrator.example.com",
  "MySQLOrchestratorPort": 3306,
  "MySQLOrchestratorDatabase": "orchestrator",
  "MySQLOrchestratorUser": "orchestrator",
  "MySQLOrchestratorPassword": "orchestrator_pass",

  "DetectClusterAliasQuery": "SELECT IFNULL(MAX(cluster_name), '') AS cluster_alias FROM meta.cluster",
  "DetectInstanceAliasQuery": "SELECT IFNULL(MAX(alias), '') AS alias FROM meta.instance",

  "RecoveryPeriodBlockSeconds": 3600,
  "RecoveryIgnoreHostnameFilters": [],
  "RecoverMasterClusterFilters": ["*"],
  "RecoverIntermediateMasterClusterFilters": [],

  "FailMasterPromotionIfSQLThreadNotUpToDate": true,
  "FailMasterPromotionOnLagMinutes": 0,

  "ApplyMySQLPromotionAfterMasterFailover": true,
  "PreventCrossDataCenterMasterFailover": false,
  "PreventCrossRegionMasterFailover": false,

  "MasterFailoverLostInstancesDowntimeMinutes": 0,

  "OnFailureDetectionProcesses": [
    "echo '(detected) {failureType} on {failureCluster}. Sending notification' >> /tmp/recovery.log"
  ],
  "PreFailoverProcesses": [
    "echo '(pre-failover) {failureType} on {failureCluster}' >> /tmp/recovery.log"
  ],
  "PostFailoverProcesses": [
    "echo '(post-failover) {failureType} on {failureCluster}. New master: {successorHost}' >> /tmp/recovery.log"
  ],
  "PostUnsuccessfulFailoverProcesses": [],
  "PostMasterFailoverProcesses": [
    "/usr/local/bin/update-vip.sh {successorHost} {successorPort}"
  ],
  "PostIntermediateMasterFailoverProcesses": []
}
```

```bash
# Operazioni Orchestrator via API
# Scoprire un cluster
curl "http://orchestrator:3000/api/discover/mysql-primary.example.com/3306"

# Stato topologia
curl "http://orchestrator:3000/api/topology/cluster-name" | jq .

# Failover manuale (graceful master takeover)
curl "http://orchestrator:3000/api/graceful-master-takeover/cluster-name/new-master/3306"

# Failover forzato di emergenza
curl "http://orchestrator:3000/api/force-master-failover/cluster-name"

# Spostare una replica su un nuovo master
curl "http://orchestrator:3000/api/relocate/replica-host/3306/new-master/3306"
```

### ProxySQL per MySQL HA

ProxySQL è un proxy layer 7 per MySQL che gestisce il routing delle query verso il nodo corretto, la connection pooling, e il failover automatico.

```sql
-- Configurazione ProxySQL
-- Aggiungere i server MySQL
INSERT INTO mysql_servers (hostgroup_id, hostname, port, weight) VALUES
  (0, 'mysql-primary.example.com', 3306, 100),    -- hostgroup 0 = scritture
  (1, 'mysql-replica1.example.com', 3306, 100),   -- hostgroup 1 = letture
  (1, 'mysql-replica2.example.com', 3306, 100);

-- Configurare le regole di routing
INSERT INTO mysql_query_rules (rule_id, active, match_pattern, destination_hostgroup, apply) VALUES
  (1, 1, '^SELECT .* FOR UPDATE', 0, 1),  -- SELECT FOR UPDATE → primario
  (2, 1, '^SELECT', 1, 1),                -- SELECT → repliche
  (3, 1, '.*', 0, 1);                     -- tutto il resto → primario

-- Configurare il monitoraggio
UPDATE global_variables SET variable_value='monitor_user' WHERE variable_name='mysql-monitor_username';
UPDATE global_variables SET variable_value='monitor_pass' WHERE variable_name='mysql-monitor_password';
UPDATE global_variables SET variable_value=2000 WHERE variable_name='mysql-monitor_connect_interval';
UPDATE global_variables SET variable_value=2000 WHERE variable_name='mysql-monitor_ping_interval';

-- Applicare la configurazione
LOAD MYSQL SERVERS TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
LOAD MYSQL QUERY RULES TO RUNTIME;
SAVE MYSQL QUERY RULES TO DISK;
LOAD MYSQL VARIABLES TO RUNTIME;
SAVE MYSQL VARIABLES TO DISK;
```

```sql
-- ProxySQL con Orchestrator: script per aggiornare hostgroup dopo failover
-- Lo script viene chiamato da Orchestrator nei PostMasterFailoverProcesses

-- /usr/local/bin/update-proxysql.sh
#!/bin/bash
NEW_MASTER_HOST=$1
NEW_MASTER_PORT=$2

mysql -h proxysql -P 6032 -u admin -padmin <<EOF
-- Spostare il nuovo master in hostgroup 0 (scritture)
UPDATE mysql_servers SET hostgroup_id=0
WHERE hostname='${NEW_MASTER_HOST}' AND port=${NEW_MASTER_PORT};

-- Assicurarsi che sia anche in hostgroup 1 (letture)
INSERT IGNORE INTO mysql_servers (hostgroup_id, hostname, port)
VALUES (1, '${NEW_MASTER_HOST}', ${NEW_MASTER_PORT});

LOAD MYSQL SERVERS TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
EOF
```

## Gestione del Connection Draining

Durante un failover, le connessioni attive al vecchio primario devono essere gestite con attenzione. Il connection draining garantisce che le transazioni in corso vengano completate (o terminate con grazia) prima del failover.

```python
# Python: gestione del failover lato applicazione con retry
import psycopg2
import time
import logging
from psycopg2.extras import RealDictCursor
from typing import Optional

logger = logging.getLogger(__name__)

class FailoverAwareConnection:
    """
    Connection manager che gestisce i failover trasparentemente.
    Usa un DSN con multiple host per PostgreSQL streaming replication.
    """
    
    def __init__(self, primary_dsn: str, replica_dsn: Optional[str] = None):
        # PostgreSQL supporta multi-host DSN nativamente:
        # host=node1,node2 target_session_attrs=read-write
        self.primary_dsn = primary_dsn
        self.replica_dsn = replica_dsn or primary_dsn
        self._conn: Optional[psycopg2.extensions.connection] = None
    
    def _connect(self, dsn: str, max_retries: int = 5) -> psycopg2.extensions.connection:
        """Tenta la connessione con exponential backoff."""
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(dsn, connect_timeout=5)
                conn.autocommit = False
                return conn
            except psycopg2.OperationalError as e:
                wait_time = 2 ** attempt  # 1, 2, 4, 8, 16 secondi
                logger.warning(
                    f"Connessione fallita (tentativo {attempt + 1}/{max_retries}): {e}. "
                    f"Riprovo tra {wait_time}s"
                )
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
        raise ConnectionError(f"Impossibile connettersi dopo {max_retries} tentativi")
    
    def execute_with_failover(self, query: str, params=None, max_retries: int = 3):
        """Esegue una query con gestione automatica del failover."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if self._conn is None or self._conn.closed:
                    self._conn = self._connect(self.primary_dsn)
                
                with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    self._conn.commit()
                    return cur.fetchall() if cur.description else None
                    
            except psycopg2.OperationalError as e:
                # Errore di connessione: probabile failover in corso
                logger.error(f"Errore operazionale (tentativo {attempt + 1}): {e}")
                last_error = e
                
                if self._conn and not self._conn.closed:
                    try:
                        self._conn.close()
                    except Exception:
                        pass
                self._conn = None
                
                # Attesa prima di riconnettersi (il failover richiede tempo)
                time.sleep(5 * (attempt + 1))
                
            except psycopg2.extensions.TransactionRollbackError as e:
                # Conflitto di serializzazione: rollback e retry
                logger.warning(f"Conflitto transazione: {e}")
                if self._conn and not self._conn.closed:
                    self._conn.rollback()
                last_error = e
                time.sleep(0.1 * (2 ** attempt))
        
        raise last_error

# Uso con DSN multi-host PostgreSQL (nativo dal driver)
# PostgreSQL selezionerà automaticamente il nodo con target_session_attrs=read-write
conn_manager = FailoverAwareConnection(
    primary_dsn=(
        "host=node1.example.com,node2.example.com "
        "port=5432 "
        "dbname=mydb "
        "user=myapp "
        "password=secret "
        "target_session_attrs=read-write "  # solo nodi che accettano scritture
        "connect_timeout=5"
    )
)
```

## Simulare e Testare il Failover

Il failover non va mai testato per la prima volta in produzione. Un runbook di test deve coprire:

```bash
#!/bin/bash
# test-failover.sh: script di test failover per PostgreSQL + Patroni

CLUSTER_NAME="postgres-cluster"
PATRONI_CONFIG="/etc/patroni/patroni.yml"
APP_DSN="host=haproxy port=5432 dbname=mydb user=myapp password=secret"

echo "=== Test Failover Patroni ==="
echo "Data: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# 1. Stato iniziale
echo "--- Stato iniziale ---"
patronictl -c $PATRONI_CONFIG list

PRIMARY=$(patronictl -c $PATRONI_CONFIG list -f json | \
  python3 -c "import sys,json; nodes=json.load(sys.stdin); \
  print(next(n['Member'] for n in nodes if n['Role']=='Leader'))")
echo "Primario attuale: $PRIMARY"

# 2. Misurare il tempo di scrittura prima del failover
echo "--- Scrittura di test pre-failover ---"
START_TIME=$(date +%s%N)
psql "$APP_DSN" -c "INSERT INTO failover_test (ts) VALUES (NOW());" 2>&1
END_TIME=$(date +%s%N)
PRE_LATENCY=$(( (END_TIME - START_TIME) / 1000000 ))
echo "Latenza pre-failover: ${PRE_LATENCY}ms"

# 3. Eseguire lo switchover
echo "--- Esecuzione switchover ---"
SWITCHOVER_START=$(date +%s%N)
patronictl -c $PATRONI_CONFIG switchover $CLUSTER_NAME \
  --master $PRIMARY \
  --scheduled now \
  --force

# 4. Attendere il completamento del failover
echo "--- Attesa completamento failover ---"
MAX_WAIT=60
WAITED=0
while true; do
    NEW_PRIMARY=$(patronictl -c $PATRONI_CONFIG list -f json 2>/dev/null | \
      python3 -c "import sys,json; nodes=json.load(sys.stdin); \
      leaders=[n for n in nodes if n['Role']=='Leader']; \
      print(leaders[0]['Member'] if leaders else '')" 2>/dev/null)
    
    if [ -n "$NEW_PRIMARY" ] && [ "$NEW_PRIMARY" != "$PRIMARY" ]; then
        SWITCHOVER_END=$(date +%s%N)
        FAILOVER_TIME=$(( (SWITCHOVER_END - SWITCHOVER_START) / 1000000 ))
        echo "Failover completato in ${FAILOVER_TIME}ms"
        echo "Nuovo primario: $NEW_PRIMARY"
        break
    fi
    
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "ERRORE: Failover non completato entro ${MAX_WAIT}s"
        exit 1
    fi
    
    sleep 1
    WAITED=$((WAITED + 1))
done

# 5. Test scrittura post-failover
echo "--- Scrittura di test post-failover ---"
START_TIME=$(date +%s%N)
psql "$APP_DSN" -c "INSERT INTO failover_test (ts) VALUES (NOW());" 2>&1
END_TIME=$(date +%s%N)
POST_LATENCY=$(( (END_TIME - START_TIME) / 1000000 ))
echo "Latenza post-failover: ${POST_LATENCY}ms"

# 6. Stato finale
echo "--- Stato finale ---"
patronictl -c $PATRONI_CONFIG list

# 7. Verifica integrità dati
echo "--- Verifica integrità ---"
ROWS=$(psql "$APP_DSN" -t -c "SELECT COUNT(*) FROM failover_test;")
echo "Righe in failover_test: $ROWS"

echo "=== Test completato ==="
```

## Metriche di Failover

| Metrica | Descrizione | Target tipico |
|---------|-------------|---------------|
| RTO (Recovery Time Objective) | Tempo da guasto a ripresa servizio | < 30s (Patroni) |
| RPO (Recovery Point Objective) | Perdita dati massima accettabile | 0 (sincrono) / < 1s (asincrono) |
| MTTR (Mean Time To Recovery) | Tempo medio di ripristino | < 5 minuti |
| MTBF (Mean Time Between Failures) | Tempo medio tra guasti | Mesi/anni |
| Failover detection time | Tempo da guasto a rilevamento | 10-30s |
| Failover promotion time | Tempo da rilevamento a promozione | 5-15s |

Patroni in configurazione standard (TTL=30s, loop_wait=10s) raggiunge RTO di circa 20-40 secondi. Con TTL più bassi (es. 10s) si riduce il RTO ma aumenta il rischio di failover per problemi transitori.

