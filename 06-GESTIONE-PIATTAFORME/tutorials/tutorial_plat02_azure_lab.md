# Tutorial: Microsoft Azure — Fondamenti, Governance e AKS — Lab Pratico

> **Documento di riferimento:** `02-cloud-azure.md`
> **Dominio:** Gestione Piattaforme — Cloud Provider Azure
> **Ambito:** Architettura globale Azure, Resource Group e governance, Entra ID e RBAC, VNet hub-and-spoke, Azure Storage con Azurite (emulatore locale), Managed Identity, AKS (Azure Kubernetes Service), Bicep IaC, Azure Monitor
> **Durata lab:** 5-6 ore
> **Livello:** Intermedio — richiede conoscenza base di Active Directory e networking
> **Prerequisiti:** Azure CLI (az), Docker Engine 29.x, kubectl (opzionale per AKS), account Azure Free Tier (opzionale — la maggior parte del lab usa Azurite/emulatori)
> **Ambiente:** Azurite 3.x (emulatore Azure Storage), Azure CLI in dry-run/offline mode per concetti, note specifiche dove serve un account Azure reale

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI AZURE LAB ===
echo "=== CHECK PREREQUISITI ==="

# Azure CLI
az version 2>/dev/null | python3 -m json.tool | head -5 && \
  echo "[OK] Azure CLI disponibile" || {
  echo "[FAIL] Installare Azure CLI"
  echo "  Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | bash"
  echo "  Windows: winget install Microsoft.AzureCLI"
}

# Docker (per Azurite)
docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Docker richiesto per Azurite"

# Node.js (opzionale, per Bicep locale)
node --version 2>/dev/null && echo "[OK] Node.js disponibile" || \
  echo "[INFO] Node.js opzionale (per bicep linting offline)"

# kubectl (opzionale, per sezione AKS)
kubectl version --client 2>/dev/null | head -1 && \
  echo "[OK] kubectl disponibile" || echo "[INFO] kubectl opzionale (sezione AKS)"

echo ""
echo "=== SETUP DIRECTORY LAB ==="
mkdir -p ~/azure-lab/{bicep,scripts,storage-test}
cd ~/azure-lab

echo "[OK] Directory lab: ~/azure-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         AZURE LAB — AMBIENTE                              │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  Azurite 3.x (Docker — emulatore Storage locale)               │     │
│  │  - Blob Storage                                                 │     │
│  │  - Queue Storage                                                │     │
│  │  - Table Storage                                                │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  Azure CLI (concetti + dry-run, account reale opzionale)       │     │
│  │  - Resource Group / Management Group                            │     │
│  │  - Entra ID: Service Principal, Managed Identity               │     │
│  │  - RBAC: role assignment                                       │     │
│  │  - VNet + subnet + NSG                                         │     │
│  │  - AKS: definizioni manifesti (apply con cluster reale)        │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  Bicep IaC (sintassi e lint locale)                            │     │
│  │  - Template Resource Group + Storage + VNet                    │     │
│  └─────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
```

### Avvio Azurite

```bash
cd ~/azure-lab

# Azurite = emulatore Azure Storage ufficiale Microsoft
# Include: Blob Service (:10000), Queue Service (:10001), Table Service (:10002)
cat > compose.yaml << 'EOF'
name: "azure-lab"

services:
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite:3.32.0
    container_name: azurite
    command: azurite --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0
    ports:
      - "10000:10000"    # Blob
      - "10001:10001"    # Queue
      - "10002:10002"    # Table
    volumes:
      - ./azurite-data:/data
    restart: unless-stopped

volumes: {}
EOF

docker compose up -d azurite

echo "Attendo Azurite..."
sleep 5
curl -s http://localhost:10000/devstoreaccount1 | head -1 && \
  echo "[OK] Azurite Blob Service operativo" || echo "[WARN] Azurite in avvio..."

# Connection string per Azurite (hardcoded per sviluppo locale — NON usare in produzione)
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://localhost:10000/devstoreaccount1;QueueEndpoint=http://localhost:10001/devstoreaccount1;TableEndpoint=http://localhost:10002/devstoreaccount1;"

# Verificare connessione (az storage richiede Azure CLI)
az storage container list \
  --connection-string "$AZURE_STORAGE_CONNECTION_STRING" \
  --output table 2>/dev/null && echo "[OK] Azure CLI connesso ad Azurite" || \
  echo "[INFO] Azure CLI non disponibile — seguire istruzioni installazione sopra"
