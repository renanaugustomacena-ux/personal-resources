# MySQL/MariaDB Isolation Levels e Locking

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
1. Isolation Levels Deep Dive
2. Lock Types Detail
3. Isolation Implementation
4. Consistency Guarantees
5. Advanced Locking Patterns
6. Isolation Level Comparison
7. Debugging Isolation Issues

---

## 1. Isolation Levels Deep Dive

### 1.1 READ UNCOMMITTED

Il livello più basso - le transazioni possono leggere dati non ancora committati. È raramente usato in produzione ma è importante capire i rischi.

**Comportamento**:
- Nessuna protezione contro dirty reads
- Le modifiche non committate sono visibili
- Nessun lock in lettura

**Problemi**:
```sql
-- Timeline:
-- Time T1: Transazione A
START TRANSACTION;
UPDATE account SET balance = balance - 100 WHERE id = 1;
-- (non commit, ancora in transaction)

-- Time T2: Transazione B (READ UNCOMMITTED)
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
START TRANSACTION;
SELECT * FROM account WHERE id = 1;
-- VEDE la modifica non committata di A!
-- Se A fa ROLLBACK, B ha letto dati che non esistono!

-- Time T3: Transazione A
ROLLBACK;
-- Ora B ha letto dati che non sono mai esistiti nel DB!
```

**Effetto collaterale**:
- Puoi leggere dati che "scompariranno" al rollback
- Reporting può mostrare numeri inconsistenti
- Nessuna garanzia di integrità

**Quando usare**: Quasi mai in produzione. Solo per:
- Debugging di transazioni
- Monitoring dove eventuali inconsistency sono accettabili
- Alcuni edge case di data mining

**Verifica stato**:
```sql
-- Vedere isolation level corrente
SELECT @@transaction_isolation;
SELECT @@session.transaction_isolation;

-- MySQL 8.0 usa transaction_isolation
-- MySQL 5.7 usa tx_isolation
```

### 1.2 READ COMMITTED

Ogni query vede solo dati committati. Ma diverse query possono vedere dati diversi all'interno della stessa transazione.

**Comportamento**:
- Protezione da dirty reads (solo dati committati)
- Snapshot viene refreshed per ogni statement
- Non-repeatable reads possibile

**Problema: Non-Repeatable Read**:
```sql
-- Timeline:
-- Time T1: Transazione A
START TRANSACTION;
UPDATE account SET balance = 900 WHERE id = 1;
COMMIT;

-- Time T2: Transazione B (READ COMMITTED)
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;
SELECT * FROM account WHERE id = 1;  -- 900

-- Time T3: Transazione C (separata)
START TRANSACTION;
UPDATE account SET balance = 800 WHERE id = 1;
COMMIT;

-- Time T4: Transazione B
SELECT * FROM account WHERE id = 1;  -- 800! Dato diverso!
-- Non-repeatable read: stessa query, risultati diversi!
COMMIT;
```

**MySQL/InnoDB behavior**:
- Snapshot per ogni statement (non per transazione)
- Lock su read (non su write come Oracle)
- Più lento di READ COMMITTED in altri DB

**Differenza Oracle**:
- Oracle: READ COMMITTED con consistent read per query
- MySQL: ogni SELECT nel mismo transaction vede dati diversi

### 1.3 REPEATABLE READ

Default InnoDB. Snapshot consistente per l'intera transazione.

**Comportamento**:
- Snapshot creato al primo SELECT
- Tutte le letture usano lo stesso snapshot
- MVCC per non-bloccante reads
- Protegge da non-repeatable e phantom reads

**Consistency garantita**:
```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION;

SELECT * FROM account WHERE id = 1;  -- 900

-- (altra transazione modifica e commit)
UPDATE account SET balance = 800 WHERE id = 1;
COMMIT;

SELECT * FROM account WHERE id = 1;  -- Ancora 900!
-- Stesso snapshot come primo SELECT!

COMMIT;
-- Ora le nuove letture vedranno 800
```

**Phantom Reads**:
- REPEATABLE READ in InnoDB blocca phantom reads
- Grazie a next-key locks
- Other databases possono avere phantom in REPEATABLE READ

