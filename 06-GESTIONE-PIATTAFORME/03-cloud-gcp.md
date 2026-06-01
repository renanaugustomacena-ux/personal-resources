---
corso: "Gestione Piattaforme e DevOps"
fase: "1 — Cloud Provider"
modulo: 3
titolo: "Google Cloud Platform (GCP) — Documentazione Completa"
versione: "2026"
livello: "Avanzato"
prerequisiti: ["01-cloud-aws", "02-cloud-azure", "04-infrastructure-as-code"]
obiettivi:
  - "Comprendere l'infrastruttura globale GCP e il modello organizzativo basato su Project e Folder"
  - "Configurare IAM con Workload Identity, Organization Policies e VPC Service Controls"
  - "Progettare architetture di rete con VPC condivise, Cloud Interconnect e Cloud Armor"
  - "Utilizzare i servizi data e AI/ML: BigQuery, Vertex AI, Pub/Sub e Cloud Storage"
  - "Implementare strategie di costo con CUD, SUD, labeling e billing export su BigQuery"
tag: [gcp, cloud, bigquery, vertex-ai, iam, vpc, gke, cloud-run, organization-policies]
---

# Google Cloud Platform (GCP) — Documentazione Completa

> **Modulo 03** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Comprendere l'infrastruttura globale GCP e il modello organizzativo basato su Project e Folder
> 2. Configurare IAM con Workload Identity, Organization Policies e VPC Service Controls
> 3. Progettare architetture di rete con VPC condivise, Cloud Interconnect e Cloud Armor
> 4. Utilizzare i servizi data e AI/ML: BigQuery, Vertex AI, Pub/Sub e Cloud Storage
> 5. Implementare strategie di costo con CUD, SUD, labeling e billing export su BigQuery
>
> **Prerequisiti:** [AWS](01-cloud-aws.md) · [Azure](02-cloud-azure.md) · [IaC](04-infrastructure-as-code.md)
> **Tempo stimato:** 90 min · **Livello:** Avanzato

## Idee guida

1. **GCP forte in data + AI/ML.** BigQuery, Vertex AI, Pub/Sub.
2. **Project = unit of billing + IAM.** Folder per gerarchia.
3. **Workload Identity per K8s/CI.** No service account key files.
4. **Live Migration VM nativa.** Maintenance senza downtime.


## Indice

