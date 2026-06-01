# PostgreSQL Disaster Recovery e Backup

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
1. Backup Strategies
2. pg_dump
3. pg_basebackup
4. Continuous Archiving
5. Point-in-Time Recovery
6. Backup Verification
7. Disaster Recovery Planning
8. RTO/RPO Considerations
9. Backup Automation
10. Restore Procedures

---

## 1. Backup Strategies

### 1.1 Backup Types

Le strategie di backup in PostgreSQL si dividono in tre categorie principali, ciascuna con caratteristiche e usi specifici:

**Backup Logico (pg_dump)**: Questo approccio esporta il contenuto del database in uno schema di file SQL leggibile. Il backup contiene comandi CREATE TABLE, INSERT, e tutti gli oggetti del database. Il vantaggio principale è la portabilità: il backup può essere ripristinato su qualsiasi versione di PostgreSQL (anche futura), rendendolo ideale per migrazioni e archiviazione a lungo termine. Lo svantaggio è che per database molto grandi, il backup e il restore possono essere lenti.

**Backup Fisico (pg_basebackup)**: Questo approccio copia direttamente i file binari del database. È significativamente più veloce del backup logico e produce un backup consistente a livello di filesystem. Il restore è quasi istantaneo rispetto al restore logico. Lo svantaggio è che il backup deve essere ripristinato su una versione identica di PostgreSQL con la stessa configurazione.

**Continuous Archiving (WAL)**: Questo approccio archivia continuamente i Write-Ahead Logs, permettendo point-in-time recovery. Combinato con un backup base, permette di recoverire il database a qualsiasi momento tra i backup. È essenziale per scenari di disaster recovery dove il RPO (Recovery Point Objective) deve essere minimo.

### 1.2 When to Use Each Type

La scelta del tipo di backup dipende da diversi fattori:

**Usare pg_dump quando**:
- Il database è piccolo (< 100GB)
- Si necessita portabilità tra versioni diverse
- Si fa migrazione di database
- Si necessita backup selettivo di specifiche tabelle
- Si archiviano dati per compliance (formato SQL leggibile)

**Usare pg_basebackup quando**:
- Il database è grande (> 100GB)
- Il tempo di backup/restore è critico
- Si necessita backup consistente per replica
- Si implementa soluzione di disaster recovery completa

**Usare continuous archiving quando**:
- RPO deve essere minimo (pochi minuti di perdita dati)
- Si necessita point-in-time recovery
- Si implementa replica geografica
- Si hanno requisiti di compliance stringenti

### 1.3 Backup Frequency

La frequenza dei backup bilancia protezione dei dati con overhead operativo:

**Backup completo giornaliero**: Per la maggior parte dei sistemi, un backup completo al giorno è sufficiente. Questo fornisce un punto di restore guarantee ogni 24 ore. Combinato con WAL archiving, il punto massimo di perdita è limitato al WAL non ancora archiviato.

**Backup ogni 4-8 ore**: Per sistemi con RPO più stringente (es. 4 ore), si eseguono backup più frequenti. Questo riduce la finestra di perdita dati in caso di disaster.

**WAL archiving continuo**: Con archiviazione continua, il RPO è limitato solo dall'intervallo di archiviazione (archive_timeout, tipicamente 5-60 minuti). Per RPO quasi-zero, si considera replica sincrona.

**Retenzione settimanale/mensile**: I backup completi più vecchi possono essere archiviati su storage a lungo termine per compliance o per recovery da corruption a lungo termine.

### 1.4 Backup Strategy Architecture

Un'architettura di backup robusta tipicamente include:

1. **Backup locale**: pg_basebackupnotturno su storage locale o NAS
2. **Archiviazione WAL**: verso storage separato dal primary
3. **Backup off-site**: copia dei backup verso altra location
4. **Backup cloud**: verso object storage (S3, GCS, Azure Blob)

Questa gerarchia garantisce recovery anche da eventi catastrofici che colpiscono il data center primario.

---

## 2. pg_dump

### 2.1 Basic Usage

**pg_dump** è lo strumento standard per creare backup logici di database PostgreSQL. Opera leggendo il database e producendo un file di output con comandi SQL che ricreano il contenuto.

```bash
# Backup completo con formato custom (compresso)
pg_dump -U postgres -Fc -f mydb_backup.dump mydb

# Backup con password via environment
PGPASSWORD=mypassword pg_dump -U postgres -Fc mydb > backup.dump

# Backup con compressione gzip
pg_dump -U postgres mydb | gzip > backup.sql.gz
```

Il comando si connette al database specificato, legge tutti gli oggetti (tabelle, indici, viste, funzioni, etc.), e li serializza nel formato scelto. Non blocca il database durante l'operazione - le letture sono consistenti perché il database continua a funzionare normalmente.

### 2.2 Output Formats

PostgreSQL supporta quattro formati di output per pg_dump:

**Plain (default)**: Produce un file SQL in testo semplice. È il formato più leggibile e portabile. Non supporta parallelismo. È adatto per database piccoli o per essere editato manualmente.

```bash
pg_dump -U postgres mydb > backup.sql
```

**Custom (-Fc)**: Formato compresso custom di PostgreSQL. Supporta restore parallelo con pg_restore. Offre compressione significativa (tipicamente 5-10x). È il formato raccomandato per la maggior parte dei casi.

