---
corso: "Gestione Piattaforme e DevOps"
fase: "6 — Sicurezza e Compliance"
modulo: 15
titolo: "Secrets Management"
versione: "Vault 1.18 · AWS Secrets Manager · Azure Key Vault · GCP Secret Manager"
livello: "Avanzato"
prerequisiti:
  - "13-sicurezza-piattaforme.md"
  - "05-kubernetes.md"
  - "07-ci-cd.md"
obiettivi:
  - "Progettare un'architettura centralizzata di secrets management con HashiCorp Vault o servizi cloud-native"
  - "Implementare rotation automatica per credenziali database, chiavi API e certificati TLS"
  - "Integrare la distribuzione sicura dei secret in Kubernetes (CSI driver, sidecar, External Secrets Operator)"
  - "Configurare audit logging e alerting per ogni accesso ai secret"
  - "Definire procedure di emergency rotation e disaster recovery per il vault"
tag: [vault, secrets-manager, key-vault, rotation, gitleaks, csi-driver, external-secrets, mtls]
---

# Secrets Management — Documentazione Completa

> **Modulo 15** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Progettare un'architettura centralizzata di secrets management con HashiCorp Vault o servizi cloud-native
> 2. Implementare rotation automatica per credenziali database, chiavi API e certificati TLS
> 3. Integrare la distribuzione sicura dei secret in Kubernetes (CSI driver, sidecar, External Secrets Operator)
> 4. Configurare audit logging e alerting per ogni accesso ai secret
> 5. Definire procedure di emergency rotation e disaster recovery per il vault
>
> **Prerequisiti:** [Sicurezza delle Piattaforme](13-sicurezza-piattaforme.md) · [Kubernetes](05-kubernetes.md) · [CI/CD](07-ci-cd.md)
> **Tempo stimato:** 8-10 ore · **Livello:** Avanzato

## Idee guida

1. **Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager.** Native cloud preferito.
2. **Rotation per secret type:** DB password 90gg, API key 180gg, TLS cert 90gg, KMS key 1y.
3. **Audit log integration mandatory.** Chi accede cosa quando.
4. **gitleaks scan in CI per detect secret leaked.**


## Indice

