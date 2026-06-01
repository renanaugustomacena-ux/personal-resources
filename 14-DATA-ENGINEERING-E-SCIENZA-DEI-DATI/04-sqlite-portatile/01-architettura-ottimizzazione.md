# SQLite Architettura e Ottimizzazione

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
1. SQLite Architecture
2. Storage Engine
3. B-Tree Implementation
4. Query Processing
5. Transaction e Locking
6. WAL Mode
7. Performance Tuning
8. Index Optimization
9. In-Memory Databases
10. Embedded Applications

---

## 1. SQLite Architecture

### 1.1 Core Components

SQLite è un database relazionale embedded che implementa un motore SQL completo in una singola libreria. L'architettura è organizzata in layer ben definiti che lavorano insieme per fornire funzionalità database complete senza dipendenze esterne.

**Frontend**:
Il frontend di SQLite gestisce la preparazione delle query SQL per l'esecuzione. È composto da tre sotto-componenti principali che trasformano la query SQL in un formato eseguibile dalla Virtual Machine. Il tokenizer analizza la stringa SQL in token识别符, identifica parole chiave, operatori, identificatori e letterali. Il parser costruisce un parse tree (albero di sintassi) che rappresenta la struttura grammaticale della query, validando la sintassi e costruendo una rappresentazione interna della query. Il code generator attraversa il parse tree e genera bytecode per la Virtual Machine di SQLite, ottimizzando dove possibile e producendo istruzioni efficienti.

**Virtual Machine**:
La Virtual Machine (VM) di SQLite è il cuore del motore di esecuzione. Non è una VM nel senso tradizionale (come JVM), ma piuttosto un processore di bytecode register-based. La VM ha 0-7 registri per manipolare dati e uno stack per chiamate di funzione. Ogni istruzione del bytecode è un opcode che opera su questi registri. Il B-Tree module gestisce tutte le strutture dati ad albero utilizzate per indici e tabelle. Il Pager gestisce il caricamento e il salvataggio delle pagine dal/disk, implementando anche il caching. Il VFS (Virtual File System) fornisce un layer di astrazione per l'I/O del filesystem, permettendo a SQLite di operare su filesystem diversi.

**Backend**:
Il backend gestisce la memorizzazione persistente e la manipolazione dei dati. Il modulo B-Tree implementa sia B+ tree per indici che B-tree per tabelle. Il page cache memorizza le pagine recentemente usate per ridurre l'I/O disk. I meccanismi di journaling (WAL o rollback journal) gestiscono le transazioni e garantiscono l'atomicità.

### 1.2 Database File Structure

Ogni database SQLite è contenuto in un singolo file che ha una struttura ben definita:

```c
// SQLite database file layout
// Header (100 bytes)
// Schema Root Page
// Data Pages (default 4096 bytes)
```

```
+----------------------------------------------------------+
| SQLite Database File                                     |
+----------------------------------------------------------+
| Header (100 bytes)                                        |
| - "SQLite format 3\0"                                    |
| - Page size (2 bytes)                                    |
| - Write version (1 byte)                                 |
| - Read version (1 byte)                                 |
| - Reserved space (1 byte)                                |
| - Embedded payload fraction (1 byte)                    |
| - Embedded payload fraction (1 byte)                    |
| - File change counter (4 bytes)                         |
| - Database size in pages (4 bytes)                      |
| - First freelist trunk page (4 bytes)                   |
| - Number of freelist pages (4 bytes)                    |
| - Schema cookie (4 bytes)                                |
| - Schema format (4 bytes)                                |
| - Default page cache size (4 bytes)                     |
| - Largest root B-Tree page (4 bytes)                    |
| - Text encoding (1 byte)                                |
| - User version (4 bytes)                                 |
| - Incremental vacuum mode (4 bytes)                     |
| - Application ID (4 bytes)                              |
| - Version-valid-for (4 bytes)                            |
| - SQLite version (4 bytes)                              |
+----------------------------------------------------------+
| B-Tree Root Page (schema)                               |
+----------------------------------------------------------+
| Data Pages (table/indices)                               |
+----------------------------------------------------------+
```

**Page Size**: La dimensione della pagina è configurabile (512, 1024, 2048, 4096, 8192, 16384, 32768 bytes) ma 4096 è il default e raccomandato per la maggior parte dei casi. Ogni pagina ha un numero unico e può essere di diversi tipi: leaf page, internal page, pointer map page, o freelist page.

**Header Details**: Il campo "text encoding" indica la codifica usata: 1 = UTF-8, 2 = UTF-16le, 3 = UTF-16be. La version di SQLite è memorizzata negli ultimi 4 byte del header per verificare la compatibilità.

### 1.3 File Format Deep Dive

Il file header contiene informazioni critiche per l'accesso al database:

```c
// Byte 16-19: Database size in pages
// Se il database è vuoto, questo campo è 0
// Il cambio di questo valore indica modifica della dimensione

// Byte 20-23: First freelist trunk page
// Puntatore alla prima pagina della freelist
// La freelist contiene pagine non più usate

// Byte 24-27: Number of freelist pages
// Numero totale di pagine nella freelist

// Byte 28-31: Schema cookie
// Incrementato ad ogni modifica dello schema
// Usato per invalidare query plan cached
```

### 1.4 Memory Architecture

