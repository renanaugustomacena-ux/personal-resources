# Tutorial: Infrastructure as Code — Terraform, OpenTofu, Ansible — Lab Pratico

> **Documento di riferimento:** `04-infrastructure-as-code.md`
> **Dominio:** Gestione Piattaforme — Infrastructure as Code
> **Ambito:** Principi IaC dichiarativo vs imperativo, OpenTofu/Terraform (state management, moduli, workspace, backend S3), Ansible (playbook, ruoli, vault, inventari dinamici), checkov per sicurezza IaC, tflint per linting, drift detection, Infracost per stima costi, integrazione CI/CD
> **Durata lab:** 6-7 ore
> **Livello:** Intermedio-Avanzato — richiede familiarità con Linux e almeno un cloud provider
> **Prerequisiti:** OpenTofu 1.8+ o Terraform 1.9+, Ansible 2.17+, Python 3.10+, Docker (per LocalStack), checkov, tflint
> **Ambiente:** OpenTofu con LocalStack (state locale), Ansible su container Docker locali

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI IaC LAB ===
echo "=== CHECK PREREQUISITI ==="

# OpenTofu (fork open-source di Terraform — preferito)
tofu --version 2>/dev/null | head -1 && echo "[OK] OpenTofu disponibile" || {
  echo "[FAIL] Installare OpenTofu"
  echo "  Linux: curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh | bash"
  echo "  Alternativa: snap install opentofu --classic"
}

# Terraform (alternativa a OpenTofu)
terraform --version 2>/dev/null | head -1 && echo "[OK] Terraform disponibile" || \
  echo "[INFO] Terraform non trovato (OpenTofu è sufficiente)"

# Ansible
ansible --version 2>/dev/null | head -1 && echo "[OK] Ansible disponibile" || {
  echo "[FAIL] Installare Ansible"
  echo "  pip3 install ansible==11.0.0   # Ansible 2.18 (versione del pacchetto 11.x)"
}

# checkov (scanner sicurezza IaC)
checkov --version 2>/dev/null | head -1 && echo "[OK] checkov disponibile" || {
  echo "[INFO] Installare checkov: pip3 install checkov"
}

# tflint (linter Terraform/OpenTofu)
tflint --version 2>/dev/null | head -1 && echo "[OK] tflint disponibile" || {
  echo "[INFO] Installare tflint: curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash"
}

# Docker (per LocalStack)
docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Docker richiesto"

echo ""
echo "=== SETUP DIRECTORY LAB ==="
mkdir -p ~/iac-lab/{terraform/{modules,environments},ansible/{roles,playbooks,inventory},scripts}
cd ~/iac-lab

echo "[OK] Directory lab: ~/iac-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          IaC LAB                                         │
│                                                                          │
│  PARTE A — FONDAMENTI                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  IaC Dichiarativo vs Imperativo                                 │     │
│  │  - HCL (HashiCorp Configuration Language)                       │     │
│  │  - State file: terraform.tfstate                                │     │
│  │  - Plan → Apply → Destroy lifecycle                             │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  PARTE B — OPENTOFU/TERRAFORM                                            │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  LocalStack ← OpenTofu provider AWS → risorse simulate         │     │
│  │  State: S3 backend (simulato su LocalStack)                     │     │
│  │  Moduli: riutilizzabili e versioned                             │     │
│  │  Workspace: dev / staging / prod                                │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  PARTE C — ANSIBLE                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  Container Docker locali ← Playbook Ansible                    │     │
│  │  Ruoli: struttura modulare                                      │     │
│  │  Vault: cifratura segreti                                       │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  PARTE D — TESTING E SICUREZZA                                           │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  checkov: 1000+ policy di sicurezza                             │     │
│  │  tflint: linting HCL                                            │     │
│  │  Infracost: stima costi                                         │     │
│  └─────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
```

### Setup LocalStack per IaC Lab

```bash
cd ~/iac-lab

cat > compose.yaml << 'EOF'
name: "iac-lab"

services:
  localstack:
    image: localstack/localstack:3.7
    container_name: localstack
    environment:
      SERVICES: s3,iam,ec2,lambda,dynamodb
      AWS_DEFAULT_REGION: eu-west-1
      DEBUG: "0"
    ports:
      - "4566:4566"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
      - localstack-data:/var/lib/localstack
    restart: unless-stopped

volumes:
  localstack-data:
EOF

docker compose up -d

echo "Attendo LocalStack..."
sleep 15

