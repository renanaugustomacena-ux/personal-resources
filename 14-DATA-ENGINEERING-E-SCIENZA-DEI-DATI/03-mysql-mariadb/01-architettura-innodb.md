# MySQL/MariaDB Architettura InnoDB

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
1. InnoDB Storage Engine
2. Buffer Pool Architecture
3. Tablespace e Data Files
4. InnoDB Log Files
5. Transaction Model
6. Lock Management
7. MVCC in InnoDB
8. Index Structure
9. Checkpoint e Recovery
10. Performance Tuning

---

## 1. InnoDB Storage Engine

### 1.1 What is InnoDB

**InnoDB** è il default storage engine di MySQL (dalla versione 5.5) e MariaDB. È la scelta predominante per applicazioni production grazie alle sue proprietà ACID e alle performance scalabili.

**Caratteristiche fondamentali**:
- **ACID Compliance**: Supporto completo per transazioni ACID con commit e rollback
- **Row-Level Locking**: Blocca solo le righe interessate, non la tabella intera
- **MVCC (Multi-Version Concurrency Control)**: Read non bloccanti per query consistenti
- **Foreign Key Constraints**: Integrità referenziale con supporto nativo CASCADE
- **Clustered Index**: Dati organizzati in B+Tree basato sulla primary key
- **Automatic Crash Recovery**: Recovery automatico basato su redo logs
- **Doublewrite Buffer**: Protezione contro partial page writes

**Confratto con MyISAM**:
| Caratteristica | InnoDB | MyISAM |
|----------------|--------|--------|
| ACID | Sì | No |
| Transaction | Sì | No |
| Row Lock | Sì | Table lock |
| Crash Recovery | Automatico | Manuale |
| Foreign Keys | Sì | No |
| Full-text Index | Sì (5.6+) | Sì |
| GIS | Sì | Limitato |

### 1.2 Architecture Overview

L'architettura InnoDB è modulare e complessa. Comprende multiple componenti che lavorano insieme:

**Componenti core**:

**Buffer Pool**: Cache in memoria per dati e indici. È la componente più critica per le performance. Gestisce pagine lette dal disco e modifiche in attesa di flush.

**InnoDB Tablespaces**: I file fisici dove i dati sono stored. Include system tablespace, per-table tablespace, undo tablespace, e temporary tablespace.

**Redo Log**: Write-ahead logging per durability. Tutte le modifiche vengono registrate nel redo log prima di essere applicate alla buffer pool.

**Undo Log**: Spazio per versioni precedenti delle righe per MVCC e rollback. Stored in undo tablespace.

**Lock Manager**: Gestisce i lock per le transazioni. Include lock hash table e deadlock detector.

**Transaction Coordinator**: Orchestrate commit e rollback. Gestisce la transazione lifecycle.

**Purge Thread**: Rimuove le vecchie versioni delle righe che non sono più necessarie.

**Checkpoint Manager**: Coordina la scrittura delle dirty pages su disco.

### 1.3 Disk Layout

Il layout su disco di InnoDB è organizzato in multiple tablespaces:

**System Tablespace (ibdata1, ibdata2, ...)**: Il tablespace principale che contiene:
- Data Dictionary: Metadati sulle tabelle
- Undo Pages: Log delle modifiche per rollback
- Change Buffer: Cache per modifiche a indici secondari
- Doublewrite Buffer: Buffer per safe page writes
- Table Statistics: Statistiche per l'optimizer
- Rollback Segments: Segmenti per undo management

**Per-Table Tablespace (.ibd files)**: Con `innodb_file_per_table=ON`, ogni tabella ha il proprio file:
- Un solo tablespace per tabella
- Possono essere troncati o eliminati
- Supportano transportable tablespaces

**Undo Tablespace (MySQL 8.0+, MariaDB 10.6+)**: Tablespace dedicato per undo logs:
- Predefined undo tablespaces
- Miglior gestione dello spazio
- Possibilità di truncate automatico

**General Tablespace**: Tablespace condivisi per multiple tabelle:
```sql
CREATE TABLESPACE ts1 ADD DATAFILE 'ts1.ibd';
CREATE TABLE t1 (...) TABLESPACE ts1;
```

