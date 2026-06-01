# MySQL/MariaDB Query Optimizer

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
1. Optimizer Overview
2. EXPLAIN Analysis
3. Index Usage
4. Query Hints
5. Cost Model
6. Statistics
7. Query Optimization Patterns

---

## 1. Optimizer Overview

### 1.1 What is the Optimizer

L'**optimizer** di MySQL/MariaDB è il componente che trasforma una query SQL in un piano di esecuzione concreto. Il suo obiettivo è trovare il modo più efficiente per eseguire la query, minimizzando l'uso di risorse come I/O, CPU e memoria.

**Optimizer Steps**:

1. **Parsing**: SQL string → Abstract Syntax Tree (AST)
   - Tokenizzazione
   - Parsing grammaticale
   - Validazione sintassi

2. **Preparazione**: risoluzione nomi, tipi
   - Lookup tabelle e colonne
   - Type checking
   - Privilege verification

3. **Cost-based optimization**: valuta piani alternativi
   - Genera multiple piani di esecuzione
   - Stima costo di ogni piano
   - Sceglie il piano con costo minimo

4. **Piano di esecuzione**: generazione final plan
   - Output: execution plan concreto

### 1.2 Cost-Based Optimizer

Il cost-based optimizer stima il costo di diversi piani basandosi su:
- Statistiche delle tabelle (row count, distribution)
- Cost constants configurabili
- Access patterns

```sql
-- Abilitare tracing per vedere decisioni dettagliate
SET optimizer_trace = 'enabled=on';
SET optimizer_trace_max_mem_size = 1048576;

SELECT * FROM orders WHERE customer_id = 100;

-- Vedere trace
SELECT * FROM information_schema.OPTIMIZER_TRACE\G;

SET optimizer_trace = 'enabled=off';
```

**Fattori di costo**:
- Number of rows to scan (rows)
- Number of index lookups (index lookups)
- I/O cost (disk reads)
- CPU cost (row evaluation)
- Memory usage

### 1.3 Join Strategies

MySQL supporta multiple join strategies:

**Nested Loop Join**:
```sql
-- MySQL usa nested loop per default
SELECT * FROM orders o 
JOIN customers c ON o.customer_id = c.id
WHERE c.region = 'West';

-- Piano: scan orders, per ogni row lookup customers
-- Nested loop: scan (orders) -> index lookup (customers)
```

**Block Nested Loop (BNL)** (deprecated in MySQL 8.0):
- Usato quando nessun index disponibile
- Bufferizza le rows in memoria
- Molto lento per grandi dataset

**Hash Join** (MySQL 8.0+):
```sql
-- Abilitare hash join (default ON in 8.0.20+)
SET optimizer_switch = 'hash_join=on';

-- Forza hash join
SELECT /*+ HASH_JOIN(c) */ * FROM orders o
JOIN customers c ON o.customer_id = c.id;
```

**Sort-Merge Join**:
- Ordina entrambe le tabelle
- Merge效果好
- Usato per grandi dataset con condizioni range

### 1.4 Optimizer Switch

```sql
-- Vedere tutte le options
SHOW VARIABLES LIKE 'optimizer_switch';

-- Esempio: disabilitare cost-based per test
SET optimizer_switch = 'condition_fanout_filter=off';
```

**Common switches**:
- `use_index_extensions`: usa extended index info
- `materialization`: materialization di subqueries
- `semijoin`: semijoin optimization
- `loosescan`: loose index scan per DISTINCT
- `firstmatch`: firstmatch strategy per semijoin
- `duplicateweedout`: duplicate elimination

---

## 2. EXPLAIN Analysis

### 2.1 EXPLAIN Basics

EXPLAIN mostra il piano di esecuzione senza eseguire la query (tranne EXPLAIN ANALYZE).

```sql
-- Piano di esecuzione base
EXPLAIN SELECT * FROM orders WHERE status = 'pending';

-- Formato JSON con più dettagli
EXPLAIN FORMAT=JSON SELECT * FROM orders WHERE customer_id = 100;

-- Formato tabella
EXPLAIN FORMAT=TREE SELECT * FROM orders WHERE id > 100;

-- Verbose
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 100;
```

