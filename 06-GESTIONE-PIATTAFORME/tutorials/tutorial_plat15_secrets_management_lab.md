# Tutorial: Secrets Management — Vault, External Secrets Operator e Rotation

> **Documento di riferimento:** `15-secrets-management.md`
> **Dominio:** Gestione Piattaforme — Sicurezza e Compliance
> **Ambito:** HashiCorp Vault dev mode, KV secrets engine, dynamic secrets PostgreSQL, cert-manager, External Secrets Operator su Kubernetes, secret rotation automatica, audit logging Vault, SOPS per GitOps
> **Durata lab:** 7-8 ore
> **Livello:** Avanzato — richiede Docker, K3s, helm, kubectl
> **Prerequisiti:** Docker Engine 29.x, K3s cluster locale, helm 3.x, kubectl, Python 3.10+
> **Ambiente:** Vault 1.18 in dev mode via Docker, cert-manager su K3s, External Secrets Operator, PostgreSQL per dynamic secrets demo

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI SECRETS LAB ===
echo "=== PREREQUISITI ==="

docker --version && echo "[OK] Docker" || echo "[FAIL] Docker richiesto"
kubectl version --client --short 2>/dev/null && echo "[OK] kubectl" || echo "[FAIL] kubectl richiesto"
helm version --short 2>/dev/null && echo "[OK] helm" || echo "[FAIL] helm richiesto"

# Vault CLI (opzionale — usiamo anche API HTTP)
command -v vault &>/dev/null && echo "[OK] vault CLI" || \
  echo "[INFO] Vault CLI opzionale — installa da https://developer.hashicorp.com/vault/downloads"

mkdir -p ~/secrets-lab/{vault,certs,eso,sops,scripts,manifests}
cd ~/secrets-lab

echo "[OK] Directory lab: ~/secrets-lab"
```

### Architettura Secrets Management

```
┌──────────────────────────────────────────────────────────────────────────┐
│               SECRETS MANAGEMENT — ARCHITETTURA                          │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  VAULT 1.18 (secrets store centrale)                           │    │
│  │  ├── KV v2: segreti statici (API keys, password)              │    │
│  │  ├── Database: dynamic secrets PostgreSQL (TTL 1h)            │    │
│  │  ├── PKI: emette certificati TLS automaticamente              │    │
│  │  └── Audit Log: ogni accesso registrato                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                          ↓ API HTTP                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  External Secrets Operator (K8s controller)                    │    │
│  │  ExternalSecret → legge da Vault → crea Kubernetes Secret     │    │
│  │  SecretStore: connessione autenticata a Vault                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                          ↓                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  APPLICAZIONI K8s                                               │    │
│  │  Pod monta Secret come env var o volume                        │    │
│  │  Secret ruotato automaticamente (refreshInterval)              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Perché i Segreti Sono il Problema Più Difficile

> I segreti sono il punto di fallimento più comune nella sicurezza moderna.
> Non perché la crittografia sia difficile — è banale da usare.
> Ma perché i segreti devono essere distribuiti a chi ne ha bisogno
> senza essere esposti a chi non ne ha bisogno.
> E devono essere cambiati regolarmente senza interrompere il servizio.
> E devono essere revocati immediatamente se compromessi.
> E devono essere tracciati per sapere chi li ha usati.
> Tutto questo, in automatico, 24/7, in produzione.
> HashiCorp Vault risolve esattamente questo problema.

---

### Concetto A1: Tipi di Segreti e Rotation Policy

```
CLASSIFICAZIONE SEGRETI:

TIPO 1 — SEGRETI STATICI (valore fisso, cambiano raramente):
  Esempi: API key esterne, token OAuth, chiavi webhook
  Rotation: ogni 90-180 giorni (o immediatamente se compromessi)
  Storage: Vault KV v2 (tiene storico versioni)
  Rischio: se leaked, validi fino alla rotation manuale

TIPO 2 — CREDENZIALI DATABASE DINAMICHE (generate on-demand):
  Esempi: username/password PostgreSQL, MySQL
  Rotation: TTL configurabile (es. 1 ora, scade e non è rinnovabile)
  Storage: Vault Database Engine (genera on-demand)
  Vantaggi: nessuna credenziale "sempre valida" — zero-standing-privileges
  Come funziona: app chiede credenziali → Vault le crea su DB → le ritorna
                 → scadono dopo TTL → Vault le revoca su DB

TIPO 3 — CERTIFICATI TLS (coppie chiave/certificato):
  Esempi: TLS per internal services, mTLS tra microservizi
  Rotation: ogni 90 giorni (Let's Encrypt impone massimo)
  Storage: Vault PKI engine OPPURE cert-manager
  Automazione: cert-manager rinnova automaticamente prima della scadenza

ROTATION POLICY RACCOMANDATA:
  DB passwords:        TTL 1-8 ore (dynamic secrets)
  API keys:            90 giorni
  TLS certificates:    90 giorni (rinnovo automatico a -30gg)
  KMS keys:            1 anno
  Vault unseal keys:   Mai (ma distribuirli con Shamir secret sharing)

REGOLA AUREA:
  "Un segreto che non ruota è un segreto che, se leaked,
   rimarrà compromesso per sempre."
```

