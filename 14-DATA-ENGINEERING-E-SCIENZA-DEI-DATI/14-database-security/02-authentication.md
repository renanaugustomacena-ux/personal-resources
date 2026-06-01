# Autenticazione nei Database

L'autenticazione è il processo di verifica dell'identità di un client che tenta di connettersi al database. È il primo strato di difesa: senza autenticazione robusta, tutti gli altri controlli di sicurezza sono inutili. Un attaccante che ottiene l'accesso come utente legittimo aggira autorizzazione, auditing, e crittografia.

## Modelli di Autenticazione

### Password-Based Authentication

L'autenticazione tramite password è la più comune ma anche la più vulnerabile a attacchi di brute-force, credential stuffing, e leak di credenziali.

```sql
-- PostgreSQL: configurazione scram-sha-256 (raccomandato)
-- In postgresql.conf:
-- password_encryption = scram-sha-256  (default in PG 14+)

-- Creare un utente con SCRAM
CREATE USER app_service
  LOGIN
  ENCRYPTED PASSWORD 'p@ssw0rd-R4ndom-Str0ng!'
  CONNECTION LIMIT 20
  VALID UNTIL '2027-06-01';

-- Verificare il metodo di hashing usato
SELECT rolname, rolpassword
FROM pg_authid
WHERE rolname = 'app_service';
-- rolpassword inizia con 'SCRAM-SHA-256$' se configurato correttamente
-- 'md5...' indica hash MD5 legacy (da migrare)

-- Migrare da md5 a scram-sha-256
-- 1. Aggiornare password_encryption in postgresql.conf
-- 2. Far cambiare la password (o cambiarla come admin)
ALTER USER legacy_user ENCRYPTED PASSWORD 'nuova_password_sicura';
-- La nuova password sarà hashata con SCRAM

-- Verificare la validità della password nella connessione
-- pg_hba.conf deve specificare scram-sha-256 per il metodo:
-- host all all 0.0.0.0/0 scram-sha-256
```

### Certificate-Based Authentication (Mutual TLS)

mTLS è il metodo più sicuro per connessioni machine-to-machine. Non ci sono password da rubare: l'identità è dimostrata con un certificato X.509 firmato da una CA fidata.

```bash
# Setup PKI per autenticazione certificato database

# 1. Creare la Certificate Authority (CA) interna
openssl genrsa -aes256 -out /etc/pki/db-ca/ca-key.pem 4096
openssl req -new -x509 -days 3650 -key /etc/pki/db-ca/ca-key.pem \
  -subj "/C=IT/O=MyOrg/CN=Database CA" \
  -out /etc/pki/db-ca/ca-cert.pem

# 2. Certificato per il server PostgreSQL
openssl genrsa -out /etc/postgresql/ssl/server-key.pem 2048
openssl req -new -key /etc/postgresql/ssl/server-key.pem \
  -subj "/C=IT/O=MyOrg/CN=db.example.com" \
  -out /etc/postgresql/ssl/server-csr.pem

# Aggiungere Subject Alternative Names per validazione hostname
cat > /tmp/server-ext.cnf << 'EOF'
[v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = db.example.com
DNS.2 = db-primary.example.com
IP.1 = 192.168.1.10
EOF

openssl x509 -req -days 365 \
  -in /etc/postgresql/ssl/server-csr.pem \
  -CA /etc/pki/db-ca/ca-cert.pem \
  -CAkey /etc/pki/db-ca/ca-key.pem \
  -CAcreateserial \
  -extfile /tmp/server-ext.cnf \
  -extensions v3_req \
  -out /etc/postgresql/ssl/server-cert.pem

# 3. Certificato per un client specifico (es. microservizio "orders")
openssl genrsa -out /etc/pki/clients/orders-key.pem 2048
openssl req -new -key /etc/pki/clients/orders-key.pem \
  -subj "/C=IT/O=MyOrg/CN=orders-service" \  # CN deve corrispondere al nome utente PostgreSQL
  -out /etc/pki/clients/orders-csr.pem

openssl x509 -req -days 365 \
  -in /etc/pki/clients/orders-csr.pem \
  -CA /etc/pki/db-ca/ca-cert.pem \
  -CAkey /etc/pki/db-ca/ca-key.pem \
  -CAcreateserial \
  -out /etc/pki/clients/orders-cert.pem
```

```
# pg_hba.conf: autenticazione con certificato client
# Il CN del certificato client deve corrispondere all'utente PostgreSQL

# clientcert=verify-full: verifica CN e CA
hostssl all orders-service 10.0.0.0/8 cert clientcert=verify-full

# Permettere qualsiasi utente con certificato valido
hostssl all all 10.0.0.0/8 cert clientcert=verify-ca
```

