# MySQL/MariaDB Backup e Recovery

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
1. Backup Types e Strategie
2. mysqldump Deep Dive
3. Physical Backup con XtraBackup
4. Point-in-Time Recovery
5. Clone e Alternative Methods
6. Backup Verification
7. Disaster Recovery Planning

---

## 1. Backup Types e Strategie

### 1.1 Logical vs Physical

La scelta tra backup logico e fisico dipende da database size, requisitos di recovery time, e risorse disponibili.

**Logical Backup**:
- Export SQL statements (INSERT, CREATE TABLE)
- Text format leggibile
- Portabile tra versioni MySQL/MariaDB
- Più lento per grandi database
- Meno efficiente per restores completi

**Physical Backup**:
- Copia raw file del database
- Formato binario
- Più veloce per grandi database
- Version-specific (stessa versione per restore)
- Include tutti i dati

**Confronto**:
| Aspetto | Logical | Physical |
|---------|---------|----------|
| Speed backup | Più lento | Più veloce |
| Speed restore | Più lento | Più veloce |
| Portabilità | Alta | Bassa |
| Size backup | Maggiore | Minore |
| Compressione | Limitata | Nativa |

### 1.2 Full vs Incremental vs Differential

**Full Backup**: Backup completo del database
```bash
#mysqldump
mysqldump -u root -p --single-transaction --all-databases > full.sql

#XtraBackup
xtrabackup --backup --target-dir=/backup/full
```

**Incremental Backup**: Solo modifiche dall'ultimo backup
```bash
# Prima: full backup
xtrabackup --backup --target-dir=/backup/full

# Poi: incremental
xtrabackup --backup --target-dir=/backup/inc1 \
  --incremental-basedir=/backup/full

# Ancora incremental
xtrabackup --backup --target-dir=/backup/inc2 \
  --incremental-basedir=/backup/inc1
```

**Differential Backup**: Solo modifiche dall'ultimo full backup
```bash
# Full
xtrabackup --backup --target-dir=/backup/full

# Differential (basato su full)
xtrabackup --backup --target-dir=/backup/diff1 \
  --incremental-basedir=/backup/full
```

**Strategies**:
- Daily full + hourly incremental
- Weekly full + daily differential
- Full monthly + incrementals daily

### 1.3 Online vs Offline

**Online Backup**: Database running durante backup
- InnoDB supporta consistent backup con --single-transaction
- MyISAM può essere inconsistente
- Lock minori, più flessibilità

```bash
# InnoDB online (consistent)
mysqldump -u root -p --single-transaction --all-databases > backup.sql
```

**Offline Backup**: Database stopped
- Garantito consistente senza locking
- Downtime richiesto
- Più semplice, più sicuro

```bash
# Stop MySQL
systemctl stop mysql

# Copy data directory
tar -czf /backup/mysql-data.tar.gz /var/lib/mysql

# Start MySQL
systemctl start mysql
```

### 1.4 Backup Retention Policy

```sql
-- Policy esempio:
-- Daily full: keep 7 days
-- Weekly full: keep 4 weeks
-- Monthly full: keep 12 months

-- Monitoring backup size
SELECT 
    table_schema AS database_name,
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
GROUP BY table_schema;
```

---

## 2. mysqldump Deep Dive

### 2.1 Basic Usage

```bash
# Backup singola database
mysqldump -u root -p mydb > mydb.sql

# Multiple databases
mysqldump -u root -p --databases db1 db2 > dbs.sql

# All databases
mysqldump -u root -p --all-databases > all.sql

# Specific tables
mysqldump -u root -p mydb orders customers > tables.sql
```

### 2.2 Important Options

```bash
# Complete insert con column names
# Utile per debugging e schema changes
mysqldump -u root -p --complete-insert mydb

# Add DROP TABLE statements
mysqldump -u root -p --add-drop-table mydb

# Disable keys (faster import)
mysqldump -u root -p --disable-keys mydb

# Extended inserts (smaller file, faster import)
mysqldump -u root -p --extended-insert mydb

# Lock tables (consistency per non-InnoDB)
mysqldump -u root -p --lock-tables mydb

# Transactional (InnoDB consistent snapshot)
mysqldump -u root -p --single-transaction mydb

# Include triggers e routines
mysqldump -u root -p --routines --triggers mydb

# Events
mysqldump -u root -p --events mydb
```

### 2.3 Advanced mysqldump