### 2.2 EXPLAIN Output Explained

Ogni colonna nell'output EXPLAIN ha significato importante:

**id**: Ordine delle operazioni nel piano (execution order di SELECT)
- Stesso id = stesso SELECT
- id crescente = ordine di esecuzione

**select_type**: Tipo di select
```sql
SIMPLE:      -- Query semplice, nessuna subquery/UNION
PRIMARY:     -- Outer query in subquery/UNION
SUBQUERY:    -- Subquery nel WHERE/SELECT
DERIVED:     -- Subquery nel FROM (inline view)
UNION:       -- Secondo+ membro di UNION
DEPENDENT:   -- Subquery che referenzia outer query
MATERIALIZED:-- Materialized subquery
```

**table**: Tabella referenziata
- `<derived N>`: tabella derivata dalla subquery N
- `<union M,N>`: resultset di UNION
- Nome tabella: tabella originale

**type**: Join/access type (MOLTO IMPORTANTE!)
```sql
system:         -- Table con una riga (const case speciale)
const:          -- Una riga: PK/UK lookup con costante
eq_ref:         -- Una riga per ogni row della previous table (best non-const)
ref:            -- Matching rows usando index non-unique
fulltext:       -- Fulltext index search
ref_or_null:   -- ref + check per NULL
index_merge:    -- Multiple indexes combinati
unique_subquery:-- Unique subquery (优化)
index_subquery: -- Index subquery
range:          -- Index range scan
index:          -- Full index scan (index in order)
ALL:            -- Full table scan (PROBLEMA!)
```

**possible_keys**: Indici disponibili che optimizer può usare

**key**: Indice effettivamente usato (può essere NULL!)

**key_len**: Lunghezza della key usata in bytes
- Minor key_len = più selettivo

**ref**: Costanti o colonne usate per index lookup
- `const`: costante
- `func`: funzione
- `column_name`: join su colonna

**rows**: Numero stimato di righe che l'operazione esaminerà
- rows × = = lavoro totale
- Più basso = meglio

**filtered**: Percentuale di righe che passeranno il filtro (100% = tutte)

**Extra**: Informazioni aggiuntive (critical!)
```sql
Using where:        -- WHERE clause usato per filtering
Using index:        -- Covering index (no data lookup)
Using index condition:-- Index condition pushdown
Using filesort:    -- External sort richiesto
Using temporary:   -- Temporary table usata
Using MRR:         -- Multi-Range Read optimization
Using sort_union:  -- Index merge with sort
Using union:       -- Index merge with union
No tables used:    -- Query come SELECT 1
Impossible WHERE:  -- WHERE impossibile (0 rows)
Distinct:          -- DISTINCT cercato
Not exists:        -- LEFT JOIN con NOT EXISTS
Using index for group by: -- Group by con index scan
```

### 2.3 Practical Examples

**Full table scan (PROBLEMA)**:
```sql
EXPLAIN SELECT * FROM orders WHERE status = 'pending';
-- type: ALL, rows: 1000000

-- Output tipico:
-- id: 1, select_type: SIMPLE, table: orders
-- type: ALL, possible_keys: NULL, key: NULL
-- rows: 1000000, Extra: Using where

-- Soluzione: aggiungere indice
CREATE INDEX idx_orders_status ON orders(status);
```

**Index Scan (OK)**:
```sql
EXPLAIN SELECT * FROM orders WHERE customer_id = 100;
-- type: ref, key: idx_orders_customer, rows: 5

-- Output:
-- type: ref (buono!)
-- possible_keys: idx_orders_customer
-- key: idx_orders_customer
-- rows: 5 (pochi!)
```

**Covering Index (Best)**:
```sql
-- Query coperta da index
EXPLAIN SELECT customer_id, status FROM orders WHERE status = 'pending';
-- type: ref, key: idx_orders_status, Extra: Using index condition

-- Significa: tutti i dati nella query sono nell'index
-- Non serve accesso alla tabella!
```

