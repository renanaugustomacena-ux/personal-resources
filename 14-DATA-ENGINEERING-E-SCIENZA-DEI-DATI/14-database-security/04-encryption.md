# Crittografia nei Database

La crittografia protegge i dati rendendoli illeggibili senza la chiave corretta. Si applica a due scenari distinti: dati in transito (sulla rete) e dati a riposo (su disco). Entrambi sono necessari: un sistema che crittografa il disco ma invia le credenziali in chiaro sulla rete è ugualmente vulnerabile.

## Crittografia in Transito (TLS)

### Configurazione TLS per PostgreSQL

```bash
# Generare certificati con OpenSSL

# CA (Certificate Authority) interna
openssl req -new -x509 -days 3650 -nodes \
  -subj "/C=IT/ST=Lombardia/O=MyOrg/CN=MyOrg Database CA" \
  -keyout /etc/postgresql/ssl/ca.key \
  -out /etc/postgresql/ssl/ca.crt

# Certificato server
openssl req -new -nodes \
  -subj "/C=IT/O=MyOrg/CN=db-primary.example.com" \
  -keyout /etc/postgresql/ssl/server.key \
  -out /etc/postgresql/ssl/server.csr

# Firmare con la CA
openssl x509 -req -days 365 \
  -CA /etc/postgresql/ssl/ca.crt \
  -CAkey /etc/postgresql/ssl/ca.key \
  -CAcreateserial \
  -in /etc/postgresql/ssl/server.csr \
  -out /etc/postgresql/ssl/server.crt

# Permessi corretti (PostgreSQL rifiuta chiavi leggibili da altri)
chmod 600 /etc/postgresql/ssl/server.key
chown postgres:postgres /etc/postgresql/ssl/server.key
```

```ini
# postgresql.conf: configurazione TLS
ssl = on
ssl_cert_file = 'server.crt'             # relativo a $PGDATA
ssl_key_file = 'server.key'
ssl_ca_file = 'ca.crt'                   # CA per verificare i client
ssl_crl_file = 'ca.crl'                  # Certificate Revocation List (opzionale)

# Versione minima e cipher suite
ssl_min_protocol_version = 'TLSv1.2'
# TLS 1.3 è preferito ma non sempre supportato da tutti i driver legacy

# Cipher suite: escludere cipher deboli
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA'

# Prefer server-side cipher order (sicurezza > compatibilità)
ssl_prefer_server_ciphers = on
```

```
# pg_hba.conf: forzare TLS per tutte le connessioni di rete
# Bloccare esplicitamente connessioni non-SSL
hostnossl all all 0.0.0.0/0 reject

# Connessioni SSL dalla rete interna
hostssl all all 10.0.0.0/8 scram-sha-256

# Connessioni SSL con certificato client per service accounts
hostssl all service_accounts 10.0.0.0/8 cert clientcert=verify-full
```

### Verifica della Connessione TLS

```python
# Python: connettersi con TLS verificato
import psycopg2
import ssl

# Metodo 1: parametri DSN
conn = psycopg2.connect(
    host="db.example.com",
    port=5432,
    dbname="myapp",
    user="app_user",
    password="password",
    sslmode="verify-full",           # verifica CN e CA
    sslrootcert="/path/to/ca.crt"   # CA da cui verificare il certificato server
)

# Verificare il TLS dopo la connessione
with conn.cursor() as cur:
    cur.execute("SELECT ssl, version FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
    result = cur.fetchone()
    print(f"SSL: {result[0]}, Versione: {result[1]}")
    # SSL: True, Versione: TLSv1.3

# Metodo 2: connection string con sslmode
conn = psycopg2.connect(
    "host=db.example.com dbname=myapp user=app sslmode=verify-full sslrootcert=/path/ca.crt"
)
```

