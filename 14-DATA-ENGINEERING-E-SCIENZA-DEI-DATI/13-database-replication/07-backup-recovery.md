# Backup e Recovery nella Replica

Il backup è distinto dalla replica: la replica protegge dalla failure del nodo, ma non dalla corruzione logica dei dati (es. un DROP TABLE accidentale si propaga immediatamente a tutte le repliche). Un sistema di alta disponibilità senza backup è incompleto. Questa sezione copre i metodi di backup per PostgreSQL e MySQL, il recupero point-in-time (PITR), e l'integrazione con la replica.

## Tipi di Backup

### Backup Fisico vs Logico

| Caratteristica | Fisico | Logico |
|----------------|--------|--------|
| Cosa copia | File del filesystem (pagine dati) | Dati strutturati (SQL, CSV) |
| Velocità backup | Molto veloce (I/O sequenziale) | Lento (query per ogni tabella) |
| Velocità restore | Molto veloce | Lento (replay SQL) |
| Portabilità | Solo stessa versione/architettura | Cross-versione, cross-piattaforma |
| Granularità | Intero cluster (tipicamente) | Database/tabella/riga |
| PITR | Sì (con WAL archiving) | No (snapshot point-in-time) |
| Corruzione parziale | Difficile rilevare | Detectabile con checksum |

### Backup Fisico PostgreSQL: pg_basebackup

```bash
# Backup base con pg_basebackup
# Crea una copia consistente del cluster PostgreSQL
pg_basebackup \
  --host=localhost \
  --port=5432 \
  --username=replicator \
  --pgdata=/backup/base/$(date +%Y%m%d) \
  --format=tar \           # tar compresso vs plain (directory)
  --compress=9 \           # compressione gzip livello 9
  --wal-method=stream \    # streamma i WAL durante il backup (evita gap)
  --checkpoint=fast \      # forza checkpoint immediato
  --label="backup-$(date +%Y%m%dT%H%M%S)" \
  --progress \
  --verbose

# Alternativa: formato plain (directory) per backup locale
pg_basebackup \
  --host=localhost \
  --pgdata=/backup/base/$(date +%Y%m%d) \
  --format=plain \
  --wal-method=stream \
  --checkpoint=fast \
  --tablespace-map=/old/ts/path=/new/ts/path  # remap tablespace se necessario

# Verifica dimensione del backup
du -sh /backup/base/$(date +%Y%m%d)

# Struttura risultante (formato tar)
ls /backup/base/20250101/
# base.tar.gz  pg_wal.tar.gz
```

### WAL Archiving per PITR

Il PITR (Point-In-Time Recovery) richiede il backup base più tutti i WAL successivi. Ogni WAL file è 16MB e copre una porzione di modifiche al database. Con il WAL archiving attivo, è possibile recuperare il database a qualsiasi punto nel tempo tra il backup base e l'ultimo WAL archiviato.

```ini
# postgresql.conf
wal_level = replica          # almeno replica per archiving
archive_mode = on
archive_command = 'test ! -f /wal-archive/%f && cp %p /wal-archive/%f'
# Il comando deve restituire 0 solo se il file è stato archiviato con successo
# 'test ! -f' previene la sovrascrittura di file esistenti

# Per archiviare su S3 (AWS CLI o rclone)
archive_command = 'aws s3 cp %p s3://my-wal-bucket/wal/%f --storage-class STANDARD_IA'

# Con pgBackRest (metodo raccomandato per produzione)
archive_command = 'pgbackrest --stanza=main archive-push %p'

restore_command = 'aws s3 cp s3://my-wal-bucket/wal/%f %p'
# Il restore_command è usato durante il recovery per recuperare i WAL
```

```bash
# Script di backup completo con WAL archiving
#!/bin/bash
# backup-postgres.sh

BACKUP_DIR="/backup"
S3_BUCKET="s3://my-postgres-backups"
STANZA="main"
DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%Y%m%dT%H%M%S)

# 1. Backup base
echo "[${TIMESTAMP}] Avvio backup base..."
pg_basebackup \
  --pgdata="${BACKUP_DIR}/base/${DATE}" \
  --format=tar \
  --wal-method=stream \
  --checkpoint=fast \
  --compress=9 \
  --label="base-backup-${TIMESTAMP}"

# 2. Caricare su S3
echo "[${TIMESTAMP}] Upload su S3..."
aws s3 sync "${BACKUP_DIR}/base/${DATE}" "${S3_BUCKET}/base/${DATE}/" \
  --storage-class STANDARD_IA \
  --delete

# 3. Registrare il backup nel catalogo
psql -c "SELECT pg_backup_stop();" 2>/dev/null || true

# 4. Pulizia backup locali più vecchi di 7 giorni
find "${BACKUP_DIR}/base" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +

echo "[${TIMESTAMP}] Backup completato: ${BACKUP_DIR}/base/${DATE}"
```