```bash
pg_dump -Fc -f backup.dump mydb
```

**Directory (-Fd)**: Crea una directory con multiple file, uno per ogni oggetto. Supporta dump parallelo con -j. Più flessibile per manipolazione manuale.

```bash
pg_dump -Fd -j 4 -f backup_dir mydb
```

**Tar (-Ft)**: Produce un tar archive compresso. Combina elementi di custom e directory. Utile per backup che devono essere trasferiti come singolo file.

```bash
pg_dump -Ft -f backup.tar mydb
```

### 2.3 Selective Backup

pg_dump permette di selezionare specifici oggetti:

```bash
# Backup di una singola tabella
pg_dump -t users mydb > users.sql

# Backup di più tabelle
pg_dump -t orders -t order_items mydb > orders.sql

# Backup solo schema (no data)
pg_dump -s mydb > schema.sql

# Backup solo data (no schema)
pg_dump -a mydb > data.sql

# Backup di uno specifico schema
pg_dump -n myschema mydb > schema_backup.sql

# Backup escludendo una tabella
pg_dump --exclude-table=logs mydb > backup.sql
```

### 2.4 Parallel Dumps

Per database grandi, il dump parallelo accelera significativamente il processo:

```bash
# Dump parallelo su 4 job
pg_dump -Fd -j 4 -f backup_dir mydb

# Con compressione
pg_dump -Fd -j 4 -f backup_dir -Z 6 mydb
```

Il parametro -j specifica il numero di worker thread. Idealmente dovrebbe corrispondere al numero di CPU cores. Il dump parallelo funziona solo con il formato directory (-Fd).

### 2.5 pg_dumpall

Per backup di tutto il cluster (incluso ruoli e database):

```bash
# Backup di tutti i database
pg_dumpall -U postgres > all_databases.sql

# Solo ruoli e settings
pg_dumpall -r -U postgres > roles.sql

# Solo global objects
pg_dumpall -g > globals.sql
```

pg_dumpall non supporta il formato custom, produce solo SQL plaintext.

### 2.6 Consistency Considerations

Per garantire consistenza, pg_dump crea uno snapshot transaction del database. Questo significa che il backup rappresenta lo stato del database al momento in cui lo snapshot è stato creato. Per backup che devono essere esattamente consistenti (es. per replica), si può usare la modalità with快照:

```bash
# Backup con snapshot consistente
pg_dump -Fc mydb > backup.dump
```

In scenari con tabelle molto grandi che vengono modificate durante il dump, si può considerare l'uso di pg_dump con --single-transaction per garantire consistenza, ma questo potrebbe causare lock prolungati.

---

## 3. pg_basebackup

### 3.1 Basic Usage

**pg_basebackup** crea una copia fisica binaria del database. È lo strumento preferito per backup consistenti di database grandi, perché è significativamente più veloce di pg_dump e produce un backup che può essere ripristinato rapidamente.

```bash
# Backup base basilare
pg_basebackup -h localhost -D /backup/base -U replicator -P -Xs

# Con compressione tar
pg_basebackup -h localhost -Ft -z -D /backup -U replicator
```

Il parametro -P mostra la progressione del backup. -Xs specifica il metodo di trasferimento del WAL.

Il backup è consistente a livello di filesystem perché pg_basebackup internally esegue un checkpoint prima di iniziare la copia e include il WAL necessario per garantire consistenza.

### 3.2 Replication Methods

PostgreSQL supporta diversi metodi per trasferire il WAL durante il backup:

**-Xs (streaming)**: Preferito per la maggior parte dei casi. Il WAL viene trasmesso in streaming dal server mentre i file vengono copiati. Non richiede archiviazione WAL attiva. È la modalità più efficiente.

```bash
pg_basebackup -h localhost -D /backup -U replicator -Xs -P
```

**-Xstream**: Simile allo streaming ma utilizza replication slot per tracciare la posizione. Utile per ripristinare la replica dopo il backup senza perdere WAL.

```bash
pg_basebackup -h localhost -D /backup -U replicator -Xstream -P
```

**-Xfetch**: Il metodo legacy dove il WAL viene copiato via tabella di archiviazione. Richiede che archive_mode sia attivo. Meno efficiente, usato solo per compatibilità.

```bash
pg_basebackup -h localhost -D /backup -U replicator -Xfetch -P
```

### 3.3 Tar Format e Compressione

pg_basebackup può produrre output in formato tar compresso:

```bash
# Tar con gzip
pg_basebackup -Ft -z -D /backup -h localhost -U replicator

# Tar con pigz (parallel gzip)
pg_basebackup -Ft -D /backup -h localhost -U replicator --checkpoint=fast
```

Il formato tar permette di estrarre il backup su filesystem diversi o trasferirlo più facilmente. Ogni tablespace viene memorizzato in un file tar separato.

### 3.4 Verification e Checkpoint

```bash
# Checkpoint fast per backup più veloce
pg_basebackup -h localhost -D /backup -U replicator --checkpoint=fast

# Verify checksum dei file
pg_basebackup -h localhost -D /backup -U replicator --verify-checksums
```

### 3.5 Scalabilità