```sql
-- Verificare le connessioni TLS attive
SELECT
  pid,
  usename,
  application_name,
  client_addr,
  ssl,
  version AS tls_version,
  cipher,
  bits AS key_bits
FROM pg_stat_ssl
JOIN pg_stat_activity USING (pid)
WHERE ssl = true
ORDER BY pid;

-- Trovare connessioni non-SSL (da investigare/bloccare)
SELECT
  pid,
  usename,
  application_name,
  client_addr
FROM pg_stat_ssl
JOIN pg_stat_activity USING (pid)
WHERE ssl = false
  AND client_addr IS NOT NULL;  -- esclude connessioni locali socket
```

## Crittografia a Riposo

### Transparent Data Encryption (TDE)

Alcuni database supportano TDE nativamente (Oracle, SQL Server, MySQL Enterprise). PostgreSQL non ha TDE nativo a livello di engine; le opzioni sono:
1. **pgcrypto**: crittografia a livello di applicazione/colonna
2. **pg_tde** (extension sperimentale Percona): TDE per PostgreSQL
3. **Filesystem encryption**: dm-crypt/LUKS su Linux

```bash
# Opzione 1: LUKS per crittografia del filesystem (raccomandato per PostgreSQL)
# Creare un volume crittografato per i dati PostgreSQL

# Inizializzare il device LUKS
cryptsetup luksFormat /dev/sdb1 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --hash sha256 \
  --iter-time 2000

# Aprire il volume
cryptsetup luksOpen /dev/sdb1 postgres-data
mkfs.ext4 /dev/mapper/postgres-data
mount /dev/mapper/postgres-data /var/lib/postgresql

# Configurare l'auto-mount (con chiave su HSM o Vault in ambienti produzione)
# /etc/crypttab
# postgres-data  /dev/sdb1  /etc/luks/postgres-data.key  luks

# Pro: trasparente per PostgreSQL, nessuna modifica all'applicazione
# Contro: la chiave deve essere disponibile al boot; gestione chiavi complessa
```

### pgcrypto: Crittografia a Livello di Colonna

pgcrypto offre crittografia a livello di dato nel database. È selettiva: si applica solo alle colonne che la richiedono.

```sql
-- Installazione
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Schema per dati sensibili di una piattaforma sanitaria
CREATE TABLE patient_records (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  medical_record_number TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,             -- non crittografato: necessario per ricerche
  date_of_birth DATE NOT NULL,
  diagnosis_codes TEXT[],         -- non crittografato: aggregazione statistica
  ssn BYTEA,                      -- crittografato: PII molto sensibile
  financial_info BYTEA,           -- crittografato: dati di pagamento
  notes BYTEA,                    -- crittografato: note cliniche
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Funzione helper per crittografare
-- La chiave NON deve essere nel codice; usare current_setting da un vault
CREATE OR REPLACE FUNCTION encrypt_pii(data TEXT)
RETURNS BYTEA AS $$
BEGIN
  RETURN pgp_sym_encrypt(
    data,
    current_setting('app.encryption_key'),
    'compress-algo=1, cipher-algo=aes256'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Funzione helper per decrittografare
CREATE OR REPLACE FUNCTION decrypt_pii(encrypted_data BYTEA)
RETURNS TEXT AS $$
BEGIN
  RETURN pgp_sym_decrypt(
    encrypted_data,
    current_setting('app.encryption_key')
  );
EXCEPTION
  WHEN OTHERS THEN
    -- Log del tentativo di decrittografia fallito
    RAISE WARNING 'Decrittografia fallita per utente %', current_user;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Inserire con crittografia
INSERT INTO patient_records (medical_record_number, name, date_of_birth, ssn, notes)
VALUES (
  'MRN-2025-001',
  'Mario Rossi',
  '1975-03-15',
  encrypt_pii('123-45-6789'),
  encrypt_pii('Diagnosi: ipertensione arteriosa. Terapia: ramipril 5mg.')
);

-- Leggere con decrittografia
SELECT
  id,
  name,
  date_of_birth,
  decrypt_pii(ssn) AS ssn,
  decrypt_pii(notes) AS notes
FROM patient_records
WHERE medical_record_number = 'MRN-2025-001';
```

