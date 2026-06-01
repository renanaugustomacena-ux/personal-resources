# SQL DDL: Data Definition Language

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
1. DDL: Gestione della Struttura del Database
2. CREATE: Creazione di Oggetti
3. ALTER: Modifica della Struttura
4. DROP: Rimozione di Oggetti
5. Gestione delle Viste
6. Gestione delle Sequenze
7. Schemi e Namespace
8. Tipi di Dato Personalizzati
9. Constraint Avanzati
10. Best Practices per Schema Design

---

## 1. DDL: Gestione della Struttura del Database

### 1.1 Cos'è il DDL

Il **Data Definition Language (DDL)** è la parte di SQL che definisce e modifica la struttura degli oggetti del database. A differenza del DML che manipola i dati, il DDL opera sugli oggetti che contengono i dati: tabelle, indici, viste, schemi, tipi.

Le operazioni DDL fondamentali sono:
- **CREATE**: Crea nuovi oggetti
- **ALTER**: Modifica oggetti esistenti
- **DROP**: Rimuove oggetti

Il DDL è solitamente **implicito commit**: ogni statement DDL automaticamente committa la transazione corrente. Questo è diverso dal DML dove è necessario un COMMIT esplicito.

### 1.2 Catalogo del Database

Il **catalogo** (o system catalog) è l'insieme dei metadati che descrivono tutti gli oggetti del database. È esso stesso costituito da tabelle di sistema.

Le **tabelle del catalogo** includono:
- `information_schema.tables`: tutte le tabelle
- `information_schema.columns`: tutte le colonne
- `information_schema.constraints`: tutti i vincoli
- `information_schema.key_column_usage`: chiavi

### 1.3 Transazioni DDL

Le **transazioni DDL** hanno semantica diversa dal DML:

```sql
BEGIN;
CREATE TABLE t1 (...);
ALTER TABLE t1 ADD COLUMN ...;
DROP TABLE t2;
COMMIT;
```

In PostgreSQL, il DDL è transazionale (può essere rollbackato). In Oracle/MySQL, ogni DDL è autocommit.

---

## 2. CREATE: Creazione di Oggetti

### 2.1 CREATE TABLE

La **CREATE TABLE** è l'operazione DDL più fondamentale:

```sql
CREATE TABLE nome_tabella (
    nome_colonna tipo_dato [vincoli],
    ...
    [vincoli_tabella]
);
```

**Esempio completo:**
```sql
CREATE TABLE utenti (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT email_check CHECK (email LIKE '%@%.%')
);
```

### 2.2 CREATE TABLE AS

La **CREATE TABLE AS (CTAS)** crea una tabella dal risultato di una query:

```sql
CREATE TABLE summary AS
SELECT categoria, COUNT(*) as num, AVG(prezzo) as avg_prezzo
FROM prodotti
GROUP BY categoria;
```

Questo è utile per:
- Tabelle di aggregazione
- Backup di tabelle
- Test con dati campione

### 2.3 CREATE INDEX

Gli **indici** migliorano le prestazioni delle query:

```sql
-- Indice semplice
CREATE INDEX idx_utenti_email ON utenti(email);

-- Indice composito
CREATE INDEX idx_ordini_cliente_data ON ordini(cliente_id, created_at DESC);

-- Indice unico
CREATE UNIQUE INDEX idx_prodotti_sku ON prodotti(sku);

-- Indice partial (PostgreSQL)
CREATE INDEX idx_attivi ON prodotti(id) WHERE status = 'active';
```

**Tipi di indice:**
- **B-Tree**: Default, per equality e range
- **Hash**: Solo equality
- **GIN**: inverted index per full-text, array, JSON
- **GiST**: strutture geometriche
- **BRIN**: block range index per dati sequenziali

### 2.4 CREATE VIEW

Le **viste** sono query salvate:

```sql
CREATE VIEW ordini_con_clienti AS
SELECT o.id, o.data, c.nome as cliente, o.totale
FROM ordini o
JOIN clienti c ON o.cliente_id = c.id;

CREATE VIEW prodotti_sotto_scorta AS
SELECT * FROM prodotti WHERE stock < reorder_point;
```

### 2.5 CREATE SCHEMA

Gli **schemi** organizzano gli oggetti:

```sql
CREATE SCHEMA vendite;
CREATE SCHema appena_vendite;

-- Creare oggetti in uno schema specifico
CREATE TABLE vendite.ordini (...);
```

---

## 3. ALTER: Modifica della Struttura

### 3.1 ALTER TABLE - Aggiungere Colonne

L'**aggiunta di colonne** è un'operazione comune:

```sql
ALTER TABLE utenti ADD COLUMN telefono VARCHAR(20);
ALTER TABLE utenti ADD COLUMN is_active BOOLEAN DEFAULT true;
```

Le colonne vengono aggiunte alla fine della tabella.

### 3.2 ALTER TABLE - Modificare Colonne

La **modifica delle colonne**:

```sql
-- Cambiare tipo (solo se compatibile)
ALTER TABLE utenti ALTER COLUMN nome TYPE VARCHAR(200);

-- Aggiungere/Rimuovere DEFAULT
ALTER TABLE utenti ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE utenti ALTER COLUMN created_at DROP DEFAULT;

-- Impostare/Rimuovere NOT NULL
ALTER TABLE utenti ALTER COLUMN email SET NOT NULL;
ALTER TABLE utenti ALTER COLUMN email DROP NOT NULL;
```

### 3.3 ALTER TABLE - Rinominare e Rimuovere

**Rinominare** e **rimuovere** colonne:

```sql
-- Rinominare
ALTER TABLE utenti RENAME COLUMN telefono TO telefono_cellulare;

-- Rimuovere (può fallire se ci sono dipendenze)
ALTER TABLE utenti DROP COLUMN telefono;
ALTER TABLE utenti DROP COLUMN telefono CASCADE; -- Forza rimozione
```

### 3.4 ALTER TABLE - Vincoli

La **gestione dei vincoli**:

```sql
-- Aggiungere vincolo
ALTER TABLE ordini ADD CONSTRAINT tot_positivo CHECK (totale >= 0);

-- Rimuovere vincolo
ALTER TABLE ordini DROP CONSTRAINT tot_positivo;

-- Rinominare vincolo
ALTER TABLE ordini RENAME CONSTRAINT tot_positivo TO totale_positivo;

-- Abilitare/Disabilitare vincolo
ALTER TABLE ordini ALTER CONSTRAINT tot_positivo DISABLE;
```

### 3.5 ALTER TABLE - Indici

La **gestione degli indici**:

```sql
-- Rinominare indice
ALTER INDEX idx_vecchio RENAME TO idx_nuovo;

-- Indici concurrently (PostgreSQL)
CREATE INDEX CONCURRENTLY idx_nuovo ON tabella(col);
DROP INDEX CONCURRENTLY idx_vecchio;
```

---

## 4. DROP: Rimuovere Oggetti

### 4.1 DROP TABLE

La **rimozione delle tabelle**:

```sql
DROP TABLE tabella; -- Fallisce se ci sono dipendenze
DROP TABLE tabella CASCADE; -- Rimuove anche le dipendenze
DROP TABLE IF EXISTS tabella; -- Non genera errore se non esiste
```

**ATTENZIONE**: CASCADE rimuove automaticamente tutte le viste, vincoli, trigger che referenziano la tabella!

### 4.2 DROP INDEX

La **rimozione degli indici**:

```sql
DROP INDEX idx_nome;
DROP INDEX IF EXISTS idx_nome; -- Sicuro
```

Gli indici possono essere ricreati senza perdere dati.

### 4.3 DROP VIEW

Le **viste** possono essere rimosse:

```sql
DROP VIEW nome_vista;
DROP VIEW IF EXISTS nome_vista;
```

Le viste sono indipendenti dalle tabelle sottostanti.

### 4.4 DROP SCHEMA

Gli **schemi** possono essere rimossi:

```sql
DROP SCHEMA nome; -- Fallisce se non vuoto
DROP SCHEMA nome CASCADE; -- Rimuove tutto il contenuto
```

### 4.5 CASCADE e RESTRICT

Le **opzioni CASCADE** e **RESTRICT** controllano la propagazione:

- **CASCADE**: rimuove automaticamente gli oggetti dipendenti
- **RESTRICT** (default): impedisce la rimozione se ci sono dipendenze

---

## 5. Gestione delle Viste

### 5.1 Viste e Sicurezza

Le **viste** forniscono sicurezza:

```sql
-- Vista che nasconde colonne sensibili
CREATE VIEW dati_pubblici AS
SELECT id, nome, email
FROM utenti;

-- Vista per ruolo
CREATE VIEW ordini_operatori AS
SELECT * FROM ordini WHERE status = 'pending';
```

Le viste possono limitare l'accesso a specifiche righe e colonne.

### 5.2 Viste Updatable

Le **viste updatable** permettono INSERT/UPDATE/DELETE:

```sql
CREATE VIEW ordini_semplice AS
SELECT id, cliente_id, totale FROM ordini WHERE status = 'open';

-- È possibile fare:
INSERT INTO ordini_semplice VALUES (100, 1, 500);
-- Si applica automaticamente a ordini WHERE status = 'open'
```

### 5.3 Viste con CHECK OPTION

La **CHECK OPTION** valida le modifiche:

```sql
CREATE VIEW ordini_2024 AS
SELECT * FROM ordini WHERE data >= '2024-01-01'
WITH CHECK OPTION;

-- INSERT in ordini_2024 fallisce se la data non è nel 2024
```

### 5.4 Viste Materializzate

Le **viste materializzate** memorizzano fisicamente il risultato:

```sql
CREATE MATERIALIZED VIEW stats_mensili AS
SELECT DATE_TRUNC('month', data) as mese, SUM(totale) as somma
FROM ordini
GROUP BY DATE_TRUNC('month', data);

-- Refresh
REFRESH MATERIALIZED VIEW stats_mensili;
```

---

## 6. Gestione delle Sequenze

### 6.1 CREATE SEQUENCE

Le **sequenze** generano numeri sequenziali:

```sql
CREATE SEQUENCE utenti_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 999999999
    CYCLE;
```

