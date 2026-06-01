# PostgreSQL Indexing Avanzato

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
1. Tipi di Indici in PostgreSQL
2. B-Tree Index Internals
3. Indici GiST, GIN, BRIN
4. Indici Compositi e Covering
5. Partial Indexes
6. Indici su Espressioni
7. Indici Unici e Exclusion Constraints
8. Index Only Scans e Visibility Map
9. Maintenance e Fragmentation
10. Index Tuning Strategies

---

## 1. Tipi di Indici in PostgreSQL

### 1.1 B-Tree (Default)

Il **B-Tree** è l'indice predefinito e più versatile in PostgreSQL. È ottimizzato per operazioni di confronto e range:

**Operatori supportati**:
- Equality: =, <>
- Comparison: <, >, <=, >=
- Range: BETWEEN, IN
- NULL: IS NULL, IS NOT NULL
- Pattern matching: LIKE, ~ con anchor iniziale (es. 'prefix%')

**Struttura**: Il B-Tree mantiene i dati ordinati, permettendo ricerche efficienti sia per equality che per range. Ogni nodo può contenere multiple chiavi, bilanciato automaticamente.

**Quando usare**: Per quasi tutti i casi d'uso normali - chiavi primarie, foreign keys, colonne usate in WHERE con operatori di confronto.

```sql
-- Creare indice B-Tree
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_order_date ON orders(order_date);
CREATE INDEX idx_product_price ON products(price);
```

### 1.2 Hash

Gli indici **Hash** sono ottimizzati esclusivamente per equality:

```sql
CREATE INDEX idx_hash ON tab USING hash(col);
```

**Caratteristiche**:
- Supportano solo l'operatore =
- Non sono scrivibili nel WAL (non durability)
- Non supportano uniqueness
- Non possono essere usati per ordinamento
- Più compatti dei B-Tree

**Limitazioni**: Sono indicati solo per tabelle statiche o read-mostly dove la durability del WAL non è necessaria. In pratica, i B-Tree sono quasi sempre preferibili.

```sql
-- Hash index ha senso solo per tabelle read-only
CREATE INDEX idx_lookup ON huge_table USING hash(uuid_column);
```

### 1.3 GiST (Generalized Search Tree)

**GiST** è un framework indices estensibile che permette di implementare strutture dati personalizzate:

**Tipi di dati supportati**:
- Geometrici: point, box, polygon, circle
- Full-text search: tsvector
- Range types: int4range, daterange, tsrange
- Array: tramite operatori specifici

**Vantaggi**: Flessibilità - permette di indicizzare tipi di dati con strutture complesse.

```sql
-- Per geometrie
CREATE INDEX idx_location ON buildings USING gist(location);
CREATE INDEX idx_geometry ON shapes USING gist(geom);

-- Per range temporali
CREATE INDEX idx_timerange ON events USING gist(tsrange);

-- Per full-text search
CREATE INDEX idx_fts ON documents USING gist(to_tsvector('italian', content));
```

### 1.4 GIN (Generalized Inverted Index)

**GIN** è un "inverted index" ottimizzato per dati multi-valore dove un valore può contenere molti elementi:

**Tipi supportati**:
- Array: ogni elemento dell'array è indicizzato
- Full-text search: tsvector
- JSONB: ogni chiave-valore è indicizzato
- hstore: coppie chiave-valore

**Caratteristiche**: GIN è ideale per query che cercano elementi specifici all'interno di strutture composite. È più lento da costruire e aggiornare rispetto a B-Tree, ma eccelle per ricerche complesse.

```sql
-- Per array
CREATE INDEX idx_tags ON articles USING gin(tags);

-- Per full-text search
CREATE INDEX idx_search ON posts USING gin(to_tsvector('italian', body));

-- Per JSONB
CREATE INDEX idx_json ON orders USING gin(data);

-- Query su array
SELECT * FROM articles WHERE tags @> '{"postgres", "database"}';
SELECT * FROM posts WHERE body_tsvector @@ to_tsquery('postgres & tutorial');
```

### 1.5 BRIN (Block Range Index)

**BRIN** (Block Range INdex) è un indice specializzato per dati sequenziali con correlazione fisica:

**Funzionamento**: Dividono la tabella in "block ranges" ( gruppi di pagine ), e per ogni range memorizzano un sommario (min/max) delle chiavi in quel blocco.

**Ideale per**:
- Time-series data (dati inseriti in ordine temporale)
- Log data
- Append-only tables
- Very large tabelle (> 100GB) dove gli indici tradizionali sarebbero troppo grandi

