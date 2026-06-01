# MySQL/MariaDB Replication e Cluster

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: draft

## Skip list
- [ ] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Replication Types
2. Async Replication Setup
3. GTID-Based Replication
4. Replication Topology
5. Delay and Lag Monitoring
6. Failover e Switchover
7. MariaDB Replication
8. Replication Troubleshooting

---

## 1. Replication Types

### 1.1 Async vs Semi-Sync

MySQL supporta diversi modi di replicare i dati, ognuno con trade-off specifici tra performance, durabilità e semplicità di gestione.

**Async Replication**:
- Default mode in MySQL
- Master non aspetta conferma dagli slave prima di considerare la transazione committata
- Più veloce perché non blocca in attesa di acknowledgment
- Potenziale lag tra master e slave
- Non garantisce che dati raggiungano slave al momento del commit

```sql
-- Verificare modalità corrente
SHOW VARIABLES LIKE 'rpl_semi_sync%';

-- Verificare se semi-sync è abilitato
SHOW STATUS LIKE 'Rpl_semi_sync_master_status';
SHOW STATUS LIKE 'Rpl_semi_sync_slave_status';
```

**Semi-Sync Replication**:
- Master aspetta che almeno uno slave confermi ricezione del transaction record prima di completare il commit
- Bilanciamento tra performance e sicurezza
- Ritardo aggiuntivo minimo (tipicamente millisecondi)
- Garantisce che almeno una replica abbia i dati prima di ritornare al client

```sql
-- Abilitare sul master
INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';

-- Abilitare su ogni slave
INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';

-- Verificare installazione
SHOW PLUGINS;

-- Configurare timeout (default: 10 secondi)
SET GLOBAL rpl_semi_sync_master_timeout = 10000;

-- Il master rimarrà bloccato se nessuno slave conferma entro 10 secondi
-- Then falls back to async
```

**Performance Impact**:
```sql
-- Monitorare le performance di semi-sync
SHOW GLOBAL STATUS LIKE 'rpl_semi_sync%';

-- Metriche importanti:
-- Rpl_semi_sync_master_no_tx: transazioni senza risposta
-- Rpl_semi_sync_master_yes_tx: transazioni confermate
-- Rpl_semi_sync_master_avg_response_time: tempo medio risposta
```

**Trade-off Analysis**:
```
                    | Async        | Semi-Sync
--------------------|--------------|------------
Latency             | Minima       | Bassa
Durability          | Solo master  | 1+ replica
Failure handling    | Più complessa| Più semplice
Network dependency  | Nessuno      | Alta
```

### 1.2 Statement vs Row vs Mixed

La scelta del formato del binary log ha implicazioni significative per la replica.

**Statement-Based Replication (SBR)**:
- Replica SQL statements così come sono stati eseguiti sul master
- Vantaggi: meno dati trasferiti nel binlog, mantiene la logica applicativa
- Svantaggi: funzioni non-deterministiche (RAND(), NOW(), UUID()) causano dati diversi
- Non sicuro per stored functions, triggers con tempo-dependent logic

```sql
-- Default in MySQL 5.7 e precedenti
binlog_format = STATEMENT

-- Problemi con SBR:
-- Query 1: INSERT INTO t VALUES (NOW());  -- Master inserisce 2024-01-15
-- Slave: INSERT INTO t VALUES (NOW());     -- Slave inserisce 2024-01-15 00:00:01
-- Risultato: dati diversi!
```

**Row-Based Replication (RBR)**:
- Replica le righe modificate (prima e dopo)
- Vantaggi: deterministico al 100%, sicuro con qualsiasi funzione
- Svantaggi: più dati nel binlog per UPDATE che modificano molte righe
- Più largo da memorizzare, ma più sicuro

```sql
-- MySQL 8.0+ default
binlog_format = ROW

-- Opzioni per ridurre size:
binlog_row_image = FULL    -- tutte le colonne (default)
binlog_row_image = MINIMAL -- solo PK + colonne modificate
binlog_row_image = NOBLOB  -- solo colonne necessarie

-- Esempio:
-- UPDATE t SET col = 'new' WHERE status = 'old'
-- Con FULL: writes entire row
-- Con MINIMAL: writes PK + 'new' + 'old'
```

**Mixed**:
- MySQL decide automaticamente tra SBR e RBR
- Usa SBR per statement sicuri, RBR per quelli non-sicuri
- Buon compromesso per la maggior parte dei casi

```sql
binlog_format = MIXED

-- MySQL usa SBR per:
-- - SELECT, INSERT senza funzioni non-deterministiche
-- - UPDATE con WHERE deterministico

-- MySQL usa RBR per:
-- - INSERT ... ON DUPLICATE KEY UPDATE
-- - INSERT ... SELECT
-- - UPDATE con funzioni non-deterministiche
-- - CREATE ... SELECT
```