# Configurare AWS CLI per LocalStack
aws configure set aws_access_key_id test
aws configure set aws_secret_access_key test
aws configure set region eu-west-1

alias awslocal='aws --endpoint-url=http://localhost:4566'

# Creare bucket S3 per il remote backend di Terraform
awslocal s3 mb s3://terraform-state-lab
awslocal s3api put-bucket-versioning \
  --bucket terraform-state-lab \
  --versioning-configuration Status=Enabled

# Creare tabella DynamoDB per il locking dello state
awslocal dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

echo "[OK] Backend remoto preparato: S3 + DynamoDB lock"
```

---

## PART A: FONDAMENTI — IaC Dichiarativo vs Imperativo

> Prima dell'IaC, configurare un server significava:
> connettersi via SSH, eseguire una serie di comandi, sperare di non aver
> dimenticato nulla, e non avere alcuna documentazione di quello che era stato
> fatto. Se il server andava in fiamme, dovevi ricominciare da zero ricordando
> a memoria le 47 cose che avevi fatto. Con l'IaC, scrivi il "desiderato":
> "voglio 3 server con queste caratteristiche, questo software, questo file di config".
> Se un server va in fiamme, il tool lo ricrea identico in automatico.

---

### Concetto A1: Dichiarativo vs Imperativo

```
IaC DICHIARATIVO (Terraform, Pulumi, Bicep, CloudFormation):
  "Cosa voglio che esista"
  Esempio: "Voglio un bucket S3 con versioning abilitato"
  
  resource "aws_s3_bucket" "artifacts" {
    bucket = "my-artifacts"
  }
  resource "aws_s3_bucket_versioning" "artifacts" {
    bucket = aws_s3_bucket.artifacts.id
    versioning_configuration { status = "Enabled" }
  }
  
  PRO: idempotente (puoi applicare 1000 volte, risultato uguale)
       il tool calcola il delta tra stato attuale e desiderato
  CON: meno flessibile per logiche complesse (if/else/loop limitati)

IaC IMPERATIVO (Ansible, Chef, Puppet, Shell scripts):
  "Cosa voglio che venga FATTO"
  Esempio: "Esegui questi comandi per installare il software"
  
  - name: Install nginx
    apt:
      name: nginx
      state: present
  
  PRO: flessibile (logica condizionale completa)
       ottimo per configurare DENTRO le macchine
  CON: dipende dall'ordine di esecuzione
       meno "state-aware" di Terraform

COMBINAZIONE BEST PRACTICE:
  Terraform: PROVISIONING infrastruttura (VM, rete, S3, database)
  Ansible:   CONFIGURAZIONE INTERNA delle macchine (software, file, servizi)
  
  Terraform crea la VM → Ansible la configura → App viene deployata
```

---

### Concetto A2: State File — Il Cuore di Terraform

> **Analogia.** Il file `terraform.tfstate` è come il libro mastro di un
> contabile. Tiene traccia di tutto quello che Terraform ha creato e del suo
> stato attuale. Quando fai `terraform plan`, Terraform confronta il tuo
> codice HCL (quello che VUOI) con lo state file (quello che ESISTE) e
> calcola la differenza. Senza questo libro mastro, Terraform non saprebbe
> distinguere una risorsa già creata da una da creare.
>
> **Pericolo:** se perdi lo state file, Terraform "dimentica" tutto quello che
> ha creato. Potresti ritrovarti a dover gestire risorse "orfane" su AWS che
> Terraform non sa più di aver creato. Ecco perché il backend remoto (S3 + lock
> DynamoDB) è OBBLIGATORIO in produzione.

```
STATE FILE — ARCHITETTURA:

terraform.tfstate (locale — SOLO per dev/lab):
  {
    "version": 4,
    "terraform_version": "1.8.0",
    "resources": [
      {
        "type": "aws_s3_bucket",
        "name": "artifacts",
        "instances": [{
          "attributes": {
            "id": "my-artifacts",
            "arn": "arn:aws:s3:::my-artifacts",
            "bucket": "my-artifacts",
            "region": "eu-west-1"
          }
        }]
      }
    ]
  }

BACKEND REMOTO (obbligatorio per team e produzione):
  terraform {
    backend "s3" {
      bucket         = "terraform-state-lab"
      key            = "prod/platform/terraform.tfstate"
      region         = "eu-west-1"
      encrypt        = true              # cifratura AES-256
      dynamodb_table = "terraform-state-lock"  # mutex per l'accesso concorrente
    }
  }

