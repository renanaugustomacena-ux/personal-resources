# Database su Linux — Guida Completa

> **Modulo 18** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **PostgreSQL > MySQL per nuovi progetti.**
2. **Tuning: `shared_buffers`, `effective_cache_size`, `max_connections`.**
3. **`huge_pages = on` per reduce TLB pressure.**
4. **Backup: pg_dumpall + WAL archive + PBR (PITR).**
5. **Ogni database in produzione richiede: monitoring, backup testato, connection pooling, sicurezza di rete.**
6. **Scegliere il database giusto per il workload: relazionale, documentale, key-value, time-series.**


## Indice

- [Panoramica](#panoramica)
- [PostgreSQL](#postgresql)
  - [Installazione e file di sistema](#installazione-e-file-di-sistema)
  - [Configurazione postgresql.conf](#configurazione-postgresqlconf)
  - [Autenticazione pg_hba.conf](#autenticazione-pg_hbaconf)
  - [Utenti, ruoli e permessi](#utenti-ruoli-e-permessi)
  - [Database e schemi](#database-e-schemi)
  - [Performance: EXPLAIN ANALYZE](#performance-explain-analyze)
  - [Indici: B-tree, GIN, GiST, BRIN](#indici-b-tree-gin-gist-brin)
  - [VACUUM e autovacuum](#vacuum-e-autovacuum)
  - [Connection pooling: PgBouncer](#connection-pooling-pgbouncer)
    - [Tuning avanzato PgBouncer e dimensionamento pool](#tuning-avanzato-pgbouncer-e-dimensionamento-pool)
  - [Backup e recovery](#postgresql-backup-e-recovery)
    - [pgBackRest e Barman: backup fisico avanzato](#pgbackrest-e-barman-backup-fisico-avanzato)
  - [Replica PostgreSQL](#replica-postgresql)
    - [PostgreSQL 17: novità nella replica logica](#postgresql-17-novità-nella-replica-logica)
  - [Sicurezza PostgreSQL](#sicurezza-postgresql)
  - [Monitoring PostgreSQL](#monitoring-postgresql)
    - [pg_stat_io e observability avanzata](#pg_stat_io-e-observability-avanzata-postgresql-16)
- [MySQL/MariaDB](#mysqlmariadb)
  - [Installazione e hardening](#installazione-e-hardening)
  - [Configurazione my.cnf](#configurazione-mycnf)
  - [InnoDB vs MyISAM](#innodb-vs-myisam)
  - [MariaDB 11 vs MySQL 8.4: punti di divergenza](#mariadb-11-vs-mysql-84-punti-di-divergenza)
  - [Utenti e privilegi MySQL](#utenti-e-privilegi-mysql)
  - [Replica MySQL](#replica-mysql)
  - [Backup MySQL](#backup-mysql)
  - [Monitoring MySQL](#monitoring-mysql)
- [SQLite](#sqlite)
  - [Casi d'uso](#casi-duso)
  - [Modalita WAL](#modalita-wal)
    - [Tabelle STRICT e configurazione di produzione](#tabelle-strict-e-configurazione-di-produzione)
  - [Accesso concorrente e locking](#accesso-concorrente-e-locking)
  - [Backup SQLite](#backup-sqlite)
- [Redis](#redis)
  - [Installazione e configurazione](#installazione-e-configurazione-redis)
  - [ACL, Functions e il fork Valkey](#acl-functions-e-il-fork-valkey)
  - [Tipi di dato](#tipi-di-dato-redis)
  - [Persistenza: RDB e AOF](#persistenza-rdb-e-aof)
  - [Replica Redis](#replica-redis)
  - [Redis Sentinel](#redis-sentinel)
  - [Redis Cluster](#redis-cluster)
- [MongoDB](#mongodb)
  - [Installazione e configurazione](#installazione-e-configurazione-mongodb)
  - [Operazioni CRUD](#operazioni-crud-mongodb)
  - [Indici MongoDB](#indici-mongodb)
  - [Replica set MongoDB](#replica-set-mongodb)
  - [Sharding MongoDB](#sharding-mongodb)
- [Matrice comparativa database](#matrice-comparativa-database)
- [Matrice decisionale: quale database scegliere](#matrice-decisionale-quale-database-scegliere)
- [Monitoring database](#monitoring-database)
- [Sicurezza database](#sicurezza-database)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

La gestione dei database è una competenza critica per l'amministratore Linux. PostgreSQL e MySQL/MariaDB sono i database relazionali più diffusi. Redis è il key-value store in-memory standard per caching e sessioni. MongoDB è il database documentale più popolare. SQLite è embedded, ideale per applicazioni locali. Per ogni database: installazione, configurazione, operazioni base, backup e monitoring.

### Classificazione dei database

| Tipo | Esempi | Modello dati | Caso d'uso principale |
|------|--------|-------------|----------------------|
| Relazionale (RDBMS) | PostgreSQL, MySQL, MariaDB | Tabelle, righe, colonne | Transazioni ACID, dati strutturati |
| Documentale | MongoDB, CouchDB | Documenti JSON/BSON | Schemi flessibili, prototipazione rapida |
| Key-Value | Redis, Memcached, etcd | Chiave → valore | Caching, sessioni, code |
| Colonnare | ClickHouse, Cassandra | Colonne raggruppate | Analytics, time-series, OLAP |
| Grafo | Neo4j, ArangoDB | Nodi e archi | Social network, knowledge graph |
| Embedded | SQLite, DuckDB | File locale | Applicazioni standalone, test |

### Protocolli e porte predefinite

| Database | Porta | Protocollo |
|----------|-------|-----------|
| PostgreSQL | 5432 | libpq (TCP) |
| MySQL/MariaDB | 3306 | MySQL protocol (TCP) |
| Redis | 6379 | RESP (TCP) |
| MongoDB | 27017 | MongoDB wire protocol (TCP) |
| SQLite | — | File locale (nessuna rete) |

---

## PostgreSQL

### Installazione e file di sistema

```bash
# Installazione su Debian/Ubuntu
sudo apt install postgresql postgresql-client postgresql-contrib

# Installazione su RHEL/Fedora
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql

# Stato del servizio
sudo systemctl status postgresql
sudo systemctl start postgresql
sudo systemctl restart postgresql
sudo systemctl reload postgresql          # Ricarica configurazione senza downtime

# Versione
sudo -u postgres psql -c "SELECT version();"

# File principali (Debian, versione 16)
/etc/postgresql/16/main/postgresql.conf   # Configurazione server
/etc/postgresql/16/main/pg_hba.conf       # Autenticazione client
/etc/postgresql/16/main/pg_ident.conf     # Mappatura utenti OS → DB
/var/lib/postgresql/16/main/              # Data directory (PGDATA)
/var/lib/postgresql/16/main/pg_wal/       # Directory WAL
/var/log/postgresql/                       # Log

# File principali (RHEL)
/var/lib/pgsql/16/data/postgresql.conf
/var/lib/pgsql/16/data/pg_hba.conf
/var/lib/pgsql/16/data/

# Verificare posizione data directory
sudo -u postgres psql -c "SHOW data_directory;"
sudo -u postgres psql -c "SHOW config_file;"
sudo -u postgres psql -c "SHOW hba_file;"
```

### Configurazione postgresql.conf

```bash
# postgresql.conf — parametri principali
# Dopo ogni modifica: sudo systemctl reload postgresql
# Alcuni parametri richiedono restart (contrassegnati con *)

# === CONNESSIONI ===
listen_addresses = '*'                     # Ascolto su tutte le interfacce
port = 5432
max_connections = 200                      # * Cambiare con cautela

# === MEMORIA ===
shared_buffers = 4GB                       # * ~25% della RAM totale
effective_cache_size = 12GB                # ~75% della RAM (stima per planner)
work_mem = 16MB                            # Per operazione sort/hash (attenzione: moltiplicato per connessione)
maintenance_work_mem = 512MB               # Per VACUUM, CREATE INDEX, ALTER TABLE
huge_pages = try                           # * Riduce TLB pressure su server con RAM > 8GB
temp_buffers = 32MB                        # Buffer per tabelle temporanee

# === CHECKPOINT E WAL ===
wal_level = replica                        # * minimal | replica | logical
max_wal_size = 2GB                         # Soglia per trigger checkpoint
min_wal_size = 512MB
checkpoint_completion_target = 0.9         # Distribuisce I/O del checkpoint
wal_compression = on                       # Comprime WAL per ridurre I/O
max_wal_senders = 5                        # * Numero massimo connessioni di replica
wal_keep_size = 1GB                        # WAL da mantenere per repliche in ritardo

# === WRITE AHEAD LOG — ARCHIVIO ===
archive_mode = on                          # * Abilita archiviazione WAL
archive_command = 'cp %p /archive/wal/%f'  # Comando per archiviare i WAL

# === QUERY PLANNER ===
random_page_cost = 1.1                     # Per SSD (default 4.0 per HDD)
effective_io_concurrency = 200             # Per SSD (default 1 per HDD)
default_statistics_target = 100            # Campioni per statistiche (aumentare per query complesse)

# === PARALLELISMO ===
max_worker_processes = 8                   # * Numero massimo processi worker
max_parallel_workers_per_gather = 4        # Worker paralleli per query
max_parallel_workers = 8                   # * Worker paralleli totali
max_parallel_maintenance_workers = 4       # Worker per VACUUM, CREATE INDEX

# === LOGGING ===
log_destination = 'stderr'
logging_collector = on                     # *
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 500           # Log query più lente di 500ms
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0                         # Log ogni file temporaneo creato
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_statement = 'ddl'                      # Log DDL (none | ddl | mod | all)

# === AUTOVACUUM ===
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.1       # VACUUM quando 10% righe modificate
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.05     # ANALYZE quando 5% righe modificate

# === LOCALE ===
timezone = 'Europe/Rome'
lc_messages = 'it_IT.UTF-8'
default_text_search_config = 'pg_catalog.italian'
```

**Calcolo rapido della memoria:**
```
RAM totale del server: 16 GB
shared_buffers         = 4 GB   (25%)
effective_cache_size   = 12 GB  (75%)
work_mem               = 16 MB  (× max_connections = 3.2 GB max teorico)
maintenance_work_mem   = 512 MB
```

> **Regola:** `work_mem × max_connections` non deve superare il 50% della RAM.

### Autenticazione pg_hba.conf

Il file `pg_hba.conf` controlla chi puo connettersi e con quale metodo di autenticazione. Le righe sono valutate dall'alto verso il basso: la prima corrispondenza vince.

```bash
# pg_hba.conf — formato:
# TYPE    DATABASE   USER       ADDRESS          METHOD

# === Connessioni locali via socket Unix ===
local   all         postgres                    peer
local   all         all                         scram-sha-256

# === Connessioni locali via TCP ===
host    all         all        127.0.0.1/32     scram-sha-256
host    all         all        ::1/128          scram-sha-256

# === Connessioni dalla rete interna ===
host    all         all        10.0.0.0/8       scram-sha-256
host    all         all        192.168.0.0/16   scram-sha-256

# === Replica ===
host    replication  replicator 10.0.0.0/8      scram-sha-256

# === SSL obbligatorio per rete esterna ===
hostssl all         all        0.0.0.0/0        scram-sha-256

# === Rifiuta tutto il resto ===
host    all         all        0.0.0.0/0        reject
```

**Metodi di autenticazione:**

| Metodo | Descrizione | Uso |
|--------|------------|-----|
| `peer` | Utente OS = utente DB | Connessioni locali Unix socket |
| `scram-sha-256` | Password con hash SCRAM | Standard per TCP |
| `md5` | Password con hash MD5 | Legacy, preferire SCRAM |
| `cert` | Certificato SSL client | Massima sicurezza |
| `ldap` | Autenticazione LDAP | Integrazione Active Directory |
| `gss` | Kerberos/GSSAPI | Ambienti enterprise |
| `reject` | Rifiuta connessione | Blocco esplicito |
| `trust` | Nessuna autenticazione | **MAI in produzione** |

```bash
# Dopo modifica, ricaricare:
sudo systemctl reload postgresql
# oppure da psql:
SELECT pg_reload_conf();
```

### Utenti, ruoli e permessi

In PostgreSQL, utenti e gruppi sono entrambi "ruoli". Un ruolo con LOGIN è un utente, senza LOGIN è un gruppo.

```sql
-- === CREAZIONE RUOLI ===
-- Creare un utente applicativo
CREATE ROLE app_user WITH LOGIN PASSWORD 'strong_password_here'
    VALID UNTIL '2027-12-31'
    CONNECTION LIMIT 20;

-- Creare un ruolo di gruppo (senza login)
CREATE ROLE app_readonly NOLOGIN;
CREATE ROLE app_readwrite NOLOGIN;
CREATE ROLE app_admin NOLOGIN;

-- Assegnare utenti ai gruppi
GRANT app_readonly TO analyst_user;
GRANT app_readwrite TO app_user;
GRANT app_admin TO dba_user;

-- === PRIVILEGI SU DATABASE ===
GRANT CONNECT ON DATABASE mydb TO app_readonly;
GRANT CREATE ON DATABASE mydb TO app_admin;
REVOKE ALL ON DATABASE mydb FROM PUBLIC;        -- Rimuovi accesso pubblico

-- === PRIVILEGI SU SCHEMA ===
GRANT USAGE ON SCHEMA public TO app_readonly;
GRANT CREATE ON SCHEMA public TO app_readwrite;

-- === PRIVILEGI SU TABELLE ===
-- Lettura
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO app_readonly;     -- Anche per tabelle future

-- Lettura e scrittura
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_readwrite;

-- Sequenze (necessario per INSERT con SERIAL/IDENTITY)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO app_readwrite;

-- === REVOCA PRIVILEGI ===
REVOKE INSERT, UPDATE, DELETE ON TABLE sensitive_data FROM app_readwrite;

-- === GESTIONE RUOLI ===
ALTER ROLE app_user SET statement_timeout = '30s';    -- Timeout query
ALTER ROLE app_user SET search_path = myschema, public;
ALTER ROLE app_user WITH PASSWORD 'new_password';

-- === VERIFICA ===
\du                                     -- Lista ruoli
\dp tablename                           -- Permessi su tabella
SELECT * FROM pg_roles WHERE rolname = 'app_user';

-- === DALLA SHELL ===
sudo -u postgres createuser --pwprompt myuser
sudo -u postgres createuser --replication replicator
sudo -u postgres dropuser myuser
```

### Database e schemi

```sql
-- === CREAZIONE DATABASE ===
CREATE DATABASE myapp
    OWNER app_admin
    ENCODING 'UTF8'
    LC_COLLATE 'it_IT.UTF-8'
    LC_CTYPE 'it_IT.UTF-8'
    TEMPLATE template0
    CONNECTION LIMIT 100;

-- === SCHEMI (namespace per organizzare tabelle) ===
CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION app_admin;
CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION analyst_user;
CREATE SCHEMA IF NOT EXISTS audit AUTHORIZATION app_admin;

-- Impostare il search_path
SET search_path TO app, public;
ALTER DATABASE myapp SET search_path TO app, public;

-- Spostare una tabella in un altro schema
ALTER TABLE public.users SET SCHEMA app;

-- === TABLESPACE (directory fisiche per i dati) ===
-- Utile per separare dati su dischi diversi (SSD per indici, HDD per archivio)
CREATE TABLESPACE fast_disk LOCATION '/mnt/ssd/pgdata';
CREATE TABLE hot_data (...) TABLESPACE fast_disk;
CREATE INDEX idx_hot ON hot_data(id) TABLESPACE fast_disk;

-- === COMANDI PSQL ===
\l                                      -- Lista database
\l+                                     -- Lista con dimensioni
\dn                                     -- Lista schemi
\dt app.*                               -- Tabelle nello schema app
\dt+                                    -- Tabelle con dimensioni
\d tablename                            -- Struttura tabella
\di                                     -- Lista indici
\df                                     -- Lista funzioni
\c dbname                               -- Cambia database
\x                                      -- Attiva/disattiva output espanso
\timing                                 -- Abilita timing query
\i file.sql                             -- Esegui file SQL
\copy                                   -- Import/export CSV
\q                                      -- Esci

-- === DALLA SHELL ===
sudo -u postgres createdb -O myuser mydb
sudo -u postgres dropdb mydb
psql -h localhost -U username -d dbname
```

### Performance: EXPLAIN ANALYZE

`EXPLAIN` mostra il piano di esecuzione scelto dal planner. `EXPLAIN ANALYZE` lo esegue realmente e confronta la stima con i dati reali. 

```sql
-- Piano stimato (non esegue la query)
EXPLAIN SELECT * FROM orders WHERE customer_id = 42;

-- Piano reale con tempi di esecuzione
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
    SELECT * FROM orders WHERE customer_id = 42;

-- Output tipico:
-- Seq Scan on orders  (cost=0.00..1250.00 rows=50 width=120)
--                     (actual time=0.015..8.432 rows=47 loops=1)
--   Filter: (customer_id = 42)
--   Rows Removed by Filter: 99953
--   Buffers: shared hit=540
-- Planning Time: 0.085 ms
-- Execution Time: 8.501 ms

-- Con indice:
-- Index Scan using idx_orders_customer on orders  (cost=0.42..12.50 rows=50 width=120)
--                                                  (actual time=0.021..0.145 rows=47 loops=1)
--   Index Cond: (customer_id = 42)
--   Buffers: shared hit=5
-- Planning Time: 0.090 ms
-- Execution Time: 0.178 ms
```

**Chiavi di lettura dell'output:**

| Campo | Significato |
|-------|------------|
| `cost=startup..total` | Costo stimato (unita arbitrarie) |
| `rows` | Righe stimate vs righe effettive |
| `width` | Dimensione media riga in byte |
| `actual time` | Tempo reale (ms), start..end |
| `loops` | Volte che il nodo e stato eseguito |
| `Buffers: shared hit` | Pagine lette dalla cache |
| `Buffers: shared read` | Pagine lette da disco |
| `Seq Scan` | Scansione sequenziale (nessun indice usato) |
| `Index Scan` | Scansione con indice (efficiente) |
| `Bitmap Index Scan` | Indice bitmap (molte righe sparse) |
| `Hash Join` / `Merge Join` / `Nested Loop` | Tipo di join |

**Red flags nel piano:**

```sql
-- Seq Scan su tabelle grandi → manca un indice
-- rows=1 stimato ma actual rows=100000 → statistiche obsolete → ANALYZE
-- Buffers: shared read molto alto → dati non in cache → aumentare shared_buffers
-- Sort Method: external merge → work_mem troppo basso
-- Nested Loop con loops alto → join inefficiente

-- Aggiornare le statistiche
ANALYZE orders;
ANALYZE VERBOSE orders;    -- Con output dettagliato

-- Forzare raccolta statistiche estese
ALTER TABLE orders ALTER COLUMN status SET STATISTICS 500;
ANALYZE orders;
```

**Query utili per trovare query lente:**

```sql
-- Richiede l'estensione pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top 10 query per tempo totale
SELECT query, calls, total_exec_time, mean_exec_time,
       rows, shared_blks_hit, shared_blks_read
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Query con più I/O
SELECT query, shared_blks_read, shared_blks_hit,
       (shared_blks_read::float / NULLIF(shared_blks_read + shared_blks_hit, 0)) AS miss_ratio
FROM pg_stat_statements
ORDER BY shared_blks_read DESC
LIMIT 10;

-- Reset statistiche
SELECT pg_stat_statements_reset();
```

### Indici: B-tree, GIN, GiST, BRIN

```sql
-- === B-TREE (default) ===
-- Ideale per: uguaglianza (=), range (<, >, BETWEEN), ORDER BY, LIKE 'prefix%'
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_date ON orders (created_at DESC);

-- Indice composto (ordine delle colonne conta!)
CREATE INDEX idx_orders_cust_date ON orders (customer_id, created_at DESC);
-- Efficiente per: WHERE customer_id = 42 AND created_at > '2026-01-01'
-- Efficiente per: WHERE customer_id = 42 ORDER BY created_at DESC
-- NON efficiente per: WHERE created_at > '2026-01-01' (senza customer_id)

-- Indice unico
CREATE UNIQUE INDEX idx_users_email ON users (email);

-- Indice parziale (solo righe che soddisfano la condizione)
CREATE INDEX idx_orders_pending ON orders (created_at)
    WHERE status = 'pending';
-- Piu piccolo e veloce perché indicizza solo le righe rilevanti

-- Indice su espressione
CREATE INDEX idx_users_email_lower ON users (lower(email));
-- Per query: WHERE lower(email) = 'user@example.com'

-- Covering index (INCLUDE: colonne nel foglia, non nella chiave)
CREATE INDEX idx_orders_cover ON orders (customer_id)
    INCLUDE (total_amount, status);
-- Index-only scan: non serve accedere alla tabella

-- === GIN (Generalized Inverted Index) ===
-- Ideale per: array, JSONB, full-text search, trigrammi
CREATE INDEX idx_products_tags ON products USING gin (tags);
-- Per query: WHERE tags @> ARRAY['electronics']

CREATE INDEX idx_docs_data ON documents USING gin (metadata jsonb_path_ops);
-- Per query: WHERE metadata @> '{"category": "tech"}'

-- Full-text search con GIN
CREATE INDEX idx_articles_fts ON articles
    USING gin (to_tsvector('italian', title || ' ' || body));
-- Per query: WHERE to_tsvector('italian', title || ' ' || body) @@ to_tsquery('italian', 'linux & database')

-- Trigrammi per ricerca fuzzy
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_products_name_trgm ON products USING gin (name gin_trgm_ops);
-- Per query: WHERE name ILIKE '%search%' oppure WHERE name % 'searc'

-- === GiST (Generalized Search Tree) ===
-- Ideale per: dati geometrici, range, nearest-neighbor, full-text search
CREATE INDEX idx_locations_point ON locations USING gist (coordinates);
-- Per query: WHERE coordinates <-> point(45.07, 7.68) < 0.01

-- Range types
CREATE INDEX idx_events_period ON events USING gist (period);
-- Per query: WHERE period && daterange('2026-01-01', '2026-12-31')

-- Exclusion constraint (impedisce sovrapposizione di periodi)
ALTER TABLE bookings ADD CONSTRAINT no_overlap
    EXCLUDE USING gist (room_id WITH =, period WITH &&);

-- === BRIN (Block Range Index) ===
-- Ideale per: tabelle grandi con dati ordinati fisicamente (log, time-series)
-- Molto compatto: ordini di grandezza più piccolo di B-tree
CREATE INDEX idx_logs_timestamp ON logs USING brin (created_at)
    WITH (pages_per_range = 32);
-- Efficiente solo se i dati sono inseriti in ordine cronologico

-- === MANUTENZIONE INDICI ===
-- Ricostruire un indice (senza bloccare la tabella)
REINDEX INDEX CONCURRENTLY idx_orders_customer;

-- Verificare l'uso degli indici
SELECT schemaname, relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
-- idx_scan = 0 → indice mai usato → candidato per rimozione

-- Dimensione degli indici
SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass))
FROM pg_indexes WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;

-- Indici duplicati o ridondanti
SELECT a.indexrelid::regclass AS idx_a, b.indexrelid::regclass AS idx_b
FROM pg_index a, pg_index b
WHERE a.indrelid = b.indrelid
  AND a.indexrelid != b.indexrelid
  AND a.indkey::text LIKE b.indkey::text || '%';
```

### VACUUM e autovacuum

PostgreSQL usa MVCC (Multi-Version Concurrency Control): le righe aggiornate o cancellate non vengono rimosse immediatamente, ma marcate come "dead tuples". VACUUM recupera lo spazio. 

```sql
-- === VACUUM MANUALE ===
VACUUM orders;                          -- Recupera dead tuples (non restituisce spazio all'OS)
VACUUM VERBOSE orders;                  -- Con output dettagliato
VACUUM (VERBOSE, PARALLEL 4) orders;   -- Vacuum parallelo (PG 13+)
VACUUM ANALYZE orders;                  -- VACUUM + aggiorna statistiche

VACUUM FULL orders;                     -- Riscrive la tabella, recupera spazio su disco
                                        -- ATTENZIONE: lock esclusivo sulla tabella!

-- === MONITORARE DEAD TUPLES ===
SELECT schemaname, relname, n_live_tup, n_dead_tup,
       round(n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) AS dead_pct,
       last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- === CONFIGURAZIONE AUTOVACUUM ===
-- Globale (postgresql.conf):
autovacuum = on
autovacuum_max_workers = 3              -- Worker paralleli
autovacuum_naptime = 1min               -- Intervallo tra i cicli
autovacuum_vacuum_threshold = 50        -- Minimo dead tuples prima di vacuum
autovacuum_vacuum_scale_factor = 0.1    -- + 10% della tabella
autovacuum_analyze_threshold = 50       -- Minimo righe modificate prima di analyze
autovacuum_analyze_scale_factor = 0.05  -- + 5% della tabella
autovacuum_vacuum_cost_delay = 2ms      -- Pausa tra blocchi di I/O (throttling)
autovacuum_vacuum_cost_limit = 200      -- Limite costo I/O per ciclo

-- Per tabella (override globale):
ALTER TABLE orders SET (autovacuum_vacuum_scale_factor = 0.01);   -- Vacuum più aggressivo
ALTER TABLE orders SET (autovacuum_vacuum_threshold = 1000);
ALTER TABLE orders SET (autovacuum_analyze_scale_factor = 0.01);

-- Per tabelle molto grandi (milioni di righe) ridurre scale_factor
-- altrimenti il 10% rappresenta troppe dead tuples prima del vacuum

-- === TRANSACTION ID WRAPAROUND ===
-- PostgreSQL usa transaction ID a 32 bit: dopo ~2 miliardi di transazioni, wraparound
-- autovacuum_freeze_max_age controlla quando forzare il freeze
-- Monitorare:
SELECT datname, age(datfrozenxid) AS xid_age,
       pg_size_pretty(pg_database_size(datname)) AS db_size
FROM pg_database
ORDER BY age(datfrozenxid) DESC;
-- Se xid_age > 200M → pericolo. > 1G → emergenza.

-- Per tabella:
SELECT relname, age(relfrozenxid) AS xid_age
FROM pg_class
WHERE relkind = 'r'
ORDER BY age(relfrozenxid) DESC
LIMIT 20;
```

### Connection pooling: PgBouncer

PgBouncer è un connection pooler leggero per PostgreSQL. Riduce il numero di connessioni reali al database, migliorando performance e scalabilità.

```bash
# Installazione
sudo apt install pgbouncer

# File di configurazione
/etc/pgbouncer/pgbouncer.ini
/etc/pgbouncer/userlist.txt

# === pgbouncer.ini ===
[databases]
mydb = host=127.0.0.1 port=5432 dbname=mydb

# Wildcard: tutte le connessioni vanno allo stesso server
* = host=127.0.0.1 port=5432

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432                        # Le applicazioni si connettono qui
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# === POOL MODE ===
pool_mode = transaction                   # Riassegna connessione dopo ogni transazione
# pool_mode = session                     # Connessione dedicata per sessione (come senza pooler)
# pool_mode = statement                   # Per query singole (non supporta transazioni multi-statement)

# === LIMITI ===
max_client_conn = 1000                    # Connessioni client massime
default_pool_size = 25                    # Connessioni reali per database/utente
min_pool_size = 5                         # Connessioni minime mantenute
reserve_pool_size = 5                     # Connessioni extra per picchi
reserve_pool_timeout = 3                  # Secondi prima di usare il reserve pool

# === TIMEOUT ===
server_idle_timeout = 600                 # Chiudi connessione server dopo 10 min idle
client_idle_timeout = 0                   # 0 = nessun timeout client
query_timeout = 0                         # 0 = nessun timeout query
server_connect_timeout = 15

# === LOGGING ===
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60

# === userlist.txt ===
# Formato: "username" "password_hash"
# Generare con:
psql -Atq -h localhost -U postgres \
  -c "SELECT '\"' || rolname || '\" \"' || rolpassword || '\"' FROM pg_authid WHERE rolcanlogin" \
  > /etc/pgbouncer/userlist.txt

# Avvio e gestione
sudo systemctl enable --now pgbouncer
sudo systemctl restart pgbouncer

# Console di amministrazione PgBouncer
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer
SHOW POOLS;                               # Stato dei pool
SHOW CLIENTS;                             # Connessioni client
SHOW SERVERS;                             # Connessioni server
SHOW STATS;                               # Statistiche
SHOW CONFIG;                              # Configurazione
RELOAD;                                   # Ricarica configurazione
```

**Scelta del pool_mode:**

| Modalita | Pro | Contro | Uso |
|----------|-----|--------|-----|
| `session` | Compatibilita completa | Basso multiplexing | Legacy, LISTEN/NOTIFY |
| `transaction` | Ottimo multiplexing | No prepared statement cross-tx | **Consigliato per la maggior parte dei casi** |
| `statement` | Massimo multiplexing | No transazioni multi-statement | Query analytics, read-only |

#### Tuning avanzato PgBouncer e dimensionamento pool

**Formula per il dimensionamento del pool:**

```
pool_size = min(RAM_disponibile_MB / 20 / numero_database, 200)
```

Ogni connessione PostgreSQL consuma circa 10-20 MB di RAM (stack, work_mem, sort buffers).
Con 32 GB di RAM e 2 database, il massimo consigliato è circa `32000/20/2 = 800`,
ma in pratica 100-200 connessioni server-side sono sufficienti per la maggior parte
dei workload grazie al multiplexing di PgBouncer.

```ini
# === pgbouncer.ini — configurazione di produzione ===
[databases]
mydb = host=127.0.0.1 port=5432 dbname=mydb
mydb_ro = host=replica1 port=5432 dbname=mydb    # Pool separato per read replica

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = scram-sha-256                # Mai md5 in produzione (deprecato PG 17)
auth_file = /etc/pgbouncer/userlist.txt

# Pool sizing
default_pool_size = 25                   # Connessioni server per user/database
min_pool_size = 5                        # Mantieni almeno 5 connessioni calde
reserve_pool_size = 5                    # Extra per picchi
reserve_pool_timeout = 3                 # Secondi prima di usare reserve pool
max_client_conn = 1000                   # Max connessioni client totali
max_db_connections = 100                 # Max connessioni verso un singolo database

# Timeouts
server_idle_timeout = 300                # Chiudi connessioni server inattive dopo 5 min
client_idle_timeout = 0                  # 0 = nessun timeout client (gestire a livello app)
query_timeout = 120                      # Kill query dopo 2 minuti
query_wait_timeout = 30                  # Max attesa per una connessione dal pool

# TLS
client_tls_sslmode = require
client_tls_cert_file = /etc/pgbouncer/server.crt
client_tls_key_file = /etc/pgbouncer/server.key
server_tls_sslmode = verify-full
server_tls_ca_file = /etc/ssl/certs/pg-ca.crt

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60
```

**Metriche chiave da monitorare:**

```sql
-- Connessioni in attesa (CRITICO: se cl_waiting > 0 costantemente, pool troppo piccolo)
SHOW POOLS;
-- Colonne importanti: cl_active, cl_waiting, sv_active, sv_idle

-- Rapporto di utilizzo server
-- sv_active / (sv_active + sv_idle) > 0.8 → pool sotto pressione

-- Statistiche aggregate
SHOW STATS;
-- avg_query_time in microsecondi: se cresce, query lente o pool saturo
```

**PgBouncer vs Pgpool-II:**

| Aspetto | PgBouncer | Pgpool-II |
|---------|-----------|-----------|
| Scopo primario | Connection pooling | Pooling + HA + load balancing |
| Overhead per connessione | ~2 KB | ~16 KB |
| Max connessioni gestite | 10.000+ | ~2.000 |
| Query caching | No | Sì (in-memory) |
| Load balancing | No (usare HAProxy) | Sì (integrato, statement-level) |
| Failover automatico | No | Sì (watchdog) |
| Complessità configurazione | Bassa | Alta |
| Uso raccomandato | **Pooling puro** (più efficiente) | Quando serve HA integrato senza strumenti esterni |

Per la maggior parte dei deployment, PgBouncer è la scelta migliore per il solo pooling.
Se serve anche failover automatico e load balancing, valutare Pgpool-II oppure la
combinazione PgBouncer + Patroni + HAProxy.

### PostgreSQL Backup e recovery

```bash
# === PG_DUMP — BACKUP LOGICO ===
# Singolo database
pg_dump -h localhost -U app_admin -d mydb > backup.sql                # Plain text
pg_dump -h localhost -U app_admin -Fc -d mydb > backup.dump           # Custom format (compresso, raccomandato)
pg_dump -h localhost -U app_admin -Fd -j 4 -d mydb -f backup_dir/    # Directory format, 4 job paralleli
pg_dump -h localhost -U app_admin -Ft -d mydb > backup.tar            # Tar format

# Opzioni utili
pg_dump --schema-only -d mydb > schema.sql                            # Solo struttura
pg_dump --data-only -d mydb > data.sql                                # Solo dati
pg_dump -t orders -t customers -d mydb > partial.sql                  # Solo tabelle specifiche
pg_dump --exclude-table='*_log' -d mydb > no_logs.sql                 # Escludi tabelle

# Tutti i database + ruoli globali
pg_dumpall -h localhost -U postgres > all_databases.sql
pg_dumpall --globals-only > globals.sql                               # Solo ruoli e tablespace

# === PG_RESTORE — RIPRISTINO ===
# Da custom format
pg_restore -h localhost -U app_admin -d mydb backup.dump
pg_restore -h localhost -U app_admin -d mydb -j 4 backup.dump         # 4 job paralleli
pg_restore -h localhost -U app_admin --clean -d mydb backup.dump       # DROP prima di CREATE
pg_restore -h localhost -U app_admin -t orders -d mydb backup.dump     # Solo tabella orders

# Da plain text
psql -h localhost -U app_admin -d mydb < backup.sql

# Lista contenuto di un dump
pg_restore -l backup.dump

# === PG_BASEBACKUP — BACKUP FISICO ===
# Copia l'intero cluster (data directory) — necessario per PITR e replica
pg_basebackup -h localhost -U replicator -D /backup/base \
    --wal-method=stream \
    --checkpoint=fast \
    --progress \
    --verbose \
    --format=tar \
    --gzip \
    --label="backup_$(date +%Y%m%d)"

# Opzioni:
# --wal-method=stream    Include WAL necessari (raccomandato)
# --checkpoint=fast      Forza checkpoint immediato
# --format=tar           Output in tar (alternativa: plain)
# --gzip                 Comprimi output tar

# === WAL ARCHIVING — ARCHIVIAZIONE WAL ===
# postgresql.conf:
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /archive/wal/%f && cp %p /archive/wal/%f'
# Alternativa con rsync:
# archive_command = 'rsync -a %p backup-server:/archive/wal/%f'

# Verifica archiviazione:
SELECT * FROM pg_stat_archiver;

# === PITR — POINT IN TIME RECOVERY ===
# 1. Avere un base backup recente (pg_basebackup)
# 2. Avere tutti i WAL archiviati dal momento del base backup
# 3. Creare un recovery target

# Procedura:
# a) Fermare PostgreSQL
sudo systemctl stop postgresql

# b) Spostare il data directory corrente
mv /var/lib/postgresql/16/main /var/lib/postgresql/16/main.old

# c) Ripristinare il base backup
tar xzf /backup/base/base.tar.gz -C /var/lib/postgresql/16/main

# d) Creare il file di recovery
cat > /var/lib/postgresql/16/main/postgresql.auto.conf << 'EOF'
restore_command = 'cp /archive/wal/%f %p'
recovery_target_time = '2026-05-22 14:30:00+02'
recovery_target_action = 'promote'
EOF

# e) Creare il signal file per il recovery
touch /var/lib/postgresql/16/main/recovery.signal

# f) Avviare PostgreSQL (entrera in recovery mode)
sudo systemctl start postgresql

# g) Verificare: il server ripristinera fino al target_time
# Una volta promosso, il file recovery.signal viene rimosso

# === SCRIPT BACKUP AUTOMATICO ===
#!/bin/bash
# /usr/local/bin/pg_backup.sh
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "${BACKUP_DIR}/dump" "${BACKUP_DIR}/base"

# Dump logico di tutti i database
pg_dumpall -U postgres | gzip > "${BACKUP_DIR}/dump/all_${DATE}.sql.gz"

# Base backup settimanale (domenica)
if [ "$(date +%u)" -eq 7 ]; then
    pg_basebackup -U replicator -D "${BACKUP_DIR}/base/${DATE}" \
        --wal-method=stream --checkpoint=fast --format=tar --gzip
fi

# Pulizia backup vecchi
find "${BACKUP_DIR}" -name "*.gz" -mtime +${RETENTION_DAYS} -delete

# Verifica: tenta un restore di prova (mensile)
# Implementare separatamente su un server di test
```

#### pgBackRest e Barman: backup fisico avanzato

Per database PostgreSQL superiori a 100 GB, `pg_dump` diventa troppo lento per
rispettare le finestre di backup. Gli strumenti di backup fisico operano a livello
di file system e supportano backup incrementali, paralleli e compressi.

**pgBackRest — backup ad alte prestazioni:**

```bash
# === INSTALLAZIONE ===
sudo apt install pgbackrest

# === CONFIGURAZIONE (/etc/pgbackrest/pgbackrest.conf) ===
[global]
repo1-path=/backup/pgbackrest
repo1-retention-full=4                    # Mantieni 4 backup full
repo1-retention-diff=14                   # Mantieni 14 differenziali
repo1-cipher-type=aes-256-cbc            # Crittografia a riposo
repo1-cipher-pass=encryption-key-here
process-max=4                            # Parallelismo
compress-type=zst                        # Zstandard (migliore rapporto velocità/compressione)
compress-level=3
log-level-console=info
log-level-file=detail

[mydb]
pg1-path=/var/lib/postgresql/16/main

# === SETUP INIZIALE ===
sudo -u postgres pgbackrest --stanza=mydb stanza-create
sudo -u postgres pgbackrest --stanza=mydb check

# === TIPI DI BACKUP ===
# Full: copia completa (settimanale)
sudo -u postgres pgbackrest --stanza=mydb --type=full backup

# Differenziale: solo blocchi cambiati dall'ultimo full (giornaliero)
sudo -u postgres pgbackrest --stanza=mydb --type=diff backup

# Incrementale: solo blocchi cambiati dall'ultimo backup qualsiasi
sudo -u postgres pgbackrest --stanza=mydb --type=incr backup

# === RESTORE ===
# Restore completo (su un server pulito)
sudo systemctl stop postgresql
sudo -u postgres pgbackrest --stanza=mydb restore

# Restore a un punto nel tempo (PITR)
sudo -u postgres pgbackrest --stanza=mydb \
    --type=time --target="2026-05-24 10:30:00+02" restore

# Delta restore: ripristina solo i file cambiati (più veloce)
sudo -u postgres pgbackrest --stanza=mydb --delta restore

# === VERIFICA ===
sudo -u postgres pgbackrest --stanza=mydb info
```

**Barman — gestione centralizzata backup PostgreSQL:**

Barman (Backup and Recovery Manager) è sviluppato da EDB (EnterpriseDB) ed è
progettato per gestire backup di più server PostgreSQL da un server centrale.

```bash
# === INSTALLAZIONE ===
sudo apt install barman barman-cli

# === CONFIGURAZIONE SERVER BARMAN (/etc/barman.conf) ===
# [barman]
# barman_home = /var/lib/barman
# configuration_files_directory = /etc/barman.d
# backup_method = postgres                # Usa pg_basebackup
# archiver = off
# streaming_archiver = on
# retention_policy = RECOVERY WINDOW OF 7 DAYS

# === CONFIGURAZIONE PER SERVER (/etc/barman.d/mydb.conf) ===
# [mydb]
# description = "Production PostgreSQL"
# ssh_command = ssh postgres@db-server
# conninfo = host=db-server user=barman dbname=postgres
# streaming_conninfo = host=db-server user=streaming_barman
# backup_method = postgres
# streaming_archiver = on
# slot_name = barman

# === OPERAZIONI ===
# Verifica configurazione
barman check mydb

# Backup
barman backup mydb

# Lista backup
barman list-backup mydb

# Restore su un server target
barman recover mydb latest /var/lib/postgresql/16/main \
    --remote-ssh-command "ssh postgres@recovery-server"

# PITR
barman recover mydb latest /var/lib/postgresql/16/main \
    --target-time "2026-05-24 10:30:00+02" \
    --remote-ssh-command "ssh postgres@recovery-server"
```

**Confronto strumenti di backup PostgreSQL:**

| Caratteristica | pg_dump | pgBackRest | Barman |
|---------------|---------|------------|--------|
| Tipo | Logico | Fisico | Fisico |
| Velocità (500 GB) | Ore | Minuti | Minuti |
| Backup incrementale | No | Sì (blocco) | Sì |
| Parallelismo | Sì (-j) | Sì (process-max) | Limitato |
| PITR | No | Sì | Sì |
| Compressione | gzip, custom | zst, lz4, gz | gzip, bzip2 |
| Crittografia | No | AES-256 | No (usare GPG) |
| Multi-server | No | Sì (multi-repo) | Sì (architettura nativa) |
| Cloud storage | No | S3, GCS, Azure | S3 (barman-cloud) |
| Caso d'uso | Dev, DB piccoli (<50 GB) | Produzione, DB grandi | Gestione centralizzata multi-server |

**Strategia raccomandata:** usare pg_dump per backup logici portabili (migrazione,
dump di singole tabelle) e pgBackRest o Barman per backup fisici di produzione con PITR.
Non sono alternativi ma complementari.

### Replica PostgreSQL

#### Streaming Replication (replica fisica)

Replica l'intero cluster byte-per-byte. La replica è identica al primario.

```bash
# === SUL PRIMARIO ===

# postgresql.conf
wal_level = replica
max_wal_senders = 5
wal_keep_size = 1GB
synchronous_standby_names = ''            # Vuoto = asincrona
# synchronous_standby_names = 'standby1'  # Per replica sincrona

# pg_hba.conf
host replication replicator 10.0.0.0/8 scram-sha-256

# Creare l'utente di replica
sudo -u postgres psql -c "CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'rep_password';"

# Ricaricare configurazione
sudo systemctl reload postgresql

# === SULLA REPLICA ===

# 1. Fermare PostgreSQL
sudo systemctl stop postgresql

# 2. Rimuovere il data directory
rm -rf /var/lib/postgresql/16/main/*

# 3. Copiare i dati dal primario
sudo -u postgres pg_basebackup \
    -h 10.0.0.1 \
    -U replicator \
    -D /var/lib/postgresql/16/main \
    --wal-method=stream \
    --checkpoint=fast \
    --write-recovery-conf \
    --progress

# L'opzione --write-recovery-conf crea automaticamente:
# - standby.signal
# - primary_conninfo in postgresql.auto.conf

# 4. Verificare postgresql.auto.conf:
# primary_conninfo = 'host=10.0.0.1 port=5432 user=replicator password=rep_password'

# 5. Avviare la replica
sudo systemctl start postgresql

# === VERIFICA ===

# Sul primario:
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
FROM pg_stat_replication;

# Sulla replica:
SELECT pg_is_in_recovery();               -- Deve restituire 't'
SELECT pg_last_wal_receive_lsn();
SELECT pg_last_wal_replay_lsn();
SELECT pg_last_xact_replay_timestamp();   -- Ultimo timestamp replicato
```

#### Replication Slots

I replication slot impediscono al primario di rimuovere WAL non ancora consumati dalla replica.

```sql
-- Sul primario: creare un replication slot fisico
SELECT pg_create_physical_replication_slot('standby1_slot');

-- Sulla replica: aggiungere al primary_conninfo
-- primary_slot_name = 'standby1_slot'

-- Verificare slot attivi
SELECT slot_name, slot_type, active, restart_lsn,
       pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS retained_bytes
FROM pg_replication_slots;

-- ATTENZIONE: slot inattivi accumulano WAL indefinitamente!
-- Rimuovere slot non più necessari:
SELECT pg_drop_replication_slot('old_standby_slot');

-- Limite di sicurezza:
-- postgresql.conf: max_slot_wal_keep_size = 10GB
```

#### Logical Replication (replica logica)

Replica singole tabelle o pubblicazioni. Permette replica selettiva e tra versioni diverse di PostgreSQL.

```sql
-- === SUL PUBLISHER (sorgente) ===
-- postgresql.conf: wal_level = logical

-- Creare una pubblicazione
CREATE PUBLICATION my_pub FOR TABLE orders, customers;
-- oppure tutte le tabelle:
CREATE PUBLICATION my_pub FOR ALL TABLES;

-- === SUL SUBSCRIBER (destinazione) ===
-- Le tabelle devono già esistere con la stessa struttura

-- Creare una sottoscrizione
CREATE SUBSCRIPTION my_sub
    CONNECTION 'host=10.0.0.1 port=5432 dbname=mydb user=replicator password=rep_password'
    PUBLICATION my_pub;

-- Verificare stato
SELECT * FROM pg_stat_subscription;
SELECT * FROM pg_subscription_rel;

-- Aggiungere tabelle alla pubblicazione
ALTER PUBLICATION my_pub ADD TABLE new_table;
-- Sul subscriber: refresh
ALTER SUBSCRIPTION my_sub REFRESH PUBLICATION;

-- Disabilitare/riabilitare
ALTER SUBSCRIPTION my_sub DISABLE;
ALTER SUBSCRIPTION my_sub ENABLE;

-- Rimuovere
DROP SUBSCRIPTION my_sub;
DROP PUBLICATION my_pub;
```

#### PostgreSQL 17: novità nella replica logica

PostgreSQL 17 introduce miglioramenti significativi alla replica logica che la rendono
adatta a scenari di alta disponibilità precedentemente riservati alla replica fisica.

**Failover slot synchronization:**

Nelle versioni precedenti, un failover da primario a standby causava la perdita degli
slot di replica logica: i subscriber dovevano ricostruire lo stato da zero. PostgreSQL 17
introduce la sincronizzazione automatica degli slot di failover tra primario e standby.

```sql
-- === CONFIGURAZIONE FAILOVER SLOTS ===

-- Sul primario: abilitare la sincronizzazione degli slot
-- postgresql.conf:
-- sync_replication_slots = on        -- PG 17+

-- Creare una pubblicazione con failover abilitato
CREATE PUBLICATION my_pub FOR TABLE orders, customers;

-- Sul subscriber: specificare l'opzione failover
CREATE SUBSCRIPTION my_sub
    CONNECTION 'host=primary dbname=mydb user=replicator'
    PUBLICATION my_pub
    WITH (failover = true);

-- Lo slot di replica logica sul primario viene marcato come "failover slot"
-- Lo standby fisico sincronizza automaticamente la posizione dello slot

-- Verificare la sincronizzazione degli slot sullo standby
SELECT slot_name, plugin, confirmed_flush_lsn, failover
FROM pg_replication_slots;
```

**pg_createsubscriber — conversione standby in subscriber:**

Questo nuovo strumento permette di convertire una replica fisica (standby) in un
subscriber logico senza dover ricostruire i dati. È utile per migrazioni graduali
da replica fisica a replica logica, o per creare subscriber su database di grandi
dimensioni senza il costo iniziale della copia completa.

```bash
# Convertire uno standby fisico in subscriber logico
# Lo standby deve essere fermato prima dell'operazione
pg_createsubscriber \
    --pgdata /var/lib/postgresql/17/standby_data \
    --publisher-server "host=primary port=5432 dbname=mydb user=replicator" \
    --publication my_pub \
    --subscription my_sub

# Dopo la conversione, avviare il server:
# Il nodo è ora un subscriber logico indipendente
# Può avere indici, trigger e schemi diversi dal publisher
pg_ctlcluster 17 standby start
```

**Standby come publisher:**

PostgreSQL 17 permette a uno standby fisico di fungere da publisher per subscriber
logici. Questo scarica il carico della replica logica dal primario allo standby,
una configurazione particolarmente utile in cluster con molti subscriber.

**Supporto hash index nella replica logica:**

Nelle versioni precedenti, le tabelle con soli hash index (senza primary key o
REPLICA IDENTITY FULL) non potevano essere replicate logicamente per operazioni
UPDATE e DELETE. PostgreSQL 17 aggiunge il supporto per hash index come
identificatore di riga nella replica logica.

```sql
-- Usare un hash index come replica identity
CREATE TABLE sensor_data (
    sensor_id TEXT NOT NULL,
    reading DOUBLE PRECISION,
    ts TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON sensor_data USING hash (sensor_id);
ALTER TABLE sensor_data REPLICA IDENTITY USING INDEX sensor_data_sensor_id_idx;
-- Ora UPDATE e DELETE su questa tabella vengono replicati correttamente
```

#### Failover

```bash
# === PROMUOVERE UNA REPLICA A PRIMARIO ===

# Metodo 1: pg_ctl
sudo -u postgres pg_ctlcluster 16 main promote

# Metodo 2: SQL (PG 12+)
SELECT pg_promote();

# Dopo la promozione:
# - La replica diventa read-write
# - Le altre repliche devono essere riconfigurate per puntare al nuovo primario
# - Aggiornare primary_conninfo nelle altre repliche
# - Aggiornare la configurazione dell'applicazione (connection string)

# === FAILOVER AUTOMATICO ===
# Strumenti consigliati:
# - Patroni (etcd/Consul + PostgreSQL) — il più diffuso
# - repmgr — più semplice, meno robusto
# - pg_auto_failover — soluzione ufficiale Citus/Microsoft

# Esempio Patroni (concetto):
# 1. Patroni monitora il primario
# 2. Se il primario non risponde, elegge una replica
# 3. La replica viene promossa
# 4. Le altre repliche si riconfigurano
# 5. VIP o DNS aggiornato per puntare al nuovo primario
```

### Sicurezza PostgreSQL

#### SSL/TLS

```bash
# === ABILITARE SSL ===
# postgresql.conf:
ssl = on
ssl_cert_file = '/etc/postgresql/16/main/server.crt'
ssl_key_file = '/etc/postgresql/16/main/server.key'
ssl_ca_file = '/etc/postgresql/16/main/ca.crt'         # Per autenticazione client
ssl_min_protocol_version = 'TLSv1.2'

# Generare certificati self-signed (solo per test):
openssl req -new -x509 -days 365 -nodes \
    -out /etc/postgresql/16/main/server.crt \
    -keyout /etc/postgresql/16/main/server.key \
    -subj "/CN=db.example.com"
chmod 600 /etc/postgresql/16/main/server.key
chown postgres:postgres /etc/postgresql/16/main/server.*

# pg_hba.conf: forzare SSL per connessioni remote
hostssl all all 0.0.0.0/0 scram-sha-256
hostnossl all all 0.0.0.0/0 reject

# Verificare connessione SSL:
psql "sslmode=verify-full host=db.example.com dbname=mydb user=app_user"
SELECT pg_ssl.pid, pg_ssl.ssl, pg_ssl.version
FROM pg_stat_ssl AS pg_ssl
JOIN pg_stat_activity ON pg_ssl.pid = pg_stat_activity.pid;
```

#### Row-Level Security (RLS)

Consente di limitare l'accesso a livello di riga in base all'utente connesso. 

```sql
-- Abilitare RLS sulla tabella
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: ogni utente vede solo i propri documenti
CREATE POLICY user_documents ON documents
    FOR ALL
    USING (owner = current_user);

-- Policy: gli admin vedono tutto
CREATE POLICY admin_all ON documents
    FOR ALL
    TO admin_role
    USING (true);

-- Policy separata per SELECT e INSERT
CREATE POLICY select_own ON documents
    FOR SELECT
    USING (owner = current_user OR is_public = true);

CREATE POLICY insert_own ON documents
    FOR INSERT
    WITH CHECK (owner = current_user);

-- Policy basata su tenant (multi-tenant)
CREATE POLICY tenant_isolation ON orders
    FOR ALL
    USING (tenant_id = current_setting('app.tenant_id')::int);

-- L'applicazione imposta il tenant per ogni connessione:
SET app.tenant_id = '42';

-- Verificare policy attive
SELECT * FROM pg_policies WHERE tablename = 'documents';

-- ATTENZIONE: il proprietario della tabella (OWNER) bypassa RLS di default!
-- Per forzare anche sul proprietario:
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
```

#### Audit Logging con pgAudit

```bash
# Installazione
sudo apt install postgresql-16-pgaudit

# postgresql.conf
shared_preload_libraries = 'pgaudit'     # Richiede restart
pgaudit.log = 'write, ddl'              # Log scritture e DDL
pgaudit.log_catalog = off                # Non loggare accessi al catalogo
pgaudit.log_level = 'log'
pgaudit.log_parameter = on               # Logga i parametri delle query
pgaudit.log_statement_once = on

# Per database specifico:
ALTER DATABASE mydb SET pgaudit.log = 'all';

# Per ruolo specifico:
ALTER ROLE audited_user SET pgaudit.log = 'all';

# Classi di log disponibili:
# read    — SELECT e COPY TO
# write   — INSERT, UPDATE, DELETE, TRUNCATE, COPY FROM
# function — chiamate a funzioni
# role    — GRANT, REVOKE, CREATE/ALTER/DROP ROLE
# ddl     — CREATE, ALTER, DROP (oggetti non-role)
# misc    — DISCARD, FETCH, CHECKPOINT, VACUUM
# all     — tutto
```

### Monitoring PostgreSQL

```sql
-- === QUERY ATTIVE ===
SELECT pid, usename, datname, state, wait_event_type, wait_event,
       now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- Query bloccate (in attesa di lock)
SELECT blocked.pid AS blocked_pid, blocked.query AS blocked_query,
       blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_stat_activity AS blocked
JOIN pg_locks AS blocked_locks ON blocked.pid = blocked_locks.pid
JOIN pg_locks AS blocking_locks ON blocked_locks.locktype = blocking_locks.locktype
    AND blocked_locks.relation = blocking_locks.relation
    AND blocked_locks.pid != blocking_locks.pid
JOIN pg_stat_activity AS blocking ON blocking_locks.pid = blocking.pid
WHERE NOT blocked_locks.granted;

-- Terminare una query
SELECT pg_cancel_backend(pid);            -- Gentile (annulla solo la query)
SELECT pg_terminate_backend(pid);         -- Forzato (chiude la connessione)

-- === DIMENSIONI ===
-- Database
SELECT datname, pg_size_pretty(pg_database_size(datname))
FROM pg_database ORDER BY pg_database_size(datname) DESC;

-- Tabelle (con indici)
SELECT schemaname, relname,
       pg_size_pretty(pg_total_relation_size(relid)) AS total,
       pg_size_pretty(pg_relation_size(relid)) AS table_only,
       pg_size_pretty(pg_indexes_size(relid)) AS indexes
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- === CONNESSIONI ===
SELECT count(*) AS total,
       count(*) FILTER (WHERE state = 'active') AS active,
       count(*) FILTER (WHERE state = 'idle') AS idle,
       count(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_tx
FROM pg_stat_activity;

-- Connessioni per database e utente
SELECT datname, usename, count(*) FROM pg_stat_activity GROUP BY datname, usename;

-- === CACHE HIT RATIO ===
-- Deve essere > 99% per un database ben tunato
SELECT
    sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) AS table_hit_ratio,
    sum(idx_blks_hit) / NULLIF(sum(idx_blks_hit) + sum(idx_blks_read), 0) AS index_hit_ratio
FROM pg_statio_user_tables;

-- === STATO REPLICA ===
-- Sul primario:
SELECT application_name, client_addr, state,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes,
       replay_lag
FROM pg_stat_replication;

-- === PROMETHEUS EXPORTER ===
# postgres_exporter: https://github.com/prometheus-community/postgres_exporter
# Installazione:
wget https://github.com/prometheus-community/postgres_exporter/releases/download/v0.16.0/postgres_exporter-0.16.0.linux-amd64.tar.gz
tar xzf postgres_exporter-*.tar.gz

# Avvio:
export DATA_SOURCE_NAME="postgresql://monitor:password@localhost:5432/postgres?sslmode=disable"
./postgres_exporter --web.listen-address=:9187

# Metriche esposte su http://localhost:9187/metrics
# Integrare con Prometheus + Grafana (dashboard ID: 9628)
```

#### pg_stat_io e observability avanzata (PostgreSQL 16+)

`pg_stat_io` è una vista introdotta in PostgreSQL 16 che fornisce statistiche I/O
disaggregate per backend type, I/O context e I/O object. Prima di questa vista, l'unico
modo per capire chi generava I/O era incrociare `pg_stat_bgwriter`, `pg_stat_wal` e
strumenti OS come `iostat`. Ora tutto è centralizzato.

```sql
-- === pg_stat_io: panoramica I/O per tipo di backend ===
SELECT
    backend_type,
    io_object,
    io_context,
    reads,
    read_time,                                -- ms totali in read (track_io_timing = on)
    writes,
    write_time,
    extends,                                  -- nuove pagine allocate
    fsyncs,
    fsync_time
FROM pg_stat_io
WHERE reads > 0 OR writes > 0
ORDER BY reads + writes DESC;

-- Backend types includono: client backend, autovacuum worker,
-- background writer, checkpointer, WAL sender, startup (recovery)

-- === RAPPORTO CACHE HIT I/O ===
-- Misurare quanto I/O fisico fanno i backend client
SELECT
    backend_type,
    io_context,
    hits,
    reads,
    CASE WHEN hits + reads > 0
         THEN round(100.0 * hits / (hits + reads), 2)
         ELSE 0
    END AS cache_hit_pct
FROM pg_stat_io
WHERE backend_type = 'client backend'
  AND io_object = 'relation';
-- Un cache_hit_pct sotto 95% indica shared_buffers troppo piccoli
-- o working set che non sta in memoria

-- === MONITORARE CHECKPOINT I/O ===
SELECT
    reads, writes, fsyncs,
    round(write_time::numeric / 1000, 2) AS write_time_sec,
    round(fsync_time::numeric / 1000, 2) AS fsync_time_sec
FROM pg_stat_io
WHERE backend_type = 'checkpointer';
-- Se fsync_time è alto, considerare checkpoint_completion_target = 0.9
-- e spostare WAL/data su storage separati
```

**pg_stat_monitor vs pg_stat_statements:**

`pg_stat_statements` (inclusa nelle contrib) aggrega statistiche per query normalizzata,
ma perde la distribuzione temporale: una query che era veloce ieri e lenta oggi mostra
solo la media complessiva. `pg_stat_monitor` (Percona) risolve questo con **time buckets**.

```sql
-- === pg_stat_monitor: statistiche con bucket temporali ===
-- Installazione:
-- sudo apt install percona-pg-stat-monitor16
-- O compilare da sorgente: https://github.com/percona/pg_stat_monitor

-- postgresql.conf:
-- shared_preload_libraries = 'pg_stat_monitor'
-- pg_stat_monitor.pgsm_bucket_time = 300   -- bucket di 5 minuti

CREATE EXTENSION pg_stat_monitor;

-- Query per bucket temporale
SELECT
    bucket_start_time,
    query,
    calls,
    round(mean_exec_time::numeric, 2) AS avg_ms,
    round(max_exec_time::numeric, 2) AS max_ms,
    rows
FROM pg_stat_monitor
WHERE bucket_start_time > now() - interval '1 hour'
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Top query per blocchi I/O nell'ultimo bucket
SELECT
    query,
    calls,
    shared_blks_read,
    shared_blks_hit,
    round(100.0 * shared_blks_hit /
          nullif(shared_blks_hit + shared_blks_read, 0), 1) AS hit_ratio
FROM pg_stat_monitor
WHERE bucket_start_time = (SELECT max(bucket_start_time) FROM pg_stat_monitor)
ORDER BY shared_blks_read DESC
LIMIT 10;
```

**Integrazione con Percona Monitoring and Management (PMM):**

PMM 3 include cinque dashboard PostgreSQL dedicati che visualizzano i dati di
pg_stat_monitor: Query Analytics con drill-down temporale, distribuzione della latenza
per percentile, e correlazione tra query lente e I/O del sistema operativo.
L'agent `pmm-agent` raccoglie automaticamente le metriche se pg_stat_monitor è caricato.

**Ricetta di tuning basata sull'observability:**

```
1. Abilitare track_io_timing = on in postgresql.conf
2. Installare pg_stat_monitor (o almeno pg_stat_statements)
3. Controllare pg_stat_io: se cache_hit_pct < 95%, aumentare shared_buffers
4. Controllare pg_stat_io checkpointer: se fsync_time > 5s, tuning checkpoint
5. Controllare pg_stat_monitor: query con max_exec_time >> avg indicano lock contention
6. shared_buffers: 25-40% della RAM totale
7. effective_cache_size: 50-75% della RAM totale
8. work_mem: RAM_disponibile / max_connections / 4 (per sort e hash)
   Attenzione: work_mem × max_connections non deve superare il 50% della RAM
9. maintenance_work_mem: 512 MB - 2 GB (per VACUUM, CREATE INDEX)
```

---

## MySQL/MariaDB

### Installazione e hardening

```bash
# Installazione MariaDB (consigliato su Debian/Ubuntu)
sudo apt install mariadb-server mariadb-client

# Installazione MySQL (da repository ufficiale Oracle)
# sudo apt install mysql-server mysql-client

# Installazione su RHEL/Fedora
sudo dnf install mariadb-server
sudo systemctl enable --now mariadb

# Hardening iniziale (OBBLIGATORIO dopo installazione)
sudo mysql_secure_installation
# - Imposta password root
# - Rimuovi utenti anonimi
# - Disabilita login root remoto
# - Rimuovi database di test
# - Ricarica tabelle privilegi

# File principali
/etc/mysql/mariadb.conf.d/              # Configurazione (Debian)
/etc/mysql/my.cnf                       # File principale (include i .conf.d)
/etc/my.cnf                             # RHEL/Fedora
/var/lib/mysql/                         # Data directory
/var/log/mysql/                         # Log
/var/run/mysqld/mysqld.sock             # Socket Unix

# Stato
sudo systemctl status mariadb
sudo systemctl start mariadb
sudo systemctl restart mariadb
```

### Configurazione my.cnf

```ini
# /etc/mysql/mariadb.conf.d/50-server.cnf
# oppure /etc/my.cnf.d/server.cnf (RHEL)

[mysqld]
# === RETE ===
bind-address = 0.0.0.0
port = 3306
max_connections = 200
max_connect_errors = 100000
wait_timeout = 600                        # Timeout connessioni idle (secondi)
interactive_timeout = 600

# === InnoDB (engine predefinito e raccomandato) ===
default_storage_engine = InnoDB
innodb_buffer_pool_size = 8G              # 50-70% della RAM dedicata a MySQL
innodb_buffer_pool_instances = 8          # 1 istanza per GB (max 64)
innodb_log_file_size = 1G                # Dimensione redo log (impatta recovery time)
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 1       # 1 = sicuro (ACID), 2 = più veloce
innodb_flush_method = O_DIRECT           # Evita double buffering con OS cache
innodb_io_capacity = 2000                # IOPS disponibili (SSD)
innodb_io_capacity_max = 4000
innodb_file_per_table = ON               # Ogni tabella in un file .ibd separato
innodb_open_files = 4000
innodb_read_io_threads = 8
innodb_write_io_threads = 8

# === QUERY CACHE (solo MariaDB, rimossa in MySQL 8) ===
# query_cache_type = 0                   # Disabilitata in ambienti write-heavy
# query_cache_size = 0

# === TEMP TABLES ===
tmp_table_size = 256M
max_heap_table_size = 256M

# === SORT E JOIN ===
sort_buffer_size = 4M
join_buffer_size = 4M
read_buffer_size = 2M
read_rnd_buffer_size = 8M

# === LOGGING ===
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1                       # Log query > 1 secondo
log_queries_not_using_indexes = 1         # Log query senza indici
log_slow_admin_statements = 1

# === GENERAL LOG (solo per debug, MAI in produzione permanente) ===
# general_log = 1
# general_log_file = /var/log/mysql/general.log

# === BINARY LOG (necessario per replica e PITR) ===
log_bin = /var/log/mysql/mysql-bin
binlog_format = ROW                       # ROW e il più sicuro per replica
binlog_expire_logs_seconds = 604800       # 7 giorni
max_binlog_size = 256M
sync_binlog = 1                           # Sync binlog ad ogni commit (sicuro)

# === CHARACTER SET ===
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
character-set-client-handshake = FALSE

# === SICUREZZA ===
local_infile = 0                          # Disabilita LOAD DATA LOCAL
symbolic-links = 0
sql_mode = STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION,ERROR_FOR_DIVISION_BY_ZERO
```

### InnoDB vs MyISAM

| Caratteristica | InnoDB | MyISAM |
|---------------|--------|--------|
| Transazioni ACID | Si | No |
| Row-level locking | Si | Solo table-level |
| Foreign keys | Si | No |
| Crash recovery | Automatica (redo log) | Manuale (myisamchk) |
| MVCC | Si | No |
| Full-text search | Si (da MySQL 5.6) | Si |
| Compressione | Si (ROW_FORMAT=COMPRESSED) | Si (myisampack) |
| Performance INSERT | Buona | Molto buona per bulk |
| Performance SELECT | Buona (con indici) | Veloce per read-only |
| Spazio disco | Maggiore (indice cluster) | Minore |
| COUNT(*) senza WHERE | Lento (scan) | Istantaneo (metadati) |
| Hot backup | Si (Percona XtraBackup) | No (lock table) |

**Raccomandazione:** usare **sempre InnoDB** per nuovi progetti. MyISAM e legacy e non garantisce integrita dei dati in caso di crash.

### MariaDB 11 vs MySQL 8.4: punti di divergenza

MariaDB e MySQL condividono un'origine comune (MySQL 5.5), ma dal 2012 i due progetti
hanno preso strade sempre più divergenti. Con MariaDB 11.x e MySQL 8.4, la compatibilità
non è più garantita e la migrazione tra i due richiede attenzione.

**Differenze architetturali fondamentali:**

| Area | MySQL 8.4 | MariaDB 11.x |
|------|-----------|-------------|
| Data dictionary | InnoDB DD (transazionale, .sdi) | File .frm tradizionali |
| Sistema di autenticazione | `caching_sha2_password` (default) | `mysql_native_password` (default) |
| JSON | Tipo nativo binario, funzioni JSON estese | Alias per LONGTEXT, validazione a runtime |
| CTE ricorsive | Supporto completo | Supporto completo |
| Window functions | Supporto completo | Supporto completo |
| LATERAL derived tables | Sì (da 8.0.14) | Non supportato |
| Invisible columns | Sì | Sì (implementazione indipendente) |
| Collation | ~266 collation | ~506 collation |
| Motore colonnare | No (HeatWave su cloud) | ColumnStore (integrato) |
| Group replication | MySQL InnoDB Cluster | Galera Cluster (più maturo) |
| Query optimizer | Cost-based, histograms | Cost-based, histograms, engine-independent stats |

**Incompatibilità da conoscere nella migrazione:**

```sql
-- === AUTENTICAZIONE ===
-- MySQL 8.4 usa caching_sha2_password di default
-- Client MariaDB non supportano SHA256 nativamente
-- Soluzione su MySQL: creare utenti con plugin compatibile
CREATE USER 'app'@'%' IDENTIFIED WITH mysql_native_password BY 'password';

-- === JSON ===
-- Su MySQL: tipo binario nativo, validazione a INSERT
CREATE TABLE t (data JSON);
INSERT INTO t VALUES ('{"a":1}');             -- OK
INSERT INTO t VALUES ('not json');             -- Error su MySQL

-- Su MariaDB: LONGTEXT con alias, validazione solo con CHECK
CREATE TABLE t (data JSON CHECK (JSON_VALID(data)));
INSERT INTO t VALUES ('not json');             -- Error solo se c'è CHECK

-- === DATA DICTIONARY ===
-- MySQL 8.4: informazioni di schema in tabelle InnoDB transazionali
-- DDL atomico: ALTER TABLE è tutto-o-niente
-- MariaDB 11: ancora file .frm sul filesystem
-- DDL non atomico: crash durante ALTER può lasciare stato inconsistente

-- === SYSTEM VERSIONING (solo MariaDB) ===
-- MariaDB supporta tabelle con versioning temporale integrato
CREATE TABLE prezzi (
    id INT PRIMARY KEY,
    prodotto VARCHAR(100),
    prezzo DECIMAL(10,2)
) WITH SYSTEM VERSIONING;

-- Query su dati storici
SELECT * FROM prezzi FOR SYSTEM_TIME AS OF '2025-01-01';
SELECT * FROM prezzi FOR SYSTEM_TIME BETWEEN '2025-01-01' AND '2025-06-01';
-- Questa funzionalità non esiste in MySQL
```

**Linee guida per la scelta:**
- **MySQL 8.4:** quando si usa l'ecosistema Oracle (MySQL Shell, Router, InnoDB Cluster),
  oppure quando servono DDL atomici, JSON nativo ad alte prestazioni, o compatibilità
  con servizi cloud specifici (RDS, Cloud SQL)
- **MariaDB 11.x:** quando serve un progetto completamente open-source (GPLv2),
  Galera Cluster per multi-master, ColumnStore per analytics, system versioning,
  o un numero maggiore di collation per internazionalizzazione avanzata
- **Migrazione:** non fare mai un upgrade in-place tra i due. Usare sempre `mysqldump`
  o replica logica, testando la compatibilità delle query e dei plugin di autenticazione

```sql
-- Verificare l'engine di ogni tabella
SELECT table_name, engine, table_rows, data_length, index_length
FROM information_schema.tables
WHERE table_schema = 'mydb';

-- Convertire una tabella MyISAM a InnoDB
ALTER TABLE old_table ENGINE = InnoDB;

-- Verificare variabili InnoDB
SHOW VARIABLES LIKE 'innodb%';
SHOW ENGINE INNODB STATUS\G
```

### Utenti e privilegi MySQL

```sql
-- === CREAZIONE UTENTI ===
CREATE USER 'app_user'@'10.0.0.%' IDENTIFIED BY 'strong_password';
CREATE USER 'admin_user'@'localhost' IDENTIFIED BY 'admin_password';
CREATE USER 'readonly'@'%' IDENTIFIED BY 'readonly_password';

-- === PRIVILEGI GRANULARI ===
-- Lettura su tutto il database
GRANT SELECT ON mydb.* TO 'readonly'@'%';

-- Lettura e scrittura
GRANT SELECT, INSERT, UPDATE, DELETE ON mydb.* TO 'app_user'@'10.0.0.%';

-- Tutti i privilegi su un database
GRANT ALL PRIVILEGES ON mydb.* TO 'admin_user'@'localhost';

-- Privilegi su tabella specifica
GRANT SELECT, INSERT ON mydb.orders TO 'app_user'@'10.0.0.%';

-- Privilegi su colonne specifiche
GRANT SELECT (id, name, email) ON mydb.users TO 'report_user'@'%';

-- Privilegi per replica
GRANT REPLICATION SLAVE ON *.* TO 'replicator'@'10.0.0.%';

-- Applicare le modifiche
FLUSH PRIVILEGES;

-- === GESTIONE ===
-- Mostrare privilegi
SHOW GRANTS FOR 'app_user'@'10.0.0.%';

-- Revocare privilegi
REVOKE DELETE ON mydb.* FROM 'app_user'@'10.0.0.%';

-- Cambiare password
ALTER USER 'app_user'@'10.0.0.%' IDENTIFIED BY 'new_password';

-- Eliminare utente
DROP USER 'app_user'@'10.0.0.%';

-- Utenti attivi
SELECT user, host, db, command, time, state FROM information_schema.processlist;

-- === BEST PRACTICES PRIVILEGI ===
-- 1. Mai usare GRANT ALL ON *.*
-- 2. Creare un utente per ogni applicazione
-- 3. Limitare l'host (mai '%' se possibile)
-- 4. Rimuovere l'utente root remoto
-- 5. Usare nomi utente descrittivi (app_name_role)
```

### Replica MySQL

#### Master-Slave (Source-Replica)

```bash
# === SUL MASTER (SOURCE) ===
# my.cnf:
[mysqld]
server-id = 1
log_bin = /var/log/mysql/mysql-bin
binlog_format = ROW
binlog_do_db = mydb                       # Opzionale: replica solo questo database
gtid_mode = ON                            # Raccomandato: Global Transaction ID
enforce_gtid_consistency = ON

# Creare l'utente di replica
CREATE USER 'replicator'@'10.0.0.%' IDENTIFIED BY 'rep_password';
GRANT REPLICATION SLAVE ON *.* TO 'replicator'@'10.0.0.%';
FLUSH PRIVILEGES;

# Ottenere posizione binlog (con GTID non serve)
SHOW MASTER STATUS;

# === SULLA REPLICA (SLAVE) ===
# my.cnf:
[mysqld]
server-id = 2
relay_log = /var/log/mysql/relay-bin
read_only = ON                            # Impedisce scritture accidentali
super_read_only = ON                      # Anche per utenti con SUPER

# Configurare la replica
CHANGE MASTER TO
    MASTER_HOST = '10.0.0.1',
    MASTER_USER = 'replicator',
    MASTER_PASSWORD = 'rep_password',
    MASTER_AUTO_POSITION = 1;             # Usa GTID

START SLAVE;

# Verificare stato
SHOW SLAVE STATUS\G
# Campi importanti:
# Slave_IO_Running: Yes
# Slave_SQL_Running: Yes
# Seconds_Behind_Master: 0
# Last_Error: (vuoto)
```

#### Group Replication

MySQL Group Replication fornisce replica multi-master con consenso distribuito (Paxos).

```bash
# my.cnf (su ogni nodo):
[mysqld]
server-id = 1                             # Unico per ogni nodo
gtid_mode = ON
enforce_gtid_consistency = ON
binlog_checksum = NONE

# Group Replication
plugin_load_add = 'group_replication.so'
group_replication_group_name = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
group_replication_start_on_boot = OFF
group_replication_local_address = "10.0.0.1:33061"
group_replication_group_seeds = "10.0.0.1:33061,10.0.0.2:33061,10.0.0.3:33061"
group_replication_single_primary_mode = ON     # Un solo nodo scrive
# group_replication_single_primary_mode = OFF  # Multi-primary (tutti scrivono)

# Avvio (sul primo nodo — bootstrap):
SET GLOBAL group_replication_bootstrap_group = ON;
START GROUP_REPLICATION;
SET GLOBAL group_replication_bootstrap_group = OFF;

# Sugli altri nodi:
START GROUP_REPLICATION;

# Verifica:
SELECT * FROM performance_schema.replication_group_members;
SELECT * FROM performance_schema.replication_group_member_stats;
```

#### ProxySQL

ProxySQL è un proxy SQL ad alte prestazioni per MySQL. Gestisce connection pooling, query routing, failover.

```bash
# Installazione
sudo apt install proxysql

# File: /etc/proxysql.cnf
# Accesso admin:
mysql -u admin -padmin -h 127.0.0.1 -P 6032

# Aggiungere server backend
INSERT INTO mysql_servers (hostgroup_id, hostname, port, weight)
VALUES (10, '10.0.0.1', 3306, 100),     -- Writer
       (20, '10.0.0.2', 3306, 100),     -- Reader
       (20, '10.0.0.3', 3306, 100);     -- Reader

# Regole di routing
INSERT INTO mysql_query_rules (rule_id, active, match_pattern, destination_hostgroup)
VALUES (1, 1, '^SELECT.*FOR UPDATE', 10),    -- SELECT FOR UPDATE → writer
       (2, 1, '^SELECT', 20);                -- SELECT → reader

# Utenti
INSERT INTO mysql_users (username, password, default_hostgroup)
VALUES ('app_user', 'password', 10);

# Applicare
LOAD MYSQL SERVERS TO RUNTIME;
LOAD MYSQL QUERY RULES TO RUNTIME;
LOAD MYSQL USERS TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
SAVE MYSQL QUERY RULES TO DISK;
SAVE MYSQL USERS TO DISK;

# Le applicazioni si connettono a ProxySQL (porta 6033)
# ProxySQL instrada le query al server appropriato
```

#### Orchestrator

Orchestrator e uno strumento per la gestione della topologià di replica MySQL e il failover automatico.

```bash
# Installazione
wget https://github.com/openark/orchestrator/releases/download/v3.2.6/orchestrator_3.2.6_amd64.deb
sudo dpkg -i orchestrator_*.deb

# Configurazione: /etc/orchestrator.conf.json
# Discovera la topologia:
orchestrator-client -c discover -i master-host:3306

# Visualizza topologia:
orchestrator-client -c topology -i master-host:3306

# Failover manuale:
orchestrator-client -c graceful-master-takeover -i new-master:3306

# Interfaccia web: http://localhost:3000
```

### Backup MySQL

```bash
# === MYSQLDUMP — BACKUP LOGICO ===
# Singolo database
mysqldump -u root -p --single-transaction mydb > backup.sql

# Tutti i database
mysqldump -u root -p --all-databases --single-transaction > all.sql

# Opzioni importanti:
mysqldump -u root -p \
    --single-transaction \                 # Consistente per InnoDB (no lock)
    --routines \                           # Include stored procedure
    --triggers \                           # Include trigger
    --events \                             # Include eventi
    --set-gtid-purged=OFF \               # Per non interferire con replica
    mydb > backup.sql

# Tabelle specifiche
mysqldump -u root -p mydb orders customers > partial.sql

# Solo struttura
mysqldump -u root -p --no-data mydb > schema.sql

# Compresso
mysqldump -u root -p mydb | gzip > backup.sql.gz

# Restore
mysql -u root -p mydb < backup.sql
zcat backup.sql.gz | mysql -u root -p mydb

# === MYSQLBINLOG — PITR ===
# Visualizzare contenuto binlog
mysqlbinlog /var/log/mysql/mysql-bin.000001

# Ripristino point-in-time (dopo restore del dump)
mysqlbinlog --start-datetime="2026-05-22 10:00:00" \
            --stop-datetime="2026-05-22 14:30:00" \
            /var/log/mysql/mysql-bin.000042 | mysql -u root -p

# Con GTID
mysqlbinlog --include-gtids="aaaa-bbbb:1-100" \
            /var/log/mysql/mysql-bin.000042 | mysql -u root -p

# === PERCONA XTRABACKUP — BACKUP FISICO ===
# Installazione
sudo apt install percona-xtrabackup-80   # Per MySQL 8
# oppure
sudo apt install mariadb-backup           # Per MariaDB (mariabackup)

# Backup completo
xtrabackup --backup --target-dir=/backup/full \
    --user=root --password=secret

# Prepare (rende il backup consistente)
xtrabackup --prepare --target-dir=/backup/full

# Backup incrementale
xtrabackup --backup --target-dir=/backup/inc1 \
    --incremental-basedir=/backup/full \
    --user=root --password=secret

# Prepare incrementale
xtrabackup --prepare --apply-log-only --target-dir=/backup/full
xtrabackup --prepare --apply-log-only --target-dir=/backup/full \
    --incremental-dir=/backup/inc1

# Restore (server fermo!)
sudo systemctl stop mysql
xtrabackup --copy-back --target-dir=/backup/full
chown -R mysql:mysql /var/lib/mysql
sudo systemctl start mysql

# === MARIABACKUP (per MariaDB) ===
mariabackup --backup --target-dir=/backup/full -u root -p
mariabackup --prepare --target-dir=/backup/full
# Restore: come xtrabackup
```

### Monitoring MySQL

```sql
-- === PROCESSLIST ===
SHOW PROCESSLIST;
SHOW FULL PROCESSLIST;                    -- Query complete
-- Terminare una query
KILL query_id;
KILL CONNECTION connection_id;

-- === STATO GLOBALE ===
SHOW GLOBAL STATUS LIKE 'Threads%';
SHOW GLOBAL STATUS LIKE 'Connections';
SHOW GLOBAL STATUS LIKE 'Slow_queries';
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool%';

-- Buffer pool hit ratio (deve essere > 99%)
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_read_requests';  -- Letture dalla cache
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_reads';          -- Letture da disco
-- hit_ratio = read_requests / (read_requests + reads)

-- === PERFORMANCE SCHEMA ===
-- Top query per tempo di esecuzione
SELECT DIGEST_TEXT, COUNT_STAR, AVG_TIMER_WAIT/1000000000 AS avg_ms,
       SUM_TIMER_WAIT/1000000000 AS total_ms, SUM_ROWS_EXAMINED, SUM_ROWS_SENT
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;

-- Tabelle con più I/O
SELECT object_schema, object_name,
       count_read, count_write, count_fetch,
       sum_timer_wait/1000000000 AS total_ms
FROM performance_schema.table_io_waits_summary_by_table
ORDER BY sum_timer_wait DESC
LIMIT 10;

-- Lock attivi
SELECT * FROM performance_schema.data_locks;
SELECT * FROM performance_schema.data_lock_waits;

-- === PROMETHEUS EXPORTER ===
# mysqld_exporter: https://github.com/prometheus/mysqld_exporter
# Creare utente monitor:
CREATE USER 'exporter'@'localhost' IDENTIFIED BY 'monitor_password';
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';

# Avvio:
export DATA_SOURCE_NAME="exporter:monitor_password@(localhost:3306)/"
./mysqld_exporter --web.listen-address=:9104
# Dashboard Grafana: ID 7362
```

---

## SQLite

### Casi d'uso

SQLite e un database embedded: non ha un server, il database e un singolo file. Ideale per:

- **Applicazioni desktop e mobile** (ogni app ha il suo DB)
- **Prototipazione rapida** (nessuna configurazione)
- **File di configurazione strutturati** (alternativa a JSON/INI)
- **Testing** (database in-memory per test veloci)
- **Edge computing e IoT** (risorse limitate)
- **Website a basso traffico** (< 100K richieste/giorno)

**NON adatto per:**
- Applicazioni multi-server (nessuna replica nativa)
- Alto volume di scritture concorrenti
- Database > 1 TB
- Accesso remoto via rete

```bash
# Installazione (spesso già presente)
sudo apt install sqlite3 libsqlite3-dev

# Creare/aprire un database
sqlite3 /path/to/database.db

# Database in-memory (per test)
sqlite3 :memory:

# Comandi meta
.databases                                 # Database aperti
.tables                                    # Tabelle
.schema tablename                          # Schema tabella
.mode column                               # Output formattato a colonne
.mode csv                                  # Output CSV
.headers on                                # Mostra intestazioni
.timer on                                  # Mostra tempo di esecuzione
.quit

# Importazione/esportazione
.import --csv data.csv tablename          # Importa CSV
.output result.csv                        # Redirect output
.mode csv
SELECT * FROM tablename;
.output stdout                            # Torna a stdout
```

### Modalita WAL

Write-Ahead Logging (WAL) migliora le prestazioni di lettura concorrente e la resilienza ai crash.

```bash
# Abilitare WAL mode
sqlite3 database.db "PRAGMA journal_mode=WAL;"

# Risultato: il database usa 3 file:
# database.db       — dati principali
# database.db-wal   — write-ahead log
# database.db-shm   — shared memory (indice WAL)

# === VANTAGGI WAL ===
# - Letture non bloccano le scritture
# - Scritture non bloccano le letture
# - Crash recovery più veloce
# - Meno operazioni fsync (più veloce su HDD)

# === SVANTAGGI WAL ===
# - Non funziona su filesystem di rete (NFS)
# - File WAL puo crescere (controllare con PRAGMA wal_checkpoint)
# - Piu lento per workload write-only

# Checkpoint manuale (applica WAL al database)
PRAGMA wal_checkpoint(TRUNCATE);

# Auto-checkpoint (default: ogni 1000 pagine WAL)
PRAGMA wal_autocheckpoint = 1000;

# === ALTRE PRAGMA UTILI ===
PRAGMA busy_timeout = 5000;               -- Attendi 5s se il DB e bloccato
PRAGMA cache_size = -64000;               -- 64 MB di cache (negativo = KB)
PRAGMA foreign_keys = ON;                 -- Abilita foreign key (disabilitate di default!)
PRAGMA synchronous = NORMAL;              -- NORMAL e sicuro con WAL (FULL per paranoia)
PRAGMA temp_store = MEMORY;               -- Tabelle temporanee in RAM
PRAGMA mmap_size = 268435456;             -- Memory-map 256 MB del file
PRAGMA optimize;                          -- Ottimizza statistiche (eseguire periodicamente)
```

#### Tabelle STRICT e configurazione di produzione

A partire da SQLite 3.37 (2021-11), è disponibile la clausola `STRICT` per le tabelle,
che introduce un type enforcement rigido simile ai database server tradizionali.
Senza `STRICT`, SQLite usa type affinity: una colonna `INTEGER` accetta tranquillamente
una stringa, un `REAL` accetta un blob. Questo comportamento flessibile è utile per
prototyping ma pericoloso in produzione.

```sql
-- === TABELLE STRICT ===
-- Tabella con type enforcement (SQLite 3.37+)
CREATE TABLE utenti (
    id    INTEGER PRIMARY KEY,
    nome  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    eta   INTEGER NOT NULL,
    saldo REAL DEFAULT 0.0
) STRICT;

-- Con STRICT, tentare di inserire un tipo errato causa errore:
INSERT INTO utenti (nome, email, eta) VALUES ('Alice', 'alice@ex.com', 'trenta');
-- Error: cannot store TEXT value in INTEGER column utenti.eta

-- Tipi consentiti in tabelle STRICT:
-- INT, INTEGER, REAL, TEXT, BLOB, ANY
-- ANY accetta qualsiasi tipo (opt-out per singola colonna)

-- === SENZA STRICT (comportamento classico) ===
CREATE TABLE legacy (id INTEGER, valore INTEGER);
INSERT INTO legacy VALUES (1, 'non un numero');  -- Nessun errore!
SELECT typeof(valore) FROM legacy;               -- 'text' (non 'integer')
```

**Configurazione di produzione raccomandata per SQLite:**

```sql
-- === RICETTA PRODUZIONE ===
-- Eseguire all'apertura di ogni connessione (non persistono tra sessioni)

PRAGMA journal_mode = WAL;                -- Write-Ahead Logging (fondamentale)
PRAGMA busy_timeout = 5000;               -- 5s di attesa su lock (critico!)
PRAGMA synchronous = NORMAL;              -- Sicuro con WAL, 30-60% p99 in meno
PRAGMA cache_size = -64000;               -- 64 MB di cache
PRAGMA foreign_keys = ON;                 -- Sempre abilitare (default OFF!)
PRAGMA temp_store = MEMORY;               -- Temp tables in RAM
PRAGMA mmap_size = 268435456;             -- Memory-map 256 MB
PRAGMA wal_autocheckpoint = 1000;         -- Checkpoint ogni 1000 pagine (default)

-- Per applicazioni ad alta scrittura:
PRAGMA wal_autocheckpoint = 2000;         -- Riduce frequenza checkpoint
PRAGMA journal_size_limit = 67108864;     -- Limita WAL a 64 MB

-- === VERIFICA CONFIGURAZIONE ===
PRAGMA journal_mode;                      -- Deve restituire 'wal'
PRAGMA integrity_check;                   -- Verifica integrità (periodico)
PRAGMA quick_check;                       -- Versione veloce di integrity_check
```

**Errore comune — `busy_timeout` non impostato:** senza `busy_timeout`, una connessione
che incontra un lock riceve immediatamente `SQLITE_BUSY`. In un'applicazione web con
scritture concorrenti, questo causa errori frequenti. Impostare sempre almeno 3000-5000 ms.

**WAL mode e prestazioni:** la modalità WAL separa lettori e scrittori: i lettori non
bloccano lo scrittore e viceversa. In benchmark reali, la latenza p99 delle letture
scende del 30-60% rispetto al journal_mode DELETE. Lo svantaggio è un file `-wal`
aggiuntivo che può crescere se il checkpoint non avviene regolarmente.

### Accesso concorrente e locking

SQLite ha un modello di locking a 5 livelli:

| Livello | Descrizione |
|---------|------------|
| UNLOCKED | Nessun lock |
| SHARED | Lettura in corso (più lettori simultanei) |
| RESERVED | Pianificazione scrittura (solo uno, lettori ancora permessi) |
| PENDING | Attesa che i lettori finiscano (nuovi lettori bloccati) |
| EXCLUSIVE | Scrittura in corso (nessun altro accesso) |

```
# Con journal_mode=DELETE (default):
# - Un solo scrittore alla volta
# - Scrittore blocca tutti i lettori durante il flush

# Con journal_mode=WAL:
# - Un solo scrittore alla volta
# - Lettori NON bloccati durante la scrittura
# - Scrittore attende solo se WAL checkpoint in corso

# Regole per applicazioni multi-thread:
# 1. Usare WAL mode
# 2. Impostare busy_timeout (5000+ ms)
# 3. Mantenere le transazioni corte
# 4. Non tenere connessioni aperte a lungo in modo inattivo
# 5. Per write-heavy: considerare PostgreSQL
```

### Backup SQLite

```bash
# === METODO 1: .backup (consigliato) ===
# Sicuro anche durante operazioni concurrent
sqlite3 database.db ".backup /path/backup.db"

# === METODO 2: .dump (SQL text) ===
sqlite3 database.db ".dump" > backup.sql
# Restore:
sqlite3 new.db < backup.sql

# === METODO 3: Copia file (con WAL checkpoint prima) ===
sqlite3 database.db "PRAGMA wal_checkpoint(TRUNCATE);"
cp database.db /backup/database.db
# ATTENZIONE: non copiare il file durante una scrittura senza checkpoint!

# === METODO 4: VACUUM INTO (PG 3.27+) ===
sqlite3 database.db "VACUUM INTO '/backup/database_compact.db';"
# Produce una copia compatta e defragmentata

# === VERIFICA INTEGRITA ===
sqlite3 database.db "PRAGMA integrity_check;"
# Risultato atteso: "ok"
```

---

## Redis

### Installazione e configurazione Redis

```bash
# Installazione
sudo apt install redis-server redis-tools

# Su RHEL/Fedora
sudo dnf install redis
sudo systemctl enable --now redis

# File principali
/etc/redis/redis.conf                     # Configurazione
/var/lib/redis/                           # Dati (RDB/AOF)
/var/log/redis/                           # Log
/var/run/redis/redis-server.pid           # PID

# === redis.conf — configurazione sicura ===
bind 127.0.0.1 -::1                       # Solo connessioni locali
# bind 0.0.0.0                            # Tutte le interfacce (per cluster/replica)
protected-mode yes                        # Rifiuta connessioni non locali senza password
requirepass "strong-password-here"
port 6379

# Memoria
maxmemory 4gb                             # Limite memoria
maxmemory-policy allkeys-lru              # Politica di eviction

# Politiche di eviction disponibili:
# noeviction          — Errore su scrittura quando pieno
# allkeys-lru         — Rimuovi la chiave meno usata di recente (consigliato per cache)
# volatile-lru        — LRU solo tra chiavi con TTL
# allkeys-random      — Rimuovi chiave casuale
# volatile-random     — Casuale tra chiavi con TTL
# volatile-ttl        — Rimuovi chiave con TTL più vicino
# allkeys-lfu         — Rimuovi la chiave meno frequentemente usata
# volatile-lfu        — LFU solo tra chiavi con TTL

# Timeout
timeout 300                               # Chiudi connessioni idle dopo 5 min
tcp-keepalive 60

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Sicurezza
rename-command FLUSHALL ""                # Disabilita comandi pericolosi
rename-command FLUSHDB ""
rename-command CONFIG ""                  # Oppure rinominare con nome segreto
rename-command DEBUG ""
rename-command KEYS ""                    # KEYS e O(n), pericoloso in produzione

# Avvio
sudo systemctl restart redis
redis-cli -a 'strong-password-here' ping  # Deve rispondere: PONG
```

### ACL, Functions e il fork Valkey

#### Sistema ACL (Redis 6+)

A partire da Redis 6, il vecchio modello `requirepass` con password unica è stato sostituito
da un sistema ACL granulare che permette di definire utenti con permessi specifici
su comandi, chiavi e canali Pub/Sub.

```bash
# === GESTIONE UTENTI ACL ===
# Creare un utente con permessi limitati
ACL SETUSER app_cache on >secure-pass-2024 ~cache:* +GET +SET +DEL +TTL +EXPIRE
# on            → utente attivo
# >password     → password (può averne più di una)
# ~cache:*      → accesso solo a chiavi che matchano il pattern
# +GET +SET ... → comandi consentiti (whitelist)

# Utente read-only per monitoring
ACL SETUSER monitor_ro on >mon-pass ~* +INFO +DBSIZE +SLOWLOG +CLIENT +PING -@dangerous

# Visualizzare tutti gli utenti
ACL LIST

# Dettaglio singolo utente
ACL GETUSER app_cache

# Salvare ACL su file (persistenza tra riavvii)
ACL SAVE

# Ricaricare da file
ACL LOAD

# Verificare permessi di un utente su un comando
ACL DRYRUN app_cache GET cache:session:42    # OK
ACL DRYRUN app_cache FLUSHDB                  # ERR

# === CATEGORIE DI COMANDI ===
# Redis raggruppa i comandi in categorie per semplificare i permessi
ACL CAT                                       # Lista tutte le categorie
ACL CAT dangerous                             # Comandi nella categoria "dangerous"

# Esempio: utente con accesso a tutto tranne comandi pericolosi
ACL SETUSER app_full on >pass ~* +@all -@dangerous -@admin

# === FILE ACL ESTERNO ===
# In redis.conf:
# aclfile /etc/redis/users.acl
#
# Formato del file users.acl:
# user default on nopass ~* +@all
# user app_cache on >hashed-pass ~cache:* +@read +@write -@admin
# user replication on >repl-pass +PSYNC +REPLCONF +PING
```

#### Redis Functions (Redis 7+)

Le Functions sostituiscono il vecchio EVAL/Lua scripting con un modello più strutturato.
Le funzioni sono registrate nel server con un nome, persistono tra riavvii, e vengono
replicate automaticamente alle repliche.

```bash
# === REGISTRAZIONE DI UNA LIBRERIA ===
# Le funzioni sono raggruppate in librerie scritte in Lua
FUNCTION LOAD "#!lua name=mylib\nredis.register_function('rate_check',
  function(keys, args)
    local current = redis.call('INCR', keys[1])
    if current == 1 then
      redis.call('EXPIRE', keys[1], tonumber(args[1]))
    end
    if current > tonumber(args[2]) then
      return 0
    end
    return 1
  end
)"

# Invocare la funzione
FCALL rate_check 1 ratelimit:user:42 60 100
# → 1 (permesso) o 0 (rate limit superato)

# Listar le librerie caricate
FUNCTION LIST

# Dump e restore (per migrazione)
FUNCTION DUMP
FUNCTION RESTORE <serialized-data>

# Eliminare una libreria
FUNCTION DELETE mylib
```

**Vantaggi rispetto a EVAL:**
- Le funzioni sono persistenti e replicate (EVAL richiede re-invio ad ogni chiamata)
- Namespace con librerie evita collisioni
- Supporto futuro per linguaggi oltre Lua (engine pluggabili)
- Visibilità nel SLOWLOG con nome della funzione, non hash dello script

#### Il fork Valkey

Nel marzo 2024, Redis Ltd. ha cambiato la licenza da BSD a una dual-license
SSPL/RSALv2, rendendo Redis non più open-source secondo la definizione OSI.
La comunità ha risposto creando **Valkey**, un fork ospitato dalla Linux Foundation,
mantenuto da contributori di AWS, Google, Oracle, Ericsson e altri.

**Stato attuale (2025-2026):**

| Aspetto | Redis 8.0 (AGPL) | Valkey 8.1+ |
|---------|-------------------|-------------|
| Licenza | AGPL v3 (dal 2025) | BSD-3-Clause |
| Compatibilità | API originale | Drop-in replacement |
| Nuove funzionalità | Vector sets, JSON nativo | RDMA, I/O threading migliorato |
| Performance | Baseline | 8% throughput in più, 22% P99 migliore, 20% meno RAM |
| Distribuzione | Pacchetti ufficiali | Ubuntu 26.04, Debian 13, Arch, Alpine (default) |
| Supporto cloud | Redis Cloud | AWS ElastiCache, Aiven, Upstash |

**Migrazione da Redis a Valkey:**

```bash
# Su Debian/Ubuntu (quando disponibile nei repository)
sudo apt install valkey-server valkey-cli

# Valkey usa gli stessi file di configurazione e protocollo
# Basta sostituire il binario e riavviare
sudo systemctl stop redis
sudo systemctl start valkey

# Verifica compatibilità
valkey-cli INFO server | grep valkey_version

# Le ACL, le Functions e la persistenza RDB/AOF sono
# completamente compatibili — nessuna migrazione dati necessaria
```

**Quando scegliere Valkey:** quando serve una soluzione completamente open-source,
oppure in ambienti dove la licenza AGPL/SSPL crea problemi legali (SaaS, embedded,
distribuzione OEM). Per workload standard, Valkey è un drop-in replacement trasparente.

### Tipi di dato Redis

Redis supporta 5 tipi di dato principali, ciascuno con comandi dedicati:

```bash
# === STRING ===
# Caso d'uso: caching, contatori, sessioni, lock distribuiti
SET user:42:name "Alice" EX 3600          # Con scadenza 1 ora
GET user:42:name
MSET key1 "val1" key2 "val2"             # Set multiplo
MGET key1 key2                           # Get multiplo
INCR page:views                          # Incremento atomico
INCRBY page:views 10
DECR stock:item:99
APPEND log:entry " new data"
STRLEN user:42:name
SETNX lock:resource "owner"              # SET if Not eXists (lock)
SET lock:resource "owner" NX EX 30       # Lock con scadenza

# === LIST ===
# Caso d'uso: code (queue), timeline, log recenti
LPUSH queue:emails "msg1" "msg2"         # Inserisci a sinistra
RPUSH queue:emails "msg3"                # Inserisci a destra
LPOP queue:emails                        # Estrai da sinistra (FIFO se push dx, pop sx)
RPOP queue:emails                        # Estrai da destra
BRPOP queue:emails 30                    # Pop bloccante (attendi fino a 30s)
LRANGE queue:emails 0 -1                 # Tutti gli elementi
LLEN queue:emails                        # Lunghezza
LTRIM recent:logs 0 99                   # Mantieni solo i primi 100 elementi

# === SET ===
# Caso d'uso: tag, like unici, relazioni, filtraggio
SADD user:42:tags "linux" "database" "python"
SMEMBERS user:42:tags                    # Tutti gli elementi
SISMEMBER user:42:tags "linux"           # Appartenenza
SCARD user:42:tags                       # Cardinalita
SINTER user:42:tags user:99:tags         # Intersezione
SUNION user:42:tags user:99:tags         # Unione
SDIFF user:42:tags user:99:tags          # Differenza
SRANDMEMBER user:42:tags 2              # 2 elementi casuali
SREM user:42:tags "python"              # Rimuovi

# === HASH ===
# Caso d'uso: oggetti strutturati, profili utente, configurazioni
HSET user:42 name "Alice" age 30 city "Roma"
HGET user:42 name
HGETALL user:42                          # Tutti i campi
HMGET user:42 name age                   # Campi multipli
HINCRBY user:42 age 1                    # Incremento campo numerico
HDEL user:42 city
HEXISTS user:42 name
HLEN user:42

# === SORTED SET (ZSET) ===
# Caso d'uso: classifiche, timeline ordinate, rate limiting, priority queue
ZADD leaderboard 1000 "alice" 900 "bob" 1200 "charlie"
ZRANGE leaderboard 0 -1 WITHSCORES      # Ordine crescente
ZREVRANGE leaderboard 0 2 WITHSCORES    # Top 3 (ordine decrescente)
ZSCORE leaderboard "alice"               # Score di alice
ZRANK leaderboard "alice"                # Posizione (0-based)
ZRANGEBYSCORE leaderboard 900 1100       # Elementi con score tra 900 e 1100
ZINCRBY leaderboard 50 "alice"           # Incrementa score
ZCARD leaderboard                        # Cardinalita
ZREM leaderboard "bob"                   # Rimuovi

# === COMANDI GENERICI ===
EXISTS key
DEL key1 key2
UNLINK key1 key2                         # DELETE asincrono (non blocca)
TYPE key                                 # Tipo del valore
TTL key                                  # Secondi rimanenti (-1 = no scadenza, -2 = non esiste)
PTTL key                                 # Millisecondi rimanenti
EXPIRE key 3600                          # Scade in 1 ora
PERSIST key                              # Rimuovi scadenza
SCAN 0 MATCH "user:*" COUNT 100         # Iterazione sicura (mai usare KEYS in produzione)
DBSIZE                                   # Numero chiavi
INFO                                     # Statistiche complete
INFO memory                              # Uso memoria
INFO replication                         # Stato replica
INFO keyspace                            # Distribuzione chiavi
MONITOR                                  # Stream comandi in tempo reale (debug, NON in produzione)
```

### Persistenza: RDB e AOF

```bash
# === RDB (Redis Database Backup) ===
# Snapshot periodico dell'intero dataset su disco
# Pro: file compatto, ripristino veloce
# Contro: possibile perdita di dati tra uno snapshot e l'altro

# redis.conf:
save 900 1                                # Salva se >= 1 chiave cambiata in 900s
save 300 10                               # Salva se >= 10 chiavi cambiate in 300s
save 60 10000                             # Salva se >= 10000 chiavi cambiate in 60s
# save ""                                 # Disabilita RDB
dbfilename dump.rdb
dir /var/lib/redis/
rdbcompression yes
rdbchecksum yes

# Trigger manuale
redis-cli BGSAVE                          # Salvataggio in background (non blocca)
redis-cli SAVE                            # Salvataggio sincrono (BLOCCA il server!)

# === AOF (Append Only File) ===
# Log di tutte le operazioni di scrittura
# Pro: perdita dati minima (configurabile)
# Contro: file più grande, ripristino più lento

# redis.conf:
appendonly yes
appendfilename "appendonly.aof"
appenddirname "appendonlydir"

# Frequenza di sync:
# appendfsync always                      # Ogni comando (più sicuro, più lento)
appendfsync everysec                      # Ogni secondo (compromesso consigliato)
# appendfsync no                          # Lascia all'OS (più veloce, rischio)

# Riscrittura AOF (compatta il file)
auto-aof-rewrite-percentage 100           # Riscrivi quando AOF e il doppio dell'ultimo
auto-aof-rewrite-min-size 64mb            # Dimensione minima per riscrittura
# Trigger manuale:
redis-cli BGREWRITEAOF

# === STRATEGIA RACCOMANDATA ===
# Usare ENTRAMBI: RDB per backup e recovery veloce, AOF per durabilità
# In caso di ripristino, Redis usa AOF (più completo) se entrambi presenti

# Backup:
cp /var/lib/redis/dump.rdb /backup/redis/dump_$(date +%Y%m%d).rdb
# Per AOF: copiare l'intera directory appendonlydir/
```

### Replica Redis

```bash
# === CONFIGURAZIONE REPLICA ===
# Sul server replica, aggiungere a redis.conf:
replicaof 10.0.0.1 6379                   # IP e porta del master
masterauth "master-password"               # Password del master
replica-read-only yes                      # Replica in sola lettura

# Oppure a runtime:
redis-cli REPLICAOF 10.0.0.1 6379

# Verificare stato:
# Sul master:
redis-cli INFO replication
# Deve mostrare: role:master, connected_slaves:N

# Sulla replica:
redis-cli INFO replication
# Deve mostrare: role:slave, master_link_status:up

# Promuovere una replica a master:
redis-cli REPLICAOF NO ONE

# === REPLICA ASINCRONA (default) ===
# Il master non attende conferma dalla replica
# Possibile perdita di dati se il master crasha dopo una scrittura

# === REPLICA SINCRONA (parziale) ===
# min-replicas-to-write 1                 # Almeno 1 replica deve confermare
# min-replicas-max-lag 10                 # Lag massimo 10 secondi
```

### Redis Sentinel

Redis Sentinel fornisce alta disponibilità: monitora i server, rileva guasti, ed esegue failover automatico.

```bash
# === ARCHITETTURA ===
# Minimo 3 istanze Sentinel (quorum per failover)
# Sentinel monitora 1 master + N repliche

# === sentinel.conf ===
port 26379
sentinel monitor mymaster 10.0.0.1 6379 2
# "mymaster" = nome del cluster
# 10.0.0.1:6379 = indirizzo del master
# 2 = quorum (numero di Sentinel che devono concordare sul guasto)

sentinel auth-pass mymaster "master-password"
sentinel down-after-milliseconds mymaster 5000      # 5s senza risposta = down
sentinel failover-timeout mymaster 60000             # Timeout failover 60s
sentinel parallel-syncs mymaster 1                   # 1 replica alla volta si sincronizza

# Avvio Sentinel
redis-sentinel /etc/redis/sentinel.conf
# oppure
redis-server /etc/redis/sentinel.conf --sentinel

# === VERIFICA ===
redis-cli -p 26379 SENTINEL masters
redis-cli -p 26379 SENTINEL replicas mymaster
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster

# === CONNESSIONE APPLICATIVA ===
# Le applicazioni si connettono a Sentinel per scoprire il master attuale:
# Python con redis-py:
# from redis.sentinel import Sentinel
# sentinel = Sentinel([('10.0.0.1', 26379), ('10.0.0.2', 26379), ('10.0.0.3', 26379)])
# master = sentinel.master_for('mymaster', password='master-password')
# slave = sentinel.slave_for('mymaster', password='master-password')
```

### Redis Cluster

Redis Cluster distribuisce i dati su più nodi (sharding automatico). Supporta fino a 1000 nodi.

```bash
# === ARCHITETTURA ===
# - Dati partizionati in 16384 hash slot
# - Ogni nodo master gestisce un sottoinsieme di slot
# - Ogni master ha 1+ repliche per alta disponibilità
# - Minimo raccomandato: 6 nodi (3 master + 3 repliche)

# === CREAZIONE CLUSTER ===
# Avviare 6 istanze Redis (porte 7000-7005):
# redis.conf per ogni istanza:
port 7000                                 # 7000, 7001, ..., 7005
cluster-enabled yes
cluster-config-file nodes-7000.conf
cluster-node-timeout 5000
appendonly yes

# Creare il cluster:
redis-cli --cluster create \
    10.0.0.1:7000 10.0.0.1:7001 \
    10.0.0.2:7002 10.0.0.2:7003 \
    10.0.0.3:7004 10.0.0.3:7005 \
    --cluster-replicas 1

# === GESTIONE ===
redis-cli -c -h 10.0.0.1 -p 7000         # -c = modalita cluster
CLUSTER INFO
CLUSTER NODES
CLUSTER SLOTS

# Aggiungere un nodo master
redis-cli --cluster add-node 10.0.0.4:7006 10.0.0.1:7000

# Aggiungere una replica
redis-cli --cluster add-node 10.0.0.4:7007 10.0.0.1:7000 \
    --cluster-slave --cluster-master-id <master-node-id>

# Ribilanciare gli slot
redis-cli --cluster rebalance 10.0.0.1:7000

# Rimuovere un nodo (spostare prima gli slot)
redis-cli --cluster reshard 10.0.0.1:7000
redis-cli --cluster del-node 10.0.0.1:7000 <node-id>

# === PROMETHEUS EXPORTER ===
# redis_exporter: https://github.com/oliver006/redis_exporter
./redis_exporter --redis.addr=redis://localhost:6379 --redis.password="password"
# Dashboard Grafana: ID 763
```

---

## MongoDB

### Installazione e configurazione MongoDB

```bash
# Installazione (da repository ufficiale MongoDB)
# Debian/Ubuntu:
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] \
    https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
    sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update && sudo apt install mongodb-org

# RHEL/Fedora: creare /etc/yum.repos.d/mongodb-org-7.0.repo
sudo dnf install mongodb-org

sudo systemctl enable --now mongod

# File principali
/etc/mongod.conf                          # Configurazione
/var/lib/mongodb/                         # Data directory
/var/log/mongodb/mongod.log               # Log
```

```yaml
# /etc/mongod.conf
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4                      # ~50% RAM - 1 GB
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen

net:
  port: 27017
  bindIp: 127.0.0.1                       # Solo locale; aggiungere IP per accesso remoto
  maxIncomingConnections: 1000

security:
  authorization: enabled                  # OBBLIGATORIO in produzione

operationProfiling:
  mode: slowOp                            # off | slowOp | all
  slowOpThresholdMs: 100

replication:
  replSetName: rs0                        # Necessario per replica set

# sharding:
#   clusterRole: shardsvr                 # Per sharding
```

```bash
# Configurazione iniziale utente admin
mongosh
use admin
db.createUser({
    user: "admin",
    pwd: "admin_password",
    roles: [{ role: "root", db: "admin" }]
})

# Creare utente applicativo
use mydb
db.createUser({
    user: "app_user",
    pwd: "app_password",
    roles: [
        { role: "readWrite", db: "mydb" },
        { role: "read", db: "analytics" }
    ]
})

# Connessione autenticata
mongosh --host localhost --port 27017 -u app_user -p --authenticationDatabase mydb
# oppure con URI:
mongosh "mongodb://app_user:app_password@localhost:27017/mydb"
```

### Operazioni CRUD MongoDB

```javascript
// === CREATE ===
db.users.insertOne({ name: "Alice", age: 30, city: "Roma", tags: ["admin", "dev"] })
db.users.insertMany([
    { name: "Bob", age: 25, city: "Milano" },
    { name: "Charlie", age: 35, city: "Roma" }
])

// === READ ===
db.users.find()                           // Tutti i documenti
db.users.find({ city: "Roma" })           // Filtro semplice
db.users.find({ age: { $gt: 25 } })      // age > 25
db.users.find({ age: { $gte: 25, $lte: 35 } })  // 25 <= age <= 35
db.users.find({ city: { $in: ["Roma", "Milano"] } })
db.users.find({ tags: "admin" })          // Array contiene "admin"
db.users.find({ name: /^A/i })            // Regex

// Proiezione (campi da restituire)
db.users.find({ city: "Roma" }, { name: 1, age: 1, _id: 0 })

// Ordinamento, limite, skip
db.users.find().sort({ age: -1 }).limit(10).skip(20)

// Conteggio
db.users.countDocuments({ city: "Roma" })
db.users.estimatedDocumentCount()         // Piu veloce (da metadati)

// Aggregation pipeline
db.orders.aggregate([
    { $match: { status: "completed" } },
    { $group: { _id: "$customer_id", total: { $sum: "$amount" }, count: { $sum: 1 } } },
    { $sort: { total: -1 } },
    { $limit: 10 }
])

// === UPDATE ===
db.users.updateOne({ name: "Alice" }, { $set: { age: 31 } })
db.users.updateMany({ city: "Roma" }, { $set: { country: "IT" } })
db.users.updateOne({ name: "Alice" }, { $inc: { age: 1 } })          // Incremento
db.users.updateOne({ name: "Alice" }, { $push: { tags: "dba" } })    // Push in array
db.users.updateOne({ name: "Alice" }, { $pull: { tags: "dev" } })    // Rimuovi da array
db.users.replaceOne({ name: "Alice" }, { name: "Alice", age: 32 })   // Sostituisci intero documento

// Upsert (inserisci se non esiste)
db.users.updateOne(
    { name: "David" },
    { $set: { age: 28, city: "Napoli" } },
    { upsert: true }
)

// === DELETE ===
db.users.deleteOne({ name: "Alice" })
db.users.deleteMany({ age: { $lt: 18 } })
db.users.drop()                           // Elimina intera collection

// === INFO ===
show dbs
show collections
db.stats()
db.users.stats()
```

### Indici MongoDB

```javascript
// === INDICE SINGOLO ===
db.users.createIndex({ email: 1 })                    // Ascendente
db.users.createIndex({ created_at: -1 })               // Discendente

// === INDICE COMPOSTO ===
db.orders.createIndex({ customer_id: 1, created_at: -1 })

// === INDICE UNICO ===
db.users.createIndex({ email: 1 }, { unique: true })

// === INDICE TTL (auto-eliminazione documenti) ===
db.sessions.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 })
// Documenti con expires_at nel passato vengono eliminati automaticamente

// === INDICE TESTO (full-text search) ===
db.articles.createIndex({ title: "text", body: "text" })
db.articles.find({ $text: { $search: "linux database" } })

// === INDICE HASHED (per sharding) ===
db.users.createIndex({ user_id: "hashed" })

// === INDICE PARZIALE ===
db.orders.createIndex(
    { status: 1 },
    { partialFilterExpression: { status: "pending" } }
)

// === INDICE SPARSE ===
// Indicizza solo documenti che hanno il campo
db.users.createIndex({ phone: 1 }, { sparse: true })

// === GESTIONE INDICI ===
db.users.getIndexes()
db.users.dropIndex("email_1")
db.users.dropIndexes()                    // Tutti tranne _id

// EXPLAIN per verificare uso indici
db.users.find({ email: "alice@example.com" }).explain("executionStats")
// Cercare: "stage": "IXSCAN" (buono) vs "COLLSCAN" (scansione completa)
```

### Replica set MongoDB

Un replica set e un gruppo di istanze mongod che mantengono lo stesso dataset. Fornisce ridondanza e alta disponibilità.

```bash
# === ARCHITETTURA ===
# - 1 Primary (letture e scritture)
# - N Secondary (letture opzionali, failover automatico)
# - Opzionale: Arbiter (solo voto, no dati)
# - Minimo raccomandato: 3 nodi (o 2 nodi + 1 arbiter)

# === CONFIGURAZIONE ===
# mongod.conf su ogni nodo:
replication:
  replSetName: rs0

# Inizializzare il replica set (dal primary designato):
mongosh
rs.initiate({
    _id: "rs0",
    members: [
        { _id: 0, host: "10.0.0.1:27017", priority: 10 },
        { _id: 1, host: "10.0.0.2:27017", priority: 5 },
        { _id: 2, host: "10.0.0.3:27017", priority: 1 }
    ]
})

# priority più alta = preferenza per primary

# === VERIFICA ===
rs.status()                               # Stato completo
rs.conf()                                 # Configurazione
rs.isMaster()                             # Chi e il primary
db.printReplicationInfo()                 # Stato oplog
db.printSecondaryReplicationInfo()        # Lag repliche

# === GESTIONE ===
# Aggiungere un membro
rs.add("10.0.0.4:27017")

# Aggiungere un arbiter
rs.addArb("10.0.0.5:27017")

# Rimuovere un membro
rs.remove("10.0.0.4:27017")

# Forzare step-down del primary (failover)
rs.stepDown(60)                           # Rinuncia per 60 secondi

# Read preference (dal driver applicativo):
# primary           — solo dal primary (default)
# primaryPreferred  — primary se disponibile, altrimenti secondary
# secondary         — solo dai secondary
# secondaryPreferred — secondary se disponibile, altrimenti primary
# nearest           — dal nodo con latenza più bassa
```

### Sharding MongoDB

Lo sharding distribuisce i dati su più shard per scalabilità orizzontale.

```bash
# === COMPONENTI ===
# - Shard: ogni shard e un replica set che contiene un sottoinsieme dei dati
# - Config Server: replica set che memorizza metadati e routing
# - mongos: router che indirizza le query allo shard corretto

# === SETUP (concettuale) ===
# 1. Avviare i config server (replica set)
mongod --configsvr --replSet configRS --port 27019

# 2. Avviare gli shard (ciascuno come replica set)
mongod --shardsvr --replSet shard1RS --port 27018
mongod --shardsvr --replSet shard2RS --port 27020

# 3. Avviare mongos (router)
mongos --configdb configRS/cfg1:27019,cfg2:27019,cfg3:27019 --port 27017

# 4. Aggiungere gli shard
mongosh --port 27017
sh.addShard("shard1RS/shard1a:27018,shard1b:27018,shard1c:27018")
sh.addShard("shard2RS/shard2a:27020,shard2b:27020,shard2c:27020")

# 5. Abilitare sharding su un database
sh.enableSharding("mydb")

# 6. Shardare una collection
# Range-based (per query su intervalli)
sh.shardCollection("mydb.orders", { customer_id: 1 })

# Hash-based (distribuzione uniforme)
sh.shardCollection("mydb.logs", { _id: "hashed" })

# === VERIFICA ===
sh.status()                               # Stato completo dello sharding
db.orders.getShardDistribution()          # Distribuzione dati

# === PROMETHEUS EXPORTER ===
# mongodb_exporter: https://github.com/percona/mongodb_exporter
./mongodb_exporter --mongodb.uri="mongodb://monitor:password@localhost:27017"
# Dashboard Grafana: ID 2583
```

---

## Matrice comparativa database

| Caratteristica | PostgreSQL | MySQL/MariaDB | MongoDB | Redis | SQLite |
|---------------|-----------|--------------|---------|-------|--------|
| **Modello** | Relazionale | Relazionale | Documentale | Key-Value | Relazionale embedded |
| **Licenza** | PostgreSQL (MIT-like) | GPL (MySQL), GPL (MariaDB) | SSPL | BSD 3-clause | Public domain |
| **ACID** | Completo | Completo (InnoDB) | Per documento (multi-doc da 4.0) | Transazioni limitate | Completo |
| **SQL** | Standard completo | Buono | No (MQL) | No | Buono (con limitazioni) |
| **JSON** | JSONB nativo, indicizzabile | JSON (da 5.7) | Nativo (BSON) | No (ma RedisJSON) | JSON1 extension |
| **Full-text search** | Si (ts_vector) | Si | Si (Atlas Search) | Si (RediSearch) | FTS5 extension |
| **Replica** | Streaming + Logica | Master-Slave, Group Repl. | Replica set | Master-Replica, Sentinel | No |
| **Sharding** | Citus extension | MySQL Cluster, Vitess | Nativo | Redis Cluster | No |
| **Max dimensione** | 32 TB per tabella | 64 TB (InnoDB) | Illimitato (sharded) | Limitato dalla RAM | ~281 TB |
| **Connessioni** | Processo per connessione | Thread per connessione | Thread per connessione | Single-thread event loop | In-process |
| **Uso RAM tipico** | Medio-alto | Medio | Alto | Molto alto (in-memory) | Molto basso |
| **Complessita ops** | Media | Bassa-media | Media | Bassa | Nessuna (embedded) |
| **Curva di apprendimento** | Media-alta | Bassa-media | Bassa | Bassa | Molto bassa |

---

## Matrice decisionale: quale database scegliere

### Per tipo di workload

| Workload | Database consigliato | Motivazione |
|----------|---------------------|-------------|
| Web app classica (CRUD) | **PostgreSQL** | ACID, JSON, indici avanzati, estensioni |
| Blog/CMS semplice | **MySQL/MariaDB** | Ecosìstema WordPress, facilita, hosting diffuso |
| E-commerce | **PostgreSQL** | Transazioni complesse, integrità referenziale |
| Caching | **Redis** | Sub-millisecondo, TTL, eviction policies |
| Sessioni utente | **Redis** | Veloce, TTL nativo, replica |
| Code di messaggi | **Redis** (semplice) / RabbitMQ (complesso) | List con BRPOP, Streams |
| Log e analytics | **ClickHouse** o **MongoDB** | Inserimento bulk, query aggregate |
| IoT / time-series | **TimescaleDB** (su PostgreSQL) | Hypertables, compressione, continuous aggregates |
| Microservizi con schema flessibile | **MongoDB** | Schema-less, documenti nidificati |
| App mobile/desktop locale | **SQLite** | Zero configurazione, file singolo |
| Search engine | **Elasticsearch** / **Meilisearch** | Full-text ottimizzato, faceted search |
| Grafo/social network | **Neo4j** | Query su relazioni, Cypher |
| Feature flags / config | **Redis** o **etcd** | Veloce, distribuito |

### Albero decisionale rapido

```
Il dato e strutturato con relazioni?
├── Si → Servono transazioni ACID forti?
│   ├── Si → PostgreSQL (o MySQL per semplicita)
│   └── No → Lo schema cambia spesso?
│       ├── Si → MongoDB
│       └── No → PostgreSQL
└── No → Serve accesso sub-millisecondo?
    ├── Si → I dati stanno in RAM?
    │   ├── Si → Redis
    │   └── No → Redis + persistenza, o database dedicato
    └── No → E una singola applicazione locale?
        ├── Si → SQLite
        └── No → Valutare in base al modello dati
```

---

## Monitoring database

### Strumenti generici

```bash
# === PROMETHEUS + GRAFANA ===
# Architettura: Database → Exporter → Prometheus → Grafana

# Exporter per ogni database:
# PostgreSQL: postgres_exporter  (:9187)
# MySQL:      mysqld_exporter    (:9104)
# Redis:      redis_exporter     (:9121)
# MongoDB:    mongodb_exporter   (:9216)

# prometheus.yml (targets):
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['db1:9187', 'db2:9187']
  - job_name: 'mysql'
    static_configs:
      - targets: ['db3:9104']
  - job_name: 'redis'
    static_configs:
      - targets: ['cache1:9121']
  - job_name: 'mongodb'
    static_configs:
      - targets: ['mongo1:9216']

# === METRICHE CHIAVE DA MONITORARE ===
# Per TUTTI i database:
# 1. Connessioni attive / massime
# 2. Query al secondo (QPS)
# 3. Latenza media delle query
# 4. Errori / query fallite
# 5. Uso disco (dati + log + WAL)
# 6. Uso CPU e RAM
# 7. Cache hit ratio (>99% obiettivo)
# 8. Replica lag (secondi o byte)
# 9. Lock contention
# 10. Slow queries al minuto
```

### Slow query analysis

```bash
# === POSTGRESQL ===
# postgresql.conf: log_min_duration_statement = 500
# Analizzare con pgBadger:
sudo apt install pgbadger
pgbadger /var/log/postgresql/postgresql-*.log -o report.html

# === MYSQL ===
# my.cnf: slow_query_log = 1, long_query_time = 1
# Analizzare con pt-query-digest (Percona Toolkit):
sudo apt install percona-toolkit
pt-query-digest /var/log/mysql/slow.log > slow_report.txt

# === MONGODB ===
# Profiling:
db.setProfilingLevel(1, { slowms: 100 })   # Log query > 100ms
db.system.profile.find().sort({ ts: -1 }).limit(10)

# === REDIS ===
# Slow log:
CONFIG SET slowlog-log-slower-than 10000   # 10ms in microsecondi
CONFIG SET slowlog-max-len 128
SLOWLOG GET 10                             # Ultime 10 query lente
SLOWLOG LEN                                # Numero entry
SLOWLOG RESET                              # Pulisci
```

---

## Sicurezza database

### Isolamento di rete

```bash
# === FIREWALL (ufw/iptables) ===
# PostgreSQL: solo dalla rete applicativa
sudo ufw allow from 10.0.0.0/8 to any port 5432

# MySQL: solo dal server web
sudo ufw allow from 10.0.0.10 to any port 3306

# Redis: solo localhost (se sulla stessa macchina dell'app)
sudo ufw deny 6379
# oppure bind 127.0.0.1 in redis.conf

# MongoDB: solo dalla rete interna
sudo ufw allow from 10.0.0.0/8 to any port 27017

# === REGOLE GENERALI ===
# 1. MAI esporre porte database su IP pubblico
# 2. Usare VPN o tunnel SSH per accesso remoto
# 3. Separare rete database dalla rete pubblica (VLAN o subnet)
# 4. Usare security group (cloud) o iptables (bare metal)

# SSH tunnel per accesso temporaneo:
ssh -L 5432:db-server:5432 bastion-host
# Poi connettersi a localhost:5432
```

### Encryption

```bash
# === ENCRYPTION IN TRANSIT (TLS/SSL) ===

# PostgreSQL: ssl = on in postgresql.conf + hostssl in pg_hba.conf
# MySQL: require_secure_transport = ON
# Redis: tls-port 6380, tls-cert-file, tls-key-file
# MongoDB: net.tls.mode: requireTLS

# === ENCRYPTION AT REST ===

# A livello filesystem (LUKS):
sudo cryptsetup luksFormat /dev/sdb1
sudo cryptsetup luksOpen /dev/sdb1 db_crypt
sudo mkfs.ext4 /dev/mapper/db_crypt
sudo mount /dev/mapper/db_crypt /var/lib/postgresql

# A livello database:
# PostgreSQL: pgcrypto extension per colonne specifiche
# MySQL: InnoDB tablespace encryption (innodb_encrypt_tables = ON in MariaDB)
# MongoDB: Encrypted Storage Engine (Enterprise)

# === ENCRYPTION DI COLONNE SENSIBILI (PostgreSQL) ===
CREATE EXTENSION pgcrypto;

-- Cifrare
INSERT INTO users (name, ssn_encrypted)
VALUES ('Alice', pgp_sym_encrypt('ABCD1234', 'encryption_key'));

-- Decifrare
SELECT name, pgp_sym_decrypt(ssn_encrypted, 'encryption_key') AS ssn
FROM users;
-- ATTENZIONE: la chiave non deve essere hardcoded nel codice
-- Usare variabili di sessione o un key management service
```

### Controllo accessi

```bash
# === PRINCIPIO DEL MINIMO PRIVILEGIO ===
# 1. Un utente database per ogni applicazione/servizio
# 2. Solo i privilegi strettamente necessari
# 3. Mai GRANT ALL ON *.*
# 4. Separare utenti di lettura da quelli di scrittura
# 5. Usare ruoli/gruppi per gestire i permessi
# 6. Audit regolare dei permessi assegnati

# === PREVENZIONE SQL INJECTION ===
# SEMPRE usare query parametrizzate, MAI concatenare stringhe

# SBAGLIATO (vulnerabile a SQL injection):
query = "SELECT * FROM users WHERE name = '" + user_input + "'"

# CORRETTO (parametrizzato):
# Python (psycopg2):
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))

# Python (SQLAlchemy):
session.query(User).filter(User.name == user_input)

# Node.js (pg):
client.query('SELECT * FROM users WHERE name = $1', [userInput])

# Go (database/sql):
db.Query("SELECT * FROM users WHERE name = $1", userInput)

# PHP (PDO):
$stmt = $pdo->prepare('SELECT * FROM users WHERE name = :name');
$stmt->execute(['name' => $userInput]);

# === AUDIT ===
# PostgreSQL: pgAudit (vedi sezione Sicurezza PostgreSQL)
# MySQL: audit_log plugin (Enterprise) o MariaDB Audit Plugin
# MongoDB: db.setProfilingLevel(2) o MongoDB Enterprise Audit
# Redis: ACL LOG (Redis 6+)
```

---

## Best Practices

1. **Backup automatizzato e testato**: backup giornaliero con retention policy. Testare il restore almeno mensilmente. Un backup non testato non e un backup.
2. **Non esporre al pubblico**: database su rete interna, non su IP pubblico. Accesso solo da app server via rete privata o tunnel SSH.
3. **Password forti**: autenticazione sempre abilitata. Nessun database in produzione senza password. Usare SCRAM-SHA-256 (PostgreSQL) o caching_sha2_password (MySQL).
4. **Monitoring**: monitorare connessioni attive, slow query, spazio disco, cache hit ratio, replica lag. Alert su anomalie.
5. **Aggiornamenti**: mantenere i database aggiornati per patch di sicurezza. Testare prima in staging. Seguire le release note per breaking changes.
6. **Connection pooling**: usare PgBouncer (PostgreSQL) o ProxySQL (MySQL) per gestire le connessioni in modo efficiente. Riduce overhead di creazione connessione.
7. **Tuning graduale**: iniziare con i default, poi ottimizzare basandosi sulle metriche reali del workload. Non copiare configurazioni trovate online senza capirle.
8. **Separazione ambienti**: database separati per sviluppo, staging, produzione. Mai usare dati di produzione in sviluppo senza anonimizzazione.
9. **Schema migration**: usare strumenti di migrazione (Flyway, Alembic, Prisma Migrate, Liquibase). Mai ALTER TABLE manualmente in produzione.
10. **Indici mirati**: creare indici basandosi sulle query reali (`EXPLAIN ANALYZE`). Troppi indici rallentano le scritture.
11. **Vacuum regolare (PostgreSQL)**: monitorare dead tuples e autovacuum. Tabelle ad alto UPDATE richiedono autovacuum aggressivo.
12. **Binary log / WAL retention**: configurare la retention dei log binari/WAL in base alla policy di PITR e alla capacita disco.
13. **Replica per HA**: almeno una replica per ogni database in produzione. Testare il failover periodicamente.
14. **Read-only replica per analytics**: deviare le query di reportistica alle repliche per non impattare il workload OLTP.

---

## Troubleshooting

### 1. "Too many connections"
`max_connections` raggiunto. `SHOW PROCESSLIST` (MySQL) o `pg_stat_activity` (PostgreSQL) per vedere chi e connesso. Chiudere connessioni idle. Lungo termine: connection pooling (PgBouncer/ProxySQL).

### 2. "Query lenta"
Abilitare slow query log. `EXPLAIN ANALYZE` per capire il piano di esecuzione. Indici mancanti? Tabella non vacuumata (PostgreSQL)? Statistiche non aggiornate (`ANALYZE`)?

### 3. "Disco pieno"
Per PostgreSQL: `VACUUM FULL` recupera spazio (ma blocca la tabella). WAL che crescono: controllare `archive_command` o `max_wal_size`. Per MySQL: `OPTIMIZE TABLE`. Verificare binary log retention (`binlog_expire_logs_seconds`).

### 4. "Replica in ritardo"
Verificare rete tra primario e replica. Il carico di scrittura e troppo alto? La replica ha hardware sufficiente? Controllare log di replica per errori. Per PostgreSQL: `pg_stat_replication` → colonna `replay_lag`. Per MySQL: `SHOW SLAVE STATUS\G` → `Seconds_Behind_Master`.

### 5. "Lock contention / deadlock"
PostgreSQL: `SELECT * FROM pg_locks WHERE NOT granted;` e `pg_stat_activity` per vedere chi blocca chi. MySQL: `SHOW ENGINE INNODB STATUS\G` → sezione DEADLOCK. Soluzione: ridurre la durata delle transazioni, accedere alle tabelle in ordine consistente.

### 6. "Connection refused"
Il servizio e in esecuzione? (`systemctl status`). `listen_addresses` include l'IP richiesto? `pg_hba.conf` / firewall permettono la connessione? La porta e corretta?

### 7. "Authentication failed"
Verificare utente/password. Controllare `pg_hba.conf` (PostgreSQL): il metodo e corretto per quel tipo di connessione? L'utente esiste? (`\du` in psql). MySQL: l'utente e associato all'host corretto? (`'user'@'host'`).

### 8. "OOM Killer termina il database"
`shared_buffers` troppo grande. `work_mem × max_connections` supera la RAM disponibile. Ridurre `work_mem` o `max_connections`. Configurare `vm.overcommit_memory = 2` e swap.

### 9. "WAL accumulation / pg_wal pieno"
Slot di replica inattivi che trattengono WAL. `SELECT * FROM pg_replication_slots WHERE NOT active;` → `pg_drop_replication_slot()`. Oppure `archive_command` fallisce: verificare con `pg_stat_archiver`.

### 10. "Autovacuum non parte"
Verificare `autovacuum = on`. Tabella con `autovacuum_enabled = false`? Worker tutti occupati (`autovacuum_max_workers`)? Tabella troppo grande per un singolo worker? Aumentare `autovacuum_work_mem` e ridurre `autovacuum_vacuum_scale_factor` per tabelle grandi.

### 11. "Corruzione dati"
PostgreSQL: `pg_amcheck` per verificare indici. `SELECT count(*) FROM tabella;` genera errori? Verificare checksum (`SHOW data_checksums`). Ripristinare da backup. MySQL: `CHECK TABLE tablename;` e `REPAIR TABLE tablename;` (solo MyISAM). Per InnoDB: ripristinare da backup.

### 12. "Slow query su MongoDB"
`db.collection.find(...).explain("executionStats")` → cercare `COLLSCAN` (nessun indice). Creare indice appropriato. Verificare dimensione documenti (`db.collection.stats()`). Aggregation pipeline con `$lookup` su collection non indicizzate.

### 13. "Redis out of memory"
Verificare `maxmemory` e `maxmemory-policy`. `INFO memory` → `used_memory_human`. Troppe chiavi senza TTL? `SCAN` per trovare chiavi grandi: `redis-cli --bigkeys`. Valutare eviction policy (allkeys-lru per cache).

### 14. "Replica Redis disconnessa"
`INFO replication` → `master_link_status:down`. Verificare rete, password (`masterauth`), porta. Il master ha raggiunto `maxmemory` e non puo generare RDB per la sincronizzazione iniziale?

### 15. "MongoDB replica set elezione continua"
Numero pari di membri (nessuna maggioranza)? Rete instabile tra i nodi? `rs.status()` → `stateStr` per ogni membro. Aggiungere un arbiter se i nodi sono pari.

### 16. "Performance degradata dopo upgrade"
Statistiche obsolete: `ANALYZE` (PostgreSQL) o `ANALYZE TABLE` (MySQL). Piano di esecuzione cambiato: confrontare `EXPLAIN` prima e dopo. Parametri di configurazione resettati al default?

### 17. "Binary log troppo grandi (MySQL)"
Verificare `binlog_expire_logs_seconds` (o `expire_logs_days` su versioni vecchie). Purgare manualmente: `PURGE BINARY LOGS BEFORE '2026-05-01';`. Non purgare log ancora necessari per le repliche.

### 18. "Connessioni idle in transaction (PostgreSQL)"
Query o transazione non chiusa dall'applicazione. `SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';`. Impostare `idle_in_transaction_session_timeout = 30000` (30s). L'applicazione deve usare correttamente BEGIN/COMMIT/ROLLBACK.

### 19. "Checkpoint troppo frequenti (PostgreSQL)"
`log_checkpoints = on` → verificare la frequenza nei log. Aumentare `max_wal_size` (es. 4GB). Checkpoint frequenti significano I/O elevato e impatto sulle performance.

### 20. "Sharding MongoDB sbilanciato"
`sh.status()` → distribuzione chunk tra shard. Il balancer e attivo? `sh.getBalancerState()`. La shard key ha scarsa cardinalità (es. booleano)? Considerare una shard key diversa. Il balancer potrebbe essere lento su collection molto grandi.

### 21. "pg_basebackup fallisce"
Verificare `max_wal_senders` (deve essere > 0 e non raggiunto). L'utente ha il privilegio `REPLICATION`? `pg_hba.conf` permette connessioni di tipo `replication`? Lo slot di replica esiste? Spazio disco sufficiente sulla destinazione?

### 22. "Tabelle bloated (PostgreSQL)"
`SELECT pg_size_pretty(pg_total_relation_size('tabella'));` confrontato con numero di righe. Rapporto alto = bloat. `VACUUM FULL tabella;` (lock esclusivo) oppure `pg_repack` (senza downtime). Prevenire con autovacuum aggressivo.

---

## FAQ

**1. PostgreSQL o MySQL: quale scegliere per un nuovo progetto?**
PostgreSQL per la maggior parte dei casi. Supporto SQL più completo, JSONB nativo, indici avanzati (GIN, GiST, BRIN), estensioni (PostGIS, TimescaleDB, pgvector), RLS, CTE ricorsive. MySQL se il progetto e un CMS WordPress-like o se il team ha già esperienza MySQL.

**2. Quanto shared_buffers impostare?**
Punto di partenza: 25% della RAM totale. Con 16 GB di RAM → 4 GB. Non superare il 40% per lasciare spazio al filesystem cache dell'OS. Monitorare il cache hit ratio (`pg_statio_user_tables`): deve essere > 99%.

**3. Devo usare un connection pooler?**
Si, quasi sempre in produzione. PostgreSQL crea un processo per ogni connessione → overhead significativo con molte connessioni. PgBouncer in `transaction` mode e il setup più comune. MySQL ha thread leggeri, ma ProxySQL aggiunge query routing e failover.

**4. Ogni quanto testare i backup?**
Almeno una volta al mese in un ambiente di staging. Automatizzare il test: ripristinare il backup su un server di test, eseguire query di verifica, confrontare row count con la produzione. Un backup mai testato non e affidabile.

**5. Come gestire le migrazioni di schema in produzione?**
Usare strumenti di migrazione (Flyway, Alembic, Prisma Migrate, Liquibase, golang-migrate). Ogni migrazione deve essere reversibile (up + down). Testare prima in staging. Per tabelle grandi, usare `ALTER TABLE ... ADD COLUMN` (che non riscrive la tabella in PostgreSQL se il default e una costante). Per MySQL, considerare `pt-online-schema-change` o `gh-ost`.

**6. Redis: RDB o AOF?**
Entrambi. RDB per backup rapidi e recovery veloce (snapshot completo). AOF per durabilità (ogni operazione loggata). In caso di crash, Redis usa AOF se disponibile. Impostare `appendfsync everysec` come compromesso tra performance e durabilità.

**7. MongoDB ha bisogno di uno schema?**
Non obbligatorio, ma fortemente consigliato in produzione. Usare la validazione schema di MongoDB (`db.createCollection("users", { validator: { $jsonSchema: {...} } })`). Schemi flessibili sono comodi in sviluppo, ma diventano un incubo di manutenzione senza validazione.

**8. Come scegliere la shard key in MongoDB?**
La shard key deve avere alta cardinalità (molti valori distinti), distribuzione uniforme, e corrispondere ai pattern di query più frequenti. Mai usare un campo monotono (es. ObjectId, timestamp) come shard key senza hashing — causa "hot shard". Usare `{ field: "hashed" }` per distribuzione uniforme o un campo composto.

**9. Quando usare SQLite in produzione?**
Per applicazioni single-server con < 100K richieste/giorno e workload prevalentemente read. Edge computing, app Electron/mobile, file di configurazione, testing. NON per applicazioni multi-server o write-heavy.

**10. Come monitorare la replica lag?**
PostgreSQL: `SELECT replay_lag FROM pg_stat_replication;` — mostra il ritardo in formato intervallo. MySQL: `SHOW SLAVE STATUS\G` → `Seconds_Behind_Master`. Redis: `INFO replication` → `master_last_io_seconds_ago`. MongoDB: `rs.printSecondaryReplicationInfo()`. Alertare se il lag supera i 30 secondi.

**11. Pool_mode transaction vs session in PgBouncer?**
`transaction` (consigliato): la connessione al server viene rilasciata al termine di ogni transazione. Massimo multiplexing. Incompatibile con LISTEN/NOTIFY, prepared statement cross-transazione, SET parametri di sessione. `session`: la connessione resta dedicata per tutta la sessione. Compatibilita completa, ma meno efficiente.

**12. Come prevenire il transaction ID wraparound in PostgreSQL?**
Monitorare `age(datfrozenxid)` con `SELECT datname, age(datfrozenxid) FROM pg_database;`. Se supera 200 milioni, indagare perché autovacuum non sta congelando. Cause comuni: tabella con `autovacuum_freeze_max_age` troppo alto, transazioni long-running, autovacuum bloccato da lock.

**13. Redis Sentinel o Redis Cluster?**
Sentinel: alta disponibilità per un singolo dataset (failover automatico, max ~100 GB). Cluster: scalabilità orizzontale per dataset grandi (sharding automatico). Se i dati stanno nella RAM di un singolo server, usare Sentinel. Se servono >100 GB o throughput > 100K ops/s, Cluster.

**14. Come gestire le connessioni "idle in transaction" in PostgreSQL?**
Impostare `idle_in_transaction_session_timeout` (es. 30000 ms). Queste connessioni impediscono VACUUM di liberare dead tuples e possono causare bloat. L'applicazione deve sempre chiudere le transazioni (COMMIT o ROLLBACK). Connection pooler in `transaction` mode mitiga il problema.

**15. Qual e la differenza tra VACUUM e VACUUM FULL?**
`VACUUM`: marca lo spazio delle dead tuples come riutilizzabile, ma non lo restituisce al filesystem. Non blocca la tabella. `VACUUM FULL`: riscrive l'intera tabella, restituendo lo spazio al filesystem. Richiede lock esclusivo (la tabella e inaccessibile durante l'operazione). Usare `pg_repack` come alternativa senza downtime.

**16. Come faccio a sapere se ho bisogno di un indice?**
Eseguire `EXPLAIN ANALYZE` sulle query lente. Se il piano mostra `Seq Scan` su una tabella grande con un filtro selettivo, serve un indice. Verificare anche `pg_stat_user_indexes` per indici esistenti mai usati (candidati alla rimozione). Non aggiungere indici preventivamente: ogni indice rallenta le scritture.

**17. PostgreSQL vs MySQL per workload ad alte scritture?**
PostgreSQL: MVCC più sofisticato, VACUUM necessario per recuperare spazio. MySQL/InnoDB: purge thread integrato, meno manutenzione per dead rows. Per workload estremamente write-heavy (> 50K INSERT/s), entrambi richiedono tuning specifico. PostgreSQL scala meglio con `COPY` per bulk insert. MySQL scala bene con INSERT multi-row e replica Group Replication.

---

> **Nota finale:** questa guida copre i fondamenti dell'amministrazione database su Linux. Ogni database ha una documentazione ufficiale molto dettagliata che va consultata per configurazioni avanzate e troubleshooting specifici. Testare sempre le modifiche in un ambiente di staging prima della produzione.
