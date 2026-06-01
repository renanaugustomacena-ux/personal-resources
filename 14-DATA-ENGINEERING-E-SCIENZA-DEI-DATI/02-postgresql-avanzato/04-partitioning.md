# PostgreSQL Partitioning

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
1. Table Partitioning Fundamentals
2. Range Partitioning
3. List Partitioning
4. Hash Partitioning
5. Partition Management
6. Partition Pruning
7. Partitioning Best Practices
8. Performance Considerations
9. Migration to Partitioned Tables
10. Monitoring Partitioned Tables

---

## 1. Table Partitioning Fundamentals

### 1.1 Cos'è il Partitioning

Il **partitioning** è una tecnica di design del database che divide una grande tabella logica in multiple partizioni fisiche più piccole. Ogni partizione contiene un sottoinsieme dei dati, ma dalla prospettiva dell'applicazione appare come una singola tabella unificata.

**Concetto fondamentale**: Invece di memorizzare tutti i dati in una singola tabella fisica, i dati vengono distribuiti across multiple tabelle figlio (partitions), ciascuna contenente una porzione dei dati. La tabella padre (parent table) non contiene dati propri, ma serve come contenitore logico che definisce la struttura e le regole di partizionamento.

**Come funziona**: Quando un'INSERT o UPDATE viene eseguita sulla tabella partizionata, PostgreSQL automaticamente determina quale partizione contiene (o dovrebbe contenere) quella riga basandosi sui valori della colonna di partizionamento. Questo processo è completamente trasparente all'applicazione.

**Vantaggi principali**:
- **Query Performance**: Il partition pruning permette di saltare automaticamente le partizioni non rilevanti per una query
- **Bulk Operations**: Operazioni su singole partizioni sono più efficienti (archiviazione, backup, DELETE bulk)
- **Data Lifecycle Management**: Gestione semplificata dei dati storici (archiviazione, cancellazione)
- **Maintenance**: VACUUM, ANALYZE, e backup possono essere eseguiti su singole partizioni

### 1.2 Vantaggi del Partitioning

I benefici concreti del partitioning includono:

**Performance delle query**:
```sql
-- Query su tabella partizionata per data
SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-01-31';
-- PostgreSQL esegue solo scan sulla partizione 2024_01
-- Le altre partizioni vengono automaticamente saltate
```

**Efficient bulk deletes**: Eliminare dati vecchi è molto più veloce:
```sql
-- Eliminare dati di un anno - operazione su singola partizione
ALTER TABLE orders DETACH PARTITION orders_2023;
-- I dati vengono rimossi senza scan dell'intera tabella
```

**Manutenzione granulare**: Ogni partizione può essere gestita indipendentemente:
- VACUUM su partizioni specifiche
- Reindex di singole partizioni
- Backup selettivi

**Parallel query support**: Le query che attraversano multiple partizioni possono eseguirle in parallelo

### 1.3 Partition Types

PostgreSQL supporta tre tipi principali di partizionamento:

**Range Partitioning**: Le partizioni contengono righe dove la chiave di partizionamento cade all'interno di un range definito. Ideale per date, numeri sequenziali, o любой range ordinabile.

**List Partitioning**: Le partizioni contengono righe con valori specifici della chiave (discrete values). Ideale per categorie, regioni, o status.

**Hash Partitioning**: Le partizioni sono determinate dal resto della divisione (modulo) della chiave. Ideale per distribuzione uniforme quando non c'è un pattern naturale.

### 1.4 Declarative Partitioning

PostgreSQL usa il **declarative partitioning**, introdotto in PostgreSQL 10, come metodo nativo e consigliato:

```sql
-- Definire una tabella partizionata
CREATE TABLE orders (
    id BIGSERIAL,
    created_at TIMESTAMP NOT NULL,
    customer_id BIGINT NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
```

La tabella padre ha una struttura identica a una tabella normale, ma include la clausola PARTITION BY che specifica il tipo e la colonna di partizionamento.

**Limitazioni della tabella padre**: La tabella parent non può avere dati propri (eccetto NULL in alcuni casi), non può avere indici unique che non includano la chiave di partizionamento, e alcune constraint possono essere applicate solo sulle partizioni.

---

## 2. Range Partitioning

### 2.1 Definizione

Il **Range Partitioning** divide i dati in partizioni basate su intervalli di valori. È il tipo più comune di partizionamento, particolarmente efficace per dati temporali o sequenziali.

