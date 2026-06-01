# SQL DML: Data Manipulation Language

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: draft

## Skip list
- [ ] Bozza iniziale
- [ ] Review tecnica
- [ ] Review security
- [ ] Formattazione
- [ ] Proofreading
- [ ] Pubblicazione

## Indice
1. Fondamenti del DML
2. INSERT: Inserimento Dati
3. SELECT: Query e Interrogazioni
4. UPDATE: Modifica Dati
5. DELETE: Cancellazione Dati
6. Transazioni e Concurrency
7. Bulk Operations e Performance
8. Upsert Patterns
9. MERGE Statement
10. Best Practices e Anti-Patterns

---

## 1. Fondamenti del DML

### 1.1 Cos'è il DML

Il **Data Manipulation Language (DML)** è la porzione di SQL dedicata alla manipolazione dei dati. Include le operazioni fondamentali per inserire, recuperare, modificare e cancellare dati nelle tabelle del database.

A differenza del DDL (Data Definition Language) che gestisce la struttura degli oggetti, il DML opera sui dati effettivamente contenuti nel database. Le quattro operazioni primarie del DML sono:

- **SELECT**: Recupera dati dal database
- **INSERT**: Aggiunge nuove tuple
- **UPDATE**: Modifica tuple esistenti
- **DELETE**: Rimuove tuple esistenti

Il DML è complementare al DDL e al DCL (Data Control Language per permessi). Inseme formano il nucleo del linguaggio SQL utilizzato quotidianamente dagli sviluppatori e dagli amministratori di database.

### 1.2 Transazioni e DML

Ogni statement DML opera all'interno di una transazione. In modalità autocommit, ogni statement è una transazione automatica. In modalità esplicita, le transazioni sono gestite con BEGIN/COMMIT.

Le transazioni garantiscono le proprietà ACID:
- **Atomicità**: Lo statement viene eseguito completamente o non viene eseguito affatto
- **Consistenza**: I vincoli di integrità sono rispettati
- **Isolamento**: Gli effetti sono visibili solo alla transazione corrente fino al commit
- **Durabilità**: Una volta committato, il dato persiste

### 1.3 Tipi di Statement DML

Gli statement DML si dividono in:
- **Single-row**: Operano su una singola riga (INSERT VALUES, UPDATE single row)
- **Bulk**: Operano su molteplici righe (INSERT SELECT, UPDATE con subquery)
- **Set-based**: Operano su insiemi di dati

La distinzione è importante per le performance e per la semantica delle transazioni.

---

## 2. INSERT: Inserimento Dati

### 2.1 Insert Singolo

L'**INSERT** base inserisce una singola riga in una tabella:

```sql
INSERT INTO tabella (colonna1, colonna2, ...)
VALUES (valore1, valore2, ...);
```

L'ordine delle colonne può essere omesso se si inseriscono valori per tutte le colonne nell'ordine della definizione della tabella:

```sql
INSERT INTO dipartimenti VALUES (1, 'IT', 'Edificio A');
```

È **fortemente consigliato** specificare esplicitamente le colonne per:
- Chiarezza e leggibilità
- Resilienza a cambiamenti dello schema
- Evitare errori con valori di default

### 2.2 Insert Multiplo

L'inserimento multiplo può essere eseguito in diversi modi:

**Valori multipli in un singolo INSERT:**
```sql
INSERT INTO dipartimenti (id, nome) VALUES 
    (1, 'IT'),
    (2, 'HR'),
    (3, 'Finance');
```

Questo è più efficiente di multipli INSERT singoli perché riduce le round-trip al database e può essere ottimizzato dal DBMS.

**INSERT ... SELECT:**
```sql
INSERT INTO dipartimenti_backup (id, nome)
SELECT id, nome FROM dipartimenti;
```

Questo copia dati da una query. È estremamente versatile e può includere filtri, trasformazioni, e join.

### 2.3 Insert con Subquery

L'**INSERT con subquery** permette di inserire dati derivati:

```sql
INSERT INTO report_mensile (mese, totale_vendite)
SELECT 
    DATE_TRUNC('month', order_date) as mese,
    SUM(total) as totale
FROM orders
WHERE order_date >= '2024-01-01'
GROUP BY DATE_TRUNC('month', order_date);
```

