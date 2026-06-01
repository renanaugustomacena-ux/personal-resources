# Teoria Fondamentale dei Database Relazionali

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
1. Introduzione ai Database Relazionali
2. Evoluzione Storica dei Sistemi di Gestione Dati
3. Concetti Fondamentali del Modello Relazionale
4. Architettura dei DBMS Relazionali
5. Componenti Core di un Sistema Relazionale
6. Transaction Processing Fundamentals
7. Concurrency Control Basics
8. Recovery e Durability
9. Query Processing e Optimization
10. Benchmark e Performance Metrics

---

## 1. Introduzione ai Database Relazionali

### 1.1 Definizione e Concetti Base

Un database relazionale rappresenta un insieme organizzato di dati correlati, memorizzati in tabelle composte da righe e colonne. Il termine "relazionale" deriva dalla teoria degli insiemi e dalla matematica delle relazioni, non dal fatto che le tabelle siano "collegate" tra loro attraverso relazioni. Questa distinzione è fondamentale per comprendere la vera natura del modello relazionale.

Il modello relazionale fu proposto per la prima volta da Edgar F. Codd, un ricercatore IBM, nel 1970 in un articolo seminal intitolato "A Relational Model of Data for Large Shared Data Banks". Codd, lavorando presso il IBM Research Laboratory di San Jose, sviluppò una teoria matematica rigorosa per la gestione dei dati che combinava semplicità concettuale con potenza espressiva. Prima del modello relazionale, i database erano gestiti attraverso modelli gerarchici e reticolari, che richiedevano una conoscenza approfondita della struttura fisica dei dati per poter essere utilizzati efficacemente.

Il paradigma relazionale introdusse un'astrazione fondamentale: la separazione tra il livello logico e il livello fisico dei dati. Gli utenti e le applicazioni interagiscono con i dati attraverso un modello astratto di tabelle, senza necessità di conoscere come questi dati siano fisicamente memorizzati. Questa astrazione viene definita "indipendenza dei dati" (data independence) ed è uno dei principali vantaggi del modello relazionale rispetto ai suoi predecessori.

Un database relazionale organizza le informazioni in strutture chiamate tabelle, dove ogni tabella rappresenta un'entità del dominio applicativo. Una tabella è composta da un insieme di colonne (attributi) che definiscono le proprietà delle entità, e da un insieme di righe (tuple) che rappresentano le istanze concrete delle entità stesse. Ogni riga in una tabella rappresenta un record univoco, identificato da una chiave primaria che garantisce l'unicità all'interno della tabella.

### 1.2 Componenti Fondamentali del Modello

Il modello relazionale si basa su tre componenti fondamentali che insieme formano la struttura teorica completa del sistema: la struttura dei dati, le operazioni possibili sui dati, e i vincoli di integrità che garantiscono la correttezza dei dati stessi. Ciascuno di questi componenti gioca un ruolo cruciale nel determinare il comportamento e le proprietà di un database relazionale.

La **struttura dei dati** nel modello relazionale è definita attraverso il concetto di relazione, che può essere pensata come una tabella bidimensionale. Ogni relazione ha un nome univoco all'interno del database e possiede un insieme di attributi, ciascuno con un nome e un dominio. Il dominio rappresenta l'insieme dei valori ammissibili per un attributo e può essere definito in modo esplicito (enumeral) o attraverso un tipo di dato predefinito (intero, stringa, data, ecc.). La cardinalità di una relazione indica il numero di tuple contenute, mentre il grado indica il numero di attributi.

Le **operazioni** sui dati sono definite attraverso l'algebra relazionale e il calcolo relazionale, due formalismi matematici che forniscono la base teorica per il linguaggio SQL. L'algebra relazionale opera su relazioni per produrre nuove relazioni, attraverso operatori come selezione, proiezione, unione, differenza, prodotto cartesiano e join. Il calcolo relazionale, invece, fornisce un approccio dichiarativo che specifica il risultato desiderato senza indicare il procedimento per ottenerlo.

I **vincoli di integrità** rappresentano le regole che i dati devono rispettare per mantenere la consistenza del database. Questi vincoli possono essere definiti a livello di tabella (come la chiave primaria e le chiavi esterne) o a livello di database (come le asserzioni). Il modello relazionale supporta diversi tipi di vincoli: vincoli di dominio (che limitano i valori ammissibili per ciascun attributo), vincoli di chiave (che garantiscono l'unicità delle tuple), vincoli di integrità referenziale (che mantengono la coerenza tra tabelle correlate), e vincoli di integrità generici (asserzioni definite dall'utente).

### 1.3 Vantaggi del Modello Relazionale

Il modello relazionale offre numerosi vantaggi che lo hanno reso lo standard de facto per la gestione dei dati nelle applicazioni enterprise per oltre quattro decenni. Questi vantaggi derivano dalla solida base teorica su cui il modello è costruito e dalla sua eleganza architetturale.

Il primo vantaggio significativo è l'**indipendenza dei dati**, che permette di modificare lo schema fisico senza influenzare le applicazioni che utilizzano i dati. Questa caratteristica è fondamentale per la manutenzione a lungo termine dei sistemi software, poiché consente di ottimizzare le prestazioni del database senza dover riscrivere il codice delle applicazioni. L'indipendenza dei dati si divide in due livelli: l'indipendenza logica (possibilità di modificare lo schema logico senza alterare le viste degli utenti) e l'indipendenza fisica (possibilità di modificare lo schema fisico senza alterare lo schema logico).

La **semplicità del modello** rappresenta un altro vantaggio cruciale. Il modello relazionale utilizza strutture intuitive (tabelle) che sono facili da comprendere sia per gli sviluppatori che per gli utenti finali. Questa semplicità si traduce in una curva di apprendimento meno ripida e in una più facile comunicazione tra i membri del team di sviluppo e gli stakeholder di business.

Il **linguaggio standardizzato** SQL (Structured Query Language) fornisce un'interfaccia uniforme per interagire con qualsiasi database relazionale conforme allo standard. Sebbene ogni vendor abbia estensioni proprietarie, il nucleo del linguaggio rimane consistente tra le diverse implementazioni, permettendo agli sviluppatori di trasferire le proprie competenze tra diversi sistemi con relativa facilità. Lo standard SQL è evoluto nel tempo attraverso diverse versioni (SQL-86, SQL-89, SQL-92, SQL:1999, SQL:2003, SQL:2006, SQL:2008, SQL:2011, SQL:2016, SQL:2019, SQL:2023), ciascuna introducendo nuove funzionalità e miglioramenti.

L'**integrità dei dati** è garantita attraverso vincoli dichiarativi che il database enforced automaticamente. Questo riduce la quantità di codice necessario nelle applicazioni per garantire la consistenza dei dati e minimizza il rischio di errori derivanti da implementazioni manuali. I vincoli di chiave primaria, chiave esterna, unicità, e controllo di validità sono tutti gestiti dal database in modo automatico e trasparente.

La **supporto per transazioni ACID** (Atomicity, Consistency, Isolation, Durability) rappresenta una caratteristica fondamentale per le applicazioni che richiedono affidabilità e consistenza dei dati. Le transazioni permettono di raggruppare multiple operazioni in unità atomiche che vengono eseguite completamente o non eseguite affatto, garantendo che il database rimanga in uno stato consistente anche in caso di fallimenti.

---

## 2. Evoluzione Storica dei Sistemi di Gestione Dati

### 2.1 Era Pre-Relazionale: Sistemi Gerarchici e Reticolari

Prima dell'avvento del modello relazionale, i database venivano gestiti principalmente attraverso due paradigmi: il modello gerarchico e il modello reticolare. Questi sistemi, sebbene rivoluzionari per la loro epoca, presentavano significative limitazioni che il modello relazionale avrebbe successivamente superato.

Il **sistema gerarchico** più celebre fu l'IBM Information Management System (IMS), sviluppato negli anni '60 per il progetto Apollo della NASA. IMS organizzava i dati in una struttura ad albero con relazioni padre-figlio uno-a-molti. Ogni record poteva avere un solo genitore ma poteva avere molteplici figli, creando una gerarchia rigida che rifletteva la struttura organizzativa dell'applicazione. Questo modello era efficiente per dati con una struttura naturale gerarchica, ma si rivelava problematico quando le relazioni tra i dati non seguivano questo pattern.

Il **modello reticolare** (network model) fu formalizzato dal CODASYL (Conference on Data Systems Languages) negli anni '70. Questo modello estendeva quello gerarchico permettendo relazioni molti-a-molti attraverso strutture chiamate "set". Ogni record poteva appartenere a molteplici set, permettendo rappresentazioni più flessibili dei dati. Il linguaggio di programmazione associato era il COBOL, e l'accesso ai dati richiedeva la navigazione esplicita attraverso i puntatori fisici.

Entrambi i modelli soffrivano di problemi fondamentali: la dipendenza programmatica dalla struttura fisica dei dati (rendendo le modifiche allo schema costose e rischiose), l'assenza di un linguaggio di query standardizzato (ogni applicazione doveva implementare la propria logica di accesso), e la complessità dello sviluppo (gli sviluppatori dovevano essere esperti della struttura fisica per scrivere codice efficiente). Questi problemi spinsero la ricerca verso un nuovo paradigma, culminato nel lavoro di Codd.

### 2.2 Nascita e Affermazione del Modello Relazionale

Il 1970 segna l'inizio della rivoluzione relazionale con la pubblicazione del paper di Codd. Tuttavia, l'implementazione pratica richiese quasi un decennio di ricerca e sviluppo. I primi prototipi di sistemi relazionali emersero nei laboratori di ricerca accademici e industriali, incluso il System R di IBM e il progetto Ingres all'University of California, Berkeley.

Il **System R**, sviluppato presso IBM Research tra il 1974 e il 1979, fu uno dei primi progetti ad implementare un DBMS relazionale completo. Da questo progetto emersero due contributi fondamentali: il linguaggio SEQUEL (Structured English Query Language), che divenne la base per SQL, e importanti tecniche di ottimizzazione delle query che sono ancora utilizzate nei DBMS moderni. Il System R dimostrò la fattibilità pratica del modello relazionale, sebbene non fosse destinato a diventare un prodotto commerciale.

