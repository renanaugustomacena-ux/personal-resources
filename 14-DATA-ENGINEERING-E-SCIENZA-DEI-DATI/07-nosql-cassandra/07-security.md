# Cassandra: Security

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [x] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Authentication
2. Authorization
3. Role-Based Access Control
4. Encryption at Rest
5. Encryption in Transit
6. Network Security
7. Audit Logging
8. Cassandra 4.x/5.x Security Features
9. Security Hardening Checklist
10. Operational Security Procedures
11. Compliance Considerations
12. Troubleshooting
13. FAQ

---

## 1. Authentication

### 1.1 Enabling Authentication

By default, Cassandra ships with authentication disabled (`AllowAllAuthenticator`). This must be changed before any production deployment.

```yaml
# cassandra.yaml
# Default (INSECURE -- anyone can connect without credentials):
# authenticator: AllowAllAuthenticator

# Production: enable password-based authentication
authenticator: PasswordAuthenticator

# Cassandra 5.0+: pluggable authentication via MutualTlsAuthenticator
# authenticator: MutualTlsAuthenticator
```

### 1.2 Default Superuser

```sql
-- After enabling PasswordAuthenticator, Cassandra creates a default superuser:
-- Username: cassandra
-- Password: cassandra
-- This MUST be changed immediately.

-- Step 1: Connect with default credentials
-- cqlsh -u cassandra -p cassandra

-- Step 2: Create a new superuser
CREATE ROLE admin WITH PASSWORD = 'STRONG_RANDOM_PASSWORD_HERE'
  AND SUPERUSER = true
  AND LOGIN = true;

-- Step 3: Connect as the new superuser
-- cqlsh -u admin -p 'STRONG_RANDOM_PASSWORD_HERE'

-- Step 4: Disable the default superuser
ALTER ROLE cassandra WITH PASSWORD = 'RANDOM_UNGUESSABLE_STRING'
  AND SUPERUSER = false
  AND LOGIN = false;

-- Alternatively, drop it (cannot be undone):
-- DROP ROLE cassandra;
```

### 1.3 Creating Application Users

```sql
-- Create a role for an application (with LOGIN)
CREATE ROLE ecommerce_app WITH PASSWORD = 'app_secret_here'
  AND LOGIN = true
  AND SUPERUSER = false;

-- Create a role for read-only analytics
CREATE ROLE analytics_reader WITH PASSWORD = 'analytics_secret'
  AND LOGIN = true
  AND SUPERUSER = false;

-- Create a role for a developer (non-production access)
CREATE ROLE dev_user WITH PASSWORD = 'dev_password'
  AND LOGIN = true
  AND SUPERUSER = false;

-- List all roles
LIST ROLES;

-- Check role details
LIST ROLES OF ecommerce_app;
```

### 1.4 Password Policy

```yaml
# cassandra.yaml (Cassandra 4.1+)
# Password strength enforcement via the PasswordValidator
credentials_validity_in_ms: 2000      # cache duration for auth checks
credentials_update_interval_in_ms: 1000

# Custom password validator (set in cassandra.yaml):
# password_validator:
#   class_name: org.apache.cassandra.auth.CassandraPasswordValidator
#   parameters:
#     min_length: 12
#     require_uppercase: true
#     require_lowercase: true
#     require_digit: true
#     require_special: true
```

### 1.5 LDAP and External Authentication

```yaml
# Cassandra does not natively support LDAP, but options exist:

# Option 1: DataStax Enterprise (DSE) includes LdapAuthenticator
# authenticator: com.datastax.bdp.cassandra.auth.LdapAuthenticator

# Option 2: Custom authenticator plugin
# authenticator: com.example.LdapCassandraAuthenticator

# Option 3: Mutual TLS authentication (Cassandra 5.0+)
# Map X.509 certificate CN/SAN to Cassandra roles
authenticator: MutualTlsAuthenticator
# Requires client certificates signed by a trusted CA
```

### 1.6 Credentials Caching

```yaml
# cassandra.yaml
# Authentication results are cached to avoid hitting system_auth on every request.
credentials_validity_in_ms: 2000          # cache TTL (default 2 seconds)
credentials_update_interval_in_ms: 1000   # background refresh interval

# For high-throughput clusters, increase caching to reduce auth overhead:
credentials_validity_in_ms: 10000
credentials_update_interval_in_ms: 5000

# TRADE-OFF: longer cache = faster auth but delayed password changes.
# After changing a password, the old one works until the cache expires.
```

---

## 2. Authorization

### 2.1 Enabling Authorization

```yaml
# cassandra.yaml
# Default (INSECURE -- everyone has full access):
# authorizer: AllowAllAuthorizer

# Production: enable Cassandra's built-in authorizer
authorizer: CassandraAuthorizer

# Must be used together with PasswordAuthenticator (or another authenticator).
# AllowAllAuthenticator + CassandraAuthorizer is a misconfiguration.
```

### 2.2 Permission Types

| Permission | Applies To | Description |
|------------|-----------|-------------|
| `ALL` | All resources | Grants all permissions |
| `ALTER` | Keyspace, Table, Function | Modify schema |
| `AUTHORIZE` | All resources | Grant/revoke permissions to others |
| `CREATE` | Keyspace, Table, Function, Index | Create new resources |
| `DESCRIBE` | All resources | Describe schema (4.1+) |
| `DROP` | Keyspace, Table, Function, Index | Delete resources |
| `EXECUTE` | Function | Execute user-defined functions |
| `MODIFY` | Keyspace, Table | INSERT, UPDATE, DELETE |
| `SELECT` | Keyspace, Table | Read data |

