# ClickHouse — Replica e Alta Disponibilità

## ReplicatedMergeTree: Replica a Livello di Motore

A differenza di PostgreSQL, dove la replica è a livello di WAL del server, ClickHouse implementa la replica **a livello di motore di tabella**. Ogni tabella con prefisso `Replicated` (ReplicatedMergeTree, ReplicatedReplacingMergeTree, etc.) gestisce la propria replica indipendentemente.

Il coordinamento avviene tramite **Apache ZooKeeper** (o il sostituto integrato ClickHouse Keeper), che mantiene i metadati di replica e il log delle operazioni.

### Architettura della Replica

```
ZooKeeper / ClickHouse Keeper
    ├── /clickhouse/tables/shard1/events/
    │   ├── replicas/
    │   │   ├── replica1/        ← stato di replica1
    │   │   └── replica2/        ← stato di replica2
    │   ├── log/                 ← log delle operazioni (INSERT, MERGE, ALTER)
    │   ├── blocks/              ← hash dei blocchi per deduplicazione
    │   └── quorum/              ← informazioni quorum per write consistenti
```

### Configurazione ReplicatedMergeTree

```sql
-- Parametri: ZooKeeper path, replica name
-- {layer}, {shard}, {replica} sono macro definite in config.xml
CREATE TABLE events_replicated (
    event_date Date,
    user_id    UInt64,
    event      LowCardinality(String),
    revenue    Decimal(10, 2)
) ENGINE = ReplicatedMergeTree(
    '/clickhouse/tables/{layer}-{shard}/events',  -- path ZK unico per shard
    '{replica}'                                    -- nome replica unico per nodo
)
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id);
```

```xml
<!-- /etc/clickhouse-server/config.d/macros.xml su nodo1/shard1 -->
<clickhouse>
    <macros>
        <layer>prod</layer>
        <shard>01</shard>
        <replica>replica1</replica>
    </macros>
</clickhouse>

<!-- Su nodo2/shard1 -->
<macros>
    <layer>prod</layer>
    <shard>01</shard>
    <replica>replica2</replica>
</macros>
```

### Ciclo di Vita di un INSERT con Replica

1. Client invia INSERT a replica1
2. Replica1 scrive i dati localmente come parte immutabile
3. Replica1 calcola l'hash del blocco e lo registra in ZooKeeper per **deduplicazione**
4. Replica1 aggiunge una entry nel **replication log** in ZooKeeper
5. Replica2 legge il log, scarica la parte da replica1 (via HTTP interserver), la scrive localmente
6. Entrambe le repliche marcano l'operazione come completata in ZooKeeper

**Deduplicazione automatica**: se lo stesso INSERT viene inviato due volte (retry dopo un timeout), ClickHouse rileva l'hash duplicato in ZooKeeper e scarta il secondo insert silenziosamente.

---

## ClickHouse Keeper: ZooKeeper Sostituto Integrato

Da ClickHouse 22.4, è disponibile **ClickHouse Keeper** come alternativa a ZooKeeper — implementazione Raft-based integrata nel processo ClickHouse stesso.

```xml
<!-- /etc/clickhouse-server/config.d/keeper.xml su tutti i nodi keeper -->
<clickhouse>
    <keeper_server>
        <tcp_port>9181</tcp_port>
        <server_id>1</server_id>         <!-- ID univoco per ogni nodo: 1, 2, 3 -->
        <log_storage_path>/var/lib/clickhouse/coordination/log</log_storage_path>
        <snapshot_storage_path>/var/lib/clickhouse/coordination/snapshots</snapshot_storage_path>

        <coordination_settings>
            <operation_timeout_ms>10000</operation_timeout_ms>
            <session_timeout_ms>30000</session_timeout_ms>
            <raft_logs_level>warning</raft_logs_level>
        </coordination_settings>

        <raft_configuration>
            <server>
                <id>1</id>
                <hostname>ch-keeper1</hostname>
                <port>9444</port>
            </server>
            <server>
                <id>2</id>
                <hostname>ch-keeper2</hostname>
                <port>9444</port>
            </server>
            <server>
                <id>3</id>
                <hostname>ch-keeper3</hostname>
                <port>9444</port>
            </server>
        </raft_configuration>
    </keeper_server>
</clickhouse>
```

**Raccomandazione di deployment**: 3 nodi Keeper per quorum (tolleranza a 1 failure), 5 nodi per tolleranza a 2 failure. I nodi Keeper possono collocare con i nodi ClickHouse su hardware shared.

---

## Monitoraggio della Replica

