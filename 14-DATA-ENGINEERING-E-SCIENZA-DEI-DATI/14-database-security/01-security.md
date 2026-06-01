# Sicurezza dei Database: Fondamenti

La sicurezza dei database è la disciplina che protegge i dati da accessi non autorizzati, modifiche non intenzionali, e perdita. In un'organizzazione, i database contengono gli asset più critici: dati finanziari, informazioni personali dei clienti, segreti aziendali, e infrastruttura operativa. Una violazione del database non è un problema tecnico secondario: può significare violazioni normative (GDPR, PCI-DSS, HIPAA), perdita di reputazione, o danni economici diretti.

La sicurezza dei database si articola in sei strati sovrapposti: autenticazione (chi sei?), autorizzazione (cosa puoi fare?), crittografia (i dati sono illeggibili senza chiave), sicurezza di rete (chi può raggiungerti?), auditing (cosa hai fatto?), e compliance (sei in regola?). Nessun singolo strato è sufficiente: la sicurezza è il prodotto di tutti questi strati.

## Autenticazione: Chi Sei?

L'autenticazione verifica l'identità di chi si connette al database. I metodi variano per sicurezza, complessità e supporto infrastrutturale.

### Metodi di Autenticazione in PostgreSQL

```
# pg_hba.conf: Host-Based Authentication
# Formato: TYPE  DATABASE  USER  ADDRESS  METHOD

# Connessioni locali via socket Unix
local   all             postgres                                peer
local   all             all                                     md5

# Connessioni SSL dalla rete interna con scram-sha-256
hostssl myapp           app_user        10.0.0.0/8              scram-sha-256

# Connessioni con certificato client (mutual TLS)
hostssl replication     replicator      192.168.1.0/24          cert clientcert=verify-full

# Autenticazione Kerberos/GSSAPI per ambienti enterprise
host    all             all             0.0.0.0/0               gss include_realm=0 krb_realm=EXAMPLE.COM

# LDAP per Active Directory
host    all             +ldap_users     0.0.0.0/0               ldap
  ldapserver=ldap.example.com
  ldapbasedn="dc=example,dc=com"
  ldapbinddn="cn=service-account,dc=example,dc=com"
  ldapbindpasswd="service-password"
  ldapsearchattribute=sAMAccountName
```

I metodi di autenticazione in ordine di sicurezza crescente:
- `trust`: nessuna password richiesta (SOLO per connessioni locali su macchine sicure)
- `md5`: hash MD5 della password + salt (deprecato, vulnerabile a precomputed rainbow tables)
- `scram-sha-256`: challenge-response sicuro (standard raccomandato attuale)
- `cert`: certificato client X.509 (mutual TLS, il più sicuro per connessioni di servizio)
- `gss`/`sspi`: Kerberos (per ambienti enterprise con AD)
- `ldap`: delegato a LDAP/AD (centralizza la gestione delle identità)

```sql
-- PostgreSQL: creare utenti con autenticazione forte
-- Usare password generate sicure (mai password leggibili nei file di config)
CREATE USER app_user
  LOGIN
  ENCRYPTED PASSWORD 'cambia_questa_password_con_una_sicura'
  CONNECTION LIMIT 50
  VALID UNTIL '2027-01-01';  -- scadenza obbligatoria in molte policy di compliance

-- Ruolo con scadenza password per utenti umani
CREATE ROLE analyst
  LOGIN
  ENCRYPTED PASSWORD 'forte_password_analista'
  VALID UNTIL '2026-12-31';

-- Cambiare la password
ALTER USER app_user ENCRYPTED PASSWORD 'nuova_password_sicura';
```

### Autenticazione in MySQL

```sql
-- MySQL: metodi di autenticazione
-- mysql_native_password (legacy, meno sicuro)
CREATE USER 'app_user'@'%' IDENTIFIED WITH mysql_native_password BY 'password';

-- caching_sha2_password (default da MySQL 8.0, raccomandato)
CREATE USER 'app_user'@'10.0.0.0/255.0.0.0' IDENTIFIED WITH caching_sha2_password BY 'password';

-- auth_socket: autenticazione basata sull'utente OS (per utenti locali)
CREATE USER 'backup_user'@'localhost' IDENTIFIED WITH auth_socket AS 'backup_os_user';

-- Scadenza password
ALTER USER 'app_user'@'%' PASSWORD EXPIRE INTERVAL 90 DAY;

-- Bloccare un utente
ALTER USER 'suspicious_user'@'%' ACCOUNT LOCK;

-- Sbloccare
ALTER USER 'suspicious_user'@'%' ACCOUNT UNLOCK;

-- Richiedere SSL per un utente specifico
ALTER USER 'sensitive_app'@'%' REQUIRE SSL;

-- Richiedere certificato specifico
ALTER USER 'service_account'@'%'
  REQUIRE SUBJECT '/CN=service-account/O=MyOrg'
  AND ISSUER '/CN=MyOrg CA';
```