Per database molto grandi, pg_basebackup può essere ottimizzato:

```bash
# Escludere pg_wal (verrà incluso dal WAL streams)
pg_basebackup -h localhost -D /backup -U replicator --no-wal

# Parallel backup (PostgreSQL 17+)
pg_basebackup -h localhost -D /backup -U replicator -j 4
```

### 3.6 Incremental Backup

PostgreSQL non supporta nativamente backup incrementale, ma tool di terze parti lo permettono:

**pg_rman**: Tool open source che supporta backup incrementale analizzando i file modificati. Mantiene un catalogo dei backup e permette restore di specifici backup incrementali.

**Barman**: Enterprise tool con supporto backup incrementale, deduplicazione, e gestione avanzata.

**pgBackRest**: Tool di backup con supporto per deduplicazione e backup incrementale. Molto efficiente per database grandi.

Questi tool analizzano i file della tabella e copiano solo quelli modificati dopo l'ultimo backup, riducendo significativamente tempo e spazio per database grandi.

---

## 4. Continuous Archiving

### 4.1 Enabling WAL Archiving

L'archiviazione continua del WAL è il fondamento del disaster recovery in PostgreSQL. Permette di conservare ogni modifica al database e quindi di recoverire a qualsiasi punto nel tempo.

Per abilitare l'archiviazione WAL, configurare postgresql.conf:

```sql
-- Livello WAL: minimal (default), replica, o logical
wal_level = replica

-- Abilita archiviazione
archive_mode = on

-- Comando di archiviazione (%p = percorso file, %f = nome file)
archive_command = 'cp %p /archive/wal/%f'

-- Timeout massimo prima di forzare archiviazione (default: 5 min)
archive_timeout = 300
```

Dopo le modifiche, riavviare PostgreSQL (o eseguire reload per le modifiche compatibili).

Il parametro wal_level deve essere almeno 'replica' per abilitare l'archiviazione. Questo aumenta leggermente la dimensione del WAL ma è necessario per point-in-time recovery.

### 4.2 Archive Command Patterns

Il comando di archiviazione può variare significativamente basandosi sull'infrastruttura:

**Archiviazione locale**:
```sql
archive_command = 'cp %p /mnt/backup/wal/%f'
```

**Archiviazione remota via SSH**:
```sql
archive_command = 'scp -o StrictHostKeyChecking=no %p user@backup-server:/mnt/wal/%f'
```

**Archiviazione su S3**:
```sql
-- Usando aws CLI
archive_command = 'aws s3 cp %p s3://mybucket/wal/%f'

-- Usando s5cmd (più veloce)
archive_command = 's5cmd cp %p s3://mybucket/wal/%f'
```

**Archiviazione su Azure Blob**:
```sql
archive_command = 'az storage blob upload --file %p --container-name wal --name %f'
```

**Archiviazione su Google Cloud Storage**:
```sql
archive_command = 'gsutil cp %p gs://mybucket/wal/%f'
```

### 4.3 Archive Validation

Validare il comando di archiviazione è cruciale:

```bash
# Testare il comando con un file fittizio
echo "test" > /tmp/test_wal
cp /tmp/test_wal /archive/wal/test_file
ls -la /archive/wal/test_file
rm /tmp/test_wal /archive/wal/test_file
```

Monitorare gli errori di archiviazione:

```sql
-- Verifica configurazione
SHOW archive_mode;
SHOW archive_command;

-- PostgreSQL scrive errori nel log
-- grep "archive" postgresql.conf
```

### 4.4 Archive Timeout

Il parametro **archive_timeout** controlla quanto spesso PostgreSQL forza l'archiviazione del WAL:

```sql
-- Forza archiviazione ogni 5 minuti
archive_timeout = 300

-- Per RPO più basso (1 minuto)
archive_timeout = 60
```

Un timeout più basso significa RPO più basso (meno dati persi in caso di disaster) ma più file WAL da gestire.

### 4.5 Monitoring Archiving

```sql
-- Statistiche di archiviazione
SELECT * FROM pg_stat_archiver;

-- View: stato dell'archiver
SELECT 
    archiver_name,
    archiver_state,
    pg_size_pretty(pg_wal_lsn_diff(archived_lsn, inserted_lsn)) AS pending_wal,
    last_archived_wal,
    last_archived_time
FROM pg_stat_archiver;
```

### 4.6 Troubleshooting

Problemi comuni e soluzioni:

**Comando archiviazione fallisce**:
- Verificare permessi sulla directory di destinazione
- Testare il comando manualmente
- Verificare spazio disco disponibile

**WAL non archiviato**:
- Controllare pg_stat_archiver
- Verificare che archive_mode sia on
- Verificare wal_level >= replica

**Performance**:
- Considerare archiviazione asincrona
- Usare storage locale veloce per temporaneo
- Implementare batch di upload per cloud storage

---

## 5. Point-in-Time Recovery

### 5.1 Configuring PITR

Il Point-in-Time Recovery (PITR) permette di recoverire il database a un momento specifico nel tempo, non solo al momento dell'ultimo backup. Questo è essenziale per scenari come recovery da accidental deletion o corruption.

PostgreSQL 13+ usa postgresql.conf per configurare la recovery (le versioni precedenti usavano recovery.conf):

