# Database Replication — Topologie

## Primary-Standby (Single Primary)

La topologia più comune: un primario accetta tutte le write, N standby ricevono la replica.

```
               ┌──────────────┐
               │   Primary    │
               │  (R/W)       │
               └──────┬───────┘
                      │ streaming replication
              ┌───────┴───────┐
              ↓               ↓
    ┌──────────────┐   ┌──────────────┐
    │  Standby 1   │   │  Standby 2   │
    │  (RO)        │   │  (RO)        │
    └──────────────┘   └──────────────┘
```

**Configurazione PostgreSQL completa**:

```bash
# Sul primario: crea utente di replica
psql -U postgres -c "
    CREATE USER replication_user REPLICATION LOGIN PASSWORD 'secure_password';
"

# pg_hba.conf
host replication replication_user 10.0.0.0/24 scram-sha-256

# postgresql.conf
wal_level = replica
max_wal_senders = 10
wal_keep_size = 512MB
hot_standby = on
```

```bash
# Sulla standby: inizializza da backup del primario
pg_basebackup -h primary-host -U replication_user -D /var/lib/postgresql/data \
    -Xs -P --wal-method=stream -R
# -R: crea automaticamente standby.signal + postgresql.auto.conf con primary_conninfo

# postgresql.auto.conf creato da pg_basebackup:
# primary_conninfo = 'host=primary-host port=5432 user=replication_user ...'
# primary_slot_name = 'standby1_slot'
```

---

## Cascading Replication

Le standby possono a loro volta replicare ad altre standby, riducendo il carico sul primario.

```
    Primary ──→ Standby 1 ──→ Standby 2
                           └──→ Standby 3
```

```properties
# postgresql.conf su Standby 1 (che diventa anche "upstream" per standby 2 e 3)
wal_level = replica
max_wal_senders = 5
hot_standby = on

# standby 2 si connette a standby 1 invece che al primario
# primary_conninfo = 'host=standby1 port=5432 user=replication_user'
```

**Vantaggio**: il primario invia i WAL una sola volta, Standby 1 li redistribuisce.
**Svantaggio**: latenza cumulativa (Standby 3 è sempre più in ritardo del Standby 1).

---

## Multi-Primary (Multi-Master)

Più nodi accettano scritture simultaneamente. Richiede conflict resolution.

### Galera Cluster (MySQL/MariaDB)

```
   ┌──────────┐
   │ Primary 1│ ←──→ ┌──────────┐
   │   (R/W)  │      │ Primary 2│
   └──────────┘      │   (R/W)  │
         ↕           └──────────┘
   ┌──────────┐           ↕
   │ Primary 3│ ←──────────
   │   (R/W)  │
   └──────────┘
```

```ini
# my.cnf su ogni nodo
[mysqld]
wsrep_on=ON
wsrep_provider=/usr/lib/galera/libgalera_smm.so
wsrep_cluster_name="galera_cluster"

# Nodo 1
wsrep_cluster_address="gcomm://node1,node2,node3"
wsrep_node_address="node1"
wsrep_sst_method=rsync

# Tutti i nodi: ROW-based required
binlog_format=row
default_storage_engine=InnoDB
innodb_autoinc_lock_mode=2  # galera richiede questo setting
```

**Protocollo Galera (virtually synchronous)**:
1. Write su qualsiasi nodo
2. Certificazione distribuita (ogni nodo verifica che non ci siano conflitti)
3. Se certifica: apply su tutti, commit confermato
4. Se non certifica (conflitto rilevato): abort e retry

**Overhead**: ogni write richiede un round di certificazione su tutti i nodi → latenza ∝ RTT del nodo più lento.

### BDR (Bi-Directional Replication) per PostgreSQL

```sql
-- PostgreSQL BDR (plugin enterprise)
CREATE EXTENSION bdr;

SELECT bdr.create_node(
    node_name := 'node1',
    local_dsn := 'host=node1 dbname=mydb'
);

SELECT bdr.create_group(node_name := 'node1');
SELECT bdr.join_node_group(
    join_target_dsn := 'host=node1 dbname=mydb',
    node_name := 'node2'
);
```