**Recommendation**: Usare ROW per production workloads dove la consistenza è critica. MIXED è ok per transizioni da versioni vecchie.

### 1.3 Replication Channels

MySQL 8.0 supporta multi-source replication attraverso canali multipli.

```sql
-- Creare canale aggiuntivo
CHANGE MASTER TO
  MASTER_HOST = 'source2.example.com',
  MASTER_USER = 'repl_user',
  MASTER_PASSWORD = 'password',
  MASTER_LOG_FILE = 'mysql-bin.000001',
  MASTER_LOG_POS = 4
FOR CHANNEL 'source_2';

-- Gestire canali
SHOW SLAVE STATUS FOR CHANNEL 'source_2';
START SLAVE FOR CHANNEL 'source_2';
STOP SLAVE FOR CHANNEL 'source_2';

-- Reset canale
RESET SLAVE ALL FOR CHANNEL 'source_2';

-- Vedere tutti i canali
SHOW SLAVE HOSTS;
```

**Use Cases**:
- Aggregare dati da multiple sorgenti
- Parallel replication da differenti master
- Disaster recovery con multiple primary

### 1.2 Statement vs Row vs Mixed

**Statement-Based Replication (SBR)**:
- Replica SQL statements
- Vantaggi: meno dati trasferiti, logiche complesse replicate
- Svantaggi: non-deterministic functions possono causare problemi

```sql
-- Default in MySQL 5.7 e anteriori
binlog_format = STATEMENT
```

**Row-Based Replication (RBR)**:
- Replica le righe modificate
- Vantaggi: deterministico, safe con funzioni non-deterministiche
- Svantaggi: più dati nel binlog per UPDATEs che modificano molte righe

```sql
-- MySQL 8.0+ default
binlog_format = ROW

-- Abilitare per sola lettura
binlog_format = ROW
binlog_row_image = MINIMAL  -- solo le colonne necessarie
```

**Mixed**:
- Usa SBR per la maggioranza, RBR dove necessario
- Buon compromesso

```sql
binlog_format = MIXED
```

### 1.3 Replication Channels

MySQL 8.0 supporta multi-source replication:

```sql
-- Creare canale aggiuntivo
CHANGE MASTER TO
  MASTER_HOST = 'source2.example.com',
  MASTER_USER = 'repl_user',
  MASTER_PASSWORD = 'password',
  MASTER_LOG_FILE = 'mysql-bin.000001',
  MASTER_LOG_POS = 4
FOR CHANNEL 'source_2';

-- Gestire canali
SHOW SLAVE STATUS FOR CHANNEL 'source_2';
START SLAVE FOR CHANNEL 'source_2';
STOP SLAVE FOR CHANNEL 'source_2';
```

---

## 2. Async Replication Setup

### 2.1 Master Configuration

Configurare il master per la replica:

```ini
# my.cnf [mysqld]
server-id = 1
log_bin = /var/log/mysql/mysql-bin
binlog_format = ROW
binlog_row_image = FULL
sync_binlog = 1
max_binlog_size = 1G
expire_logs_days = 7

# GTID-based (MySQL 5.6+)
gtid_mode = ON
enforce_gtid_consistency = ON
```

**Parametri chiave**:
- `server-id`: deve essere unico per ogni server
- `log_bin`: abilita binary log
- `sync_binlog`: forza fsync su ogni commit (importante per durability)

```sql
-- Verificare master status
SHOW MASTER STATUS;
-- Output: File, Position, Binlog_Do_DB, Expire_Logs_User, Gtid_Set
```

### 2.2 Create Replication User

```sql
-- Creare utente dedicato alla replica
CREATE USER 'repl_user'@'%' IDENTIFIED BY 'strong_password';
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'%';
FLUSH PRIVILEGES;
```

### 2.3 Slave Configuration

```ini
# my.cnf [mysqld] su slave
server-id = 2
relay_log = /var/log/mysql/mysql-relay-bin
read_only = ON
log_replica_updates = ON  # se slave è anche master
skip_slave_start = OFF

# GTID
gtid_mode = ON
enforce_gtid_consistency = ON
```

### 2.4 Start Replication

**Per position-based**:
```sql
CHANGE MASTER TO
  MASTER_HOST = 'master.example.com',
  MASTER_USER = 'repl_user',
  MASTER_PASSWORD = 'strong_password',
  MASTER_LOG_FILE = 'mysql-bin.000001',
  MASTER_LOG_POS = 4;

START SLAVE;
SHOW SLAVE STATUS\G
```

**Per GTID**:
```sql
-- Automatico con GTID
CHANGE MASTER TO
  MASTER_HOST = 'master.example.com',
  MASTER_USER = 'repl_user',
  MASTER_PASSWORD = 'strong_password',
  MASTER_AUTO_POSITION = 1;

START SLAVE;
```

---

## 3. GTID-Based Replication