### 2.3 Granting and Revoking Permissions

```sql
-- Grant SELECT on a specific table
GRANT SELECT ON ecommerce.orders TO analytics_reader;

-- Grant SELECT on all tables in a keyspace
GRANT SELECT ON KEYSPACE ecommerce TO analytics_reader;

-- Grant read and write on a table
GRANT SELECT, MODIFY ON ecommerce.orders TO ecommerce_app;

-- Grant full access to a keyspace
GRANT ALL ON KEYSPACE ecommerce TO ecommerce_app;

-- Grant on all keyspaces (dangerous; use sparingly)
GRANT SELECT ON ALL KEYSPACES TO analytics_reader;

-- Revoke permissions
REVOKE MODIFY ON ecommerce.orders FROM analytics_reader;

-- List permissions for a role
LIST ALL PERMISSIONS OF analytics_reader;

-- List permissions on a resource
LIST ALL PERMISSIONS ON ecommerce.orders;
```

### 2.4 Permission Caching

```yaml
# cassandra.yaml
permissions_validity_in_ms: 2000          # cache TTL
permissions_update_interval_in_ms: 1000   # background refresh

# Increase for large clusters with many roles:
permissions_validity_in_ms: 10000
permissions_update_interval_in_ms: 5000

# TRADE-OFF: longer cache = faster permission checks but delayed
# permission changes. After GRANT/REVOKE, wait for cache expiry.
```

---

## 3. Role-Based Access Control

### 3.1 Role Hierarchy

Cassandra supports role inheritance. A role can be granted to another role, forming a hierarchy.

```sql
-- Create base roles (no login, used for grouping permissions)
CREATE ROLE data_reader WITH LOGIN = false;
CREATE ROLE data_writer WITH LOGIN = false;
CREATE ROLE schema_admin WITH LOGIN = false;

-- Assign permissions to base roles
GRANT SELECT ON ALL KEYSPACES TO data_reader;
GRANT MODIFY ON ALL KEYSPACES TO data_writer;
GRANT ALTER, CREATE, DROP ON ALL KEYSPACES TO schema_admin;

-- Create login roles that inherit from base roles
CREATE ROLE reporting_service WITH PASSWORD = 'secret1'
  AND LOGIN = true;
GRANT data_reader TO reporting_service;

CREATE ROLE api_service WITH PASSWORD = 'secret2'
  AND LOGIN = true;
GRANT data_reader TO api_service;
GRANT data_writer TO api_service;

CREATE ROLE dba_team WITH PASSWORD = 'secret3'
  AND LOGIN = true;
GRANT data_reader TO dba_team;
GRANT data_writer TO dba_team;
GRANT schema_admin TO dba_team;

-- Verify role hierarchy
LIST ROLES OF api_service;
-- Output:
-- role          | super | login | member_of
-- api_service   | False | True  | {data_reader, data_writer}
-- data_reader   | False | False | {}
-- data_writer   | False | False | {}
```

### 3.2 Principle of Least Privilege

```sql
-- CORRECT: narrow permissions per application
-- Each service gets only what it needs.

-- Order processing service: read/write orders, read products
GRANT SELECT, MODIFY ON ecommerce.orders TO order_service;
GRANT SELECT ON ecommerce.products TO order_service;

-- Recommendation engine: read-only access to user interactions
GRANT SELECT ON ecommerce.user_events TO recommendation_service;

-- WRONG: overly broad permissions
-- GRANT ALL ON ALL KEYSPACES TO app_service;
-- This gives the app superuser-like access. Never do this.
```

### 3.3 Service Account Best Practices

```sql
-- 1. One role per service/application
-- 2. Never share credentials between services
-- 3. Rotate passwords on a schedule
-- 4. Use descriptive role names that indicate purpose

-- Naming convention: <service>_<access_level>
CREATE ROLE payment_service_rw WITH PASSWORD = 'ROTATED_SECRET'
  AND LOGIN = true;
CREATE ROLE analytics_pipeline_ro WITH PASSWORD = 'ROTATED_SECRET'
  AND LOGIN = true;

-- 5. Review permissions periodically
LIST ALL PERMISSIONS;
```

---

## 4. Encryption at Rest

### 4.1 Transparent Data Encryption (TDE)

```yaml
# cassandra.yaml
# Cassandra supports encryption of SSTables, commitlog, and hints.
# Available in DataStax Enterprise (DSE) and via third-party plugins.

# Open-source Cassandra does NOT include TDE out of the box.
# Options for encryption at rest:

# Option 1: Filesystem-level encryption (recommended for open-source)
# Use LUKS (Linux) or dm-crypt:
# cryptsetup luksFormat /dev/sdb
# cryptsetup open /dev/sdb cassandra_data
# mkfs.xfs /dev/mapper/cassandra_data
# mount /dev/mapper/cassandra_data /data/cassandra

# Option 2: Cloud-provider managed encryption
# AWS EBS encryption, GCP Persistent Disk encryption, Azure Disk Encryption
# These are transparent to Cassandra and require no configuration changes.

# Option 3: DSE Transparent Data Encryption
# Encrypts SSTables, commitlog, and hints at the file level.
# transparent_data_encryption_options:
#   enabled: true
#   chunk_length_kb: 64
#   cipher: AES/CBC/PKCS5Padding
#   key_provider:
#     - class_name: com.datastax.bdp.cassandra.crypto.SystemKeyKeyProvider
#       parameters:
#         - secret_key_file: /etc/dse/conf/system_key
```

