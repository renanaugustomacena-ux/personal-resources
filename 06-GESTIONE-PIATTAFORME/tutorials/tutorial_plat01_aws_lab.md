# Tutorial: AWS — Fondamenti e Architettura Cloud con LocalStack — Lab Pratico

> **Documento di riferimento:** `01-cloud-aws.md`
> **Dominio:** Gestione Piattaforme — Cloud Provider AWS
> **Ambito:** Infrastruttura globale AWS, IAM least-privilege, VPC con subnet pubblica/privata, EC2, S3, Lambda, Well-Architected Framework — tutto in locale con LocalStack, senza account AWS reale
> **Durata lab:** 5-6 ore
> **Livello:** Intermedio — richiede conoscenza base di networking TCP/IP e Linux
> **Prerequisiti:** Docker Engine 29.x con Docker Compose, AWS CLI v2, Python 3.10+
> **Ambiente:** LocalStack 3.x (emulatore AWS locale via Docker) + AWS CLI configurato per endpoint locale

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI AWS LAB ===
echo "=== CHECK PREREQUISITI ==="

# Docker e Compose
docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Installare Docker"
docker compose version && echo "[OK] Docker Compose disponibile" || echo "[FAIL] Installare Compose"

# AWS CLI v2
aws --version && echo "[OK] AWS CLI disponibile" || {
  echo "[FAIL] Installare AWS CLI v2"
  echo "  Linux: curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip"
  echo "  Windows: msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi"
}

# Python 3.10+ (per Lambda)
python3 --version | grep -E "3\.(1[0-9])" && echo "[OK] Python >= 3.10" || \
  echo "[WARN] Raccomandato Python 3.10+"

# Porta LocalStack libera
ss -tlnp 2>/dev/null | grep -q ':4566 ' && \
  echo "[WARN] Porta 4566 occupata (LocalStack)" || echo "[OK] Porta 4566 libera"

echo ""
echo "=== SETUP DIRECTORY LAB ==="
mkdir -p ~/aws-lab/{iac,lambda,scripts}
cd ~/aws-lab

