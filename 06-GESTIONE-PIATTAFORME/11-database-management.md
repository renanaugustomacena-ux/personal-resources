---
corso: "Gestione Piattaforme e DevOps"
fase: "5 — Dati e Messaging"
modulo: 11
titolo: "Database Management"
versione: "PostgreSQL 17 · MySQL 8.4 · MongoDB 8"
livello: "Avanzato"
prerequisiti:
  - "01-cloud-aws.md"
  - "04-infrastructure-as-code.md"
  - "08-monitoring-observability.md"
obiettivi:
  - "Progettare e gestire database relazionali e NoSQL in ambienti cloud-managed e self-hosted"
  - "Configurare replication, sharding e high-availability con RPO/RTO definiti"
  - "Implementare strategie di backup, restore e disaster recovery con drill periodici"
  - "Ottimizzare le performance tramite connection pooling, indexing e query tuning"
  - "Applicare data governance, GDPR compliance e classificazione dei dati sensibili"
tag: [postgresql, mysql, mongodb, replication, backup, connection-pooling, ha, dr, gdpr]
---

# Database Management — Documentazione Completa

> **Modulo 11** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Progettare e gestire database relazionali e NoSQL in ambienti cloud-managed e self-hosted
> 2. Configurare replication, sharding e high-availability con RPO/RTO definiti
> 3. Implementare strategie di backup, restore e disaster recovery con drill periodici
> 4. Ottimizzare le performance tramite connection pooling, indexing e query tuning
> 5. Applicare data governance, GDPR compliance e classificazione dei dati sensibili
>
> **Prerequisiti:** [Cloud AWS](01-cloud-aws.md) · [Infrastructure as Code](04-infrastructure-as-code.md) · [Monitoring e Observability](08-monitoring-observability.md)
> **Tempo stimato:** 10-14 ore · **Livello:** Avanzato

## Idee guida

1. **Managed DB > self-hosted nei cloud.** RDS/CloudSQL/Azure DB risparmia ops time.
2. **Replication async: RPO > 0 ma performance preserved.**
3. **Backup + restore drill mensile.** Senza drill, backup = teatro.
4. **Connection pooling (PgBouncer, ProxySQL) > naked client.**


## Indice

