# Normalizzazione: Teoria e Pratica

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
1. Fondamenti della Normalizzazione
2. Prima Forma Normale (1NF)
3. Seconda Forma Normale (2NF)
4. Terza Forma Normale (3NF)
5. Forma Normale di Boyce-Codd (BCNF)
6. Forme Normali Avanzate (4NF, 5NF)
7. Denormalizzazione Consapevole
8. Strumenti e Tecniche di Normalizzazione
9. Anti-Patterns nella Normalizzazione
10. Case Study: Normalizzazione Completa

---

## 1. Fondamenti della Normalizzazione

### 1.1 Perché Normalizzare

La **normalizzazione** organizza le tabelle per minimizzare la ridondanza e prevenire anomalie:

**Anomalie di inserimento**: Dati duplicati, impossibilità di inserire dati incompleti

**Anomalie di aggiornamento**: Update su righe multiple per lo stesso dato

**Anomalie di cancellazione**: Perdita di dati correlati quando si cancella

### 1.2 Dipendenze Funzionali

Le **dipendenze funzionali** (FD) sono il fondamento della normalizzazione:

X → Y significa: ogni valore di X determina univocamente Y

**Esempio**: Se id è la chiave, id → (nome, email, telefono)

### 1.3 Chiavi e Superchiavi

Le **chiavi** identificano univocamente le tuple:

- **Chiave candidato**: insieme minimo di attributi che identificano univocamente
- **Chiave primaria**: chiave candidato scelta
- **Superchiave**: insieme di attributi che contiene una chiave

### 1.4 Decomposizione delle Relazioni

La **decomposizione** divide una relazione in relazioni più piccole:

R(A, B, C) può essere decomposta in R1(A, B) e R2(B, C)

La decomposizione deve essere:
- **Senza perdita (lossless)**: R = R1 ⋈ R2
- **Preservare le dipendenze**: le FD originali sono mantenute

---

## 2. Prima Forma Normale (1NF)

### 2.1 Requisiti della 1NF

Una relazione è in **1NF** se:
- Ha una chiave primaria
- Tutti gli attributi contengono solo valori atomici
- Non ci sono gruppi ripetuti

### 2.2 Eliminazione dei Gruppi Ripetuti

I **gruppi ripetuti** sono eliminati creando nuove tabelle:

**Prima**:
| ID | Telefono1 | Telefono2 | Telefono3 |
|----|-----------|-----------|-----------|

**Dopo** (1NF):
| ID | telefono |
|----|----------|
| 1 | 333... |
| 1 | 444... |

### 2.3 Valori Multi-Valore

I **valori multi-valore** richiedono strutture separate:

```sql
-- Non normalizzato
CREATE TABLE clienti (
    id INT PRIMARY KEY,
    nome VARCHAR(100),
    telefoni VARCHAR(500) -- "333111,444222"
);

-- Normalizzato (1NF)
CREATE TABLE clienti (
    id INT PRIMARY KEY,
    nome VARCHAR(100)
);

CREATE TABLE telefoni (
    cliente_id INT,
    telefono VARCHAR(20),
    PRIMARY KEY (cliente_id, telefono)
);
```

---

## 3. Seconda Forma Normale (2NF)

### 3.1 Requisiti della 2NF

Una relazione è in **2NF** se:
- È in 1NF
- Ogni attributo non-chiave dipende completamente dalla chiave primaria

La 2NF si applica solo a **chiavi composite**!

### 3.2 Dipendenze Parziali

Le **dipendenze parziali** violano la 2NF:

| ordine_id | prodotto_id | cliente_nome | quantità |
|-----------|-------------|--------------|----------|
| 1 | 100 | Mario | 2 |

La chiave è (ordine_id, prodgetto_id).
cliente_nome dipende solo da ordine_id → dipendenza parziale.

### 3.3 Decomposizione in 2NF

Per eliminare le dipendenze parziali:

**Prima**:
OrdiniDettagli(ordine_id, prodotto_id, cliente_nome, quantità)

**Dopo**:
- Ordini(ordine_id, cliente_nome)
- OrdiniDettagli(ordine_id, prodotto_id, quantità)

### 3.4 Esempio Pratico

```sql
-- Non in 2NF
CREATE TABLE ordini_prodotti (
    ordine_id INT,
    prodotto_id INT,
    cliente_nome VARCHAR(100), -- Dipende solo da ordine_id!
    quantita INT,
    PRIMARY KEY (ordine_id, prodotto_id)
);

-- In 2NF
CREATE TABLE ordini (
    ordine_id INT PRIMARY KEY,
    cliente_nome VARCHAR(100)
);

CREATE TABLE ordini_prodotti (
    ordine_id INT REFERENCES ordini(ordine_id),
    prodotto_id INT,
    quantita INT,
    PRIMARY KEY (ordine_id, prodotto_id)
);
```

---