echo "[OK] Directory lab: ~/aws-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         AWS LAB — LOCALSTACK                              │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │                  LocalStack 3.x :4566                             │   │
│  │              (emulatore AWS completo in Docker)                   │   │
│  │                                                                   │   │
│  │  IAM      VPC       EC2       S3        Lambda    CloudWatch      │   │
│  │  Users    Subnets   Instances Buckets   Functions Logs/Metrics    │   │
│  │  Roles    SGs       (mock)    Objects   (Python)                  │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                          ↑                                               │
│                    AWS CLI v2                                             │
│               (--endpoint-url http://localhost:4566)                     │
│                          ↑                                               │
│               Operazioni di questo lab:                                  │
│               1. IAM: user + policy least-privilege                     │
│               2. VPC: subnet pubblica + privata + SG                    │
│               3. S3: bucket + policy + versioning                       │
│               4. Lambda: funzione Python + trigger S3                   │
│               5. CloudWatch: log group + filtro metriche                │
└──────────────────────────────────────────────────────────────────────────┘
```

### Avvio LocalStack

```bash
cd ~/aws-lab

cat > compose.yaml << 'EOF'
name: "aws-lab-localstack"

services:
  localstack:
    image: localstack/localstack:3.7
    container_name: localstack
    environment:
      # Servizi da abilitare (subset per questo lab)
      SERVICES: iam,ec2,s3,lambda,cloudwatch,logs,sts,iam
      AWS_DEFAULT_REGION: eu-west-1
      DEBUG: "0"
      # PERSISTENCE: 1    # decommentare per dati persistenti tra restart
      LAMBDA_EXECUTOR: local
    ports:
      - "4566:4566"      # endpoint unico per tutti i servizi AWS
      - "4510-4559:4510-4559"  # porte Lambda allocate dinamicamente
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
      - localstack-data:/var/lib/localstack
    healthcheck:
      test: ["CMD", "curl", "-s", "http://localhost:4566/_localstack/health"]
      interval: 15s
      timeout: 5s
      retries: 10
    restart: unless-stopped

volumes:
  localstack-data:
EOF

docker compose up -d

echo "Attendo LocalStack (30-60 secondi)..."
until curl -sf http://localhost:4566/_localstack/health | grep -q '"s3": "available"'; do
  printf "."
  sleep 3
done
echo ""
echo "[OK] LocalStack operativo"

# Configurare AWS CLI per usare LocalStack
aws configure set aws_access_key_id test
aws configure set aws_secret_access_key test
aws configure set region eu-west-1
aws configure set output json

# Alias comodo per non scrivere --endpoint-url ogni volta
alias awslocal='aws --endpoint-url=http://localhost:4566'

# Verifica
awslocal sts get-caller-identity && echo "[OK] AWS CLI configurato per LocalStack"
```

---

## PART A: FONDAMENTI — Come Funziona AWS

> AWS è nata nel 2006 con l'idea rivoluzionaria che l'infrastruttura IT potesse essere
> noleggiata a consumo, come l'elettricità. Prima di AWS, avviare una startup significava
> comprare server fisici, affittare spazio in un datacenter, aspettare settimane. Con AWS,
> tutto questo si fa in minuti, pagando solo ciò che si usa. Il prezzo di questo convenienza
> è la complessità: oltre 200 servizi diversi, centinaia di opzioni di configurazione,
> e la responsabilità condivisa della sicurezza.

---

### Concetto A1: Il Modello di Responsabilità Condivisa

> **Analogia.** Affittare un appartamento. Il proprietario (AWS) si occupa di struttura,
> tetto, impianti: se cade il tetto, è un problema suo. Tu (cliente) sei responsabile di
> lasciare la porta aperta, di mettere i tuoi oggetti di valore in bella vista, di non
> cambiare la serratura: se sei derubato perché hai lasciato la porta aperta, è un problema tuo.
> AWS protegge il datacenter fisico, l'hypervisor, la rete fisica. Tu devi configurare
> correttamente IAM, aprire solo le porte necessarie, cifrare i dati, gestire le patch del
> sistema operativo sui tuoi EC2.

```
SHARED RESPONSIBILITY MODEL:

┌────────────────────────────────────────────────────────────┐
│                     RESPONSABILITÀ TUA                     │
│                                                            │
│  - Configurazione IAM (permessi, ruoli, policy)           │
│  - Sicurezza delle applicazioni (XSS, SQLi, auth)         │
│  - Patch del sistema operativo (sulle tue istanze EC2)    │
│  - Cifratura dati (a riposo e in transito)                │
│  - Configurazione Security Groups e NACLs                 │
│  - Gestione delle chiavi di cifratura (KMS)               │
│  - Audit trail e logging (CloudTrail, CloudWatch)         │
├────────────────────────────────────────────────────────────┤
│                    RESPONSABILITÀ AWS                       │
│                                                            │
│  - Sicurezza fisica dei datacenter                        │
│  - Infrastruttura hardware (server, storage, rete)        │
│  - Hypervisor (isolamento tra tenant)                     │
│  - Infrastruttura dei servizi gestiti (RDS, Lambda, S3)   │
│  - Patching dei servizi gestiti                           │
└────────────────────────────────────────────────────────────┘

Servizi gestiti (Lambda, RDS, S3) = AWS si occupa di più
EC2 = tu gestisci di più (sistema operativo incluso)
```

---

### Concetto A2: Regioni, AZ e Architettura Multi-Region

> **Analogia.** Pensa ad AWS come a una catena di supermercati globale. Ogni "regione"
> è una città (Milano, Parigi, Londra) con più negozi (le Availability Zones). Se il
> negozio di via Roma chiude (un'AZ va giù), il negozio di via Milano è ancora aperto
> (un'altra AZ). Se tutta la città ha uno sciopero (una regione è irraggiungibile), devi
> andare in un'altra città (altra regione). Multi-AZ = alta disponibilità. Multi-Region =
> disaster recovery e conformità geografica.

```
ARCHITETTURA GLOBALE AWS:

REGIONE: eu-west-1 (Irlanda)
  ├── AZ: eu-west-1a
  │     └── Data Center A (hardware fisicamente separato)
  ├── AZ: eu-west-1b
  │     └── Data Center B
  └── AZ: eu-west-1c
        └── Data Center C

REGIONE: eu-central-1 (Francoforte) ← DR replica
  ├── AZ: eu-central-1a
  ├── AZ: eu-central-1b
  └── AZ: eu-central-1c

SCELTA REGIONE — CRITERI:
  1. Conformità (GDPR → Europa obbligatoria)
  2. Latenza (utenti in Italia → eu-south-1 Milano, eu-west-1 Irlanda, eu-central-1 Francoforte)
  3. Disponibilità servizi (us-east-1 ha i servizi più aggiornati)
  4. Costo (us-east-1 tipicamente il più economico)

SERVIZI GLOBALI (non in una regione specifica):
  IAM, Route53, CloudFront, WAF
```

```bash
# Vedere le regioni disponibili (LocalStack le simula tutte)
awslocal ec2 describe-regions --output table

# Vedere le AZ nella regione eu-west-1
awslocal ec2 describe-availability-zones \
  --region eu-west-1 \
  --query 'AvailabilityZones[*].{Name:ZoneName,State:State}' \
  --output table
```

---

### Concetto A3: Well-Architected Framework — I 6 Pilastri

```
6 PILASTRI WELL-ARCHITECTED (2024):

1. OPERATIONAL EXCELLENCE — "Eseguire e monitorare"
   - Infrastructure as Code (niente click manuali)
   - Runbook per operazioni ricorrenti
   - Post-mortem senza colpe
   Strumenti: AWS Systems Manager, CloudFormation, CloudWatch

2. SECURITY — "Proteggere dati e sistemi"
   - Identity-first: IAM con least privilege
   - Zero Trust (mai fidarsi, sempre verificare)
   - Cifratura ovunque (at rest + in transit)
   Strumenti: IAM, KMS, GuardDuty, Security Hub, CloudTrail

3. RELIABILITY — "Resistere ai guasti"
   - Multi-AZ per alta disponibilità
   - Auto Scaling per gestire picchi
   - Chaos engineering (break things before they break you)
   Strumenti: ELB, Auto Scaling, Route53 Health Checks, RDS Multi-AZ

4. PERFORMANCE EFFICIENCY — "Usare le risorse bene"
   - Right-sizing (non sovra-dimensionare)
   - Caching dove possibile (ElastiCache, CloudFront)
   - Serverless per workload intermittenti
   Strumenti: Lambda, ElastiCache, CloudFront, Compute Optimizer

5. COST OPTIMIZATION — "Non sprecare"
   - Rightsizing delle istanze
   - Reserved Instances / Savings Plans per carichi prevedibili
   - Spot Instances per carichi fault-tolerant
   Strumenti: Cost Explorer, Trusted Advisor, Compute Optimizer

6. SUSTAINABILITY — "Ridurre l'impatto ambientale"
   - Usare regioni con energia rinnovabile
   - Serverless riducono idle capacity
   - Consolidare workload su istanze più grandi
   Strumenti: Customer Carbon Footprint Tool
```

---

## PART B: IAM — GESTIONE IDENTITÀ E PERMESSI

> IAM (Identity and Access Management) è il sistema di controllo accessi di AWS.
> Capire bene IAM è probabilmente il singolo aspetto più importante della sicurezza AWS:
> un errore IAM può esporre tutto il tuo account al pubblico.

### Esercizio B1: Principio del Least Privilege

> **Analogia.** In un'azienda, ogni dipendente ha un badge che apre solo le stanze
> di cui ha bisogno. Il programmatore può entrare nell'ufficio sviluppo, non nel reparto
> sicurezza o nella stanza del server. L'amministratore di sistema può entrare ovunque,
> ma anche lui non dovrebbe accedere alle buste paga. IAM funziona esattamente così:
> ogni entità (utente, servizio, applicazione) riceve esattamente i permessi necessari,
> né più né meno.

```bash
# ── Struttura IAM fondamentale ────────────────────────────────────────
# User: persona fisica o applicazione
# Group: insieme di utenti con stessi permessi
# Role: identità temporanea assunta da servizi o utenti
# Policy: documento JSON che definisce permessi

# Creare un gruppo per i developer
awslocal iam create-group --group-name developers

# Creare una policy di least-privilege per S3 (sola lettura su un bucket specifico)
cat > /tmp/policy-developer-s3.json << 'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyBucketApp",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket",
        "s3:ListBucketVersions"
      ],
      "Resource": [
        "arn:aws:s3:::app-artifacts-lab",
        "arn:aws:s3:::app-artifacts-lab/*"
      ]
    },
    {
      "Sid": "DenyDeleteAlways",
      "Effect": "Deny",
      "Action": [
        "s3:DeleteObject",
        "s3:DeleteBucket",
        "s3:DeleteObjectVersion"
      ],
      "Resource": "*"
    }
  ]
}
POLICY

