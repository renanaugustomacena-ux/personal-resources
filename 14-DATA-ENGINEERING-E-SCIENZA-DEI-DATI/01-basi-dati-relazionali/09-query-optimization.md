# Query Optimization: Tecniche e Strategie

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
1. Fondamenti dell'Ottimizzazione
2. Query Planning e Explain
3. Analisi dei Piani di Esecuzione
4. Join Order Optimization
5. Index Usage Optimization
6. Subquery Optimization
7. Aggregation Optimization
8. Parallel Query Execution
9. Advanced Optimization Techniques
10. Performance Tuning Checklist

---

## 1. Fondamenti dell'Ottimizzazione

### 1.1 Cos'è l'Ottimizzazione

L'**ottimizzazione delle query** è il processo di miglioramento delle performance delle query SQL. L'ottimizzatore del database seleziona il piano di esecuzione più efficiente.

L'ottimizzazione si basa su:
- **Stime di costo**: IO, CPU, rete
- **Statistiche**: distribuzione dei dati
- **Regole**: trasformazioni algebriche

### 1.2 Cost-Based vs Rule-Based

Due approcci principali:

**Cost-Based Optimizer** (CBO):
- Stima il costo di diversi piani
- Seleziona il piano a costo minimo
- Più sofisticato, usato dai DBMS moderni

**Rule-Based Optimizer** (RBO):
- Segue regole fisse
- Meno flessibile
- Obsoleto

### 1.3 Components dell'Optimizer

L'ottimizzatore include:
- **Query parser**: Analizza la query
- **Query rewriter**: Trasforma in forma equivalente
- **Plan generator**: Genera piani di esecuzione
- **Plan evaluator**: Valuta e seleziona il piano

### 1.4 Costo dell'Ottimizzazione

L'ottimizzazione ha un costo:
- Troppi piani possibili = tempo di ottimizzazione elevato
- Cache dei piani per query ricorrenti

---

## 2. Query Planning e Explain

### 2.1 EXPLAIN Basic

Il comando **EXPLAIN** mostra il piano di esecuzione:

```sql
-- PostgreSQL
EXPLAIN SELECT * FROM utenti WHERE email = 'test@test.com';

-- MySQL
EXPLAIN SELECT * FROM utenti WHERE email = 'test@test.com';

-- SQL Server
SET SHOWPLAN_ALL ON
SELECT * FROM utenti WHERE email = 'test@test.com';
```

### 2.2 EXPLAIN ANALYZE

**EXPLAIN ANALYZE** esegue realmente la query e mostra i tempi:

```sql
EXPLAIN ANALYZE SELECT * FROM utenti WHERE email = 'test@test.com';
```

Mostra:
- Tempo di esecuzione reale
- Rows realmente processate
- Buffer usage

### 2.3 Interpretazione Output

L'output di EXPLAIN include:
- **Operation**: Tipo di operazione (Seq Scan, Index Scan, etc.)
- **Relation**: Tabella coinvolta
- **Rows**: Righe stimate
- **Width**: Larghezza stimata
- **Cost**: Costo stimato (startup, total)

### 2.4 Formati Output

Diversi formati:
```sql
-- Testo (default)
EXPLAIN SELECT ...

-- JSON (più strutturato)
EXPLAIN (FORMAT JSON) SELECT ...

-- YAML
EXPLAIN (FORMAT YAML) SELECT ...

-- XML
EXPLAIN (FORMAT XML) SELECT ...
```

### 2.5 Explain in Pratica

Usare EXPLAIN per:
- Capire come viene eseguita la query
- Identificare colli di bottiglia
- Verificare l'effetto di indici

---

## 3. Analisi dei Piani di Esecuzione

### 3.1 Sequential Scan

Il **sequential scan** legge tutte le righe:

```
Seq Scan on orders  (cost=0.00..2000.00 rows=100000 width=100)
  Filter: status = 'pending'
```

Indica:
- Nessun indice utilizzabile
- Full table scan
- Filter applicato dopo

### 3.2 Index Scan vs Index Only Scan

L'**Index Scan** usa l'indice per trovare le righe:

```
Index Scan using idx_orders_status on orders
  Index Cond: (status = 'pending'::text)
```

**Index Only Scan** non accede alla tabella:

```
Index Only Scan using idx_orders_status on orders
  Index Cond: (status = 'pending'::text)
```

Più veloce se l'indice copre tutte le colonne necessarie.

### 3.3 Nested Loop Join

Il **nested loop** è per piccole tabelle:

```
Nested Loop  (cost=100.00..200.00 rows=10 width=100)
  ->  Seq Scan on utenti  (cost=0.00..10.00 rows=100)
  ->  Index Scan on ordini  (cost=100.00..100.00 rows=1)
        Index Cond: (cliente_id = utenti.id)
```