---

### Concetto A2: Vault Token Hierarchy

```
VAULT AUTHENTICATION HIERARCHY:

Root Token (SOLO durante init, poi revocato):
  └── Policy: all → tutto accesso
  
Policy: admin (per operazioni vault):
  └── Può: creare policy, abilitare auth methods, gestire mount
  
Policy: app-read-secrets (per le applicazioni):
  └── Può: leggere path secret/data/myapp/*
  └── Non può: scrivere, eliminare, gestire policy
  
Auth Methods (come gli utenti si autenticano a Vault):
  ├── token: token diretto (per testing)
  ├── kubernetes: K8s ServiceAccount JWT → Vault token
  ├── approle: role_id + secret_id (per CI/CD)
  └── aws/gcp: identity cloud nativa

FLUSSO KUBERNETES AUTH:
  1. Pod usa ServiceAccount token (montato in /var/run/secrets/...)
  2. ESO invia il token a Vault /auth/kubernetes/login
  3. Vault verifica il token con K8s API server
  4. Vault ritorna un token con TTL e policy
  5. ESO usa il token per leggere i segreti
  6. ESO crea/aggiorna Kubernetes Secret
```

---

## PART B: HASHICORP VAULT — SETUP E CONFIGURAZIONE

### Esercizio B1: Avviare Vault in Dev Mode

```bash
cd ~/secrets-lab

# Vault dev mode: ottimo per lab, NON per produzione
# Dev mode: in-memory storage, unseal automatico, root token noto
docker network create secrets-net

docker run -d \
  --name vault-dev \
  --network secrets-net \
  -p 8200:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=dev-root-token-lab \
  -e VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200 \
  -e VAULT_LOG_LEVEL=info \
  hashicorp/vault:1.18.0

sleep 5

export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-root-token-lab"

# Verificare Vault è attivo
curl -s "${VAULT_ADDR}/v1/sys/health" | python3 -m json.tool | head -10

echo ""
echo "[OK] Vault 1.18 dev mode avviato"
echo "[INFO] UI: http://localhost:8200 (token: dev-root-token-lab)"

# Usando vault CLI se disponibile
if command -v vault &>/dev/null; then
  vault status
fi
```

---

### Esercizio B2: KV Secrets Engine

```bash
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-root-token-lab"

echo "=== KV v2 SECRETS ENGINE ==="

# KV v2 è già abilitato in dev mode su path secret/
# Verificare
curl -s \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/sys/mounts" | python3 -c "
import json, sys
mounts = json.load(sys.stdin)
for path, info in mounts.items():
    if 'kv' in info.get('type', ''):
        print(f'[OK] KV mount: {path} (versione={info.get(\"options\",{}).get(\"version\",\"?\")})')
"

# Scrivere segreti
echo ""
echo "--- Scrittura segreti ---"

# Segreto 1: credenziali database produzione
curl -s -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "DB_HOST": "prod-db.internal",
      "DB_PORT": "5432",
      "DB_NAME": "orders",
      "DB_USERNAME": "app_orders",
      "DB_PASSWORD": "secure-pass-DO-NOT-LOG"
    },
    "metadata": {
      "description": "Credenziali PostgreSQL produzione — GDPR: PII",
      "owner": "platform-team"
    }
  }' \
  "${VAULT_ADDR}/v1/secret/data/myapp/database" | python3 -m json.tool

# Segreto 2: API keys esterne
curl -s -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "STRIPE_KEY": "sk_live_fake_key_for_lab_only",
      "SENDGRID_KEY": "SG.fake_key_for_lab_only",
      "SLACK_WEBHOOK": "https://hooks.slack.com/services/FAKE/WEBHOOK"
    }
  }' \
  "${VAULT_ADDR}/v1/secret/data/myapp/external-apis"

echo ""
echo "--- Lettura segreto ---"
curl -s \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/secret/data/myapp/database" | python3 -c "
import json, sys
resp = json.load(sys.stdin)
data = resp.get('data', {}).get('data', {})
metadata = resp.get('data', {}).get('metadata', {})
print(f'Versione: {metadata.get(\"version\")}')
print(f'Creato: {metadata.get(\"created_time\")}')
print('Chiavi disponibili:', list(data.keys()))
# Non stampare i valori — mai!
"

echo ""
echo "--- Versioning KV v2 ---"
# Aggiornare il segreto (crea nuova versione, preserva la vecchia)
curl -s -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"data": {"DB_HOST": "prod-db.internal", "DB_PORT": "5432", "DB_NAME": "orders", "DB_USERNAME": "app_orders", "DB_PASSWORD": "new-secure-pass-after-rotation"}}' \
  "${VAULT_ADDR}/v1/secret/data/myapp/database" > /dev/null

# Vedere la versione precedente
echo "Versione 1 (prima della rotation):"
curl -s \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/secret/data/myapp/database?version=1" | python3 -c "
import json, sys
resp = json.load(sys.stdin)
meta = resp.get('data', {}).get('metadata', {})
print(f'  Versione: {meta.get(\"version\")}')
print(f'  Distrutta: {meta.get(\"destroyed\")}')
print(f'  Eliminata: {meta.get(\"deletion_time\", \"no\")}')
"

echo "Versione corrente (dopo rotation):"
curl -s \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/secret/data/myapp/database" | python3 -c "
import json, sys
resp = json.load(sys.stdin)
meta = resp.get('data', {}).get('metadata', {})
print(f'  Versione: {meta.get(\"version\")} (aggiornata)')
"
```

