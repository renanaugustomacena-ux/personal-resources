# Troubleshooting della Replica Database

Il troubleshooting della replica richiede un approccio sistematico: identificare il sintomo, raccogliere i dati diagnostici, isolare la causa, applicare la soluzione, e verificare. Questa sezione cataloga i problemi più frequenti con le procedure di diagnostica e soluzione.

## Metodologia di Diagnostica

```
Sintomo osservato
       │
       ▼
Raccogliere metriche di sistema (IO, CPU, rete)
       │
       ▼
Controllare i log PostgreSQL/MySQL
       │
       ▼
Interrogare le viste di sistema (pg_stat_replication, SHOW REPLICA STATUS)
       │
       ▼
Isolare: problema del primario, della rete, o della replica?
       │
       ▼
Applicare la soluzione appropriata
       │
       ▼
Monitorare per conferma (lag scende? connessione stabile?)
```

## Problemi PostgreSQL

### Problema 1: Replica disconnessa (lag cresce indefinitamente)

**Sintomi:**
- `pg_stat_replication` non mostra la replica
- `pg_stat_activity` non mostra connessioni `walsender`
- Alert di replica disconnessa

```sql
-- Diagnostica: verificare lo stato delle connessioni di replica
SELECT
  pid,
  application_name,
  client_addr,
  state,
  sent_lsn,
  replay_lsn,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes,
  reply_time,
  EXTRACT(EPOCH FROM (NOW() - reply_time)) AS seconds_since_reply
FROM pg_stat_replication;
-- Vuoto = nessuna replica connessa

-- Verificare se ci sono slot di replica in attesa
SELECT slot_name, active, restart_lsn,
  pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS wal_retained
FROM pg_replication_slots;

-- Log del primario
-- /var/log/postgresql/postgresql.log
-- Cercare: "connection reset", "walsender", "authentication failed"
```

**Possibili cause e soluzioni:**

```bash
# Causa 1: Problema di rete tra primario e replica
ping -c 10 replica.example.com
traceroute replica.example.com
# Testare la porta 5432 specificamente
nc -zv replica.example.com 5432

# Causa 2: Il WAL necessario è stato eliminato (replica troppo indietro)
# Sul primario verificare il WAL disponibile:
ls -la /var/lib/postgresql/data/pg_wal/ | head -20
# Se la replica ha un restart_lsn molto indietro e il WAL è stato eliminato,
# la replica deve essere reclonata

# Reclonare la replica:
# Sul nodo replica (dopo aver fermato PostgreSQL):
pg_ctl stop -D /var/lib/postgresql/data

# Eliminare i dati esistenti (backup prima se possibile!)
rm -rf /var/lib/postgresql/data/*

# Reclonare dal primario
pg_basebackup \
  --host=primary.example.com \
  --port=5432 \
  --username=replicator \
  --pgdata=/var/lib/postgresql/data \
  --format=plain \
  --wal-method=stream \
  --checkpoint=fast \
  --progress

# Riconfigurare come standby
cat > /var/lib/postgresql/data/postgresql.auto.conf << 'EOF'
primary_conninfo = 'host=primary.example.com port=5432 user=replicator password=secret'
EOF
touch /var/lib/postgresql/data/standby.signal

pg_ctl start -D /var/lib/postgresql/data

# Causa 3: Autenticazione fallita (pg_hba.conf non aggiornato)
# Log: "FATAL: no pg_hba.conf entry for replication connection"
# Soluzione: aggiungere l'IP della replica a pg_hba.conf e ricaricare
psql -c "SELECT pg_reload_conf();"
```

### Problema 2: Replica in lag costante (non recupera)

**Sintomi:**
- La replica è connessa ma il lag cresce costantemente
- Il primario ha I/O molto alto
- La replica non riesce ad applicare il WAL abbastanza velocemente

```sql
-- Diagnostica: verificare il lag in dettaglio
SELECT
  client_addr,
  write_lag,
  flush_lag,
  replay_lag,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) / 1024 / 1024 AS lag_mb
FROM pg_stat_replication;

-- Sulla replica: verificare il throughput di applicazione WAL
SELECT
  last_apply_lsn,
  last_msg_send_time,
  last_msg_receipt_time,
  latest_end_lsn,
  EXTRACT(EPOCH FROM (last_msg_receipt_time - last_msg_send_time)) AS network_delay_s
FROM pg_stat_wal_receiver;

-- Verificare se ci sono hot_standby_feedback che bloccano il vacuum
SELECT COUNT(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock';
```

