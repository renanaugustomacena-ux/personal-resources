# Transazioni ACID: Atomicity, Consistency, Isolation, Durability

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
1. Il Modello ACID
2. Atomicità in Profondità
3. Consistenza del Database
4. Isolamento delle Transazioni
5. Durabilità e Recovery
6. Isolation Levels
7. Concurrency Control
8. Distributed Transactions
9. Transazioni Long-Running
10. Anti-Patterns e Best Practices

---

## 1. Il Modello ACID

### 1.1 Fondamenti delle Transazioni ACID

Il modello **ACID** definisce le proprietà fondamentali che un sistema di gestione database deve garantire per le transazioni. Sviluppato negli anni '80, ACID rimane lo standard per i database relazionali.

Le quattro proprietà ACID sono:

**Atomicity (Atomicità)**: Una transazione è un'unità atomica - o tutte le sue operazioni vengono completate, o nessuna viene applicata. Non esistono stati parziali.

**Consistency (Consistenza)**: Una transazione deve portare il database da uno stato valido a un altro stato valido. Tutti i vincoli devono essere rispettati.

**Isolation (Isolamento)**: Le transazioni concurrenti devono essere eseguite come se fossero sequenziali. Gli effetti di una transazione non devono essere visibili ad altre transazioni fino al commit.

**Durability (Durabilità)**: Una volta committata, una transazione deve persistere permanentemente, anche in caso di fallimento del sistema.

### 1.2 Perché ACID è Importante

ACID è essenziale per applicazioni che richiedono **affidabilità**:

- **Sistemi finanziari**: Transazioni atomiche garantiscono che bonifici e pagamenti siano completi
- **E-commerce**: Ordini atomici evitano stati inconsistenti
- **Sistemi di prenotazione**: Prenotazioni isolate prevengono doppie assegnazioni

I database NoSQL spesso sacrificano ACID per **scalabilità**, ma i sistemi relazionali mantengono ACID come priorità.

### 1.3 ACID nei Database Moderni

I database moderni implementano ACID attraverso meccanismi sofisticati:

- **Write-Ahead Logging (WAL)**: Tutte le modifiche sono loggate prima di essere applicate
- **MVCC**: Multiple Version Concurrency Control per isolamento
- **Checkpoint e recovery**: Per durabilità
- **Lock manager**: Per controllo di concorrenza

---

## 2. Atomicità in Profondità

### 2.1 Implementazione dell'Atomicità

L'atomicità è implementata attraverso il **logging**:

Ogni operazione nella transazione genera record di log che descrivono:
- La modifica apportata
- Il valore precedente (before image)
- Il nuovo valore (after image)

Se la transazione viene committata, i record "commit" sono scritti.
Se la transazione viene abortita, le operazioni vengono annullate usando le before image.

### 2.2 Commit e Rollback

Il **commit** rende le modifiche permanenti:
```sql
BEGIN;
UPDATE conti SET saldo = saldo - 100 WHERE id = 1;
UPDATE conti SET saldo = saldo + 100 WHERE id = 2;
COMMIT;
```

Il **rollback** annulla le modifiche:
```sql
BEGIN;
UPDATE conti SET saldo = saldo - 100 WHERE id = 1;
-- Qualcosa va wrong
ROLLBACK; -- Tutte le modifiche annullate
```

### 2.3 Partial Rollback con Savepoint

I **savepoint** permettono rollback parziali:

```sql
BEGIN;
INSERT INTO ordini (...) VALUES (...);
SAVEPOINT punto1;
INSERT INTO dettagli (...); -- Fallisce
ROLLBACK TO SAVEPOINT punto1; -- Annulla solo l'ultimo inserimento
-- Il primo inserimento rimane
COMMIT;
```

### 2.4 Transazioni Implicite vs Esplicite

Le **modalità** di transazione variano:

```sql
-- Autocommit (ogni statement è una transazione)
SET autocommit = ON;

-- Transazione esplicita
BEGIN;
-- operazioni
COMMIT;
```

### 2.5 Error Handling e Rollback

La gestione degli **errori** deve includere il rollback:

```sql
BEGIN;
TRY:
    UPDATE conti SET saldo = saldo - 100 WHERE id = 1;
    UPDATE conti SET saldo = saldo + 100 WHERE id = 2;
    COMMIT;
CATCH:
    ROLLBACK;
    THROW;
```

---

## 3. Consistenza del Database

### 3.1 Vincoli di Integrità

La **consistenza** è mantenuta attraverso vincoli:

- **Domain constraints**: Tipo e dominio delle colonne
- **Key constraints**: Primary key, unique
- **Referential integrity**: Foreign keys
- **Check constraints**: Condizioni personalizzate

```sql
ALTER TABLE ordini 
ADD CONSTRAINT totale_positivo CHECK (totale >= 0);
```

### 3.2 Trigger per Consistenza

I **trigger** possono implementare regole complesse:

```sql
CREATE TRIGGER check_saldo
AFTER UPDATE ON conti
FOR EACH ROW
BEGIN
    IF NEW.saldo < 0 THEN
        RAISE EXCEPTION 'Saldo non può essere negativo';
    END IF;
END;
```