---

### Esercizio B3: Dynamic Secrets PostgreSQL

```bash
# Avviare PostgreSQL per demo dynamic secrets
docker run -d \
  --name postgres-demo \
  --network secrets-net \
  -e POSTGRES_USER=vault_admin \
  -e POSTGRES_PASSWORD=vault-admin-password \
  -e POSTGRES_DB=orders \
  postgres:17-alpine

sleep 5

# Creare un ruolo di esempio nel DB
docker exec postgres-demo psql \
  -U vault_admin -d orders \
  -c "CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, created_at TIMESTAMP DEFAULT NOW());"

echo "[OK] PostgreSQL pronto"

export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-root-token-lab"

echo ""
echo "=== VAULT DYNAMIC SECRETS — POSTGRESQL ==="

# 1. Abilitare il database secrets engine
curl -s -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"type": "database"}' \
  "${VAULT_ADDR}/v1/sys/mounts/database"

# 2. Configurare la connessione al DB
curl -s -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_name": "postgresql-database-plugin",
    "allowed_roles": ["app-role"],
    "connection_url": "postgresql://{{username}}:{{password}}@postgres-demo:5432/orders?sslmode=disable",
    "username": "vault_admin",
    "password": "vault-admin-password"
  }' \
  "${VAULT_ADDR}/v1/database/config/orders-db" | python3 -m json.tool

# 3. Creare un ruolo: definisce le credenziali che Vault genera dinamicamente
curl -s -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "db_name": "orders-db",
    "creation_statements": [
      "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '\''{{password}}'\'' VALID UNTIL '\''{{expiration}}'\''",
      "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO \"{{name}}\""
    ],
    "revocation_statements": [
      "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"",
      "DROP ROLE IF EXISTS \"{{name}}\""
    ],
    "default_ttl": "1h",
    "max_ttl": "4h"
  }' \
  "${VAULT_ADDR}/v1/database/roles/app-role"

echo ""
echo "--- Generare credenziali dinamiche ---"

# 4. Richiedere credenziali (simula ciò che fa l'applicazione all'avvio)
echo "Richiesta 1 (simula avvio istanza A):"
CREDS_1=$(curl -s \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/database/creds/app-role")

USERNAME=$(echo "$CREDS_1" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data']['username'])")
echo "  Username: $USERNAME"
echo "  Lease ID: $(echo "$CREDS_1" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('lease_id','?'))")"
echo "  TTL: 1 ora"

echo ""
echo "Richiesta 2 (simula avvio istanza B — DIVERSA credenziale):"
CREDS_2=$(curl -s \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/database/creds/app-role")
USERNAME2=$(echo "$CREDS_2" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data']['username'])")
echo "  Username: $USERNAME2"

echo ""
echo "[INFO] Vault ha creato 2 utenti DB DISTINTI con TTL 1h"
echo "[INFO] Dopo 1h scadono automaticamente — zero standing privileges!"

# Verificare utenti creati nel DB
docker exec postgres-demo psql \
  -U vault_admin -d orders \
  -c "\du" 2>/dev/null | grep -v "^$"
```

---

## PART C: POLICY E AUTH

### Esercizio C1: Policy Vault con Least Privilege

