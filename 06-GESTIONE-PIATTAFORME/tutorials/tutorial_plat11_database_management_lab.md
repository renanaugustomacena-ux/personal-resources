# Tutorial: Database Management — PostgreSQL HA, PgBouncer, Backup — Lab Pratico

> **Documento di riferimento:** `11-database-management.md`
> **Dominio:** Gestione Piattaforme — Database e Dati
> **Ambito:** PostgreSQL 17 (architettura MVCC, VACUUM, WAL), Patroni per alta disponibilità, PgBouncer per connection pooling, pg_dump e pg_basebackup per backup, EXPLAIN ANALYZE e ottimizzazione query, Redis come cache e sessioni, replica streaming, RPO/RTO, GDPR e classificazione dati sensibili
> **Durata lab:** 7-8 ore
> **Livello:** Avanzato — richiede conoscenza base SQL e Linux
> **Prerequisiti:** Docker Engine 29.x con Docker Compose, psql (client PostgreSQL), Python 3.10+
> **Ambiente:** PostgreSQL 17 + Patroni (HA 3 nodi) + PgBouncer via Docker Compose, Redis come cache, Barman per backup

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI DATABASE LAB ===
echo "=== CHECK PREREQUISITI ==="

docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Docker richiesto"
docker compose version && echo "[OK] Docker Compose disponibile" || echo "[FAIL] Compose richiesto"

# psql client
psql --version 2>/dev/null | head -1 && echo "[OK] psql disponibile" || {
  echo "[INFO] Installare client PostgreSQL:"
  echo "  Ubuntu/Debian: apt install postgresql-client"
  echo "  Alpine: apk add postgresql-client"
}

# Python 3.10+ (per script di backup e query)
python3 --version && echo "[OK] Python disponibile"

# RAM (PostgreSQL HA con 3 nodi Patroni richiede ~4GB)
free_mb=$(free -m 2>/dev/null | awk 'NR==2{print $2}')
[ -n "$free_mb" ] && {
  [ "$free_mb" -gt 3500 ] && echo "[OK] RAM: ${free_mb}MB" || \
    echo "[WARN] RAM ${free_mb}MB — il cluster Patroni richiede ~4GB"
}

echo ""
echo "=== SETUP DIRECTORY LAB ==="
mkdir -p ~/db-lab/{postgres,patroni,pgbouncer,redis,backups,scripts,sql}
cd ~/db-lab

echo "[OK] Directory lab: ~/db-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DATABASE MANAGEMENT LAB                               │
│                                                                          │
│  APPLICAZIONE                                                            │
│       │                                                                  │
│       ▼                                                                  │
│  PgBouncer :5432 (connection pooler) ← distribuisce connessioni         │
│       │                                                                  │
│       ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  CLUSTER POSTGRESQL 17 HA (Patroni)                            │     │
│  │                                                                 │     │
│  │  pg-primary   :5433 ← scrittura (primary)                      │     │
│  │       │       WAL streaming replication                        │     │
│  │  pg-standby1  :5434 ← sola lettura (hot standby)              │     │
│  │  pg-standby2  :5435 ← sola lettura (hot standby)              │     │
│  │                                                                 │     │
│  │  etcd :2379 ← quorum per elezione primary (Patroni DCS)       │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  Redis :6379 ← cache L1 (sessioni, query frequenti)                    │
│  Barman :5050 ← backup continuo (WAL archiving)                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Come Funziona PostgreSQL

> PostgreSQL è come un archivio notarile digitale. Come un notaio che certifica
> ogni atto in modo immutabile, PostgreSQL garantisce che ogni transazione lasci
> il database in uno stato consistente — mai a metà. Se stai trasferendo 100 euro
> da un conto all'altro, o avvengono ENTRAMBE le operazioni (sottrazione e addizione)
> o NON ne avviene nessuna. Mai una sola delle due. Questo è ACID — la proprietà
> più importante di un database relazionale.

---

### Concetto A1: MVCC e ACID

