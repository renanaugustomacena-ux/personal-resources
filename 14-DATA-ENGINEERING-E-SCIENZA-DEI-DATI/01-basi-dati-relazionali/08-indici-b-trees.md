# Indici e B-Trees: Strutture per l'Ottimizzazione delle Query

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
1. Fondamenti degli Indici
2. B-Tree: Struttura e Algoritmi
3. Indici in Pratica
4. Indici Compositi
5. Indici Unici
6. Partial Indexes
7. Covering Indexes
8. Indici per Join e Subquery
9. Manutenzione degli Indici
10. Troubleshoot e Ottimizzazione

---

## 1. Fondamenti degli Indici

### 1.1 Perché Servono gli Indici

Gli **indici** sono strutture che permettono di trovare dati senza scandire tutte le righe. Senza indici, una query deve fare **full table scan**.

**Esempio**: Trovare un utente per email
- Senza indice: scan di tutti i milioni di righe
- Con indice: ricerca diretta in millisecondi

### 1.2 Struttura Base degli Indici

Un **indice** è una struttura separata dalla tabella:
- Contiene valori di colonne indicizzate
- Contiene puntatori alle righe (rowid)
- È ordinato per加速are la ricerca

### 1.3 Costo degli Indici

Gli indici hanno **costi**:
- **Spazio**: Ogni indice occupa spazio aggiuntivo
- **Write overhead**: INSERT/UPDATE devono aggiornare gli indici
- **Maintenance**: Indici frammentati degradano

### 1.4 Tipi di Indici

I tipi principali:
- **B-Tree**: Standard, per la maggior parte dei casi
- **Hash**: Solo equality, memoria
- **GIN**: Full-text, array, JSON
- **GiST**: Geometrici, range
- **BRIN**: Block range, dati sequenziali

---

## 2. B-Tree: Struttura e Algoritmi

### 2.1 Struttura del B-Tree

Il **B-Tree** (Balanced Tree) è la struttura più usata:

- **Root**: Nodo superiore
- **Branch nodes**: Nodi intermedi
- **Leaf nodes**: Nodi finali con dati

Ogni nodo può avere molteplici chiavi e puntatori.

### 2.2 Ricerca nel B-Tree

La **ricerca** è efficiente:
1. Partire dalla root
2. Confrontare il valore cercato con le chiavi nel nodo
3. Seguire il puntatore appropriato
4. Ripetere fino ai leaf nodes

Complessità: O(log n)

### 2.3 Insert nel B-Tree

L'**inserimento** mantiene l'equilibrio:
1. Trovare la leaf dove inserire
2. Inserire la chiave
3. Se pieno, split e propagare

Gli split mantengono l'albero bilanciato.

### 2.4 Delete nel B-Tree

La **cancellazione** può richiedere:
- Rimozione diretta se il nodo non è troppo pieno
- Merge con nodi adiacenti
- Borrow (redistribute) da nodi fratelli

### 2.5 B-Tree vs BST

Il **B-Tree** è ottimizzato per disco:
- Meno nodi → meno I/O
- Meno profondità
- Cache-friendly

Il **BST** (Binary Search Tree) è per memoria.

---

## 3. Indici in Pratica

### 3.1 Creazione di Indici

```sql
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_ordini_data ON ordini(created_at DESC);
CREATE INDEX idx_prodotti_categoria ON prodotti(categoria_id);
```

### 3.2 Indici in PostgreSQL

PostgreSQL supporta:
```sql
-- Indici B-tree (default)
CREATE INDEX idx1 ON tab(col);

-- Indici per full-text
CREATE INDEX idx2 ON tab USING gin(to_tsvector('italian', col));

-- Indici per array
CREATE INDEX idx3 ON tab USING gin(tags);
```

### 3.3 Indici in MySQL

MySQL con InnoDB:
```sql
-- Indici B-tree (default)
ALTER TABLE tab ADD INDEX idx1(col);

-- Index prefix
ALTER TABLE tab ADD INDEX idx2(col(10));
```

### 3.4 Indici in SQL Server

SQL Server:
```sql
CREATE NONCLUSTERED INDEX idx1 ON tab(col);
CREATE CLUSTERED INDEX idx2 ON tab(pk);
```

### 3.5 Verifica Utilizzo Indici

Controllare se gli indici sono usati:
```sql
-- PostgreSQL
EXPLAIN SELECT * FROM tab WHERE col = 'value';

-- MySQL
EXPLAIN SELECT * FROM tab WHERE col = 'value';

-- SQL Server
SET SHOWPLAN_ALL ON; SELECT ...
```

---

## 4. Indici Compositi

### 4.1 Ordine delle Colonne

L'**ordine** delle colonne in un indice composito è cruciale:

```sql
CREATE INDEX idx_ordini ON ordini(cliente_id, created_at DESC);
```

Questo indice supporta:
- WHERE cliente_id = X
- WHERE cliente_id = X AND created_at > Y
- WHERE cliente_id = X (ma non created_at da solo!)

### 4.2 Selectivity

La **selectivity** (selettività) indica quanti record matching:

- Bassa selectivity: pochi match → indice utile
- Alta selectivity: molti match → full scan preferibile

### 4.3 Covering Index

Un **covering index** include tutte le colonne necessarie:

```sql
CREATE INDEX idx_covering ON tab(a, b, c) INCLUDE (d, e);
```

La query può essere soddisfatta solo con l'indice.

### 4.4 Indici Multi-Colonna vs Multi-Indici

**Indice composito**: (a, b) → un indice
**Multi-indici**: idx_a ON (a), idx_b ON (b) → due indici

Il composito è migliore per query con entrambe le colonne.