```bash
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-root-token-lab"

echo "=== VAULT POLICY — LEAST PRIVILEGE ==="

# Policy per l'applicazione: solo lettura del proprio path
cat > vault/policy-app-myapp.hcl << 'EOF'
# Policy: app-myapp
# Applicabile a: istanze dell'applicazione myapp
# Permessi: solo lettura del proprio path KV, richiesta dynamic creds

path "secret/data/myapp/*" {
  capabilities = ["read"]
  # No list, no write, no delete
}

path "secret/metadata/myapp/*" {
  capabilities = ["read", "list"]
  # Per verificare versioni disponibili
}

path "database/creds/app-role" {
  capabilities = ["read"]
  # Richiesta dynamic credentials PostgreSQL
}

# Rinnovare il proprio token (necessario per token renewal)
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Revocare il proprio token (logout pulito)
path "auth/token/revoke-self" {
  capabilities = ["update"]
}
EOF

# Caricare la policy in Vault
curl -s -X PUT \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"policy\": $(cat vault/policy-app-myapp.hcl | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" \
  "${VAULT_ADDR}/v1/sys/policies/acl/app-myapp"

echo "[OK] Policy app-myapp creata"

# Policy per il team platform (admin)
cat > vault/policy-platform-admin.hcl << 'EOF'
# Policy: platform-admin
# Applicabile a: team platform
# Permessi: gestione completa dei segreti, NO gestione Vault internals

path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "database/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "sys/policies/acl/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# NO accesso a: sys/unseal, sys/init, auth/token/* di altri utenti
EOF

curl -s -X PUT \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"policy\": $(cat vault/policy-platform-admin.hcl | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" \
  "${VAULT_ADDR}/v1/sys/policies/acl/platform-admin"

echo "[OK] Policy platform-admin creata"

# Creare token con policy limitata (per l'applicazione)
APP_TOKEN=$(curl -s -X POST \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "policies": ["app-myapp"],
    "ttl": "24h",
    "renewable": true,
    "display_name": "myapp-instance-1"
  }' \
  "${VAULT_ADDR}/v1/auth/token/create" | python3 -c "
import json, sys
resp = json.load(sys.stdin)
print(resp['auth']['client_token'])
")

echo "[OK] Token app creato (24h, rinnovabile)"

# Verificare che il token possa leggere il proprio path
echo ""
echo "--- Test: app token legge secret propri ---"
curl -s \
  -H "X-Vault-Token: ${APP_TOKEN}" \
  "${VAULT_ADDR}/v1/secret/data/myapp/database" | python3 -c "
import json, sys
resp = json.load(sys.stdin)
if 'data' in resp:
    print('[OK] Lettura riuscita')
else:
    print('[FAIL]', resp.get('errors', ['?']))
"

# Verificare che NON possa leggere altri path
echo "--- Test: app token NON legge altri path ---"
curl -s \
  -H "X-Vault-Token: ${APP_TOKEN}" \
  "${VAULT_ADDR}/v1/secret/data/other-app/credentials" | python3 -c "
import json, sys
resp = json.load(sys.stdin)
errors = resp.get('errors', [])
if errors:
    print('[OK] Accesso negato correttamente:', errors[0])
else:
    print('[FAIL] Ha avuto accesso a path non autorizzato!')
"
```

---

## PART D: EXTERNAL SECRETS OPERATOR

### Esercizio D1: ESO su Kubernetes

```bash
cd ~/secrets-lab

echo "=== EXTERNAL SECRETS OPERATOR (ESO) ==="

# ESO è un controller K8s che legge segreti da Vault/AWS/GCP/Azure
# e li crea automaticamente come Kubernetes Secret

helm repo add external-secrets https://charts.external-secrets.io --force-update
helm repo update

helm upgrade --install external-secrets \
  external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace \
  --set installCRDs=true \
  --wait \
  --timeout 120s

kubectl -n external-secrets get pods

echo "[OK] External Secrets Operator installato"

# SecretStore: definisce come ESO si connette a Vault
# In questo lab Vault gira su Docker — usiamo l'IP del Docker bridge
VAULT_IP=$(docker inspect vault-dev --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "172.17.0.2")

cat > eso/cluster-secret-store.yaml << EOF
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
  annotations:
    description: >
      Connessione a HashiCorp Vault per External Secrets Operator.
      In produzione: usare Kubernetes auth method (ServiceAccount JWT).
      In lab: usare token diretto (dev mode).
spec:
  provider:
    vault:
      server: "http://${VAULT_IP}:8200"
      path: "secret"    # path del KV mount
      version: "v2"     # KV v2
      auth:
        tokenSecretRef:
          name: vault-token
          namespace: external-secrets
          key: token
EOF

# Creare il secret con il token Vault (in produzione: Kubernetes auth method)
kubectl -n external-secrets create secret generic vault-token \
  --from-literal=token=dev-root-token-lab \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f eso/cluster-secret-store.yaml

# Verificare che il ClusterSecretStore sia valid
sleep 5
kubectl get clustersecretstores 2>/dev/null
```

---

### Esercizio D2: ExternalSecret