1. [Panoramica e Concetti Fondamentali](#1-panoramica-e-concetti-fondamentali)
2. [HashiCorp Vault](#2-hashicorp-vault)
3. [Vault — Secrets Engines in Dettaglio](#3-vault--secrets-engines-in-dettaglio)
4. [Vault — Integrazione con Applicazioni](#4-vault--integrazione-con-applicazioni)
5. [AWS Secrets Manager e SSM Parameter Store](#5-aws-secrets-manager-e-ssm-parameter-store)
6. [Azure Key Vault](#6-azure-key-vault)
7. [GCP Secret Manager](#7-gcp-secret-manager)
8. [SOPS (Secrets OPerationS)](#8-sops-secrets-operations)
9. [cert-manager e Gestione Certificati](#9-cert-manager-e-gestione-certificati)
10. [Secret Rotation e Lifecycle](#10-secret-rotation-e-lifecycle)
11. [Kubernetes Secrets](#11-kubernetes-secrets)
12. [Best Practices](#12-best-practices)
13. [Vault Enterprise — Namespace e Multi-Tenancy](#13-vault-enterprise--namespace-e-multi-tenancy)
14. [Vault Enterprise — Performance Replication e Disaster Recovery](#14-vault-enterprise--performance-replication-e-disaster-recovery)
15. [Confronto Cloud Secrets Manager](#15-confronto-cloud-secrets-manager)
16. [Secrets nelle Pipeline CI/CD — OIDC e Credenziali Effimere](#16-secrets-nelle-pipeline-cicd--oidc-e-credenziali-effimere)
17. [Secrets Scanning Avanzato](#17-secrets-scanning-avanzato)
18. [Secrets Governance e Identita Non-Umane (NHI)](#18-secrets-governance-e-identita-non-umane-nhi)
19. [Zero-Trust Secrets Access](#19-zero-trust-secrets-access)

---

## 1. Panoramica e Concetti Fondamentali

### Definizione di Secret

Un **secret** e qualsiasi informazione che garantisce accesso privilegiato a sistemi, dati o risorse.
Le categorie principali includono:

- **Password** — credenziali di accesso per utenti, servizi e database
- **API Key** — token di autenticazione per servizi REST, SaaS e cloud provider
- **Certificati TLS/SSL** — chiavi pubbliche e private per la crittografia del traffico
- **Token OAuth/JWT** — credenziali temporanee per l'autenticazione delegata
- **Chiavi di crittografia** — chiavi simmetriche (AES) e asimmetriche (RSA, ECDSA) per proteggere dati
- **Connection string** — stringhe di connessione a database contenenti host, utente e password
- **SSH key** — coppie di chiavi per l'accesso remoto ai server
- **Signing key** — chiavi per la firma digitale di artifact, container image e commit

### Rischi della Gestione Inadeguata

La gestione impropria dei secret rappresenta una delle vulnerabilita piu critiche in ambito IT:

**Hardcoded secrets nel codice sorgente:**
```python
# MAI FARE QUESTO — secret esposto nel codice
DATABASE_URL = "postgresql://admin:S3cretP@ss!@db.prod.internal:5432/appdb"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

**Secrets committati in repository Git:**
Anche dopo la rimozione, i secret restano nella cronologia Git. Strumenti come `trufflehog` e `gitleaks`
possono estrarre secret da qualsiasi commit storico.

**Secrets in variabili d'ambiente non protette:**
Le variabili d'ambiente sono visibili tramite `/proc/<pid>/environ` su Linux, nei dump di processo,
nei log di debug e nei sistemi di orchestrazione che espongono le env var nei manifest.

**Secrets condivisi via canali non sicuri:**
Email, Slack, documenti condivisi e ticket tracker non sono canali adeguati per la distribuzione di secret.

### Principi Fondamentali

| Principio | Descrizione |
|---|---|
| **Least Privilege** | Ogni identita riceve solo i permessi strettamente necessari |
| **Rotation** | I secret vengono ruotati regolarmente per limitare l'impatto di una compromissione |
| **Audit** | Ogni accesso ai secret viene registrato e monitorato |
| **Encryption at Rest** | I secret sono crittografati quando memorizzati su disco o database |
| **Encryption in Transit** | I secret viaggiano sempre su canali crittografati (TLS 1.2+) |
| **Short-lived Credentials** | Preferire credenziali temporanee con TTL breve rispetto a credenziali statiche |
| **Centralized Management** | Gestione centralizzata per visibilita, controllo e compliance |
| **Zero Trust** | Non fidarsi mai implicitamente, verificare sempre l'identita e i permessi |

### Secrets Lifecycle

Il ciclo di vita di un secret comprende cinque fasi:

```
┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌────────────┐
│ Creation │───>│ Storage  │───>│ Distribution │───>│ Rotation │───>│ Revocation │
└──────────┘    └──────────┘    └──────────────┘    └──────────┘    └────────────┘
     │                                                                     │
     └─────────────────────────────────────────────────────────────────────┘
                            Ciclo continuo
```

1. **Creation** — generazione del secret con entropia sufficiente (CSPRNG)
2. **Storage** — memorizzazione sicura in un vault crittografato con accesso controllato
3. **Distribution** — consegna sicura ai consumer autorizzati (injection, API, sidecar)
4. **Rotation** — sostituzione periodica o event-driven del secret
5. **Revocation** — invalidazione immediata in caso di compromissione o decommissioning

### Static vs Dynamic Secrets

**Static secrets** — creati manualmente, memorizzati nel vault, validi fino a rotazione esplicita:
- Password di database configurate manualmente
- API key generate una volta e riutilizzate
- Chiavi SSH a lunga durata

**Dynamic secrets** — generati on-demand con TTL definito, automaticamente revocati alla scadenza:
- Credenziali database temporanee generate da Vault
- Token AWS STS con durata limitata
- Certificati TLS con validita breve

I dynamic secret riducono drasticamente la superficie di attacco perche ogni credenziale
ha una finestra di validita limitata e viene revocata automaticamente.

---

## 2. HashiCorp Vault

### Architettura

HashiCorp Vault e il sistema di secrets management piu diffuso in ambienti enterprise.
L'architettura si compone di:

- **Barrier** — livello di crittografia che protegge tutti i dati. Vault opera in modo "sealed" fino
  all'unseal, momento in cui la master key viene ricostruita per decrittare il barrier
- **Storage Backend** — persistenza dei dati crittografati (Consul, Raft integrato, S3, PostgreSQL, etcd)
- **Secrets Engines** — moduli che generano, memorizzano o trasformano secret
- **Auth Methods** — meccanismi di autenticazione degli utenti e delle applicazioni
- **Audit Devices** — registrazione di ogni operazione per compliance e forensics
- **Policy Engine** — sistema di autorizzazione path-based in formato HCL

```
                    ┌─────────────────────────────┐
                    │        Vault API (HTTPS)     │
                    ├─────────────────────────────┤
                    │       Policy Engine          │
                    ├──────┬──────┬───────┬────────┤
                    │ Auth │Secret│ Audit │ System │
                    │Methods│Engines│Devices│Backend│
                    ├──────┴──────┴───────┴────────┤
                    │         Barrier (AES-256-GCM) │
                    ├─────────────────────────────┤
                    │      Storage Backend         │
                    │  (Raft / Consul / S3 / ...)  │
                    └─────────────────────────────┘
```

### Installazione

**Installazione da binary (Linux):**
```bash
# Scaricare l'ultima versione stabile
VAULT_VERSION="1.17.3"
wget "https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip"
unzip "vault_${VAULT_VERSION}_linux_amd64.zip"
sudo mv vault /usr/local/bin/
vault version

# Abilitare l'autocompletamento
vault -autocomplete-install
```

**Installazione con Docker:**
```bash
docker run -d \
  --name vault \
  --cap-add IPC_LOCK \
  -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=dev-root-token' \
  hashicorp/vault:1.17.3 server -dev

# Il flag -dev avvia Vault in modalita sviluppo (non per produzione):
# - Gia inizializzato e unsealed
# - Storage in memoria (non persistente)
# - TLS disabilitato
```

**Installazione con Helm su Kubernetes:**
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Installazione in modalita HA con Raft integrato
helm install vault hashicorp/vault \
  --namespace vault \
  --create-namespace \
  --set server.ha.enabled=true \
  --set server.ha.replicas=3 \
  --set server.ha.raft.enabled=true \
  --set server.dataStorage.size=10Gi \
  --set ui.enabled=true
```

**Configurazione server per produzione** (`vault-config.hcl`):
```hcl
storage "raft" {
  path    = "/opt/vault/data"
  node_id = "vault-node-1"

  retry_join {
    leader_api_addr = "https://vault-node-2:8200"
  }
  retry_join {
    leader_api_addr = "https://vault-node-3:8200"
  }
}

listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/opt/vault/tls/vault-cert.pem"
  tls_key_file  = "/opt/vault/tls/vault-key.pem"

  # Timeout per richieste lente
  max_request_duration = "90s"
}

api_addr     = "https://vault-node-1.example.com:8200"
cluster_addr = "https://vault-node-1.example.com:8201"

# Telemetria
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname          = true
}

# Audit — registrare TUTTE le operazioni
audit {
  type = "file"
  path = "file"
  options = {
    file_path = "/var/log/vault/audit.log"
  }
}
```

### Inizializzazione e Unseal

```bash
# Inizializzazione con Shamir's Secret Sharing
# 5 chiavi totali, soglia di 3 per unseal
vault operator init -key-shares=5 -key-threshold=3

# Output:
# Unseal Key 1: aB3d...
# Unseal Key 2: eF7g...
# Unseal Key 3: hI9j...
# Unseal Key 4: kL1m...
# Unseal Key 5: nO3p...
# Initial Root Token: hvs.aBcDeFgHiJkL

# CRITICO: distribuire le chiavi a persone diverse
# MAI memorizzare tutte le chiavi nello stesso luogo

# Unseal (ripetere con 3 chiavi diverse)
vault operator unseal aB3d...
vault operator unseal eF7g...
vault operator unseal hI9j...

# Verificare lo stato
vault status
```

### Auto-Unseal

L'auto-unseal delega la protezione della master key a un KMS esterno, eliminando
la necessita dell'intervento umano al riavvio:

**Auto-unseal con AWS KMS:**
```hcl
seal "awskms" {
  region     = "eu-west-1"
  kms_key_id = "arn:aws:kms:eu-west-1:123456789:key/abcd-1234-efgh-5678"
}
```

**Auto-unseal con Azure Key Vault:**
```hcl
seal "azurekeyvault" {
  tenant_id  = "aaaabbbb-cccc-dddd-eeee-ffffgggghhhh"
  vault_name = "vault-unseal-keyvault"
  key_name   = "vault-unseal-key"
}
```

**Auto-unseal con GCP Cloud KMS:**
```hcl
seal "gcpckms" {
  project    = "my-project"
  region     = "global"
  key_ring   = "vault-keyring"
  crypto_key = "vault-unseal-key"
}
```

**Transit unseal (un Vault sblocca un altro Vault):**
```hcl
seal "transit" {
  address         = "https://primary-vault.example.com:8200"
  token           = "hvs.transit-unseal-token"
  disable_renewal = false
  key_name        = "autounseal"
  mount_path      = "transit/"
}
```

### Auth Methods

```bash
# Abilitare AppRole (per applicazioni e automazione)
vault auth enable approle

vault write auth/approle/role/webapp \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=10m \
  secret_id_num_uses=1 \
  token_policies="webapp-policy"

# Ottenere role_id e secret_id
vault read auth/approle/role/webapp/role-id
vault write -f auth/approle/role/webapp/secret-id

# Login con AppRole
vault write auth/approle/login \
  role_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  secret_id="yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"

# Abilitare Kubernetes auth
vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443" \
  token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

vault write auth/kubernetes/role/webapp \
  bound_service_account_names=webapp-sa \
  bound_service_account_namespaces=production \
  policies=webapp-policy \
  ttl=1h

# Abilitare OIDC
vault auth enable oidc

vault write auth/oidc/config \
  oidc_discovery_url="https://accounts.google.com" \
  oidc_client_id="xxxx.apps.googleusercontent.com" \
  oidc_client_secret="GOCSPX-xxxxxxxxx" \
  default_role="reader"

# Abilitare LDAP
vault auth enable ldap

vault write auth/ldap/config \
  url="ldaps://ldap.example.com:636" \
  userattr="sAMAccountName" \
  userdn="ou=Users,dc=example,dc=com" \
  groupdn="ou=Groups,dc=example,dc=com" \
  groupfilter="(&(objectClass=group)(member:1.2.840.113556.1.4.1941:={{.UserDN}}))" \
  certificate=@ldap-ca.pem \
  insecure_tls=false
```

### Policies

Le policy di Vault controllano l'accesso ai path tramite capabilities:

```hcl
# webapp-policy.hcl
# Accesso ai secret dell'applicazione web
path "secret/data/webapp/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Solo lettura per i secret condivisi
path "secret/data/shared/*" {
  capabilities = ["read", "list"]
}

# Accesso alle credenziali database dinamiche
path "database/creds/webapp-role" {
  capabilities = ["read"]
}

# Accesso ai certificati PKI
path "pki/issue/webapp" {
  capabilities = ["create", "update"]
}

# Negare esplicitamente l'accesso ai secret di altri team
path "secret/data/infra/*" {
  capabilities = ["deny"]
}

# Permettere il rinnovo del proprio token
path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
```

```bash
# Applicare la policy
vault policy write webapp-policy webapp-policy.hcl

# Verificare la policy
vault policy read webapp-policy

# Elencare tutte le policy
vault policy list
```

### Audit Logging

```bash
# Abilitare audit su file
vault audit enable file file_path=/var/log/vault/audit.log

# Abilitare audit su syslog
vault audit enable syslog tag="vault" facility="AUTH"

# Abilitare audit su socket (per SIEM)
vault audit enable socket address="logstash.example.com:9200" socket_type="tcp"

# Ogni operazione viene registrata in formato JSON:
# {
#   "type": "request",
#   "auth": { "client_token": "hmac-sha256:...", "policies": ["webapp-policy"] },
#   "request": { "path": "secret/data/webapp/db", "operation": "read" },
#   "response": { "data": { "keys": ["username", "password"] } }
# }
# I valori sensibili sono HMAC-ati per protezione
```

---

## 3. Vault — Secrets Engines in Dettaglio

### KV v2 (Key-Value con Versioning)

Il secrets engine KV v2 supporta il versioning dei secret, consentendo di mantenere
la cronologia delle modifiche e di ripristinare versioni precedenti.

```bash
# Abilitare KV v2
vault secrets enable -path=secret -version=2 kv

# Scrivere un secret
vault kv put secret/webapp/database \
  username="webapp_user" \
  password="P@ssw0rd!2024" \
  host="db.prod.internal" \
  port=5432

# Leggere il secret (versione corrente)
vault kv get secret/webapp/database

# Leggere una versione specifica
vault kv get -version=2 secret/webapp/database

# Leggere i metadata
vault kv metadata get secret/webapp/database

# Configurare il numero massimo di versioni
vault kv metadata put -max-versions=10 secret/webapp/database

# Configurare check-and-set (CAS) per prevenire sovrascritture concorrenti
vault kv metadata put -cas-required=true secret/webapp/database

# Scrivere con CAS (deve specificare la versione corrente)
vault kv put -cas=3 secret/webapp/database \
  username="webapp_user" \
  password="N3wP@ssw0rd!2024"

# Soft delete (la versione e marcata come eliminata ma recuperabile)
vault kv delete -versions=3 secret/webapp/database

# Ripristinare una versione soft-deleted
vault kv undelete -versions=3 secret/webapp/database

# Hard delete (irreversibile)
vault kv destroy -versions=1,2 secret/webapp/database

# Eliminare tutti i metadata e tutte le versioni
vault kv metadata delete secret/webapp/database

# Elencare tutti i secret sotto un path
vault kv list secret/webapp/
```

### PKI (Public Key Infrastructure)

Il secrets engine PKI consente di gestire un'intera infrastruttura a chiave pubblica:

```bash
# Abilitare il secrets engine PKI per la Root CA
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki

# Generare la Root CA
vault write pki/root/generate/internal \
  common_name="Example Inc Root CA" \
  issuer_name="root-2024" \
  ttl=87600h \
  key_type=ec \
  key_bits=384

# Configurare gli URL di distribuzione
vault write pki/config/urls \
  issuing_certificates="https://vault.example.com:8200/v1/pki/ca" \
  crl_distribution_points="https://vault.example.com:8200/v1/pki/crl" \
  ocsp_servers="https://vault.example.com:8200/v1/pki/ocsp"

# Abilitare il secrets engine per la Intermediate CA
vault secrets enable -path=pki_int pki
vault secrets tune -max-lease-ttl=43800h pki_int

# Generare il CSR per la Intermediate CA
vault write -format=json pki_int/intermediate/generate/internal \
  common_name="Example Inc Intermediate CA" \
  issuer_name="intermediate-2024" \
  key_type=ec \
  key_bits=256 \
  | jq -r '.data.csr' > pki_int.csr

# Firmare il CSR con la Root CA
vault write -format=json pki/root/sign-intermediate \
  csr=@pki_int.csr \
  format=pem_bundle \
  ttl=43800h \
  | jq -r '.data.certificate' > signed_intermediate.pem

# Importare il certificato firmato nella Intermediate CA
vault write pki_int/intermediate/set-signed \
  certificate=@signed_intermediate.pem

# Creare un ruolo per l'emissione di certificati
vault write pki_int/roles/webapp \
  allowed_domains="example.com,internal.example.com" \
  allow_subdomains=true \
  allow_bare_domains=false \
  max_ttl=720h \
  key_type=ec \
  key_bits=256 \
  require_cn=false \
  allowed_uri_sans="spiffe://example.com/*"

# Emettere un certificato
vault write pki_int/issue/webapp \
  common_name="api.example.com" \
  alt_names="api-v2.example.com" \
  ttl=72h

# Revocare un certificato
vault write pki_int/revoke serial_number="39:dd:2e:90:..."

# Ruotare la CRL
vault write pki_int/tidy \
  tidy_cert_store=true \
  tidy_revoked_certs=true \
  safety_buffer="72h"
```

### Transit (Encryption as a Service)

Il secrets engine Transit offre crittografia come servizio senza esporre le chiavi:

```bash
# Abilitare Transit
vault secrets enable transit

# Creare una chiave di crittografia
vault write -f transit/keys/payment-data \
  type=aes256-gcm96 \
  auto_rotate_period=720h

# Crittografare dati (input in base64)
vault write transit/encrypt/payment-data \
  plaintext=$(echo -n "4111-1111-1111-1111" | base64)

# Output: ciphertext = vault:v1:aBcDeFgHiJkLmNoPqRsTuVwXyZ...

# Decrittografare dati
vault write -format=json transit/decrypt/payment-data \
  ciphertext="vault:v1:aBcDeFgHiJkLmNoPqRsTuVwXyZ..." \
  | jq -r '.data.plaintext' | base64 -d

# Ruotare la chiave (le vecchie versioni restano per decrittazione)
vault write -f transit/keys/payment-data/rotate

# Re-wrapping — ricrittografare con la chiave piu recente senza esporre il plaintext
vault write transit/rewrap/payment-data \
  ciphertext="vault:v1:aBcDeFgHiJkLmNoPqRsTuVwXyZ..."

# Output: ciphertext = vault:v2:xYzAbCdEfGhIjKlMnOpQrS...

# Firmare dati
vault write transit/sign/signing-key \
  input=$(echo -n "data-to-sign" | base64) \
  hash_algorithm=sha2-256 \
  signature_algorithm=pkcs1v15

# Verificare la firma
vault write transit/verify/signing-key \
  input=$(echo -n "data-to-sign" | base64) \
  signature="vault:v1:MEUCIQDx..."

# Generare un data key per envelope encryption
vault write -f transit/datakey/plaintext/payment-data

# Output: plaintext (chiave effimera) + ciphertext (chiave protetta da Vault)
# Usare plaintext per crittografare localmente, memorizzare ciphertext accanto ai dati
```

### Database (Dynamic Credentials)

Il secrets engine Database genera credenziali effimere per database:

```bash
# Abilitare il secrets engine
vault secrets enable database

# Configurare la connessione a PostgreSQL
vault write database/config/webapp-db \
  plugin_name=postgresql-database-plugin \
  allowed_roles="webapp-role,readonly-role" \
  connection_url="postgresql://{{username}}:{{password}}@db.prod.internal:5432/webapp?sslmode=require" \
  username="vault_admin" \
  password="VaultAdminPassword!" \
  password_authentication="scram-sha-256"

# Ruotare la password dell'utente di connessione (Vault la gestisce internamente)
vault write -f database/rotate-root/webapp-db

# Creare un ruolo per credenziali dinamiche (PostgreSQL)
vault write database/roles/webapp-role \
  db_name=webapp-db \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  revocation_statements="REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"; \
    DROP ROLE IF EXISTS \"{{name}}\";" \
  default_ttl=1h \
  max_ttl=24h

# Creare un ruolo read-only
vault write database/roles/readonly-role \
  db_name=webapp-db \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
  default_ttl=30m \
  max_ttl=4h

# Ottenere credenziali dinamiche
vault read database/creds/webapp-role

# Output:
# Key                Value
# lease_id           database/creds/webapp-role/abcd1234
# lease_duration     1h
# username           v-approle-webapp-r-aBcDeFgH-1234567890
# password           xYz-AbCdEfGhIjKl

# Configurare la connessione a MySQL
vault write database/config/mysql-db \
  plugin_name=mysql-database-plugin \
  allowed_roles="mysql-webapp" \
  connection_url="{{username}}:{{password}}@tcp(mysql.prod.internal:3306)/" \
  username="vault_admin" \
  password="VaultMySQLPassword!"

vault write database/roles/mysql-webapp \
  db_name=mysql-db \
  creation_statements="CREATE USER '{{name}}'@'%' IDENTIFIED BY '{{password}}'; \
    GRANT SELECT, INSERT, UPDATE, DELETE ON webapp.* TO '{{name}}'@'%';" \
  default_ttl=1h \
  max_ttl=24h

# Configurare la connessione a MongoDB
vault write database/config/mongo-db \
  plugin_name=mongodb-database-plugin \
  allowed_roles="mongo-webapp" \
  connection_url="mongodb://{{username}}:{{password}}@mongo.prod.internal:27017/admin?tls=true" \
  username="vault_admin" \
  password="VaultMongoPassword!"

vault write database/roles/mongo-webapp \
  db_name=mongo-db \
  creation_statements='{"db":"webapp","roles":[{"role":"readWrite"}]}' \
  default_ttl=1h \
  max_ttl=24h

# Rinnovare un lease
vault lease renew database/creds/webapp-role/abcd1234

# Revocare un lease (le credenziali vengono eliminate dal database)
vault lease revoke database/creds/webapp-role/abcd1234

# Revocare tutti i lease per un prefisso
vault lease revoke -prefix database/creds/webapp-role
```

---

## 4. Vault — Integrazione con Applicazioni

### Vault Agent

Vault Agent e un processo daemon che gestisce l'autenticazione automatica,
il caching dei token e il rendering di template con i secret:

```hcl
# vault-agent-config.hcl
pid_file = "/tmp/vault-agent.pid"

vault {
  address = "https://vault.example.com:8200"
  tls_skip_verify = false
  ca_cert = "/etc/vault/ca.pem"
}

auto_auth {
  method "approle" {
    config = {
      role_id_file_path   = "/etc/vault/role-id"
      secret_id_file_path = "/etc/vault/secret-id"
      remove_secret_id_file_after_reading = true
    }
  }

  sink "file" {
    config = {
      path = "/tmp/vault-token"
      mode = 0600
    }
  }
}

cache {
  use_auto_auth_token = true
  persist "kubernetes" {
    path = "/vault/agent-cache"
  }
}

template {
  source      = "/etc/vault/templates/db-config.tpl"
  destination = "/app/config/database.yml"
  perms       = 0600
  command     = "systemctl reload webapp"

  wait {
    min = "5s"
    max = "30s"
  }
}

template {
  source      = "/etc/vault/templates/tls-cert.tpl"
  destination = "/app/tls/cert.pem"
  perms       = 0644
}

template {
  source      = "/etc/vault/templates/tls-key.tpl"
  destination = "/app/tls/key.pem"
  perms       = 0600
}
```

**Template di esempio** (`db-config.tpl`):
```
{{ with secret "database/creds/webapp-role" }}
database:
  host: db.prod.internal
  port: 5432
  name: webapp
  username: {{ .Data.username }}
  password: {{ .Data.password }}
  pool_size: 10
{{ end }}
```

### Vault Agent Injector per Kubernetes

Il Vault Agent Injector utilizza un MutatingWebhookConfiguration per iniettare
automaticamente un sidecar Vault Agent nei Pod:

```yaml
# deployment-con-vault-injector.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
      annotations:
        # Abilitare l'injection
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "webapp"
        vault.hashicorp.com/agent-inject-status: "update"

        # Secret del database
        vault.hashicorp.com/agent-inject-secret-db-creds: "database/creds/webapp-role"
        vault.hashicorp.com/agent-inject-template-db-creds: |
          {{ with secret "database/creds/webapp-role" -}}
          export DB_USERNAME="{{ .Data.username }}"
          export DB_PASSWORD="{{ .Data.password }}"
          {{- end }}

        # Certificato TLS
        vault.hashicorp.com/agent-inject-secret-tls-cert: "pki_int/issue/webapp"
        vault.hashicorp.com/agent-inject-template-tls-cert: |
          {{ with secret "pki_int/issue/webapp" "common_name=webapp.example.com" "ttl=72h" -}}
          {{ .Data.certificate }}
          {{ .Data.ca_chain }}
          {{- end }}

        vault.hashicorp.com/agent-inject-secret-tls-key: "pki_int/issue/webapp"
        vault.hashicorp.com/agent-inject-template-tls-key: |
          {{ with secret "pki_int/issue/webapp" "common_name=webapp.example.com" "ttl=72h" -}}
          {{ .Data.private_key }}
          {{- end }}
    spec:
      serviceAccountName: webapp-sa
      containers:
        - name: webapp
          image: webapp:1.5.0
          command: ["/bin/sh", "-c"]
          args:
            - source /vault/secrets/db-creds && exec /app/start
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
```

### Vault Secrets Operator

Il Vault Secrets Operator (VSO) e l'approccio nativo Kubernetes per sincronizzare
i secret da Vault in Kubernetes Secret:

```yaml
# vault-connection.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultConnection
metadata:
  name: vault-connection
  namespace: vault-secrets-operator-system
spec:
  address: https://vault.example.com:8200
  caCertSecretRef: vault-ca-cert
  skipTLSVerify: false
---
# vault-auth.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultAuth
metadata:
  name: vault-auth
  namespace: production
spec:
  vaultConnectionRef: vault-connection
  method: kubernetes
  mount: kubernetes
  kubernetes:
    role: webapp
    serviceAccount: webapp-sa
---
# VaultStaticSecret — sincronizza un secret KV
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultStaticSecret
metadata:
  name: webapp-config
  namespace: production
spec:
  vaultAuthRef: vault-auth
  mount: secret
  path: webapp/config
  type: kv-v2
  refreshAfter: 60s
  destination:
    name: webapp-config-secret
    create: true
    labels:
      app: webapp
    transformation:
      excludeRaw: true
      templates:
        config.yaml:
          text: |
            database:
              host: {{ get .Secrets "db_host" }}
              password: {{ get .Secrets "db_password" }}
---
# VaultDynamicSecret — genera credenziali dinamiche
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultDynamicSecret
metadata:
  name: webapp-db-creds
  namespace: production
spec:
  vaultAuthRef: vault-auth
  mount: database
  path: creds/webapp-role
  renewalPercent: 67
  destination:
    name: webapp-db-credentials
    create: true
---
# VaultPKISecret — gestisce certificati TLS
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultPKISecret
metadata:
  name: webapp-tls
  namespace: production
spec:
  vaultAuthRef: vault-auth
  mount: pki_int
  role: webapp
  commonName: webapp.example.com
  altNames:
    - api.example.com
  ttl: 72h
  expiryOffset: 24h
  destination:
    name: webapp-tls-secret
    create: true
    type: kubernetes.io/tls
```

### Accesso Diretto via API

```bash
# Login con AppRole
VAULT_TOKEN=$(curl -s --request POST \
  --data '{"role_id":"xxx","secret_id":"yyy"}' \
  https://vault.example.com:8200/v1/auth/approle/login \
  | jq -r '.auth.client_token')

# Leggere un secret KV v2
curl -s --header "X-Vault-Token: ${VAULT_TOKEN}" \
  https://vault.example.com:8200/v1/secret/data/webapp/database \
  | jq '.data.data'

# Scrivere un secret
curl -s --request POST \
  --header "X-Vault-Token: ${VAULT_TOKEN}" \
  --data '{"data":{"username":"admin","password":"new-pass"}}' \
  https://vault.example.com:8200/v1/secret/data/webapp/database

# Ottenere credenziali database dinamiche
curl -s --header "X-Vault-Token: ${VAULT_TOKEN}" \
  https://vault.example.com:8200/v1/database/creds/webapp-role \
  | jq '.data'

# Crittografare con Transit
curl -s --request POST \
  --header "X-Vault-Token: ${VAULT_TOKEN}" \
  --data "{\"plaintext\":\"$(echo -n 'dati sensibili' | base64)\"}" \
  https://vault.example.com:8200/v1/transit/encrypt/payment-data \
  | jq '.data.ciphertext'
```

### SDK — Esempi Applicativi

**Python (hvac):**
```python
import hvac

client = hvac.Client(url='https://vault.example.com:8200')

# Login con AppRole
client.auth.approle.login(
    role_id='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    secret_id='yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy'
)

# Leggere un secret
secret = client.secrets.kv.v2.read_secret_version(
    path='webapp/database',
    mount_point='secret'
)
db_password = secret['data']['data']['password']

# Ottenere credenziali dinamiche
creds = client.secrets.database.generate_credentials(
    name='webapp-role',
    mount_point='database'
)
db_user = creds['data']['username']
db_pass = creds['data']['password']
lease_id = creds['lease_id']
```

**Go:**
```go
package main

import (
    "context"
    "fmt"
    "log"

    vault "github.com/hashicorp/vault-client-go"
    "github.com/hashicorp/vault-client-go/schema"
)

func main() {
    ctx := context.Background()

    client, err := vault.New(
        vault.WithAddress("https://vault.example.com:8200"),
    )
    if err != nil {
        log.Fatal(err)
    }

    // Login con AppRole
    resp, err := client.Auth.AppRoleLogin(ctx, schema.AppRoleLoginRequest{
        RoleId:   "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        SecretId: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
    })
    if err != nil {
        log.Fatal(err)
    }
    client.SetToken(resp.Auth.ClientToken)

    // Leggere un secret KV v2
    secret, err := client.Secrets.KvV2Read(ctx, "webapp/database",
        vault.WithMountPath("secret"),
    )
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("Password: %s\n", secret.Data.Data["password"])
}
```

**Node.js (node-vault):**
```javascript
const vault = require("node-vault")({
  apiVersion: "v1",
  endpoint: "https://vault.example.com:8200",
});

async function getSecret() {
  // Login con AppRole
  const loginResult = await vault.approleLogin({
    role_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    secret_id: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
  });
  vault.token = loginResult.auth.client_token;

  // Leggere un secret KV v2
  const secret = await vault.read("secret/data/webapp/database");
  const password = secret.data.data.password;

  // Ottenere credenziali database dinamiche
  const creds = await vault.read("database/creds/webapp-role");
  console.log(`DB User: ${creds.data.username}`);
  console.log(`DB Pass: ${creds.data.password}`);
}

getSecret().catch(console.error);
```

---

## 5. AWS Secrets Manager e SSM Parameter Store

### AWS Secrets Manager

AWS Secrets Manager e il servizio gestito per la memorizzazione, la rotazione
e il recupero di secret in ambiente AWS.

```bash
# Creare un secret
aws secretsmanager create-secret \
  --name "prod/webapp/database" \
  --description "Credenziali database di produzione per webapp" \
  --secret-string '{"username":"admin","password":"P@ssw0rd!2024","host":"db.prod.internal","port":5432}' \
  --kms-key-id "alias/secrets-key" \
  --tags '[{"Key":"Environment","Value":"production"},{"Key":"Application","Value":"webapp"}]'

# Recuperare un secret
aws secretsmanager get-secret-value \
  --secret-id "prod/webapp/database" \
  --query 'SecretString' --output text | jq .

# Recuperare una versione specifica
aws secretsmanager get-secret-value \
  --secret-id "prod/webapp/database" \
  --version-stage "AWSPREVIOUS"

# Aggiornare un secret
aws secretsmanager update-secret \
  --secret-id "prod/webapp/database" \
  --secret-string '{"username":"admin","password":"N3wP@ssw0rd!2025"}'

# Elencare tutti i secret
aws secretsmanager list-secrets \
  --filters Key=tag-key,Values=Environment Key=tag-value,Values=production

# Eliminare un secret (con periodo di recupero)
aws secretsmanager delete-secret \
  --secret-id "prod/webapp/database" \
  --recovery-window-in-days 30

# Ripristinare un secret eliminato
aws secretsmanager restore-secret \
  --secret-id "prod/webapp/database"

# Replicare un secret cross-region
aws secretsmanager replicate-secret-to-regions \
  --secret-id "prod/webapp/database" \
  --add-replica-regions Region=eu-central-1,KmsKeyId=alias/secrets-key-eu
```

**Rotazione automatica con Lambda:**
```bash
# Abilitare la rotazione automatica
aws secretsmanager rotate-secret \
  --secret-id "prod/webapp/database" \
  --rotation-lambda-arn "arn:aws:lambda:eu-west-1:123456789:function:SecretsRotation" \
  --rotation-rules '{"ScheduleExpression":"rate(30 days)","Duration":"2h"}'
```

**Lambda di rotazione per RDS (Python):**
```python
import boto3
import json
import string
import secrets

def lambda_handler(event, context):
    secret_id = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    sm_client = boto3.client('secretsmanager')

    if step == "createSecret":
        # Generare una nuova password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        new_password = ''.join(secrets.choice(alphabet) for _ in range(32))

        current = sm_client.get_secret_value(SecretId=secret_id, VersionStage="AWSCURRENT")
        current_dict = json.loads(current['SecretString'])
        current_dict['password'] = new_password

        sm_client.put_secret_value(
            SecretId=secret_id,
            ClientRequestToken=token,
            SecretString=json.dumps(current_dict),
            VersionStages=['AWSPENDING']
        )

    elif step == "setSecret":
        # Aggiornare la password nel database
        pending = sm_client.get_secret_value(
            SecretId=secret_id, VersionId=token, VersionStage="AWSPENDING"
        )
        creds = json.loads(pending['SecretString'])
        # Connettersi al database e aggiornare la password
        # conn = psycopg2.connect(host=creds['host'], ...)
        # conn.cursor().execute("ALTER USER ... PASSWORD ...")

    elif step == "testSecret":
        # Verificare che le nuove credenziali funzionino
        pending = sm_client.get_secret_value(
            SecretId=secret_id, VersionId=token, VersionStage="AWSPENDING"
        )
        creds = json.loads(pending['SecretString'])
        # Tentare la connessione con le nuove credenziali

    elif step == "finishSecret":
        # Promuovere AWSPENDING a AWSCURRENT
        versions = sm_client.describe_secret(SecretId=secret_id)['VersionIdsToStages']
        current_version = [v for v, s in versions.items() if "AWSCURRENT" in s][0]

        sm_client.update_secret_version_stage(
            SecretId=secret_id,
            VersionStage="AWSCURRENT",
            MoveToVersionId=token,
            RemoveFromVersionId=current_version
        )
```

**Resource policy per cross-account access:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::999888777666:role/CrossAccountSecretsReader"
      },
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Environment": "production"
        }
      }
    }
  ]
}
```

### SSM Parameter Store

```bash
# Creare un parametro SecureString (crittografato con KMS)
aws ssm put-parameter \
  --name "/prod/webapp/database/password" \
  --value "P@ssw0rd!2024" \
  --type SecureString \
  --key-id "alias/ssm-key" \
  --tags '[{"Key":"Environment","Value":"production"}]'

# Creare una gerarchia di parametri
aws ssm put-parameter --name "/prod/webapp/database/host" --value "db.prod.internal" --type String
aws ssm put-parameter --name "/prod/webapp/database/port" --value "5432" --type String
aws ssm put-parameter --name "/prod/webapp/database/username" --value "webapp_user" --type String
aws ssm put-parameter --name "/prod/webapp/database/password" --value "P@ss!" --type SecureString

# Recuperare un singolo parametro (con decrittazione)
aws ssm get-parameter \
  --name "/prod/webapp/database/password" \
  --with-decryption \
  --query 'Parameter.Value' --output text

# Recuperare tutti i parametri sotto un path
aws ssm get-parameters-by-path \
  --path "/prod/webapp/database" \
  --with-decryption \
  --recursive

# Parameter Store Advanced — policy di scadenza e notifica
aws ssm put-parameter \
  --name "/prod/webapp/api-key" \
  --value "ak_live_xxxxxxxxx" \
  --type SecureString \
  --tier Advanced \
  --policies '[
    {"Type":"Expiration","Version":"1.0","Attributes":{"Timestamp":"2025-06-30T00:00:00Z"}},
    {"Type":"ExpirationNotification","Version":"1.0","Attributes":{"Before":"15","Unit":"Days"}},
    {"Type":"NoChangeNotification","Version":"1.0","Attributes":{"After":"90","Unit":"Days"}}
  ]'
```

### Differenze e Scelta

| Caratteristica | Secrets Manager | SSM Parameter Store |
|---|---|---|
| **Rotazione automatica** | Nativa con Lambda | Non nativa |
| **Costo** | ~$0.40/secret/mese + $0.05/10K API | Gratuito (Standard), $0.05/Advanced/mese |
| **Dimensione massima** | 64 KB | 4 KB (Standard) / 8 KB (Advanced) |
| **Versioning** | Nativo (AWSCURRENT, AWSPREVIOUS) | Nativo con cronologia |
| **Cross-region replication** | Nativa | Non disponibile |
| **Integrazione RDS nativa** | Rotazione integrata | Manuale |

**Usare Secrets Manager** per: credenziali database con rotazione, secret cross-region, segreti ad alto valore.
**Usare Parameter Store** per: configurazione applicativa, parametri non sensibili, costi contenuti.

**Terraform per Secrets Manager:**
```hcl
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "prod/webapp/database"
  kms_key_id             = aws_kms_key.secrets.arn
  recovery_window_in_days = 30

  replica {
    region     = "eu-central-1"
    kms_key_id = aws_kms_key.secrets_eu.arn
  }

  tags = {
    Environment = "production"
    Application = "webapp"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = "webapp_user"
    password = random_password.db.result
    host     = aws_db_instance.main.address
    port     = 5432
  })
}

resource "aws_secretsmanager_secret_rotation" "db_rotation" {
  secret_id           = aws_secretsmanager_secret.db_credentials.id
  rotation_lambda_arn = aws_lambda_function.secret_rotation.arn

  rotation_rules {
    schedule_expression = "rate(30 days)"
    duration            = "2h"
  }
}
```

---

## 6. Azure Key Vault

### Architettura e Concetti

Azure Key Vault offre due livelli di protezione:

- **Standard** — chiavi protette dal software (FIPS 140-2 Level 1)
- **Premium / Managed HSM** — chiavi protette da HSM (FIPS 140-2 Level 3)

Tipi di oggetti gestiti:
- **Keys** — chiavi crittografiche (RSA, EC) per crittografia, firma e wrapping
- **Secrets** — stringhe opache (password, connection string, certificati)
- **Certificates** — certificati X.509 con gestione completa del ciclo di vita

```bash
# Creare un Key Vault
az keyvault create \
  --name "webapp-prod-kv" \
  --resource-group "rg-webapp-prod" \
  --location "westeurope" \
  --sku premium \
  --enable-soft-delete true \
  --soft-delete-retention-days 90 \
  --enable-purge-protection true \
  --enable-rbac-authorization true

# Creare un secret
az keyvault secret set \
  --vault-name "webapp-prod-kv" \
  --name "database-password" \
  --value "P@ssw0rd!2024" \
  --content-type "text/plain" \
  --tags "Environment=production" "Application=webapp" \
  --expires "2025-12-31T23:59:59Z"

# Recuperare un secret
az keyvault secret show \
  --vault-name "webapp-prod-kv" \
  --name "database-password" \
  --query "value" --output tsv

# Recuperare una versione specifica
az keyvault secret show \
  --vault-name "webapp-prod-kv" \
  --name "database-password" \
  --version "abcdef1234567890"

# Elencare tutte le versioni di un secret
az keyvault secret list-versions \
  --vault-name "webapp-prod-kv" \
  --name "database-password"

# Eliminare un secret (soft delete)
az keyvault secret delete \
  --vault-name "webapp-prod-kv" \
  --name "database-password"

# Ripristinare un secret eliminato
az keyvault secret recover \
  --vault-name "webapp-prod-kv" \
  --name "database-password"

# Backup di un secret
az keyvault secret backup \
  --vault-name "webapp-prod-kv" \
  --name "database-password" \
  --file "database-password.bak"

# Restore di un secret
az keyvault secret restore \
  --vault-name "webapp-prod-kv" \
  --file "database-password.bak"
```

### Access Control

```bash
# RBAC — assegnare il ruolo Key Vault Secrets User a una managed identity
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee-object-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --scope "/subscriptions/SUB_ID/resourceGroups/rg-webapp-prod/providers/Microsoft.KeyVault/vaults/webapp-prod-kv"

# Ruoli disponibili:
# - Key Vault Administrator — gestione completa
# - Key Vault Secrets Officer — CRUD su secrets
# - Key Vault Secrets User — solo lettura secrets
# - Key Vault Certificates Officer — CRUD su certificati
# - Key Vault Crypto Officer — operazioni crittografiche e gestione chiavi
# - Key Vault Crypto User — solo operazioni crittografiche
# - Key Vault Reader — lettura metadata (non valori)

# Access Policy (alternativa legacy a RBAC)
az keyvault set-policy \
  --name "webapp-prod-kv" \
  --object-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --secret-permissions get list \
  --key-permissions get list unwrapKey wrapKey \
  --certificate-permissions get list
```

### Key Management e Rotation

```bash
# Creare una chiave RSA
az keyvault key create \
  --vault-name "webapp-prod-kv" \
  --name "data-encryption-key" \
  --kty RSA \
  --size 4096 \
  --ops encrypt decrypt sign verify wrapKey unwrapKey

# Creare una chiave EC
az keyvault key create \
  --vault-name "webapp-prod-kv" \
  --name "signing-key" \
  --kty EC \
  --curve P-256

# Configurare la rotazione automatica delle chiavi
az keyvault key rotation-policy update \
  --vault-name "webapp-prod-kv" \
  --name "data-encryption-key" \
  --value '{
    "lifetimeActions": [
      {
        "trigger": {"timeBeforeExpiry": "P30D"},
        "action": {"type": "Notify"}
      },
      {
        "trigger": {"timeAfterCreate": "P90D"},
        "action": {"type": "Rotate"}
      }
    ],
    "attributes": {"expiryTime": "P1Y"}
  }'

# Ruotare manualmente una chiave
az keyvault key rotate \
  --vault-name "webapp-prod-kv" \
  --name "data-encryption-key"
```

### Certificate Management

```bash
# Creare un certificato self-signed
az keyvault certificate create \
  --vault-name "webapp-prod-kv" \
  --name "webapp-tls" \
  --policy '{
    "issuerParameters": {"name": "Self"},
    "keyProperties": {"exportable": true, "keyType": "EC", "curve": "P-256"},
    "secretProperties": {"contentType": "application/x-pkcs12"},
    "x509CertificateProperties": {
      "subject": "CN=webapp.example.com",
      "subjectAlternativeNames": {
        "dnsNames": ["webapp.example.com", "api.example.com"]
      },
      "validityInMonths": 12
    },
    "lifetimeActions": [
      {
        "trigger": {"daysBeforeExpiry": 30},
        "action": {"actionType": "AutoRenew"}
      }
    ]
  }'

# Importare un certificato esistente
az keyvault certificate import \
  --vault-name "webapp-prod-kv" \
  --name "imported-cert" \
  --file "certificate.pfx" \
  --password "pfx-password"
```

### Networking e Private Endpoints

```bash
# Configurare il firewall del Key Vault
az keyvault update \
  --name "webapp-prod-kv" \
  --default-action Deny \
  --bypass AzureServices

# Aggiungere un IP consentito
az keyvault network-rule add \
  --name "webapp-prod-kv" \
  --ip-address "203.0.113.0/24"

# Creare un private endpoint
az network private-endpoint create \
  --name "kv-private-endpoint" \
  --resource-group "rg-webapp-prod" \
  --vnet-name "vnet-prod" \
  --subnet "subnet-private-endpoints" \
  --private-connection-resource-id "/subscriptions/SUB_ID/resourceGroups/rg-webapp-prod/providers/Microsoft.KeyVault/vaults/webapp-prod-kv" \
  --group-id vault \
  --connection-name "kv-connection"
```

**Terraform per Azure Key Vault:**
```hcl
resource "azurerm_key_vault" "webapp" {
  name                       = "webapp-prod-kv"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "premium"
  soft_delete_retention_days = 90
  purge_protection_enabled   = true
  enable_rbac_authorization  = true

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
    ip_rules       = ["203.0.113.0/24"]

    virtual_network_subnet_ids = [
      azurerm_subnet.app.id
    ]
  }
}

resource "azurerm_key_vault_secret" "db_password" {
  name         = "database-password"
  value        = random_password.db.result
  key_vault_id = azurerm_key_vault.webapp.id
  content_type = "text/plain"
  expiration_date = "2025-12-31T23:59:59Z"

  tags = {
    Environment = "production"
  }
}

resource "azurerm_role_assignment" "webapp_secrets_user" {
  scope                = azurerm_key_vault.webapp.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.webapp.principal_id
}
```

---

## 7. GCP Secret Manager

### Architettura e Concetti

GCP Secret Manager memorizza i secret come risorse di primo livello in Google Cloud,
con versioning automatico, replication configurabile e integrazione IAM nativa.

I secret sono crittografati automaticamente con Google-managed encryption key
oppure con Customer-Managed Encryption Key (CMEK) tramite Cloud KMS.

```bash
# Abilitare l'API
gcloud services enable secretmanager.googleapis.com

# Creare un secret
gcloud secrets create webapp-database-password \
  --replication-policy="automatic" \
  --labels="env=production,app=webapp"

# Aggiungere una versione (il valore effettivo)
echo -n "P@ssw0rd!2024" | gcloud secrets versions add webapp-database-password \
  --data-file=-

# Creare un secret con replication user-managed
gcloud secrets create webapp-api-key \
  --replication-policy="user-managed" \
  --locations="europe-west1,europe-west4" \
  --kms-key-name="projects/my-project/locations/europe-west1/keyRings/secrets/cryptoKeys/secret-key"

# Accedere alla versione corrente
gcloud secrets versions access latest \
  --secret="webapp-database-password"

# Accedere a una versione specifica
gcloud secrets versions access 2 \
  --secret="webapp-database-password"

# Elencare tutte le versioni
gcloud secrets versions list webapp-database-password

# Disabilitare una versione (non piu accessibile ma non eliminata)
gcloud secrets versions disable 1 \
  --secret="webapp-database-password"

# Abilitare una versione disabilitata
gcloud secrets versions enable 1 \
  --secret="webapp-database-password"

# Eliminare una versione (irreversibile)
gcloud secrets versions destroy 1 \
  --secret="webapp-database-password"

# Elencare tutti i secret del progetto
gcloud secrets list --filter="labels.env=production"

# Eliminare un secret (tutte le versioni)
gcloud secrets delete webapp-database-password
```

### IAM per Accesso ai Secret

```bash
# Concedere accesso in lettura a un service account
gcloud secrets add-iam-policy-binding webapp-database-password \
  --member="serviceAccount:webapp@my-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Concedere accesso admin
gcloud secrets add-iam-policy-binding webapp-database-password \
  --member="user:admin@example.com" \
  --role="roles/secretmanager.admin"

# Ruoli disponibili:
# - roles/secretmanager.secretAccessor — accesso ai valori dei secret
# - roles/secretmanager.secretVersionAdder — aggiungere nuove versioni
# - roles/secretmanager.secretVersionManager — gestire versioni (disable, enable, destroy)
# - roles/secretmanager.admin — gestione completa
# - roles/secretmanager.viewer — visualizzare metadata (non i valori)

# Condizioni IAM (accesso solo in orario lavorativo)
gcloud secrets add-iam-policy-binding webapp-database-password \
  --member="serviceAccount:webapp@my-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --condition='expression=request.time.getHours("Europe/Rome") >= 8 && request.time.getHours("Europe/Rome") <= 18,title=orario-lavorativo'
```

### Rotazione con Pub/Sub e Cloud Functions

```bash
# Creare un topic Pub/Sub per le notifiche di rotazione
gcloud pubsub topics create secret-rotation-topic

# Configurare la rotazione periodica
gcloud secrets update webapp-database-password \
  --next-rotation-time="2025-04-01T00:00:00Z" \
  --rotation-period="2592000s" \
  --topics="projects/my-project/topics/secret-rotation-topic"
```

**Cloud Function per la rotazione (Python):**
```python
import functions_framework
from google.cloud import secretmanager
import secrets
import string

@functions_framework.cloud_event
def rotate_secret(cloud_event):
    """Triggered da un messaggio Pub/Sub per ruotare il secret."""
    import base64
    import json

    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    event = json.loads(message_data)

    secret_name = event.get("name")
    event_type = event.get("eventType")

    if event_type != "SECRET_ROTATE":
        return

    client = secretmanager.SecretManagerServiceClient()

    # Generare una nuova password
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    new_password = ''.join(secrets.choice(alphabet) for _ in range(40))

    # Aggiungere la nuova versione
    client.add_secret_version(
        request={
            "parent": secret_name,
            "payload": {"data": new_password.encode("UTF-8")}
        }
    )

    # Aggiornare la password nel database target
    # update_database_password(new_password)

    print(f"Secret {secret_name} ruotato con successo")
```

### Integrazione con GKE (Workload Identity)

```bash
# Configurare Workload Identity per accedere ai secret
gcloud iam service-accounts create webapp-sa \
  --display-name="Webapp Service Account"

gcloud secrets add-iam-policy-binding webapp-database-password \
  --member="serviceAccount:webapp-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Associare il KSA al GSA
gcloud iam service-accounts add-iam-policy-binding \
  webapp-sa@my-project.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:my-project.svc.id.goog[production/webapp-ksa]"
```

```yaml
# kubernetes-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: webapp-ksa
  namespace: production
  annotations:
    iam.gke.io/gcp-service-account: webapp-sa@my-project.iam.gserviceaccount.com
```

**Terraform per GCP Secret Manager:**
```hcl
resource "google_secret_manager_secret" "db_password" {
  secret_id = "webapp-database-password"

  labels = {
    env = "production"
    app = "webapp"
  }

  replication {
    user_managed {
      replicas {
        location = "europe-west1"
        customer_managed_encryption {
          kms_key_name = google_kms_crypto_key.secret_key.id
        }
      }
      replicas {
        location = "europe-west4"
        customer_managed_encryption {
          kms_key_name = google_kms_crypto_key.secret_key_dr.id
        }
      }
    }
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db.result
}

resource "google_secret_manager_secret_iam_member" "webapp_accessor" {
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.webapp.email}"
}

# Configurare la rotazione
resource "google_secret_manager_secret" "rotating_secret" {
  secret_id = "webapp-api-key"

  replication {
    auto {}
  }

  rotation {
    next_rotation_time = "2025-04-01T00:00:00Z"
    rotation_period    = "2592000s"
  }

  topics {
    name = google_pubsub_topic.secret_rotation.id
  }
}
```

---

## 8. SOPS (Secrets OPerationS)

### Panoramica

SOPS (sviluppato originariamente da Mozilla) e uno strumento per la crittografia di file
di configurazione. A differenza di altri strumenti, SOPS crittografa solo i **valori**,
lasciando le chiavi e la struttura del file in chiaro, facilitando la revisione in Git.

### Installazione e Configurazione

```bash
# Installazione
SOPS_VERSION="3.9.0"
wget "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64"
chmod +x "sops-v${SOPS_VERSION}.linux.amd64"
sudo mv "sops-v${SOPS_VERSION}.linux.amd64" /usr/local/bin/sops

sops --version
```

**Configurazione `.sops.yaml` nella root del repository:**
```yaml
# .sops.yaml
creation_rules:
  # Secret di produzione — crittografati con AWS KMS + age come backup
  - path_regex: environments/production/.*\.yaml$
    kms: "arn:aws:kms:eu-west-1:123456789:key/abcd-1234-efgh-5678"
    age: "age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    encrypted_regex: "^(password|secret|token|api_key|private_key|connection_string)$"

  # Secret di staging — solo age
  - path_regex: environments/staging/.*\.yaml$
    age: "age1yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
    encrypted_regex: "^(password|secret|token|api_key)$"

  # Secret GCP — crittografati con GCP KMS
  - path_regex: gcp/.*\.json$
    gcp_kms: "projects/my-project/locations/global/keyRings/sops/cryptoKeys/sops-key"

  # Secret Azure — crittografati con Azure Key Vault
  - path_regex: azure/.*\.yaml$
    azure_keyvault: "https://sops-keyvault.vault.azure.net/keys/sops-key/abcdef1234"

  # Default — PGP per sviluppo locale
  - path_regex: .*\.env$
    pgp: "FBC7B9E2A4F9289AC0C1D4843D16CEE4A27381B4"
```

### Operazioni con SOPS

```bash
# Crittografare un file YAML
sops --encrypt secrets.yaml > secrets.enc.yaml

# Crittografare in-place
sops --encrypt --in-place secrets.yaml

# Decrittografare e visualizzare
sops --decrypt secrets.enc.yaml

# Decrittografare in-place
sops --decrypt --in-place secrets.enc.yaml

# Modificare un file crittografato (apre l'editor, salva crittografato)
sops secrets.enc.yaml

# Crittografare con una chiave age specifica
sops --encrypt --age "age1xxxxxxx..." secrets.yaml > secrets.enc.yaml

# Crittografare con AWS KMS
sops --encrypt --kms "arn:aws:kms:..." secrets.yaml > secrets.enc.yaml

# Crittografare solo valori specifici (regex)
sops --encrypt --encrypted-regex "^(password|token)$" config.yaml > config.enc.yaml

# Ruotare le chiavi di crittografia (re-encrypt con nuove chiavi)
sops --rotate --in-place secrets.enc.yaml

# Estrarre un singolo valore
sops --decrypt --extract '["database"]["password"]' secrets.enc.yaml
```

**Esempio di file crittografato con SOPS:**
```yaml
# Le chiavi restano in chiaro, i valori sono crittografati
database:
    host: db.prod.internal           # non crittografato (non matcha il regex)
    port: 5432                       # non crittografato
    username: webapp_user            # non crittografato
    password: ENC[AES256_GCM,data:aBcDeFg==,iv:...,tag:...,type:str]
api:
    endpoint: https://api.example.com
    api_key: ENC[AES256_GCM,data:xYzAbCd==,iv:...,tag:...,type:str]
    token: ENC[AES256_GCM,data:mNoPqRs==,iv:...,tag:...,type:str]
sops:
    kms:
        - arn: arn:aws:kms:eu-west-1:123456789:key/abcd-1234
          created_at: "2024-01-15T10:30:00Z"
          enc: AQICAHh...
    age:
        - recipient: age1xxxxxxx...
          enc: |
            -----BEGIN AGE ENCRYPTED FILE-----
            ...
            -----END AGE ENCRYPTED FILE-----
    lastmodified: "2024-01-15T10:30:00Z"
    mac: ENC[AES256_GCM,data:...,tag:...,type:str]
    version: 3.9.0
```

### Integrazione con Terraform

```hcl
# Usare il provider sops per leggere file crittografati
terraform {
  required_providers {
    sops = {
      source  = "carlpett/sops"
      version = "~> 1.0"
    }
  }
}

data "sops_file" "secrets" {
  source_file = "${path.module}/secrets.enc.yaml"
}

resource "aws_db_instance" "main" {
  engine         = "postgres"
  engine_version = "16.1"
  instance_class = "db.r6g.large"
  username       = data.sops_file.secrets.data["database.username"]
  password       = data.sops_file.secrets.data["database.password"]
}
```

### Integrazione con Helm (helm-secrets)

```bash
# Installare il plugin helm-secrets
helm plugin install https://github.com/jkroepke/helm-secrets

# Struttura directory
# charts/webapp/
# ├── Chart.yaml
# ├── values.yaml                    # valori non sensibili
# ├── secrets.yaml                   # valori sensibili (crittografato con SOPS)
# └── templates/

# Crittografare i valori sensibili
sops --encrypt --in-place charts/webapp/secrets.yaml

# Deploy con helm-secrets (decrittografa automaticamente)
helm secrets upgrade webapp charts/webapp/ \
  -f charts/webapp/values.yaml \
  -f charts/webapp/secrets.yaml \
  --namespace production

# Il file secrets.yaml in chiaro contiene:
# database:
#   password: "P@ssw0rd!2024"
# api:
#   token: "tk_live_xxxxxxxxx"
```

### Integrazione con ArgoCD

```yaml
# argocd-repo-server con SOPS
apiVersion: apps/v1
kind: Deployment
metadata:
  name: argocd-repo-server
spec:
  template:
    spec:
      containers:
        - name: argocd-repo-server
          env:
            - name: HELM_PLUGINS
              value: /custom-tools/helm-plugins
            - name: HELM_SECRETS_SOPS_PATH
              value: /custom-tools/sops
            - name: HELM_SECRETS_BACKEND
              value: sops
          volumeMounts:
            - name: custom-tools
              mountPath: /custom-tools
            - name: sops-age-key
              mountPath: /home/argocd/.config/sops/age
      initContainers:
        - name: install-tools
          image: alpine:3.19
          command: ["/bin/sh", "-c"]
          args:
            - |
              wget -qO /custom-tools/sops https://github.com/getsops/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64
              chmod +x /custom-tools/sops
              helm plugin install https://github.com/jkroepke/helm-secrets --version v4.6.0
              cp -r /root/.local/share/helm/plugins /custom-tools/helm-plugins
          volumeMounts:
            - name: custom-tools
              mountPath: /custom-tools
      volumes:
        - name: custom-tools
          emptyDir: {}
        - name: sops-age-key
          secret:
            secretName: sops-age-key-secret
```

---

## 9. cert-manager e Gestione Certificati

### Architettura

cert-manager e un controller Kubernetes che automatizza l'emissione e il rinnovo
dei certificati TLS. Opera come un operatore che monitora le risorse Certificate
e interagisce con i provider di certificati (Let's Encrypt, Vault, CA interne).

```bash
# Installazione con Helm
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.16.1 \
  --set crds.enabled=true \
  --set prometheus.enabled=true \
  --set webhook.timeoutSeconds=30
```

### Issuers e ClusterIssuers

```yaml
# ClusterIssuer per Let's Encrypt (produzione)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: certs@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      # HTTP-01 challenge per domini pubblici
      - http01:
          ingress:
            class: nginx
            podTemplate:
              spec:
                nodeSelector:
                  kubernetes.io/os: linux
        selector:
          dnsZones:
            - "example.com"
      # DNS-01 challenge per wildcard e domini interni
      - dns01:
          cloudDNS:
            project: my-gcp-project
            serviceAccountSecretRef:
              name: clouddns-sa-key
              key: key.json
        selector:
          dnsZones:
            - "internal.example.com"
---
# ClusterIssuer per Let's Encrypt (staging — per test)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: certs@example.com
    privateKeySecretRef:
      name: letsencrypt-staging-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
---
# ClusterIssuer per HashiCorp Vault PKI
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: vault-issuer
spec:
  vault:
    path: pki_int/sign/webapp
    server: https://vault.example.com:8200
    caBundle: <base64-encoded-ca-cert>
    auth:
      kubernetes:
        role: cert-manager
        mountPath: /v1/auth/kubernetes
        serviceAccountRef:
          name: cert-manager
---
# Issuer per CA interna (self-signed root)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-root
spec:
  selfSigned: {}
---
# Certificato root CA
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: internal-root-ca
  namespace: cert-manager
spec:
  isCA: true
  commonName: "Internal Root CA"
  duration: 87600h    # 10 anni
  renewBefore: 8760h  # rinnova 1 anno prima della scadenza
  secretName: internal-root-ca-secret
  privateKey:
    algorithm: ECDSA
    size: 384
  issuerRef:
    name: selfsigned-root
    kind: ClusterIssuer
---
# ClusterIssuer con la CA interna
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: internal-ca
spec:
  ca:
    secretName: internal-root-ca-secret
---
# Issuer per DNS-01 con Route53
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-route53
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: certs@example.com
    privateKeySecretRef:
      name: letsencrypt-route53-key
    solvers:
      - dns01:
          route53:
            region: eu-west-1
            hostedZoneID: Z1234567890ABC
            role: arn:aws:iam::123456789:role/cert-manager-route53
```

### Certificate Resource

```yaml
# Certificato per un servizio web
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: webapp-tls
  namespace: production
spec:
  secretName: webapp-tls-secret
  duration: 2160h      # 90 giorni
  renewBefore: 720h    # rinnova 30 giorni prima della scadenza
  isCA: false
  privateKey:
    algorithm: ECDSA
    size: 256
    rotationPolicy: Always
  usages:
    - server auth
    - client auth
  dnsNames:
    - webapp.example.com
    - api.example.com
    - "*.staging.example.com"
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
    group: cert-manager.io
  secretTemplate:
    annotations:
      reloader.stakater.com/match: "true"
    labels:
      app: webapp
---
# Certificato wildcard (richiede DNS-01 challenge)
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard-tls
  namespace: production
spec:
  secretName: wildcard-tls-secret
  duration: 2160h
  renewBefore: 720h
  privateKey:
    algorithm: RSA
    size: 4096
  dnsNames:
    - "*.example.com"
    - "example.com"
  issuerRef:
    name: letsencrypt-route53
    kind: ClusterIssuer
---
# Certificato per mTLS tra servizi
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: service-mtls
  namespace: production
spec:
  secretName: service-mtls-secret
  duration: 720h     # 30 giorni
  renewBefore: 240h  # rinnova 10 giorni prima
  commonName: "webapp.production.svc.cluster.local"
  privateKey:
    algorithm: ECDSA
    size: 256
  usages:
    - server auth
    - client auth
  dnsNames:
    - "webapp.production.svc.cluster.local"
    - "webapp.production.svc"
  uris:
    - "spiffe://cluster.local/ns/production/sa/webapp"
  issuerRef:
    name: internal-ca
    kind: ClusterIssuer
```

### trust-manager per CA Bundles

```yaml
# Installazione trust-manager
# helm install trust-manager jetstack/trust-manager --namespace cert-manager

# Bundle che combina CA pubbliche e interne
apiVersion: trust.cert-manager.io/v1alpha1
kind: Bundle
metadata:
  name: trusted-cas
spec:
  sources:
    # CA bundle di sistema
    - useDefaultCAs: true
    # CA interna dal cert-manager
    - secret:
        name: internal-root-ca-secret
        key: ca.crt
    # CA personalizzata da ConfigMap
    - configMap:
        name: custom-ca-bundle
        key: ca-certificates.crt
  target:
    configMap:
      key: ca-certificates.crt
    namespaceSelector:
      matchLabels:
        trust-bundle: "enabled"
```

### Monitoring con Prometheus

```yaml
# PrometheusRule per cert-manager
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cert-manager-alerts
  namespace: cert-manager
spec:
  groups:
    - name: cert-manager
      rules:
        - alert: CertificateExpiringSoon
          expr: |
            certmanager_certificate_expiration_timestamp_seconds - time() < 7 * 24 * 3600
          for: 1h
          labels:
            severity: warning
          annotations:
            summary: "Il certificato {{ $labels.name }} scade tra meno di 7 giorni"
            description: "Namespace: {{ $labels.namespace }}, Secret: {{ $labels.name }}"

        - alert: CertificateNotReady
          expr: |
            certmanager_certificate_ready_status{condition="False"} == 1
          for: 15m
          labels:
            severity: critical
          annotations:
            summary: "Il certificato {{ $labels.name }} non e nello stato Ready"

        - alert: CertificateRenewalFailure
          expr: |
            increase(certmanager_certificate_renewal_errors_total[1h]) > 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Errore nel rinnovo del certificato {{ $labels.name }}"
```

---

## 10. Secret Rotation e Lifecycle

### Strategie di Rotazione

La rotazione dei secret e fondamentale per limitare l'impatto di una compromissione.
Esistono tre strategie principali:

| Strategia | Descrizione | Caso d'Uso |
|---|---|---|
| **Manual** | Rotazione su richiesta da parte di un operatore | Secret a basso rischio, ambienti non critici |
| **Scheduled** | Rotazione periodica automatica (30/60/90 giorni) | Credenziali database, API key |
| **Event-driven** | Rotazione immediata in risposta a un evento di sicurezza | Compromissione sospetta, dimissioni dipendente |

### Rotazione Senza Downtime — Dual-Credential Pattern

Il dual-credential pattern consente la rotazione senza interruzione del servizio:

```
Stato Iniziale:
┌─────────────┐         ┌─────────────┐
│  Applicazione│────────>│  Database    │
│  usa cred A  │         │  accetta A   │
└─────────────┘         └─────────────┘

Fase 1 — Creare nuova credenziale:
┌─────────────┐         ┌─────────────┐
│  Applicazione│────────>│  Database    │
│  usa cred A  │         │  accetta A+B │
└─────────────┘         └─────────────┘

Fase 2 — Aggiornare l'applicazione:
┌─────────────┐         ┌─────────────┐
│  Applicazione│────────>│  Database    │
│  usa cred B  │         │  accetta A+B │
└─────────────┘         └─────────────┘

Fase 3 — Revocare la vecchia credenziale:
┌─────────────┐         ┌─────────────┐
│  Applicazione│────────>│  Database    │
│  usa cred B  │         │  accetta B   │
└─────────────┘         └─────────────┘
```

**Script di rotazione graceful per PostgreSQL:**
```bash
#!/usr/bin/env bash
set -euo pipefail

# Variabili
SECRET_ID="prod/webapp/database"
DB_HOST="db.prod.internal"
DB_NAME="webapp"
ADMIN_USER="rotation_admin"

# 1. Generare una nuova password
NEW_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)

# 2. Recuperare le credenziali correnti
CURRENT_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id "${SECRET_ID}" \
  --query 'SecretString' --output text)
CURRENT_USER=$(echo "${CURRENT_SECRET}" | jq -r '.username')
CURRENT_PASS=$(echo "${CURRENT_SECRET}" | jq -r '.password')

# 3. Creare la nuova credenziale nel database (fase 1)
PGPASSWORD="${ADMIN_PASS}" psql -h "${DB_HOST}" -U "${ADMIN_USER}" -d "${DB_NAME}" <<SQL
DO \$\$
BEGIN
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = '${CURRENT_USER}_new') THEN
    DROP ROLE "${CURRENT_USER}_new";
  END IF;
  CREATE ROLE "${CURRENT_USER}_new" WITH LOGIN PASSWORD '${NEW_PASSWORD}';
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "${CURRENT_USER}_new";
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "${CURRENT_USER}_new";
END
\$\$;
SQL

# 4. Aggiornare il secret nel vault (fase 2)
aws secretsmanager update-secret \
  --secret-id "${SECRET_ID}" \
  --secret-string "{\"username\":\"${CURRENT_USER}_new\",\"password\":\"${NEW_PASSWORD}\",\"host\":\"${DB_HOST}\"}"

# 5. Attendere che le applicazioni ricarichino le credenziali
echo "Attendere 60 secondi per la propagazione..."
sleep 60

# 6. Revocare la vecchia credenziale (fase 3)
PGPASSWORD="${ADMIN_PASS}" psql -h "${DB_HOST}" -U "${ADMIN_USER}" -d "${DB_NAME}" <<SQL
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM "${CURRENT_USER}";
DROP ROLE IF EXISTS "${CURRENT_USER}";
SQL

echo "Rotazione completata con successo"
```

### Rotazione Chiavi di Crittografia — Envelope Encryption

L'envelope encryption utilizza una gerarchia di chiavi per limitare l'impatto della rotazione:

```
┌─────────────────────────────────────────────────────┐
│                    Master Key (KEK)                  │
│  Memorizzata nel KMS (AWS KMS, Vault Transit, etc.) │
│  Ruotata raramente — richiede re-wrapping dei DEK    │
└─────────────┬───────────────────────┬───────────────┘
              │                       │
     ┌────────▼────────┐    ┌────────▼────────┐
     │   Data Key 1    │    │   Data Key 2    │
     │   (DEK)         │    │   (DEK)         │
     │ Crittografa i   │    │ Crittografa i   │
     │ dati del set A  │    │ dati del set B  │
     └────────┬────────┘    └────────┬────────┘
              │                       │
     ┌────────▼────────┐    ┌────────▼────────┐
     │  Dati cifrati A │    │  Dati cifrati B │
     └─────────────────┘    └─────────────────┘
```

**Rotazione con Vault Transit (re-wrapping senza esporre il plaintext):**
```bash
# 1. Ruotare la master key
vault write -f transit/keys/data-encryption/rotate

# 2. Re-wrappare tutti i data key crittografati
# Il vecchio ciphertext (v1) viene ricrittografato con la nuova chiave (v2)
# senza MAI esporre il plaintext
vault write transit/rewrap/data-encryption \
  ciphertext="vault:v1:aBcDeFgHiJkLmNoPqRsTuVwXyZ..."

# Output: ciphertext = vault:v2:xYzAbCdEfGhIjKlMnOpQrStUv...

# 3. Impostare la versione minima di decrittazione
# Dopo aver re-wrappato tutti i dati, impedire l'uso delle vecchie chiavi
vault write transit/keys/data-encryption/config \
  min_decryption_version=2 \
  min_encryption_version=2
```

### Emergency Rotation Runbook

Procedura in caso di compromissione sospetta di un secret:

```
RUNBOOK — ROTAZIONE D'EMERGENZA

Livello di Severita: CRITICO
Tempo massimo di risposta: 15 minuti

FASE 1 — TRIAGE (0-5 minuti)
[ ] Identificare quale secret e stato compromesso
[ ] Determinare l'ambito della compromissione (quali sistemi usano il secret)
[ ] Notificare il team di sicurezza e il responsabile on-call
[ ] Aprire un incident nel sistema di tracking

FASE 2 — CONTENIMENTO (5-10 minuti)
[ ] Revocare immediatamente il secret compromesso nel vault
[ ] Se possibile, bloccare l'accesso dall'IP sospetto
[ ] Generare un nuovo secret con entropia massima
[ ] Aggiornare il secret nel vault/KMS

FASE 3 — RIPRISTINO (10-15 minuti)
[ ] Distribuire il nuovo secret a tutti i consumer
[ ] Verificare che tutti i servizi funzionino con il nuovo secret
[ ] Controllare i log di audit per accessi non autorizzati
[ ] Documentare la timeline dell'incidente

FASE 4 — POST-INCIDENT (entro 24 ore)
[ ] Analisi forense completa dei log di accesso
[ ] Identificare la root cause della compromissione
[ ] Implementare misure preventive
[ ] Aggiornare le procedure di sicurezza
[ ] Condurre il post-mortem
```

---

## 11. Kubernetes Secrets

### Native Secrets

Kubernetes offre diverse tipologie di Secret nativi:

```yaml
# Opaque Secret (generico)
apiVersion: v1
kind: Secret
metadata:
  name: webapp-credentials
  namespace: production
  labels:
    app: webapp
type: Opaque
data:
  # I valori sono codificati in base64 — NON crittografati!
  username: d2ViYXBwX3VzZXI=           # echo -n "webapp_user" | base64
  password: UEBzc3cwcmQhMjAyNA==       # echo -n "P@ssw0rd!2024" | base64
---
# TLS Secret
apiVersion: v1
kind: Secret
metadata:
  name: webapp-tls
  namespace: production
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTi...         # certificato in base64
  tls.key: LS0tLS1CRUdJTi...         # chiave privata in base64
---
# Docker Registry Secret
apiVersion: v1
kind: Secret
metadata:
  name: registry-credentials
  namespace: production
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: eyJhdXRocyI6...   # docker config in base64
---
# Creazione da CLI
kubectl create secret generic webapp-credentials \
  --namespace production \
  --from-literal=username=webapp_user \
  --from-literal=password='P@ssw0rd!2024'

kubectl create secret tls webapp-tls \
  --namespace production \
  --cert=tls.crt \
  --key=tls.key

kubectl create secret docker-registry registry-creds \
  --namespace production \
  --docker-server=registry.example.com \
  --docker-username=deploy \
  --docker-password=token123
```

**Utilizzo dei Secret nei Pod:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
        - name: webapp
          image: webapp:1.5.0
          # Montare come variabili d'ambiente
          env:
            - name: DB_USERNAME
              valueFrom:
                secretKeyRef:
                  name: webapp-credentials
                  key: username
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: webapp-credentials
                  key: password
          # Montare come file
          volumeMounts:
            - name: tls-certs
              mountPath: /etc/tls
              readOnly: true
            - name: app-secrets
              mountPath: /etc/secrets
              readOnly: true
      volumes:
        - name: tls-certs
          secret:
            secretName: webapp-tls
            defaultMode: 0400
        - name: app-secrets
          secret:
            secretName: webapp-credentials
            defaultMode: 0400
            items:
              - key: password
                path: db-password
```

### Limitazioni dei Kubernetes Secrets Nativi

I Kubernetes Secret nativi hanno limitazioni significative:

1. **base64 non e crittografia** — la codifica base64 e reversibile da chiunque abbia accesso
2. **Memorizzati in chiaro in etcd** — senza configurazione aggiuntiva, etcd memorizza i secret in plaintext
3. **Accesso RBAC insufficiente** — il default RBAC puo essere troppo permissivo
4. **Nessuna rotazione automatica** — la rotazione richiede intervento manuale o strumenti esterni
5. **Nessun audit granulare** — i log standard non tracciano chi accede ai secret

### Encryption at Rest con EncryptionConfiguration

```yaml
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps
    providers:
      # Provider preferito per la scrittura (primo della lista)
      - aescbc:
          keys:
            - name: key-2024-q1
              secret: <base64-encoded-32-byte-key>
      # KMS provider per integrazione con KMS esterno
      # - kms:
      #     apiVersion: v2
      #     name: aws-kms
      #     endpoint: unix:///var/run/kms-plugin/socket.sock
      #     cachesize: 1000
      #     timeout: 3s
      # Fallback per leggere secret non ancora crittografati
      - identity: {}
```

```bash
# Applicare la configurazione all'API server
# Aggiungere al manifest dell'API server:
# --encryption-provider-config=/etc/kubernetes/encryption-config.yaml

# Verificare che la crittografia sia attiva
kubectl get secrets -A -o json | kubectl replace -f -
# Questo forza la ri-scrittura di tutti i secret con il nuovo provider

# Verificare la crittografia leggendo direttamente da etcd
ETCDCTL_API=3 etcdctl get /registry/secrets/production/webapp-credentials \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key | hexdump -C | head
# Se crittografato, il payload inizia con "k8s:enc:aescbc:v1:key-2024-q1"
```

### External Secrets Operator (ESO)

L'External Secrets Operator sincronizza i secret da provider esterni in Kubernetes Secret:

```bash
# Installazione
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace \
  --set installCRDs=true
```

```yaml
# SecretStore per AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: eu-west-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets
---
# SecretStore per HashiCorp Vault
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.example.com:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets
---
# SecretStore per GCP Secret Manager
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: gcp-secret-manager
spec:
  provider:
    gcpsm:
      projectID: my-project
      auth:
        workloadIdentity:
          clusterLocation: europe-west1
          clusterName: production-cluster
          clusterProjectID: my-project
          serviceAccountRef:
            name: external-secrets-gcp-sa
            namespace: external-secrets
---
# ExternalSecret — sincronizzare un secret da AWS
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: webapp-db-credentials
  namespace: production
spec:
  refreshInterval: 1m
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: webapp-db-secret
    creationPolicy: Owner
    deletionPolicy: Retain
    template:
      type: Opaque
      data:
        DATABASE_URL: "postgresql://{{ .username }}:{{ .password }}@{{ .host }}:{{ .port }}/webapp"
  data:
    - secretKey: username
      remoteRef:
        key: prod/webapp/database
        property: username
    - secretKey: password
      remoteRef:
        key: prod/webapp/database
        property: password
    - secretKey: host
      remoteRef:
        key: prod/webapp/database
        property: host
    - secretKey: port
      remoteRef:
        key: prod/webapp/database
        property: port
---
# ExternalSecret — sincronizzare da Vault
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: webapp-config
  namespace: production
spec:
  refreshInterval: 5m
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: webapp-config-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: webapp/config
```

### Sealed Secrets (Bitnami)

Sealed Secrets permette di committare i secret crittografati nel repository Git:

```bash
# Installazione del controller
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system

# Installazione del client kubeseal
KUBESEAL_VERSION="0.27.1"
wget "https://github.com/bitnami-labs/sealed-secrets/releases/download/v${KUBESEAL_VERSION}/kubeseal-${KUBESEAL_VERSION}-linux-amd64.tar.gz"
tar -xzf "kubeseal-${KUBESEAL_VERSION}-linux-amd64.tar.gz"
sudo mv kubeseal /usr/local/bin/

# Creare un SealedSecret da un Secret standard
kubectl create secret generic webapp-credentials \
  --namespace production \
  --from-literal=password='P@ssw0rd!2024' \
  --dry-run=client -o yaml | \
  kubeseal \
    --controller-name=sealed-secrets \
    --controller-namespace=kube-system \
    --format yaml > sealed-webapp-credentials.yaml

# Il file risultante puo essere committato in Git in sicurezza
```

```yaml
# sealed-webapp-credentials.yaml (sicuro per Git)
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: webapp-credentials
  namespace: production
spec:
  encryptedData:
    password: AgBy3i4OJSWK+PIf...  # crittografato con la chiave pubblica del controller
  template:
    metadata:
      name: webapp-credentials
      namespace: production
    type: Opaque
```

---

## 12. Best Practices

### Mai Secrets nel Codice o in Git

La regola fondamentale del secrets management: **nessun secret deve mai trovarsi nel codice sorgente
o nella cronologia Git**. Anche un secret rimosso in un commit successivo resta accessibile
tramite `git log` e `git show`.

**.gitignore obbligatorio:**
```gitignore
# Variabili d'ambiente
.env
.env.*
!.env.example

# Chiavi private
*.pem
*.key
*.p12
*.pfx
*.jks

# Credenziali cloud
credentials.json
service-account-key.json
*-sa-key.json

# Terraform state (contiene secret in chiaro)
*.tfstate
*.tfstate.backup
.terraform/

# Configurazioni locali con secret
config.local.yaml
config.local.json
secrets.yaml
secrets.json
!secrets.enc.yaml
!secrets.enc.json

# Editor
.idea/
.vscode/settings.json
```

### Pre-commit Hooks per la Prevenzione

```yaml
# .pre-commit-config.yaml
repos:
  # detect-secrets — rileva pattern di secret nel codice
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: '(\.lock|\.sum|go\.mod)$'

  # gitleaks — scanner avanzato per secret
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks

  # git-secrets — pattern matching per AWS keys
  - repo: https://github.com/awslabs/git-secrets
    rev: master
    hooks:
      - id: git-secrets
```

```bash
# Installare e configurare pre-commit
pip install pre-commit
pre-commit install

# Inizializzare il baseline per detect-secrets
detect-secrets scan --baseline .secrets.baseline

# Configurare git-secrets per pattern AWS
git secrets --register-aws
git secrets --install

# Configurare gitleaks
cat > .gitleaks.toml << 'EOF'
title = "Gitleaks Configuration"

[extend]
useDefault = true

[[rules]]
id = "custom-api-key"
description = "Custom API Key pattern"
regex = '''(?i)(api[_-]?key|apikey)\s*[:=]\s*['"]?([a-zA-Z0-9_\-]{20,})['"]?'''
tags = ["api", "key"]

[[rules]]
id = "connection-string"
description = "Database connection string"
regex = '''(?i)(postgres|mysql|mongodb|redis):\/\/[^:]+:[^@]+@[^\/]+'''
tags = ["database", "connection"]

[allowlist]
description = "Allowlist"
paths = [
  '''\.secrets\.baseline$''',
  '''\.gitleaks\.toml$''',
  '''go\.sum$''',
  '''package-lock\.json$''',
]
EOF
```

### Secret Scanning in CI/CD

```yaml
# GitHub Actions — scanning dei secret
name: Security Scan
on: [push, pull_request]

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Gitleaks scan
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: TruffleHog scan
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified
```

```yaml
# GitLab CI — scanning dei secret
secret_detection:
  stage: test
  image: registry.gitlab.com/security-products/secrets:5
  variables:
    SECRET_DETECTION_HISTORIC_SCAN: "true"
    SECRET_DETECTION_LOG_OPTIONS: "--all"
  artifacts:
    reports:
      secret_detection: gl-secret-detection-report.json
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Principi Operativi

**Least privilege per ogni identita:**
```hcl
# Vault policy — solo i permessi strettamente necessari
path "secret/data/webapp/database" {
  capabilities = ["read"]
}

# MAI concedere root o admin se non necessario
# MAI usare wildcard sui path se non necessario
# Preferire policy granulari per servizio
```

**Short-lived secrets dove possibile:**
```bash
# Preferire dynamic secrets con TTL breve
vault write database/roles/webapp-role \
  default_ttl=30m \    # 30 minuti — non 24 ore
  max_ttl=2h           # massimo 2 ore
```

**Audit logging obbligatorio:**
```bash
# Vault — abilitare SEMPRE l'audit
vault audit enable file file_path=/var/log/vault/audit.log

# AWS — abilitare CloudTrail per Secrets Manager
aws cloudtrail create-trail \
  --name secrets-audit-trail \
  --s3-bucket-name audit-logs-bucket \
  --is-multi-region-trail \
  --enable-log-file-validation

# Monitorare accessi anomali
# - Accessi fuori orario
# - Accessi da IP non conosciuti
# - Volume di lettura insolito
# - Tentativi di accesso negati
```

### Disaster Recovery per il Vault

```bash
# Vault Raft — snapshot automatico
vault operator raft snapshot save /backup/vault-snapshot-$(date +%Y%m%d).snap

# Ripristino da snapshot
vault operator raft snapshot restore /backup/vault-snapshot-20240315.snap

# Automatizzare con cron
# 0 */6 * * * /usr/local/bin/vault operator raft snapshot save /backup/vault-$(date +\%Y\%m\%d-\%H\%M).snap

# Verificare l'integrita del backup
vault operator raft snapshot inspect /backup/vault-snapshot-20240315.snap
```

**Checklist di sicurezza per secrets management:**
```
CHECKLIST — SECRETS MANAGEMENT

Prevenzione:
[ ] .gitignore configurato per escludere file con secret
[ ] Pre-commit hooks attivi (detect-secrets, gitleaks, git-secrets)
[ ] Secret scanning attivo nella CI/CD pipeline
[ ] Nessun secret hardcoded nel codice sorgente
[ ] Nessun secret nei log applicativi (mascheramento attivo)

Storage:
[ ] Tutti i secret memorizzati in un vault centralizzato
[ ] Crittografia at rest abilitata (AES-256 o superiore)
[ ] Accesso al vault protetto da autenticazione forte
[ ] Policy di accesso granulari (least privilege)

Distribuzione:
[ ] Secret distribuiti tramite canali sicuri (API vault, sidecar, CSI driver)
[ ] Nessun secret in variabili d'ambiente visibili
[ ] TLS 1.2+ per tutte le comunicazioni
[ ] mTLS per comunicazioni tra servizi dove possibile

Rotazione:
[ ] Policy di rotazione definite per ogni tipo di secret
[ ] Rotazione automatica implementata per credenziali database
[ ] Rotazione automatica per certificati TLS
[ ] Procedura di rotazione d'emergenza documentata e testata

Monitoring:
[ ] Audit logging attivo per ogni accesso ai secret
[ ] Alert per accessi anomali configurati
[ ] Dashboard di monitoraggio per scadenze secret e certificati
[ ] Revisione periodica degli accessi e delle policy

Disaster Recovery:
[ ] Backup regolari del vault
[ ] Procedura di ripristino documentata e testata
[ ] Chiavi di unseal distribuite in modo sicuro
[ ] Recovery plan per la compromissione del vault stesso
```

---

## 13. Vault Enterprise — Namespace e Multi-Tenancy

### Concetto di Namespace

I namespace di Vault Enterprise abilitano il **Secure Multi-Tenancy (SMT)** all'interno di una singola
installazione Vault. Ogni namespace funziona come un'istanza Vault isolata con i propri secret engine,
auth method, policy e audit device. Questa funzionalita richiede la licenza Vault Enterprise Standard
o un cluster HCP Vault.

I namespace risolvono diversi problemi organizzativi:
- **Isolamento tra team** — ogni team opera nel proprio namespace senza interferire con gli altri
- **Delegazione amministrativa** — gli admin di namespace gestiscono le proprie risorse autonomamente
- **Compliance** — audit separati per business unit, utili per conformita normativa
- **Self-service** — i team possono abilitare secret engine e configurare policy senza intervento del team platform

### Gerarchia dei Namespace

I namespace supportano una struttura gerarchica ad albero. Il namespace `root` e il padre di tutti
gli altri namespace. I namespace figli ereditano alcune configurazioni dal padre ma operano in modo
indipendente per quanto riguarda secret, token e lease.

```
root/
├── engineering/
│   ├── team-alpha/
│   └── team-beta/
├── finance/
│   ├── payments/
│   └── reporting/
└── platform/
    ├── shared-services/
    └── infrastructure/
```

### Gestione dei Namespace

```bash
# Creare un namespace
vault namespace create engineering
vault namespace create -namespace=engineering team-alpha
vault namespace create -namespace=engineering team-beta

# Elencare i namespace
vault namespace list
vault namespace list -namespace=engineering

# Operare all'interno di un namespace specifico
export VAULT_NAMESPACE="engineering/team-alpha"

# Oppure specificare il namespace per singola operazione
vault kv put -namespace=engineering/team-alpha secret/app/config api_key="abc123"

# Leggere un secret in un namespace figlio
vault kv get -namespace=engineering/team-alpha secret/app/config

# Abilitare un secret engine nel namespace
vault secrets enable -namespace=engineering/team-alpha -path=database database
vault auth enable -namespace=engineering/team-alpha kubernetes

# Eliminare un namespace (ATTENZIONE: elimina tutti i contenuti)
vault namespace delete -namespace=engineering team-beta
```

### Policy Cross-Namespace

Le policy nel namespace root possono concedere accesso ai namespace figli.
Le policy nei namespace figli non possono mai accedere ai namespace genitori o fratelli.

```hcl
# policy-engineering-admin.hcl — admin del namespace engineering
# Questa policy risiede nel namespace root

# Accesso completo al namespace engineering e ai suoi figli
path "engineering/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Gestione dei namespace figli sotto engineering
path "sys/namespaces/engineering/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
```

```hcl
# policy-team-alpha-dev.hcl — sviluppatore nel namespace team-alpha
# Questa policy risiede nel namespace engineering/team-alpha

# Accesso ai secret dell'applicazione
path "secret/data/app/*" {
  capabilities = ["read", "list"]
}

# Accesso alle credenziali dinamiche del database
path "database/creds/readonly" {
  capabilities = ["read"]
}

# Impossibile accedere a qualsiasi risorsa fuori dal proprio namespace
```

### Audit per Namespace

Ogni namespace puo avere i propri audit device, consentendo la separazione dei log
per conformita e governance:

```bash
# Abilitare audit nel namespace engineering
vault audit enable -namespace=engineering file \
  file_path=/var/log/vault/engineering-audit.log

# Abilitare audit nel namespace finance (log separati)
vault audit enable -namespace=finance file \
  file_path=/var/log/vault/finance-audit.log

# L'audit del namespace root cattura TUTTE le operazioni
# Gli audit dei namespace figli catturano solo le operazioni nel proprio scope
```

### Quotas e Rate Limiting per Namespace

Vault Enterprise permette di definire quote per namespace per prevenire l'abuso
di risorse e garantire l'equita tra i tenant:

```bash
# Rate limit per il namespace engineering: max 1000 richieste/secondo
vault write sys/quotas/rate-limit/engineering-limit \
  name="engineering-limit" \
  path="engineering/" \
  rate=1000 \
  interval="1s"

# Lease count quota: max 10000 lease attivi nel namespace finance
vault write sys/quotas/lease-count/finance-limit \
  name="finance-limit" \
  path="finance/" \
  max_leases=10000

# Verificare le quote attive
vault list sys/quotas/rate-limit/
vault read sys/quotas/rate-limit/engineering-limit
```

---

## 14. Vault Enterprise — Performance Replication e Disaster Recovery

### Modelli di Replication

Vault Enterprise offre due modelli di replication complementari che servono scopi distinti:

| Caratteristica | Performance Replication (PR) | Disaster Recovery (DR) |
|---|---|---|
| **Scopo** | Scalabilita orizzontale delle letture | Continuita operativa in caso di guasto |
| **Token e lease** | Gestiti localmente da ogni cluster | Condivisi con il primario |
| **Traffico in scrittura** | Inoltrato al primario | Non accettato (cluster passivo) |
| **Traffico in lettura** | Servito localmente | Non servito (standby) |
| **Failover** | Manuale — richiede promozione | Manuale o automatico con Vault Autopilot |
| **Licenza richiesta** | Enterprise Premium | Enterprise Standard |
| **Caso d'uso tipico** | Multi-region, riduzione latenza | Business continuity, RPO basso |

### Performance Replication

La Performance Replication replica la configurazione statica di Vault (secret KV, chiavi Transit,
policy, auth method) dal cluster primario ai cluster secondari. I cluster secondari gestiscono
i propri token e lease, rispondono autonomamente al traffico in lettura e inoltrano le scritture
al primario.

```bash
# --- Sul cluster PRIMARIO ---

# Abilitare la performance replication
vault write -f sys/replication/performance/primary/enable

# Generare un token per il cluster secondario
vault write sys/replication/performance/primary/secondary-token \
  id="eu-west-secondary" \
  ttl="30m"

# Output: un wrapping_token da consegnare al cluster secondario
```

```bash
# --- Sul cluster SECONDARIO ---

# Attivare il cluster come secondario
vault write sys/replication/performance/secondary/enable \
  token="<wrapping-token-dal-primario>"

# Verificare lo stato della replication
vault read sys/replication/performance/status

# Il cluster secondario ora:
# - Replica automaticamente secret, policy, auth method dal primario
# - Gestisce i propri token e lease
# - Risponde alle letture localmente
# - Inoltra le scritture al primario
```

**Architettura multi-region con Performance Replication:**
```
                  ┌────────────────────┐
                  │  Vault Primary     │
                  │  (eu-west-1)       │
                  │  Read + Write      │
                  └────────┬───────────┘
                           │ Replication
              ┌────────────┼────────────┐
              │            │            │
    ┌─────────▼──────┐ ┌──▼──────────┐ ┌▼──────────────┐
    │ PR Secondary   │ │ PR Secondary│ │ DR Secondary  │
    │ (us-east-1)    │ │ (ap-south-1)│ │ (eu-central-1)│
    │ Read + Forward │ │ Read+Forward│ │ Standby only  │
    └────────────────┘ └─────────────┘ └───────────────┘
```

### Disaster Recovery Replication

La DR Replication crea una copia esatta del cluster primario, inclusi token e lease.
Il cluster DR secondario resta in standby passivo e non accetta traffico finche non viene
promosso a primario durante un failover.

```bash
# --- Sul cluster PRIMARIO ---

# Abilitare la DR replication
vault write -f sys/replication/dr/primary/enable

# Generare un token DR per il secondario
vault write sys/replication/dr/primary/secondary-token \
  id="dr-eu-central" \
  ttl="30m"
```

```bash
# --- Sul cluster DR SECONDARIO ---

# Attivare come DR secondario
vault write sys/replication/dr/secondary/enable \
  token="<wrapping-token-dr>"

# Verificare lo stato DR
vault read sys/replication/dr/status
```

### Procedura di Failover DR

```bash
# SCENARIO: il cluster primario non e raggiungibile

# 1. Generare un DR operation token (richiede unseal key o recovery key)
vault operator generate-root -dr-token -init
vault operator generate-root -dr-token \
  -nonce="<nonce-dal-comando-init>" \
  "<unseal-key>"
# Ripetere con le unseal key fino al raggiungimento della soglia

# 2. Promuovere il DR secondario a primario
vault write sys/replication/dr/secondary/promote \
  dr_operation_token="<dr-operation-token>"

# 3. Il cluster promosso diventa il nuovo primario
# Aggiornare il DNS per puntare al nuovo primario
# Riconfigurare i secondari per puntare al nuovo primario

# 4. Quando il vecchio primario torna operativo, demotarlo a secondario
vault write sys/replication/dr/primary/demote
vault write sys/replication/dr/secondary/enable \
  token="<nuovo-token-dal-nuovo-primario>"
```

### Snapshot e Backup

```bash
# Snapshot automatico (Vault Enterprise)
vault operator raft snapshot save /backup/vault-$(date +%Y%m%d-%H%M%S).snap

# Snapshot scheduling automatico (Vault Enterprise 1.12+)
vault write sys/storage/raft/snapshot-auto/config/daily \
  interval="24h" \
  retain=30 \
  path_prefix="vault/snapshots" \
  storage_type="aws-s3" \
  aws_s3_bucket="vault-backups-prod" \
  aws_s3_region="eu-west-1" \
  aws_s3_server_side_encryption=true \
  aws_s3_kms_key="arn:aws:kms:eu-west-1:123456789:key/backup-key"

# Verificare lo stato degli snapshot automatici
vault read sys/storage/raft/snapshot-auto/config/daily
vault list sys/storage/raft/snapshot-auto/status/

# Ripristino da snapshot
vault operator raft snapshot restore -force /backup/vault-20260524-120000.snap
```

---

## 15. Confronto Cloud Secrets Manager

### Tabella Comparativa Completa

| Caratteristica | HashiCorp Vault | AWS Secrets Manager | Azure Key Vault | GCP Secret Manager |
|---|---|---|---|---|
| **Tipo** | Self-hosted / HCP (SaaS) | Fully managed | Fully managed | Fully managed |
| **Multi-cloud** | Nativo | Solo AWS | Solo Azure | Solo GCP |
| **Dynamic secrets** | Nativo (database, cloud, PKI) | Solo rotation | Non nativo | Non nativo |
| **Secrets engine** | 30+ engine | N/A | N/A | N/A |
| **Encryption as a Service** | Transit engine | No (usare KMS) | No (usare KV keys) | No (usare Cloud KMS) |
| **PKI/Certificati** | PKI engine integrato | ACM (servizio separato) | Certificate management | Certificate Manager |
| **Versioning** | KV v2 con N versioni | AWSCURRENT / AWSPREVIOUS | Versioni illimitate | Versioni illimitate |
| **Rotazione** | Dinamica + scheduled | Lambda + scheduled | Event Grid + Functions | Pub/Sub + Cloud Functions |
| **Replication** | PR + DR (Enterprise) | Cross-region nativa | Geo-replication (Premium) | Automatic / User-managed |
| **HSM support** | Vault Enterprise HSM | AWS CloudHSM | Managed HSM (FIPS 140-2 L3) | Cloud HSM |
| **Audit** | Audit device (file, syslog, socket) | CloudTrail | Azure Monitor / Diagnostic Logs | Cloud Audit Logs |
| **Costo (100 secret)** | Open source gratuito; Enterprise ~$0.03/hr | ~$40/mese + API calls | ~$0.03/secret/mese (Standard) | Gratuito (primi 10K versioni) |
| **Dimensione max secret** | Illimitata (KV) | 64 KB | 25 KB | 64 KB |
| **Soft delete** | KV v2 (configurabile) | Recovery window 7-30gg | Soft delete 7-90gg | Versioni disabilitabili |
| **Network isolation** | VPC, mTLS, private endpoint | VPC endpoint | Private endpoint | VPC Service Controls |
| **RBAC** | Policy HCL path-based | IAM + resource policy | Azure RBAC / Access Policy | IAM |
| **Kubernetes nativo** | VSO, Agent Injector, CSI | ESO, ASCP | ESO, CSI | ESO, Workload Identity |

### Criteri di Scelta

**Scegliere HashiCorp Vault quando:**
- L'organizzazione opera in ambiente multi-cloud o hybrid-cloud
- Si necessita di dynamic secrets per database, cloud provider o certificati
- Si richiede Encryption as a Service (Transit engine) per le applicazioni
- Si desidera una PKI completa gestita centralmente
- Sono necessari namespace per multi-tenancy
- Il team ha competenze per operare e mantenere l'infrastruttura Vault

**Scegliere AWS Secrets Manager quando:**
- L'infrastruttura risiede prevalentemente o esclusivamente su AWS
- Si desidera integrazione nativa con RDS, Redshift, DocumentDB
- Si preferisce un servizio fully managed senza overhead operativo
- La rotazione automatica con Lambda soddisfa i requisiti
- Non si necessita di dynamic secrets o encryption as a service

**Scegliere Azure Key Vault quando:**
- L'infrastruttura risiede prevalentemente su Azure
- Si necessita di HSM hardware (Managed HSM con FIPS 140-2 Level 3)
- Si richiede integrazione nativa con Azure AD, App Service, AKS
- La gestione dei certificati deve integrarsi con il ciclo di vita Azure

**Scegliere GCP Secret Manager quando:**
- L'infrastruttura risiede prevalentemente su GCP
- Si desidera un modello di pricing favorevole (gratuito fino a 10K versioni)
- Si utilizza GKE con Workload Identity per l'accesso ai secret
- Si richiede replication granulare per conformita con requisiti di residenza dati

### Strategia Multi-Cloud

In ambienti multi-cloud e consigliabile adottare un approccio a livelli:

```
Livello 1 — Vault Enterprise come orchestratore centrale
    ├── Secrets engine per ogni cloud provider
    ├── Transit engine per encryption unificata
    ├── PKI centralizzata
    └── Policy e audit unificati

Livello 2 — Cloud-native secrets manager per integrazione locale
    ├── AWS Secrets Manager per workload AWS
    ├── Azure Key Vault per workload Azure
    └── GCP Secret Manager per workload GCP

Livello 3 — External Secrets Operator per Kubernetes
    └── Sincronizzazione da qualsiasi backend verso K8s Secret
```

Vault funge da piano di controllo centralizzato, mentre i secrets manager cloud-native
servono come punti di distribuzione locali. ESO collega entrambi i livelli al mondo Kubernetes.

---

## 16. Secrets nelle Pipeline CI/CD — OIDC e Credenziali Effimere

### Il Problema delle Credenziali Statiche in CI/CD

Le pipeline CI/CD rappresentano uno dei vettori di attacco piu significativi per i secret.
Secondo il report GitGuardian 2026, i file di configurazione CI/CD e i build artifact
sono tra i principali vettori di esposizione dei secret. I rischi includono:

- **Secret statici nei CI/CD variables** — chiavi AWS, token Docker Hub, credenziali database
  memorizzate come variabili di pipeline, accessibili a chiunque abbia accesso al progetto
- **Secret nei log di build** — comandi che stampano variabili d'ambiente, output di debug
  che include credenziali in chiaro
- **Lifetime illimitato** — credenziali CI/CD che non vengono mai ruotate perche "funzionano"
- **Blast radius** — una singola credenziale CI/CD compromessa puo dare accesso a produzione

### OIDC Federation — Eliminare i Secret Statici

L'OpenID Connect (OIDC) federation consente alle pipeline CI/CD di autenticarsi
presso i cloud provider senza memorizzare credenziali statiche. La pipeline riceve
un token OIDC dal CI/CD provider, lo scambia con il cloud provider per ottenere
credenziali temporanee con scope limitato.

```
┌────────────┐    1. Richiesta     ┌────────────────┐
│ CI/CD      │───────────────────>│ OIDC Provider   │
│ Pipeline   │<───────────────────│ (GitHub/GitLab) │
│            │    2. JWT Token     │                 │
│            │                     └────────────────┘
│            │    3. JWT Token     ┌────────────────┐
│            │───────────────────>│ Cloud Provider   │
│            │<───────────────────│ (AWS/Azure/GCP)  │
│            │ 4. Credenziali     │                  │
│            │    Temporanee       └────────────────┘
└────────────┘    (15-60 min)
```

### GitHub Actions con OIDC

**Configurazione AWS con GitHub Actions OIDC:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS
on:
  push:
    branches: [main]

permissions:
  id-token: write   # Necessario per richiedere il token OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Nessun AWS_ACCESS_KEY_ID o AWS_SECRET_ACCESS_KEY necessario!
      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          role-session-name: github-actions-${{ github.run_id }}
          aws-region: eu-west-1
          # Il token dura solo per la durata del job

      - name: Deploy
        run: |
          aws ecs update-service --cluster prod --service webapp --force-new-deployment
```

**IAM Role per GitHub Actions OIDC (Terraform):**
```hcl
# Identity provider per GitHub
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]
}

# IAM Role assumibile solo da specifici repository e branch
resource "aws_iam_role" "github_actions_deploy" {
  name = "github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            # CRITICO: limitare a specifici repository e branch
            "token.actions.githubusercontent.com:sub" = "repo:myorg/myrepo:ref:refs/heads/main"
          }
        }
      }
    ]
  })
}

# Attachare solo i permessi strettamente necessari
resource "aws_iam_role_policy_attachment" "deploy" {
  role       = aws_iam_role.github_actions_deploy.name
  policy_arn = aws_iam_policy.ecs_deploy_only.arn
}
```

### GitLab CI con OIDC

```yaml
# .gitlab-ci.yml
deploy_production:
  stage: deploy
  image: amazon/aws-cli:2.17.0
  id_tokens:
    GITLAB_OIDC_TOKEN:
      aud: https://gitlab.example.com
  variables:
    ROLE_ARN: "arn:aws:iam::123456789012:role/gitlab-deploy"
  script:
    # Scambiare il token OIDC di GitLab per credenziali AWS temporanee
    - >
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s"
      $(aws sts assume-role-with-web-identity
      --role-arn ${ROLE_ARN}
      --role-session-name "gitlab-ci-${CI_JOB_ID}"
      --web-identity-token ${GITLAB_OIDC_TOKEN}
      --duration-seconds 900
      --query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]"
      --output text))
    - aws ecs update-service --cluster prod --service webapp --force-new-deployment
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### Vault come Broker di Credenziali per CI/CD

```yaml
# GitHub Actions — ottenere secret da Vault via JWT auth
name: Deploy with Vault
on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Import secrets from Vault
        uses: hashicorp/vault-action@v3
        with:
          url: https://vault.example.com:8200
          method: jwt
          role: github-actions-deploy
          jwtGithubAudience: https://vault.example.com
          secrets: |
            secret/data/webapp/database username | DB_USERNAME ;
            secret/data/webapp/database password | DB_PASSWORD ;
            database/creds/deploy-role username | DYNAMIC_DB_USER ;
            database/creds/deploy-role password | DYNAMIC_DB_PASS

      - name: Run database migration
        run: |
          # Le variabili DB_USERNAME, DB_PASSWORD, DYNAMIC_DB_USER, DYNAMIC_DB_PASS
          # sono disponibili come env var mascherate nel log
          ./scripts/migrate.sh
```

```bash
# Configurazione Vault JWT auth per GitHub Actions
vault auth enable jwt

vault write auth/jwt/config \
  bound_issuer="https://token.actions.githubusercontent.com" \
  oidc_discovery_url="https://token.actions.githubusercontent.com"

vault write auth/jwt/role/github-actions-deploy \
  role_type="jwt" \
  bound_audiences="https://vault.example.com" \
  bound_claims_type="glob" \
  bound_claims='{"sub":"repo:myorg/myrepo:ref:refs/heads/main"}' \
  user_claim="actor" \
  policies="cicd-deploy-policy" \
  token_ttl="10m" \
  token_max_ttl="15m"
```

### Protezione dei Log di Build

```yaml
# GitHub Actions — mascherare tutti i secret nei log
- name: Mask sensitive values
  run: |
    echo "::add-mask::${{ env.DB_PASSWORD }}"
    echo "::add-mask::${{ env.API_TOKEN }}"

# GitLab CI — variabili masked e protected
variables:
  DB_PASSWORD:
    value: ""  # impostato nella UI di GitLab
    masked: true       # non appare mai nei log
    protected: true    # disponibile solo su branch protetti
    description: "Database password for production"
```

---

## 17. Secrets Scanning Avanzato

### Panoramica degli Strumenti

Il secrets scanning e la pratica di analizzare il codice sorgente, la history Git,
i file di configurazione e i build artifact per individuare credenziali accidentalmente esposte.
Secondo GitGuardian, nel 2025 sono stati esposti quasi 29 milioni di nuovi secret su GitHub
pubblico, con un incremento del 34% anno su anno. Il 64% dei secret esposti nel 2022
risultava ancora valido all'inizio del 2026.

### Confronto Strumenti di Scanning

| Caratteristica | TruffleHog | Gitleaks | detect-secrets | GitGuardian |
|---|---|---|---|---|
| **Approccio** | Regex + entropy + verifica live | Regex (pattern matching) | Entropy + plugin + baseline | SaaS + pattern + ML |
| **Tipi di secret** | 800+ con verifica API | 150+ pattern predefiniti | Estensibile con plugin | 400+ con context analysis |
| **Verifica live** | Si — conferma se il secret e valido | No | No | Si (piano enterprise) |
| **Falsi positivi** | Bassi (grazie alla verifica) | Medi (solo pattern) | Bassi (baseline riduce noise) | Bassi (ML-based) |
| **Velocita** | Media | Alta | Media | Alta (SaaS) |
| **Pre-commit hook** | Si | Si | Si | Si |
| **CI/CD integration** | GitHub Actions, GitLab CI | GitHub Actions, GitLab CI | GitHub Actions, hook locali | Dashboard SaaS + API |
| **Licenza** | Open source (AGPL v3) | Open source (MIT) | Open source (Apache 2.0) | Freemium / Enterprise |
| **Scansione history** | Completa | Completa | Solo diff (per default) | Completa |

### TruffleHog — Scansione con Verifica

TruffleHog si distingue per la capacita di verificare se un secret individuato e effettivamente
valido, effettuando chiamate API al servizio corrispondente. Questo riduce drasticamente
i falsi positivi e permette di prioritizzare la remediation.

```bash
# Installazione
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin

# Scansione di un repository Git (include tutta la history)
trufflehog git https://github.com/myorg/myrepo --only-verified

# Scansione del filesystem locale
trufflehog filesystem --directory=/path/to/project --only-verified

# Scansione di un'organizzazione GitHub intera
trufflehog github --org=myorg --only-verified --token=$GITHUB_TOKEN

# Scansione di un registro Docker
trufflehog docker --image=myregistry.io/myapp:latest

# Scansione di un bucket S3
trufflehog s3 --bucket=my-config-bucket --only-verified

# Scansione CI/CD (GitHub Actions, GitLab, CircleCI)
trufflehog github --org=myorg --include-workflows --only-verified

# Output in formato JSON per integrazione con SIEM
trufflehog git /path/to/repo --only-verified --json | \
  jq 'select(.Verified == true)' > verified-secrets.json
```

**Esempio di output TruffleHog:**
```json
{
  "SourceMetadata": {
    "Data": {
      "Git": {
        "commit": "a1b2c3d4e5f6...",
        "file": "config/prod.env",
        "email": "dev@example.com",
        "repository": "https://github.com/myorg/myrepo",
        "timestamp": "2024-03-15T10:30:00Z",
        "line": 42
      }
    }
  },
  "DetectorType": "AWS",
  "Verified": true,
  "Raw": "AKIA...",
  "ExtraData": {
    "account": "123456789012",
    "arn": "arn:aws:iam::123456789012:user/ci-deploy",
    "resource_type": "Access key"
  }
}
```

### Gitleaks — Scansione Leggera e Veloce

```bash
# Installazione
GITLEAKS_VERSION="8.21.0"
wget "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
tar -xzf "gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
sudo mv gitleaks /usr/local/bin/

# Scansione di un repository locale (tutta la history)
gitleaks detect --source=/path/to/repo --verbose

# Scansione solo dei file non committati (pre-commit)
gitleaks protect --source=/path/to/repo --staged

# Scansione con report
gitleaks detect --source=/path/to/repo \
  --report-format=json \
  --report-path=gitleaks-report.json

# Scansione con configurazione personalizzata
gitleaks detect --source=/path/to/repo \
  --config=/path/to/.gitleaks.toml
```

### detect-secrets — Approccio Baseline

detect-secrets adotta un approccio diverso: crea un file baseline che registra
i "secret accettabili" (falsi positivi noti) e segnala solo le nuove occorrenze.
Questo riduce significativamente il rumore su codebase esistenti di grandi dimensioni.

```bash
# Installazione
pip install detect-secrets

# Creare il baseline iniziale (scansione completa del progetto)
detect-secrets scan --baseline .secrets.baseline

# Audit interattivo del baseline (classificare ogni finding)
detect-secrets audit .secrets.baseline

# Scansione incrementale (solo nuovi file/modifiche)
detect-secrets scan --baseline .secrets.baseline --update .secrets.baseline

# Verificare che non ci siano nuovi secret non presenti nel baseline
detect-secrets-hook --baseline .secrets.baseline file1.py file2.yaml

# Plugin personalizzati per pattern specifici
detect-secrets scan \
  --list-all-plugins   # mostra i plugin disponibili

# Disabilitare plugin ad alto rumore
detect-secrets scan \
  --disable-plugin HexHighEntropyString \
  --baseline .secrets.baseline
```

### Workflow di Remediation Post-Detection

Quando un secret viene individuato nel codice o nella history Git, la procedura di remediation
deve seguire un ordine preciso:

```
WORKFLOW DI REMEDIATION — SECRET ESPOSTO

1. REVOCA IMMEDIATA (entro 15 minuti dal rilevamento)
   [ ] Revocare/disabilitare il secret esposto presso il provider
   [ ] AWS: disattivare la access key in IAM
   [ ] Database: ALTER USER ... PASSWORD ... o DROP USER
   [ ] API key: revocare nel dashboard del provider
   [ ] Token: invalidare nel sistema di autenticazione

2. SOSTITUZIONE (entro 1 ora)
   [ ] Generare un nuovo secret con entropia adeguata
   [ ] Aggiornare il secret nel vault centralizzato
   [ ] Verificare che tutti i consumer utilizzino il nuovo secret
   [ ] Monitorare gli errori di autenticazione post-sostituzione

3. PULIZIA DELLA HISTORY GIT (se necessario)
   [ ] Usare git-filter-repo per rimuovere il secret dalla history
       git filter-repo --invert-paths --path <file-con-secret>
   [ ] OPPURE usare BFG Repo-Cleaner per la rimozione specifica
       bfg --replace-text secrets.txt repo.git
   [ ] Force-push (solo dopo coordinamento con il team)
   [ ] Tutti i collaboratori devono re-clonare il repository

4. ANALISI FORENSE (entro 24 ore)
   [ ] Verificare se il secret e stato utilizzato in modo non autorizzato
   [ ] Analizzare CloudTrail / audit log per accessi sospetti
   [ ] Determinare il periodo di esposizione
   [ ] Documentare la root cause

5. PREVENZIONE
   [ ] Aggiungere pattern al pre-commit hook
   [ ] Aggiungere alla CI/CD pipeline
   [ ] Formare il team sull'uso dei vault
```

### Integrazione Multi-Layer in CI/CD

```yaml
# GitHub Actions — scanning multi-tool
name: Secret Scanning
on: [push, pull_request]

jobs:
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # History completa per scansione approfondita

      # Layer 1: Gitleaks — veloce, cattura i pattern comuni
      - name: Gitleaks scan
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # Layer 2: TruffleHog — verifica live dei secret trovati
      - name: TruffleHog deep scan
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified --results=verified

      # Layer 3: detect-secrets — confronto con baseline
      - name: detect-secrets check
        run: |
          pip install detect-secrets
          detect-secrets scan --baseline .secrets.baseline --update .secrets.baseline
          git diff --exit-code .secrets.baseline || \
            (echo "ERRORE: nuovi secret rilevati!" && exit 1)
```

---

## 18. Secrets Governance e Identita Non-Umane (NHI)

### Il Problema delle Non-Human Identities

Le Non-Human Identities (NHI) — service account, API key, token di servizio, certificati machine-to-machine,
bot, pipeline CI/CD — superano le identita umane in rapporto di 45:1 nella maggior parte delle organizzazioni.
La gestione inadeguata delle NHI rappresenta uno dei rischi di sicurezza piu sottovalutati.

OWASP ha pubblicato nel 2025 la **Non-Human Identities Top 10**, una classificazione dei rischi
specifici per le identita non umane:

| Posizione | Rischio OWASP NHI | Descrizione |
|---|---|---|
| NHI1 | Improper Offboarding | Credenziali non revocate quando un servizio viene dismesso |
| NHI2 | Secret Leakage | Secret esposti in codice, log, configurazioni |
| NHI3 | Vulnerable Third-Party NHI | Dipendenze con secret compromessi o permessi eccessivi |
| NHI4 | Insecure Authentication | Meccanismi di autenticazione deboli per le NHI |
| NHI5 | Overprivileged NHI | Permessi eccessivi rispetto al principio del minimo privilegio |
| NHI6 | Insecure Cloud Deployment Configurations | Misconfigurazioni cloud che espongono le NHI |
| NHI7 | Long-Lived Secrets | Credenziali statiche con lifetime illimitato o eccessivamente lungo |
| NHI8 | Environment Isolation Failure | Secret di produzione accessibili da ambienti non-prod |
| NHI9 | NHI Reuse | Stessa identita condivisa tra piu servizi o ambienti |
| NHI10 | Human Use of NHI | Operatori che usano service account per attivita interattive |

### Lifecycle Management delle NHI

La gestione del ciclo di vita delle identita non umane richiede processi equivalenti
a quelli delle identita umane, con automazione aggiuntiva:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Provisioning│───>│  Active Use  │───>│  Rotation    │───>│ Decommission │
│              │    │              │    │              │    │              │
│ - Creare NHI │    │ - Monitorare │    │ - Ruotare    │    │ - Revocare   │
│ - Assegnare  │    │   accessi    │    │   credenziali│    │   credenziali│
│   permessi   │    │ - Audit log  │    │ - Verificare │    │ - Eliminare  │
│   minimi     │    │ - Anomaly    │    │   funzionalita│   │   permessi   │
│ - Documentare│    │   detection  │    │ - Aggiornare │    │ - Archiviare │
│   owner      │    │              │    │   consumer   │    │   audit log  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### Inventario e Classificazione

Un programma di secrets governance efficace inizia con un inventario completo:

```bash
# Script di discovery per NHI su AWS
# Elencare tutte le access key IAM con l'eta
aws iam generate-credential-report
aws iam get-credential-report --output text --query Content | base64 -d | \
  awk -F, '$4=="true" && $9!="N/A" {
    split($9,a,"T"); 
    cmd="date -d \""a[1]"\" +%s"; cmd | getline created; close(cmd);
    cmd="date +%s"; cmd | getline now; close(cmd);
    age=int((now-created)/86400);
    if(age>90) print "CRITICO: "$1" - access key vecchia di "age" giorni"
  }'

# Elencare tutti i service account GCP con i ruoli
gcloud iam service-accounts list --format="table(email,disabled)" | \
  while read -r sa disabled; do
    echo "--- $sa (disabled: $disabled) ---"
    gcloud projects get-iam-policy PROJECT_ID \
      --flatten="bindings[].members" \
      --filter="bindings.members:serviceAccount:$sa" \
      --format="value(bindings.role)"
  done

# Vault — elencare tutti i token attivi e i loro accessor
vault list auth/token/accessors
```

### Secrets Ownership e Accountability

Ogni secret deve avere un proprietario identificato. La mancanza di ownership porta
a secret orfani che non vengono mai ruotati ne dismessi:

```hcl
# Vault KV — metadata di ownership (pratica raccomandata)
vault kv put secret/webapp/database \
  username="webapp_user" \
  password="SecurePassword123!" \
  _metadata_owner="team-platform@example.com" \
  _metadata_classification="critical" \
  _metadata_rotation_policy="90days" \
  _metadata_created_date="2026-05-24" \
  _metadata_next_rotation="2026-08-22" \
  _metadata_jira_ticket="SEC-4521"
```

### Conformita Normativa

**PCI DSS 4.0 (requisiti mandatori dal 31 marzo 2025):**
- Requisito 7.2.5 — gestire e monitorare tutti gli account, incluse le NHI
- Requisito 8.3.6 — complessita minima per le password di account di servizio
- Requisito 8.6.1 — se gli account di sistema possono essere usati interattivamente,
  gestirli con autenticazione multi-fattore
- Requisito 8.6.3 — cambiare le password degli account di servizio periodicamente
  e alla sospetta compromissione

**SOC 2 Type II:**
- CC6.1 — implementare controlli logici di accesso per proteggere le informazioni sensibili
- CC6.3 — autorizzare, modificare e rimuovere l'accesso alle risorse in modo tempestivo

**GDPR:**
- Articolo 32 — misure tecniche adeguate per garantire la sicurezza del trattamento,
  inclusa la crittografia e la capacita di garantire la riservatezza dei sistemi

### Metriche di Governance

```
DASHBOARD — SECRETS GOVERNANCE

Metriche operative:
- Numero totale di secret gestiti: ___
- Numero di NHI attive: ___
- Secret con owner assegnato: ___%
- Secret con policy di rotazione definita: ___%
- Secret ruotati entro la policy: ___%
- Tempo medio di rotazione (MTTR): ___ ore
- Secret scaduti non ruotati: ___

Metriche di sicurezza:
- Secret esposti in scansioni (ultimi 30gg): ___
- Tempo medio di remediation per secret esposto: ___ ore
- Tentativi di accesso negati (ultimi 30gg): ___
- NHI con permessi eccessivi identificate: ___
- NHI orfane (senza owner) identificate: ___
- Access key con eta > 90 giorni: ___

Metriche di compliance:
- Secret conformi alla policy di rotazione: ___%
- Audit log completi e integri: Si/No
- Ultima revisione degli accessi NHI: data
- Prossima revisione pianificata: data
```

---

## 19. Zero-Trust Secrets Access

### Principi Zero-Trust Applicati ai Secret

Il modello Zero Trust applicato al secrets management elimina la fiducia implicita
basata sulla posizione di rete, sull'identita del servizio o sulla membership
in un namespace. Ogni accesso a un secret deve essere:

1. **Verificato** — l'identita del richiedente e confermata crittograficamente
2. **Autorizzato** — i permessi sono valutati al momento della richiesta, non staticamente
3. **Limitato** — l'accesso e concesso con il minimo privilegio per il minimo tempo necessario
4. **Auditato** — ogni accesso e registrato con contesto completo per analisi forense
5. **Effimero** — le credenziali rilasciate hanno una durata limitata e vengono revocate automaticamente

### Credenziali Effimere come Default

In un'architettura zero-trust, le credenziali statiche a lunga durata sono l'eccezione,
non la regola. L'obiettivo e che ogni credenziale abbia un TTL il piu breve possibile:

| Tipo di Credenziale | TTL Raccomandato | Meccanismo |
|---|---|---|
| Token CI/CD | 10-15 minuti | OIDC federation |
| Credenziali database per applicazioni | 30-60 minuti | Vault dynamic secrets |
| Credenziali database per batch job | Durata del job | Vault dynamic secrets |
| Certificati TLS inter-servizio | 24-72 ore | Vault PKI / cert-manager |
| Token di accesso API | 1-4 ore | OAuth 2.0 / Vault |
| Chiavi di firma | 90 giorni | Vault Transit con auto-rotation |

### SPIFFE/SPIRE per Workload Identity

SPIFFE (Secure Production Identity Framework For Everyone) e uno standard CNCF
per l'identita crittografica dei workload. SPIRE e l'implementazione di riferimento.
Insieme forniscono identita verificabile senza richiedere secret pre-condivisi.

```
┌────────────────────────────────────────────────────────┐
│                    SPIRE Server                         │
│  - Emette SVID (SPIFFE Verifiable Identity Document)   │
│  - Attesta l'identita dei workload                     │
│  - Gestisce la trust root (certificate authority)      │
└─────────────────────┬──────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
   ┌──────▼─────┐ ┌──▼──────┐ ┌─▼─────────┐
   │ SPIRE Agent│ │ SPIRE   │ │ SPIRE     │
   │ (Node 1)   │ │ Agent   │ │ Agent     │
   │            │ │ (Node 2)│ │ (Node 3)  │
   └──────┬─────┘ └────┬────┘ └─────┬─────┘
          │             │            │
   ┌──────▼─────┐ ┌────▼────┐ ┌────▼──────┐
   │ Workload A │ │Workload │ │ Workload  │
   │ SVID:      │ │B: SVID: │ │ C: SVID:  │
   │ spiffe://  │ │spiffe://│ │ spiffe:// │
   │ example/   │ │example/ │ │ example/  │
   │ webapp     │ │api      │ │ database  │
   └────────────┘ └─────────┘ └───────────┘
```

Ogni workload riceve un SVID (X.509 o JWT) che:
- Identifica univocamente il workload tramite un URI SPIFFE
- E emesso senza richiedere secret pre-condivisi (attestazione basata su piattaforma)
- Ha un TTL breve e viene rinnovato automaticamente
- Puo essere usato per mTLS tra servizi senza gestione manuale dei certificati

```yaml
# SPIRE Server su Kubernetes (Helm)
# helm install spire spiffe/spire --namespace spire --create-namespace

# RegistrationEntry — definire quale workload riceve quale identita
apiVersion: spire.spiffe.io/v1alpha1
kind: ClusterSPIFFEID
metadata:
  name: webapp-identity
spec:
  spiffeIDTemplate: "spiffe://example.com/ns/{{ .PodMeta.Namespace }}/sa/{{ .PodSpec.ServiceAccountName }}"
  podSelector:
    matchLabels:
      app: webapp
  namespaceSelector:
    matchLabels:
      environment: production
```

### Just-In-Time (JIT) Access

Il JIT access concede permessi elevati solo quando necessario e solo per la durata
strettamente richiesta, eliminando i permessi permanenti:

```bash
# Vault — Sentinel policy per JIT access (Enterprise)
# L'accesso a secret critici richiede approvazione in tempo reale

# Configurare un Control Group (Vault Enterprise)
vault write auth/approle/role/emergency-access \
  token_ttl=15m \
  token_max_ttl=30m \
  token_policies="emergency-readonly"

# Control Group policy — richiede approvazione da un admin
# control-group-policy.hcl
path "secret/data/production/master-key" {
  capabilities = ["read"]
  control_group = {
    factor "admin-approval" {
      controlled_capabilities = ["read"]
      identity {
        group_names = ["security-admins"]
        approvals   = 1
      }
    }
    ttl = "10m"
  }
}
```

### Identity Broker Pattern

L'Identity Broker centralizza l'emissione di credenziali effimere, eliminando
la necessita per i workload di gestire direttamente secret statici:

```
┌────────────┐                           ┌────────────────┐
│ Workload A │──1. Attestazione────────>│ Identity Broker │
│ (nessun    │     (prova di identita)   │ (Vault/SPIRE)  │
│  secret    │                           │                 │
│  statico)  │<─2. Credenziale effimera──│ - Verifica      │
│            │     (TTL breve, scoped)   │   identita      │
│            │                           │ - Emette cred   │
│            │──3. Accesso alla──────────│   con minimo    │
│            │     risorsa target        │   privilegio    │
└────────────┘                           └────────────────┘
                                                │
                                         ┌──────▼──────┐
                                         │ Risorsa     │
                                         │ (Database,  │
                                         │  API, Cloud)│
                                         └─────────────┘
```

L'Identity Broker verifica l'identita del workload tramite attestazione della piattaforma
(Kubernetes service account, instance metadata, TPM) e non tramite un secret pre-condiviso.
Questo elimina il bootstrap problem dei secret.

### Monitoring Zero-Trust per i Secret

```yaml
# PrometheusRule — alert per violazioni zero-trust
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: secrets-zero-trust-alerts
  namespace: monitoring
spec:
  groups:
    - name: secrets-zero-trust
      rules:
        # Alert: secret statico non ruotato da piu di 90 giorni
        - alert: StaleStaticSecret
          expr: |
            (time() - vault_secret_last_rotation_timestamp) > 90 * 24 * 3600
          for: 1h
          labels:
            severity: high
          annotations:
            summary: "Secret statico {{ $labels.path }} non ruotato da piu di 90 giorni"
            runbook: "Ruotare immediatamente o migrare a dynamic secrets"

        # Alert: volume anomalo di letture su un secret
        - alert: AnomalousSecretAccess
          expr: |
            rate(vault_audit_log_request_total{operation="read"}[5m]) > 
            2 * avg_over_time(vault_audit_log_request_total{operation="read"}[7d])
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Volume anomalo di letture sul path {{ $labels.path }}"

        # Alert: accesso a secret da IP non previsto
        - alert: UnexpectedSecretAccessSource
          expr: |
            vault_audit_log_request_total{source_ip!~"10\\..*|172\\.1[6-9]\\..*|172\\.2[0-9]\\..*|172\\.3[0-1]\\..*|192\\.168\\..*"} > 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "Accesso a secret da IP esterno {{ $labels.source_ip }}"
            action: "Investigare immediatamente — possibile compromissione"

        # Alert: lease dinamico non rinnovato (workload potenzialmente crashato)
        - alert: OrphanedDynamicLease
          expr: |
            vault_expire_num_leases{type="dynamic"} > 1000
          for: 30m
          labels:
            severity: warning
          annotations:
            summary: "Elevato numero di lease dinamici attivi — verificare workload"
```

### Checklist Zero-Trust per Secrets

```
CHECKLIST — ZERO-TRUST SECRETS ACCESS

Identita:
[ ] Ogni workload ha un'identita crittografica verificabile (SPIFFE, K8s SA, Managed Identity)
[ ] Nessun workload si autentica tramite secret statici pre-condivisi
[ ] Le identita sono attestate dalla piattaforma (non da file statici)
[ ] Le identita hanno scope limitato al singolo workload (no condivisione tra servizi)

Credenziali:
[ ] Default: credenziali dinamiche con TTL breve (<1h per database, <15m per CI/CD)
[ ] Nessuna credenziale a lunga durata senza giustificazione documentata
[ ] Le credenziali sono scoped al minimo privilegio necessario
[ ] Le credenziali non ruotate sono individuate e segnalate automaticamente

Accesso:
[ ] Ogni accesso a secret e autenticato e autorizzato al momento della richiesta
[ ] Policy di accesso valutate dinamicamente (non solo al login)
[ ] JIT access per operazioni privilegiate con approvazione e TTL limitato
[ ] Nessun accesso basato su posizione di rete (VPN/IP non e sufficiente)

Audit:
[ ] Ogni accesso ai secret e registrato con timestamp, identita, IP, operazione
[ ] Alert automatici per pattern anomali (volume, orario, IP, frequenza)
[ ] Log inalterabili e centralizzati (SIEM, CloudTrail, Vault audit)
[ ] Revisione periodica degli accessi (almeno trimestrale)

Segmentazione:
[ ] Secret di produzione isolati da staging/development (namespace, account, progetto)
[ ] Nessun secret di produzione accessibile da ambienti non-prod
[ ] Rotazione indipendente per ogni ambiente
[ ] Blast radius limitato per ogni credenziale (scope al singolo servizio)
```

---

## Esercizi

### Esercizio 1 — Vault Dev Server e Secret Engine

Avviare un HashiCorp Vault in modalita dev. Abilitare il secret engine KV v2. Scrivere, leggere e versionare un secret. Configurare una policy che consenta a un'applicazione l'accesso in sola lettura a un path specifico. Creare un token con quella policy e verificare che non possa scrivere.

### Esercizio 2 — Dynamic Database Credentials

Configurare il database secret engine di Vault per generare credenziali PostgreSQL dinamiche con TTL di 1 ora. Creare un ruolo che generi utenti con permessi limitati (SELECT su specifiche tabelle). Verificare che le credenziali scadano automaticamente e che l'utente venga revocato nel database.

### Esercizio 3 — External Secrets Operator su Kubernetes

Installare External Secrets Operator (ESO) su un cluster Kubernetes. Configurare un SecretStore che punti a Vault o AWS Secrets Manager. Creare un ExternalSecret che sincronizzi un secret nel namespace dell'applicazione. Verificare che la modifica del secret nel vault si propaghi automaticamente.

### Esercizio 4 — Secret Detection e Pre-commit Hook

Configurare `gitleaks` come pre-commit hook in un repository. Aggiungere intenzionalmente un API key hardcoded in un file e verificare che il commit venga bloccato. Configurare anche un job CI che esegua gitleaks sull'intera history del repository. Remediation: rimuovere il secret e ruotarlo.

### Esercizio 5 — Emergency Rotation e Disaster Recovery

Simulare la compromissione di un secret critico (es. credenziali database di produzione). Eseguire la procedura di emergency rotation: revocare immediatamente le credenziali compromesse, generare nuove credenziali, distribuirle ai servizi, verificare che tutti i servizi funzionino con le nuove credenziali. Documentare il runbook e il tempo totale.

---

## Letture e Riferimenti

### Documentazione ufficiale

- HashiCorp Vault Documentation — <https://developer.hashicorp.com/vault/docs> (consultato: 2026-05-24)
- AWS Secrets Manager User Guide — <https://docs.aws.amazon.com/secretsmanager/latest/userguide/> (consultato: 2026-05-24)
- Azure Key Vault Documentation — <https://learn.microsoft.com/en-us/azure/key-vault/> (consultato: 2026-05-24)
- GCP Secret Manager Documentation — <https://cloud.google.com/secret-manager/docs> (consultato: 2026-05-24)
- External Secrets Operator — <https://external-secrets.io/latest/> (consultato: 2026-05-24)
- Gitleaks Documentation — <https://github.com/gitleaks/gitleaks> (consultato: 2026-05-24)

### Libri consigliati

- Rice L., *Container Security*, O'Reilly, 2020
- Madakor G., *Kubernetes Security and Observability*, O'Reilly, 2022
- Ratan A., *HashiCorp Vault*, Packt, 2024

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con Secrets Management |
|--------|--------|----------------------------------|
| [05](05-kubernetes.md) | Kubernetes | CSI Secret Store Driver, ExternalSecret, RBAC per Secret nativi |
| [07](07-ci-cd.md) | CI/CD | Iniezione secret nella pipeline, gitleaks scan, OIDC per autenticazione |
| [11](11-database-management.md) | Database Management | Dynamic credentials per DB, rotation password, connection string sicure |
| [13](13-sicurezza-piattaforme.md) | Sicurezza delle Piattaforme | Gestione chiavi di encryption, mTLS certificate management |
| [14](14-compliance.md) | Compliance e Normative | Audit trail accessi ai secret, conformita GDPR e SOC 2 |
| [20](20-supply-chain-slsa-cosign.md) | Supply Chain SLSA e Cosign | Signing keys, cosign keyless, chiavi di firma per la supply chain |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Vault** | Strumento open source di HashiCorp per la gestione centralizzata di secret, encryption e accessi |
| **Secret engine** | Componente di Vault che genera, gestisce o memorizza un tipo specifico di secret (KV, database, PKI) |
| **Dynamic secret** | Credenziale generata on-demand da Vault con TTL definito, revocata automaticamente alla scadenza |
| **Unsealing** | Processo di apertura del vault crittografato tramite combinazione di chiavi condivise (Shamir) |
| **Rotation** | Processo di sostituzione periodica dei secret per limitare l'esposizione in caso di compromissione |
| **Lease** | Durata temporale associata a un secret dinamico, dopo la quale il secret viene automaticamente revocato |
| **KV (Key-Value) engine** | Secret engine di Vault per memorizzare coppie chiave-valore con supporto a versionamento |
| **CSI Secret Store Driver** | Driver Kubernetes che monta i secret da un vault esterno come volume nel pod |
| **External Secrets Operator (ESO)** | Operatore Kubernetes che sincronizza i secret da sistemi esterni in Secret K8s nativi |
| **Gitleaks** | Strumento open source per rilevare secret hardcoded nel codice sorgente e nella history git |
| **mTLS certificate** | Certificato X.509 usato per l'autenticazione reciproca tra client e server in comunicazioni TLS |
| **OIDC (OpenID Connect)** | Protocollo di autenticazione federata usato per l'accesso a Vault senza credenziali statiche |
| **Shamir's Secret Sharing** | Algoritmo crittografico che divide un secret in N parti di cui M sono sufficienti per la ricostruzione |
| **Emergency rotation** | Processo accelerato di sostituzione di un secret compromesso con revoca immediata del precedente |
| **Namespace (Vault)** | Partizione logica all'interno di Vault Enterprise che fornisce isolamento multi-tenant con secret engine, auth method, policy e audit device indipendenti per ogni tenant |
| **Performance Replication** | Funzionalita Vault Enterprise che replica la configurazione statica (secret, policy, auth) dal cluster primario ai secondari per scalabilita orizzontale delle letture, con token e lease gestiti localmente |
| **Disaster Recovery Replication** | Funzionalita Vault Enterprise che crea una copia esatta del cluster primario (inclusi token e lease) in un cluster standby, pronto per la promozione in caso di guasto del primario |
| **OIDC Federation** | Meccanismo che consente alle pipeline CI/CD di autenticarsi presso cloud provider scambiando un token OIDC emesso dal CI/CD provider per credenziali temporanee, eliminando la necessita di secret statici |
| **TruffleHog** | Strumento open source di secrets scanning che verifica la validita dei secret individuati effettuando chiamate API live ai servizi corrispondenti, classificando oltre 800 tipi di credenziali |
| **detect-secrets** | Strumento open source di Yelp che utilizza un approccio baseline per il secrets scanning, registrando le occorrenze note e segnalando solo le nuove, riducendo i falsi positivi su codebase di grandi dimensioni |
| **Non-Human Identity (NHI)** | Identita digitale associata a un'entita non umana come service account, API key, bot, pipeline CI/CD o certificato machine-to-machine, che richiede gestione del ciclo di vita equivalente alle identita umane |
| **SPIFFE** | Secure Production Identity Framework For Everyone — standard CNCF per l'identita crittografica verificabile dei workload, basato su URI univoci e documenti di identita verificabili (SVID) senza richiedere secret pre-condivisi |
| **SPIRE** | Implementazione di riferimento dello standard SPIFFE che fornisce attestazione dell'identita dei workload, emissione di SVID (X.509 o JWT) e gestione della trust root tramite una certificate authority integrata |
| **SVID** | SPIFFE Verifiable Identity Document — documento crittografico (certificato X.509 o token JWT) che attesta l'identita di un workload secondo lo standard SPIFFE, con TTL breve e rinnovo automatico |
| **JIT Access** | Just-In-Time Access — modello di accesso zero-trust in cui i permessi elevati vengono concessi solo al momento della richiesta, per una durata limitata, con approvazione esplicita e audit completo |
| **Secrets sprawl** | Fenomeno di proliferazione incontrollata di credenziali e secret attraverso codice sorgente, file di configurazione, log, build artifact e canali di comunicazione non sicuri |
| **Identity Broker** | Componente dell'architettura zero-trust che centralizza l'emissione di credenziali effimere, verificando l'identita del workload tramite attestazione della piattaforma e rilasciando credenziali scoped con TTL breve |
| **Envelope Encryption** | Schema di crittografia gerarchica in cui una master key (KEK) protegge le data key (DEK) che a loro volta crittografano i dati effettivi, consentendo la rotazione della master key senza ricrittografare tutti i dati |
| **Control Group (Vault)** | Funzionalita Vault Enterprise che richiede l'approvazione esplicita da parte di uno o piu autorizzatori prima di concedere l'accesso a un secret critico, implementando il principio del JIT access |
| **Secrets baseline** | File di riferimento utilizzato da strumenti come detect-secrets che registra le occorrenze di potenziali secret note e accettate, consentendo la scansione incrementale e la riduzione dei falsi positivi |