### 3.1 GTID Concepts

**GTID (Global Transaction ID)**:
- Identificatore unico per ogni transazione
- Format: `server_uuid:transaction_number`
- Più facile da gestire rispetto a coordinate file:position

**Vantaggi GTID**:
- Failover semplificato
- Non serve sapere coordinate esatte per riconnettersi
- Automatic position tracking

### 3.2 Enable GTID

```ini
# my.cnf su tutti i server
gtid_mode = ON
enforce_gtid_consistency = ON
```

**Requistes**:
- Nessuna transazione non-transazionale (ALTER TABLE, CREATE TABLE LIKE)
- Tutte le tabelle InnoDB
- No `CREATE TEMPORARY TABLE` o `DROP TEMPORARY TABLE` in transazioni

### 3.3 GTID Auto-Positioning

```sql
-- Abilitare auto-position
CHANGE MASTER TO
  MASTER_AUTO_POSITION = 1;
```

In caso di problemi di rete temporanei, il slave ritenta automaticamente dal punto corretto.

### 3.4 Monitor GTID

```sql
-- Vedere GTID eseguiti
SHOW MASTER STATUS\G
SHOW SLAVE STATUS\G
-- Output include: Retrieved_Gtid_Set, Executed_Gtid_Set

-- GTID di una specifica sessione
SET GTID_NEXT = 'AUTOMATIC';
BEGIN;
COMMIT;
-- GTID assegnato automaticamente
```

---

## 4. Replication Topology

### 4.1 Master-Slave Basic

La topologia Master-Slave è la più semplice e comunemente usata per:
- Read scaling (leggere dagli slave)
- Backup (backup dallo slave senza impattare master)
- Disaster recovery (slave in data center separato)

```
[Master] → [Slave 1] → [Slave 2]
   │           │
   └───────────┴──→ [Slave 3]
```

**Setup primo slave**:
```ini
# my.cnf [mysqld]
server-id = 2
relay_log = /var/log/mysql/mysql-relay-bin
read_only = ON
log_replica_updates = ON
super_read_only = ON  # MySQL 8.0+
```

**Setup second slave**:
```ini
# my.cnf su slave2
server-id = 3
relay_log = /var/log/mysql/mysql-relay-bin
read_only = ON
super_read_only = ON
```

**Clonare uno slave**:
Esistono multiple metodologie per creare un nuovo slave:

**Opzione 1: mysqldump con --master-data**
```bash
# Full dump con master coordinates
mysqldump -h master -u root -p \
  --all-databases \
  --master-data \
  --single-transaction \
  --routines \
  --triggers \
  > backup.sql

# Opzioni aggiuntive utili:
# --add-drop-database
# --extended-insert (più veloce restore)
# --compress (meno bandwidth)
```

**Opzione 2: Clone Plugin (MySQL 8.0.17+)**
```sql
-- Sul donor (master o slave)
INSTALL PLUGIN clone SONAME 'mysql_clone.so';

-- Configurare allowlist
SET GLOBAL clone_valid_donor_list = 'admin:password@donor_host:3306';

-- Sul recipient
INSTALL PLUGIN clone SONAME 'mysql_clone.so';

-- Eseguire clone
CLONE INSTANCE FROM 'admin'@'donor_host':3306
IDENTIFIED BY 'password';
```

**Opzione 3: Xtrabackup (Percona)**
```bash
# Backup dal master
xtrabackup --backup \
  --user=root --password=pass \
  --target-dir=/backup/full

# Prepare
xtrabackup --prepare --target-dir=/backup/full

# Restore su slave
xtrabackup --copy-back --target-dir=/backup/full
```

**Opzione 4: rsync (per grandi database)**
```bash
# 1. Stop MySQL sul source
systemctl stop mysql

# 2. Copy data directory
rsync -avz /var/lib/mysql/ new_slave:/var/lib/mysql/

# 3. Adjust server-id
# 4. Start MySQL
```

### 4.2 Master-Master Active-Passive

Due master dove solo uno è attivo per scritture (active-passive):

```
[Master 1] ←→ [Master 2]
   (active)   (passive)
```

Questa topologia permette:
- Failover veloce (basta promuovere il passive)
- Backup dal passive senza impattare active
- Manutenzione del active senza downtime

**Configurazione per auto-increment**:
```ini
# master1 my.cnf
auto_increment_increment = 2
auto_increment_offset = 1

# master2 my.cnf
auto_increment_increment = 2
auto_increment_offset = 2
```

**Configurare replica su entrambi**:

Sul master1:
```sql
CHANGE MASTER TO
  MASTER_HOST = 'master2.example.com',
  MASTER_USER = 'repl_user',
  MASTER_PASSWORD = 'password',
  MASTER_AUTO_POSITION = 1;

START SLAVE;
```

