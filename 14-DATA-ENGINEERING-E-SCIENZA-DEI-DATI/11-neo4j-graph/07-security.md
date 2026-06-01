# Neo4j — Sicurezza, Autenticazione e Autorizzazione

## Autenticazione

### Provider di Autenticazione

Neo4j supporta autenticazione nativa, LDAP/Active Directory, e SSO via Kerberos.

```properties
# neo4j.conf

# Autenticazione abilitata (sempre in produzione)
dbms.security.auth_enabled=true

# Provider di autenticazione (lista ordinata per priorità)
dbms.security.auth_provider=native  # o ldap, kerberos, oidc-azure, oidc-google

# Blocco automatico dopo N tentativi falliti
dbms.security.auth_max_failed_attempts=3
dbms.security.auth_lock_time=60s

# Require password change al primo login
dbms.security.require_change_on_first_login=true
```

### Gestione Utenti (Cypher)

```cypher
// Lista utenti
SHOW USERS YIELD username, roles, passwordChangeRequired, suspended;

// Crea utente
CREATE USER alice
SET PASSWORD "SecurePass123!"
CHANGE REQUIRED  -- deve cambiare password al primo login
SET STATUS ACTIVE;

// Modifica password
ALTER USER alice SET PASSWORD "NewPass456!" CHANGE NOT REQUIRED;

// Sospendi/riattiva utente
ALTER USER alice SET STATUS SUSPENDED;
ALTER USER alice SET STATUS ACTIVE;

// Elimina utente
DROP USER alice;
```

---

## Autorizzazione: Role-Based Access Control

### Ruoli Predefiniti

| Ruolo | Permessi |
|-------|---------|
| `reader` | Lettura su tutti i database |
| `editor` | Lettura e scrittura senza schema changes |
| `publisher` | Come editor + creazione constraint/indici |
| `architect` | Come publisher + gestione database |
| `admin` | Accesso completo + gestione utenti |
| `PUBLIC` | Ruolo base assegnato a tutti gli utenti |

```cypher
// Assegna ruolo
GRANT ROLE reader TO alice;
GRANT ROLE editor, reader TO bob;

// Revoca ruolo
REVOKE ROLE editor FROM bob;

// Mostra ruoli di un utente
SHOW USERS YIELD username, roles WHERE username = "alice";
```

### Ruoli Custom (Enterprise)

```cypher
// Crea ruolo custom
CREATE ROLE analytics_ro;

// Assegna permessi specifici al ruolo
GRANT MATCH {*} ON GRAPH analytics TO analytics_ro;           -- legge tutti i nodi e rel
GRANT TRAVERSE ON GRAPH analytics TO analytics_ro;            -- traversal
GRANT READ {*} ON GRAPH analytics ELEMENTS * TO analytics_ro; -- legge tutte le proprietà

// Permessi su database specifico
GRANT ACCESS ON DATABASE analytics TO analytics_ro;
DENY WRITE ON GRAPH analytics TO analytics_ro;  -- esplicita negazione scrittura

// Assegna il ruolo a utenti
GRANT ROLE analytics_ro TO alice, charlie;

// Verifica permessi di un ruolo
SHOW ROLE analytics_ro PRIVILEGES;
```

---

## Property-Level Security (Enterprise)

```cypher
// Permesso di leggere solo specifiche proprietà
GRANT READ {name, age, country} ON GRAPH social NODES Person TO limited_reader;
DENY READ {ssn, salary, phone} ON GRAPH social NODES Person TO limited_reader;

// Utenti con il ruolo limited_reader vedono Person senza ssn, salary, phone
// Le proprietà negate appaiono come null nella query
```

---

## Sub-Graph Security (Segment Isolation)

```cypher
// Permesso su label specifici
GRANT TRAVERSE ON GRAPH social NODES :Person TO person_reader;
DENY TRAVERSE ON GRAPH social NODES :InternalUser TO person_reader;

// Permesso su tipo di relazione specifico
GRANT TRAVERSE ON GRAPH social RELATIONSHIPS :KNOWS TO person_reader;
DENY TRAVERSE ON GRAPH social RELATIONSHIPS :INTERNAL_LINK TO person_reader;
```