### 4.2 Commitlog and Hint Encryption (DSE)

```yaml
# DSE cassandra.yaml
# Encrypt commitlog
transparent_data_encryption_options:
  enabled: true
  cipher: AES/CBC/PKCS5Padding
  key_provider:
    - class_name: com.datastax.bdp.cassandra.crypto.SystemKeyKeyProvider

# Encrypt hints
# Hints inherit TDE settings when enabled.
```

---

## 5. Encryption in Transit

### 5.1 Client-to-Node Encryption

```yaml
# cassandra.yaml
client_encryption_options:
  enabled: true
  optional: false              # true = allow unencrypted connections too
  keystore: /etc/cassandra/conf/.keystore
  keystore_password: ${KEYSTORE_PASSWORD}   # use env var, never plaintext
  truststore: /etc/cassandra/conf/.truststore
  truststore_password: ${TRUSTSTORE_PASSWORD}
  protocol: TLSv1.3           # minimum TLS version
  cipher_suites:
    - TLS_AES_256_GCM_SHA384
    - TLS_AES_128_GCM_SHA256
    - TLS_CHACHA20_POLY1305_SHA256
  require_client_auth: false   # set true for mutual TLS
```

### 5.2 Node-to-Node Encryption

```yaml
# cassandra.yaml
server_encryption_options:
  internode_encryption: all     # Options: none, all, dc, rack
  # none:  no encryption (insecure)
  # all:   encrypt all internode traffic
  # dc:    encrypt only cross-DC traffic
  # rack:  encrypt only cross-rack traffic
  enable_legacy_ssl_storage_port: false
  keystore: /etc/cassandra/conf/.keystore
  keystore_password: ${KEYSTORE_PASSWORD}
  truststore: /etc/cassandra/conf/.truststore
  truststore_password: ${TRUSTSTORE_PASSWORD}
  protocol: TLSv1.3
  cipher_suites:
    - TLS_AES_256_GCM_SHA384
    - TLS_AES_128_GCM_SHA256
  require_client_auth: true    # mutual TLS between nodes (recommended)
  require_endpoint_verification: true  # verify hostname in cert (4.0+)
```

### 5.3 Generating Keystores and Truststores

```bash
# Step 1: Generate a CA key pair (do this once)
openssl req -new -x509 -days 3650 \
  -keyout ca-key.pem -out ca-cert.pem \
  -subj "/CN=CassandraCA/O=MyOrg" \
  -nodes

# Step 2: For EACH node, generate a key pair and sign it
NODE_IP="10.0.1.1"
NODE_HOSTNAME="cass-node-1"

# Generate node key pair
keytool -genkeypair -alias "$NODE_HOSTNAME" \
  -keyalg RSA -keysize 2048 \
  -dname "CN=$NODE_HOSTNAME, O=MyOrg" \
  -validity 3650 \
  -keystore "$NODE_HOSTNAME.keystore" \
  -storepass changeit \
  -keypass changeit \
  -ext "SAN=IP:$NODE_IP,DNS:$NODE_HOSTNAME"

# Generate CSR
keytool -certreq -alias "$NODE_HOSTNAME" \
  -keystore "$NODE_HOSTNAME.keystore" \
  -storepass changeit \
  -file "$NODE_HOSTNAME.csr" \
  -ext "SAN=IP:$NODE_IP,DNS:$NODE_HOSTNAME"

# Sign with CA
openssl x509 -req -in "$NODE_HOSTNAME.csr" \
  -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out "$NODE_HOSTNAME.crt" \
  -days 3650 \
  -extfile <(printf "subjectAltName=IP:$NODE_IP,DNS:$NODE_HOSTNAME")

# Import CA cert into keystore
keytool -importcert -alias ca -file ca-cert.pem \
  -keystore "$NODE_HOSTNAME.keystore" \
  -storepass changeit -noprompt

# Import signed cert into keystore
keytool -importcert -alias "$NODE_HOSTNAME" -file "$NODE_HOSTNAME.crt" \
  -keystore "$NODE_HOSTNAME.keystore" \
  -storepass changeit -noprompt

# Step 3: Create truststore with CA cert (same for all nodes)
keytool -importcert -alias ca -file ca-cert.pem \
  -keystore cassandra.truststore \
  -storepass changeit -noprompt

# Step 4: Deploy to each node
# Copy $NODE_HOSTNAME.keystore to /etc/cassandra/conf/.keystore
# Copy cassandra.truststore to /etc/cassandra/conf/.truststore
# Set permissions:
chmod 600 /etc/cassandra/conf/.keystore /etc/cassandra/conf/.truststore
chown cassandra:cassandra /etc/cassandra/conf/.keystore /etc/cassandra/conf/.truststore
```

### 5.4 PEM-Based TLS (Cassandra 5.0+)

```yaml
# Cassandra 5.0 supports PEM files directly (no more Java keystores)
client_encryption_options:
  enabled: true
  ssl_context_factory:
    class_name: org.apache.cassandra.security.PEMBasedSslContextFactory
    parameters:
      private_key: /etc/cassandra/certs/node-key.pem
      private_key_password: ${KEY_PASSWORD}
      certificate_chain: /etc/cassandra/certs/node-cert.pem
      trusted_certificates: /etc/cassandra/certs/ca-cert.pem
  protocol: TLSv1.3
  require_client_auth: false

server_encryption_options:
  internode_encryption: all
  ssl_context_factory:
    class_name: org.apache.cassandra.security.PEMBasedSslContextFactory
    parameters:
      private_key: /etc/cassandra/certs/node-key.pem
      private_key_password: ${KEY_PASSWORD}
      certificate_chain: /etc/cassandra/certs/node-cert.pem
      trusted_certificates: /etc/cassandra/certs/ca-cert.pem
  protocol: TLSv1.3
  require_client_auth: true
```

