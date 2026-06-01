# Architettura Interna di PostgreSQL

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
1. Panoramica dell'Architettura
2. Processi Backend e Shared Memory
3. Gestione delle Connessioni
4. Storage Engine e Buffer Pool
5. Query Execution Pipeline
6. Catalogo di Sistema
7. Memory Architecture
8. Disk Layout
9. Background Processes
10. Recovery e Checkpoints

---

## 1. Panoramica dell'Architettura

### 1.1 Architettura Multi-Processo

PostgreSQL utilizza un'architettura **multi-processo** che è una delle caratteristiche distintive rispetto ad altri database come MySQL. Questa architettura offre vantaggi significativi in termini di robustezza e affidabilità.

Il **postmaster** è il processo padre del cluster PostgreSQL. Funziona come orchestratore centrale del sistema: ascolta le connessioni in arrivo sulla porta configurata (default 5432), genera nuovi processi backend per gestire ogni connessione client, gestisce il recovery dopo un crash, e coordina i segnali di sistema per tutte le operazioni critiche. Il postmaster rimane in esecuzione per tutta la durata del server e supervisiona tutti gli altri processi.

I **backend processes** sono processi individuali creati per gestire ogni connessione client. Quando un client si connette, il postmaster fork un nuovo processo backend che eredita una copia della memoria del postmaster. Questo processo gestisce l'intero ciclo di vita della query: parsing, analisi, ottimizzazione, esecuzione, e restituzione dei risultati. Quando il client si disconnette, il backend process termina.

I **background workers** sono processi aggiuntivi che eseguono attività in background senza una connessione client diretta. Esempi includono: autovacuum launcher che gestisce la manutenzione automatica, parallel query workers per query parallele, logical replication workers, e background writer per la gestione delle pagine dirty.

Questa architettura multi-processo offre vantaggi importanti: l'isolamento dei processi significa che un crash in un backend non influenza gli altri processi; la memoria di un processo non può essere corrotta accidentalmente da un altro; e il debugging è semplificato perché ogni processo può essere ispezionato indipendentemente.

### 1.2 Shared Memory

La **shared memory** è una regione di memoria condivisa tra tutti i processi PostgreSQL, essenziale per la comunicazione inter-processo e la cache condivisa.

Il **buffer pool** è la cache principale delle pagine del database. Memorizza le pagine di dati in memoria per evitare accessi frequenti al disco. La dimensione è controllata dal parametro shared_buffers (default: 128MB, consigliato: 25% della RAM per server dedicati).

Il **WAL buffer** è la cache per il Write-Ahead Log. Le modifiche vengono prima scritte nel WAL buffer prima di essere sincronizzate su disco. La dimensione è controllata da wal_buffers.

La **lock table** gestisce i lock a livello di database: row-level locks, table-level locks, advisory locks. È implementata come una tabella hash in shared memory.

Il **transaction status** (CLOG - Commit Log) traccia lo stato di ogni transazione: in-progress, committed, o aborted. Questo è cruciale per determinare la visibilità delle tuple MVCC.

### 1.3 Client-Server Communication

La **comunicazione** tra client e server PostgreSQL avviene attraverso un protocollo binario efficiente che supporta diversi modelli di interazione.

Il flusso base della comunicazione:
1. Client stabilisce una connessione TCP sulla porta del server
2. Client invia un messaggio di startup con credenziali
3. Server autentica il client e crea un backend process
4. Client invia query come messaggi
5. Server parsa, analizza, ottimizza, esegue
6. Server invia risultati al client
7. Ripetere per altre query fino alla disconnessione

Il protocollo supporta diverse modalità:

**Simple Query Protocol**: Il client invia query come stringhe SQL complete. Il server le parsa ed esegue direttamente. Semplice ma meno efficiente per query ripetute.

**Extended Query Protocol**: Il client può separare le fasi di parsing, binding, e execution. Permette l'uso di prepared statements con parametrizzazione. Più efficiente per query ripetute con parametri diversi.

**Binary Protocol**: I dati vengono trasferiti in formato binario invece che come stringhe testuali. Più efficiente per grandi volumi di dati, ma richiede gestione esplicita dei tipi.

### 1.4 Extensions Architecture

L'**architecture delle estensioni** è una delle caratteristiche più potenti di PostgreSQL, permettendo di estendere funzionalità del core senza modificare il codice sorgente.

Le **internal extensions** (contrib modules) sono moduli inclusi nella distribuzione PostgreSQL ma non compilati per default. Esempi: pg_trgm per trigrammi, hstore per chiavi-valori, uuid-ossp per generazione UUID, citext per case-insensitive text.

Le **external extensions** sono estensioni sviluppate dalla comunità o da terze parti. Possono aggiungere: nuovi tipi di dati (PostGIS per GIS, pgvector per embeddings), indici specializzati (PGroonga per full-text search), funzionalità di replica.

Le **procedural languages** permettono di scrivere funzioni stored in diversi linguaggi: PL/pgSQL (default), PL/Python, PL/Perl, PL/R, PL/Tcl, e molti altri.

Le estensioni vengono installate con CREATE EXTENSION e gestite tramite pg_extension system catalog.

---

## 2. Processi Backend e Shared Memory

### 2.1 Postmaster

Il **postmaster** (processo con PID originale) è il cuore del cluster PostgreSQL. È responsabile di:

**Gestione delle connessioni**: Il postmaster rimane in ascolto sulla porta configurata (5432 di default) usando select() o poll() per rilevare nuove connessioni TCP. Quando arriva una richiesta di connessione, crea un nuovo processo backend.

**Autenticazione**: Prima di creare il backend process, il postmaster gestisce l'autenticazione del client. Supporta vari metodi: trust (nessuna autenticazione), md5, scram-sha-256, certificati SSL, GSSAPI, e altri. Se l'autenticazione fallisce, il postmaster chiude la connessione senza creare un backend.