Le subquery possono essere correlate per inserire dati basati su condizioni complesse.

### 2.4 Insert con DEFAULT e ON CONFLICT

I **valori DEFAULT** permettono di accettare i valori predefiniti:

```sql
INSERT INTO dipartimenti (id, nome, budget) 
VALUES (4, 'Operations', DEFAULT);
```

**ON CONFLICT** (PostgreSQL) gestisce i conflitti di chiave:

```sql
INSERT INTO utenti (email, nome) VALUES ('test@test.com', 'Test')
ON CONFLICT (email) DO UPDATE SET nome = EXCLUDED.nome;
```

Questo è l'equivalente dell'"upsert" in altri DBMS.

### 2.5 Insert e Vincoli di Integrità

L'INSERT fallisce se viola vincoli:
- **NOT NULL**: Colonna obbligatoria
- **UNIQUE**: Valore duplicato
- **PRIMARY KEY**: Chiave primaria duplicata
- **FOREIGN KEY**: Referenza non esistente
- **CHECK**: Condizione non soddisfatta

La gestione degli errori può essere:
- **Try-catch** nel codice applicativo
- **ON CONFLICT** per gestire conflitti specifici
- **Esecuzione condizionale** con controllo pre-insert

---

## 3. SELECT: Query e Interrogazioni

### 3.1 Struttura Base del SELECT

Il **SELECT** è l'operazione più complessa e versatile del DML:

```sql
SELECT [DISTINCT] colonna1, colonna2, ...
FROM tabella
[WHERE condizione]
[GROUP BY colonna]
[HAVING condizione_gruppo]
[ORDER BY colonna [ASC|DESC]]
[LIMIT count [OFFSET start]];
```

Ogni clausola ha uno scopo specifico e un ordine di elaborazione logico:

1. **FROM**: Determina le tabelle sorgente
2. **WHERE**: Filtra le righe
3. **GROUP BY**: Aggrega le righe
4. **HAVING**: Filtra i gruppi
5. **SELECT**: Proietta le colonne
6. **ORDER BY**: Ordina il risultato
7. **LIMIT**: Limita le righe

### 3.2 SELECT con Join

I **JOIN** combinano dati da multiple tabelle:

**INNER JOIN:**
```sql
SELECT o.id, c.nome, o.total
FROM ordini o
INNER JOIN clienti c ON o.cliente_id = c.id;
```

**LEFT/RIGHT OUTER JOIN:**
```sql
SELECT c.nome, o.id
FROM clienti c
LEFT JOIN ordini o ON c.id = o.cliente_id;
-- Include tutti i clienti, anche senza ordini
```

**Multiple JOIN:**
```sql
SELECT o.id, c.nome, p.nome
FROM ordini o
JOIN clienti c ON o.cliente_id = c.id
JOIN ordini_dettagli od ON o.id = od.ordine_id
JOIN prodotti p ON od.prodotto_id = p.id;
```

### 3.3 Subquery nel SELECT

Le **subquery** possono apparire in varie posizioni:

**Subquery nel WHERE:**
```sql
SELECT * FROM prodotti 
WHERE prezzo > (SELECT AVG(prezzo) FROM prodotti);
```

**Subquery come tabella temporanea:**
```sql
SELECT * FROM (
    SELECT id, nome, prezzo FROM prodotti 
    WHERE attivo = true
) AS prodotti_attivi;
```

**Subquery nel FROM (CTE):**
```sql
WITH prodotti_cari AS (
    SELECT * FROM prodotti WHERE prezzo > 100
)
SELECT * FROM prodotti_cari WHERE stock < 10;
```

### 3.4 Aggregazioni e GROUP BY

Le **funzioni di aggregazione** calcolano valori su gruppi di righe:

```sql
SELECT 
    categoria,
    COUNT(*) as num_prodotti,
    AVG(prezzo) as prezzo_medio,
    SUM(stock) as stock_totale
FROM prodotti
GROUP BY categoria
HAVING COUNT(*) > 5
ORDER BY num_prodotti DESC;
```