### 5.5 Client Driver TLS Configuration

```java
// Java driver (DataStax 4.x)
CqlSession session = CqlSession.builder()
    .addContactPoint(new InetSocketAddress("10.0.1.1", 9142))  // SSL port
    .withSslContext(SSLContext.getDefault())
    .withLocalDatacenter("us-east-1")
    .build();

// With custom truststore:
SSLContext sslContext = SSLContext.getInstance("TLSv1.3");
TrustManagerFactory tmf = TrustManagerFactory.getInstance("SunX509");
KeyStore ts = KeyStore.getInstance("JKS");
ts.load(new FileInputStream("/path/to/truststore"), "changeit".toCharArray());
tmf.init(ts);
sslContext.init(null, tmf.getTrustManagers(), null);

CqlSession session = CqlSession.builder()
    .addContactPoint(new InetSocketAddress("10.0.1.1", 9142))
    .withSslContext(sslContext)
    .build();
```

```python
# Python driver with TLS
from cassandra.cluster import Cluster
from ssl import SSLContext, PROTOCOL_TLS_CLIENT

ssl_context = SSLContext(PROTOCOL_TLS_CLIENT)
ssl_context.load_verify_locations('/path/to/ca-cert.pem')
# For mutual TLS:
# ssl_context.load_cert_chain('/path/to/client-cert.pem', '/path/to/client-key.pem')

cluster = Cluster(
    contact_points=['10.0.1.1'],
    port=9142,
    ssl_context=ssl_context
)
session = cluster.connect()
```

---

## 6. Network Security

### 6.1 Port Configuration

```yaml
# cassandra.yaml
# Native transport (CQL client connections)
native_transport_port: 9042          # plaintext
native_transport_port_ssl: 9142      # TLS

# Internode communication
storage_port: 7000                   # plaintext internode
ssl_storage_port: 7001               # TLS internode

# JMX monitoring
# cassandra-env.sh: JMX_PORT=7199

# Thrift (deprecated, remove if not needed)
# rpc_port: 9160
```

### 6.2 Listen and RPC Address

```yaml
# cassandra.yaml
# listen_address: IP other Cassandra nodes use to reach this node
listen_address: 10.0.1.1

# rpc_address: IP clients use to connect
rpc_address: 10.0.1.1
# Or bind to all interfaces (useful behind a load balancer):
# rpc_address: 0.0.0.0
# broadcast_rpc_address: 10.0.1.1  # what clients are told to connect to

# NEVER set listen_address to 0.0.0.0
# Cassandra uses listen_address for internode communication;
# binding to all interfaces causes ambiguity and gossip failures.
```

### 6.3 Firewall Rules

```bash
# iptables: allow only necessary ports from trusted sources

# Client connections (from application subnet)
iptables -A INPUT -p tcp --dport 9042 -s 10.1.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 9142 -s 10.1.0.0/16 -j ACCEPT  # TLS

# Internode communication (from other Cassandra nodes only)
iptables -A INPUT -p tcp --dport 7000 -s 10.0.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 7001 -s 10.0.1.0/24 -j ACCEPT  # TLS
iptables -A INPUT -p tcp --dport 7000 -s 10.0.2.0/24 -j ACCEPT  # remote DC
iptables -A INPUT -p tcp --dport 7001 -s 10.0.2.0/24 -j ACCEPT  # remote DC TLS

# JMX (from monitoring servers only)
iptables -A INPUT -p tcp --dport 7199 -s 10.3.0.10/32 -j ACCEPT
iptables -A INPUT -p tcp --dport 7199 -j DROP

# Prometheus JMX exporter (from Prometheus server only)
iptables -A INPUT -p tcp --dport 9500 -s 10.3.0.20/32 -j ACCEPT

# Drop everything else on Cassandra ports
iptables -A INPUT -p tcp --dport 9042 -j DROP
iptables -A INPUT -p tcp --dport 7000 -j DROP
iptables -A INPUT -p tcp --dport 7001 -j DROP
```

### 6.4 JMX Security

```bash
# cassandra-env.sh
# NEVER expose JMX to untrusted networks without authentication.

# Option 1: Local JMX only (most secure; use virtual tables for remote)
LOCAL_JMX=yes

# Option 2: Remote JMX with authentication
LOCAL_JMX=no
# Create JMX password file:
# /etc/cassandra/jmxremote.password
# monitorRole  readonly_password
# controlRole  readwrite_password
chmod 400 /etc/cassandra/jmxremote.password
chown cassandra:cassandra /etc/cassandra/jmxremote.password

# /etc/cassandra/jmxremote.access
# monitorRole  readonly
# controlRole  readwrite
chmod 400 /etc/cassandra/jmxremote.access

# Option 3: JMX over TLS
# Add to cassandra-env.sh:
# JVM_OPTS="$JVM_OPTS -Dcom.sun.management.jmxremote.ssl=true"
# JVM_OPTS="$JVM_OPTS -Dcom.sun.management.jmxremote.ssl.need.client.auth=true"
# JVM_OPTS="$JVM_OPTS -Djavax.net.ssl.keyStore=/etc/cassandra/conf/.keystore"
# JVM_OPTS="$JVM_OPTS -Djavax.net.ssl.trustStore=/etc/cassandra/conf/.truststore"
```

