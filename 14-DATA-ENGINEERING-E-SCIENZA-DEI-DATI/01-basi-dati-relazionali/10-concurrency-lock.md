# Concurrency Control e Locking

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
1. Fondamenti del Concurrency Control
2. Locking in Database
3. Livelli di Locking
4. Deadlock: Prevenzione e Risoluzione
5. MVCC: Alternativa al Locking
6. Isolation Levels in Pratica
7. Transaction Isolation per Applicazioni
8. Lock Monitoring
9. Optimistic Concurrency Control
10. Best Practices e Anti-Patterns

---

## 1. Fondamenti del Concurrency Control

### 1.1 Perché il Concurrency Control

Il **concurrency control** gestisce l'accesso concorrente ai dati. Senza controllo, le transazioni possono interferire producendo risultati inconsistenti.

Il problema fondamentale: multiple transazioni accessano gli stessi dati contemporaneamente.

### 1.2 Problemi di Concurrency

I **problemi** includono:

**Dirty Read**: Una transazione legge dati non committati da un'altra.

**Non-Repeatable Read**: Una transazione legge lo stesso dato due volte con risultati diversi.

**Phantom Read**: Una transazione esegue la stessa query due volte e trova righe diverse.

**Lost Update**: Due transazioni leggono e aggiornano lo stesso dato, una sovrascrive l'altra.

### 1.3 Obiettivi del Concurrency Control

Gli **obiettivi** sono:

- **Serializzabilità**: Le transazioni sembrano eseguite una alla volta
- **Consistenza**: Il database rimane consistente
- **Throughput**: Massimo accesso concorrente possibile
- **Latenza minima**: Transazioni veloci

### 1.4 Approcci al Concurrency Control

Due approcci principali:

- **Pessimistico (Locking)**: Previene conflitti acquisendo lock prima
- **Ottimistico**: Permette conflitti, li rileva e li risolve

---

## 2. Locking in Database

### 2.1 Tipi di Lock

I **tipi di lock** fondamentali:

**Shared Lock (S)**: Per letture. Multiple transazioni possono avere shared lock.

**Exclusive Lock (X)**: Per scritture. Una sola transazione può avere exclusive lock.

**Compatibility matrix**:
| | S | X |
|---|---|---|
| S | Yes | No |
| X | No | No |

### 2.2 Lock Modes

Diversi **modi di lock**:

- **Row-level**: Lock su singole righe
- **Page-level**: Lock su pagine (8KB)
- **Table-level**: Lock su intere tabelle

### 2.3 Lock Escalation

L'**escalation** converte lock:

- Da row-level a page-level
- Da page-level a table-level

Avviene quando troppi lock di basso livello.

### 2.4 Lock Implementation

I **lock** sono implementati come:

- Spinlocks (per breve durata)
- Latch (protezione strutture)
- Locks (per transazioni)

### 2.5 Lock Manager

Il **lock manager** è un componente del DBMS:

- Mantiene una tabella dei lock attivi
- Gestisce richieste di lock
- Rilascia lock quando non più necessari

---

## 3. Livelli di Locking

### 3.1 Row-Level Locking

Il **row-level locking** blocca singole righe:

```sql
-- PostgreSQL (lock mode)
BEGIN;
UPDATE conti SET saldo = saldo - 100 WHERE id = 1;
-- Lock sulla riga id=1
COMMIT;
```

Vantaggi:
- Massima concorrenza
- Per transazioni OLTP

### 3.2 Page-Level Locking

Il **page-level locking** blocca pagine:

- Meno overhead che row-level
- Meno concorrenza
- Usato da alcuni DBMS legacy

### 3.3 Table-Level Locking

Il **table-level locking** blocca tabelle intere:

```sql
-- MySQL
LOCK TABLES tab WRITE;
-- Solo una transazione alla volta

-- PostgreSQL
LOCK TABLE tab IN ACCESS EXCLUSIVE MODE;
```

Usato per operazioni DDL.

### 3.4 Intent Locks

Gli **intent locks** segnalano lock a livelli superiori:

- **IS** (Intent Shared): Intende acquisire S-lock su righe
- **IX** (Intent Exclusive): Intende acquisire X-lock su righe

Permettono rapida identificazione di conflitti.

### 3.5 Lock Modes in Pratica

Esempi in PostgreSQL:

```sql
-- Row Share
SELECT ... FOR UPDATE;

-- Row Exclusive
UPDATE, DELETE, INSERT

-- Share
VACUUM (solo lettura)

-- Access Exclusive
DROP TABLE, ALTER TABLE
```

---

## 4. Deadlock: Prevenzione e Risoluzione

### 4.1 Cos'è un Deadlock

Un **deadlock** è una situazione circolare:

- Transazione A aspetta lock di B
- Transazione B aspetta lock di A
- Nessuna può procedere

### 4.2 Rilevamento Deadlock

I DBMS rilevano i deadlock:

```sql
-- PostgreSQL: deadlock_timeout
-- SQL Server: lock timeout
-- MySQL: innodb_lock_wait_timeout
```

Il timeout è un approccio.

### 4.3 Grafo di Attesa

I DBMS costruiscono un **waits-for graph**:

- Nodi = transazioni
- Archi = transazioni in attesa

Un ciclo indica deadlock.

### 4.4 Prevenzione Deadlock

La **prevenzione** include:

- Acquisire lock in ordine
- Lock timeout
- Trasaction retry

### 4.5 Risoluzione Deadlock

Quando rilevato:
1. Selezionare una "vittima"
2. Abortire la transazione
3. Rilasciare i lock
4. Ritentare l'operazione

---

## 5. MVCC: Alternativa al Locking

### 5.1 Introduzione al MVCC

**MVCC** (Multiversion Concurrency Control) fornisce isolamento con versioni multiple:

- Ogni transazione vede uno snapshot
- Scritture non bloccano letture
- Letture non bloccano scritture

### 5.2 Implementazione MVCC

In **PostgreSQL**:
- xmin: transazione che ha creato la riga
- xmax: transazione che ha cancellato/modificato

In **MySQL/InnoDB**:
- transaction_id
- roll_pointer

### 5.3 Snapshot Isolation

Con **snapshot isolation**:
- READ COMMITTED: vede i commit prima della query
- REPEATABLE READ: vede i commit prima della transazione

### 5.4 Write Skew

Il **write skew** è un problema MVCC:

- Transazione A legge X e Y
- Transazione B legge X e Y
- A scrive X, B scrive Y
- Risultato: entrambe le modifiche perse

### 5.5 Serializable e MVCC

Per serializzabilità con MVCC:

- **PostgreSQL**: serializable + predicate locks
- **MySQL**: serializable + gap locks

---

## 6. Isolation Levels in Pratica

### 6.1 READ UNCOMMITTED

Il livello **READ UNCOMMITTED**:

- Può leggere dati non committati
- Virtualmente non usato
- Performance massima, protezione minima

### 6.2 READ COMMITTED

Il livello **READ COMMITTED** (default PostgreSQL):

- Legge solo dati committati
- Non-repeatable read possibile
- Bilanciamento buono

### 6.3 REPEATABLE READ

Il livello **REPEATABLE READ** (default MySQL):

- Letti dati consistenti nella transazione
- Phantom read possibile
- Più costoso

### 6.4 SERIALIZABLE

Il livello **SERIALIZABLE**:

- Isolamento totale
- Può causare retry
- Più costoso

### 6.5 Settare Isolation Level