```sql
-- recovery.conf (PostgreSQL 12 e inferiori)
-- postgresql.conf (PostgreSQL 13+)

-- Comando per recuperare i WAL archiviati
restore_command = 'cp /archive/wal/%f %p'

-- Target di recovery (scegliere uno)
recovery_target_time = '2026-05-04 10:30:00'
-- recovery_target_xid = '12345'
-- recovery_target_lsn = '0/12345678'
-- recovery_target_name = 'before_migration'

-- Azione dopo il recovery
recovery_target_action = 'promote'  -- diventa primary
-- recovery_target_action = 'shutdown'  -- ferma il server
-- recovery_target_action = 'pause'  -- ferma in stato di recovery

-- Opzioni aggiuntive
recovery_target_inclusive = true  -- include il target (default)
pause_at_recovery_target = true  -- pausa al raggiungimento del target
```

### 5.2 Recovery Process

Il processo di recovery completo:

**Fase 1: Preparazione**
```bash
# 1. Stop PostgreSQL
systemctl stop postgresql

# 2. Verificare che sia fermo
pg_ctl status -D /var/lib/postgresql/data
```

**Fase 2: Ripristino backup base**
```bash
# 3. Backup dei file attuali (opzionale ma consigliato)
cp -r /var/lib/postgresql/data /var/lib/postgresql/data.old

# 4. Rimuovere o pulire la data directory
rm -rf /var/lib/postgresql/data/*

# 5. Ripristinare il backup base
pg_restore -D /var/lib/postgresql/data backup_dir/
# o
tar -xf backup.tar -C /var/lib/postgresql/data
```

**Fase 3: Configurare recovery**
```bash
# 6. Creare o modificare postgresql.conf per recovery
# (vedi sezione 5.1)

# 7. PostgreSQL 12 e inferiori: creare recovery.conf
cat > /var/lib/postgresql/data/recovery.conf << EOF
restore_command = 'cp /archive/wal/%f %p'
recovery_target_time = '2026-05-04 10:30:00'
recovery_target_action = 'promote'
EOF
```

**Fase 4: Avviare recovery**
```bash
# 8. Avviare PostgreSQL
systemctl start postgresql

# 9. Verificare i log
tail -f /var/log/postgresql/postgresql.log
```

### 5.3 Recovery Target Types

PostgreSQL supporta diversi tipi di target:

**recovery_target_time**: Recovery a un timestamp specifico. Più usato per recovery da errori.

```sql
recovery_target_time = '2026-05-04 10:30:00'
```

**recovery_target_xid**: Recovery a un transaction ID specifico. Utile se si conosce l'XID problematico.

```sql
recovery_target_xid = '12345'
```

**recovery_target_lsn**: Recovery a una specifica WAL location (Log Sequence Number). Più preciso.

```sql
recovery_target_lsn = '0/7000060'
```

**recovery_target_name**: Recovery a un named restore point. Permette di marcare momenti specifici.

```sql
-- Creare un restore point
SELECT pg_create_restore_point('before_major_change');

-- Recovery a quel punto
recovery_target_name = 'before_major_change'
```

### 5.4 Recovery inclusivo vs esclusivo

Il parametro **recovery_target_inclusive** controlla se il target è incluso o escluso:

```sql
-- true (default): recovery include transazioni fino al target
recovery_target_inclusive = true

-- false: recovery esclude transazioni al target
recovery_target_inclusive = false
```

### 5.5 Continuous Recovery

Per applicare continuamente nuovi WAL:

```sql
-- Non specificare target - PostgreSQL leggerà tutti i WAL disponibili
restore_command = 'cp /archive/wal/%f %p'
recovery_target_action = 'promote'
```

Il database rimarrà in recovery mode, applicando WAL man mano che arrivano. Questo è utile per warm standby.

---

## 6. Backup Verification

### 6.1 Test Restore

Un backup non verificato è come non avere backup. Testare regolarmente il restore è essenziale:

**Test restore locale**:
```bash
# Creare un database di test
createdb test_restore

# Restore del backup
pg_restore -d test_restore backup.dump

# Verificare che il database funzioni
psql -d test_restore -c "SELECT count(*) FROM users"
psql -d test_restore -c "\dt"  -- lista tabelle

# Verificare dati specifici
psql -d test_restore -c "SELECT * FROM orders WHERE created_at > '2026-01-01' LIMIT 10"
```

**Test con PostgreSQL temporaneo**:
```bash
# Avviare un'istanza temporanea su porta diversa
pg_ctl -D /tmp/test_pgdata start -o "-p 5433"

# Restore sulla porta 5433
pg_restore -p 5433 -d test_db backup.dump

# Testare query
psql -p 5433 -d test_db -c "SELECT version();"

# Fermare l'istanza temporanea
pg_ctl -D /tmp/test_pgdata stop
```

### 6.2 Integrity Verification

Verificare l'integrità del backup:

```sql
-- Verificare la struttura
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Verificare i constraint
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public';

-- Verificare gli indici
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE schemaname = 'public';

-- Verificare le sequenze
SELECT 
    sequence_name, 
    start_value, 
    last_value, 
    increment_by 
FROM information_schema.sequences;
```

### 6.3 Data Integrity Checks