**Range Scan**:
```sql
EXPLAIN SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-01-31';
-- type: range, key: idx_orders_created, rows: 50000

-- Range scan è ok per grandi dataset
-- Ma considera partitioning
```

**Join with Index**:
```sql
EXPLAIN SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.region = 'West';

-- Output:
-- id=1, table=c, type=ref, key=PRIMARY, rows=10
-- id=1, table=o, type=ref, key=idx_orders_customer, rows=50
-- Using join buffer (Block Nested Loop) se no index
```

### 2.4 EXPLAIN ANALYZE (MySQL 8.0+)

EXPLAIN ANALYZE esegue la query e misura i tempi reali:

```sql
EXPLAIN ANALYZE 
SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.region = 'West'\G

-- Output include:
-- actual time (ms): tempo per ogni step
-- rows: actual rows esaminati
-- loops: quante volte eseguito
-- buffers: memory usata
```

**Interpretazione**:
```
-> Nested loop inner join  (cost=1000 rows=500)
   -> Index lookup on c using PRIMARY (id=c.id)  (cost=10 rows=100)
      -> Index scan on o using idx_orders_customer (customer_id=c.id)  (actual time=0.5..5.0 rows=500)
```

**Difference from EXPLAIN**:
- EXPLAIN: stime basate su statistics
- ANALYZE: misurazioni reali durante esecuzione

### 2.5 MariaDB EXPLAIN

```sql
-- MariaDB: EXPLAIN FORMAT
EXPLAIN FORMAT=JSON SELECT * FROM orders WHERE status = 'pending';
EXPLAIN FORMAT=TREE SELECT * FROM orders WHERE status = 'pending';
EXPLAIN FORMAT=TRADITIONAL SELECT * FROM orders;

-- Extended SHOW
EXPLAIN EXTENDED SELECT * FROM orders WHERE status = 'pending';
SHOW WARNINGS;

-- Explain delle tracce
SET optimizer_trace = 'enabled=on';
SELECT * FROM orders;
SET optimizer_trace = 'enabled=off';
SELECT * FROM information_schema.OPTIMIZER_TRACE;
```

### 2.6 Common Patterns

**Index hint problem**:
```sql
-- Force index (da evitare se possibile)
EXPLAIN SELECT * FROM orders USE INDEX (idx_status) 
WHERE customer_id = 100;
-- MySQL ignora l'hint perché customer_id è più selettivo
```

**Wrong index selected**:
```sql
-- MySQL usa index sbagliato
-- Soluzioni:
-- 1. Force correct index
-- 2. Drop wrong index
-- 3. Update statistics

SELECT /*+ INDEX(orders idx_customer) */ * FROM orders...
```

**Covering for complex query**:
```sql
-- Creare covering index
CREATE INDEX idx_order_covering 
ON orders(customer_id, status, created_at);

EXPLAIN SELECT customer_id, status, created_at 
FROM orders WHERE customer_id = 100;
-- key: idx_order_covering
-- Extra: Using index (no table access!)
```

---

## 3. Index Usage

### 3.1 Index Types

**B-Tree Index** (default):
- Per =, >, <, BETWEEN, LIKE 'prefix%'
- Non per: functions, negation

**Hash Index**:
- Solo = comparisons
- Memory only

**Full-text Index**:
```sql
-- MySQL
CREATE FULLTEXT INDEX idx_content ON articles(content);

SELECT * FROM articles 
WHERE MATCH(content) AGAINST('database' IN NATURAL LANGUAGE MODE);
```

**Spatial Index** (GIS):
```sql
CREATE TABLE cities (
  id INT,
  location POINT NOT NULL SRID 0,
  SPATIAL INDEX(location)
);
```

### 3.2 Composite Index

```sql
CREATE INDEX idx_order_customer_status 
ON orders(customer_id, status, created_at);

-- Ordine delle colonne MATTERS!
-- Index usato per:
--   WHERE customer_id = 1 AND status = 'pending'
--   WHERE customer_id = 1
--   WHERE customer_id = 1 AND status = 'pending' AND created_at > '2024-01-01'

-- MA NON per:
--   WHERE status = 'pending'
--   WHERE status = 'pending' AND created_at > '2024-01-01'
```