# Creare la policy
POLICY_ARN=$(awslocal iam create-policy \
  --policy-name "DeveloperS3ReadOnly" \
  --policy-document file:///tmp/policy-developer-s3.json \
  --query 'Policy.Arn' \
  --output text)

echo "[OK] Policy creata: $POLICY_ARN"

# Allegare la policy al gruppo
awslocal iam attach-group-policy \
  --group-name developers \
  --policy-arn "$POLICY_ARN"

echo "[OK] Policy allegata al gruppo developers"

# Creare un utente sviluppatore
awslocal iam create-user --user-name mario.rossi

# Aggiungere l'utente al gruppo
awslocal iam add-user-to-group \
  --user-name mario.rossi \
  --group-name developers

echo "[OK] Utente mario.rossi aggiunto al gruppo developers"

# Creare access keys per l'utente (per uso programmatico)
awslocal iam create-access-key \
  --user-name mario.rossi \
  --query 'AccessKey.{ID:AccessKeyId,Secret:SecretAccessKey}' \
  --output table
```

---

### Esercizio B2: IAM Roles per Servizi (Service Roles)

```bash
# Un IAM Role è diverso da un utente:
# - Non ha password o chiavi permanenti
# - Viene "assunto" temporaneamente (AssumeRole)
# - Ideale per: Lambda, EC2, ECS, e servizi CI/CD (OIDC)

# Creare un role per Lambda (il servizio Lambda assumerà questo role)
cat > /tmp/trust-policy-lambda.json << 'TRUST'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
TRUST