Verificare la consistenza dei dati:

```sql
-- Contare righe in ogni tabella
SELECT 
    schemaname, 
    relname, 
    n_live_tup 
FROM pg_stat_user_tables 
ORDER BY n_live_tup DESC;

-- Verificare valori NULL
SELECT 
    'users' as table_name, 
    count(*) as total,
    count(*) - count(email) as null_emails
FROM users;

-- Verificare foreign key
SELECT 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

### 6.4 Automated Verification Script

Creare uno script di verifica automatizzato:

```bash
#!/bin/bash
# verify_backup.sh

set -e

BACKUP_FILE=$1
TEST_DB="test_restore_$$"

echo "Creazione database di test: $TEST_DB"
createdb $TEST_DB

echo "Restore del backup..."
pg_restore -d $TEST_DB $BACKUP_FILE > /dev/null 2>&1

echo "Verifica tabelle..."
TABLE_COUNT=$(psql -d $TEST_DB -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
echo "Tabelle trovate: $TABLE_COUNT"

echo "Verifica righe..."
psql -d $TEST_DB -c "SELECT schemaname, relname, n_lup AS rows FROM pg_stat_user_tables;"

echo "Pulizia database di test..."
dropdb $TEST_DB

echo "Verifica completata con successo!"
```

### 6.5 Verification Frequency

Frequenza delle verifiche:

- **Dopo ogni backup completo**: Verificare che il backup sia stato creato correttamente
- **Settimanale**: Restore completo su ambiente di test
- **Mensile**: Verifica di restore con benchmark temporale
- **Dopo modifiche sostanziali**: Testare restore dopo major upgrade o migrazione

---

## 7. Disaster Recovery Planning

### 7.1 DR Strategy Fundamentals

Un piano di disaster recovery efficace deve rispondere a domande fondamentali:

**RPO (Recovery Point Objective)**: Quanti dati possiamo permetterci di perdere? Questo determina la frequenza dei backup e l'intervallo di archiviazione WAL.

**RTO (Recovery Time Objective)**: Quanto tempo possiamo stare senza il database? Questo determina la strategia di backup e la complessità della recovery.

**Budget**: Quanto possiamo spendere per il disaster recovery? Questo bilancia tra soluzioni manuali economicali e soluzioni automatizzate costose.

### 7.2 RPO vs RTO Trade-offs

I due obiettivi sono spesso in conflitto:

**Basso RPO (minima perdita dati)**:
- Backup frequenti (ogni ora o più)
- Archiviazione WAL continua
- Replica sincrona
- Costo: storage extra, complexity, potenziale latency

**Basso RTO (recovery veloce)**:
- Backup fisici (pg_basebackup) per restore veloce
- Backup incrementali
- Procedure di recovery automatizzate
- Environment di recovery pre-configurato
- Costo: risorse per standby, automazione

### 7.3 DR Location Strategy

La geografia della soluzione di recovery determina la protezione:

**On-site**: Recovery nel mismo data center. Vantaggi: recovery veloce, basso costo. Svantaggi: non protegge da disaster che colpiscono tutto il data center.

**Off-site**: Recovery in location geograficamente separata. Protezione da disaster locali. Richiede trasferimento dati (replica asincrona o backup off-site).

**Cloud**: Recovery su cloud provider. Massima flessibilità, pay-as-you-go. Richiede competenze cloud e configurazione di networking.

**Multi-region**: Per cloud provider, distribuzione su multiple regioni. Massima protezione, ma complessità di configurazione.

### 7.4 DR Documentation

La documentazione è cruciale per un recovery efficace:

**Recovery Runbook**: Passo-passo per ogni scenario di failure:
- Recovery da backup
- Recovery PITR
- Recovery da replica
- Failover a standby

**Contact List**: Chi contattare in caso di disaster:
- Team database
- Management
- Fornitori di infrastruttura
- Supporto PostgreSQL (se Enterprise)

**Network Diagrams**: Topologia della recovery, come connettersi al sistema di recovery.

**Testing Schedule**: Quando e come testare il DR.

### 7.5 DR Testing

Testare regolarmente il piano di disaster recovery:

**Test trimestrali**:
1. Simulare un failure completo
2. Eseguire la procedura di recovery
3. Verificare che i dati siano consistenti
4. Documentare il tempo effettivo

**Test dopo cambiamenti**:
- Dopo major upgrade
- Dopo cambiamenti di infrastruttura
- Dopo cambiamenti nelle procedure

### 7.6 DR Automation

Automatizzare il recovery per ridurre RTO:

```bash
#!/bin/bash
# disaster_recovery.sh

# Parametri
PRIMARY_HOST="prod-db.example.com"
STANDBY_HOST="dr-db.example.com"
BACKUP_DIR="/backup"

# 1. Identificare il problema
echo "Checking primary: $PRIMARY_HOST"
ssh $PRIMARY_HOST "pg_isready" || PRIMARY_DOWN=true

# 2. Se primary down, failover
if [ "$PRIMARY_DOWN" ]; then
    echo "Primary down, initiating failover..."
    
    # 3. Promuovere standby
    ssh $STANDBY_HOST "pg_ctl promote -D /var/lib/postgresql/data"
    
    # 4. Aggiornare DNS o connection string
    # (implementare logica specifica)
    
    # 5. Verificare
    ssh $STANDBY_HOST "pg_isready"
    
    echo "Failover completato"
fi
```

---

## 8. RTO/RPO Considerations

### 8.1 RPO Calculation

Il **Recovery Point Objective (RPO)** è la massima quantità di dati che un'organizzazione può permettersi di perdere. Per calcolare il RPO:

**Backup base**: Se eseguiamo backup completo ogni notte alle 2AM, il RPO massimo è di 24 ore (dalle 2AM del giorno prima a现在). Ma con WAL archiviati ogni 5 minuti, il RPO è al massimo 5 minuti.

**WAL Archiving**: L'intervallo di archive_timeout determina il RPO:
- archive_timeout = 300 (5 min) → RPO max 5 min
- archive_timeout = 3600 (1 ora) → RPO max 1 ora

**Replica**: Con replica sincrona, RPO teoricamente 0 (nessuna perdita dati). Con replica asincrona, dipende dal lag.

**Calcolo pratico**:
```
RPO = max(backup_interval, archive_timeout, replication_lag)
```

Per un'organizzazione con backup giornaliero (24h) e WAL ogni 5 minuti:
```
RPO = max(24h, 5min, 0) = 24h
```
Ma se i WAL sono archiviati, e il backup base è utilizzabile con i WAL, il RPO effettivo è 5 minuti.

### 8.2 RTO Calculation

Il **Recovery Time Objective (RTO)** è il tempo massimo per ripristinare il servizio. Per calcolare il RTO:

**Tempo di backup**: Con pg_basebackup, un backup di 500GB su una connessione 1Gbps richiede circa 67 minuti (500GB * 8 / 1Gbps = 4000 secondi).

**Tempo di restore**: Il restore di un backup compresso è più lento del backup. Stimare 2x il tempo di backup.

**Tempo di PITR**: Applicare i WAL dal backup al punto di recovery. Con 5 minuti di WAL ogni 5 minuti, e 6 ore di WAL da applicare → ~45 minuti.

**Tempo di verifica**: 15-30 minuti per verificare che il recovery sia corretto.

**Calcolo pratico**:
```
RTO = backup_time + restore_time + PITR_time + verify_time
RTO = 67min + 134min + 45min + 30min = ~4.5 ore
```

Per ridurre RTO:
- Backup più piccoli (partitioning, cleanup)
- Connection più veloce
- Standby pre-configurato
- Procedure automatizzate

### 8.3 Matrix RPO/RTO

| RPO | RTO | Strategy |
|-----|-----|----------|
| Ore | Giorni | Backup notturno |
| Ore | Ore | Backup giornaliero + WAL |
| Minuti | Ore | Backup frequente + WAL archiviato |
| Minuti | Minuti | Replica asincrona + backup |
| Zero | Minuti | Replica sincrona |

### 8.4 Cost vs Benefit Analysis

Ogni riduzione di RPO/RTO ha un costo:

**Aumentare frequenza backup**:
- Costo: storage, tempo CPU, complessità
- Beneficio: minore RPO

**Migliorare velocità recovery**:
- Costo: hardware standby, configurazione
- Beneficio: minore RTO

**Replicas**:
- Costo: hardware, network, complessità
- Beneficio: RPO e RTO minimi

**Cloud DR**:
- Costo: subscription cloud
- Beneficio: flessibilità, scalabilità

### 8.5 Sizing della Soluzione DR

Per dimensionare la soluzione DR:

**Storage**:
- Retention WAL: 7 giorni = 7 * 24 * 60 / archive_timeout * WAL_size
- Retention backup: 30 giorni di backup base

**Network**:
- Banda per replica: write_rate * replication_factor
- Banda per backup: backup_size / backup_window

**Compute**:
- CPU per recovery: proporzionale a backup_size
- I/O per restore: deve essere veloce abbastanza per RTO

### 8.6 Monitoring RPO/RTO

Monitorare continuamente gli obiettivi:

```sql
-- Monitorare lag di replica (RPO effettivo)
SELECT 
    client_addr, 
    pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lag) as lag_bytes,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lag)) as lag