SQLite utilizza diverse aree di memoria per diversi scopi:

```c
// Aree di memoria principali:
// 1. Page Cache - memorizza pagine del database
// 2. Statement Cache - memorizza query compilate  
// 3. Lookaside Buffer - allocations rapide per tuple
// 4. Scratch Area - memoria temporanea per ordinamento
```

La page cache è configurabile tramite PRAGMA cache_size e può essere in memoria o su disco (per database molto grandi). La statement cache evita la ricompilazione di query usate frequentemente.

---

## 2. Storage Engine

### 2.1 Page-Based Storage

SQLite organizza i dati in pagine di dimensione configurabile. Questo approccio page-based offre un buon bilanciamento tra overhead di I/O e granularità dell'accesso:

```sql
-- Default page size
PRAGMA page_size;

-- Available sizes: 512, 1024, 2048, 4096, 8192, 16384, 32768
-- Attenzione: deve essere settato PRIMA di creare tabelle
-- Se il database non esiste ancora:
PRAGMA page_size = 4096;
-- Poi CREATE TABLE

-- Verificare la page size corrente
PRAGMA page_size;
-- Output: 4096 (default)

-- Database info
PRAGMA database_list;
```

La scelta della page size dipende dal tipo di dati: page più grandi sono più efficienti per grandi record, mentre page più piccole sono migliori per record piccoli e frequenti letture random.

### 2.2 Record Format

Ogni record in SQLite è codificato in un formato compatto chiamato "record format":

```c
// Record format
// Varint: length of payload (n bytes)  -- lunghezza payload
// Varint: rowid (if not primary key)   -- rowid per tabelle senza PK
// Payload: column data                -- dati delle colonne

// Varint: SQLite usa variable-length integers
// Per efficienza di spazio
```

**Varint Encoding**: SQLite usa una codifica variable-length per integers (varint) per minimizzare lo spazio:

```c
// Varint encoding examples:
// 0-127: 1 byte (bit 7 = 0, bits 0-6 = valore)
// 128-16383: 2 byte (primo byte bits 0-6 = parte bassa, bit 7 = 1)
// 16384-2097151: 3 byte
// etc.

// Esempi:
// 0 -> 0x00
// 127 -> 0x7F
// 128 -> 0x80 0x01
// 1000 -> 0x88 0x07
```

Il formato record include:
- Un varint per la lunghezza del payload
- Un varint per il rowid (solo se la tabella non ha INTEGER PRIMARY KEY)
- I dati delle colonne serializzati

### 2.3 Tables as B-Trees

In SQLite, le tabelle sono implementate come B-Tree:

**Table B-Tree** (con INTEGER PRIMARY KEY):
- La chiave del B-Tree è il rowid
- I leaf nodes contengono i record completi
- Searching è O(log n) dove n è il numero di record

**WITHOUT ROWID tables** (SQLite 3.15+):
- La chiave è derivata dalla primary key
- Più efficienti per certain workloads
- Richiedono almeno una primary key

```sql
-- Tabella standard (rowid-based)
CREATE TABLE standard (
    id INTEGER PRIMARY KEY,
    name TEXT
);
-- Internamente: B-Tree con key=rowid

-- Tabella WITHOUT ROWID
CREATE TABLE without_rowid (
    id TEXT PRIMARY KEY,
    name TEXT
) WITHOUT ROWID;
-- Internamente: B-Tree con key=id (non rowid)
```

### 2.4 Index Structure

Gli indici in SQLite sono B-Tree separati:

```sql
-- Index B-Tree:
-- Key = valori della colonna indicizzata
-- Value = rowid della tabella (per lookup)
```

Quando si crea un indice, SQLite crea un nuovo B-Tree dove:
- Le chiavi sono i valori delle colonne indicizzate
- I valori sono i rowid delle righe corrispondenti
- Questo permette lookup O(log n) invece di O(n)

---

## 3. B-Tree Implementation

### 3.1 B-Tree Types in SQLite

SQLite implementa due tipi principali di B-Tree:

**Table B-Tree**:
- Memorizza records di tabella
- Key = rowid (intero)
- Leaf nodes contengono record completi
- Ogni riga ha un entry nel table B-Tree

**Index B-Tree**:
- Memorizza index entries
- Key = valori delle colonne indicizzate
- Value = rowid per puntare alla tabella
- Non contiene i dati, solo puntatori

### 3.2 Page Types

Ogni pagina nel database SQLite ha un tipo specifico:

```sql
-- Vedere page type per debugging
-- Non direttamente accessibile via SQL
-- Ma visibile tramite sqlite3_page_type() in C API

-- I tipi di pagina sono:
-- 0x02 (2): Interior index page
-- 0x05 (5): Interior table page  
-- 0x0A (10): Leaf index page
-- 0x0D (13): Leaf table page
-- 0x1E (30): Pointer map page (auto-vacuum)
-- 0x1F (31): Freelist page
```

**Interior Pages**: Pagine non-leaf che contengono puntatori a pagine figlie e chiavi di separazione. Permettono di navigare l'albero.

**Leaf Pages**: Contengono i dati effettivi (record per table B-Tree, index entries per index B-Tree).

### 3.3 Overflow Pages

Per record che non stanno in una singola pagina, SQLite usa overflow pages:

