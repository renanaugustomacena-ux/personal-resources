# Tutorial Linux 18 — Database: PostgreSQL Install, pg_hba, Tuning, pg_dump

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** PostgreSQL installazione, configurazione, tuning, backup, replica, sicurezza
> **Prerequisiti:** `tutorial_linux_06_storage.md`, `tutorial_linux_11_sicurezza.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
PostgreSQL su Linux
│
├── Installazione
│   ├── repo PGDG ufficiale
│   ├── cluster init
│   └── postgresql.conf principale
│
├── Autenticazione
│   ├── pg_hba.conf — regole accesso
│   ├── md5 / scram-sha-256
│   └── Ruoli e permessi
│
├── Tuning performance
│   ├── Memory: shared_buffers, work_mem
│   ├── I/O: effective_io_concurrency
│   ├── WAL: wal_level, checkpoint
│   └── Connection pool (PgBouncer)
│
├── Backup
│   ├── pg_dump / pg_dumpall
│   ├── pg_basebackup (fisico)
│   └── pgBackRest
│
├── Manutenzione
│   ├── VACUUM / ANALYZE / REINDEX
│   ├── pg_stat_* views
│   └── Slow query log
│
└── Alta disponibilità
    ├── Streaming replication
    ├── Logical replication
    └── Patroni / Repmgr
```

---

# Parte A — Installazione e configurazione base

---

## A1. Installazione PostgreSQL

```bash
# Repository PGDG (PostgreSQL Global Development Group)
apt install -y postgresql-common
/usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# Installa PostgreSQL 16
apt install -y postgresql-16 postgresql-client-16

# RHEL/Fedora
dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
dnf -qy module disable postgresql
dnf install -y postgresql16-server postgresql16
/usr/pgsql-16/bin/postgresql-16-setup initdb
systemctl enable --now postgresql-16

# Ubuntu: cluster viene inizializzato automaticamente
systemctl enable --now postgresql
systemctl status postgresql

# Accedi come utente postgres
sudo -u postgres psql
# oppure
psql -U postgres -h localhost

# Verifica versione
psql -U postgres -c "SELECT version();"
```

---

## A2. pg_hba.conf — controllo accessi

```bash
# /etc/postgresql/16/main/pg_hba.conf
# Formato: type database user address method [options]

# Metodi:
# trust        = accesso senza password (PERICOLOSO su prod!)
# md5          = password hashata MD5 (obsoleto, usa scram)
# scram-sha-256 = autenticazione moderna sicura
# peer         = usa utente OS (solo connessioni locali unix socket)
# reject       = nega accesso

# Configurazione tipica produzione
cat > /etc/postgresql/16/main/pg_hba.conf << 'EOF'
# Local connections
# postgres usa peer (nessuna password richiesta per utente OS postgres)
local   all             postgres                                peer

# Applicazioni locali via socket UNIX
local   appdb           appuser                                 scram-sha-256

# Connessioni TCP locali
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256

# Rete interna — solo per monitoring
host    postgres        monitoring      10.0.0.100/32           scram-sha-256

# Replica — solo da server slave
host    replication     replica         10.0.0.6/32             scram-sha-256

# NEGA tutto il resto
host    all             all             0.0.0.0/0               reject
EOF

# Ricarica senza restart
sudo -u postgres pg_ctlcluster 16 main reload
# oppure:
systemctl reload postgresql
```

> **Analogia:** pg_hba.conf è come il registratore del portiere di un condominio. Per ogni tentativo di entrata, controlla: da dove arriva (indirizzo), chi è (utente), a quale appartamento vuole andare (database), e che metodo di identificazione usa (password, carta, badge). La prima riga che corrisponde viene applicata — le successive ignorate.

---

## A3. postgresql.conf — tuning

```bash
# /etc/postgresql/16/main/postgresql.conf

# ==========================================
# MEMORY — regola in base alla RAM disponibile
# ==========================================
# shared_buffers: 25% della RAM totale (cache dati PostgreSQL)
shared_buffers = 4GB        # per server con 16GB RAM

# work_mem: memoria per operazioni sort/join (per OGNI sort di OGNI query)
# Attenzione: molti processi × sort annidati = consumo alto!
# Formula: (RAM - shared_buffers) / (max_connections × 3)
work_mem = 64MB

# Memoria totale disponibile per query
effective_cache_size = 12GB  # 75% della RAM

# ==========================================
# WAL (Write-Ahead Log)
# ==========================================
wal_level = replica          # minimal/replica/logical
wal_compression = on
checkpoint_completion_target = 0.9
wal_buffers = 64MB
max_wal_size = 4GB
min_wal_size = 1GB

# ==========================================
# I/O
# ==========================================
# SSD: 200, NVMe: 500, HDD: 1-2
effective_io_concurrency = 200
random_page_cost = 1.1       # SSD: 1.1, HDD: 4.0

# ==========================================
# CONNESSIONI
# ==========================================
max_connections = 100        # usa PgBouncer per più connessioni
superuser_reserved_connections = 3

# ==========================================
# LOGGING
# ==========================================
log_destination = 'csvlog'
logging_collector = on
log_directory = '/var/log/postgresql'
log_min_duration_statement = 1000  # log query > 1 secondo
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0          # log tutti i file temporanei

# ==========================================
# AUTOVACUUM
# ==========================================
autovacuum = on              # MAI disabilitare in produzione!
autovacuum_vacuum_cost_delay = 2ms
autovacuum_vacuum_scale_factor = 0.02
autovacuum_analyze_scale_factor = 0.01
```

```bash
# Applica modifiche
systemctl restart postgresql

# Verifica parametri correnti
sudo -u postgres psql -c "SHOW shared_buffers;"
sudo -u postgres psql -c "SHOW work_mem;"

# pgTune — genera configurazione automatica
# https://pgtune.leopard.in.ua/
```