**Temporary Tablespace**: Per tabelle temporanee interne:
- Non è crash-safe
- Rilasciato alla chiusura

**Nomenclature delle pagine**:
- Page size: 16KB default (configurabile: 4K, 8K, 16K, 32K, 64K)
- Page types: FIL_PAGE_INDEX, FIL_PAGE_UNDO_LOG, FIL_PAGE_INODE, etc.
- Extent: 1MB (64 pagine da 16KB)
- Segment: Collezione di extents per un index

---

## 2. Buffer Pool Architecture

### 2.1 Buffer Pool

Il **Buffer Pool** è la cache in memoria più importante di InnoDB. Memorizza sia dati che indici per ridurre accessi al disco.

**Dimensione consigliata**:
```sql
-- Verificare dimensione attuale
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
-- Default: 128MB, Production: 50-70% della RAM

-- Calcolo: se hai 32GB RAM, usa 24GB per buffer pool
SET GLOBAL innodb_buffer_pool_size = 24159191040;  -- 24GB in bytes
```

**Struttura interna**:
```
Buffer Pool
├── Pages (16KB ciascuna)
│   ├── Clean pages (non modificate)
│   └── Dirty pages (modificate, non flushate)
├── Hash Table (per lookup O(1))
├── LRU List (Least Recently Used)
│   ├── New sublist (young)
│   └── Old sublist
└── Free List (pagine libere)
```

**Page States**:
- **FREE**: Pagina non usata, disponibile
- **CLEAN**: Caricata, non modificata
- **DIRTY**: Modificata, in attesa di flush
- **FLUSH**: Attualmente in flush su disco

### 2.2 LRU Replacement

L'algoritmo LRU (Least Recently Used) gestisce l'eviction delle pagine meno utilizzate.

**InnoDB LRU Implementation**:

```c
// Concetto: LRU a due parti
// New pages inserite al 5/8 dalla tail (non dalla testa)
// Access recenti spostano verso head
// LRU tail = candidate per eviction
```

**Comportamento**:
1. Nuova pagina letta dal disco
2. Inserita nel "new" sublist (5/8 dalla tail)
3. Se acceduta, spostata in "young" sublist (head)
4. Pagine vecchie nel "old" sublist sono candidate a eviction

**Parametri di tuning**:
```sql
-- Posizione inserimento (default 37% = 5/8)
SHOW VARIABLES LIKE 'innodb_old_blocks_pct';
-- Range: 5-95

-- Tempo per considerare "recent access"
SHOW VARIABLES LIKE 'innodb_old_blocks_time';
-- Millisecondi prima che pagina possa essere spostata a young

-- Esempio: ridurre scan impact
SET GLOBAL innodb_old_blocks_pct = 20;  -- più conservativo
SET GLOBAL innodb_old_blocks_time = 1000;  # 1 secondo
```

**Problemi comuni**:

**Buffer Pool Scans**:
```sql
-- Full table scan può riempir buffer pool
SELECT * FROM huge_table;  -- problematico

-- Soluzione: usare cover WHERE o LIMIT
SELECT * FROM huge_table WHERE id > 0 LIMIT 1000;
```

**Prefetching**: InnoDB legge pagine "anticipate" durante le scansioni. Configurabile:
```sql
SHOW VARIABLES LIKE 'innodb_read_ahead_threshold';
-- Def: 56, range: 0-64

SHOW VARIABLES LIKE 'innodb_random_read_ahead';
-- Def: OFF, abilita random read ahead
```

### 2.3 Buffer Pool Instances

Per sistemi con molta memoria, multiple istanze del buffer pool riducono la contesa:

```sql
-- Numero di istanze (default: 1, raccomandato: 1 per 1-2GB)
SET GLOBAL innodb_buffer_pool_instances = 8;

-- Verificare
SHOW VARIABLES LIKE 'innodb_buffer_pool_instances';
```

**Quando usare multiple istanze**:
- Buffer pool > 1GB
- Sistemi con alta concorrenza
- Molte sessioni simultanee
- Contesa sulla mutex del buffer pool