```sql
-- Per record grandi (> pagina_size/4 circa)
-- Prima pagina contiene header + parte iniziale
-- Overflow pages linked in catena

-- Configurazione overflow
-- Non direttamente configurabile
-- SQLite gestisce automaticamente

-- Limite pratica: un record dovrebbe essere < 1MB
-- Overflow pages non supportate per chiavi < 64 byte
```

### 3.4 B-Tree Operations

Le operazioni base sul B-Tree:

```c
// Pseudo-codice delle operazioni:

// Search: O(log n)
// 1. Partire dalla root page
// 2. Confrontare chiave con chiavi nella pagina
// 3. Seguire puntatore appropriato (child page o leaf)
// 4. Ripetere fino a trovare o determinare assente

// Insert: O(log n) + I/O
// 1. Trovare leaf page appropriata
// 2. Se spazio disponibile: inserire direct
// 3. Se piena: split page, propagare overflow
// 4. Aggiornare parent pages

// Delete: O(log n) + I/O
// 1. Trovare record
// 2. Rimuovere
// 3. Se pagina troppo vuota: coalesce con sibling
// 4. Propagare verso root
```

---

## 4. Query Processing

### 4.1 Query Compiler Pipeline

SQLite processa le query attraverso una pipeline ben definita:

```
SQL String → Tokenizer → Parser → Query Planner → Code Generator → VM Bytecode → Executor
```

**Step 1 - Tokenizer**:
Il tokenizer analizza la stringa SQL e la divide in token. Identifica:
- Keywords (SELECT, INSERT, etc.)
- Identifiers (nomi di tabelle, colonne)
- Operators (=, +, etc.)
- Literals (stringhe, numeri)
- Comments

**Step 2 - Parser**:
Il parser costruisce un parse tree usando una grammatica context-free. Verifica la correttezza sintattica e costruisce una rappresentazione interna della query.

**Step 3 - Query Planner**:
Il planner determina il modo migliore per eseguire la query. Considera:
- Indici disponibili
- Ordine delle tabelle nei JOIN
- Stima dei costi usando statistiche
- Possibili semplificazioni

**Step 4 - Code Generator**:
Il code generator attraversa il parse tree e genera bytecode per la Virtual Machine. Ogni operazione SQL diventa una o più istruzioni VM.

### 4.2 EXPLAIN Query Plans

```sql
-- Vedere il piano di esecuzione
EXPLAIN QUERY PLAN
SELECT * FROM users WHERE name = 'John';

-- Output:
-- id | parent | notused | detail
-- 0  | 0      | 0       | SEARCH TABLE users USING INDEX idx_name (name=?)

EXPLAIN QUERY PLAN
SELECT u.name, o.total 
FROM users u 
JOIN orders o ON u.id = o.user_id;

-- output mostra l'ordine di join e gli indici usati
```

Il piano di query mostra:
- id: ID dell'operazione nel piano
- parent: operazione padre
- notused: se l'operazione non è stata usata
- detail: informazioni specifiche (table scan, index use, etc.)

### 4.3 Query Optimizer

SQLite usa un optimizer basato su costi che stima il costo di diversi piani e sceglie il più economico:

```sql
-- Statistiche per l'optimizer
PRAGMA table_info(users);

-- Output:
-- cid | name | type | notnull | dflt_value | pk
-- 0   | id   | INT  | 0       | NULL       | 1
-- 1   | name | TEXT | 0       | NULL       | 0

PRAGMA index_list(users);
-- Mostra indici esistenti

-- ANALYZE per aggiornare statistiche
ANALYZE;
-- Raccoglie informazioni sulla distribuzione dei dati

-- Vedere statistiche raccolte
PRAGMA index_info(idx_name);
```

L'optimizer considera:
- Numero stimato di righe che saranno processate
- Costo di I/O per letture pagine
- Costo di CPU per valutazione condizioni
- Uso di indici vs table scans

### 4.4 Query Execution

La Virtual Machine di SQLite esegue il bytecode generato:

```c
// VM ha 0-7 registri (storage temporaneo)
// e uno stack per call/return

// Istruzioni VM comuni:
// OpenRead: apre una tabella/index per lettura
// Seek: posiciona il cursore
// Column: legge valore dalla posizione attuale
// ResultRow: ritorna una riga al caller
// Halt: termina l'esecuzione
```

La VM è un processore register-based con:
- Registro 0: usato per risultati
- Registri 1-7: per manipolazione temporanea
- Program counter
- Stack per sub-routine

```
+----------------------------------------------------------+
| SQLite Database File                                     |
+----------------------------------------------------------+
| Header (100 bytes)                                        |
| - "SQLite format 3\0"                                    |
| - Page size (2 bytes)                                    |
| - Write version (1 byte)                                 |
| - Read version (1 byte)                                 |
| - Reserved space (1 byte)                                |
| - Embedded payload fraction (1 byte)                    |
| - Embedded payload fraction (1 byte)                    |
| - File change counter (4 bytes)                         |
| - Database size in pages (4 bytes)                      |
| - First freelist trunk page (4 bytes)                   |
| - Number of freelist pages (4 bytes)                    |
| - Schema cookie (4 bytes)                                |
| - Schema format (4 bytes)                                |
| - Default page cache size (4 bytes)                     |
| - Largest root B-Tree page (4 bytes)                    |
| - Text encoding (1 byte)                                |
| - User version (4 bytes)                                |
| - Incremental vacuum mode (4 bytes)                     |
| - Application ID (4 bytes)                              |
| - Version-valid-for (4 bytes)                            |
| - SQLite version (4 bytes)                              |
+----------------------------------------------------------+
| B-Tree Root Page (schema)                               |
+----------------------------------------------------------+
| Data Pages (table/indices)                               |
+----------------------------------------------------------+
```