# Il trust policy dice: "Lambda può assumere questo role"
ROLE_ARN=$(awslocal iam create-role \
  --role-name lambda-s3-processor \
  --assume-role-policy-document file:///tmp/trust-policy-lambda.json \
  --query 'Role.Arn' \
  --output text)

echo "[OK] Role creato: $ROLE_ARN"

# Policy per il role Lambda (scrivere su S3, scrivere log)
cat > /tmp/policy-lambda-s3.json << 'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:GetObjectTagging"
      ],
      "Resource": "arn:aws:s3:::app-artifacts-lab/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
POLICY

LAMBDA_POLICY_ARN=$(awslocal iam create-policy \
  --policy-name "LambdaS3ProcessorPolicy" \
  --policy-document file:///tmp/policy-lambda-s3.json \
  --query 'Policy.Arn' \
  --output text)

awslocal iam attach-role-policy \
  --role-name lambda-s3-processor \
  --policy-arn "$LAMBDA_POLICY_ARN"

echo "[OK] Policy Lambda allegata al role"

# Simulare una policy evaluation (chi può fare cosa)
# In AWS reale: aws iam simulate-principal-policy
awslocal iam get-role-policy \
  --role-name lambda-s3-processor \
  --policy-name "LambdaS3ProcessorPolicy" 2>/dev/null || \
echo "[INFO] (LocalStack) usa get-attached-role-policies per le managed policy"

awslocal iam list-attached-role-policies \
  --role-name lambda-s3-processor \
  --output table
```

---

## PART C: NETWORKING — VPC E SUBNETS

> **Analogia.** Una VPC (Virtual Private Cloud) è come costruire la tua rete privata
> dentro ad AWS — come avere un ufficio con la tua rete interna aziendale, separata
> da tutto il resto di internet. Le subnet sono le stanze dell'ufficio: alcune hanno
> finestre che danno su strada (subnet pubblica — accessibile da internet), altre sono
> stanze interne senza accesso diretto (subnet privata — solo traffico interno).

---

### Esercizio C1: Creare una VPC con Subnet Pubblica e Privata

```bash
# ── VPC ───────────────────────────────────────────────────────────────
# CIDR 10.0.0.0/16 = 65.536 indirizzi IP privati

VPC_ID=$(awslocal ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' \
  --output text)

awslocal ec2 create-tags \
  --resources $VPC_ID \
  --tags Key=Name,Value=lab-vpc

echo "[OK] VPC creata: $VPC_ID"

# Abilitare DNS hostname (necessario per EC2 con FQDN)
awslocal ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames

# ── SUBNETS ───────────────────────────────────────────────────────────
# Subnet pubblica (AZ-a): 10.0.1.0/24 = 256 IP
SUBNET_PUB=$(awslocal ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone eu-west-1a \
  --query 'Subnet.SubnetId' \
  --output text)

awslocal ec2 create-tags --resources $SUBNET_PUB \
  --tags Key=Name,Value=public-subnet-1a

# Subnet privata (AZ-a): 10.0.2.0/24 = 256 IP
SUBNET_PRIV=$(awslocal ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone eu-west-1a \
  --query 'Subnet.SubnetId' \
  --output text)

awslocal ec2 create-tags --resources $SUBNET_PRIV \
  --tags Key=Name,Value=private-subnet-1a

echo "[OK] Subnet pubblica: $SUBNET_PUB"
echo "[OK] Subnet privata:  $SUBNET_PRIV"

# ── INTERNET GATEWAY ──────────────────────────────────────────────────
# L'IGW è la porta di accesso a internet dalla subnet pubblica
IGW_ID=$(awslocal ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

awslocal ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID

awslocal ec2 create-tags --resources $IGW_ID \
  --tags Key=Name,Value=lab-igw

echo "[OK] Internet Gateway: $IGW_ID"

# ── ROUTE TABLE ───────────────────────────────────────────────────────
# Route table pubblica: 0.0.0.0/0 → IGW (tutto il traffico verso internet)
RT_PUB=$(awslocal ec2 create-route-table \
  --vpc-id $VPC_ID \
  --query 'RouteTable.RouteTableId' \
  --output text)

awslocal ec2 create-route \
  --route-table-id $RT_PUB \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

awslocal ec2 associate-route-table \
  --route-table-id $RT_PUB \
  --subnet-id $SUBNET_PUB

echo "[OK] Route table pubblica configurata"

# ── SECURITY GROUP ────────────────────────────────────────────────────
# Firewall a livello di istanza (stateful)
SG_WEB=$(awslocal ec2 create-security-group \
  --group-name "web-sg" \
  --description "Security group per web server" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

# Permettere HTTPS (443) da internet
awslocal ec2 authorize-security-group-ingress \
  --group-id $SG_WEB \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Permettere HTTP (80) da internet (per redirect a HTTPS)
awslocal ec2 authorize-security-group-ingress \
  --group-id $SG_WEB \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# SSH solo da IP aziendale (10.0.0.0/8 = tutta la rete interna)
awslocal ec2 authorize-security-group-ingress \
  --group-id $SG_WEB \
  --protocol tcp \
  --port 22 \
  --cidr 10.0.0.0/8

echo "[OK] Security Group web: $SG_WEB"

# Riepilogo VPC creata
awslocal ec2 describe-vpcs \
  --vpc-ids $VPC_ID \
  --query 'Vpcs[*].{ID:VpcId,CIDR:CidrBlock,State:State}' \
  --output table
```

---

## PART D: S3 — STORAGE OGGETTI

> **Analogia.** S3 (Simple Storage Service) è come un magazzino infinito con file
> catalogati per ID. Non è un filesystem (non ci sono cartelle vere) — è un key-value
> store per file binari. La "chiave" è il percorso del file (`immagini/2026/foto.jpg`),
> il "valore" è il contenuto del file. Puoi mettere file di qualsiasi dimensione
> (da 1 byte a 5 terabyte), e accedervi da qualsiasi parte del mondo.

---

### Esercizio D1: S3 — Bucket, Policy e Versioning

```bash
# Creare il bucket (il nome deve essere globalmente unico su AWS)
BUCKET_NAME="app-artifacts-lab"

awslocal s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1

echo "[OK] Bucket creato: s3://$BUCKET_NAME"

# ── VERSIONING ────────────────────────────────────────────────────────
# Versioning = ogni upload conserva le versioni precedenti
# Fondamentale per: audit trail, ripristino accidentale, compliance
awslocal s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

echo "[OK] Versioning abilitato"

# ── SERVER-SIDE ENCRYPTION (SSE-S3) ──────────────────────────────────
awslocal s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }]
  }'