---

## TLS / Cifratura del Trasporto

```properties
# neo4j.conf

# HTTPS
server.https.enabled=true
server.https.listen_address=:7473

# Bolt TLS
server.bolt.tls_level=REQUIRED  # DISABLED, OPTIONAL, REQUIRED

# Certificati
dbms.ssl.policy.bolt.enabled=true
dbms.ssl.policy.bolt.base_directory=/var/lib/neo4j/certificates/bolt
dbms.ssl.policy.bolt.private_key=private.key
dbms.ssl.policy.bolt.public_certificate=public.crt
dbms.ssl.policy.bolt.client_auth=NONE  # NONE, OPTIONAL, REQUIRE

dbms.ssl.policy.https.enabled=true
dbms.ssl.policy.https.base_directory=/var/lib/neo4j/certificates/https
dbms.ssl.policy.https.private_key=private.key
dbms.ssl.policy.https.public_certificate=public.crt
```

### Generazione Certificati

```bash
# Self-signed per test
openssl req -newkey rsa:4096 -nodes \
    -keyout /var/lib/neo4j/certificates/bolt/private.key \
    -x509 -days 365 \
    -out /var/lib/neo4j/certificates/bolt/public.crt \
    -subj "/CN=neo4j-server"

# Let's Encrypt per produzione
certbot certonly --standalone -d neo4j.yourdomain.com
cp /etc/letsencrypt/live/neo4j.yourdomain.com/privkey.pem .../private.key
cp /etc/letsencrypt/live/neo4j.yourdomain.com/fullchain.pem .../public.crt
```

---

## Audit Logging

```properties
# Abilita security log
dbms.logs.security.level=INFO
# Log di: login, logout, access denied, privilege changes

# Query log (separato)
db.logs.query.enabled=INFO
db.logs.query.threshold=0ms  # log tutte le query
db.logs.query.parameter_logging_enabled=true
db.logs.query.allocation_logging_enabled=true
db.logs.query.page_logging_enabled=true
```

```bash
# File di log
/var/log/neo4j/security.log  -- accessi e privilege changes
/var/log/neo4j/query.log     -- tutte le query con timing e parametri
/var/log/neo4j/neo4j.log     -- log principale del server
```

**Esempio di entry nel security.log**:

```
2024-01-15 10:30:45.123+0000 INFO  [alice]: logged in
2024-01-15 10:31:02.456+0000 INFO  [alice]: logged out
2024-01-15 10:32:15.789+0000 WARN  [bob]: failed to log in (wrong credentials)
2024-01-15 10:32:16.100+0000 WARN  [bob]: failed to log in (wrong credentials)
2024-01-15 10:32:16.200+0000 WARN  [bob]: failed to log in (wrong credentials)
2024-01-15 10:32:16.300+0000 WARN  [bob]: user locked out
```

---

## Secure Deployment Checklist

- [ ] `dbms.security.auth_enabled=true` (default in produzione)
- [ ] Password di default cambiata (`neo4j`/`neo4j` → credenziali forti)
- [ ] TLS abilitato su Bolt e HTTPS
- [ ] Utenti con ruoli minimi necessari (principle of least privilege)
- [ ] `server.default_listen_address` limitato all'interfaccia necessaria
- [ ] Security log abilitato e monitorato
- [ ] Firewall: porta 7687 (Bolt) e 7474 (HTTP) accessibili solo da app server
- [ ] Backup cifrati se contengono dati sensibili
- [ ] Nessuna procedura unrestricted se non necessario (`dbms.security.procedures.unrestricted`)

La sicurezza di Neo4j combina autenticazione robusta, RBAC granulare e cifratura del trasporto per proteggere sia l'accesso ai dati che la comunicazione nel cluster.

---

## LDAP Integration

### Active Directory Configuration