**Non ideale per**: Dati non correlati fisicamente, dati modificati frequentemente in posizioni random.

```sql
-- Per timestamp
CREATE INDEX idx_logs ON logs USING brin(created_at);

-- Configurazione personalizzata
CREATE INDEX idx_events ON events USING brin(event_time) 
WITH (pages_per_range = 32);

-- Per dati geografici con correlazione fisica
CREATE INDEX idx_sensors ON sensor_data USING brin(sensor_id, reading_time);
```

---

## 2. B-Tree Index Internals

### 2.1 Struttura B-Tree

La struttura **B-Tree** in PostgreSQL è un albero bilanciato ottimizzato per I/O su disco:

**Componenti della struttura**:
- **Root node**: Il nodo radice da cui inizia la navigazione. Ha puntatori ai nodi figli.
- **Branch nodes**: Nodi intermedi che contengono chiavi e puntatori. Guidano la navigazione verso il basso.
- **Leaf nodes**: Contengono le chiavi reali e i puntatori alle tuple nella heap (ctid).
- **livelli**: L'altezza dell'albero - tipicamente 2-3 per tabelle normali, più per tabelle enormi.

**Caratteristiche**:
- Bilanciato automaticamente: tutti i leaf nodes sono alla stessa profondità
- Ogni nodo contiene multiple chiavi (non binario)
- I/O ottimizzato: ogni nodo è circa una pagina (8KB)
- ordinamento: le chiavi sono ordinate per permettere ricerche efficienti

### 2.2 Index Scan

Il processo di **index scan** per trovare righe:

**Fase 1: Navigazione dall'alto**
- Parti dalla root del B-Tree
- Per ogni livello, confronta la chiave di ricerca con le chiavi nel nodo
- Segui il puntatore appropriato al livello successivo

**Fase 2: Raggiungimento delle leaf**
- Arriva ai leaf nodes
- Trova la chiave esatta o l'intervallo di chiavi
- Estrai i puntatori (ctid) alle tuple

**Fase 3: Fetch dalla heap**
- Per ogni ctid, accede alla heap per recuperare la tupla
- Verifica la visibilità della tupla (MVCC)
- Applica filtri WHERE aggiuntivi

**Complessità**: O(log n) per trovare il punto nel B-Tree, poi O(k) per k tuple trovate.

### 2.3 Index Only Scan

L'**Index Only Scan** è un'ottimizzazione che salta l'accesso alla heap:

**Requisiti**:
- La query deve richiedere solo colonne presenti nell'indice (covering index)
- La pagina nell'indice deve essere "all visible" nella visibility map
- L'optimizer deve stimare che sia più efficiente

**Vantaggi**:
- Evita un accesso alla heap per ogni tuple
- Molto più veloce per query che coprono l'indice
- Riduce I/O significativamente

**Limitazioni**:
- Se la pagina non è "all visible", deve comunque accedere alla heap
- Se colonne richieste non sono nell'indice, usa Index Scan normale

```sql
-- Verificare Index Only Scan usato
EXPLAIN SELECT id, email FROM users WHERE email LIKE 'a%';
-- Se la query è coperta dall'indice, vedrai "Index Only Scan"
```

### 2.4 Bitmap Scans

I **Bitmap Scans** sono un'ottimizzazione per query con condizioni multiple:

**Processo**:
1. Scansiona l'indice e costruisci una bitmap delle pagine che potrebbero contenere righe
2. Combina multiple bitmaps (AND, OR) se ci sono multiple condizioni
3. Accedi alla heap usando la bitmap combinata (Bitmap Heap Scan)

**Vantaggi**:
- Gestisce multiple condizioni su indici diversi
- Riduce random I/O con accesso sequenziale alle pagine
- Non ripete l'accesso all'indice per ogni riga

**Tipi**:
- **Bitmap Index Scan**: Produce bitmap delle pagine matchate
- **Bitmap Heap Scan**: Legge le pagine dalla heap in ordine bitmap
- **BitmapAnd/Or**: Combina multiple bitmaps

```sql
-- Query che usa Bitmap Scan
EXPLAIN SELECT * FROM orders 
WHERE status = 'pending' AND created_at > '2024-01-01';

-- Output tipico:
-- Bitmap Heap Scan on orders
--   Recheck Cond: (status = 'pending'::bpchar)
--   ->  Bitmap Index Scan on idx_orders_status
--   ->  Bitmap Index Scan on idx_orders_date
```

### 2.5 Index Bloat

