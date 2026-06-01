---
corso: "Sviluppo Web"
fase: "4 — Backend"
modulo: "12"
titolo: "Database per lo Sviluppo Web"
versione: "PostgreSQL 16 / Prisma 5.x / Drizzle ORM / Redis 7.x"
livello: "Intermedio"
prerequisiti:
  - "10 — Node.js"
  - "06 — TypeScript"
obiettivi:
  - "Modellare dati relazionali con PostgreSQL e SQL avanzato"
  - "Utilizzare ORM type-safe (Prisma, Drizzle) per query e migrazioni"
  - "Implementare caching con Redis e strategie di invalidazione"
  - "Comprendere NoSQL (MongoDB, DynamoDB) e quando usarlo"
  - "Ottimizzare query con indici, EXPLAIN e connection pooling"
  - "Gestire migrazioni di schema in modo sicuro"
tag: [database, PostgreSQL, Prisma, Drizzle, Redis, SQL, migrazioni, ORM]
---

# Database per lo Sviluppo Web

> **Modulo 12** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Node.js](10-nodejs.md), [TypeScript](06-typescript.md)
>
> Al termine di questo modulo saprai:
> 1. Modellare dati relazionali con PostgreSQL e SQL avanzato
> 2. Utilizzare ORM type-safe (Prisma, Drizzle) per query e migrazioni
> 3. Implementare caching con Redis e strategie di invalidazione
> 4. Comprendere NoSQL (MongoDB, DynamoDB) e quando usarlo
> 5. Ottimizzare query con indici, EXPLAIN e connection pooling
> 6. Gestire migrazioni di schema in modo sicuro
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio

## Idee guida
1. **Postgres > MySQL per nuovi progetti.** JSONB, generated columns, RLS.
2. **Prisma > Drizzle > raw SQL: trade-off type-safety vs flexibility.**
3. **Connection pool nei serverless: PgBouncer transaction mode.**
4. **Read replica per scalability.** Beware of replication lag.


## Indice