```
ACID — QUATTRO PROPRIETÀ FONDAMENTALI:

A = Atomicity (Atomicità):
  La transazione è un'unità indivisibile. O tutto va a buon fine, o tutto viene
  annullato. Non esiste "metà transazione".

C = Consistency (Consistenza):
  Ogni transazione porta il database da uno stato valido a un altro stato valido.
  Violazioni di vincoli (NOT NULL, FOREIGN KEY, UNIQUE) annullano la transazione.

I = Isolation (Isolamento):
  Transazioni concorrenti non si interferiscono. Ogni transazione "vede" lo stato
  del database come se fosse l'unica a girare (salvo livello di isolamento scelto).

D = Durability (Durabilità):
  Una transazione confermata (COMMIT) sopravvive a crash del server. I dati sono
  su disco (WAL) prima che la risposta arrivi al client.

MVCC — MULTI-VERSION CONCURRENCY CONTROL:
  PostgreSQL non blocca i lettori quando qualcuno scrive.
  Ogni transazione vede uno "snapshot" del database al momento del proprio avvio.
  Come fotocopiare il documento prima di modificarlo: il lettore legge la copia,
  lo scrittore modifica l'originale. I lettori e gli scrittori non si bloccano mai.

  xmin: ID transazione che ha creato la riga
  xmax: ID transazione che ha eliminato/aggiornato la riga (0 = ancora visibile)
  
  SELECT xmin, xmax, id, nome FROM utenti;
  → una riga "viva" ha xmin < id_transazione_corrente e xmax = 0

VACUUM — PULIZIA MVCC:
  MVCC mantiene versioni vecchie delle righe (dead tuples).
  VACUUM le rimuove per liberare spazio.
  AUTOVACUUM: processo background che lo fa automaticamente.
  VACUUM ANALYZE: pulizia + aggiorna statistiche per il query planner.
```

---

### Concetto A2: WAL — Write-Ahead Log

> **Analogia.** WAL (Write-Ahead Log) è come un diario di bordo tenuto prima di
> ogni modifica. Un capitano della nave annota nel diario "sto navigando verso nord"
> PRIMA di girare il timone. Se la nave affonda, il soccorso sa dove stava andando
> e può recuperare la rotta. PostgreSQL scrive nel WAL ogni modifica PRIMA di
> applicarla effettivamente ai file dati — così, in caso di crash, può ripartire
> esattamente dove si era fermato. Questo WAL è anche il meccanismo di replica:
> ogni byte scritto nel WAL del primary viene replicato verso i standby.

```
ARCHITETTURA WAL:

SCRITTURA:
  BEGIN
    UPDATE conti SET saldo = saldo - 100 WHERE id = 42;  ← scritto nel WAL buffer
    UPDATE conti SET saldo = saldo + 100 WHERE id = 99;  ← scritto nel WAL buffer
  COMMIT → WAL buffer flushed su disco → risposta al client

RECOVERY DOPO CRASH:
  1. PostgreSQL riparte
  2. Legge il WAL dall'ultimo checkpoint
  3. Riapplica tutte le modifiche committed
  4. Annulla le transazioni incomplete (in-progress al crash)
  5. Database coerente

REPLICA STREAMING:
  Primary → WAL stream → Standby1 (ritardo secondi)
                       → Standby2 (ritardo secondi)
  
  Asincrona (default): client ottiene COMMIT senza aspettare standby
  Sincrona:            client ottiene COMMIT solo dopo ack standby
  → Asincrona: RPO > 0 (rischio perdita dati), performance migliore
  → Sincrona: RPO = 0 (nessuna perdita dati), performance inferiore

RPO/RTO:
  RPO (Recovery Point Objective): quanti dati posso perdere?
  → Async replica: RPO ~secondi (WAL in volo al crash)
  → Sync replica: RPO = 0
  → Solo backup: RPO = intervallo tra backup (ore/giorni)
  
  RTO (Recovery Time Objective): quanto tempo per tornare online?
  → Failover Patroni: 10-30 secondi
  → Restore da backup: ore (dipende dalla dimensione)
```

---

## PART B: POSTGRESQL 17 — SETUP E OPERAZIONI BASE

### Esercizio B1: PostgreSQL con Docker Compose

