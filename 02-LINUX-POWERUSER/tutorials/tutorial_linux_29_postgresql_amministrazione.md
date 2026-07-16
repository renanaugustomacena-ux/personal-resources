# Tutorial Linux 29 — PostgreSQL Amministrazione Avanzata

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** streaming replication, Patroni HA, pgBouncer, EXPLAIN ANALYZE, partitioning, pg_stat_statements
> **Prerequisiti:** `tutorial_linux_18_database.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
PostgreSQL Avanzato
│
├── Alta disponibilità
│   ├── Streaming Replication (primary → standby)
│   ├── Patroni (orchestrazione HA automatica)
│   └── pgBouncer (connection pooling)
│
├── Performance
│   ├── EXPLAIN ANALYZE
│   ├── pg_stat_statements
│   ├── Indici (B-Tree, GIN, BRIN, GiST)
│   └── Partitioning (range, list, hash)
│
├── Manutenzione
│   ├── VACUUM / AUTOVACUUM
│   ├── REINDEX
│   └── pg_dump / pg_restore
│
└── Monitoring
    ├── pg_stat_activity
    ├── pg_blocking_pids
    └── Prometheus postgres_exporter
```

---

# Parte A — Streaming Replication

---

## A1. Configurazione primary

```bash
# Su primary: postgresql.conf
cat >> /etc/postgresql/16/main/postgresql.conf << 'EOF'
# Replication
wal_level = replica
max_wal_senders = 5
wal_keep_size = 1GB
hot_standby = on

# Performance
synchronous_commit = local   # async per replica, sync per local
EOF

# pg_hba.conf — permetti replica
echo "host replication replicatore 10.0.0.11/32 scram-sha-256" \
    >> /etc/postgresql/16/main/pg_hba.conf

# Crea utente replica
psql -U postgres -c "CREATE USER replicatore REPLICATION LOGIN PASSWORD 'pass_sicura';"

systemctl reload postgresql
```

---

## A2. Configurazione standby

```bash
# Su standby: fai base backup da primary
pg_basebackup -h 10.0.0.10 -U replicatore \
    -D /var/lib/postgresql/16/main \
    -P -Xs -R
# -P: progress, -Xs: wal streaming, -R: crea standby.signal + postgresql.auto.conf

# postgresql.conf (standby)
cat >> /var/lib/postgresql/16/main/postgresql.auto.conf << 'EOF'
primary_conninfo = 'host=10.0.0.10 port=5432 user=replicatore password=pass_sicura'
primary_slot_name = 'standby1'
EOF

# Avvia standby
systemctl start postgresql

# Su primary: crea replication slot
psql -U postgres -c "SELECT pg_create_physical_replication_slot('standby1');"

# Verifica replica
psql -U postgres -c "SELECT * FROM pg_stat_replication;"
# sent_lsn e replay_lsn devono essere vicini
```

> **Analogia:** Lo streaming replication è come una fotocopiatrice in tempo reale. Il primary scrive ogni modifica nel WAL (Write-Ahead Log), e la standby riceve quel WAL istante per istante — come se avesse una linea telefonica aperta con il primary e copiasse ogni azione. Se il primary cade, il WAL è già lì, e la standby può prendere il controllo in secondi.

---

## A3. Failover manuale e Patroni

```bash
# Failover manuale (standby → primary)
pg_ctl promote -D /var/lib/postgresql/16/main

# Patroni: HA automatica con ETCD
# docker-compose.patroni.yml
cat > docker-compose.patroni.yml << 'EOF'
version: '3.8'
services:
  etcd:
    image: quay.io/coreos/etcd:v3.5
    command:
      - etcd
      - --name=etcd0
      - --initial-cluster=etcd0=http://etcd:2380
      - --listen-client-urls=http://0.0.0.0:2379
      - --advertise-client-urls=http://etcd:2379
    networks: [patroni]

  pg1:
    image: patroni:3.3
    environment:
      PATRONI_NAME: pg1
      PATRONI_POSTGRESQL_DATA_DIR: /data
      PATRONI_ETCD_HOSTS: etcd:2379
      PATRONI_REPLICATION_USERNAME: replicatore
      PATRONI_REPLICATION_PASSWORD: pass_sicura
      PATRONI_SUPERUSER_USERNAME: postgres
      PATRONI_SUPERUSER_PASSWORD: admin_pass
    networks: [patroni]

networks:
  patroni:
EOF

# Comandi Patroni
patronictl -c /etc/patroni.yml list          # stato cluster
patronictl -c /etc/patroni.yml failover      # failover manuale
patronictl -c /etc/patroni.yml switchover    # switchover pianificato
patronictl -c /etc/patroni.yml show-config   # configurazione
```