**Stato del buffer pool**:
```sql
-- Statistiche dettagliate
SHOW ENGINE INNODB STATUS\G

-- Info su buffer pool
SELECT * FROM information_schema.INNODB_BUFFER_POOL_STATS\G

-- Pagine in cache
SELECT * FROM information_schema.INNODB_BUFFER_PAGE
WHERE TABLE_NAME = 'db/t' LIMIT 10;
```

### 2.4 Buffer Pool Flush

InnoDB flusha le dirty pages in background per mantenere la consistenza:

**Page Cleaner Thread**:
```sql
-- Numero di thread per flush (default: 4 o CPU count)
SHOW VARIABLES LIKE 'innodb_page_cleaners';

-- Pagine per flush batch
SHOW VARIABLES LIKE 'innodb_flush_neighbors';
-- 0: no neighbors
-- 1: flush consecutive dirty pages
-- 2: flash all in range (default)
```

**Adaptive Flushing**: InnoDB aggiusta automaticamente la velocità di flush basandosi su:
- Numero di dirty pages
- Checkpoint age
- I/O capacity

**Forzare flush**:
```sql
-- Flush di tutte le dirty pages
SET GLOBAL innodb_flush_neighbors = 0;
ALTER TABLE t ENGINE=InnoDB;  -- rebuild e flush

-- Checkpoint manuale
SET GLOBAL innodb_flush_log_at_trx_commit = 1;
FLUSH LOGS;
```

### 2.5 Buffer Pool Memory Components

La memoria del buffer pool è divisa in multiple aree:

```sql
-- Statistiche memoria
SHOW ENGINE INNODB STATUS\G
-- cerca "Buffer pool hit rate"
```

**Memory Allocation**:
- **Data Pages**: Dati delle tabelle
- **Index Pages**: Pagine degli indici
- **Lock Info**: Informazioni sui lock (piccola quota)
- **Page Hash**: Hash table per lookup
- **Dictionary Cache**: Cache del data dictionary
- **Adaptive Hash Index**: Hash index in-memory

---

## 3. Tablespace e Data Files

### 3.1 System Tablespace

System tablespace:
- Contains: data dictionary, undo, change buffer
- File: ibdata1, ibdata2, ...

### 3.2 Per-Table Tablespaces

File-per-table:
```sql
SET GLOBAL innodb_file_per_table = ON;
-- Creates .ibd file per table
```

### 3.3 General Tablespace

General tablespace:
```sql
CREATE TABLESPACE ts1 ADD DATAFILE 'ts1.ibd';
```

---

## 4. InnoDB Log Files

### 4.1 Redo Logs

Il **redo log** è il cuore della durability di InnoDB. Registra tutte le modifiche ai dati prima che siano scritte nel data files.

**Caratteristiche**:
- Write-ahead logging (WAL): Log scritto prima delle modifiche
- Circular log: Vecchi log sovrascritti dopo checkpoint
- crash-safe: Permette recovery dopo crash

**Configurazione**:
```sql
-- Dimensione file di log (MySQL 8.0+)
SHOW VARIABLES LIKE 'innodb_redo_log_capacity';
-- Default: 100MB (auto-managed in 8.0.30+)

-- Per versioni precedenti:
SHOW VARIABLES LIKE 'innodb_log_file_size';
-- Default: 48MB, raccomandato: 256MB-1GB
SHOW VARIABLES LIKE 'innodb_log_files_in_group';
-- Default: 2

-- Calcolo: log_capacity = log_files * file_size
-- Per 2 file da 512MB = 1GB redo log
SET GLOBAL innodb_log_file_size = 536870912;  # 512MB
```

**Monitoraggio**:
```sql
-- Spazio usato nei redo log
SHOW ENGINE INNODB STATUS\G
-- cerca "Log sequence number", "Log flushed up to"

-- Se "Unflushed log" è alto, il disco non tiene il carico
-- Considera: SSD, increased log size, reduced commit frequency
```

### 4.2 Log Group

InnoDB usa un gruppo di log con due o più file:

**Log Group**:
```
Log Group
├── ib_logfile0 (512MB)
└── ib_logfile1 (512MB)

Scrittura circolare:
[ib_logfile0] -----> [ib_logfile1] -----> [ib_logfile0]
   write point          checkpoint
```

**Checkpoint**:
- Scrive LSN (Log Sequence Number) periodicamente
- Permette di sapere da dove partire in recovery
- Triggerato da: buffer pool piena, timeout, manual

