# Manutenzione IT — Panoramica e Piano di Studio

## Indice

1. [Panoramica del Campo](#panoramica-del-campo)
   - [Che Cos'è la Manutenzione IT](#che-cosè-la-manutenzione-it)
   - [Tipologie di Manutenzione](#tipologie-di-manutenzione)
   - [Perché la Manutenzione IT è Fondamentale](#perché-la-manutenzione-it-è-fondamentale)
   - [Relazione con ITIL e i Framework ITSM](#relazione-con-itil-e-i-framework-itsm)
   - [Destinatari di Questo Percorso](#destinatari-di-questo-percorso)
2. [Piano di Studio](#piano-di-studio)
   - [Fase 1: Framework e Metodologie (settimane 1-2)](#fase-1-framework-e-metodologie-settimane-1-2)
   - [Fase 2: Manutenzione Operativa (settimane 3-6)](#fase-2-manutenzione-operativa-settimane-3-6)
   - [Fase 3: Sicurezza e Continuità (settimane 7-9)](#fase-3-sicurezza-e-continuità-settimane-7-9)
   - [Fase 4: Governance e Miglioramento (settimane 10-12)](#fase-4-governance-e-miglioramento-settimane-10-12)
3. [Ambiente di Laboratorio](#ambiente-di-laboratorio)
   - [Configurazione Raccomandata del Laboratorio](#configurazione-raccomandata-del-laboratorio)
   - [Strumenti Necessari](#strumenti-necessari)
   - [Configurazione VM per Simulazione di Guasti](#configurazione-vm-per-simulazione-di-guasti)
4. [Glossario](#glossario)
5. [Certificazioni Rilevanti](#certificazioni-rilevanti)
6. [Risorse Consigliate](#risorse-consigliate)

---

## Panoramica del Campo

### Che Cos'è la Manutenzione IT

La manutenzione IT comprende l'insieme di tutte le attività, processi e procedure volte a garantire che l'infrastruttura tecnologica di un'organizzazione funzioni in modo affidabile, sicuro ed efficiente nel tempo. Non si tratta semplicemente di "riparare ciò che si rompe": è una disciplina strutturata che abbraccia la pianificazione strategica, l'esecuzione operativa quotidiana, il monitoraggio proattivo e il miglioramento continuo.

In un'organizzazione moderna, l'infrastruttura IT è il tessuto connettivo che sostiene ogni processo di business. Server, reti, applicazioni, database, sistemi di sicurezza, piattaforme cloud — tutti questi componenti richiedono attenzione costante per continuare a operare ai livelli richiesti. La manutenzione IT è la disciplina che rende possibile questa continuità.

Il campo della manutenzione IT si estende attraverso molteplici domini tecnici: dalla gestione dei sistemi operativi server (Windows Server, Linux) alla manutenzione dell'infrastruttura di rete; dalla gestione dello storage e dei backup alla sicurezza operativa; dal monitoraggio delle prestazioni alla gestione degli asset e del loro ciclo di vita. Ogni dominio ha le proprie specificità, ma tutti condividono principi metodologici comuni che derivano dai framework internazionali di IT Service Management.

### Tipologie di Manutenzione

La manutenzione IT si articola in tre macrocategorie fondamentali, ciascuna con un ruolo distinto ma complementare.

**Manutenzione preventiva.** È l'insieme delle attività pianificate e programmate eseguite a intervalli regolari per prevenire guasti e degradazione delle prestazioni. Include operazioni come l'applicazione regolare di patch e aggiornamenti di sicurezza, la verifica periodica dello stato dei backup, il controllo dello spazio disco e delle risorse computazionali, la rotazione dei log, il rinnovo dei certificati SSL/TLS, la revisione delle policy di sicurezza e la pulizia programmata dei componenti hardware. La manutenzione preventiva opera secondo calendari prestabiliti — giornalieri, settimanali, mensili, trimestrali, semestrali e annuali — e rappresenta la prima linea di difesa contro i downtime non pianificati. Il suo obiettivo è ridurre al minimo la probabilità che si verifichino guasti, mantenendo i sistemi in condizioni operative ottimali.

**Manutenzione correttiva.** Interviene dopo che un guasto o un malfunzionamento si è già verificato. Il suo obiettivo è ripristinare il servizio nel minor tempo possibile, minimizzando l'impatto sulle operazioni di business. La manutenzione correttiva include la diagnosi del problema (troubleshooting), l'applicazione della soluzione (fix), la verifica del ripristino e la documentazione dell'intervento. Un processo maturo di manutenzione correttiva si integra strettamente con i processi ITIL di Incident Management e Problem Management: il primo garantisce il ripristino rapido del servizio, il secondo indaga le cause radice per prevenire ricorrenze.

**Manutenzione predittiva.** Rappresenta l'evoluzione più avanzata della disciplina. Utilizza dati storici, metriche in tempo reale, analisi dei trend e, sempre più frequentemente, algoritmi di machine learning per anticipare i guasti prima che si verifichino. Indicatori come l'analisi SMART dei dischi, i trend di utilizzo della CPU e della memoria, i pattern di errore nei log di sistema, le curve di degradazione delle prestazioni e i dati di telemetria dell'hardware vengono correlati per identificare componenti o sistemi a rischio di guasto imminente. La manutenzione predittiva consente di intervenire in modo mirato e tempestivo, trasformando potenziali incidenti critici in attività di manutenzione pianificata.

A queste tre categorie si aggiungono due approcci complementari: la **manutenzione adattiva**, che riguarda le modifiche necessarie per adeguare i sistemi a nuovi requisiti normativi, tecnologici o di business; e la **manutenzione perfettiva**, orientata all'ottimizzazione delle prestazioni e all'implementazione di miglioramenti anche in assenza di guasti o requisiti espliciti.

### Perché la Manutenzione IT è Fondamentale

La manutenzione IT non è un costo da minimizzare, ma un investimento strategico che produce valore misurabile su quattro assi fondamentali.

**Uptime e disponibilità dei servizi.** L'obiettivo primario della manutenzione è garantire che i servizi IT siano disponibili quando gli utenti e i processi di business ne hanno bisogno. Un piano di manutenzione strutturato è ciò che separa un'organizzazione con il 99,9% di availability (circa 8,76 ore di downtime all'anno) da una con il 99% (87,6 ore di downtime). La differenza, misurata in termini economici, può raggiungere centinaia di migliaia di euro per le organizzazioni di medie dimensioni e milioni per le grandi imprese. Ogni ora di downtime non pianificato ha un costo diretto (perdita di produttività, mancati ricavi) e un costo indiretto (danno reputazionale, perdita di fiducia dei clienti).

**Sicurezza informatica.** La manutenzione è il primo livello di difesa contro le minacce informatiche. L'applicazione tempestiva delle patch di sicurezza, l'aggiornamento delle firme antivirus e delle regole del firewall, la revisione periodica degli accessi e dei privilegi, il monitoraggio dei log di sicurezza — tutte queste attività manutentive sono essenziali per mantenere una postura di sicurezza adeguata. Un sistema non manutenuto è un sistema vulnerabile: le vulnerabilità zero-day ricevono attenzione mediatica, ma la maggior parte degli attacchi informatici sfrutta vulnerabilità note per le quali esistono patch disponibili da settimane o mesi. La manutenzione regolare chiude queste finestre di esposizione.

**Conformità normativa.** Normative come il GDPR, la direttiva NIS2, lo standard PCI DSS, le certificazioni ISO 27001 e ISO 20000 richiedono tutte che le organizzazioni dimostrino di avere processi strutturati di manutenzione e gestione dei sistemi IT. La capacità di produrre evidenze di manutenzione regolare — log delle patch applicate, report dei backup verificati, risultati dei test di disaster recovery, registri degli accessi revisionati — è essenziale per superare audit di conformità e mantenere le certificazioni.

**Ottimizzazione dei costi.** Una manutenzione preventiva strutturata è significativamente meno costosa della manutenzione correttiva d'emergenza. Prevenire un guasto costa una frazione rispetto alla gestione di un incidente critico fuori orario lavorativo, con i relativi costi di straordinario, di consulenti esterni chiamati in urgenza e di perdita di business. Inoltre, la manutenzione predittiva consente di pianificare la sostituzione dell'hardware al momento ottimale — non troppo presto (spreco di investimento residuo) né troppo tardi (rischio di guasto).

### Relazione con ITIL e i Framework ITSM

La manutenzione IT non opera in un vuoto metodologico. Si inserisce nel contesto più ampio dell'IT Service Management (ITSM), di cui ITIL (Information Technology Infrastructure Library) rappresenta il framework di riferimento più diffuso a livello globale.

ITIL v4, nella sua versione più recente, definisce un Service Value System (SVS) che descrive come tutti i componenti e le attività di un'organizzazione IT lavorano insieme per creare valore. La manutenzione IT si colloca al cuore di questo sistema, intersecando numerose practice ITIL.

La **practice di Incident Management** definisce come gestire e risolvere gli interruzioni non pianificate dei servizi — il cuore della manutenzione correttiva. La **practice di Problem Management** guida l'indagine delle cause radice dei guasti ricorrenti, trasformando la conoscenza acquisita durante la manutenzione correttiva in azioni preventive. La **practice di Change Management** (ora denominata Change Enablement in ITIL v4) fornisce il framework per gestire in modo controllato tutte le modifiche all'infrastruttura — essenziale per le attività di manutenzione che comportano cambiamenti ai sistemi in produzione.

La **practice di Service Level Management** definisce gli SLA che stabiliscono le aspettative di disponibilità e prestazioni — gli obiettivi a cui la manutenzione deve tendere. La **practice di IT Asset Management** gestisce il ciclo di vita degli asset che sono oggetto della manutenzione. La **practice di Monitoring and Event Management** fornisce la visibilità in tempo reale sullo stato dell'infrastruttura, alimentando sia la manutenzione correttiva (rilevamento di guasti) sia quella predittiva (rilevamento di trend anomali).

Oltre a ITIL, altri framework contribuiscono alla strutturazione della manutenzione IT: **COBIT** per gli aspetti di governance, **ISO/IEC 20000** come standard certificabile per l'ITSM, **NIST** per le linee guida sulla sicurezza informatica, e il modello **SRE** (Site Reliability Engineering) di Google per un approccio ingegneristico all'affidabilità dei servizi.

### Destinatari di Questo Percorso

Questo materiale di studio è stato progettato per due profili professionali specifici, sebbene sia utile per chiunque operi nell'ambito della gestione dei sistemi IT.

**IT Systems Manager (Responsabile Sistemi IT).** Il professionista responsabile della gestione quotidiana dell'infrastruttura tecnologica aziendale. Coordina il team tecnico, pianifica le attività di manutenzione, gestisce i rapporti con i fornitori, definisce e monitora gli SLA, e garantisce che i servizi IT soddisfino le esigenze del business. Per questo profilo, il percorso di studio fornisce il framework metodologico per strutturare e ottimizzare le attività di manutenzione, template e procedure operative immediatamente utilizzabili, e le competenze per comunicare efficacemente con il management sull'importanza e il valore della manutenzione IT.

**Cybersecurity Team Chief (Responsabile Sicurezza Informatica).** Il professionista responsabile della postura di sicurezza dell'organizzazione. Deve integrare le attività di sicurezza con la manutenzione operativa dei sistemi, garantendo che patch di sicurezza, hardening, monitoraggio delle minacce e risposta agli incidenti siano parte integrante del ciclo di manutenzione. Per questo profilo, il percorso di studio offre la comprensione di come la manutenzione operativa e la sicurezza si intersecano, le procedure per integrare la sicurezza nei processi di change management e incident management, e le competenze per condurre assessment di sicurezza come parte delle attività di manutenzione periodica.

Si raccomanda un'esperienza pregressa di almeno 3-5 anni in ambito IT operations, system administration o cybersecurity, insieme a una conoscenza di base dei sistemi operativi server, del networking e dei concetti fondamentali di sicurezza informatica.

---

## Piano di Studio

Il percorso è strutturato in quattro fasi da completare in circa 12 settimane, con un impegno stimato di 6-10 ore settimanali. Ogni fase costruisce sulle precedenti, creando una progressione dalla teoria metodologica alla pratica operativa, fino alla governance e al miglioramento continuo.

### Fase 1: Framework e Metodologie (settimane 1-2)

**Obiettivo:** Acquisire le fondamenta teoriche e metodologiche su cui si basa l'intera disciplina della manutenzione IT. Comprendere i framework ITIL e ITSM, i processi di gestione dei cambiamenti, degli incidenti e dei problemi, e gli standard di documentazione.

**Settimana 1 — ITIL, Change Management e Problem Management**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `01-FRAMEWORK-METODOLOGIE/itil-fondamenti-per-manutenzione.md` | Service Value System, guiding principles, service lifecycle, practice fondamentali di ITIL v4 | 4-5 |
| `01-FRAMEWORK-METODOLOGIE/gestione-cambiamenti-change-management.md` | Tipologie di change (standard, normal, emergency), CAB, RFC, risk assessment, rollback planning | 3-4 |
| `01-FRAMEWORK-METODOLOGIE/gestione-problemi-problem-management.md` | Differenza tra incident e problem, Root Cause Analysis (5 Whys, Ishikawa, Fault Tree Analysis), KEDB | 3-4 |

Attività pratica della settimana: mappare i processi ITIL attualmente in uso nella propria organizzazione, identificare le lacune rispetto al framework e creare un template RFC personalizzato.

**Settimana 2 — Incident Management, SLA, CMDB, CSI e Documentazione**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `01-FRAMEWORK-METODOLOGIE/gestione-incidenti-incident-management.md` | Lifecycle dell'incidente, severity level, SLA per livello, escalation, major incident, metriche (MTTD, MTTA, MTTR) | 3-4 |
| `01-FRAMEWORK-METODOLOGIE/gestione-livelli-servizio-sla.md` | SLA, OLA, Underpinning Contract, calcolo availability, monitoring, service catalog | 2-3 |
| `01-FRAMEWORK-METODOLOGIE/gestione-configurazione-cmdb.md` | Configuration Item, relazioni, discovery automatico, data quality, integrazione con altri processi | 2-3 |
| `01-FRAMEWORK-METODOLOGIE/miglioramento-continuo-csi.md` | Ciclo PDCA, 7-step improvement process, maturity assessment, improvement register | 2-3 |
| `01-FRAMEWORK-METODOLOGIE/documentazione-standard-e-procedure.md` | SOP, runbook, knowledge article, naming conventions, Documentation-as-Code | 2-3 |

Attività pratica della settimana: rivedere gli SLA esistenti, valutare lo stato del CMDB e definire le matrici di escalation per il team.

**Milestone Fase 1:** Al termine delle prime due settimane, il professionista deve essere in grado di descrivere il Service Value System di ITIL v4, gestire il processo completo di change management, condurre una Root Cause Analysis strutturata, definire SLA realistici e misurabili, e valutare la maturità dei processi ITSM della propria organizzazione.

### Fase 2: Manutenzione Operativa (settimane 3-6)

**Obiettivo:** Passare dalla teoria alla pratica operativa. Implementare checklist, calendari e procedure per la manutenzione preventiva; acquisire competenze specifiche su sistemi operativi, servizi infrastrutturali e gestione degli asset.

**Settimana 3 — Manutenzione Preventiva: Pianificazione e Checklist Giornaliere/Settimanali**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `02-MANUTENZIONE-PREVENTIVA/calendario-manutenzione-annuale.md` | Piano annuale mese per mese, maintenance windows, blackout periods, coordinamento inter-team | 3-4 |
| `02-MANUTENZIONE-PREVENTIVA/pianificazione-finestre-manutenzione.md` | Definizione, comunicazione, approval process, emergency maintenance, rollback criteria | 2-3 |
| `02-MANUTENZIONE-PREVENTIVA/checklist-giornaliere.md` | Backup verification, monitoring check, spazio disco, servizi critici, security alerts | 2-3 |
| `02-MANUTENZIONE-PREVENTIVA/checklist-settimanali.md` | Patch status, trend performance, log analysis, job schedulati, Active Directory health | 2-3 |

**Settimana 4 — Manutenzione Preventiva: Checklist Periodiche**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `02-MANUTENZIONE-PREVENTIVA/checklist-mensili.md` | Firmware review, certificati SSL/TLS, access review, test restore, security scan | 2-3 |
| `02-MANUTENZIONE-PREVENTIVA/checklist-trimestrali.md` | DR drill, penetration test, license audit, vendor review, capacity planning | 2-3 |
| `02-MANUTENZIONE-PREVENTIVA/checklist-semestrali.md` | Full infrastructure audit, BCP test, vendor contract review, technology roadmap | 2-3 |
| `02-MANUTENZIONE-PREVENTIVA/checklist-annuali.md` | Full asset inventory, warranty audit, complete DR test, budget e strategic planning | 2-3 |

Attività pratica: creare il calendario di manutenzione annuale personalizzato per la propria organizzazione e iniziare a implementare le checklist giornaliere.

**Settimana 5 — Gestione Sistemi Operativi e Servizi Infrastrutturali**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `03-GESTIONE-SISTEMI-OPERATIVI/` (tutti i documenti) | Patch management Windows e Linux, lifecycle management OS, hardening, performance tuning | 5-6 |
| `04-SERVIZI-INFRASTRUTTURA/` (tutti i documenti) | DNS, DHCP, Active Directory, web server, database server, mail server, servizi di stampa | 4-5 |

**Settimana 6 — Gestione Asset e Procedure Operative**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `08-GESTIONE-ASSET/` (tutti i documenti) | Ciclo di vita degli asset, inventory management, license compliance, EOL/EOS planning, procurement | 4-5 |
| `09-PROCEDURE-OPERATIVE/` (tutti i documenti) | SOP operative, runbook per task comuni, escalation procedures, on-call management, war room protocol | 4-5 |

Attività pratica: implementare le checklist a tutti i livelli temporali, verificare l'inventario degli asset e creare/aggiornare almeno tre SOP per le attività più critiche.

**Milestone Fase 2:** Al termine della sesta settimana, il professionista deve avere un calendario di manutenzione annuale operativo, set completo di checklist implementate, competenze aggiornate sulla gestione dei sistemi operativi e dei servizi infrastrutturali, e un inventario degli asset verificato con le relative procedure operative.

### Fase 3: Sicurezza e Continuità (settimane 7-9)

**Obiettivo:** Integrare la sicurezza operativa nei processi di manutenzione e garantire la capacità di ripristino in caso di disastro. Sviluppare competenze avanzate in monitoraggio, risposta agli incidenti di sicurezza e business continuity.

**Settimana 7 — Sicurezza Operativa**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `05-SICUREZZA-OPERATIVA/` (tutti i documenti) | Vulnerability management, patch di sicurezza, hardening periodico, firewall rule review, access control review, SIEM monitoring, EDR management | 6-8 |

Attività pratica: condurre un vulnerability scan dell'infrastruttura, rivedere le regole del firewall e le policy di accesso, e verificare che tutti i sistemi di sicurezza siano aggiornati e configurati correttamente.

**Settimana 8 — Backup e Disaster Recovery**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `06-BACKUP-DISASTER-RECOVERY/` (tutti i documenti) | Strategia 3-2-1, policy di backup, test di restore, RPO/RTO, piano di disaster recovery, BCP, site recovery, runbook DR | 6-8 |

Attività pratica: verificare i backup esistenti eseguendo test di restore reali, documentare RPO e RTO per ogni servizio critico, e condurre un tabletop exercise di disaster recovery con il team.

**Settimana 9 — Monitoraggio e Gestione degli Incidenti**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `07-MONITORAGGIO-INCIDENTI/` (tutti i documenti) | Architettura di monitoraggio, alerting, threshold, dashboard, correlazione eventi, incident response operativo, post-mortem, comunicazione durante gli incidenti | 6-8 |

Attività pratica: rivedere la configurazione del sistema di monitoraggio, ottimizzare le soglie di alerting per ridurre i falsi positivi, e creare un template per post-mortem da utilizzare dopo ogni incidente significativo.

**Milestone Fase 3:** Al termine della nona settimana, il professionista deve avere una postura di sicurezza operativa verificata e documentata, procedure di backup e disaster recovery testate, un sistema di monitoraggio ottimizzato e procedure di incident response mature.

### Fase 4: Governance e Miglioramento (settimane 10-12)

**Obiettivo:** Elevare la manutenzione IT da attività operativa a funzione strategica governata. Implementare metriche e KPI, sviluppare capacità di pianificazione a lungo termine e istituzionalizzare il miglioramento continuo.

**Settimana 10 — Pianificazione e Reportistica**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `10-PIANIFICAZIONE-REPORTISTICA/` (tutti i documenti) | Capacity planning, budget IT, TCO analysis, reporting per il management, dashboard KPI, trend analysis, technology roadmap | 6-8 |

Attività pratica: creare un report di manutenzione mensile per il management, definire i KPI principali da monitorare e costruire una dashboard operativa.

**Settimana 11 — Troubleshooting Sistematico**

| Documento | Argomenti Chiave | Ore Stimate |
|-----------|------------------|-------------|
| `11-TROUBLESHOOTING-GENERALE/` (tutti i documenti) | Metodologie di troubleshooting, diagnosi di rete, diagnosi server, diagnosi applicativa, strumenti diagnostici, escalation tecnica, knowledge base | 6-8 |

Attività pratica: creare una knowledge base di troubleshooting per i problemi più comuni nell'infrastruttura, con alberi decisionali e procedure passo-passo.

**Settimana 12 — Revisione, Integrazione e Piano di Miglioramento**

Questa settimana è dedicata alla revisione complessiva del percorso e alla creazione di un piano di miglioramento continuo:

- Rifare l'autovalutazione delle competenze e confrontare con i risultati iniziali
- Identificare le aree che necessitano di ulteriore approfondimento
- Creare un improvement register con le azioni concrete da implementare nei prossimi 3-6 mesi
- Pianificare sessioni di knowledge sharing con il team
- Definire obiettivi SMART per il prossimo trimestre
- Aggiornare il calendario di manutenzione annuale alla luce dell'esperienza acquisita

**Milestone Fase 4:** Al termine della dodicesima settimana, il professionista deve avere un sistema di reporting e KPI operativo, competenze avanzate di troubleshooting sistematico, un piano di miglioramento continuo documentato e la capacità di comunicare il valore della manutenzione IT al management.

---

## Ambiente di Laboratorio

### Configurazione Raccomandata del Laboratorio

Per praticare in modo efficace gli scenari di manutenzione IT è fondamentale disporre di un ambiente di laboratorio che replichi, almeno in scala ridotta, un'infrastruttura IT reale. L'ambiente di laboratorio permette di esercitarsi in attività come il patch management, il disaster recovery, il troubleshooting e la simulazione di guasti senza rischi per l'infrastruttura di produzione.

**Requisiti hardware minimi della workstation host:**
- CPU: processore con almeno 8 core e supporto alla virtualizzazione (Intel VT-x / AMD-V)
- RAM: 32 GB (raccomandati 64 GB per eseguire più VM simultaneamente)
- Storage: SSD NVMe da almeno 500 GB dedicato al laboratorio (raccomandato 1 TB)
- Rete: una scheda di rete fisica; si possono creare reti virtuali via software

**Architettura dell'ambiente di laboratorio consigliata:**

```
+-----------------------------------------------------+
|                    HOST HYPERVISOR                    |
|           (Proxmox VE, VMware Workstation            |
|            oppure VirtualBox + Vagrant)               |
+-----------------------------------------------------+
|                                                       |
|  +-------------+  +-------------+  +--------------+  |
|  | VM-DC01     |  | VM-SRV01    |  | VM-SRV02     |  |
|  | Windows     |  | Windows     |  | Linux         |  |
|  | Server 2022 |  | Server 2022 |  | (Ubuntu/RHEL) |  |
|  | AD, DNS,    |  | File Server,|  | Web Server,   |  |
|  | DHCP, GPO   |  | Print Svc   |  | Database      |  |
|  +-------------+  +-------------+  +--------------+  |
|                                                       |
|  +-------------+  +-------------+  +--------------+  |
|  | VM-MON01    |  | VM-FW01     |  | VM-BKP01     |  |
|  | Linux       |  | pfSense /   |  | Linux         |  |
|  | Zabbix +    |  | OPNsense    |  | Veeam CE /    |  |
|  | Grafana     |  | Firewall    |  | BorgBackup    |  |
|  +-------------+  +-------------+  +--------------+  |
|                                                       |
|  +-------------+  +-------------+                    |
|  | VM-TICKET01 |  | VM-SIEM01   |                    |
|  | GLPI / iTop |  | Wazuh       |                    |
|  | Ticketing   |  | SIEM + EDR  |                    |
|  +-------------+  +-------------+                    |
+-----------------------------------------------------+
```

### Strumenti Necessari

**Monitoraggio e alerting:**
- **Zabbix** (open source): piattaforma di monitoraggio enterprise-grade. Supporta SNMP, agent-based e agentless monitoring, discovery automatico, dashboard personalizzabili e alerting avanzato. Ideale per monitorare server, reti, applicazioni e servizi.
- **Grafana** (open source): piattaforma di visualizzazione dati. Si integra con Zabbix, Prometheus e numerose altre sorgenti dati per creare dashboard operative e manageriali.
- **Prometheus** (open source): sistema di monitoraggio e alerting basato su time-series. Particolarmente indicato per ambienti containerizzati e cloud-native.
- **Uptime Kuma** (open source): monitor semplice per verificare la disponibilità di servizi web, porte TCP, DNS e certificati SSL.

**Ticketing e ITSM:**
- **GLPI** (open source): piattaforma completa di IT Asset Management e Service Desk. Include gestione ticket, inventory, CMDB, knowledge base e reporting.
- **iTop** (open source): piattaforma ITSM conforme ITIL. Gestisce CMDB, incident, problem, change management e SLA.
- **Zammad** (open source): alternativa moderna per il service desk con interfaccia web intuitiva e supporto multicanale.

**Backup e disaster recovery:**
- **Veeam Backup & Replication Community Edition** (gratuito): soluzione di backup per ambienti virtualizzati, limitata a 10 workload nella versione gratuita.
- **BorgBackup** (open source): backup deduplicato e crittografato per sistemi Linux. Efficiente in termini di spazio e prestazioni.
- **Restic** (open source): backup crittografato con supporto per molteplici backend di storage (locale, S3, SFTP, Azure Blob).

**Sicurezza:**
- **Wazuh** (open source): piattaforma SIEM e EDR. Fornisce analisi dei log, rilevamento intrusioni, vulnerability assessment, file integrity monitoring e incident response.
- **OpenVAS / Greenbone** (open source): scanner di vulnerabilità per identificare debolezze nell'infrastruttura.
- **CrowdSec** (open source): sistema collaborativo di rilevamento e risposta alle intrusioni.

**Automazione:**
- **Ansible** (open source): strumento di configuration management e automazione agentless. Ideale per automatizzare attività di manutenzione ripetitive.
- **PowerShell** (integrato in Windows, disponibile per Linux): linguaggio di scripting essenziale per l'automazione su piattaforme Microsoft.
- **Bash scripting**: fondamentale per l'automazione su sistemi Linux.

### Configurazione VM per Simulazione di Guasti

L'apprendimento più efficace nella manutenzione IT avviene attraverso la pratica della gestione dei guasti in un ambiente controllato. Di seguito sono descritti alcuni scenari di simulazione.

**Scenario 1: Guasto disco e rebuild RAID.**
Configurare una VM con un array RAID 1 o RAID 5 software (mdadm su Linux o Storage Spaces su Windows). Rimuovere un disco virtuale dall'array per simulare un guasto. Praticare le procedure di identificazione del disco guasto, sostituzione con un hot spare e rebuild dell'array. Verificare l'integrità dei dati dopo il rebuild. Questo scenario esercita le competenze di manutenzione correttiva e la comprensione dei concetti di ridondanza.

**Scenario 2: Failure di un servizio critico e disaster recovery.**
Arrestare intenzionalmente il servizio Active Directory sulla VM-DC01 o corrompere un database sulla VM-SRV02. Praticare le procedure di ripristino: restore da backup, ricostruzione del servizio, verifica dell'integrità. Misurare il tempo effettivo di ripristino e confrontarlo con l'RTO definito. Questo scenario esercita sia le competenze di incident management sia quelle di disaster recovery.

**Scenario 3: Incidente di sicurezza simulato.**
Utilizzare strumenti di penetration testing (in ambiente controllato e isolato) per simulare un attacco. Monitorare il rilevamento da parte del SIEM (Wazuh), praticare le procedure di incident response, contenere l'attacco, eradicare la minaccia e documentare l'intero processo in un post-mortem. Questo scenario integra le competenze di sicurezza operativa con quelle di gestione degli incidenti.

**Scenario 4: Patch management e rollback.**
Applicare un aggiornamento su una VM di test che causa un'incompatibilità applicativa (simulare il problema configurando deliberatamente un conflitto). Praticare le procedure di identificazione del problema, rollback dell'aggiornamento, comunicazione agli stakeholder e pianificazione di una soluzione alternativa. Questo scenario esercita le competenze di change management e troubleshooting.

**Scenario 5: Capacity planning sotto stress.**
Utilizzare strumenti di stress testing (stress-ng su Linux, HeavyLoad su Windows) per saturare le risorse di una o più VM. Osservare il comportamento del sistema di monitoraggio, analizzare gli alert generati, identificare i colli di bottiglia e pianificare un'azione di capacity expansion. Questo scenario esercita le competenze di monitoraggio e pianificazione della capacità.

---

## Glossario

Glossario completo dei termini fondamentali della manutenzione IT. Per ogni termine viene indicata la definizione in italiano e, dove applicabile, il termine originale in inglese.

| Termine | Equivalente Inglese | Definizione |
|---------|---------------------|-------------|
| **ITIL** | Information Technology Infrastructure Library | Framework di best practice per la gestione dei servizi IT, attualmente alla versione 4. Definisce processi, practice e principi guida per la fornitura e il supporto dei servizi IT. |
| **ITSM** | IT Service Management | Disciplina che riguarda la progettazione, la fornitura, la gestione e il miglioramento dei servizi IT all'interno di un'organizzazione. |
| **SLA** | Service Level Agreement | Accordo formale tra un fornitore di servizi e un cliente che definisce i livelli di servizio attesi, le metriche di misurazione e le conseguenze del mancato rispetto. |
| **SLO** | Service Level Objective | Obiettivo specifico e misurabile all'interno di un SLA. Ad esempio: disponibilità del 99,9%, tempo di risposta inferiore a 200ms. |
| **SLI** | Service Level Indicator | Metrica quantitativa utilizzata per misurare il livello di servizio effettivamente erogato. L'SLI alimenta la valutazione del raggiungimento dell'SLO. |
| **MTTR** | Mean Time To Repair/Resolve | Tempo medio necessario per riparare un componente guasto o risolvere un incidente, calcolato dalla presa in carico alla risoluzione. |
| **MTBF** | Mean Time Between Failures | Tempo medio tra un guasto e il successivo su un componente o sistema. Indicatore chiave dell'affidabilità. |
| **MTTA** | Mean Time To Acknowledge | Tempo medio che intercorre tra il rilevamento di un incidente e la sua presa in carico da parte del team tecnico. |
| **MTTD** | Mean Time To Detect | Tempo medio necessario per rilevare un guasto o un incidente dal momento in cui si verifica. |
| **MTTF** | Mean Time To Failure | Tempo medio al primo guasto per componenti non riparabili. Differisce dal MTBF che si applica a componenti riparabili. |
| **RTO** | Recovery Time Objective | Tempo massimo accettabile per il ripristino di un servizio dopo un'interruzione. Definisce "quanto tempo possiamo permetterci di stare fermi". |
| **RPO** | Recovery Point Objective | Quantità massima di dati che l'organizzazione può permettersi di perdere, espressa in termini temporali. Definisce "quanti dati possiamo permetterci di perdere". |
| **CMDB** | Configuration Management Database | Database centralizzato che contiene informazioni dettagliate su tutti i componenti dell'infrastruttura IT (Configuration Item) e le relazioni tra di essi. |
| **CI** | Configuration Item | Qualsiasi componente gestito nell'ambito dell'IT Service Management che deve essere controllato per garantire l'erogazione dei servizi: server, switch, applicazioni, licenze, documentazione. |
| **CAB** | Change Advisory Board | Comitato consultivo composto da rappresentanti tecnici e di business che valuta, autorizza e pianifica i cambiamenti all'infrastruttura IT. |
| **RFC** | Request for Change | Richiesta formale per l'implementazione di un cambiamento all'infrastruttura IT. Contiene la descrizione del cambiamento, la giustificazione, l'analisi dei rischi e il piano di rollback. |
| **Incidente** | Incident | Interruzione non pianificata di un servizio IT o riduzione della qualità di un servizio. L'obiettivo della gestione degli incidenti è ripristinare il servizio il prima possibile. |
| **Problema** | Problem | Causa radice di uno o più incidenti. La gestione dei problemi indaga le cause e implementa soluzioni permanenti per prevenire ricorrenze. |
| **Errore noto** | Known Error | Un problema di cui è stata identificata la causa radice e per il quale esiste un workaround documentato, ma non ancora una soluzione definitiva. |
| **Workaround** | Workaround | Soluzione temporanea che permette di ridurre l'impatto di un incidente o problema in attesa di una risoluzione definitiva. |
| **Analisi delle cause radice** | Root Cause Analysis (RCA) | Processo sistematico di indagine per identificare la causa fondamentale di un incidente o problema, utilizzando tecniche come 5 Whys, diagramma di Ishikawa, Fault Tree Analysis. |
| **Post-mortem** | Post-Mortem / Post-Incident Review | Revisione strutturata condotta dopo un incidente significativo per documentare cosa è successo, perché, come è stato risolto e quali azioni preventive implementare. Deve essere blameless (senza colpevolizzazione). |
| **Patch Tuesday** | Patch Tuesday | Secondo martedì di ogni mese, data in cui Microsoft rilascia gli aggiornamenti di sicurezza per i propri prodotti. Riferimento chiave per la pianificazione del patch management. |
| **Zero-day** | Zero-Day | Vulnerabilità di sicurezza sconosciuta al vendor del software, per la quale non esiste ancora una patch. Rappresenta il rischio più elevato in termini di sicurezza. |
| **CVE** | Common Vulnerabilities and Exposures | Sistema standardizzato di identificazione delle vulnerabilità di sicurezza note. Ogni vulnerabilità riceve un identificativo univoco (es. CVE-2024-12345). |
| **CVSS** | Common Vulnerability Scoring System | Sistema di punteggio standardizzato (da 0 a 10) per valutare la gravità delle vulnerabilità di sicurezza. Guida la prioritizzazione del patching. |
| **SOC** | Security Operations Center | Centro operativo dedicato al monitoraggio continuo della sicurezza informatica, al rilevamento delle minacce e alla risposta agli incidenti di sicurezza. |
| **SIEM** | Security Information and Event Management | Piattaforma che raccoglie, correla e analizza i log e gli eventi di sicurezza provenienti da tutte le fonti dell'infrastruttura IT per identificare minacce e anomalie. |
| **EDR** | Endpoint Detection and Response | Soluzione di sicurezza installata sugli endpoint (server, workstation) che monitora le attività in tempo reale, rileva comportamenti sospetti e consente la risposta remota agli incidenti. |
| **SNMP** | Simple Network Management Protocol | Protocollo standard per il monitoraggio e la gestione dei dispositivi di rete. Permette di raccogliere metriche di prestazione e stato da switch, router, server e altri dispositivi. |
| **UPS** | Uninterruptible Power Supply | Gruppo di continuità che fornisce alimentazione elettrica di emergenza in caso di interruzione della rete elettrica, proteggendo i sistemi da spegnimenti improvvisi. |
| **PDU** | Power Distribution Unit | Unità di distribuzione dell'alimentazione all'interno di un rack o data center. Le PDU intelligenti permettono il monitoraggio remoto del consumo energetico e il controllo delle singole prese. |
| **RAID** | Redundant Array of Independent Disks | Tecnologia di ridondanza dei dischi che combina più unità fisiche per migliorare le prestazioni e/o la tolleranza ai guasti. I livelli più comuni sono RAID 1 (mirroring), RAID 5 (striping con parità) e RAID 10. |
| **Hot spare** | Hot Spare | Disco di riserva pre-configurato in un array RAID che entra automaticamente in funzione quando un disco dell'array si guasta, avviando il rebuild senza intervento manuale. |
| **Failover** | Failover | Meccanismo automatico di commutazione su un sistema ridondante quando il sistema primario si guasta. Garantisce la continuità del servizio con interruzione minima o nulla. |
| **Runbook** | Runbook | Documento operativo che contiene le procedure passo-passo per l'esecuzione di attività di routine o la gestione di scenari specifici. Deve essere sufficientemente dettagliato da poter essere seguito da qualsiasi membro del team. |
| **SOP** | Standard Operating Procedure | Procedura operativa standard: documento formale che descrive le istruzioni dettagliate per l'esecuzione di un processo o attività specifica in modo coerente e ripetibile. |
| **Escalation** | Escalation | Processo di trasferimento di un incidente o problema a un livello di competenza o autorità superiore. Può essere funzionale (a un team più specializzato) o gerarchica (al management). |
| **Reperibilità** | On-Call | Regime di disponibilità in cui un tecnico è reperibile al di fuori dell'orario lavorativo per gestire incidenti critici. Prevede rotazioni, tempi di risposta definiti e procedure di escalation. |
| **War room** | War Room | Sessione operativa di emergenza in cui i membri chiave del team tecnico e del management si riuniscono (fisicamente o virtualmente) per coordinare la risposta a un incidente critico (major incident). |
| **Pianificazione della capacità** | Capacity Planning | Processo di analisi e previsione della domanda futura di risorse IT (CPU, memoria, storage, banda di rete) per garantire che l'infrastruttura sia adeguata a soddisfare le esigenze del business. |
| **TCO** | Total Cost of Ownership | Costo totale di possesso di un asset IT, che include non solo il costo di acquisto ma anche i costi di installazione, manutenzione, formazione, energia, licenze e dismissione. |
| **EOL / EOS** | End of Life / End of Support | Fine vita / fine supporto di un prodotto. EOL indica che il prodotto non è più venduto; EOS indica che il vendor non fornisce più aggiornamenti e supporto tecnico. |
| **Hardening** | Hardening | Processo di riduzione della superficie di attacco di un sistema attraverso la disabilitazione di servizi non necessari, la configurazione restrittiva dei permessi, l'applicazione di policy di sicurezza e la rimozione di componenti superflui. |
| **KEDB** | Known Error Database | Database che contiene gli errori noti, le relative cause radice identificate e i workaround disponibili. Alimentato dal processo di Problem Management, è utilizzato dall'Incident Management per velocizzare la risoluzione. |
| **CSI** | Continual Service Improvement | Approccio sistematico al miglioramento continuo dei servizi IT, basato sul ciclo PDCA e sulle metriche di performance. In ITIL v4 è integrato nel Service Value System. |
| **PDCA** | Plan-Do-Check-Act | Ciclo di Deming: metodologia iterativa di miglioramento continuo composta da quattro fasi — pianificare, eseguire, verificare, agire per correggere e standardizzare. |

---

## Certificazioni Rilevanti

Lo studio del materiale di questa sezione prepara, direttamente o indirettamente, al conseguimento di diverse certificazioni professionali riconosciute a livello internazionale.

### ITIL 4 Foundation

**Ente certificatore:** AXELOS / PeopleCert
**Prerequisiti:** Nessuno
**Formato esame:** 40 domande a risposta multipla, 60 minuti, punteggio minimo 65% (26/40)
**Costo indicativo:** 350-450 EUR
**Validità:** 3 anni (rinnovabile tramite CPD)

La certificazione ITIL 4 Foundation è il punto di partenza per qualsiasi professionista IT che voglia strutturare la gestione dei servizi. Copre il Service Value System, i 7 guiding principles, le 4 dimensioni del service management, la Service Value Chain e le 34 practice ITIL. Il materiale della Fase 1 del piano di studio fornisce una preparazione solida sui concetti fondamentali, sebbene si raccomandi lo studio del manuale ufficiale per la preparazione completa all'esame.

Percorso di certificazione successivo: ITIL 4 Managing Professional (MP) con i moduli Create Deliver and Support, Drive Stakeholder Value, High Velocity IT e Direct Plan and Improve; oppure ITIL 4 Strategic Leader (SL) con i moduli Direct Plan and Improve e Digital and IT Strategy.

### CompTIA Server+

**Ente certificatore:** CompTIA
**Prerequisiti:** Raccomandati 18-24 mesi di esperienza con server
**Formato esame:** massimo 90 domande (multiple choice e performance-based), 90 minuti, punteggio minimo 750/900
**Costo indicativo:** 300-380 EUR
**Validità:** 3 anni (rinnovabile tramite CE)

La certificazione Server+ valida le competenze nella gestione e manutenzione dei server in ambienti data center. I domini dell'esame — Server Hardware Installation and Management, Server Administration, Security and Disaster Recovery, Troubleshooting — si allineano strettamente con i contenuti delle fasi 2, 3 e 4 del piano di studio.

### Certificazioni Vendor-Specific

**Microsoft Certified: Windows Server Hybrid Administrator Associate.**
Certificazione che valida le competenze nella gestione di ambienti Windows Server on-premises e hybrid. Rilevante per la Sezione 03 (Gestione Sistemi Operativi) e la Sezione 04 (Servizi Infrastruttura). Richiede il superamento dell'esame AZ-800 e AZ-801.

**Linux Professional Institute (LPI) — LPIC-1 e LPIC-2.**
Certificazioni vendor-neutral per l'amministrazione di sistemi Linux. LPIC-1 copre l'amministrazione di base, LPIC-2 l'amministrazione avanzata inclusa la manutenzione dei servizi di rete e la pianificazione della capacità. Rilevanti per le sezioni 03 e 04.

**Red Hat Certified System Administrator (RHCSA) e Red Hat Certified Engineer (RHCE).**
Certificazioni specifiche per ambienti Red Hat Enterprise Linux. La RHCSA copre le competenze fondamentali di amministrazione, la RHCE aggiunge competenze avanzate di automazione con Ansible. Rilevanti per le sezioni 03, 04 e per l'automazione della manutenzione.

**Altre certificazioni complementari:**
- ISO/IEC 20000 Foundation — standard certificabile per l'IT Service Management
- COBIT 2019 Foundation — framework di governance IT
- CompTIA Security+ — fondamenti di sicurezza informatica, complementare alla Fase 3
- VMware Certified Professional - Data Center Virtualization (VCP-DCV) — per ambienti virtualizzati

---

## Risorse Consigliate

### Libri

| Titolo | Autore(i) | Focus | Rilevanza |
|--------|-----------|-------|-----------|
| *ITIL 4 Foundation: ITIL 4 Edition* | AXELOS | Framework ITIL completo | Riferimento principale per la Fase 1 |
| *The Practice of System and Network Administration* (3a ed.) | T. Limoncelli, C. Hogan, S. Chalup | Best practice per sysadmin | Riferimento trasversale per tutte le fasi |
| *The Phoenix Project* | G. Kim, K. Behr, G. Spafford | DevOps e IT operations (romanzo) | Comprensione culturale del cambiamento IT |
| *Site Reliability Engineering* | Google (B. Beyer et al.) | Pratiche SRE | Approccio ingegneristico all'affidabilità |
| *The Visible Ops Handbook* | G. Kim, K. Behr, G. Spafford | IT operations improvement | Quick win per migliorare le operazioni IT |
| *Time Management for System Administrators* | T. Limoncelli | Produttività per sysadmin | Gestione del tempo nelle attività di manutenzione |
| *Infrastructure as Code* (2a ed.) | K. Morris | Automazione infrastruttura | Manutenzione automatizzata e ripetibile |
| *Database Reliability Engineering* | L. Campbell, C. Majors | Affidabilità database | Manutenzione dei sistemi database |

### Documentazione e Standard

- **ITIL 4 Practice Guides** — guide ufficiali per ogni practice ITIL, disponibili tramite sottoscrizione PeopleCert
- **NIST SP 800-53** — catalogo di controlli di sicurezza, rilevante per la sicurezza operativa
- **NIST Cybersecurity Framework (CSF)** — framework per la gestione del rischio di cybersecurity
- **CIS Benchmarks** — linee guida di hardening per sistemi operativi, applicazioni e dispositivi di rete
- **ISO/IEC 27001** — standard per i sistemi di gestione della sicurezza delle informazioni
- **Documentazione ufficiale Microsoft** — docs.microsoft.com per Windows Server, Active Directory, Azure
- **Red Hat Documentation** — documentazione ufficiale per RHEL, Ansible, OpenShift
- **Documentazione Debian/Ubuntu** — wiki e manuale dell'amministratore Debian

### Strumenti e Piattaforme

**ITSM e Ticketing:**
ServiceNow, Jira Service Management, GLPI, iTop, Znuny (fork di OTRS), Zammad

**Monitoraggio:**
Zabbix, Prometheus + Grafana, Nagios / Icinga2, PRTG, Datadog, Checkmk, Uptime Kuma

**Documentazione e Knowledge Base:**
Confluence, BookStack, Outline, Wiki.js, MkDocs, DocuWiki, Notion

**Asset Management:**
Snipe-IT, GLPI, Lansweeper, PDQ Inventory, ManageEngine AssetExplorer

**Automazione e Configuration Management:**
Ansible, Terraform, Puppet, Chef, SaltStack, PowerShell DSC

**Backup e Recovery:**
Veeam Backup and Replication, Commvault, Bacula / Bareos, Restic, BorgBackup, Acronis Cyber Protect

**Sicurezza:**
Wazuh (SIEM/EDR), OpenVAS / Greenbone (vulnerability scanner), CrowdSec, Nessus, Qualys

### Community e Formazione Online

- **r/sysadmin** (Reddit) — community attiva di system administrator
- **ServerFault** (Stack Exchange) — domande e risposte per professionisti IT
- **Spiceworks Community** — forum per IT professionals
- **AXELOS / PeopleCert** (axelos.com) — risorse ufficiali ITIL
- **CompTIA** (comptia.org) — risorse per certificazioni e formazione
- **ISACA** (isaca.org) — governance, risk management, compliance
- **Linux Foundation Training** — corsi su Linux, Kubernetes, cloud-native
- **Microsoft Learn** — percorsi di apprendimento gratuiti per tecnologie Microsoft

---

*Ultimo aggiornamento: Marzo 2026*
*Versione: 2.0*