LOCKING:
  Se sviluppatore A e B eseguono terraform apply contemporaneamente,
  il secondo riceve: "Error acquiring the state lock"
  → Evita corruzioni dello state (race condition)

COMANDI STATE:
  terraform state list          # lista risorse nello state
  terraform state show aws_s3_bucket.artifacts  # dettagli risorsa
  terraform state mv old_name new_name  # rinominare risorsa
  terraform state rm aws_s3_bucket.old  # rimuovere dal state (senza distruggere)
  terraform import aws_s3_bucket.existing my-existing-bucket  # importare risorsa esistente
```

---

## PART B: OPENTOFU/TERRAFORM — PRIMO PROGETTO

### Esercizio B1: Progetto Base con State Remoto

```bash
mkdir -p ~/iac-lab/terraform/lab-infra
cd ~/iac-lab/terraform/lab-infra

# ── Configurazione backend ─────────────────────────────────────────────
cat > backend.tf << 'EOF'
terraform {
  required_version = ">= 1.8"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
  
  # Backend remoto: S3 + DynamoDB lock (su LocalStack per lab)
  backend "s3" {
    bucket         = "terraform-state-lab"
    key            = "lab-infra/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    
    # Configurazione per LocalStack
    endpoint                    = "http://localhost:4566"
    access_key                  = "test"
    secret_key                  = "test"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
    skip_region_validation      = true
  }
}

provider "aws" {
  region                      = "eu-west-1"
  access_key                  = "test"
  secret_key                  = "test"
  
  endpoints {
    s3       = "http://localhost:4566"
    iam      = "http://localhost:4566"
    ec2      = "http://localhost:4566"
    dynamodb = "http://localhost:4566"
  }
  
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true
}
EOF

# ── Variabili ─────────────────────────────────────────────────────────
cat > variables.tf << 'EOF'
variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Ambiente deve essere: dev, staging, o prod."
  }
}

variable "project_name" {
  description = "Nome del progetto (usato per tag e naming)"
  type        = string
  default     = "lab-platform"
  
  validation {
    condition     = length(var.project_name) <= 20 && can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Nome progetto: max 20 caratteri, solo minuscole, numeri, trattini."
  }
}

variable "common_tags" {
  description = "Tag comuni applicati a tutte le risorse"
  type        = map(string)
  default     = {}
}
EOF

# ── Valori per ambiente dev ────────────────────────────────────────────
cat > environments/dev.tfvars << 'EOF'
environment  = "dev"
project_name = "lab-platform"

common_tags = {
  Environment = "dev"
  ManagedBy   = "opentofu"
  Team        = "platform"
  CostCenter  = "IT-Lab"
}
EOF

mkdir -p environments

# ── Risorse principali ────────────────────────────────────────────────
cat > main.tf << 'EOF'
# ── Locals: derivati da variabili ─────────────────────────────────────
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  merged_tags = merge(var.common_tags, {
    Project    = var.project_name
    ManagedBy  = "opentofu"
    LastUpdate = "2026-07-16"  # in produzione usare timestamp() ma causa sempre plan non-empty
  })
}

# ── S3 Buckets ────────────────────────────────────────────────────────
resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.name_prefix}-artifacts"
  tags   = merge(local.merged_tags, { Purpose = "artifact-storage" })
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle: sposta oggetti vecchi in storage più economico
resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}

# ── IAM Roles ─────────────────────────────────────────────────────────
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
  name               = "${local.name_prefix}-lambda-processor"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.merged_tags
}