```sql
CREATE TABLE orders (
    id BIGSERIAL,
    created_at TIMESTAMP NOT NULL,
    customer_id BIGINT NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
```

La colonna di partizionamento (created_at) determina quale partizione ospita ogni riga. Le partizioni sono definite con range esclusivi (FROM ... TO ...).

### 2.2 Partitions Creation

Creare partizioni per intervalli specifici:

```sql
-- Partizione per anno 2024
CREATE TABLE orders_2024 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Partizione per anno 2025
CREATE TABLE orders_2025 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Partizione per mese (esempio)
CREATE TABLE orders_2024_01 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE orders_2024_02 PARTITION OF orders
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

**Nota importante**: Il valore TO è esclusivo. Una riga con created_at = '2025-01-01' (mezzanotte del primo gennaio) andrebbe nella partizione 2025, non in quella 2024.

### 2.3 Default Partition

Una partizione di default cattura righe che non corrispondono a nessuna altra partizione:

```sql
CREATE TABLE orders_default PARTITION OF orders
    DEFAULT;
```

**Usi della default partition**:
- Catturare dati fuori dal range normale
- Semplificare la gestione durante la transizione
- Prevenire errori per dati non previsti

**Attenzione**: Una default partition può diventare un "catch-all" che accumula dati inaspettatamente. Monitorare regolarmente le dimensioni.

### 2.4 Composite Partitioning

Il partizionamento composito usa multiple colonne per definire i range:

```sql
CREATE TABLE logs (
    id BIGSERIAL,
    log_date DATE NOT NULL,
    service VARCHAR(50) NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT
) PARTITION BY RANGE (log_date, service);
```

Con partizionamento composito:
- Prima colonna (log_date) definisce il range primario
- Seconda colonna (service) per subrange dentro ogni partition

```sql
CREATE TABLE logs_2024 PARTITION OF logs
    FOR VALUES FROM ('2024-01-01', 'auth') TO ('2024-01-02', 'auth');

CREATE TABLE logs_2024_service PARTITION OF logs
    FOR VALUES FROM ('2024-01-01', MINVALUE) TO ('2025-01-01', MAXVALUE);
```

---

## 3. List Partitioning

### 3.1 Definizione

Il **List Partitioning** assegna righe a partizioni basandosi su valori discreti specifici della chiave. A differenza del range, non c'è ordinamento implicito - ogni partizione contiene righe con valori specifici.

```sql
CREATE TABLE products (
    id BIGSERIAL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id, category)
) PARTITION BY LIST (category);
```

### 3.2 Partition Creation

Creare partizioni per categorie specifiche:

```sql
-- Elettronica e computers
CREATE TABLE products_electronics PARTITION OF products
    FOR VALUES IN ('electronics', 'computers', 'phones', 'tablets');

-- Abbigliamento
CREATE TABLE products_clothing PARTITION OF products
    FOR VALUES IN ('clothing', 'shoes', 'accessories');

-- Casa e giardino
CREATE TABLE products_home PARTITION OF products
    FOR VALUES IN ('home', 'garden', 'furniture');

-- Sport
CREATE TABLE products_sports PARTITION OF products
    FOR VALUES IN ('sports', 'outdoor', 'fitness');
```

**Nota**: Ogni valore può appartenere a una sola partizione. Non c'è sovrapposizione tra partizioni.

### 3.3 Use Cases

Il List Partitioning è ideale per:

**Geographic partitioning**:
```sql
CREATE TABLE sales (
    id BIGSERIAL,
    region VARCHAR(20) NOT NULL,
    amount DECIMAL(12,2)
) PARTITION BY LIST (region);

CREATE TABLE sales_europe PARTITION OF sales FOR VALUES IN ('EU', 'UK', 'DE', 'FR');
CREATE TABLE sales_americas PARTITION OF sales FOR VALUES IN ('US', 'CA', 'MX', 'BR');
CREATE TABLE sales_asia PARTITION OF sales FOR VALUES IN ('CN', 'JP', 'IN', 'KR');
```

**Status-based partitioning**:
```sql
CREATE TABLE orders (
    id BIGSERIAL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP
) PARTITION BY LIST (status);