### 6.2 Utilizzo delle Sequenze

Le **sequenze** si usano con nextval:

```sql
INSERT INTO utenti (id, nome) VALUES (nextval('utenti_id_seq'), 'Mario');
```

Le sequenze sono spesso usate per le chiavi surrogate.

### 6.3 ALTER e DROP SEQUENCE

Le **sequenze** possono essere modificate:

```sql
ALTER SEQUENCE utenti_id_seq RESTART WITH 1000;
DROP SEQUENCE utenti_id_seq;
```

---

## 7. Schemi e Namespace

### 7.1 Schema Default e Public

Ogni database ha uno **schema public** (o default):

```sql
-- Creare nel schema public (default)
CREATE TABLE tabella (...);

-- In PostgreSQL, il default è 'public'
```

### 7.2 Ricerca degli Schemi

Il **search_path** determina la risoluzione dei nomi:

```sql
SHOW search_path; -- PostgreSQL

SET search_path TO vendite, pubblico, '$user';
```

Il search path è una lista di schemi dove cercare gli oggetti.

### 7.3 Autorizzazioni sugli Schemi

Gli **schemi** hanno autorizzazioni:

```sql
GRANT USAGE ON SCHEMA vendite TO ruolo_vendite;
GRANT CREATE ON SCHEMA vendite TO ruolo_vendite;
```

---

## 8. Tipi di Dato Personalizzati

### 8.1 CREATE TYPE

I **tipi personalizzati** estendono i tipi base:

```sql
-- Tipo enumerato
CREATE TYPE stato_order AS ENUM ('pending', 'processing', 'shipped', 'delivered');

-- Tipo composito
CREATE TYPE indirizzo AS (
    via VARCHAR(200),
    citta VARCHAR(100),
    cap VARCHAR(10),
    nazione VARCHAR(2)
);
```

### 8.2 Utilizzo dei Tipi Personalizzati

I **tipi** si usano nelle tabelle:

```sql
CREATE TABLE clienti (
    id SERIAL,
    nome VARCHAR(100),
    indirizzo indirizzo,
    stato stato_order DEFAULT 'pending'
);
```

### 8.3 DOMAIN

I **domain** sono tipi con vincoli:

```sql
CREATE DOMAIN email_type AS VARCHAR(255)
    CHECK (VALUE ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

CREATE TABLE utenti (
    email email_type
);
```

---

## 9. Constraint Avanzati

### 9.1 Exclusion Constraints

I **constraint di esclusione** (PostgreSQL) prevengono sovrapposizioni:

```sql
CREATE TABLE appuntamenti (
    id SERIAL,
    medico_id INT,
    orario TIMESTAMP,
    durata INTERVAL,
    EXCLUDE USING gist (
        medico_id WITH =,
        orario WITH &&
    )
);
```

Questo impedisce doppi appuntamenti per lo stesso medico.

### 9.2 Unique con NULL

Le **chiavi uniche** con NULL hanno semantica specifica:

```sql
-- UNIQUE permette un solo NULL
-- In PostgreSQL: multiple NULL sono permesse
-- In SQL standard: un solo NULL
```

### 9.3 Constraint Deferrable

I **constraint differibili** possono essere rinviati:

```sql
ALTER TABLE ordini 
ADD CONSTRAINT fk_cliente FOREIGN KEY (cliente_id) REFERENCES clienti(id)
DEFERRABLE INITIALLY DEFERRED;
```

Questo valuta il vincolo alla fine della transazione.

### 9.4 Partial Unique Index

Gli **indici unici parziali** creano unicità condizionale:

```sql
-- Solo ordini attivi hanno order_number unico
CREATE UNIQUE INDEX idx_ordini_numero ON ordini(order_number) 
WHERE status != 'cancelled';
```

### 9.5 Column-Level Constraints

I **vincoli a livello di colonna** sono definiti con la colonna:

```sql
CREATE TABLE (
    id INT PRIMARY KEY, -- Vincolo inline
    nome VARCHAR(100) NOT NULL
);
```

---

## 10. Best Practices per Schema Design

### 10.1 Naming Conventions

Le **convenzioni di nome** dovrebbero essere:
- Consistenti (snake_case, camelCase)
- Descrittive
- Non troppo lunghe
- Evitare parole riservate

### 10.2 Primary Key Strategy

Le **chiavi primarie** dovrebbero:
- Essere stabili (mai cambiate)
- Essere corte per indici efficienti
- Essere uniche
- Considerare surrogate keys per tabelle transazionali

### 10.3 Foreign Key Design

Le **chiavi esterne** dovrebbero:
- Aver sempre indici (per JOIN performance)
- Usare nomi descrittivi
- Definire azioni ON DELETE/UPDATE appropriate

### 10.4 Default Values

I **valori di default** semplificano INSERT:
- DEFAULT CURRENT_TIMESTAMP per timestamps
- DEFAULT true/false per booleani
- Evitare default complessi

### 10.5 Documentazione dello Schema

La **documentazione** è essenziale:
- Commenti su tabelle e colonne
- Diagrammi ER
- Change log delle migrazioni

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*