FROM pg_stat_replication;

-- Monitorare WAL non archiviato
SELECT 
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), archived_lsn)) as pending_wal,
    last_archived_wal,
    last_archived_time
FROM pg_stat_archiver;
```

---

## 9. Backup Automation

### 9.1 Cron Jobs

L'automazione dei backup con cron è semplice ma efficace:

```cron
# Backup giornaliero a mezzanotte
0 0 * * * pg_dump -U postgres -Fc mydb > /backup/daily_$(date +\%Y\%m\%d).dump

# Backup settimanale domenica notte
0 2 * * 0 pg_dump -U postgres -Fc -f /backup/weekly_$(date +\%Y\%m\%d).dump mydb

# Backup mensile il primo del mese
0 3 1 * * pg_dump -U postgres -Fc -f /backup/monthly_$(date +\%Y\%m).dump mydb
```

Per pg_basebackup (backup fisico):

```cron
# Backup base giornaliero alle 2AM
0 2 * * * pg_basebackup -h localhost -D /backup/base_$(date +\%Y\%m\%d) -U replicator -Xs -P
```

### 9.2 Retention Policy

La retention policy determina quanto a lungo conservare i backup:

```bash
#!/bin/bash
# backup_retention.sh

BACKUP_DIR="/backup"
DAILY_RETENTION=7    # 7 giorni
WEEKLY_RETENTION=4  # 4 settimane
MONTHLY_RETENTION=6 # 6 mesi