```properties
# neo4j.conf — LDAP authentication
dbms.security.auth_provider=ldap

# LDAP server
dbms.security.ldap.host=ldap://ad.corp.example.com:389
# For LDAPS:
# dbms.security.ldap.host=ldaps://ad.corp.example.com:636

# System account for LDAP searches
dbms.security.ldap.authorization.system_username=cn=neo4j-svc,ou=ServiceAccounts,dc=corp,dc=example,dc=com
dbms.security.ldap.authorization.system_password=service-password

# User search
dbms.security.ldap.authentication.user_dn_template=cn={0},ou=Users,dc=corp,dc=example,dc=com
dbms.security.ldap.authentication.search_for_attribute=sAMAccountName

# Group-to-role mapping
dbms.security.ldap.authorization.group_to_role_mapping=\
    "cn=neo4j-admins,ou=Groups,dc=corp,dc=example,dc=com" = admin ;\
    "cn=neo4j-architects,ou=Groups,dc=corp,dc=example,dc=com" = architect ;\
    "cn=neo4j-readers,ou=Groups,dc=corp,dc=example,dc=com" = reader ;\
    "cn=neo4j-editors,ou=Groups,dc=corp,dc=example,dc=com" = editor

# Group search
dbms.security.ldap.authorization.group_membership_attributes=memberOf
dbms.security.ldap.authorization.use_system_account=true
```

### LDAP + Native Fallback

```properties
# Allow both LDAP and native auth (LDAP checked first)
dbms.security.auth_providers=ldap,native

# This allows local admin accounts while all regular users authenticate via LDAP
```

---

## OIDC (OpenID Connect) SSO

### Azure AD Integration

```properties
# neo4j.conf — Azure AD OIDC
dbms.security.auth_providers=oidc-azure,native

dbms.security.oidc.azure.display_name=Azure AD
dbms.security.oidc.azure.auth_flow=pkce
dbms.security.oidc.azure.well_known_discovery_uri=https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration
dbms.security.oidc.azure.audience=api://{app-id}
dbms.security.oidc.azure.claims.username=preferred_username
dbms.security.oidc.azure.claims.groups=groups
dbms.security.oidc.azure.params=client_id={client-id};response_type=code;scope=openid profile email
dbms.security.oidc.azure.authorization.group_to_role_mapping=\
    "{group-object-id-admins}" = admin ;\
    "{group-object-id-readers}" = reader
```

### Google Workspace OIDC

```properties
dbms.security.auth_providers=oidc-google,native

dbms.security.oidc.google.display_name=Google
dbms.security.oidc.google.auth_flow=pkce
dbms.security.oidc.google.well_known_discovery_uri=https://accounts.google.com/.well-known/openid-configuration
dbms.security.oidc.google.audience={client-id}.apps.googleusercontent.com
dbms.security.oidc.google.claims.username=email
dbms.security.oidc.google.params=client_id={client-id};response_type=code;scope=openid email profile
```

---

## Fine-Grained Access Control (Enterprise)

### Procedure-Level Security

```cypher
// Allow specific roles to execute specific procedures
GRANT EXECUTE PROCEDURE gds.* TO analytics_role;
DENY EXECUTE PROCEDURE apoc.load.jdbc TO read_only_role;

// Boosted procedures (run with elevated privileges)
GRANT EXECUTE BOOSTED PROCEDURE db.* TO monitoring_role;

// Function-level control
GRANT EXECUTE FUNCTION apoc.text.* TO text_processing_role;
DENY EXECUTE FUNCTION apoc.cypher.* TO restricted_role;
```

### Database-Level Permissions

```cypher
// Grant access only to specific databases
GRANT ACCESS ON DATABASE production TO app_user;
DENY ACCESS ON DATABASE staging TO app_user;
DENY ACCESS ON DATABASE system TO app_user;

// Home database (default database for a user)
ALTER USER app_user SET HOME DATABASE production;

// Composite database access
GRANT ACCESS ON DATABASE composite_analytics TO analytics_user;
```

### Write Restrictions

