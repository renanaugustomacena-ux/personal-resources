---
corso: "Gestione Piattaforme e DevOps"
fase: "1 — Cloud Provider"
modulo: 2
titolo: "Microsoft Azure — Documentazione Completa"
versione: "2026"
livello: "Avanzato"
prerequisiti: ["01-cloud-aws", "03-cloud-gcp", "04-infrastructure-as-code"]
obiettivi:
  - "Comprendere l'architettura globale Azure e il modello di gestione basato su Resource Group"
  - "Configurare identità e accessi con Entra ID, RBAC, Managed Identities e PIM"
  - "Progettare reti hub-and-spoke con VNet, Azure Firewall e Private Endpoints"
  - "Implementare governance con Management Groups, Azure Policy e tagging obbligatorio"
  - "Ottimizzare costi con Reserved Instances, Savings Plans e Azure Advisor"
tag: [azure, cloud, entra-id, rbac, vnet, governance, bicep, management-groups]
---

# Microsoft Azure — Documentazione Completa

> **Modulo 02** · **Tempo:** 90 min · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Comprendere l'architettura globale Azure e il modello di gestione basato su Resource Group
> 2. Configurare identità e accessi con Entra ID, RBAC, Managed Identities e PIM
> 3. Progettare reti hub-and-spoke con VNet, Azure Firewall e Private Endpoints
> 4. Implementare governance con Management Groups, Azure Policy e tagging obbligatorio
> 5. Ottimizzare costi con Reserved Instances, Savings Plans e Azure Advisor
>
> **Prerequisiti:** [AWS](01-cloud-aws.md) · [GCP](03-cloud-gcp.md) · [IaC](04-infrastructure-as-code.md)
> **Tempo stimato:** 90 min · **Livello:** Avanzato

## Idee guida

1. **Azure forte in M365 ecosystem.** AD/Entra ID integration nativa.
2. **Resource Group = unit of management.** Tagging mandatory.
3. **Workload Identity Federation > SP secret.** OIDC per CI/CD.
4. **Cost: Reserved Instance 1-3 anni risparmia 30-60%.**


## Indice