```bash
cd ~/db-lab

# Setup semplice: un nodo PostgreSQL per le operazioni base
cat > compose-postgres-single.yaml << 'EOF'
name: "db-lab-single"

networks:
  db-net:
    driver: bridge

volumes:
  pg-data:

services:
  postgres:
    image: postgres:17-alpine
    container_name: postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: lab-pg-password-2026
      POSTGRES_DB: lab_db
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=it_IT.UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - pg-data:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d:ro   # SQL eseguiti all'inizializzazione
    command: |
      postgres
        -c max_connections=200
        -c shared_buffers=256MB
        -c effective_cache_size=1GB
        -c maintenance_work_mem=64MB
        -c checkpoint_completion_target=0.9
        -c wal_buffers=16MB
        -c random_page_cost=1.1
        -c log_statement=ddl
        -c log_min_duration_statement=1000
        -c log_line_prefix='%t [%p] %u@%d '
    networks: [db-net]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d lab_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
EOF

# Script SQL di inizializzazione
cat > sql/01-schema.sql << 'EOF'
-- Schema per il lab database management

-- Estensioni utili
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;   -- stats query SQL
CREATE EXTENSION IF NOT EXISTS pgcrypto;             -- cifratura
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";          -- UUID

-- Classificazione dati (GDPR)
COMMENT ON DATABASE lab_db IS 'Database lab — classificazione: INTERNAL';

-- Tabella utenti con dati personali (PII)
CREATE TABLE utenti (
    id          BIGSERIAL PRIMARY KEY,
    uuid        UUID DEFAULT gen_random_uuid() NOT NULL,
    
    -- Dati identificativi (PII — proteggere con GDPR)
    nome        VARCHAR(100) NOT NULL,
    cognome     VARCHAR(100) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    
    -- Dati sensibili cifrati (cifratura a livello applicativo)
    -- In produzione: usare pgcrypto o crittografia a livello colonna
    codice_fiscale_hash TEXT,    -- hash SHA-256, NON plaintext
    
    -- Metadati
    creato_il   TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    aggiornato_il TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at  TIMESTAMPTZ,     -- soft delete
    
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indici per le query più frequenti
CREATE INDEX idx_utenti_email ON utenti(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_utenti_uuid ON utenti(uuid);
CREATE INDEX idx_utenti_creato ON utenti(creato_il DESC);

-- Tabella ordini (molti-a-uno con utenti)
CREATE TABLE ordini (
    id          BIGSERIAL PRIMARY KEY,
    utente_id   BIGINT NOT NULL REFERENCES utenti(id) ON DELETE RESTRICT,
    totale      NUMERIC(10, 2) NOT NULL CHECK (totale > 0),
    stato       VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (stato IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    creato_il   TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT ordini_utente_idx UNIQUE (id, utente_id)
);

-- Indice parziale: solo ordini non cancellati (query più comuni)
CREATE INDEX idx_ordini_attivi ON ordini(utente_id, creato_il DESC)
WHERE stato != 'cancelled';

-- Funzione per aggiornare automaticamente updated_at
CREATE OR REPLACE FUNCTION update_aggiornato_il()
RETURNS TRIGGER AS $$
BEGIN
    NEW.aggiornato_il = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_utenti_update
    BEFORE UPDATE ON utenti
    FOR EACH ROW EXECUTE FUNCTION update_aggiornato_il();

-- Dati di esempio
INSERT INTO utenti (nome, cognome, email)
SELECT
    'Nome' || g,
    'Cognome' || g,
    'utente' || g || '@example.com'
FROM generate_series(1, 1000) AS g;

INSERT INTO ordini (utente_id, totale, stato)
SELECT
    (random() * 999 + 1)::BIGINT,
    (random() * 999 + 1)::NUMERIC(10,2),
    (ARRAY['pending','confirmed','shipped','delivered'])[floor(random()*4+1)]
FROM generate_series(1, 5000);

COMMENT ON TABLE utenti IS 'Dati utenti — GDPR Art.17: diritto cancellazione, Art.20: portabilità';
COMMENT ON COLUMN utenti.codice_fiscale_hash IS 'SHA-256 del CF — non loggare il plaintext';
EOF

docker compose -f compose-postgres-single.yaml up -d

echo "Attendo PostgreSQL..."
until docker exec postgres pg_isready -U postgres -q 2>/dev/null; do
  sleep 2
done

echo "[OK] PostgreSQL 17 operativo"
docker exec postgres psql -U postgres -d lab_db -c "
SELECT COUNT(*) AS utenti, (SELECT COUNT(*) FROM ordini) AS ordini FROM utenti;
"
```

