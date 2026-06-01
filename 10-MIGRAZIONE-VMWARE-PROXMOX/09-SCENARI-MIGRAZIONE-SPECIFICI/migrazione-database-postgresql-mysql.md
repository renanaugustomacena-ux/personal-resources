# Migrazione di Database PostgreSQL e MySQL/MariaDB da VMware a Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 09.2 (segue 09.1 stateful generico, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 09.1 (applicazioni stateful — concetti di drain, parallel run, rolling); modulo 06.1-06.3 (strategie e live cutover); modulo 08 (migrazione storage, formato raw, cache none); fluenza SQL DDL/DML; familiarita con `psql`/`mysql` CLI.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere i tre approcci di migrazione DB (offline dump/restore, online via streaming/binlog replication, application-level) e scegliere quello corretto in base a downtime tollerabile, dimensione del database e versione major sorgente/destinazione;
> 2. eseguire una migrazione PostgreSQL offline con `pg_dumpall` e formato custom (`pg_dump -Fc`), incluso il restore parallelo (`pg_restore --jobs=N`) e la verifica integrita post-restore (counts, foreign key, indici validi, `ANALYZE`);
> 3. configurare e gestire una **streaming replication** PostgreSQL come strategia online: setup primary, `pg_basebackup -R`, monitoraggio `pg_stat_replication`/`pg_stat_wal_receiver`, cutover con `pg_promote()`, e gestione di `wal_keep_size` per evitare timeline mismatch;
> 4. eseguire una migrazione MySQL/MariaDB con `mysqldump --single-transaction --master-data=2`, oppure con `xtrabackup` per hot backup fisico, comprendendo il trade-off velocita vs portabilita;
> 5. configurare una **GTID-based replication** MySQL 8.0+ come strategia online: `gtid_mode=ON`, `enforce_gtid_consistency=ON`, `CHANGE REPLICATION SOURCE TO ... SOURCE_AUTO_POSITION=1`, e cutover con `STOP REPLICA; RESET REPLICA ALL`;
> 6. progettare la VM Proxmox per workload database secondo i parametri critici (`--balloon 0`, `--cpu host`, `--numa 1`, dischi raw con `cache=none,iothread=1`, separazione fisica dati / WAL-binlog), e adattare il tuning del DB (`shared_buffers`, `innodb_buffer_pool_size`, `huge_pages`) alla nuova RAM;
> 7. eseguire baseline di performance pre-migrazione con `pgbench`, `sysbench` e `fio`, replicarle post-migrazione, e valutare se la degradazione (> 10% TPS / latenza p99) richiede tuning aggiuntivo.
> **Tempo stimato:** lettura 90-120 min · lab 360-540 min (per simulare un caso pratico end-to-end con benchmark)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** PostgreSQL 13, 14, 15, 16, 17 (con focus su 15+ per `wal_keep_size`); MySQL 8.0 / 8.4 LTS, MariaDB 10.6 / 10.11 / 11.4; Percona XtraBackup 8.0 / 8.4; pgBouncer 1.22+; Proxmox VE 8.x; QEMU/KVM 7.x → 10.x.

## Mappa concettuale

```
+============================================================+
|     Migrazione Database — albero decisionale e flussi      |
+============================================================+
|                                                            |
|   1. Caratterizzare il DB                                  |
|      - dimensione totale (GB), tasso di scrittura (TPS)    |
|      - versione major (sorgente == destinazione?)          |
|      - downtime tollerabile (secondi / minuti / ore)       |
|                                                            |
|              +------------------+                          |
|              | Downtime > 30min |--YES--> OFFLINE          |
|              +------------------+         pg_dumpall /     |
|                       |                   mysqldump /      |
|                       NO                  xtrabackup       |
|                       |                                    |
|              +------------------+                          |
|              | DB < 100 GB ?    |--YES--> ONLINE LOGICAL   |
|              +------------------+         pg_basebackup +  |
|                       |                   streaming        |
|                       NO                  GTID binlog      |
|                       |                                    |
|              +------------------+                          |
|              | Stessa major     |--YES--> ONLINE PHYSICAL  |
|              | sorgente/dest?   |         streaming repl   |
|              +------------------+         (PG) / xtrabackup|
|                       |                   + binlog (MySQL) |
|                       NO                                   |
|                       |                                    |
|                  APP-LEVEL                                 |
|                  (refactor schema +                        |
|                   logical replica /                        |
|                   external ETL)                            |
|                                                            |
|------------------------------------------------------------|
|   2. Configurazione VM Proxmox per DB                      |
|      --balloon 0      no swap del buffer pool              |
|      --cpu host       SIMD (CRC32, AES-NI, AVX2)           |
|      --numa 1         allineamento RAM/CPU                 |
|      virtio-scsi-single + iothread per ogni disco          |
|      raw  + cache=none + discard=on                        |
|      WAL/binlog su device fisico separato                  |
|                                                            |
|------------------------------------------------------------|
|   3. Tuning post-migrazione                                |
|      PostgreSQL    shared_buffers = 25% RAM                |
|                    effective_cache_size = 75% RAM          |
|                    random_page_cost = 1.1 (SSD)            |
|                    huge_pages = on (se vm.nr_hugepages OK) |
|      MySQL/MariaDB innodb_buffer_pool_size = 65-70% RAM    |
|                    innodb_flush_method = O_DIRECT          |
|                    innodb_io_capacity = 2000-5000 (SSD)    |
|                                                            |
|------------------------------------------------------------|
|   4. Validazione                                           |
|      pgbench / sysbench   TPS post >= TPS pre              |
|      fio                  IOPS / latency p99 baseline      |
|      pg_checksums --check / mysqlcheck                     |
|      counts/checksums applicativi (es. SUM(amount))        |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Il database e il componente piu stateful per definizione.** A differenza di un app server, ogni byte conta: una transazione persa o un indice corrotto puo manifestarsi giorni dopo il cutover come bug applicativo difficile da diagnosticare. La verifica di integrita non e opzionale.
2. **Il downtime guida la scelta di strategia, non la tua preferenza.** DB da 50 GB con downtime accettabile di 6 ore = offline (semplice, sicuro). DB da 500 GB con SLA "99.99% mensile" = streaming/binlog replication (complesso, ma necessario).
3. **`--balloon 0` e `cache=none` sono obbligatori, non opzionali.** Il database ha un proprio sistema di gestione memoria (buffer pool) e cache (page cache interna). Lasciare attivo il ballooning o `cache=writeback` produce double-caching → pessima localita di accesso, page fault duri, picchi di latenza imprevedibili.
4. **`pg_basebackup -R` e `xtrabackup --copy-back` non sono symmetric.** Il primo e safe online (non ferma il primary, usa replication slot opzionale). Il secondo richiede filesystem snapshot consistency e produce un backup gia "prepared" che deve essere riavviato come istanza nuova. Confonderli costa ore di re-sync.
5. **GTID o Position-based: scegli e non mischiare.** Per MySQL 8.0+ e MariaDB 10.6+, GTID e lo standard. `SOURCE_AUTO_POSITION=1` semplifica il cutover. Per cluster legacy ancora su position-based (`MASTER_LOG_FILE`, `MASTER_LOG_POS`), il porting a GTID si fa *prima* della migrazione, non durante.
6. **Lo storage backend Proxmox decide piu del tuning del DB.** Ceph RBD su HDD = 200 IOPS per disco → un PostgreSQL con `effective_io_concurrency=200` non fara magie. Pre-migration `fio` test sul backend e un check go/no-go.

## Indice
- [Panoramica](#panoramica)
- [Approcci di Migrazione per Database](#approcci-di-migrazione-per-database)
- [Migrazione PostgreSQL: Offline con pg_dumpall](#migrazione-postgresql-offline-con-pg_dumpall)
- [Migrazione PostgreSQL: Online con Streaming Replication](#migrazione-postgresql-online-con-streaming-replication)
- [Tuning PostgreSQL Post-Migrazione](#tuning-postgresql-post-migrazione)
- [Migrazione MySQL/MariaDB: Offline con mysqldump e xtrabackup](#migrazione-mysqlmariadb-offline-con-mysqldump-e-xtrabackup)
- [Migrazione MySQL/MariaDB: Online con Binlog Replication](#migrazione-mysqlmariadb-online-con-binlog-replication)
- [Tuning MySQL/MariaDB Post-Migrazione](#tuning-mysqlmariadb-post-migrazione)
- [Configurazione VM Proxmox Ottimale per Database](#configurazione-vm-proxmox-ottimale-per-database)
- [Baseline di Performance e Validazione](#baseline-di-performance-e-validazione)
- [Pianificazione della Finestra di Downtime](#pianificazione-della-finestra-di-downtime)
- [Procedura di Rollback](#procedura-di-rollback)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La migrazione di server database da VMware a Proxmox VE è tra le operazioni più delicate dell'intero processo di transizione infrastrutturale. I database rappresentano il componente statefu per eccellenza: ogni byte di dati deve essere trasferito integralmente, ogni transazione deve essere preservata, e l'integrità referenziale deve rimanere intatta. Un errore durante la migrazione può risultare in corruzione dati, perdita di transazioni, o inconsistenze che si manifestano solo settimane dopo il cutover.

Esistono tre approcci fondamentali per la migrazione dei database: offline (dump/restore), online (basato su replication), e a livello applicativo. La scelta dipende dalla tolleranza al downtime, dalla dimensione del database, dalla complessità dello schema, e dai requisiti di consistenza. L'approccio offline è il più semplice e sicuro ma richiede un periodo di indisponibilità proporzionale alla dimensione del database. L'approccio online tramite replica riduce il downtime a pochi secondi ma richiede una configurazione più complessa e un monitoraggio costante durante il processo.

Questo documento copre entrambi i motori database più diffusi nell'ecosistema enterprise: PostgreSQL e MySQL/MariaDB. Per ciascuno, vengono descritte le procedure di migrazione offline e online, il tuning specifico per l'ambiente Proxmox/KVM, e le verifiche di integrità post-migrazione. La configurazione ottimale della VM Proxmox per workload database è trattata come sezione dedicata, poiché i requisiti di CPU pinning, memory management e I/O sono significativamente diversi da quelli di un application server generico.

---

## Approcci di Migrazione per Database

### Confronto degli Approcci

| Criterio | Offline (dump/restore) | Online (replication) | Application-level |
|---|---|---|---|
| Downtime | Alto (minuti-ore) | Minimo (secondi) | Variabile |
| Complessità | Bassa | Alta | Media |
| Rischio corruzione | Molto basso | Basso | Medio |
| Dimensioni DB supportate | Qualsiasi (tempo cresce) | Qualsiasi | Dipende dall'app |
| Requisiti rete | Moderati | Elevati (banda continua) | Variabili |
| Rollback | Semplice (DB originale intatto) | Medio (invertire replica) | Complesso |
| Versioni diverse src/dst | Sì (con limitazioni) | Solo stessa major version | Sì |

### Diagramma Decisionale

```
                    ┌─────────────────────┐
                    │ Downtime accettabile │
                    │    > 30 minuti?      │
                    └─────────┬───────────┘
                         ┌────┴────┐
                         │         │
                        Sì        No
                         │         │
                         ▼         ▼
                   ┌──────────┐  ┌─────────────────┐
                   │ Offline  │  │ DB size < 100GB? │
                   │ dump/    │  └────────┬────────┘
                   │ restore  │      ┌────┴────┐
                   └──────────┘     Sì        No
                                    │         │
                                    ▼         ▼
                              ┌──────────┐ ┌──────────────┐
                              │ Online   │ │ Online       │
                              │ logical  │ │ streaming/   │
                              │ replica  │ │ physical     │
                              └──────────┘ │ replica      │
                                           └──────────────┘