Sul master2:
```sql
CHANGE MASTER TO
  MASTER_HOST = 'master1.example.com',
  MASTER_USER = 'repl_user',
  MASTER_PASSWORD = 'password',
  MASTER_AUTO_POSITION = 1;

START SLAVE;
```

**Monitoring**:
```sql
-- Verificare che entrambi replichino
SHOW SLAVE STATUS\G;

-- Vedere position
SHOW MASTER STATUS\G;
```

### 4.3 Active-Active (Multi-Master)

Entrambi i master accettano scritture:

```
[Master 1] ←→ [Master 2]
   (write)     (write)
```

**Attenzione**: Conflitti possibili!

```sql
-- ID collision su auto_increment
-- UPDATE sullo stesso record su entrambi i master

-- Soluzioni:
-- 1. Application-level sharding (diverse tabelle/db)
-- 2. Conflict detection (tool come MySQL NDB Cluster)
-- 3. Evitare writes sullo stesso dato
```

**Configurazione**:
```ini
# Su entrambi i master
binlog_format = ROW
auto_increment_increment = 1
auto_increment_offset = 1
log-slave-updates = ON
```

### 4.4 Multi-Source Replication

MySQL 8.0+ supporta replicare da multiple sorgenti:

```sql
-- Creare primo canale
CHANGE MASTER TO
  MASTER_HOST = 'source1.example.com',
  MASTER_USER = 'repl',
  MASTER_PASSWORD = 'pass',
  MASTER_AUTO_POSITION = 1
FOR CHANNEL 'source_1';

-- Creare secondo canale
CHANGE MASTER TO
  MASTER_HOST = 'source2.example.com',
  MASTER_USER = 'repl',
  MASTER_PASSWORD = 'pass',
  MASTER_AUTO_POSITION = 1
FOR CHANNEL 'source_2';

-- Avviare entrambi
START SLAVE FOR CHANNEL 'source_1';
START SLAVE FOR CHANNEL 'source_2';
```

**Gestire conflitti**:

Quando la stessa tabella viene scritta da multiple sorgenti:
```sql
-- Opzione 1: Ignore conflicts
SET GLOBAL slave_exec_mode = IDEMPOTENT;

-- Opzione 2: Different databases
-- Ogni source ha database diverso

-- Opzione 3: Percona Toolkit per conflict resolution
pt-table-checksum h=source1,h=source2 --replicate=checksums.checksums
pt-table-sync --sync-to-master h=source2 --database=mydb
```

### 4.5 Intermediate Master

Topologia gerarchica per distribuire carico:

```
[Master] → [Intermediate Master] → [Leaf Slave]
                       ↓
                [Leaf Slave 2]
```

**Configurazione intermedio**:
```ini
# Intermediate master my.cnf
log_slave_updates = ON
server-id = 2

# Slave my.cnf
server-id = 3
read_only = ON
```

**Vantaggi**:
- Riduce carico di rete sul master
- Distribution layer per geographic distribution

**Svantaggi**:
- Più latency (più hop)
- Più complesso da gestire
- Single point of failure se l'intermedio ha problemi

### 4.3 Multi-Source Replication

MySQL 8.0+ supporta replicare da multiple sorgenti:

```sql
-- Creare primo canale
CHANGE MASTER TO
  MASTER_HOST = 'source1.example.com',
  MASTER_USER = 'repl',
  MASTER_PASSWORD = 'pass',
  MASTER_AUTO_POSITION = 1
FOR CHANNEL 'source_1';

-- Creare secondo canale
CHANGE MASTER TO
  MASTER_HOST = 'source2.example.com',
  MASTER_USER = 'repl',
  MASTER_PASSWORD = 'pass',
  MASTER_AUTO_POSITION = 1
FOR CHANNEL 'source_2';

START SLAVE FOR CHANNEL 'source_1';
START SLAVE FOR CHANNEL 'source_2';
```

**Gestire conflitti**:
- Diverse strategie per gestire conflitti:
  - Different databases
  - Same database, different tables
  - Conflict detection and resolution

### 4.4 Intermediate Master

Topologia gerarchica:

```
[Master] → [Intermediate Master] → [Leaf Slave]
                       ↓
                [Leaf Slave 2]
```

Configurazione intermedio come slave del master e master per gli slave.

```ini
# Intermediate master
log_slave_updates = ON
```

---

## 5. Delay and Lag Monitoring

### 5.1 Check Replication Lag

Il replication lag è la differenza temporale tra quando una transazione viene committata sul master e quando viene applicata sullo slave.

```sql
-- Verificare lag base
SHOW SLAVE STATUS\G
-- Seconds_Behind_Master: secondi di ritardo

-- Note:
-- - 0 = sincronizzato
-- - NULL = replica non attiva
-- - Valori positivi = slave è indietro
```