Il **Bloat** negli indici è lo spazio occupato da tuple morte o obsolete:

**Cause**:
- UPDATE: la vecchia versione nell'indice non viene rimossa immediatamente
- DELETE: le entries nell'indice vengono marcate come morte
- VACUUM: recupera lo spazio nel B-Tree

**Impatto**:
- Indici più grandi del necessario
- Performance degradata (meno chiavi per pagina)
- Più I/O per scansioni

**Monitoraggio**:
```sql
-- Verificare bloat con pgstattuple
SELECT * FROM pgstattuple('idx_user_email');

-- Verificare dimensione effettiva vs attesa
SELECT 
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) as actual_size,
    index_pages,
    (SELECT count(*) * 8 FROM heap_table) as expected_pages
FROM pg_stat_user_indexes;
```

---

## 3. Indici GiST, GIN, BRIN

### 3.1 GiST Index

**GiST (Generalized Search Tree)** è un framework che permette di implementare indici per tipi di dati personalizzati mantenendo le proprietà di bilanciamento e ricerca efficienti.

**Come funziona**: GiST definisce un'interfaccia che ogni tipo di dati deve implementare:
- **Consistent**: determina se una chiave satisfies una condition
- **Union**: combina due entry in una
- **Compression/Decompression**: per memorizzare strutture complesse
- ** penalty**: calcola il costo di inserire un valore

**Applicazioni tipiche**:

```sql
-- Geometrie spaziali (con PostGIS)
CREATE INDEX idx_buildings ON buildings USING gist(geom);

-- Range temporali
CREATE INDEX idx_reservations ON reservations USING gist(daterange);

-- Full-text search
CREATE INDEX idx_fts ON articles USING gist(to_tsvector('italian', content));

-- Indici personalizzati (con estensioni)
-- Esempio con pg_trgm per trigrammi
CREATE INDEX idx_trgm ON words USING gist(word gin_trgm_ops);
```

**Vantaggi**: Estensibilità - qualsiasi tipo di dati può essere indicizzato se implementa le funzioni necessarie.

### 3.2 GIN Index

**GIN (Generalized Inverted Index)** è ottimizzato per dati dove un singolo valore contiene multiple sotto-componenti:

**Struttura**: Mantiene un inverted index: per ogni elemento, una lista di posizioni (pagine) dove appare.

**Ideale per**:
- Arrays: ogni elemento dell'array diventa una chiave
- tsvector: ogni termine diventa una chiave
- JSONB: ogni chiave-valore diventa una chiave
- hstore: ogni coppia chiave-valore

```sql
-- Per array di tag
CREATE INDEX idx_articles ON articles USING gin(tags);

-- Per full-text search
CREATE INDEX idx_fts ON documents USING gin(to_tsvector('italian', content));

-- Per JSONB
CREATE INDEX idx_order_data ON orders USING gin(data);

-- Query tipiche su array
SELECT * FROM articles WHERE tags @> ['postgres', 'tutorial'];
SELECT * FROM articles WHERE tags && ['database', 'performance'];

-- Query full-text
SELECT * FROM documents WHERE content_tsvector @@ to_tsquery('postgresql & optimization');
```

**Performance**: GIN è più lento da costruire e aggiornare rispetto a B-Tree, ma le query su dati compositi sono molto più veloci. È la scelta giusta quando le query sono più frequenti delle scritture.

### 3.3 BRIN Index

**BRIN (Block Range INdex)** sfrutta la correlazione fisica dei dati:

**Struttura**: Dividere la tabella in block ranges (gruppi di pagine consecutive). Per ogni block range, memorizza:
- min值的
- max值
- (opzionalmente) altri summari

**Parametro chiave**: pages_per_range determina quanti blocchi sono raggruppati:
- Valori piccoli (1-8): più preciso, indice più grande
- Valori grandi (128+): meno preciso, indice più piccolo

```sql
-- Default (128 pagine per range)
CREATE INDEX idx_logs ON logs USING brin(created_at);

-- Più preciso per dati molto ordinati
CREATE INDEX idx_sensors ON sensor_data USING brin(timestamp) 
WITH (pages_per_range = 8);

-- Meno preciso per dati dispersi
CREATE INDEX idx_large ON huge_table USING brin(id) 
WITH (pages_per_range = 256);
```

**Quando usare**:
- Dati con alta correlazione fisica (inseriti in ordine)
- Time-series data
- Append-only data
- Tabelle molto grandi dove indici B-Tree sarebbero proibitivi

**Quando NON usare**:
- Dati modificati frequentemente in posizioni random
- Dati senza correlazione fisica
- Query che richiedono precisione

