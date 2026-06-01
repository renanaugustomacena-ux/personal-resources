# PostgreSQL: Amministrazione su Linux — Guida Approfondita

> **Modulo 29** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **`pg_basebackup` + WAL archive per PITR.**
2. **Streaming replication setup; `synchronous_commit=on` per consistency.**
3. **VACUUM + autovacuum tuning.**
4. **`pg_stat_statements` per slow query analysis.**
5. **pgBackRest / Barman per backup enterprise.**
6. **Partitioning + Extensions per scalare.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Interna](#architettura-interna)
- [Installazione e Setup Iniziale](#installazione-e-setup-iniziale)
- [Configurazione: pg_hba.conf](#configurazione-pg_hbaconf)
- [Configurazione: postgresql.conf Tuning](#configurazione-postgresqlconf-tuning)
- [SSL/TLS Setup](#ssltls-setup)
- [Gestione Database e Utenti](#gestione-database-e-utenti)
- [VACUUM e ANALYZE](#vacuum-e-analyze)
- [Replicazione](#replicazione)
- [Backup e Recovery](#backup-e-recovery)
- [pgBackRest: Backup Enterprise](#pgbackrest-backup-enterprise)
- [Barman: Backup e Disaster Recovery](#barman-backup-e-disaster-recovery)
- [Monitoring e Performance](#monitoring-e-performance)
- [pgBouncer: Connection Pooling](#pgbouncer-connection-pooling)
- [Pgpool-II: Load Balancing e Connection Pooling](#pgpool-ii-load-balancing-e-connection-pooling)
- [Partitioning](#partitioning)
- [Estensioni](#estensioni)
- [Upgrade Strategies](#upgrade-strategies)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Domande e Risposte (Q&A)](#domande-e-risposte-qa)
- [Esercizi Pratici](#esercizi-pratici)
- [Riferimenti](#riferimenti)

---

## Panoramica

PostgreSQL è il database relazionale open source più avanzato, con oltre 35 anni di sviluppo attivo. È lo standard per applicazioni che richiedono integrità dei dati, conformità ACID, estensibilità e performance su workload complessi. A differenza di MySQL/MariaDB, PostgreSQL implementa lo standard SQL in modo molto più rigoroso e offre funzionalità avanzate come tipi di dato JSON con indici GIN, full-text search integrato, Common Table Expressions (CTE) ricorsive, window functions e un sistema di estensioni che permette di aggiungere tipi di dato, operatori e indici custom.

Per il system administrator Linux, l'amministrazione di PostgreSQL va ben oltre l'installazione: richiede la comprensione del modello di autenticazione (pg_hba.conf), il tuning dei parametri di memoria e I/O (postgresql.conf), la gestione del VACUUM (fondamentale per le performance), la configurazione della replicazione per alta disponibilità, e strategie di backup robuste con point-in-time recovery.

Questo documento si concentra sull'amministrazione di PostgreSQL dalla prospettiva del sistema operativo Linux, non sulla scrittura di query SQL. L'obiettivo è fornire le competenze per installare, configurare, monitorare, replicare e fare backup di un'istanza PostgreSQL in modo production-ready.

---

## Architettura Interna

### Processi PostgreSQL

PostgreSQL segue un modello **multi-processo** (non multi-thread). Ogni connessione client genera un processo backend dedicato tramite `fork()` del processo postmaster.

```
                          ┌─────────────────────────────────────────────────┐
                          │              PostgreSQL Instance                │
                          │                                                 │
   Client ────────────────┤  Postmaster (PID 1 del cluster)                │
   Client ────────────────┤    ├── Backend Process (per client)            │
   Client ────────────────┤    ├── Backend Process (per client)            │
                          │    ├── Backend Process (per client)            │
                          │    │                                            │
                          │    ├── Background Writer (bgwriter)            │
                          │    │    └── Scrive dirty buffers su disco       │
                          │    │        gradualmente (evita burst I/O)      │
                          │    │                                            │
                          │    ├── WAL Writer                               │
                          │    │    └── Scrive WAL buffers su disco         │
                          │    │        periodicamente (ogni wal_writer_    │
                          │    │        delay, default 200ms)               │
                          │    │                                            │
                          │    ├── Checkpointer                            │
                          │    │    └── Esegue checkpoint: forza scrittura  │
                          │    │        di tutti i dirty buffers su disco   │
                          │    │        e crea un punto di recovery         │
                          │    │                                            │
                          │    ├── Autovacuum Launcher                     │
                          │    │    └── Spawna autovacuum workers           │
                          │    │        per pulire dead tuples              │
                          │    │                                            │
                          │    ├── WAL Sender (se replica connessa)        │
                          │    │    └── Invia WAL al replica via streaming  │
                          │    │                                            │
                          │    ├── WAL Receiver (se questo è un replica)   │
                          │    │    └── Riceve WAL dal primary              │
                          │    │                                            │
                          │    ├── Stats Collector                         │
                          │    │    └── Raccoglie statistiche di runtime    │
                          │    │                                            │
                          │    └── Logical Replication Worker              │
                          │         └── Applica cambiamenti logici          │
                          │                                                 │
                          │  ┌───────────── Shared Memory ──────────────┐  │
                          │  │  Shared Buffers    │  WAL Buffers        │  │
                          │  │  Lock Tables       │  Proc Array         │  │
                          │  │  CLOG (pg_xact)    │  Stats (pg_stat)    │  │
                          │  └──────────────────────────────────────────┘  │
                          └─────────────────────────────────────────────────┘
```

### Shared Buffers e Buffer Manager

Lo **Shared Buffer Pool** è la cache dei dati in memoria condivisa tra tutti i processi backend. È la componente più critica per le performance.

```
Flusso di una lettura:
                                                    
  Backend riceve query          Buffer Manager
  "SELECT * FROM users"    ──>  cerca pagina nel buffer pool
         │                            │
         │                     ┌──────┴───────┐
         │                     │  Cache Hit?   │
         │                     └──────┬───────┘
         │                        sì/  \no
         │                       /      \
         │              Ritorna      Legge da disco
         │              pagina       (pread) e la mette
         │              dal buffer   nel buffer pool
         │                  \          /
         │                   \        /
         └──── riceve dati ───────────
```

**Clock Sweep Algorithm**: PostgreSQL usa un algoritmo clock sweep per decidere quale pagina rimuovere dal buffer pool quando serve spazio. Ogni buffer ha un `usage_count` (0-5). Quando un buffer viene acceduto, il contatore sale. L'algoritmo "ruota" cercando buffer con `usage_count=0` da evicere. I buffer acceduti frequentemente (hot data) hanno contatori alti e sopravvivono a più passaggi.

```sql
-- Verifica stato buffer pool
SELECT
    c.relname,
    count(*) AS buffers,
    round(100.0 * count(*) / (SELECT setting::integer
        FROM pg_settings WHERE name = 'shared_buffers'), 1) AS pct_of_shared_buffers
FROM pg_buffercache b
JOIN pg_class c ON b.relfilenode = c.relfilenode
WHERE b.reldatabase = (SELECT oid FROM pg_database WHERE datname = current_database())
GROUP BY c.relname
ORDER BY buffers DESC
LIMIT 20;
-- Richiede l'estensione pg_buffercache
```

### Write-Ahead Log (WAL)

Il WAL è il meccanismo che garantisce la durabilità dei dati (la "D" in ACID). Ogni modifica viene prima scritta nel WAL e solo successivamente nei file dati.

```
Flusso di una scrittura:

  Backend esegue UPDATE     1. Scrive nel WAL buffer (in shared memory)
         │                  2. WAL Writer o fsync scrive WAL su disco
         │                  3. Modifica la pagina nel shared buffer (dirty)
         │                  4. Risponde "commit OK" al client
         │
         │                  ... più tardi ...
         │
         │                  5. Checkpointer/bgwriter scrive dirty buffers
         │                     sul disco (file dati)
```

**Perché funziona**: se il server crasha dopo il commit ma prima che il dirty buffer venga scritto su disco, al restart PostgreSQL rilegge il WAL (redo) e riapplica le modifiche. Il WAL è sequenziale (append-only) quindi estremamente veloce da scrivere.

### MVCC (Multi-Version Concurrency Control)

PostgreSQL non usa lock a livello di riga per le letture. Invece, ogni transazione vede uno **snapshot** del database al momento in cui è iniziata.

```
Tempo ──────────────────────────────────────────────────>

T1 (xid=100): BEGIN → UPDATE users SET name='B' WHERE id=1 → COMMIT
                      (crea nuova versione, vecchia resta visibile a T2)

T2 (xid=101): BEGIN ─────────────────────────────────> SELECT * FROM users
                                                        WHERE id=1
                                                        → vede name='A' (vecchia)
                                                        (perché T1 ha committato dopo
                                                         lo snapshot di T2)

Tuple nel disco per id=1:
┌────────────────────────────────────────────────────┐
│ xmin=95  xmax=100  name='A'  ← dead dopo T1 commit │
│ xmin=100 xmax=0    name='B'  ← live                 │
└────────────────────────────────────────────────────┘
```

Ogni tupla ha:
- **xmin**: ID della transazione che ha creato la versione
- **xmax**: ID della transazione che ha "cancellato" questa versione (0 se live)
- **ctid**: puntatore fisico alla prossima versione della stessa riga

Le tuple morte (con `xmax` committato e non più visibili a nessuna transazione) vengono rimosse da VACUUM.

### Struttura dei File Dati

```bash
# Ogni database ha una sotto-directory in base/
ls /var/lib/postgresql/16/main/base/
# 1/    — template1
# 4/    — template0
# 16384/ — mydb (OID del database)

# Ogni tabella è un file (o multipli file da 1GB ciascuno per tabelle grandi)
ls /var/lib/postgresql/16/main/base/16384/
# 16385      — tabella (primo segmento, max 1GB)
# 16385.1    — secondo segmento
# 16385_fsm  — Free Space Map
# 16385_vm   — Visibility Map

# Mappa OID → nome tabella
sudo -u postgres psql -c "SELECT oid, relname, relfilenode
    FROM pg_class WHERE relname = 'users';"
```

**Free Space Map (FSM)**: traccia lo spazio libero in ogni pagina per INSERT e UPDATE senza full table scan.

**Visibility Map (VM)**: traccia quali pagine contengono solo tuple visibili a tutte le transazioni. VACUUM può saltare queste pagine (index-only scan le usa per evitare di consultare la heap).

---

## Installazione e Setup Iniziale

### Installazione da Repository Ufficiale

```bash
# Debian/Ubuntu — PostgreSQL Global Development Group (PGDG) repository
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

sudo apt install -y postgresql-16 postgresql-client-16

# RHEL/Fedora
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo dnf install -y postgresql16-server postgresql16
sudo /usr/pgsql-16/bin/postgresql-16-setup initdb
sudo systemctl enable --now postgresql-16

# Verifica
pg_lsclusters       # Debian/Ubuntu — lista cluster
systemctl status postgresql
psql --version
```

### Struttura delle Directory

```
/etc/postgresql/16/main/          # Config (Debian/Ubuntu)
├── pg_hba.conf                   # Autenticazione
├── pg_ident.conf                 # User mapping
├── postgresql.conf               # Configurazione principale
└── conf.d/                       # Override personalizzati

/var/lib/postgresql/16/main/      # Data directory (PGDATA)
├── base/                         # Database files
├── global/                       # Cluster-wide tables
├── pg_wal/                       # WAL (Write-Ahead Log)
├── pg_stat_tmp/                  # Statistiche temporanee
├── pg_tblspc/                    # Tablespace symlinks
└── postmaster.pid                # PID del server

/var/log/postgresql/              # Log files

# RHEL/Fedora layout
/var/lib/pgsql/16/data/           # PGDATA
/var/lib/pgsql/16/data/pg_hba.conf
/var/lib/pgsql/16/data/postgresql.conf
```

### Inizializzazione Cluster Manuale

```bash
# Utile quando si vogliono opzioni non-default
sudo -u postgres /usr/lib/postgresql/16/bin/initdb \
    -D /var/lib/postgresql/16/custom \
    --encoding=UTF8 \
    --locale=en_US.UTF-8 \
    --data-checksums \                 # RACCOMANDATO: rileva corruzione dati
    --wal-segsize=64                   # WAL segment da 64MB (default 16MB)

# Verifica checksums abilitati
sudo -u postgres pg_controldata /var/lib/postgresql/16/custom | grep checksum
# Data page checksum version:           1
```

**Data checksums**: rilevano la corruzione silente dei dati (bit rot). Aggiungono un overhead trascurabile (~1-2% CPU) ma permettono di rilevare problemi hardware prima che causino perdita di dati. È praticamente impossibile abilitarli su un cluster esistente senza downtime (serve `pg_checksums --enable` con server fermo).

### Primo Accesso

```bash
# PostgreSQL crea un utente di sistema "postgres"
# Accesso come superuser
sudo -u postgres psql

# Dentro psql:
postgres=# \l              -- lista database
postgres=# \du             -- lista ruoli/utenti
postgres=# \conninfo       -- informazioni connessione
postgres=# SELECT version();
postgres=# \q              -- esci

# Output tipico di \l:
#                                    List of databases
#    Name    |  Owner   | Encoding | Collate       | Ctype         | Access
# -----------+----------+----------+---------------+---------------+--------
#  postgres  | postgres | UTF8     | en_US.UTF-8   | en_US.UTF-8   |
#  template0 | postgres | UTF8     | en_US.UTF-8   | en_US.UTF-8   | =c/postgres
#  template1 | postgres | UTF8     | en_US.UTF-8   | en_US.UTF-8   | =c/postgres

# Crea un utente per l'amministrazione
sudo -u postgres createuser --interactive --pwprompt admin
# Sarà superuser? sì
# poi crea il database:
sudo -u postgres createdb -O admin myapp
```

---

## Configurazione: pg_hba.conf

`pg_hba.conf` (Host-Based Authentication) controlla chi può connettersi e come viene autenticato. È il firewall applicativo di PostgreSQL. Le regole vengono valutate dall'alto verso il basso — la prima che matcha viene applicata.

### Formato delle Righe

```
# TYPE   DATABASE  USER      ADDRESS         METHOD
local    all       postgres                  peer
local    all       all                       peer
host     all       all       127.0.0.1/32    scram-sha-256
host     all       all       ::1/128         scram-sha-256
host     myapp     appuser   10.0.0.0/24     scram-sha-256
host     all       all       0.0.0.0/0       reject
```

### Tipi di Connessione

| Tipo | Descrizione |
|------|-------------|
| `local` | Connessione via Unix socket |
| `host` | Connessione TCP/IP (con o senza SSL) |
| `hostssl` | Solo connessioni SSL |
| `hostnossl` | Solo connessioni non-SSL |
| `hostgssenc` | Solo connessioni GSSAPI encrypted |

### Metodi di Autenticazione

| Metodo | Descrizione | Uso |
|--------|-------------|-----|
| `peer` | Usa l'utente OS come nome utente PG | Connessioni locali |
| `scram-sha-256` | Password con hash sicuro (PBKDF2) | Standard per TCP |
| `md5` | Password con hash MD5 (legacy, debole) | Compatibilità |
| `cert` | Certificato client SSL | Alta sicurezza |
| `gss` | Kerberos/GSSAPI | Active Directory |
| `ldap` | LDAP authentication | Directory services |
| `reject` | Nega sempre | Catch-all |
| `trust` | Accetta senza password | MAI in produzione |

### SCRAM-SHA-256 vs MD5

`scram-sha-256` (RFC 7677) è significativamente più sicuro di `md5`:

- **MD5**: hash = `md5(password + username)`. Se un attaccante ottiene pg_shadow, può eseguire un attacco offline. Inoltre, la password viene inviata come hash, ma il protocollo è vulnerabile a replay attack.
- **SCRAM-SHA-256**: usa PBKDF2 con salt random e iterazioni configurabili. Il server non vede mai la password in chiaro. Protegge da replay attack con nonce.

```sql
-- Migrazione da md5 a scram-sha-256
-- 1. Verifica il metodo di encryption attuale
SHOW password_encryption;

-- 2. Cambia in scram-sha-256
ALTER SYSTEM SET password_encryption = 'scram-sha-256';
SELECT pg_reload_conf();

-- 3. Ri-imposta le password degli utenti (rigenera hash)
ALTER USER appuser PASSWORD 'new_secure_password';

-- 4. Aggiorna pg_hba.conf: sostituisci md5 con scram-sha-256
-- 5. Reload
```

### User Mapping con pg_ident.conf

`pg_ident.conf` permette di mappare utenti OS a utenti PostgreSQL, utile con autenticazione `peer` o `cert`:

```conf
# /etc/postgresql/16/main/pg_ident.conf
# MAPNAME     SYSTEM-USERNAME    PG-USERNAME

# L'utente OS "www-data" può connettersi come "appuser"
mymap         www-data           appuser

# L'utente OS "deploy" può connettersi come "admin"
mymap         deploy             admin

# Regex: qualsiasi utente nel gruppo "dev_" diventa utente PG "developer"
mymap         /^dev_(.*)$        developer
```

```conf
# pg_hba.conf — usa il mapping
local   myapp   all                  peer map=mymap
```

### Configurazione per Produzione

```conf
# /etc/postgresql/16/main/pg_hba.conf

# ── Connessioni locali (Unix socket) ──────────────────
local   all         postgres                peer
local   all         admin                   peer
local   all         all                     scram-sha-256

# ── IPv4 loopback ────────────────────────────────────
host    all         all       127.0.0.1/32  scram-sha-256

# ── IPv6 loopback ────────────────────────────────────
host    all         all       ::1/128       scram-sha-256

# ── Applicazione — solo dal backend (SSL obbligatorio) ──
hostssl myapp       appuser   10.0.1.0/24   scram-sha-256

# ── Replicazione — solo dai replica (SSL obbligatorio) ──
hostssl replication replicator 10.0.2.0/24  scram-sha-256

# ── Monitoring ───────────────────────────────────────
host    all         monitor   10.0.0.0/16   scram-sha-256

# ── Deny tutto il resto ─────────────────────────────
host    all         all       0.0.0.0/0     reject
host    all         all       ::/0          reject
```

```bash
# Dopo aver modificato pg_hba.conf:
sudo systemctl reload postgresql
# oppure
sudo -u postgres psql -c "SELECT pg_reload_conf();"

# Verifica regole caricate
sudo -u postgres psql -c "TABLE pg_hba_file_rules;" 2>/dev/null
# PostgreSQL 15+ mostra le regole parsate con eventuali errori
```

---

## Configurazione: postgresql.conf Tuning

### Parametri di Connessione

```conf
# /etc/postgresql/16/main/conf.d/tuning.conf

# ── Connessioni ──────────────────────────────────────
listen_addresses = '*'           # o '0.0.0.0' per IPv4, o IP specifico
port = 5432
max_connections = 200            # Numero massimo connessioni (con pgBouncer, abbassare)
superuser_reserved_connections = 3
```

### Parametri di Memoria

Il tuning della memoria è l'aspetto più critico. Le impostazioni dipendono dalla RAM disponibile.

```conf
# ── Memoria ──────────────────────────────────────────
# Assumi un server dedicato con 32 GB di RAM

# shared_buffers: cache dati in memoria condivisa
# Regola: 25% della RAM totale (non superare 40% su Linux)
# Motivo: Linux ha la propria page cache che gestisce il resto.
# Se shared_buffers è troppo grande, ruba RAM alla page cache
# e le performance peggiorano (double buffering).
shared_buffers = 8GB

# effective_cache_size: stima della memoria disponibile per la cache
# (shared_buffers + page cache OS)
# Non alloca memoria — è un hint per il query planner
# Valori alti favoriscono index scan, valori bassi favoriscono seq scan
# Regola: 50-75% della RAM totale
effective_cache_size = 24GB

# work_mem: memoria per operazioni di sort/hash PER QUERY PER OPERAZIONE
# ATTENZIONE: se max_connections=200 e una query ha 5 sort → 200*5*work_mem
# Valori troppo alti possono causare OOM
# Regola: RAM / (max_connections * 2-4)
work_mem = 32MB

# hash_mem_multiplier: moltiplicatore per hash-based operations
# Hash aggregation e hash join allocano work_mem * hash_mem_multiplier
hash_mem_multiplier = 2.0       # PostgreSQL 13+ (default 2.0)

# maintenance_work_mem: per VACUUM, CREATE INDEX, ALTER TABLE
# Può essere più alto perché queste operazioni sono rare e sequenziali
maintenance_work_mem = 2GB

# autovacuum_work_mem: memoria dedicata all'autovacuum (separata da maintenance)
# -1 = usa maintenance_work_mem
autovacuum_work_mem = 512MB     # separare evita che autovacuum rubi RAM

# wal_buffers: buffer per WAL in shared memory
# Regola: 1/32 di shared_buffers, cap a 64MB
wal_buffers = 64MB

# temp_buffers: per tabelle temporanee (per-sessione, non condiviso)
temp_buffers = 16MB

# huge_pages: usa hugepages del kernel (raccomandato per shared_buffers grandi)
# "try" tenta hugepages, fallback a pagine normali se non disponibili
# "on" fallisce se hugepages non disponibili — meglio per produzione
huge_pages = try
```

### Configurazione Huge Pages su Linux

```bash
# Calcola quante hugepages servono per shared_buffers = 8GB
# Hugepage size di default su Linux: 2MB
# 8GB / 2MB = 4096 hugepages (più un margine per le altre allocazioni)
echo 4400 | sudo tee /proc/sys/vm/nr_hugepages

# Persistente in /etc/sysctl.conf:
vm.nr_hugepages = 4400

# Verifica
grep -i huge /proc/meminfo
# HugePages_Total:    4400
# HugePages_Free:     4400
# HugePages_Rsvd:        0
# Hugepagesize:       2048 kB

# Permetti a PostgreSQL di usare hugepages
# L'utente postgres deve essere nel gruppo "postgres"
echo "vm.hugetlb_shm_group = $(id -g postgres)" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Poi in postgresql.conf: huge_pages = on
# Restart PostgreSQL (non reload — shared memory viene allocata all'avvio)
sudo systemctl restart postgresql
```

### Parametri WAL e Checkpoint

```conf
# ── WAL (Write-Ahead Log) ───────────────────────────
# Livello WAL: minimal, replica, logical
wal_level = replica              # necessario per replicazione
# "logical" necessario per logical replication (overhead leggermente più alto)

# Checkpoint: quando i dirty buffers vengono scritti su disco
# Un checkpoint crea un punto di recovery: tutti i dirty buffers vengono scritti,
# permettendo il riciclo dei WAL precedenti
checkpoint_timeout = 10min       # ogni 10 minuti (default 5min)
checkpoint_completion_target = 0.9  # spalma I/O sul 90% dell'intervallo
max_wal_size = 4GB               # trigger checkpoint se WAL supera questa dimensione
min_wal_size = 1GB

# Compressione WAL
wal_compression = zstd           # riduce I/O su disco (PostgreSQL 16+)
# Opzioni: off, pglz, lz4, zstd
# zstd offre il miglior rapporto compressione/velocità

# full_page_writes: scrive pagina intera nel WAL dopo ogni checkpoint
# Necessario per proteggersi da partial page write (torn page)
# Non disabilitare a meno che il filesystem garantisca scritture atomiche
full_page_writes = on

# Synchronous commit: controlla quando il commit ritorna al client
# on     — aspetta che WAL sia su disco locale (default, più sicuro)
# off    — ritorna subito, rischio di perdere ultime transazioni su crash
#           (finestra di vulnerabilità: ~3x wal_writer_delay ≈ 600ms)
# remote_apply — aspetta che il replica abbia applicato i cambiamenti
synchronous_commit = on
```

### Comprensione dei Checkpoint

```
Tempo ─────────────────────────────────────────────────────────>

Checkpoint 1              Checkpoint 2              Checkpoint 3
    │                         │                         │
    │←── checkpoint_timeout ─→│←── checkpoint_timeout ─→│
    │                         │                         │
    │  WAL accumulati:        │  WAL accumulati:        │
    │  [wal1][wal2][wal3]     │  [wal4][wal5]           │
    │                         │                         │
    ▼                         ▼                         ▼
  Scrivi tutti              Scrivi tutti              Scrivi tutti
  dirty buffers             dirty buffers             dirty buffers
  su disco                  su disco                  su disco
    │                         │                         │
    │  WAL prima di qui      │  WAL prima di qui      │
    │  possono essere        │  possono essere        │
    │  riciclati             │  riciclati             │
    └─────────────────────────┘                         │

checkpoint_completion_target = 0.9
→ spalma le scritture sul 90% dell'intervallo per evitare burst I/O
```

### Parametri di Query e Performance

```conf
# ── Query Planner ────────────────────────────────────
# Costo relativo di una lettura random (accesso a indice)
random_page_cost = 1.1           # 1.1 per SSD (default 4.0 per HDD)
seq_page_cost = 1.0
# Il rapporto random/seq influenza la scelta tra index scan e seq scan
# Su SSD, random e sequential hanno costi simili

effective_io_concurrency = 200   # per SSD/NVMe (default 1 per HDD)
# Quante operazioni I/O concorrenti il disco può gestire
# NVMe: 200+, SSD SATA: 100-200, HDD: 2-4

maintenance_io_concurrency = 10  # per VACUUM e operazioni di manutenzione

default_statistics_target = 200  # più statistiche = piani migliori
# Default 100. Per tabelle con distribuzione non uniforme, aumentare.
# Costo: più tempo per ANALYZE, più memoria per il planner

# JIT compilation (PostgreSQL 11+)
jit = on
jit_above_cost = 100000          # abilita JIT per query con costo > 100000
jit_inline_above_cost = 500000
jit_optimize_above_cost = 500000

# ── Parallel Queries ─────────────────────────────────
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_maintenance_workers = 4
max_parallel_workers = 8
min_parallel_table_scan_size = 8MB
min_parallel_index_scan_size = 512kB

# ── Logging ──────────────────────────────────────────
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000  # logga query più lente di 1 secondo
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0               # logga uso di file temporanei (sort on disk)
log_autovacuum_min_duration = 0  # logga tutte le operazioni autovacuum
log_line_prefix = '%m [%p] %q%u@%d '  # timestamp, pid, user@database

# ── Autovacuum ───────────────────────────────────────
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 30s         # quanto spesso controllare se serve vacuum
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.1   # vacuum quando 10% delle tuple sono dead
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.05 # analyze quando 5% delle tuple cambiano
autovacuum_vacuum_cost_delay = 2ms     # riduci impatto I/O
autovacuum_vacuum_cost_limit = 1000
```

### Autovacuum per Tabelle Grandi

Per tabelle con molte righe, il `scale_factor` globale può non funzionare bene. Con 100M di righe e `scale_factor=0.1`, autovacuum parte solo dopo 10M dead tuples — troppo tardi.

```sql
-- Override per-tabella dell'autovacuum
ALTER TABLE orders SET (
    autovacuum_vacuum_scale_factor = 0.01,    -- 1% invece di 10%
    autovacuum_vacuum_threshold = 1000,
    autovacuum_analyze_scale_factor = 0.005,  -- 0.5% invece di 5%
    autovacuum_vacuum_cost_delay = 0          -- nessun throttle per questa tabella
);

-- Verifica impostazioni per-tabella
SELECT relname, reloptions
FROM pg_class
WHERE relname = 'orders';
```

### Tabella Riassuntiva per Dimensione Server

| Parametro | 4GB RAM | 16GB RAM | 64GB RAM | 256GB RAM |
|-----------|---------|----------|----------|-----------|
| shared_buffers | 1GB | 4GB | 16GB | 64GB |
| effective_cache_size | 3GB | 12GB | 48GB | 192GB |
| work_mem | 8MB | 32MB | 128MB | 256MB |
| maintenance_work_mem | 512MB | 1GB | 4GB | 8GB |
| max_connections | 100 | 200 | 300 | 500 |
| wal_buffers | 32MB | 64MB | 64MB | 64MB |
| effective_io_concurrency | 200 | 200 | 200 | 200 |
| max_worker_processes | 4 | 8 | 16 | 32 |
| max_parallel_workers | 4 | 8 | 16 | 32 |

### Applicare Modifiche

```bash
# Parametri che richiedono RELOAD (nessun downtime):
# - work_mem, maintenance_work_mem, autovacuum_*, log_*, effective_cache_size
# - checkpoint_timeout, checkpoint_completion_target, random_page_cost
sudo systemctl reload postgresql

# Parametri che richiedono RESTART:
# - shared_buffers, wal_buffers, max_connections, wal_level
# - max_worker_processes, huge_pages, shared_preload_libraries
sudo systemctl restart postgresql

# Verifica se un parametro richiede restart
SELECT name, setting, context
FROM pg_settings
WHERE name IN ('shared_buffers', 'work_mem', 'max_connections');
-- context = 'postmaster' → richiede restart
-- context = 'sighup'     → reload sufficiente
-- context = 'user'       → cambiabile per sessione con SET
-- context = 'superuser'  → cambiabile con SET da superuser

# Verifica parametri pending restart
SELECT name, setting, pending_restart
FROM pg_settings
WHERE pending_restart = true;
```

---

## SSL/TLS Setup

### Generazione Certificati

```bash
# ── Creare una CA auto-firmata ────────────────────────
mkdir -p /etc/postgresql/16/ssl
cd /etc/postgresql/16/ssl

# Genera chiave privata CA
openssl genrsa -out ca.key 4096
chmod 600 ca.key

# Genera certificato CA (validità 10 anni)
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
    -subj "/CN=PostgreSQL-Internal-CA/O=MyOrg"

# ── Certificato server ───────────────────────────────
# Genera chiave privata server
openssl genrsa -out server.key 2048
chmod 600 server.key
chown postgres:postgres server.key

# Genera CSR (Certificate Signing Request)
openssl req -new -key server.key -out server.csr \
    -subj "/CN=db-primary.internal/O=MyOrg"

# Crea file estensioni (SAN — Subject Alternative Names)
cat > server_ext.cnf <<EOF
subjectAltName = DNS:db-primary.internal,DNS:localhost,IP:10.0.1.1,IP:127.0.0.1
EOF

# Firma il CSR con la CA
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out server.crt -days 365 \
    -extfile server_ext.cnf

# ── Certificato client (opzionale, per autenticazione cert) ──
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr \
    -subj "/CN=appuser"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out client.crt -days 365

# Imposta permessi
chown postgres:postgres server.key server.crt ca.crt
chmod 600 server.key
chmod 644 server.crt ca.crt
```

### Configurazione Server SSL

```conf
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/postgresql/16/ssl/server.crt'
ssl_key_file = '/etc/postgresql/16/ssl/server.key'
ssl_ca_file = '/etc/postgresql/16/ssl/ca.crt'      # per validare client cert

# Cipher suites — solo cipher forti
ssl_min_protocol_version = 'TLSv1.2'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
# Per TLS 1.3 specifico:
# ssl_min_protocol_version = 'TLSv1.3'

# OCSP stapling (se disponibile)
# ssl_crl_file = '/etc/postgresql/16/ssl/root.crl'
```

```conf
# pg_hba.conf — forza SSL per connessioni remote
hostssl   all         all       10.0.0.0/8    scram-sha-256
hostssl   all         all       0.0.0.0/0     reject

# Autenticazione via certificato client
hostssl   myapp       appuser   10.0.1.0/24   cert clientcert=verify-full
```

### Connessione Client con SSL

```bash
# Connessione con verifica completa
PGSSLMODE=verify-full \
PGSSLROOTCERT=/path/to/ca.crt \
psql -h db-primary.internal -U appuser -d myapp

# Con certificato client
PGSSLMODE=verify-full \
PGSSLROOTCERT=/path/to/ca.crt \
PGSSLCERT=/path/to/client.crt \
PGSSLKEY=/path/to/client.key \
psql -h db-primary.internal -U appuser -d myapp

# Verifica stato SSL della connessione
psql -c "SELECT ssl, version, cipher, bits FROM pg_stat_ssl
         JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid
         WHERE usename = current_user;"
```

### Modalità sslmode

| Modalità | Descrizione | Sicurezza |
|----------|-------------|-----------|
| `disable` | Nessun SSL | Nessuna |
| `allow` | Prova senza SSL, poi con SSL | Minima |
| `prefer` | Prova con SSL, fallback senza (DEFAULT) | Bassa |
| `require` | SSL obbligatorio, nessuna verifica certificato | Media |
| `verify-ca` | SSL + verifica che il cert sia firmato da CA fidata | Alta |
| `verify-full` | SSL + verifica CA + verifica hostname | Massima |

**Produzione**: usare sempre `verify-full`. La modalità `require` senza verifica del certificato è vulnerabile a MITM.

---

## Gestione Database e Utenti

### Sistema dei Ruoli

PostgreSQL non ha "utenti" e "gruppi" separati — tutto è un **ruolo**. Un ruolo con `LOGIN` è un utente; un ruolo senza `LOGIN` è un gruppo.

```sql
-- ── Creare ruoli ────────────────────────────────────
-- Ruolo applicativo (nessun superuser)
CREATE ROLE appuser WITH LOGIN PASSWORD 'secure_password_here'
    NOSUPERUSER NOCREATEDB NOCREATEROLE
    CONNECTION LIMIT 50           -- limite connessioni per questo ruolo
    VALID UNTIL '2027-01-01';     -- scadenza password

-- Ruolo read-only per monitoring
CREATE ROLE monitor WITH LOGIN PASSWORD 'monitor_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE;

-- Ruolo per replicazione
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'repl_password';

-- Ruolo gruppo (nessun LOGIN)
CREATE ROLE readonly NOLOGIN;
CREATE ROLE readwrite NOLOGIN;

-- Eredità: assegna ruolo gruppo a un utente
GRANT readonly TO monitor;
GRANT readwrite TO appuser;
```

### Schema dei Permessi

```sql
-- ── Permessi granulari ──────────────────────────────

-- Crea database
CREATE DATABASE myapp OWNER appuser
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.UTF-8'
    LC_CTYPE 'en_US.UTF-8'
    TEMPLATE template0;

-- Connettiti al database
\c myapp

-- Crea schema dedicato per l'applicazione
CREATE SCHEMA app AUTHORIZATION appuser;

-- Revoca i permessi di default sullo schema public
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE myapp FROM PUBLIC;

-- Permessi per il ruolo readonly
GRANT CONNECT ON DATABASE myapp TO readonly;
GRANT USAGE ON SCHEMA app TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA app
    GRANT SELECT ON TABLES TO readonly;

-- Permessi per il ruolo readwrite
GRANT CONNECT ON DATABASE myapp TO readwrite;
GRANT USAGE, CREATE ON SCHEMA app TO readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO readwrite;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA app
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA app
    GRANT USAGE, SELECT ON SEQUENCES TO readwrite;

-- Verifica permessi
\dp app.*                      -- mostra ACL per oggetti nello schema app
SELECT * FROM information_schema.role_table_grants
WHERE grantee = 'readonly';
```

### Row-Level Security (RLS)

```sql
-- Abilita RLS sulla tabella
ALTER TABLE app.documents ENABLE ROW LEVEL SECURITY;

-- Policy: ogni utente vede solo i propri documenti
CREATE POLICY user_documents ON app.documents
    USING (owner = current_user);

-- Policy: inserimento solo con owner = current_user
CREATE POLICY user_insert_docs ON app.documents
    FOR INSERT
    WITH CHECK (owner = current_user);

-- Admin bypassa RLS
ALTER TABLE app.documents FORCE ROW LEVEL SECURITY;
-- (FORCE applica RLS anche al table owner; senza FORCE, il owner bypassa)
```

### Gestione Tablespace

```sql
-- Crea tablespace su storage veloce
CREATE TABLESPACE fast_storage LOCATION '/mnt/nvme/pg_data';

-- Sposta tabella su tablespace
ALTER TABLE large_table SET TABLESPACE fast_storage;

-- Crea database su tablespace specifico
CREATE DATABASE analytics TABLESPACE fast_storage;

-- Sposta indici su storage veloce
ALTER INDEX idx_orders_date SET TABLESPACE fast_storage;

-- Verifica usage tablespace
SELECT spcname, pg_size_pretty(pg_tablespace_size(oid)) AS size
FROM pg_tablespace;
```

---

## VACUUM e ANALYZE

### Perché VACUUM è Necessario

PostgreSQL usa MVCC (Multi-Version Concurrency Control): quando una riga viene aggiornata, la vecchia versione non viene sovrascritta ma marcata come "dead". VACUUM rimuove queste tuple morte e rende lo spazio riutilizzabile.

```
Prima del VACUUM:                  Dopo il VACUUM:
┌────────┬─────────┐              ┌────────┬─────────┐
│ Live   │ Data A  │              │ Live   │ Data A  │
├────────┼─────────┤              ├────────┼─────────┤
│ Dead   │ (old A) │              │ Free   │         │ ← riutilizzabile
├────────┼─────────┤              ├────────┼─────────┤
│ Live   │ Data B  │              │ Live   │ Data B  │
├────────┼─────────┤              ├────────┼─────────┤
│ Dead   │ (old B) │              │ Free   │         │ ← riutilizzabile
└────────┴─────────┘              └────────┴─────────┘
```

**VACUUM vs VACUUM FULL**: VACUUM standard marca lo spazio come riutilizzabile all'interno del file, ma non restituisce spazio all'OS (il file non si riduce). VACUUM FULL riscrive l'intera tabella in un nuovo file compatto, ma richiede un `ACCESS EXCLUSIVE` lock — la tabella è inaccessibile durante l'operazione.

### Tipi di VACUUM

```sql
-- VACUUM standard: marca spazio come riutilizzabile (non restituisce all'OS)
VACUUM my_table;

-- VACUUM VERBOSE: con output dettagliato
VACUUM VERBOSE my_table;
-- Output tipico:
-- INFO: vacuuming "public.my_table"
-- INFO: table "my_table": found 15023 removable, 89234 nonremovable row versions
-- in 1234 pages
-- DETAIL: 0 dead row versions cannot be removed yet, oldest xmin: 12345678
--   15023 dead row version removed from 456 pages
--   CPU: user: 0.12 s, system: 0.03 s, elapsed: 0.28 s

-- VACUUM FULL: riscrive l'intera tabella, restituisce spazio all'OS
-- ATTENZIONE: blocca la tabella con ACCESS EXCLUSIVE lock!
VACUUM FULL my_table;

-- VACUUM con ANALYZE (aggiorna anche le statistiche del planner)
VACUUM ANALYZE my_table;

-- ANALYZE da solo (solo statistiche, nessuna pulizia)
ANALYZE my_table;

-- ANALYZE su colonne specifiche (utile per colonne con distribuzione anomala)
ANALYZE my_table (status, created_at, category);
```

### Freeze: Prevenire il Transaction ID Wraparound

```sql
-- PostgreSQL usa XID a 32-bit (circa 4 miliardi di transazioni)
-- Dopo 2 miliardi di transazioni senza freeze, le tuple "vecchie"
-- diventerebbero invisibili (in futuro dal punto di vista MVCC)

-- VACUUM FREEZE marca le tuple come "frozen" (visibili a tutte le transazioni)
VACUUM FREEZE my_table;

-- Parametri correlati:
-- vacuum_freeze_min_age = 50000000     — età minima prima del freeze
-- vacuum_freeze_table_age = 150000000  — forza full-table vacuum per freeze
-- autovacuum_freeze_max_age = 200000000 — forza vacuum se non fatto entro qui

-- Transaction ID wraparound — la metrica più critica
-- Se age(datfrozenxid) si avvicina a 2 miliardi, PostgreSQL FORZERÀ un vacuum
-- anti-wraparound che è single-threaded e NON throttled — impatto pesante
SELECT datname,
       age(datfrozenxid) AS xid_age,
       round(age(datfrozenxid)::numeric / 2000000000 * 100, 2) AS pct_towards_wraparound
FROM pg_database
ORDER BY age(datfrozenxid) DESC;

-- Per-tabella: quali tabelle sono più vicine al wraparound?
SELECT schemaname || '.' || relname AS table_name,
       age(relfrozenxid) AS xid_age,
       pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_stat_user_tables
ORDER BY age(relfrozenxid) DESC
LIMIT 20;
```

### Monitoraggio Autovacuum

```sql
-- Autovacuum attualmente in esecuzione
SELECT pid, datname, relid::regclass, phase,
       heap_blks_total, heap_blks_scanned, heap_blks_vacuumed,
       index_vacuum_count, max_dead_tuples
FROM pg_stat_progress_vacuum;

-- Tabelle che necessitano VACUUM urgente
SELECT
    schemaname || '.' || relname AS table_name,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;

-- Tabelle dove autovacuum NON sta funzionando (dead_pct alto ma nessun vacuum recente)
SELECT
    schemaname || '.' || relname AS table_name,
    n_dead_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
    last_autovacuum,
    age(now(), last_autovacuum) AS time_since_vacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 50000
  AND (last_autovacuum IS NULL OR last_autovacuum < now() - interval '1 day')
ORDER BY n_dead_tup DESC;
```

### Alternativa a VACUUM FULL: pg_repack

`pg_repack` ripacked una tabella senza `ACCESS EXCLUSIVE` lock (usa un approccio basato su trigger):

```bash
# Installazione
sudo apt install postgresql-16-repack

# Repack una tabella (online, nessun lock esclusivo)
pg_repack -d myapp -t orders --no-superuser-check

# Repack tutte le tabelle bloated
pg_repack -d myapp --table-only --no-order

# Con monitoring del progresso
pg_repack -d myapp -t orders --echo
```

---

## Replicazione

### Streaming Replication (Fisico)

La streaming replication replica l'intero cluster a livello binario (WAL streaming). Il replica è una copia esatta bit-per-bit del primary.

```
                    WAL Stream
  ┌──────────┐  ──────────────>  ┌──────────┐
  │ Primary  │                   │ Replica  │
  │          │  wal_sender ────> │          │
  │          │         wal_receiver          │
  │          │                   │          │
  │  R/W     │                   │  R/O     │
  │          │                   │  (hot    │
  │          │                   │  standby)│
  └──────────┘                   └──────────┘
     10.0.1.1                      10.0.2.10
```

**Sul primary:**

```conf
# postgresql.conf
wal_level = replica
max_wal_senders = 5
wal_keep_size = 1GB      # o usa replication slots (raccomandato)
max_replication_slots = 5
hot_standby = on

# Synchronous replication (opzionale — attenzione alla latenza)
# synchronous_standby_names = 'replica1'
# synchronous_commit = on
```

```conf
# pg_hba.conf
hostssl replication    replicator    10.0.2.10/32    scram-sha-256
```

```sql
-- Crea ruolo replicazione
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'secure_repl_pass';

-- Crea replication slot (previene rimozione WAL necessari al replica)
SELECT pg_create_physical_replication_slot('replica1');

-- Verifica slots
SELECT slot_name, slot_type, active, restart_lsn
FROM pg_replication_slots;
```

**Sul replica:**

```bash
# Ferma PostgreSQL sul replica
sudo systemctl stop postgresql

# Pulisci data directory del replica
sudo -u postgres rm -rf /var/lib/postgresql/16/main/*

# Base backup dal primary
sudo -u postgres pg_basebackup \
    -h 10.0.1.1 \
    -D /var/lib/postgresql/16/main \
    -U replicator \
    -S replica1 \           # usa il replication slot
    -X stream \             # includi WAL via streaming
    -C \                    # crea lo slot se non esiste
    -P \                    # mostra progresso
    -R                      # crea standby.signal e configura recovery

# -R crea automaticamente:
# /var/lib/postgresql/16/main/standby.signal
# e aggiunge a postgresql.auto.conf:
# primary_conninfo = 'user=replicator host=10.0.1.1 port=5432 sslmode=prefer'
# primary_slot_name = 'replica1'

# Avvia il replica
sudo systemctl start postgresql
```

**Verifica:**

```sql
-- Sul primary: verifica repliche connesse
SELECT
    client_addr,
    state,
    sync_state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replication_lag_bytes,
    pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) AS send_lag_bytes
FROM pg_stat_replication;

-- Output tipico:
--  client_addr | state     | sync_state | sent_lsn    | replay_lsn  | replication_lag_bytes
-- -------------+-----------+------------+-------------+-------------+----------------------
--  10.0.2.10   | streaming | async      | 0/3000A28   | 0/3000A28   |                    0

-- Sul replica: verifica stato recovery
SELECT
    pg_is_in_recovery() AS is_replica,
    pg_last_wal_receive_lsn() AS last_received,
    pg_last_wal_replay_lsn() AS last_replayed,
    pg_last_xact_replay_timestamp() AS last_replay_time,
    now() - pg_last_xact_replay_timestamp() AS replay_lag;
```

### Synchronous Replication

```conf
# postgresql.conf sul primary

# Definisci quali repliche sono sincrone
# FIRST 1: almeno 1 replica conferma prima di commit
synchronous_standby_names = 'FIRST 1 (replica1, replica2)'

# synchronous_commit controlla il livello di garanzia:
# on             — aspetta WAL su disco del primary (default)
# remote_write   — aspetta che il replica abbia scritto in OS cache
# remote_flush   — aspetta che il replica abbia scritto su disco
# remote_apply   — aspetta che il replica abbia applicato i cambiamenti
#                  (query sul replica vedono subito i dati committati)
synchronous_commit = remote_apply
```

```sql
-- Verifica sync_state
SELECT application_name, sync_state, sync_priority
FROM pg_stat_replication;
-- sync_state: async, potential, sync, quorum
```

**Trade-off**: la replicazione sincrona garantisce zero data loss ma introduce latenza su ogni COMMIT (round-trip al replica). Usare solo quando la perdita di dati è inaccettabile.

### Failover e Promozione

```bash
# ── Failover manuale ────────────────────────────────
# Sul replica, promuovilo a primary:
sudo -u postgres pg_ctl promote -D /var/lib/postgresql/16/main

# Oppure via SQL (PostgreSQL 12+):
sudo -u postgres psql -c "SELECT pg_promote();"

# Verifica che non sia più in recovery
sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
# Deve restituire: false

# ── Patroni per failover automatico ─────────────────
# Patroni + etcd/Consul/ZooKeeper gestisce:
# - Monitoraggio health del primary
# - Failover automatico
# - Switchover pianificato
# - Fencing (impedisce split-brain)
```

### Logical Replication

La logical replication replica dati a livello di tabella, permettendo replicazione selettiva, tra versioni diverse, e verso database eterogenei:

```sql
-- ── Sul primary (publisher) ─────────────────────────

-- Prerequisito: wal_level = logical nel postgresql.conf
-- (richiede restart)

-- Crea pubblicazione per tabelle specifiche
CREATE PUBLICATION my_pub FOR TABLE users, orders;

-- Pubblicazione per tutte le tabelle
CREATE PUBLICATION full_pub FOR ALL TABLES;

-- Pubblicazione solo per INSERT (no UPDATE/DELETE)
CREATE PUBLICATION insert_only_pub FOR TABLE events
    WITH (publish = 'insert');

-- Pubblicazione con filtro (PostgreSQL 15+)
CREATE PUBLICATION regional_pub FOR TABLE orders
    WHERE (region = 'EU');

-- ── Sul subscriber ──────────────────────────────────

-- Le tabelle devono ESISTERE con schema compatibile
CREATE SUBSCRIPTION my_sub
    CONNECTION 'host=10.0.1.1 port=5432 dbname=myapp user=replicator password=pass sslmode=verify-full'
    PUBLICATION my_pub
    WITH (
        copy_data = true,            -- copia dati iniziali (default true)
        create_slot = true,          -- crea replication slot sul publisher
        enabled = true,
        synchronous_commit = 'off'   -- non aspettare sync commit locale
    );

-- Verifica stato
SELECT * FROM pg_stat_subscription;          -- sul subscriber
SELECT * FROM pg_replication_slots;          -- sul publisher

-- Aggiungi tabella alla pubblicazione
ALTER PUBLICATION my_pub ADD TABLE new_table;
-- Sul subscriber, refresh:
ALTER SUBSCRIPTION my_sub REFRESH PUBLICATION;

-- Disabilita temporaneamente la subscription
ALTER SUBSCRIPTION my_sub DISABLE;
ALTER SUBSCRIPTION my_sub ENABLE;

-- Rimuovi subscription
DROP SUBSCRIPTION my_sub;  -- rimuove anche il replication slot sul publisher
```

### Logical vs Streaming Replication

| Caratteristica | Streaming (Fisico) | Logical |
|---|---|---|
| Granularità | Intero cluster | Per-tabella |
| Versioni diverse | No (stessa major) | Sì |
| Direzione | Unidirezionale | Multi-direzionale (con pg 16+) |
| DDL replicato | Sì (automatico) | No (manuale) |
| Replica scrivibile | No (read-only) | Sì (per tabelle non replicate) |
| Overhead | Basso | Medio (decodifica WAL) |
| Uso tipico | HA, read scaling | Migration, ETL, partial replication |

---

## Backup e Recovery

### Strategia di Backup: Tre Livelli

```
Livello 1: pg_dump (Logical)
├── Pro: portabile, cross-version, selettivo
├── Contro: lento per DB grandi, no PITR
└── Uso: backup periodico, migration, test

Livello 2: pg_basebackup + WAL archiving (Physical)
├── Pro: veloce, PITR, backup incrementale con WAL
├── Contro: same version, intero cluster
└── Uso: PITR, seeding repliche

Livello 3: pgBackRest / Barman (Enterprise)
├── Pro: incrementale, parallelo, compresso, verifica, retention
├── Contro: infrastruttura aggiuntiva
└── Uso: produzione enterprise
```

### pg_dump (Logical Backup)

```bash
# ── Formati di pg_dump ───────────────────────────────

# Plain SQL (testo)
sudo -u postgres pg_dump myapp > /backup/myapp_$(date +%Y%m%d).sql
# Pro: leggibile, editabile
# Contro: nessun restore parallelo, nessuna compressione nativa

# Custom format (-Fc) — RACCOMANDATO per singolo database
sudo -u postgres pg_dump -Fc myapp > /backup/myapp_$(date +%Y%m%d).dump
# Pro: compresso, restore parallelo, restore selettivo
# Contro: non leggibile direttamente

# Directory format (-Fd) — per database grandi
sudo -u postgres pg_dump -Fd -j 4 myapp -f /backup/myapp_$(date +%Y%m%d)/
# Pro: dump parallelo (-j), un file per tabella
# Contro: molti file, directory

# Tar format (-Ft)
sudo -u postgres pg_dump -Ft myapp > /backup/myapp_$(date +%Y%m%d).tar

# ── Opzioni comuni ───────────────────────────────────

# Backup solo schema (niente dati)
sudo -u postgres pg_dump -s myapp > /backup/myapp_schema.sql

# Backup tabella specifica
sudo -u postgres pg_dump -t users -t orders myapp > /backup/tables.dump

# Backup escludendo tabelle grandi (es. tabelle di log)
sudo -u postgres pg_dump --exclude-table='audit_*' myapp -Fc > /backup/myapp_no_audit.dump

# Backup solo dati (niente schema)
sudo -u postgres pg_dump -a myapp > /backup/myapp_data.sql

# Backup con compressione specifica (PG 16+)
sudo -u postgres pg_dump --compress=zstd:3 -Fc myapp > /backup/myapp.dump.zst

# Backup di tutti i database (include ruoli e tablespace)
sudo -u postgres pg_dumpall > /backup/all_databases_$(date +%Y%m%d).sql

# Backup solo global objects (ruoli, tablespace)
sudo -u postgres pg_dumpall --globals-only > /backup/globals.sql
```

### Restore

```bash
# ── Restore da formati diversi ───────────────────────

# Restore da SQL plain
sudo -u postgres psql myapp < /backup/myapp_20240401.sql

# Restore da formato custom
sudo -u postgres pg_restore -d myapp /backup/myapp_20240401.dump

# Restore parallelo (molto più veloce)
sudo -u postgres pg_restore -d myapp -j 4 /backup/myapp_20240401.dump

# Restore in un database nuovo
sudo -u postgres createdb myapp_restored
sudo -u postgres pg_restore -d myapp_restored /backup/myapp_20240401.dump

# Restore selettivo: solo una tabella
sudo -u postgres pg_restore -d myapp -t users /backup/myapp_20240401.dump

# Restore solo schema
sudo -u postgres pg_restore -d myapp -s /backup/myapp_20240401.dump

# Restore con --clean: droppa e ricrea gli oggetti
sudo -u postgres pg_restore -d myapp --clean --if-exists /backup/myapp_20240401.dump

# Lista contenuto di un backup custom
sudo -u postgres pg_restore -l /backup/myapp_20240401.dump
```

### pg_basebackup (Physical Backup)

```bash
# Backup fisico completo (per PITR o seeding replica)
sudo -u postgres pg_basebackup \
    -D /backup/base_$(date +%Y%m%d) \
    -Ft \           # formato tar
    -z \            # compressione gzip
    -X stream \     # includi WAL via streaming
    -P \            # mostra progresso
    -v              # verbose

# Con compressione specifica (PG 15+)
sudo -u postgres pg_basebackup \
    -D /backup/base_$(date +%Y%m%d) \
    -Ft \
    --compress=server-zstd:3 \   # comprime lato server con zstd
    -X stream \
    -P

# Il risultato contiene:
# base.tar.gz — tutti i file del data directory
# pg_wal.tar.gz — WAL necessari per la consistenza

# Verifica integrità (PG 13+)
pg_verifybackup /backup/base_20240401/
```

### WAL Archiving e Point-in-Time Recovery (PITR)

```conf
# postgresql.conf — abilita archiving

archive_mode = on
archive_command = 'test ! -f /backup/wal_archive/%f && cp %p /backup/wal_archive/%f'
# Il 'test ! -f' previene sovrascrittura accidentale

# Con compressione:
# archive_command = 'gzip < %p > /backup/wal_archive/%f.gz'

# archive_timeout: forza archiviazione WAL anche se non pieno
# Utile per limitare la finestra di perdita dati su DB con poco traffico
archive_timeout = 300    # 5 minuti — al massimo 5 min di dati persi

# Alternativa: pg_receivewal (processo separato che riceve WAL in tempo reale)
# Più affidabile di archive_command per ambienti critici
```

```bash
# pg_receivewal: daemon separato per archiviare WAL in tempo reale
pg_receivewal -h 10.0.1.1 -U replicator \
    -D /backup/wal_archive \
    -S wal_archiver_slot \
    --compress=zstd:3

# Questo approccio è più affidabile di archive_command perché:
# 1. Non dipende dal server PostgreSQL per l'esecuzione del comando
# 2. Usa streaming replication (meno latenza)
# 3. Può essere monitorato indipendentemente
```

### Point-in-Time Recovery (PITR) — Procedura Dettagliata

```bash
# Scenario: alle 15:30 un DELETE errato ha cancellato dati critici.
# Abbiamo un base backup delle 02:00 e WAL archiviati.

# 1. Ferma PostgreSQL
sudo systemctl stop postgresql

# 2. Salva il data directory corrente (safety)
sudo -u postgres mv /var/lib/postgresql/16/main /var/lib/postgresql/16/main.bak

# 3. Crea directory vuota con permessi corretti
sudo -u postgres mkdir /var/lib/postgresql/16/main
sudo chmod 700 /var/lib/postgresql/16/main

# 4. Ripristina il base backup
sudo -u postgres tar xzf /backup/base_20240401_0200/base.tar.gz \
    -C /var/lib/postgresql/16/main/

# 5. Se hai tar separato per pg_wal:
sudo -u postgres tar xzf /backup/base_20240401_0200/pg_wal.tar.gz \
    -C /var/lib/postgresql/16/main/pg_wal/

# 6. Configura il recovery
cat > /var/lib/postgresql/16/main/postgresql.auto.conf <<EOF
restore_command = 'cp /backup/wal_archive/%f %p'
recovery_target_time = '2024-04-01 15:29:00+02'
recovery_target_action = 'pause'
EOF
# recovery_target_action:
#   pause   — pausa e permette di verificare prima di promuovere
#   promote — promuove automaticamente a primary
#   shutdown — si ferma dopo il recovery

# 7. Crea il file signal
sudo -u postgres touch /var/lib/postgresql/16/main/recovery.signal

# 8. Avvia e attendi il recovery
sudo systemctl start postgresql
# PostgreSQL applicherà i WAL fino al target_time specificato

# 9. Verifica i dati
sudo -u postgres psql -c "SELECT count(*) FROM important_table;"

# 10. Se i dati sono OK, promuovi:
sudo -u postgres psql -c "SELECT pg_wal_replay_resume();"
# oppure
sudo -u postgres pg_ctl promote -D /var/lib/postgresql/16/main

# 11. Il file recovery.signal viene rimosso automaticamente dopo la promozione
```

### Recovery Target Alternativi

```conf
# Ripristino a una transazione specifica
recovery_target_xid = '12345678'

# Ripristino a un named restore point
# (creato con: SELECT pg_create_restore_point('before_migration');)
recovery_target_name = 'before_migration'

# Ripristino a una posizione LSN specifica
recovery_target_lsn = '0/3000A28'

# Ripristino "inclusivo" vs "esclusivo"
recovery_target_inclusive = false   # ferma PRIMA della transazione target
```

---

## pgBackRest: Backup Enterprise

pgBackRest è lo strumento di backup enterprise più utilizzato per PostgreSQL. Supporta backup incrementale, differenziale, parallelo, compresso, e verificabile.

### Installazione e Configurazione

```bash
# Installazione
sudo apt install pgbackrest          # Debian/Ubuntu
sudo dnf install pgbackrest          # RHEL/Fedora

# Configurazione
sudo mkdir -p /etc/pgbackrest /var/lib/pgbackrest /var/log/pgbackrest
sudo chown postgres:postgres /var/lib/pgbackrest /var/log/pgbackrest
```

```ini
# /etc/pgbackrest/pgbackrest.conf

[global]
# Repository di backup (locale)
repo1-path=/var/lib/pgbackrest
repo1-retention-full=2               # mantieni 2 backup full
repo1-retention-diff=7               # mantieni 7 differenziali
repo1-cipher-type=aes-256-cbc        # crittografia backup
repo1-cipher-pass=CHANGE_THIS_ENCRYPTION_KEY

# Compressione
compress-type=zst
compress-level=3

# Parallelismo
process-max=4

# Logging
log-level-console=info
log-level-file=detail

# Repository S3 (alternativa a locale)
# repo2-type=s3
# repo2-path=/pgbackrest
# repo2-s3-bucket=my-pg-backup-bucket
# repo2-s3-endpoint=s3.eu-central-1.amazonaws.com
# repo2-s3-region=eu-central-1
# repo2-s3-key=ACCESS_KEY
# repo2-s3-key-secret=SECRET_KEY
# repo2-retention-full=4

[mydb]
pg1-path=/var/lib/postgresql/16/main
pg1-port=5432
pg1-user=postgres
```

```conf
# postgresql.conf — configurazione per pgBackRest
archive_mode = on
archive_command = 'pgbackrest --stanza=mydb archive-push %p'
```

### Operazioni pgBackRest

```bash
# ── Inizializzazione ─────────────────────────────────
# Crea lo stanza (validazione configurazione)
sudo -u postgres pgbackrest --stanza=mydb stanza-create

# Verifica la configurazione
sudo -u postgres pgbackrest --stanza=mydb check

# ── Backup ───────────────────────────────────────────
# Backup completo (full)
sudo -u postgres pgbackrest --stanza=mydb --type=full backup

# Backup differenziale (solo blocchi cambiati dall'ultimo full)
sudo -u postgres pgbackrest --stanza=mydb --type=diff backup

# Backup incrementale (solo blocchi cambiati dall'ultimo backup qualsiasi)
sudo -u postgres pgbackrest --stanza=mydb --type=incr backup

# Backup con annotazione
sudo -u postgres pgbackrest --stanza=mydb --type=full \
    --annotation="pre-migration-v2.0" backup

# ── Informazioni backup ─────────────────────────────
sudo -u postgres pgbackrest --stanza=mydb info
# Output tipico:
# stanza: mydb
#     status: ok
#     cipher: aes-256-cbc
#
#     db (current)
#         wal archive min/max (16): 000000010000000000000001/000000010000000000000005
#
#         full backup: 20240401-020000F
#             timestamp start/stop: 2024-04-01 02:00:00+02 / 2024-04-01 02:15:32+02
#             wal start/stop: 000000010000000000000003 / 000000010000000000000003
#             database size: 15.2GB, database backup size: 15.2GB
#             repo1: backup set size: 3.8GB, backup size: 3.8GB (compression ratio 4:1)
#
#         diff backup: 20240401-120000F_20240402-020000D
#             ...
#             repo1: backup set size: 3.8GB, backup size: 245MB

# ── Restore ──────────────────────────────────────────
# Ferma PostgreSQL prima del restore
sudo systemctl stop postgresql

# Restore l'ultimo backup
sudo -u postgres pgbackrest --stanza=mydb restore

# Restore con PITR
sudo -u postgres pgbackrest --stanza=mydb \
    --type=time "--target=2024-04-01 15:29:00+02" \
    --target-action=promote \
    restore

# Restore di un backup specifico
sudo -u postgres pgbackrest --stanza=mydb \
    --set=20240401-020000F \
    restore

# Restore selettivo (solo un database)
sudo -u postgres pgbackrest --stanza=mydb \
    --db-include=myapp \
    restore

# Avvia dopo il restore
sudo systemctl start postgresql

# ── Verifica backup ──────────────────────────────────
# Verifica integrità del backup (ripristina in temp e controlla)
sudo -u postgres pgbackrest --stanza=mydb verify

# ── Scheduling con cron ──────────────────────────────
# /etc/cron.d/pgbackrest
# Full backup ogni domenica alle 2:00
0 2 * * 0   postgres   pgbackrest --stanza=mydb --type=full backup
# Diff backup ogni giorno alle 2:00 (tranne domenica)
0 2 * * 1-6 postgres   pgbackrest --stanza=mydb --type=diff backup
```

---

## Barman: Backup e Disaster Recovery

Barman (Backup and Recovery Manager) è un'alternativa a pgBackRest sviluppata da EDB (EnterpriseDB). È particolarmente forte nel disaster recovery con gestione centralizzata di più server PostgreSQL.

### Architettura Barman

```
  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
  │ PG Server 1 │    │ PG Server 2 │    │ PG Server 3 │
  │  (primary)  │    │  (primary)  │    │  (primary)  │
  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
         │                   │                   │
         │ WAL streaming     │ WAL streaming     │ rsync/SSH
         │ + pg_basebackup   │ + pg_basebackup   │
         │                   │                   │
         └───────────┬───────┴───────────────────┘
                     │
              ┌──────▼──────┐
              │ Barman      │
              │ Server      │
              │             │
              │ Backup repo │
              │ WAL archive │
              └─────────────┘
```

### Installazione e Setup

```bash
# Sul server Barman (server di backup centralizzato)
sudo apt install barman barman-cli           # Debian/Ubuntu
sudo dnf install barman barman-cli           # RHEL

# Sui server PostgreSQL
sudo apt install barman-cli
```

```ini
# /etc/barman.conf — configurazione globale

[barman]
barman_user = barman
configuration_files_directory = /etc/barman.d
barman_home = /var/lib/barman
log_file = /var/log/barman/barman.log
compression = gzip
retention_policy = RECOVERY WINDOW OF 7 DAYS
minimum_redundancy = 1
```

```ini
# /etc/barman.d/pg-primary.conf — configurazione per singolo server

[pg-primary]
description = "Primary PostgreSQL Server"
ssh_command = ssh postgres@10.0.1.1
conninfo = host=10.0.1.1 user=barman dbname=postgres
streaming_conninfo = host=10.0.1.1 user=streaming_barman dbname=postgres
backup_method = postgres               # pg_basebackup
streaming_archiver = on
slot_name = barman
create_slot = auto

retention_policy = RECOVERY WINDOW OF 14 DAYS
```

### Operazioni Barman

```bash
# ── Setup iniziale ───────────────────────────────────
# Verifica configurazione
barman check pg-primary

# Ricevi WAL dal server
barman receive-wal pg-primary
# (in genere lanciato come servizio/cron)

# ── Backup ───────────────────────────────────────────
barman backup pg-primary

# Lista backup disponibili
barman list-backup pg-primary

# Info dettagliata su un backup
barman show-backup pg-primary latest

# ── Restore ──────────────────────────────────────────
# Restore l'ultimo backup su un server target
barman recover pg-primary latest /var/lib/postgresql/16/main \
    --remote-ssh-command="ssh postgres@10.0.2.10" \
    --target-time="2024-04-01 15:29:00+02"

# ── Verifica ─────────────────────────────────────────
barman check pg-primary
# Output:
# Server pg-primary:
#         PostgreSQL: OK
#         superuser or standard user with backup privileges: OK
#         wal_level: OK
#         directories: OK
#         retention policy settings: OK
#         backup maximum age: OK (1d 2h)
#         compression settings: OK
#         WAL archive: OK
#         ...

# ── Scheduling ───────────────────────────────────────
# /etc/cron.d/barman
# Backup giornaliero alle 3:00
0 3 * * * barman   barman backup pg-primary
# Manutenzione giornaliera (cleanup, WAL)
30 3 * * * barman  barman cron
```

### pgBackRest vs Barman

| Caratteristica | pgBackRest | Barman |
|---|---|---|
| Backup incrementale (block-level) | Sì (nativo) | Sì (con rsync) |
| Compressione parallela | Sì | Limitata |
| S3/Azure/GCS | Sì (nativo) | Plugin |
| Multi-repository | Sì (fino a 4) | Sì |
| Verifica backup | Sì (verify) | Sì (check) |
| Gestione centralizzata multi-server | Limitata | Sì (design nativo) |
| Performance restore | Molto veloce (parallelo) | Buono |
| Maturità community | Molto alta | Alta |

---

## Monitoring e Performance

### Viste di Sistema Essenziali

```sql
-- ── pg_stat_activity: connessioni attive ────────────
-- Connessioni per stato
SELECT state, count(*)
FROM pg_stat_activity
WHERE backend_type = 'client backend'
GROUP BY state
ORDER BY count DESC;

-- Output tipico:
--    state    | count
-- ------------+-------
--  idle       |    45
--  active     |    12
--  idle in transaction |  3
--  idle in transaction (aborted) | 1

-- Query lente in esecuzione
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    usename,
    datname,
    state,
    wait_event_type,
    wait_event,
    left(query, 100) AS query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC
LIMIT 10;

-- Sessioni idle in transaction (pericolose: tengono lock e bloccano vacuum)
SELECT
    pid,
    usename,
    now() - xact_start AS transaction_duration,
    now() - state_change AS idle_in_txn_duration,
    left(query, 80) AS last_query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '5 minutes';

-- Termina una query/sessione problematica
SELECT pg_cancel_backend(12345);     -- cancella la query (SIGINT)
SELECT pg_terminate_backend(12345);  -- termina la sessione (SIGTERM)
```

### Lock Monitoring

```sql
-- Lock in attesa
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    left(blocked_activity.query, 60) AS blocked_statement,
    left(blocking_activity.query, 60) AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity
    ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
   AND blocking_locks.relation = blocked_locks.relation
   AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity
    ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Deadlock detection (PostgreSQL rileva automaticamente i deadlock
-- e abortisce una delle transazioni coinvolte — controllare i log)
-- log_lock_waits = on mostra i lock che durano più di deadlock_timeout

-- Advisory locks (application-level)
SELECT * FROM pg_locks WHERE locktype = 'advisory';
```

### Cache e I/O Performance

```sql
-- Cache hit ratio (deve essere > 99% per workload OLTP)
SELECT
    sum(heap_blks_read) AS heap_read,
    sum(heap_blks_hit) AS heap_hit,
    round(sum(heap_blks_hit) * 100.0 /
        NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) AS cache_hit_ratio
FROM pg_statio_user_tables;

-- Cache hit ratio per indice
SELECT
    indexrelname,
    idx_blks_read,
    idx_blks_hit,
    round(idx_blks_hit * 100.0 /
        NULLIF(idx_blks_hit + idx_blks_read, 0), 2) AS idx_hit_ratio
FROM pg_statio_user_indexes
WHERE idx_blks_read + idx_blks_hit > 100
ORDER BY idx_hit_ratio ASC
LIMIT 20;

-- Dimensioni database e tabelle
SELECT pg_database.datname,
       pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;

-- Top tabelle per dimensione
SELECT
    schemaname || '.' || relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- Tabelle con bloat stimato
SELECT
    schemaname || '.' || relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    n_live_tup,
    n_dead_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC
LIMIT 20;
```

### Index Usage Analysis

```sql
-- Indici mai usati (candidati alla rimozione)
SELECT
    schemaname || '.' || relname AS table_name,
    indexrelname AS index_name,
    idx_scan AS times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelid NOT IN (
      SELECT conindid FROM pg_constraint
      WHERE contype IN ('p', 'u')    -- escludi primary key e unique constraints
  )
ORDER BY pg_relation_size(indexrelid) DESC;

-- Tabelle con sequential scan dominante (possibile indice mancante)
SELECT
    schemaname || '.' || relname AS table_name,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_stat_user_tables
WHERE seq_scan > 0
  AND pg_total_relation_size(relid) > 10 * 1024 * 1024  -- > 10MB
ORDER BY seq_tup_read DESC
LIMIT 20;

-- Indici duplicati
SELECT
    a.indrelid::regclass AS table_name,
    a.indexrelid::regclass AS index_1,
    b.indexrelid::regclass AS index_2,
    pg_size_pretty(pg_relation_size(a.indexrelid)) AS index_1_size,
    pg_size_pretty(pg_relation_size(b.indexrelid)) AS index_2_size
FROM pg_index a
JOIN pg_index b ON a.indrelid = b.indrelid
    AND a.indexrelid != b.indexrelid
    AND a.indkey::text = b.indkey::text
WHERE a.indexrelid > b.indexrelid;
```

### pg_stat_statements

```sql
-- Abilita l'estensione (richiede shared_preload_libraries e restart)
-- In postgresql.conf: shared_preload_libraries = 'pg_stat_statements'
-- pg_stat_statements.max = 10000
-- pg_stat_statements.track = all        -- track anche nested queries
-- pg_stat_statements.track_utility = on -- track anche DDL/utility

CREATE EXTENSION pg_stat_statements;

-- Top query per tempo totale
SELECT
    calls,
    round(total_exec_time::numeric, 2) AS total_time_ms,
    round(mean_exec_time::numeric, 2) AS mean_time_ms,
    round(stddev_exec_time::numeric, 2) AS stddev_ms,
    rows,
    round((100.0 * total_exec_time / sum(total_exec_time) OVER ()), 2) AS pct_of_total,
    left(query, 100) AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Query con maggior variabilità (spikes imprevedibili)
SELECT
    calls,
    round(mean_exec_time::numeric, 2) AS mean_ms,
    round(min_exec_time::numeric, 2) AS min_ms,
    round(max_exec_time::numeric, 2) AS max_ms,
    round(stddev_exec_time::numeric, 2) AS stddev_ms,
    left(query, 100) AS query
FROM pg_stat_statements
WHERE calls > 100
ORDER BY stddev_exec_time DESC
LIMIT 20;

-- Query che leggono più dati (I/O bound)
SELECT
    calls,
    shared_blks_read + shared_blks_hit AS total_blks,
    round(shared_blks_hit * 100.0 /
        NULLIF(shared_blks_read + shared_blks_hit, 0), 2) AS hit_ratio,
    rows,
    left(query, 100) AS query
FROM pg_stat_statements
WHERE calls > 10
ORDER BY (shared_blks_read + shared_blks_hit) DESC
LIMIT 20;

-- Query con maggior utilizzo di file temporanei (sort/hash su disco)
SELECT
    calls,
    round(mean_exec_time::numeric, 2) AS mean_ms,
    temp_blks_read + temp_blks_written AS temp_blks,
    left(query, 100) AS query
FROM pg_stat_statements
WHERE temp_blks_read + temp_blks_written > 0
ORDER BY (temp_blks_read + temp_blks_written) DESC
LIMIT 20;

-- Reset statistiche
SELECT pg_stat_statements_reset();
```

### Wait Events Analysis

```sql
-- Wait events: cosa stanno aspettando i processi?
SELECT
    wait_event_type,
    wait_event,
    count(*) AS cnt
FROM pg_stat_activity
WHERE state = 'active'
  AND wait_event IS NOT NULL
GROUP BY wait_event_type, wait_event
ORDER BY cnt DESC;

-- Tipi di wait events:
-- LWLock      — lightweight lock interni (es. buffer_content, wal_insert)
-- Lock        — lock tradizionali SQL (row lock, table lock)
-- BufferPin   — attesa per pin su buffer
-- Activity    — processi di background in attesa di lavoro
-- Client      — attesa input dal client
-- IPC         — inter-process communication
-- IO          — attesa I/O su disco (DataFileRead, WALWrite, etc.)
```

---

## pgBouncer: Connection Pooling

pgBouncer è un connection pooler leggero che riduce l'overhead di connessione a PostgreSQL. Ogni connessione PostgreSQL consuma circa 5-10 MB di RAM (a causa del processo fork), quindi con molte connessioni il risparmio è significativo.

### Perché serve il Connection Pooling

```
Senza pooling (1000 connessioni app):
App → [1000 connessioni TCP] → PostgreSQL (1000 processi backend)
                                 = ~5-10GB RAM solo per le connessioni

Con pgBouncer (1000 connessioni app, 50 pool):
App → [1000 connessioni TCP] → pgBouncer → [50 connessioni] → PostgreSQL
                                                                = ~250-500MB
```

### Installazione e Configurazione

```bash
sudo apt install pgbouncer
```

```ini
# /etc/pgbouncer/pgbouncer.ini

[databases]
myapp = host=127.0.0.1 port=5432 dbname=myapp
# Pool per replica read-only
myapp_ro = host=10.0.2.10 port=5432 dbname=myapp

# Database wildcard (tutti i database con pool di default)
# * = host=127.0.0.1 port=5432

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# ── Modalità di pooling ──────────────────────────────
# session      — una connessione PG per sessione client (default)
#                meno efficiente ma compatibile con tutto
# transaction  — una connessione PG per transazione (RACCOMANDATO)
#                la connessione torna al pool dopo COMMIT
# statement    — una connessione PG per statement (molto aggressivo)
#                incompatibile con transazioni multi-statement
pool_mode = transaction

# ── Pool sizing ──────────────────────────────────────
default_pool_size = 25       # connessioni per utente/database pair
max_client_conn = 1000       # max client connessi a pgbouncer
min_pool_size = 5            # connessioni pre-create
reserve_pool_size = 5        # connessioni extra per picchi
reserve_pool_timeout = 3     # secondi prima di usare reserve pool

max_db_connections = 50      # max connessioni PER DATABASE a PostgreSQL
max_user_connections = 0     # 0 = nessun limite per utente

# ── Timeout ──────────────────────────────────────────
server_connect_timeout = 15
server_idle_timeout = 600    # chiudi connessione inutilizzata dopo 10 min
server_lifetime = 3600       # ricicla connessione dopo 1 ora
client_idle_timeout = 0      # 0 = nessun timeout client idle
client_login_timeout = 60
query_timeout = 0            # 0 = nessun timeout query
query_wait_timeout = 120     # max attesa in coda per una connessione

# ── Cleanup ──────────────────────────────────────────
# In transaction mode, queste query vengono eseguite
# quando la connessione torna al pool
server_reset_query = DISCARD ALL
# Alternativa più leggera:
# server_reset_query = RESET ALL; SET SESSION AUTHORIZATION DEFAULT;

# ── TLS ──────────────────────────────────────────────
# Client → pgBouncer
client_tls_sslmode = require
client_tls_cert_file = /etc/pgbouncer/server.crt
client_tls_key_file = /etc/pgbouncer/server.key

# pgBouncer → PostgreSQL
server_tls_sslmode = verify-full
server_tls_ca_file = /etc/pgbouncer/ca.crt

# ── Logging ──────────────────────────────────────────
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60

# ── Admin ────────────────────────────────────────────
admin_users = admin
stats_users = monitor
```

```bash
# File delle password
# Genera automaticamente da PostgreSQL
sudo -u postgres psql -Atq -c \
    "SELECT '\"' || usename || '\" \"' || passwd || '\"' FROM pg_shadow" \
    > /etc/pgbouncer/userlist.txt

sudo chown pgbouncer:pgbouncer /etc/pgbouncer/userlist.txt
sudo chmod 600 /etc/pgbouncer/userlist.txt

# Oppure con auth_query (niente file password, query a PostgreSQL):
# auth_type = scram-sha-256
# auth_query = SELECT usename, passwd FROM pg_shadow WHERE usename=$1

# Avvia pgBouncer
sudo systemctl enable --now pgbouncer

# L'applicazione si connette a pgBouncer sulla porta 6432
psql -h 127.0.0.1 -p 6432 -U appuser myapp
```

### Monitoring pgBouncer

```bash
# Connetti alla console admin
psql -h 127.0.0.1 -p 6432 -U admin pgbouncer

# Comandi utili:
SHOW POOLS;
# Output:
# database | user    | cl_active | cl_waiting | sv_active | sv_idle | pool_mode
# ---------+---------+-----------+------------+-----------+---------+----------
# myapp    | appuser | 45        | 0          | 12        | 13      | transaction

SHOW STATS;
# Statistiche per database: total_xact_count, total_query_count, avg_xact_time, ...

SHOW CLIENTS;
SHOW SERVERS;
SHOW CONFIG;

# Comandi admin
RELOAD;            -- ricarica configurazione
PAUSE myapp;       -- pausa il pool (drain delle connessioni)
RESUME myapp;      -- riprendi dopo la pausa
KILL myapp;        -- termina tutte le connessioni del database
```

### Limitazioni in Transaction Mode

In `pool_mode = transaction`, le seguenti funzionalità NON funzionano perché la connessione PostgreSQL cambia tra una transazione e l'altra:

- `LISTEN`/`NOTIFY`
- Prepared statements con nome (`PREPARE`/`EXECUTE`)
- Variabili di sessione (`SET`)
- Cursori con nome (`DECLARE`/`FETCH`)
- Advisory locks a livello sessione
- Temporary tables (fuori dalla transazione)

**Soluzione**: usare prepared statements con protocollo esteso (supportato dalla maggior parte dei driver), oppure passare a `pool_mode = session` per le connessioni che necessitano di queste funzionalità.

---

## Pgpool-II: Load Balancing e Connection Pooling

Pgpool-II è un middleware più complesso di pgBouncer che offre connection pooling, load balancing, replication management e query caching.

### Architettura

```
                        ┌────────────────────┐
  App ──────────────>   │  Pgpool-II         │
  App ──────────────>   │                    │
  App ──────────────>   │  Pool Manager      │
                        │  Load Balancer     │
                        │  Query Cache       │
                        │  Health Check      │
                        │  Watchdog (HA)     │
                        └──────┬─────┬───────┘
                               │     │
                    Write ─────┘     └───── Read
                               │             │
                        ┌──────▼──────┐ ┌────▼────────┐
                        │  Primary    │ │  Replica 1   │
                        │  (R/W)      │ │  (R/O)       │
                        └─────────────┘ └──────────────┘
```

### Configurazione

```conf
# /etc/pgpool2/pgpool.conf

# Backend servers
backend_hostname0 = '10.0.1.1'
backend_port0 = 5432
backend_weight0 = 1          # peso per load balancing
backend_flag0 = 'ALLOW_TO_FAILOVER'

backend_hostname1 = '10.0.2.10'
backend_port1 = 5432
backend_weight1 = 2          # doppio peso = doppio traffico read
backend_flag1 = 'ALLOW_TO_FAILOVER'

# Connection pooling
num_init_children = 32       # processi worker
max_pool = 4                 # connessioni cache per worker
connection_cache = on

# Load balancing
load_balance_mode = on
# Le query in transazione R/W vanno al primary
# Le SELECT fuori transazione vengono bilanciate
statement_level_load_balance_mode = off

# Health check
health_check_period = 10
health_check_timeout = 20
health_check_user = 'monitor'
health_check_database = 'postgres'
health_check_max_retries = 3

# Failover
failover_on_backend_error = on
failover_command = '/etc/pgpool2/failover.sh %d %h %p %D %m %H %M %P %r %R %N %S'
# Lo script deve promuovere il replica a primary

# Query cache (in-memory, opzionale)
memory_cache_enabled = off
# Abilitare solo per workload con query identiche e ripetitive

# Watchdog (HA per Pgpool-II stesso — evita SPOF)
use_watchdog = on
wd_hostname = 'pgpool1'
wd_port = 9000
```

### pgBouncer vs Pgpool-II

| Caratteristica | pgBouncer | Pgpool-II |
|---|---|---|
| Connection pooling | Eccellente (leggero) | Buono |
| Load balancing read | No (serve HAProxy) | Sì (nativo) |
| Failover automatico | No | Sì |
| Query cache | No | Sì |
| Overhead risorse | Minimo (~2MB RAM) | Moderato |
| Complessità config | Bassa | Alta |
| Uso raccomandato | Pooling + HAProxy per LB | All-in-one (pool+LB+failover) |

---

## Partitioning

Il partitioning divide tabelle grandi in pezzi più piccoli (partizioni) per migliorare performance delle query, semplificare la manutenzione, e velocizzare operazioni come VACUUM e backup.

### Tipi di Partitioning

```sql
-- ═══════════════════════════════════════════════════
-- RANGE PARTITIONING
-- Uso: dati temporali (log, ordini, metriche)
-- ═══════════════════════════════════════════════════

CREATE TABLE orders (
    id          BIGSERIAL,
    customer_id INTEGER NOT NULL,
    order_date  TIMESTAMPTZ NOT NULL,
    total       NUMERIC(10,2),
    status      TEXT,
    PRIMARY KEY (id, order_date)    -- partition key DEVE essere nella PK
) PARTITION BY RANGE (order_date);

-- Partizioni mensili
CREATE TABLE orders_2024_01 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE orders_2024_02 PARTITION OF orders
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE orders_2024_03 PARTITION OF orders
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
-- ...

-- Partizione default (cattura righe senza match)
CREATE TABLE orders_default PARTITION OF orders DEFAULT;

-- ═══════════════════════════════════════════════════
-- LIST PARTITIONING
-- Uso: dati categorici (regione, tipo, stato)
-- ═══════════════════════════════════════════════════

CREATE TABLE customers (
    id          BIGSERIAL,
    name        TEXT NOT NULL,
    region      TEXT NOT NULL,
    email       TEXT,
    PRIMARY KEY (id, region)
) PARTITION BY LIST (region);

CREATE TABLE customers_eu PARTITION OF customers
    FOR VALUES IN ('IT', 'DE', 'FR', 'ES', 'NL');
CREATE TABLE customers_us PARTITION OF customers
    FOR VALUES IN ('US', 'CA');
CREATE TABLE customers_apac PARTITION OF customers
    FOR VALUES IN ('JP', 'KR', 'AU', 'SG');
CREATE TABLE customers_other PARTITION OF customers DEFAULT;

-- ═══════════════════════════════════════════════════
-- HASH PARTITIONING
-- Uso: distribuzione uniforme quando non c'è un criterio naturale
-- ═══════════════════════════════════════════════════

CREATE TABLE sessions (
    id          UUID PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    data        JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
) PARTITION BY HASH (id);

CREATE TABLE sessions_p0 PARTITION OF sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE sessions_p1 PARTITION OF sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE sessions_p2 PARTITION OF sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE sessions_p3 PARTITION OF sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

### Sub-Partitioning

```sql
-- Multi-level: prima per regione, poi per data
CREATE TABLE events (
    id          BIGSERIAL,
    region      TEXT NOT NULL,
    event_date  DATE NOT NULL,
    data        JSONB,
    PRIMARY KEY (id, region, event_date)
) PARTITION BY LIST (region);

CREATE TABLE events_eu PARTITION OF events
    FOR VALUES IN ('EU')
    PARTITION BY RANGE (event_date);

CREATE TABLE events_eu_2024_q1 PARTITION OF events_eu
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
CREATE TABLE events_eu_2024_q2 PARTITION OF events_eu
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
```

### Automazione Creazione Partizioni

```sql
-- Funzione per creare partizioni mensili automaticamente
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Crea partizioni per i prossimi 3 mesi
    FOR i IN 0..2 LOOP
        partition_date := date_trunc('month', now() + (i || ' months')::interval);
        start_date := partition_date;
        end_date := partition_date + interval '1 month';
        partition_name := 'orders_' || to_char(partition_date, 'YYYY_MM');

        -- Controlla se la partizione esiste già
        IF NOT EXISTS (
            SELECT 1 FROM pg_class WHERE relname = partition_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE %I PARTITION OF orders FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date
            );
            RAISE NOTICE 'Created partition: %', partition_name;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Scheduling con pg_cron (estensione)
-- CREATE EXTENSION pg_cron;
-- SELECT cron.schedule('create_partitions', '0 0 25 * *',
--     'SELECT create_monthly_partition()');
```

### Manutenzione Partizioni

```sql
-- Detach una partizione vecchia (senza DROP, mantiene i dati)
ALTER TABLE orders DETACH PARTITION orders_2023_01;
-- La tabella orders_2023_01 esiste ancora come tabella standalone
-- Puoi fare pg_dump, spostare su cold storage, etc.

-- Detach CONCURRENTLY (PostgreSQL 14+, senza lock esclusivo)
ALTER TABLE orders DETACH PARTITION orders_2023_01 CONCURRENTLY;

-- Drop una partizione (elimina i dati — IRREVERSIBILE)
DROP TABLE orders_2023_01;

-- VACUUM è più veloce con partitioning: opera su partizioni piccole
VACUUM ANALYZE orders_2024_03;   -- solo la partizione di marzo

-- Partition pruning: il planner esclude automaticamente partizioni irrilevanti
EXPLAIN ANALYZE SELECT * FROM orders WHERE order_date = '2024-03-15';
-- Output mostra: Append → Seq Scan on orders_2024_03
-- Le altre partizioni non vengono toccate
```

### Verifica Partition Pruning

```sql
-- Abilita (default on)
SET enable_partition_pruning = on;

-- Verifica con EXPLAIN
EXPLAIN (COSTS OFF)
SELECT * FROM orders WHERE order_date BETWEEN '2024-03-01' AND '2024-03-31';
-- Append
--   ->  Seq Scan on orders_2024_03
--         Filter: (order_date >= '2024-03-01' AND order_date <= '2024-03-31')

-- Senza pruning (scansiona TUTTE le partizioni):
SET enable_partition_pruning = off;
EXPLAIN (COSTS OFF)
SELECT * FROM orders WHERE order_date BETWEEN '2024-03-01' AND '2024-03-31';
-- Append
--   ->  Seq Scan on orders_2024_01
--   ->  Seq Scan on orders_2024_02
--   ->  Seq Scan on orders_2024_03  ← unica con risultati
--   ->  Seq Scan on orders_2024_04
--   ...
```

---

## Estensioni

Le estensioni sono una delle funzionalità più potenti di PostgreSQL. Permettono di aggiungere tipi di dato, funzioni, indici e interi motori di ricerca.

### Estensioni Essenziali

```sql
-- ── pg_stat_statements (già trattato) ───────────────
-- shared_preload_libraries = 'pg_stat_statements'
CREATE EXTENSION pg_stat_statements;

-- ── pg_trgm: ricerca fuzzy e similarità ─────────────
CREATE EXTENSION pg_trgm;

-- Indice GIN per ricerca LIKE/ILIKE veloce
CREATE INDEX idx_users_name_trgm ON users USING gin (name gin_trgm_ops);

-- Ora ILIKE usa l'indice!
SELECT * FROM users WHERE name ILIKE '%smith%';

-- Similarità
SELECT name, similarity(name, 'Jhon') AS sim
FROM users
WHERE name % 'Jhon'     -- usa indice GIN
ORDER BY sim DESC
LIMIT 10;

-- ── btree_gist: indici GiST per tipi scalari ───────
CREATE EXTENSION btree_gist;

-- Utile per exclusion constraints (es. prenotazioni senza overlap)
CREATE TABLE bookings (
    room_id INTEGER NOT NULL,
    during TSTZRANGE NOT NULL,
    EXCLUDE USING GIST (room_id WITH =, during WITH &&)
);
-- Impedisce overlap di prenotazioni per la stessa stanza

-- ── uuid-ossp / gen_random_uuid ─────────────────────
-- PostgreSQL 13+: gen_random_uuid() è built-in, nessuna estensione necessaria
SELECT gen_random_uuid();

-- Per UUIDv7 (time-sortable, PG 17+):
-- CREATE EXTENSION pg_uuidv7;

-- ── pgcrypto: funzioni crittografiche ───────────────
CREATE EXTENSION pgcrypto;

-- Hash password con bcrypt
SELECT crypt('my_password', gen_salt('bf', 12));

-- Verifica password
SELECT (crypt('user_input', stored_hash) = stored_hash) AS password_match;

-- ── hstore: key-value pairs in una colonna ──────────
CREATE EXTENSION hstore;

CREATE TABLE product_attributes (
    product_id INTEGER,
    attrs hstore
);
INSERT INTO product_attributes VALUES (1, 'color => red, size => XL');
SELECT attrs -> 'color' FROM product_attributes;

-- ── PostGIS: dati geospaziali ───────────────────────
CREATE EXTENSION postgis;

-- Trova punti entro un raggio
SELECT name, ST_Distance(
    location::geography,
    ST_SetSRID(ST_MakePoint(12.4964, 41.9028), 4326)::geography
) AS distance_meters
FROM restaurants
WHERE ST_DWithin(
    location::geography,
    ST_SetSRID(ST_MakePoint(12.4964, 41.9028), 4326)::geography,
    5000    -- 5km
)
ORDER BY distance_meters;

-- ── pg_cron: job scheduling nel database ────────────
-- shared_preload_libraries = 'pg_cron'
CREATE EXTENSION pg_cron;

-- Scheduled VACUUM ogni notte alle 3:00
SELECT cron.schedule('nightly_vacuum', '0 3 * * *',
    'VACUUM ANALYZE orders');

-- Pulizia partizioni vecchie ogni mese
SELECT cron.schedule('cleanup_old_partitions', '0 4 1 * *',
    'SELECT create_monthly_partition()');

-- Lista job schedulati
SELECT * FROM cron.job;

-- ── pg_buffercache: ispeziona il buffer pool ────────
CREATE EXTENSION pg_buffercache;

-- Già mostrato nella sezione architettura

-- ── auto_explain: logga piani di esecuzione automaticamente ──
-- shared_preload_libraries = 'auto_explain'
-- auto_explain.log_min_duration = 1000    -- query > 1s
-- auto_explain.log_analyze = on
-- auto_explain.log_buffers = on
-- auto_explain.log_timing = on
-- auto_explain.log_nested_statements = on
```

### Installazione Estensioni di Terze Parti

```bash
# Su Debian/Ubuntu, molte estensioni sono pacchettizzate:
sudo apt install postgresql-16-postgis-3     # PostGIS
sudo apt install postgresql-16-pgvector      # pgvector (AI/ML)
sudo apt install postgresql-16-repack        # pg_repack
sudo apt install postgresql-16-cron          # pg_cron
sudo apt install postgresql-16-partman       # pg_partman (partition management)

# PGXN (PostgreSQL Extension Network) — per estensioni non pacchettizzate
sudo apt install pgxnclient
pgxn install temporal_tables

# Lista estensioni disponibili
sudo -u postgres psql -c "SELECT name, default_version, comment
    FROM pg_available_extensions
    ORDER BY name;"

# Lista estensioni installate
sudo -u postgres psql -c "SELECT extname, extversion FROM pg_extension;"
```

---

## Upgrade Strategies

### pg_upgrade (In-Place, Major Version)

`pg_upgrade` è il metodo più veloce per upgrade major version. Supporta due modalità: `--copy` (copia i file dati) e `--link` (hard link, quasi istantaneo).

```bash
# ── Preparazione ─────────────────────────────────────

# 1. Installa la nuova versione SENZA rimuovere la vecchia
sudo apt install postgresql-17

# 2. Ferma entrambi i cluster
sudo systemctl stop postgresql

# 3. Verifica compatibilità
sudo -u postgres /usr/lib/postgresql/17/bin/pg_upgrade \
    --old-datadir /var/lib/postgresql/16/main \
    --new-datadir /var/lib/postgresql/17/main \
    --old-bindir /usr/lib/postgresql/16/bin \
    --new-bindir /usr/lib/postgresql/17/bin \
    --check

# ── Upgrade con --link (quasi istantaneo) ────────────
# ATTENZIONE: --link modifica il vecchio cluster in modo irreversibile.
# NON è possibile tornare indietro dopo aver avviato il nuovo cluster.
# FARE BACKUP PRIMA.

sudo -u postgres /usr/lib/postgresql/17/bin/pg_upgrade \
    --old-datadir /var/lib/postgresql/16/main \
    --new-datadir /var/lib/postgresql/17/main \
    --old-bindir /usr/lib/postgresql/16/bin \
    --new-bindir /usr/lib/postgresql/17/bin \
    --link \
    --jobs 4          # parallelismo

# ── Post-upgrade ─────────────────────────────────────

# 4. Avvia il nuovo cluster
sudo systemctl start postgresql@17-main

# 5. Aggiorna le estensioni
sudo -u postgres psql -c "ALTER EXTENSION pg_stat_statements UPDATE;"

# 6. Rigenera le statistiche (IMPORTANTE)
# pg_upgrade genera uno script per questo:
sudo -u postgres /usr/lib/postgresql/17/bin/vacuumdb \
    --all --analyze-in-stages --jobs 4

# 7. Rimuovi il vecchio cluster quando tutto funziona
sudo -u postgres /usr/lib/postgresql/17/bin/pg_upgrade \
    --old-datadir /var/lib/postgresql/16/main \
    --new-datadir /var/lib/postgresql/17/main \
    --old-bindir /usr/lib/postgresql/16/bin \
    --new-bindir /usr/lib/postgresql/17/bin \
    --delete-old-cluster
```

### Upgrade via Logical Replication (Zero-Downtime)

Per ambienti che non possono permettersi downtime:

```
Flusso:
1. Installa nuova versione su server separato
2. Setup logical replication: vecchio → nuovo
3. Aspetta che il nuovo sia in sync
4. Switch traffico al nuovo server
5. Decomissiona il vecchio

Vecchio (PG 16)                     Nuovo (PG 17)
┌─────────────┐   logical repl     ┌─────────────┐
│  Publisher   │ ──────────────>    │  Subscriber  │
│  (R/W)       │                   │  (R/O → R/W) │
└─────────────┘                    └─────────────┘
      │                                  │
   cutover: switch DNS/VIP ──────────────┘
```

```bash
# Sul vecchio server (PG 16)
# wal_level = logical deve essere già attivo

# Crea pubblicazione
sudo -u postgres psql -c "CREATE PUBLICATION upgrade_pub FOR ALL TABLES;"

# Sul nuovo server (PG 17)
# Importa lo schema (NON i dati)
sudo -u postgres pg_dump -s -h old-server myapp | sudo -u postgres psql myapp

# Crea subscription
sudo -u postgres psql -c "
CREATE SUBSCRIPTION upgrade_sub
    CONNECTION 'host=old-server port=5432 dbname=myapp user=replicator'
    PUBLICATION upgrade_pub
    WITH (copy_data = true);"

# Aspetta sync (controlla lag)
sudo -u postgres psql -c "SELECT * FROM pg_stat_subscription;"

# Cutover:
# 1. Ferma le applicazioni (o redirect a maintenance page)
# 2. Aspetta che il lag sia 0
# 3. Dropa la subscription sul nuovo server
# 4. Switch DNS/VIP al nuovo server
# 5. Riavvia le applicazioni
```

### Upgrade via pg_dump/pg_restore

Il metodo più semplice ma più lento, accettabile solo per database piccoli:

```bash
# 1. Dump dal vecchio server
sudo -u postgres pg_dumpall -h old-server > /backup/all_dbs.sql

# 2. Restore sul nuovo server
sudo -u postgres psql -h new-server -f /backup/all_dbs.sql

# Downtime = tempo di dump + tempo di restore
# Per un DB da 100GB, può essere molte ore
```

### Confronto Strategie di Upgrade

| Strategia | Downtime | Complessità | Rischio | Rollback |
|---|---|---|---|---|
| pg_upgrade --link | Minuti | Media | Medio | No (irreversibile) |
| pg_upgrade --copy | Minuti-Ore | Media | Basso | Sì (vecchio intatto) |
| Logical replication | Secondi | Alta | Basso | Sì (vecchio attivo) |
| pg_dump/restore | Ore | Bassa | Basso | Sì |

---

## Best Practices

### Sicurezza

1. **Non usare mai `trust` in pg_hba.conf in produzione**: `trust` permette connessione senza password.

2. **Usa `scram-sha-256` per l'autenticazione**: È il metodo più sicuro disponibile. MD5 è deprecato.

3. **Forza SSL per connessioni remote**: usa `hostssl` in pg_hba.conf e `sslmode=verify-full` nei client.

4. **Principio del minimo privilegio**: ogni applicazione ha un ruolo dedicato con solo i permessi necessari. Mai connettere come superuser.

5. **Ruota le password regolarmente**: usa `VALID UNTIL` per forzare la scadenza.

### Performance

6. **Tuna shared_buffers al 25% della RAM**: È il parametro singolo più importante. Non superare il 40%.

7. **Configura `random_page_cost = 1.1` per SSD**: Il default (4.0) è per HDD e causa piani subottimali su SSD.

8. **Usa pg_stat_statements**: Sempre attivo. È lo strumento più importante per l'ottimizzazione.

9. **Monitora il cache hit ratio**: deve essere > 99% per OLTP. Se inferiore, aumenta shared_buffers.

10. **Log le query lente**: `log_min_duration_statement = 1000` per trovare query problematiche.

### Manutenzione

11. **Non disabilitare autovacuum**: Se causa problemi, regola i parametri (cost_delay, cost_limit). Per tabelle grandi, usa override per-tabella.

12. **Monitora il transaction ID wraparound**: Se `age(datfrozenxid)` > 1 miliardo, c'è rischio. Setup alerting.

13. **Backup: pg_dump + WAL archiving + pgBackRest**: tre livelli di protezione. Testa i restore regolarmente.

14. **Connection pooling**: Se l'applicazione apre > 100 connessioni, pgBouncer è obbligatorio.

15. **Partitioning per tabelle > 100M righe**: migliora VACUUM, query su range temporali, e gestione dati storici.

### Replicazione e HA

16. **Usa replication slots**: prevengono la rimozione prematura dei WAL necessari al replica. Monitora che gli slot non accumulino troppo lag.

17. **Testa il failover regolarmente**: non aspettare un'emergenza per scoprire che il failover non funziona.

18. **Considera Patroni per HA automatico**: in ambienti dove il downtime ha costo elevato.

---

## Troubleshooting

### Problema: Connessione rifiutata

**Sintomi**: `psql: error: connection refused` o `no pg_hba.conf entry for host`.

**Causa**: PostgreSQL non ascolta sull'interfaccia richiesta, o pg_hba.conf non permette la connessione.

**Soluzione**:
```bash
# Verifica listen_addresses
sudo -u postgres psql -c "SHOW listen_addresses;"

# Verifica porta in ascolto
ss -tlnp | grep 5432

# Verifica pg_hba.conf per l'IP del client
grep -v '^#' /etc/postgresql/16/main/pg_hba.conf | grep -v '^$'

# Verifica errori nel pg_hba.conf (PG 15+)
sudo -u postgres psql -c "SELECT * FROM pg_hba_file_rules WHERE error IS NOT NULL;"

# Dopo modifiche: reload (non restart)
sudo systemctl reload postgresql

# Se "no pg_hba.conf entry":
# L'indirizzo IP del client non matcha nessuna regola
# Aggiungi una regola in pg_hba.conf e fai reload
```

### Problema: Database lento, query timeout

**Sintomi**: Le query che normalmente sono veloci impiegano minuti.

**Causa**: Tabella bloated, statistiche obsolete, lock contention, o parametri di memoria sbagliati.

**Soluzione**:
```sql
-- 1. Verifica dead tuples (bloat)
SELECT relname, n_dead_tup, n_live_tup,
       round(n_dead_tup * 100.0 / NULLIF(n_live_tup, 0), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
-- Se dead_pct è alto: VACUUM ANALYZE table_name;

-- 2. Verifica lock
SELECT pid, usename, state, wait_event_type, wait_event,
       left(query, 60) AS query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';

-- 3. Verifica cache hit ratio
SELECT round(sum(heap_blks_hit) * 100.0 /
    NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) AS ratio
FROM pg_statio_user_tables;
-- Se < 99%, aumenta shared_buffers

-- 4. Verifica query plan
EXPLAIN (ANALYZE, BUFFERS, TIMING) SELECT ...;
-- Cerca: Seq Scan su tabelle grandi (indice mancante?)
-- Cerca: Nested Loop con molte righe (hash join sarebbe meglio?)
-- Cerca: Sort con external merge (work_mem troppo basso?)
```

### Problema: Disco pieno da WAL

**Sintomi**: `PANIC: could not write to file "pg_wal/..."` o disco pieno nella partizione di pg_wal.

**Causa**: Replication slot inutilizzato che impedisce la rimozione dei WAL, o archive_command che fallisce.

**Soluzione**:
```sql
-- 1. Verifica replication slots con lag
SELECT slot_name, active, slot_type,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag
FROM pg_replication_slots
ORDER BY pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) DESC;

-- 2. Rimuovi slot inattivo che accumula WAL
SELECT pg_drop_replication_slot('stale_slot_name');

-- 3. Verifica archive_command
SELECT archived_count, failed_count, last_archived_wal,
       last_archived_time, last_failed_wal, last_failed_time
FROM pg_stat_archiver;
-- Se failed_count è alto, l'archive_command fallisce
-- Controlla i log per i dettagli dell'errore

-- 4. Emergenza: se il disco è davvero pieno, libera spazio
-- NON eliminare manualmente file da pg_wal!
-- Piuttosto, dropa un replication slot inattivo o correggi archive_command
```

### Problema: Autovacuum non riesce a completare

**Sintomi**: Dead tuples crescono costantemente, autovacuum gira continuamente ma non completa.

**Causa**: long-running transactions che impediscono la rimozione delle dead tuples (il vacuum non può rimuovere tuple visibili a transazioni ancora attive).

```sql
-- Trova la transazione più vecchia ancora attiva
SELECT pid, usename, datname,
       now() - xact_start AS transaction_age,
       state,
       left(query, 60) AS query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start ASC
LIMIT 5;

-- La colonna "oldest xmin" nel VACUUM VERBOSE output indica
-- l'XID più vecchio che impedisce la pulizia

-- Soluzione:
-- 1. Termina le transazioni long-running
SELECT pg_terminate_backend(pid);

-- 2. Previeni con:
-- idle_in_transaction_session_timeout = '10min'  -- kill sessioni idle in txn
-- statement_timeout = '60s'                      -- timeout query (applicazione)

-- 3. Configura hot_standby_feedback = off sui replica
-- (un replica con feedback attivo può bloccare il vacuum sul primary)
```

### Problema: Replica lag in crescita

**Sintomi**: Il lag di replicazione cresce costantemente.

```sql
-- Sul primary
SELECT
    client_addr,
    state,
    pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) AS replay_lag,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn)) AS send_lag
FROM pg_stat_replication;

-- Cause comuni:
-- 1. Replica con risorse insufficienti (CPU, I/O)
-- 2. Query pesanti sul replica (hot_standby = on)
-- 3. Rete lenta tra primary e replica
-- 4. max_wal_senders troppo basso (WAL sender saturati)

-- Sul replica: verifica conflitti
SELECT datname, confl_tablespace, confl_lock, confl_snapshot,
       confl_bufferpin, confl_deadlock
FROM pg_stat_database_conflicts
WHERE datname = current_database();
-- confl_snapshot alto → query sul replica conflittano con vacuum del primary
-- Soluzione: hot_standby_feedback = on (ma attenzione al vacuum sul primary)
-- Oppure: max_standby_streaming_delay = 300s (tollerare più delay)
```

### Problema: Connessioni esaurite (too many connections)

**Sintomi**: `FATAL: too many connections for role "app_user"` oppure `FATAL: sorry, too many clients already`. L'applicazione non riesce a connettersi al database.

**Causa**: il numero di connessioni attive ha raggiunto `max_connections` (default: 100). Cause frequenti: (1) connection leak nell'applicazione — connessioni aperte ma mai chiuse. (2) Transazioni long-running che tengono occupate le connessioni. (3) Pool di connessioni non configurato o con `pool_size` troppo alto. (4) Più istanze dell'applicazione senza coordinamento sul numero totale di connessioni.

**Soluzione**:
```sql
-- 1. Diagnostica immediata: vedere chi occupa le connessioni
SELECT
    usename,
    client_addr,
    state,
    count(*) AS conn_count,
    max(now() - state_change) AS max_idle_time
FROM pg_stat_activity
WHERE backend_type = 'client backend'
GROUP BY usename, client_addr, state
ORDER BY conn_count DESC;

-- 2. Trovare connessioni idle da troppo tempo
SELECT pid, usename, state, now() - state_change AS idle_time,
       left(query, 60) AS last_query
FROM pg_stat_activity
WHERE state = 'idle'
  AND now() - state_change > interval '10 minutes';

-- 3. Terminare connessioni idle vecchie (con cautela)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND now() - state_change > interval '30 minutes'
  AND usename != 'postgres';

-- 4. Prevenzione: configurare timeout
-- idle_in_transaction_session_timeout = '5min'  -- kill sessioni idle in transazione
-- statement_timeout = '60s'                     -- timeout per singole query
```

**Soluzione strutturale**: installare pgBouncer in `transaction` mode. Con pgBouncer, 200 client condividono 25 connessioni PostgreSQL reali. Senza pooler, 200 client richiedono 200 connessioni — ogni connessione PostgreSQL consuma ~10 MB di RAM.

### Problema: Query che causa spike di CPU al 100%

**Sintomi**: una o più query saturano la CPU del server. Altre query diventano lente. `top` mostra processi PostgreSQL al 100%.

**Causa**: query senza indici su tabelle grandi (sequential scan completo), join cartesiani accidentali (prodotto cartesiano tra tabelle), funzioni custom inefficienti in loop, CTE ricorsive senza condizione di uscita, `ORDER BY` su colonne non indicizzate con milioni di righe.

**Soluzione**:
```sql
-- 1. Trovare la query che consuma più risorse
SELECT pid, usename,
       now() - query_start AS duration,
       state,
       wait_event_type,
       left(query, 100) AS query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY query_start ASC;

-- 2. Cancellare la query (non la sessione)
SELECT pg_cancel_backend(<pid>);
-- Se non risponde al cancel:
SELECT pg_terminate_backend(<pid>);

-- 3. Analizzare il piano della query problematica
EXPLAIN (ANALYZE, BUFFERS, TIMING) <la query>;
-- Cercare:
-- - "Seq Scan" su tabelle con milioni di righe → manca un indice
-- - "Nested Loop" con "rows=1" stimato ma migliaia effettivi → statistiche obsolete
-- - "Sort Method: external merge" → work_mem troppo basso
-- - "Hash" con "Batches: 4" → work_mem troppo basso per hash join in memoria

-- 4. Se le statistiche sono obsolete
ANALYZE <table_name>;
-- O per tutte le tabelle
ANALYZE;
```

### Problema: Corruzione dati sospetta

```bash
# Se data checksums sono abilitati:
# PostgreSQL scrive "WARNING: page verification failed" nei log

# Verifica checksums offline
sudo systemctl stop postgresql
sudo -u postgres pg_checksums --check -D /var/lib/postgresql/16/main
# Output: bad checksums found in X blocks

# Opzioni:
# 1. Se solo pochi blocchi: potrebbe essere riparabile con pg_resetwal (ULTIMO RESORT)
# 2. Se molti blocchi: restore dal backup
# 3. Se singola tabella: REINDEX può riparare corruzione indice
sudo -u postgres psql -c "REINDEX TABLE corrupted_table;"

# AMCHECK: verifica integrità indici B-tree (online)
CREATE EXTENSION amcheck;
SELECT bt_index_check('idx_users_email');
-- Verifica senza lock esclusivo

SELECT bt_index_parent_check('idx_users_email', true);
-- Verifica più approfondita ma richiede ACCESS SHARE lock
```

---

## Domande e Risposte (Q&A)

**D1: Quanto grande dovrebbe essere `shared_buffers`? C'è un massimo assoluto?**

Il 25% della RAM è la regola generale per server dedicati a PostgreSQL. Non superare il 40% perché Linux ha la propria page cache: se `shared_buffers` è troppo grande, si crea "double buffering" (gli stessi dati vengono cached sia in shared_buffers che nella page cache). Con 256GB+ di RAM, alcuni test mostrano benefici fino a 64-80GB ma raramente oltre. Usa `pg_buffercache` per verificare l'hit ratio del buffer pool: se è > 99% stai bene.

**D2: `pool_mode = transaction` in pgBouncer rompe le mie prepared statements. Come risolvo?**

Con `pool_mode = transaction`, la connessione PostgreSQL sottostante cambia tra una transazione e l'altra, quindi prepared statements con nome (`PREPARE`/`EXECUTE`) non persistono. Soluzioni: (1) Usa prepared statements a livello di protocollo (extended query protocol) — supportati dalla maggior parte dei driver moderni e compatibili con transaction mode. (2) Se devi usare prepared statements SQL, configura pgBouncer con `pool_mode = session` per quelle connessioni specifiche (puoi avere pool diversi nello stesso pgBouncer).

**D3: Quando usare `VACUUM FULL` vs `pg_repack`?**

Quasi mai `VACUUM FULL`. `VACUUM FULL` richiede un `ACCESS EXCLUSIVE` lock — la tabella è completamente inaccessibile durante l'operazione, che su tabelle grandi può durare ore. `pg_repack` fa lo stesso lavoro (riscrive la tabella in modo compatto) ma usa un approccio basato su trigger che mantiene la tabella accessibile. L'unico caso per `VACUUM FULL` è in una finestra di manutenzione pianificata dove puoi permetterti il downtime completo della tabella.

**D4: Streaming replication vs logical replication: quale scegliere?**

Streaming per HA e read scaling (stessa versione, replica completa). Logical per: (1) replicazione tra versioni diverse (es. upgrade), (2) replicazione selettiva di tabelle specifiche, (3) replica scrivibile per altre tabelle, (4) replicazione cross-database o cross-cluster. In molti ambienti si usano entrambe: streaming per i replica HA e logical per ETL/analytics.

**D5: Il mio autovacuum non riesce mai a completare il vacuum su una tabella grande. Perché?**

La causa più comune è una long-running transaction (anche idle in transaction) che impedisce la rimozione delle dead tuples. VACUUM non può rimuovere tuple che sono ancora potenzialmente visibili a transazioni attive. Verifica con `SELECT min(xact_start) FROM pg_stat_activity WHERE xact_start IS NOT NULL;`. Altra causa: il replica con `hot_standby_feedback = on` — lo snapshot del replica impedisce il vacuum sul primary. Soluzione: configura `idle_in_transaction_session_timeout` e monitora le transazioni long-running.

**D6: Come scelgo tra range, list e hash partitioning?**

- **Range**: dati temporali (log, ordini, metriche). Le query filtrano quasi sempre per intervallo di date. Permette facile archiviazione dei dati vecchi (detach partizioni).
- **List**: dati categorici con valori discreti (regione, tipo, tenant in multi-tenant). Ogni valore corrisponde a una partizione.
- **Hash**: distribuzione uniforme quando non c'è un criterio naturale. Utile per parallelizzare vacuum e index build su tabelle enormi. Non supporta detach naturale di "vecchi" dati.

**D7: Qual è il rischio reale del transaction ID wraparound?**

Se `age(datfrozenxid)` raggiunge 2 miliardi, PostgreSQL entra in "emergency autovacuum mode": rifiuta TUTTE le transazioni in scrittura e si ferma (o diventa read-only) fino a quando il vacuum anti-wraparound non completa. Questo è un evento catastrofico in produzione. Il vacuum anti-wraparound è single-threaded e non throttled, quindi può saturare I/O. Previeni monitorando `age(datfrozenxid)` con alerting a 500M e 1B.

**D8: Dovrei usare pgBackRest o Barman?**

pgBackRest se: gestisci pochi server, vuoi backup incrementali veloci, usi S3/cloud storage, e hai bisogno di restore parallelo veloce. Barman se: gestisci molti server PostgreSQL da un punto centralizzato, e preferisci un'architettura client-server per il backup management. Entrambi sono production-ready e ben mantenuti. pgBackRest ha una community più ampia e performance di restore generalmente migliori.

**D9: Posso usare pgBouncer e Pgpool-II insieme?**

Sì, è un pattern comune: Pgpool-II per load balancing read/write e failover, pgBouncer davanti a ogni PostgreSQL per connection pooling. pgBouncer è molto più efficiente nel pooling, mentre Pgpool-II eccelle nel routing. Lo stack è: App → Pgpool-II (routing) → pgBouncer (pooling) → PostgreSQL.

**D10: Come monitorare le dimensioni delle tabelle e il bloat?**

```sql
-- Dimensione tabelle con indici
SELECT
    schemaname || '.' || tablename AS tabella,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS dim_totale,
    pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS dim_tabella,
    pg_size_pretty(pg_indexes_size(schemaname || '.' || tablename)) AS dim_indici,
    n_dead_tup,
    CASE WHEN n_live_tup > 0
         THEN round(100.0 * n_dead_tup / n_live_tup, 1)
         ELSE 0 END AS dead_pct
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
LIMIT 20;
```

Il rapporto `dead_pct` indica il bloat: se supera il 20%, la tabella necessita vacuum aggressivo. Oltre il 50%, considerare `pg_repack` per ricompattare senza downtime. Per un'analisi precisa del bloat a livello di pagina, usare l'estensione `pgstattuple`.

**D11: Come configurare pg_stat_statements e interpretare i risultati?**

`pg_stat_statements` è lo strumento più importante per l'ottimizzazione delle performance. Deve essere sempre attivo in produzione.

```sql
-- Abilitare (richiede restart)
-- postgresql.conf: shared_preload_libraries = 'pg_stat_statements'
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top 10 query per tempo totale
SELECT
    left(query, 80) AS query,
    calls,
    round(total_exec_time::numeric, 2) AS total_ms,
    round(mean_exec_time::numeric, 2) AS mean_ms,
    round(stddev_exec_time::numeric, 2) AS stddev_ms,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Resettare le statistiche periodicamente (es. dopo deploy)
SELECT pg_stat_statements_reset();
```

La colonna `stddev_exec_time` è particolarmente utile: una deviazione standard alta indica performance instabili — la query è veloce con dati in cache e lenta senza. La colonna `shared_blks_hit` vs `shared_blks_read` mostra se la query beneficia del cache o colpisce il disco.

**D12: Come gestire correttamente i lock e prevenire deadlock?**

PostgreSQL usa MVCC e lock a granularità di riga. I deadlock si verificano quando due transazioni acquisiscono lock in ordine opposto.

```sql
-- Trovare lock attivi e conflitti
SELECT
    blocked.pid AS blocked_pid,
    blocked.usename AS blocked_user,
    left(blocked.query, 60) AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.usename AS blocking_user,
    left(blocking.query, 60) AS blocking_query,
    blocked.wait_event_type
FROM pg_stat_activity AS blocked
JOIN pg_locks AS bl ON bl.pid = blocked.pid
JOIN pg_locks AS bk ON bk.locktype = bl.locktype
    AND bk.database IS NOT DISTINCT FROM bl.database
    AND bk.relation IS NOT DISTINCT FROM bl.relation
    AND bk.page IS NOT DISTINCT FROM bl.page
    AND bk.tuple IS NOT DISTINCT FROM bl.tuple
    AND bk.pid != bl.pid
JOIN pg_stat_activity AS blocking ON blocking.pid = bk.pid
WHERE NOT bl.granted;

-- Terminare una transazione che blocca (con cautela)
SELECT pg_cancel_backend(<blocking_pid>);   -- cancella la query
SELECT pg_terminate_backend(<blocking_pid>); -- termina la sessione
```

Prevenzione: (1) acquisire lock sempre nello stesso ordine (es. per ID crescente), (2) mantenere transazioni corte, (3) impostare `lock_timeout = '10s'` per evitare attese indefinite, (4) usare `SKIP LOCKED` per pattern di code di lavoro.

**D13: Qual è la configurazione ottimale di `work_mem`?**

`work_mem` controlla la memoria per operazioni di sort e hash per query. Il default di 4 MB è spesso troppo basso per query analitiche e troppo alto se moltiplicato per centinaia di connessioni concorrenti.

Calcolo: `work_mem = RAM disponibile / (max_connections × 3)`. Con 16 GB RAM e 100 connessioni: `work_mem = 16384 / 300 ≈ 50 MB`. Tuttavia, non tutte le connessioni eseguono sort contemporaneamente. Un approccio pragmatico: impostare un valore moderato a livello globale (32-64 MB) e aumentarlo a livello di sessione per query analitiche pesanti: `SET work_mem = '256MB';` prima della query. Monitorare i file temporanei (`temp_files`, `temp_bytes` in `pg_stat_database`): se frequenti, `work_mem` è troppo basso.

**D14: Come configurare pg_cron per task schedulati all'interno di PostgreSQL?**

pg_cron è un'estensione che permette di schedulare job SQL direttamente nel database, eliminando la necessità di cron job esterni per operazioni di manutenzione.

```sql
-- Installare pg_cron (richiede shared_preload_libraries e restart)
CREATE EXTENSION pg_cron;

-- Vacuum analyze notturno su una tabella pesante
SELECT cron.schedule('vacuum-orders', '0 3 * * *',
    'VACUUM ANALYZE orders');

-- Pulizia dati vecchi ogni domenica
SELECT cron.schedule('cleanup-logs', '0 4 * * 0',
    'DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL ''90 days''');

-- Refresh materialized view ogni 15 minuti
SELECT cron.schedule('refresh-mv-stats', '*/15 * * * *',
    'REFRESH MATERIALIZED VIEW CONCURRENTLY mvw_daily_stats');

-- Elencare i job
SELECT * FROM cron.job;

-- Verificare le esecuzioni recenti
SELECT * FROM cron.job_run_details
ORDER BY start_time DESC LIMIT 20;

-- Rimuovere un job
SELECT cron.unschedule('vacuum-orders');
```

**D15: Come gestire l'upgrade di PostgreSQL in produzione con zero downtime?**

L'approccio a zero downtime usa la replicazione logica per sincronizzare i dati tra la versione vecchia e quella nuova, poi effettua un rapido switchover.

Procedura: (1) Installare la nuova versione di PostgreSQL su un server separato. (2) Configurare la pubblicazione sulla vecchia versione: `CREATE PUBLICATION full_pub FOR ALL TABLES;`. (3) Creare una subscription sulla nuova versione che replica i dati. (4) Attendere che la replica sia sincronizzata (`SELECT * FROM pg_stat_subscription;`). (5) Fermare il traffico applicativo, verificare che non ci sia lag, poi switchare il DNS o il load balancer verso la nuova versione. Il downtime è limitato al tempo di switchover (pochi secondi con DNS TTL basso o istantaneo con load balancer).

Attenzione: la replicazione logica non replica DDL, sequenze, large objects, e tabelle senza primary key. Questi elementi devono essere gestiti manualmente prima dello switchover.

**D16: Quando e come usare le tabelle UNLOGGED?**

Le tabelle UNLOGGED non scrivono WAL (Write-Ahead Log), rendendole significativamente più veloci per le scritture (2-5x), ma i dati vengono persi in caso di crash e non sono replicati.

Casi d'uso appropriati: (1) tabelle di sessione web, (2) cache applicativa, (3) staging area per ETL, (4) tabelle temporanee persistenti tra sessioni. Mai per dati di business. Creare con `CREATE UNLOGGED TABLE staging_import (...)`. Convertire a logged dopo il caricamento: `ALTER TABLE staging_import SET LOGGED;` (richiede riscrittura completa della tabella).

---

## Esercizi Pratici

### Esercizio 1: Setup Replicazione con Failover

**Obiettivo**: Configurare streaming replication tra un primary e un replica, poi eseguire un failover manuale.

**Passi**:
1. Installa PostgreSQL su due VM/container (primary: 10.0.1.1, replica: 10.0.2.10)
2. Configura `wal_level = replica`, `max_wal_senders = 5`, `max_replication_slots = 5` sul primary
3. Crea il ruolo `replicator` con REPLICATION e configura pg_hba.conf
4. Esegui `pg_basebackup` con `-R` per seedare il replica
5. Verifica lo streaming con `pg_stat_replication` e `pg_is_in_recovery()`
6. Crea dati sul primary e verifica che appaiano sul replica
7. Simula un crash: ferma il primary
8. Promuovi il replica: `SELECT pg_promote();`
9. Verifica che il replica accetti scritture
10. **Verifica**: il nuovo primary accetta INSERT e `pg_is_in_recovery()` restituisce `false`

### Esercizio 2: PITR con pgBackRest

**Obiettivo**: Configurare pgBackRest, eseguire un backup full, simulare un errore, e fare un PITR.

**Passi**:
1. Installa e configura pgBackRest con repository locale
2. Configura `archive_command = 'pgbackrest --stanza=mydb archive-push %p'`
3. Esegui `stanza-create` e `check`
4. Esegui un backup full
5. Crea un restore point: `SELECT pg_create_restore_point('before_delete');`
6. Inserisci dati importanti, nota il timestamp
7. Simula un errore: `DELETE FROM important_table;`
8. Esegui PITR al timestamp del punto 6
9. Verifica che i dati importanti siano stati ripristinati
10. **Verifica**: `SELECT count(*) FROM important_table;` restituisce i dati pre-delete

### Esercizio 3: Partitioning e Performance

**Obiettivo**: Creare una tabella partizionata, popolarla, e verificare il partition pruning.

**Passi**:
1. Crea una tabella `events` partizionata per range su `event_date`
2. Crea 12 partizioni mensili per il 2024
3. Crea una partizione DEFAULT
4. Inserisci 1M di righe distribuite uniformemente
5. Esegui `EXPLAIN ANALYZE` su una query che filtra per un mese specifico
6. Verifica che solo una partizione venga scansionata (partition pruning)
7. Disabilita il pruning con `SET enable_partition_pruning = off` e confronta
8. Detach una partizione vecchia e verifica che la tabella principale funzioni
9. Configura autovacuum per-partizione con parametri più aggressivi
10. **Verifica**: il piano mostra "Append" con una sola partizione scansionata

### Esercizio 4: Connection Pooling con pgBouncer

**Obiettivo**: Configurare pgBouncer in transaction mode e verificare il miglioramento.

**Passi**:
1. Installa pgBouncer
2. Configura `pool_mode = transaction`, `default_pool_size = 25`, `max_client_conn = 200`
3. Genera il file userlist.txt da pg_shadow
4. Connetti un'applicazione via pgBouncer (porta 6432)
5. Usa `SHOW POOLS` per verificare il pooling
6. Esegui un benchmark con `pgbench` direttamente a PostgreSQL e via pgBouncer
7. Confronta: connessioni attive a PostgreSQL (`pg_stat_activity`)
8. Configura TLS client → pgBouncer e pgBouncer → PostgreSQL
9. Testa le limitazioni: LISTEN/NOTIFY, prepared statements
10. **Verifica**: con pgBouncer, PostgreSQL mantiene max 25 connessioni anche con 200 client

### Esercizio 5: Monitoring Completo

**Obiettivo**: Creare un dashboard di monitoring con le query essenziali.

**Passi**:
1. Abilita `pg_stat_statements` (shared_preload_libraries + CREATE EXTENSION)
2. Scrivi uno script che raccoglie:
   - Connessioni per stato
   - Cache hit ratio (> 99%?)
   - Dead tuples per tabella
   - Transaction ID age (wraparound risk?)
   - Replication lag (se replica presente)
   - Top 10 query lente (da pg_stat_statements)
   - Indici inutilizzati
   - Lock attivi
3. Configura `auto_explain` per loggare piani di query > 2s
4. Crea alerting per: cache hit ratio < 95%, xid age > 500M, replication lag > 1MB
5. Simula un problema (es. tabella non vacuumata, query senza indice) e verifica che il monitoring lo rilevi
6. **Verifica**: lo script identifica correttamente il problema simulato

---

## Checklist Operativa per Nuova Installazione PostgreSQL

Una checklist pragmatica per mettere in produzione una nuova istanza PostgreSQL in modo sicuro e performante:

```
═══════════════════════════════════════════════════════════════
           POSTGRESQL PRODUCTION READINESS CHECKLIST
═══════════════════════════════════════════════════════════════

▸ INSTALLAZIONE E CONFIGURAZIONE
  [ ] Versione PostgreSQL recente (16+ consigliato)
  [ ] Data checksums abilitati (initdb --data-checksums)
  [ ] Timezone impostato correttamente (timezone = 'UTC' consigliato)
  [ ] Locale UTF-8 configurato
  [ ] shared_buffers = 25% RAM (non superare 40%)
  [ ] effective_cache_size = 75% RAM
  [ ] work_mem = RAM / (max_connections × 3) (minimo 32MB)
  [ ] maintenance_work_mem = 512MB-2GB
  [ ] random_page_cost = 1.1 (per SSD)
  [ ] effective_io_concurrency = 200 (per SSD)

▸ SICUREZZA
  [ ] pg_hba.conf: nessuna regola "trust" (solo scram-sha-256)
  [ ] SSL forzato per connessioni remote (hostssl in pg_hba.conf)
  [ ] ssl_min_protocol_version = 'TLSv1.3'
  [ ] Utente applicativo con minimo privilegio (no superuser)
  [ ] Utente migrazioni separato dall'utente applicativo
  [ ] Password con complessità adeguata e scadenza
  [ ] listen_addresses limitato alle interfacce necessarie

▸ MONITORAGGIO
  [ ] pg_stat_statements abilitato
  [ ] log_min_duration_statement = 1000 (log query > 1 sec)
  [ ] log_checkpoints = on
  [ ] log_connections = on / log_disconnections = on
  [ ] log_lock_waits = on
  [ ] Alert su: cache hit ratio, XID age, replication lag
  [ ] Alert su: spazio disco, connessioni attive, query lente

▸ BACKUP E RECOVERY
  [ ] WAL archiving configurato e funzionante
  [ ] Backup full giornaliero (pgBackRest o Barman)
  [ ] Restore testato (non "configurato" — testato)
  [ ] RPO e RTO documentati e verificati
  [ ] Retention policy definita (minimo 7 giorni full)

▸ MANUTENZIONE
  [ ] autovacuum attivo con parametri ragionevoli
  [ ] idle_in_transaction_session_timeout configurato
  [ ] statement_timeout configurato (applicazione)
  [ ] Monitoraggio XID wraparound (alert a 500M)
  [ ] Piano di upgrade major version documentato

▸ ALTA DISPONIBILITÀ (se necessaria)
  [ ] Streaming replication configurata con almeno 1 standby
  [ ] Replication slot per prevenire perdita WAL
  [ ] Failover automatico (Patroni) o procedura manuale testata
  [ ] Connection pooler (pgBouncer) se > 50 connessioni

═══════════════════════════════════════════════════════════════
```

---

## Riferimenti

- **PostgreSQL Documentation**: https://www.postgresql.org/docs/16/
- **PostgreSQL Wiki — Tuning**: https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server
- **pgTune**: https://pgtune.leopard.in.ua/ — calcolatore parametri
- **pg_stat_statements**: https://www.postgresql.org/docs/16/pgstatstatements.html
- **pgBouncer**: https://www.pgbouncer.org/
- **Pgpool-II**: https://www.pgpool.net/
- **pgBackRest**: https://pgbackrest.org/
- **Barman**: https://www.pgbarman.org/
- **Patroni** (HA): https://github.com/patroni/patroni
- **pg_repack**: https://github.com/reorg/pg_repack
- **PostGIS**: https://postgis.net/
- **The Internals of PostgreSQL**: https://www.interdb.jp/pg/

---

## Note Operative

### Comandi di Emergenza

Situazioni che richiedono intervento immediato e i comandi corrispondenti — da memorizzare o tenere nel runbook:

```sql
-- EMERGENZA: Database non accetta connessioni (max_connections raggiunto)
-- Soluzione immediata: liberare connessioni idle
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND now() - state_change > interval '5 minutes'
  AND usename != 'postgres';

-- EMERGENZA: Query bloccante che tiene lock su tabelle critiche
-- 1. Trovare il PID della query bloccante
SELECT pid, usename, state, now() - query_start AS duration,
       left(query, 80) AS query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock' OR state = 'active'
ORDER BY query_start ASC;
-- 2. Cancellare la query (tentativo soft)
SELECT pg_cancel_backend(<pid>);
-- 3. Se non risponde entro 10 secondi, terminare la sessione
SELECT pg_terminate_backend(<pid>);

-- EMERGENZA: Disco pieno da WAL
-- 1. Verificare slot di replica orfani
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag
FROM pg_replication_slots WHERE NOT active;
-- 2. Droppare slot orfani
SELECT pg_drop_replication_slot('nome_slot_orfano');

-- EMERGENZA: XID wraparound imminente (age > 1.5 miliardi)
-- 1. Verificare
SELECT datname, age(datfrozenxid) AS xid_age
FROM pg_database ORDER BY xid_age DESC;
-- 2. Forzare vacuum anti-wraparound
VACUUM FREEZE VERBOSE <tabella_con_xid_piu_vecchio>;

-- EMERGENZA: Verifica rapida dello stato generale
SELECT
    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') AS active_queries,
    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') AS idle_connections,
    (SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock') AS waiting_on_lock,
    (SELECT max(age(datfrozenxid)) FROM pg_database) AS max_xid_age,
    (SELECT pg_size_pretty(pg_database_size(current_database()))) AS db_size,
    (SELECT round(sum(heap_blks_hit)*100.0/nullif(sum(heap_blks_hit)+sum(heap_blks_read),0),2)
     FROM pg_statio_user_tables) AS cache_hit_pct;
```

Questi comandi dovrebbero essere in un runbook accessibile offline — durante un'emergenza, il database potrebbe essere lento e la connessione a Internet potrebbe non essere disponibile.
- `man psql`, `man pg_dump`, `man pg_basebackup`, `man pg_upgrade`
