# CMDB e Asset Management — Implementazione con GLPI, Snipe-IT, ServiceNow

> **Modulo 13** · **Tempo:** 90 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **CMDB pulito > grande.** 1000 CI accurati > 10K con 30% obsoleti.
2. **Auto-discovery + reconcile periodico.** Manual entry e drift.
3. **Relationship CI critico per impact analysis.** "Se cade DB-01, quali servizi?"
4. **Orphan cleanup mensile.** CI senza relationship = candidato remozione.


## Indice

1. [Panoramica](#panoramica)
2. [Concetti Fondamentali](#concetti-fondamentali)
   - [Cos'è un CMDB](#cosè-un-cmdb)
   - [CMDB vs Asset Management](#cmdb-vs-asset-management)
   - [Modello Configuration Item (CI)](#modello-configuration-item-ci)
   - [Service Mapping](#service-mapping)
   - [Discovery automatizzata](#discovery-automatizzata)
   - [Federazione CMDB](#federazione-cmdb)
   - [Pattern di adozione](#pattern-di-adozione)
3. [Guida Pratica](#guida-pratica)
   - [GLPI](#glpi)
   - [Snipe-IT](#snipe-it)
   - [ServiceNow CMDB](#servicenow-cmdb)
   - [Cenni: i-doit, iTop, Lansweeper, Device42, Ralph](#cenni-i-doit-itop-lansweeper-device42-ralph)
4. [Configurazione e Implementazione](#configurazione-e-implementazione)
   - [Setup GLPI 10 + FusionInventory step-by-step](#setup-glpi-10--fusioninventory-step-by-step)
   - [Modellazione esempi (server, VM, app, service)](#modellazione-esempi-server-vm-app-service)
   - [Automazione popolamento via REST API Python](#automazione-popolamento-via-rest-api-python)
   - [Mantenimento qualità dati](#mantenimento-qualità-dati)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Riferimenti](#riferimenti)

---

## Panoramica

Il Configuration Management Database (CMDB) è uno dei concetti più dibattuti dell'IT Service Management. Promesso come la "single source of truth" per tutto ciò che esiste nell'IT, è stato sia santificato come fondamento di ITIL sia denigrato come progetto da milioni di euro che termina con un database stantio popolato a metà.

La verità sta nel mezzo. Un CMDB ben fatto è uno strumento operativo straordinario: permette di rispondere in secondi a domande come "se questo server cade, quali servizi business si fermano?", "quali sono tutti gli asset coperti dalla licenza Oracle in scadenza?", "su quante VM gira ancora Windows Server 2012 R2?", "qual è l'impatto di un cambio di certificato SSL su questo dominio?". Un CMDB mal fatto è un cimitero di dati obsoleti che nessuno consulta perché sa che mente.

La differenza tra i due esiti è il modello adottato. CMDB monolitico-greenfield-totale → fallimento garantito. CMDB iterativo-federato-focused-on-services → asset operativo. Questo documento copre entrambi gli scenari, mostrando perché il primo è anti-pattern e come implementare correttamente il secondo, con focus su tre tool: GLPI (open source, popolare in EU/Italia), Snipe-IT (asset-focused, semplice), ServiceNow (gold standard enterprise).

L'asset management è il fratello commerciale del CMDB: mentre la CMDB tracciare ciò che gestisci operativamente (con relazioni e servizi), l'asset management tracciare ciò che possiedi finanziariamente (con costo, ammortamento, garanzia, contratto). I due si sovrappongono ma non coincidono. Questo documento copre entrambe le viste e mostra come integrarle, perché in una PMI italiana 50 dipendenti il vero valore arriva quando le due viste convergono in un singolo strumento (tipicamente GLPI o Snipe-IT + integrazione).

---

## Concetti Fondamentali

### Cos'è un CMDB

Un Configuration Management Database (CMDB) è un repository che contiene informazioni sui Configuration Items (CI) — le entità che costituiscono l'ambiente IT — e sulle relazioni tra di essi. Il termine nasce con ITIL v2 nei primi anni 2000 e si consolida in ITIL v3 (2007), per evolvere in ITIL 4 sotto la practice "Service Configuration Management".

Un CI è qualsiasi componente che debba essere gestito per fornire un servizio IT. Esempi: server fisici, VM, container, dispositivi di rete, database, applicazioni, servizi business, contratti, persone (in CMDB estesi), location, licenze.

La differenza chiave tra un CMDB e un semplice inventario è il **modello di relazioni**. Un inventario dice "ho 50 server, 200 PC, 30 stampanti". Un CMDB dice "il server SRV-DB01 ospita la database instance ORDERS_PROD che è usata dall'applicazione OrderManagement che eroga il servizio business 'Gestione Ordini' che è critico per il processo Vendite". Questa catena di dipendenze è ciò che permette analisi di impatto, root cause analysis e service mapping.

Il CMDB ITIL "ortodosso" — repository unico, completo, sempre aggiornato — è raramente raggiungibile in pratica. Realisticamente si parla di **CMDB pragmatica**: copertura sui servizi business critici, dati di qualità verificata, federata con sistemi specialistici (AD, Intune, JAMF, vCenter, cloud) anziché duplicare tutto.

### CMDB vs Asset Management

Confusione frequente. Le due discipline si sovrappongono ma hanno obiettivi diversi.

| Aspetto | CMDB | IT Asset Management (ITAM) |
|---------|------|----------------------------|
| **Domanda fondamentale** | "Cosa gestisco operativamente?" | "Cosa possiedo finanziariamente?" |
| **Owner tipico** | IT Operations / Service Management | IT Finance / Procurement |
| **Granularità** | Anche entità intangibili (servizi, contratti SLA, processi) | Asset tangibili (hardware) e intangibili (software, licenze) |
| **Ciclo di vita tracciato** | Operativo: provisioning, modifiche, decommissioning | Finanziario: acquisto, ammortamento, dismissione, smaltimento |
| **Attributi chiave** | Stato, relazioni, ownership operativo, criticità | Costo, fornitore, garanzia, contratto, ammortamento |
| **Use case** | Impact analysis, change management, problem analysis | Audit licenze, ottimizzazione costi, refresh hardware |
| **Frequenza aggiornamento** | Continuo (ad ogni change) | Periodico (acquisti, fine garanzia, audit) |

Esempio concreto: un laptop Dell Latitude 5530 acquistato il 15/03/2024 per €1.230 con garanzia ProSupport NBD fino al 15/03/2027, assegnato a Mario Rossi del dipartimento Vendite, con seriale 7XYZ123, MAC address aa:bb:cc:dd:ee:ff, IP 10.0.5.42, hostname IT-VND-MR01, su cui è installato Windows 11 Pro, Office 365 E3, AutoCAD LT 2024, VPN client.

- **Asset**: tutto ciò che riguarda costo, fornitore, garanzia, dipendente assegnato, ammortamento, contratto.
- **CI**: tutto ciò che riguarda hostname, IP, MAC, OS, software installato, ruolo (workstation utente vendite), criticità, servizi che usa.

Lo stesso oggetto fisico vive in due dimensioni. Tool come **GLPI** e **ServiceNow** integrano nativamente le due viste; **Snipe-IT** è puro asset, richiede integrazione con CMDB esterno o accetta di gestire solo asset.

### Modello Configuration Item (CI)

Il modello CI definisce **classi/tipi** di CI, i loro **attributi** e le **relazioni** ammesse.

**Classi tipiche di CI**

- Hardware: Server, Network Device (Switch/Router/Firewall/AP), Workstation, Laptop, Mobile Device, Printer, Storage Array, UPS, Rack
- Software: Operating System, Application, Database Instance, Web Service, Container, Container Image
- Virtualization: Hypervisor, Virtual Machine, Cluster, Resource Pool
- Cloud: Cloud Account, VPC/VNet, Subnet, Cloud VM, Managed Database, S3 Bucket, Lambda Function, ecc.
- Network: VLAN, Subnet, IP Address, DNS Zone, Certificate, Load Balancer
- Service: Business Service, Application Service, Technical Service, Service Offering
- Contract / License: Software License, Maintenance Contract, SLA, Vendor Contract
- People & Org: User, Group, Department, Location, Site

**Attributi tipici di un CI**

- Identità: nome, ID univoco, alias
- Tipo: classe del CI
- Stato: in produzione, in test, in manutenzione, ritirato
- Ownership: technical owner, business owner
- Criticità: bassa/media/alta/critica
- Lifecycle: data installazione, data fine vita prevista
- Specifici per tipo: per server (CPU, RAM, storage, OS, hostname, IP); per applicazione (versione, vendor, deploy date, URL)

**Relazioni tipiche tra CI**

Le relazioni sono direzionali e tipizzate. ITIL non prescrive un set fisso, ma un vocabolario standard è:

| Relazione | Descrizione | Esempio |
|-----------|-------------|---------|
| `depends on` | A non funziona senza B | App OrderMgmt depends on DB ORDERS_PROD |
| `hosted on` | A risiede su B | DB ORDERS_PROD hosted on Server SRV-DB01 |
| `runs on` | A esegue su B (per VM/container) | VM srv-db01 runs on Hypervisor ESX-PROD-01 |
| `connected to` | A connesso a B (network) | Switch SW-CORE-01 connected to Router RTR-WAN |
| `member of` | A è membro di B (cluster, group) | ESX-PROD-01 member of Cluster ESX-PROD |
| `used by` | A è usato da B | Service Email used by Department All |
| `installed on` | Software A installato su HW B | Office 365 installed on Workstation IT-VND-MR01 |
| `manages` | A gestisce B | Admin Mario Rossi manages Server SRV-DB01 |

Il grafo di CI + relazioni è la chiave del CMDB. Una visualizzazione grafica (GLPI ha "Topology", ServiceNow ha "Dependency Views", iTop ha "Impact Analysis") permette di vedere immediatamente l'impatto di un cambio o guasto.

### Service Mapping

Il Service Mapping è il processo che collega i CI tecnici (server, database, network) ai servizi business (Gestione Ordini, Posta Aziendale, ERP). È **top-down** (parto dal servizio business e mappo le componenti tecniche) o **bottom-up** (parto dai CI tecnici e ricostruisco i servizi).

Top-down è preferibile perché:
- Si focalizza su ciò che ha valore business
- Forza la definizione di "cosa è un servizio" per il business
- Limita il scope (non si mappa tutto, solo ciò che serve a un servizio)

ServiceNow ha un modulo dedicato "Service Mapping" che fa discovery automatica delle dipendenze attraverso pattern (es. parte dall'URL del servizio business, segue la catena: load balancer → web server → app server → database server). È costoso ma estremamente potente. In open source, GLPI e iTop permettono modellazione manuale con qualche aiuto da plugin.

**Esempio mappatura "Gestione Ordini" — PMI italiana**

```
[Servizio Business: Gestione Ordini] (criticità: alta)
  ├─ used by → [Dipartimento Vendite]
  ├─ used by → [Dipartimento Logistica]
  ├─ depends on → [Application: OrderMgmt v3.4]
  │                ├─ hosted on → [VM: app-orders-prod-01]
  │                │              └─ runs on → [Hypervisor: esx-prod-02]
  │                │                            └─ member of → [Cluster: ESX-PROD]
  │                ├─ depends on → [DB Instance: ORDERS_PROD (PostgreSQL 14)]
  │                │                ├─ hosted on → [VM: db-orders-prod-01]
  │                │                └─ backup → [Veeam Job: ORDERS_DAILY]
  │                ├─ depends on → [Service: Email Aziendale (per notifiche)]
  │                └─ depends on → [Service: Storage NAS \\nas01\orders\]
  └─ documented in → [KB Article: KB-ORD-001 Procedura Ordini]
```

Da questa mappa, in un ticket "OrderMgmt non risponde", l'agent vede immediatamente: la VM, l'hypervisor, il database, lo storage, il backup. Può aprire ticket child di chiunque sia "depends on", verificare lo stato, escalation al team giusto.

### Discovery automatizzata

Popolare manualmente un CMDB è insostenibile oltre i 50 CI. La discovery automatica è essenziale.

**Tecniche di discovery**

- **Agentless via SNMP**: per dispositivi di rete (switch, router, AP, printer). Polling SNMP v2c/v3 su community/credenziali. Estrae: hostname, MAC, modello, OS version, interfacce, neighbor (LLDP/CDP per topology).
- **Agentless via SSH/CLI**: per server Unix/Linux/network. Login con account read-only, esecuzione comandi (uname, cat /etc/os-release, lscpu, free -h, lsblk, dpkg/rpm -l).
- **Agentless via WMI/WinRM**: per Windows. Query a `Win32_*` classes (Win32_OperatingSystem, Win32_Processor, Win32_LogicalDisk, Win32_Product, Win32_NetworkAdapterConfiguration).
- **Agent-based**: agent installato sul target che invia inventario al server (FusionInventory Agent, OCS Inventory Agent, Lansweeper Agent, Tanium Agent, Snipe-IT helper script).
- **Network Discovery (sweep)**: NMAP scan su range IP per scoprire host vivi, poi tentativo identificazione (OS detection -O, service detection -sV).
- **Cloud Discovery via API**: AWS (boto3, AWS Config), Azure (Azure Resource Graph, Az CLI), GCP (gcloud asset inventory), VMware vCenter (PowerCLI, govc).
- **Integration con sistemi specialistici**: Active Directory (LDAP query per utenti, computer, group), Intune (Graph API), JAMF (REST API per Mac), vCenter (REST API/SOAP), HPE iLO/Dell iDRAC/Lenovo XClarity per BMC.

**Trade-off agent vs agentless**

| Aspetto | Agent-based | Agentless |
|---------|-------------|-----------|
| Deploy | Richiede installazione su ogni target | Solo credenziali centralizzate |
| Mantenimento | Aggiornare agent periodicamente | Nessun software sul target |
| Profondità dati | Massima (accesso completo locale) | Limitata a ciò che protocollo espone |
| Footprint risorse | Memoria/CPU sul target (modesta) | Carico sul collector |
| Dispositivi senza OS gestibile | Ovviamente no | Sì (switch, printer) |
| Latenza dati | Tempo reale o vicino | Cadenza scan (tipicamente notturna) |

In pratica si combina: agent per workstation/server, agentless SNMP per network/printer, API per cloud/virtualizzazione/sistemi specialistici.

### Federazione CMDB

Antipattern: replicare in CMDB tutti i dati che già esistono altrove. Risultato: due sistemi che divergono, dati obsoleti, lavoro manuale.

Pattern corretto: **federazione**. Il CMDB centrale contiene i CI con un set minimo di attributi e i collegamenti ai sistemi authoritative. Per dettagli specifici si consulta il sistema authoritative.

| Tipo di CI | Sistema authoritative |
|-----------|---------------------|
| Utenti, gruppi, computer Windows joined a dominio | Active Directory |
| Workstation iOS/macOS gestite | JAMF |
| Workstation Windows gestite via MDM | Intune |
| VM e infrastruttura virtuale | vCenter |
| Risorse cloud AWS | AWS Config / Tags |
| Risorse cloud Azure | Azure Resource Graph |
| Container in Kubernetes | API server K8s |
| Patches applicate | WSUS/SCCM/Satellite |
| Antivirus status | Defender XDR / SentinelOne / CrowdStrike |
| Backup status | Veeam / Acronis / Networker |

Il CMDB referenzia il CI con un identificatore univoco (es. SAM account name per AD, distinguishedName, instance-id AWS) e usa l'API del sistema authoritative per recuperare al volo i dettagli quando servono.

ServiceNow CMDB ha un meccanismo formale chiamato **CMDB IRE** (Identification and Reconciliation Engine) che gestisce CI provenienti da più source con regole di precedence per attributo.

### Pattern di adozione

**Regola d'oro: start small, focus on services.**

**Fase 1 — Top services first (mese 1-2)**

Identificare i 5-10 servizi business più critici (vendite, contabilità, posta, ERP, file server). Per ciascuno, mappare CI critici e relazioni. Risultato: 50-200 CI, tutti rilevanti, tutti con qualità verificata.

**Fase 2 — Discovery e copertura (mese 3-6)**

Attivare discovery automatica per popolare CI mass (workstation, server, network device). Popolare attributi base. Non investire ancora in qualità relazioni per CI marginali.

**Fase 3 — Service Mapping completo (mese 6-12)**

Estendere mappatura a tutti i servizi a catalogo. Definire process di certificazione CI ogni 90 giorni per owner di servizio.

**Fase 4 — Integrazione operativa (mese 12+)**

CMDB integrata con: Incident (auto-popolazione CI impattato), Change (auto-impact analysis), Problem (relazioni causali), Monitoring (alert mappato a CI/servizio). A questo punto la CMDB è asset operativo.

**Anti-pattern: "swamp di dati irrilevanti"**

Tracciare in CMDB dettagli che non servono mai (versione precisa firmware UPS, MAC address di ogni dispositivo USB connesso) genera rumore. La domanda da farsi: "se questo dato cambia, qualcuno deve agire? se non cambia per 5 anni, qualcuno se ne accorge?". Se entrambe le risposte sono no, il dato non va in CMDB.

---

## Guida Pratica

### GLPI

GLPI (Gestion Libre de Parc Informatique) è il principale ITSM open source di origine francese. Nato nel 2003, mantenuto da Teclib' (sponsor commerciale) e community attiva. Adozione massiccia in EU, in particolare Francia, Italia, Spagna, settore pubblico (scuole, comuni, ASL) e MSP.

**Punti di forza**

- Open source GPL, free, no vendor lock-in
- Coverage ampia: ticketing ITIL, ITAM, CMDB, finance, contratti, knowledge base, project management
- Modulare: 200+ plugin community (FusionInventory, GenericObject, OCS Sync, FormCreator, GLPI Inventory, Reports)
- Multi-entity: gestione di più "tenant" (utile per MSP che gestiscono più clienti dallo stesso GLPI)
- Localizzazione completa in italiano
- REST API moderna (GLPI 9.5+) per automazione
- Integrazione LDAP/AD nativa, SAML SSO via plugin
- Self-hostable su LAMP standard

**Punti deboli**

- UI datata per gli standard 2024 (sebbene migliorata in v10)
- Performance può degradare con database molto grandi (>500.000 ticket storici)
- Documentazione comunitaria, non sempre aggiornata
- Customizzazione complessa richiede competenze PHP

**Architettura tipica**

- Apache/Nginx + PHP 7.4-8.2 + MariaDB 10.6/MySQL 8.0
- 1 server applicativo + database (può essere stesso host per piccole installazioni)
- Storage: dimensione database scala con # ticket + # documenti allegati (consiglio: filesystem separato per `/files`)
- Sizing tipico PMI 50 dip: 4 vCPU, 8 GB RAM, 100 GB SSD, MariaDB locale

**Modulo CMDB in GLPI**

GLPI tratta come CI nativi: Computers, Network equipment, Printers, Phones, Monitors, Peripherals, Software, Software Licenses, Cartridges, Consumables, Racks, Enclosures, PDU, Cluster, Domain, Certificate. Tramite il plugin **GenericObject** si possono definire classi CI custom (es. Cloud Instance, Service, Database Instance).

Le relazioni si modellano via "Connections" (es. Computer → Monitor) o tramite "Links" tra entità. Per modellare servizi, il pattern comune è:
- Creare una entità "Application" (Software in GLPI o classe custom)
- Linkare Application → Computer (hosted on)
- Linkare Application → Application (depends on)
- Creare classe custom "BusinessService" via GenericObject
- Linkare BusinessService → Application (uses)

Per discovery automatica, plugin **FusionInventory** è lo standard de-facto (fino a GLPI 10.x). Da GLPI 10.0.3+ e soprattutto GLPI 11, la discovery nativa con **GLPI Agent** sostituisce progressivamente FusionInventory.

#### GLPI 11 e Inventory Nativo

Con il rilascio di GLPI 11.0 (ramo stabile, ultimo fix 11.0.7 a maggio 2026) l'architettura dell'inventario cambia radicalmente:

- **Inventory server nativo**: GLPI accetta file di inventario in formato XML e JSON tramite POST HTTP diretto, senza bisogno del plugin FusionInventory come intermediario. Il server di inventario nativo processa, deduplicare e inserisce i CI nel database con regole di matching configurabili.
- **GLPI Agent**: l'agent ufficiale (scritto in Perl, disponibile per Windows/macOS/Linux) sostituisce FusionInventory Agent. Versione corrente 1.16 con roadmap verso 1.17. Supporta: computer inventory, network discovery, network SNMP inventory, ESX remote inventory, deploy (distribuzione software), collect (raccolta file, registry Windows, query WMI custom).
- **Toolbox**: il GLPI Agent introduce un'interfaccia Toolbox per configurare e schedulare task di discovery e inventario SNMP direttamente dall'agent, senza dipendere da scheduling lato server. Utile per agent in ambienti con connettività intermittente o dietro firewall restrittivi.
- **Protocollo GLPI Native Inventory Protocol (GNIP)**: comunicazione diretta agent-server, con supporto per compressione, autenticazione mutua TLS, e trasferimento incrementale (solo delta rispetto all'ultimo inventario inviato).

**Migrazione FusionInventory → GLPI Agent**

La transizione è graduale:

1. GLPI 10.0.x: FusionInventory funziona, GLPI Agent supportato in parallelo. Il plugin FusionInventory riceve ancora aggiornamenti di manutenzione.
2. GLPI 11.0.x: il plugin FusionInventory ha un fork "Migration Tool" (FormCreator Migration Tool v3.0.0) che prepara i dati per la migrazione. L'inventario nativo è la via ufficiale. FusionInventory può ancora funzionare ma non è la strada raccomandata.
3. Raccomandazione 2026: per nuove installazioni, usare GLPI 11 + GLPI Agent. Per installazioni esistenti con FusionInventory, pianificare migrazione entro fine 2026.

Passi di migrazione:
```bash
# 1. Installare GLPI Agent su tutti i target (coesiste con FusionInventory Agent)
# Windows — MSI silenzioso
msiexec /i glpi-agent-1.16-x64.msi /quiet ^
  SERVER=https://glpi.azienda.it ^
  TAG=MIGRAZIONE ^
  EXECMODE=Service

# 2. Verificare che l'inventario arrivi al server nativo
# In GLPI 11: Amministrazione > Inventario > Inventari ricevuti
# Dovrebbe apparire il nuovo host con source "GLPI Agent"

# 3. Una volta verificato su batch pilota, rimuovere FusionInventory Agent
# Windows:
msiexec /x {FUSION_PRODUCT_GUID} /quiet
# Linux:
sudo apt remove fusioninventory-agent

# 4. Disattivare plugin FusionInventory in GLPI
# Setup > Plugin > FusionInventory > Disattiva
```

#### Plugin CMDB Infotel per GLPI

Il plugin **CMDB** sviluppato da InfotelGLPI (versione corrente 3.1.5 per GLPI ~11.0) arricchisce le funzionalità CMDB native di GLPI con:

- **Icone personalizzate per tipo CI**: ogni classe di oggetto può avere un'icona distintiva nella visualizzazione topologica, migliorando la leggibilità dei diagrammi di impatto.
- **Campi informativi custom nell'analisi di impatto**: è possibile aggiungere aree di informazione con campi personalizzati direttamente nella vista di impact analysis, senza uscire dalla mappa delle dipendenze.
- **Oggetto "Service"**: il plugin aggiunge un tipo di oggetto "Service" utilizzabile nell'analisi di impatto. GLPI nativo ha le classi hardware/software/network, ma manca un concetto di "servizio business" — il plugin lo introduce.
- **Supporto per oggetti core aggiuntivi**: permette di includere nell'analisi di impatto oggetti GLPI che non sono abilitati di default (es. certificati, domini, PDU).

Configurazione dell'analisi di impatto in GLPI 11:
1. Navigare a **Configurazione > Generale > Analisi di impatto**
2. Selezionare i tipi di elemento per cui attivare l'analisi (Computers, Network equipment, Software, e con il plugin CMDB: Services, custom objects)
3. Nella scheda di ogni CI, tab "Analisi di impatto": aggiungere dipendenze con frecce direzionali
4. Le frecce viola indicano dipendenza bidirezionale (entrambi gli elementi impattati)
5. Le frecce nere indicano nessun impatto da quell'elemento

#### Ecosistema Plugin GLPI — Marketplace

Il Marketplace GLPI (accessibile da Setup > Plugin > Marketplace, richiede licenza GLPI Network per alcuni plugin) offre oltre 200 plugin. I più rilevanti per CMDB/ITAM:

| Plugin | Funzione | Licenza |
|--------|----------|---------|
| **CMDB** (Infotel) | Service objects, impact analysis estesa | GPL |
| **GenericObject** | Classi CI custom con attributi personalizzati | GPL |
| **FormCreator** | Form personalizzati che generano ticket/change | GPL |
| **GLPI Inventory** | Complemento per inventario nativo avanzato | Commerciale |
| **Reports** | Report SQL personalizzabili con export CSV/PDF | GPL |
| **Dashboard** | Dashboard KPI configurabili | GPL/Commerciale |
| **Connections** | Gestione connessioni fisiche tra CI (cavi, porte) | GPL |
| **Racks** | Visualizzazione rack con posizionamento U | Nativo GLPI 10+ |
| **Carbon** | Calcolo impronta carbonica degli asset digitali | GPL |
| **SmartAssign** | Assegnazione automatica ticket basata su regole | Commerciale |
| **Geolocation** | Posizionamento geografico asset su mappa | GPL |
| **Fields** | Campi custom aggiuntivi su qualsiasi tipo GLPI | GPL |
| **OCS Import** | Importazione da OCS Inventory NG | GPL |
| **Escalade** | Escalation automatica ticket tra gruppi | GPL |

Il plugin **Carbon** (rilasciato ottobre 2025) è particolarmente innovativo: trasforma la CMDB in uno strumento di gestione della transizione ecologica, calcolando l'impronta carbonica dei servizi digitali basandosi sugli asset inventariati (server, storage, network, workstation) e sul loro consumo energetico stimato. Utile per compliance con direttive UE sulla sostenibilità digitale e per reporting ESG aziendale.

**FormCreator e workflow ITSM**

FormCreator merita menzione speciale: permette di creare form web personalizzati (es. "Richiesta nuovo PC", "Richiesta accesso VPN", "Segnalazione guasto stampante") che alla compilazione generano automaticamente ticket GLPI con campi pre-popolati, categoria corretta, assegnazione automatica e CI collegato. In GLPI 11, le form native sostituiscono progressivamente FormCreator — il Migration Tool v3.0.0 facilita la transizione.

### Snipe-IT

Snipe-IT è un asset management open source nato nel 2013, sviluppato da Grokability. Concepito esplicitamente come tool di IT asset management — non ITSM, non CMDB completo. La filosofia: fare una cosa sola e farla bene.

**Punti di forza**

- Focus laser: asset management, basta
- UX moderna e pulita (Bootstrap-based, mobile-friendly)
- REST API completa e ben documentata
- Deploy semplice via Docker
- License management eccellente (tracking attivazioni, scadenze, audit)
- Audit log completo: chi ha fatto cosa quando
- Multi-location, multi-company
- Categories, manufacturers, suppliers configurabili
- Checkout/checkin asset a utenti, location, asset (es. monitor a workstation)
- Custom fields per tipologia asset
- Email notifications (asset assegnato, in scadenza garanzia, license expiring)
- Integration con LDAP/AD/SAML
- Support per QR code labels

**Punti deboli**

- No ITIL ticketing (deve essere accoppiato a tool esterno)
- No CMDB con relazioni complesse (relazioni limitate a checkout)
- Discovery non nativa (richiede script esterni o agent terzi)
- Reporting base, no analytics avanzata

**Casi d'uso ideali**

- PMI con 50-500 asset HW dove l'ITSM è separato (es. tickets via Freshdesk, Jira SM)
- MSP che vogliono asset dei clienti separati ma non ITIL completo
- Aziende dove la priorità è audit licenze e compliance

**Deploy con Docker**

```bash
# docker-compose.yml minimal
version: '3.8'
services:
  snipeit:
    image: snipe/snipe-it:latest
    container_name: snipeit
    restart: unless-stopped
    depends_on:
      - mysql
    env_file:
      - .env
    ports:
      - "80:80"
    volumes:
      - ./storage:/var/lib/snipeit
  mysql:
    image: mysql:8.0
    container_name: snipeit-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - ./mysql:/var/lib/mysql
```

```bash
# .env
APP_KEY=base64:GENERATE_WITH_php_artisan_key:generate
APP_URL=https://snipeit.azienda.local
APP_TIMEZONE=Europe/Rome
APP_LOCALE=it
DB_CONNECTION=mysql
DB_HOST=mysql
DB_PORT=3306
DB_DATABASE=snipeit
DB_USERNAME=snipeit
DB_PASSWORD=STRONG_PASS_HERE
MYSQL_ROOT_PASSWORD=STRONG_ROOT_PASS
MYSQL_DATABASE=snipeit
MYSQL_USER=snipeit
MYSQL_PASSWORD=STRONG_PASS_HERE
MAIL_MAILER=smtp
MAIL_HOST=smtp.azienda.local
MAIL_PORT=587
MAIL_USERNAME=snipeit@azienda.local
MAIL_PASSWORD=SMTP_PASS
MAIL_FROM_ADDR=snipeit@azienda.local
MAIL_FROM_NAME='Snipe-IT'
```

```bash
docker compose up -d
# Prima volta: setup wizard via web https://snipeit.azienda.local
```

**Integrazione discovery via SCCM/JAMF**

Snipe-IT non discovera, ma riceve via API. Pattern comune: SCCM esporta JSON degli asset Windows, script Python POST a Snipe-IT. Per Mac: webhook JAMF → Snipe-IT.

```python
import requests
import json

SNIPE_URL = "https://snipeit.azienda.local"
TOKEN = "JWT_TOKEN_FROM_SETTINGS_API"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Esempio: aggiunta asset
asset = {
    "asset_tag": "IT-NB-2024-0042",
    "name": "Latitude 5530 Mario Rossi",
    "serial": "7XYZ123",
    "model_id": 12,         # ID del modello già censito
    "status_id": 4,         # 4 = Ready to Deploy
    "company_id": 1,
    "location_id": 3,
    "purchase_date": "2024-03-15",
    "purchase_cost": 1230.00,
    "warranty_months": 36,
    "supplier_id": 2,
    "_snipeit_mac_address_8": "aa:bb:cc:dd:ee:ff",  # custom field
    "_snipeit_hostname_9": "IT-VND-MR01"
}

resp = requests.post(
    f"{SNIPE_URL}/api/v1/hardware",
    headers=headers,
    data=json.dumps(asset),
    timeout=30
)
resp.raise_for_status()
print(resp.json())
```

#### Snipe-IT v8 — Novità e Funzionalità Avanzate

Snipe-IT v8 (rilasciato febbraio 2025, versione corrente 8.4.1 a maggio 2026) introduce miglioramenti significativi:

- **Custom fields su checkin/checkout**: i campi personalizzati possono ora essere compilati durante le operazioni di assegnazione/restituzione asset, non solo in fase di creazione. Esempio: al checkout di un laptop, il tecnico può compilare un campo "Condizioni display" con valori predefiniti (Perfetto/Graffi minori/Pixel morti).
- **Report custom asset avanzato**: range di ricerca estesi, valori multi-selezionabili, e filtro "giorni dall'ultimo aggiornamento" per identificare asset trascurati.
- **Upload file su fornitori**: possibilità di allegare contratti, preventivi e documentazione direttamente all'entità fornitore.
- **Report Unaccepted Items migliorato**: tracking degli asset assegnati ma non ancora accettati dall'utente destinatario.

#### Provisioning SCIM

Snipe-IT supporta **SCIM 2.0** (System for Cross-domain Identity Management) per il provisioning automatico degli utenti da identity provider:

- **Endpoint SCIM**: `https://snipeit.azienda.local/scim/v2`
- **Provider supportati**: Azure AD (Entra ID), Okta, OneLogin, JumpCloud
- **Operazioni supportate**: creazione utenti, aggiornamento attributi, disattivazione
- **Gruppi**: supporto in arrivo post-upgrade a Laravel 12

Configurazione SCIM con Azure AD (Entra ID):
1. In Snipe-IT: Admin Settings > API > generare SCIM Bearer Token
2. In Azure AD: Enterprise Applications > Snipe-IT > Provisioning
3. Tenant URL: `https://snipeit.azienda.local/scim/v2?aadOptscim062020`
4. Secret Token: il Bearer Token generato in Snipe-IT
5. Mappare attributi: `userName` → `username`, `displayName` → `name`, `emails[0].value` → `email`, `department` → `department`
6. Abilitare provisioning automatico con scope "Assigned users and groups"

#### Webhook Integration

Snipe-IT invia notifiche webhook per eventi asset:

```json
// Configurazione in Admin > Settings > Notifications > Webhooks
{
  "webhook_endpoint": "https://teams.webhook.office.com/...",
  "webhook_channel": "#it-asset-tracking",
  "webhook_botname": "Snipe-IT Bot"
}
```

Piattaforme supportate nativamente: Slack, Microsoft Teams, Google Chat. Per webhook generici (es. n8n, Make, Zapier), usare l'endpoint "General Webhook" con payload JSON standard.

Eventi che generano webhook:
- Asset checkout/checkin
- Asset creato/aggiornato/eliminato
- Licenza assegnata/revocata
- Componente consumato
- Accessorio checkout/checkin
- Utente creato/aggiornato

#### Reference Completo API Snipe-IT

L'API REST Snipe-IT (base URL: `/api/v1/`) segue le convenzioni RESTful con autenticazione Bearer Token. Specifica OpenAPI/Swagger disponibile.

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/v1/hardware` | GET | Lista tutti gli asset con paginazione |
| `/api/v1/hardware` | POST | Crea nuovo asset |
| `/api/v1/hardware/{id}` | GET | Dettaglio singolo asset |
| `/api/v1/hardware/{id}` | PUT/PATCH | Aggiorna asset |
| `/api/v1/hardware/{id}` | DELETE | Elimina asset |
| `/api/v1/hardware/{id}/checkout` | POST | Checkout asset a utente/location/asset |
| `/api/v1/hardware/{id}/checkin` | POST | Checkin asset (restituzione) |
| `/api/v1/hardware/audit` | POST | Audit asset (verifica fisica) |
| `/api/v1/hardware/byserial/{serial}` | GET | Cerca asset per serial number |
| `/api/v1/hardware/bytag/{tag}` | GET | Cerca asset per asset tag |
| `/api/v1/licenses` | GET/POST | Gestione licenze |
| `/api/v1/licenses/{id}/seats` | GET | Postazioni licenza disponibili |
| `/api/v1/users` | GET/POST | Gestione utenti |
| `/api/v1/users/{id}/assets` | GET | Asset assegnati a utente |
| `/api/v1/components` | GET/POST | Gestione componenti (RAM, SSD, ecc.) |
| `/api/v1/consumables` | GET/POST | Gestione consumabili |
| `/api/v1/accessories` | GET/POST | Gestione accessori |
| `/api/v1/locations` | GET/POST | Gestione sedi/location |
| `/api/v1/companies` | GET/POST | Gestione company (multi-tenant) |
| `/api/v1/departments` | GET/POST | Gestione dipartimenti |
| `/api/v1/categories` | GET/POST | Gestione categorie asset |
| `/api/v1/models` | GET/POST | Gestione modelli asset |
| `/api/v1/manufacturers` | GET/POST | Gestione produttori |
| `/api/v1/suppliers` | GET/POST | Gestione fornitori |
| `/api/v1/statuslabels` | GET/POST | Gestione stati asset |
| `/api/v1/fieldsets` | GET | Lista fieldset (gruppi campi custom) |
| `/api/v1/fields` | GET | Lista campi custom |
| `/api/v1/reports/activity` | GET | Report attività con filtri data |

**Paginazione API**: tutte le chiamate GET lista supportano parametri `limit` (default 50, max 1000), `offset`, `sort`, `order` (asc/desc), e `search` (ricerca testuale).

```python
"""
Esempio: export completo asset con paginazione automatica
"""
import requests
from typing import Generator

SNIPE_URL = "https://snipeit.azienda.local"
TOKEN = "BEARER_TOKEN"

def fetch_all_assets(base_url: str, token: str) -> Generator[dict, None, None]:
    """Genera tutti gli asset con paginazione automatica."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    offset = 0
    limit = 500
    while True:
        resp = requests.get(
            f"{base_url}/api/v1/hardware",
            headers=headers,
            params={"limit": limit, "offset": offset},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("rows", [])
        if not rows:
            break
        for asset in rows:
            yield asset
        offset += limit
        if offset >= data.get("total", 0):
            break

# Utilizzo
for asset in fetch_all_assets(SNIPE_URL, TOKEN):
    print(f"{asset['asset_tag']} | {asset['name']} | {asset.get('serial', 'N/A')}")
```

#### Custom Fields e Fieldset — Progettazione

I custom fields in Snipe-IT sono raggruppati in **Fieldset** (insiemi di campi) associati a **Modelli** (es. modello "Dell Latitude 5540" usa Fieldset "Laptop Standard").

Tipi di campo supportati:
- Text: testo libero
- Textarea: testo multilinea
- Checkbox: booleano sì/no
- Radio: scelta singola da lista
- List (select): dropdown singola
- List (multi-select): dropdown multipla — novità v7+
- Date: campo data
- MAC Address: validazione formato MAC automatica

**Esempio di Fieldset "Laptop Corporate"**:

| Campo | Tipo | Obbligatorio | Valori |
|-------|------|-------------|--------|
| MAC Address WiFi | MAC Address | Sì | — |
| MAC Address Ethernet | MAC Address | No | — |
| Hostname | Text | Sì | — |
| Domain Joined | Checkbox | Sì | — |
| Encryption Status | List | Sì | BitLocker Attivo / BitLocker Sospeso / Non Crittografato |
| Condizioni Display | List | No | Perfetto / Graffi minori / Pixel morti / Schermo rotto |
| Note Tecnico | Textarea | No | — |
| Data Ultimo Re-image | Date | No | — |
| Adesivo Inventario | Checkbox | Sì | — |

I campi custom sono accessibili via API con prefisso `_snipeit_` seguito dal nome-campo normalizzato e dall'ID numerico del campo (es. `_snipeit_mac_address_wifi_12`).

### ServiceNow CMDB

ServiceNow è la piattaforma ITSM enterprise di riferimento. Il modulo CMDB è considerato gold standard, integrato con Discovery, Service Mapping, Event Management, Change Management, Incident, Problem, Asset, Cost Management.

**Caratteristiche distintive**

- **CI Class Manager**: gerarchia di classi CI estensibile (~250 classi out-of-the-box, derivate da `cmdb_ci` base class)
- **CMDB Identification and Reconciliation Engine (IRE)**: gestisce CI da source multiple con regole di identification (matching) e reconciliation (precedence per attributo)
- **Discovery**: motore di scoperta agentless per server, network, applicazioni. MID Server (collector intermedio) per accesso a target dietro firewall
- **Service Mapping**: pattern-based discovery di dipendenze applicative (parte dall'entry point del servizio e mappa la catena)
- **CMDB Health Dashboard**: KPI nativi su completeness, correctness, compliance dei CI
- **CMDB Workspace** (UI moderna): visualizzazione, query, gestione CI in dashboard configurabili
- **CSDM (Common Service Data Model)**: modello standardizzato per organizzare CI in foundation, design, build, manage layers

**Pricing**

Modello per fulfiller (agent IT) con bundle annuali. Approssimativamente €100-150/agent/mese per ITSM Pro, +Discovery +Service Mapping incrementi separati. Costi totali per implementazione enterprise tipica partono da €100K/anno e salgono. Out of scope per PMI italiana.

**Quando ha senso**

- Enterprise > 1.000 dipendenti
- Necessità integrazione ITSM + ITAM + CMDB + GRC + HR Service Delivery
- Budget IT > €1M
- Presenza di IT team strutturato con ServiceNow developers/admins certificati

### Cenni: i-doit, iTop, Lansweeper, Device42, Ralph

**i-doit (Synetics)**

Open source CMDB pura (Pro version commerciale). Tedesco. Fortissima nella modellazione CI custom, relazioni, viste topologiche. Manca ticketing ITIL nativo (sebbene esista i-doit add-ons). Adatta quando si vuole una CMDB standalone integrata con un ticketing esterno (es. OTRS, Zammad, Jira). Discovery via i-doit Pro o plugin community.

**iTop (Combodo)**

Open source ITSM + CMDB francese, alternativo a GLPI. Modello ITIL più formale (CI gerarchici, relations type, impact analysis grafica nativa). Multi-tenant excellent per MSP. UI un po' rigida ma funzionale. Datamodel customizzabile via XML.

**Lansweeper**

SaaS / on-prem proprietario specializzato in network discovery e asset inventory. Discovery agentless eccezionale (SNMP, WMI, SSH, Office365, AWS, Azure, vSphere). Forte sul versante sicurezza (vulnerability scan integrato, OS support life cycle tracking). Pricing per asset, da circa €1/asset/mese. Buon fit per PMI 100-1000 asset che vuole asset+vulnerability senza implementare ITSM.

**Device42**

Asset management + CMDB + IPAM + DCIM (Data Center Infrastructure Management) + Application Dependency Mapping. Closed source. Forte su data center fisici complessi (rack, power, cooling). Discovery autonoma multi-tecnologia. Pricing enterprise.

**Ralph (NTT Data, ex-Allegro)**

Open source asset + DCIM polacco. Forte su data center hardware (rack visualization, network mapping). Adozione concentrata in Polonia/Europa centro-orientale. Modello di sviluppo meno attivo di GLPI/iTop.

---

## Configurazione e Implementazione

### Setup GLPI 10 + FusionInventory step-by-step

Scenario: PMI italiana 50 dipendenti, 1 sede, infrastruttura mista Windows/Linux. Ubuntu Server 22.04 LTS dedicato come VM (4 vCPU, 8 GB RAM, 100 GB SSD). Nome host: `glpi.azienda.local`, IP 10.0.0.50.

**Step 1 — Sistema base e LAMP**

```bash
# Aggiornamento sistema
sudo apt update && sudo apt full-upgrade -y

# Hostname e fuso orario
sudo hostnamectl set-hostname glpi.azienda.local
sudo timedatectl set-timezone Europe/Rome

# Hardening base
sudo apt install -y ufw fail2ban unattended-upgrades
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 22 proto tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Apache + PHP 8.1 + MariaDB
sudo apt install -y apache2 mariadb-server \
  php8.1 php8.1-{cli,common,curl,gd,intl,mbstring,mysql,xml,zip,bz2,ldap,imap,bcmath,xmlrpc,opcache} \
  libapache2-mod-php8.1

# PHP tuning per GLPI
sudo tee /etc/php/8.1/apache2/conf.d/99-glpi.ini <<EOF
memory_limit = 512M
file_uploads = On
max_execution_time = 600
max_input_vars = 5000
post_max_size = 100M
upload_max_filesize = 100M
session.cookie_httponly = On
session.cookie_secure = On
session.use_strict_mode = On
date.timezone = Europe/Rome
opcache.enable = 1
opcache.memory_consumption = 256
opcache.max_accelerated_files = 16229
opcache.validate_timestamps = 1
opcache.revalidate_freq = 60
EOF

sudo systemctl restart apache2
```

**Step 2 — Database**

```bash
sudo mysql_secure_installation

# Creazione database GLPI
sudo mysql -u root -p <<EOF
CREATE DATABASE glpidb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'glpiuser'@'localhost' IDENTIFIED BY 'CHANGE_THIS_STRONG_PASS';
GRANT ALL PRIVILEGES ON glpidb.* TO 'glpiuser'@'localhost';
FLUSH PRIVILEGES;
EOF

# MariaDB tuning per GLPI
sudo tee /etc/mysql/mariadb.conf.d/99-glpi.cnf <<EOF
[mysqld]
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 1
innodb_file_per_table = 1
max_allowed_packet = 64M
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
sql_mode = ""
EOF

sudo systemctl restart mariadb

# Inizializzazione timezone tables (necessario per GLPI 10)
sudo mysql_tzinfo_to_sql /usr/share/zoneinfo | sudo mysql -u root -p mysql
sudo mysql -u root -p -e "GRANT SELECT ON mysql.time_zone_name TO 'glpiuser'@'localhost'; FLUSH PRIVILEGES;"
```

**Step 3 — Download e deploy GLPI 10**

```bash
cd /tmp
wget https://github.com/glpi-project/glpi/releases/download/10.0.10/glpi-10.0.10.tgz
sudo tar -xzf glpi-10.0.10.tgz -C /var/www/

# Permessi
sudo chown -R www-data:www-data /var/www/glpi
sudo find /var/www/glpi -type d -exec chmod 750 {} \;
sudo find /var/www/glpi -type f -exec chmod 640 {} \;

# Spostamento config/data fuori da webroot per sicurezza (raccomandato GLPI 10)
sudo mkdir -p /etc/glpi /var/lib/glpi /var/log/glpi
sudo chown www-data:www-data /etc/glpi /var/lib/glpi /var/log/glpi

sudo mv /var/www/glpi/config /etc/glpi/
sudo mv /var/www/glpi/files /var/lib/glpi/

# Configurazione downstream
sudo tee /var/www/glpi/inc/downstream.php <<'EOF'
<?php
define('GLPI_CONFIG_DIR', '/etc/glpi/config');
if (file_exists(GLPI_CONFIG_DIR . '/local_define.php')) {
    require_once GLPI_CONFIG_DIR . '/local_define.php';
}
EOF

sudo tee /etc/glpi/config/local_define.php <<'EOF'
<?php
define('GLPI_VAR_DIR', '/var/lib/glpi/files');
define('GLPI_LOG_DIR', '/var/log/glpi');
EOF

sudo chown www-data:www-data /var/www/glpi/inc/downstream.php /etc/glpi/config/local_define.php
```

**Step 4 — VirtualHost Apache + Let's Encrypt**

```bash
sudo tee /etc/apache2/sites-available/glpi.conf <<'EOF'
<VirtualHost *:80>
    ServerName glpi.azienda.local
    DocumentRoot /var/www/glpi/public

    <Directory /var/www/glpi/public>
        Require all granted
        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteRule ^(.*)$ index.php [QSA,L]
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/glpi-error.log
    CustomLog ${APACHE_LOG_DIR}/glpi-access.log combined
</VirtualHost>
EOF

sudo a2dissite 000-default
sudo a2enmod rewrite ssl headers
sudo a2ensite glpi
sudo systemctl reload apache2

# Let's Encrypt (se DNS pubblico) o cert interno self-signed/CA aziendale
# Caso DNS pubblico:
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d glpi.azienda.it --redirect --hsts --staple-ocsp

# Caso interno: usare cert da CA aziendale (riferimento documento PKI)
```

**Step 5 — Setup wizard GLPI**

Navigare a `https://glpi.azienda.it/install/install.php` e seguire procedura:

1. Lingua: italiano
2. Accettazione licenza GPL
3. Step "Installazione" (non upgrade)
4. Test environment: deve essere tutto verde (timezone, php extensions, db privileges)
5. Connessione DB: localhost / glpiuser / password / glpidb
6. Crea schema database
7. Account default creati (glpi/glpi super-admin, tech/tech, normal/normal, post-only/postonly)

**SUBITO DOPO L'INSTALLAZIONE**: cambiare password di tutti gli account default ed eliminare quelli non necessari (almeno tech/normal/post-only). Eliminare directory install:

```bash
sudo rm -rf /var/www/glpi/install
```

**Step 6 — Configurazione base**

In GLPI come super-admin:

- Setup > Generale: nome organizzazione, lingua default, fuso orario
- Setup > Notifiche: attivare invio email, configurare SMTP (smtp.azienda.local:587, account dedicato)
- Setup > Autenticazione > LDAP directories: aggiungere AD aziendale
  - Server: dc01.azienda.local:389 (o ldaps:636)
  - BaseDN: `DC=azienda,DC=local`
  - User: `CN=glpi-svc,OU=ServiceAccounts,DC=azienda,DC=local` (account dedicato read-only)
  - Filtro: `(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))`
  - Sync schedule: ogni 4 ore
- Amministrazione > Profili: definire profilo "IT Tech", "User", "Manager", "ReadOnly"
- Setup > Mailbox collector: support@azienda.it via IMAPS, polling ogni 5 min, ticket auto-create

**Step 7 — Plugin FusionInventory**

```bash
cd /var/www/glpi/plugins
sudo wget https://github.com/fusioninventory/fusioninventory-for-glpi/releases/download/glpi10.0.6%2B1.1/fusioninventory-10.0.6+1.1.tar.bz2
sudo tar -xjf fusioninventory-10.0.6+1.1.tar.bz2
sudo chown -R www-data:www-data fusioninventory/
sudo rm fusioninventory-10.0.6+1.1.tar.bz2
```

In GLPI: Setup > Plugins > FusionInventory > Installa > Attiva.

Configurazione:
- Plugin > FusionInventory > Generale: token URL, frequenze
- Plugin > FusionInventory > Discovery: range IP da scoprire, credenziali SNMP/SSH/WMI
- Plugin > FusionInventory > Network discovery: target → Switch core, periodicità 7 giorni

**Step 8 — Deploy agent FusionInventory**

Su Windows Server (via GPO MSI):

Download MSI: https://github.com/fusioninventory/fusioninventory-agent/releases (versione 2.6.x)

Comando installazione silenziosa:
```cmd
msiexec /i fusioninventory-agent_windows-x64_2.6.1.msi /quiet ^
  ADD_FIREWALL_EXCEPTION=1 ^
  EXECMODE=Service ^
  RUNNOW=1 ^
  SERVER=https://glpi.azienda.it/plugins/fusioninventory/
```

Pacchetto in GPO Software Installation per deploy massivo su tutti i computer del dominio.

Su Linux (via Ansible):

```yaml
# fusion-inventory-agent.yml
---
- name: Deploy FusionInventory Agent
  hosts: linux_servers
  become: yes
  tasks:
    - name: Install agent (Debian/Ubuntu)
      apt:
        name: fusioninventory-agent
        state: present
        update_cache: yes
      when: ansible_os_family == "Debian"

    - name: Install agent (RHEL family)
      dnf:
        name: fusioninventory-agent
        state: present
      when: ansible_os_family == "RedHat"

    - name: Configure server URL
      lineinfile:
        path: /etc/fusioninventory/agent.cfg
        regexp: '^server\s*='
        line: 'server = https://glpi.azienda.it/plugins/fusioninventory/'
      notify: restart fusion-agent

    - name: Configure tag (per sito/ruolo)
      lineinfile:
        path: /etc/fusioninventory/agent.cfg
        regexp: '^tag\s*='
        line: 'tag = MILANO-DC1-PROD'

    - name: Enable and start service
      systemd:
        name: fusioninventory-agent
        enabled: yes
        state: started

  handlers:
    - name: restart fusion-agent
      systemd:
        name: fusioninventory-agent
        state: restarted
```

```bash
ansible-playbook -i inventory.yml fusion-inventory-agent.yml
```

Su Mac: agent OSX disponibile come .pkg, deploy via JAMF/Munki.

Su switch/router/printer: configurazione SNMP v2c o v3 sull'apparato, GLPI lancia discovery scheduled che popola network equipment.

### Modellazione esempi (server, VM, app, service)

**Esempio 1 — Server fisico Dell PowerEdge**

CI Type: Computer (subtype Server)
Attributi chiave:
- Nome: SRV-ESX-PROD-01
- Serial number: ABCD1234
- Manufacturer: Dell, Modello: PowerEdge R740
- OS: VMware ESXi 8.0U2
- Location: Milano DC1, Rack R12, U-position 14-15
- Status: In produzione
- Owner technical: IT Infrastructure Team
- Criticità: Alta

Relazioni:
- has → 2x CPU Intel Xeon Gold 6248R
- has → 384 GB RAM (12x 32GB DIMM)
- has → 8x SSD Enterprise 1.92TB
- has → 4x Network Adapter 25GbE
- connected to → Switch SW-CORE-01 port 12
- managed by → iDRAC https://idrac-srv-esx-prod-01.azienda.local
- contract → MaintContract Dell-2024-005 (ProSupport Plus 5y NBD)

**Esempio 2 — VM ospitata**

CI Type: Computer (subtype VirtualMachine)
- Nome: vm-app-orders-prod-01
- vCPU: 8, vRAM: 32GB, vDisk: 200GB thin
- OS: Ubuntu Server 22.04 LTS
- Hostname: app-orders-prod-01.azienda.local
- IP: 10.0.20.15

Relazioni:
- runs on → Hypervisor SRV-ESX-PROD-01 (relazione "hosted on")
- member of → vSphere Cluster ESX-PROD
- depends on → VLAN 20 (App Tier)
- monitored by → Zabbix host vm-app-orders-prod-01

**Esempio 3 — Applicazione**

CI Type: Software (subtype Application) [via plugin GenericObject]
- Nome: OrderMgmt
- Versione: 3.4.2
- Vendor: AcmeSoft S.r.l.
- License: 50 named users, scadenza 2026-12-31

Relazioni:
- installed on → vm-app-orders-prod-01
- depends on → DB Instance ORDERS_PROD
- exposes → URL https://orders.azienda.it
- documented → Procedure Operative Section 4.2
- supported by → Vendor AcmeSoft (UnderpinningContract UC-2024-007)

**Esempio 4 — Database instance**

CI Type: Custom "Database Instance"
- Nome: ORDERS_PROD
- Engine: PostgreSQL 14.10
- Listener: 0.0.0.0:5432
- Size: 45 GB
- Backup policy: daily full + WAL archiving (RPO 5min)

Relazioni:
- hosted on → vm-db-orders-prod-01
- backed up by → Veeam Job ORDERS_DAILY
- accessed by → Application OrderMgmt (read/write)
- accessed by → Application Reporting (read-only)

**Esempio 5 — Servizio business**

CI Type: Custom "BusinessService"
- Nome: Gestione Ordini
- Description: Servizio core per inserimento/gestione ordini commerciali
- Owner business: Direttore Commerciale
- Owner technical: IT Manager
- Criticality: Critical (Tier 1)
- SLA: 99.5% uptime business hours, P1 resolution 2h
- Users: ~25 in dipartimento Vendite

Relazioni:
- depends on → Application OrderMgmt (primary)
- depends on → Service Email (secondary, per notifiche)
- depends on → Service NAS Storage (secondary, per allegati)
- documented → KB Article KB-ORD-001
- monitored by → Zabbix Service "Gestione Ordini" (composite check)

### Automazione popolamento via REST API Python

GLPI espone REST API a `https://glpi.azienda.it/apirest.php`. Token API si genera in Setup > Generale > API.

```python
"""
glpi_sync.py — Sincronizzazione asset da fonte esterna a GLPI CMDB
"""
import requests
import json
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

GLPI_URL = "https://glpi.azienda.it/apirest.php"
USER_TOKEN = "USER_TOKEN_FROM_GLPI_USER_PROFILE"
APP_TOKEN = "APP_TOKEN_FROM_GLPI_GENERAL_SETUP"

class GLPIClient:
    def __init__(self, url: str, app_token: str, user_token: str):
        self.url = url
        self.app_token = app_token
        self.user_token = user_token
        self.session_token: Optional[str] = None

    def __enter__(self):
        resp = requests.get(
            f"{self.url}/initSession",
            headers={
                "Authorization": f"user_token {self.user_token}",
                "App-Token": self.app_token
            },
            timeout=10
        )
        resp.raise_for_status()
        self.session_token = resp.json()["session_token"]
        log.info("GLPI session established")
        return self

    def __exit__(self, *args):
        if self.session_token:
            requests.get(
                f"{self.url}/killSession",
                headers=self._headers(),
                timeout=10
            )
            log.info("GLPI session closed")

    def _headers(self) -> dict:
        return {
            "Session-Token": self.session_token,
            "App-Token": self.app_token,
            "Content-Type": "application/json"
        }

    def find_computer_by_serial(self, serial: str) -> Optional[int]:
        params = {
            "criteria[0][field]": "5",  # field 5 = serialnumber
            "criteria[0][searchtype]": "equals",
            "criteria[0][value]": serial,
            "forcedisplay[0]": "2"      # field 2 = name
        }
        resp = requests.get(
            f"{self.url}/search/Computer",
            headers=self._headers(),
            params=params,
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("totalcount", 0) > 0:
            return data["data"][0]["2"]  # ID retrievable
        return None

    def create_computer(self, payload: dict) -> int:
        resp = requests.post(
            f"{self.url}/Computer",
            headers=self._headers(),
            data=json.dumps({"input": payload}),
            timeout=30
        )
        resp.raise_for_status()
        new_id = resp.json()["id"]
        log.info(f"Created Computer ID {new_id}: {payload.get('name')}")
        return new_id

    def update_computer(self, ci_id: int, payload: dict) -> None:
        payload["id"] = ci_id
        resp = requests.put(
            f"{self.url}/Computer/{ci_id}",
            headers=self._headers(),
            data=json.dumps({"input": payload}),
            timeout=30
        )
        resp.raise_for_status()
        log.info(f"Updated Computer ID {ci_id}")

# ESEMPIO: sync da inventory cloud (es. csv export da AWS Config)
external_asset = {
    "name": "i-0abcd1234ef567890",
    "serial": "i-0abcd1234ef567890",
    "comment": "EC2 instance us-west-2",
    "computertypes_id": 4,    # ID corrispondente a "Cloud VM" (custom)
    "operatingsystems_id": 12, # ID Ubuntu 22.04
    "states_id": 1,            # In produzione
    "locations_id": 5,         # AWS us-west-2
}

with GLPIClient(GLPI_URL, APP_TOKEN, USER_TOKEN) as glpi:
    existing_id = glpi.find_computer_by_serial(external_asset["serial"])
    if existing_id:
        glpi.update_computer(existing_id, external_asset)
    else:
        glpi.create_computer(external_asset)
```

Pattern simile per Snipe-IT (vedi sezione precedente). ServiceNow espone Table API REST simile.

### Mantenimento qualità dati

Una CMDB senza qualità dati è peggio di nessuna CMDB: induce decisioni sbagliate. Quattro pratiche essenziali.

**1. Data ownership**

Per ogni classe CI, designare un owner. Esempi:
- Network device → Network Engineer
- Server fisici → System Administrator
- VM → Virtualization team
- Cloud resources → DevOps
- Workstation utenti → Service Desk
- Software & licenses → IT Procurement / Asset Manager

L'owner è responsabile della qualità dati per i CI della sua classe. Reportistica trimestrale di qualità lo coinvolge.

**2. Certificazione CI ogni 90 giorni**

Per CI critici (servizi, server produzione), workflow di certificazione: ogni 90 giorni l'owner riceve task di "verifica e certifica" con elenco CI sotto sua responsabilità. Modifica eventuali drift, conferma. Storicizzato.

In GLPI: implementabile via plugin Workflow + scheduled task che genera tickets di review.

**3. Dashboard data quality**

Metriche da monitorare:
- **Coverage %**: # CI registrati / # CI esistenti (stimato). Target > 90% per categorie critiche.
- **Accuracy %**: # CI con dati validati / # CI registrati. Misurato via spot-check periodici.
- **Completeness %**: # CI con tutti gli attributi obbligatori popolati / # CI totali. Target 100% per attributi critici.
- **Freshness**: % CI con last-modified < 90 giorni. Target > 80%.
- **Orphan CI**: CI senza relazioni (sospetti di obsolescenza).
- **Discovery drift**: differenza tra ciò che discovery scopre e ciò che è in CMDB. Trigger investigation.

Esempio query SQL su GLPI per trovare CI stantii:

```sql
SELECT id, name, date_mod
FROM glpi_computers
WHERE is_deleted = 0
  AND states_id = 1  -- In produzione
  AND date_mod < DATE_SUB(NOW(), INTERVAL 180 DAY)
ORDER BY date_mod ASC;
```

**4. Alerting su drift**

Quando discovery rileva un asset non presente in CMDB → ticket automatico al sistemista per investigazione. Quando un CI in CMDB non viene visto da discovery per N giorni → alert (potrebbe essere dismesso, oppure problema di accesso).

```python
# pseudo-code per drift detection
discovery_set = set(discovery.fetch_active_hosts())
cmdb_set = set(cmdb.fetch_in_production_hosts())

# In discovery ma non in CMDB → nuovo asset non registrato
unregistered = discovery_set - cmdb_set
for host in unregistered:
    open_ticket(category="ITAM", summary=f"Host {host} discovered but not in CMDB")

# In CMDB ma non in discovery → potenziale CI obsoleto
missing = cmdb_set - discovery_set
for host in missing:
    if cmdb.last_seen(host) < days_ago(7):
        continue  # ancora recente
    open_ticket(category="ITAM", summary=f"Host {host} in CMDB but not discovered for >7d")
```

---

## Integrazione GLPI + Snipe-IT — Architettura Complementare

In molte organizzazioni la scelta non è GLPI **oppure** Snipe-IT, ma GLPI **insieme a** Snipe-IT, ciascuno nel ruolo in cui eccelle. L'architettura complementare prevede:

- **GLPI**: ITSM (ticketing, change, problem, knowledge base), CMDB (CI con relazioni e servizi), discovery (GLPI Agent), contratti, licenze software, SLA monitoring.
- **Snipe-IT**: asset management puro (hardware lifecycle, costi, ammortamento, garanzia, checkout/checkin, audit fisico, QR code label, report finanziari).

Questa separazione riflette la distinzione ITIL tra **Service Configuration Management** (GLPI) e **IT Asset Management** (Snipe-IT).

### Pattern di Sincronizzazione

La sincronizzazione bidirezionale è l'approccio più robusto: Snipe-IT è authoritative per dati finanziari (costo, fornitore, garanzia, ammortamento), GLPI è authoritative per dati operativi (stato CI, relazioni, servizi, ticket associati).

```python
"""
sync_snipeit_to_glpi.py — Sincronizzazione asset Snipe-IT → GLPI
Eseguire come cron job giornaliero: 0 2 * * * /usr/bin/python3 /opt/scripts/sync_snipeit_to_glpi.py
"""
import requests
import json
import logging
from dataclasses import dataclass
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/var/log/cmdb-sync/sync.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

@dataclass(frozen=True)
class SyncConfig:
    snipe_url: str
    snipe_token: str
    glpi_url: str
    glpi_app_token: str
    glpi_user_token: str

def fetch_snipeit_assets(config: SyncConfig) -> list[dict]:
    """Recupera tutti gli asset attivi da Snipe-IT."""
    headers = {
        "Authorization": f"Bearer {config.snipe_token}",
        "Accept": "application/json"
    }
    assets = []
    offset = 0
    while True:
        resp = requests.get(
            f"{config.snipe_url}/api/v1/hardware",
            headers=headers,
            params={"limit": 500, "offset": offset, "status": "Deployed"},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("rows", [])
        if not rows:
            break
        assets.extend(rows)
        offset += 500
        if offset >= data.get("total", 0):
            break
    log.info(f"Recuperati {len(assets)} asset da Snipe-IT")
    return assets

def map_snipeit_to_glpi(snipe_asset: dict) -> dict:
    """Mappa campi Snipe-IT a campi GLPI Computer."""
    return {
        "name": snipe_asset.get("name", ""),
        "serial": snipe_asset.get("serial", ""),
        "comment": f"Sync Snipe-IT ID:{snipe_asset['id']} | "
                   f"Tag:{snipe_asset.get('asset_tag', '')} | "
                   f"Cost:{snipe_asset.get('purchase_cost', 'N/A')}",
        "contact": snipe_asset.get("assigned_to", {}).get("name", "") if snipe_asset.get("assigned_to") else "",
        "states_id": 1,  # In produzione — mappare secondo propria configurazione
    }

def sync_to_glpi(config: SyncConfig, assets: list[dict]) -> dict:
    """Sincronizza asset verso GLPI via REST API."""
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Init session GLPI
    session_resp = requests.get(
        f"{config.glpi_url}/initSession",
        headers={
            "Authorization": f"user_token {config.glpi_user_token}",
            "App-Token": config.glpi_app_token
        },
        timeout=10
    )
    session_resp.raise_for_status()
    session_token = session_resp.json()["session_token"]

    headers = {
        "Session-Token": session_token,
        "App-Token": config.glpi_app_token,
        "Content-Type": "application/json"
    }

    for asset in assets:
        try:
            glpi_payload = map_snipeit_to_glpi(asset)
            serial = glpi_payload.get("serial", "")
            if not serial:
                stats["skipped"] += 1
                continue

            # Cerca CI esistente per serial
            search_resp = requests.get(
                f"{config.glpi_url}/search/Computer",
                headers=headers,
                params={
                    "criteria[0][field]": "5",
                    "criteria[0][searchtype]": "equals",
                    "criteria[0][value]": serial
                },
                timeout=15
            )
            search_resp.raise_for_status()
            existing = search_resp.json()

            if existing.get("totalcount", 0) > 0:
                ci_id = existing["data"][0]["2"]
                requests.put(
                    f"{config.glpi_url}/Computer/{ci_id}",
                    headers=headers,
                    data=json.dumps({"input": {**glpi_payload, "id": ci_id}}),
                    timeout=30
                ).raise_for_status()
                stats["updated"] += 1
            else:
                requests.post(
                    f"{config.glpi_url}/Computer",
                    headers=headers,
                    data=json.dumps({"input": glpi_payload}),
                    timeout=30
                ).raise_for_status()
                stats["created"] += 1
        except Exception as e:
            log.error(f"Errore sync asset {asset.get('asset_tag')}: {e}")
            stats["errors"] += 1

    # Kill session
    requests.get(f"{config.glpi_url}/killSession", headers=headers, timeout=10)
    return stats
```

### Alternativa No-Code: Shuffle SOAR

Per organizzazioni senza sviluppatori Python, **Shuffle** (piattaforma SOAR open source) offre connettori pre-built per GLPI e Snipe-IT. Il workflow visuale permette di:

1. Trigger: webhook da Snipe-IT su evento "asset creato"
2. Azione: fetch dettagli asset da Snipe-IT API
3. Trasformazione: mapping campi
4. Azione: crea/aggiorna Computer in GLPI API
5. Notifica: messaggio Slack/Teams con risultato

Configurazione in Shuffle:
- Autenticare entrambe le app (GLPI con App Token + User Token, Snipe-IT con Bearer Token)
- Creare workflow con nodi drag-and-drop
- Testare con singolo asset, poi attivare su tutti gli eventi

### Matrice Decisionale

| Scenario | Strumento consigliato |
|----------|----------------------|
| PMI < 50 dip., solo inventario HW | Snipe-IT standalone |
| PMI 50-200 dip., serve ticketing + inventario | GLPI standalone |
| PMI 50-200 dip., ITSM separato (Freshdesk/Jira) | Snipe-IT per asset + ITSM esterno |
| Organizzazione 200-1000 dip., serve CMDB + ITSM + ITAM completo | GLPI (ITSM+CMDB) + Snipe-IT (ITAM) sincronizzati |
| Enterprise > 1000 dip., budget disponibile | ServiceNow o iTop enterprise |
| MSP multi-tenant | GLPI con multi-entity o iTop |
| Solo compliance licenze software | Snipe-IT standalone |

---

## GLPI Agent — Guida Approfondita

Il GLPI Agent è il successore ufficiale di FusionInventory Agent. Scritto in Perl, distribuito per tutte le piattaforme maggiori, è il componente che esegue la raccolta dati sui dispositivi target e la invia al server GLPI.

### Architettura del GLPI Agent

```
┌─────────────────────────────────────────────────────┐
│                    GLPI Server                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │  Native      │ │   CMDB       │ │   ITSM       │ │
│  │  Inventory   │ │  (Relations) │ │  (Tickets)   │ │
│  │  Server      │ │              │ │              │ │
│  └──────┬───────┘ └──────────────┘ └──────────────┘ │
│         │ HTTPS POST (XML/JSON)                      │
└─────────┼───────────────────────────────────────────┘
          │
    ┌─────┴─────┐
    │ GLPI Agent│
    │ (Perl)    │
    ├───────────┤
    │ Tasks:    │
    │ • Inventory (local HW/SW collection)             │
    │ • NetDiscovery (IP range scan: ARP, ICMP,        │
    │   NetBIOS, SNMP)                                  │
    │ • NetInventory (SNMP deep poll per device)       │
    │ • Deploy (software distribution)                  │
    │ • Collect (files, registry, WMI queries)          │
    │ • ESX (VMware ESXi remote inventory via SOAP)    │
    └───────────┘
```

### Installazione per Piattaforma

**Windows — MSI (deploy via GPO/SCCM/Intune)**

```cmd
REM Download da https://github.com/glpi-project/glpi-agent/releases
REM Versione 1.16 — MSI x64

msiexec /i glpi-agent-1.16-x64.msi /quiet /norestart ^
  SERVER=https://glpi.azienda.it ^
  TAG=SEDE-MILANO ^
  EXECMODE=Service ^
  RUNNOW=1 ^
  DEBUG=0 ^
  NO_SSL_CHECK=0 ^
  ADD_FIREWALL_EXCEPTION=1 ^
  DELAYTIME=3600 ^
  TIMEOUT=180
```

Parametri MSI chiave:
- `SERVER`: URL del server GLPI (senza path aggiuntivo — l'agent sa dove inviare)
- `TAG`: etichetta per classificare il dispositivo in GLPI (sede, ruolo, ambiente)
- `EXECMODE`: `Service` (daemon), `Task` (scheduled task Windows), `Manual`
- `DELAYTIME`: intervallo tra inventari in secondi (default 3600 = 1 ora)
- `NO_SSL_CHECK`: `0` in produzione (validare sempre il certificato TLS)

**Linux — Package Manager**

```bash
# Debian/Ubuntu — repository ufficiale
curl -fsSL https://raw.githubusercontent.com/glpi-project/glpi-agent/main/contrib/unix/glpi-agent.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/glpi-agent.gpg

echo "deb [signed-by=/usr/share/keyrings/glpi-agent.gpg] https://glpi-project.github.io/glpi-agent/debian stable main" \
  | sudo tee /etc/apt/sources.list.d/glpi-agent.list

sudo apt update && sudo apt install -y glpi-agent

# Configurazione
sudo tee /etc/glpi-agent/agent.cfg <<'EOF'
server = https://glpi.azienda.it
tag = DATACENTER-PROD
delaytime = 3600
no-ssl-check = 0
timeout = 180
# Tasks abilitati
tasks = inventory,netdiscovery,netinventory,collect
EOF

sudo systemctl enable --now glpi-agent

# RHEL/Rocky/Alma
sudo dnf install -y https://github.com/glpi-project/glpi-agent/releases/download/1.16/glpi-agent-1.16-1.noarch.rpm
# Stessa configurazione in /etc/glpi-agent/agent.cfg
```

**macOS — PKG**

```bash
# Download .pkg da GitHub releases
# Installazione:
sudo installer -pkg glpi-agent-1.16.pkg -target /
# Configurazione:
sudo nano /etc/glpi-agent/agent.cfg
# server = https://glpi.azienda.it
# tag = MAC-UTENTI
sudo launchctl load /Library/LaunchDaemons/com.glpi-project.agent.plist
```

### Network Discovery — Configurazione Dettagliata

Il task NetDiscovery scansiona range IP per scoprire dispositivi in rete. Protocolli utilizzati in sequenza:

1. **ARP table locale**: l'agent consulta la propria tabella ARP
2. **ICMP Echo (ping)**: identifica host attivi
3. **NetBIOS**: nome NetBIOS per host Windows
4. **SNMP**: interrogazione OID di sistema per identificazione modello/vendor

Configurazione dei range IP nel GLPI Agent Toolbox:

```yaml
# /etc/glpi-agent/netdiscovery.yaml (esempio)
# Nota: la configurazione può avvenire anche via interfaccia Toolbox web
jobs:
  - name: "Sede Milano - Rete Server"
    ranges:
      - start: "10.0.10.1"
        end: "10.0.10.254"
    credentials:
      - community: "SNMP_COMMUNITY_RO"
        version: "2c"
    schedule: "weekly"

  - name: "Sede Milano - Rete Client"
    ranges:
      - start: "10.0.20.1"
        end: "10.0.20.254"
      - start: "10.0.21.1"
        end: "10.0.21.254"
    credentials:
      - community: "SNMP_COMMUNITY_RO"
        version: "2c"
    schedule: "daily"

  - name: "Sede Milano - Network Equipment"
    ranges:
      - start: "10.0.0.1"
        end: "10.0.0.50"
    credentials:
      - version: "3"
        username: "glpi-snmpv3"
        auth_protocol: "SHA256"
        auth_passphrase: "AUTH_PASS_HERE"
        priv_protocol: "AES256"
        priv_passphrase: "PRIV_PASS_HERE"
        security_level: "authPriv"
    schedule: "daily"
```

### SNMPv3 — Configurazione Sicura

SNMPv3 è raccomandato per ambienti production perché introduce autenticazione e cifratura, a differenza di SNMPv2c che trasmette la community string in chiaro.

Configurazione lato switch/router (esempio Cisco IOS):

```
! Configurazione SNMPv3 su switch Cisco
snmp-server group GLPI-GROUP v3 priv
snmp-server user glpi-snmpv3 GLPI-GROUP v3 auth sha256 AUTH_PASS_HERE priv aes 256 PRIV_PASS_HERE
snmp-server host 10.0.0.50 version 3 priv glpi-snmpv3

! ACL per limitare accesso SNMP al solo server GLPI
ip access-list standard SNMP-ACL
 permit host 10.0.0.50
 deny any log
snmp-server community GLPI-RO RO SNMP-ACL
```

### MibSupport — Dispositivi Personalizzati

Il GLPI Agent include un sistema di moduli MibSupport che permette di riconoscere e inventariare dispositivi specifici attraverso i loro `sysObjectID` SNMP. Quando l'agent scopre un dispositivo con un OID specifico (es. Synology NAS, Ubiquiti UniFi, dispositivi IEC 61850), il modulo MibSupport corrispondente viene attivato per estrarre attributi specifici del vendor.

Moduli MibSupport inclusi (v1.16):
- **LinuxAppliance**: Synology, Ubiquiti, QNAP, NAS generici Linux
- **Cisco**: switch, router, AP Catalyst/Meraki
- **HP/Aruba**: switch ProCurve, AP Aruba
- **Fortinet**: FortiGate, FortiSwitch
- **APC/Schneider**: UPS, PDU
- **IEC61850**: dispositivi industriali conformi allo standard IEC 61850

### Collect — Query WMI Custom

Il task Collect permette di raccogliere informazioni specifiche non coperte dall'inventario standard. Esempio pratico: verificare lo stato BitLocker su tutti i laptop Windows.

Configurazione in GLPI (Amministrazione > GLPI Inventory > Collect):

```json
{
  "name": "BitLocker Status",
  "type": "wmi",
  "query": "SELECT DriveLetter, ProtectionStatus, EncryptionMethod FROM Win32_EncryptableVolume WHERE DriveLetter='C:'",
  "namespace": "root\\CIMV2\\Security\\MicrosoftVolumeEncryption"
}
```

Altro esempio: stato servizio Windows Defender:

```json
{
  "name": "Defender Service Status",
  "type": "wmi",
  "query": "SELECT Name, State, StartMode FROM Win32_Service WHERE Name='WinDefend'",
  "namespace": "root\\CIMV2"
}
```

I risultati delle collect appaiono nel CI in GLPI sotto la tab "Collect", consultabili per audit e compliance.

---

## Confronto Dettagliato Strumenti CMDB / ITAM

La tabella seguente confronta le principali soluzioni su dimensioni operative rilevanti per una scelta informata.

| Dimensione | GLPI 11 | Snipe-IT v8 | iTop | i-doit Pro | ServiceNow | Lansweeper |
|------------|---------|-------------|------|------------|------------|------------|
| **Licenza** | GPL v3 (gratuito) | AGPL v3 (gratuito) | AGPL v3 (Community) / Commerciale | GPL (Open) / Commerciale (Pro) | Commerciale SaaS | Commerciale SaaS/On-Prem |
| **ITSM Ticketing** | Sì (nativo, ITIL-aligned) | No | Sì (ITIL formale) | No (richiede integrazione) | Sì (gold standard ITIL) | No |
| **CMDB con relazioni** | Sì (nativo + plugin CMDB) | No (solo asset flat) | Sì (eccellente, impact analysis nativa) | Sì (eccellente, modello relazioni profondo) | Sì (best-in-class, CSDM) | Limitato (relazioni base) |
| **Asset Management** | Sì (discreto) | Sì (eccellente, focus principale) | Sì (buono) | Sì (buono) | Sì (completo) | Sì (buono) |
| **Discovery nativa** | Sì (GLPI Agent) | No (script esterni) | No (import/API) | Sì (i-doit Pro) | Sì (MID Server) | Sì (eccellente, agentless) |
| **REST API** | Sì (completa) | Sì (eccellente, Swagger) | Sì (completa) | Sì (completa) | Sì (Table API, eccellente) | Sì |
| **Multi-tenant** | Sì (multi-entity) | Sì (multi-company) | Sì (eccellente) | Sì (mandanti) | Sì (domain separation) | Limitato |
| **Scalabilità** | ~500K asset | ~100K asset | ~200K asset | ~500K CI | Milioni CI | ~500K asset |
| **Skill richieste** | PHP/MySQL, admin medio | Laravel/PHP, admin base | PHP/MySQL, admin esperto | PHP/MySQL, admin esperto | JavaScript/ServiceNow dev | Admin base |
| **Costo indicativo** | €0 + infra self-hosted | €0 + infra self-hosted | €0 (Community) / ~€50K/anno (Enterprise) | €0 (Open) / ~€5K-30K/anno (Pro) | ~€100-500K+/anno | ~€1-3/asset/mese |
| **Ideale per** | PMI EU, PA, MSP | PMI, focus ITAM | MSP, organizzazioni ITIL-mature | Aziende DACH, CMDB-centric | Enterprise globali | PMI-Enterprise, focus discovery |

### Criteri di Selezione Approfonditi

**Quando scegliere GLPI**:
- Budget zero per licenze software
- Necessità di ITSM + ITAM in un unico strumento
- Organizzazione in Italia/Francia/Spagna (community forte, localizzazione completa)
- Pubblica Amministrazione italiana (conformità linee guida AgID)
- MSP che gestisce più clienti (multi-entity)

**Quando scegliere Snipe-IT**:
- Focus esclusivo su asset management senza ITSM
- Team IT piccolo che vuole setup rapido
- Necessità di audit fisico asset con QR code
- Compliance licenze software come priorità
- UX moderna come requisito (onboarding utenti non-IT)

**Quando scegliere iTop**:
- Modello ITIL formale richiesto (certificazione, audit)
- MSP che necessita multi-tenant avanzato
- Impact analysis grafica nativa come requisito
- Datamodel altamente personalizzabile (via XML)

**Quando scegliere ServiceNow**:
- Enterprise > 1000 dipendenti con budget adeguato
- Necessità di ITSM + ITOM + ITAM + HR + GRC integrati
- Team dedicato di ServiceNow developers/admins
- Service Mapping automatica come requisito

---

## Compliance e Governance

### CMDB e ISO/IEC 27001

Lo standard ISO/IEC 27001:2022 include due controlli direttamente rilevanti per la CMDB:

**Annex A 5.9 — Inventario delle risorse informative e degli altri asset associati**

Requisito: l'organizzazione deve identificare gli asset relativi alle informazioni e mantenere un inventario completo e aggiornato. Per ogni asset deve essere designato un proprietario (owner).

Mapping CMDB/ITAM:
- L'inventario GLPI/Snipe-IT soddisfa il requisito di censimento asset
- Il campo "Owner" su ogni CI/asset documenta la proprietà
- L'audit trail (storico modifiche) dimostra l'aggiornamento continuo
- I report di completezza (% campi obbligatori popolati) dimostrano la qualità

**Annex A 8.9 — Configuration Management**

Requisito: le configurazioni di hardware, software, servizi e reti devono essere stabilite, documentate, implementate, monitorate e riesaminate. Questo include configurazioni di sicurezza, hardening baseline, impostazioni di rete.

Mapping CMDB:
- Il CI in GLPI con attributi OS, versione, patch level, stato hardening
- Le relazioni CI→Servizio documentano le dipendenze operative
- Il processo di certificazione CI ogni 90 giorni soddisfa il "riesame periodico"
- Le regole di discovery drift (asset in rete non in CMDB) supportano il monitoraggio continuo

### CMDB e GDPR

Il Regolamento (UE) 2016/679 (GDPR) non prescrive una CMDB, ma la CMDB supporta la compliance in modo significativo:

- **Art. 30 — Registro delle attività di trattamento**: la mappatura servizi → applicazioni → database → server nella CMDB documenta dove risiedono i dati personali. Esempio: il servizio "Gestione Clienti" dipende dall'applicazione CRM che usa il database CUSTOMERS_PROD ospitato su vm-db-crm-01 → questo trail documenta il "dove" del trattamento.
- **Art. 32 — Sicurezza del trattamento**: l'inventario degli asset che trattano dati personali, con classificazione di criticità e stato hardening, supporta le misure tecniche adeguate.
- **Art. 33/34 — Notifica violazioni**: in caso di data breach, la CMDB con service mapping permette di determinare rapidamente quali dati personali sono potenzialmente coinvolti (impact analysis: "se il server X è compromesso, quali database contiene? quali applicazioni usano quei database? quali trattamenti di dati personali coinvolgono quelle applicazioni?").

### NIS2 e Gestione Asset

La Direttiva NIS2 (Direttiva UE 2022/2555), con scadenza di recepimento ottobre 2024, richiede alle entità essenziali e importanti una gestione rigorosa degli asset ICT:

- **Inventario completo**: ogni asset ICT deve essere censito, classificato e assegnato a un responsabile
- **Gestione configurazioni**: baseline di sicurezza definite e monitorate
- **Incident response**: capacità di determinare rapidamente l'impatto di un incidente → richiede service mapping CMDB
- **Supply chain**: tracciamento dei fornitori e dei contratti → modellabile come CI "Vendor Contract" in CMDB

La combinazione GLPI (CMDB + ITSM) + Snipe-IT (ITAM) genera la documentazione necessaria per dimostrare compliance NIS2 agli auditor.

### Linee Guida AgID per la PA Italiana

L'Agenzia per l'Italia Digitale (AgID) ha pubblicato linee guida sull'inventario delle risorse digitali della PA (2022), richiedendo:

- Censimento completo di tutti gli asset ICT (hardware, software, servizi cloud)
- Classificazione per criticità e livello di esposizione
- Proprietario (dirigente responsabile) per ogni asset
- Aggiornamento periodico con cadenza almeno semestrale
- Tracciabilità delle modifiche (audit trail)

GLPI con localizzazione italiana è adottato da numerosi enti PA (comuni, ASL, scuole, regioni) proprio per la conformità a questi requisiti e il costo zero di licenza.

### Generazione Evidenze Audit

Procedura per generare report di compliance da GLPI:

```sql
-- Report ISO 27001 Annex A 5.9: Inventario completo asset con owner
SELECT
    c.name AS "Nome Asset",
    ct.name AS "Tipo",
    s.name AS "Stato",
    CONCAT(u.firstname, ' ', u.realname) AS "Owner",
    c.serial AS "Serial Number",
    l.name AS "Location",
    c.date_creation AS "Data Creazione",
    c.date_mod AS "Ultima Modifica"
FROM glpi_computers c
LEFT JOIN glpi_computertypes ct ON c.computertypes_id = ct.id
LEFT JOIN glpi_states s ON c.states_id = s.id
LEFT JOIN glpi_users u ON c.users_id_tech = u.id
LEFT JOIN glpi_locations l ON c.locations_id = l.id
WHERE c.is_deleted = 0
ORDER BY ct.name, c.name;
```

```sql
-- Report NIS2: Asset critici senza owner designato
SELECT c.name, ct.name AS tipo, s.name AS stato
FROM glpi_computers c
LEFT JOIN glpi_computertypes ct ON c.computertypes_id = ct.id
LEFT JOIN glpi_states s ON c.states_id = s.id
WHERE c.is_deleted = 0
  AND c.states_id = 1  -- In produzione
  AND (c.users_id_tech = 0 OR c.users_id_tech IS NULL)
ORDER BY c.name;
```

Per Snipe-IT, i report sono generabili sia da interfaccia web (Reports > Custom Asset Report con export CSV/PDF) sia via API:

```bash
# Export tutti gli asset deployed con dettagli finanziari (per audit ITAM)
curl -s -H "Authorization: Bearer $SNIPE_TOKEN" \
     -H "Accept: application/json" \
     "https://snipeit.azienda.local/api/v1/hardware?status=Deployed&limit=1000" \
  | python3 -m json.tool > audit_asset_$(date +%Y%m%d).json
```

---

## Automazione Avanzata

### Pattern REST API Avanzati

**Operazioni bulk GLPI**

L'API GLPI supporta operazioni batch: creazione/aggiornamento multiplo in una singola chiamata, riducendo il numero di round-trip HTTP.

```python
"""
Creazione batch di Computer in GLPI (fino a 100 per chiamata)
"""
def bulk_create_computers(glpi_client, computers: list[dict]) -> list[int]:
    """Crea multipli Computer in una singola POST."""
    payload = {"input": computers}  # lista di dict, non singolo dict
    resp = requests.post(
        f"{glpi_client.url}/Computer",
        headers=glpi_client._headers(),
        data=json.dumps(payload),
        timeout=60
    )
    resp.raise_for_status()
    # Risposta: lista di {"id": X, "message": "..."} per ogni CI creato
    results = resp.json()
    return [r["id"] for r in results if "id" in r]

# Esempio: import da CSV
import csv
batch = []
with open("asset_import.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        batch.append({
            "name": row["hostname"],
            "serial": row["serial"],
            "computertypes_id": int(row["type_id"]),
            "states_id": 1,
            "locations_id": int(row["location_id"])
        })
        if len(batch) >= 100:
            bulk_create_computers(glpi, batch)
            batch = []
    if batch:
        bulk_create_computers(glpi, batch)
```

**Gestione paginazione robusta Snipe-IT**

```python
"""
Wrapper paginazione con retry e rate limiting per Snipe-IT API
"""
import time
from functools import wraps

def retry_on_429(max_retries: int = 3):
    """Decorator per gestire HTTP 429 Too Many Requests."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                resp = func(*args, **kwargs)
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", 5))
                    log.warning(f"Rate limited, attendo {wait}s (tentativo {attempt + 1})")
                    time.sleep(wait)
                    continue
                return resp
            raise Exception(f"Rate limit persistente dopo {max_retries} tentativi")
        return wrapper
    return decorator

@retry_on_429(max_retries=5)
def api_get(url: str, headers: dict, params: dict) -> requests.Response:
    return requests.get(url, headers=headers, params=params, timeout=30)
```

### Ansible Dynamic Inventory da GLPI

Ansible può usare GLPI come source di inventario dinamico, eliminando la necessità di mantenere file `inventory.yml` statici.

```python
#!/usr/bin/env python3
"""
glpi_inventory.py — Ansible dynamic inventory plugin per GLPI
Utilizzo: ansible-playbook -i glpi_inventory.py playbook.yml
"""
import json
import os
import sys
import requests

GLPI_URL = os.environ.get("GLPI_URL", "https://glpi.azienda.it/apirest.php")
APP_TOKEN = os.environ["GLPI_APP_TOKEN"]
USER_TOKEN = os.environ["GLPI_USER_TOKEN"]

def get_session():
    resp = requests.get(
        f"{GLPI_URL}/initSession",
        headers={"Authorization": f"user_token {USER_TOKEN}", "App-Token": APP_TOKEN},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()["session_token"]

def get_computers(session_token: str) -> list[dict]:
    headers = {"Session-Token": session_token, "App-Token": APP_TOKEN}
    computers = []
    offset = 0
    while True:
        resp = requests.get(
            f"{GLPI_URL}/Computer",
            headers=headers,
            params={
                "range": f"{offset}-{offset + 99}",
                "expand_dropdowns": "true"
            },
            timeout=15
        )
        if resp.status_code == 206 or resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                computers.extend(data)
                offset += 100
                if len(data) < 100:
                    break
            else:
                break
        else:
            break
    return computers

def build_inventory(computers: list[dict]) -> dict:
    inventory = {"_meta": {"hostvars": {}}, "all": {"children": []}}
    groups = {}

    for c in computers:
        hostname = c.get("name", "")
        if not hostname or c.get("states_id_name", "") == "Ritirato":
            continue

        # Raggruppa per location
        location = c.get("locations_id_name", "unknown").replace(" ", "_").lower()
        if location not in groups:
            groups[location] = {"hosts": []}
            inventory["all"]["children"].append(location)
        groups[location]["hosts"].append(hostname)

        # Raggruppa per OS
        os_name = c.get("operatingsystems_id_name", "unknown").replace(" ", "_").lower()
        os_group = f"os_{os_name}"
        if os_group not in groups:
            groups[os_group] = {"hosts": []}
            inventory["all"]["children"].append(os_group)
        groups[os_group]["hosts"].append(hostname)

        # Host vars
        inventory["_meta"]["hostvars"][hostname] = {
            "glpi_id": c.get("id"),
            "glpi_serial": c.get("serial", ""),
            "glpi_type": c.get("computertypes_id_name", ""),
            "glpi_os": c.get("operatingsystems_id_name", ""),
            "glpi_location": c.get("locations_id_name", ""),
        }

    inventory.update(groups)
    return inventory

if __name__ == "__main__":
    if "--list" in sys.argv:
        session = get_session()
        computers = get_computers(session)
        inv = build_inventory(computers)
        print(json.dumps(inv, indent=2))
    elif "--host" in sys.argv:
        print(json.dumps({}))
    else:
        print(json.dumps({"_meta": {"hostvars": {}}}))
```

### Integrazione Monitoring → CMDB → Ticketing

Il flusso Zabbix → GLPI permette di creare ticket automatici con CI corretto pre-popolato quando un alert di monitoring scatta.

```python
"""
zabbix_glpi_webhook.py — Webhook Zabbix che crea ticket GLPI con CI correlato
Deploy come Flask/FastAPI endpoint chiamato da Zabbix Media Type webhook.
"""
from fastapi import FastAPI, Request
import requests
import json

app = FastAPI()

GLPI_URL = "https://glpi.azienda.it/apirest.php"
GLPI_APP_TOKEN = "APP_TOKEN"
GLPI_USER_TOKEN = "USER_TOKEN"

@app.post("/zabbix-webhook")
async def handle_zabbix_alert(request: Request):
    payload = await request.json()
    hostname = payload.get("host", "")
    trigger = payload.get("trigger", "")
    severity = payload.get("severity", "")
    message = payload.get("message", "")

    # 1. Init GLPI session
    session = requests.get(
        f"{GLPI_URL}/initSession",
        headers={
            "Authorization": f"user_token {GLPI_USER_TOKEN}",
            "App-Token": GLPI_APP_TOKEN
        },
        timeout=10
    ).json()["session_token"]

    headers = {
        "Session-Token": session,
        "App-Token": GLPI_APP_TOKEN,
        "Content-Type": "application/json"
    }

    # 2. Cercare CI in GLPI per hostname
    search = requests.get(
        f"{GLPI_URL}/search/Computer",
        headers=headers,
        params={
            "criteria[0][field]": "1",
            "criteria[0][searchtype]": "equals",
            "criteria[0][value]": hostname
        },
        timeout=15
    ).json()

    computer_id = None
    if search.get("totalcount", 0) > 0:
        computer_id = search["data"][0].get("2")

    # 3. Mappare severity Zabbix a urgency/priority GLPI
    severity_map = {
        "Disaster": {"urgency": 5, "priority": 6},
        "High": {"urgency": 4, "priority": 5},
        "Average": {"urgency": 3, "priority": 4},
        "Warning": {"urgency": 2, "priority": 3},
        "Information": {"urgency": 1, "priority": 2},
    }
    urgency = severity_map.get(severity, {}).get("urgency", 3)
    priority = severity_map.get(severity, {}).get("priority", 3)

    # 4. Creare ticket
    ticket_payload = {
        "input": {
            "name": f"[Zabbix] {trigger} su {hostname}",
            "content": f"Alert Zabbix:\n\nHost: {hostname}\n"
                       f"Trigger: {trigger}\nSeverity: {severity}\n\n{message}",
            "urgency": urgency,
            "priority": priority,
            "type": 1,  # Incident
            "itilcategories_id": 8,  # Monitoring (configurare ID)
            "status": 2,  # Assegnato
        }
    }

    ticket_resp = requests.post(
        f"{GLPI_URL}/Ticket",
        headers=headers,
        data=json.dumps(ticket_payload),
        timeout=30
    )
    ticket_resp.raise_for_status()
    ticket_id = ticket_resp.json()["id"]

    # 5. Associare CI al ticket (se trovato)
    if computer_id:
        requests.post(
            f"{GLPI_URL}/Ticket/{ticket_id}/Item_Ticket",
            headers=headers,
            data=json.dumps({
                "input": {
                    "tickets_id": ticket_id,
                    "itemtype": "Computer",
                    "items_id": computer_id
                }
            }),
            timeout=15
        )

    # Cleanup session
    requests.get(f"{GLPI_URL}/killSession", headers=headers, timeout=10)

    return {"status": "ok", "ticket_id": ticket_id, "ci_linked": computer_id is not None}
```

### CI/CD Pipeline → CMDB Update

Quando un deploy in produzione avviene via CI/CD, la pipeline può aggiornare automaticamente la CMDB con la nuova versione dell'applicazione.

```yaml
# .gitlab-ci.yml — stage per aggiornamento CMDB post-deploy
update_cmdb:
  stage: post-deploy
  image: python:3.12-slim
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  script:
    - pip install requests
    - |
      python3 -c "
      import requests, json, os
      GLPI_URL = os.environ['GLPI_API_URL']
      headers = {
          'Authorization': f\"user_token {os.environ['GLPI_USER_TOKEN']}\",
          'App-Token': os.environ['GLPI_APP_TOKEN']
      }
      # Init session
      s = requests.get(f'{GLPI_URL}/initSession', headers=headers, timeout=10).json()
      h = {'Session-Token': s['session_token'], 'App-Token': os.environ['GLPI_APP_TOKEN'], 'Content-Type': 'application/json'}
      # Update software version CI
      software_id = int(os.environ['GLPI_SOFTWARE_CI_ID'])
      requests.put(
          f'{GLPI_URL}/Software/{software_id}',
          headers=h,
          data=json.dumps({'input': {
              'id': software_id,
              'comment': f\"Deploy {os.environ['CI_COMMIT_SHORT_SHA']} - {os.environ['CI_COMMIT_TITLE']}\"
          }}),
          timeout=30
      ).raise_for_status()
      requests.get(f'{GLPI_URL}/killSession', headers=h, timeout=10)
      print(f'CMDB aggiornata: Software ID {software_id}')
      "
  variables:
    GLPI_API_URL: "https://glpi.azienda.it/apirest.php"
```

---

## Gestione del Ciclo di Vita CI

### Stadi del Ciclo di Vita

Il ciclo di vita di un Configuration Item segue stadi ben definiti, ciascuno con implicazioni operative e finanziarie diverse.

| Stadio | Descrizione | Azioni CMDB | Stato GLPI | Stato Snipe-IT |
|--------|-------------|-------------|-----------|----------------|
| **Ideazione** | Richiesta di nuovo asset/servizio, approvazione budget | CI non ancora creato, eventuale ticket RFC | — | — |
| **Procurement** | Ordine emesso, attesa consegna | CI creato con stato "Ordinato", dati fornitore e costo | Ordinato | Pending |
| **Ricevimento** | Asset ricevuto fisicamente, verifica conformità | Aggiornamento serial, modello, data ricezione | In magazzino | — |
| **Staging** | Configurazione, hardening, test pre-deploy | Aggiornamento OS, hostname, configurazione, test | In fase di test | — |
| **Deploy** | Messa in produzione, assegnazione a servizio/utente | Relazioni CI→Servizio, ownership, classificazione | In produzione | Deployed |
| **Operativo** | Funzionamento normale, manutenzione ordinaria | Aggiornamenti periodici (patch, versioni), certificazione 90gg | In produzione | Deployed |
| **Manutenzione** | Guasto, riparazione, upgrade | Stato temporaneo, ticket associato | In riparazione | Out for Repair |
| **Fine vita pianificata** | Scadenza garanzia, obsolescenza, refresh cycle | Alert automatico 90gg prima di fine garanzia | In produzione (alert) | Deployed (alert) |
| **Decommissioning** | Rimozione dal servizio, migrazione workload | Rimozione relazioni CI→Servizio, cambio stato | Ritirato | Archived |
| **Dismissione** | Cancellazione dati, smaltimento RAEE, ricondizionamento | CI archiviato (non eliminato, per audit trail) | Ritirato/Eliminato | Archived |

### Automazione Decommissioning

Il decommissioning è il punto dove CMDB e Asset Management convergono: il CI operativo va ritirato dal servizio (CMDB) e l'asset finanziario va dismissato (ITAM).

Workflow automatizzato in GLPI:

1. **Trigger**: chiusura di un Change Request di tipo "Decommissioning" con stato "Implemented"
2. **Regola automatica** (Setup > Rules > Rules for assigning items): quando un ticket/change con categoria "Decommissioning" viene chiuso con successo, aggiornare il CI associato:
   - Stato → "Ritirato"
   - Rimuovere relazioni CI→Servizio (le relazioni restano nello storico)
   - Aggiungere nota: "Decommissionato via Change #XXXX il YYYY-MM-DD"
3. **Sync verso Snipe-IT**: script cron che cerca CI appena ritirati in GLPI e aggiorna lo stato in Snipe-IT via API
4. **Notifica**: email al responsabile ITAM per procedura di dismissione fisica (cancellazione dati, RAEE)

```python
"""
decommission_sync.py — Sincronizza stato "Ritirato" da GLPI a Snipe-IT
Cron: 0 6 * * * /usr/bin/python3 /opt/scripts/decommission_sync.py
"""
import requests
import json
from datetime import datetime, timedelta

GLPI_URL = "https://glpi.azienda.it/apirest.php"
SNIPE_URL = "https://snipeit.azienda.local/api/v1"

# Trova CI ritirati nelle ultime 24h in GLPI
def find_recently_retired_glpi(session_headers: dict) -> list[str]:
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    resp = requests.get(
        f"{GLPI_URL}/search/Computer",
        headers=session_headers,
        params={
            "criteria[0][field]": "31",  # stato
            "criteria[0][searchtype]": "equals",
            "criteria[0][value]": "6",   # ID stato "Ritirato"
            "criteria[1][link]": "AND",
            "criteria[1][field]": "19",  # data modifica
            "criteria[1][searchtype]": "morethan",
            "criteria[1][value]": yesterday,
            "forcedisplay[0]": "5",  # serial
        },
        timeout=15
    )
    resp.raise_for_status()
    data = resp.json()
    return [item["5"] for item in data.get("data", []) if item.get("5")]

# Aggiorna stato in Snipe-IT
def archive_in_snipeit(serials: list[str], snipe_token: str):
    headers = {
        "Authorization": f"Bearer {snipe_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    archived_status_id = 3  # Configurare l'ID dello stato "Archived"
    for serial in serials:
        # Cerca asset per serial
        resp = requests.get(
            f"{SNIPE_URL}/hardware/byserial/{serial}",
            headers=headers,
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            rows = data.get("rows", [])
            for asset in rows:
                requests.patch(
                    f"{SNIPE_URL}/hardware/{asset['id']}",
                    headers=headers,
                    data=json.dumps({"status_id": archived_status_id}),
                    timeout=15
                )
```

---

## Best Practices

**1. Iniziare dai servizi business, non dagli asset**
Top-down è più focalizzato. Mappare 5 servizi critici end-to-end produce più valore che inventariare 500 asset senza relazioni.

**2. Federare, non duplicare**
Se un dato vive authoritative in AD, non duplicarlo in CMDB. Linkare. Se vive in vCenter, idem.

**3. Discovery automatica obbligatoria oltre i 100 CI**
Manuale non scala. FusionInventory (gratis con GLPI) o equivalente vendor.

**4. Owner per classe CI**
Senza ownership la CMDB diventa terra di nessuno e marcisce.

**5. Certificazione periodica come processo formale**
Ogni 90gg per CI critici. Senza re-certificazione, dopo 12 mesi i dati sono inutilizzabili.

**6. Attributi minimi, non massimi**
Resistere alla tentazione di tracciare 47 attributi per ogni CI. Solo quelli usati operativamente. Gli altri vivono nel sistema authoritative o nella documentazione.

**7. Backup CMDB stesso**
La CMDB è un asset critico. Backup database GLPI/ServiceNow/Snipe-IT con stessa retention dei sistemi production.

**8. Audit trail completo**
Chi ha modificato cosa, quando. Tutti i tool seri lo offrono nativamente (GLPI: Historical, Snipe-IT: Activity log, ServiceNow: Audit history).

**9. Integrazione bidirezionale con Incident/Change**
CI impattato auto-popolato in incident; change correlato a CI per impact analysis. Senza questa integrazione la CMDB resta esercizio teorico.

**10. Visualizzazione delle relazioni**
La forza del CMDB sta nelle relazioni. Una topology view è 10x più utile di una tabella. GLPI ha "Topology" (limitata), ServiceNow "Dependency Views" (eccellente), iTop "Impact Analysis" (buona). Privilegiare tool che hanno questa funzionalità.

---

## Troubleshooting

**Problema: la CMDB cresce ma nessuno la usa per analisi di impatto**

Cause: CI non collegati a servizi business; relazioni mancanti; integrazione assente con incident/change. Rimedio: forzare top-down service mapping per i 10 servizi più critici; integrare CMDB nel workflow ticketing (campo CI obbligatorio per ticket > P3).

**Problema: agent FusionInventory non si connette al server GLPI**

Cause comuni:
- Firewall blocca outbound HTTPS dal client al server
- URL server non raggiungibile da client (DNS, routing)
- Plugin FusionInventory disattivato in GLPI
- Certificato SSL non valido sul server (self-signed senza CA installata sul client)

Verifica:
```bash
# Sul client Linux
sudo fusioninventory-agent --debug --server=https://glpi.azienda.it/plugins/fusioninventory/ --no-task=deploy

# Verifica connettività
curl -v https://glpi.azienda.it/plugins/fusioninventory/

# Log
sudo tail -f /var/log/fusioninventory/agent.log
```

**Problema: discovery SNMP non vede gli switch**

Cause: SNMP community sbagliata, ACL su switch che blocca il GLPI server, versione SNMP incompatibile.

Verifica da CLI server:
```bash
sudo apt install -y snmp
snmpwalk -v2c -c PUBLIC_COMMUNITY 10.0.0.1 system
```

Su switch Cisco, verificare ACL `snmp-server community` con permit per IP GLPI.

**Problema: duplicati CI dopo re-discovery**

Cause: matching incorretto (es. usa hostname invece di serial), MAC address cambiato, hostname rinominato.

Rimedio in GLPI: configurare entity rules per matching corretto (Configuration > Rules > Rules for assigning items to entities). In ServiceNow IRE: rivedere identification rules.

**Problema: GLPI lento con > 200K ticket**

Cause: indice DB mancanti, opcache PHP disattivato, query non ottimizzate.

Rimedio:
```bash
# Verifica opcache
php -i | grep opcache

# Tuning MariaDB innodb_buffer_pool_size > dimensione DB (se RAM permette)
# Indici aggiuntivi: GLPI ha tool "GLPI Database Optimization" Marketplace
```

**Problema: i dati Asset (costo, fornitore) sono incompleti perché i tecnici non li compilano**

Cause: i tecnici non hanno accesso ai dati finance, e non vedono il valore di compilarli.

Rimedio: integrazione automatica con sistema procurement/ERP. Quando arriva una fattura, importazione automatica asset con dati finanziari. I tecnici aggiungono solo dati operativi.

**Problema: CMDB ServiceNow ha "CI duplicati" segnalati dal CMDB Health Dashboard**

Cause: identification rules non configurate per certe classi; più discovery sources che generano lo stesso CI con identifier diversi.

Rimedio: revisione CMDB Identification Rules per ogni classe CI; configurazione Reconciliation Rules per scegliere data source authoritative; uso del CI Class Manager per merge manuale dei duplicati storici.

**Problema: drift tra CMDB e realtà — VM dismessa ma ancora "In produzione" in CMDB**

Cause: processo di decommissioning non aggiorna CMDB; manca trigger automatico.

Rimedio: integrare workflow decommissioning con auto-update CMDB (script che cambia stato CI a "Ritirato" alla chiusura del Change di decommissioning); quartely review dei CI senza activity per > 90gg; alerting drift discovery vs CMDB.

---

## Riferimenti

- AXELOS, "ITIL 4 Foundation: ITIL 4 Edition", 2019. Capitolo Service Configuration Management.
- AXELOS, "ITIL 4 Specialist: Create, Deliver and Support", 2020. Sezioni Service Configuration Management e IT Asset Management.
- ISO/IEC 19770-1:2017, "Information technology — IT asset management — Part 1: IT asset management systems — Requirements".
- ISO/IEC 19770-2:2015, "Software identification tag" (SWID tags per asset SW).
- ServiceNow CSDM (Common Service Data Model) Whitepaper: https://www.servicenow.com/community/csdm-articles/
- ServiceNow CMDB Documentation: https://docs.servicenow.com/bundle/washingtondc-servicenow-platform/page/product/configuration-management/concept/c_ITILConfigurationManagement.html
- GLPI Documentation: https://glpi-project.org/documentation/
- GLPI Plugin Catalog (GenericObject, FusionInventory, FormCreator): https://plugins.glpi-project.org/
- FusionInventory Documentation: http://fusioninventory.org/documentation/
- Snipe-IT Documentation: https://snipe-it.readme.io/
- Snipe-IT GitHub: https://github.com/snipe/snipe-it
- i-doit Documentation: https://docs.i-doit.com/
- iTop Documentation: https://www.itophub.io/wiki/page
- Lansweeper Documentation: https://docs.lansweeper.com/
- Device42 Documentation: https://docs.device42.com/
- Ralph CMDB GitHub: https://github.com/allegro/ralph
- AgID — Linee guida sull'inventario delle risorse digitali della PA italiana (2022).
- ENISA — Asset management for ICT systems and networks, 2020.

---

## Esercizi
1. **Lab — GLPI deploy + import.** Setup GLPI Docker; import 50 asset via CSV.
2. **Stretch — auto-discovery.** Setup GLPI agent + discovery passive su rete.

## Auto-valutazione
1. CMDB vs Asset DB.
2. Orphan CI: come rilevare?
3. Reconciliation: tecniche?

## Glossario locale
| Termine | Definizione |
|---|---|
| **CMDB** | Configuration Management Database. |
| **CI** | Configuration Item. |
| **Auto-discovery** | Scoperta automatica asset. |
| **Reconciliation** | Allineamento sources. |
| **Orphan CI** | CI senza relazioni. |