**Signal handling**: Il postmaster gestisce i segnali di sistema: SIGTERM per shutdown elegante, SIGINT per shutdown interrupt, SIGHUP per reload configurazione, SIGQUIT per shutdown immediato. Propaga i segnali ai backend figli.

**Recovery**: Dopo un crash, il postmaster coordina il recovery del database. Analizza lo stato nel pg_control e avvia il processo di recovery prima di accettare nuove connessioni.

**Processo di bootstrap**: Durante l'inizializzazione del cluster (initdb), il postmaster crea le strutture iniziali del database.

### 2.2 Backend Processes

Ogni **backend process** (postgres) è un processo separato che gestisce le query di una singola connessione client. Il backend è isolato: problemi in un backend non influenzano gli altri.

Il backend esegue il **query processing pipeline**:
1. **Parser**: Converte la query SQL in un parse tree
2. **Analyzer**: Analizza semanticamente e crea query tree
3. **Rewriter**: Applica regole di riscrittura (views, rules)
4. **Optimizer**: Genera piani di esecuzione e seleziona il migliore
5. **Executor**: Esegue il piano e produce risultati

La memoria del backend è privata: ogni processo ha il proprio spazio di indirizzamento. I backend possono comunicare attraverso la shared memory per lock e coordinamento.

### 2.3 Shared Memory Structure

La **shared memory** PostgreSQL è una regione di memoria condivisa creata all'avvio del server e accessibile da tutti i processi.

**ShmemHeader** contiene metadati globali: dimensione della shared memory, identificatori, flags di stato, puntatori alle strutture principali.

**BufferDesc** (descrittori buffer) è un array che descrive ogni buffer nel buffer pool. Ogni descrittore contiene: ID della relazione e numero di pagina, flag di pin count, flag di dirty, usecount per algoritmo di rimpiazzo, pointer ai dati effettivi.

**Lock table** implementa il lock manager. È una tabella hash che memorizza i lock attivi. Ogni lock è identificato da: tipo di lock (relation, page, tuple, transactionid, etc.), identificatore della risorsa, modalità (AccessShareLock, RowExclusiveLock, etc.), elenco dei processi che lo detengono.

**Proclist** mantiene la lista dei processi attivi nel cluster. Ogni elemento contiene: PID del processo, stato, informazioni sulla transazione corrente, timestamp dell'ultima attività.

**XLOG buffers** (WAL buffers) sono la cache per il Write-Ahead Log. Dimensione configurabile con wal_buffers.

**CLOG** (Commit Log) memorizza lo stato di ogni transaction ID: IN_PROGRESS, COMMITTED, ABORTED. Implementato come array di bit in shared memory.

### 2.4 Dynamic Shared Memory

La **dynamic shared memory (DSM)** è memoria allocata dinamicamente per scopi specifici, diversa dalla shared memory fissa creata all'avvio.

**Parallel query**: Durante l'esecuzione parallela, i worker condividono dati attraverso DSM. Il leader alloca memoria per condividere risultati intermedi con i worker.

**Logical replication**: ILogical decoding slot richiedono memoria per tracciare lo stato della replica.

**Custom background workers**: Estensioni possono richiedere DSM per la comunicazione tra worker.

### 2.5 Interprocess Communication

La **comunicazione inter-processo (IPC)** in PostgreSQL usa diversi meccanismi:

**Spinlocks**: Lock very lightweight per proteggere strutture piccole e accessibili frequentemente. Implementati con operazioni atomiche sulla CPU. Usati per: buffer pin counts, contatori, piccole strutture.

**Lightweight locks (LWL)**: Lock più robusti per strutture di dimensione media. Usano un meccanismo di spinning iniziale, poi schedulazione. Esempi: lock sulla hash table, lock su transazioni.

**Regular locks**: Lock pesanti per risorse grandi. Implementati con semafori o code di attesa. Usati per: table-level locks, advisory locks.

**Condition variables**: Per la sincronizzazione su eventi. Un processo può sospendersi aspettando che una condizione diventi vera.

**Signal-based communication**: Per notifiche asincrone: SIGUSR1 per notificare altri processi, usato dal backend writer per dirty page notification.

---

## 3. Gestione delle Connessioni

### 3.1 Connection Pool

PostgreSQL non include un connection pool integrato a livello server, ma supporta connessioni multiple gestite dal postmaster.

**max_connections** è il parametro che definisce il numero massimo di connessioni client al server. Il valore predefinito è 100. Questo parametro determina la dimensione di diverse strutture in shared memory, inclusa la tabella dei lock. Aumentare questo valore aumenta il consumo di memoria.

**superuser_reserved_connections** riserva un numero di slot di connessione per gli utenti superuser. Default: 3. Anche quando il pool è pieno, i superuser possono sempre connettersi per manutenzione.

**Connection pooling esterno**: Poiché PostgreSQL non ha connection pool integrato, si usano soluzioni esterne:

- **PgBouncer**: Connection pool leggero con tre modalità: session pooling (connessione per sessione), transaction pooling (connessione per transazione), statement pooling (connessione per statement). Gestisce centinaia di migliaia di connessioni con una frazione della memoria.

- **Pgpool-II**: Oltre al connection pooling, offre: load balancing per query di sola lettura, query caching, replication, e high availability.

- **ODBC/JDBC built-in pooling**: Driver client possono implementare pooling a livello applicativo.

### 3.2 Authentication

PostgreSQL supporta diversi **metodi di autenticazione**, configurabili in pg_hba.conf:

**trust**: Il client è automaticamente autenticato senza verifica. Usato solo per connessioni locali o in ambienti di sviluppo. MAI usare in produzione per connessioni remote.

**md5**: Autenticazione con challenge-response usando hash MD5 della password. Obsoleto: MD5 è considerato debole. Richiede che la password sia memorizzata in chiaro o come MD5 sul server.

**scram-sha-256** (SCRAM-SHA-256): Metodo moderno e raccomandato. Sicuro, usa hashing forte (SHA-256) e negoziazione challenge-response senza trasmettere mai la password. Richiede password memorizzata come SCRAM.