data "aws_iam_policy_document" "lambda_permissions" {
  statement {
    effect  = "Allow"
    actions = ["s3:GetObject", "s3:PutObject", "s3:GetObjectVersion"]
    resources = [
      aws_s3_bucket.artifacts.arn,
      "${aws_s3_bucket.artifacts.arn}/*"
    ]
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
EOF

# ── Outputs ───────────────────────────────────────────────────────────
cat > outputs.tf << 'EOF'
output "artifacts_bucket_name" {
  description = "Nome del bucket S3 per gli artefatti"
  value       = aws_s3_bucket.artifacts.bucket
}

output "artifacts_bucket_arn" {
  description = "ARN del bucket S3"
  value       = aws_s3_bucket.artifacts.arn
}

output "lambda_role_arn" {
  description = "ARN del role IAM per Lambda"
  value       = aws_iam_role.lambda_processor.arn
}
EOF

echo "[OK] File Terraform creati"

# ── Init e apply ──────────────────────────────────────────────────────
tofu init || terraform init

echo ""
echo "Plan:"
tofu plan -var-file=environments/dev.tfvars || terraform plan -var-file=environments/dev.tfvars

echo ""
echo "Apply:"
tofu apply -var-file=environments/dev.tfvars -auto-approve || \
  terraform apply -var-file=environments/dev.tfvars -auto-approve

echo ""
echo "Outputs:"
tofu output || terraform output
```

---

### Esercizio B2: Moduli Riutilizzabili

```bash
mkdir -p ~/iac-lab/terraform/modules/s3-secure-bucket
cd ~/iac-lab/terraform/modules/s3-secure-bucket

# Modulo: S3 Bucket con sicurezza configurata (riutilizzabile)
cat > main.tf << 'EOF'
# Modulo: s3-secure-bucket
# Crea un bucket S3 con tutte le best practice di sicurezza preconfigurate

resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  tags   = merge(var.tags, { Module = "s3-secure-bucket" })
  
  lifecycle {
    prevent_destroy = var.prevent_destroy  # in prod: true
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = var.kms_key_arn != null
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = length(var.lifecycle_rules) > 0 ? 1 : 0
  bucket = aws_s3_bucket.this.id

  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      dynamic "noncurrent_version_expiration" {
        for_each = rule.value.noncurrent_version_expiration_days != null ? [1] : []
        content {
          noncurrent_days = rule.value.noncurrent_version_expiration_days
        }
      }
    }
  }
}
EOF

cat > variables.tf << 'EOF'
variable "bucket_name" {
  description = "Nome del bucket S3 (globalmente unico)"
  type        = string
}

variable "enable_versioning" {
  description = "Abilitare versioning degli oggetti"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN della chiave KMS per cifratura (null = AES-256 gestito da AWS)"
  type        = string
  default     = null
}

variable "prevent_destroy" {
  description = "Prevenire la distruzione accidentale del bucket"
  type        = bool
  default     = false  # true in produzione
}

variable "lifecycle_rules" {
  description = "Regole lifecycle per la gestione automatica degli oggetti"
  type = list(object({
    id                                   = string
    enabled                              = bool
    noncurrent_version_expiration_days   = optional(number)
  }))
  default = [
    {
      id                                 = "expire-old-versions"
      enabled                            = true
      noncurrent_version_expiration_days = 90
    }
  ]
}

variable "tags" {
  description = "Tag da applicare alle risorse"
  type        = map(string)
  default     = {}
}
EOF

cat > outputs.tf << 'EOF'
output "bucket_id"   { value = aws_s3_bucket.this.id }
output "bucket_arn"  { value = aws_s3_bucket.this.arn }
output "bucket_name" { value = aws_s3_bucket.this.bucket }
EOF

echo "[OK] Modulo s3-secure-bucket creato"

# Usare il modulo in un progetto
mkdir -p ~/iac-lab/terraform/environments/dev
cat > ~/iac-lab/terraform/environments/dev/main.tf << 'EOF'
# Usare il modulo locale (in produzione: source = "git::https://..." con ref=v1.0.0)
module "artifacts_bucket" {
  source = "../../modules/s3-secure-bucket"
  
  bucket_name       = "lab-platform-dev-artifacts-2026"
  enable_versioning = true
  prevent_destroy   = false  # In prod: true
  
  lifecycle_rules = [
    {
      id                                 = "expire-noncurrent"
      enabled                            = true
      noncurrent_version_expiration_days = 30
    }
  ]
  
  tags = {
    Environment = "dev"
    ManagedBy   = "opentofu"
    Module      = "s3-secure-bucket"
  }
}

module "logs_bucket" {
  source = "../../modules/s3-secure-bucket"
  
  bucket_name       = "lab-platform-dev-logs-2026"
  enable_versioning = false   # I log non hanno bisogno di versioning
  
  lifecycle_rules = [
    {
      id                                 = "expire-logs"
      enabled                            = true
      noncurrent_version_expiration_days = 7
    }
  ]
  
  tags = {
    Environment = "dev"
    Purpose     = "logging"
  }
}

output "artifacts_bucket" { value = module.artifacts_bucket.bucket_name }
output "logs_bucket"      { value = module.logs_bucket.bucket_name }
EOF
```

---

## PART C: ANSIBLE — CONFIGURAZIONE IMPERATIVA

> **Analogia.** Se Terraform è il progetto architettonico che costruisce l'edificio,
> Ansible è l'arredatore che configura ogni stanza. Non costruisce i muri (quelli
> li fa Terraform), ma installa le appliance, configura i software, posiziona i file.
> Ansible funziona via SSH su host già esistenti — non crea VM, le configura.

---

### Esercizio C1: Playbook Base per un Web Server

```bash
cd ~/iac-lab/ansible