```bash
# ExternalSecret: dice a ESO cosa leggere da Vault e come creare il K8s Secret
cat > eso/external-secret-database.yaml << 'EOF'
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: myapp-database-creds
  namespace: default
  annotations:
    description: >
      Sincronizza le credenziali PostgreSQL da Vault al namespace default.
      Il Secret K8s viene aggiornato ogni 5 minuti se Vault cambia.
spec:
  refreshInterval: "5m"   # ricontrolla Vault ogni 5 minuti
  
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  
  target:
    name: myapp-database-secret    # nome del K8s Secret creato
    creationPolicy: Owner           # ESO è il proprietario, elimina se ExternalSecret è eliminato
    
    # Template: trasforma i dati Vault nel formato atteso dall'app
    template:
      type: Opaque
      data:
        DATABASE_URL: "postgresql://{{ .DB_USERNAME }}:{{ .DB_PASSWORD }}@{{ .DB_HOST }}:{{ .DB_PORT }}/{{ .DB_NAME }}"
        DB_HOST: "{{ .DB_HOST }}"
        DB_PORT: "{{ .DB_PORT }}"
  
  data:
    - secretKey: DB_HOST
      remoteRef:
        key: myapp/database    # path Vault: secret/data/myapp/database
        property: DB_HOST
    
    - secretKey: DB_PORT
      remoteRef:
        key: myapp/database
        property: DB_PORT
    
    - secretKey: DB_USERNAME
      remoteRef:
        key: myapp/database
        property: DB_USERNAME
    
    - secretKey: DB_PASSWORD
      remoteRef:
        key: myapp/database
        property: DB_PASSWORD
    
    - secretKey: DB_NAME
      remoteRef:
        key: myapp/database
        property: DB_NAME
EOF

kubectl apply -f eso/external-secret-database.yaml

echo "Attendo sincronizzazione (10 secondi)..."
sleep 10

# Verificare che il Secret sia stato creato
kubectl get secret myapp-database-secret -o yaml | head -30
echo ""

# Verificare le chiavi (senza mostrare i valori)
kubectl get secret myapp-database-secret \
  -o jsonpath='{.data}' | python3 -c "
import json, sys, base64
data = json.load(sys.stdin)
print('Chiavi nel Secret K8s:')
for key in data.keys():
    value = base64.b64decode(data[key]).decode()
    masked = value[:3] + '***' + value[-3:] if len(value) > 6 else '***'
    print(f'  {key}: {masked}')
"

# Verificare status ExternalSecret
kubectl get externalsecrets
```

---

## PART E: CERT-MANAGER E PKI

### Esercizio E1: cert-manager per Certificati TLS Automatici

```bash
cd ~/secrets-lab

echo "=== CERT-MANAGER — CERTIFICATI TLS AUTOMATICI ==="

helm repo add jetstack https://charts.jetstack.io --force-update
helm repo update

helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set crds.enabled=true \
  --wait \
  --timeout 120s

kubectl -n cert-manager get pods

echo "[OK] cert-manager installato"

# === ISSUER: autorità di certificazione locale per il lab ===
cat > certs/self-signed-issuer.yaml << 'EOF'
# ClusterIssuer "self-signed": crea certificati auto-firmati
# Per produzione: usare Let's Encrypt o Vault PKI
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-issuer
spec:
  selfSigned: {}

---
# CA certificate (certificato root della nostra CA interna)
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: lab-ca
  namespace: cert-manager
spec:
  isCA: true
  commonName: "Lab Internal CA"
  subject:
    organizations: ["Lab Corp"]
    countries: ["IT"]
  secretName: lab-ca-secret
  privateKey:
    algorithm: ECDSA
    size: 256
  issuerRef:
    name: selfsigned-issuer
    kind: ClusterIssuer
    group: cert-manager.io
  duration: 8760h   # 1 anno
  renewBefore: 360h # rinnova 15 giorni prima

---
# ClusterIssuer che usa la nostra CA per firmare certificati
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: lab-ca-issuer
spec:
  ca:
    secretName: lab-ca-secret
EOF

kubectl apply -f certs/self-signed-issuer.yaml

sleep 5

# Verificare che la CA sia pronta
kubectl -n cert-manager get certificate lab-ca

echo ""
echo "--- Richiedere un certificato per myapp.lab.local ---"

cat > certs/myapp-certificate.yaml << 'EOF'
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: myapp-tls
  namespace: default
  annotations:
    description: >
      Certificato TLS per myapp.lab.local.
      cert-manager lo rinnova automaticamente 30 giorni prima della scadenza.
      Rinnovato: nessuna interruzione del servizio.
spec:
  secretName: myapp-tls-secret    # K8s Secret con cert + key
  commonName: myapp.lab.local
  dnsNames:
    - myapp.lab.local
    - myapp.default.svc.cluster.local
  ipAddresses:
    - 127.0.0.1
  
  duration: 2160h    # 90 giorni (raccomandato per mTLS interni)
  renewBefore: 720h  # rinnova 30 giorni prima (= a 60 giorni dalla creazione)
  
  privateKey:
    algorithm: ECDSA
    size: 256
    rotationPolicy: Always  # ruota la chiave privata ad ogni rinnovo
  
  issuerRef:
    name: lab-ca-issuer
    kind: ClusterIssuer
    group: cert-manager.io
EOF

kubectl apply -f certs/myapp-certificate.yaml

echo "Attendo emissione certificato..."
kubectl wait --for=condition=Ready certificate/myapp-tls --timeout=60s

echo ""
echo "[OK] Certificato emesso"
kubectl get certificate myapp-tls

# Vedere info certificato (senza private key)
kubectl get secret myapp-tls-secret -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -text 2>/dev/null | grep -E "(Subject|Validity|DNS)" | head -10
```