**Regole importanti:**
- Le colonne non aggregated nel SELECT devono essere nel GROUP BY
- Il GROUP BY crea gruppi; ogni riga del risultato rappresenta un gruppo
- Il HAVING filtra dopo l'aggregazione (WHERE filtra prima)

### 3.5 SELECT con Condizioni Avanzate

Le **condizioni avanzate** permettono query complesse:

**CASE (conditionally):**
```sql
SELECT 
    nome,
    prezzo,
    CASE 
        WHEN prezzo > 100 THEN 'Alto'
        WHEN prezzo > 50 THEN 'Medio'
        ELSE 'Basso'
    END as fascia_prezzo
FROM prodotti;
```

**COALESCE e NULLIF:**
```sql
SELECT COALESCE(nome, 'Sconosciuto') FROM prodotti; -- Sostituisce NULL
SELECT NULLIF(prezzo, 0) FROM ordini; -- NULL se prezzo = 0
```

**IN e BETWEEN:**
```sql
SELECT * FROM prodotti 
WHERE categoria IN ('A', 'B', 'C')
AND prezzo BETWEEN 10 AND 100;
```

---

## 4. UPDATE: Modifica Dati

### 4.1 Update Base

L'**UPDATE** modifica le righe esistenti:

```sql
UPDATE tabella
SET colonna1 = valore1, colonna2 = valore2
WHERE condizione;
```

Il **WHERE** è cruciale: senza filtri, tutte le righe vengono modificate!

**UPDATE con calcolo:**
```sql
UPDATE prodotti
SET prezzo = prezzo * 1.1
WHERE categoria = 'Elettronica';
```

### 4.2 Update con Subquery

Le **subquery nell'UPDATE** permettono modifiche basate su dati di altre tabelle:

```sql
UPDATE ordini
SET stato = 'cancellato'
WHERE cliente_id IN (
    SELECT id FROM clienti 
    WHERE tipo = 'sospeso'
);
```

**UPDATE correlato:**
```sql
UPDATE prodotti p
SET stock = stock - 1
WHERE EXISTS (
    SELECT 1 FROM ordini_dettagli od
    WHERE od.prodotto_id = p.id
    AND od.ordine_id = 123
);
```

### 4.3 Update con JOIN

Alcuni DBMS permettono **UPDATE con JOIN**:

```sql
UPDATE ordini o
SET cliente_nome = c.nome
FROM clienti c
WHERE o.cliente_id = c.id;
```

In PostgreSQL:
```sql
UPDATE ordini o
SET total = o.total * 1.1
FROM clienti c
WHERE o.cliente_id = c.id
AND c.tipo = 'premium';
```

### 4.4 Update e Vincoli

L'UPDATE può fallire se viola vincoli:
- Violazione di CHECK
- Violazione di UNIQUE
- Violazione di FOREIGN KEY (se referenzia righe che non esistono più)
- Violazione di NOT NULL

**Transazioni:**
```sql
BEGIN;
UPDATE conti SET saldo = saldo - 100 WHERE id = 1;
UPDATE conti SET saldo = saldo + 100 WHERE id = 2;
COMMIT; -- Atomico: entrambi o nessuno
```

### 4.5 Update con Returning

Il **RETURNING** (PostgreSQL) restituisce le righe modificate:

```sql
UPDATE prodotti
SET stock = stock - 1
WHERE id = 123
RETURNING id, nome, stock;
```

Questo è utile per conferme all'utente o per ulteriori elaborazioni.

---

## 5. DELETE: Cancellazione Dati

### 5.1 Delete Base

Il **DELETE** rimuove righe dalla tabella:

```sql
DELETE FROM tabella
WHERE condizione;
```

**ATTENZIONE**: Senza WHERE, tutte le righe vengono cancellate!

```sql
-- PERICOLOSO: cancella tutto!
DELETE FROM tabella;
-- Meglio: TRUNCATE tabella; (più efficiente per grandi tabelle)
```

### 5.2 Delete con Subquery

Le **subquery nel DELETE** permettono cancellazioni complesse:

```sql
DELETE FROM ordini
WHERE cliente_id IN (
    SELECT id FROM clienti 
    WHERE created_at < '2020-01-01'
    AND (SELECT COUNT(*) FROM ordini WHERE cliente_id = clienti.id) = 0
);
```

**DELETE correlato:**
```sql
DELETE FROM prodotti p
WHERE NOT EXISTS (
    SELECT 1 FROM ordini_dettagli 
    WHERE prodotto_id = p.id
);
-- Cancella prodotti mai ordinati
```

### 5.3 Delete con JOIN

Alcuni DBMS supportano **DELETE con JOIN**:

```sql
DELETE FROM ordini
USING clienti
WHERE ordini.cliente_id = clienti.id
AND clienti.stato = 'sospeso';
```

In PostgreSQL, la clause USING specifica le tabelle aggiuntive per il join.

### 5.4 Delete in Transazioni

Il DELETE può essere rollbackato se in una transazione:

```sql
BEGIN;
DELETE FROM prodotti WHERE id = 123;
-- Ops, era sbagliato!
ROLLBACK; -- Ripristina i dati
```

Per cancellazioni massive, è consigliabile:
- Pre-backup dei dati
- Cancellazione in batch per non bloccare la tabella
- Verifica prima con SELECT

### 5.5 Cascade Delete

Le **foreign key con CASCADE** automaticano la cancellazione:

```sql
CREATE TABLE ordini (
    id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clienti(id) ON DELETE CASCADE
);
-- Cancellando un cliente, i suoi ordini vengono cancellati automaticamente
```

Questo è comodo ma **pericoloso**: una cancellazione involontaria può propagarsi. È consigliabile:
- Verificare prima le conseguenze
- Usare SOFT DELETE (flag) quando possibile
- Disabilitare temporarily i constraint per operazioni massive

---

## 6. Transazioni e Concurrency

### 6.1 Isolation Levels e DML

Gli **isolation levels** influenzano come le transazioni DML interagiscono:

- **READ UNCOMMITTED**: Può leggere dati non ancora committati (dangling)
- **READ COMMITTED**: Legge solo dati committati (default in PostgreSQL, MySQL)
- **REPEATABLE READ**: Riga consistente all'interno della transazione
- **SERIALIZABLE**: Isolamento massimo, blocchi su tutte le righe lette

L'isolation level si imposta:
```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

### 6.2 Locking nel DML

Il DML acquisisce **lock** per garantire consistenza:

- **UPDATE/DELETE**: Lock esclusivo sulle righe
- **INSERT**: Lock esclusivo (varia per DBMS)
- **SELECT**: Lock condiviso (varia per implementazione MVCC)

I **deadlock** si verificano quando due transazioni attendono l'una i lock dell'altra:
```sql
-- Transazione A
UPDATE conti SET saldo = saldo - 100 WHERE id = 1;
UPDATE conti SET saldo = saldo + 100 WHERE id = 2;

-- Transazione B (contestuale)
UPDATE conti SET saldo = saldo - 100 WHERE id = 2;
UPDATE conti SET saldo = saldo + 100 WHERE id = 1;
-- DEADLOCK!
```

### 6.3 Savepoint e Partial Rollback

I **savepoint** permettono rollback parziali:

```sql
BEGIN;
INSERT INTO ordini (...) VALUES (...); -- A1
SAVEPOINT punto1;
INSERT INTO dettagli (...) VALUES (...); -- A2
-- Qualcosa va wrong
ROLLBACK TO SAVEPOINT punto1;
-- Solo A2 viene rollbackato, A1 resta
COMMIT;
```

### 6.4 Autocommit e Commit Frequente

Le **modalità di commit** influenzano la durabilità e le prestazioni:

**Autocommit** (default in alcuni DBMS):
```sql
SET autocommit = ON; -- Ogni statement è una transazione
```

**Commit esplicito**:
```sql
BEGIN;
-- Molteplici operazioni
COMMIT; -- Atomiche insieme
```

Il **commit frequente** garantisce durabilità ma aumenta I/O.

### 6.5 Retry Logic

La **retry logic** gestisce retry in caso di fallimenti transienti:

```sql
-- Pseudocode
REPEAT 3 TIMES:
    TRY:
        BEGIN;
        UPDATE conti SET saldo = saldo - 100 WHERE id = 1;
        UPDATE conti SET saldo = saldo + 100 WHERE id = 2;
        COMMIT;
        BREAK;
    CATCH deadlock:
        ROLLBACK;
        WAIT random(100ms, 500ms);