### Crittografia Asimmetrica con pgcrypto

```sql
-- Crittografia asimmetrica: più chiavi pubbliche possono crittografare,
-- ma solo chi ha la chiave privata può leggere

-- Generare una coppia di chiavi RSA (in PostgreSQL o esternamente)
-- Solitamente le chiavi sono generate esternamente e caricate nel database

-- Crittografare con chiave pubblica
INSERT INTO sensitive_messages (recipient, content)
VALUES (
  'mario.rossi@example.com',
  pgp_pub_encrypt(
    'Messaggio confidenziale per Mario',
    dearmor('-----BEGIN PGP PUBLIC KEY BLOCK-----
...blocco chiave pubblica...
-----END PGP PUBLIC KEY BLOCK-----')
  )
);

-- Decrittografare richiede la chiave privata
-- La chiave privata non è mai nel database: la decrittografia avviene lato applicazione
SELECT
  pgp_pub_decrypt(
    content,
    dearmor('-----BEGIN PGP PRIVATE KEY BLOCK-----
...blocco chiave privata...
-----END PGP PRIVATE KEY BLOCK-----'),
    'passphrase-chiave-privata'
  ) AS message_plain
FROM sensitive_messages
WHERE recipient = 'mario.rossi@example.com';
```

## Key Management

La crittografia è utile solo quanto la gestione delle chiavi. Una chiave persa significa dati persi. Una chiave compromessa significa dati violati.

### Integrazione con HashiCorp Vault

```python
import hvac
import psycopg2
from functools import lru_cache
import time

class VaultKeyManager:
    """
    Gestisce le chiavi di crittografia tramite HashiCorp Vault.
    Le chiavi non vengono mai memorizzate nell'applicazione in modo permanente.
    """
    
    def __init__(self, vault_addr: str, vault_token: str):
        self.client = hvac.Client(url=vault_addr, token=vault_token)
        self._key_cache: dict = {}
        self._cache_ttl = 300  # 5 minuti
    
    def get_encryption_key(self, key_name: str = 'patient-data-key') -> str:
        """
        Recupera la chiave di crittografia da Vault.
        Vault gestisce la rotazione automatica delle chiavi.
        """
        cache_entry = self._key_cache.get(key_name)
        if cache_entry and (time.time() - cache_entry['fetched_at']) < self._cache_ttl:
            return cache_entry['value']
        
        # Recuperare da Vault
        response = self.client.secrets.transit.read_key(name=key_name)
        # Per il key material effettivo, usare il metodo export (solo se necessario)
        # Meglio: usare Vault Transit per crittografare/decrittografare senza mai esporre la chiave
        
        # Vault Transit: crittografa/decrittografa senza esporre il key material
        return self._use_vault_transit(key_name)
    
    def encrypt(self, plaintext: str, key_name: str = 'patient-data-key') -> str:
        """Crittografa tramite Vault Transit API."""
        import base64
        plaintext_b64 = base64.b64encode(plaintext.encode()).decode()
        
        response = self.client.secrets.transit.encrypt_data(
            name=key_name,
            plaintext=plaintext_b64
        )
        return response['data']['ciphertext']  # es. "vault:v2:abc123..."
    
    def decrypt(self, ciphertext: str, key_name: str = 'patient-data-key') -> str:
        """Decrittografa tramite Vault Transit API."""
        import base64
        
        response = self.client.secrets.transit.decrypt_data(
            name=key_name,
            ciphertext=ciphertext
        )
        plaintext_b64 = response['data']['plaintext']
        return base64.b64decode(plaintext_b64).decode()

# Uso nell'applicazione
vault = VaultKeyManager('https://vault.example.com', os.environ['VAULT_TOKEN'])

# Crittografare prima di salvare nel database
encrypted_ssn = vault.encrypt('123-45-6789')
# Valore: "vault:v2:hvs.CAESINhbDKwxWmjCJWlE..."
# Il ciphertext include la versione della chiave: la rotazione è automatica

# Inserire nel database (il ciphertext è testo, non bytea)
with psycopg2.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO patients (name, ssn_encrypted) VALUES (%s, %s)",
            ('Mario Rossi', encrypted_ssn)
        )

# Decrittografare alla lettura
with psycopg2.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT ssn_encrypted FROM patients WHERE id = %s", (patient_id,))
        row = cur.fetchone()
        ssn = vault.decrypt(row[0])
```