---

## PART F: AUDIT LOG VAULT

### Esercizio F1: Configurare Audit Log

```bash
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-root-token-lab"

echo "=== VAULT AUDIT LOG ==="

# Vault può scrivere audit log su file, syslog o socket
# L'audit log registra OGNI operazione con: timestamp, utente, path, risposta (senza secret values)

# Abilitare audit log su file
curl -s -X PUT \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "file",
    "description": "Audit log principale",
    "options": {
      "file_path": "/vault/logs/audit.log",
      "mode": "0640",
      "format": "json"
    }
  }' \
  "${VAULT_ADDR}/v1/sys/audit/file"

echo "[OK] Audit log abilitato"

# Eseguire alcune operazioni per generare audit log
curl -s \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/secret/data/myapp/database" > /dev/null

curl -s \
  -H "X-Vault-Token: ${VAULT_TOKEN}" \
  "${VAULT_ADDR}/v1/database/creds/app-role" > /dev/null

echo ""
echo "=== ANALISI AUDIT LOG ==="
cat > scripts/analyze-vault-audit.py << 'PYTHON'
"""
Analizzatore Vault Audit Log.
Input: file JSONL generato da Vault audit device.
Output: report accessi, anomalie, statistiche.
"""
import json
import sys
from collections import defaultdict
from datetime import datetime

def analyze_vault_log(log_content: list) -> dict:
    """Analizza le entry dell'audit log Vault."""
    stats = {
        "total": 0,
        "by_path": defaultdict(int),
        "by_operation": defaultdict(int),
        "by_auth": defaultdict(int),
        "errors": [],
        "secret_reads": [],
    }
    
    for entry in log_content:
        if not isinstance(entry, dict):
            continue
        
        stats["total"] += 1
        
        # Path acceduto
        path = entry.get("request", {}).get("path", "?")
        stats["by_path"][path] += 1
        
        # Operazione
        op = entry.get("request", {}).get("operation", "?")
        stats["by_operation"][op] += 1
        
        # Auth entity
        auth = entry.get("auth", {})
        display_name = auth.get("display_name", "anonymous")
        stats["by_auth"][display_name] += 1
        
        # Errori
        resp = entry.get("response", {})
        if resp.get("error"):
            stats["errors"].append({
                "time": entry.get("time", ""),
                "path": path,
                "error": resp["error"],
                "auth": display_name
            })
        
        # Letture segreti (solo path KV)
        if "secret/data/" in path and op == "read":
            stats["secret_reads"].append({
                "time": entry.get("time", ""),
                "path": path,
                "auth": display_name
            })
    
    return stats


def print_audit_report(stats: dict):
    """Stampa report audit leggibile."""
    print("=" * 60)
    print("VAULT AUDIT REPORT")
    print(f"Generato: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)
    
    print(f"\nEventi totali: {stats['total']}")
    
    print("\n--- TOP PATH ACCEDUTI ---")
    for path, count in sorted(stats["by_path"].items(), key=lambda x: -x[1])[:10]:
        print(f"  {path}: {count} volte")
    
    print("\n--- OPERAZIONI ---")
    for op, count in sorted(stats["by_operation"].items(), key=lambda x: -x[1]):
        print(f"  {op}: {count}")
    
    print("\n--- CLIENT AUTENTICATI ---")
    for auth, count in sorted(stats["by_auth"].items(), key=lambda x: -x[1]):
        print(f"  {auth}: {count} operazioni")
    
    if stats["errors"]:
        print(f"\n--- ERRORI ({len(stats['errors'])}) ---")
        for err in stats["errors"][:10]:
            print(f"  [{err['time'][:19]}] {err['auth']}: {err['error'][:60]}")
    
    if stats["secret_reads"]:
        print(f"\n--- LETTURA SEGRETI ({len(stats['secret_reads'])}) ---")
        for read in stats["secret_reads"][:10]:
            print(f"  [{read['time'][:19]}] {read['auth']} → {read['path']}")


# Simulare parsing log (in lab, i log sono nel container)
print("[INFO] Vault audit log path nel container: /vault/logs/audit.log")
print("[INFO] Comando per leggere: docker exec vault-dev cat /vault/logs/audit.log")
print("[INFO] Parsing automatico:")

# Simulare alcune entries per demo
demo_entries = [
    {
        "time": "2026-01-15T10:00:00Z",
        "type": "request",
        "auth": {"display_name": "root"},
        "request": {"path": "secret/data/myapp/database", "operation": "read"},
        "response": {}
    },
    {
        "time": "2026-01-15T10:01:00Z",
        "type": "request",
        "auth": {"display_name": "myapp-instance-1"},
        "request": {"path": "secret/data/myapp/database", "operation": "read"},
        "response": {}
    },
    {
        "time": "2026-01-15T10:02:00Z",
        "type": "request",
        "auth": {"display_name": "unknown"},
        "request": {"path": "secret/data/other-app/credentials", "operation": "read"},
        "response": {"error": "permission denied"}
    },
]

stats = analyze_vault_log(demo_entries)
print_audit_report(stats)
PYTHON

python3 scripts/analyze-vault-audit.py
```