### 3.4 Use Cases Comparison

| Tipo | Scritture | Letture | Uso ideale |
|------|-----------|---------|------------|
| B-Tree | Moderate | Molto veloci | Tuttofare |
| GiST | Moderate | Veloci per operatori specifici | Dati strutturati, geometrie |
| GIN | Lente | Molto veloci per contains | Array, JSONB, full-text |
| BRIN | Molto veloci | Dipende da correlazione | Time-series, append-only |

---

## 4. Indici Compositi e Covering

### 4.1 Composite Indexes

Gli **indici composti** (multi-colonna) includono più di una colonna nella chiave:

```sql
CREATE INDEX idx_composite ON orders(customer_id, order_date, status);
```

**Ordine delle colonne** è critico:

**Query supportate**:
- WHERE a = 1 - Sì, usa l'indice dall'inizio
- WHERE a = 1 AND b = 'x' - Sì, usa l'indice completamente
- WHERE a = 1 AND b > '2024-01-01' - Sì, fino alla colonna b

**Query NON supportate**:
- WHERE b = 'x' - NO, la colonna a manca
- WHERE b > '2024-01-01' - NO, manca la colonna a
- WHERE a = 1 AND c = 'y' - NO, c non è nel prefix

**Regola del leftmost prefix**: L'indice può essere usato solo per le colonne dall'inizio fino a un certo punto.

### 4.2 Covering Indexes

Gli **indici covering** (INCLUDE) permettono di aggiungere colonne non-key che sono "incluse" nell'indice:

```sql
CREATE INDEX idx_cover ON orders(customer_id, order_date) 
INCLUDE (total, status);
```

**Vantaggi**:
- Index Only Scan possibile per query che richiedono colonne INCLUDE
- Evita accesso alla heap
- Le colonne INCLUDE non partecipano all'ordinamento dell'indice

**Limitazioni**:
- Le colonne INCLUDE non possono essere usate per navigare l'albero
- Non possono essere uniche
- Non possono essere parte di un filtro index scan

**Esempio**:
```sql
-- Senza covering: deve accedere alla heap
EXPLAIN SELECT id, name, email FROM users WHERE name LIKE 'J%';

-- Con covering: Index Only Scan
CREATE INDEX idx_user_name_email ON users(name) INCLUDE (email);
EXPLAIN SELECT id, name, email FROM users WHERE name LIKE 'J%';
```

### 4.3 Index Column Ordering

L'**ordinamento delle colonne** nell'indice influenza l'utilizzo:

**Regole per l'ordinamento**:

1. **Colonne più selective prima**: Colonne che riducono drasticamente le righe dovrebbero essere prime.

2. **Colonne con equality prima**: Colonne usate con = dovrebbero precedere quelle con range.

3. **Colonne in ORDER BY**: Se la query ha ORDER BY, includere queste colonne nell'indice può evitare sort.

4. **Colonne in WHERE frequenti**: Colonne usate frequentemente nelle condizioni.

**Esempio pratico**:
```sql
-- Query: WHERE status = 'active' AND date > '2024-01-01' ORDER BY date
CREATE INDEX idx_orders ON orders(status, date);

-- Se la query è solo WHERE status = 'active', funziona
-- Se la query è solo WHERE date > '2024-01-01', NON funziona (status manca)
```

---

## 5. Partial Indexes

### 5.1 Definizione

Gli **indici parziali** (partial indexes) includono solo un sottoinsieme di righe basato su una condizione WHERE:

```sql
-- Indice solo per utenti attivi
CREATE INDEX idx_active_users ON users(id) WHERE status = 'active';

-- Indice solo per ordini pendenti
CREATE INDEX idx_pending_orders ON orders(id) WHERE status = 'pending';

-- Indice solo per dati recenti
CREATE INDEX idx_recent_orders ON orders(id) WHERE created_at > '2024-01-01';
```

La condizione WHERE viene memorizzata con l'indice e usata automaticamente dall'optimizer.

### 5.2 Vantaggi

I partial indexes offrono benefici significativi:

**Indice più piccolo**: Solo le righe che soddisfano la condizione sono incluse. Per una tabella con 90% di righe "attive", l'indice parziale sarà 1/10 delle dimensioni.

**Query più veloci**: Le query che usano la condizione appropriata useranno solo l'indice parziale, più piccolo e più veloce da scansionare.

**Meno overhead per INSERT/UPDATE**: Le righe che non soddisfano la condizione non vengono inserite nell'indice, riducendo il lavoro per le scritture.