**Filtered backup**:
```bash
# Backup con WHERE clause
mysqldump -u root -p mydb orders \
  --where="created_at > '2024-01-01'" > orders_2024.sql

# Backup specific columns
mysqldump -u root -p mydb orders \
  --columns=id,created_at,total > orders_columns.sql
```

**Compression**:
```bash
# Direct compression
mysqldump -u root -p mydb | gzip > mydb.sql.gz

# Split large dumps
mysqldump -u root -p mydb | split -b 1000M - dump_part_
```

### 2.4 Restore

```bash
# Restore singola database
mysql -u root -p mydb < mydb.sql

# Restore all
mysql -u root -p < all.sql

# Restore compressed
gunzip < mydb.sql.gz | mysql -u root -p mydb

# Restore specific tables
mysql -u root -p mydb < tables.sql
```

### 2.5 mydumper/myloader

**mydumper** è più veloce di mysqldump per grandi database:

```bash
# Install
apt install mydumper

# Backup with threads
mydumper -u root -p -B mydb -o /backup/dir \
  --threads=4 \
  --rows=10000 \
  --compress \
  --build-empty-files

# Restore
myloader -u root -p -B mydb -d /backup/dir \
  --threads=4
```

**Vantaggi mydumper**:
- Backup parallelo (molto più veloce)
- Tablestream support
- Consistent backup con --snapshot
- Chunked output

---

## 3. Physical Backup con XtraBackup

### 3.1 XtraBackup Overview

**XtraBackup** è lo standard per backup fisici InnoDB. Supporta hot backup, compression, encryption.

### 3.2 Full Backup

```bash
# Install
apt install percona-xtrabackup

# Full backup
xtrabackup --backup \
  --user=root \
  --password=pass \
  --target-dir=/backup/full \
  --no-timestamp

# Con compression
xtrabackup --backup \
  --user=root \
  --password=pass \
  --target-dir=/backup/compressed \
  --compress \
  --compress-threads=4
```

### 3.3 Incremental Backup

```bash
# Full backup (base)
xtrabackup --backup \
  --user=root \
  --password=pass \
  --target-dir=/backup/full

# Primo incremental
xtrabackup --backup \
  --user=root \
  --password=pass \
  --target-dir=/backup/inc1 \
  --incremental-basedir=/backup/full

# Secondo incremental
xtrabackup --backup \
  --user=root \
  --password=pass \
  --target-dir=/backup/inc2 \
  --incremental-basedir=/backup/inc1
```

### 3.4 Prepare e Restore

**Prepare (apply logs)**:
```bash
# Prepare full
xtrabackup --prepare --target-dir=/backup/full

# Prepare incremental (apply to base)
xtrabackup --prepare \
  --target-dir=/backup/inc1 \
  --incremental-basedir=/backup/full
```

**Restore**:
```bash
# Stop MySQL
systemctl stop mysql

# Remove existing data
rm -rf /var/lib/mysql/*

# Copy back
xtrabackup --copy-back --target-dir=/backup/full

# Set permissions
chown -R mysql:mysql /var/lib/mysql

# Start MySQL
systemctl start mysql
```

### 3.5 MariaDB Backup

```bash
# Mariabackup (drop-in replacement per XtraBackup)
mariabackup --backup \
  --user=root \
  --password=pass \
  --target-dir=/backup/mariadb

# Prepare
mariabackup --prepare --target-dir=/backup/mariadb

# Restore
mariabackup --copy-back --target-dir=/backup/mariadb
```

---

## 4. Point-in-Time Recovery

### 4.1 Setup Binary Logs

```ini
# my.cnf
server-id = 1
log_bin = /var/log/mysql/mysql-bin
binlog_format = ROW

# Per retention
expire_logs_days = 7
max_binlog_size = 1G
```

### 4.2 PITR Process

Point-in-time recovery permette di recoverare a un momento specifico.

**Step 1: Restore last full backup**:
```bash
mysql -u root -p mydb < full_backup.sql
```

**Step 2: Identify binlog position**:
```bash
# Vedere position del backup
mysql -u root -p -e "SHOW MASTER STATUS" mydb

# Output:
-- File: mysql-bin.000123
-- Position: 456
```

**Step 3: Apply binlogs to point in time**:
```bash
# Specific datetime
mysqlbinlog \
  --stop-datetime="2024-01-15 10:30:00" \
  mysql-bin.000123 | mysql -u root -p mydb

# O specific position
mysqlbinlog \
  --stop-position=12345 \
  mysql-bin.000123 | mysql -u root -p mydb
```