### 3.3 Index Hints

**Forza uso index**:
```sql
SELECT * FROM orders USE INDEX (idx_customer) 
WHERE customer_id = 100;
```

**Ignora index**:
```sql
SELECT * FROM orders IGNORE INDEX (idx_status) 
WHERE status = 'pending';
```

**Forza join order**:
```sql
SELECT * FROM orders FORCE INDEX (idx_customer) 
JOIN customers USE INDEX (idx_pk) ON ...
```

---

## 4. Query Hints

### 4.1 Optimizer Hints

```sql
-- Forza tipo di join
SELECT /*+ BNL(t1, t2) */ * FROM t1 JOIN t2 ON ...

-- Tipi di hint:
-- BNL: Block Nested Loop
-- HASH: Hash Join
-- NO_ICP: No Index Condition Pushdown

-- Ordine join
SELECT /*+ ORDER(t1, t2, t3) */ * FROM t1 
JOIN t2 ON ... JOIN t3 ON ...
```

### 4.2 Index Hints

```sql
-- Usa specific index
SELECT /*+ INDEX(t idx_name) */ * FROM t WHERE ...

-- Forza use
SELECT /*+ FORCE_INDEX(t idx_name) */ * FROM t WHERE ...

-- Ignora index
SELECT /*+ NO_INDEX(t idx_name) */ * FROM t WHERE ...
```

### 4.3 Resource Hints

```sql
-- Limita scan time
SELECT /*+ MAX_EXECUTION_TIME(5000) */ * FROM large_table;

-- Query buffer (MariaDB)
SELECT /*+ SET_VAR(join_buffer_size = 256M) */ * FROM ...
```

---

## 5. Cost Model

### 5.1 Cost Constants

MySQL usa cost constants configurabili:

```sql
-- Vedere costi
SELECT * FROM mysql.server_cost;

-- Modificare
UPDATE mysql.server_cost 
SET cost_value = 1.1 
WHERE cost_name = 'disk_temptable_create_cost';

FLUSH OPTIMIZER_COSTS;
```

**Costi configurabili**:
- disk_temptable_create_cost
- disk_temptable_row_cost
- key_compare_cost
- row_evaluate_cost
- memory_temptable_create_cost
- memory_temptable_row_cost

### 5.2 Session Cost Variables

```sql
-- Adjust per sessione
SET SESSION optimizer_switch = 'index_merge=on,index_merge_union=on';

-- Settare costi in runtime
SET SESSION optimizer_trace = 'enabled=on';
SET SESSION optimizer_trace_limit = 100;
```

---

## 6. Statistics

### 6.1 Statistics Storage

MySQL store statistics in:

```sql
-- InnoDB statistics
SHOW INDEXES FROM orders;

-- Table statistics
SHOW TABLE STATUS LIKE 'orders';

-- Session statistics
SHOW STATUS LIKE 'Handler%';
```

### 6.2 Analyze Tables

```sql
-- Update statistics
ANALYZE TABLE orders;

-- Verify histogram
SELECT * FROM information_schema.COLUMN_STATISTICS
WHERE SCHEMA_NAME = 'mydb' AND TABLE_NAME = 'orders';
```

### 6.3 Histograms

MySQL 8.0+ supporta histogram:

```sql
-- Create histogram
ALTER TABLE orders UPDATE HISTOGRAM ON status, customer_id;

-- Drop histogram
ALTER TABLE orders DROP HISTOGRAM ON status;

-- View histogram
SELECT * FROM information_schema.COLUMN_STATISTICS
WHERE JSON_EXTRACT(HISTOGRAM, '$.$schema_type') IS NOT NULL;
```

## 7. Query Optimization Patterns

### 7.1 Common Problems e Soluzioni

**1. Full table scan su WHERE**:
```sql
-- PROBLEMA: function su colonna
SELECT * FROM orders WHERE YEAR(created_at) = 2024;

-- SOLUZIONE: range predicate
SELECT * FROM orders 
WHERE created_at >= '2024-01-01' 
AND created_at < '2025-01-01';

-- Creare indice su created_at
CREATE INDEX idx_orders_created ON orders(created_at);
```