**Metriche importanti in SHOW SLAVE STATUS**:
```
Slave_IO_Running: Yes
Slave_SQL_Running: Yes
Last_IO_Error: None
Last_SQL_Error: None

Seconds_Behind_Master: 0  <- IMPORTANTE

Read_Master_Log_Pos: 1234567
Relay_Log_Pos: 1234567
Exec_Master_Log_Pos: 1234567

Relay_Log_Space: 1234567
```

**In MariaDB**:
```sql
-- Seconds_Behind_Master può essere -1 in certi casi
-- Usare GTID-based monitoring
SHOW STATUS LIKE 'Slave_received_heartbeats';
SHOW STATUS LIKE 'Slave_heartbeat_period';
```

**Query per monitoraggio dettagliato via GTID**:
```sql
-- Calcolo lag via GTID
SELECT 
  @@server_id AS server_id,
  (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS 
   WHERE VARIABLE_NAME = 'GTID_EXECUTED') AS gtid_executed,
  (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS 
   WHERE VARIABLE_NAME = 'GTID_RETRIEVED') AS gtid_retrieved;

-- Lag preciso
SELECT 
  (SELECT MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(Executed_Gtid_Set, ',', -1), ':', -1) AS UNSIGNED)) 
   FROM information_schema.GLOBAL_STATUS WHERE Variable_name = 'GTID_EXECUTED') -
  (SELECT MAX(CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(Retrieved_Gtid_Set, ',', -1), ':', -1) AS UNSIGNED)) 
   FROM information_schema.GLOBAL_STATUS WHERE Variable_name = 'GTID_RETRIEVED') AS lag;
```

### 5.2 Monitorare in Production

**Performance Schema** (MySQL 8.0+):
```sql
-- Abilitare instrument per replication
UPDATE performance_schema.setup_instruments 
SET ENABLED = 'YES' WHERE NAME LIKE 'stage/sql/Relay log%';

UPDATE performance_schema.setup_instruments 
SET ENABLED = 'YES' WHERE NAME LIKE 'statement/sql/change_master%';

-- Monitorare applicazione eventi
SELECT * FROM performance_schema.replication_applier_status\G;

-- Monitorare worker threads
SELECT * FROM performance_schema.replication_applier_status_by_worker\G;

-- Vedere lag stimato
SELECT 
  SERVICE_TYPE,
  COUNT_STAR,
  SUM_TIMER_WAIT,
  AVG_TIMER_WAIT
FROM performance_schema.events_statements_summary_by_account_by_EVENT_NAME
WHERE EVENT_NAME LIKE '%repl%';
```

**Query per script di monitoring**:
```sql
-- Script completo per health check
SELECT 
  @@server_id AS server_id,
  @@hostname AS hostname,
  (SELECT COUNT(*) FROM mysql.slave_master_info) AS master_info_rows,
  (SELECT COUNT(*) FROM mysql.slave_relay_log_info) AS relay_log_info_rows,
  (SELECT COUNT(*) FROM mysql.slave_worker_info) AS worker_info_rows,
  (SELECT LAST_ERROR_MESSAGE FROM mysql.slave_master_info LIMIT 1) AS last_io_error,
  (SELECT LAST_ERROR_MESSAGE FROM mysql.slave_relay_log_info LIMIT 1) AS last_sql_error;
```

**Nagios/Icinga check plugin**:
```bash
#!/bin/bash
# check_mysql_replication.sh
mysql -u root -p -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master"
LAG=$(mysql -u root -p -N -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master" | cut -d: -f2 | tr -d ' ')

if [ "$LAG" = "NULL" ] || [ "$LAG" -gt 300 ]; then
  echo "CRITICAL: Replication lag is $LAG"
  exit 2
elif [ "$LAG" -gt 60 ]; then
  echo "WARNING: Replication lag is $LAG"
  exit 1
fi
echo "OK: Replication healthy"
exit 0
```

### 5.3 Causes of Lag

**Comuni cause di lag** e come risolverle:

**1. Network lento**:
```sql
-- Monitorare: network throughput, latency
-- Misure:
-- - Check bandwidth tra master e slave
-- - Monitorare latency ping
-- - Considerare compressione (MySQL 8.0.20+)
SET GLOBAL binlog_transaction_dependency_tracking = WRITESET;
```

**2. Large transactions**:
```sql
-- Problema: una transazione da 1GB blocca la replica
-- Soluzioni:
-- - Dividere in transazioni più piccole
-- - Commit più frequenti
-- - Evitare LOAD DATA INFILE di grandi file

-- Best practice:
-- INSERT INTO t VALUES (...), (...), (...);  -- max 1000 rows per statement
-- Commit ogni 1000-5000 rows
```

**3. Slave con risorse limitate**:
```sql
-- Verificare: CPU, disk I/O, memory
SHOW GLOBAL STATUS LIKE 'Cpu%';

-- Monitorare I/O
SHOW GLOBAL STATUS LIKE 'Innodb_data_read%';
SHOW GLOBAL STATUS LIKE 'Innodb_data_written%';

-- Check disk
iostat -x 5
```