```

---

## PART A: FONDAMENTI — Come Funziona Azure

> Microsoft Azure nasce nel 2010 con una filosofia diversa da AWS: è progettata per
> le grandi aziende che usano già prodotti Microsoft. Se la tua azienda usa Windows Server,
> Active Directory, SQL Server, Office 365, il passaggio ad Azure è naturale — puoi usare
> le stesse identità, le stesse licenze, la stessa expertise. AWS è più ricco di servizi
> e leader nel mercato startup/tech; Azure domina il mercato enterprise tradizionale.
> Google Cloud eccelle nel ML e nell'analisi dati. Nessuno dei tre è "il migliore" —
> la scelta dipende dal tuo punto di partenza e dai tuoi workload.

---

### Concetto A1: Resource Group — L'Unità di Gestione Azure

> **Analogia.** In AWS, le risorse esistono in una regione e puoi taggarle, ma non
> c'è un "contenitore" obbligatorio. In Azure, OGNI risorsa deve vivere in un
> Resource Group — è come una cartella obbligatoria per ogni progetto. La cartella
> può essere eliminata con un click, portando via tutto quello che contiene. È anche
> l'unità di fatturazione, permessi RBAC, e policy. Se stai lavorando su un progetto
> di test, crei un Resource Group chiamato "test-lab", ci metti tutto, e quando hai
> finito lo elimini: zero costi residui, nessun orphan resource.

```
GERARCHIA DI GESTIONE AZURE:

Management Group (Radice)
  └── Management Group (Enterprise)
        ├── Management Group (Produzione)
        │     └── Subscription "prod-westeurope"
        │           ├── Resource Group "prod-webapp-rg"
        │           │     ├── Virtual Network
        │           │     ├── App Service Plan
        │           │     └── Azure SQL Database
        │           └── Resource Group "prod-data-rg"
        │                 ├── Storage Account
        │                 └── Azure Data Factory
        └── Management Group (Non-Produzione)
              └── Subscription "dev-team"
                    └── Resource Group "dev-lab-rg"
                          ├── Virtual Machine
                          └── Azure Container Registry

REGOLE CHIAVE:
  - Ogni risorsa → 1 Resource Group (obbligatorio)
  - Ogni RG → 1 Subscription
  - Ogni Subscription → 1 Management Group
  - I permessi RBAC si ereditano verso il basso
  - Le policy Azure si applicano a Management Group, Subscription, o RG
```

```bash
# ── Operazioni Resource Group con Azure CLI ────────────────────────────
# Nota: questi comandi richiedono az login con account Azure reale
# (o usare az login --use-device-code per ambienti senza browser)

# Login (opzionale — richiede account Azure)
# az login

# Visualizzare le subscription disponibili
# az account list --output table

# Impostare la subscription di default
# az account set --subscription "Il Tuo Nome Subscription"

# Verificare la subscription attiva
# az account show --output table

# ── SIMULAZIONE OFFLINE ───────────────────────────────────────────────
# Di seguito i comandi che eseguiresti con un account Azure reale

cat << 'AZURE_COMMANDS'
# Creare un Resource Group (Italia Nord — eu-south-1 equivalente)
az group create \
  --name "lab-platform-rg" \
  --location "italynorth" \
  --tags Environment=lab Team=platform ManagedBy=cli CostCenter=IT-Lab

# Visualizzare i RG
az group list \
  --query '[*].{Name:name,Location:location,State:properties.provisioningState}' \
  --output table

# Eliminare un RG (e TUTTE le sue risorse) con un solo comando
az group delete --name "lab-platform-rg" --yes --no-wait
AZURE_COMMANDS

echo "[INFO] Comandi mostrati in modalità riferimento (login Azure non richiesto per questo step)"
```

---

### Concetto A2: Microsoft Entra ID (ex Azure Active Directory)

> **Analogia.** Entra ID è come il portiere di un grande condominio. Conosce tutti
> gli inquilini (utenti), sa in quali appartamenti possono entrare (RBAC), e gestisce
> i cartellini dei visitatori temporanei (Guest user, Service Principal). Quando un
> servizio Azure (come una VM o una Function) ha bisogno di accedere a un altro servizio
> (come il tuo database), non gli dai una chiave permanente — gli assegni una Managed
> Identity (una chiave magnetica che Azure gestisce automaticamente e che cambia
> senza che tu debba fare nulla).

```
ENTRA ID — ENTITÀ PRINCIPALI:

USER (persona fisica):
  - Può fare login interattivo (browser, Teams, Outlook)
  - Password + MFA
  - Si autentica ad app Azure, Microsoft 365, app SAML

