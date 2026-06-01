# Redis: Persistence, Backup and Disaster Recovery

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [x] Review tecnica
- [x] Formattazione
- [ ] Pubblicazione

## Table of Contents

1. [Persistence Overview](#1-persistence-overview)
2. [RDB Snapshots](#2-rdb-snapshots)
3. [AOF (Append-Only File)](#3-aof-append-only-file)
4. [Hybrid Persistence (RDB+AOF)](#4-hybrid-persistence-rdb-aof)
5. [Backup Strategies](#5-backup-strategies)
6. [Point-in-Time Recovery](#6-point-in-time-recovery)
7. [Disaster Recovery](#7-disaster-recovery)
8. [Redis on Kubernetes Persistence](#8-redis-on-kubernetes-persistence)
9. [Troubleshooting](#9-troubleshooting)
10. [Q&A](#10-qa)
11. [Exercises](#11-exercises)

---

## 1. Persistence Overview

### 1.1 Why Persistence Matters

Redis is an in-memory data store. Without persistence, a process restart means total data loss. Persistence bridges the gap between in-memory speed and on-disk durability. Every production Redis deployment must answer one question: **how much data can you afford to lose?**

The answer determines which persistence mechanism to use:

| Scenario | Acceptable Loss | Recommended |
|----------|----------------|-------------|
| Pure cache (data reconstructible) | All | None or RDB |
| Session store | A few seconds | AOF `everysec` |
| Primary data store | None | AOF `always` or hybrid |
| Queue / message broker | Sub-second | AOF `everysec` + replication |
| Leaderboard / counter | Minutes | RDB snapshots |

### 1.2 The Two Mechanisms

Redis provides two fundamentally different persistence approaches:

**RDB (Redis Database Backup)** -- Point-in-time snapshots of the entire dataset, written as a compact binary file. Think of it as a photograph of memory at a specific instant.

**AOF (Append-Only File)** -- A sequential log of every write command received by the server. Think of it as a journal that records every mutation. Replaying the journal reconstructs state.

### 1.3 Redis 7+ Multi-Part AOF

Starting with Redis 7.0, the AOF is split into multiple files managed under a manifest:

```
appendonlydir/
  appendonly.aof.1.base.rdb      # RDB preamble (optional)
  appendonly.aof.1.incr.aof      # Incremental AOF segments
  appendonly.aof.2.incr.aof
  appendonly.aof.manifest         # Tracks active files
```

This replaced the single-file AOF model. The manifest-based approach eliminates the risk of a corrupted monolithic AOF blocking startup.

### 1.4 Persistence Decision Matrix

```
                    RDB only    AOF only    Hybrid (RDB+AOF)
Startup speed       Fast        Slow        Fast (RDB preamble)
Data safety         Low         High        High
Disk usage          Low         High        Medium
CPU impact          Periodic    Continuous  Mixed
Fork overhead       Yes         Rewrite     Both
Recommended for     Cache       DB-like     Production default
```

---

## 2. RDB Snapshots

### 2.1 How RDB Works Internally

When Redis creates an RDB snapshot, it follows this sequence:

1. **fork()**: Redis calls the system `fork()` to create a child process. The parent continues serving requests; the child writes the snapshot.
2. **Copy-on-Write (CoW)**: The OS uses CoW semantics. Parent and child share memory pages until one writes to a page, at which point the OS copies that page. This keeps memory overhead proportional to the write volume during the snapshot, not the total dataset size.
3. **Serialization**: The child iterates all databases, serializing each key-value pair into the RDB binary format.
4. **Atomic replace**: The child writes to a temporary file (`temp-<pid>.rdb`), then atomically renames it to the configured `dbfilename`. This guarantees a crash during write never corrupts the existing snapshot.
5. **Exit**: The child process exits. The parent notes the completion via `waitpid()`.

```
Parent process                 Child process
     |                              |
     |--- fork() --->               |
     |  (continue serving)          |-- serialize DB to temp file
     |  (CoW pages as needed)       |-- fsync temp file
     |                              |-- rename temp -> dump.rdb
     |<-- waitpid() ---             |-- exit
     |  (log "Background saving
     |   terminated with success")
```

### 2.2 RDB Configuration

```bash
# redis.conf -- RDB settings

# Save triggers: save <seconds> <changes>
# "Save if at least <changes> keys changed in <seconds>"
save 3600 1        # After 3600s (1 hour) if at least 1 key changed
save 300 100       # After 300s (5 min) if at least 100 keys changed
save 60 10000      # After 60s (1 min) if at least 10000 keys changed

# To disable RDB completely:
# save ""

# Stop writes on BGSAVE failure (safety net)
stop-writes-on-bgsave-error yes

# Enable LZF compression (slight CPU cost, major space savings)
rdbcompression yes

# CRC64 checksum at end of file (catches corruption)
rdbchecksum yes

# Sanitize ziplist/listpack entries during RDB load
# Protects against crafted RDB attacks
sanitize-dump-payload clients

# Filename
dbfilename dump.rdb

# Directory where RDB (and AOF) files live
dir /var/lib/redis

# Delete RDB file used by replication ASAP after sync
rdb-del-sync-files no
```

### 2.3 SAVE vs BGSAVE

```bash
# SAVE: synchronous, blocks ALL clients
# Use ONLY in maintenance windows or shutdown hooks
redis-cli SAVE
# Output: OK (after potentially minutes of blocking)

# BGSAVE: asynchronous, forks a child
redis-cli BGSAVE
# Output: Background saving started

# Check if a BGSAVE is in progress
redis-cli LASTSAVE
# Returns: Unix timestamp of last successful save

# Detailed info
redis-cli INFO persistence
# Output includes:
#   rdb_bgsave_in_progress:0
#   rdb_last_save_time:1716379200
#   rdb_last_bgsave_status:ok
#   rdb_last_bgsave_time_sec:2
#   rdb_current_bgsave_time_sec:-1
#   rdb_saves:145
```

### 2.4 SAVE on Shutdown

By default, Redis performs a synchronous SAVE on `SHUTDOWN` (unless `SHUTDOWN NOSAVE` is specified). This means a clean shutdown always produces a consistent RDB:

```bash
# Clean shutdown with save (default)
redis-cli SHUTDOWN

# Force shutdown without saving (data may be lost)
redis-cli SHUTDOWN NOSAVE

# Save and shutdown even if persistence is disabled
redis-cli SHUTDOWN SAVE
```

### 2.5 RDB File Inspection

```bash
# Check RDB integrity
redis-check-rdb /var/lib/redis/dump.rdb
# Output: successful if file is valid

# Get RDB file info (Redis 7+)
redis-check-rdb --info /var/lib/redis/dump.rdb
# Shows: Redis version, creation time, used memory, key count per DB

# Parse RDB for analysis (using rdb-tools, a third-party utility)
# pip install rdbtools python-lzf
rdb --command memory /var/lib/redis/dump.rdb --bytes 1024 -f memory_report.csv
# Generates per-key memory report for keys > 1KB
```

### 2.6 RDB Advantages and Limitations

**Advantages**:
- Compact single-file format, ideal for backups and transport
- Fast restart: loading an RDB is significantly faster than replaying AOF
- Minimal runtime overhead (only periodic forks)
- Excellent for disaster recovery: ship one file off-site

**Limitations**:
- Data loss between snapshots. If Redis crashes 4 minutes after the last snapshot and your interval is 5 minutes, those 4 minutes are gone
- fork() can be expensive on large datasets (10GB+). The fork itself is fast (CoW), but the parent pays for CoW page copies during heavy writes
- On systems with Transparent Huge Pages (THP), fork latency and memory usage can spike dramatically

### 2.7 Transparent Huge Pages Warning

THP causes Redis to copy 2MB pages instead of 4KB pages during CoW, massively increasing memory use during BGSAVE:

```bash
# Check current THP status
cat /sys/kernel/mm/transparent_hugepage/enabled
# Output: always [madvise] never

# Disable THP for Redis (recommended)
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# Persist across reboots (systemd)
cat > /etc/systemd/system/disable-thp.service << 'EOF'
[Unit]
Description=Disable Transparent Huge Pages
DefaultDependencies=no
After=sysinit.target local-fs.target
Before=redis-server.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo never > /sys/kernel/mm/transparent_hugepage/enabled && echo never > /sys/kernel/mm/transparent_hugepage/defrag'

[Install]
WantedBy=basic.target
EOF

systemctl daemon-reload
systemctl enable disable-thp.service
```

### 2.8 Monitoring BGSAVE Memory Overhead

```bash
# During BGSAVE, watch CoW memory usage
redis-cli INFO persistence | grep rdb
# rdb_last_cow_size:8388608   <-- 8MB of CoW pages copied

# OS-level monitoring (Linux)
# The child process's RSS grows as CoW pages are duplicated
watch -n 1 'ps -C redis-server -o pid,rss,vsz,comm'

# If CoW size is large relative to dataset, writes are heavy during save
# Consider scheduling BGSAVE during low-write periods
```

---

## 3. AOF (Append-Only File)

### 3.1 How AOF Works

Every write command that modifies the dataset is appended to the AOF in Redis protocol format (RESP). On restart, Redis replays the AOF from beginning to end, reconstructing the dataset.

```
Write arrives -> Execute in memory -> Append to AOF buffer -> fsync to disk
```

The AOF buffer is flushed to disk according to the configured `appendfsync` policy.

### 3.2 AOF Configuration

```bash
# redis.conf -- AOF settings

# Enable AOF
appendonly yes

# AOF file naming (Redis 7+ uses appendonlydir)
appendfilename "appendonly.aof"
appenddirname "appendonlydir"

# fsync policy -- THE most important durability knob
#
# always   -- fsync after EVERY write. Maximum durability, significant
#             performance cost (hundreds of ops/sec vs millions).
#             Use when Redis is a primary data store with zero-loss requirement.
#
# everysec -- fsync once per second (DEFAULT). You can lose at most ~1 second
#             of writes. Best balance of durability and performance.
#             Recommended for most production deployments.
#
# no       -- Let the OS decide when to flush (typically every 30s on Linux).
#             Fastest but you can lose 30+ seconds of data.
#             Acceptable only for pure cache workloads.
appendfsync everysec

# Prevent fsync during BGSAVE/BGREWRITEAOF
# Setting to yes reduces disk contention but risks more data loss on crash
no-appendfsync-on-rewrite no

# Automatic AOF rewrite triggers
# Rewrite when the AOF is 100% larger than after the last rewrite
auto-aof-rewrite-percentage 100
# Minimum AOF size before auto-rewrite kicks in
auto-aof-rewrite-min-size 64mb

# Handle truncated AOF on startup (e.g., crash during write)
aof-load-truncated yes

# Use RDB preamble in AOF (hybrid mode, see section 4)
aof-use-rdb-preamble yes

# AOF timestamp annotations (Redis 7+)
# Enables point-in-time recovery
aof-timestamp-enabled no
```

### 3.3 fsync Policies Deep Dive

```
Policy      Durability      Performance          Use Case
----------- --------------- -------------------- --------------------------
always      ~0 data loss    ~10K ops/sec         Financial data, primary store
everysec    ~1s data loss   ~100K+ ops/sec       General production
no          ~30s data loss  Maximum throughput    Pure cache, ephemeral data
```

The `always` policy calls `fsync()` after every write. On Linux, this means the kernel flushes the page cache to disk before returning. SSDs handle this well; spinning disks suffer.

The `everysec` policy spawns a background thread that calls `fsync()` once per second. If the previous fsync is still running when the next tick arrives, Redis logs a warning:

```
Asynchronous AOF fsync is taking too long (disk is busy?). 
Writing the AOF buffer without waiting for fsync to complete, 
this may slow down Redis.
```

This warning is a critical signal of disk saturation.

### 3.4 AOF Rewrite

The AOF grows indefinitely as commands accumulate. The rewrite process compacts it:

1. Redis forks a child process
2. The child reads the current dataset from memory and writes the minimal set of commands that reconstruct it
3. While the child writes, new commands from the parent are buffered in a rewrite buffer
4. When the child finishes, the parent appends the rewrite buffer to the new AOF
5. The new AOF atomically replaces the old one

```bash
# Manual rewrite
redis-cli BGREWRITEAOF
# Output: Background append only file rewriting started

# Monitor rewrite progress
redis-cli INFO persistence
# aof_rewrite_in_progress:1
# aof_rewrite_scheduled:0
# aof_last_rewrite_time_sec:3
# aof_current_rewrite_time_sec:2

# In Redis 7+ with multi-part AOF, old segments are deleted after
# a successful rewrite, governed by the manifest file
```

**Before rewrite** (verbose AOF):
```
*3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$1\r\n1\r\n
*3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$1\r\n2\r\n
*3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$1\r\n3\r\n
*3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$1\r\n4\r\n
*3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$1\r\n5\r\n
```

**After rewrite** (compacted):
```
*3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$1\r\n5\r\n
```

Five SET commands for the same key collapse to one.

### 3.5 AOF Repair

If Redis fails to start because of a corrupted AOF:

```bash
# Check AOF integrity
redis-check-aof /var/lib/redis/appendonlydir/appendonly.aof.1.incr.aof
# Output: AOF is not valid. Use the --fix option to try fixing it.

# Fix by truncating the corrupted tail
redis-check-aof --fix /var/lib/redis/appendonlydir/appendonly.aof.1.incr.aof
# Output: Successfully truncated AOF

# For Redis 7+ multi-part AOF, fix the specific segment reported in logs
# The manifest file tells you which file is problematic
```

### 3.6 AOF Advantages and Limitations

**Advantages**:
- Much better durability (sub-second with `everysec`, zero-loss with `always`)
- Human-readable format (RESP protocol text)
- Rewritable to compact size
- Recoverable from partial corruption (truncate the bad tail)

**Limitations**:
- Larger files than RDB for the same dataset
- Slower restart (replaying commands is slower than loading a binary snapshot)
- `always` fsync significantly reduces throughput
- Rewrite process also requires fork(), same CoW concerns as RDB

---

## 4. Hybrid Persistence (RDB+AOF)

### 4.1 The Best of Both Worlds

Hybrid persistence uses an RDB snapshot as the AOF preamble. When Redis triggers an AOF rewrite:

1. The child process writes the current dataset as an RDB binary blob at the start of the new AOF
2. Subsequent commands are appended in RESP format after the RDB section
3. On restart, Redis loads the RDB preamble (fast), then replays the RESP tail (small)

This gives you RDB's fast loading with AOF's durability.

### 4.2 Configuration

```bash
# Enable hybrid persistence (recommended for production)
appendonly yes
appendfsync everysec
aof-use-rdb-preamble yes

# RDB saves still run for backup purposes
save 3600 1
save 300 100
save 60 10000
```

### 4.3 File Structure (Redis 7+)

```
/var/lib/redis/appendonlydir/
  appendonly.aof.1.base.rdb       # RDB preamble from last rewrite
  appendonly.aof.1.incr.aof       # Commands since last rewrite
  appendonly.aof.manifest          # Tracks which files to load
```

The manifest file content:

```
file appendonly.aof.1.base.rdb seq 1 type b
file appendonly.aof.1.incr.aof seq 1 type i
```

`type b` = base (RDB preamble), `type i` = incremental (RESP commands).

### 4.4 Loading Order on Restart

```
1. Redis reads the manifest
2. Loads the base RDB file (fast binary deserialization)
3. Replays incremental AOF segments in sequence order
4. Dataset is fully reconstructed
```

If both RDB and AOF are present and `appendonly yes`, Redis always prefers AOF for recovery because AOF is the more durable format. The standalone RDB file (`dump.rdb`) is only used when AOF is disabled.

### 4.5 Production Configuration Template

```bash
# --- Hybrid Persistence Production Config ---

# Enable AOF with hybrid preamble
appendonly yes
appendfsync everysec
aof-use-rdb-preamble yes

# Auto-rewrite when AOF doubles
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 128mb

# RDB snapshots for backup (not primary recovery)
save 3600 1
save 300 100

# Safety: stop writes if persistence fails
stop-writes-on-bgsave-error yes

# Performance: avoid fsync during rewrite
no-appendfsync-on-rewrite no

# Recovery: handle truncated AOF gracefully
aof-load-truncated yes
```

---

## 5. Backup Strategies

### 5.1 Local Backup with Cron

```bash
#!/bin/bash
# /usr/local/bin/redis-backup.sh
# Local RDB backup with rotation

REDIS_CLI="/usr/local/bin/redis-cli"
REDIS_DIR="/var/lib/redis"
BACKUP_DIR="/backup/redis"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Trigger background save
${REDIS_CLI} BGSAVE

# Wait for BGSAVE to complete
while [ "$(${REDIS_CLI} LASTSAVE)" = "$(cat /tmp/redis_lastsave 2>/dev/null)" ]; do
    sleep 1
done
${REDIS_CLI} LASTSAVE > /tmp/redis_lastsave

# Copy RDB file
cp "${REDIS_DIR}/dump.rdb" "${BACKUP_DIR}/dump-${DATE}.rdb"

# Also back up AOF directory if present
if [ -d "${REDIS_DIR}/appendonlydir" ]; then
    tar czf "${BACKUP_DIR}/aof-${DATE}.tar.gz" -C "${REDIS_DIR}" appendonlydir/
fi

# Rotate old backups
find "${BACKUP_DIR}" -name "dump-*.rdb" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "aof-*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup completed: dump-${DATE}.rdb"
```

```bash
# Crontab: daily at 02:00
0 2 * * * /usr/local/bin/redis-backup.sh >> /var/log/redis-backup.log 2>&1
```

### 5.2 Remote Backup with rsync

```bash
#!/bin/bash
# /usr/local/bin/redis-backup-remote.sh
# Backup RDB to remote server via rsync over SSH

REDIS_CLI="/usr/local/bin/redis-cli"
REDIS_DIR="/var/lib/redis"
REMOTE_HOST="backup.internal.example.com"
REMOTE_DIR="/data/redis-backups/$(hostname)"
DATE=$(date +%Y%m%d_%H%M%S)

# Trigger and wait for BGSAVE
${REDIS_CLI} BGSAVE
sleep 2
LAST=$(${REDIS_CLI} LASTSAVE)
while true; do
    CURRENT=$(${REDIS_CLI} LASTSAVE)
    if [ "${CURRENT}" != "${LAST}" ]; then
        break
    fi
    sleep 1
    LAST=${CURRENT}
done

# Copy to temp location to avoid rsync reading a partially-written file
cp "${REDIS_DIR}/dump.rdb" "/tmp/dump-${DATE}.rdb"

# Transfer
rsync -az --progress "/tmp/dump-${DATE}.rdb" "${REMOTE_HOST}:${REMOTE_DIR}/"

# Cleanup temp
rm -f "/tmp/dump-${DATE}.rdb"

echo "Remote backup completed: ${REMOTE_HOST}:${REMOTE_DIR}/dump-${DATE}.rdb"
```

### 5.3 Cloud Storage Backup (S3-Compatible)

```bash
#!/bin/bash
# /usr/local/bin/redis-backup-s3.sh
# Upload RDB to S3 with server-side encryption

REDIS_CLI="/usr/local/bin/redis-cli"
REDIS_DIR="/var/lib/redis"
S3_BUCKET="s3://my-redis-backups"
S3_PREFIX="prod/redis-primary"
DATE=$(date +%Y%m%d_%H%M%S)

${REDIS_CLI} BGSAVE
sleep 2

# Wait for background save to finish
while [ "$(${REDIS_CLI} INFO persistence | grep rdb_bgsave_in_progress | tr -d '\r' | cut -d: -f2)" = "1" ]; do
    sleep 1
done

# Upload with SSE-S3 encryption
aws s3 cp "${REDIS_DIR}/dump.rdb" \
    "${S3_BUCKET}/${S3_PREFIX}/dump-${DATE}.rdb" \
    --sse AES256

# Set lifecycle rule for retention (one-time setup)
# aws s3api put-bucket-lifecycle-configuration \
#   --bucket my-redis-backups \
#   --lifecycle-configuration file://lifecycle.json
```

### 5.4 GCS Backup (Google Cloud Storage)

```bash
#!/bin/bash
# /usr/local/bin/redis-backup-gcs.sh
# Upload RDB to Google Cloud Storage

REDIS_CLI="/usr/local/bin/redis-cli"
REDIS_DIR="/var/lib/redis"
GCS_BUCKET="gs://my-redis-backups"
GCS_PREFIX="prod/redis-primary"
DATE=$(date +%Y%m%d_%H%M%S)

${REDIS_CLI} BGSAVE
sleep 2

# Wait for BGSAVE to complete
while [ "$(${REDIS_CLI} INFO persistence | grep rdb_bgsave_in_progress | tr -d '\r' | cut -d: -f2)" = "1" ]; do
    sleep 1
done

# Upload with customer-managed encryption key
gsutil -o "GSUtil:encryption_key=$(cat /etc/redis/gcs-encryption-key)" \
    cp "${REDIS_DIR}/dump.rdb" \
    "${GCS_BUCKET}/${GCS_PREFIX}/dump-${DATE}.rdb"

# Set lifecycle rule for 30-day retention
# gsutil lifecycle set lifecycle.json ${GCS_BUCKET}

echo "GCS backup completed: ${GCS_BUCKET}/${GCS_PREFIX}/dump-${DATE}.rdb"
```

### 5.5 Backup Monitoring and Alerting

```bash
#!/bin/bash
# /usr/local/bin/redis-backup-monitor.sh
# Alert if no successful backup in the last N hours

MAX_AGE_HOURS=6
BACKUP_DIR="/backup/redis"
ALERT_WEBHOOK="https://hooks.slack.example.com/services/XXX/YYY/ZZZ"

LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/dump-*.rdb 2>/dev/null | head -1)

if [ -z "${LATEST_BACKUP}" ]; then
    ALERT_MSG="CRITICAL: No Redis backups found in ${BACKUP_DIR}"
else
    BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "${LATEST_BACKUP}")) / 3600 ))
    if [ ${BACKUP_AGE} -ge ${MAX_AGE_HOURS} ]; then
        ALERT_MSG="WARNING: Latest Redis backup is ${BACKUP_AGE}h old (threshold: ${MAX_AGE_HOURS}h)"
    fi
fi

if [ -n "${ALERT_MSG}" ]; then
    curl -s -X POST "${ALERT_WEBHOOK}" \
        -H 'Content-Type: application/json' \
        -d "{\"text\": \"${ALERT_MSG}\"}"
fi
```

```bash
# Crontab: check every hour
0 * * * * /usr/local/bin/redis-backup-monitor.sh
```

### 5.6 Backup Strategy Comparison

| Strategy | RPO | Storage Cost | Complexity | Best For |
|----------|-----|-------------|------------|----------|
| Local cron + RDB | Hours | Low | Low | Dev/staging |
| Replica BGSAVE + rsync | Hours | Medium | Medium | Mid-size prod |
| S3/GCS + lifecycle | Hours | Medium | Medium | Cloud-native |
| Replica + continuous ship | Minutes | High | High | Critical data |
| Volume snapshots (K8s) | Seconds | Medium | Low | K8s deployments |

### 5.7 Replication-Based Backup

Never run BGSAVE on the master in high-traffic environments. Instead, back up from a replica:

```bash
# On the replica (configured with `replicaof master_host 6379`)
# The replica already has a consistent copy of data

# Trigger BGSAVE on the replica, not the master
redis-cli -h replica-host BGSAVE

# Copy the replica's RDB
scp replica-host:/var/lib/redis/dump.rdb /backup/
```

This eliminates fork() overhead from the master, keeping production latency stable.

### 5.5 Backup Verification

A backup is only as good as its last successful restore test:

```bash
#!/bin/bash
# Verify a backup by loading it in an isolated Redis instance

BACKUP_FILE="/backup/redis/dump-20260522_020000.rdb"
TEST_PORT=6399
TEST_DIR="/tmp/redis-verify-$$"

mkdir -p "${TEST_DIR}"
cp "${BACKUP_FILE}" "${TEST_DIR}/dump.rdb"

# Start isolated Redis on a different port
redis-server \
    --port ${TEST_PORT} \
    --dir "${TEST_DIR}" \
    --dbfilename dump.rdb \
    --appendonly no \
    --save "" \
    --daemonize yes \
    --pidfile "${TEST_DIR}/redis.pid"

sleep 2

# Verify data is accessible
KEY_COUNT=$(redis-cli -p ${TEST_PORT} DBSIZE | awk '{print $2}')
echo "Loaded ${KEY_COUNT} keys from backup"

# Spot-check a known key
redis-cli -p ${TEST_PORT} GET "health:check:key"

# Shutdown test instance
redis-cli -p ${TEST_PORT} SHUTDOWN NOSAVE
rm -rf "${TEST_DIR}"

echo "Backup verification completed: ${KEY_COUNT} keys loaded successfully"
```

---

## 6. Point-in-Time Recovery

### 6.1 AOF Timestamp Annotations (Redis 7+)

Redis 7 introduced timestamp annotations in the AOF, enabling PITR:

```bash
# Enable timestamps in AOF
aof-timestamp-enabled yes

# The AOF now contains timestamp markers:
# #TS:1716379200
# *3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$1\r\n5\r\n
# #TS:1716379201
# *3\r\n$3\r\nDEL\r\n$6\r\nbadkey\r\n
```

### 6.2 Recovering to a Specific Point in Time

```bash
# Truncate AOF to a specific timestamp
redis-check-aof --truncate-to-timestamp 1716379200 \
    /var/lib/redis/appendonlydir/appendonly.aof.1.incr.aof

# This removes all commands after the specified Unix timestamp
# Then start Redis normally -- it will load data up to that point
```

### 6.3 Manual PITR with AOF Editing

If timestamp annotations are disabled, you can still do approximate PITR by manually editing the AOF:

```bash
# 1. Stop Redis
systemctl stop redis

# 2. Make a copy of the AOF
cp -r /var/lib/redis/appendonlydir /tmp/aof-recovery

# 3. Convert AOF to human-readable format
redis-check-aof --aof-to-preamble no /tmp/aof-recovery/appendonly.aof.1.incr.aof

# 4. Identify the problematic command (e.g., a FLUSHALL)
grep -n "FLUSHALL\|DEL" /tmp/aof-recovery/appendonly.aof.1.incr.aof

# 5. Truncate at the line before the unwanted command
# (Requires understanding RESP format -- each command spans multiple lines)

# 6. Replace the AOF and restart Redis
```

### 6.4 PITR Strategy for Critical Data

For systems where PITR is essential:

```
Tier 1: Continuous -- AOF with everysec + timestamp annotations
Tier 2: Hourly    -- RDB snapshots rotated, shipped off-site
Tier 3: Daily     -- Full backup to S3/GCS with 30-day retention
Tier 4: Weekly    -- Verified restore test on isolated instance
```

---

## 7. Disaster Recovery

### 7.1 Restore from RDB

```bash
# 1. Stop Redis
systemctl stop redis

# 2. Remove existing data files
rm -f /var/lib/redis/dump.rdb
rm -rf /var/lib/redis/appendonlydir

# 3. Copy backup RDB
cp /backup/redis/dump-20260522_020000.rdb /var/lib/redis/dump.rdb

# 4. Fix ownership and permissions
chown redis:redis /var/lib/redis/dump.rdb
chmod 640 /var/lib/redis/dump.rdb

# 5. Ensure AOF is disabled if restoring from RDB only
#    (or Redis will look for AOF first and find nothing)
#    Temporarily in redis.conf:
#    appendonly no

# 6. Start Redis
systemctl start redis

# 7. Verify
redis-cli PING
redis-cli DBSIZE
redis-cli INFO keyspace

# 8. Re-enable AOF if desired
redis-cli CONFIG SET appendonly yes
# Redis will generate a fresh AOF from the in-memory dataset
```

### 7.2 Restore from AOF

```bash
# 1. Stop Redis
systemctl stop redis

# 2. Replace the AOF directory with backup
rm -rf /var/lib/redis/appendonlydir
cp -r /backup/redis/aof-20260522/ /var/lib/redis/appendonlydir

# 3. Fix ownership
chown -R redis:redis /var/lib/redis/appendonlydir

# 4. Ensure AOF is enabled
# In redis.conf: appendonly yes

# 5. Start Redis (it will replay the AOF)
systemctl start redis

# 6. Monitor replay progress in logs
tail -f /var/log/redis/redis-server.log
# You'll see: "DB loaded from append only file: X.XXX seconds"
```

### 7.3 Cross-Region Disaster Recovery

For multi-region setups, combine replication with backup shipping:

```
Primary (us-east-1)
  |
  |-- Replication --> Replica (us-east-1)  [HA within region]
  |
  |-- RDB backup --> S3 (us-east-1)
  |                   |
  |                   |-- Cross-region replication --> S3 (eu-west-1)
  |
  |-- Replication --> Replica (eu-west-1)  [Disaster recovery]
```

```bash
# S3 cross-region replication (setup once)
# Ensures backups survive a full region outage
aws s3api put-bucket-replication \
    --bucket my-redis-backups \
    --replication-configuration '{
        "Role": "arn:aws:iam::role/s3-replication-role",
        "Rules": [{
            "Status": "Enabled",
            "Destination": {
                "Bucket": "arn:aws:s3:::my-redis-backups-dr"
            }
        }]
    }'
```

### 7.4 RTO and RPO Planning

| Strategy | RPO (Data Loss) | RTO (Downtime) |
|----------|-----------------|----------------|
| RDB only (hourly) | Up to 1 hour | Minutes (copy + load) |
| AOF everysec | ~1 second | Minutes to hours (replay) |
| Hybrid + replica | ~1 second | Seconds (promote replica) |
| Hybrid + Sentinel | ~1 second | 5-30 seconds (auto-failover) |
| Redis Cluster | ~1 second | Near-zero (auto-failover) |

### 7.5 Disaster Recovery Runbook Template

```bash
# DR Runbook: Redis Primary Failure
# Estimated RTO: 15 minutes (manual) / 30 seconds (Sentinel)

# Step 1: Assess (1 minute)
redis-cli -h primary-host PING
# If no response:
ssh primary-host "systemctl status redis"

# Step 2: Decide recovery path
# Option A: Promote existing replica (fastest)
# Option B: Restore from backup (if all replicas lost)

# Step 3A: Manual replica promotion
redis-cli -h replica-host REPLICAOF NO ONE
# Update application config to point to replica-host
# After primary is fixed, make it a replica of the new primary

# Step 3B: Restore from backup
# Follow section 7.1 or 7.2 on a fresh host
# Update application config to point to restored host

# Step 4: Verify
redis-cli -h new-primary PING
redis-cli -h new-primary DBSIZE
redis-cli -h new-primary INFO replication

# Step 5: Post-mortem
# Document: what failed, timeline, data loss, corrective actions
```

---

## 8. Redis on Kubernetes Persistence

### 8.1 The Challenge

Kubernetes pods are ephemeral. Without persistent volumes, Redis data vanishes when a pod restarts. Additionally, StatefulSets provide stable network identities but require careful volume configuration.

### 8.2 PersistentVolumeClaim for Redis

```yaml
# redis-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-data
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3       # AWS EBS gp3, adjust per provider
  resources:
    requests:
      storage: 50Gi
```

### 8.3 Redis StatefulSet with Persistence

```yaml
# redis-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: default
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7.4-alpine
          ports:
            - containerPort: 6379
          command:
            - redis-server
            - /etc/redis/redis.conf
          volumeMounts:
            - name: redis-data
              mountPath: /data
            - name: redis-config
              mountPath: /etc/redis
          resources:
            requests:
              memory: "2Gi"
              cpu: "500m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
          readinessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 15
            periodSeconds: 20
      volumes:
        - name: redis-config
          configMap:
            name: redis-config
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: gp3
        resources:
          requests:
            storage: 50Gi
```

### 8.4 ConfigMap for Redis Configuration

```yaml
# redis-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: default
data:
  redis.conf: |
    # Persistence
    dir /data
    dbfilename dump.rdb
    appendonly yes
    appendfsync everysec
    aof-use-rdb-preamble yes
    save 3600 1
    save 300 100

    # Memory
    maxmemory 3gb
    maxmemory-policy allkeys-lru

    # Network
    bind 0.0.0.0
    protected-mode no
    tcp-backlog 511

    # Logging
    loglevel notice
```

### 8.5 Backup CronJob on Kubernetes

```yaml
# redis-backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: redis-backup
  namespace: default
spec:
  schedule: "0 */6 * * *"    # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: redis:7.4-alpine
              command:
                - /bin/sh
                - -c
                - |
                  redis-cli -h redis-0.redis BGSAVE
                  sleep 5
                  # Wait for BGSAVE
                  while redis-cli -h redis-0.redis INFO persistence | grep -q "rdb_bgsave_in_progress:1"; do
                    sleep 2
                  done
                  # Copy to backup volume
                  cp /data/dump.rdb /backup/dump-$(date +%Y%m%d_%H%M%S).rdb
                  # Rotate (keep last 20)
                  ls -t /backup/dump-*.rdb | tail -n +21 | xargs rm -f
              volumeMounts:
                - name: redis-data
                  mountPath: /data
                  readOnly: true
                - name: backup-volume
                  mountPath: /backup
          restartPolicy: OnFailure
          volumes:
            - name: redis-data
              persistentVolumeClaim:
                claimName: redis-data-redis-0
            - name: backup-volume
              persistentVolumeClaim:
                claimName: redis-backup-storage
```

### 8.6 Helm Chart Persistence (Bitnami)

```bash
# Using Bitnami Redis Helm chart with persistence
helm install redis oci://registry-1.docker.io/bitnamicharts/redis \
  --set master.persistence.enabled=true \
  --set master.persistence.size=50Gi \
  --set master.persistence.storageClass=gp3 \
  --set replica.persistence.enabled=true \
  --set replica.persistence.size=50Gi \
  --set replica.persistence.storageClass=gp3 \
  --set master.extraFlags="{--appendonly yes,--appendfsync everysec}" \
  --set auth.password="$(openssl rand -base64 32)"
```

### 8.7 Volume Snapshot for K8s Backup

```yaml
# CSI VolumeSnapshot -- crash-consistent backup
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: redis-snapshot-20260522
  namespace: default
spec:
  volumeSnapshotClassName: csi-gp3-snapclass
  source:
    persistentVolumeClaimName: redis-data-redis-0
```

```bash
# Restore from snapshot
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-data-restored
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: gp3
  resources:
    requests:
      storage: 50Gi
  dataSource:
    name: redis-snapshot-20260522
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
EOF
```

### 8.8 Common K8s Persistence Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| No PVC | Data lost on pod restart | Add volumeClaimTemplates |
| Wrong `dir` config | RDB written to ephemeral path | Set `dir /data` matching mountPath |
| ReadWriteMany for single-node | Performance issues | Use ReadWriteOnce |
| No resource limits | OOMKilled during BGSAVE | Set memory limit >= 2x dataset |
| Missing fsGroup | Permission denied on mount | Add `securityContext.fsGroup: 999` |
| emptyDir instead of PVC | Data lost on node drain | Use PVC with durable storage class |

---

## 9. Troubleshooting

### 9.1 BGSAVE Failures

**Error: "Can't save in background: fork: Cannot allocate memory"**

```bash
# Cause: Linux overcommit is disabled and there's not enough memory for fork()
# Even though CoW is efficient, the kernel may reserve full RSS for the child

# Fix: Enable memory overcommit
echo 1 > /proc/sys/vm/overcommit_memory
# Persist:
echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf
sysctl -p

# Alternative: reduce dataset size or add RAM
# Rule of thumb: need ~1.5x dataset memory for safe BGSAVE
```

**Error: "Background saving error"**

```bash
# Check Redis logs
tail -50 /var/log/redis/redis-server.log

# Common causes:
# 1. Disk full
df -h /var/lib/redis

# 2. Permission denied
ls -la /var/lib/redis/
# Fix:
chown redis:redis /var/lib/redis

# 3. Read-only filesystem (K8s or Docker volume issue)
mount | grep "$(df /var/lib/redis | tail -1 | awk '{print $1}')"
```

### 9.2 AOF Growing Unboundedly

```bash
# Check AOF size
ls -lh /var/lib/redis/appendonlydir/

# If AOF is unexpectedly large, trigger manual rewrite
redis-cli BGREWRITEAOF

# If auto-rewrite never triggers, check thresholds
redis-cli CONFIG GET auto-aof-rewrite-*
# Ensure auto-aof-rewrite-percentage > 0
# Ensure auto-aof-rewrite-min-size is reasonable

# Check if rewrite is stuck
redis-cli INFO persistence | grep aof_rewrite
```

### 9.3 Slow Redis Restart

```bash
# Symptom: Redis takes minutes to start
# Cause: large AOF being replayed

# Check which file Redis is loading
tail -f /var/log/redis/redis-server.log
# "DB loaded from append only file: 180.432 seconds"

# Solutions:
# 1. Enable RDB preamble (loads faster)
redis-cli CONFIG SET aof-use-rdb-preamble yes
redis-cli BGREWRITEAOF

# 2. Reduce AOF size by running rewrite before restart
redis-cli BGREWRITEAOF
# Wait for completion, then restart
```

### 9.4 fsync Latency Warnings

```bash
# Log message: "Asynchronous AOF fsync is taking too long"
# Cause: Disk I/O saturation

# Diagnose:
iostat -xz 1 5
# Look for %util > 90% on the Redis disk

# Solutions:
# 1. Use faster disks (SSD/NVMe)
# 2. Move AOF to a separate disk from RDB
# 3. Reduce write volume
# 4. Set no-appendfsync-on-rewrite yes (risky but reduces contention)
```

### 9.5 Corrupted RDB File

```bash
# Symptom: Redis won't start, log shows "Short read or OOM loading DB"
redis-check-rdb /var/lib/redis/dump.rdb
# "--- RDB ERROR ---"

# Recovery options:
# 1. Restore from a previous backup
cp /backup/redis/dump-latest.rdb /var/lib/redis/dump.rdb

# 2. If AOF exists, disable RDB and load from AOF
# In redis.conf: save ""
# Redis will use AOF for recovery

# 3. Use redis-check-rdb for partial recovery info
redis-check-rdb --info /var/lib/redis/dump.rdb
```

### 9.6 Persistence-Related Memory Issues

```bash
# During BGSAVE, memory can spike due to CoW
# Monitor during BGSAVE:
redis-cli INFO memory
# mem_fragmentation_ratio   -- should be near 1.0
# used_memory_rss           -- physical memory used
# lazyfree_pending_objects   -- pending lazy free operations

# If CoW causes OOM:
# 1. Schedule BGSAVE during low-write periods
# 2. Increase system memory (need ~2x dataset for worst case)
# 3. Use replica for backups instead of master
```

---

## 10. Q&A

**Q1: Should I use RDB, AOF, or both?**
A: For production, use both (hybrid with `aof-use-rdb-preamble yes`). You get AOF's durability with RDB's fast restart. For pure caching, RDB alone or no persistence is fine.

**Q2: What happens if Redis crashes mid-BGSAVE?**
A: Nothing bad. The child was writing to a temp file. The old `dump.rdb` is untouched. On restart, Redis loads the last complete snapshot.

**Q3: Does `appendfsync always` guarantee zero data loss?**
A: Almost. It calls `fsync()` after every write, so data hits stable storage before the client gets acknowledgment. But if the disk controller lies about flushing (battery-backed cache failure), you could still lose data. True zero-loss requires replication.

**Q4: How do I migrate from RDB-only to AOF?**
A: Run `CONFIG SET appendonly yes` at runtime. Redis will generate a full AOF from the current dataset. Then update `redis.conf` to persist the change. No restart needed.

**Q5: Can I use NFS for Redis persistence?**
A: Technically yes, but strongly discouraged. NFS adds latency to every fsync, and file locking behavior differs across implementations. Use local SSDs or block storage (EBS, PD).

**Q6: How much disk space does AOF need?**
A: The AOF can be 3-10x larger than the equivalent RDB before rewrite. After rewrite, it's roughly the same size as an RDB plus a small margin. Monitor with `INFO persistence` and set reasonable rewrite thresholds.

**Q7: Why does fork() take so long with large datasets?**
A: `fork()` itself is fast (milliseconds), but the kernel must duplicate page table entries. With 100GB of memory, page tables can be several hundred MB. THP makes this worse. After fork, CoW page copies during heavy writes add latency spikes.

**Q8: What is the `rdb_last_cow_size` metric?**
A: It reports how many bytes were copied due to CoW during the last BGSAVE. A high value relative to `used_memory` means heavy writes during the snapshot. Consider scheduling BGSAVE during quiet periods or using a replica.

**Q9: Can I back up Redis without any performance impact?**
A: Back up from a replica. The master never forks. The replica handles BGSAVE independently. This is the recommended pattern for large production datasets.

**Q10: How do I verify my backups are valid?**
A: Use `redis-check-rdb` for integrity checks. For full validation, load the backup in an isolated Redis instance (different port/host), run `DBSIZE`, and spot-check critical keys. Automate this in CI.

**Q11: What is the difference between Redis 6 and Redis 7 AOF?**
A: Redis 7 introduced multi-part AOF with a manifest file. Instead of one monolithic file, AOF is split into a base file (RDB preamble) and incremental segments. This improves rewrite safety and enables timestamp-based PITR.

**Q12: How do I handle persistence in Redis Cluster?**
A: Each node in a Redis Cluster handles its own persistence independently. Configure RDB+AOF on every master node. Backup each node's RDB separately. For restore, you must restore the correct RDB to each node based on its slot assignments.

**Q13: What is the `no-appendfsync-on-rewrite` setting?**
A: When set to `yes`, Redis skips `fsync()` calls during an active BGREWRITEAOF or BGSAVE. This reduces disk contention (both operations write heavily), but the trade-off is that a crash during rewrite could lose more AOF data. Recommended: `no` for critical data, `yes` if disk I/O is the bottleneck.

**Q14: How do I estimate memory overhead for BGSAVE?**
A: Worst case: 2x your dataset memory (every page is CoW-copied). Typical case: dataset size + 10-30% (only modified pages are copied). Monitor `rdb_last_cow_size` after each BGSAVE to get actual numbers for your workload. For read-heavy workloads, CoW overhead is minimal.

**Q15: Can I run multiple Redis instances on the same machine with different persistence settings?**
A: Yes. Each instance needs its own `dir`, `port`, `dbfilename`, and `appendfilename`. Common pattern: one instance as a cache (no persistence), another as a session store (AOF everysec). Use separate systemd units or supervisord configs.

**Q16: What happens if disk is full during BGSAVE?**
A: The child process fails to write the temp RDB file. Redis logs "Background saving error" and, if `stop-writes-on-bgsave-error yes`, it stops accepting writes. Free disk space and trigger a manual BGSAVE. Always monitor disk usage with alerts at 80% capacity.

**Q17: Is there a way to compress AOF files?**
A: The AOF itself is not compressed (it's RESP text). However, with `aof-use-rdb-preamble yes`, the base file is an RDB which uses LZF compression. The incremental segments remain uncompressed. External compression (gzip for backups) works fine but should not be applied to the live AOF directory.

**Q18: How do I migrate persistence data between Redis versions?**
A: RDB files are forward-compatible within major versions (a Redis 6 RDB loads on Redis 7). Going backward is not guaranteed. For major version upgrades: upgrade the replica first, verify it loads correctly, then promote and upgrade the old master. Always keep a backup of the pre-upgrade RDB.

**Q19: Should I disable persistence entirely for cache-only Redis?**
A: Yes, if the data is fully reconstructible from the source of truth. Set `save ""` and `appendonly no`. This eliminates fork() overhead, disk I/O, and BGSAVE memory spikes. Common for CDN origin-shield caches, query result caches, and rate-limiter counters. If you want warm restart capability, keep RDB with a long save interval (e.g., `save 3600 1`).

---

## 11. Exercises

### Exercise 1: Configure Hybrid Persistence

Set up a Redis instance with hybrid persistence. Verify the configuration:

1. Start Redis with `appendonly yes` and `aof-use-rdb-preamble yes`
2. Write 1000 keys using a loop
3. Trigger `BGREWRITEAOF`
4. Inspect the `appendonlydir/` -- confirm the base file is RDB format (`REDIS` magic bytes)
5. Write 100 more keys
6. Inspect the incremental AOF segment -- confirm it contains RESP commands
7. Restart Redis and verify all 1100 keys are present

### Exercise 2: Simulate and Recover from Data Loss

1. Start Redis with RDB-only persistence (`save 60 10`)
2. Write 500 keys
3. Wait for an automatic RDB save (check `LASTSAVE`)
4. Write 200 more keys
5. Kill Redis with `kill -9` (simulate crash -- no shutdown save)
6. Restart Redis and check `DBSIZE` -- expect ~500, not 700
7. Repeat with AOF `everysec` enabled -- verify you recover ~700 keys

### Exercise 3: Backup and Restore

1. Create a Redis instance with test data (users, sessions, counters)
2. Write a backup script that: triggers BGSAVE, waits for completion, copies the RDB
3. Destroy the Redis data directory
4. Restore from your backup
5. Verify all keys are intact with `DBSIZE` and spot checks

### Exercise 4: AOF Corruption Recovery

1. Start Redis with AOF enabled
2. Write several keys
3. Stop Redis
4. Manually corrupt the AOF (append garbage bytes to the end)
5. Try starting Redis -- observe the error
6. Use `redis-check-aof --fix` to repair
7. Start Redis again and verify data integrity

### Exercise 5: PITR with Timestamps

1. Start Redis 7+ with `aof-timestamp-enabled yes`
2. Write keys at different times (use `sleep` between batches)
3. Note the Unix timestamp between batches
4. Stop Redis
5. Use `redis-check-aof --truncate-to-timestamp <ts>` to recover to a point between batches
6. Restart and verify only the keys before the timestamp exist

### Exercise 6: Kubernetes Persistence

1. Deploy Redis on Kubernetes with the StatefulSet from section 8.3
2. Write test data
3. Delete the pod (`kubectl delete pod redis-0`)
4. Wait for the pod to restart
5. Verify data survived the restart
6. Scale to 0 and back to 1 -- verify data again

### Exercise 7: Monitoring Persistence Health

Write a monitoring script that checks:
- Time since last successful BGSAVE
- AOF rewrite status
- CoW memory during BGSAVE
- Disk space remaining on the persistence volume
- Alert if BGSAVE hasn't succeeded in over 2 hours

### Exercise 8: Compare Persistence Modes Under Load

1. Start three Redis instances: RDB-only, AOF-only, and hybrid
2. Use `redis-benchmark` to generate identical load on all three:
   ```bash
   redis-benchmark -p 6379 -t set,get -n 500000 -d 256 -c 50
   redis-benchmark -p 6380 -t set,get -n 500000 -d 256 -c 50
   redis-benchmark -p 6381 -t set,get -n 500000 -d 256 -c 50
   ```
3. Compare throughput (ops/sec) across the three modes
4. Compare disk usage after the benchmark completes
5. Kill each instance with `kill -9` and restart
6. Compare recovery time and data loss for each mode
7. Document your findings in a comparison table

### Exercise 9: Cross-Region Disaster Recovery Drill

1. Set up two Redis instances simulating two "regions"
2. Configure the second as a replica of the first
3. Write 10,000 keys to the primary
4. Verify replication lag is zero
5. Simulate primary failure (stop the first instance)
6. Promote the replica: `REPLICAOF NO ONE`
7. Write 1,000 new keys to the promoted replica
8. Bring the old primary back as a replica of the new primary
9. Verify all 11,000 keys are consistent across both instances

### Exercise 10: Kubernetes Persistence Resilience

1. Deploy Redis on Kubernetes with the StatefulSet and PVC configuration
2. Write 5,000 keys with varying TTLs
3. Simulate a node failure by cordoning and draining the node
4. Observe the pod rescheduling on another node
5. Verify data survival after rescheduling
6. Take a VolumeSnapshot, write 2,000 more keys
7. Restore from the snapshot to a new PVC
8. Start a second Redis instance on the restored PVC
9. Compare DBSIZE between the two instances (should differ by ~2,000)

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
