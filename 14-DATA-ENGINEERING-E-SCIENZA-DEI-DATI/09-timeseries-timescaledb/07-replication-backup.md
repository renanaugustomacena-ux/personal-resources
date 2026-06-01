# Replicazione e Backup in TimescaleDB

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. Replicazione Streaming con PostgreSQL
2. Replicazione Logica e Limitazioni
3. Backup Fisico con pg_basebackup
4. WAL Archiving e PITR
5. Strumenti di Backup Avanzati

---

## 1. Replicazione Streaming con PostgreSQL

### 1.1 TimescaleDB e la Replicazione Standard

Poiché TimescaleDB è un'estensione PostgreSQL, la replicazione streaming standard funziona esattamente come su PostgreSQL puro. Il primary server scrive le modifiche nel WAL (Write-Ahead Log); il standby server si connette tramite il protocollo di replicazione, riceve il flusso WAL, e applica le modifiche al suo database locale. Dall'esterno, il setup è identico a quello di qualsiasi cluster PostgreSQL con streaming replication.

Le hypertable, i chunk, le continuous aggregate, e tutti gli oggetti di catalogo TimescaleDB si replicano normalmente attraverso il WAL. La replica è fisicamente identica al primary: contiene gli stessi chunk nella stessa struttura. Questo significa che un failover su uno standby produce immediatamente un server TimescaleDB funzionante con tutti i dati.

```sql
-- Sul primary: configurazione replicazione
-- postgresql.conf
-- wal_level = replica
-- max_wal_senders = 5
-- wal_keep_size = 1024  -- 1 GB di WAL mantenuto per i replica

-- Creazione dell'utente di replicazione
CREATE USER replicatore REPLICATION LOGIN PASSWORD 'password_sicura';

-- pg_hba.conf (su primary)
-- host replication replicatore standby_ip/32 scram-sha-256

-- Sul standby: avvio della replica
pg_basebackup -h primary_host -U replicatore -D /var/lib/postgresql/16/main \
    --wal-method=stream --checkpoint=fast --progress

-- Configurazione dello standby (postgresql.conf)
-- primary_conninfo = 'host=primary_host port=5432 user=replicatore password=...'
-- hot_standby = on
```

### 1.2 Considerazioni Specifiche per TimescaleDB

Alcune configurazioni di TimescaleDB richiedono attenzione nella replica. Il parametro `timescaledb.max_background_workers` deve essere configurato in modo identico (o maggiore) su primary e standby, altrimenti lo standby potrebbe avere problemi ad applicare alcune operazioni WAL che dipendono dai worker in background.

Le continuous aggregate in stato di refresh producono WAL aggiuntivo rispetto a una tabella ordinaria: durante il refresh, vengono create, aggiornate, ed eliminate righe nella tabella materiale interna. Su carichi con molte continuous aggregate con refresh frequenti, questo può aumentare il lag della replica durante i picchi di refresh.

```sql
-- Monitoraggio del lag di replica (da eseguire sul primary)
SELECT
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes,
    write_lag,
    flush_lag,
    replay_lag
FROM pg_stat_replication;
```

---

## 2. Replicazione Logica e Limitazioni

### 2.1 Limiti della Replicazione Logica con Hypertable

La replicazione logica di PostgreSQL (usando `PUBLICATION` e `SUBSCRIPTION`) presenta limitazioni significative con le hypertable di TimescaleDB. Il problema principale è che PostgreSQL replica logicamente le modifiche alle tabelle fisiche (i chunk), non alla hypertable virtuale. Sul lato subscriber, non c'è TimescaleDB che ricostruisce automaticamente la struttura hypertable: i chunk arrivano come tabelle ordinarie senza la struttura di partizionamento.

TimescaleDB Enterprise offre una soluzione con **pglogical** e il supporto nativo per la replicazione logica tra hypertable. Nella versione Community, è possibile usare la replicazione logica per tabelle ordinarie nello stesso database, ma le hypertable devono essere replicate attraverso la replicazione fisica (streaming).

```sql
-- Replicazione logica su tabelle ORDINARIE (non hypertable) - funziona normalmente
CREATE PUBLICATION pub_tabelle_ordinarie FOR TABLE 
    dispositivi, configurazioni, soglie_allarme;

-- Sul subscriber
CREATE SUBSCRIPTION sub_tabelle_ordinarie
    CONNECTION 'host=primary dbname=produzione user=replicatore password=...'
    PUBLICATION pub_tabelle_ordinarie;
```

### 2.2 Caso d'Uso: Upgrade di Versione PostgreSQL

La replicazione logica è però utile per upgrade di versione PostgreSQL senza downtime. La procedura prevede: avviare un nuovo server PostgreSQL con la versione target, configurare la replica logica dal vecchio al nuovo server per le tabelle ordinarie, e eseguire un pg_basebackup fisico per la struttura TimescaleDB iniziale, poi switchover del traffico al nuovo server.

---

## 3. Backup Fisico con pg_basebackup

### 3.1 Backup Completo