1. [Panoramica](#panoramica)
2. [SQL Fondamenti](#sql-fondamenti)
3. [PostgreSQL](#postgresql)
4. [MySQL e MariaDB](#mysql-e-mariadb)
5. [MongoDB](#mongodb)
6. [Redis](#redis)
7. [ORM e Query Builder](#orm-e-query-builder)
8. [Migrazioni](#migrazioni)
9. [Database Design](#database-design)
10. [Performance e Ottimizzazione](#performance-e-ottimizzazione)
11. [Best Practices](#best-practices)
12. [Prisma Avanzato](#prisma-avanzato)
13. [Drizzle ORM Approfondimento](#drizzle-orm-approfondimento)
14. [Strategie di Migrazione Avanzate](#strategie-di-migrazione-avanzate)
15. [Connection Pooling Avanzato](#connection-pooling-avanzato)
16. [Performance Avanzata del Database](#performance-avanzata-del-database)
17. [Sicurezza del Database](#sicurezza-del-database)
18. [MongoDB con Mongoose](#mongodb-con-mongoose)
19. [Database Testing](#database-testing)
20. [Pattern Multi-Tenancy](#pattern-multi-tenancy)
21. [Monitoraggio e Osservabilità](#monitoraggio-e-osservabilità)
22. [Database Edge e Serverless](#database-edge-e-serverless)
23. [Ricerca Full-Text Avanzata](#ricerca-full-text-avanzata)

---

## Panoramica

I database rappresentano il fondamento di qualsiasi applicazione web non triviale. Ogni volta che un utente si registra, pubblica un contenuto, effettua un acquisto o semplicemente naviga una pagina dinamica, dietro le quinte un database memorizza, organizza e restituisce i dati necessari. La scelta del database influenza profondamente l'architettura, le prestazioni, la scalabilita e la manutenibilita dell'intero sistema. Comprendere le differenze tra le famiglie di database, i loro modelli di dati e i contesti d'uso ottimali e una competenza imprescindibile per ogni sviluppatore web.

### SQL vs NoSQL

Il panorama dei database si divide in due grandi famiglie: i database **relazionali** (SQL) e i database **non relazionali** (NoSQL). Questa distinzione non e meramente tecnica, ma riflette filosofie profondamente diverse nella modellazione e gestione dei dati.

I **database relazionali** organizzano i dati in tabelle con righe e colonne, legate tra loro tramite chiavi primarie e chiavi esterne. Ogni tabella ha uno schema rigido definito a priori: ogni colonna ha un tipo di dato specifico e vincoli di integrita. Questa rigidita e un punto di forza, non un limite, perche garantisce coerenza e affidabilita dei dati. I database SQL rispettano le proprieta ACID (Atomicity, Consistency, Isolation, Durability), assicurando che ogni transazione venga completata interamente o annullata senza lasciare il sistema in uno stato inconsistente. Esempi principali: PostgreSQL, MySQL, MariaDB, SQLite, Microsoft SQL Server, Oracle Database.

I **database NoSQL** abbandonano il modello tabulare a favore di strutture piu flessibili. Si suddividono in quattro sottocategorie principali:

| Tipo | Struttura dati | Esempi | Caso d'uso tipico |
|------|----------------|--------|---------------------|
| Document store | Documenti JSON/BSON | MongoDB, CouchDB | CMS, cataloghi prodotti, profili utente |
| Key-value store | Coppie chiave-valore | Redis, DynamoDB, Memcached | Caching, sessioni, configurazioni |
| Column-family | Colonne raggruppate | Cassandra, HBase, ScyllaDB | Time-series, analytics su larga scala |
| Graph database | Nodi e relazioni | Neo4j, ArangoDB, Amazon Neptune | Social network, recommendation engine |

### Quando usare SQL

I database relazionali sono la scelta ottimale quando i dati hanno una struttura ben definita e stabile, quando l'integrita referenziale e critica, quando le transazioni ACID sono un requisito e quando le query coinvolgono JOIN complesse tra entita correlate. Applicazioni finanziarie, sistemi ERP, piattaforme e-commerce con inventario complesso e qualsiasi sistema dove la coerenza dei dati e non negoziabile beneficiano enormemente del modello relazionale. Se il dominio dei dati puo essere rappresentato naturalmente come un insieme di tabelle interconnesse, SQL e quasi sempre la scelta giusta.

### Quando usare NoSQL

I database NoSQL eccellono quando la struttura dei dati e eterogenea o evolve frequentemente, quando si necessita di scalabilita orizzontale massiva, quando le prestazioni in lettura e scrittura ad alta velocita sono prioritarie rispetto alla coerenza immediata e quando i dati si modellano naturalmente come documenti, grafi o coppie chiave-valore. Applicazioni real-time, sistemi di caching, piattaforme IoT con milioni di dispositivi e content management system con schemi flessibili traggono vantaggio dall'approccio NoSQL.

La realta e che la maggior parte delle applicazioni web moderne adotta un approccio **poliglotta**: un database relazionale come source of truth principale, affiancato da Redis per il caching e le sessioni, eventualmente MongoDB per contenuti con struttura variabile. Non si tratta di scegliere uno o l'altro, ma di combinare gli strumenti giusti per ogni esigenza specifica.

---

## SQL Fondamenti

SQL (Structured Query Language) e il linguaggio standard per interagire con i database relazionali. Nonostante ogni DBMS implementi estensioni proprietarie, il nucleo del linguaggio e universale e portatile. SQL si divide in sottolinguaggi distinti: DDL per la definizione delle strutture, DML per la manipolazione dei dati, DCL per il controllo degli accessi e TCL per la gestione delle transazioni.

### DDL — Data Definition Language

Il DDL definisce la struttura del database: tabelle, colonne, vincoli, indici. Le operazioni DDL sono tipicamente irreversibili e modificano lo schema del database.

#### CREATE

```sql
-- Creazione di un database
CREATE DATABASE ecommerce
  ENCODING 'UTF8'
  LC_COLLATE 'it_IT.UTF-8';

-- Creazione di una tabella con vincoli completi
CREATE TABLE utenti (
  id            SERIAL PRIMARY KEY,
  email         VARCHAR(255) NOT NULL UNIQUE,
  username      VARCHAR(50) NOT NULL,
  password_hash CHAR(60) NOT NULL,
  nome          VARCHAR(100),
  cognome       VARCHAR(100),
  ruolo         VARCHAR(20) DEFAULT 'utente' CHECK (ruolo IN ('utente', 'admin', 'moderatore')),
  attivo        BOOLEAN DEFAULT TRUE,
  creato_il     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  aggiornato_il TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Creazione di una tabella con chiave esterna
CREATE TABLE ordini (
  id          SERIAL PRIMARY KEY,
  utente_id   INTEGER NOT NULL REFERENCES utenti(id) ON DELETE CASCADE,
  totale      DECIMAL(10, 2) NOT NULL CHECK (totale >= 0),
  stato       VARCHAR(20) DEFAULT 'in_attesa',
  creato_il   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Creazione di una tabella ponte per relazioni N:M
CREATE TABLE ordini_prodotti (
  ordine_id   INTEGER REFERENCES ordini(id) ON DELETE CASCADE,
  prodotto_id INTEGER REFERENCES prodotti(id) ON DELETE RESTRICT,
  quantita    INTEGER NOT NULL CHECK (quantita > 0),
  prezzo      DECIMAL(10, 2) NOT NULL,
  PRIMARY KEY (ordine_id, prodotto_id)
);
```

#### ALTER

```sql
-- Aggiungere una colonna
ALTER TABLE utenti ADD COLUMN telefono VARCHAR(20);

-- Modificare il tipo di una colonna
ALTER TABLE utenti ALTER COLUMN username TYPE VARCHAR(100);

-- Aggiungere un vincolo
ALTER TABLE utenti ADD CONSTRAINT email_formato
  CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Rinominare una colonna
ALTER TABLE utenti RENAME COLUMN nome TO first_name;

-- Eliminare una colonna
ALTER TABLE utenti DROP COLUMN telefono;

-- Aggiungere un indice
CREATE INDEX idx_utenti_email ON utenti(email);
CREATE INDEX idx_ordini_utente ON ordini(utente_id);
```

#### DROP

```sql
-- Eliminare una tabella (con cautela!)
DROP TABLE IF EXISTS ordini_prodotti;

-- Eliminare a cascata (rimuove anche oggetti dipendenti)
DROP TABLE ordini CASCADE;

-- Eliminare un database
DROP DATABASE IF EXISTS ecommerce;

-- Svuotare una tabella mantenendo la struttura
TRUNCATE TABLE log_accessi RESTART IDENTITY;
```

### DML — Data Manipulation Language

Il DML gestisce i dati all'interno delle tabelle: inserimento, lettura, aggiornamento e cancellazione (le operazioni CRUD).

#### SELECT

```sql
-- Selezione base con alias e ordinamento
SELECT
  u.id,
  u.nome || ' ' || u.cognome AS nome_completo,
  u.email,
  u.ruolo
FROM utenti u
WHERE u.attivo = TRUE
ORDER BY u.cognome ASC, u.nome ASC;

-- Filtraggio avanzato
SELECT *
FROM prodotti
WHERE prezzo BETWEEN 10.00 AND 50.00
  AND categoria IN ('elettronica', 'accessori')
  AND nome ILIKE '%wireless%'
  AND disponibile = TRUE
ORDER BY prezzo DESC
LIMIT 20 OFFSET 40;

-- Funzioni aggregate e GROUP BY
SELECT
  categoria,
  COUNT(*) AS totale_prodotti,
  AVG(prezzo)::NUMERIC(10,2) AS prezzo_medio,
  MIN(prezzo) AS prezzo_minimo,
  MAX(prezzo) AS prezzo_massimo,
  SUM(quantita_magazzino) AS stock_totale
FROM prodotti
WHERE attivo = TRUE
GROUP BY categoria
HAVING COUNT(*) > 5
ORDER BY totale_prodotti DESC;
```

#### INSERT

```sql
-- Inserimento singolo
INSERT INTO utenti (email, username, password_hash, nome, cognome)
VALUES ('mario@example.com', 'mario_r', '$2b$10$...hash...', 'Mario', 'Rossi');

-- Inserimento multiplo
INSERT INTO prodotti (nome, prezzo, categoria, quantita_magazzino) VALUES
  ('Mouse wireless', 29.99, 'accessori', 150),
  ('Tastiera meccanica', 89.99, 'accessori', 75),
  ('Monitor 27"', 349.99, 'elettronica', 30);

-- Inserimento con gestione conflitti (UPSERT)
INSERT INTO utenti (email, username, password_hash)
VALUES ('mario@example.com', 'mario_r', '$2b$10$...hash...')
ON CONFLICT (email)
DO UPDATE SET aggiornato_il = CURRENT_TIMESTAMP;

-- Inserimento da SELECT
INSERT INTO archivio_ordini (ordine_id, utente_id, totale, stato)
SELECT id, utente_id, totale, stato
FROM ordini
WHERE stato = 'completato' AND creato_il < '2025-01-01';
```

#### UPDATE

```sql
-- Aggiornamento semplice
UPDATE utenti
SET ruolo = 'admin', aggiornato_il = CURRENT_TIMESTAMP
WHERE email = 'mario@example.com';

-- Aggiornamento con subquery
UPDATE prodotti
SET prezzo = prezzo * 0.90
WHERE categoria IN (
  SELECT categoria FROM categorie WHERE in_offerta = TRUE
);

-- Aggiornamento con RETURNING (PostgreSQL)
UPDATE ordini
SET stato = 'spedito'
WHERE stato = 'confermato' AND creato_il < NOW() - INTERVAL '2 days'
RETURNING id, utente_id, totale;
```

#### DELETE

```sql
-- Cancellazione con condizione
DELETE FROM sessioni
WHERE scadenza < CURRENT_TIMESTAMP;

-- Cancellazione con JOIN (PostgreSQL)
DELETE FROM notifiche n
USING utenti u
WHERE n.utente_id = u.id AND u.attivo = FALSE;

-- Soft delete (preferibile nella maggior parte dei casi)
UPDATE utenti
SET attivo = FALSE, eliminato_il = CURRENT_TIMESTAMP
WHERE id = 42;
```

### JOIN

Le JOIN sono il meccanismo fondamentale per combinare dati da tabelle diverse. La comprensione dei diversi tipi di JOIN e essenziale per scrivere query efficaci.

```sql
-- INNER JOIN — solo le righe con corrispondenza in entrambe le tabelle
SELECT u.nome, u.cognome, o.id AS ordine_id, o.totale
FROM utenti u
INNER JOIN ordini o ON u.id = o.utente_id
WHERE o.stato = 'completato';

-- LEFT JOIN — tutte le righe della tabella sinistra, con o senza corrispondenza
SELECT u.nome, u.cognome, COUNT(o.id) AS numero_ordini
FROM utenti u
LEFT JOIN ordini o ON u.id = o.utente_id
GROUP BY u.id, u.nome, u.cognome;

-- RIGHT JOIN — tutte le righe della tabella destra
SELECT p.nome AS prodotto, c.nome AS categoria
FROM prodotti p
RIGHT JOIN categorie c ON p.categoria_id = c.id;

-- FULL OUTER JOIN — tutte le righe di entrambe le tabelle
SELECT u.email, p.nome AS piano
FROM utenti u
FULL OUTER JOIN piani_abbonamento p ON u.piano_id = p.id;

-- CROSS JOIN — prodotto cartesiano
SELECT t.taglia, c.colore
FROM taglie t
CROSS JOIN colori c;

-- Self JOIN — una tabella unita a se stessa
SELECT
  e.nome AS dipendente,
  m.nome AS manager
FROM dipendenti e
LEFT JOIN dipendenti m ON e.manager_id = m.id;

-- JOIN multipli
SELECT
  o.id AS ordine,
  u.nome || ' ' || u.cognome AS cliente,
  p.nome AS prodotto,
  op.quantita,
  op.prezzo AS prezzo_unitario,
  (op.quantita * op.prezzo) AS subtotale
FROM ordini o
JOIN utenti u ON o.utente_id = u.id
JOIN ordini_prodotti op ON o.id = op.ordine_id
JOIN prodotti p ON op.prodotto_id = p.id
WHERE o.creato_il >= '2025-01-01'
ORDER BY o.id, p.nome;
```

### Subquery

Le subquery (o query annidate) sono query incorporate all'interno di altre query. Possono comparire nella clausola WHERE, nella clausola FROM (come tabelle derivate) o nella clausola SELECT.

```sql
-- Subquery nella clausola WHERE
SELECT nome, cognome, email
FROM utenti
WHERE id IN (
  SELECT DISTINCT utente_id
  FROM ordini
  WHERE totale > 100 AND creato_il >= '2025-01-01'
);

-- Subquery correlata
SELECT p.nome, p.prezzo
FROM prodotti p
WHERE p.prezzo > (
  SELECT AVG(p2.prezzo)
  FROM prodotti p2
  WHERE p2.categoria = p.categoria
);

-- Subquery nella clausola FROM (tabella derivata)
SELECT categoria, prezzo_medio
FROM (
  SELECT categoria, AVG(prezzo) AS prezzo_medio
  FROM prodotti
  GROUP BY categoria
) AS stats
WHERE prezzo_medio > 50;

-- CTE (Common Table Expression) — alternativa piu leggibile alle subquery
WITH ordini_recenti AS (
  SELECT utente_id, COUNT(*) AS num_ordini, SUM(totale) AS spesa_totale
  FROM ordini
  WHERE creato_il >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY utente_id
),
clienti_top AS (
  SELECT utente_id, num_ordini, spesa_totale
  FROM ordini_recenti
  WHERE spesa_totale > 500
)
SELECT u.nome, u.cognome, u.email, ct.num_ordini, ct.spesa_totale
FROM clienti_top ct
JOIN utenti u ON ct.utente_id = u.id
ORDER BY ct.spesa_totale DESC;
```

### Indici

Gli indici sono strutture dati ausiliarie che accelerano le operazioni di ricerca nel database, analogamente all'indice analitico di un libro. Senza indici, il database deve eseguire una scansione sequenziale dell'intera tabella (full table scan) per ogni query.

```sql
-- Indice B-tree (predefinito, adatto per =, <, >, BETWEEN, ORDER BY)
CREATE INDEX idx_prodotti_categoria ON prodotti(categoria);

-- Indice unico
CREATE UNIQUE INDEX idx_utenti_email ON utenti(email);

-- Indice composto (l'ordine delle colonne conta!)
CREATE INDEX idx_ordini_stato_data ON ordini(stato, creato_il DESC);

-- Indice parziale (solo su un sottoinsieme di righe)
CREATE INDEX idx_ordini_in_attesa ON ordini(creato_il)
WHERE stato = 'in_attesa';

-- Indice GIN per ricerche full-text e JSONB (PostgreSQL)
CREATE INDEX idx_prodotti_tag ON prodotti USING GIN(tag);

-- Indice GiST per dati geometrici e range
CREATE INDEX idx_eventi_periodo ON eventi USING GIST(periodo);
```

### Transazioni e ACID

Le transazioni garantiscono che un gruppo di operazioni venga eseguito come un'unita atomica. Le proprieta ACID definiscono le garanzie fornite da un sistema transazionale:

- **Atomicity** (Atomicita): tutte le operazioni nella transazione vengono completate, oppure nessuna. Non esistono stati intermedi.
- **Consistency** (Coerenza): una transazione porta il database da uno stato valido a un altro stato valido, rispettando tutti i vincoli definiti.
- **Isolation** (Isolamento): le transazioni concorrenti non interferiscono tra loro. Ogni transazione vede il database come se fosse l'unica in esecuzione.
- **Durability** (Durabilita): una volta confermata (commit), una transazione e permanente anche in caso di crash del sistema.

```sql
-- Transazione per un trasferimento di fondi
BEGIN;

UPDATE conti SET saldo = saldo - 100.00
WHERE id = 1 AND saldo >= 100.00;

-- Verifica che l'operazione sia riuscita
-- (in una stored procedure si controllerebbe il numero di righe modificate)

UPDATE conti SET saldo = saldo + 100.00
WHERE id = 2;

INSERT INTO movimenti (conto_da, conto_a, importo, tipo)
VALUES (1, 2, 100.00, 'trasferimento');

COMMIT;

-- In caso di errore:
-- ROLLBACK;

-- Savepoint per rollback parziale
BEGIN;
INSERT INTO ordini (utente_id, totale) VALUES (1, 150.00);
SAVEPOINT dopo_ordine;

INSERT INTO pagamenti (ordine_id, metodo) VALUES (currval('ordini_id_seq'), 'carta');
-- Se il pagamento fallisce:
-- ROLLBACK TO dopo_ordine;
-- Si puo tentare un metodo alternativo

COMMIT;
```

### View

Le view sono query salvate che funzionano come tabelle virtuali. Semplificano query complesse, forniscono un livello di astrazione e possono limitare l'accesso ai dati.

```sql
-- View semplice
CREATE VIEW vista_ordini_completi AS
SELECT
  o.id AS ordine_id,
  u.nome || ' ' || u.cognome AS cliente,
  u.email,
  o.totale,
  o.stato,
  o.creato_il,
  COUNT(op.prodotto_id) AS num_articoli
FROM ordini o
JOIN utenti u ON o.utente_id = u.id
JOIN ordini_prodotti op ON o.id = op.ordine_id
GROUP BY o.id, u.nome, u.cognome, u.email;

-- Utilizzo della view
SELECT * FROM vista_ordini_completi
WHERE stato = 'completato' AND creato_il >= '2025-06-01';

-- Materialized view (PostgreSQL) — i risultati vengono memorizzati fisicamente
CREATE MATERIALIZED VIEW stats_vendite_mensili AS
SELECT
  DATE_TRUNC('month', o.creato_il) AS mese,
  COUNT(DISTINCT o.id) AS ordini,
  SUM(o.totale) AS ricavo_totale,
  AVG(o.totale)::NUMERIC(10,2) AS ordine_medio
FROM ordini o
WHERE o.stato = 'completato'
GROUP BY DATE_TRUNC('month', o.creato_il);

-- Aggiornamento della materialized view
REFRESH MATERIALIZED VIEW CONCURRENTLY stats_vendite_mensili;
```

### Stored Procedure e Function

Le stored procedure e le function incapsulano logica business direttamente nel database. Le function restituiscono un valore, le procedure eseguono operazioni senza restituire risultati direttamente.

```sql
-- Function che calcola il totale di un ordine
CREATE OR REPLACE FUNCTION calcola_totale_ordine(p_ordine_id INTEGER)
RETURNS DECIMAL(10,2) AS $$
DECLARE
  v_totale DECIMAL(10,2);
BEGIN
  SELECT SUM(quantita * prezzo) INTO v_totale
  FROM ordini_prodotti
  WHERE ordine_id = p_ordine_id;

  RETURN COALESCE(v_totale, 0);
END;
$$ LANGUAGE plpgsql;

-- Utilizzo
SELECT calcola_totale_ordine(42);

-- Stored procedure per processare un ordine
CREATE OR REPLACE PROCEDURE processa_ordine(p_ordine_id INTEGER)
LANGUAGE plpgsql AS $$
DECLARE
  v_prodotto RECORD;
BEGIN
  FOR v_prodotto IN
    SELECT prodotto_id, quantita FROM ordini_prodotti WHERE ordine_id = p_ordine_id
  LOOP
    UPDATE prodotti
    SET quantita_magazzino = quantita_magazzino - v_prodotto.quantita
    WHERE id = v_prodotto.prodotto_id
      AND quantita_magazzino >= v_prodotto.quantita;

    IF NOT FOUND THEN
      RAISE EXCEPTION 'Stock insufficiente per prodotto %', v_prodotto.prodotto_id;
    END IF;
  END LOOP;

  UPDATE ordini SET stato = 'confermato' WHERE id = p_ordine_id;
END;
$$;

-- Invocazione della procedura
CALL processa_ordine(42);
```

---

## PostgreSQL

PostgreSQL e il database relazionale open source piu avanzato al mondo. Sviluppato attivamente dalla comunita da oltre 35 anni, combina la robustezza dei database enterprise con l'innovazione continua. E la scelta predefinita per la maggior parte delle applicazioni web moderne, da startup a grandi aziende. Supporta pienamente lo standard SQL, offre estensibilita senza pari e include funzionalita che in altri database richiederebbero licenze costose.

### Caratteristiche Principali

PostgreSQL si distingue per una serie di funzionalita che lo rendono unico nel panorama dei database relazionali:

- **MVCC** (Multi-Version Concurrency Control): gestisce la concorrenza senza lock in lettura, permettendo a lettori e scrittori di non bloccarsi reciprocamente.
- **Tipi di dato avanzati**: oltre ai tipi standard, supporta UUID, JSONB, array, hstore, range, tipi geometrici, network address, e consente la creazione di tipi personalizzati.
- **Full ACID compliance**: transazioni completamente conformi con livelli di isolamento configurabili (Read Committed, Repeatable Read, Serializable).
- **Partitioning nativo**: partizionamento dichiarativo per tabelle di grandi dimensioni (range, list, hash).
- **Replicazione**: streaming replication sincrona e asincrona, logical replication per scenari avanzati.
- **Estensibilita**: sistema di estensioni che permette di aggiungere tipi di dato, funzioni, operatori, linguaggi procedurali e metodi di indicizzazione.

### Tipi di Dato

```sql
-- Tipi numerici
id          SERIAL                -- intero auto-incrementante (legacy, preferire GENERATED)
id          INTEGER GENERATED ALWAYS AS IDENTITY  -- standard SQL
prezzo      DECIMAL(10, 2)        -- precisione esatta per valori monetari
peso        REAL                  -- virgola mobile 4 byte
coordinate  DOUBLE PRECISION      -- virgola mobile 8 byte

-- Tipi testuali
nome        VARCHAR(100)          -- lunghezza variabile con limite
bio         TEXT                  -- lunghezza variabile senza limite
codice      CHAR(10)              -- lunghezza fissa

-- Tipi temporali
creato_il   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
data_nascita DATE
durata       INTERVAL

-- Tipi booleani
attivo       BOOLEAN DEFAULT TRUE

-- UUID
id           UUID DEFAULT gen_random_uuid()

-- Array
tag          TEXT[]                -- array di stringhe
punteggi     INTEGER[]

-- Tipi speciali
metadata     JSONB                 -- JSON binario con indicizzazione
indirizzo_ip INET                  -- indirizzo IPv4/IPv6
mac          MACADDR
coordinate   POINT                 -- tipo geometrico
```

### JSON e JSONB

PostgreSQL offre supporto nativo per JSON, con due tipi distinti: `JSON` (memorizzato come testo) e `JSONB` (memorizzato in formato binario decomposto). JSONB e quasi sempre preferibile perche supporta l'indicizzazione e operazioni efficienti.

```sql
-- Creazione tabella con JSONB
CREATE TABLE prodotti (
  id       SERIAL PRIMARY KEY,
  nome     VARCHAR(200) NOT NULL,
  attributi JSONB DEFAULT '{}'::JSONB
);

-- Inserimento con dati JSONB
INSERT INTO prodotti (nome, attributi) VALUES
('Laptop Pro', '{
  "marca": "TechBrand",
  "ram": 16,
  "storage": "512GB SSD",
  "display": {"pollici": 15.6, "risoluzione": "1920x1080"},
  "porte": ["USB-C", "HDMI", "USB-A"],
  "colori_disponibili": ["argento", "grigio"]
}');

-- Query su campi JSONB
SELECT nome, attributi->>'marca' AS marca, attributi->'display'->>'pollici' AS display
FROM prodotti
WHERE attributi->>'marca' = 'TechBrand';

-- Filtrare per valori annidati
SELECT nome FROM prodotti
WHERE (attributi->'ram')::INTEGER >= 16;

-- Operatore di contenimento (@>)
SELECT nome FROM prodotti
WHERE attributi @> '{"marca": "TechBrand"}';

-- Verificare esistenza di una chiave
SELECT nome FROM prodotti
WHERE attributi ? 'porte';

-- Aggiornare un campo JSONB
UPDATE prodotti
SET attributi = jsonb_set(attributi, '{ram}', '32')
WHERE nome = 'Laptop Pro';

-- Indice GIN su JSONB per ricerche efficienti
CREATE INDEX idx_prodotti_attributi ON prodotti USING GIN(attributi);
```

### Full-Text Search

PostgreSQL include un motore di ricerca full-text integrato che per molti casi d'uso elimina la necessita di strumenti esterni come Elasticsearch.

```sql
-- Configurazione base per la ricerca full-text
ALTER TABLE articoli ADD COLUMN search_vector TSVECTOR;

UPDATE articoli SET search_vector =
  setweight(to_tsvector('italian', COALESCE(titolo, '')), 'A') ||
  setweight(to_tsvector('italian', COALESCE(contenuto, '')), 'B');

-- Indice GIN per ricerche veloci
CREATE INDEX idx_articoli_search ON articoli USING GIN(search_vector);

-- Trigger per aggiornamento automatico
CREATE OR REPLACE FUNCTION aggiorna_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('italian', COALESCE(NEW.titolo, '')), 'A') ||
    setweight(to_tsvector('italian', COALESCE(NEW.contenuto, '')), 'B');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_articoli_search
  BEFORE INSERT OR UPDATE ON articoli
  FOR EACH ROW EXECUTE FUNCTION aggiorna_search_vector();

-- Ricerca con ranking
SELECT
  titolo,
  ts_rank(search_vector, query) AS rilevanza,
  ts_headline('italian', contenuto, query, 'StartSel=<b>, StopSel=</b>, MaxFragments=3') AS estratto
FROM articoli, plainto_tsquery('italian', 'sviluppo web moderno') AS query
WHERE search_vector @@ query
ORDER BY rilevanza DESC
LIMIT 10;
```

### Estensioni

Le estensioni ampliano le capacita di PostgreSQL in modo modulare. Alcune tra le piu utilizzate nello sviluppo web:

```sql
-- pgcrypto — funzioni crittografiche
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SELECT crypt('password123', gen_salt('bf', 10));

-- uuid-ossp — generazione UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SELECT uuid_generate_v4();

-- pg_trgm — ricerca fuzzy basata su trigrammi
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_prodotti_nome_trgm ON prodotti USING GIN(nome gin_trgm_ops);
SELECT nome FROM prodotti WHERE nome % 'tasteira';  -- trova "tastiera" anche con typo

-- PostGIS — dati geospaziali
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT nome FROM negozi
WHERE ST_DWithin(posizione, ST_MakePoint(12.4964, 41.9028)::geography, 5000);
```

### Backup e Restore

```bash
# Dump logico di un database completo
pg_dump -h localhost -U postgres -d ecommerce -F custom -f ecommerce_backup.dump

# Dump solo dello schema (senza dati)
pg_dump -h localhost -U postgres -d ecommerce --schema-only -f schema.sql

# Dump di tabelle specifiche
pg_dump -h localhost -U postgres -d ecommerce -t utenti -t ordini -F custom -f utenti_ordini.dump

# Restore da dump custom
pg_restore -h localhost -U postgres -d ecommerce_nuovo -F custom ecommerce_backup.dump

# Restore con pulizia preventiva
pg_restore --clean --if-exists -d ecommerce ecommerce_backup.dump

# Dump in formato SQL leggibile
pg_dump -h localhost -U postgres -d ecommerce --inserts -f ecommerce.sql
```

---

## MySQL e MariaDB

MySQL e il database relazionale open source piu diffuso al mondo, parte integrante dello stack LAMP (Linux, Apache, MySQL, PHP) che ha dominato lo sviluppo web per oltre un decennio. MariaDB e un fork di MySQL creato dal fondatore originale Monty Widenius dopo l'acquisizione di MySQL da parte di Oracle, con l'obiettivo di mantenere il progetto completamente open source e accelerare l'innovazione.

### Panoramica MySQL

MySQL si distingue per la semplicita di configurazione, le buone prestazioni in lettura e un ecosistema vastissimo. E il database predefinito di WordPress, Drupal, Joomla e innumerevoli applicazioni PHP. Supporta diversi motori di storage, il piu importante dei quali e **InnoDB** (predefinito dalla versione 5.5), che fornisce transazioni ACID, chiavi esterne e row-level locking.

### Differenze Principali tra PostgreSQL e MySQL

| Aspetto | PostgreSQL | MySQL (InnoDB) |
|---------|------------|----------------|
| Standard SQL | Aderenza molto elevata | Aderenza buona con eccezioni |
| JSONB nativo | Si, con indicizzazione GIN | JSON con indici generati |
| Full-text search | Integrato con ranking e pesi | Integrato, meno flessibile |
| Tipi di dato | Estremamente ricchi (array, range, composite) | Piu limitati |
| Replicazione | Streaming + logica | Binlog-based |
| Estensioni | Sistema estensioni modulare | Plugin con API diverse |
| Stored procedure | PL/pgSQL potente | SQL/PSM piu limitato |
| CTE ricorsive | Pieno supporto | Supporto dalla 8.0 |
| UPSERT | ON CONFLICT (flessibile) | ON DUPLICATE KEY UPDATE |
| Licenza | PostgreSQL License (permissiva) | GPL v2 (Oracle) |
| Prestazioni | Eccelle in query complesse | Eccelle in read-heavy semplici |
| Partizionamento | Dichiarativo (range, list, hash) | Range, list, hash, key |

### MariaDB vs MySQL

MariaDB mantiene la compatibilita binaria con MySQL per la maggior parte dei casi d'uso, ma introduce miglioramenti significativi. Offre il motore di storage **Aria** come alternativa a MyISAM, **ColumnStore** per analytics, ottimizzazioni del query optimizer, pool di thread nativi e funzionalita JSON migliorate. Per nuovi progetti che tradizionalmente avrebbero scelto MySQL, MariaDB e spesso l'alternativa consigliata grazie alla governance comunitaria e al ritmo di innovazione piu rapido.

---

## MongoDB

MongoDB e il database NoSQL document-oriented piu popolare. Memorizza i dati come **documenti** in formato BSON (Binary JSON), raggruppati in **collezioni** (l'analogo delle tabelle SQL). Ogni documento e un oggetto con struttura flessibile: documenti diversi nella stessa collezione possono avere campi differenti. Questa flessibilita e il punto di forza principale di MongoDB, ma anche la fonte dei suoi rischi: senza disciplina nella modellazione, i dati possono diventare incoerenti rapidamente.

### Documenti e Collezioni

Un documento MongoDB e sostanzialmente un oggetto JSON arricchito con tipi BSON aggiuntivi (ObjectId, Date, Binary, Decimal128). Ogni documento ha un campo `_id` univoco generato automaticamente se non specificato.

```javascript
// Documento esempio: un prodotto nel catalogo
{
  _id: ObjectId("64a7f8b2e4b0d1a2c3456789"),
  nome: "Laptop Pro 15",
  marca: "TechBrand",
  prezzo: 1299.99,
  specifiche: {
    ram: 16,
    storage: "512GB SSD",
    processore: "Intel i7-13700H",
    display: { pollici: 15.6, risoluzione: "2560x1440" }
  },
  tag: ["laptop", "gaming", "professionale"],
  recensioni: [
    { utente: "mario_r", voto: 5, commento: "Eccellente!", data: ISODate("2025-06-15") },
    { utente: "lucia_b", voto: 4, commento: "Buon rapporto qualità/prezzo", data: ISODate("2025-06-20") }
  ],
  disponibile: true,
  creato_il: ISODate("2025-01-10T10:30:00Z")
}
```

### Operazioni CRUD

```javascript
// CREATE — Inserimento
db.prodotti.insertOne({
  nome: "Mouse Ergonomico",
  marca: "ComfortTech",
  prezzo: 49.99,
  tag: ["accessori", "ergonomia"],
  disponibile: true
});

db.prodotti.insertMany([
  { nome: "Webcam HD", marca: "VisioTech", prezzo: 79.99 },
  { nome: "Microfono USB", marca: "AudioPro", prezzo: 129.99 }
]);

// READ — Lettura
// Trova tutti i prodotti della marca TechBrand
db.prodotti.find({ marca: "TechBrand" });

// Query con operatori di confronto
db.prodotti.find({
  prezzo: { $gte: 50, $lte: 200 },
  disponibile: true
}).sort({ prezzo: 1 }).limit(10);

// Query su campi annidati
db.prodotti.find({ "specifiche.ram": { $gte: 16 } });

// Query su array
db.prodotti.find({ tag: { $in: ["gaming", "professionale"] } });

// Proiezione (selezionare solo alcuni campi)
db.prodotti.find(
  { marca: "TechBrand" },
  { nome: 1, prezzo: 1, _id: 0 }
);

// UPDATE — Aggiornamento
db.prodotti.updateOne(
  { nome: "Mouse Ergonomico" },
  {
    $set: { prezzo: 44.99 },
    $addToSet: { tag: "offerta" },
    $currentDate: { aggiornato_il: true }
  }
);

db.prodotti.updateMany(
  { marca: "TechBrand" },
  { $mul: { prezzo: 0.9 } }  // sconto 10%
);

// DELETE — Cancellazione
db.prodotti.deleteOne({ _id: ObjectId("64a7f8b2e4b0d1a2c3456789") });
db.prodotti.deleteMany({ disponibile: false, aggiornato_il: { $lt: ISODate("2024-01-01") } });
```

### Aggregation Pipeline

L'aggregation pipeline e il framework di MongoDB per trasformazioni ed analisi complesse dei dati. Ogni stage della pipeline trasforma i documenti e passa il risultato allo stage successivo.

```javascript
// Pipeline: vendite mensili per categoria con statistiche
db.ordini.aggregate([
  // Stage 1: filtra ordini completati dell'ultimo anno
  { $match: {
    stato: "completato",
    data: { $gte: ISODate("2025-01-01") }
  }},

  // Stage 2: scomponi l'array dei prodotti
  { $unwind: "$articoli" },

  // Stage 3: lookup per ottenere dettagli del prodotto
  { $lookup: {
    from: "prodotti",
    localField: "articoli.prodotto_id",
    foreignField: "_id",
    as: "prodotto"
  }},

  // Stage 4: appiattisci il risultato del lookup
  { $unwind: "$prodotto" },

  // Stage 5: raggruppa per mese e categoria
  { $group: {
    _id: {
      mese: { $dateToString: { format: "%Y-%m", date: "$data" } },
      categoria: "$prodotto.categoria"
    },
    ricavo: { $sum: { $multiply: ["$articoli.quantita", "$articoli.prezzo"] } },
    ordini: { $sum: 1 },
    pezzi_venduti: { $sum: "$articoli.quantita" }
  }},

  // Stage 6: ordina per mese e ricavo
  { $sort: { "_id.mese": -1, ricavo: -1 } },

  // Stage 7: formatta l'output
  { $project: {
    _id: 0,
    mese: "$_id.mese",
    categoria: "$_id.categoria",
    ricavo: { $round: ["$ricavo", 2] },
    ordini: 1,
    pezzi_venduti: 1
  }}
]);
```

### Indicizzazione in MongoDB

```javascript
// Indice singolo
db.prodotti.createIndex({ nome: 1 });

// Indice composto
db.ordini.createIndex({ utente_id: 1, data: -1 });

// Indice unico
db.utenti.createIndex({ email: 1 }, { unique: true });

// Indice testuale per ricerche full-text
db.articoli.createIndex({ titolo: "text", contenuto: "text" });
db.articoli.find({ $text: { $search: "sviluppo web moderno" } });

// Indice TTL per scadenza automatica dei documenti
db.sessioni.createIndex({ creato_il: 1 }, { expireAfterSeconds: 3600 });

// Indice parziale
db.ordini.createIndex(
  { data_spedizione: 1 },
  { partialFilterExpression: { stato: "spedito" } }
);
```

### MongoDB Atlas

MongoDB Atlas e la piattaforma cloud-managed ufficiale per MongoDB. Elimina la complessita operativa della gestione di un cluster MongoDB, offrendo deploy automatizzato su AWS, Google Cloud e Azure, scaling automatico, backup continui, monitoring integrato, global cluster per distribuzione geografica e Atlas Search (basato su Lucene) per ricerche full-text avanzate. Per la maggior parte dei progetti, Atlas e la soluzione consigliata rispetto a un'installazione self-managed, specialmente per team che non dispongono di competenze DBA dedicate.

---

## Redis

Redis (Remote Dictionary Server) e un data store in-memory che opera come database, cache e message broker. La sua caratteristica distintiva e la velocita: operando interamente in memoria, Redis raggiunge latenze inferiori al millisecondo per la maggior parte delle operazioni. Questo lo rende lo strumento ideale per tutti gli scenari dove le prestazioni sono critiche: caching, sessioni utente, rate limiting, classifiche in tempo reale, code di messaggi e molto altro.

### Strutture Dati

Redis non e un semplice key-value store. Supporta strutture dati ricche che permettono operazioni atomiche complesse direttamente sul server, riducendo il carico di lavoro dell'applicazione.

#### String

Il tipo piu semplice. Ogni chiave mappa a un valore stringa, che puo contenere testo, numeri o dati binari fino a 512 MB.

```redis
SET utente:42:nome "Mario Rossi"
GET utente:42:nome                    -- "Mario Rossi"

-- Operazioni numeriche atomiche
SET contatore:visite 0
INCR contatore:visite                 -- 1
INCRBY contatore:visite 10           -- 11

-- Impostare con scadenza
SET sessione:abc123 "{\"utente_id\": 42}" EX 3600   -- scade in 1 ora
SETEX token:reset:xyz "utente42" 900                  -- scade in 15 minuti

-- SET condizionale
SET lock:risorsa42 "worker1" NX EX 30  -- NX = solo se non esiste (distributed lock)
```

#### Hash

Gli hash sono mappe di campi-valore, ideali per rappresentare oggetti. Piu efficienti in memoria rispetto a chiavi separate per ogni campo.

```redis
HSET utente:42 nome "Mario" cognome "Rossi" email "mario@example.com" ruolo "admin"
HGET utente:42 email                  -- "mario@example.com"
HGETALL utente:42                     -- restituisce tutti i campi
HMGET utente:42 nome email            -- restituisce piu campi
HINCRBY utente:42 login_count 1       -- incremento atomico di un campo
HDEL utente:42 ruolo                  -- rimuove un campo
HEXISTS utente:42 email               -- verifica esistenza campo
```

#### List

Le liste sono sequenze ordinate di stringhe, implementate come linked list. Supportano operazioni push/pop da entrambe le estremita, rendendole ideali per code e stack.

```redis
-- Coda di lavoro (FIFO)
LPUSH coda:email "job:invio_benvenuto:42"
LPUSH coda:email "job:invio_fattura:99"
RPOP coda:email                       -- "job:invio_benvenuto:42" (primo inserito)

-- Coda bloccante (il consumer attende se la coda e vuota)
BRPOP coda:email 30                   -- attende fino a 30 secondi

-- Ultimi N elementi (es. attivita recenti)
LPUSH attivita:utente:42 "Login effettuato"
LTRIM attivita:utente:42 0 99        -- mantiene solo le ultime 100 attivita
LRANGE attivita:utente:42 0 9        -- ultimi 10 eventi
```

#### Set

I set sono collezioni non ordinate di stringhe univoche. Supportano operazioni insiemistiche come unione, intersezione e differenza.

```redis
-- Tag di un articolo
SADD articolo:1:tag "javascript" "nodejs" "backend"
SADD articolo:2:tag "javascript" "react" "frontend"

-- Operazioni insiemistiche
SINTER articolo:1:tag articolo:2:tag     -- {"javascript"} (intersezione)
SUNION articolo:1:tag articolo:2:tag     -- tutti i tag unici
SDIFF articolo:1:tag articolo:2:tag      -- {"nodejs", "backend"} (in 1 ma non in 2)

SISMEMBER articolo:1:tag "nodejs"        -- 1 (vero)
SCARD articolo:1:tag                     -- 3 (cardinalita)
```

#### Sorted Set

I sorted set combinano le proprieta dei set (unicita) con un punteggio numerico associato a ogni membro, mantenendo l'ordinamento automatico. Struttura ideale per classifiche e leaderboard.

```redis
-- Classifica giocatori
ZADD classifica 1500 "mario" 2300 "lucia" 1800 "paolo" 2100 "anna"

-- Top 3 giocatori (punteggio piu alto)
ZREVRANGE classifica 0 2 WITHSCORES
-- 1) "lucia" 2) "2300" 3) "anna" 4) "2100" 5) "paolo" 6) "1800"

-- Posizione di un giocatore (0-based, dal piu alto)
ZREVRANK classifica "paolo"            -- 2 (terza posizione)

-- Incremento punteggio atomico
ZINCRBY classifica 500 "mario"         -- 2000

-- Range per punteggio
ZRANGEBYSCORE classifica 1500 2000 WITHSCORES
```

### Pattern di Caching

Il caching e il caso d'uso piu comune di Redis nello sviluppo web. Il pattern fondamentale e il **cache-aside** (o lazy loading):

```javascript
// Cache-aside pattern in Node.js
async function getUtente(id) {
  const cacheKey = `utente:${id}`;

  // 1. Prova a leggere dalla cache
  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);  // cache hit
  }

  // 2. Cache miss: leggi dal database
  const utente = await db.query('SELECT * FROM utenti WHERE id = $1', [id]);

  // 3. Salva in cache con TTL
  await redis.setex(cacheKey, 3600, JSON.stringify(utente));

  return utente;
}

// Invalidazione della cache dopo un aggiornamento
async function aggiornaUtente(id, dati) {
  await db.query('UPDATE utenti SET nome = $1 WHERE id = $2', [dati.nome, id]);
  await redis.del(`utente:${id}`);  // invalida la cache
}
```

Altri pattern di caching includono il **write-through** (scrivi in cache e database simultaneamente), il **write-behind** (scrivi prima in cache, poi in database in modo asincrono) e il **read-through** (la cache stessa si occupa di leggere dal database in caso di miss).

### Pub/Sub

Il sistema Publish/Subscribe di Redis permette la comunicazione asincrona tra componenti disaccoppiati. Un publisher invia messaggi a un canale senza sapere chi li ricevera; i subscriber si iscrivono ai canali di interesse.

```javascript
// Publisher
await redis.publish('notifiche:ordini', JSON.stringify({
  tipo: 'nuovo_ordine',
  ordine_id: 42,
  utente_id: 7,
  totale: 149.99
}));

// Subscriber
const subscriber = redis.duplicate();
await subscriber.subscribe('notifiche:ordini', (messaggio) => {
  const dati = JSON.parse(messaggio);
  console.log(`Nuovo ordine #${dati.ordine_id}: €${dati.totale}`);
  // Invia email, aggiorna dashboard, ecc.
});

// Pattern matching per canali multipli
await subscriber.pSubscribe('notifiche:*', (messaggio, canale) => {
  console.log(`Messaggio su ${canale}: ${messaggio}`);
});
```

### TTL e Scadenza

Il Time-To-Live (TTL) e un meccanismo fondamentale per la gestione automatica della memoria. Redis elimina automaticamente le chiavi scadute, garantendo che la cache non cresca indefinitamente.

```redis
SET sessione:abc "dati_sessione" EX 1800    -- scade in 30 minuti
TTL sessione:abc                             -- secondi rimanenti
PERSIST sessione:abc                         -- rimuove la scadenza
EXPIRE sessione:abc 3600                     -- imposta nuova scadenza
EXPIREAT sessione:abc 1735689600             -- scadenza a timestamp specifico
```

### Persistenza

Nonostante sia un database in-memory, Redis offre due meccanismi di persistenza per garantire la durabilita dei dati:

- **RDB** (Redis Database Backup): snapshot periodici dell'intero dataset. Compatto ed efficiente per il backup, ma si rischia di perdere i dati tra uno snapshot e l'altro.
- **AOF** (Append Only File): registra ogni operazione di scrittura in un log. Maggiore durabilita (configurabile fino a fsync ad ogni operazione), ma file piu grandi e recovery piu lento.

La configurazione tipica per la produzione utilizza entrambi i meccanismi: AOF per la durabilita e RDB per backup veloci e riavvii rapidi.

---

## ORM e Query Builder

Gli ORM (Object-Relational Mapping) e i query builder semplificano l'interazione tra il codice applicativo e il database, astraendo le differenze tra il paradigma a oggetti del codice e il paradigma relazionale del database. Un ORM mappa le tabelle a classi e le righe a istanze di oggetti. Un query builder fornisce un'API fluente per costruire query SQL programmaticamente senza scrivere SQL grezzo.

### Prisma

Prisma e l'ORM di nuova generazione per Node.js e TypeScript. A differenza degli ORM tradizionali che mappano classi a tabelle, Prisma adotta un approccio dichiarativo basato su uno schema centrale da cui genera un client type-safe, le migrazioni e le query.

#### Schema Prisma

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Utente {
  id          Int       @id @default(autoincrement())
  email       String    @unique
  username    String    @unique
  passwordHash String  @map("password_hash")
  nome        String?
  cognome     String?
  ruolo       Ruolo     @default(UTENTE)
  attivo      Boolean   @default(true)
  creatoIl    DateTime  @default(now()) @map("creato_il")
  aggiornatoIl DateTime @updatedAt @map("aggiornato_il")

  ordini      Ordine[]
  profilo     Profilo?
  recensioni  Recensione[]

  @@map("utenti")
}

model Profilo {
  id        Int     @id @default(autoincrement())
  bio       String?
  avatar    String?
  utenteId  Int     @unique @map("utente_id")
  utente    Utente  @relation(fields: [utenteId], references: [id], onDelete: Cascade)

  @@map("profili")
}

model Ordine {
  id        Int      @id @default(autoincrement())
  totale    Decimal  @db.Decimal(10, 2)
  stato     StatoOrdine @default(IN_ATTESA)
  creatoIl  DateTime @default(now()) @map("creato_il")
  utenteId  Int      @map("utente_id")
  utente    Utente   @relation(fields: [utenteId], references: [id], onDelete: Cascade)

  articoli  OrdineArticolo[]

  @@index([utenteId, creatoIl])
  @@map("ordini")
}

model Prodotto {
  id          Int      @id @default(autoincrement())
  nome        String
  prezzo      Decimal  @db.Decimal(10, 2)
  categoria   String
  disponibile Boolean  @default(true)

  ordini      OrdineArticolo[]
  recensioni  Recensione[]

  @@map("prodotti")
}

model OrdineArticolo {
  ordineId   Int     @map("ordine_id")
  prodottoId Int     @map("prodotto_id")
  quantita   Int
  prezzo     Decimal @db.Decimal(10, 2)

  ordine     Ordine   @relation(fields: [ordineId], references: [id], onDelete: Cascade)
  prodotto   Prodotto @relation(fields: [prodottoId], references: [id])

  @@id([ordineId, prodottoId])
  @@map("ordini_articoli")
}

model Recensione {
  id         Int      @id @default(autoincrement())
  voto       Int
  commento   String?
  creatoIl   DateTime @default(now()) @map("creato_il")
  utenteId   Int      @map("utente_id")
  prodottoId Int      @map("prodotto_id")

  utente     Utente   @relation(fields: [utenteId], references: [id])
  prodotto   Prodotto @relation(fields: [prodottoId], references: [id])

  @@unique([utenteId, prodottoId])
  @@map("recensioni")
}

enum Ruolo {
  UTENTE
  ADMIN
  MODERATORE
}

enum StatoOrdine {
  IN_ATTESA
  CONFERMATO
  SPEDITO
  CONSEGNATO
  ANNULLATO
}
```

#### Prisma Migrate

```bash
# Creare una migrazione dopo aver modificato lo schema
npx prisma migrate dev --name aggiungi_tabella_recensioni

# Applicare migrazioni in produzione
npx prisma migrate deploy

# Resettare il database (SOLO sviluppo)
npx prisma migrate reset

# Generare il client dopo modifiche allo schema
npx prisma generate

# Visualizzare lo stato delle migrazioni
npx prisma migrate status

# Ispezionare il database esistente e generare lo schema
npx prisma db pull
```

#### Prisma Client — Query

```typescript
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// CREATE
const nuovoUtente = await prisma.utente.create({
  data: {
    email: 'mario@example.com',
    username: 'mario_r',
    passwordHash: '$2b$10$...hash...',
    nome: 'Mario',
    cognome: 'Rossi',
    profilo: {
      create: { bio: 'Sviluppatore web' }  // crea anche il profilo correlato
    }
  },
  include: { profilo: true }
});

// READ con filtri, relazioni e paginazione
const utenti = await prisma.utente.findMany({
  where: {
    attivo: true,
    ruolo: 'UTENTE',
    ordini: { some: { totale: { gte: 100 } } }
  },
  include: {
    profilo: true,
    ordini: {
      where: { stato: 'CONSEGNATO' },
      orderBy: { creatoIl: 'desc' },
      take: 5
    },
    _count: { select: { recensioni: true } }
  },
  orderBy: { creatoIl: 'desc' },
  skip: 20,
  take: 10
});

// UPDATE
const utenteAggiornato = await prisma.utente.update({
  where: { email: 'mario@example.com' },
  data: {
    ruolo: 'ADMIN',
    profilo: {
      update: { bio: 'Senior developer e team lead' }
    }
  }
});

// DELETE
await prisma.utente.delete({ where: { id: 42 } });

// Transazioni
const [ordine, _] = await prisma.$transaction([
  prisma.ordine.create({
    data: {
      utenteId: 1,
      totale: 149.99,
      articoli: {
        create: [
          { prodottoId: 5, quantita: 2, prezzo: 49.99 },
          { prodottoId: 8, quantita: 1, prezzo: 50.01 }
        ]
      }
    }
  }),
  prisma.prodotto.update({
    where: { id: 5 },
    data: { disponibile: false }
  })
]);

// Aggregazioni
const statistiche = await prisma.ordine.aggregate({
  _count: true,
  _sum: { totale: true },
  _avg: { totale: true },
  where: { stato: 'CONSEGNATO', creatoIl: { gte: new Date('2025-01-01') } }
});
```

### Sequelize

Sequelize e un ORM maturo per Node.js che supporta PostgreSQL, MySQL, MariaDB, SQLite e Microsoft SQL Server. Utilizza un approccio basato su modelli definiti nel codice.

```javascript
const { Sequelize, DataTypes, Op } = require('sequelize');
const sequelize = new Sequelize(process.env.DATABASE_URL);

// Definizione modello
const Utente = sequelize.define('Utente', {
  email: { type: DataTypes.STRING, allowNull: false, unique: true },
  nome: { type: DataTypes.STRING(100) },
  ruolo: { type: DataTypes.ENUM('utente', 'admin'), defaultValue: 'utente' }
}, { tableName: 'utenti', underscored: true });

const Ordine = sequelize.define('Ordine', {
  totale: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  stato: { type: DataTypes.STRING(20), defaultValue: 'in_attesa' }
}, { tableName: 'ordini', underscored: true });

// Associazioni
Utente.hasMany(Ordine, { foreignKey: 'utente_id' });
Ordine.belongsTo(Utente, { foreignKey: 'utente_id' });

// Query
const utentiConOrdini = await Utente.findAll({
  where: { ruolo: 'utente' },
  include: [{ model: Ordine, where: { stato: { [Op.ne]: 'annullato' } }, required: false }],
  order: [['createdAt', 'DESC']],
  limit: 20
});
```

### Knex.js

Knex.js e un query builder SQL per Node.js che offre un'interfaccia fluente per costruire query senza la complessita di un ORM completo. Supporta PostgreSQL, MySQL, SQLite, Oracle e MSSQL.

```javascript
const knex = require('knex')({
  client: 'pg',
  connection: process.env.DATABASE_URL
});

// Query builder fluente
const ordiniRecenti = await knex('ordini')
  .join('utenti', 'ordini.utente_id', 'utenti.id')
  .select('ordini.id', 'utenti.nome', 'ordini.totale', 'ordini.stato')
  .where('ordini.stato', '!=', 'annullato')
  .andWhere('ordini.creato_il', '>=', '2025-01-01')
  .orderBy('ordini.creato_il', 'desc')
  .limit(50);

// Transazioni
await knex.transaction(async (trx) => {
  const [ordineId] = await trx('ordini').insert({ utente_id: 1, totale: 99.99 }).returning('id');
  await trx('ordini_prodotti').insert({ ordine_id: ordineId.id, prodotto_id: 5, quantita: 1, prezzo: 99.99 });
});
```

### TypeORM

TypeORM e un ORM TypeScript-first che supporta sia il pattern Active Record che il pattern Data Mapper. Funziona con i principali database relazionali e con MongoDB.

```typescript
import { Entity, PrimaryGeneratedColumn, Column, ManyToOne, CreateDateColumn } from 'typeorm';

@Entity('utenti')
class Utente {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @Column({ length: 100 })
  nome: string;

  @Column({ type: 'enum', enum: ['utente', 'admin'], default: 'utente' })
  ruolo: string;

  @CreateDateColumn({ name: 'creato_il' })
  creatoIl: Date;

  @OneToMany(() => Ordine, ordine => ordine.utente)
  ordini: Ordine[];
}

// Query con repository
const repo = dataSource.getRepository(Utente);
const utenti = await repo.find({
  where: { ruolo: 'admin' },
  relations: ['ordini'],
  order: { creatoIl: 'DESC' }
});
```

### Drizzle ORM

Drizzle e un ORM leggero e type-safe per TypeScript che si distingue per le sue query che assomigliano al SQL nativo. Non utilizza decoratori ne code generation, ma un approccio puramente funzionale.

```typescript
import { pgTable, serial, varchar, decimal, boolean, timestamp } from 'drizzle-orm/pg-core';
import { drizzle } from 'drizzle-orm/node-postgres';
import { eq, gte, and, desc } from 'drizzle-orm';

// Definizione schema
const utenti = pgTable('utenti', {
  id: serial('id').primaryKey(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  nome: varchar('nome', { length: 100 }),
  attivo: boolean('attivo').default(true),
  creatoIl: timestamp('creato_il').defaultNow()
});

const ordini = pgTable('ordini', {
  id: serial('id').primaryKey(),
  utenteId: serial('utente_id').references(() => utenti.id),
  totale: decimal('totale', { precision: 10, scale: 2 }).notNull(),
  creatoIl: timestamp('creato_il').defaultNow()
});

const db = drizzle(pool);

// Query type-safe che assomiglia a SQL
const risultati = await db
  .select({
    nome: utenti.nome,
    email: utenti.email,
    totaleOrdini: ordini.totale
  })
  .from(utenti)
  .leftJoin(ordini, eq(utenti.id, ordini.utenteId))
  .where(and(eq(utenti.attivo, true), gte(ordini.totale, '100')))
  .orderBy(desc(ordini.creatoIl));
```

---

## Migrazioni

Le migrazioni sono il meccanismo standard per gestire l'evoluzione dello schema del database nel tempo. Funzionano come un sistema di version control per il database: ogni migrazione descrive una trasformazione dello schema (aggiunta di tabelle, modifica di colonne, creazione di indici) e la sua operazione inversa (rollback). Le migrazioni sono file di codice versionati nel repository, garantendo che ogni ambiente (sviluppo, staging, produzione) possa riprodurre esattamente lo stesso schema.

### Concetto Fondamentale

Senza migrazioni, la gestione dello schema diventa rapidamente caotica. Sviluppatori diversi applicano modifiche manuali ai propri database locali, lo schema di produzione diverge da quello di sviluppo, e i deploy diventano operazioni rischiose e non riproducibili. Le migrazioni risolvono questi problemi fornendo una sequenza ordinata e deterministica di trasformazioni, tipicamente con timestamp per l'ordinamento e meccanismi di tracking per sapere quali migrazioni sono gia state applicate.

### Prisma Migrate

Prisma Migrate genera migrazioni SQL a partire dalle differenze tra lo schema Prisma attuale e lo stato del database. Ogni migrazione viene salvata come file SQL leggibile nella cartella `prisma/migrations`.

```bash
# Flusso di lavoro tipico:
# 1. Modifica il file schema.prisma
# 2. Genera e applica la migrazione
npx prisma migrate dev --name descrizione_cambio

# La migrazione generata sara in prisma/migrations/TIMESTAMP_descrizione_cambio/migration.sql
```

```sql
-- Esempio di migrazione generata automaticamente
-- prisma/migrations/20250615120000_aggiungi_recensioni/migration.sql

CREATE TABLE "recensioni" (
  "id" SERIAL NOT NULL,
  "voto" INTEGER NOT NULL,
  "commento" TEXT,
  "creato_il" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "utente_id" INTEGER NOT NULL,
  "prodotto_id" INTEGER NOT NULL,

  CONSTRAINT "recensioni_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "recensioni_utente_id_prodotto_id_key"
  ON "recensioni"("utente_id", "prodotto_id");

ALTER TABLE "recensioni"
  ADD CONSTRAINT "recensioni_utente_id_fkey"
  FOREIGN KEY ("utente_id") REFERENCES "utenti"("id") ON DELETE RESTRICT;

ALTER TABLE "recensioni"
  ADD CONSTRAINT "recensioni_prodotto_id_fkey"
  FOREIGN KEY ("prodotto_id") REFERENCES "prodotti"("id") ON DELETE RESTRICT;
```

### Alembic (Python/SQLAlchemy)

Alembic e lo strumento di migrazione standard per progetti Python che utilizzano SQLAlchemy. Supporta migrazioni auto-generate e manuali.

```bash
# Inizializzazione
alembic init alembic

# Generazione automatica basata sui modelli SQLAlchemy
alembic revision --autogenerate -m "aggiungi_tabella_recensioni"

# Applicazione migrazioni
alembic upgrade head

# Rollback di una migrazione
alembic downgrade -1

# Visualizzare cronologia
alembic history
```

```python
# alembic/versions/abc123_aggiungi_tabella_recensioni.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'recensioni',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('voto', sa.Integer(), nullable=False),
        sa.Column('commento', sa.Text()),
        sa.Column('utente_id', sa.Integer(), sa.ForeignKey('utenti.id')),
        sa.Column('prodotto_id', sa.Integer(), sa.ForeignKey('prodotti.id')),
        sa.Column('creato_il', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('utente_id', 'prodotto_id')
    )

def downgrade():
    op.drop_table('recensioni')
```

### Knex Migrations

```bash
# Creare una nuova migrazione
npx knex migrate:make aggiungi_recensioni

# Eseguire le migrazioni pendenti
npx knex migrate:latest

# Rollback dell'ultima batch
npx knex migrate:rollback
```

```javascript
// migrations/20250615120000_aggiungi_recensioni.js
exports.up = function(knex) {
  return knex.schema.createTable('recensioni', (table) => {
    table.increments('id').primary();
    table.integer('voto').notNullable();
    table.text('commento');
    table.integer('utente_id').references('id').inTable('utenti').onDelete('CASCADE');
    table.integer('prodotto_id').references('id').inTable('prodotti').onDelete('CASCADE');
    table.timestamp('creato_il').defaultTo(knex.fn.now());
    table.unique(['utente_id', 'prodotto_id']);
  });
};

exports.down = function(knex) {
  return knex.schema.dropTable('recensioni');
};
```

---

## Database Design

La progettazione del database e una delle decisioni architetturali piu impattanti di un progetto software. Uno schema ben progettato semplifica lo sviluppo, migliora le prestazioni e facilita l'evoluzione del sistema. Uno schema mal progettato genera query contorte, problemi di coerenza, difficolta di manutenzione e colli di bottiglia prestazionali che peggiorano con la crescita dei dati.

### Normalizzazione

La normalizzazione e il processo di organizzazione delle tabelle per ridurre la ridondanza dei dati e le anomalie di inserimento, aggiornamento e cancellazione. Si esprime attraverso una serie di **forme normali** progressive.

**Prima Forma Normale (1NF)**: ogni cella contiene un solo valore atomico (non liste, non gruppi ripetuti) e ogni riga e univocamente identificabile tramite una chiave primaria.

```
-- Viola 1NF (valori multipli in una cella)
| id | nome  | telefoni                    |
|----|-------|-----------------------------|
| 1  | Mario | 333-1234567, 06-12345678    |

-- Conforme a 1NF
| id | nome  | telefono     | tipo    |
|----|-------|--------------|---------|
| 1  | Mario | 333-1234567  | mobile  |
| 1  | Mario | 06-12345678  | fisso   |
```

**Seconda Forma Normale (2NF)**: soddisfa 1NF e ogni attributo non-chiave dipende dall'intera chiave primaria (non da un suo sottoinsieme). Questo e rilevante solo per tabelle con chiavi primarie composte.

```
-- Viola 2NF (nome_prodotto dipende solo da prodotto_id, non dalla chiave composta)
| ordine_id | prodotto_id | nome_prodotto     | quantita |
|-----------|-------------|-------------------|----------|
| 1         | 5           | Mouse Wireless    | 2        |

-- Conforme a 2NF: separare in due tabelle
-- Tabella ordini_prodotti: ordine_id, prodotto_id, quantita
-- Tabella prodotti: prodotto_id, nome_prodotto
```

**Terza Forma Normale (3NF)**: soddisfa 2NF e nessun attributo non-chiave dipende transitivamente da un altro attributo non-chiave.

```
-- Viola 3NF (nome_citta dipende da cap, che dipende da id)
| id | nome  | cap   | nome_citta |
|----|-------|-------|------------|
| 1  | Mario | 00100 | Roma       |

-- Conforme a 3NF: separare
-- Tabella utenti: id, nome, cap
-- Tabella citta: cap, nome_citta
```

Per la maggior parte delle applicazioni web, raggiungere la 3NF e sufficiente e rappresenta un buon equilibrio tra integrita dei dati e complessita delle query.

### Denormalizzazione

La denormalizzazione e il processo deliberato di introdurre ridondanza per migliorare le prestazioni in lettura. Non e l'opposto della normalizzazione ne una scorciatoia per evitarla: si denormalizza solo dopo aver normalizzato correttamente e identificato colli di bottiglia reali misurati attraverso profiling.

Scenari in cui la denormalizzazione e giustificata:

- **Contatori materializzati**: memorizzare il conteggio dei commenti direttamente nella tabella articoli anziche contarli con COUNT(*) ad ogni richiesta.
- **Campi calcolati**: salvare il totale dell'ordine nella riga dell'ordine anziche calcolarlo sommando i prezzi degli articoli.
- **Dati di lettura frequente**: duplicare il nome dell'autore nella tabella articoli per evitare JOIN costose su pagine ad alto traffico.
- **Tabelle di reporting**: creare tabelle aggregate specifiche per dashboard e analytics.

### Diagrammi ER (Entity-Relationship)

I diagrammi ER rappresentano visivamente la struttura del database, mostrando le entita (tabelle), i loro attributi e le relazioni tra esse. Sono lo strumento fondamentale per la comunicazione tra sviluppatori, DBA e stakeholder durante la fase di progettazione.

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   UTENTI     │       │     ORDINI       │       │   PRODOTTI   │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ PK id        │──┐    │ PK id            │    ┌──│ PK id        │
│    email     │  │    │ FK utente_id     │──┘ │  │    nome      │
│    nome      │  └───>│    totale        │    │  │    prezzo    │
│    cognome   │       │    stato         │    │  │    categoria │
│    ruolo     │       │    creato_il     │    │  └──────────────┘
└──────────────┘       └──────────────────┘    │
                              │                │
                       ┌──────────────────┐    │
                       │ ORDINI_PRODOTTI  │    │
                       ├──────────────────┤    │
                       │ PK,FK ordine_id  │────┘
                       │ PK,FK prodotto_id│───────
                       │     quantita     │
                       │     prezzo       │
                       └──────────────────┘
```

### Tipi di Relazioni

**Uno-a-Uno (1:1)**: ogni riga in una tabella corrisponde a esattamente una riga nell'altra. Si usa tipicamente per separare dati acceduti raramente (es. utente e profilo dettagliato) o per ragioni di sicurezza (dati sensibili in tabella separata).

```sql
-- 1:1 — Utente e Profilo
CREATE TABLE profili (
  id         SERIAL PRIMARY KEY,
  bio        TEXT,
  avatar_url VARCHAR(500),
  utente_id  INTEGER UNIQUE NOT NULL REFERENCES utenti(id) ON DELETE CASCADE
);
```

**Uno-a-Molti (1:N)**: una riga nella tabella padre puo corrispondere a molte righe nella tabella figlia. E la relazione piu comune nei database relazionali. Si implementa con una chiave esterna nella tabella "molti" che punta alla tabella "uno".

```sql
-- 1:N — Un utente ha molti ordini
CREATE TABLE ordini (
  id         SERIAL PRIMARY KEY,
  utente_id  INTEGER NOT NULL REFERENCES utenti(id),
  totale     DECIMAL(10, 2) NOT NULL
);
```

**Molti-a-Molti (N:M)**: righe in entrambe le tabelle possono corrispondere a molte righe nell'altra. Si implementa con una tabella ponte (junction table) che contiene le chiavi esterne di entrambe le tabelle.

```sql
-- N:M — Studenti e Corsi (con attributi sulla relazione)
CREATE TABLE iscrizioni (
  studente_id INTEGER REFERENCES studenti(id) ON DELETE CASCADE,
  corso_id    INTEGER REFERENCES corsi(id) ON DELETE CASCADE,
  data_iscrizione DATE DEFAULT CURRENT_DATE,
  voto        INTEGER CHECK (voto BETWEEN 18 AND 30),
  PRIMARY KEY (studente_id, corso_id)
);
```

---

## Performance e Ottimizzazione

Le prestazioni del database diventano critiche man mano che l'applicazione cresce in termini di dati e traffico. Una query che funziona perfettamente con mille righe puo diventare inutilizzabile con un milione. L'ottimizzazione delle prestazioni richiede un approccio sistematico: misurare, identificare i colli di bottiglia, applicare soluzioni mirate e verificare i risultati.

### Strategia di Indicizzazione

La creazione di indici e la singola azione con il maggiore impatto sulle prestazioni delle query. Tuttavia, gli indici non sono gratuiti: occupano spazio disco, rallentano le operazioni di scrittura (INSERT, UPDATE, DELETE) e richiedono manutenzione.

Regole fondamentali per una strategia di indicizzazione efficace:

- Indicizzare le colonne utilizzate frequentemente nelle clausole WHERE, JOIN e ORDER BY.
- Per indici composti, posizionare per prime le colonne con maggiore selettivita (quelle che filtrano piu righe).
- Usare indici parziali quando le query filtrano sistematicamente un sottoinsieme dei dati.
- Non indicizzare colonne con bassa cardinalita (es. un campo booleano con il 50% di TRUE e 50% di FALSE) a meno che non sia un indice parziale.
- Monitorare gli indici inutilizzati e rimuoverli: consumano risorse senza beneficio.

```sql
-- Identificare indici inutilizzati in PostgreSQL
SELECT
  schemaname, tablename, indexname,
  idx_scan AS volte_usato,
  pg_size_pretty(pg_relation_size(indexrelid)) AS dimensione
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Query Optimization con EXPLAIN

Il comando EXPLAIN e lo strumento diagnostico fondamentale per comprendere come il database esegue una query. Mostra il piano di esecuzione scelto dal query planner, inclusi i metodi di accesso alle tabelle, i tipi di JOIN e le stime sui costi.

```sql
-- EXPLAIN base: mostra il piano senza eseguire la query
EXPLAIN
SELECT u.nome, COUNT(o.id) AS num_ordini
FROM utenti u
JOIN ordini o ON u.id = o.utente_id
WHERE o.creato_il >= '2025-01-01'
GROUP BY u.id, u.nome
HAVING COUNT(o.id) > 5;

-- EXPLAIN ANALYZE: esegue la query e mostra tempi reali vs stimati
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM prodotti
WHERE categoria = 'elettronica' AND prezzo < 100
ORDER BY prezzo;
```

L'output di EXPLAIN rivela problemi comuni:

- **Seq Scan** su tabelle grandi indica un indice mancante.
- **Nested Loop** con tabelle grandi suggerisce la necessita di un Hash Join o Merge Join.
- Grande differenza tra righe stimate e righe effettive indica statistiche obsolete (eseguire `ANALYZE`).
- **Sort** con alto costo indica la necessita di un indice sull'ordinamento richiesto.

### Connection Pooling

Aprire una nuova connessione al database per ogni richiesta HTTP e estremamente costoso: l'handshake TCP, l'autenticazione e l'allocazione di memoria lato server richiedono tempo e risorse. Il connection pooling risolve questo problema mantenendo un pool di connessioni preallocate e riutilizzabili.

```javascript
// Connection pooling con pg-pool (Node.js + PostgreSQL)
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,                // massimo connessioni nel pool
  idleTimeoutMillis: 30000, // chiudi connessioni inattive dopo 30s
  connectionTimeoutMillis: 5000 // timeout per ottenere una connessione
});

// Ogni query usa una connessione dal pool e la rilascia automaticamente
const result = await pool.query('SELECT * FROM utenti WHERE id = $1', [42]);
```

Per applicazioni con elevata concorrenza, **PgBouncer** e un connection pooler esterno che si posiziona tra l'applicazione e PostgreSQL. Supporta tre modalita: session pooling, transaction pooling e statement pooling, permettendo a centinaia di connessioni applicative di condividere poche decine di connessioni reali al database.

### Read Replica

Le read replica sono copie in sola lettura del database primario, mantenute aggiornate attraverso la replicazione. Distribuiscono il carico di lettura su piu server, migliorando drasticamente le prestazioni per applicazioni read-heavy (la maggior parte delle applicazioni web ha un rapporto lettura/scrittura di 80/20 o superiore).

```javascript
// Esempio di routing lettura/scrittura
import { Pool } from 'pg';

const writerPool = new Pool({ connectionString: process.env.DATABASE_PRIMARY_URL });
const readerPool = new Pool({ connectionString: process.env.DATABASE_REPLICA_URL });

async function query(sql, params, readOnly = false) {
  const pool = readOnly ? readerPool : writerPool;
  return pool.query(sql, params);
}

// Le letture vanno alla replica
const prodotti = await query('SELECT * FROM prodotti WHERE attivo = true', [], true);

// Le scritture vanno al primary
await query('INSERT INTO ordini (utente_id, totale) VALUES ($1, $2)', [1, 99.99], false);
```

Considerazioni importanti: le replica hanno un ritardo di replicazione (replication lag), tipicamente da millisecondi a pochi secondi. Questo significa che dopo una scrittura sul primary, la replica potrebbe non riflettere immediatamente il cambiamento. Per operazioni dove la coerenza immediata e critica (es. leggere i dati appena aggiornati), bisogna forzare la lettura dal primary.

### Caching Layer

Un livello di cache tra l'applicazione e il database riduce drasticamente il numero di query, migliorando tempi di risposta e riducendo il carico sul database. Redis e lo strumento standard per questo scopo.

L'architettura tipica di un caching layer prevede tre livelli:

1. **Cache applicativa in-memory** (es. LRU cache nel processo Node.js): latenza zero, ma limitata alla memoria del singolo processo e non condivisa tra istanze.
2. **Cache distribuita** (Redis): latenza sub-millisecondo via rete, condivisa tra tutte le istanze dell'applicazione, persistente tra i restart.
3. **Database**: fonte di verita primaria, consultata solo in caso di cache miss a tutti i livelli.

```javascript
// Caching multilivello con invalidazione basata su eventi
const NodeCache = require('node-cache');
const localCache = new NodeCache({ stdTTL: 60, checkperiod: 30 });

async function getProdotto(id) {
  const key = `prodotto:${id}`;

  // Livello 1: cache locale
  const locale = localCache.get(key);
  if (locale) return locale;

  // Livello 2: Redis
  const remoto = await redis.get(key);
  if (remoto) {
    const dati = JSON.parse(remoto);
    localCache.set(key, dati);
    return dati;
  }

  // Livello 3: database
  const prodotto = await db.query('SELECT * FROM prodotti WHERE id = $1', [id]);
  await redis.setex(key, 3600, JSON.stringify(prodotto));
  localCache.set(key, prodotto);

  return prodotto;
}
```

---

## Best Practices

Le seguenti dieci best practice rappresentano principi consolidati che, applicati sistematicamente, prevengono i problemi piu comuni nella gestione dei database per applicazioni web.

**1. Utilizzare sempre le migrazioni per le modifiche allo schema.** Mai modificare il database di produzione manualmente. Ogni cambiamento deve essere tracciato in una migrazione versionata, testata in ambiente di sviluppo e staging prima di essere applicata in produzione. Le migrazioni devono essere idempotenti quando possibile e includere sempre l'operazione di rollback.

**2. Parametrizzare tutte le query per prevenire SQL injection.** Non concatenare mai stringhe utente nelle query SQL. Utilizzare sempre parametri posizionali (`$1`, `?`) o named parameters forniti dal driver del database o dall'ORM. La SQL injection rimane una delle vulnerabilita piu comuni e piu pericolose nelle applicazioni web.

```javascript
// PERICOLOSO — mai fare questo
const query = `SELECT * FROM utenti WHERE email = '${email}'`;

// SICURO — sempre usare parametri
const result = await pool.query('SELECT * FROM utenti WHERE email = $1', [email]);
```

**3. Implementare connection pooling fin dall'inizio.** Anche per applicazioni piccole, il connection pooling migliora le prestazioni e previene l'esaurimento delle connessioni disponibili. Configurare il pool con limiti appropriati al carico previsto e monitorare l'utilizzo.

**4. Progettare lo schema partendo dalla normalizzazione, denormalizzare solo con dati concreti.** Iniziare con uno schema normalizzato in 3NF. Denormalizzare solo quando il profiling dimostra che una specifica query e un collo di bottiglia e l'aggiunta di indici non e sufficiente. Documentare ogni denormalizzazione e il razionale che la giustifica.

**5. Indicizzare in modo strategico, non indiscriminato.** Creare indici basandosi sulle query reali dell'applicazione, non su ipotesi. Monitorare le query lente tramite il log delle slow query, analizzarle con EXPLAIN e creare indici mirati. Rimuovere periodicamente gli indici inutilizzati.

**6. Implementare backup automatizzati e testare il restore regolarmente.** Configurare backup automatici giornalieri (o piu frequenti per dati critici). Ma un backup non testato non e un backup: eseguire periodicamente il restore su un ambiente di test per verificare che i backup siano integri e che la procedura di ripristino funzioni correttamente.

**7. Non memorizzare mai password in chiaro nel database.** Utilizzare algoritmi di hashing robusti come bcrypt, scrypt o Argon2 con salt unico per ogni password. Non utilizzare MD5 o SHA-256 per le password: sono troppo veloci e vulnerabili ad attacchi brute-force.

**8. Gestire le transazioni con scope minimale.** Mantenere le transazioni il piu brevi possibile per ridurre i lock e la contesa tra operazioni concorrenti. Non eseguire mai operazioni lente (chiamate HTTP, invio email) all'interno di una transazione. Acquisire i lock nell'ordine piu restrittivo per prevenire deadlock.

**9. Monitorare le prestazioni del database in modo continuo.** Implementare il monitoring delle metriche chiave: tempo medio di risposta delle query, numero di connessioni attive, utilizzo di CPU e memoria, dimensione del database, replication lag. Configurare alerting per soglie critiche. Strumenti come pg_stat_statements (PostgreSQL), Performance Schema (MySQL) e MongoDB Profiler forniscono dati essenziali.

**10. Separare le credenziali del database dal codice sorgente.** Utilizzare variabili d'ambiente o secret manager (AWS Secrets Manager, HashiCorp Vault, Doppler) per le stringhe di connessione. Mai committare credenziali nel repository. Utilizzare credenziali diverse per ogni ambiente (sviluppo, staging, produzione) con privilegi minimi necessari (principio del least privilege).

---

## Prisma Avanzato

La sezione precedente ha introdotto Prisma con schema, migrazioni e query di base. Qui si esplorano le funzionalita avanzate che distinguono un utilizzo professionale in produzione: relazioni complesse, transazioni interattive, middleware, estensioni e Prisma Accelerate per ambienti serverless.

### Relazioni Avanzate e Query Complesse

Prisma gestisce relazioni auto-referenziali (un modello che punta a se stesso) e relazioni polimorfe attraverso pattern specifici. Le relazioni auto-referenziali sono comuni per strutture gerarchiche come categorie, commenti annidati e organigrammi.

```prisma
// Schema: commenti annidati (auto-referenziale)
model Commento {
  id          Int        @id @default(autoincrement())
  testo       String
  creatoIl    DateTime   @default(now()) @map("creato_il")
  autoreId    Int        @map("autore_id")
  postId      Int        @map("post_id")
  parentId    Int?       @map("parent_id")

  autore      Utente     @relation(fields: [autoreId], references: [id])
  post        Post       @relation(fields: [postId], references: [id])
  parent      Commento?  @relation("RisposteCommento", fields: [parentId], references: [id])
  risposte    Commento[] @relation("RisposteCommento")

  @@map("commenti")
}
```

```typescript
// Query: albero di commenti con risposte annidate su 3 livelli
const commenti = await prisma.commento.findMany({
  where: { postId: 1, parentId: null },
  include: {
    autore: { select: { nome: true, avatar: true } },
    risposte: {
      include: {
        autore: { select: { nome: true, avatar: true } },
        risposte: {
          include: {
            autore: { select: { nome: true, avatar: true } }
          }
        }
      }
    }
  },
  orderBy: { creatoIl: 'desc' }
});

// Filtraggio relazionale: utenti che hanno almeno un ordine spedito
// con prodotti di una specifica categoria
const utentiAttivi = await prisma.utente.findMany({
  where: {
    ordini: {
      some: {
        stato: 'SPEDITO',
        articoli: {
          some: {
            prodotto: { categoria: 'elettronica' }
          }
        }
      }
    }
  },
  include: {
    _count: {
      select: { ordini: true, recensioni: true }
    }
  }
});

// groupBy avanzato: revenue per categoria per mese
const revenuePerCategoria = await prisma.ordineArticolo.groupBy({
  by: ['prodottoId'],
  _sum: { prezzo: true },
  _count: { _all: true },
  having: {
    prezzo: { _sum: { gt: 1000 } }
  },
  orderBy: { _sum: { prezzo: 'desc' } },
  take: 10
});
```

### Transazioni Interattive

Oltre alle transazioni batch (array di operazioni), Prisma supporta transazioni interattive con callback. Queste permettono logica condizionale all'interno della transazione: leggere dati, prendere decisioni, scrivere di conseguenza, il tutto in un'unica unita atomica.

```typescript
// Transazione interattiva: acquisto con verifica stock in tempo reale
const risultato = await prisma.$transaction(async (tx) => {
  // 1. Verifica stock all'interno della transazione
  const prodotto = await tx.prodotto.findUniqueOrThrow({
    where: { id: prodottoId }
  });

  if (prodotto.quantitaMagazzino < quantitaRichiesta) {
    throw new Error(`Stock insufficiente: ${prodotto.quantitaMagazzino} disponibili`);
  }

  // 2. Decrementa lo stock
  const prodottoAggiornato = await tx.prodotto.update({
    where: { id: prodottoId },
    data: {
      quantitaMagazzino: { decrement: quantitaRichiesta }
    }
  });

  // 3. Crea l'ordine
  const ordine = await tx.ordine.create({
    data: {
      utenteId,
      totale: prodotto.prezzo.mul(quantitaRichiesta),
      stato: 'CONFERMATO',
      articoli: {
        create: {
          prodottoId,
          quantita: quantitaRichiesta,
          prezzo: prodotto.prezzo
        }
      }
    }
  });

  // 4. Registra il movimento
  await tx.movimentoMagazzino.create({
    data: {
      prodottoId,
      tipo: 'VENDITA',
      quantita: -quantitaRichiesta,
      riferimento: `ordine:${ordine.id}`
    }
  });

  return ordine;
}, {
  maxWait: 5000,      // tempo massimo di attesa per iniziare la transazione
  timeout: 10000,     // timeout totale della transazione
  isolationLevel: 'Serializable'
});
```

### Prisma Client Extensions

Le estensioni di Prisma Client permettono di aggiungere funzionalita personalizzate al client senza modificare il codice generato. Si possono estendere modelli, client, query e risultati.

```typescript
// Estensione per soft delete e audit log
const prismaExtended = prisma.$extends({
  model: {
    $allModels: {
      // Aggiunge softDelete a tutti i modelli
      async softDelete<T>(this: T, where: any) {
        const context = Prisma.getExtensionContext(this);
        return (context as any).update({
          where,
          data: { eliminatoIl: new Date(), attivo: false }
        });
      }
    }
  },
  query: {
    $allModels: {
      // Intercetta tutte le query di lettura per escludere i record eliminati
      async findMany({ model, operation, args, query }) {
        args.where = { ...args.where, eliminatoIl: null };
        return query(args);
      },
      // Audit log per tutte le operazioni di scrittura
      async $allOperations({ model, operation, args, query }) {
        const inizio = Date.now();
        const risultato = await query(args);
        const durata = Date.now() - inizio;

        if (['create', 'update', 'delete'].includes(operation)) {
          console.log(`[Audit] ${model}.${operation} in ${durata}ms`);
        }
        return risultato;
      }
    }
  },
  result: {
    utente: {
      nomeCompleto: {
        needs: { nome: true, cognome: true },
        compute(utente) {
          return `${utente.nome} ${utente.cognome}`;
        }
      }
    }
  }
});

// Utilizzo trasparente
await prismaExtended.utente.softDelete({ id: 42 });
const utenti = await prismaExtended.utente.findMany(); // esclude automaticamente i soft-deleted
```

### Prisma Accelerate

Prisma Accelerate e il servizio gestito di Prisma che fornisce connection pooling globale e caching a livello query per ambienti serverless e edge. Risolve due problemi critici: l'esaurimento delle connessioni in ambienti con molte funzioni serverless concorrenti e la latenza di accesso al database da edge function distribuite globalmente.

```typescript
// Configurazione Prisma Accelerate
// 1. La connection string diventa quella di Accelerate
// DATABASE_URL="prisma://accelerate.prisma-data.net/?api_key=..."

// 2. Utilizzo con cache strategy
const prodottiPopolari = await prisma.prodotto.findMany({
  where: { disponibile: true },
  orderBy: { vendite: 'desc' },
  take: 20,
  cacheStrategy: {
    ttl: 300,           // cache per 5 minuti
    swr: 60             // stale-while-revalidate: serve dati stale per 60s mentre rivalidaSw
  }
});

// Query senza cache (solo connection pooling)
const saldoConto = await prisma.conto.findUnique({
  where: { utenteId: 42 }
  // Nessuna cacheStrategy = nessuna cache, solo pooling
});
```

Accelerate opera come proxy tra l'applicazione e il database. Le connessioni dalla funzione serverless terminano al nodo Accelerate piu vicino (disponibile in 16+ regioni), che mantiene un pool persistente di connessioni verso il database. Questo elimina il cold start della connessione e previene l'esaurimento del limite di connessioni.

### Prisma 7: Architettura Pure TypeScript

Prisma 7 (rilasciato nel tardo 2025) ha rappresentato il cambiamento architetturale piu significativo nella storia del progetto. Il query engine in Rust e stato completamente rimosso e sostituito da un'implementazione puramente TypeScript. Questo ha ridotto il peso del pacchetto (da oltre 8 MB a circa 1.6 MB), eliminato i problemi di compatibilita con piattaforme edge e semplificato il debugging. Il comando `prisma generate` resta necessario ma il processo e notevolmente piu veloce. Per i progetti che aggiornano da Prisma 5.x/6.x, la migrazione e sostanzialmente trasparente: le API del client non cambiano, ma le dipendenze binarie native non sono piu necessarie.

---

## Drizzle ORM Approfondimento

Drizzle ORM si e affermato come alternativa principale a Prisma nell'ecosistema TypeScript. Con un bundle di soli 7.4 KB (minified + gzipped) e zero dipendenze esterne, Drizzle adotta una filosofia radicalmente diversa: lo schema e definito come codice TypeScript ordinario, le query assomigliano a SQL nativo con autocompletamento completo, e non esiste un passaggio di generazione del codice. La versione 1.0 beta, rilasciata a inizio 2025, ha stabilizzato l'ecosistema con tooling di migrazione affidabile e supporto esteso per PostgreSQL, MySQL, SQLite e i principali database serverless.

### Schema Avanzato

Lo schema Drizzle e codice TypeScript puro. Questo significa che si possono usare costanti, funzioni helper e logica condizionale durante la definizione dello schema, cosa impossibile con il DSL dichiarativo di Prisma.

```typescript
import {
  pgTable, pgEnum, serial, varchar, text, integer,
  decimal, boolean, timestamp, jsonb, uuid, index,
  uniqueIndex, primaryKey, foreignKey, check
} from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

// Enum PostgreSQL nativo
export const ruoloEnum = pgEnum('ruolo', ['utente', 'admin', 'moderatore']);
export const statoOrdineEnum = pgEnum('stato_ordine', [
  'in_attesa', 'confermato', 'spedito', 'consegnato', 'annullato'
]);

// Schema con vincoli avanzati
export const utenti = pgTable('utenti', {
  id: uuid('id').defaultRandom().primaryKey(),
  email: varchar('email', { length: 255 }).notNull(),
  username: varchar('username', { length: 50 }).notNull(),
  passwordHash: text('password_hash').notNull(),
  nome: varchar('nome', { length: 100 }),
  cognome: varchar('cognome', { length: 100 }),
  ruolo: ruoloEnum('ruolo').default('utente'),
  attivo: boolean('attivo').default(true),
  metadata: jsonb('metadata').$type<{ preferenze: Record<string, unknown> }>(),
  creatoIl: timestamp('creato_il', { withTimezone: true }).defaultNow(),
  aggiornatoIl: timestamp('aggiornato_il', { withTimezone: true }).defaultNow()
}, (table) => [
  uniqueIndex('idx_utenti_email').on(table.email),
  uniqueIndex('idx_utenti_username').on(table.username),
  index('idx_utenti_ruolo_attivo').on(table.ruolo, table.attivo)
]);

export const ordini = pgTable('ordini', {
  id: serial('id').primaryKey(),
  utenteId: uuid('utente_id').notNull().references(() => utenti.id, { onDelete: 'cascade' }),
  totale: decimal('totale', { precision: 10, scale: 2 }).notNull(),
  stato: statoOrdineEnum('stato').default('in_attesa'),
  note: text('note'),
  creatoIl: timestamp('creato_il', { withTimezone: true }).defaultNow()
}, (table) => [
  index('idx_ordini_utente_data').on(table.utenteId, table.creatoIl),
  index('idx_ordini_stato').on(table.stato).where(
    sql`${table.stato} != 'annullato'`
  )
]);

// Definizione relazioni (separata dalla tabella, non modifica lo schema SQL)
export const utentiRelations = relations(utenti, ({ many, one }) => ({
  ordini: many(ordini),
  profilo: one(profili, {
    fields: [utenti.id],
    references: [profili.utenteId]
  })
}));

export const ordiniRelations = relations(ordini, ({ one, many }) => ({
  utente: one(utenti, {
    fields: [ordini.utenteId],
    references: [utenti.id]
  }),
  articoli: many(ordiniArticoli)
}));
```

### Queries API Relazionale

Drizzle offre due API per le query: la API SQL-like (select/insert/update/delete) e la Relational Queries API. Quest'ultima genera sempre esattamente una query SQL ottimizzata, evitando il problema N+1 tipico di altri ORM.

```typescript
import { drizzle } from 'drizzle-orm/node-postgres';
import * as schema from './schema';

const db = drizzle(pool, { schema });

// Query relazionale: un unico SQL generato
const utentiConOrdini = await db.query.utenti.findMany({
  where: (utenti, { eq }) => eq(utenti.attivo, true),
  columns: {
    passwordHash: false  // escludi campi sensibili
  },
  with: {
    ordini: {
      where: (ordini, { gte }) => gte(ordini.creatoIl, new Date('2025-01-01')),
      orderBy: (ordini, { desc }) => [desc(ordini.creatoIl)],
      limit: 5,
      with: {
        articoli: {
          with: { prodotto: true }
        }
      }
    },
    profilo: true
  },
  orderBy: (utenti, { desc }) => [desc(utenti.creatoIl)],
  limit: 20,
  offset: 0
});

// findFirst con relazioni
const ordine = await db.query.ordini.findFirst({
  where: (ordini, { eq }) => eq(ordini.id, 42),
  with: {
    utente: { columns: { nome: true, email: true } },
    articoli: {
      with: {
        prodotto: { columns: { nome: true, prezzo: true } }
      }
    }
  }
});
```

### Prepared Statements e Performance

Le prepared statement in Drizzle eliminano il costo di parsing SQL ripetuto. Per query frequenti in produzione, il guadagno e misurabile: il database riusa il piano di esecuzione precompilato e i parametri posizionali, eliminando l'overhead di concatenazione SQL ad ogni invocazione.

```typescript
// Prepared statement per query frequente
const getUtenteByEmail = db
  .select()
  .from(utenti)
  .where(eq(utenti.email, sql.placeholder('email')))
  .prepare('get_utente_by_email');

// Riuso in ogni richiesta: zero costo di parsing
const utente = await getUtenteByEmail.execute({ email: 'mario@example.com' });

// Prepared statement con join complessa
const getOrdiniUtente = db
  .select({
    ordineId: ordini.id,
    totale: ordini.totale,
    stato: ordini.stato,
    prodotto: prodotti.nome,
    quantita: ordiniArticoli.quantita
  })
  .from(ordini)
  .innerJoin(ordiniArticoli, eq(ordini.id, ordiniArticoli.ordineId))
  .innerJoin(prodotti, eq(ordiniArticoli.prodottoId, prodotti.id))
  .where(eq(ordini.utenteId, sql.placeholder('utenteId')))
  .orderBy(desc(ordini.creatoIl))
  .prepare('get_ordini_utente');
```

### Drizzle Kit: Migrazioni

Drizzle Kit e il CLI per generare e gestire le migrazioni SQL a partire dallo schema TypeScript. A differenza di Prisma, le migrazioni generate sono file SQL puri, leggibili e modificabili senza restrizioni.

```bash
# Configurazione in drizzle.config.ts
# export default defineConfig({
#   schema: './src/db/schema.ts',
#   out: './drizzle',
#   dialect: 'postgresql',
#   dbCredentials: { url: process.env.DATABASE_URL! }
# });

# Generare migrazione dalle differenze dello schema
npx drizzle-kit generate

# Applicare migrazioni al database
npx drizzle-kit migrate

# Push diretto dello schema (sviluppo rapido, senza file di migrazione)
npx drizzle-kit push

# Pull dello schema dal database esistente
npx drizzle-kit pull

# Ispezionare il database con Drizzle Studio (browser)
npx drizzle-kit studio
```

Le migrazioni generate sono accelerate di circa 14 volte rispetto alle versioni precedenti di Drizzle Kit. Per migrazioni personalizzate (seed, trasformazioni dati, DDL non supportato dal kit), Drizzle permette di creare file di migrazione vuoti con `drizzle-kit generate --custom` e scrivere SQL arbitrario.

---

## Strategie di Migrazione Avanzate

Le migrazioni di base (creare tabelle, aggiungere colonne) sono state trattate nella sezione precedente. Qui si affrontano le strategie necessarie quando il database e in produzione, con traffico attivo, e le modifiche allo schema non possono interrompere il servizio.

### Pattern Expand-Contract

Il pattern expand-contract (detto anche parallel change) e la strategia fondamentale per migrazioni zero-downtime. Si articola in fasi distinte, ciascuna deployabile indipendentemente.

**Fase 1 — Expand:** aggiungere la nuova struttura senza rimuovere quella esistente. Entrambe coesistono. L'applicazione continua a usare la vecchia struttura.

```sql
-- Esempio: dividere "indirizzo" (stringa) in campi separati
-- Fase 1: aggiungere le nuove colonne
ALTER TABLE utenti ADD COLUMN via VARCHAR(200);
ALTER TABLE utenti ADD COLUMN citta VARCHAR(100);
ALTER TABLE utenti ADD COLUMN cap VARCHAR(10);
ALTER TABLE utenti ADD COLUMN provincia CHAR(2);

-- Trigger di sincronizzazione bidirezionale
CREATE OR REPLACE FUNCTION sync_indirizzo() RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' OR NEW.indirizzo IS DISTINCT FROM OLD.indirizzo THEN
    -- parsing semplificato, in produzione usare logica robusta
    NEW.via := split_part(NEW.indirizzo, ', ', 1);
    NEW.citta := split_part(NEW.indirizzo, ', ', 2);
  END IF;
  IF NEW.via IS DISTINCT FROM OLD.via OR NEW.citta IS DISTINCT FROM OLD.citta THEN
    NEW.indirizzo := CONCAT(NEW.via, ', ', NEW.citta, ' ', NEW.cap);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_indirizzo
  BEFORE INSERT OR UPDATE ON utenti
  FOR EACH ROW EXECUTE FUNCTION sync_indirizzo();
```

**Fase 2 — Migrate (backfill):** popolare le nuove colonne con i dati esistenti. Per tabelle grandi, operare in batch con pause tra un batch e l'altro per non saturare il database.

```sql
-- Backfill in batch da 5000 righe con pausa tra i batch
DO $$
DECLARE
  batch_size INTEGER := 5000;
  righe_aggiornate INTEGER;
BEGIN
  LOOP
    UPDATE utenti
    SET via = split_part(indirizzo, ', ', 1),
        citta = split_part(indirizzo, ', ', 2)
    WHERE via IS NULL AND indirizzo IS NOT NULL
    LIMIT batch_size;

    GET DIAGNOSTICS righe_aggiornate = ROW_COUNT;
    EXIT WHEN righe_aggiornate = 0;

    RAISE NOTICE 'Aggiornate % righe', righe_aggiornate;
    PERFORM pg_sleep(0.5);  -- pausa di 500ms tra i batch
  END LOOP;
END $$;
```

**Fase 3 — Contract (codice):** aggiornare l'applicazione per leggere e scrivere solo le nuove colonne. Verificare che tutto funzioni correttamente.

**Fase 4 — Contract (schema):** rimuovere le vecchie colonne, i trigger di sincronizzazione e i vincoli obsoleti.

```sql
-- Solo dopo che l'applicazione usa esclusivamente i nuovi campi
DROP TRIGGER trg_sync_indirizzo ON utenti;
DROP FUNCTION sync_indirizzo();
ALTER TABLE utenti DROP COLUMN indirizzo;
```

### Blue-Green Database Migrations

Nelle architetture blue-green, la migrazione del database richiede attenzione particolare perche il database e condiviso tra le due versioni dell'applicazione. La regola fondamentale: ogni migrazione deve essere compatibile con la versione precedente e quella successiva dell'applicazione. Questo significa che le migrazioni che rimuovono colonne o rinominano tabelle devono essere suddivise in piu step, con almeno un deployment intermedio dove entrambe le strutture coesistono.

### Rollback di Migrazioni

Ogni migrazione deve includere un'operazione di rollback testata. In Prisma, il rollback si esegue con `prisma migrate resolve` per marcare una migrazione come annullata e applicare manualmente lo SQL inverso. In Drizzle e Knex, le migrazioni down sono esplicite. La regola critica: testare il rollback in staging prima di applicare la migrazione in produzione.

---

## Connection Pooling Avanzato

La sezione Performance ha introdotto il concetto di connection pooling. Qui si approfondiscono le configurazioni avanzate con PgBouncer, le differenze tra le modalita di pooling e le considerazioni specifiche per ambienti serverless.

### PgBouncer: Modalita e Configurazione

PgBouncer opera in tre modalita, ciascuna con trade-off diversi:

**Session pooling:** la connessione viene assegnata al client per l'intera durata della sessione. E la modalita piu conservativa: supporta tutte le funzionalita PostgreSQL (prepared statements, LISTEN/NOTIFY, cursori), ma il riuso delle connessioni e limitato. Utile quando l'applicazione usa feature session-specific.

**Transaction pooling:** la connessione viene rilasciata al pool alla fine di ogni transazione. E la modalita consigliata per la maggior parte delle applicazioni web: massimizza il riuso delle connessioni permettendo a centinaia di client di condividere poche connessioni reali. Limitazione: le prepared statements con nome e le variabili di sessione (`SET`) non funzionano tra transazioni diverse.

**Statement pooling:** la connessione viene rilasciata dopo ogni singolo statement. Massimo riuso ma non supporta transazioni multi-statement. Raramente usato in pratica.

```ini
; pgbouncer.ini — configurazione tipica per applicazione web
[databases]
ecommerce = host=db-primary.internal port=5432 dbname=ecommerce

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

; Transaction pooling per applicazioni web
pool_mode = transaction

; Dimensionamento del pool
default_pool_size = 25          ; connessioni per database/utente
min_pool_size = 5               ; connessioni minime mantenute
reserve_pool_size = 5           ; connessioni extra per picchi
reserve_pool_timeout = 3        ; secondi prima di usare la reserve

; Limiti
max_client_conn = 1000          ; connessioni client totali
max_db_connections = 50         ; connessioni reali al database

; Timeout
server_idle_timeout = 600       ; chiudi connessioni server inattive dopo 10min
client_idle_timeout = 0         ; disabilitato (gestito dall'applicazione)
query_timeout = 30              ; timeout per singola query
query_wait_timeout = 120        ; timeout attesa per connessione dal pool

; Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
stats_period = 60
```

### Dimensionamento del Pool

La formula classica per il dimensionamento del pool di connessioni PostgreSQL e:

```
connessioni_ottimali = (core_cpu * 2) + dischi_spindle
```

Per SSD, una regola empirica affidabile e `core_cpu * 2 + 1`. Un server con 4 core funziona bene con 9-10 connessioni. Aggiungere connessioni oltre questo punto non migliora le prestazioni e puo peggiorarle a causa del context switching.

Per l'applicazione, il pool lato client (pg-pool, HikariCP) deve essere dimensionato considerando il numero di istanze: se ci sono 10 istanze dell'applicazione ciascuna con pool di 20, il database riceve 200 connessioni. PgBouncer tra applicazione e database permette di disaccoppiare queste dimensioni: 200 connessioni dall'applicazione a PgBouncer, 25 connessioni da PgBouncer a PostgreSQL.

### Pooling in Ambienti Serverless

Le funzioni serverless (AWS Lambda, Vercel Functions, Cloudflare Workers) creano una sfida unica: ogni invocazione concorrente puo aprire una connessione al database, e il numero di invocazioni concorrenti e imprevedibile. Senza pooling esterno, un picco di traffico puo esaurire rapidamente il limite di connessioni di PostgreSQL (tipicamente 100-200 di default).

Soluzioni consolidate:

- **PgBouncer su un'istanza dedicata** tra le funzioni Lambda e il database RDS.
- **Prisma Accelerate** come proxy gestito con pooling globale integrato su 16+ regioni. Le connessioni dalla funzione terminano al nodo Accelerate piu vicino via HTTP, eliminando il TCP handshake verso il database.
- **Neon pooler** integrato nella piattaforma Neon con endpoint dedicato (`-pooler` nel hostname).
- **Supabase Supavisor** come pooler Elixir-based incluso nella piattaforma Supabase.

---

## Performance Avanzata del Database

Le ottimizzazioni di base — indici B-tree, `EXPLAIN`, `LIMIT` — coprono l'80% dei casi. Questa sezione affronta le tecniche avanzate che separano un database "funzionante" da uno genuinamente performante sotto carico reale.

### Tipologie di Indice Avanzate

PostgreSQL offre diverse strutture d'indice oltre al classico B-tree, ciascuna ottimale per pattern di accesso specifici.

**BRIN (Block Range Index):** Ideale per tabelle grandi con dati naturalmente ordinati (tipicamente time-series). Anziche indicizzare ogni riga, BRIN memorizza il valore minimo e massimo per ogni blocco fisico di pagine. Occupano pochissimo spazio (ordini di grandezza meno di un B-tree equivalente), ma funzionano solo se la correlazione fisica tra ordine di inserimento e valore della colonna e alta.

```sql
-- Tabella eventi con ~500M righe, inseriti cronologicamente
CREATE INDEX idx_events_created_brin ON events
  USING BRIN (created_at)
  WITH (pages_per_range = 32);

-- Verifica correlazione fisica (deve essere > 0.9 per BRIN efficace)
SELECT correlation
FROM pg_stats
WHERE tablename = 'events' AND attname = 'created_at';
```

**Expression Index:** Indicizza il risultato di un'espressione, non la colonna grezza. Essenziale quando le query filtrano su valori trasformati.

```sql
-- Ricerca case-insensitive su email senza full-table scan
CREATE INDEX idx_users_email_lower ON users (LOWER(email));

-- La query deve usare la stessa espressione
SELECT * FROM users WHERE LOWER(email) = 'mario@example.com';

-- Indice su estrazione JSONB
CREATE INDEX idx_metadata_status ON orders ((metadata->>'status'));
```

**Covering Index (INCLUDE):** Aggiunge colonne non-chiave all'indice per soddisfare query interamente dall'indice (index-only scan), senza accedere alla tabella heap.

```sql
-- La query cerca per user_id ma seleziona anche email e name
CREATE INDEX idx_users_userid_covering ON users (user_id)
  INCLUDE (email, name);

-- Questa query ora e un index-only scan — zero heap access
SELECT email, name FROM users WHERE user_id = 42;
```

**Partial Index:** Indicizza solo un sottoinsieme di righe. Riduce drasticamente dimensione dell'indice e costo di manutenzione.

```sql
-- Solo ordini attivi (il 5% della tabella)
CREATE INDEX idx_orders_active ON orders (created_at)
  WHERE status = 'active';
```

### EXPLAIN ANALYZE: Interpretazione Pratica

`EXPLAIN ANALYZE` esegue realmente la query e confronta le stime del planner con i risultati effettivi. La chiave e leggere i numeri critici.

```sql
-- Query lenta: ricerca su colonna non indicizzata
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE customer_email = 'test@example.com';
```

Output tipico problematico:

```
Seq Scan on orders  (cost=0.00..45892.00 rows=1 width=120)
                    (actual time=289.431..892.102 rows=1 loops=1)
  Filter: (customer_email = 'test@example.com'::text)
  Rows Removed by Filter: 2000000
  Buffers: shared hit=12034 read=23858
Planning Time: 0.089 ms
Execution Time: 892.156 ms
```

Segnali di allarme: `Seq Scan` su tabella grande, `Rows Removed by Filter` alto (2M righe scartate per trovarne 1), tempo di esecuzione ~900ms.

Dopo l'aggiunta dell'indice:

```sql
CREATE INDEX idx_orders_email ON orders (customer_email);

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE customer_email = 'test@example.com';
```

```
Index Scan using idx_orders_email on orders  (cost=0.43..8.45 rows=1 width=120)
                                              (actual time=0.028..0.029 rows=1 loops=1)
  Index Cond: (customer_email = 'test@example.com'::text)
  Buffers: shared hit=4
Planning Time: 0.112 ms
Execution Time: 0.048 ms
```

Da 892ms a 0.048ms — miglioramento di 18.000x. Il `Buffers: shared hit=4` conferma che servono solo 4 pagine dall'indice anziche 35.892 dalla tabella.

### Tuning del Query Planner

PostgreSQL espone parametri che influenzano le decisioni del planner. Modificarli a livello di sessione permette di diagnosticare scelte subottimali.

```sql
-- Forza il planner a evitare sequential scan (solo per debugging)
SET enable_seqscan = off;
EXPLAIN ANALYZE SELECT ...;
SET enable_seqscan = on;  -- ripristinare sempre

-- Costo pagina random — su SSD abbassare da 4.0 (default HDD) a 1.1
ALTER SYSTEM SET random_page_cost = 1.1;

-- Parallelismo: PostgreSQL 16+ puo parallelizzare molte operazioni
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;

-- Statistiche piu accurate per colonne ad alta cardinalita
ALTER TABLE orders ALTER COLUMN customer_id SET STATISTICS 1000;
ANALYZE orders;
```

### Monitoraggio Query Lente

Abilitare `pg_stat_statements` e il primo passo per identificare le query che consumano piu risorse:

```sql
-- Top 10 query per tempo totale di esecuzione
SELECT
  queryid,
  calls,
  round(total_exec_time::numeric, 2) AS total_ms,
  round(mean_exec_time::numeric, 2) AS avg_ms,
  rows,
  query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

Combinare con `auto_explain` per loggare automaticamente i piani di query che superano una soglia:

```sql
-- In postgresql.conf
-- auto_explain.log_min_duration = '500ms'
-- auto_explain.log_analyze = on
-- auto_explain.log_buffers = on
```

---

## Sicurezza del Database

La sicurezza del database e un aspetto critico spesso sottovalutato. Un'applicazione web puo avere autenticazione robusta e input validation perfetta, ma se il database non e configurato correttamente, un singolo punto di accesso compromesso puo esporre tutti i dati.

### SQL Injection: Prevenzione Approfondita

La SQL injection rimane nella OWASP Top 10 ed e la vulnerabilita piu comune nelle applicazioni che interagiscono con database. La regola fondamentale e semplice: mai concatenare input utente nelle query SQL. Ma l'applicazione pratica richiede attenzione a scenari meno ovvi.

```typescript
// VULNERABILE: concatenazione diretta
const query = `SELECT * FROM utenti WHERE ruolo = '${req.query.ruolo}'`;
// Un attaccante invia: ruolo = "admin' OR '1'='1"
// Query risultante: SELECT * FROM utenti WHERE ruolo = 'admin' OR '1'='1'

// VULNERABILE: template literal con interpolazione
const query = `SELECT * FROM prodotti WHERE categoria = '${categoria}'
               ORDER BY ${req.query.orderBy}`;
// ORDER BY non puo essere parametrizzato — richiede whitelist

// SICURO: query parametrizzata
const result = await pool.query(
  'SELECT * FROM utenti WHERE ruolo = $1',
  [req.query.ruolo]
);

// SICURO: ORDER BY con whitelist
const colonnePermesse = ['nome', 'prezzo', 'creato_il'];
const orderBy = colonnePermesse.includes(req.query.orderBy)
  ? req.query.orderBy
  : 'creato_il';
const result = await pool.query(
  `SELECT * FROM prodotti WHERE categoria = $1 ORDER BY ${orderBy}`,
  [categoria]
);

// SICURO: Prisma gestisce automaticamente la parametrizzazione
const utenti = await prisma.utente.findMany({
  where: { ruolo: req.query.ruolo as Ruolo }
});
// Prisma genera: SELECT ... WHERE ruolo = $1 con binding sicuro

// ATTENZIONE: $queryRaw richiede il tagged template literal
// VULNERABILE
const utenti = await prisma.$queryRawUnsafe(
  `SELECT * FROM utenti WHERE nome = '${nome}'`
);
// SICURO
const utenti = await prisma.$queryRaw`
  SELECT * FROM utenti WHERE nome = ${nome}
`;
```

### Row-Level Security (RLS)

PostgreSQL RLS permette di definire politiche di accesso a livello di riga. Ogni query viene automaticamente filtrata in base all'utente connesso, fornendo un livello di sicurezza difensivo in profondita che protegge i dati anche in caso di bug applicativo.

```sql
-- Abilitare RLS sulla tabella
ALTER TABLE ordini ENABLE ROW LEVEL SECURITY;

-- Policy: ogni utente vede solo i propri ordini
CREATE POLICY ordini_utente ON ordini
  FOR ALL
  USING (utente_id = current_setting('app.utente_corrente')::INTEGER);

-- Policy per admin: accesso completo
CREATE POLICY ordini_admin ON ordini
  FOR ALL
  USING (current_setting('app.ruolo_corrente') = 'admin');

-- Impostare il contesto utente per ogni richiesta
-- (tipicamente in un middleware o all'inizio della transazione)
SET LOCAL app.utente_corrente = '42';
SET LOCAL app.ruolo_corrente = 'utente';

-- Ora ogni query sulla tabella ordini restituisce solo le righe dell'utente 42
SELECT * FROM ordini;  -- automaticamente filtrato

-- Policy per multi-tenancy: isolamento per tenant
CREATE POLICY tenant_isolation ON dati_azienda
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id')::UUID);
```

### Crittografia dei Dati

La protezione dei dati richiede crittografia su piu livelli:

**Encryption at rest:** i file del database sul disco sono crittografati. PostgreSQL non offre TDE (Transparent Data Encryption) nativo, ma si puo ottenere con LUKS a livello filesystem o con servizi gestiti come RDS che lo includono di default.

**Encryption in transit:** tutte le connessioni tra applicazione e database devono usare TLS. In PostgreSQL si configura con `sslmode=require` (o `verify-full` per ambienti critici) nella stringa di connessione.

**Encryption a livello colonna:** per dati particolarmente sensibili (PII, dati sanitari), si puo crittografare a livello applicativo prima dell'inserimento.

```sql
-- Crittografia a livello colonna con pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Inserimento con dato crittografato
INSERT INTO dati_sensibili (utente_id, codice_fiscale_enc)
VALUES (
  42,
  pgp_sym_encrypt('RSSMRA85M01H501Z', current_setting('app.encryption_key'))
);

-- Lettura con decrittografia
SELECT utente_id,
       pgp_sym_decrypt(codice_fiscale_enc::bytea, current_setting('app.encryption_key')) AS codice_fiscale
FROM dati_sensibili
WHERE utente_id = 42;
```

### Audit Logging

Un sistema di audit logging registra chi ha fatto cosa e quando sul database. PostgreSQL offre diverse opzioni: trigger personalizzati, l'estensione `pgaudit`, o il log nativo configurato opportunamente.

```sql
-- Tabella di audit generica
CREATE TABLE audit_log (
  id          BIGSERIAL PRIMARY KEY,
  tabella     VARCHAR(100) NOT NULL,
  operazione  VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
  riga_id     TEXT,
  dati_prima  JSONB,
  dati_dopo   JSONB,
  utente_db   VARCHAR(100) DEFAULT current_user,
  utente_app  VARCHAR(100) DEFAULT current_setting('app.utente_corrente', true),
  timestamp   TIMESTAMPTZ DEFAULT now(),
  ip_client   INET
);

-- Trigger di audit generico
CREATE OR REPLACE FUNCTION fn_audit_trigger() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_log (tabella, operazione, riga_id, dati_prima, dati_dopo)
  VALUES (
    TG_TABLE_NAME,
    TG_OP,
    CASE TG_OP WHEN 'DELETE' THEN OLD.id::TEXT ELSE NEW.id::TEXT END,
    CASE TG_OP WHEN 'INSERT' THEN NULL ELSE to_jsonb(OLD) END,
    CASE TG_OP WHEN 'DELETE' THEN NULL ELSE to_jsonb(NEW) END
  );
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Applicare l'audit a tabelle specifiche
CREATE TRIGGER audit_utenti
  AFTER INSERT OR UPDATE OR DELETE ON utenti
  FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();

CREATE TRIGGER audit_ordini
  AFTER INSERT OR UPDATE OR DELETE ON ordini
  FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();
```

---

## MongoDB con Mongoose

Mongoose e l'ODM (Object-Document Mapper) standard per MongoDB in ambienti Node.js. Fornisce una struttura di schema sopra la flessibilita nativa di MongoDB, aggiungendo validazione, middleware, virtual e population — concetti che mancano nel driver MongoDB nativo.

### Schema e Modelli

```typescript
import mongoose, { Schema, Document, Types } from 'mongoose';

// Interfaccia TypeScript per type-safety
interface IProdotto extends Document {
  nome: string;
  slug: string;
  prezzo: number;
  categoria: string;
  specifiche: Record<string, unknown>;
  tag: string[];
  disponibile: boolean;
  venditeCount: number;
  recensioni: Types.ObjectId[];
  creatoIl: Date;
  aggiornatoIl: Date;
}

const prodottoSchema = new Schema<IProdotto>({
  nome: {
    type: String,
    required: [true, 'Il nome e obbligatorio'],
    trim: true,
    maxlength: [200, 'Il nome non puo superare 200 caratteri']
  },
  slug: {
    type: String,
    unique: true,
    lowercase: true,
    index: true
  },
  prezzo: {
    type: Number,
    required: true,
    min: [0, 'Il prezzo non puo essere negativo'],
    set: (v: number) => Math.round(v * 100) / 100  // arrotonda a 2 decimali
  },
  categoria: {
    type: String,
    required: true,
    enum: ['elettronica', 'accessori', 'abbigliamento', 'casa'],
    index: true
  },
  specifiche: { type: Schema.Types.Mixed, default: {} },
  tag: [{ type: String, lowercase: true, trim: true }],
  disponibile: { type: Boolean, default: true, index: true },
  venditeCount: { type: Number, default: 0 },
  recensioni: [{ type: Schema.Types.ObjectId, ref: 'Recensione' }]
}, {
  timestamps: { createdAt: 'creatoIl', updatedAt: 'aggiornatoIl' },
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Virtual: campo calcolato, non persistito nel database
prodottoSchema.virtual('prezzoFormattato').get(function() {
  return `€${this.prezzo.toFixed(2)}`;
});

// Indice composto per query frequenti
prodottoSchema.index({ categoria: 1, prezzo: -1 });
prodottoSchema.index({ nome: 'text', tag: 'text' });  // full-text search

const Prodotto = mongoose.model<IProdotto>('Prodotto', prodottoSchema);
```

### Middleware (Hooks)

Mongoose middleware permette di intercettare operazioni di salvataggio, validazione, rimozione e query. Sono l'equivalente dei trigger di database, ma eseguiti a livello applicativo.

```typescript
// Pre-save: genera slug dal nome prima del salvataggio
prodottoSchema.pre('save', function(next) {
  if (this.isModified('nome')) {
    this.slug = this.nome
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }
  next();
});

// Pre-find: escludi automaticamente i prodotti non disponibili
prodottoSchema.pre(/^find/, function(next) {
  // Applicare solo se non esplicitamente richiesto
  if (!this.getOptions().includiNonDisponibili) {
    this.where({ disponibile: true });
  }
  next();
});

// Post-save: invalidare la cache Redis dopo il salvataggio
prodottoSchema.post('save', async function(doc) {
  await redis.del(`prodotto:${doc.slug}`);
  await redis.del('prodotti:lista:*');  // invalidazione pattern
});
```

### Population e Lean Queries

Population e il meccanismo di Mongoose per risolvere riferimenti tra documenti (simile a JOIN in SQL). Le lean query restituiscono oggetti JavaScript puri (POJO) anziche documenti Mongoose completi, migliorando significativamente le prestazioni in lettura.

```typescript
// Population standard
const ordine = await Ordine.findById(ordineId)
  .populate('utente', 'nome email')  // solo campi nome ed email
  .populate({
    path: 'articoli.prodotto',
    select: 'nome prezzo categoria',
    match: { disponibile: true }
  });

// Lean query: 3-5x piu veloce, restituisce POJO
const prodotti = await Prodotto
  .find({ categoria: 'elettronica' })
  .sort({ prezzo: -1 })
  .limit(20)
  .lean()    // POJO, senza metodi Mongoose (.save(), .validate(), ecc.)
  .exec();
// prodotti[0].save() -> errore, non e un documento Mongoose
// Ma e significativamente piu veloce per risposte API read-only
```

---

## Database Testing

Il testing del database richiede strategie specifiche: isolamento tra test, dati riproducibili, gestione delle migrazioni e prestazioni accettabili nella suite di test. Un test che condivide lo stato con altri test e un test fragile che fallira in modo imprevedibile.

### Testcontainers

Testcontainers avvia un container Docker con un database reale per ogni suite di test. Questo garantisce che i test eseguano contro lo stesso database usato in produzione, non un sostituto in-memory con comportamento diverso.

```typescript
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { PrismaClient } from '@prisma/client';
import { execSync } from 'child_process';

let container: StartedPostgreSqlContainer;
let prisma: PrismaClient;

beforeAll(async () => {
  // Avvia un container PostgreSQL dedicato per questa suite
  container = await new PostgreSqlContainer('postgres:16-alpine')
    .withDatabase('test_db')
    .withUsername('test')
    .withPassword('test')
    .start();

  // Connection string del container
  const databaseUrl = container.getConnectionUri();
  process.env.DATABASE_URL = databaseUrl;

  // Applica le migrazioni Prisma al database di test
  execSync('npx prisma migrate deploy', {
    env: { ...process.env, DATABASE_URL: databaseUrl }
  });

  prisma = new PrismaClient({ datasourceUrl: databaseUrl });
}, 60000); // timeout lungo per il pull dell'immagine

afterAll(async () => {
  await prisma.$disconnect();
  await container.stop();
});

// Isolamento: pulisci le tabelle tra un test e l'altro
afterEach(async () => {
  const tabelle = await prisma.$queryRaw<Array<{ tablename: string }>>`
    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
      AND tablename != '_prisma_migrations'
  `;
  for (const { tablename } of tabelle) {
    await prisma.$executeRawUnsafe(`TRUNCATE TABLE "${tablename}" CASCADE`);
  }
});
```

### Fixture e Seeding

I fixture sono insiemi di dati predefiniti utilizzati per popolare il database prima dei test. Un buon sistema di fixture e componibile (si possono combinare fixture diversi), deterministico (stesso input = stesso output) e indipendente dall'ordine di esecuzione.

```typescript
// fixtures/utenti.ts
export function creaUtenteFixture(overrides: Partial<Prisma.UtenteCreateInput> = {}) {
  return {
    email: `test-${Date.now()}-${Math.random().toString(36).slice(2)}@example.com`,
    username: `testuser_${Date.now()}`,
    passwordHash: '$2b$10$fixedHashForTests...',
    nome: 'Test',
    cognome: 'User',
    ruolo: 'UTENTE' as const,
    attivo: true,
    ...overrides
  };
}

// fixtures/ordini.ts
export async function creaOrdineConArticoli(
  prisma: PrismaClient,
  utenteId: number,
  articoli: Array<{ prodottoId: number; quantita: number; prezzo: number }>
) {
  const totale = articoli.reduce((sum, a) => sum + a.quantita * a.prezzo, 0);
  return prisma.ordine.create({
    data: {
      utenteId,
      totale,
      stato: 'CONFERMATO',
      articoli: { create: articoli }
    },
    include: { articoli: true }
  });
}

// Test con fixture componibili
describe('Repository Ordini', () => {
  test('calcola il totale correttamente', async () => {
    // Arrange
    const utente = await prisma.utente.create({
      data: creaUtenteFixture()
    });
    const prodotto = await prisma.prodotto.create({
      data: { nome: 'Test', prezzo: 29.99, categoria: 'test' }
    });
    const ordine = await creaOrdineConArticoli(prisma, utente.id, [
      { prodottoId: prodotto.id, quantita: 3, prezzo: 29.99 }
    ]);

    // Assert
    expect(Number(ordine.totale)).toBeCloseTo(89.97, 2);
  });
});
```

### Strategie di Isolamento

L'isolamento tra test puo essere ottenuto in tre modi, ciascuno con trade-off diversi:

**Truncate tra test:** rapido e semplice, ma richiede attenzione all'ordine di truncate per le foreign key (CASCADE risolve). E la strategia consigliata per la maggior parte dei casi.

**Transaction rollback:** ogni test esegue in una transazione che viene annullata alla fine. Velocissimo perche non scrive realmente su disco, ma non funziona se il codice testato gestisce le proprie transazioni.

**Database per test:** ogni test crea un database dedicato. Massimo isolamento ma alto costo in termini di tempo. Riservato a test di integrazione complessi dove le altre strategie non sono sufficienti.

---

## Pattern Multi-Tenancy

Le applicazioni SaaS servono tipicamente piu organizzazioni (tenant) dalla stessa infrastruttura. La strategia di isolamento dei dati tra tenant e una delle decisioni architetturali piu critiche, con impatto su sicurezza, prestazioni, costi e complessita operativa.

### Shared Table con Tenant ID

Tutti i tenant condividono le stesse tabelle. Ogni riga include una colonna `tenant_id` che identifica il proprietario. E l'approccio piu semplice e scalabile per la maggior parte delle applicazioni SaaS.

```sql
-- Ogni tabella include tenant_id
CREATE TABLE progetti (
  id          SERIAL PRIMARY KEY,
  tenant_id   UUID NOT NULL,
  nome        VARCHAR(200) NOT NULL,
  descrizione TEXT,
  creato_il   TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Indice composto: tenant_id SEMPRE come prima colonna
CREATE INDEX idx_progetti_tenant ON progetti(tenant_id, creato_il DESC);

-- RLS per isolamento automatico
ALTER TABLE progetti ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolamento ON progetti
  FOR ALL USING (tenant_id = current_setting('app.tenant_id')::UUID);
```

```typescript
// Middleware per impostare il tenant su ogni richiesta
async function tenantMiddleware(req: Request, res: Response, next: NextFunction) {
  const tenantId = req.headers['x-tenant-id'];
  if (!tenantId) return res.status(403).json({ error: 'Tenant non specificato' });

  // Imposta il contesto PostgreSQL per RLS
  await pool.query(`SET LOCAL app.tenant_id = '${tenantId}'`);
  req.tenantId = tenantId;
  next();
}
```

**Vantaggi:** schema unificato, migrazioni applicate una sola volta, aggregazioni cross-tenant possibili, costi contenuti.
**Svantaggi:** rischio di bug che espongono dati cross-tenant (RLS mitiga), prestazioni degradano con molti dati senza partizionamento.

### Schema-per-Tenant

Ogni tenant ottiene un proprio schema PostgreSQL. L'applicazione imposta il `search_path` all'inizio di ogni richiesta per indirizzare le query allo schema corretto.

```sql
-- Creazione schema per nuovo tenant
CREATE SCHEMA tenant_acme;

-- Tabelle nello schema del tenant
CREATE TABLE tenant_acme.progetti (
  id          SERIAL PRIMARY KEY,
  nome        VARCHAR(200) NOT NULL,
  descrizione TEXT
);

-- Impostare il search_path per la richiesta
SET search_path TO tenant_acme, public;
-- Ora: SELECT * FROM progetti → cerca in tenant_acme.progetti
```

**Vantaggi:** isolamento forte senza rischio di leak cross-tenant via bug applicativi, possibilita di struttura leggermente diversa per tenant (rollout graduali), backup e restore per singolo tenant.
**Svantaggi:** le migrazioni devono essere applicate a ogni schema, le prestazioni di PostgreSQL degradano con migliaia di schemi, complessita operativa significativa.

### Database-per-Tenant

Ogni tenant ha un database dedicato. Massimo isolamento: un incidente su un database non impatta gli altri. Questa strategia e tipica di applicazioni enterprise con requisiti di compliance stringenti (dati residenti in regioni specifiche, SLA personalizzati).

**Vantaggi:** isolamento perfetto, configurazione e tuning per tenant, backup e disaster recovery indipendenti, compliance geografica.
**Svantaggi:** costo lineare (1000 tenant = 1000 database), migrazioni orchestrate con sistema di retry, impossibilita di query cross-tenant dirette, complessita di routing delle connessioni.

### Scelta della Strategia

| Criterio | Shared Table | Schema-per-Tenant | Database-per-Tenant |
|----------|-------------|-------------------|---------------------|
| Numero tenant | Migliaia-milioni | Centinaia | Decine-centinaia |
| Isolamento | Logico (RLS) | Forte (schema) | Completo |
| Costo per tenant | Minimo | Basso | Alto |
| Complessita migrazioni | Bassa | Media | Alta |
| Compliance geografica | Difficile | Possibile | Nativa |
| Caso d'uso tipico | SaaS B2C/B2SMB | SaaS B2B mid-market | Enterprise regulated |

---

## Monitoraggio e Osservabilita

Un database in produzione senza monitoraggio e una bomba a orologeria. I problemi di prestazioni si accumulano gradualmente: query lente che peggiorano, connessioni che si esauriscono, bloat delle tabelle. Senza metriche e alerting, il primo segnale di un problema e spesso un'interruzione del servizio.

### pg_stat_statements

L'estensione `pg_stat_statements` e lo strumento piu importante per il monitoraggio delle query PostgreSQL. Registra statistiche aggregate per ogni query normalizzata: numero di esecuzioni, tempo totale e medio, righe restituite, blocchi letti da cache e da disco.

```sql
-- Abilitare l'estensione (richiede riavvio se non gia nel shared_preload_libraries)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top 10 query per tempo totale
SELECT
  LEFT(query, 100) AS query_troncata,
  calls AS esecuzioni,
  ROUND(total_exec_time::NUMERIC, 2) AS tempo_totale_ms,
  ROUND(mean_exec_time::NUMERIC, 2) AS tempo_medio_ms,
  rows AS righe_restituite,
  ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2)
    AS cache_hit_pct
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Query con peggior cache hit ratio (leggono troppo da disco)
SELECT
  LEFT(query, 80) AS query,
  calls,
  shared_blks_read AS blocchi_disco,
  shared_blks_hit AS blocchi_cache,
  ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2)
    AS cache_hit_pct
FROM pg_stat_statements
WHERE calls > 100
  AND shared_blks_hit + shared_blks_read > 0
ORDER BY cache_hit_pct ASC
LIMIT 10;

-- Reset periodico delle statistiche
SELECT pg_stat_statements_reset();
```

### Slow Query Logging

Il log delle query lente permette di identificare le query problematiche in tempo reale. PostgreSQL registra nel log tutte le query che superano la soglia configurata.

```sql
-- postgresql.conf
-- log_min_duration_statement = 500   -- logga query piu lente di 500ms
-- log_statement = 'none'             -- non loggare tutte le query (troppo rumore)
-- log_line_prefix = '%t [%p] %u@%d '  -- timestamp, PID, utente, database

-- Identificare le connessioni attive e le query in esecuzione
SELECT
  pid,
  usename,
  datname,
  state,
  NOW() - query_start AS durata,
  LEFT(query, 100) AS query
FROM pg_stat_activity
WHERE state = 'active'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_start;

-- Kill di una query bloccata (con cautela)
-- SELECT pg_cancel_backend(pid);      -- annullamento graceful
-- SELECT pg_terminate_backend(pid);   -- terminazione forzata
```

### Metriche Chiave da Monitorare

Un sistema di monitoraggio efficace per PostgreSQL deve tracciare almeno queste metriche:

| Metrica | Soglia di allarme | Significato |
|---------|-------------------|-------------|
| Connessioni attive / max_connections | > 80% | Rischio di esaurimento connessioni |
| Cache hit ratio | < 95% | Memoria insufficiente, troppe letture da disco |
| Transazioni per secondo (TPS) | Anomalia vs baseline | Variazione indica problemi o picchi |
| Replication lag | > 10 secondi | Le replica non sono aggiornate |
| Dead tuples / live tuples | > 20% | VACUUM necessario, tabella bloated |
| Tempo medio query (p99) | > 1 secondo | Query lente da ottimizzare |
| Dimensione WAL | Crescita anomala | Possibile problema di checkpoint |
| Lock wait events | > 0 sostenuto | Deadlock o contesa di risorse |

### Stack di Monitoraggio

Lo stack Prometheus + Grafana e lo standard de facto per il monitoraggio dei database. L'esportatore `postgres_exporter` raccoglie metriche da PostgreSQL e le espone in formato Prometheus.

```yaml
# docker-compose.yml — stack di monitoraggio
services:
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15.0
    environment:
      DATA_SOURCE_NAME: "postgresql://monitor:password@db:5432/ecommerce?sslmode=disable"
    ports:
      - "9187:9187"

  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.4.0
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "admin"
```

Per PgBouncer, l'endpoint `SHOW STATS` espone metriche sulle connessioni attive, le transazioni e le query. Strumenti come Datadog, Netdata e Grafana Cloud offrono integrazioni dedicate per PgBouncer con dashboard preconfigurate che monitorano utilizzo del pool, throughput e latenze.

---

## Database Edge e Serverless

I database edge e serverless rappresentano l'evoluzione piu significativa nel panorama dei database per applicazioni web. Offrono pricing basato sull'utilizzo effettivo, eliminazione della gestione infrastrutturale e funzionalita come il branching dei database e lo scale-to-zero che cambiano radicalmente il workflow di sviluppo.

### Neon

Neon e una piattaforma PostgreSQL serverless open-source che separa compute e storage. Il compute si avvia e si spegne automaticamente in base al traffico (scale-to-zero), e lo storage cresce senza limiti predefiniti. La killer feature di Neon e il **database branching**: creare un branch del database come si crea un branch Git, con copia copy-on-write istantanea dell'intero dataset.

```bash
# CLI Neon: creare un branch per una feature
neonctl branches create --name feature-nuova-auth --parent main

# Il branch condivide i dati del parent (copy-on-write)
# Le modifiche al branch non impattano il parent
# Ideale per: preview environments, CI/CD, test di migrazioni

# Connessione al branch (connection string diversa)
# DATABASE_URL="postgresql://user:pass@ep-branch-xyz.eu-central-1.aws.neon.tech/dbname"

# Eliminare il branch dopo il merge
neonctl branches delete feature-nuova-auth
```

Neon include un connection pooler integrato (basato su PgBouncer) accessibile aggiungendo `-pooler` all'endpoint hostname. E l'unica piattaforma che ancora offre scale-to-zero di default, il che la rende particolarmente economica per ambienti di sviluppo e staging. La latenza di cold start (primo query dopo l'idle) e di 400-750ms.

### Turso

Turso utilizza libSQL, un fork open-source di SQLite con capacita server. L'architettura si basa su **embedded replicas**: repliche di lettura che eseguono all'interno del processo dell'applicazione stessa, con latenza di lettura pari a zero (nessun round-trip di rete). Le scritture vengono inviate al nodo primario e propagate alle repliche.

```typescript
import { createClient } from '@libsql/client';

// Client con embedded replica
const db = createClient({
  url: 'libsql://my-database-org.turso.io',  // nodo primario per scritture
  authToken: process.env.TURSO_AUTH_TOKEN,
  syncUrl: 'file:local-replica.db'            // replica locale per letture
});

// Lettura: dalla replica locale, latenza ~0ms
const result = await db.execute('SELECT * FROM prodotti WHERE categoria = ?', ['elettronica']);

// Scrittura: al nodo primario, propagata alla replica
await db.execute('INSERT INTO ordini (utente_id, totale) VALUES (?, ?)', [42, 99.99]);

// Sincronizzazione manuale della replica
await db.sync();
```

Turso e particolarmente adatto per applicazioni con pattern di lettura intensivo distribuite globalmente. In gennaio 2025, Turso ha pero annunciato cambiamenti significativi: scale-to-zero deprecato per nuovi utenti e edge replicas discontinuate per nuove registrazioni, con consolidamento dell'infrastruttura su AWS.

### PlanetScale

PlanetScale offre database MySQL scalabile basato su Vitess (il framework di sharding sviluppato da YouTube). Dal settembre 2025, PlanetScale offre anche PostgreSQL gestito come prodotto separato. La piattaforma si distingue per: schema management con branching (simile a Neon ma con workflow di review delle migrazioni), query insights con analisi dettagliata delle prestazioni e zero cold start (i database sono always-on).

```bash
# CLI PlanetScale: workflow di migrazione con branch
pscale branch create ecommerce add-colonna-telefono

# Connettersi al branch per applicare modifiche
pscale connect ecommerce add-colonna-telefono --port 3307
# -> mysql -h 127.0.0.1 -P 3307

# Creare un deploy request (simile a una pull request per lo schema)
pscale deploy-request create ecommerce add-colonna-telefono

# Dopo la review, deployare
pscale deploy-request deploy ecommerce 1
```

### Confronto Database Edge

| Caratteristica | Neon | Turso | PlanetScale |
|----------------|------|-------|-------------|
| Database | PostgreSQL | libSQL (SQLite fork) | MySQL / PostgreSQL |
| Scale-to-zero | Si (default) | Deprecato (nuovi utenti) | No (always-on) |
| Cold start | 400-750ms | N/A | Nessuno |
| Branching | Si (copy-on-write) | No | Si (con deploy request) |
| Edge replicas | Via pooler regionale | Embedded replicas | CDN cache |
| Free tier | 0.5 GB storage | 9 GB storage | 5 GB storage |
| Caso d'uso ideale | Dev/staging + prod PostgreSQL | Letture globali, SQLite ecosystem | Enterprise MySQL scaling |

---

## Ricerca Full-Text Avanzata

La sezione PostgreSQL ha introdotto la ricerca full-text con `tsvector`, `tsquery` e ranking di base. Qui si approfondiscono le strategie avanzate che rendono PostgreSQL un motore di ricerca competitivo per la maggior parte delle applicazioni web, eliminando la necessita di strumenti esterni come Elasticsearch fino a volumi dell'ordine di milioni di documenti.

### Operatori tsquery Avanzati

Oltre al semplice `plainto_tsquery` visto in precedenza, PostgreSQL offre operatori di ricerca sofisticati per query precise.

```sql
-- Operatore AND (&): entrambi i termini devono essere presenti
SELECT titolo FROM articoli
WHERE search_vector @@ to_tsquery('italian', 'sicurezza & database');

-- Operatore OR (|): almeno uno dei termini
SELECT titolo FROM articoli
WHERE search_vector @@ to_tsquery('italian', 'PostgreSQL | MySQL');

-- Operatore NOT (!): escludere un termine
SELECT titolo FROM articoli
WHERE search_vector @@ to_tsquery('italian', 'database & !NoSQL');

-- Operatore di prossimita (<->): termini adiacenti (phrase search)
SELECT titolo FROM articoli
WHERE search_vector @@ to_tsquery('italian', 'sviluppo <-> web');

-- Prossimita con distanza (<N>): termini entro N posizioni
SELECT titolo FROM articoli
WHERE search_vector @@ to_tsquery('italian', 'machine <2> learning');

-- Prefix matching (:*): ricerca per prefisso
SELECT titolo FROM articoli
WHERE search_vector @@ to_tsquery('italian', 'program:*');
-- Trova: programmazione, programma, programmatore, ecc.

-- websearch_to_tsquery: interpreta query "naturali" (come farebbe un utente)
SELECT titolo, ts_rank(search_vector, query) AS rank
FROM articoli, websearch_to_tsquery('italian', '"sviluppo web" -PHP react OR vue') AS query
WHERE search_vector @@ query
ORDER BY rank DESC;
-- Interpreta: frase esatta "sviluppo web", escludi PHP, includi react o vue
```

### Ricerca Fuzzy con pg_trgm

L'estensione `pg_trgm` complementa la ricerca full-text gestendo casi che `tsvector` non copre: errori di battitura, nomi propri, parole non presenti nel dizionario linguistico. Opera scomponendo le stringhe in trigrammi (sequenze di 3 caratteri) e calcolando la similarita tra essi.

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Indice GIN per ricerche fuzzy
CREATE INDEX idx_prodotti_nome_trgm ON prodotti USING GIN(nome gin_trgm_ops);
CREATE INDEX idx_utenti_nome_trgm ON utenti USING GIN(nome gin_trgm_ops);

-- Ricerca per similarita: trova "tastiera" anche con typo "tasteira"
SELECT nome, similarity(nome, 'tasteira') AS sim
FROM prodotti
WHERE nome % 'tasteira'      -- operatore % usa la soglia di similarita (default 0.3)
ORDER BY sim DESC
LIMIT 10;

-- Regolare la soglia di similarita
SET pg_trgm.similarity_threshold = 0.4;  -- piu alto = piu restrittivo

-- Ricerca per distanza: utile per autocomplete
SELECT nome, nome <-> 'mous' AS distanza  -- operatore distanza (1 - similarity)
FROM prodotti
ORDER BY distanza
LIMIT 5;
-- Risultati: Mouse wireless (0.6), Mouse ergonomico (0.6), Mouse gaming (0.65), ...

-- LIKE e ILIKE accelerati: con indice trgm, anche LIKE '%pattern%' usa l'indice
SELECT nome FROM prodotti
WHERE nome ILIKE '%wireless%';  -- con indice GIN trgm: Index Scan, non Seq Scan
```

### Strategia di Ricerca Combinata

Per un'esperienza di ricerca di qualita in produzione, la strategia ottimale combina full-text search (per la rilevanza semantica) e pg_trgm (per la tolleranza agli errori), con pesi e ranking personalizzati.

```sql
-- Funzione di ricerca combinata con fallback
CREATE OR REPLACE FUNCTION cerca_prodotti(termine TEXT, limite INTEGER DEFAULT 20)
RETURNS TABLE(id INTEGER, nome VARCHAR, prezzo NUMERIC, rank REAL) AS $$
BEGIN
  -- Prima: ricerca full-text con ranking
  RETURN QUERY
  SELECT p.id, p.nome, p.prezzo,
         ts_rank_cd(p.search_vector, websearch_to_tsquery('italian', termine)) AS rank
  FROM prodotti p
  WHERE p.search_vector @@ websearch_to_tsquery('italian', termine)
    AND p.disponibile = true
  ORDER BY rank DESC
  LIMIT limite;

  -- Se la ricerca full-text non ha risultati, fallback a fuzzy
  IF NOT FOUND THEN
    RETURN QUERY
    SELECT p.id, p.nome, p.prezzo,
           similarity(p.nome, termine) AS rank
    FROM prodotti p
    WHERE p.nome % termine AND p.disponibile = true
    ORDER BY rank DESC
    LIMIT limite;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Utilizzo
SELECT * FROM cerca_prodotti('tasteira mecanica');
-- Se il full-text non trova risultati (typo), pg_trgm trovera "tastiera meccanica"
```

### Indici GIN: Ottimizzazione

Gli indici GIN (Generalized Inverted Index) sono la struttura dati chiave per la ricerca full-text e per `pg_trgm`. Per tabelle molto grandi (milioni di righe), la configurazione dell'indice impatta significativamente prestazioni di ricerca e tempo di aggiornamento.

```sql
-- Indice GIN con fast update (default: on)
-- Fast update accumula le modifiche in una lista pendente, accelerando INSERT/UPDATE
-- ma la lista va compattata periodicamente per non degradare le ricerche
CREATE INDEX idx_articoli_search ON articoli USING GIN(search_vector)
  WITH (fastupdate = on, gin_pending_list_limit = 4096);

-- Per tabelle con INSERT frequenti e ricerche meno frequenti: fast update ON
-- Per tabelle con pochi INSERT e ricerche intensive: fast update OFF

-- Verificare lo stato della pending list
SELECT * FROM pg_stat_all_indexes WHERE indexrelname = 'idx_articoli_search';

-- Compattare manualmente la pending list
-- REINDEX INDEX idx_articoli_search;  -- attenzione: blocca le scritture

-- Indice combinato tsvector + trgm su colonne diverse
CREATE INDEX idx_search_fulltext ON articoli USING GIN(search_vector);
CREATE INDEX idx_search_fuzzy ON articoli USING GIN(titolo gin_trgm_ops);
```

### Quando PostgreSQL Non Basta

PostgreSQL full-text search e adeguato per la maggior parte delle applicazioni web con fino a milioni di documenti. I limiti emergono quando si richiedono: ricerca su miliardi di documenti (Elasticsearch/OpenSearch), analisi linguistica avanzata multi-lingua (Elasticsearch con analyzer personalizzati), ricerca geo-distribuita a latenza sub-10ms (Algolia, Typesense), o faceted search complessa con aggregazioni real-time su dataset molto grandi. Per queste esigenze, la soluzione consigliata e un motore di ricerca dedicato (Elasticsearch, Meilisearch, Typesense) sincronizzato con PostgreSQL tramite CDC (Change Data Capture) o event-driven update.

---

Questa guida copre i fondamenti dei database per lo sviluppo web, dalla teoria della normalizzazione alle strategie di ottimizzazione in produzione. La padronanza di questi concetti permette di progettare sistemi che rimangono performanti e manutenibili al crescere della complessita e del volume dei dati. Il consiglio finale e sperimentare attivamente: creare un database locale, popolare le tabelle con dati realistici, eseguire query con EXPLAIN, confrontare le prestazioni con e senza indici. La teoria diventa competenza solida solo attraverso la pratica diretta.

---

## Esercizi

### Esercizio 1 — Modellazione relazionale e normalizzazione

**Obiettivo:** Progettare uno schema relazionale normalizzato partendo da requisiti di business.

Dato il seguente scenario — un sistema di prenotazione per una catena di ristoranti — modellare il database:

- Entità: `restaurants` (nome, indirizzo, orari apertura, capacità), `tables` (numero, posti, zona), `customers` (nome, email, telefono), `reservations` (data, ora, durata, numero ospiti, stato), `menu_items` (nome, descrizione, prezzo, categoria, allergeni)
- Ogni ristorante ha più tavoli; ogni prenotazione riguarda un tavolo specifico in un ristorante specifico
- Un cliente può avere più prenotazioni; una prenotazione può includere un pre-ordine da menu

Requisiti:
- Scrivere lo schema DDL in PostgreSQL con tipi appropriati (TIMESTAMPTZ, ENUM o check constraint per gli stati, JSONB per gli orari di apertura)
- Normalizzare fino alla 3NF e documentare la dipendenza funzionale di ogni tabella
- Creare indici per le query più frequenti: prenotazioni per data, prenotazioni per cliente, tavoli disponibili per ristorante e fascia oraria
- Scrivere le query: trovare tutti i tavoli disponibili per una data/ora, elencare le prenotazioni di un cliente con dettaglio ristorante, calcolare il revenue medio per ristorante per mese
- Popolare le tabelle con almeno 50 prenotazioni di test tramite script SQL

### Esercizio 2 — CRUD con Prisma e migrazioni versionarie

**Obiettivo:** Padroneggiare un ORM type-safe con workflow di migrazione professionale.

Costruire un servizio Node.js/TypeScript per la gestione di un blog con Prisma:

- Schema Prisma con modelli: `User` (id, email unique, name, role enum), `Post` (id, title, content, slug unique, status enum draft/published/archived, publishedAt nullable, authorId), `Tag` (id, name unique), relazione many-to-many `Post` ↔ `Tag`
- Generare la migrazione iniziale con `prisma migrate dev`
- Implementare una seconda migrazione che aggiunga il campo `viewCount` a `Post` con default 0 e un indice su `publishedAt`
- Repository layer con metodi: `createPost` (con tag), `findPublishedPosts` (paginato, filtrabile per tag, ordinabile per data), `findPostBySlug` (con include di autore e tag), `updatePost` (con gestione dei tag: aggiunta e rimozione), `softDeletePost` (impostare status ad archived)
- Scrivere test unitari per ogni metodo del repository utilizzando un database SQLite in-memory per i test
- Documentare il flusso di rollback di una migrazione

### Esercizio 3 — Caching con Redis e strategie di invalidazione

**Obiettivo:** Implementare caching multi-livello con gestione corretta dell'invalidazione.

Estendere l'applicazione dell'esercizio 2 con caching Redis:

- Configurare una connessione Redis con `ioredis` e health check periodico
- Implementare le seguenti strategie di caching:
  - **Cache-aside** per `findPostBySlug`: verificare Redis prima del database, memorizzare con TTL 5 minuti, invalidare su update/delete
  - **Write-through** per `viewCount`: incrementare atomicamente in Redis con `INCR`, sincronizzare periodicamente su PostgreSQL con un job schedulato
  - **Cache warming** all'avvio: pre-popolare la cache con i 20 post più recenti
- Strutturare le chiavi Redis con namespace: `blog:post:slug:{slug}`, `blog:post:views:{id}`, `blog:posts:page:{page}:tag:{tag}`
- Invalidazione a cascata: quando un post viene aggiornato, invalidare sia la chiave del singolo post sia le chiavi di lista che potrebbero contenerlo
- Aggiungere un endpoint `/cache/stats` che restituisca hit rate, miss rate, dimensione della cache e memoria utilizzata
- Scrivere test che verifichino: hit della cache (la query al DB non viene eseguita), miss della cache (fallback al DB), invalidazione corretta dopo un update

### Esercizio 4 — Ottimizzazione query con EXPLAIN e indici

**Obiettivo:** Diagnosticare e risolvere problemi di performance su query reali.

Partendo da un database PostgreSQL con dati realistici:

- Creare una tabella `orders` con almeno 500.000 righe generate tramite `generate_series` e `random()`, con colonne: `id`, `customer_id` (FK), `product_id` (FK), `quantity`, `total_price`, `status` (enum), `created_at`, `shipped_at` (nullable)
- Creare le tabelle correlate `customers` (10.000 righe) e `products` (1.000 righe) con dati realistici
- Scrivere e ottimizzare le seguenti query:
  - Top 10 clienti per fatturato totale nell'ultimo trimestre (JOIN + aggregazione + filtro data)
  - Prodotti mai ordinati (LEFT JOIN + IS NULL o NOT EXISTS)
  - Revenue giornaliero degli ultimi 30 giorni con media mobile su 7 giorni (window function)
  - Ordini con dettaglio cliente e prodotto, filtrati per stato e range di date (multi-JOIN con filtri compositi)
- Per ogni query: eseguire `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` prima e dopo l'aggiunta degli indici
- Documentare in un file Markdown: il piano di esecuzione originale, gli indici creati, il piano dopo l'ottimizzazione, il miglioramento in termini di tempo e I/O
- Identificare almeno una query dove un indice parziale (`CREATE INDEX ... WHERE status = 'shipped'`) è più efficiente di un indice completo

### Esercizio 5 — Migrazione live di schema senza downtime

**Obiettivo:** Eseguire una migrazione di schema complessa su un database attivo senza interrompere il servizio.

Simulare una migrazione zero-downtime su PostgreSQL:

- Scenario: rinominare la colonna `email` in `email_address` nella tabella `users` e spostare il campo `address` (stringa) in una tabella separata `addresses` (normalizzazione)
- Implementare la migrazione in 4 fasi:
  1. **Expand** — aggiungere la nuova colonna `email_address` e la tabella `addresses`, creare un trigger che sincronizzi i valori tra `email` e `email_address` in entrambe le direzioni
  2. **Migrate** — backfill batch dei dati esistenti (`UPDATE ... SET email_address = email WHERE email_address IS NULL LIMIT 1000`) con sleep tra i batch per non saturare il database
  3. **Contract (codice)** — aggiornare l'applicazione per leggere/scrivere solo `email_address` e dalla tabella `addresses`
  4. **Contract (schema)** — rimuovere la colonna `email`, il trigger e i vincoli obsoleti
- Ogni fase deve essere una migrazione separata e reversibile
- Scrivere un test che simuli richieste concorrenti durante la migrazione e verifichi che nessuna query fallisca
- Documentare i comandi di rollback per ogni fase

---

## Letture e Riferimenti

### Documentazione ufficiale

- **PostgreSQL Documentation** — documentazione completa di PostgreSQL 16, inclusi SQL avanzato, indici, JSONB e RLS. https://www.postgresql.org/docs/16/ (consultato: 2026-05-24)
- **Prisma Documentation** — guida ufficiale dell'ORM Prisma per schema modeling, migrazioni e client API. https://www.prisma.io/docs (consultato: 2026-05-24)
- **Drizzle ORM Documentation** — ORM type-safe alternativo con approccio SQL-first. https://orm.drizzle.team/docs/overview (consultato: 2026-05-24)
- **Redis Documentation** — comandi, strutture dati, persistence e clustering di Redis 7.x. https://redis.io/docs/ (consultato: 2026-05-24)
- **MongoDB Manual** — documentazione ufficiale per il database document-oriented. https://www.mongodb.com/docs/manual/ (consultato: 2026-05-24)
- **Use The Index, Luke** — guida pratica all'indicizzazione SQL indipendente dal database, con visualizzazioni del piano di esecuzione. https://use-the-index-luke.com/ (consultato: 2026-05-24)

### Libri e approfondimenti

- Kleppmann, Martin, *Designing Data-Intensive Applications*, O'Reilly, 2017.
- Winand, Markus, *SQL Performance Explained*, self-published, 2012.
- Petrov, Alex, *Database Internals*, O'Reilly, 2019.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [10 — Node.js](10-nodejs.md) | Prerequisito: driver database e ORM eseguiti nel runtime Node.js con connection pooling |
| [06 — TypeScript](06-typescript.md) | Prerequisito: tipizzazione statica utilizzata da Prisma e Drizzle per query type-safe |
| [11 — API Design](11-api-design.md) | Le API espongono i dati gestiti dal database; il design degli endpoint riflette il data model |
| [13 — Autenticazione e Autorizzazione](13-autenticazione-autorizzazione.md) | Sessioni, token e permessi vengono persistiti e verificati a livello database |
| [14 — Sicurezza Web](14-sicurezza-web.md) | SQL injection, input sanitization e RLS come contromisure di sicurezza a livello dati |
| [17 — Performance Web](17-performance-web.md) | Ottimizzazione query, caching e connection pooling come fattori critici di performance |

---

## Glossario

| Termine | Definizione |
|---|---|
| **ORM** | Object-Relational Mapping: libreria che mappa tabelle del database a oggetti del linguaggio di programmazione. |
| **Migrazione** | Script versionato che modifica lo schema del database in modo controllato e reversibile. |
| **Connection Pooling** | Tecnica che mantiene un insieme di connessioni database riutilizzabili per evitare il costo di apertura/chiusura ripetuta. |
| **Indice** | Struttura dati ausiliaria (tipicamente B-tree) che accelera le ricerche su una o più colonne a costo di spazio e scrittura aggiuntivi. |
| **Normalizzazione** | Processo di organizzazione dei dati per ridurre la ridondanza, suddividendo in tabelle con dipendenze funzionali ben definite. |
| **Denormalizzazione** | Introduzione deliberata di ridondanza nello schema per migliorare le prestazioni di lettura di query specifiche. |
| **Transazione ACID** | Operazione atomica, consistente, isolata e durabile che garantisce l'integrità dei dati anche in caso di errore. |
| **JSONB** | Tipo di dato PostgreSQL per archiviare JSON in formato binario indicizzabile, con operatori di query dedicati. |
| **RLS** | Row-Level Security: meccanismo PostgreSQL che filtra le righe visibili in base all'utente connesso. |
| **TTL** | Time To Live: durata dopo la quale un dato nella cache viene automaticamente invalidato. |
| **Cache-aside** | Pattern di caching in cui l'applicazione verifica la cache prima del database e la popola al miss. |
| **EXPLAIN** | Comando SQL che mostra il piano di esecuzione di una query, fondamentale per la diagnosi delle prestazioni. |
| **Replication Lag** | Ritardo nella propagazione dei dati dal database primario alle repliche di lettura. |
| **Backfill** | Processo di popolamento retroattivo di una nuova colonna o tabella con dati derivati da strutture esistenti. |