```bash
# Possibili cause:

# 1. I/O della replica saturato
iostat -x 1 10  # verificare % utilization del disco
# Soluzione: usare hardware più veloce o ottimizzare le query

# 2. hot_standby_feedback attivo + query lunghe sulla replica
# Le query sulla replica possono bloccare il vacuum del primario
# postgresql.conf della replica:
# hot_standby_feedback = off  # disabilitare se causa problemi
# max_standby_streaming_delay = 30s  # massimo ritardo prima di cancellare la query

# 3. Troppo carico sulla replica (query di lettura pesanti)
# Soluzione: dedicare una replica separata per le query analitiche

# 4. max_wal_size troppo basso causa checkpoint troppo frequenti
# postgresql.conf del primario:
# max_wal_size = 4GB  # aumentare se necessario
```

### Problema 3: Divergenza dopo failover (split-brain)

**Sintomi:**
- Due nodi si credono entrambi primari
- Query scritte su entrambi i nodi, dati divergenti
- pg_wal_lsn_diff mostra posizioni incompatibili

```bash
# Diagnostica: verificare lo stato di entrambi i nodi
psql -h node1 -c "SELECT pg_is_in_recovery(), pg_current_wal_lsn();"
psql -h node2 -c "SELECT pg_is_in_recovery(), pg_current_wal_lsn();"

# Se entrambi restituiscono pg_is_in_recovery = false: SPLIT-BRAIN

# PROCEDURA DI EMERGENZA:
# 1. IMMEDIATAMENTE: bloccare tutte le applicazioni da scrivere su entrambi i nodi
#    Spegnere il bilanciatore di carico, bloccare a livello di rete, ecc.

# 2. Determinare quale nodo ha i dati più recenti o più critici
#    Confrontare le transazioni recenti su entrambi i nodi
psql -h node1 -c "SELECT MAX(updated_at) FROM tabella_critica;"
psql -h node2 -c "SELECT MAX(updated_at) FROM tabella_critica;"

# 3. Scegliere il nodo "vincitore" e reclonare l'altro come standby
# Opzione A: usare pg_rewind (se disponibile)
pg_rewind \
  --target-pgdata=/var/lib/postgresql/data \
  --source-server="host=nodo-vincitore port=5432 user=postgres" \
  --progress

# Opzione B: reclonare completamente (perde le transazioni del nodo "perdente")
pg_basebackup -h nodo-vincitore -U replicator -D /var/lib/postgresql/data --wal-method=stream

# 4. Analizzare le transazioni perse e valutare se recuperarle manualmente
```

### Problema 4: Errore `WAL file not found` durante recovery

```bash
# Log errore:
# LOG:  requested WAL segment 000000010000001800000001 has already been removed

# Causa: il file WAL necessario per il recovery non è disponibile
# Il recovery si interrompe perché non può trovare la sequenza WAL completa

# Soluzioni:
# 1. Verificare il restore_command:
psql -c "SHOW restore_command;"
# Testare manualmente il restore_command con un file WAL specifico
restore_command='cp /wal-archive/%f %p'
# Testare: cp /wal-archive/000000010000001800000001 /tmp/test_wal

# 2. Se si usa S3, verificare che il file esista
aws s3 ls s3://my-wal-bucket/wal/000000010000001800000001

# 3. Se il file mancante è nelle prime posizioni, il backup base è troppo vecchio
# Soluzione: ripristinare da un backup base più recente

# 4. recovery_target_timeline = 'latest' può causare confusione
# Impostare esplicitamente la timeline:
recovery_target_timeline = '1'  # o il numero corretto di timeline
```

## Problemi MySQL

### Problema 1: Replica fermata con errore