```cypher
// Allow writes only on specific labels
GRANT CREATE ON GRAPH production NODES :Order TO order_service;
GRANT CREATE ON GRAPH production RELATIONSHIPS :PLACED TO order_service;
DENY CREATE ON GRAPH production NODES :User TO order_service;
DENY DELETE ON GRAPH production TO order_service;

// Allow only SET property operations (no CREATE/DELETE)
GRANT SET PROPERTY {status, updated_at} ON GRAPH production NODES :Order TO order_updater;
DENY CREATE ON GRAPH production TO order_updater;
DENY DELETE ON GRAPH production TO order_updater;
```

---

## Encryption at Rest

### Transparent Data Encryption (Enterprise)

```properties
# neo4j.conf — encryption at rest
dbms.security.tde.enabled=true
dbms.security.tde.key_name=neo4j-master-key

# Key management — file-based (dev/test only)
dbms.security.tde.key_source=file
dbms.security.tde.key_file=/etc/neo4j/keys/master.key

# Key management — AWS KMS (production)
dbms.security.tde.key_source=aws-kms
dbms.security.tde.aws.kms.key_id=arn:aws:kms:eu-west-1:123456789:key/abc-def-123
dbms.security.tde.aws.region=eu-west-1

# Key management — HashiCorp Vault
dbms.security.tde.key_source=vault
dbms.security.tde.vault.address=https://vault.corp.example.com:8200
dbms.security.tde.vault.token_file=/etc/neo4j/vault-token
dbms.security.tde.vault.secret_path=secret/data/neo4j/tde-key
```

### Backup Encryption

```bash
# Encrypted backup
neo4j-admin database backup \
    --database=neo4j \
    --to-path=/backup/ \
    --encrypt=true \
    --cc-key-id=my-backup-key

# Encrypted dump
neo4j-admin database dump \
    --database=neo4j \
    --to-path=/backup/dump/ \
    --encrypt=true
```

---

## Network Security Hardening

### Firewall Rules

```bash
# Only expose necessary ports
# Bolt (client connections): 7687
# HTTP API: 7474 (disable in prod or restrict to internal)
# HTTPS API: 7473
# Discovery (cluster): 5000 (internal only)
# Transaction (cluster): 6000 (internal only)
# Raft (cluster): 7000 (internal only)
# Backup: 6362 (internal only)
# Prometheus: 2004 (internal only)

# iptables example — allow only app servers to Bolt
iptables -A INPUT -p tcp --dport 7687 -s 10.0.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 7687 -j DROP

# Allow cluster communication only between core members
iptables -A INPUT -p tcp --dport 5000:7000 -s 10.0.2.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 5000:7000 -j DROP
```

### Bind Address Restriction

```properties
# neo4j.conf — restrict listening interfaces
server.default_listen_address=10.0.2.1  # specific internal interface
server.bolt.listen_address=0.0.0.0:7687  # allow Bolt from any (behind LB)
server.http.listen_address=127.0.0.1:7474  # HTTP only from localhost
server.https.listen_address=0.0.0.0:7473  # HTTPS from any
```

---

## Security Monitoring and Alerting

### Query Audit Trail

```properties
# neo4j.conf — full query logging
db.logs.query.enabled=INFO
db.logs.query.threshold=0ms
db.logs.query.parameter_logging_enabled=true
db.logs.query.time_logging_enabled=true
db.logs.query.allocation_logging_enabled=true
db.logs.query.page_logging_enabled=true
db.logs.query.runtime_logging_enabled=true
db.logs.query.max_parameter_length=1000
```

### Detect Suspicious Activity

```cypher
// Audit: find users with admin role added recently
// (Must be tracked via custom AuditLog nodes or external SIEM)

// Detect potential data exfiltration — user reading unusually large datasets
// Configure in query.log monitoring:
// Alert when any single query returns > 100,000 rows
// Alert when user issues > 50 MATCH queries in 1 minute

// Detect privilege escalation attempts
// Monitor security.log for:
// - Failed login attempts
// - Unauthorized procedure calls
// - DENY violations
```