```sql
-- Stato delle repliche
SELECT
    database,
    table,
    engine,
    is_leader,
    is_readonly,
    is_session_expired,
    future_parts,
    parts_to_check,
    queue_size,
    inserts_in_queue,
    merges_in_queue,
    log_pointer,
    log_max_index,
    log_max_index - log_pointer as lag,   -- quanto siamo indietro rispetto al log
    total_replicas,
    active_replicas
FROM system.replicas
WHERE is_readonly = 1 OR queue_size > 100
ORDER BY lag DESC;

-- Dettaglio della coda di replica
SELECT
    type,
    create_time,
    required_quorum,
    source_replica,
    new_part_name,
    is_currently_executing
FROM system.replication_queue
WHERE database = 'analytics' AND table = 'events'
ORDER BY create_time;

-- Health check script
SELECT
    if(max(lag) > 1000, 'CRITICAL', if(max(lag) > 100, 'WARNING', 'OK')) as status,
    max(lag) as max_replica_lag
FROM (
    SELECT log_max_index - log_pointer as lag
    FROM system.replicas
);
```

---

## Gestione dei Failure di Replica

### Replica in Read-Only Mode

Una replica entra in `is_readonly = 1` quando perde la connessione a ZooKeeper. Non accetta più INSERT ma risponde alle query di lettura.

```sql
-- Forzare il ripristino dopo una disconnessione ZK
SYSTEM RESTART REPLICA analytics.events;

-- Risincronizzare una parte mancante da un'altra replica
SYSTEM SYNC REPLICA analytics.events;

-- Recuperare da un errore di checksum su una parte
-- 1. Identificare la parte corrotta
SELECT * FROM system.parts WHERE table = 'events' AND is_frozen = 0 AND active = 0;

-- 2. Detach della parte corrotta
ALTER TABLE analytics.events DETACH PART '20240115_1_1_0';

-- 3. SYNC forzerà il download della parte corretta dall'altra replica
SYSTEM SYNC REPLICA analytics.events;
```

### Ripristino da Zero (New Replica Join)

Quando si aggiunge una nuova replica o si ripristina una replica da zero:

```bash
# Il nodo con dati vuoti su ZooKeeper si auto-sincronizza all'avvio
# Se lo ZNode della replica esiste ma la replica ha dati errati:
clickhouse-client --query "SYSTEM DROP REPLICA 'replica3' FROM TABLE analytics.events"
clickhouse-client --query "DROP TABLE analytics.events"
# Ricrea la tabella con lo stesso schema e ZK path — si sincronizza automaticamente
```

---

## Cluster Distribuito con Replica: Layout Completo

Il layout standard per produzione è **N shard × 2 repliche**:

```
analytics_cluster:
    shard1:
        replica1 → ch-node1:9000 (leader shard1)
        replica2 → ch-node2:9000 (follower shard1)
    shard2:
        replica1 → ch-node3:9000 (leader shard2)
        replica2 → ch-node4:9000 (follower shard2)
```

Con tabella Distributed su `rand()` come sharding key, ogni INSERT viene distribuito casualmente ai shard. Per data locality (es. tutte le righe di un `user_id` sullo stesso shard):

```sql
ENGINE = Distributed('analytics_cluster', 'analytics', 'events_local', intHash64(user_id));
-- user_id mod num_shards → stesso shard per stesso user
```

---

## Backup e Ripristino

```sql
-- BACKUP: snapshots atomici
BACKUP TABLE analytics.events TO Disk('backups', 'events-2024-01-15.zip');
BACKUP TABLE analytics.events TO S3('https://my-bucket/backups/events/', 'key', 'secret');

-- BACKUP DATABASE
BACKUP DATABASE analytics TO S3('https://my-bucket/backups/analytics-full/', 'key', 'secret')
SETTINGS async = true;  -- non-bloccante

-- Monitorare il backup
SELECT * FROM system.backups ORDER BY start_time DESC LIMIT 10;

-- RESTORE
RESTORE TABLE analytics.events FROM Disk('backups', 'events-2024-01-15.zip');
RESTORE DATABASE analytics FROM S3('https://my-bucket/backups/analytics-full/', 'key', 'secret');

-- FREEZE per backup manuale (hardlink su filesystem)
ALTER TABLE events FREEZE;
-- Crea hardlink in /var/lib/clickhouse/shadow/
-- Copiare via rsync/s3 senza impattare il servizio attivo
```

La replica in ClickHouse è robusta ma richiede comprensione del modello per gestire correttamente i failure. Il pattern chiave è: ogni shard ha N repliche gestite da Keeper/ZooKeeper, il layer Distributed è stateless e si occupa solo del routing delle query.