CREATE TABLE orders_active PARTITION OF orders FOR VALUES IN ('pending', 'processing', 'shipped');
CREATE TABLE orders_completed PARTITION OF sales FOR VALUES IN ('delivered', 'cancelled');
```

**Multi-tenant con tenant_id**:
```sql
CREATE TABLE events (
    event_id BIGSERIAL,
    tenant_id INT NOT NULL,
    event_type VARCHAR(50),
    event_time TIMESTAMP
) PARTITION BY LIST (tenant_id);

CREATE TABLE events_tenant_1 PARTITION OF events FOR VALUES IN (1);
CREATE TABLE events_tenant_2 PARTITION OF events FOR VALUES IN (2);
CREATE TABLE events_tenant_3 PARTITION OF events FOR VALUES IN (3);
```

### 3.4 Default in List

Come per Range, una partizione DEFAULT cattura valori non mappati:

```sql
CREATE TABLE products_other PARTITION OF products
    DEFAULT;
```

**Attenzione**: Se tutti i valori possibili sono mappati esplicitamente, la default partition rimarrà vuota. Se ci sono valori non previsti, finiranno nella default partition.

---

## 4. Hash Partitioning

### 4.1 Definizione

Il **Hash Partitioning** usa una funzione hash per determinare la partizione. Questo garantisce una distribuzione uniforme dei dati, indipendentemente dal pattern dei valori.

```sql
CREATE TABLE events (
    id BIGSERIAL,
    user_id BIGINT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload JSONB,
    PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);
```

### 4.2 Partition Creation

Il number di partizioni è fisso e definito al momento della creazione:

```sql
-- Creare 4 partizioni
CREATE TABLE events_0 PARTITION OF events
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE events_1 PARTITION OF events
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE events_2 PARTITION OF events
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE events_3 PARTITION OF events
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

**MODULUS e REMAINDER**:
- MODULUS: il numero totale di partizioni
- REMAINDER: quale partizione per quel resto

Il calcolo è: hash(user_id) MOD 4 = remainder → partizione corrispondente

### 4.3 Distribution

La distribuzione dipende dalla qualità della funzione hash:

**Vantaggi**:
- Distribuzione uniforme anche per dati skewed
- Nessun "hot spot" su partizioni specifiche
- Prevedibile dimensione delle partizioni

**Svantaggi**:
- Non puoi sapere in anticipo quale partizione contiene quali dati
- Non puoi "arciviare" dati vecchi eliminano una partizione
- Query che filtra per la chiave di partizionamento possono accedere tutte le partizioni

### 4.4 Use Cases

Il Hash Partitioning è appropriato quando:

**Nessun pattern naturale**: I dati non hanno una colonna con distribuzione temporale o categoriale naturale.

**Distribuzione uniforme richiesta**: Quando vuoi assicurarti che nessuna partizione diventi eccessivamente grande.

**Scaling orizzontale**: Per prepararsi a future partizioni aggiuntive.

```sql
-- Eventi utente senza pattern temporale
CREATE TABLE user_sessions (
    session_id BIGSERIAL,
    user_id BIGINT NOT NULL,
    session_start TIMESTAMP,
    session_end TIMESTAMP
) PARTITION BY HASH (user_id);

-- 8 partizioni per bilanciamento
CREATE TABLE user_sessions_0 PARTITION OF user_sessions FOR VALUES WITH (MODULUS 8, REMAINDER 0);
-- ... ripetere per 1-7
```

---

## 5. Partition Management

### 5.1 ATTACH Partition

Aggiungere una partizione a una tabella esistente:

```sql
-- Creare la partizione (può essere vuota o avere dati)
CREATE TABLE orders_2026 (
    LIKE orders INCLUDING ALL
);

-- Popolare la partizione (opzionale)
INSERT INTO orders_2026 SELECT * FROM staging WHERE created_at >= '2026-01-01';

-- Attach alla tabella parent
ALTER TABLE orders ATTACH PARTITION orders_2026
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

**Requisiti per attach**:
- La partizione deve avere schema compatibile con la parent
- I valori nella partizione devono rientrare nel range definito
- Nessun conflitto con constraint esistenti

### 5.2 DETACH Partition

Rimuovere una partizione dalla gerarchia:

```sql
-- Detach semplice (la partizione diventa tabella standalone)
ALTER TABLE orders DETACH PARTITION orders_2024;