```

### Approccio Application-Level

In alcuni scenari, la migrazione può essere gestita a livello applicativo. Questo è appropriato quando l'applicazione ha un meccanismo proprio di export/import dei dati, o quando si approfitta della migrazione per effettuare un refactoring dello schema. Esempi includono: applicazioni con un layer di abstraction del database che supporta la migrazione nativa, sistemi di ETL che possono ridirigere il flusso dati, e microservizi con database isolati di piccole dimensioni dove il re-seeding da un'API è più semplice della migrazione del database.

---

## Migrazione PostgreSQL: Offline con pg_dumpall

### Preparazione Pre-Migrazione

```bash
# Sul server PostgreSQL VMware: raccogliere informazioni
psql -U postgres -c "SELECT version();"
psql -U postgres -c "SELECT pg_database_size(datname), datname FROM pg_database ORDER BY 1 DESC;"
psql -U postgres -c "SELECT count(*) FROM pg_stat_replication;"

# Documentare la configurazione corrente
cat /etc/postgresql/*/main/postgresql.conf | grep -v '^#' | grep -v '^$'
cat /etc/postgresql/*/main/pg_hba.conf | grep -v '^#' | grep -v '^$'

# Verificare le estensioni installate
psql -U postgres -c "SELECT extname, extversion FROM pg_extension ORDER BY 1;"
```

### Dump Completo con pg_dumpall

```bash
# Dump di tutti i database, ruoli, tablespace
pg_dumpall -U postgres --clean --if-exists --verbose > /backup/pg_dumpall_$(date +%Y%m%d_%H%M%S).sql

# Per database molto grandi, usare formato custom con compressione (per singolo DB)
pg_dump -U postgres -Fc -Z 6 --verbose -d mydb > /backup/mydb_$(date +%Y%m%d).dump

# Dump separato dei ruoli e dei tablespace (non inclusi in pg_dump singolo)
pg_dumpall -U postgres --roles-only > /backup/roles.sql
pg_dumpall -U postgres --tablespaces-only > /backup/tablespaces.sql
```

### Stima del Tempo di Dump e Restore

La durata del dump è proporzionale alla dimensione del database e alla velocità I/O:

```bash
# Stimare la dimensione totale
psql -U postgres -c "SELECT pg_size_pretty(sum(pg_database_size(datname))) AS total_size FROM pg_database;"

# Regola empirica:
# - Dump: ~50-100 MB/s su disco locale SSD
# - Restore: ~20-50 MB/s (dipende dagli indici e vincoli)
# - DB da 100 GB: dump ~20 min, restore ~40-80 min
```

### Restore sul Server Proxmox

```bash
# Sul nuovo server PostgreSQL (Proxmox VM), preparare l'istanza
sudo apt install postgresql-15  # o la versione appropriata

# Restore completo
psql -U postgres -f /backup/pg_dumpall_20260412.sql 2>&1 | tee /var/log/pg_restore.log

# Per formato custom (singolo database)
pg_restore -U postgres -d mydb --verbose --clean --if-exists /backup/mydb_20260412.dump

# Restore parallelo (significativamente più veloce)
pg_restore -U postgres -d mydb --verbose --clean --jobs=4 /backup/mydb_20260412.dump
```

### Verifica Integrità Post-Restore

```bash
# Conteggio righe per tabella (confrontare con sorgente)
psql -U postgres -d mydb -c "
SELECT schemaname, relname, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;"

# Verificare vincoli di integrità
psql -U postgres -d mydb -c "
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE contype = 'f'
ORDER BY conrelid::regclass::text;"

# Verificare che gli indici siano validi
psql -U postgres -d mydb -c "
SELECT indexrelid::regclass, indisvalid
FROM pg_index
WHERE NOT indisvalid;"

# Aggiornare le statistiche
psql -U postgres -d mydb -c "ANALYZE VERBOSE;"
```

---

## Migrazione PostgreSQL: Online con Streaming Replication

L'approccio con streaming replication riduce il downtime a pochi secondi. Il server Proxmox viene configurato come standby replica del server VMware, e al momento del cutover i ruoli vengono invertiti.

### Architettura

```
┌─────────────────────┐     WAL streaming      ┌─────────────────────┐
│  PostgreSQL Primary  │ ───────────────────▶   │ PostgreSQL Standby  │
│   (VMware VM)        │     porta 5432         │   (Proxmox VM)      │
│                      │                        │                      │
│  IP: 10.0.1.10       │                        │  IP: 10.0.1.20       │
└─────────────────────┘                        └─────────────────────┘
         │                                              │
         │         Al cutover:                          │
         │         1. Promote standby                   │
         │         2. Reindirizzare applicazioni        │
         │         3. Aggiornare DNS/VIP                │
         ▼                                              ▼
   [Diventa standby                              [Diventa primary
    o viene spento]                               con IP 10.0.1.10]