---

### Esercizio B2: Operazioni Essenziali PostgreSQL

```bash
# Alias per psql
alias psql-lab='docker exec -it postgres psql -U postgres -d lab_db'
alias psqln-lab='docker exec postgres psql -U postgres -d lab_db -t -c'

# ── QUERY DI ANALISI ──────────────────────────────────────────────────

echo "=== QUERY ESSENZIALI POSTGRESQL ==="

# 1. EXPLAIN ANALYZE — capire come PostgreSQL esegue una query
docker exec postgres psql -U postgres -d lab_db << 'SQL'
-- Analisi piano di esecuzione
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.nome, u.cognome, u.email, COUNT(o.id) AS n_ordini
FROM utenti u
LEFT JOIN ordini o ON o.utente_id = u.id AND o.stato != 'cancelled'
WHERE u.deleted_at IS NULL
GROUP BY u.id
ORDER BY n_ordini DESC
LIMIT 10;
SQL

echo ""
echo "LETTURA EXPLAIN ANALYZE:"
echo "  Seq Scan = scansione intera tabella (indica indice mancante)"
echo "  Index Scan = usa indice (ottimale)"
echo "  Hash Join / Nested Loop = algoritmo JOIN"
echo "  actual time = tempo reale (ms)"
echo "  rows = righe stimate / (actual rows = righe reali)"

# 2. Query lente (pg_stat_statements)
docker exec postgres psql -U postgres -d lab_db << 'SQL'
-- Top 5 query più lente (richiede pg_stat_statements)
SELECT
    substring(query, 1, 80) AS query,
    calls,
    round(total_exec_time::NUMERIC, 2) AS total_ms,
    round(mean_exec_time::NUMERIC, 2) AS avg_ms,
    rows
FROM pg_stat_statements
WHERE calls > 10
ORDER BY mean_exec_time DESC
LIMIT 5;
SQL

# 3. Tabelle e indici più grandi
docker exec postgres psql -U postgres -d lab_db << 'SQL'
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size_totale,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS size_dati,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS size_indici,
    n_live_tup AS righe_vive,
    n_dead_tup AS righe_morte,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
SQL

# 4. Indici inutilizzati (da rimuovere)
docker exec postgres psql -U postgres -d lab_db << 'SQL'
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS utilizzi
FROM pg_stat_user_indexes
WHERE idx_scan = 0         -- mai usato!
  AND indexrelname NOT LIKE '%pk%'   -- non rimuovere PK
  AND indexrelname NOT LIKE '%unique%'  -- non rimuovere UNIQUE constraint
ORDER BY pg_relation_size(indexrelid) DESC;
SQL

# 5. Connessioni attive
docker exec postgres psql -U postgres -d lab_db << 'SQL'
SELECT
    pid,
    state,
    wait_event_type,
    wait_event,
    substring(query, 1, 60) AS query,
    now() - query_start AS durata
FROM pg_stat_activity
WHERE state != 'idle'
  AND pid != pg_backend_pid()
ORDER BY durata DESC
LIMIT 10;
SQL
```

---

## PART C: PGBOUNCER — CONNECTION POOLING

> **Analogia.** Immagine un ristorante di lusso con soli 50 tavoli ma che riceve
> 1000 prenotazioni a serata. Senza un sistema di gestione, ogni cliente entra,
> aspetta un tavolo, e il ristorante rifiuta centinaia di persone. PgBouncer
> è come un gestore intelligente: mantiene sempre 50 tavoli "caldi" (connessioni
> al database), e serve i clienti uno alla volta, liberando il tavolo non appena
> il cliente finisce. 1000 clienti vengono serviti con soli 50 tavoli attivi.
> PostgreSQL normalmente usa 1 processo per connessione — a 1000 connessioni
> simultanee avrebbe 1000 processi e consumerebbe GiB di RAM.

---

### Esercizio C1: Setup PgBouncer