-- Detach con/conversion (da PostgreSQL 12+)
ALTER TABLE orders DETACH PARTITION orders_2024 CONCURRENTLY;
ALTER TABLE orders DETACH PARTITION orders_2024 FINALIZE;
```

**Opzioni**:
- **DETACH PARTITION**: Rimuove la partizione, diventa tabella indipendente
- **DETACH CONCURRENTLY**: Non blocca writes sulla tabella parent (richiede PostgreSQL 12+)
- **DROP PARTITION**: Elimina completamente la partizione e i suoi dati

```sql
-- Eliminare una partizione vecchia
ALTER TABLE orders DROP PARTITION orders_2023;
```

### 5.3 Split Partition

PostgreSQL non supporta split diretto di partizioni. La strategia è:

```sql
-- 1. Detach la partizione da dividere
ALTER TABLE orders DETACH PARTITION orders_2024;

-- 2. Creare due nuove partizioni
CREATE TABLE orders_2024_H1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-07-01');

CREATE TABLE orders_2024_H2 PARTITION OF orders
    FOR VALUES FROM ('2024-07-01') TO ('2025-01-01');

-- 3. Copiare i dati nella partizione appropriata
INSERT INTO orders_2024_H1 SELECT * FROM orders_2024 WHERE created_at < '2024-07-01';
INSERT INTO orders_2024_H2 SELECT * FROM orders_2024 WHERE created_at >= '2024-07-01';

-- 4. Eliminare la vecchia tabella
DROP TABLE orders_2024;
```

### 5.4 Rename Partitions

Rinominare partizioni:

```sql
-- Rinominare una partizione
ALTER TABLE orders RENAME PARTITION orders_2024 TO orders_archive_2024;

-- Verificare il nome
SELECT relname FROM pg_class WHERE relname LIKE 'orders_%';
```

### 5.5 Truncate Partition

Truncated tutti i dati in una partizione:

```sql
-- Truncate di una partizione (più veloce di DELETE)
TRUNCATE TABLE orders_2024;
```

Questa operazione è significativamente più veloce di DELETE FROM perché non genera tuple morte e non richiede VACUUM successivo.

---

## 6. Partition Pruning

### 6.1 Automatic Pruning

Il **Partition Pruning** è l'ottimizzazione che permette a PostgreSQL di saltare automaticamente le partizioni non rilevanti per una query:

```sql
-- Query che cerca dati di un anno specifico
EXPLAIN SELECT * FROM orders WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';

-- Output mostra solo scan su partizioni rilevanti
-- -> Append (cost=0.00..100.00)
--    -> Seq Scan on orders_2024
--    -> Seq Scan on orders_2025 (lettà ma non usata per i criteri)
```

PostgreSQL determina a compile-time quali partizioni possono contenere dati che matchano la query e salta le altre.

### 6.2 Constraint Exclusion

La funzionalità che abilita il pruning è **constraint_exclusion**:

```sql
-- Valori possibili
SET constraint_exclusion = on;         -- Abilita per tutte le tabelle
SET constraint_exclusion = off;         -- Disabilita completamente
SET constraint_exclusion = partition;   -- Solo per tabelle partizionate (default)
```

Il default (partition) è raccomandato - abilita pruning solo per tabelle partizionate senza overhead per tabelle normali.

### 6.3 Dynamic Pruning

Il pruning dinamico avviene quando i parametri non sono noti a compile-time:

```sql
-- Parametro esterno - pruning a runtime
PREPARE stmt(DATE) AS SELECT * FROM orders WHERE created_at = $1;
EXECUTE stmt('2024-06-15');
-- Il piano viene eseguito con pruning dinamico
```

**Execution-time pruning**: Quando la query usa parametri, PostgreSQL esegue il pruning durante l'esecuzione invece che durante il planning.

### 6.4 Planning vs Execution

**Planning-time pruning**: Noto a compile-time. Più efficiente perché il piano è ottimizzato per le partizioni specifiche.

**Execution-time pruning**: Necessario quando i parametri sono dinamici. Leggermente meno efficiente ma comunque corretto.

**Esempio con subquery**:
```sql
-- Subquery rende impossibile il planning-time pruning
SELECT * FROM orders WHERE created_at = (
    SELECT MAX(created_at) FROM orders WHERE status = 'shipped'
);
-- PostgreSQL può solo fare execution-time pruning
```

### 6.5 Verificare il Pruning

```sql
-- Verificare che il pruning avvenga
EXPLAIN (COSTS OFF) SELECT * FROM orders WHERE created_at = '2024-06-15';

