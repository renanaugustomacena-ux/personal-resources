# MySQL/MariaDB Security

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
1. User Management e Authentication
2. Password Policies
3. Data Encryption
4. SSL/TLS Configuration
5. Audit e Monitoring
6. SQL Injection Prevention
7. Network Security
8. Compliance

---

## 1. User Management e Authentication

### 1.1 Creating Users Securely

```sql
-- Create user with strong password
CREATE USER 'app_user'@'localhost' 
IDENTIFIED BY 'StrongP@ssw0rd!123';

-- Create with specific host
CREATE USER 'app_user'@'192.168.1.%' 
IDENTIFIED BY 'StrongP@ssw0rd!123';

-- Allow from any host
CREATE USER 'app_user'@'%' 
IDENTIFIED BY 'StrongP@ssw0rd!123';
```

### 1.2 Granting Privileges

```sql
-- Minimal privileges for application
GRANT SELECT, INSERT, UPDATE, DELETE ON mydb.* 
TO 'app_user'@'localhost';

-- Read-only user
GRANT SELECT ON mydb.* TO 'readonly'@'%';

-- Backup user
GRANT SELECT, LOCK TABLES, EVENT, TRIGGER 
ON mydb.* TO 'backup'@'localhost';

-- Admin user
GRANT ALL PRIVILEGES ON mydb.* 
TO 'admin'@'localhost' 
WITH GRANT OPTION;
```

### 1.3 Resource Limits

```sql
-- Create with resource limits
CREATE USER 'limited_user'@'%' 
IDENTIFIED BY 'password'
WITH MAX_QUERIES_PER_HOUR 100
       MAX_UPDATES_PER_HOUR 50
       MAX_CONNECTIONS_PER_HOUR 10
       MAX_USER_CONNECTIONS 5;
```

### 1.4 Roles (MySQL 8.0+)

```sql
-- Create roles
CREATE ROLE 'app_readonly';
CREATE ROLE 'app_write';
CREATE ROLE 'app_admin';

-- Grant privileges to roles
GRANT SELECT ON mydb.* TO 'app_readonly';
GRANT SELECT, INSERT, UPDATE, DELETE ON mydb.* TO 'app_write';
GRANT ALL ON mydb.* TO 'app_admin';

-- Assign roles to users
GRANT 'app_readonly' TO 'user1'@'%';
GRANT 'app_write' TO 'user2'@'%';
GRANT 'app_admin' TO 'admin'@'%';

-- Set default role
SET DEFAULT ROLE 'app_readonly' FOR 'user1'@'%';
```

### 1.5 Password Requirements

```sql
-- Require password
ALTER USER 'user'@'localhost' REQUIRE SSL;

-- Lock account after failed attempts
ALTER USER 'user'@'localhost' 
FAILED_LOGIN_ATTEMPTS 3 PASSWORD_LOCK_TIME 3;
```

---

## 2. Password Policies

### 2.1 Password Validation Plugin

```sql
-- Install validate_password
INSTALL PLUGIN validate_password SONAME 'validate_password.so';

-- Verify installation
SHOW PLUGINS LIKE 'validate_password';

-- Configure policies
SET GLOBAL validate_password_length = 12;
SET GLOBAL validate_password_mixed_case_count = 1;
SET GLOBAL validate_password_special_char_count = 1;
SET GLOBAL validate_password_number_count = 1;
SET GLOBAL validate_password_policy = MEDIUM;

-- Policies: 0=LOW, 1=MEDIUM, 2=STRONG
```

### 2.2 Password Expiration

```sql
-- Force password expiration
ALTER USER 'user'@'localhost' PASSWORD EXPIRE;

-- Set password expire after 90 days
ALTER USER 'user'@'localhost' 
PASSWORD EXPIRE INTERVAL 90 DAY;

-- Check password expiration
SELECT user, host, password_lifetime, password_last_changed
FROM mysql.user 
WHERE password_lifetime IS NOT NULL;
```