# Avviare container Docker come target per Ansible (simula VM SSH)
docker network create ansible-lab 2>/dev/null || true

docker run -d \
  --name webserver-1 \
  --hostname webserver-1 \
  --network ansible-lab \
  -p 8881:80 \
  ubuntu:24.04 \
  bash -c "apt-get update -qq && apt-get install -y -qq openssh-server && \
    mkdir -p /run/sshd && \
    echo 'root:ansible-lab-pw' | chpasswd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    /usr/sbin/sshd -D"

docker run -d \
  --name webserver-2 \
  --hostname webserver-2 \
  --network ansible-lab \
  -p 8882:80 \
  ubuntu:24.04 \
  bash -c "apt-get update -qq && apt-get install -y -qq openssh-server && \
    mkdir -p /run/sshd && \
    echo 'root:ansible-lab-pw' | chpasswd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    /usr/sbin/sshd -D"

sleep 10
echo "[OK] Container target avviati (webserver-1 :8881, webserver-2 :8882)"

# Ottenere IP dei container
WS1_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' webserver-1)
WS2_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' webserver-2)
echo "[INFO] webserver-1 IP: $WS1_IP"
echo "[INFO] webserver-2 IP: $WS2_IP"

# ── Inventario ────────────────────────────────────────────────────────
mkdir -p ~/iac-lab/ansible/{inventory,playbooks,roles}

cat > ~/iac-lab/ansible/inventory/hosts.ini << EOF
# Inventario statico Ansible
[webservers]
webserver-1 ansible_host=$WS1_IP ansible_user=root ansible_password=ansible-lab-pw
webserver-2 ansible_host=$WS2_IP ansible_user=root ansible_password=ansible-lab-pw

[all:vars]
ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
ansible_python_interpreter=/usr/bin/python3
EOF

# Test connessione
ansible webservers -i ~/iac-lab/ansible/inventory/hosts.ini -m ping

# ── Playbook: installare e configurare nginx ──────────────────────────
cat > ~/iac-lab/ansible/playbooks/webserver.yml << 'EOF'
---
# Playbook: configura web server nginx su tutti gli host del gruppo "webservers"
- name: Configurazione Web Server
  hosts: webservers
  become: yes          # sudo (diventare root)
  vars:
    nginx_port: 80
    app_name: "lab-platform"
    app_version: "1.0.0"
  
  pre_tasks:
    - name: Aggiornare cache apt
      apt:
        update_cache: yes
        cache_valid_time: 3600   # non aggiornare se la cache ha meno di 1 ora

  tasks:
    # ── Installazione nginx ──────────────────────────────────────────
    - name: Installare nginx
      apt:
        name: nginx
        state: present
      notify: Restart nginx      # se nginx non era installato, fai restart

    # ── Configurazione ───────────────────────────────────────────────
    - name: Creare directory per il sito
      file:
        path: /var/www/{{ app_name }}
        state: directory
        owner: www-data
        group: www-data
        mode: '0755'

    - name: Deployare pagina HTML
      copy:
        dest: /var/www/{{ app_name }}/index.html
        content: |
          <!DOCTYPE html>
          <html>
          <head><title>{{ app_name }}</title></head>
          <body>
          <h1>{{ app_name }} v{{ app_version }}</h1>
          <p>Host: {{ ansible_hostname }}</p>
          <p>Configurato da Ansible il: {{ ansible_date_time.date }}</p>
          </body>
          </html>
        mode: '0644'

    - name: Configurare virtual host nginx
      template:
        src: templates/nginx-vhost.conf.j2
        dest: /etc/nginx/sites-available/{{ app_name }}
        mode: '0644'
      notify: Reload nginx      # se la config cambia, ricarica nginx

    - name: Abilitare il sito
      file:
        src: /etc/nginx/sites-available/{{ app_name }}
        dest: /etc/nginx/sites-enabled/{{ app_name }}
        state: link

    - name: Disabilitare sito default nginx
      file:
        path: /etc/nginx/sites-enabled/default
        state: absent
      notify: Reload nginx

    # ── Firewall (UFW) ───────────────────────────────────────────────
    - name: Installare UFW
      apt:
        name: ufw
        state: present

    - name: Aprire porta HTTP
      ufw:
        rule: allow
        port: "{{ nginx_port }}"
        proto: tcp

    - name: Aprire porta SSH
      ufw:
        rule: allow
        port: 22
        proto: tcp

    - name: Abilitare UFW
      ufw:
        state: enabled
        policy: deny        # nega tutto il non autorizzato

    # ── Verifica ─────────────────────────────────────────────────────
    - name: Verificare nginx attivo e in ascolto
      uri:
        url: "http://localhost:{{ nginx_port }}"
        status_code: 200
      retries: 3
      delay: 2

  handlers:
    # I handler sono eseguiti SOLO se notificati, DOPO tutti i task
    - name: Restart nginx
      service:
        name: nginx
        state: restarted
        enabled: yes

    - name: Reload nginx
      service:
        name: nginx
        state: reloaded