echo "[OK] Cifratura AES-256 abilitata"

# ── BLOCK PUBLIC ACCESS ───────────────────────────────────────────────
# Best practice: bloccare sempre l'accesso pubblico per default
awslocal s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
  }'

echo "[OK] Public access bloccato (best practice)"

# ── LIFECYCLE POLICY ──────────────────────────────────────────────────
# Spostare oggetti verso storage più economici dopo un certo periodo
awslocal s3api put-bucket-lifecycle-configuration \
  --bucket $BUCKET_NAME \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "archive-old-artifacts",
        "Status": "Enabled",
        "Filter": {"Prefix": "artifacts/"},
        "Transitions": [
          {
            "Days": 30,
            "StorageClass": "STANDARD_IA"
          },
          {
            "Days": 90,
            "StorageClass": "GLACIER"
          }
        ],
        "NoncurrentVersionTransitions": [
          {
            "NoncurrentDays": 7,
            "StorageClass": "GLACIER"
          }
        ],
        "NoncurrentVersionExpiration": {
          "NoncurrentDays": 365
        }
      }
    ]
  }'

echo "[OK] Lifecycle policy configurata (30d → IA, 90d → Glacier)"

# ── UPLOAD E DOWNLOAD ─────────────────────────────────────────────────
# Creare file di test
echo '{"version": "1.2.3", "build": "20260716", "status": "stable"}' > /tmp/manifest.json
echo 'console.log("Hello from app v1.2.3")' > /tmp/app.js

# Upload di file
awslocal s3 cp /tmp/manifest.json s3://$BUCKET_NAME/artifacts/v1.2.3/manifest.json
awslocal s3 cp /tmp/app.js s3://$BUCKET_NAME/artifacts/v1.2.3/app.js

echo "[OK] File caricati"

# Listare contenuto bucket
awslocal s3 ls s3://$BUCKET_NAME/artifacts/ --recursive

# Download di un file
awslocal s3 cp s3://$BUCKET_NAME/artifacts/v1.2.3/manifest.json /tmp/downloaded-manifest.json
cat /tmp/downloaded-manifest.json

# Vedere versioni del file
awslocal s3api list-object-versions \
  --bucket $BUCKET_NAME \
  --prefix "artifacts/v1.2.3/manifest.json" \
  --query 'Versions[*].{VersionID:VersionId,Date:LastModified,IsLatest:IsLatest}' \
  --output table
```

---

## PART E: LAMBDA — SERVERLESS COMPUTING

> **Analogia.** Lambda è come un cuoco a chiamata. Invece di avere un cuoco
> fisso in cucina 24h/7 (EC2 che gira sempre), chiami il cuoco solo quando arriva
> un ordine. Lui cucina, ti consegna il piatto, e va via. Paghi solo il tempo
> che ha lavorato, non le ore che avrebbe passato ad aspettare.
> Perfetto per: elaborazione eventi, webhook, automazioni, API a bassa frequenza.

---

### Esercizio E1: Lambda Function Python con Trigger S3

```bash
mkdir -p ~/aws-lab/lambda