```sql
-- PostgreSQL
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- MySQL
SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- SQL Server
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

---

## 7. Transaction Isolation per Applicazioni

### 7.1 Pattern per OLTP

Per applicazioni **OLTP**:

- Usare READ COMMITTED
- Tenere transazioni brevi
- Evitare interattività prolungata

### 7.2 Pattern per Reporting

Per **reporting**:

- READ ONLY isolation
- Snapshot isolation per consistenza
- Transazioni lunghe accettabili

### 7.3 Locking Applicativo

A volte serve **locking applicativo**:

```sql
-- Seleziona per aggiornamento
SELECT * FROM conti WHERE id = 1 FOR UPDATE;
-- Ora la riga è bloccata
UPDATE conti SET saldo = saldo - 100 WHERE id = 1;
```

### 7.4 Optimistic Locking

Il **locking ottimistico** usa versioni:

```sql
UPDATE tab 
SET col = new_val, version = version + 1 
WHERE id = ? AND version = old_version;
-- Se 0 righe, qualcun altro ha modificato
```

### 7.5 Retry Logic

Implementare **retry logic**:

```sql
MAX_RETRIES = 3
for i in range(MAX_RETRIES):
    try:
        transaction()
        break
    except DeadlockException:
        wait(random_time)
        continue
```

---

## 8. Lock Monitoring

### 8.1 Query Lock Info

Monitorare i **lock**:

```sql
-- PostgreSQL
SELECT * FROM pg_locks;

-- MySQL
SELECT * FROM information_schema.INNODB_LOCKS;

-- SQL Server
SELECT * FROM sys.dm_tran_locks;
```

### 8.2 Blocking Queries

Identificare **query bloccanti**:

```sql
-- PostgreSQL
SELECT * FROM pg_stat_activity WHERE state = 'active' 
AND wait_event_type = 'Lock';
```

### 8.3 Long Running Queries

Trovare **query lunghe**:

```sql
-- PostgreSQL
SELECT * FROM pg_stat_activity 
WHERE state != 'idle' 
AND query_start < NOW() - INTERVAL '5 minutes';
```

### 8.4 Lock Waits

Monitorare le **attese**:

```sql
-- PostgreSQL: pg_stat_activity
SELECT * FROM pg_stat_activity WHERE wait_event IS NOT NULL;
```

### 8.5 Diagnostic Tools

Strumenti diagnostici:
- **PostgreSQL**: pg_stat_activity, pg_locks
- **MySQL**: SHOW ENGINE INNODB STATUS
- **SQL Server**: sp_whoisactive

---

## 9. Optimistic Concurrency Control

### 9.1 Quando Usare OCC

L'**OCC** è appropriato quando:
- Conflitti rari (basso write rate)
- Latenza non accettabile di lock
- Read-heavy workload

### 9.2 Implementazione OCC

Implementare OCC:

```sql
-- 1. Leggi versione
SELECT *, version FROM tab WHERE id = 1;

-- 2. Modifica con version check
UPDATE tab SET col = new_val, version = version + 1 
WHERE id = 1 AND version = old_version;
```

### 9.3 Version Field

Aggiungere **campo version**:

```sql
ALTER TABLE tab ADD COLUMN version INT DEFAULT 1;
```

### 9.4 Conflict Resolution

Quando OCC fallisce:

1. Notifica utente
2. Ricarica dati
3. Mostra conflitto
4. Utente decide: sovrascrivi o annulla

### 9.5 OCC vs Pessimistico

Scegliere tra:

**Ottimistico**: Conflitti rari, preferisce throughput

**Pessimistico**: Conflitti frequenti, preferisce semplicità

---

## 10. Best Practices e Anti-Patterns

### 10.1 Best Practices

Le **best practices**:

- Tenere transazioni brevi
- Accedere ai dati in ordine consistente
- Non tenere lock durante interazione utente
- Monitorare e risolvere deadlock

### 10.2 Anti-Patterns

Gli **anti-patterns**:

- Transazioni lunghe
- Lock non necessari
- Ignorare timeout deadlock
- Non gestire retry

### 10.3 Locking per DDL

Il **DDL locking**:
- Table-level lock di default
- Long-running per modifiche struttura
- Planificare finestre di manutenzione

### 10.4 Isolation in Distributed Systems

Nei **sistemi distribuiti**:
- Two-Phase Commit per transazioni
- Eventual consistency per performance
- Saga pattern per workflow lunghi

### 10.5 Monitoring Continuo

Monitorare sempre:
- Lock wait time
- Deadlock frequency
- Transaction duration
- Contention patterns

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*