```

### Configurazione del Primary (VMware)

```bash
# postgresql.conf sul primary VMware
wal_level = replica
max_wal_senders = 5
wal_keep_size = '2GB'     # PostgreSQL 13+; per versioni precedenti: wal_keep_segments = 128
synchronous_commit = on
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'

# pg_hba.conf: permettere la connessione dal server Proxmox
# TYPE  DATABASE  USER         ADDRESS          METHOD
host    replication replicator  10.0.1.20/32     scram-sha-256
```

```bash
# Creare l'utente di replica
psql -U postgres -c "CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'strong_password_here';"

# Ricaricare la configurazione
psql -U postgres -c "SELECT pg_reload_conf();"
```

### Configurazione dello Standby (Proxmox)

```bash
# Arrestare PostgreSQL sul server Proxmox
sudo systemctl stop postgresql

# Base backup dal primary
pg_basebackup -h 10.0.1.10 -U replicator -D /var/lib/postgresql/15/main \
  --wal-method=stream --checkpoint=fast --progress --verbose -R

# Il flag -R crea automaticamente standby.signal e configura primary_conninfo
# Verificare:
cat /var/lib/postgresql/15/main/postgresql.auto.conf
# Deve contenere:
# primary_conninfo = 'host=10.0.1.10 port=5432 user=replicator password=...'

# Avviare PostgreSQL in modalità standby
sudo systemctl start postgresql

# Verificare lo stato della replica
psql -U postgres -c "SELECT * FROM pg_stat_wal_receiver;"
```

### Monitoraggio della Replica

```bash
# Sul primary: verificare le connessioni di replica
psql -U postgres -c "
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       (sent_lsn - replay_lsn) AS replication_lag
FROM pg_stat_replication;"

# Sullo standby: verificare il ritardo
psql -U postgres -c "
SELECT now() - pg_last_xact_replay_timestamp() AS replication_delay;"
```

### Procedura di Cutover

```bash
# 1. Bloccare le scritture sul primary (o fermare le applicazioni)
psql -U postgres -c "SELECT pg_switch_wal();"  -- forza il flush del WAL corrente

# 2. Attendere che lo standby sia completamente sincronizzato
# Sullo standby:
psql -U postgres -c "
SELECT pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() AS synced;"
# Deve restituire true

# 3. Promuovere lo standby a primary
sudo -u postgres pg_ctl promote -D /var/lib/postgresql/15/main
# Oppure:
psql -U postgres -c "SELECT pg_promote();"

# 4. Verificare che lo standby sia diventato primary
psql -U postgres -c "SELECT pg_is_in_recovery();"
# Deve restituire false

# 5. Aggiornare le applicazioni per puntare al nuovo server
# (aggiornare connection string, DNS, o VIP)

# 6. Verificare la connettività e le scritture
psql -U postgres -d mydb -c "CREATE TABLE migration_test (id serial, ts timestamp default now()); INSERT INTO migration_test DEFAULT VALUES; SELECT * FROM migration_test; DROP TABLE migration_test;"
```

### pgBouncer per Connection Pooling

Per minimizzare l'impatto del cambio di indirizzo del database sulle applicazioni, pgBouncer può fungere da proxy:

```ini
; /etc/pgbouncer/pgbouncer.ini
[databases]
mydb = host=10.0.1.10 port=5432 dbname=mydb

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 25
```

Al momento del cutover, basta aggiornare l'indirizzo host in pgBouncer e ricaricare la configurazione:

```bash
# Aggiornare l'host nel file di configurazione
sed -i 's/host=10.0.1.10/host=10.0.1.20/' /etc/pgbouncer/pgbouncer.ini

# Ricaricare senza interrompere le connessioni attive
pgbouncer -R /etc/pgbouncer/pgbouncer.ini
# Oppure:
psql -p 6432 -U pgbouncer pgbouncer -c "RELOAD;"
```

---

## Tuning PostgreSQL Post-Migrazione

La configurazione di PostgreSQL deve essere adattata alle risorse della nuova VM Proxmox. I parametri critici dipendono dalla quantità di RAM e dal tipo di storage.

### Parametri Fondamentali

```ini
# postgresql.conf — Esempio per VM con 32 GB RAM, SSD/NVMe

# Memoria
shared_buffers = '8GB'                # 25% della RAM totale
effective_cache_size = '24GB'         # 75% della RAM totale
work_mem = '64MB'                     # Attenzione: moltiplicato per connessioni x sort
maintenance_work_mem = '2GB'          # Per VACUUM, CREATE INDEX
huge_pages = try                      # Usare huge pages se disponibili

# WAL e Checkpoint
wal_buffers = '64MB'
checkpoint_completion_target = 0.9
min_wal_size = '1GB'
max_wal_size = '4GB'

# Planner
random_page_cost = 1.1               # Per SSD (default 4.0 è per HDD)
effective_io_concurrency = 200        # Per SSD (default 1 è per HDD)

# Parallelismo
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

# Connessioni
max_connections = 200                 # Meglio usare pgBouncer e tenere basso
```

### Huge Pages su Proxmox per PostgreSQL

```bash
# Sul nodo Proxmox: calcolare il numero di huge pages necessarie
# shared_buffers = 8GB = 8192 MB; huge page = 2 MB
# 8192 / 2 = 4096 huge pages (+ margine del 5%)

# In /etc/sysctl.conf:
vm.nr_hugepages = 4300

sysctl -p

# Verificare
grep -i huge /proc/meminfo

# In postgresql.conf:
huge_pages = on
```

---

## Migrazione MySQL/MariaDB: Offline con mysqldump e xtrabackup

### mysqldump: Metodo Classico

```bash
# Dump completo di tutti i database
mysqldump -u root -p --all-databases --single-transaction --routines \
  --triggers --events --flush-logs --master-data=2 --verbose \
  > /backup/full_dump_$(date +%Y%m%d).sql

# Per database specifici con compressione
mysqldump -u root -p --databases mydb --single-transaction --routines \
  --triggers | gzip > /backup/mydb_$(date +%Y%m%d).sql.gz

# Nota: --single-transaction garantisce consistenza per InnoDB senza lock globale
# Nota: --master-data=2 include la posizione del binlog (utile per replica)
```

### Percona XtraBackup: Hot Backup Fisico

Per database di grandi dimensioni, `xtrabackup` è significativamente più veloce di `mysqldump` perché copia i file fisici del database:

```bash
# Installare xtrabackup sul server VMware
apt install percona-xtrabackup-80  # per MySQL 8.0

# Backup completo
xtrabackup --backup --user=root --password=secret \
  --target-dir=/backup/xtrabackup_full

# Preparare il backup (apply log)
xtrabackup --prepare --target-dir=/backup/xtrabackup_full

# Trasferire al server Proxmox
rsync -avzP /backup/xtrabackup_full/ proxmox-db:/backup/xtrabackup_full/

