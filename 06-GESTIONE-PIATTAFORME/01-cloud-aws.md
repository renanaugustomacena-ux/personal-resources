---
corso: "Gestione Piattaforme e DevOps"
fase: "1 — Cloud Provider"
modulo: 1
titolo: "AWS (Amazon Web Services) — Documentazione Completa"
versione: "2026"
livello: "Avanzato"
prerequisiti: ["02-cloud-azure", "03-cloud-gcp", "04-infrastructure-as-code"]
obiettivi:
  - "Comprendere l'infrastruttura globale AWS e i principi del Well-Architected Framework"
  - "Progettare architetture multi-account con AWS Organizations e Service Control Policies"
  - "Configurare networking avanzato con VPC, Transit Gateway e architetture multi-region"
  - "Implementare strategie di sicurezza con IAM, GuardDuty, Security Hub e OIDC federation"
  - "Gestire costi, limiti di servizio e ottimizzazione delle risorse in ambienti produttivi"
tag: [aws, cloud, iam, vpc, ec2, s3, lambda, well-architected, multi-account]
---

# AWS (Amazon Web Services) — Documentazione Completa

> **Modulo:** Piattaforme cloud-native · Modulo 01 · **Tempo:** 90 min · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Comprendere l'infrastruttura globale AWS e i principi del Well-Architected Framework
> 2. Progettare architetture multi-account con AWS Organizations e Service Control Policies
> 3. Configurare networking avanzato con VPC, Transit Gateway e architetture multi-region
> 4. Implementare strategie di sicurezza con IAM, GuardDuty, Security Hub e OIDC federation
> 5. Gestire costi, limiti di servizio e ottimizzazione delle risorse in ambienti produttivi
>
> **Prerequisiti:** [Azure](02-cloud-azure.md) · [GCP](03-cloud-gcp.md) · [IaC](04-infrastructure-as-code.md)
> **Tempo stimato:** 90 min · **Livello:** Avanzato

## Idee guida

1. **AWS = mercato leader, ricco di servizi.** Curva apprendimento ripida.
2. **Well-Architected Framework: 6 pilastri.** Reliability, Security, Performance, Cost, Operational, Sustainability.
3. **OIDC > IAM key per CI/CD.** Trust pipeline GitHub/GitLab tramite federation.
4. **Multi-region per DR mandatory per produzione.** us-east-1 e single point of failure storico.


## Indice