**Indici multipli**: Possono creare indici parziali per query frequenti su subset diversi, più efficienti di un singolo indice completo.

### 5.3 Use Cases

I casi d'uso comuni includono:

**Status-specific indexes**:
```sql
-- Query frequenti su ordini attivi
CREATE INDEX idx_active_orders ON orders(id) WHERE status = 'active';
CREATE INDEX idx_completed_orders ON orders(id) WHERE status = 'completed';

-- Query su ordini cancellati sono rare
CREATE INDEX idx_cancelled_orders ON orders(id) WHERE status = 'cancelled';
```

**Temporal data**:
```sql
-- Query frequenti su dati recenti
CREATE INDEX idx_recent_logs ON logs(id) WHERE created_at > current_date - interval '30 days';

-- Dati storici raramente interrogati
CREATE INDEX idx_2024_logs ON logs(id) WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';
```

**Multi-tenant**:
```sql
-- Isolare tenant in indici separati
CREATE INDEX idx_tenant_data ON data(tenant_id, id) WHERE tenant_id = 1;
```

### 5.4 Partial Unique Index

Gli indici parziali possono essere **unique**, garantendo unicità solo per le righe che soddisfano la condizione:

```sql
-- Email unica solo per utenti attivi
CREATE UNIQUE INDEX idx_unique_active_email ON users(email) 
WHERE status = 'active';

-- Codice ordine unico solo per ordini confermati
CREATE UNIQUE INDEX idx_unique_order_code ON orders(order_code) 
WHERE status IN ('confirmed', 'processing');
```

**Applicazioni pratiche**:
- Permettere "soft delete" ma mantenere uniqueness
- Gestire codici temporanei con expiry
- Implementare "pending" states con uniqueness

---

## 6. Indici su Espressioni

### 6.1 Expression Indexes

Gli **indici su espressioni** (expression indexes) creano indici basati su funzioni o calcoli delle colonne:

```sql
-- Case-insensitive search
CREATE INDEX idx_lower_email ON users(LOWER(email));

-- Estrazione di componenti
CREATE INDEX idx_year ON orders(EXTRACT(YEAR FROM order_date));
CREATE INDEX idx_month ON orders(DATE_TRUNC('month', order_date));

-- Computazioni
CREATE INDEX idx_total ON orders((quantity * unit_price));

-- Con cast
CREATE INDEX idx_status_str ON orders(status::text);
```

La chiave dell'indice è il risultato dell'espressione, non il valore della colonna.

### 6.2 Use Cases

**Case-insensitive search**:
```sql
-- Senza indice: scan case-insensitive è lento
SELECT * FROM users WHERE LOWER(email) = LOWER('User@Example.com');

-- Con indice: usa l'indice
CREATE INDEX idx_lower_email ON users(LOWER(email));
```

**Date/time extractions**:
```sql
-- Query su anno specifico
CREATE INDEX idx_order_year ON orders(EXTRACT(YEAR FROM order_date));
SELECT * FROM orders WHERE EXTRACT(YEAR FROM order_date) = 2024;
```

**Computed columns**:
```sql
-- Totale calcolato
CREATE INDEX idx_order_total ON orders(quantity * unit_price);
SELECT * FROM orders WHERE quantity * unit_price > 1000;
```

**Partial string matching**:
```sql
-- Prefisso
CREATE INDEX idx_prefix ON products(SUBSTRING(sku, 1, 4));
```

### 6.3 Functional Indexes

Gli indici funzionali sono espressioni che usano funzioni complesse:

```sql
-- JSON path
CREATE INDEX idx_json ON data USING gin((data->'tags')::text[]);

-- JSON containment
CREATE INDEX idx_jsonb ON orders USING gin(data jsonb_path_ops);

-- Array transformation
CREATE INDEX idx_array_sort ON articles USING gin(ARRAY[sorted_tags]);
```

**Nota**: L'espressione deve essere racchiusa in parentesi quando usata con tipi specifici di indice (es. GIN).

### 6.4 Performance Considerations

Gli indici su espressioni hanno implicazioni importanti:

**Costo di mantenimento**: Ogni INSERT/UPDATE deve valutare l'espressione e aggiornare l'indice. Questo aggiunge overhead.

**Dimensione**: L'indice può essere più grande perché memorizza il risultato dell'espressione, non il valore originale.

**Consistenza delle query**: Le query DEVONO usare la stessa espressione per usare l'indice:
```sql
-- Usa l'indice
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- NON usa l'indice (diverso dalla definizione)
SELECT * FROM users WHERE email ILIKE 'test@example.com';
```

