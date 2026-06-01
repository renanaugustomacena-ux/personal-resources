---
corso: "Gestione Piattaforme e DevOps"
fase: "2 — IaC e CI/CD"
modulo: 4
titolo: "Infrastructure as Code (IaC)"
versione: "Terraform 1.9+ / Ansible 2.17+"
livello: "Avanzato"
prerequisiti: ["01-cloud-aws", "02-cloud-azure", "03-cloud-gcp"]
obiettivi:
  - "Comprendere i principi fondamentali dell'Infrastructure as Code e la differenza tra approccio dichiarativo e imperativo"
  - "Padroneggiare Terraform: state management, moduli riutilizzabili, workspace e backend remoti"
  - "Automatizzare la configurazione con Ansible: playbook, ruoli, inventari dinamici e vault"
  - "Implementare testing e scansione di sicurezza del codice IaC con checkov, tflint e terratest"
  - "Integrare IaC nelle pipeline CI/CD con drift detection, approvazioni e policy as code"
tag: [iac, terraform, ansible, opentofu, pulumi, state-management, drift-detection, ci-cd]
---

# Infrastructure as Code (IaC)

> **Modulo 04** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Comprendere i principi fondamentali dell'Infrastructure as Code e la differenza tra approccio dichiarativo e imperativo
> 2. Padroneggiare Terraform: state management, moduli riutilizzabili, workspace e backend remoti
> 3. Automatizzare la configurazione con Ansible: playbook, ruoli, inventari dinamici e vault
> 4. Implementare testing e scansione di sicurezza del codice IaC con checkov, tflint e terratest
> 5. Integrare IaC nelle pipeline CI/CD con drift detection, approvazioni e policy as code
>
> **Prerequisiti:** [AWS](01-cloud-aws.md) · [Azure](02-cloud-azure.md) · [GCP](03-cloud-gcp.md)
> **Tempo stimato:** 90 min · **Livello:** Avanzato

## Idee guida

1. **Terraform/OpenTofu = standard de facto.** Pulumi, Crossplane sono niche.
2. **State file e source of truth, treat carefully.** Remote backend (S3 + DynamoDB lock) mandatory.
3. **Module reuse > monolithic config.** Versioned modules.
4. **Drift detection: regular `terraform plan`.** Drift = qualcuno cambio fuori IaC.


## Indice