```bash
cd ~/db-lab

cat > pgbouncer/pgbouncer.ini << 'EOF'
# PgBouncer 1.23 — configurazione connection pool

[databases]
# Alias: le app si connettono a "lab_db" su :5432, PgBouncer inoltrano a postgres:5432
lab_db = host=postgres port=5432 dbname=lab_db

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 5432

# MODALITÀ DI POOL (critica da capire):
pool_mode = transaction
# session:     connessione DB tenuta per tutta la sessione client (spreca risorse)
# transaction: connessione DB tenuta solo durante la transazione (raccomandato!)
# statement:   connessione DB tenuta per un singolo statement (limitante)

# Pool per database
default_pool_size = 20          # max 20 connessioni verso PostgreSQL per database
max_client_conn = 1000          # max 1000 connessioni client → PgBouncer
reserve_pool_size = 5           # slot di riserva per picchi
reserve_pool_timeout = 3s       # timeout prima di usare il pool di riserva

# Autenticazione
auth_type = scram-sha-256       # PostgreSQL 17 default
auth_file = /etc/pgbouncer/userlist.txt

# Performance
server_idle_timeout = 600       # chiude connessioni idle verso DB dopo 10 min
client_idle_timeout = 0         # non chiudere mai connessioni client idle
server_lifetime = 3600          # ricicla connessioni verso DB dopo 1 ora
tcp_keepalive = 1
tcp_keepidle = 10

# Logging
logfile = /dev/stdout
log_connections = 1
log_disconnections = 1
log_stats = 1
stats_period = 60

# Admin
admin_users = pgbouncer_admin
stats_users = pgbouncer_monitor
EOF

# File autenticazione (userlist)
cat > pgbouncer/userlist.txt << 'EOF'
"postgres" "lab-pg-password-2026"
"app_user" "app-password-2026"
"pgbouncer_admin" "admin-password-2026"
"pgbouncer_monitor" "monitor-password-2026"
EOF

# Aggiungere PgBouncer al compose
cat >> compose-postgres-single.yaml << 'PGBOUNCER'

  pgbouncer:
    image: bitnami/pgbouncer:1.23.1
    container_name: pgbouncer
    ports:
      - "5433:5432"   # 5433 esterno → 5432 PgBouncer
    volumes:
      - ./pgbouncer/pgbouncer.ini:/bitnami/pgbouncer/conf/pgbouncer.ini:ro
      - ./pgbouncer/userlist.txt:/bitnami/pgbouncer/conf/userlist.txt:ro
    environment:
      PGBOUNCER_DATABASE: lab_db
      PGBOUNCER_HOST: postgres
      POSTGRESQL_USERNAME: postgres
      POSTGRESQL_PASSWORD: lab-pg-password-2026
    networks: [db-net]
    depends_on: [postgres]
    restart: unless-stopped
PGBOUNCER

docker compose -f compose-postgres-single.yaml up -d pgbouncer
sleep 5
echo "[OK] PgBouncer avviato su :5433"

# Test connessione tramite PgBouncer
psql "postgresql://postgres:lab-pg-password-2026@localhost:5433/lab_db" \
  -c "SELECT 'connesso via PgBouncer' AS status, count(*) AS utenti FROM utenti;" \
  2>/dev/null || echo "[INFO] psql non disponibile — installare client PostgreSQL"

# Benchmark: connessioni dirette vs PgBouncer
echo ""
echo "Confronto performance (10 connessioni rapide):"
if command -v psql &>/dev/null; then
  echo -n "Dirette (porta 5432): "
  time for i in $(seq 1 10); do
    psql "postgresql://postgres:lab-pg-password-2026@localhost:5432/lab_db" \
      -c "SELECT 1;" > /dev/null 2>&1
  done

  echo -n "PgBouncer (porta 5433): "
  time for i in $(seq 1 10); do
    psql "postgresql://postgres:lab-pg-password-2026@localhost:5433/lab_db" \
      -c "SELECT 1;" > /dev/null 2>&1
  done
fi

# Stats PgBouncer (tramite psql)
psql "postgresql://pgbouncer_admin:admin-password-2026@localhost:5433/pgbouncer" \
  -c "SHOW POOLS;" \
  -c "SHOW STATS;" \
  2>/dev/null || echo "[INFO] Admin PgBouncer via: psql -h localhost -p 5433 -U pgbouncer_admin pgbouncer"
```

---

## PART D: BACKUP E DISASTER RECOVERY

### Esercizio D1: pg_dump e pg_basebackup