### SIEM Integration

```bash
# Forward security and query logs to ELK/Splunk
# Filebeat configuration for Neo4j logs
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/neo4j/security.log
    fields:
      log_type: neo4j_security
    multiline.pattern: '^\d{4}-'
    multiline.negate: true
    multiline.match: after

  - type: log
    enabled: true
    paths:
      - /var/log/neo4j/query.log
    fields:
      log_type: neo4j_query

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "neo4j-security-%{+yyyy.MM.dd}"
```

---

## Troubleshooting

### 1. Authentication Fails After Password Change

**Symptom**: User cannot log in after changing password.

**Fix**: Clear credential cache or restart:
```cypher
// Verify user status
SHOW USERS YIELD username, passwordChangeRequired, suspended
WHERE username = "alice";

// Force password reset if needed
ALTER USER alice SET PASSWORD "TempPass123!" CHANGE REQUIRED;
```

### 2. LDAP Connection Timeout

**Symptom**: Login hangs for 30+ seconds, then fails.

**Fix**: Verify LDAP connectivity and increase timeout:
```properties
dbms.security.ldap.connection_timeout=10s
dbms.security.ldap.read_timeout=10s
```
```bash
# Test LDAP connectivity
ldapsearch -x -H ldap://ad.corp.example.com:389 -D "cn=neo4j-svc,..." -W -b "dc=corp,dc=example,dc=com" "(sAMAccountName=testuser)"
```

### 3. Role Mapping Does Not Work with OIDC

**Symptom**: User authenticates via OIDC but has no roles.

**Root cause**: Group claim is not included in the token.

**Fix**: Configure the OIDC provider to include group memberships in the ID token. For Azure AD, add the "groups" claim in the App Registration manifest.

### 4. TLS Certificate Rejected by Client

**Symptom**: `ServiceUnavailable: SSL: CERTIFICATE_VERIFY_FAILED`.

**Fix**: Client must trust the CA or use the correct TLS configuration:
```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    "bolt+s://neo4j-server:7687",
    auth=("neo4j", "password"),
    encrypted=True,
    trusted_certificates="/path/to/ca-cert.pem"
)
```

### 5. Procedure Execution Denied

**Symptom**: `Client not authorized to execute procedure`.

**Fix**:
```cypher
// Check user's effective privileges
SHOW USER alice PRIVILEGES AS COMMANDS;

// Grant procedure execution
GRANT EXECUTE PROCEDURE apoc.load.json TO alice_role;
```

### 6. Property-Level Security Leaks via Aggregation

**Symptom**: User cannot read `salary` directly but can compute `avg(p.salary)`.

**Reality**: Neo4j property-level security applies to aggregation functions too. Denied properties return null, and aggregations over null values skip them. However, `count(p.salary)` would reveal how many non-null values exist.

**Mitigation**: Also deny READ on the property, not just TRAVERSE:
```cypher
DENY READ {salary} ON GRAPH hr NODES Employee TO public_role;
```

### 7. Audit Log Growing Too Large

**Symptom**: /var/log/neo4j/query.log consuming disk space.

**Fix**: Configure log rotation:
```properties
db.logs.query.rotation.size=50m
db.logs.query.rotation.keep_number=7
```

### 8. User Locked Out After Failed Attempts

**Symptom**: Valid user cannot log in.

**Fix**:
```cypher
// Check if user is locked
SHOW USERS YIELD username, suspended WHERE username = "bob";

// Unlock
ALTER USER bob SET STATUS ACTIVE;
```

### 9. CORS Issues with Browser Access

**Symptom**: Neo4j Browser works but custom web app gets CORS errors.

**Fix**:
```properties
# neo4j.conf — restrict to specific origins
dbms.security.http_access_control_allow_origin=https://app.example.com
# Never use * in production
```

### 10. Cannot Create Database-Specific Roles

**Symptom**: Custom roles grant permissions on all databases.