```sql
-- Verificare lo stato della replica
SHOW REPLICA STATUS\G

-- Campi chiave:
-- Replica_IO_Running: Yes/No - thread di lettura binlog dal primario
-- Replica_SQL_Running: Yes/No - thread di applicazione degli eventi
-- Last_IO_Error: errore del thread IO
-- Last_SQL_Error: errore del thread SQL
-- Seconds_Behind_Source: lag in secondi

-- Errore tipico 1062 (Duplicate key): un INSERT già presente
-- Last_SQL_Error: Could not execute Write_rows event on table mydb.users;
-- Duplicate entry '123' for key 'PRIMARY', Error_code: 1062

-- Soluzione: saltare l'evento problematico (GTID mode)
STOP REPLICA;
SET GLOBAL gtid_next='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee:12345';
BEGIN; COMMIT;  -- transazione vuota per "bruciare" il GTID
SET GLOBAL gtid_next='AUTOMATIC';
START REPLICA;

-- ATTENZIONE: saltare eventi è pericoloso. Verificare sempre perché l'evento
-- causa un errore e se i dati sono consistenti dopo il salto.
```

```sql
-- Errore 1032 (Record not found): un DELETE o UPDATE su riga non esistente
-- Causa tipica: manipolazione diretta dei dati sulla replica

-- Verifica se la riga esiste
SELECT * FROM mydb.users WHERE id = 123;

-- Opzione A: inserire la riga mancante manualmente sulla replica
SET @@SESSION.SQL_LOG_BIN=0;  -- non replicare questa operazione
INSERT INTO mydb.users (id, name, ...) VALUES (123, ...);
SET @@SESSION.SQL_LOG_BIN=1;

-- Poi riavviare la replica
START REPLICA;

-- Opzione B: saltare l'evento (lascia i dati inconsistenti, usare con cautela)
-- Stessa procedura del GTID skip sopra
```

### Problema 2: Replication lag alto su MySQL

```sql
-- Diagnostica
SHOW REPLICA STATUS\G
-- Seconds_Behind_Source: lag in secondi

-- Verificare il tipo di bottleneck
SHOW PROCESSLIST;
-- Cercare thread con State: 'system lock', 'Waiting for table lock', ecc.

-- Abilitare la replica multi-threaded (MySQL 5.7+)
-- Se Seconds_Behind_Source cresce e la CPU della replica è bassa:
STOP REPLICA SQL_THREAD;
SET GLOBAL replica_parallel_workers = 8;
SET GLOBAL replica_parallel_type = 'LOGICAL_CLOCK';
-- LOGICAL_CLOCK usa i timestamp di commit per parallelizzare in sicurezza
-- DATABASE parallelizza per database (meno efficiente con un singolo db)
START REPLICA SQL_THREAD;

-- Verificare l'impatto
SHOW REPLICA STATUS\G
-- Verificare che Seconds_Behind_Source stia scendendo
```

```sql
-- Replica lag causato da lock contention
SELECT
  r.trx_id waiting_trx_id,
  r.trx_mysql_thread_id waiting_thread,
  r.trx_query waiting_query,
  b.trx_id blocking_trx_id,
  b.trx_mysql_thread_id blocking_thread,
  b.trx_query blocking_query
FROM information_schema.innodb_lock_waits w
INNER JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
INNER JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id;

-- Terminare una transazione bloccante se necessario
KILL 12345;  -- thread ID della transazione bloccante
```

### Problema 3: Errore di connessione tra primario e replica MySQL

```bash
# Log della replica (/var/log/mysql/error.log)
# [ERROR] Replica I/O thread: error connecting to master
# 'replicator@primary.example.com:3306' - retry-time: 60 retries: 10

# Diagnostica:
# 1. Testare la connettività di rete
mysql -h primary.example.com -u replicator -p --protocol=TCP -e "SELECT 1;"

# 2. Verificare le credenziali dell'utente di replica
mysql -h primary -u replicator -p -e "SHOW GRANTS FOR 'replicator'@'%';"
# Deve mostrare: GRANT REPLICATION SLAVE ON *.* TO 'replicator'@'%'

# 3. Verificare il firewall
# Sul primario:
iptables -L -n | grep 3306
# O con nftables:
nft list ruleset | grep 3306

# 4. Verificare che il primario accetti connessioni di replica
mysql -h primary -u root -p -e "SHOW VARIABLES LIKE 'bind_address';"
# Deve essere 0.0.0.0 o l'IP del primario, non 127.0.0.1

# Soluzione: aggiornare la configurazione CHANGE REPLICATION SOURCE
mysql -u root -p << 'EOF'
STOP REPLICA;
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='primary.example.com',
  SOURCE_PORT=3306,
  SOURCE_USER='replicator',
  SOURCE_PASSWORD='correct_password',
  SOURCE_SSL=1,
  SOURCE_AUTO_POSITION=1;
START REPLICA;
SHOW REPLICA STATUS\G
EOF
```