## 4. Terza Forma Normale (3NF)

### 4.1 Requisiti della 3NF

Una relazione è in **3NF** se:
- È in 2NF
- Non ci sono dipendenze transitive

Una dipendenza transitiva: X → Y → Z (X determina Y, Y determina Z)

### 4.2 Eliminazione delle Dipendenze Transitive

**Esempio**: Dipartimento → Manager → Stipendio

dipartimento_id → manager_id → stipendio_manager

Dipartimento(dipartimento_id, nome, manager_id, stipendio_manager)

### 4.3 Algoritmo di Decomposizione 3NF

L'algoritmo produce una decomposizione che preserva le dipendenze:

1. Trova la cover minima delle FD
2. Per ogni FD X → Y, crea una relazione (X ∪ Y)
3. Se nessuna relazione contiene una chiave di R, aggiungi una

### 4.4 Esempio Completo 3NF

```sql
-- Non in 3NF: dipendenza transitiva
-- Dipartimento → Manager → Stipendio
CREATE TABLE dipartimenti (
    id INT PRIMARY KEY,
    nome VARCHAR(100),
    manager_id INT,
    stipendio_manager DECIMAL(10,2) -- Transitivo!
);

-- In 3NF
CREATE TABLE dipartimenti (
    id INT PRIMARY KEY,
    nome VARCHAR(100),
    manager_id INT REFERENCES impiegati(id)
);

CREATE TABLE impiegati (
    id INT PRIMARY KEY,
    nome VARCHAR(100),
    ruolo VARCHAR(50),
    stipendio DECIMAL(10,2)
);
```

---

## 5. Forma Normale di Boyce-Codd (BCNF)

### 5.1 Requisiti della BCNF

Una relazione è in **BCNF** se:
- È in 3NF
- Ogni determinante è una superchiave

Un determinante è un attributo (o insieme) che determina altri attributi.

### 5.2 Quando BCNF È Necessaria

La BCNF corregge situazioni dove la 3NF non è sufficiente:

**Esempio**: Prenotazioni(aula, corso, insegnante)

- Un insegnante può insegnare un solo corso
- Un corso può essere in una sola aula
- FD: insegnante → corso, corso → aula

La chiave è (aula, corso) ma (insegnante → corso) viola BCNF perché insegnante non è superchiave.

### 5.3 Decomposizione in BCNF

```sql
-- Non in BCNF
CREATE TABLE prenotazioni (
    aula VARCHAR(20),
    corso VARCHAR(50),
    insegnante VARCHAR(100),
    PRIMARY KEY (aula, corso)
);

-- In BCNF
CREATE TABLE corsi (
    corso VARCHAR(50) PRIMARY KEY,
    insegnante VARCHAR(100) -- Insegnante determina corso
);

CREATE TABLE prenotazioni (
    aula VARCHAR(20),
    corso VARCHAR(50) REFERENCES corsi(corso),
    PRIMARY KEY (aula, corso)
);
```

### 5.4 Limitazioni della BCNF

La BCNF può:
- Non preservare tutte le dipendenze
- Aumentare il numero di tabelle

Non sempre è necessaria o desiderabile.

---

## 6. Forme Normali Avanzate (4NF, 5NF)

### 6.1 Quarta Forma Normale (4NF)

La **4NF** elimina le dipendenze multi-valore:

R è in 4NF se è in BCNF e non ci sono dipendenze multi-valore non banali.

**Esempio**: Corsi(insegnante, lingua, livello)

Un insegnante può insegnare multiple lingue a multiple livelli.
FD non banali: insegnante →→ lingua (multi-valore), insegnante →→ livello (multi-valore)

### 6.2 Quinta Forma Normale (5NF)

La **5NF** (PJ/NF) elimina le join anomalies:

Una relazione è in 5NF se non può essere decomposta senza perdita e senza preservare le dipendenze.

Utile per tabelle con molte chiavi e relazioni complesse.

### 6.3 Domain-Key Normal Form (DK/NF)

La **DK/NF** è la forma normale ideale:

Ogni vincolo è una conseguenza logica delle chiavi e dei domini.

Difficile da raggiungere; raramente necessaria in pratica.

### 6.4 Tabella delle Forme Normali

| Forma Normale | Requisiti | Quando Applicare |
|---------------|-----------|------------------|
| 1NF | Valori atomici | Sempre |
| 2NF | 1NF + dipendenze complete dalla PK | Tabelle con chiavi composite |
| 3NF | 2NF + no dipendenze transitive | Generalmente sufficiente |
| BCNF | 3NF + ogni determinante è superchiave | Quando 3NF produce anomalie |
| 4NF | BCNF + no dipendenze multi-valore | Dati multi-valore problematici |
| 5NF | 4NF + non decomponibile | Relazioni molte-a-molte complesse |

---

## 7. Denormalizzazione Consapevole

### 7.1 Quando Denormalizzare