-- Se funziona, vedrai solo le partizioni rilevanti
-- Se non funziona, vedrai "on all partitions"
```

---

## 7. Partitioning Best Practices

### 7.1 Partition Size

Le dimensioni delle partizioni influenzano significativamente le performance:

**Raccomandazioni**:
- Partizioni tra **10-50GB** ciascuna sono gestibili
- Partizioni più piccole hanno più overhead di gestione
- Partizioni più grandi possono essere meno efficienti

**Numero di partizioni**:
- Non troppe: overhead di 查询 planning
- Non poche: poco beneficio dal pruning
- Tipicamente 10-100 partizioni è un buon range

**Esempio pratico**:
```sql
-- Per una tabella da 500GB con dati di 5 anni
-- Range annuale -> 5 partizioni da ~100GB (troppo grandi)
-- Range mensile -> 60 partizioni da ~8GB (gestibile)
-- Range settimanale -> 260 partizioni (troppe?)
```

### 7.2 Column Selection

La scelta della colonna di partizionamento è critica:

**Criteri**:
1. **Frequenza nelle WHERE**: La colonna dovrebbe apparire frequentemente nei filtri
2. **Cardinalità**: Valori distribuiti uniformemente
3. **Stabilità**: Non dovrebbe essere aggiornata frequentemente
4. **Dimensione**: Non troppo grande (limita overhead)

**Candidati comuni**:
- Timestamp/date per dati temporali
- Region/country per dati geografici
- Category/type per dati categorici
- Tenant_id per multi-tenant

**Evitare**:
- Colonne con alta cardinalità unica
- Colonne frequentemente aggiornate
- Colonne con molti NULL

### 7.3 Partition Maintenance

Un piano di manutenzione robusto include:

**Creazione proattiva delle partizioni**:
```sql
-- Script per creare partizioni future
DO $$
DECLARE
    y INT;
    m INT;
BEGIN
    FOR y IN 2025..2027 LOOP
        FOR m IN 1..12 LOOP
            EXECUTE format('CREATE TABLE IF NOT EXISTS orders_%I PARTITION OF orders FOR VALUES FROM (%L) TO (%L)',
                to_char(y, '9999') || '_' || to_char(m, '09'),
                make_date(y, m, 1)::text,
                make_date(y, m + 1, 1)::text
            );
        END LOOP;
    END LOOP;
END $$;
```

**Archiviazione delle partizioni vecchie**:
```sql
-- Storicizzare dati vecchi
-- 1. Detach partizione
ALTER TABLE orders DETACH PARTITION orders_2023;