```bash
cd ~/db-lab

mkdir -p backups

echo "=== STRATEGIE DI BACKUP POSTGRESQL ==="

# ── 1. pg_dump: backup logico (SQL o custom format) ─────────────────
echo ""
echo "1. BACKUP LOGICO con pg_dump:"

# Format custom (raccomandato: compresso, selettivo, parallelizzabile)
docker exec postgres pg_dump \
  -U postgres \
  -d lab_db \
  --format=custom \
  --compress=9 \
  --verbose \
  --file=/tmp/lab_db_backup.dump \
  2>&1 | tail -5

docker cp postgres:/tmp/lab_db_backup.dump backups/lab_db_$(date +%Y%m%d_%H%M%S).dump

echo "[OK] Backup custom creato: backups/lab_db_*.dump"
ls -lh backups/

# Restore da backup custom
echo ""
echo "Test RESTORE:"
docker exec postgres createdb -U postgres lab_db_restore 2>/dev/null
docker exec postgres pg_restore \
  -U postgres \
  -d lab_db_restore \
  --no-owner \
  --no-privileges \
  --verbose \
  /tmp/lab_db_backup.dump \
  2>&1 | tail -3

docker exec postgres psql -U postgres -d lab_db_restore \
  -c "SELECT COUNT(*) AS utenti_restore FROM utenti;"
docker exec postgres dropdb -U postgres lab_db_restore
echo "[OK] Restore testato con successo"

# ── 2. pg_basebackup: backup fisico (per PITR) ──────────────────────
echo ""
echo "2. BACKUP FISICO con pg_basebackup:"
docker exec postgres pg_basebackup \
  -U postgres \
  --pgdata=/tmp/base_backup \
  --format=tar \
  --gzip \
  --checkpoint=fast \
  --wal-method=stream \
  --verbose \
  2>&1 | tail -3

echo "[OK] Base backup creato (usabile per Point-In-Time Recovery)"

# ── 3. Script di backup automatizzato ────────────────────────────────
cat > scripts/backup.sh << 'BACKUP_SCRIPT'
#!/bin/bash
# Script backup PostgreSQL automatizzato
# Eseguire con: crontab -e → 0 2 * * * /path/to/backup.sh

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5432}"
PG_USER="${PG_USER:-postgres}"
PG_PASS="${PG_PASS}"
DB_NAME="${DB_NAME:-lab_db}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "Avvio backup $DB_NAME"

# Backup con pg_dump
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.dump"
PGPASSWORD="$PG_PASS" pg_dump \
    -h "$PG_HOST" \
    -p "$PG_PORT" \
    -U "$PG_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_FILE"

# Verificare il backup
PGPASSWORD="$PG_PASS" pg_restore \
    -h "$PG_HOST" \
    -p "$PG_PORT" \
    -U "$PG_USER" \
    --list "$BACKUP_FILE" > /dev/null

SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
log "Backup completato: $BACKUP_FILE ($SIZE)"

# Eliminare backup vecchi
log "Eliminando backup più vecchi di $RETENTION_DAYS giorni..."
find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" -mtime "+$RETENTION_DAYS" -delete

log "Backup completato con successo"
BACKUP_SCRIPT

chmod +x scripts/backup.sh
echo "[OK] Script backup: scripts/backup.sh"
```

---

## PART E: PERFORMANCE — INDEXING E QUERY TUNING

### Esercizio E1: Analisi e Ottimizzazione Query