---

## 2. Storage Engine

### 2.1 Page-Based Storage

SQLite organizza i dati in pagine di dimensione configurabile:

```sql
-- Default page size
PRAGMA page_size;

-- Available sizes: 512, 1024, 2048, 4096, 8192, 16384, 32768
PRAGMA page_size = 4096;

-- Create new DB with specific size
-- (must be done before any tables are created)
```

### 2.2 Record Format

```c
// Record format
// Varint: length of payload (n bytes)
// Varint: rowid (if not primary key)
// Payload: column data
```

**Varint**: SQLite uses variable-length integers for efficiency:

```c
// Varint encoding examples:
// 0-127: 1 byte
// 128-16383: 2 bytes
// 16384-2097151: 3 bytes
// etc.
```

### 2.3 Tables as B-Trees

```sql
-- Internal table B-Tree structure:
-- - Key = rowid (INTEGER PRIMARY KEY)
-- - Value = record data

-- WITHOUT ROWID tables:
-- - Key = computed from primary key
-- - Value = record data
```

---

## 3. B-Tree Implementation

### 3.1 B-Tree Types

SQLite implementsa due tipi di B-Tree:

**Table B-Tree**:
- Memorizza records di tabella
- Key = rowid
- Leaf nodes contengono record completi

**Index B-Tree**:
- Memorizza index entries
- Key = index key
- Value = rowid (pointer to table)

### 3.2 Page Types

```sql
-- Interior index page
-- Interior table page  
-- Leaf index page
-- Leaf table page
-- Pointer map page (for auto-vacuum)
-- Freelist page
```

### 3.3 Overflow Pages

```sql
-- For large records
-- First page contains header + initial data
-- Overflow pages linked via pointer
-- Configurable with PRAGMA
PRAGMA hard_heap_limit = 0;  -- No limit
```

---

## 4. Query Processing

### 4.1 Query Compiler

```sql
-- SQLite query pipeline:
-- 1. Parse -> AST
-- 2. Analyze -> Query Plan
-- 3. Generate -> VM Bytecode
-- 4. Execute -> Results
```

### 4.2 EXPLAIN Query Plans

```sql
-- See query plan
EXPLAIN QUERY PLAN
SELECT * FROM users WHERE name = 'John';

-- Output format:
-- id | parent | notused | detail
-- 0  | 0      | 0       | SEARCH TABLE users USING INDEX idx_name (name=?)
```

### 4.3 Query Optimizer

```sql
-- Statistics
PRAGMA table_info(users);
PRAGMA index_list(users);

-- ANALYZE to update statistics
ANALYZE;
```

---

## 5. Transaction e Locking

### 5.1 Transaction Types

```sql
-- DEFERRED (default)
BEGIN;
-- Lock acquired when needed

-- IMMEDIATE
BEGIN IMMEDIATE;
-- Acquire RESERVED lock immediately

-- EXCLUSIVE
BEGIN EXCLUSIVE;
-- Acquire EXCLUSIVE lock immediately
```

### 5.2 Lock Levels

```sql
-- UNLOCKED: No locks
-- SHARED: Read access (multiple allowed)
-- RESERVED: Will write, read allowed
-- PENDING: Waiting for exclusive, allow readers
-- EXCLUSIVE: Write access
```

### 5.3 Journal Modes

```sql
-- DELETE (default)
-- - Rename old to journal
-- - Write to journal
-- - Commit

-- TRUNCATE
-- - Truncate journal to 0

-- PERSIST
-- - Keep journal file

-- MEMORY
-- - Keep journal in memory

-- WAL (Write-Ahead Logging)
-- - See dedicated section
```

---

## 6. WAL Mode

### 6.1 WAL Overview

Write-Ahead Logging (WAL) provides better concurrency:

```sql
-- Enable WAL
PRAGMA journal_mode = WAL;

-- Checkpoint settings
PRAGMA wal_autocheckpoint = 1000;  -- pages

-- Synchronous mode
PRAGMA synchronous = NORMAL;  -- 0=OFF, 1=NORMAL, 2=FULL, 3=EXTRA
```

### 6.2 WAL Structure

```
+------------------------------------------+
| Main Database File (.db)                 |
+------------------------------------------+
| - Header                                 |
| - B-Tree pages                          |
+------------------------------------------+

+------------------------------------------+
| WAL File (.db-wal)                      |
+------------------------------------------+
| - Frame header (24 bytes)                |
| - Page data                              |
+------------------------------------------+

+------------------------------------------+
| SHM File (.db-shm)                      |
+------------------------------------------+
| - Shared memory for WAL index           |
+------------------------------------------+
```

### 6.3 WAL Operations

```sql
-- Checkpoint
PRAGMA wal_checkpoint(PASSIVE);  -- TRUNCATE, FULL, or PASSIVE
CHECKPOINT;

-- Lock WAL
BEGIN EXCLUSIVE;  -- blocks writers, allows readers
```