# Rimuovere backup giornalieri più vecchi di 7 giorni
find $BACKUP_DIR/daily* -type f -mtime +$DAILY_RETENTION -delete

# Rimuovere backup settimanali più vecchi di 4 settimane
find $BACKUP_DIR/weekly* -type f -mtime +$(($WEEKLY_RETENTION * 7)) -delete

# Rimuovere backup mensili più vecchi di 6 mesi
find $BACKUP_DIR/monthly* -type f -mtime +$(($MONTHLY_RETENTION * 30)) -delete

# Rimuovere WAL archiviati più vecchi di 7 giorni
find $BACKUP_DIR/wal/* -type f -mtime +$DAILY_RETENTION -delete
```

### 9.3 Monitoring

Monitorare i backup è essenziale:

```bash
#!/bin/bash
# check_backup.sh

# Verificare backup recente
LAST_BACKUP=$(find /backup -name "daily_*.dump" -mtime -1 | head -1)

if [ -z "$LAST_BACKUP" ]; then
    echo "ALERT: Nessun backup nelle ultime 24 ore!"
    # Inviare alert (email, Slack, etc.)
fi

# Verificare dimensione backup
BACKUP_SIZE=$(stat -f%z "$LAST_BACKUP" 2>/dev/null || stat -c%s "$LAST_BACKUP")
if [ $BACKUP_SIZE -lt 1000000 ]; then
    echo "ALERT: Backup troppo piccolo: $BACKUP_SIZE bytes"
fi
```

Integrare con monitoring:

```bash
# Prometheus exporter per backup
#!/bin/bash
echo "# HELP pg_backup_last_success Unix timestamp of last successful backup"
echo "# TYPE pg_backup_last_success gauge"
LAST_SUCCESS=$(find /backup -name "daily_*.dump" -mmin -1440 -printf '%T+\n' 2>/dev/null | sort | tail -1 | head -c 10)
if [ -n "$LAST_SUCCESS" ]; then
    echo "pg_backup_last_success $(date -d "$LAST_SUCCESS" +%s)"
fi
```

### 9.4 Backup Scripts Best Practices

Best practices per script di backup:

```bash
#!/bin/bash
# backup.sh - Esempio completo

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Configurazione
DB_NAME="mydb"
DB_USER="postgres"
BACKUP_DIR="/backup"
RETENTION_DAYS=7

# Log
LOGFILE="/var/log/backup.log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a $LOGFILE
}

# Error handling
error_exit() {
    log "ERROR: $1"
    # Inviare notifica
    exit 1
}

# Verificare database disponibile
pg_isready -U $DB_USER || error_exit "Database non disponibile"

# Backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/daily_${DB_NAME}_${TIMESTAMP}.dump"

log "Iniziando backup di $DB_NAME"

if pg_dump -U $DB_USER -Fc "$DB_NAME" -f "$BACKUP_FILE"; then
    log "Backup completato: $BACKUP_FILE"
    
    # Compressione (se non usando -Fc che già comprime)
    # gzip "$BACKUP_FILE"
    
    # Verifica dimensione
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Dimensione backup: $SIZE"
else
    error_exit "Backup fallito"
fi

# Cleanup vecchi backup
find $BACKUP_DIR -name "daily_${DB_NAME}_*.dump" -mtime +$RETENTION_DAYS -delete

log "Backup e cleanup completati"
```

### 9.5 Integration con strumenti di orchestrazione

Per ambienti complessi, considerare:

**Ansible**: Per automazione di configurazione e deployment dei backup
```yaml
- name: PostgreSQL backup
  postgresql_sql:
    db: mydb
    query: "SELECT pg_start_backup('full');"
```

**Kubernetes**: Per backup in ambiente containerizzato
- CronJobs per backup scheduling
- PersistentVolume per storage

**Terraform**: Per infrastuttura DR
- Provisioning di standby
- Configurazione di replica

---

## 10. Restore Procedures

### 10.1 Restore from pg_dump

Il restore da pg_dump dipende dal formato utilizzato:

**Restore da formato plain (SQL)**:
```bash
# Restore completo
psql -U postgres -d mydb < backup.sql

# Restore su database diverso
psql -U postgres -d newdb < backup.sql

# Restore con verbose per debugging
psql -U postgres -d mydb -f backup.sql 2>&1 | tee restore.log
```

**Restore da formato custom (-Fc)**:
```bash
# Restore completo
pg_restore -U postgres -d mydb backup.dump

# Restore su database nuovo
createdb newdb
pg_restore -U postgres -d newdb backup.dump

# Restore di solo schema (no data)
pg_restore -U postgres -d mydb --schema-only backup.dump

# Restore di solo data (no schema)
pg_restore -U postgres -d mydb --data-only backup.dump

# Restore di specifiche tabelle
pg_restore -U postgres -d mydb -t users -t orders backup.dump
```

**Restore parallelo (formato directory)**:
```bash
# Restore con 4 job
pg_restore -d mydb -j 4 backup_dir/
```

### 10.2 Restore from pg_basebackup

Il restore da backup fisico richiede più attenzione:

**Preparazione**:
```bash
# 1. Fermare PostgreSQL
systemctl stop postgresql
# o
pg_ctl stop -D $PGDATA -m fast

# 2. Backup dei file attuali (consigliato)
cp -r $PGDATA $PGDATA.backup.$(date +%Y%m%d)

# 3. Rimuovere contenuto corrente
rm -rf $PGDATA/*
```

**Restore da tar**:
```bash
# 4. Estrarre il backup
tar -xf backup.tar -C $PGDATA

# 5. Assicurarsi che i permessi siano corretti
chown -R postgres:postgres $PGDATA
chmod 700 $PGDATA

# 6. Avviare PostgreSQL
systemctl start postgresql
```

**Restore da directory**:
```bash
# 4. Copiare i file
cp -r backup_dir/* $PGDATA/

# 5. Permessi
chown -R postgres:postgres $PGDATA

# 6. Avviare
systemctl start postgresql
```

### 10.3 Point-in-Time Restore Procedure

Il PITR richiede configurazione specifica:

**Setup recovery**:
```bash
# PostgreSQL 13+: usare postgresql.conf
cat >> $PGDATA/postgresql.conf << EOF

# Recovery settings
restore_command = 'cp /archive/wal/%f %p'
recovery_target_time = '2026-05-04 10:30:00'
recovery_target_action = 'promote'
EOF

# PostgreSQL 12 e inferiori: creare recovery.conf
cat > $PGDATA/recovery.conf << EOF
restore_command = 'cp /archive/wal/%f %p'
recovery_target_time = '2026-05-04 10:30:00'
recovery_target_action = 'promote'
EOF
chown postgres:postgres $PGDATA/recovery.conf
chmod 600 $PGDATA/recovery.conf
```

**Esecuzione**:
```bash
# Avviare PostgreSQL - inizierà automaticamente il recovery
systemctl start postgresql

# Monitorare il recovery
tail -f $PGDATA/log/postgresql.log
```

**Verifica**:
```bash
# Verificare che il database sia up
pg_isready

# Verificare i dati al punto di recovery
psql -c "SELECT now();"
psql -c "SELECT max(created_at) FROM orders;"
```

### 10.4 Post-Restore Steps

Dopo ogni restore, eseguire questi passi di verifica:

**Ricostruire statistiche**:
```sql
-- ANALYZE su tutto il database
ANALYZE;

-- Per database grandi, ANALYZE su singole tabelle
ANALYZE users;
ANALYZE orders;
ANALYZE order_items;
```

**Verificare indici**:
```sql
-- Verificare che tutti gli indici siano validi
SELECT 
    schemaname, 
    tablename, 
    indexname, 
    idx_scan, 
    idx_tup_read, 
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Verificare indici corrotti (usare REINDEX se necessario)
-- Notare: REINDEX può essere耗时
```

**Verificare sequence**:
```sql
-- Le sequence potrebbero non essere state ripristinate correttamente
-- Verificare e correggere
SELECT 
    sequence_name, 
    last_value 
FROM information_schema.sequences;

-- Se necessario, aggiornare
SELECT setval('users_id_seq', (SELECT max(id) FROM users));
```

**Verificare constraint**:
```sql
-- Verificare foreign key
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type,
    status
FROM information_schema.table_constraints tc
WHERE tc.constraint_type = 'FOREIGN KEY';

-- Verificare CHECK constraints
SELECT * FROM pg_catalog.pg_constraint WHERE contype = 'c';
```

**Ricostruire extensioni**:
```sql
-- Se il database usa estensioni, verificare
SELECT * FROM pg_extension;

-- Installare se mancanti
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 10.5 Troubleshooting Restore

Problemi comuni e soluzioni:

**Restore fallisce con errori di permesso**:
```bash
# Correggere permessi
chown -R postgres:postgres $PGDATA
chmod 700 $PGDATA
```

**Database già esistente**:
```bash
# Drop del database prima del restore
dropdb mydb
pg_restore -C -d postgres backup.dump  # -C crea il database
```

**Tablespace mancanti**:
```sql
-- Creare tablespace se necessario
CREATE TABLESPACE newts LOCATION '/path/to/newts';
```

**Duplicate data**:
```bash
# Usare --clean per droppare gli oggetti prima di ricreare
pg_restore --clean -d mydb backup.dump
# Attenzione: questo può causare problemi con foreign key
```

**Lock timeout**:
```bash
# Aumentare lock timeout
pg_restore --lock-wait-timeout=60s -d mydb backup.dump
```

### 10.6 Complete Recovery Checklist

Checklist per recovery completo:

- [ ] Verificare che il backup sia integro
- [ ] Preparare la data directory
- [ ] Ripristinare il backup base
- [ ] Configurare recovery (se PITR)
- [ ] Avviare PostgreSQL
- [ ] Verificare startup nei log
- [ ] Eseguire ANALYZE
- [ ] Verificare dati critici
- [ ] Testare query comuni
- [ ] Aggiornare connection string
- [ ] Notificare stakeholders
- [ ] Documentare il tempo di recovery

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*