**Implementation InnoDB**:
- Read view creato al primo accesso
- mvcc: Multiple Version Concurrency Control
- Undo logs per versioni precedenti
- Visible se trx_id < low_limit_id e trx_id non in active

### 1.4 SERIALIZABLE

Comportamento più stretto. Tutte le letture diventano locking reads.

**Comportamento**:
- SELECT diventa automaticamente LOCK IN SHARE MODE
- Previene phantom reads
- Equivalent a REPEATABLE READ + next-key locks
- Più lento ma garantisce serializzazione

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
START TRANSACTION;
SELECT * FROM account WHERE id = 1;
-- Equivalente a: SELECT * FROM account WHERE id = 1 LOCK IN SHARE MODE
COMMIT;
```

**Effetti**:
- Più blocking che REPEATABLE READ
- Transactioni simultanee "serialize"
- Throughput ridotto
- Ma: garanzia di consistenza assoluta

**Trade-off**:
```sql
-- SERIALIZABLE
-- Pro: massima consistenza
-- Contro: più blocking, meno throughput

-- REPEATABLE READ (InnoDB)
-- Pro: buona consistenza, meno blocking
-- Contro: gap locks per writes, non per reads

-- READ COMMITTED
-- Pro: minima blocking
-- Contro: non-repeatable reads
```

---

## 2. Lock Types Detail

### 2.1 Shared e Exclusive Locks

InnoDB implementa due tipi principali di lock a livello di riga:

**Shared Lock (S-lock)**:
```sql
-- Acquisisce S-lock su row
SELECT * FROM account WHERE id = 1 LOCK IN SHARE MODE;

-- Multiple transazioni possono avere S-lock sullo stesso record
-- Tutte possono leggere, nessuna può modificare

-- Esempio:
-- T1: LOCK IN SHARE MODE su row 1 -> acquisisce S-lock
-- T2: LOCK IN SHARE MODE su row 1 -> acquisisce S-lock (OK!)
-- T3: FOR UPDATE su row 1 -> aspetta S-lock (bloccata!)
```

**Exclusive Lock (X-lock)**:
```sql
-- Acquisisce X-lock su row
SELECT * FROM account WHERE id = 1 FOR UPDATE;

-- UPDATE/DELETE acquisisce X-lock implicito
UPDATE account SET balance = balance + 100 WHERE id = 1;
DELETE FROM account WHERE id = 1;

-- Solo una transazione può avere X-lock su un record
-- блокирует sia lettura che scrittura

-- Esempio:
-- T1: FOR UPDATE su row 1 -> acquisisce X-lock
-- T2: LOCK IN SHARE MODE su row 1 -> aspetta (bloccata!)
-- T2: FOR UPDATE su row 1 -> aspetta (bloccata!)
```

**Compatibility Matrix**:
| Lock Request | S-lock held | X-lock held |
|--------------|-------------|-------------|
| S-lock       | ✓ Compatible | ✗ Blocked   |
| X-lock       | ✗ Blocked   | ✗ Blocked   |

### 2.2 Intention Locks

Table-level locks per coordinamento con row-level locks:

```sql
-- IS: Intention Shared - transazione intende acquisire S-lock su alcune righe
GRANT LOCK TABLES;
SELECT * FROM table LOCK IN SHARE MODE;

-- IX: Intention Exclusive - transazione intende acquisire X-lock su alcune righe
SELECT * FROM table FOR UPDATE;
```

**Perché servono**:
- Permettono a row-level locks di coesistere con table locks
- InnoDB acquisisce automaticamente IS/IX prima di row locks

**Esempio**:
```sql
-- Transazione fa:
SELECT * FROM table FOR UPDATE;