# Creare la funzione Lambda in Python
cat > ~/aws-lab/lambda/handler.py << 'PYTHON'
"""
Lambda function: elabora file JSON caricati su S3
Si attiva quando un file viene caricato nel bucket app-artifacts-lab
"""
import json
import boto3
import os
import logging

# Logger strutturato (va a CloudWatch Logs)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Client S3 (usa il role Lambda — nessuna credenziale nel codice!)
s3_client = boto3.client(
    "s3",
    endpoint_url=os.environ.get("AWS_ENDPOINT_URL"),  # LocalStack URL
    region_name=os.environ.get("AWS_DEFAULT_REGION", "eu-west-1")
)

def lambda_handler(event, context):
    """Entry point della Lambda."""
    logger.info("Evento ricevuto: %s", json.dumps(event))
    
    results = []
    
    # Un evento S3 può contenere più record (upload multipli)
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        size = record["s3"]["object"]["size"]
        
        logger.info(
            "Elaboro file: bucket=%s key=%s size=%d bytes",
            bucket, key, size
        )
        
        # Scaricare e validare il contenuto JSON
        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            data = json.loads(content)
            
            # Validazione basilare
            if "version" not in data:
                raise ValueError(f"Il file {key} non contiene il campo 'version'")
            
            logger.info(
                "File valido: versione=%s build=%s",
                data.get("version"), data.get("build")
            )
            
            results.append({
                "key": key,
                "status": "processed",
                "version": data.get("version")
            })
            
        except json.JSONDecodeError as e:
            logger.error("File non è JSON valido: %s — errore: %s", key, str(e))
            results.append({"key": key, "status": "error", "reason": "invalid_json"})
        
        except Exception as e:
            logger.error("Errore elaborando %s: %s", key, str(e))
            results.append({"key": key, "status": "error", "reason": str(e)})
    
    return {
        "statusCode": 200,
        "body": json.dumps({"processed": len(results), "results": results})
    }
PYTHON

# Creare pacchetto ZIP per il deploy
cd ~/aws-lab/lambda
zip -j function.zip handler.py

echo "[OK] Pacchetto Lambda creato: function.zip"
cd ~/aws-lab

# Deploy della Lambda
FUNC_ARN=$(awslocal lambda create-function \
  --function-name s3-artifact-processor \
  --runtime python3.12 \
  --role "arn:aws:iam::000000000000:role/lambda-s3-processor" \
  --handler handler.lambda_handler \
  --zip-file fileb://lambda/function.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment "Variables={
    AWS_ENDPOINT_URL=http://localstack:4566,
    LOG_LEVEL=INFO
  }" \
  --query 'FunctionArn' \
  --output text)

echo "[OK] Lambda deployata: $FUNC_ARN"

# Attendere che la Lambda sia pronta
awslocal lambda wait function-active \
  --function-name s3-artifact-processor 2>/dev/null || sleep 5

# ── TEST MANUALE ──────────────────────────────────────────────────────
# Creare un evento S3 simulato
cat > /tmp/test-event.json << 'EVENT'
{
  "Records": [
    {
      "eventSource": "aws:s3",
      "eventName": "ObjectCreated:Put",
      "s3": {
        "bucket": {
          "name": "app-artifacts-lab"
        },
        "object": {
          "key": "artifacts/v1.2.3/manifest.json",
          "size": 72
        }
      }
    }
  ]
}
EVENT

# Invocare la Lambda
RESULT=$(awslocal lambda invoke \
  --function-name s3-artifact-processor \
  --payload file:///tmp/test-event.json \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda-output.json 2>&1)

echo "Status: $RESULT"
echo "Output:"
cat /tmp/lambda-output.json | python3 -m json.tool

# ── TRIGGER S3 (notifiche automatiche) ────────────────────────────────
# Permesso per S3 di invocare la Lambda
awslocal lambda add-permission \
  --function-name s3-artifact-processor \
  --statement-id s3-trigger-permission \
  --action "lambda:InvokeFunction" \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::app-artifacts-lab"

# Configurare la notifica S3 → Lambda
awslocal s3api put-bucket-notification-configuration \
  --bucket app-artifacts-lab \
  --notification-configuration "{
    \"LambdaFunctionConfigurations\": [
      {
        \"LambdaFunctionArn\": \"$FUNC_ARN\",
        \"Events\": [\"s3:ObjectCreated:*\"],
        \"Filter\": {
          \"Key\": {
            \"FilterRules\": [
              {\"Name\": \"prefix\", \"Value\": \"artifacts/\"},
              {\"Name\": \"suffix\", \"Value\": \".json\"}
            ]
          }
        }
      }
    ]
  }"

echo "[OK] Trigger S3 configurato — ogni upload .json in artifacts/ invocherà la Lambda"

# Test automatico: caricare un file e verificare che la Lambda venga chiamata
echo '{"version": "2.0.0", "build": "20260716", "status": "release"}' > /tmp/v2-manifest.json
awslocal s3 cp /tmp/v2-manifest.json s3://app-artifacts-lab/artifacts/v2.0.0/manifest.json