**Log Write Process**:
```sql
-- Controllo persistenza
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';
-- 1 (default): fsync su ogni commit - massima durability
-- 2: flush to OS cache - miglior performance, rischio lose < 1 sec
-- 0: async to buffer - rischio perdita transazioni intere
```

**Trade-offs**:
```sql
-- Durability massima (default)
SET GLOBAL innodb_flush_log_at_trx_commit = 1;
-- Ogni commit = fsync (lento ma sicuro)

-- Performance
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
-- Flush a OS (più veloce, rischio: crash = max 1 sec dati)

-- Benchmarking
SET GLOBAL innodb_flush_log_at_trx_commit = 0;
-- Async (massima velocità, rischio: perdita intere transactions)
```

### 4.3 Undo Logs

Gli **undo logs** memorizzano le versioni precedenti delle righe per MVCC e rollback.

**Funzioni**:
- **Rollback**: Permette di annullare transazioni
- **MVCC**: Fornisce snapshot consistenti per letture
- **Consistency**: Mantiene consistenza durante recovery

**Archiviazione**:
```sql
-- Undo tablespace (MySQL 8.0+)
SHOW VARIABLES LIKE 'innodb_undo_tablespaces';
-- Minimo: 2 (per truncation)

-- Spazio massimo per undo
SHOW VARIABLES LIKE 'innodb_undo_log_truncate';
-- Default: ON

-- Retention: quante transazioni possono trattenere undo
SHOW VARIABLES LIKE 'innodb_max_purge_lag';
-- Default: 0 (no delay)
-- Valori più alti: più spazio per MVCC, più overhead
```

**Monitoraggio**:
```sql
-- Statistiche undo
SHOW ENGINE INNODB STATUS\G
-- cerca "History list length" (transazioni non purgeate)

-- Spazio undo
SELECT * FROM information_schema.INNODB_TABLESPACES
WHERE NAME LIKE 'innodb_undo%';
```

**Problemi comuni**:
```sql
-- Undo tablespace pieno
-- Soluzione: truncate
SET GLOBAL innodb_undo_log_truncate = ON;

-- Transazioni a lungo bloccano purge
-- Evitare transazioni long-running
-- Commit frequenti
```

### 4.4 Log Compression (MariaDB)

In MariaDB 10.6+ è disponibile la compressione dei log:

```sql
-- Abilitare compressione log
SET GLOBAL innodb_redo_log_compress = ON;

-- Livello compressione
SET GLOBAL innodb_redo_log_encrypt = ON;  -- anche encrypted
```

---

## 5. Transaction Model

### 5.1 ACID in InnoDB

InnoDB implementa completamente le proprietà ACID:

**Atomicity (原子性)**:
- Tutte le operazioni nella transazione succeedono o falliscono come unità
- Implementato tramite: redo log per commit, undo log per rollback
- Se crash durante transazione: undo delle modifiche non committate

**Consistency (一致性)**:
- Il database rimane sempre in uno stato consistente
- Implementato tramite: doublewrite buffer, constraint checks, foreign keys
- Validazione: data types, unique constraints, foreign keys, check constraints

**Isolation (隔离性)**:
- Transazioni concurrenti non interferiscono tra loro
- Implementato tramite: MVCC + lock management
- Isolation levels configurabili: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE

**Durability (持久性)**:
- Transazioni committate sopravvivono a crash
- Implementato tramite: redo log + fsync
- `innodb_flush_log_at_trx_commit` controlla il livello di durability

### 5.2 Commit Process

Quando una transazione fa COMMIT, InnoDB esegue una sequenza precisa:

**Processo di Commit**:
```
1. Write redo log (in-memory)
2. Flush redo log a disco (fsync)
3. Mark transaction come committed
4. Release locks
5. Return to client
```

**Sequenza dettagliata**:
```sql
START TRANSACTION;
UPDATE account SET balance = balance - 100 WHERE id = 1;
UPDATE account SET balance = balance + 100 WHERE id = 2;
COMMIT;

-- Durante COMMIT:
-- 1. InnoDB writes "commit" al redo log buffer
-- 2. InnoDB calls fsync() sul redo log file
-- 3. Transaction coordinator marks commit
-- 4. Locks rilasciati
-- 5. Client riceve OK
```