```

---

## 7. Bulk Operations e Performance

### 7.1 Bulk Insert Performance

Gli **INSERT bulk** sono molto più efficienti di INSERT multipli:

```sql
-- Molto efficiente
INSERT INTO tabella VALUES 
    (1, 'a'), (2, 'b'), (3, 'c'), ...; -- 1000 righe
```

**COPY** (PostgreSQL) è ancora più veloce:
```sql
COPY tabella FROM '/path/to/file.csv' WITH (FORMAT csv);
```

**Inserimento parallelo** in database moderni:
```sql
INSERT INTO tabella SELECT * FROM source_table;
-- Il DBMS può parallelizzare la lettura
```

### 7.2 Batch Processing

Il **batch processing** processa dati in chunks:

```sql
-- Processa in batch da 1000 righe
INSERT INTO target_table (id, data)
SELECT id, transform(data)
FROM source_table
WHERE id BETWEEN ? AND ?;
```

Questo evita:
- Memory overflow
- Lock prolungati
- Timeout

### 7.3 Bulk Update e Delete

Il **bulk UPDATE/DELETE** può essere ottimizzato:

```sql
-- Più efficiente che row-by-row
UPDATE tabella 
SET status = 'archived'
WHERE created_at < '2023-01-01';
```

**Con indici appropriati**:
```sql
CREATE INDEX idx_created_at ON tabella(created_at);
-- Questo rende il WHERE molto più veloce
```

### 7.4 Partition Operations

Le **operazioni su partizioni** sono più efficienti:

```sql
-- Solo una partizione
ALTER TABLE tabella TRUNCATE PARTITION p2024;
```

### 7.5 Hints e Optimizations

Gli **hints** guidano l'optimizer:

```sql
-- SQL Server
SELECT * FROM tabella WITH (NOLOCK);

-- PostgreSQL (configurazione)
SET enable_seqscan = off;
```

I hints dovrebbero essere usati **con cautela**: indicano che l'optimizer sta sbagliando qualcosa.

---

## 8. Upsert Patterns

### 8.1 On Conflict - PostgreSQL

L'**upsert** (INSERT or UPDATE) in PostgreSQL:

```sql
INSERT INTO utenti (email, nome, last_login)
VALUES ('test@test.com', 'Test', NOW())
ON CONFLICT (email) 
DO UPDATE SET 
    nome = EXCLUDED.nome,
    last_login = EXCLUDED.last_login;
```

La **clausola DO UPDATE** definisce cosa fare in caso di conflitto. EXCLUDED riferisce i valori proposti nell'INSERT.

### 8.2 On Duplicate Key - MySQL

In **MySQL**:

```sql
INSERT INTO utenti (email, nome)
VALUES ('test@test.com', 'Test')
ON DUPLICATE KEY UPDATE nome = VALUES(nome);
```

### 8.3 Merge - SQL Standard

Il **MERGE** è lo standard SQL:

```sql
MERGE INTO target_table AS t
USING source_table AS s
ON t.id = s.id
WHEN MATCHED THEN
    UPDATE SET t.nome = s.nome
WHEN NOT MATCHED THEN
    INSERT (id, nome) VALUES (s.id, s.nome);
```

### 8.4 Pattern Complessi

L'upsert può includere condizioni:

```sql
INSERT INTO inventory (product_id, quantity)
VALUES (123, 10)
ON CONFLICT (product_id) 
DO UPDATE SET 
    quantity = inventory.quantity + EXCLUDED.quantity