### 2.3 Password Reuse

```sql
-- Prevent password reuse
SET GLOBAL password_history = 5;

-- Check password history for user
ALTER USER 'user'@'localhost' 
PASSWORD HISTORY 5;
```

---

## 3. Data Encryption

### 3.1 InnoDB Tablespace Encryption

```sql
-- Create encrypted tablespace
CREATE TABLESPACE ts1 ENCRYPTION = 'Y';

-- Create table in encrypted tablespace
CREATE TABLE sensitive_data (
    id INT,
    data VARCHAR(255)
) TABLESPACE ts1;

-- Enable general tablespace encryption
SET GLOBAL innodb_encrypt_tables = ON;

-- Key rotation
ALTER TABLESPACE ts1 ENCRYPTION = 'Y' KEY_NAME = 'key_2';
```

### 3.2 Column Encryption

```sql
-- MariaDB column encryption
CREATE TABLE secrets (
    id INT PRIMARY KEY,
    data VARBINARY(256)
);

-- Encrypt data
INSERT INTO secrets (id, data) VALUES 
(1, AES_ENCRYPT('secret_data', 'encryption_key_here'));

-- Decrypt data
SELECT id, AES_DECRYPT(data, 'encryption_key_here') 
AS decrypted_data FROM secrets;
```

### 3.3 Key Management

```sql
-- Key file configuration
[mysqld]
innodb_encryption_rotate_key_age = 1
innodb_encryption_threads = 4

-- Key rotation schedule
SET GLOBAL innodb_encryption_rotate_key_age = 1;
```

---

## 4. SSL/TLS Configuration

### 4.1 Server Configuration

```ini
# my.cnf

[mysqld]
ssl_ca = /etc/mysql/ssl/ca.pem
ssl_cert = /etc/mysql/ssl/server-cert.pem
ssl_key = /etc/mysql/ssl/server-key.pem
ssl_ciphers = 'HIGH:!aNULL:!MD5'
require_secure_transport = ON
```

### 4.2 Generate SSL Certificates

```bash
# Create CA
openssl genrsa 2048 > ca-key.pem
openssl req -new -x509 -nodes -days 3650 \
  -key ca-key.pem > ca-cert.pem

# Create server key and CSR
openssl genrsa 2048 > server-key.pem
openssl req -new -key server-key.pem \
  -out server.csr

# Sign server certificate
openssl x509 -req -days 3650 \
  -in server.csr -CA ca-cert.pem \
  -CAkey ca-key.pem -CAcreateserial \
  > server-cert.pem

# Create client certificate similarly
```

### 4.3 Connect with SSL

```bash
# Client connection with SSL
mysql -u user -p \
  --ssl-ca=ca.pem \
  --ssl-cert=client-cert.pem \
  --ssl-key=client-key.pem

# Verify SSL connection
mysql -u user -p -e "SHOW STATUS LIKE 'ssl_version';"
```

---

## 5. Audit e Monitoring

### 5.1 MySQL Enterprise Audit

```sql
-- Install audit plugin
INSTALL PLUGIN audit_log SONAME 'audit_log.so';

-- Configure
SET GLOBAL audit_log_policy = 'ALL';
SET GLOBAL audit_log_format = 'JSON';
SET GLOBAL audit_log = '/var/log/mysql/audit.log';
SET GLOBAL audit_log_flush = ON;

-- Filter events
SET GLOBAL audit_log_events = 'CONNECT,QUERY,TABLE';
```

### 5.2 MariaDB Audit

```ini
# MariaDB
plugin_load_add = server_audit
server_audit_logging = ON
server_audit_events = CONNECT,QUERY,TABLE
server_audit_output_type = file
server_audit_file_path = /var/log/mysql/audit.log
server_audit_file_rotate_size = 100000000
server_audit_file_rotations = 10
```

### 5.3 General Log Security