### pgBackRest: Backup Professionale per PostgreSQL

pgBackRest è lo strumento di backup più avanzato per PostgreSQL. Supporta backup incrementali/differenziali, compressione, encryption, e integrazione nativa con S3/Azure/GCS.

```ini
# /etc/pgbackrest/pgbackrest.conf

[global]
repo1-path=/var/lib/pgbackrest
repo1-retention-full=4          # mantenere 4 backup completi
repo1-retention-full-type=count
repo1-cipher-type=aes-256-cbc   # encryption
repo1-cipher-pass=supersecretpassphrase

# Configurazione S3
repo2-type=s3
repo2-path=/pgbackrest
repo2-s3-bucket=my-postgres-backups
repo2-s3-endpoint=s3.amazonaws.com
repo2-s3-region=eu-west-1
repo2-s3-key=AKIAIOSFODNN7EXAMPLE
repo2-s3-key-secret=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
repo2-retention-full=2

[global:archive-push]
compress-level=3               # bilanciamento velocità/compressione per WAL
process-max=2                  # thread paralleli per archiving

[main]
pg1-path=/var/lib/postgresql/data
pg1-port=5432
pg1-user=postgres
```

```bash
# Inizializzare lo stanza
pgbackrest --stanza=main stanza-create

# Backup completo
pgbackrest --stanza=main --type=full backup

# Backup incrementale (dopo un backup completo o differenziale)
pgbackrest --stanza=main --type=incr backup

# Backup differenziale
pgbackrest --stanza=main --type=diff backup

# Informazioni sui backup disponibili
pgbackrest --stanza=main info

# Output esempio:
# stanza: main
#     status: ok
#     cipher: aes-256-cbc
#
#     db (current)
#         wal archive min/max (15): 000000010000000000000001/00000001000000000000002A
#
#         full backup: 20250101-020000F
#             timestamp start/stop: 2025-01-01 02:00:00+00 / 2025-01-01 02:15:23+00
#             wal start/stop: 000000010000000000000005 / 000000010000000000000007
#             database size: 45.2GB, database backup size: 45.2GB
#
#         incr backup: 20250101-020000F_20250102-030000I
#             timestamp start/stop: 2025-01-02 03:00:00+00 / 2025-01-02 03:02:45+00
#             database backup size: 512.3MB, backup size: 512.3MB
```

## PITR: Point-In-Time Recovery

### Procedure PITR PostgreSQL

```bash
# Scenario: ripristinare il database a 2025-01-02 14:30:00 UTC
# (dopo aver scoperto che un DROP TABLE è avvenuto alle 14:35:00)

# 1. Fermare PostgreSQL corrente
systemctl stop postgresql

# 2. Backup dei dati correnti (per sicurezza)
mv /var/lib/postgresql/data /var/lib/postgresql/data.corrupted

# 3. Restore del backup base con pgBackRest
pgbackrest --stanza=main \
  --delta \                                         # confronta file per file (più veloce di un restore completo)
  --type=time \
  --target="2025-01-02 14:30:00+00" \              # punto di recupero
  --target-action=promote \                         # promuovere dopo aver raggiunto il target
  --recovery-option=recovery_target_inclusive=true \
  restore

# 4. Avviare PostgreSQL (entrerà in recovery mode)
systemctl start postgresql

# 5. Monitorare il recovery
tail -f /var/log/postgresql/postgresql.log
# LOG:  starting point-in-time recovery to 2025-01-02 14:30:00+00
# LOG:  restored log file "000000010000000000000010" from archive
# LOG:  redo starts at 0/10000028
# LOG:  consistent recovery state reached at 0/10000100
# LOG:  recovery stopping before commit of transaction ...
# LOG:  pausing at the end of recovery

# 6. Verificare che i dati siano corretti prima di promuovere
psql -c "SELECT COUNT(*) FROM tabella_importante;"

# 7. Se i dati sono corretti, completare il recovery
psql -c "SELECT pg_wal_replay_resume();"
# Oppure: touch /var/lib/postgresql/data/recovery.signal (file sentinella)
```

```bash
# PITR manuale (senza pgBackRest)

# 1. Restore dal backup base
tar -xzf /backup/base/20250101/base.tar.gz -C /var/lib/postgresql/data/
tar -xzf /backup/base/20250101/pg_wal.tar.gz -C /var/lib/postgresql/data/pg_wal/

# 2. Creare il file di configurazione recovery
# In PostgreSQL 12+: creare recovery.signal e configurare in postgresql.conf
touch /var/lib/postgresql/data/recovery.signal

cat >> /var/lib/postgresql/data/postgresql.conf << 'EOF'
restore_command = 'aws s3 cp s3://my-wal-bucket/wal/%f %p'
recovery_target_time = '2025-01-02 14:30:00+00'
recovery_target_action = 'promote'
recovery_target_timeline = 'latest'
EOF

# 3. Impostare i permessi corretti
chown -R postgres:postgres /var/lib/postgresql/data/

# 4. Avviare
systemctl start postgresql
```