Il progetto **Ingres** (Interactive Graphics and Retrieval System), guidato da Michael Stonebraker all'UC Berkeley, rappresentò un altro pilastro dello sviluppo dei database relazionali. Ingres introdusse concetti innovativi come le viste aggiornabili e il query optimizer basato su costi. Il codice di Ingres divenne la base per diversi prodotti commerciali, inclusi PostgreSQL e Illustra (poi acquistato da Informix).

I primi **prodotti commerciali** basati sul modello relazionale apparvero sul mercato alla fine degli anni '70 e all'inizio degli anni '80. Oracle rilasciò la prima versione commerciale nel 1979, basata sul lavoro svolto su Ingres. IBM introdusse DB2 nel 1983, estabelecendosi come leader nel mercato enterprise. Altri vendor seguirono rapidamente: Sybase, Informix, e progressivamente Microsoft con SQL Server.

### 2.3 Sviluppo dello Standard SQL

Lo **SQL** nacque come linguaggio per il modello relazionale e divenne lo standard de facto per l'interazione con i database relazionali. La standardizzazione formale iniziò nel 1986 con l'ANSI X3H2 e l'ISO, portando alla pubblicazione della prima versione dello standard SQL (SQL-86 o SQL-87).

Lo standard SQL ha subito numerose revisioni nel corso dei decenni, ciascuna aggiungendo funzionalità significative:

Lo standard **SQL-92** rappresentò un major upgrade, introducendo join espliciti (INNER, OUTER, CROSS), supporto per constraint, gestione delle transazioni, e statement per la manipolazione dello schema. Questa versione rese SQL un linguaggio completo e utilizzabile.

**SQL:1999** (SQL3) introdusse le estensioni object-oriented, le stored procedure, i trigger, i tipi definiti dall'utente, e le espressioni regolari. Questa versione segnò anche l'introduzione delle window functions, una funzionalità powerful per l'analisi dei dati.

**SQL:2003** introdusse le funzionalità di analisi statistica, le sequence, e il supporto per XML. **SQL:2006** estese il supporto per XQuery. **SQL:2008** aggiunse le truncate table e le modalità di conformità. **SQL:2011** introdusse le temporal tables. **SQL:2016** aggiunse il supporto per JSON. **SQL:2019** introdusse le columnar storage extensions e le proprietà row pattern recognition.

### 2.4 Era Moderna: Cloud, NewSQL e Multi-Model

Il XXI secolo ha portato nuove sfide e opportunità per i database relazionali. L'esplosione dei dati, le applicazioni web su larga scala, e il cloud computing hanno spinto l'evoluzione del mercato.

I **database cloud-native** come Amazon Aurora, Google Cloud Spanner, e Azure SQL Database hanno ridefinito le aspettative in termini di scalabilità, disponibilità e gestione. Questi sistemi combinano le garanzie ACID dei database relazionali con la scalabilità dei sistemi distribuiti, utilizzando tecniche innovative come il log-structured storage e la replicazione geografica.

Il movimento **NewSQL** ha prodotto sistemi che mantengono le proprietà ACID del modello relazionale mentre offrono la scalabilità dei sistemi NoSQL. Prodotti come CockroachDB, TiDB, e YugabyteDB rappresentano questa categoria, offrendo transazioni distribuite conformi ACID, SQL compatibility, e scalabilità orizzontale.

I database **multi-modello** hanno guadagnato popolarità, combinando le capacità relazionali con modelli di dati alternativi come documenti, grafi, e time-series in un singolo sistema. PostgreSQL, con le sue estensioni, e ArangoDB sono esempi di questa tendenza.

---

## 3. Concetti Fondamentali del Modello Relazionale

### 3.1 Il Modello Matematico delle Relazioni

A livello matematico, una relazione è un sottoinsieme del prodotto cartesiano di uno o più domini. Formalmente, se abbiamo domini D1, D2, ..., Dn, una relazione R è un sottoinsieme di D1 × D2 × ... × Dn. Questa definizione formale fornisce la base teorica per il funzionamento dei database relazionali e garantisce le proprietà matematiche del modello.

Un **dominio** (domain) rappresenta l'insieme dei valori ammissibili per un attributo. Ogni dominio ha un nome e può essere definito in modo primitivo (usando tipi di dati come interi, stringhe, date) o in modo enumerato (specificando esplicitamente tutti i valori possibili). In un contesto pratico, i domini sono tipicamente identificati con i tipi di dati supportati dal DBMS.

Una **n-upla** (tuple) è un elemento specifico della relazione, rappresentato come una sequenza ordinata di valori. In termini di tabella, ogni riga rappresenta una n-upla. L'ordine delle n-uple all'interno di una relazione non è significativo per la definizione matematica, poiché una relazione è un insieme (non una lista ordinata).

Una **relazione schema** definisce la struttura della relazione, specificando il nome della relazione e l'insieme degli attributi con i rispettivi domini. Ad esempio, la relazione "Impiegato" potrebbe avere attributi come ID (dominio: intero positivo), Nome (dominio: stringa di massimo 100 caratteri), DataDiNascita (dominio: data), Stipendio (dominio: decimale).

Lo **stato di una relazione** in un dato momento è l'insieme delle n-uple attualmente contenute nella relazione. Lo stato cambia nel tempo attraverso le operazioni di inserimento, modifica e cancellazione dei dati.

### 3.2 Chiavi e Vincoli di Integrità

Il concetto di **chiave** è fondamentale nel modello relazionale per garantire l'unicità e l'identificazione delle tuple. Esistono diversi tipi di chiavi, ciascuna con un ruolo specifico nel mantenimento dell'integrità dei dati.

Una **superchiave** (superkey) è un insieme di attributi che identifica unicamente ogni tupla nella relazione. Intuitivamente, nessuna tupla può avere gli stessi valori per tutti gli attributi della superchiave. La superchiave minima è chiamata chiave canditata (candidate key).

Una **chiave primaria** (primary key) è una chiave candidato scelta per identificare univocamente le tuple nella relazione. La chiave primaria deve avere valore non nullo per ogni tupla e non può contenere duplicati. È convenzione consolidata che ogni tabella abbia una e una sola chiave primaria.

Una **chiave alternativa** (alternate key) è una chiave candidato che non è stata scelta come chiave primaria. Sebbene non utilizzata come identificatore principale, una chiave alternativa può comunque avere un vincolo di unicità e può essere referenziata da chiavi esterne.

Una **chiave esterna** (foreign key) è un attributo (o insieme di attributi) in una relazione che referenzia la chiave primaria di un'altra relazione. La chiave esterna stabilisce un legame tra le due tabelle e garantisce l'integrità referenziale: il valore della chiave esterna deve corrispondere a un valore esistente nella relazione referenziata, oppure essere nullo.

I **vincoli di integrità** (integrity constraints) sono regole che definiscono quali stati del database sono validi. Il modello relazionale supporta diversi tipi di vincoli:

Il **vincolo di dominio** specifica che il valore di ogni attributo deve appartenere al dominio definito per quell'attributo. Ad esempio, lo stipendio di un impiegato deve essere un numero positivo.

Il **vincolo di chiave** garantisce che due tuple non possano avere valori identici per tutti gli attributi che formano una chiave. Questo vincolo viene enforced dal DBMS attraverso la creazione di indici unici.

Il **vincolo di integrità referenziale** assicura che ogni valore di una chiave esterna corrisponda a un valore esistente nella relazione referenziata, o sia nullo. Questo vincolo viene enforced attraverso azioni di cascading (ON DELETE, ON UPDATE) che specificano come comportarsi quando una tupla referenziata viene modificata o cancellata.

Il **vincolo di integrità dell'entità** richiede che la chiave primaria non possa avere valori nulli. Questo garantisce che ogni tupla possa essere identificata univocamente.

I **vincoli generali** (asserzioni) permettono di definire condizioni complesse che coinvolgono più tabelle e più attributi. Ad esempio, si potrebbe definire un vincolo che lo stipendio di un impiegato non possa superare lo stipendio del suo manager.

### 3.3 Valori Nulli e la Logica Trivalente

Il modello relazionale affronta il problema dei valori mancanti o sconosciuti attraverso il concetto di **valore nullo** (NULL). Il NULL rappresenta l'assenza di un valore, non un valore specifico, e la sua gestione richiede una logica speciale chiamata logica trivalente (three-valued logic, 3VL).

In SQL, il NULL ha un significato specifico: indica che il valore di un attributo è sconosciuto, non applicabile, o non ancora assegnato. Questo è diverso da una stringa vuota, da zero, o da qualsiasi altro valore specifico. La presenza dei NULL introduce complessità nelle query e nelle operazioni.

La logica trivalente introduce tre possibili valori di verità: TRUE, FALSE, e UNKNOWN. Qualsiasi comparazione che coinvolge un NULL produce il risultato UNKNOWN, non TRUE né FALSE. Questo ha implicazioni significative:

L'espressione ` WHERE column = NULL` non restituisce le righe con valore NULL perché il confronto produce UNKNOWN, non TRUE. Per verificare la presenza di valori NULL si deve usare `IS NULL` o `IS NOT NULL`.

Le operazioni di aggregazione (SUM, AVG, COUNT, etc.) tipicamente ignorano i valori NULL, ma il comportamento specifico varia a seconda della funzione e del DBMS.

Le espressioni booleane con NULL richiedono attenzione particolare: `TRUE OR NULL` produce TRUE (perché TRUE OR qualsiasi cosa è TRUE), ma `FALSE AND NULL` produce FALSE (perché FALSE AND qualsiasi cosa è FALSE). Questo comportamento può generare risultati controintuitivi se non compreso correttamente.

Le funzioni di coalescenza come COALESCE o NVL permettono di sostituire i NULL con valori predefiniti, semplificando la gestione dei valori mancanti.

### 3.4 Algebra Relazionale e Operatori Fondamentali

L'**algebra relazionale** fornisce un insieme di operatori che agiscono su relazioni per produrre nuove relazioni. Questi operatori formano la base teorica per SQL e permettono di esprimere qualsiasi manipolazione dei dati in modo formale e non ambiguo.

L'**operatore di selezione** (σ, sigma) estrae le tuple che soddisfano una condizione predicativa. La selezione reduce il numero di tuple nel risultato (cardinalità) ma mantiene tutti gli attributi della relazione originale (grado invariato). La condizione di selezione può includere comparazioni (=, <, >, ≤, ≥, ≠), connettivi logici (AND, OR, NOT), e riferimenti ad attributi.

