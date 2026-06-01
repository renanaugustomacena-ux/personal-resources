# Database Replication — Monitoraggio

## Metriche Fondamentali

### Replication Lag

Il lag di replica è la metrica più critica da monitorare. Indica quanto le repliche sono "indietro" rispetto al primario.

```sql
-- PostgreSQL: lag sul primario
SELECT
    application_name,
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS bytes_lag,
    write_lag,
    flush_lag,
    replay_lag,
    sync_state  -- async, sync, potential, quorum
FROM pg_stat_replication
ORDER BY replay_lag DESC NULLS LAST;

-- PostgreSQL: lag in secondi dalla replica
SELECT
    now() - pg_last_xact_replay_timestamp() AS replica_lag;

-- MySQL: lag sulla replica
SHOW REPLICA STATUS\G
-- Cerca: Seconds_Behind_Source (0 = no lag)
-- Replica_IO_Running: Yes
-- Replica_SQL_Running: Yes
```

### Monitoraggio con Prometheus + postgres_exporter

```yaml
# prometheus.yml - scrape config
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-primary:9187', 'postgres-replica1:9187']

# Alert rules
groups:
  - name: postgres_replication
    rules:
      - alert: PostgresReplicationLagHigh
        expr: pg_replication_lag > 60  # più di 60 secondi
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Replication lag > 60s on {{ $labels.instance }}"

      - alert: PostgresReplicationLagCritical
        expr: pg_replication_lag > 300  # più di 5 minuti
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "CRITICAL: Replication lag > 5min on {{ $labels.instance }}"

      - alert: PostgresReplicaDown
        expr: pg_up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical

      - alert: PostgresReplicationSlotPermanentlyLagging
        expr: pg_replication_slots_wal_retained_bytes > 10737418240  # 10 GB
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Replication slot retaining > 10GB WAL"
```

```python
# Script di monitoring custom
import psycopg2
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ReplicationStatus:
    replica_name: str
    lag_bytes: int
    lag_seconds: float
    is_streaming: bool
    sync_state: str

def check_replication_health(primary_conn_str: str) -> list[ReplicationStatus]:
    conn = psycopg2.connect(primary_conn_str)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                application_name,
                pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes,
                EXTRACT(EPOCH FROM replay_lag) as lag_seconds,
                state = 'streaming' as is_streaming,
                sync_state
            FROM pg_stat_replication
        """)
        results = []
        for row in cur.fetchall():
            status = ReplicationStatus(*row)
            results.append(status)

            if status.lag_seconds > 60:
                logger.warning(
                    f"Replica {status.replica_name} lag: {status.lag_seconds:.1f}s"
                )
            if not status.is_streaming:
                logger.error(
                    f"Replica {status.replica_name} NOT streaming! State: unknown"
                )
    return results
```

---

## Monitoraggio Replication Slots

I replication slot che accumulano WAL sono una causa comune di esaurimento disco.

```sql
-- Lista slot e quanto WAL stanno trattenendo
SELECT
    slot_name,
    plugin,
    slot_type,
    active,
    active_pid,
    restart_lsn,
    confirmed_flush_lsn,
    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS wal_bytes_retained,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS wal_retained_pretty
FROM pg_replication_slots
ORDER BY wal_bytes_retained DESC NULLS LAST;

-- Alert se un slot inattivo sta accumulando
SELECT slot_name, active
FROM pg_replication_slots
WHERE active = false;
-- Azione: DROP REPLICATION SLOT 'slot_name' se non serve più
```

---

## Dashboard Grafana per Replica PostgreSQL

```json
// Panel: Replication Lag (secondi per replica)
{
  "query": "pg_replication_lag{job='postgres', instance=~'$instance'}",
  "type": "timeseries",
  "title": "Replication Lag (seconds)",
  "thresholds": [
    {"value": 30, "color": "yellow"},
    {"value": 120, "color": "red"}
  ]
}
```

```sql
-- Query per tabella di status in Grafana (data source PostgreSQL)
SELECT
    time,
    application_name,
    lag_seconds
FROM (
    SELECT
        now() as time,
        application_name,
        EXTRACT(EPOCH FROM replay_lag) as lag_seconds
    FROM pg_stat_replication
) stats
WHERE $__timeFilter(time)
```

---

## Monitoraggio MySQL Replication

```sql
-- Stato completo sulla replica
SHOW REPLICA STATUS\G

-- Campi chiave da monitorare:
-- Replica_IO_Running: Yes       ← thread IO connesso al primario
-- Replica_SQL_Running: Yes      ← thread SQL applicando i binlog
-- Seconds_Behind_Source: 0      ← lag in secondi
-- Last_Error: ""                ← nessun errore
-- Source_Log_File: binlog.000042
-- Read_Source_Log_Pos: 1234567
-- Relay_Log_File: relay.000015
-- Exec_Source_Log_Pos: 1234567  ← posizione applicata

-- Con GTID (più affidabile)
SELECT
    CHANNEL_NAME,
    SERVICE_STATE,
    RECEIVED_TRANSACTION_SET,
    LAST_ERROR_NUMBER,
    LAST_ERROR_MESSAGE
FROM performance_schema.replication_connection_status;

SELECT
    CHANNEL_NAME,
    SERVICE_STATE,
    LAST_APPLIED_TRANSACTION,
    APPLYING_TRANSACTION,
    LAST_ERROR_MESSAGE
FROM performance_schema.replication_applier_status_by_worker;
```

### Script di Health Check MySQL

```bash
#!/bin/bash
# mysql_replication_check.sh

MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASS="${MYSQL_PASS}"
LAG_THRESHOLD_WARN=30
LAG_THRESHOLD_CRIT=120

status=$(mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASS" \
    -e "SHOW REPLICA STATUS\G" 2>/dev/null)

io_running=$(echo "$status" | grep "Replica_IO_Running" | awk '{print $2}')
sql_running=$(echo "$status" | grep "Replica_SQL_Running" | awk '{print $2}')
lag=$(echo "$status" | grep "Seconds_Behind_Source" | awk '{print $2}')
last_error=$(echo "$status" | grep "Last_Error" | cut -d: -f2-)

if [[ "$io_running" != "Yes" ]] || [[ "$sql_running" != "Yes" ]]; then
    echo "CRITICAL: Replication thread down (IO: $io_running, SQL: $sql_running)"
    echo "Last error: $last_error"
    exit 2
fi

if [[ "$lag" -gt "$LAG_THRESHOLD_CRIT" ]]; then
    echo "CRITICAL: Replication lag ${lag}s (threshold: ${LAG_THRESHOLD_CRIT}s)"
    exit 2
elif [[ "$lag" -gt "$LAG_THRESHOLD_WARN" ]]; then
    echo "WARNING: Replication lag ${lag}s (threshold: ${LAG_THRESHOLD_WARN}s)"
    exit 1
else
    echo "OK: Replication healthy, lag ${lag}s"
    exit 0
fi
```

---

## pg_activity e Monitoraggio Real-Time

```bash
# pg_activity: htop-like per PostgreSQL
pip install pg_activity
pg_activity -h localhost -p 5432 -U postgres -d mydb

# pgBadger: analisi log PostgreSQL per identificare query lente
pgbadger /var/log/postgresql/postgresql-*.log \
    --outfile report.html \
    --format html \
    --sample 3
```

Il monitoraggio della replica non è un'attività occasionale — è una serie di alert e dashboard sempre attivi. Un lag di replica che cresce silenziosamente può portare a failover con perdita di dati se non viene rilevato e gestito in tempo.