## 5. Transaction e Locking

### 5.1 Transaction Types

SQLite supporta tre tipi di transazione con comportamenti di locking diversi:

```sql
-- DEFERRED (default)
BEGIN;
-- Nessun lock acquisito immediatamente
-- SHARED lock acquisito quando necessario
-- RESERVED quando scrittura
-- Più tollerante per conflitti

-- IMMEDIATE
BEGIN IMMEDIATE;
-- Acquire RESERVED lock immediatamente
-- Altri writer bloccati
-- Utile per transazioni brevi

-- EXCLUSIVE
BEGIN EXCLUSIVE;
-- Acquire EXCLUSIVE lock subito
-- Nessun altro accesso possibile
-- Per operazioni che devono essere sole
```

La differenza principale è quando SQLite acquisisce i lock. In modalità DEFERRED, SQLite aspetta fino al primo accesso effettivo ai dati per acquisire lock, mentre IMMEDIATE e EXCLUSIVE acquisiscono lock prima.

### 5.2 Lock Levels

SQLite implementa un sistema di locking a 5 livelli per gestire la concorrenza:

```sql
-- UNLOCKED: Nessun lock attivo
-- - Nessuna transazione attiva
-- - Database modificabile da chiunque

-- SHARED: Lock di lettura
-- - Multiple transazioni possono leggere
-- - Acquisito quando legge dati
-- - Non impedisce altre letture
-- - BLOCKED da: RESERVED, PENDING, EXCLUSIVE

-- RESERVED: Lock futuro di scrittura  
-- - Una transazione scriverà
-- - Altre letture permesse
-- - BLOCKED da: EXCLUSIVE (se altro RESERVED)
-- - HOLDERS: solo una transazione alla volta

-- PENDING: In attesa di EXCLUSIVE
-- - Transazione vuole scrivere ma bloccata
-- - Permette letture esistenti
-- - BLOCKED da: SHARED (aspetta lettori finire)
-- - Bloccherà nuovi reader

-- EXCLUSIVE: Lock di scrittura
-- - Solo una transazione può accedere
-- - Necessario per scrivere
-- - BLOCKED da: qualsiasi altro lock
```

### 5.3 Journal Modes

SQLite supporta diversi modi di gestire il journal per le transazioni:

```sql
-- DELETE (default in SQLite 3)
-- Vecchio database rinominato a .db-journal
-- Nuovo journal creato per transazione
-- On commit: journal rinominato eliminato
-- On crash: .db-journal contiene da applicare

-- TRUNCATE
-- Come DELETE ma trunka journal a 0
-- Più veloce su alcuni filesystem

-- PERSIST
-- Come DELETE ma mantiene file journal
-- Evita ricreazione file

-- MEMORY
-- Tiene journal in RAM
-- Più veloce ma NON CRASH-SAFE
-- Usare solo per dati temporanei

-- WAL (Write-Ahead Logging) - RACCOMANDATO
-- Modifiche scritte prima in WAL file
-- Commit immediato senza modificare main file
-- Checkpoint periodico sposta in main file
-- Permette letture concurrenti
-- Vedi sezione dedicata sotto

-- Impostare journal mode
PRAGMA journal_mode = WAL;
PRAGMA journal_mode = DELETE;
```

### 5.4 Transaction Guarantees

SQLite fornisce garanzie ACID per le transazioni:

```sql
-- Atomicità
-- Tutte le operazioni nella transazione succeedono o falliscono insieme
-- Implementato via rollback journal

-- Consistenza
-- Database sempre in stato valido
-- Vincoli verificati alla fine della transazione

-- Isolamento
-- Transazioni concurrenti isolate tra loro
-- Ma: SQLite usa "serializable" semantics per default

-- Durabilità
-- Dati scritti su disco al commit
-- Ma: PRAGMA synchronous influenza questo
```

---

## 6. WAL Mode

### 6.1 WAL Overview

WAL (Write-Ahead Logging) è il metodo di journaling raccomandato per SQLite. Offre migliore concorrenza rispetto ai metodi tradizionali:

```sql
-- Abilitare WAL
PRAGMA journal_mode = WAL;

-- Verificare modalità corrente
PRAGMA journal_mode;
```

**Con WAL**:
- Scritture vanno in WAL file separato (.db-wal)
- Letture possono procedere dal main file
- Commit è più veloce (non riscrive main)
- Checkpoint sposta da WAL a main

### 6.2 WAL Structure

```
+------------------------------------------+
| Main Database File (.db)                 |
+------------------------------------------+
| - Header                                 |
| - B-Tree pages (non modificati durante WAL)
+------------------------------------------+

+------------------------------------------+
| WAL File (.db-wal)                      |
+------------------------------------------+
| - Frame header (24 bytes)              |
| - Page data                              |
| - Frames sono appesi sequenzialmente    |
+------------------------------------------+

+------------------------------------------+
| SHM File (.db-shm)                      |
+------------------------------------------+
| - Shared memory per WAL index           |
| - Indice delle posizioni nei frame      |
| - Permette accesso condiviso            |
+------------------------------------------+
```

Ogni frame nel WAL consiste di:
- Header (24 bytes): frame number, size, checksum
- Page data (4KB): la pagina modificata

