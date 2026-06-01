# PostgreSQL Streaming Replication

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
1. Replication Fundamentals
2. Streaming Replication Setup
3. Replication Slots
4. WAL Sender/Receiver
5. Async vs Sync Replication
6. Hot Standby
7. Physical Replication
8. Replication Monitoring
9. Failover e Switchover
10. High Availability Configurations

---

## 1. Replication Fundamentals

### 1.1 Replication Types

PostgreSQL offre diversi tipi di replica per soddisfare differenti esigenze:

**Physical Replication**: Replica a livello di byte l'intero cluster. È la replica più basilare - copia esattamente i file del database. Include tutto: database, tabelle, indici, etc. È ideale per disaster recovery e high availability dove serve una copia identica.

**Logical Replication**: Replica a livello di singole operazioni DML (INSERT, UPDATE, DELETE). Permette replica selettiva - solo alcune tabelle o database. Utile per: aggiornamenti parziali, migrazioni, integrare dati da multiple fonti. Più flessibile ma con overhead maggiore.

**Streaming Replication**: Modalità di trasmissione in tempo reale del WAL. Può essere combinata con physical o logical. In tempo reale significa che il WAL viene trasmesso appena scritto, minimizzando il lag. Questo documento si concentra sulla streaming replication fisica.

**Synchronous vs Asynchronous**: La replica sincrona attende la conferma dal standby prima di completare la transazione. La asincrona invia e dimentica. Sincrona garantisce zero perdita dati (RPO=0) ma aggiunge latenza.

### 1.2 Architecture

L'architettura di streaming replication coinvolge diversi componenti:

**Primary (Master)**: Il server principale che accetta le scritture. Genera il WAL e lo trasmette ai standby. Mantiene le connessioni di replica attive.

**Standby (Replica)**: Server che riceve e applica le modifiche dal primary. Può essere in modalità hot (accetta query di lettura) o warm (solo recovery).

**WAL Sender**: Processo sul primary che legge il WAL e lo trasmette ai standby. Gestisce multiple connessioni simultanee. Traccia lo stato di ogni standby.

**WAL Receiver**: Processo sul standby che si connette al primary, riceve il WAL, lo scrive localmente, e notifica il recovery process.

**Replication Slots**: Meccanismo per tracciare quali WAL sono necessari a ogni standby, prevenendo la rimozione prematura del WAL dal primary.

### 1.3 Use Cases

La replica in PostgreSQL risolve diversi scenari:

**High Availability**: Se il primary fallisce, un standby può essere promosso per continuare le operazioni. Minimizza il downtime.

**Read Scaling**: Gli standby possono servire query di sola lettura (in hot standby mode). Distribuisce il carico di lettura su multiple copie.

**Disaster Recovery**: Un standby geograficamente separato può sopravvivere a disaster che colpiscono il data center primario. Fornisce protezione contro perdita dati.

**Backup**: Gli standby possono essere usati per backup online senza impattare il primary. Backup consistenti senza query block.

**Reporting e Analytics**: Query pesanti di reporting possono essere eseguite sugli standby senza impattare le operazioni OLTP sul primary.

---

## 2. Streaming Replication Setup

### 2.1 Primary Configuration

La configurazione del primary richiede modifiche al file postgresql.conf:

```sql
-- Livello WAL - replica include le informazioni necessarie per la replica fisica
wal_level = replica

-- Numero massimo di connessioni di replica concorrenti
max_wal_senders = 10

-- Slot di replica per tracciare i WAL necessari a ogni standby
max_replication_slots = 10

-- WAL da mantenere anche se nessuno lo richiede (minimo da conservare)
wal_keep_size = 1GB  -- default: 0 (da PostgreSQL 13+)

-- Opzionale: compressione WAL per ridurre bandwidth
wal_compression = off  -- può essere on per risparmiare bandwidth
```

Dopo le modifiche, ricaricare la configurazione:
```sql
SELECT pg_reload_conf();
-- o
systemctl reload postgresql
```

### 2.2 Create Replication User

Creare un utente dedicato per la replica con privilegi appropriati:

```sql
-- Creare l'utente con permesso REPLICATION
CREATE USER replicator WITH REPLICATION PASSWORD 'strong_password_here';

-- Alternativa: creare un ruolo con solo permessi di replica
CREATE ROLE replicator WITH
    LOGIN
    REPLICATION
    PASSWORD 'strong_password_here';
```

Il permesso REPLICATION permette:
- Connessioni di replica
- Accesso ai file di WAL
- Nessun altro permesso sul database

### 2.3 pg_hba.conf

Configurare pg_hba.conf per permettere le connessioni di replica:

```sql
# Syntax: host database user address auth_method

# Per replica con password (md5)
host replication replicator 10.0.0.0/24 md5

# Per replica con password (scram-sha-256 - più sicuro)
host replication replicator 10.0.0.0/24 scram-sha-256

# Per localhost (se necessario)
host replication replicator 127.0.0.1/32 md5
```

Dopo le modifiche, ricaricare:
```sql
SELECT pg_reload_conf();
```

### 2.4 Standby Setup