1. [Panoramica dell'Infrastruttura Globale GCP](#1-panoramica-dellinfrastruttura-globale-gcp)
2. [IAM e Resource Hierarchy](#2-iam-e-resource-hierarchy)
3. [Networking — VPC](#3-networking--vpc)
4. [Compute — Compute Engine](#4-compute--compute-engine)
5. [Storage — Cloud Storage](#5-storage--cloud-storage)
6. [Database](#6-database)
7. [Serverless](#7-serverless)
8. [Containers — GKE](#8-containers--gke)
9. [Monitoring e Observability](#9-monitoring-e-observability)
10. [Security](#10-security)
11. [Infrastructure as Code](#11-infrastructure-as-code)
12. [Cost Management](#12-cost-management)
13. [Best Practices](#13-best-practices)

---

## 1. Panoramica dell'Infrastruttura Globale GCP

Google Cloud Platform e il provider cloud di Google, terzo per quota di mercato globale dopo AWS e Azure. Si distingue per la rete globale privata di Google (una delle reti piu estese al mondo), le capacita avanzate di analisi dati e machine learning, e il ruolo fondante nell'ecosistema Kubernetes. GCP condivide l'infrastruttura fisica con i servizi consumer di Google (Search, YouTube, Gmail), il che garantisce una scala e un'affidabilita comprovate.

### Regions (Regioni)

Una **Region** GCP e un'area geografica indipendente che ospita le risorse cloud. Ogni regione e identificata da un nome composto da continente, area e numero progressivo, ad esempio `europe-west1` (Belgio), `europe-west8` (Milano), `us-central1` (Iowa). GCP opera in oltre 40 regioni distribuite su tutti i continenti, con una copertura particolarmente forte in Europa, Nord America e Asia-Pacifico. La scelta della regione dipende da:

- **Conformita normativa**: il GDPR e altre normative europee richiedono che i dati risiedano in giurisdizioni specifiche. Le regioni `europe-west1` (Belgio), `europe-west3` (Francoforte), `europe-west4` (Paesi Bassi), `europe-west6` (Zurigo) e `europe-west8` (Milano) sono scelte tipiche per workload europei soggetti a vincoli di residenza dati.
- **Latenza**: si seleziona la regione piu vicina agli utenti finali. Google fornisce lo strumento GCP Ping per misurare la latenza verso ciascuna regione.
- **Disponibilita dei servizi**: non tutti i servizi sono disponibili in tutte le regioni. BigQuery, ad esempio, e disponibile in tutte le regioni, mentre servizi piu recenti possono essere limitati alle regioni principali come `us-central1` o `europe-west1`.
- **Costo**: i prezzi variano tra regioni. Le regioni negli Stati Uniti (Iowa, Oregon) tendono a essere le meno costose, seguite dall'Europa, con l'Asia e il Sud America generalmente piu care.

A differenza di AWS, GCP non adotta il concetto di paired regions per il disaster recovery. La strategia di replica geografica si basa su risorse **multi-regionali** o **dual-region** configurate esplicitamente dall'utente.

### Zones (Zone di Disponibilita)

Ogni regione contiene almeno tre **Zones** (zone). Ogni zona e un deployment isolato dell'infrastruttura Google all'interno della regione, con alimentazione, raffreddamento e networking indipendenti. Le zone sono identificate aggiungendo una lettera alla regione: `us-central1-a`, `us-central1-b`, `us-central1-c`, `us-central1-f`.

La distribuzione delle risorse su piu zone garantisce alta disponibilita: se una zona diventa irraggiungibile, le istanze nelle altre continuano a operare. Servizi come Managed Instance Groups, Cloud SQL con HA e GKE con cluster regionali sfruttano nativamente la distribuzione multi-zona.

| Confronto | AWS | Azure | GCP |
|-----------|-----|-------|-----|
| Area geografica | Region (es. `eu-west-1`) | Region (es. `West Europe`) | Region (es. `europe-west1`) |
| Isolamento fisico | Availability Zone (es. `eu-west-1a`) | Availability Zone (es. Zone 1) | Zone (es. `europe-west1-b`) |
| Min zone per regione | 2 (tipicamente 3) | 3 (dove supportate) | 3 |
| Naming convention | `{area}-{dir}-{num}{lettera}` | Nome descrittivo | `{continente}-{dir}{num}-{lettera}` |

### Multi-Region e Dual-Region

Alcuni servizi GCP supportano configurazioni **multi-region** che replicano automaticamente i dati su piu regioni all'interno di un'area geografica. Ad esempio, Cloud Storage offre le location multi-region `US`, `EU` e `ASIA`, che distribuiscono i dati su almeno due regioni per garantire alta disponibilita e bassa latenza. Le **dual-region** consentono di scegliere due regioni specifiche per la replica, ad esempio `europe-west1` e `europe-west4`.

### Network Tiers — Premium vs Standard

GCP offre due livelli di networking, una differenziazione unica rispetto ad AWS e Azure:

- **Premium Tier** (default): il traffico transita sulla rete privata globale di Google dal punto di presenza piu vicino all'utente fino alla regione di destinazione. La rete di Google conta oltre 180 punti di presenza e oltre 200.000 km di cavi in fibra ottica (comprendendo i cavi sottomarini di proprieta). Il Premium Tier offre latenza piu bassa, perdita di pacchetti inferiore e throughput superiore. Supporta Global Load Balancing con un singolo IP anycast.
- **Standard Tier**: il traffico transita sulla rete pubblica Internet per la maggior parte del percorso, entrando nella rete di Google solo nella regione di destinazione. Costi di egress inferiori (circa 24-33% in meno rispetto al Premium Tier), ma latenza e affidabilita superiori non garantite. Il Load Balancing e disponibile solo a livello regionale.

```bash
# Creare un indirizzo IP con Premium Tier (default)
gcloud compute addresses create ip-premium \
    --region=europe-west1 \
    --network-tier=PREMIUM

# Creare un indirizzo IP con Standard Tier
gcloud compute addresses create ip-standard \
    --region=europe-west1 \
    --network-tier=STANDARD
```

### Points of Presence (PoP) e Cloud CDN

I **Points of Presence** (PoP) di Google sono localizzati in oltre 180 sedi in 40+ paesi. Questi PoP servono il traffico di **Cloud CDN**, il servizio di content delivery di GCP che utilizza la stessa infrastruttura edge di YouTube e Google Search. Cloud CDN si integra nativamente con il Global HTTP(S) Load Balancer e supporta cache invalidation, signed URLs e signed cookies.

---

## 2. IAM e Resource Hierarchy

La gestione delle identita e degli accessi in GCP si basa su un modello gerarchico di risorse e su un sistema di policy IAM che si propaga lungo la gerarchia. Questo modello e concettualmente diverso da AWS (basato su account isolati con AWS Organizations) e da Azure (basato su Management Groups, Subscription, Resource Groups).

### Resource Hierarchy (Gerarchia delle Risorse)

La gerarchia delle risorse GCP si compone di quattro livelli:

```
Organization (esempio: mia-azienda.com)
├── Folder "Produzione"
│   ├── Project "prod-webapp" (project ID: prod-webapp-a1b2c3)
│   │   ├── Compute Engine instances
│   │   ├── Cloud SQL databases
│   │   └── Cloud Storage buckets
│   └── Project "prod-data" (project ID: prod-data-d4e5f6)
│       ├── BigQuery datasets
│       └── Pub/Sub topics
├── Folder "Sviluppo"
│   ├── Project "dev-webapp" (project ID: dev-webapp-g7h8i9)
│   └── Project "dev-experiments"
└── Folder "Shared Services"
    ├── Project "shared-networking"
    └── Project "shared-monitoring"
```

- **Organization**: il nodo radice, associato a un dominio Google Workspace o Cloud Identity. E l'entita a cui si applicano le policy piu ampie. Ogni dominio puo avere una sola Organization.
- **Folders**: contenitori logici per raggruppare progetti. Possono essere annidati fino a 10 livelli. Utili per riflettere la struttura organizzativa (per reparto, ambiente, regione geografica).
- **Projects**: l'unita fondamentale di organizzazione in GCP. Ogni risorsa (VM, bucket, database) appartiene a esattamente un progetto. Ogni progetto ha un **project ID** (globalmente unico, immutabile), un **project name** (modificabile) e un **project number** (numerico, assegnato automaticamente). Il progetto e anche il confine di fatturazione e di quota.
- **Resources**: le risorse individuali (istanze Compute Engine, bucket Cloud Storage, cluster GKE, ecc.).

### IAM Policies e Bindings

Le **IAM policies** definiscono chi (member) ha quale ruolo (role) su quale risorsa. Le policy si applicano a qualsiasi livello della gerarchia e vengono ereditate dai livelli inferiori. Una policy e un insieme di **bindings** che collegano uno o piu **members** a un **role**.

```json
{
  "bindings": [
    {
      "role": "roles/compute.admin",
      "members": [
        "user:admin@mia-azienda.com",
        "group:devops-team@mia-azienda.com"
      ]
    },
    {
      "role": "roles/storage.objectViewer",
      "members": [
        "serviceAccount:app-backend@prod-webapp-a1b2c3.iam.gserviceaccount.com"
      ],
      "condition": {
        "title": "solo_orario_lavorativo",
        "expression": "request.time.getHours('Europe/Rome') >= 8 && request.time.getHours('Europe/Rome') <= 18"
      }
    }
  ]
}
```

I **members** possono essere: `user:` (account Google), `serviceAccount:` (service account), `group:` (gruppo Google), `domain:` (intero dominio) o `allUsers`/`allAuthenticatedUsers` (pubblico).

### Tipi di Ruoli

GCP definisce tre categorie di ruoli:

- **Basic roles** (ex primitive roles): `Owner`, `Editor`, `Viewer`. Concedono permessi molto ampi su tutte le risorse del progetto. Da evitare in produzione per la violazione del principio del least privilege.
- **Predefined roles**: ruoli definiti da Google per ogni servizio, con permessi granulari. Ad esempio, `roles/compute.instanceAdmin.v1` consente la gestione delle istanze Compute Engine senza accesso ad altri servizi. Esistono centinaia di ruoli predefiniti.
- **Custom roles**: ruoli definiti dall'utente con un set specifico di permessi. Utili quando i ruoli predefiniti sono troppo ampi o troppo restrittivi. Possono essere creati a livello di Organization o di Project.

```bash
# Assegnare un ruolo predefinito a un utente
gcloud projects add-iam-policy-binding prod-webapp-a1b2c3 \
    --member="user:sviluppatore@mia-azienda.com" \
    --role="roles/compute.instanceAdmin.v1"

# Creare un ruolo personalizzato
gcloud iam roles create customStorageReader \
    --project=prod-webapp-a1b2c3 \
    --title="Custom Storage Reader" \
    --permissions="storage.objects.get,storage.objects.list,storage.buckets.list" \
    --stage="GA"

# Visualizzare la policy IAM di un progetto
gcloud projects get-iam-policy prod-webapp-a1b2c3 --format=json
```

### Service Accounts

I **Service Accounts** sono identita utilizzate dalle applicazioni e dai servizi per autenticarsi verso le API GCP. Ogni service account ha un indirizzo email nel formato `{nome}@{project-id}.iam.gserviceaccount.com`. Esistono tre tipi:

- **Default service accounts**: creati automaticamente quando si abilitano determinati servizi (ad esempio, il Compute Engine default service account `{project-number}-compute@developer.gserviceaccount.com`). Hanno tipicamente permessi troppo ampi (Editor) e non dovrebbero essere utilizzati in produzione.
- **User-managed service accounts**: creati esplicitamente dall'utente per applicazioni specifiche, con permessi granulari.
- **Google-managed service accounts**: utilizzati internamente dai servizi GCP (ad esempio, il Google APIs Service Agent).

```bash
# Creare un service account
gcloud iam service-accounts create sa-backend \
    --display-name="Backend Application SA" \
    --project=prod-webapp-a1b2c3

# Creare e scaricare una chiave (da evitare se possibile, preferire Workload Identity)
gcloud iam service-accounts keys create key.json \
    --iam-account=sa-backend@prod-webapp-a1b2c3.iam.gserviceaccount.com

# Assegnare un ruolo al service account
gcloud projects add-iam-policy-binding prod-webapp-a1b2c3 \
    --member="serviceAccount:sa-backend@prod-webapp-a1b2c3.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
```

### Workload Identity Federation

**Workload Identity Federation** consente ai workload esterni (AWS, Azure, GitHub Actions, GitLab CI, OIDC/SAML provider) di accedere alle risorse GCP senza chiavi di service account. Il workload esterno si autentica con il proprio identity provider e scambia il token per credenziali GCP temporanee. Questo elimina la necessita di gestire e ruotare chiavi JSON, riducendo significativamente il rischio di sicurezza.

```bash
# Creare un Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
    --location="global" \
    --display-name="GitHub Actions Pool"

# Creare un provider OIDC per GitHub Actions
gcloud iam workload-identity-pools providers create-oidc github-provider \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"

# Consentire al workload di impersonare un service account
gcloud iam service-accounts add-iam-policy-binding \
    sa-deploy@prod-webapp-a1b2c3.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/{PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/mia-org/mio-repo"
```

### Organization Policies

Le **Organization Policies** sono vincoli che si applicano a livello di Organization, Folder o Project per imporre regole di governance. A differenza delle IAM policies (che definiscono chi puo fare cosa), le Organization Policies definiscono cosa puo essere fatto indipendentemente dall'identita. Esempi:

- `constraints/compute.vmExternalIpAccess`: limitare quali VM possono avere IP esterni.
- `constraints/iam.allowedPolicyMemberDomains`: restringere i domini da cui si possono aggiungere membri IAM.
- `constraints/gcp.resourceLocations`: limitare le regioni in cui si possono creare risorse (utile per conformita GDPR).

```bash
# Applicare un vincolo per limitare le regioni consentite
gcloud resource-manager org-policies set-policy policy.yaml --organization=123456789

# policy.yaml
# constraint: constraints/gcp.resourceLocations
# listPolicy:
#   allowedValues:
#     - in:europe-west1-locations
#     - in:europe-west3-locations
#     - in:europe-west8-locations
```

---

## 3. Networking — VPC

Il networking in GCP presenta differenze architetturali significative rispetto ad AWS e Azure. La piu rilevante e che le **VPC in GCP sono risorse globali**, non regionali. Una singola VPC puo contenere subnet in qualsiasi regione, semplificando le architetture multi-region senza la necessita di peering tra VPC della stessa organizzazione.

### VPC Networks — Auto-Mode vs Custom-Mode

GCP offre due modalita di creazione VPC:

- **Auto-mode**: la VPC crea automaticamente una subnet in ogni regione con un range CIDR predefinito dalla rete `10.128.0.0/9`. Ogni subnet ha un range `/20` (4096 indirizzi). Utile per prototipi e ambienti di test, ma sconsigliata in produzione perche i range non sono personalizzabili e possono causare conflitti in scenari di peering o VPN.
- **Custom-mode**: nessuna subnet viene creata automaticamente. L'utente definisce esplicitamente le subnet con range CIDR personalizzati. Raccomandata per ambienti di produzione.

```bash
# Creare una VPC custom-mode
gcloud compute networks create vpc-produzione \
    --subnet-mode=custom \
    --bgp-routing-mode=global

# Creare subnet in regioni diverse (la VPC e globale)
gcloud compute networks subnets create subnet-web-eu \
    --network=vpc-produzione \
    --region=europe-west1 \
    --range=10.10.0.0/24

gcloud compute networks subnets create subnet-app-us \
    --network=vpc-produzione \
    --region=us-central1 \
    --range=10.20.0.0/24

# Abilitare Private Google Access sulla subnet
gcloud compute networks subnets update subnet-web-eu \
    --region=europe-west1 \
    --enable-private-ip-google-access
```

### Firewall Rules

Le **Firewall Rules** in GCP operano a livello di VPC (non di subnet come in AWS con i Network ACL). Sono stateful e supportano sia regole di ingress che di egress. Ogni regola ha una **priority** (0-65535, dove 0 e la massima priorita) e si applica tramite **target tags**, **service accounts** o a tutte le istanze della VPC.

```bash
# Consentire SSH da un range specifico
gcloud compute firewall-rules create allow-ssh \
    --network=vpc-produzione \
    --allow=tcp:22 \
    --source-ranges=203.0.113.0/24 \
    --target-tags=bastion \
    --priority=1000

# Consentire il traffico HTTP interno
gcloud compute firewall-rules create allow-internal-http \
    --network=vpc-produzione \
    --allow=tcp:80,tcp:443 \
    --source-ranges=10.10.0.0/16 \
    --target-tags=web-server \
    --priority=1000

# Negare tutto il traffico in egress verso Internet (default allow viene sovrascritto)
gcloud compute firewall-rules create deny-all-egress \
    --network=vpc-produzione \
    --direction=EGRESS \
    --action=DENY \
    --rules=all \
    --destination-ranges=0.0.0.0/0 \
    --priority=65534
```

Le regole firewall implicite di ogni VPC sono: deny all ingress (priorita 65535), allow all egress (priorita 65535). Queste non possono essere eliminate ma possono essere sovrascritte con regole a priorita piu alta (numero inferiore).

### Cloud NAT

**Cloud NAT** (Network Address Translation) consente alle istanze senza IP pubblico di accedere a Internet per il download di aggiornamenti, l'accesso ad API esterne e l'invio di richieste in uscita, senza esporre le istanze a traffico in ingresso da Internet. Cloud NAT opera a livello di regione ed e configurato tramite un **Cloud Router**.

```bash
# Creare un Cloud Router
gcloud compute routers create router-eu \
    --network=vpc-produzione \
    --region=europe-west1

# Configurare Cloud NAT
gcloud compute routers nats create nat-eu \
    --router=router-eu \
    --region=europe-west1 \
    --nat-all-subnet-ip-ranges \
    --auto-allocate-nat-external-ips
```

### Cloud VPN — Classic e HA

GCP offre due tipologie di VPN per connettere reti on-premises alla VPC:

- **Classic VPN**: un singolo tunnel IPsec con SLA del 99.9%. Supporta routing statico e dinamico (BGP). Bandwidth fino a 3 Gbps per tunnel.
- **HA VPN**: due tunnel IPsec con SLA del 99.99% quando configurato con ridondanza completa (due interfacce e due tunnel per gateway). Supporta solo routing dinamico (BGP). Ogni interfaccia supporta fino a 3 Gbps.

```bash
# Creare un HA VPN Gateway
gcloud compute vpn-gateways create vpn-gw-eu \
    --network=vpc-produzione \
    --region=europe-west1

# Creare un External VPN Gateway (peer on-premises con due interfacce)
gcloud compute external-vpn-gateways create peer-onprem \
    --interfaces=0=203.0.113.1,1=203.0.113.2

# Creare i tunnel VPN
gcloud compute vpn-tunnels create tunnel-0 \
    --region=europe-west1 \
    --vpn-gateway=vpn-gw-eu \
    --peer-external-gateway=peer-onprem \
    --peer-external-gateway-interface=0 \
    --ike-version=2 \
    --shared-secret=chiave_condivisa_sicura \
    --router=router-eu \
    --vpn-gateway-interface=0
```

### Cloud Interconnect

**Cloud Interconnect** fornisce connettivita dedicata ad alta velocita tra la rete on-premises e la VPC GCP:

- **Dedicated Interconnect**: connessione fisica diretta ai punti di peering di Google. Capacita di 10 Gbps o 100 Gbps per link, con possibilita di aggregare piu link (LACP). SLA del 99.99% con configurazione ridondante. Richiede che l'infrastruttura on-premises sia co-locata in un punto di peering Google.
- **Partner Interconnect**: connessione attraverso un provider di servizi di rete partner di Google. Capacita da 50 Mbps a 50 Gbps. Adatto quando non si dispone di co-locazione presso un punto di peering Google.

### Shared VPC e VPC Peering

- **Shared VPC**: consente di condividere una VPC (host project) con altri progetti (service projects) nella stessa Organization. Le risorse nei service projects utilizzano le subnet della Shared VPC. Centralizza la gestione della rete mantenendo separata la gestione delle risorse. E il modello raccomandato per organizzazioni multi-progetto.
- **VPC Network Peering**: connette due VPC (anche in organizzazioni diverse) consentendo la comunicazione tramite IP privati. Non transitivo (A peered con B e B peered con C non implica comunicazione tra A e C). Non supporta range CIDR sovrapposti.

```bash
# Abilitare Shared VPC nel host project
gcloud compute shared-vpc enable host-project-id

# Associare un service project
gcloud compute shared-vpc associated-projects add service-project-id \
    --host-project=host-project-id

# Creare VPC Peering
gcloud compute networks peerings create peer-ab \
    --network=vpc-a \
    --peer-network=vpc-b \
    --peer-project=progetto-b
```

### Private Google Access e Private Service Connect

**Private Google Access** consente alle istanze con solo IP privato di accedere alle API e ai servizi Google (Cloud Storage, BigQuery, Container Registry) senza transitare su Internet. Si abilita a livello di subnet.

**Private Service Connect** fornisce endpoint privati per accedere ai servizi Google o ai servizi pubblicati da altri produttori, con un indirizzo IP interno nella VPC del consumer. Offre maggiore controllo rispetto a Private Google Access, includendo DNS automatico e firewall granulare.

### Private Service Connect — Architettura Avanzata

Private Service Connect (PSC) opera secondo un modello **producer-consumer**. Il **producer** pubblica un servizio tramite un **Service Attachment** associato a un Internal Load Balancer. Il **consumer** crea un **PSC Endpoint** (un forwarding rule con un indirizzo IP interno) nella propria VPC che si connette al Service Attachment del producer. Questo modello consente la comunicazione privata tra VPC diverse — anche in organizzazioni diverse — senza VPC peering, VPN o IP pubblici.

PSC supporta due modalita principali:

- **PSC per Google APIs**: consente l'accesso alle API Google (Cloud Storage, BigQuery, Cloud SQL, Vertex AI) tramite un indirizzo IP interno dedicato nella VPC del consumer, con DNS automatico e controllo granulare tramite firewall rules. Sostituisce Private Google Access per scenari che richiedono maggiore controllo.
- **PSC per servizi pubblicati**: consente ai producer (interni o di terze parti) di esporre servizi tramite Service Attachment. Il consumer si connette tramite un PSC Endpoint senza conoscere l'infrastruttura del producer.

```bash
# Creare un PSC Endpoint per accedere alle Google APIs
gcloud compute addresses create psc-google-apis \
    --region=europe-west1 \
    --subnet=subnet-web-eu \
    --addresses=10.10.0.100

gcloud compute forwarding-rules create psc-google-apis-fwd \
    --region=europe-west1 \
    --network=vpc-produzione \
    --address=psc-google-apis \
    --target-google-apis-bundle=all-apis

# Creare un Service Attachment (lato producer)
gcloud compute service-attachments create sa-internal-api \
    --region=europe-west1 \
    --producer-forwarding-rule=ilb-internal-api \
    --nat-subnets=subnet-psc-nat \
    --connection-preference=ACCEPT_MANUAL \
    --consumer-accept-list=consumer-project-id=5
```

### Cloud CDN — Configurazione Avanzata

**Cloud CDN** utilizza i PoP globali di Google per distribuire contenuti con bassa latenza. Si integra nativamente con il **Global External HTTP(S) Load Balancer** e supporta diverse modalita di caching:

- **Cache modes**: `CACHE_ALL_STATIC` (cache automatica per risorse statiche basata su Content-Type), `USE_ORIGIN_HEADERS` (rispetta le direttive Cache-Control dell'origin), `FORCE_CACHE_ALL` (cache forzata per tutte le risposte con TTL configurabile).
- **Cache keys**: configurabili per includere o escludere query string parameters, headers HTTP e cookies specifici. Utile per evitare cache pollution e ottimizzare l'hit ratio.
- **Signed URLs e Signed Cookies**: accesso temporaneo a contenuti protetti tramite firme crittografiche. I Signed Cookies sono preferibili quando si protegge un insieme di risorse piuttosto che un singolo URL.
- **Cache invalidation**: invalidazione per URL pattern o tag. Le invalidazioni si propagano globalmente in pochi secondi.

```bash
# Abilitare Cloud CDN su un backend service
gcloud compute backend-services update backend-web \
    --enable-cdn \
    --cache-mode=CACHE_ALL_STATIC \
    --default-ttl=3600 \
    --max-ttl=86400 \
    --client-ttl=3600 \
    --global

# Invalidare la cache per un path specifico
gcloud compute url-maps invalidate-cdn-cache lb-web \
    --path="/static/*" \
    --global
```

### Cloud DNS

**Cloud DNS** e il servizio DNS gestito ad alte prestazioni di GCP, con SLA del 100% di disponibilita. Supporta zone pubbliche e private, DNSSEC, routing policies (geolocation, weighted round robin, failover) e integrazione nativa con Private Service Connect per la risoluzione DNS automatica degli endpoint privati.

```bash
# Creare una zona DNS privata
gcloud dns managed-zones create zona-interna \
    --dns-name="internal.mia-azienda.com." \
    --visibility=private \
    --networks=vpc-produzione \
    --description="Zona DNS interna"

# Creare un record A
gcloud dns record-sets create api.internal.mia-azienda.com. \
    --zone=zona-interna \
    --type=A \
    --ttl=300 \
    --rrdatas="10.10.0.50"
```

### Network Intelligence Center

**Network Intelligence Center** fornisce strumenti di visibilita e diagnostica per la rete GCP:

- **Network Topology**: visualizzazione grafica della topologia di rete con metriche di traffico in tempo reale tra regioni, zone e risorse.
- **Connectivity Tests**: test di raggiungibilita tra due endpoint che analizza il percorso dei pacchetti attraverso firewall rules, route e NAT, identificando il punto esatto di blocco in caso di problemi.
- **Performance Dashboard**: metriche di latenza e perdita di pacchetti tra regioni GCP e tra GCP e Internet.
- **Firewall Insights**: analisi dell'utilizzo delle firewall rules, identificazione di regole shadowed (mai raggiunte perche sovrascritte da regole a priorita piu alta) e regole non utilizzate.

```bash
# Eseguire un connectivity test
gcloud network-management connectivity-tests create test-web-to-db \
    --source-instance=projects/progetto/zones/europe-west1-b/instances/web-server-1 \
    --destination-instance=projects/progetto/zones/europe-west1-c/instances/db-server \
    --destination-port=5432 \
    --protocol=TCP
```

---

## 4. Compute — Compute Engine

**Compute Engine** e il servizio IaaS di GCP per la creazione e gestione di macchine virtuali. Equivalente funzionale di Amazon EC2 e Azure Virtual Machines.

### Machine Types (Famiglie di Macchine)

GCP organizza le macchine virtuali in famiglie ottimizzate per workload diversi:

| Famiglia | Serie | Caratteristiche | Casi d'uso |
|----------|-------|-----------------|------------|
| **General-purpose** | E2, N2, N2D, N1, C3 | Bilanciamento CPU/memoria, rapporto 1:4 GB | Web server, app server, database piccoli, ambienti dev |
| **Compute-optimized** | C2, C2D, H3 | CPU ad alta frequenza (fino a 3.8 GHz), rapporto 1:4 GB | HPC, gaming, batch processing, media transcoding |
| **Memory-optimized** | M1, M2, M3 | Fino a 12 TB di RAM, rapporto 1:14+ GB | SAP HANA, database in-memory, analytics in-memory |
| **Accelerator-optimized** | A2, A3, G2 | GPU NVIDIA (A100, H100, L4) | ML training/inference, rendering, simulazione scientifica |
| **Storage-optimized** | Z3 | SSD locali ad altissime prestazioni | Database ad alte IOPS, Elasticsearch |

La serie **E2** supporta anche le **Shared-core machine types** (`e2-micro`, `e2-small`, `e2-medium`) con CPU condivisa e costi molto bassi, ideali per microservizi leggeri e ambienti di sviluppo.

GCP consente inoltre la creazione di **Custom machine types**, dove l'utente specifica il numero esatto di vCPU e la quantita di memoria, ottimizzando il rapporto costo/prestazioni per workload specifici.

```bash
# Creare una VM con machine type predefinito
gcloud compute instances create web-server-1 \
    --zone=europe-west1-b \
    --machine-type=e2-standard-4 \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-balanced \
    --tags=web-server \
    --metadata=startup-script='#!/bin/bash
apt-get update && apt-get install -y nginx
systemctl enable nginx && systemctl start nginx'

# Creare una VM con custom machine type (6 vCPU, 20 GB RAM)
gcloud compute instances create custom-vm \
    --zone=europe-west1-b \
    --custom-cpu=6 \
    --custom-memory=20GB \
    --image-family=ubuntu-2404-lts-amd64 \
    --image-project=ubuntu-os-cloud
```

### Preemptible VMs e Spot VMs

- **Preemptible VMs** (legacy): istanze a basso costo (60-91% di sconto) che possono essere terminate da Google in qualsiasi momento con un preavviso di 30 secondi. Durata massima di 24 ore. Nessuno SLA di disponibilita.
- **Spot VMs**: evoluzione delle Preemptible VMs. Stesso pricing, ma senza il limite di 24 ore. Possono essere terminate in qualsiasi momento. Supportano provisioning model dinamico. Raccomandate al posto delle Preemptible per nuovi workload.

Entrambe sono adatte per workload fault-tolerant: batch processing, rendering, CI/CD pipelines, data analytics.

```bash
# Creare una Spot VM
gcloud compute instances create batch-worker \
    --zone=us-central1-a \
    --machine-type=c2-standard-8 \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --image-family=debian-12 \
    --image-project=debian-cloud
```

### Instance Templates e Managed Instance Groups (MIG)

Un **Instance Template** definisce la configurazione di una VM (machine type, immagine, disco, rete, metadata) e viene utilizzato come blueprint per la creazione di istanze, sia individualmente che all'interno di Instance Groups.

Un **Managed Instance Group** (MIG) gestisce un gruppo di istanze identiche create da un Instance Template. I MIG supportano:

- **Autoscaling**: scalabilita orizzontale automatica basata su CPU, memoria, metriche Cloud Monitoring o capacita del load balancer.
- **Autohealing**: riavvio automatico delle istanze non sane (verificato tramite health checks).
- **Rolling updates**: aggiornamenti progressivi senza downtime.
- **Regional MIG**: distribuzione automatica delle istanze su piu zone nella stessa regione per alta disponibilita.

```bash
# Creare un Instance Template
gcloud compute instance-templates create tmpl-web-v1 \
    --machine-type=e2-standard-2 \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=20GB \
    --tags=web-server \
    --metadata=startup-script='#!/bin/bash
apt-get update && apt-get install -y nginx'

# Creare un Regional Managed Instance Group
gcloud compute instance-groups managed create mig-web \
    --template=tmpl-web-v1 \
    --size=3 \
    --region=europe-west1 \
    --zones=europe-west1-b,europe-west1-c,europe-west1-d

# Configurare autoscaling
gcloud compute instance-groups managed set-autoscaling mig-web \
    --region=europe-west1 \
    --min-num-replicas=2 \
    --max-num-replicas=10 \
    --target-cpu-utilization=0.70 \
    --cool-down-period=90
```

### Sole-Tenant Nodes

I **Sole-Tenant Nodes** sono server fisici dedicati esclusivamente al workload del cliente. Nessun'altra organizzazione condivide lo stesso hardware. Utili per requisiti di conformita (licenze software bring-your-own-license, isolamento hardware per dati sensibili, HIPAA, PCI DSS).

### OS Images e Disk Types

GCP fornisce immagini pubbliche per i principali sistemi operativi (Debian, Ubuntu, CentOS, RHEL, SUSE, Windows Server) e supporta immagini personalizzate. I tipi di disco disponibili sono:

| Tipo disco | IOPS (lettura) | Throughput | Uso |
|------------|----------------|------------|-----|
| **pd-standard** (HDD) | 7.500 | 1.200 MB/s | Backup, storage economico |
| **pd-balanced** (SSD) | 80.000 | 1.200 MB/s | Workload bilanciato costo/prestazioni |
| **pd-ssd** (SSD) | 100.000 | 1.200 MB/s | Database, workload ad alte IOPS |
| **pd-extreme** (SSD) | 120.000 | 2.200 MB/s | Database mission-critical, SAP HANA |
| **Local SSD** | 900.000 | 9.600 MB/s | Cache, storage temporaneo (dati non persistenti) |
| **Hyperdisk Balanced** | 120.000 | 2.400 MB/s | Workload flessibili con IOPS e throughput configurabili |

---

## 5. Storage — Cloud Storage

**Cloud Storage** e il servizio di object storage di GCP, equivalente di Amazon S3 e Azure Blob Storage. Offre storage durevole (99.999999999% durabilita, 11 nines), scalabile e accessibile tramite API REST, librerie client, gsutil CLI e la Console.

### Storage Classes

Cloud Storage definisce quattro classi di storage con costi e SLA diversi:

| Classe | SLA disponibilita | Durata minima | Costo storage (US) | Caso d'uso |
|--------|-------------------|---------------|---------------------|------------|
| **Standard** | 99.95% (regionale), 99.99% (multi-region) | Nessuna | ~$0.020/GB/mese | Dati ad accesso frequente, siti web, streaming |
| **Nearline** | 99.0% | 30 giorni | ~$0.010/GB/mese | Backup, dati acceduti meno di una volta al mese |
| **Coldline** | 99.0% | 90 giorni | ~$0.004/GB/mese | Disaster recovery, dati acceduti meno di una volta a trimestre |
| **Archive** | 99.0% | 365 giorni | ~$0.0012/GB/mese | Archivi a lungo termine, conformita normativa |

Le classi Nearline, Coldline e Archive applicano costi di retrieval per ogni operazione di lettura, oltre a un costo di cancellazione anticipata se l'oggetto viene eliminato prima della durata minima.

### Buckets e Oggetti

Un **bucket** e il contenitore per gli oggetti. Il nome del bucket e globalmente unico in tutta la piattaforma GCP. La location del bucket determina dove i dati sono fisicamente archiviati:

- **Region**: una singola regione (es. `europe-west1`).
- **Dual-region**: due regioni specifiche (es. `europe-west1` + `europe-west4`).
- **Multi-region**: area geografica ampia (`EU`, `US`, `ASIA`).

```bash
# Creare un bucket regionale con classe Standard
gsutil mb -l europe-west1 -c standard gs://mio-bucket-produzione-2024

# Creare un bucket multi-region con classe Nearline
gsutil mb -l EU -c nearline gs://mio-bucket-backup-eu

# Caricare un file
gsutil cp /local/report.pdf gs://mio-bucket-produzione-2024/documenti/

# Caricare ricorsivamente una directory con parallelismo
gsutil -m cp -r /local/data/ gs://mio-bucket-produzione-2024/data/

# Sincronizzare una directory locale con il bucket
gsutil -m rsync -r /local/data/ gs://mio-bucket-produzione-2024/data/
```

### Lifecycle Policies

Le **Lifecycle Policies** automatizzano la gestione degli oggetti: transizione tra classi di storage, eliminazione automatica e modifica dell'ACL basata su condizioni temporali o di stato.

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30, "matchesStorageClass": ["STANDARD"]}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 90, "matchesStorageClass": ["NEARLINE"]}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
        "condition": {"age": 365, "matchesStorageClass": ["COLDLINE"]}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 1825}
      }
    ]
  }
}
```

```bash
# Applicare la lifecycle policy
gsutil lifecycle set lifecycle.json gs://mio-bucket-produzione-2024

# Visualizzare la lifecycle policy corrente
gsutil lifecycle get gs://mio-bucket-produzione-2024
```

### IAM vs ACL

Cloud Storage supporta due sistemi di controllo accesso:

- **IAM** (raccomandato): gestione degli accessi a livello di bucket tramite il modello IAM standard di GCP. Ruoli come `roles/storage.objectViewer`, `roles/storage.objectCreator`, `roles/storage.admin`. Consente l'uso di condizioni IAM.
- **ACL** (Access Control Lists): controllo granulare a livello di singolo oggetto. Modello legacy, piu complesso da gestire. Si puo abilitare **Uniform bucket-level access** per disabilitare le ACL e utilizzare esclusivamente IAM.

```bash
# Abilitare Uniform bucket-level access (disabilita ACL)
gsutil uniformbucketlevelaccess set on gs://mio-bucket-produzione-2024

# Concedere accesso in lettura a un service account
gsutil iam ch \
    serviceAccount:app@progetto.iam.gserviceaccount.com:objectViewer \
    gs://mio-bucket-produzione-2024
```

### Signed URLs e Signed Policy Documents

I **Signed URLs** consentono l'accesso temporaneo a un oggetto senza richiedere autenticazione Google. L'URL include una firma crittografica con scadenza configurabile. Utili per condivisione file, download da applicazioni client, upload diretto.

```bash
# Generare un Signed URL valido per 1 ora
gsutil signurl -d 1h key.json gs://mio-bucket-produzione-2024/documenti/report.pdf
```

### Versioning e Retention Policies

Il **Versioning** mantiene ogni versione di un oggetto. Quando un oggetto viene sovrascritto o eliminato, la versione precedente viene preservata. Utile per protezione contro eliminazioni accidentali e audit trail.

Le **Retention Policies** impediscono l'eliminazione o la sovrascrittura di oggetti per un periodo specificato. Possono essere bloccate (locked) per renderle immutabili, soddisfacendo requisiti di conformita come SEC 17a-4 o WORM (Write Once Read Many).

```bash
# Abilitare versioning
gsutil versioning set on gs://mio-bucket-produzione-2024

# Impostare una retention policy di 365 giorni
gsutil retention set 365d gs://mio-bucket-archivio-compliance

# Bloccare la retention policy (irreversibile)
gsutil retention lock gs://mio-bucket-archivio-compliance
```

### Storage Transfer Service

**Storage Transfer Service** consente trasferimenti schedulati e ricorrenti di dati verso Cloud Storage da fonti multiple: Amazon S3, Azure Blob Storage, URL HTTP(S), file system on-premises (tramite Transfer Service for on-premises data) o altri bucket Cloud Storage.

---

## 6. Database

GCP offre una gamma completa di servizi database gestiti, ciascuno ottimizzato per pattern di accesso e requisiti specifici.

### Cloud SQL

**Cloud SQL** e il servizio database relazionale completamente gestito, equivalente di Amazon RDS e Azure SQL Database. Supporta tre motori: **MySQL** (5.7, 8.0), **PostgreSQL** (12-16) e **SQL Server** (2017, 2019, 2022).

Cloud SQL gestisce automaticamente: backup, replica, patch del sistema operativo e del motore, failover e monitoraggio. Le istanze possono avere fino a 96 vCPU, 624 GB di RAM e 64 TB di storage.

```bash
# Creare un'istanza Cloud SQL PostgreSQL con HA
gcloud sql instances create db-produzione \
    --database-version=POSTGRES_16 \
    --tier=db-custom-4-16384 \
    --region=europe-west1 \
    --availability-type=REGIONAL \
    --storage-type=SSD \
    --storage-size=100GB \
    --storage-auto-increase \
    --backup-start-time=02:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --database-flags=max_connections=200,log_min_duration_statement=1000

# Creare una read replica
gcloud sql instances create db-produzione-replica \
    --master-instance-name=db-produzione \
    --region=europe-west1 \
    --tier=db-custom-2-8192 \
    --availability-type=ZONAL

# Connettersi tramite Cloud SQL Auth Proxy (raccomandato)
cloud-sql-proxy --port=5432 progetto:europe-west1:db-produzione
```

**High Availability**: la configurazione `REGIONAL` crea una replica standby in una zona diversa della stessa regione con failover automatico (tipicamente 60-120 secondi). Il failover e trasparente per l'applicazione se si utilizza l'IP privato o il Cloud SQL Auth Proxy.

### Cloud Spanner

**Cloud Spanner** e il database relazionale globalmente distribuito, con forte consistenza (linearizzabilita) e scalabilita orizzontale. Combina le garanzie ACID di un database relazionale con la scalabilita di un database NoSQL. E un servizio unico nel panorama cloud, senza equivalente diretto in AWS o Azure.

Caratteristiche principali:
- Scalabilita orizzontale illimitata con distribuzione automatica dei dati
- Forte consistenza globale tramite TrueTime (orologi atomici e GPS nei data center Google)
- SLA del 99.999% (five nines) per configurazioni multi-region
- Supporto SQL completo con transazioni ACID distribuite
- Costo elevato: a partire da circa $0.90/nodo/ora (minimo 1 nodo per istanza)

Cloud Spanner e indicato per applicazioni globali mission-critical: sistemi finanziari, inventario globale, gaming backends con milioni di utenti contemporanei.

### Firestore

**Firestore** e il database documentale NoSQL serverless, evoluzione di Cloud Datastore. Offre due modalita:

- **Native mode**: modello documentale con query in tempo reale, offline support e sincronizzazione automatica. Ideale per applicazioni mobile e web.
- **Datastore mode**: retrocompatibile con Cloud Datastore, senza real-time listeners. Adatto per workload server-side.

Firestore scala automaticamente, non richiede provisioning di capacita e offre forte consistenza. Supporta transazioni ACID, query composite con indici automatici e manual indexes.

### Bigtable

**Cloud Bigtable** e il database NoSQL wide-column ad alte prestazioni, progettato per workload con latenza nell'ordine dei millisecondi e throughput massivo. E lo stesso database che alimenta Google Search, Maps e Gmail. Equivalente funzionale di Apache HBase (con cui e API-compatibile) e paragonabile ad Amazon DynamoDB per casi d'uso time-series e IoT.

Caratteristiche: latenza sub-10ms per il 99th percentile, scalabilita lineare aggiungendo nodi, compatibilita con l'ecosistema Hadoop/HBase, integrazione nativa con Dataflow, Dataproc e BigQuery.

### Memorystore

**Memorystore** e il servizio di database in-memory completamente gestito:

- **Memorystore for Redis**: compatibile con il protocollo Redis OSS (versioni 5.0, 6.x, 7.x). Supporta Standard Tier (con replica per HA) e Basic Tier. Capacita fino a 300 GB per istanza.
- **Memorystore for Memcached**: cache distribuita compatibile con il protocollo Memcached. Ideale per caching di sessioni e risultati di query.

```bash
# Creare un'istanza Memorystore Redis con HA
gcloud redis instances create cache-prod \
    --region=europe-west1 \
    --tier=standard \
    --size=5 \
    --redis-version=redis_7_0 \
    --network=vpc-produzione
```

### AlloyDB

**AlloyDB for PostgreSQL** e il servizio database relazionale di nuova generazione, completamente compatibile con PostgreSQL ma con prestazioni significativamente superiori grazie al motore di storage proprietario di Google. Benchmark di Google riportano prestazioni 4x superiori a PostgreSQL standard per workload transazionali e 100x per query analitiche.

Caratteristiche: separazione compute/storage, storage distribuito con replica cross-zone automatica, columnar engine per analytics, integrazione con Vertex AI per query di machine learning direttamente nel database.

| Servizio | Tipo | Consistenza | Scalabilita | Caso d'uso |
|----------|------|-------------|-------------|------------|
| Cloud SQL | Relazionale gestito | Forte (singola istanza) | Verticale + read replicas | App tradizionali, CMS, ERP |
| Cloud Spanner | Relazionale distribuito | Forte globale | Orizzontale illimitata | Sistemi globali mission-critical |
| Firestore | Documentale NoSQL | Forte | Automatica serverless | Mobile, web, real-time |
| Bigtable | Wide-column NoSQL | Eventuale (singola riga: forte) | Orizzontale (nodi) | Time-series, IoT, analytics |
| AlloyDB | PostgreSQL-compatibile | Forte | Verticale + read pool | PostgreSQL ad alte prestazioni |
| Memorystore | In-memory (Redis/Memcached) | Dipende dalla configurazione | Verticale | Caching, sessioni |

### BigQuery — Approfondimento Avanzato

**BigQuery** e il data warehouse serverless di GCP, progettato per analisi SQL su dataset di scala petabyte. Si distingue nel panorama cloud per l'architettura di separazione completa tra storage e compute (Dremel + Colossus), il pricing serverless e le capacita native di machine learning.

#### Edizioni e Modello di Pricing

A partire dal 2023, BigQuery adotta un modello basato su **Editions** che sostituisce il precedente flat-rate pricing:

| Edizione | Caratteristiche | Prezzo indicativo slot/ora |
|----------|----------------|---------------------------|
| **Standard** | Baseline, nessun SLA garantito sulle query | ~$0.04/slot/ora |
| **Enterprise** | SLA 99.99%, CMEK, streaming avanzato, sottoscrizioni PITR | ~$0.06/slot/ora |
| **Enterprise Plus** | Tutto Enterprise + BI Engine incluso, sottoscrizioni ottimizzate | ~$0.10/slot/ora |

Ogni edizione supporta due modelli di consumo:

- **On-demand**: pagamento per TB di dati analizzati ($6.25/TB nelle regioni US). Ideale per workload sporadici e analisi esplorative. Il primo TB mensile e gratuito.
- **Slot-based (Capacity)**: acquisto di capacita di calcolo espressa in **slot**. Uno slot e un'unita di calcolo equivalente a circa 0.5 vCPU e 0.5 GB di RAM. I slot vengono acquistati tramite **Reservations** e assegnati a **Assignments** (progetti, folder o organizzazione). Supporta autoscaling: si definisce un baseline di slot garantiti e un massimo per gestire picchi di carico.

```bash
# Creare una reservation con autoscaling
bq mk --reservation \
    --project_id=progetto \
    --location=EU \
    --slots=100 \
    --edition=ENTERPRISE \
    --autoscale_max_slots=400 \
    reservation-prod

# Assegnare la reservation a un progetto
bq mk --reservation_assignment \
    --project_id=progetto \
    --location=EU \
    --reservation_id=reservation-prod \
    --assignee_id=prod-data-d4e5f6 \
    --assignee_type=PROJECT \
    --job_type=QUERY
```

#### BI Engine — Analisi Sub-Secondo

**BI Engine** e un servizio di accelerazione in-memory integrato in BigQuery che memorizza i dati frequentemente acceduti nella RAM per fornire risposte sub-secondo. Caratteristiche:

- Capacita configurabile da 1 GB a 100 GB per progetto/regione
- Accelerazione automatica senza modifiche alle query SQL
- Integrazione nativa con Looker, Looker Studio, Connected Sheets e strumenti BI di terze parti via ODBC/JDBC
- Preferential pricing incluso nell'edizione Enterprise Plus, oppure acquistabile separatamente
- Le tabelle candidate vengono selezionate automaticamente in base alla frequenza di accesso, oppure specificate manualmente tramite **Preferred Tables**

```bash
# Creare una BI Engine reservation
bq update --project_id=progetto \
    --location=EU \
    --bi_reservation_size=10GB

# Specificare tabelle preferite
bq update --project_id=progetto \
    --location=EU \
    --preferred_tables=progetto:dataset.tabella_vendite,progetto:dataset.tabella_prodotti
```

#### BigQuery ML (BQML) — Machine Learning in SQL

**BigQuery ML** consente di creare, addestrare e valutare modelli di machine learning direttamente in BigQuery utilizzando sintassi SQL standard, senza esportare dati o gestire infrastruttura ML separata.

Modelli supportati nativamente:
- **Linear regression** e **logistic regression**: per previsioni numeriche e classificazione binaria
- **K-means clustering**: segmentazione non supervisionata
- **Matrix factorization**: sistemi di raccomandazione
- **Time series** (ARIMA_PLUS): previsioni temporali con decomposizione automatica di trend, stagionalita e holiday effects
- **Boosted Tree** e **Random Forest**: modelli XGBoost integrati per classificazione e regressione complesse
- **Deep Neural Networks (DNN)**: reti neurali per pattern complessi
- **Importazione modelli TensorFlow e ONNX**: per utilizzare modelli addestrati esternamente

```sql
-- Creare un modello di previsione vendite con ARIMA_PLUS
CREATE OR REPLACE MODEL `progetto.dataset.modello_vendite`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'data_vendita',
  time_series_data_col = 'totale_vendite',
  time_series_id_col = 'categoria_prodotto',
  holiday_region = 'IT',
  auto_arima = TRUE,
  data_frequency = 'DAILY'
) AS
SELECT data_vendita, totale_vendite, categoria_prodotto
FROM `progetto.dataset.storico_vendite`
WHERE data_vendita >= '2023-01-01';

-- Generare previsioni per i prossimi 30 giorni
SELECT *
FROM ML.FORECAST(MODEL `progetto.dataset.modello_vendite`,
  STRUCT(30 AS horizon, 0.95 AS confidence_level));

-- Valutare le metriche del modello
SELECT *
FROM ML.EVALUATE(MODEL `progetto.dataset.modello_vendite`);
```

#### Streaming e Ingestione Dati

BigQuery supporta due meccanismi di ingestione in tempo reale:

- **Legacy Streaming API** (`insertAll`): inserimento riga per riga con buffer di deduplicazione. Costo basato sui byte inseriti (~$0.05/GB). Latenza tipica < 5 secondi per la disponibilita nelle query. Limite di 100.000 righe/secondo per tabella.
- **Storage Write API**: API di nuova generazione che sostituisce la legacy streaming. Supporta inserimento in batch e streaming con semantica exactly-once. Throughput superiore (fino a 3 GB/s per stream), costi inferiori e supporto per transazioni (commit/rollback di interi stream). Raccomandato per tutti i nuovi workload.

```bash
# Caricare dati in batch da Cloud Storage
bq load --source_format=PARQUET \
    --autodetect \
    progetto:dataset.tabella_eventi \
    gs://bucket-dati/eventi/2024/*.parquet

# Caricare dati in streaming via CLI (per test)
echo '{"user_id":"u123","evento":"click","timestamp":"2024-06-15T10:30:00Z"}' | \
    bq insert progetto:dataset.tabella_eventi
```

#### Materialized Views e Tabelle Partizionate

Le **Materialized Views** sono viste pre-calcolate che BigQuery mantiene aggiornate automaticamente. Le query che coinvolgono materialized views vengono automaticamente riscritte per utilizzare i dati pre-aggregati, riducendo i costi di scansione e la latenza. Supportano filtri incrementali e aggregazioni.

Le **tabelle partizionate** dividono i dati in segmenti basati su una colonna temporale (giorno, mese, anno) o su un intervallo intero. Le query con filtri sulla colonna di partizionamento scansionano solo le partizioni rilevanti, riducendo drasticamente i costi e il tempo di esecuzione. Il **clustering** ordina i dati all'interno di ogni partizione per un massimo di quattro colonne, ottimizzando ulteriormente le scansioni per query con filtri su quelle colonne.

```sql
-- Creare una tabella partizionata e clusterizzata
CREATE TABLE `progetto.dataset.eventi_web`
(
  event_id STRING,
  user_id STRING,
  event_type STRING,
  country STRING,
  event_timestamp TIMESTAMP,
  payload JSON
)
PARTITION BY DATE(event_timestamp)
CLUSTER BY country, event_type
OPTIONS(
  partition_expiration_days = 365,
  require_partition_filter = TRUE
);

-- Creare una materialized view con aggregazione
CREATE MATERIALIZED VIEW `progetto.dataset.mv_eventi_giornalieri`
OPTIONS(enable_refresh = TRUE, refresh_interval_minutes = 30)
AS
SELECT
  DATE(event_timestamp) AS giorno,
  event_type,
  country,
  COUNT(*) AS totale_eventi,
  COUNT(DISTINCT user_id) AS utenti_unici
FROM `progetto.dataset.eventi_web`
GROUP BY giorno, event_type, country;
```

---

## 7. Serverless

GCP offre tre servizi serverless principali, ciascuno con un livello di astrazione e un modello di deployment diverso. La scelta dipende dal livello di controllo richiesto e dalla complessita dell'applicazione.

### Cloud Functions

**Cloud Functions** e il servizio FaaS (Function as a Service) di GCP, equivalente di AWS Lambda e Azure Functions. Permette di eseguire codice in risposta a eventi senza gestire server o infrastruttura.

**1st gen**: la versione originale. Supporta Node.js, Python, Go, Java, .NET, Ruby, PHP. Timeout massimo 540 secondi, memoria massima 8 GB, una richiesta per istanza (nessuna concorrenza).

**2nd gen**: basata su Cloud Run. Supporta concorrenza (fino a 1000 richieste per istanza), timeout fino a 60 minuti, traffic splitting, revisioni. Supporta gli stessi linguaggi della 1st gen con l'aggiunta di qualsiasi linguaggio tramite container custom.

```bash
# Deployare una Cloud Function 2nd gen (Python)
gcloud functions deploy process-upload \
    --gen2 \
    --region=europe-west1 \
    --runtime=python312 \
    --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
    --trigger-event-filters="bucket=mio-bucket-produzione-2024" \
    --entry-point=main \
    --memory=512MiB \
    --timeout=300s \
    --max-instances=100 \
    --min-instances=1 \
    --service-account=sa-functions@progetto.iam.gserviceaccount.com \
    --source=./src/

# Deployare una Cloud Function 2nd gen con trigger HTTP
gcloud functions deploy api-handler \
    --gen2 \
    --region=europe-west1 \
    --runtime=nodejs20 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point=handleRequest \
    --memory=256MiB \
    --source=./functions/api/
```

### Cloud Run

**Cloud Run** e il servizio serverless per l'esecuzione di container. Accetta qualsiasi container Docker che ascolta su una porta HTTP. Non richiede un cluster Kubernetes e scala automaticamente a zero (nessun costo quando non ci sono richieste). Equivalente parziale di AWS Fargate (ma con scaling a zero) e Azure Container Apps.

Caratteristiche principali:
- Qualsiasi linguaggio e framework (e un container)
- Scaling automatico da 0 a migliaia di istanze
- Concurrency configurabile (fino a 1000 richieste per istanza)
- Traffic splitting tra revisioni (canary deployments)
- Integrazione con VPC Connector per accesso a risorse private
- Timeout fino a 60 minuti (3600 secondi)
- Supporto per gRPC, WebSocket e HTTP/2

```bash
# Deployare un container su Cloud Run
gcloud run deploy api-service \
    --image=europe-west1-docker.pkg.dev/progetto/repo/api:v1.2.0 \
    --region=europe-west1 \
    --platform=managed \
    --port=8080 \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=1 \
    --max-instances=50 \
    --concurrency=80 \
    --timeout=300 \
    --service-account=sa-api@progetto.iam.gserviceaccount.com \
    --set-env-vars="DB_HOST=10.10.0.3,ENVIRONMENT=production" \
    --vpc-connector=connector-eu \
    --allow-unauthenticated

# Dividere il traffico tra due revisioni (canary deployment)
gcloud run services update-traffic api-service \
    --region=europe-west1 \
    --to-revisions=api-service-v2=10,api-service-v1=90
```

### App Engine

**App Engine** e il PaaS originale di Google, lanciato nel 2008. Offre due ambienti:

- **Standard Environment**: supporta linguaggi specifici (Python, Java, Node.js, PHP, Ruby, Go) con scaling a zero e avvio rapido (millisecondi). Restrizioni sul runtime (no scritture su filesystem, no socket raw). Ideale per applicazioni web tradizionali.
- **Flexible Environment**: basato su container Docker, supporta qualsiasi linguaggio. Non scala a zero (minimo una istanza). Piu flessibile ma costi minimi piu alti. Equivalente funzionale di un PaaS gestito.

App Engine e un servizio regionale (non globale) con un singolo deployment per progetto. Per nuovi progetti, Cloud Run e generalmente preferito per la maggiore flessibilita, la portabilita dei container e l'assenza del lock-in specifico di App Engine.

| Caratteristica | Cloud Functions | Cloud Run | App Engine Standard |
|----------------|----------------|-----------|---------------------|
| Unita di deployment | Funzione | Container | Applicazione |
| Scaling a zero | Si (2nd gen) | Si | Si |
| Concurrency | Fino a 1000 (2nd gen) | Fino a 1000 | Automatica |
| Timeout massimo | 60 min (2nd gen) | 60 min | 10 min |
| Linguaggi | Predefiniti | Qualsiasi (container) | Predefiniti |
| Lock-in | Medio | Basso (standard container) | Alto |

### Cloud Run — Approfondimento Avanzato

#### Cloud Run Jobs

**Cloud Run Jobs** eseguono container fino al completamento senza ascoltare richieste HTTP. Sono progettati per workload batch, migrazioni dati, elaborazioni programmate e pipeline ETL. A differenza dei servizi Cloud Run, i Job terminano al completamento del container e non hanno un endpoint HTTP persistente.

Caratteristiche principali:
- **Task paralleli**: un Job puo eseguire fino a 10.000 task in parallelo, ciascuno con la propria istanza del container. Ogni task riceve un indice univoco tramite la variabile d'ambiente `CLOUD_RUN_TASK_INDEX`.
- **Retry policy**: tentativi configurabili per task falliti (fino a 10 retry per task). Il Job e considerato completato quando tutti i task terminano con successo.
- **Timeout**: fino a 24 ore per task (rispetto ai 60 minuti dei servizi).
- **Schedulazione**: integrazione nativa con Cloud Scheduler per esecuzioni ricorrenti (cron).

```bash
# Creare un Cloud Run Job
gcloud run jobs create batch-elaborazione \
    --image=europe-west1-docker.pkg.dev/progetto/repo/batch:v1.0 \
    --region=europe-west1 \
    --tasks=100 \
    --parallelism=10 \
    --max-retries=3 \
    --task-timeout=3600 \
    --memory=2Gi \
    --cpu=2 \
    --service-account=sa-batch@progetto.iam.gserviceaccount.com \
    --set-env-vars="BATCH_SIZE=1000,OUTPUT_BUCKET=gs://bucket-output"

# Eseguire il Job
gcloud run jobs execute batch-elaborazione --region=europe-west1

# Schedulare l'esecuzione giornaliera
gcloud scheduler jobs create http job-giornaliero \
    --location=europe-west1 \
    --schedule="0 2 * * *" \
    --uri="https://europe-west1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/progetto/jobs/batch-elaborazione:run" \
    --http-method=POST \
    --oauth-service-account-email=sa-scheduler@progetto.iam.gserviceaccount.com
```

#### Multi-Container (Sidecar)

Cloud Run supporta l'esecuzione di **fino a 10 container** nella stessa istanza, condividendo lo stesso namespace di rete e volumi in-memory. Questa funzionalita abilita il pattern sidecar senza la complessita di un cluster Kubernetes.

Casi d'uso tipici:
- **Proxy di autenticazione**: un sidecar gestisce OAuth2/mTLS, il container principale si concentra sulla logica applicativa.
- **Collettori di telemetria**: un sidecar OpenTelemetry Collector raccoglie metriche e trace e li invia a Cloud Monitoring o a backend esterni.
- **Adapter di protocollo**: un sidecar converte gRPC in HTTP o gestisce la serializzazione/deserializzazione.
- **Cache locale**: un sidecar Redis o Memcached per caching in-memory condiviso.

Vincoli: solo un container (il **container di ingress**) riceve il traffico HTTP esterno. I sidecar comunicano con il container principale via `localhost`. I sidecar non sono supportati per Cloud Run Jobs.

```yaml
# Configurazione multi-container con sidecar (service.yaml)
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: api-con-sidecar
spec:
  template:
    spec:
      containers:
        - image: europe-west1-docker.pkg.dev/progetto/repo/api:v2.0
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: shared-data
              mountPath: /shared
        - image: europe-west1-docker.pkg.dev/progetto/repo/otel-collector:latest
          env:
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "https://monitoring.googleapis.com"
          volumeMounts:
            - name: shared-data
              mountPath: /shared
      volumes:
        - name: shared-data
          emptyDir:
            medium: Memory
            sizeLimit: 256Mi
```

#### GPU su Cloud Run

Cloud Run supporta GPU **NVIDIA L4** per workload di inferenza AI/ML direttamente su container serverless, senza gestire cluster o nodi GPU. Questa funzionalita elimina la necessita di GKE per workload di inferenza che non richiedono orchestrazione complessa.

Vincoli e requisiti:
- Disponibile solo in regioni selezionate (`us-central1`, `europe-west1`, `asia-southeast1` tra le prime)
- Una GPU NVIDIA L4 per istanza (24 GB VRAM)
- Minimo 4 CPU e 16 GiB di memoria per istanza (8 CPU e 32 GiB raccomandati)
- Scaling a zero supportato, ma il cold start con GPU e piu lungo (30-90 secondi tipici per il caricamento del modello)
- Il container deve includere i driver NVIDIA CUDA compatibili

```bash
# Deployare un servizio Cloud Run con GPU
gcloud run deploy inference-llm \
    --image=europe-west1-docker.pkg.dev/progetto/repo/llm-server:v1.0 \
    --region=europe-west1 \
    --gpu=1 \
    --gpu-type=nvidia-l4 \
    --cpu=8 \
    --memory=32Gi \
    --max-instances=5 \
    --min-instances=1 \
    --no-cpu-throttling \
    --service-account=sa-ml@progetto.iam.gserviceaccount.com
```

#### Min Instances e Startup CPU Boost

L'opzione **min-instances** mantiene un numero minimo di istanze sempre pronte (warm), eliminando il cold start per i primi N utenti. Le istanze minime incorrono in costi anche senza traffico, ma a tariffa ridotta quando non elaborano richieste.

Lo **Startup CPU Boost** alloca temporaneamente CPU aggiuntive durante l'avvio del container (fino a 2x), accelerando il cold start per applicazioni con inizializzazione pesante (caricamento framework, connessioni a database, precompilazione JIT). Si disattiva automaticamente dopo l'avvio.

```bash
# Configurare min instances e startup CPU boost
gcloud run deploy api-service \
    --image=europe-west1-docker.pkg.dev/progetto/repo/api:v3.0 \
    --region=europe-west1 \
    --min-instances=2 \
    --max-instances=100 \
    --cpu-boost \
    --cpu=2 \
    --memory=1Gi
```

---

## 8. Containers — GKE

**Google Kubernetes Engine** (GKE) e il servizio managed Kubernetes di GCP. Dato che Google ha creato Kubernetes internamente (evoluzione del sistema Borg) e lo ha reso open source nel 2014, GKE e generalmente considerato il servizio Kubernetes gestito piu maturo e integrato tra i cloud provider.

### Architettura GKE

Un cluster GKE si compone di:
- **Control plane**: gestito interamente da Google. Include l'API server, etcd, scheduler e controller manager. SLA del 99.95% (Standard) o 99.9% (Autopilot). Non accessibile direttamente (nessun SSH ai nodi master).
- **Node pools**: gruppi di nodi worker (istanze Compute Engine) con la stessa configurazione. Ogni node pool puo avere un machine type, una versione di Kubernetes e impostazioni di autoscaling diverse.

### Autopilot vs Standard

GKE offre due modalita operative:

- **Standard**: l'utente gestisce i node pools, il machine type dei nodi, l'autoscaling e la configurazione dei nodi. Maggiore flessibilita e controllo. L'utente paga per le VM dei nodi indipendentemente dall'utilizzo effettivo.
- **Autopilot**: Google gestisce completamente l'infrastruttura dei nodi. L'utente definisce solo i workload (Pod). Google ottimizza automaticamente il dimensionamento dei nodi, applica best practices di sicurezza (nodi hardened, nessun accesso SSH), e fattura per le risorse richieste dai Pod (CPU, memoria, GPU, storage effimero) anziche per le VM sottostanti.

Autopilot e raccomandato per la maggior parte dei casi d'uso: riduce il carico operativo, applica automaticamente le security best practices e semplifica la gestione dei costi.

```bash
# Creare un cluster GKE Autopilot
gcloud container clusters create-auto cluster-prod \
    --region=europe-west1 \
    --release-channel=regular \
    --network=vpc-produzione \
    --subnetwork=subnet-gke \
    --cluster-ipv4-cidr=/17 \
    --services-ipv4-cidr=/22 \
    --enable-private-nodes \
    --master-ipv4-cidr=172.16.0.0/28

# Creare un cluster GKE Standard
gcloud container clusters create cluster-standard \
    --region=europe-west1 \
    --num-nodes=2 \
    --machine-type=e2-standard-4 \
    --disk-size=100GB \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5 \
    --release-channel=regular \
    --network=vpc-produzione \
    --subnetwork=subnet-gke \
    --enable-ip-alias \
    --enable-private-nodes \
    --master-ipv4-cidr=172.16.0.0/28 \
    --workload-pool=progetto.svc.id.goog

# Ottenere le credenziali del cluster
gcloud container clusters get-credentials cluster-prod \
    --region=europe-west1

# Aggiungere un node pool GPU
gcloud container node-pools create gpu-pool \
    --cluster=cluster-standard \
    --region=europe-west1 \
    --machine-type=a2-highgpu-1g \
    --accelerator=type=nvidia-tesla-a100,count=1 \
    --num-nodes=1 \
    --enable-autoscaling \
    --min-nodes=0 \
    --max-nodes=3
```

### Networking del Cluster

GKE utilizza un modello di networking basato su **VPC-native** (alias IP) dove ogni Pod riceve un indirizzo IP dalla VPC, eliminando la necessita di overlay network. Questo consente:

- Comunicazione diretta tra Pod e risorse nella VPC (Cloud SQL, Memorystore)
- Firewall rules applicabili direttamente ai range IP dei Pod
- Integrazione nativa con il load balancing di GCP

I range CIDR del cluster sono suddivisi in: **node CIDR** (IP dei nodi), **pod CIDR** (IP dei Pod, tipicamente un `/14` per cluster di grandi dimensioni) e **service CIDR** (IP dei Service Kubernetes).

### Workload Identity

**Workload Identity** e il meccanismo raccomandato per autenticare i Pod verso le API GCP. Collega un Kubernetes Service Account (KSA) a un Google Service Account (GSA), permettendo ai Pod di ottenere credenziali GCP temporanee senza gestire chiavi JSON.

```yaml
# Configurazione Workload Identity
# 1. Annotare il Kubernetes Service Account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-ksa
  namespace: production
  annotations:
    iam.gke.io/gcp-service-account: sa-app@progetto.iam.gserviceaccount.com
```

```bash
# 2. Collegare il KSA al GSA
gcloud iam service-accounts add-iam-policy-binding \
    sa-app@progetto.iam.gserviceaccount.com \
    --role=roles/iam.workloadIdentityUser \
    --member="serviceAccount:progetto.svc.id.goog[production/app-ksa]"
```

### GKE Security

GKE implementa molteplici livelli di sicurezza:

- **Shielded GKE Nodes**: Secure Boot, vTPM e integrity monitoring sui nodi.
- **Binary Authorization**: verifica che solo container firmati e autorizzati vengano deployati.
- **Network Policies**: segmentazione del traffico tra Pod tramite Calico o Dataplane V2.
- **Pod Security Standards**: applicazione di policy di sicurezza a livello di namespace.
- **Private clusters**: il control plane e i nodi non hanno IP pubblici.
- **Encryption**: dati etcd crittografati at-rest con chiavi gestite da Google o customer-managed (CMEK).

### Upgrades e Release Channels

GKE supporta tre **Release Channels** per la gestione degli aggiornamenti:

- **Rapid**: versioni piu recenti, per ambienti di test e early adopters.
- **Regular** (raccomandato): versioni bilanciate tra novita e stabilita, 2-3 mesi dopo Rapid.
- **Stable**: versioni piu conservative, 4-5 mesi dopo Rapid. Per workload mission-critical.

Gli aggiornamenti dei nodi avvengono tramite **surge upgrades** (creazione di nodi aggiuntivi durante l'upgrade) o **blue-green upgrades** (creazione di un node pool parallelo).

### GKE Enterprise — Fleet Management e Governance Multi-Cluster

**GKE Enterprise** e il tier avanzato di GKE che estende le capacita di gestione a flotte di cluster distribuiti su piu regioni, cloud e ambienti on-premises (tramite Anthos). GKE Enterprise introduce concetti di governance fleet-level che operano al di sopra del singolo cluster.

#### Fleet e Membership

Una **Fleet** e un raggruppamento logico di cluster GKE (e non solo) che consente di applicare policy, configurazioni e osservabilita in modo uniforme. Ogni cluster viene registrato nella fleet tramite una **Membership**. La fleet consente di trattare l'intera infrastruttura Kubernetes come un'unita gestibile, piuttosto che come cluster isolati.

```bash
# Registrare un cluster nella fleet
gcloud container fleet memberships register cluster-prod \
    --gke-cluster=europe-west1/cluster-prod \
    --enable-workload-identity \
    --project=progetto

# Registrare un cluster esterno (on-premises o altro cloud)
gcloud container fleet memberships register cluster-onprem \
    --context=onprem-context \
    --kubeconfig=/path/to/kubeconfig \
    --enable-workload-identity \
    --project=progetto

# Visualizzare i membri della fleet
gcloud container fleet memberships list --project=progetto
```

#### Config Sync

**Config Sync** sincronizza la configurazione dei cluster con un repository Git (GitOps). Consente di dichiarare la configurazione desiderata (namespace, RBAC, network policies, resource quotas) in un repository centrale e di applicarla automaticamente a tutti i cluster della fleet o a un sottoinsieme selezionato. Config Sync rileva e corregge automaticamente le deviazioni dalla configurazione dichiarata (drift detection e remediation).

```yaml
# config-sync-config.yaml — Configurazione Config Sync
apiVersion: configsync.gke.io/v1beta1
kind: RootSync
metadata:
  name: root-sync
  namespace: config-management-system
spec:
  sourceFormat: unstructured
  git:
    repo: "https://github.com/mia-org/gke-config"
    branch: "main"
    dir: "config/clusters"
    auth: "gcpserviceaccount"
    gcpServiceAccountEmail: "sa-config-sync@progetto.iam.gserviceaccount.com"
  sourceType: git
```

#### Policy Controller

**Policy Controller** (basato su OPA Gatekeeper) consente di definire e applicare policy di governance su tutti i cluster della fleet. Le policy sono definite come **Constraints** basati su template e possono impedire il deployment di risorse non conformi. Esempi di policy comuni:

- Impedire container con immagini `latest` tag
- Richiedere limiti di CPU e memoria su tutti i Pod
- Impedire l'uso di namespace `default`
- Richiedere label specifici su tutte le risorse
- Impedire privilege escalation nei container
- Limitare i registri container consentiti

```yaml
# Constraint: impedire container senza limiti di risorse
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredResources
metadata:
  name: require-resource-limits
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production", "staging"]
  parameters:
    limits:
      - cpu
      - memory
    requests:
      - cpu
      - memory
```

#### Fleet-Level Observability

GKE Enterprise fornisce dashboard di osservabilita a livello di fleet che aggregano metriche, log e stato di salute di tutti i cluster registrati. Le funzionalita includono:

- **Fleet Overview Dashboard**: stato di tutti i cluster, versioni Kubernetes, conformita delle policy, utilizzo risorse aggregato
- **Fleet Logging**: log centralizzati da tutti i cluster con query unificate
- **Fleet Metrics**: metriche aggregate per la capacity planning cross-cluster
- **Service Mesh** (Anthos Service Mesh / Cloud Service Mesh): osservabilita del traffico tra servizi con topology map, metriche golden signals (latenza, traffico, errori, saturazione), distributed tracing e mTLS automatico

### Autopilot — Funzionalita Avanzate

#### Compute Classes

Le **Compute Classes** in Autopilot consentono di richiedere tipi specifici di hardware per i Pod senza gestire node pool:

| Classe | Hardware | Caso d'uso |
|--------|----------|------------|
| `general-purpose` (default) | CPU E2/N2 standard | Workload bilanciati |
| `balanced` | CPU N2/N2D ad alte prestazioni | Applicazioni che richiedono CPU stabile |
| `scale-out` | CPU ottimizzata per alta densita | Microservizi, web server |
| `accelerator` | GPU NVIDIA (T4, L4, A100, H100) | ML training/inference |
| `performance` | CPU C3/C3D ad altissime prestazioni | HPC, simulazioni |

```yaml
# Pod con Compute Class specifica
apiVersion: v1
kind: Pod
metadata:
  name: ml-inference
  annotations:
    cloud.google.com/compute-class: "accelerator"
spec:
  nodeSelector:
    cloud.google.com/gke-accelerator: "nvidia-l4"
  containers:
    - name: inference
      image: europe-west1-docker.pkg.dev/progetto/repo/model:v1
      resources:
        requests:
          nvidia.com/gpu: 1
          cpu: "4"
          memory: "16Gi"
        limits:
          nvidia.com/gpu: 1
```

#### Pod Burstabili e Spot Pods

I **Burstable Pods** in Autopilot consentono ai Pod di utilizzare CPU eccedente rispetto ai requests quando disponibile, senza pagare per i limits. Il Pod paga solo per i resources requests, ma puo burst fino ai limits impostati. Questo modello e ideale per workload con pattern di utilizzo variabile.

Gli **Spot Pods** eseguono i Pod su capacita Spot (preemptible) con sconti fino al 60-91%. Google puo terminare i Spot Pods in qualsiasi momento. Adatti per workload fault-tolerant: batch, CI/CD, test, pre-processing dati.

```yaml
# Spot Pod in Autopilot
apiVersion: v1
kind: Pod
metadata:
  name: batch-worker
spec:
  nodeSelector:
    cloud.google.com/gke-spot: "true"
  terminationGracePeriodSeconds: 25
  containers:
    - name: worker
      image: europe-west1-docker.pkg.dev/progetto/repo/worker:v1
      resources:
        requests:
          cpu: "2"
          memory: "4Gi"
```

### Gateway API — Evoluzione di Ingress

La **Gateway API** e lo standard Kubernetes di nuova generazione che sostituisce l'Ingress Controller tradizionale. GKE supporta nativamente la Gateway API con integrazione al Global Load Balancer di Google. Vantaggi rispetto a Ingress:

- **Ruoli separati**: la Gateway API separa i ruoli di infrastruttura (GatewayClass, Gateway) dai ruoli applicativi (HTTPRoute), consentendo ai team di piattaforma di gestire il gateway e ai team applicativi di gestire il routing.
- **Routing avanzato**: header-based routing, URL rewriting, traffic mirroring, request/response transformation.
- **Multi-protocollo**: supporto nativo per HTTP, HTTPS, gRPC, TCP e TLS.
- **Traffic splitting**: distribuzione del traffico tra backend diversi per canary e blue-green deployments.

```yaml
# Gateway con routing avanzato
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: gw-produzione
  namespace: infra
spec:
  gatewayClassName: gke-l7-global-external-managed
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        certificateRefs:
          - name: cert-produzione
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-routes
  namespace: production
spec:
  parentRefs:
    - name: gw-produzione
      namespace: infra
  hostnames:
    - "api.mia-azienda.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /v2/
      backendRefs:
        - name: api-v2
          port: 8080
          weight: 90
        - name: api-v3-canary
          port: 8080
          weight: 10
```

---

## 9. Monitoring e Observability

GCP offre una suite integrata di strumenti di observability sotto il brand **Google Cloud Operations** (precedentemente noto come Stackdriver). A differenza di AWS (dove CloudWatch e il servizio principale) e Azure (Azure Monitor), GCP separa le funzionalita in servizi dedicati ma strettamente integrati.

### Cloud Monitoring

**Cloud Monitoring** raccoglie metriche, gestisce dashboard e configura alerting. Raccoglie automaticamente metriche da tutti i servizi GCP (Compute Engine, GKE, Cloud SQL, Cloud Run, ecc.) senza necessita di configurazione. Supporta anche metriche custom e metriche da fonti esterne tramite l'agente Ops.

```bash
# Creare una custom metric
gcloud monitoring metrics-descriptors create \
    custom.googleapis.com/app/request_latency \
    --type=DOUBLE \
    --metric-kind=GAUGE \
    --description="Latenza delle richieste dell'applicazione in millisecondi"

# Creare una alerting policy (CPU > 80% per 5 minuti)
gcloud monitoring policies create \
    --notification-channels="projects/progetto/notificationChannels/12345" \
    --display-name="High CPU Usage" \
    --condition-display-name="CPU above 80%" \
    --condition-filter='resource.type="gce_instance" AND metric.type="compute.googleapis.com/instance/cpu/utilization"' \
    --condition-threshold-value=0.8 \
    --condition-threshold-comparison=COMPARISON_GT \
    --condition-threshold-duration=300s
```

### Cloud Logging

**Cloud Logging** (precedentemente Stackdriver Logging) e il servizio centralizzato di gestione log. Raccoglie automaticamente i log da tutti i servizi GCP, dalle VM (tramite Ops Agent) e da fonti esterne. Supporta query avanzate, log-based metrics e log routing.

I log sono organizzati in **Log Buckets**: `_Required` (log di audit e accesso, retention 400 giorni, non eliminabili), `_Default` (tutti gli altri log, retention 30 giorni configurabile) e bucket personalizzati.

```bash
# Cercare nei log errori HTTP 500 delle ultime 2 ore
gcloud logging read 'resource.type="cloud_run_revision" AND httpRequest.status=500 AND timestamp>="2024-01-15T10:00:00Z"' \
    --limit=50 \
    --format=json

# Creare un sink per esportare log verso Cloud Storage
gcloud logging sinks create export-to-gcs \
    storage.googleapis.com/bucket-log-archivio \
    --log-filter='resource.type="gce_instance" AND severity>=ERROR'

# Creare un sink verso BigQuery per analytics
gcloud logging sinks create export-to-bq \
    bigquery.googleapis.com/projects/progetto/datasets/logs_analysis \
    --log-filter='resource.type="cloud_run_revision"'
```

### Cloud Trace

**Cloud Trace** e il servizio di distributed tracing, equivalente di AWS X-Ray. Raccoglie dati di latenza dalle applicazioni e visualizza i trace per identificare colli di bottiglia. Si integra automaticamente con Cloud Run, Cloud Functions e App Engine. Per applicazioni su Compute Engine o GKE, richiede l'instrumentazione tramite librerie OpenTelemetry o le librerie client di Cloud Trace.

### Cloud Profiler

**Cloud Profiler** e un profiler di produzione a basso overhead (tipicamente < 0.5% di impatto sulle prestazioni). Raccoglie continuamente profili CPU e heap dalle applicazioni in produzione, consentendo di identificare le funzioni piu costose senza impattare le prestazioni. Supporta Go, Java, Node.js, Python.

### Error Reporting

**Error Reporting** aggrega e analizza automaticamente gli errori delle applicazioni, raggruppandoli per stack trace simili, tracciando la frequenza e notificando il team di nuovi errori. Si integra con Cloud Logging per collegare gli errori ai log contestuali.

### SLI/SLO Monitoring

GCP offre un framework integrato per definire e monitorare **Service Level Indicators** (SLI) e **Service Level Objectives** (SLO). Si possono definire SLO basati su disponibilita, latenza e qualita, con burn rate alerts che notificano quando il budget di errore si sta esaurendo troppo rapidamente.

### Uptime Checks

Gli **Uptime Checks** verificano periodicamente la disponibilita di URL, istanze VM o servizi Cloud Run da piu locazioni globali. Supportano HTTP, HTTPS e TCP. Intervalli configurabili da 1 a 15 minuti. Si integrano con le alerting policies per notifiche immediate in caso di downtime.

```bash
# Creare un uptime check HTTP
gcloud monitoring uptime create \
    --display-name="API Production Health" \
    --resource-type=uptime-url \
    --hostname=api.mia-azienda.com \
    --path=/health \
    --port=443 \
    --protocol=HTTPS \
    --period=60 \
    --timeout=10 \
    --content-match="OK" \
    --regions=europe-west1,us-central1,asia-east1
```

### Log Analytics — Analisi Avanzata con BigQuery

**Log Analytics** consente di eseguire query SQL sui log di Cloud Logging tramite dataset linkati a BigQuery, senza configurare sink di esportazione separati. I log bucket possono essere **upgraded** per abilitare l'accesso BigQuery diretto, mantenendo i log nel bucket originale ma rendendoli interrogabili con SQL standard.

Questo approccio combina la gestione operativa dei log (alerting, streaming, ricerca rapida) in Cloud Logging con la potenza analitica di BigQuery per analisi complesse, correlazione cross-servizio e reporting a lungo termine.

```sql
-- Analisi dei pattern di errore HTTP negli ultimi 7 giorni (via Log Analytics)
SELECT
  DATE(timestamp) AS giorno,
  resource.labels.service_name AS servizio,
  http_request.status AS stato_http,
  COUNT(*) AS conteggio
FROM `progetto.global._Default._AllLogs`
WHERE
  timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND http_request.status >= 400
GROUP BY giorno, servizio, stato_http
ORDER BY giorno DESC, conteggio DESC;

-- Identificare i top 10 endpoint piu lenti
SELECT
  http_request.request_url AS endpoint,
  ROUND(AVG(http_request.latency.seconds * 1000 + http_request.latency.nanos / 1e6), 2) AS latenza_media_ms,
  APPROX_QUANTILES(http_request.latency.seconds * 1000, 100)[OFFSET(95)] AS p95_ms,
  COUNT(*) AS richieste
FROM `progetto.global._Default._AllLogs`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND http_request IS NOT NULL
GROUP BY endpoint
HAVING richieste > 100
ORDER BY p95_ms DESC
LIMIT 10;
```

### Structured Logging — Best Practices

L'adozione di **structured logging** (log in formato JSON) consente una migliore indicizzazione, ricerca e correlazione dei log in Cloud Logging. Cloud Run, Cloud Functions e GKE riconoscono automaticamente i log JSON e li parsano nei campi appropriati.

Campi speciali riconosciuti da Cloud Logging:
- `severity`: livello del log (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `message`: testo principale del log
- `httpRequest`: oggetto con dettagli della richiesta HTTP
- `logging.googleapis.com/trace`: ID del trace per correlazione con Cloud Trace
- `logging.googleapis.com/spanId`: ID dello span per correlazione dettagliata
- `logging.googleapis.com/labels`: label personalizzati per filtraggio avanzato

```json
{
  "severity": "ERROR",
  "message": "Connessione al database fallita dopo 3 tentativi",
  "logging.googleapis.com/trace": "projects/progetto/traces/abc123def456",
  "logging.googleapis.com/labels": {
    "component": "db-connector",
    "environment": "production",
    "retry_count": "3"
  },
  "serviceContext": {
    "service": "api-service",
    "version": "v2.1.0"
  },
  "context": {
    "reportLocation": {
      "filePath": "src/db/connector.py",
      "lineNumber": 142,
      "functionName": "connect_with_retry"
    }
  }
}
```

### OpenTelemetry su GKE — Collector Pattern

Per ambienti GKE, il pattern raccomandato prevede il deployment di un **OpenTelemetry Collector** come DaemonSet che raccoglie metriche, trace e log da tutti i Pod e li invia a Cloud Monitoring, Cloud Trace e Cloud Logging. Questo approccio centralizza la configurazione dell'esportazione e riduce il carico sulle applicazioni.

```yaml
# OpenTelemetry Collector come DaemonSet su GKE
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: otel-collector
  namespace: observability
spec:
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      serviceAccountName: otel-collector-sa
      containers:
        - name: collector
          image: otel/opentelemetry-collector-contrib:0.96.0
          args: ["--config=/conf/otel-config.yaml"]
          ports:
            - containerPort: 4317  # OTLP gRPC
            - containerPort: 4318  # OTLP HTTP
          volumeMounts:
            - name: config
              mountPath: /conf
      volumes:
        - name: config
          configMap:
            name: otel-collector-config
```

### SLO Burn Rate Alerting — Approfondimento

Il **burn rate alerting** e il meccanismo raccomandato per il monitoraggio degli SLO. Invece di inviare alert su ogni singola violazione, calcola la velocita con cui il **budget di errore** viene consumato. Un burn rate di 1x significa che il budget di errore si esaurira esattamente alla fine del periodo SLO. Un burn rate di 10x significa che il budget si esaurira in 1/10 del tempo.

La strategia raccomandata utilizza finestre multiple:

| Finestra | Burn rate soglia | Significato |
|----------|-----------------|-------------|
| 1 ora + 5 minuti | 14.4x | Incidente critico in corso, budget si esaurisce in ~2.5 giorni |
| 6 ore + 30 minuti | 6x | Problema significativo, budget si esaurisce in ~5 giorni |
| 3 giorni + 6 ore | 1x | Erosione lenta, budget si esaurisce nel periodo SLO |

La combinazione di una finestra lunga (per la significativita statistica) e una finestra corta (per la conferma che il problema e in corso) riduce drasticamente i falsi positivi rispetto agli alert tradizionali basati su soglie.

---

## 10. Security

GCP offre un ecosistema completo di servizi di sicurezza integrati, coprendo dalla protezione perimetrale alla rilevazione delle minacce fino alla conformita.

### Security Command Center (SCC)

**Security Command Center** e la piattaforma centralizzata di gestione della sicurezza, equivalente di AWS Security Hub e Azure Defender for Cloud. Disponibile in due tier:

- **Standard**: gratuito, include Security Health Analytics (scansione automatica delle misconfigurazioni), Web Security Scanner e asset inventory.
- **Premium**: include tutte le funzionalita Standard piu Event Threat Detection (rilevazione minacce in tempo reale), Container Threat Detection, Virtual Machine Threat Detection, attacco simulation e compliance reporting (CIS, PCI DSS, NIST).

SCC aggrega i findings da tutti i servizi di sicurezza GCP e da fonti esterne, fornendo una vista unificata della postura di sicurezza dell'organizzazione.

### Cloud Armor

**Cloud Armor** e il servizio di protezione DDoS e Web Application Firewall (WAF) di GCP, equivalente di AWS WAF/Shield e Azure Front Door/WAF. Funzionalita principali:

- **Protezione DDoS**: sempre attiva per il traffico che transita attraverso il Global Load Balancer. La protezione base (Layer 3/4) e inclusa senza costi aggiuntivi. La protezione avanzata (Managed Protection Plus) include SLA di risposta, crediti finanziari per eventi DDoS e supporto dedicato.
- **WAF Rules**: regole preconfigurate basate su OWASP ModSecurity Core Rule Set (CRS) per SQL injection, XSS, LFI, RFI e altri attacchi comuni.
- **Rate Limiting**: limitazione del traffico per IP o header, con azioni configurabili (deny, throttle, redirect).
- **Adaptive Protection**: rilevazione automatica degli attacchi Layer 7 tramite machine learning, con suggerimento automatico delle regole di mitigazione.
- **Bot Management**: identificazione e gestione del traffico bot tramite reCAPTCHA Enterprise.

```bash
# Creare una security policy Cloud Armor
gcloud compute security-policies create policy-waf \
    --description="WAF per applicazione web"

# Aggiungere regola per bloccare SQL injection
gcloud compute security-policies rules create 1000 \
    --security-policy=policy-waf \
    --expression="evaluatePreconfiguredExpr('sqli-v33-stable')" \
    --action=deny-403 \
    --description="Blocca SQL injection"

# Aggiungere regola per bloccare XSS
gcloud compute security-policies rules create 1001 \
    --security-policy=policy-waf \
    --expression="evaluatePreconfiguredExpr('xss-v33-stable')" \
    --action=deny-403 \
    --description="Blocca XSS"

# Aggiungere rate limiting
gcloud compute security-policies rules create 2000 \
    --security-policy=policy-waf \
    --src-ip-ranges="*" \
    --action=throttle \
    --rate-limit-threshold-count=100 \
    --rate-limit-threshold-interval-sec=60 \
    --conform-action=allow \
    --exceed-action=deny-429 \
    --enforce-on-key=IP
```

### VPC Service Controls

**VPC Service Controls** creano un perimetro di sicurezza attorno alle risorse GCP per prevenire l'esfiltrazione di dati. Anche se un attaccante ottiene credenziali IAM valide, non puo accedere alle risorse se la richiesta proviene dall'esterno del perimetro. Il perimetro puo essere basato su: rete VPC, indirizzo IP, identita dell'utente, device trust (tramite Access Context Manager).

Servizi supportati: Cloud Storage, BigQuery, Cloud SQL, Spanner, Pub/Sub, Container Registry, Artifact Registry e altri.

```bash
# Creare un Access Policy
gcloud access-context-manager policies create \
    --organization=123456789 \
    --title="Policy aziendale"

# Creare un perimetro di servizio
gcloud access-context-manager perimeters create perimetro-dati \
    --policy=POLICY_ID \
    --title="Perimetro dati sensibili" \
    --resources="projects/123,projects/456" \
    --restricted-services="storage.googleapis.com,bigquery.googleapis.com" \
    --access-levels=accessPolicies/POLICY_ID/accessLevels/livello-rete-aziendale
```

### Binary Authorization

**Binary Authorization** verifica che solo container fidati e autorizzati vengano deployati su GKE e Cloud Run. Utilizza attestazioni crittografiche (firme digitali) per verificare che un'immagine container abbia superato i controlli richiesti (build verificata, scansione vulnerabilita, approvazione manuale) prima del deployment.

### Certificate Authority Service (CAS)

**Certificate Authority Service** e un servizio gestito per creare e gestire Certificate Authority (CA) private. Consente di emettere certificati X.509 per mTLS, autenticazione device, code signing e altri casi d'uso. Elimina la complessita operativa della gestione di una PKI on-premises.

### Chronicle SIEM

**Chronicle** (precedentemente Chronicle Security Operations) e la piattaforma SIEM (Security Information and Event Management) di Google, costruita sull'infrastruttura Google. Caratteristiche distintive:

- Ingestione e ricerca su petabyte di dati di sicurezza con latenza sub-secondo
- Retention di 12 mesi a prezzo fisso (non basato sul volume di dati ingeriti, a differenza di molti SIEM concorrenti)
- Integrazione nativa con il threat intelligence di Google (VirusTotal, Mandiant)
- Detection engine basato su YARA-L per la definizione di regole di rilevazione personalizzate

#### Chronicle SIEM — Approfondimento Architetturale

Chronicle utilizza il **Unified Data Model** (UDM), un modello dati normalizzato che traduce i log da fonti eterogenee (firewall, endpoint, cloud, identity provider) in un formato comune. Questo consente query cross-source senza conoscere il formato nativo di ciascuna fonte.

Il **Detection Engine** di Chronicle utilizza **YARA-L 2.0**, un linguaggio di detection rule proprietario ottimizzato per la threat detection su grandi volumi di dati. YARA-L consente correlazioni temporali tra eventi, matching su entita multiple e aggregazioni statistiche.

```
// Esempio regola YARA-L: brute force detection
rule brute_force_login {
  meta:
    author = "security-team"
    description = "Rileva piu di 10 login falliti dallo stesso IP in 5 minuti"
    severity = "HIGH"
    priority = "HIGH"

  events:
    $login.metadata.event_type = "USER_LOGIN"
    $login.security_result.action = "BLOCK"
    $login.principal.ip = $ip

  match:
    $ip over 5m

  condition:
    #login > 10

  outcome:
    $risk_score = 85
    $event_count = count_distinct($login.metadata.id)
    $target_users = array_distinct($login.target.user.userid)
}
```

Chronicle integra **SOAR** (Security Orchestration, Automation and Response) per l'automazione delle risposte agli incidenti. I playbook SOAR definiscono flussi automatizzati di triage, arricchimento (lookup su VirusTotal, Mandiant Threat Intelligence, WHOIS) e risposta (blocco IP su Cloud Armor, disabilitazione service account, notifica al team SOC).

### BeyondCorp Enterprise — Zero Trust Avanzato

**BeyondCorp Enterprise** implementa il modello Zero Trust di Google, sostituendo il tradizionale modello di sicurezza perimetrale (VPN) con un approccio basato sull'identita e sul contesto. Il principio fondante e che la fiducia non deve essere concessa in base alla posizione nella rete, ma verificata continuamente per ogni richiesta.

#### Identity-Aware Proxy (IAP)

**IAP** e il componente centrale di BeyondCorp. Intercetta tutte le richieste verso le applicazioni protette e verifica l'identita dell'utente e il contesto del dispositivo prima di consentire l'accesso. Supporta applicazioni su GKE, Compute Engine, Cloud Run e App Engine, oltre ad applicazioni on-premises tramite il **IAP Connector**.

```bash
# Abilitare IAP su un backend service
gcloud compute backend-services update backend-app \
    --iap=enabled,oauth2-client-id=CLIENT_ID,oauth2-client-secret=CLIENT_SECRET \
    --global

# Concedere accesso tramite IAP a un gruppo
gcloud iap web add-iam-policy-binding \
    --resource-type=backend-services \
    --service=backend-app \
    --member="group:engineering@mia-azienda.com" \
    --role="roles/iap.httpsResourceAccessor"
```

#### Context-Aware Access

Le **Access Levels** in Access Context Manager definiscono le condizioni di contesto che devono essere soddisfatte per consentire l'accesso. Le condizioni possono includere:

- **Rete di origine**: range IP, VPN aziendale, regione geografica
- **Stato del dispositivo**: crittografia del disco abilitata, versione OS aggiornata, screen lock attivo, verifica dell'endpoint aziendale
- **Identita**: appartenenza a gruppi specifici, dominio dell'identita
- **Orario**: finestre temporali consentite per l'accesso

Queste condizioni si combinano per creare policy granulari: ad esempio, consentire l'accesso all'applicazione finanziaria solo da dispositivi aziendali con disco crittografato, su rete aziendale, durante l'orario lavorativo.

### Assured Workloads — Conformita Regolamentare

**Assured Workloads** consente di creare ambienti GCP conformi a requisiti regolamentari specifici, applicando automaticamente restrizioni su residenza dei dati, accesso del personale Google e crittografia. Supporta framework di conformita come:

- **EU Regions and Support**: dati e supporto limitati all'Unione Europea
- **CJIS** (Criminal Justice Information Services): per agenzie governative US
- **FedRAMP High**: per workload governativi US
- **IL4/IL5** (Impact Level): per il Dipartimento della Difesa US
- **HIPAA**: per dati sanitari (combinato con BAA)
- **PCI DSS**: per dati di pagamento

Assured Workloads applica automaticamente Organization Policies, restrizioni CMEK, controlli sull'accesso del personale Google (Access Transparency e Access Approval) e monitoring della conformita.

```bash
# Creare un ambiente Assured Workloads per EU
gcloud assured workloads create \
    --organization=123456789 \
    --location=europe-west1 \
    --display-name="Workload EU Conforme" \
    --compliance-regime=EU_REGIONS_AND_SUPPORT \
    --billing-account=01ABCD-234567-EFGHIJ \
    --provisioned-resources-parent=folders/987654321
```

---

## 11. Infrastructure as Code

GCP supporta molteplici approcci per gestire l'infrastruttura come codice, dal servizio nativo Deployment Manager alle soluzioni open-source come Terraform, fino all'integrazione Kubernetes-native tramite Config Connector.

### Deployment Manager

**Deployment Manager** e il servizio nativo di IaC di GCP, equivalente di AWS CloudFormation e Azure Resource Manager (ARM). Utilizza template in YAML o Python (Jinja2) per definire le risorse. Supporta preview delle modifiche, aggiornamenti incrementali e rollback.

```yaml
# deployment.yaml — Esempio Deployment Manager
resources:
- name: vm-web-server
  type: compute.v1.instance
  properties:
    zone: europe-west1-b
    machineType: zones/europe-west1-b/machineTypes/e2-standard-2
    disks:
    - deviceName: boot
      type: PERSISTENT
      boot: true
      autoDelete: true
      initializeParams:
        sourceImage: projects/debian-cloud/global/images/family/debian-12
        diskSizeGb: 50
    networkInterfaces:
    - network: global/networks/vpc-produzione
      subnetwork: regions/europe-west1/subnetworks/subnet-web-eu
      accessConfigs:
      - name: External NAT
        type: ONE_TO_ONE_NAT
    metadata:
      items:
      - key: startup-script
        value: |
          #!/bin/bash
          apt-get update && apt-get install -y nginx
    tags:
      items:
      - web-server

- name: firewall-http
  type: compute.v1.firewall
  properties:
    network: global/networks/vpc-produzione
    allowed:
    - IPProtocol: tcp
      ports:
      - "80"
      - "443"
    sourceRanges:
    - 0.0.0.0/0
    targetTags:
    - web-server
```

```bash
# Creare il deployment
gcloud deployment-manager deployments create web-stack --config=deployment.yaml

# Visualizzare lo stato
gcloud deployment-manager deployments describe web-stack

# Aggiornare il deployment (preview prima dell'applicazione)
gcloud deployment-manager deployments update web-stack --config=deployment-v2.yaml --preview
gcloud deployment-manager deployments update web-stack

# Eliminare il deployment (e tutte le risorse create)
gcloud deployment-manager deployments delete web-stack
```

Deployment Manager e meno utilizzato rispetto a Terraform nell'ecosistema GCP. Google stessa raccomanda Terraform per nuovi progetti e ha investito significativamente nel provider Terraform ufficiale.

### Terraform con Google Provider

**Terraform** con il **Google provider** (`hashicorp/google` e `hashicorp/google-beta`) e l'approccio IaC piu diffuso per GCP. Il provider e mantenuto congiuntamente da HashiCorp e Google, con copertura completa dei servizi GCP.

```hcl
# main.tf — Infrastruttura GCP con Terraform
terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "terraform-state-progetto"
    prefix = "prod/infra"
  }
}

provider "google" {
  project = "prod-webapp-a1b2c3"
  region  = "europe-west1"
}

# VPC custom-mode
resource "google_compute_network" "vpc" {
  name                    = "vpc-produzione"
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"
}

# Subnet
resource "google_compute_subnetwork" "web" {
  name          = "subnet-web"
  ip_cidr_range = "10.10.0.0/24"
  region        = "europe-west1"
  network       = google_compute_network.vpc.id

  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.100.0.0/16"
  }
  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.200.0.0/20"
  }
}

# Cloud SQL PostgreSQL con HA
resource "google_sql_database_instance" "db" {
  name                = "db-produzione"
  database_version    = "POSTGRES_16"
  region              = "europe-west1"
  deletion_protection = true

  settings {
    tier              = "db-custom-4-16384"
    availability_type = "REGIONAL"
    disk_type         = "PD_SSD"
    disk_size         = 100
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    database_flags {
      name  = "max_connections"
      value = "200"
    }
  }
}

# GKE Autopilot cluster
resource "google_container_cluster" "primary" {
  name     = "cluster-prod"
  location = "europe-west1"

  enable_autopilot = true

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.web.name

  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  release_channel {
    channel = "REGULAR"
  }
}
```

### Config Connector

**Config Connector** e un add-on Kubernetes che permette di gestire risorse GCP tramite manifest Kubernetes (CRD). Le risorse GCP vengono dichiarate come oggetti Kubernetes, e Config Connector si occupa di creare, aggiornare e eliminare le risorse reali. Adatto per team che preferiscono un workflow unificato basato su `kubectl`.

```yaml
# Cloud SQL via Config Connector
apiVersion: sql.cnrm.cloud.google.com/v1beta1
kind: SQLInstance
metadata:
  name: db-produzione
  namespace: config-connector
spec:
  databaseVersion: POSTGRES_16
  region: europe-west1
  settings:
    tier: db-custom-4-16384
    availabilityType: REGIONAL
    diskType: PD_SSD
    diskSize: 100
    backupConfiguration:
      enabled: true
      startTime: "02:00"
      pointInTimeRecoveryEnabled: true
```

### DevOps — CI/CD con Cloud Build, Cloud Deploy e Artifact Registry

GCP fornisce una toolchain CI/CD nativa completamente integrata che copre il ciclo completo: build, test, archiviazione artefatti e deployment progressivo.

#### Artifact Registry

**Artifact Registry** e il servizio universale di archiviazione artefatti che sostituisce Container Registry (deprecato). Supporta container Docker, pacchetti npm, Maven, Python (PyPI), Go, Apt e Yum. Ogni repository e regionale e supporta CMEK, vulnerability scanning automatico e cleanup policies.

```bash
# Creare un repository Docker
gcloud artifacts repositories create repo-docker \
    --repository-format=docker \
    --location=europe-west1 \
    --description="Repository Docker di produzione" \
    --kms-key=projects/progetto/locations/europe-west1/keyRings/kr/cryptoKeys/key

# Creare un repository Python
gcloud artifacts repositories create repo-python \
    --repository-format=python \
    --location=europe-west1 \
    --description="Repository PyPI interno"

# Configurare Docker per autenticarsi verso Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Push di un'immagine
docker tag api:v1.2.0 europe-west1-docker.pkg.dev/progetto/repo-docker/api:v1.2.0
docker push europe-west1-docker.pkg.dev/progetto/repo-docker/api:v1.2.0

# Abilitare la scansione automatica delle vulnerabilita
gcloud artifacts repositories update repo-docker \
    --location=europe-west1 \
    --enable-vulnerability-scanning
```

#### Cloud Build

**Cloud Build** e il servizio di CI/CD serverless per la compilazione, il testing e il packaging delle applicazioni. Supporta build multi-step definite in `cloudbuild.yaml`, con accesso a un ampio set di builder pre-configurati e la possibilita di utilizzare qualsiasi container come step di build.

Caratteristiche:
- **Trigger**: attivazione automatica da push/PR su GitHub, GitLab, Bitbucket o Cloud Source Repositories
- **Build pools privati**: build eseguite in un VPC privato per accedere a risorse interne (database, registri privati) durante la build
- **Parallelismo**: step di build paralleli per ridurre i tempi
- **Approvazioni**: gate manuali per build che richiedono approvazione prima del deployment
- **Caching**: cache delle dipendenze tramite Kaniko cache o Cloud Storage per build piu veloci

```yaml
# cloudbuild.yaml — Pipeline CI completa
steps:
  # Step 1: Eseguire i test
  - name: 'python:3.12-slim'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
        pytest tests/ --cov=src --cov-report=xml --junitxml=results.xml
    id: 'test'

  # Step 2: Scansione di sicurezza (parallelo con i test di integrazione)
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['builds', 'submit', '--tag', 'temp-scan', '--no-source']
    id: 'security-scan'
    waitFor: ['test']

  # Step 3: Build dell'immagine Docker con Kaniko (cache abilitata)
  - name: 'gcr.io/kaniko-project/executor:latest'
    args:
      - '--destination=europe-west1-docker.pkg.dev/$PROJECT_ID/repo-docker/api:$SHORT_SHA'
      - '--destination=europe-west1-docker.pkg.dev/$PROJECT_ID/repo-docker/api:latest'
      - '--cache=true'
      - '--cache-ttl=72h'
    id: 'build-image'
    waitFor: ['test']

  # Step 4: Creare release Cloud Deploy
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'deploy'
      - 'releases'
      - 'create'
      - 'release-$SHORT_SHA'
      - '--delivery-pipeline=pipeline-api'
      - '--region=europe-west1'
      - '--images=api=europe-west1-docker.pkg.dev/$PROJECT_ID/repo-docker/api:$SHORT_SHA'
    id: 'create-release'
    waitFor: ['build-image']

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'

timeout: '1800s'

# Trigger configurazione
trigger:
  github:
    owner: 'mia-org'
    name: 'api-service'
    push:
      branch: '^main$'
```

#### Cloud Deploy

**Cloud Deploy** gestisce il deployment progressivo delle applicazioni verso ambienti multipli (dev, staging, prod). Implementa il modello **delivery pipeline** con **targets** (ambienti di destinazione) e **releases** (versioni da deployare). Supporta strategie di deployment avanzate:

- **Standard**: deployment diretto che sostituisce la versione corrente
- **Canary**: deployment progressivo con percentuali di traffico configurabili (es. 10%, 25%, 50%, 100%)
- **Blue-Green**: deployment parallelo con switch istantaneo del traffico
- **Rollback automatico**: rollback basato su metriche Cloud Monitoring (percentuale di errori, latenza)
- **Approvazioni**: gate manuali tra gli ambienti

```yaml
# delivery-pipeline.yaml — Pipeline di deployment
apiVersion: deploy.cloud.google.com/v1
kind: DeliveryPipeline
metadata:
  name: pipeline-api
description: "Pipeline di deployment per API service"
serialPipeline:
  stages:
    - targetId: dev
      profiles: [dev]
    - targetId: staging
      profiles: [staging]
      strategy:
        canary:
          runtimeConfig:
            cloudRun:
              automaticTrafficControl: true
          canaryDeployment:
            percentages: [25, 50, 75]
            verify: true
    - targetId: production
      profiles: [production]
      strategy:
        canary:
          runtimeConfig:
            cloudRun:
              automaticTrafficControl: true
          canaryDeployment:
            percentages: [10, 25, 50]
            verify: true
      deployParameters:
        - values:
            minInstances: "3"
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: production
description: "Ambiente di produzione"
requireApproval: true
run:
  location: projects/progetto/locations/europe-west1
```

Il flusso integrato tipico e: **commit** → **Cloud Build** (test, build, push su Artifact Registry) → **Cloud Deploy** (release, promozione tra ambienti, canary, approvazione, rollout) → **GKE o Cloud Run** (target di deployment).

---

## 12. Cost Management

La gestione dei costi in GCP richiede una comprensione dei modelli di pricing, degli strumenti di monitoraggio e delle strategie di ottimizzazione disponibili.

### Billing Accounts e Projects

Ogni progetto GCP deve essere associato a un **Billing Account** per creare risorse a pagamento. Un billing account puo essere associato a piu progetti. La struttura tipica separa i billing accounts per business unit o ambiente.

Le **Billing Sub-accounts** (disponibili per i rivenditori) consentono di segregare la fatturazione mantenendo una gerarchia gerarchica.

```bash
# Visualizzare i billing accounts disponibili
gcloud billing accounts list

# Associare un progetto a un billing account
gcloud billing projects link prod-webapp-a1b2c3 \
    --billing-account=01ABCD-234567-EFGHIJ

# Visualizzare i costi per progetto
gcloud billing projects describe prod-webapp-a1b2c3
```

### Budgets e Alerts

I **Budgets** definiscono soglie di spesa con notifiche automatiche quando la spesa raggiunge percentuali configurabili del budget (tipicamente 50%, 80%, 100%). Le notifiche possono essere inviate via email, Pub/Sub (per automazione) o collegati a Cloud Functions per azioni automatiche (ad esempio, disabilitare la fatturazione su un progetto sandbox quando il budget viene superato).

```bash
# Creare un budget di 1000 EUR con soglie al 50%, 80% e 100%
gcloud billing budgets create \
    --billing-account=01ABCD-234567-EFGHIJ \
    --display-name="Budget Produzione Q1" \
    --budget-amount=1000EUR \
    --threshold-rule=percent=0.5 \
    --threshold-rule=percent=0.8 \
    --threshold-rule=percent=1.0 \
    --filter-projects="projects/prod-webapp-a1b2c3" \
    --notifications-rule-pubsub-topic="projects/progetto/topics/budget-alerts"
```

### Committed Use Discounts (CUD)

I **Committed Use Discounts** offrono sconti significativi (fino al 57% per Compute Engine, fino al 52% per Cloud SQL) in cambio dell'impegno a utilizzare una quantita minima di risorse per 1 o 3 anni. I CUD si applicano automaticamente alle risorse corrispondenti nel progetto o nell'organizzazione.

Due tipi di CUD per Compute Engine:
- **Resource-based CUD**: impegno su un numero specifico di vCPU e memoria in una regione specifica. Applicabile indipendentemente dal machine type.
- **Spend-based CUD**: impegno su una spesa minima oraria per servizi specifici (Cloud SQL, Memorystore, Cloud Run).

| Durata | Sconto Compute (resource-based) | Sconto Cloud SQL (spend-based) |
|--------|------|-----------|
| 1 anno | 20-28% | 25% |
| 3 anni | 46-57% | 52% |

### Sustained Use Discounts (SUD)

I **Sustained Use Discounts** sono sconti automatici applicati alle VM Compute Engine (famiglie N1, N2, N2D) che vengono eseguite per una parte significativa del mese. Lo sconto aumenta progressivamente:

- 0-25% del mese: prezzo pieno
- 25-50% del mese: 20% di sconto sulla porzione eccedente
- 50-75% del mese: 40% di sconto
- 75-100% del mese: 60% di sconto

Il SUD effettivo per un'istanza che esegue per l'intero mese e circa il 30%. I SUD non si applicano alle famiglie E2, Tau (T2D) e alle Spot VMs. I SUD e i CUD sono mutuamente esclusivi (se si ha un CUD, il SUD non si applica).

### BigQuery Billing Export

L'esportazione della fatturazione verso **BigQuery** consente analisi dettagliate e personalizzate dei costi. I dati di fatturazione vengono esportati in una tabella BigQuery con granularita a livello di singola risorsa, servizio, SKU e progetto.

```sql
-- Query per i 10 servizi piu costosi dell'ultimo mese
SELECT
  service.description AS servizio,
  ROUND(SUM(cost), 2) AS costo_totale,
  ROUND(SUM(cost) / (SELECT SUM(cost) FROM `progetto.billing.gcp_billing_export_v1_*` WHERE invoice.month = '202401') * 100, 1) AS percentuale
FROM `progetto.billing.gcp_billing_export_v1_*`
WHERE invoice.month = '202401'
GROUP BY servizio
ORDER BY costo_totale DESC
LIMIT 10;

-- Query per costi giornalieri dell'ultimo mese
SELECT
  DATE(usage_start_time) AS giorno,
  ROUND(SUM(cost), 2) AS costo_giornaliero
FROM `progetto.billing.gcp_billing_export_v1_*`
WHERE invoice.month = '202401'
GROUP BY giorno
ORDER BY giorno;
```

### Pricing Calculator e Recommender

Il **Google Cloud Pricing Calculator** consente di stimare i costi prima del deployment. Il servizio **Recommender** analizza l'utilizzo effettivo delle risorse e suggerisce ottimizzazioni:

- **VM rightsizing**: ridimensionamento delle VM sottoutilizzate (ad esempio, ridurre da `n2-standard-8` a `n2-standard-4` se la CPU media e sotto il 30%).
- **Idle resources**: identificazione di risorse non utilizzate (IP statici non assegnati, dischi non collegati, load balancer senza backend).
- **Committed use discount recommendations**: suggerimenti per l'acquisto di CUD basati sui pattern di utilizzo.

```bash
# Visualizzare le raccomandazioni per un progetto
gcloud recommender recommendations list \
    --project=prod-webapp-a1b2c3 \
    --location=europe-west1 \
    --recommender=google.compute.instance.MachineTypeRecommender \
    --format="table(name,description,primaryImpact.costProjection)"
```

### Spot VMs — Pattern di Utilizzo Avanzati

Le **Spot VMs** (ex Preemptible) offrono sconti del 60-91% rispetto alle VM on-demand. I pattern di utilizzo avanzati includono:

- **MIG con Spot**: configurare un Managed Instance Group con `provisioning-model=SPOT` per workload batch. Il MIG ricrea automaticamente le istanze terminate da Google. Si puo combinare con un secondo MIG on-demand come fallback per garantire una capacita minima.
- **GKE con Spot Pods**: in Autopilot, i Pod possono essere schedulati su nodi Spot tramite il nodeSelector `cloud.google.com/gke-spot: "true"`. In Standard mode, creare un node pool Spot dedicato con taint `cloud.google.com/gke-spot=true:NoSchedule` e toleration sui Pod appropriati.
- **Dataproc con Spot workers**: i cluster Dataproc supportano secondary workers Spot per ridurre i costi di Spark/Hadoop fino all'80%, mantenendo i primary workers on-demand per la stabilita.
- **Batch API**: il servizio **Cloud Batch** e progettato nativamente per workload su Spot VMs, con gestione automatica dei retry e della schedulazione.

```bash
# Creare un MIG con Spot VMs e fallback on-demand
gcloud compute instance-templates create tmpl-batch-spot \
    --machine-type=c2-standard-8 \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP \
    --image-family=debian-12 \
    --image-project=debian-cloud

gcloud compute instance-groups managed create mig-batch \
    --template=tmpl-batch-spot \
    --size=10 \
    --region=us-central1
```

### Active Assist e Recommender Hub

**Active Assist** e la piattaforma che aggrega tutte le raccomandazioni di ottimizzazione di GCP in un'unica interfaccia. Il **Recommender Hub** fornisce raccomandazioni categorizzate per:

- **Costo**: rightsizing VM, eliminazione risorse inutilizzate, acquisto CUD, migrazione a machine type piu efficienti
- **Sicurezza**: rimozione permessi IAM non utilizzati, identificazione service account sovra-privilegiati, rotazione chiavi
- **Prestazioni**: upgrade a tipi di disco piu performanti, ottimizzazione configurazione rete
- **Affidabilita**: suggerimenti per alta disponibilita, backup, distribuzioni multi-zona
- **Sostenibilita**: migrazione verso regioni a basse emissioni di carbonio

Ogni raccomandazione include l'impatto stimato (risparmio economico, riduzione rischio) e la priorita, consentendo al team FinOps di prioritizzare le azioni con il massimo ROI.

### Carbon Footprint

La **Carbon Footprint Dashboard** fornisce visibilita sulle emissioni di CO2 associate all'utilizzo delle risorse GCP. Mostra le emissioni lorde (prima degli offset) e nette (dopo i crediti di energia rinnovabile acquistati da Google). Le metriche possono essere segmentate per progetto, servizio, regione e mese. Consente di identificare opportunita di migrazione verso regioni a basse emissioni e di reportare l'impronta ambientale del cloud per compliance ESG.

### FinOps Workflow — Processo di Ottimizzazione Continua

Un workflow FinOps maturo per GCP si articola in tre fasi cicliche:

1. **Inform** (Visibilita):
   - Esportare i dati di billing verso BigQuery con granularita a livello di risorsa
   - Creare dashboard Looker Studio con breakdown per progetto, team, servizio e ambiente
   - Implementare alerting su anomalie di spesa tramite Budgets + Pub/Sub + Cloud Functions
   - Utilizzare label obbligatori per allocazione dei costi ai centri di costo

2. **Optimize** (Azione):
   - Applicare le raccomandazioni di Active Assist con cadenza settimanale
   - Acquistare CUD per workload con baseline stabile (utilizzo > 60% costante)
   - Migrare workload batch a Spot VMs
   - Configurare autoscaling aggressivo per ambienti non-produzione (scaling a zero notturno)
   - Applicare lifecycle policies su Cloud Storage per archiviazione automatica

3. **Operate** (Governance):
   - Review mensile dei costi con i team responsabili (showback/chargeback)
   - Aggiornamento trimestrale dei CUD basato sui trend di utilizzo
   - Policy automatiche per shutdown ambienti dev/test fuori orario lavorativo
   - Quota management per prevenire spese incontrollate nei progetti sandbox

---

## 13. Best Practices

### 1. Progettare una Landing Zone Strutturata

Definire la struttura organizzativa prima di deployare qualsiasi risorsa. Creare una gerarchia di folders che rifletta la struttura aziendale (per ambiente, business unit o regione). Separare i progetti per ambiente (dev, staging, prod) e per funzione (networking, security, data, applicazioni). Utilizzare il modulo Terraform **Cloud Foundation Fabric** o il **Google Cloud Setup Checklist** come punto di partenza. Abilitare le Organization Policies per imporre vincoli di conformita fin dal primo giorno.

#### Landing Zone — Architettura di Riferimento

Una **Landing Zone** e l'ambiente cloud di base pre-configurato che fornisce la fondazione per il deployment sicuro e governato dei workload. In GCP, la landing zone comprende la gerarchia organizzativa, la configurazione IAM, il networking centralizzato, il logging, il billing e le policy di sicurezza.

L'architettura di riferimento raccomandata si articola in livelli:

```
Organization (mia-azienda.com)
├── Folder "Bootstrap"
│   └── Project "bootstrap-automation"          # Terraform state, CI/CD pipeline per IaC
├── Folder "Core / Shared Services"
│   ├── Project "shared-networking"              # Shared VPC host, Cloud DNS, Cloud NAT, Interconnect
│   ├── Project "shared-security"                # Security Command Center, Chronicle, KMS
│   ├── Project "shared-logging"                 # Log sink centralizzati, Cloud Logging buckets
│   └── Project "shared-monitoring"              # Dashboard aggregati, Uptime Checks, SLO
├── Folder "Produzione"
│   ├── Folder "Team A"
│   │   ├── Project "prod-team-a-app"            # Workload applicativi
│   │   └── Project "prod-team-a-data"           # BigQuery, Cloud SQL, Pub/Sub
│   └── Folder "Team B"
│       ├── Project "prod-team-b-app"
│       └── Project "prod-team-b-data"
├── Folder "Non-Produzione"
│   ├── Folder "Staging"
│   │   └── Project "staging-app"
│   └── Folder "Development"
│       └── Project "dev-experiments"
└── Folder "Sandbox"
    └── Project "sandbox-esplorazione"           # Budget limitato, nessun dato sensibile
```

#### Cloud Foundation Fabric FAST

**Cloud Foundation Fabric FAST** e l'implementazione Terraform di riferimento per la landing zone GCP, sviluppata dal team di Google Cloud. FAST e organizzato in **stage** sequenziali:

| Stage | Scopo | Risorse create |
|-------|-------|----------------|
| **0 — Bootstrap** | Fondazione organizzativa | Service accounts per automazione, bucket GCS per Terraform state, Organization Policies base |
| **1 — Resource Management** | Gerarchia risorse | Folder structure, progetti base, automazione per creazione progetti |
| **2 — Networking** | Rete centralizzata | Shared VPC, Cloud NAT, Cloud DNS, VPN/Interconnect, firewall rules |
| **2 — Security** | Sicurezza centralizzata | KMS keyrings, VPC Service Controls, Security Command Center |
| **3 — Project Factory** | Creazione progetti | Factory YAML-driven per creare progetti con configurazione standardizzata |

Ogni stage produce output utilizzati come input dallo stage successivo, garantendo una dipendenza esplicita e un ordine di deployment deterministico. I team applicativi non interagiscono direttamente con gli stage infrastrutturali ma ricevono progetti pre-configurati con networking, IAM e logging gia impostati.

#### Organization Policies Essenziali per la Landing Zone

Le Organization Policies minime raccomandate per una landing zone enterprise:

```yaml
# Vincoli essenziali per la landing zone
organization_policies:
  # Residenza dati: solo regioni EU
  constraints/gcp.resourceLocations:
    allowedValues:
      - in:eu-locations

  # Impedire IP esterni sulle VM
  constraints/compute.vmExternalIpAccess:
    deniedValues:
      - all

  # Limitare i domini IAM consentiti
  constraints/iam.allowedPolicyMemberDomains:
    allowedValues:
      - C0xxxxxxx  # Customer ID del dominio aziendale

  # Impedire la creazione di default service accounts
  constraints/iam.automaticIamGrantsForDefaultServiceAccounts:
    enforce: true

  # Impedire chiavi di service account
  constraints/iam.disableServiceAccountKeyCreation:
    enforce: true

  # Richiedere OS Login sulle VM
  constraints/compute.requireOsLogin:
    enforce: true

  # Impedire reti VPC in auto-mode
  constraints/compute.skipDefaultNetworkCreation:
    enforce: true

  # Richiedere Shielded VMs
  constraints/compute.requireShieldedVm:
    enforce: true
```

### 2. Centralizzare il Networking con Shared VPC

Adottare il pattern **Shared VPC** per centralizzare la gestione della rete in un progetto host dedicato. I progetti di servizio utilizzano le subnet della Shared VPC senza gestire la propria infrastruttura di rete. Questo semplifica la governance, riduce la superficie di attacco e facilita l'applicazione di firewall rules e Cloud NAT a livello centralizzato. Limitare l'uso del VPC peering ai casi in cui la Shared VPC non e applicabile (ad esempio, comunicazione tra organizzazioni diverse).

### 3. Applicare il Principio del Least Privilege

Non utilizzare i basic roles (Owner, Editor, Viewer) in produzione. Utilizzare esclusivamente ruoli predefiniti granulari o ruoli personalizzati. Assegnare i permessi a gruppi Google anziche a utenti individuali. Utilizzare IAM Recommender per identificare e revocare i permessi non utilizzati. Per i service accounts, creare un service account dedicato per ogni applicazione con i permessi minimi necessari. Eliminare le chiavi dei service account ovunque possibile, preferendo Workload Identity (per GKE) e Workload Identity Federation (per workload esterni).

### 4. Crittografare i Dati Ovunque

GCP crittografa tutti i dati at-rest per default con chiavi gestite da Google (Google-managed encryption keys). Per un controllo superiore, utilizzare **Customer-Managed Encryption Keys** (CMEK) tramite Cloud KMS per i servizi che lo supportano (Cloud Storage, Compute Engine, BigQuery, Cloud SQL, GKE). Per requisiti di massima sicurezza, valutare **Customer-Supplied Encryption Keys** (CSEK) dove il cliente gestisce interamente le chiavi al di fuori di Google. Abilitare TLS per tutti i dati in transito. Non archiviare mai segreti nel codice sorgente: utilizzare Secret Manager.

### 5. Automatizzare con Infrastructure as Code

Gestire l'intera infrastruttura tramite Terraform con il Google provider. Archiviare lo state di Terraform in un bucket Cloud Storage con versioning e locking (tramite un backend GCS). Implementare pipeline CI/CD con Cloud Build o GitHub Actions per validare (`terraform plan`), approvare e applicare (`terraform apply`) le modifiche infrastrutturali. Non creare mai risorse manualmente tramite la Console per ambienti diversi dalla prototipazione rapida.

### 6. Implementare una Strategia di Labeling

Definire uno schema di labeling obbligatorio per tutte le risorse. I label (equivalenti dei tags AWS/Azure) sono coppie chiave-valore che facilitano l'organizzazione, l'allocazione dei costi e l'automazione. Schema raccomandato:

- `env`: `dev`, `staging`, `prod`
- `team`: nome del team responsabile
- `app`: nome dell'applicazione
- `cost-center`: centro di costo per la fatturazione
- `managed-by`: `terraform`, `manual`, `config-connector`

Utilizzare Organization Policies per imporre la presenza di label obbligatori su tutte le risorse.

### 7. Monitorare e Osservare in Profondita

Configurare Cloud Monitoring per raccogliere metriche da tutti i componenti. Definire SLI e SLO per ogni servizio critico e configurare burn rate alerts. Implementare Cloud Logging con routing verso BigQuery per analisi a lungo termine e verso Cloud Storage per archiviazione economica. Installare l'Ops Agent su tutte le VM Compute Engine per metriche di sistema e log applicativi. Per le applicazioni, implementare il tracing con OpenTelemetry e Cloud Trace per la visibilita end-to-end sulle richieste distribuite.

### 8. Ottimizzare i Costi Continuamente

Rivedere mensilmente i costi con la Billing Console e il BigQuery billing export. Implementare CUD per workload stabili e sfruttare i SUD dove disponibili. Utilizzare Spot VMs per workload fault-tolerant. Implementare autoscaling per tutti i servizi che lo supportano (MIG, GKE, Cloud Run). Eliminare le risorse inutilizzate identificate dal Recommender. Per Cloud Storage, configurare lifecycle policies per transizionare automaticamente i dati tra classi di storage.

### 9. Proteggere il Perimetro e Rilevare le Minacce

Abilitare Security Command Center Premium per l'intera organizzazione. Configurare VPC Service Controls per prevenire l'esfiltrazione di dati dai servizi sensibili. Abilitare Cloud Armor con regole WAF e rate limiting per tutte le applicazioni web-facing. Implementare Binary Authorization per garantire che solo container verificati vengano deployati su GKE. Abilitare Cloud Audit Logs per tutti i servizi e archiviarli in un progetto di sicurezza dedicato con retention adeguata.

### 10. Pianificare il Disaster Recovery

Definire RPO (Recovery Point Objective) e RTO (Recovery Time Objective) per ogni applicazione. Utilizzare Regional MIG per alta disponibilita intra-regione. Per disaster recovery cross-region, implementare Cloud SQL con cross-region read replicas, Cloud Storage con dual-region o multi-region, e GKE con cluster multi-region. Testare periodicamente il piano di disaster recovery simulando il fallimento di una regione. Documentare le procedure di failover e formare il team operativo.

---

## Esercizi

1. **Progetto e IAM Base (Base)**
   Creare un progetto GCP all'interno di un folder organizzativo. Configurare tre service account con permessi minimi (uno per Cloud Storage, uno per Cloud SQL, uno per Compute Engine). Applicare un'Organization Policy che impedisca la creazione di external IP su VM. Verificare che la policy blocchi correttamente la creazione di VM con IP pubblico.

2. **VPC Condivisa e Networking (Intermedio)**
   Progettare una Shared VPC con un host project e due service project (dev e prod). Configurare subnet dedicate per ogni ambiente, firewall rules che consentano solo il traffico necessario e Cloud NAT per l'uscita Internet delle istanze private. Implementare Private Service Connect per accedere a Cloud SQL senza IP pubblico.

3. **Pipeline Dati con BigQuery e Pub/Sub (Intermedio)**
   Creare un topic Pub/Sub che riceva eventi JSON. Configurare una subscription push che invii i messaggi a una Cloud Function. La funzione deve validare, trasformare e inserire i dati in una tabella BigQuery partizionata per data. Configurare un scheduled query in BigQuery per generare un report aggregato giornaliero.

4. **GKE con Workload Identity e Binary Authorization (Avanzato)**
   Deployare un cluster GKE Autopilot con Workload Identity abilitata. Configurare un service account Kubernetes legato a un service account GCP con accesso a Cloud Storage. Abilitare Binary Authorization con una policy che consenta solo immagini firmate da un attestor specifico. Verificare che il deploy di un'immagine non firmata venga bloccato.

5. **Disaster Recovery Cross-Region (Avanzato)**
   Implementare un'architettura DR per un'applicazione su GKE con Cloud SQL: cluster GKE in due regioni, Cloud SQL con cross-region replica, Cloud Storage dual-region per gli asset statici, Global Load Balancer con health check. Simulare il failover disabilitando la regione primaria e misurare RTO e RPO effettivi.

---

## Letture e Riferimenti

**Documentazione ufficiale**

- Google Cloud Architecture Framework — https://cloud.google.com/architecture/framework (consultato: 2026-05-24)
- Cloud IAM Documentation — https://cloud.google.com/iam/docs (consultato: 2026-05-24)
- VPC Documentation — https://cloud.google.com/vpc/docs (consultato: 2026-05-24)
- BigQuery Documentation — https://cloud.google.com/bigquery/docs (consultato: 2026-05-24)
- GKE Documentation — https://cloud.google.com/kubernetes-engine/docs (consultato: 2026-05-24)
- Cloud Security Best Practices — https://cloud.google.com/security/best-practices (consultato: 2026-05-24)
- Cloud Billing Documentation — https://cloud.google.com/billing/docs (consultato: 2026-05-24)

**Libri consigliati**

- *Google Cloud Certified Professional Cloud Architect Study Guide* — Dan Sullivan (Sybex/Wiley)
- *Data Engineering with Google Cloud Platform* — Adi Foulger (Packt)
- *Google Cloud Platform in Action* — JJ Geewax (Manning)

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|--------|--------|-----------|
| [01](01-cloud-aws.md) | AWS | Confronto servizi equivalenti e strategie multi-cloud |
| [02](02-cloud-azure.md) | Microsoft Azure | Confronto IAM, networking e governance |
| [04](04-infrastructure-as-code.md) | Infrastructure as Code | Terraform provider Google, Config Connector |
| [05](05-kubernetes.md) | Kubernetes | GKE Autopilot, Workload Identity, Binary Authorization |
| [08](08-monitoring-observability.md) | Monitoring e Observability | Cloud Monitoring, Cloud Trace, Cloud Logging |
| [21](21-finops-cost-governance.md) | FinOps e Cost Governance | CUD, SUD, billing export, Recommender |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **BigQuery** | Data warehouse serverless di Google per analisi SQL su dataset di scala petabyte |
| **Cloud Armor** | Servizio WAF e DDoS protection per proteggere le applicazioni esposte tramite load balancer globali |
| **Cloud Run** | Piattaforma serverless per eseguire container stateless con scaling automatico a zero |
| **CUD (Committed Use Discount)** | Sconto ottenuto impegnandosi a un consumo minimo di risorse per 1 o 3 anni |
| **Folder** | Contenitore organizzativo nella gerarchia GCP che raggruppa progetti per applicare policy e IAM |
| **GKE (Google Kubernetes Engine)** | Servizio managed Kubernetes di Google con modalità Standard e Autopilot |
| **IAM Policy Binding** | Associazione tra un ruolo IAM e un principal (utente, gruppo, service account) su una risorsa specifica |
| **Organization Policy** | Vincolo centralizzato che limita la configurazione delle risorse a livello di organizzazione, folder o progetto |
| **Project** | Unità fondamentale di organizzazione in GCP che raggruppa risorse, billing e permessi IAM |
| **Pub/Sub** | Servizio di messaggistica asincrona publish-subscribe per la comunicazione disaccoppiata tra servizi |
| **Shared VPC** | Configurazione che condivide una VPC tra più progetti, centralizzando la gestione di rete |
| **SUD (Sustained Use Discount)** | Sconto automatico applicato da GCP alle VM Compute Engine utilizzate per più del 25% del mese |
| **VPC Service Controls** | Perimetro di sicurezza che limita l'accesso ai servizi GCP per prevenire l'esfiltrazione di dati |
| **Workload Identity** | Meccanismo che associa un service account Kubernetes a un service account GCP senza chiavi statiche |

> **Riferimenti e approfondimenti**: [Google Cloud Architecture Framework](https://cloud.google.com/architecture/framework), [Google Cloud Documentation](https://cloud.google.com/docs), [Google Cloud Best Practices](https://cloud.google.com/docs/enterprise/best-practices-for-enterprise-organizations)
