---
corso: "Gestione Piattaforme e DevOps"
fase: "7 — Architetture Avanzate"
modulo: 19
titolo: "Platform Engineering e Internal Developer Platform (IDP)"
versione: "Backstage 1.x · Port 2.x · Humanitec Platform Orchestrator · Crossplane 1.17 · Cortex 2.x"
livello: "Avanzato"
prerequisiti:
  - "05-kubernetes.md"
  - "07-ci-cd.md"
  - "15-secrets-management.md"
obiettivi:
  - "Comprendere la differenza tra DevOps tradizionale e Platform Engineering"
  - "Progettare e implementare un Internal Developer Platform (IDP) con Backstage"
  - "Configurare software catalog, tech docs e template di scaffolding in Backstage"
  - "Integrare l'IDP con la pipeline CI/CD, il service mesh e il secrets management"
  - "Misurare il successo della piattaforma con DORA metrics e Developer Experience (DevEx)"
tag: [platform-engineering, idp, backstage, developer-portal, golden-path, dora-metrics, devex, crossplane, port]
---

# Platform Engineering e Internal Developer Platform (IDP) — Documentazione Completa

> **Modulo 19** · **Aggiornamento:** 2026-07-16

> **Obiettivi di apprendimento**
>
> 1. Comprendere la differenza tra DevOps tradizionale e Platform Engineering
> 2. Progettare e implementare un Internal Developer Platform (IDP) con Backstage
> 3. Configurare software catalog, tech docs e template di scaffolding in Backstage
> 4. Integrare l'IDP con la pipeline CI/CD, il service mesh e il secrets management
> 5. Misurare il successo della piattaforma con DORA metrics e Developer Experience (DevEx)
>
> **Prerequisiti:** [Kubernetes](05-kubernetes.md) · [CI/CD](07-ci-cd.md) · [Secrets Management](15-secrets-management.md)
> **Tempo stimato:** 10-14 ore · **Livello:** Avanzato

## Idee guida

1. **Platform Engineering = prodotto per sviluppatori.** La piattaforma è un prodotto, i developer sono i clienti.
2. **Golden Path: la strada più semplice è quella sicura e corretta.** Non vietare le alternative, ma rendere la via corretta la più comoda.
3. **Self-service: developer non devono aspettare un ticket.** Ogni risorsa può essere provisioned in autonomia via catalog.
4. **Misurare: DORA metrics + Developer Experience surveys.** Senza metriche, non si sa se la piattaforma migliora.

---

## Indice