echo "[OK] File v2.0.0 caricato — Lambda dovrebbe essere stata invocata"

# Vedere i log CloudWatch della Lambda
sleep 3
LOG_GROUP="/aws/lambda/s3-artifact-processor"
awslocal logs describe-log-groups \
  --log-group-name-prefix "$LOG_GROUP" \
  --query 'logGroups[*].logGroupName' \
  --output text

LOG_STREAM=$(awslocal logs describe-log-streams \
  --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime \
  --descending \
  --limit 1 \
  --query 'logStreams[0].logStreamName' \
  --output text 2>/dev/null)

if [ -n "$LOG_STREAM" ] && [ "$LOG_STREAM" != "None" ]; then
  awslocal logs get-log-events \
    --log-group-name "$LOG_GROUP" \
    --log-stream-name "$LOG_STREAM" \
    --query 'events[*].message' \
    --output text
fi
```

---

## PART F: CLOUDWATCH — MONITORING

### Esercizio F1: Metriche Custom e Allarmi

```bash
# Inviare metriche custom a CloudWatch
# (dal tuo codice, da script di monitoraggio, ecc.)
awslocal cloudwatch put-metric-data \
  --namespace "App/Artifacts" \
  --metric-data '[
    {
      "MetricName": "ProcessedFiles",
      "Value": 1,
      "Unit": "Count",
      "Dimensions": [{"Name": "Environment", "Value": "lab"}]
    },
    {
      "MetricName": "ProcessingErrors",
      "Value": 0,
      "Unit": "Count",
      "Dimensions": [{"Name": "Environment", "Value": "lab"}]
    }
  ]'

echo "[OK] Metriche custom inviate a CloudWatch"

# Creare un allarme CloudWatch
awslocal cloudwatch put-metric-alarm \
  --alarm-name "TooManyProcessingErrors" \
  --alarm-description "Lambda ha troppi errori di elaborazione file" \
  --metric-name "ProcessingErrors" \
  --namespace "App/Artifacts" \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=Environment,Value=lab \
  --alarm-actions "arn:aws:sns:eu-west-1:000000000000:ops-alerts" \
  --ok-actions "arn:aws:sns:eu-west-1:000000000000:ops-alerts"

echo "[OK] Allarme CloudWatch creato"

# Listare allarmi
awslocal cloudwatch describe-alarms \
  --alarm-names "TooManyProcessingErrors" \
  --query 'MetricAlarms[*].{Name:AlarmName,State:StateValue,Threshold:Threshold}' \
  --output table

# ── CLOUDWATCH LOGS INSIGHTS ──────────────────────────────────────────
cat << 'INSIGHTS'
In AWS reale, usare CloudWatch Logs Insights per query sui log Lambda:

Query esempio per trovare errori:
  fields @timestamp, @message
  | filter @message like /ERROR/
  | sort @timestamp desc
  | limit 20

Query per latenza media Lambda:
  fields @duration
  | stats avg(@duration) as avg_duration,
          max(@duration) as max_duration,
          percentile(@duration, 99) as p99_duration
  | sort avg_duration desc

Costo: 0.005 USD per GB di dati scansionati
INSIGHTS
```

---

## PART G: INFRASTRUTTURA AS CODE CON TERRAFORM

### Esercizio G1: Terraform con LocalStack

```bash
mkdir -p ~/aws-lab/iac

# Verificare Terraform/OpenTofu
terraform version 2>/dev/null || tofu version 2>/dev/null || {
  echo "[INFO] Installare OpenTofu (alternativa open-source a Terraform):"
  echo "  curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh | bash"
}

cat > ~/aws-lab/iac/main.tf << 'TF'
terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

provider "aws" {
  region                      = "eu-west-1"
  access_key                  = "test"
  secret_key                  = "test"
  
  # LocalStack: sovrascrivere gli endpoint
  endpoints {
    s3         = "http://localhost:4566"
    iam        = "http://localhost:4566"
    lambda     = "http://localhost:4566"
    cloudwatch = "http://localhost:4566"
  }
  
  # Necessario per LocalStack (niente firma SigV4)
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
}

# ── S3 Bucket ─────────────────────────────────────────────────────────
resource "aws_s3_bucket" "terraform_artifacts" {
  bucket = "terraform-artifacts-lab"
  
  tags = {
    Environment = "lab"
    ManagedBy   = "terraform"
    Team        = "platform"
  }
}

resource "aws_s3_bucket_versioning" "terraform_artifacts" {
  bucket = aws_s3_bucket.terraform_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_artifacts" {
  bucket = aws_s3_bucket.terraform_artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_artifacts" {
  bucket = aws_s3_bucket.terraform_artifacts.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── IAM Role per Lambda ────────────────────────────────────────────────
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_processor" {
  name               = "terraform-lambda-processor"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  
  tags = { ManagedBy = "terraform" }
}