### Rotazione delle Chiavi

```python
# Vault Transit supporta la rotazione automatica delle chiavi
# I dati crittografati con versioni precedenti possono essere riletti
# e poi ricrittografati con la nuova versione (rewrap)

def rotate_and_rewrap_keys(vault: VaultKeyManager, key_name: str):
    """
    1. Ruota la chiave in Vault (crea una nuova versione)
    2. Riletti i dati con la vecchia versione
    3. Li ricrittografa con la nuova versione
    """
    # 1. Ruotare la chiave in Vault (non espone mai il key material)
    vault.client.secrets.transit.rotate_key(name=key_name)
    
    # 2. Recuperare i dati da ricrittografare
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, ssn_encrypted FROM patients WHERE ssn_encrypted LIKE 'vault:v1:%'")
            rows = cur.fetchall()
    
    # 3. Rewrap: decrittografare con v1 e ricrittografare con v2
    for patient_id, old_ciphertext in rows:
        new_ciphertext = vault.client.secrets.transit.rewrap_data(
            name=key_name,
            ciphertext=old_ciphertext
        )['data']['ciphertext']
        
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE patients SET ssn_encrypted = %s WHERE id = %s",
                    (new_ciphertext, patient_id)
                )
    
    # 4. Disabilitare la vecchia versione della chiave (non la cancella, ma non può più crittografare)
    vault.client.secrets.transit.update_key_configuration(
        name=key_name,
        min_decryption_version=2  # la v1 non può più essere usata per decrittografare
    )
```

## Mascheramento dei Dati (Data Masking)

Il mascheramento protegge i dati sensibili sostituendoli con dati fittizi in ambienti non-produzione.

```sql
-- Mascheramento per ambiente di test/staging
-- Funzione di mascheramento dell'email che preserva il dominio
CREATE OR REPLACE FUNCTION mask_email(email TEXT) RETURNS TEXT AS $$
BEGIN
  IF email IS NULL THEN RETURN NULL; END IF;
  RETURN CONCAT(
    REPEAT('*', LENGTH(SPLIT_PART(email, '@', 1))),
    '@',
    SPLIT_PART(email, '@', 2)
  );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Mascheramento del SSN (mantiene solo gli ultimi 4 caratteri)
CREATE OR REPLACE FUNCTION mask_ssn(ssn TEXT) RETURNS TEXT AS $$
BEGIN
  IF ssn IS NULL OR LENGTH(ssn) < 4 THEN RETURN '***-**-****'; END IF;
  RETURN CONCAT('***-**-', RIGHT(ssn, 4));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Vista mascherata per l'ambiente di sviluppo
CREATE VIEW dev_patients AS
SELECT
  id,
  'Patient-' || id::TEXT AS name,     -- nome fittizio
  mask_ssn(ssn) AS ssn,               -- SSN mascherato
  date_of_birth,                       -- data OK per testing
  medical_record_number,               -- numero record OK
  CURRENT_DATE - (RANDOM() * 1000)::int AS artificial_dob  -- data di nascita randomizzata
FROM patients;

-- Revocare l'accesso alla tabella reale per gli sviluppatori
REVOKE SELECT ON patients FROM developer_role;
GRANT SELECT ON dev_patients TO developer_role;
```