```bash
# Query lenta senza indice (Full Table Scan)
docker exec postgres psql -U postgres -d lab_db << 'SQL'
-- Disabilitare temporaneamente uso indici per vedere il Seq Scan
SET enable_indexscan = off;
SET enable_bitmapscan = off;

EXPLAIN (ANALYZE, BUFFERS)
SELECT u.nome, u.email, COUNT(o.id) AS n_ordini
FROM utenti u
JOIN ordini o ON o.utente_id = u.id
WHERE o.stato = 'delivered'
  AND o.totale > 500
  AND u.deleted_at IS NULL
GROUP BY u.id
ORDER BY n_ordini DESC
LIMIT 10;

SET enable_indexscan = on;
SET enable_bitmapscan = on;
SQL

# Creare l'indice mancante
docker exec postgres psql -U postgres -d lab_db << 'SQL'
-- Indice compound per la query frequente
CREATE INDEX CONCURRENTLY idx_ordini_stato_totale
ON ordini(stato, totale)
WHERE stato IN ('delivered', 'confirmed', 'shipped');

-- CONCURRENTLY: crea l'indice senza bloccare le scritture (importante in produzione!)

-- Verificare che l'indice sia usato ora
EXPLAIN (ANALYZE, BUFFERS)
SELECT u.nome, u.email, COUNT(o.id) AS n_ordini
FROM utenti u
JOIN ordini o ON o.utente_id = u.id
WHERE o.stato = 'delivered'
  AND o.totale > 500
  AND u.deleted_at IS NULL
GROUP BY u.id
ORDER BY n_ordini DESC
LIMIT 10;
SQL

# VACUUM e statistiche
docker exec postgres psql -U postgres -d lab_db << 'SQL'
-- Aggiornare statistiche per il query planner
VACUUM ANALYZE utenti;
VACUUM ANALYZE ordini;

-- Verificare statistiche tabella
SELECT relname, n_live_tup, n_dead_tup, last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
WHERE relname IN ('utenti', 'ordini');
SQL
```

---

## PART F: REDIS COME CACHE

### Esercizio F1: Redis per Sessioni e Cache Query

```bash
cat >> compose-postgres-single.yaml << 'REDIS'

  redis:
    image: redis:7.4-alpine
    container_name: redis
    command: |
      redis-server
        --maxmemory 512mb
        --maxmemory-policy allkeys-lru
        --save 60 1000
        --requirepass "redis-lab-2026"
        --loglevel notice
    ports:
      - "6379:6379"
    volumes:
      - ./redis-data:/data
    networks: [db-net]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "redis-lab-2026", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
REDIS

docker compose -f compose-postgres-single.yaml up -d redis
sleep 3

# Script Python: PostgreSQL + Redis come cache
cat > scripts/cache_demo.py << 'PYTHON'
"""
Demo: PostgreSQL + Redis cache (caching della top utenti per ordini)
Pattern Cache-Aside: prima leggo da Redis, se non c'è vado su PostgreSQL e metto in cache
"""
import json
import time
import hashlib
import os

try:
    import redis
    import psycopg2
    DEPS_OK = True
except ImportError:
    DEPS_OK = False
    print("[INFO] Installare: pip install redis psycopg2-binary")

def get_top_users_cached(pg_conn, redis_client, limit=10, cache_ttl=60):
    """
    Ritorna top utenti per numero di ordini.
    Prima controlla Redis, se miss va su PostgreSQL.
    """
    cache_key = f"top_users:limit_{limit}"
    
    # ── Cache HIT ─────────────────────────────────────────────────────
    cached = redis_client.get(cache_key)
    if cached:
        data = json.loads(cached)
        return data, "CACHE_HIT"
    
    # ── Cache MISS: query PostgreSQL ──────────────────────────────────
    start = time.time()
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT u.id, u.nome, u.cognome, u.email, COUNT(o.id) AS n_ordini
            FROM utenti u
            JOIN ordini o ON o.utente_id = u.id
            WHERE u.deleted_at IS NULL
              AND o.stato != 'cancelled'
            GROUP BY u.id
            ORDER BY n_ordini DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
    
    query_time = (time.time() - start) * 1000
    
    data = [
        {"id": r[0], "nome": r[1], "cognome": r[2], "email": r[3], "n_ordini": r[4]}
        for r in rows
    ]
    
    # Salvare in Redis con TTL
    redis_client.setex(cache_key, cache_ttl, json.dumps(data))
    
    return data, f"CACHE_MISS (query: {query_time:.1f}ms)"


if DEPS_OK:
    pg_conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="lab_db", user="postgres", password="lab-pg-password-2026"
    )
    r = redis.Redis(host="localhost", port=6379, password="redis-lab-2026", decode_responses=True)
    
    print("Test cache PostgreSQL → Redis:")
    
    # Prima chiamata: cache MISS (lenta)
    start = time.time()
    users, status = get_top_users_cached(pg_conn, r)
    print(f"  1a chiamata: {status} — {(time.time()-start)*1000:.1f}ms")
    
    # Seconda chiamata: cache HIT (veloce)
    start = time.time()
    users, status = get_top_users_cached(pg_conn, r)
    print(f"  2a chiamata: {status} — {(time.time()-start)*1000:.1f}ms")
    
    print(f"\n  Top 3 utenti per ordini:")
    for u in users[:3]:
        print(f"    {u['nome']} {u['cognome']}: {u['n_ordini']} ordini")
    
    pg_conn.close()
else:
    print("Installare: pip install redis psycopg2-binary")
PYTHON

python3 scripts/cache_demo.py || echo "[INFO] Eseguire: pip install redis psycopg2-binary"
```