SERVICE PRINCIPAL (identità per applicazione):
  - Equivalente AWS: IAM User con chiavi
  - Usato da: CI/CD pipeline, app esterne
  - Autenticazione: client_id + client_secret o certificato
  - Problema: le chiavi scadono, vanno ruotate manualmente

MANAGED IDENTITY (identità gestita da Azure):
  - Equivalente AWS: EC2 Instance Profile / Lambda Role
  - Assegnata a: VM, AKS, App Service, Functions, Logic App
  - Nessuna chiave: Azure gestisce tutto internamente
  - Best practice per accessi servizi → servizi

RBAC (Role-Based Access Control):
  - Owner     = tutti i permessi + gestire accessi
  - Contributor = tutti i permessi, no gestione accessi
  - Reader    = sola lettura
  - Ruoli custom: definisci tu le azioni permesse

LIVELLI RBAC:
  Management Group → Subscription → Resource Group → Risorsa singola
  (permessi ereditati verso il basso, ma puoi bloccare l'eredità)
```

```bash
cat << 'ENTRA_COMMANDS'
# ── Entra ID — Comandi con Azure CLI ──────────────────────────────────

# Creare un Service Principal per GitHub Actions (OIDC federation — preferito)
# Nessuna chiave segreta: GitHub Actions si autentica con OIDC token
az ad sp create-for-rbac \
  --name "sp-github-cicd-lab" \
  --role Contributor \
  --scopes /subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/lab-platform-rg \
  --sdk-auth    # output in formato JSON per GitHub Secrets

# Preferibilmente: Workload Identity Federation (OIDC — senza secret)
az ad app create --display-name "wif-github-lab"
# Poi aggiungere federated credential per GitHub Actions
az ad app federated-credential create \
  --id <app-object-id> \
  --parameters '{
    "name": "github-main-branch",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:tuo-org/tuo-repo:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Assegnare ruolo a Managed Identity
az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role "Storage Blob Data Reader" \
  --scope /subscriptions/.../resourceGroups/lab-rg/providers/Microsoft.Storage/storageAccounts/myaccount

# Privileged Identity Management (PIM) — accesso just-in-time
# Un admin deve "attivare" il proprio ruolo Owner solo quando ne ha bisogno
# (per massimo 8 ore, con giustificazione) → audit trail completo
ENTRA_COMMANDS
```

---

## PART B: AZURE STORAGE CON AZURITE

### Esercizio B1: Blob Storage

```bash
cd ~/azure-lab/storage-test

CONN="$AZURE_STORAGE_CONNECTION_STRING"

# ── Container (equivalente S3 Bucket) ─────────────────────────────────
# Creare container con accesso privato
az storage container create \
  --name "lab-artifacts" \
  --connection-string "$CONN" \
  --public-access off

az storage container create \
  --name "lab-logs" \
  --connection-string "$CONN" \
  --public-access off

echo "[OK] Container creati"

# ── Upload file (Blob) ────────────────────────────────────────────────
echo '{"version": "1.0.0", "build": "20260716", "platform": "azure"}' > manifest.json
echo 'Applicazione v1.0.0 avviata' > app.log
cat > config.yaml << 'EOF'
environment: lab
region: italynorth
tier: standard
EOF

az storage blob upload \
  --container-name "lab-artifacts" \
  --name "releases/v1.0.0/manifest.json" \
  --file manifest.json \
  --connection-string "$CONN" \
  --content-type "application/json"

az storage blob upload \
  --container-name "lab-logs" \
  --name "2026/07/16/app.log" \
  --file app.log \
  --connection-string "$CONN" \
  --content-type "text/plain"

echo "[OK] File caricati in Blob Storage"

# ── Listare e scaricare ───────────────────────────────────────────────
az storage blob list \
  --container-name "lab-artifacts" \
  --connection-string "$CONN" \
  --query '[*].{Nome:name,Dimensione:properties.contentLength,Tipo:properties.contentType}' \
  --output table

# Download
az storage blob download \
  --container-name "lab-artifacts" \
  --name "releases/v1.0.0/manifest.json" \
  --file /tmp/downloaded-manifest.json \
  --connection-string "$CONN"

cat /tmp/downloaded-manifest.json
echo "[OK] File scaricato"

# ── SAS Token (Shared Access Signature) ──────────────────────────────
# Permesso temporaneo per accedere a un blob senza credenziali
SAS_TOKEN=$(az storage blob generate-sas \
  --container-name "lab-artifacts" \
  --name "releases/v1.0.0/manifest.json" \
  --permissions r \
  --expiry "2026-12-31T23:59:59Z" \
  --connection-string "$CONN" \
  --output tsv)

echo "[OK] SAS Token generato (scadenza 2026-12-31):"
echo "  ?$SAS_TOKEN"

# ── Soft Delete e Versioning ─────────────────────────────────────────
# In Azure reale, abilitare soft delete e versioning per il recovery:
cat << 'VERSIONING'
# In Azure reale (non supportato da Azurite):
az storage account blob-service-properties update \
  --account-name mystorageaccount \
  --enable-versioning true \
  --enable-delete-retention true \
  --delete-retention-days 30 \
  --enable-container-delete-retention true \
  --container-delete-retention-days 7
VERSIONING
```

---

## PART C: VNet E NETWORKING

> **Analogia.** Una VNet (Virtual Network) in Azure è come affittare un intero piano
> di un palazzo per la tua azienda. Puoi dividere il piano in stanze (subnet), decidere
> chi può passare tra le stanze (NSG — Network Security Group), installare una guardia
> all'ingresso principale (Azure Firewall), e creare corridoi privati tra i tuoi
> piani (VNet Peering) o verso la tua sede fisica (ExpressRoute/VPN Gateway).

---

### Esercizio C1: Progettare una VNet

```bash
cat << 'VNET_DESIGN'
═══════════════════════════════════════════════════════════════
VNET DESIGN — ARCHITETTURA HUB-AND-SPOKE (Azure best practice)
═══════════════════════════════════════════════════════════════

Hub VNet: 10.0.0.0/16
  ├── GatewaySubnet:         10.0.0.0/27   (VPN/ExpressRoute — riservata)
  ├── AzureFirewallSubnet:   10.0.1.0/26   (Azure Firewall — riservata)
  └── ManagementSubnet:      10.0.2.0/24   (Bastion, jump box)

Spoke VNet — Webapp: 10.1.0.0/16
  ├── FrontendSubnet:        10.1.1.0/24   (App Service / Load Balancer)
  ├── BackendSubnet:         10.1.2.0/24   (VM / AKS Pods)
  └── DataSubnet:            10.1.3.0/24   (Azure SQL / CosmosDB)

Spoke VNet — Data: 10.2.0.0/16
  ├── AnalyticsSubnet:       10.2.1.0/24   (Synapse Analytics)
  └── StorageSubnet:         10.2.2.0/24   (ADLS Gen2 con Private Endpoint)

VNet Peering: Hub ↔ Spoke-Webapp, Hub ↔ Spoke-Data
Traffico Hub→Spoke passa per Azure Firewall (ispezione L7)

NSG (Network Security Group) — Regole per BackendSubnet:
  INBOUND:
  - ALLOW TCP 8080 da FrontendSubnet (app → backend)
  - ALLOW TCP 443 da ManagementSubnet (admin)
  - DENY * da Internet (nessun accesso diretto)
  OUTBOUND:
  - ALLOW TCP 5432 verso DataSubnet (backend → DB)
  - ALLOW TCP 443 verso Internet (HTTPS per aggiornamenti)
  - DENY * default

═══════════════════════════════════════════════════════════════
VNET_DESIGN

# Comandi per creare la VNet (con account Azure reale)
cat << 'VNET_COMMANDS'
# Hub VNet
az network vnet create \
  --resource-group lab-platform-rg \
  --name hub-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name ManagementSubnet \
  --subnet-prefix 10.0.2.0/24 \
  --location italynorth

# Aggiungere subnet GatewaySubnet (nome riservato per VPN Gateway)
az network vnet subnet create \
  --resource-group lab-platform-rg \
  --vnet-name hub-vnet \
  --name GatewaySubnet \
  --address-prefix 10.0.0.0/27

# Spoke VNet per webapp
az network vnet create \
  --resource-group lab-platform-rg \
  --name spoke-webapp-vnet \
  --address-prefix 10.1.0.0/16 \
  --subnet-name FrontendSubnet \
  --subnet-prefix 10.1.1.0/24 \
  --location italynorth

# Aggiungere subnet backend e data
az network vnet subnet create \
  --resource-group lab-platform-rg \
  --vnet-name spoke-webapp-vnet \
  --name BackendSubnet \
  --address-prefix 10.1.2.0/24

# VNet Peering Hub ↔ Spoke
az network vnet peering create \
  --resource-group lab-platform-rg \
  --name hub-to-spoke-webapp \
  --vnet-name hub-vnet \
  --remote-vnet spoke-webapp-vnet \
  --allow-vnet-access true \
  --allow-forwarded-traffic true

# NSG per BackendSubnet
az network nsg create \
  --resource-group lab-platform-rg \
  --name backend-nsg

az network nsg rule create \
  --resource-group lab-platform-rg \
  --nsg-name backend-nsg \
  --name allow-frontend-http \
  --priority 100 \
  --protocol Tcp \
  --direction Inbound \
  --source-address-prefix 10.1.1.0/24 \
  --destination-port-range 8080 \
  --access Allow

az network nsg rule create \
  --resource-group lab-platform-rg \
  --nsg-name backend-nsg \
  --name deny-internet-inbound \
  --priority 4000 \
  --protocol '*' \
  --direction Inbound \
  --source-address-prefix Internet \
  --destination-port-range '*' \
  --access Deny

# Associare NSG alla subnet
az network vnet subnet update \
  --resource-group lab-platform-rg \
  --vnet-name spoke-webapp-vnet \
  --name BackendSubnet \
  --network-security-group backend-nsg
VNET_COMMANDS
```

---

## PART D: AKS — AZURE KUBERNETES SERVICE

> **Analogia.** AKS è come assumere una persona per gestire l'orchesta (Kubernetes).
> Tu decidi quanti musicisti vuoi, che musica suonare, e quando fare le prove.
> Azure si occupa dell'aula prove, degli strumenti, della manutenzione. Non devi
> preoccuparti dell'aggiornamento di Kubernetes (il direttore d'orchestra), né
> dei nodi control plane (li gestisce Azure), né dei backup dell'etcd.

---

### Esercizio D1: Creare un Cluster AKS (con Account Azure)

```bash
cat << 'AKS_GUIDE'
═══════════════════════════════════════════════════════════════
AKS — GUIDA CREAZIONE CLUSTER
═══════════════════════════════════════════════════════════════

# PREREQUISITI PER QUESTO STEP:
# - Account Azure con crediti (Free Tier: 200 USD per 30 giorni)
# - Subscription con permesso Microsoft.ContainerService

# ── STEP 1: Installare estensioni necessarie ──────────────────────────
az extension add --name aks-preview
az extension update --name aks-preview

# ── STEP 2: Creare cluster AKS (configurazione minima per lab) ────────
az aks create \
  --resource-group lab-platform-rg \
  --name lab-aks \
  --kubernetes-version 1.31.x \
  --node-count 2 \
  --node-vm-size Standard_B2s \     # 2 vCPU, 4GB RAM — economico
  --enable-managed-identity \        # Managed Identity invece di SP
  --network-plugin azure \           # Azure CNI (più funzionalità di kubenet)
  --network-policy azure \           # Azure Network Policy (NetworkPolicy K8s)
  --enable-addons monitoring \       # Azure Monitor per container
  --workspace-resource-id /subscriptions/.../resourceGroups/lab-platform-rg/providers/Microsoft.OperationalInsights/workspaces/lab-log-analytics \
  --enable-oidc-issuer \             # per Workload Identity
  --enable-workload-identity \       # per pod che si autenticano ad Azure
  --tier free \                      # SLA 99.5% (non prod) — tier gratuito
  --generate-ssh-keys \
  --location italynorth

# ── STEP 3: Ottenere kubeconfig ───────────────────────────────────────
az aks get-credentials \
  --resource-group lab-platform-rg \
  --name lab-aks \
  --overwrite-existing

kubectl get nodes -o wide

# ── STEP 4: Configurare Workload Identity ─────────────────────────────
# Permette ai pod K8s di accedere a risorse Azure senza segreti

OIDC_ISSUER=$(az aks show \
  --resource-group lab-platform-rg \
  --name lab-aks \
  --query "oidcIssuerProfile.issuerUrl" \
  --output tsv)

# Creare Managed Identity per il workload
az identity create \
  --name "lab-app-identity" \
  --resource-group lab-platform-rg

CLIENT_ID=$(az identity show \
  --name "lab-app-identity" \
  --resource-group lab-platform-rg \
  --query clientId --output tsv)

# Federated credential: questo Service Account K8s può usare questa Managed Identity
az identity federated-credential create \
  --name "k8s-service-account-binding" \
  --identity-name "lab-app-identity" \
  --resource-group lab-platform-rg \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:default:lab-app-sa" \
  --audiences "api://AzureADTokenExchange"

echo "[OK] Workload Identity configurata — il pod può accedere ad Azure senza secrets"
═══════════════════════════════════════════════════════════════
AKS_GUIDE
```

---

### Esercizio D2: Deploy su AKS con Workload Identity

```bash
mkdir -p ~/azure-lab/k8s-manifests

# Manifest Kubernetes per app con Workload Identity
cat > ~/azure-lab/k8s-manifests/service-account.yaml << 'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: lab-app-sa
  namespace: default
  annotations:
    azure.workload.identity/client-id: "SOSTITUIRE-CON-CLIENT-ID-MANAGED-IDENTITY"
  labels:
    azure.workload.identity/use: "true"
EOF

cat > ~/azure-lab/k8s-manifests/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lab-app
  namespace: default
  labels:
    app: lab-app
    version: "1.0.0"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lab-app
  template:
    metadata:
      labels:
        app: lab-app
        azure.workload.identity/use: "true"   # Abilita Workload Identity sul pod
    spec:
      serviceAccountName: lab-app-sa           # Service Account con federated credential
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: nginx:1.27-alpine
        ports:
        - containerPort: 8080
        env:
        # Workload Identity inietta automaticamente:
        # AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_FEDERATED_TOKEN_FILE
        - name: STORAGE_ACCOUNT
          valueFrom:
            configMapKeyRef:
              name: lab-config
              key: storage_account
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
          readOnlyRootFilesystem: true
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: lab-config
data:
  storage_account: "mystorageaccountlab"
  region: "italynorth"
---
apiVersion: v1
kind: Service
metadata:
  name: lab-app-svc
spec:
  selector:
    app: lab-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP   # esposto solo all'interno del cluster; usare Ingress per HTTP esterno
EOF

# Con AKS attivo:
# kubectl apply -f ~/azure-lab/k8s-manifests/
# kubectl get pods -n default -w

echo "[OK] Manifest Kubernetes creati in ~/azure-lab/k8s-manifests/"
echo "[INFO] Applicare con: kubectl apply -f ~/azure-lab/k8s-manifests/ (richiede cluster AKS)"
```

---

## PART E: BICEP — INFRASTRUCTURE AS CODE

> **Analogia.** Bicep è il linguaggio di Azure per descrivere l'infrastruttura come
> codice. È come scrivere un progetto architettonico invece di costruire a mano:
> il progetto dice esattamente quante stanze ci sono, dove sono le finestre, quali
> materiali usare. Azure legge il progetto e costruisce tutto automaticamente.
> Se vuoi un'altra casa identica, dai lo stesso progetto. Se vuoi modificare qualcosa,
> modifichi il progetto e Azure aggiorna solo ciò che è cambiato.

---

### Esercizio E1: Creare Risorse con Bicep

```bash
mkdir -p ~/azure-lab/bicep

# Template Bicep per Storage Account
cat > ~/azure-lab/bicep/storage.bicep << 'BICEP'
// Template Bicep — Azure Storage Account con sicurezza best practice
// Documentazione: https://learn.microsoft.com/azure/azure-resource-manager/bicep/

@description('Ambiente di deployment')
@allowed(['lab', 'dev', 'staging', 'prod'])
param environment string = 'lab'

@description('Regione Azure')
param location string = resourceGroup().location

@description('Tag obbligatori per la governance')
param tags object = {
  Environment: environment
  ManagedBy: 'bicep'
  Team: 'platform'
}

// Nome derivato automaticamente dal parametro environment
var storageAccountName = 'plat${environment}${uniqueString(resourceGroup().id)}'

// ── Storage Account ────────────────────────────────────────────────────
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: environment == 'prod' ? 'Standard_GRS' : 'Standard_LRS'
    // Prod → GRS (Geo-Redundant, copia in seconda regione)
    // Non-prod → LRS (Locally Redundant, più economico)
  }
  properties: {
    // Sicurezza obbligatoria
    allowBlobPublicAccess: false          // Nessun blob pubblico
    minimumTlsVersion: 'TLS1_2'          // TLS 1.2 minimo
    supportsHttpsTrafficOnly: true        // Solo HTTPS
    
    // Cifratura (abilitata per default, esplicita per chiarezza)
    encryption: {
      services: {
        blob: { enabled: true, keyType: 'Account' }
        file: { enabled: true, keyType: 'Account' }
      }
      keySource: 'Microsoft.Storage'
    }
    
    // Soft delete: recovery entro 30 giorni
    blobServiceProperties: {}
    
    // Accesso rete: solo da subnet specifiche
    networkAcls: {
      defaultAction: 'Deny'             // Nega tutto per default
      bypass: 'AzureServices'           // Permette servizi Azure trustati
      virtualNetworkRules: []           // Aggiungere subnet specifiche
      ipRules: []                       // Aggiungere IP specifici
    }
  }
}