**Configurazione durabilità**:
```sql
-- Massima durabilità (default)
SET GLOBAL innodb_flush_log_at_trx_commit = 1;
-- Ogni commit = fsync

-- Trade-off: prestazioni
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
-- Flush a OS buffer, fsync meno frequente
-- Rischio max: 1 secondo di dati

SET GLOBAL innodb_flush_log_at_trx_commit = 0;
-- Async, più veloce ma rischioso
-- Solo per non-critical data
```

**Partial Commit (group commit)**:
```sql
-- Multiple transazioni possono essere flushate insieme
-- Riduce overhead di fsync per molte piccole transazioni

SHOW VARIABLES LIKE 'innodb_flush_sync';
-- Default: ON - skip flush se checkpoint imminente
```

### 5.3 Transaction Isolation Levels

MySQL/MariaDB supporta quattro isolation levels:

```sql
-- Impostare isolation level
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- oppure per sessione:
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

**READ UNCOMMITTED**:
- Letture non bloccanti
- Può leggere dati non committati (dirty reads)
- Non usare in produzione

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SELECT * FROM orders WHERE id = 1;  -- può vedere dati non committati
```

**READ COMMITTED** (default Oracle, PostgreSQL):
- Ogni read vede solo dati committati
- Non repeatable reads: stessa query può vedere dati diversi

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- Query 1: SELECT * FROM t WHERE id = 1;  -- vede valore A
-- (altra transazione modifica id=1 con commit)
-- Query 2: SELECT * FROM t WHERE id = 1;  -- vede valore B
```

**REPEATABLE READ** (default InnoDB):
- Snapshot consistente per l'intera transazione
- Nessun dirty read o non-repeatable read
- Ma: phantom reads possibili con locking

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- Query 1: SELECT * FROM t;  -- 10 righe
-- (altra transazione inserisce 5 righe)
-- Query 2: SELECT * FROM t;  -- still 10 righe (snapshot)
```

**SERIALIZABLE**:
- Comportamento simile a REPEATABLE READ con lock impliciti
- Tutte le letture diventano locking reads
- Equivalent a `LOCK IN SHARE MODE`

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- Ogni SELECT diventa: SELECT ... LOCK IN SHARE MODE
```

**Confronto Isolation Levels**:
| Level | Dirty Read | Non-Repeatable | Phantom |
|-------|------------|----------------|---------|
| Read Uncommitted | Possibile | Possibile | Possibile |
| Read Committed | No | Possibile | Possibile |
| Repeatable Read | No | No | Possibile |
| Serializable | No | No | No |

### 5.4 Autocommit

```sql
-- Default: autocommit = ON
SHOW VARIABLES LIKE 'autocommit';

-- Ogni statement è una transazione implicita
INSERT INTO t VALUES (1);  -- auto-commit
INSERT INTO t VALUES (2);  -- auto-commit

-- Disabilitare per transazioni esplicite
SET GLOBAL autocommit = 0;
START TRANSACTION;
-- multiple statements
COMMIT;  -- o ROLLBACK;
```

---

## 6. Lock Management

### 6.1 Lock Types

InnoDB implementa diversi tipi di lock:

**Shared Lock (S-lock)**:
- Permette lettura
- Multiple S-locks possono coesistere sulla stessa risorsa
- Acquisito da: `SELECT ... LOCK IN SHARE MODE`

**Exclusive Lock (X-lock)**:
- Permette lettura e scrittura
- Solo un X-lock per risorsa
- Acquisito da: `SELECT ... FOR UPDATE`, `INSERT`, `UPDATE`, `DELETE`

**Intention Locks** (table-level):
- **IS (Intention Shared)**: Transazione intende acquisire S-lock su righe
- **IX (Intention Exclusive)**: Transazione intende acquisire X-lock su righe
- Necessari per protocollo di escalation a table lock

**Record Locks** (row-level):
- Lock su singolo record nell'indice
- Non blockano l'intera pagina o tabella

**Gap Locks**:
- Lock sul range tra record
- Previene insert di nuove righe nel gap
- Solo in REPEATABLE READ o superiore

**Next-Key Locks**:
- Combinazione di record lock + gap lock
- Previene phantom reads

**AUTO-INC Locks**:
- Lock speciale per colonne AUTO_INCREMENT
- Rilasciato dopo statement (non transaction)

### 6.2 Lock Implementation

**Lock Hash Table**:
```
Lock Hash Table (in memory)
├── Hash bucket 0 → [lock_t, lock_t, ...]
├── Hash bucket 1 → [lock_t, ...]
...
└── Hash bucket N