---

## 5. Indici Unici

### 5.1 Definizione

Gli **indici unici** garantiscono valori non duplicati:

```sql
CREATE UNIQUE INDEX idx_email ON utenti(email);
```

### 5.2 Primary Key vs Unique

- **Primary key**: obbligatorio, una sola tabella
- **Unique**: opzionali, multipli

### 5.3 Partial Unique Index

Indici unici parziali:

```sql
CREATE UNIQUE INDEX idx_active_email ON utenti(email) 
WHERE stato = 'active';
```

Solo le righe attive devono avere email uniche.

### 5.4 Unique e NULL

Le chiavi uniche con NULL:
- SQL standard: un solo NULL
- PostgreSQL: multiple NULL permesse (behavior configurabile)

---

## 6. Partial Indexes

### 6.1 Definizione

Gli **indici parziali** includono solo un sottoinsieme di righe:

```sql
CREATE INDEX idx_attivi ON utenti(id) WHERE stato = 'active';
```

### 6.2 Vantaggi

I **vantaggi**:
- Indice più piccolo
- Query più veloci su dati specifici
- Write overhead ridotto

### 6.3 Utilizzo Tipico

Usare per:
- Dati archiviati (stato = 'archived')
- Dati temporanei
- Partizioni

### 6.4 Partial Index su Espressioni

```sql
CREATE INDEX idx_recenti ON ordini(id) 
WHERE created_at > CURRENT_DATE - INTERVAL '30 days';
```

---

## 7. Covering Indexes

### 7.1 Index-Only Scan

Il **covering index** permette index-only scan:

```sql
CREATE INDEX idx_cov ON tab(a, b, c);

-- Questa query usa solo l'indice:
SELECT a, b, c FROM tab WHERE a = 1;
```

Non serve accedere alla tabella!

### 7.2 Include Columns

Le **INCLUDE columns** aggiungono dati non-key:

```sql
CREATE INDEX idx ON tab(a) INCLUDE (b, c);
```

### 7.3 Pro e Contro

**Pro**:
- Nessun accesso alla tabella
- Più veloce

**Contro**:
- Indice più grande
- Maintenance aggiuntivo

### 7.4 Design del Covering Index

Per creare un covering index:
1. Identificare query lente
2. Trovare colonne nella SELECT
3. Aggiungerle all'indice

---

## 8. Indici per Join e Subquery

### 8.1 Indici per JOIN

Per JOIN efficienti, indicizzare le colonne di join:

```sql
-- Se JOIN su cliente_id
CREATE INDEX idx_ordini_cliente ON ordini(cliente_id);
CREATE INDEX idx_clienti_pk ON clienti(id); -- di solito c'è
```

### 8.2 Foreign Key Index

Le **foreign key** dovrebbero avere indici:

```sql
-- PostgreSQL non crea automaticamente indici sulle FK
CREATE INDEX idx_ordini_cliente ON ordini(cliente_id);
```

### 8.3 Indici per Subquery

Le **subquery** in WHERE possono usare indici:

```sql
SELECT * FROM tab WHERE id IN (SELECT id FROM altra_tab WHERE ...);
-- L'indice su altra_tab.id aiuta
```

### 8.4 Indici per EXISTS

Le **subquery EXISTS** beneficiano di indici:

```sql
SELECT * FROM prodotti p 
WHERE EXISTS (SELECT 1 FROM ordini o WHERE o.prodotto_id = p.id);
```

Indici su ordini(prodotto_id) aiutano.

---

## 9. Manutenzione degli Indici

### 9.1 Frammentazione

La **frammentazione** degrada le performance:

- Page split frequenti
- Spazio vuoto negli indici

### 9.2 Rebuild degli Indici

Il **rebuild** defragmentalizza:

```sql
-- PostgreSQL
REINDEX INDEX idx_name;

-- MySQL
OPTIMIZE TABLE tab;

-- SQL Server
ALTER INDEX idx REBUILD;
```

### 9.3 Monitoraggio Utilizzo

Monitorare **quali indici sono usati**:

```sql
-- PostgreSQL: pg_stat_user_indexes
SELECT * FROM pg_stat_user_indexes WHERE relname = 'tab';
```

### 9.4 Indici Non Utilizzati

Identificare **indici mai usati**:

```sql
SELECT indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

### 9.5 Spazio Occupato

Controllare **spazio degli indici**:

```sql
-- PostgreSQL
SELECT pg_size_pretty(pg_relation_size('idx_name'));
```

---

## 10. Troubleshoot e Ottimizzazione

### 10.1 Query che Non Usano Indici

Se l'indice non viene usato:
- Verificare che la colonna sia nella WHERE
- Controllare statistica aggiornata
- Verificare il piano di query

### 10.2 Wrong Index Selected

Se viene selezionato l'indice sbagliato:
- Usare hint per forzare l'indice
- Verificare statistica
- Considerare index hints

### 10.3 Index Hints

Gli **hints** forzano l'uso dell'indice:

```sql
-- MySQL
SELECT * FROM tab USE INDEX (idx_name) WHERE ...

-- SQL Server
SELECT * FROM tab WITH (INDEX(idx_name)) WHERE ...
```

### 10.4 Tuning delle Query

Per **migliorare le query**:
1. Verificare EXPLAIN
2. Identificare table/index scan
3. Aggiungere indici appropriati
4. Verificare miglioramento

### 10.5 Checklist degli Indici

**Checklist** per indici:
- Ogni primary key ha un indice (automatico)
- Ogni foreign key ha un indice
- Colonne usate in WHERE sono indicizzate
- Colonne usate in JOIN sono indicizzate
- Indici non usati rimossi

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*