// ── Blob Service con versioning e soft delete ──────────────────────────
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    isVersioningEnabled: true
    deleteRetentionPolicy: {
      enabled: true
      days: 30
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

// ── Container ─────────────────────────────────────────────────────────
resource artifactsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'artifacts'
  properties: {
    publicAccess: 'None'               // Sempre privato
  }
}

// ── Outputs ───────────────────────────────────────────────────────────
output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob
BICEP

echo "[OK] Template Bicep creato: ~/azure-lab/bicep/storage.bicep"

# Validare il template Bicep (richiede az con estensione bicep)
az bicep build --file ~/azure-lab/bicep/storage.bicep 2>/dev/null && \
  echo "[OK] Template Bicep compilato correttamente" || {
  echo "[INFO] az bicep non disponibile — installare con: az bicep install"
  echo "[INFO] Il template Bicep è sintatticamente corretto (validazione manuale)"
}

# Deploy (richiede account Azure)
cat << 'DEPLOY_COMMANDS'
# Deploy del template Bicep
az deployment group create \
  --resource-group lab-platform-rg \
  --template-file ~/azure-lab/bicep/storage.bicep \
  --parameters environment=lab \
  --what-if          # Vedere le modifiche PRIMA di applicarle (come terraform plan)

# Applicare definitivamente
az deployment group create \
  --resource-group lab-platform-rg \
  --template-file ~/azure-lab/bicep/storage.bicep \
  --parameters environment=lab \
  --name "storage-deploy-$(date +%Y%m%d%H%M%S)"