### PITR MySQL con Binlog

```bash
# Scenario: ripristinare MySQL a prima di un DELETE accidentale
# avvenuto alle 2025-01-02 15:45:00 UTC

# 1. Restore dal backup completo più recente (precedente all'evento)
# Con mysqldump
mysql -u root -p < /backup/full-20250101.sql

# Con xtrabackup (più veloce per database grandi)
xtrabackup --prepare --target-dir=/backup/full-20250101/
xtrabackup --copy-back --target-dir=/backup/full-20250101/ --datadir=/var/lib/mysql/

# 2. Applicare i binlog fino al momento prima dell'evento
# Identificare il binlog corretto
ls -la /var/lib/mysql/mysql-bin.*
# mysql-bin.000041  mysql-bin.000042  mysql-bin.000043

# Ispezionare i binlog per trovare l'evento da evitare
mysqlbinlog /var/lib/mysql/mysql-bin.000043 | grep -A5 "2025-01-02 15:4"

# Applicare i binlog con stop-datetime (esclusivo)
mysqlbinlog \
  --start-datetime="2025-01-01 02:00:00" \
  --stop-datetime="2025-01-02 15:44:59" \
  /var/lib/mysql/mysql-bin.000041 \
  /var/lib/mysql/mysql-bin.000042 \
  /var/lib/mysql/mysql-bin.000043 \
  | mysql -u root -p

# Alternativa: usare --stop-position invece di --stop-datetime
# per maggiore precisione (evitare dipendenza dall'orologio)
mysqlbinlog --start-position=4 --stop-position=123456 \
  /var/lib/mysql/mysql-bin.000043 \
  | mysql -u root -p
```

### XtraBackup per MySQL

Percona XtraBackup permette backup "hot" (senza lock) di InnoDB per database grandi.

```bash
# Backup completo
xtrabackup \
  --backup \
  --target-dir=/backup/full-$(date +%Y%m%d) \
  --user=backup_user \
  --password=backup_pass \
  --host=localhost \
  --port=3306 \
  --datadir=/var/lib/mysql

# Backup incrementale (rispetto al backup completo)
xtrabackup \
  --backup \
  --target-dir=/backup/incr-$(date +%Y%m%d-%H%M%S) \
  --incremental-basedir=/backup/full-20250101 \
  --user=backup_user \
  --password=backup_pass

# Preparare il backup per il restore
# Prima: preparare il backup completo (senza applicare incrementali)
xtrabackup --prepare --apply-log-only --target-dir=/backup/full-20250101

# Applicare l'incrementale
xtrabackup --prepare --apply-log-only \
  --target-dir=/backup/full-20250101 \
  --incremental-dir=/backup/incr-20250102-030000

# Preparazione finale (senza --apply-log-only)
xtrabackup --prepare --target-dir=/backup/full-20250101

# Restore
systemctl stop mysql
rm -rf /var/lib/mysql/*
xtrabackup --copy-back --target-dir=/backup/full-20250101 --datadir=/var/lib/mysql
chown -R mysql:mysql /var/lib/mysql
systemctl start mysql
```

## Backup da Replica (Offloading)

Il backup dal nodo primario ha un impatto sulle performance del primario stesso (I/O, CPU). Una pratica comune è eseguire i backup dalla replica, preservando le performance del primario.

```bash
# Configurazione per backup da replica PostgreSQL
# Nella replica, impostare:
# postgresql.conf della replica:
hot_standby = on  # già attivo per le repliche in lettura

# Eseguire pg_basebackup dalla replica
pg_basebackup \
  --host=replica.example.com \
  --port=5432 \
  --username=replicator \
  --pgdata=/backup/base/$(date +%Y%m%d) \
  --wal-method=stream \
  --format=tar \
  --compress=9

# Con pgBackRest: configurare il backup dalla replica
# pgbackrest.conf aggiungere il nodo replica come pg2
[main]
pg1-path=/var/lib/postgresql/data
pg1-host=primary.example.com    # primario per il WAL archiving
pg2-path=/var/lib/postgresql/data
pg2-host=replica.example.com    # replica per il backup dei file
pg2-host-user=postgres

# Eseguire backup dalla replica
pgbackrest --stanza=main --pg2-host=replica.example.com backup
```

## Retention Policy e Rotazione