Ogni lock_t contiene:
├── space_id (tablespace)
├── page_no (pagina)
├── n_bits (numero bit per record)
└── locks (bitmask per record)
```

**Lock Compatibility Matrix**:
|  | S | X | IS | IX |
|--|---|---|----|----|
| S | ✓ | ✗ | ✓ | ✗ |
| X | ✗ | ✗ | ✗ | ✗ |
| IS | ✓ | ✗ | ✓ | ✓ |
| IX | ✗ | ✗ | ✓ | ✓ |

**Acquisizione lock**:
```sql
-- Lock implicito (automatico)
INSERT INTO t VALUES (1);  -- X-lock su nuovo record
UPDATE t SET col = 'x' WHERE id = 1;  -- X-lock su record esistente

-- Lock esplicito
SELECT * FROM t WHERE id = 1 LOCK IN SHARE MODE;  -- S-lock
SELECT * FROM t WHERE id = 1 FOR UPDATE;  -- X-lock
```

### 6.3 Deadlock Detection

**Wait-for Graph**:
- InnoDB costruisce un grafo delle transazioni in attesa
- Ciclo nel grafo = deadlock
- Trigger: quando una transazione aspetta > `innodb_lock_wait_timeout`

**Detection Process**:
```
Transazione A: lock su row 1, vuole row 2
Transazione B: lock su row 2, vuole row 1

Wait-for graph:
A → (waits for) → B → (waits for) → A = DEADLOCK!

InnoDB detecta ciclo e:
1. Sceglie "victim" (transazione con meno modifiche)
2. Rollback della victim
3. L'altra transazione continua
```

**Configurazione**:
```sql
-- Timeout di attesa lock (default: 50s)
SHOW VARIABLES LIKE 'innodb_lock_wait_timeout';
SET GLOBAL innodb_lock_wait_timeout = 5;  # 5 secondi

-- Livello deadlock detection (MySQL 8.0+)
SHOW VARIABLES LIKE 'innodb_deadlock_detect';
SET GLOBAL innodb_deadlock_detect = ON;  # default ON

-- Se disabilitato: timeout è l'unica detection
```

**Selezione Victim**:
- InnoDB sceglie la transazione con meno undo log
- Transazioni con molte modifiche hanno più probabilità di essere preserved

**Minimizzare deadlock**:
```sql
-- 1. Accesso in ordine consistente
BEGIN;
UPDATE t SET col = 1 WHERE id = 1;
UPDATE t SET col = 2 WHERE id = 2;  -- stesso ordine in tutte le transazioni
COMMIT;

-- 2. Transazioni brevi
-- 3. Indices appropriati (evita lock su range grandi)
-- 4. Avoid hot rows
```

### 6.4 Lock Monitoring

```sql
-- Visualizzare lock attivi
SHOW ENGINE INNODB STATUS\G
-- cerca "TRANSACTIONS" section

-- Informazioni lock
SELECT * FROM information_schema.INNODB_LOCKS;

-- Attese lock
SELECT * FROM information_schema.INNODB_LOCK_WAITS;

-- Processlist con lock
SELECT 
    p.id,
    p.user,
    p.command,
    i.lock_mode,
    i.lock_type,
    i.lock_index,
    i.lock_data
FROM information_schema.PROCESSLIST p
JOIN information_schema.INNODB_TRX t ON p.id = t.ID
JOIN information_schema.INNODB_LOCKS i ON t.trx_id = i.lock_trx_id;
```

### 6.5 Gap Locks e Phantom Prevention

**Gap Lock**:
```sql
-- REPEATABLE READ
BEGIN;
SELECT * FROM t WHERE id BETWEEN 10 AND 20;
-- Acquisisce gap lock sul range (10,20)
-- Nessun altro può inserire in questo range
INSERT INTO t VALUES (15);  # Bloccato!
```

**Next-Key Lock**:
- Record lock + gap lock combinati
- Previene insert nel gap e lock sul record
- Automatico in REPEATABLE READ per scansioni

**避免 Phantom**:
```sql
-- Per prevenire phantom reads:
-- Opzione 1: Serializable isolation
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Opzione 2: Lock esplicito con FOR UPDATE
SELECT * FROM t WHERE id > 10 FOR UPDATE;
-- Acquisisce next-key locks, nessun insert possibile