### 4.3 GTID-Based PITR

```bash
# Using GTID
mysqlbinlog --skip-gtids mysql-bin.000123 | mysql -u root -p mydb

# From position to end
mysqlbinlog --start-position=456 mysql-bin.000123 | mysql -u root -p mydb
```

### 4.4 Recover to Specific Table

```bash
# Extract specific table from binlog
mysqlbinlog mysql-bin.000123 | grep -A 100 "CREATE TABLE" > table.sql
```

---

## 5. Clone e Alternative Methods

### 5.1 MySQL 8.0 Clone Plugin

```sql
-- Install plugin
INSTALL PLUGIN clone SONAME 'mysql_clone.so';

-- Verify
SHOW PLUGINS;

-- Clone from donor
SET GLOBAL clone_valid_donor_list = 'admin:password@donor_host:3306';
CLONE INSTANCE FROM 'admin'@'donor_host':3306;
```

**Clone behavior**:
- Consistent snapshot
- Non-bloccante sul donor
- Copia dati e metadata
- Non copia users/privileges

### 5.2 LVM Snapshots

```bash
# Setup LVM
pvcreate /dev/sdb1
vgcreate vgmysql /dev/sdb1
lvcreate -L 20G -n lvdata vgmysql

# Create snapshot
lvcreate -L 10G -s -n mysql_snap /dev/vgmysql/lvdata

# Mount snapshot
mount /dev/vgmysql/mysql_snap /mnt/snap

# Copy files
tar -czf /backup/mysql-$(date +%Y%m%d).tar.gz -C /mnt/snap .

# Cleanup
umount /mnt/snap
lvremove /dev/vgmysql/mysql_snap
```

### 5.3 EBS Snapshots (AWS)

```bash
# Create snapshot
aws ec2 create-snapshot \
  --volume-id vol-123456789 \
  --description "MySQL backup $(date)"

# Restore
aws ec2 create-volume \
  --snapshot-id snap-123456789 \
  --availability-zone us-east-1a

# Attach to instance
aws ec2 attach-volume \
  --volume-id vol-new \
  --instance-id i-123456789 \
  --device /dev/sdf
```

---

## 6. Backup Verification

### 6.1 Verify Backup Integrity

```bash
# Test MySQL dump
mysql -u root -p -e "SELECT 1" < backup.sql

# Check compressed
gunzip -t backup.sql.gz

# Verify XtraBackup
xtrabackup --prepare --target-dir=/backup/full
```

### 6.2 Test Restore

```bash
# Create test database
mysql -u root -p -e "CREATE DATABASE test_restore"

# Restore to test
mysql -u root -p test_restore < backup.sql

# Verify
mysql -u root -p -e "SHOW TABLES" test_restore

# Cleanup
mysql -u root -p -e "DROP DATABASE test_restore"
```

---

## 7. Disaster Recovery Planning

### 7.1 Recovery Time Objectives

```sql
-- Definire obiettivi:
-- RTO (Recovery Time Objective): quanto tempo per recover?
-- RPO (Recovery Point Objective): quanti dati posso perdere?

-- Esempi:
-- Critical: RTO 1 hour, RPO 0 (no data loss)
-- Important: RTO 4 hours, RPO 1 hour
-- Standard: RTO 24 hours, RPO 24 hours
```

### 7.2 Recovery Procedures

```bash
#!/bin/bash
# recovery.sh - Disaster recovery script

# Step 1: Identify failure
echo "Checking system status..."
systemctl status mysql || echo "MySQL not running"

# Step 2: Assess damage
echo "Checking data integrity..."
mysql -u root -p -e "SHOW DATABASES"

# Step 3: Restore
echo "Restoring from backup..."
xtrabackup --copy-back --target-dir=/backup/full

# Step 4: Apply binlogs
echo "Applying point-in-time recovery..."
mysqlbinlog --start-position=456 mysql-bin.000123 | mysql -u root -p

# Step 5: Verify
echo "Verifying..."
mysql -u root -p -e "SELECT COUNT(*) FROM orders"
```

### 7.3 Documentation

```sql
-- Documentare:
-- 1. Backup schedule
-- 2. Retention policy  
-- 3. Recovery procedures
-- 4. Test schedule
-- 5. Contact information

-- Test recovery quarterly!
```

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*