1. [Panoramica](#panoramica)
2. [Terraform — Fondamenti](#terraform--fondamenti)
3. [Terraform — Avanzato](#terraform--avanzato)
4. [Terraform per AWS](#terraform-per-aws)
5. [Terraform per Azure](#terraform-per-azure)
6. [Ansible — Fondamenti](#ansible--fondamenti)
7. [Ansible — Avanzato](#ansible--avanzato)
8. [Ansible per Server](#ansible-per-server)
9. [Pulumi](#pulumi)
10. [CloudFormation e Bicep](#cloudformation-e-bicep)
11. [OpenTofu — Il Fork Open-Source](#opentofu--il-fork-open-source)
12. [Pulumi — Approfondimento](#pulumi--approfondimento)
13. [Crossplane — IaC Kubernetes-Native](#crossplane--iac-kubernetes-native)
14. [CI/CD per IaC](#cicd-per-iac)
15. [CI/CD per IaC — Approfondimento](#cicd-per-iac--approfondimento)
16. [Testing dell'IaC](#testing-delliac)
17. [Sicurezza dell'IaC](#sicurezza-delliac)
18. [Pattern di Gestione dello State](#pattern-di-gestione-dello-state)
19. [Pattern di Design dei Moduli](#pattern-di-design-dei-moduli)
20. [Strategie Multi-Cloud](#strategie-multi-cloud)
21. [Stima dei Costi — Infracost](#stima-dei-costi--infracost)
22. [IaC su Scala](#iac-su-scala)
23. [Best Practices](#best-practices)

---

## Panoramica

### Filosofia dell'Infrastructure as Code

L'Infrastructure as Code rappresenta un cambio di paradigma fondamentale nella gestione delle infrastrutture IT. Invece di configurare server, reti e servizi manualmente attraverso console grafiche o comandi interattivi, l'intera infrastruttura viene descritta in file di testo versionabili, ripetibili e verificabili. Questo approccio porta i principi dell'ingegneria del software — controllo di versione, code review, testing automatico, continuous integration — nel mondo delle operazioni infrastrutturali.

La filosofia alla base dell'IaC si fonda su alcuni principi cardine. Primo fra tutti, la **ripetibilita**: eseguendo lo stesso codice piu volte si ottiene sempre lo stesso risultato. Secondo, la **tracciabilita**: ogni modifica all'infrastruttura e registrata nel sistema di version control, rendendo possibile sapere chi ha cambiato cosa, quando e perche. Terzo, la **collaborazione**: il codice infrastrutturale puo essere rivisto, commentato e approvato esattamente come il codice applicativo.

Prima dell'IaC, il provisioning infrastrutturale era dominato da processi manuali, spesso documentati in wiki obsolete o tramandati oralmente fra operatori. Questo approccio generava i cosiddetti "snowflake server" — macchine configurate in modo unico e irriproducibile, dove nessuno sapeva esattamente quali modifiche fossero state applicate nel tempo. L'IaC elimina questo problema alla radice.

### Approccio Imperativo vs Dichiarativo

Nell'IaC esistono due paradigmi fondamentali per descrivere l'infrastruttura desiderata.

L'**approccio imperativo** specifica *come* raggiungere lo stato desiderato, elencando passo dopo passo le operazioni da eseguire. Ansible, ad esempio, adotta prevalentemente questo modello: un playbook descrive una sequenza ordinata di task da eseguire sui target. Se si vuole installare Nginx su un server, si scrive esplicitamente "installa il pacchetto nginx, copia il file di configurazione, avvia il servizio".

L'**approccio dichiarativo** specifica *cosa* si vuole ottenere, lasciando allo strumento il compito di determinare le azioni necessarie per raggiungere quello stato. Terraform e l'esempio piu rappresentativo: si dichiara "voglio un'istanza EC2 con queste caratteristiche" e Terraform calcola automaticamente le operazioni necessarie — creazione, modifica o distruzione — per allineare lo stato reale a quello desiderato.

In pratica, la distinzione non e sempre netta. Ansible include moduli dichiarativi (come quelli per i servizi cloud), mentre Terraform supporta costrutti imperativi attraverso i provisioners. La scelta fra i due approcci dipende dal contesto: il dichiarativo eccelle nel provisioning di risorse cloud, l'imperativo nella configurazione dettagliata dei sistemi operativi.

### Infrastruttura Mutabile vs Immutabile

L'**infrastruttura mutabile** prevede che i server vengano aggiornati in-place: si applica una patch, si aggiorna un pacchetto, si modifica una configurazione direttamente sulla macchina in esecuzione. E l'approccio tradizionale, tipico della gestione con Ansible o script Bash. Il rischio principale e il *configuration drift*: col tempo, le macchine divergono dallo stato desiderato a causa di modifiche manuali, aggiornamenti parziali o errori.

L'**infrastruttura immutabile** adotta un approccio radicalmente diverso: i server non vengono mai modificati dopo la creazione. Quando serve un aggiornamento, si costruisce una nuova immagine (AMI, Docker image, VM image), si distribuiscono nuove istanze basate su quell'immagine e si distruggono quelle vecchie. Strumenti come Packer (per le immagini VM) e Docker (per i container) abilitano questo modello. Terraform si sposa naturalmente con l'infrastruttura immutabile, poiche la sua logica di `create_before_destroy` facilita la sostituzione delle risorse.

### Idempotenza

L'idempotenza e una proprieta cruciale nell'IaC: un'operazione e idempotente quando eseguirla una volta o mille volte produce lo stesso risultato finale. Se si dichiara "il pacchetto nginx deve essere installato", un sistema idempotente verifichera prima se nginx e gia presente e, solo in caso contrario, procedera all'installazione.

Terraform e intrinsecamente idempotente grazie al suo meccanismo di state: confronta lo stato desiderato (il codice) con lo stato corrente (il file di state) e applica solo le differenze. Ansible raggiunge l'idempotenza attraverso moduli ben progettati: il modulo `apt` con `state: present` non reinstalla un pacchetto gia presente. Tuttavia, l'idempotenza in Ansible richiede attenzione: usare il modulo `command` o `shell` per eseguire comandi arbitrari puo facilmente violare questa proprieta, a meno che non si utilizzi il parametro `creates` o `when` per condizionare l'esecuzione.

---

## Terraform — Fondamenti

### Sintassi HCL

Terraform utilizza l'HashiCorp Configuration Language (HCL), un linguaggio dichiarativo progettato per essere leggibile sia dagli umani che dalle macchine. HCL si basa su blocchi, argomenti e espressioni.

```hcl
# Commento su singola riga

/* Commento
   multi-riga */

# Blocco risorsa con tipo e nome logico
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name        = "WebServer"
    Environment = "production"
  }
}
```

I tipi di dato principali in HCL includono stringhe, numeri, booleani, liste (`["a", "b", "c"]`), mappe (`{ key = "value" }`), e set. Le espressioni supportano interpolazione di stringhe (`"${var.name}-server"`), operatori logici e aritmetici, e funzioni built-in come `join()`, `lookup()`, `length()`, `file()`, `templatefile()`.

### Providers

I providers sono plugin che permettono a Terraform di interagire con API esterne — cloud provider, servizi SaaS, piattaforme di virtualizzazione. Ogni provider espone un insieme di resource types e data sources.

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.5.0"
}

provider "aws" {
  region  = "eu-west-1"
  profile = "production"

  default_tags {
    tags = {
      ManagedBy = "Terraform"
      Project   = "studio-lavoro"
    }
  }
}
```

Il vincolo di versione `~> 5.0` (operatore "pessimistic constraint") permette aggiornamenti minori (5.1, 5.2...) ma non major (6.0). Questo garantisce stabilita evitando breaking changes.

### Resources

Le resources sono l'elemento fondamentale di Terraform. Ogni blocco `resource` descrive uno o piu oggetti infrastrutturali — un'istanza EC2, un bucket S3, un record DNS.

```hcl
resource "aws_s3_bucket" "data_lake" {
  bucket = "azienda-data-lake-prod"
}

resource "aws_s3_bucket_versioning" "data_lake_versioning" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake_enc" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}
```

Le risorse possono referenziarsi tra loro attraverso il formato `tipo.nome_logico.attributo`. Terraform costruisce automaticamente un grafo delle dipendenze e parallelizza le operazioni dove possibile.

### Data Sources

I data sources permettono di interrogare dati esistenti senza gestirli direttamente. Sono utili per leggere informazioni su risorse create al di fuori di Terraform o in un altro state.

```hcl
# Recupera l'AMI Amazon Linux 2 piu recente
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Recupera informazioni sulla VPC di default
data "aws_vpc" "default" {
  default = true
}

# Uso del data source
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  subnet_id     = data.aws_vpc.default.main_route_table_id
}
```

### Variabili: Input, Output e Local

Le **variabili di input** parametrizzano la configurazione, rendendola riutilizzabile in ambienti diversi.

```hcl
# variables.tf
variable "environment" {
  description = "Ambiente di deploy (dev, staging, production)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "L'ambiente deve essere dev, staging o production."
  }
}

variable "instance_count" {
  description = "Numero di istanze da creare"
  type        = number
  default     = 1
}

variable "allowed_cidrs" {
  description = "Lista di CIDR autorizzati"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tag aggiuntivi per le risorse"
  type        = map(string)
  default     = {}
}
```

Le **variabili di output** espongono valori utili dopo l'applicazione, utilizzabili da altri moduli o script esterni.

```hcl
# outputs.tf
output "instance_public_ips" {
  description = "Indirizzi IP pubblici delle istanze"
  value       = aws_instance.web[*].public_ip
}

output "load_balancer_dns" {
  description = "DNS name del load balancer"
  value       = aws_lb.main.dns_name
}

output "database_endpoint" {
  description = "Endpoint del database RDS"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
```

Le **variabili locali** calcolano valori intermedi, evitando ripetizioni e migliorando la leggibilita.

```hcl
locals {
  common_tags = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "studio-lavoro"
  })

  name_prefix = "${var.project}-${var.environment}"

  is_production = var.environment == "production"
}
```

### Comandi Fondamentali

Il workflow di Terraform si articola in quattro comandi principali.

**`terraform init`** inizializza la directory di lavoro: scarica i provider dichiarati, configura il backend per lo state e installa i moduli referenziati. Va eseguito ogni volta che si modifica la configurazione dei provider o del backend.

**`terraform plan`** calcola il piano di esecuzione confrontando lo stato desiderato con quello attuale. Mostra le risorse che verranno create, modificate o distrutte, senza applicare alcuna modifica. E il momento della revisione: prima di ogni `apply`, si verifica che il piano corrisponda alle intenzioni.

**`terraform apply`** applica le modifiche calcolate dal piano. Per default chiede conferma interattiva; con il flag `-auto-approve` procede automaticamente (utile nelle pipeline CI/CD, pericoloso se usato manualmente).

**`terraform destroy`** elimina tutte le risorse gestite dallo state. Richiede conferma esplicita. In produzione, questo comando dovrebbe essere protetto da policy e approvazioni.

```bash
# Workflow tipico
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Distruzione (con cautela)
terraform destroy
```

---

## Terraform — Avanzato

### Moduli: Struttura, Registry e Versioning

I moduli sono il meccanismo di astrazione e riutilizzo in Terraform. Un modulo e semplicemente una directory contenente file `.tf`. La struttura raccomandata prevede:

```
modules/
  vpc/
    main.tf          # Risorse principali
    variables.tf     # Input del modulo
    outputs.tf       # Output del modulo
    versions.tf      # Vincoli su provider e Terraform
    README.md        # Documentazione
```

L'utilizzo di un modulo locale o remoto segue la stessa sintassi:

```hcl
# Modulo locale
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr     = "10.0.0.0/16"
  environment  = var.environment
  azs          = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
}

# Modulo dal Terraform Registry
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"

  name = "main-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}

# Modulo da repository Git con tag di versione
module "custom_module" {
  source = "git::https://github.com/org/terraform-modules.git//networking/vpc?ref=v2.3.1"
}
```

Il versioning dei moduli e fondamentale per la stabilita. Si usa il pinning esplicito della versione per evitare aggiornamenti inaspettati.

### Gestione dello State

Lo state di Terraform e il file JSON che mappa le risorse dichiarate nel codice agli oggetti reali nell'infrastruttura. Per impostazione predefinita, lo state viene salvato localmente nel file `terraform.tfstate`. In un contesto di team, questo e inaccettabile: lo state deve essere centralizzato, protetto e condiviso.

**Backend S3 con DynamoDB** (approccio AWS classico):

```hcl
terraform {
  backend "s3" {
    bucket         = "azienda-terraform-state"
    key            = "production/networking/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

Il bucket S3 ospita il file di state (con versioning abilitato per il recovery), mentre la tabella DynamoDB implementa il **state locking**: quando un operatore esegue `terraform apply`, un lock impedisce ad altri di modificare lo state simultaneamente, prevenendo corruzioni e conflitti.

**Terraform Cloud** offre un'alternativa gestita che include state storage, locking, esecuzione remota, policy enforcement e audit log:

```hcl
terraform {
  cloud {
    organization = "azienda"
    workspaces {
      name = "production-networking"
    }
  }
}
```

### Workspaces

I workspaces permettono di gestire ambienti multipli (dev, staging, production) con lo stesso codice e state files separati.

```bash
terraform workspace new dev
terraform workspace new staging
terraform workspace new production
terraform workspace select production
terraform workspace list
```

```hcl
# Uso del workspace nel codice
locals {
  instance_type = {
    dev        = "t3.micro"
    staging    = "t3.small"
    production = "t3.large"
  }
}

resource "aws_instance" "app" {
  instance_type = local.instance_type[terraform.workspace]
}
```

Tuttavia, molti team preferiscono directory separate per ambiente piuttosto che i workspaces, per avere isolamento completo dello state e configurazioni piu esplicite.

### Import di Risorse Esistenti

Quando si adotta Terraform su un'infrastruttura gia esistente, e necessario importare le risorse nello state senza ricrearle.

```bash
# Import classico (richiede di scrivere prima il blocco resource)
terraform import aws_instance.legacy i-0abc123def456

# Import block (Terraform 1.5+, approccio dichiarativo)
```

```hcl
import {
  to = aws_instance.legacy
  id = "i-0abc123def456"
}

# Genera automaticamente il codice HCL corrispondente
# terraform plan -generate-config-out=generated.tf
```

### Lifecycle Meta-Arguments

I meta-argomenti `lifecycle` controllano il comportamento di creazione, aggiornamento e distruzione delle risorse.

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.latest.id
  instance_type = "t3.micro"

  lifecycle {
    # Crea la nuova istanza prima di distruggere la vecchia (zero-downtime)
    create_before_destroy = true

    # Impedisce la distruzione accidentale (utile per database)
    prevent_destroy = true

    # Ignora modifiche esterne a certi attributi
    ignore_changes = [
      tags["LastModified"],
      ami,
    ]
  }
}
```

`create_before_destroy` e essenziale per le risorse che non possono avere downtime: Terraform crea il sostituto, verifica che sia operativo, e solo poi distrugge l'originale. `prevent_destroy` protegge risorse critiche come database e bucket con dati importanti. `ignore_changes` e utile quando sistemi esterni (auto-scaling, tag automatici) modificano attributi che Terraform non deve sovrascrivere.

### Provisioners

I provisioners eseguono azioni sulla macchina locale o su risorse remote dopo la creazione. Sono considerati una "ultima risorsa" dalla documentazione ufficiale, perche violano il modello dichiarativo.

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y nginx",
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("~/.ssh/id_rsa")
      host        = self.public_ip
    }
  }

  provisioner "local-exec" {
    command = "echo ${self.public_ip} >> inventory.txt"
  }
}
```

Nella pratica moderna, i provisioners vengono sostituiti da user_data (cloud-init), immagini preconfigurate (Packer) o strumenti dedicati come Ansible.

### Dynamic Blocks

I dynamic blocks generano blocchi ripetuti all'interno di una risorsa, evitando duplicazione di codice.

```hcl
variable "ingress_rules" {
  type = list(object({
    port        = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))
  default = [
    { port = 80,  protocol = "tcp", cidr_blocks = ["0.0.0.0/0"], description = "HTTP" },
    { port = 443, protocol = "tcp", cidr_blocks = ["0.0.0.0/0"], description = "HTTPS" },
    { port = 22,  protocol = "tcp", cidr_blocks = ["10.0.0.0/8"], description = "SSH interno" },
  ]
}

resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Security group per web server"
  vpc_id      = module.vpc.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### for_each vs count

Entrambi permettono di creare risorse multiple, ma con differenze importanti.

**`count`** crea risorse indicizzate numericamente. Rimuovere un elemento dalla lista causa la ricostruzione di tutte le risorse successive (shift dell'indice).

```hcl
resource "aws_instance" "web" {
  count         = 3
  ami           = data.aws_ami.latest.id
  instance_type = "t3.micro"
  tags = {
    Name = "web-${count.index}"
  }
}
```

**`for_each`** crea risorse indicizzate per chiave. Rimuovere un elemento non influenza gli altri, rendendolo l'approccio preferito nella maggior parte dei casi.

```hcl
variable "instances" {
  type = map(object({
    instance_type = string
    ami           = string
  }))
  default = {
    web    = { instance_type = "t3.micro",  ami = "ami-abc123" }
    api    = { instance_type = "t3.small",  ami = "ami-abc123" }
    worker = { instance_type = "t3.medium", ami = "ami-def456" }
  }
}

resource "aws_instance" "server" {
  for_each      = var.instances
  ami           = each.value.ami
  instance_type = each.value.instance_type
  tags = {
    Name = each.key
  }
}
```

### terraform_remote_state e Valori Sensibili

Il data source `terraform_remote_state` permette di leggere gli output di un altro state, abilitando la composizione di progetti separati.

```hcl
data "terraform_remote_state" "networking" {
  backend = "s3"
  config = {
    bucket = "azienda-terraform-state"
    key    = "production/networking/terraform.tfstate"
    region = "eu-west-1"
  }
}

resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.networking.outputs.private_subnet_ids[0]
}
```

Per i valori sensibili, Terraform offre il flag `sensitive` che impedisce la visualizzazione nell'output del plan.

```hcl
variable "db_password" {
  type      = string
  sensitive = true
}

output "db_connection_string" {
  value     = "postgresql://admin:${var.db_password}@${aws_db_instance.main.endpoint}/app"
  sensitive = true
}
```

I segreti non devono mai essere salvati nel codice o nello state in chiaro. Si integrano con sistemi come AWS Secrets Manager, HashiCorp Vault o variabili d'ambiente nella pipeline CI/CD.

### Moved e Removed Blocks

I blocchi `moved` e `removed` sono strumenti dichiarativi per il refactoring sicuro dell'infrastruttura, introdotti rispettivamente in Terraform 1.1 e 1.7.

**Moved Block (Terraform 1.1+)**: registra il rinominazione o lo spostamento di risorse senza ricrearle. Senza `moved`, rinominare una risorsa in HCL causa la distruzione della vecchia e la creazione di una nuova — inaccettabile per risorse stateful come database o volumi.

```hcl
# Prima: la risorsa si chiamava aws_instance.web
# Dopo: rinominata in aws_instance.app_server

resource "aws_instance" "app_server" {
  ami           = data.aws_ami.latest.id
  instance_type = "t3.micro"
}

# Registra la migrazione — Terraform aggiornera lo state
# senza distruggere e ricreare l'istanza
moved {
  from = aws_instance.web
  to   = aws_instance.app_server
}
```

```hcl
# Spostamento di una risorsa in un modulo
moved {
  from = aws_instance.app_server
  to   = module.compute.aws_instance.app_server
}

# Spostamento tra moduli
moved {
  from = module.old_module.aws_s3_bucket.data
  to   = module.new_module.aws_s3_bucket.data
}

# Refactoring da count a for_each
moved {
  from = aws_subnet.private[0]
  to   = aws_subnet.private["eu-west-1a"]
}

moved {
  from = aws_subnet.private[1]
  to   = aws_subnet.private["eu-west-1b"]
}
```

**Removed Block (Terraform 1.7+)**: permette di rimuovere una risorsa dalla gestione di Terraform senza distruggerla nel cloud. Utile quando una risorsa viene trasferita a un altro team, strumento o state.

```hcl
# La risorsa legacy non sara piu gestita da Terraform
# ma non verra distrutta nel cloud
removed {
  from = aws_instance.legacy_server

  lifecycle {
    destroy = false
  }
}
```

Prima dell'introduzione dei `removed` block, la stessa operazione richiedeva il comando imperative `terraform state rm`, che non era tracciabile nel version control. Il vantaggio dei blocchi dichiarativi e che il refactoring e documentato nel codice, revisionabile nel PR, e applicabile da qualsiasi membro del team.

### Funzioni Built-in Avanzate

Terraform offre un ricco set di funzioni built-in per manipolare dati all'interno delle configurazioni. Le piu utili in contesti avanzati:

```hcl
locals {
  # cidrsubnet: calcola subnet CIDR automaticamente
  private_subnets = [
    for i in range(3) : cidrsubnet("10.0.0.0/16", 8, i)
    # Risultato: ["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24"]
  ]

  # flatten: appiattisce liste annidate
  all_security_groups = flatten([
    module.web.security_group_ids,
    module.api.security_group_ids,
  ])

  # try: valuta espressioni con fallback
  instance_type = try(var.overrides[var.environment].instance_type, "t3.micro")

  # one: estrae un singolo elemento da una lista di 0-1 elementi
  primary_subnet = one(aws_subnet.primary[*].id)

  # regex: estrae pattern da stringhe
  account_id = regex("arn:aws:iam::(\\d{12}):", data.aws_caller_identity.current.arn)

  # templatefile: rende un template con variabili
  user_data = templatefile("${path.module}/templates/init.sh.tpl", {
    app_version = var.app_version
    db_endpoint = aws_db_instance.main.endpoint
  })
}
```

---

## Terraform per AWS

Questo esempio pratico mostra come creare un'infrastruttura completa su AWS: VPC con subnets, Security Groups, istanze EC2 dietro un Application Load Balancer, un database RDS e un bucket S3.

```hcl
# ============================================================
# Provider e Backend
# ============================================================
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "azienda-terraform-state"
    key            = "production/app/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
}

# ============================================================
# Variabili
# ============================================================
variable "aws_region" {
  default = "eu-west-1"
}

variable "environment" {
  default = "production"
}

variable "db_password" {
  type      = string
  sensitive = true
}

locals {
  name_prefix = "app-${var.environment}"
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================================
# Networking: VPC, Subnets, Security Groups
# ============================================================
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-${count.index + 1}"
    Tier = "Public"
  })
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-${count.index + 1}"
    Tier = "Private"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.common_tags, { Name = "${local.name_prefix}-igw" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-public-rt" })
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Security Groups
resource "aws_security_group" "alb" {
  name   = "${local.name_prefix}-alb-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_security_group" "app" {
  name   = "${local.name_prefix}-app-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_security_group" "rds" {
  name   = "${local.name_prefix}-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = local.common_tags
}

# ============================================================
# Application Load Balancer
# ============================================================
resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = local.common_tags
}

resource "aws_lb_target_group" "app" {
  name     = "${local.name_prefix}-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    interval            = 30
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# ============================================================
# EC2 Instances
# ============================================================
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "app" {
  count                  = 2
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.private[count.index].id
  vpc_security_group_ids = [aws_security_group.app.id]

  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y docker
    systemctl start docker
    systemctl enable docker
    docker run -d -p 8080:8080 myapp:latest
  EOF

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-app-${count.index + 1}"
  })
}

resource "aws_lb_target_group_attachment" "app" {
  count            = 2
  target_group_arn = aws_lb_target_group.app.arn
  target_id        = aws_instance.app[count.index].id
  port             = 8080
}

# ============================================================
# RDS PostgreSQL
# ============================================================
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet"
  subnet_ids = aws_subnet.private[*].id
  tags       = local.common_tags
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name_prefix}-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage     = 50
  max_allocated_storage = 200
  storage_encrypted     = true

  db_name  = "appdb"
  username = "dbadmin"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az            = true
  skip_final_snapshot = false
  final_snapshot_identifier = "${local.name_prefix}-db-final-snapshot"

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  lifecycle {
    prevent_destroy = true
  }

  tags = local.common_tags
}

# ============================================================
# S3 Bucket per Assets
# ============================================================
resource "aws_s3_bucket" "assets" {
  bucket = "${local.name_prefix}-assets"
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================
# Outputs
# ============================================================
output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "rds_endpoint" {
  value     = aws_db_instance.main.endpoint
  sensitive = true
}
```

---

## Terraform per Azure

Azure richiede il provider `azurerm` e segue una struttura organizzativa basata su Resource Groups. Ecco un esempio sintetico che crea una VNet, una VM e un cluster AKS.

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group — contenitore logico per tutte le risorse
resource "azurerm_resource_group" "main" {
  name     = "rg-app-production-westeurope"
  location = "West Europe"
}

# Virtual Network e Subnet
resource "azurerm_virtual_network" "main" {
  name                = "vnet-app-prod"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_subnet" "app" {
  name                 = "snet-app"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "aks" {
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/22"]
}

# Network Interface e VM
resource "azurerm_network_interface" "vm" {
  name                = "nic-vm-app"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.app.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_linux_virtual_machine" "app" {
  name                = "vm-app-prod"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "Standard_B2s"
  admin_username      = "azureadmin"

  network_interface_ids = [azurerm_network_interface.vm.id]

  admin_ssh_key {
    username   = "azureadmin"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }
}

# Azure Kubernetes Service (AKS)
resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-app-prod"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "aks-app-prod"

  default_node_pool {
    name           = "default"
    node_count     = 3
    vm_size        = "Standard_D2_v5"
    vnet_subnet_id = azurerm_subnet.aks.id
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    service_cidr   = "10.1.0.0/16"
    dns_service_ip = "10.1.0.10"
  }
}

output "aks_kube_config" {
  value     = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive = true
}
```

In Azure, ogni risorsa deve appartenere a un Resource Group. La struttura organizzativa differisce da AWS: dove AWS usa Account e OU, Azure utilizza Management Groups, Subscriptions e Resource Groups. Il provider `azurerm` richiede il blocco `features {}` anche quando vuoto.

---

## Ansible — Fondamenti

### Architettura Agentless

Ansible adotta un'architettura senza agenti (*agentless*): non richiede l'installazione di alcun software sui nodi gestiti. La comunicazione avviene tramite SSH per i sistemi Linux/Unix e WinRM per Windows. Questa scelta architetturale semplifica enormemente l'adozione: qualunque macchina raggiungibile via SSH e immediatamente gestibile con Ansible.

Il nodo di controllo (dove si esegue Ansible) necessita di Python 3 e del pacchetto Ansible. I nodi gestiti necessitano solo di Python (gia presente sulla quasi totalita dei sistemi Linux) e connettivita SSH.

### Inventory: Statico e Dinamico

L'inventory definisce i nodi gestiti e la loro organizzazione in gruppi. L'inventory statico e un file INI o YAML.

```ini
# inventory/production.ini

[webservers]
web01.example.com ansible_host=10.0.1.10
web02.example.com ansible_host=10.0.1.11

[dbservers]
db01.example.com ansible_host=10.0.2.10 ansible_user=dbadmin

[monitoring]
grafana.example.com

[production:children]
webservers
dbservers
monitoring

[webservers:vars]
http_port=8080
max_connections=1000
```

L'inventory dinamico interroga fonti esterne (AWS, Azure, GCP, Consul) per generare l'inventario in tempo reale:

```bash
# Uso del plugin di inventory dinamico AWS
ansible-inventory -i aws_ec2.yml --graph
```

### Comandi Ad-Hoc

I comandi ad-hoc eseguono operazioni singole senza scrivere un playbook. Sono utili per operazioni rapide e troubleshooting.

```bash
# Ping di tutti gli host
ansible all -m ping -i inventory/production.ini

# Verifica lo spazio disco
ansible webservers -m shell -a "df -h" -i inventory/production.ini

# Installa un pacchetto
ansible webservers -m apt -a "name=nginx state=present" -b -i inventory/production.ini

# Riavvia un servizio
ansible webservers -m service -a "name=nginx state=restarted" -b

# Copia un file
ansible all -m copy -a "src=./config.conf dest=/etc/app/config.conf" -b
```

Il flag `-b` (become) esegue il comando con privilegi elevati (sudo). Il flag `-m` specifica il modulo, `-a` gli argomenti.

### Struttura di un Playbook

I playbook sono file YAML che descrivono una sequenza di task organizzati in play. Ogni play seleziona un gruppo di host e definisce i task da eseguire.

```yaml
---
# playbook: deploy-webapp.yml
- name: Configura i web server
  hosts: webservers
  become: true
  vars:
    app_port: 8080
    app_version: "2.1.0"
    deploy_dir: /opt/webapp

  pre_tasks:
    - name: Aggiorna la cache dei pacchetti
      apt:
        update_cache: true
        cache_valid_time: 3600

  tasks:
    - name: Installa le dipendenze
      apt:
        name:
          - nginx
          - python3
          - python3-pip
        state: present

    - name: Crea la directory dell'applicazione
      file:
        path: "{{ deploy_dir }}"
        state: directory
        owner: www-data
        group: www-data
        mode: '0755'

    - name: Distribuisci la configurazione Nginx
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/sites-available/webapp.conf
        owner: root
        group: root
        mode: '0644'
      notify: Ricarica Nginx

    - name: Abilita il sito Nginx
      file:
        src: /etc/nginx/sites-available/webapp.conf
        dest: /etc/nginx/sites-enabled/webapp.conf
        state: link
      notify: Ricarica Nginx

    - name: Assicurati che Nginx sia avviato
      service:
        name: nginx
        state: started
        enabled: true

  handlers:
    - name: Ricarica Nginx
      service:
        name: nginx
        state: reloaded
```

I **handlers** sono task speciali che vengono eseguiti solo quando notificati da un task che ha effettuato un cambiamento. Se il template non cambia, il handler non viene attivato — un esempio pratico di idempotenza.

### Moduli Principali

Ansible offre migliaia di moduli. I piu utilizzati:

- **`command`**: esegue comandi senza shell (piu sicuro, non supporta pipe e redirect)
- **`shell`**: esegue comandi tramite shell (supporta pipe, redirect, variabili d'ambiente)
- **`copy`**: copia file dal nodo di controllo ai nodi gestiti
- **`template`**: processa template Jinja2 e distribuisce il risultato
- **`service`** / **`systemd`**: gestisce servizi (start, stop, restart, enable)
- **`apt`** / **`yum`** / **`dnf`**: gestione pacchetti per Debian/RHEL
- **`user`**: gestione utenti (creazione, modifica, eliminazione)
- **`file`**: gestione file e directory (permessi, proprietario, link simbolici)
- **`lineinfile`**: modifica singole righe in file di configurazione
- **`git`**: operazioni Git (clone, pull)

---

## Ansible — Avanzato

### Struttura dei Roles

I roles organizzano playbook complessi in componenti riutilizzabili con una struttura di directory convenzionale.

```
roles/
  nginx/
    tasks/
      main.yml          # Task principali
      install.yml        # Task di installazione
      configure.yml      # Task di configurazione
    handlers/
      main.yml          # Handlers
    templates/
      nginx.conf.j2     # Template Jinja2
      vhost.conf.j2
    files/
      ssl-params.conf   # File statici
    vars/
      main.yml          # Variabili del ruolo (alta priorita)
    defaults/
      main.yml          # Variabili di default (bassa priorita, sovrascrivibili)
    meta/
      main.yml          # Metadati e dipendenze
    tests/
      test.yml          # Playbook di test
```

Utilizzo del ruolo in un playbook:

```yaml
---
- name: Configura il web tier
  hosts: webservers
  become: true

  roles:
    - role: common
    - role: nginx
      vars:
        nginx_worker_processes: 4
        nginx_worker_connections: 2048
    - role: app_deploy
      vars:
        app_version: "{{ lookup('env', 'APP_VERSION') }}"
```

### Ansible Galaxy

Ansible Galaxy e il repository pubblico di roles e collections condivise dalla community. Si utilizza tramite il comando `ansible-galaxy`.

```bash
# Installa un ruolo da Galaxy
ansible-galaxy install geerlingguy.docker

# Installa ruoli da un requirements file
ansible-galaxy install -r requirements.yml

# Inizializza la struttura di un nuovo ruolo
ansible-galaxy init my_custom_role
```

```yaml
# requirements.yml
---
roles:
  - name: geerlingguy.docker
    version: "6.1.0"
  - name: geerlingguy.certbot
    version: "5.0.0"

collections:
  - name: amazon.aws
    version: ">=6.0.0"
  - name: community.general
    version: ">=7.0.0"
```

### Ansible Vault

Ansible Vault cifra file e variabili sensibili (password, chiavi API, certificati) all'interno del progetto.

```bash
# Crea un file cifrato
ansible-vault create secrets.yml

# Cifra un file esistente
ansible-vault encrypt vars/production_secrets.yml

# Modifica un file cifrato
ansible-vault edit secrets.yml

# Esegui un playbook con vault
ansible-playbook deploy.yml --ask-vault-pass
ansible-playbook deploy.yml --vault-password-file ~/.vault_pass
```

```yaml
# group_vars/production/vault.yml (cifrato)
---
vault_db_password: "SuperSecretPassword123!"
vault_api_key: "sk-abcdef123456"
vault_ssl_private_key: |
  -----BEGIN RSA PRIVATE KEY-----
  MIIEpAIBAAKCAQEA...
  -----END RSA PRIVATE KEY-----
```

### Inventory Dinamico per AWS e Azure

L'inventory dinamico interroga le API del cloud provider per scoprire automaticamente le istanze.

```yaml
# aws_ec2.yml - Plugin di inventory dinamico AWS
---
plugin: amazon.aws.aws_ec2
regions:
  - eu-west-1
  - eu-central-1

keyed_groups:
  - key: tags.Environment
    prefix: env
  - key: instance_type
    prefix: type
  - key: placement.availability_zone
    prefix: az

filters:
  instance-state-name: running
  "tag:ManagedBy": "Ansible"

compose:
  ansible_host: private_ip_address
```

```yaml
# azure_rm.yml - Plugin di inventory dinamico Azure
---
plugin: azure.azcollection.azure_rm
auth_source: auto
include_vm_resource_groups:
  - rg-app-production
keyed_groups:
  - prefix: tag
    key: tags
```

### Template Jinja2

I template Jinja2 generano file di configurazione dinamici basati su variabili e logica.

```jinja2
{# templates/nginx.conf.j2 #}
worker_processes {{ nginx_worker_processes | default(ansible_processor_vcpus) }};

events {
    worker_connections {{ nginx_worker_connections | default(1024) }};
}

http {
    upstream app_backend {
    {% for host in groups['appservers'] %}
        server {{ hostvars[host]['ansible_host'] }}:{{ app_port }};
    {% endfor %}
    }

    server {
        listen 80;
        server_name {{ server_name }};

    {% if ssl_enabled | default(false) %}
        listen 443 ssl;
        ssl_certificate     {{ ssl_cert_path }};
        ssl_certificate_key {{ ssl_key_path }};
    {% endif %}

        location / {
            proxy_pass http://app_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### Condizionali, Loop, Tag e Gestione Errori

```yaml
---
- name: Esempio avanzato di task Ansible
  hosts: all
  become: true

  tasks:
    # Condizionale con when
    - name: Installa pacchetti per Debian/Ubuntu
      apt:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - python3
        - htop
      when: ansible_os_family == "Debian"
      tags:
        - packages
        - setup

    # Condizionale con when per RedHat
    - name: Installa pacchetti per RedHat/CentOS
      yum:
        name: "{{ item }}"
        state: present
      loop:
        - nginx
        - python3
        - htop
      when: ansible_os_family == "RedHat"
      tags:
        - packages
        - setup

    # Loop con dizionari
    - name: Crea utenti di sistema
      user:
        name: "{{ item.name }}"
        groups: "{{ item.groups }}"
        shell: "{{ item.shell | default('/bin/bash') }}"
        state: present
      loop:
        - { name: "deployer", groups: "www-data,docker" }
        - { name: "monitor", groups: "adm", shell: "/usr/sbin/nologin" }
      tags:
        - users

    # Gestione errori con block/rescue/always
    - name: Deploy dell'applicazione con rollback
      block:
        - name: Scarica il nuovo artefatto
          get_url:
            url: "https://releases.example.com/app-{{ app_version }}.tar.gz"
            dest: "/tmp/app-{{ app_version }}.tar.gz"

        - name: Estrai l'artefatto
          unarchive:
            src: "/tmp/app-{{ app_version }}.tar.gz"
            dest: "{{ deploy_dir }}"
            remote_src: true

        - name: Riavvia l'applicazione
          systemd:
            name: webapp
            state: restarted

      rescue:
        - name: Rollback alla versione precedente
          command: "ln -sfn {{ deploy_dir }}/releases/{{ previous_version }} {{ deploy_dir }}/current"

        - name: Notifica il fallimento
          slack:
            token: "{{ slack_token }}"
            channel: "#deploy"
            msg: "FALLITO il deploy della versione {{ app_version }}. Rollback eseguito."

      always:
        - name: Pulizia file temporanei
          file:
            path: "/tmp/app-{{ app_version }}.tar.gz"
            state: absent
      tags:
        - deploy
```

I **tag** permettono di eseguire selettivamente parti del playbook: `ansible-playbook deploy.yml --tags "deploy"` esegue solo i task con il tag "deploy".

I **callback plugins** estendono il comportamento di Ansible per personalizzare l'output, inviare notifiche o integrare sistemi di monitoraggio. Ad esempio, il plugin `profile_tasks` mostra il tempo di esecuzione di ogni task, `json` formatta l'output in JSON per l'integrazione con pipeline, e `slack` invia notifiche a canali Slack al termine dell'esecuzione.

---

## Ansible per Server

### Hardening di un Server Linux

Questo playbook implementa le pratiche fondamentali di sicurezza su un server Linux.

```yaml
---
# playbook: hardening-linux.yml
- name: Hardening del server Linux
  hosts: all
  become: true
  vars:
    ssh_port: 2222
    allowed_ssh_users:
      - deployer
      - sysadmin
    sysctl_settings:
      net.ipv4.ip_forward: 0
      net.ipv4.conf.all.send_redirects: 0
      net.ipv4.conf.default.accept_redirects: 0
      net.ipv4.conf.all.accept_source_route: 0
      net.ipv4.tcp_syncookies: 1
      net.ipv6.conf.all.disable_ipv6: 1

  tasks:
    - name: Aggiorna tutti i pacchetti
      apt:
        upgrade: dist
        update_cache: true
      tags: updates

    - name: Installa pacchetti di sicurezza
      apt:
        name:
          - ufw
          - fail2ban
          - unattended-upgrades
          - auditd
          - aide
          - rkhunter
        state: present
      tags: security-packages

    - name: Configura SSH hardening
      template:
        src: templates/sshd_config.j2
        dest: /etc/ssh/sshd_config
        owner: root
        group: root
        mode: '0600'
        validate: '/usr/sbin/sshd -t -f %s'
      notify: Riavvia SSH
      tags: ssh

    - name: Applica impostazioni sysctl
      sysctl:
        name: "{{ item.key }}"
        value: "{{ item.value }}"
        sysctl_set: true
        state: present
        reload: true
      loop: "{{ sysctl_settings | dict2items }}"
      tags: kernel

    - name: Configura il firewall UFW
      block:
        - name: Imposta policy di default (deny incoming)
          ufw:
            direction: incoming
            policy: deny

        - name: Permetti SSH sulla porta personalizzata
          ufw:
            rule: allow
            port: "{{ ssh_port }}"
            proto: tcp

        - name: Permetti HTTP e HTTPS
          ufw:
            rule: allow
            port: "{{ item }}"
            proto: tcp
          loop:
            - "80"
            - "443"

        - name: Abilita il firewall
          ufw:
            state: enabled
      tags: firewall

    - name: Disabilita servizi non necessari
      systemd:
        name: "{{ item }}"
        state: stopped
        enabled: false
      loop:
        - avahi-daemon
        - cups
        - rpcbind
      ignore_errors: true
      tags: services

    - name: Configura fail2ban per SSH
      template:
        src: templates/jail.local.j2
        dest: /etc/fail2ban/jail.local
      notify: Riavvia fail2ban
      tags: fail2ban

    - name: Imposta permessi restrittivi su cron
      file:
        path: "{{ item }}"
        owner: root
        group: root
        mode: '0600'
      loop:
        - /etc/crontab
        - /etc/cron.hourly
        - /etc/cron.daily
        - /etc/cron.weekly
        - /etc/cron.monthly
      tags: permissions

    - name: Configura password policy
      lineinfile:
        path: /etc/login.defs
        regexp: "^{{ item.key }}"
        line: "{{ item.key }} {{ item.value }}"
      loop:
        - { key: "PASS_MAX_DAYS", value: "90" }
        - { key: "PASS_MIN_DAYS", value: "7" }
        - { key: "PASS_MIN_LEN", value: "14" }
        - { key: "PASS_WARN_AGE", value: "14" }
      tags: password-policy

  handlers:
    - name: Riavvia SSH
      systemd:
        name: sshd
        state: restarted

    - name: Riavvia fail2ban
      systemd:
        name: fail2ban
        state: restarted
```

### Gestione Server Windows

Ansible gestisce server Windows attraverso WinRM e moduli dedicati con prefisso `win_`.

```yaml
---
# playbook: configure-windows.yml
- name: Configura server Windows
  hosts: windows_servers
  vars:
    ansible_connection: winrm
    ansible_winrm_transport: kerberos

  tasks:
    - name: Installa IIS
      win_feature:
        name: Web-Server
        state: present
        include_sub_features: true
        include_management_tools: true
      tags: iis

    - name: Crea directory per l'applicazione
      win_file:
        path: C:\inetpub\webapp
        state: directory

    - name: Distribuisci la configurazione del sito
      win_template:
        src: templates/web.config.j2
        dest: C:\inetpub\webapp\web.config

    - name: Assicurati che il servizio W3SVC sia avviato
      win_service:
        name: W3SVC
        state: started
        start_mode: auto

    - name: Installa pacchetti Chocolatey
      win_chocolatey:
        name:
          - dotnet-runtime
          - notepadplusplus
          - 7zip
        state: present

    - name: Configura Windows Firewall
      win_firewall_rule:
        name: "Allow HTTP"
        localport: 80
        action: allow
        direction: in
        protocol: tcp
        state: present
        enabled: true

    - name: Esegui script PowerShell
      win_shell: |
        Get-WindowsFeature | Where-Object {$_.Installed -eq $true} |
        Select-Object Name, InstallState |
        Export-Csv C:\reports\installed_features.csv
      tags: audit

    - name: Copia file sul server
      win_copy:
        src: files/app-config.json
        dest: C:\inetpub\webapp\app-config.json

    - name: Gestisci utenti locali
      win_user:
        name: svc_webapp
        password: "{{ vault_svc_password }}"
        state: present
        groups:
          - IIS_IUSRS
        password_never_expires: true
```

---

## Pulumi

### Panoramica: IaC con Linguaggi di Programmazione Reali

Pulumi rappresenta un approccio alternativo all'IaC che utilizza linguaggi di programmazione generici — Python, TypeScript, Go, C#, Java — al posto di linguaggi domain-specific come HCL. Questo permette di sfruttare l'intero ecosistema del linguaggio scelto: IDE con autocompletamento avanzato, librerie di testing, costrutti di programmazione standard (condizionali, cicli, classi, funzioni), e package manager.

**Esempio in Python:**

```python
import pulumi
import pulumi_aws as aws

# Crea una VPC
vpc = aws.ec2.Vpc("main-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    tags={"Name": "main-vpc", "Environment": "production"}
)

# Crea subnets con un loop Python nativo
azs = ["eu-west-1a", "eu-west-1b"]
subnets = []
for i, az in enumerate(azs):
    subnet = aws.ec2.Subnet(f"subnet-{i}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i+1}.0/24",
        availability_zone=az,
        tags={"Name": f"subnet-{az}"}
    )
    subnets.append(subnet)

# Crea un security group con logica condizionale
is_production = pulumi.Config().get_bool("isProduction") or False

sg = aws.ec2.SecurityGroup("web-sg",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
        ),
        # SSH solo in non-produzione
        *([aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["10.0.0.0/8"],
        )] if not is_production else []),
    ]
)

# Esporta gli output
pulumi.export("vpc_id", vpc.id)
pulumi.export("subnet_ids", [s.id for s in subnets])
```

**Esempio in TypeScript:**

```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const vpc = new aws.ec2.Vpc("main-vpc", {
    cidrBlock: "10.0.0.0/16",
    enableDnsHostnames: true,
    tags: { Name: "main-vpc" },
});

const subnets = ["eu-west-1a", "eu-west-1b"].map((az, index) =>
    new aws.ec2.Subnet(`subnet-${index}`, {
        vpcId: vpc.id,
        cidrBlock: `10.0.${index + 1}.0/24`,
        availabilityZone: az,
    })
);

export const vpcId = vpc.id;
export const subnetIds = subnets.map(s => s.id);
```

### Confronto con Terraform

| Aspetto | Terraform | Pulumi |
|---------|-----------|--------|
| **Linguaggio** | HCL (domain-specific) | Python, TypeScript, Go, C#, Java |
| **State** | File JSON (S3, Terraform Cloud) | Pulumi Service, S3, locale |
| **Curva di apprendimento** | Richiede apprendimento di HCL | Usa linguaggi gia noti agli sviluppatori |
| **Testing** | Limitato (terratest in Go) | Testing nativo del linguaggio (pytest, jest) |
| **Ecosistema** | Vastissimo, maturo, standard de facto | In crescita, ottima copertura cloud |
| **IDE support** | Buono (plugin HCL) | Eccellente (autocompletamento nativo) |
| **Logica complessa** | Possibile ma verbosa (for_each, dynamic) | Naturale con costrutti del linguaggio |
| **Community** | Enorme, standard industriale | Piu piccola ma in rapida crescita |

La scelta tra Terraform e Pulumi dipende dal contesto del team: se il team e composto da sviluppatori che preferiscono lavorare nel loro linguaggio abituale, Pulumi offre un'esperienza piu naturale. Se il team opera in un ambiente enterprise dove Terraform e lo standard, la familiarita e l'ecosistema di Terraform sono vantaggi significativi.

---

## CloudFormation e Bicep

### AWS CloudFormation

CloudFormation e il servizio nativo di AWS per l'IaC. Utilizza template JSON o YAML per dichiarare le risorse AWS. Il vantaggio principale e l'integrazione profonda con l'ecosistema AWS: supporto immediato per nuovi servizi, drift detection nativa, integrazione con AWS Organizations e Service Catalog.

```yaml
# cloudformation-template.yml
AWSTemplateFormatVersion: '2010-09-09'
Description: Stack applicativo con VPC, EC2 e RDS

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, production]
    Default: dev
  InstanceType:
    Type: String
    Default: t3.micro

Resources:
  AppVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub "${Environment}-vpc"

  WebInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Ref InstanceType
      ImageId: !FindInMap [RegionAMI, !Ref "AWS::Region", HVM64]
      SubnetId: !Ref PublicSubnet
      Tags:
        - Key: Name
          Value: !Sub "${Environment}-web"

Outputs:
  VPCId:
    Value: !Ref AppVPC
    Export:
      Name: !Sub "${Environment}-VPCId"
```

Lo svantaggio principale di CloudFormation e il vendor lock-in: funziona esclusivamente con AWS. Inoltre, la sintassi e piu verbosa rispetto a Terraform e le funzionalita di modularizzazione (Nested Stacks, StackSets) sono meno flessibili dei moduli Terraform.

### Azure Bicep

Bicep e il linguaggio domain-specific di Azure per l'IaC, concepito come evoluzione dei template ARM (Azure Resource Manager). Offre una sintassi piu pulita e leggibile rispetto ai template ARM JSON.

```bicep
// main.bicep
param location string = resourceGroup().location
param environment string = 'production'

var namePrefix = 'app-${environment}'

resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: '${namePrefix}-vnet'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.0.0.0/16']
    }
    subnets: [
      {
        name: 'app-subnet'
        properties: {
          addressPrefix: '10.0.1.0/24'
        }
      }
    ]
  }
}

resource aks 'Microsoft.ContainerService/managedClusters@2023-08-01' = {
  name: '${namePrefix}-aks'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    dnsPrefix: '${namePrefix}-aks'
    agentPoolProfiles: [
      {
        name: 'default'
        count: 3
        vmSize: 'Standard_D2_v5'
        vnetSubnetID: vnet.properties.subnets[0].id
        mode: 'System'
      }
    ]
  }
}

output aksClusterName string = aks.name
```

Come CloudFormation per AWS, Bicep e specifico per Azure. La scelta fra strumenti nativi e multi-cloud (Terraform/Pulumi) dipende dalla strategia cloud dell'organizzazione: se si opera esclusivamente su un singolo cloud, gli strumenti nativi offrono integrazione superiore; se si adotta o si prevede una strategia multi-cloud, Terraform o Pulumi garantiscono uniformita.

---

## OpenTofu — Il Fork Open-Source

### Storia e Motivazioni

Nel agosto 2023, HashiCorp ha cambiato la licenza di Terraform dalla Mozilla Public License 2.0 (MPL) alla Business Source License 1.1 (BSL), una licenza non open-source che limita l'uso commerciale competitivo. La decisione ha provocato una reazione immediata dalla community: in poche settimane, un consorzio di aziende e contributori ha lanciato il progetto OpenTofu sotto la Linux Foundation, effettuando un fork del codice Terraform alla versione 1.5.7 (l'ultima sotto MPL).

OpenTofu ha rapidamente raggiunto la maturita: la versione 1.6 (dicembre 2023) ha stabilito la compatibilita con Terraform 1.6, la 1.7 ha introdotto la cifratura client-side dello state, e la 1.8 (2024) ha aggiunto funzionalita innovative come provider-defined functions e early variable evaluation — feature non ancora presenti in Terraform al momento del rilascio.

### Differenze Chiave con Terraform

La divergenza tra OpenTofu e Terraform si sta ampliando progressivamente. Alcune differenze significative:

**Cifratura Client-Side dello State (OpenTofu 1.7+)**:

OpenTofu supporta la cifratura dello state file lato client, una funzionalita a lungo richiesta dalla community e mai implementata in Terraform. Questo permette di cifrare lo state prima che venga scritto nel backend remoto, proteggendo i segreti anche in caso di compromissione del backend.

```hcl
# Configurazione della cifratura dello state in OpenTofu
terraform {
  encryption {
    key_provider "pbkdf2" "state_key" {
      passphrase = var.state_encryption_passphrase
    }

    method "aes_gcm" "state_encryption" {
      keys = key_provider.pbkdf2.state_key
    }

    state {
      method   = method.aes_gcm.state_encryption
      enforced = true
    }

    plan {
      method   = method.aes_gcm.state_encryption
      enforced = true
    }
  }
}
```

**Provider-Defined Functions (OpenTofu 1.8+)**:

I provider possono esporre funzioni personalizzate utilizzabili direttamente nel codice HCL, estendendo il linguaggio senza modificare il core di OpenTofu.

```hcl
# Esempio: funzione definita dal provider AWS
locals {
  decoded_arn = provider::aws::arn_parse(aws_iam_role.example.arn)
  account_id  = local.decoded_arn.account_id
}
```

**Early Variable and Local Evaluation (OpenTofu 1.8+)**:

Le variabili e i locals vengono valutati prima della fase di inizializzazione dei provider, permettendo di usarli nella configurazione del backend e dei provider stessi — un limite storico di Terraform.

```hcl
variable "environment" {
  type = string
}

# In OpenTofu 1.8+, le variabili possono essere usate nel backend
terraform {
  backend "s3" {
    bucket = "state-${var.environment}"  # Non possibile in Terraform
    key    = "terraform.tfstate"
    region = "eu-west-1"
  }
}
```

### Migrazione da Terraform a OpenTofu

La migrazione e generalmente diretta per le versioni fino a Terraform 1.5.x:

```bash
# 1. Installare OpenTofu
curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh \
  | sh -s -- --install-method deb

# 2. Verificare la versione
tofu version

# 3. Nel progetto Terraform, sostituire il binario
# I file .tf sono identici, nessuna modifica richiesta
tofu init
tofu plan

# 4. Per lo state, il formato e compatibile
# Lo state esistente funziona senza modifiche
```

Per le versioni successive alla divergenza (Terraform 1.6+ vs OpenTofu 1.7+), verificare la compatibilita delle funzionalita utilizzate — feature specifiche di una piattaforma non sono disponibili nell'altra.

### Quando Scegliere OpenTofu

- **Requisito di licenza open-source**: OpenTofu sotto MPL 2.0 e utilizzabile senza restrizioni commerciali
- **Cifratura dello state**: se la cifratura client-side e un requisito, OpenTofu e l'unica opzione nativa
- **Vendor neutrality**: la governance sotto Linux Foundation garantisce indipendenza dal singolo vendor
- **Early adoption**: team che vogliono accesso anticipato a funzionalita innovative come provider-defined functions

**Quando restare su Terraform**:
- Ecosistema enterprise consolidato con Terraform Cloud/Enterprise
- Dipendenza da Sentinel policy (non supportato in OpenTofu, che usa OPA/Rego)
- Team con formazione e certificazioni HashiCorp esistenti

---

## Pulumi — Approfondimento

### Automation API

L'Automation API di Pulumi permette di eseguire operazioni IaC (up, preview, destroy, refresh) da codice applicativo, senza invocare la CLI. Questo abilita scenari avanzati come piattaforme self-service, provisioning on-demand e integrazione in applicazioni web.

```python
# automation_api_example.py
import pulumi
from pulumi import automation as auto
import pulumi_aws as aws


def create_infrastructure():
    """Programma Pulumi eseguito dall'Automation API."""
    bucket = aws.s3.Bucket("auto-bucket",
        tags={"Environment": "ephemeral", "CreatedBy": "automation-api"}
    )
    pulumi.export("bucket_name", bucket.id)
    pulumi.export("bucket_arn", bucket.arn)


# Crea o seleziona lo stack
stack = auto.create_or_select_stack(
    stack_name="ephemeral-env",
    project_name="self-service",
    program=create_infrastructure
)

# Configura il provider
stack.set_config("aws:region", auto.ConfigValue(value="eu-west-1"))

# Preview (equivalente a `pulumi preview`)
preview_result = stack.preview(on_output=print)
print(f"Risorse da creare: {preview_result.change_summary.get('create', 0)}")

# Deploy (equivalente a `pulumi up`)
up_result = stack.up(on_output=print)
print(f"Bucket creato: {up_result.outputs['bucket_name'].value}")

# Destroy quando l'ambiente non serve piu
# stack.destroy(on_output=print)
# stack.workspace.remove_stack("ephemeral-env")
```

Casi d'uso dell'Automation API:

- **Piattaforme self-service**: un'applicazione web che permette agli sviluppatori di creare ambienti di sviluppo on-demand
- **Testing E2E**: creazione di infrastruttura effimera per test di integrazione, distrutta al termine
- **Multi-tenancy**: provisioning automatico di infrastruttura per ogni nuovo tenant di un'applicazione SaaS

### State Backend di Pulumi

Pulumi supporta diversi backend per lo state:

```bash
# Pulumi Cloud (default, gestito)
pulumi login

# S3-compatible (auto-gestito)
pulumi login s3://my-pulumi-state-bucket

# Azure Blob Storage
pulumi login azblob://my-pulumi-state-container

# Google Cloud Storage
pulumi login gs://my-pulumi-state-bucket

# File system locale (solo sviluppo)
pulumi login file://~/.pulumi-state
```

A differenza di Terraform, Pulumi Cloud offre funzionalita integrate come la visualizzazione della storia dei deployment, la gestione dei segreti con cifratura per-stack, e il supporto per team e organizzazioni con RBAC.

### CrossGuard — Policy as Code

CrossGuard e il framework di policy di Pulumi, scritto nello stesso linguaggio del programma Pulumi. Le policy vengono valutate durante preview e update, bloccando le risorse non conformi prima del deployment.

```python
# policy_pack/__main__.py
from pulumi_policy import (
    EnforcementLevel,
    PolicyPack,
    ResourceValidationPolicy,
)

def no_public_s3(args, report_violation):
    if args.resource_type == "aws:s3/bucket:Bucket":
        acl = args.props.get("acl")
        if acl and acl in ["public-read", "public-read-write"]:
            report_violation(
                "I bucket S3 non devono avere ACL pubbliche. "
                f"Trovato: acl={acl}"
            )

def require_encryption(args, report_violation):
    if args.resource_type == "aws:s3/bucket:Bucket":
        sse = args.props.get("serverSideEncryptionConfiguration")
        if not sse:
            report_violation(
                "I bucket S3 devono avere la server-side encryption configurata."
            )

PolicyPack(
    name="security-policies",
    enforcement_level=EnforcementLevel.MANDATORY,
    policies=[
        ResourceValidationPolicy(
            name="no-public-s3-buckets",
            description="Impedisce la creazione di bucket S3 con accesso pubblico",
            validate=no_public_s3,
        ),
        ResourceValidationPolicy(
            name="require-s3-encryption",
            description="Richiede encryption su tutti i bucket S3",
            validate=require_encryption,
        ),
    ],
)
```

```bash
# Applica il policy pack durante il deployment
pulumi up --policy-pack ./policy_pack

# Pubblica il policy pack per uso organizzativo
pulumi policy publish ./policy_pack
```

### Testing con Linguaggi Nativi

Il vantaggio principale di Pulumi e la possibilita di testare l'infrastruttura con i framework di test standard del linguaggio scelto, senza dipendenze esterne come Terratest.

**Unit test in Python con pytest:**

```python
# test_infrastructure.py
import pulumi
import pytest


class MockedMixin:
    """Mixin per mockare le risorse Pulumi nei test."""

    def __init__(self, resource_type, name, props):
        self.resource_type = resource_type
        self.name = name
        self.props = props


# Mock del runtime Pulumi
pulumi.runtime.set_mocks(
    pulumi.runtime.MockMonitor(
        resources={},
        calls={},
    )
)

# Importa il modulo dopo aver configurato i mock
import infra  # il programma Pulumi da testare


@pulumi.runtime.test
def test_bucket_has_encryption():
    """Verifica che il bucket S3 abbia encryption abilitata."""
    def check_encryption(args):
        sse = args.get("serverSideEncryptionConfiguration")
        assert sse is not None, "Il bucket deve avere SSE configurata"

    return infra.bucket.server_side_encryption_configuration.apply(check_encryption)


@pulumi.runtime.test
def test_bucket_is_private():
    """Verifica che il bucket S3 non sia pubblico."""
    def check_acl(args):
        assert args != "public-read", "Il bucket non deve essere pubblico"

    return infra.bucket.acl.apply(check_acl)
```

---

## Crossplane — IaC Kubernetes-Native

### Architettura e Filosofia

Crossplane e un framework CNCF (Graduated nel 2025) che estende Kubernetes per gestire infrastruttura cloud attraverso Custom Resource Definitions (CRD) e controller di riconciliazione. A differenza di Terraform, che opera con un ciclo plan/apply manuale, Crossplane implementa un loop di riconciliazione continua: il controller verifica costantemente che lo stato reale dell'infrastruttura corrisponda allo stato dichiarato nei manifest Kubernetes.

Lo state in Crossplane e archiviato in etcd (il database di Kubernetes), eliminando la necessita di gestire file di state separati, backend remoti o meccanismi di locking — tutto e gestito nativamente da Kubernetes.

### Installazione e Provider

```bash
# Installazione di Crossplane nel cluster Kubernetes
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update

helm install crossplane crossplane-stable/crossplane \
  --namespace crossplane-system \
  --create-namespace

# Verifica l'installazione
kubectl get pods -n crossplane-system
```

```yaml
# Installazione del provider AWS
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws-ec2
spec:
  package: xpkg.upbound.io/upbound/provider-aws-ec2:v1.14.0

---
# Configurazione delle credenziali del provider
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-credentials
      key: credentials
```

### Managed Resources

Le Managed Resources sono la rappresentazione Kubernetes 1:1 delle risorse cloud. Ogni risorsa cloud corrisponde a un CRD.

```yaml
# Creazione di un bucket S3 come risorsa gestita Crossplane
apiVersion: s3.aws.upbound.io/v1beta2
kind: Bucket
metadata:
  name: app-data-bucket
spec:
  forProvider:
    region: eu-west-1
    tags:
      Environment: production
      ManagedBy: Crossplane
  providerConfigRef:
    name: default

---
# Creazione di un VPC
apiVersion: ec2.aws.upbound.io/v1beta1
kind: VPC
metadata:
  name: production-vpc
spec:
  forProvider:
    region: eu-west-1
    cidrBlock: "10.0.0.0/16"
    enableDnsHostnames: true
    enableDnsSupport: true
    tags:
      Name: production-vpc
```

### Compositions e XRDs — Astrazione di Livello Superiore

Le Compositions definiscono come assemblare piu Managed Resources in un'unica astrazione. Le CompositeResourceDefinitions (XRD) definiscono lo schema della risorsa composita.

```yaml
# XRD: definisce il contratto della risorsa composita
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xnetworks.infra.example.com
spec:
  group: infra.example.com
  names:
    kind: XNetwork
    plural: xnetworks
  claimNames:
    kind: Network
    plural: networks
  versions:
    - name: v1alpha1
      served: true
      referenceable: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                region:
                  type: string
                  default: eu-west-1
                vpcCidr:
                  type: string
                  default: "10.0.0.0/16"
                subnetCount:
                  type: integer
                  default: 2
              required:
                - region

---
# Composition: implementazione della risorsa composita
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xnetworks-aws
spec:
  compositeTypeRef:
    apiVersion: infra.example.com/v1alpha1
    kind: XNetwork
  resources:
    - name: vpc
      base:
        apiVersion: ec2.aws.upbound.io/v1beta1
        kind: VPC
        spec:
          forProvider:
            enableDnsHostnames: true
            enableDnsSupport: true
      patches:
        - fromFieldPath: spec.region
          toFieldPath: spec.forProvider.region
        - fromFieldPath: spec.vpcCidr
          toFieldPath: spec.forProvider.cidrBlock

    - name: subnet-a
      base:
        apiVersion: ec2.aws.upbound.io/v1beta1
        kind: Subnet
        spec:
          forProvider:
            cidrBlock: "10.0.1.0/24"
            mapPublicIpOnLaunch: false
      patches:
        - fromFieldPath: spec.region
          toFieldPath: spec.forProvider.region
        - type: CombineFromComposite
          combine:
            variables:
              - fromFieldPath: spec.region
            strategy: string
            string:
              fmt: "%sa"
          toFieldPath: spec.forProvider.availabilityZone
```

### Utilizzo della Risorsa Composita

Una volta definiti XRD e Composition, gli utenti della piattaforma possono creare infrastruttura con un manifest semplificato senza conoscere i dettagli implementativi.

```yaml
# Claim: l'utente richiede una rete senza conoscere i dettagli
apiVersion: infra.example.com/v1alpha1
kind: Network
metadata:
  name: team-alpha-network
  namespace: team-alpha
spec:
  region: eu-west-1
  vpcCidr: "10.10.0.0/16"
  subnetCount: 3
```

### Crossplane vs Terraform — Quando Usare Cosa

| Criterio | Crossplane | Terraform/OpenTofu |
|----------|------------|--------------------|
| **Riconciliazione** | Continua (controller loop) | On-demand (plan/apply) |
| **State** | etcd (Kubernetes) | File JSON (backend remoto) |
| **Drift correction** | Automatica | Richiede plan/apply manuale |
| **Curva di apprendimento** | Richiede Kubernetes | Indipendente da Kubernetes |
| **GitOps** | Nativo (ArgoCD, Flux) | Richiede wrapper (Atlantis) |
| **Ecosistema** | In crescita, meno provider | Maturo, vastissimo |
| **Platform engineering** | Eccellente (XRD/Composition) | Moduli (meno self-service) |
| **Debug** | `kubectl describe` + eventi K8s | `terraform plan` + log |

Crossplane eccelle quando il team ha gia investito in Kubernetes e vuole un modello operativo unificato per applicazioni e infrastruttura. Terraform resta la scelta migliore per team che non operano in contesto Kubernetes o che necessitano dell'ecosistema di provider piu vasto disponibile.

---

## CI/CD per IaC

### Pipeline GitHub Actions

L'automazione della pipeline IaC e fondamentale per garantire qualita, sicurezza e tracciabilita delle modifiche infrastrutturali. Una pipeline tipica prevede le fasi di lint, plan e apply.

```yaml
# .github/workflows/terraform.yml
name: Terraform CI/CD

on:
  pull_request:
    branches: [main]
    paths: ['infrastructure/**']
  push:
    branches: [main]
    paths: ['infrastructure/**']

permissions:
  contents: read
  pull-requests: write
  id-token: write

env:
  TF_VERSION: "1.6.0"
  WORKING_DIR: "infrastructure/production"

jobs:
  lint:
    name: Lint e Validazione
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        working-directory: infrastructure/

      - name: Terraform Init
        run: terraform init -backend=false
        working-directory: ${{ env.WORKING_DIR }}

      - name: Terraform Validate
        run: terraform validate
        working-directory: ${{ env.WORKING_DIR }}

      - name: tflint
        uses: terraform-linters/setup-tflint@v4
        with:
          tflint_version: latest
      - run: |
          tflint --init
          tflint --recursive
        working-directory: infrastructure/

      - name: Checkov Security Scan
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: ${{ env.WORKING_DIR }}
          framework: terraform
          quiet: true

  plan:
    name: Terraform Plan
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        run: terraform init
        working-directory: ${{ env.WORKING_DIR }}

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -out=tfplan
        working-directory: ${{ env.WORKING_DIR }}

      - name: Commenta il PR con il piano
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const plan = `${{ steps.plan.outputs.stdout }}`;
            const truncatedPlan = plan.length > 60000
              ? plan.substring(0, 60000) + "\n\n... (troncato)"
              : plan;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `### Piano Terraform\n\n\`\`\`\n${truncatedPlan}\n\`\`\``
            });

      - name: Salva il piano come artefatto
        uses: actions/upload-artifact@v4
        with:
          name: tfplan
          path: ${{ env.WORKING_DIR }}/tfplan

  apply:
    name: Terraform Apply
    needs: plan
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Scarica il piano
        uses: actions/download-artifact@v4
        with:
          name: tfplan
          path: ${{ env.WORKING_DIR }}

      - name: Terraform Init
        run: terraform init
        working-directory: ${{ env.WORKING_DIR }}

      - name: Terraform Apply
        run: terraform apply -auto-approve tfplan
        working-directory: ${{ env.WORKING_DIR }}
```

### Atlantis

Atlantis e un'applicazione self-hosted che automatizza i workflow Terraform direttamente nei pull request. Quando viene aperto un PR che modifica file Terraform, Atlantis esegue automaticamente `terraform plan` e pubblica il risultato come commento. Il team puo rivedere il piano e approvare l'applicazione con un commento `atlantis apply`.

```yaml
# atlantis.yaml (nella root del repository)
version: 3
projects:
  - name: production-networking
    dir: infrastructure/production/networking
    workspace: default
    terraform_version: v1.6.0
    autoplan:
      when_modified: ["*.tf", "*.tfvars", "modules/**/*.tf"]
      enabled: true
    apply_requirements: [approved, mergeable]

  - name: production-compute
    dir: infrastructure/production/compute
    workspace: default
    terraform_version: v1.6.0
    apply_requirements: [approved, mergeable]
```

Il vantaggio di Atlantis e il flusso collaborativo integrato: il plan e visibile a tutti nel PR, l'apply richiede approvazione, e l'intero processo e tracciabile. Lo svantaggio e la necessita di gestire un'istanza Atlantis con accesso alle credenziali cloud.

### Spacelift

Spacelift e una piattaforma SaaS per la gestione di workflow Terraform (e altri strumenti IaC). Offre funzionalita avanzate rispetto ad Atlantis: policy-as-code con Open Policy Agent (OPA), drift detection automatica, gestione centralizzata di state e credenziali, e un sistema di moduli privati. E particolarmente adatto a organizzazioni enterprise con requisiti di governance e compliance stringenti.

---

## CI/CD per IaC — Approfondimento

### HCP Terraform (ex Terraform Cloud)

HCP Terraform (precedentemente Terraform Cloud) e la piattaforma gestita di HashiCorp che integra state management, esecuzione remota, policy enforcement e audit in un unico servizio. A differenza di Atlantis, non richiede infrastruttura self-hosted. Dalla ridenominazione del 2024, HCP Terraform fa parte della suite HashiCorp Cloud Platform.

Le funzionalita chiave includono:

- **Remote Execution**: i plan e apply vengono eseguiti nei runner di HCP, eliminando la necessita di credenziali cloud sulle macchine degli sviluppatori.
- **Sentinel Policies**: framework proprietario di policy-as-code che valuta le modifiche prima dell'apply. Le policy possono bloccare risorse non conformi, imporre tagging, limitare instance type o regioni.
- **Run Tasks**: hook pre-plan e post-plan che integrano strumenti esterni (Infracost, Snyk, Bridgecrew) direttamente nel workflow.
- **Private Module Registry**: registry interno per moduli aziendali con versioning semantico e documentazione generata automaticamente.
- **Cost Estimation nativa**: stima dei costi integrata nel piano, visibile prima dell'approvazione.

```hcl
# Configurazione HCP Terraform con workspace taggati
terraform {
  cloud {
    organization = "azienda-prod"

    workspaces {
      tags = ["networking", "eu-west-1"]
    }
  }
}
```

**Sentinel Policy — esempio di enforcement tagging:**

```python
# policy: enforce-mandatory-tags.sentinel
import "tfplan/v2" as tfplan

mandatory_tags = ["Environment", "Project", "Owner", "CostCenter"]

allResourcesHaveTags = rule {
  all tfplan.resource_changes as _, rc {
    rc.mode is "managed" and
    rc.change.after.tags is not null and
    all mandatory_tags as tag {
      rc.change.after.tags contains tag
    }
  }
}

main = rule {
  allResourcesHaveTags
}
```

### Atlantis — Configurazione Avanzata

Atlantis supporta configurazioni avanzate per scenari enterprise, inclusa l'integrazione con provider di identita, workflow personalizzati e policy di sicurezza.

```yaml
# atlantis.yaml — workflow personalizzato con pre/post hooks
version: 3
automerge: false
parallel_plan: true
parallel_apply: true

workflows:
  secure-workflow:
    plan:
      steps:
        - env:
            name: INFRACOST_API_KEY
            command: 'echo $INFRACOST_API_KEY'
        - init
        - run: tflint --recursive
        - run: checkov -d . --quiet --compact
        - plan
        - run: infracost breakdown --path=. --format=json --out-file=/tmp/infracost.json
    apply:
      steps:
        - run: echo "Applying changes to $REPO_NAME/$DIR"
        - apply

projects:
  - name: prod-networking
    dir: infrastructure/production/networking
    workspace: default
    workflow: secure-workflow
    autoplan:
      when_modified:
        - "*.tf"
        - "*.tfvars"
        - "../../modules/networking/**/*.tf"
      enabled: true
    apply_requirements:
      - approved
      - mergeable
      - undiverged

  - name: prod-compute
    dir: infrastructure/production/compute
    workspace: default
    workflow: secure-workflow
    apply_requirements:
      - approved
      - mergeable
```

Il parametro `parallel_plan: true` permette ad Atlantis di eseguire plan per progetti multipli in parallelo, riducendo significativamente i tempi di attesa nei repository con molti progetti. Il vincolo `undiverged` richiede che il branch sia aggiornato con il target prima dell'apply, prevenendo conflitti di state.

### env0

env0 e una piattaforma alternativa a Spacelift e HCP Terraform che si distingue per il focus su governance dei costi e self-service per i team di sviluppo. Supporta Terraform, OpenTofu, Pulumi, CloudFormation e Terragrunt. Le funzionalita differenzianti includono:

- **Budget Policies**: limiti di spesa per ambiente/progetto con approvazione automatica sotto soglia.
- **TTL (Time-To-Live)**: ambienti temporanei che vengono automaticamente distrutti dopo un periodo configurato.
- **Environment as a Service**: portale self-service dove gli sviluppatori possono creare ambienti pre-approvati senza intervento del team infrastruttura.

### Drift Detection Schedulata

La drift detection e il processo di rilevamento delle modifiche all'infrastruttura avvenute al di fuori dell'IaC — interventi manuali nella console cloud, script ad-hoc, o azioni di auto-scaling non catturate. Una strategia efficace prevede l'esecuzione schedulata di `terraform plan` con notifica automatica in caso di differenze.

```yaml
# .github/workflows/drift-detection.yml
name: Drift Detection

on:
  schedule:
    - cron: '0 6 * * *'  # Ogni giorno alle 06:00 UTC
  workflow_dispatch: {}

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project:
          - infrastructure/production/networking
          - infrastructure/production/compute
          - infrastructure/production/database
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Terraform Init
        run: terraform init
        working-directory: ${{ matrix.project }}

      - name: Detect Drift
        id: drift
        run: |
          terraform plan -detailed-exitcode -no-color -out=drift.plan 2>&1 | tee plan_output.txt
          echo "exit_code=$?" >> $GITHUB_OUTPUT
        working-directory: ${{ matrix.project }}
        continue-on-error: true

      - name: Notify on Drift
        if: steps.drift.outputs.exit_code == '2'
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"DRIFT RILEVATO in ${{ matrix.project }}. Verificare il plan nel workflow.\"}"
```

Il codice di uscita `2` di `terraform plan -detailed-exitcode` indica che esistono differenze tra lo stato dichiarato e quello reale, senza errori. Il codice `0` indica nessuna differenza, `1` un errore nel plan.

---

## Testing dell'IaC

### La Piramide dei Test per l'Infrastruttura

Il testing dell'IaC segue una piramide analoga a quella del software applicativo, ma con costi e tempi radicalmente diversi. Alla base ci sono i test statici (veloci, economici, locali), al vertice i test di integrazione (lenti, costosi, richiedono risorse cloud reali).

**Livello 1 — Analisi Statica (secondi)**
- `terraform fmt`: formattazione consistente
- `terraform validate`: correttezza sintattica e referenze
- `tflint`: errori specifici del provider, risorse deprecate
- `checkov` / `tfsec`: misconfigurazioni di sicurezza

**Livello 2 — Plan Analysis (secondi-minuti)**
- `terraform plan` con validazione automatica dell'output
- Policy-as-code con OPA/Conftest sul plan JSON
- Sentinel policies in HCP Terraform

**Livello 3 — Contract Testing (minuti)**
- `terraform test` nativo (Terraform 1.6+)
- Validazione di moduli con input/output attesi
- Mock dei provider per test senza risorse reali

**Livello 4 — Integration Testing (minuti-ore)**
- Terratest: deploy reale, asserzioni, destroy
- Kitchen-Terraform con InSpec
- Test E2E su infrastruttura effimera

### tflint — Analisi Statica Avanzata

tflint e un linter specifico per Terraform che va oltre `terraform validate`. Rileva risorse con tipi di istanza inesistenti, attributi deprecati, violazioni di naming convention e pattern insicuri specifici per AWS, Azure e GCP attraverso plugin dedicati.

```hcl
# .tflint.hcl
config {
  # Abilita la scansione dei moduli referenziati
  call_module_type = "local"
}

plugin "terraform" {
  enabled = true
  version = "0.9.1"
  source  = "github.com/terraform-linters/tflint-ruleset-terraform"

  preset = "recommended"
}

plugin "aws" {
  enabled = true
  version = "0.32.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

# Regola personalizzata: imponi naming convention
rule "terraform_naming_convention" {
  enabled = true
  format  = "snake_case"
}

# Forza la dichiarazione esplicita della versione del provider
rule "terraform_required_providers" {
  enabled = true
}

# Impedisci moduli senza vincolo di versione
rule "terraform_module_pinned_source" {
  enabled = true
}
```

```bash
# Esecuzione
tflint --init
tflint --recursive --format=compact

# In pipeline CI con formato machine-readable
tflint --recursive --format=json > tflint-results.json
```

### Checkov — Scansione di Sicurezza

Checkov scansiona codice Terraform, CloudFormation, Kubernetes, Dockerfile e ARM per identificare misconfigurazioni di sicurezza. Supporta oltre 2.500 policy built-in mappate a framework di compliance come CIS, SOC2, PCI-DSS, HIPAA e NIST.

```bash
# Scansione di base
checkov -d infrastructure/ --framework terraform

# Con output JUnit per CI
checkov -d infrastructure/ --output junitxml > checkov-results.xml

# Escludi check specifici (con documentazione del motivo)
checkov -d infrastructure/ \
  --skip-check CKV_AWS_18 \   # S3 access logging: gestito centralmente
  --skip-check CKV_AWS_144     # S3 cross-region replication: non richiesta

# Scansione su terraform plan (cattura valori dinamici)
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
checkov -f plan.json --framework terraform_plan
```

La scansione del plan JSON e preferibile alla scansione statica dei file `.tf` perche risolve le variabili, le espressioni dinamiche e i valori dei data source, catturando misconfigurazioni che l'analisi statica non puo rilevare.

### Terratest — Test di Integrazione

Terratest e una libreria Go per scrivere test di integrazione che creano infrastruttura reale, eseguono asserzioni e distruggono tutto al termine. E lo standard de facto per validare moduli Terraform in ambienti cloud reali.

```go
// test/vpc_test.go
package test

import (
	"testing"

	"github.com/gruntwork-io/terratest/modules/aws"
	"github.com/gruntwork-io/terratest/modules/terraform"
	"github.com/stretchr/testify/assert"
)

func TestVpcModule(t *testing.T) {
	t.Parallel()

	terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
		TerraformDir: "../modules/vpc",
		Vars: map[string]interface{}{
			"vpc_cidr":     "10.99.0.0/16",
			"environment":  "test",
			"azs":          []string{"eu-west-1a", "eu-west-1b"},
		},
		EnvVars: map[string]string{
			"AWS_DEFAULT_REGION": "eu-west-1",
		},
	})

	// Distruggi l'infrastruttura al termine del test
	defer terraform.Destroy(t, terraformOptions)

	// Crea l'infrastruttura
	terraform.InitAndApply(t, terraformOptions)

	// Asserzioni
	vpcID := terraform.Output(t, terraformOptions, "vpc_id")
	assert.NotEmpty(t, vpcID)

	// Verifica che la VPC esista realmente in AWS
	vpc := aws.GetVpcById(t, vpcID, "eu-west-1")
	assert.Equal(t, "10.99.0.0/16", *vpc.CidrBlock)

	// Verifica il numero di subnet
	subnetIDs := terraform.OutputList(t, terraformOptions, "private_subnet_ids")
	assert.Equal(t, 2, len(subnetIDs))

	// Verifica i tag
	tags := aws.GetTagsForVpc(t, vpcID, "eu-west-1")
	assert.Equal(t, "test", tags["Environment"])
}
```

**Considerazioni sui costi**: ogni esecuzione di Terratest crea risorse cloud reali. Per contenere i costi si usa un account AWS/Azure dedicato al testing con budget alert, si parallelizzano i test con `t.Parallel()`, e si utilizzano le istanze piu piccole possibili.

### OPA e Conftest — Policy as Code

Open Policy Agent (OPA) e un motore di policy universale che valuta regole scritte in linguaggio Rego su dati strutturati (JSON). Conftest e un wrapper che semplifica l'uso di OPA per validare file di configurazione, inclusi i piani Terraform.

```rego
# policy/terraform/deny_public_buckets.rego
package terraform.deny

import input.resource_changes

# Impedisci bucket S3 senza encryption
deny[msg] {
  rc := resource_changes[_]
  rc.type == "aws_s3_bucket"
  rc.change.after.server_side_encryption_configuration == null
  msg := sprintf(
    "Il bucket S3 '%s' deve avere la server-side encryption abilitata",
    [rc.address]
  )
}

# Impedisci security group con ingress 0.0.0.0/0 sulla porta 22
deny[msg] {
  rc := resource_changes[_]
  rc.type == "aws_security_group"
  ingress := rc.change.after.ingress[_]
  ingress.from_port <= 22
  ingress.to_port >= 22
  cidr := ingress.cidr_blocks[_]
  cidr == "0.0.0.0/0"
  msg := sprintf(
    "Il security group '%s' permette SSH (porta 22) da 0.0.0.0/0",
    [rc.address]
  )
}

# Impedisci istanze senza tag Environment
deny[msg] {
  rc := resource_changes[_]
  rc.type == "aws_instance"
  not rc.change.after.tags.Environment
  msg := sprintf(
    "L'istanza '%s' deve avere il tag 'Environment'",
    [rc.address]
  )
}
```

```bash
# Genera il plan JSON e validalo con Conftest
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
conftest test plan.json --policy policy/terraform/ --output table
```

### terraform test — Testing Nativo

A partire da Terraform 1.6, e disponibile il comando nativo `terraform test` che permette di scrivere test direttamente in HCL senza dipendenze esterne. I test possono utilizzare mock dei provider per evitare la creazione di risorse reali.

```hcl
# tests/vpc_validation.tftest.hcl
variables {
  vpc_cidr    = "10.0.0.0/16"
  environment = "test"
  azs         = ["eu-west-1a", "eu-west-1b"]
}

run "vpc_cidr_is_valid" {
  command = plan

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "Il CIDR della VPC non corrisponde al valore atteso"
  }
}

run "creates_correct_number_of_subnets" {
  command = plan

  assert {
    condition     = length(aws_subnet.private) == 2
    error_message = "Il numero di subnet private non corrisponde al numero di AZ"
  }
}

run "tags_are_applied" {
  command = plan

  assert {
    condition     = aws_vpc.main.tags_all["Environment"] == "test"
    error_message = "Il tag Environment non e presente sulla VPC"
  }
}
```

```bash
# Esecuzione
terraform test

# Con filtro su specifici file di test
terraform test -filter=tests/vpc_validation.tftest.hcl
```

---

## Sicurezza dell'IaC

### tfsec e Trivy

tfsec e stato per anni lo standard per l'analisi statica di sicurezza del codice Terraform. Dal 2023, tfsec e confluito nel progetto Trivy di Aqua Security, che offre una piattaforma unificata per la scansione di vulnerabilita su container, IaC, file system e repository.

```bash
# tfsec (legacy, ancora funzionante)
tfsec infrastructure/ --format json > tfsec-results.json

# Trivy (successore raccomandato)
trivy config infrastructure/ --severity HIGH,CRITICAL
trivy config infrastructure/ --format json -o trivy-results.json

# Trivy con policy personalizzate
trivy config infrastructure/ --policy policy/custom/ --namespaces user
```

Le regole di tfsec/Trivy coprono scenari come:

- Bucket S3 senza encryption o con accesso pubblico
- Security group con porte aperte a `0.0.0.0/0`
- Database RDS senza backup automatico
- CloudTrail non abilitato
- Password di IAM user senza rotazione
- EBS volume non cifrati
- Lambda function senza VPC

### Terrascan

Terrascan e uno scanner open-source di Tenable (ex Accurics) per la scansione di codice IaC contro standard di sicurezza e compliance. Supporta Terraform, Kubernetes manifests, Helm charts, Dockerfiles e CloudFormation. Le policy sono scritte in Rego (stesso linguaggio di OPA) e mappate a framework di compliance.

```bash
# Scansione di base
terrascan scan -i terraform -d infrastructure/

# Con standard di compliance specifico
terrascan scan -i terraform -d infrastructure/ \
  --policy-type aws \
  --category-list "CIS" \
  --severity high

# Output SARIF per integrazione con GitHub Security
terrascan scan -i terraform -d infrastructure/ \
  --output sarif > terrascan.sarif
```

### KICS (Keeping Infrastructure as Code Secure)

KICS e uno scanner di Checkmarx che supporta il maggior numero di framework IaC: Terraform, CloudFormation, Ansible, Docker, Kubernetes, Helm, OpenAPI e Pulumi. Le query sono scritte in Rego e coprono oltre 3.000 scenari di misconfiguration.

```bash
# Scansione multi-framework
kics scan -p infrastructure/ \
  --type Terraform,Ansible \
  --output-path results/ \
  --report-formats "json,html,sarif"

# Con esclusione di query specifiche
kics scan -p infrastructure/ \
  --exclude-queries "a227ec01-f97a-4084-91a4-47b350c1db54" \
  --exclude-severities info,low
```

### Supply Chain dei Moduli

La sicurezza della supply chain IaC riguarda l'integrita e l'affidabilita dei moduli e provider utilizzati. Un modulo Terraform malevolo o compromesso puo esfiltrare credenziali, creare backdoor nell'infrastruttura, o modificare risorse in modo subdolo.

Misure di mitigazione:

- **Pin della versione**: specificare sempre versioni esatte dei moduli (`version = "5.1.0"`, non `version = ">= 5.0"`).
- **Hash verification**: Terraform genera automaticamente il file `.terraform.lock.hcl` con gli hash SHA256 dei provider. Committare questo file nel repository.
- **Registry privato**: ospitare moduli approvati in un registry interno (HCP Terraform, Artifactory, GitLab) piuttosto che referenziare direttamente repository esterni.
- **Code review dei moduli**: ogni aggiornamento di versione di un modulo esterno deve passare per code review, verificando il changelog e le differenze nel codice.
- **Scansione delle dipendenze**: utilizzare `terraform providers lock` per generare hash multi-piattaforma e verificare l'integrita dei download.

```bash
# Genera lock file con hash per multiple piattaforme
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_amd64 \
  -platform=darwin_arm64
```

---

## Pattern di Gestione dello State

### Confronto Backend Remoti

| Backend | Provider | Locking | Encryption | Versioning | Costo |
|---------|----------|---------|------------|------------|-------|
| S3 + DynamoDB | AWS | DynamoDB | SSE-S3/KMS | S3 versioning | Basso |
| Azure Blob | Azure | Blob lease | AES-256 | Blob versioning | Basso |
| GCS | GCP | Nativo | AES-256/CMEK | Object versioning | Basso |
| HCP Terraform | Multi-cloud | Nativo | At-rest + in-transit | Automatico | Medio-Alto |
| Consul | On-premises | Nativo | TLS | Nativo | Medio |
| PostgreSQL | On-premises | Advisory lock | TLS | Manuale | Basso |

### State Splitting — Ridurre il Blast Radius

Lo state splitting e la pratica di separare lo state in file distinti per dominio funzionale. Un singolo state monolitico per un'intera infrastruttura di produzione e un rischio critico: un errore nel plan o un conflitto nello state puo compromettere tutte le risorse.

**Pattern raccomandato — separazione per layer:**

```
infrastructure/
  production/
    networking/          # State: VPC, subnet, route tables, NAT
      terraform.tfstate  # → s3://state/prod/networking/
    security/            # State: IAM roles, policies, KMS keys
      terraform.tfstate  # → s3://state/prod/security/
    compute/             # State: EC2, ASG, ALB
      terraform.tfstate  # → s3://state/prod/compute/
    database/            # State: RDS, ElastiCache, DynamoDB
      terraform.tfstate  # → s3://state/prod/database/
    monitoring/          # State: CloudWatch, alarms, dashboards
      terraform.tfstate  # → s3://state/prod/monitoring/
```

I layer comunicano attraverso `terraform_remote_state` o, preferibilmente, tramite data source che interrogano direttamente le risorse cloud (piu resiliente alla riorganizzazione dello state).

### State Locking e Concorrenza

Il locking dello state impedisce che due operatori o pipeline eseguano `terraform apply` contemporaneamente sullo stesso state, causando corruzione o conflitti.

```hcl
# Backend S3 con locking DynamoDB — la tabella deve avere
# una partition key di nome "LockID" di tipo String
terraform {
  backend "s3" {
    bucket         = "azienda-terraform-state"
    key            = "production/networking/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    
    # Abilita il locking con retry automatico
    skip_metadata_api_check = false
  }
}
```

```bash
# In caso di lock orfano (operazione interrotta senza rilascio del lock)
terraform force-unlock LOCK_ID

# Verifica lo stato del lock
aws dynamodb get-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "azienda-terraform-state/production/networking/terraform.tfstate"}}'
```

### Drift Detection e Remediation

Il drift si verifica quando lo stato reale dell'infrastruttura diverge dalla configurazione dichiarata. Le cause piu comuni sono: interventi manuali nella console cloud, script ad-hoc, auto-scaling non dichiarato, o modifiche da parte di altri strumenti.

**Strategia di rilevamento:**

1. **Plan schedulato**: `terraform plan -detailed-exitcode` eseguito via cron (exit code 2 = drift rilevato)
2. **CloudTrail/Activity Log**: monitorare eventi di modifica sulle risorse gestite da Terraform
3. **HCP Terraform**: drift detection automatica con notifiche e possibilita di reconciliazione one-click

**Strategia di remediation:**

- **Riconciliazione automatica**: `terraform apply` ripristina lo stato desiderato (rischio: sovrascrive modifiche intenzionali non ancora codificate)
- **Riconciliazione manuale**: analisi del drift, decisione caso per caso se aggiornare il codice o ripristinare lo stato
- **Import selettivo**: se una risorsa e stata modificata in modo intenzionale, aggiornare il codice e importare il nuovo stato

### State Surgery — Operazioni Avanzate

Le operazioni di "chirurgia" sullo state sono necessarie durante refactoring, migrazioni, o recovery da errori. Devono essere eseguite con estrema cautela e dopo backup.

```bash
# Backup dello state prima di qualsiasi operazione
terraform state pull > state-backup-$(date +%Y%m%d-%H%M%S).json

# Visualizza le risorse nello state
terraform state list

# Mostra i dettagli di una risorsa specifica
terraform state show aws_instance.web

# Rimuovi una risorsa dallo state (senza distruggerla nel cloud)
terraform state rm aws_instance.legacy

# Sposta una risorsa (rinominazione o spostamento in modulo)
terraform state mv aws_instance.web aws_instance.app
terraform state mv aws_instance.app module.compute.aws_instance.app

# Importa una risorsa esistente nello state
terraform import aws_instance.legacy i-0abc123def456

# Taint: forza la ricreazione alla prossima apply
terraform taint aws_instance.web
# Untaint: annulla il taint
terraform untaint aws_instance.web
```

**Nota**: `terraform taint` e deprecato a favore di `terraform apply -replace=aws_instance.web` (Terraform 0.15.2+), che e piu sicuro perche mostra il piano completo prima dell'esecuzione.

---

## Pattern di Design dei Moduli

### Modulo Thin Wrapper

Il pattern thin wrapper crea un modulo che avvolge un modulo community con valori predefiniti aziendali, senza duplicare logica. Questo garantisce conformita agli standard interni pur sfruttando moduli battle-tested.

```hcl
# modules/vpc-aziendale/main.tf
# Wrapper attorno al modulo community con default aziendali

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"

  name = "${var.project}-${var.environment}-vpc"
  cidr = var.cidr

  azs             = var.azs
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  # Default aziendali: sempre attivi
  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  enable_dns_hostnames   = true
  enable_dns_support     = true
  enable_flow_log        = true
  flow_log_destination_type = "cloud-watch-logs"

  # Tagging aziendale automatico
  tags = merge(var.extra_tags, {
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "Terraform"
    Module      = "vpc-aziendale"
  })
}
```

### Composizione vs Ereditarieta

I moduli Terraform non supportano l'ereditarieta nel senso OOP. Il pattern raccomandato e la **composizione**: moduli piccoli e focalizzati che vengono assemblati in moduli di livello superiore.

```hcl
# modules/app-stack/main.tf — compone moduli atomici
module "networking" {
  source      = "../vpc-aziendale"
  project     = var.project
  environment = var.environment
  cidr        = var.vpc_cidr
  azs         = var.azs
}

module "security" {
  source      = "../security-groups"
  vpc_id      = module.networking.vpc_id
  environment = var.environment
}

module "compute" {
  source            = "../ec2-cluster"
  subnet_ids        = module.networking.private_subnet_ids
  security_group_id = module.security.app_sg_id
  instance_type     = var.instance_type
  instance_count    = var.instance_count
}

module "database" {
  source            = "../rds-postgres"
  subnet_ids        = module.networking.database_subnet_ids
  security_group_id = module.security.db_sg_id
  instance_class    = var.db_instance_class
}
```

### Contratto del Modulo

Ogni modulo dovrebbe definire un "contratto" chiaro attraverso:

- **Input validation**: regole `validation` su ogni variabile con vincoli semantici
- **Output documentati**: ogni output con `description` che ne chiarisce l'uso
- **Preconditions e postconditions**: (Terraform 1.2+) asserzioni sullo stato delle risorse

```hcl
# Precondizione: la subnet deve esistere
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id

  lifecycle {
    precondition {
      condition     = var.instance_type != "t3.nano" || var.environment != "production"
      error_message = "Le istanze t3.nano non sono permesse in produzione."
    }

    postcondition {
      condition     = self.public_ip != ""
      error_message = "L'istanza non ha ricevuto un IP pubblico."
    }
  }
}
```

### Opinionated Defaults

I moduli aziendali devono avere default sicuri e conformi, richiedendo override espliciti per deviare. Il principio e "secure by default, configurable by exception".

```hcl
variable "encryption_enabled" {
  description = "Abilita encryption at-rest. Default: true. Disabilitare solo per ambienti di sviluppo non-critici."
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Giorni di retention dei backup. Minimo 7 in produzione."
  type        = number
  default     = 14

  validation {
    condition     = var.backup_retention_days >= 7
    error_message = "La retention dei backup deve essere almeno 7 giorni."
  }
}

variable "deletion_protection" {
  description = "Protezione dalla cancellazione accidentale. Default: true."
  type        = bool
  default     = true
}
```

---

## Strategie Multi-Cloud

### Quando Unificare e Quando Divergere

L'IaC multi-cloud presenta una tensione fondamentale: quanto astrarre le differenze tra cloud provider? Due approcci estremi esistono.

**Approccio unificato**: un singolo modulo Terraform con variabili condizionali che crea risorse su AWS o Azure in base a un parametro `cloud_provider`. Vantaggi: interfaccia unica, DRY. Svantaggi: complessita esplosiva, impossibilita di sfruttare funzionalita specifiche del provider, debug difficile.

**Approccio separato**: moduli completamente distinti per ogni cloud, con un layer di composizione che li seleziona. Vantaggi: semplicita, utilizzo completo delle funzionalita native. Svantaggi: duplicazione, divergenza nel tempo.

**Approccio raccomandato — astrazione a livello di interfaccia**: definire un contratto di output comune tra moduli cloud-specific, mantenendo implementazioni separate.

```hcl
# modules/compute-aws/outputs.tf
output "instance_ids" {
  description = "Lista di ID delle istanze create"
  value       = aws_instance.app[*].id
}

output "private_ips" {
  description = "Lista di IP privati delle istanze"
  value       = aws_instance.app[*].private_ip
}

# modules/compute-azure/outputs.tf — stesso contratto di output
output "instance_ids" {
  description = "Lista di ID delle istanze create"
  value       = azurerm_linux_virtual_machine.app[*].id
}

output "private_ips" {
  description = "Lista di IP privati delle istanze"
  value       = azurerm_linux_virtual_machine.app[*].private_ip_address
}
```

### Provider Aliasing per Multi-Region

Il provider aliasing permette di gestire risorse in regioni multiple all'interno della stessa configurazione.

```hcl
provider "aws" {
  region = "eu-west-1"
  alias  = "primary"
}

provider "aws" {
  region = "us-east-1"
  alias  = "disaster_recovery"
}

# Replica cross-region del bucket S3
resource "aws_s3_bucket" "primary" {
  provider = aws.primary
  bucket   = "app-data-primary"
}

resource "aws_s3_bucket" "replica" {
  provider = aws.disaster_recovery
  bucket   = "app-data-dr"
}

resource "aws_s3_bucket_replication_configuration" "replication" {
  provider = aws.primary
  bucket   = aws_s3_bucket.primary.id
  role     = aws_iam_role.replication.arn

  rule {
    status = "Enabled"
    destination {
      bucket        = aws_s3_bucket.replica.arn
      storage_class = "STANDARD_IA"
    }
  }
}
```

---

## Stima dei Costi — Infracost

### Panoramica

Infracost e uno strumento open-source che stima i costi cloud analizzando i piani Terraform e OpenTofu *prima* del deploy. Supporta oltre 1.100 risorse su AWS, Azure e GCP, includendo risorse usage-based come Lambda, S3 e API Gateway tramite file di stima dell'utilizzo.

L'integrazione nel workflow IaC implementa il concetto di "FinOps shift-left": rendere visibili i costi al momento della scrittura del codice, non dopo il deployment.

### Utilizzo CLI

```bash
# Stima dei costi da codice Terraform
infracost breakdown --path infrastructure/production/

# Confronto tra branch (utile nei PR)
infracost diff \
  --path infrastructure/production/ \
  --compare-to infracost-base.json

# Output JSON per automazione
infracost breakdown \
  --path infrastructure/production/ \
  --format json \
  --out-file infracost.json

# Con file di utilizzo stimato per risorse usage-based
infracost breakdown \
  --path infrastructure/production/ \
  --usage-file infracost-usage.yml
```

```yaml
# infracost-usage.yml — stima dell'utilizzo per risorse dinamiche
version: 0.1

resource_usage:
  aws_lambda_function.api:
    monthly_requests: 1000000
    request_duration_ms: 200

  aws_s3_bucket.data:
    standard:
      storage_gb: 500
      monthly_tier_1_requests: 100000
      monthly_tier_2_requests: 1000000

  aws_nat_gateway.main:
    monthly_data_processed_gb: 100
```

### Integrazione CI/CD

```yaml
# .github/workflows/infracost.yml
name: Infracost Cost Estimation

on:
  pull_request:
    paths: ['infrastructure/**']

jobs:
  infracost:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Setup Infracost
        uses: infracost/actions/setup@v3
        with:
          api-key: ${{ secrets.INFRACOST_API_KEY }}

      - name: Generate baseline
        run: |
          infracost breakdown \
            --path infrastructure/production/ \
            --format json \
            --out-file /tmp/infracost-base.json
        env:
          INFRACOST_TERRAFORM_CLOUD_TOKEN: ${{ secrets.TFC_TOKEN }}

      - name: Generate diff
        run: |
          infracost diff \
            --path infrastructure/production/ \
            --compare-to /tmp/infracost-base.json \
            --format json \
            --out-file /tmp/infracost-diff.json

      - name: Post PR comment
        run: |
          infracost comment github \
            --path /tmp/infracost-diff.json \
            --repo $GITHUB_REPOSITORY \
            --pull-request ${{ github.event.pull_request.number }} \
            --github-token ${{ secrets.GITHUB_TOKEN }} \
            --behavior update
```

### Policy di Costo

Infracost supporta policy che bloccano i PR se il costo supera soglie definite.

```yaml
# infracost-policy.yml
version: 0.1
policies:
  - path: infrastructure/production/
    rules:
      - name: block-high-cost-changes
        description: "Blocca modifiche con costo mensile > $500"
        condition: '{{ .DiffTotalMonthlyCost | float64 }} > 500'
        action: block

      - name: warn-medium-cost-changes
        description: "Warning per modifiche con costo mensile > $100"
        condition: '{{ .DiffTotalMonthlyCost | float64 }} > 100'
        action: warn
```

---

## IaC su Scala

### Monorepo vs Polyrepo

La scelta tra monorepo (un unico repository per tutto il codice IaC) e polyrepo (repository separati per componente o team) ha impatti profondi sulla governance, la velocita di sviluppo e la complessita operativa.

**Monorepo — un repository per tutta l'infrastruttura:**

| Vantaggio | Svantaggio |
|-----------|------------|
| Visibilita completa sulle dipendenze | Pipeline CI/CD complesse (path filtering) |
| Refactoring atomico cross-componente | Permission granulari difficili (CODEOWNERS) |
| Versioning unificato dei moduli | Rischio di blast radius elevato |
| Onboarding semplificato | Tempi di clone/checkout crescenti |

**Polyrepo — repository separati per dominio:**

| Vantaggio | Svantaggio |
|-----------|------------|
| Isolamento naturale dei team | Difficolta nel refactoring cross-repo |
| Permission granulari native | Duplicazione di configurazione base |
| Pipeline CI/CD semplici | Drift tra versioni dei moduli |
| Blast radius contenuto | Visibilita frammentata |

**Raccomandazione**: per organizzazioni fino a 5-10 team infrastrutturali, il monorepo con path-based CODEOWNERS e pipeline filtrate per percorso offre il miglior bilanciamento. Oltre questa soglia, la transizione a polyrepo con un registry di moduli centralizzato diventa piu gestibile.

### Terragrunt — DRY Configuration

Terragrunt e un wrapper per Terraform che risolve il problema della duplicazione di configurazione tra ambienti. Permette di definire backend, provider e variabili comuni una sola volta e di ereditarli nei sotto-directory.

```hcl
# terragrunt.hcl (root)
remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket         = "azienda-terraform-state"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = "eu-west-1"
  default_tags {
    tags = {
      ManagedBy = "Terraform"
      Project   = "studio-lavoro"
    }
  }
}
EOF
}
```

```hcl
# infrastructure/production/networking/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../modules/vpc"
}