### 6.3 WAL Operations

```sql
-- Checkpoint: copia da WAL a main database
PRAGMA wal_checkpoint(PASSIVE);  -- non blocca, ritorna subito
PRAGMA wal_checkpoint(FULL);     -- blocca fino a complete
PRAGMA wal_checkpoint(TRUNCATE); -- FULL + truncate WAL

-- 也可以 chiamare come funzione
SELECT wal_checkpoint();

-- Auto-checkpoint (default: 1000 pages)
PRAGMA wal_autocheckpoint = 1000;

-- Synchronous level per WAL
PRAGMA synchronous = NORMAL;  -- default,平衡 performance/safety
PRAGMA synchronous = FULL;   -- massima safety, più lento
PRAGMA synchronous = OFF;    -- nessun sync, veloce ma rischioso
```

### 6.4 WAL Advantages

**Concorrenza di lettura**:
- Lettori non bloccano scrittori
- Scrittori non bloccano lettori
- Molto utile per applicazioni con mix read/write

**Velocità di scrittura**:
- Scritture sequentiali al WAL invece di random-write al DB
- Commit più veloce (non necesita fsync del main file)
- Better per SSD

**Recovery**:
- WAL contiene tutte le modifiche non ancora checkpointed
- Recovery veloce: replay WAL da checkpoint
- Nessuna perdita di dati (con synchronous appropriato)

---

## 7. Performance Tuning

### 7.1 PRAGMA Settings

SQLite ha numerose PRAGMA per ottimizzare performance:

```sql
-- Cache size (default: -2000 = 2MB)
-- Valore negativo = KB, positivo = pagine
PRAGMA cache_size = -4000;  -- 4MB cache
PRAGMA cache_size = 10000; -- 10000 pagine (~40MB)

-- Temp store
PRAGMA temp_store = MEMORY;  -- più veloce per grandi operazioni
PRAGMA temp_store = FILE;    -- default, usa disco

-- Locking mode
PRAGMA locking_mode = NORMAL;  -- rilascia lock tra transazioni
PRAGMA locking_mode = EXCLUSIVE; -- mantiene lock

-- Page size
-- Da settare PRIMA di creare il database
-- Non modificabile dopo senza ricreare DB
PRAGMA page_size = 4096; -- default, ottimo per la maggior parte

-- mmap (memory-mapped I/O)
-- Legge direttamente da file in memoria
-- Più veloce per read-heavy workload
PRAGMA mmap_size = 268435456; -- 256MB
PRAGMA mmap_size = 0; -- disable per write-heavy
```

### 7.2 Schema Optimization

Ottimizzare lo schema per le query comuni:

```sql
-- Creare indici per query frequenti
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status_date ON orders(status, order_date);

-- Covering indexes (tutti i dati nella index)
CREATE INDEX idx_users_email_name 
ON users(email, name); -- SELECT email, name FROM users WHERE email=?

-- Partial indexes (solo subset di dati)
CREATE INDEX idx_active_orders 
ON orders(order_date) 
WHERE status = 'active';

-- Composite index ordine colonne
-- Per query: WHERE a = ? AND b = ?
-- Create: (a, b) non (b, a)
CREATE INDEX idx ON table(a, b);

-- Verifica uso indici
EXPLAIN QUERY PLAN 
SELECT * FROM orders WHERE customer_id = 1;
```

### 7.3 Query Optimization

```sql
-- Usare EXPLAIN ANALYZE per vedere tempi reali
EXPLAIN ANALYZE 
SELECT * FROM users WHERE email = 'test@example.com';

-- Evitare SELECT *
-- Specificare solo le colonne necessarie
SELECT name, email FROM users;

-- LIMIT per keyset pagination
-- invece di OFFSET (lento per grandi offset)
-- Prima query:
SELECT * FROM users ORDER BY id LIMIT 10;
-- Query successive:
SELECT * FROM users WHERE id > 10 ORDER BY id LIMIT 10;

-- Usare LIKE con % alla fine (prefix search)
-- LIKE 'abc%' usa index
-- LIKE '%abc%' non usa index

-- Batch INSERT/DELETE
-- Invece di molte piccole operazioni:
INSERT INTO logs VALUES ('a'), ('b'), ('c'), ...;
DELETE FROM cache WHERE id IN (1, 2, 3, ...);
```

### 7.4 PRAGMA per Performance

```sql
-- Compile options
PRAGMA compile_options;

-- Query-only (read-only mode)
PRAGMA query_only = ON;

-- Read uncommitted isolation
PRAGMA read_uncommitted = 1;

-- Cache hits/misses
PRAGMA cache_hit;
PRAGMA cache_miss;

-- Database stats
PRAGMA page_count;
PRAGMA page_size;
PRAGMA freelist_count;
```

---

## 8. Index Optimization

### 8.1 Index Types

SQLite supporta diversi tipi di indice:

```sql
-- Single column index
CREATE INDEX idx_users_email ON users(email);

-- Unique index
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Composite index
CREATE INDEX idx_orders_cust_date 
ON orders(customer_id, order_date);

-- Expression index
CREATE INDEX idx_lower_email ON users(LOWER(email));

-- Partial index
CREATE INDEX idx_active 
ON users(email) 
WHERE status = 'active';

-- Descending index (solo SQLite 3.30+)
CREATE INDEX idx_date_desc ON events(event_date DESC);
```