**Optimizer awareness**: L'optimizer riconosce le espressioni matching e usa l'indice automaticamente.

---

## 7. Indici Unici e Exclusion Constraints

### 7.1 Unique Indexes

Gli **indici unici** garantiscono che non ci siano duplicati nella chiave:

```sql
-- Unicità su singola colonna
CREATE UNIQUE INDEX idx_unique_email ON users(email);

-- Unicità su multiple colonne
CREATE UNIQUE INDEX idx_unique_order_item ON order_items(order_id, product_id);

-- Unicità con condizione
CREATE UNIQUE INDEX idx_unique_active_user ON users(email) 
WHERE status = 'active';
```

**Implementazione**: Un unique index è un B-Tree con il vincolo che non può contenere chiavi duplicate. Se si tenta di inserire un duplicato, PostgreSQL genera un errore.

### 7.2 Primary Keys

La **primary key** è un unique index + NOT NULL + la colonna viene usata come riferimento:

```sql
-- Definita al momento della creazione tabella
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

-- Aggiunta successiva
ALTER TABLE orders ADD PRIMARY KEY (id);

-- Constraint naming
ALTER TABLE orders ADD CONSTRAINT pk_orders PRIMARY KEY (id);
```

**Caratteristiche**:
- Obbligatoria: una sola per tabella
- Non nullable: le colonne chiave non possono essere NULL
- Referenziabile: usata come target per FOREIGN KEY

### 7.3 Exclusion Constraints

I **vincoli di esclusione** (EXCLUDE) prevengono sovrapposizioni tra righe:

```sql
-- Prenotazioni: una stanza non può avere due prenotazioni sovrapposte
CREATE TABLE bookings (
    id SERIAL,
    room_id INTEGER NOT NULL,
    period TSRANGE NOT NULL,
    EXCLUDE USING gist (
        room_id WITH =,
        period WITH &&
    )
);

-- Con nome del vincolo
ALTER TABLE bookings ADD CONSTRAINT no_double_booking 
EXCLUDE USING gist (
    room_id WITH =,
    period WITH &&
);
```

**Operatori comuni**:
- = : uguaglianza
- && : overlap (per range)
- <> : disuguaglianza
- &< : strettamente a sinistra
- &> : strettamente a destra

### 7.4 Partial Unique

Gli indici unici parziali implementano unicità condizionale:

```sql
-- Un solo ordine attivo per cliente
CREATE UNIQUE INDEX idx_active_order_per_customer ON orders(customer_id) 
WHERE status = 'active';

-- Codice ordine unico solo per non cancellati
CREATE UNIQUE INDEX idx_order_code ON orders(order_code) 
WHERE status != 'cancelled';
```

**Applicazioni pratiche**:
- Permettere un solo record "attivo" per entity
- Gestire soft-delete mantenendo uniqueness
- Implementare stati transizionali con unicità temporanea

---

## 8. Index Only Scans e Visibility Map

### 8.1 Index Only Scan

L'**Index Only Scan** è una tecnica di query execution che ottiene tutti i dati dall'indice senza accedere alla heap:

**Come funziona**:
- Le colonne richieste dalla query sono tutte nell'indice
- La visibility map conferma che tutte le tuple nella pagina sono visibili
- Non c'è necessità di accedere alla heap per verificare MVCC

**Vantaggi**:
- Elimina un accesso alla heap per ogni tuple
- Riduce I/O significativamente
- Più veloce per query che "coprono" l'indice

**Esempio**:
```sql
-- Query che può essere Index Only Scan
CREATE INDEX idx_user_cover ON users(email, name);
SELECT email, name FROM users WHERE email = 'test@example.com';

-- Query che NON può essere IOS (manca status)
SELECT email, name, status FROM users WHERE email = 'test@example.com';
```

### 8.2 Visibility Map

La **Visibility Map** è una struttura che traccia quali pagine sono "visibili a tutti":

**Struttura**: Un bit per ogni pagina della tabella. Se il bit è 1, tutte le tuple in quella pagina sono visibili a tutte le transazioni.

**Aggiornamento**: La visibility map viene aggiornata durante VACUUM:
- Prima che una pagina sia "all visible", tutte le sue tuple devono essere visibili
- Il vacuum marca la pagina quando tutte le tuple sono visibili

**Utilizzo**:
- Index Only Scan: se la pagina è "all visible", salta la heap
- VACUUM: le pagine "all visible" possono essere saltate

### 8.3 Index Only Scan Requirements