# Sul server Proxmox: arrestare MySQL e ripristinare
systemctl stop mysql
rm -rf /var/lib/mysql/*
xtrabackup --copy-back --target-dir=/backup/xtrabackup_full
chown -R mysql:mysql /var/lib/mysql
systemctl start mysql
```

### Restore da mysqldump

```bash
# Sul server Proxmox
mysql -u root -p < /backup/full_dump_20260412.sql

# Per dump compressi
zcat /backup/mydb_20260412.sql.gz | mysql -u root -p mydb

# Verificare
mysql -u root -p -e "SHOW DATABASES;"
mysql -u root -p -e "SELECT COUNT(*) FROM mydb.important_table;"
```

---

## Migrazione MySQL/MariaDB: Online con Binlog Replication

### Configurazione del Primary (VMware)

```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf sul server VMware
[mysqld]
server-id = 1
log_bin = /var/log/mysql/mysql-bin
binlog_format = ROW
binlog_row_image = full
expire_logs_days = 7
max_binlog_size = 500M
gtid_mode = ON
enforce_gtid_consistency = ON
```

```sql
-- Creare l'utente di replica
CREATE USER 'replicator'@'10.0.1.20' IDENTIFIED BY 'strong_password';
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'replicator'@'10.0.1.20';
FLUSH PRIVILEGES;

-- Verificare lo stato del binlog
SHOW MASTER STATUS;
```

### Configurazione della Replica (Proxmox)

```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf sul server Proxmox
[mysqld]
server-id = 2
relay_log = /var/log/mysql/relay-bin
read_only = ON
super_read_only = ON
gtid_mode = ON
enforce_gtid_consistency = ON
```

```bash
# Dump iniziale dal primary con informazioni GTID
mysqldump -u root -p --all-databases --single-transaction \
  --set-gtid-purged=ON --routines --triggers > /backup/initial_dump.sql

# Restore sul server Proxmox
mysql -u root -p < /backup/initial_dump.sql
```

```sql
-- Configurare la replica con GTID
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='10.0.1.10',
  SOURCE_USER='replicator',
  SOURCE_PASSWORD='strong_password',
  SOURCE_AUTO_POSITION=1;

START REPLICA;

-- Verificare lo stato
SHOW REPLICA STATUS\G
-- Verificare: Slave_IO_Running: Yes, Slave_SQL_Running: Yes, Seconds_Behind_Master: 0
```

### Cutover

```sql
-- 1. Fermare le applicazioni o mettere il primary in read-only
SET GLOBAL read_only = ON;
SET GLOBAL super_read_only = ON;

-- 2. Attendere che la replica sia sincronizzata
-- Sulla replica: Seconds_Behind_Master deve essere 0
SHOW REPLICA STATUS\G

-- 3. Fermare la replica
STOP REPLICA;
RESET REPLICA ALL;

-- 4. Rimuovere il read_only sulla nuova primary
SET GLOBAL read_only = OFF;
SET GLOBAL super_read_only = OFF;

-- 5. Aggiornare le applicazioni per puntare al nuovo server
```

---

## Tuning MySQL/MariaDB Post-Migrazione

```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf — Esempio per VM con 32 GB RAM, SSD/NVMe

[mysqld]
# InnoDB Buffer Pool
innodb_buffer_pool_size = 22G          # 65-70% della RAM totale
innodb_buffer_pool_instances = 8       # 1 per ogni GB di buffer pool (max 64)

# InnoDB I/O
innodb_io_capacity = 2000             # SSD: 2000-5000; HDD: 200-400
innodb_io_capacity_max = 4000
innodb_read_io_threads = 8
innodb_write_io_threads = 8
innodb_flush_method = O_DIRECT        # Evita double buffering con OS cache

# InnoDB Log
innodb_log_file_size = 1G             # Più grande = meno checkpoint, più recovery time
innodb_log_buffer_size = 64M
innodb_flush_log_at_trx_commit = 1    # ACID compliant (2 per più performance, meno safety)

# Connessioni e Thread
max_connections = 200
thread_cache_size = 32
table_open_cache = 4096
table_definition_cache = 2048

# Query Cache (disabilitato in MySQL 8.0+, opzionale in MariaDB)
# query_cache_type = 0

# Temp tables
tmp_table_size = 256M
max_heap_table_size = 256M

# Sort e Join
sort_buffer_size = 4M
join_buffer_size = 4M
read_rnd_buffer_size = 4M
```

---

## Configurazione VM Proxmox Ottimale per Database

I server database hanno requisiti specifici che differiscono significativamente da una VM generica. La configurazione deve massimizzare le prestazioni I/O e minimizzare la latenza.

### Creazione della VM

```bash
qm create 300 \
  --name DB-SERVER \
  --memory 32768 \
  --balloon 0 \
  --cores 8 \
  --sockets 1 \
  --cpu host \
  --numa 1 \
  --net0 virtio,bridge=vmbr0 \
  --ostype l26 \
  --scsihw virtio-scsi-single \
  --agent enabled=1
```

Punti critici:

- **`--balloon 0`**: Disabilitare il memory ballooning. Il database gestisce la propria memoria (buffer pool) e il ballooning causerebbe swap e degrado delle prestazioni.
- **`--cpu host`**: Passthrough completo delle istruzioni CPU, necessario per le ottimizzazioni SIMD usate dai database moderni.
- **`--numa 1`**: NUMA awareness per allineare memoria e CPU dello stesso nodo NUMA.

### Formato Disco e Backend Storage

```bash
# Disco OS su storage standard
qm set 300 --scsi0 local-lvm:32,iothread=1,discard=on

# Disco dati database: formato RAW su LVM per massime prestazioni
qm set 300 --scsi1 nvme-lvm:200,iothread=1,cache=none,discard=on

# Disco WAL/binlog: separare fisicamente su un altro device
qm set 300 --scsi2 nvme-lvm:50,iothread=1,cache=none,discard=on
```

La scelta del formato raw e della cache `none` è fondamentale per i database:

| Impostazione | Valore | Motivazione |
|---|---|---|
| Formato | raw | Nessun overhead di traduzione, IOPS diretti |
| Cache | none | Il database ha il proprio buffer; double caching è dannoso |
| iothread | 1 | Thread I/O dedicato per disco |
| discard | on | TRIM/unmap per thin provisioning |

### CPU Pinning

```bash
# Pinnare i vCPU a core fisici specifici per evitare migrazione tra core
# Proxmox non supporta CPU pinning nativo nella GUI;
# usare taskset o cgroup manualmente:

# Identificare il PID del processo QEMU
VMID=300
PID=$(cat /run/qemu-server/${VMID}.pid)

# Pinnare a core 0-7
taskset -apc 0-7 $PID

# Persistente: creare un hookscript
cat > /var/lib/vz/snippets/db-cpupin.pl << 'EOF'
#!/usr/bin/perl
use strict;
my $vmid = shift;
my $phase = shift;
if ($phase eq 'post-start') {
    my $pid = `cat /run/qemu-server/$vmid.pid`;
    chomp $pid;
    system("taskset -apc 0-7 $pid");
}
EOF
chmod +x /var/lib/vz/snippets/db-cpupin.pl
qm set 300 --hookscript local:snippets/db-cpupin.pl
```

---

## Baseline di Performance e Validazione

### Pre-Migrazione: Raccogliere Metriche su VMware

```bash
# PostgreSQL: query di benchmark
pgbench -i -s 100 mydb
pgbench -c 10 -j 4 -T 300 mydb > /tmp/pgbench_vmware.txt

# MySQL: sysbench
sysbench oltp_read_write --db-driver=mysql --mysql-host=127.0.0.1 \
  --mysql-user=root --mysql-password=secret --mysql-db=sbtest \
  --tables=10 --table-size=1000000 prepare

sysbench oltp_read_write --db-driver=mysql --mysql-host=127.0.0.1 \
  --mysql-user=root --mysql-password=secret --mysql-db=sbtest \
  --tables=10 --table-size=1000000 --threads=8 --time=300 run \
  > /tmp/sysbench_vmware.txt

# I/O puro: fio
fio --name=db_workload --ioengine=libaio --direct=1 --bs=8k \
  --iodepth=32 --rw=randrw --rwmixread=70 --size=10G \
  --numjobs=4 --time_based --runtime=300 --group_reporting \
  --filename=/var/lib/postgresql/fio_test \
  > /tmp/fio_vmware.txt
```

### Post-Migrazione: Stessi Test su Proxmox

Eseguire esattamente gli stessi benchmark sulla VM Proxmox e confrontare i risultati. Le metriche chiave sono:

- **Transactions per second (TPS)**: deve essere >= del valore VMware
- **Latenza media e p99**: deve essere <= del valore VMware
- **IOPS random read/write**: confrontare con baseline
- **Throughput sequenziale**: confrontare con baseline

```bash
# Confronto rapido dei risultati
diff /tmp/pgbench_vmware.txt /tmp/pgbench_proxmox.txt
diff /tmp/fio_vmware.txt /tmp/fio_proxmox.txt
```

Una degradazione superiore al 10% richiede investigazione e tuning aggiuntivo.

### Validazione dell'Integrità dei Dati

```bash
# PostgreSQL: verificare checksum (se abilitati)
pg_checksums --check -D /var/lib/postgresql/15/main

# PostgreSQL: verificare conteggi e checksum applicativi
psql -U postgres -d mydb -c "
SELECT
  (SELECT count(*) FROM orders) AS orders_count,
  (SELECT count(*) FROM customers) AS customers_count,
  (SELECT sum(amount) FROM orders) AS orders_total;"

# MySQL: CHECK TABLE per ogni tabella
mysqlcheck -u root -p --all-databases --check

# MySQL: confrontare checksum
mysql -u root -p -e "CHECKSUM TABLE mydb.orders, mydb.customers;"
```

---

## Pianificazione della Finestra di Downtime

### Template di Piano di Migrazione

```
MIGRAZIONE DATABASE: [nome-db]
Data: [data] Ora inizio: [ora] Finestra: [durata]

PRE-MIGRAZIONE (T-1h)
[ ] Notifica agli stakeholder inviata
[ ] Backup completo verificato
[ ] Server Proxmox pronto e testato
[ ] Replica sincronizzata (se online)
[ ] Script di rollback pronti e testati

CUTOVER (T=0)
[ ] T+0:00  Fermare le applicazioni / mettere in manutenzione
[ ] T+0:05  Verificare che tutte le connessioni siano chiuse
[ ] T+0:10  Dump finale o promozione replica
[ ] T+0:15  Verificare integrità dati
[ ] T+0:20  Aggiornare connection string nelle applicazioni
[ ] T+0:25  Avviare le applicazioni
[ ] T+0:30  Test funzionale completo

POST-MIGRAZIONE (T+1h a T+24h)
[ ] Monitorare performance
[ ] Verificare log per errori
[ ] Confrontare metriche con baseline
[ ] Confermare backup funzionanti sul nuovo server

ROLLBACK (se necessario, entro T+30m)
[ ] Fermare le applicazioni
[ ] Reindirizzare al server VMware originale
[ ] Avviare le applicazioni
[ ] Investigare causa del fallimento
```

---

## Procedura di Rollback

### Rollback per Migrazione Offline

Il rollback è semplice: il server VMware originale non è stato modificato. Basta reindirizzare le applicazioni al server originale.

```bash
# 1. Fermare le applicazioni
# 2. Se ci sono state scritture sul nuovo server che devono essere preservate:
pg_dumpall -U postgres -h proxmox-db > /backup/proxmox_changes.sql
# 3. Riavviare il server VMware originale (se spento)
# 4. Aggiornare connection string per puntare al server VMware
# 5. Avviare le applicazioni
```

### Rollback per Migrazione Online (Replication)

```bash
# 1. Fermare le applicazioni
# 2. Sul server Proxmox (ora primary): abilitare read_only

# PostgreSQL:
psql -U postgres -c "ALTER SYSTEM SET default_transaction_read_only = on;"
psql -U postgres -c "SELECT pg_reload_conf();"

# MySQL:
mysql -u root -p -e "SET GLOBAL read_only = ON; SET GLOBAL super_read_only = ON;"

# 3. Configurare il server VMware come nuova replica del Proxmox
# 4. Sincronizzare
# 5. Promuovere il server VMware
# 6. Aggiornare connection string
# 7. Avviare le applicazioni
```

---

## Best Practices

- **Eseguire sempre benchmark pre e post migrazione** utilizzando gli stessi strumenti e parametri per un confronto valido
- **Separare fisicamente i dischi** per dati, WAL/binlog, e temp su storage backend diversi quando possibile
- **Usare formato raw** per i dischi dati del database, mai qcow2 in produzione per workload I/O intensive
- **Disabilitare il memory ballooning** per tutte le VM database — il database gestisce la propria memoria
- **Impostare cache=none** per i dischi dati — il database ha il proprio sistema di caching (buffer pool), e il double caching degrada le prestazioni
- **Utilizzare VirtIO SCSI con iothread** per ogni disco, con il controller `virtio-scsi-single`
- **Non migrare mai un database senza un piano di rollback testato** — il rollback deve essere eseguibile in meno di 15 minuti
- **Preferire l'approccio online (replication)** per database superiori a 50 GB o con requisiti di downtime inferiore a 30 minuti
- **Verificare l'integrità dei dati** confrontando conteggi righe, checksum applicativi, e risultati di query note prima e dopo la migrazione
- **Configurare il monitoraggio** (Prometheus + Grafana con pg_exporter o mysqld_exporter) prima del cutover, non dopo
- **Mantenere il server VMware operativo** per almeno 7 giorni dopo il cutover come opzione di rollback
- **Documentare ogni parametro di tuning** modificato e la ragione della modifica

---

## Troubleshooting

### Problema: Prestazioni I/O Inferiori su Proxmox Rispetto a VMware

**Sintomi**: Le query sono più lente, il TPS è inferiore al baseline VMware, `iostat` mostra latenza elevata o IOPS ridotti.

**Causa**: Configurazione dello storage non ottimale: uso di qcow2 anziché raw, cache mode errata (writeback/writethrough invece di none), mancanza di iothread, o backend storage Proxmox con prestazioni inferiori al datastore VMware.

**Soluzione**: Verificare la configurazione del disco con `qm config <VMID>`. Convertire a raw se necessario (`qemu-img convert`). Impostare `cache=none,iothread=1`. Verificare le prestazioni dello storage sottostante con `fio` direttamente sul nodo Proxmox. Se il backend è Ceph, assicurarsi che gli OSD siano su SSD e che la regola CRUSH sia corretta.

**Prevenzione**: Eseguire benchmark fio sullo storage Proxmox prima della migrazione per validare che le prestazioni siano adeguate.

---

### Problema: Connessioni al Database Rifiutate Dopo il Cutover

**Sintomi**: Le applicazioni ricevono errori "Connection refused" o "No route to host" quando tentano di connettersi al database sul nuovo server Proxmox.

**Causa**: Il database è in ascolto solo su localhost, il firewall blocca la porta del database, l'indirizzo IP del nuovo server è diverso e le applicazioni non sono state aggiornate, o pg_hba.conf/bind-address non permette connessioni dall'esterno.

**Soluzione**: Verificare `listen_addresses` in postgresql.conf (deve essere `'*'` o l'IP specifico) o `bind-address` in mysqld.cnf. Verificare `pg_hba.conf` per le regole di accesso. Controllare il firewall (`iptables -L -n` o `ufw status`). Verificare che le applicazioni puntino all'indirizzo corretto.

**Prevenzione**: Testare la connettività da un client esterno prima del cutover. Preparare i file di configurazione in anticipo.

---

### Problema: Replication Lag Crescente Durante la Migrazione Online

**Sintomi**: Il valore `Seconds_Behind_Master` (MySQL) o il ritardo di replay (PostgreSQL) continua a crescere anziché diminuire, rendendo impossibile il cutover.

**Causa**: La banda di rete tra VMware e Proxmox è insufficiente per il volume di WAL/binlog generato. Scritture intensive sul primary durante la sincronizzazione iniziale. La replica non ha risorse sufficienti (CPU, I/O) per tenere il passo.

**Soluzione**: Ridurre il carico di scrittura sul primary durante la sincronizzazione. Aumentare la banda di rete (dedicare un'interfaccia alla replica). Ottimizzare la configurazione della replica per il replay più veloce. Per PostgreSQL, aumentare `max_parallel_workers` sulla replica. Per MySQL, abilitare il parallel replication (`slave_parallel_workers`).

**Prevenzione**: Stimare il throughput WAL/binlog medio e di picco prima di iniziare la replica. Assicurarsi che la banda di rete sia almeno 2x il throughput di picco.

---

### Problema: Corruzione Dati Rilevata Dopo la Migrazione

**Sintomi**: Query restituiscono errori inaspettati, conteggi righe non corrispondono, o checksum delle tabelle differiscono tra sorgente e destinazione.

**Causa**: Errore durante la conversione del disco VMDK, dump/restore incompleto (connessione interrotta), o il database non era in stato consistente al momento del dump (mancanza di `--single-transaction` per mysqldump).

**Soluzione**: Non utilizzare il database corrotto in produzione. Eseguire un nuovo dump dal server VMware originale (che non è stato modificato). Verificare l'integrità del dump prima del restore. Per PostgreSQL, usare `pg_checksums --check`. Per MySQL, eseguire `CHECK TABLE` su tutte le tabelle.

**Prevenzione**: Usare sempre `--single-transaction` con mysqldump. Verificare checksum MD5/SHA256 dei file di dump dopo il trasferimento. Eseguire la verifica di integrità immediatamente dopo il restore, prima di reindirizzare le applicazioni.

---

### Problema: Out of Memory Dopo la Migrazione con Buffer Pool Invariato

**Sintomi**: Il processo del database viene terminato dall'OOM killer del kernel. I log mostrano "Out of memory" o "Cannot allocate memory". Il sistema diventa irresponsivo.

**Causa**: La VM Proxmox ha meno memoria rispetto alla VM VMware, o il memory ballooning è attivo e sta riducendo la memoria disponibile, ma il buffer pool del database è configurato per la dimensione originale.

**Soluzione**: Ridurre `shared_buffers` (PostgreSQL) o `innodb_buffer_pool_size` (MySQL) in proporzione alla RAM disponibile. Verificare con `free -h` la memoria effettivamente disponibile. Disabilitare il ballooning: `qm set <VMID> --balloon 0`.

**Prevenzione**: Verificare la RAM allocata alla VM Proxmox prima della migrazione. Adattare i parametri di memoria del database. Disabilitare sempre il ballooning per le VM database.

---

### Problema: Errore "Timeline Does Not Match" nella Replica PostgreSQL

**Sintomi**: La streaming replication si interrompe con errore "requested WAL segment has already been removed" o "timeline does not match". Lo standby non riesce a riconnettersi al primary.

**Causa**: Il primary ha esaurito lo spazio per i WAL segment (parametro `wal_keep_size` troppo basso) e ha rimosso i segmenti prima che lo standby potesse leggerli. Oppure, un failover/promote accidentale ha causato un cambio di timeline.

**Soluzione**: Se il gap WAL è piccolo, aumentare `wal_keep_size` e usare `pg_rewind` per risincronizzare lo standby. Se il gap è grande, eseguire un nuovo `pg_basebackup` per ricostruire lo standby da zero. Configurare l'archivio WAL (`archive_command`) come backup aggiuntivo.

**Prevenzione**: Impostare `wal_keep_size` a un valore sufficientemente grande (almeno 2-4 GB). Configurare `archive_mode = on` con un archivio WAL accessibile dallo standby. Monitorare il replication lag con alerting.

---

## Riferimenti

- [PostgreSQL Documentation — pg_dumpall](https://www.postgresql.org/docs/current/app-pg-dumpall.html)
- [PostgreSQL Documentation — Streaming Replication](https://www.postgresql.org/docs/current/warm-standby.html)
- [PostgreSQL Documentation — Server Configuration](https://www.postgresql.org/docs/current/runtime-config.html)
- [PostgreSQL Wiki — Tuning Your PostgreSQL Server](https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server)
- [MySQL Documentation — mysqldump](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html)
- [MySQL Documentation — Replication](https://dev.mysql.com/doc/refman/8.0/en/replication.html)
- [Percona XtraBackup Documentation](https://docs.percona.com/percona-xtrabackup/latest/)
- [pgBouncer Documentation](https://www.pgbouncer.org/)
- [Proxmox VE Wiki — Performance Tweaks](https://pve.proxmox.com/wiki/Performance_Tweaks)
- [sysbench Documentation](https://github.com/akopytov/sysbench)
- [fio Documentation](https://fio.readthedocs.io/en/latest/)

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — `wal_keep_size` (PostgreSQL ≥ 13) sostituisce `wal_keep_segments`.** Su PostgreSQL 13+ il parametro storico `wal_keep_segments` (numero di file WAL da 16 MB) e stato sostituito da `wal_keep_size` espresso in MB/GB. Una configurazione tipica per uno standby a banda buona e `wal_keep_size = 2GB`; per replica geografica con possibile interruzione di rete prolungata, `wal_keep_size = 8GB` riduce il rischio di gap. La soluzione architetturale piu robusta resta pero il **replication slot fisico**: `SELECT pg_create_physical_replication_slot('standby_proxmox')` sul primary e `primary_slot_name = 'standby_proxmox'` nello standby. Lo slot trattiene WAL finche non sono stati replicati, eliminando il rischio di "requested WAL segment has already been removed". Attenzione al rovescio: se lo standby e offline a lungo, il primary accumula WAL fino a riempire `pg_wal/`. Mitigazione: `max_slot_wal_keep_size = 16GB` (≥ 13) per drop automatico oltre soglia. Fonte: [PostgreSQL 17 — Replication](https://www.postgresql.org/docs/17/runtime-config-replication.html), retrieved 2026-04-27.

> **Approfondimento — `pg_basebackup` con `--wal-method=stream` e `--checkpoint=fast` evita gap.** Il flag `--wal-method=stream` apre una seconda connessione al primary che streamma i WAL generati durante il base backup. Senza questo, un backup di > 1h su DB write-heavy puo finire con WAL gia rotati prima della fine, e `pg_basebackup` fallisce. `--checkpoint=fast` forza un checkpoint immediato sul primary invece di aspettare il prossimo naturale, riducendo il tempo di start del backup ma aumentando l'I/O di picco sul primary. Per produzione, schedulare il backup in finestra di basso carico. Per una replica live durante migrazione, accettare il picco e lanciare comunque. Fonte: [PostgreSQL 17 — pg_basebackup](https://www.postgresql.org/docs/17/app-pgbasebackup.html), retrieved 2026-04-27.

> **Errore comune — `mysqldump` senza `--single-transaction` su tabelle InnoDB.** Sintomo: dump apparentemente riuscito, restore senza errori, ma alcune righe in tabelle write-heavy sono inconsistenti rispetto al primary (per esempio, una row ordine senza la sua row order_item). Causa: senza `--single-transaction`, `mysqldump` fa un dump tabella per tabella senza snapshot ACID, e una transazione attiva durante il dump puo essere "vista a meta": righe inserite nella tabella A ma non ancora in B. Soluzione: **usare sempre `--single-transaction`** per dump InnoDB; per dump che includono tabelle MyISAM/Aria (no MVCC), aggiungere `--master-data=2 --flush-logs --lock-tables=false` e accettare un breve lock globale via `FLUSH TABLES WITH READ LOCK`. Fonte: [MySQL 8.4 — mysqldump options](https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html#option_mysqldump_single-transaction), retrieved 2026-04-27.

> **Errore comune — `cache=writeback` su disco DB perche "va piu veloce".** Sintomo: TPS migliora del 30-40% in benchmark; al primo crash del nodo Proxmox, il DB non parte piu, errore "WAL is corrupt" o "InnoDB: Database page corruption". Causa: `cache=writeback` lascia che il guest creda di aver fsync-ato dati che in realta sono ancora in page cache QEMU; un crash perde quei dati con conseguenze fatali sul WAL/redolog. Soluzione: `cache=none` e l'unica modalita safe per database in produzione su Proxmox; `cache=writethrough` e accettabile ma piu lenta di `none`. Per recovery: ripartire da PITR / backup verificato; non c'e fix in-place per pagine corrotte di un DB transazionale. Fonte: [Proxmox VE Wiki — Performance Tweaks (Cache modes)](https://pve.proxmox.com/wiki/Performance_Tweaks), retrieved 2026-04-27.

> **Caso reale — pgBouncer `pool_mode = transaction` e prepared statement non server-side.** Un cluster PostgreSQL con pgBouncer in `transaction` mode ha registrato errori "prepared statement does not exist" dopo la migrazione, sotto carico. Causa: in `transaction` mode pgBouncer multiplexa connessioni client su un pool di backend; un `PREPARE` su una connessione backend non e visibile alla successiva. Soluzione: o passare a `pool_mode = session` (perdendo il beneficio di multiplexing), oppure abilitare il prepared-statement caching client-side della libreria DB driver (es. `pgjdbc` con `prepareThreshold=0`). Per pgBouncer 1.21+, la feature `track_extra_parameters` e i prepared statement transparent multiplexing (release 1.22) risolvono nativamente molti casi d'uso. Verifica versione: `pgbouncer -V`. Fonte: [pgBouncer — pool_mode](https://www.pgbouncer.org/config.html#pool_mode) + [pgBouncer 1.22 release notes](https://github.com/pgbouncer/pgbouncer/releases/tag/pgbouncer_1_22_0), retrieved 2026-04-27.

> **Caso reale — `O_DIRECT` su filesystem ZFS in Proxmox: DB silently slow.** Un DB MySQL 8.0 migrato su VM Proxmox con storage ZFS ha mostrato TPS 60% inferiori al baseline VMware. Investigazione: `innodb_flush_method = O_DIRECT` e di fatto un no-op su ZFS, che non supporta direct I/O nel modo in cui gli altri filesystem lo fanno. Risultato: il DB pensa di bypassare la cache OS, ma ZFS lo cachea comunque (ARC), causando double caching e contention sulla memoria. Soluzione: per DB su ZFS impostare `innodb_flush_method = fsync` (o `O_DSYNC`), e configurare ARC con `zfs_arc_max` esplicito per non competere con `innodb_buffer_pool_size`. Riferimento: ZFS on Linux non implementa `O_DIRECT` per default; opzione modulo `zfs_dio_enabled` solo da OpenZFS 2.2+. Fonte: [OpenZFS Issue #224 — O_DIRECT support](https://github.com/openzfs/zfs/issues/224) + [Percona blog — ZFS for MySQL](https://www.percona.com/blog/), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — scegli la strategia.** Per ognuno dei seguenti scenari, indica strategia (offline / online streaming-binlog / app-level) e giustifica in 3-4 righe. (a) PostgreSQL 14, 80 GB, e-commerce con 200 TPS picco, downtime massimo 4h notturni; (b) MySQL 5.7, 1.5 TB, SaaS multi-tenant, downtime massimo 5 min; (c) MariaDB 10.5 → 11.4 con cambio di major version durante la migrazione; (d) PostgreSQL 11 (EOL) con schema OLAP (1 TB, scritture nightly), si vuole il refactor di alcune tabelle. *Risposte attese:* (a) offline con `pg_dumpall` + restore parallelo (downtime ~2-3h con DB SSD); (b) online binlog GTID (1.5 TB e oltre soglia logical, ma stessa major → physical xtrabackup + binlog catch-up); (c) cambio major version → app-level o `pg_dump` logico (xtrabackup non supporta cambio major); (d) refactor + EOL → app-level con `pg_dump --schema-only` per portare schema + ETL custom per i dati storici.

2. **Lab — streaming replication PostgreSQL end-to-end.** Su due VM Linux (puo bastare Proxmox + 2 LXC o 2 VM piccole), simulare la migrazione: (a) installare PostgreSQL 16 su `db-old` (simula VMware), creare un DB di test con `pgbench -i -s 50` (~750 MB di dati); (b) avviare un loop `pgbench -c 4 -j 2 -T 600 -P 5` per generare carico; (c) configurare `db-new` come standby con `pg_basebackup -h db-old -U replicator -D /var/lib/postgresql/16/main --wal-method=stream -R --slot=standby_test`; (d) verificare lag con `SELECT now() - pg_last_xact_replay_timestamp();`; (e) eseguire cutover con `pg_promote()`; (f) misurare l'effective downtime (tempo tra ultimo SUCCESS su `db-old` e primo SUCCESS su `db-new`). Atteso: < 5s su rete LAN.

3. **Scenario — degrado post-migrazione 25% sul TPS.** Hai migrato un MySQL 8.0 da VMware a Proxmox. Pre-migrazione: `sysbench oltp_read_write` mostrava 1200 TPS, latenza p99 = 18ms. Post-migrazione: 900 TPS, p99 = 35ms. Stesso `innodb_buffer_pool_size = 22G`, stessa CPU count. Argomenta in 12-15 righe come investigare e ipotizza le 3 cause piu probabili. *Risposta attesa:* (1) verificare `cache=` del disco con `qm config` — se non e `none`, fix; (2) verificare `iothread=1` per il disco scsi del DB; (3) `iostat -xdz 1` durante run sysbench per vedere `await` e `%util`; (4) verificare se `--cpu host` e attivo (mancanza di SIMD costa 10-15% sui DB moderni); (5) verificare `numactl --hardware` dentro la VM (se NUMA non passato, scheduler kernel sub-ottimale); (6) verificare lo storage backend (Ceph RBD HDD vs LVM-thin SSD: differenza 4-10x sul random IOPS); (7) `SHOW ENGINE INNODB STATUS\G` per vedere se ci sono lock contention o checkpoint storms.

4. **Stretch — orchestratore migration-as-code.** Scrivere un Ansible playbook (o Python script con `pyVmomi` + `proxmoxer`) che esegue end-to-end: (1) snapshot della VM PostgreSQL su VMware; (2) export OVA via `ovftool`; (3) import su Proxmox via `qm importovf`; (4) modifica config disco a `cache=none,iothread=1`; (5) avvia VM su Proxmox; (6) configura come replica streaming del primary VMware originale (che resta acceso); (7) attende sync (`replication_delay < 1s`); (8) fa promote dello standby; (9) emit report con metriche pre/post. Bonus: rollback automatico se la sync non converge entro 30 min.

5. **Stretch — DR drill PostgreSQL post-migrazione.** Simulare uno scenario di disaster recovery dopo la migrazione: corrompere intenzionalmente una tabella (`UPDATE orders SET total = NULL WHERE id < 1000`), verificare che il backup PBS pre-cutover (riferito al DB pre-migrazione) sia restorable, eseguire un Point-in-Time Recovery a 1 minuto prima della corruzione, validare integrita. Misurare RTO ed RPO effettivi.

## Auto-valutazione

1. Quale parametro PostgreSQL sostituisce `wal_keep_segments` da v13 in poi e quale unita usa?
2. Cosa fa `mysqldump --master-data=2` e perche e utile per setup di replica?
3. Spiega perche `cache=none` e l'unica modalita safe per dischi DB su Proxmox.
4. `--single-transaction` di `mysqldump`: che lock prende e per quali storage engine funziona?
5. `pg_basebackup --wal-method=stream` vs `--wal-method=fetch`: differenza pratica per backup di lunga durata.
6. Su PostgreSQL standby, quale query restituisce `true` solo quando lo standby ha applicato tutti i WAL ricevuti?
7. Cosa fa `SOURCE_AUTO_POSITION=1` in MySQL 8.0+ e perche evita di specificare `MASTER_LOG_FILE`/`MASTER_LOG_POS`?
8. Perche `--balloon 0` e obbligatorio per VM database e cosa succede se si lascia il default?
9. Differenza fra streaming replication (PostgreSQL) e binlog replication (MySQL) in termini di formato di replicazione (fisico vs logico).
10. Quale tool fornisce hot backup fisico per MySQL/MariaDB e quale e la sua differenza chiave rispetto a `mysqldump`?
11. `huge_pages = on` per PostgreSQL: come si calcola il numero di huge pages necessarie e dove si configura nel kernel?
12. Cosa indica `Seconds_Behind_Master = NULL` su uno standby MySQL e quali sono le 3 cause piu comuni?

## Letture primarie consigliate

- PostgreSQL 17 — Streaming Replication. https://www.postgresql.org/docs/17/warm-standby.html (retrieved 2026-04-27).
- PostgreSQL 17 — `wal_keep_size` and replication slots. https://www.postgresql.org/docs/17/runtime-config-replication.html (retrieved 2026-04-27).
- PostgreSQL 17 — `pg_basebackup`. https://www.postgresql.org/docs/17/app-pgbasebackup.html (retrieved 2026-04-27).
- PostgreSQL 17 — `pg_dumpall` / `pg_dump` / `pg_restore`. https://www.postgresql.org/docs/17/backup-dump.html (retrieved 2026-04-27).
- PostgreSQL Wiki — Tuning Your PostgreSQL Server. https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server (retrieved 2026-04-27).
- MySQL 8.4 — `mysqldump`. https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html (retrieved 2026-04-27).
- MySQL 8.4 — Replication with GTIDs. https://dev.mysql.com/doc/refman/8.4/en/replication-gtids.html (retrieved 2026-04-27).
- MySQL 8.4 — `CHANGE REPLICATION SOURCE TO`. https://dev.mysql.com/doc/refman/8.4/en/change-replication-source-to.html (retrieved 2026-04-27).
- MariaDB Knowledge Base — Replication Overview. https://mariadb.com/kb/en/standard-replication/ (retrieved 2026-04-27).
- Percona XtraBackup 8.4 — User Guide. https://docs.percona.com/percona-xtrabackup/8.4/index.html (retrieved 2026-04-27).
- pgBouncer — Configuration Reference. https://www.pgbouncer.org/config.html (retrieved 2026-04-27).
- Proxmox VE Wiki — Performance Tweaks. https://pve.proxmox.com/wiki/Performance_Tweaks (retrieved 2026-04-27).
- Proxmox VE Administrator Guide — QEMU/KVM Virtual Machines (cache modes, iothread). https://pve.proxmox.com/pve-docs/pve-admin-guide.html (retrieved 2026-04-27).
- Linux kernel — Transparent / Explicit Hugepages. https://www.kernel.org/doc/html/latest/admin-guide/mm/hugetlbpage.html (retrieved 2026-04-27).
- sysbench — Benchmark Tool. https://github.com/akopytov/sysbench (retrieved 2026-04-27).
- fio — Flexible I/O Tester Documentation. https://fio.readthedocs.io/en/latest/ (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 09.1 — `migrazione-applicazioni-stateful.md`: concetti di drain, parallel run, rolling che il DB cutover applica.
- Modulo 06.3 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/live-migration-minimo-downtime.md`: tecniche di live cutover applicabili anche al DB tier.
- Modulo 06.2 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/migrazione-con-virt-v2v.md`: alternativa physical-to-virtual quando il DB e su VM monolitica e non si vuole un re-deploy.
- Modulo 07.1 — `../07-MIGRAZIONE-NETWORKING/ip-planning-dns-dhcp-firewall.md`: pianificazione DNS/VIP per il cutover del DB endpoint.
- Modulo 08.1 — `../08-MIGRAZIONE-STORAGE/conversione-vmdk-qcow2-raw.md`: conversione dei dischi DB a raw, motivazione cache=none, sparse vs preallocated.
- Modulo 08.4 — `../08-MIGRAZIONE-STORAGE/validazione-performance-storage.md`: come validare il backend Proxmox con `fio` prima del DB cutover.
- Modulo 09.3 — `migrazione-high-io-workloads.md`: pattern I/O del DB all'interno della categoria piu ampia di workload high-IOPS.
- Modulo 11.x — `../11-BACKUP-E-RIPRISTINO-PROXMOX/proxmox-backup-server-configurazione.md`: PBS come secondo livello di backup oltre al backup logico DB.
- Modulo 12.1 — `../12-SICUREZZA-E-COMPLIANCE/certificati-ssl-tls-proxmox.md`: TLS per le connessioni di replica (`sslmode=verify-full` PG, `REQUIRE SSL` MySQL).

## Glossario locale

| Termine | Definizione |
|---|---|
| **`pg_dumpall`** | Tool PostgreSQL per dump logico di tutti i database, ruoli e tablespace di un cluster. |
| **`pg_dump -Fc`** | Dump in formato custom binario, comprimibile, restorable in parallelo via `pg_restore --jobs=N`. |
| **`pg_basebackup`** | Tool per copia fisica completa del data directory di un primary, base per streaming replication. |
| **WAL (Write-Ahead Log)** | Log delle modifiche PostgreSQL prima dell'applicazione ai data file; base per replica e PITR. |
| **`wal_keep_size`** | Quantita minima di WAL trattenuta sul primary per gli standby (≥ PG13; sostituisce `wal_keep_segments`). |
| **Replication slot** | Meccanismo PostgreSQL per garantire che il primary trattenga WAL finche un consumer specifico li ha ricevuti. |
| **Streaming replication** | Replica fisica PostgreSQL: il primary invia WAL byte-per-byte allo standby. |
| **`pg_promote()`** | Funzione PostgreSQL che promuove uno standby a primary in-place. |
| **`pg_rewind`** | Tool per risincronizzare un primary divergente come standby di un altro primary, evitando re-baseback up. |
| **`pg_checksums`** | Tool PostgreSQL per abilitare/verificare checksum di pagina sui data file. |
| **pgBouncer** | Connection pooler PostgreSQL; modalita session/transaction/statement con trade-off diversi. |
| **`mysqldump --single-transaction`** | Apre una transazione con snapshot consistente per tabelle InnoDB; nessun lock globale. |
| **`mysqldump --master-data=2`** | Aggiunge come commento la posizione binlog corrente, utile per setup di replica. |
| **Binlog (binary log)** | Log MySQL/MariaDB delle modifiche; base per replication e PITR. |
| **GTID (Global Transaction Identifier)** | Identificatore globale univoco di transazione MySQL 8.0+/MariaDB 10.0+; semplifica failover e topology change. |
| **`enforce_gtid_consistency`** | Vincolo MySQL che impedisce statement non GTID-safe (es. CREATE TABLE...SELECT in alcuni casi). |
| **`SOURCE_AUTO_POSITION=1`** | Setting MySQL replica che usa GTID per posizionarsi automaticamente nel binlog; non serve `MASTER_LOG_FILE`. |
| **xtrabackup** | Tool Percona/MariaDB per hot backup fisico di MySQL InnoDB; molto piu veloce di `mysqldump` su DB grandi. |
| **`xtrabackup --prepare`** | Step post-backup che applica i log uncommitted; prepara il backup per il restore. |
| **`xtrabackup --copy-back`** | Copia il backup preparato nella datadir di destinazione. |
| **`innodb_buffer_pool_size`** | Dimensione del buffer pool InnoDB; cache principale del DB MySQL. |
| **`innodb_flush_method`** | Modalita di sync/flush dei file InnoDB (`O_DIRECT`, `fsync`, `O_DSYNC`); critico per ZFS. |
| **`innodb_io_capacity`** | Stima IOPS del backend storage; usato per scheduling background flush. |
| **`shared_buffers`** | Cache pagine PostgreSQL; tipicamente 25% RAM su DB dedicato. |
| **`effective_cache_size`** | Stima totale di RAM disponibile per cache (DB + OS); usato dal planner. |
| **`huge_pages`** | Pagine di memoria ampie (2 MB) che riducono pressure sul TLB; configurate via `vm.nr_hugepages`. |
| **`cache=none`** | Modalita disco QEMU/KVM senza host page cache; obbligatoria per DB. |
| **`iothread=1`** | Thread I/O dedicato per disco virtuale; riduce contention sui multi-disk DB VM. |
| **NUMA (Non-Uniform Memory Access)** | Architettura multi-socket dove l'accesso a RAM ha latenza diversa in base al socket. |
| **`--numa 1` (Proxmox)** | Espone topologia NUMA al guest; necessario per DB su host multi-socket. |
| **`--cpu host`** | Passa istruzioni CPU complete (incluse SIMD: AVX2, AES-NI, CRC32); ~10-15% di prestazioni sui DB. |
| **TPS (Transactions Per Second)** | Metrica primaria per benchmark DB OLTP. |
| **PITR (Point-In-Time Recovery)** | Restore di un DB a un istante specifico, combinando base backup + replay WAL/binlog. |
| **RTO (Recovery Time Objective)** | Tempo massimo accettabile per il ripristino di un servizio. |
| **RPO (Recovery Point Objective)** | Quantita massima di dati (espressa in tempo) che si puo permettere di perdere. |