**4. Lock contention**:
```sql
-- Identificare queries bloccanti sullo slave
SHOW PROCESSLIST;
-- Cercare "Waiting for table metadata lock"

-- Tipico problema:
-- Transazione sul master con lock lungo
-- Slave aspetta di replicare quella transazione

-- Soluzione: keep transactions short
```

**5. Slow queries sul slave**:
```sql
-- Il slave applica le stesse queries del master
-- Indices mancanti sul master = slow apply sul slave

-- Soluzione:
-- Verificare indici identici su master e slave
SHOW INDEX FROM orders;
SHOW INDEX FROM orders;

-- abilitare slow query log sullo slave per debug
SET GLOBAL slow_query_log = ON;
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow_slave.log';
```

### 5.4 Tune Slave Performance

```ini
# my.cnf slave

# Parallel apply (MySQL 8.0+)
slave_parallel_workers = 4  # numero di thread
slave_parallel_type = LOGICAL_CLOCK  # default
# alternative: DATABASE (per database-based parallelism)

# Batch size
slave_batch_size = 100000

# Preserve commit order
replica_preserve_commit_order = ON

# Memory per eventi
# Se transaction events sono grandi, aumenta
replica_max_allowed_packet = 1G

# Per latenza bassa:
# - SSD per relay logs
# - adequate CPU
# - buffering adeguato
```

**Monitorare parallel replication**:
```sql
-- Vedere worker threads status
SELECT * FROM performance_schema.replication_applier_status_by_worker
LIMIT 10;

-- Verificare se workers sono occupati
SHOW GLOBAL STATUS LIKE 'Slave_parallel%';
-- Slave_parallel_warnings: number of transactions delayed
-- Slave_parallel_commits: number of commits done in parallel
```

**Considerazioni per dimensionamento**:
```ini
# Regola generale:
# 1 thread per 2 core CPU
# Ma non più di 32 (overhead)

# Esempio: 8 core -> 4 threads
slave_parallel_workers = 4

# Per SSD veloci, possono essere di più
# Per HDD, meno thread
```

---

## 6. Failover e Switchover

### 6.1 Manual Failover

**Promuovere slave a master manualmente**:
```sql
-- 1. Sul slave designato
STOP SLAVE;
RESET SLAVE ALL;

-- 2. Configurare applicazioni per nuovo master

-- 3. Se altri slave, riconfigurare
CHANGE MASTER TO
  MASTER_HOST = 'new_master.example.com',
  MASTER_USER = 'repl',
  MASTER_PASSWORD = 'pass',
  MASTER_AUTO_POSITION = 1;

START SLAVE;
```

### 6.2 GTID-Based Automatic Failover

MySQL 8.0.22+ supporta automatic failover con MySQL Shell:

```bash
# Usare MySQL Shell
mysqlsh
dba failover replCluster
```

### 6.3 Switchover (Planned)

Per manutenzione programmata:

```sql
-- 1. Assicurarsi slave è sincronizzato
SHOW SLAVE STATUS\G
-- Seconds_Behind_Master = 0

-- 2. Bloccare scritture sul master
FLUSH TABLES WITH READ LOCK;

-- 3. Verificare slave aggiornato
SHOW SLAVE STATUS\G

-- 4. Su slave
STOP SLAVE;
RESET SLAVE ALL;

-- 5. Promuovere slave
-- Cambiare applicazioni al nuovo master

-- 6. Riconfigurare vecchio master come slave
-- Point to new master
```

### 6.4 Replication Failover Tools

**Orchestrator** (da GitHub):
```bash
# Supporta failover automatico
# Configurazione in orchestrator.conf.json
{
  "RecoveryPeriodBlockSeconds": 3600,
  "RecoveryOnMasterBinlogServerFailure": true,
  "AuditLogging": true
}
```

---

## 7. MariaDB Replication

### 7.1 MariaDB Binary Log

MariaDB ha un formato binlog diverso da MySQL. Mentre mantiene la compatibilità per la replica, ci sono differenze interne.

**Configurazione base**:
```ini
# my.cnf
log_bin = mariadb-bin
binlog_format = ROW

# Opzioni MariaDB specifiche
binlog_checksum = CRC32  # default MariaDB
binlog_row_metadata = FULL  # include metadata per change data capture
```

**Differenze da MySQL**:
- Formato binlog diverso (MariaDB binlog ha struttura specifica)
- GTID non richiede enforce_gtid_consistency (più flessibile)
- Variabili con nomi diversi

**Variabili MariaDB specifiche**:
```sql
-- GTID in MariaDB
SHOW VARIABLES LIKE 'gtid%';

-- MariaDB GTID mode
gtid_domain_id = 1  # different for each server in ring
-- Ogni server ha un domain_id univoco

-- Replication convention
log_slave_updates = ON
```