## Gestione degli Utenti e dei Ruoli

La gestione corretta degli utenti segue il principio del minimo privilegio: ogni utente o servizio riceve esattamente i permessi necessari e niente di più.

### Modello a Ruoli PostgreSQL

```sql
-- Struttura gerarchica dei ruoli per un'applicazione web

-- Ruolo base per accesso in sola lettura
CREATE ROLE readonly_role;
GRANT CONNECT ON DATABASE myapp TO readonly_role;
GRANT USAGE ON SCHEMA public TO readonly_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_role;
-- ALTER DEFAULT PRIVILEGES è cruciale: si applica anche alle tabelle future

-- Ruolo per l'applicazione (lettura + scrittura)
CREATE ROLE app_role;
GRANT CONNECT ON DATABASE myapp TO app_role;
GRANT USAGE ON SCHEMA public TO app_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO app_role;

-- Ruolo per migrazioni (DDL)
CREATE ROLE migration_role;
GRANT app_role TO migration_role;
GRANT CREATE ON SCHEMA public TO migration_role;
-- Solo il migration_role può fare DDL; l'app_role non può

-- Utenti concreti che ereditano dai ruoli
CREATE USER web_app LOGIN ENCRYPTED PASSWORD 'password_web' CONNECTION LIMIT 100;
GRANT app_role TO web_app;

CREATE USER analyst_1 LOGIN ENCRYPTED PASSWORD 'password_analyst1';
GRANT readonly_role TO analyst_1;

CREATE USER migration_runner LOGIN ENCRYPTED PASSWORD 'password_migration';
GRANT migration_role TO migration_runner;

-- Service accounts per microservizi (connection limit basso = superficie ridotta)
CREATE USER orders_service LOGIN ENCRYPTED PASSWORD 'password_orders' CONNECTION LIMIT 20;
GRANT app_role TO orders_service;

-- Revocare un privilegio specifico da un ruolo
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM app_role;
```

### Row Level Security (RLS)

RLS permette di controllare l'accesso a livello di singola riga basandosi sull'identità dell'utente. È fondamentale per applicazioni multi-tenant dove ogni utente deve vedere solo i propri dati.

```sql
-- Abilitare RLS su una tabella
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
-- FORCE si applica anche ai superuser (raramente usato)

-- Policy per limitare ogni utente ai propri ordini
-- La funzione current_user restituisce il nome dell'utente PostgreSQL corrente
CREATE POLICY orders_isolation ON orders
  USING (user_id = (SELECT id FROM users WHERE username = current_user));

-- Policy più comune nelle applicazioni: usare una variabile di sessione
-- L'applicazione imposta la variabile all'inizio di ogni sessione
-- SET app.current_user_id = 123;
CREATE POLICY orders_app_isolation ON orders
  USING (user_id = current_setting('app.current_user_id')::int);

-- Policy per ruoli diversi
CREATE POLICY admin_sees_all ON orders
  TO admin_role
  USING (true);  -- gli admin vedono tutto

CREATE POLICY users_see_own ON orders
  TO app_role
  USING (user_id = current_setting('app.current_user_id')::int);

-- Policy con INSERT/UPDATE: un utente può solo inserire righe sue
CREATE POLICY orders_insert ON orders FOR INSERT
  WITH CHECK (user_id = current_setting('app.current_user_id')::int);

-- Esempio di uso nell'applicazione
-- conn.execute("SET app.current_user_id = %s", [user_id])
-- Poi tutte le query su 'orders' filtrano automaticamente per user_id
```

## Crittografia

### Crittografia in Transito

```ini
# PostgreSQL: abilitare TLS
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/postgresql/ssl/server.crt'
ssl_key_file = '/etc/postgresql/ssl/server.key'
ssl_ca_file = '/etc/postgresql/ssl/ca.crt'

# Versione minima TLS (TLS 1.2 minimum, TLS 1.3 preferito)
ssl_min_protocol_version = 'TLSv1.2'

# Cipher suite sicure (escludere cipher deboli)
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA'

# Richiedere SSL per tutte le connessioni non locali
# pg_hba.conf:
# hostnossl all all 0.0.0.0/0 reject  # blocca connessioni non-SSL
```

```ini
# MySQL: TLS configuration
# my.cnf
[mysqld]
ssl_ca=/etc/mysql/ssl/ca.pem
ssl_cert=/etc/mysql/ssl/server-cert.pem
ssl_key=/etc/mysql/ssl/server-key.pem
tls_version=TLSv1.2,TLSv1.3
require_secure_transport=ON  # rifiuta connessioni non-SSL
```