### 3.3 Consistency During Recovery

Durante il **recovery**, la consistenza è verificata:

1. Le transazioni non committate sono rollbackate
2. I vincoli sono verificati
3. Il database è portato a uno stato consistente

### 3.4 Delayed Constraint Validation

I **vincoli differibili** permettono verifica ritardata:

```sql
ALTER TABLE ordini 
ADD CONSTRAINT fk_cliente FOREIGN KEY (cliente_id) REFERENCES clienti(id)
DEFERRABLE INITIALLY DEFERRED;
```

---

## 4. Isolamento delle Transazioni

### 4.1 Problemi di Concurrency

Le transazioni concurrenti possono avere problemi:

**Dirty Read**: Leggere dati non ancora committati.

**Non-Repeatable Read**: Leggere lo stesso dato due volte con risultati diversi.

**Phantom Read**: Leggere righe diverse in due letture.

### 4.2 MVCC: Multiversion Concurrency Control

Il **MVCC** fornisce isolamento attraverso versioni multiple:

- Ogni transazione vede uno snapshot del database
- Le scritture non bloccano le letture
- Le letture non bloccano le scritture

In PostgreSQL con MVCC:
- L'isolamento predefinito è READ COMMITTED
- Ogni transazione vede le modifiche committate prima del suo inizio

### 4.3 Snapshot Isolation

La **snapshot isolation** garantisce:
- Transazioni read-only vedono uno snapshot consistente
- Transazioni write-write sono serializzate
- Non ci sono dirty read o non-repeatable read

**Write Skew**: Problema dove due transazioni leggono e modificano dati sovrapposti.

### 4.4 Locking per Isolamento

Il **locking** tradizionale fornisce isolamento:
- Lock condivisi per letture
- Lock esclusivi per scritture
- Serializzabilità attraverso lock appropriati

### 4.5 Performance vs Isolation

L'**isolamento elevato** ha costo in performance:

- SERIALIZABLE: massima garanzia, massimo blocco
- READ COMMITTED: buon bilanciamento
- READ UNCOMMITTED: massima concorrenza, minima protezione

---

## 5. Durabilità e Recovery

### 5.1 Write-Ahead Logging (WAL)

Il **WAL** garantisce la durabilità:

1. Le modifiche sono scritte nel log prima di essere applicate
2. Il log è sincronizzato su disco prima del commit
3. Dopo un crash, il log può essere riprodotto

### 5.2 Checkpoint

I **checkpoint** sono punti di sync:

- Tutte le pagine dirty sono scritte
- Il log può essere troncato dopo il checkpoint
- Riduce il tempo di recovery

### 5.3 Recovery Procedures

Il **recovery** dopo crash:

1. **Analysis**: Determina transazioni attive
2. **Redo**: Ripete operazioni committate
3. **Undo**: Annulla operazioni non committate

### 5.4 Durabilità Asincrona

La **durabilità ritardata** migliora performance:

```sql
-- PostgreSQL: commit asincrono
synchronous_commit = off;
```

Questo rischia di perdere transazioni in caso di crash.

### 5.5 Durabilità in Database Distribuiti

Nei **sistemi distribuiti**, la durabilità è più complessa:

- **Synchronous replication**: Tutti i nodi confermano
- **Quorum writes**: Maggioranza dei nodi
- **Async replication**: Rischio di perdita dati

---

## 6. Isolation Levels

### 6.1 READ UNCOMMITTED

Il livello **READ UNCOMMITTED**:
- Permette dirty reads
- Minimale protezione
- Raramente usato in produzione

```sql
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
```

### 6.2 READ COMMITTED

Il livello **READ COMMITTED** (default in PostgreSQL, MySQL):
- Legge solo dati committati
- Non-repeatable reads possibili
- Buon bilanciamento

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

### 6.3 REPEATABLE READ

Il livello **REPEATABLE READ**:
- Garanzia di lettura consistente
- Phantom reads possibili
- Più costoso di READ COMMITTED

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

### 6.4 SERIALIZABLE

Il livello **SERIALIZABLE**:
- Massima garanzia di isolamento
- Transazioni sembrano seriali
- Può causare conflitti e abort

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

### 6.5 Isolation Levels per DBMS

| DBMS | Default | Livelli Supportati |
|------|---------|-------------------|
| PostgreSQL | READ COMMITTED | READ COMMITTED, REPEATABLE READ, SERIALIZABLE |
| MySQL/InnoDB | REPEATABLE READ | READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE |
| SQL Server | READ COMMITTED | READ UNCOMMITTED, READ COMMITTED SNAPSHOT, REPEATABLE READ, SNAPSHOT, SERIALIZABLE |

---

## 7. Concurrency Control

### 7.1 Two-Phase Locking (2PL)

Il **2PL** garantisce serializzabilità:

**Fase 1 - Growing**: Acquisire lock, non rilasciare.
**Fase 2 - Shrinking**: Rilasciare lock, non acquisirne di nuovi.