**cert**: Autenticazione usando certificati SSL client. Il server verifica il certificato del client contro la CA configurata. Fornisce autenticazione forte basata su PKI.

**gssapi**: Autenticazione Kerberos/SSO. Richiede configurazione Kerberos sul server e sui client.

**peer**: Per connessioni locali, verifica che l'utente del processo client corrisponda a un utente PostgreSQL.

**ldap**: Delega l'autenticazione a un server LDAP.

### 3.3 Connection Lifecycle

Il **ciclo di vita** di una connessione PostgreSQL attraversa diverse fasi:

**1. TCP Connection**: Il client stabilisce una connessione TCP con il server. Il server accetta la connessione nella coda di listen backlog.

**2. Startup Message**: Il client invia un messaggio di startup con: protocol version, database name, username, opzioni di connessione. Se la versione del protocollo non è supportata, il server chiude la connessione.

**3. Authentication**: Il server invia un messaggio di richiesta autenticazione. Il client risponde con le credenziali appropriate. Il server verifica e accetta o rifiuta la connessione.

**4. Session Initialization**: Il backend process inizializza la sessione: imposta parametri default, esegue procedure di authentik接, carica configurazioni specifiche dell'utente.

**5. Query Execution**: La sessione entra nel loop di esecuzione query:
- Client invia query
- Server esegue query
- Server invia risultati
- Ripeti

**6. Termination**: La disconnessione può essere:
- Client-initiated: client invia Terminate message
- Server-initiated: per errori, timeout, admin action

### 3.4 Statement Timeout

PostgreSQL fornisce diversi **timeout** per controllare l'esecuzione:

**statement_timeout**: Limita il tempo totale di esecuzione di una singola query. Valore 0 (default) significa nessun timeout. Esempi:
```sql
SET statement_timeout = '30s';
-- or
SET statement_timeout = 30000;  -- milliseconds
```

**idle_in_transaction_session_timeout**: Limita il tempo che una sessione può rimanere in stato "idle in transaction" (transazione iniziata ma non conclusa). Previene connessioni che bloccano risorse:

```sql
SET idle_in_transaction_session_timeout = '2min';
```

**lock_timeout**: Limita il tempo di attesa per l'acquisizione di un lock:

```sql
SET lock_timeout = '10s';
-- Previene attese infinite su lock
```

**deadlock_timeout**: Tempo prima che il sistema controlli i deadlock:

```sql
SET deadlock_timeout = '1s';
```

### 3.5 Prepared Statements

I **prepared statements** ottimizzano l'esecuzione ripetuta di query simili:

**Vantaggi**:
- Il parsing viene fatto una volta
- Il piano di esecuzione può essere riutilizzato (in certi casi)
- Riduce overhead di rete
- Protegge da SQL injection

**Utilizzo**:
```sql
-- Preparare lo statement
PREPARE user_lookup AS SELECT * FROM users WHERE id = $1;

-- Eseguire con parametri
EXECUTE user_lookup(123);
EXECUTE user_lookup(456);

-- Rimuovere
DEALLOCATE user_lookup;
```

**Con protocollo esteso**:
```python
# Il driver gestisce automaticamente prepared statements
# Parametri separati dal corpo della query
cursor.execute("SELECT * FROM users WHERE id = %s", (123,))
```

**Limiti**: I piani preparati vengono invalidati se le statistiche cambiano significativamente, se lo schema delle tabelle cambia, o dopo un certo periodo di inattività.

---

## 4. Storage Engine e Buffer Pool

### 4.1 Buffer Manager

Il **buffer manager** è il componente che gestisce la cache delle pagine del database in memoria condivisa.

**Buffer pool condiviso**: La dimensione è controllata da shared_buffers. Ogni buffer è una pagina di 8KB. Il buffer pool è condiviso tra tutti i backend process.

**Buffer tag**: Ogni buffer è identificato da un "tag" che include: relfilenode (identificatore del file), fork number (main, vm, fsm, init), block number (numero della pagina nel file).

**Buffer state**: Ogni buffer ha uno stato: pinned (qualcuno lo sta usando), dirty (modificato ma non scritto), reference count (usecount).

**Hit vs Miss**: Un buffer hit significa che la pagina era già in memoria - accesso rapidissimo. Un buffer miss significa che la pagina deve essere letta dal disco - molto più lento.

### 4.2 Buffer Replacement

Quando il buffer pool è pieno e serve una nuova pagina, PostgreSQL deve scegliere quale buffer rimpiazzare. L'algoritmo è una **clock-sweep approximation**:

**Usacount tracking**: Ogni buffer mantiene un contatore usecount. Quando un buffer viene acceduto, usecount viene incrementato (fino a un massimo, tipicamente 5). Quando il clock sweep gira, usecount viene decrementato.

**Victim selection**: Il clock sweep cerca il primo buffer con usecount = 0. Questo buffer viene scelto come vittima - la sua pagina viene se necessario scritta (se dirty), e la nuova pagina viene caricata.

**Pin count**: Un buffer non può essere rimpiazzato se ha pin_count > 0 (qualcuno lo sta usando attivamente).

**Algoritmo: Clock Sweep Approximation**:
1. Mantieni un puntatore (clock hand) che gira circularmente
2. Per ogni buffer toccato: usecount = min(usecount + 1, max)
3. Per ogni buffer esaminato: usecount = usecount - 1
4. Prima buffer con usecount = 0 diventa vittima

Questo approccio è efficiente O(1) per la selezione e approssima LRU senza il costo di mantenere una lista ordinata.

### 4.3 Page Layout

Ogni pagina nel database è esattamente **8KB** (8192 bytes) e ha una struttura fissa:

**PageHeaderData** (24 bytes): Contiene:
- pd_lsn: WAL LSN dell'ultima modifica
- pd_tli: Timeline ID
- pd_flags: Flag (has free line pointers, etc.)
- pd_lower: Offset all'inizio dello spazio libero
- pd_upper: Offset alla fine dello spazio libero
- pd_special: Offset per dati speciali (indici)
- pd_pagesize_version: Dimensione pagina e versione
- pd_prune_xid: Transaction ID più vecchio che potrebbe essere rimosso