EOF

# Template Jinja2 per nginx
mkdir -p ~/iac-lab/ansible/playbooks/templates

cat > ~/iac-lab/ansible/playbooks/templates/nginx-vhost.conf.j2 << 'EOF'
server {
    listen {{ nginx_port }} default_server;
    server_name _;
    
    root /var/www/{{ app_name }};
    index index.html;
    
    # Nascondere versione nginx (sicurezza)
    server_tokens off;
    
    # Header sicurezza
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Nessun accesso ai file nascosti
    location ~ /\. {
        deny all;
    }
}
EOF

# Eseguire il playbook
cd ~/iac-lab/ansible
ansible-playbook \
  -i inventory/hosts.ini \
  playbooks/webserver.yml \
  --diff           # mostra le differenze nei file modificati

# Verificare
curl -s http://localhost:8881 | grep "lab-platform"
curl -s http://localhost:8882 | grep "lab-platform"
echo "[OK] Entrambi i web server configurati"
```

---

### Esercizio C2: Ansible Vault per i Segreti

```bash
cd ~/iac-lab/ansible

# Ansible Vault: cifra segreti nel repository
# NON mettere mai password/token in chiaro nei playbook!

# Creare un file vault con le password del DB
ansible-vault create vars/db-secrets.yml << 'EOF'
db_host: "db.internal.azienda.com"
db_password: "super-secret-password-2026"
db_ssl_cert: |
  -----BEGIN CERTIFICATE-----
  (certificato cifrato con vault)
  -----END CERTIFICATE-----
EOF
# Richiederà una passphrase vault — usare: vault-lab-passphrase-2026

# In alternativa: generare automaticamente
mkdir -p vars
echo "vault-lab-passphrase-2026" > .vault-pass  # NON committare questo file!
echo ".vault-pass" >> .gitignore

# File vault non interattivo
cat > vars/db-secrets.yml.plain << 'EOF'
db_host: "db.internal.azienda.com"
db_password: "super-secret-password-2026"
EOF

ansible-vault encrypt vars/db-secrets.yml.plain \
  --output vars/db-secrets.yml \
  --vault-password-file .vault-pass

rm vars/db-secrets.yml.plain  # rimuovere il file in chiaro!

echo "[OK] Segreti cifrati con Vault"

# Usare il vault in un playbook
cat > playbooks/use-vault-demo.yml << 'EOF'
---
- name: Demo uso Vault
  hosts: localhost
  gather_facts: false
  vars_files:
    - ../vars/db-secrets.yml    # cifrato con vault
  tasks:
    - name: Mostrare DB host (password è oscurata automaticamente da Ansible)
      debug:
        msg: "Connessione a DB: {{ db_host }} (password=OSCURATA)"
    
    - name: Simulare uso password
      no_log: true    # impedisce il log della task che contiene la password
      command: echo "Connessione con password"
      when: db_password is defined
EOF

ansible-playbook playbooks/use-vault-demo.yml \
  --vault-password-file .vault-pass

# Vedere il contenuto cifrato
cat vars/db-secrets.yml | head -5

# Decifrare temporaneamente per leggere
ansible-vault view vars/db-secrets.yml --vault-password-file .vault-pass
```

---

## PART D: SICUREZZA IaC — CHECKOV E TFLINT

### Esercizio D1: Scansione con checkov

```bash
cd ~/iac-lab/terraform/lab-infra

# checkov: oltre 1000 policy di sicurezza per Terraform, CloudFormation, Kubernetes, Dockerfile
checkov --version 2>/dev/null || pip3 install checkov

