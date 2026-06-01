# Modello Relazionale: Teoria e Implementazione

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
1. Fondamenti Teorici del Modello Relazionale
2. Entity-Relationship Model e Traduzione in Relazioni
3. Dipendenze Funzionali e Normalizzazione
4. Integrità del Dominio e Vincoli
5. Rappresentazione delle Relazioni in SQL
6. View e Viste Materializzate
7. Schema Design Best Practices
8. Schema Evolution e Migration
9. Design Pattern per Schema Relazionali
10. Case Study: Progettazione Schema E-commerce

---

## 1. Fondamenti Teorici del Modello Relazionale

### 1.1 Teoria degli Insiemi Applicata ai Database

Il modello relazionale è profondamente radicato nella teoria matematica degli insiemi. Comprendere questi fondamenti teorici è essenziale per progettare schema efficienti e per comprendere il comportamento dei database relazionali.

Una **relazione matematica** è un sottoinsieme del prodotto cartesiano di due o più insiemi (domini). Formalmente, se D1, D2, ..., Dn sono domini, una relazione R ⊆ D1 × D2 × ... × Dn è un sottoinsieme del prodotto cartesiano. Questa definizione garantisce che le relazioni siano insiemi, con le conseguenze che ne derivano: nessun ordinamento implicito, nessuna duplicazione, e appartenenza ben definita.

Il **prodotto cartesiano** D1 × D2 produce tutte le possibili combinazioni di elementi presi da D1 e D2. Se D1 = {A, B} e D2 = {1, 2, 3}, il prodotto cartesiano D1 × D2 = {(A,1), (A,2), (A,3), (B,1), (B,2), (B,3)}. Una relazione specifica quale di queste combinazioni sono valide.

I **domini** nel contesto dei database rappresentano l'insieme di valori ammissibili per un attributo. Un dominio può essere definito in modo primitivo (tipi come INTEGER, VARCHAR, DATE) o in modo enumerato (solo determinati valori). In SQL, i domini sono tipicamente mappati ai tipi di dati built-in, ma lo standard SQL permette la definizione di domini personalizzati con vincoli.

La **tuple** (n-upla) è un elemento specifico di una relazione, rappresentato come una sequenza ordinata di valori. In termini di database, ogni riga di una tabella è una tuple. Formalmente, una tuple t su attributi A = {A1, ..., An} è una funzione che assegna a ogni attributo Ai un valore del dominio corrispondente.

### 1.2 Algebra Relazionale in Profondità

L'**algebra relazionale** fornisce un insieme di operatori che, applicati a relazioni, producono nuove relazioni. Questi operatori formano la base teorica per l'ottimizzazione delle query e per la comprensione del comportamento di SQL.

L'operatore di **selezione** (σ, sigma) opera su una singola relazione e produce una relazione contenente solo le tuple che soddisfano un predicato. Formalmente: σ_predicato(R) = {t ∈ R | predicato(t) = true}. Il predicato può essere semplice (A = 'value') o composto con operatori booleani (AND, OR, NOT). La selezione riduce il numero di tuple (cardinalità) ma mantiene tutti gli attributi (grado inalterato).

L'operatore di **proiezione** (π, pi) opera su una singola relazione e produce una relazione contenente solo gli attributi specificati. Formalmente: π_A1,A2,...,Ak(R) = {t[A1, ..., Ak] | t ∈ R}. La proiezione riduce il grado della relazione. Poiché le relazioni sono insiemi, i duplicati vengono eliminati, potenzialmente riducendo la cardinalità.

L'operatore di **unione** (∪) combina due relazioni compatibili (stesso insieme di attributi) producendo una relazione che contiene tutte le tuple che appartengono ad almeno una delle due relazioni. Formalmente: R ∪ S = {t | t ∈ R ∨ t ∈ S}. L'unione rimuove i duplicati.

L'operatore di **differenza** (-) produce una relazione contenente le tuple della prima relazione che non appartengono alla seconda. Formalmente: R - S = {t ∈ R | t ∉ S}. Entrambe le relazioni devono essere compatibili.

L'operatore di **prodotto cartesiano** (×) combina due relazioni producendo tutte le possibili combinazioni di tuple. Formalmente: R × S = {(r, s) | r ∈ R ∧ s ∈ S}. Il risultato ha tutti gli attributi di entrambe le relazioni; attributi con lo stesso nome devono essere qualificati per evitare ambiguità.

L'operatore di **join** (⋈) combina il prodotto cartesiano con una selezione. Formalmente: R ⋈_cond S = σ_cond(R × S). Esistono varianti: equi-join (condizione di uguaglianza), natural join (join su attributi con lo stesso nome), outer join (include tuple senza match).

### 1.3 Proprietà Matematiche delle Relazioni

Le relazioni nel modello relazionale hanno proprietà matematiche specifiche che influenzano il design dello schema e il comportamento delle query.

L'**irriducibilità** (irreducibility) di una relazione significa che non è possibile decomporla ulteriormente senza perdere informazioni. Una relazione è irriducibile se ogni attributo è un sottoinsieme non vuoto del candidato key. Questo concetto è fondamentale per la normalizzazione.

La **chiusura** (closure) di un insieme di attributi rispetto a un insieme di dipendenze funzionali è l'insieme di tutti gli attributi determinati funzionalmente da quell'insieme. Si calcola iterativamente applicando le dipendenze funzionali. La chiusura è utilizzata per verificare le superchiavi e per determinare le dipendenze implicite.

La **cover minima** (minimal cover) di un insieme di dipendenze funzionali è l'insieme equivalente più piccolo dove ogni dipendenza ha un solo attributo a destra e nessun attributo può essere rimosso senza cambiare la chiusura. La cover minima è utile per decomporre le relazioni durante la normalizzazione.

La **decomposizione senza perdita** (lossless-join decomposition) è una proprietà di una decomposizione che garantisce che la ricostruzione della relazione originale attraverso join delle decomposizioni non produca tuple spurie. Formalmente: (R1 ⋈ R2) ⊇ R. La proprietà è verificata attraverso un algoritmo specifico che verifica le dipendenze funzionali.

### 1.4 Teoria della Normalizzazione

La **normalizzazione** è il processo di organizzazione dei dati in tabelle per minimizzare la ridondanza e prevenire anomalie. Si basa sulla decomposizione delle relazioni in forme normali progressivamente più restrittive.

La **prima forma normale (1NF)** richiede che tutti gli attributi contengano solo valori atomici, non multi-valori o gruppi ripetuti. Questo elimina le strutture nidificate all'interno delle tuple. Per ottenere 1NF, i gruppi ripetuti vengono estratti in tabelle separate con relazione uno-a-molti.