-- InnoDB acquisisce in ordine:
-- 1. IX lock sulla tabella (automatico)
-- 2. X lock sul record (esplicito)
```

**Compatibility**:
|     | IS | IX | S  | X |
|-----|----|----|----|---|
| IS  | ✓ | ✓ | ✓ | ✗ |
| IX  | ✓ | ✓ | ✗ | ✗ |
| S   | ✓ | ✗ | ✓ | ✗ |
| X   | ✗ | ✗ | ✗ | ✗ |

### 2.3 Record vs Gap vs Next-Key

**Record Lock**:
- Lock sul singolo index record
- Non blocca gap prima/dopo il record
- Blocca modifiche a quel record specifico

```sql
-- Record lock su id=10
SELECT * FROM orders WHERE id = 10 FOR UPDATE;
-- Blocca UPDATE/DELETE su id=10
-- Non blocca INSERT su id=11
```

**Gap Lock**:
- Lock sul range tra record
- Previene INSERT di nuovi record nel gap
- Solo in REPEATABLE READ o superiore

```sql
-- Gap lock tra 10 e 20
SELECT * FROM orders WHERE id BETWEEN 10 AND 20 FOR UPDATE;
-- Blocca INSERT con id = 15 (nel range)
-- Non blocca UPDATE su id esistenti
```

**Next-Key Lock**:
- Combinazione di record lock + gap lock
- InnoDB usa next-key locks in REPEATABLE READ
- Previene sia modifiche che inserts

```sql
-- Next-key lock:
-- - X-lock su record 10
-- - Gap lock tra 10 e 20

SELECT * FROM orders WHERE id >= 10 AND id < 20 FOR UPDATE;
```

**Perché serve**:
```sql
-- Senza next-key locks:
T1: SELECT * FROM orders WHERE id > 10;  -- legge id=15
T2: INSERT INTO orders VALUES (16, ...); -- inserisce!
T1: SELECT * FROM orders WHERE id > 10;  -- vede 16! Phantom read!

-- Con next-key locks:
T1: SELECT * FROM orders WHERE id > 10 FOR UPDATE;
T2: INSERT INTO orders VALUES (16, ...); -- BLOCCATO!
T1: SELECT * FROM orders WHERE id > 10;  -- stessi risultati
```

### 2.4 Lock Escalation

**InnoDB**: Non fa lock escalation come SQL Server o Oracle.
- Locks rimangono row-level fino a fine transazione
- Più memory usage ma più granularità
- OK per la maggior parte dei casi

**SQL Server/Oracle**: Fanno lock escalation:
- Table-level locks quando troppi row locks
- Più memory-efficient ma meno granularità
- Può causare blocking

```sql
-- InnoDB: locks rimangono row-level
-- Può avere milioni di locks attivi
-- Ma non diventa table lock

-- SQL Server: potrebbe scalare a table lock
-- SELECT con milioni di rows -> table lock
```

### 2.5 AUTO-INC Lock

Lock speciale per colonne AUTO_INCREMENT:

```sql
INSERT INTO orders (customer_id) VALUES (1);
INSERT INTO orders (customer_id) VALUES (2);
-- Ogni insert acquisisce AUTO-INC lock
-- Lock rilasciato dopo statement (non transaction)
```

**Configurazione**:
```sql
-- InnoDB lock mode
SHOW VARIABLES LIKE 'innodb_autoinc_lock_mode';

-- 0: traditional (serializzato)
-- 1: consecutive (default, bulk inserts together)
-- 2: interleaved (più veloce, ma gap possible)
```

---

## 3. Isolation Implementation

### 3.1 InnoDB MVCC per Isolation

**Read View struttura**:
```
Read View:
- low_limit_id: transaction ID minima visibile (tutte le transazioni >= questo sono invisibili)
- high_limit_id: transaction ID massima visibile (transazioni >= questo sono invisibili)
- read_trx_ids: lista transazioni attive
- creator_trx_id: ID della transazione corrente
```

**Visibility rules**:
```sql
-- Per ogni riga con trx_id:

-- 1. Se trx_id < low_limit_id:
--    Transazione già committata quando read view creato
--    VISIBILE

-- 2. Se trx_id >= high_limit_id:
--    Transazione non ancora iniziata quando read view creato
--    NON VISIBILE: usa undo per versione precedente

-- 3. Se trx_id in read_trx_ids:
--    Transazione attiva nel read view
--    NON VISIBILE: non ancora committata

-- 4. Altrimenti:
--    Transazione committata prima del read view
--    VISIBILE
```

### 3.2 Lock Wait Timeout

```sql
-- Default: 50 secondi
SHOW VARIABLES LIKE 'innodb_lock_wait_timeout';

-- Modificare globalmente
SET GLOBAL innodb_lock_wait_timeout = 10;