**ItemIdData** (array): Ogni entry (4 bytes) contiene:
- lp_off: Offset della tuple nella pagina
- lp_len: Lunghezza della tuple
- lp_flags: Flag (LP_USED, LP_REDIRECT, LP_DEAD)

**Tuple data**: Le tuple effettive sono memorizzate dopo l'array ItemId. Ogni tuple include:
- Null bitmap: bit per ogni colonna nullable
- Tuple header (da 23 a 27 bytes): xmin, xmax, ctid, etc.
- Dati delle colonne

**Special space**: Spazio riservato per usi specifici degli indici. Per le tabelle, è tipicamente 0.

### 4.4 Visibility Map

La **visibility map** è una struttura di ottimizzazione che traccia quali pagine contengono solo tuple visibili a tutte le transazioni.

**Struttura**: Un bit per ogni pagina della tabella. Se il bit è 1, tutte le tuple nella pagina sono visibili a tutte le transazioni.

**Utilizzo**:
- **Index Only Scan**: Se una pagina è "all visible", l'executor può restituire dati solo dall'indice senza accedere alla heap.
- **VACUUM**: Il vacuum salta le pagine "all visible" perché non contenne tuple che possono essere recuperate.

**Aggiornamento**: La visibility map viene aggiornata durante VACUUM. Prima di una pagina viene considerata "all visible", tutte le sue tuple devono essere visibili a tutte le transazioni.

### 4.5 Ring Buffers

I **ring buffers** sono buffer temporanei usati per operazioni specifiche che non devono competere per il buffer pool principale.

**Sequential scans**: Durante una scansione sequenziale, il reader usa un ring buffer di dimensione configurabile (effetive_cache_size / 4). Questo permette di缓冲izzare le letture ahead of processing.

**Temporary results**: Le tabelle temporanee e i risultati intermedi usano ring buffers invece del buffer pool principale. Questo evita di espellere dati utili dalla cache.

**Non-replacement**: I ring buffers non usano il meccanismo di replacement normale. Sono scartati quando l'operazione termina.

**Vantaggi**: Evita che scansioni large sequential non riempiranno il buffer pool con dati che potrebbero non essere riutilizzati.

---

## 5. Query Execution Pipeline

### 5.1 Parser

Il **parser** trasforma la query SQL in una rappresentazione interna processabile. Il parsing avviene in tre fasi:

**Lexical analysis (scanner)**: Il lexer tokenizza la stringa SQL in token: keywords (SELECT, FROM), identificatori, operatori, literal. Lo scanner è generato con flex e riconosce la grammatica SQL.

**Syntax analysis (parser)**: Il parser verifica che la query abbia una struttura sintattica valida e costruisce un parse tree. Il parser è generato con bison e segue la grammatica SQL standard. Il parse tree rappresenta la struttura grammaticale della query senza considerare il significato.

**Semantic analysis**: Il parser controlla anche aspetti semantici base:
- Verifica che i riferimenti a tabelle e colonne esistano
- Verifica che i tipi di dati siano compatibili
- Risolve i nomi (table.column → tabella specifica)

### 5.2 Analyzer/Rewriter

L'**analyzer** (o Analyzer/Rewriter) trasforma il parse tree in un query tree con informazioni semantiche complete:

**Query tree**: Rappresentazione interna che include:
- targetlist: Liste di espressioni da restituire
- range tables: Tabelle referenziate
- qual conditions: Condizioni WHERE
- join tree: Struttura dei join
- group clause: Clausole GROUP BY
- having clause: Clausola HAVING
- sort clause: Clausola ORDER BY

**Query rewrite rules**: Il rewriter applica regole di riscrittura:
- **View expansion**: Sostituisce le viste con la loro definizione
- **Rule system**: Applica regole CREATE RULE
- **Subquery flattening**: Semplifica subquery in join dove possibile
- **Constraint pushing**: Spinge i vincoli più vicino alle tabelle

**Constraint validation**: Verifica che la query rispetti i constraint del database: foreign key, unique, check constraints.

### 5.3 Optimizer

L'**optimizer** è il cuore del query processing. Genera e valuta diversi piani di esecuzione, selezionando quello con costo stimato minore.

**Cost model**: L'optimizer stima il costo di ogni operazione basandosi su:
- Statistiche: cardinalità delle tabelle, distribuzione dei valori, correlazione
- Costi hardware: sequenza vs random I/O, CPU per row processing
- Configurazione: random_page_cost, seq_page_cost

**Join order optimization**: Per query con multiple tabelle, l'optimizer deve decidere l'ordine dei join. Usa algoritmi come:
- Exhaustive search per pochi join
- Genetic algorithm per molti join
- Heuristic (greedy) per molti join

**Join methods**: L'optimizer sceglie il metodo di join migliore:
- Nested loop join: per join con piccole tabelle o indici
- Hash join: per join di grandi tabelle senza indici
- Merge join: per join su dati già ordinati

**Plan space**: L'optimizer esplora uno spazio di piani ma non può esplorare tutto. Limita la ricerca con:
- Limit su subquery
- Limit su join order
- Pruning basato su constraint

### 5.4 Executor

L'**executor** esegue il piano di query selezionato, producendo risultati per il client.

**Node-based execution**: Il piano è un albero di nodi. Ogni nodo implementa un'operazione specifica:
- Scan nodes: Sequential Scan, Index Scan, Index Only Scan, Bitmap Scan
- Join nodes: Nested Loop, Hash Join, Merge Join
- Modification nodes: Insert, Update, Delete
- Aggregation nodes: Sort, Hash Aggregation, Group
- Result node: Per query senza from

**Iterator model**: L'executor usa un modello iteratore: ogni nodo fornisce una tuple alla volta quando richiesto dal nodo padre. Questo evita di materializzare interi risultati in memoria.