Perché l'optimizer scelga Index Only Scan:

**Requisiti**:
1. **Tutte le colonne nella query**: devono essere nell'indice (key o INCLUDE)
2. **Pagina "all visible"**: la visibility map deve avere il bit settato
3. **Statistiche aggiornate**: l'optimizer deve avere informazioni recenti
4. **Costo stimato minore**: l'optimizer confronta i costi

**Verificare**:
```sql
-- Forzare Index Only Scan se possibile
SET enable_seqscan = off;

-- Verificare nel piano
EXPLAIN SELECT email, name FROM users WHERE email LIKE 'a%';
```

### 8.4 pg_stat_user_indexes

Monitorare l'uso degli indici:

```sql
-- Statistiche base
SELECT 
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    idx_blks_hit,
    idx_blks_read
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Verificare Index Only Scans
SELECT 
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY idx_tup_fetch DESC;

-- Verificare indici mai usati
SELECT 
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE '%pkey%';
```

---

## 9. Maintenance e Fragmentation

### 9.1 Index Bloat

Il **Bloat** negli indices è lo spazio occupato da tuple morte o obsolete che non sono state rimosse:

**Cause del bloat**:
- UPDATE: la vecchia chiave nell'indice rimane fino al vacuum
- DELETE: le chiavi morte rimangono fino al vacuum
- HOT updates: le chiavi potrebbero non essere aggiornate
- Transaction rollbacks: le entries rimangono

**Impatto**:
- Indici più grandi del necessario
- Più I/O per scansioni
- Cache meno efficace
- Degradamento progressivo delle performance

**Prevenzione**: VACUUM regolare mantiene gli indici compatti.

### 9.2 REINDEX

Il comando **REINDEX** ricostruisce un indice da zero, eliminando completamente il bloat:

```sql
-- Reindex singolo indice
REINDEX INDEX idx_user_email;

-- Reindex tutti gli indici di una tabella
REINDEX TABLE orders;

-- Reindex tutti gli indici di un database (tutto il cluster)
REINDEX DATABASE mydb;

-- Reindex con opzioni
REINDEX (VERBOSE, CONCURRENTLY) INDEX idx_name;
```

**REINDEX CONCURRENTLY**: Da PostgreSQL 12, può creare l'indice senza blocking writes. Richiede che non ci siano lock sulla tabella.

**Quando usare REINDEX**:
- Dopo un bulk DELETE
- Quando il bloat è eccessivo
- Dopo un crash
- Per recovery da corruption

### 9.3 VACUUM Index

**VACUUM** gestisce automaticamente il bloat:

```sql
-- VACUUM standard (libera spazio, non ricompatta)
VACUUM orders;

-- VACUUM con verbose output
VACUUM VERBOSE orders;

-- VACUUM FULL (ricostruisce la tabella interamente)
VACUUM FULL orders;

-- VACUUM con freeze (per transaction wraparound)
VACUUM FREEZE orders;
```

**Differenze**:
- **VACUUM**: Marca lo spazio come riutilizzabile, non riduce la dimensione fisica del file
- **VACUUM FULL**: Ricostruisce la tabella compatta, richiede ACCESS EXCLUSIVE lock

**Autovacuum**: L'autovacuum gestisce automaticamente la manutenzione. Assicurarsi che sia abilitato e correttamente configurato.

### 9.4 Monitoring Bloat

Monitorare regolarmente il bloat:

```sql
-- Verificare bloat con pgstattuple
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size,
    (avg_leaf_fragmentation + avg_leaf_density) / 2 as frag_pct
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Query più dettagliata
SELECT 
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    n_tup_del,
    n_tup_dead,
    n_live_tup
FROM pg_stat_user_tables t
JOIN pg_stat_user_indexes i ON t.relid = i.relid
WHERE n_tup_dead > 0
ORDER BY n_tup_dead DESC;

-- Verificare quando è stato l'ultimo VACUUM/ANALYZE
SELECT 
    schemaname,
    relname,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY last_autovacuum NULLS LAST;
```

---

## 10. Index Tuning Strategies

### 10.1 Identify Missing Indexes

Identificare le query che mancano di indici:

```sql
-- Abilitare pg_stat_statements
CREATE EXTENSION pg_stat_statements;

-- Query più lente per tempo totale
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows,
    shared_blks_hit,
    shared_blks_read
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Query con molte read (probabilmente manca indice)
SELECT 
    query,
    calls,
    shared_blks_read,
    shared_blks_hit,
    round(shared_blks_hit::numeric / nullif(shared_blks_hit + shared_blks_read, 0), 3) as cache_hit_ratio
FROM pg_stat_statements
WHERE shared_blks_read > 0
ORDER BY shared_blks_read DESC
LIMIT 20;
```