-- Modificare per sessione
SET SESSION innodb_lock_wait_timeout = 5;
```

**Effetto**:
- Se una transazione aspetta un lock > timeout
- Riceve errore: "Lock wait timeout exceeded"
- Transazione viene rolled back

**Best practice**: Usare timeout bassi per evitare lock lunghi.

### 3.3 Deadlock Handling

**Deadlock detection**:
```sql
-- Timeout-based
SET GLOBAL innodb_lock_wait_timeout = 5;

-- Detection (MySQL 8.0+)
SET GLOBAL innodb_deadlock_detect = ON;  -- default ON
```

**Quando rileva deadlock**:
- InnoDB costruisce wait-for graph
- Se trova ciclo, deadlock!
- Sceglie victim e fa rollback

**Victim selection**:
```sql
-- InnoDB sceglie:
-- 1. Transazione con meno modifiche (meno undo)
-- 2. Transazione con meno locks

-- Vedere ultima deadlock
SHOW ENGINE INNODB STATUS;
-- Output include "LATEST DETECTED DEADLOCK"
```

**Deadlock example**:
```sql
-- T1: BEGIN; UPDATE t1 SET x=1 WHERE id=1; (X-lock su id=1)
-- T2: BEGIN; UPDATE t2 SET x=1 WHERE id=1; (X-lock su id=1)
-- T1: UPDATE t2 SET x=1 WHERE id=1; (aspetta X-lock di T2)
-- T2: UPDATE t1 SET x=1 WHERE id=1; (aspetta X-lock di T1)
-- -> DEADLOCK!

-- InnoDB detecta e fa rollback di una
```

---

## 4. Consistency Guarantees

### 4.1 Consistent Reads (Non-Locking)

**Default in REPEATABLE READ**:
```sql
START TRANSACTION;
SELECT * FROM orders;  -- snapshot read
-- Non acquisisce locks
-- Non blocca altre transazioni
-- Vede snapshot consistente
COMMIT;
```

**Caratteristiche**:
- Non-bloccante (non usa locks)
- Vede snapshot consistente
- Utile per SELECT che non modificano dati

### 4.2 Locking Reads

**FOR UPDATE**:
```sql
-- Acquisisce X-lock
SELECT * FROM orders WHERE id = 1 FOR UPDATE;
-- Blocca altri da modificare quella riga
-- Blocca altri da leggere con FOR UPDATE

-- Uso tipico: read-then-update pattern
SELECT * FROM orders WHERE id = 1 FOR UPDATE;
UPDATE orders SET status = 'processed' WHERE id = 1;
```

**LOCK IN SHARE MODE**:
```sql
-- Acquisisce S-lock
SELECT * FROM orders WHERE id = 1 LOCK IN SHARE MODE;
-- Blocca others da acquisire X-lock
-- Ma others possono leggere normalmente (non-FOR UPDATE)

-- Uso tipico: verificare dati prima di decidere
SELECT * FROM orders WHERE id = 1 LOCK IN SHARE MODE;
-- Decisioni basate su dati, poi可能的 UPDATE
```

**SELECT senza lock**:
```sql
-- Lock implicito in SERIALIZABLE
-- Ma in REPEATABLE READ: no lock

-- Se hai bisogno di lock per consistenza:
-- - FOR UPDATE per modificare
-- - LOCK IN SHARE MODE per controllare prima di agire
```

### 4.3 Isolation e Durability Trade-offs

```sql
-- Isolation level influenza locks
-- Durability (flush) influenza recoverability

-- Massima safety:
SET GLOBAL innodb_flush_log_at_trx_commit = 1;
SET GLOBAL sync_binlog = 1;

-- Performance:
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL sync_binlog = 0;

-- Ma: rischio perdita dati se crash
```

**Consistency vs Performance**:
- Isolation altos = più locking = meno concurrency
- Durability alta = più I/O = meno throughput

---

## 5. Advanced Locking Patterns

### 5.1 Locking per "Check-Then-Act"

```sql
-- Pattern comune: verifica, poi agisci
-- Sbagliato (race condition):
SELECT balance FROM accounts WHERE id = 1;
-- (altra transazione modifica balance qui!)
UPDATE accounts SET balance = balance - 100 WHERE id = 1;