**Fix**: Specify database in GRANT statement:
```cypher
CREATE ROLE prod_reader;
GRANT ACCESS ON DATABASE production TO prod_reader;
GRANT MATCH {*} ON GRAPH production TO prod_reader;
// This role has zero access to other databases
```

---

## FAQ

### 1. Is Neo4j SOC 2 / ISO 27001 compliant?

Neo4j Enterprise provides features needed for compliance (TLS, RBAC, audit logging, encryption at rest). The compliance certification depends on your deployment. Neo4j Aura holds SOC 2 Type II certification.

### 2. Can I use external secret managers for database credentials?

Yes. In Kubernetes, use init containers or sidecars to fetch secrets from Vault/AWS Secrets Manager and write them to environment variables or files that Neo4j reads at startup. Aura uses its own secret management.

### 3. How do I rotate TLS certificates without downtime?

For a cluster: update certificates on read replicas first, then followers, then leader — same rolling procedure as version upgrades. Clients must trust both old and new CA during the transition.

### 4. Does Neo4j support multi-factor authentication?

Not natively. MFA is handled at the identity provider level (LDAP/AD with MFA, OIDC provider with MFA). Neo4j delegates authentication to the IdP, which enforces MFA before issuing the token.

### 5. What is the default admin password?

The default credentials are `neo4j`/`neo4j`. On first login, Neo4j forces a password change. In containerized deployments, set `NEO4J_AUTH=neo4j/yourPassword` to avoid the initial change prompt.

### 6. How do I prevent Cypher injection?

Always use parameterized queries in application code:
```python
# WRONG — vulnerable to injection
session.run(f"MATCH (p:Person {{name: '{user_input}'}}) RETURN p")

# CORRECT — parameterized
session.run("MATCH (p:Person {name: $name}) RETURN p", name=user_input)
```
APOC procedures that accept dynamic Cypher strings (e.g., `apoc.cypher.run`) should never receive unsanitized user input.

### 7. Can I restrict access to specific nodes based on user identity?

Yes, using sub-graph security (Enterprise). You can GRANT/DENY TRAVERSE on specific labels:
```cypher
DENY TRAVERSE ON GRAPH production NODES :InternalDocument TO external_role;
```
External users will not see InternalDocument nodes in any query.

### 8. How do I secure the HTTP API in production?

Disable HTTP (7474) entirely and use only HTTPS (7473) and Bolt+TLS (7687):
```properties
server.http.enabled=false
server.https.enabled=true
server.bolt.tls_level=REQUIRED
```

### 9. What logging is needed for GDPR compliance?

Log all data access (query.log), all authentication events (security.log), and all schema changes. Implement data retention policies for logs. Ensure logs themselves do not contain PII from query parameters — consider redacting sensitive parameters:
```properties
db.logs.query.parameter_logging_enabled=false  # disable parameter logging if queries contain PII
```

### 10. How do I handle key rotation for encryption at rest?

Use the key management backend's rotation mechanism (AWS KMS automatic rotation, Vault's versioned keys). Neo4j will use the new key for new writes while still decrypting old data with the previous key version. Plan a re-encryption maintenance window for full key rotation.

Neo4j's security model combines authentication (native, LDAP, OIDC), fine-grained RBAC authorization (database, graph, label, property, procedure level), transport encryption (TLS), data-at-rest encryption (TDE), and comprehensive audit logging to meet enterprise and compliance requirements.

---

## Security Hardening Recipes

### Production Configuration Template

```properties
# neo4j.conf — hardened production configuration

# Authentication
dbms.security.auth_enabled=true
dbms.security.auth_max_failed_attempts=5
dbms.security.auth_lock_time=300s

# TLS on all channels
server.bolt.tls_level=REQUIRED
server.https.enabled=true
server.http.enabled=false  # disable unencrypted HTTP

# Restrict listen addresses
server.default_listen_address=0.0.0.0
server.http.listen_address=127.0.0.1:7474  # only localhost if needed for monitoring

# Procedure restrictions
dbms.security.procedures.unrestricted=apoc.meta.*,apoc.export.*
dbms.security.procedures.allowlist=apoc.*,gds.*

# Logging
db.logs.query.enabled=INFO
db.logs.query.threshold=1000ms  # log only slow queries
dbms.logs.security.level=INFO

# Connection limits
server.bolt.thread_pool_keep_alive=5m
server.bolt.thread_pool_max_size=400
server.bolt.connection_keep_alive=60s
```