**Expression evaluation**: Le espressioni nel piano vengono valutate per ogni tupla: calcoli aritmetici, funzioni, cast di tipo.

**Projection**: Le colonne finali vengono proiettate nel formato richiesto dal client.

**Sorting**: ORDER BY viene implementato con sort in-memory o external merge sort se i dati non fit in memory.

### 5.5 Parallel Execution

PostgreSQL supporta l'**esecuzione parallela** per query che possono beneficiare di multiple CPU:

**Parallel query setup**:
```sql
SET max_parallel_workers_per_gather = 4;
SET parallel_tuple_cost = 0.01;
SET parallel_setup_cost = 100;
```

**Parallel sequential scan**: Multiple worker process scansionano la tabella in parallelo, dividendo le pagine tra loro. I risultati vengono poi combinati.

**Parallel hash join**: La tabella hash viene costruita in parallelo, poi i worker processano le partition in parallelo.

**Parallel aggregation**: L'aggregazione viene fatta in due fasi: ogni worker aggrega parzialmente, poi i risultati parziali vengono combinati.

**Limitazioni**: Non tutte le operazioni supportano parallelismo. Bitmap scan, index scan su tabelle piccole, e query con subquery potrebbero non beneficiare.

---

## 6. Catalogo di Sistema

### 6.1 pg_catalog

Il **system catalog** è l'insieme di tabelle che memorizzano i metadati del database. È implementato come un insieme di tabelle normali nel schema pg_catalog.

**pg_class**: Il catalogo principale che descrive tutte le relazioni (tabelle, indici, viste, sequenze, etc.). Ogni riga rappresenta una relazione con informazioni su: relname (nome), relnamespace (schema), reltype (tipo di dati), relowner (proprietario), relkind (tipo: r=table, i=index, v=view, etc.), relfilenode (file fisico).

**pg_attribute**: Memorizza informazioni su ogni colonna di ogni tabella. Include: attname (nome), attrelid (tabella padre), atttypid (tipo), attlen (lunghezza), attnum (numero ordinale), attndims (numero dimensioni per array), attnotnull (nullable), etc.

**pg_proc**: Catalogo delle funzioni. Include: proname (nome), pronamespace (schema), proowner (proprietario), prokind (tipo: f=function, p=procedure), proargs (argomenti), prosrc (codice sorgente).

**pg_type**: Catalogo dei tipi di dati. Include: typname (nome), typnamespace (schema), typowner (proprietario), typlen (lunghezza), typbyval (passed by value), etc.

### 6.2 System Catalogs

Altri cataloghi essenziali:

**pg_database**: Elenca i database nel cluster. Ogni cluster PostgreSQL può contenere molteplici database. Colonne: datname (nome), datdba (owner), encoding, datcollate, datctype, etc.

**pg_tablespace**: Catalogo dei tablespace. Include: spcname (nome), spcowner (proprietario), spcacl (permissions), spcpath (percorso filesystem).

**pg_namespace**: Catalogo degli schemi. Schema "pg_catalog" contiene i cataloghi di sistema, "public" è lo schema default per gli oggetti utente.

**pg_authid**: Catalogo dei ruoli (utenti e gruppi). Include: rolname, rolsuper, rolcanlogin, rolpassword, rolvaliduntil, etc.

**pg_shdepend**: Dipendenze tra oggetti. Traccia quali oggetti dipendono da altri (es. una view che dipende da una tabella).

**pg_index**: Informazioni specifiche sugli indici. Include: indrelid (tabella), indexrelid (indice), indkey (colonne indicizzate), indoption (opzioni).

### 6.3 Information Schema

L'**information schema** è una vista standard SQL che espone i metadati in modo portatile:

**information_schema.tables**: Elenca tutte le tabelle. Colonne: table_catalog, table_schema, table_name, table_type.

**information_schema.columns**: Elenca tutte le colonne. Include: table_schema, table_name, column_name, data_type, is_nullable, column_default.

**information_schema.views**: Elenca le viste. Include: table_schema, table_name, definition.

**information_schema.table_constraints**: Elenca i constraint. Include: constraint_name, table_name, constraint_type.

**information_schema.referential_constraints**: Informazioni sulle foreign key.

Vantaggio dell'information schema: portabilità tra database SQL-compliant. Svantaggio: non espone tutte le funzionalità PostgreSQL (es. informazioni sugli indici parziali, operatori).

### 6.4 Catalog Access

I cataloghi possono essere interrogati come tabelle normali:

```sql
-- Tabelle nello schema public
SELECT * FROM pg_tables WHERE schemaname = 'public';

-- Colonne di una tabella
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users';

-- Indici su una tabella
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'users';

-- Statistiche delle tabelle
SELECT * FROM pg_stat_user_tables;

-- Proprietà delle colonne
SELECT * FROM pg_attribute WHERE attrelid = 'users'::regclass;
```

### 6.5 Catalogo Esteso

Le **estensioni** aggiungono voci al catalogo:

**pg_extension**: Elenca le estensioni installate. Colonne: extname, extversion, extconfig, extcondition.

**pg_config**: Informazioni sulle opzioni di compilazione di PostgreSQL (disponibile se compilato con --configure).

**pg_depend**: Traccia le dipendenze tra oggetti. Usato per CASCADE drops e per tracciare ciò che deve essere invalidato quando un oggetto cambia.

---

## 7. Memory Architecture

### 7.1 Memory Contexts

I **memory contexts** sono la base della gestione della memoria in PostgreSQL. Un context è una struttura che gestisce l'allocazione e deallocazione di memoria come un gruppo.

**TopMemoryContext**: Il context radice da cui derivano tutti gli altri. Non dovrebbe essere usato direttamente per allocazioni normali - serve come genitore per altri contesti.

**ErrorContext**: Usato per gestire la memoria durante l'elaborazione degli errori. Quando si verifica un errore, questo context viene ripulito per prevenire memory leaks.

**PortalContext**: Contiene i piani di query e i risultati per la sessione corrente. Ogni portal (statement preparato o cursor) ha il suo spazio qui.