# Scansionare il codice Terraform
checkov -d . \
  --framework terraform \
  --output cli \
  --compact \
  2>/dev/null | head -60

# Scansionare con output SARIF (per GitHub Actions Code Scanning)
checkov -d . \
  --framework terraform \
  --output sarif \
  --output-file checkov-results.sarif \
  2>/dev/null

echo "[INFO] Report SARIF: checkov-results.sarif"

# Creare un file con una vulnerability intenzionale per vedere checkov in azione
cat > /tmp/vulnerable-test.tf << 'EOF'
# ATTENZIONE: questo file contiene vulnerabilità intenzionali per test checkov
resource "aws_s3_bucket" "vulnerable" {
  bucket = "test-vulnerable-bucket"
  # MANCANO: versioning, cifratura, public access block → checkov lo rileverà
}

resource "aws_security_group" "open_to_world" {
  name = "open-sg"
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # VULNERABILE: apre tutto a internet
  }
}
EOF

echo "Scansione file vulnerabile:"
checkov -f /tmp/vulnerable-test.tf --framework terraform --compact 2>/dev/null | \
  grep -E "FAILED|PASSED" | head -20

rm /tmp/vulnerable-test.tf
```

---

### Esercizio D2: tflint e Infracost

```bash
cd ~/iac-lab/terraform/lab-infra

# tflint: linting per Terraform/OpenTofu
tflint --version 2>/dev/null || {
  echo "[INFO] tflint non disponibile — installare:"
  echo "  curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash"
}

# .tflint.hcl — configurazione linter
cat > .tflint.hcl << 'TFLINT'
plugin "aws" {
  enabled = true
  version = "0.36.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_required_version" {
  enabled = true
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}
TFLINT

tflint --init 2>/dev/null && tflint 2>/dev/null || \
  echo "[INFO] tflint non installato — vedere istruzioni sopra"

# Infracost: stima costi infrastruttura
cat << 'INFRACOST'
═══════════════════════════════════════════════════════════════
INFRACOST — STIMA COSTI PRIMA DI APPLICARE
═══════════════════════════════════════════════════════════════

# Installare
curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | bash

# Autenticarsi (gratuito — richiede email)
infracost auth login

# Vedere il costo del tuo codice Terraform
infracost breakdown --path .

# Confrontare il costo PRIMA e DOPO una modifica (per PR)
# Prima della modifica:
infracost snapshot --path . --format json > infracost-base.json

# Dopo la modifica (stessa directory, codice modificato):
infracost diff --path . --compare-to infracost-base.json

# Output esempio:
# +----------+----------+----------+
# | Resource | Monthly  | Diff     |
# +----------+----------+----------+
# | S3 Bucket| $2.30    | +$0.00   |
# | Lambda   | $0.00    | +$0.00   |
# | Total    | $2.30    | +$0.00   |
# +----------+----------+----------+
═══════════════════════════════════════════════════════════════
INFRACOST
```

---

## PART E: DRIFT DETECTION E CI/CD

### Esercizio E1: Drift Detection

```bash
# Drift = qualcuno ha modificato le risorse al di fuori di Terraform
# (click su console, curl API, script bash)

cd ~/iac-lab/terraform/lab-infra

echo "=== SIMULARE UN DRIFT ==="

# 1. Creare un tag manualmente fuori da Terraform (simula click su console)
awslocal s3api put-bucket-tagging \
  --bucket "lab-platform-dev-artifacts" \
  --tagging '{"TagSet": [{"Key": "ManualTag", "Value": "aggiunto-a-mano"}]}'

echo "[OK] Tag aggiunto manualmente (fuori da Terraform)"

# 2. Eseguire plan — Terraform rileverà il drift
tofu plan -var-file=environments/dev.tfvars 2>/dev/null | grep -E "will be|must be|Plan:"

# Il drift è visibile nella sezione "Changes to Outputs" e "Changes to Resource"
echo ""
echo "Se Terraform vuole RIMUOVERE il tag 'ManualTag' → questo è drift!"
echo "Soluzione: aggiornare il codice Terraform per includere quel tag,"
echo "o eliminare il tag manuale e applicare di nuovo."

# Drift detection automatica in CI/CD:
cat << 'DRIFT_WORKFLOW'
# .github/workflows/drift-detection.yml
name: Drift Detection

on:
  schedule:
    - cron: '0 6 * * 1-5'    # Ogni giorno feriale alle 6:00
  workflow_dispatch:           # Trigger manuale

jobs:
  drift-check:
    runs-on: ubuntu-24.04
    permissions:
      id-token: write   # OIDC
      issues: write     # Per aprire issue in caso di drift
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Auth AWS (OIDC)
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: arn:aws:iam::123456789012:role/github-actions-drift
        aws-region: eu-west-1
    
    - name: Setup OpenTofu
      uses: opentofu/setup-opentofu@v1
    
    - name: Tofu init
      run: tofu init
    
    - name: Drift check
      id: plan
      run: |
        tofu plan -detailed-exitcode 2>&1 | tee plan-output.txt
        echo "exitcode=$?" >> $GITHUB_OUTPUT
    
    - name: Apri issue se c'è drift
      if: steps.plan.outputs.exitcode == '2'   # 2 = modifiche rilevate
      uses: actions/github-script@v7
      with:
        script: |
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: '⚠️ Drift infrastruttura rilevato!',
            body: 'Il piano Terraform ha rilevato modifiche fuori da IaC. Verificare!'
          })