```python
# Connessione PostgreSQL con certificato client (Python psycopg2)
import psycopg2

conn = psycopg2.connect(
    host="db.example.com",
    port=5432,
    dbname="myapp",
    user="orders-service",
    sslmode="verify-full",           # verifica il certificato server
    sslcert="/etc/pki/clients/orders-cert.pem",
    sslkey="/etc/pki/clients/orders-key.pem",
    sslrootcert="/etc/pki/db-ca/ca-cert.pem"
)
```

### LDAP / Active Directory Integration

Nelle organizzazioni enterprise, PostgreSQL può delegare l'autenticazione a LDAP/AD, centralizzando la gestione degli utenti.

```
# pg_hba.conf: autenticazione LDAP
host all +staff_role 10.0.0.0/8 ldap
  ldapserver=ldap.example.com ldapport=636
  ldaptls=1
  ldapbasedn="ou=People,dc=example,dc=com"
  ldapbinddn="cn=postgres-service,ou=ServiceAccounts,dc=example,dc=com"
  ldapbindpasswd="service-account-password"
  ldapsearchattribute=uid
  ldapsearchfilter="(memberOf=cn=db-users,ou=Groups,dc=example,dc=com)"
```

Il flusso di autenticazione LDAP è:
1. Il client fornisce username e password a PostgreSQL
2. PostgreSQL si collega al server LDAP con le credenziali del service account
3. PostgreSQL cerca l'utente nella directory LDAP
4. PostgreSQL tenta il bind LDAP con le credenziali fornite dal client
5. Se il bind ha successo, PostgreSQL permette la connessione

Nota: l'utente deve esistere sia in LDAP che in PostgreSQL (solo come ruolo, senza password):

```sql
-- Creare utenti corrispondenti agli utenti LDAP
-- Non impostare password: l'autenticazione è gestita da LDAP
CREATE ROLE mario.rossi LOGIN;
GRANT readonly_role TO mario.rossi;

CREATE ROLE luigi.bianchi LOGIN;
GRANT app_role TO luigi.bianchi;
```

### Kerberos / GSSAPI

Kerberos è il protocollo di autenticazione preferito in ambienti Windows/Active Directory e in ambienti enterprise Unix con MIT Kerberos.

```ini
# postgresql.conf
krb_server_keyfile = '/etc/postgresql/postgresql.keytab'
krb_caseins_users = off  # username case-sensitive

# pg_hba.conf
host all all 10.0.0.0/8 gss include_realm=0 krb_realm=EXAMPLE.COM
# include_realm=0: rimuove @EXAMPLE.COM dallo username
# krb_realm: accetta solo ticket del realm specificato
```

```bash
# Creare il keytab per PostgreSQL
# Sul Domain Controller (Windows) o KDC (MIT Kerberos):
kadmin.local -q "addprinc -randkey postgres/db.example.com@EXAMPLE.COM"
kadmin.local -q "ktadd -k /etc/postgresql/postgresql.keytab postgres/db.example.com@EXAMPLE.COM"

# Sul client: ottenere un ticket Kerberos
kinit mario.rossi@EXAMPLE.COM
klist  # verificare il ticket

# Connessione con Kerberos (nessuna password richiesta)
psql -h db.example.com -U mario.rossi -d myapp
```

## Gestione del Ciclo di Vita delle Credenziali

### Rotazione Automatica delle Password

```python
#!/usr/bin/env python3
"""
Rotazione automatica delle password database usando HashiCorp Vault.
Da eseguire come cron job periodico.
"""
import hvac
import psycopg2
import secrets
import string
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_strong_password(length: int = 32) -> str:
    """Genera una password crittograficamente sicura."""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    # Garantire almeno un carattere di ogni tipo
    password = (
        secrets.choice(string.ascii_lowercase) +
        secrets.choice(string.ascii_uppercase) +
        secrets.choice(string.digits) +
        secrets.choice('!@#$%^&*') +
        ''.join(secrets.choice(alphabet) for _ in range(length - 4))
    )
    # Mescolare per evitare pattern prevedibili
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return ''.join(password_list)

def rotate_db_password(
    vault_client: hvac.Client,
    vault_path: str,
    db_conn_str: str,
    username: str
) -> bool:
    """
    Ruota la password di un utente database.
    1. Genera nuova password
    2. Aggiorna in PostgreSQL
    3. Aggiorna in Vault
    4. Verifica che la connessione funzioni con la nuova password
    """
    new_password = generate_strong_password()
    timestamp = datetime.utcnow().isoformat()
    
    try:
        # 1. Aggiornare la password in PostgreSQL
        with psycopg2.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "ALTER USER %s ENCRYPTED PASSWORD %s",
                    (username, new_password)
                )
                # Non committare ancora: verificare prima
        
        # 2. Testare la nuova password
        test_dsn = db_conn_str.replace(
            f"user={username}",
            f"user={username} password={new_password}"
        )
        with psycopg2.connect(test_dsn) as test_conn:
            with test_conn.cursor() as cur:
                cur.execute("SELECT 1")
        
        # 3. Salvare in Vault
        vault_client.secrets.kv.v2.create_or_update_secret(
            path=vault_path,
            secret={
                'username': username,
                'password': new_password,
                'rotated_at': timestamp
            }
        )
        
        logger.info(f"Password rotata per {username} alle {timestamp}")
        return True
        
    except Exception as e:
        logger.error(f"Errore rotazione password {username}: {e}")
        return False

# Vault Dynamic Secrets: approccio preferito
# Vault crea credenziali temporanee direttamente nel database
def setup_vault_database_secret(vault_client: hvac.Client):
    """Configura Vault per generare credenziali dinamiche."""
    # Configurare la connessione al database in Vault
    vault_client.secrets.database.configure(
        name='myapp-postgres',
        plugin_name='postgresql-database-plugin',
        connection_url='postgresql://{{username}}:{{password}}@db.example.com:5432/myapp',
        allowed_roles=['myapp-readonly', 'myapp-readwrite'],
        username='vault-admin',
        password='vault-admin-password'
    )
    
    # Definire un ruolo per credenziali di sola lettura (TTL 1 ora)
    vault_client.secrets.database.create_role(
        name='myapp-readonly',
        db_name='myapp-postgres',
        creation_statements=[
            "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';",
            "GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";",
            "GRANT USAGE ON SCHEMA public TO \"{{name}}\";"
        ],
        revocation_statements=[
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = '{{name}}';",
            "DROP ROLE IF EXISTS \"{{name}}\";"
        ],
        default_ttl='1h',
        max_ttl='24h'
    )
```