-- Corretto (con locking):
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;
-- Ora posso fare calcoli con valore certo
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;
```

### 5.2 Optimistic vs Pessimistic Locking

**Optimistic Locking**:
```sql
-- Non usare lock, usare version column
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    version INT DEFAULT 1
);

-- Update con check versione
UPDATE products 
SET name = 'New Name', version = version + 1 
WHERE id = 1 AND version = 5;

-- Se version != 5, nessuna riga aggiornata
-- Applicazione deve retry
```

**Pessimistic Locking**:
```sql
-- Usare locks
SELECT * FROM products WHERE id = 1 FOR UPDATE;
-- Procedere con update
UPDATE products SET name = 'New Name' WHERE id = 1;
```

**When to use each**:
- Optimistic: bassa contention, pochi conflitti
- Pessimistic: alta contention, conflitti frequenti

### 5.3 Gap Locking Patterns

**Evitare gap locks dove possibile**:
```sql
-- Gap lock su range:
SELECT * FROM orders WHERE id BETWEEN 10 AND 20 FOR UPDATE;
-- Blocca INSERT con id nel range!

-- Per evitare: usa precise conditions
SELECT * FROM orders WHERE id = 10 FOR UPDATE;
-- Solo record 10 lockato, non gap
```

**Quando gap locks sono necessari**:
- Prevengono phantom inserts
- Necessari per serializzabilità
- Ma: possono causare blocking

### 5.4 Advisory Locks

```sql
-- MySQL advisory locks (non InnoDB)
-- Usabili per applicazioni esterne

-- Get lock
SELECT GET_LOCK('my_lock', 10);  -- 10 secondi timeout

-- Release lock
SELECT RELEASE_LOCK('my_lock');

-- Check lock
SELECT IS_FREE_LOCK('my_lock');
```

---

## 6. Isolation Level Comparison

### 6.1 Anomaly Summary

| Anomaly | READ UNCOMMITTED | READ COMMITTED | REPEATABLE READ | SERIALIZABLE |
|---------|------------------|----------------|-----------------|--------------|
| Dirty Read | Possibile | Impossibile | Impossibile | Impossibile |
| Non-Repeatable Read | Possibile | Possibile | Impossibile | Impossibile |
| Phantom Read | Possibile | Possibile | Impossibile* | Impossibile |

*InnoDB: impossibile grazie a next-key locks

### 6.2 Performance Comparison

```sql
-- Benchmark approssimativo
-- READ COMMITTED: 100% (baseline, più veloce)
-- REPEATABLE READ: 80-90% (più locking)
-- SERIALIZABLE: 50-70% (massimo blocking)
```

### 6.3 Choosing Isolation Level

```sql
-- READ COMMITTED quando:
-- Non ti importa non-repeatable reads
-- Vuoi minima blocking
-- Reporting queries dove inconsistency accettabile

-- REPEATABLE READ quando:
-- Vuoi consistenza
-- Transazioni tipicamente corte
-- Caso default di InnoDB

-- SERIALIZABLE quando:
-- Critical consistency richiesta
-- Banking/financial transactions
-- Transazioni multipli writes concurrenti
```

---

## 7. Debugging Isolation Issues

### 7.1 Identifying Locks

```sql
-- Vedere locks attivi
SHOW ENGINE INNODB STATUS;

-- Information schema locks
SELECT * FROM information_schema.INNODB_LOCKS;

-- Lock waits
SELECT * FROM information_schema.INNODB_LOCK_WAITS;
```

### 7.2 Processlist Analysis

```sql
-- Vedere transazioni bloccanti
SHOW PROCESSLIST;

-- Thread ID, Command, State, Info
-- State "Waiting for table metadata lock" = metadata lock
-- State "Locked" = row lock
```

### 7.3 Locking Debug Script

```sql
-- Query per identificare blocking
SELECT 
    p.id AS blocking_process_id,
    p.user AS blocking_user,
    p.host AS blocking_host,
    p.command AS blocking_command,
    p.time AS blocking_time,
    p.state AS blocking_state,
    p.info AS blocking_query,
    b.id AS blocked_process_id,
    b.info AS blocked_query
FROM information_schema.PROCESSLIST b
JOIN information_schema.PROCESSLIST p ON b.id = p.id
WHERE b.command = 'Sleep' AND b.time > 5;
```

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*