---

# Parte B — Gestione utenti e database

---

## B1. Utenti e permessi

```bash
# Connetti come postgres
sudo -u postgres psql

-- Crea database
CREATE DATABASE appdb
    ENCODING 'UTF8'
    LC_COLLATE 'it_IT.UTF-8'
    LC_CTYPE 'it_IT.UTF-8'
    TEMPLATE template0;

-- Crea utente applicazione (no superuser, no createdb)
CREATE USER appuser WITH
    PASSWORD 'password-sicura-qui'
    CONNECTION LIMIT 50
    VALID UNTIL '2025-12-31';

-- Permessi minimi necessari
GRANT CONNECT ON DATABASE appdb TO appuser;
\c appdb
GRANT USAGE ON SCHEMA public TO appuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO appuser;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO appuser;

-- Permessi per future tabelle
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO appuser;

-- Utente read-only (per analytics)
CREATE USER readonly WITH PASSWORD 'altra-password';
GRANT CONNECT ON DATABASE appdb TO readonly;
\c appdb
GRANT USAGE ON SCHEMA public TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO readonly;

-- Cambia password
ALTER USER appuser WITH PASSWORD 'nuova-password';

-- Revoca accesso
REVOKE ALL ON DATABASE appdb FROM appuser;
DROP USER appuser;
```

---

# Parte C — Backup

---

## C1. pg_dump

```bash
# Dump logico di un database
sudo -u postgres pg_dump appdb > /backup/appdb-$(date +%Y%m%d).sql

# Compresso (raccomandato)
sudo -u postgres pg_dump -Fc appdb > /backup/appdb-$(date +%Y%m%d).dump

# Solo schema (no dati)
pg_dump -s appdb > schema.sql

# Solo dati (no schema)
pg_dump -a appdb > dati.sql

# Tabelle specifiche
pg_dump -t utenti -t ordini appdb > utenti-ordini.sql

# Tutti i database + ruoli
pg_dumpall -U postgres > full-backup.sql
pg_dumpall -U postgres --globals-only > globals.sql   # solo ruoli

# Restore da dump compresso
pg_restore -U postgres -d appdb /backup/appdb-20240115.dump

# Restore con creazione database
pg_restore -U postgres --create -d postgres /backup/appdb-20240115.dump

# Restore solo schema
pg_restore -s -U postgres -d appdb /backup/appdb-20240115.dump

# Backup in parallelo (più veloce su tabelle grandi)
pg_dump -Fd -j 4 -f /backup/appdb-dir appdb
pg_restore -j 4 -d appdb /backup/appdb-dir
```

---

## C2. Script backup automatico

```bash
#!/usr/bin/env bash
# /opt/scripts/backup-postgres.sh
set -euo pipefail

BACKUP_DIR="/backup/postgresql"
RETENTION_DAYS=30
DATABASES=$(sudo -u postgres psql -t -c "SELECT datname FROM pg_database WHERE datname NOT IN ('template0','template1');")

mkdir -p "$BACKUP_DIR"

for db in $DATABASES; do
    echo "Backup: $db"
    sudo -u postgres pg_dump -Fc "$db" \
        > "$BACKUP_DIR/${db}-$(date +%Y%m%d_%H%M%S).dump"
done

# Pulizia backup vecchi
find "$BACKUP_DIR" -name "*.dump" -mtime +"$RETENTION_DAYS" -delete
echo "Backup completato."
```

---

# Parte D — Manutenzione e monitoring

---

## D1. Manutenzione

```bash
# VACUUM — libera spazio tabelle bloated
sudo -u postgres psql appdb -c "VACUUM VERBOSE;"
sudo -u postgres psql appdb -c "VACUUM FULL VERBOSE tablename;"  # lock!
sudo -u postgres psql appdb -c "VACUUM ANALYZE;"

# ANALYZE — aggiorna statistiche per query planner
sudo -u postgres psql appdb -c "ANALYZE VERBOSE;"

# Tabelle più grandi
sudo -u postgres psql appdb << 'SQL'
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total,
       pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
       pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
SQL

# Query lente
sudo -u postgres psql appdb << 'SQL'
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
SQL

# Blocchi tra query
sudo -u postgres psql appdb << 'SQL'
SELECT pid, usename, pg_blocking_pids(pid) AS blocked_by, query AS blocked_query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
SQL
```

---

# Parte E — Riepilogo

## Checklist sicurezza PostgreSQL

```bash
# 1. No accesso diretto da internet
# pg_hba.conf: host all all 0.0.0.0/0 reject

# 2. Usa scram-sha-256, non md5
# pg_hba.conf: host all all ... scram-sha-256

# 3. Password forti (usa generatore)
openssl rand -base64 32

# 4. Backup giornaliero e test restore mensile

# 5. Log query lente
log_min_duration_statement = 1000

# 6. Limitare connessioni per utente
ALTER USER appuser CONNECTION LIMIT 50;

# 7. Utenti con permessi minimi necessari
```

## Comandi psql essenziali

| Comando | Scopo |
|---|---|
| `\l` | Lista database |
| `\c db` | Connetti a database |
| `\dt` | Lista tabelle |
| `\d tabella` | Struttura tabella |
| `\du` | Lista utenti/ruoli |
| `\dp` | Permessi tabelle |
| `\timing` | Mostra tempo query |
| `\x` | Output espanso (colonne verticali) |
| `\q` | Esci |

## Prossimi passi

- `tutorial_linux_29_postgresql.md` — amministrazione avanzata completa
- `tutorial_linux_19_servizi_rete.md` — DNS, NFS, Samba