1. [Panoramica dell'Infrastruttura Globale Azure](#1-panoramica-dellinfrastruttura-globale-azure)
2. [Identita e Accesso — Microsoft Entra ID](#2-identita-e-accesso--microsoft-entra-id)
3. [Networking](#3-networking)
4. [Compute](#4-compute)
5. [Storage](#5-storage)
6. [Database](#6-database)
7. [Containers — ACI, AKS, ACR](#7-containers--aci-aks-acr)
8. [Monitoring e Observability](#8-monitoring-e-observability)
9. [Security](#9-security)
10. [Cost Management](#10-cost-management)
11. [Infrastructure as Code — ARM e Bicep](#11-infrastructure-as-code--arm-e-bicep)
12. [Best Practices](#12-best-practices)
13. [Azure DevOps e GitHub Integration](#13-azure-devops-e-github-integration)
14. [Azure Landing Zones](#14-azure-landing-zones)
15. [Azure Well-Architected Framework — I Cinque Pilastri](#15-azure-well-architected-framework--i-cinque-pilastri)

---

## 1. Panoramica dell'Infrastruttura Globale Azure

Microsoft Azure e la piattaforma cloud di Microsoft, seconda per quota di mercato globale dopo AWS. Offre oltre 200 servizi su un'infrastruttura globale progettata per resilienza, scalabilita e conformita normativa. Si distingue per l'integrazione nativa con l'ecosistema Microsoft (Active Directory, Office 365, Windows Server, SQL Server) e per la copertura capillare nelle regioni europee, rilevante per il GDPR.

### Regions (Regioni)

Una **Region** Azure e un insieme di data center collegati tramite una rete regionale dedicata a bassa latenza. Azure opera in oltre 60 regioni distribuite in piu di 140 paesi. La scelta della regione dipende da:

- **Conformita normativa**: il GDPR e altre normative europee richiedono che i dati risiedano in specifiche giurisdizioni. Le regioni `West Europe` (Paesi Bassi), `North Europe` (Irlanda), `Germany West Central` (Francoforte) e `Italy North` (Milano) sono scelte tipiche per workload europei.
- **Latenza**: si seleziona la regione piu vicina agli utenti finali per ottimizzare i tempi di risposta. Azure fornisce lo strumento Azure Speed Test per misurare la latenza verso ciascuna regione.
- **Disponibilita dei servizi**: non tutti i servizi sono disponibili in tutte le regioni. I servizi piu recenti vengono rilasciati progressivamente, partendo dalle regioni principali come `East US` o `West Europe`.
- **Costo**: i prezzi variano tra regioni. Le regioni negli Stati Uniti tendono a essere meno costose rispetto a quelle in Asia o Sudamerica.
- **Paired Regions**: molte regioni Azure sono accoppiate a un'altra regione nella stessa area geografica (ad esempio, `North Europe` e `West Europe`). Microsoft garantisce che gli aggiornamenti della piattaforma vengano distribuiti in sequenza tra le regioni accoppiate, riducendo il rischio di downtime simultaneo. La replicazione geografica dello storage (GRS) utilizza le paired regions.

### Availability Zones (Zone di Disponibilita)

Le **Availability Zones** sono ubicazioni fisicamente separate all'interno di una regione Azure. Ogni zona e composta da uno o piu data center dotati di alimentazione, raffreddamento e connettivita indipendenti. Le regioni che supportano le Availability Zones ne offrono almeno tre, collegate da una rete ad alta velocita con latenza inferiore a 2 millisecondi.

Le Availability Zones sono fondamentali per architetture ad alta disponibilita. I servizi Azure si classificano in:

- **Zonal services**: risorse ancorate a una zona specifica (ad esempio, una VM in Zona 1). L'utente sceglie esplicitamente la zona.
- **Zone-redundant services**: la piattaforma replica automaticamente le risorse tra le zone (ad esempio, Azure SQL Database con zone-redundant deployment, ZRS per lo storage).
- **Always-available services**: servizi globali resilienti per progettazione, non legati a una regione specifica (ad esempio, Azure Front Door, Traffic Manager).

### Resource Groups (Gruppi di Risorse)

Un **Resource Group** e un contenitore logico che raggruppa risorse Azure correlate. Ogni risorsa Azure deve appartenere a uno e un solo Resource Group. I Resource Group servono per:

- **Organizzazione logica**: raggruppare risorse per applicazione, ambiente (dev, staging, prod) o team.
- **Gestione del ciclo di vita**: eliminare un Resource Group elimina tutte le risorse contenute, semplificando il cleanup degli ambienti temporanei.
- **Controllo degli accessi**: le assegnazioni RBAC a livello di Resource Group vengono ereditate da tutte le risorse contenute.
- **Tagging e cost management**: i tag applicati al Resource Group facilitano l'allocazione dei costi.

Un Resource Group ha una location (che indica dove vengono archiviati i metadati), ma le risorse al suo interno possono risiedere in regioni diverse.

### Subscriptions (Sottoscrizioni)

Una **Subscription** e l'unita di fatturazione e il confine logico per le risorse Azure. Ogni subscription e associata a un tenant Microsoft Entra ID e rappresenta un accordo di fatturazione con Microsoft. Le subscription servono come:

- **Confine di fatturazione**: ogni subscription genera una fattura separata, consentendo l'allocazione dei costi per reparto o progetto.
- **Confine di accesso**: le policy RBAC e Azure Policy possono essere applicate a livello di subscription.
- **Confine di scala**: alcune risorse hanno limiti (quote) per subscription. Subscription multiple consentono di superare questi limiti.

I tipi di subscription includono: Free (credito iniziale di 200 USD per 30 giorni), Pay-As-You-Go, Enterprise Agreement (EA), Cloud Solution Provider (CSP) e Microsoft Customer Agreement (MCA).

### Management Groups (Gruppi di Gestione)

I **Management Groups** forniscono un livello di governance superiore alle subscription. Consentono di organizzare le subscription in una gerarchia e applicare policy e controlli di accesso ereditati. La struttura gerarchica e:

```
Root Management Group
├── Management Group "Produzione"
│   ├── Subscription "Prod-App1"
│   └── Subscription "Prod-App2"
├── Management Group "Sviluppo"
│   ├── Subscription "Dev-Team-A"
│   └── Subscription "Dev-Team-B"
└── Management Group "Sandbox"
    └── Subscription "Sandbox-Experiments"
```

I Management Group supportano fino a sei livelli di profondita (escluso il root). Le Azure Policy applicate a un Management Group vengono ereditate da tutte le subscription e risorse sottostanti.

---

## 2. Identita e Accesso — Microsoft Entra ID

**Microsoft Entra ID** (precedentemente Azure Active Directory / Azure AD) e il servizio di identita e gestione degli accessi cloud di Microsoft. E il pilastro dell'autenticazione e dell'autorizzazione per Azure, Microsoft 365 e migliaia di applicazioni SaaS. A differenza dell'Active Directory on-premises (LDAP e Kerberos), Entra ID utilizza protocolli moderni: OAuth 2.0, OpenID Connect e SAML 2.0.

### Users e Groups

Un **User** in Entra ID rappresenta un'identita che puo accedere alle risorse. Gli utenti possono essere:

- **Cloud-only**: creati direttamente in Entra ID.
- **Sincronizzati**: provenienti da Active Directory on-premises tramite **Microsoft Entra Connect** (precedentemente Azure AD Connect).
- **Guest**: utenti esterni invitati tramite **B2B Collaboration**, che accedono con le credenziali della propria organizzazione.

I **Groups** organizzano gli utenti per semplificare l'assegnazione di permessi. I tipi principali sono:

- **Security Groups**: utilizzati per assegnare permessi a risorse. Possono essere assegnati staticamente o con **Dynamic Membership Rules** basate sugli attributi dell'utente (ad esempio, `user.department -eq "Engineering"`).
- **Microsoft 365 Groups**: forniscono strumenti di collaborazione (casella di posta condivisa, calendario, SharePoint, Teams).

### RBAC — Role-Based Access Control

Azure RBAC e il sistema di autorizzazione per gestire l'accesso granulare alle risorse Azure. Si basa su tre elementi fondamentali:

- **Security Principal**: l'identita che richiede l'accesso (user, group, service principal, managed identity).
- **Role Definition**: una collezione di permessi (actions, notActions, dataActions, notDataActions).
- **Scope**: il livello gerarchico a cui si applica il ruolo (Management Group, Subscription, Resource Group, risorsa specifica).

I **built-in roles** piu utilizzati sono:

| Ruolo | Descrizione |
|-------|-------------|
| **Owner** | Accesso completo a tutte le risorse, inclusa la possibilita di delegare l'accesso ad altri |
| **Contributor** | Puo creare e gestire tutte le risorse, ma non puo assegnare ruoli |
| **Reader** | Puo visualizzare le risorse esistenti, ma non modificarle |
| **User Access Administrator** | Puo gestire le assegnazioni di ruolo, ma non le risorse stesse |
| **Network Contributor** | Gestione completa delle risorse di rete |
| **Storage Blob Data Contributor** | Lettura, scrittura e cancellazione su Blob Storage |
| **Virtual Machine Contributor** | Gestione delle VM, ma non della rete virtuale o dello storage account |

Quando i built-in roles non soddisfano le esigenze, si possono creare **Custom Roles** definendo esattamente le azioni consentite:

```json
{
  "Name": "VM Operator Custom",
  "Description": "Puo avviare, fermare e riavviare le VM, ma non crearle o eliminarle",
  "Actions": [
    "Microsoft.Compute/virtualMachines/start/action",
    "Microsoft.Compute/virtualMachines/restart/action",
    "Microsoft.Compute/virtualMachines/deallocate/action",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/instanceView/read"
  ],
  "NotActions": [],
  "AssignableScopes": [
    "/subscriptions/{subscription-id}"
  ]
}
```

### Managed Identities

Le **Managed Identities** eliminano la necessita di gestire credenziali nel codice. Azure crea e gestisce automaticamente un'identita in Entra ID per la risorsa. Esistono due tipi:

- **System-assigned**: l'identita e legata al ciclo di vita della risorsa. Viene creata quando la risorsa viene abilitata e distrutta quando la risorsa viene eliminata. Ogni risorsa ha la propria identita dedicata.
- **User-assigned**: l'identita viene creata come risorsa Azure indipendente e puo essere assegnata a piu risorse. Il ciclo di vita e indipendente dalle risorse che la utilizzano.

Un esempio tipico: una VM con system-assigned managed identity che accede a Azure Key Vault per recuperare i secret, senza che il codice applicativo contenga credenziali. Il token viene ottenuto dall'Instance Metadata Service (IMDS) all'endpoint `169.254.169.254`.

### Conditional Access

Le **Conditional Access Policies** sono il motore decisionale zero-trust di Entra ID. Ogni policy valuta condizioni (signals) e applica decisioni (controls):

- **Signals**: utente/gruppo, applicazione di destinazione, location (IP/named location), stato del dispositivo (compliant, hybrid joined), livello di rischio dell'utente o del sign-in, piattaforma client.
- **Decisions**: consentire l'accesso, bloccare l'accesso, richiedere MFA, richiedere un dispositivo conforme, richiedere il cambio password, accettare i termini d'uso.

Esempio di policy: "Richiedere MFA per tutti gli utenti quando accedono ad Azure Portal da una location non aziendale".

### Privileged Identity Management (PIM)

**PIM** implementa il principio del **just-in-time access** per i ruoli privilegiati. Invece di assegnazioni permanenti, gli utenti attivano il ruolo privilegiato solo quando necessario, per una durata limitata. Le funzionalita principali includono:

- **Eligible assignments**: l'utente e idoneo al ruolo ma deve attivarlo esplicitamente.
- **Time-bound activation**: l'attivazione ha una durata massima configurabile (ad esempio, 8 ore).
- **Approval workflows**: l'attivazione puo richiedere l'approvazione di un responsabile.
- **MFA enforcement**: richiesta di MFA al momento dell'attivazione.
- **Audit trail**: tutte le attivazioni vengono registrate per il controllo.

PIM si applica sia ai ruoli Entra ID (Global Administrator, Application Administrator) sia ai ruoli RBAC di Azure (Owner, Contributor a livello di subscription).

---

## 3. Networking

Azure offre un set completo di servizi di rete per connettivita, sicurezza, distribuzione del traffico e integrazione con reti on-premises.

### Virtual Network (VNet)

Una **Virtual Network** e il blocco fondamentale della rete privata in Azure, che fornisce un ambiente isolato per la comunicazione tra risorse Azure, con Internet e con reti on-premises. Caratteristiche principali:

- **Address space**: lo spazio di indirizzi IP privati definito in notazione CIDR (ad esempio, `10.0.0.0/16`). Si utilizzano gli intervalli RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
- **Scope regionale**: una VNet e confinata a una singola regione Azure, ma puo comunicare con VNet in altre regioni tramite peering.
- **Isolamento**: ogni VNet e isolata dalle altre per impostazione predefinita.

### Subnets

Le **Subnets** segmentano lo spazio di indirizzi della VNet in segmenti piu piccoli. Ogni subnet risiede interamente all'interno di una singola Availability Zone o si estende su tutte le zone della regione. Le subnet servono per:

- Separazione logica dei tier applicativi (frontend, backend, database).
- Applicazione di regole di sicurezza differenziate tramite NSG.
- Delegazione a servizi specifici (ad esempio, `Microsoft.Sql/managedInstances`).

Azure riserva cinque indirizzi IP in ogni subnet: il primo (indirizzo di rete), i successivi tre (uso interno Azure) e l'ultimo (broadcast). Una subnet `/24` fornisce quindi 251 indirizzi utilizzabili.

### Network Security Groups (NSG)

Un **NSG** contiene regole di sicurezza per consentire o negare il traffico in ingresso e in uscita. Ogni regola specifica:

- **Priority**: un numero tra 100 e 4096. Le regole vengono valutate in ordine di priorita crescente; la prima corrispondenza viene applicata.
- **Source/Destination**: indirizzo IP, CIDR, service tag o Application Security Group.
- **Protocol**: TCP, UDP, ICMP o Any.
- **Port range**: porta singola, intervallo o asterisco per tutte.
- **Action**: Allow o Deny.

Un NSG puo essere associato a una subnet o a una NIC. Se applicati entrambi, il traffico deve superare entrambi i set di regole. I **Service Tags** (`AzureLoadBalancer`, `Internet`, `VirtualNetwork`, `Storage.WestEurope`) semplificano le regole evitando indirizzi IP specifici.

### Application Security Groups (ASG)

Gli **ASG** raggruppano le interfacce di rete delle VM per utilizzarli come sorgente o destinazione nelle regole NSG, scrivendo regole basate sulla funzione applicativa anziche sugli indirizzi IP:

```
Regola: Allow | Source: ASG-WebServers | Destination: ASG-AppServers | Port: 8080 | TCP
```

Gli ASG eliminano la necessita di aggiornare le regole NSG quando gli indirizzi IP cambiano.

### Azure Firewall

**Azure Firewall** e un servizio firewall gestito, stateful, con alta disponibilita e scalabilita illimitata. A differenza degli NSG (Layer 3/4), Azure Firewall supporta:

- **Application rules** (Layer 7): filtraggio basato su FQDN (ad esempio, consentire il traffico verso `*.microsoft.com`).
- **Network rules** (Layer 3/4): filtraggio basato su IP, porta e protocollo.
- **NAT rules**: DNAT per il traffico in ingresso.
- **Threat intelligence**: blocco automatico del traffico da/verso indirizzi IP e domini malevoli noti, basato sul feed di Microsoft Threat Intelligence.
- **TLS inspection** (Premium SKU): decifra e ispeziona il traffico HTTPS.
- **IDPS** (Premium SKU): sistema di rilevamento e prevenzione delle intrusioni.

Azure Firewall viene tipicamente distribuito in una VNet hub in un'architettura hub-and-spoke, con UDR che forzano il traffico delle VNet spoke attraverso il firewall.

### Application Gateway e WAF

**Azure Application Gateway** e un load balancer Layer 7 (HTTP/HTTPS) con funzionalita avanzate:

- **URL-based routing**: instradamento del traffico basato sul path dell'URL (ad esempio, `/images/*` verso un backend, `/api/*` verso un altro).
- **Multi-site hosting**: hosting di piu siti web dietro un singolo Application Gateway, con routing basato sull'header `Host`.
- **SSL/TLS termination**: decifra il traffico HTTPS al gateway, riducendo il carico sui backend.
- **Session affinity**: cookie-based session affinity per applicazioni stateful.
- **Autoscaling**: scalabilita automatica basata sul carico di traffico.

Il **Web Application Firewall (WAF)** protegge da exploit comuni come SQL injection, XSS e altre vulnerabilita OWASP Top 10. Opera in modalita Detection (logging) o Prevention (blocco attivo).

### Azure Load Balancer Standard

**Azure Load Balancer** opera a Layer 4 (TCP/UDP) distribuendo il traffico tra le istanze di backend. Lo SKU **Standard** offre:

- **Availability Zones support**: distribuzione zone-redundant o zonal.
- **Health probes**: TCP, HTTP e HTTPS per verificare lo stato dei backend.
- **HA Ports**: bilanciamento di tutto il traffico su tutte le porte in un'unica regola (utile per appliance di rete virtuali — NVA).
- **Outbound rules**: controllo granulare del traffico in uscita e SNAT.
- **Backend pools**: fino a 1000 istanze per pool.
- **Secure by default**: il traffico e bloccato a meno che non sia esplicitamente consentito da un NSG.

Lo Standard Load Balancer puo essere **Public** (con IP pubblico, per il traffico Internet-facing) o **Internal** (con IP privato, per il traffico tra tier applicativi).

### VNet Peering

Il **VNet Peering** connette due VNet tramite la rete backbone di Microsoft, senza gateway o Internet pubblico. Due tipi:

- **Regional VNet Peering**: tra VNet nella stessa regione.
- **Global VNet Peering**: tra VNet in regioni diverse.

Il peering e non transitivo: se la VNet A e in peering con B, e B con C, A non puo comunicare con C a meno che non venga creato un peering diretto A-C o si utilizzi un'architettura hub-and-spoke con routing tramite una NVA o Azure Firewall nella VNet hub.

### VPN Gateway

**Azure VPN Gateway** consente la connettivita crittografata tra la rete Azure e altre reti:

- **Site-to-Site (S2S)**: connessione IPsec/IKE tra la rete on-premises e la VNet Azure tramite un tunnel VPN su Internet. Richiede un dispositivo VPN on-premises compatibile.
- **Point-to-Site (P2S)**: connessione VPN da un singolo client (laptop, workstation) alla VNet Azure. Supporta protocolli OpenVPN, SSTP e IKEv2.
- **VNet-to-VNet**: connessione crittografata tra due VNet Azure tramite gateway VPN.

I gateway VPN sono disponibili in diversi SKU che determinano throughput, numero di tunnel e supporto per la configurazione active-active.

### ExpressRoute

**Azure ExpressRoute** fornisce connessioni private dedicate tra on-premises e Azure, senza Internet pubblico:

- **Banda garantita**: da 50 Mbps a 10 Gbps (fino a 100 Gbps con ExpressRoute Direct).
- **Latenza prevedibile**: percorso di rete dedicato e deterministic.
- **Alta affidabilita**: connessioni ridondanti presso ogni punto di peering.
- **Peering privato**: accesso alle risorse nella VNet.
- **Microsoft peering**: accesso ai servizi Microsoft 365 e Azure PaaS.

ExpressRoute e raccomandato per workload critici che richiedono prestazioni di rete prevedibili tra on-premises e cloud.

### Private Endpoint e Private Link

**Azure Private Link** consente di accedere ai servizi PaaS (Storage, SQL Database, Cosmos DB, Key Vault) tramite un **Private Endpoint** — un'interfaccia di rete con IP privato nella VNet. Il traffico resta sulla rete backbone di Microsoft.

Vantaggi principali:

- **Eliminazione dell'esposizione pubblica**: il servizio PaaS non necessita di un endpoint pubblico.
- **Protezione dall'esfiltrazione dei dati**: il traffico resta confinato alla rete privata.
- **Accesso da reti on-premises**: tramite VPN o ExpressRoute, le reti on-premises possono raggiungere i servizi PaaS attraverso il Private Endpoint.

### Azure DNS

**Azure DNS** consente di ospitare domini DNS su infrastruttura globale anycast. Supporta **Public DNS zones** (risoluzione pubblica) e **Private DNS zones** (risoluzione interna alla VNet, fondamentale per Private Endpoints). Offre registrazione automatica dei record per le VM nella VNet.

### Azure Front Door

**Azure Front Door** e il servizio globale di bilanciamento del carico e accelerazione delle applicazioni di Azure. Opera su oltre 210 edge location distribuite a livello mondiale, combinando le funzionalita di un CDN, di un load balancer globale Layer 7 e di un WAF in un'unica piattaforma gestita. A differenza dell'Application Gateway (regionale), Front Door opera a livello globale e instrada il traffico verso il backend piu performante in base alla latenza misurata in tempo reale.

**Funzionalita principali**:

- **Bilanciamento globale basato su latenza**: Front Door misura continuamente la latenza verso ciascun backend e instrada ogni richiesta al backend con la latenza piu bassa. Questo garantisce tempi di risposta ottimali indipendentemente dalla posizione geografica dell'utente.
- **Accelerazione del contenuto**: tramite split TCP, compressione edge e caching intelligente, Front Door accelera sia il contenuto statico (immagini, CSS, JavaScript) sia il contenuto dinamico (API, pagine generate server-side).
- **Failover automatico**: i health probes monitorano continuamente lo stato di salute dei backend. In caso di guasto di un backend in una regione, il traffico viene reindirizzato automaticamente al backend disponibile piu vicino, con failover completato in pochi secondi.
- **URL-based routing e session affinity**: instradamento del traffico basato su path URL, header HTTP e cookie di sessione. Supporta regole di routing complesse per architetture microservizi.
- **WAF integrato**: il Web Application Firewall di Front Door protegge dalle vulnerabilita OWASP Top 10 (SQL injection, XSS, CSRF), con ruleset gestiti da Microsoft e regole personalizzabili. Supporta rate limiting, geo-filtering e bot protection.
- **Private Link**: Front Door Premium supporta l'origine tramite Azure Private Link, consentendo di mantenere i backend completamente privati (senza IP pubblico) pur servendo il traffico globalmente tramite la rete edge di Microsoft.
- **Certificati TLS gestiti**: gestione automatica dei certificati TLS/SSL con rinnovo automatico, eliminando la complessita operativa della gestione dei certificati.

**Tier disponibili**:

| Tier | Caratteristiche |
|------|----------------|
| **Standard** | CDN, routing basato su latenza, caching, compressione, WAF con ruleset gestiti |
| **Premium** | Tutte le funzionalita Standard + Private Link origins, enhanced WAF con bot protection avanzata, reportistica di sicurezza estesa |

Front Door e la scelta raccomandata per applicazioni web distribuite globalmente che richiedono bassa latenza, alta disponibilita e protezione DDoS/WAF integrata. Per scenari puramente regionali, l'Application Gateway rimane la scelta appropriata.

### Network Watcher

**Network Watcher** e la suite di strumenti diagnostici e di monitoraggio per le reti Azure:

- **IP flow verify**: verifica se un pacchetto e consentito o negato da/verso una VM.
- **Next hop**: determina il prossimo hop per il traffico da una VM.
- **NSG diagnostics**: analizza le regole NSG applicate e identifica quali regole consentono o bloccano il traffico.
- **Connection troubleshoot**: testa la connettivita TCP tra due endpoint.
- **Packet capture**: cattura del traffico di rete sulle VM.
- **NSG flow logs**: registra il traffico consentito e negato dagli NSG, analizzabile con Traffic Analytics.
- **Connection monitor**: monitoraggio continuo della connettivita tra endpoint.

---

## 4. Compute

### Virtual Machines — Dimensioni e Famiglie

Le **Azure Virtual Machines** sono il servizio IaaS fondamentale. Le dimensioni sono organizzate in famiglie ottimizzate per workload specifici:

| Famiglia | Serie | Uso |
|----------|-------|-----|
| **General Purpose** | B, D, Dv2-v5, DC | Workload bilanciati, sviluppo/test, piccoli database, web server |
| **Compute Optimized** | F, Fx | Workload CPU-intensive: batch processing, gaming server, modellazione |
| **Memory Optimized** | E, Ev3-v5, M, Mv2 | Database relazionali in-memory, cache, analytics in-memory (SAP HANA con serie M) |
| **Storage Optimized** | L, Ls | Big data, database SQL/NoSQL, data warehousing. Throughput disco elevato |
| **GPU** | NC, ND, NV | Machine learning, rendering grafico, transcoding video. GPU NVIDIA |
| **HPC** | H, HB, HC | High Performance Computing, simulazioni, modellazione meteo, fluidodinamica |

La serie **B** (burstable) e particolarmente conveniente per workload con utilizzo CPU variabile: le VM accumulano crediti durante i periodi di basso utilizzo e li spendono durante i picchi.

La nomenclatura segue il pattern: `Standard_D4s_v5` dove `D` e la famiglia, `4` il numero di vCPU, `s` indica il supporto per Premium SSD, e `v5` la generazione.

### Availability Sets

Un **Availability Set** distribuisce le VM su **Fault Domains** (FD) e **Update Domains** (UD) all'interno di un singolo data center:

- **Fault Domains** (max 3): gruppi di VM che condividono una sorgente di alimentazione e uno switch di rete comuni. Distribuire le VM su piu FD protegge da guasti hardware.
- **Update Domains** (max 20): gruppi di VM che vengono riavviate simultaneamente durante gli aggiornamenti della piattaforma. Distribuire le VM su piu UD garantisce che non tutte vengano riavviate contemporaneamente.

Gli Availability Set offrono uno SLA del 99.95%. Per una resilienza superiore, le Availability Zones (SLA 99.99%) sono la scelta raccomandata.

### Virtual Machine Scale Sets (VMSS)

I **VMSS** consentono di creare e gestire un gruppo di VM identiche con bilanciamento del carico automatico. Le caratteristiche principali sono:

- **Autoscaling**: scalabilita automatica basata su metriche (CPU, memoria, metriche custom) o schedulazione.
- **Distribuzione su Availability Zones**: le istanze possono essere distribuite automaticamente su piu zone.
- **Rolling upgrades**: aggiornamento progressivo delle istanze senza downtime.
- **Overprovisioning**: creazione di istanze aggiuntive durante lo scale-out per garantire che il numero richiesto sia raggiunto rapidamente.
- **Orchestration modes**: Uniform (tutte le VM identiche, il modello tradizionale) e Flexible (consente di aggiungere VM con configurazioni diverse).

### Azure Bastion

**Azure Bastion** fornisce accesso RDP e SSH sicuro alle VM tramite browser, senza IP pubblici. Viene distribuito in una subnet dedicata (`AzureBastionSubnet`) e funge da jump box gestito, eliminando le porte RDP/SSH dall'esposizione a Internet.

### Proximity Placement Groups

I **Proximity Placement Groups** garantiscono che le risorse vengano distribuite in stretta prossimita fisica nel data center, riducendo la latenza inter-VM a microsecondi. Essenziali per SAP HANA, database distribuiti e HPC.

### Spot VMs

Le **Azure Spot VMs** utilizzano capacita inutilizzata con sconti fino al 90%. Azure puo reclamare le istanze con preavviso di 30 secondi. Le policy di eviction sono:

- **Stop/Deallocate**: la VM viene fermata e deallocata, ma puo essere riavviata successivamente.
- **Delete**: la VM viene eliminata definitivamente.

Le Spot VM sono ideali per workload fault-tolerant: batch processing, rendering, CI/CD pipeline, data analytics, ambienti di test.

### Azure Functions (Cenni)

**Azure Functions** e il servizio di compute serverless di Azure. Consente di eseguire codice in risposta a eventi senza gestire l'infrastruttura sottostante. I piani di hosting includono:

- **Consumption Plan**: pagamento solo per il tempo di esecuzione e le risorse consumate. Scalabilita automatica a zero. Cold start possibile.
- **Premium Plan**: istanze pre-warmed per eliminare i cold start, con connettivita VNet e capacita superiore.
- **Dedicated (App Service) Plan**: esecuzione su VM dedicate, utile per workload con esecuzione continua.

I trigger supportati includono HTTP, Timer, Blob Storage, Queue Storage, Event Hub, Service Bus, Cosmos DB e molti altri. Le bindings semplificano l'integrazione con altri servizi Azure senza codice boilerplate per connessioni e SDK.

**Durable Functions**:

Le **Durable Functions** estendono Azure Functions con la capacita di gestire workflow stateful e orchestrazioni complesse. Utilizzano un framework di programmazione basato su pattern ben definiti:

- **Function Chaining**: esecuzione sequenziale di funzioni in cui l'output di una diventa l'input della successiva. Il framework gestisce automaticamente i checkpoint e il replay in caso di errore.
- **Fan-out / Fan-in**: esecuzione parallela di piu funzioni e aggregazione dei risultati. Ideale per batch processing dove ogni elemento puo essere elaborato indipendentemente.
- **Async HTTP APIs**: implementazione di operazioni long-running con polling endpoint automatici. Il client riceve un URL di status per verificare il completamento dell'operazione.
- **Monitor Pattern**: polling ricorrente di una condizione esterna con intervalli configurabili e timeout.
- **Human Interaction**: workflow che attendono un'approvazione umana (tramite webhook, email con link di approvazione) con timeout configurabile.

Lo stato dell'orchestrazione viene persistito automaticamente in Azure Storage (Table Storage e Queue Storage), garantendo la durabilita anche in caso di riavvio dell'istanza. I linguaggi supportati includono C#, JavaScript/TypeScript, Python, Java e PowerShell.

**Flex Consumption Plan**: il piano **Flex Consumption** (disponibile dalla fine del 2024) combina le caratteristiche migliori dei piani Consumption e Premium — scaling a zero con istanze pre-warmed on-demand, concurrency configurabile per istanza, supporto VNet nativo e private endpoint. Rappresenta la scelta raccomandata per nuovi progetti serverless che richiedono sia l'efficienza di costo dello scaling a zero sia le prestazioni di cold start ridotte.

### Azure Container Apps

**Azure Container Apps** e la piattaforma serverless completamente gestita per l'esecuzione di applicazioni containerizzate. A differenza di AKS (che richiede la gestione dei cluster Kubernetes), Container Apps astrae completamente l'infrastruttura sottostante, consentendo agli sviluppatori di concentrarsi esclusivamente sul codice applicativo. Il servizio e costruito su Kubernetes, ma non espone l'API Kubernetes agli utenti.

**Caratteristiche architetturali**:

- **Scaling automatico event-driven**: Container Apps utilizza KEDA (Kubernetes Event-Driven Autoscaling) per scalare i container in base a eventi provenienti da molteplici sorgenti — richieste HTTP concorrenti, messaggi in coda (Service Bus, Event Hub, Storage Queue), metriche CPU/memoria, e trigger personalizzati. Il scaling include la capacita di scalare a zero, eliminando i costi quando non ci sono richieste da processare.
- **Revisioni e traffic splitting**: ogni modifica alla configurazione o all'immagine container genera una nuova revisione. Il traffico puo essere suddiviso tra revisioni attive con percentuali configurabili, abilitando pattern di deployment come blue-green, canary e A/B testing senza strumenti esterni.
- **Dapr integration nativa**: il runtime Distributed Application Runtime (Dapr) e integrato nativamente, fornendo building blocks per service invocation, state management, pub/sub messaging, bindings e observability. L'attivazione di Dapr richiede una singola flag nella configurazione del container.
- **Ambienti (Container Apps Environment)**: le applicazioni vengono distribuite all'interno di un Container Apps Environment, che rappresenta un confine di sicurezza e di rete. Un ambiente puo ospitare piu applicazioni che condividono la stessa VNet, le stesse policy di logging e la stessa configurazione Dapr.
- **Managed Identity e Secret management**: supporto nativo per system-assigned e user-assigned managed identities. I secret possono essere referenziati da Azure Key Vault direttamente nella configurazione dell'app.

**Piani di hosting**:

| Piano | Caratteristiche |
|-------|----------------|
| **Consumption** | Pagamento per le risorse effettivamente consumate, scaling a zero, SLA 99.95% |
| **Dedicated** | Hardware dedicato per workload con requisiti di isolamento, prestazioni prevedibili |
| **Consumption + GPU** | Accesso a GPU serverless (NVIDIA A100, T4) con fatturazione al secondo, per workload AI/ML |

**Container Apps Jobs**: oltre alle applicazioni con esecuzione continua, Container Apps supporta i **Jobs** — container che eseguono un task e terminano. I Job possono essere attivati manualmente, tramite schedulazione (cron) o in risposta a eventi. Sono ideali per batch processing, ETL, data migration e task di manutenzione.

**Ingress e networking**: Container Apps supporta ingress HTTP/HTTPS automatico con terminazione TLS, custom domains e routing basato su regole. L'integrazione VNet consente di esporre le applicazioni solo internamente o di connetterle a risorse private nella rete virtuale. Il supporto per Private Endpoints garantisce che il traffico non transiti sulla rete pubblica.

Container Apps e la scelta raccomandata per team che desiderano i benefici dei container senza la complessita operativa di Kubernetes. Per workload che richiedono accesso diretto all'API Kubernetes, personalizzazione del control plane o operatori custom, AKS rimane la scelta appropriata.

---

## 5. Storage

### Storage Account

Lo **Storage Account** fornisce un namespace unico per i dati Azure Storage (ad esempio, `https://myaccount.blob.core.windows.net`). I tipi sono:

| Tipo | Servizi supportati | Uso |
|------|-------------------|-----|
| **Standard general-purpose v2** | Blob, File, Queue, Table | La scelta raccomandata per la maggior parte degli scenari |
| **Premium block blobs** | Solo Blob (block blobs) | Bassa latenza, alto throughput per blob di piccole dimensioni |
| **Premium file shares** | Solo Azure Files | File share ad alte prestazioni (supporto SMB e NFS) |
| **Premium page blobs** | Solo Blob (page blobs) | Dischi non gestiti (scenario legacy) |

La performance tier **Standard** utilizza dischi HDD, mentre la tier **Premium** utilizza SSD per latenze nell'ordine dei millisecondi singoli.

### Blob Storage — Tiers Hot, Cool, Archive

**Azure Blob Storage** archivia oggetti non strutturati (documenti, immagini, video, backup, log) organizzati in **containers**. I tre access tiers principali ottimizzano il rapporto costo/prestazioni:

- **Hot**: per dati ad accesso frequente. Costi di storage piu alti, costi di accesso piu bassi. E il tier predefinito.
- **Cool**: per dati ad accesso infrequente, conservati per almeno 30 giorni. Costi di storage inferiori al Hot (circa 50% in meno), costi di accesso superiori. Ideale per backup a breve termine e dati di staging.
- **Archive**: per dati raramente acceduti, conservati per almeno 180 giorni. Costo di storage estremamente basso (ordine di centesimi per GB/mese), ma il recupero dei dati richiede un'operazione di **rehydration** che puo impiegare ore (Standard: fino a 15 ore, High Priority: sotto un'ora). Non accessibile online direttamente.

Esiste anche il tier **Cold** (introdotto come intermedio tra Cool e Archive), per dati acceduti raramente e conservati per almeno 90 giorni, con costi di storage inferiori a Cool ma costi di accesso superiori.

### Azure Files — SMB e NFS

**Azure Files** offre file share completamente gestite accessibili tramite i protocolli standard:

- **SMB (Server Message Block)**: protocollo standard per Windows, supportato anche da Linux e macOS. Supporta SMB 3.0 con crittografia in transito. Ideale per lift-and-shift di applicazioni che utilizzano file share.
- **NFS (Network File System)**: supportato nelle file share Premium. Utilizzato tipicamente da workload Linux. Richiede connettivita tramite VNet (Private Endpoint o Service Endpoint).

Azure Files supporta l'autenticazione Active Directory (on-premises o Entra Domain Services) per l'autorizzazione a livello di file. **Azure File Sync** sincronizza le file share con i file server Windows on-premises, abilitando il tiering dei dati nel cloud.

### Azure Disk — Tipi

**Azure Managed Disks** sono i dischi a blocchi utilizzati dalle VM. I tipi disponibili sono:

| Tipo | IOPS max | Throughput max | Uso |
|------|----------|----------------|-----|
| **Ultra Disk** | 160.000 | 4.000 MB/s | Database mission-critical (SAP HANA, SQL Server), workload transaction-intensive |
| **Premium SSD v2** | 80.000 | 1.200 MB/s | Workload production con IOPS e throughput configurabili indipendentemente |
| **Premium SSD** | 20.000 | 900 MB/s | Workload production, database |
| **Standard SSD** | 6.000 | 750 MB/s | Web server, ambienti di sviluppo/test |
| **Standard HDD** | 2.000 | 500 MB/s | Backup, archiviazione, workload non critici |

I Managed Disks (da 4 GiB a 64 TiB) includono gestione automatica di ridondanza e snapshot. La crittografia at-rest avviene tramite SSE con chiavi Microsoft (PMK) o chiavi del cliente (CMK) tramite Key Vault.

### Lifecycle Management

Le **Lifecycle Management Policies** automatizzano la transizione dei blob tra i tiers e la loro eliminazione. Si definiscono regole basate su:

- **Ultima modifica** (lastModified): ad esempio, spostare i blob da Hot a Cool dopo 30 giorni, da Cool ad Archive dopo 90 giorni, eliminare dopo 365 giorni.
- **Ultimo accesso** (lastAccessTime): richiede l'abilitazione del last access time tracking.
- **Filtri**: si possono applicare regole solo a specifici container o prefissi di blob.

Esempio di policy:

```json
{
  "rules": [
    {
      "name": "archiveOldBlobs",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["logs/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": { "daysAfterModificationGreaterThan": 30 },
            "tierToArchive": { "daysAfterModificationGreaterThan": 90 },
            "delete": { "daysAfterModificationGreaterThan": 365 }
          }
        }
      }
    }
  ]
}
```

### Replicazione — LRS, ZRS, GRS

Azure Storage offre diverse opzioni di ridondanza:

- **LRS (Locally Redundant Storage)**: tre copie all'interno di un singolo data center nella regione primaria. Protegge da guasti hardware di singoli componenti. SLA 99.9%. L'opzione meno costosa.
- **ZRS (Zone-Redundant Storage)**: tre copie distribuite su tre Availability Zones nella regione primaria. Protegge dal fallimento di un'intera zona. SLA 99.9%. Raccomandata per applicazioni ad alta disponibilita.
- **GRS (Geo-Redundant Storage)**: LRS nella regione primaria + LRS nella regione secondaria accoppiata (sei copie totali). Protegge da disastri regionali. SLA 99.9% (99.99% con RA-GRS). I dati nella regione secondaria sono accessibili in lettura solo con **RA-GRS** (Read-Access GRS).
- **GZRS (Geo-Zone-Redundant Storage)**: ZRS nella regione primaria + LRS nella regione secondaria. Combina la protezione zonale con quella geografica. L'opzione piu resiliente.

### AzCopy e Storage Explorer

**AzCopy** e lo strumento CLI per copiare dati da/verso Azure Storage con alte prestazioni. Supporta autenticazione Entra ID o SAS, sincronizzazione bidirezionale e trasferimento tra storage account. Esempio:

```bash
azcopy copy '/local/path/*' 'https://myaccount.blob.core.windows.net/mycontainer?sv=...' --recursive
```

**Azure Storage Explorer** e un'applicazione desktop (Windows, macOS, Linux) per la gestione visuale dei dati in Blob, File, Queue e Table Storage.

### Azure Data Lake Storage Gen2 (ADLS Gen2)

**Azure Data Lake Storage Gen2** e la soluzione di data lake di Azure, costruita sopra Azure Blob Storage con l'abilitazione del **Hierarchical Namespace (HNS)**. L'HNS trasforma lo storage a oggetti piatto in un vero file system gerarchico con directory reali, operazioni atomiche sulle directory (rinomina, spostamento, eliminazione ricorsiva in O(1)) e Access Control List (ACL) POSIX-compatible. Questa architettura combina la scalabilita e il costo dello storage a oggetti con le prestazioni e la semantica di un file system, rendendola ideale per i workload di big data analytics.

**Architettura e integrazione**:

ADLS Gen2 non e un servizio separato: e un Azure Storage Account con l'opzione HNS abilitata al momento della creazione. Questo significa che eredita tutte le funzionalita dello Storage Account standard — ridondanza (LRS, ZRS, GRS, GZRS), lifecycle management, crittografia at-rest, firewall e VNet integration, Private Endpoints — con l'aggiunta delle capacita analitiche del file system gerarchico.

L'integrazione con l'ecosistema analytics di Azure e nativa:

- **Azure Synapse Analytics**: accesso diretto ai dati nel data lake tramite Synapse SQL serverless pool e Spark pool.
- **Azure Databricks**: mount diretto del data lake come file system DBFS con autenticazione tramite Entra ID (passthrough) o service principal.
- **Azure HDInsight**: supporto nativo per Hadoop, Spark, Hive e altri framework big data.
- **Microsoft Fabric**: il data lake funge da storage layer per i lakehouse di Fabric.
- **Azure Data Factory / Synapse Pipelines**: orchestrazione dei flussi ETL/ELT con connettori nativi per ADLS Gen2.

**Modello di sicurezza a due livelli**:

ADLS Gen2 implementa un modello di sicurezza a due livelli che combina RBAC e ACL:

1. **RBAC (Role-Based Access Control)**: controlla l'accesso a livello di storage account, container o directory tramite ruoli come `Storage Blob Data Contributor`, `Storage Blob Data Reader` e `Storage Blob Data Owner`. Le assegnazioni RBAC si applicano a tutti i file e le directory nello scope definito.
2. **ACL POSIX**: controllo granulare a livello di singolo file o directory, con permessi `rwx` (read, write, execute) assegnabili a utenti, gruppi e altri. Le **Access ACL** definiscono i permessi di accesso, mentre le **Default ACL** vengono ereditate automaticamente dai nuovi file e directory creati all'interno della directory padre.

La best practice consiste nell'utilizzare RBAC per l'accesso a livello di container (ad esempio, il team Data Engineering ha accesso Contributor al container `raw`) e le ACL per il controllo granulare all'interno del container.

**Struttura raccomandata del data lake — Medallion Architecture**:

La struttura a tre livelli (Bronze, Silver, Gold) e il pattern architetturale raccomandato:

```
data-lake-container/
├── bronze/          # Dati grezzi, ingestione as-is (JSON, CSV, Parquet, Avro)
│   ├── erp/
│   ├── crm/
│   └── iot-sensors/
├── silver/          # Dati puliti, deduplicati, tipizzati (Parquet, Delta Lake)
│   ├── customers/
│   ├── orders/
│   └── telemetry/
├── gold/            # Dati aggregati e pronti per il business (Delta Lake, Parquet)
│   ├── sales-summary/
│   ├── kpi-dashboard/
│   └── ml-features/
└── sandbox/         # Area esplorativa per data scientist
```

**Best practices per le prestazioni**:

- Utilizzare formati colonnari (Apache Parquet, ORC, Delta Lake) per le query analitiche.
- Dimensione file ottimale tra 100 MB e 1 GB per bilanciare il parallelismo e l'overhead di apertura file.
- Partizionare i dati per data (`year=2025/month=05/day=24/`) per le query con filtri temporali.
- Evitare file molto piccoli (< 1 MB) che degradano le prestazioni dei framework Spark e Hive.
- Abilitare il last access time tracking per le lifecycle management policies che spostano i dati infrequentemente acceduti verso tier piu economici.

---

## 6. Database

### Azure SQL Database

**Azure SQL Database** e un database relazionale completamente gestito basato sull'engine di Microsoft SQL Server. Modelli di acquisto:

- **DTU-based**: unita predefinite che combinano CPU, I/O e memoria in tier (Basic, Standard, Premium). Semplice da dimensionare per workload prevedibili.
- **vCore-based**: consente di selezionare indipendentemente il numero di vCPU, la memoria e lo storage. Offre piu flessibilita e trasparenza. Include i tier General Purpose (SSD), Business Critical (SSD locale con replica locale per bassa latenza) e Hyperscale (scalabilita fino a 100 TB, snapshot istantanee).

Le opzioni di distribuzione includono:

- **Single Database**: database isolato con risorse dedicate.
- **Elastic Pool**: un pool di risorse (eDTU o vCore) condiviso da piu database. Ideale quando i database hanno pattern di utilizzo variabili e complementari, consentendo di ottimizzare i costi.

Azure SQL Database supporta nativamente: backup automatici con retention fino a 35 giorni (piu long-term retention fino a 10 anni), geo-replication attiva (fino a 4 repliche in lettura in regioni diverse), auto-failover groups, Transparent Data Encryption (TDE), Always Encrypted e auditing.

### Azure SQL Managed Instance

**Azure SQL Managed Instance** offre quasi il 100% di compatibilita con SQL Server on-premises Enterprise. A differenza di SQL Database, supporta:

- Cross-database queries e distributed transactions.
- SQL Server Agent per job scheduling.
- CLR integration (.NET nel database).
- Service Broker per la messaggistica asincrona.
- Linked Servers per la connessione ad altri database.

Managed Instance viene distribuita in una VNet dedicata con isolamento di rete nativo. Ideale per il lift-and-shift di database SQL Server on-premises che utilizzano funzionalita a livello di istanza.

### Cosmos DB

**Azure Cosmos DB** e un database distribuito globalmente, progettato per latenze sotto i 10 ms al 99° percentile, scalabilita orizzontale elastica e disponibilita del 99.999%:

- **Distribuzione globale turnkey**: replicazione dei dati in qualsiasi numero di regioni Azure con un click, con multi-region writes.
- **Multi-model APIs**: SQL (Core), MongoDB, Cassandra, Gremlin (graph) e Table. Ogni API consente di interagire con Cosmos DB utilizzando il protocollo nativo del rispettivo database.
- **Modelli di consistenza**: cinque livelli configurabili — Strong, Bounded Staleness, Session (default, il piu utilizzato), Consistent Prefix, Eventual. Questo consente di bilanciare consistenza, disponibilita e latenza in base alle esigenze dell'applicazione.
- **Throughput**: misurato in **Request Units (RU/s)**, una misura normalizzata di CPU, I/O e memoria. Puo essere provisioned (fisso) o autoscale (si adatta automaticamente tra il 10% e il 100% del valore massimo configurato). La modalita **serverless** e disponibile per workload con traffico intermittente.

Cosmos DB e ideale per gaming, IoT, real-time personalization, cataloghi prodotti e social feed.

### Azure Database for PostgreSQL e MySQL

Azure offre servizi database gestiti per i motori open-source piu diffusi:

**Azure Database for PostgreSQL — Flexible Server** e la modalita di distribuzione raccomandata. Offre:

- Controllo granulare sulla configurazione del server (parametri del database, finestre di manutenzione, zona di disponibilita).
- High availability con failover automatico (same-zone o zone-redundant).
- Scalabilita del compute e dello storage indipendenti.
- Intelligent performance: query store, intelligent tuning, slow query insights.
- Supporto per le principali estensioni PostgreSQL (PostGIS, pg_partman, pgvector per ricerche vettoriali AI).

**Azure Database for MySQL — Flexible Server** offre funzionalita analoghe per il motore MySQL. Entrambi supportano le major versions recenti, backup automatici, crittografia at-rest e in-transit, e integrazione con Private Link per l'accesso dalla VNet.

---

## 7. Containers — ACI, AKS, ACR

### Azure Container Instances (ACI)

**ACI** e il modo piu rapido per eseguire un container in Azure senza gestire server o orchestratori. Le caratteristiche principali sono:

- **Avvio rapido**: i container vengono avviati in pochi secondi.
- **Fatturazione al secondo**: si paga solo per le risorse CPU e memoria effettivamente consumate.
- **Container groups**: piu container possono essere raggruppati in un "pod" che condivide rete, storage e ciclo di vita (simile ai Pod di Kubernetes).
- **Integrazione VNet**: i container groups possono essere distribuiti all'interno di una subnet della VNet per l'isolamento di rete.
- **Persistent storage**: supporto per il mount di Azure Files.

ACI e ideale per task a breve durata (batch jobs, build agents), ambienti di test, e come burst target per AKS tramite il **Virtual Kubelet** (ACI virtual node).

### Azure Kubernetes Service (AKS) — Architettura e Deployment

**AKS** e il servizio gestito di orchestrazione Kubernetes. Azure gestisce il control plane (API Server, etcd, scheduler, controller manager) gratuitamente; l'utente paga solo per i nodi worker.

**Architettura AKS**:

```
┌─────────────────────────────────────────────────┐
│ AKS Cluster                                      │
│                                                   │
│ ┌─────────────────────────────────────────────┐  │
│ │ Control Plane (gestito da Azure)             │  │
│ │ API Server · etcd · Scheduler · Controllers  │  │
│ └─────────────────────────────────────────────┘  │
│                                                   │
│ ┌─────────────────────────────────────────────┐  │
│ │ Node Pools (gestiti dall'utente)              │  │
│ │                                               │  │
│ │  System Node Pool        User Node Pool       │  │
│ │  ┌──────┐ ┌──────┐     ┌──────┐ ┌──────┐    │  │
│ │  │Node 1│ │Node 2│     │Node 1│ │Node 2│    │  │
│ │  │CoreDNS│ │Kube  │     │App   │ │App   │    │  │
│ │  │Proxy  │ │Proxy │     │Pods  │ │Pods  │    │  │
│ │  └──────┘ └──────┘     └──────┘ └──────┘    │  │
│ └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Componenti e funzionalita chiave**:

- **Node Pools**: gruppi di nodi con la stessa configurazione VM. Il **System Node Pool** esegue i pod di sistema (CoreDNS, kube-proxy, metrics-server); gli **User Node Pools** eseguono i workload applicativi. Ogni pool puo utilizzare dimensioni VM diverse e abilitare l'autoscaling indipendentemente.
- **Cluster Autoscaler**: scala automaticamente il numero di nodi in base alla domanda di risorse dei pod.
- **Azure CNI networking**: assegna IP della VNet direttamente ai pod, consentendo la comunicazione nativa con altre risorse Azure nella VNet. L'alternativa **kubenet** utilizza una rete overlay con NAT.
- **Ingress Controller**: tipicamente NGINX Ingress Controller o Application Gateway Ingress Controller (AGIC) per esporre i servizi HTTP/HTTPS.
- **Managed Identity**: il cluster utilizza una managed identity per interagire con le risorse Azure (ACR, Load Balancer, dischi).
- **Azure Policy for AKS**: applica policy di governance ai cluster (ad esempio, impedire container con privilegi root, forzare limiti di risorse).

Deployment di un cluster AKS con Azure CLI:

```bash
az aks create \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v5 \
  --network-plugin azure \
  --enable-managed-identity \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10 \
  --zones 1 2 3 \
  --generate-ssh-keys

az aks get-credentials --resource-group myResourceGroup --name myAKSCluster
kubectl get nodes
```

### Azure Container Registry (ACR)

**ACR** e il registry privato per le immagini container. I tier disponibili sono:

- **Basic**: per scenari di sviluppo e test con volume ridotto.
- **Standard**: throughput e storage maggiori per la maggior parte degli scenari di produzione.
- **Premium**: geo-replication (replica del registry in piu regioni per bassa latenza e resilienza), Private Link, content trust (firma delle immagini), customer-managed keys.

ACR si integra nativamente con AKS: il cluster puo effettuare il pull delle immagini tramite managed identity senza gestire credenziali. ACR Tasks consente di automatizzare la build, il test e il push delle immagini container direttamente nel cloud, attivati da commit sul codice sorgente o aggiornamento dell'immagine base.

---

## 8. Monitoring e Observability

### Azure Monitor

**Azure Monitor** e la piattaforma centrale di monitoraggio. Raccoglie e analizza dati da ogni livello dello stack. I dati si classificano in:

- **Metrics**: valori numerici time-series (CPU, memoria, richieste al secondo, latenza). Vengono archiviati nel Metrics Store con retention di 93 giorni. Supportano query in near real-time e sono la base per autoscaling e alerting.
- **Logs**: record strutturati e non strutturati (log di attivita, log diagnostici, log applicativi). Vengono inviati a un **Log Analytics Workspace** dove possono essere interrogati con KQL.

### Log Analytics e Query KQL

**Log Analytics** e il motore di analisi dei log di Azure Monitor. I dati vengono archiviati in un **Log Analytics Workspace** e interrogati tramite **KQL (Kusto Query Language)**. KQL e un linguaggio di query potente e ottimizzato per l'analisi di grandi volumi di dati.

Esempi di query KQL:

```kql
// Errori HTTP 5xx negli ultimi 24 ore, raggruppati per URL
AppRequests
| where TimeGenerated > ago(24h)
| where ResultCode startswith "5"
| summarize ErrorCount = count() by Url
| order by ErrorCount desc
| take 20

// Percentile 95 del tempo di risposta per operazione
AppRequests
| where TimeGenerated > ago(1h)
| summarize P95_Duration = percentile(DurationMs, 95) by OperationName
| order by P95_Duration desc

// Rilevamento anomalie nell'utilizzo CPU delle VM
Perf
| where ObjectName == "Processor" and CounterName == "% Processor Time"
| where TimeGenerated > ago(7d)
| summarize AvgCPU = avg(CounterValue) by bin(TimeGenerated, 1h), Computer
| render timechart

// Pod in stato non Running in AKS
KubePodInventory
| where TimeGenerated > ago(30m)
| where PodStatus != "Running" and PodStatus != "Succeeded"
| project TimeGenerated, Namespace, Name, PodStatus, ContainerStatusReason
```

### Application Insights

**Application Insights** e il componente APM di Azure Monitor per la visibilita sulle prestazioni applicative:

- **Distributed tracing**: tracciamento end-to-end delle richieste attraverso microservizi.
- **Application Map**: visualizzazione grafica delle dipendenze tra componenti e loro stato di salute.
- **Live Metrics**: stream in tempo reale delle metriche applicative.
- **Smart Detection**: rilevamento automatico delle anomalie di prestazione.
- **Availability Tests**: test sintetici che verificano la disponibilita degli endpoint a intervalli regolari da location globali.
- **User Analytics**: session tracking, page views, user flows per comprendere il comportamento degli utenti.

L'integrazione avviene tramite SDK (.NET, Java, Python, Node.js) o auto-instrumentation.

### Alerts

Gli **Alerts** notificano proattivamente quando si verificano condizioni specifiche. I tipi principali:

- **Metric alerts**: basati su soglie di metriche (ad esempio, CPU > 90% per 5 minuti). Supportano soglie statiche e dinamiche (basate su machine learning).
- **Log alerts**: basati su query KQL che restituiscono risultati superiori a una soglia (ad esempio, piu di 10 errori 5xx in 5 minuti).
- **Activity log alerts**: basati su eventi del piano di gestione (ad esempio, VM deallocata, ruolo assegnato).

Gli alert attivano **Action Groups** per notifiche (email, SMS, push) o azioni automatiche (Azure Function, Logic App, webhook, runbook).

### Workbooks

I **Workbooks** sono report interattivi che combinano testo, query KQL, metriche e visualizzazioni. Supportano parametri interattivi, drill-down e condizionali, risultando piu flessibili dei dashboard statici del portale.

### Diagnostic Settings e Data Collection Rules

I **Diagnostic Settings** sono il meccanismo per inviare i dati di telemetria dalle risorse Azure alle destinazioni di analisi. Ogni risorsa Azure genera due categorie di dati diagnostici:

- **Platform Metrics**: metriche raccolte automaticamente dalla piattaforma (CPU, memoria, richieste, errori) con retention di 93 giorni nel Metrics Store. Non richiedono configurazione esplicita.
- **Resource Logs** (precedentemente Diagnostic Logs): log dettagliati delle operazioni interne alla risorsa (ad esempio, query eseguite su un database, richieste HTTP su un App Service, operazioni su Key Vault). Questi log **non vengono raccolti** a meno che non si configuri un Diagnostic Setting esplicito.

Le destinazioni supportate per i Diagnostic Settings sono:

| Destinazione | Uso |
|--------------|-----|
| **Log Analytics Workspace** | Analisi con KQL, correlazione tra risorse, alerting basato su log |
| **Storage Account** | Archiviazione a lungo termine, compliance, audit trail |
| **Event Hub** | Streaming verso sistemi SIEM di terze parti (Splunk, Datadog, Elastic) |
| **Partner Solution** | Integrazione diretta con soluzioni partner (Datadog, Elastic, Logz.io) |

Le **Data Collection Rules (DCR)** sono il meccanismo di nuova generazione per la raccolta dei dati dall'Azure Monitor Agent (AMA) installato sulle VM. Le DCR consentono di definire:

- Quali dati raccogliere (performance counters specifici, log del sistema operativo, log applicativi custom).
- Trasformazioni in-flight dei dati (filtraggio, proiezione, aggregazione) tramite query KQL, riducendo il volume dei dati inviati al workspace e i costi associati.
- Destinazioni multiple per lo stesso set di dati.

La configurazione centralizzata delle DCR sostituisce l'approccio precedente basato su workspace configuration, consentendo una gestione piu granulare e scalabile della raccolta dati.

**Architettura di monitoraggio enterprise raccomandata**:

```
Risorse Azure ──── Diagnostic Settings ──────┐
                                              │
VM (AMA Agent) ── Data Collection Rules ──────┤
                                              ├──▶ Log Analytics Workspace ──▶ KQL Queries
Application ────── App Insights SDK ──────────┤                              ──▶ Alerts
                                              │                              ──▶ Workbooks
Activity Log ──── Subscription Diagnostic ────┘
                                              
                  Event Hub ──────────────────────▶ SIEM Esterno (Sentinel, Splunk)
                  
                  Storage Account ────────────────▶ Archiviazione Compliance (7 anni)
```

**Costi di Log Analytics**: la fatturazione si basa sul volume di dati ingeriti (GB/giorno). I piani disponibili sono:

- **Pay-As-You-Go**: ideale per volumi inferiori a 100 GB/giorno.
- **Commitment Tiers**: sconti progressivi per volumi garantiti (100, 200, 300, 400, 500, 1000, 2000, 5000 GB/giorno), con risparmio fino al 30% rispetto al pay-as-you-go.
- **Basic Logs**: tier a costo ridotto (circa 60% in meno) per i log che devono essere conservati ma raramente interrogati. Supporta solo query KQL limitate e retention fissa di 8 giorni con archiviazione opzionale.

La strategia di ottimizzazione dei costi include: filtrare i dati non necessari con le trasformazioni DCR, utilizzare Basic Logs per i dati a bassa priorita, configurare la retention appropriata (30-730 giorni nel workspace, piu archival tier per periodi piu lunghi), e analizzare regolarmente le tabelle con il volume maggiore per identificare opportunita di riduzione.

### Azure Advisor

**Azure Advisor** analizza la configurazione e l'utilizzo delle risorse per fornire raccomandazioni nelle categorie:

- **Affidabilita (Reliability)**: raccomandazioni per migliorare la disponibilita (ad esempio, abilitare la zone-redundancy per un database).
- **Sicurezza (Security)**: integrazione con Microsoft Defender for Cloud.
- **Prestazioni (Performance)**: ottimizzazione delle dimensioni delle VM, configurazioni di caching.
- **Costi (Cost)**: identificazione di risorse sottoutilizzate, suggerimenti di Reserved Instances.
- **Eccellenza operativa (Operational Excellence)**: best practices di configurazione e gestione.

### Azure Managed Grafana

**Azure Managed Grafana** e un'istanza Grafana completamente gestita che si integra nativamente con le fonti dati Azure:

- **Integrazione nativa con Azure Monitor**: connessione diretta a Azure Monitor Metrics e Log Analytics senza configurazione manuale delle credenziali. Le dashboard Grafana possono interrogare le metriche e i log di tutte le subscription accessibili all'identita gestita dell'istanza.
- **Azure Data Explorer e Azure Managed Prometheus**: supporto nativo per le query su cluster Azure Data Explorer e per le metriche Prometheus raccolte da Azure Monitor managed service for Prometheus.
- **Autenticazione Entra ID**: l'accesso a Grafana e gestito tramite Entra ID con RBAC — Grafana Admin, Editor e Viewer corrispondono a ruoli Azure assegnabili a utenti e gruppi.
- **Alerting**: il sistema di alerting di Grafana puo essere utilizzato in aggiunta o in alternativa agli Azure Monitor Alerts, con notifiche via email, Slack, Teams, PagerDuty e webhook.

Azure Managed Grafana e la scelta raccomandata per i team che preferiscono l'ecosistema Grafana per la visualizzazione dei dati operativi, o che necessitano di dashboard che combinano dati provenienti da Azure, Prometheus e fonti dati non Azure.

### Azure Chaos Studio

**Azure Chaos Studio** e il servizio di chaos engineering di Azure che consente di iniettare guasti controllati nei workload per testare la resilienza:

- **Fault Library**: catalogo di guasti iniettabili — shutdown di VM, aumento della latenza di rete, saturazione CPU/memoria, errori DNS, disconnessione di dischi, failover di database.
- **Experiments**: un esperimento definisce la sequenza di guasti da iniettare, i target (risorse Azure specifiche), la durata e le condizioni di sicurezza (abort conditions).
- **Agent-based e Service-direct**: i guasti possono essere iniettati tramite un agent installato sulla VM (per guasti a livello di sistema operativo) o direttamente tramite l'API del servizio Azure (per guasti a livello di piattaforma come il failover di un database).
- **Integrazione CI/CD**: gli esperimenti possono essere eseguiti come step nelle pipeline CI/CD per validare automaticamente la resilienza prima del deployment in produzione.

Chaos Studio implementa il principio "test in production" in modo controllato: l'iniezione dei guasti e progressiva (blast radius inizialmente limitato) e monitorata, con condizioni di abort automatiche basate su metriche di salute del workload.

---

## 9. Security

### Microsoft Defender for Cloud

**Microsoft Defender for Cloud** (precedentemente Azure Security Center) e la piattaforma unificata CSPM e CWP:

- **Secure Score**: un punteggio numerico (0-100%) che misura la postura di sicurezza dell'organizzazione. Ogni raccomandazione non implementata riduce il punteggio. Implementare le raccomandazioni migliora lo score e la sicurezza complessiva.
- **Security Recommendations**: raccomandazioni dettagliate con guide di remediation per ogni problema rilevato (VM senza patch, storage account con accesso pubblico, database senza crittografia).
- **Defender Plans**: piani di protezione per workload specifici (Servers, SQL, Storage, Containers, Key Vault, App Service) con rilevamento minacce e vulnerability assessment.
- **Regulatory Compliance**: dashboard che misura la conformita rispetto a standard come CIS Benchmarks, PCI DSS, ISO 27001, SOC 2 e GDPR.
- **Multi-cloud**: supporta la valutazione della postura di sicurezza anche per workload su AWS e GCP.

**CSPM e CWPP — Due Livelli di Protezione**:

Defender for Cloud opera su due livelli distinti e complementari:

- **Cloud Security Posture Management (CSPM)**: analisi continua della configurazione delle risorse per identificare misconfiguration, violazioni delle best practice e non-conformita normative. Il livello **Foundational CSPM** (gratuito) fornisce il Secure Score e le raccomandazioni base. Il livello **Defender CSPM** (a pagamento) aggiunge funzionalita avanzate: attack path analysis (visualizzazione grafica dei percorsi di attacco che un avversario potrebbe sfruttare), agentless scanning per vulnerabilita delle VM e dei container, governance delle raccomandazioni con assegnazione di owner e scadenze, e risk prioritization basata sul contesto (una vulnerabilita su una VM esposta a Internet con accesso a dati sensibili ha priorita superiore rispetto alla stessa vulnerabilita su una VM isolata).
- **Cloud Workload Protection Platform (CWPP)**: protezione runtime dei workload tramite i Defender Plans specifici. Ogni piano monitora il tipo di risorsa corrispondente per attivita sospette e minacce attive. Ad esempio, Defender for Servers rileva malware, accessi anomali e lateral movement; Defender for Containers rileva immagini vulnerabili, container con privilegi eccessivi e comportamenti anomali in runtime; Defender for SQL rileva SQL injection, brute force e accessi anomali ai dati.

**Integrazione con Sentinel**: Defender for Cloud invia gli alert al workspace di Sentinel tramite il data connector dedicato. In Sentinel, gli alert vengono correlati con segnali provenienti da altre fonti (Entra ID, Office 365, firewall, endpoint) per identificare attacchi complessi multi-stage. I playbook di Sentinel possono automatizzare la risposta — ad esempio, isolando una VM compromessa dalla rete, disabilitando l'account utente coinvolto e notificando il team di incident response.

### Key Vault

**Azure Key Vault** e il servizio per la gestione centralizzata di:

- **Secrets**: stringhe di connessione, password, chiavi API, certificati PFX.
- **Keys**: chiavi crittografiche utilizzate per la crittografia dei dati (Bring Your Own Key — BYOK). Supporta chiavi protette da HSM (Hardware Security Module) con certificazione FIPS 140-2 Level 2 (Standard) o Level 3 (Premium/Managed HSM).
- **Certificates**: gestione del ciclo di vita dei certificati TLS/SSL, con rinnovo automatico tramite integrazione con Certificate Authority (DigiCert, GlobalSign).

Key Vault si integra con Managed Identities per l'accesso senza credenziali nel codice. Soft-delete e purge protection proteggono dalla cancellazione accidentale. Tutte le operazioni vengono registrate per l'audit.

### Microsoft Sentinel — SIEM

**Microsoft Sentinel** e la soluzione cloud-native SIEM (Security Information and Event Management) e SOAR (Security Orchestration, Automation and Response):

- **Data Connectors**: oltre 200 connettori per raccogliere log da fonti Azure, Microsoft 365, AWS, GCP, Cisco, Palo Alto, Fortinet e molti altri.
- **Analytics Rules**: regole di correlazione per rilevare minacce. Include regole predefinite basate sull'intelligence di Microsoft e la possibilita di creare regole custom in KQL.
- **Incidents**: gli alert correlati vengono raggruppati in incident per facilitare l'investigazione. Ogni incident ha un grafico di investigazione che visualizza le relazioni tra entita (utenti, IP, host).
- **Playbooks**: workflow di automazione basati su Logic Apps che eseguono azioni di risposta automatiche (bloccare un IP sul firewall, disabilitare un utente compromesso, aprire un ticket ITSM).
- **Threat Hunting**: query proattive di hunting in KQL per cercare indicatori di compromissione nei log prima che vengano rilevati dalle regole automatiche.
- **Workbooks**: dashboard interattivi per la visualizzazione dei dati di sicurezza.

**Architettura operativa di Sentinel**:

Sentinel utilizza un Log Analytics Workspace dedicato come data store. La best practice per le organizzazioni enterprise e utilizzare un workspace separato per Sentinel rispetto al workspace operativo (monitoraggio infrastrutturale), per garantire la separazione dei doveri tra il team SecOps e il team di operations. I dati di sicurezza hanno spesso requisiti di retention piu lunghi (1-7 anni) e policy di accesso piu restrittive.

Il modello di pricing di Sentinel si basa sul volume di dati ingeriti, con due opzioni:

- **Pay-As-You-Go**: fatturazione per GB di dati ingeriti, adatto a volumi variabili o ambienti in fase di valutazione.
- **Commitment Tiers**: tariffe ridotte per volumi garantiti giornalieri (100, 200, 300, 400, 500, 1000 GB/giorno e oltre), con risparmio progressivo fino al 50%.

**User and Entity Behavior Analytics (UEBA)**: Sentinel include UEBA, che crea profili comportamentali degli utenti e delle entita (host, IP, applicazioni) utilizzando machine learning. UEBA rileva anomalie come accessi da location insolite, orari atipici, volumi di dati trasferiti anomali e pattern di lateral movement, generando alert che sarebbero difficili da rilevare con regole basate su soglie statiche.

**Content Hub**: Sentinel Content Hub e il marketplace di soluzioni pre-confezionate che includono data connectors, analytics rules, workbooks, playbook e hunting queries per specifici scenari (Microsoft 365 Security, AWS CloudTrail, Cisco ASA, Palo Alto Networks, SAP, ServiceNow). L'installazione di una soluzione dal Content Hub configura automaticamente l'ingestione dei log, le regole di rilevamento e i dashboard per il servizio o la piattaforma selezionata.

**Automation Rules e Triage Automatico**: le Automation Rules consentono di automatizzare il triage degli incident senza la complessita dei Logic Apps. Possono assegnare automaticamente gli incident a un analista, modificare la severity basandosi su condizioni (ad esempio, elevare la severity se l'entita coinvolta e un domain admin), aggiungere tag per la categorizzazione, e chiudere automaticamente gli incident riconosciuti come falsi positivi basandosi su pattern noti.

### Azure Policy

**Azure Policy** impone regole sulle risorse Azure, valutandole come compliant o non-compliant. Gli effetti disponibili:

- **Deny**: impedisce la creazione o modifica di risorse non conformi.
- **Audit**: segnala le risorse non conformi senza bloccarle.
- **Append**: aggiunge campi alla richiesta di creazione della risorsa (ad esempio, aggiungere un tag obbligatorio).
- **Modify**: modifica i tag o le proprieta delle risorse esistenti.
- **DeployIfNotExists**: distribuisce automaticamente una risorsa correlata se non esiste (ad esempio, un agent di monitoraggio su una VM).
- **AuditIfNotExists**: segnala se una risorsa correlata non esiste.
- **Disabled**: la policy esiste ma non viene valutata.

Le **Policy Initiatives** raggruppano piu policy correlate. Azure fornisce iniziative predefinite come "CIS Benchmark" e "ISO 27001". Le policy si assegnano a Management Group, Subscription o Resource Group, con ereditarieta.

### Azure Blueprints

**Azure Blueprints** definisce un insieme ripetibile di risorse che aderisce a standard organizzativi. Un Blueprint puo includere:

- Assegnazioni di ruoli RBAC.
- Assegnazioni di Azure Policy.
- Template ARM per la distribuzione di risorse.
- Resource Groups.

I Blueprint sono versionati e supportano il locking delle risorse. Nota: Microsoft sta orientando i clienti verso **Template Specs** e **Deployment Stacks** come alternative piu moderne.

### Deployment Stacks

I **Deployment Stacks** sono il sostituto raccomandato da Microsoft per Azure Blueprints. Un Deployment Stack e una risorsa Azure che gestisce un gruppo di risorse distribuite tramite un template Bicep o ARM, aggiungendo funzionalita di governance che i deployment standard non offrono:

- **Deny Settings**: protezione delle risorse gestite dallo stack da modifiche o eliminazioni non autorizzate. Le deny settings bloccano le operazioni di modifica/eliminazione sulle risorse gestite dallo stack a meno che non vengano eseguite tramite lo stack stesso. Questo previene il configuration drift causato da modifiche manuali nel portale.
- **Cleanup delle risorse orfane**: quando una risorsa viene rimossa dal template e lo stack viene aggiornato, il Deployment Stack puo automaticamente eliminare (detach o delete) la risorsa orfana, mantenendo l'ambiente allineato con lo stato dichiarato nel codice.
- **Scope gerarchici**: gli stack possono essere creati a livello di Resource Group, Subscription o Management Group, distribuendo risorse nello scope corrente e negli scope inferiori. Uno stack a livello di Management Group puo creare subscription, Resource Group e risorse in un'unica operazione atomica.
- **Versionamento e rollback**: come i deployment standard, gli stack mantengono la storia dei deployment precedenti, consentendo il rollback a una versione precedente del template.

Esempio di creazione di un Deployment Stack con Azure CLI:

```bash
az stack group create \
  --name 'app-stack-prod' \
  --resource-group 'rg-prod' \
  --template-file 'main.bicep' \
  --deny-settings-mode 'denyWriteAndDelete' \
  --deny-settings-excluded-principals '<object-id-del-team-ops>' \
  --action-on-unmanage 'deleteAll' \
  --yes
```

I Deployment Stacks, combinati con i Template Specs (template Bicep/ARM versionati e pubblicati come risorse Azure riutilizzabili), forniscono una soluzione completa per la governance dell'infrastruttura senza le limitazioni di Azure Blueprints.

### Governance Avanzata — Pattern Operativi

La governance Azure a scala enterprise richiede un approccio strutturato che combina strumenti tecnici, processi organizzativi e automazione. I pattern operativi seguenti rappresentano le best practice per organizzazioni con decine o centinaia di subscription.

**Gerarchia Management Groups — Design Principles**:

La progettazione della gerarchia di Management Groups deve riflettere i confini di business e compliance, non la struttura dell'organigramma IT. Le linee guida principali sono:

- Mantenere la gerarchia superficiale (3-4 livelli massimo, escluso il root). Gerarchie profonde aumentano la complessita operativa senza benefici proporzionali.
- Creare Management Groups per ambiente (`Produzione`, `Non-Produzione`, `Sandbox`) al livello superiore, e per business unit o applicazione ai livelli inferiori.
- Applicare le policy di sicurezza piu restrittive al livello piu alto (root o primo livello) e rilassarle progressivamente verso i livelli inferiori solo quando giustificato.
- Riservare un Management Group `Sandbox` o `Decommissioned` per subscription sperimentali o in fase di dismissione, con policy permissive ma monitoring attivo.

**Tagging Enforcement — Strategia a Tre Livelli**:

Un framework di tagging efficace opera su tre livelli:

1. **Tag obbligatori (Deny)**: tag senza i quali la risorsa non puo essere creata. Tipicamente: `Environment` (dev/staging/prod), `Owner` (email del responsabile), `CostCenter` (codice centro di costo), `Application` (nome dell'applicazione). Implementati con Azure Policy e effetto `Deny`.
2. **Tag ereditati (Modify)**: tag copiati automaticamente dal Resource Group alla risorsa al momento della creazione. Implementati con Azure Policy e effetto `Modify` usando la funzione `[resourceGroup().tags['TagName']]`.
3. **Tag raccomandati (Audit)**: tag desiderabili ma non bloccanti, come `DataClassification`, `Criticality`, `ManagedBy`. Implementati con effetto `Audit` per visibilita nella compliance dashboard.

**Compliance Automation**:

L'automazione della compliance si basa su tre pilastri:

- **Policy Initiatives predefinite**: Azure fornisce iniziative per CIS Microsoft Azure Foundations Benchmark, ISO 27001:2013, PCI DSS 3.2.1, SOC 2, GDPR e NIST 800-53. Queste iniziative contengono decine di policy pre-configurate che valutano la conformita delle risorse rispetto allo standard selezionato.
- **Remediation Tasks**: quando una policy con effetto `DeployIfNotExists` o `Modify` rileva risorse non conformi esistenti, un **Remediation Task** puo correggere automaticamente la configurazione. I task di remediation richiedono una managed identity con i permessi necessari per modificare le risorse.
- **Compliance Dashboard**: il pannello di Azure Policy mostra lo stato di conformita aggregato per Management Group, subscription e Resource Group. Le metriche di compliance (percentuale di risorse conformi, trend nel tempo, risorse non conformi per categoria) alimentano i report di audit.

**Subscription Vending — Automazione del Provisioning**:

Il **Subscription Vending** e il processo automatizzato di creazione e configurazione delle subscription per nuovi team o applicazioni. Un processo di vending ben progettato:

- Crea la subscription tramite API (Enrollment Account o MCA).
- Sposta la subscription nel Management Group corretto.
- Applica automaticamente i Blueprint o Deployment Stacks con la configurazione baseline (networking, logging, policy, RBAC).
- Crea i Resource Group iniziali con i tag obbligatori.
- Configura i diagnostic settings per inviare i log al Log Analytics Workspace centralizzato.
- Notifica il team richiedente con le credenziali e la documentazione di onboarding.

L'intero processo puo essere implementato come pipeline CI/CD in Azure DevOps o GitHub Actions, attivata da un ticket approvato nel sistema ITSM.

---

## 10. Cost Management

### Cost Analysis

**Cost Analysis** in Azure Cost Management fornisce una visualizzazione dettagliata dei costi:

- **Vista giornaliera/mensile**: trend di spesa nel tempo con previsioni basate sui pattern storici.
- **Raggruppamento**: analisi dei costi per Resource Group, servizio, location, tag, meter o subscription.
- **Filtri**: drill-down su specifici servizi, periodi temporali o dimensioni personalizzate.
- **Export**: esportazione dei dati di costo in formato CSV o invio automatico a uno Storage Account per l'analisi con strumenti BI.

Le **Cost Views** personalizzate possono essere salvate e condivise con il team per un monitoraggio continuativo.

### Budgets

I **Budgets** consentono di impostare limiti di spesa e ricevere notifiche al raggiungimento di soglie percentuali:

- Si definisce un importo mensile/trimestrale/annuale.
- Si configurano soglie di notifica (ad esempio, 50%, 75%, 90%, 100% del budget).
- Le notifiche vengono inviate tramite email o Action Groups.
- Opzionalmente, al superamento di una soglia, si possono attivare azioni automatiche tramite Azure Functions o Logic Apps (ad esempio, arrestare le VM non critiche, ridimensionare le risorse).

I budget possono essere definiti a livello di subscription, Resource Group o con filtri specifici per tag o servizio.

### Raccomandazioni di Azure Advisor

Azure Advisor analizza l'utilizzo delle risorse e fornisce raccomandazioni specifiche per l'ottimizzazione dei costi:

- **Right-sizing**: identificazione di VM sottoutilizzate (CPU media < 5%) con suggerimento di ridimensionamento a una dimensione inferiore.
- **Risorse inutilizzate**: rilevamento di dischi non collegati, IP pubblici non associati, Gateway VPN/ExpressRoute inattivi.
- **Reserved Instances**: analisi dei pattern di utilizzo e suggerimento di Reserved Instances per i workload stabili.
- **Azure Hybrid Benefit**: identificazione delle VM che possono beneficiare delle licenze Windows Server o SQL Server esistenti.

### Reserved Instances e Savings Plans

Le **Reserved Instances (RI)** offrono sconti significativi (fino al 72% rispetto al pay-as-you-go) in cambio di un impegno di 1 o 3 anni per una specifica dimensione di VM in una specifica regione:

- **Instance Size Flexibility**: all'interno della stessa famiglia di VM, lo sconto si applica automaticamente a dimensioni diverse (ad esempio, una reservation per `D4s_v5` copre anche due `D2s_v5`).
- **Scope**: la reservation puo essere applicata a una singola subscription, a un Resource Group condiviso o a tutta l'organizzazione (shared scope).
- **Exchangeability**: le reservation possono essere scambiate con dimensioni o regioni diverse (entro i limiti della policy).

I **Savings Plans** offrono un modello piu flessibile: si impegna un importo orario fisso per 1 o 3 anni, e lo sconto si applica automaticamente all'utilizzo di compute che corrisponde al piano, indipendentemente dalla regione, dimensione o famiglia di VM. I Savings Plans sono la scelta raccomandata per workload con esigenze di compute variabili.

### Azure Hybrid Benefit

**Azure Hybrid Benefit** consente di utilizzare le licenze on-premises di Windows Server e SQL Server (con Software Assurance attiva) sulle VM Azure, riducendo il costo del compute fino al 40% per Windows Server e fino all'85% per SQL Server (combinato con Reserved Instances). Si applica anche a Azure SQL Database, SQL Managed Instance e Azure Kubernetes Service (per i nodi Windows).

### FinOps e Pratiche Avanzate di Ottimizzazione

L'ottimizzazione dei costi cloud va oltre l'uso di Reserved Instances e richiede una disciplina operativa strutturata nota come **FinOps** (Financial Operations). FinOps unisce team di engineering, finance e business per gestire i costi cloud come una competenza organizzativa.

**Cost Anomaly Detection**:

Azure Cost Management include la funzionalita di **Cost Anomaly Detection** basata su machine learning. Il sistema analizza i pattern storici di spesa e genera alert automatici quando rileva deviazioni significative — ad esempio, un aumento improvviso dei costi di compute dovuto a un autoscaling non controllato, un deployment errato che crea risorse sovradimensionate, o un attacco che genera traffico anomalo. Gli alert di anomalia si integrano con gli Action Groups per notifiche immediate al team FinOps.

**Showback e Chargeback**:

La distinzione tra showback e chargeback e fondamentale per la responsabilizzazione dei team:

- **Showback**: i costi vengono attribuiti ai team in modo informativo, senza addebito reale. Ogni team visualizza il proprio consumo tramite dashboard filtrate per tag (`CostCenter`, `Team`, `Application`). Lo showback aumenta la consapevolezza dei costi senza creare frizioni organizzative.
- **Chargeback**: i costi vengono effettivamente addebitati ai budget dei singoli team o business unit. Richiede un tagging rigoroso (con enforcement via Azure Policy) e processi contabili per la riconciliazione mensile. L'export automatico dei dati di costo verso lo Storage Account consente l'integrazione con i sistemi ERP e di contabilita.

**Automazione del risparmio**:

- **Auto-shutdown schedulato**: le VM di sviluppo e test possono essere configurate con l'auto-shutdown (built-in nella configurazione della VM) o tramite Azure Automation con runbook che arrestano le VM fuori orario lavorativo e nei weekend, con risparmio stimato del 65-70%.
- **Spot VM con fallback**: per workload batch, configurare i job per utilizzare prima le Spot VM (sconto fino al 90%) con fallback automatico su VM on-demand quando le Spot vengono reclamate.
- **Storage lifecycle automation**: combinare le lifecycle management policies con il monitoraggio dell'access time per spostare automaticamente i dati tra i tier Hot, Cool, Cold e Archive basandosi sull'effettivo pattern di accesso.

**Azure Cost Management API e integrazione BI**:

L'API di Azure Cost Management consente di estrarre i dati di costo programmaticamente per integrarli in dashboard personalizzate (Power BI, Grafana) e sistemi di alerting custom. L'export schedulato verso Storage Account in formato CSV o Parquet alimenta pipeline di analisi che producono report dettagliati per il management, con breakdown per servizio, regione, team e ambiente.

---

## 11. Infrastructure as Code — ARM e Bicep

### ARM Templates (Cenni)

I **Azure Resource Manager (ARM) Templates** sono file JSON dichiarativi che definiscono l'infrastruttura Azure. Un template ARM contiene le sezioni:

- **parameters**: valori di input forniti al momento del deployment.
- **variables**: valori calcolati utilizzati nel template.
- **resources**: le risorse Azure da distribuire.
- **outputs**: valori restituiti dopo il deployment.

Esempio minimale di un ARM Template per uno Storage Account:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "storageAccountName": {
      "type": "string"
    },
    "location": {
      "type": "string",
      "defaultValue": "[resourceGroup().location]"
    }
  },
  "resources": [
    {
      "type": "Microsoft.Storage/storageAccounts",
      "apiVersion": "2023-01-01",
      "name": "[parameters('storageAccountName')]",
      "location": "[parameters('location')]",
      "sku": { "name": "Standard_LRS" },
      "kind": "StorageV2"
    }
  ]
}
```

I template ARM sono potenti ma verbosi. Microsoft ha sviluppato Bicep come alternativa semplificata.

### Bicep — Sintassi ed Esempi

**Bicep** e un DSL che compila in ARM Templates JSON, con sintassi concisa e leggibile. Non e un'astrazione sopra ARM: e una trasformazione sintattica diretta.

Vantaggi di Bicep rispetto ad ARM JSON:

- Sintassi concisa e leggibile (riduzione del 50-70% del codice).
- Rilevamento automatico delle dipendenze tra risorse (niente piu `dependsOn` espliciti nella maggior parte dei casi).
- Supporto nativo per moduli riutilizzabili.
- Validazione e IntelliSense nell'editor (VS Code con l'estensione Bicep).
- Decompilazione da ARM JSON a Bicep con `az bicep decompile`.

Esempio di un file Bicep per un'applicazione web con database:

```bicep
// main.bicep — Distribuzione di un App Service con SQL Database

@description('Nome dell ambiente (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string

@description('Location per tutte le risorse')
param location string = resourceGroup().location

@secure()
@description('Password dell amministratore SQL')
param sqlAdminPassword string

var appServicePlanName = 'asp-${environment}-001'
var webAppName = 'webapp-${environment}-${uniqueString(resourceGroup().id)}'
var sqlServerName = 'sql-${environment}-${uniqueString(resourceGroup().id)}'
var sqlDatabaseName = 'sqldb-${environment}-001'

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: environment == 'prod' ? 'P1v3' : 'B1'
  }
  properties: {
    reserved: true // Linux
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'DOTNETCORE|8.0'
      alwaysOn: environment == 'prod'
      appSettings: [
        {
          name: 'ASPNETCORE_ENVIRONMENT'
          value: environment == 'prod' ? 'Production' : 'Development'
        }
        {
          name: 'ConnectionStrings__DefaultConnection'
          value: 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=${sqlDatabaseName};'
        }
      ]
    }
  }
}

// SQL Server
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: 'sqladmin'
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
  }
}

// SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  sku: {
    name: environment == 'prod' ? 'S1' : 'Basic'
  }
}

// Outputs
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
```

Deployment tramite Azure CLI:

```bash
az deployment group create \
  --resource-group myResourceGroup \
  --template-file main.bicep \
  --parameters environment='prod' sqlAdminPassword='SecureP@ss123!'
```

I **moduli Bicep** consentono di scomporre l'infrastruttura in componenti riutilizzabili:

```bicep
// Utilizzo di un modulo
module network 'modules/network.bicep' = {
  name: 'networkDeployment'
  params: {
    vnetName: 'vnet-prod-001'
    location: location
    addressPrefix: '10.0.0.0/16'
  }
}

module database 'modules/database.bicep' = {
  name: 'databaseDeployment'
  params: {
    subnetId: network.outputs.dbSubnetId
  }
}
```

### Riferimento a Terraform

**Terraform** (HashiCorp) e ampiamente utilizzato per Azure tramite il provider **azurerm**. Offre vantaggi per ambienti multi-cloud e dispone di un ecosistema maturo nel Terraform Registry. Per un approfondimento, consultare la sezione [Infrastructure as Code](../04-infrastructure-as-code.md).

---

## 12. Best Practices

Principi chiave per una gestione efficace dell'infrastruttura Azure:

1. **Applicare il principio del least privilege con RBAC e Managed Identities**: assegnare sempre i permessi minimi necessari. Utilizzare le Managed Identities per eliminare le credenziali dal codice. Abilitare PIM per i ruoli privilegiati con attivazione just-in-time e approvazione. Evitare l'uso di chiavi di accesso condivise quando e disponibile l'autenticazione tramite Entra ID.

2. **Progettare per l'alta disponibilita con Availability Zones**: distribuire le risorse critiche su piu Availability Zones (VM in zone diverse, zone-redundant services per database e storage). Utilizzare ZRS o GZRS per lo storage dei dati critici. Configurare auto-failover groups per i database. Ogni componente dell'architettura deve avere un piano di resilienza zonale.

3. **Implementare una strategia di networking hub-and-spoke**: centralizzare la connettivita e la sicurezza di rete in una VNet hub con Azure Firewall, e connettere le VNet applicative (spoke) tramite peering. Utilizzare Private Endpoints per tutti i servizi PaaS per eliminare l'esposizione su Internet. Abilitare NSG flow logs e Traffic Analytics per la visibilita del traffico di rete.

4. **Adottare Infrastructure as Code con Bicep o Terraform**: non creare mai risorse manualmente dal portale per ambienti di staging e produzione. Versionare tutti i template IaC nel repository Git. Utilizzare moduli riutilizzabili per standardizzare i pattern architetturali. Implementare pipeline CI/CD per il deployment automatizzato con validation (what-if) prima dell'applicazione.

5. **Implementare una strategia di tagging coerente**: definire un set obbligatorio di tag (Environment, Owner, CostCenter, Application, ManagedBy) e applicarli tramite Azure Policy con effetto Deny per impedire la creazione di risorse senza tag. Utilizzare i tag per l'allocazione dei costi, l'automazione (ad esempio, arrestare le VM di sviluppo fuori orario) e la governance.

6. **Monitorare proattivamente con Azure Monitor e alerting**: configurare Azure Monitor per raccogliere metriche e log da tutte le risorse. Definire alert su metriche critiche (CPU, memoria, errori, latenza) e log (errori applicativi, eventi di sicurezza). Utilizzare Application Insights per le applicazioni. Creare Workbooks per la visualizzazione dei dati operativi e condividerli con il team.

7. **Ottimizzare i costi sistematicamente**: rivedere le raccomandazioni di Azure Advisor mensilmente. Utilizzare Reserved Instances o Savings Plans per workload stabili (risparmio fino al 72%). Abilitare l'auto-shutdown per le VM di sviluppo. Dimensionare correttamente le risorse (right-sizing) in base all'utilizzo effettivo. Implementare lifecycle management policies per lo storage. Configurare budgets con soglie di notifica.

8. **Centralizzare la gestione dei secret con Key Vault**: archiviare tutti i secret, le chiavi crittografiche e i certificati in Azure Key Vault. Non inserire mai credenziali nel codice sorgente, nei file di configurazione o nelle variabili di ambiente hardcoded. Abilitare soft-delete e purge protection per prevenire la perdita accidentale. Ruotare i secret periodicamente e automaticamente.

9. **Implementare una strategia di governance con Azure Policy e Management Groups**: definire una gerarchia di Management Groups che rifletta la struttura organizzativa. Applicare Azure Policy a livello di Management Group per garantire la conformita di tutte le subscription. Utilizzare iniziative di policy predefinite (CIS Benchmarks) come baseline di sicurezza. Monitorare la compliance dashboard regolarmente e rimediare le non-conformita.

---

## 13. Azure DevOps e GitHub Integration

Azure offre due piattaforme principali per il ciclo di vita dello sviluppo software: **Azure DevOps Services** e **GitHub**. Microsoft possiede entrambe e sta convergendo progressivamente le funzionalita, mantenendo pero identita distinte. La scelta tra le due (o l'adozione ibrida) dipende dal contesto organizzativo, dal modello di sviluppo e dai requisiti di compliance.

### Azure DevOps Services

**Azure DevOps** e una piattaforma integrata che fornisce cinque servizi principali:

- **Azure Repos**: repository Git privati con supporto per branch policies, pull request con reviewer obbligatori, build validation (CI che deve passare prima del merge), e policy di merge (squash, rebase, merge commit). Supporta repository TFVC (Team Foundation Version Control) per legacy.
- **Azure Pipelines**: il motore CI/CD di Azure DevOps. Supporta pipeline YAML (dichiarative, versionabili nel repository) e Classic (editor visuale, legacy). Le pipeline YAML sono la scelta raccomandata per la riproducibilita e il version control. Azure Pipelines supporta agent hosted da Microsoft (Linux, Windows, macOS) e agent self-hosted per ambienti con requisiti di rete specifici.
- **Azure Boards**: gestione del lavoro con work items, board Kanban, sprint planning e backlog. Si integra con i commit e le pull request tramite tag nei messaggi di commit (ad esempio, `AB#1234` per collegare un work item).
- **Azure Artifacts**: registry di pacchetti che supporta NuGet, npm, Maven, Python (PyPI) e Universal Packages. Consente di ospitare feed privati per le dipendenze interne dell'organizzazione.
- **Azure Test Plans**: gestione dei test manuali e automatizzati con tracciabilita verso i work items e le build.

**Pipeline YAML — Struttura e Best Practices**:

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include: [main, release/*]
  paths:
    exclude: [docs/*, '*.md']

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: 'production-secrets'  # Variable group da Azure Key Vault
  - name: buildConfiguration
    value: 'Release'

stages:
  - stage: Build
    jobs:
      - job: BuildAndTest
        steps:
          - task: UseDotNet@2
            inputs:
              packageType: 'sdk'
              version: '8.x'
          - script: dotnet build --configuration $(buildConfiguration)
            displayName: 'Build'
          - script: dotnet test --configuration $(buildConfiguration) --collect:"XPlat Code Coverage"
            displayName: 'Test'
          - task: PublishCodeCoverageResults@2
            inputs:
              summaryFileLocation: '$(Agent.TempDirectory)/**/coverage.cobertura.xml'

  - stage: Deploy
    dependsOn: Build
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployToProduction
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureWebApp@1
                  inputs:
                    azureSubscription: 'Production-ServiceConnection'
                    appName: 'myapp-prod'
```

**Service Connections e Sicurezza**:

Le Service Connections autenticano le pipeline verso le risorse Azure. La best practice attuale e utilizzare **Workload Identity Federation (OIDC)** anziche Service Principal con secret. Con OIDC, Azure DevOps presenta un token federato che Azure verifica senza secret persistenti, eliminando il rischio di esposizione delle credenziali e la necessita di rotazione.

### GitHub Actions per Azure

**GitHub Actions** e il sistema CI/CD nativo di GitHub. Per i deployment Azure, l'integrazione avviene tramite:

- **Azure Login Action** (`azure/login@v2`): autenticazione verso Azure tramite OIDC (Workload Identity Federation), Service Principal con secret, o Managed Identity (per runner self-hosted in Azure).
- **Azure Verified Actions**: azioni ufficiali Microsoft per il deployment su App Service, Container Apps, AKS, Azure Functions, Static Web Apps e altri servizi.
- **GitHub Environments**: configurazione di ambienti (staging, production) con regole di protezione — reviewer obbligatori, timer di attesa, branch restrictions e secret con scope limitato all'ambiente.

**Workflow GitHub Actions con OIDC per Azure**:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure
on:
  push:
    branches: [main]

permissions:
  id-token: write   # Necessario per OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy Bicep
        uses: azure/arm-deploy@v2
        with:
          resourceGroupName: 'rg-prod'
          template: './infra/main.bicep'
          parameters: 'environment=prod'

      - name: Deploy App
        uses: azure/webapps-deploy@v3
        with:
          app-name: 'myapp-prod'
          package: './publish'
```

### Strategia Ibrida — Azure DevOps + GitHub

Molte organizzazioni adottano un approccio ibrido che sfrutta i punti di forza di ciascuna piattaforma:

- **GitHub** per il codice sorgente (collaborazione open-source, community, Code Search, Copilot, Dependabot per la sicurezza delle dipendenze).
- **Azure DevOps Boards** per la gestione del lavoro enterprise (SAFe, sprint planning, integrazione con Microsoft Project).
- **Azure Pipelines** per deployment complessi che richiedono multi-stage approvals, gate conditions e integrazione con ambienti on-premises tramite agent self-hosted.

L'integrazione bidirezionale consente di collegare i commit GitHub ai work items di Azure Boards tramite la sintassi `AB#<id>` nei messaggi di commit, e di triggerare pipeline Azure DevOps da eventi GitHub (push, pull request) tramite il connettore GitHub per Azure Pipelines.

---

## 14. Azure Landing Zones

Le **Azure Landing Zones** rappresentano l'architettura di riferimento di Microsoft per il deployment enterprise di Azure. Una Landing Zone e un ambiente Azure pre-configurato che implementa le best practice di governance, sicurezza, networking e gestione delle identita, fornendo una base solida e scalabile su cui i team applicativi possono costruire i propri workload.

### Architettura Concettuale

L'architettura delle Azure Landing Zones si compone di due elementi fondamentali:

**Platform Landing Zone**: fornisce i servizi condivisi utilizzati da tutte le applicazioni. Include:

- **Identity**: tenant Entra ID, domain controllers sincronizzati (se necessari), configurazione SSO e Conditional Access.
- **Management**: Log Analytics Workspace centralizzato, Azure Monitor, Azure Automation, Update Management.
- **Connectivity**: VNet hub con Azure Firewall, ExpressRoute/VPN Gateway, Azure DNS Private Zones, routing centralizzato.
- **Security**: Microsoft Defender for Cloud, Sentinel, Key Vault centralizzato per i secret della piattaforma.

**Application Landing Zones**: subscription dedicate ai singoli workload o applicazioni. Ogni Application Landing Zone:

- Ha una propria subscription per l'isolamento della fatturazione e delle risorse.
- Eredita le policy di governance e sicurezza dal Management Group padre.
- Si connette alla Platform Landing Zone tramite VNet peering con il hub di connettivita.
- Contiene le risorse specifiche dell'applicazione (compute, storage, database).

```
Root Management Group
├── Platform
│   ├── Identity          (Subscription: domain controllers, Entra DS)
│   ├── Management        (Subscription: Log Analytics, Automation)
│   └── Connectivity      (Subscription: hub VNet, Firewall, DNS)
├── Landing Zones
│   ├── Corp              (Subscription per workload interni connessi alla rete aziendale)
│   │   ├── Sub: ERP-Prod
│   │   ├── Sub: CRM-Prod
│   │   └── Sub: Data-Platform
│   └── Online            (Subscription per workload internet-facing)
│       ├── Sub: WebApp-Prod
│       └── Sub: API-Gateway
├── Sandbox               (Subscription per sperimentazione)
│   └── Sub: Innovation-Lab
└── Decommissioned        (Subscription in fase di dismissione)
```

### Aree di Design

Le Azure Landing Zones sono organizzate attorno a otto aree di design critiche:

1. **Billing e Tenant Entra ID**: definizione della strategia di fatturazione (Enterprise Agreement, MCA, CSP) e della relazione tra tenant Entra ID e subscription.
2. **Identity e Access Management**: configurazione di Entra ID, sincronizzazione con AD on-premises, Conditional Access, PIM e modello RBAC.
3. **Management Group e Subscription Organization**: progettazione della gerarchia di Management Groups e delle politiche di creazione delle subscription.
4. **Network Topology e Connectivity**: scelta tra topologia hub-and-spoke tradizionale o Azure Virtual WAN, configurazione della connettivita hybrid (ExpressRoute, VPN) e del routing.
5. **Security**: deployment di Defender for Cloud, Sentinel, policy di sicurezza e baseline di hardening.
6. **Management**: configurazione del monitoraggio centralizzato, patch management, backup e disaster recovery.
7. **Governance**: definizione delle Azure Policy, tagging strategy e compliance monitoring.
8. **Platform Automation e DevOps**: approccio IaC per il deployment e la manutenzione della piattaforma.

### Implementazione con Azure Verified Modules (AVM)

Microsoft raccomanda l'utilizzo degli **Azure Verified Modules (AVM)** per l'implementazione delle Landing Zones. Gli AVM sono moduli Terraform e Bicep ufficiali, testati e manutenuti da Microsoft, che incapsulano le best practice per il deployment delle risorse Azure.

L'**ALZ IaC Accelerator** e lo strumento ufficiale che genera la configurazione iniziale della Landing Zone basata su AVM. Il processo tipico di deployment e:

1. Eseguire l'ALZ Accelerator per generare il codice IaC personalizzato per l'organizzazione.
2. Versionare il codice generato in un repository Git.
3. Configurare una pipeline CI/CD per il deployment della piattaforma.
4. Iterare sulla configurazione tramite pull request e code review.

Questo approccio **GitOps** garantisce che ogni modifica alla piattaforma sia tracciabile, reversibile e soggetta ad approvazione.

---

## 15. Azure Well-Architected Framework — I Cinque Pilastri

L'**Azure Well-Architected Framework (WAF)** e la guida architetturale di Microsoft per la progettazione e la gestione di workload cloud di alta qualita. Il framework definisce cinque pilastri che rappresentano le dimensioni fondamentali di un'architettura well-architected. Ogni workload dovrebbe essere valutato rispetto a ciascun pilastro, bilanciando i trade-off in base alle priorita di business.

### Pilastro 1 — Affidabilita (Reliability)

Il pilastro dell'affidabilita si concentra sulla capacita del workload di resistere ai guasti e di recuperare completamente. I principi fondamentali sono:

- **Progettare per il guasto**: ogni componente puo fallire. Implementare ridondanza a ogni livello — compute (multi-zone, multi-region), storage (ZRS, GZRS), database (geo-replication, auto-failover groups). Definire RTO (Recovery Time Objective) e RPO (Recovery Point Objective) per ogni workload e progettare l'architettura per rispettarli.
- **Osservare la salute del sistema**: implementare health checks a ogni livello (infrastruttura, applicazione, dipendenze). Utilizzare health probes per i load balancer, liveness e readiness probes per i container, e Application Insights Availability Tests per il monitoraggio end-to-end.
- **Automatizzare il recovery**: il failover deve essere automatico, non manuale. Configurare auto-failover groups per i database, Azure Site Recovery per le VM, e runbook di Azure Automation per le procedure di recovery complesse.
- **Testare la resilienza**: eseguire **chaos engineering** con Azure Chaos Studio per iniettare guasti controllati (shutdown di una zona, aumento della latenza di rete, esaurimento delle risorse) e verificare che il sistema si comporti come previsto. I test di resilienza devono essere eseguiti regolarmente in ambienti di pre-produzione e, progressivamente, in produzione.

**Metriche chiave**: SLA composito del workload, MTTR (Mean Time To Recovery), frequenza degli incidenti, successo dei test di failover.

### Pilastro 2 — Sicurezza (Security)

Il pilastro della sicurezza protegge il workload da minacce e vulnerabilita durante l'intero ciclo di vita. I principi fondamentali sono:

- **Zero Trust**: non fidarsi mai, verificare sempre. Ogni richiesta deve essere autenticata e autorizzata, indipendentemente dall'origine. Implementare Conditional Access, MFA, e network segmentation.
- **Defense in depth**: applicare controlli di sicurezza a piu livelli — identita (Entra ID, RBAC), rete (NSG, Firewall, Private Link), applicazione (WAF, input validation), dati (crittografia at-rest e in-transit, Key Vault).
- **Least privilege**: assegnare solo i permessi necessari per svolgere il compito specifico. Utilizzare PIM per l'accesso just-in-time ai ruoli privilegiati. Preferire Managed Identities ai Service Principal con secret.
- **Shift-left security**: integrare la sicurezza nel ciclo di sviluppo. Utilizzare GitHub Advanced Security o Azure DevOps per la scansione del codice (SAST), delle dipendenze (SCA), dei secret (secret scanning) e dei container (vulnerability scanning) nelle pipeline CI/CD.

**Strumenti chiave**: Microsoft Defender for Cloud (Secure Score, Regulatory Compliance), Sentinel (SIEM/SOAR), Key Vault, Azure Policy, Microsoft Entra Permissions Management.

### Pilastro 3 — Ottimizzazione dei Costi (Cost Optimization)

Il pilastro dell'ottimizzazione dei costi garantisce che il workload fornisca il massimo valore al minor costo possibile. I principi fondamentali sono:

- **Comprendere il modello di costo**: mappare ogni componente dell'architettura al relativo modello di fatturazione. Distinguere tra costi fissi (Reserved Instances) e variabili (pay-as-you-go). Utilizzare il Pricing Calculator di Azure per stimare i costi prima del deployment.
- **Monitorare e attribuire**: implementare un framework di tagging rigoroso per attribuire i costi a team, applicazioni e ambienti. Utilizzare Azure Cost Management per analizzare i trend, identificare le anomalie e prevedere la spesa futura.
- **Ottimizzare le risorse**: applicare il right-sizing basato sull'utilizzo effettivo. Utilizzare Spot VM per workload fault-tolerant. Implementare autoscaling per adattare le risorse alla domanda. Spostare i dati infrequentemente acceduti verso tier di storage piu economici.
- **Pianificare gli impegni**: per workload stabili e prevedibili, utilizzare Reserved Instances (sconto fino al 72%) o Savings Plans (flessibilita tra regioni e famiglie di VM). Combinare con Azure Hybrid Benefit per le licenze on-premises.

**Strumenti chiave**: Azure Cost Management, Azure Advisor, Budget Alerts, Cost Anomaly Detection, Azure Pricing Calculator.

### Pilastro 4 — Eccellenza Operativa (Operational Excellence)

Il pilastro dell'eccellenza operativa si concentra sui processi e sulle pratiche che mantengono il workload funzionante in produzione. I principi fondamentali sono:

- **Infrastructure as Code**: definire tutta l'infrastruttura in codice (Bicep, Terraform). Non effettuare mai modifiche manuali in produzione. Versionare i template IaC nel repository Git e applicarli tramite pipeline CI/CD con validation (what-if/plan) prima dell'applicazione.
- **Automazione end-to-end**: automatizzare build, test, deployment, monitoring e incident response. Le pipeline CI/CD devono includere test automatizzati (unit, integration, e2e), security scanning, e deployment progressivo (canary, blue-green).
- **Osservabilita**: implementare i tre pilastri dell'osservabilita — **metriche** (Azure Monitor Metrics), **log** (Log Analytics con KQL), e **tracce distribuite** (Application Insights con distributed tracing). Correlare i dati tra i tre livelli per diagnosticare rapidamente i problemi.
- **Continuous improvement**: condurre post-incident review (blameless post-mortems) dopo ogni incidente. Mantenere runbook aggiornati per le procedure operative ricorrenti. Utilizzare Azure Chaos Studio per identificare proattivamente le debolezze del sistema.
- **AI-assisted operations**: integrare l'intelligenza artificiale nelle operazioni quotidiane. Azure Monitor supporta la rilevazione automatica di anomalie nelle metriche, la correlazione intelligente degli alert, e suggerimenti di root cause analysis basati su machine learning.

**Strumenti chiave**: Azure Monitor, Log Analytics, Application Insights, Azure DevOps/GitHub Actions, Azure Automation, Azure Chaos Studio.

### Pilastro 5 — Efficienza delle Prestazioni (Performance Efficiency)

Il pilastro dell'efficienza delle prestazioni garantisce che il workload sia dimensionato correttamente e possa scalare per soddisfare la domanda. I principi fondamentali sono:

- **Scalabilita orizzontale**: progettare l'architettura per scalare orizzontalmente (aggiungendo istanze) anziche verticalmente (aumentando le risorse di una singola istanza). Utilizzare VMSS, AKS con Cluster Autoscaler o Container Apps con scaling event-driven.
- **Scelta del servizio appropriato**: selezionare il servizio Azure che meglio corrisponde ai requisiti del workload. Non utilizzare una VM quando un servizio PaaS (App Service, Container Apps, Azure Functions) puo soddisfare le esigenze con meno overhead operativo.
- **Caching strategico**: implementare caching a piu livelli — Azure CDN/Front Door per il contenuto statico, Azure Cache for Redis per i dati applicativi, application-level caching per i risultati di query costose. Il caching e il singolo intervento con il maggiore impatto sulle prestazioni nella maggior parte delle architetture web.
- **Ottimizzazione del data access**: utilizzare replica in lettura per i database (Azure SQL read replicas, Cosmos DB multi-region reads). Scegliere il tier di storage appropriato per le prestazioni richieste (Premium SSD v2 per workload database critici, Standard SSD per sviluppo). Implementare connection pooling per ridurre l'overhead delle connessioni al database.
- **Performance testing**: eseguire test di carico regolari con Azure Load Testing per identificare i colli di bottiglia prima che impattino gli utenti. Definire baseline di prestazioni e monitorare le deviazioni nel tempo.

**Strumenti chiave**: Azure Load Testing, Azure Monitor Metrics, Application Insights Performance Profiler, Azure Cache for Redis, Azure Front Door.

### Well-Architected Review

L'**Azure Well-Architected Review** e un assessment strutturato che valuta un workload rispetto ai cinque pilastri. Disponibile tramite il portale Azure (Azure Advisor) o come assessment guidato nel Well-Architected Framework documentation site, produce raccomandazioni prioritizzate con link alla documentazione di implementazione. E raccomandato eseguire la review prima di andare in produzione (pre-production review), dopo ogni cambiamento architetturale significativo, e periodicamente (almeno annualmente) per i workload in produzione.

---

## Esercizi

1. **Resource Group e Tagging (Base)**
   Creare un Resource Group con tag obbligatori (Environment, Owner, CostCenter). Deployare una VM Linux con Managed Identity system-assigned. Configurare un Azure Policy con effetto Deny che impedisca la creazione di risorse senza il tag `Environment`. Verificare che la policy blocchi risorse non conformi.

2. **Networking Hub-and-Spoke (Intermedio)**
   Progettare una rete hub-and-spoke con tre VNet: una hub (con Azure Firewall e Bastion) e due spoke (dev e prod). Configurare il peering VNet, le User Defined Routes per forzare il traffico attraverso il firewall, e un Private Endpoint per un Azure SQL Database accessibile solo dalla spoke prod.

3. **Entra ID e RBAC con PIM (Intermedio)**
   Configurare Entra ID con almeno tre gruppi di sicurezza. Assegnare ruoli RBAC custom a livello di subscription con il principio del minimo privilegio. Abilitare PIM per il ruolo Contributor sulla subscription di produzione con attivazione just-in-time, durata massima di 4 ore e approvazione obbligatoria.

4. **CI/CD con Workload Identity Federation (Avanzato)**
   Configurare una Federated Identity Credential su un'app registration Entra ID per GitHub Actions. Creare un workflow che si autentichi via OIDC, esegua `az deployment group what-if` per un template Bicep, e applichi il deployment solo dopo approvazione manuale nell'ambiente di produzione.

5. **Governance Multi-Subscription (Avanzato)**
   Implementare una gerarchia di Management Groups con almeno tre livelli. Applicare iniziative Azure Policy per CIS Benchmarks a livello root. Configurare diagnostic settings per inviare Activity Log di tutte le subscription a un Log Analytics Workspace centralizzato. Creare un Workbook di Azure Monitor che visualizzi lo stato di compliance e le anomalie di costo.

---

## Letture e Riferimenti

**Documentazione ufficiale**

- Microsoft Azure Well-Architected Framework — https://learn.microsoft.com/en-us/azure/well-architected/ (consultato: 2026-05-24)
- Azure RBAC Documentation — https://learn.microsoft.com/en-us/azure/role-based-access-control/ (consultato: 2026-05-24)
- Azure Virtual Network Documentation — https://learn.microsoft.com/en-us/azure/virtual-network/ (consultato: 2026-05-24)
- Azure Policy Documentation — https://learn.microsoft.com/en-us/azure/governance/policy/ (consultato: 2026-05-24)
- Bicep Language Reference — https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/ (consultato: 2026-05-24)
- Azure Cost Management Documentation — https://learn.microsoft.com/en-us/azure/cost-management-billing/ (consultato: 2026-05-24)
- Microsoft Entra ID Documentation — https://learn.microsoft.com/en-us/entra/identity/ (consultato: 2026-05-24)

**Libri consigliati**

- *Exam Ref AZ-305: Designing Microsoft Azure Infrastructure Solutions* — Ashish Agrawal et al. (Microsoft Press)
- *Azure Architecture Explained* — David Rendón (Packt)
- *Microsoft Azure Security Technologies* — Yuri Diogenes, Orin Thomas (Microsoft Press)

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|--------|--------|-----------|
| [01](01-cloud-aws.md) | AWS | Confronto servizi equivalenti e strategie multi-cloud |
| [03](03-cloud-gcp.md) | Google Cloud Platform | Confronto IAM, networking e modelli organizzativi |
| [04](04-infrastructure-as-code.md) | Infrastructure as Code | Provider azurerm Terraform, template Bicep/ARM |
| [07](07-ci-cd.md) | CI/CD | Azure DevOps Pipelines, GitHub Actions con OIDC |
| [14](14-compliance.md) | Compliance | Azure Policy, CIS Benchmarks, regulatory compliance |
| [21](21-finops-cost-governance.md) | FinOps e Cost Governance | Cost Management, Reserved Instances, Advisor |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Availability Zone** | Data center fisicamente separato all'interno di una regione Azure, con alimentazione e rete indipendenti |
| **Bicep** | Linguaggio dichiarativo domain-specific di Azure per il deployment di risorse, compilato in template ARM |
| **Entra ID** | Servizio di identità cloud di Microsoft (ex Azure AD) per autenticazione, SSO e gestione degli accessi |
| **Key Vault** | Servizio gestito per archiviare e controllare l'accesso a segreti, chiavi crittografiche e certificati |
| **Managed Identity** | Identità gestita automaticamente da Azure per autenticare le risorse senza credenziali nel codice |
| **Management Group** | Contenitore gerarchico che raggruppa subscription per applicare policy e RBAC in modo ereditario |
| **NSG (Network Security Group)** | Filtro di rete a livello di subnet o NIC che controlla il traffico in ingresso e uscita con regole a priorità |
| **PIM (Privileged Identity Management)** | Servizio per l'attivazione just-in-time di ruoli privilegiati con approvazione e audit |
| **Private Endpoint** | Interfaccia di rete privata che connette una VNet a un servizio PaaS senza passare dalla rete pubblica |
| **RBAC (Role-Based Access Control)** | Modello di autorizzazione che assegna permessi in base a ruoli predefiniti o custom su uno scope specifico |
| **Resource Group** | Contenitore logico per raggruppare e gestire risorse Azure correlate come unità |
| **VNet (Virtual Network)** | Rete virtuale isolata in Azure per la comunicazione sicura tra risorse cloud |
| **Workload Identity Federation** | Meccanismo OIDC che consente a identità esterne di assumere ruoli Azure senza secret client |

10. **Automatizzare il disaster recovery e testarlo regolarmente**: definire RTO (Recovery Time Objective) e RPO (Recovery Point Objective) per ogni workload. Configurare backup automatici per VM, database e storage. Implementare geo-replication per i database critici. Utilizzare Azure Site Recovery per la replica delle VM tra regioni. Eseguire drill di disaster recovery periodici (almeno trimestrali) per verificare che le procedure funzionino e che RTO/RPO siano rispettati. Documentare e automatizzare le procedure di failover e failback.