---

## PART G: ROTATION AUTOMATICA

### Esercizio G1: Script di Rotation

```bash
cd ~/secrets-lab

cat > scripts/rotate-secret.py << 'PYTHON'
"""
Rotation automatica segreti Vault.
Esegue: aggiorna secret in Vault → verifica → notifica (opzionale).
"""
import json
import secrets
import string
import urllib.request
import urllib.error

VAULT_ADDR = "http://localhost:8200"
VAULT_TOKEN = "dev-root-token-lab"


def vault_api(method: str, path: str, data: dict | None = None) -> dict:
    """Chiama l'API Vault."""
    url = f"{VAULT_ADDR}/v1/{path}"
    body = json.dumps(data).encode("utf-8") if data else None
    
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "X-Vault-Token": VAULT_TOKEN,
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": str(e)}


def generate_password(length: int = 32) -> str:
    """Genera una password sicura."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    safe = alphabet.replace('"', '').replace("'", "").replace("\\", "")
    return ''.join(secrets.choice(safe) for _ in range(length))


def rotate_database_password(secret_path: str, db_field: str = "DB_PASSWORD"):
    """
    Ruota la password database in Vault.
    NOTA: In produzione, sincronizzare anche con il DB reale.
    """
    print(f"\nRotazione: {secret_path}")
    
    # 1. Leggere la versione corrente
    current = vault_api("GET", f"secret/data/{secret_path}")
    if "error" in current:
        print(f"  [FAIL] Impossibile leggere: {current['error']}")
        return False
    
    current_data = current.get("data", {}).get("data", {})
    current_version = current.get("data", {}).get("metadata", {}).get("version", 0)
    print(f"  Versione corrente: {current_version}")
    
    # 2. Generare nuova password
    new_password = generate_password(32)
    updated_data = {**current_data, db_field: new_password}
    
    # 3. Scrivere nuova versione
    result = vault_api("POST", f"secret/data/{secret_path}", {"data": updated_data})
    
    if "error" in result:
        print(f"  [FAIL] Rotazione fallita: {result['error']}")
        return False
    
    new_version = result.get("data", {}).get("version", "?")
    print(f"  [OK] Rotazione completata — versione {current_version} → {new_version}")
    print(f"  Vecchia versione preservata per rollback (massimo: 5 versioni)")
    
    # 4. Verificare che la nuova versione sia leggibile
    verify = vault_api("GET", f"secret/data/{secret_path}")
    if verify.get("data", {}).get("metadata", {}).get("version") == new_version:
        print(f"  [OK] Verifica: nuova versione leggibile correttamente")
        return True
    else:
        print(f"  [WARN] Verifica: discrepanza versione")
        return False


def check_secret_age(secret_path: str, max_age_days: int = 90):
    """Controlla se un segreto ha superato la data di rotation raccomandata."""
    from datetime import datetime, timezone
    
    result = vault_api("GET", f"secret/data/{secret_path}")
    if "error" in result:
        return
    
    created_str = result.get("data", {}).get("metadata", {}).get("created_time", "")
    if not created_str:
        return
    
    created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - created).days
    
    print(f"\nControllo età segreto: {secret_path}")
    print(f"  Ultima modifica: {created_str[:10]} ({age} giorni fa)")
    
    if age >= max_age_days:
        print(f"  [WARN] Segreto ha più di {max_age_days} giorni — rotation raccomandata!")
    elif age >= max_age_days * 0.8:
        print(f"  [INFO] Segreto si avvicina alla scadenza ({max_age_days - age} giorni rimanenti)")
    else:
        print(f"  [OK] Segreto recente ({max_age_days - age} giorni rimanenti)")


if __name__ == "__main__":
    print("=== SECRET ROTATION TOOL ===")
    
    # Controllo età segreti
    check_secret_age("myapp/database", max_age_days=90)
    check_secret_age("myapp/external-apis", max_age_days=180)
    
    # Rotazione
    rotate_database_password("myapp/database", "DB_PASSWORD")
PYTHON

python3 scripts/rotate-secret.py

echo ""
echo "[OK] Script rotation completato"
echo "     Produzione: eseguire come CronJob K8s ogni 90 giorni"
```