-- Opzione 3: Consistent read con index lock (MariaDB)
SELECT * FROM t WHERE id > 10 LOCK WITH CONSISTENT SNAPSHOT;
```

---

## 7. MVCC in InnoDB

### 7.1 Version Storage

**MVCC (Multi-Version Concurrency Control)** permette letture non bloccanti mantenendo multiple versioni delle righe.

**Struttura di ogni riga** (in clustered index):
```c
struct innodb_row {
    // Fixed-size fields
    trx_id_t trx_id;      // Transaction ID che ha modificato
    roll_ptr_t roll_ptr;  // Pointer a undo log
    ...
    // Variable-size fields
    var_fields...
}
```

**Roll Pointer**:
- Pointer a undo log record
- Permette di navigare alle versioni precedenti
- 7 bytes: 6 per undo location + 1 per flag

**Undo Log Records**:
```
Undo Log
├── Old values delle colonne modificate
├── Pointer a versione precedente
├── Transaction ID della transazione
└── Table ID
```

**Esempio di versioni**:
```sql
-- Transazione 10: INSERT
INSERT INTO t (id, name) VALUES (1, 'Alice');
-- Row: trx_id=10, roll_ptr=null

-- Transazione 20: UPDATE (after 10 commits)
UPDATE t SET name = 'Bob' WHERE id = 1;
-- Row: trx_id=20, roll_ptr -> undo(record v1)
-- Undo: name='Alice', trx_id=10

-- Transazione 30: UPDATE (after 20 commits)
UPDATE t SET name = 'Carol' WHERE id = 1;
-- Row: trx_id=30, roll_ptr -> undo(record v2)
-- Undo: name='Bob', trx_id=20 -> undo v1 -> 'Alice'
```

### 7.2 Read Views

Il **Read View** è lo snapshot che una transazione vede. Determina quali versioni sono visibili.

**Componenti del Read View**:
```c
struct read_view {
    trx_id_t trx_id;           // ID transazione corrente
    trx_id_t low_limit_id;    // Non vedere trx > questo
    trx_id_t high_limit_id;   // Non vedere trx >= questo
    trx_id_t *ids;            // Transazioni attive
    uint_t n_ids;             // Numero transazioni attive
    bool update_not_allowed;  // Non può modificare se ci sono trx attive
}
```

**Visibility Rules**:
```
Per ogni riga con trx_id:

1. Se trx_id < low_limit_id:
   - Trx già committata
   - VISIBILE

2. Se trx_id >= high_limit_id:
   - Trx non ancora attiva quando read view creata
   - NON VISIBILE (usa undo per versione precedente)

3. Se trx_id in ids[]:
   - Trx attiva nel read view
   - NON VISIBILE (vedi versione precedente)

4. Altrimenti:
   - Trx committata prima del read view
   - VISIBILE
```

**Consistent Read (Snapshot Read)**:
```sql
-- Default in REPEATABLE READ
SELECT * FROM t;  -- usa read view creato all'inizio

-- READ COMMITTED: new read view per ogni statement
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
SELECT * FROM t;  -- nuovo snapshot ogni SELECT
```

**Locking Read**:
```sql
-- Acquisisce lock + legge
SELECT * FROM t WHERE id = 1 FOR UPDATE;  -- X-lock
SELECT * FROM t WHERE id = 1 LOCK IN SHARE MODE;  -- S-lock
```

### 7.3 Purge

Il **Purge** è il processo che rimuove le vecchie versioni delle righe che non sono più necessarie.

**Quando fare purge**:
- Quando non ci sono più transazioni che possono vedere le vecchie versioni
- Dopo che le transazioni attive sono "passate oltre"

**Purge Thread**:
```sql
-- Numero thread purge (default: 4 in MySQL 8.0+)
SHOW VARIABLES LIKE 'innodb_purge_threads';