---

## 7. Audit Logging

### 7.1 Cassandra 4.0 Audit Logging

```yaml
# cassandra.yaml
audit_logging_options:
  enabled: true
  logger:
    - class_name: BinAuditLogger       # binary format, efficient
    # - class_name: FileAuditLogger    # human-readable text logs
  audit_logs_dir: /var/log/cassandra/audit
  # Filter by keyspace
  included_keyspaces: ecommerce,user_data,financial
  excluded_keyspaces: system,system_schema,system_auth,system_distributed
  # Filter by category
  included_categories: QUERY,DML,DDL,DCL,AUTH
  # QUERY: SELECT statements
  # DML:   INSERT, UPDATE, DELETE
  # DDL:   CREATE, ALTER, DROP (schema changes)
  # DCL:   GRANT, REVOKE (permission changes)
  # AUTH:  LOGIN attempts (successful and failed)
  # PREPARE: prepared statement registration
  # ERROR:   failed queries
  # Filter by user
  # included_users: admin,ecommerce_app
  # excluded_users: monitoring_agent
  # Roll size
  roll_cycle: HOURLY    # MINUTELY, HOURLY, DAILY
  max_queue_weight: 268435456         # 256 MB
  max_log_size: 17179869184           # 16 GB
```

### 7.2 Viewing Audit Logs

```bash
# Binary audit logs (BinAuditLogger)
auditlogviewer /var/log/cassandra/audit/

# Output format:
# Type: QUERY | User: ecommerce_app | Timestamp: 1716393600000
# Source: 10.1.0.50 | Keyspace: ecommerce | Scope: orders
# Operation: SELECT * FROM ecommerce.orders WHERE order_id = ?

# Text audit logs (FileAuditLogger)
tail -f /var/log/cassandra/audit/audit.log

# Search for specific user activity
auditlogviewer /var/log/cassandra/audit/ | grep "User: admin"

# Search for DDL changes
auditlogviewer /var/log/cassandra/audit/ | grep "Type: DDL"

# Search for failed auth attempts
auditlogviewer /var/log/cassandra/audit/ | grep "Type: AUTH" | grep -i "fail"
```

### 7.3 Full Query Logging (FQL)

```bash
# Enable full query logging at runtime (no restart needed)
nodetool enablefullquerylog --path /var/log/cassandra/fql/

# Disable FQL
nodetool disablefullquerylog

# View FQL logs
fqltool dump /var/log/cassandra/fql/

# Replay FQL logs against a test cluster (load testing)
fqltool replay --target 10.0.1.100 /var/log/cassandra/fql/

# Compare FQL results between clusters (verify migration)
fqltool compare --target 10.0.1.100 --target 10.0.2.100 /var/log/cassandra/fql/
```

---

## 8. Cassandra 4.x/5.x Security Features

### 8.1 Cassandra 4.0

- **Audit logging**: built-in query auditing without third-party tools.
- **Full Query Logging (FQL)**: capture and replay every query.
- **`require_endpoint_verification`**: verify hostnames in TLS certificates (prevents MITM via cert misuse).
- **Internode messaging v4**: encrypted single-connection multiplexing.
- **Diagnostic events**: monitor auth events via JMX subscriptions.

### 8.2 Cassandra 4.1

- **Guardrails framework**: prevent dangerous queries and configurations.
- **CIDR-based authorization** (pluggable): restrict connections by source IP.
- **Password validator**: enforce password complexity requirements.
- **`DESCRIBE` permission**: separate permission for viewing schema (previously anyone with SELECT could describe).

```yaml
# cassandra.yaml (4.1+)
# Guardrails act as security controls too:
guardrails:
  # Prevent ALLOW FILTERING in production
  allow_filtering_enabled: false
  # Limit IN clause size (prevents denial-of-service queries)
  in_select_cartesian_product_warn_threshold: 25
  in_select_cartesian_product_fail_threshold: 100
  # Limit page size
  page_size_warn_threshold: 5000
  page_size_fail_threshold: 10000
```

### 8.3 Cassandra 5.0

- **Mutual TLS authenticator**: `MutualTlsAuthenticator` maps client certificate identities to Cassandra roles. No passwords needed.
- **PEM-based TLS**: use PEM files directly instead of Java keystores.
- **Transactional Cluster Metadata (TCM)**: schema and topology changes go through Raft consensus, preventing unauthorized metadata corruption.
- **CIDR-based authorization** (built-in): restrict which IPs can use which roles.

```yaml
# Cassandra 5.0: Mutual TLS authentication
authenticator: MutualTlsAuthenticator
# Client must present a valid certificate.
# The CN or SAN from the certificate is mapped to a Cassandra role.

# Role mapping:
# If cert CN = "ecommerce-service", it maps to role "ecommerce-service"
# The role must exist in Cassandra:
# CREATE ROLE 'ecommerce-service' WITH LOGIN = true;
```

```sql
-- Cassandra 5.0: CIDR-based authorization
-- Restrict a role to specific source IP ranges
CREATE ROLE restricted_app WITH PASSWORD = 'secret'
  AND LOGIN = true
  AND ACCESS FROM CIDRS {'10.1.0.0/16', '10.2.0.0/16'};

-- Connections from outside these CIDRs are rejected even with valid credentials.
```

---

## 9. Security Hardening Checklist

### 9.1 Pre-Production Checklist