---

# Parte B — pgBouncer e Performance

---

## B1. pgBouncer connection pooling

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
appdb = host=localhost port=5432 dbname=appdb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 5432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Pool mode
pool_mode = transaction    # migliore per web app (connection per transaction)
# pool_mode = session       # connection per session (default)
# pool_mode = statement     # connection per statement (limitato)

max_client_conn = 1000     # connessioni totali client
default_pool_size = 25     # connessioni verso PostgreSQL per database
min_pool_size = 5
reserve_pool_size = 5

# Log
log_connections = 0
log_disconnections = 0
stats_period = 60
```

```bash
# Crea userlist
psql -U postgres -c "SELECT rolname, rolpassword FROM pg_authid WHERE rolcanlogin;" \
    | grep -v "^-" > /etc/pgbouncer/userlist_raw.txt

# Formato: "username" "md5hash_o_scram"
# Esempio:
echo '"appuser" "SCRAM-SHA-256$4096:..."' > /etc/pgbouncer/userlist.txt

systemctl enable --now pgbouncer

# Monitoring pgBouncer
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer
# Poi nel prompt:
# SHOW POOLS;
# SHOW STATS;
# SHOW CLIENTS;
# SHOW SERVERS;
```

---

## B2. EXPLAIN ANALYZE e ottimizzazione

```sql
-- EXPLAIN ANALYZE per capire il piano di esecuzione
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.name, COUNT(o.id) as orders
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5
ORDER BY orders DESC
LIMIT 100;

-- Output da interpretare:
-- Seq Scan = scansione completa (BAD se tabella grande)
-- Index Scan = usa indice (GOOD)
-- Bitmap Heap Scan = usa indice ma non sequenzialmente (MIXED)
-- Hash Join vs Nested Loop vs Merge Join
-- Buffers: hit=1000 read=50 → hit sono da cache, read da disco
-- actual time=X..Y: X=prima riga, Y=ultima riga (ms)
-- rows=N (actual): righe effettive
-- rows=N (estimated): stima del planner — se molto diversa, aggiorna statistiche

-- Aggiorna statistiche
ANALYZE users;
ANALYZE orders;
VACUUM ANALYZE;  -- entrambi

-- pg_stat_statements — query più lente
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- postgresql.conf
-- shared_preload_libraries = 'pg_stat_statements'
-- pg_stat_statements.max = 10000
-- pg_stat_statements.track = all

-- Top 10 query per tempo totale
SELECT
    round(total_exec_time::numeric, 2) AS total_ms,
    round(mean_exec_time::numeric, 2) AS mean_ms,
    calls,
    round((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) AS pct,
    substring(query, 1, 100) AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Reset statistiche
SELECT pg_stat_statements_reset();
```

---

# Parte C — Indici e Partitioning

---

## C1. Tipi di indici

```sql
-- B-Tree (default) — per =, <, >, BETWEEN, LIKE 'prefix%'
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_date ON orders(created_at DESC);

-- Indice parziale — solo subset dei dati
CREATE INDEX idx_orders_pending ON orders(user_id)
    WHERE status = 'pending';

-- Indice composito — per query su più colonne
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);
-- Usato da: WHERE user_id = X ORDER BY created_at DESC

-- GIN — per array, JSONB, full-text search
CREATE INDEX idx_tags_gin ON articles USING GIN(tags);  -- array
CREATE INDEX idx_data_gin ON events USING GIN(data);    -- JSONB
CREATE INDEX idx_fts ON articles USING GIN(to_tsvector('italian', content));

-- BRIN — per tabelle grandi ordinate fisicamente (es. log con timestamp)
-- Molto leggero, meno preciso
CREATE INDEX idx_logs_time_brin ON logs USING BRIN(created_at)
    WITH (pages_per_range = 128);

-- Rebuilding indice (online, no lock)
REINDEX INDEX CONCURRENTLY idx_users_email;