### Crittografia a Riposo

```sql
-- PostgreSQL: crittografia a livello di colonna con pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Crittografia simmetrica (AES-256 via pgp_sym_encrypt)
-- ATTENZIONE: la chiave non deve essere nel codice; usare un vault
CREATE TABLE patients (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  ssn BYTEA,  -- Social Security Number crittografato
  dob DATE NOT NULL,
  insurance_data BYTEA
);

-- Inserire con crittografia
INSERT INTO patients (name, ssn, dob)
VALUES (
  'Mario Rossi',
  pgp_sym_encrypt('123-45-6789', current_setting('app.encryption_key')),
  '1980-01-15'
);

-- Leggere con decrittografia
SELECT
  name,
  pgp_sym_decrypt(ssn, current_setting('app.encryption_key')) AS ssn_plain,
  dob
FROM patients
WHERE id = 1;

-- Crittografia asimmetrica (pgp_pub_encrypt con chiave pubblica)
-- Solo chi ha la chiave privata può decrittografare
INSERT INTO sensitive_messages (content)
VALUES (
  pgp_pub_encrypt('messaggio segreto', dearmor('-----BEGIN PGP PUBLIC KEY BLOCK-----...'))
);
```

## Auditing

```sql
-- PostgreSQL: audit tramite pgaudit extension
-- Installazione:
-- apt-get install postgresql-15-pgaudit

-- postgresql.conf
-- shared_preload_libraries = 'pgaudit'

-- Configurazione audit
ALTER SYSTEM SET pgaudit.log = 'ddl, role, write, connection';
-- ddl: CREATE/ALTER/DROP
-- role: GRANT/REVOKE
-- write: INSERT/UPDATE/DELETE
-- connection: CONNECT/DISCONNECT
-- read: SELECT (attenzione: molto verboso)

SELECT pg_reload_conf();

-- Audit per tabella specifica
-- Per tabelle con dati sensibili, abilitare audit a livello di oggetto
ALTER TABLE patients SET (audit = on);

-- I log di audit appaiono nel log PostgreSQL:
-- AUDIT: SESSION,1,1,DDL,CREATE TABLE,...
-- AUDIT: SESSION,1,1,WRITE,INSERT,public,patients,...
```

```sql
-- MySQL: General Query Log e Audit Plugin
-- my.cnf per general query log (attenzione: molto verboso in produzione)
[mysqld]
general_log = 1
general_log_file = /var/log/mysql/general.log

-- Percona Audit Plugin (enterprise-grade)
INSTALL PLUGIN audit_log SONAME 'audit_log.so';

SET GLOBAL audit_log_policy = 'ALL';          -- tutto
-- O selettivo:
SET GLOBAL audit_log_policy = 'LOGINS';       -- solo login
SET GLOBAL audit_log_policy = 'QUERIES';      -- solo query
SET GLOBAL audit_log_format = 'JSON';         -- formato strutturato

-- Whitelist di query da non auditare (ridurre il volume)
SET GLOBAL audit_log_exclude_accounts = 'monitor_user@%,backup_user@localhost';
```

## Principi di Sicurezza Database

### Defense in Depth

Il principio fondamentale è che ogni strato di sicurezza deve essere indipendente. La compromissione di uno strato non deve portare alla compromissione dell'intero sistema:

1. **Rete**: il database non è accessibile dall'internet pubblico; solo da reti interne autorizzate
2. **Autenticazione**: credenziali forti, MFA dove possibile, rotazione periodica
3. **Autorizzazione**: minimo privilegio, separazione dei ruoli (DBA, app, analytics, migration)
4. **Crittografia**: in transito (TLS) e a riposo (per dati PII/sensibili)
5. **Auditing**: log di tutte le operazioni critiche, correlato con SIEM
6. **Patching**: aggiornamenti di sicurezza applicati tempestivamente

### Gestione dei Segreti

```bash
# MAI hardcodare password nei file di configurazione o nel codice

# BAD: password nel codice
DATABASE_URL = "postgresql://app_user:password123@db.example.com/myapp"

# GOOD: variabili d'ambiente (minimo)
DATABASE_URL = f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}/{os.environ['DB_NAME']}"

# BETTER: HashiCorp Vault
import hvac

client = hvac.Client(url='https://vault.example.com', token=os.environ['VAULT_TOKEN'])
secret = client.secrets.database.generate_credentials(name='myapp-role')
# Usa credenziali dinamiche con scadenza breve (es. 1 ora)
username = secret['data']['username']
password = secret['data']['password']

# Vault genera credenziali temporanee direttamente in PostgreSQL:
# - scadono automaticamente
# - sono revocabili immediatamente
# - ogni deployment ottiene credenziali uniche
```