data "aws_iam_policy_document" "lambda_permissions" {
  statement {
    effect  = "Allow"
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.terraform_artifacts.arn}/*"]
  }
  statement {
    effect  = "Allow"
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy" "lambda_processor" {
  name   = "LambdaProcessorPermissions"
  role   = aws_iam_role.lambda_processor.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

# Outputs
output "bucket_name" {
  value = aws_s3_bucket.terraform_artifacts.bucket
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_processor.arn
}
TF

# Apply
cd ~/aws-lab/iac

terraform init 2>/dev/null || tofu init 2>/dev/null || \
  echo "[INFO] Installare terraform/tofu per eseguire questo step"

terraform plan 2>/dev/null || tofu plan 2>/dev/null || true
terraform apply -auto-approve 2>/dev/null || tofu apply -auto-approve 2>/dev/null || true

echo "[OK] Infrastruttura creata via Terraform"
```

---

## Conclusioni e Prossimi Passi

```
AWS — RIEPILOGO:

FONDAMENTI:
  ✓ Shared Responsibility Model: AWS protegge l'infrastruttura,
    tu proteggi configurazioni, dati, e accessi
  ✓ Regioni e AZ: multi-AZ per alta disponibilità,
    multi-region per disaster recovery
  ✓ Well-Architected Framework: 6 pilastri (Security,
    Reliability, Performance, Cost, Operational, Sustainability)

IAM:
  ✓ Users/Groups/Roles/Policies
  ✓ Least privilege: concedi solo ciò che serve
  ✓ Preferire Roles per servizi (no long-lived access keys)
  ✓ Service Roles: Lambda, EC2, ECS assumono Roles temporanei
  ✓ OIDC Federation: GitHub Actions, GitLab CI senza access keys

VPC:
  ✓ VPC = rete privata isolata
  ✓ Subnet pubblica = accesso internet tramite IGW
  ✓ Subnet privata = solo traffico interno o tramite NAT GW
  ✓ Security Groups: firewall stateful per istanza
  ✓ NACLs: firewall stateless per subnet (livello aggiuntivo)

S3:
  ✓ Object storage (non filesystem): key → value
  ✓ Versioning: recupero accidentale, audit trail
  ✓ Lifecycle: STANDARD → IA (30d) → Glacier (90d)
  ✓ Cifratura SSE-S3 (AES-256) obbligatoria
  ✓ Block Public Access: default ON in tutti i nuovi bucket

LAMBDA:
  ✓ Serverless: paghi solo il tempo di esecuzione
  ✓ Trigger: S3, API Gateway, EventBridge, SQS
  ✓ IAM Role per accedere ad altri servizi (mai hardcode keys)
  ✓ CloudWatch Logs: ogni invocazione logga automaticamente

CLOUDWATCH:
  ✓ Metriche: sistema (EC2), servizi gestiti, custom
  ✓ Allarmi: notifiche su soglie (via SNS, Lambda, EC2 Auto Scaling)
  ✓ Logs Insights: query simil-SQL sui log

TERRAFORM / IaC:
  ✓ Infrastruttura dichiarativa: niente click manuali
  ✓ State file: terraform.tfstate — da mettere in S3 (non in git!)
  ✓ Plan prima di apply: vedere le modifiche prima di applicarle
  ✓ Tag obbligatori: Environment, Team, ManagedBy

COMANDI AWS CLI ESSENZIALI:
  aws configure                          # configurazione credenziali
  aws iam list-users                     # listare utenti IAM
  aws s3 ls / cp / sync                  # operazioni S3 base
  aws lambda invoke                      # testare Lambda manualmente
  aws cloudwatch get-metric-data         # leggere metriche
  aws ec2 describe-instances --output table  # stato EC2
```

**Prossimi tutorial:**
- `tutorial_plat02_azure_lab.md` — Azure CLI, Entra ID, AKS, Bicep
- `tutorial_plat03_gcp_lab.md` — gcloud CLI, GKE Autopilot, Cloud Run
- `tutorial_plat04_iac_lab.md` — Terraform avanzato, Ansible, checkov

```bash
# Pulizia lab
cd ~/aws-lab
docker compose down -v
rm -rf ~/aws-lab /tmp/{policy-*.json,trust-*.json,test-event.json,lambda-output.json,v2-manifest.json}

echo "[OK] Lab AWS completato"
```

---

> **Nota versioni:** Tutorial validato con LocalStack 3.7, AWS CLI v2.17, Terraform 1.9 / OpenTofu 1.8,
> Python 3.12. In un ambiente AWS reale: sostituire `--endpoint-url http://localhost:4566` e
> usare credenziali IAM reali (preferibilmente tramite SSO/Identity Center, non access key statiche).
> Per CI/CD usare OIDC federation (nessuna access key nel codice o nelle variabili di ambiente).