1. [Panoramica dell'Infrastruttura Globale AWS](#1-panoramica-dellinfrastruttura-globale-aws)
2. [IAM — Identity and Access Management](#2-iam--identity-and-access-management)
3. [Networking — VPC](#3-networking--vpc)
4. [Compute — EC2](#4-compute--ec2)
5. [Storage — S3, EBS, EFS, FSx](#5-storage--s3-ebs-efs-fsx)
6. [Database — RDS, Aurora e DynamoDB](#6-database--rds-aurora-e-dynamodb)
7. [Serverless — Lambda, API Gateway, Step Functions, EventBridge](#7-serverless--lambda-api-gateway-step-functions-eventbridge)
8. [Containers — ECS, EKS, ECR, App Runner](#8-containers--ecs-eks-ecr-app-runner)
9. [Monitoring — CloudWatch, X-Ray, CloudTrail](#9-monitoring--cloudwatch-x-ray-cloudtrail)
10. [Security](#10-security)
11. [Infrastructure as Code — CloudFormation, CDK, Terraform](#11-infrastructure-as-code--cloudformation-cdk-terraform)
12. [Cost Management](#12-cost-management)
13. [Best Practices](#13-best-practices)
14. [Well-Architected Framework — I 6 Pilastri](#14-well-architected-framework--i-6-pilastri)
15. [Pattern Architetturali](#15-pattern-architetturali)
16. [Troubleshooting — Problemi Comuni e Soluzioni](#16-troubleshooting--problemi-comuni-e-soluzioni)
17. [FAQ — Domande Frequenti](#17-faq--domande-frequenti)

---

## 1. Panoramica dell'Infrastruttura Globale AWS

Amazon Web Services e il provider cloud piu ampio e maturo sul mercato, con oltre 200 servizi distribuiti su un'infrastruttura globale progettata per alta disponibilita, tolleranza ai guasti e bassa latenza.

### Regions (Regioni)

Una **Region** e un'area geografica fisica che contiene piu data center isolati. Ogni regione e indipendente dalle altre, con il proprio set di servizi e infrastruttura. AWS gestisce oltre 30 regioni nel mondo. La scelta della regione dipende da:

- **Conformita normativa**: alcune legislazioni (come il GDPR europeo) richiedono che i dati risiedano in specifiche aree geografiche. Per workload destinati a utenti europei, le regioni `eu-west-1` (Irlanda), `eu-central-1` (Francoforte) o `eu-south-1` (Milano) sono scelte tipiche.
- **Latenza**: per ottimizzare i tempi di risposta, si seleziona la regione piu vicina agli utenti finali.
- **Disponibilita dei servizi**: non tutti i servizi AWS sono disponibili in tutte le regioni. I servizi piu recenti vengono lanciati prima nelle regioni principali come `us-east-1` (Virginia del Nord).
- **Costo**: i prezzi variano tra regioni. Le regioni negli Stati Uniti tendono ad essere meno costose rispetto a quelle in Asia o Sud America.

### Availability Zones (Zone di Disponibilita)

Ogni regione contiene almeno due (tipicamente tre o piu) **Availability Zones** (AZ). Ciascuna AZ e costituita da uno o piu data center fisicamente separati, dotati di alimentazione e connettivita ridondanti. Le AZ sono collegate tramite reti a bassa latenza, ma sufficientemente distanti da essere isolate in caso di disastri localizzati.

Distribuire le applicazioni su piu AZ garantisce alta disponibilita: se una AZ diventa irraggiungibile, le istanze nelle altre continuano a funzionare. Servizi come RDS Multi-AZ, ELB e Auto Scaling sfruttano nativamente questa distribuzione.

### Edge Locations e Regional Edge Caches

Le **Edge Locations** sono punti di presenza (PoP) distribuiti globalmente, utilizzati da **Amazon CloudFront** (CDN) e **Route 53** (DNS). Esistono oltre 400 edge locations che servono contenuti con la minima latenza possibile tramite caching.

Le **Regional Edge Caches** si posizionano tra le edge locations e la regione di origine, mantenendo in cache contenuti meno frequenti per ridurre le richieste al server di origine.

### AWS Local Zones e Wavelength Zones

Le **Local Zones** sono estensioni di una regione posizionate in prossimita di grandi centri urbani, per applicazioni che richiedono latenze nell'ordine dei millisecondi singoli. Le **Wavelength Zones** integrano l'infrastruttura AWS direttamente nelle reti 5G dei provider di telecomunicazioni, abilitando applicazioni ultra-low-latency per dispositivi mobili.

### AWS Global Accelerator

**AWS Global Accelerator** utilizza la rete globale di AWS per instradare il traffico degli utenti verso l'endpoint applicativo ottimale in base a salute, prossimita geografica e policy di routing configurate. Fornisce due indirizzi IP anycast statici che fungono da punto di ingresso fisso per l'applicazione, indipendentemente dalla regione in cui le risorse sono distribuite. A differenza di CloudFront (che opera a livello applicativo per il caching dei contenuti), Global Accelerator opera a livello di rete (Layer 4) ottimizzando il percorso TCP/UDP.

---

## 2. IAM — Identity and Access Management

IAM e il servizio fondamentale di AWS per il controllo degli accessi. E un servizio globale (non regionale): ogni richiesta ad AWS passa attraverso IAM per autenticazione e autorizzazione.

### Users (Utenti)

Un **IAM User** rappresenta una persona o un servizio che interagisce con AWS. Un utente appena creato non ha alcun permesso: vige il principio del **least privilege**. Le credenziali possono includere una password per la Console AWS e/o **Access Keys** per l'accesso programmatico tramite CLI, SDK o API.

### Groups (Gruppi)

Un **IAM Group** e una collezione di utenti IAM. I permessi assegnati a un gruppo vengono ereditati da tutti i membri. Si definiscono gruppi funzionali (`Developers`, `Admins`, `ReadOnlyUsers`) e si aggiungono gli utenti. Un utente puo appartenere a piu gruppi. I gruppi non supportano il nesting e non sono un'identita referenziabile in resource-based policy.

### Roles (Ruoli)

Un **IAM Role** e un'identita con permessi specifici assumibile temporaneamente da entita fidate. A differenza degli utenti, i ruoli non hanno credenziali permanenti: AWS fornisce credenziali temporanee tramite **AWS STS**. Casi d'uso principali:

- **EC2 Instance Roles**: permettono alle istanze EC2 di accedere ad altri servizi AWS senza dover inserire credenziali nel codice.
- **Cross-Account Access**: consentono a utenti di un account AWS di accedere a risorse in un altro account.
- **Service-Linked Roles**: ruoli predefiniti che permettono ai servizi AWS di operare per conto dell'utente.
- **Federation**: permettono a utenti autenticati tramite sistemi esterni (SAML 2.0, OIDC) di ottenere accesso temporaneo alle risorse AWS.

### Policies (Policy) — Formato JSON

Le policy IAM sono documenti JSON che definiscono i permessi. Ogni policy contiene uno o piu **Statement**, ciascuno dei quali specifica:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3ReadAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::mio-bucket",
        "arn:aws:s3:::mio-bucket/*"
      ],
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "203.0.113.0/24"
        }
      }
    }
  ]
}
```

- **Effect**: `Allow` o `Deny`. In caso di conflitto, `Deny` ha sempre la precedenza.
- **Action**: le operazioni API permesse o negate (es. `s3:GetObject`, `ec2:RunInstances`). Si possono usare wildcard come `s3:*`.
- **Resource**: le risorse AWS specifiche a cui si applica la policy, identificate tramite ARN (Amazon Resource Name).
- **Condition** (opzionale): condizioni aggiuntive che devono essere soddisfatte affinche la policy si applichi (indirizzo IP sorgente, tag, orario, MFA attiva, ecc.).

Esistono diversi tipi di policy:

- **AWS Managed Policies**: create e gestite da AWS, coprono casi d'uso comuni (es. `AmazonS3ReadOnlyAccess`).
- **Customer Managed Policies**: create dall'utente, riutilizzabili su piu entita.
- **Inline Policies**: incorporate direttamente in un singolo utente, gruppo o ruolo. Da usare con cautela poiche non sono riutilizzabili.

### Identity-Based vs Resource-Based Policies

Le policy IAM si dividono in due categorie fondamentali che determinano dove vengono applicate:

**Identity-Based Policies** sono associate a utenti, gruppi o ruoli. Definiscono cosa l'identita puo fare. Esempio: "L'utente Mario puo leggere oggetti dal bucket `documenti`".

**Resource-Based Policies** sono associate direttamente alla risorsa AWS (bucket S3, coda SQS, chiave KMS, topic SNS). Specificano chi puo accedere alla risorsa e con quali azioni. Contengono un campo `Principal` che indica l'identita autorizzata. Esempio: "L'account `111122223333` puo pubblicare messaggi su questo topic SNS".

Differenza chiave: le resource-based policies consentono l'accesso **cross-account** senza che l'entita chiamante debba assumere un ruolo. Quando un'identita dell'account A accede a una risorsa dell'account B tramite resource-based policy, l'identita mantiene i propri permessi nell'account A contemporaneamente — non avviene lo switch di contesto tipico dell'assunzione di ruolo.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CrossAccountAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111122223333:root"
      },
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:eu-central-1:444455556666:ordini-coda"
    }
  ]
}
```

### Permission Boundaries (Confini dei Permessi)

Le **Permission Boundaries** sono policy gestite che definiscono il perimetro massimo dei permessi che un'identita IAM puo ottenere. Non concedono permessi: limitano i permessi concedibili tramite identity-based policy.

Caso d'uso principale: delegare la creazione di ruoli e utenti IAM a sviluppatori senza rischiare privilege escalation. Un amministratore puo consentire a uno sviluppatore di creare ruoli IAM, a condizione che ogni ruolo creato abbia un permission boundary specifico.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOnlySpecificServices",
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "dynamodb:*",
        "lambda:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

L'effetto risultante e l'**intersezione** tra la permission boundary e le identity-based policy: un permesso deve essere presente in entrambe per essere effettivo. Se la identity-based policy concede `ec2:*` ma la permission boundary consente solo `s3:*`, l'accesso EC2 viene negato.

### Logica di Valutazione delle Policy IAM

Quando AWS riceve una richiesta API, la valutazione dei permessi segue un ordine preciso e deterministico:

```
1. Deny esplicito?        --> SI --> DENY (fine)
                           --> NO --> passo 2
2. SCP (Organizations)?    --> Nega? --> DENY (fine)
                           --> Consente? --> passo 3
3. Resource-based policy?  --> Allow con Principal esplicito? --> ALLOW (fine)
                           --> Altrimenti --> passo 4
4. Permission boundary?    --> Non consente? --> DENY (fine)
                           --> Consente? --> passo 5
5. Session policy?         --> Non consente? --> DENY (fine)
                           --> Consente? --> passo 6
6. Identity-based policy?  --> Allow? --> ALLOW
                           --> Altrimenti --> DENY (implicit deny)
```

Regole chiave:
- **Deny esplicito vince sempre** su qualsiasi Allow, indipendentemente da dove proviene.
- **Default implicit deny**: in assenza di un Allow esplicito, l'accesso e negato.
- Le **SCP** agiscono come guardrail: filtrano i permessi prima che identity-based policies vengano valutate.
- Le **permission boundaries** agiscono come limiti massimi: restringono cio che le identity-based policies possono concedere.
- Per l'accesso **cross-account** tramite ruoli, sia l'account di origine che quello di destinazione devono consentire l'azione.

### MFA (Multi-Factor Authentication)

L'autenticazione multi-fattore aggiunge un ulteriore livello di sicurezza richiedendo, oltre alla password, un codice generato da un dispositivo. Tipi supportati:

- **Virtual MFA Device**: applicazioni come Google Authenticator o Authy.
- **U2F Security Key**: chiavi hardware come YubiKey.
- **Hardware MFA Device**: dispositivi dedicati che generano codici a tempo.

E fortemente consigliato abilitare MFA sull'account root e su tutti gli utenti con privilegi elevati. Si possono configurare policy che richiedono MFA per operazioni sensibili, ad esempio aggiungendo una condition `aws:MultiFactorAuthPresent` nelle policy IAM.

### AWS IAM Identity Center (ex SSO)

**IAM Identity Center** e il servizio consigliato per gestire l'accesso centralizzato a piu account AWS e applicazioni cloud. Si integra con provider di identita esterni (Active Directory, Okta, Azure AD) tramite SAML 2.0 o SCIM. Consente di definire **Permission Sets** (insiemi di policy) assegnabili a utenti e gruppi federati per ciascun account dell'organizzazione, eliminando la necessita di creare utenti IAM individuali in ogni account.

### Access Keys

Le Access Keys sono composte da un **Access Key ID** (pubblico) e un **Secret Access Key** (segreto, visibile solo al momento della creazione). Ogni utente puo avere al massimo due coppie attive, consentendo la rotazione senza downtime. Il flusso di rotazione: creare una nuova chiave, aggiornare le applicazioni, disattivare la vecchia, verificare, eliminare.

### IAM Access Analyzer

**IAM Access Analyzer** identifica risorse condivise con entita esterne all'organizzazione o all'account. Analizza bucket S3, ruoli IAM, chiavi KMS, code SQS, secret di Secrets Manager e funzioni Lambda. Genera **findings** quando rileva accessi pubblici o cross-account non intenzionali.

Access Analyzer offre anche la funzionalita di **policy generation**: analizza i log CloudTrail per generare policy IAM basate sull'attivita effettiva di un'identita, trasformando permessi ampi in permessi minimi basati sull'utilizzo reale. Questa funzionalita e fondamentale per implementare il least privilege in modo pragmatico: si parte da permessi ampi, si osserva l'utilizzo effettivo per un periodo (30-90 giorni), poi si restringe la policy ai soli permessi utilizzati.

Supporta anche la **validazione delle policy** durante la creazione: segnala errori, warning e suggerimenti prima che la policy venga applicata.

### IAM Best Practices

- Non utilizzare mai l'account root per operazioni quotidiane; proteggerlo con MFA e conservare le credenziali in modo sicuro.
- Applicare il principio del **least privilege**: concedere solo i permessi strettamente necessari.
- Utilizzare i gruppi per assegnare i permessi piuttosto che policy individuali.
- Preferire i ruoli IAM alle access keys per le applicazioni in esecuzione su servizi AWS.
- Abilitare MFA per tutti gli utenti, specialmente quelli con privilegi amministrativi.
- Ruotare regolarmente le access keys e rimuovere quelle non utilizzate.
- Utilizzare **IAM Access Analyzer** per identificare risorse condivise con entita esterne.
- Configurare una password policy robusta (lunghezza minima, complessita, scadenza).
- Monitorare l'attivita IAM tramite **CloudTrail**.

### AWS Organizations e Service Control Policies (SCPs)

**AWS Organizations** gestisce centralmente piu account AWS raggruppandoli in **Organizational Units** (OU), fornendo isolamento tra workload, separazione dei costi e confini di sicurezza.

Le **Service Control Policies (SCPs)** definiscono il perimetro massimo dei permessi per gli account membri. Anche se una policy IAM concede un permesso, una SCP puo bloccarlo. Le SCP non concedono permessi: definiscono i limiti entro cui le policy IAM operano.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRegionsOutsideEU",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "eu-central-1",
            "eu-west-1",
            "eu-south-1"
          ]
        }
      }
    }
  ]
}
```

Questo esempio di SCP impedisce qualsiasi operazione al di fuori delle regioni europee specificate, garantendo la conformita con i requisiti di residenza dei dati.

### Architettura Multi-Account con AWS Organizations

Una struttura organizzativa matura prevede OU separate per funzione:

```
Root
 ├── Security OU
 │    ├── Log Archive Account      (CloudTrail, Config, VPC Flow Logs centralizzati)
 │    ├── Security Tooling Account (GuardDuty delegated admin, Security Hub)
 │    └── Audit Account            (accesso read-only cross-account)
 ├── Infrastructure OU
 │    ├── Networking Account       (Transit Gateway, Direct Connect, DNS)
 │    └── Shared Services Account  (CI/CD, artifact registries, AMI condivise)
 ├── Workloads OU
 │    ├── Prod OU
 │    │    ├── App-A Prod Account
 │    │    └── App-B Prod Account
 │    ├── Staging OU
 │    │    ├── App-A Staging Account
 │    │    └── App-B Staging Account
 │    └── Dev OU
 │         ├── App-A Dev Account
 │         └── App-B Dev Account
 └── Sandbox OU
      └── Developer Sandbox Accounts (con SCP restrittive e budget ridotto)
```

Vantaggi dell'architettura multi-account:
- **Isolamento blast radius**: un problema in un account non impatta gli altri.
- **Limiti di servizio indipendenti**: ogni account ha i propri limiti API/risorse.
- **Separazione costi netta**: allocazione immediata senza tag.
- **Confini di sicurezza**: le credenziali compromesse in un account non hanno accesso agli altri.
- **Conformita**: account separati per dati regolamentati (PCI, HIPAA).

### AWS Control Tower

**AWS Control Tower** automatizza il setup e la governance dell'ambiente multi-account. Costruisce una **Landing Zone** con:

- OU pre-configurate (Security, Sandbox)
- Account obbligatori: Management, Log Archive, Audit
- **Guardrails** (controlli) pre-configurati in tre categorie:
  - **Mandatory**: abilitati automaticamente, non disattivabili (es. proibire l'accesso pubblico ai log)
  - **Strongly recommended**: best practices consigliate (es. abilitare CloudTrail in tutte le regioni)
  - **Elective**: opzionali per esigenze specifiche (es. limitare le regioni disponibili)

Guardrails implementati come:
- **Preventive guardrails**: SCP che bloccano azioni non conformi
- **Detective guardrails**: AWS Config Rules che rilevano risorse non conformi
- **Proactive guardrails**: hook CloudFormation che validano risorse prima del deployment

**Account Factory** consente la creazione standardizzata di nuovi account tramite Service Catalog, applicando automaticamente la configurazione di rete (VPC pre-configurata), i guardrails dell'OU di destinazione e le baseline di sicurezza. Il **Customizations for AWS Control Tower (CfCT)** permette di estendere la Landing Zone con template CloudFormation personalizzati applicati automaticamente a nuovi account.

---

## 3. Networking — VPC

### VPC (Virtual Private Cloud)

Una **VPC** e una rete virtuale isolata all'interno di AWS. Ogni VPC e confinata a una singola regione ma si estende su tutte le AZ. Si definisce un blocco CIDR IPv4 (es. `10.0.0.0/16`) con netmask tra `/16` (65.536 indirizzi) e `/28` (16 indirizzi). Ogni account ha una Default VPC in ogni regione; per la produzione si creano VPC personalizzate.

Si possono aggiungere **CIDR secondari** alla VPC (fino a 5 blocchi aggiuntivi) per espandere lo spazio di indirizzi. AWS supporta anche **IPv6**: si puo associare un blocco CIDR IPv6 `/56` fornito da Amazon alla VPC e blocchi `/64` alle subnet per abilitare il dual-stack.

### Subnets — Pubbliche e Private

Le **Subnets** suddividono la VPC in segmenti, ciascuno in una singola AZ. La distinzione pubblica/privata dipende dal routing:

- **Subnet pubblica**: route table con rotta verso Internet Gateway (`0.0.0.0/0 -> igw-xxx`). Le istanze possono avere IP pubblici.
- **Subnet privata**: nessuna rotta diretta verso Internet. Per l'accesso in uscita, usano un NAT Gateway in una subnet pubblica.

Pattern tipico con due livelli per AZ:

```
VPC 10.0.0.0/16
  AZ-a:
    Subnet pubblica  10.0.1.0/24  (load balancer, bastion host)
    Subnet privata   10.0.10.0/24 (application server)
    Subnet privata   10.0.20.0/24 (database)
  AZ-b:
    Subnet pubblica  10.0.2.0/24
    Subnet privata   10.0.11.0/24
    Subnet privata   10.0.21.0/24
```

### Progettazione CIDR e Pianificazione IP

La pianificazione degli indirizzi IP e critica per evitare conflitti e consentire il peering:

- Evitare sovrapposizioni tra VPC che dovranno comunicare (peering, Transit Gateway).
- Riservare spazio per crescita futura: un `/16` (65.536 IP) per VPC di produzione e un buon punto di partenza.
- Usare blocchi CIDR dalla RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- Pianificare le subnet con dimensioni adeguate: `/24` (254 IP utilizzabili) per la maggior parte dei casi, `/20` per subnet con molti container o Lambda (ENI-intensive).
- AWS riserva 5 indirizzi per subnet: .0 (network), .1 (VPC router), .2 (DNS), .3 (riservato), .255 (broadcast).

### Internet Gateway (IGW)

L'**Internet Gateway** consente la comunicazione bidirezionale tra VPC e Internet. E altamente disponibile e ridondante. Una VPC ha al massimo un IGW. Esegue il NAT uno-a-uno per le istanze con IP pubblici.

### NAT Gateway

Il **NAT Gateway** consente alle istanze nelle subnet private di avviare connessioni verso Internet senza essere raggiungibili dall'esterno. Deve essere in una subnet pubblica con un **Elastic IP** associato. Banda fino a 100 Gbps. Per alta disponibilita, creare un NAT Gateway per ogni AZ utilizzata.

Considerazioni sui costi: il NAT Gateway addebita per ora di funzionamento e per GB di traffico elaborato. Per workload ad alto volume, valutare alternative come VPC Endpoints per il traffico verso servizi AWS (eliminando il passaggio attraverso il NAT Gateway) o NAT Instance (istanza EC2 configurata per NAT, meno costosa ma con gestione manuale e limitazioni di banda).

### Route Tables (Tabelle di Routing)

Ogni subnet e associata a una **Route Table** che determina l'instradamento del traffico. Contiene una rotta locale implicita per il CIDR della VPC e rotte personalizzate verso destinazioni esterne (IGW, NAT Gateway, VPC Peering, Transit Gateway, VPN Gateway). Le rotte piu specifiche hanno la precedenza. Ogni subnet puo essere associata a una sola route table; una route table puo essere condivisa tra piu subnet.

Esempio di route table per subnet privata:

| Destinazione     | Target           | Descrizione                        |
|------------------|------------------|------------------------------------|
| 10.0.0.0/16      | local            | Traffico interno VPC               |
| 0.0.0.0/0        | nat-gw-xxx       | Internet via NAT Gateway           |
| 172.16.0.0/16    | pcx-xxx          | VPC Peering verso VPC condivisa    |
| pl-xxx (S3)      | vpce-xxx         | Gateway endpoint S3                |

### VPC Endpoints

I **VPC Endpoints** consentono di connettere la VPC ai servizi AWS senza passare attraverso Internet, NAT Gateway o VPN. Esistono due tipi:

- **Gateway Endpoints**: gratuiti, disponibili per S3 e DynamoDB. Si aggiunge una rotta nella route table.
- **Interface Endpoints** (PrivateLink): creano un'interfaccia di rete elastica (ENI) nella subnet con un indirizzo IP privato. Supportano la maggior parte dei servizi AWS e servizi di terze parti. Addebitati per ora e per GB trasferito.

L'uso di VPC Endpoints migliora la sicurezza (il traffico non attraversa Internet) e puo ridurre i costi di trasferimento dati eliminando la necessita del NAT Gateway per l'accesso ai servizi AWS.

**AWS PrivateLink** consente di esporre i propri servizi privatamente ad altre VPC o account tramite Network Load Balancer. Il consumatore crea un Interface Endpoint nella propria VPC per accedere al servizio senza esporre il traffico a Internet.

### Security Groups vs NACLs

AWS offre due livelli di firewall:

**Security Groups** operano a livello di istanza (ENI). Sono **stateful**: il traffico di risposta e automaticamente consentito. Default: tutto bloccato in ingresso, tutto aperto in uscita. Possono referenziare altri Security Groups. Non supportano deny esplicito.

**Network ACLs (NACLs)** operano a livello di subnet. Sono **stateless**: il traffico di ritorno va consentito esplicitamente. Regole valutate in ordine numerico, supportano Allow e Deny.

| Caratteristica | Security Group | NACL |
|---|---|---|
| Livello | Istanza (ENI) | Subnet |
| Stato | Stateful | Stateless |
| Regole | Solo Allow | Allow e Deny |
| Valutazione | Tutte le regole | In ordine numerico |
| Applicazione | Associato esplicitamente | Automatico per la subnet |

Best practice per Security Groups:
- Usare nomi descrittivi con prefisso: `sg-web-alb-prod`, `sg-app-ecs-prod`, `sg-db-rds-prod`.
- Referenziare altri SG piuttosto che CIDR quando possibile (es. l'SG del database accetta traffico solo dall'SG dell'application layer).
- Evitare regole con `0.0.0.0/0` in ingresso tranne che per ALB/NLB pubblici.
- Limitare le porte aperte al minimo necessario.

### VPC Peering

Il **VPC Peering** crea una connessione privata tra due VPC, consentendo il routing tramite IP privati. Funziona cross-region e cross-account. Non e transitivo: VPC-A peered con VPC-B e VPC-B con VPC-C non implica connettivita tra A e C.

Limitazioni: non supporta CIDR sovrapposti, non supporta routing transitivo, non scala bene oltre un numero limitato di VPC (la complessita cresce con N*(N-1)/2 connessioni).

### Transit Gateway

**AWS Transit Gateway** e un hub centralizzato che connette VPC, reti on-premises e VPN. Supporta routing transitivo e scala per decine o centinaia di VPC, a differenza del peering.

Funzionalita avanzate:
- **Route Tables multiple**: per segmentare il traffico (es. isolare produzione da sviluppo).
- **Transit Gateway peering**: connette Transit Gateway in regioni diverse per architetture multi-region.
- **Multicast support**: per applicazioni che richiedono distribuzione multicast.
- **Network Manager**: visibilita centralizzata sulla topologia di rete globale.

Pattern tipico: hub-and-spoke con un Transit Gateway per regione, VPC di servizi condivisi (DNS, Active Directory, CI/CD) accessibili da tutte le VPC spoke tramite route table condivisa.

### VPN e Direct Connect

**AWS Site-to-Site VPN** stabilisce una connessione crittografata IPSec tra la rete on-premises e la VPC. Due tunnel per ridondanza, throughput massimo ~1,25 Gbps per tunnel.

**AWS Direct Connect** fornisce una connessione dedicata e privata tra data center e AWS. Banda da 1 a 100 Gbps, latenza consistente, costi di trasferimento ridotti. Si consiglia una VPN come backup.

### VPC Flow Logs

I **VPC Flow Logs** catturano metadati sul traffico IP (IP sorgente/destinazione, porte, protocollo, accept/reject) a livello di VPC, subnet o interfaccia di rete. Destinazione: CloudWatch Logs o S3. Utili per troubleshooting, monitoraggio e analisi di sicurezza.

---

## 4. Compute — EC2

### Panoramica EC2

**Amazon EC2** (Elastic Compute Cloud) fornisce capacita di calcolo ridimensionabile nel cloud sotto forma di macchine virtuali con pieno controllo amministrativo.

### Instance Types (Tipi di Istanza)

I tipi di istanza sono organizzati in famiglie ottimizzate per diversi casi d'uso:

- **General Purpose (T3, T3a, M5, M6i, M7g)**: bilanciamento tra compute, memoria e rete. Ideali per web server, ambienti di sviluppo e microservizi. Le istanze T3 supportano il **burst** di CPU tramite crediti accumulati durante i periodi di basso utilizzo.
- **Compute Optimized (C5, C6i, C7g)**: elevata potenza di calcolo per batch processing, modelli ML, gaming server e HPC.
- **Memory Optimized (R5, R6i, X1, X2gd)**: grandi quantita di RAM per database in-memory (Redis, Memcached) e analisi in tempo reale.
- **Storage Optimized (I3, I4i, D2, D3)**: alto throughput I/O e storage NVMe locale per data warehouse e database NoSQL.
- **Accelerated Computing (P4, P5, G5, Inf1, Inf2)**: GPU e acceleratori per deep learning, rendering grafico e video encoding.

La nomenclatura segue il pattern: `m5.xlarge` dove `m` e la famiglia, `5` la generazione e `xlarge` la dimensione. Le istanze con suffisso `g` (es. M7g, C7g) utilizzano processori AWS Graviton basati su architettura ARM, offrendo un rapporto prestazioni/costo fino al 40% migliore rispetto alle equivalenti x86. Le istanze con suffisso `d` includono storage locale NVMe.

### AWS Graviton — Processori ARM

I processori **AWS Graviton** sono progettati da AWS su architettura ARM (Arm Neoverse):

- **Graviton2** (M6g, C6g, R6g): 40% miglior rapporto prezzo/prestazioni rispetto alle istanze x86 di quinta generazione. 64 core, supporto sempre attivo per crittografia a 256 bit.
- **Graviton3** (M7g, C7g, R7g): 25% di prestazioni superiori a Graviton2, 2x prestazioni in virgola mobile, 2x prestazioni crypto, fino al 60% in meno di consumo energetico.
- **Graviton4** (M8g, C8g, R8g): ultima generazione con miglioramenti ulteriori in compute, memoria e networking.

Workload adatti a Graviton: web server, container, microservizi, runtime interpretati (Node.js, Python, Java), database open-source (MySQL, PostgreSQL, Redis). Workload da verificare: software con dipendenze native compilate per x86, software proprietario senza build ARM. La migrazione tipicamente richiede solo il cambio di AMI e la ricompilazione delle dipendenze native.

### Modelli di Pricing EC2

AWS offre diversi modelli di acquisto per le istanze EC2:

- **On-Demand**: pagamento al secondo (minimo 60 secondi) senza impegno. Massima flessibilita ma costo piu elevato.
- **Reserved Instances / Savings Plans**: sconti significativi con impegno a termine (vedi sezione Cost Management).
- **Spot Instances**: fino al 90% di sconto per capacita non utilizzata (vedi sotto).
- **Dedicated Hosts**: server fisici dedicati all'account, necessari per licenze software legate all'hardware (Oracle, Windows Server con licenze BYOL).
- **Dedicated Instances**: istanze che girano su hardware dedicato all'account ma senza il controllo completo del server fisico.

### AMI (Amazon Machine Image)

Una **AMI** e un template con sistema operativo, applicazioni e configurazione per lanciare istanze. AWS fornisce AMI ufficiali (Amazon Linux, Ubuntu, Windows Server, Red Hat). Si possono creare AMI personalizzate per standardizzare gli ambienti. Le AMI sono regionali ma copiabili tra regioni.

### Key Pairs

Le **Key Pairs** sono coppie di chiavi crittografiche per l'autenticazione SSH. La chiave pubblica viene iniettata nell'istanza; la privata resta all'utente. Supporto RSA e ED25519. La chiave privata non e recuperabile se persa.

### User Data

Lo **User Data** e uno script (bash/PowerShell) eseguito al primo avvio dell'istanza per automatizzare installazione pacchetti, configurazione servizi e setup iniziale.

```bash
#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>Server attivo in $(hostname -f)</h1>" > /var/www/html/index.html
```

### EBS Volumes e Snapshots

**Amazon EBS** (Elastic Block Store) fornisce volumi di storage persistente a blocchi per le istanze EC2. I principali tipi di volume sono:

- **gp3 / gp2** (General Purpose SSD): uso generico, buon bilanciamento prezzo/prestazioni. gp3 offre IOPS e throughput configurabili indipendentemente.
- **io2 / io2 Block Express** (Provisioned IOPS SSD): per workload con requisiti di I/O elevati e consistenti, come database transazionali. Fino a 256.000 IOPS.
- **st1** (Throughput Optimized HDD): per accesso sequenziale ad alto throughput, come big data e data warehouse.
- **sc1** (Cold HDD): storage a basso costo per dati ad accesso infrequente.

I volumi sono replicati nella stessa AZ. Gli **EBS Snapshots** sono backup incrementali archiviati in S3, utilizzabili per creare volumi in AZ/regioni diverse e per la creazione di AMI.

### Elastic IP

Un **Elastic IP** e un indirizzo IPv4 statico che rimane fisso (a differenza degli IP dinamici che cambiano al riavvio). AWS addebita un costo per Elastic IP non associati a istanze in esecuzione.

### Placement Groups

I **Placement Groups** controllano il posizionamento fisico delle istanze EC2:

- **Cluster**: le istanze sono posizionate nello stesso rack della stessa AZ. Fornisce la minima latenza di rete tra le istanze. Ideale per HPC e applicazioni che richiedono comunicazione inter-nodo ad alte prestazioni.
- **Spread**: le istanze sono distribuite su hardware fisico separato. Massimizza la resilienza. Limitato a 7 istanze per AZ.
- **Partition**: le istanze sono distribuite su partizioni logiche (rack separati). Ogni partizione e isolata dalle altre. Ideale per applicazioni distribuite su larga scala come Hadoop, Cassandra e Kafka.

### Auto Scaling Group (ASG)

Un **Auto Scaling Group** gestisce il numero di istanze EC2 in base alla domanda (minimo, desiderato, massimo). Tipi di scaling:

- **Target Tracking**: mantiene una metrica a un valore target (es. CPU media al 50%).
- **Step Scaling**: aggiunge/rimuove istanze in base a soglie CloudWatch definite.
- **Scheduled Scaling**: scala in base a un programma temporale (es. aumento durante le ore lavorative).
- **Predictive Scaling**: utilizza il machine learning per prevedere la domanda futura.

L'ASG si integra con **Elastic Load Balancing** e **health check** per distribuire il traffico e sostituire istanze non funzionanti.

Configurazione avanzata dell'ASG:
- **Warm Pool**: mantiene istanze pre-inizializzate in stato stopped o running per ridurre i tempi di scale-out. Utile quando l'avvio dell'applicazione richiede minuti (caricamento cache, connessione a database).
- **Instance Refresh**: esegue rolling replacement delle istanze per applicare nuove AMI o configurazioni, con percentuale minima di istanze sane configurabile.
- **Lifecycle Hooks**: intercettano il lancio/terminazione per eseguire azioni personalizzate (installazione agenti, drain delle connessioni, backup).
- **Mixed Instances Policy**: combina On-Demand e Spot su piu tipi di istanza per resilienza e ottimizzazione costi.

### Launch Template

Un **Launch Template** definisce la configurazione per il lancio di istanze: AMI, tipo, security groups, key pair, user data, volumi, IAM role. Supporta il versionamento per rollback. Preferito rispetto al legacy Launch Configuration.

Funzionalita avanzate dei Launch Template:
- **Versionamento**: ogni modifica crea una nuova versione. Si puo impostare la versione di default e la versione Latest. L'ASG puo essere configurato per usare la `$Latest` o la `$Default`.
- **Override di istanza**: nell'ASG, si possono specificare piu tipi di istanza (es. `m5.large`, `m5a.large`, `m6i.large`) per aumentare la probabilita di ottenere capacita Spot.
- **Ereditarieta**: un Launch Template puo ereditare da un template sorgente, sovrascrivendo solo i parametri necessari.

### Spot Instances

Le **Spot Instances** offrono sconti fino al 90% utilizzando capacita inutilizzata. AWS puo reclamarle con 2 minuti di preavviso. Ideali per workload fault-tolerant (batch, CI/CD, rendering). Combinabili con on-demand e reserved tramite **mixed instances policy** nell'ASG.

Strategie avanzate per Spot:
- **Diversificazione**: specificare almeno 6-10 pool di capacita (combinazioni tipo/AZ) per ridurre la probabilita di interruzione simultanea.
- **Capacity-Optimized allocation**: l'ASG sceglie i pool con maggiore disponibilita, riducendo le interruzioni.
- **Spot Fleet**: gestisce un fleet di Spot (e opzionalmente On-Demand) con target di capacita, supportando strategie di allocazione `lowestPrice`, `capacityOptimized` e `diversified`.
- **Interruption handling**: il metadata endpoint `http://169.254.169.254/latest/meta-data/spot/termination-time` avvisa 2 minuti prima della terminazione. Usare EventBridge per intercettare gli eventi di interruzione e triggerare azioni di drain.

### Elastic Load Balancing (ELB)

AWS offre tre tipi di load balancer:

- **Application Load Balancer (ALB)**: Layer 7 (HTTP/HTTPS). Routing basato su path, host, headers, metodi HTTP e query string. Supporta WebSocket, gRPC e autenticazione OIDC/Cognito integrata. Ideale per microservizi e applicazioni web.
- **Network Load Balancer (NLB)**: Layer 4 (TCP/UDP/TLS). Gestisce milioni di richieste al secondo con latenza ultra-bassa. IP statici per AZ. Necessario per servizi esposti tramite PrivateLink.
- **Gateway Load Balancer (GWLB)**: Layer 3. Distribuisce traffico verso appliance di terze parti (firewall, IDS/IPS). Opera in modo trasparente sulla rete.

---

## 5. Storage — S3, EBS, EFS, FSx

### Panoramica S3

**Amazon S3** (Simple Storage Service) e un object storage con durabilita 99,999999999% (11 nines), scalabilita illimitata e alta disponibilita.

### Buckets e Objects

Un **bucket** e il contenitore principale, con nome globalmente univoco e associato a una regione. I dati sono **objects** identificati da una **key** (es. `immagini/foto-2024/panorama.jpg`), fino a 5 TB ciascuno. Per upload superiori a 5 GB si usa il **multipart upload**. S3 e uno storage flat basato su chiavi: le "cartelle" sono semplicemente prefissi.

### Storage Classes (Classi di Storage)

S3 offre diverse classi di storage per ottimizzare i costi in base ai pattern di accesso:

- **S3 Standard**: per dati ad accesso frequente. Alta disponibilita (99,99%) e bassa latenza. E la classe predefinita.
- **S3 Standard-IA (Infrequent Access)**: per dati acceduti meno frequentemente ma che richiedono accesso rapido quando necessario. Costo di archiviazione inferiore ma con un costo per retrieval.
- **S3 One Zone-IA**: come Standard-IA ma i dati risiedono in una singola AZ. Meno costoso ma meno resiliente.
- **S3 Glacier Instant Retrieval**: per dati di archivio con accesso raro (circa una volta al trimestre) ma recupero in millisecondi. Costo di storage 68% inferiore a Standard-IA.
- **S3 Glacier Flexible Retrieval**: per archivi con tempi di recupero configurabili (Expedited: 1-5 min, Standard: 3-5 ore, Bulk: 5-12 ore). Ideale per backup e archivi di conformita.
- **S3 Glacier Deep Archive**: la classe piu economica, per dati di archivio a lungo termine con accesso una o due volte all'anno. Recupero in 12-48 ore. Pensata per la conservazione decennale di dati regolamentari.
- **S3 Intelligent-Tiering**: sposta automaticamente gli oggetti tra livelli di accesso in base ai pattern effettivi, senza costi di retrieval. Ideale quando i pattern di accesso sono imprevedibili. Monitora ogni oggetto individualmente e lo sposta tra i livelli Frequent Access, Infrequent Access, Archive Instant Access e opzionalmente Archive e Deep Archive.

### Lifecycle Policies

Le **Lifecycle Policies** automatizzano la transizione degli oggetti tra classi di storage e la loro eliminazione, riducendo significativamente i costi di archiviazione senza intervento manuale. Si possono definire regole basate sull'eta dell'oggetto, su prefissi e tag, applicabili sia alla versione corrente che alle versioni precedenti degli oggetti.

```json
{
  "Rules": [
    {
      "ID": "ArchiviaDopoUnAnno",
      "Status": "Enabled",
      "Filter": { "Prefix": "logs/" },
      "Transitions": [
        { "Days": 30, "StorageClass": "STANDARD_IA" },
        { "Days": 90, "StorageClass": "GLACIER" },
        { "Days": 365, "StorageClass": "DEEP_ARCHIVE" }
      ],
      "Expiration": { "Days": 2555 }
    }
  ]
}
```

### Versioning

Il **Versioning** mantiene tutte le versioni di un oggetto. L'eliminazione inserisce un **delete marker** senza cancellare fisicamente. Per eliminazione definitiva, specificare il version ID. Una volta abilitato, il versioning puo solo essere sospeso, non disabilitato.

### Encryption

S3 supporta la crittografia lato server per proteggere i dati at-rest:

- **SSE-S3**: AWS gestisce le chiavi (AES-256). Abilitata per default su tutti i nuovi bucket.
- **SSE-KMS**: utilizza AWS KMS per maggiore controllo (rotazione chiavi, audit CloudTrail, policy). Attenzione ai limiti di throughput API KMS.
- **SSE-C**: il cliente fornisce le proprie chiavi. AWS le utilizza per crittografare ma non le archivia.
- **Client-Side Encryption**: dati crittografati prima dell'upload. AWS non ha visibilita sulle chiavi.

### Bucket Policies

Le **Bucket Policies** sono policy JSON resource-based che controllano l'accesso al bucket. Utili per accesso cross-account, crittografia obbligatoria e restrizioni per IP o VPC endpoint.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnforceEncryption",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::mio-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

### S3 Block Public Access

**S3 Block Public Access** fornisce quattro impostazioni configurabili a livello di account o di singolo bucket per prevenire l'accesso pubblico accidentale:

- `BlockPublicAcls`: blocca nuove ACL pubbliche.
- `IgnorePublicAcls`: ignora ACL pubbliche esistenti.
- `BlockPublicPolicy`: blocca nuove bucket policy che concedono accesso pubblico.
- `RestrictPublicBuckets`: limita l'accesso a bucket con policy pubbliche ai soli principal autorizzati e ai servizi AWS.

Best practice: abilitare tutte e quattro le impostazioni a livello di account e disabilitarle selettivamente solo per i bucket che necessitano realmente di accesso pubblico (es. hosting statico).

### Presigned URLs

I **Presigned URLs** sono URL temporanei per accedere a oggetti privati. Durata configurabile (default 1 ora, massimo 7 giorni con credenziali IAM, 12 ore con STS). Utili per condivisione file e upload diretti senza esporre credenziali.

```python
import boto3

s3_client = boto3.client('s3')
url = s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'mio-bucket', 'Key': 'report/Q1-2026.pdf'},
    ExpiresIn=3600  # 1 ora
)
```

Per upload diretti dal browser, si usa `generate_presigned_post` che restituisce URL e campi del form. Questo pattern e fondamentale per evitare che il file transiti attraverso il backend applicativo: il client carica direttamente su S3.

### Cross-Region Replication (CRR)

La **Cross-Region Replication** replica oggetti tra bucket in regioni diverse (richiede versioning su entrambi). Utile per conformita, latenza e disaster recovery. La **Same-Region Replication (SRR)** replica nella stessa regione per aggregazione log e replica tra account.

Configurazione: si definiscono regole di replica con filtri per prefisso o tag, con opzione di cambiare la classe di storage nella destinazione e di modificare l'ownership degli oggetti. La replica e asincrona. Per monitorare il ritardo, usare **S3 Replication Time Control (RTC)** che garantisce il 99,99% degli oggetti replicati entro 15 minuti.

### S3 Event Notifications

Le **Event Notifications** attivano azioni in risposta a eventi (creazione, eliminazione oggetti). Destinazioni: **Lambda**, **SQS**, **SNS**, **EventBridge**. Esempi: generazione thumbnail, elaborazione CSV, notifiche su nuovi upload.

### S3 Transfer Acceleration

**S3 Transfer Acceleration** utilizza le edge locations di CloudFront per accelerare i trasferimenti di dati verso S3 su lunghe distanze. Il client carica sulla edge location piu vicina, e AWS instrada i dati al bucket di destinazione attraverso la propria rete backbone ottimizzata. Utile quando gli utenti caricano file da posizioni geograficamente distanti dalla regione del bucket. Si abilita a livello di bucket e l'endpoint cambia in `<bucket>.s3-accelerate.amazonaws.com`.

### S3 Select e S3 Object Lock

**S3 Select** consente di estrarre sottoinsiemi di dati da un oggetto utilizzando espressioni SQL semplici. Invece di scaricare l'intero oggetto, si recuperano solo le righe/colonne necessarie da file CSV, JSON o Parquet. Riduce il trasferimento dati e il tempo di elaborazione fino al 400%.

**S3 Object Lock** impedisce la cancellazione o la sovrascrittura di oggetti per un periodo definito, implementando il modello WORM (Write Once Read Many). Due modalita:

- **Governance mode**: gli utenti con permessi speciali (`s3:BypassGovernanceRetention`) possono sovrascrivere la protezione.
- **Compliance mode**: nessuno (incluso l'account root) puo cancellare o modificare l'oggetto fino alla scadenza del periodo di retention.

Indispensabile per conformita regolamentare (SEC 17a-4, FINRA, GDPR diritto all'oblio va bilanciato con retention obbligatoria).

### Amazon EBS — Approfondimento

Oltre ai tipi di volume gia descritti nella sezione EC2, aspetti avanzati di EBS:

**EBS Multi-Attach** (solo io2/io2 Block Express): consente di collegare un singolo volume a fino a 16 istanze EC2 nella stessa AZ contemporaneamente. Richiede un file system cluster-aware (GFS2, OCFS2) per coordinare gli accessi. Caso d'uso: applicazioni cluster ad alta disponibilita.

**EBS Encryption**: crittografia AES-256 tramite KMS, trasparente e senza impatto significativo sulle prestazioni. Si puo abilitare la crittografia predefinita a livello di regione per tutti i nuovi volumi. I volumi crittografati generano snapshot crittografati e viceversa.

**EBS Snapshots avanzati**: le snapshot sono incrementali (solo i blocchi modificati vengono salvati), ma ogni snapshot e autonoma per il ripristino. **EBS Snapshots Archive** sposta snapshot raramente accedute in un tier piu economico (costo ridotto del 75%) con tempo di ripristino di 24-72 ore. **Fast Snapshot Restore (FSR)** elimina il penalty di latenza al primo accesso di un volume creato da snapshot, utile per boot rapido in scenari di scaling.

### Amazon EFS (Elastic File System)

**Amazon EFS** e un file system NFS gestito, elastico e scalabile per workload Linux. Si monta su istanze EC2, container ECS/EKS e funzioni Lambda contemporaneamente.

Caratteristiche principali:
- **Scalabilita automatica**: cresce e si riduce automaticamente senza provisioning. Supporta petabyte di dati.
- **Multi-AZ**: i dati sono replicati su piu AZ per alta disponibilita e durabilita.
- **Performance modes**: **General Purpose** (bassa latenza, adatto alla maggior parte dei workload) e **Max I/O** (throughput aggregato elevato, per workload altamente paralleli con centinaia di client).
- **Throughput modes**: **Bursting** (throughput proporzionale alla dimensione del file system), **Provisioned** (throughput fisso indipendente dalla dimensione) e **Elastic** (scala automaticamente il throughput con il carico, consigliato per workload imprevedibili).
- **Storage classes**: **Standard** (accesso frequente) e **Infrequent Access (IA)** con costo fino all'88% inferiore. Le **lifecycle policies** spostano automaticamente i file tra le classi.
- **EFS One Zone**: variante a singola AZ con costo ridotto del 47%, per workload di sviluppo o dove la ridondanza multi-AZ non e necessaria.

Caso d'uso tipico: CMS con piu web server che condividono il filesystem, data science con notebook condivisi, home directory utente, build artifacts condivisi.

```bash
# Montaggio EFS su un'istanza EC2
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 \
  fs-0123456789abcdef0.efs.eu-central-1.amazonaws.com:/ /mnt/efs
```

### Amazon FSx

**Amazon FSx** fornisce file system gestiti ad alte prestazioni per workload specifici:

- **FSx for Windows File Server**: file system Windows nativo con supporto SMB, Active Directory, DFS namespace, shadow copies. Per workload Windows enterprise (home directory, CRM, ERP).
- **FSx for Lustre**: file system ad alte prestazioni per HPC, machine learning, elaborazione video. Si integra nativamente con S3 (lazy loading dei dati). Throughput fino a centinaia di GB/s e milioni di IOPS. Due tipi di deployment: **Scratch** (storage temporaneo, massime prestazioni, nessuna replica) e **Persistent** (replica intra-AZ, per storage a lungo termine).
- **FSx for NetApp ONTAP**: file system NetApp gestito con supporto NFS, SMB e iSCSI. Funzionalita avanzate: thin provisioning, deduplication, compression, SnapMirror. Ideale per migrazioni di workload NAS on-premises.
- **FSx for OpenZFS**: file system ZFS gestito con supporto NFS. Funzionalita ZFS: snapshot, cloni, compressione. Ideale per migrazioni da ZFS on-premises.

---

## 6. Database — RDS, Aurora e DynamoDB

### Amazon RDS (Relational Database Service)

**Amazon RDS** e un servizio gestito per database relazionali che automatizza provisioning, patching, backup e ripristino.

### Engine Supportati

RDS supporta sei motori di database: **MySQL**, **PostgreSQL**, **MariaDB**, **Oracle**, **Microsoft SQL Server** e **Amazon Aurora**. La scelta del motore dipende dai requisiti dell'applicazione, dalle competenze del team e dalla compatibilita con il software esistente. Per nuovi progetti senza vincoli di compatibilita, Aurora e generalmente la scelta consigliata per le sue prestazioni superiori e le funzionalita avanzate di resilienza.

### Multi-AZ Deployment

In **Multi-AZ**, RDS mantiene una replica sincrona in un'altra AZ con failover automatico (60-120 secondi). La standby non serve traffico di lettura: il suo scopo e l'alta disponibilita.

**Multi-AZ DB Cluster** (disponibile per MySQL e PostgreSQL) e un'evoluzione che mantiene due repliche in lettura in AZ diverse, oltre al primario. Le repliche servono traffico di lettura, riducendo il carico sul primario. Il failover e piu rapido (tipicamente sotto i 35 secondi) e le repliche sono sempre sincronizzate.

### Read Replicas

Le **Read Replicas** sono copie asincrone per traffico di lettura. Fino a 5 per RDS standard, 15 per Aurora. Supportano cross-region e possono essere promosse a database standalone. L'applicazione deve instradare letture alle replicas e scritture al primario.

Considerazioni sulle Read Replicas:
- Il **replication lag** (ritardo di replica) e tipicamente di millisecondi ma puo aumentare sotto carico pesante di scrittura. Monitare la metrica `ReplicaLag` in CloudWatch.
- Le read replicas cross-region sono utili per DR e per servire letture in regioni vicine agli utenti finali, ma generano costi di trasferimento dati inter-region.
- La promozione di una read replica a standalone e irreversibile e la nuova istanza non avra piu la relazione di replica con il source.

### Parameter Groups e Option Groups

I **Parameter Groups** personalizzano la configurazione del motore (equivalente a `my.cnf` o `postgresql.conf`). Esistono parameter groups di tipo statico (richiedono riavvio) e dinamico (applicati immediatamente). Gli **Option Groups** abilitano funzionalita aggiuntive specifiche del motore.

### Backup e Restore

RDS supporta due tipi di backup:

- **Backup automatici**: snapshot giornaliere e transaction log ogni 5 minuti, consentendo il **point-in-time recovery** fino al secondo. Retention configurabile da 1 a 35 giorni. I backup sono archiviati in S3 e replicati su piu AZ.
- **Snapshot manuali**: create dall'utente su richiesta, non scadono automaticamente. Utili prima di upgrade o migrazioni. Possono essere copiate tra regioni per disaster recovery o condivise con altri account AWS.

Per il restore, AWS crea sempre una nuova istanza RDS dalla snapshot o dal point-in-time specificato. Non e possibile ripristinare sovrascrivendo un'istanza esistente: l'applicazione deve essere aggiornata per puntare al nuovo endpoint.

### Amazon Aurora

**Amazon Aurora** e il motore proprietario AWS, compatibile con MySQL e PostgreSQL con prestazioni superiori (5x MySQL, 3x PostgreSQL). Storage distribuito su 3 AZ con 6 copie, auto-scaling fino a 128 TB, fino a 15 read replicas. **Aurora Serverless** scala automaticamente la capacita per workload intermittenti.

#### Aurora — Architettura Storage

Aurora separa compute e storage. Il layer di storage e un sistema distribuito proprietario:

- I dati sono segmentati in **Protection Groups** da 10 GB, ciascuno replicato 6 volte su 3 AZ.
- Le scritture richiedono un quorum di 4/6 repliche; le letture di 3/6.
- Tolleranza: Aurora sopravvive alla perdita di un'intera AZ senza interruzione delle scritture, e a 2 copie in una singola AZ senza interruzione delle letture.
- Lo storage cresce automaticamente in incrementi di 10 GB fino a 128 TB, senza downtime.
- Le **repliche Aurora** condividono lo stesso volume di storage del writer: non necessitano di replicazione dati separata. Il replication lag e tipicamente sotto i 10 ms.

#### Aurora Serverless v2

**Aurora Serverless v2** scala la capacita di compute in incrementi granulari (0,5 ACU), reagendo in secondi ai cambiamenti di carico. Vantaggi rispetto a v1:

- Scaling piu rapido e granulare (v1 scalava a step piu grossi con secondi di pausa).
- Supporta tutte le funzionalita di Aurora provisioned: read replicas, Multi-AZ, Global Database.
- Si definiscono **min ACU** e **max ACU** (1 ACU = circa 2 GB RAM).
- Ideale per workload con traffico imprevedibile: dev/test, applicazioni con picchi, nuovi progetti senza baseline di carico.

#### Aurora Global Database

**Aurora Global Database** fornisce replica cross-region con replication lag tipico sotto 1 secondo (basato su replicazione fisica dello storage). Il database primario in una regione e fino a 5 regioni secondarie con fino a 16 read replicas ciascuna. In caso di disastro regionale, una regione secondaria puo essere promossa a primaria in meno di 1 minuto (RPO tipico < 1 secondo, RTO < 1 minuto).

### DynamoDB — Concetti Base

**Amazon DynamoDB** e un database NoSQL completamente gestito con prestazioni in millisecondi a qualsiasi scala. Utilizza un modello chiave-valore e documenti. Offre alta disponibilita nativa con replica su tre AZ. **DynamoDB Global Tables** forniscono replica multi-regione attiva-attiva per applicazioni distribuite globalmente. I concetti principali includono:

- **Table**: la risorsa principale, simile a una tabella relazionale ma senza schema fisso.
- **Partition Key**: la chiave primaria che determina la distribuzione dei dati. Deve essere scelta per garantire una distribuzione uniforme.
- **Sort Key** (opzionale): combinata con la partition key, forma una chiave primaria composita che permette di organizzare e interrogare i dati in modo piu flessibile.
- **Capacity Modes**: **On-Demand** (paga per richiesta, scala automaticamente) o **Provisioned** (si definiscono le Read/Write Capacity Units, con possibilita di auto-scaling).
- **Global Secondary Index (GSI)**: permette di interrogare la tabella su attributi diversi dalla chiave primaria.
- **DynamoDB Streams**: cattura le modifiche ai dati in tempo reale, utile per trigger Lambda e replicazione.

### DynamoDB — Progettazione delle Chiavi

La scelta della partition key e la decisione piu critica nella progettazione di una tabella DynamoDB. Una partition key non uniforme porta a **hot partitions** (partizioni sovraccariche) che limitano il throughput effettivo.

Principi per una buona partition key:
- **Alta cardinalita**: molti valori distinti (es. `userId`, `orderId`, non `status` con pochi valori).
- **Distribuzione uniforme**: le richieste si distribuiscono equamente tra le partizioni.
- **Pattern di accesso noti**: la chiave deve supportare le query principali senza scansione completa.

Pattern di chiavi composte (partition key + sort key):

| Pattern | Partition Key | Sort Key | Caso d'uso |
|---------|---------------|----------|------------|
| Utente-Ordini | `USER#user123` | `ORDER#2026-05-22#ord456` | Ordini di un utente, ordinati per data |
| Prodotto-Recensioni | `PROD#prod789` | `REVIEW#2026-05-22#rev012` | Recensioni di un prodotto |
| Single-Table Design | `ACCOUNT#acc123` | `METADATA` / `ORDER#ord456` / `INVOICE#inv789` | Entita multiple in una tabella |

### DynamoDB — GSI vs LSI

**Global Secondary Index (GSI)**:
- Partition key e sort key diverse dalla tabella base.
- Creabile in qualsiasi momento.
- Ha la propria capacita di throughput (RCU/WCU) separata dalla tabella.
- Supporta **eventually consistent reads** (non strongly consistent).
- Proiezione configurabile: `ALL`, `KEYS_ONLY`, `INCLUDE` (attributi specifici).
- La dimensione della proiezione impatta costi e prestazioni: proiettare solo gli attributi necessari.
- Massimo 20 GSI per tabella.

**Local Secondary Index (LSI)**:
- Stessa partition key della tabella, sort key diversa.
- Deve essere creato al momento della creazione della tabella (non modificabile).
- Condivide la capacita di throughput con la tabella base.
- Supporta **strongly consistent reads**.
- Limita la dimensione totale degli item con la stessa partition key a 10 GB.
- Massimo 5 LSI per tabella.

Regola pratica: preferire GSI per flessibilita. Usare LSI solo quando serve strongly consistent reads su un ordinamento alternativo.

### DynamoDB — Capacity Modes

**On-Demand Mode**:
- Nessun provisioning: DynamoDB scala automaticamente.
- Pagamento per lettura/scrittura effettuata (circa 5x il costo unitario di provisioned).
- Ideale per: traffico imprevedibile, nuove applicazioni senza baseline, workload con picchi sporadici.
- Attenzione: le tabelle On-Demand hanno un limite iniziale di burst e potrebbero richiedere un warm-up graduale per workload che passano da zero a milioni di richieste istantaneamente.

**Provisioned Mode con Auto Scaling**:
- Si definiscono target RCU/WCU.
- Auto Scaling regola la capacita in base all'utilizzo effettivo.
- Meno costoso per workload prevedibili e stabili.
- Configurare **target utilization** (tipicamente 70%) e limiti min/max.

E possibile cambiare tra On-Demand e Provisioned una volta ogni 24 ore.

### DynamoDB Accelerator (DAX)

**DAX** e un layer di cache in-memory per DynamoDB con latenza in microsecondi (da millisecondi singoli a microsecondi). DAX e un cluster gestito compatibile con l'API DynamoDB: il cambio richiede solo la modifica dell'endpoint client.

Architettura: cluster di nodi con un nodo primario (read/write) e nodi replica (read-only). La cache opera su due livelli:

- **Item cache**: risultati di `GetItem` e `BatchGetItem`. TTL default 5 minuti.
- **Query cache**: risultati di `Query` e `Scan`. TTL default 5 minuti.

Le scritture sono **write-through**: DAX scrive sia nella cache che in DynamoDB. La consistenza e **eventually consistent** per default.

Quando non usare DAX:
- Workload write-heavy (DAX aggiunge overhead senza beneficio).
- Applicazioni che richiedono strongly consistent reads (DAX non li supporta).
- Applicazioni che non rileggono frequentemente gli stessi item.

---

## 7. Serverless — Lambda, API Gateway, Step Functions, EventBridge

### Panoramica Lambda

**AWS Lambda** consente di eseguire codice senza gestire server. Fatturazione al millisecondo, scaling automatico da zero a migliaia di esecuzioni concorrenti.

### Creazione di una Function

Una Lambda function richiede:

- **Runtime**: il linguaggio di programmazione (Python, Node.js, Java, Go, .NET, Ruby, custom runtime).
- **Handler**: la funzione entry point che Lambda invoca (es. `index.handler`).
- **IAM Execution Role**: il ruolo che definisce a quali servizi AWS la funzione puo accedere.
- **Memoria**: da 128 MB a 10.240 MB. La CPU viene allocata proporzionalmente alla memoria.
- **Timeout**: durata massima di esecuzione, da 1 secondo a 15 minuti.

```python
import json
import boto3

def handler(event, context):
    """Esempio di funzione Lambda che elabora un evento S3."""
    s3_client = boto3.client('s3')

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        response = s3_client.get_object(Bucket=bucket, Key=key)
        contenuto = response['Body'].read().decode('utf-8')

        # Elaborazione del contenuto...
        print(f"Elaborato file {key} dal bucket {bucket}")

    return {
        'statusCode': 200,
        'body': json.dumps({'messaggio': 'Elaborazione completata'})
    }
```

### Triggers (Sorgenti di Eventi)

Lambda puo essere invocata da numerosi servizi AWS in modalita sincrona o asincrona:

- **API Gateway**: per creare API REST e WebSocket serverless (sincrono).
- **S3 Event Notifications**: in risposta a eventi su oggetti (asincrono).
- **DynamoDB Streams**: in risposta a modifiche nelle tabelle (event source mapping).
- **SQS**: per elaborare messaggi da una coda (event source mapping con batching configurabile).
- **SNS**: in risposta a notifiche (asincrono).
- **EventBridge**: per eventi schedulati (cron) o personalizzati (asincrono).
- **CloudWatch Logs**: per elaborare log in tempo reale.
- **Kinesis Data Streams**: per elaborazione di dati in streaming.

La **concurrency** di Lambda e il numero di istanze in esecuzione simultanea. Il limite default e 1.000 per regione (incrementabile). Si puo configurare la **reserved concurrency** per garantire capacita a una funzione specifica e la **provisioned concurrency** per eliminare il cold start mantenendo istanze pre-riscaldate.

### Cold Start — Analisi e Mitigazione

Il **cold start** e il tempo aggiuntivo necessario quando Lambda deve inizializzare un nuovo ambiente di esecuzione (download del codice, avvio del runtime, esecuzione del codice di inizializzazione). Si verifica quando non ci sono ambienti caldi disponibili.

Fattori che influenzano il cold start:
- **Runtime**: Go e Rust hanno cold start piu brevi (~100 ms). Java e .NET piu lunghi (1-5 secondi senza ottimizzazioni). Python e Node.js nel mezzo (~200-500 ms).
- **Dimensione del pacchetto**: pacchetti piu grandi = cold start piu lunghi. Minimizzare le dipendenze.
- **VPC**: funzioni in VPC aggiungono tempo per l'allocazione dell'ENI (mitigato da Hyperplane, ora tipicamente < 1 secondo addizionale).
- **Memoria**: piu memoria = piu CPU = inizializzazione piu rapida.

Strategie di mitigazione:
- **Provisioned Concurrency**: mantiene N ambienti pre-riscaldati. Costo fisso aggiuntivo ma elimina il cold start. Configurabile con auto-scaling basato su schedule o utilizzo.
- **SnapStart** (Java): cattura uno snapshot dell'ambiente inizializzato e lo ripristina per le invocazioni successive. Riduce il cold start Java da secondi a ~200 ms.
- **Codice di inizializzazione ottimizzato**: inizializzare client SDK, connessioni database e cache al di fuori dell'handler (nel modulo principale), cosi vengono riutilizzati tra invocazioni nello stesso ambiente.
- **Mantenere i pacchetti leggeri**: usare tree-shaking, escludere dev dependencies, usare Layers per dipendenze condivise.

### Lambda Destinations

Le **Lambda Destinations** consentono di instradare il risultato di invocazioni asincrone verso altri servizi senza codice personalizzato:

- **onSuccess**: destinazione per invocazioni riuscite (SQS, SNS, Lambda, EventBridge).
- **onFailure**: destinazione per invocazioni fallite dopo tutti i retry (SQS, SNS, Lambda, EventBridge).

Le Destinations sono preferite rispetto alle **Dead Letter Queues (DLQ)** perche:
- Supportano sia successi che fallimenti (DLQ solo fallimenti).
- Includono il contesto completo dell'invocazione (request payload, response, error info).
- Supportano piu tipi di destinazione (DLQ solo SQS o SNS).

### Layers

I **Lambda Layers** sono archivi ZIP con librerie e file condivisi tra funzioni (max 5 per funzione). Riducono la dimensione dei deployment e separano logica applicativa dalle dipendenze.

Struttura di un Layer:

```
layer.zip
└── python/              # Per Python runtime
    └── lib/
        └── python3.12/
            └── site-packages/
                ├── requests/
                └── boto3/
```

Il Layer viene montato in `/opt` nell'ambiente Lambda. Ogni runtime ha la propria struttura convenzionale:

| Runtime | Percorso nel Layer |
|---------|-------------------|
| Python | `python/` o `python/lib/python3.x/site-packages/` |
| Node.js | `nodejs/node_modules/` |
| Java | `java/lib/` |

### Environment Variables

Le **Environment Variables** passano configurazioni alla funzione senza modificare il codice. Crittografabili con KMS. Accessibili tramite `os.environ['DB_HOST']` (Python) o equivalenti.

### Integrazione con API Gateway

**Amazon API Gateway** crea API REST, HTTP e WebSocket come punto di ingresso per Lambda. L'integrazione **Lambda Proxy** passa l'intera richiesta alla funzione, che restituisce statusCode, headers e body.

Tipi di API Gateway:

- **REST API**: funzionalita complete (caching, throttling, WAF, validation, API keys, usage plans, request/response transformation). Costo piu elevato.
- **HTTP API**: piu semplice e 70% meno costosa. Supporta JWT authorizer nativo, CORS semplificato. Mancano caching e request validation integrati. Preferita per la maggior parte dei casi d'uso nuovi.
- **WebSocket API**: per comunicazione bidirezionale in tempo reale (chat, dashboard live, gaming).

Funzionalita avanzate dell'API Gateway:
- **Throttling**: limiti di richieste per secondo configurabili per stage, metodo o API key. Default: 10.000 req/s con burst di 5.000.
- **Caching**: cache delle risposte con TTL configurabile (0,5-3600 secondi). Riduce le invocazioni Lambda e migliora la latenza.
- **Authorizers**: Lambda authorizer (logica personalizzata), Cognito authorizer, IAM authorization, JWT authorizer (HTTP API).
- **Custom domain names**: CNAME con certificato ACM per esporre l'API su un dominio personalizzato.

### AWS SAM (Serverless Application Model)

**AWS SAM** e un framework che semplifica il deployment serverless estendendo CloudFormation con sintassi abbreviata. Include CLI (`sam build`, `sam deploy`, `sam local invoke`) per sviluppo e testing locale.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  MiaFunzione:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.handler
      Runtime: python3.12
      MemorySize: 256
      Timeout: 30
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /elabora
            Method: post
```

### Step Functions

**AWS Step Functions** orchestra funzioni Lambda e servizi AWS in workflow (state machines) con esecuzioni sequenziali, parallele, branching e retry automatici. Due tipi: **Standard** (fino a un anno, exactly-once) e **Express** (fino a 5 minuti, at-least-once).

Tipi di stato in ASL (Amazon States Language):

| Stato | Funzione |
|-------|----------|
| `Task` | Esegue un'azione (invocazione Lambda, chiamata API AWS, attivita HTTP) |
| `Choice` | Branching condizionale basato sull'input |
| `Parallel` | Esecuzione parallela di branch indipendenti |
| `Map` | Iterazione su un array con esecuzione parallela o sequenziale |
| `Wait` | Pausa per un periodo o fino a un timestamp |
| `Succeed` / `Fail` | Terminazione con successo o errore |
| `Pass` | Trasformazione dati senza azione esterna |

Step Functions offre **SDK integrations** dirette con oltre 200 servizi AWS (senza bisogno di Lambda come intermediario): si possono invocare DynamoDB `PutItem`, SQS `SendMessage`, ECS `RunTask` direttamente da uno stato Task.

**Workflow Studio** fornisce un'interfaccia visuale drag-and-drop per progettare workflow Step Functions, generando automaticamente la definizione ASL corrispondente.

### Amazon EventBridge

**Amazon EventBridge** (ex CloudWatch Events) e un bus di eventi serverless. Le **rules** corrispondono a pattern di eventi e li instradano verso targets (Lambda, SQS, SNS, Step Functions). Fondamentale per architetture event-driven e automazione operativa. Supporta **scheduled rules** con espressioni cron o rate per eseguire attivita periodiche (es. `rate(5 minutes)` o `cron(0 8 * * ? *)`). L'**event replay** consente di rielaborare eventi passati per testing o recovery, archiviando gli eventi in un **archive** configurabile.

Funzionalita avanzate:

- **Schema Registry**: scopre e cataloga automaticamente gli schemi degli eventi. Genera bindings per codice in Java, Python e TypeScript per serializzazione/deserializzazione tipizzata.
- **EventBridge Pipes**: connettono una sorgente (SQS, DynamoDB Streams, Kinesis, Kafka) a un target con trasformazione opzionale e arricchimento tramite Lambda, Step Functions o API Gateway. Semplificano pipeline di eventi senza dover scrivere codice di integrazione.
- **Event bus personalizzati**: oltre al bus default, si creano bus dedicati per domini applicativi. Eventi da servizi partner SaaS (Zendesk, PagerDuty, Auth0) arrivano su bus partner dedicati.

Pattern EventBridge per disaccoppiamento:

```json
{
  "source": ["com.miaapp.ordini"],
  "detail-type": ["OrdineCreato"],
  "detail": {
    "stato": ["confermato"],
    "importo": [{"numeric": [">", 100]}]
  }
}
```

Questa regola cattura solo gli eventi di ordini confermati con importo superiore a 100, instradandoli verso il target configurato (es. Lambda per notifica, SQS per elaborazione asincrona).

---

## 8. Containers — ECS, EKS, ECR, App Runner

### Amazon ECS (Elastic Container Service)

**Amazon ECS** e il servizio di orchestrazione container proprietario di AWS.

### Task Definitions

Una **Task Definition** e un documento JSON che descrive i container dell'applicazione: immagine Docker, CPU, memoria, variabili d'ambiente, volumi, rete, log e ruolo IAM.

```json
{
  "family": "web-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "123456789012.dkr.ecr.eu-central-1.amazonaws.com/mia-app:latest",
      "portMappings": [
        { "containerPort": 8080, "protocol": "tcp" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/web-app",
          "awslogs-region": "eu-central-1",
          "awslogs-stream-prefix": "app"
        }
      }
    }
  ]
}
```

Ruoli IAM in ECS:
- **Task Execution Role** (`executionRoleArn`): usato dall'agente ECS per pull dell'immagine da ECR e invio log a CloudWatch. Gestito da AWS.
- **Task Role** (`taskRoleArn`): assunto dal container durante l'esecuzione per accedere a servizi AWS (S3, DynamoDB, SQS). Equivalente dell'instance profile per EC2.

### Services

Un **ECS Service** mantiene il numero desiderato di task con integrazione load balancer. Sostituisce automaticamente i task falliti. Supporta rolling updates, blue/green deployments e circuit breaker.

**ECS Service Connect** semplifica la comunicazione tra servizi ECS fornendo service discovery e load balancing integrati tramite un sidecar proxy gestito (basato su Envoy). Ogni servizio si registra con un nome DNS e il traffico viene bilanciato automaticamente.

**AWS Cloud Map** fornisce service discovery basato su DNS o API per risorse cloud. ECS si integra nativamente con Cloud Map per registrare automaticamente i task e deregistrarli alla terminazione.

### AWS Fargate

**AWS Fargate** e un motore serverless per container che elimina la gestione delle istanze EC2. Si definiscono solo CPU e memoria; Fargate scala automaticamente. L'alternativa e il **launch type EC2** con gestione diretta delle istanze.

Confronto Fargate vs EC2 launch type:

| Aspetto | Fargate | EC2 Launch Type |
|---------|---------|-----------------|
| Gestione infrastruttura | Zero (serverless) | Gestione cluster EC2 |
| Costo unitario | Piu alto per task | Piu basso con Reserved/Spot |
| Scaling | Automatico, rapido | Richiede ASG separato |
| GPU | Non supportato | Supportato |
| Daemon tasks | Non supportato | Supportato |
| Storage locale | 20 GB ephemeral (estendibile a 200 GB) | Volumi EBS dell'host |

**Fargate Spot**: fino al 70% di sconto su task Fargate tolleranti all'interruzione. I task ricevono un segnale SIGTERM 30 secondi prima della terminazione.

### Amazon ECR (Elastic Container Registry)

**Amazon ECR** e un registro container gestito, integrato con ECS/EKS. Supporta scansione vulnerabilita, crittografia, lifecycle policies e replicazione cross-region.

Funzionalita:
- **Image scanning**: scansione automatica alla push o on-demand. **Basic scanning** (Clair) per vulnerabilita CVE in pacchetti OS. **Enhanced scanning** (Amazon Inspector) per vulnerabilita in pacchetti OS e linguaggi di programmazione.
- **Lifecycle policies**: eliminazione automatica di immagini vecchie o non taggate per contenere i costi di storage.
- **Immutable tags**: impedisce la sovrascrittura di tag esistenti (es. `latest` rimane mutabile, ma `v1.2.3` diventa immutabile). Best practice per produzione.
- **Pull through cache**: proxy-cache per registri upstream (Docker Hub, GitHub, Quay). Riduce la dipendenza da registri esterni e i limiti di rate.

### Amazon EKS (Elastic Kubernetes Service)

**Amazon EKS** e il servizio gestito per Kubernetes. Gestisce il control plane su piu AZ. Worker nodes tramite **Managed Node Groups**, **Self-Managed Nodes** o **Fargate Profiles**. Preferito quando il team ha competenze Kubernetes o serve portabilita multi-cloud.

La scelta tra ECS e EKS dipende dal contesto: ECS e piu semplice da configurare e gestire, con integrazione nativa profonda nell'ecosistema AWS. EKS offre la portabilita dell'ecosistema Kubernetes (Helm charts, operatori, strumenti open-source) e facilita strategie multi-cloud o ibride. Entrambi supportano Fargate per un'esperienza completamente serverless.

EKS Add-ons gestiti:
- **CoreDNS**: DNS interno del cluster.
- **kube-proxy**: regole di networking per la comunicazione tra pod.
- **Amazon VPC CNI**: assegna IP della VPC ai pod, consentendo comunicazione diretta con risorse AWS.
- **EBS CSI driver**: provisioning dinamico di volumi EBS per pod.
- **EFS CSI driver**: mount di file system EFS in pod.

Costi EKS: il control plane costa 0,10 USD/ora (~73 USD/mese). I nodi worker sono istanze EC2 standard (o Fargate) con i rispettivi costi. Considerare Fargate per workload intermittenti per evitare costi di nodi EC2 idle.

### AWS App Runner

**AWS App Runner** e il servizio piu semplice per eseguire container e applicazioni web su AWS. Si fornisce un'immagine container (da ECR) o codice sorgente (da GitHub) e App Runner gestisce build, deploy, scaling, load balancing, TLS e osservabilita.

Caratteristiche:
- **Auto scaling**: scala da zero a centinaia di istanze basandosi su richieste concorrenti.
- **Custom domains**: supporta domini personalizzati con certificato TLS automatico.
- **VPC Connector**: consente ai container di accedere a risorse in VPC private (RDS, ElastiCache).
- **Observability**: log in CloudWatch, metriche pre-configurate, integrazione con X-Ray.

Posizionamento: App Runner e la scelta giusta per team che vogliono la semplicita di un PaaS (simile a Heroku o Google Cloud Run) senza la complessita di ECS o EKS. Non e adatto per workload con requisiti avanzati di networking, scheduling personalizzato o sidecar containers.

---

## 9. Monitoring — CloudWatch, X-Ray, CloudTrail

### Panoramica CloudWatch

**Amazon CloudWatch** e il servizio di monitoraggio e osservabilita che raccoglie metriche, log e eventi.

### Metrics (Metriche)

CloudWatch raccoglie metriche automaticamente (CPU EC2, latenza ALB, errori Lambda) con granularita di 5 minuti (base) o 1 minuto (detailed monitoring). Si pubblicano **custom metrics** tramite API `PutMetricData` o CloudWatch Agent. Organizzazione per **namespace** e **dimensions**.

Metriche importanti per servizio:

| Servizio | Metriche chiave |
|----------|----------------|
| EC2 | `CPUUtilization`, `NetworkIn/Out`, `StatusCheckFailed` |
| RDS | `DatabaseConnections`, `FreeableMemory`, `ReadLatency`, `ReplicaLag` |
| Lambda | `Invocations`, `Errors`, `Duration`, `Throttles`, `ConcurrentExecutions` |
| ALB | `RequestCount`, `TargetResponseTime`, `HTTPCode_Target_5XX_Count` |
| SQS | `ApproximateNumberOfMessagesVisible`, `ApproximateAgeOfOldestMessage` |
| DynamoDB | `ConsumedReadCapacityUnits`, `ThrottledRequests`, `SuccessfulRequestLatency` |

Nota: EC2 non pubblica metriche di memoria e disco per default. Il **CloudWatch Agent** deve essere installato per raccogliere metriche a livello OS come `mem_used_percent`, `disk_used_percent`, `swap_used`.

### Alarms

I **CloudWatch Alarms** attivano azioni al superamento di soglie: notifiche SNS, scaling policies ASG, arresto istanze. Tre stati: `OK`, `ALARM`, `INSUFFICIENT_DATA`. I **composite alarms** combinano piu allarmi con logica AND/OR.

Best practice per gli allarmi:
- Usare **percentili** (p99, p95) per latenza invece della media, per catturare problemi che colpiscono una minoranza di richieste.
- Configurare allarmi su **anomaly detection** per metriche con pattern stagionali (ML-based, apprende il pattern normale).
- Usare **metric math** per calcolare metriche derivate (es. error rate = errors / invocations * 100).
- Impostare periodi di valutazione adeguati: periodi troppo brevi causano falsi positivi, troppo lunghi ritardano la rilevazione.

### Logs

**CloudWatch Logs** aggrega e analizza i log organizzati in **Log Groups** e **Log Streams**. I **Metric Filters** estraggono metriche dai log; i **Subscription Filters** inviano log in tempo reale a Lambda, Elasticsearch o Kinesis.

Il **CloudWatch Agent** invia metriche di sistema (memoria, disco) e log personalizzati dalle istanze. **CloudWatch Logs Insights** permette query interattive per troubleshooting rapido.

### CloudWatch Logs Insights — Esempi di Query

```
# Top 10 errori nell'ultima ora
fields @timestamp, @message
| filter @message like /ERROR/
| stats count(*) as errori by @message
| sort errori desc
| limit 10
```

```
# Latenza p99 delle richieste per endpoint
fields @timestamp, @message
| filter @message like /latency/
| parse @message "endpoint=* latency=*ms" as endpoint, latency
| stats pct(latency, 99) as p99, avg(latency) as media by endpoint
| sort p99 desc
```

```
# Richieste Lambda con cold start
fields @timestamp, @duration, @billedDuration, @memorySize, @maxMemoryUsed
| filter @type = "REPORT"
| filter @initDuration > 0
| stats count(*) as coldStarts, avg(@initDuration) as avgColdStart by bin(1h)
```

### Dashboards

I **CloudWatch Dashboards** visualizzano metriche e log in grafici personalizzabili, combinando dati da regioni e account diversi per visibilita operativa in tempo reale.

### CloudWatch Container Insights

**Container Insights** raccoglie e aggrega metriche e log da workload containerizzati su ECS, EKS e Kubernetes self-managed. Fornisce metriche a livello di cluster, servizio, task e pod: CPU, memoria, rete, storage, conteggio task/pod. Include dashboard pre-configurati per visibilita immediata sulla salute dei container.

### CloudWatch Contributor Insights

**Contributor Insights** analizza dati di log strutturati per identificare i **top contributors** a un pattern (es. i 10 IP che generano piu errori, gli endpoint piu lenti, gli utenti con piu richieste). Crea report in tempo reale basati su regole personalizzabili.

### AWS X-Ray — Distributed Tracing

**AWS X-Ray** fornisce il tracciamento distribuito delle richieste attraverso i servizi dell'applicazione. Raccoglie dati da Lambda, API Gateway, ECS, EC2, SNS, SQS e altri servizi per costruire una **service map** visuale delle dipendenze.

Concetti principali:
- **Trace**: l'intero percorso di una richiesta attraverso i servizi.
- **Segment**: un'unita di lavoro eseguita da un singolo servizio.
- **Subsegment**: dettagli all'interno di un segmento (chiamate HTTP esterne, query database, chiamate AWS SDK).
- **Annotations**: coppie chiave-valore indicizzate per filtrare le trace.
- **Metadata**: dati aggiuntivi non indicizzati per debug.

X-Ray identifica colli di bottiglia, errori e anomalie visualizzando la latenza di ogni componente. Fondamentale per il troubleshooting di architetture a microservizi dove una richiesta attraversa molteplici servizi.

**Sampling**: X-Ray campiona una percentuale delle richieste per ridurre costi e overhead. Il default e 1 richiesta al secondo + 5% delle richieste successive. Le regole di campionamento sono configurabili per servizio.

### Amazon EventBridge

**Amazon EventBridge** (ex CloudWatch Events) e un bus di eventi serverless. Le **rules** corrispondono a pattern di eventi e li instradano verso targets (Lambda, SQS, SNS, Step Functions). Fondamentale per architetture event-driven e automazione operativa. Supporta **scheduled rules** con espressioni cron o rate per eseguire attivita periodiche (es. `rate(5 minutes)` o `cron(0 8 * * ? *)`). L'**event replay** consente di rielaborare eventi passati per testing o recovery, archiviando gli eventi in un **archive** configurabile.

### AWS CloudTrail — Approfondimento

**CloudTrail** registra tutte le chiamate API (chi, cosa, quando, da dove). I **management events** sono registrati per default; i **data events** (S3, Lambda) vanno abilitati esplicitamente. Consigliato: trail in tutte le regioni con log in un bucket S3 dedicato in un account separato (log archive).

Configurazione avanzata:
- **Organization trail**: un singolo trail che raccoglie eventi da tutti gli account dell'organizzazione.
- **CloudTrail Lake**: query SQL su eventi CloudTrail senza necessita di configurare Athena/S3. Retention fino a 7 anni. Ideale per investigazioni di sicurezza.
- **Insights events**: CloudTrail rileva automaticamente attivita anomale (volumi di API call insoliti, errori di accesso) e genera eventi Insights.
- **Integrita dei log**: abilitare la validazione dell'integrita per garantire che i log non siano stati manomessi (firma digitale SHA-256 ogni ora).

---

## 10. Security

### AWS KMS (Key Management Service)

**AWS KMS** gestisce chiavi di crittografia simmetriche (AES-256) e asimmetriche (RSA, ECC). Le chiavi non lasciano mai il servizio in chiaro. Integrazione nativa con S3, EBS, RDS, Lambda. Rotazione automatica annuale e audit tramite CloudTrail.

Tipi di chiavi KMS:
- **AWS managed keys**: create automaticamente da AWS per servizi specifici (es. `aws/s3`, `aws/rds`). Rotazione automatica ogni anno. Non modificabili dall'utente.
- **Customer managed keys (CMK)**: create e gestite dall'utente. Pieno controllo su policy, rotazione, abilitazione/disabilitazione. Rotazione automatica configurabile o manuale.
- **AWS owned keys**: usate internamente da AWS, non visibili all'utente. Usate per crittografia default di servizi come DynamoDB.

**Envelope Encryption**: KMS genera una data key, la usa per crittografare i dati localmente, poi crittografa la data key stessa con la CMK. La data key cifrata viene archiviata con i dati. Questo pattern evita di inviare grandi volumi di dati a KMS (limite 4 KB per chiamata diretta).

### AWS Secrets Manager

**Secrets Manager** gestisce segreti (password, API keys, token) con **rotazione automatica** senza downtime. Crittografia KMS e accesso controllato tramite IAM.

La rotazione automatica usa una Lambda function per aggiornare il segreto nel servizio di destinazione (es. password RDS). Flusso: `createSecret` (nuovo valore) -> `setSecret` (aggiornamento nel servizio) -> `testSecret` (verifica) -> `finishSecret` (attivazione). AWS fornisce template di rotazione per RDS, Redshift, DocumentDB. Per servizi personalizzati si scrive una Lambda custom.

Alternativa economica: **AWS Systems Manager Parameter Store** archivia parametri di configurazione e segreti (con tipo `SecureString` crittografato via KMS) gratuitamente per parametri standard. Non supporta rotazione automatica nativa. Usare Parameter Store per configurazione non-secret e Secrets Manager per credenziali che richiedono rotazione.

### AWS WAF (Web Application Firewall)

**AWS WAF** protegge da SQL injection, XSS e altri attacchi Layer 7. Si associa a CloudFront, ALB o API Gateway. Filtri per IP, headers, body, URI e geolocalizzazione. **Managed Rule Groups** disponibili da AWS e vendor terzi.

Managed Rule Groups principali:
- **AWSManagedRulesCommonRuleSet**: protezione base contro OWASP Top 10.
- **AWSManagedRulesSQLiRuleSet**: prevenzione SQL injection.
- **AWSManagedRulesKnownBadInputsRuleSet**: blocca pattern di input malevoli noti.
- **AWSManagedRulesBotControlRuleSet**: rilevamento e gestione bot.
- **AWSManagedRulesATPRuleSet**: protezione contro credential stuffing e account takeover.

Web ACL evaluation: le regole vengono valutate in ordine di priorita. Ogni regola puo avere azione `Allow`, `Block`, `Count` (solo monitoraggio) o `CAPTCHA`. E possibile combinare piu managed rule groups con regole personalizzate.

### AWS Shield

**AWS Shield** protegge contro attacchi DDoS:

- **Shield Standard**: incluso gratuitamente. Protegge contro attacchi DDoS comuni Layer 3/4.
- **Shield Advanced**: rilevamento in tempo reale, mitigazione automatica, accesso al DDoS Response Team (DRT) e protezione dei costi. Si integra con WAF, CloudFront e Route 53 per una difesa a piu livelli. Costa 3.000 USD/mese.

### Amazon GuardDuty

**GuardDuty** analizza VPC Flow Logs, CloudTrail events e DNS logs per identificare attivita malevole tramite machine learning e threat intelligence. Rileva compromissioni account, ricognizione, comunicazioni con server C2 e comportamenti anomali nell'accesso a dati S3. I findings sono classificati per severita (bassa, media, alta) e possono essere inviati a EventBridge per attivare risposte automatizzate (es. isolare un'istanza compromessa modificandone il security group tramite Lambda).

Funzionalita aggiuntive:
- **EKS Audit Log Monitoring**: rileva attivita sospette nei cluster EKS.
- **Malware Protection**: scansione di volumi EBS per malware quando GuardDuty rileva comportamenti sospetti.
- **S3 Protection**: monitora accessi anomali ai dati S3 (esfiltrazione, accesso da IP insoliti).
- **Runtime Monitoring**: agente leggero che monitora attivita a livello OS su istanze EC2 e container ECS/EKS.

### AWS Security Hub

**Security Hub** aggrega findings da GuardDuty, Inspector, Macie e altri servizi. Esegue controlli di conformita automatici contro CIS AWS Foundations, PCI DSS e AWS Foundational Security Best Practices.

Standard di conformita supportati:
- **AWS Foundational Security Best Practices (FSBP)**: controlli specifici AWS per configurazioni sicure.
- **CIS AWS Foundations Benchmark**: standard del Center for Internet Security per hardening AWS.
- **PCI DSS**: requisiti per ambienti che elaborano dati di carte di pagamento.
- **NIST SP 800-53**: framework di sicurezza governativo USA.

Security Hub assegna un **security score** per ogni standard, con drill-down sui singoli controlli falliti. I findings seguono il formato **AWS Security Finding Format (ASFF)** e possono essere esportati verso SIEM esterni.

### Amazon Inspector

**Amazon Inspector** esegue vulnerability assessment automatici e continui su istanze EC2, immagini ECR e funzioni Lambda. Rileva vulnerabilita software (CVE), esposizione di rete e configurazioni non sicure.

Differenza con GuardDuty: Inspector trova vulnerabilita (prevenzione), GuardDuty rileva minacce attive (rilevamento). Sono complementari.

### Amazon Macie

**Amazon Macie** utilizza machine learning per scoprire, classificare e proteggere dati sensibili in S3. Rileva automaticamente PII (numeri di carte di credito, codici fiscali, indirizzi email), credenziali, chiavi API e altri dati sensibili. Genera findings con la localizzazione precisa dei dati sensibili e suggerimenti di remediation.

### AWS Config

**AWS Config** registra e valuta continuamente la configurazione delle risorse AWS. Ogni modifica genera un **configuration item** con lo stato completo della risorsa. Le **Config Rules** verificano la conformita delle risorse (es. "tutti i bucket S3 devono avere la crittografia abilitata", "tutte le security group non devono avere porte aperte verso 0.0.0.0/0"). Le regole non conformi generano finding e possono triggerare azioni di **auto-remediation** tramite SSM Automation.

### Amazon Detective

**Amazon Detective** analizza e visualizza dati di sicurezza per investigare cause e impatto di security findings. Costruisce un grafo di comportamento aggregando dati da CloudTrail, VPC Flow Logs e GuardDuty findings. Consente di rispondere a domande come "cosa ha fatto questa identity nelle ultime 24 ore?" o "quali risorse ha acceduto questo IP?".

### AWS CloudTrail

**CloudTrail** registra tutte le chiamate API (chi, cosa, quando, da dove). I **management events** sono registrati per default; i **data events** (S3, Lambda) vanno abilitati esplicitamente. Consigliato: trail in tutte le regioni con log in un bucket S3 dedicato in un account separato (log archive).

---

## 11. Infrastructure as Code — CloudFormation, CDK, Terraform

### Panoramica CloudFormation

**AWS CloudFormation** e il servizio nativo IaC di AWS per modellare l'infrastruttura tramite template dichiarativi JSON o YAML.

### Struttura del Template

Un template CloudFormation e composto da diverse sezioni:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Infrastruttura web application a tre livelli'

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Default: dev
  InstanceType:
    Type: String
    Default: t3.micro

Mappings:
  RegionAMI:
    eu-central-1:
      AMI: ami-0abcdef1234567890
    eu-west-1:
      AMI: ami-0fedcba0987654321

Conditions:
  IsProd: !Equals [!Ref Environment, prod]

Resources:
  WebServerSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Accesso HTTP e HTTPS
      VpcId: !Ref VPCId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  WebServer:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !If [IsProd, m5.large, !Ref InstanceType]
      ImageId: !FindInMap [RegionAMI, !Ref 'AWS::Region', AMI]
      SecurityGroupIds:
        - !Ref WebServerSecurityGroup

Outputs:
  WebServerPublicIP:
    Description: IP pubblico del web server
    Value: !GetAtt WebServer.PublicIp
    Export:
      Name: !Sub '${Environment}-WebServerIP'
```

Le sezioni principali:

- **Parameters**: valori di input forniti al deployment (tipo istanza, ambiente, ecc.). Supportano tipi come String, Number, List e CommaDelimitedList con validazione tramite AllowedValues, AllowedPattern e ConstraintDescription.
- **Mappings**: tabelle di lookup statiche (es. AMI per regione) accessibili con la funzione intrinseca `!FindInMap`.
- **Conditions**: logica condizionale per creare risorse solo in determinati scenari, definita tramite funzioni come `!Equals`, `!If`, `!And`, `!Or`.
- **Resources** (obbligatoria): le risorse AWS da creare e configurare. Ogni risorsa ha un tipo (`Type: AWS::EC2::Instance`) e proprieta. Si possono definire dipendenze esplicite con `DependsOn` e proteggere risorse dalla cancellazione con `DeletionPolicy: Retain`.
- **Outputs**: valori di output come IP, ARN, endpoint, esportabili per cross-stack references tramite `Export`.

### Stacks

Uno **Stack** e un'istanza di un template. Le risorse vengono gestite come unita con rollback automatico in caso di errore. I **Nested Stacks** modularizzano l'infrastruttura referenziando altri template. Lo **stack drift detection** identifica le risorse che sono state modificate manualmente (fuori da CloudFormation), consentendo di individuare discrepanze tra lo stato attuale e quello definito nel template. Le **stack policies** proteggono risorse critiche da aggiornamenti accidentali.

### Change Sets

I **Change Sets** mostrano in anteprima le modifiche allo stack prima di applicarle, evitando modifiche distruttive involontarie. Flusso: creare il change set, esaminare le modifiche, eseguire solo dopo verifica.

### AWS CDK (Cloud Development Kit)

**AWS CDK** consente di definire l'infrastruttura AWS utilizzando linguaggi di programmazione familiari (TypeScript, Python, Java, C#, Go). CDK sintetizza il codice in template CloudFormation, combinando i vantaggi di IaC dichiarativo con la potenza dei linguaggi general-purpose.

Concetti fondamentali:
- **App**: il punto di ingresso dell'applicazione CDK.
- **Stack**: equivalente a uno stack CloudFormation. Contiene i costrutti.
- **Construct**: l'unita base, rappresenta una o piu risorse AWS.
  - **L1 (CloudFormation Resources)**: mapping diretto 1:1 con le risorse CloudFormation. Prefisso `Cfn` (es. `CfnBucket`).
  - **L2 (Curated Constructs)**: astrazione con default sensati e metodi helper. Es. `Bucket` con encryption abilitata per default.
  - **L3 (Patterns)**: combinazioni di risorse per pattern architetturali (es. `ApplicationLoadBalancedFargateService`).

Esempio CDK in TypeScript:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import { Construct } from 'constructs';

export class ElaborazioneImmaginiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const bucket = new s3.Bucket(this, 'ImmaginiUpload', {
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [{
        transitions: [{
          storageClass: s3.StorageClass.INFREQUENT_ACCESS,
          transitionAfter: cdk.Duration.days(30),
        }],
      }],
    });

    const elaboratore = new lambda.Function(this, 'ElaboraImmagine', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/elabora-immagine'),
      memorySize: 1024,
      timeout: cdk.Duration.seconds(60),
      environment: {
        BUCKET_NAME: bucket.bucketName,
      },
    });

    bucket.grantRead(elaboratore);
    bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(elaboratore),
      { prefix: 'upload/' },
    );
  }
}
```

Vantaggi CDK rispetto a CloudFormation YAML:
- Autocompletamento e type checking dell'IDE.
- Logica imperativa (loop, condizioni, funzioni) per generare infrastruttura dinamica.
- Riutilizzo di pattern tramite classi e composizione.
- Testing con framework standard del linguaggio (Jest, pytest).
- L2/L3 constructs con default sicuri (encryption, logging abilitati per default).

Comandi CDK principali: `cdk synth` (genera CloudFormation), `cdk diff` (confronta con lo stato deployed), `cdk deploy` (applica le modifiche), `cdk destroy` (elimina lo stack).

### Terraform per AWS

Per una trattazione completa di Terraform e IaC multi-cloud, si rimanda a `04-INFRASTRUCTURE-AS-CODE/`. CloudFormation e ideale per ambienti esclusivamente AWS; Terraform offre maggiore flessibilita in contesti multi-cloud o ibridi.

Esempio Terraform per AWS:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "mia-azienda-terraform-state"
    key            = "prod/vpc/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = "eu-central-1"
  default_tags {
    tags = {
      Environment = "prod"
      ManagedBy   = "terraform"
      Project     = "piattaforma-web"
    }
  }
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "vpc-prod-main"
  }
}

resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "subnet-private-${data.aws_availability_zones.available.names[count.index]}"
    Tier = "private"
  }
}
```

Confronto CloudFormation vs CDK vs Terraform:

| Aspetto | CloudFormation | CDK | Terraform |
|---------|---------------|-----|-----------|
| Linguaggio | YAML/JSON | TypeScript, Python, Java, Go, C# | HCL |
| State management | Gestito da AWS | Gestito da AWS (via CFN) | File di stato separato (S3 + DynamoDB) |
| Multi-cloud | Solo AWS | Solo AWS | Multi-cloud, multi-provider |
| Rollback | Automatico | Automatico (via CFN) | Manuale (plan + apply) |
| Preview modifiche | Change Sets | `cdk diff` | `terraform plan` |
| Modularita | Nested Stacks, Modules | Constructs, npm/PyPI packages | Modules, Terraform Registry |
| Curva apprendimento | Bassa (YAML) | Media (programmazione) | Media (HCL) |

---

## 12. Cost Management

La gestione dei costi e critica nell'adozione del cloud. AWS offre strumenti dedicati per monitorare e ottimizzare la spesa.

### AWS Cost Explorer

**Cost Explorer** visualizza e analizza costi nel tempo con filtri per servizio, regione, account e tag. Identifica trend e anomalie, offre previsioni e raccomandazioni per Reserved Instances e Savings Plans. La funzionalita **AWS Cost Anomaly Detection** utilizza machine learning per identificare automaticamente spese anomale e inviare notifiche in tempo reale, consentendo di intervenire rapidamente su costi imprevisti causati da errori di configurazione o attacchi.

### AWS Budgets

**AWS Budgets** definisce budget personalizzati con **alert** via email/SNS al superamento di soglie (es. 80%, 100%). Le **budget actions** eseguono azioni correttive automatiche (SCP restrittive, arresto istanze).

Tipi di budget:
- **Cost budget**: avvisi basati sulla spesa effettiva o prevista.
- **Usage budget**: avvisi basati sull'utilizzo (ore EC2, GB S3, richieste Lambda).
- **Reservation budget**: monitoraggio dell'utilizzo di Reserved Instances.
- **Savings Plans budget**: monitoraggio dell'utilizzo dei Savings Plans.

### Savings Plans

I **Savings Plans** offrono sconti significativi (fino al 72%) in cambio di un impegno di spesa oraria per un periodo di 1 o 3 anni. Esistono due tipi:

- **Compute Savings Plans**: flessibilita massima. Lo sconto si applica indipendentemente dalla famiglia di istanza, dalla regione, dal sistema operativo o dalla tenancy. Coprono EC2, Lambda e Fargate.
- **EC2 Instance Savings Plans**: sconto maggiore ma vincolato a una specifica famiglia di istanza e regione.

### Reserved Instances

Le **Reserved Instances (RI)** offrono sconti fino al 75% con impegno di 1 o 3 anni. Pagamento: tutto anticipato (sconto massimo), parziale o niente. Applicabili a EC2, RDS, ElastiCache, Redshift. Per EC2 si preferiscono i Savings Plans; le RI restano utili per RDS.

### AWS Compute Optimizer e Right-Sizing

**AWS Compute Optimizer** analizza le metriche di utilizzo delle risorse e raccomanda il tipo/dimensione ottimale. Supporta EC2, Auto Scaling Groups, EBS, Lambda e ECS su Fargate.

Processo di right-sizing:
1. Abilitare Compute Optimizer e raccogliere dati per almeno 14 giorni (idealmente 30).
2. Analizzare le raccomandazioni: `Over-provisioned` (ridimensionare), `Under-provisioned` (aumentare), `Optimized` (nessuna azione).
3. Verificare i pattern di utilizzo: un'istanza con picchi periodici potrebbe necessitare della dimensione attuale nonostante la media bassa.
4. Implementare gradualmente, partendo dagli ambienti non-produttivi.
5. Monitorare dopo il ridimensionamento per confermare che le prestazioni rimangano adeguate.

### Spot Best Practices per il Risparmio

- Usare **Spot Fleet** o **ASG mixed instances** con almeno 6 pool di capacita diversificati.
- Implementare **graceful shutdown**: intercettare il segnale di terminazione (2 minuti di preavviso) per completare il lavoro in corso e salvare lo stato.
- Usare **checkpointing** per workload di batch processing: salvare lo stato periodicamente per riprendere dal checkpoint in caso di interruzione.
- Non usare Spot per servizi stateful senza strategia di persistenza esterna.
- Combinare Spot con On-Demand nell'ASG: la base minima On-Demand garantisce disponibilita, Spot gestisce i picchi.

### Strategia di Tagging

Una strategia di tagging e fondamentale per allocazione costi, automazione e governance. Tag consigliati:

| Tag Key | Esempio Valore | Scopo |
|---|---|---|
| `Environment` | prod, staging, dev | Separazione ambienti |
| `Project` | ecommerce-platform | Allocazione costi per progetto |
| `Owner` | team-backend | Responsabilita |
| `CostCenter` | CC-4521 | Centro di costo aziendale |
| `ManagedBy` | terraform, cloudformation | Strumento IaC |
| `Application` | payment-service | Identificazione applicazione |

Implementare **tag policy** in Organizations e **AWS Config Rules** per verificare il tagging. Le risorse non taggate diventano costi non attribuibili.

Enforcement del tagging:
- **Tag Policies** in AWS Organizations: definiscono i tag obbligatori e i valori consentiti. Impediscono la creazione di risorse senza tag richiesti.
- **AWS Config Rule `required-tags`**: rileva risorse esistenti senza tag obbligatori.
- **SCP condizionale**: blocca operazioni `RunInstances`, `CreateBucket` ecc. se mancano tag specifici.
- **Cost Allocation Tags**: attivare i tag come "cost allocation tags" in Billing per visualizzarli in Cost Explorer e nei report di fatturazione.

### Ulteriori Strumenti di Ottimizzazione

- **S3 Storage Lens**: dashboard di analytics per l'utilizzo e l'attivita degli oggetti S3 attraverso account e regioni. Identifica bucket con costi elevati, oggetti non crittografati, e suggerisce azioni di ottimizzazione.
- **Trusted Advisor**: checklist automatizzata per ottimizzazione costi, sicurezza, prestazioni, tolleranza ai guasti e limiti di servizio. Il livello gratuito include controlli base; il piano Business/Enterprise include tutti i controlli.
- **Cost and Usage Report (CUR)**: il report piu granulare sui costi AWS, con dati a livello di riga di fatturazione. Consegnato in S3, analizzabile con Athena o QuickSight.

---

## 13. Best Practices

Dieci best practices fondamentali per operare efficacemente su AWS.

### 1. Adottare un'Architettura Multi-Account

Utilizzare AWS Organizations per separare i workload in account dedicati: un account per la produzione, uno per lo staging, uno per il development, uno per i log centralizzati, uno per la sicurezza e uno per i servizi condivisi. Questa separazione fornisce isolamento dei guasti, confini di sicurezza netti, limiti di servizio indipendenti e allocazione dei costi precisa. Utilizzare le SCP per applicare guardrails a livello organizzativo e AWS Control Tower per automatizzare il setup dell'ambiente multi-account.

### 2. Progettare per l'Alta Disponibilita

Distribuire ogni componente su almeno due Availability Zones. Utilizzare Elastic Load Balancing per distribuire il traffico, Auto Scaling Groups per gestire la capacita e RDS Multi-AZ per i database. Implementare health check a tutti i livelli e automatizzare il failover. Testare regolarmente la resilienza con esperimenti di chaos engineering.

### 3. Applicare il Principio del Least Privilege

Concedere solo i permessi strettamente necessari per ogni utente, ruolo e servizio. Iniziare con zero permessi e aggiungere progressivamente solo quelli richiesti. Utilizzare IAM Access Analyzer per identificare permessi eccessivi. Revisionare periodicamente le policy IAM e rimuovere i permessi non utilizzati. Utilizzare le condition nelle policy per restringere ulteriormente l'accesso (per IP, tag, orario, MFA).

### 4. Crittografare i Dati Ovunque

Crittografare i dati at-rest utilizzando KMS (S3 SSE, EBS encryption, RDS encryption) e i dati in-transit utilizzando TLS/SSL. Abilitare la crittografia per impostazione predefinita su tutti i servizi che la supportano. Gestire le chiavi in modo centralizzato tramite KMS e implementare la rotazione automatica. Non archiviare mai segreti nel codice sorgente: utilizzare Secrets Manager o Parameter Store.

### 5. Automatizzare Tutto con Infrastructure as Code

Gestire l'intera infrastruttura tramite CloudFormation, Terraform o CDK. Non creare mai risorse manualmente tramite la Console per ambienti diversi dal prototipazione rapida. Versionare i template IaC nel repository del codice sorgente. Implementare pipeline di CI/CD per validare, testare e applicare le modifiche infrastrutturali in modo controllato e ripetibile.

### 6. Implementare Monitoraggio e Osservabilita Completi

Configurare CloudWatch per raccogliere metriche, log e trace da tutti i componenti. Creare allarmi per metriche critiche con notifiche tempestive al team. Implementare logging strutturato (JSON) con correlazione tramite request ID. Utilizzare CloudWatch Dashboards per la visibilita operativa in tempo reale. Considerare soluzioni avanzate come AWS X-Ray per il distributed tracing e CloudWatch ServiceLens per la mappa dei servizi.

### 7. Ottimizzare i Costi in Modo Continuo

Rivedere mensilmente i costi con Cost Explorer. Implementare Savings Plans o Reserved Instances per i workload stabili. Utilizzare Spot Instances per i workload fault-tolerant. Implementare policy di spegnimento automatico per ambienti non produttivi fuori orario lavorativo. Eliminare le risorse non utilizzate (Elastic IP non associati, EBS volumes non collegati, snapshot obsoleti). Utilizzare S3 Lifecycle Policies e Intelligent-Tiering per lo storage.

### 8. Implementare una Strategia di Backup e Disaster Recovery

Definire RPO (Recovery Point Objective) e RTO (Recovery Time Objective) per ogni applicazione. Configurare backup automatici con retention adeguata. Testare periodicamente il ripristino dai backup. Per applicazioni critiche, implementare strategie di DR cross-region (pilot light, warm standby o multi-site active-active). Utilizzare AWS Backup per centralizzare la gestione dei backup su tutti i servizi.

### 9. Proteggere il Perimetro e Rilevare le Minacce

Abilitare GuardDuty in tutti gli account e tutte le regioni. Configurare AWS Config per monitorare le modifiche alla configurazione delle risorse e verificare la conformita. Abilitare CloudTrail in tutte le regioni con log centralizzati in un account dedicato. Utilizzare Security Hub per aggregare i findings di sicurezza. Implementare WAF per le applicazioni web-facing. Eseguire vulnerability assessment regolari con Amazon Inspector.

### 10. Scegliere il Servizio Giusto per il Caso d'Uso

Non forzare ogni workload su EC2. Valutare servizi gestiti e serverless che riducono il carico operativo: Lambda per workload event-driven, Fargate per container senza gestione dei server, Aurora Serverless per database con traffico variabile, SQS/SNS per il disaccoppiamento dei componenti, EventBridge per architetture event-driven. I servizi gestiti offrono patching automatico, scaling integrato e alta disponibilita nativa, consentendo al team di concentrarsi sulla logica di business anziche sull'infrastruttura.

---

## 14. Well-Architected Framework — I 6 Pilastri

Il **AWS Well-Architected Framework** fornisce best practice architetturali organizzate in sei pilastri. Ogni pilastro contiene domande, principi di progettazione e servizi AWS rilevanti. AWS offre il **Well-Architected Tool** nella console per eseguire review formali dei propri workload rispetto al framework.

### Pilastro 1 — Operational Excellence (Eccellenza Operativa)

Obiettivo: eseguire e monitorare i sistemi per fornire valore di business, migliorando continuamente processi e procedure.

Principi:
- Eseguire operazioni come codice (IaC, pipeline CI/CD).
- Apportare modifiche piccole e frequenti, reversibili.
- Anticipare i guasti e testare le procedure di ripristino.
- Apprendere da tutti gli eventi operativi.
- Usare runbook e playbook documentati per le operazioni.

Servizi chiave: **CloudFormation/CDK** (IaC), **CodePipeline/CodeDeploy** (CI/CD), **CloudWatch** (monitoraggio), **Systems Manager** (automazione operativa, patching, runbook), **Config** (configurazione), **X-Ray** (tracing).

### Pilastro 2 — Security (Sicurezza)

Obiettivo: proteggere informazioni, sistemi e asset sfruttando le tecnologie cloud per migliorare la postura di sicurezza.

Principi:
- Implementare solide basi identitarie (IAM, federazione, least privilege).
- Abilitare la tracciabilita (CloudTrail, logging, auditing).
- Applicare sicurezza a tutti i livelli (rete, applicazione, dati).
- Automatizzare le best practice di sicurezza.
- Proteggere i dati in transito e a riposo.
- Prepararsi per gli incidenti di sicurezza.

Servizi chiave: **IAM**, **Organizations/SCPs**, **KMS**, **Secrets Manager**, **WAF**, **Shield**, **GuardDuty**, **Security Hub**, **Inspector**, **Macie**, **CloudTrail**, **Config**, **Detective**.

### Pilastro 3 — Reliability (Affidabilita)

Obiettivo: garantire che un workload esegua la funzione prevista correttamente e in modo consistente, con capacita di ripristino rapido da guasti.

Principi:
- Testare automaticamente le procedure di ripristino.
- Recuperare automaticamente dai guasti.
- Scalare orizzontalmente per aumentare la disponibilita aggregata.
- Evitare ipotesi sulla capacita (auto-scaling).
- Gestire i cambiamenti tramite automazione.

Servizi chiave: **CloudWatch** (monitoraggio), **Auto Scaling** (elasticita), **ELB** (distribuzione traffico), **RDS Multi-AZ** (database HA), **S3** (storage durabile), **Route 53** (DNS failover), **Backup** (backup centralizzato), **Resilience Hub** (assessment resilienza).

Strategie di Disaster Recovery:

| Strategia | RTO | RPO | Costo | Descrizione |
|-----------|-----|-----|-------|-------------|
| Backup & Restore | Ore | Ore | Basso | Ripristino da backup in un'altra regione |
| Pilot Light | Minuti-ore | Minuti | Medio-basso | Componenti core (DB) replicati, compute spento |
| Warm Standby | Minuti | Secondi | Medio | Ambiente ridotto sempre attivo, scale-up al failover |
| Multi-Site Active-Active | Secondi | Zero/Secondi | Alto | Traffico distribuito su piu regioni attive |

### Pilastro 4 — Performance Efficiency (Efficienza delle Prestazioni)

Obiettivo: utilizzare le risorse di calcolo in modo efficiente per soddisfare i requisiti di sistema e mantenere l'efficienza al variare della domanda e dell'evoluzione delle tecnologie.

Principi:
- Democratizzare le tecnologie avanzate (usare servizi gestiti).
- Diventare globali in minuti (multi-region).
- Usare architetture serverless.
- Sperimentare piu frequentemente.
- Considerare la sympathia meccanica (capire come le tecnologie si comportano).

Servizi chiave: **Auto Scaling** (elasticita compute), **Lambda** (serverless), **ElastiCache/DAX** (caching), **CloudFront** (CDN), **Global Accelerator** (networking), **EBS io2** (storage ad alte prestazioni), **Graviton** (compute efficiente).

### Pilastro 5 — Cost Optimization (Ottimizzazione dei Costi)

Obiettivo: evitare spese non necessarie, comprendendo e controllando dove viene speso il denaro.

Principi:
- Implementare la gestione finanziaria del cloud (Cloud Financial Management).
- Adottare un modello di consumo (pagare solo per cio che si usa).
- Misurare l'efficienza complessiva.
- Smettere di investire in operazioni infrastrutturali non differenzianti.
- Analizzare e attribuire la spesa.

Servizi chiave: **Cost Explorer**, **Budgets**, **Savings Plans/RI**, **Spot Instances**, **Compute Optimizer**, **S3 Intelligent-Tiering/Lifecycle**, **Trusted Advisor**, **Cost and Usage Report**.

### Pilastro 6 — Sustainability (Sostenibilita)

Obiettivo: minimizzare l'impatto ambientale dei workload cloud.

Principi:
- Comprendere il proprio impatto.
- Stabilire obiettivi di sostenibilita.
- Massimizzare l'utilizzo delle risorse.
- Anticipare e adottare offerte hardware e software piu efficienti.
- Usare servizi gestiti.
- Ridurre l'impatto downstream dei workload cloud.

Azioni concrete:
- Usare **Graviton** (efficienza energetica superiore ai chip x86).
- Dimensionare correttamente le risorse (right-sizing).
- Usare regioni con energia rinnovabile.
- Sfruttare Spot Instances (utilizzano capacita altrimenti inattiva).
- Implementare scaling aggressivo (ridurre a zero quando non necessario).
- Ottimizzare lo storage con lifecycle policies.
- Usare il **Customer Carbon Footprint Tool** per monitorare le emissioni.

---

## 15. Pattern Architetturali

### Pattern 1 — Web Application a Tre Livelli

Architettura classica con separazione tra presentazione, logica applicativa e dati.

```
                Internet
                   │
            ┌──────┴──────┐
            │  CloudFront  │  CDN + WAF
            └──────┬──────┘
                   │
            ┌──────┴──────┐
            │     ALB      │  Subnet pubblica, multi-AZ
            └──────┬──────┘
                   │
         ┌─────────┴─────────┐
    ┌────┴────┐         ┌────┴────┐
    │  EC2/ECS │         │  EC2/ECS │  Subnet private, ASG
    │  (AZ-a)  │         │  (AZ-b)  │
    └────┬────┘         └────┬────┘
         └─────────┬─────────┘
                   │
            ┌──────┴──────┐
            │   Aurora     │  Multi-AZ, subnet private (DB)
            │   (Writer)   │
            └──────┬──────┘
                   │
            ┌──────┴──────┐
            │   Aurora     │  Read Replica
            │   (Reader)   │
            └─────────────┘
```

Componenti:
- **CloudFront**: caching, WAF, certificato TLS, compressione.
- **ALB**: routing HTTP/HTTPS, health check, sticky sessions se necessario.
- **Application tier**: EC2 con ASG o ECS Fargate nelle subnet private. Auto-scaling basato su CPU o richieste concorrenti.
- **Data tier**: Aurora Multi-AZ con read replicas nelle subnet isolate (nessun accesso Internet). Security group che accetta connessioni solo dall'application tier.
- **ElastiCache**: session store e/o cache dei risultati delle query per ridurre il carico sul database.

### Pattern 2 — Microservizi su Container

Architettura basata su servizi indipendenti, ciascuno con il proprio ciclo di vita e deployment.

```
                   API Gateway / ALB
                        │
          ┌─────────────┼─────────────┐
          │             │             │
    ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
    │  Servizio │ │  Servizio │ │  Servizio │
    │   Ordini  │ │  Catalogo │ │  Pagamenti│
    │  (ECS)    │ │  (ECS)    │ │  (ECS)    │
    └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
          │             │             │
     DynamoDB      Aurora RR      DynamoDB
                        │
                   ┌────┴────┐
                   │   SQS   │  Comunicazione asincrona
                   └────┬────┘
                        │
                   EventBridge  Orchestrazione eventi
```

Pattern di comunicazione:
- **Sincrona**: Service-to-service via ALB interno o ECS Service Connect. Usare circuit breaker per resilienza.
- **Asincrona**: SQS per task queue, SNS per fan-out, EventBridge per eventi di dominio. Preferita per disaccoppiamento.
- **Coreografia vs Orchestrazione**: EventBridge per coreografia (servizi reagiscono a eventi), Step Functions per orchestrazione (un coordinatore gestisce il flusso).

Ogni servizio:
- Ha il proprio database (database per-service pattern).
- E deployato indipendentemente tramite pipeline CI/CD separata.
- Ha il proprio set di metriche, allarmi e dashboard.
- Comunica con gli altri servizi tramite API ben definite o eventi.

### Pattern 3 — Data Lake su AWS

Architettura per raccolta, archiviazione, elaborazione e analisi di grandi volumi di dati eterogenei.

```
    Sorgenti Dati
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Database │  │   API    │  │  IoT /   │
    │   (RDS)   │  │ esterne  │  │ Streaming │
    └─────┬────┘  └─────┬────┘  └─────┬────┘
          │             │             │
    ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
    │   DMS     │ │  Lambda   │ │  Kinesis   │
    │ (migraz.) │ │ (ingest)  │ │  (stream)  │
    └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
          └─────────────┼─────────────┘
                        │
                 ┌──────┴──────┐
                 │   S3 Raw    │  Landing zone (dati grezzi)
                 └──────┬──────┘
                        │
                 ┌──────┴──────┐
                 │  AWS Glue   │  ETL, Crawlers, Data Catalog
                 └──────┬──────┘
                        │
              ┌─────────┼─────────┐
        ┌─────┴─────┐      ┌─────┴─────┐
        │ S3 Curated │      │ S3 Enriched│
        │ (Parquet)  │      │ (analytics)│
        └─────┬─────┘      └─────┬─────┘
              │                   │
        ┌─────┴─────┐      ┌─────┴─────┐
        │  Athena   │      │ QuickSight │
        │  (query)  │      │  (BI/viz)  │
        └───────────┘      └───────────┘
```

Componenti:
- **S3**: storage centrale del data lake. Zone organizzate per livello di maturita dei dati (raw, curated, enriched).
- **AWS Glue**: servizio ETL serverless. I **Crawlers** scansionano i dati e popolano il **Data Catalog** con schemi e metadati. I **Glue Jobs** (Spark/Python) trasformano i dati tra le zone.
- **Amazon Athena**: query SQL serverless direttamente su dati in S3. Supporta Parquet, ORC, JSON, CSV. Pagamento per query (per TB scansionato). Usare formati colonnari (Parquet) e partitioning per ridurre costi e tempi.
- **Amazon Redshift**: data warehouse per analisi complesse e dashboard ad alte prestazioni. Redshift Spectrum interroga dati in S3 senza doverli caricare in Redshift.
- **AWS Lake Formation**: governance del data lake con controllo degli accessi a livello di tabella, colonna e riga. Semplifica la configurazione delle policy di accesso rispetto a policy IAM granulari su S3.
- **Amazon QuickSight**: servizio BI serverless per dashboard e visualizzazioni interattive.

### Pattern 4 — Applicazione Serverless Event-Driven

```
    Client Mobile / Web
           │
    ┌──────┴──────┐
    │  API Gateway │
    │  (HTTP API)  │
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │   Lambda    │  Logica di business
    │  (handler)  │
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │  DynamoDB   │  Storage primario
    └──────┬──────┘
           │ (DynamoDB Streams)
    ┌──────┴──────┐
    │ EventBridge │  Bus eventi
    └──────┬──────┘
      ┌────┼────┐
      │    │    │
   Lambda Lambda Step Functions
   (email)(audit)(workflow complesso)
```

Vantaggi: nessun server da gestire, scaling automatico, pagamento a consumo, time-to-market rapido. Limitazioni: cold start, timeout Lambda 15 min, vendor lock-in, debugging distribuito piu complesso.

---

## 16. Troubleshooting — Problemi Comuni e Soluzioni

### 16.1 EC2 — L'istanza non si avvia

**Sintomo**: `RunInstances` restituisce errore o l'istanza va in stato `terminated` immediatamente.

**Cause e soluzioni**:
- `InsufficientInstanceCapacity`: AWS non ha capacita sufficiente per il tipo di istanza nella AZ selezionata. Provare un'altra AZ, un tipo di istanza diverso, o attendere.
- `InstanceLimitExceeded`: superato il limite di istanze per l'account nella regione. Richiedere un aumento del limite tramite Service Quotas.
- AMI corrotta o non compatibile con il tipo di istanza (es. AMI x86 su istanza Graviton ARM).
- EBS volume cifrato con una chiave KMS a cui il ruolo dell'istanza non ha accesso.

### 16.2 EC2 — Impossibile connettersi via SSH

**Sintomo**: `Connection timed out` o `Connection refused` quando si tenta di accedere all'istanza.

**Cause e soluzioni**:
- Security Group: verificare che la porta 22 sia aperta per l'IP sorgente.
- NACL: verificare che le regole della NACL consentano traffico in ingresso sulla porta 22 e in uscita sulle porte effimere (1024-65535).
- Route table: verificare che la subnet abbia una rotta verso l'IGW (subnet pubblica) o che si stia usando un bastion host.
- Elastic IP / Public IP: verificare che l'istanza abbia un IP pubblico assegnato.
- Key pair: verificare di usare la chiave privata corretta per la coppia di chiavi associata all'istanza.
- Sistema operativo: verificare che il servizio SSH sia avviato e in ascolto (`sshd`).

### 16.3 S3 — Access Denied (403)

**Sintomo**: `AccessDenied` quando si tenta di accedere a un oggetto o bucket.

**Cause e soluzioni**:
- Verificare la identity-based policy dell'identita chiamante (utente, ruolo).
- Verificare la bucket policy: potrebbe avere un Deny esplicito.
- Verificare le impostazioni di Block Public Access: potrebbero bloccare l'accesso anche se la policy lo consente.
- Se il bucket e in un altro account, verificare che sia la identity-based policy che la bucket policy consentano l'accesso.
- Se l'oggetto e cifrato con KMS, verificare che l'identita abbia permessi sulla chiave KMS (`kms:Decrypt`).
- Se l'oggetto e stato caricato da un altro account, il proprietario del bucket potrebbe non averne l'ownership. Usare `bucket-owner-full-control` ACL.

### 16.4 Lambda — Timeout

**Sintomo**: la funzione viene terminata con errore `Task timed out after X seconds`.

**Cause e soluzioni**:
- Verificare se il timeout configurato e sufficiente per l'operazione (max 15 minuti).
- Se la funzione accede a risorse in VPC (es. RDS), verificare che la subnet abbia un NAT Gateway per l'accesso a Internet o VPC Endpoint per servizi AWS.
- Ottimizzare il codice: connessioni al database fuori dall'handler (riutilizzate tra invocazioni), ridurre la dimensione dei dati elaborati, usare operazioni batch.
- Se il problema e il cold start, aumentare la memoria (piu CPU) o usare provisioned concurrency.

### 16.5 Lambda — Errori di Permesso

**Sintomo**: `AccessDeniedException` quando la funzione tenta di accedere a un servizio AWS.

**Cause e soluzioni**:
- Verificare che l'execution role della funzione abbia le policy necessarie (es. `s3:GetObject` per leggere da S3).
- Verificare che le resource-based policy del servizio di destinazione consentano l'accesso dalla funzione.
- Se il servizio usa KMS, verificare che il ruolo abbia permessi sulla chiave.
- Verificare eventuali SCP a livello di Organizations che potrebbero bloccare l'azione.

### 16.6 RDS — Connessione Rifiutata

**Sintomo**: l'applicazione non riesce a connettersi al database RDS.

**Cause e soluzioni**:
- Security Group dell'istanza RDS: verificare che consenta connessioni in ingresso sulla porta del database (3306 per MySQL, 5432 per PostgreSQL) dal Security Group dell'applicazione.
- L'istanza RDS non e accessibile pubblicamente (default): verificare che l'applicazione sia nella stessa VPC o che ci sia una connessione di rete (peering, Transit Gateway).
- Subnet Group: verificare che le subnet del DB Subnet Group siano raggiungibili dall'applicazione.
- Credenziali: verificare username, password e nome del database.
- Max connections: il numero massimo di connessioni potrebbe essere stato raggiunto. Verificare la metrica `DatabaseConnections` in CloudWatch.

### 16.7 RDS — Prestazioni Degradate

**Sintomo**: query lente, latenza elevata, alta CPU.

**Cause e soluzioni**:
- Verificare il tipo di istanza: potrebbe essere sottodimensionato. Usare Performance Insights per identificare le query piu costose.
- Abilitare Read Replicas per scaricare il traffico di lettura.
- Ottimizzare le query: indici mancanti, full table scan, query N+1.
- Verificare i parametri IOPS del volume EBS: storage gp2 potrebbe essere in throttling se il burst credit e esaurito. Passare a gp3 o io2.
- Connessioni idle: implementare connection pooling (es. RDS Proxy, PgBouncer).

### 16.8 VPC — Le Istanze nella Subnet Privata non Accedono a Internet

**Sintomo**: le istanze in subnet private non possono raggiungere endpoint esterni.

**Cause e soluzioni**:
- Verificare che esista un NAT Gateway in una subnet pubblica.
- Verificare la route table della subnet privata: deve avere `0.0.0.0/0 -> nat-gw-xxx`.
- Verificare la route table della subnet pubblica del NAT Gateway: deve avere `0.0.0.0/0 -> igw-xxx`.
- Verificare che il NAT Gateway abbia un Elastic IP associato.
- Verificare Security Group e NACL: il traffico in uscita deve essere consentito.
- Se l'accesso e solo verso servizi AWS, usare VPC Endpoints invece del NAT Gateway (piu economico e sicuro).

### 16.9 CloudFormation — Stack in Stato UPDATE_ROLLBACK_FAILED

**Sintomo**: lo stack non puo completare il rollback e rimane bloccato.

**Cause e soluzioni**:
- Una risorsa creata durante l'aggiornamento e stata modificata manualmente e non puo essere eliminata.
- Utilizzare `ContinueUpdateRollback` con la lista di risorse da saltare.
- Identificare la risorsa problematica nel tab Events.
- In ultimo resort, eliminare la risorsa manualmente e riprovare il rollback.

### 16.10 CloudFormation — Errore "No updates are to be performed"

**Sintomo**: il deployment fallisce con il messaggio che non ci sono aggiornamenti.

**Causa**: il template non ha modifiche rispetto allo stato corrente dello stack. Se le modifiche sono solo nei parametri o nelle condizioni senza impatto sulle risorse, CloudFormation non rileva differenze. Soluzione: usare Change Sets per verificare prima se ci sono modifiche effettive.

### 16.11 IAM — Policy Non Funziona Come Previsto

**Sintomo**: un Allow non ha effetto o un'azione e bloccata nonostante la policy.

**Cause e soluzioni**:
- Verificare la logica di valutazione: un Deny esplicito in qualsiasi policy (SCP, identity-based, resource-based, permission boundary) blocca sempre.
- Verificare le SCP dell'OU/account: potrebbero non includere l'azione.
- Verificare i permission boundaries dell'identita.
- Usare **IAM Policy Simulator** per testare l'effetto delle policy senza eseguire realmente le azioni.
- Usare **CloudTrail** per verificare quale policy ha causato il deny (campo `errorCode: AccessDenied`, `errorMessage` con dettagli).

### 16.12 ECS — Task che Fallisce Continuamente

**Sintomo**: i task ECS si avviano e si arrestano in loop (`STOPPED` con codice di uscita non zero).

**Cause e soluzioni**:
- Verificare i log del container in CloudWatch (il task deve avere `logConfiguration` configurato).
- Codice di uscita 137: Out of Memory. Aumentare la memoria nella Task Definition.
- Codice di uscita 1: errore applicativo. Verificare i log per l'errore specifico.
- `CannotPullContainerError`: l'immagine non esiste in ECR o il Task Execution Role non ha permessi `ecr:GetDownloadUrlForLayer`.
- Health check fallito: verificare che l'endpoint di health check risponda correttamente e che il timeout sia adeguato.

### 16.13 DynamoDB — Throttling (ProvisionedThroughputExceededException)

**Sintomo**: le richieste vengono rifiutate con errore di throttling.

**Cause e soluzioni**:
- **Hot partition**: la partition key ha distribuzione non uniforme. Verificare con CloudWatch Contributor Insights quali chiavi generano piu traffico.
- Capacita insufficiente: aumentare le RCU/WCU o passare a modalita On-Demand.
- Auto-scaling non reattivo: le policy di auto-scaling potrebbero avere target troppo alto o scaling troppo lento. Abbassare il target utilization (es. da 70% a 50%).
- Burst capacity: DynamoDB riserva una porzione di capacita non utilizzata per i burst. Se il burst e esaurito e il traffico supera la capacita provisionata, si verifica throttling.

### 16.14 API Gateway — Errore 502 Bad Gateway

**Sintomo**: API Gateway restituisce 502 alle richieste.

**Cause e soluzioni**:
- Il backend (Lambda, EC2) restituisce una risposta in formato non valido. Per Lambda Proxy integration, la risposta deve avere `statusCode`, `headers` e `body`.
- Lambda timeout: la funzione impiega piu tempo del timeout di API Gateway (29 secondi per REST API).
- Integration timeout: verificare il timeout dell'integrazione backend.
- Errore nel backend: verificare i log della funzione Lambda o del servizio backend.

### 16.15 CloudWatch — Metriche Custom Non Visibili

**Sintomo**: le metriche pubblicate con `PutMetricData` non appaiono in CloudWatch.

**Cause e soluzioni**:
- Verificare il namespace: le metriche custom devono usare un namespace personalizzato (non `AWS/`).
- Verificare il timestamp: metriche con timestamp futuro o troppo passato (> 2 settimane) vengono ignorate.
- Verificare le dimensioni: le metriche con dimensioni diverse sono metriche separate.
- Verificare i permessi: il ruolo deve avere `cloudwatch:PutMetricData`.
- Attendere: le metriche possono richiedere fino a 5 minuti per essere visibili.

### 16.16 Auto Scaling — Scaling Troppo Lento

**Sintomo**: l'ASG non scala abbastanza velocemente per gestire i picchi di traffico.

**Cause e soluzioni**:
- Ridurre il cooldown period (default 300 secondi) per consentire scaling piu frequente.
- Usare **step scaling** con soglie multiple per scaling piu aggressivo a carichi elevati.
- Abilitare **predictive scaling** per anticipare i picchi basandosi su pattern storici.
- Usare un **warm pool** per avere istanze pre-inizializzate pronte al lancio.
- Ottimizzare il tempo di avvio dell'istanza: AMI pre-configurate, user data minimale.

### 16.17 VPC Peering — Traffico Non Instradato

**Sintomo**: le istanze in VPC peered non possono comunicare.

**Cause e soluzioni**:
- Verificare che il peering sia in stato `Active` (accettato da entrambi i lati).
- Verificare le route tables di entrambe le VPC: ciascuna deve avere una rotta verso il CIDR dell'altra VPC con target la connessione di peering.
- Verificare che i CIDR delle VPC non si sovrappongano.
- Verificare Security Groups e NACL in entrambe le VPC.
- Per peering cross-account, verificare che DNS resolution sia abilitata su entrambi i lati.

### 16.18 EBS — Volume Pieno

**Sintomo**: l'applicazione smette di scrivere, errori di "no space left on device".

**Cause e soluzioni**:
- Aumentare la dimensione del volume tramite `ModifyVolume` (operazione online, senza downtime).
- Dopo il resize, estendere il filesystem: `growpart /dev/xvda 1` + `resize2fs /dev/xvda1` (ext4) o `xfs_growfs /` (xfs).
- Identificare i file che occupano piu spazio: `du -sh /* | sort -rh | head -20`.
- Implementare monitoraggio proattivo: alarm su metrica `disk_used_percent` del CloudWatch Agent.

### 16.19 Route 53 — Record DNS Non Risolto

**Sintomo**: il dominio non risolve o risolve all'indirizzo sbagliato.

**Cause e soluzioni**:
- Verificare che il record esista nella hosted zone corretta.
- Verificare i nameserver del dominio: devono puntare ai nameserver della hosted zone Route 53.
- Propagazione DNS: le modifiche possono richiedere fino al TTL precedente per propagarsi. Usare `dig @ns-xxx.awsdns-xx.com dominio.com` per query diretta ai nameserver Route 53.
- Per record Alias verso risorse AWS, verificare che la risorsa di destinazione esista e sia nella stessa regione (dove applicabile).

### 16.20 Secrets Manager — Rotazione Fallita

**Sintomo**: il segreto non viene ruotato e la Lambda di rotazione fallisce.

**Cause e soluzioni**:
- Verificare i log della Lambda di rotazione in CloudWatch.
- La Lambda deve avere accesso di rete al servizio di destinazione (es. RDS). Se il servizio e in una VPC privata, la Lambda deve essere nella stessa VPC con un NAT Gateway o VPC endpoint per Secrets Manager.
- Verificare che il ruolo della Lambda abbia permessi per accedere a Secrets Manager (`secretsmanager:GetSecretValue`, `secretsmanager:PutSecretValue`).
- Verificare che le credenziali master (se usate) siano valide e che l'utente master abbia i permessi per modificare la password dell'utente target.

### 16.21 Certificate Manager — Validazione DNS Bloccata

**Sintomo**: il certificato ACM rimane in stato `Pending validation`.

**Cause e soluzioni**:
- Per validazione DNS: verificare che il record CNAME fornito da ACM sia stato creato nella zona DNS corretta. Il record ha un nome del tipo `_xxxxx.dominio.com` e un valore del tipo `_yyyyy.acm-validations.aws`.
- Se il DNS e gestito da Route 53, usare il pulsante "Create record in Route 53" nella console ACM.
- Se il DNS e gestito esternamente, copiare il record CNAME esattamente come fornito da ACM.
- La propagazione puo richiedere fino a 72 ore in casi estremi, ma tipicamente avviene in minuti.

---

## 17. FAQ — Domande Frequenti

### Q1: Dovrei usare una singola regione o multi-region?

**R**: Dipende dai requisiti. Per la maggior parte delle applicazioni, una singola regione con deployment multi-AZ e sufficiente per l'alta disponibilita. Multi-region e necessaria quando: (a) la normativa richiede residenza dei dati in piu paesi, (b) il RTO/RPO richiede failover immediato su un'altra regione, (c) gli utenti finali sono distribuiti globalmente e la latenza e critica. Multi-region aumenta significativamente la complessita operativa e i costi. Usare CloudFront per mitigare la latenza prima di investire in multi-region.

### Q2: Quando usare Lambda vs Fargate vs EC2?

**R**: **Lambda** per funzioni event-driven di breve durata (< 15 min), basso traffico o con picchi sporadici, logica semplice senza stato. **Fargate** per container long-running senza gestione dei server, microservizi con traffico costante, applicazioni che richiedono piu di 15 minuti di esecuzione o configurazioni di rete complesse. **EC2** quando serve pieno controllo sull'OS, GPU, software con requisiti di licenza specifici, o workload ad alte prestazioni (HPC). In generale, preferire serverless (Lambda/Fargate) per nuovi progetti e usare EC2 solo quando ci sono vincoli specifici che lo richiedono.

### Q3: Come proteggere le credenziali nel codice?

**R**: Non inserire mai credenziali nel codice sorgente, variabili d'ambiente hardcodate o file di configurazione committati in git. Usare **Secrets Manager** per credenziali che richiedono rotazione (password database, API key). Usare **SSM Parameter Store** (SecureString) per configurazione sensibile che non richiede rotazione automatica. Per servizi AWS, usare **IAM Roles** (instance profile per EC2, execution role per Lambda/ECS, OIDC federation per pipeline CI/CD) invece di access keys. Implementare `.gitignore` per escludere file `.env` e usare pre-commit hooks per rilevare segreti accidentali (es. git-secrets).

### Q4: Quale strategia di disaster recovery scegliere?

**R**: La strategia dipende da RPO e RTO dell'applicazione e dal budget. **Backup & Restore** (RPO/RTO ore): sufficiente per ambienti non critici, costo minimo. **Pilot Light** (RPO minuti, RTO minuti-ore): database replicato in altra regione, compute avviato al bisogno. **Warm Standby** (RPO secondi, RTO minuti): ambiente ridotto sempre attivo nella regione secondaria. **Multi-Site Active-Active** (RPO/RTO ~zero): piu regioni servono traffico contemporaneamente, massimo costo e complessita. Per la maggior parte delle applicazioni business, Pilot Light o Warm Standby offrono il miglior rapporto costo/protezione.

### Q5: VPC Peering o Transit Gateway?

**R**: **VPC Peering** per connessioni punto-a-punto tra poche VPC (< 10) con pattern di traffico semplici. E gratuito (si paga solo il trasferimento dati). **Transit Gateway** quando: ci sono molte VPC da connettere (> 10), serve routing transitivo, si vogliono route tables centralizzate per segmentazione, o si integrano VPN e Direct Connect. Transit Gateway ha un costo per attachment e per GB. Non miscelare i due approcci senza una strategia chiara.

### Q6: Come ridurre i costi di un ambiente AWS esistente?

**R**: Processo sistematico: (1) Abilitare **Compute Optimizer** e analizzare le raccomandazioni di right-sizing. (2) Identificare risorse inutilizzate con **Trusted Advisor** (EIP non associati, EBS non collegati, istanze idle). (3) Implementare **Savings Plans** per il baseline di compute stabile. (4) Usare **Spot** per workload fault-tolerant. (5) Implementare **S3 Lifecycle Policies** e Intelligent-Tiering. (6) Spegnere ambienti non-prod fuori orario con **Instance Scheduler**. (7) Usare **VPC Endpoints** per eliminare costi NAT Gateway per traffico verso servizi AWS. (8) Valutare **Graviton** per carichi compatibili. (9) Usare **RDS Reserved Instances** per database stabili. (10) Monitorare mensilmente con **Cost Explorer**.

### Q7: Come migrare un database on-premises a AWS?

**R**: Usare **AWS Database Migration Service (DMS)** per migrazioni con downtime minimo. DMS supporta migrazioni omogenee (stesso engine) e eterogenee (engine diversi, con **Schema Conversion Tool** per la conversione dello schema). Flusso: (1) Valutare il database sorgente con SCT. (2) Creare l'istanza RDS/Aurora target. (3) Configurare la task DMS con full load + CDC (Change Data Capture) per sincronizzazione continua. (4) Testare l'applicazione con il nuovo database. (5) Eseguire il cutover (switchare l'applicazione al nuovo endpoint). DMS supporta MySQL, PostgreSQL, Oracle, SQL Server, MongoDB, Redis e altri.

### Q8: Quando usare DynamoDB vs RDS?

**R**: **DynamoDB** quando: i pattern di accesso sono noti e limitati (key-value o chiave composta), serve scaling orizzontale illimitato, serve latenza in millisecondi singoli a qualsiasi scala, non servono join o transazioni complesse. **RDS/Aurora** quando: i dati sono altamente relazionali con molte relazioni, servono query SQL complesse con join, i pattern di accesso sono vari e imprevedibili, serve conformita ACID completa con transazioni multi-tabella. Non usare DynamoDB come database relazionale forzato: il modello single-table design e potente ma richiede una progettazione accurata delle chiavi basata sui pattern di accesso.

### Q9: Come gestire i segreti tra ambienti (dev, staging, prod)?

**R**: Usare una naming convention in Secrets Manager o Parameter Store che includa l'ambiente: `/prod/app-name/db-password`, `/staging/app-name/db-password`. Le funzioni Lambda e i servizi leggono il percorso appropriato tramite variabile d'ambiente che specifica il prefisso dell'ambiente. I permessi IAM restringono l'accesso ai segreti per ambiente: il ruolo di produzione non puo leggere i segreti di staging e viceversa. Per multi-account, ogni account ha i propri segreti con replica automatica tramite Secrets Manager cross-account sharing dove necessario.

### Q10: Come implementare CI/CD per infrastruttura AWS?

**R**: Pipeline tipica: (1) Commit di template IaC (CloudFormation/CDK/Terraform) su un branch. (2) Pipeline CI (CodePipeline, GitHub Actions) esegue `cdk diff` / `terraform plan` / change set CloudFormation. (3) Review manuale del plan. (4) Apply automatico su ambiente dev/staging. (5) Test automatizzati sull'ambiente. (6) Approvazione manuale per produzione. (7) Apply su produzione con rollback automatico in caso di errore. Per CI/CD di infrastruttura AWS, usare **OIDC federation** per l'autenticazione del pipeline (non access keys), con ruoli IAM separati per ogni ambiente e permessi minimi.

### Q11: Qual e la differenza tra NLB e ALB?

**R**: **ALB** opera a Layer 7 (HTTP/HTTPS) con routing basato su contenuto (path, host, headers), supporta WebSocket, gRPC, autenticazione integrata. Ideale per applicazioni web e microservizi. **NLB** opera a Layer 4 (TCP/UDP) con prestazioni estreme (milioni di richieste/secondo), latenza minima, IP statici per AZ. Ideale per protocolli non-HTTP, applicazioni che necessitano di IP fissi, e servizi esposti via PrivateLink. Non usare NLB per applicazioni web standard: ALB offre funzionalita di routing che semplificano l'architettura.

### Q12: Come monitorare i costi in tempo reale?

**R**: (1) Configurare **AWS Budgets** con alert al 50%, 80% e 100% della spesa prevista. (2) Abilitare **Cost Anomaly Detection** per notifiche automatiche su spese anomale. (3) Creare **Cost Explorer reports** salvati per i principali centri di costo. (4) Implementare **tag-based cost allocation** per attribuire i costi ai team/progetti. (5) Per alert piu immediati, usare una Lambda schedulata che controlla la spesa giornaliera tramite Cost Explorer API e invia notifiche Slack/email quando supera soglie personalizzate.

### Q13: Come gestire i limiti di servizio AWS?

**R**: Ogni servizio AWS ha limiti (service quotas) per account e regione. Esempi: 1.000 istanze EC2 per regione, 100 bucket S3 per account, 500 security groups per VPC. (1) Monitorare i limiti con **AWS Service Quotas** e configurare alarm CloudWatch sulle metriche di utilizzo. (2) Richiedere aumenti proattivamente prima di raggiungere i limiti. (3) L'architettura multi-account distribuisce i workload su account separati, ciascuno con i propri limiti. (4) Usare **Trusted Advisor** per identificare risorse vicine ai limiti.

### Q14: ECS Fargate o EKS Fargate?

**R**: Entrambi eliminano la gestione dei server. **ECS Fargate** per team che preferiscono la semplicita AWS-native, non necessitano di portabilita Kubernetes e vogliono integrazione profonda con l'ecosistema AWS. **EKS Fargate** per team con competenze Kubernetes, che usano Helm charts e operatori, necessitano di portabilita multi-cloud, o hanno workload che beneficiano delle funzionalita avanzate di Kubernetes (custom controllers, service mesh). EKS Fargate non supporta DaemonSets, ha limitazioni su hostNetwork e richiede un Fargate Profile per namespace. Per la maggior parte dei nuovi progetti su AWS, ECS Fargate e la scelta piu semplice ed efficiente.

### Q15: Come implementare la comunicazione tra microservizi?

**R**: Due pattern principali: **Sincrono** (HTTP/gRPC via ALB interno o service mesh) per operazioni che richiedono risposta immediata. Implementare retry con backoff esponenziale e circuit breaker per resilienza. **Asincrono** (SQS, SNS, EventBridge) per operazioni che non richiedono risposta immediata. SQS per task queue punto-a-punto, SNS per fan-out a piu consumatori, EventBridge per routing basato su contenuto degli eventi. Preferire la comunicazione asincrona per il disaccoppiamento: i servizi restano operativi anche quando le dipendenze sono temporaneamente non disponibili.

### Q16: Come gestire la sicurezza in un ambiente multi-account?

**R**: (1) Account dedicato per la sicurezza con **GuardDuty** come delegated administrator. (2) **Security Hub** aggregato a livello organizzazione con standard CIS e FSBP abilitati. (3) **CloudTrail** organization trail con log in un bucket dell'account Log Archive con policy che impediscono la cancellazione. (4) **AWS Config** con regole di conformita aggregate cross-account. (5) SCP restrittive sulle OU (blocco regioni, impedire la disabilitazione di GuardDuty/CloudTrail/Config). (6) **IAM Identity Center** per l'accesso centralizzato con permission sets per ruolo. (7) Automazione della risposta: EventBridge rules che triggerano Lambda per remediation automatica (es. chiudere porte aperte, revocare accessi anomali).

---

## Esercizi

1. **VPC Multi-Tier (Base)**
   Creare una VPC con tre subnet (pubblica, privata applicativa, privata database) distribuite su due AZ. Configurare le route table, il NAT Gateway e un Security Group che consenta solo traffico HTTPS in ingresso sulla subnet pubblica. Verificare la connettività con un'istanza EC2 in ogni tier.

2. **IAM OIDC Federation per CI/CD (Intermedio)**
   Configurare un Identity Provider OIDC in IAM per GitHub Actions. Creare un ruolo IAM con trust policy che limiti l'assunzione al repository e al branch specifico. Scrivere un workflow GitHub Actions che assuma il ruolo e deploji un file su S3 senza access key statiche.

3. **Architettura Multi-Account con Organizations (Intermedio)**
   Disegnare e implementare una struttura AWS Organizations con almeno tre OU (Security, Workloads-Prod, Workloads-Dev). Applicare SCP che blocchino le regioni non utilizzate e impediscano la disabilitazione di CloudTrail. Configurare un trail organizzativo con log centralizzati.

4. **Disaster Recovery Cross-Region (Avanzato)**
   Implementare un'architettura DR pilot-light per un'applicazione web: RDS con cross-region read replica, AMI replicate nella regione secondaria, Route 53 con health check e failover routing. Simulare il failover e misurare l'RTO effettivo.

5. **Cost Optimization e Alerting (Avanzato)**
   Configurare AWS Budgets con soglie al 50%, 80% e 100%. Abilitare Cost Anomaly Detection. Creare una Lambda schedulata che interroghi Cost Explorer API e invii un report giornaliero su Slack con i costi per servizio e per tag. Identificare almeno tre opportunità di risparmio con Trusted Advisor e Compute Optimizer.

---

## Letture e Riferimenti

**Documentazione ufficiale**

- AWS Well-Architected Framework — https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html (consultato: 2026-05-24)
- AWS IAM User Guide — https://docs.aws.amazon.com/IAM/latest/UserGuide/ (consultato: 2026-05-24)
- Amazon VPC User Guide — https://docs.aws.amazon.com/vpc/latest/userguide/ (consultato: 2026-05-24)
- AWS Organizations User Guide — https://docs.aws.amazon.com/organizations/latest/userguide/ (consultato: 2026-05-24)
- AWS Security Hub User Guide — https://docs.aws.amazon.com/securityhub/latest/userguide/ (consultato: 2026-05-24)
- AWS Cost Management — https://docs.aws.amazon.com/cost-management/latest/userguide/ (consultato: 2026-05-24)
- AWS CloudFormation User Guide — https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/ (consultato: 2026-05-24)
- AWS Architecture Center — https://aws.amazon.com/architecture/ (consultato: 2026-05-24)

**Libri consigliati**

- *AWS Certified Solutions Architect Study Guide* — Ben Piper, David Clinton (Sybex/Wiley)
- *Amazon Web Services in Action* — Michael Wittig, Andreas Wittig (Manning, 3ª edizione)
- *Security Best Practices on AWS* — Albert Zhichun Li, AWS (O'Reilly)

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|--------|--------|-----------|
| [02](02-cloud-azure.md) | Microsoft Azure | Confronto servizi equivalenti e strategie multi-cloud |
| [03](03-cloud-gcp.md) | Google Cloud Platform | Confronto IAM, networking e servizi managed |
| [04](04-infrastructure-as-code.md) | Infrastructure as Code | Terraform provider AWS, CloudFormation, CDK |
| [07](07-ci-cd.md) | CI/CD | Pipeline con CodePipeline, GitHub Actions e OIDC |
| [13](13-sicurezza-piattaforme.md) | Sicurezza Piattaforme | GuardDuty, Security Hub, hardening account |
| [21](21-finops-cost-governance.md) | FinOps e Cost Governance | Budgets, Cost Explorer, Reserved Instances |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **AZ (Availability Zone)** | Data center isolato all'interno di una regione AWS, connesso con bassa latenza alle altre AZ della stessa regione |
| **ARN (Amazon Resource Name)** | Identificatore univoco globale per ogni risorsa AWS, usato nelle policy IAM |
| **CloudTrail** | Servizio di auditing che registra tutte le chiamate API effettuate sull'account AWS |
| **GuardDuty** | Servizio di rilevamento minacce che analizza log VPC Flow, DNS e CloudTrail per attività sospette |
| **IAM (Identity and Access Management)** | Sistema di gestione delle identità e dei permessi per controllare l'accesso alle risorse AWS |
| **NAT Gateway** | Componente di rete che consente alle istanze in subnet private di accedere a Internet senza esporre IP pubblici |
| **OIDC Federation** | Meccanismo di autenticazione federata basato su OpenID Connect per assumere ruoli IAM senza credenziali statiche |
| **OU (Organizational Unit)** | Contenitore logico all'interno di AWS Organizations per raggruppare account e applicare policy |
| **SCP (Service Control Policy)** | Policy che definisce i permessi massimi applicabili agli account di un'organizzazione AWS |
| **Security Group** | Firewall virtuale a livello di istanza che controlla il traffico in ingresso e uscita |
| **Security Hub** | Servizio centralizzato per la gestione della postura di sicurezza e la conformità agli standard |
| **VPC (Virtual Private Cloud)** | Rete virtuale isolata all'interno di AWS dove vengono deployate le risorse |
| **Well-Architected Framework** | Framework AWS con sei pilastri per progettare architetture cloud sicure, affidabili e ottimizzate |
| **Transit Gateway** | Hub di rete regionale che connette VPC multipli e reti on-premises con routing centralizzato |

> **Riferimenti e approfondimenti**: [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/), [AWS Documentation](https://docs.aws.amazon.com/), [AWS Architecture Center](https://aws.amazon.com/architecture/)