La **seconda forma normale (2NF)** richiede che la relazione sia in 1NF e che ogni attributo non-key sia completamente dipendente dalla chiave primaria (non da un sottoinsieme della chiave). Le dipendenze parziali vengono estratte in tabelle separate. Questa forma normale si applica solo a relazioni con chiavi composite.

La **terza forma normale (3NF)** richiede che la relazione sia in 2NF e che nessun attributo non-key sia transitivamente dipendente dalla chiave primaria. In altre parole, ogni dipendenza funzionale non deve avere attributi non-key a destra che non siano nella chiave. La 3NF è generalmente considerata sufficiente per la maggior parte delle applicazioni.

La **forma normale di Boyce-Codd (BCNF)** è una versione più rigorosa della 3NF dove ogni determinante deve essere una superchiave. Non tutte le decomposizioni che soddisfano la 3NF soddisfano la BCNF. La BCNF può portare a decomposizioni che non preservano tutte le dipendenze funzionali.

La **forma normale 4NF (4NF)** e la **forma normale 5NF (5NF)** affrontano rispettivamente le dipendenze multi-valore e le dipendenze di join, trattando relazioni con strutture più complesse.

---

## 2. Entity-Relationship Model e Traduzione in Relazioni

### 2.1 Componenti del Modello ER

Il **modello Entity-Relationship** (ER) è lo strumento standard per la progettazione concettuale dei database. Fornisce una rappresentazione grafica delle entità, dei loro attributi, e delle relazioni tra di esse.

Le **entità** rappresentano oggetti del mondo reale che esistono indipendentemente e hanno identità distinta. Le entità sono classificate in entità forti (con esistenza indipendente, hanno una chiave propria) e entità deboli (la cui esistenza dipende da un'altra entità, identificata dalla combinazione della propria chiave e della chiave dell'entità forte padre).

Gli **attributi** descrivono le proprietà delle entità. Gli attributi possono essere:
- **Semplici** vs **composti**: gli attributi composti sono formati da più attributi semplici (es. indirizzo = via + città + CAP)
- **Single-valued** vs **multi-valued**: gli attributi multi-valued possono avere più valori per una singola istanza (es. numeri di telefono)
- **Derivati**: calcolabili da altri attributi (es. età dalla data di nascita)
- **Key**: identificano univocamente ogni istanza dell'entità

Le **relazioni** (associazioni) rappresentano connessioni logiche tra entità. Una relazione può avere attributi propri. Le relazioni sono caratterizzate dalla **cardinalità**:
- **Uno-a-uno (1:1)**: ogni istanza di un'entità è associata al massimo a una istanza dell'altra entità
- **Uno-a-molti (1:N)**: un'istanza di un'entità può essere associata a molte istanze dell'altra, ma non viceversa
- **Molti-a-molti (M:N)**: ogni istanza di un'entità può essere associata a molte istanze dell'altra e viceversa

Le **partecipazioni** (total vs parziale) indicano se l'esistenza di un'entità dipende dalla sua partecipazione a una relazione. Una partecipazione totale (indicata con linea doppia nel diagramma ER) significa che ogni istanza dell'entità deve partecipare alla relazione.

### 2.2 Mapping da ER a Relazionale

La **traduzione** da diagramma ER a schema relazionale è un processo sistematico che converte il modello concettuale in uno schema implementabile.

Per le **entità forti**, ogni entità diventa una tabella. Gli attributi semplici e composti diventano colonne. Gli attributi multi-valued diventano tabelle separate con chiave esterna verso la tabella originale. L'identificatore dell'entità diventa la chiave primaria.

Per le **entità deboli**, si crea una tabella che include gli attributi dell'entità debole e la chiave primaria dell'entità forte padre come chiave esterna. La chiave primaria della tabella debole è la combinazione della chiave esterna e di un discriminatore (attributo che distingue le istanze deboli).

Per le **relazioni 1:1**, ci sono tre opzioni di traduzione:
- **Accorpamento**: gli attributi della relazione e la chiave esterna vengono aggiunti a una delle due tabelle
- ** Chiave esterna**: si sceglie una delle entità come "dominante" e si aggiunge la chiave dell'altra come chiave esterna
- **Tabella separata**: si crea una nuova tabella con le chiavi primarie di entrambe le entità e gli attributi della relazione

Per le **relazioni 1:N**, si aggiunge la chiave primaria dell'entità "uno" come chiave esterna nell'entità "molti". Gli attributi della relazione vengono aggiunti alla tabella del lato "molti".

Per le **relazioni M:N**, si crea una nuova tabella (tabella associativa o junction table) che include le chiavi primarie di entrambe le entità come chiave composita, più gli eventuali attributi della relazione.

### 2.3 Inheritance e Modellazione Avanzata

L'**ereditarietà** nel modello ER può essere tradotta in diversi modi nello schema relazionale:

L'opzione di **accorpamento** (single table inheritance) crea una sola tabella per tutte le entità nella gerarchia, includendo tutti gli attributi di tutte le entità. Una colonna discriminatore indica il tipo specifico. Questa opzione è semplice ma può portare a colonne nullable per gli attributi non applicabili a certi tipi.

L'opzione di **separazione** (concrete table inheritance) crea una tabella separata per ogni sottoclasse, includendo sia gli attributi ereditati che quelli specifici. Le tabelle delle sottoclassi hanno riferimento (FK) alla tabella padre per la chiave primaria. Questa opzione evita gli attributi nullable ma complica le query che devono accedere a tutti i tipi.

L'opzione di **classi astratte** (abstract table inheritance) non crea tabella per la classe padre ma solo per le sottoclassi concrete. Gli attributi comuni sono duplicati nelle tabelle delle sottoclassi. Questa opzione è utile quando la classe padre non ha istanze proprie.

Le **relazioni ricorsive** (self-referencing relationships) sono relazioni dove un'entità è in relazione con se stessa. Si implementano con una chiave esterna che referenzia la stessa tabella. Esempi includono strutture gerarchiche (manager-impiegato) e grafi (componenti che contengono altri componenti).

Le **relazioni n-arie** coinvolgono più di due entità. Si implementano come tabella separata con chiavi esterne verso tutte le entità partecipanti, più eventuali attributi della relazione.

### 2.4 Best Practices nel Design ER

La **progettazione ER efficace** richiede considerazioni che vanno oltre la semplice traduzione in schema relazionale.

La **naming convention** dovrebbe essere consistente: nomi in singolare per le tabelle, nomi in camelCase o snake_case per le colonne, nomi descrittivi che riflettano il dominio. Evitare abbreviazioni non standardizzate.

La **chiave primaria** dovrebbe essere stabile (non cambiare nel tempo), breve (per performances), e unica. Le chiavi surrogate (ID auto-generati) sono spesso preferibili alle chiavi naturali che possono cambiare.