Efficiente se:
- Una tabella è piccola
- C'è un indice sulla join column

### 3.4 Hash Join

Il **hash join** è per tabelle grandi:

```
Hash Join  (cost=1000.00..2000.00 rows=500 width=100)
  ->  Seq Scan on ordini
  ->  Hash
       ->  Seq Scan on clienti
```

Efficiente quando non ci sono indici utili.

### 3.5 Merge Join

Il **merge join** per dati ordinati:

```
Merge Join  (cost=1000.00..2000.00 rows=500 width=100)
  ->  Sort
       ->  Index Scan on ordini
  ->  Sort
       ->  Index Scan on clienti
```

Efficiente se i dati sono già ordinati.

---

## 4. Join Order Optimization

### 4.1 Importanza dell'Ordine

L'**ordine dei join** influenza drasticamente le performance:

- Tabella piccola prima = risultati intermedi piccoli
- Tabella grande prima = risultati intermedi enormi

### 4.2 Dynamic Programming

L'ottimizzatore usa **dynamic programming** per join piccoli:

- Calcola costi per ogni sottoinsieme
- Costruisce soluzione ottimale per l'intero

### 4.3 Heuristic Join Order

Per join con molte tabelle, usa **euristiche**:
1. Unisci prima le tabelle con filtri più selettivi
2. Unisci prima le tabelle più piccole

### 4.4 Forzare l'Ordine

È possibile forzare l'ordine con hints:

```sql
-- PostgreSQL (via join_collapse_limit)
SET join_collapse_limit = 1;

-- MySQL
SELECT /*+ JOIN_FIXED_ORDER() */ ...

-- SQL Server
SELECT * FROM a INNER JOIN b ON ... INNER JOIN c ON ...
OPTION (FORCE ORDER);
```

### 4.5 Join Strategy Selection

Scegliere la strategia di join appropriata:

- **Nested loop**: per join su chiave unica
- **Hash join**: per grandi tabelle non ordinate
- **Merge join**: per tabelle già ordinate/indicizzate

---

## 5. Index Usage Optimization

### 5.1 Index Condition Pushdown

L'**ICP** spinge i filtri nell'indice:

```
Index Scan using idx on tab
  Index Cond: (col1 = value)
  Filter: (col2 > 100)
```

Il filtro viene applicato durante l'accesso all'indice.

### 5.2 Index-Only Scans

Usare **covering indexes** per index-only scan:

```sql
CREATE INDEX idx_cover ON tab(a, b, c);
-- Query su a, b, c usa solo l'indice
```

### 5.3 Partial Index Usage

Le **partial indexes** per query su sottoinsiemi:

```sql
CREATE INDEX idx_active ON tab(id) WHERE status = 'active';
-- Query con WHERE status = 'active' usa l'indice
```

### 5.4 Indexes on Expressions

Indicizzare **espressioni** invece di colonne:

```sql
CREATE INDEX idx_lower ON tab(LOWER(email));
SELECT * FROM tab WHERE LOWER(email) = 'test@test.com';
```

### 5.5 Multi-Column Index Usage

Usare correttamente gli **indici compositi**:

```sql
CREATE INDEX idx(a, b, c);
-- Utile per WHERE a = 1 AND b > 10
-- Non utile per WHERE b > 10 (colonna b da sola)
```

---

## 6. Subquery Optimization

### 6.1 Subquery Flattening

Le **subquery** possono essere trasformate in join:

```sql
-- Prima
SELECT * FROM tab WHERE id IN (SELECT id FROM altra);

-- Dopo (spesso più efficiente)
SELECT DISTINCT tab.* FROM tab JOIN altra ON tab.id = altra.id;
```

### 6.2 Semi-Join vs Anti-Join

L'ottimizzatore sceglie tra:
- **Semi-join**: EXISTS con subquery
- **Anti-join**: NOT EXISTS con subquery

### 6.3 Subquery in FROM

Le subquery nel FROM possono essere ottimizzate:

```sql
-- Aggiungere indici alla subquery se usata spesso
-- Considerare CTE con materializzazione
```

### 6.4 Correlated Subqueries

Le **subquery correlate** sono eseguite per ogni riga:

```sql
SELECT * FROM tab t1
WHERE price > (SELECT AVG(price) FROM tab t2 WHERE t1.cat = t2.cat);
```

**Ottimizzazioni**:
- Trasformare in JOIN se possibile
- Materializzare la subquery

### 6.5 LATERAL Subqueries

Le **LATERAL subqueries** sono eseguite per ogni riga:

```sql
SELECT * FROM t1, LATERAL (SELECT * FROM t2 WHERE t2.id = t1.id) sub;
```

Usare con cautela, può essere costoso.

---

## 7. Aggregation Optimization

### 7.1 Group By Optimization

Ottimizzare le **GROUP BY**:

- Assicurarsi che le colonne siano indicizzate
- Considerare indici covering per GROUP BY
- Verificare se Hash Aggregate o Group Aggregate

### 7.2 Indexes for Aggregations

Gli **indici** possono accelerare le aggregazioni:

```sql
-- Indice su colonna di GROUP BY
CREATE INDEX idx ON tab(col_group, col_agg);
```

### 7.3 Aggregate Pushdown

L'**aggregate pushdown** spinge l'aggregazione:

```
GroupAggregate  (cost=1000.00..2000.00)
  ->  Index Scan using idx on tab
```

Se l'indice copre la GROUP BY e le funzioni di aggregazione.

### 7.4 DISTINCT Optimization

Il **DISTINCT** può essere costoso:

```sql
-- Usare GROUP BY se equivalente
SELECT DISTINCT col FROM tab;
-- è equivalente a:
SELECT col FROM tab GROUP BY col;
```

### 7.5 Window Functions

Le **window functions** possono essere ottimizzate:

```sql
-- Se l'ordinamento corrisponde a un indice
SELECT *, ROW_NUMBER() OVER (ORDER BY indexed_col) FROM tab;
```

---

## 8. Parallel Query Execution

### 8.1 Parallel Plans

I database moderni supportano **query parallele**:

```
Parallel Seq Scan on tab
  Workers: 4
```

Divide il lavoro su multiple CPU.

### 8.2 Parallelism Configuration

Configurare il **parallelismo**:

```sql
-- PostgreSQL
SET max_parallel_workers_per_gather = 4;

-- MySQL (non supporta pienamente)
-- Dipende da storage engine

-- SQL Server
-- Automatico, configurabile con MAXDOP
```

### 8.3 Parallel Join

I **join paralleli** distribuiscono il lavoro:

```
Parallel Hash Join
  Workers: 4
```

### 8.4 When to Use Parallelism

Usare per:
- Query CPU-intensive
- Grandi dataset
- Operazioni di aggregazione

Non usare per:
- Query piccole (overhead > beneficio)
- Query con alta latenza (network)

### 8.5 Monitoring Parallel Queries

Monitorare le **query parallele**:

```sql
-- PostgreSQL: verificare parallelism in EXPLAIN
EXPLAIN (ANALYZE) SELECT ...
```

---

## 9. Advanced Optimization Techniques

### 9.1 Query Rewrite

La **riscrittura delle query** può migliorare le performance:

```sql
-- Prima: NOT IN
SELECT * FROM a WHERE id NOT IN (SELECT id FROM b);

-- Dopo: NOT EXISTS o LEFT JOIN
SELECT * FROM a WHERE NOT EXISTS (SELECT 1 FROM b WHERE b.id = a.id);
```

### 9.2 CTE Materialization

Le **CTE** possono essere materializzate:

```sql
WITH cte AS (
    SELECT * FROM large_table WHERE ...
)
SELECT * FROM cte JOIN other ON ...
```

Utile per subquery ricorrenti.

### 9.3 Temporary Tables

Le **tabelle temporanee** possono aiutare:

```sql
CREATE TEMP TABLE tmp AS SELECT ...;
-- Operazioni multiple su tmp
DROP TABLE tmp;
```

Utile per calcoli intermedi complessi.

### 9.4 hints e Directives

Gli **hints** forzano l'ottimizzatore:

```sql
-- PostgreSQL: pg_hint_plan
/*+ SeqScan(tab) */

-- MySQL
/*+ INDEX(tab idx_name) */

-- SQL Server
OPTION (HASH JOIN, INDEX(idx_name))
```

### 9.5 Plan Caching

La **cache dei piani** migliora query ripetute:

- I piani compilati sono memorizzati
- Query parametriche usano cached plans

---

## 10. Performance Tuning Checklist

### 10.1 Analisi Iniziale

**Checklist** iniziale:
1. Identificare query lente
2. Eseguire EXPLAIN
3. Identificare operations costose
4. Verificare utilizzo indici

### 10.2 Ottimizzazione Indici

**Checklist indici**:
1. Ogni WHERE column ha indice?
2. Ogni JOIN column ha indice?
3. Coverage index per query frequenti?
4. Indici non usati rimossi?

### 10.3 Ottimizzazione Query

**Checklist query**:
1. SELECT * avoided?
2. Filtri nel WHERE più selettivi prima?
3. Subquery trasformate in join?
4. DISTINCT/ORDER BY ottimizzati?

### 10.4 Configurazione DBMS

**Checklist configurazione**:
1. Memory settings appropriati?
2. Statistics aggiornate?
3. Parallelism configurato?
4. Logging minimizzato?

### 10.5 Monitoraggio Continuo

**Monitoraggio**:
1. Query lente loggate?
2. Index usage tracciato?
3. Query execution time monitorato?
4. Trend identificati?

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*