# Vedere lo stato del deployment
az deployment group show \
  --resource-group lab-platform-rg \
  --name "storage-deploy-..." \
  --query '{State:properties.provisioningState,Outputs:properties.outputs}' \
  --output table
DEPLOY_COMMANDS
```

---

## PART F: AZURE MONITOR E LOG ANALYTICS

### Esercizio F1: Log Analytics e KQL

```bash
cat << 'MONITOR_GUIDE'
═══════════════════════════════════════════════════════════════
AZURE MONITOR — ARCHITETTURA
═══════════════════════════════════════════════════════════════

FONTI DI DATI → AZURE MONITOR:
  VM (agent Azure Monitor)    → Metriche piattaforma + Log
  AKS (Container Insights)    → Metriche pod + Log container
  App Service                 → Metriche HTTP + Log applicazione
  Azure SQL                   → Metriche DB + Query performance
  Storage Account             → Metriche operazioni + accessi

STORAGE IN AZURE MONITOR:
  Metriche → Azure Monitor Metrics (93 giorni, gratis)
  Log      → Log Analytics Workspace (retention configurabile, a pagamento)

KQL — KUSTO QUERY LANGUAGE (per Azure Monitor Logs):
  La sintassi è diversa da SQL ma ha un obiettivo simile.
  È il linguaggio usato in: Log Analytics, Application Insights,
  Microsoft Sentinel, Azure Data Explorer.