---

## Conclusioni e Prossimi Passi

```
SECRETS MANAGEMENT — RIEPILOGO:

VAULT FONDAMENTI:
  ✓ Dev mode: ideale per lab, mai per produzione
  ✓ Produzione: Integrated Storage (Raft), HA con 3+ nodi
  ✓ Unseal: auto-unseal con AWS KMS / Azure Key Vault / GCP KMS
  ✓ Audit log: abilitare SEMPRE (GDPR accountability)

KV v2:
  ✓ Versioning: ogni modifica crea nuova versione (rollback possibile)
  ✓ Soft delete: versione marcata come deleted, recuperabile
  ✓ max-versions: configurare per controllo retention
  ✓ Metadata: campo custom per owner, classification, retention

DYNAMIC SECRETS:
  ✓ PostgreSQL: Vault crea user dedicato con TTL → revoca automatica
  ✓ Zero standing privileges: nessuna credenziale "sempre valida"
  ✓ Ogni istanza ha le proprie credenziali → tracciabilità completa
  ✓ Alternativa cloud: AWS IAM Roles, GCP Service Account Key rotation

EXTERNAL SECRETS OPERATOR:
  ✓ ClusterSecretStore: connessione al backend (Vault, AWS, GCP, Azure)
  ✓ ExternalSecret: mapping Vault path → K8s Secret key
  ✓ refreshInterval: aggiornamento automatico (es. "5m")
  ✓ template: trasformare i dati Vault nel formato atteso

CERT-MANAGER:
  ✓ Issuer: self-signed (lab), Let's Encrypt (HTTP), Vault PKI, CA
  ✓ Certificate: richiede cert, salva in Secret, rinnova automaticamente
  ✓ renewBefore: rinnova N ore prima della scadenza
  ✓ rotationPolicy: Always (ruota anche la chiave privata, più sicuro)

ROTATION:
  ✓ DB passwords: TTL breve via dynamic secrets (1-8 ore)
  ✓ API keys statiche: rotation ogni 90-180 giorni (CronJob)
  ✓ TLS certs: rinnovo automatico cert-manager (renewBefore 30gg)
  ✓ Audit: ogni accesso e rotation registrati in Vault audit log

ANTI-PATTERN DA EVITARE:
  ✗ Segreti in variabili d'ambiente del Deployment (visibili in kubectl describe)
  ✗ Segreti in ConfigMap (non cifrati, base64 ≠ cifratura)
  ✗ Segreti hardcoded nel codice (gitleaks li trova)
  ✗ Segreti in S3/GCS bucket senza encryption + versioning
  ✗ Token Vault senza TTL (token eterni = blast radius enorme)

CITAZIONE:
  "Il segreto migliore è quello che non esiste abbastanza a lungo
   da essere rubato, e che non lascia traccia di essere mai stato lì."
```

**Prossimi tutorial:**
- `tutorial_plat16_api_gateway_lab.md` — Kong Gateway DB-less, rate limiting, JWT
- `tutorial_plat17_storage_distribuito_lab.md` — MinIO, Longhorn, CSI driver

```bash
# Pulizia lab
docker rm -f vault-dev postgres-demo 2>/dev/null
docker network rm secrets-net 2>/dev/null
kubectl delete -f eso/ --ignore-not-found=true 2>/dev/null
kubectl delete -f certs/ --ignore-not-found=true 2>/dev/null
helm uninstall external-secrets -n external-secrets 2>/dev/null
helm uninstall cert-manager -n cert-manager 2>/dev/null
rm -rf ~/secrets-lab

echo "[OK] Lab Secrets Management completato"
```

---

> **Nota versioni:** HashiCorp Vault 1.18.x (ottobre 2024 — BSL license),
> OpenBao 2.0.x (fork community FOSS da Vault 1.14 — alternativa open source).
> External Secrets Operator 0.10.x (Helm chart external-secrets 0.10.x).
> cert-manager 1.16.x (Helm chart jetstack/cert-manager 1.16.x).
> Vault BSL (Business Source License): uso produzione gratuito per istanze <10.
> OpenBao: drop-in replacement per progetti che necessitano licenza OSI-approved.
> AWS Secrets Manager: $0.40/segreto/mese + $0.05 per 10.000 chiamate API.
> HashiCorp Vault Enterprise: pricing per core, necessario per namespace multi-tenant e DR replication.
