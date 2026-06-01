# MVCC e Write-Ahead Log in PostgreSQL

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
1. MVCC: Multi-Version Concurrency Control
2. Tuple Header e Versioni
3. Transaction ID e Xmin/Xmax
4. Visibility Map
5. Write-Ahead Logging (WAL)
6. WAL Structure e Segments
7. Checkpoints e Recovery
8. Hot Update e Vacuum
9. Concurrency Control con MVCC
10. Performance Tuning WAL

---

## 1. MVCC: Multi-Version Concurrency Control

### 1.1 Fondamenti MVCC

Il **Multi-Version Concurrency Control (MVCC)** è il paradigma fundamental utilizzato da PostgreSQL per gestire l'accesso concorrente ai dati senza ricorrere a meccanismi di locking pessimistico. A differenza dei database che utilizzano lock a livello di riga o tabella per serializzare le operazioni, MVCC permette a multiple transazioni di operare simultaneamente mantenendo l'isolamento necessario per la consistenza dei dati.

Il principio base di MVCC è elegant nella sua semplicità: invece di modificare i dati esistenti, ogni scrittura crea una nuova versione della tuple. Le transazioni lettori accedono alla versione appropriata basandosi sul proprio snapshot, senza mai bloccarsi. Questo approccio elimina completamente il problema del read/write blocking che affligge i database tradizionali.

In PostgreSQL, ogni transazione riceve al suo avvio un **snapshot** che definisce quale versione delle tuple è visibile. Lo snapshot contiene tre informazioni critiche: l'ID della transazione corrente (CurrentXmin), l'elenco delle transazioni attive al momento dello snapshot (activeTransactions), e il limite massimo delle transazioni visibili (xmax). Questo meccanismo garantisce che ogni transazione veda un'immagine consistente del database al momento dell'avvio.

La visibilità delle tuple segue regole precise determinate dal transaction ID. Una tuple è visibile a una transazione se:
- xmin è uguale all'ID della transazione corrente (la tuple è stata creata dalla transazione stessa)
- xmin è inferiore a CurrentXmin e la transazione corrispondente è stata committata prima dello snapshot
- xmin è presente nella lista delle transazioni attive dello snapshot (transazione ancora in corso)

### 1.2 Vantaggi MVCC

I **vantaggi** del modello MVCC sono molteplici e profondi nell'impatto sulle prestazioni e sulla semplicità di sviluppo:

**Non-blocking readers**: Le transazioni di lettura non bloccano mai le scritture. Un SELECT può leggere dati senza acquistare lock, semplicemente utilizzando il proprio snapshot. Questo è fondamentale per workload OLTP dove le letture sono molto più frequenti delle scritture. Anche se una tabella ha milioni di righe in modifica, le letture procedono indisturbate.

**Non-blocking writers**: Le transazioni di scrittura non si bloccano reciprocamente per le letture. Due transazioni possono modificare tuple differenti contemporaneamente. Anche se modificano la stessa tuple, il sistema crea versioni multiple che verranno gestite al commit attraverso il meccanismo di serialization.

**Consistent snapshots**: Ogni transazione vede un'immagine consistente del database. Non esiste il fenomeno del "dirty read" o del "non-repeatable read" nel senso tradizionale. Una query all'interno di una transazione vedrà sempre gli stessi dati, indipendentemente dalle modifiche committate da altre transazioni durante l'esecuzione.

**Online backups**: La consistenza dei snapshot permette backup online senza blocchi. pg_basebackup e strumenti simili possono copiare i file del database mentre le transazioni continuano. Il backup sarà consistente perché basato su uno snapshot.

**Cloneable backups**: Similarmente, è possibile clonare un database per testing o development senza fermare il sistema primario. I clone sono consistenti e utilizzabili immediatamente.

### 1.3 Implementazione in PostgreSQL

L'**implementazione** di MVCC in PostgreSQL si articola su tre pilastri fondamentali:

Il **tuple header** contiene xmin e xmax che tracciano rispettivamente la transazione creatrice e quella che ha cancellato o modificato la tuple. Ogni tuple ha anche cmax (command ID all'interno della transazione) e ctid (puntatore alla versione corrente della tuple).

Il **transaction status array** (CLOG - Commit Log) mantiene lo stato di ogni transazione: in-progress, committed, o aborted. Questo array è accessibile da tutte le transazioni e viene consultato per determinare la visibilità di ogni tuple.

La **visibility map** è una struttura di ottimizzazione che traccia quali pagine sono interamente visibili a tutte le transazioni. Questa informazione permette di evitare l'accesso alla heap durante index-only scans e guida il processo di vacuum.

### 1.4 MVCC e Isolation Levels

PostgreSQL implementa quattro livelli di isolamento secondo lo standard SQL, ma il comportamento differisce significativamente dai database basati su locking:

**READ UNCOMMITTED**: In PostgreSQL si comporta come READ COMMITTED perché il modello MVCC non permette letture di dati non committati. Non esiste possibilità di dirty read.

**READ COMMITTED** (default): Ogni statement nella transazione vede le modifiche committate prima dell'inizio dello statement. Questo significa che due SELECT consecutivi possono vedere dati diversi se altre transazioni hanno committato nel frattempo.

**REPEATABLE READ**: La transazione vede uno snapshot taken all'inizio della transazione. Tutte le query vedono consistentemente lo stesso stato del database, indipendentemente dalle modifiche committate da altre transazioni.

**SERIALIZABLE**: Simile a REPEATABLE READ ma con controlli aggiuntivi per prevenire anomalie di serializzazione. PostgreSQL utilizza la tecnica del "serializable snapshot isolation" (SSI) per rilevare potenziali conflitti e richiedere retry delle transazioni.

---

## 2. Tuple Header e Versioni

### 2.1 Struttura Tuple

Ogni tuple in PostgreSQL è memorizzata in una pagina di 8KB e include un **header** che contiene metadati essenziali per MVCC. La struttura del tuple header è la seguente:

Il campo **xmin** (TransactionId, 4 bytes) memorizza l'ID della transazione che ha creato la tuple. Questo valore determina quando la tuple diventa visibile alle altre transazioni. Valori speciali includono InvalidTransactionId (0) per tuple di sistema e BootstrapTransactionId (1) per tuple create durante l'inizializzazione del database.

Il campo **xmax** (TransactionId, 4 bytes) memorizza l'ID della transazione che ha cancellato o modificato la tuple. Se xmax è 0 (InvalidTransactionId), la tuple non è stata cancellata né modificata. Se xmax è diverso da zero, la tuple è potenzialmente invisibile a seconda dello stato della transazione xmax.

Il campo **cmax** (CommandId, 4 bytes) rappresenta il command ID all'interno della transazione. Insieme a xmin, identifica univocamente quale comando della transazione ha creato la tuple. Questo è utile per implementareMVCC a livello di comando (command-level MVCC).

Il campo **ctid** (ItemPointerData, 6 bytes) è un puntatore alla versione corrente della tuple nella pagina. Quando una tuple viene aggiornata, ctid punta alla nuova versione, creando una catena di versioni. Questo campo permette di tracciare la catena di versioni durante la navigazione.

Il campo **infomask** (uint16) contiene bit flags che indicano proprietà della tuple come: HOT updated (tupla aggiornata hot), heap only (solo in heap, non in indice), has nulls (contiene valori null), has oid (contiene OID), e altri flag di stato.

### 2.2 Version Management

Il **version management** in PostgreSQL segue un modello append-only per la heap. Quando una tuple viene aggiornata:

1. La vecchia versione nella heap mantiene xmax settato all'ID della transazione che ha eseguito l'UPDATE
2. Una nuova tuple viene inserita con xmin uguale all'ID della transazione corrente e xmax = 0
3. Il ctid della vecchia tuple viene aggiornato per puntare alla nuova versione

Questo meccanismo crea una **catena di versioni** (version chain). Per trovare la versione visibile di una tuple, il sistema potrebbe dover seguire questa catena fino a trovare una versione con xmax non committato o con xmax = 0.

La catena di versioni può diventare lunga in scenari con molte modifiche sulla stessa riga. PostgreSQL ottimizza questo caso con la tecnica **HOT (Heap-Only Tuples)** che mantiene le nuove versioni nella stessa pagina quando possibile, evitando l'aggiornamento degli indici.

### 2.3 Tuple Fragmentation

La **fragmentation** è una conseguenza naturale del modello MVCC. Le tuple vecchie rimangono fisicamente nello spazio finché non vengono rimosse dal VACUUM. Questo causa:

**Spazio occupato da versioni obsolete**: Le tuple cancellate o superate occupano spazio nelle pagine. Se una tabella subisce frequenti aggiornamenti, lo spazio "morto" può crescere significativamente.

**Degradazione delle prestazioni**: Le scansioni devono saltare le tuple invisibili, spendendo cicli CPU per elaborare dati già obsoleti.

**Crescita della tabella**: Lo spazio su disco può crescere anche se il numero di righe "reali" rimane costante, causando inefficienze di storage e scanning.

**Impatto sugli indici**: Gli indici contengono puntatori alle tuple. Quando le tuple vengono aggiornate HOT, gli indici non devono essere aggiornati. Ma quando le versioni vecchie vengono rimosse, i puntatori diventano invalidi.

### 2.4 Tuple Visibility Rules

Le regole di visibilità delle tuple sono il cuore del MVCC. Per determinare se una tuple è visibile a una transazione:

**Regola 1**: Se xmin = current transaction ID, la tuple è visibile (è stata creata dalla transazione stessa).

**Regola 2**: Se xmin è nello snapshot come transazione attiva, la tuple non è visibile (la transazione creatrice è ancora in corso).

**Regola 3**: Se xmin è inferiore a snapshot's xmin ma la transazione non è committata, la tuple non è visibile.

**Regola 4**: Se xmin è committata prima dello snapshot e xmax = 0, la tuple è visibile.

**Regola 5**: Se xmax = 0, la tuple è visibile (non è mai stata cancellata/modificata).

**Regola 6**: Se xmax è committata prima dello snapshot, la tuple non è visibile (è stata cancellata/modificata).

**Regola 7**: Se xmax è nello snapshot come transazione attiva, la tuple è visibile (la cancellazione/modifica è parte della transazione corrente).

Queste regole vengono implementate nella funzione HeapTupleSatisfiesMVCC() in PostgreSQL.

---

## 3. Transaction ID e Xmin/Xmax

### 3.1 Transaction IDs

Il **Transaction ID (XID)** è un numero a 32 bit che identifica univocamente ogni transazione nel sistema. PostgreSQL assegna un XID progressivo a ogni transazione, partendo da 2 all'avvio del database (1 è riservato per BootstrapTransactionId).

Il limite di 2^32 (circa 4.3 miliardi) di transazioni porta a un fenomeno di **wrap-around**: quando il contatore raggiunge il massimo, riparte da 2. Questo richiede un meccanismo speciale chiamato "XID wraparound prevention" per evitare che le transazioni vecchie vengano confuse con quelle nuove.

PostgreSQL implementa la protezione attraverso il **Freeze Max XID**: ogni database ha un limite di età oltre il quale le tuple devono essere "congelate". Il vacuum automatico marca le tuple vecchie con xmin = 2 (BootstrapTransactionId) che è considerato sempre visibile. Questo meccanismo garantisce che le transazioni non perdano mai la visibilità dei dati.

Gli **XID speciali** includono:
- **InvalidTransactionId (0)**: utilizzato per tuple mai completate, xmax = 0 significa "non cancellata"
- **BootstrapTransactionId (1)**: utilizzato durante l'inizializzazione del database, sempre visibile
- **FrozenTransactionId (2)**: utilizzato per tuple congelate dal vacuum, sempre visibile a tutte le transazioni

### 3.2 Xmin: Creazione Tuple

Il campo **xmin** nella tuple header identifica la transazione che ha creato la tuple. Questo valore è cruciale per determinare la visibilità:

Quando una transazione esegue un INSERT, il sistema assegna l'XID corrente come xmin della nuova tuple. Questo XID è visibile solo alla transazione stessa e, una volta committato, a tutte le transazioni future che iniziano dopo il commit.

Se xmin corrisponde a una transazione ancora in corso (presente nello snapshot come "attiva"), la tuple è visibile solo a quella transazione. Altre transazioni non possono vedere questa tuple fino a quando la transazione creatrice non viene committata.

Se xmin corrisponde a una transazione abortita, la tuple non è mai visibile a nessun altra transazione. Il sistema controlla lo stato della transazione nel CLOG (Commit Log) per determinare se è stata committata o abortita.

### 3.3 Xmax: Cancellazione/Update

Il campo **xmax** nella tuple header identifica la transazione che ha cancellato o modificato la tuple:

Quando una transazione esegue un DELETE, la tuple esistente non viene fisicamente rimossa. Invece, xmax viene impostato all'XID della transazione delete. Le transazioni che iniziano dopo il commit del delete non vedranno più questa tuple.

Quando una transazione esegue un UPDATE, in realtà esegue un DELETE (imposta xmax) followed by un INSERT (crea nuova tuple con nuovo xmin). La vecchia versione rimane fino al vacuum con xmax impostato.

Se xmax = 0 (InvalidTransactionId), significa che la tuple non è mai stata cancellata o modificata. Questo è il caso più comune per le tuple "attive".

Se xmax corrisponde a una transazione in corso, la tuple è visibile solo a quella transazione (comportamento di read consistency). Questo permette alla transazione di vedere le proprie modifiche non ancora committate.

### 3.4 CLOG: Commit Log

Il **CLOG** (Commit Log) è una struttura di storage che mantiene lo stato di ogni transazione. È implementato come un set di file nella directory pg_xact/:

Ogni transazione ha un entry nel CLOG che può essere in uno di tre stati: IN_PROGRESS (in corso), COMMITTED (committata), o ABORTED (abortita). Il CLOG è consulted durante la determinazione della visibilità delle tuple.

Il CLOG è implementato con un formato compresso: 2 bit per transazione (00=in-progress, 01=committed, 10=aborted, 11=reserved). Questo permette di memorizzare informazioni per milioni di transazioni in pochi megabyte.

Il CLOG deve essere preservato durante il recovery e non viene mai troncato fino a quando tutte le tuple con XID precedenti sono state processate dal vacuum.

### 3.5 Subtransactions e XID

PostgreSQL supporta **subtransactions** per gestire savepoint e transazioni annidate. Ogni subtransaction riceve il proprio XID, ma è associata alla transazione padre:

Le subtransactions permettono a una transazione di eseguire operazioni parzialmente revertibili. Se un savepoint fallisce, solo le operazioni dopo il savepoint vengono annullate.

Il XID della subtransaction è visibile nel tuple header e nel CLOG. Le regole di visibilità considerano sia la subtransaction che la transazione padre.

Le subtransactions introducono complessità aggiuntiva nel MVCC perché devono essere gestiti correttamente durante il commit o rollback.

---

## 4. Visibility Map

### 4.1 Purpose e Struttura

La **Visibility Map** è una struttura di ottimizzazione che traccia quali pagine della heap contengono solo tuple visibili a tutte le transazioni. Questa informazione permette di saltare l'accesso alla heap in molti casi.

Ogni bit nella visibility map corrisponde a una pagina della tabella. Se il bit è impostato, significa che tutte le tuple in quella pagina sono visibili a tutte le transazioni (non ci sono tuple con XID non committati, tuple abortite, o tuple create da transazioni in corso).

La visibility map è memorizzata in un file separato con estensione .vm per ogni tabella. Insieme al file FSM (Free Space Map) che traccia lo spazio disponibile, forma il set di "fork" della relazione.

La visibility map viene aggiornata durante il VACUUM. Quando il vacuum determina che una pagina è completamente visibile, imposta il bit corrispondente. Quando le tuple in una pagina diventano parzialmente invisibili (es. nuove modifiche), il bit viene resettato.

### 4.2 Index Only Scan

L'**Index Only Scan** è una tecnica di query execution che utilizza la visibility map per evitare l'accesso alla heap:

Tradizionalmente, un index scan doveva prima trovare le chiavi nell'indice, poi accedere alla heap per verificare la visibilità delle tuple. Questo perché l'indice non contiene informazioni sulla visibilità delle tuple.

Con l'Index Only Scan, se la pagina indicata nell'indice ha il bit di visibilità impostato nella visibility map, il sistema può restituire direttamente i risultati dall'indice senza toccare la heap. Questo è significativamente più veloce per query che selezionano colonne coperte dall'indice.

Le limitazioni dell'Index Only Scan includono:
- La pagina potrebbe non essere "all visible" (bit non impostato)
- Colonne non nell'indice devono comunque essere lette dalla heap
- La query potrebbe accedere a colonne non coperte dall'indice

Per massimizzare i benefici dell'Index Only Scan, è consigliabile creare indici covering che includono tutte le colonne necessarie alla query (INCLUDE per indici B-Tree in PostgreSQL 11+).

### 4.3 Vacuum Optimization

Il **VACUUM** utilizza la visibility map per ottimizzare le proprie operazioni:

Durante un VACUUM, il sistema salta le pagine che sono "all visible" perché non contengono tuple che possono essere riutilizzate o rimosse. Questo accelera significativamente il vacuum su tabelle con molte pagine stabili.

Per le pagine non "all visible", il vacuum esamina ogni tuple per determinare se può essere rimossa o se lo spazio può essere reclamato. Le tuple con xmax committato (cancellazioni) e le tuple con XID vecchi (congelabili) vengono elaborate.

La visibility map viene aggiornata durante il vacuum:
- Bit resettati per pagine che hanno perso visibilità completa
- Bit impostati per pagine che sono diventate completamente visibili

### 4.4 Visibility Map e Autovacuum

L'**autovacuum** gestisce automaticamente la manutenzione della visibility map:

Quando una tabella riceve abbastanza modifiche (secondo i parametri autovacuum_vacuum_threshold, autovacuum_vacuum_scale_factor), l'autovacuum esegue un VACUUM che aggiorna la visibility map.

La visibility map è condivisa tra i processi attraverso la shared memory. I worker autovacuum aggiornano la mappa e i backend process la leggono per determinare se una pagina è accessibile con Index Only Scan.

Una visibility map obsoleta può causare piani di query subottimali. Se una pagina è "all visible" ma il bit non è impostato, l'optimizer potrebbe scegliere un piano meno efficiente.

### 4.5 All Visible Flag in Practice

Il flag **all visible** è cruciale per le prestazioni delle workload readonly:

Le tabelle che vengono lette frequentemente senza modifiche hanno alta probabilità di avere pagine "all visible". Dopo un VACUUM completo, quasi tutte le pagine saranno marcate.

Le tabelle con modifiche frequenti avranno meno pagine "all visible", specialmente le pagine recenti. Questo è il comportamento atteso.

Il monitoraggio della visibility map può rivelare problemi:
```sql
-- Verifica percentuali di pagine all visible
SELECT 
    schemaname, 
    relname, 
    n_live_tup, 
    n_dead_tup, 
    round(n_dead_tup::numeric / nullif(n_live_tup::numeric, 0) * 100, 2) as dead_ratio
FROM pg_stat_user_tables 
ORDER BY n_dead_tup DESC;
```

---

## 5. Write-Ahead Logging (WAL)

### 5.1 WAL Principle

Il **Write-Ahead Logging (WAL)** è il meccanismo fondamentale che garantisce la durabilità delle transazioni in PostgreSQL. Il principio è semplice ma potente: ogni modifica ai dati deve essere registrata nel WAL prima che la modifica stessa venga applicata alle pagine su disco.

Questo approccio fornisce due proprietà critiche:
- **Durabilità**: anche in caso di crash, le transazioni committate possono essere recoverite dal WAL
- **Atomicità**: il WAL registra abbastanza informazione per ricostruire lo stato del database o per annullare transazioni incomplete

Il WAL agisce come un registro append-only di tutte le modifiche. Le modifiche non sono mai scritte direttamente alla heap; invece, vengono prima scritte nel WAL, e poi applicate alla heap in background.

### 5.2 WAL vs Data Write

Il contrasto tra write-without-WAL e write-with-WAL illustra l'importanza del logging:

**Senza WAL**: Se una transazione viene committta e i dati vengono scritti direttamente alle pagine, un crash durante la scrittura lascia il database in stato inconsistente. Le pagine potrebbero essere parzialmente scritte, con alcuni blocchi modificati e altri no. Non c'è modo di sapere quali transazioni erano complete.

**Con WAL**: Ogni transazione viene registrata nel WAL prima del commit. Al commit, un fsync garantisce che il WAL record sia su disco. Se il sistema crasha, può leggere il WAL, determinare quali transazioni erano committate (record presente e sincronizzato), e riapplicare quelle modifiche. Le transazioni non committate non vengono applicate (sono "undo").

Questo è esattamente il modello ARIES (Algorithm for Recovery and Isolation Exploiting Semantics) usato da PostgreSQL e altri database enterprise.

### 5.3 Durability Guarantees

Il parametro **synchronous_commit** controlla quando il database ritorna il controllo al client dopo un commit:

**on (default)**: Il WAL viene sincronizzato su disco prima di restituire OK al client. Questo garantisce la massima durabilità ma aggiunge latenza (tempo di I/O del disco).

**off**: Il WAL è scritto asincronamente. Il commit ritorna immediatamente, ma c'è un rischio di perdita di dati se il sistema crasha prima che il WAL sia sincronizzato. L'intervallo di perdita massima è determinato da wal_writer_delay.

**local**: Come "on" ma solo per la synchronous_commit=local specifica che il WAL è scritto localmente ma potrebbe non essere replicato.

**remote_write**: Richiede che il WAL sia scritto sia localmente che sullo standby prima di restituire OK. Usato per replica sincrona.

**always**: Come "on" ma include replica sincrona.

### 5.4 WAL Record Structure

Ogni **WAL record** contiene:

**Header**:
- xl_rec_len: lunghezza del record
- xl_xlogid / xl_xloffset: posizione nel file WAL (LSN)
- xl_prev: LSN del record precedente (per linked list)
- xl_info: flags e tipo di operazione
- xl_rmid: resource manager ID
- xl_xid: transaction ID

**Body** (variabile secondo il tipo):
- Per INSERT: dati della tuple da inserire
- Per UPDATE: dati vecchi e nuovi della tuple
- Per DELETE: identificatore della tuple da cancellare

Il WAL è organizzato in segmenti (default 16MB) in pg_wal/. Ogni segmento può essere archiviato per point-in-time recovery.

### 5.5 Resource Managers

PostgreSQL usa **resource managers** per organizzare diversi tipi di operazioni nel WAL:

**Heap**: operazioni sulla heap (INSERT, UPDATE, DELETE, truncate)
**Btree**: operazioni sugli indici B-tree
**Hash**: operazioni sugli indici hash
**Gin**: operazioni sugli indici GIN
**GiST**: operazioni sugli indici GiST
**Sequence**: operazioni sulle sequenze
**CLOG**: modifiche al transaction status
**Xact**: transaction commit/abort records

Questa separazione permette recovery mirato e gestione efficiente dei record.

### 5.6 WAL and Checkpoints

I **checkpoint** nel WAL servono come punti di riferimento per il recovery:

Un checkpoint nel WAL indica che tutte le pagine dirty sono state scritte su disco e il database è in stato consistente. Durante il recovery, il sistema trova l'ultimo checkpoint e applica solo i WAL records successivi.

Il recovery proceeds così:
1. Trova l'ultimo checkpoint valido
2. Leggi il WAL da quel punto
3. Redo tutte le transazioni committate
4. Annulla le transazioni non committate

Il checkpoint include informazioni sullo stato del buffer pool, della clog, e altre strutture interne.

---

## 6. WAL Structure e Segments

### 6.1 Segment Files

I **segment files** sono l'unità di storage fisica del WAL. Ogni segmento ha una dimensione configurabile (default 16MB) e contiene sequenze di WAL records.

La directory **pg_wal/** contiene i segment files. I nomi sono esadecimali a 24 caratteri che rappresentano timeline ID (8), log segment (8), e offset (8). Esempio: 000000010000000000000001.

Quando un segmento si riempie, PostgreSQL automaticamente chiude quello corrente e ne apre uno nuovo. Questo è trasparente all'applicazione.

I segmenti possono essere compressi con gzip per ridurre lo spazio (se wal_compression è abilitato). Questo è utile per ambienti con molto write-ahead logging.

### 6.2 WAL Records

Ogni **WAL record** è composto da:

**Physical Layout**:
- LSN (Log Sequence Number): identificatore univoco della posizione nel WAL
- length: dimensione del record
- xid: transaction ID
- info: tipo di operazione
- data: i dati effettivi dell'operazione

Il WAL record è costruito dal codice che esegue la modifica. Per ogni operazione (INSERT/UPDATE/DELETE su una tabella o indice), il codice costruisce un record che descrive la modifica.

**Page Images vs Logical Records**:
PostgreSQL usa una combinazione:
- Per alcune operazioni, registra l'immagine completa della pagina (page-level)
- Per altre, registra l'operazione logica (logical)

Questo approccio ibrido fornisce flessibilità e permette recovery a livello di pagina o di record.

### 6.3 Logical vs Physical WAL

**Physical WAL**: Registra immagini complete delle pagine. Vantaggi: semplice recovery. Svantaggi: grande volume di dati.

**Logical WAL**: Registra le operazioni logiche (SQL-level). Vantaggi: più compatto, permette logical decoding. Svantaggi: recovery più complesso.

PostgreSQL usa un approccio ibrido:
- Write-Ahead Logging a livello di pagina
- Logical decoding per replica e CDC

Questo permette:
- Efficient page-level recovery
- Logical replication per standby e change data capture

### 6.4 WAL Segmentation e Circular Buffer

Il WAL funziona come un **circular buffer**:
- I segmenti vecchi possono essere riutilizzati quando il WAL è avanti
- Ma solo se non sono necessari per recovery
- La retention del WAL dipende dai backup e dalla replica

Il parametro **min_wal_size** e **max_wal_size** controllano la gestione:
- min_wal_size: spazio minimo da mantenere
- max_wal_size: spazio massimo prima di checkpoint forzato

### 6.5 WAL Archiving

Il **WAL archiving** permette di preservare i segmenti per recovery lungo:

**Configurazione**:
```sql
archive_mode = on
archive_command = 'cp %p /archive/%f'
archive_timeout = 300  -- forza archiviazione ogni 5 minuti
```

Con archiviazione, è possibile:
- Point-in-time recovery a qualsiasi momento
- Replica logica a distanza
- Backup incremental basato su WAL

Il **wal_level** controlla il dettaglio del WAL:
- minimal: solo what's strictly needed for crash recovery
- replica: include info per replica fisica
- logical: include info per replica logica (massimo dettaglio)

---

## 7. Checkpoints e Recovery

### 7.1 Checkpoint Purpose

I **checkpoint** sono punti di sincronizzazione che permettono al database di ridurre il tempo di recovery e di gestire lo spazio WAL:

**Obiettivi del checkpoint**:
1. Scrivere tutte le pagine dirty (modificate) sul disco
2. Scrivere un record di checkpoint nel WAL
3. Permettere il troncamento del WAL (rimozione segmenti vecchi non necessari)
4. Sincronizzare il control file con lo stato corrente

Senza checkpoint, il recovery dovrebbe leggere tutto il WAL dalla notte dei tempi. Con checkpoint regolari, il recovery inizia dall'ultimo checkpoint e processa solo i WAL records successivi.

### 7.2 Trigger Checkpoint

I checkpoint possono essere **automatici** o **manuali**:

**Automatici**:
- **checkpoint_timeout**: default 5 minuti. Forza un checkpoint dopo questo intervallo.
- **checkpoint_completion_target**: default 0.9. Distribuisce le writes del checkpoint su questo frazione del timeout (riduce I/O spikes).
- **max_wal_size**: default 1GB. Trigger checkpoint quando il WAL supera questa dimensione.
- **min_wal_size**: mantiene almeno questa dimensione di WAL.

**Manuali**:
```sql
CHECKPOINT;  -- checkpoint completo
CHECKPOINT SHUTDOWN;  -- checkpoint con shutdown
```

**Trigger anticipati**: checkpoint possono essere triggers anche da altre operazioni come backup (pg_start_backup/pg_stop_backup).

### 7.3 Recovery Process

Il **recovery process** dopo un crash segue questi passi:

**Fase 1 - Localizzazione checkpoint**:
- Leggi il control file per trovare l'ultimo checkpoint valido
- Il control file contiene la posizione (LSN) del checkpoint

**Fase 2 - Analisi**:
- Leggi il WAL dal checkpoint
- Determina quali transazioni erano in corso
- Identifica le pagine dirty e i loro stati

**Fase 3 - Redo**:
- Applica tutte le operazioni nel WAL successive al checkpoint
- Per ogni operazione, verifica se la pagina è già aggiornata (LSN check)
- Le operazioni con LSN < page LSN sono saltate (già applicate)

**Fase 4 - Undo**:
- Per le transazioni che non erano committate, annulla le modifiche
- Questo è il "rollback" delle transazioni incomplete
- In PostgreSQL, le modifiche delle transazioni non committate non sono applicate alla heap (il WAL registra, ma la heap ha ancora i dati vecchi)

### 7.4 Point-in-Time Recovery (PITR)

Il **PITR** permette di recoverire il database a un punto specifico nel tempo:

**Configurazione**:
```sql
recovery_target_time = '2026-05-04 15:00:00'
recovery_target_action = 'pause'
```

**Target options**:
- recovery_target_time: timestamp specifico
- recovery_target_xid: transaction ID
- recovery_target_lsn: WAL position
- recovery_target_name: restore point

**Processo**:
1. Ripristina i backup base
2. Configura recovery per usare WAL archiviati
3. Avvia il recovery
4. Il database si ferma al target specificato o alla fine del WAL

### 7.5 Crash Recovery vs Media Recovery

**Crash Recovery**: Dopo un crash del sistema (power failure, kernel panic), il database si riavvia e esegue recovery automatico. Non ci sono file corrotti; il recovery è basato solo sul WAL.

**Media Recovery**: Dopo perdita o corruzione dei file dati. Richiede:
- Restore da backup
- Applicazione dei WAL (archiviati e/o WAL residuo)
- Questo è il vero "disaster recovery"

Entrambi usano lo stesso meccanismo di recovery, ma media recovery richiede restore iniziale.

### 7.6 Backup e Recovery Integrazione

I backup e il recovery sono strettamente integrati:

**pg_basebackup** crea un backup consistente a livello di filesystem:
- Si connette al database e richiede uno checkpoint
- Copia tutti i file (data directory, tablespaces)
- Include la timeline e la posizione WAL

**Recovery**:
- Ripristina i file dal backup
- Crea un file recovery.conf (o config in PostgreSQL 12+)
- Avvia il database - il recovery parte automaticamente

La combinazione di backup base + WAL archiviati fornisce RPO (Recovery Point Objective)理论上 zero se la replica è sincrona.

---

## 8. Hot Update e Vacuum

### 8.1 Hot Update (HOT)

La tecnica **HOT (Heap-Only Tuples)** ottimizza gli UPDATE mantenendo le nuove versioni nella stessa pagina della vecchia versione:

**Funzionamento**:
1. Quando un UPDATE colpisce una tuple, il sistema verifica se c'è spazio sufficiente nella stessa pagina
2. Se lo spazio c'è, la nuova versione viene inserita nella stessa pagina
3. La vecchia versione ha xmax impostato e il suo ctid punta alla nuova versione
4. Gli indici NON vengono aggiornati - puntano ancora alla vecchia versione

**Vantaggi**:
- Evita l'aggiornamento degli indici (operazione costosa)
- Riduce lo I/O per gli aggiornamenti
- Mantiene le versioni vicine fisicamente nella heap

**Limitazioni**:
- Funziona solo se c'è spazio sufficiente nella pagina
- Crea catene di versioni più corte
- Se la pagina è piena, l'UPDATE diventa "non-HOT"

**Rilevamento**: Il campo infomask della tuple indica se l'UPDATE era HOT. Il bit HEAP_ONLY_TUPLE viene impostato.

### 8.2 VACUUM

Il **VACUUM** è il processo di manutenzione che reclaima lo spazio occupato da tuple obsolete:

**VACUUM standard**:
```sql
VACUUM my_table;  -- marca tuple come riutilizzabili
VACUUM VERBOSE my_table;  -- con output dettagliato
```

Il VACUUM:
1. Scansiona le pagine della tabella
2. Per ogni tuple, verifica se è visibile a qualche transazione attiva
3. Le tuple invisibili vengono marcate come "free space"
4. Aggiorna la visibility map
5. Rimuove le voci dagli indici per le tuple rimosse

**VACUUM FULL**:
```sql
VACUUM FULL my_table;
```

Ricostruisce completamente la tabella:
- Crea una nuova tabella con solo le tuple visibili
- Ricostruisce tutti gli indici
- La tabella risultante è compatta senza spazio vuoto
- Richiede ACCESS EXCLUSIVE lock (tabella non disponibile durante l'operazione)
- Più lento ma più efficace

**VACUUM FREEZE**:
```sql
VACUUM FREEZE my_table;
```

Marca le tuple con XID vecchi come "congelate", impostando xmin a FrozenTransactionId (2). Questo è importante per prevenire il wraparound del transaction ID.

### 8.3 Autovacuum

L'**autovacuum** è il sistema automatico di manutenzione:

**Abilitazione**:
```sql
-- In postgresql.conf
autovacuum = on
autovacuum_max_workers = 3
```

**Trigger**:
- autovacuum_vacuum_threshold + autovacuum_vacuum_scale_factor * n_live_tup
- Default: 50 righe + 10% delle righe vive

**Worker processes**:
-autovacuum_launcher: processo responsabile che lancia i worker
- autovacuum worker: processo che esegue VACUUM su una tabella specifica

**Monitoraggio**:
```sql
SELECT * FROM pg_stat_activity WHERE datname = 'mydb' AND query LIKE '%autovacuum%';
```

### 8.4 ANALYZE

L'**ANALYZE** raccoglie statistiche per l'optimizer:

```sql
ANALYZE my_table;
```

ANALYZE:
- Campiona le righe nella tabella
- Calcola distribuzione dei valori (istogrammi)
- Stima cardinalità per le query
- Informazioni su valori NULL

**Autovacuum esegue ANALYZE automaticamente** dopo VACUUM se necessario.

### 8.5 Vacuum e Transaction ID Wraparound

Il **wraparound prevention** è cruciale per la sopravvivenza del database:

Il transaction ID è a 32 bit, quindi dopo ~2 miliardi di transazioni wrap-around. Se le tuple hanno XID vecchi che sembrano "futuri", potrebbero non essere mai visibili.

**Protezione**:
- vacuum_freeze_min_age: età minima di una tuple prima di essere congelata (default: 100M)
- vacuum_freeze_table_age: età della tabella prima del freeze completo
- autovacuum_freeze_max_age: massimo XID age prima che la tabella venga processata forzatamente

**Monitoraggio**:
```sql
-- Verifica età delle tabelle
SELECT relname, age(relfrozenxid) FROM pg_class 
WHERE relkind = 'r' ORDER BY age(relfrozenxid) DESC LIMIT 10;
```

### 8.6 Visibility Map Update

Il **visibility map update** è parte integrante del VACUUM:

Quando il VACUUM processa una pagina:
- Se tutte le tuple sono visibili, imposta il bit nella visibility map
- Se alcune tuple sono invisibili, resetta il bit

La visibility map aggiornata permette:
- Index Only Scans più efficienti
- VACUUM più veloci (saltano pagine all-visible)
- Migliore utilizzo della cache

---

## 9. Concurrency Control con MVCC

### 9.1 Isolation Levels

PostgreSQL implementa quattro livelli di isolamento secondo lo standard SQL, con comportamenti specifici:

**READ COMMITTED (default)**:
Ogni comando vede le transazioni committate prima del comando stesso. Questo significa che due SELECT consecutivi possono vedere dati diversi se altre transazioni hanno committato modifiche.

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- Query 1
SELECT COUNT(*) FROM orders;  -- 1000
-- (altra transazione inserisce 100 ordini e committa)
SELECT COUNT(*) FROM orders;  -- 1100
```

**REPEATABLE READ**:
La transazione vede uno snapshot taken all'inizio della transazione. Tutte le query vedono consistentemente lo stesso stato.

```sql
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- Query 1
SELECT COUNT(*) FROM orders;  -- 1000
-- (altra transazione inserisce 100 ordini e committa)
SELECT COUNT(*) FROM orders;  -- 1000 (ancora!)
```

**SERIALIZABLE**:
Come REPEATABLE READ ma con aggiuntivi controlli per garantire che l'esecuzione sia equivalente a una esecuzione seriale. PostgreSQL usa SSI (Serializable Snapshot Isolation).

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- Se due transazioni modificano lo stesso dato:
-- Una fallirà con: could not serialize access due to concurrent update
```

### 9.2 Anomalie di Isolamento

Le anomalie che MVCC in PostgreSQL previene o gestisce:

**Dirty Read**: Lettura di dati non committati. Impossibile in PostgreSQL perché le transazioni vedono solo tuple con XID committato o transazioni in corso.

**Non-Repeatable Read**: Stessa query restituisce risultati diversi nella stessa transazione. Previsto da REPEATABLE READ e SERIALIZABLE.

**Phantom Read**: Nuove righe appaiono tra due query. Previsto da REPEATABLE READ (le nuove righe possono apparire), gestito da SERIALIZABLE.

**Write Skew**: Due transazioni leggono e scrivono dati sovrapposti. Gestito da SERIALIZABLE con SSI.

### 9.3 Write Conflicts

I **write conflicts** emergono quando due transazioni cercano di modificare la stessa tuple:

**Scenario**:
1. Transazione A: UPDATE table SET x = x + 1 WHERE id = 1
2. Transazione B: UPDATE table SET x = x + 1 WHERE id = 1
3. Entrambe committano

Sotto READ COMMITTED, entrambe vedono il valore originale e aggiungono 1. Risultato: x = old + 1 (non old + 2).

Sotto REPEATABLE READ, la seconda transazione attenderà il commit della prima e poi vedrà il nuovo valore.

Sotto SERIALIZABLE, una delle due transazioni fallirà.

### 9.4 Row-level Lock

Per le modifiche a livello di riga, PostgreSQL usa **row-level locks**:

**Acquisizione**:
```sql
SELECT * FROM orders WHERE id = 1 FOR UPDATE;  -- acquisisce lock
SELECT * FROM orders WHERE id = 1 FOR UPDATE NOWAIT;  -- errore se lock esiste
SELECT * FROM orders WHERE id = 1 FOR UPDATE SKIP LOCKED;  -- salta righe bloccate
```

**Implementazione**:
- I lock sono memorizzati nella shared lock table
- Ogni lock specifica: relation, page, tuple (o transaction ID)
- I lock vengono rilasciati alla fine della transazione

**Tipi di lock**:
- RowExclusiveLock: per UPDATE, DELETE, SELECT FOR UPDATE
- RowShareLock: per SELECT ... FOR SHARE
- AccessExclusiveLock: per ALTER TABLE, DROP TABLE, LOCK TABLE

### 9.5 Serializable Snapshot Isolation (SSI)

L'**SSI** è l'implementazione PostgreSQL per SERIALIZABLE:

SSI rileva i conflitti a livello di write-write tra transazioni serializzate:

1. Tracking delle read e write sets
2. Rilevamento di "dipolarities" (dipendenti circolari)
3. Prevenzione o rollback delle transazioni conflittuali

```sql
-- Esempio di conflitto serializable
BEGIN ISOLATION LEVEL SERIALIZABLE;
UPDATE account SET balance = balance - 100 WHERE id = 1;
COMMIT;

-- Se un'altra transazione ha letto e scritto sugli stessi account, fallisce
```

### 9.6 Advisory Locks

Gli **advisory locks** sono lock applicativi che non sono legati a dati specifici:

```sql
-- Acquire advisory lock
SELECT pg_advisory_lock(12345);
-- Release
SELECT pg_advisory_unlock(12345);
-- Try lock (non blocking)
SELECT pg_try_advisory_lock(12345);
```

Usi comuni:
- Sincronizzazione tra transazioni per logica applicativa
- Implementazione di code distribuite
- Prevenzione di esecuzione concorrente di job

### 9.7 Lock Monitoring

```sql
-- View dei lock attivi
SELECT * FROM pg_locks;

-- Lock con dettagli
SELECT l.locktype, l.relation::regclass, l.mode, l.granted, l.pid, p.query
FROM pg_locks l
JOIN pg_stat_activity p ON l.pid = p.pid
WHERE NOT l.relation IS NULL;

-- Transazioni bloccate
SELECT blocked_locks.*, blocked_activity.query AS blocked_query
FROM pg_stat_activity blocked_activity
JOIN pg_locks blocked_locks ON blocked_activity.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocked_locks.transactionid = blocking_locks.transactionid
JOIN pg_stat_activity blocking_activity ON blocking_locks.pid = blocking_activity.pid
WHERE blocked_activity.state = 'active';
```

---

## 10. Performance Tuning WAL

### 10.1 wal_buffers

Il parametro **wal_buffers** controlla la memoria dedicata al WAL:

```sql
-- Configurazione
wal_buffers = 16MB  -- default: -1 (auto, 1/32 di shared_buffers)
```

**Considerazioni**:
- Valori più grandi riducono le scritture sincronizzate
- Non dovrebbe superare i 16MB (limite interno)
- Valori eccessivi possono essere uno spreco di memoria
- Il default -1 calcola automaticamente: max(64KB, min(shared_buffers/32, 16MB))

Per workload con molte scritture concurrenti:
- Aumentare wal_buffers può ridurre I/O
- Ma non sostituisce un sistema I/O adeguato

### 10.2 wal_writer_delay

Il parametro **wal_writer_delay** controlla la frequenza del WAL writer:

```sql
-- Configurazione
wal_writer_delay = 200ms  -- default: 200ms
wal_writer_flush_after = 1MB  -- flush dopo questa quantità (PostgreSQL 13+)
```

**Trade-off**:
- Valori bassi (es. 50ms): più responsivo, meno latenza, più I/O
- Valori alti (es. 1000ms): meno I/O, più rischio di perdita dati

Per sistemi con replica sincrona:
- Valori bassi possono migliorare la replica latency

### 10.3 checkpoint_completion_target

Il parametro **checkpoint_completion_target** distribuisce le scritture del checkpoint:

```sql
-- Configurazione
checkpoint_completion_target = 0.9  -- default: 0.9
```

**Significato**:
- 0.9 significa che il checkpoint dovrebbe completare il 90% del tempo verso il prossimo checkpoint
- Questo distribuisce lo I/O su un periodo più lungo

**Esempio**:
- checkpoint_timeout = 5 min
- completion_target = 0.9
- => le writes del checkpoint sono distribuite su 4.5 minuti

**Impatto**:
- Riduce gli I/O spikes
- Ma può aumentare la durata del checkpoint
- Utile per sistemi con I/O limitato

### 10.4 synchronous_commit

Il parametro **synchronous_commit** controlla quando la transazione è considerata committata:

```sql
-- Configurazione
synchronous_commit = on  -- default: on
```

**Opzioni**:

- **off**: Ritorna immediatamente dopo la scrittura nel WAL buffer. Massimo rischio (nessuna garanzia di durabilità in caso di crash).

- **on**: Aspetta fsync del WAL prima di restituire OK. Massimo durabilità, massima latenza.

- **local**: Come "on" ma solo per commit locali. Non attende replica.

- **remote_write**: Aspetta che il WAL sia scritto sia localmente che sullo standby (non che sia committato sullo standby). Meno latenza di "always".

- **always**: Come "on" ma attende anche la replica. Per replica sincrona.

**Scelta consigliata**:
- Per massima durabilità: on
- Per massime prestazioni: off (con backup appropriato)
- Per replica sincrona: always
- Per replica asincrona con minima latenza: remote_write

### 10.5 wal_level

Il parametro **wal_level** controlla il dettaglio del WAL:

```sql
-- Configurazione
wal_level = replica  -- default: replica
```

**Opzioni**:
- **minimal**: Solo crash recovery. Minor WAL size, nessuna replica.
- **replica**: Crash recovery + replica fisica. Incluso per streaming replication.
- **logical**: Crash recovery + replica logica. Per logical replication e CDC. Massimo WAL size.

**Impatto sulle performance**:
- minimal è più performante (meno logging)
- logical è più lento (più informazione registrata)

### 10.6 Performance Monitoring

Monitorare il WAL per identificare problemi:

```sql
-- Statistiche WAL
SELECT * FROM pg_stat_database WHERE datname = current_database();

-- WAL activity
SELECT 
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), 
                                   pg_current_wal_insert_lsn())) AS uninserted_wal,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), 
                                   pg_current_wal_flush_lsn())) AS unflushed_wal;

-- Checkpoint stats
SELECT * FROM pg_stat_bgwriter;

-- Wal sender stats (replica)
SELECT * FROM pg_stat_replication;
```

### 10.7 Tuning checklist

Lista di controllo per ottimizzare WAL:

1. **Scegliere synchronous_commit appropriato**: off per speed, on per durability
2. **Dimensionare wal_buffers**: automatico va bene nella maggior parte dei casi
3. **Configurare checkpoint_completion_target**: 0.9 per distribuzione I/O
4. **Impostare checkpoint_timeout**: adatto al carico (5-30 min)
5. **Considerare wal_compression**: riduce spazio se CPU non è bottleneck
6. **Monitorare wal_writer**: verificare che non sia bloccato
7. **Verificare I/O subsystem**: il WAL è la componente più I/O intensive

### 10.8 Common Issues

**WAL filling up**:
- Aumentare max_wal_size
- Abilitare archiviazione
- Aumentare checkpoint_frequency

**Long checkpoint**:
- Aumentare checkpoint_completion_target
- Verificare I/O performance
- Considerare checkpoint_timeout più breve

**Replication lag**:
- Verificare synchronous_commit
- Aumentare wal_sender_delay
- Verificare network bandwidth

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*