**Replication con GTID**:
```sql
-- MariaDB: gtid_mode è diverso da MySQL
SET GLOBAL gtid_mode = ON;

-- Non serve enforce_gtid_consistency in MariaDB
-- Più flessibile
```

### 7.2 MariaDB Parallel Replication

MariaDB offre diverse modalità di parallel replication:

**Modalità disponibili**:
- `optimistic`: prova parallelizzazione aggressiva, rollback se conflitti
- `conservative`: solo transazioni che non possono causare conflitti
- `none`: no parallel (default in alcune versioni)

```ini
# Abilitare parallel replication
slave_parallel_threads = 4
slave_parallel_mode = optimistic

# Determinare numero thread
# Regola: 2-4 thread per core
# Considerare: I/O capacity, transaction size

# Verificare performance
SHOW GLOBAL STATUS LIKE 'Slave_parallel%';
-- Slave_parallel_commits: transazioni committate in parallel
-- Slave_parallel_seconds_behind_master: lag ridotto
```

**Transaction-based parallelism**:
```ini
# MariaDB 10.5+
slave_parallel_mode = transaction
# Parallelismo basato su transazioni individuali
# Più semplice, meno conflitti
```

### 7.3 MariaDB Crash-Safe Slave

MariaDB ha migliore supporto per crash-safe replication nativamente.

```ini
# Crash-safe replication
relay_log_recovery = ON
relay_log_purge = ON
```

**Relay log recovery**:
```sql
-- In caso di crash dello slave
-- Il relay log viene ricostruito dal master
-- Necessita connessione al master attiva

-- Verificare recovery settings
SHOW VARIABLES LIKE 'relay_log_recovery';
```

**Crash-safe tables**:
```sql
-- MariaDB supporta crash-safe MyISAM
myisam_recover_options = FORCE

-- Per InnoDB (default)
-- Crash-safe di default
```

### 7.4 MariaDB Special Features

**Binlog rotate**:
```sql
-- Rotate automatico
SET GLOBAL max_binlog_size = 1G;
SET GLOBAL expire_logs_days = 7;

-- Manual rotate
FLUSH LOGS;
```

**MariaDB vs MySQL replication compatibility**:
```ini
# MySQL 8.0 -> MariaDB 10.6
# Potrebbe richiedere: log_slave_updates = ON
# E gtid adjustments
```

### 7.5 MariaDB Replica Plugins

**Sincronous replication (MySQL non ha)**:
```sql
-- MariaDB: Sphinx storage engine per full-text search
-- MariaDB Connect storage engine per ODBC/JDBC

-- Spider storage engine per sharding
-- Permette sharding a livello storage engine
```

---

## 8. Replication Troubleshooting

### 8.1 Common Errors

**Error 1236 - Could not find GTID position**:
```
Error 'Could not find GTID position'
```
Causa: Il master ha fatto log rotate o i binlog sono stati purgati.

```sql
-- Soluzione 1: Trovare la position corretta sul master
SHOW MASTER STATUS;
-- Usare la nuova File e Position 4

-- Soluzione 2: Usare GTID auto-positioning (se GTID abilitato)
STOP SLAVE;
CHANGE MASTER TO MASTER_AUTO_POSITION = 1;
START SLAVE;
```

**Error 1062 - Duplicate entry**:
```
Error: Duplicate entry '123' for key 'PRIMARY'
```
Causa: Race condition o data inconsistente tra master e slave.

```sql
-- Opzione 1: Skip una transazione
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;
-- Attenzione: perdi una transazione!

-- Opzione 2: Configurare per ignorare duplicate
SET GLOBAL slave_exec_mode = IDEMPOTENT;
-- In MariaDB, MySQL 8.0+

-- Opzione 3: Investigare cause
-- Verificare dati sul master e slave
SELECT * FROM table WHERE id = 123;
```

**Error 1050 - Table already exists**:
```
Error: Table 't' doesn't exist
```
Causa: DROP TABLE su master, CREATE TABLE su slave?

```sql
-- Skip l'errore
SET GLOBAL slave_exec_mode = IDEMPOTENT;
-- O skip specifico
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;
```

**Error 1064 - Syntax error in relay log**:
```
Error: Relay log read failure
```
Causa: Corrupted relay log

```sql
-- Reset e ricollegare
STOP SLAVE;
RESET SLAVE;
CHANGE MASTER TO ...;  -- riconfigurare
START SLAVE;
```

### 8.2 Verify Data Consistency

**CheckSUM tables**:
```sql
-- MySQL built-in
CHECKSUM TABLE table_name;

-- Per verificare consistenza tra master e slave:
-- 1. Su master
CHECKSUM TABLE orders EXTENDED;

-- 2. Su slave
CHECKSUM TABLE orders EXTENDED;
-- Confrontare risultati
```