1. [Panoramica e Concetti Fondamentali](#1-panoramica-e-concetti-fondamentali)
2. [PostgreSQL — Amministrazione](#2-postgresql--amministrazione)
3. [PostgreSQL — Replica e High Availability](#3-postgresql--replica-e-high-availability)
4. [MySQL/MariaDB — Amministrazione](#4-mysqlmariadb--amministrazione)
5. [MySQL/MariaDB — Replica e High Availability](#5-mysqlmariadb--replica-e-high-availability)
6. [Redis — Amministrazione e Architettura](#6-redis--amministrazione-e-architettura)
7. [MongoDB — Amministrazione](#7-mongodb--amministrazione)
8. [MongoDB — Replica Set e Sharding](#8-mongodb--replica-set-e-sharding)
9. [Database su Kubernetes](#9-database-su-kubernetes)
10. [Performance Tuning](#10-performance-tuning)
11. [Backup e Disaster Recovery](#11-backup-e-disaster-recovery)
12. [Best Practices](#12-best-practices)

---

## 1. Panoramica e Concetti Fondamentali

### Ruolo del DBA nel Platform Engineering

Il Database Administrator (DBA) nel contesto del platform engineering moderno non si limita alla gestione manuale delle istanze. Il suo ruolo si estende alla progettazione di piattaforme dati self-service, alla definizione di policy di governance, all'automazione dei cicli di vita dei database e all'integrazione con pipeline CI/CD. Il DBA opera come ponte tra gli sviluppatori applicativi e l'infrastruttura, garantendo affidabilita, sicurezza e performance.

Le responsabilita principali includono:

- **Provisioning e lifecycle management**: creazione, configurazione, aggiornamento e decommissioning delle istanze.
- **Performance monitoring e tuning**: analisi continua delle query, ottimizzazione degli indici, capacity planning.
- **Backup e disaster recovery**: definizione di strategie di backup, verifica periodica dei restore, gestione del failover.
- **Security e compliance**: hardening dei database, gestione dei permessi, audit logging, conformita GDPR.
- **Automazione**: Infrastructure as Code per database, operatori Kubernetes, script di manutenzione automatizzati.

### SQL vs NoSQL vs NewSQL

**SQL (Relazionale)**: modello basato su tabelle con schema rigido, relazioni definite tramite foreign key, transazioni ACID complete. Ideale per dati strutturati con relazioni complesse. Esempi: PostgreSQL, MySQL, MariaDB, Oracle, SQL Server.

**NoSQL**: categoria ampia che comprende diversi modelli di dati senza schema rigido. Progettati per scalabilita orizzontale e flessibilita dello schema. Sacrificano tipicamente alcune garanzie ACID in favore di disponibilita e performance.

**NewSQL**: sistemi che combinano il modello relazionale e le garanzie ACID dei database SQL tradizionali con la scalabilita orizzontale dei sistemi NoSQL. Esempi: CockroachDB, TiDB, YugabyteDB, Google Spanner.

| Caratteristica | SQL | NoSQL | NewSQL |
|---|---|---|---|
| Schema | Rigido | Flessibile | Rigido |
| Scalabilita | Verticale (primaria) | Orizzontale | Orizzontale |
| Transazioni | ACID complete | Eventuale/limitate | ACID distribuite |
| Query language | SQL standard | Proprietario/vario | SQL standard |
| Consistency | Strong | Eventual (tipica) | Strong |

### CAP Theorem

Il teorema CAP (Brewer, 2000) stabilisce che un sistema distribuito puo garantire al massimo due delle seguenti tre proprieta simultaneamente:

- **Consistency (C)**: ogni lettura riceve il dato piu recente o un errore. Tutti i nodi vedono gli stessi dati nello stesso momento.
- **Availability (A)**: ogni richiesta riceve una risposta (non necessariamente il dato piu recente). Il sistema resta operativo.
- **Partition Tolerance (P)**: il sistema continua a funzionare nonostante la perdita di messaggi tra nodi della rete.

In un sistema distribuito reale, le partizioni di rete sono inevitabili, quindi la scelta pratica si riduce a CP (consistency + partition tolerance) o AP (availability + partition tolerance).

- **CP**: PostgreSQL con replica sincrona, MongoDB (con write concern majority), etcd, ZooKeeper.
- **AP**: Cassandra, DynamoDB, CouchDB, Redis Cluster (in alcune configurazioni).

### ACID vs BASE

**ACID** (Atomicity, Consistency, Isolation, Durability):
- **Atomicity**: la transazione e indivisibile — o si completa interamente o viene annullata.
- **Consistency**: la transazione porta il database da uno stato valido a un altro stato valido.
- **Isolation**: le transazioni concorrenti non interferiscono tra loro (livelli: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE).
- **Durability**: una volta confermata, la transazione persiste anche in caso di crash.

**BASE** (Basically Available, Soft state, Eventually consistent):
- **Basically Available**: il sistema garantisce la disponibilita dei dati anche in caso di fallimento parziale.
- **Soft state**: lo stato del sistema puo cambiare nel tempo anche senza input.
- **Eventually consistent**: il sistema convergera verso uno stato consistente, dato un tempo sufficiente.

### Tipi di Database

**Relazionale**: PostgreSQL, MySQL, MariaDB. Dati strutturati in tabelle con relazioni. Ideale per applicazioni transazionali (OLTP), sistemi finanziari, ERP.

**Document**: MongoDB, CouchDB, Amazon DocumentDB. Dati memorizzati come documenti JSON/BSON. Ideale per CMS, cataloghi prodotti, profili utente con struttura variabile.

**Key-Value**: Redis, Memcached, Amazon DynamoDB, etcd. Coppie chiave-valore con accesso O(1). Ideale per cache, sessioni, configurazioni, feature flags.

**Graph**: Neo4j, Amazon Neptune, ArangoDB. Nodi e relazioni (edges) con proprieta. Ideale per social network, fraud detection, recommendation engine, knowledge graph.

**Time-Series**: InfluxDB, TimescaleDB, Prometheus, QuestDB. Ottimizzati per dati con timestamp. Ideale per monitoring, IoT, dati finanziari, metriche applicative.

**Column-Family**: Apache Cassandra, HBase, ScyllaDB. Dati organizzati per colonne anziche per righe. Ideale per analytics su grandi volumi, log storage, dati con pattern di accesso prevedibili.

### Criteri di Scelta del Database

La scelta del database dipende da molteplici fattori:

1. **Modello dei dati**: strutturato vs semi-strutturato vs non strutturato.
2. **Pattern di accesso**: letture vs scritture, point lookup vs range scan, aggregazioni.
3. **Scalabilita richiesta**: volume dei dati, throughput, numero di connessioni concorrenti.
4. **Garanzie di consistenza**: transazioni ACID necessarie o eventual consistency accettabile.
5. **Latenza**: requisiti di latenza per letture e scritture.
6. **Competenze del team**: familiarita con la tecnologia e disponibilita di supporto.
7. **Ecosistema**: tooling, monitoring, backup, integrazione con lo stack esistente.
8. **Costo**: licenze, infrastruttura, operational overhead.

### Managed vs Self-Hosted

**Managed** (AWS RDS, Azure Database, Google Cloud SQL, MongoDB Atlas):
- Vantaggi: backup automatici, patching, alta disponibilita gestita, scaling semplificato, monitoring integrato.
- Svantaggi: costo maggiore, meno controllo sulla configurazione, vendor lock-in, limitazioni su estensioni e versioni.

**Self-Hosted** (su VM, bare metal, Kubernetes):
- Vantaggi: controllo totale sulla configurazione, nessun vendor lock-in, costo inferiore per grandi volumi, personalizzazione completa.
- Svantaggi: responsabilita operativa completa, necessita di competenze DBA, gestione manuale di backup/HA/patching.

---

## 2. PostgreSQL — Amministrazione

### Installazione

```bash
# Debian/Ubuntu — repository ufficiale PostgreSQL
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y postgresql-16 postgresql-client-16

# RHEL/CentOS/Rocky
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo dnf install -y postgresql16-server postgresql16
sudo /usr/pgsql-16/bin/postgresql-16-setup initdb
sudo systemctl enable --now postgresql-16

# Verifica installazione
psql --version
sudo -u postgres psql -c "SELECT version();"
```

### Architettura Interna

PostgreSQL utilizza un'architettura multi-processo con un processo postmaster principale che gestisce le connessioni client e crea processi backend dedicati per ogni sessione.

**Shared Buffers**: area di memoria condivisa dove PostgreSQL memorizza le pagine dei dati. Il valore consigliato e il 25% della RAM disponibile (fino a 8-16 GB). Evitare di superare il 40% della RAM totale perche il sistema operativo necessita di memoria per il filesystem cache.

**Write-Ahead Logging (WAL)**: meccanismo che garantisce la durabilita scrivendo le modifiche su un log sequenziale prima di applicarle ai file dati. Il WAL consente il recovery dopo un crash e la replica.

**Checkpoints**: processo periodico che scrive le pagine modificate (dirty pages) dai shared buffers al disco. Parametri critici:
- `checkpoint_timeout`: intervallo massimo tra checkpoint (default 5 min, consigliato 15-30 min per carichi OLTP).
- `checkpoint_completion_target`: percentuale del periodo tra checkpoint in cui completare la scrittura (default 0.9).
- `max_wal_size`: dimensione massima del WAL prima di forzare un checkpoint.

**VACUUM**: processo di manutenzione che recupera spazio occupato da tuple morte (righe cancellate o aggiornate). PostgreSQL usa MVCC (Multi-Version Concurrency Control) e ogni UPDATE crea una nuova versione della riga. VACUUM rimuove le versioni obsolete.

```sql
-- VACUUM manuale su una tabella specifica
VACUUM VERBOSE my_table;

-- VACUUM con analisi delle statistiche
VACUUM ANALYZE my_table;

-- VACUUM FULL — riscrive l'intera tabella, acquisisce un lock esclusivo
-- Usare solo quando necessario, blocca tutte le operazioni sulla tabella
VACUUM FULL my_table;
```

### Configurazione postgresql.conf

```ini
# === Memoria ===
shared_buffers = 4GB                    # 25% della RAM
effective_cache_size = 12GB             # 75% della RAM — stima per il query planner
work_mem = 64MB                         # memoria per operazione di sort/hash
maintenance_work_mem = 1GB              # memoria per VACUUM, CREATE INDEX
huge_pages = try                        # abilitare huge pages se disponibili

# === WAL ===
wal_level = replica                     # necessario per replica e PITR
max_wal_size = 4GB
min_wal_size = 1GB
checkpoint_timeout = 15min
checkpoint_completion_target = 0.9
wal_compression = lz4                   # compressione WAL per ridurre I/O

# === Query Planner ===
random_page_cost = 1.1                  # per storage SSD (default 4.0 per HDD)
effective_io_concurrency = 200          # per SSD (default 1 per HDD)
seq_page_cost = 1.0

# === Connessioni ===
max_connections = 200                   # usare connection pooling per valori alti
listen_addresses = '*'
port = 5432

# === Logging ===
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_duration_statement = 500        # log query che superano 500ms
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_statement = 'ddl'                   # logga tutti i comandi DDL
log_temp_files = 0                      # logga tutti i file temporanei

# === Autovacuum ===
autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 30s
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.05   # default 0.2, ridurre per tabelle grandi
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.02
```

### Configurazione pg_hba.conf

```
# TYPE  DATABASE    USER        ADDRESS            METHOD
# Connessioni locali via socket Unix
local   all         postgres                       peer
local   all         all                            scram-sha-256

# Connessioni IPv4 locali
host    all         all         127.0.0.1/32       scram-sha-256

# Connessioni dalla rete applicativa
host    app_db      app_user    10.0.1.0/24        scram-sha-256

# Connessioni per la replica
host    replication repl_user   10.0.2.0/24        scram-sha-256

# Rifiuta tutto il resto
host    all         all         0.0.0.0/0          reject
```

### Utenti e Ruoli

```sql
-- Creare un ruolo con login
CREATE ROLE app_user WITH LOGIN PASSWORD 'strong_password_here' VALID UNTIL '2027-01-01';

-- Creare un ruolo di gruppo senza login
CREATE ROLE readonly_group NOLOGIN;

-- Concedere permessi al gruppo
GRANT CONNECT ON DATABASE app_db TO readonly_group;
GRANT USAGE ON SCHEMA public TO readonly_group;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_group;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_group;

-- Assegnare l'utente al gruppo
GRANT readonly_group TO app_user;

-- Ruolo con permessi di scrittura
CREATE ROLE readwrite_group NOLOGIN;
GRANT CONNECT ON DATABASE app_db TO readwrite_group;
GRANT USAGE, CREATE ON SCHEMA public TO readwrite_group;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO readwrite_group;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO readwrite_group;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO readwrite_group;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO readwrite_group;

-- Revocare permessi
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Verificare i permessi
\du                          -- lista ruoli
\dp my_table                 -- permessi su una tabella
SELECT * FROM pg_roles;      -- dettaglio ruoli
```

### Tablespace e Schema Management

```sql
-- Creare un tablespace su un disco dedicato
CREATE TABLESPACE fast_storage LOCATION '/mnt/nvme/pg_data';

-- Creare un database su un tablespace specifico
CREATE DATABASE analytics_db TABLESPACE fast_storage;

-- Creare uno schema per separare i dati
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS archive;

-- Impostare il search_path
ALTER ROLE app_user SET search_path TO app, public;

-- Spostare una tabella su un tablespace diverso
ALTER TABLE large_table SET TABLESPACE fast_storage;
```

### Estensioni Utili

```sql
-- pg_stat_statements — analisi delle query piu eseguite
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-- In postgresql.conf: shared_preload_libraries = 'pg_stat_statements'

SELECT query, calls, total_exec_time, mean_exec_time, rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- pgcrypto — funzioni di crittografia
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SELECT crypt('my_password', gen_salt('bf', 12));

-- PostGIS — dati geospaziali
CREATE EXTENSION IF NOT EXISTS postgis;

-- pg_trgm — ricerca per similarita
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_name_trgm ON users USING gin (name gin_trgm_ops);

-- uuid-ossp — generazione UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SELECT uuid_generate_v4();
```

### Backup: pg_dump e pg_restore

```bash
# Backup logico di un singolo database in formato custom (compresso)
pg_dump -h localhost -U postgres -Fc -f /backup/app_db_$(date +%Y%m%d_%H%M%S).dump app_db

# Backup logico in formato plain SQL
pg_dump -h localhost -U postgres -Fp -f /backup/app_db.sql app_db

# Backup di tabelle specifiche
pg_dump -h localhost -U postgres -Fc -t public.orders -t public.customers -f /backup/tables.dump app_db

# Backup solo dello schema (senza dati)
pg_dump -h localhost -U postgres --schema-only -f /backup/schema.sql app_db

# Backup solo dei dati
pg_dump -h localhost -U postgres --data-only -Fc -f /backup/data.dump app_db

# Backup di tutti i database
pg_dumpall -h localhost -U postgres -f /backup/full_cluster.sql

# Restore da formato custom
pg_restore -h localhost -U postgres -d app_db -C -c /backup/app_db.dump

# Restore parallelo (piu veloce per database grandi)
pg_restore -h localhost -U postgres -d app_db -j 4 /backup/app_db.dump
```

### Point-in-Time Recovery (PITR)

```bash
# Configurazione per PITR in postgresql.conf
# wal_level = replica
# archive_mode = on
# archive_command = 'cp %p /archive/wal/%f'
# restore_command = 'cp /archive/wal/%f %p'

# 1. Eseguire un base backup
pg_basebackup -h localhost -U repl_user -D /backup/base -Fp -Xs -P -R

# 2. Per il restore, creare recovery.signal e configurare
# In postgresql.conf (o postgresql.auto.conf):
# restore_command = 'cp /archive/wal/%f %p'
# recovery_target_time = '2026-04-10 14:30:00'
# recovery_target_action = 'promote'

# 3. Avviare PostgreSQL — eseguira il recovery fino al punto specificato
```

### Monitoring

```sql
-- Sessioni attive e query in esecuzione
SELECT pid, usename, datname, state, query_start, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND pid != pg_backend_pid()
ORDER BY duration DESC;

-- Query bloccate da lock
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.relation = blocked_locks.relation
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Statistiche sulle tabelle
SELECT schemaname, relname, seq_scan, idx_scan, n_tup_ins, n_tup_upd, n_tup_del,
       n_live_tup, n_dead_tup, last_vacuum, last_autovacuum, last_analyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;

-- Dimensione database e tabelle
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database ORDER BY pg_database_size(pg_database.datname) DESC;

SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
       pg_size_pretty(pg_relation_size(relid)) AS table_size,
       pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- Cache hit ratio — dovrebbe essere > 99%
SELECT sum(heap_blks_read) AS heap_read,
       sum(heap_blks_hit) AS heap_hit,
       round(sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read))::numeric, 4) AS ratio
FROM pg_statio_user_tables;

-- Index usage — tabelle con scansioni sequenziali eccessive
SELECT relname, seq_scan, idx_scan,
       CASE WHEN seq_scan + idx_scan > 0
            THEN round(100.0 * idx_scan / (seq_scan + idx_scan), 2)
            ELSE 0 END AS idx_scan_pct
FROM pg_stat_user_tables
WHERE seq_scan + idx_scan > 100
ORDER BY seq_scan DESC;
```

### Comandi psql Essenziali

```
\l                  -- lista database
\c dbname           -- connetti a un database
\dt                 -- lista tabelle
\dt+                -- lista tabelle con dimensioni
\d table_name       -- struttura di una tabella
\di                 -- lista indici
\dn                 -- lista schemi
\du                 -- lista ruoli/utenti
\df                 -- lista funzioni
\dx                 -- lista estensioni installate
\timing on          -- mostra tempo di esecuzione delle query
\x                  -- formato espanso (verticale)
\copy               -- import/export CSV
\watch 5            -- ripeti query ogni 5 secondi
```

---

## 3. PostgreSQL — Replica e High Availability

### Streaming Replication

La streaming replication di PostgreSQL consente di mantenere uno o piu server standby sincronizzati con il server primario tramite il flusso continuo dei record WAL.

**Configurazione sul Primary**:

```ini
# postgresql.conf sul primary
wal_level = replica
max_wal_senders = 10
wal_keep_size = 2GB
max_replication_slots = 10
hot_standby = on
```

```
# pg_hba.conf sul primary
host    replication     repl_user    10.0.0.0/24    scram-sha-256
```

```sql
-- Creare l'utente di replica sul primary
CREATE ROLE repl_user WITH REPLICATION LOGIN PASSWORD 'repl_secure_password';
```

**Setup dello Standby**:

```bash
# Eseguire il base backup dal primary
pg_basebackup -h primary_host -U repl_user -D /var/lib/postgresql/16/main -Fp -Xs -P -R

# Il flag -R crea automaticamente standby.signal e configura primary_conninfo
# in postgresql.auto.conf

# Verificare il contenuto di postgresql.auto.conf
cat /var/lib/postgresql/16/main/postgresql.auto.conf
# primary_conninfo = 'host=primary_host port=5432 user=repl_user password=repl_secure_password'

# Avviare lo standby
sudo systemctl start postgresql
```

### Replication Slots

I replication slot impediscono al primary di rimuovere segmenti WAL che lo standby non ha ancora ricevuto, evitando la necessita di ricostruire lo standby.

```sql
-- Creare un replication slot sul primary
SELECT pg_create_physical_replication_slot('standby1_slot');

-- Verificare i replication slot
SELECT slot_name, slot_type, active, restart_lsn, confirmed_flush_lsn
FROM pg_replication_slots;

-- Configurare lo standby per usare il slot
-- In postgresql.auto.conf o recovery.conf:
-- primary_slot_name = 'standby1_slot'

-- Attenzione: un replication slot per uno standby non connesso causa accumulo WAL
-- Rimuovere slot inutilizzati
SELECT pg_drop_replication_slot('standby1_slot');
```

### Synchronous vs Asynchronous Replication

```ini
# Replica sincrona — il primary attende la conferma dallo standby prima del COMMIT
# Maggiore durabilita, latenza piu alta per le scritture
synchronous_commit = on
synchronous_standby_names = 'FIRST 1 (standby1, standby2)'

# Replica asincrona (default) — il primary non attende conferma
# Latenza minore, rischio di perdita dati in caso di failover
synchronous_commit = on
synchronous_standby_names = ''
```

```sql
-- Verificare lo stato della replica
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replication_lag_bytes,
       sync_state
FROM pg_stat_replication;

-- Sullo standby, verificare il ritardo
SELECT now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

### Patroni per HA Automatizzata

Patroni e un template per PostgreSQL HA che gestisce automaticamente failover, switchover e configurazione della replica. Utilizza un Distributed Configuration Store (DCS) come etcd, Consul o ZooKeeper per il leader election.

```yaml
# /etc/patroni/patroni.yml
scope: pg-cluster-prod
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: 10.0.1.1:8008

etcd3:
  hosts:
    - 10.0.0.1:2379
    - 10.0.0.2:2379
    - 10.0.0.3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576  # 1MB
    synchronous_mode: true
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 200
        shared_buffers: 4GB
        effective_cache_size: 12GB
        work_mem: 64MB
        maintenance_work_mem: 1GB
        wal_level: replica
        max_wal_senders: 10
        max_replication_slots: 10
        hot_standby: on
        wal_log_hints: on

  initdb:
    - encoding: UTF8
    - data-checksums

  pg_hba:
    - host replication replicator 10.0.0.0/24 scram-sha-256
    - host all all 10.0.0.0/24 scram-sha-256

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.1.1:5432
  data_dir: /var/lib/postgresql/16/main
  authentication:
    superuser:
      username: postgres
      password: postgres_password
    replication:
      username: replicator
      password: repl_password
    rewind:
      username: rewind_user
      password: rewind_password
```

```bash
# Comandi Patroni
patronictl -c /etc/patroni/patroni.yml list          # stato del cluster
patronictl -c /etc/patroni/patroni.yml switchover     # switchover manuale
patronictl -c /etc/patroni/patroni.yml failover       # failover forzato
patronictl -c /etc/patroni/patroni.yml reinit node2   # reinizializzare un nodo
patronictl -c /etc/patroni/patroni.yml edit-config     # modificare configurazione
```

### pgBouncer per Connection Pooling

pgBouncer e un connection pooler leggero che riduce il numero di connessioni reali a PostgreSQL, fondamentale per applicazioni con molte connessioni concorrenti.

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
app_db = host=127.0.0.1 port=5432 dbname=app_db

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Modalita di pooling:
# session  — una connessione per sessione client (meno efficiente)
# transaction — una connessione per transazione (consigliato)
# statement — una connessione per statement (limitazioni con transazioni multi-statement)
pool_mode = transaction

# Limiti connessioni
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3

# Timeouts
server_idle_timeout = 300
client_idle_timeout = 0
query_timeout = 0
query_wait_timeout = 120

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60
```

### PgPool-II

PgPool-II offre funzionalita aggiuntive rispetto a pgBouncer: load balancing delle query in lettura, query caching, e watchdog per HA del pooler stesso.

```ini
# /etc/pgpool2/pgpool.conf
backend_hostname0 = 'primary_host'
backend_port0 = 5432
backend_weight0 = 1
backend_flag0 = 'ALWAYS_PRIMARY'

backend_hostname1 = 'standby1_host'
backend_port1 = 5432
backend_weight1 = 1
backend_flag1 = 'DISALLOW_TO_FAILOVER'

# Load balancing — invia le SELECT agli standby
load_balance_mode = on
statement_level_load_balance = on

# Connection pooling
num_init_children = 32
max_pool = 4
connection_cache = on

# Health check
health_check_period = 10
health_check_timeout = 20
health_check_max_retries = 3
```

### Logical Replication

La logical replication consente la replica selettiva di tabelle o gruppi di tabelle, utile per migrazioni, aggregazione dati e upgrade con zero downtime.

```sql
-- Sul publisher (sorgente)
-- wal_level = logical (in postgresql.conf)

CREATE PUBLICATION my_pub FOR TABLE orders, customers;
-- oppure tutte le tabelle
CREATE PUBLICATION all_tables_pub FOR ALL TABLES;

-- Sul subscriber (destinazione)
CREATE SUBSCRIPTION my_sub
    CONNECTION 'host=publisher_host port=5432 dbname=app_db user=repl_user password=repl_pass'
    PUBLICATION my_pub;

-- Verificare lo stato della subscription
SELECT subname, subenabled, subconninfo FROM pg_subscription;
SELECT * FROM pg_stat_subscription;

-- Verificare lo stato della publication
SELECT * FROM pg_publication;
SELECT * FROM pg_stat_replication WHERE application_name = 'my_sub';
```

### PostgreSQL su Kubernetes

**CloudNativePG** e l'operatore nativo per PostgreSQL su Kubernetes, sviluppato da EDB.

```yaml
# CloudNativePG Cluster
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: pg-cluster-prod
  namespace: databases
spec:
  instances: 3
  postgresql:
    parameters:
      shared_buffers: "4GB"
      effective_cache_size: "12GB"
      work_mem: "64MB"
      maintenance_work_mem: "1GB"
      max_connections: "200"
      log_min_duration_statement: "500"
  bootstrap:
    initdb:
      database: app_db
      owner: app_user
  storage:
    size: 100Gi
    storageClass: fast-ssd
  backup:
    barmanObjectStore:
      destinationPath: "s3://pg-backups/prod"
      s3Credentials:
        accessKeyId:
          name: aws-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: aws-creds
          key: SECRET_ACCESS_KEY
      wal:
        compression: gzip
    retentionPolicy: "30d"
  monitoring:
    enablePodMonitor: true
  resources:
    requests:
      memory: "8Gi"
      cpu: "2"
    limits:
      memory: "16Gi"
      cpu: "4"
```

**Zalando Postgres Operator**:

```yaml
apiVersion: acid.zalan.do/v1
kind: postgresql
metadata:
  name: pg-cluster-prod
  namespace: databases
spec:
  teamId: "platform"
  numberOfInstances: 3
  volume:
    size: 100Gi
    storageClass: fast-ssd
  postgresql:
    version: "16"
    parameters:
      shared_buffers: "4GB"
      work_mem: "64MB"
  patroni:
    synchronous_mode: true
    synchronous_node_count: 1
  users:
    app_user:
      - superuser
      - createdb
  databases:
    app_db: app_user
  resources:
    requests:
      cpu: "2"
      memory: "8Gi"
    limits:
      cpu: "4"
      memory: "16Gi"
```

---

## 4. MySQL/MariaDB — Amministrazione

### Installazione

```bash
# MySQL 8.x su Debian/Ubuntu
wget https://dev.mysql.com/get/mysql-apt-config_0.8.30-1_all.deb
sudo dpkg -i mysql-apt-config_0.8.30-1_all.deb
sudo apt-get update
sudo apt-get install -y mysql-server

# MariaDB 11.x su Debian/Ubuntu
sudo apt-get install -y mariadb-server mariadb-client

# RHEL/CentOS/Rocky — MySQL
sudo dnf install -y mysql-server
sudo systemctl enable --now mysqld

# Configurazione iniziale di sicurezza
sudo mysql_secure_installation
# Imposta password root, rimuove utenti anonimi, disabilita login root remoto,
# rimuove database test

# Verifica
mysql --version
mysql -u root -p -e "SELECT VERSION();"
```

### Architettura InnoDB

InnoDB e il motore di storage predefinito in MySQL e MariaDB. Comprendere la sua architettura e fondamentale per il tuning.

**Buffer Pool**: area di memoria dove InnoDB memorizza le pagine dei dati e degli indici. E il parametro piu importante per le performance. Si consiglia di impostarlo al 70-80% della RAM disponibile su un server dedicato.

**Redo Log (WAL di InnoDB)**: registra le modifiche ai dati prima che vengano scritte su disco. Garantisce la durabilita e il recovery dopo crash. Configurato tramite `innodb_redo_log_capacity` (MySQL 8.0.30+) o `innodb_log_file_size` e `innodb_log_files_in_group` (versioni precedenti).

**Binary Log (binlog)**: registra tutte le modifiche ai dati a livello di istruzioni SQL (statement-based) o di righe modificate (row-based). Utilizzato per la replica e il point-in-time recovery.

**Doublewrite Buffer**: meccanismo di protezione che scrive le pagine in un'area temporanea prima di applicarle alla loro posizione finale, prevenendo corruzioni in caso di crash durante la scrittura.

### Configurazione my.cnf

```ini
[mysqld]
# === Identificazione ===
server-id = 1
port = 3306
bind-address = 0.0.0.0
datadir = /var/lib/mysql
socket = /var/run/mysqld/mysqld.sock

# === InnoDB Buffer Pool ===
innodb_buffer_pool_size = 12G           # 70-80% RAM su server dedicato
innodb_buffer_pool_instances = 8        # 1 istanza per GB di buffer pool (max 64)
innodb_buffer_pool_dump_at_shutdown = ON
innodb_buffer_pool_load_at_startup = ON

# === InnoDB Redo Log ===
innodb_redo_log_capacity = 4G           # MySQL 8.0.30+
innodb_flush_log_at_trx_commit = 1      # 1=sicuro (ACID), 2=flush ogni secondo
innodb_flush_method = O_DIRECT          # evita double buffering con OS cache

# === InnoDB I/O ===
innodb_io_capacity = 2000               # IOPS per operazioni background (SSD)
innodb_io_capacity_max = 4000
innodb_read_io_threads = 8
innodb_write_io_threads = 8

# === Connessioni ===
max_connections = 500
max_connect_errors = 100
wait_timeout = 600
interactive_timeout = 600
thread_cache_size = 50

# === Binary Log ===
log_bin = mysql-bin
binlog_format = ROW                     # ROW e il formato consigliato
binlog_expire_logs_seconds = 604800     # 7 giorni
sync_binlog = 1                         # sincrono — sicuro ma piu lento
binlog_row_image = MINIMAL              # riduce dimensione binlog

# === Query Cache (deprecato in MySQL 8, disponibile in MariaDB) ===
# query_cache_type = 0                  # disabilitato — usare cache applicativa

# === Slow Query Log ===
slow_query_log = ON
slow_query_log_file = /var/log/mysql/slow-query.log
long_query_time = 1                     # query piu lente di 1 secondo
log_queries_not_using_indexes = ON
min_examined_row_limit = 1000

# === Temporary Tables ===
tmp_table_size = 256M
max_heap_table_size = 256M
tmpdir = /tmp

# === Performance Schema ===
performance_schema = ON
performance_schema_max_table_instances = 500

# === Sicurezza ===
local_infile = OFF
skip_name_resolve = ON
default_authentication_plugin = caching_sha2_password
```

### Utenti e Permessi

```sql
-- Creare un utente con autenticazione sicura
CREATE USER 'app_user'@'10.0.1.%'
    IDENTIFIED WITH caching_sha2_password BY 'strong_password_here'
    PASSWORD EXPIRE INTERVAL 90 DAY
    FAILED_LOGIN_ATTEMPTS 5
    PASSWORD_LOCK_TIME 1;

-- Concedere permessi specifici
GRANT SELECT, INSERT, UPDATE, DELETE ON app_db.* TO 'app_user'@'10.0.1.%';

-- Utente read-only per reporting
CREATE USER 'report_user'@'10.0.2.%' IDENTIFIED BY 'report_password';
GRANT SELECT ON app_db.* TO 'report_user'@'10.0.2.%';

-- Utente per backup
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'backup_password';
GRANT SELECT, RELOAD, LOCK TABLES, REPLICATION CLIENT, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'backup_user'@'localhost';

-- Utente per la replica
CREATE USER 'repl_user'@'10.0.0.%' IDENTIFIED BY 'repl_password';
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'10.0.0.%';

-- Verificare i permessi
SHOW GRANTS FOR 'app_user'@'10.0.1.%';

-- Revocare permessi
REVOKE DELETE ON app_db.* FROM 'app_user'@'10.0.1.%';

-- Applicare le modifiche
FLUSH PRIVILEGES;
```

### Backup con mysqldump e xtrabackup

```bash
# mysqldump — backup logico
# Backup completo con metadati di posizione per la replica
mysqldump -u backup_user -p \
    --all-databases \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --source-data=2 \
    --flush-logs \
    | gzip > /backup/full_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup di un singolo database
mysqldump -u backup_user -p \
    --single-transaction \
    --routines --triggers \
    app_db > /backup/app_db.sql

# Restore da mysqldump
mysql -u root -p app_db < /backup/app_db.sql
zcat /backup/full.sql.gz | mysql -u root -p

# Percona XtraBackup — backup fisico (piu veloce per database grandi)
# Backup completo
xtrabackup --backup --user=backup_user --password=backup_pass \
    --target-dir=/backup/base

# Preparare il backup per il restore
xtrabackup --prepare --target-dir=/backup/base

# Backup incrementale
xtrabackup --backup --user=backup_user --password=backup_pass \
    --target-dir=/backup/inc1 \
    --incremental-basedir=/backup/base

# Preparare backup incrementale
xtrabackup --prepare --apply-log-only --target-dir=/backup/base
xtrabackup --prepare --apply-log-only --target-dir=/backup/base \
    --incremental-dir=/backup/inc1

# Restore con xtrabackup
sudo systemctl stop mysqld
xtrabackup --copy-back --target-dir=/backup/base --datadir=/var/lib/mysql
sudo chown -R mysql:mysql /var/lib/mysql
sudo systemctl start mysqld
```

### Performance Schema e Slow Query Log

```sql
-- Attivare e analizzare il Performance Schema
-- Query piu costose per tempo totale
SELECT DIGEST_TEXT, COUNT_STAR, SUM_TIMER_WAIT/1000000000000 AS total_latency_sec,
       AVG_TIMER_WAIT/1000000000 AS avg_latency_ms, SUM_ROWS_EXAMINED, SUM_ROWS_SENT
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;

-- Tabelle con piu I/O
SELECT OBJECT_SCHEMA, OBJECT_NAME,
       COUNT_READ, COUNT_WRITE, COUNT_FETCH,
       SUM_TIMER_WAIT/1000000000000 AS total_latency_sec
FROM performance_schema.table_io_waits_summary_by_table
WHERE OBJECT_SCHEMA NOT IN ('performance_schema', 'mysql', 'sys')
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 20;

-- Connessioni per utente/host
SELECT USER, HOST, CURRENT_CONNECTIONS, TOTAL_CONNECTIONS
FROM performance_schema.accounts
WHERE USER IS NOT NULL
ORDER BY CURRENT_CONNECTIONS DESC;

-- Analizzare lo slow query log con mysqldumpslow
mysqldumpslow -s t -t 20 /var/log/mysql/slow-query.log

-- Analizzare con pt-query-digest (Percona Toolkit)
pt-query-digest /var/log/mysql/slow-query.log > /tmp/slow_report.txt
```

### Indici e EXPLAIN

```sql
-- Creare indici efficaci
CREATE INDEX idx_orders_customer_date ON orders (customer_id, order_date);
CREATE INDEX idx_orders_status ON orders (status) WHERE status != 'completed';

-- Analizzare il piano di esecuzione
EXPLAIN FORMAT=TREE
SELECT o.id, o.order_date, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending' AND o.order_date > '2026-01-01';

-- EXPLAIN ANALYZE — esegue realmente la query e mostra tempi reali
EXPLAIN ANALYZE
SELECT o.id, o.order_date, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending' AND o.order_date > '2026-01-01';

-- Indici inutilizzati
SELECT s.TABLE_SCHEMA, s.TABLE_NAME, s.INDEX_NAME, s.COLUMN_NAME
FROM information_schema.STATISTICS s
LEFT JOIN performance_schema.table_io_waits_summary_by_index_usage p
    ON s.TABLE_SCHEMA = p.OBJECT_SCHEMA
    AND s.TABLE_NAME = p.OBJECT_NAME
    AND s.INDEX_NAME = p.INDEX_NAME
WHERE p.COUNT_STAR = 0 AND s.INDEX_NAME != 'PRIMARY'
    AND s.TABLE_SCHEMA NOT IN ('mysql', 'performance_schema', 'sys');
```

---

## 5. MySQL/MariaDB — Replica e High Availability

### Source-Replica Replication

La replica tradizionale MySQL utilizza il binary log. Il server source (precedentemente "master") scrive le modifiche nel binlog, e il server replica (precedentemente "slave") le legge e le applica.

```ini
# my.cnf sul source
[mysqld]
server-id = 1
log_bin = mysql-bin
binlog_format = ROW
binlog_expire_logs_seconds = 604800
sync_binlog = 1
innodb_flush_log_at_trx_commit = 1
```

```ini
# my.cnf sulla replica
[mysqld]
server-id = 2
relay_log = relay-bin
read_only = ON
super_read_only = ON
log_bin = mysql-bin            # se la replica deve essere a sua volta source
log_replica_updates = ON       # propaga gli update nel suo binlog
```

```sql
-- Sul source: creare l'utente di replica
CREATE USER 'repl_user'@'10.0.0.%' IDENTIFIED BY 'repl_password';
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'10.0.0.%';

-- Sulla replica: configurare e avviare la replica
CHANGE REPLICATION SOURCE TO
    SOURCE_HOST = 'source_host',
    SOURCE_PORT = 3306,
    SOURCE_USER = 'repl_user',
    SOURCE_PASSWORD = 'repl_password',
    SOURCE_AUTO_POSITION = 1,        -- richiede GTID
    GET_SOURCE_PUBLIC_KEY = 1;

START REPLICA;

-- Verificare lo stato della replica
SHOW REPLICA STATUS\G
-- Controllare: Replica_IO_Running = Yes, Replica_SQL_Running = Yes,
-- Seconds_Behind_Source = 0 (ideale)
```

### GTID-Based Replication

Global Transaction Identifiers (GTID) assegnano un identificatore unico a ogni transazione, semplificando la gestione della replica e il failover.

```ini
# my.cnf — sia su source che replica
[mysqld]
gtid_mode = ON
enforce_gtid_consistency = ON
```

```sql
-- Verificare GTID
SELECT @@GLOBAL.gtid_executed;
SELECT @@GLOBAL.gtid_purged;

-- Sulla replica con GTID
CHANGE REPLICATION SOURCE TO
    SOURCE_HOST = 'source_host',
    SOURCE_USER = 'repl_user',
    SOURCE_PASSWORD = 'repl_password',
    SOURCE_AUTO_POSITION = 1;

START REPLICA;

-- Vantaggi GTID:
-- 1. Failover semplificato — la replica sa esattamente quale transazione ha applicato
-- 2. Non serve specificare binlog file e position manualmente
-- 3. Verifica di consistenza automatica tra source e replica
```

### Group Replication e InnoDB Cluster

MySQL Group Replication fornisce replica sincrona multi-master con conflict detection automatico e membership management.

```ini
# my.cnf per Group Replication
[mysqld]
server-id = 1
gtid_mode = ON
enforce_gtid_consistency = ON
binlog_checksum = NONE
log_bin = mysql-bin
binlog_format = ROW
log_replica_updates = ON
relay_log = relay-bin

# Group Replication
plugin_load_add = 'group_replication.so'
group_replication_group_name = "aaaa1111-bbbb-cccc-dddd-eeee2222ffff"
group_replication_start_on_boot = OFF
group_replication_local_address = "10.0.1.1:33061"
group_replication_group_seeds = "10.0.1.1:33061,10.0.1.2:33061,10.0.1.3:33061"
group_replication_single_primary_mode = ON
```

```sql
-- Avviare il primo nodo (bootstrap)
SET GLOBAL group_replication_bootstrap_group = ON;
START GROUP_REPLICATION;
SET GLOBAL group_replication_bootstrap_group = OFF;

-- Avviare i nodi successivi
START GROUP_REPLICATION;

-- Verificare lo stato del gruppo
SELECT MEMBER_ID, MEMBER_HOST, MEMBER_PORT, MEMBER_STATE, MEMBER_ROLE
FROM performance_schema.replication_group_members;
```

**InnoDB Cluster** combina Group Replication, MySQL Shell e MySQL Router per una soluzione HA completa:

```bash
# MySQL Shell — creare un cluster
mysqlsh root@primary_host

# Nella shell interattiva
dba.configureInstance('root@10.0.1.1:3306')
dba.configureInstance('root@10.0.1.2:3306')
dba.configureInstance('root@10.0.1.3:3306')

var cluster = dba.createCluster('prodCluster')
cluster.addInstance('root@10.0.1.2:3306')
cluster.addInstance('root@10.0.1.3:3306')
cluster.status()
```

### MySQL Router

MySQL Router e un middleware leggero che fornisce routing trasparente delle connessioni verso il cluster InnoDB, separando letture e scritture.

```ini
# /etc/mysqlrouter/mysqlrouter.conf
[routing:primary]
bind_address = 0.0.0.0
bind_port = 6446
destinations = metadata-cache://prodCluster/?role=PRIMARY
routing_strategy = first-available
protocol = classic

[routing:secondary]
bind_address = 0.0.0.0
bind_port = 6447
destinations = metadata-cache://prodCluster/?role=SECONDARY
routing_strategy = round-robin-with-fallback
protocol = classic

[metadata_cache:prodCluster]
cluster_type = gr
router_id = 1
user = mysql_router_user
metadata_cluster = prodCluster
ttl = 0.5
```

```bash
# Bootstrap del router (configurazione automatica dal cluster)
mysqlrouter --bootstrap root@primary_host:3306 --directory /etc/mysqlrouter --user=mysqlrouter

# Connessione applicativa
# Scritture: mysql -h router_host -P 6446 -u app_user -p
# Letture:   mysql -h router_host -P 6447 -u app_user -p
```

### MariaDB Galera Cluster

Galera Cluster fornisce replica sincrona multi-master per MariaDB con certificazione delle transazioni basata su group communication.

```ini
# /etc/mysql/mariadb.conf.d/60-galera.cnf
[galera]
wsrep_on = ON
wsrep_provider = /usr/lib/galera/libgalera_smm.so
wsrep_cluster_name = "galera_prod"
wsrep_cluster_address = "gcomm://10.0.1.1,10.0.1.2,10.0.1.3"
wsrep_node_address = "10.0.1.1"
wsrep_node_name = "node1"
wsrep_sst_method = mariabackup
wsrep_sst_auth = "sst_user:sst_password"

# InnoDB richiesto per Galera
default_storage_engine = InnoDB
innodb_autoinc_lock_mode = 2       # obbligatorio per Galera
innodb_flush_log_at_trx_commit = 2 # compromesso sicurezza/performance per Galera

binlog_format = ROW                # obbligatorio
```

```bash
# Bootstrap del primo nodo
galera_new_cluster

# Avviare i nodi successivi
sudo systemctl start mariadb

# Verificare lo stato del cluster
mysql -u root -p -e "SHOW STATUS LIKE 'wsrep_%';"
# Verificare: wsrep_cluster_size, wsrep_cluster_status, wsrep_ready, wsrep_connected
```

### ProxySQL

ProxySQL e un proxy SQL ad alte performance per MySQL che offre connection pooling, query routing, query caching e failover automatico.

```bash
# Installazione
wget https://github.com/sysown/proxysql/releases/download/v2.6.0/proxysql_2.6.0-ubuntu22_amd64.deb
sudo dpkg -i proxysql_2.6.0-ubuntu22_amd64.deb
sudo systemctl start proxysql

# Connessione all'interfaccia di amministrazione (porta 6032)
mysql -u admin -padmin -h 127.0.0.1 -P 6032 --prompt='ProxySQL> '
```

```sql
-- Configurazione backend servers
INSERT INTO mysql_servers (hostgroup_id, hostname, port, weight, max_connections) VALUES
    (10, '10.0.1.1', 3306, 1, 100),   -- writer (hostgroup 10)
    (20, '10.0.1.2', 3306, 1, 100),   -- reader (hostgroup 20)
    (20, '10.0.1.3', 3306, 1, 100);   -- reader (hostgroup 20)

-- Configurazione utenti
INSERT INTO mysql_users (username, password, default_hostgroup, max_connections) VALUES
    ('app_user', 'app_password', 10, 200);

-- Query routing rules
-- Inviare SELECT (non FOR UPDATE) ai reader
INSERT INTO mysql_query_rules (rule_id, active, match_pattern, destination_hostgroup, apply) VALUES
    (1, 1, '^SELECT .* FOR UPDATE$', 10, 1),
    (2, 1, '^SELECT', 20, 1);

-- Applicare la configurazione
LOAD MYSQL SERVERS TO RUNTIME;
LOAD MYSQL USERS TO RUNTIME;
LOAD MYSQL QUERY RULES TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
SAVE MYSQL USERS TO DISK;
SAVE MYSQL QUERY RULES TO DISK;

-- Monitoraggio
SELECT hostgroup, srv_host, srv_port, status, ConnUsed, ConnFree, ConnOK, ConnERR, Queries
FROM stats_mysql_connection_pool;
```

---

## 6. Redis — Amministrazione e Architettura

### Data Structures

Redis non e un semplice key-value store. Offre strutture dati native server-side che consentono operazioni atomiche e ad alta performance.

**Strings**: tipo base, supporta valori fino a 512 MB. Utilizzato per cache, contatori, sessioni.

```bash
redis-cli SET user:1001:name "Mario Rossi"
redis-cli GET user:1001:name
redis-cli INCR page:views                # incremento atomico
redis-cli INCRBY page:views 10
redis-cli SETNX lock:resource "owner1"   # SET if Not eXists — per distributed locking
redis-cli SET session:abc123 "data" EX 3600  # scade dopo 1 ora
redis-cli MSET key1 "v1" key2 "v2" key3 "v3"  # set multiplo
redis-cli MGET key1 key2 key3
```

**Hashes**: mappe di campi-valore associate a una chiave. Efficienti per oggetti con molti attributi.

```bash
redis-cli HSET user:1001 name "Mario" surname "Rossi" email "mario@example.com" age 35
redis-cli HGET user:1001 name
redis-cli HGETALL user:1001
redis-cli HINCRBY user:1001 age 1        # incremento atomico di un campo
redis-cli HDEL user:1001 email
redis-cli HLEN user:1001
```

**Lists**: liste ordinate di stringhe, implementate come linked list. Supportano push/pop da entrambi i lati.

```bash
redis-cli LPUSH queue:tasks "task1" "task2" "task3"  # push a sinistra
redis-cli RPUSH queue:tasks "task4"                   # push a destra
redis-cli LPOP queue:tasks                             # pop da sinistra
redis-cli RPOP queue:tasks                             # pop da destra
redis-cli LRANGE queue:tasks 0 -1                      # tutti gli elementi
redis-cli LLEN queue:tasks
redis-cli BRPOP queue:tasks 30                         # blocking pop (timeout 30s)
```

**Sets**: collezioni non ordinate di stringhe uniche. Supportano operazioni insiemistiche.

```bash
redis-cli SADD tags:article:1 "database" "redis" "nosql"
redis-cli SADD tags:article:2 "database" "postgresql" "sql"
redis-cli SMEMBERS tags:article:1
redis-cli SINTER tags:article:1 tags:article:2        # intersezione
redis-cli SUNION tags:article:1 tags:article:2        # unione
redis-cli SDIFF tags:article:1 tags:article:2         # differenza
redis-cli SISMEMBER tags:article:1 "redis"            # appartenenza
redis-cli SCARD tags:article:1                         # cardinalita
```

**Sorted Sets**: set con uno score numerico per ogni elemento, mantenuti ordinati per score.

```bash
redis-cli ZADD leaderboard 1500 "player1" 2300 "player2" 1800 "player3"
redis-cli ZRANGE leaderboard 0 -1 WITHSCORES          # dal piu basso
redis-cli ZREVRANGE leaderboard 0 2 WITHSCORES         # top 3
redis-cli ZINCRBY leaderboard 100 "player1"            # incremento score
redis-cli ZRANK leaderboard "player2"                  # posizione (0-based)
redis-cli ZRANGEBYSCORE leaderboard 1000 2000          # range per score
redis-cli ZCOUNT leaderboard 1000 2000                 # conteggio nel range
```

**Streams**: struttura append-only simile a un log, ideale per event sourcing e messaging.

```bash
redis-cli XADD orders:stream "*" product "laptop" quantity 1 price 999
redis-cli XADD orders:stream "*" product "mouse" quantity 2 price 25
redis-cli XLEN orders:stream
redis-cli XRANGE orders:stream - +                     # tutti gli eventi
redis-cli XRANGE orders:stream - + COUNT 10            # ultimi 10
# Consumer group
redis-cli XGROUP CREATE orders:stream processing $ MKSTREAM
redis-cli XREADGROUP GROUP processing consumer1 COUNT 5 BLOCK 5000 STREAMS orders:stream >
redis-cli XACK orders:stream processing "1234567890-0" # acknowledge
```

**HyperLogLog**: struttura probabilistica per conteggio di elementi unici con memoria costante (~12 KB).

```bash
redis-cli PFADD visitors:2026-04-11 "user1" "user2" "user3" "user1"
redis-cli PFCOUNT visitors:2026-04-11                  # restituisce 3 (stima)
redis-cli PFMERGE visitors:week visitors:2026-04-11 visitors:2026-04-10
```

### Persistenza: RDB vs AOF vs Hybrid

**RDB (Redis Database Snapshot)**: salva snapshot periodici dell'intero dataset su disco. Compatto, veloce nel restore, ma rischio di perdita dati tra uno snapshot e l'altro.

**AOF (Append-Only File)**: registra ogni operazione di scrittura in un log. Maggiore durabilita, file piu grande, restore piu lento.

**Hybrid**: combina RDB e AOF. Il file AOF contiene uno snapshot RDB iniziale seguito dalle operazioni successive.

```ini
# redis.conf — Persistenza

# RDB
save 900 1                              # snapshot se almeno 1 chiave modificata in 900s
save 300 10                             # snapshot se almeno 10 chiavi modificate in 300s
save 60 10000                           # snapshot se almeno 10000 chiavi modificate in 60s
dbfilename dump.rdb
dir /var/lib/redis

# AOF
appendonly yes
appendfilename "appendonly.aof"
# appendfsync options:
# always  — fsync ad ogni scrittura (piu sicuro, piu lento)
# everysec — fsync ogni secondo (compromesso consigliato)
# no      — fsync gestito dal kernel
appendfsync everysec

# Hybrid (Redis 4.0+)
aof-use-rdb-preamble yes

# Riscrittura AOF automatica
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

### Configurazione redis.conf

```ini
# === Rete ===
bind 10.0.1.1 127.0.0.1
port 6379
protected-mode yes
tcp-backlog 511
timeout 300
tcp-keepalive 300

# === Memoria ===
maxmemory 8gb
# Eviction policies:
# noeviction      — restituisce errore quando la memoria e piena
# allkeys-lru     — rimuove le chiavi usate meno recentemente (consigliato per cache)
# volatile-lru    — rimuove chiavi con TTL usate meno recentemente
# allkeys-lfu     — rimuove le chiavi usate meno frequentemente
# volatile-lfu    — rimuove chiavi con TTL usate meno frequentemente
# allkeys-random  — rimuove chiavi casuali
# volatile-ttl    — rimuove chiavi con TTL piu breve
maxmemory-policy allkeys-lru
maxmemory-samples 10                   # precisione dell'algoritmo LRU

# === Sicurezza ===
requirepass strong_redis_password
# ACL per utenti (Redis 6+)
# user app_user on >app_password ~app:* &* +@all -@admin
# user readonly_user on >ro_password ~* &* +@read -@write -@admin

# === Performance ===
hz 10                                   # frequenza task background (default 10)
dynamic-hz yes
lazyfree-lazy-eviction yes              # rimozione asincrona per eviction
lazyfree-lazy-expire yes                # rimozione asincrona per scadenza TTL
lazyfree-lazy-server-del yes
io-threads 4                            # I/O threading (Redis 6+)
io-threads-do-reads yes

# === Logging ===
loglevel notice
logfile /var/log/redis/redis-server.log

# === Limiti ===
maxclients 10000
```

### Redis Sentinel per HA

Redis Sentinel fornisce monitoring, notifica e failover automatico per Redis.

```ini
# /etc/redis/sentinel.conf
port 26379
sentinel monitor mymaster 10.0.1.1 6379 2     # quorum di 2 Sentinel per failover
sentinel auth-pass mymaster strong_redis_password
sentinel down-after-milliseconds mymaster 5000  # ms senza risposta prima di SDOWN
sentinel failover-timeout mymaster 60000        # timeout failover in ms
sentinel parallel-syncs mymaster 1              # repliche sincronizzate in parallelo
sentinel deny-scripts-reconfig yes
```

```bash
# Avviare Sentinel (almeno 3 istanze)
redis-sentinel /etc/redis/sentinel.conf

# Verificare lo stato
redis-cli -p 26379 SENTINEL masters
redis-cli -p 26379 SENTINEL replicas mymaster
redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
redis-cli -p 26379 SENTINEL ckquorum mymaster
```

### Redis Cluster per Sharding

Redis Cluster distribuisce automaticamente i dati su piu nodi usando hash slot (16384 slot totali). Ogni nodo gestisce un sottoinsieme degli slot.

```bash
# Creare un cluster con 3 master e 3 replica
redis-cli --cluster create \
    10.0.1.1:6379 10.0.1.2:6379 10.0.1.3:6379 \
    10.0.1.4:6379 10.0.1.5:6379 10.0.1.6:6379 \
    --cluster-replicas 1

# Verificare lo stato del cluster
redis-cli -c -h 10.0.1.1 CLUSTER INFO
redis-cli -c -h 10.0.1.1 CLUSTER NODES

# Aggiungere un nodo al cluster
redis-cli --cluster add-node 10.0.1.7:6379 10.0.1.1:6379

# Resharding — spostare slot a un nuovo nodo
redis-cli --cluster reshard 10.0.1.1:6379

# Connessione al cluster (flag -c per il redirect automatico)
redis-cli -c -h 10.0.1.1 -p 6379
```

### Redis come Cache vs Data Store vs Message Broker

**Cache**: dati con TTL, eviction policy aggressiva, no persistenza necessaria. Pattern cache-aside, write-through, write-behind.

**Data Store**: persistenza abilitata (AOF everysec o always), backup regolari, nessuna eviction (noeviction policy). Usato per sessioni, contatori, classifiche.

**Message Broker**: utilizzo di Streams o Pub/Sub per comunicazione asincrona tra servizi. Streams forniscono persistenza e consumer group; Pub/Sub e fire-and-forget.

### Monitoring

```bash
# Statistiche generali
redis-cli INFO

# Sezioni specifiche
redis-cli INFO server
redis-cli INFO memory
redis-cli INFO stats
redis-cli INFO replication
redis-cli INFO keyspace

# Metriche chiave da monitorare:
# used_memory / maxmemory — utilizzo memoria
# connected_clients — numero connessioni attive
# instantaneous_ops_per_sec — throughput corrente
# keyspace_hits / keyspace_misses — cache hit ratio
# evicted_keys — chiavi rimosse per eviction
# rdb_last_bgsave_status — stato ultimo backup

# Monitor in tempo reale (attenzione: impatta le performance)
redis-cli MONITOR

# Slow log — query lente
redis-cli SLOWLOG GET 20                # ultime 20 query lente
redis-cli SLOWLOG LEN                   # numero di entry
redis-cli CONFIG SET slowlog-log-slower-than 10000  # soglia in microsecondi

# Latenza
redis-cli --latency                     # test latenza continuo
redis-cli --latency-history             # storico latenza
redis-cli --latency-dist                # distribuzione latenza
redis-cli LATENCY LATEST                # ultimi eventi di latenza

# Analisi delle chiavi
redis-cli --bigkeys                     # trova le chiavi piu grandi
redis-cli --memkeys                     # analisi memoria per chiave
redis-cli MEMORY USAGE key_name         # memoria usata da una chiave
redis-cli DBSIZE                        # numero totale di chiavi
redis-cli SCAN 0 MATCH "user:*" COUNT 100  # iterazione sicura sulle chiavi
```

---

## 7. MongoDB — Amministrazione

### Architettura e Document Model

MongoDB e un database document-oriented che memorizza dati in documenti BSON (Binary JSON). I documenti sono raggruppati in collection, che a loro volta risiedono in database. A differenza dei database relazionali, MongoDB non richiede uno schema fisso: ogni documento in una collection puo avere una struttura diversa.

**BSON** supporta tipi aggiuntivi rispetto a JSON: Date, ObjectId, Binary Data, Decimal128, Regular Expression, e altri. Il limite massimo di un documento e 16 MB.

### Installazione

```bash
# MongoDB 7.x su Ubuntu
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Avviare e abilitare il servizio
sudo systemctl enable --now mongod

# Verificare
mongosh --eval "db.version()"
```

### Configurazione mongod.conf

```yaml
# /etc/mongod.conf
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 8                   # 50% RAM - 1GB (formula consigliata)
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen

net:
  port: 27017
  bindIp: 127.0.0.1,10.0.1.1
  maxIncomingConnections: 1000
  tls:
    mode: requireTLS
    certificateKeyFile: /etc/ssl/mongodb.pem
    CAFile: /etc/ssl/ca.pem

security:
  authorization: enabled
  keyFile: /etc/mongodb/keyfile          # per la replica set authentication

operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100

replication:
  replSetName: "rs-prod"
  oplogSizeMB: 10240
```

### mongosh — Operazioni Base

```javascript
// Connessione
mongosh "mongodb://admin_user:password@10.0.1.1:27017/admin"

// Database management
show dbs
use app_db
db.stats()
db.dropDatabase()    // ATTENZIONE: operazione distruttiva

// Collection management
show collections
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customer_id", "items", "total", "created_at"],
      properties: {
        customer_id: { bsonType: "objectId" },
        items: { bsonType: "array", minItems: 1 },
        total: { bsonType: "decimal", minimum: 0 },
        status: { enum: ["pending", "processing", "shipped", "delivered", "cancelled"] },
        created_at: { bsonType: "date" }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
});

// CRUD
db.orders.insertOne({
  customer_id: ObjectId("507f1f77bcf86cd799439011"),
  items: [{ product: "laptop", qty: 1, price: NumberDecimal("999.99") }],
  total: NumberDecimal("999.99"),
  status: "pending",
  created_at: new Date()
});

db.orders.insertMany([
  { customer_id: ObjectId("507f1f77bcf86cd799439012"), items: [{product: "mouse", qty: 2, price: NumberDecimal("25.00")}], total: NumberDecimal("50.00"), status: "pending", created_at: new Date() },
  { customer_id: ObjectId("507f1f77bcf86cd799439013"), items: [{product: "keyboard", qty: 1, price: NumberDecimal("75.00")}], total: NumberDecimal("75.00"), status: "shipped", created_at: new Date() }
]);

// Query
db.orders.find({ status: "pending" }).sort({ created_at: -1 }).limit(10);
db.orders.findOne({ _id: ObjectId("...") });
db.orders.countDocuments({ status: "pending" });
db.orders.distinct("status");

// Update
db.orders.updateOne(
  { _id: ObjectId("...") },
  { $set: { status: "shipped" }, $currentDate: { updated_at: true } }
);

db.orders.updateMany(
  { status: "pending", created_at: { $lt: new Date("2026-01-01") } },
  { $set: { status: "cancelled" } }
);

// Delete
db.orders.deleteOne({ _id: ObjectId("...") });
db.orders.deleteMany({ status: "cancelled", created_at: { $lt: new Date("2025-01-01") } });
```

### Indici

```javascript
// Indice singolo
db.orders.createIndex({ customer_id: 1 });

// Indice composto — l'ordine dei campi conta per l'ESR rule
// (Equality, Sort, Range)
db.orders.createIndex({ status: 1, created_at: -1 });

// Indice multikey — su array
db.orders.createIndex({ "items.product": 1 });

// Indice text — per ricerca full-text
db.articles.createIndex({ title: "text", body: "text" },
  { weights: { title: 10, body: 1 }, default_language: "italian" });
db.articles.find({ $text: { $search: "database management" } },
  { score: { $meta: "textScore" } }).sort({ score: { $meta: "textScore" } });

// Indice geospaziale (2dsphere)
db.locations.createIndex({ coordinates: "2dsphere" });
db.locations.find({
  coordinates: {
    $near: {
      $geometry: { type: "Point", coordinates: [12.4964, 41.9028] },
      $maxDistance: 5000  // metri
    }
  }
});

// Indice TTL — rimuove automaticamente i documenti scaduti
db.sessions.createIndex({ "expire_at": 1 }, { expireAfterSeconds: 0 });
// Il documento verra rimosso quando expire_at <= now()

// Indice parziale — indicizza solo i documenti che soddisfano il filtro
db.orders.createIndex(
  { customer_id: 1, created_at: -1 },
  { partialFilterExpression: { status: "pending" } }
);

// Indice unico
db.users.createIndex({ email: 1 }, { unique: true });

// Gestione indici
db.orders.getIndexes();
db.orders.dropIndex("idx_name");
db.orders.totalIndexSize();

// Analisi utilizzo indici
db.orders.aggregate([{ $indexStats: {} }]);
```

### Aggregation Pipeline

```javascript
// Esempio: fatturato mensile per status
db.orders.aggregate([
  { $match: { created_at: { $gte: ISODate("2026-01-01"), $lt: ISODate("2027-01-01") } } },
  { $unwind: "$items" },
  { $group: {
      _id: {
        month: { $month: "$created_at" },
        year: { $year: "$created_at" },
        status: "$status"
      },
      total_revenue: { $sum: "$items.price" },
      order_count: { $sum: 1 },
      avg_order_value: { $avg: "$items.price" }
  }},
  { $sort: { "_id.year": 1, "_id.month": 1 } },
  { $project: {
      period: { $concat: [{ $toString: "$_id.year" }, "-", { $toString: "$_id.month" }] },
      status: "$_id.status",
      total_revenue: { $round: ["$total_revenue", 2] },
      order_count: 1,
      avg_order_value: { $round: ["$avg_order_value", 2] }
  }}
]);

// Lookup (equivalent di JOIN)
db.orders.aggregate([
  { $lookup: {
      from: "customers",
      localField: "customer_id",
      foreignField: "_id",
      as: "customer"
  }},
  { $unwind: "$customer" },
  { $project: {
      order_id: "$_id",
      customer_name: "$customer.name",
      total: 1,
      status: 1
  }}
]);

// Bucket — raggruppamento per intervalli
db.orders.aggregate([
  { $bucket: {
      groupBy: "$total",
      boundaries: [0, 50, 100, 500, 1000, Infinity],
      default: "Other",
      output: { count: { $sum: 1 }, avg_total: { $avg: "$total" } }
  }}
]);
```

### Utenti e Ruoli (RBAC)

```javascript
// Creare l'utente amministratore
use admin
db.createUser({
  user: "admin_user",
  pwd: "secure_admin_password",
  roles: [{ role: "userAdminAnyDatabase", db: "admin" },
          { role: "readWriteAnyDatabase", db: "admin" },
          { role: "clusterAdmin", db: "admin" }]
});

// Utente applicativo con permessi limitati
use app_db
db.createUser({
  user: "app_user",
  pwd: "app_password",
  roles: [{ role: "readWrite", db: "app_db" }]
});

// Utente read-only per reporting
db.createUser({
  user: "report_user",
  pwd: "report_password",
  roles: [{ role: "read", db: "app_db" }]
});

// Ruolo custom
use admin
db.createRole({
  role: "orderManager",
  privileges: [
    { resource: { db: "app_db", collection: "orders" },
      actions: ["find", "insert", "update"] },
    { resource: { db: "app_db", collection: "customers" },
      actions: ["find"] }
  ],
  roles: []
});

db.createUser({
  user: "order_user",
  pwd: "order_password",
  roles: [{ role: "orderManager", db: "admin" }]
});

// Gestione utenti
db.getUsers();
db.getUser("app_user");
db.updateUser("app_user", { roles: [{ role: "read", db: "app_db" }] });
db.changeUserPassword("app_user", "new_password");
db.dropUser("old_user");
```

### Backup e Restore

```bash
# mongodump — backup logico
mongodump --uri="mongodb://backup_user:password@10.0.1.1:27017" \
    --db=app_db --gzip --out=/backup/$(date +%Y%m%d_%H%M%S)

# Backup di tutte i database
mongodump --uri="mongodb://backup_user:password@10.0.1.1:27017" \
    --gzip --oplog --out=/backup/full_$(date +%Y%m%d)

# mongorestore
mongorestore --uri="mongodb://admin_user:password@10.0.1.1:27017" \
    --db=app_db --gzip /backup/20260411/app_db

# Restore con oplog replay (point-in-time)
mongorestore --uri="mongodb://admin_user:password@10.0.1.1:27017" \
    --oplogReplay --gzip /backup/full_20260411
```

### Profiler

```javascript
// Attivare il profiler
db.setProfilingLevel(1, { slowms: 100 });  // livello 1: solo operazioni lente
db.setProfilingLevel(2);                    // livello 2: tutte le operazioni

// Query sul system.profile
db.system.profile.find({ millis: { $gt: 100 } })
  .sort({ ts: -1 }).limit(10);

// Operazioni lente con dettagli del piano di esecuzione
db.system.profile.find(
  { op: "query", millis: { $gt: 200 } },
  { op: 1, ns: 1, millis: 1, planSummary: 1, command: 1 }
).sort({ millis: -1 });

// Disattivare il profiler
db.setProfilingLevel(0);

// Explain per analizzare le query
db.orders.find({ status: "pending" }).explain("executionStats");
// Verificare: totalDocsExamined vs nReturned — rapporto vicino a 1 = buon indice
// Verificare: stage COLLSCAN indica scansione senza indice
```

---

## 8. MongoDB — Replica Set e Sharding

### Replica Set

Un Replica Set e un gruppo di istanze MongoDB che mantengono lo stesso dataset. Fornisce ridondanza e alta disponibilita. Un replica set e composto da:

- **Primary**: riceve tutte le operazioni di scrittura.
- **Secondary**: replica i dati dal primary. Puo servire letture (se configurato).
- **Arbiter**: partecipa solo alle elezioni, non memorizza dati. Utile per avere un numero dispari di membri senza il costo di un nodo dati completo.

```javascript
// Inizializzare il replica set sul primo nodo
rs.initiate({
  _id: "rs-prod",
  members: [
    { _id: 0, host: "10.0.1.1:27017", priority: 2 },  // preferenza come primary
    { _id: 1, host: "10.0.1.2:27017", priority: 1 },
    { _id: 2, host: "10.0.1.3:27017", priority: 1 }
  ]
});

// Aggiungere un membro
rs.add("10.0.1.4:27017");

// Aggiungere un arbiter
rs.addArb("10.0.1.5:27017");

// Verificare lo stato
rs.status();
rs.conf();
rs.printReplicationInfo();      // stato dell'oplog
rs.printSecondaryReplicationInfo();  // ritardo delle secondarie

// Forzare il ricalcolo del primary (stepdown)
rs.stepDown(60);   // il primary diventa secondary per 60 secondi
```

### Elections

Le elezioni avvengono automaticamente quando il primary non e raggiungibile. Per vincere un'elezione, un candidato necessita della maggioranza dei voti (majority). Per un replica set di 3 membri, servono almeno 2 voti.

Fattori che influenzano le elezioni:
- **Priority**: membri con priority piu alta sono preferiti. Priority 0 = non puo diventare primary.
- **Oplog freshness**: il candidato deve avere i dati piu recenti.
- **Network partitions**: in caso di split, il segmento con la maggioranza elegge il primary.

### Read Preference e Write/Read Concern

```javascript
// Read Preference — dove leggere
// primary         — solo dal primary (default, consistenza forte)
// primaryPreferred — primary preferito, secondary come fallback
// secondary       — solo dai secondary
// secondaryPreferred — secondary preferiti, primary come fallback
// nearest         — nodo con latenza piu bassa

// Configurazione nella connection string
// mongodb://host1:27017,host2:27017,host3:27017/app_db?replicaSet=rs-prod&readPreference=secondaryPreferred

// Write Concern — garanzie di scrittura
db.orders.insertOne(
  { item: "laptop", qty: 1 },
  { writeConcern: { w: "majority", j: true, wtimeout: 5000 } }
);
// w: "majority" — conferma dalla maggioranza dei membri
// j: true — conferma di scrittura sul journal
// wtimeout: 5000 — timeout in ms

// Read Concern — garanzie di lettura
db.orders.find({ status: "pending" }).readConcern("majority");
// "local"      — dati locali, senza garanzia di durabilita
// "majority"   — dati confermati dalla maggioranza
// "linearizable" — lettura consistente con le ultime scritture (piu lento)
// "snapshot"   — lettura da uno snapshot consistente (per transazioni multi-documento)
```

### Change Streams

I Change Streams permettono alle applicazioni di ricevere notifiche in tempo reale sulle modifiche ai dati, senza polling.

```javascript
// Watch su una collection
const changeStream = db.orders.watch([
  { $match: { "fullDocument.status": "shipped" } }
]);

changeStream.on("change", (change) => {
  console.log("Ordine spedito:", change.fullDocument);
  // change.operationType: insert, update, replace, delete
  // change.fullDocument: il documento completo (se richiesto)
  // change.updateDescription: campi modificati (per update)
});

// Watch su tutto il database
const dbStream = db.watch();

// Watch con resume token — per riprendere dopo un'interruzione
const resumeToken = changeStream.resumeToken;
const resumedStream = db.orders.watch([], { resumeAfter: resumeToken });
```

### Sharding

Lo sharding distribuisce i dati su piu shard (server o replica set), consentendo scalabilita orizzontale per dataset che superano la capacita di un singolo server.

**Componenti dell'architettura di sharding**:
- **Shard**: ogni shard contiene un sottoinsieme dei dati. In produzione ogni shard e un replica set.
- **Config Server**: memorizza i metadati del cluster (mapping chunk-shard). Deve essere un replica set.
- **mongos Router**: instrada le query verso gli shard corretti. Applicazione si connette a mongos.

### Shard Key Selection

La scelta della shard key e la decisione piu critica nello sharding. Una shard key mal scelta causa hot spot e performance degradate.

```javascript
// Shard key con buona cardinalita e distribuzione
// Esempio: hashed shard key per distribuzione uniforme
sh.enableSharding("app_db");
sh.shardCollection("app_db.orders", { _id: "hashed" });

// Shard key composta per query range + distribuzione
sh.shardCollection("app_db.events", { tenant_id: 1, created_at: 1 });

// Verificare lo stato dello sharding
sh.status();

// Bilanciamento dei chunk
sh.getBalancerState();
sh.startBalancer();
sh.stopBalancer();

// Impostare finestra di bilanciamento (per evitare impatto durante peak hours)
db.settings.updateOne(
  { _id: "balancer" },
  { $set: { activeWindow: { start: "02:00", stop: "06:00" } } },
  { upsert: true }
);
```

**Criteri per una buona shard key**:
1. **Alta cardinalita**: molti valori distinti per distribuzione uniforme.
2. **Bassa frequenza**: nessun valore che domina (evitare hot spot).
3. **Non monotonicamente crescente**: evitare ObjectId o timestamp come shard key singola (tutti gli insert vanno sullo stesso shard). Usare hashed o composta.
4. **Allineata con le query**: la shard key dovrebbe corrispondere ai filtri piu comuni per consentire query mirate (targeted query anziche scatter-gather).

### Configurazione Sharding

```yaml
# mongod.conf per un config server
sharding:
  clusterRole: configsvr
replication:
  replSetName: "cfg-rs"

# mongod.conf per uno shard
sharding:
  clusterRole: shardsvr
replication:
  replSetName: "shard1-rs"

# mongos.conf
sharding:
  configDB: "cfg-rs/cfg1:27019,cfg2:27019,cfg3:27019"
net:
  port: 27017
```

```bash
# Inizializzare il config server replica set
mongosh --port 27019
rs.initiate({ _id: "cfg-rs", configsvr: true, members: [
  { _id: 0, host: "cfg1:27019" },
  { _id: 1, host: "cfg2:27019" },
  { _id: 2, host: "cfg3:27019" }
]});

# Inizializzare ogni shard replica set
mongosh --port 27018
rs.initiate({ _id: "shard1-rs", members: [
  { _id: 0, host: "shard1a:27018" },
  { _id: 1, host: "shard1b:27018" },
  { _id: 2, host: "shard1c:27018" }
]});

# Aggiungere gli shard tramite mongos
mongosh --port 27017
sh.addShard("shard1-rs/shard1a:27018,shard1b:27018,shard1c:27018");
sh.addShard("shard2-rs/shard2a:27018,shard2b:27018,shard2c:27018");
```

---

## 9. Database su Kubernetes

### Operators Pattern

Il pattern Operator estende le API di Kubernetes con Custom Resource Definitions (CRD) e controller dedicati per gestire il ciclo di vita di applicazioni stateful come i database. Un operatore codifica la conoscenza operativa del DBA in software, automatizzando provisioning, scaling, backup, restore, failover e upgrade.

Vantaggi dell'approccio operatore:
- **Automazione day-2**: non solo il deployment iniziale, ma tutte le operazioni successive.
- **Self-healing**: l'operatore monitora lo stato desiderato e corregge le deviazioni.
- **Standardizzazione**: ogni istanza di database segue le stesse procedure operative.
- **Integrazione nativa**: l'operatore sfrutta le primitive Kubernetes (Pod, Service, PVC, Secret).

### StatefulSets per Database

I StatefulSet sono il building block fondamentale per i database su Kubernetes. A differenza dei Deployment, garantiscono:

- **Identita stabile**: ogni Pod ha un hostname persistente (es. `pg-0`, `pg-1`, `pg-2`).
- **Storage persistente**: ogni Pod ha il proprio PersistentVolumeClaim che sopravvive ai riavvii.
- **Ordinamento**: i Pod vengono creati e terminati in ordine (importante per l'inizializzazione dei cluster).

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: databases
spec:
  serviceName: postgres-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: pg-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: pg-data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "1"
              memory: "4Gi"
            limits:
              cpu: "2"
              memory: "8Gi"
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 30
            periodSeconds: 10
  volumeClaimTemplates:
    - metadata:
        name: pg-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: databases
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

### PersistentVolumeClaim e Storage Classes

```yaml
# Storage class per SSD ad alte performance
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com          # AWS EBS CSI
parameters:
  type: gp3
  iops: "6000"
  throughput: "250"
  encrypted: "true"
reclaimPolicy: Retain                  # non eliminare il volume quando il PVC viene rimosso
allowVolumeExpansion: true             # consente il resize online
volumeBindingMode: WaitForFirstConsumer  # provisioning lazy
```

### CloudNativePG

Operatore nativo per PostgreSQL su Kubernetes, sviluppato da EDB. Gestisce automaticamente replica, failover, backup su object storage, monitoring.

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: pg-prod
  namespace: databases
spec:
  instances: 3
  imageName: ghcr.io/cloudnative-pg/postgresql:16.2
  postgresql:
    parameters:
      shared_buffers: "4GB"
      effective_cache_size: "12GB"
      work_mem: "64MB"
      maintenance_work_mem: "1GB"
      max_connections: "200"
      wal_level: "replica"
      log_min_duration_statement: "500"
    pg_hba:
      - host all all 10.0.0.0/8 scram-sha-256
  bootstrap:
    initdb:
      database: app_db
      owner: app_user
      secret:
        name: pg-app-user-secret
  storage:
    size: 200Gi
    storageClass: fast-ssd
  walStorage:
    size: 50Gi
    storageClass: fast-ssd
  backup:
    barmanObjectStore:
      destinationPath: "s3://pg-backups/prod"
      s3Credentials:
        accessKeyId:
          name: aws-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: aws-creds
          key: SECRET_ACCESS_KEY
      wal:
        compression: gzip
        maxParallel: 4
      data:
        compression: gzip
    retentionPolicy: "30d"
  monitoring:
    enablePodMonitor: true
  affinity:
    topologyKey: topology.kubernetes.io/zone
  resources:
    requests:
      cpu: "2"
      memory: "8Gi"
    limits:
      cpu: "4"
      memory: "16Gi"
---
# Scheduled Backup
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: pg-prod-daily-backup
  namespace: databases
spec:
  schedule: "0 2 * * *"                # ogni giorno alle 02:00
  backupOwnerReference: self
  cluster:
    name: pg-prod
```

```bash
# Comandi kubectl per CloudNativePG
kubectl get clusters -n databases
kubectl describe cluster pg-prod -n databases
kubectl get pods -n databases -l cnpg.io/cluster=pg-prod

# Failover manuale (promuovere un secondary)
kubectl cnpg promote pg-prod pg-prod-2 -n databases

# Backup on-demand
kubectl cnpg backup pg-prod -n databases

# Connessione al cluster
kubectl port-forward svc/pg-prod-rw 5432:5432 -n databases
```

### Percona Operators

Percona fornisce operatori open-source per MySQL, MongoDB e PostgreSQL su Kubernetes.

```yaml
# Percona XtraDB Cluster (MySQL) Operator
apiVersion: pxc.percona.com/v1
kind: PerconaXtraDBCluster
metadata:
  name: mysql-prod
  namespace: databases
spec:
  crVersion: "1.14.0"
  secretsName: mysql-secrets
  pxc:
    size: 3
    image: percona/percona-xtradb-cluster:8.0
    resources:
      requests:
        memory: 4Gi
        cpu: "2"
    volumeSpec:
      persistentVolumeClaim:
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
  haproxy:
    enabled: true
    size: 2
    image: percona/haproxy:2.8
  proxysql:
    enabled: false
  backup:
    image: percona/percona-xtradb-cluster-operator:1.14.0-pxc8.0-backup
    storages:
      s3-backup:
        type: s3
        s3:
          bucket: mysql-backups
          credentialsSecret: aws-creds
          region: eu-west-1
    schedule:
      - name: daily-backup
        schedule: "0 3 * * *"
        keep: 7
        storageName: s3-backup
```

### Vitess per MySQL Sharding

Vitess e un sistema di sharding e scaling per MySQL, originariamente sviluppato da YouTube. Su Kubernetes si integra tramite l'operatore Vitess.

```yaml
apiVersion: planetscale.com/v2
kind: VitessCluster
metadata:
  name: vitess-prod
spec:
  cells:
    - name: zone1
      gateway:
        replicas: 2
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
  keyspaces:
    - name: commerce
      turndownPolicy: Immediate
      partitionings:
        - equal:
            parts: 4
            shardTemplate:
              databaseInitScriptSecret:
                name: vitess-init-script
              tabletPools:
                - cell: zone1
                  type: replica
                  replicas: 3
                  mysqld:
                    resources:
                      requests:
                        cpu: "2"
                        memory: "4Gi"
                  dataVolumeClaimTemplate:
                    storageClassName: fast-ssd
                    resources:
                      requests:
                        storage: 50Gi
```

### Anti-Patterns: Quando NON Usare DB su Kubernetes

Non tutti gli scenari beneficiano dell'esecuzione di database su Kubernetes. Evitare in questi casi:

1. **Mancanza di competenze Kubernetes**: la complessita operativa e significativa. Senza un team esperto, i managed services cloud sono piu sicuri.
2. **Storage locale necessario**: se il database richiede performance I/O estrema con storage locale NVMe, Kubernetes aggiunge overhead di rete.
3. **Database legacy monolitici**: migrare un Oracle o SQL Server monolitico su K8s raramente porta vantaggi.
4. **Cluster molto piccoli**: per un singolo database non critico, un managed service e piu economico operativamente.
5. **Assenza di operatori maturi**: senza un operatore affidabile, gestire manualmente StatefulSet, backup e failover e rischioso.
6. **Requisiti di compliance stringenti**: alcuni regolamenti richiedono controllo totale sull'hardware, rendendo K8s meno adatto.

---

## 10. Performance Tuning

### Query Optimization

L'ottimizzazione delle query e il singolo intervento con il maggiore impatto sulle performance di un database. Una query mal scritta puo essere milioni di volte piu lenta della versione ottimizzata.

**PostgreSQL — EXPLAIN ANALYZE**:

```sql
-- EXPLAIN mostra il piano stimato, EXPLAIN ANALYZE esegue e mostra dati reali
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT o.id, o.order_date, c.name, SUM(oi.quantity * oi.unit_price) AS total
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
WHERE o.order_date BETWEEN '2026-01-01' AND '2026-03-31'
  AND c.country = 'IT'
GROUP BY o.id, o.order_date, c.name
ORDER BY total DESC
LIMIT 100;

-- Elementi critici da verificare nell'output:
-- Seq Scan: scansione sequenziale — potrebbe servire un indice
-- Nested Loop: accettabile per piccoli dataset, problematico per grandi
-- Hash Join / Merge Join: generalmente efficienti per join di grandi tabelle
-- Sort: se il sort spilla su disco (external sort), aumentare work_mem
-- Rows: confrontare righe stimate vs righe reali — statistiche obsolete?
-- Buffers: shared hit vs shared read — cache hit ratio
```

**MySQL — EXPLAIN**:

```sql
EXPLAIN FORMAT=TREE
SELECT o.id, o.order_date, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending'
  AND o.order_date > '2026-01-01'
ORDER BY o.order_date DESC
LIMIT 50;

-- Valori critici nella colonna 'type':
-- ALL: full table scan (pessimo per tabelle grandi)
-- index: full index scan
-- range: scan su un intervallo dell'indice
-- ref: lookup per uguaglianza su indice non-unico
-- eq_ref: lookup per uguaglianza su indice unico (migliore per join)
-- const: la tabella ha al massimo una riga corrispondente
```

### Strategia degli Indici

Principi fondamentali per la creazione degli indici:

1. **Regola ESR** (per indici composti): ordinare i campi nell'indice come Equality, Sort, Range.
2. **Covering index**: includere tutti i campi necessari alla query nell'indice per evitare l'accesso alla tabella.
3. **Selettivita**: creare indici su colonne con alta selettivita (molti valori distinti).
4. **Non sovra-indicizzare**: ogni indice costa spazio e rallenta le scritture. Rimuovere indici inutilizzati.

```sql
-- PostgreSQL: covering index con INCLUDE
CREATE INDEX idx_orders_status_date ON orders (status, order_date DESC)
    INCLUDE (customer_id, total);

-- PostgreSQL: partial index — indicizza solo le righe rilevanti
CREATE INDEX idx_orders_pending ON orders (customer_id, order_date)
    WHERE status = 'pending';

-- PostgreSQL: expression index
CREATE INDEX idx_users_email_lower ON users (LOWER(email));

-- MySQL: invisible index — disabilita l'indice senza rimuoverlo (test)
ALTER TABLE orders ALTER INDEX idx_old_index INVISIBLE;
-- Se le performance peggiorano, riabilitare:
ALTER TABLE orders ALTER INDEX idx_old_index VISIBLE;

-- Identificare indici inutilizzati in PostgreSQL
SELECT schemaname, relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch,
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Connection Pooling

Le connessioni ai database sono risorse costose. Un connection pooler riduce il numero di connessioni reali al database mantenendo un pool condiviso.

```
# Architettura tipica
[App Instances (200+)] --> [Connection Pooler (pgBouncer/ProxySQL)] --> [Database (max 50-100 connessioni)]
```

Regola empirica per PostgreSQL (formula di Joe Conway):
```
max_connections = (core_count * 2) + effective_disk_count
```

Per un server con 8 core e 1 disco SSD: `max_connections = 17`. Il resto delle connessioni deve essere gestito dal pooler.

### Caching Layers

```
[Client] --> [CDN (contenuti statici)]
         --> [Application Cache (in-memory)]
         --> [Redis/Memcached (distributed cache)]
         --> [Database (source of truth)]
```

**Pattern Cache-Aside** (Lazy Loading):

```python
# Pseudocodice
def get_user(user_id):
    # 1. Controllare la cache
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    # 2. Cache miss — query al database
    user = db.query("SELECT * FROM users WHERE id = %s", user_id)

    # 3. Popolare la cache con TTL
    redis.setex(f"user:{user_id}", 3600, json.dumps(user))

    return user
```

**Pattern Write-Through**:

```python
def update_user(user_id, data):
    # 1. Scrivere nel database
    db.execute("UPDATE users SET name = %s WHERE id = %s", data['name'], user_id)

    # 2. Aggiornare la cache
    redis.setex(f"user:{user_id}", 3600, json.dumps(data))
```

### Partitioning

Il partitioning divide una tabella grande in parti piu piccole e gestibili, migliorando le performance delle query che accedono a un sottoinsieme dei dati.

```sql
-- PostgreSQL: Range partitioning per data
CREATE TABLE orders (
    id          BIGSERIAL,
    customer_id BIGINT NOT NULL,
    order_date  DATE NOT NULL,
    total       NUMERIC(10,2),
    status      VARCHAR(20)
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2026_q1 PARTITION OF orders
    FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE orders_2026_q2 PARTITION OF orders
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE TABLE orders_2026_q3 PARTITION OF orders
    FOR VALUES FROM ('2026-07-01') TO ('2026-10-01');
CREATE TABLE orders_2026_q4 PARTITION OF orders
    FOR VALUES FROM ('2026-10-01') TO ('2027-01-01');

-- Partizione di default per dati fuori range
CREATE TABLE orders_default PARTITION OF orders DEFAULT;

-- PostgreSQL: Hash partitioning
CREATE TABLE sessions (
    id          UUID PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    data        JSONB,
    created_at  TIMESTAMPTZ NOT NULL
) PARTITION BY HASH (user_id);

CREATE TABLE sessions_p0 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE sessions_p1 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE sessions_p2 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE sessions_p3 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- MySQL: Range partitioning
ALTER TABLE orders PARTITION BY RANGE (YEAR(order_date)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

### Sharding Strategies

Lo sharding distribuisce i dati su piu istanze di database indipendenti.

**Range-Based Sharding**: i dati vengono distribuiti per intervalli della shard key (es. customer_id 1-1000 su shard1, 1001-2000 su shard2). Semplice ma rischio di hot spot.

**Hash-Based Sharding**: la shard key viene hashata per determinare lo shard di destinazione. Distribuzione uniforme ma range query inefficienti.

**Directory-Based Sharding**: un servizio di lookup mantiene la mappatura chiave-shard. Flessibile ma il directory e un single point of failure.

**Geographic Sharding**: dati distribuiti per regione geografica. Riduce latenza per utenti locali e semplifica compliance GDPR.

### Capacity Planning

```sql
-- PostgreSQL: tasso di crescita delle tabelle
SELECT relname,
       pg_size_pretty(pg_total_relation_size(relid)) AS current_size,
       n_tup_ins - n_tup_del AS net_rows_added,
       n_tup_ins AS inserts,
       n_tup_del AS deletes
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- Proiezione: se una tabella cresce di 1 GB/mese e attualmente e 50 GB,
-- con 200 GB di disco disponibile, raggiungeremo il limite in ~150 mesi.
-- Considerare: compressione, partitioning con drop delle partizioni vecchie,
-- archiviazione dei dati storici.
```

---

## 11. Backup e Disaster Recovery

### Strategie di Backup

**Full Backup**: copia completa di tutti i dati. Base per qualsiasi strategia di recovery. Richiede piu tempo e spazio ma e il piu semplice da ripristinare.

**Incremental Backup**: copia solo i dati modificati dall'ultimo backup (full o incrementale). Veloce da eseguire, risparmia spazio, ma il restore richiede l'applicazione sequenziale di tutti gli incrementali.

**Differential Backup**: copia tutti i dati modificati dall'ultimo full backup. Piu veloce del full, restore piu semplice dell'incrementale (serve solo il full + l'ultimo differential).

| Strategia | Tempo Backup | Spazio | Tempo Restore | Complessita |
|---|---|---|---|---|
| Full | Lungo | Grande | Veloce | Bassa |
| Incremental | Veloce | Piccolo | Lento (sequenziale) | Alta |
| Differential | Medio | Medio | Medio | Media |

**Strategia consigliata**: full settimanale + incrementale giornaliero + WAL/binlog archiving continuo per PITR.

### RTO e RPO

**RPO (Recovery Point Objective)**: quantita massima di dati che si possono perdere, espressa in tempo. RPO = 1 ora significa che si accetta la perdita massima di 1 ora di dati.

**RTO (Recovery Time Objective)**: tempo massimo tollerabile per il ripristino del servizio dopo un'interruzione.

| Livello | RPO | RTO | Strategia |
|---|---|---|---|
| Critico | 0 (zero data loss) | < 5 min | Replica sincrona + failover automatico |
| Alto | < 1 ora | < 30 min | Replica asincrona + PITR + failover semi-automatico |
| Medio | < 24 ore | < 4 ore | Backup giornaliero + PITR |
| Basso | < 1 settimana | < 24 ore | Backup settimanale |

### Backup Verification

Un backup non testato non e un backup. Verificare regolarmente:

```bash
# Script di verifica backup PostgreSQL
#!/bin/bash
set -euo pipefail

BACKUP_FILE="/backup/latest/app_db.dump"
TEST_DB="backup_verify_$(date +%s)"
LOG_FILE="/var/log/backup_verify.log"

echo "$(date): Avvio verifica backup" >> "$LOG_FILE"

# Creare un database temporaneo per il test
createdb -h localhost -U postgres "$TEST_DB"

# Restore del backup nel database di test
pg_restore -h localhost -U postgres -d "$TEST_DB" "$BACKUP_FILE" 2>> "$LOG_FILE"

# Verifiche di integrita
TABLES=$(psql -h localhost -U postgres -d "$TEST_DB" -t -c \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
ROWS=$(psql -h localhost -U postgres -d "$TEST_DB" -t -c \
    "SELECT sum(n_live_tup) FROM pg_stat_user_tables;")

echo "$(date): Tabelle: $TABLES, Righe totali: $ROWS" >> "$LOG_FILE"

# Pulizia
dropdb -h localhost -U postgres "$TEST_DB"

echo "$(date): Verifica backup completata con successo" >> "$LOG_FILE"
```

### Cross-Region Replication

```bash
# PostgreSQL: streaming replication cross-region tramite WAL shipping su S3
# Configurazione con wal-g (strumento moderno per WAL archiving)

# Sul primary — archiviazione WAL su S3
export WALG_S3_PREFIX=s3://pg-wal-archive/prod
export AWS_REGION=eu-west-1

# In postgresql.conf
# archive_mode = on
# archive_command = 'wal-g wal-push %p'
# archive_timeout = 60

# Eseguire un base backup
wal-g backup-push /var/lib/postgresql/16/main

# Sullo standby in un'altra regione — restore da S3
wal-g backup-fetch /var/lib/postgresql/16/main LATEST
# In postgresql.auto.conf:
# restore_command = 'wal-g wal-fetch %f %p'
# primary_conninfo = 'host=primary.eu-west-1.rds.example.com ...'
```

### Runbook di Restore

Un runbook di restore documenta la procedura passo-passo per il ripristino in caso di disastro. Deve essere testato regolarmente.

```
=== RUNBOOK: Restore PostgreSQL da Backup ===

PREREQUISITI:
- Accesso SSH al server di destinazione
- Credenziali per il bucket S3 dei backup
- Server PostgreSQL installato (stessa major version)

PROCEDURA:

1. FERMARE il servizio PostgreSQL
   sudo systemctl stop postgresql

2. PRESERVARE la directory dati corrente (se applicabile)
   sudo mv /var/lib/postgresql/16/main /var/lib/postgresql/16/main.old

3. SCARICARE il backup
   # Con wal-g:
   wal-g backup-fetch /var/lib/postgresql/16/main LATEST
   # Oppure con pg_basebackup:
   pg_basebackup -h backup_host -U repl_user -D /var/lib/postgresql/16/main -Fp -Xs -P

4. CONFIGURARE il recovery
   # Creare recovery.signal
   touch /var/lib/postgresql/16/main/recovery.signal
   # Configurare restore_command in postgresql.auto.conf
   echo "restore_command = 'wal-g wal-fetch %f %p'" >> /var/lib/postgresql/16/main/postgresql.auto.conf
   # Per PITR specificare anche:
   echo "recovery_target_time = '2026-04-10 14:30:00 UTC'" >> /var/lib/postgresql/16/main/postgresql.auto.conf
   echo "recovery_target_action = 'promote'" >> /var/lib/postgresql/16/main/postgresql.auto.conf

5. IMPOSTARE i permessi
   sudo chown -R postgres:postgres /var/lib/postgresql/16/main
   sudo chmod 700 /var/lib/postgresql/16/main

6. AVVIARE PostgreSQL
   sudo systemctl start postgresql
   # Monitorare i log durante il recovery
   sudo tail -f /var/log/postgresql/postgresql-16-main.log

7. VERIFICARE
   psql -U postgres -c "SELECT pg_is_in_recovery();"   -- false dopo il promote
   psql -U postgres -c "SELECT count(*) FROM pg_stat_user_tables;"
   # Confrontare il conteggio delle righe con l'ultimo backup noto

8. AGGIORNARE le connessioni applicative se il hostname e cambiato
```

### Automazione Backup con Cron

```bash
# /etc/cron.d/database-backup

# PostgreSQL — full backup giornaliero alle 02:00
0 2 * * * postgres /usr/local/bin/pg_backup.sh >> /var/log/pg_backup.log 2>&1

# PostgreSQL — WAL archiving continuo (gestito da archive_command)

# MySQL — full backup giornaliero alle 03:00
0 3 * * * mysql /usr/local/bin/mysql_backup.sh >> /var/log/mysql_backup.log 2>&1

# MySQL — incrementale ogni 6 ore
0 */6 * * * mysql /usr/local/bin/mysql_incremental.sh >> /var/log/mysql_inc_backup.log 2>&1

# MongoDB — backup giornaliero alle 04:00
0 4 * * * mongodb /usr/local/bin/mongo_backup.sh >> /var/log/mongo_backup.log 2>&1

# Redis — RDB snapshot ogni 4 ore (in aggiunta alla configurazione save in redis.conf)
0 */4 * * * redis /usr/bin/redis-cli BGSAVE >> /var/log/redis_backup.log 2>&1

# Verifica backup settimanale (domenica alle 06:00)
0 6 * * 0 postgres /usr/local/bin/backup_verify.sh >> /var/log/backup_verify.log 2>&1

# Pulizia backup vecchi (> 30 giorni)
0 5 * * * root find /backup -name "*.dump" -mtime +30 -delete
```

```bash
#!/bin/bash
# /usr/local/bin/pg_backup.sh
set -euo pipefail

BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_LIST=$(psql -U postgres -t -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datname != 'postgres';")

mkdir -p "${BACKUP_DIR}/${DATE}"

for DB in $DB_LIST; do
    DB=$(echo "$DB" | xargs)  # trim whitespace
    pg_dump -U postgres -Fc -f "${BACKUP_DIR}/${DATE}/${DB}.dump" "$DB"
    echo "$(date): Backup completato per $DB"
done

# Upload su S3
aws s3 sync "${BACKUP_DIR}/${DATE}" "s3://pg-backups/daily/${DATE}/" --storage-class STANDARD_IA

# Verifica integrita
for DUMP in "${BACKUP_DIR}/${DATE}"/*.dump; do
    pg_restore --list "$DUMP" > /dev/null 2>&1
    echo "$(date): Verifica integrita OK per $(basename $DUMP)"
done

echo "$(date): Backup giornaliero completato"
```

### Cloud-Native Backup

```bash
# AWS RDS — snapshot automatici e manuali
aws rds create-db-snapshot \
    --db-instance-identifier prod-postgres \
    --db-snapshot-identifier prod-postgres-manual-$(date +%Y%m%d)

# AWS RDS — copia snapshot cross-region per DR
aws rds copy-db-snapshot \
    --source-db-snapshot-identifier arn:aws:rds:eu-west-1:123456789:snapshot:prod-postgres-manual-20260411 \
    --target-db-snapshot-identifier prod-postgres-dr-20260411 \
    --region us-east-1

# AWS RDS — restore da snapshot
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier prod-postgres-restored \
    --db-snapshot-identifier prod-postgres-manual-20260411 \
    --db-instance-class db.r6g.xlarge

# Azure Database for PostgreSQL — backup
az postgres flexible-server backup create \
    --resource-group rg-prod \
    --name pg-prod \
    --backup-name manual-backup-20260411

# GCP Cloud SQL — backup
gcloud sql backups create \
    --instance=pg-prod \
    --description="Manual backup 2026-04-11"

# GCP Cloud SQL — restore da backup
gcloud sql backups restore BACKUP_ID \
    --restore-instance=pg-prod-restored
```

---

## 12. Best Practices

### Security Hardening

**Rete**:
- Posizionare i database in subnet private, non accessibili direttamente da Internet.
- Utilizzare security group/firewall rules per limitare l'accesso alle sole IP autorizzate.
- Configurare VPN o bastion host per l'accesso amministrativo.
- Separare il traffico di replica dal traffico applicativo su VLAN dedicate.

**Autenticazione**:
- Utilizzare metodi di autenticazione forti: `scram-sha-256` per PostgreSQL, `caching_sha2_password` per MySQL.
- Implementare il principio del minimo privilegio: ogni utente deve avere solo i permessi strettamente necessari.
- Ruotare le password regolarmente e utilizzare un secrets manager (Vault, AWS Secrets Manager).
- Disabilitare account di default e rinominare gli utenti admin.

```sql
-- PostgreSQL: revocare tutti i permessi di default
REVOKE ALL ON DATABASE app_db FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- MySQL: rimuovere utenti con accesso senza password
SELECT user, host FROM mysql.user WHERE authentication_string = '';
DROP USER ''@'localhost';  -- utente anonimo

-- MongoDB: disabilitare l'accesso senza autenticazione
-- In mongod.conf: security.authorization = enabled
```

**Encryption at Rest**:

```ini
# PostgreSQL con pgcrypto per crittografia a livello colonna
# Per crittografia a livello di storage, usare LUKS o la crittografia del cloud provider

# MySQL: TDE (Transparent Data Encryption)
# my.cnf
[mysqld]
early-plugin-load = keyring_file.so
keyring_file_data = /var/lib/mysql-keyring/keyring
innodb_undo_log_encrypt = ON
innodb_redo_log_encrypt = ON

# Per crittografare una tabella InnoDB
ALTER TABLE sensitive_data ENCRYPTION='Y';
```

**Encryption in Transit**:

```ini
# PostgreSQL: ssl in postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
ssl_min_protocol_version = 'TLSv1.3'

# Forzare SSL in pg_hba.conf
hostssl all all 0.0.0.0/0 scram-sha-256
```

```ini
# MySQL: ssl in my.cnf
[mysqld]
ssl_cert = /etc/mysql/ssl/server-cert.pem
ssl_key = /etc/mysql/ssl/server-key.pem
ssl_ca = /etc/mysql/ssl/ca.pem
require_secure_transport = ON
tls_version = TLSv1.3
```

**Audit Logging**:

```sql
-- PostgreSQL: pgAudit
-- In postgresql.conf: shared_preload_libraries = 'pgaudit'
CREATE EXTENSION pgaudit;
-- Log di tutti i DDL e DML
ALTER SYSTEM SET pgaudit.log = 'ddl, write, role';
SELECT pg_reload_conf();

-- MySQL: audit log plugin
INSTALL COMPONENT "file://component_audit_api_message_emit";
SET GLOBAL audit_log_policy = 'ALL';
```

### Naming Conventions

Convenzioni consistenti facilitano la manutenzione e la comprensione del database.

```
DATABASE:       snake_case, descrittivo          app_production, analytics_dw
SCHEMA:         snake_case                       public, app, staging, archive
TABLE:          snake_case, plurale              users, order_items, audit_logs
COLUMN:         snake_case                       first_name, created_at, is_active
PRIMARY KEY:    id (o table_id)                  id, user_id
FOREIGN KEY:    referenced_table_id              customer_id, product_id
INDEX:          idx_{table}_{columns}            idx_users_email, idx_orders_status_date
UNIQUE INDEX:   uniq_{table}_{columns}           uniq_users_email
CHECK:          chk_{table}_{description}        chk_orders_total_positive
SEQUENCE:       {table}_{column}_seq             users_id_seq
FUNCTION:       verb_noun                        calculate_total, validate_email
TRIGGER:        trg_{table}_{timing}_{event}     trg_orders_before_insert
VIEW:           vw_{description}                 vw_active_users, vw_monthly_revenue
MATERIALIZED:   mvw_{description}                mvw_daily_stats
```

### Schema Migration Tools

I tool di migrazione gestiscono l'evoluzione dello schema in modo versionato e ripetibile.

**Flyway** (Java/SQL-based):

```bash
# Struttura delle migrazioni
# sql/
#   V1__create_users_table.sql
#   V2__add_email_to_users.sql
#   V3__create_orders_table.sql

# Eseguire le migrazioni
flyway -url=jdbc:postgresql://localhost:5432/app_db \
       -user=flyway_user -password=password \
       migrate

# Verificare lo stato
flyway -url=jdbc:postgresql://localhost:5432/app_db info
```

```sql
-- V1__create_users_table.sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);

-- V2__add_email_verified.sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX idx_users_email_verified ON users (email_verified) WHERE email_verified = FALSE;
```

**Alembic** (Python/SQLAlchemy):

```bash
# Inizializzare Alembic
alembic init migrations

# Creare una migrazione
alembic revision --autogenerate -m "add_orders_table"

# Eseguire le migrazioni
alembic upgrade head

# Rollback dell'ultima migrazione
alembic downgrade -1

# Verificare lo stato
alembic current
alembic history
```

**Liquibase** (XML/YAML/JSON/SQL):

```yaml
# changelog.yaml
databaseChangeLog:
  - changeSet:
      id: 1
      author: dba
      changes:
        - createTable:
            tableName: users
            columns:
              - column:
                  name: id
                  type: bigint
                  autoIncrement: true
                  constraints:
                    primaryKey: true
              - column:
                  name: email
                  type: varchar(255)
                  constraints:
                    nullable: false
                    unique: true
```

### Database as Code

Trattare il database come codice significa versionare schema, migrazioni, seed data, e configurazioni nello stesso repository dell'applicazione.

```
project/
  src/                      # codice applicativo
  db/
    migrations/             # migrazioni schema (Flyway, Alembic, Liquibase)
    seeds/                  # dati iniziali per sviluppo/test
    functions/              # stored procedures e funzioni
    views/                  # viste e materialized views
    policies/               # Row Level Security policies
    grants/                 # permessi (da applicare in CI/CD)
  tests/
    db/                     # test di integrazione per le migrazioni
```

### Monitoring Baseline

Metriche fondamentali da monitorare per ogni database:

```
=== Metriche Universali ===
- Connessioni attive / massime
- Query al secondo (throughput)
- Latenza media e percentili (p50, p95, p99)
- Errori per secondo
- Cache/buffer hit ratio (target > 99%)
- Dimensione database e tasso di crescita
- Replica lag (secondi o bytes)
- Spazio disco utilizzato / disponibile
- CPU e memoria del server
- I/O disco (IOPS, throughput, latenza)

=== PostgreSQL Specifiche ===
- Dead tuples e frequenza autovacuum
- Transaction wraparound proximity (critico)
- WAL generation rate
- Checkpoint frequency e duration
- Lock waits e deadlocks
- Temporary files creati

=== MySQL Specifiche ===
- InnoDB buffer pool hit ratio
- Threads running vs threads connected
- Binary log size e growth
- Table open cache hit ratio
- InnoDB row lock waits

=== Redis Specifiche ===
- Memory used vs maxmemory
- Evicted keys per second
- Keyspace hit ratio
- Connected clients
- RDB/AOF last save status

=== MongoDB Specifiche ===
- Oplog window (ore di retention)
- Document/query scanned vs returned ratio
- Page faults
- WiredTiger cache utilization
- Ticket availability (read/write)
```

### Capacity Planning

Il capacity planning richiede dati storici e proiezioni:

1. **Raccogliere metriche storiche**: almeno 3-6 mesi di dati su dimensione DB, throughput, latenza, risorse.
2. **Identificare trend**: crescita lineare, esponenziale, stagionale.
3. **Proiettare**: quando le risorse correnti saranno saturate (CPU > 70% sostenuto, disco > 80%, connessioni > 80%).
4. **Pianificare**: aggiornamento hardware, sharding, partitioning, archiviation dei dati storici.

### Upgrade Strategies

**Rolling Upgrade**: aggiornare i nodi uno alla volta, con failover. Minimizza il downtime ma richiede compatibilita tra versioni.

**Blue-Green**: due ambienti identici. Aggiornare l'ambiente inattivo, testare, poi switchare il traffico. Rollback immediato in caso di problemi.

**Logical Replication Upgrade**: per major version upgrade di PostgreSQL, configurare logical replication dalla vecchia alla nuova versione. Quando sincronizzato, switchare le applicazioni.

```bash
# PostgreSQL major version upgrade con pg_upgrade
# 1. Installare la nuova versione
sudo apt install postgresql-17

# 2. Fermare entrambi i servizi
sudo systemctl stop postgresql

# 3. Eseguire pg_upgrade in modalita check
sudo -u postgres /usr/lib/postgresql/17/bin/pg_upgrade \
    --old-datadir /var/lib/postgresql/16/main \
    --new-datadir /var/lib/postgresql/17/main \
    --old-bindir /usr/lib/postgresql/16/bin \
    --new-bindir /usr/lib/postgresql/17/bin \
    --check

# 4. Se il check passa, eseguire l'upgrade
sudo -u postgres /usr/lib/postgresql/17/bin/pg_upgrade \
    --old-datadir /var/lib/postgresql/16/main \
    --new-datadir /var/lib/postgresql/17/main \
    --old-bindir /usr/lib/postgresql/16/bin \
    --new-bindir /usr/lib/postgresql/17/bin \
    --link    # usa hard link anziche copiare (piu veloce)

# 5. Avviare la nuova versione e analizzare le statistiche
sudo systemctl start postgresql@17-main
sudo -u postgres /usr/lib/postgresql/17/bin/vacuumdb --all --analyze-in-stages
```

### Compliance: GDPR

**Data Retention**: definire policy di retention per ogni tipo di dato. Eliminare automaticamente i dati quando non piu necessari.

```sql
-- Esempio: eliminazione automatica dei log dopo 90 giorni
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';

-- Partitioning per facilitare la retention
-- Creare partizioni mensili e droppare le partizioni scadute
ALTER TABLE audit_logs DETACH PARTITION audit_logs_2025_01;
DROP TABLE audit_logs_2025_01;
```

**Right to Be Forgotten**: implementare procedure per la cancellazione dei dati personali su richiesta dell'utente.

```sql
-- Procedura di anonimizzazione (preferibile alla cancellazione per integrita referenziale)
CREATE OR REPLACE FUNCTION anonymize_user(p_user_id BIGINT) RETURNS VOID AS $$
BEGIN
    UPDATE users SET
        email = 'deleted_' || p_user_id || '@anonymized.local',
        name = 'Utente Rimosso',
        phone = NULL,
        address = NULL,
        date_of_birth = NULL,
        anonymized_at = NOW()
    WHERE id = p_user_id;

    -- Rimuovere dati da tabelle correlate non necessarie
    DELETE FROM user_sessions WHERE user_id = p_user_id;
    DELETE FROM user_preferences WHERE user_id = p_user_id;

    -- Log dell'operazione (senza dati personali)
    INSERT INTO gdpr_audit_log (action, entity_type, entity_id, performed_at)
    VALUES ('ANONYMIZE', 'user', p_user_id, NOW());
END;
$$ LANGUAGE plpgsql;
```

**Data Classification**: classificare i dati per sensibilita e applicare controlli proporzionati.

```
PUBBLICO:       nomi prodotti, prezzi, contenuti del sito
INTERNO:        metriche di performance, log operativi
CONFIDENZIALE:  email utenti, indirizzi, dati di pagamento
RISERVATO:      password hash, chiavi API, dati sanitari
```

Per ogni livello, definire: chi puo accedere, come viene protetto (crittografia, masking), per quanto viene conservato, e come viene eliminato.

**Data Masking per Ambienti Non-Production**: i dati di produzione non devono mai essere copiati tal quali in ambienti di sviluppo o staging. Implementare una pipeline di masking che anonimizza i dati sensibili preservando la struttura e le relazioni referenziali.

```sql
-- Pipeline di masking per PostgreSQL
-- Creare un database di staging da un dump di produzione

-- 1. Restore del backup in ambiente staging
-- pg_restore -d staging_db backup_prod.dump

-- 2. Masking dei dati sensibili
UPDATE users SET
    email = 'user_' || id || '@staging.local',
    name = 'Test User ' || id,
    phone = '+39 000 000 ' || lpad(id::text, 4, '0'),
    address = id || ' Via di Test, Roma',
    date_of_birth = '1990-01-01'::date + (id % 10000 || ' days')::interval;

-- 3. Randomizzare i dati finanziari preservando i range
UPDATE orders SET
    total = round((random() * 500 + 10)::numeric, 2),
    payment_reference = 'STAGING-' || id;

-- 4. Troncare tabelle con dati altamente sensibili
TRUNCATE TABLE payment_methods, user_sessions, audit_logs;

-- 5. Resettare le sequenze
SELECT setval(pg_get_serial_sequence('users', 'id'),
    (SELECT max(id) FROM users));

-- 6. VACUUM FULL per compattare (e impedire recovery dei dati originali)
VACUUM FULL;
```

**Compliance Audit Trail**: per settori regolamentati (finanza, sanità, pubblica amministrazione), l'audit trail deve essere tamper-proof — cioè non modificabile nemmeno da amministratori del database. Implementare con:

1. **Tabelle di audit append-only**: revocare UPDATE e DELETE sulla tabella di audit per tutti i ruoli, incluso il DBA. Solo INSERT è permesso.
2. **Trigger automatici**: catturare ogni modifica (INSERT, UPDATE, DELETE) sulle tabelle monitorate con un trigger che registra: chi, quando, cosa è cambiato, il valore prima e dopo.
3. **Log immutabili esterni**: inoltrare gli audit log a un sistema esterno (SIEM, S3 con Object Lock, blockchain privata) dove non possono essere alterati.

```sql
-- Trigger di audit automatico
CREATE OR REPLACE FUNCTION audit_trigger_func() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name, operation, row_id,
        old_data, new_data,
        changed_by, changed_at
    ) VALUES (
        TG_TABLE_NAME, TG_OP,
        COALESCE(NEW.id, OLD.id),
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) END,
        current_user, NOW()
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Applicare a una tabella sensibile
CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Proteggere la tabella di audit
REVOKE UPDATE, DELETE ON audit_log FROM PUBLIC;
REVOKE UPDATE, DELETE ON audit_log FROM app_user;
-- Solo il superuser può (e non dovrebbe) modificarla
```

### Disaster Recovery Planning

Il disaster recovery non è solo backup — è la capacità di ripristinare l'intero servizio database in tempi definiti dopo un evento catastrofico. Un piano DR completo deve definire:

**RPO (Recovery Point Objective)**: quanti dati possiamo permetterci di perdere. RPO = 0 richiede replicazione sincrona (performance penalizzata). RPO = 1 ora è raggiungibile con WAL archiving continuo. RPO = 24 ore è sufficiente con backup giornalieri.

**RTO (Recovery Time Objective)**: quanto tempo può durare il downtime. RTO < 30 secondi richiede failover automatico (Patroni, CloudNativePG). RTO < 1 ora è raggiungibile con standby server pronto e procedure di failover documentate. RTO < 4 ore richiede backup verificati e procedure di restore testate.

**Matrice di scenari DR**:

| Scenario | RPO target | RTO target | Strategia |
|----------|-----------|-----------|-----------|
| Corruzione singola tabella | 0 (PITR) | < 30 min | pg_dump tabella da PITR + restore selettivo |
| Crash del server primario | < 1 min | < 30 sec | Failover automatico su standby (Patroni) |
| Perdita datacenter | < 5 min | < 1 ora | Standby in datacenter remoto + DNS failover |
| Ransomware/attacco | 0 (backup offsite) | < 4 ore | Restore da backup isolato (air-gapped) |
| Errore umano (DROP TABLE) | 0 (PITR) | < 15 min | PITR al momento prima dell'errore |

**Test DR obbligatorio**: eseguire un drill completo almeno trimestralmente. Il drill deve simulare lo scenario più probabile (crash del primary) e misurare RPO e RTO effettivi. Un piano DR non testato è un piano inesistente.

---

## Esercizi

### Esercizio 1 — Backup e Restore Drill

**Obiettivo**: configurare un backup automatico giornaliero di un database PostgreSQL e testare il restore completo.

**Passi**:
1. Creare un database `app_production` con almeno 3 tabelle e dati realistici (>10.000 righe totali).
2. Configurare un cron job che esegue `pg_dump` compresso con `pg_dump -Fc -Z6 -f /backup/app_$(date +%Y%m%d).dump app_production`.
3. Aggiungere retention automatica: eliminare backup più vecchi di 30 giorni con `find /backup -name "*.dump" -mtime +30 -delete`.
4. Simulare la perdita del database: `DROP DATABASE app_production;`.
5. Ripristinare da backup con `pg_restore -C -d postgres /backup/app_latest.dump`.
6. Verificare l'integrità dei dati: conteggio righe per tabella, checksum di un campione, verifica vincoli FK.
7. Misurare e documentare RPO (dati persi tra ultimo backup e crash) e RTO (tempo effettivo del restore).
8. Ripetere con backup incrementale usando WAL archiving per ridurre RPO a pochi secondi.
9. Testare il restore su un server diverso per verificare la portabilità del backup.
10. **Verifica**: il database ripristinato è funzionalmente identico all'originale — tutti i test applicativi passano.

### Esercizio 2 — Connection Pooling con PgBouncer

**Obiettivo**: installare PgBouncer, configurarlo e misurare l'impatto sulle performance.

**Passi**:
1. Installare PgBouncer: `sudo apt install pgbouncer`.
2. Configurare `/etc/pgbouncer/pgbouncer.ini`:
   - `pool_mode = transaction`
   - `default_pool_size = 25`
   - `max_client_conn = 200`
   - `reserve_pool_size = 5`
   - `reserve_pool_timeout = 3`
3. Generare `userlist.txt` con le credenziali: `SELECT '"' || usename || '" "' || passwd || '"' FROM pg_shadow;`.
4. Avviare PgBouncer e verificare la connessione: `psql -h 127.0.0.1 -p 6432 -U app_user app_db`.
5. Eseguire `SHOW POOLS;` e `SHOW CLIENTS;` dalla console admin di PgBouncer.
6. Benchmark diretto a PostgreSQL: `pgbench -c 100 -j 10 -T 30 -U app_user app_db` (porta 5432).
7. Benchmark via PgBouncer: `pgbench -c 100 -j 10 -T 30 -h 127.0.0.1 -p 6432 -U app_user app_db`.
8. Confrontare: TPS (transactions per second), latenza media, connessioni attive in `pg_stat_activity`.
9. Configurare TLS tra client e PgBouncer e tra PgBouncer e PostgreSQL.
10. Testare le limitazioni: verificare che LISTEN/NOTIFY e prepared statements SQL non funzionino in transaction mode.
11. **Verifica**: con PgBouncer, PostgreSQL mantiene al massimo `default_pool_size` connessioni anche con 200 client concorrenti.

### Esercizio 3 — Replication e Failover

**Obiettivo**: configurare streaming replication e simulare un failover completo.

**Passi**:
1. Preparare due istanze PostgreSQL (container Docker o VM): primary (10.0.1.1) e standby (10.0.1.2).
2. Sul primary: `wal_level = replica`, `max_wal_senders = 5`, `max_replication_slots = 5`.
3. Creare il ruolo di replicazione: `CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD '...';`.
4. Configurare `pg_hba.conf` per consentire la connessione di replica.
5. Sul standby: `pg_basebackup -h 10.0.1.1 -D /var/lib/postgresql/16/main -U replicator -R -P`.
6. Avviare lo standby e verificare lo streaming: `SELECT * FROM pg_stat_replication;` sul primary.
7. Creare una tabella e inserire dati sul primary. Verificare che appaiano sullo standby.
8. Simulare il crash: `sudo systemctl stop postgresql` sul primary.
9. Promuovere lo standby: `SELECT pg_promote();` (PostgreSQL 12+) oppure `pg_ctl promote`.
10. Verificare che il nuovo primary accetti scritture e che `pg_is_in_recovery()` restituisca `false`.
11. Misurare il tempo di failover (dall'arresto del primary alla prima scrittura sul nuovo primary).
12. **Verifica**: RPO = 0 (se sincrono) o < 1 secondo (se asincrono); downtime < 30 secondi con promozione manuale.

### Esercizio 4 — Query Tuning e Indexing

**Obiettivo**: analizzare query lente, creare indici strategici e misurare il miglioramento.

**Passi**:
1. Creare una tabella `orders` con 1M+ righe generate con `generate_series` e dati randomici.
2. Eseguire le query tipiche senza indici e salvare i piani con `EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT JSON)`.
3. Identificare i sequential scan su tabelle grandi e i sort esterni (external merge).
4. Creare indici B-tree sulle colonne più filtrate: `CREATE INDEX idx_orders_status ON orders(status);`.
5. Creare un partial index per query frequenti su subset: `CREATE INDEX idx_orders_pending ON orders(created_at) WHERE status = 'pending';`.
6. Creare un indice GIN per ricerche full-text o JSONB: `CREATE INDEX idx_orders_meta ON orders USING gin(metadata jsonb_path_ops);`.
7. Rieseguire le stesse query e confrontare i piani — documentare: tipo di scan (Index vs Seq), tempo effettivo, buffer hit/read.
8. Verificare l'impatto degli indici sulle scritture: `pgbench` con e senza indici.
9. Identificare indici inutilizzati con `pg_stat_user_indexes` (idx_scan = 0) e rimuoverli.
10. **Verifica**: la query più lenta passa da >1s a <50ms; il rapporto buffer hit/(hit+read) è >99%.

### Esercizio 5 — GDPR Data Anonymization Pipeline

**Obiettivo**: implementare una pipeline completa di anonimizzazione conforme GDPR.

**Passi**:
1. Creare le tabelle: `users`, `user_sessions`, `user_preferences`, `orders`, `gdpr_audit_log`.
2. Popolare con dati realistici (nomi, email, indirizzi, telefoni — dati fittizi).
3. Implementare la stored procedure `anonymize_user(p_user_id)` che:
   - Sostituisce email con `deleted_{id}@anonymized.local`
   - Imposta nome a "Utente Rimosso", telefono/indirizzo/data_nascita a NULL
   - Registra `anonymized_at = NOW()`
   - Elimina sessioni e preferenze dell'utente
   - Mantiene gli ordini (necessari per contabilità) ma senza riferimento ai dati personali
   - Inserisce un record nell'audit log senza dati personali
4. Testare: eseguire `anonymize_user` su 5 utenti e verificare che i dati personali siano irreversibilmente rimossi.
5. Verificare l'integrità referenziale: gli ordini dell'utente anonimizzato devono ancora esistere.
6. Verificare l'irreversibilità: non deve essere possibile risalire all'identità originale dell'utente.
7. Implementare una procedura batch per anonimizzazione di massa (utenti inattivi da > 3 anni).
8. Aggiungere una vista `vw_gdpr_report` che mostra: utenti anonimizzati, data, audit trail.
9. **Verifica**: `SELECT * FROM users WHERE id = <anonimizzato>` non contiene dati personali; l'audit log registra l'operazione completa.

### Esercizio 6 — Database su Kubernetes con CloudNativePG

**Obiettivo**: deployare un cluster PostgreSQL HA su Kubernetes usando l'operatore CloudNativePG.

**Passi**:
1. Installare l'operatore CloudNativePG nel cluster Kubernetes: `kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.4.yaml`.
2. Creare un manifest `Cluster` con 3 istanze (1 primary + 2 standby):

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: app-db
spec:
  instances: 3
  storage:
    size: 10Gi
    storageClass: standard
  postgresql:
    parameters:
      shared_buffers: "256MB"
      max_connections: "200"
  backup:
    barmanObjectStore:
      destinationPath: "s3://backup-bucket/cnpg/"
      s3Credentials:
        accessKeyId:
          name: s3-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: s3-creds
          key: SECRET_ACCESS_KEY
```

3. Applicare il manifest e attendere che tutte le istanze siano Ready.
4. Connettersi al primary: `kubectl exec -it app-db-1 -- psql -U postgres`.
5. Creare un database e inserire dati di test.
6. Simulare il crash del primary: `kubectl delete pod app-db-1`.
7. Verificare che l'operatore promuova automaticamente uno standby e ricrei il pod mancante.
8. Verificare che i dati siano intatti dopo il failover.
9. Eseguire un backup on-demand: `kubectl apply -f backup.yaml` (tipo `Backup`).
10. **Verifica**: il failover completa in < 30 secondi; i dati sono consistenti; il backup su S3 è valido.

### Esercizio 7 — Multi-Database Monitoring Stack

**Obiettivo**: creare un sistema di monitoring unificato per PostgreSQL, MySQL e Redis.

**Passi**:
1. Deployare istanze PostgreSQL, MySQL e Redis (locale o Docker Compose).
2. Configurare i rispettivi exporter Prometheus:
   - `postgres_exporter` con DSN configurato
   - `mysqld_exporter` con utente dedicato `GRANT SELECT, PROCESS, REPLICATION CLIENT`
   - `redis_exporter` con connessione all'istanza Redis
3. Configurare Prometheus per scrape degli exporter.
4. Importare le dashboard Grafana standard per ciascun database (ID: 9628 per PostgreSQL, 7362 per MySQL, 763 per Redis).
5. Creare alert rules per:
   - PostgreSQL: cache hit ratio < 95%, replication lag > 1MB, XID age > 500M
   - MySQL: InnoDB buffer pool hit ratio < 95%, threads_running > 50
   - Redis: memory_used > 80% di maxmemory, evicted_keys > 0
6. Simulare un problema (tabella senza vacuum, query senza indice, cache Redis piena) e verificare che l'alerting lo rilevi.
7. **Verifica**: ogni alert produce una notifica con informazioni azionabili entro 2 minuti dal problema.

---

## Troubleshooting Cross-Database

### Problema: Connessioni esaurite in applicazione multi-database

**Sintomi**: l'applicazione non riesce a connettersi a uno o più database. Errori come `too many connections` (PostgreSQL), `Too many connections` (MySQL), o connessioni che restano in stato `idle` indefinitamente.

**Causa**: ogni servizio dell'applicazione apre connessioni verso più database (PostgreSQL per dati relazionali, Redis per cache, MongoDB per documenti). Senza connection pooling coordinato, il numero totale di connessioni può superare i limiti configurati.

**Soluzione**:
1. **PostgreSQL**: pgBouncer in transaction mode. Verificare `pg_stat_activity` per connessioni idle.
2. **MySQL**: ProxySQL come pooler. Verificare `SHOW PROCESSLIST` per connessioni bloccate.
3. **Redis**: configurare `maxclients` e monitorare con `CLIENT LIST | wc -l`.
4. **Applicazione**: configurare il pool di ogni driver con limiti espliciti. La somma dei `pool_size` di tutte le istanze dell'applicazione non deve superare `max_connections` del database.

### Problema: Latenza database variabile in Kubernetes

**Sintomi**: le query hanno tempi di risposta normalmente bassi (< 10ms) ma periodicamente salgono a centinaia di millisecondi o secondi. Il pattern è irregolare e difficile da riprodurre.

**Causa**: (1) Pod database su nodo Kubernetes con risorse condivise — altri pod consumano CPU/I/O (noisy neighbor). (2) Storage class con IOPS non garantiti (es. EBS gp2 burst). (3) Pod reschedulato su un nodo diverso con cold cache.

**Soluzione**: (1) Usare node affinity e taints/tolerations per dedicare nodi al database. (2) Usare storage class con IOPS garantiti (gp3 con IOPS configurati, io2). (3) Impostare resource limits e requests corretti per CPU e memoria. (4) Verificare che `shared_buffers` e `effective_cache_size` siano allineati con le risorse del pod.

---

## Letture e Riferimenti

### Documentazione ufficiale

- PostgreSQL 17 Documentation — <https://www.postgresql.org/docs/17/> (consultato: 2026-05-24)
- MySQL 8.4 Reference Manual — <https://dev.mysql.com/doc/refman/8.4/en/> (consultato: 2026-05-24)
- MongoDB Manual v8.0 — <https://www.mongodb.com/docs/manual/> (consultato: 2026-05-24)
- PgBouncer Documentation — <https://www.pgbouncer.org/config.html> (consultato: 2026-05-24)
- AWS RDS User Guide — <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/> (consultato: 2026-05-24)

### Libri consigliati

- Kleppmann M., *Designing Data-Intensive Applications*, O'Reilly, 2017
- Schönig H.-J., *Mastering PostgreSQL 17*, Packt, 2025
- Petrov A., *Database Internals*, O'Reilly, 2019

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con Database Management |
|--------|--------|-----------------------------------|
| [01](01-cloud-aws.md) | Cloud AWS | RDS, Aurora, DynamoDB — servizi database managed AWS |
| [02](02-cloud-azure.md) | Cloud Azure | Azure SQL, Cosmos DB — servizi database managed Azure |
| [03](03-cloud-gcp.md) | Cloud GCP | Cloud SQL, Spanner, Firestore — servizi database managed GCP |
| [08](08-monitoring-observability.md) | Monitoring e Observability | Metriche database, query performance, alerting su latenza |
| [14](14-compliance.md) | Compliance e Normative | GDPR data retention, anonimizzazione, audit trail |
| [15](15-secrets-management.md) | Secrets Management | Credenziali database, rotation automatica, dynamic secrets |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **RPO (Recovery Point Objective)** | Quantita massima di dati che si accetta di perdere in caso di disastro, espressa in tempo |
| **RTO (Recovery Time Objective)** | Tempo massimo entro cui il servizio deve essere ripristinato dopo un'interruzione |
| **Replication** | Processo di copia dei dati da un database primario a una o piu repliche per disponibilita e scalabilita |
| **Sharding** | Partizionamento orizzontale dei dati su piu istanze per distribuire il carico e la capacita di storage |
| **Connection Pooling** | Tecnica di riutilizzo delle connessioni al database per ridurre overhead e migliorare la concorrenza |
| **WAL (Write-Ahead Log)** | Registro sequenziale delle modifiche scritto prima dell'applicazione effettiva, garantendo durabilita |
| **MVCC (Multi-Version Concurrency Control)** | Meccanismo che consente letture concorrenti senza blocco mantenendo versioni multiple delle righe |
| **Failover** | Passaggio automatico o manuale dal nodo primario a uno standby in caso di guasto |
| **PgBouncer** | Lightweight connection pooler per PostgreSQL che gestisce le connessioni tra client e server |
| **Backup incrementale** | Backup che salva solo i dati modificati rispetto all'ultimo backup completo, riducendo tempo e spazio |
| **Anonimizzazione** | Processo irreversibile di rimozione di informazioni personali identificabili (PII) dai dati |
| **Query plan** | Piano di esecuzione generato dall'ottimizzatore per determinare il modo piu efficiente di eseguire una query |
| **Indice GIN** | Generalized Inverted Index, ottimizzato per ricerche full-text, array e dati JSONB in PostgreSQL |
| **Data classification** | Categorizzazione dei dati per livello di sensibilita per applicare controlli di accesso proporzionati |
| **Managed database** | Servizio database gestito dal cloud provider che automatizza backup, patching e alta disponibilita |
| **Blue-Green deployment** | Strategia di upgrade che mantiene due ambienti identici (blue attivo, green inattivo) per switchover rapido e rollback immediato |
| **pg_upgrade** | Tool ufficiale PostgreSQL per major version upgrade che opera copiando o linkando i file di dati tra versioni |
| **Logical replication** | Replicazione basata su decodifica logica dei WAL; replica tabelle specifiche tra versioni diverse, cluster diversi o con subscriber scrivibili |
| **CloudNativePG** | Operatore Kubernetes per PostgreSQL che automatizza deploy, failover, backup e scaling di cluster PostgreSQL su Kubernetes |
| **Noisy neighbor** | Problema di performance in ambienti condivisi dove un workload consuma risorse (CPU, I/O, rete) impattando altri workload sullo stesso host |
| **Data masking** | Tecnica di protezione che sostituisce dati sensibili con dati realistici ma fittizi, preservando la struttura per ambienti non-production |
| **Audit trigger** | Trigger di database che registra automaticamente ogni modifica (INSERT, UPDATE, DELETE) in una tabella di audit per tracciabilità e compliance |