**CacheMemoryContext**: Per la cache delle query (prepared statements), la cache delle relazioni (tabelle, indici), e altre strutture cache.

Ogni context gestisce l'allocazione con:
- Allocazione (palloc): prende memoria dal context corrente
- Deallocazione individuale: può liberare blocchi specifici
- Reset: libera tutta la memoria del context in una volta
- Delete: distrugge il context e toda la sua memoria

### 7.2 Allocation Types

PostgreSQL offre diversi meccanismi di allocazione:

**palloc()**: Funzione base di allocazione PostgreSQL. Alloca memoria nel context corrente. Esempi: palloc(), palloc0() (azzera la memoria).

**MemoryContextAlloc()**: Allocazione esplicita in un context specifico. Più controllo sul dove viene allocata la memoria.

**C standard (malloc, free)**: Usato raramente e solo per interoperabilità con codice C esterno. Non è tracciato dai context - potenziale per memory leaks.

```c
// Esempio di allocazione in C
void *my_data = palloc(size);
pfree(my_data);

// Con context specifico
void *my_data = MemoryContextAlloc(TopMemoryContext, size);
```

### 7.3 Memory Pools

I **memory pools** sono configurazioni che determinano quanta memoria è disponibile per diverse operazioni:

**work_mem**: Memoria disponibile per operazioni di sorting e hashing. Default: 4MB. Per query complesse con ORDER BY, hash join, o hash aggregation:
```sql
SET work_mem = '256MB';  -- per una sessione
```
Valori più alti migliorano performance per query grandi ma consumano più memoria per sessione.

**maintenance_work_mem**: Memoria per operazioni di manutenzione. Default: 64MB. Usato per: VACUUM, CREATE INDEX, REINDEX, ALTER TABLE ADD COLUMN:
```sql
SET maintenance_work_mem = '1GB';  -- prima di grandi operazioni
```

**temp_buffers**: Buffer per tabelle temporanee. Default: 8MB. Impostato per sessione:
```sql
SET temp_buffers = '256MB';
```

**effective_cache_size**: Suggerimento per l'optimizer sulla cache disponibile. Non alloca memoria, influenza solo i piani:
```sql
SET effective_cache_size = '8GB';
```

### 7.4 Local Memory

La **memoria locale** è specifica per ogni backend process - non è condivisa con altri processi.

Ogni backend ha la propriaallocazione:
- Stack: per le variabili locali e chiamate di funzione
- Context privati: TopMemoryContext del backend, PortalContext
- Session state: variabili di sessione, transazioni

La memoria locale viene deallocata quando:
- La sessione termina
- Un contesto viene resettato (es. alla fine di una transazione)
- Un portale viene chiuso

Monitoraggio della memoria:
```sql
-- Memoria usata dal backend corrente
SELECT * FROM pg_backend_memory_contexts;

-- Statistiche di memoria
SELECT * FROM pg_memmem_usage();
```

### 7.5 Large Objects

PostgreSQL gestisce oggetti grandi (> 1 page, ~8KB) con meccanismi speciali:

**TOAST (The Oversized-Attribute Storage Technique)**: Per colonne di grandi dimensioni in tabelle normali:
- Se una colonna supera ~2KB, viene compressa
- Se ancora troppo grande, viene frammentata in multiple row
- Gestito automaticamente dal sistema

**pg_largeobject**: Per oggetti binari grandi (immagini, file):
```sql
-- Creare large object
SELECT lo_from_bytea(0, decode('...', 'hex'));

-- Leggere large object
SELECT lo_get(12345);

-- Esportare
SELECT lo_export(12345, '/path/to/file');
```

**Streaming**: Per upload/download di grandi oggetti, PostgreSQL supporta streaming via protocollo:
- lo_open() con inv_write = true
- lo_write() in chunks
- lo_close()

**External storage**: Per dati che non devono essere nel database:
- COPY con binary mode
- PostgreSQL FDW per dati esterni

---

## 8. Disk Layout

### 8.1 Data Directory

La **data directory** (PGDATA) è la directory root del cluster PostgreSQL. La sua struttura è standard:

**base/**: Contiene le sottodirectory per ogni database nel cluster. Ogni database ha una directory identificata dall'OID. All'interno, i file delle tabelle e degli indici: 1/ (database OID 1), 16384/ (database OID 16384), etc.

**global/**: Contiene tabelle e indici condivisi a livello di cluster. Include: pg_control, pg_dboidmap, pg_internal.init. Questo è il "database 0".

**pg_wal/**: Directory del Write-Ahead Log. Contiene i segmenti WAL (default 16MB ciascuno). Da PostgreSQL 10+: pg_wal (precedentemente pg_xlog).

**pg_xact/**: Directory del transaction commit log (CLOG). Memorizza lo stato delle transazioni (committed, aborted, in-progress). File da 256KB.

**pg_subtrans/**: Sottotransaction log. Per gestire le subtransactions (savepoints).

**pg_notify/**: Per LISTEN/NOTIFY.

**pg_replslot/**: Replication slots.

**pg_serial/**: Informazioni su serializable transactions.

**pg_snapshots/**: Esportati snapshot.

**pg_dynshmem/**: Dynamic shared memory.

**pg_stat/**: File per statistics.

**pg_tmp/**: File temporanei.

### 8.2 Tablespace Layout

I **tablespace** permettono di specificare dove memorizzare i dati su filesystem:

**Default tablespace**: pg_default (i file sono in base/<oid>/).

**Tablespace personalizzati**: Creati con CREATE TABLESPACE:
```sql
CREATE TABLESPACE fast_storage LOCATION '/mnt/ssd/data';
CREATE TABLE users (...) TABLESPACE fast_storage;
```

**Layout**: I tablespace mappano a directory nel filesystem:
- Ogni tablespace ha una directory nel percorso specificato
- Contains symbolic links in base/ che puntano ai file reali

**pg_tablespace catalog**: Traccia i tablespace nel database:
```sql
SELECT spcname, spclocation FROM pg_tablespace;
```

### 8.3 File Organization

L'**organizzazione dei file** ottimizza l'I/O per tabelle grandi:

**Filenode**: Ogni relazione (tabella, indice) è identificata da un filenode (numero). Il file fisico ha nome <filenode> nella directory del database.

**Relation forks**: Ogni relazione può avere diversi "fork":
- main: dati principali (heap per tabelle, btree per indici)
- vm: visibility map
- fsm: free space map
- init: per sequence

**Segment size**: Per tabelle grandi (> 1GB), i file vengono segmentati:
- <filename>.1, <filename>.2, etc.
- Ogni segmento è 1GB di default (controllabile con --with-segsize)

**File naming**: Per una tabella con relfilenode 12345:
- 12345: prima porzione dei dati
- 12345.1: seconda porzione (se > 1GB)
- 12345_vm: visibility map
- 12345_fsm: free space map

### 8.4 Checkpoint Files

I **checkpoint** sono punti di sincronizzazione salvati su disco:

**pg_control**: File fondamentale contenente:
- Database cluster OID
- WAL LSN del checkpoint
- Timeline ID
- Stato del database (shutting_down, in archive recovery, etc.)
-Checkpoint LSN, time, etc.

**Backup label file**: Creato durante pg_basebackup:
- Contiene informazioni sul backup
- WAL starting point
- Tabellepace mapping

**Tablespace map**:Durante backup, traccia la posizione dei tablespace.

### 8.5 WAL Layout

Il **WAL** (Write-Ahead Log) è organizzato in:

**Segment files**: Ogni segmento è 16MB di default (configurabile con --wal-segsize):
- Nome: 000000010000000000000001 (formato: timeline-high, xlogid-high, segment)
- Posizionati in pg_wal/
- Riciclati automaticamente quando non più necessari

**WAL record**: Ogni modifica produce un record:
- Header: LSN, transaction ID, length, type
- Body: dati della modifica

**WAL Archiviazione**: Se abilitata (archive_mode = on):
- I segmenti completi vengono copiati altrove
- Configurato con archive_command

**Streaming replication**: WAL viene trasmesso in streaming ai replica prima di essere scritto su disco locale del replica

---

## 9. Background Processes

### 9.1 Background Writer

Il **background writer (bgwriter)** è un processo che scrive le pagine "dirty" (modificate) dal buffer pool su disco in background, riducendo il lavoro al momento del checkpoint.

**Funzioni principali**:
- Scan periodica del buffer pool
- Scrittura di pagine dirty che non sono state usate di recente
- Riduzione del numero di dirty pages al momento del checkpoint
- Cleaning del buffer pool

**Configurazione**:
```sql
bgwriter_delay = 200ms  -- default: 200ms
bgwriter_lru_maxpages = 100  -- max pages per round
bgwriter_lru_multiplier = 2.0  -- cleaning multiplier
bgwriter_flush_after = 512kB  -- flush after this much
```

**Comportamento**: Il bgwriter esegue un loop con bgwriter_delay tra ogni iterazione. In ogni iterazione, tenta di scrivere un numero di pagine basato su:
- Numero di dirty pages nel buffer pool
- Moltiplicatore bgwriter_lru_multiplier
- Limite bgwriter_lru_maxpages

**Tuning**: Un bgwriter aggressivo riduce il lavoro al checkpoint ma usa I/O in background. Un bgwriter conservativo lascia più dirty pages ma consuma meno risorse.

### 9.2 WAL Writer

Il **WAL writer** scrive il contenuto del WAL buffer su disco in modo asincrono:

**Funzioni**:
- Scrive i WAL buffer nel WAL file
- Gestisce la sincronizzazione periodica
-Minimizza la latenza di scrittura

**Configurazione**:
```sql
wal_writer_delay = 200ms  -- default
wal_writer_flush_after = 1MB  -- force flush after this
wal_sync_method = fdatasync  -- sync method (default)
```

**Comportamento**: Il WAL writer non aspetta che un record sia sincronizzato prima di tornare al client. La sincronizzazione avviene:
- Dopo wal_writer_delay
- Dopo wal_writer_flush_after bytes
- Al momento del commit (se synchronous_commit = on)

### 9.3 Autovacuum Launcher

L'**autovacuum** è il sistema di manutenzione automatica:

**Componenti**:
- **autovacuum launcher**: processo che gira in background, lancia i worker
- **autovacuum worker**: processi che eseguono VACUUM e ANALYZE sulle singole tabelle

**Funzioni**:
- **VACUUM**: Rimuove tuple morte (cancellate o obsolete), recupera spazio, aggiorna visibility map
- **ANALYZE**: Aggiorna statistiche per l'optimizer
- **Freeze**: Previene transaction ID wraparound

**Configurazione**:
```sql
autovacuum = on  -- enable
autovacuum_max_workers = 3  -- number of workers
autovacuum_naptime = 1min  -- delay between launcher cycles

-- Per tabella specifica
ALTER TABLE mytable SET (
    autovacuum_vacuum_threshold = 10000,
    autovacuum_vacuum_scale_factor = 0.1
);
```

**Trigger automatici**:
- vacuum: n_dead_tup > vacuum_threshold + vacuum_scale_factor * n_live_tup
- analyze: n_changes_since_analyze > analyze_threshold + analyze_scale_factor * n_live_tup

### 9.4 Statistics Collector

Il **statistics collector** raccoglie informazioni sulle attività del database:

**Statistiche raccolte**:
- pg_stat_database: attività per database
- pg_stat_user_tables: statistiche per tabella
- pg_stat_user_indexes: statistiche per indice
- pg_stat_activity: attività dei backend
- pg_stat_replication: replica status

**Funzionamento**:
- I backend inviano statistiche al collector (via shared memory)
- Il collector aggrega e memorizza
- Le view pg_stat_* espongono le statistiche

**Configurazione**:
```sql
track_activities = on  -- track query in activity
track_counts = on  -- track table/index counts
track_functions = pl  -- track function calls
track_io_timing = on  -- track I/O timing
```

### 9.5 Other Background Processes

Altri processi background essenziali:

**Checkpointer**: Processo dedicato per i checkpoint (se abilitato). Gestisce la scrittura sincronizzata delle dirty pages durante il checkpoint.

**WAL Writer**: Già descritto sopra.

**WAL Sender**: Per streaming replication. Invia il WAL al replica. Parametri configurabili: wal_sender_delay, wal_keep_size.

**WAL Receiver**: Per replica. Riceve il WAL dal primary. Gestisce il replay.

**Logical Replication Workers**: Per replica logica. Ogni subscription ha worker dedicati.

**Archive Receiver**: Se WAL archiving è abilitato, gestisce l'archiviazione.

**Log Writer**: Scrive i log del server su disco. Ha il proprio processo per non bloccare le operazioni.

**Syslogger**: Gestisce i log di sistema in un file separato.

Monitoraggio dei processi:
```sql
SELECT pid, usename, application_name, state, query 
FROM pg_stat_activity 
WHERE backend_type = 'background worker';
```

---

## 10. Recovery e Checkpoints

### 10.1 Recovery Basics

Il **recovery** in PostgreSQL è basato sul WAL (Write-Ahead Log). Quando il database si riavvia dopo un crash, usa il WAL per tornare a uno stato consistente.

**Principi del recovery**:
- **Redo**: Riapplicare le transazioni committate che non sono state scritte nelle pagine dati
- **Undo**: Annullare le transazioni che non sono state committate

**Crash recovery**: Dopo un crash:
1. PostgreSQL legge il pg_control per trovare l'ultimo checkpoint valido
2. Legge il WAL dal checkpoint
3. Riapplica le operazioni delle transazioni committate
4. Annulla (non applica) le operazioni delle transazioni non committate

Il recovery è automatico e avviene all'avvio del server. Non richiede intervento dell'amministratore.

### 10.2 Checkpoint Trigger

I **checkpoint** sono punti di sincronizzazione dove il database garantisce che tutte le dirty pages siano scritte su disco.

**Trigger automatici**:
- **checkpoint_timeout**: Default 5 minuti. Forza un checkpoint dopo questo periodo.
- **checkpoint_completion_target**: Default 0.9. Determina quanto tempo del periodo il checkpoint dovrebbe usare per completare.
- **max_wal_size**: Default 1GB. Trigger checkpoint quando il WAL supera questa dimensione.

**Trigger manuali**:
```sql
CHECKPOINT;  -- checkpoint completo
CHECKPOINT(FAST);  -- checkpoint veloce
CHECKPOINT(WAIT);  -- checkpoint che aspetta il completamento
```

**Checkpoint during backup**: pg_basebackup crea un checkpoint all'inizio per garantire consistenza del backup.

### 10.3 Recovery Process

Il **processo di recovery** completo:

**Fase 1: Localizzazione checkpoint**
- Leggi pg_control
- Trova la posizione (LSN) dell'ultimo checkpoint valido
- Determina la timeline

**Fase 2: Analisi**
- Scan il WAL dal checkpoint
- Identifica le transazioni in corso al momento del crash
- Determina quali pagine sono dirty e il loro stato

**Fase 3: Redo**
- Riapplica ogni WAL record dal checkpoint
- Per ogni record, verifica che la pagina non sia già aggiornata (usando LSN)
- Applica le modifiche alle pagine dati
- Questo garantisce che tutte le transazioni committate siano persistite

**Fase 4: Undo**
- In PostgreSQL, le modifiche delle transazioni non committate non sono nelle pagine dati (sono solo nel WAL)
- Il recovery semplicemente non le applica
- Le transazioni incomplete vengono "dimenticate"

### 10.4 Point-in-Time Recovery

Il **PITR (Point-in-Time Recovery)** permette di recoverire il database a un momento specifico, non solo al momento del backup:

**Prerequisiti**:
- Backup base (pg_basebackup o pg_dump)
- WAL archiviati (archive_mode = on)
- Configurazione di recovery

**Configurazione recovery** (PostgreSQL 13+):
```sql
-- postgresql.conf o recovery configuration
restore_command = 'cp /archive/wal/%f %p'
recovery_target_time = '2026-05-04 15:30:00'
recovery_target_action = 'promote'
```

**Target types**:
- **time**: Timestamp specifico
- **xid**: Transaction ID
- **lsn**: WAL LSN
- **name**: Named restore point

**Target inclusività**:
```sql
recovery_target_inclusive = true  -- include il target
```

**Azione post-recovery**:
- promote: promuovi a standalone server
- pause: ferma in recovery mode
- shutdown: spegni il server

### 10.5 Streaming Recovery

La **replica streaming** è una forma di hot standby dove il replica riceve WAL in streaming:

**Componenti**:
- **WAL Sender** (sul primary): Invia WAL al replica
- **WAL Receiver** (sul replica): Riceve e applica WAL
- **Replication Slot**: Mantiene traccia di quali WAL sono stati inviati

**Configurazione primary**:
```sql
wal_level = replica  -- o logical
max_wal_senders = 10
wal_keep_size = 1GB
```

**Configurazione replica** (recovery.conf):
```sql
primary_conninfo = 'host=primary port=5432 user=replicator'
```

**Replication slot**: Garantisce che il primary non rimuova WAL finché il replica non li ha ricevuti:
```sql
-- Sul primary
CREATE REPLICATION SLOT my_slot;

-- Monitorare
SELECT * FROM pg_replication_slots;
```

**Lag monitoring**:
```sql
-- Sul primary
SELECT * FROM pg_stat_replication;

-- Sul replica
SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;
```

**Promoting replica**: Per failover:
```sql
-- Sul replica
pg_ctl promote -D /var/lib/postgresql/data

-- O
SELECT pg_promote();
```

Il replica diventa un server standalone con i dati fino al momento del failover.

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*