---

## Read Replicas con Connection Pooler

In produzione, le connessioni alle repliche vengono gestite tramite un connection pooler (PgBouncer, ProxySQL) che instrada automaticamente le letture.

### PgBouncer per PostgreSQL

```ini
# pgbouncer.ini
[databases]
mydb_rw = host=primary-host port=5432 dbname=mydb
mydb_ro = host=replica1-host port=5432 dbname=mydb

[pgbouncer]
listen_addr = *
listen_port = 6432
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
server_reset_query = DISCARD ALL
```

### HAProxy per Load Balancing delle Letture

```
# /etc/haproxy/haproxy.cfg
frontend pg_read
    bind *:5433
    mode tcp
    default_backend pg_replicas

backend pg_replicas
    mode tcp
    balance roundrobin
    option tcp-check
    server replica1 10.0.0.11:5432 check inter 5s fall 3 rise 2
    server replica2 10.0.0.12:5432 check inter 5s fall 3 rise 2
    server replica3 10.0.0.13:5432 check inter 5s fall 3 rise 2

frontend pg_write
    bind *:5432
    mode tcp
    default_backend pg_primary

backend pg_primary
    mode tcp
    server primary 10.0.0.10:5432 check inter 5s
```

---

## Replica per Analytics: Read Replica Dedicata

```python
# Pattern: connessione dual per OLTP + Analytics
from sqlalchemy import create_engine

# Engine per scritture e letture transazionali (primary)
primary_engine = create_engine(
    "postgresql://user:pass@primary:5432/db",
    pool_size=10,
    max_overflow=20,
)

# Engine per analytics (replica con hardware potenziato per query pesanti)
analytics_engine = create_engine(
    "postgresql://user:pass@analytics-replica:5432/db",
    pool_size=5,
    max_overflow=10,
    connect_args={"options": "-c statement_timeout=300000"}  # 5 min timeout
)

# ORM con session routing
from sqlalchemy.orm import Session

class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kwargs):
        if self._flushing:
            return primary_engine  # write sempre sul primario
        if hasattr(clause, '_execution_options'):
            if clause._execution_options.get('analytics', False):
                return analytics_engine
        return primary_engine

# Utilizzo
with RoutingSession() as session:
    # Query analitica sulla replica
    result = session.execute(
        text("SELECT date, sum(revenue) FROM orders GROUP BY date"),
        execution_options={"analytics": True}
    )
```

---

## Cross-Region Replication

```
   EU-West (Primary)              US-East (Replica)
   ┌──────────────┐               ┌──────────────┐
   │  Primary     │──── WAL ────→ │  Standby     │
   │              │    ~80ms RTT  │              │
   └──────────────┘               └──────────────┘
                                         ↓
                                  Read-only per utenti US
```

**Sfide della replica cross-region**:
1. **Alta latenza WAL**: 50-200ms RTT. Con sincrona: ogni write aggiunge questa latenza
2. **Bandwidth cost**: il traffico inter-region è costoso
3. **Timezone e compliance**: i dati devono restare nella stessa regione geografica

**Soluzione pratica**: replica asincrona cross-region + routing intelligente delle letture

```python
import geoip2.database

def get_connection(user_ip: str, write: bool = False):
    if write:
        return eu_primary  # sempre sul primario EU

    # Routing geografico per letture
    with geoip2.database.Reader('/GeoLite2-Country.mmdb') as reader:
        response = reader.country(user_ip)
        if response.country.iso_code in ["US", "CA", "MX"]:
            return us_replica
        return eu_primary  # default

```

Le topologie di replica coprono un range ampio di trade-off tra semplicità operativa (single primary) e disponibilità/performance (multi-primary). La scelta dipende da: SLA di uptime richiesto, distribuzione geografica degli utenti, tolleranza alla complessità operativa del multi-master.