DRIFT_WORKFLOW
```

---

## Conclusioni e Prossimi Passi

```
IaC — RIEPILOGO:

PRINCIPI:
  ✓ Dichiarativo (Terraform): "cosa voglio che esista"
  ✓ Imperativo (Ansible): "cosa voglio che venga fatto"
  ✓ Idempotenza: applicare N volte = stesso risultato
  ✓ Drift detection: monitorare modifiche fuori IaC

OPENTOFU/TERRAFORM:
  ✓ Backend remoto: S3 + DynamoDB lock (obbligatorio per team)
  ✓ Variabili: variables.tf + *.tfvars per ambiente
  ✓ Moduli: riutilizzabili, versioned (source = "git::...")
  ✓ Plan before Apply: mai applicare senza vedere il piano
  ✓ Workspace: ambienti separati con uno stesso codice
  ✓ prevent_destroy: protezione bucket/DB produzione

ANSIBLE:
  ✓ Inventario: statico (hosts.ini) o dinamico (AWS, Azure)
  ✓ Playbook: tasks con idempotenza (state: present/absent)
  ✓ Handler: eseguiti solo quando notificati (restart/reload)
  ✓ Template Jinja2: configurazioni dinamiche
  ✓ Vault: cifratura segreti in repository (ansible-vault encrypt)
  ✓ no_log: true per task che usano password/token

SICUREZZA IaC:
  ✓ checkov: 1000+ policy (CKV_AWS_*, CKV_AZURE_*, CKV_K8S_*)
  ✓ tflint: linting HCL (naming, documentazione, deprecazioni)
  ✓ Infracost: costo stimato PRIMA del deploy (integrazione PR)
  ✓ State file: mai in git, sempre cifrato, sempre con lock

COMANDI ESSENZIALI:
  tofu init / plan / apply / destroy
  tofu state list / show / mv / rm / import
  tofu workspace new staging / select staging
  ansible-playbook -i inventory/hosts.ini playbooks/site.yml --check --diff
  ansible-vault encrypt/decrypt/view/edit
  checkov -d . --framework terraform
  infracost breakdown --path .
```

**Prossimi tutorial:**
- `tutorial_plat09_service_mesh_lab.md` — Istio mTLS e traffic management
- `tutorial_plat13_sicurezza_piattaforme_lab.md` — Falco, OPA, Kyverno

```bash
# Pulizia lab
cd ~/iac-lab/terraform/lab-infra
tofu destroy -var-file=environments/dev.tfvars -auto-approve 2>/dev/null || true

cd ~/iac-lab
docker stop webserver-1 webserver-2 2>/dev/null
docker rm webserver-1 webserver-2 2>/dev/null
docker network rm ansible-lab 2>/dev/null
docker compose down -v
rm -rf ~/iac-lab /tmp/vulnerable-test.tf

echo "[OK] Lab IaC completato"
```

---

> **Nota versioni:** Tutorial validato con OpenTofu 1.8.x, Terraform 1.9.x, Ansible 2.18.x
> (pacchetto ansible 11.0.0), checkov 3.x, tflint 0.53.x, Infracost 0.10.x.
> OpenTofu: fork open-source di Terraform dopo il cambio di licenza BSL 1.1 (agosto 2023).
> Terraform BSL 1.1: non permette uso commerciale come servizio SaaS (HashiCorp TFC/TFE rimane commerciale).
> Per nuovi progetti preferire OpenTofu — compatibile con Terraform ≤ 1.5 senza modifiche al codice.