La **cardinalità appropriata** dovrebbe riflettere accuratamente le regole del business. Evitare over-generalizzazioni (assumere sempre M:N quando non necessario) o sotto-generalizzazioni (semplificare relazioni che dovrebbero essere M:N).

L'**astrazione appropriata** significa modellare ciò che è necessario, non tutto ciò che è possibile. Evitare di modellare ogni attributo possibile; concentrarsi su quelli rilevanti per i requisiti del sistema.

Il **balanced level of detail** significa evitare modelli troppo semplici (che perdono informazioni rilevanti) o troppo dettagliati (che complicano inutilmente). Il modello ER dovrebbe essere comprensibile e comunicare chiaramente la struttura del dominio.

---

## 3. Dipendenze Funzionali e Normalizzazione

### 3.1 Dipendenze Funzionali: Definizione e Tipi

Una **dipendenza funzionale** (FD, Functional Dependency) è una relazione tra attributi dove il valore di un attributo (o insieme di attributi) determina univocamente il valore di un altro attributo (o insieme). Formalmente, dati attributi X e Y di una relazione R, si dice che X → Y (X determina funzionalmente Y) se per ogni tuple t1, t2 in R, se t1[X] = t2[X] allora t1[Y] = t2[Y].

Le dipendenze funzionali derivano dalla semantica del dominio, non dalle specifiche istanze. La presenza di certe FD in una relazione implica regole che devono essere mantenute per tutti i possibili stati del database.

Le **FD banali** sono dipendenze dove Y è un sottoinsieme di X (X → X è sempre vera). Queste non aggiungono vincoli e possono essere ignorate.

Le **FD non banali** sono quelle dove Y non è un sottoinsieme di X. Queste definiscono vincoli significativi sullo schema.

Le **FD completamente non banali** sono quelle dove X ∩ Y = ∅ (gli attributi determinanti e quelli determinati sono disgiunti). Queste sono le dipendenze più utili per la normalizzazione.

Le **dipendenze transitive** si verificano quando un attributo determina un altro attributo che a sua volta determina un terzo. In termini di FD: X → Y e Y → Z implicano X → Z. Le dipendenze transitive causano anomalie di aggiornamento e sono eliminate dalla 3NF.

### 3.2 Calcolo delle Closure e delle Chiavi

La **closure** di un insieme di attributi X rispetto a un insieme di dipendenze funzionali F, denotata X+, è l'insieme di tutti gli attributi determinati funzionalmente da X attraverso F. Si calcola iterativamente:

1. X+ = X
2. Ripetere:
   - Per ogni FD Y → Z in F, se Y ⊆ X+ allora aggiungere Z a X+
   - Se X+ è cambiato, continuare
3. Finché X+ non cambia più

Il calcolo della closure è fondamentale per determinare se un insieme di attributi è una superchiave (la sua closure include tutti gli attributi della relazione) e per verificare l'implicazione logica tra FD.