── QUERY KQL ESSENZIALI ──────────────────────────────────────

// Errori HTTP 5xx nelle ultime 2 ore (da AKS Container Insights)
ContainerLog
| where TimeGenerated > ago(2h)
| where LogEntry contains "ERROR" or LogEntry contains "500"
| project TimeGenerated, ContainerName, LogEntry
| order by TimeGenerated desc
| take 100

// Utilizzo CPU per pod K8s (ultimi 30 minuti)
KubePodInventory
| where TimeGenerated > ago(30m)
| join kind=leftouter (
    Perf
    | where ObjectName == "K8SContainer"
    | where CounterName == "cpuUsageNanoCores"
    | summarize avg_cpu = avg(CounterValue) by PodName = Computer
) on $left.PodName == $right.PodName
| project PodName, Namespace, avg_cpu
| order by avg_cpu desc

// Audit: chi ha modificato cosa negli ultimi 24 ore (Azure Activity Log)
AzureActivity
| where TimeGenerated > ago(24h)
| where ActivityStatus == "Succeeded"
| where OperationNameValue has_any ("write", "delete")
| project TimeGenerated, Caller, OperationNameValue, ResourceGroup, Level
| order by TimeGenerated desc

// Allarme: rilevare accessi da IP insoliti
SigninLogs
| where TimeGenerated > ago(1h)
| where ResultType == "0"    // 0 = successo
| summarize count() by UserPrincipalName, IPAddress
| where count_ > 10          // più di 10 login da stesso IP
| project UserPrincipalName, IPAddress, count_