**Strict 2PL**: Mantiene lock fino al commit/rollback.

### 7.2 Deadlock Detection

I **deadlock** si verificano con lock circolari:

```sql
-- Transazione A
LOCK table1
LOCK table2 -- Aspetta A

-- Transazione B
LOCK table2
LOCK table1 -- Aspetta B
-- DEADLOCK
```

Il DBMS rileva e abortisce una transazione.

### 7.3 Optimistic Concurrency Control

Il **OCC** evita i lock:

1. **Validation**: Quando si tenta di commitare
2. **Check**: Verifica che non ci siano conflitti
3. **Abort**: Se ci sono conflitti, rollback

Utile quando i conflitti sono rari.

### 7.4 Lock Granularity

La **granularità** del lock influenza performance:

- **Row-level**: Più concorrenza, più overhead
- **Page-level**: Meno overhead, meno concorrenza
- **Table-level**: Poco overhead, bassa concorrenza

### 7.5 Lock Escalation

L'**escalation** converte lock a livelli più alti:

```sql
-- Se una transazione acquisisce troppi row lock
-- Il DBMS può escalare a table lock
```

---

## 8. Distributed Transactions

### 8.1 Two-Phase Commit (2PC)

Il **2PC** coordina transazioni distribuite:

**Fase 1 - Prepare**:
- Coordinator chiede a tutti i partecipanti se possono commitare
- I partecipanti rispondono YES o NO

**Fase 2 - Commit/Rollback**:
- Se tutti YES, invia COMMIT a tutti
- Se uno NO, invia ROLLBACK a tutti

### 8.2 Three-Phase Commit (3PC)

Il **3PC** migliora 2PC:

1. **CanCommit**: Pre-commit check
2. **PreCommit**: Preparazione
3. **DoCommit**: Commit finale

Riduce i blocchi in caso di failure del coordinator.

### 8.3 Saga Pattern

Il **Saga** è un pattern per transazioni distribuite:

- Sequenza di transazioni locali
- Compensazione per rollback
- Nessun blocco globale

```sql
-- Transazione 1: Ordine
-- Transazione 2: Pagamento
-- Transazione 3: Spedizione

-- Se transazione 3 fallisce:
-- Compensazione: annulla pagamento, annulla ordine
```

### 8.4 Event Sourcing

L'**event sourcing** memorizza eventi invece di stati:

- Ogni modifica è un evento
- Lo stato è derivato replayando eventi
- Transazioni come sequenze di eventi

### 8.5 Pericoli delle Transazioni Distribuite

Le **transazioni distribuite** hanno rischi:

- **Blocchi lunghi**: Più nodi coinvolti
- **Failure parziali**: Alcuni nodi committano, altri no
- **Latenza**: Comunicazione tra nodi

---

## 9. Transazioni Long-Running

### 9.1 Problemi con Transazioni Lunghe

Le **transazioni lunghe** causano problemi:

- Lock trattenuti a lungo
- MVCC: Vecchie versioni occupano spazio
- Timeout di connessione

### 9.2 Transactional Outbox Pattern

Il **pattern outbox** permette operazioni atomiche con external systems:

```sql
-- Tabella outbox per messaggi
BEGIN;
UPDATE inventory SET stock = stock - 1;
INSERT INTO outbox (event_type, payload) VALUES ('STOCK_UPDATED', {...});
COMMIT;
-- Un job separato legge outbox e invia eventi
```

### 9.3 Compensating Transactions

Le **transazioni compensative** annullano operazioni:

```sql
-- Operazione originale
UPDATE flights SET seats = seats - 1 WHERE id = 123;

-- Compensazione se serve annullare
UPDATE flights SET seats = seats + 1 WHERE id = 123;
```

### 9.4 Saga Orchestration

L'**orchestrazione Saga** coordina transazioni distribuite:

- Un orchestrator gestisce la sequenza
- Compensazione automatica in caso di fallimento
- Più gestibile di 2PC per sistemi loosely coupled

### 9.5 Choreography

La **coreografia** è un approccio decentralizzato:

- Ogni servizio reagisce agli eventi
- Nessun orchestratore centrale
- Più difficile da tracciare e gestire

---

## 10. Anti-Patterns e Best Practices

### 10.1 Anti-Patterns Comuni

Gli **anti-pattern** da evitare:

- Transazioni che tengono lock troppo a lungo
- Transazioni che fanno operazioni non correlate
- Ignorare i deadlock

### 10.2 Best Practices

Le **best practices**:

- Transazioni brevi
- Accesso ai dati in ordine consistente
- Rilascio lock presto
- Retry logic per deadlock

### 10.3 Appropriate Isolation Level

Scegliere il **livello appropriato**:

- READ COMMITTED per OLTP
- SERIALIZABLE per operazioni finanziarie
- READ UNCOMMITTED solo per query read-only non critiche

### 10.4 Monitoring

Il **monitoraggio** delle transazioni:

- Query execution time
- Lock wait time
- Deadlock frequency

### 10.5 Testing

Il **testing** di transazioni:

- Test di concorrenza
- Test di recovery
- Test di rollback

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*