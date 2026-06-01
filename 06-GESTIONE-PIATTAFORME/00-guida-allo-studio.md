# Gestione Piattaforme — Panoramica e Piano di Studio

Guida allo studio della gestione piattaforme IT, dai fondamenti cloud alla sicurezza
e all'osservabilita in ambienti distribuiti. Questo documento fornisce la struttura
organizzativa, il piano di studio progressivo, gli strumenti di laboratorio e il glossario
di riferimento per il modulo dedicato al platform management.

---

## Indice

1. [Panoramica del Campo](#panoramica-del-campo)
2. [Piano di Studio](#piano-di-studio)
   - [Fase 1: Cloud Fundamentals (settimane 1-4)](#fase-1-cloud-fundamentals--aws-azure-gcp-settimane-1-4)
   - [Fase 2: Container e Orchestrazione (settimane 5-8)](#fase-2-container-e-orchestrazione--docker-kubernetes-settimane-5-8)
   - [Fase 3: IaC e CI/CD (settimane 9-12)](#fase-3-iac-e-cicd--terraform-ansible-pipeline-settimane-9-12)
   - [Fase 4: Osservabilita e Sicurezza (settimane 13-16)](#fase-4-osservabilita-e-sicurezza-settimane-13-16)
   - [Fase 5: Argomenti Avanzati (settimane 17-19)](#fase-5-argomenti-avanzati-settimane-17-19)
3. [Ambiente di Laboratorio](#ambiente-di-laboratorio)
4. [Glossario](#glossario)
5. [Certificazioni Rilevanti](#certificazioni-rilevanti)
6. [Risorse Consigliate](#risorse-consigliate)

---

## Panoramica del Campo

La gestione delle piattaforme IT rappresenta il nucleo operativo su cui poggiano tutte le
applicazioni e i servizi di un'organizzazione moderna. Dalla migrazione al cloud alla
containerizzazione, dall'automazione dell'infrastruttura tramite codice fino al monitoraggio
continuo e alla protezione degli ambienti, questa disciplina richiede competenze
sistemistiche, architetturali e di sicurezza di ampia portata.

### Il Ruolo dell'IT Systems Manager

Un professionista della gestione piattaforme e responsabile dell'intera catena che collega
il codice sorgente all'esperienza utente in produzione:

- Progettare e mantenere infrastrutture cloud multi-account e multi-regione.
- Containerizzare applicazioni e orchestrare deployment su larga scala.
- Codificare l'infrastruttura come codice versionato, testato e riproducibile.
- Costruire pipeline di integrazione e distribuzione continua affidabili.
- Implementare sistemi di osservabilita per rendere trasparente lo stato di ogni componente.
- Garantire conformita normativa e sicurezza a ogni livello dello stack.

### I Pilastri della Gestione Piattaforme

**Cloud Computing** — I tre hyperscaler (Amazon Web Services, Microsoft Azure e Google
Cloud Platform) offrono risorse computazionali on-demand attraverso API. La comprensione
dei modelli di servizio (IaaS, PaaS, SaaS, FaaS) e la capacita di navigare tra centinaia
di servizi managed e fondamentale.

**Infrastructure as Code** — Definire infrastruttura attraverso file di configurazione
dichiarativi. Terraform, Ansible, CloudFormation e Pulumi trasformano l'infrastruttura in
un artefatto versionabile, testabile e riproducibile.

**Container e Orchestrazione** — Docker standardizza il packaging in unita isolate e
portabili. Kubernetes risolve l'esecuzione su larga scala con service discovery,
bilanciamento del carico, self-healing e aggiornamenti senza downtime.

**Osservabilita** — I tre pilastri (metriche, log e tracce distribuite) forniscono la
visibilita necessaria per diagnosticare problemi in sistemi distribuiti.

**Sicurezza** — Aspetto trasversale che permea ogni decisione architetturale: dal minimo
privilegio alla protezione dei segreti, dalla segmentazione di rete alla conformita
normativa. Deve essere integrata fin dalla progettazione (shift-left security).

---

## Piano di Studio

Il percorso e strutturato in cinque fasi progressive che coprono 19 settimane. I riferimenti
tra parentesi quadre indicano le sottocartelle di studio del modulo.

### Fase 1: Cloud Fundamentals — AWS, Azure, GCP (settimane 1-4)

La prima fase costruisce le fondamenta della comprensione cloud. L'obiettivo e sviluppare
una comprensione trasversale dei concetti che si applicano a qualsiasi piattaforma.

#### Settimane 1-2: Amazon Web Services `[01-CLOUD-AWS]`

- Architettura globale AWS: regioni, zone di disponibilita, edge location.
- IAM: utenti, gruppi, ruoli, policy JSON, principio del minimo privilegio.
- Networking: VPC, subnet pubbliche e private, route table, Internet Gateway, NAT Gateway, security group, NACL.
- Compute: EC2 (tipi di istanza, AMI, user data), Auto Scaling Group, Elastic Load Balancer.
- Storage: S3 (classi di storage, lifecycle policy, versioning, encryption), EBS, EFS.
- Database: RDS (Multi-AZ, Read Replica), DynamoDB, ElastiCache.
- Serverless: Lambda (trigger, layer, concurrency), API Gateway, Step Functions.
- Messaging: SQS, SNS, EventBridge.
- Costi: Cost Explorer, Budgets, Reserved Instances, Savings Plans.

**Esercizio chiave**: Deployare un'applicazione web a tre livelli (frontend S3/CloudFront,
backend ECS Fargate, database RDS PostgreSQL) con networking isolato e IAM granulare.

#### Settimane 2-3: Microsoft Azure `[02-CLOUD-AZURE]`

- Struttura organizzativa: management group, subscription, resource group, tag.
- Identita: Entra ID, RBAC, Managed Identity, service principal.
- Networking: Virtual Network, subnet, NSG, Azure Firewall, Application Gateway, Private Endpoint.
- Compute: Virtual Machines, VM Scale Sets, App Service, Azure Functions.
- Storage: Blob Storage (tier hot/cool/archive), Azure Files, Managed Disk.
- Database: Azure SQL Database, Cosmos DB, Azure Cache for Redis.
- Governance: Azure Policy, Blueprints, Microsoft Defender for Cloud.

**Esercizio chiave**: Replicare l'architettura a tre livelli su Azure usando App Service,
Azure SQL e Blob Storage, con Managed Identity per l'autenticazione tra servizi.

#### Settimane 3-4: Google Cloud Platform `[03-CLOUD-GCP]`

- Gerarchia risorse: organization, folder, project, label.
- IAM: ruoli predefiniti e personalizzati, service account, Workload Identity Federation.
- Networking: VPC (shared VPC, VPC peering), subnet, firewall rule, Cloud NAT, Cloud Load Balancing.
- Compute: Compute Engine, Cloud Run, Cloud Functions, GKE.
- Storage: Cloud Storage (classi, lifecycle), Persistent Disk, Filestore.
- Database: Cloud SQL, Firestore, Cloud Spanner, Memorystore.
- Operations: Cloud Monitoring, Cloud Logging, Cloud Trace.

**Esercizio chiave**: Costruire un'architettura serverless su GCP con Cloud Run, Cloud SQL
e Cloud Storage, confrontando costi e complessita con le soluzioni AWS e Azure.

#### Settimana 4: Confronto Multi-Cloud

- Mappatura dei servizi equivalenti tra i tre provider.
- Criteri di scelta: costo, maturita del servizio, lock-in, presenza geografica.
- Strategie multi-cloud vs hybrid-cloud: quando e perche adottarle.
- Landing zone: concetti di base per una struttura organizzativa sicura e scalabile.

---

### Fase 2: Container e Orchestrazione — Docker, Kubernetes (settimane 5-8)

Container e orchestrazione formano la spina dorsale della piattaforma applicativa moderna.

#### Settimane 5-6: Docker Avanzato `[06-DOCKER-AVANZATO]`

- Architettura Docker: daemon, client, registry, image layer, copy-on-write.
- Dockerfile: multi-stage build, ottimizzazione dimensioni, cache delle build.
- Networking Docker: bridge, host, overlay, DNS interno.
- Volumi: named volume, bind mount, tmpfs.
- Docker Compose: servizi multipli, dipendenze, healthcheck, profili.
- Sicurezza: utente non-root, scansione vulnerabilita (Trivy), firma immagini.
- Registry privato: Harbor, ECR, ACR, Artifact Registry.
- Pattern: init container, sidecar, ambassador.

**Esercizio chiave**: Containerizzare un'applicazione composta da frontend, backend, database
e cache con Docker Compose, implementando multi-stage build e scansione di sicurezza.

#### Settimane 7-8: Kubernetes `[05-KUBERNETES]`

- Architettura: control plane (API server, etcd, scheduler, controller manager),
  nodi worker (kubelet, kube-proxy, container runtime).
- Oggetti fondamentali: Pod, ReplicaSet, Deployment, Service (ClusterIP, NodePort, LoadBalancer).
- Configurazione: ConfigMap, Secret, environment variable, volume projection.
- Storage: PersistentVolume (PV), PersistentVolumeClaim (PVC), StorageClass, provisioning dinamico.
- Workload avanzati: StatefulSet, DaemonSet, Job, CronJob.
- Networking: Ingress, Ingress Controller (NGINX, Traefik), NetworkPolicy.
- Helm: chart, values, template, release, repository.
- Scaling: resource request/limit, HorizontalPodAutoscaler, VerticalPodAutoscaler.
- RBAC: Role, ClusterRole, RoleBinding, ClusterRoleBinding, ServiceAccount.
- Troubleshooting: `kubectl describe`, `kubectl logs`, `kubectl exec`, eventi del cluster.

**Esercizio chiave**: Deployare un'applicazione multi-tier su Kubernetes con Helm,
configurando Ingress, PVC, HPA, RBAC e NetworkPolicy.

---

### Fase 3: IaC e CI/CD — Terraform, Ansible, Pipeline (settimane 9-12)

L'automazione dell'infrastruttura e della delivery elimina processi manuali, riduce errori
e aumenta la velocita di rilascio.

#### Settimane 9-10: Terraform `[04-INFRASTRUCTURE-AS-CODE]`

- Concetti: provider, resource, data source, variable, output, locals.
- HCL: sintassi, tipi, espressioni, funzioni built-in.
- Stato: terraform state, backend remoto (S3, Azure Blob, GCS), state locking, state import.
- Moduli: struttura, input/output, registry pubblico, moduli privati, composizione.
- Workflow: `init`, `plan`, `apply`, `destroy`, `import`, `state` subcommands.
- Gestione ambienti: workspace, directory separate, Terragrunt.
- Testing: `terraform validate`, Checkov, tflint, Terratest.
- Pattern avanzati: `count` e `for_each`, dynamic blocks, `moved` blocks.
- Sicurezza: variabili sensibili, integrazione con Vault.

**Esercizio chiave**: Definire l'intera infrastruttura cloud della Fase 1 come codice
Terraform con moduli riutilizzabili, backend remoto e validazione automatica.

#### Settimane 10-11: Ansible `[04-INFRASTRUCTURE-AS-CODE]`

- Architettura agentless: connessione SSH/WinRM, inventario, pattern push.
- Inventario: statico, dinamico (da cloud provider), gruppi, variabili host e group.
- Playbook: play, task, handler, tag, condizionali, loop.
- Moduli: command, shell, file, template, package, service, user, moduli cloud.
- Ruoli: struttura di directory, Galaxy, dipendenze tra ruoli.
- Ansible Vault: cifratura di variabili e file sensibili.
- Template Jinja2: variabili, filtri, condizioni, loop nei file di configurazione.
- Idempotenza: comprendere e verificare che i playbook siano ripetibili senza effetti collaterali.
- Integrazione: Terraform per provisioning, Ansible per configurazione.

**Esercizio chiave**: Scrivere playbook Ansible per la configurazione completa di un server
applicativo: installazione pacchetti, configurazione servizi, deployment dell'applicazione.

#### Settimane 11-12: CI/CD Pipeline `[07-CI-CD]`

- Principi: integrazione continua, distribuzione continua, deployment continuo — distinzioni.
- GitHub Actions: workflow, job, step, action, secret, environment, matrice di build.
- GitLab CI: `.gitlab-ci.yml`, stage, job, artifact, cache, runner.
- Pipeline design: build, lint, test, scan, deploy — stage gate pattern.
- Branching: trunk-based development, GitFlow, impatto sulla pipeline.
- Deployment strategy: rolling update, blue-green, canary, feature flag.
- GitOps: ArgoCD, Flux — reconciliation loop, stato desiderato in Git.

**Esercizio chiave**: Costruire una pipeline CI/CD con GitHub Actions che esegua lint, test,
build Docker, scansione vulnerabilita, push su registry e deploy su Kubernetes tramite ArgoCD.

---

### Fase 4: Osservabilita e Sicurezza (settimane 13-16)

Dopo aver costruito e automatizzato l'infrastruttura, questa fase si concentra sulla
visibilita operativa e sulla protezione dell'intero stack.

#### Settimane 13-14: Monitoraggio e Osservabilita `[08-MONITORING-OBSERVABILITY]`

- I tre pilastri: metriche, log, tracce distribuite — differenze e complementarieta.
- Prometheus: architettura pull-based, PromQL, scraping, alerting rule, recording rule.
- Grafana: dashboard, pannelli, data source, variabili, alerting, provisioning as code.
- Stack ELK/EFK: Elasticsearch, Logstash/Fluentd, Kibana.
- Loki: log aggregation leggera, integrazione con Grafana, LogQL.
- Tracce distribuite: OpenTelemetry, Jaeger, correlazione tra servizi.
- Alerting: soglie statiche e dinamiche, runbook, escalation, on-call rotation.
- SLI, SLO, SLA: definizione degli indicatori di livello di servizio, error budget.
- Metriche: RED (Rate, Errors, Duration), USE (Utilization, Saturation, Errors).

**Esercizio chiave**: Implementare uno stack di osservabilita con Prometheus, Grafana, Loki
e Jaeger per un'applicazione multi-servizio su Kubernetes.

#### Settimane 15-16: Sicurezza delle Piattaforme `[13-SICUREZZA-PIATTAFORME]` `[14-COMPLIANCE]` `[15-SECRETS-MANAGEMENT]`

- Principi: defense in depth, zero trust, least privilege, separation of duty.
- Network security: segmentazione, micro-segmentazione, WAF, DDoS protection.
- mTLS: autenticazione bidirezionale tra servizi, certificate management.
- RBAC: implementazione su Kubernetes, cloud provider e strumenti CI/CD.
- OPA (Open Policy Agent): policy as code, Rego, Gatekeeper su Kubernetes.
- Gestione dei segreti: HashiCorp Vault (secret engine, auth method, policy),
  AWS Secrets Manager, Azure Key Vault, external-secrets-operator.
- Container security: scansione immagini, runtime security (Falco), admission controller.
- Supply chain security: firma delle immagini (Cosign), SBOM, Sigstore.
- Compliance: framework di riferimento (CIS Benchmark, SOC 2, GDPR), audit automatizzato.
- Incident response: playbook di risposta, post-mortem blameless.

**Esercizio chiave**: Configurare Vault per la gestione centralizzata dei segreti con
integrazione Kubernetes, implementare policy OPA/Gatekeeper e scansione di sicurezza.

---

### Fase 5: Argomenti Avanzati (settimane 17-19)

L'ultima fase copre componenti infrastrutturali specializzati che completano una piattaforma
enterprise.

#### Settimana 17: Service Mesh e API Gateway `[09-SERVICE-MESH]` `[16-API-GATEWAY]`

- Service mesh: concetto, data plane e control plane, sidecar pattern.
- Istio: architettura (Envoy, istiod), traffic management, mTLS automatico, osservabilita.
- Linkerd: alternativa leggera, differenze architetturali rispetto a Istio.
- API Gateway: Kong, APISIX — routing, rate limiting, autenticazione, trasformazione richieste.
- Quando serve un service mesh vs un API Gateway vs entrambi.

**Esercizio chiave**: Installare Istio su Kubernetes, configurare traffic splitting per
canary deployment e osservare il traffico tramite Kiali.

#### Settimana 18: Message Queue e Storage Distribuito `[12-MESSAGE-QUEUES]` `[17-STORAGE-DISTRIBUITO]`

- Pattern di messaging: point-to-point, publish/subscribe, fan-out, dead-letter queue.
- Apache Kafka: architettura (broker, topic, partition, consumer group), garanzie di delivery.
- RabbitMQ: exchange, queue, binding, modelli di routing, confronto con Kafka.
- NATS: messaging leggero, JetStream per persistenza.
- Storage distribuito: replicazione, sharding, consistenza, CAP theorem.
- Soluzioni: MinIO (object storage S3-compatible), Ceph (block, object, file).
- Backup e disaster recovery: strategia 3-2-1, RTO, RPO, automatizzazione.

**Esercizio chiave**: Deployare Kafka su Kubernetes con Strimzi operator, configurare
topic e consumer group, implementare dead-letter queue.

#### Settimane 18-19: Load Balancer e Database Management `[10-LOAD-BALANCER-REVERSE-PROXY]` `[11-DATABASE-MANAGEMENT]`

- Load balancing: layer 4 vs layer 7, algoritmi (round-robin, least-connections, IP hash).
- NGINX: reverse proxy, load balancer, TLS termination, configurazione avanzata.
- HAProxy: alta disponibilita, sticky session, health check, ACL.
- Traefik: auto-discovery con Docker e Kubernetes, Let's Encrypt automatico.
- Database in produzione: replica, failover, connection pooling (PgBouncer).
- Backup database: pg_dump, WAL archiving, point-in-time recovery.
- Database operator su Kubernetes: CloudNativePG, Percona Operator.

**Esercizio chiave**: Configurare NGINX come reverse proxy con TLS e load balancing per
un'applicazione multi-istanza, con failover automatico.

#### Riferimento Trasversale: Troubleshooting `[18-TROUBLESHOOTING-E-GUIDE-PRATICHE]`

Il file di troubleshooting e un riferimento costante durante tutto il percorso. Contiene
guide pratiche per la risoluzione dei problemi piu comuni in ambienti cloud e Kubernetes,
pattern di debug per container e networking, e checklist operative per incidenti.

---

## Ambiente di Laboratorio

Un ambiente di laboratorio ben configurato e essenziale per la pratica. La gestione
piattaforme richiede accesso a risorse cloud reali e strumenti locali che simulino ambienti
di produzione.

### Account Cloud — Free Tier

- **AWS Free Tier** — 12 mesi di accesso a servizi core: 750 ore/mese EC2 t2.micro, 5 GB S3,
  750 ore/mese RDS db.t2.micro, 1 milione di invocazioni Lambda/mese. Configurare un budget
  alert a 5 USD per evitare costi imprevisti.
- **Azure Free Account** — 200 USD di credito per 30 giorni piu servizi gratuiti per 12 mesi:
  750 ore B1s VM, 5 GB Blob Storage, 250 GB SQL Database.
- **GCP Free Tier** — 300 USD di credito per 90 giorni piu servizi always-free: f1-micro
  Compute Engine, 5 GB Cloud Storage, 1 GB Firestore.

### Kubernetes Locale

- **minikube** — Cluster Kubernetes locale single-node. Supporta addon per Ingress, Dashboard,
  metrics-server. Ideale per lo studio individuale.
- **k3s** — Distribuzione Kubernetes leggera di Rancher. Binario singolo con footprint ridotto.
  Perfetto per cluster multi-nodo su macchine virtuali locali.
- **kind (Kubernetes in Docker)** — Esegue nodi Kubernetes come container Docker. Eccellente
  per test di integrazione CI/CD.

### Strumenti Locali Essenziali

- **Docker Desktop** — Ambiente Docker completo con Engine, Compose e integrazione Kubernetes.
  Su Linux si puo utilizzare Docker Engine direttamente.
- **Terraform** — Installare tramite `tfenv` per gestire versioni multiple.
- **Ansible** — Installare tramite `pipx` o il package manager di sistema.
- **kubectl** — Client CLI per Kubernetes. Configurare autocompletamento e alias (`alias k=kubectl`).
- **Helm** — Package manager per Kubernetes. Gestire repository di chart.

### Strumenti di Osservabilita e Sicurezza

- **Prometheus + Grafana** — Installabili su Kubernetes tramite kube-prometheus-stack (Helm chart).
- **Loki** — Aggregazione log leggera, installabile tramite Helm.
- **Jaeger** — Tracing distribuito, deployabile su Kubernetes.
- **HashiCorp Vault** — Modalita dev per sperimentazione locale (`vault server -dev`).
- **Trivy** — Scanner di vulnerabilita per immagini container e configurazioni IaC.
- **OPA/Gatekeeper** — Installabile su Kubernetes tramite Helm per l'applicazione di policy.

---

## Glossario

Terminologia essenziale della gestione piattaforme, organizzata per area tematica.

### Modelli di Servizio Cloud

- **IaaS (Infrastructure as a Service)** — Infrastruttura virtualizzata on-demand: VM, rete,
  storage. Esempi: EC2, Azure VM, Compute Engine.
- **PaaS (Platform as a Service)** — Piattaforma gestita per deployment di applicazioni senza
  gestire l'infrastruttura. Esempi: App Service, App Engine, Beanstalk.
- **SaaS (Software as a Service)** — Applicazione completa erogata via internet. Il provider
  gestisce tutto lo stack. Esempi: Gmail, Salesforce, Microsoft 365.
- **FaaS (Function as a Service)** — Modello serverless dove il codice esegue in risposta a
  eventi. Esempi: Lambda, Azure Functions, Cloud Functions.

### Networking Cloud

- **VPC (Virtual Private Cloud)** — Rete virtuale isolata all'interno del cloud provider con
  controllo completo sullo spazio di indirizzamento IP, subnet, route e gateway.
- **Subnet** — Segmento di una VPC con un range CIDR specifico. Pubbliche con accesso diretto
  a Internet, private con comunicazione tramite NAT Gateway.
- **Security Group** — Firewall stateful a livello di istanza che controlla traffico in
  ingresso e uscita con regole permissive (allow-only).
- **NACL (Network Access Control List)** — Firewall stateless a livello di subnet con regole
  numerate di allow e deny.
- **IAM (Identity and Access Management)** — Sistema che definisce chi puo fare cosa su quali
  risorse e sotto quali condizioni.

### Servizi AWS Core

- **S3 (Simple Storage Service)** — Object storage con durabilita 99,999999999%. Supporta
  versioning, lifecycle policy, encryption e access control granulare.
- **EC2 (Elastic Compute Cloud)** — Macchine virtuali scalabili con ampia scelta di tipi di
  istanza ottimizzati per compute, memoria, storage o GPU.
- **RDS (Relational Database Service)** — Database relazionale gestito con backup automatico,
  patching, replica e failover. Supporta MySQL, PostgreSQL, MariaDB, Oracle, SQL Server.
- **Lambda** — Servizio FaaS che esegue codice in risposta a eventi, scalando automaticamente
  da zero a migliaia di esecuzioni concorrenti.

### Kubernetes Managed

- **AKS (Azure Kubernetes Service)** — Kubernetes gestito di Azure con integrazione Entra ID,
  Azure Monitor e Azure Policy.
- **EKS (Elastic Kubernetes Service)** — Kubernetes gestito di AWS con integrazione IAM, VPC
  networking e supporto Fargate.
- **GKE (Google Kubernetes Engine)** — Kubernetes gestito di Google Cloud, considerato il piu
  maturo grazie alle origini di Kubernetes in Google.

### Oggetti Kubernetes

- **Helm** — Package manager per Kubernetes che organizza manifest in chart riutilizzabili
  con valori parametrizzabili.
- **Ingress** — Risorsa che gestisce l'accesso HTTP/HTTPS esterno ai servizi del cluster.
  Richiede un Ingress Controller (NGINX, Traefik).
- **ConfigMap** — Oggetto per dati di configurazione non sensibili come coppie chiave-valore,
  montabili come volume o variabili d'ambiente.
- **Secret** — Simile a ConfigMap ma per dati sensibili. Codificato in base64 per default;
  richiede encryption at rest per una gestione sicura.
- **PV (PersistentVolume)** — Risorsa di storage nel cluster, provisionata staticamente o
  dinamicamente, indipendente dal ciclo di vita del Pod.
- **PVC (PersistentVolumeClaim)** — Richiesta di storage da parte di un Pod. Specifica
  dimensione, access mode e StorageClass.
- **StatefulSet** — Controller per workload stateful con identita stabile, storage persistente
  e ordine di deployment prevedibile. Usato per database e sistemi distribuiti.
- **DaemonSet** — Controller che esegue una copia del Pod su ogni nodo del cluster. Tipico
  per agenti di logging e monitoring.

### Infrastructure as Code

- **Terraform State** — File che mappa risorse nel codice a risorse reali nel cloud. Senza
  stato, Terraform non sa cosa gestisce.
- **Terraform Provider** — Plugin che implementa l'interazione con un'API specifica. Ogni
  provider espone risorse e data source.
- **Terraform Module** — Insieme riutilizzabile di risorse raggruppate logicamente con
  variabili di input e output.
- **Ansible Playbook** — File YAML che definisce una sequenza di task da eseguire su un
  insieme di host, invocando moduli per raggiungere uno stato desiderato.
- **Ansible Role** — Struttura standardizzata per organizzare task, handler, variabili e
  template in unita riutilizzabili.
- **Idempotenza** — Eseguire la stessa operazione piu volte produce sempre lo stesso risultato
  senza effetti collaterali. Proprieta fondamentale dell'IaC.

### Osservabilita

- **Prometheus** — Sistema di monitoraggio open-source con modello pull-based. Archivia
  metriche come serie temporali e le interroga con PromQL.
- **Grafana** — Piattaforma di visualizzazione e dashboarding. Si connette a molteplici
  data source per creare dashboard interattive.
- **ELK (Elasticsearch, Logstash, Kibana)** — Stack per aggregazione, indicizzazione e
  visualizzazione dei log.
- **Jaeger** — Piattaforma di tracing distribuito che traccia il percorso delle richieste
  attraverso i microservizi.
- **OpenTelemetry** — Framework vendor-neutral per la raccolta di metriche, log e tracce
  con SDK e collector standardizzati.
- **PromQL** — Linguaggio di query di Prometheus per selezionare, aggregare e calcolare
  metriche con operazioni vettoriali e funzioni.

### Sicurezza

- **mTLS (mutual TLS)** — Autenticazione TLS bidirezionale dove sia client che server
  presentano certificati. Implementato automaticamente dai service mesh.
- **RBAC (Role-Based Access Control)** — Modello di autorizzazione che assegna permessi a
  ruoli e associa ruoli a utenti. Presente in Kubernetes, cloud provider e CI/CD.
- **OPA (Open Policy Agent)** — Motore di policy generico che valuta regole in Rego.
  Gatekeeper e il suo adapter per Kubernetes.
- **Vault** — Piattaforma HashiCorp per gestione centralizzata di segreti, cifratura come
  servizio e gestione delle identita.
- **Zero Trust** — Modello di sicurezza che non assume fiducia implicita per nessuna entita.
  Ogni richiesta viene autenticata e autorizzata.
- **SBOM (Software Bill of Materials)** — Inventario di tutti i componenti software inclusi
  in un'applicazione. Essenziale per supply chain security.

### Concetti Trasversali

- **GitOps** — Paradigma dove lo stato desiderato e dichiarato in Git. Un operatore (ArgoCD,
  Flux) riconcilia continuamente lo stato reale con quello desiderato.
- **SLI (Service Level Indicator)** — Metrica quantitativa: disponibilita, latenza, throughput.
- **SLO (Service Level Objective)** — Obiettivo target per un SLI.
- **SLA (Service Level Agreement)** — Accordo contrattuale con conseguenze per mancato
  rispetto degli SLO.
- **Error Budget** — Quantita di errore tollerata prima di violare un SLO.
- **CAP Theorem** — In un sistema distribuito e impossibile garantire simultaneamente
  Consistency, Availability e Partition tolerance.
- **Drift** — Divergenza tra stato dell'infrastruttura reale e quello definito nel codice.

---

## Certificazioni Rilevanti

### AWS Solutions Architect — Associate (SAA-C03)

Certifica la capacita di progettare architetture resilienti, performanti e cost-optimized su
AWS. Copre servizi compute, storage, networking, database e sicurezza. Allineata con le
settimane 1-2. Certificazione cloud piu richiesta dal mercato.

### Microsoft Azure Administrator — Associate (AZ-104)

Certifica la gestione di identita, governance, storage, compute e virtual network in Azure.
Include monitoring, backup e disaster recovery. Utile in ambienti enterprise dove Azure e
dominante.

### Certified Kubernetes Administrator (CKA)

Certifica installazione, configurazione e gestione di cluster Kubernetes di produzione.
Esame pratico basato su laboratorio che copre networking, storage, sicurezza e
troubleshooting. Allineata con la Fase 2.

### Certified Kubernetes Security Specialist (CKS)

Estensione del CKA focalizzata sulla sicurezza: hardening del cluster, supply chain security,
runtime security e monitoring. Prerequisito: CKA valido. Allineata con la Fase 4.

### HashiCorp Terraform Associate (003)

Certifica la comprensione dei concetti IaC, della workflow Terraform e delle best practice.
Copre state management, moduli, provider e HCL. Allineata con le settimane 9-10.

### AWS DevOps Engineer — Professional (DOP-C02)

Certificazione avanzata che copre CI/CD, monitoring, logging, incident response e
automazione su AWS. Consigliata dopo aver completato tutte le fasi.

### Prometheus Certified Associate (PCA)

Certificazione CNCF che valida competenze su Prometheus: architettura, PromQL, service
discovery, alerting e integrazione con Grafana. Allineata con la Fase 4.

---

## Risorse Consigliate

### Documentazione Ufficiale

- **AWS Documentation** (docs.aws.amazon.com) — Riferimento completo per tutti i servizi AWS.
  Le guide "Getting Started" e i "Well-Architected Labs" sono particolarmente utili.
- **Microsoft Learn** (learn.microsoft.com) — Piattaforma gratuita con percorsi strutturati,
  sandbox e laboratori interattivi per Azure.
- **Google Cloud Documentation** (cloud.google.com/docs) — Tutorial, quickstart e architecture
  center per pattern di riferimento.
- **Kubernetes Documentation** (kubernetes.io/docs) — Tutorial progressivi, concept guide e
  task reference. Il tutorial "Learn Kubernetes Basics" e il punto di partenza consigliato.
- **Terraform Documentation** (developer.hashicorp.com/terraform) — Guide, tutorial e
  reference per provider e moduli.

### Piattaforme di Apprendimento

- **KodeKloud** (kodekloud.com) — Laboratori pratici per Kubernetes, Docker, Terraform,
  Ansible e certificazioni cloud.
- **A Cloud Guru / Pluralsight** — Corsi strutturati con laboratori per certificazioni AWS,
  Azure e GCP.
- **Linux Foundation Training** (training.linuxfoundation.org) — Corsi ufficiali per CKA,
  CKS e CKAD con simulatori d'esame.

### Libri

- **Kubernetes: Up and Running** di Brendan Burns, Joe Beda, Kelsey Hightower — Testo di
  riferimento per Kubernetes, scritto dai creatori del progetto.
- **Terraform: Up and Running** di Yevgeniy Brikman — Guida pratica all'IaC con Terraform
  che copre moduli, testing e pattern avanzati.
- **The Phoenix Project** di Gene Kim, Kevin Behr, George Spafford — Romanzo che illustra i
  principi DevOps attraverso una narrativa aziendale.

### Comunita e Riferimenti

- **CNCF Landscape** (landscape.cncf.io) — Mappa interattiva dell'ecosistema cloud-native.
- **The Twelve-Factor App** (12factor.net) — Metodologia per costruire applicazioni cloud-native.
- **AWS Well-Architected Framework** — Best practice organizzate in pilastri: eccellenza
  operativa, sicurezza, affidabilita, efficienza, ottimizzazione dei costi, sostenibilita.

---

*Ultimo aggiornamento: 2026-03-28*