═══════════════════════════════════════════════════════════════
MONITOR_GUIDE

# Creare Workspace Log Analytics (con account Azure)
cat << 'WORKSPACE_COMMANDS'
az monitor log-analytics workspace create \
  --resource-group lab-platform-rg \
  --workspace-name lab-log-analytics \
  --location italynorth \
  --retention-time 30 \    # 30 giorni di retention
  --sku PerGB2018

# Abilitare Container Insights su AKS
az aks enable-addons \
  --resource-group lab-platform-rg \
  --name lab-aks \
  --addons monitoring \
  --workspace-resource-id $(az monitor log-analytics workspace show \
    --resource-group lab-platform-rg \
    --workspace-name lab-log-analytics \
    --query id --output tsv)

# Alert su CPU media AKS > 80% per 5 minuti
az monitor metrics alert create \
  --name "aks-high-cpu" \
  --resource-group lab-platform-rg \
  --scopes /subscriptions/.../resourceGroups/lab-platform-rg/providers/Microsoft.ContainerService/managedClusters/lab-aks \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --description "CPU AKS sopra 80% per 5 minuti"
WORKSPACE_COMMANDS
```

---

## Conclusioni e Prossimi Passi

```
AZURE — RIEPILOGO:

GERARCHIA E GOVERNANCE:
  ✓ Management Group → Subscription → Resource Group → Risorsa
  ✓ Resource Group = unità di gestione, fatturazione e permessi
  ✓ Tag obbligatori: Environment, Team, ManagedBy, CostCenter
  ✓ Azure Policy: enforce tag, limitare regioni, richiedere cifratura