-- Batch size per purge
SHOW VARIABLES LIKE 'innodb_purge_batch_size';
-- Default: 300

-- Transazioni da trattenere
SHOW VARIABLES LIKE 'innodb_max_purge_lag';
-- Default: 0 (nessun ritardo)
```

**Problemi con purge lag**:
```sql
-- Se history list è troppo lunga
SHOW ENGINE INNODB STATUS\G
-- cerca "History list length"

-- Causa: transazioni long-running che non fanno commit spesso
-- Soluzione: commit più frequenti, dividere transazioni
```

**Trigger purge manuale**:
```sql
-- In MariaDB
OPTIMIZE TABLE t;  -- rebuild e purge
-- In MySQL 8.0+
SET GLOBAL innodb_redo_log_capacity = 10000000000;  # trigger purge
```

### 7.4 Transaction ID e Rollback

**Transaction ID**:
- Identificatore unico per ogni transazione
- Assegnato quando la transazione acquisisce il primo lock
- Transactions con solo read (consistent read) non acquisiscono trx_id

**Rollback Process**:
```sql
-- Rollback di una transazione
ROLLBACK;

-- InnoDB:
-- 1. Legge i record undo
-- 2. Applica reverse operations
-- 3. Scrive nuovo undo per le inversioni
-- 4. Mark transazione come rolled back
```

**Esempio rollback**:
```
Transazione: UPDATE t SET col = 'new' WHERE col = 'old'

Undo record: (col = 'new') -> (col = 'old')

Rollback:
1. Read undo: "col = new"
2. Reverse: SET col = 'old'
3. Write redo for reversal
4. Mark trx rolled back
```

### 7.5 MVCC e Isolation Levels

**REPEATABLE READ** (default):
- Read view creato una volta, all'inizio della transazione
- Tutte le query vedono lo stesso snapshot
- Non-repeatable reads non possibili

**READ COMMITTED**:
- Nuovo read view prima di ogni statement
- Stessa transazione può vedere dati diversi
- Più flessibile, meno isolamento

```sql
-- READ COMMITTED
START TRANSACTION;
SELECT * FROM t;  -- vede versione snapshot A
-- (altra transazione committa)
SELECT * FROM t;  -- vede versione snapshot B (aggiornata!)
COMMIT;
```

**Impatto performance**:
- REPEATABLE READ: più storage per versioni, più lavoro per purge
- READ COMMITTED: meno versioni, meno storage, migliori performance

---

## 8. Index Structure

### 8.1 B+Tree

InnoDB uses B+Tree:
- Clustered index = primary key
- Secondary indexes point to primary key
- All indexes include transaction ID

### 8.2 Adaptive Hash Index

AHI:
- In-memory hash index
- Automatic for frequent queries
- Partial B+tree indexing

### 8.3 Index Statistics

Statistics:
```sql
ANALYZE TABLE table_name;
SHOW TABLE STATUS LIKE 'table_name';
```

---

## 9. Checkpoint e Recovery

### 9.1 Fuzzy Checkpoint

Checkpoint:
- Dirty pages flushed periodically
- Async to avoid blocking
- Adaptive checkpoint

### 9.2 Recovery Process

Recovery:
1. Identify last checkpoint
2. Read log from checkpoint
3. Apply redo entries
4. Roll back uncommitted

### 9.3 Doublewrite Buffer

Doublewrite:
- Pages written to buffer, then to data files
- Protects against partial writes

---

## 10. Performance Tuning

### 10.1 Buffer Pool

Tuning:
```sql
SET GLOBAL innodb_buffer_pool_size = 4G;
SET GLOBAL innodb_buffer_pool_instances = 4;
```

### 10.2 Log Files

Tuning:
```sql
SET GLOBAL innodb_log_file_size = 512M;
SET GLOBAL innodb_flush_log_at_trx_commit = 1;
-- 1: fsync on commit (default, safe)
-- 2: flush to OS
-- 0: async
```

### 10.3 Thread Tuning

Thread:
```sql
SET GLOBAL innodb_page_cleaners = 4;
SET GLOBAL innodb_purge_threads = 4;
```

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*