`pg_basebackup` esegue un backup fisico consistente dell'intero cluster PostgreSQL, incluse tutte le estensioni, hypertable, chunk, indici, e catalog di sistema. È il metodo di backup raccomandato per TimescaleDB in produzione.

```bash
# Backup completo con WAL incluso
pg_basebackup \
    --host=localhost \
    --username=replicatore \
    --pgdata=/backup/$(date +%Y%m%d_%H%M%S) \
    --format=tar \
    --compress=gzip \
    --wal-method=stream \
    --checkpoint=fast \
    --progress \
    --verbose

# Backup su S3 (con barman o pgBackRest)
# Richiede configurazione archive_command per WAL
```

### 3.2 Verifica del Backup

```bash
# Verifica dell'integrità del backup (PostgreSQL 17+)
pg_basebackup --verify-checksums \
    --pgdata=/backup/20260506_120000

# Test di restore su istanza separata (essenziale in produzione)
pg_restore_backup \
    --pgdata=/restore_test \
    --backup=/backup/20260506_120000

# Avvio dell'istanza di test
postgres -D /restore_test &
psql -d telemetria -c "SELECT COUNT(*) FROM telemetria_sensori;"
psql -d telemetria -c "SELECT * FROM timescaledb_information.hypertables;"
```

---

## 4. WAL Archiving e PITR

### 4.1 Configurazione dell'Archiving

Il Point-In-Time Recovery (PITR) permette di ripristinare il database a un qualsiasi momento nel passato, a patto di conservare il WAL continuo dal momento del backup fisico base fino al target. Questo è fondamentale per la disaster recovery: se si verifica un'eliminazione accidentale di dati, si può ripristinare il database al momento immediatamente precedente all'incidente.

```ini
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /wal_archivio/%f && cp %p /wal_archivio/%f'

# Per archivio su S3 (usando wal-g o pgBackRest)
archive_command = 'wal-g wal-push %p'
restore_command = 'wal-g wal-fetch %f %p'
```

### 4.2 Procedura di PITR

```bash
# 1. Restore del backup base
cp -r /backup/20260506_120000/* /var/lib/postgresql/data/

# 2. Configurazione del recovery target
cat >> /var/lib/postgresql/data/postgresql.conf << 'CONF'
restore_command = 'cp /wal_archivio/%f %p'
recovery_target_time = '2026-05-06 14:30:00+01'
recovery_target_action = 'promote'
CONF

# 3. Creazione del file di segnale
touch /var/lib/postgresql/data/recovery.signal

# 4. Avvio: PostgreSQL applica il WAL fino al target
pg_ctl start -D /var/lib/postgresql/data

# 5. Verifica del recovery
psql -c "SELECT pg_is_in_recovery();"  -- deve restituire FALSE dopo il promote
psql -c "SELECT COUNT(*) FROM telemetria_sensori WHERE tempo < '2026-05-06 14:30:00';"
```

---

## 5. Strumenti di Backup Avanzati

### 5.1 pgBackRest

pgBackRest è lo strumento di backup raccomandato per ambienti PostgreSQL di produzione, con supporto nativo per TimescaleDB. Offre backup incrementali, compressione e cifratura, backup paralleli multi-thread, e upload diretto su S3/Azure/GCS.

```ini
# pgbackrest.conf
[global]
repo1-path=/var/lib/pgbackrest
repo1-retention-full=2
repo1-retention-diff=7
process-max=4

# Per S3
repo1-type=s3
repo1-s3-bucket=mio-bucket-backup
repo1-s3-region=eu-south-1
repo1-s3-endpoint=s3.eu-south-1.amazonaws.com

[db-primary]
pg1-path=/var/lib/postgresql/16/main
pg1-socket-path=/var/run/postgresql
```

```bash
# Inizializzazione e primo backup full
pgbackrest --stanza=db-primary stanza-create
pgbackrest --stanza=db-primary --type=full backup

# Backup incrementale (usa solo il WAL dall'ultimo backup)
pgbackrest --stanza=db-primary --type=incr backup

# Restore a un punto preciso
pgbackrest --stanza=db-primary --target="2026-05-06 14:30:00+01" \
    --target-action=promote restore

# Verifica dell'integrità del repository
pgbackrest --stanza=db-primary check
pgbackrest --stanza=db-primary verify
```

### 5.2 timescaledb-parallel-copy per Dump Logico

Per backup logici (export in formato leggibile/importabile), TimescaleDB fornisce `timescaledb-parallel-copy`, uno strumento che accelera significativamente l'import di grandi quantità di dati CSV rispetto al `COPY` standard di PostgreSQL.

```bash
# Export di una hypertable in CSV
psql -d produzione -c "\COPY telemetria_sensori TO '/backup/telemetria.csv' CSV HEADER"

# Import parallelo con timescaledb-parallel-copy
timescaledb-parallel-copy \
    --db-name=restore \
    --table=telemetria_sensori \
    --file=/backup/telemetria.csv \
    --header-line \
    --workers=8 \
    --reporting-period=5s \
    --batch-size=50000
```

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*
