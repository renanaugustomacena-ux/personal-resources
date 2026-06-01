# Database Replication — Fondamenti e Architettura

## Cos'è la Replica

La **database replication** è il processo di copiare e mantenere sincronizzati i dati di un database su uno o più server separati. Non è backup — la replica mantiene i dati in real-time o near-real-time, mentre il backup è uno snapshot point-in-time.

**Obiettivi della replica**:

1. **Alta disponibilità (HA)**: se il server primario cade, la replica prende il suo posto (failover)
2. **Scalabilità delle letture**: le query SELECT vengono distribuite sulle repliche, alleggerendo il primario
3. **Distribuzione geografica**: dati vicini agli utenti (multi-region)
4. **Isolamento workload**: analytics/reporting su repliche dedicate, OLTP sul primario
5. **Disaster recovery**: replica in datacenter separato come backup "vivo"

---

## Meccanismi Fondamentali

### Statement-Based Replication (SBR)

Il primario registra nel log binario le **istruzioni SQL** che vengono poi rieseguite sulla replica.

```sql
-- Sul primario: eseguita questa query
UPDATE users SET last_login = NOW() WHERE id = 1001;

-- Sul log binario: registrato l'SQL
-- UPDATE users SET last_login = NOW() WHERE id = 1001;

-- Sulla replica: rieseguita la stessa query
-- last_login otterrà un valore diverso (NOW() restituisce il tempo attuale della replica!)
```

**Problemi di SBR**:
- Funzioni non deterministiche (`NOW()`, `UUID()`, `RAND()`) producono valori diversi
- Richiede che le funzioni utente e trigger siano presenti su entrambi i server
- Difficile tracciare quali righe sono state modificate

### Row-Based Replication (RBR)

Il primario registra le **righe modificate** (before/after image).

```
Log entry per UPDATE users SET last_login = NOW() WHERE id = 1001:
{
  "type": "UPDATE",
  "table": "users",
  "before": {"id": 1001, "last_login": "2024-01-14 09:00:00"},
  "after":  {"id": 1001, "last_login": "2024-01-15 10:30:00"}
}
```

**Vantaggi di RBR**:
- Deterministico: la replica applica esattamente le stesse righe
- Nessuna riesecuzione di SQL (più sicuro e prevedibile)
- Supporta trigger diversi sulle repliche senza problemi

**Svantaggi**:
- Log più grande per query che modificano molte righe (es. `UPDATE ... WHERE 1=1` → miliardi di row changes)

### Mixed Replication

Combinazione: usa SBR per default, passa a RBR automaticamente quando rileva istruzioni non sicure.

---

## Write-Ahead Log (WAL) e Replica in PostgreSQL

PostgreSQL usa il **WAL** (Write-Ahead Log) come meccanismo di replica. Il WAL registra ogni modifica al database a livello di blocco di storage.

```
WAL Record:
  LSN (Log Sequence Number): posizione univoca nel log
  Resource Manager: quale componente ha generato il record (Heap, Index, XLOG, etc.)
  Data: il dato grezzo modificato (before/after image a livello di blocco)
```

**Streaming Replication**: la replica si connette al primario via TCP e riceve i WAL record in streaming man mano che vengono generati.

```
Primary WAL:  [LSN 0/1000] [LSN 0/1001] [LSN 0/1002] ...
                   ↓ WAL sender process
Replica:      [LSN 0/1000] [LSN 0/1001] [LSN 0/1002] ...
              WAL receiver → WAL writer → Recovery process (apply)
```

---

## Binlog in MySQL

MySQL usa il **Binary Log** (binlog) per la replica. Supporta tutti e tre i formati (SBR, RBR, mixed).

```bash
# Configurazione primario (/etc/mysql/mysql.conf.d/mysqld.cnf)
[mysqld]
server-id = 1                    # Univoco per ogni server nel cluster
log_bin = /var/log/mysql/binlog  # Abilita binary logging
binlog_format = ROW              # RBR raccomandato
binlog_row_image = FULL          # Registra before + after image complete
sync_binlog = 1                  # fsync per ogni transaction (durabilità)
expire_logs_days = 7             # Retention binlog

# GTID (Global Transaction ID) - raccomandato
gtid_mode = ON
enforce_gtid_consistency = ON
```

```bash
# Ispezione del binlog
mysqlbinlog --base64-output=decode-rows -v /var/log/mysql/binlog.000001

# Output:
# # at 4
# #240115 10:30:00 server id 1  end_log_pos 123 CRC32 0x12345678
# ### UPDATE `mydb`.`users`
# ### WHERE
# ###   @1=1001  (user_id)
# ###   @3='2024-01-14 09:00:00'  (last_login)
# ### SET
# ###   @3='2024-01-15 10:30:00'
```

---

## Replica Fisica vs Replica Logica

### Replica Fisica (Block-Level)

Copia le modifiche a livello di pagina di storage. La replica è identica byte per byte al primario (stessa versione del DB, stessa architettura hardware).

**PostgreSQL Streaming Replication**: fisica per default.

**Pro**: semplice, completa (DDL incluso), bassa latenza
**Contro**: stessa versione del DB richiesta, stessa architettura hardware, nessuna trasformazione dei dati possibile

### Replica Logica (Tuple-Level)

Copia le modifiche a livello di tupla (riga), con la possibilità di filtrare tabelle, colonne, e trasformare i dati.

**PostgreSQL Logical Replication**: disponibile da PG10.
**Debezium**: CDC (Change Data Capture) su Kafka.

**Pro**: versioni diverse del DB, filtraggio per tabella/colonna, trasformazioni, multi-master possibile
**Contro**: DDL non replicato automaticamente, più complesso da configurare

```sql
-- PostgreSQL Logical Replication

-- Sul primario: crea un publication (cosa replicare)
CREATE PUBLICATION my_pub FOR TABLE users, orders, products;
-- oppure: per tutte le tabelle
CREATE PUBLICATION my_pub FOR ALL TABLES;

-- Sulla replica: crea una subscription (da dove ricevere)
CREATE SUBSCRIPTION my_sub
    CONNECTION 'host=primary user=replication password=secret dbname=mydb'
    PUBLICATION my_pub;

-- Monitoring
SELECT * FROM pg_stat_replication;  -- sul primario
SELECT * FROM pg_stat_subscription; -- sulla replica
```

---

## Lag di Replica: Definizione e Impatto

Il **replication lag** è il ritardo tra quando una transazione viene committata sul primario e quando viene applicata sulla replica.

```sql
-- PostgreSQL: misura il lag
SELECT
    application_name,
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    sent_lsn - replay_lsn AS bytes_lag,
    (now() - reply_time) AS time_since_last_reply,
    write_lag,
    flush_lag,
    replay_lag  -- lag di applicazione effettivo
FROM pg_stat_replication;

-- MySQL: lag sulla replica
SHOW REPLICA STATUS\G
-- Seconds_Behind_Source: 0  ← nessun lag
-- Seconds_Behind_Source: 120 ← la replica è 2 minuti indietro
```

**Cause comuni del lag**:
1. Query pesanti sulla replica (analytics, VACUUM) contendono CPU/I/O con il recovery process
2. Network tra primario e replica congestionata
3. Replica troppo lenta (hardware inferiore)
4. Transazioni molto grandi (multi-milioni di righe) che richiedono tempo per essere applicate

Il lag di replica è il fattore critico che determina la **consistenza eventuale** del sistema — un'applicazione che legge dalla replica subito dopo una write sul primario potrebbe vedere dati vecchi.