## Diagnostica Avanzata

### Script di diagnostica completo

```bash
#!/bin/bash
# diagnose-replication.sh: raccoglie informazioni diagnostiche complete

echo "=== Diagnostica Replica PostgreSQL ==="
echo "Timestamp: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Host: $(hostname -f)"
echo ""

echo "--- Stato recovery ---"
psql -U postgres -c "SELECT pg_is_in_recovery() AS is_replica, version();"

echo ""
echo "--- Connessioni di replica (se primario) ---"
psql -U postgres -c "
SELECT
  pid,
  application_name,
  client_addr,
  state,
  sync_state,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) / 1024 AS lag_kb,
  replay_lag
FROM pg_stat_replication
ORDER BY lag_kb DESC;
" 2>/dev/null || echo "Non disponibile (nodo in recovery)"

echo ""
echo "--- Stato WAL receiver (se replica) ---"
psql -U postgres -c "
SELECT
  status,
  receive_start_lsn,
  received_lsn,
  last_msg_send_time,
  last_msg_receipt_time,
  EXTRACT(EPOCH FROM (NOW() - last_msg_receipt_time))::int AS seconds_since_msg,
  conninfo
FROM pg_stat_wal_receiver;
" 2>/dev/null || echo "Non in replica"

echo ""
echo "--- Slot di replica ---"
psql -U postgres -c "
SELECT
  slot_name,
  slot_type,
  active,
  pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS wal_retained
FROM pg_replication_slots
ORDER BY pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) DESC;
"

echo ""
echo "--- Spazio disco WAL ---"
du -sh /var/lib/postgresql/*/main/pg_wal/
df -h /var/lib/postgresql/

echo ""
echo "--- Ultimi 20 log errori replica ---"
grep -E "(FATAL|ERROR|replication|wal|standby)" \
  /var/log/postgresql/postgresql-$(date +%Y-%m-%d).log \
  2>/dev/null | tail -20

echo ""
echo "--- Checkpoint recenti ---"
psql -U postgres -c "
SELECT
  checkpoint_lsn,
  write_time,
  sync_time,
  data_sync_retries
FROM pg_control_checkpoint();
"

echo "=== Fine diagnostica ==="
```

### Confronto dati tra primario e replica

```sql
-- Verificare se i dati sono consistenti tra primario e replica
-- Eseguire la stessa query su entrambi e confrontare

-- Query checksum per tabella critica
SELECT
  'primary' AS source,
  COUNT(*) AS row_count,
  SUM(HASHTEXT(t::text)) AS checksum
FROM mydb.critical_table t

UNION ALL

-- (eseguire sulla replica)
SELECT
  'replica' AS source,
  COUNT(*) AS row_count,
  SUM(HASHTEXT(t::text)) AS checksum
FROM mydb.critical_table t;

-- Se i checksum differiscono, i dati sono divergenti
-- Usare pg_comparedb o pgdiff per identificare le differenze specifiche
```

## Tabella di Riferimento Rapido

| Problema | Prima cosa da controllare | Tool/Query |
|---------|--------------------------|------------|
| Replica non connessa | Log del primario | grep "walsender" nel log |
| Lag crescente | I/O disco replica | iostat -x 1 |
| WAL esaurito | Replication slot inattivi | pg_replication_slots |
| Split-brain | pg_is_in_recovery() | Entrambi i nodi |
| MySQL stopped | SHOW REPLICA STATUS | Last_*_Error |
| MySQL lag alto | Multi-threading | replica_parallel_workers |
| Credenziali scadute | pg_hba.conf | Tentare connessione manuale |
| Rete instabile | TCP keepalive | wal_sender_timeout |