L'**operatore di proiezione** (π, pi) estrae gli attributi specificati da una relazione, scartando gli altri. La proiezione riduce il grado della relazione (numero di attributi) ma può aumentare o diminuire la cardinalità a causa dell'eliminazione dei duplicati (a meno che non si utilizzi l'operatore di proiezione con mantenimento dei duplicati).

L'**operatore di unione** (∪) combina le tuple di due relazioni compatibili (stesso schema) in una singola relazione. L'unione rimuove i duplicati. La differenza rispetto all'unione è che l'unione include tutte le tuple che appaiono in almeno una delle due relazioni.

L'**operatore di differenza** (-) estrae le tuple che appaiono nella prima relazione ma non nella seconda. Anche le due relazioni devono essere compatibili per schema.

L'**operatore di prodotto cartesiano** (×) combina ogni tupla della prima relazione con ogni tupla della seconda, producendo una relazione con tutti gli attributi di entrambe. Questo operatore può produrre risultati molto grandi, quindi viene tipicamente combinato con selezioni per formare join.

L'**operatore di join** (⋈) combina il prodotto cartesiano con una selezione, estraendo le tuple che soddisfano una condizione di join. Esistono diversi tipi di join: inner join (solo tuple che soddisfano la condizione), left outer join (tutte le tuple della sinistra, con NULL per quelle senza match), right outer join, full outer join, e natural join (join basato su attributi con lo stesso nome).

### 3.5 Calcolo Relazionale e SQL

Il **calcolo relazionale** fornisce un approccio dichiarativo alla definizione delle query, specificando cosa si desidera ottenere senza indicare come ottenerlo. Esistono due varianti: il calcolo relazionale su tuple e il calcolo relazionale su domini.

Nel calcolo relazionale su tuple, ogni query specifica la forma delle tuple desiderate attraverso una formula. Ad esempio, la query "trova i nomi degli impiegati che guadagnano più di 50000" si esprime come: {I.Nome | Impiegato(I) ∧ I.Stipendio > 50000}.

Nel calcolo relazionale su domini, le variabili rappresentano valori individuali invece che tuple intere. La stessa query si esprimerebbe come: {N | ∃I (Impiegato(I) ∧ I.Nome = N ∧ I.Stipendio > 50000)}.

Il calcolo relazionale è equivalente in potenza espressiva all'algebra relazionale (risultato dimostrato da Codd): qualsiasi query esprimibile in algebra può essere espressa in calcolo e viceversa. Questa equivalenza è importante perché dimostra che non esiste un "limite" intrinseco in nessuno dei due formalismi.

**SQL** può essere visto come un'implementazione pratica del calcolo relazionale, con l'aggiunta di caratteristiche procedurali. La maggior parte delle query SQL può essere tradotta in espressioni di algebra relazionale e viceversa. Tuttavia, SQL introduce funzionalità che vanno oltre il modello relazionale teorico, come i valori NULL, le aggregazioni, e le subquery.

---

## 4. Architettura dei DBMS Relazionali

### 4.1 Architettura a Tre Livelli

L'architettura a tre livelli (three-schema architecture) rappresenta il modello concettuale per la organizzazione dei database, definendo tre livelli di astrazione che separano le diverse viste dei dati.

Il **livello interno** (internal schema) descrive come i dati sono fisicamente memorizzati nel sistema. Questo livello include la definizione delle strutture di memorizzazione, degli indici, dei metodi di accesso, e delle strategie di compressione. Gli amministratori del database lavorano principalmente a questo livello per ottimizzare le prestazioni.

Il **livello concettuale** (conceptual schema) rappresenta la vista logica completa del database, ignorando considerazioni di memorizzazione fisica. Questo livello definisce le tabelle, le colonne, i vincoli, le relazioni, e le viste che costituiscono il modello del dominio applicativo. È a questo livello che vengono definiti i vincoli di integrità globali.

Il **livello esterno** (external schema) definisce le viste specifiche per gli utenti o le applicazioni. Ogni vista esterna è un sottocon schema del concettuale, nascondendo dettagli non rilevanti per un particolare utente. Le viste possono essere utilizzate per implementare sicurezza (limitando l'accesso a specifiche colonne o righe) e per semplificare l'interfaccia utente.

Questa architettura fornisce l'indipendenza dei dati: le modifiche a un livello non richiedono cambiamenti agli altri livelli. L'indipendenza logica permette di modificare lo schema concettuale senza influenzare le viste esterne. L'indipendenza fisica permette di modificare lo schema interno (ad esempio, aggiungere indici) senza modificare lo schema concettuale.

### 4.2 Componenti del Database Engine

Un DBMS relazionale è composto da diversi componenti che collaborano per gestire i dati in modo efficiente e affidabile.

Il **parser** analizza le query SQL, verificando la sintassi e costruendo un parse tree che rappresenta la struttura grammaticale della query. Il parser verifica l'esistenza delle tabelle e delle colonne referenziate e risolve i nomi degli oggetti.

Il **query optimizer** è il componente che determina il modo più efficiente per eseguire una query. L'optimizer analizza il parse tree, considera molteplici piani di esecuzione, stima il costo di ciascun piano (basato su statistiche sullo stato del database), e seleziona il piano con il costo stimato minore. Questo è uno dei componenti più complessi di un DBMS.

L'**executor** esegue il piano di query selezionato dall'optimizer, iterando attraverso gli operatori fisici che implementano le operazioni logiche (scan, join, sort, aggregation, etc.). L'executor gestisce il flusso dei dati tra gli operatori e materializza i risultati intermedi.

Il **storage engine** gestisce la memorizzazione физиica dei dati su disco e il loro recupero. Include componenti per la gestione dei buffer (caching delle pagine in memoria), la gestione dei file di dati e degli indici, il logging delle transazioni, e il recovery.

Il **transaction manager** coordina l'esecuzione delle transazioni, garantendo le proprietà ACID. Gestisce il locking, la concorrenza, e il recovery in caso di fallimenti.

Il **recovery manager** assicura la durabilità dei dati anche in caso di fallimenti di sistema. Utilizza tecniche come write-ahead logging (WAL), checkpointing, e rollforward/rollback delle transazioni.

### 4.3 Gestione della Memoria e Buffer Pool

La gestione efficace della memoria è cruciale per le prestazioni di un database relazionale. Il **buffer pool** è la porzione di memoria principale dedicata alla caching delle pagine del database.

Quando una query richiede dati, il storage engine verifica prima se la pagina è già presente nel buffer pool. Se presente (cache hit), la pagina può essere letta direttamente dalla memoria, evitando l'I/O su disco. Se non presente (cache miss), la pagina deve essere letta dal disco e caricata nel buffer pool, potenzialmente rimuovendo un'altra pagina per fare spazio.

La **politica di rimpiazzo** (replacement policy) determina quale pagina espellere quando il buffer pool è pieno e una nuova pagina deve essere caricata. Le politiche comuni includono LRU (Least Recently Used), Clock, e algoritmi basati su frequenza di accesso. Alcuni DBMS implementano versioni avanzate come LRU-K o ARC (Adaptive Replacement Cache).

Il **buffer pool è tipicamente diviso in pool separati** per diverse tipologie di dati: pool per le tabelle, pool per gli indici, pool per i dati temporanei (sorting, hashing), e pool per le viste materializzate. Questa segmentazione permette di ottimizzare la configurazione per diversi carichi di lavoro.

Le **tabelle di controllo** (control tables) nel buffer pool tracciano lo stato di ogni frame: libero, occupato, dirty (modificato ma non scritto su disco), e pinning (la pagina è in uso e non può essere rimossa).

### 4.4 Gestione dello Spazio di Archiviazione

Lo storage engine gestisce l'organizzazione fisica dei dati su disco attraverso diversi meccanismi.

I **tablespace** sono container logici che raggruppano oggetti del database (tabelle, indici) e li mapeano a file fisici. In PostgreSQL, i tablespace permettono di allocare oggetti su diversi filesystem. In Oracle, i tablespace sono l'unità logica fondamentale per la gestione dello spazio.

I **segmenti** sono strutture che occupano spazio in un tablespace. Ogni tabella e indice è un segmento. I segmenti sono composti da **extents**, che sono allocazioni consecutive di pagine.

Le **pagine** (o blocchi) sono l'unità minima di I/O. La dimensione tipica delle pagine è 8KB, sebbene possa essere configurata (generalmente da 2KB a 32KB). Ogni pagina contiene un header (metadati sulla pagina), un array di tuple (i dati veri e propri), e un offset array per localizzare le tuple.

I **record** (tuple) sono memorizzati all'interno delle pagine. A causa della possibilità di aggiornamenti che aumentano la dimensione del record, i record possono essere memorizzati in modoframmentato, con uno stato di "dead" record che occupano spazio ma non sono più accessibili.

La **frammentazione** può essere interna (spazio non utilizzato all'interno di una pagina) o esterna (pagine non contigue su disco). La frammentazione degrada le prestazioni e viene gestita attraverso operazioni di manutenzione periodica come VACUUM in PostgreSQL o OPTIMIZE TABLE in MySQL.

---

## 5. Componenti Core di un Sistema Relazionale

### 5.1 Gestione delle Transazioni

Una transazione è un'unità logica di lavoro che raggruppa multiple operazioni sul database. Le transazioni forniscono il meccanismo per garantire la consistenza dei dati anche in presenza di fallimenti e accesso concorrente.

Il modello ACID definisce le quattro proprietà fondamentali delle transazioni:

**Atomicità** (Atomicity): Una transazione è un'unità atomica - o tutte le sue operazioni vengono eseguite, o nessuna viene eseguita. Se una qualsiasi operazione fallisce, l'intera transazione viene annullata (rollback), riportando il database allo stato precedente. L'atomicità è implementata attraverso il logging delle operazioni, che permette di annullare transazioni incomplete.

**Consistenza** (Consistency): Una transazione deve trasformare il database da uno stato valido a un altro stato valido. I vincoli di integrità definiti sul database devono essere rispettati alla fine di ogni transizione. Se una transazione viola un vincolo, deve essere abortita.

**Isolamento** (Isolation): Le transazioni concurrenti non devono interferire tra loro. Ciascuna transazione dovrebbe apparire come se fosse l'unica transazione in esecuzione nel sistema. L'isolamento è implementato attraverso tecniche di concurrency control come il locking.

**Durabilità** (Durability): Una volta che una transazione è committata, i suoi effetti devono persistere permanentemente nel database, anche in caso di fallimento del sistema. La durabilità è garantita attraverso il logging e la scrittura su disco dei dati.

### 5.2 Concurrency Control e Locking

Il **concurrency control** è il processo di gestione delle operazioni simultanee su un database per garantire la consistenza dei dati senza degradare eccessivamente le prestazioni. Esistono diverse tecniche per implementare il concurrency control.

Il **locking** è la tecnica più comune. Ogni risorsa (tabella, pagina, riga) può essere bloccata per prevenire accessi concurrenti che potrebbero causare inconsistenze. Esistono diversi tipi di lock:

Il **lock condiviso** (S-lock, shared lock) viene acquisito quando una transazione legge un dato. Lock condivisi possono essere tenuti simultaneamente da multiple transazioni perché le letture non interferiscono tra loro.

Il **lock esclusivo** (X-lock, exclusive lock) viene acquisito quando una transazione modifica un dato. Un lock esclusivo non può essere tenuto contemporaneamente a nessun altro lock (condiviso o esclusivo).

Il **lock di tabella** blocca un'intera tabella invece di singole righe. È meno granulare ma più semplice da gestire. Le modalità includono lock in lettura (LIKE) e lock in scrittura (LIKE).

Il **deadlock** si verifica quando due o più transazioni attendono indefinitamente le une le altre per rilasciare dei lock. I DBMS implementano meccanismi di detection dei deadlock (generalmente attraverso un grafo di attesa) e di resolution (tipicamente abortendo una delle transazioni coinvolte).

Il **two-phase locking** (2PL) è un protocollo che garantisce la serializzabilità delle transazioni. La prima fase (growing) acquisisce lock ma non ne rilascia. La seconda fase (shrinking) rilascia lock ma non ne acquisisce di nuovi. Varianti come Strict 2PL e Strong Strict 2PL migliorano la gestione dei rollback.

### 5.3 Isolation Levels e Anomalie

Lo **standard SQL** definisce quattro livelli di isolamento che bilanciano le prestazioni con la protezione da anomalie di concorrenza. I livelli sono ordinati dalla protezione maggiore alla minore protezione:

**SERIALIZABLE** garantisce che l'esecuzione concurrentede transazioni produca lo stesso risultato di un'esecuzione seriale. Fornisce la massima protezione ma può causare significanti degradi nelle prestazioni a causa dei lock necessari.

**REPEATABLE READ** garantisce che se una transazione legge la stessa riga due volte, otrarrà lo stesso risultato entrambe le volte. Tuttavia, potrebbe leggere righe nuove inserite da altre transazioni (phantom reads).

**READ COMMITTED** garantisce che una transazione legga solo i dati che sono stati committati da altre transazioni. È il livello di isolamento predefinito in molti DBMS moderni. Può incorrere in non-repeatable reads (la stessa riga può restituire valori diversi in letture successive) e phantom reads.

**READ UNCOMMITTED** permette di leggere dati non ancora committati (dirty reads). Fornisce le massime prestazioni ma la minima protezione. È raramente utilizzato in produzione.

Le **anomalie di concorrenza** che i diversi livelli prevengono sono:

**Dirty read**: Una transazione legge dati non ancora committati da un'altra transazione. Se la seconda transazione viene rollbacked, i dati letti dalla prima sono inconsistenti.

**Non-repeatable read**: Una transazione legge la stessa riga due volte e ottiene valori diversi perché un'altra transazione ha modificato e committato quella riga nel frattempo.

**Phantom read**: Una transazione esegue la stessa query due volte e ottiene un numero diverso di righe perché un'altra transazione ha inserito o cancellato righe che soddisfano i criteri della query.

### 5.4 Logging e Recovery

Il **logging** è il componente fondamentale per garantire la durabilità e la capacità di recovery. I database relazionali utilizzano tecniche di logging dettagliate per poter ricostruire lo stato del database dopo un fallimento.

Il **write-ahead logging** (WAL) è il principio fondamentale: i record di log devono essere scritti su disco prima che le modifiche corrispondenti siano scritte sul disco. Questo garantisce che in caso di fallimento, è possibile ricostruire le operazioni non ancora completate.

Ogni operazione di modifica genera uno o più **log record** che contengono: l'identificatore della transazione, l'identificatore del record modificato, i valori precedenti (before image) per il rollback, e i nuovi valori (after image) per il redo.

Il **recovery** dopo un fallimento segue tipicamente due fasi:

La fase di **analysis** scorre il log per determinare quali transazioni erano attive al momento del fallimento e quali pagine potrebbero essere state modificate.

La fase di **redo** ripete tutte le operazioni di modifica delle transazioni committate, riportando il database a uno stato consistente. Il redo parte dalla posizione dell'ultimo checkpoint valido.

La fase di **undo** annulla le operazioni delle transazioni che non erano committate al momento del fallimento, riportando il database allo stato precedente. Le transazioni da annullare sono identificate durante la fase di analysis.

I **checkpoint** sono punti sincronizzati nel log dove tutte le pagine modificate in memoria sono forzatamente scritte su disco. I checkpoint permettono di limitare la quantità di log da processare durante il recovery.

---

## 6. Transaction Processing Fundamentals

### 6.1 Gestione delle Transazioni in SQL

Il linguaggio SQL fornisce comandi espliciti per la gestione delle transazioni, permettendo ai programmatori di controllare quando le modifiche diventano permanenti.

Il comando **BEGIN** (o START TRANSACTION) inizia una nuova transazione esplicita. Da questo punto, tutte le successive istruzioni SQL fanno parte della transazione fino a quando non viene eseguito un COMMIT o un ROLLBACK.

Il comando **COMMIT** finalizza la transazione, rendendo permanenti tutte le modifiche eseguite all'interno della transazione. Dopo il commit, una nuova transazione può essere iniziata.

Il comando **ROLLBACK** annulla tutte le modifiche eseguite dalla transazione, riportando il database allo stato precedente l'inizio della transazione. Il rollback può essere esplicito (specificato dal programmatore) o implicito (dovuto a un errore o a un deadlock).

Le transazioni possono essere **autocommit** in alcuni DBMS, dove ogni singola istruzione SQL è trattata come una transazione autonoma. Questo è il comportamento predefinito in MySQL. In PostgreSQL, il comportamento predefinito è quello di richiedere una transazione esplicita per operazioni che modificano i dati.

I **savepoint** permettono di creare punti intermedi all'interno di una transazione ai quali è possibile fare rollback parziale. Se una transazione fallisce in un punto specifico, è possibile rollbackare solo la porzione finale mantenendo le modifiche precedenti i savepoint.

### 6.2 Commit in Dettaglio e Two-Phase Commit

Il processo di **commit** è più complesso di una semplice scrittura su disco. Coinvolge diverse fasi per garantire la durabilità:

1. Il transaction manager scrive i log record per il commit nel log su disco (sincrono).
2. Il log viene "flushato" per assicurare che sia scritto fisicamente.
3. Le modifiche vengono contrassegnate come committate nel log.
4. Il buffer pool può procedere a scrivere le pagine modificate su disco in background.
5. Un messaggio di conferma viene inviato all'applicazione.

Il **two-phase commit** (2PC) è un protocollo utilizzato nelle transazioni distribuite che coinvolgono multiple risorse (database differenti, sistemi di messaggistica). Il protocollo garantisce la consistenza anche in presenza di fallimenti:

La fase di **prepare**: Il coordinator invia un messaggio "prepare" a tutti i partecipanti. Ciascun partecipante risponde con "ready" (se può garantire il commit) o "abort" (se non può).

La fase di **commit**: Se tutti i partecipanti hanno risposto "ready", il coordinator invia "commit" a tutti. Se anche un solo partecipante ha risposto "abort", il coordinator invia "abort" a tutti. I partecipanti eseguono il commit (o abort) e confermano al coordinator.

Il protocollo 2PC gestisce i fallimenti attraverso timeout e logging delle decisioni, permettendo il recovery del coordinamento dopo fallimenti.

### 6.3 Locking a Livello di Riga vs pagina

La granularità del locking influisce significativamente sulle prestazioni e sulla concorrenza.

Il **locking a livello di riga** permette a multiple transazioni di modificare diverse righe della stessa tabella simultaneamente, massimizzando la concorrenza. Tuttavia, richiede più lock (overhead di gestione) e può portare a deadlock se le transazioni accedono a righe in ordini diversi.

Il **locking a livello di pagina** è meno granulare, bloccando un'intera pagina (tipicamente 8KB) invece di singole righe. Riduce l'overhead di gestione dei lock ma può causare contenzione quando transazioni diverse devono accedere a righe diverse nella stessa pagina.

Il **locking a livello di tabella** blocca un'intera tabella. È la forma più semplice ma la meno concurrente, poiché solo una transazione alla volta può accedere alla tabella.

I DBMS moderni implementano tipicamente una combinazione di questi livelli: locking a livello di riga come default, con escalation a livello di pagina o tabella quando necessario (ad esempio, quando una transazione acquisisce troppi lock di riga).

### 6.4 Transaction Isolation in Pratica

La scelta del livello di isolamento appropriato dipende dal caso d'uso specifico e dal bilanciamento tra correttezza e prestazioni.

Per **applicazioni finanziarie** dove la consistenza dei dati è critica, è generalmente consigliato SERIALIZABLE o almeno REPEATABLE READ. Il rischio di letture inconsistenti (non-repeatable reads, phantom reads) può portare a calcoli errati, come saldi bancari errati.

Per **applicazioni OLTP** con alto volume di transazioni brevi, READ COMMITTED è spesso il livello predefinito. Offre un buon bilanciamento tra protezione e prestazioni. Le applicazioni devono gestire eventuali anomalie al livello applicativo.

Per **batch processing** e operazioni analitiche, livelli di isolamento più bassi possono essere accettabili perché le operazioni sono tipicamente read-only o operano su snapshot isolati.

La configurazione del livello di isolamento può essere fatta a livello di sessione o a livello di transazione individuale. In PostgreSQL, si usa `SET TRANSACTION ISOLATION LEVEL`. In MySQL, si usa `SET SESSION TRANSACTION ISOLATION LEVEL`.

### 6.5 Distributed Transactions e Saga Pattern

Le **transazioni distribuite** sono necessarie quando i dati sono partizionati su multiple risorse (database, servizi). Mantenere la consistenza ACID attraverso sistemi distribuiti è challenging a causa del CAP theorem: non è possibile garantire simultaneamente consistenza, disponibilità e tolleranza alla partizione.

Il **two-phase commit** (2PC) già descritto fornisce consistenza atomica ma ha limitazioni: è sincrono (blocca le risorse durante il processo), non scala bene, e ha problemi di availability se il coordinator fallisce.

Il **pattern Saga** è un approccio alternativo per orchestrate transazioni distribuite in modo asincrono. Invece di una transazione atomica, una saga è una sequenza di transazioni locali, ciascuna delle quali aggiorna un singolo servizio. Se una transazione fallisce, la saga esegue transazioni di compensazione (compensating transactions) per annullare le operazioni precedenti.

Le transazioni compensating devono essere idempotenti (ripetibili senza effetti collaterali) e devono gestire la compensazione parziale (quando alcune transazioni sono state eseguite prima del fallimento).

Esempi di orchestratori per saga includono Camunda, Zeebe, e AWS Step Functions.

---

## 7. Concurrency Control Basics

### 7.1 Timestamp-Based Concurrency Control

Il **timestamp-based concurrency control** è un'alternativa al locking che fornisce serializzabilità senza utilizzare lock espliciti. Ogni transazione riceve un timestamp che determina il suo ordinamento nel sistema.

Il **timestamp ordering** (TO) assegna un timestamp di avvio a ogni transazione. Le operazioni sono ordinate in base a questi timestamp. Se una transazione T1 inizia prima di T2, allora T1 ha un timestamp minore e dovrebbe apparire "prima" nell'esecuzione.

Quando una transizione tenta di leggere un dato scritto da una transazione futura, si verifica un conflitto. La transazione viene abortita e riavviata con un nuovo timestamp. Analogamente, se una transazione tenta di scrivere un dato già letto o scritto da una transazione futura, viene abortita.

Il **Thomas' Write Rule** è una variante che permette di ignorare alcuni write-write se la transazione più vecchia è già stata completata, migliorando la concorrenza.

Il vantaggio del timestamp ordering è che non causa deadlock (perché non ci sono attese per lock). Lo svantaggio è che può portare a molti restart e potenzialmente a starvation per transazioni che continuano a essere abortite.

### 7.2 Optimistic Concurrency Control

L'**optimistic concurrency control** (OCC) assume che i conflitti tra transazioni siano rari e gestisce la concorrenza attraverso la validazione a posteriori invece del locking a priori.

L'OCC opera in tre fasi:

**Fase di lettura**: La transazione legge i dati, mantiene le proprie modifiche in uno spazio privato (workspace), e registra le versioni dei dati letti.

**Fase di validazione**: Quando la transazione tenta di committare, il sistema verifica che non ci siano conflitti con altre transazioni. La validazione controlla se le modifiche della transazione sono compatibili con le modifiche committate da altre transazioni nel frattempo.

**Fase di scrittura**: Se la validazione ha successo, le modifiche vengono applicate al database. Se la validazione fallisce, la transazione viene abortita e le modifiche sono scartate.

La validazione verifica che non ci siano stati conflitti read-write o write-write. La transizione T1 può committare solo se tutte le transazioni T2 che hanno committato modifiche a dati letti da T1 sono state completate prima dell'inizio di T1 (validazione backwards), o se T1 non ha letto dati modificati da transazioni che si sono completate mentre T1 era in esecuzione (validazione forwards).

L'OCC è efficace quando i conflitti sono rari (high read-to-write ratio). È inefficiente quando ci sono molti conflitti perché le transizioni vengono abortite e riavviate. È comunemente utilizzato in implementazioni di MVCC (Multiversion Concurrency Control).

### 7.3 MVCC (Multiversion Concurrency Control)

Il **MVCC** è una tecnica di concurrency control che mantiene multiple versioni dei dati, permettendo letture non bloccanti mentre le scritture procedono. È l'implementazione di default in PostgreSQL e MySQL InnoDB.

In MVCC, ogni transazione vede una snapshot dei dati al momento in cui la transazione è iniziata. Questa snapshot fornisce una vista consistente dei dati senza bloccare le scritture. Le letture non attendono le scritture, e le scritture non attendono le letture.

Ogni riga nel database ha campi aggiuntivi che tracciano le versioni: un identificatore della transizione che ha creato la versione (xmin), un identificatore della transazione che ha invalidato la versione (xmax), e un campo per i flag di cancellazione.

Quando una transazione modifica una riga, non sovrascrive la riga esistente ma crea una nuova versione. La vecchia versione rimane accessibile alle transazioni che hanno iniziato prima della modifica. Le versioni obsolete vengono successivamente "garbage collected".

I vantaggi di MVCC includono: letture senza lock (eccellente per carichi di lavoro read-heavy), minor blocking rispetto al locking tradizionale, e transazioni che possono ottenere una vista consistente del database senza lock.

Gli svantaggi includono: overhead di storage per le versioni multiple, complessità nella garbage collection delle versioni, e l'impossibilità di fare certain ottimizzazioni che richiedono lock esclusivi.

### 7.4 Granularità dei Lock e Lock Escalation

La **granularità** del locking influenza direttamente la concorrenza. Lock più fini (a livello di riga) permettono maggiore concorrenza ma richiedono più risorse per la gestione. Lock più grossolani (a livello di pagina o tabella) usano meno risorse ma limitano la concorrenza.

La **lock escalation** è il processo con cui un DBMS converte automaticamente lock di granularità fine in lock di granularità maggiore quando il numero di lock acquistati supera una soglia. Ad esempio, se una transazione acquisisce troppi lock di riga, il DBMS può escalare a un lock di pagina o di tabella.

L'escalation è un meccanismo per prevenire l'esaurimento delle risorse di sistema (tabelle di lock, memoria). Tuttavia, può portare a contenzione non necessaria quando una transazione che accederebbe a molte righe diverse scala a un lock di tabella, bloccando altre transizioni.

La configurazione corretta della soglia di escalation dipende dal carico di lavoro. Carichi di lavoro con transazioni che accedono a poche righe beneficiano di lock a livello di riga. Carichi con transazioni che accedono a molte righe potrebbero vedere degradi dalle escalation.

### 7.5 Deadlock Detection e Prevention

I **deadlock** si verificano quando due o più transazioni attendono indefinitamente che l'altra rilasci un lock. I DBMS implementano meccanismi per rilevare e risolvere i deadlock.

La **detection** dei deadlock tipicamente utilizza un "waits-for graph", un grafo diretto dove i nodi sono transazioni e gli archi indicano che una transazione attende un lock detenuto da un'altra. Un ciclo nel grafo indica un deadlock. I DBMS eseguono periodicamente (o su ogni attesa) la detection del ciclo.

Una volta rilevato un deadlock, il DBMS deve selezionare una "vittima" da abortire per spezzare il ciclo. La scelta considera tipicamente: il costo della transazione (quanto lavoro verrebbe perso), il numero di lock detenuti, e il tempo di esecuzione accumulato. La transazione vittima viene abortita con un errore che l'applicazione deve gestire.

La **prevention** dei deadlock evita che si formino cicli nel waits-for graph. Strategie comuni includono:

L'ordine di lock: tutte le transazioni acquisiscono i lock in un ordine predefinito (es. ordine delle tabelle). Questo previene i deadlock perché le transizioni non possono "inseguirsi" a vicenda.

La preemptive lock acquisition: se una transizione deve attendere per un lock, invece di attendere, viene abortita immediatamente. Questo evita l'accumulo di attese che porta ai deadlock.

Il timeout: transazioni che attendono troppo a lungo vengono automaticamente abortite. È un approccio semplice ma può portare a falsi positivi (abort di transizioni che non sono in deadlock ma solo lente).

---

## 8. Recovery e Durability

### 8.1 ARIES Recovery Algorithm

**ARIES** (Algorithm for Recovery and Isolation Exploiting Semantics) è l'algoritmo di recovery utilizzato da IBM DB2 e, con variazioni, da PostgreSQL e MySQL InnoDB. È un algoritmo sofisticato che combina redo e undo in modo efficiente.

ARIES si basa su tre principi:

**Write-ahead logging**: Tutte le modifiche sono registrate nel log prima di essere applicate ai dati su disco. Questo garantisce la possibilità di recovery.

**Repeating history during recovery**: Durante il recovery, ARIES ripete tutte le operazioni registrate nel log per riportare il database allo stato esatto al momento del fallimento, poi annulla le transazioni incomplete.

**Logging changes during undo**: Durante l'annullamento delle transazioni, ARIES registra le operazioni di undo nel log. Questo permette di gestire fallimenti durante il recovery stesso (richiedendo retry dell'undo).

Il recovery in ARIES consiste in tre fasi:

**Analysis**: Si scorre il log forward dall'ultimo checkpoint per identificare le pagine dirty (modificate), le transizioni attive al momento del crash, e il punto di inizio del redo.

**Redo**: Si ripetono tutte le operazioni dal punto identificato dall'analisi fino alla fine del log, applicando le modifiche alle pagine. Questo garantisce che tutte le modifiche committate siano applicate.

**Undo**: Si annullano le operazioni delle transazioni che erano attive al momento del crash, lavorando a ritroso nel log.

### 8.2 Checkpoint e Log Truncation

I **checkpoint** sono punti di sincronizzazione dove lo stato del database è registrato in modo che il recovery non debba processare l'intero log.

Durante un checkpoint:
- Tutte le transizioni attive sono registrate
- Tutte le pagine dirty in memoria sono scritte su disco
- Un record di checkpoint è scritto nel log

Dopo un checkpoint, il recovery può iniziare dal checkpoint invece che dall'inizio del log, riducendo significativamente il tempo di recovery.

Il **log truncation** è il processo di eliminazione delle porzioni di log che non sono più necessarie per il recovery. Questo previene la crescita illimitata del log.

In PostgreSQL, il truncation avviene automaticamente quando il log è abbastanza vecchio da essere fuori dal "reach" di qualsiasi transazione attiva. Questo è gestito dal processo background WAL writer e dal autorecovery.

In MySQL/InnoDB, il log viene troncato quando il checkpoint è completato e tutte le transazioni che hanno generato log precedente sono state committate.

### 8.3 Crash Recovery e Warm vs Cold Recovery

Il **crash recovery** è il processo di ripristino del database dopo un fallimento del sistema (power failure, kernel panic, crash dell'applicazione DBMS). Il database deve essere riportato a uno stato consistente.

Il **warm recovery** (recovery a caldo) avviene quando il DBMS è ancora in esecuzione ma deve ripristinare la consistenza dopo un crash. Tipicamente, il DBMS si avvia in modalità recovery, processa il log, e poi diventa disponibile per le connessioni.

Il **cold recovery** (recovery a freddo) è necessario quando il DBMS stesso non può avviarsi. In questo caso, potrebbe essere necessario ripristinare da backup e applicare i log delle transazioni (restore and recovery).

Il **media recovery** è necessario quando i file di dati su disco sono corrotti o persi (es. disco guasto). Richiede il ripristino da backup più l'applicazione dei log delle transazioni.

Il **time-based recovery** permette di ripristinare il database a un momento specifico nel tempo. Utilizzando i backup e i log, è possibile ricostruire lo stato del database a qualsiasi punto nel tempo entro il periodo coperto dai backup e dai log.

### 8.4 Durabilità e Write Performance

La **durabilità** delle transazioni è garantita dalla scrittura su disco prima della conferma alla applicazione. Questo ha implicazioni significative sulle prestazioni.

La **sincronizzazione del log** è l'operazione più costosa nel percorso di commit. Prima di restituire il controllo all'applicazione, il DBMS deve assicurare che il record di log sia scritto fisicamente su disco. Questo richiede un'operazione di fsync() o equivalente, che è relativamente lenta.

Le **ottimizzazioni** includono:

**Group commit**: Transazioni multiple che completano simultaneamente possono scrivere un singolo record di log, riducendo il numero di sincronizzazioni.

**Batch commit**: Le applicazioni possono raggruppare multiple transazioni in una singola transazione, riducendo il numero di commit.

**Write-back cache**: Alcuni sistemi utilizzano controller di storage con batteria (BBU) che permettono di scrivere prima nella cache del controller, con la garanzia che i dati saranno scritti su disco anche in caso di power failure.

**Durabilità ritardata**: Alcuni DBMS (come Cassandra, o configurazioni di PostgreSQL) permettono di configurare la durabilità come "ritardata" (asynchronous commit), accettando il rischio di perdere alcune transazioni in cambio di prestazioni migliori.

### 8.5 Disaster Recovery e Backup Strategies

Le strategie di **disaster recovery** proteggono contro perdite di dati dovute a fallimenti catastrofici (data center, disasters naturali).

Il **backup completo** cattura lo stato completo del database a un certo punto nel tempo. Può essere eseguito in diversi modi: a caldo (database online), a freddo (database offline), o incrementale (solo le modifiche dall'ultimo backup).

Il **backup incrementale** cattura solo le modifiche dall'ultimo backup. Riduce lo spazio di storage e il tempo di backup, ma rende il recovery più complesso (richiede l'applicazione di molteplici incrementali).

Il **backup del log delle transazioni** è essenziale per il point-in-time recovery. Mantenendo i log delle transazioni, è possibile ripristinare il database a qualsiasi momento tra i backup completi.

La **replica geografica** fornisce protezione contro disaster che colpiscono un'intera location. Le tecniche includono replica sincrona (zero RPO ma latenza elevata) e replica asincrona (RPO>0 ma latenza gestibile).

Le **metriche** per il disaster recovery includono:

**RTO** (Recovery Time Objective): il tempo massimo accettabile per ripristinare il servizio dopo un disastro.

**RPO** (Recovery Point Objective): la quantità massima accettabile di dati persi, espressa come tempo (es. "massimo 1 ora di dati").

---

## 9. Query Processing e Optimization

### 9.1 Query Processing Pipeline

Il processing di una query SQL passa attraverso diverse fasi, ciascuna trasformando la query e producendo output per la fase successiva.

Il **parsing** analizza la sintassi della query, costruendo un parse tree che rappresenta la struttura grammaticale della query. Il parser verifica che la query sia sintatticamente valida e produce errori significativi per query mal formate.

La **validazione** controlla che gli oggetti referenziati (tabelle, colonne) esistano nel database e che l'utente abbia i permessi necessari per accedervi. La validazione risolve anche i nomi (table alias, column references) e verifica i tipi di dati.

La **trasformazione** converte la query in una rappresentazione interna (algebrica) che è più adatta all'ottimizzazione. Questa fase include la riscrittura della query in forme equivalenti (es. flattening delle subquery, piani di join reordering).

L'**ottimizzazione** è la fase più complessa. L'optimizer considera molteplici piani di esecuzione equivalenti, stima il costo di ciascun piano (basandosi su statistiche sullo stato del database), e seleziona il piano con il costo stimato minore.

L'**esecuzione** implementa il piano di query scelto, orchestrando gli operatori fisici che eseguono le operazioni logiche (scan, join, sort, aggregation).

### 9.2 Cost-Based Optimization

L'ottimizzazione **basata sui costi** (CBO) stima il costo computazionale di diversi piani di esecuzione e seleziona quello con costo stimato minore. Questo richiede:

**Statistiche** sullo stato del database, incluse: il numero di righe in ogni tabella, la distribuzione dei valori nelle colonne (istogrammi), il numero di valori unici per ogni colonna (cardinalità), e informazioni sugli indici esistenti.

Un **modello di costo** che stima il tempo di esecuzione in base alle operazioni: costo di lettura sequenziale vs random, costo di join, costo di sort, costo di aggregazione, e overhead di comunicazione per query distribuite.

L'optimizer esplora lo spazio dei piani di esecuzione possibili. Per query complesse, il numero di piani possibili può essere astronomicamente grande, quindi l'optimizer utilizza tecniche di ricerca euristiche (bottom-up, top-down, genetic algorithms) per trovare buone soluzioni in tempi ragionevoli.

### 9.3 Join Order e Join Methods

L'ottimizzazione dei join è una delle decisioni più critiche per le prestazioni delle query. Il join order influenza drammaticamente il costo della query.

Il **join order** determina l'ordine in cui le tabelle vengono unite. Per una query con N tabelle, ci sono N! possibili ordini di join. Gli optimizer utilizzano tecniche come il dynamic programming (per query con poche tabelle) o algoritmi greedy (per query con molte tabelle) per trovare ordini efficienti.

I **metodi di join** disponibili dipendono dal DBMS e dal contesto:

**Nested loop join** è il metodo più semplice. Per ogni riga della tabella esterna, scandisce tutte le righe della tabella interna cercando match. Efficiente quando una delle tabelle è piccola o ha un indice sulla chiave di join.

**Hash join** costruisce una hash table sulla tabella più piccola, poi scandisce l'altra tabella cercando match nella hash table. Efficiente per join su tabelle grandi senza indici appropriati.

**Sort-merge join** ordina entrambe le tabelle sulla chiave di join, poi le scansiona in parallelo. Efficiente quando i dati sono già ordinati o quando l'ordinamento è necessario per altri motivi.

### 9.4 Index Usage e Scan Methods

I **metodi di scansione** determinano come le righe vengono recuperate dalle tabelle:

**Table scan** legge tutte le pagine della tabella in sequenza. È l'unica opzione quando non esistono indici utili o quando la query richiede la maggior parte delle righe.

**Index scan** utilizza un indice per trovare le righe. L'indice può essere usato per filtrare (index condition pushdown), per coprire (covering index - tutti i dati necessari sono nell'indice), o per ordinare.

**Index only scan** è un caso speciale dove tutti i dati necessari sono contenuti nell'indice, evitando l'accesso alla tabella. Richiede indici covering.

**Bitmap scan** è una tecnica usata in PostgreSQL che costruisce bitmap di bit per ogni valore di chiave, poi le combina con operazioni di AND/OR per filtrare le righe.

La scelta del scan method dipende dalla query, dagli indici disponibili, e dalle statistiche. L'optimizer decide basandosi sul costo stimato.

### 9.5 Query Rewrite e Optimization Techniques

Le **trasformazioni di query** (query rewrite) convertono la query in forme equivalenti ma potenzialmente più efficienti:

**Subquery flattening**: Le subquery nella clausola FROM vengono trasformate in join. Le subquery nella clausola WHERE vengono talvolta convertite in join o semi-join.

**Predicate pushdown**: I filtri vengono spinti il più vicino possibile alle tabelle, riducendo la quantità di dati processati nelle fasi successive.

**Join elimination**: Join ridondanti vengono rimossi. Ad esempio, se una tabella viene joinata per la sua chiave primaria, il join potrebbe essere eliminato se non ci sono altre colonne utili dalla tabella.

**Constant folding**: Espressioni costanti vengono valutate a compile-time.

**Or to union**: Condizioni OR possono talvolta essere convertite in UNION per sfruttare indici separati.

---

## 10. Benchmark e Performance Metrics

### 10.1 TPC-C e TPC-E Benchmark

I **benchmark TPC** sono lo standard industriale per la misurazione delle prestazioni dei database relazionali.

**TPC-C** è un benchmark OLTP (Online Transaction Processing) che simula un sistema di ordini per un'azienda di vendita. Include transazioni come nuovi ordini, pagamenti, spedizioni, verifica dello stato dell'ordine, e aggiornamento del magazzino. Le metriche principali sono:

**tpmC**: transazioni al minuto (new-order) che il sistema può processare.

**$/tpmC**: costo per tpmC (include hardware, software, e manutenzione).

**TPC-E** è un benchmark OLTP più recente che simula un sistema di trading azionario. È considerato più rappresentativo delle applicazioni enterprise moderne. Include transazioni più complesse di TPC-C e ha requisiti più stringenti per la consistenza.

### 10.2 Performance Metrics e Monitoring

Le **metriche di performance** per i database relazionali includono:

**Throughput**: Il numero di operazioni per unità di tempo. Può essere misurato come transazioni al secondo (TPS), query al secondo (QPS), o operazioni di I/O al secondo (IOPS).

**Latenza**: Il tempo per completare una singola operazione. Si misura in millisecondi. Le metriche includono latenza media, latenza al 95° percentile (p95), e latenza al 99° percentile (p99).

**Utilizzo delle risorse**: CPU utilization, memoria utilizzata, I/O su disco, network bandwidth.

**Contention**: Lock wait time, latch wait time, buffer busy waits.

Gli strumenti di **monitoraggio** per database relazionali includono:

**Performance schema** in MySQL, **pg_stat_statements** in PostgreSQL, **Dynamic Management Views** in SQL Server, e strumenti di terze parti come Datadog, New Relic, e Grafana con Prometheus.

### 10.3 Query Performance Tuning

L'ottimizzazione delle query coinvolge diverse attività:

L'**analisi del piano di esecuzione** mostra come il DBMS intende eseguire la query. Il piano rivela le operazioni (scansioni, join, aggregazioni), l'ordine di esecuzione, e le stime di costo.

L'**individuazione delle criticità** identifica le operazioni più costose nel piano di esecuzione. Operazioni come full table scans, nested loop join non efficienti, e sort in memoria che traboccano su disco sono indicatori comuni di problemi.

La **creazione di indici** appropriati può migliorare drammaticamente le prestazioni. Gli indici devono essere selettivi (riducono significativamente il numero di righe), devono coprire le colonne utilizzate nelle query, e devono essere mantenibili (overhead di scrittura accettabile).

La **ristrutturazione delle query** può eliminare inefficienze: evitare funzioni sulle colonne indicizzate, minimizzare le subquery, usare join invece di subquery dove appropriato, e filtrare presto (predicate pushdown).

### 10.4 Capacity Planning

Il **capacity planning** proietta i requisiti futuri di risorse basandosi sulla crescita dei dati e del carico di lavoro.

La **proiezione della crescita dei dati** stima la dimensione del database nel tempo, basandosi sul tasso di ingestione e sulla retention policy.

La **proiezione del carico** stima il throughput e la latenza futuri basandosi sulla crescita degli utenti e delle transazioni.

Il **dimensionamento delle risorse** determina le risorse hardware necessarie (CPU, memoria, storage, network) per soddisfare i requisiti di performance.

I modelli di **scaling** influenzano le decisioni: scaling vertical (hardware più potente) vs scaling horizontal (aggiungere più server). Lo scaling orizzontale è più complesso per i database relazionali a causa delle transazioni distribuite.

### 10.5 Performance Anti-Patterns

I **pattern anti-performance** sono errori comuni che degradano le prestazioni:

**N+1 query problem**: Eseguire una query per ogni elemento in un loop invece di bulk fetch. Risultato: N query invece di una.

**Missing indexes**: Query che richiedono full table scan su tabelle grandi. Soluzione: creare indici sulle colonne usate in WHERE, JOIN, ORDER BY.

**Unnecessary sorting**: Ordini non necessari, sort di dataset troppo grandi in memoria. Soluzione: creare indici che già forniscono l'ordinamento desiderato.

**Excessive normalization**: Over-normalizzazione che richiede join costosi. Denormalizzazione controllata può migliorare le prestazioni.

**Inappropriate data types**: Uso di VARCHAR per dati numerici, uso di TEXT per dati che potrebbero essere più piccoli. Impatto su storage e performance.

**Transaction scope troppo ampio**: Transazioni che includono operazioni non necessarie, bloccando risorse più a lungo del necessario.

---

## Appendice: Risorse e Riferimenti

### A.1 Libri Consigliati

- "Database System Concepts" di Silberschatz, Korth, Sudarshan - copre teoria e implementazione dei database relazionali
- "The Architecture of Open Source Databases" di MySQL, PostgreSQL, SQLite - approfondisce le implementazioni specifiche
- "Transaction Processing" di Gray e Reuter - reference fondamentale per il transaction processing
- "SQL and Relational Theory" di C.J. Date - approfondisce la teoria relazionale

### A.2 Standard e Specifiche

- ISO/IEC 9075:2023 - SQL Standard
- TPC-C Benchmark Specification - www.tpc.org

### A.3 Link Utili

- PostgreSQL Documentation: postgresql.org/docs
- MySQL Documentation: dev.mysql.com/doc
- SQL Server Documentation: docs.microsoft.com/en-us/sql

**ARIES** (Algorithm for Recovery and Isolation Exploiting Semantics) è l'algoritmo di recovery utilizzato da IBM DB2 e, con variazioni, da altri DBMS come PostgreSQL e MySQL InnoDB. È un algoritmo sofisticato che combina redo e undo in modo efficiente.

ARIES si basa su tre principi:

**Write-ahead logging**: Tutte le modifiche sono registrate nel log prima di essere applicate ai dati su disco. Questo garantisce la possibilità di recovery.

**Repeating history during recovery**: Durante il recovery, ARIES ripete tutte le operazioni registrate nel log per riportare il database allo stato esatto al momento del fallimento, poi annulla le transazioni incomplete.

**Logging changes during undo**: Durante l'annullamento delle transazioni, ARIES registra le operazioni di undo nel log. Questo permette di gestire fallimenti durante il recovery stesso (richiedendo retry dell'undo).

Il recovery in ARIES consiste in tre fasi:

**Analysis**: Si scorre il log forward dall'ultimo checkpoint per identificare le pagine dirty (modificate), le transizioni attive al momento del crash, e il punto di inizio del redo.

**Redo**: Si ripetono tutte le operazioni dal punto identificato dall'analisi fino alla fine del log, applicando le modifiche alle pagine. Questo garantisce che tutte le modifiche committate siano applicate.

**Undo**: Si annullano le operazioni delle transazioni che erano attive al momento del crash, lavorando a ritroso nel log.

### 8.2 Checkpoint e Log Truncation

I **checkpoint** sono punti di sincronizzazione dove lo stato del database è registrato in modo che il recovery non debba processare l'intero log.

Durante un checkpoint:
- Tutte le transizioni attive sono registrate
- Tutte le pagine dirty in memoria sono scritte su disco
- Un record di checkpoint è scritto nel log

Dopo un checkpoint, il recovery può iniziare dal checkpoint invece che dall'inizio del log, riducendo significativamente il tempo di recovery.

Il **log truncation** è il processo di eliminazione delle porzioni di log che non sono più necessarie per il recovery. Questo previene la crescita illimitata del log.

In PostgreSQL, il truncation avviene automaticamente quando il log è abbastanza vecchio da essere fuori dal "reach" di qualsiasi transazione attiva. Questo è gestito dal processo background WAL writer e dal autorecovery.

In MySQL/InnoDB, il log viene troncato quando il checkpoint è completato e tutte le transazioni che hanno generato log precedente sono state committate.

### 8.3 Crash Recovery e Warm vs Cold Recovery

Il **crash recovery** è il processo di ripristino del database dopo un fallimento del sistema (power failure, kernel panic, crash dell'applicazione DBMS). Il database deve essere riportato a uno stato consistente.

Il **warm recovery** (recovery a caldo) avviene quando il DBMS è ancora in esecuzione ma deve ripristinare la consistenza dopo un crash. Tipicamente, il DBMS si avvia in modalità recovery, processa il log, e poi diventa disponibile per le connessioni.

Il **cold recovery** (recovery a freddo) è necessario quando il DBMS stesso non può avviarsi. In questo caso, potrebbe essere necessario ripristinare da backup e applicare i log delle transazioni (restore and recovery).

Il **media recovery** è necessario quando i file di dati su disco sono corrotti o persi (es. disco guasto). Richiede il ripristino da backup più l'applicazione dei log delle transazioni fino a un punto nel tempo.

Il **time-based recovery** permette di ripristinare il database a un momento specifico nel tempo. Utilizzando i backup e i log, è possibile ricostruire lo stato del database a qualsiasi punto nel tempo entro il periodo coperto dai backup e dai log.

### 8.4 Durabilità e Write Performance

La **durabilità** delle transazioni è garantita dalla scrittura su disco prima della conferma alla applicazione. Questo ha implicazioni significative sulle prestazioni.

La **sincronizzazione del log** è l'operazione più costosa nel percorso di commit. Prima di restituire il controllo all'applicazione, il DBMS deve assicurare che il record di log sia scritto fisicamente su disco. Questo richiede un'operazione di fsync() o equivalente, che è relativamente lenta.

Le **ottimizzazioni** includono:

**Group commit**: Transazioni multiple che completano simultaneamente possono scrivere un singolo record di log, riducendo il numero di sincronizzazioni.

**Batch commit**: Le applicazioni possono raggruppare multiple transazioni in una singola transazione, riducendo il numero di commit.

**Write-back cache**: Alcuni sistemi utilizzano controller di storage con batteria (BBU) che permettono di scrivere prima nella cache del controller, con la garanzia che i dati saranno scritti su disco anche in caso di power failure.

**Durabilità ritardata**: Alcuni DBMS (come Cassandra, o configurazioni di PostgreSQL) permettono di configurare la durabilità come "ritardata" (asynchronous commit), accettando il rischio di perdere alcune transazioni in cambio di prestazioni migliori.

### 8.5 Disaster Recovery e Backup Strategies

Le strategie di **disaster recovery** proteggono contro perdite di dati dovute a fallimenti catastrofici (data center, disasters naturali).

Il **backup completo** cattura lo stato completo del database a un certo punto nel tempo. Può essere eseguito in diversi modi: a caldo (database online), a freddo (database offline), o incrementale (solo le modifiche dall'ultimo backup).

Il **backup incrementale** cattura solo le modifiche dall'ultimo backup. Riduce lo spazio di storage e il tempo di backup, ma rende il recovery più complesso (richiede l'applicazione di molteplici incrementali).

Il **backup del log delle transazioni** è essenziale per il point-in-time recovery. Mantenendo i log delle transazioni, è possibile ripristinare il database a qualsiasi momento tra i backup completi.

La **replica geografica** fornisce protezione contro disaster che colpiscono un'intera location. Le tecniche includono replica sincrona (zero RPO ma latenza elevata) e replica asincrona (RPO>0 ma latenza gestibile).

Le **metriche** per il disaster recovery includono:

**RTO** (Recovery Time Objective): il tempo massimo accettabile per ripristinare il servizio dopo un disastro.

**RPO** (Recovery Point Objective): la quantità massima accettabile di dati persi, espressa come tempo (es. "massimo 1 ora di dati").

---

## 9. Query Processing e Optimization

### 9.1 Query Processing Pipeline

Il processing di una query SQL passa attraverso diverse fasi, ciascuna trasformando la query e producendo output per la fase successiva.

Il **parsing** analizza la sintassi della query, costruendo un parse tree che rappresenta la struttura grammaticale. Il parser verifica che la query sia sintatticamente valida e produce errori significativi per query mal formate.

La **validazione** controlla che gli oggetti referenziati (tabelle, colonne) esistano nel database e che l'utente abbia i permessi necessari per accedervi. La validazione risolve anche i nomi (table alias, column references) e verifica i tipi di dati.

La **trasformazione** converte la query in una rappresentazione interna (algebrica) che è più adatta all'ottimizzazione. Questa fase include la riscrittura della query in forme equivalenti (es. flattening delle subquery, piani di join reordering).

L'**ottimizzazione** è la fase più complessa. L'optimizer considera molteplici piani di esecuzione equivalenti, stima il costo di ciascun piano (basandosi su statistiche sullo stato del database), e seleziona il piano con il costo stimato minore.

L'**esecuzione** implementa il piano di query scelto, orchestrando gli operatori fisici che eseguono le operazioni logiche (scan, join, sort, aggregation).

### 9.2 Cost-Based Optimization

L'ottimizzazione **basata sui costi** (CBO) stima il costo computazionale di diversi piani di esecuzione e seleziona quello con costo stimato minore. Questo richiede:

**Statistiche** sullo stato del database, incluse: il numero di righe in ogni tabella, la distribuzione dei valori nelle colonne (istogrammi), il numero di valori unici per ogni colonna (cardinalità), e informazioni sugli indici esistenti.

Un **modello di costo** che stima il tempo di esecuzione in base alle operazioni: costo di lettura sequenziale vs random, costo di join, costo di sort, costo di aggregazione, e overhead di comunicazione per query distribuite.

L'optimizer esplora lo spazio dei piani di esecuzione possibili. Per query complesse, il numero di piani possibili può essere astronomicamente grande, quindi l'optimizer utilizza tecniche di ricerca euristiche (bottom-up, top-down, genetic algorithms) per trovare buone soluzioni in tempi ragionevoli.

### 9.3 Join Order e Join Methods

L'ottimizzazione dei join è una delle decisioni più critiche per le prestazioni delle query. Il join order influenza drammaticamente il costo della query.

Il **join order** determina l'ordine in cui le tabelle vengono unite. Per una query con N tabelle, ci sono N! possibili ordini di join. Gli optimizer utilizzano tecniche come il dynamic programming (per query con poche tabelle) o algoritmi greedy (per query con molte tabelle) per trovare ordini efficienti.

I **metodi di join** disponibili dipendono dal DBMS e dal contesto:

**Nested loop join** è il metodo più semplice. Per ogni riga della tabella esterna, scandisce tutte le righe della tabella interna cercando match. Efficiente quando una delle tabelle è piccola o ha un indice sulla chiave di join.

**Hash join** costruisce una hash table sulla tabella più piccola, poi scandisce l'altra tabella cercando match nella hash table. Efficiente per join su tabelle grandi senza indici appropriati.

**Sort-merge join** ordina entrambe le tabelle sulla chiave di join, poi le scansiona in parallelo. Efficiente quando i dati sono già ordinati o quando l'ordinamento è necessario per altri motivi.

### 9.4 Index Usage e Scan Methods

I **metodi di scansione** determinano come le righe vengono recuperate dalle tabelle:

**Table scan** legge tutte le pagine della tabella in sequenza. È l'unica opzione quando non esistono indici utili o quando la query richiede la maggior parte delle righe.

**Index scan** utilizza un indice per trovare le righe. L'indice può essere used per filtrare (index condition pushdown), per coprire (covering index - tutti i dati necessari sono nell'indice), o per ordinare.

**Index only scan** è un caso speciale dove tutti i dati necessari sono contenuti nell'indice, evitando l'accesso alla tabella. Richiede indici covering.

**Bitmap scan** è una tecnica usata in PostgreSQL che costruisce bitmap di bit per ogni valore di chiave, poi le combina con operazioni di AND/OR per filtrare le righe.

La scelta del scan method dipende dalla query, dagli indici disponibili, e dalle statistiche. L'optimizer decide basandosi sul costo stimato.

### 9.5 Query Rewrite e Optimization Techniques

Le **trasformazioni di query** (query rewrite) convertono la query in forme equivalenti ma potenzialmente più efficienti:

**Subquery flattening**: Le subquery nella clausola FROM vengono trasformate in join. Le subquery nella clausola WHERE vengono talvolta convertite in join o semi-join.

**Predicate pushdown**: I filtri vengono spinti il più vicino possibile alle tabelle, riducendo la quantità di dati processati nelle fasi successive.

**Join elimination**: Join ridondanti vengono rimossi. Ad esempio, se una tabella viene joinata per la sua chiave primaria, il join potrebbe essere eliminato se non ci sono altre colonne utili dalla tabella.

**Constant folding**: Espressioni costanti vengono valutate a compile-time.

**Or to union**: Condizioni OR possono talvolta essere convertite in UNION per sfruttare indici separati.

---

## 10. Benchmark e Performance Metrics

### 10.1 TPC-C e TPC-E Benchmark

I **benchmark TPC** sono lo standard industriale per la misurazione delle prestazioni dei database relazionali.

**TPC-C** è un benchmark OLTP (Online Transaction Processing) che simula un sistema di ordini per un'azienda di vendita. Include transazioni come nuovi ordini, pagamenti, spedizioni, verifica dello stato dell'ordine, e aggiornamento del magazzino. Le metriche principali sono:

**tpmC**: transazioni al minuto (new-order) che il sistema può processare.

**$/tpmC**: costo per tpmC (include hardware, software, e manutenzione).

**TPC-E** è un benchmark OLTP più recente che simula un sistema di trading azionario. È considerato più rappresentativo delle applicazioni enterprise moderne. Include transazioni più complesse di TPC-C e ha requisiti più stringenti per la consistenza.

### 10.2 Performance Metrics e Monitoring

Le **metriche di performance** per i database relazionali includono:

**Throughput**: Il numero di operazioni per unità di tempo. Può essere misurato come transazioni al secondo (TPS), query al secondo (QPS), o operazioni di I/O al secondo (IOPS).

**Latency**: Il tempo per completare una singola operazione. Si misura in millisecondi. Le metriche includono latenza media, latenza al 95° percentile (p95), e latenza al 99° percentile (p99).

**Utilizzo delle risorse**: CPU utilization, memoria utilizzata, I/O su disco, network bandwidth.

**Contention**: Lock wait time, latch wait time, buffer busy waits.

Gli strumenti di **monitoraggio** per database relazionali includono:

**Performance schema** in MySQL, **pg_stat_statements** in PostgreSQL, **Dynamic Management Views** in SQL Server, e strumenti di terze parti come Datadog, New Relic, e Grafana con Prometheus.

### 10.3 Query Performance Tuning

L'ottimizzazione delle query coinvolge diverse attività:

L'**analisi del piano di esecuzione** mostra come il DBMS intende eseguire la query. Il piano rivela le operazioni (scansioni, join, aggregazioni), l'ordine di esecuzione, e le stime di costo.

L'**individuazione delle criticità** identifica le operazioni più costose nel piano di esecuzione. Operazioni come full table scans, nested loop join non efficienti, e sort in memoria che traboccano su disco sono indicatori comuni di problemi.

La **creazione di indici** appropriati può migliorare drammaticamente le prestazioni. Gli indici devono essere selettivi (riducono significativamente il numero di righe), devono coprire le colonne utilizzate nelle query, e devono essere mantenibili (overhead di scrittura accettabile).

La **ristrutturazione delle query** può eliminare inefficienze: evitare funzioni sulle colonne indicizzate, minimizzare le subquery, usare join invece di subquery dove appropriato, e filtrare presto (predicate pushdown).

### 10.4 Capacity Planning

Il **capacity planning** proietta i requisiti futuri di risorse basandosi sulla crescita dei dati e del carico di lavoro.

La **proiezione della crescita dei dati** stima la dimensione del database nel tempo, basandosi sul tasso di ingestione e sulla retention policy.

La **proiezione del carico** stima il throughput e la latenza futuri basandosi sulla crescita degli utenti e delle transazioni.

Il **dimensionamento delle risorse** determina le risorse hardware necessarie (CPU, memoria, storage, network) per soddisfare i requisiti di performance.

I modelli di **scaling** influenzano le decisioni: scaling vertical (hardware più potente) vs scaling horizontal (aggiungere più server). Lo scaling orizzontale è più complesso per i database relazionali a causa delle transazioni distribuite.

### 10.5 Performance Anti-Patterns

I **pattern anti-performance** sono errori comuni che degradano le prestazioni:

**N+1 query problem**: Eseguire una query per ogni elemento in un loop invece di bulk fetch. Risultato: N query invece di una.

**Missing indexes**: Query che richiedono full table scan su tabelle grandi. Soluzione: creare indici sulle colonne usate in WHERE, JOIN, ORDER BY.

**Unnecessary sorting**: Ordini non necessari, sort di dataset troppo grandi in memoria. Soluzione: creare indici che già forniscono l'ordinamento desiderato.

**Excessive normalization**: Over-normalizzazione che richiede join costosi. Denormalizzazione controllata può migliorare le prestazioni.

**Inappropriate data types**: Uso di VARCHAR per dati numerici, uso di TEXT per dati che potrebbero essere più piccoli. Impatto su storage e performance.

**Transaction scope troppo ampio**: Transazioni che includono operazioni non necessarie, bloccando risorse più a lungo del necessario.

---

## Appendice: Risorse e Riferimenti

### A.1 Libri Consigliati

- "Database System Concepts" di Silberschatz, Korth, Sudarshan - copre teoria e implementazione dei database relazionali
- "The Architecture of Open Source Databases" di MySQL, PostgreSQL, SQLite - approfondisce le implementazioni specifiche
- "Transaction Processing" di Gray e Reuter - reference fondamentale per il transaction processing
- "SQL and Relational Theory" di C.J. Date - approfondisce la teoria relazionale

### A.2 Standard e Specifiche

- ISO/IEC 9075:2023 - SQL Standard
- TPC-C Benchmark Specification - www.tpc.org

### A.3 Link Utili

- PostgreSQL Documentation: postgresql.org/docs
- MySQL Documentation: dev.mysql.com/doc
- SQL Server Documentation: docs.microsoft.com/en-us/sql

---

*Questo documento fa parte del modulo 01 "Basi Dati Relazionali" della Data Encyclopedia.*
*Per domande o correzioni, consultare il repository o contattare il team di documentazione.*