-- 2. Spostare su storage più economico
-- (dipende dall'infrastruttura)

-- 3. Oppure eliminare se non più necessari
DROP TABLE orders_2023;
```

**Monitoraggio crescita**:
```sql
-- Controllare dimensioni delle partizioni
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as size
FROM pg_tables
WHERE tablename LIKE 'orders_%'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;
```

### 7.4 Indexes

Le strategie di indicizzazione per tabelle partizionate:

**Indici su ogni partizione**:
```sql
-- Ogni partizione ha i propri indici
CREATE INDEX ON orders_2024 (customer_id);
CREATE INDEX ON orders_2025 (customer_id);
-- etc.
```

**Partial indexes**:
```sql
-- Index su partizioni specifiche per query frequenti
CREATE INDEX ON orders_2024 (status) WHERE status = 'pending';
CREATE INDEX ON orders_2025 (status) WHERE status = 'pending';
```

**Indici sulla parent**:
```sql
-- Non sono generalmente necessari - i dati sono nelle partizioni
-- Ma possono essere utili per constraint
CREATE UNIQUE INDEX ON orders (id, created_at);
```

**Non su parent**: Se le query filtrovano per la chiave di partizionamento, gli indici sulla parent non sono necessari.

---

## 8. Performance Considerations

### 8.1 Query Performance

Il partitioning offre significativi vantaggi di performance:

**Partition Pruning**: Query che filtrano per la chiave di partizionamento saltano automaticamente le partizioni non rilevanti:

```sql
-- Senza partition pruning
-- Scan dell'intera tabella (500GB)

-- Con partition pruning
-- Scan solo della partizione 2024 (8GB)
SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31';
```

**Less data to scan**: Anche senza pruning completo, ogni partizione è più piccola della tabella intera.

**Parallel query**: Query che accedono multiple partizioni possono parallelizzare lo scan:

```sql
-- PostgreSQL può eseguire scansioni parallele su diverse partizioni
SET max_parallel_workers_per_gather = 4;
SET parallel_leader_participation = on;
```

### 8.2 Write Performance

L'overhead di scrittura è minimo:

**Check di partizionamento**: Ogni INSERT/UPDATE deve determinare la partizione target. Questo è un semplice confronto di constraint, molto veloce.

```sql
-- Costo aggiuntivo trascurabile per INSERT
-- PostgreSQL valuta i constraint delle partizioni
-- Questo è O(1) - solo la partizione giusta viene controllata
```

**Bulk inserts**: Per bulk load, inserire direttamente nelle partizioni è più veloce:

```sql
-- Inserimento diretto nella partizione
INSERT INTO orders_2024 SELECT * FROM staging WHERE created_at >= '2024-01-01';
-- Non passa attraverso la logica di routing
```

### 8.3 Parallel Queries

PostgreSQL supporta query parallele sulle partizioni:

**Parallel Partition Scan**:
```sql
-- Configurazione
SET max_parallel_workers_per_gather = 4;

-- PostgreSQL parallelizza lo scan su partizioni
SELECT * FROM orders WHERE status = 'pending';
-- I worker processano partizioni diverse in parallelo
```

**Limitazioni**:
- Non tutte le operazioni beneficiano del parallelismo
- Il parallelismo ha overhead (non utile per query piccole)
- Dipende da max_parallel_workers_per_gather

### 8.4 Data Loading

Strategie efficienti per il caricamento dati:

**Direct insert to partition**:
```sql
-- Caricare direttamente nella partizione corretta
INSERT INTO orders_2024 SELECT * FROM staging_orders 
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';
```

**Detach and load**:
```sql
-- Per grandi volumi
-- 1. Creare tabella temporanea
CREATE TEMP TABLE staging_orders (LIKE orders);

-- 2. Caricare nella temp
COPY staging_orders FROM '/path/to/file.csv';

-- 3. Spostare nella partizione
INSERT INTO orders_2024 SELECT * FROM staging_orders;

-- 4. Pulire
TRUNCATE staging_orders;
```

**COPY command**:
```sql
-- Direct COPY in partizione
COPY orders_2024 (id, created_at, total, status) 
FROM '/path/to/data.csv' 
WITH (FORMAT csv);
```

---

## 9. Migration to Partitioned Tables

### 9.1 Requisiti

La migrazione a tabelle partizionate richiede pianificazione:

**Passi preliminari**:
1. **Analizzare i pattern di query**: Quali colonne sono usate nei WHERE?
2. **Identificare colonna di partizionamento**: Deve essereFrequently filtered e avere distribuzione adeguata
3. **Pianificare partizioni**: Quante? Quali dimensioni?
4. **Testare con dati reali**: Benchmark con query pattern reali
5. **Pianificare downtime**: La migrazione richiede tempo

### 9.2 Strategy: Create New

La strategia consigliata - creare una nuova tabella partizionata e migrarvi i dati:

```sql
-- 1. Creare la tabella partizionata
CREATE TABLE orders_part (
    id BIGSERIAL,
    created_at TIMESTAMP NOT NULL,
    customer_id BIGINT NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 2. Creare le partizioni iniziali
CREATE TABLE orders_part_2024 PARTITION OF orders_part
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE orders_part_2025 PARTITION OF orders_part
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE orders_part_default PARTITION OF orders_part DEFAULT;

-- 3. Copiare i dati
INSERT INTO orders_part 
SELECT * FROM orders 
ORDER BY created_at;

-- 4. Verificare
SELECT COUNT(*) FROM orders_part;
SELECT COUNT(*) FROM orders;

-- 5. Swap (durante downtime)
BEGIN;
ALTER TABLE orders RENAME TO orders_backup;
ALTER TABLE orders_part RENAME TO orders;
COMMIT;

-- 6. Dopo verifica, eliminare la tabella backup
-- DROP TABLE orders_backup;
```

### 9.3 Strategy: Partition Existing

Per partizionare una tabella esistente senza ricrearla:

```sql
-- Questo approccio non è direttamente supportato
-- La tabella esistente deve diventare una partizione

-- 1. Creare la tabella partizionata
CREATE TABLE orders_part (...) PARTITION BY RANGE (created_at);

-- 2. Rendere la tabella originale una partizione
ALTER TABLE orders_part ATTACH PARTITION orders 
FOR VALUES FROM (SELECT MIN(created_at) FROM orders) 
TO (SELECT MAX(created_at) FROM orders);
```

Questo è utile quando la tabella originale è già molto grande e la migrazione completa richiederebbe troppo tempo.

### 9.4 Downtime

Pianificare il downtime per la migrazione:

**Tempo stimato**:
- COPY di 100GB: ~10-30 minuti (dipende da I/O)
- Index creation: ~5-15 minuti
- Swap: secondi

**Minimizzare downtime**:
- Pre-creare partizioni vuote
- Usare COPY parallelo
- Preparare script per esecuzione rapida

**Rollback plan**:
- Mantenere backup della tabella originale
- Testare la procedura su ambiente simile
- Avere script di rollback pronti

### 9.5 Post-Migration

Dopo la migrazione:

```sql
-- Ricreare indici (non vengono migrati automaticamente)
CREATE INDEX ON orders_part (customer_id);
CREATE INDEX ON orders_part (status);

-- Verificare che le query usino il pruning
EXPLAIN (COSTS OFF) SELECT * FROM orders WHERE created_at = '2024-06-15';

-- Monitorare performance
SELECT * FROM pg_stat_user_tables WHERE relname LIKE 'orders%';
```

---

## 10. Monitoring Partitioned Tables

### 10.1 Check Sizes

Monitorare regolarmente le dimensioni delle partizioni:

```sql
-- Dimensioni di tutte le partizioni
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables
WHERE schemaname = 'public'
AND tablename LIKE 'orders%'
ORDER BY size_bytes DESC;

-- Dimensioni totali
SELECT 
    'orders' as table_name,
    COUNT(*) as partitions,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename LIKE 'orders_%'
AND tablename != 'orders';
```

### 10.2 Check Growth

Monitorare la crescita delle partizioni:

```sql
-- Statistiche di crescita
SELECT 
    schemaname,
    relname as table_name,
    n_live_tup,
    n_dead_tup,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND relname LIKE 'orders_%'
ORDER BY n_live_tup DESC;

-- Partizioni con tuple morte eccessive
SELECT 
    schemaname,
    relname,
    n_dead_tup,
    n_live_tup,
    CASE 
        WHEN n_live_tup > 0 THEN round(n_dead_tup::numeric / n_live_tup * 100, 2)
        ELSE 0 
    END as dead_ratio_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

### 10.3 Partition Usage

Verificare che le query utilizzino il partition pruning:

```sql
-- Verificare pruning per query date-based
EXPLAIN (COSTS OFF, ANALYZE) 
SELECT * FROM orders WHERE created_at >= '2024-01-01' AND created_at < '2024-02-01';

-- Verificare pruning per condizioni specifiche
EXPLAIN (COSTS OFF) 
SELECT * FROM orders WHERE created_at = '2024-06-15' AND status = 'shipped';

-- Monitorare sezioni in pg_stat_user_indexes per indici sulle partizioni
SELECT 
    schemaname,
    relname as table_name,
    indexrelname as index_name,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND relname LIKE 'orders_%'
ORDER BY idx_scan;
```

### 10.4 Maintenance Planning

Pianificare la manutenzione delle partizioni:

```sql
-- Script per identificare partizioni che necessitano manutenzione
SELECT 
    schemaname,
    relname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as size,
    last_vacuum,
    last_autovacuum,
    CASE 
        WHEN last_autovacuum IS NULL OR last_autovacuum < now() - interval '7 days' 
        THEN 'needs vacuum'
        ELSE 'ok'
    END as vacuum_status
FROM pg_stat_user_tables
WHERE relname LIKE 'orders_%'
ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC;

-- Monitorare partizioni "orfane" o non più utilizzate
SELECT 
    schemaname,
    tablename
FROM pg_tables
WHERE schemaname = 'public'
AND tablename LIKE 'orders_%'
AND tablename != 'orders'
AND NOT EXISTS (
    SELECT 1 FROM pg_class c 
    WHERE c.relname = tablename 
    AND c.relrowsecurity = false
);
```

**Checklist di manutenzione**:
- [ ] VACUUM regolare su partizioni con alto dead_tup
- [ ] ANALYZE dopo bulk loads
- [ ] REINDEX se bloat eccessivo
- [ ] Monitorare crescita e creare partizioni proattivamente
- [ ] Archiviare/eliminare partizioni vecchie

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*