**2. Function on column**:
```sql
-- PROBLEMA
SELECT * FROM orders WHERE LOWER(status) = 'pending';

-- SOLUZIONE 1: function-based index (MySQL 8.0+)
CREATE INDEX idx_status_lower ON orders((LOWER(status)));

-- SOLUZIONE 2: stored computed column
ALTER TABLE orders ADD status_lower VARCHAR(20) 
GENERATED ALWAYS AS (LOWER(status));
CREATE INDEX idx_status_lower ON orders(status_lower);

-- SOLUZIONE 3: avoid function
SELECT * FROM orders WHERE status = 'Pending';
-- (se input è già normalizzato)
```

**3. OR in WHERE**:
```sql
-- PROBLEMA
SELECT * FROM orders WHERE customer_id = 1 OR status = 'pending';

-- SOLUZIONE 1: UNION (spesso più veloce)
SELECT * FROM orders WHERE customer_id = 1
UNION ALL
SELECT * FROM orders WHERE status = 'pending' AND customer_id != 1;

-- SOLUZIONE 2: IN clause
SELECT * FROM orders WHERE customer_id IN (1);

-- SOLUZIONE 3: Index merge (MySQL 8.0+)
-- Assicurati di avere indici su entrambe le colonne
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
-- MySQL può usare index_merge automaticamente
```

**4. LIKE with leading wildcard**:
```sql
-- PROBLEMA
SELECT * FROM products WHERE name LIKE '%widget%';

-- SOLUZIONE 1: Full-text search
CREATE FULLTEXT INDEX idx_products_name ON products(name);
SELECT * FROM products 
WHERE MATCH(name) AGAINST('widget' IN NATURAL LANGUAGE MODE);

-- SOLUZIONE 2: Search engine (Elasticsearch)
-- Per search complessi
```

**5. IN subquery**:
```sql
-- PROBLEMA: subquery nella IN
SELECT * FROM orders 
WHERE customer_id IN (
  SELECT id FROM customers WHERE region = 'West'
);

-- SOLUZIONE: JOIN
SELECT DISTINCT o.* FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.region = 'West';
```

### 7.2 Subquery Optimization

**Correlated subquery** (spesso lento):
```sql
-- Lento: eseguito per ogni riga
SELECT * FROM orders o
WHERE EXISTS (
  SELECT 1 FROM customers c 
  WHERE c.id = o.customer_id 
  AND c.region = 'West'
);

-- Verificare piano
EXPLAIN SELECT * FROM orders o
WHERE EXISTS (
  SELECT 1 FROM customers c 
  WHERE c.id = o.customer_id 
  AND c.region = 'West'
);
-- type: ALL (problema!)
```

**Soluzione: JOIN**:
```sql
-- Più efficiente
SELECT DISTINCT o.* FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.region = 'West';

-- Verificare
EXPLAIN SELECT DISTINCT o.* FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.region = 'West';
-- type: ref (meglio!)
```

**Scalar subquery in SELECT**:
```sql
-- Ok per valori singoli
SELECT 
  o.*,
  (SELECT name FROM customers c WHERE c.id = o.customer_id) as customer_name
FROM orders o;

-- Ma evitare per aggregazioni
-- Invece:
SELECT o.*, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;
```

### 7.3 JOIN Optimization

**Join order**:
```sql
-- Controllare ordine
EXPLAIN SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
WHERE c.region = 'West';

-- Output:
-- type: ALL per una tabella significa problema!
-- MySQL inizia dalla tabella con filtering maggiore
```

**Forzare specific order**:
```sql
-- MySQL 8.0+ hints
SELECT /*+ LEADING(c o p) */ 
  o.*, c.name, p.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
WHERE c.region = 'West';
```

**STRAIGHT_JOIN**:
```sql
-- Forza join order come written
SELECT STRAIGHT_JOIN o.*, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;
-- Usare con cautela!
```