Creare un standby dal primary usando pg_basebackup:

```bash
# Sintassi base
pg_basebackup -h primary_host -D /var/lib/postgresql/14/main -U replicator -P -Xs

# Con compressione
pg_basebackup -h primary_host -D /var/lib/postgresql/14/main -U replicator -P -Xs -z

# Esempio completo
pg_basebackup -h 10.0.0.1 -D /var/lib/postgresql/14/main -U replicator -P -Xs -v
```

Parametri:
- -h: hostname del primary
- -D: directory dove creare i dati
- -U: utente di replica
- -P: mostra progressione
- -Xs: streaming WAL (preferito)

### 2.5 Recovery Config

Configurare il standby per connettersi al primary:

PostgreSQL 12+ usa postgresql.auto.conf (creato automaticamente da pg_basebackup):

```sql
-- postgresql.auto.conf (non postgresql.conf!)
primary_conninfo = 'host=10.0.0.1 port=5432 user=replicator application_name=standby1'

-- Opzioni aggiuntive
-- primary_conninfo = 'host=10.0.0.1 port=5432 user=replicator password=xxx application_name=standby1'
```

Avviare il standby:
```bash
systemctl start postgresql
systemctl status postgresql
```

Verificare la replica:
```sql
-- Sul primary
SELECT * FROM pg_stat_replication;
```

---

## 3. Replication Slots

### 3.1 What are Slots

I **Replication Slots** sono un meccanismo che garantisce che il primary non rimuova il WAL necessario ai standby, anche quando il standby è disconnesso.

**Funzionamento**: Quando uno standby si connette e usa uno slot, il primary sa esattamente quale WAL deve conservare. Anche se lo standby si disconnette (per manutenzione, network issues, etc.), il WAL viene preservato.

**Senza slot**: Il primary potrebbe rimuovere WAL che il standby non ha ancora ricevuto. Alla riconnessione, il standby non può recuperare e deve essere ricostruito.

**Con slot**: Il WAL viene conservato fino a quando lo standby non lo richiede esplicitamente. Questo garantisce recovery anche dopo lunghe disconnessioni.

### 3.2 Create Slot

Creare slot sul primary:

```sql
-- Slot fisico per streaming replica
SELECT * FROM pg_create_physical_replication_slot('standby1_slot');

-- Con nome visibile
SELECT pg_create_physical_replication_slot('standby1_slot', true);
```

Il secondo parametro (true) rende il nome visibile in pg_replication_slots.

### 3.3 Manage Slots

Gestire gli slot esistenti:

```sql
-- Listare tutti gli slot
SELECT 
    slot_name,
    slot_type,
    database,
    active,
    restart_lsn,
    confirmed_flush_lsn
FROM pg_replication_slots;

-- Verificare se uno slot è attivo (standby connesso)
SELECT * FROM pg_replication_slots WHERE active = true;

-- Eliminare uno slot
SELECT pg_drop_replication_slot('standby1_slot');

-- Monitorare WAL conservato per ogni slot
SELECT 
    slot_name,
    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as wal_to_keep
FROM pg_replication_slots;
```

### 3.4 Physical vs Logical

Distinzione tra tipi di slot:

**Physical Replication Slots**:
- Usati per replica fisica
- Tracciano WAL a livello di byte
- Non specificano un database
- Sono per l'intero cluster

```sql
SELECT pg_create_physical_replication_slot('my_slot');
```

**Logical Replication Slots**:
- Usati per replica logica
- Tracciano le modifiche a livello DML
- Associati a un database specifico
- Permettono replica selettiva

```sql
-- Creare slot logico
SELECT pg_create_logical_replication_slot('my_logical_slot', 'pg_output');

-- Usato per decodifica delle modifiche
SELECT * FROM pg_logical_slot_get_changes('my_logical_slot', NULL, NULL);
```

---

## 4. WAL Sender/Receiver

### 4.1 WAL Sender

Processo primary:
- Legge WAL
- Invia a standby
- Traccia progresso

### 4.2 WAL Receiver

Processo standby:
- Riceve WAL
- Scrive su disco
- Informa stato

### 4.3 Monitoring

Monitorare:
```sql
-- Primary
SELECT * FROM pg_stat_replication;

-- Standby
SELECT * FROM pg_stat_wal_receiver;
```

### 4.4 Replication Lag

Verificare lag:
```sql
SELECT 
    client_addr,
    state,
    lag 
FROM pg_stat_replication;
```

---

## 5. Async vs Sync Replication

### 5.1 Async Replication

La replica **asincrona** è il default. Le transazioni completano immediatamente sul primary, senza aspettare conferma dal standby.

**Comportamento**:
1. Client esegue COMMIT sul primary
2. Primary scrive e conferma al client
3. WAL viene trasmesso al standby in background
4. Standby applica il WAL quando arriva

**Vantaggi**:
- Zero latenza aggiuntiva per le transazioni
- Migliori performance write sul primary
- Semplicità di configurazione

**Rischi**:
- RPO > 0: possibile perdita dati se il primary crash prima della trasmissione
- Lag variabile tra primary e standby
- In caso di disaster, si possono perdere le ultime transazioni