La **denormalizzazione** è appropriata quando:
- Le prestazioni di lettura sono critiche
- Le query sono prevedibili
- La ridondanza è accettabile e gestibile

### 7.2 Tipi di Denormalizzazione

La denormalizzazione può essere:
- **Joins pre-calcolati**: Viste materializzate
- **Colonne duplicate**: Cache denormalizzate
- **Tabelle di aggregazione**: Summary tables
- **Gruppi ripetuti**: Denormalizzazione intenzionale

### 7.3 Star Schema

Lo **star schema** è una denormalizzazione controllata:

- **Fact table**: Dati transazionali, foreign keys
- **Dimension tables**: Attributi descrittivi, denormalizzati

Optimizzato per query analitiche (OLAP).

### 7.4 Denormalizzazione con Trigger

I **trigger** mantengono la consistenza:

```sql
CREATE TRIGGER update_order_totals
AFTER UPDATE ON ordini_dettagli
FOR EACH ROW
EXECUTE FUNCTION update_order_total();
```

### 7.5 Rischi della Denormalizzazione

I **rischi** includono:
- Inconsistenza dei dati
- Update complessi
- Maggiore spazio di storage

---

## 8. Strumenti e Tecniche di Normalizzazione

### 8.1 Analisi delle Dipendenze

Per normalizzare, prima analizzare le **dipendenze funzionali**:

```sql
-- Identificare FD
-- Determinare chiavi
-- Verificare forme normali
```

### 8.2 Database Modeling Tools

Gli **strumenti** per la modellazione:
- DBeaver
- DbVisualizer
- pgModeler
- MySQL Workbench

### 8.3 Reverse Engineering

Il **reverse engineering** analizza schema esistenti:

```sql
-- PostgreSQL
SELECT table_name, column_name 
FROM information_schema.columns
WHERE table_schema = 'public';
```

### 8.4 Script di Normalizzazione

La **normalizzazione** può essere scriptata:

```sql
-- Creare nuova struttura normalizzata
CREATE TABLE ...;

-- Copiare dati dalla vecchia tabella
INSERT INTO ... SELECT ...;

-- Verificare e rimuovere tabella vecchia
```

### 8.5 Validazione

La **validazione** verifica la normalizzazione:
- Verificare che le chiavi funzionino
- Testare i vincoli
- Verificare l'assenza di anomalie

---

## 9. Anti-Patterns nella Normalizzazione

### 9.1 Over-Normalization

L'**over-normalizzazione** crea troppe tabelle:
- Query con troppi join
- Performance degradate
- Complessità eccessiva

### 9.2 Under-Normalization

La **under-normalizzazione** ha ridondanza eccessiva:
- Anomalie di aggiornamento
- Inconsistenza dei dati
- Storage sprecato

### 9.3 Normalizzazione Prematura

La **normalizzazione prematura** anticipa requisiti non necessari:
- Modello troppo complesso
- Over-engineering
- Difficoltà di evoluzione

### 9.4 Ignorare le Performance

Le **performance** non dovrebbero essere ignorate:
- Profilare le query prima di denormalizzare
- Considerare il carico di lavoro reale
- Bilanciare normalizzazione con performance

### 9.5 Non Considerare i Dati di Accesso

Le **modalità di accesso** influenzano la normalizzazione:
- Pattern di lettura
- Pattern di scrittura
- Frequenza delle operazioni

---

## 10. Case Study: Normalizzazione Completa

### 10.1 Scenario Iniziale

Supponiamo un foglio Excel non normalizzato:

| OrderID | Customer | Product | Qty | Price | Date | Category |
|---------|----------|---------|-----|-------|------|----------|
| 1 | Mario | Laptop | 1 | 999 | 2024-01-15 | Electronics |
| 1 | Mario | Mouse | 2 | 29 | 2024-01-15 | Electronics |
| 2 | Luigi | Keyboard | 1 | 89 | 2024-01-16 | Electronics |

### 10.2 Identificare le FD

Le dipendenze funzionali:
- OrderID → Customer, Date
- Product → Category, Price
- (OrderID, Product) → Qty

### 10.3 Prima Normalizzazione

**Problema**: OrderID 1 ha due prodotti → non atomico

**Soluzione**: Estrarre righe separate

### 10.4 Seconda Normalizzazione

**Problema**: Category e Price dipendono solo da Product, non da (OrderID, Product)

**Soluzione**: 
- Products(id, name, category, price)
- Orders(id, customer, date)
- OrderItems(order_id, product_id, qty)

### 10.5 Terza Normalizzazione

**Problema**: Category potrebbe dipendere da qualcos'altro?

In questo caso, è in 3NF.

### 10.6 Schema Finale

```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50)
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2),
    category_id INT REFERENCES categories(id)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    order_date DATE
);

CREATE TABLE order_items (
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT,
    PRIMARY KEY (order_id, product_id)
);
```

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*