inputs = {
  vpc_cidr    = "10.0.0.0/16"
  environment = "production"
  azs         = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
}

# Dipendenza esplicita: il networking deve essere applicato
# prima del compute
dependencies {
  paths = []  # Nessuna dipendenza — e il primo layer
}
```

```hcl
# infrastructure/production/compute/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../modules/ec2-cluster"
}

dependency "networking" {
  config_path = "../networking"
}

inputs = {
  vpc_id     = dependency.networking.outputs.vpc_id
  subnet_ids = dependency.networking.outputs.private_subnet_ids
}
```

Terragrunt risolve le dipendenze automaticamente: `terragrunt run-all apply` esegue prima il networking, poi il compute, rispettando il grafo di dipendenze dichiarato.

### Dependency Management e Blast Radius

Il blast radius e l'impatto massimo di un errore in un singolo `terraform apply`. Si riduce attraverso:

1. **State splitting per dominio**: networking, compute, database, monitoring in state separati
2. **Limiti sulle risorse per state**: un singolo state non dovrebbe gestire piu di 200-300 risorse
3. **Target selettivo**: `terraform apply -target=module.compute` limita l'applicazione a un sotto-insieme
4. **Approvazioni stratificate**: modifiche al networking richiedono approvazione del team infrastruttura; modifiche al compute possono essere self-service

### Versioning dei Moduli

Il versioning semantico (SemVer) dei moduli interni e critico per la stabilita a scala. Ogni modulo ha un ciclo di vita indipendente con changelog, release e migrazione documentata.

```hcl
# Pinning esplicito nel consumatore
module "vpc" {
  source  = "app.terraform.io/azienda/vpc/aws"
  version = "3.2.1"  # Pin esatto, mai range in produzione
}
```

**Convenzione SemVer per moduli IaC:**

- **MAJOR** (4.0.0): breaking changes — risorse distrutte e ricreate, variabili rimosse, output rinominati
- **MINOR** (3.3.0): nuove funzionalita retrocompatibili — nuove variabili con default, nuovi output, nuove risorse opzionali
- **PATCH** (3.2.2): bug fix, aggiornamento documentazione, fix di sicurezza senza cambi di interfaccia

---

## Best Practices

### 1. Versionare Tutto nel Version Control

Ogni aspetto dell'infrastruttura deve essere nel repository Git: codice Terraform, playbook Ansible, configurazioni dei moduli, pipeline CI/CD. Lo state di Terraform non va versionato nel repository (va su backend remoto), ma la sua configurazione si. Il repository diventa la "single source of truth" per l'infrastruttura.

### 2. Adottare una Struttura di Directory Chiara e Consistente

Organizzare il codice IaC in modo logico e prevedibile facilita la navigazione e la manutenzione. Un modello efficace prevede la separazione per ambiente e per componente:

```
infrastructure/
  modules/                  # Moduli riutilizzabili
    vpc/
    compute/
    database/
  environments/
    dev/
      networking/
      compute/
    staging/
    production/
      networking/
        main.tf
        variables.tf
        outputs.tf
        terraform.tfvars
      compute/
      database/