## Protezione contro gli Attacchi di Autenticazione

### Rate Limiting e Account Lockout

PostgreSQL non ha account lockout nativo. Si implementa a livello applicativo o con extension:

```python
# Implementazione rate limiting a livello applicativo
import redis
import time

class DatabaseAuthRateLimiter:
    """
    Limita i tentativi di connessione per prevenire brute force.
    Usa Redis come storage per i contatori.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minuti
        self.window = 60  # finestra di 60 secondi
    
    def check_and_record_attempt(self, username: str, ip_address: str) -> bool:
        """
        Restituisce True se il tentativo è permesso, False se bloccato.
        """
        key = f"db_auth:{username}:{ip_address}"
        
        # Controllare se l'account è bloccato
        lockout_key = f"db_lockout:{username}:{ip_address}"
        if self.redis.exists(lockout_key):
            return False
        
        # Incrementare il contatore
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window)
        results = pipe.execute()
        
        attempt_count = results[0]
        
        if attempt_count >= self.max_attempts:
            # Bloccare l'account
            self.redis.setex(lockout_key, self.lockout_duration, 1)
            self.redis.delete(key)
            
            # Log del blocco per SIEM
            logger.warning(
                f"Account bloccato: username={username} ip={ip_address} "
                f"tentativi={attempt_count}"
            )
            return False
        
        return True
    
    def reset_attempts(self, username: str, ip_address: str):
        """Chiamare dopo autenticazione riuscita."""
        key = f"db_auth:{username}:{ip_address}"
        self.redis.delete(key)
```

### Connection Hijacking Prevention

```sql
-- Impostare scadenza automatica delle sessioni inattive
-- postgresql.conf
idle_session_timeout = 3600000  -- 1 ora in ms; 0 = disabilitato
idle_in_transaction_session_timeout = 300000  -- 5 minuti per transazioni aperte

-- A livello di ruolo (override per utenti specifici)
ALTER USER analyst_role SET idle_in_transaction_session_timeout = '5min';
ALTER USER app_service SET idle_session_timeout = '1hour';

-- Verificare sessioni lunghe
SELECT
  pid,
  usename,
  application_name,
  client_addr,
  state,
  state_change,
  EXTRACT(EPOCH FROM (NOW() - state_change)) AS seconds_in_state,
  query
FROM pg_stat_activity
WHERE state != 'idle'
  AND EXTRACT(EPOCH FROM (NOW() - state_change)) > 3600
ORDER BY seconds_in_state DESC;
```

## Tabella di Confronto Metodi di Autenticazione

| Metodo | Sicurezza | Complessità | Adatto per |
|--------|-----------|-------------|------------|
| trust | Nessuna | Minima | Solo socket locale su macchine sicure |
| md5 | Bassa (deprecated) | Minima | Legacy, da migrare |
| scram-sha-256 | Media-Alta | Bassa | Standard per la maggior parte dei casi |
| cert (mTLS) | Alta | Media | Servizi machine-to-machine |
| gss (Kerberos) | Alta | Alta | Enterprise con AD/MIT KDC |
| ldap | Media | Media | Enterprise con directory LDAP |
| Vault dynamic secrets | Molto alta | Alta | Cloud-native, zero-trust |

La raccomandazione attuale: usare `scram-sha-256` come baseline, mTLS per servizi critici, Vault dynamic secrets per ambienti cloud con requisiti di compliance elevati.