```
Authentication:
- [ ] PasswordAuthenticator enabled (not AllowAllAuthenticator)
- [ ] Default cassandra/cassandra superuser disabled or deleted
- [ ] New superuser created with strong password
- [ ] Application-specific roles created with least privilege
- [ ] Password complexity policy enforced (4.1+)

Authorization:
- [ ] CassandraAuthorizer enabled (not AllowAllAuthorizer)
- [ ] Per-service roles with minimal permissions
- [ ] No application role has SUPERUSER
- [ ] system_auth keyspace replicated to all DCs with adequate RF

Encryption in Transit:
- [ ] Client-to-node TLS enabled (port 9142)
- [ ] Node-to-node TLS enabled (internode_encryption: all or dc)
- [ ] TLS 1.3 enforced (no TLS 1.0/1.1/1.2)
- [ ] Strong cipher suites only
- [ ] require_endpoint_verification: true
- [ ] Certificates signed by internal CA (not self-signed in production)

Encryption at Rest:
- [ ] Disk-level encryption (LUKS, cloud-provider encryption)
- [ ] Or DSE TDE enabled

Network:
- [ ] Firewall rules restrict port 9042/9142 to application subnets
- [ ] Firewall rules restrict port 7000/7001 to Cassandra node IPs
- [ ] JMX restricted to localhost or monitoring IPs with auth
- [ ] listen_address is a private IP (not 0.0.0.0)
- [ ] Thrift disabled (start_rpc: false)

Audit:
- [ ] Audit logging enabled for DML, DDL, AUTH
- [ ] Audit logs stored on separate partition (prevent disk fill DoS)
- [ ] Audit log retention policy defined

JVM:
- [ ] JMX authentication enabled
- [ ] Remote code loading disabled
- [ ] JVM attach disabled in production
```

### 9.2 OS-Level Hardening

```bash
# Run Cassandra as a dedicated non-root user
useradd -r -s /sbin/nologin cassandra

# Restrict data directory permissions
chmod 750 /data/cassandra
chown -R cassandra:cassandra /data/cassandra

# Restrict config file permissions (contains keystore passwords)
chmod 600 /etc/cassandra/cassandra.yaml
chmod 600 /etc/cassandra/conf/.keystore
chmod 600 /etc/cassandra/conf/.truststore
chown -R cassandra:cassandra /etc/cassandra/

# Disable core dumps (may contain sensitive data)
echo "cassandra hard core 0" >> /etc/security/limits.conf

# Set file descriptor limits (Cassandra needs many open files)
echo "cassandra soft nofile 65536" >> /etc/security/limits.conf
echo "cassandra hard nofile 65536" >> /etc/security/limits.conf

# Disable swap (Cassandra should never swap; it causes severe latency)
swapoff -a
# Or set vm.swappiness = 1
echo "vm.swappiness = 1" >> /etc/sysctl.conf
sysctl -p
```

---

## 10. Operational Security Procedures

### 10.1 Password Rotation

```sql
-- Rotate application role passwords
ALTER ROLE ecommerce_app WITH PASSWORD = 'NEW_STRONG_PASSWORD';

-- IMPORTANT: update the application configuration to use the new password
-- BEFORE the credentials cache expires (default 2 seconds).
-- For zero-downtime rotation:
-- 1. Create a new role with the same permissions
-- 2. Update the application to use the new role
-- 3. Verify the application works with the new role
-- 4. Drop the old role
```

### 10.2 Certificate Rotation

```bash
# Step 1: Generate new certificates signed by the same CA (or new CA)
# Step 2: Add the new CA cert to all truststores
# Step 3: Rolling restart with new keystore containing new cert
# Step 4: After all nodes have the new cert, remove old CA from truststores
# Step 5: Rolling restart to apply new truststores

# For zero-downtime cert rotation:
# - Add new CA to truststore BEFORE switching keystores
# - Both old and new certs are trusted simultaneously during rollover
# - After all nodes have new certs, remove old CA
```

### 10.3 Security Incident Response

```bash
# If a credential is compromised:

# 1. Immediately change the password
cqlsh -u admin -e "ALTER ROLE compromised_role WITH PASSWORD = 'NEW_RANDOM';"

# 2. Check audit logs for unauthorized access
auditlogviewer /var/log/cassandra/audit/ | grep "User: compromised_role"

# 3. Check for data exfiltration (large SELECT queries)
auditlogviewer /var/log/cassandra/audit/ \
  | grep "User: compromised_role" \
  | grep "Type: QUERY"

# 4. Check for schema modifications
auditlogviewer /var/log/cassandra/audit/ \
  | grep "User: compromised_role" \
  | grep "Type: DDL"

# 5. If the superuser was compromised:
#    - Change ALL role passwords
#    - Rotate ALL certificates
#    - Review all schema changes since compromise
#    - Consider restoring from a pre-compromise backup
```

---

## 11. Compliance Considerations

### 11.1 GDPR / Data Privacy

```sql
-- Right to deletion: use TTL or explicit DELETE
DELETE FROM users WHERE user_id = 'user_to_delete';

-- Right to access: provide a query path for user data export
SELECT * FROM user_data WHERE user_id = 'requesting_user';

-- Data minimization: collect only necessary fields
-- Use TTL to auto-expire data after retention period

-- Encryption: enable TLS in transit and encryption at rest
-- Audit: enable audit logging for all DML on personal data keyspaces
```

### 11.2 PCI DSS