```sql
-- Disable general query log in production
SET GLOBAL general_log = 'OFF';

-- If needed, log to table with limited access
SET GLOBAL general_log = 'ON';
SET GLOBAL log_output = 'TABLE';
SET GLOBAL general_log = 'mysql.general_log';

-- Restrict access to log table
REVOKE ALL ON mysql.general_log FROM 'app_user'@'%';
```

---

## 6. SQL Injection Prevention

### 6.1 Prepared Statements

```python
# Python - parameterized queries
import mysql.connector

conn = mysql.connector.connect(...)
cursor = conn.cursor(prepared=True)

stmt = "SELECT * FROM users WHERE id = ?"
cursor.execute(stmt, (user_id,))

# Multiple queries
stmt = "SELECT * FROM users WHERE name = ? AND status = ?"
cursor.execute(stmt, (name, status))
```

```php
// PHP PDO prepared statements
$pdo = new PDO($dsn, $user, $pass);

$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id");
$stmt->execute(['id' => $user_id]);

$stmt = $pdo->prepare("SELECT * FROM users WHERE name = :name");
$stmt->execute(['name' => $name]);
```

### 6.2 Input Validation

```sql
-- Validate types in stored procedures
DELIMITER //
CREATE PROCEDURE get_user(IN user_id_param INT)
BEGIN
    SET @user_id = user_id_param;
    PREPARE stmt FROM 'SELECT * FROM users WHERE id = ?';
    EXECUTE stmt USING @user_id;
    DEALLOCATE PREPARE stmt;
END //
DELIMITER ;
```

### 6.3 ORM Usage

```python
# SQLAlchemy - automatic escaping
from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://user:pass@host/db")
with engine.connect() as conn:
    # Parameters automatically escaped
    result = conn.execute(
        text("SELECT * FROM users WHERE id = :id"),
        {"id": user_id}
    )
```

### 6.4 Web Application Patterns

```python
# Flask with parameterized queries
@app.route('/user/<int:user_id>')
def get_user(user_id):
    # user_id automatically validated as integer
    cursor.execute(
        "SELECT * FROM users WHERE id = %s",
        (user_id,)
    )
    return jsonify(cursor.fetchone())
```

---

## 7. Network Security

### 7.1 Bind Address

```ini
# my.cnf - listen on specific interface
bind-address = 127.0.0.1

# Or specific IP
bind-address = 192.168.1.100
```

### 7.2 Firewall Configuration

```bash
# UFW
ufw allow from 10.0.0.0/8 to any port 3306 proto tcp

# iptables
iptables -A INPUT -p tcp -s 10.0.0.0/8 --dport 3306 -j ACCEPT
iptables -A INPUT -p tcp --dport 3306 -j DROP
```

### 7.3 Connection Restrictions

```sql
-- Only local connections
CREATE USER 'local_app'@'localhost' IDENTIFIED BY 'pass';

-- Only specific IP range
CREATE USER 'app'@'192.168.1.%' IDENTIFIED BY 'pass';

-- No remote root
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1');
```

---

## 8. Compliance

### 8.1 GDPR Considerations

```sql
-- Audit access to personal data
-- Implement in application logic

-- Data retention policies
CREATE EVENT cleanup_old_data
ON SCHEDULE EVERY 1 DAY
DO
    DELETE FROM logs WHERE created_at < NOW() - INTERVAL 90 DAY;
```

### 8.2 Security Best Practices Checklist

- [ ] Strong passwords with validation
- [ ] SSL/TLS for all connections
- [ ] Minimal privilege grants
- [ ] Prepared statements for all queries
- [ ] Regular security updates
- [ ] Audit logging enabled
- [ ] Network restrictions
- [ ] Encryption at rest
- [ ] Regular password rotation
- [ ] Monitor failed login attempts

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*

---

*Questo documento fa parte del modulo 03 "MySQL/MariaDB" della Data Encyclopedia.*