WHERE inventory.quantity + EXCLUDED.quantity < 100;
```

### 8.5 Returning per Verifica

Il **RETURNING** conferma l'operazione:

```sql
INSERT INTO tabella (data)
VALUES ('value')
ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data
RETURNING id, action;
```

Restituisce 'insert' o 'update' per sapere cosa è successo.

---

## 9. MERGE Statement

### 9.1 Struttura del MERGE

Il **MERGE** combina INSERT, UPDATE, DELETE in una singola operazione:

```sql
MERGE INTO tabella_target AS target
USING source_table ON source.id = target.id
WHEN MATCHED THEN
    UPDATE SET target.value = source.value
WHEN NOT MATCHED BY TARGET THEN
    INSERT (id, value) VALUES (source.id, source.value);
```

### 9.2 MERGE con Condizioni

Le **condizioni** permettono azioni diverse:

```sql
MERGE INTO inventory i
USING (SELECT product_id, SUM(quantity) as qty FROM orders GROUP BY product_id) o
ON i.product_id = o.product_id
WHEN MATCHED AND i.quantity > o.qty THEN
    UPDATE SET i.quantity = i.quantity - o.qty
WHEN MATCHED AND i.quantity <= o.qty THEN
    DELETE
WHEN NOT MATCHED THEN
    INSERT (product_id, quantity) VALUES (o.product_id, o.qty);
```

### 9.3 MERGE vs Single Operations

Il MERGE è più **efficiente** di multiple operazioni:
- Una sola round-trip
- Una sola transazione implicita
- Optimizer può ottimizzare l'intera operazione

Ma è **meno leggibile** di singoli statement. Usarlo quando appropriato.

### 9.4 Limitazioni del MERGE

Le **limitazioni** del MERGE:
- Non supportato in tutti i DBMS (MySQL fino a 8.0)
- Performance può essere peggiore di statement separati in alcuni casi
- Più difficile da debuggare

### 9.5 Error Handling nel MERGE

Il MERGE può avere ** clausole di errore**:

```sql
MERGE INTO target t
USING source s ON t.id = s.id
WHEN NOT MATCHED THEN
    INSERT VALUES (s.id, s.val)
LOG ERRORS INTO error_log ('Error inserting');
```

---

## 10. Best Practices e Anti-Patterns

### 10.1 Best Practices DML

Le **best practices** per operazioni DML:

- **Specificare sempre le colonne** nell'INSERT
- **Usare WHERE** in UPDATE e DELETE
- **Transazioni** per operazioni multiple
- **Indici** appropriati per query efficienti
- **Batch** per operazioni massive

### 10.2 Anti-Patterns Comuni

Gli **anti-pattern** da evitare:

**SELECT * quando non necessario:**
```sql
-- Peggio: seleziona tutte le colonne
SELECT * FROM tabella WHERE id = 1;
-- Meglio: seleziona solo quelle necessarie
SELECT nome, email FROM tabella WHERE id = 1;
```

**N+1 Query:**
```sql
-- Peggio: query per ogni riga
FOR row IN SELECT id FROM tabella:
    UPDATE tabella SET col = row.val WHERE id = row.id;

-- Meglio: una singola UPDATE
UPDATE tabella SET col = CASE id WHEN ... END;
```

### 10.3 Parameterized Queries

Le **query parametrizzate** prevengono SQL injection:

```sql
-- Invece di: "SELECT * FROM tabella WHERE nome = '" + userInput + "'"
-- Usare: parametri
PREPARE stmt(text) AS SELECT * FROM tabella WHERE nome = $1;
EXECUTE stmt(' valoreUtente ');
```

### 10.4 Transaction Scope Appropriato

La **dimensione della transazione** appropriata:

- **Transazioni piccole** per operazioni veloci
- **Transazioni grandi** quando necessario (es. import massive)
- **Non tenere transazioni aperte** tra request HTTP

### 10.5 Logging e Audit

Il **logging** delle operazioni DML:

```sql
-- Trigger di audit
CREATE TRIGGER audit_dml
AFTER INSERT OR UPDATE OR DELETE ON tabella
FOR EACH ROW EXECUTE FUNCTION log_dml();
```

Questo è cruciale per compliance e debugging.

---

## Appendice

### A.1 Riferimenti SQL

- PostgreSQL: postgresql.org/docs
- MySQL: dev.mysql.com/doc
- SQL Server: docs.microsoft.com/sql

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*