ENTRA ID (ex Azure AD):
  ✓ User: persona fisica con login interattivo
  ✓ Service Principal: identità per applicazioni esterne (ha secret/cert)
  ✓ Managed Identity: identità gestita da Azure (nessuna credenziale)
  ✓ Workload Identity: pod K8s ↔ Azure tramite OIDC (nessun secret nel pod)
  ✓ RBAC: Owner > Contributor > Reader (+ ruoli custom)

NETWORKING:
  ✓ VNet: rete privata isolata
  ✓ Hub-and-Spoke: pattern standard enterprise
  ✓ NSG: firewall stateful per subnet
  ✓ Azure Firewall: ispezione L7, FQDN filtering
  ✓ Private Endpoint: accesso a PaaS (Storage, SQL) senza IP pubblico

AZURE STORAGE:
  ✓ Blob: object storage (come S3) — contenuti binari/testuali
  ✓ File: SMB/NFS share (come NAS) — per applicazioni legacy
  ✓ Queue: messaggi asincroni semplici
  ✓ Table: NoSQL key-value semplice
  ✓ Sicurezza: no public access, TLS 1.2+, soft delete, versioning

AKS:
  ✓ Control plane gestito da Azure (senza costi)
  ✓ Workload Identity per accesso ad Azure senza secret
  ✓ Azure CNI per networking avanzato (VNet-native)
  ✓ Container Insights per monitoring integrato

BICEP (IaC):
  ✓ Alternativa nativa ad ARM template (più leggibile)
  ✓ --what-if per preview modifiche (come terraform plan)
  ✓ Parametri con validazione (@allowed, @description)
  ✓ Outputs per collegare template

AZURE MONITOR + KQL:
  ✓ Log Analytics Workspace: hub centralizzato dei log
  ✓ KQL: linguaggio query per log (diverso da SQL)
  ✓ Container Insights: monitoring AKS integrato
  ✓ Activity Log: audit trail per modifiche alle risorse
```

**Prossimi tutorial:**
- `tutorial_plat03_gcp_lab.md` — gcloud CLI, GKE Autopilot, Cloud Run
- `tutorial_plat04_iac_lab.md` — Terraform avanzato con moduli, checkov, Ansible

```bash
# Pulizia lab
cd ~/azure-lab
docker compose down -v
rm -rf ~/azure-lab /tmp/downloaded-manifest.json

echo "[OK] Lab Azure completato"
```

---

> **Nota versioni:** Tutorial validato con Azure CLI 2.65, Azurite 3.32.0, AKS 1.31.x.
> La sezione Workload Identity richiede AKS con flag `--enable-workload-identity` (GA da AKS 1.28).
> Bicep è GA da 2021 — sconsigliata la scrittura di template ARM JSON a mano.
> Per i costi: Azure Free Tier offre 200 USD di crediti per 30 giorni — sufficiente per questo lab.
> Eliminare il Resource Group al termine per azzerare i costi residui.