**pt-table-checksum (Percona Toolkit)**:
```bash
# Installare Percona Toolkit
apt install percona-toolkit

# Checksum con replica
pt-table-checksum h=master,u=user,P=3306 \
  --replicate=checksums.checksums \
  --create-replicate-table \
  h=slave

# Verificare differenze
pt-table-sync --print --sync-to-master h=slave --database=mydb
```

**Schema verification**:
```sql
-- Verificare struttura tabelle
SHOW CREATE TABLE table_name;
-- Confrontare master e slave
```

### 8.3 Replication Health Check

**Query completa per health**:
```sql
-- Status generale
SELECT 
  @@server_id AS server_id,
  @@hostname AS hostname,
  (SELECT COUNT(*) FROM mysql.slave_master_info) AS master_info_rows,
  (SELECT COUNT(*) FROM mysql.slave_relay_log_info) AS relay_log_info_rows,
  (SELECT COUNT(*) FROM mysql.slave_worker_info) AS worker_info_rows,
  (SELECT LAST_ERROR_MESSAGE FROM mysql.slave_master_info LIMIT 1) AS last_io_error,
  (SELECT LAST_ERROR_MESSAGE FROM mysql.slave_relay_log_info LIMIT 1) AS last_sql_error,
  (SELECT LAST_ERROR_TIMESTAMP FROM mysql.slave_master_info LIMIT 1) AS last_io_time,
  (SELECT LAST_ERROR_TIMESTAMP FROM mysql.slave_relay_log_info LIMIT 1) AS last_sql_time;
```

**Automatic health monitoring script**:
```bash
#!/bin/bash
# Monitora replication health

while true; do
  # Check IO thread
  IO_STATUS=$(mysql -u root -N -e "SHOW SLAVE STATUS\G" | grep "Slave_IO_Running" | cut -d: -f2 | tr -d ' ')
  SQL_STATUS=$(mysql -u root -N -e "SHOW SLAVE STATUS\G" | grep "Slave_SQL_Running" | cut -d: -f2 | tr -d ' ')
  LAG=$(mysql -u root -N -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master" | cut -d: -f2 | tr -d ' ')
  
  if [ "$IO_STATUS" != "Yes" ] || [ "$SQL_STATUS" != "Yes" ]; then
    echo "ALERT: Replication stopped!"
    # Send alert
  fi
  
  if [ "$LAG" != "NULL" ] && [ "$LAG" -gt 300 ]; then
    echo "ALERT: Replication lag: $LAG seconds"
    # Send alert
  fi
  
  sleep 60
done
```

### 8.4 Network Troubleshooting

**Verificare connettività**:
```bash
# Test network
ping master.example.com
telnet master.example.com 3306

# Throughput test
iperf -c master.example.com -p 3306
```

**Check binlog size**:
```sql
-- Sul master
SHOW MASTER LOGS;
-- Vedere sizes e positions

-- Purging vecchi logs (attenzione!)
PURGE BINARY LOGS BEFORE '2024-01-15 00:00:00';
PURGE BINARY LOGS TO 'mysql-bin.000010';
```

**Verify slave connection**:
```sql
-- Testare credenziali
mysql -h master.example.com -u repl_user -p -e "SELECT 1"

-- Verificare privileges
SHOW GRANTS FOR 'repl_user'@'slave_host';
```

---

## 8. Replication Troubleshooting

### 8.1 Common Errors

**Error 1236**:
```
Error 'Could not find GTID position'
```
Soluzione:
```sql
-- Trovare la position corretta sul master
SHOW MASTER STATUS;

-- O usare GTID auto-positioning
CHANGE MASTER TO MASTER_AUTO_POSITION = 1;
```

**Error 1062** - Duplicate entry:
```sql
-- Skip la transazione
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;

-- O configurare per ignorare errori
SET GLOBAL slave_exec_mode = IDEMPOTENT;
```

**Error 1050** - Table already exists:
```sql
-- Saltare l'errore
SET GLOBAL slave_exec_mode = IDEMPOTENT;
-- O saltare specifici errori
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;
```

### 8.2 Verify Data Consistency

```sql
-- Checksum delle tabelle
CHECKSUM TABLE table_name;

-- pt-table-checksum (Percona Toolkit)
pt-table-checksum h=master,u=user,P=3306 --replicate=checksums.checksums h=slave
```

### 8.3 Replication Health Check

```sql
-- Query completa per health
SELECT 
  @@server_id AS server_id,
  @@hostname AS hostname,
  (SELECT COUNT(*) FROM mysql.slave_master_info) AS master_info_rows,
  (SELECT COUNT(*) FROM mysql.slave_relay_log_info) AS relay_log_info_rows,
  (SELECT COUNT(*) FROM mysql.slave_worker_info) AS worker_info_rows;
```

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*