### 8.2 Index Usage

```sql
-- Vedere se un index viene usato
EXPLAIN QUERY PLAN 
SELECT * FROM users WHERE email = 'john@example.com';

-- Forzare uso di un index
SELECT * FROM users INDEXED BY idx_users_email 
WHERE email = 'john@example.com';

-- Disabilitare index (per testing)
SELECT * FROM users NOT INDEXED 
WHERE email = 'john@example.com';

-- Vedere tutti gli indici
PRAGMA index_list(users);
PRAGMA index_info(idx_users_email);
```

### 8.3 Index Maintenance

```sql
-- Rebuild index (se corrotto o frammentato)
REINDEX idx_users_email;

-- ANALYZE per aggiornare statistiche
ANALYZE;
-- Dopo ANALYZE, query planner ha info aggiornate

-- Vedere dimensione indici
-- Index è contenuto nel database file
PRAGMA page_count;
-- Confrontare prima e dopo CREATE INDEX
```

### 8.4 When NOT to Index

```sql
-- Non creare indici su:
-- - Colonne con pochi valori unici (low cardinality)
-- - Tabelle molto piccole (full scan più veloce)
-- - Colonne aggiornate frequentemente (overhead write)
-- - Query che non usano WHERE/JOIN/ORDER BY

-- Esempio: status con 3 valori
-- Se la maggior parte delle query è "WHERE status = ?"
-- probabilmente è ok avere index
-- Ma se query è "WHERE status != 'deleted'" l'index non aiuta
```

---

## 9. In-Memory Databases

### 9.1 Memory Database

SQLite può operare interamente in RAM:

```sql
-- Database in-memory
:memory:

-- Equivalente a:
PRAGMA journal_mode = MEMORY;
-- Crea database temporaneo

-- Connect a named in-memory DB
ATTACH DATABASE ':memory:' AS memdb;
-- Più sessioni possono condividerlo
```

### 9.2 Named In-Memory with Cache Sharing

```sql
-- Shared cache per in-memory
PRAGMA cache_size = -2000;  -- 2MB
PRAGMA read_uncommitted = 1;
ATTACH DATABASE 'file::memory:?cache=shared' AS shared_db;

-- Questo permette a multiple connessioni
-- di condividere lo stesso database in-memory
```

### 9.3 Use Cases

```sql
-- Cache applicativa
-- Tenere dati frequently accessed in memoria

-- Testing
-- Database pulito per ogni test

-- Temporary processing
-- Large aggregazioni senza scrivere disk

-- Session storage
-- Dati di sessione temporanei
```

---

## 10. Embedded Applications

### 10.1 C API

L'API C è la base per tutte le altre:

```c
#include <sqlite3.h>

int main() {
    sqlite3 *db;
    char *err_msg = 0;
    
    // Aprire/creare database
    int rc = sqlite3_open("mydb.sqlite", &db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(db));
        return 1;
    }
    
    // Creare tabella
    const char *sql = "CREATE TABLE users ("  \
        "id INTEGER PRIMARY KEY," \
        "name TEXT NOT NULL," \
        "email TEXT UNIQUE" \
    ");";
    
    rc = sqlite3_exec(db, sql, 0, 0, &err_msg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", err_msg);
        sqlite3_free(err_msg);
    }
    
    // Inserire dati (raw SQL - attento a SQL injection!)
    sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com');";
    rc = sqlite3_exec(db, sql, 0, 0, &err_msg);
    
    // Query con prepared statement
    sqlite3_stmt *stmt;
    const char *query = "SELECT id, name, email FROM users WHERE id = ?";
    
    rc = sqlite3_prepare_v2(db, query, -1, &stmt, 0);
    if (rc == SQLITE_OK) {
        sqlite3_bind_int(stmt, 1, 1);  // bind param
        
        while (sqlite3_step(stmt) == SQLITE_ROW) {
            int id = sqlite3_column_int(stmt, 0);
            const char *name = (const char*)sqlite3_column_text(stmt, 1);
            const char *email = (const char*)sqlite3_column_text(stmt, 2);
            printf("User: %d, %s, %s\n", id, name, email);
        }
    }
    sqlite3_finalize(stmt);
    
    // Chiudere
    sqlite3_close(db);
    return 0;
}
```

### 10.2 Prepared Statements

I prepared statement sono essenziali per performance e sicurezza:

```c
// Create prepared statement
sqlite3_prepare_v2(db, "INSERT INTO users (name) VALUES (?)", -1, &stmt, 0);

// Bind parameters
sqlite3_bind_text(stmt, 1, "John", -1, SQLITE_TRANSIENT);
// Nota: SQLITE_TRANSIENT = copia i dati, 
//        SQLITE_STATIC = usa puntatore

// Execute repeatedly
for (int i = 0; i < 1000; i++) {
    sqlite3_bind_text(stmt, 1, names[i], -1, SQLITE_TRANSIENT);
    sqlite3_step(stmt);
    sqlite3_reset(stmt);  // clear bindings
}

// Cleanup
sqlite3_finalize(stmt);
```

### 10.3 Binding Parameters