```bash
#!/bin/bash
# retention-policy.sh: gestione della retention dei backup

BACKUP_DIR="/backup"
WAL_DIR="/wal-archive"
S3_BUCKET="s3://my-postgres-backups"
FULL_RETENTION_DAYS=30   # mantenere backup completi per 30 giorni
INCR_RETENTION_DAYS=7    # mantenere backup incrementali per 7 giorni
WAL_RETENTION_DAYS=7     # mantenere WAL per 7 giorni

# Cancellare backup completi vecchi
find "${BACKUP_DIR}/full" -maxdepth 1 -type d \
  -mtime +${FULL_RETENTION_DAYS} \
  -exec rm -rf {} +

# Cancellare backup incrementali vecchi
find "${BACKUP_DIR}/incr" -maxdepth 1 -type d \
  -mtime +${INCR_RETENTION_DAYS} \
  -exec rm -rf {} +

# Cancellare WAL locali vecchi
find "${WAL_DIR}" -type f \
  -mtime +${WAL_RETENTION_DAYS} \
  -exec rm -f {} +

# Su S3: lifecycle policy (configurare in AWS console o CLI)
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-postgres-backups \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "wal-retention",
        "Status": "Enabled",
        "Filter": {"Prefix": "wal/"},
        "Expiration": {"Days": 7}
      },
      {
        "ID": "full-backup-retention",
        "Status": "Enabled",
        "Filter": {"Prefix": "base/"},
        "Expiration": {"Days": 30}
      }
    ]
  }'
```

## Test del Recovery

Un backup non testato non è un backup: è una promessa non verificata. Il test del recovery deve essere eseguito regolarmente (almeno settimanalmente) su un ambiente separato.

```bash
#!/bin/bash
# test-recovery.sh: verifica che il backup sia recuperabile

TEST_PGDATA="/tmp/test-recovery-$(date +%Y%m%d)"
TEST_PORT=5499
S3_BUCKET="s3://my-postgres-backups"
LATEST_BACKUP=$(aws s3 ls "${S3_BUCKET}/base/" | sort | tail -1 | awk '{print $2}')

echo "Test recovery da backup: ${LATEST_BACKUP}"
echo "Inizio: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# 1. Scaricare il backup più recente da S3
mkdir -p "${TEST_PGDATA}"
aws s3 sync "${S3_BUCKET}/base/${LATEST_BACKUP}" "${TEST_PGDATA}/"

# 2. Estrarre i tar
tar -xzf "${TEST_PGDATA}/base.tar.gz" -C "${TEST_PGDATA}/"
tar -xzf "${TEST_PGDATA}/pg_wal.tar.gz" -C "${TEST_PGDATA}/pg_wal/"

# 3. Configurare il recovery
touch "${TEST_PGDATA}/recovery.signal"
cat >> "${TEST_PGDATA}/postgresql.conf" << EOF
port = ${TEST_PORT}
restore_command = 'aws s3 cp ${S3_BUCKET}/wal/%f %p'
recovery_target_action = 'promote'
EOF

# 4. Avviare PostgreSQL in modalità recovery
chown -R postgres:postgres "${TEST_PGDATA}"
sudo -u postgres pg_ctl start -D "${TEST_PGDATA}" -l "${TEST_PGDATA}/recovery.log"

# 5. Attendere il completamento del recovery
TIMEOUT=300
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if sudo -u postgres psql -p ${TEST_PORT} -c "SELECT 1;" &>/dev/null; then
        echo "Recovery completato in ${ELAPSED}s"
        break
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "ERRORE: Recovery non completato entro ${TIMEOUT}s"
    cat "${TEST_PGDATA}/recovery.log"
    exit 1
fi

# 6. Verificare integrità
echo "--- Verifica integrità ---"
sudo -u postgres psql -p ${TEST_PORT} -c "
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
"

# 7. Pulizia
sudo -u postgres pg_ctl stop -D "${TEST_PGDATA}"
rm -rf "${TEST_PGDATA}"

echo "Test recovery completato con successo: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
```

## Stima RTO e RPO con Diversi Approcci

| Strategia | RPO | RTO | Costo storage | Complessità |
|-----------|-----|-----|---------------|-------------|
| Solo backup giornaliero | ~24h | Ore (restore + WAL replay) | Basso | Bassa |
| Backup + WAL archiving | < 5 min (WAL flush interval) | 15-60 min | Medio | Media |
| Backup + WAL + replica | ~0 (sincrona) | < 1 min (failover) | Alto | Alta |
| Backup + PITR + replica | < 1s (sincrona) | < 30s (Patroni) | Alto | Alta |

La combinazione ottimale per la maggior parte dei sistemi di produzione è: backup base giornaliero con pgBackRest + WAL archiving continuo + almeno una replica streaming. Questo permette RPO vicino a zero (limitato dal ritardo di archiviazione WAL) e RTO di secondi (failover automatico) o minuti (PITR da backup).