```

### 3. Utilizzare Remote State con Locking

Non si usa mai lo state locale in un contesto di team. Si configura un backend remoto (S3 + DynamoDB, Terraform Cloud, GCS) con cifratura e locking. Si abilita il versioning sul bucket di state per poter recuperare versioni precedenti in caso di corruzione.

### 4. Applicare il Principio del Minimo Privilegio

Le credenziali utilizzate da Terraform e Ansible devono avere esclusivamente i permessi necessari. Si preferisce l'autenticazione OIDC nelle pipeline CI/CD (nessuna chiave statica da gestire). Si usano ruoli IAM specifici per ogni pipeline e si ruotano regolarmente le credenziali dove l'OIDC non e disponibile.

### 5. Implementare Code Review e Approvazioni

Ogni modifica infrastrutturale deve passare attraverso un pull request con review obbligatorio. Il piano Terraform deve essere visibile nel PR (tramite Atlantis, Spacelift o GitHub Actions). L'applicazione in produzione richiede approvazione esplicita tramite environment protection rules o policy di merge.

### 6. Testare il Codice IaC

Il testing dell'IaC include diversi livelli. Il **linting statico** (terraform fmt, terraform validate, tflint) verifica la correttezza sintattica. La **scansione di sicurezza** (checkov, tfsec, Snyk) identifica misconfigurazioni. I **test di integrazione** (terratest, kitchen-terraform) verificano che l'infrastruttura creata funzioni correttamente. I **test di policy** (OPA, Sentinel) garantiscono la conformita alle policy aziendali.

### 7. Gestire i Segreti in Modo Sicuro

I segreti non devono mai apparire nel codice, nelle variabili tfvars committate, ne nello state non cifrato. Si utilizzano Ansible Vault per le variabili nei playbook, AWS Secrets Manager o HashiCorp Vault per i segreti runtime, e variabili d'ambiente o sistemi di secrets management nella pipeline CI/CD. Si marca ogni variabile sensibile con il flag `sensitive = true` in Terraform.

### 8. Implementare il Tagging Consistente

Un sistema di tagging uniforme su tutte le risorse e indispensabile per il cost management, la sicurezza e l'organizzazione. Come minimo, ogni risorsa deve avere: `Environment`, `Project`, `ManagedBy`, `Owner`, `CostCenter`. In Terraform, si utilizzano `default_tags` nel provider o variabili locali con `merge()` per applicare i tag in modo uniforme.

### 9. Pianificare il Disaster Recovery dello State

Lo state di Terraform e un asset critico: la sua perdita o corruzione puo rendere impossibile la gestione dell'infrastruttura. Si abilita il versioning sul bucket S3/GCS che ospita lo state. Si configura il backup cross-region. Si documenta la procedura di recovery e si testa periodicamente. Per il worst case, `terraform import` permette di ricostruire lo state da zero, ma e un'operazione lunga e soggetta a errori.

### 10. Adottare l'Approccio Incrementale e Modulare

Non si riscrive l'intera infrastruttura in una volta. Si inizia importando le risorse esistenti e codificandole progressivamente. Si creano moduli riutilizzabili per i pattern comuni. Si separano gli state per ridurre il raggio di impatto di ogni modifica: lo state del networking e separato da quello del compute, che e separato da quello del database. Un errore in un apply non deve poter compromettere risorse non correlate.

---

## Esercizi

1. **OpenTofu Migration (Intermedio)**
   Prendere un progetto Terraform esistente con backend S3. Installare OpenTofu, eseguire `tofu init` e `tofu plan` sullo stesso codice. Verificare che il piano sia identico a quello di Terraform. Configurare la cifratura client-side dello state di OpenTofu e verificare che il file di state nel bucket S3 sia effettivamente cifrato. Documentare le differenze operative riscontrate.

2. **Crossplane Composition (Avanzato)**
   In un cluster Kubernetes di sviluppo, installare Crossplane e il provider AWS. Creare una CompositeResourceDefinition (XRD) per un pattern "Application Environment" che includa VPC, subnet, security group e istanza EC2. Scrivere la Composition corrispondente. Pubblicare un Claim e verificare che tutte le risorse cloud vengano create. Modificare il Claim e osservare la riconciliazione automatica.

3. **Pipeline di Sicurezza IaC Completa (Avanzato)**
   Configurare una pipeline GitHub Actions che integri: tflint per il linting, Checkov per la scansione di sicurezza, Conftest con policy OPA personalizzate per la governance, e Infracost per la stima dei costi. Ogni strumento deve produrre un commento nel PR con i risultati. Scrivere una policy OPA che impedisca la creazione di risorse senza tag obbligatori e una policy Infracost che blocchi cambiamenti con costo superiore a una soglia definita.

4. **Terragrunt Multi-Environment (Avanzato)**
   Strutturare un progetto IaC con Terragrunt per gestire tre ambienti (dev, staging, production) con configurazione DRY. Il backend, il provider e i tag comuni devono essere definiti una sola volta nel `terragrunt.hcl` root. Implementare dipendenze tra i layer (networking -> compute -> database) e verificare che `terragrunt run-all plan` risolva l'ordine corretto. Aggiungere un modulo wrapper aziendale attorno al modulo community `terraform-aws-modules/vpc/aws`.

5. **Primo Progetto Terraform (Base)**
   Inizializzare un progetto Terraform con backend locale. Definire un provider AWS (o Azure/GCP). Creare una VPC con due subnet usando variabili per CIDR e regione. Eseguire `terraform plan`, applicare, verificare le risorse nel cloud, poi distruggere. Convertire il backend a S3 con DynamoDB lock e ripetere il ciclo.

6. **Moduli Riutilizzabili e Workspace (Intermedio)**
   Creare un modulo Terraform per un pattern VPC+Subnet+NAT con input parametrizzati (numero di AZ, CIDR, tag). Pubblicare il modulo in un registry privato o Git. Usare workspace per separare gli ambienti dev e prod. Deployare lo stesso modulo in entrambi i workspace con `tfvars` differenti.

7. **Ansible Playbook con Ruoli e Vault (Intermedio)**
   Scrivere un playbook Ansible che configuri un server web (Nginx + certificato TLS). Organizzare la logica in ruoli separati (common, webserver, tls). Cifrare le credenziali del certificato con Ansible Vault. Usare un inventario dinamico (AWS EC2 plugin o equivalente). Verificare l'idempotenza eseguendo il playbook due volte.

8. **Pipeline CI/CD con Drift Detection (Avanzato)**
   Configurare una pipeline GitHub Actions che: (a) esegua `terraform fmt -check` e `terraform validate`, (b) esegua `tflint` e `checkov` per scansione statica, (c) generi ed esponga il `terraform plan` come commento sul PR, (d) applichi solo dopo approvazione manuale. Aggiungere uno step schedulato (cron) che esegua `terraform plan` notturno per rilevare drift.

9. **Terratest e Policy as Code (Avanzato)**
   Scrivere test di integrazione con Terratest (Go) per un modulo Terraform: il test deve creare l'infrastruttura, verificare che le risorse siano raggiungibili e conformi (porte corrette, tag presenti, encryption abilitata), e distruggere tutto al termine. Aggiungere una policy OPA (Rego) che impedisca la creazione di bucket S3 senza encryption e validarla nella pipeline.

---

## Letture e Riferimenti

**Documentazione ufficiale**

- Terraform Language Documentation — https://developer.hashicorp.com/terraform/language (consultato: 2026-05-24)
- Terraform CLI Documentation — https://developer.hashicorp.com/terraform/cli (consultato: 2026-05-24)
- OpenTofu Documentation — https://opentofu.org/docs/ (consultato: 2026-05-24)
- Ansible Documentation — https://docs.ansible.com/ansible/latest/ (consultato: 2026-05-24)
- Checkov Documentation — https://www.checkov.io/1.Welcome/What%20is%20Checkov.html (consultato: 2026-05-24)
- Terratest Documentation — https://terratest.gruntwork.io/docs/ (consultato: 2026-05-24)
- Pulumi Documentation — https://www.pulumi.com/docs/ (consultato: 2026-05-24)
- Crossplane Documentation — https://docs.crossplane.io/ (consultato: 2026-05-24)
- Infracost Documentation — https://www.infracost.io/docs/ (consultato: 2026-05-24)
- Terragrunt Documentation — https://terragrunt.gruntwork.io/docs/ (consultato: 2026-05-24)
- Atlantis Documentation — https://www.runatlantis.io/docs/ (consultato: 2026-05-24)
- Spacelift Documentation — https://docs.spacelift.io/ (consultato: 2026-05-24)
- tflint Documentation — https://github.com/terraform-linters/tflint (consultato: 2026-05-24)
- Open Policy Agent (OPA) — https://www.openpolicyagent.org/docs/ (consultato: 2026-05-24)
- Trivy (ex tfsec) Documentation — https://aquasecurity.github.io/trivy/ (consultato: 2026-05-24)
- Terrascan Documentation — https://runterrascan.io/docs/ (consultato: 2026-05-24)

**Libri consigliati**

- *Terraform: Up & Running* — Yevgeniy Brikman (O'Reilly, 3ª edizione)
- *Ansible for DevOps* — Jeff Geerling (LeanPub)
- *Infrastructure as Code* — Kief Morris (O'Reilly, 2ª edizione)
- *Pulumi in Action* — Aurelie Vache (Manning, 2024)
- *Production Kubernetes* — Josh Rosso et al. (O'Reilly) — contiene capitoli su Crossplane e platform engineering

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|--------|--------|-----------|
| [01](01-cloud-aws.md) | AWS | Provider AWS, CloudFormation, CDK, state su S3 |
| [02](02-cloud-azure.md) | Microsoft Azure | Provider azurerm, Bicep, ARM template |
| [03](03-cloud-gcp.md) | Google Cloud Platform | Provider Google, Config Connector, state su GCS |
| [05](05-kubernetes.md) | Kubernetes | Crossplane richiede un cluster Kubernetes, gestione CRD e controller |
| [07](07-ci-cd.md) | CI/CD | Pipeline per plan/apply, Atlantis, Spacelift, drift detection |
| [08](08-gitops.md) | GitOps | Crossplane con ArgoCD/Flux, riconciliazione continua dell'infrastruttura |
| [15](15-secrets-management.md) | Secrets Management | Ansible Vault, HashiCorp Vault, variabili sensibili, cifratura state OpenTofu |
| [16](16-finops.md) | FinOps | Infracost, stima dei costi shift-left, budget policies |
| [20](20-supply-chain-slsa-cosign.md) | Supply Chain e SLSA | Integrità dei moduli, firma degli artefatti IaC, lock file dei provider |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Backend** | Componente che determina dove Terraform archivia lo state file (locale, S3, GCS, Azure Blob) |
| **Checkov** | Strumento di analisi statica che scansiona codice IaC per identificare misconfigurazioni di sicurezza |
| **Drift** | Divergenza tra lo stato reale dell'infrastruttura e la configurazione dichiarata nel codice IaC |
| **HCL (HashiCorp Configuration Language)** | Linguaggio dichiarativo usato da Terraform per definire risorse infrastrutturali |
| **Idempotenza** | Proprietà per cui l'applicazione ripetuta della stessa configurazione produce sempre lo stesso risultato |
| **Module** | Unità riutilizzabile di configurazione Terraform che incapsula un insieme di risorse correlate |
| **OpenTofu** | Fork open-source di Terraform mantenuto dalla Linux Foundation con licenza MPL |
| **Playbook** | File YAML di Ansible che definisce una sequenza di task da eseguire su host target |
| **Provider** | Plugin Terraform che traduce le risorse HCL in chiamate API verso un cloud o servizio specifico |
| **State File** | File JSON che mappa le risorse dichiarate nel codice alle risorse reali nel cloud |
| **Terraform Plan** | Comando che calcola le differenze tra stato attuale e configurazione desiderata senza applicare modifiche |
| **tflint** | Linter per Terraform che rileva errori, warning e violazioni di best practice nel codice HCL |
| **Workspace** | Meccanismo Terraform per gestire ambienti multipli (dev, staging, prod) con state separati |
| **Ansible Vault** | Funzionalità di Ansible per cifrare variabili e file contenenti dati sensibili nei playbook |
| **Automation API** | Interfaccia programmatica di Pulumi che permette di eseguire operazioni IaC (up, preview, destroy) da codice applicativo senza CLI |
| **Composition (Crossplane)** | Risorsa Crossplane che definisce come assemblare piu risorse gestite (managed resources) in un'unica astrazione di livello superiore |
| **CrossGuard** | Framework di policy-as-code di Pulumi che valida le risorse durante preview e update, scritto nello stesso linguaggio del programma Pulumi |
| **Crossplane** | Framework CNCF Graduated che estende Kubernetes per gestire infrastruttura cloud attraverso Custom Resources e controller di riconciliazione |
| **Infracost** | Strumento open-source che stima i costi cloud analizzando piani Terraform/OpenTofu prima del deploy, integrabile in pipeline CI/CD |
| **KICS (Keeping Infrastructure as Code Secure)** | Scanner di sicurezza open-source di Checkmarx per template IaC che supporta Terraform, CloudFormation, Ansible, Kubernetes e Docker |
| **Moved Block** | Blocco dichiarativo in Terraform 1.1+ che registra il refactoring di risorse (rinominazione, spostamento in moduli) senza ricrearle |
| **OPA (Open Policy Agent)** | Motore di policy universale CNCF che valuta regole scritte in linguaggio Rego su dati JSON, usato per governance IaC |
| **OpenTofu** | Fork open-source di Terraform mantenuto dalla Linux Foundation sotto licenza MPL 2.0, nato dopo il cambio di licenza BSL di HashiCorp |
| **Removed Block** | Blocco dichiarativo in Terraform 1.7+ che permette di rimuovere risorse dallo state senza distruggerle nel cloud |
| **Sentinel** | Framework di policy-as-code proprietario di HashiCorp integrato in Terraform Cloud/Enterprise per enforcement di compliance |
| **Terragrunt** | Wrapper per Terraform che gestisce configurazioni DRY, dipendenze tra moduli, e orchestrazione multi-directory |
| **Terrascan** | Scanner di sicurezza open-source per IaC che verifica conformita a standard come CIS, SOC2, PCI-DSS su codice Terraform, Kubernetes e CloudFormation |
| **tfsec** | Strumento di analisi statica per la sicurezza di codice Terraform, ora integrato nel progetto Trivy di Aqua Security |
| **XRD (CompositeResourceDefinition)** | Definizione schema in Crossplane che specifica la struttura e i parametri di una risorsa composita personalizzata |

> **Nota**: Questo documento copre i fondamenti e gli aspetti avanzati dell'Infrastructure as Code con focus su Terraform e Ansible, i due strumenti dominanti nel settore. Per approfondimenti specifici su ciascun cloud provider, consultare le rispettive sezioni dedicate nella documentazione del progetto. La padronanza dell'IaC e una competenza fondamentale per qualsiasi professionista DevOps e Cloud, e la pratica costante su progetti reali e il modo migliore per consolidarla.