Per **determinare la chiave minima** di una relazione:
1. Calcolare la closure di tutti gli attributi (dovrebbe essere l'intero schema)
2. Tentare di rimuovere attributi dalla chiave e verificare se la closure è ancora completa
3. La chiave minima (chiave candidato) è la chiave senza attributi ridondanti

L'**Armstrong's Axioms** sono le regole di inferenza per le dipendenze funzionali:

- **Riflessività**: Se Y ⊆ X, allora X → Y
- **Aumentatività**: Se X → Y, allora XZ → YZ
- **Transitività**: Se X → Y e Y → Z, allora X → Z

Da questi tre assiomi derivano:
- **Unione**: Se X → Y e X → Z, allora X → YZ
- **Decomposizione**: Se X → YZ, allora X → Y e X → Z
- **Pseudotransitività**: Se X → Y e YW → Z, allora XW → Z

### 3.3 Algoritmi di Normalizzazione

L'**algoritmo di decomposizione in 3NF** produce una decomposizione che preserva le dipendenze:

1. Trovare la cover minima F di tutte le FD
2. Per ogni FD X → Y in F, creare una relazione R(X ∪ Y)
3. Se nessuna relazione contiene una chiave della relazione originale, aggiungere una relazione con una chiave
4. Rimuovere le relazioni che sono contenute in altre

L'**algoritmo di decomposizione in BCNF** produce una decomposizione che soddisfa BCNF ma potrebbe non preservare tutte le FD:

1. Per ogni relazione R che viola BCNF (esiste FD X → A dove X non è una superchiave)
2. Decomporre R in R1(X ∪ A) e R2(R - A)
3. Ripetere fino a quando tutte le relazioni soddisfano BCNF

L'**algoritmo di synthesi per 3NF** è un metodo alternativo:
1. Calcolare la cover minima delle FD
2. Per ogni FD nella cover minima, creare una relazione
3. Se una relazione contiene le altre, unirle
4. Selezionare una delle relazioni come contenitore della chiave

### 3.4 Denormalizzazione: Quando e Come

La **denormalizzazione** è il processo intenzionale di aggiunta di ridondanza allo schema per migliorare le prestazioni. Contrariamente alla normalizzazione che minimizza la ridondanza, la denormalizzazione la accetta consapevolmente.

I **benefici** della denormalizzazione includono:
- Query più semplici (meno join)
- Letture più veloci (dati pre-calcolati)
- Aggregazioni materializzate
- Recupero più semplice per certain patterns

Gli **svantaggi** includono:
- Aggiornamenti più complessi (aggiornamento multiplo)
- Rischio di inconsistenza
- Maggiore spazio di storage
- Complessità di manutenzione

I **casi d'uso comuni** per la denormalizzazione includono:
- Tabelle di aggregazione per reporting (contatori pre-calcolati)
- Cache denormalizzate per query frequenti
- Snapshot per query storiche
- Dimensioni in data warehouse (star schema)

La denormalizzazione dovrebbe essere **consapevole e controllata**: documentare la ridondanza intenzionale, implementare trigger o application logic per mantenere la consistenza, monitorare la divergenza dei dati.

### 3.5 Normalizzazione nella Pratica

Nella pratica, la normalizzazione segue un approccio bilanciato:

Il **livello di normalizzazione appropriato** dipende dal caso d'uso:
- **OLTP**: tipicamente 3NF, bilanciando integrità e performance
- **OLAP/DW**: spesso denormalizzato (star schema, snowflake)
- **Sistemi embedded**:可能的mente meno normalizzato per semplicità

La **metodologia pratica** include:
1. Modello concettuale ER completo
2. Traduzione in schema relazionale normalizzato
3. Analisi delle query dominanti
4. Denormalizzazione selettiva dove necessario
5. Validazione con dati di test

I **trade-off** comuni:
- 3NF vs performance: join costosi su tabelle normalizzate
- BCNF vs preservazione dipendenze: impossibile in alcuni casi
- Normalizzazione vs readability: schema molto frammentato

---

## 4. Integrità del Dominio e Vincoli

### 4.1 Tipi di Vincoli nel Modello Relazionale

I **vincoli di integrità** (integrity constraints) sono regole che i dati devono rispettare per mantenere la consistenza del database. Lo standard SQL supporta diversi tipi di vincoli.

I **vincoli di dominio** (domain constraints) limitano i valori ammissibili per un attributo basandosi sul suo dominio. In SQL, i domini sono implementati attraverso tipi di dati (INT, VARCHAR, DATE), constraint CHECK, e domini personalizzati.

I **vincoli di chiave** (key constraints) garantiscono l'unicità delle tuple:
- **PRIMARY KEY**: identifica la chiave primaria, NOT NULL e UNIQUE
- **UNIQUE**: garantisce unicità ma permette NULL (una o più colonne)
- **NOT NULL**: impedisce valori NULL per una colonna

I **vincoli di integrità referenziale** (referential integrity) mantengono la coerenza tra tabelle correlate:
- **FOREIGN KEY**: referenzia la chiave primaria di un'altra tabella
- **ON DELETE**: specifica il comportamento quando la riga referenziata viene cancellata (NO ACTION, CASCADE, SET NULL, SET DEFAULT)
- **ON UPDATE**: specifica il comportamento quando la chiave referenziata viene aggiornata

I **vincoli generali** (table constraints) sono condizioni che coinvolgono multiple colonne:
- **CHECK**: condizione booleana che deve essere vera per ogni riga
- **UNIQUE (multiple columns)**: combinazione unica di colonne
- **EXCLUDE**: (PostgreSQL) vincoli di esclusione su tuple

### 4.2 Implementazione dei Vincoli in SQL

L'**implementazione dei vincoli** in SQL avviene durante la creazione o modifica delle tabelle:

```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    salary DECIMAL(10,2) CHECK (salary >= 0),
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT valid_email CHECK (email LIKE '%@%.%')
);
```

I vincoli possono essere aggiunti anche dopo la creazione della tabella:

```sql
ALTER TABLE employees 
ADD CONSTRAINT salary_min CHECK (salary >= 500);
```

I **vincoli differiti** (deferred constraints) vengono verificati solo al momento del commit, non dopo ogni statement. Sono utili quando una transazione temporaneamente viola vincoli ma li ripristina prima del commit:

```sql
SET CONSTRAINTS ALL DEFERRED;
-- Operazioni che temporaneamente violano vincoli
COMMIT; -- I vincoli vengono verificati qui
```

La **gestione delle violazioni** può essere configurata: NO ACTION (default, genera errore), CASCADE (propaga l'operazione alle righe figlie), SET NULL (imposta la chiave esterna a NULL), SET DEFAULT (imposta la chiave esterna al valore di default).

### 4.3 Vincoli Computazionali e Trigger

I **trigger** estendono i vincoli al di là delle semplici verifiche dichiarative. Un trigger è codice eseguito automaticamente in risposta a eventi DML (INSERT, UPDATE, DELETE) o DDL.

I trigger possono implementare:
- Vincoli complessi che coinvolgono multiple tabelle
- Cascading updates/deletes personalizzati
- Logging delle modifiche
- Computazione di colonne derivate
- Enforcement di business rules complesse

Esempio di trigger per audit:

```sql
CREATE TRIGGER employees_audit
AFTER UPDATE ON employees
FOR EACH ROW
EXECUTE FUNCTION audit_trigger();
```

I **trigger BEFORE** eseguono prima dell'operazione e possono modificare i valori prima dell'inserimento. I trigger **AFTER** eseguono dopo l'operazione e sono utili per logging e cascading. I trigger **INSTEAD OF** sono disponibili per le viste e permettono di rendere le viste updatable.

Le **considerazioni sulle performance** sono importanti: i trigger aggiungono overhead a ogni operazione DML, possono causare deadlock se modificano tabelle coinvolte in transazioni concorrenti, e possono rendere difficile la comprensione del flusso dei dati.

### 4.4 Valori di Default e Generated Columns

I **valori di default** forniscono un valore automatico quando non viene specificato esplicitamente:

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    quantity INTEGER DEFAULT 1
);
```

Le **generated columns** calcolano valori automaticamente da altre colonne:

```sql
CREATE TABLE products (
    price DECIMAL(10,2),
    tax_rate DECIMAL(5,4) DEFAULT 0.22,
    price_with_tax DECIMAL(10,2) GENERATED ALWAYS AS (price * (1 + tax_rate)) STORED
);
```

Le generated columns possono essere:
- **VIRTUAL**: calcolate al momento della lettura, non memorizzate
- **STORED**: calcolate e memorizzate come colonne normali

Le **sequenze** sono oggetti che generano numeri sequenziali, utilizzate per le chiavi surrogate:

```sql
CREATE SEQUENCE employee_id_seq;
INSERT INTO employees (id, name) VALUES (nextval('employee_id_seq'), 'John');
```

### 4.5 Data Quality e Validazione

La **qualità dei dati** richiede vincoli che vadano oltre la semplice sintassi. I **vincoli semantici** catturano le regole del business:

```sql
-- Un ordine non può avere data di consegna precedente alla data di creazione
ALTER TABLE orders
ADD CONSTRAINT valid_dates CHECK (delivery_date >= order_date);

-- Un impiegato non può avere stipendio superiore al doppio della media
-- Questo richiede una subquery
CREATE FUNCTION check_salary() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.salary > 2 * (SELECT AVG(salary) FROM employees WHERE department_id = NEW.department_id) THEN
        RAISE EXCEPTION 'Salary exceeds department limit';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

I **vincoli temporali** gestiscono dati con validità temporale:

```sql
-- Tabella con periodo di validità
CREATE TABLE employee_positions (
    employee_id INT,
    position VARCHAR(50),
    valid_from DATE,
    valid_to DATE,
    CONSTRAINT valid_period CHECK (valid_from <= valid_to),
    CONSTRAINT no_overlap EXCLUDE USING gist (
        employee_id WITH =,
        valid_from WITH <=,
        valid_to WITH >=
    )
);
```

La **validazione cross-table** verifica regole che coinvolgono multiple tabelle:

```sql
-- Verifica che l'ordine non superi il credito disponibile del cliente
ALTER TABLE orders
ADD CONSTRAINT credit_limit CHECK (
    total_amount <= (
        SELECT credit_limit - COALESCE(SUM(total_amount), 0)
        FROM orders o
        WHERE o.customer_id = orders.customer_id
        AND o.id != orders.id
    )
);
```

---

## 5. Rappresentazione delle Relazioni in SQL

### 5.1 DDL: Data Definition Language

Il **DDL** (Data Definition Language) è la parte di SQL dedicata alla definizione e modifica della struttura degli oggetti del database.

La **creazione delle tabelle** è l'operazione fondamentale:

```sql
CREATE TABLE table_name (
    column_name data_type constraints,
    ...
    table_constraints
);
```

I **tipi di dati comuni** includono:
- **Numerici**: INT, BIGINT, SMALLINT, DECIMAL(p,s), NUMERIC(p,s), FLOAT, REAL, DOUBLE PRECISION
- **Stringhe**: CHAR(n), VARCHAR(n), TEXT
- **Date/Time**: DATE, TIME, TIMESTAMP, TIMESTAMPTZ, INTERVAL
- **Booleani**: BOOLEAN
- **Binari**: BYTEA, BLOB
- **UUID**: UUID
- **JSON/JSONB**: JSON, JSONB
- **Array**: array types

La **modifica delle tabelle** (ALTER TABLE) permette di aggiungere, modificare, o rimuovere colonne e vincoli:

```sql
ALTER TABLE table_name
ADD COLUMN column_name data_type constraints;

ALTER TABLE table_name
DROP COLUMN column_name;

ALTER TABLE table_name
ALTER COLUMN column_name SET/DROP DEFAULT;

ALTER TABLE table_name
ADD CONSTRAINT constraint_name constraint_definition;
```

La **rimozione delle tabelle** (DROP TABLE) elimina la tabella e i suoi dati:

```sql
DROP TABLE table_name; -- Fallisce se ci sono dipendenze
DROP TABLE table_name CASCADE; -- Rimuove anche le dipendenze
DROP TABLE table_name IF EXISTS; -- Non genera errore se non esiste
```

### 5.2 Tipi di Tabelle Speciali

Le **tabelle temporanee** (temporary tables) esistono solo per la durata della sessione o della transazione:

```sql
CREATE TEMPORARY TABLE temp_results AS
SELECT * FROM large_table WHERE condition;
```

Le **tabelle esterne** (foreign tables) rappresentano dati esterni al database:

```sql
CREATE FOREIGN TABLE staging_sales (...)
SERVER remote_server
OPTIONS (table_name 'sales_data');
```

Le **tabelle non loggate** (unlogged tables) in PostgreSQL bypassano il write-ahead log per migliorare le prestazioni (ma non sono crash-safe):

```sql
CREATE UNLOGGED TABLE cache_data (...);
```

Le **tabelle partizionate** (partitioned tables) dividono i dati in partition fisiche basate su criteri:

```sql
CREATE TABLE orders (
    id BIGSERIAL,
    created_at TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2024 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

Le **tabelle con tipi personalizzati** (composite types) permettono di definire tipi strutturati:

```sql
CREATE TYPE address AS (
    street VARCHAR(200),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(50)
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    address address
);
```

### 5.3 Viste: Definizione e Utilizzo

Le **viste** (views) sono query memorizzate che presentano i dati in modo astratto:

```sql
CREATE VIEW view_name AS
SELECT ...
FROM ...
WHERE ...;
```

Le **viste possono essere semplici** (single-table, senza aggregazioni, senza funzioni di gruppo) o **complesse** (multi-table, con aggregazioni, con subquery).

Le **viste updatable** permettono INSERT, UPDATE, DELETE sulla vista, che si propagano alla tabella sottostante. Una vista è updatable se:
- È basata su una singola tabella
- Non contiene aggregazioni, GROUP BY, DISTINCT
- Non contiene sottoquery nella SELECT
- Ogni colonna non derivata ha una corrispondenza diretta nella tabella

Le **viste con CHECK OPTION** garantiscono che le modifiche rispettino il WHERE della vista:

```sql
CREATE VIEW active_employees AS
SELECT * FROM employees WHERE status = 'active'
WITH CHECK OPTION; -- Previene inserimenti di impiegati non attivi
```

Le **viste ricorsive** permettono query gerarchiche:

```sql
CREATE RECURSIVE VIEW org_chart AS
    SELECT id, name, manager_id, 1 as level
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, oc.level + 1
    FROM employees e
    JOIN org_chart oc ON e.manager_id = oc.id;
```

### 5.4 Viste Materializzate

Le **viste materializzate** (materialized views) memorizzano fisicamente il risultato della query, a differenza delle viste normali che sono virtuali:

```sql
CREATE MATERIALIZED VIEW monthly_sales AS
SELECT 
    DATE_TRUNC('month', order_date) as month,
    SUM(total) as revenue,
    COUNT(*) as order_count
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
WITH DATA;
```

Le **viste materializzate forniscono**:
- Prestazioni migliori per query complesse (risultato pre-calcolato)
- Possibilità di indici sulla vista materializzata
- Supporto per refresh incrementale in alcuni DBMS

Le **operazioni di refresh** aggiornano i dati:

```sql
REFRESH MATERIALIZED VIEW monthly_sales; -- Bloccante
REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_sales; -- Non bloccante (PostgreSQL)
```

Le **strategie di refresh** includono:
- **On-demand**: refresh manuale
- **Scheduled**: refresh automatico a intervalli
- **On-commit**: refresh dopo ogni transazione che modifica le tabelle sorgente

### 5.5 Schema Information e Metadati

I **metadati dello schema** sono accessibili attraverso viste di sistema:

In **PostgreSQL**:
```sql
-- Liste delle tabelle
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Lista delle colonne con tipi
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'employees';

-- Lista degli indici
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'employees';
```

In **MySQL**:
```sql
SHOW TABLES;
DESCRIBE table_name;
SHOW INDEX FROM table_name;
```

In **SQL Server**:
```sql
SELECT * FROM INFORMATION_SCHEMA.TABLES;
SELECT * FROM INFORMATION_SCHEMA.COLUMNS;
SELECT * FROM sys.indexes;
```

---

## 6. Schema Design Best Practices

### 6.1 Naming Convention

Le **convenzioni di naming** sono essenziali per la manutenibilità del database. Le convenzioni dovrebbero essere:
- Consistenti all'interno del progetto
- Comprensibili senza contesto aggiuntivo
- Pronunciabili
- Non troppo lunghe

Le **tabelle** dovrebbero avere:
- Nomi in singolare (products non product_list)
- Nomi in snake_case (customer_orders)
- Evita abbreviazioni non standard
- Non usare prefissi come "tbl_" o "table_"

Le **colonne** dovrebbero avere:
- Nomi che indicano chiaramente il contenuto
- Nomi unici all'interno dello schema (non "id" ovunque)
- Convenzioni coerenti per le chiavi (customer_id, non customerId o customer_num)

Le **chiavi** dovrebbero seguire pattern consistenti:
- Primary key: table_id (product_id) o solo id con nome tabella implicito
- Foreign key: referenced_table_id (customer_id)

Le **indici** dovrebbero seguire un pattern: idx_tablename_columns (idx_orders_customer_date)

### 6.2 Chiavi Primarie: Scelta e Design

La **scelta della chiave primaria** è una decisione fondamentale che influenza l'intero design:

Le **chiavi surrogate** (surrogate keys) sono identificatori generati automaticamente, tipicamente interi auto-incrementali o UUID. Vantaggi:
- Non cambiano mai (storico)
- Sempre uniche
- Dimensione ridotta e constante
- Indipendenti dal dominio

Svantaggi:
- Non hanno significato di per sé
- Richiedono join per visualizzare dati significativi
- Possono essere problematiche in sistemi distribuiti

Le **chiavi naturali** (natural keys) derivano dal dominio. Vantaggi:
- Significative per gli utenti
- Non richiedono join per identificazione
- Autodescrittive

Svantaggi:
- Possono cambiare nel tempo
- Possono non essere uniche inizialmente (codici fiscali, ecc.)
- Più complesse da gestire

Le **best practices** raccomandano:
- Preferire chiavi surrogate per tabelle transazionali
- Mantenere chiavi naturali come chiavi alternative (UNIQUE)
- Usare UUID per sistemi distribuiti o quando le chiavi sono utilizzate in URL
- Considerare keys composite solo quando strettamente necessario

### 6.3 Foreign Keys e Relazioni

Le **foreign keys** implementano le relazioni tra tabelle:

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id),
    ...
);
```

Le **azioni di riferimento** definiscono il comportamento in caso di cancellazione o aggiornamento della riga referenziata:
- **NO ACTION**: errore se ci sono righe figlie
- **CASCADE**: cancella/aggiorna le righe figlie
- **SET NULL**: imposta la FK a NULL
- **SET DEFAULT**: imposta la FK al valore di default

Le **foreign keys composte** sono necessarie per relazionimany-to-many attraverso tabelle junction:

```sql
CREATE TABLE order_items (
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE RESTRICT,
    quantity INT NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

Le **foreign keys deferibili** permettono di rimandare la verifica alla fine della transazione:

```sql
ALTER TABLE orders 
ADD CONSTRAINT fk_customer 
FOREIGN KEY (customer_id) REFERENCES customers(id) 
DEFERRABLE INITIALLY DEFERRED;
```

### 6.4 Timestamp e Audit Columns

Le **colonne di audit** tracciano la storia delle tuple:

```sql
CREATE TABLE records (
    id SERIAL PRIMARY KEY,
    data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    version INTEGER NOT NULL DEFAULT 1
);
```

Le **colonne di versioning** (optimistic locking) prevengono conflitti di modifiche concorrenti:

```sql
UPDATE records 
SET data = 'new value', version = version + 1 
WHERE id = ? AND version = ?;
-- Se nessuna riga aggiornata, significa che la versione era cambiata
```

Le **colonne soft delete** permettono di "cancellare" senza eliminare fisicamente:

```sql
ALTER TABLE records 
ADD COLUMN deleted_at TIMESTAMP NULL;

SELECT * FROM records WHERE deleted_at IS NULL; -- Query "normali"
```

I **trigger** possono automatizzare l'aggiornamento dei timestamp:

```sql
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.updated_by = current_user;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_update_timestamp
    BEFORE UPDATE ON records
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();
```

### 6.5 Colonne Ridondanti e Denormalizzazione Controllata

Le **colonne denormalizzate** sono accettate consapevolmente per migliorare le prestazioni:

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    customer_name VARCHAR(100), -- Denormalizzato per evitare join
    ...
);
```

Le **tabelle di aggregazione** pre-calcolano statistiche:

```sql
CREATE TABLE order_stats (
    customer_id INT PRIMARY KEY,
    total_orders INT DEFAULT 0,
    total_spent DECIMAL(15,2) DEFAULT 0,
    last_order_date DATE
);

-- Refresh periodico o via trigger
```

Le **considerazioni** per la denormalizzazione:
- Documentare esplicitamente la ridondanza
- Implementare meccanismi di sincronizzazione (trigger, application logic)
- Monitorare la divergenza dei dati
- Valutare se il beneficio di prestazioni giustifica la complessità aggiuntiva

---

## 7. Schema Evolution e Migration

### 7.1 Modifiche allo Schema

Le **modifiche allo schema** (schema evolution) sono inevitabili durante il ciclo di vita di un'applicazione. Le operazioni comuni includono:

L'**aggiunta di colonne**:
```sql
ALTER TABLE customers 
ADD COLUMN phone VARCHAR(20);
```

La **rimozione di colonne**:
```sql
ALTER TABLE customers 
DROP COLUMN phone; -- Potrebbe fallire se ci sono dipendenze
ALTER TABLE customers 
DROP COLUMN phone CASCADE; -- Rimuove anche le dipendenze
```

La **modifica del tipo di una colonna**:
```sql
ALTER TABLE orders 
ALTER COLUMN notes TYPE TEXT; -- Potrebbe richiedere cast esplicito
```

L'**aggiunta di vincoli**:
```sql
ALTER TABLE orders 
ADD CONSTRAINT positive_quantity CHECK (quantity > 0);
```

La **rimozione di vincoli**:
```sql
ALTER TABLE orders 
DROP CONSTRAINT positive_quantity;
```

### 7.2 Migration Strategies

Le **strategie di migrazione** affrontano i cambiamenti in ambienti di produzione:

La **migrazione in-place** modifica direttamente la tabella:
- Semplice ma può bloccare la tabella
- Adatta per cambiamenti piccoli
- Richiede finestra di manutenzione per operazioni lunghe

La **migrazione con tabella temporanea** copia i dati in una nuova struttura:
```sql
-- 1. Creare nuova tabella
CREATE TABLE customers_new (...);

-- 2. Copiare i dati con trasformazione
INSERT INTO customers_new (...) SELECT ... FROM customers;

-- 3. Sostituire la tabella
ALTER TABLE customers RENAME TO customers_old;
ALTER TABLE customers_new RENAME TO customers;

-- 4. Verificare e rimuovere la tabella vecchia
```

La ** migrazione con colonna parallela** aggiunge la nuova struttura accanto a quella esistente:
```sql
-- 1. Aggiungere nuova colonna (nullable)
ALTER TABLE customers ADD COLUMN new_id UUID;

-- 2. Popolare la nuova colonna
UPDATE customers SET new_id = gen_random_uuid() WHERE new_id IS NULL;

-- 3. Aggiungere vincolo
ALTER TABLE customers ALTER COLUMN new_id SET NOT NULL;

-- 4. Rimuovere la vecchia colonna
```

### 7.3 Schema Versioning

Il **schema versioning** tiene traccia delle versioni dello schema nel tempo:

I **numeri di versione** possono essere:
- Sequenziali (v1, v2, v3)
- Basati su date (2024-01-15)
- Semantic (1.0.0, 1.1.0)

Le **tabelle di versione** tracciano lo stato corrente:
```sql
CREATE TABLE schema_version (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
```

Le **migration scripts** dovrebbero essere:
- Idempotenti (rieseguibili senza effetti collaterali)
- Versionati insieme al codice
- Testati in ambienti simili alla produzione

### 7.4 Zero-Downtime Migrations

Le **migrazioni a downtime zero** sono essenziali per sistemi ad alta disponibilità:

La **gradualità** significa:
- Aggiungere prima le nuove colonne (nullable)
- Popolare i dati in background
- Spostare il codice che scrive sulla nuova struttura
- Rimuovere la vecchia struttura

Gli **indici** possono essere aggiunti CONCURRENTLY in PostgreSQL:
```sql
CREATE INDEX CONCURRENTLY idx_new_column ON table(column);
```

Le **tabelle temporanee** permettono di testare strutture nuove senza impatto:
```sql
-- Test con tabella temporanea
CREATE TEMPORARY TABLE new_structure AS 
SELECT * FROM old_structure WITH NO DATA;

-- Applicare le modifiche
ALTER TABLE new_structure ADD COLUMN ...;

-- Verificare con dati reali
INSERT INTO new_structure SELECT * FROM old_structure LIMIT 100;
```

### 7.5 Rollback Strategies

Le **strategie di rollback** sono necessarie quando le migrazioni falliscono:

Il **backup pre-migrazione** è la strategia più sicura:
```sql
-- Backup della tabella
CREATE TABLE orders_backup AS SELECT * FROM orders;
```

Il **doppio write** mantiene due scritture durante la transizione:
- Scrivere sia sulla struttura vecchia che sulla nuova
- Validare la consistenza
- Rimuovere la doppia scrittura dopo la validazione

Il **feature flag** permette di attivare/disattivare le nuove funzionalità:
```sql
-- Nel codice applicativo
if (feature_enabled('new_schema')) {
    insert into new_table(...);
} else {
    insert into old_table(...);
}
```

---

## 8. Design Pattern per Schema Relazionali

### 8.1 Pattern per Timestamp e Temporal Data

Il **temporal table pattern** gestisce dati con validità temporale:

```sql
-- Tabella con periodo di validità
CREATE TABLE employee_departments (
    employee_id INT REFERENCES employees(id),
    department_id INT REFERENCES departments(id),
    effective_from DATE NOT NULL,
    effective_to DATE,
    PRIMARY KEY (employee_id, effective_from)
);

-- Query: trovare il dipartimento attuale
SELECT ed.* 
FROM employee_departments ed 
WHERE ed.employee_id = 123 
AND CURRENT_DATE BETWEEN ed.effective_from 
    AND COALESCE(ed.effective_to, '9999-12-31');
```

Il **soft delete pattern** permette la "cancellazione" senza perdita di dati:

```sql
-- Colonna di stato invece di cancellazione fisica
ALTER TABLE orders ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- Query che escludono cancellate
CREATE VIEW active_orders AS SELECT * FROM orders WHERE status = 'active';
```

Il **audit log pattern** registra ogni modifica:
```sql
CREATE TABLE audit_log (
    table_name VARCHAR(100),
    operation VARCHAR(10),
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.2 Pattern per Hierarchies

Il **materialized path pattern** memorizza il percorso completo:

```sql
ALTER TABLE categories ADD COLUMN path TEXT;

-- Esempio: "0001/0004/0007"
-- Per cercare tutti i discendenti:
SELECT * FROM categories WHERE path LIKE '0001/0004/%';
```

Il **nested set pattern** memorizza gli intervalli:

```sql
ALTER TABLE categories ADD COLUMN lft INT, ADD COLUMN rgt INT;

-- Query per tutti i discendenti:
SELECT * FROM categories WHERE lft BETWEEN ? AND ?;
-- Query per tutti i progenitori:
SELECT * FROM categories WHERE lft < ? AND rgt > ?;
```

Il **adjacency list pattern** è il più semplice:

```sql
ALTER TABLE categories ADD COLUMN parent_id INT REFERENCES categories(id);

-- Query ricorsiva (PostgreSQL 8.4+):
WITH RECURSIVE tree AS (
    SELECT id, name, parent_id, 1 as level
    FROM categories WHERE id = ?
    UNION ALL
    SELECT c.id, c.name, c.parent_id, t.level + 1
    FROM categories c
    JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree;
```

### 8.3 Pattern per Many-to-Many

Le **tabelle junction** implementano relazioni many-to-many:

```sql
CREATE TABLE order_items (
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

Le **relazioni con attributi** aggiungono informazioni alla relazione:

```sql
CREATE TABLE student_courses (
    student_id INT REFERENCES students(id),
    course_id INT REFERENCES courses(id),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    grade VARCHAR(2),
    PRIMARY KEY (student_id, course_id)
);
```

Le **tabelle con tipi multipli** permettono relazioni con entità diverse:

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    recipient_id INT NOT NULL,
    recipient_type VARCHAR(20) NOT NULL, -- 'user', 'group', 'role'
    message TEXT,
    ...
    CONSTRAINT valid_recipient CHECK (
        (recipient_type = 'user' AND recipient_id > 0) OR
        (recipient_type = 'group' AND recipient_id < 0)
    )
);
```

### 8.4 Pattern per CQRS e Read Models

Il **CQRS pattern** (Command Query Responsibility Segregation) separa le operazioni di lettura da quelle di scrittura:

```sql
-- Tabella di write (normalizzata)
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    status VARCHAR(20),
    ...
);

-- Tabella di lettura (denormalizzata per query specifiche)
CREATE TABLE orders_read (
    id BIGINT PRIMARY KEY,
    customer_name VARCHAR(100),
    customer_email VARCHAR(255),
    status VARCHAR(20),
    total DECIMAL(12,2),
    item_count INT,
    created_date DATE,
    ...
);
```

Il **materialized view pattern** pre-calcola le query complesse:

```sql
CREATE MATERIALIZED VIEW customer_stats AS
SELECT 
    c.id,
    c.name,
    COUNT(o.id) as order_count,
    SUM(o.total) as lifetime_value,
    MAX(o.created_at) as last_order
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id;
```

### 8.5 Pattern per Soft Deletes e Multi-Tenancy

Il **soft delete con polymorphic** gestisce cancellazioni per tipi diversi:

```sql
CREATE TABLE deleted_records (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id BIGINT NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_by VARCHAR(100)
);
```

Il **multi-tenant con schema** isola i tenant con schemi separati:

```sql
-- Ogni tenant ha il proprio schema
CREATE SCHEMA tenant_123;
CREATE SCHEMA tenant_456;

-- Query per un tenant specifico:
SET search_path TO tenant_123, public;
```

Il **multi-tenant con colonna** condivide le tabelle con filtro:

```sql
ALTER TABLE records ADD COLUMN tenant_id INT NOT NULL;

-- Query con filtro automatico:
CREATE VIEW tenant_records AS
SELECT * FROM records WHERE tenant_id = current_tenant_id();
```

---

## 9. Case Study: Progettazione Schema E-commerce

### 9.1 Requisiti del Dominio

Per illustrare l'applicazione pratica dei concetti, consideriamo la progettazione di uno schema per un sistema e-commerce.

I **requisiti funzionali** includono:
- Gestione prodotti con categorie e attributi
- Catalogo prodotti con ricerca e navigazione
- Carrello della spesa
- Ordini e gestione ordini
- Clienti e autenticazione
- Pagamenti
- Spedizioni
- Resi e rimborsi

I **requisiti non funzionali** includono:
- Supporto per migliaia di prodotti
- Query di ricerca full-text
- Gestione di immagini multiple per prodotto
- Prezzi convaliduti per valute multiple
- Storico ordini completo

### 9.2 Progettazione Concettuale

Le **entità principali** identificate:

**Product**: id, name, description, sku, price, cost, category, brand, images, attributes, stock, is_active

**Category**: id, name, parent_category (hierarchical)

**Customer**: id, email, password_hash, name, addresses, phone, created_at

**Order**: id, customer_id, status, subtotal, tax, shipping, total, shipping_address, billing_address, created_at

**OrderItem**: order_id, product_id, quantity, unit_price

**Payment**: order_id, amount, method, status, transaction_id

**Shipment**: order_id, carrier, tracking_number, status

Le **relazioni**:
- Product → Category (many-to-one)
- Category auto-referencing (parent-child)
- Order → Customer (many-to-one)
- Order → OrderItem (one-to-many)
- OrderItem → Product (many-to-one)
- Order → Payment (one-to-many, tipicamente uno)
- Order → Shipment (one-to-one o one-to-many)

### 9.3 Progettazione Logica Normalizzata

Lo **schema normalizzato** risultante:

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id INT REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(12,2) NOT NULL,
    cost DECIMAL(12,2),
    category_id INT REFERENCES categories(id),
    brand VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    sort_order INT DEFAULT 0
);

CREATE TABLE product_attributes (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    value VARCHAR(255) NOT NULL
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id) ON DELETE CASCADE,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(2) NOT NULL,
    is_default BOOLEAN DEFAULT false
);

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    status VARCHAR(20) DEFAULT 'pending',
    subtotal DECIMAL(12,2) NOT NULL,
    tax DECIMAL(12,2) DEFAULT 0,
    shipping DECIMAL(12,2) DEFAULT 0,
    total DECIMAL(12,2) NOT NULL,
    shipping_address_id INT REFERENCES addresses(id),
    billing_address_id INT REFERENCES addresses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    product_name VARCHAR(255) NOT NULL,
    sku VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    total DECIMAL(12,2) NOT NULL
);

-- Indici per query comuni
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = true;
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
```

### 9.4 Progettazione Denormalizzata

Per **performance di lettura**, consideriamo viste materializzate e tabelle di aggregazione:

```sql
-- Vista per catalogo prodotti con informazioni complete
CREATE VIEW product_catalog AS
SELECT 
    p.id,
    p.sku,
    p.name,
    p.description,
    p.price,
    c.name as category_name,
    (SELECT url FROM product_images WHERE product_id = p.id ORDER BY sort_order LIMIT 1) as main_image,
    p.is_active
FROM products p
LEFT JOIN categories c ON p.category_id = c.id;

-- Tabella di aggregazione per statistiche prodotto
CREATE TABLE product_stats (
    product_id INT PRIMARY KEY REFERENCES products(id),
    times_viewed INT DEFAULT 0,
    times_purchased INT DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    last_purchased_at TIMESTAMP
);

-- Tabella di aggregazione per statistiche cliente
CREATE TABLE customer_stats (
    customer_id INT PRIMARY KEY REFERENCES customers(id),
    total_orders INT DEFAULT 0,
    total_spent DECIMAL(15,2) DEFAULT 0,
    last_order_at TIMESTAMP,
    average_order_value DECIMAL(12,2)
);
```

### 9.5 Gestione dell'Inventory

Per la **gestione dell'inventory**, implementiamo:

```sql
-- Tabella inventory con tracciamento versione
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INT UNIQUE REFERENCES products(id),
    quantity INT NOT NULL DEFAULT 0,
    reserved INT NOT NULL DEFAULT 0,
    available INT GENERATED ALWAYS AS (quantity - reserved) STORED,
    reorder_point INT DEFAULT 10,
    reorder_quantity INT DEFAULT 50,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INT DEFAULT 1
);

-- Funzione per prenotare inventario
CREATE OR REPLACE FUNCTION reserve_inventory(
    p_product_id INT, 
    p_quantity INT
) RETURNS BOOLEAN AS $$
DECLARE
    v_available INT;
BEGIN
    SELECT available INTO v_available 
    FROM inventory 
    WHERE product_id = p_product_id
    FOR UPDATE; -- Lock della riga
    
    IF v_available >= p_quantity THEN
        UPDATE inventory 
        SET reserved = reserved + p_quantity,
            version = version + 1
        WHERE product_id = p_product_id;
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Funzione per confermare l'ordine (dedurre dall'inventario)
CREATE OR REPLACE FUNCTION commit_inventory(
    p_product_id INT, 
    p_quantity INT
) RETURNS VOID AS $$
BEGIN
    UPDATE inventory 
    SET quantity = quantity - p_quantity,
        reserved = reserved - p_quantity,
        version = version + 1
    WHERE product_id = p_product_id;
END;
$$ LANGUAGE plpgsql;
```

---

## 10. Appendice: Risorse e Riferimenti

### A.1 Strumenti di Modellazione

- **DB Diagram**: dbdiagram.io - diagrammi ER in formato DSL
- **Draw.io**: draw.io - diagrammi generici
- **pgModeler**: pgmodeler.io - modeling specifico per PostgreSQL
- **DBeaver**: dbeaver.io - client database con reverse engineering

### A.2 Riferimenti Teorici

- "The Relational Model for Database Management: Version 2" - E.F. Codd
- "Fundamentals of Database Systems" - Elmasri & Navathe
- "Database Management Systems" - Ramakrishnan & Gehrke

### A.3 Link Utili

- SQL Standard: iso.org
- PostgreSQL Documentation: postgresql.org/docs/current
- MySQL Reference Manual: dev.mysql.com/doc/refman/8.0/en/

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*
*Per domande o correzioni, consultare il repository o contattare il team di documentazione.*