```c
// Tipi di bind:
sqlite3_bind_null(stmt, 1);
sqlite3_bind_int(stmt, 1, 123);
sqlite3_bind_int64(stmt, 1, 123456789);
sqlite3_bind_double(stmt, 1, 123.456);
sqlite3_bind_text(stmt, 1, "text", -1, SQLITE_TRANSIENT);
sqlite3_bind_blob(stmt, 1, data, size, SQLITE_TRANSIENT);

// Leggere risultati:
sqlite3_column_int(stmt, 0);
sqlite3_column_text(stmt, 0);
sqlite3_column_double(stmt, 0);
sqlite3_column_type(stmt, 0);  // tipo del dato
```

### 10.4 Performance Tips per App Embedded

```c
// 1. Usa transactions per bulk operations
sqlite3_exec(db, "BEGIN", 0, 0, 0);
for (...) { /* insert */ }
sqlite3_exec(db, "COMMIT", 0, 0, 0);

// 2. Usa PRAGMA per ottimizzazione
sqlite3_exec(db, "PRAGMA synchronous = OFF", 0, 0, 0);
sqlite3_exec(db, "PRAGMA journal_mode = MEMORY", 0, 0, 0);
sqlite3_exec(db, "PRAGMA cache_size = 10000", 0, 0, 0);

// 3. Prepared statements riutilizzati
// Crea una volta, usa molte volte

// 4. Close connection quando non serve
sqlite3_close(db);  // rilascia risorse

// 5. Usa VACUUM per recuperare spazio
sqlite3_exec(db, "VACUUM", 0, 0, 0);
```

### 7.2 Schema Optimization

```sql
-- Index creation
CREATE INDEX idx_users_email ON users(email);

-- Composite index
CREATE INDEX idx_orders_customer_date 
ON orders(customer_id, order_date);

-- Covering index
CREATE INDEX idx_users_name_email 
ON users(name, email);
-- Now: SELECT name, email FROM users WHERE name = 'John'
```

### 7.3 Query Optimization

```sql
-- Use EXPLAIN to check plans
EXPLAIN QUERY PLAN 
SELECT * FROM users WHERE email = 'test@example.com';

-- Use covering indexes for SELECT
-- Avoid: SELECT * 
-- Prefer: SELECT needed_columns

-- Use LIMIT for pagination
SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 100000;
-- Better: WHERE id > last_seen_id LIMIT 10
```

---

## 8. Index Optimization

### 8.1 Index Types

```sql
-- Single column
CREATE INDEX idx_users_email ON users(email);

-- Composite
CREATE INDEX idx_orders ON orders(customer_id, order_date);

-- UNIQUE
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Partial (SQLite 3.15+)
CREATE INDEX idx_users_active ON users(email) 
WHERE status = 'active';
```

### 8.2 Index Usage

```sql
-- Check index usage
EXPLAIN QUERY PLAN 
SELECT * FROM users WHERE email = 'test@test.com';

-- Force index usage
SELECT * FROM users INDEXED BY idx_users_email 
WHERE email = 'test@test.com';

-- Disable index usage (for testing)
SELECT * FROM users NOT INDEXED WHERE email = 'test@test.com';
```

### 8.3 Index Maintenance

```sql
-- REINDEX to rebuild corrupted indexes
REINDEX idx_users_email;

-- ANALYZE to update statistics
ANALYZE users;

-- Check index info
PRAGMA index_info(idx_users_email);
PRAGMA index_list(users);
```

---

## 9. In-Memory Databases

### 9.1 Memory Database

```sql
-- Create in-memory database
:memory:
-- or
PRAGMA journal_mode = MEMORY;

-- Use case: caching, testing, temp tables
CREATE TEMP TABLE temp_data AS SELECT * FROM large_table;
```

### 9.2 Named Memory Databases

```sql
-- Named in-memory DB
ATTACH ':memory:' AS memdb;

-- Or with cache
PRAGMA cache_size = -4000;
ATTACH DATABASE 'file::memory:?cache=shared' AS shared_db;
```

---

## 10. Embedded Applications

### 10.1 Application Integration

```c
// C API example
#include <sqlite3.h>

int main() {
    sqlite3 *db;
    sqlite3_open("mydb.sqlite", &db);
    
    sqlite3_exec(db, "CREATE TABLE t(a TEXT)", NULL, NULL, NULL);
    sqlite3_exec(db, "INSERT INTO t VALUES('hello')", NULL, NULL, NULL);
    
    sqlite3_close(db);
    return 0;
}
```

### 10.2 Binding Parameters

```c
// Prepared statements
sqlite3_prepare_v2(db, "INSERT INTO t VALUES(?)", -1, &stmt, NULL);
sqlite3_bind_text(stmt, 1, "value", -1, SQLITE_TRANSIENT);
sqlite3_step(stmt);
sqlite3_finalize(stmt);
```

### 10.3 Performance Tips

```c
// Use transactions for bulk inserts
sqlite3_exec(db, "BEGIN", 0, 0, 0);
for (i = 0; i < 10000; i++) {
    sqlite3_exec(db, "INSERT ...", 0, 0, 0);
}
sqlite3_exec(db, "COMMIT", 0, 0, 0);

// Use PRAGMA synchronous = OFF for speed
// Use PRAGMA journal_mode = MEMORY
// Use batch inserts with multi-row VALUES
```

---

*Questo documento fa parte del modulo 04 "SQLite Portatile" della Data Encyclopedia.*