### 7.4 Limit Optimization

**Offset-based pagination**:
```sql
-- LENTO per grandi offset
SELECT * FROM orders ORDER BY id DESC 
LIMIT 1000000, 10;

-- Problema: MySQL scansisce 1,000,010 righe
```

**Keyset pagination**:
```sql
-- PIÙ VELOCE
SELECT * FROM orders 
WHERE id < 1000000
ORDER BY id DESC 
LIMIT 10;

-- Usa index e non scansisce righe non necessarie
```

**Cursor-based pagination**:
```sql
-- Per applicazioni web
-- Prima query
SELECT * FROM orders ORDER BY id DESC LIMIT 20;
-- Restituisce last_id = min(id)

-- Query successiva
SELECT * FROM orders 
WHERE id < :last_id 
ORDER BY id DESC 
LIMIT 20;
```

### 7.5 Aggregation Optimization

**COUNT(*) optimization**:
```sql
-- Evita scansioni non necessarie
-- Con WHERE
SELECT COUNT(*) FROM orders WHERE status = 'pending';
-- Usa index se disponibile

-- Senza WHERE (table-level)
SELECT COUNT(*) FROM orders;
-- Fast se MyISAM (mantiene count)
-- Per InnoDB: SELECT COUNT(*) FROM orders;
-- Può essere lento: usa approssimazione
SELECT TABLE_ROWS FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'mydb' AND TABLE_NAME = 'orders';
```

**GROUP BY optimization**:
```sql
-- Assicurati GROUP BY column ha index
CREATE INDEX idx_orders_status ON orders(status);

SELECT status, COUNT(*) 
FROM orders 
GROUP BY status;
-- Usa index scan
```

**Covering index per aggregation**:
```sql
-- Index per aggregazione
CREATE INDEX idx_agg 
ON orders(customer_id, status, created_at);

SELECT customer_id, status, COUNT(*) 
FROM orders 
WHERE created_at > '2024-01-01'
GROUP BY customer_id, status;
```

### 7.6 Complex Query Patterns

**Temporal queries**:
```sql
-- Ottimizzare per time ranges
-- No: YEAR(), MONTH(), DAY() functions
SELECT * FROM orders WHERE YEAR(created_at) = 2024 AND MONTH(created_at) = 1;

-- Sì: range
SELECT * FROM orders 
WHERE created_at >= '2024-01-01' 
AND created_at < '2024-02-01';

-- Indice composito
CREATE INDEX idx_orders_temporal 
ON orders(created_at, status, customer_id);
```

**Pivot queries**:
```sql
-- Evitare pivot in SQL se possibile
-- Invece: application-level o usare GROUP BY
SELECT 
  status,
  COUNT(*) as count
FROM orders
GROUP BY status;

-- Per matrix: multiple aggregations
SELECT 
  (SELECT COUNT(*) FROM orders WHERE status = 'pending') as pending,
  (SELECT COUNT(*) FROM orders WHERE status = 'completed') as completed,
  (SELECT COUNT(*) FROM orders WHERE status = 'cancelled') as cancelled;
```

### 7.7 Debugging Slow Queries

```sql
-- 1. Abilitare slow query log
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;  -- 1 secondo
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- 2. Analizzare con EXPLAIN
EXPLAIN ANALYZE SELECT * FROM ...;

-- 3. Check indexes
SHOW INDEX FROM orders;

-- 4. Check statistics
SHOW TABLE STATUS LIKE 'orders';
SHOW INDEXES FROM orders;

-- 5. Check query cache (MySQL 5.7)
SHOW VARIABLES LIKE 'have_query_cache';
```

### 7.8 Performance Checklist

- [ ] Tutte le WHERE columns hanno index
- [ ] EXPLAIN mostra type != ALL per tabelle grandi
- [ ] No functions su indexed columns in WHERE
- [ ] LIMIT offset piccoli o keyset pagination
- [ ] Query non ritorna più dati del necessario
- [ ] JOIN order ottimale (small table first)
- [ ] GROUP BY/ORDER BY usano index
- [ ] Covering indexes per query frequenti

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*