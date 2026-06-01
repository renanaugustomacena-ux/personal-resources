# MySQL/MariaDB Performance Tuning

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
1. Configuration Basics
2. InnoDB Tuning Deep Dive
3. Query Tuning
4. Connection Management
5. Monitoring e Profiling
6. Memory Tuning
7. I/O Optimization

---

## 1. Configuration Basics

### 1.1 Key Variables

```sql
-- Most important for InnoDB
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
SHOW VARIABLES LIKE 'innodb_log_file_size';
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';
SHOW VARIABLES LIKE 'max_connections';
```

### 1.2 Recommended Values

```ini
# Production my.cnf

[mysqld]
# Buffer pool - 70% RAM
innodb_buffer_pool_size = 24G

# Log files - 1GB total
innodb_log_file_size = 1G

# Durability - 1 = safest
innodb_flush_log_at_trx_commit = 1
sync_binlog = 1

# Connections
max_connections = 500

# Query cache (MariaDB only, deprecated in MySQL)
query_cache_type = 1
query_cache_size = 64M
```

---

## 2. InnoDB Tuning Deep Dive

### 2.1 Buffer Pool Configuration

The buffer pool is the most critical configuration for InnoDB performance.

```sql
-- Set buffer pool size (70% RAM for dedicated server)
SET GLOBAL innodb_buffer_pool_size = 24159191040;  # 24GB

-- Buffer pool instances (reduce contention)
SET GLOBAL innodb_buffer_pool_instances = 8;

-- Buffer pool preload at startup
innodb_buffer_pool_load = ON
innodb_buffer_pool_load_at_startup = ON
```

**Sizing guidelines**:
- Dedicated MySQL server: 70-80% RAM
- Shared server: 50% RAM
- Minimum: 1GB (for small databases)

### 2.2 Log Configuration

```sql
-- Log file size (1GB recommended)
SET GLOBAL innodb_log_file_size = 1073741824;

-- Flush method
SET GLOBAL innodb_flush_method = 'O_DIRECT';

-- Adaptive checkpoint
SET GLOBAL innodb_adaptive_flushing = ON;
SET GLOBAL innodb_flush_neighbors = 1;
```

### 2.3 Thread Configuration

```sql
-- Page cleaner threads
SET GLOBAL innodb_page_cleaners = 4;

-- Purge threads
SET GLOBAL innodb_purge_threads = 4;

-- IO threads
SET GLOBAL innodb_read_io_threads = 16;
SET GLOBAL innodb_write_io_threads = 16;
```

---

## 3. Query Tuning

### 3.1 Slow Query Log Configuration

```sql
-- Enable slow query log
SET GLOBAL slow_query_log = ON;
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';
SET GLOBAL long_query_time = 1;

-- Enable logging of queries not using indexes
SET GLOBAL log_queries_not_using_indexes = ON;

-- Slow log extra info
SET GLOBAL log_slow_verbosity = 'explain';
```

### 3.2 Query Profiling

```sql
-- Enable profiling
SET profiling = ON;

-- Run query
SELECT COUNT(*) FROM orders WHERE status = 'pending';

-- Show all profiles
SHOW PROFILES;

-- Show details for specific query
SHOW PROFILE FOR QUERY 1;
SHOW PROFILE CPU FOR QUERY 1;
```

### 3.3 EXPLAIN Analysis

```sql
-- Analyze query plan
EXPLAIN FORMAT=JSON 
SELECT * FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE c.region = 'West';

-- EXPLAIN ANALYZE (MySQL 8.0+)
EXPLAIN ANALYZE 
SELECT * FROM orders WHERE status = 'pending';
```

---

## 4. Connection Management

### 4.1 Connection Configuration

```sql
-- Max connections
SET GLOBAL max_connections = 500;

-- Connection timeout
SET GLOBAL wait_timeout = 600;
SET GLOBAL interactive_timeout = 600;

-- Connection errors (prevent brute force)
SHOW VARIABLES LIKE 'max_connect_errors';
SET GLOBAL max_connect_errors = 100;
```

### 4.2 Connection Pool (ProxySQL)

ProxySQL provides connection pooling and routing:

```ini
# /etc/proxysql.cnf

databases:
  - address: 10.0.0.1
    port: 3306
    name: mydb

users:
  - username: app
    password: secret

query_rules:
  - rule_id: 1
    destination_hostgroup: 10
    match_pattern: "^SELECT.*FOR UPDATE"
    apply: 1
```

---

## 5. Monitoring e Profiling

### 5.1 Status Variables

```sql
-- Connection status
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Threads_running';
SHOW STATUS LIKE 'Max_used_connections';
SHOW STATUS LIKE 'Aborted_connects';

-- Query statistics
SHOW STATUS LIKE 'Questions';
SHOW STATUS LIKE 'Slow_queries';
SHOW STATUS LIKE 'Com_select';
SHOW STATUS LIKE 'Com_insert';
SHOW STATUS LIKE 'Com_update';
SHOW STATUS LIKE 'Com_delete';

-- InnoDB stats
SHOW ENGINE INNODB STATUS;
SHOW ENGINE INNODB MUTEX;
```

### 5.2 Performance Schema

```sql
-- Enable instrument
UPDATE performance_schema.setup_instruments 
SET ENABLED = 'YES' WHERE NAME LIKE 'statement%';

-- Top queries by time
SELECT * FROM events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC LIMIT 10;

-- Top queries by rows sent
SELECT * FROM events_statements_summary_by_digest
ORDER BY SUM_ROWS_SENT DESC LIMIT 10;

-- Long queries
SELECT * FROM events_statements_history_long
WHERE TIMESTADDIF(SECOND, TIMESTARTCOLLECT, NOW()) > 10;
```

---

## 6. Memory Tuning

### 6.1 Memory Allocation

```sql
-- Sort buffer
SET GLOBAL sort_buffer_size = 262144;

-- Join buffer
SET GLOBAL join_buffer_size = 262144;

-- Read buffer
SET GLOBAL read_buffer_size = 131072;

-- tmp_table_size
SET GLOBAL tmp_table_size = 64M;
SET GLOBAL max_heap_table_size = 64M;
```

### 6.2 Query Cache (MariaDB)

```sql
-- Enable query cache
SET GLOBAL query_cache_type = 1;
SET GLOBAL query_cache_size = 64M;

-- Monitor cache usage
SHOW STATUS LIKE 'Qcache%';
```

---

## 7. I/O Optimization

### 7.1 I/O Configuration

```sql
-- Doublewrite buffer
SET GLOBAL innodb_doublewrite = 1;

-- Flush method
SET GLOBAL innodb_flush_method = 'O_DIRECT';

-- Log flush
SET GLOBAL innodb_flush_log_at_trx_commit = 2;

-- Flush neighbors
SET GLOBAL innodb_flush_neighbors = 0;
```

### 7.2 Table Space

```sql
-- File per table
SET GLOBAL innodb_file_per_table = ON;

-- Compression
SET GLOBAL innodb_compression_level = 6;

-- Page size
SET GLOBAL innodb_page_size = 16K;
```

---

## 8. Disk I/O Tuning

### 8.1 SSD Optimization

```sql
-- Disable doublewrite for SSD (optional, less safe)
SET GLOBAL innodb_doublewrite = 0;

-- Increase read ahead
SET GLOBAL innodb_random_read_ahead = ON;

-- Optimize for SSD
SET GLOBAL innodb_flush_neighbors = 0;
SET GLOBAL innodb_adaptive_flushing = ON;
```

### 8.2 Scheduler

```sql
-- Check IO scheduler
SELECT @@io_scheduler;

-- For Linux, use deadline or noop
```

---

## 9. Network Tuning

### 9.1 Connection Tuning

```sql
-- TCP settings
SET GLOBAL net_buffer_length = 16384;
SET GLOBAL max_allowed_packet = 64M;

-- Timeout settings
SET GLOBAL net_read_timeout = 30;
SET GLOBAL net_write_timeout = 60;
```

---

## 10. System Tuning

### 10.1 OS Settings

```bash
# /etc/sysctl.conf
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 5

# /etc/security/limits.conf
mysql soft nofile 65535
mysql hard nofile 65535
```

### 10.2 Performance Monitoring

```sql
-- Status overview
SHOW GLOBAL STATUS LIKE 'Uptime';
SHOW GLOBAL STATUS LIKE 'Questions';
SHOW GLOBAL STATUS LIKE 'Threads_connected';
SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*