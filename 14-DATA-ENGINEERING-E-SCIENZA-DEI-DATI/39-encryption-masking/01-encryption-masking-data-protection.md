# Encryption, Data Masking, and Tokenization for Data Systems

## Table of Contents

1. [Encryption Fundamentals for Data Engineers](#1-encryption-fundamentals-for-data-engineers)
2. [Database Encryption](#2-database-encryption)
3. [Encryption at Rest](#3-encryption-at-rest)
4. [Encryption in Transit](#4-encryption-in-transit)
5. [Key Management](#5-key-management)
6. [Data Masking](#6-data-masking)
7. [Tokenization](#7-tokenization)
8. [Data Anonymization vs Pseudonymization](#8-data-anonymization-vs-pseudonymization)
9. [Attack Vectors Against Encrypted Data](#9-attack-vectors-against-encrypted-data)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Encryption Fundamentals for Data Engineers

Encryption is the mathematical transformation of plaintext into ciphertext using an algorithm (cipher) and a key. For data engineers, understanding encryption is not optional — it is a core competency that directly affects system design, pipeline architecture, compliance posture, and incident response capability.

### 1.1 Symmetric Encryption

Symmetric encryption uses the same key for both encryption and decryption. It is the workhorse of data-at-rest and bulk data encryption due to its superior throughput compared to asymmetric alternatives.

#### AES (Advanced Encryption Standard)

AES operates on 128-bit blocks with key sizes of 128, 192, or 256 bits. The algorithm performs substitution-permutation rounds (10, 12, or 14 rounds depending on key size).

**AES-128** provides 2^128 key space — sufficient against brute-force for the foreseeable future barring quantum computing advances. AES-256 doubles the key schedule complexity and provides quantum resistance margin (Grover's algorithm reduces effective security to 128-bit equivalent).

**Block cipher modes** critical for data engineering:

- **GCM (Galois/Counter Mode):** Authenticated encryption with associated data (AEAD). Provides confidentiality + integrity + authentication in a single pass. Standard for TLS 1.3, database encryption, and cloud KMS operations. Produces a 128-bit authentication tag. Nonce must never repeat for the same key — catastrophic if violated (key stream reuse).

- **CBC (Cipher Block Chaining):** Legacy but still encountered in TDE implementations. Requires separate HMAC for integrity. Vulnerable to padding oracle attacks if error messages leak padding validity.

- **CTR (Counter Mode):** Turns block cipher into stream cipher. Parallelizable, no padding needed. Foundation of GCM. Nonce reuse is equally catastrophic.

- **XTS (XEX-based Tweaked-codebook mode with Ciphertext Stealing):** Purpose-built for disk encryption. Used by LUKS, BitLocker, FileVault. Each sector gets a unique tweak value preventing ECB-like patterns.

```python
# AES-256-GCM encryption with Python cryptography library
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = AESGCM.generate_key(bit_length=256)  # 32 bytes
nonce = os.urandom(12)  # 96-bit nonce for GCM
aad = b"table:users,column:ssn,row:42"  # associated data for context binding

aesgcm = AESGCM(key)
ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, aad)
# ciphertext includes 16-byte auth tag appended

# Decryption — will raise InvalidTag if tampered
plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
```

#### ChaCha20-Poly1305

A stream cipher designed by Daniel Bernstein. 256-bit key, 96-bit nonce, 32-bit counter. Combined with Poly1305 MAC for authenticated encryption.

**Advantages over AES-GCM:**
- No timing side-channels from lookup tables (pure ARX operations: add, rotate, XOR)
- Faster in software on platforms without AES-NI hardware instructions (mobile, IoT, older ARM)
- Same security level with simpler implementation (fewer footguns)

**When to choose ChaCha20:**
- Software-only environments without hardware AES acceleration
- Embedded data collection agents running on ARM without crypto extensions
- Environments where constant-time AES is difficult to guarantee

```python
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

key = ChaCha20Poly1305.generate_key()  # 32 bytes
chacha = ChaCha20Poly1305(key)
nonce = os.urandom(12)
ciphertext = chacha.encrypt(nonce, data, associated_data)
```

### 1.2 Asymmetric Encryption

Asymmetric (public-key) encryption uses mathematically related key pairs: a public key for encryption/verification and a private key for decryption/signing.

#### RSA

Based on the difficulty of factoring large semiprimes. Minimum 2048-bit keys for current security (NIST recommends 3072+ for use beyond 2030).

**RSA-OAEP** (Optimal Asymmetric Encryption Padding): The only acceptable RSA encryption padding. PKCS#1 v1.5 padding is vulnerable to Bleichenbacher's adaptive chosen-ciphertext attack and must not be used in new systems.

RSA encryption is limited to small payloads (key_size/8 - 2*hash_size - 2 bytes). For RSA-2048 with SHA-256: maximum 190 bytes of plaintext. This is why hybrid encryption exists.

#### Elliptic Curve Cryptography

ECC provides equivalent security to RSA with dramatically smaller key sizes:

| Security Level | RSA Key Size | ECC Key Size |
|---------------|-------------|-------------|
| 128-bit | 3072 | 256 |
| 192-bit | 7680 | 384 |
| 256-bit | 15360 | 521 |

**ECDSA (Elliptic Curve Digital Signature Algorithm):** Widely deployed for signing. Curves: P-256 (NIST), P-384, P-521. Requires cryptographically secure random nonce per signature — nonce reuse or bias leaks private key (see PlayStation 3 ECDSA break, 2010).

**Ed25519 (EdDSA on Curve25519):** Deterministic signatures (nonce derived from private key + message via hash), eliminating the nonce-reuse vulnerability class entirely. Faster than ECDSA, smaller signatures (64 bytes), constant-time by design. Preferred for new systems.

**X25519 (ECDH on Curve25519):** Key agreement protocol. Two parties derive a shared secret from their private keys and the other's public key. Foundation of modern TLS key exchange and Signal protocol.

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Key generation
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Signing
signature = private_key.sign(data)

# Verification (raises InvalidSignature if tampered)
public_key.verify(signature, data)
```

### 1.3 Hybrid Encryption

Combines asymmetric and symmetric encryption to get the best properties of both:

1. Generate a random symmetric key (DEK — Data Encryption Key)
2. Encrypt the data with the DEK using AES-GCM or ChaCha20-Poly1305
3. Encrypt the DEK with the recipient's public key (RSA-OAEP or ECIES)
4. Transmit both encrypted DEK and encrypted data

This is the pattern behind PGP/GPG, TLS, envelope encryption in cloud KMS, and most real-world cryptosystems.

```python
# Hybrid encryption pattern
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# Sender side
dek = os.urandom(32)  # Random AES-256 key
encrypted_data = aesgcm_encrypt(dek, nonce, plaintext)
encrypted_dek = recipient_public_key.encrypt(
    dek,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

# Recipient side
dek = recipient_private_key.decrypt(encrypted_dek, padding.OAEP(...))
plaintext = aesgcm_decrypt(dek, nonce, encrypted_data)
```

### 1.4 Key Derivation Functions (KDFs)

KDFs transform passwords or low-entropy secrets into cryptographic keys. They are deliberately slow to resist brute-force attacks.

#### PBKDF2 (Password-Based Key Derivation Function 2)

RFC 8018. Iterates HMAC-SHA256 (or SHA512) a configured number of times. NIST recommends minimum 600,000 iterations for PBKDF2-HMAC-SHA256 (2023 guidance). Simple but GPU-parallelizable — inferior to memory-hard alternatives for password hashing.

#### scrypt

Memory-hard KDF. Parameters: N (CPU/memory cost), r (block size), p (parallelization). Designed to resist ASIC/GPU attacks by requiring large amounts of memory proportional to computation. Minimum recommended: N=2^15, r=8, p=1 (32 MB memory).

#### Argon2

Winner of the Password Hashing Competition (2015). Three variants:
- **Argon2d:** Data-dependent memory access (faster, vulnerable to side-channel)
- **Argon2i:** Data-independent memory access (side-channel resistant, slower)
- **Argon2id:** Hybrid — first pass is Argon2i, subsequent passes are Argon2d

**Argon2id is the recommended default.** Parameters: memory (minimum 64 MB for interactive, 1 GB for sensitive), iterations (minimum 3), parallelism (number of threads).

```python
import argon2

# Password hashing for authentication
hasher = argon2.PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    type=argon2.Type.ID  # Argon2id
)

hash_value = hasher.hash("user_password")
# $argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>

# Key derivation for encryption
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
kdf = Scrypt(salt=salt, length=32, n=2**15, r=8, p=1)
key = kdf.derive(password.encode())
```

### 1.5 Envelope Encryption Pattern

The foundational pattern for scalable encryption in data systems:

```
                    ┌─────────────────┐
                    │   Master Key    │  ← Stored in HSM/KMS
                    │   (Root Key)    │  ← Never leaves secure boundary
                    └────────┬────────┘
                             │ encrypts
                    ┌────────▼────────┐
                    │  Key Encryption │  ← KEK: encrypts/wraps DEKs
                    │    Key (KEK)    │  ← Cached in memory briefly
                    └────────┬────────┘
                             │ encrypts
                    ┌────────▼────────┐
                    │ Data Encryption │  ← DEK: encrypts actual data
                    │    Key (DEK)    │  ← Unique per object/record
                    └────────┬────────┘
                             │ encrypts
                    ┌────────▼────────┐
                    │    Your Data    │
                    └─────────────────┘
```

**Benefits:**
- Key rotation only requires re-encrypting the DEK wrapper, not all data
- Different data classifications can use different KEKs under the same master
- Master key never leaves HSM boundary — only unwrap operations cross the border
- Compromise of a single DEK exposes only that data object, not the entire corpus

---

## 2. Database Encryption

### 2.1 Transparent Data Encryption (TDE)

TDE encrypts data at the storage layer without application code changes. The database engine handles encrypt/decrypt transparently during I/O operations.

#### PostgreSQL with pgcrypto

PostgreSQL does not have built-in TDE (as of PG 16). Options:

1. **pgcrypto extension** — column-level encryption via SQL functions
2. **File-system level encryption** (LUKS, dm-crypt)
3. **Third-party TDE patches** (Cybertec TDE, PostgreSQL TDE fork)

```sql
-- Enable pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Symmetric encryption with AES-256-CBC (pgcrypto default)
INSERT INTO sensitive_data (id, encrypted_ssn)
VALUES (1, pgp_sym_encrypt('123-45-6789', 'encryption_key_here', 'cipher-algo=aes256'));

-- Decryption
SELECT pgp_sym_decrypt(encrypted_ssn, 'encryption_key_here') AS ssn
FROM sensitive_data WHERE id = 1;

-- Asymmetric encryption with PGP keys
-- Generate keypair externally, import public key
INSERT INTO sensitive_data (id, encrypted_payload)
VALUES (1, pgp_pub_encrypt('secret data', dearmor(public_key_text)));

-- Decrypt with private key (requires passphrase)
SELECT pgp_pub_decrypt(encrypted_payload, dearmor(private_key_text), 'passphrase')
FROM sensitive_data WHERE id = 1;
```

**Performance impact of pgcrypto:**
- AES-256 column encryption: 15-40% overhead on INSERT/UPDATE for encrypted columns
- Decryption on SELECT: 10-25% overhead depending on result set size
- Cannot use indexes on encrypted columns (encrypted values differ each time due to random IV)
- Workaround: store a HMAC of the value for equality lookups (blind index pattern)

#### MySQL / InnoDB TDE

MySQL 8.0+ supports tablespace-level TDE with the keyring plugin:

```sql
-- Enable InnoDB tablespace encryption
ALTER TABLE customers ENCRYPTION='Y';

-- Verify encryption status
SELECT TABLE_SCHEMA, TABLE_NAME, CREATE_OPTIONS
FROM INFORMATION_SCHEMA.TABLES
WHERE CREATE_OPTIONS LIKE '%ENCRYPTION%';

-- Configure keyring (in my.cnf)
-- early-plugin-load=keyring_encrypted_file.so
-- keyring_encrypted_file_data=/var/lib/mysql-keyring/keyring-encrypted
-- keyring_encrypted_file_password=master_password_here
```

**MySQL TDE architecture:**
- Each tablespace has its own tablespace key (DEK)
- Tablespace keys are encrypted by the master encryption key (MEK)
- MEK stored in keyring plugin (file, HashiCorp Vault, AWS KMS, OCI Vault)
- Redo logs and undo logs can also be encrypted
- Binary logs support encryption (binlog_encryption=ON)

**Performance benchmarks (MySQL 8.0, NVMe SSD):**
| Workload | No Encryption | TDE Enabled | Overhead |
|----------|--------------|-------------|----------|
| OLTP Read-Heavy | 45,000 TPS | 43,200 TPS | 4% |
| OLTP Write-Heavy | 12,000 TPS | 11,100 TPS | 7.5% |
| Bulk INSERT | 180 MB/s | 165 MB/s | 8.3% |
| Full Table Scan | 2.1 GB/s | 1.95 GB/s | 7.1% |

#### SQL Server TDE

SQL Server has mature TDE since 2008:

```sql
-- Create master key in master database
USE master;
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'StrongP@ssw0rd!';

-- Create certificate for TDE
CREATE CERTIFICATE TDE_Cert WITH SUBJECT = 'TDE Certificate';

-- Create database encryption key
USE target_database;
CREATE DATABASE ENCRYPTION KEY
WITH ALGORITHM = AES_256
ENCRYPTION BY SERVER CERTIFICATE TDE_Cert;

-- Enable TDE
ALTER DATABASE target_database SET ENCRYPTION ON;

-- Monitor encryption progress
SELECT db_name(database_id), encryption_state, percent_complete
FROM sys.dm_database_encryption_keys;
```

**Encryption states:** 0=unencrypted, 1=unencrypted (key exists), 2=encryption in progress, 3=encrypted, 4=key change in progress, 5=decryption in progress.

#### Oracle TDE

Oracle Advanced Security (extra-cost option):

```sql
-- Configure wallet (Oracle 12c+: keystore)
ADMINISTER KEY MANAGEMENT CREATE KEYSTORE '/opt/oracle/wallet'
IDENTIFIED BY wallet_password;

ADMINISTER KEY MANAGEMENT SET KEY IDENTIFIED BY wallet_password
WITH BACKUP;

-- Column-level encryption
ALTER TABLE customers MODIFY (ssn ENCRYPT SALT);

-- Tablespace encryption
CREATE TABLESPACE secure_ts DATAFILE '/data/secure01.dbf'
SIZE 100M ENCRYPTION USING 'AES256' DEFAULT STORAGE(ENCRYPT);
```

### 2.2 Column-Level vs Full-Disk Encryption

| Aspect | Column-Level | Full-Disk (TDE/LUKS) |
|--------|-------------|---------------------|
| Granularity | Per-column, per-row | Entire volume |
| Key management | Application-managed | OS/DB-managed |
| Index support | Limited (blind indexes) | Full index support |
| Performance | Higher per-query overhead | Near-zero overhead |
| Protection scope | Protects against DB admin | Protects against disk theft |
| Compliance | Meets field-level requirements | Meets at-rest requirements |
| Query flexibility | Cannot query encrypted values | Full SQL capability |

**Decision framework:**
- Use full-disk/TDE when: protecting against physical media theft, meeting basic compliance checkboxes, performance is critical
- Use column-level when: DBAs should not see sensitive fields, different columns need different access controls, regulatory requirement for field-level encryption (PCI-DSS for cardholder data)

### 2.3 Always Encrypted (SQL Server)

Client-side encryption where the database engine never sees plaintext:

```csharp
// Connection string enables Always Encrypted
string connStr = "Server=...;Column Encryption Setting=enabled;";

// Driver automatically encrypts parameters and decrypts results
using (SqlCommand cmd = new SqlCommand(
    "SELECT Name, SSN FROM Patients WHERE SSN = @ssn", conn))
{
    cmd.Parameters.AddWithValue("@ssn", "123-45-6789");
    // Driver encrypts @ssn before sending to server
    // Server processes query on ciphertext
    // Driver decrypts SSN in result set
}
```

**Encryption types:**
- **Deterministic:** Same plaintext always produces same ciphertext. Enables equality comparisons, JOINs, GROUP BY, indexing. Vulnerable to frequency analysis.
- **Randomized:** Different ciphertext each time. Stronger security but no server-side operations possible.

**Key hierarchy:**
- Column Encryption Key (CEK): encrypts column data
- Column Master Key (CMK): protects CEK, stored in Windows Certificate Store, Azure Key Vault, or HSM

### 2.4 MongoDB Client-Side Field Level Encryption (CSFLE)

MongoDB 4.2+ supports automatic client-side encryption:

```javascript
// CSFLE configuration
const kmsProviders = {
  aws: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  },
};

const schemaMap = {
  "mydb.patients": {
    bsonType: "object",
    encryptMetadata: { keyId: [dataKeyId] },
    properties: {
      ssn: {
        encrypt: {
          bsonType: "string",
          algorithm: "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
        },
      },
      medicalRecords: {
        encrypt: {
          bsonType: "array",
          algorithm: "AEAD_AES_256_CBC_HMAC_SHA_512-Random",
        },
      },
    },
  },
};

const client = new MongoClient(uri, {
  autoEncryption: {
    kmsProviders,
    keyVaultNamespace: "encryption.__keyVault",
    schemaMap,
  },
});
```

**CSFLE algorithms:**
- Deterministic: equality queries work, same plaintext = same ciphertext
- Random: no query capability, maximum security for sensitive fields
- Both use AES-256-CBC with HMAC-SHA-512 for authenticated encryption

**Queryable Encryption (MongoDB 7.0+):** Extends CSFLE with range queries and equality queries on randomized encryption using structured encryption techniques. Uses a metadata collection to enable encrypted search without revealing plaintext to the server.

---

## 3. Encryption at Rest

### 3.1 Linux Volume Encryption — LUKS

LUKS (Linux Unified Key Setup) is the standard for Linux disk encryption, built on dm-crypt:

```bash
# Create encrypted partition
cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --hash sha256 \
  --pbkdf argon2id \
  --pbkdf-memory 1048576 \
  --pbkdf-parallel 4 \
  /dev/sdb1

# Open (unlock) the encrypted volume
cryptsetup luksOpen /dev/sdb1 encrypted_data

# Create filesystem
mkfs.ext4 /dev/mapper/encrypted_data
mount /dev/mapper/encrypted_data /mnt/secure

# Add additional key slot (LUKS supports 8 key slots)
cryptsetup luksAddKey /dev/sdb1

# Key rotation: add new key, then remove old slot
cryptsetup luksAddKey /dev/sdb1        # adds to next free slot
cryptsetup luksRemoveKey /dev/sdb1     # prompts for passphrase to remove
```

**LUKS2 improvements over LUKS1:**
- Argon2id as default KDF (LUKS1 uses PBKDF2)
- JSON metadata area with redundancy
- Authenticated encryption for metadata
- Token support for external key retrieval (FIDO2, TPM2, Tang/Clevis)
- Online re-encryption capability

**Performance considerations:**
- AES-XTS with AES-NI: negligible CPU overhead (< 3% throughput loss)
- Without AES-NI: 15-30% throughput reduction on sustained sequential I/O
- Random I/O: overhead is masked by storage latency on spinning disks; measurable on NVMe

### 3.2 Cloud Provider Encryption at Rest

#### AWS KMS + EBS Encryption

```bash
# Create a Customer Managed Key (CMK)
aws kms create-key \
  --description "Data pipeline encryption key" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT \
  --multi-region false

# Create encrypted EBS volume
aws ec2 create-volume \
  --volume-type gp3 \
  --size 500 \
  --encrypted \
  --kms-key-id arn:aws:kms:us-east-1:123456789:key/uuid-here \
  --availability-zone us-east-1a

# Enable default EBS encryption for the account
aws ec2 enable-ebs-encryption-by-default
aws ec2 modify-ebs-default-kms-key-id --kms-key-id arn:aws:kms:...

# S3 bucket encryption with CMK
aws s3api put-bucket-encryption \
  --bucket data-lake-production \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:us-east-1:123456789:key/uuid"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

**S3 Bucket Keys:** Reduce KMS API calls by generating a bucket-level key from the CMK. This key encrypts object-level DEKs, reducing cost by up to 99% for high-volume buckets.

#### GCP Customer-Managed Encryption Keys (CMEK)

```bash
# Create keyring and key
gcloud kms keyrings create data-pipeline-ring \
  --location us-central1

gcloud kms keys create pipeline-encryption-key \
  --keyring data-pipeline-ring \
  --location us-central1 \
  --purpose encryption \
  --rotation-period 90d \
  --next-rotation-time "2024-04-01T00:00:00Z"

# Encrypt a disk with CMEK
gcloud compute disks create data-disk \
  --size 500GB \
  --type pd-ssd \
  --kms-key projects/my-project/locations/us-central1/keyRings/data-pipeline-ring/cryptoKeys/pipeline-encryption-key

# BigQuery dataset with CMEK
bq mk --dataset \
  --default_kms_key=projects/my-project/locations/us/keyRings/ring/cryptoKeys/key \
  my_project:encrypted_dataset
```

#### Azure Key Vault Integration

```bash
# Create Key Vault
az keyvault create \
  --name data-pipeline-vault \
  --resource-group data-rg \
  --location eastus \
  --sku premium  # HSM-backed keys

# Create encryption key
az keyvault key create \
  --vault-name data-pipeline-vault \
  --name disk-encryption-key \
  --ktype RSA \
  --size 4096

# Enable disk encryption set
az disk-encryption-set create \
  --name data-des \
  --resource-group data-rg \
  --key-url "https://data-pipeline-vault.vault.azure.net/keys/disk-encryption-key/version" \
  --source-vault "/subscriptions/.../vaults/data-pipeline-vault"
```

### 3.3 Key Hierarchy Architecture

```
┌─────────────────────────────────────────────────┐
│                HSM / CloudHSM                    │
│  ┌───────────────────────────────────────────┐  │
│  │          Root Key (Master Key)            │  │
│  │  - Never exported                         │  │
│  │  - Hardware-bound                         │  │
│  │  - FIPS 140-2 Level 3 / Level 4          │  │
│  └──────────────────┬────────────────────────┘  │
└─────────────────────┼───────────────────────────┘
                      │ wraps/unwraps
         ┌────────────▼────────────┐
         │    Key Encryption Keys   │
         │    (KEKs / Wrapping Keys)│
         │  - Per-service or per-   │
         │    data-classification   │
         │  - Rotated quarterly     │
         │  - Cached in memory      │
         └────────────┬─────────────┘
                      │ wraps/unwraps
         ┌────────────▼────────────┐
         │   Data Encryption Keys   │
         │         (DEKs)           │
         │  - Per-object/per-row    │
         │  - Ephemeral             │
         │  - Stored encrypted      │
         │    alongside data        │
         └──────────────────────────┘
```

### 3.4 Hardware Security Modules (HSM)

HSMs are tamper-resistant hardware devices that perform cryptographic operations and store keys securely:

**FIPS 140-2/140-3 Levels:**
- Level 1: Software-only, no physical security
- Level 2: Tamper-evident seals, role-based auth
- Level 3: Tamper-resistant, identity-based auth, physical key zeroization on breach attempt
- Level 4: Environmental failure protection, active tamper response

**Cloud HSM options:**
- AWS CloudHSM: Dedicated HSM instances in your VPC, FIPS 140-2 Level 3
- GCP Cloud HSM: FIPS 140-2 Level 3, integrated with Cloud KMS
- Azure Dedicated HSM: Thales Luna Network HSMs, FIPS 140-2 Level 3

```python
# AWS CloudHSM PKCS#11 usage pattern
import pkcs11

lib = pkcs11.lib('/opt/cloudhsm/lib/libcloudhsm_pkcs11.so')
token = lib.get_token(token_label='hsm_partition')

with token.open(user_pin='crypto_user_password') as session:
    # Generate AES key in HSM (never leaves hardware)
    key = session.generate_key(
        pkcs11.KeyType.AES, 256,
        label='data-pipeline-dek',
        store=True,
        capabilities=[pkcs11.Mechanism.AES_GCM]
    )
    
    # Encrypt data — operation happens inside HSM
    ciphertext = key.encrypt(plaintext, mechanism=pkcs11.Mechanism.AES_GCM)
```

---

## 4. Encryption in Transit

### 4.1 TLS 1.3 for Database Connections

TLS 1.3 reduces handshake to one round-trip (1-RTT) or zero (0-RTT for resumed sessions). Removes insecure cipher suites, mandates forward secrecy.

#### PostgreSQL TLS Configuration

```ini
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
ssl_min_protocol_version = 'TLSv1.3'
ssl_ciphers = 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256'

# pg_hba.conf — enforce SSL for all remote connections
hostssl all         all    0.0.0.0/0    scram-sha-256 clientcert=verify-full
hostssl replication rep    10.0.0.0/8   scram-sha-256 clientcert=verify-full
```

```bash
# Client connection with certificate verification
psql "host=db.example.com \
      port=5432 \
      dbname=production \
      user=app_user \
      sslmode=verify-full \
      sslcert=/etc/ssl/client.crt \
      sslkey=/etc/ssl/client.key \
      sslrootcert=/etc/ssl/ca.crt"
```

**sslmode levels:**
- `disable`: No SSL (never acceptable for production)
- `allow`: Try non-SSL first, fall back to SSL
- `prefer`: Try SSL first, fall back to non-SSL (default — dangerous)
- `require`: SSL required, no certificate verification (MITM vulnerable)
- `verify-ca`: SSL + verify server certificate against CA
- `verify-full`: SSL + verify certificate + verify hostname matches (required for production)

#### MySQL TLS Configuration

```ini
# my.cnf [mysqld]
require_secure_transport = ON
tls_version = TLSv1.3
ssl_cert = /etc/mysql/server-cert.pem
ssl_key = /etc/mysql/server-key.pem
ssl_ca = /etc/mysql/ca-cert.pem

# Require client certificates for replication
[mysqld]
ssl_cipher = TLS_AES_256_GCM_SHA384

# Per-user enforcement
ALTER USER 'app_user'@'%' REQUIRE X509;
ALTER USER 'replication_user'@'10.%' REQUIRE ISSUER '/CN=Internal CA' SUBJECT '/CN=replica1';
```

### 4.2 Mutual TLS (mTLS) Between Services

In data pipelines, mTLS authenticates both client and server. Essential for service-to-service communication in zero-trust architectures.

```yaml
# Example: Kafka with mTLS (server.properties)
listeners=SSL://0.0.0.0:9093
ssl.keystore.location=/etc/kafka/kafka.server.keystore.jks
ssl.keystore.password=${KEYSTORE_PASS}
ssl.key.password=${KEY_PASS}
ssl.truststore.location=/etc/kafka/kafka.server.truststore.jks
ssl.truststore.password=${TRUSTSTORE_PASS}
ssl.client.auth=required
ssl.enabled.protocols=TLSv1.3
ssl.protocol=TLSv1.3

# Kafka producer with mTLS (Python)
from confluent_kafka import Producer

config = {
    'bootstrap.servers': 'kafka:9093',
    'security.protocol': 'SSL',
    'ssl.ca.location': '/etc/ssl/ca.pem',
    'ssl.certificate.location': '/etc/ssl/client.pem',
    'ssl.key.location': '/etc/ssl/client.key',
    'ssl.key.password': 'key_passphrase',
}
producer = Producer(config)
```

### 4.3 Certificate Management for Data Pipelines

```bash
# Generate CA (internal PKI for data infrastructure)
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
  -days 3650 -nodes -keyout ca.key -out ca.crt \
  -subj "/CN=Data Pipeline Internal CA/O=DataOps"

# Generate server certificate
openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
  -nodes -keyout server.key -out server.csr \
  -subj "/CN=postgres-primary.internal/O=DataOps"

# Sign with SAN (Subject Alternative Names)
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365 \
  -extfile <(printf "subjectAltName=DNS:postgres-primary.internal,DNS:pg-01.internal,IP:10.0.1.50")

# Generate client certificate for pipeline service
openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
  -nodes -keyout pipeline.key -out pipeline.csr \
  -subj "/CN=etl-service/O=DataOps/OU=Pipeline"

openssl x509 -req -in pipeline.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out pipeline.crt -days 90
```

**Certificate rotation strategy:**
- CA certificates: 5-10 year validity, offline storage
- Server certificates: 90-365 days, automated renewal (cert-manager, Vault PKI)
- Client certificates: 30-90 days, rotated via CI/CD pipeline
- Short-lived certificates (< 24h): ideal for ephemeral pipeline workers

### 4.4 WireGuard for Replication Traffic

WireGuard provides kernel-level encrypted tunnels with minimal overhead — ideal for database replication across availability zones or regions:

```ini
# /etc/wireguard/wg-replication.conf (Primary)
[Interface]
PrivateKey = <primary_private_key>
Address = 10.200.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <replica_public_key>
AllowedIPs = 10.200.0.2/32
Endpoint = replica.example.com:51820
PersistentKeepalive = 25

# /etc/wireguard/wg-replication.conf (Replica)
[Interface]
PrivateKey = <replica_private_key>
Address = 10.200.0.2/24
ListenPort = 51820

[Peer]
PublicKey = <primary_public_key>
AllowedIPs = 10.200.0.1/32
Endpoint = primary.example.com:51820
PersistentKeepalive = 25
```

```bash
# PostgreSQL replication over WireGuard
# primary postgresql.conf
listen_addresses = '10.200.0.1'  # WireGuard interface only

# replica recovery.conf
primary_conninfo = 'host=10.200.0.1 port=5432 user=replicator sslmode=verify-full'
```

**WireGuard vs TLS for replication:**
- WireGuard: Lower latency (kernel-space), simpler config, no certificate management
- TLS: Application-aware, fine-grained per-connection control, industry standard compliance
- Recommendation: WireGuard for network layer + TLS for application layer (defense in depth)

---

## 5. Key Management

### 5.1 KMS Architecture

Key Management Systems provide centralized, auditable key lifecycle operations.

#### AWS KMS

```python
import boto3

kms = boto3.client('kms', region_name='us-east-1')

# Generate data key (envelope encryption)
response = kms.generate_data_key(
    KeyId='alias/data-pipeline-key',
    KeySpec='AES_256',
    EncryptionContext={
        'service': 'etl-pipeline',
        'environment': 'production',
        'table': 'customers'
    }
)
plaintext_dek = response['Plaintext']      # Use for encryption, then discard
encrypted_dek = response['CiphertextBlob'] # Store alongside encrypted data

# Decrypt data key when needed
response = kms.decrypt(
    CiphertextBlob=encrypted_dek,
    EncryptionContext={
        'service': 'etl-pipeline',
        'environment': 'production',
        'table': 'customers'
    }
)
plaintext_dek = response['Plaintext']  # Use for decryption
```

**Encryption Context:** Additional authenticated data (AAD) bound to the ciphertext. Decryption fails if context doesn't match. Logged in CloudTrail for audit. Use to bind encrypted data to its purpose/location.

#### HashiCorp Vault

```bash
# Enable transit secrets engine
vault secrets enable transit

# Create encryption key
vault write transit/keys/pipeline-key \
  type=aes256-gcm96 \
  auto_rotate_period=90d

# Encrypt data
vault write transit/encrypt/pipeline-key \
  plaintext=$(echo -n "sensitive data" | base64)

# Response: ciphertext = vault:v1:base64encodedciphertext

# Decrypt data
vault write transit/decrypt/pipeline-key \
  ciphertext="vault:v1:base64encodedciphertext"

# Key rotation (new version created, old versions still decrypt)
vault write -f transit/keys/pipeline-key/rotate

# Rewrap ciphertext to latest key version (no plaintext exposure)
vault write transit/rewrap/pipeline-key \
  ciphertext="vault:v1:oldciphertext"
# Returns vault:v2:newciphertext
```

**Vault Transit vs AWS KMS:**
| Feature | Vault Transit | AWS KMS |
|---------|--------------|---------|
| Deployment | Self-hosted or HCP | Managed service |
| Latency | < 1ms (local) | 5-50ms (API call) |
| Throughput | 10,000+ ops/sec | 5,500-30,000 req/sec per key |
| Key export | Configurable | Never (by design) |
| Multi-cloud | Yes | AWS only |
| Audit | Vault audit log | CloudTrail |
| Cost | Infrastructure + license | Per-API-call |

### 5.2 Key Rotation Strategies

**Rotation types:**

1. **Manual rotation:** Administrator triggers rotation. Required for compliance events, suspected compromise.
2. **Automatic rotation:** KMS rotates on schedule (AWS: annual, configurable; Vault: configurable period).
3. **Re-encryption rotation:** Decrypt all data with old key, re-encrypt with new key. Required when old key version must be destroyed.

**Rotation without downtime (envelope encryption):**

```python
# Key rotation procedure for envelope encryption
def rotate_keys(kms_client, old_key_id, new_key_id, data_store):
    """Rotate KEK: re-wrap all DEKs without touching data."""
    for record in data_store.get_all_encrypted_deks():
        # Decrypt DEK with old KEK
        old_dek_plaintext = kms_client.decrypt(
            CiphertextBlob=record.encrypted_dek,
            KeyId=old_key_id
        )['Plaintext']
        
        # Re-encrypt DEK with new KEK
        new_encrypted_dek = kms_client.encrypt(
            KeyId=new_key_id,
            Plaintext=old_dek_plaintext
        )['CiphertextBlob']
        
        # Update stored wrapped DEK (data remains unchanged)
        data_store.update_dek(record.id, new_encrypted_dek)
        
        # Securely wipe DEK from memory
        del old_dek_plaintext
```

### 5.3 Key Lifecycle

```
Generation → Distribution → Storage → Use → Rotation → Archival → Destruction
    │             │            │        │        │          │           │
    ▼             ▼            ▼        ▼        ▼          ▼           ▼
 HSM/KMS    Secure channel  Encrypted  Audit   Schedule   Retain for  Crypto-
 CSPRNG     (TLS/mTLS)      at rest    all     based on   compliance  graphic
 FIPS       Envelope        HSM for    usage   risk       period      erasure
 approved   pattern         master                                    (zeroize)
```

**Key destruction:**
- Cryptographic erasure: destroy all copies of key, making encrypted data permanently inaccessible
- Faster and more reliable than deleting individual data records
- Critical for: decommissioning systems, GDPR right to erasure, tenant offboarding in multi-tenant systems
- AWS KMS: 7-30 day waiting period before key deletion (configurable, irreversible after)

### 5.4 BYOK vs Provider-Managed Keys

| Aspect | Provider-Managed | BYOK | External KMS (HYOK) |
|--------|-----------------|------|---------------------|
| Key generation | Cloud provider | Customer, imported | Customer's HSM |
| Key storage | Provider HSM | Provider HSM | Customer's HSM |
| Rotation | Provider handles | Customer responsibility | Customer responsibility |
| Audit | Provider logs | Provider logs | Full customer control |
| Compliance | Shared responsibility | Customer responsible | Customer responsible |
| Latency | Lowest | Same | Higher (external call) |
| Vendor lock-in | High | Medium | Low |
| Risk | Provider compromise | Import process | Availability depends on customer infra |

**BYOK import flow (AWS KMS):**

```bash
# 1. Create CMK with EXTERNAL origin
aws kms create-key --origin EXTERNAL --key-spec SYMMETRIC_DEFAULT

# 2. Get import parameters (wrapping key + import token)
aws kms get-parameters-for-import \
  --key-id <key-id> \
  --wrapping-algorithm RSAES_OAEP_SHA_256 \
  --wrapping-key-spec RSA_4096

# 3. Wrap your key material with the KMS wrapping public key
openssl pkeyutl -encrypt \
  -pubin -inkey wrapping_public_key.pem \
  -in key_material.bin \
  -out encrypted_key_material.bin \
  -pkeyopt rsa_padding_mode:oaep \
  -pkeyopt rsa_oaep_md:sha256

# 4. Import wrapped key material
aws kms import-key-material \
  --key-id <key-id> \
  --encrypted-key-material fileb://encrypted_key_material.bin \
  --import-token fileb://import_token.bin \
  --expiration-model KEY_MATERIAL_DOES_NOT_EXPIRE
```

### 5.5 Key Escrow

Key escrow stores copies of keys with a trusted third party for recovery scenarios:

**Legitimate use cases:**
- Business continuity (key holder unavailable)
- Legal compliance (lawful intercept requirements in some jurisdictions)
- Disaster recovery (HSM destruction)

**Implementation with Shamir's Secret Sharing:**

```python
# Split a master key into N shares where K are required to reconstruct
# Using shamir-mnemonic or secretsharing library
from secretsharing import PlaintextToHexSecretSharer

shares = PlaintextToHexSecretSharer.split_secret(
    master_key_hex,
    threshold=3,    # K: minimum shares needed
    num_shares=5    # N: total shares distributed
)
# Distribute shares to different custodians/locations
# Any 3 of 5 custodians can reconstruct the master key
```

---

## 6. Data Masking

### 6.1 Static Data Masking

Static masking permanently transforms sensitive data in non-production environments. The original values are irreversibly replaced.

**Use cases:**
- Populating dev/test databases from production backups
- Sharing datasets with third-party contractors
- Training ML models without exposing real PII

```sql
-- Static masking transformation examples (PostgreSQL)

-- Email masking: preserve domain, mask local part
UPDATE users SET email = 
  CONCAT(
    LEFT(MD5(email), 8),
    '@',
    SPLIT_PART(email, '@', 2)
  );

-- Name masking: consistent fake names from hash
UPDATE users SET 
  first_name = (ARRAY['Alex','Blake','Casey','Dana','Ellis'])[
    (ABS(HASHTEXT(first_name)) % 5) + 1
  ],
  last_name = (ARRAY['Smith','Jones','Brown','Davis','Wilson'])[
    (ABS(HASHTEXT(last_name)) % 5) + 1
  ];

-- SSN: format-preserving random
UPDATE users SET ssn = 
  LPAD((ABS(HASHTEXT(ssn || 'salt_value')) % 900000000 + 100000000)::TEXT, 9, '0');

-- Credit card: preserve BIN (first 6), mask middle, valid Luhn check digit
UPDATE payments SET card_number = 
  CONCAT(
    LEFT(card_number, 6),
    LPAD((RANDOM() * 999999)::INT::TEXT, 6, '0'),
    LPAD((RANDOM() * 999)::INT::TEXT, 3, '0'),
    '0'  -- simplified; production should compute Luhn
  );

-- Date shift: +-30 days random offset, preserving year
UPDATE patients SET date_of_birth = 
  date_of_birth + (FLOOR(RANDOM() * 61) - 30)::INT;

-- Address: generalize to ZIP code only
UPDATE users SET 
  street_address = 'REDACTED',
  city = 'REDACTED',
  state = state;  -- keep state for geographic analysis
```

**Static masking tools:**
- Open source: pgmasker, Jailer, DataMasker
- Commercial: Delphix, Informatica Data Masking, IBM Optim

### 6.2 Dynamic Data Masking

Dynamic masking applies transformations at query time based on the requesting user's role. The underlying data remains unchanged.

#### PostgreSQL Row-Level Security + Views

```sql
-- Create security policy for column masking via views
CREATE OR REPLACE VIEW public.customers_masked AS
SELECT 
  id,
  CASE 
    WHEN current_user IN ('admin', 'compliance_officer') THEN email
    ELSE CONCAT(LEFT(email, 2), '***@', SPLIT_PART(email, '@', 2))
  END AS email,
  CASE 
    WHEN current_user IN ('admin') THEN ssn
    WHEN current_user IN ('compliance_officer') THEN CONCAT('***-**-', RIGHT(ssn, 4))
    ELSE '***-**-****'
  END AS ssn,
  CASE 
    WHEN current_user IN ('admin', 'compliance_officer') THEN phone
    ELSE CONCAT('(***) ***-', RIGHT(phone, 4))
  END AS phone,
  first_name,
  last_name,
  created_at
FROM customers;

-- Row-Level Security for complete row filtering
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

CREATE POLICY customer_access ON customers
  FOR SELECT
  USING (
    current_user = 'admin'
    OR region = current_setting('app.user_region', true)
  );

-- Force RLS even for table owner
ALTER TABLE customers FORCE ROW LEVEL SECURITY;
```

#### SQL Server Dynamic Data Masking

```sql
-- Built-in dynamic masking (SQL Server 2016+)
CREATE TABLE Customers (
    ID INT PRIMARY KEY,
    FirstName VARCHAR(100) MASKED WITH (FUNCTION = 'partial(1, "****", 1)'),
    LastName VARCHAR(100),
    Email VARCHAR(256) MASKED WITH (FUNCTION = 'email()'),
    SSN CHAR(11) MASKED WITH (FUNCTION = 'partial(0, "XXX-XX-", 4)'),
    CreditCard CHAR(16) MASKED WITH (FUNCTION = 'partial(0, "XXXX-XXXX-XXXX-", 4)'),
    Phone VARCHAR(20) MASKED WITH (FUNCTION = 'default()'),
    Salary MONEY MASKED WITH (FUNCTION = 'random(10000, 90000)')
);

-- Grant unmask permission to specific roles
GRANT UNMASK TO [ComplianceOfficer];
GRANT UNMASK ON Customers(FirstName, LastName) TO [CustomerService];

-- Masking functions:
-- default(): Shows 0/empty/1900-01-01 based on type
-- email(): First character + "XXX@XXXX.com"  
-- random(start, end): Random value in range (numeric types)
-- partial(prefix, padding, suffix): Partial exposure with custom padding
```

**Limitations of SQL Server DDM:**
- No protection against inference attacks (WHERE clause comparison)
- Users can potentially unmask through calculated columns
- Not a security boundary — intended for casual exposure prevention
- Cannot mask results of computed columns or expressions

### 6.3 Format-Preserving Encryption (FPE)

FPE produces ciphertext that has the same format and length as the plaintext. Essential when encrypted values must pass format validation or fit existing database schemas.

**Standards:**
- **FF1 (NIST SP 800-38G):** Based on Feistel networks with AES round function. Supports arbitrary radix alphabets. Minimum domain size: 1,000,000 values (radix^minlen >= 10^6).
- **FF3-1 (revised FF3):** Faster than FF1 for short inputs. 8 Feistel rounds vs FF1's 10. Revised to fix attack on original FF3 (reduced tweak to 56 bits).

```python
# FPE with ff3 library (Python)
from ff3 import FF3Cipher

# Key: 32 hex chars (128-bit) or 48 hex chars (192-bit)
key = "EF4359D8D580AA4F7F036D6F04FC6A94"
tweak = "D8E7920AFA330A"  # 7-byte tweak

# Encrypt credit card number (preserves 16-digit format)
cipher = FF3Cipher(key, tweak, radix=10)  # decimal digits

plaintext_ccn = "4111111111111111"
encrypted_ccn = cipher.encrypt(plaintext_ccn)
# Result: "6837485920174256" (still 16 digits, passes Luhn? No — FPE doesn't preserve Luhn)

decrypted_ccn = cipher.decrypt(encrypted_ccn)
assert decrypted_ccn == plaintext_ccn

# Encrypt SSN (preserves NNN-NN-NNNN format)
ssn_digits = "123456789"
encrypted_ssn = cipher.encrypt(ssn_digits)
formatted = f"{encrypted_ssn[:3]}-{encrypted_ssn[3:5]}-{encrypted_ssn[5:]}"

# FPE for alphabetic data
alpha_cipher = FF3Cipher(key, tweak, radix=26)  # a-z
encrypted_name = alpha_cipher.encrypt("johnsmith")
```

**FPE security considerations:**
- Small domain sizes are vulnerable to exhaustive search (all possible SSNs = 10^9 ≈ 2^30)
- Deterministic: same input always produces same output (enables frequency analysis)
- Tweak provides additional variability — use unique tweak per record/context
- Not a substitute for proper encryption when format preservation is not required

### 6.4 Masking Rules by Data Type

| Data Type | Masking Strategy | Example Input | Masked Output |
|-----------|-----------------|---------------|---------------|
| SSN | Show last 4 | 123-45-6789 | ***-**-6789 |
| Credit Card | Show last 4, preserve BIN | 4111-1111-1111-1234 | 4111-11**-****-1234 |
| Email | Partial local part | john.doe@company.com | jo***@company.com |
| Phone | Show area code only | (555) 123-4567 | (555) ***-**** |
| Date of Birth | Generalize to year | 1985-03-15 | 1985-01-01 |
| IP Address | Truncate last octet | 192.168.1.42 | 192.168.1.0 |
| Name | Consistent pseudonym | John Smith | Person_A7B3 |
| Address | Generalize to city/ZIP | 123 Main St, Apt 4 | [REDACTED], City, 90210 |
| Salary | Range bucketing | $87,500 | $80,000-$90,000 |
| Medical Code | Category only | ICD-10: J45.20 | Category: Respiratory |

---

## 7. Tokenization

### 7.1 Tokenization vs Encryption

| Aspect | Tokenization | Encryption |
|--------|-------------|------------|
| Reversibility | Via token vault lookup | Via key + algorithm |
| Mathematical relationship | None (random token) | Deterministic function |
| Key management | Vault security | Key lifecycle |
| Format preservation | Easy (token = same format) | Requires FPE |
| Performance | Vault lookup latency | CPU computation |
| Scope reduction | Removes data from scope | Data still exists (encrypted) |
| PCI-DSS impact | Reduces scope to vault only | Entire encrypted data path in scope |

### 7.2 Vault-Based Tokenization

A token vault stores the mapping between tokens and original values in a highly secured, isolated database:

```
┌─────────────────┐         ┌──────────────────┐
│  Application    │ ──(1)──▶│ Tokenization     │
│  (POS, Web)     │         │    Service       │
│                 │◀──(2)── │                  │
│ Stores: token   │         └────────┬─────────┘
└─────────────────┘                  │
                                     │ (stores mapping)
                            ┌────────▼─────────┐
                            │   Token Vault    │
                            │                  │
                            │ Token    → PAN   │
                            │ TK_9X3F → 4111..│
                            │ TK_7Y2D → 5500..│
                            │                  │
                            │ Encrypted at rest│
                            │ HSM-protected    │
                            │ Air-gapped       │
                            └──────────────────┘
```

**Vault architecture requirements:**
- Network isolation (separate VLAN, firewall rules)
- HSM-backed encryption of vault contents
- Multi-factor authentication for administrative access
- Complete audit logging of all tokenize/detokenize operations
- Rate limiting and anomaly detection
- Geographic redundancy with synchronous replication

### 7.3 Vaultless Tokenization

Vaultless tokenization uses FPE or HMAC-based derivation to generate tokens without storing mappings:

```python
# HMAC-based vaultless tokenization
import hmac
import hashlib

def tokenize_pan(pan: str, secret_key: bytes, tweak: bytes = b"") -> str:
    """Generate a format-preserving token from PAN using HMAC."""
    mac = hmac.new(secret_key, pan.encode() + tweak, hashlib.sha256).digest()
    
    # Convert to numeric, preserving 16-digit format
    numeric = int.from_bytes(mac[:8], 'big')
    token_digits = str(numeric % 10**12).zfill(12)
    
    # Preserve BIN (first 6) for routing, replace middle
    token = pan[:6] + token_digits[:6] + pan[12:]
    
    # Note: simplified example. Production uses FF1/FF3-1.
    return token
```

**Trade-offs:**
- No vault infrastructure to manage or scale
- Deterministic: same input always produces same token (enables JOINs)
- Cannot revoke individual tokens without rotating the key (affects all tokens)
- If key is compromised, all tokens are reversible

### 7.4 PCI-DSS Tokenization Requirements

PCI-DSS v4.0 defines tokenization as a scope-reduction technique:

**Requirements for tokens:**
- Token must not be derivable from the PAN through a reversible mathematical function (unless using approved FPE with proper key management)
- Systems storing tokens that cannot be used to retrieve PAN are out of PCI scope
- The tokenization system itself remains in scope (CDE — Cardholder Data Environment)

**Token format guidelines:**
- Must not be usable as a payment instrument
- Should not be confused with real PANs
- Common approach: preserve first 6 + last 4, randomize middle (passes visual inspection as "masked PAN")
- Alternative: completely random with same length

**Detokenization controls:**
- Need-to-know access only
- Separate authentication for detokenization vs tokenization
- Rate limiting (max N detokenizations per user per time window)
- Audit trail with business justification required
- Temporal access: detokenization tokens expire

### 7.5 Token Formats

```
Original PAN:     4111 1111 1111 1234

Format options:
┌──────────────────────────────────────────────────────┐
│ Preserving first 6 + last 4:                         │
│   4111 11XX XXXX 1234  (X = random digits)           │
│                                                       │
│ Fully random (same length):                           │
│   8372 9461 5028 7193  (16 random digits)            │
│                                                       │
│ Alphanumeric (different format):                      │
│   TKN-4F7A2B9C-1234  (clearly not a PAN)            │
│                                                       │
│ UUID-style:                                           │
│   a8f3d2c1-4e5b-6789-abcd-ef0123456789              │
│                                                       │
│ Prefixed (preserving BIN for routing):                │
│   TOK_411111_7F3A2B9C4D  (BIN preserved)            │
└──────────────────────────────────────────────────────┘
```

### 7.6 Vendor Comparison

| Feature | Protegrity | Voltage (Micro Focus) | TokenEx | Thales CipherTrust |
|---------|-----------|----------------------|---------|-------------------|
| Vaultless FPE | Yes (SecureData) | Yes (SecureData) | Yes | Yes |
| Vault-based | Yes | Yes | Yes (primary) | Yes |
| Cloud-native | Partial | Yes | Yes (cloud-first) | Yes |
| PCI-DSS certified | Level 1 | Level 1 | Level 1 | Level 1 |
| Format-preserving | FF1, FF3-1 | FF1 | Multiple | FF1 |
| API-first | REST/gRPC | REST | REST | REST |
| Batch processing | Yes (high throughput) | Yes | Limited | Yes |
| Multi-cloud | Yes | Yes | Yes | Yes |
| Pricing model | Enterprise license | Enterprise license | Per-transaction | Platform license |
| Integration | SDK + proxy | SDK + proxy | Proxy + API | SDK + proxy |

---

## 8. Data Anonymization vs Pseudonymization

### 8.1 Definitions and Legal Distinctions

**Pseudonymization** (GDPR Article 4(5)): Processing personal data so it can no longer be attributed to a specific person without additional information. The additional information (mapping) exists and is kept separately. Still personal data under GDPR — full regulation applies.

**Anonymization**: Irreversible transformation making re-identification impossible. Not personal data under GDPR — regulation does not apply. However, "impossible" is a high bar — research consistently shows re-identification is feasible with auxiliary data.

### 8.2 k-Anonymity

A dataset satisfies k-anonymity if every combination of quasi-identifiers (indirect identifiers like age, ZIP, gender) appears at least k times.

```python
import pandas as pd
import numpy as np

def check_k_anonymity(df: pd.DataFrame, quasi_identifiers: list[str], k: int) -> bool:
    """Check if dataset satisfies k-anonymity for given quasi-identifiers."""
    groups = df.groupby(quasi_identifiers).size()
    min_group_size = groups.min()
    violating_groups = groups[groups < k]
    
    print(f"Minimum group size: {min_group_size}")
    print(f"Groups violating {k}-anonymity: {len(violating_groups)}")
    
    return min_group_size >= k

def generalize_age(age: int, bin_size: int = 5) -> str:
    """Generalize age to ranges."""
    lower = (age // bin_size) * bin_size
    upper = lower + bin_size - 1
    return f"{lower}-{upper}"

def generalize_zip(zipcode: str, level: int = 1) -> str:
    """Generalize ZIP code by suppressing trailing digits."""
    return zipcode[:5-level] + "*" * level

def achieve_k_anonymity(df: pd.DataFrame, quasi_ids: list[str], k: int) -> pd.DataFrame:
    """Iteratively generalize until k-anonymity is achieved."""
    result = df.copy()
    
    # Generalize age
    if 'age' in quasi_ids:
        bin_size = 5
        while not check_k_anonymity(result, quasi_ids, k):
            bin_size += 5
            result['age'] = result['age_original'].apply(
                lambda x: generalize_age(x, bin_size)
            )
            if bin_size > 50:
                break
    
    # Generalize ZIP
    if 'zip' in quasi_ids:
        for level in range(1, 5):
            result['zip'] = result['zip_original'].apply(
                lambda x: generalize_zip(x, level)
            )
            if check_k_anonymity(result, quasi_ids, k):
                break
    
    return result

# Example usage
df = pd.DataFrame({
    'age': [29, 30, 31, 29, 55, 56, 57, 55],
    'zip': ['10001', '10002', '10001', '10003', '90210', '90211', '90210', '90212'],
    'gender': ['M', 'M', 'F', 'M', 'F', 'F', 'M', 'F'],
    'diagnosis': ['Flu', 'COVID', 'Flu', 'Asthma', 'Diabetes', 'COVID', 'Flu', 'Asthma']
})

# Check 3-anonymity on quasi-identifiers
quasi_ids = ['age', 'zip', 'gender']
print(check_k_anonymity(df, quasi_ids, k=3))
```

**Weaknesses of k-anonymity:**
- Homogeneity attack: if all k records in a group have the same sensitive value, it's exposed
- Background knowledge attack: attacker knows additional constraints to narrow candidates

### 8.3 l-Diversity

Extends k-anonymity: each equivalence class must have at least l "well-represented" values for the sensitive attribute.

```python
def check_l_diversity(df: pd.DataFrame, quasi_ids: list[str], 
                      sensitive_attr: str, l: int) -> bool:
    """Check if dataset satisfies l-diversity."""
    groups = df.groupby(quasi_ids)[sensitive_attr]
    
    for name, group in groups:
        distinct_values = group.nunique()
        if distinct_values < l:
            print(f"Group {name} has only {distinct_values} distinct values (need {l})")
            return False
    
    return True

# Entropy l-diversity (stronger): H(sensitive) >= log(l) for each group
def check_entropy_l_diversity(df: pd.DataFrame, quasi_ids: list[str],
                               sensitive_attr: str, l: int) -> bool:
    """Check entropy l-diversity."""
    from scipy.stats import entropy
    
    threshold = np.log(l)
    groups = df.groupby(quasi_ids)[sensitive_attr]
    
    for name, group in groups:
        value_counts = group.value_counts(normalize=True)
        group_entropy = entropy(value_counts)
        if group_entropy < threshold:
            return False
    
    return True
```

### 8.4 t-Closeness

The distribution of sensitive values in any equivalence class should be "close" (within threshold t) to the overall distribution using Earth Mover's Distance:

```python
from scipy.stats import wasserstein_distance

def check_t_closeness(df: pd.DataFrame, quasi_ids: list[str],
                      sensitive_attr: str, t: float) -> bool:
    """Check if dataset satisfies t-closeness."""
    
    # Overall distribution of sensitive attribute
    overall_dist = df[sensitive_attr].value_counts(normalize=True).sort_index()
    
    groups = df.groupby(quasi_ids)
    
    for name, group in groups:
        if len(group) == 0:
            continue
            
        group_dist = group[sensitive_attr].value_counts(normalize=True).sort_index()
        
        # Align distributions
        all_values = sorted(set(overall_dist.index) | set(group_dist.index))
        overall_aligned = [overall_dist.get(v, 0) for v in all_values]
        group_aligned = [group_dist.get(v, 0) for v in all_values]
        
        # Earth Mover's Distance
        emd = wasserstein_distance(
            range(len(all_values)), range(len(all_values)),
            group_aligned, overall_aligned
        )
        
        if emd > t:
            print(f"Group {name}: EMD = {emd:.4f} > t = {t}")
            return False
    
    return True
```

### 8.5 Differential Privacy

Differential privacy provides a mathematical guarantee: the output of a computation changes negligibly whether any single individual is included or excluded from the dataset.

**Definition:** A randomized mechanism M satisfies epsilon-differential privacy if for all datasets D1, D2 differing in one record, and all outputs S:

```
P[M(D1) ∈ S] ≤ e^ε × P[M(D2) ∈ S]
```

**Epsilon (privacy budget):**
- ε = 0: Perfect privacy (random noise only)
- ε = 0.1: Very strong privacy
- ε = 1.0: Moderate privacy (common practical choice)
- ε = 10+: Weak privacy

#### Laplace Mechanism

For numeric queries (counts, sums, averages):

```python
import numpy as np

def laplace_mechanism(true_value: float, sensitivity: float, epsilon: float) -> float:
    """Add Laplace noise to achieve epsilon-differential privacy.
    
    Args:
        true_value: The actual query result
        sensitivity: Maximum change in query output from adding/removing one record
        epsilon: Privacy parameter (smaller = more private)
    """
    scale = sensitivity / epsilon  # b parameter of Laplace distribution
    noise = np.random.laplace(0, scale)
    return true_value + noise

# Example: counting query
# Sensitivity of COUNT = 1 (one person changes count by at most 1)
true_count = 1247
private_count = laplace_mechanism(true_count, sensitivity=1.0, epsilon=0.5)
print(f"True: {true_count}, Private: {private_count:.0f}")

# Example: average salary
# Sensitivity of AVG = (max_salary - min_salary) / n
# For bounded salary [30000, 500000] with n=1000 employees:
sensitivity_avg = (500000 - 30000) / 1000  # = 470
true_avg = 87500
private_avg = laplace_mechanism(true_avg, sensitivity=sensitivity_avg, epsilon=1.0)
```

#### Gaussian Mechanism

For (epsilon, delta)-differential privacy. Better composition properties:

```python
def gaussian_mechanism(true_value: float, sensitivity: float, 
                       epsilon: float, delta: float) -> float:
    """Add Gaussian noise for (epsilon, delta)-DP.
    
    delta: probability of pure epsilon-DP being violated (typically 1/n^2)
    """
    sigma = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
    noise = np.random.normal(0, sigma)
    return true_value + noise
```

#### Privacy Budget Composition

```python
class PrivacyAccountant:
    """Track cumulative privacy expenditure."""
    
    def __init__(self, total_budget: float, delta: float = 1e-5):
        self.total_budget = total_budget
        self.delta = delta
        self.spent = 0.0
        self.queries = []
    
    def query(self, name: str, epsilon: float) -> bool:
        """Check if query is within budget."""
        if self.spent + epsilon > self.total_budget:
            raise PrivacyBudgetExhausted(
                f"Query '{name}' requires ε={epsilon}, "
                f"but only {self.total_budget - self.spent:.4f} remains"
            )
        self.spent += epsilon
        self.queries.append({'name': name, 'epsilon': epsilon})
        return True
    
    @property
    def remaining(self) -> float:
        return self.total_budget - self.spent

# Usage
accountant = PrivacyAccountant(total_budget=3.0)
accountant.query("age_histogram", epsilon=0.5)
accountant.query("salary_average", epsilon=1.0)
accountant.query("gender_count", epsilon=0.3)
print(f"Remaining budget: {accountant.remaining}")  # 1.2
```

### 8.6 Practical PostgreSQL Anonymization

```sql
-- PostgreSQL Anonymizer extension (postgresql_anonymizer)
CREATE EXTENSION IF NOT EXISTS anon CASCADE;

-- Define masking rules
SELECT anon.init();

-- Declare masking rules on columns
SECURITY LABEL FOR anon ON COLUMN customers.name
  IS 'MASKED WITH FUNCTION anon.fake_first_name()';

SECURITY LABEL FOR anon ON COLUMN customers.email
  IS 'MASKED WITH FUNCTION anon.partial_email(email)';

SECURITY LABEL FOR anon ON COLUMN customers.phone
  IS 'MASKED WITH FUNCTION anon.random_phone()';

SECURITY LABEL FOR anon ON COLUMN customers.birth_date
  IS 'MASKED WITH FUNCTION anon.random_date_between(''1950-01-01'', ''2000-12-31'')';

-- Apply static masking to a dump
-- pg_dump with anonymization:
SELECT anon.anonymize_database();

-- Dynamic masking for specific role
CREATE ROLE analyst;
SECURITY LABEL FOR anon ON ROLE analyst IS 'MASKED';

-- analyst sees masked data, admin sees real data
SET ROLE analyst;
SELECT * FROM customers;  -- masked
RESET ROLE;
SELECT * FROM customers;  -- real
```

### 8.7 Synthetic Data Generation

When anonymization is insufficient, generate entirely synthetic data that preserves statistical properties:

```python
# Using SDV (Synthetic Data Vault) library
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import SingleTableMetadata

# Define metadata
metadata = SingleTableMetadata()
metadata.detect_from_dataframe(real_data)
metadata.update_column('ssn', sdtype='ssn')
metadata.update_column('email', sdtype='email')

# Train synthesizer on real data
synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.fit(real_data)

# Generate synthetic data
synthetic_data = synthesizer.sample(num_rows=10000)

# Evaluate quality
from sdv.evaluation.single_table import evaluate_quality
quality_report = evaluate_quality(real_data, synthetic_data, metadata)
print(quality_report.get_score())  # 0.0-1.0 (higher = more realistic)
```

**Privacy guarantees of synthetic data:**
- No formal mathematical guarantee (unlike differential privacy)
- Overfitting risk: synthetic data may memorize rare individuals
- Mitigation: add DP noise during training (DP-SGD), use holdout validation
- Never assume synthetic data is automatically anonymous — validate empirically

---

## 9. Attack Vectors Against Encrypted Data

### 9.1 Known Plaintext Attacks

If an attacker knows (or can guess) plaintext-ciphertext pairs:

**ECB mode exploitation:** Identical plaintext blocks produce identical ciphertext blocks. Even with AES-256, ECB reveals patterns in structured data (the "ECB penguin" demonstration).

**Deterministic encryption at scale:** Column-level encryption with deterministic mode enables frequency analysis. If encrypted SSN values are deterministic, the most common ciphertext maps to common states/areas.

**Mitigation:**
- Always use authenticated encryption with random nonces (AES-GCM, ChaCha20-Poly1305)
- Never use ECB mode for anything beyond single-block encryption
- For database columns requiring equality search, accept the security trade-off explicitly

### 9.2 Padding Oracle Attacks

Applicable to CBC mode with PKCS#7 padding when the system reveals whether padding is valid:

```
Attacker sends modified ciphertext → Server attempts decrypt → 
Server returns "padding error" vs "application error" → 
Attacker iteratively recovers plaintext byte-by-byte
```

**POODLE (2014):** Exploited SSL 3.0's CBC padding. **Lucky13 (2013):** Timing variation in TLS CBC implementations.

**Mitigation:**
- Use AEAD modes (GCM, Poly1305) — no separate padding step
- Encrypt-then-MAC if CBC is unavoidable (verify MAC before attempting decryption)
- Constant-time comparison for all cryptographic checks
- Generic error messages (never distinguish padding errors from other failures)

### 9.3 Side-Channel Attacks

**Timing attacks:** Execution time varies based on secret-dependent branches or memory access patterns.

```c
// VULNERABLE: timing leaks key comparison result
int compare_macs(uint8_t *computed, uint8_t *received, size_t len) {
    for (int i = 0; i < len; i++) {
        if (computed[i] != received[i]) return 0;  // early exit leaks position
    }
    return 1;
}

// SAFE: constant-time comparison
int constant_time_compare(uint8_t *a, uint8_t *b, size_t len) {
    uint8_t diff = 0;
    for (int i = 0; i < len; i++) {
        diff |= a[i] ^ b[i];  // accumulate differences
    }
    return diff == 0;  // single comparison at the end
}
```

**Cache-timing attacks:** AES T-table implementations leak key bits through cache access patterns (Bernstein 2005, Osvik-Shamir-Tromer 2006). Modern mitigations: AES-NI hardware instruction, bitsliced implementations.

**Power analysis:** Simple Power Analysis (SPA) and Differential Power Analysis (DPA) recover keys from hardware devices by measuring power consumption during cryptographic operations. Relevant for IoT/embedded data collectors.

**Electromagnetic emanation:** TEMPEST attacks capture EM radiation from devices performing crypto. Theoretical for most data engineering contexts but relevant for HSM certification (FIPS 140-2 Level 4 requires EM shielding).

### 9.4 Key Extraction from Memory

**Attack surfaces:**
- Process memory dumps (core dumps, crash reports)
- Swap space containing key material
- Hypervisor access in cloud environments (speculative execution: Spectre, Meltdown)
- Live memory forensics via DMA (FireWire, Thunderbolt, PCIe)
- Hibernation files

**Mitigations:**

```python
# Python: memory wiping is difficult due to GC, but effort should be made
import ctypes
import sys

def secure_wipe(secret: bytearray):
    """Attempt to overwrite secret in memory."""
    ctypes.memset(id(secret) + sys.getsizeof(bytearray()) - len(secret), 0, len(secret))

# Better: use mlock to prevent swapping
import mmap
# Allocate locked memory for keys
locked_page = mmap.mmap(-1, 4096, mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
# On Linux, also call mlock() via ctypes
```

```bash
# System-level mitigations
# Disable swap
swapoff -a

# Or encrypt swap
echo '/dev/mapper/cryptswap none swap sw 0 0' >> /etc/fstab

# Disable core dumps
echo '* hard core 0' >> /etc/security/limits.conf
echo 'kernel.core_pattern=|/bin/false' >> /etc/sysctl.conf

# Lock sensitive processes in RAM
# In systemd service:
# MemoryDenyWriteExecute=yes
# LockPersonality=yes
```

### 9.5 Cold Boot Attacks

DRAM retains data for seconds to minutes after power loss (longer at low temperatures). An attacker can freeze RAM, extract modules, and read key material.

**Practical relevance:** Physical access scenarios (stolen servers, decommissioned hardware, evil-maid attacks in data centers).

**Mitigations:**
- Full-memory encryption (AMD SEV, Intel TME/MKTME)
- Key schedules in CPU registers only (register-based AES implementations)
- TPM-sealed keys with boot measurement (PCR-based unsealing)
- Physical security controls (tamper-evident chassis, rack locks, CCTV)

### 9.6 Cloud Provider Access Model

**What cloud providers can access:**
- Physical hardware and hypervisor layer
- Network metadata (source, destination, size, timing — not content if encrypted)
- Encrypted storage (they hold the physical media)
- KMS operations are logged but key material stays in HSM

**What cloud providers cannot access (with proper configuration):**
- Client-side encrypted data (CSFLE, client-side envelope encryption)
- Data encrypted with BYOK/HYOK keys (they cannot access key material)
- End-to-end encrypted communications within customer VPC

**Trust boundary analysis:**

```
Full trust in provider:     Default encryption (SSE-S3, Google-managed keys)
Partial trust:              CMEK/CMK (you control key lifecycle, they hold it)  
Minimal trust:              BYOK (you generate, they import into their HSM)
Zero trust in provider:     Client-side encryption (data arrives pre-encrypted)
                            External KMS (key never touches provider infrastructure)
```

**Subpoena/warrant considerations:**
- Providers must comply with valid legal process for data they can decrypt
- Client-side encryption with customer-held keys = provider cannot comply (compelled to produce ciphertext only)
- Geo-residency does not guarantee protection from extraterritorial legal reach (US CLOUD Act, EU requests)

### 9.7 Quantum Computing Threats

#### Grover's Algorithm

Provides quadratic speedup for brute-force key search:
- AES-128: Effective security reduced to 64 bits (breakable)
- AES-256: Effective security reduced to 128 bits (still secure)
- Hash functions: 256-bit hash provides 128-bit collision resistance

**Implication:** Double symmetric key sizes. AES-256 is quantum-safe. SHA-256 for collision resistance requires SHA-512.

#### Shor's Algorithm

Polynomial-time factoring and discrete logarithm:
- RSA: Broken regardless of key size
- ECDSA / Ed25519: Broken (discrete log on elliptic curves)
- DH / ECDH: Broken

**Implication:** All currently deployed asymmetric cryptography is vulnerable to a sufficiently large quantum computer.

#### Post-Quantum Cryptography (PQC)

NIST standardized PQC algorithms (2024):

| Algorithm | Type | Use Case | Standard |
|-----------|------|----------|----------|
| ML-KEM (Kyber) | Lattice-based | Key encapsulation | FIPS 203 |
| ML-DSA (Dilithium) | Lattice-based | Digital signatures | FIPS 204 |
| SLH-DSA (SPHINCS+) | Hash-based | Digital signatures (stateless) | FIPS 205 |
| HBS (XMSS, LMS) | Hash-based | Firmware/code signing | SP 800-208 |

**Harvest-now-decrypt-later (HNDL):**
- Adversaries record encrypted traffic today
- Store ciphertext until quantum computers are available
- Decrypt historical communications/data

**Data engineering implications:**
- Data with 10+ year confidentiality requirements needs PQC protection now
- Long-lived signing keys (CA certificates, firmware signing) should migrate to hybrid schemes
- Database encryption (symmetric) is already quantum-resistant with AES-256
- Key exchange for replication / pipeline TLS needs hybrid PQC+classical

```python
# Hybrid key exchange example (conceptual — use established libraries)
# Combine classical X25519 with ML-KEM for quantum resistance

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
# from pqcrypto.kem import kyber1024  # post-quantum KEM

# Classical key exchange
classical_private = X25519PrivateKey.generate()
classical_shared = classical_private.exchange(peer_public_key)

# Post-quantum key exchange (when libraries mature)
# pq_ciphertext, pq_shared = kyber1024.encapsulate(peer_pq_public_key)

# Combine both shared secrets
# combined_secret = HKDF(classical_shared || pq_shared)
# Even if one is broken, the other provides security
```

---

## 10. Lab Exercises

### Lab 1: Column-Level Encryption with pgcrypto and Key Rotation

**Objective:** Implement field-level encryption in PostgreSQL, demonstrate key rotation without data loss.

```sql
-- Setup: Create extension and tables
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Key management table (in practice, keys come from Vault/KMS)
CREATE TABLE encryption_keys (
    key_id SERIAL PRIMARY KEY,
    key_version INT NOT NULL,
    encrypted_key BYTEA NOT NULL,  -- KEK-encrypted DEK
    algorithm TEXT DEFAULT 'aes256',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(key_version)
);

-- Table with encrypted sensitive columns
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    encrypted_ssn BYTEA NOT NULL,
    encrypted_diagnosis BYTEA NOT NULL,
    key_version INT NOT NULL REFERENCES encryption_keys(key_version),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert encrypted data
-- In production: key comes from Vault, not hardcoded
DO $$
DECLARE
    v_key TEXT := 'production-encryption-key-v1-replace-me';
BEGIN
    INSERT INTO encryption_keys (key_version, encrypted_key, is_active)
    VALUES (1, pgp_sym_encrypt(v_key, 'master-key-from-hsm')::BYTEA, true);
END $$;

-- Encrypt and insert patient record
CREATE OR REPLACE FUNCTION insert_patient(
    p_name TEXT, p_ssn TEXT, p_diagnosis TEXT
) RETURNS INT AS $$
DECLARE
    v_key TEXT;
    v_key_version INT;
    v_patient_id INT;
BEGIN
    -- Get active key
    SELECT key_version INTO v_key_version
    FROM encryption_keys WHERE is_active = true
    ORDER BY key_version DESC LIMIT 1;
    
    -- In production: decrypt key from Vault
    v_key := 'production-encryption-key-v1-replace-me';
    
    INSERT INTO patients (name, encrypted_ssn, encrypted_diagnosis, key_version)
    VALUES (
        p_name,
        pgp_sym_encrypt(p_ssn, v_key, 'cipher-algo=aes256'),
        pgp_sym_encrypt(p_diagnosis, v_key, 'cipher-algo=aes256'),
        v_key_version
    ) RETURNING id INTO v_patient_id;
    
    RETURN v_patient_id;
END;
$$ LANGUAGE plpgsql;

-- Decrypt patient record
CREATE OR REPLACE FUNCTION decrypt_patient(p_id INT)
RETURNS TABLE(name TEXT, ssn TEXT, diagnosis TEXT) AS $$
DECLARE
    v_key TEXT;
    v_record RECORD;
BEGIN
    SELECT p.*, ek.key_version as ek_version
    INTO v_record
    FROM patients p
    JOIN encryption_keys ek ON p.key_version = ek.key_version
    WHERE p.id = p_id;
    
    -- Get appropriate key version
    -- In production: fetch from Vault with version parameter
    v_key := 'production-encryption-key-v1-replace-me';
    
    RETURN QUERY SELECT
        v_record.name,
        pgp_sym_decrypt(v_record.encrypted_ssn, v_key)::TEXT,
        pgp_sym_decrypt(v_record.encrypted_diagnosis, v_key)::TEXT;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- KEY ROTATION PROCEDURE
CREATE OR REPLACE FUNCTION rotate_encryption_key(
    p_new_key TEXT,
    p_old_key TEXT
) RETURNS TEXT AS $$
DECLARE
    v_new_version INT;
    v_rotated_count INT := 0;
    v_record RECORD;
BEGIN
    -- Create new key version
    SELECT COALESCE(MAX(key_version), 0) + 1 INTO v_new_version
    FROM encryption_keys;
    
    INSERT INTO encryption_keys (key_version, encrypted_key, is_active)
    VALUES (v_new_version, pgp_sym_encrypt(p_new_key, 'master-key-from-hsm')::BYTEA, true);
    
    -- Deactivate old key (but keep for decryption of not-yet-rotated records)
    UPDATE encryption_keys SET is_active = false
    WHERE key_version < v_new_version;
    
    -- Re-encrypt all records with new key
    FOR v_record IN SELECT id, encrypted_ssn, encrypted_diagnosis 
                    FROM patients WHERE key_version < v_new_version
    LOOP
        UPDATE patients SET
            encrypted_ssn = pgp_sym_encrypt(
                pgp_sym_decrypt(v_record.encrypted_ssn, p_old_key),
                p_new_key, 'cipher-algo=aes256'
            ),
            encrypted_diagnosis = pgp_sym_encrypt(
                pgp_sym_decrypt(v_record.encrypted_diagnosis, p_old_key),
                p_new_key, 'cipher-algo=aes256'
            ),
            key_version = v_new_version
        WHERE id = v_record.id;
        
        v_rotated_count := v_rotated_count + 1;
    END LOOP;
    
    -- Mark old key as rotated
    UPDATE encryption_keys SET rotated_at = NOW()
    WHERE key_version < v_new_version;
    
    RETURN format('Rotated %s records to key version %s', v_rotated_count, v_new_version);
END;
$$ LANGUAGE plpgsql;

-- Execute rotation
SELECT rotate_encryption_key(
    'production-encryption-key-v2-new-key',
    'production-encryption-key-v1-replace-me'
);

-- Verify: all records should now be on latest version
SELECT key_version, COUNT(*) FROM patients GROUP BY key_version;

-- Blind index for searchable encrypted columns
ALTER TABLE patients ADD COLUMN ssn_hash BYTEA;

CREATE OR REPLACE FUNCTION update_ssn_blind_index() RETURNS TRIGGER AS $$
BEGIN
    -- HMAC with separate key (not the encryption key)
    NEW.ssn_hash := hmac(
        pgp_sym_decrypt(NEW.encrypted_ssn, current_setting('app.encryption_key')),
        current_setting('app.hmac_key'),
        'sha256'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE INDEX idx_patients_ssn_hash ON patients(ssn_hash);

-- Search by SSN without decrypting all rows
SELECT * FROM patients
WHERE ssn_hash = hmac('123-45-6789', current_setting('app.hmac_key'), 'sha256');
```

### Lab 2: Dynamic Masking Layer for a REST API

**Objective:** Build a middleware that dynamically masks sensitive fields based on the authenticated user's role.

```python
# masking_middleware.py
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable
import re
import hashlib

class AccessLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVILEGED = "privileged"
    ADMIN = "admin"

@dataclass
class MaskingRule:
    """Defines how a field should be masked for a given access level."""
    field_path: str  # dot-notation path: "user.ssn", "payment.card_number"
    max_visible_level: AccessLevel
    masking_function: Callable[[str], str]
    
class MaskingEngine:
    """Applies masking rules to API response payloads."""
    
    def __init__(self):
        self.rules: list[MaskingRule] = []
    
    def register_rule(self, rule: MaskingRule):
        self.rules.append(rule)
    
    def mask_response(self, data: dict, access_level: AccessLevel) -> dict:
        """Apply all applicable masking rules to the response data."""
        result = self._deep_copy(data)
        
        for rule in self.rules:
            if self._should_mask(rule, access_level):
                self._apply_mask(result, rule.field_path, rule.masking_function)
        
        return result
    
    def _should_mask(self, rule: MaskingRule, user_level: AccessLevel) -> bool:
        """Determine if masking should be applied."""
        level_hierarchy = [
            AccessLevel.PUBLIC,
            AccessLevel.INTERNAL, 
            AccessLevel.PRIVILEGED,
            AccessLevel.ADMIN
        ]
        return level_hierarchy.index(user_level) < level_hierarchy.index(rule.max_visible_level)
    
    def _apply_mask(self, data: dict, field_path: str, mask_fn: Callable):
        """Navigate nested dict and apply masking function."""
        parts = field_path.split('.')
        current = data
        
        for i, part in enumerate(parts[:-1]):
            if part == '*':  # wildcard for arrays
                if isinstance(current, list):
                    for item in current:
                        self._apply_mask(item, '.'.join(parts[i+1:]), mask_fn)
                    return
            elif part in current:
                current = current[part]
            else:
                return  # field not present, skip
        
        final_key = parts[-1]
        if isinstance(current, dict) and final_key in current:
            if current[final_key] is not None:
                current[final_key] = mask_fn(str(current[final_key]))
        elif isinstance(current, list):
            for item in current:
                if isinstance(item, dict) and final_key in item:
                    if item[final_key] is not None:
                        item[final_key] = mask_fn(str(item[final_key]))
    
    def _deep_copy(self, data: Any) -> Any:
        """Immutable transformation — never mutate input."""
        import json
        return json.loads(json.dumps(data))


# Masking functions library
def mask_ssn(value: str) -> str:
    """Show last 4 digits only."""
    digits = re.sub(r'[^0-9]', '', value)
    if len(digits) >= 4:
        return f"***-**-{digits[-4:]}"
    return "***-**-****"

def mask_email(value: str) -> str:
    """Show first 2 chars + domain."""
    parts = value.split('@')
    if len(parts) == 2:
        local = parts[0][:2] + '***'
        return f"{local}@{parts[1]}"
    return "***@***.***"

def mask_credit_card(value: str) -> str:
    """Show last 4 digits, mask rest."""
    digits = re.sub(r'[^0-9]', '', value)
    if len(digits) >= 4:
        return f"****-****-****-{digits[-4:]}"
    return "****-****-****-****"

def mask_phone(value: str) -> str:
    """Show area code only."""
    digits = re.sub(r'[^0-9]', '', value)
    if len(digits) >= 10:
        return f"({digits[:3]}) ***-****"
    return "(***) ***-****"

def mask_full(value: str) -> str:
    """Complete redaction."""
    return "[REDACTED]"

def mask_name_pseudonym(value: str) -> str:
    """Consistent pseudonym via hash."""
    hash_val = hashlib.sha256(value.encode()).hexdigest()[:6]
    return f"Person_{hash_val.upper()}"


# FastAPI integration
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
import json

app = FastAPI()

# Initialize masking engine with rules
engine = MaskingEngine()
engine.register_rule(MaskingRule("ssn", AccessLevel.ADMIN, mask_ssn))
engine.register_rule(MaskingRule("email", AccessLevel.INTERNAL, mask_email))
engine.register_rule(MaskingRule("card_number", AccessLevel.ADMIN, mask_credit_card))
engine.register_rule(MaskingRule("phone", AccessLevel.PRIVILEGED, mask_phone))
engine.register_rule(MaskingRule("patients.*.diagnosis", AccessLevel.PRIVILEGED, mask_full))
engine.register_rule(MaskingRule("salary", AccessLevel.ADMIN, mask_full))

def get_user_access_level(request: Request) -> AccessLevel:
    """Extract access level from JWT claims or session."""
    # In production: decode JWT, check role claims
    role = request.headers.get("X-User-Role", "public")
    return AccessLevel(role)

@app.middleware("http")
async def masking_middleware(request: Request, call_next):
    """Apply dynamic masking to all JSON responses."""
    response = await call_next(request)
    
    if response.headers.get("content-type", "").startswith("application/json"):
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Parse and mask
        data = json.loads(body)
        access_level = get_user_access_level(request)
        masked_data = engine.mask_response(data, access_level)
        
        # Return masked response
        masked_body = json.dumps(masked_data).encode()
        return JSONResponse(
            content=masked_data,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    
    return response

@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: int):
    """Example endpoint — masking applied by middleware."""
    return {
        "id": patient_id,
        "name": "John Smith",
        "ssn": "123-45-6789",
        "email": "john.smith@hospital.org",
        "phone": "(555) 867-5309",
        "diagnosis": "Type 2 Diabetes",
        "salary": 95000,
        "card_number": "4111-1111-1111-1234"
    }
```

**Testing the masking middleware:**

```bash
# As public user — maximum masking
curl -H "X-User-Role: public" http://localhost:8000/api/patients/1
# {"ssn": "***-**-6789", "email": "jo***@hospital.org", 
#  "phone": "(***) ***-****", "diagnosis": "[REDACTED]", ...}

# As internal user — email visible
curl -H "X-User-Role: internal" http://localhost:8000/api/patients/1
# {"ssn": "***-**-6789", "email": "john.smith@hospital.org",
#  "phone": "(***) ***-****", "diagnosis": "[REDACTED]", ...}

# As admin — everything visible
curl -H "X-User-Role: admin" http://localhost:8000/api/patients/1
# {"ssn": "123-45-6789", "email": "john.smith@hospital.org", ...}
```

### Lab 3: Tokenization Service with Vault Transit Engine

**Objective:** Build a tokenization service using HashiCorp Vault's Transit secrets engine for PCI-compliant card number protection.

```bash
# Start Vault in dev mode (for lab only — never in production)
vault server -dev -dev-root-token-id="lab-root-token"

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='lab-root-token'

# Enable Transit secrets engine
vault secrets enable transit

# Create tokenization key
vault write transit/keys/card-tokenization \
  type=aes256-gcm96 \
  exportable=false \
  allow_plaintext_backup=false

# Create policy for tokenization service
vault policy write tokenization-service - <<EOF
path "transit/encrypt/card-tokenization" {
  capabilities = ["update"]
}
path "transit/decrypt/card-tokenization" {
  capabilities = ["update"]
}
path "transit/rewrap/card-tokenization" {
  capabilities = ["update"]
}
# Detokenization requires separate, more restrictive policy
EOF

# Create policy for detokenization (separate, audited)
vault policy write detokenization-service - <<EOF
path "transit/decrypt/card-tokenization" {
  capabilities = ["update"]
  # In production: add required_parameters, sentinel policies
}
EOF
```

```python
# tokenization_service.py
import hvac
import base64
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class TokenRecord:
    token: str
    vault_ciphertext: str
    created_at: str
    last_accessed: str
    access_count: int
    metadata: dict

class VaultTokenizationService:
    """PCI-compliant tokenization using Vault Transit engine."""
    
    def __init__(self, vault_url: str, vault_token: str, key_name: str = "card-tokenization"):
        self.client = hvac.Client(url=vault_url, token=vault_token)
        self.key_name = key_name
        self.token_store: dict[str, TokenRecord] = {}  # In production: persistent store
        
        if not self.client.is_authenticated():
            raise RuntimeError("Vault authentication failed")
    
    def tokenize(self, pan: str, metadata: dict = None) -> str:
        """Convert PAN to a format-preserving token."""
        # Validate PAN format
        clean_pan = re.sub(r'[^0-9]', '', pan)
        if not self._validate_luhn(clean_pan):
            raise ValueError("Invalid card number (Luhn check failed)")
        
        # Check if already tokenized (idempotent)
        pan_hash = self._hash_pan(clean_pan)
        for token, record in self.token_store.items():
            if hashlib.sha256(token.encode()).hexdigest() == pan_hash:
                # Already tokenized — return existing token
                return token
        
        # Encrypt PAN with Vault Transit
        plaintext_b64 = base64.b64encode(clean_pan.encode()).decode()
        response = self.client.secrets.transit.encrypt_data(
            name=self.key_name,
            plaintext=plaintext_b64,
            context=base64.b64encode(b"card-tokenization-context").decode()
        )
        vault_ciphertext = response['data']['ciphertext']
        
        # Generate format-preserving token
        # Preserve BIN (first 6) + last 4, randomize middle
        token = self._generate_token(clean_pan)
        
        # Store mapping
        self.token_store[token] = TokenRecord(
            token=token,
            vault_ciphertext=vault_ciphertext,
            created_at=datetime.now(timezone.utc).isoformat(),
            last_accessed=datetime.now(timezone.utc).isoformat(),
            access_count=0,
            metadata=metadata or {}
        )
        
        return token
    
    def detokenize(self, token: str, requester: str, justification: str) -> str:
        """Recover original PAN from token. Requires audit justification."""
        if token not in self.token_store:
            raise ValueError("Token not found")
        
        record = self.token_store[token]
        
        # Audit logging (in production: structured logging to SIEM)
        self._audit_log("DETOKENIZE", token, requester, justification)
        
        # Decrypt via Vault Transit
        response = self.client.secrets.transit.decrypt_data(
            name=self.key_name,
            ciphertext=record.vault_ciphertext,
            context=base64.b64encode(b"card-tokenization-context").decode()
        )
        
        pan = base64.b64decode(response['data']['plaintext']).decode()
        
        # Update access tracking
        record.last_accessed = datetime.now(timezone.utc).isoformat()
        record.access_count += 1
        
        return pan
    
    def rotate_key(self) -> dict:
        """Rotate the Vault Transit encryption key."""
        # Rotate key in Vault (old versions still decrypt)
        self.client.secrets.transit.rotate_key(name=self.key_name)
        
        # Rewrap all stored ciphertexts with new key version
        rewrapped = 0
        for token, record in self.token_store.items():
            response = self.client.secrets.transit.rewrap_data(
                name=self.key_name,
                ciphertext=record.vault_ciphertext,
                context=base64.b64encode(b"card-tokenization-context").decode()
            )
            record.vault_ciphertext = response['data']['ciphertext']
            rewrapped += 1
        
        return {"rewrapped_tokens": rewrapped, "rotated_at": datetime.now(timezone.utc).isoformat()}
    
    def _generate_token(self, pan: str) -> str:
        """Generate a token preserving BIN + last 4."""
        import secrets
        bin_prefix = pan[:6]
        last_four = pan[-4:]
        middle_length = len(pan) - 10
        
        # Generate random middle digits (not derivable from PAN)
        middle = ''.join([str(secrets.randbelow(10)) for _ in range(middle_length)])
        
        token = f"{bin_prefix}{middle}{last_four}"
        
        # Ensure token is not a valid card number (break Luhn)
        while self._validate_luhn(token):
            middle = ''.join([str(secrets.randbelow(10)) for _ in range(middle_length)])
            token = f"{bin_prefix}{middle}{last_four}"
        
        return token
    
    def _validate_luhn(self, number: str) -> bool:
        """Luhn algorithm validation."""
        digits = [int(d) for d in number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        total = sum(odd_digits)
        for d in even_digits:
            total += sum(divmod(d * 2, 10))
        return total % 10 == 0
    
    def _hash_pan(self, pan: str) -> str:
        """One-way hash for deduplication (not reversible)."""
        return hashlib.sha256(f"pan-dedupe-salt-{pan}".encode()).hexdigest()
    
    def _audit_log(self, operation: str, token: str, requester: str, justification: str):
        """Audit log entry for compliance."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "token_last4": token[-4:],
            "requester": requester,
            "justification": justification,
            "source_ip": "10.0.0.1"  # from request context in production
        }
        # In production: send to SIEM, append-only audit log
        print(f"[AUDIT] {entry}")


# Usage example
if __name__ == "__main__":
    service = VaultTokenizationService(
        vault_url="http://127.0.0.1:8200",
        vault_token="lab-root-token"
    )
    
    # Tokenize
    token = service.tokenize("4111111111111111", metadata={"merchant": "lab-store"})
    print(f"Token: {token}")  # e.g., "4111117382941111" (BIN + random + last4)
    
    # Detokenize (with audit trail)
    pan = service.detokenize(
        token, 
        requester="compliance-officer-jane",
        justification="Chargeback investigation #CB-2024-5678"
    )
    print(f"PAN: {pan}")
    
    # Key rotation
    result = service.rotate_key()
    print(f"Rotation: {result}")
```

### Lab 4: Demonstrating k-Anonymity on a Dataset

**Objective:** Take a realistic dataset, assess re-identification risk, and apply anonymization techniques to achieve k-anonymity.

```python
# k_anonymity_lab.py
import pandas as pd
import numpy as np
from typing import Optional

# Generate realistic patient dataset
np.random.seed(42)
n_records = 500

data = pd.DataFrame({
    'patient_id': range(1, n_records + 1),
    'age': np.random.normal(45, 15, n_records).astype(int).clip(18, 95),
    'gender': np.random.choice(['M', 'F', 'NB'], n_records, p=[0.48, 0.48, 0.04]),
    'zip_code': np.random.choice(
        ['10001', '10002', '10003', '10004', '10005',
         '90210', '90211', '90212', '90213', '90214',
         '60601', '60602', '60603', '60604', '60605'], n_records
    ),
    'diagnosis': np.random.choice(
        ['Hypertension', 'Diabetes', 'Asthma', 'Depression', 
         'Arthritis', 'Migraine', 'COPD', 'Anxiety',
         'Heart Disease', 'Cancer'], n_records,
        p=[0.20, 0.15, 0.12, 0.12, 0.10, 0.08, 0.08, 0.07, 0.05, 0.03]
    ),
    'visit_date': pd.date_range('2023-01-01', periods=n_records, freq='4h'),
    'charges': np.random.lognormal(7, 1, n_records).round(2)
})

print("Original dataset:")
print(data.head(10))
print(f"\nTotal records: {len(data)}")

# Define quasi-identifiers (attributes that could be used for re-identification)
quasi_identifiers = ['age', 'gender', 'zip_code']
sensitive_attribute = 'diagnosis'

# Step 1: Assess current k-anonymity
def assess_k_anonymity(df: pd.DataFrame, qi: list[str]) -> dict:
    """Analyze k-anonymity status of dataset."""
    groups = df.groupby(qi).size()
    
    result = {
        'total_groups': len(groups),
        'min_group_size': groups.min(),
        'max_group_size': groups.max(),
        'mean_group_size': groups.mean(),
        'median_group_size': groups.median(),
        'unique_individuals': (groups == 1).sum(),
        'groups_below_5': (groups < 5).sum(),
        'records_in_small_groups': df.groupby(qi).filter(lambda x: len(x) < 5).shape[0],
    }
    
    print(f"\n{'='*60}")
    print(f"K-ANONYMITY ASSESSMENT")
    print(f"{'='*60}")
    print(f"Quasi-identifiers: {qi}")
    print(f"Total equivalence classes: {result['total_groups']}")
    print(f"Minimum k (current): {result['min_group_size']}")
    print(f"Unique individuals (k=1, fully identifiable): {result['unique_individuals']}")
    print(f"Groups with k < 5: {result['groups_below_5']}")
    print(f"Records at risk (in groups < 5): {result['records_in_small_groups']}")
    print(f"{'='*60}")
    
    return result

assessment_before = assess_k_anonymity(data, quasi_identifiers)

# Step 2: Apply generalization to achieve k=5
def generalize_age(age: int, bin_size: int) -> str:
    """Generalize age into ranges."""
    lower = (age // bin_size) * bin_size
    upper = lower + bin_size - 1
    return f"{lower}-{upper}"

def generalize_zip(zipcode: str, level: int) -> str:
    """Generalize ZIP code by masking trailing digits."""
    if level >= len(zipcode):
        return '*' * len(zipcode)
    return zipcode[:len(zipcode) - level] + '*' * level

def suppress_outliers(df: pd.DataFrame, qi: list[str], k: int) -> pd.DataFrame:
    """Remove records that cannot achieve k-anonymity even after generalization."""
    groups = df.groupby(qi).size()
    small_groups = groups[groups < k].index
    
    mask = ~df.set_index(qi).index.isin(small_groups)
    suppressed_count = (~mask).sum()
    
    if suppressed_count > 0:
        print(f"  Suppressed {suppressed_count} records ({suppressed_count/len(df)*100:.1f}%)")
    
    return df[mask].reset_index(drop=True)

def achieve_k_anonymity(df: pd.DataFrame, quasi_ids: list[str], 
                        target_k: int, max_iterations: int = 10) -> pd.DataFrame:
    """Iteratively generalize until target k-anonymity is achieved."""
    result = df.copy()
    
    age_bin_size = 1
    zip_level = 0
    
    for iteration in range(max_iterations):
        # Check current state
        groups = result.groupby(quasi_ids).size()
        current_k = groups.min()
        
        if current_k >= target_k:
            print(f"\n  Achieved {target_k}-anonymity in {iteration} iterations")
            print(f"  Age bin size: {age_bin_size}, ZIP generalization level: {zip_level}")
            break
        
        # Determine which generalization to apply next
        # Strategy: generalize the QI with most distinct values first
        distinct_counts = {qi: result[qi].nunique() for qi in quasi_ids}
        most_distinct = max(distinct_counts, key=distinct_counts.get)
        
        print(f"  Iteration {iteration + 1}: Generalizing '{most_distinct}' "
              f"(current k={current_k}, distinct values: {distinct_counts})")
        
        if most_distinct == 'age':
            age_bin_size += 2
            result['age'] = df['age'].apply(lambda x: generalize_age(x, age_bin_size))
        elif most_distinct == 'zip_code':
            zip_level += 1
            result['zip_code'] = df['zip_code'].apply(lambda x: generalize_zip(x, zip_level))
        elif most_distinct == 'gender':
            # Gender has few values — suppress rare categories
            gender_counts = result['gender'].value_counts()
            rare_genders = gender_counts[gender_counts < target_k].index
            result.loc[result['gender'].isin(rare_genders), 'gender'] = 'Other'
    
    # Final suppression of any remaining small groups
    result = suppress_outliers(result, quasi_ids, target_k)
    
    return result

# Apply anonymization
print("\nApplying anonymization for k=5...")
anonymized = achieve_k_anonymity(data, quasi_identifiers, target_k=5)

# Step 3: Verify
print("\nAnonymized dataset sample:")
print(anonymized[quasi_identifiers + [sensitive_attribute]].head(15))

assessment_after = assess_k_anonymity(anonymized, quasi_identifiers)

# Step 4: Measure information loss
def information_loss_metric(original: pd.DataFrame, anonymized: pd.DataFrame, 
                            column: str) -> float:
    """Calculate normalized certainty penalty (NCP) for a column."""
    if original[column].dtype in ['int64', 'float64']:
        original_range = original[column].max() - original[column].min()
        if original_range == 0:
            return 0.0
        
        # For generalized ranges, compute average range width / total range
        if anonymized[column].dtype == 'object' and '-' in str(anonymized[column].iloc[0]):
            widths = anonymized[column].apply(
                lambda x: int(x.split('-')[1]) - int(x.split('-')[0]) if '-' in str(x) else 0
            )
            return (widths.mean() / original_range)
    
    # For categorical: 1 - (distinct_after / distinct_before)
    distinct_before = original[column].nunique()
    distinct_after = anonymized[column].nunique()
    return 1 - (distinct_after / distinct_before)

print(f"\n{'='*60}")
print("INFORMATION LOSS ANALYSIS")
print(f"{'='*60}")
for qi in quasi_identifiers:
    loss = information_loss_metric(data, anonymized, qi)
    print(f"  {qi}: {loss:.2%} information loss")

print(f"\n  Records retained: {len(anonymized)}/{len(data)} "
      f"({len(anonymized)/len(data)*100:.1f}%)")

# Step 5: Check l-diversity on the anonymized data
def check_l_diversity(df: pd.DataFrame, qi: list[str], 
                      sensitive: str, l: int) -> bool:
    """Verify l-diversity after k-anonymity."""
    groups = df.groupby(qi)[sensitive].nunique()
    min_diversity = groups.min()
    
    print(f"\n  L-diversity check (l={l}):")
    print(f"  Minimum distinct sensitive values per group: {min_diversity}")
    print(f"  Result: {'PASS' if min_diversity >= l else 'FAIL'}")
    
    return min_diversity >= l

check_l_diversity(anonymized, quasi_identifiers, sensitive_attribute, l=3)
```

**Expected output:**
```
Original dataset:
   patient_id  age gender zip_code     diagnosis           visit_date  charges
0           1   52      M    10003  Hypertension  2023-01-01 00:00:00   987.45
1           2   38      F    90212      Diabetes  2023-01-01 04:00:00  1542.30
...

K-ANONYMITY ASSESSMENT
Quasi-identifiers: ['age', 'gender', 'zip_code']
Total equivalence classes: 387
Minimum k (current): 1
Unique individuals (k=1, fully identifiable): 312
Groups with k < 5: 380
Records at risk (in groups < 5): 465

Applying anonymization for k=5...
  Iteration 1: Generalizing 'age' (current k=1, ...)
  Iteration 2: Generalizing 'zip_code' (current k=1, ...)
  Iteration 3: Generalizing 'age' (current k=2, ...)
  ...
  Achieved 5-anonymity in 5 iterations
  Age bin size: 9, ZIP generalization level: 2

INFORMATION LOSS ANALYSIS
  age: 11.5% information loss
  zip_code: 60.0% information loss
  gender: 0.0% information loss
  Records retained: 496/500 (99.2%)
```

---

## Security Assessment Perspective

Understanding encryption implementations enables identification of weaknesses during authorized security assessments:

**Common findings in data engineering systems:**
- Encryption keys stored alongside encrypted data (same S3 bucket, same database)
- Use of deprecated algorithms (DES, 3DES, RC4, MD5 for integrity)
- Hard-coded encryption keys in application code or configuration files
- Missing TLS verification (sslmode=prefer or sslmode=require without certificate pinning)
- Key material logged in application debug logs or crash dumps
- Deterministic encryption used where randomized is required
- Missing key rotation (keys unchanged since system deployment)
- Token vaults accessible from the same network segment as the application
- Insufficient entropy in nonce/IV generation (time-based, sequential)
- Backup tapes and snapshots containing plaintext of "encrypted" databases (TDE only protects on-disk, not in memory or during backup)
- ECB mode in legacy integrations with payment processors
- Format-preserving encryption on small domains without additional access controls
- Cloud KMS key policies that grant decrypt to overly broad IAM roles

**Assessment methodology:**
1. Map data flows — identify all points where sensitive data exists in cleartext
2. Verify key management — check key storage, rotation, access controls
3. Test encryption configurations — attempt downgrade attacks, verify minimum TLS version
4. Check for side channels — timing differences in authentication, error message verbosity
5. Validate scope boundaries — ensure tokenized systems truly remove data from scope
6. Review access patterns — identify excessive detokenization or decryption frequency
7. Audit compliance — verify implementation matches documented security architecture

---

## References and Standards

- NIST SP 800-175B: Guideline for Using Cryptographic Standards
- NIST SP 800-38G: Recommendation for Block Cipher Modes — Format-Preserving Encryption
- NIST SP 800-57: Recommendation for Key Management
- NIST SP 800-131A: Transitioning to Use of Cryptographic Algorithms and Key Lengths
- FIPS 197: Advanced Encryption Standard (AES)
- FIPS 203/204/205: Post-Quantum Cryptography Standards
- PCI DSS v4.0: Payment Card Industry Data Security Standard
- GDPR Articles 4, 25, 32: Pseudonymization, Data Protection by Design, Security of Processing
- RFC 8018: PKCS #5 Password-Based Cryptography Specification
- RFC 9180: Hybrid Public Key Encryption (HPKE)
- RFC 7748: Elliptic Curves for Security (Curve25519, Curve448)