1. [Panoramica: da DevOps a Platform Engineering](#1-panoramica-da-devops-a-platform-engineering)
2. [Internal Developer Platform (IDP) — Architettura](#2-internal-developer-platform-idp--architettura)
3. [Backstage — Il Portale Developer Open Source di Spotify](#3-backstage--il-portale-developer-open-source-di-spotify)
4. [Software Catalog](#4-software-catalog)
5. [TechDocs — Documentazione as Code](#5-techdocs--documentazione-as-code)
6. [Software Templates — Scaffolding](#6-software-templates--scaffolding)
7. [Backstage Plugin Ecosystem](#7-backstage-plugin-ecosystem)
8. [Crossplane — Infrastructure as Code via K8s API](#8-crossplane--infrastructure-as-code-via-k8s-api)
9. [DORA Metrics e Developer Experience (DevEx)](#9-dora-metrics-e-developer-experience-devex)
10. [Implementazione Golden Path](#10-implementazione-golden-path)
11. [Confronto IDP: Backstage vs Port vs Cortex vs Humanitec](#11-confronto-idp-backstage-vs-port-vs-cortex-vs-humanitec)
12. [Best Practices](#12-best-practices)

---

## 1. Panoramica: da DevOps a Platform Engineering

### Il Problema della Cognitive Load

Con l'adozione del cloud e dei microservizi, ogni team di sviluppo deve gestire:
Docker, Kubernetes, Terraform, CI/CD, secrets management, monitoring, service mesh,
cost governance, compliance, e decine di altri tool. La **cognitive load** è diventata
insostenibile per un singolo developer.

**DevOps tradizionale** ("you build it, you run it"):
- Pro: ownership completo, autonomia
- Contro: ogni team reinventa la ruota, inconsistenza, cognitive load altissima

**Platform Engineering**:
- Il Platform Team costruisce una piattaforma interna che astrae la complessità
- I team di prodotto usano la piattaforma tramite self-service
- La piattaforma implementa le best practice una volta sola
- I developer si concentrano sul codice di business, non sull'infrastruttura

```
PRIMA (DevOps):
  Developer A → Kubernetes → Docker → Terraform → Vault → Prometheus → ...
  Developer B → Kubernetes → Docker → Terraform → Vault → Prometheus → ...
  Developer C → (reinventa tutto da zero)
  
  Risultato: 3 implementazioni diverse, 3 set di bug, 3 configurazioni da mantenere

DOPO (Platform Engineering):
  Developer A → IDP Portal → [selezione template] → deployment automatico
  Developer B → IDP Portal → [selezione template] → deployment automatico
  Developer C → IDP Portal → [selezione template] → deployment automatico
  
  Platform Team → K8s + Docker + Terraform + Vault + Prometheus (una volta, per tutti)
```

### Platform Team come Prodotto

Il Platform Team deve applicare a sé stesso il pensiero product:
- **Clienti**: i developer interni
- **Prodotto**: la piattaforma (IDP, CI/CD, infrastruttura)
- **Feedback loop**: DORA metrics + Developer Experience surveys
- **Roadmap**: priorità basate su pain point dei clienti, non su preferenze tecnologiche

---

## 2. Internal Developer Platform (IDP) — Architettura

### Componenti di un IDP maturo

```
┌─────────────────────────────────────────────────────────────────────┐
│                   INTERNAL DEVELOPER PLATFORM                        │
│                                                                     │
│  DEVELOPER PORTAL (Backstage)                                       │
│  ├── Software Catalog: inventario servizi, API, team                │
│  ├── TechDocs: documentazione tecnica interna                      │
│  ├── Software Templates: scaffolding nuovo servizio in 1 click     │
│  └── Dashboard: DORA metrics, SLO, costi per team                 │
│                                                                     │
│  GOLDEN PATHS (pathways pre-approvati)                              │
│  ├── Template microservizio Python/Go/Java                          │
│  ├── Template data pipeline (Airflow, dbt)                        │
│  └── Template ML training job                                      │
│                                                                     │
│  INFRASTRUTTURA SELF-SERVICE                                        │
│  ├── Crossplane: provision K8s + DB + RDS in K8s API style        │
│  ├── Vault: secrets management integrato nel template              │
│  └── ArgoCD: deploy automatico via GitOps                         │
│                                                                     │
│  OSSERVABILITÀ                                                      │
│  ├── Prometheus + Grafana: metriche                                │
│  ├── Loki: log aggregation                                         │
│  └── Jaeger: distributed tracing                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Layers dell'IDP

**Layer 1 — Developer Experience (DX Layer):**
Il portale developer (Backstage) è l'interfaccia unica.
I developer non devono conoscere i tool sottostanti.

**Layer 2 — Orchestration Layer:**
Backstage chiama API di tool come ArgoCD, Vault, Terraform Cloud, GitHub.
Il developer interagisce con una UI semplice; la piattaforma orchesta i tool.

**Layer 3 — Infrastructure Layer:**
Kubernetes, cloud provider, storage, networking.
Questo layer è astratto dal developer — gestito solo dal Platform Team.

---

## 3. Backstage — Il Portale Developer Open Source di Spotify

### Storia e Adozione

Backstage è stato creato da Spotify nel 2020 e donato alla CNCF (graduated 2022).
Usato da: Spotify, Netflix, American Airlines, Zalando, Twilio, e migliaia di altre organizzazioni.

### Architettura Backstage

```
ARCHITETTURA BACKSTAGE:

Frontend (React):
  ├── Plugin UI: ogni plugin contribuisce pagine e componenti React
  ├── App Config: app-config.yaml definisce integrazioni e plugin
  └── Router: navigazione tra plugin

Backend (Node.js Express):
  ├── Plugin Backend: ogni plugin ha la propria logica backend
  ├── Catalog: database dei componenti software (PostgreSQL)
  ├── Auth: integrazione con IdP (GitHub, Google, Okta, SAML)
  └── Search: indice ricercabile di tutto il catalog

Database:
  ├── PostgreSQL (produzione)
  └── SQLite (sviluppo locale)

Deployment:
  ├── Docker container
  ├── Kubernetes (Helm chart)
  └── Cloud: Netlify, Vercel (solo frontend)
```

---

## 4. Software Catalog

### catalog-info.yaml — Il DNA di ogni Componente

Il Software Catalog è il cuore di Backstage. Ogni servizio, API, libreria, website
è rappresentato da un file `catalog-info.yaml` nel repository.

```yaml
# Esempio: catalog-info.yaml per un microservizio

apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: order-service
  title: "Order Service"
  description: "Gestisce la creazione e il tracking degli ordini"
  
  annotations:
    # Integrazione GitHub Actions
    github.com/project-slug: myorg/order-service
    
    # TechDocs (documentazione)
    backstage.io/techdocs-ref: dir:.
    
    # Kubernetes (stato del deployment)
    backstage.io/kubernetes-id: order-service
    backstage.io/kubernetes-namespace: production
    
    # Grafana (dashboard)
    grafana/dashboard-selector: "folder=Production,tag=order-service"
    
    # SonarQube (qualità codice)
    sonarqube.org/project-key: myorg_order-service
  
  tags:
    - python
    - rest-api
    - critical
  
  links:
    - url: https://order-service.internal
      title: "Produzione"
    - url: https://grafana.internal/d/order-service
      title: "Dashboard Grafana"

spec:
  type: service
  lifecycle: production    # experimental | deprecated | production
  owner: team-backend      # chi è responsabile
  system: ecommerce-platform
  
  # Dipendenze: il catalog costruisce un grafo delle dipendenze
  consumesApis:
    - payment-api
    - inventory-api
  providesApis:
    - order-api
  
  dependsOn:
    - component:payment-service
    - resource:orders-database
```

### Tipi di Entità nel Catalog

```
BACKSTAGE ENTITY KINDS:

Component: un servizio, libreria, website, data pipeline
  type: service | library | website | documentation

API: contratto esposto da un Component
  type: openapi | asyncapi | grpc | graphql | thrift

Resource: infrastruttura esterna al codice
  type: database | s3-bucket | redis-cluster | ml-model

System: collezione di Component correlati
  Esempio: "ecommerce-platform" raggruppa order-service, payment-service

Domain: area di business più ampia
  Esempio: "commerce" raggruppa "ecommerce-platform", "marketplace"

Group: team, squad, chapter, tribe
User: singolo utente con appartenenza a Group

Location: source dell'entity (URL del catalog-info.yaml)
```

---

## 5. TechDocs — Documentazione as Code

### Docs as Code con MkDocs

```yaml
# mkdocs.yml nella root del repository
site_name: "Order Service"
docs_dir: docs/
theme:
  name: material

plugins:
  - techdocs-core    # plugin Backstage per generazione

nav:
  - Home: index.md
  - Architecture: architecture.md
  - API Reference: api.md
  - Runbook: runbook.md
  - ADR: decisions/
```

```markdown
<!-- docs/index.md -->
# Order Service

Il servizio gestisce la creazione e il tracking degli ordini.

## Quick Start

```bash
# Sviluppo locale
docker compose up
# L'app sarà disponibile su http://localhost:5000
```

## SLO

| Metrica | Target | Alert |
|---------|--------|-------|
| Disponibilità | 99.9% | < 99.5% |
| Latenza p99 | < 200ms | > 500ms |
| Error Rate | < 0.1% | > 1% |
```

---

## 6. Software Templates — Scaffolding

### Template: Nuovo Microservizio Python

```yaml
# template.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: python-microservice
  title: "Microservizio Python (Flask)"
  description: >
    Crea un nuovo microservizio Python con Flask, Docker, GitHub Actions,
    Kubernetes manifests, Prometheus metrics e TechDocs preconfigurati.
  tags: [python, flask, recommended]

spec:
  owner: platform-team
  type: service
  
  parameters:
    - title: "Informazioni servizio"
      required: [name, description, owner]
      properties:
        name:
          title: "Nome servizio"
          type: string
          pattern: "^[a-z][a-z0-9-]{2,49}$"
          description: "Kebab-case, es: order-processor"
        
        description:
          title: "Descrizione"
          type: string
        
        owner:
          title: "Team owner"
          type: string
          ui:field: OwnerPicker    # mostra i Group del catalog
          ui:options:
            catalogFilter:
              kind: Group
        
        tier:
          title: "Tier"
          type: string
          default: standard
          enum: [critical, standard, experimental]
  
  steps:
    # Step 1: fetch il template da un repo
    - id: fetch-template
      name: "Fetch template"
      action: fetch:template
      input:
        url: ./skeleton    # cartella con i file template
        values:
          name: ${{ parameters.name }}
          description: ${{ parameters.description }}
          owner: ${{ parameters.owner }}
    
    # Step 2: creare il repository GitHub
    - id: create-repo
      name: "Crea repository GitHub"
      action: publish:github
      input:
        repoUrl: "github.com?repo=${{ parameters.name }}&owner=myorg"
        description: ${{ parameters.description }}
        defaultBranch: main
        topics: [python, microservice, ${{ parameters.tier }}]
    
    # Step 3: registrare nel catalog
    - id: register
      name: "Registra nel catalog"
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps['create-repo'].output.repoContentsUrl }}
        catalogInfoPath: /catalog-info.yaml
  
  output:
    links:
      - title: "Repository"
        url: ${{ steps['create-repo'].output.remoteUrl }}
      - title: "Nel Catalog"
        entityRef: ${{ steps['register'].output.entityRef }}
```

---

## 7. Backstage Plugin Ecosystem

### Plugin Fondamentali

```
PLUGIN BACKSTAGE ESSENZIALI:

Catalog:
  @backstage/plugin-catalog                   → visualizzare entità
  @backstage/plugin-catalog-import            → importare catalog-info.yaml
  @backstage/plugin-catalog-graph             → grafo dipendenze

CI/CD:
  @backstage/plugin-github-actions            → GitHub Actions pipelines
  @backstage-community/plugin-gitlab          → GitLab CI
  @backstage-community/plugin-jenkins         → Jenkins

Kubernetes:
  @backstage/plugin-kubernetes                → visualizzare K8s resources
  @backstage/plugin-kubernetes-backend        → backend query K8s

Qualità e Sicurezza:
  @backstage-community/plugin-sonarqube       → qualità codice
  @backstage-community/plugin-snyk            → security scanning
  @roadiehq/backstage-plugin-security-insights → CVE insights

FinOps:
  @backstage-community/plugin-cost-insights   → costi cloud
  @backstage-community/plugin-opencost        → costi K8s

Monitoring:
  @backstage-community/plugin-grafana         → Grafana dashboard
  @backstage-community/plugin-pagerduty       → alert e on-call

Infrastruttura:
  @backstage/plugin-terraform                 → Terraform state
  @backstage-community/plugin-argo-cd         → ArgoCD deployment
  @backstage-community/plugin-vault           → Vault secrets
```

---

## 8. Crossplane — Infrastructure as Code via K8s API

### Provisioning Cloud tramite K8s Manifests

Crossplane permette di fare provision di risorse cloud (RDS, S3, GKE) usando
la stessa API K8s che si usa per i Pod.

```yaml
# Composite Resource Definition (XRD): definisce il "tipo" di infrastruttura
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xpostgresqldatabases.platform.myorg.com
spec:
  group: platform.myorg.com
  names:
    kind: XPostgreSQLDatabase
    plural: xpostgresqldatabases
  
  claimNames:
    kind: PostgreSQLDatabase     # ciò che lo sviluppatore vede
    plural: postgresqldatabases
  
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
                parameters:
                  type: object
                  properties:
                    storageGB:
                      type: integer
                      default: 20
                    tier:
                      type: string
                      enum: [basic, standard, premium]
                      default: standard
```

```yaml
# Lo sviluppatore crea questo Claim (non conosce AWS RDS):
apiVersion: platform.myorg.com/v1alpha1
kind: PostgreSQLDatabase
metadata:
  name: orders-db
  namespace: team-backend
spec:
  parameters:
    storageGB: 100
    tier: standard
  compositionSelector:
    matchLabels:
      provider: aws
      region: eu-west-1
  writeConnectionSecretToRef:
    name: orders-db-secret    # Crossplane scrive il secret K8s con la connection string
```

---

## 9. DORA Metrics e Developer Experience (DevEx)

### Le 4 Metriche DORA (DevOps Research and Assessment)

```
DORA METRICS — MISURARE LA PERFORMANCE DEL DELIVERY:

1. DEPLOYMENT FREQUENCY (quanto spesso si deploya):
   Elite: on-demand (più volte al giorno)
   High: tra una volta al giorno e una a settimana
   Medium: tra una volta a settimana e una al mese
   Low: meno di una volta al mese
   
   Misura: COUNT(deploy_production) / periodo

2. LEAD TIME FOR CHANGES (dal commit al deploy):
   Elite: < 1 ora
   High: 1 giorno - 1 settimana
   Medium: 1 settimana - 1 mese
   Low: > 1 mese
   
   Misura: deploy_timestamp - first_commit_timestamp

3. CHANGE FAILURE RATE (% deploy che causano incidenti):
   Elite: 0-5%
   High: 5-10%
   Medium: 10-15%
   Low: > 15%
   
   Misura: COUNT(incidents_triggered) / COUNT(deploys)

4. MEAN TIME TO RECOVERY (MTTR - tempo per riprendersi):
   Elite: < 1 ora
   High: < 1 giorno
   Medium: 1 giorno - 1 settimana
   Low: > 1 settimana
   
   Misura: incident_resolved_timestamp - incident_detected_timestamp

5. RELIABILITY (5a metrica aggiunta nel 2023):
   Misura se i SLO vengono rispettati nel tempo
   Target: 99.9% uptime mantenuto
```

### Developer Experience (DevEx)

```
DEVELOPER EXPERIENCE SURVEY (trimestrale):

Satisfaction (1-10):
  "Quanto sei soddisfatto della piattaforma?"
  
Flow State (1-10):
  "Riesci a concentrarti sul codice senza interruzioni?"
  
Cognitive Load (1-10):
  "Quanta energia mentale richiede gestire l'infrastruttura?"
  
Net Promoter Score (NPS):
  "Consiglieresti questa piattaforma a un collega?"

METRICHE OGGETTIVE:
  Time to First Deployment (TTFD): nuovo developer → primo deploy
  Build Time: durata media pipeline CI/CD
  Incident MTTR: tempo medio di risoluzione incidenti
  P2P (PR to Production): dal merge all'arrivo in prod
```

---

## 10. Implementazione Golden Path

### Struttura di un Golden Path

```
GOLDEN PATH: la via più semplice è quella corretta

Non proibire le alternative → renderle meno convenienti:

PRIMA (senza golden path):
  Developer A crea Dockerfile → reinventa il multi-stage
  Developer B crea Dockerfile → dimentica il non-root user
  Developer C crea Dockerfile → non ha le label giuste per Kyverno
  
  Risultato: 3 Dockerfile diversi, 3 livelli di sicurezza diversi

DOPO (con golden path):
  Developer → Backstage template → Dockerfile generato automaticamente
  Dockerfile: multi-stage, non-root, label corretti, seccomp, SBOM
  
  Risultato: tutti i Dockerfile uguali, tutti sicuri, nessuna cognitive load

IMPLEMENTAZIONE:
  1. Identificare i pain point (survey DevEx)
  2. Costruire il template (scheletro del servizio)
  3. Automatizzare il provisioning (GitHub repo, K8s namespace, Vault secrets)
  4. Documentare il golden path (TechDocs)
  5. Misurare l'adozione (% team che usano il template vs custom)
```

---

## 11. Confronto IDP: Backstage vs Port vs Cortex vs Humanitec

```
CONFRONTO SOLUZIONI IDP (2026):

BACKSTAGE (Spotify/CNCF):
  Tipo: Open source (Apache 2.0), self-hosted
  Pro: massima flessibilità, plugin ecosystem enorme, CNCF graduated
  Contro: richiede team per mantenimento, setup complesso
  Costo: gratuito (self-hosted)
  Adozione: >3000 organizzazioni (2024)
  Best for: organizzazioni con team platform dedicato

PORT (Port.io):
  Tipo: SaaS + self-hosted
  Pro: setup in minuti, UI moderna, no maintenance
  Contro: vendor lock-in, costo
  Costo: da $12/utente/mese
  Best for: team piccoli o senza risorse per gestire Backstage

CORTEX (Cortex.io):
  Tipo: SaaS
  Pro: scorecard e quality gates, ottimo per engineering excellence
  Contro: SaaS, meno customizzabile di Backstage
  Costo: enterprise pricing
  Best for: organizzazioni focalizzate su engineering quality metrics

HUMANITEC PLATFORM ORCHESTRATOR:
  Tipo: SaaS (cloud-based)
  Pro: score model standardizzato, integrazione Backstage
  Contro: costo, vendor dependency
  Costo: enterprise pricing
  Best for: platform engineers che vogliono IDP + orchestration out-of-box

RACCOMANDAZIONE:
  Startup/Scale-up (< 50 dev): Port o Cortex (SaaS, no ops burden)
  Mid-size (50-500 dev): Backstage (flessibilità, community)
  Enterprise (> 500 dev): Backstage o Humanitec (scalabilità, controllo)
```

---

## 12. Best Practices

```
PLATFORM ENGINEERING — REGOLE D'ORO:

1. TRATTARE LA PIATTAFORMA COME UN PRODOTTO
   ✓ Product manager dedicato alla piattaforma
   ✓ Roadmap pubblica con priorità guidate da developer feedback
   ✓ SLA della piattaforma stessa (es. template deploy < 5 min)
   ✗ Non: "facciamo quello che il management dice"

2. GOLDEN PATH PRIMA DI TUTTO
   ✓ Ogni nuovo servizio segue il template
   ✓ Il template è la via più semplice, non quella obbligata
   ✓ Chi devia deve documentare il perché (ADR)
   ✗ Non: bloccare completamente le alternative

3. MISURARE CONTINUAMENTE
   ✓ DORA metrics automatizzate in ogni pipeline
   ✓ Developer Experience survey trimestrale
   ✓ SLO della piattaforma monitorati 24/7
   ✗ Non: "feedback informale" senza dati

4. TEAM SIZE E STRUTTURA
   ✓ 1 platform engineer ogni 10-15 developer (Puppet survey)
   ✓ Team embedded: platform engineer nei team prodotto come advisor
   ✗ Non: platform team in silos separati dai developer

5. BACKWARD COMPATIBILITY
   ✓ Versioning dei template e delle API
   ✓ Deprecation path graduale (6+ mesi di preavviso)
   ✓ Migration guide automatizzata dove possibile
   ✗ Non: breaking change senza avviso

6. DOCUMENTAZIONE ALWAYS UP TO DATE
   ✓ Docs as Code: TechDocs in ogni repository
   ✓ Esempi funzionanti (non pseudo-codice)
   ✓ ADR (Architecture Decision Records) per ogni scelta
   ✗ Non: wiki che nessuno aggiorna

7. TEAM TOPOLOGIES
   ✓ Platform Team = Enabling Team (Skelton & Pais, 2019)
   ✓ Stream-aligned teams: autonomi sulla propria domanda di business
   ✓ Complicated Subsystem teams: per domini altamente specializzati
   ✗ Non: platform team come gatekeeper che rallenta i team prodotto
```

---

> **Versioni di riferimento:** Backstage 1.30.x (2024), Crossplane 1.17.x (2024),
> Port 2.x (2024), Cortex 2.x. DORA Report 2024 (Accelerate State of DevOps).
> Team Topologies (Skelton & Pais, 2019) — modello organizzativo fondante del Platform Engineering.
> CNCF Platform Engineering Maturity Model v1.0 (2023).
> Gartner: entro il 2026, il 80% delle grandi organizzazioni avranno un platform engineering team.