### Docker Hardening

```dockerfile
# Run as non-root
FROM neo4j:5-enterprise
USER neo4j

# Read-only filesystem where possible
# Mount data and logs volumes separately
```

```yaml
# docker-compose.yml — security settings
services:
  neo4j:
    image: neo4j:5-enterprise
    security_opt:
      - no-new-privileges:true
    read_only: false  # Neo4j needs write access to data dir
    tmpfs:
      - /tmp
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}  # from .env file, not hardcoded
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
      - ./certificates:/certificates:ro  # read-only cert mount
```

### Principle of Least Privilege — Role Design

```cypher
// Application service accounts — minimal permissions

// Read-only analytics user
CREATE ROLE analytics_reader;
GRANT ACCESS ON DATABASE analytics TO analytics_reader;
GRANT MATCH {*} ON GRAPH analytics TO analytics_reader;
GRANT EXECUTE PROCEDURE gds.*.stream TO analytics_reader;
DENY WRITE ON GRAPH analytics TO analytics_reader;
CREATE USER analytics_svc SET PASSWORD "..." CHANGE NOT REQUIRED SET STATUS ACTIVE;
GRANT ROLE analytics_reader TO analytics_svc;

// Write-limited order service
CREATE ROLE order_writer;
GRANT ACCESS ON DATABASE production TO order_writer;
GRANT MATCH {*} ON GRAPH production TO order_writer;
GRANT CREATE ON GRAPH production NODES :Order, :OrderItem TO order_writer;
GRANT CREATE ON GRAPH production RELATIONSHIPS :PLACED, :CONTAINS TO order_writer;
GRANT SET PROPERTY {status, updated_at} ON GRAPH production NODES :Order TO order_writer;
DENY DELETE ON GRAPH production TO order_writer;
DENY CREATE ON GRAPH production NODES :User, :Admin TO order_writer;
CREATE USER order_svc SET PASSWORD "..." CHANGE NOT REQUIRED SET STATUS ACTIVE;
GRANT ROLE order_writer TO order_svc;
```

### Compliance Matrix

| Requirement | Neo4j Feature | Configuration |
|-------------|---------------|---------------|
| Data in transit encryption | Bolt TLS, HTTPS | `server.bolt.tls_level=REQUIRED` |
| Data at rest encryption | TDE (Enterprise) | `dbms.security.tde.enabled=true` |
| Access control | RBAC + sub-graph security | Custom roles + label-level grants |
| Audit trail | Query log + security log | `db.logs.query.enabled=INFO` |
| Password policy | Auth provider config | `dbms.security.auth_max_failed_attempts` |
| Session management | Connection timeouts | `server.bolt.connection_keep_alive` |
| Data masking | Property-level DENY | `DENY READ {ssn} ON GRAPH ...` |
| Key management | KMS integration | TDE with AWS KMS / Vault |
| Network segmentation | Listen address + firewall | Bind to internal interfaces |
| Vulnerability scanning | Regular patching | Monitor Neo4j CVE advisories |


### Data Classification Labels

```cypher
// Tag sensitive data with classification labels for governance
CREATE (p:Person:PII {name: "Alice", ssn: "..."});
CREATE (d:Document:Confidential {title: "Board Minutes"});
CREATE (f:FinancialRecord:Restricted {amount: 50000});

// Deny access to classified labels by default
DENY TRAVERSE ON GRAPH production NODES :PII TO public_role;
DENY TRAVERSE ON GRAPH production NODES :Confidential TO external_role;
DENY READ {ssn} ON GRAPH production NODES :PII TO analyst_role;
```