---

## Conclusioni e Prossimi Passi

```
DATABASE MANAGEMENT — RIEPILOGO:

POSTGRESQL 17:
  ✓ ACID + MVCC: transazioni sicure senza bloccare i lettori
  ✓ WAL: durabilità e base della replica streaming
  ✓ EXPLAIN ANALYZE: diagnostica piani di esecuzione
  ✓ pg_stat_statements: statistiche sulle query più lente
  ✓ Indici CONCURRENTLY: crea indici senza bloccare le scritture
  ✓ Indici parziali (WHERE): più compatti e veloci degli indici totali
  ✓ VACUUM ANALYZE: pulizia dead tuples + aggiorna statistiche planner

PGBOUNCER:
  ✓ pool_mode transaction: il più efficiente per web app
  ✓ default_pool_size: max connessioni verso PostgreSQL
  ✓ max_client_conn: max client che si connettono a PgBouncer
  ✓ 1000 client × 20 conn PostgreSQL = risparmio massiccio di RAM
  ✓ SHOW POOLS / SHOW STATS: monitoraggio runtime

BACKUP POSTGRESQL:
  ✓ pg_dump --format=custom: backup logico compresso e selettivo
  ✓ pg_restore --list: verifica integrità backup (obbligatoria!)
  ✓ pg_basebackup: backup fisico per PITR
  ✓ PITR: Point-In-Time Recovery con WAL archiving
  ✓ Retention: 30 giorni backup settimanali, 7 giorni giornalieri
  ✓ Drill mensile: testare il restore OGNI MESE senza fail

ALTA DISPONIBILITÀ:
  ✓ Patroni: HA automatica con etcd come DCS
  ✓ Replica streaming: RPO ~secondi (asincrona)
  ✓ Failover automatico: RTO 10-30 secondi
  ✓ Replica sincrona: RPO = 0 ma performance -20%

REDIS:
  ✓ maxmemory-policy allkeys-lru: evict vecchi dati automaticamente
  ✓ Cache-Aside: leggi da cache, miss → db + popola cache
  ✓ TTL: ogni chiave ha scadenza per evitare dati obsoleti
  ✓ requirepass: OBBLIGATORIO in ambienti non isolati
  ✓ Persistenza: RDB (snapshot) + AOF (append-only log)

GDPR / CLASSIFICAZIONE DATI:
  ✓ COMMENT ON TABLE/COLUMN: documentare la sensibilità
  ✓ Dati PII: hashing (non plaintext) → codice_fiscale_hash
  ✓ Soft delete (deleted_at): diritto cancellazione GDPR art.17
  ✓ pg_audit / log_statement: audit trail completo
  ✓ Row-Level Security: isolare dati tra tenant
```

**Prossimi tutorial:**
- `tutorial_plat12_message_queues_lab.md` — RabbitMQ, Kafka, DLQ
- `tutorial_plat17_storage_distribuito_lab.md` — MinIO S3, Longhorn

```bash
# Pulizia lab
cd ~/db-lab
docker compose -f compose-postgres-single.yaml down -v
rm -rf ~/db-lab

echo "[OK] Lab Database Management completato"
```

---

> **Nota versioni:** Tutorial validato con PostgreSQL 17.x (settembre 2024), PgBouncer 1.23.x,
> Redis 7.4.x, Patroni 4.0.x (Python, solo in cluster reale).
> PostgreSQL 17 novità: COPY FROM RETURN, identity columns improvements, pg_stat_io più dettagliato.
> PgBouncer 1.22+ (2024): supporto SCRAM-SHA-256 nativo (non richiedere pg_md5 password).
> Redis 7.4: Redis Stack integrato (RediSearch, RedisJSON) — senza moduli aggiuntivi.