```yaml
# PCI DSS requirements for Cassandra:

# Req 2: Change default passwords
# - Done: default cassandra/cassandra changed (Section 1.2)

# Req 3: Protect stored cardholder data
# - Encryption at rest (LUKS or cloud encryption)
# - Never store full PAN in Cassandra (mask or tokenize)

# Req 4: Encrypt transmission of cardholder data
# - TLS 1.3 for client and internode traffic

# Req 7: Restrict access by business need
# - Role-based access control (Section 3)
# - Principle of least privilege

# Req 8: Identify and authenticate access
# - PasswordAuthenticator or MutualTlsAuthenticator
# - Unique role per service

# Req 10: Track and monitor all access
# - Audit logging enabled (Section 7)
# - Log retention per PCI requirements (1 year, 3 months readily available)

# Req 11: Regularly test security
# - Periodic permission reviews
# - Certificate expiry monitoring
```

### 11.3 SOC 2

```
SOC 2 controls relevant to Cassandra:

CC6.1 - Logical and physical access:
  - Authentication and authorization enabled
  - Role-based access with least privilege
  - JMX restricted to authorized personnel

CC6.3 - Encryption of data:
  - TLS in transit (client + internode)
  - Encryption at rest (disk-level or TDE)

CC7.2 - Monitoring:
  - Audit logging enabled
  - Alerting on failed auth attempts
  - Alerting on permission changes (DDL/DCL)

CC8.1 - Change management:
  - Schema changes audited (DDL logging)
  - Configuration changes tracked (version control cassandra.yaml)
```

---

## 12. Troubleshooting

### 12.1 Authentication Failed After Enabling PasswordAuthenticator

**Symptom**: `AuthenticationException: Unable to perform authentication`

**Fix**:
```bash
# Ensure system_auth keyspace has sufficient replicas
cqlsh -u cassandra -p cassandra -e "
  SELECT * FROM system_schema.keyspaces WHERE keyspace_name = 'system_auth';
"
# If RF=1 and that node is down, auth fails for everyone.

# Fix: increase RF
cqlsh -u cassandra -p cassandra -e "
  ALTER KEYSPACE system_auth
  WITH REPLICATION = {'class': 'NetworkTopologyStrategy', 'us-east-1': 3};
"
nodetool repair -full system_auth
```

### 12.2 Permission Denied Despite GRANT

**Symptom**: `UnauthorizedException` even after granting permissions.

**Fix**:
```bash
# Permissions are cached. Wait for cache expiry:
# Default: permissions_validity_in_ms = 2000 (2 seconds)

# Or flush the cache:
nodetool invalidatepermissionscache

# Verify the grant took effect:
cqlsh -u admin -e "LIST ALL PERMISSIONS OF ecommerce_app;"
```

### 12.3 TLS Handshake Failure

**Symptom**: `SSLHandshakeException` when connecting.

**Fix**:
```bash
# Check certificate validity
keytool -list -keystore /etc/cassandra/conf/.keystore -storepass changeit

# Check if CA cert is in truststore
keytool -list -keystore /etc/cassandra/conf/.truststore -storepass changeit

# Check TLS version compatibility
# Ensure client and server both support the configured protocol (TLS 1.3)

# Check cipher suite compatibility
# Client must support at least one cipher listed in cassandra.yaml

# Test connectivity with openssl
openssl s_client -connect 10.0.1.1:9142 -tls1_3

# Check for expired certificates
keytool -list -v -keystore /etc/cassandra/conf/.keystore -storepass changeit \
  | grep -A2 "Valid"
```

### 12.4 JMX Connection Refused

**Symptom**: `nodetool status` fails with connection refused.

**Fix**:
```bash
# Check if Cassandra is listening on JMX port
ss -tlnp | grep 7199

# Check LOCAL_JMX setting in cassandra-env.sh
grep LOCAL_JMX /etc/cassandra/cassandra-env.sh

# If LOCAL_JMX=yes, nodetool only works from localhost
# For remote access, set LOCAL_JMX=no and configure auth

# Cassandra 4.0+: use virtual tables instead of JMX for remote monitoring
cqlsh -e "SELECT * FROM system_views.settings;"
```

### 12.5 Audit Log Filling Disk

**Symptom**: audit log partition runs out of space.

**Fix**:
```yaml
# Limit audit log size
audit_logging_options:
  max_log_size: 5368709120            # 5 GB
  roll_cycle: HOURLY

# Set up log rotation
# /etc/logrotate.d/cassandra-audit:
# /var/log/cassandra/audit/*.log {
#   daily
#   rotate 30
#   compress
#   missingok
#   notifempty
# }
```

### 12.6 Cannot Login After Disabling Default Superuser

**Symptom**: locked out of the cluster after disabling the default cassandra role.

**Fix**:
```bash
# Emergency procedure:
# 1. Stop Cassandra on one node
systemctl stop cassandra

# 2. Temporarily disable authentication
# cassandra.yaml: authenticator: AllowAllAuthenticator

# 3. Start Cassandra
systemctl start cassandra

# 4. Create a new superuser
cqlsh -e "CREATE ROLE emergency_admin WITH PASSWORD = 'temp_password'
  AND SUPERUSER = true AND LOGIN = true;"

# 5. Re-enable PasswordAuthenticator
# cassandra.yaml: authenticator: PasswordAuthenticator

# 6. Restart Cassandra
systemctl restart cassandra

# 7. Login with emergency_admin and fix the issue
# 8. Delete emergency_admin after creating a proper superuser
```

### 12.7 Cross-DC Authentication Failure

**Symptom**: nodes in a remote DC cannot authenticate after system_auth replication change.