**Log slow queries**:
```sql
-- Configurare per loggare query lente
SET log_min_duration_statement = 1000;  -- log queries > 1s

-- Nel postgresql.conf:
-- log_min_duration_statement = 1000
-- log_statement = 'none'
-- log_line_prefix = '%t [%p] '
```

### 10.2 Explain Analyze

Analizzare il piano di esecuzione per verificare l'uso degli indici:

```sql
-- Analisi base
EXPLAIN SELECT * FROM orders WHERE status = 'pending';

-- Analisi con timing reale (esegue la query!)
EXPLAIN ANALYZE 
SELECT * FROM orders WHERE status = 'pending';

-- Con buffer info
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM orders WHERE customer_id = 123;

-- Formattazione leggibile
EXPLAIN (ANALYZE, FORMAT JSON) 
SELECT * FROM orders WHERE status = 'pending'\g
```

**Interpretazione**:
- **Seq Scan**: Scansione completa della tabella (spesso cattivo)
- **Index Scan**: Usa l'indice per trovare righe
- **Index Only Scan**: Usa solo l'indice (ottimo)
- **Bitmap Scan**: Combina risultati di multiple condizioni
- **Recheck Cond**: La condizione deve essere rivalutata nella heap

### 10.3 Index Recommendations

Linee guida per creare indici:

**Colonne in WHERE**:
```sql
-- WHERE column = value
CREATE INDEX idx_col ON table(column);

-- WHERE column IN (list)
CREATE INDEX idx_col ON table(column);

-- WHERE column BETWEEN a AND b
CREATE INDEX idx_col ON table(column);
```

**Colonne in JOIN**:
```sql
-- JOIN su foreign key
CREATE INDEX idx_fk ON order_items(product_id);
```

**Colonne in ORDER BY**:
```sql
-- ORDER BY column
CREATE INDEX idx_order ON table(column);

-- ORDER BY column1, column2
CREATE INDEX idx_order ON table(column1, column2);
```

**Foreign Keys**: Sempre indicizzare le colonne foreign key per performance di JOIN e per referential integrity actions.

### 10.4 Unused Indexes

Trovare e rimuovere indici non utilizzati:

```sql
-- Indici mai usati
SELECT 
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE '%pkey%'
AND indexrelname NOT LIKE '%_pkey%';

-- Indici usati raramente (ultimi 30 giorni)
SELECT 
    indexrelname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE idx_scan < 10
ORDER BY idx_scan;

-- Monitorare nel tempo
-- Confrontare snapshot di pg_stat_user_indexes
SELECT 
    indexrelname,
    idx_scan as scans_now,
    (SELECT idx_scan FROM pg_stat_user_indexes i2 
     WHERE i2.indexrelname = i1.indexrelname 
     AND i2.relname = i1.relname 
     AND i2.schemaname = i1.schemaname
     ORDER BY indexrelname 
     OFFSET 1) as scans_before
FROM pg_stat_user_indexes i1
ORDER BY scans_now - COALESCE(scans_before, 0);
```

**Prima di eliminare**:
- Verificare che l'indice non sia usato per constraint (primary key, unique)
- Considerare se la tabella è molto piccola
- Aspettare almeno un ciclo di query completo prima di decidere

### 10.5 Indexes Performance Tips

Best practices per l'ottimizzazione degli indici:

**Creare indici selettivi**:
```sql
-- Invece di indicizzare tutto, considerare indici parziali
CREATE INDEX idx_recent_orders ON orders(id) 
WHERE created_at > current_date - interval '90 days';
```

**Usare covering indexes**:
```sql
-- Query che accede frequentemente certe colonne
CREATE INDEX idx_cover ON orders(customer_id, created_at) 
INCLUDE (total, status);
```

**Considerare l'ordine delle colonne**:
```sql
-- Per query WHERE a = 1 AND b > 10
CREATE INDEX idx_ab ON table(a, b);
```

**Monitorare e mantenere**:
```sql
-- Automatizzare il monitoraggio
-- Rimuovere indici non usati dopo periodo di osservazione
-- Reindex periodicamente se bloat è alto
```

**Capire i trade-offs**:
- Ogni indice aggiunge overhead di scrittura
- Indici multipli possono essere combinati in Bitmap Scan
- Troppi indici possono degradare le performance di scrittura

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*