**Latenza tipica**: millisecondi a secondi, dipende dal carico e network.

### 5.2 Sync Replication

La replica **sincrona** garantisce che le transazioni siano applicate anche sul standby prima di confermare al client.

```sql
-- Abilitare replica sincrona sul primary
synchronous_commit = on
synchronous_standby_names = 'standby1'
```

**Comportamento**:
1. Client esegue COMMIT sul primary
2. Primary aspetta che il standby confermi la ricezione del WAL
3. Primary conferma al client
4. Standby applica il WAL

**Vantaggi**:
- RPO = 0: nessuna perdita dati garantita
- Consistente tra primary e standby

**Svantaggi**:
- Latenza aggiuntiva: ogni COMMIT aspetta il standby
- Se il standby è giù, le transazioni bloccano

### 5.3 Remote Apply

Opzioni per synchronous_commit:

```sql
-- Commit locale + conferma sincrona (default)
synchronous_commit = on

-- Scrittura locale + scrittura remota (Più sicuro)
synchronous_commit = remote_write

-- Solo commit locale (disabilita sincronismo)
synchronous_commit = off

-- Come 'on' ma per replica asincrona
synchronous_commit = local
```

**remote_write** vs **on**:
- on: aspetta fsync sul primary e conferma dal standby
- remote_write: aspetta scrittura su OS del standby, non fsync
- Più veloce di on, meno sicuro di on

### 5.4 Quorum Commit

Per maggiore protezione, configurare quorum di standby:

```sql
-- 2 di 3 standby devono confermare
synchronous_standby_names = 'standby1, standby2, standby3'

-- Con priorità (solo standby1 + uno qualsiasi degli altri)
synchronous_standby_names = 'standby1 (1), standby2 (2), standby3 (2)'

-- Quorum: almeno 2 standby
synchronous_standby_names = 'ANY 2 (standby1, standby2, standby3)'
```

**Configurazione**:
```sql
-- quorum: almeno N standby confermano
synchronous_standby_names = 'ANY 2 (standby1, standby2, standby3)'

-- first: solo il primo nella lista
synchronous_standby_names = 'standby1, standby2'
```

---

## 6. Hot Standby

### 6.1 Enable Hot Standby

Abilitare standby:
```sql
-- postgresql.conf (standby)
hot_standby = on
hot_standby_feedback = on
```

### 6.2 Read Queries

Query su standby:
- Read-only
- Non blocking primary
- Eventually consistent

### 6.3 Conflicts

Conflitti risolti:
- vacuum vs queries
- lock timeouts
- hot_standby_feedback aiuta

### 6.4 Use Cases

- Read scaling
- Reporting queries
- Backup

---

## 7. Physical Replication

### 7.1 Base Backup

Backup completo:
```sql
pg_basebackup -h primary -D /backup -U replicator -P -Xs
```

### 7.2 Continuous Recovery

Continuous recovery:
- WAL streaming
- Standby sempre aggiornato
- Point-in-time recovery

### 7.3 Replication Slots

Con slot:
- WAL non cancellato
- Standby garantito recovery

### 7.4 Limitations

Limiti:
- Same major version
- Same OS/architecture
- Complete cluster replica

---

## 8. Replication Monitoring

### 8.1 pg_stat_replication

Monitorare primaria:
```sql
SELECT 
    pid,
    usesysid,
    usename,
    application_name,
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    lag
FROM pg_stat_replication;
```

### 8.2 pg_stat_wal_receiver

Monitorare standby:
```sql
SELECT * FROM pg_stat_wal_receiver;
```

### 8.3 Lag Monitoring

Lag critico:
```sql
-- bytes lag
SELECT pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) 
FROM pg_stat_replication;

-- time lag (approximated)
SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;
```

### 8.4 Alerts

Set up alerts per:
- Lag crescente
- Standby down
- Replication errors

---

## 9. Failover e Switchover

### 9.1 Failover

Failover automatico:
- Use patroni, repmgr
- Promote standby
- Update DNS

### 9.2 Switchover

Switchover planned:
- Graceful switch
- Primary becomes standby
- No data loss

### 9.3 pg_ctl promote

Promuovere standby:
```sql
-- On standby
pg_ctl promote -D /var/lib/postgresql/14/main
```

### 9.4 Timeline History

Timeline switching:
- New timeline after failover
- pg_timeline tables
- Understandable via pg_controldata

---

## 10. High Availability Configurations

### 10.1 Patroni

Patroni per HA:
- Distributed consensus
- Automatic failover
- PostgreSQL management

### 10.2 repmgr

repmr for HA:
- Open source
- Management commands
- Automatic failover

### 10.3 pgpool-II

pgpool per:
- Connection pooling
- Load balancing
- Automatic failover

### 10.4 Cloud Solutions

Cloud providers:
- AWS RDS/Aurora
- Azure Database
- Cloud SQL GCP

### 10.5 Architecture Patterns

Patterns:
- 1 primary, 1 sync, N async
- 2 primaries (write to both)
- Cascaded replication

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*