**Fix**:
```bash
# Ensure system_auth is replicated to all DCs
cqlsh -e "SELECT * FROM system_schema.keyspaces WHERE keyspace_name = 'system_auth';"

# If RF is missing for the remote DC, add it:
cqlsh -e "
  ALTER KEYSPACE system_auth WITH REPLICATION = {
    'class': 'NetworkTopologyStrategy',
    'us-east-1': 3,
    'eu-west-1': 3
  };
"
# Run repair on system_auth in the affected DC
nodetool repair -full system_auth
```

### 12.8 Performance Degradation After Enabling Encryption

**Symptom**: latency increases after enabling TLS.

**Fix**:
```yaml
# TLS adds CPU overhead. Mitigation:
# 1. Use TLS 1.3 (faster handshake than 1.2)
# 2. Use AES-NI capable hardware (check with: grep -i aes /proc/cpuinfo)
# 3. For internode, use "dc" encryption (only cross-DC, not intra-DC LAN)
server_encryption_options:
  internode_encryption: dc

# 4. Increase native_transport_max_threads if client connections are bottlenecked
native_transport_max_threads: 256
```

### 12.9 Role Not Found After Cluster Restart

**Symptom**: `InvalidRequestException: Role 'app_user' doesn't exist` after restart.

**Cause**: system_auth has RF=1 and the single replica was not yet up when the query executed.

**Fix**:
```bash
# Ensure system_auth has RF >= 3 (or equal to number of nodes if < 3)
# Wait for all nodes to be UN before clients connect

# Add a startup health check in application:
# Retry connection with exponential backoff until auth succeeds
```

### 12.10 Unauthorized Schema Change Detected

**Symptom**: unexpected DDL change found in audit logs.

**Fix**:
```bash
# 1. Identify who made the change
auditlogviewer /var/log/cassandra/audit/ | grep "Type: DDL"

# 2. Check the role's permissions
cqlsh -e "LIST ALL PERMISSIONS OF <suspect_role>;"

# 3. Revoke unnecessary permissions
cqlsh -e "REVOKE ALTER ON KEYSPACE ecommerce FROM <suspect_role>;"

# 4. If the role was compromised, rotate its password immediately
cqlsh -e "ALTER ROLE <suspect_role> WITH PASSWORD = 'NEW_PASSWORD';"

# 5. Restore schema if needed from a snapshot
```

---

## 13. FAQ

### Q1: Does Cassandra support LDAP authentication?

Not in open-source Cassandra. DataStax Enterprise (DSE) includes `LdapAuthenticator`. For open-source, you can write a custom `IAuthenticator` plugin or use Cassandra 5.0's `MutualTlsAuthenticator` with client certificates issued by your PKI.

### Q2: What happens if system_auth is unavailable?

If the system_auth keyspace replicas are all down, no user can authenticate. This is why system_auth must have RF >= 3 and must be replicated to ALL DCs. Always treat system_auth replication as a critical configuration.

### Q3: Can I use Cassandra without authentication in production?

Technically yes, but this is a severe security risk. Any client that can reach port 9042 has full access. Always enable `PasswordAuthenticator` in production.

### Q4: How do I rotate TLS certificates without downtime?

Add the new CA to all truststores first (rolling restart). Then replace keystores with new certs (second rolling restart). During the overlap, both old and new certs are trusted. After all nodes have new certs, remove the old CA from truststores (third rolling restart). This is a 3-phase rolling restart.

### Q5: Does enabling TLS significantly impact performance?

TLS adds 5-15% CPU overhead depending on cipher suite and hardware. With AES-NI (hardware AES acceleration), the impact is minimal. Use `internode_encryption: dc` to only encrypt cross-DC traffic if intra-DC LAN is trusted.

### Q6: How do I encrypt data at rest in open-source Cassandra?

Use filesystem-level encryption: LUKS on Linux, cloud-provider managed encryption (AWS EBS, GCP PD, Azure Disk). Cassandra does not need configuration changes for disk-level encryption. DSE includes built-in TDE.

### Q7: Can different users have different consistency levels?

No. Consistency level is set per query, not per user. However, application services connect with different roles and can use different CLs in their queries. You can enforce CL policies at the application layer.

### Q8: How do I prevent accidental data deletion?

- Use authorization to restrict DELETE/MODIFY permissions.
- Enable audit logging for DML operations.
- Use guardrails (4.1+) to limit destructive operations.
- Consider setting `gc_grace_seconds` longer for critical tables.
- Take frequent snapshots for recovery.

### Q9: Is JMX safe to expose to the network?

JMX without authentication allows arbitrary code execution. Never expose JMX to untrusted networks. Use `LOCAL_JMX=yes` and access via SSH tunnel, or enable JMX authentication + TLS. In Cassandra 4.0+, prefer virtual tables (`system_views`) via CQL for remote monitoring.

### Q10: What is the MutualTlsAuthenticator in Cassandra 5.0?

It maps client X.509 certificate identities (CN or SAN) to Cassandra roles. Clients authenticate by presenting a valid certificate signed by the trusted CA, eliminating the need for passwords entirely. The certificate's identity must match a Cassandra role name.

### Q11: How do I audit who accessed specific data?

Enable audit logging with `included_categories: QUERY,DML` and filter by keyspace. The audit log records the user, source IP, timestamp, and full query text for every matching operation.

### Q12: Can I restrict access based on source IP?

In Cassandra 5.0, use CIDR-based authorization: `CREATE ROLE ... WITH ACCESS FROM CIDRS {'10.0.0.0/8'}`. In earlier versions, use firewall rules (iptables, security groups) or a proxy layer.

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*