-- Indice inutilizzati
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;
```

---

## C2. Table partitioning

```sql
-- Partizionamento per range (es. per data)
CREATE TABLE orders (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    user_id INT NOT NULL,
    amount NUMERIC(10,2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Crea partizioni per anno
CREATE TABLE orders_2023
    PARTITION OF orders
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE orders_2024
    PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Indici sulle partizioni (ereditati automaticamente in PG 11+)
CREATE INDEX ON orders(user_id, created_at DESC);

-- Partizionamento per lista (es. per regione)
CREATE TABLE events (
    id BIGINT,
    region TEXT NOT NULL,
    data JSONB
) PARTITION BY LIST (region);

CREATE TABLE events_eu PARTITION OF events FOR VALUES IN ('IT', 'DE', 'FR', 'ES');
CREATE TABLE events_us PARTITION OF events FOR VALUES IN ('US', 'CA', 'MX');
CREATE TABLE events_other PARTITION OF events DEFAULT;

-- Detach/attach partizione (operazione admin)
ALTER TABLE orders DETACH PARTITION orders_2023;
ALTER TABLE orders ATTACH PARTITION orders_2023
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

-- Rimuovi partizione vecchia (elimina solo dati di quell'anno)
DROP TABLE orders_2022;
-- MOLTO più veloce di DELETE FROM orders WHERE created_at < '2023-01-01'
```

---

# Parte D — Monitoring e Diagnostica

---

## D1. Query di diagnostica

```sql
-- Connessioni attive
SELECT pid, usename, application_name, client_addr,
       state, wait_event_type, wait_event,
       now() - query_start AS durata,
       substring(query, 1, 80) AS query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY durata DESC;

-- Lock e blocchi
SELECT
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query,
    now() - blocked.query_start AS durata_blocco
FROM pg_stat_activity AS blocked
JOIN pg_stat_activity AS blocking
    ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE cardinality(pg_blocking_pids(blocked.pid)) > 0;

-- Termina query lenta
SELECT pg_cancel_backend(PID);   -- segnale SIGINT (graceful)
SELECT pg_terminate_backend(PID); -- segnale SIGTERM (force)

-- Dimensione tabelle
SELECT
    relname AS tabella,
    pg_size_pretty(pg_total_relation_size(relid)) AS dimensione_totale,
    pg_size_pretty(pg_relation_size(relid)) AS dimensione_dati,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS indici
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- Autovacuum performance
SELECT
    relname,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) AS pct_dead,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

---

## D2. prometheus postgres_exporter

```yaml
# docker-compose.yml
services:
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:password@localhost:5432/postgres?sslmode=disable"
      PG_EXPORTER_EXTEND_QUERY_PATH: /etc/postgres_exporter/queries.yml
    volumes:
      - ./queries.yml:/etc/postgres_exporter/queries.yml:ro
    ports:
      - "9187:9187"
```

```yaml
# queries.yml — query personalizzate per postgres_exporter
pg_table_bloat:
  query: |
    SELECT schemaname, tablename,
           round((n_dead_tup::float / NULLIF(n_live_tup + n_dead_tup, 0)) * 100, 2) AS bloat_pct
    FROM pg_stat_user_tables
    WHERE n_live_tup + n_dead_tup > 1000
  metrics:
    - schemaname:
        usage: "LABEL"
    - tablename:
        usage: "LABEL"
    - bloat_pct:
        usage: "GAUGE"
        description: "Percentuale di tuple morte (bloat)"
```

---

# Parte E — Riepilogo

## Comandi essenziali admin

```sql
-- Mostra configurazione
SHOW shared_buffers;
SHOW max_connections;
SELECT * FROM pg_settings WHERE name LIKE 'max_%';

-- Ricarica configurazione (senza restart)
SELECT pg_reload_conf();

-- Checkpoint forzato
CHECKPOINT;

-- Backup logico
-- pg_dump -Fc -Z 5 -j 4 -f dump.pgc dbname

-- Restore
-- pg_restore -Fc -j 4 -d dbname dump.pgc
```

## Parametri postgresql.conf chiave

| Parametro | Valore tipico (16GB RAM) | Impatto |
|---|---|---|
| `shared_buffers` | `4GB` | Cache dati in RAM |
| `work_mem` | `64MB` | Memoria per sort/join |
| `maintenance_work_mem` | `512MB` | VACUUM, CREATE INDEX |
| `effective_cache_size` | `12GB` | Stima cache OS per planner |
| `wal_buffers` | `64MB` | Buffer WAL |
| `checkpoint_completion_target` | `0.9` | Spread checkpoint nel tempo |
| `max_connections` | `100` | Con pgBouncer: 50 |

## Prossimi passi

- `tutorial_linux_30_prometheus_grafana.md` — monitoring avanzato
- `tutorial_linux_18_database.md` — basi PostgreSQL
