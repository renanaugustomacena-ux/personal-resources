# ITIL 4 — Service Value Chain e 34 Practices in Pratica

> **Modulo 12** · **Tempo:** 90 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **34 practices ITIL v4: scegli quelle rilevanti, non tutte.** Per PMI italiane: 8-12 practices essenziali.
2. **SVS (Service Value System) abbraccia tutto.** Non e modulo, e mindset.
3. **Continual improvement: kaizen iterativo, no big bang.**
4. **Guiding principles: applicabili sempre.** "Focus on value", "Start where you are", ecc.


## Indice

1. [Panoramica](#panoramica)
2. [Concetti Fondamentali](#concetti-fondamentali)
   - [Da ITIL v3 a ITIL 4: il cambio di paradigma](#da-itil-v3-a-itil-4-il-cambio-di-paradigma)
   - [Il Service Value System (SVS)](#il-service-value-system-svs)
   - [I 7 Guiding Principles](#i-7-guiding-principles)
   - [La Service Value Chain](#la-service-value-chain)
   - [Le 4 Dimensioni del Service Management](#le-4-dimensioni-del-service-management)
3. [Guida Pratica alle 34 Practices](#guida-pratica-alle-34-practices)
   - [General Management Practices (14)](#general-management-practices-14)
   - [Service Management Practices (17)](#service-management-practices-17)
   - [Technical Management Practices (3)](#technical-management-practices-3)
   - [Le 10 Practices Critiche per PMI](#approfondimento-le-10-practices-critiche-per-pmi)
   - [NIS2 e Compliance: Impatto sulle Practices](#nis2-e-compliance-impatto-sulle-practices-itil-4)
   - [Analisi Costi Implementazione ITIL 4](#analisi-costi-implementazione-itil-4)
4. [Configurazione e Implementazione](#configurazione-e-implementazione)
   - [Mappatura ITIL 4 sulla realtà PMI italiana](#mappatura-itil-4-sulla-realtà-pmi-italiana)
   - [Tooling](#tooling-servicenow-glpi-jira-service-management-freshservice-otrs-zammad)
   - [Piano di adozione 90 giorni per PMI 50 dipendenti](#piano-di-adozione-90-giorni-per-pmi-50-dipendenti)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
   - [Problemi Organizzativi](#problemi-organizzativi)
   - [Problemi Tecnici](#problemi-tecnici)
   - [Problemi di Processo](#problemi-di-processo)
7. [FAQ — Domande Frequenti](#faq--domande-frequenti)
8. [Caso Studio: PMI Manifatturiera](#caso-studio-pmi-manifatturiera-80-dipendenti--prima-e-dopo-itil)
9. [Value Stream Mapping — Esempio Concreto](#value-stream-mapping--esempio-concreto)
10. [Template SLA per PMI](#template-sla-per-pmi)
11. [Riferimenti](#riferimenti)
12. [Esercizi](#esercizi)
13. [Auto-valutazione](#auto-valutazione)
14. [Glossario locale](#glossario-locale)

---

## Panoramica

ITIL (Information Technology Infrastructure Library) è il framework di service management più diffuso al mondo. Nato negli anni '80 come iniziativa del governo britannico (CCTA, oggi Cabinet Office), è passato attraverso cinque revisioni maggiori — v1 (1989), v2 (2000-2004), v3 (2007), v3 update (2011) — fino ad arrivare a ITIL 4 nel 2019, attualmente mantenuto da AXELOS (joint venture tra Cabinet Office e Capita) e ora di proprietà di PeopleCert.

ITIL 4 non è un semplice aggiornamento incrementale: rappresenta un ripensamento completo della disciplina. Il framework abbandona la rigidità procedurale dei "26 processi e 4 funzioni" della v3 in favore di un modello fluido basato su value streams, principi guida e practices riconfigurabili. Il cambiamento riflette l'evoluzione del contesto IT: cloud computing, DevOps, agile, lean, microservizi, sviluppo iterativo, prodotti invece di progetti.

Per una PMI italiana di 10-200 dipendenti il valore di ITIL 4 non è la certificazione — quella serve all'IT manager o al freelance che vuole vendere consulenza — ma la disponibilità di un vocabolario condiviso e di pattern collaudati. Sapere cosa significa "Change Enablement" o "Service Catalogue" evita di reinventare ruote già rotonde da quarant'anni. Allo stesso tempo, applicare ITIL alla lettera in un'azienda con 30 dipendenti è una ricetta per la paralisi: il framework va calato sul contesto, scegliendo cosa adottare subito, cosa rimandare, cosa skippare definitivamente.

Questa guida copre l'intero Service Value System, le 34 practices con focus su quelle critiche per ambienti enterprise e PMI, il confronto con framework affini (ISO/IEC 20000, COBIT 2019, DevOps), e un piano di adozione concreto su 90 giorni applicabile a una realtà italiana tipo: PMI 50 dipendenti, IT team 2-3 persone, ticketing rudimentale via email, qualche CI tracciato a memoria.

---

## Concetti Fondamentali

### Da ITIL v3 a ITIL 4: il cambio di paradigma

ITIL v3 era organizzato intorno al **Service Lifecycle**: 5 fasi (Service Strategy, Service Design, Service Transition, Service Operation, Continual Service Improvement) con 26 processi distribuiti tra le fasi e 4 funzioni (Service Desk, Technical Management, Application Management, IT Operations Management). Ogni processo aveva owner, attività, input/output formali e KPI definiti. Il modello era prescrittivo, esaustivo, e — onestamente — pesante. Una piccola variazione di firmware su uno switch poteva richiedere il passaggio formale per Change Management, Release Management, Deployment Management, con tre comitati separati e cinque approvazioni.

ITIL 4 abbandona questo schema. Il nuovo modello centrale si chiama **Service Value System (SVS)**: una struttura olistica che descrive come tutti i componenti dell'organizzazione concorrono insieme alla creazione di valore. Le novità sostanziali sono cinque:

1. **Da "processi" a "practices"**: una practice non è una sequenza rigida di passi, ma un set riconfigurabile di risorse (persone, processi, tecnologia, partner, informazioni) progettate per raggiungere un obiettivo. La stessa practice può essere implementata in modo molto diverso a seconda del contesto.
2. **Value Streams al posto del Service Lifecycle**: invece di seguire un servizio attraverso fasi sequenziali, si descrivono flussi di valore end-to-end che attraversano practices e attività.
3. **Principi guida espliciti**: i 7 Guiding Principles diventano parte centrale del framework e si applicano a qualsiasi practice in qualsiasi situazione.
4. **Integrazione esplicita con Agile, Lean, DevOps**: ITIL 4 non si pone più in alternativa a queste correnti, ma ne assorbe linguaggio e pratiche (ad esempio kanban, retrospective, blameless postmortem, value stream mapping).
5. **Change Enablement al posto di Change Management**: il termine non è cosmetico. Il vecchio Change Management era spesso percepito come freno burocratico (CAB rigido, lead time settimanali). Change Enablement enfatizza il rendere il cambiamento sicuro e veloce, con tre tipologie di change (Standard, Normal, Emergency) e meccanismi automatizzati per le pre-approvate.

In pratica, un team che faceva ITIL v3 "by the book" si trovava con Change Advisory Board settimanali da due ore in cui si discuteva di patch antivirus. ITIL 4 dice: quella patch antivirus va in Standard Change pre-approvato, eseguito automaticamente la notte del Patch Tuesday, e il CAB si occupa solo dei Normal Change con impatto significativo.

### Il Service Value System (SVS)

Il SVS è la struttura concettuale di alto livello di ITIL 4. Riceve in input **opportunità e domanda** dagli stakeholder e produce in output **valore**. È composto da cinque elementi:

**1. Guiding Principles**
Sette principi universali che guidano qualsiasi decisione (vedi sezione successiva). Si applicano alla pianificazione strategica come al troubleshooting di un singolo incidente.

**2. Governance**
Il sistema con cui l'organizzazione dirige e controlla le attività. In una PMI non significa avere un consiglio di governance IT formale, ma aver definito chi decide su priorità, budget, rischi, eccezioni. Anche un foglio Google con la matrice RACI è governance, se applicata.

**3. Service Value Chain (SVC)**
Modello operativo composto da sei attività interconnesse (Plan, Improve, Engage, Design & Transition, Obtain/Build, Deliver & Support) che descrivono il "come" si creano e si erogano i servizi.

**4. Practices**
Le 34 practices (14 General Management, 17 Service Management, 3 Technical Management) che forniscono le capacità organizzative concrete.

**5. Continual Improvement**
Attività ricorrente a tutti i livelli per garantire il miglioramento costante. ITIL 4 fornisce il **Continual Improvement Model** in 7 passi (vision, dove siamo, dove vogliamo arrivare, come ci arriviamo, agire, valutare, mantenere lo slancio).

L'idea chiave è che SVS non è una "macchina lineare" ma un sistema. Un ticket che arriva in Service Desk può attivare contemporaneamente Engage (comunicazione con utente), Deliver & Support (risoluzione), Improve (analisi trend), e l'attività non segue una sequenza rigida ma fluttua tra i sei snodi della Service Value Chain in base al contesto.

### I 7 Guiding Principles

I principi guida sono il cuore filosofico di ITIL 4. Li commento uno per uno con esempi calati su PMI italiana.

**1. Focus on Value (Concentrarsi sul valore)**

Ogni attività deve essere riconducibile a valore percepito dallo stakeholder. Esempio concreto: il team IT propone l'acquisto di una nuova soluzione di backup da 18.000 euro/anno. La domanda da farsi non è "è una buona soluzione?" ma "quale RPO/RTO permette di garantire? quanto costerebbe un downtime di 8 ore? il management considera accettabili i livelli attuali?". Il valore va sempre quantificato — anche grossolanamente — in termini comprensibili al business.

Anti-pattern tipico: l'IT che acquista uno strumento perché "è la best practice" e poi lo deve giustificare in CdA senza riferimenti al business case.

**2. Start Where You Are (Partire da dove ci si trova)**

Non si parte mai da zero. L'organizzazione ha già asset, processi (anche informali), competenze, dati. Prima di proporre rivoluzioni, fare assessment oggettivo. In una PMI italiana 50 dip., probabilmente esiste già: un foglio Excel con gli asset, una casella support@azienda.it dove arrivano i ticket, un calendario di backup che il sistemista esegue. Quello È il punto di partenza, non un greenfield.

Un consulente che arriva e dice "sostituiamo tutto con ServiceNow" senza guardare cosa esiste, sta violando il principio.

**3. Progress Iteratively with Feedback (Progredire iterativamente con feedback)**

Implementare un framework completo "big bang" è un fallimento garantito. Si procede a iterazioni piccole, misurabili, con feedback raccolto a ogni passo. Esempio: prima si introduce ticketing strutturato (1 mese), poi si formalizza la classificazione incidenti (1 mese), poi i workflow di escalation (1 mese), poi la knowledge base (2 mesi), poi la CMDB minima (3 mesi).

Il principio è anche difensivo: se la prima iterazione fallisce, hai perso un mese. Se tenti il big bang e fallisce dopo 9 mesi, hai perso il budget IT dell'anno e la fiducia del management.

**4. Collaborate and Promote Visibility (Collaborare e promuovere visibilità)**

Lavorare in silos uccide il flusso. Le decisioni invisibili generano sospetti e duplicazioni. Pratiche concrete: dashboard pubblici (anche un Grafana o Metabase letto in lettura da chiunque), kanban board visibile a tutto il team, post-mortem condivisi. In una PMI: anche solo un canale Teams o Slack #it-status con le attività in corso fa enorme differenza.

**5. Think and Work Holistically (Pensare e lavorare in modo olistico)**

Un cambiamento non vive isolato. La patch su un controller di dominio impatta autenticazione, fileserver, applicazioni line-of-business, accesso VPN, posta. Pensare olistico significa mappare le dipendenze prima di cambiare. La CMDB serve a questo, ma anche un grafico whiteboard dei servizi critici è un punto di partenza.

**6. Keep It Simple and Practical (Mantenere semplicità e praticità)**

Se il modulo di Change Request ha 47 campi obbligatori, nessuno lo compilerà correttamente: i tecnici barreranno valori a caso, e il dato sarà rumore. Meglio 6 campi compilati onestamente che 47 falsi. La regola pratica: ogni campo, ogni passo del workflow, ogni livello di approvazione deve giustificare la propria esistenza con un beneficio misurabile. Altrimenti taglia.

**7. Optimize and Automate (Ottimizzare e automatizzare)**

Prima si ottimizza il processo manuale, poi lo si automatizza. Automatizzare un processo inefficiente produce risultati inefficienti più rapidamente. Esempio: automatizzare l'onboarding utenti via PowerShell DSC ha senso solo dopo aver standardizzato cosa significa "utente nuovo": template AD, gruppi, mailbox, licenze M365, accessi LOB. Senza standardizzazione, ogni esecuzione dello script genera un caso particolare.

### La Service Value Chain

La Service Value Chain (SVC) è il "come operativo" del SVS. Sei attività interconnesse che assorbono input e producono output, riconfigurate dinamicamente in **value streams** specifici per scenario.

| Attività | Scopo |
|----------|-------|
| **Plan** | Garantire la comprensione condivisa di vision, stato attuale, priorità di miglioramento |
| **Improve** | Migliorare continuamente prodotti, servizi, practices in tutte le attività e dimensioni |
| **Engage** | Comprendere stakeholder, fornire trasparenza, costruire relazioni |
| **Design & Transition** | Progettare prodotti/servizi che soddisfino aspettative di qualità, costo, time-to-market |
| **Obtain/Build** | Garantire la disponibilità di componenti (hardware, software, licenze, persone) |
| **Deliver & Support** | Erogare servizi secondo le specifiche concordate |

Esempio di **value stream "Risoluzione incidente critico P1"**: arriva alert dal monitoring (Engage) → triage e classificazione (Deliver & Support) → ricerca soluzioni note in knowledge base (Plan + Deliver) → workaround temporaneo (Deliver) → comunicazione stakeholder (Engage) → root cause analysis post-risoluzione (Improve) → eventuale change permanente (Design & Transition + Obtain/Build).

Lo stesso value stream coinvolge contemporaneamente practices diverse: Incident Management, Service Desk, Problem Management, Knowledge Management, Communication, Change Enablement, Service Continuity. Non c'è una sequenza unica.

### Le 4 Dimensioni del Service Management

Per garantire un approccio olistico, ITIL 4 richiede di considerare quattro dimensioni in ogni iniziativa:

**1. Organizations and People**
Strutture, ruoli, competenze, cultura. Una nuova practice può fallire perché manca una skill, perché la cultura aziendale è ostile al cambiamento, perché i ruoli non sono chiari. In una PMI: chi è il "process owner" del Change Enablement quando l'IT è una persona che fa anche helpdesk e sistemista?

**2. Information and Technology**
Sistemi, dati, conoscenza, tecnologia. Include la CMDB, knowledge base, sistemi di monitoring, ticketing, ITSM platform, automazione. La qualità dei dati nella CMDB determina la qualità di Incident, Change, Problem.

**3. Partners and Suppliers**
Fornitori, vendor, MSP, contratti. Una PMI italiana ha tipicamente: un fornitore di connettività (TIM/Vodafone/Wind/Fastweb), un MSP per la posta M365, un fornitore di gestionale (Zucchetti, TeamSystem, ecc.), un produttore HW (Dell/HP/Lenovo). I rapporti vanno gestiti con SLA chiari, non con strette di mano.

**4. Value Streams and Processes**
I flussi di lavoro end-to-end e i processi che li compongono. È la dimensione "operativa" pura.

Tutte e quattro le dimensioni sono influenzate da fattori esterni (PESTLE: Political, Economic, Social, Technological, Legal, Environmental). Esempio: NIS2 (Legal/Political) impone audit di sicurezza che richiedono CMDB accurata (Technology) e competenze nuove (People) e contratti aggiornati con fornitori (Partners).

---

## Guida Pratica alle 34 Practices

Le 34 practices sono divise in tre categorie. Per ciascuna categoria descrivo tutte le practices, con focus dettagliato su quelle critiche per la manutenzione IT e per le PMI italiane.

### General Management Practices (14)

Le General Management Practices derivano da business management generico e non sono specifiche dell'IT.

**1. Architecture Management**
Mantiene visione olistica della struttura dell'organizzazione (business, applicazioni, dati, tecnologia, ambiente). Owner tipico: Enterprise Architect (in PMI: l'IT Manager). KPI: % servizi mappati nell'architettura di riferimento, debito architetturale stimato. Tool: ArchiMate, Sparx EA, draw.io per le PMI.

**2. Continual Improvement**
Iniziative ricorrenti a tutti i livelli per migliorare prodotti, servizi, practices. Owner: Process Owner / Service Owner. KPI: numero di Continual Improvement Register (CIR) entries chiuse per trimestre, ROI delle iniziative. Tool: registro CIR su Confluence/Jira/SharePoint.

**3. Information Security Management**
Protegge informazioni e sistemi da accesso non autorizzato. Owner: CISO o IT Manager con cappello sicurezza. KPI: incident di sicurezza, vulnerabilità non patchate sopra SLA, % asset coperti da scan vulnerabilità. Tool: SIEM (Wazuh, Splunk, Elastic), vulnerability scanner (Nessus, OpenVAS, Qualys).

**4. Knowledge Management**
Mantiene e migliora utilizzo efficace di informazioni e conoscenza. Owner: Knowledge Manager (in PMI: distribuita). KPI: # articoli KB creati, % ticket risolti via self-service, accuracy degli articoli (dating). Tool: Confluence, BookStack, MediaWiki, Notion, articoli embedded in GLPI/ServiceNow.

**5. Measurement and Reporting**
Supporta processo decisionale tramite dati. Owner: Service Manager. KPI: % servizi con metriche definite, frequenza review reportistica. Tool: Grafana, Metabase, Power BI, dashboard nativi ITSM platform.

**6. Organizational Change Management**
Garantisce che cambiamenti siano implementati in modo sostenibile, gestendo gli aspetti umani. Tipica differenza con Change Enablement: OCM riguarda persone e cultura, Change Enablement riguarda i sistemi.

**7. Portfolio Management**
Garantisce mix giusto di programmi, progetti, prodotti, servizi. Owner: Portfolio Manager / IT Director. Tool: Jira Portfolio, Microsoft Project Online, ServiceNow Strategic Portfolio.

**8. Project Management**
Garantisce esecuzione di progetti entro vincoli di tempo, costo, qualità. PMI: spesso si usano kanban semplici (Trello, Asana, Linear) o solo Gantt in Excel.

**9. Relationship Management**
Stabilisce e nutre relazioni tra organizzazione e stakeholder. KPI: NPS, CSAT, frequenza review business.

**10. Risk Management**
Identifica, valuta, gestisce rischi. KPI: # rischi nel registro, % mitigati, esposizione residua. Tool: Risk Register su Excel/Confluence, GRC tool (LogicGate, ServiceNow GRC) per enterprise.

**11. Service Financial Management**
Supporta strategia gestendo costi, fatturazione, charging. KPI: TCO per servizio, deviazione budget, costo per ticket.

**12. Strategy Management**
Definisce obiettivi dell'organizzazione e indirizzi per raggiungerli. Owner: CIO / IT Director.

**13. Supplier Management**
Garantisce che fornitori contribuiscano efficacemente alla strategia. KPI: % SLA fornitori rispettati, # contratti scaduti senza rinnovo. Tool: contratti in DMS, scadenzario, supplier scorecard.

**14. Workforce and Talent Management**
Garantisce che organizzazione abbia persone con skill e know-how giusti. KPI: skill matrix, giorni training/anno per persona, turnover.

### Service Management Practices (17)

Sono il cuore di ITIL e direttamente rilevanti per la manutenzione.

**1. Availability Management**
Garantisce che i servizi forniscano la disponibilità concordata. Owner: Availability Manager. KPI: % uptime per servizio, MTBF, MTTR, disponibilità misurata vs concordata. In una PMI: si traduce nel monitoring dei servizi critici e nella reportistica mensile sulla disponibilità.

**2. Business Analysis**
Analizza un business o sue componenti, definisce bisogni, raccomanda soluzioni.

**3. Capacity and Performance Management**
Garantisce che servizi raggiungano performance concordata e prevista. KPI: utilizzo CPU/RAM/storage/banda vs threshold, capacity forecast accuracy. Tool: Prometheus + Grafana, Zabbix, PRTG, vROps.

**4. Change Enablement**
Massimizza il numero di cambiamenti riusciti garantendo che rischio sia valutato correttamente. Sostituisce il vecchio "Change Management" v3. Tre tipologie di change:

| Tipologia | Descrizione | Esempio | Approvazione |
|-----------|-------------|---------|-------------|
| **Standard** | Pre-approvato, basso rischio, ripetibile | Onboarding utente standard, patch antivirus | Pre-approvazione globale |
| **Normal** | Richiede valutazione rischio caso per caso | Upgrade DBMS, migrazione fileserver | Change Authority (può essere CAB o singolo) |
| **Emergency** | Cambio urgente per risolvere incidente critico | Patch out-of-band per zero-day | Emergency Change Authority |

Owner: Change Manager. KPI: success rate cambiamenti, % cambiamenti emergency, lead time cambiamenti normal, # incidenti causati da change. Differenza chiave vs v3: il CAB rigido settimanale di 2 ore con 30 partecipanti è un anti-pattern. Si preferisce delega della decisione a Change Authority per ambito (es. il senior network engineer è Change Authority per cambi di rete sotto criticità media).

**5. Incident Management**
Minimizza impatto degli incidenti ripristinando il servizio. Owner: Incident Manager. KPI: MTTR, MTTA (Mean Time to Acknowledge), % incidenti risolti within SLA, % incidenti P1/P2.

**6. IT Asset Management (ITAM)**
Pianifica e gestisce ciclo di vita completo degli asset IT. Owner: IT Asset Manager. KPI: asset under management, % asset registrati, # licenze sotto-utilizzate, software audit risk. Tool: Snipe-IT, GLPI, ServiceNow ITAM, Lansweeper.

**7. Monitoring and Event Management**
Osserva sistematicamente servizi e CI, registrando e riportando cambi di stato come eventi. KPI: % servizi monitorati, signal-to-noise ratio degli alert, false positive rate. Tool: Zabbix, Nagios/Icinga, Prometheus, Datadog, New Relic.

**8. Problem Management**
Riduce probabilità e impatto di incidenti identificando cause reali e potenziali e gestendo workaround/known errors. KPI: # problem aperti, % problem risolti via permanent fix vs workaround, % incident ricorrenti collegati a problem aperto.

**9. Release Management**
Rende disponibili nuove o modificate funzionalità. KPI: # release/mese, success rate, lead time da merge a produzione.

**10. Service Catalogue Management**
Fornisce singola fonte coerente di informazioni su tutti i servizi. KPI: # servizi a catalogo, % aggiornati negli ultimi 12 mesi. Tool: catalogo nativo ServiceNow/GLPI/Jira SM, Confluence pages.

**11. Service Configuration Management**
Garantisce che informazioni accurate e affidabili sui CI siano disponibili (CMDB). Owner: Configuration Manager. KPI: # CI tracciati, accuracy CMDB, % servizi con relazioni CI mappate. Vedi documento dedicato `13-cmdb-glpi-snipeit-implementazione.md`.

**12. Service Continuity Management**
Garantisce che disponibilità e performance siano mantenute a livello sufficiente in caso di disastro. Include Business Continuity Plan, Disaster Recovery Plan. KPI: RTO, RPO, # DR test eseguiti/anno, success rate DR test.

**13. Service Design**
Progetta prodotti e servizi adatti allo scopo e all'uso.

**14. Service Desk**
Cattura domanda di risoluzione incidenti e richieste di servizio. Punto di contatto con utenti. KPI: First Call Resolution rate, abandonment rate, CSAT, AHT (Average Handle Time). Modelli: tier 1/2/3, swarming, follow-the-sun. Tool: tutti i ITSM citati.

**15. Service Level Management (SLM)**
Definisce, documenta, gestisce livelli di servizio. Genera SLA (Service Level Agreement) con clienti, OLA (Operational Level Agreement) interni, UC (Underpinning Contract) con fornitori. KPI: % SLA rispettati, breach count, trend.

**16. Service Request Management**
Supporta qualità concordata di un servizio gestendo le richieste user-initiated pre-definite. Esempi: nuovo utente, ripristino password, accesso a cartella, installazione SW standard.

**17. Service Validation and Testing**
Garantisce che nuovi/modificati prodotti soddisfino requisiti definiti. Include test funzionali, di performance, di sicurezza, di accessibilità. In PMI: almeno un ambiente di staging per testare prima del deploy in produzione. KPI: test coverage, defect rate post-release.

### Matrice Practices × Maturità PMI

Matrice che mostra quale forma assume ogni practice in funzione della maturità organizzativa:

| Practice | Livello 1 (Iniziale) | Livello 2 (Ripetibile) | Livello 3 (Definito) | Livello 4 (Gestito) |
|---|---|---|---|---|
| Service Desk | Email al sistemista | Casella support@ letta | GLPI con form + categorie | Portale self-service + chatbot |
| Incident Mgmt | "Qualcosa si è rotto" | Ticket con priorità | Workflow P1-P4 con SLA | Analytics, postmortem, trend |
| Change | "Aggiorno e vedo" | Log delle modifiche | Workflow Standard/Normal | Pre-approvazione automatica |
| Knowledge | Nella testa del tecnico | Foglio Word condiviso | Wiki strutturata con 50+ articoli | KB integrata nel ticketing, self-service |
| Monitoring | Nessuno | Ping + uptime check | Zabbix con template + alert | Alert intelligence, threshold dinamici |
| Asset Mgmt | Foglio Excel parziale | Excel completo | Tool ITAM (Snipe-IT, GLPI) | Discovery automatico + lifecycle |
| CMDB | Non esiste | Lista server manuale | CI critici mappati con relazioni | CMDB automatizzata + certificazione |
| Problem | Non esiste | "Perché succede sempre?" | Registro problemi + RCA | Proactive problem management |
| SLM | Non esiste | SLA informali | SLA formali + reporting | SLO + error budget |
| Continuity | "Abbiamo il backup" | Backup automatizzato | DR plan documentato | DR testato trimestralmente |

### Errori di Implementazione ITIL — Lezioni dal Campo

Raccolta di errori reali osservati in implementazioni ITIL in PMI italiane:

**Errore 1: Acquistare ServiceNow per 5 utenti.** Una PMI 40 dipendenti ha acquistato ServiceNow "perché è lo standard" — costo €70.000/anno, utilizzato al 5% delle funzionalità. GLPI avrebbe coperto il 95% delle esigenze a costo zero. Lezione: il tool deve essere proporzionato all'organizzazione.

**Errore 2: Implementare la CMDB prima del ticketing.** Un IT manager ha speso 6 mesi a mappare 2.000 CI in i-doit prima di avere un sistema di ticketing. Risultato: CMDB perfetta ma inutile, nessun miglioramento operativo. Lezione: Service Desk + Incident Management prima di tutto.

**Errore 3: CAB settimanale di 2 ore per 3 cambiamenti.** Una PMI ha replicato il modello CAB di un cliente enterprise: meeting settimanale da 2 ore con 8 partecipanti per discutere 3 cambiamenti che potevano essere Standard Change pre-approvati. Lezione: il CAB deve essere proporzionato al volume e alla complessità dei cambiamenti.

**Errore 4: KPI senza azione.** Un team produceva un report mensile con 25 KPI ma nessuno li leggeva o agiva su di essi. Lezione: 5 KPI con owner e target sono meglio di 25 KPI ignorati.

**Errore 5: Formazione ITIL senza implementazione.** Un'azienda ha certificato ITIL Foundation tutto il team IT (6 persone, €6.000) senza implementare nulla nei 12 mesi successivi. Lezione: la formazione senza applicazione pratica è spreco. Certificare 1-2 persone e investire il resto in implementazione.

**Errore 6: Ignorare la dimensione People.** Un IT manager ha implementato processi e tool perfetti ma non ha coinvolto il team nella progettazione. Risultato: resistenza, bypass, shadow IT. Lezione: le 4 dimensioni includono People — coinvolgere il team fin dall'inizio.

**Errore 7: Big bang vs iterazione.** Tentativo di implementare 15 practices contemporaneamente in 3 mesi. Risultato: nessuna implementata bene, burnout del team, management deluso. Lezione: 6 practices in 3 mesi, poi espandere. Guiding Principle #3: Progress Iteratively with Feedback.

**Errore 8: Customizzare il tool ITSM oltre ogni ragionevolezza.** Una PMI ha speso 4 mesi a customizzare GLPI con 47 campi custom, 12 workflow personalizzati, 8 profili ruolo diversi per 3 persone IT. Risultato: ogni aggiornamento GLPI rompeva le customizzazioni. Lezione: usare il tool as-is il più possibile, customizzare solo dove il beneficio è misurabile.

**Errore 9: Misurare senza agire.** Report SLA mensili perfetti, grafici bellissimi, nessuna azione correttiva. I report diventano decorazione. Lezione: ogni report deve includere "raccomandazioni" con owner e deadline. Se il report non genera azione, non serve il report.

**Errore 10: Separare IT Operations da IT Projects.** In una PMI, le stesse persone fanno entrambi. Creare una separazione artificiale (sprint planning separato dal ticket queue) genera conflitto di priorità e overhead di coordinamento. Lezione: in PMI <200 dipendenti, un backlog unificato con prioritizzazione chiara è più efficace di due silos.

### Technical Management Practices (3)

**1. Deployment Management**
Sposta nuovo/modificato hardware, software, documentazione, processo in ambienti live. Spesso confuso con Release: Release rende disponibile la funzionalità all'utente, Deployment è l'atto tecnico di muovere componenti.

KPI: deployment frequency, deployment failure rate, deployment lead time, rollback count. In PMI: ogni deploy deve essere tracciato con timestamp, versione, operatore, esito. Anche un deploy manuale di un aggiornamento gestionale va registrato.

Modelli di deployment:
- **Big bang**: tutto in una volta. Rischio alto, rollback complesso. Usato per migrazioni infrastrutturali one-shot.
- **Phased**: deploy progressivo per ambiente (dev → staging → produzione). Standard per PMI.
- **Blue/green**: due ambienti identici, switch del traffico. Richiede infrastruttura duplicata.
- **Canary**: deploy su piccolo subset di utenti/traffico, espansione progressiva. Richiede load balancer intelligente.
- **Rolling**: aggiornamento nodo per nodo nel cluster. Zero downtime se ben configurato.
- **Feature flags**: codice deployato ma funzionalità attivabile/disattivabile via configurazione. Separa deploy da release.

**2. Infrastructure and Platform Management**
Supervisiona infrastruttura e piattaforme. Cloud, on-prem, hybrid. Include: provisioning, configurazione, patching, capacity management, monitoring, dismissione. In una PMI: chi gestisce i server, il networking, lo storage, il cloud. KPI: uptime infrastrutturale, incident rate per piattaforma, compliance posture, cost per workload.

**3. Software Development and Management**
Garantisce che applicazioni soddisfino bisogni stakeholder per funzionalità, affidabilità, manutenibilità, conformità, controllabilità. Include SDLC (Software Development Life Cycle), testing, quality assurance, code review, CI/CD. In PMI che sviluppano software interno: pipeline Git → CI → test → staging → produzione. KPI: lead time for change, change failure rate, deployment frequency, MTTR (le 4 DORA metrics).

### Approfondimento: Le 10 Practices Critiche per PMI

Delle 34 practices ITIL 4, queste 10 sono quelle che una PMI italiana 30-200 dipendenti deve implementare per avere un IT strutturato. Per ciascuna forniamo un livello di dettaglio operativo maggiore.

**1. Service Desk — Il Punto di Contatto**

Il Service Desk è la faccia dell'IT verso il business. Un Service Desk inefficace significa utenti frustrati, problemi non tracciati, escalation caotiche, percezione negativa dell'IT.

Modelli di Service Desk:
| Modello | Descrizione | Adatto a |
|---|---|---|
| **Local** | SD fisicamente presente nella sede | PMI mono-sede con team IT locale |
| **Centralizzato** | SD unico per tutte le sedi | PMI multi-sede con team IT HQ |
| **Virtual** | SD distribuito, raggiungibile da ovunque | Aziende remote-first, MSP |
| **Follow-the-sun** | SD distribuito su timezone diverse per copertura 24h | Enterprise internazionale |
| **Swarming** | Nessun tier rigido, l'esperto giusto risponde direttamente | Team tecnici maturi, DevOps |

KPI operativi Service Desk:
- **FCR (First Call Resolution)**: % ticket risolti al primo contatto. Target PMI: >65%.
- **CSAT (Customer Satisfaction)**: sondaggio post-ticket. Target: >4.0/5.0.
- **AHT (Average Handle Time)**: tempo medio di gestione ticket. Benchmark PMI: 15-30 min.
- **Abandonment Rate**: % chiamate/chat abbandonate. Target: <5%.
- **Ticket Reopen Rate**: % ticket riaperti dopo chiusura. Target: <10%.
- **Backlog Age**: età media ticket aperti. Alert se P3 >5 giorni.

**2. Incident Management — Ripristinare il Servizio**

L'Incident Management ha un unico obiettivo: ripristinare il servizio il più rapidamente possibile minimizzando l'impatto. Non cerca il root cause (quello è Problem Management).

Workflow standard incident:

```
[Utente segnala / Alert monitoring]
        |
        v
[Registrazione ticket con categoria + priorità]
        |
        v
[Triage: è un incident o una request?]
        |
   Incident ─────────── Request → Service Request Management
        |
        v
[Classificazione priorità (Impatto × Urgenza)]
        |
   P1/P2 ─────────── P3/P4 → Coda standard
        |
        v
[Escalation immediata: on-call + IC]
        |
        v
[Investigation + workaround]
        |
        v
[Resolution + verifica con utente]
        |
        v
[Chiusura ticket + documentazione]
        |
   Se P1/P2 ──────── Trigger postmortem
```

**3. Problem Management — Trovare il Root Cause**

Problem Management è il complemento strategico di Incident Management. Mentre IM ripristina il servizio, PM identifica perché il servizio è fallito e previene ricorrenze.

Due modalità:
- **Reactive Problem Management**: analisi post-incident per incident ricorrenti o gravi. Input: postmortem, trend analysis incident.
- **Proactive Problem Management**: identificazione problemi prima che causino incident. Input: trend monitoring, capacity planning, vulnerability scanning.

Workflow: Incident ricorrente → apertura Problem Record → investigation → known error (workaround documentato) → change request per fix permanente → verifica → chiusura.

**4. Change Enablement — Cambiare in Sicurezza**

Il Change Enablement è la practice più controversa e più importante. Un processo troppo rigido rallenta l'innovazione. Un processo troppo permissivo genera incident da cambiamenti non controllati. Il bilanciamento è la sfida.

Template RFC (Request for Change) minimo per PMI:

```markdown
# Request for Change

**ID**: CHG-2026-0142
**Richiedente**: [Nome]
**Data richiesta**: [YYYY-MM-DD]
**Tipo change**: [Standard / Normal / Emergency]

## Descrizione
[Cosa si vuole cambiare e perché]

## Impatto
- Servizi affetti: [lista]
- Utenti affetti: [numero/percentuale]
- Downtime previsto: [durata]
- Rischio stimato: [Basso / Medio / Alto / Critico]

## Piano di implementazione
1. [Step 1]
2. [Step 2]
3. [Step n]

## Piano di rollback
1. [Step rollback 1]
2. [Step rollback n]
- Tempo stimato rollback: [durata]

## Test plan
- [ ] Testato in ambiente staging
- [ ] Verificato backup pre-change
- [ ] Comunicato a utenti affetti

## Approvazione
- Change Authority: [Nome] — [Approvato/Rifiutato] — [Data]
- Note: [eventuali condizioni]
```

**5. Knowledge Management — Documentare per Non Ripetere**

Una Knowledge Base efficace è il moltiplicatore di forza del team IT. Un articolo KB ben scritto permette a un junior di risolvere un problema che altrimenti richiederebbe un senior. Trasforma il know-how individuale in capacità organizzativa.

Struttura KB raccomandata:
- **Troubleshooting articles**: sintomo → diagnosi → soluzione step-by-step
- **How-to guides**: procedure operative standard (onboarding, backup restore, VPN setup)
- **FAQ**: domande ricorrenti con risposta
- **Architecture docs**: diagrammi e descrizioni dei servizi
- **Runbook**: procedure di emergenza per incident noti

KPI Knowledge Management:
- Articoli totali attivi
- % ticket risolti referenziando un articolo KB
- Articoli più consultati (top 10)
- Articoli senza accesso >12 mesi (candidati per archiviazione)
- Feedback utente (utile / non utile)

### NIS2 e Compliance: Impatto sulle Practices ITIL 4

La Direttiva NIS2 (UE 2022/2555), applicabile dal 18 ottobre 2024, impone obblighi significativi a molte organizzazioni italiane (non solo infrastrutture critiche). Le practices ITIL 4 si mappano direttamente sui requisiti NIS2:

| Requisito NIS2 | Practice ITIL 4 | Azione concreta |
|---|---|---|
| Art. 21(2)(a) — Politiche di analisi dei rischi e sicurezza sistemi informativi | Risk Management, Information Security Management | Risk register, assessment annuale |
| Art. 21(2)(b) — Gestione degli incidenti | Incident Management, Service Desk | Processo incident con severità, escalation, reporting |
| Art. 21(2)(c) — Continuità operativa e gestione delle crisi | Service Continuity Management | BCP/DRP documentati e testati |
| Art. 21(2)(d) — Sicurezza della catena di approvvigionamento | Supplier Management | SLA fornitori con clausole sicurezza, audit |
| Art. 21(2)(e) — Sicurezza nell'acquisizione, sviluppo e manutenzione | Software Development, Change Enablement | SDLC sicuro, code review, patch management |
| Art. 21(2)(f) — Valutazione efficacia misure | Measurement and Reporting | KPI sicurezza, audit periodici |
| Art. 21(2)(g) — Pratiche base di igiene informatica e formazione | Workforce and Talent Management, Knowledge Management | Formazione security, phishing awareness |
| Art. 21(2)(h) — Crittografia | Information Security Management | Encryption at rest e in transit |
| Art. 21(2)(i) — Risorse umane, accesso e asset | ITAM, Service Configuration Management | CMDB, access management, HR onboarding/offboarding |
| Art. 21(2)(j) — MFA e comunicazioni sicure | Information Security Management | MFA su tutti gli accessi, VPN, encrypted email |

### Analisi Costi Implementazione ITIL 4

**Costi per PMI 50 dipendenti, team IT 2 persone:**

| Voce | Opzione Budget | Opzione Standard | Opzione Enterprise |
|---|---|---|---|
| ITSM Platform | GLPI free | Freshservice €228/anno (2 agent × €19 × 12) | Jira SM €1.200/anno |
| CMDB | GLPI integrato | i-doit Community free | Lansweeper €1.800/anno |
| Monitoring | Zabbix free | PRTG 500 sensori €1.800/anno | Datadog ~€3.600/anno |
| Knowledge Base | BookStack free | Confluence €660/anno | Notion €1.800/anno |
| Formazione ITIL | YouTube + libri €200 | ITIL Foundation exam €395/persona | Foundation + specialist €2.500/persona |
| Consulenza setup | Self-service | 5gg consulente €3.000 | 15gg consulente €9.000 |
| **Totale anno 1** | **~€200** | **~€6.000** | **~€20.000** |

ROI atteso: riduzione MTTR 40-50%, riduzione incident ricorrenti 30%, risparmio tempo IT 20-30% (meno firefighting, più struttura). Per PMI con costo orario IT €60, un risparmio del 25% su 2 FTE = 2 × 1.760h × 25% × €60 = €52.800/anno.

---

## Configurazione e Implementazione

### Mappatura ITIL 4 sulla realtà PMI italiana

Una PMI italiana 10-200 dipendenti con team IT di 1-3 persone non può adottare 34 practices. Va fatta una selezione brutale. Ecco la mia mappatura proposta su tre livelli.

**Livello 1 — Adozione immediata (mese 1-3)**

Queste practices sono indispensabili anche nella PMI più piccola. Senza di esse l'IT funziona per puro caso.

| Practice | Forma minima accettabile |
|----------|-------------------------|
| Service Desk | Casella support@ + ticketing strutturato (anche solo GLPI free) |
| Incident Management | Workflow con priorità P1-P4, SLA basici, escalation |
| Service Request Management | Catalogo richieste standard (5-10 voci: nuovo utente, password, accesso, installazione SW, hardware) |
| Knowledge Management | Knowledge base interna (Confluence, BookStack, anche SharePoint) con minimo 30 articoli operativi |
| Monitoring and Event Management | Monitoraggio servizi critici (Zabbix free, PRTG 100 sensori free) |
| Information Security Management | Antivirus EDR, patch management base, MFA su tutti gli accessi |

**Livello 2 — Adozione entro 12 mesi**

Queste arrivano quando il livello 1 è stabile.

| Practice | Forma minima accettabile |
|----------|-------------------------|
| Change Enablement | Catalogo Standard Change pre-approvati + workflow Normal Change |
| IT Asset Management | Inventario hardware/software/licenze con tool (Snipe-IT) |
| Service Configuration Management | CMDB minima (servizi business + CI critici) |
| Problem Management | Registro problemi separato da incidents, RCA per P1 |
| Backup / Service Continuity | DR plan documentato, test annuale |
| Supplier Management | Registro fornitori, contratti, SLA, scadenzario |
| Service Level Management | SLA interni concordati con il business per servizi critici |

**Livello 3 — Da rimandare oltre i 12 mesi (o skippare)**

| Practice | Motivazione del rinvio |
|----------|------------------------|
| Architecture Management | Eccessivo per PMI, basta una mappa servizi |
| Portfolio Management | Inutile sotto i 200 dipendenti, basta backlog progetti |
| Service Financial Management formale | TCO grossolano sufficiente |
| Workforce and Talent Management strutturato | Skill matrix base sufficiente |
| Service Validation and Testing formale | Testing pratico in ambiente UAT |

**Confronto ITIL vs framework affini**

| Aspetto | ITIL 4 | ISO/IEC 20000 | COBIT 2019 | DevOps/SRE |
|---------|--------|---------------|------------|-----------|
| Natura | Framework di best practice | Standard certificabile | Framework governance | Cultura + practices |
| Scope | Service Management | Service Management | IT Governance | Software delivery + ops |
| Certificazione | Persone (4 livelli) | Aziende | Persone | Persone (Google SRE, AWS DevOps) |
| Prescrittività | Bassa (linee guida) | Alta (requisiti) | Media (governance objectives) | Bassa |
| Adatto a | Tutte dimensioni | Enterprise certificate | Enterprise governance | Tech-driven org |
| Costo adozione PMI | Basso (free reading) | Alto (audit) | Medio | Medio |

ISO/IEC 20000 è quasi una "ITIL certificabile": l'azienda dimostra di aver implementato un Service Management System che copre i requisiti dello standard. Si va in audit, si ottiene certificato, si rinnova ogni 3 anni con sorveglianza annuale. Per una PMI italiana ha senso solo se richiesto da clienti enterprise.

COBIT 2019 si concentra su governance (quali obiettivi IT supportano gli obiettivi di business, come si misurano, chi è accountable). È complementare a ITIL: COBIT dice "cosa" governare, ITIL dice "come" gestire i servizi.

DevOps/SRE non è un framework formale ma un insieme di practices culturali (cross-functional team, automazione, blameless postmortem, error budget, SLI/SLO) emerse da Google, Netflix, Etsy. ITIL 4 ha integrato molti concetti DevOps (value streams, automazione, agile change). In pratica un team moderno applica entrambi.

### Tooling: ServiceNow, GLPI, Jira Service Management, Freshservice, OTRS, Zammad

| Tool | Tipo | Costo indicativo | Punto di forza | Quando sceglierlo |
|------|------|------------------|----------------|-------------------|
| **ServiceNow** | Enterprise SaaS | da €100/user/mese, totali 6+ cifre/anno | ITSM completo, ITAM, CMDB, AIOps, GRC | Enterprise 500+ dipendenti, budget elevato |
| **GLPI** | Open source self-hosted | Gratuito (LAMP) + opzionale GLPI Network paid | Modulare, italiano-friendly, popolare in EU | PMI, scuole, MSP, P.A. |
| **Jira Service Management** | SaaS Atlassian | da €17/agent/mese (Standard), €50/agent (Premium) | Integrazione con Jira Software, automation engine | Org già Atlassian-centric |
| **Freshservice** | SaaS | da €19/agent/mese (Starter) | UX moderna, AI features, time-to-value rapido | PMI/midmarket, no IT specializzato |
| **OTRS** | Open source / Enterprise | Free Community Edition (limitata), enterprise paid | Robust ticketing, customizzabile | Enterprise tradizionali, settore pubblico tedesco |
| **Zammad** | Open source self-hosted | Gratuito + Hosted da €5/agent/mese | UX moderna open source | PMI tech-friendly, MSP |
| **i-doit** | Open source CMDB-focused | Free CE, Pro paid | CMDB pura, ITAM | Quando il tool ITSM fornisce ticketing ma non CMDB |
| **iTop** | Open source | Free + extensions | ITIL coverage, multi-tenant | MSP, contesti multi-cliente |
| **Spiceworks** | Free SaaS/on-prem | Gratuito (ad-supported) | Comunità, semplicità | Micro PMI, lab, no budget |

Per una PMI italiana 50 dipendenti la scelta tipica è tra **GLPI** (se c'è competenza Linux/LAMP e si vuole self-host) e **Freshservice** (se si preferisce SaaS chiavi-in-mano). Jira Service Management ha senso se l'azienda usa già Jira Software. ServiceNow è sovradimensionato.

### Piano di adozione 90 giorni per PMI 50 dipendenti

Scenario di partenza: PMI 50 dipendenti, IT team 2 persone (1 IT Manager + 1 sistemista), ticketing via email (support@), nessuna CMDB, nessun monitoring strutturato, backup eseguiti manualmente, patch applicate "quando ci si pensa", 1 incidente critico al mese che paralizza per ore.

Stack proposto: **GLPI** (ticketing + asset + CMDB minima), **Zabbix** (monitoring), **BookStack** (knowledge base), **Ansible** (automazione patch), tutti su 1 VM Ubuntu Server 22.04 LTS da 8 vCPU / 16 GB RAM / 200 GB SSD.

**Settimane 1-2 — Setup infrastruttura**

```bash
# Setup VM Ubuntu 22.04 LTS, hardening base
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y ufw fail2ban unattended-upgrades

# UFW: deny all in, allow ssh + 80/443 da subnet aziendale
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 22 proto tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Installazione GLPI (LAMP stack)
sudo apt install -y apache2 mariadb-server php php-mysql php-gd php-xml \
  php-curl php-intl php-zip php-mbstring php-ldap php-bz2 php-imap

# MariaDB hardening
sudo mysql_secure_installation

# Database GLPI
sudo mysql -u root -p <<EOF
CREATE DATABASE glpidb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'glpiuser'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON glpidb.* TO 'glpiuser'@'localhost';
FLUSH PRIVILEGES;
EOF

# Download GLPI 10.x
cd /var/www/html
sudo wget https://github.com/glpi-project/glpi/releases/download/10.0.10/glpi-10.0.10.tgz
sudo tar -xzf glpi-10.0.10.tgz
sudo chown -R www-data:www-data glpi/

# Apache vhost + Let's Encrypt
sudo a2enmod ssl rewrite
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d glpi.azienda.local
```

Procedere con installazione web GLPI: navigare https://glpi.azienda.local, accettare licenza, fornire credenziali DB, creare super-admin, eliminare account default (glpi/glpi, tech/tech, normal/normal, post-only/postonly che sono backdoor di sviluppo).

**Settimane 3-4 — Configurazione GLPI base**

Configurazione minima per partire:

1. **Entità unica** (no multi-tenant per PMI singola)
2. **Categorie ticket**: Hardware, Software, Rete, Account/Accessi, Stampa, Telefonia, Generale
3. **Tipi richieste**: Incident, Request, Change
4. **Priorità con matrice impatto×urgenza**: P1/P2/P3/P4/P5
5. **SLA per priorità**:
   - P1: risposta 15min, risoluzione 2h, 24/7
   - P2: risposta 30min, risoluzione 4h business
   - P3: risposta 2h, risoluzione 8h business
   - P4: risposta 4h, risoluzione 24h business
6. **LDAP/AD integration**: utenti sincronizzati da Active Directory
7. **Email collector**: support@azienda.it polled via IMAP, ticket creati automaticamente
8. **Notifiche**: email automatiche su apertura/aggiornamento/chiusura ticket

**Settimane 5-6 — Asset inventory**

Installazione plugin **FusionInventory** per discovery automatica:

```bash
cd /var/www/html/glpi/plugins
sudo wget https://github.com/fusioninventory/fusioninventory-for-glpi/releases/download/glpi10.0.6%2B1.1/fusioninventory-10.0.6+1.1.tar.bz2
sudo tar -xjf fusioninventory-10.0.6+1.1.tar.bz2
sudo chown -R www-data:www-data fusioninventory/
```

Attivare plugin in GLPI > Setup > Plugins > Install/Activate.

Deploy agent FusionInventory su tutti i Windows via GPO (MSI silenziato) e su Linux via Ansible:

```yaml
# fusion-inventory-agent.yml
- hosts: linux_servers
  become: yes
  tasks:
    - name: Install FusionInventory Agent
      apt:
        name: fusioninventory-agent
        state: present
        update_cache: yes
    - name: Configure agent server
      lineinfile:
        path: /etc/fusioninventory/agent.cfg
        regexp: '^server='
        line: 'server=https://glpi.azienda.local/plugins/fusioninventory/'
    - name: Enable and start service
      systemd:
        name: fusioninventory-agent
        enabled: yes
        state: started
```

Programmare scansione SNMP rete per scoprire switch, AP, stampanti.

**Settimane 7-8 — Service Catalogue & Knowledge Base**

In GLPI: creare catalogo servizi standard (Service Request templates):

- Nuovo utente (form: nome, cognome, manager, dipartimento, data inizio, copia da utente esistente)
- Reset password
- Accesso a cartella di rete (form: utente, percorso, permessi R/RW, owner approvante)
- Installazione software approvato (lista whitelist)
- Richiesta hardware (laptop standard, monitor, dock, headset)
- Onboarding/offboarding

Workflow di approvazione: per accessi → manager utente; per hardware oltre 500€ → IT Manager + manager utente.

Setup BookStack per Knowledge Base:

```bash
# Docker compose minimal
mkdir -p /opt/bookstack && cd /opt/bookstack
cat > docker-compose.yml <<EOF
version: '3'
services:
  bookstack:
    image: lscr.io/linuxserver/bookstack:latest
    container_name: bookstack
    environment:
      - APP_URL=https://kb.azienda.local
      - DB_HOST=bookstack_db
      - DB_USER=bookstack
      - DB_PASS=STRONG_PASS
      - DB_DATABASE=bookstackapp
    volumes:
      - ./config:/config
    ports:
      - 6875:80
    restart: unless-stopped
  bookstack_db:
    image: lscr.io/linuxserver/mariadb:latest
    container_name: bookstack_db
    environment:
      - MYSQL_ROOT_PASSWORD=STRONG_ROOT_PASS
      - MYSQL_DATABASE=bookstackapp
      - MYSQL_USER=bookstack
      - MYSQL_PASSWORD=STRONG_PASS
    volumes:
      - ./db:/config
    restart: unless-stopped
EOF
docker compose up -d
```

Popolare KB con almeno 30 articoli base: procedure backup, restore, reset password AD, sblocco utente, installazione software standard, troubleshooting stampa, accesso VPN, recupero file da backup, ecc.

**Settimane 9-10 — Monitoring**

Setup Zabbix Server + Frontend:

```bash
# Zabbix 6.4 LTS su Ubuntu 22.04
wget https://repo.zabbix.com/zabbix/6.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.4-1+ubuntu22.04_all.deb
sudo dpkg -i zabbix-release_6.4-1+ubuntu22.04_all.deb
sudo apt update
sudo apt install -y zabbix-server-mysql zabbix-frontend-php zabbix-apache-conf \
  zabbix-sql-scripts zabbix-agent

# Database
sudo mysql -u root -p <<EOF
CREATE DATABASE zabbix CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
CREATE USER 'zabbix'@'localhost' IDENTIFIED BY 'STRONG_PASS';
GRANT ALL PRIVILEGES ON zabbix.* TO 'zabbix'@'localhost';
SET GLOBAL log_bin_trust_function_creators = 1;
FLUSH PRIVILEGES;
EOF

# Schema
zcat /usr/share/zabbix-sql-scripts/mysql/server.sql.gz | mysql --default-character-set=utf8mb4 -u zabbix -p zabbix

# Configurazione Zabbix Server
sudo sed -i 's/# DBPassword=/DBPassword=STRONG_PASS/' /etc/zabbix/zabbix_server.conf
sudo systemctl restart zabbix-server zabbix-agent apache2
sudo systemctl enable zabbix-server zabbix-agent apache2
```

Deploy Zabbix Agent su tutti i server via Ansible. Template Linux/Windows applicati. Trigger configurati per CPU > 90% per 5min, RAM > 95%, disk > 85%, servizi critici down (AD, file server, DBMS, gestionale).

Integrazione Zabbix → GLPI: webhook su trigger problem state che apre automaticamente ticket in GLPI con severity mappata.

**Settimane 11-12 — Change Enablement minimo + Patch Management**

Definire catalogo Standard Change pre-approvati:

| Standard Change | Frequenza | Owner | Window |
|-----------------|-----------|-------|--------|
| Patch Tuesday Windows servers | Mensile, 2° martedì + 1 settimana | Sistemista | Sabato 22:00-02:00 |
| Patch Linux servers | Mensile, 1° sabato | Sistemista | 22:00-02:00 |
| Backup retention rotation | Settimanale | Sistemista | Domenica notte |
| Antivirus signature update | Giornaliero automatico | Automazione | Continuo |
| Riavvio servizi non critici | Mensile | Sistemista | Sabato mattina |

Ogni Standard Change: documentato in KB, change log automatico in GLPI, rollback documentato.

Normal Change: workflow GLPI con approvazione IT Manager, RFC compilato (descrizione, motivazione, impatto, rollback, test plan, window).

Setup automazione patch via Ansible (vedi documento `14-patch-management-enterprise.md`).

**Risultati attesi a 90 giorni**

- 100% ticket tracciati (vs email caos)
- Backlog tickets visibile, priorità chiare
- 90% asset inventariati con FusionInventory
- 30+ articoli KB attivi, 20% ticket risolti via self-service
- Monitoring attivo su 100% server critici, alert in 5min
- Patch applicate in modo strutturato e tracciato
- Riduzione MTTR del 40-50% su incidenti tipici
- IT in grado di rispondere a domanda "perché è giù?" in minuti, non ore

---

## Best Practices

**1. Iniziare dal Service Desk, non dalla CMDB**
La CMDB è seducente ma richiede tempo e disciplina. Senza Service Desk e Incident Management funzionanti la CMDB è un esercizio teorico. Prima si stabilizza il flusso operativo, poi si modella la realtà.

**2. Misurare prima di migliorare**
Senza baseline non sai se stai migliorando. Misura MTTR, ticket count, % SLA breach prima di introdurre modifiche. Ripeti misurazioni a 30/60/90 giorni post-cambio.

**3. Resistere alla tentazione del CAB rigido**
Il CAB settimanale di due ore con 30 partecipanti è il bersaglio facile delle critiche a ITIL. Standard Change pre-approvati + Change Authority delegate sono più moderni e producono meno attrito.

**4. Knowledge base come prodotto, non come archivio**
Una KB invecchia se nessuno la cura. Definire un owner per articolo, data di review obbligatoria (ogni 6-12 mesi), processo di feedback (utente vota utilità). Articoli senza accessi negli ultimi 12 mesi: archiviare.

**5. SLA realistici, non aspirational**
SLA con tempi di risoluzione P1 di 30 minuti quando l'IT team è di 2 persone in single-shift sono aspirational. Definire SLA che il team può rispettare 95% delle volte. Meglio SLA P1 = 4h al 95% che P1 = 1h al 50%.

**6. Roles vs persone**
In una PMI la stessa persona ricopre più ruoli (Incident Manager + Problem Manager + Change Manager + Service Desk Tier 2). È normale, basta che i ruoli siano dichiarati. Quando si scala, si separano.

**7. Continual Improvement Register pubblico**
Non lasciare il miglioramento alla buona volontà. Un registro CIR con voci, owner, scadenze, status visibile a tutto il team forza la disciplina.

**8. Postmortem blameless dopo P1**
Ogni incidente P1 deve generare postmortem entro 5 giorni lavorativi. Focus su sistema, non su persone. Output: timeline, root cause, contributing factors, action items con owner e deadline.

**9. Service Catalogue = contratto con il business**
Pubblicare il catalogo servizi (anche solo internamente) forza chiarezza su cosa l'IT eroga, con quali SLA, quali escalation. Riduce drasticamente le richieste fuori scope.

**10. Automazione laser-focused**
Non automatizzare per principio. Misurare quale attività occupa più tempo umano ripetitivo, automatizzare quella per prima. L'80/20 si applica brutalmente: 20% delle attività occupa 80% del tempo.

**11. RACI matrix per ogni practice**
In una PMI i ruoli sono pochi e le persone ricoprono ruoli multipli. Una matrice RACI chiarisce chi è Responsible, Accountable, Consulted, Informed per ogni processo. Esempio minimo:

| Attività | IT Manager | Sistemista | Help Desk | Manager Dipart. |
|---|---|---|---|---|
| Apertura ticket | I | I | R | I |
| Triage P1 | A | R | I | I |
| Approvazione Normal Change | A | R | I | C |
| Postmortem P1 | A | R | C | I |
| Budget IT annuale | R | C | I | C |
| Acquisto hardware | A | C | I | C |

R = fa il lavoro, A = approva/è accountable, C = consultato, I = informato.

**12. Feedback loop strutturato con il business**
L'IT deve ricevere feedback dal business regolarmente, non solo quando qualcosa si rompe. Pratiche concrete:
- Survey CSAT post-ticket (anche 1 domanda: "Ti sei sentito supportato? 1-5")
- Review trimestrale IT-Management (30 min): cosa funziona, cosa no, priorità prossimo trimestre
- Business stakeholder in postmortem P1 (per impatto utente)
- Service Review semestrale: SLA rispettati? servizi adeguati? nuove esigenze?

**13. Shadow IT: riconoscerlo e gestirlo**
In ogni PMI italiana esiste shadow IT: fogli Excel per tracking, Dropbox personale per condividere file, WhatsApp per comunicare con clienti, software installato senza approvazione. Non combatterlo con divieti (non funziona). Comprenderlo: perché l'utente usa Dropbox invece del fileserver? Forse il fileserver è lento, o l'accesso VPN è complicato. Risolvere la causa e offrire alternativa migliore. Tracciare shadow IT con discovery tools (Lansweeper, GLPI agent).

**14. Documentare le decisioni, non solo i processi**
Un processo ITIL documentato spiega "come si fa". Ma le decisioni architetturali ("perché abbiamo scelto Zabbix invece di PRTG", "perché lo SLA P1 è 4 ore e non 2") sono altrettanto importanti. Usare ADR (Architecture Decision Records) o semplicemente un documento "Decisioni IT" nella KB con data, decisione, razionale, alternativa scartata.

**15. Celebrare i successi**
L'IT è un ruolo ingrato: quando funziona tutto nessuno lo nota, quando si rompe tutti si lamentano. Celebrare i successi attivamente: "Questo mese MTTR medio 45 minuti, record dell'anno". "Zero incidenti P1 per 3 mesi consecutivi". "La KB ha risolto 200 ticket senza intervento umano". Comunicare al management e al team.

### Checklist di Implementazione ITIL 4 — Quick Start

Checklist operativa per i primi 90 giorni:

**Settimana 1-2: Setup Tecnico**
- [ ] VM per ITSM tool provisionata e hardenizzata
- [ ] GLPI (o alternativa) installato e configurato
- [ ] SSL/TLS attivo su tutti i portali web
- [ ] Account admin creati, account di default eliminati
- [ ] Email collector configurato (support@azienda.it)
- [ ] Integrazione LDAP/AD per autenticazione utenti

**Settimana 3-4: Configurazione Processo**
- [ ] Categorie ticket definite (5-8 categorie di primo livello)
- [ ] Matrice priorità (Impatto × Urgenza → P1/P2/P3/P4) configurata
- [ ] SLA per ogni priorità definiti e configurati nel tool
- [ ] Template notifiche email personalizzati
- [ ] Workflow approvazione per richieste > soglia costo
- [ ] Ruoli e permessi assegnati

**Settimana 5-6: Asset & Discovery**
- [ ] Agent discovery installato su tutti gli endpoint (FusionInventory/GLPI Agent)
- [ ] Prima scansione rete completata
- [ ] Asset registrati con campi obbligatori (tag, modello, S/N, ubicazione, owner)
- [ ] Licenze software censite (almeno Windows, Office, antivirus)
- [ ] Contratti vendor registrati con date scadenza

**Settimana 7-8: Knowledge & Monitoring**
- [ ] Knowledge Base tool installato (BookStack/Confluence)
- [ ] 10 articoli fondamentali pubblicati
- [ ] Portale self-service attivo per utenti
- [ ] Monitoring installato (Zabbix/PRTG)
- [ ] Agent monitoring su tutti i server critici
- [ ] Alert configurati per: CPU, RAM, disco, servizi critici
- [ ] Integrazione monitoring → ticketing (alert → auto-ticket)

**Settimana 9-10: Change & Communication**
- [ ] Catalogo Standard Change definito (8-10 voci)
- [ ] Workflow Normal Change configurato nel tool
- [ ] Template RFC disponibile
- [ ] Comunicazione a tutti gli utenti: "da oggi IT via portale"
- [ ] Training utenti (30 min, anche in video)
- [ ] Canale #it-status per comunicazioni proattive

**Settimana 11-12: Review & Stabilization**
- [ ] Primo report SLA generato e presentato alla direzione
- [ ] Review delle prime 8 settimane: cosa funziona, cosa no
- [ ] Aggiustamenti SLA basati su dati reali
- [ ] Piano per i prossimi 6 mesi definito
- [ ] CIR iniziato con almeno 3 voci

### Template Report Mensile IT per Direzione

```markdown
# Report IT Mensile — [Mese Anno]

## Executive Summary
[2-3 frasi: highlights del mese, trend, raccomandazioni]

## Metriche Operative

| Metrica | Questo mese | Mese precedente | Target | Trend |
|---|---|---|---|---|
| Ticket totali | 187 | 165 | — | ↑ 13% |
| MTTR P1/P2 | 1h 15min | 1h 45min | <2h | ✅ ↓ 29% |
| SLA breach rate | 8% | 12% | <10% | ✅ ↓ |
| FCR | 62% | 58% | >65% | ↗ migliorando |
| CSAT | 4.0/5.0 | 3.8/5.0 | >4.0 | ✅ |
| Self-service rate | 28% | 22% | >30% | ↗ |

## Incidenti Rilevanti
- [Data]: [Descrizione breve]. MTTR: [durata]. Postmortem: [link]
- ...

## Cambiamenti Eseguiti
- Standard Change: [N] (tutti con esito positivo)
- Normal Change: [N] (di cui [M] con esito positivo)
- Emergency Change: [N]

## Progetti in Corso
- [Progetto 1]: [stato / % completamento]
- [Progetto 2]: [stato]

## Asset
- Nuovi asset registrati: [N]
- Asset dismessi: [N]
- Garanzie in scadenza prossimi 90gg: [N]

## Raccomandazioni
1. [Raccomandazione 1 — budget richiesto €X]
2. [Raccomandazione 2]
3. [Raccomandazione 3]
```

### Integrazione ITIL con ISO 27001

Per organizzazioni che implementano o pianificano ISO 27001, le practices ITIL si mappano direttamente sui controlli:

| Controllo ISO 27001:2022 | Practice ITIL 4 | Note |
|---|---|---|
| A.5.1 Policies for information security | Information Security Management | Policy sicurezza = input per ISM practice |
| A.5.9 Inventory of information and other assets | IT Asset Management | Asset register = output ITAM |
| A.5.23 Information security for use of cloud services | Supplier Management, Infrastructure Management | SLA cloud provider, security assessment |
| A.5.24 Information security incident management planning | Incident Management | Processo incident = parte del piano |
| A.5.26 Response to information security incidents | Incident Management | Workflow incident security |
| A.5.27 Learning from information security incidents | Problem Management + postmortem | RCA + action items |
| A.7.10 Storage media | IT Asset Management | Tracking supporti dati |
| A.7.14 Secure disposal or re-use | IT Asset Management | NIST SP 800-88, certificati distruzione |
| A.8.1 User endpoint devices | Service Request Management, ITAM | Onboarding/offboarding, MDM |
| A.8.8 Management of technical vulnerabilities | Change Enablement (patch), Monitoring | Patch management, vulnerability scanning |
| A.8.9 Configuration management | Service Configuration Management | CMDB, baseline configuration |
| A.8.16 Monitoring activities | Monitoring and Event Management | SIEM, log management |

Questa mappatura permette di usare l'implementazione ITIL come fondamento per l'audit ISO 27001, riducendo significativamente il lavoro di preparazione.

### Metriche DORA e ITIL 4

Le 4 metriche DORA (DevOps Research and Assessment) si integrano naturalmente con le practices ITIL:

| Metrica DORA | Definizione | Practice ITIL Correlata |
|---|---|---|
| **Deployment Frequency** | Quanto spesso si deploya in produzione | Deployment Management, Release Management |
| **Lead Time for Changes** | Tempo da commit a produzione | Change Enablement, Deployment Management |
| **Change Failure Rate** | % deployment che causano incident | Change Enablement, Incident Management |
| **Mean Time to Restore** | Tempo per ripristinare il servizio dopo failure | Incident Management |

Target per performance level:

| Metrica | Elite | High | Medium | Low |
|---|---|---|---|---|
| Deployment Frequency | On-demand | 1/giorno - 1/settimana | 1/settimana - 1/mese | 1/mese - 1/6 mesi |
| Lead Time for Changes | <1 giorno | 1 giorno - 1 settimana | 1 settimana - 1 mese | 1-6 mesi |
| Change Failure Rate | 0-15% | 16-30% | 31-45% | >45% |
| MTTR | <1 ora | <1 giorno | <1 settimana | >6 mesi |

Una PMI italiana tipica si colloca tra Medium e Low. L'adozione di ITIL 4 con automazione mira a portarla a High entro 12-18 mesi.

---

## Troubleshooting

### Problemi Organizzativi

**Problema 1: gli utenti continuano a scrivere direttamente al sistemista invece di aprire ticket**

Cause: nessuna policy formale, paura di lentezza ticketing, abitudine, mancanza di vantaggio percepito dall'utente. Rimedio articolato:
1. Il sistemista DEVE redirezionare gentilmente: "ti chiedo di aprire ticket per tracciare — così non rischio di dimenticarmene"
2. Policy comunicata da CdA/management (non dall'IT — l'autorità deve venire dal business)
3. KPI sul team IT include "% interventi tracciati come ticket" (target 95%+)
4. Rendere il ticketing FACILE: form breve (3-4 campi), email auto-ticket, app mobile se disponibile
5. Rendere il ticketing VANTAGGIOSO per l'utente: visibilità sullo stato, SLA trasparente, storico
6. Dopo 60 giorni il comportamento si stabilizza se la direzione sostiene la policy
7. Mai ignorare un utente che apre ticket — la prima esperienza negativa uccide l'adozione

**Problema: il tasso di breach SLA è altissimo nei primi mesi**

Cause: SLA aspirational, non realistici. Rimedio: rivedere SLA dopo 90 giorni con dati reali, ridefinirli su livelli che il team può rispettare con qualche margine.

**Problema: la CMDB è popolata ma non riflette la realtà (drift)**

Cause: aggiornamento manuale, scoperta non automatizzata. Rimedio: scoperta automatica (FusionInventory, OCS, vendor agent), processo di certificazione CI per owner ogni 90gg, alerting su discrepanze tra discovery e CMDB.

**Problema: il CAB diventa un collo di bottiglia che rallenta i cambiamenti**

Cause: CAB rigido v3, troppi tipi di change processati come Normal. Rimedio: ridefinire i Standard Change (catalogo ampio), delegare Change Authority per ambito, riservare CAB solo a Normal Change ad alto impatto.

**Problema: la knowledge base è ricca ma nessuno la usa**

Cause: KB non integrata nel workflow ticketing, articoli obsoleti, search scadente. Rimedio: in fase di apertura ticket, suggerire articoli KB correlati; agent forzato a indicare articoli usati per risolvere; review periodica obsolescenza; integrare KB dentro il portale self-service utenti.

**Problema: gli stakeholder business non capiscono ITIL e lo percepiscono come burocrazia**

Cause: linguaggio tecnico, mancanza di traduzione in business value. Rimedio: parlare in termini business (uptime, costi evitati, tempo risparmiato), non in termini ITIL. "Abbiamo ridotto MTTR del 40%" diventa "i guasti durano la metà di prima, risparmio stimato X €/anno".

**Problema: introdotto ITSM tool ma il team continua a usare email e Excel**

Cause: tool troppo complesso, formazione insufficiente, vantaggio percepito basso. Rimedio: semplificare configurazione (rimuovere campi inutili), formazione hands-on, cerimonia di "morte ufficiale" del tool legacy con data di cutoff, leadership da esempio.

**Problema 8: troppi alert dal monitoring, alert fatigue**

Cause: threshold troppo bassi, troppi alert non actionable, mancanza di severità differenziata, correlazione assente. Rimedio articolato:
1. Audit completo alert: per ogni alert, chiedere "qual è l'azione che il tecnico deve fare quando riceve questo alert?" Se la risposta è "nessuna" o "verificare", l'alert va eliminato o degradato a informational.
2. Ridefinire threshold su baseline reale — non usare i default del vendor (spesso troppo conservativi).
3. Separare canali notifica: alert critical → PagerDuty/telefono, alert warning → email, alert info → solo dashboard.
4. Aggregare alert correlati: se 10 servizi sullo stesso server generano alert quando il server va giù, un'unica notifica "server down" è sufficiente.
5. Rule of thumb: un on-call non dovrebbe ricevere più di 5-10 alert actionable per turno. Sopra questo livello, c'è un problema di tuning.
6. Review trimestrale: report alert volume, false positive rate, alert senza azione. Target: signal-to-noise ratio >80%.

### Problemi Tecnici

**Problema 9: GLPI lento dopo 12 mesi di utilizzo**

Cause: database MySQL/MariaDB non ottimizzato, tabella dei log eventi cresciuta senza manutenzione, assenza di indici ottimizzati. Rimedio: scheduled maintenance MySQL (OPTIMIZE TABLE su tabelle principali), configurare log rotation in GLPI (Setup > General > Logs, retention 90 giorni), aumentare `innodb_buffer_pool_size` a 50-70% della RAM del server, aggiungere cron per pulizia sessioni scadute.

**Problema 10: integrazione LDAP/AD con GLPI che si desincronizza**

Cause: cambio password account LDAP bind, modifica OU structure in AD, timeout di connessione. Rimedio: verificare credenziali LDAP bind in GLPI > Setup > Authentication > LDAP, testare connessione con `ldapsearch` dalla shell del server GLPI, verificare firewall tra server GLPI e Domain Controller (porta 389/TCP o 636/TCP per LDAPS), schedulare sync automatico via cron ogni 6 ore.

**Problema 11: la CMDB diverge dalla realtà dopo 6 mesi**

Cause: onboarding asset senza registrazione, dismissione senza cancellazione, cambi configurazione non tracciati. Rimedio: processo di riconciliazione trimestrale (discovery automatico con FusionInventory + verifica manuale), policy che ogni acquisto hardware DEVE passare per registrazione CMDB prima del deploy, audit fisico annuale (conteggio asset vs CMDB), report mensile "asset scoperti da discovery ma non in CMDB" con owner per riconciliazione.

**Problema 12: il Change Enablement viene bypassato per "urgenza"**

Cause: processo percepito come troppo lento, mancanza di Emergency Change path chiaro, cultura del "faccio prima io". Rimedio: definire chiaramente il percorso Emergency Change (approvazione verbale IC + documentazione retroattiva entro 24h), ridurre lead time Normal Change (delegare Change Authority per ambito), espandere catalogo Standard Change pre-approvati (ogni change che si ripete >3 volte/anno diventa Standard Change candidato), tracking dei bypass come KPI di processo.

**Problema 13: la Knowledge Base contiene articoli obsoleti che causano errori**

Cause: nessun processo di review periodico, nessun owner per articolo, nessun feedback loop dagli utenti. Rimedio: assegnare un owner per articolo, definire scadenza review (ogni 6-12 mesi), integrare feedback nel workflow ticket ("Hai usato un articolo KB? Era utile/aggiornato?"), archiviare automaticamente articoli senza accesso per 12 mesi, marcare visibilmente la data di ultimo aggiornamento.

**Problema 14: i report SLA mostrano performance pessime ma il team IT lavora tantissimo**

Cause: SLA definiti male (troppo ambiziosi), prioritizzazione errata (molti P3 trattati come P1), tempo speso su attività non tracciate. Rimedio: ridefinire SLA su livelli raggiungibili (basati su dati reali dei primi 3 mesi), forzare corretta categorizzazione priorità (matrice impatto × urgenza), tracciare TUTTE le attività IT come ticket (anche quelle proattive: patch, monitoring, manutenzione), report che distingua tempo su incident vs request vs progetto.

**Problema 15: il Continual Improvement Register è vuoto dopo 6 mesi**

Cause: nessuno ha tempo, CIR non è parte del workflow quotidiano, mancanza di incentivo. Rimedio: integrare CIR nel postmortem workflow (ogni postmortem genera almeno 1 voce CIR), dedicare 30 minuti alla settimana per revisione CIR (anche solo 1 persona), piccoli quick win prima di grandi progetti (dimostrare che il CIR produce risultati), celebrare miglioramenti completati.

### Problemi di Processo

**Problema 16: il catalogo servizi è completo ma i ticket arrivano comunque categorizzati male**

Cause: catalogo troppo complesso, naming poco intuitivo per utenti non-IT, mancanza di formazione. Rimedio: semplificare le categorie visibili all'utente (max 8-10 categorie di primo livello), usare linguaggio business non tecnico ("Il mio computer è lento" invece di "Performance degradation endpoint"), aggiungere wizard guidato nel portale self-service, analizzare i ticket miscategorizzati e ridisegnare le categorie basandosi sull'uso reale.

**Problema 17: il Service Desk è oberato e i tempi di risposta peggiorano**

Cause: crescita organica senza adeguamento risorse, mancanza di self-service, troppo knowledge tacita (tutto passa dal SD). Rimedio: analizzare top 10 ticket types per volume e automatizzare i primi 3 (reset password self-service, FAQ su portale, form pre-compilati per richieste standard), implementare chatbot per triage iniziale (anche semplice: Freshservice, GLPI con plugin), delegare L1 a utenti power-user per dipartimento, valutare outsourcing L1 parziale.

**Problema 18: l'adozione ITIL è percepita come "fare carta" senza valore pratico**

Cause: implementazione troppo burocratica, linguaggio ITIL non tradotto in business value, troppi campi obbligatori nei form. Rimedio articolato:
1. Misurare PRIMA di iniziare (baseline): MTTR, ticket count, uptime, tempo su firefighting
2. Misurare DOPO ogni iterazione (30/60/90 giorni) e comunicare i delta in termini business
3. "I guasti durano la metà di prima" è più efficace di "MTTR ridotto del 50%"
4. "Risparmiamo €40.000/anno in downtime evitato" è più efficace di "SLA compliance al 95%"
5. Eliminare ogni campo/step che non ha giustificazione misurabile — test: "Se rimuovo questo campo, perdo informazione che mi serve per prendere una decisione?"
6. Coinvolgere il business nella definizione di cosa è utile: survey, feedback loop
7. Citare ITIL solo internamente — verso il business parlare di risultati, costi, rischi
8. Guiding Principle #6: Keep It Simple and Practical

**Problema 19: turnover del team IT causa perdita di knowledge**

Cause: documentazione insufficiente, processi non formalizzati, bus factor basso. Rimedio: Knowledge Management come practice prioritaria — ogni procedura documentata nella KB prima che diventi necessaria. Cross-training: ogni task critico deve poter essere eseguito da almeno 2 persone. Onboarding strutturato per nuovi assunti IT: 10 giorni di formazione su processi, tool, infrastruttura con checklist. ADR (Architecture Decision Records) per documentare il "perché" delle scelte, non solo il "come".

**Problema 20: il tool ITSM non si integra con il resto dello stack**

Cause: tool scelto senza valutare requisiti di integrazione, API assenti o scadenti, mancanza di competenza di integrazione. Rimedio: valutare API REST come requisito non negoziabile nella scelta del tool. Usare n8n o Zapier come middleware di integrazione per connettere sistemi senza sviluppo custom. Integrazioni prioritarie: monitoring → auto-ticket, AD → user sync, asset discovery → CMDB, email → ticket, chat (Slack/Teams) → ticket. Test l'integrazione PRIMA di acquistare il tool.

### FAQ — Domande Frequenti

**1. ITIL 4 è obbligatorio per le aziende italiane?**

No. ITIL è un framework di best practice, non un requisito normativo. Tuttavia, la certificazione ISO/IEC 20000 (che si basa su concetti ITIL) può essere richiesta da clienti enterprise come requisito contrattuale. Inoltre, NIS2 richiede "misure appropriate e proporzionate" che si mappano naturalmente sulle practices ITIL. Non devi adottare ITIL formalmente, ma devi avere processi equivalenti.

**2. Quante practices ITIL dovrebbe adottare una PMI con 2 persone IT?**

Da 6 a 8 nel primo anno: Service Desk, Incident Management, Service Request Management, Knowledge Management, Monitoring, Information Security Management. Aggiungere Change Enablement e ITAM nei mesi 6-12. Le altre possono aspettare o essere ignorate. Non tentare di adottare tutte e 34: è una garanzia di fallimento.

**3. GLPI è davvero sufficiente per fare ITIL 4?**

Sì, per una PMI fino a 200 dipendenti. GLPI copre ticketing, asset management, CMDB, knowledge base, SLA, catalogo servizi. Mancano: dashboard avanzate (compensabili con Grafana/Metabase), automation sofisticata (compensabile con Ansible/n8n), ITSM analytics (compensabile con query SQL + report). Il costo nullo lo rende ideale come punto di partenza.

**4. Quanto costa la certificazione ITIL 4 Foundation?**

L'esame ITIL 4 Foundation costa circa €395 (prezzo PeopleCert 2025-2026). Un corso preparatorio accreditato costa €500-€1.500 aggiuntivi. L'auto-studio è possibile con il libro ufficiale (€45-60) e risorse online gratuite. La certificazione è personale (certifichi la persona, non l'azienda). Ha validità perpetua (non scade).

**5. Qual è la differenza tra Change Management e Change Enablement?**

Il nome è cambiato da ITIL v3 a v4, e il cambio non è cosmetico. Change Management v3 era spesso implementato come gate burocratico (CAB settimanale, 47 campi obbligatori, lead time di settimane). Change Enablement v4 enfatizza rendere il cambiamento veloce E sicuro: Standard Change pre-approvati, Change Authority delegata per ambito, automazione dei controlli, CAB solo per cambiamenti ad alto rischio. L'obiettivo è abilitare, non bloccare.

**6. Come si integra ITIL 4 con DevOps?**

ITIL 4 e DevOps non sono in conflitto — anzi, ITIL 4 ha esplicitamente incorporato concetti DevOps (value streams, automazione, feedback loop, blameless postmortem). In pratica: DevOps fornisce le pratiche di delivery (CI/CD, IaC, monitoring-as-code), ITIL fornisce il framework di gestione (incident management, change enablement, service level management). Un team moderno usa entrambi senza conflitto.

**7. Come convincere il management a investire in ITIL?**

Non vendere "ITIL" — vendi i risultati: "Ridurre il tempo medio di risoluzione guasti del 40% (risparmiando €X/anno di downtime)", "Eliminare il 30% degli incidenti ricorrenti", "Passare da reactive firefighting a proactive management". Presenta un pilot di 90 giorni con metriche prima/dopo. Il management non si interessa a framework — si interessa a costi, rischi e risultati.

**8. Serve un Service Desk 24/7 per una PMI?**

Raramente. La maggior parte delle PMI italiane opera in orario business (8-18 lun-ven). Un Service Desk 24/7 richiede almeno 5 FTE (3 turni + copertura ferie/malattia). Alternativa per emergenze notturne: on-call rotation (1 persona reperibile con PagerDuty/OpsGenie), escalation automatica da monitoring per alert critici, contratto con MSP per copertura notturna/weekend.

**9. Come si misura il ROI di un programma ITIL?**

Metriche chiave: (1) MTTR prima vs dopo — riduzione tempo downtime × costo orario downtime = risparmio. (2) Incident count trend — riduzione incidenti ricorrenti × costo medio incident. (3) Tempo IT su firefighting vs proactive work — shift verso proactive libera capacità per progetti. (4) FCR Service Desk — aumento FCR riduce escalation e tempo senior engineer. (5) CSAT utenti — soddisfazione utenti correla con produttività business.

**10. ITIL è compatibile con Agile/Scrum?**

Sì. ITIL 4 è stato progettato per essere compatibile con Agile. Il principio "Progress Iteratively with Feedback" è essenzialmente Agile. Le practices ITIL possono essere implementate all'interno di sprint. Esempio: un team Scrum può includere nel proprio backlog gli action item da postmortem, i miglioramenti al monitoring, gli aggiornamenti KB. Il Product Owner collabora con il Service Owner per bilanciare feature development e operational improvement.

**11. Come gestire ITIL quando l'IT è una persona sola?**

Una persona ricopre tutti i ruoli (Service Desk, Incident Manager, Change Manager, Sysadmin). È normale nelle micro-PMI. L'importante è: (1) avere un sistema di ticketing (anche GLPI free), (2) tracciare ogni intervento, (3) documentare procedure nella KB, (4) fare backup e testarli, (5) avere un contatto esterno per emergenze (MSP, collega freelance). La struttura ITIL serve come checklist mentale, non come organigramma.

**12. Quale framework scegliere: ITIL, COBIT o ISO 20000?**

Dipende dall'obiettivo: (1) Strutturare la gestione IT quotidiana → ITIL 4. (2) Governance IT alignment con business objectives → COBIT 2019. (3) Certificazione aziendale per clienti/gare → ISO 20000. (4) Nessun budget → ITIL 4 (il framework è documentato gratuitamente su fonti pubbliche). In pratica, la maggior parte delle PMI italiane inizia con ITIL per operazioni, aggiunge COBIT se serve governance formale, e considera ISO 20000 solo se richiesto contrattualmente.

**13. Quanto tempo serve per implementare ITIL 4 in una PMI?**

Piano realistico: 90 giorni per le basics (ticketing + incident management + monitoring + KB), 6-12 mesi per consolidare (change enablement + CMDB + problem management + SLM), 12-24 mesi per maturità (continual improvement, analytics, automation). Non è un progetto con fine: è un processo di miglioramento continuo. L'errore tipico è trattarlo come un progetto da "completare".

**14. Come si gestisce il CAB in una PMI dove tutti sono sempre occupati?**

Non serve un CAB tradizionale. Alternativa: (1) Standard Change coprono l'80% dei cambiamenti (nessun CAB richiesto). (2) Normal Change: approvazione via workflow (review asincrono nel tool ITSM, il Change Authority approva/rifiuta in 24h). (3) CAB meeting solo per cambiamenti ad alto rischio o cross-team, max 30 minuti, max 4 partecipanti. (4) Emergency Change: approvazione verbale IC, documentazione retroattiva.

**15. ITIL 4 affronta il tema del cloud e SaaS?**

Sì. La pratica "Infrastructure and Platform Management" copre esplicitamente cloud, hybrid e multi-cloud. La dimensione "Partners and Suppliers" copre la gestione dei rapporti con cloud provider (AWS, Azure, GCP) e SaaS vendor. ITIL 4 Digital and IT Strategy (modulo avanzato) affronta in dettaglio cloud strategy, digital transformation, SaaS governance. Per una PMI: i principi restano gli stessi — monitoring, change management, SLA — ma l'oggetto cambia da server fisici a servizi cloud.

**16. Come si gestiscono le licenze software in ITIL 4?**

Tramite la practice IT Asset Management (ITAM). L'ITAM include la gestione del ciclo di vita delle licenze: acquisto, assegnazione, utilizzo, compliance, rinnovo, dismissione. Tool come Snipe-IT e GLPI tracciano le licenze. KPI: % licenze utilizzate vs acquistate (target >80%), licenze in scadenza prossimi 90 giorni, audit readiness (Microsoft, Adobe, Oracle fanno audit regolari — essere preparati evita penali significative).

**17. Esiste una versione italiana ufficiale di ITIL 4?**

Il libro ufficiale ITIL 4 Foundation è disponibile in traduzione italiana tramite PeopleCert/TSO. Anche l'esame di certificazione è disponibile in italiano. Tuttavia, la terminologia tecnica (incident, change, problem, service desk) è universalmente usata in inglese anche in contesti italiani. Consiglio: studiare in italiano per la teoria, ma familiarizzare con i termini inglesi perché tutti i tool ITSM usano terminologia inglese.

### Caso Studio: PMI Manifatturiera 80 Dipendenti — Prima e Dopo ITIL

**Prima dell'adozione (2024):**

- Richieste IT via WhatsApp, email, telefono al cellulare del sistemista
- Nessun tracking: il sistemista gestiva tutto a memoria
- Incidenti medi P1/P2: 3-4 al mese, MTTR medio 4 ore
- Hardware inventory su foglio Excel aggiornato "ogni tanto"
- Backup: script bash eseguito manualmente 3 volte a settimana
- Monitoring: nessuno (scoprire i problemi da utente arrabbiato)
- Change management: "faccio un aggiornamento e vedo cosa succede"
- Knowledge base: nella testa del sistemista (bus factor = 1)
- Soddisfazione utenti: 2.8/5.0

**Dopo 12 mesi di adozione ITIL 4 (2025):**

- Tutte le richieste via portale GLPI o email support@
- 100% ticket tracciati con priorità, SLA, owner
- Incidenti P1/P2: 1-2 al mese, MTTR medio 1h 30min (riduzione 62%)
- Hardware e software tracciati in GLPI con FusionInventory
- Backup automatizzato con Borg Backup, test restore mensile
- Monitoring Zabbix su tutti i server critici, alert in <5min
- Change Enablement: Standard Change pre-approvati per operazioni comuni
- BookStack con 45 articoli, 30% ticket risolti via self-service
- Soddisfazione utenti: 4.1/5.0

**Investimento totale:**
- GLPI + FusionInventory + Zabbix + BookStack: €0 (FOSS)
- VM server (8 vCPU, 16GB RAM, 200GB SSD): già disponibile
- Tempo setup (160 ore in 3 mesi): €9.600 costo opportunità
- Formazione ITIL Foundation (1 persona): €500

**ROI:**
- Riduzione MTTR: 2.5h risparmiati × 2 incidenti/mese × €60/h × 3 persone = €10.800/anno
- Riduzione incidenti: 2 incidenti/mese in meno × €2.000/incidente medio = €48.000/anno
- Self-service KB: 30% ticket autogestiti × 200 ticket/mese × 15min risparmiati = 900h/anno = €54.000/anno
- **ROI anno 1: ~€100.000 risparmiati su investimento €10.100 = ROI 890%**

### Value Stream Mapping — Esempio Concreto

Un value stream è una sequenza di attività end-to-end che producono valore per uno stakeholder. ITIL 4 usa i value stream per descrivere come le practices collaborano.

**Value Stream: "Onboarding Nuovo Dipendente"**

```
[HR comunica assunzione] ── Engage
       |
       v
[IT riceve richiesta via form standardizzato] ── Service Request Management
       |
       v
[Verifica disponibilità hardware] ── IT Asset Management
       |
   Disponibile ────── Non disponibile → Obtain/Build (ordine hardware)
       |
       v
[Preparazione workstation] ── Deploy: immagine standard, join AD,
       |                       installazione software, configurazione email
       v
[Creazione account utente] ── Service Request: AD, M365, VPN, gestionale, badge
       |
       v
[Consegna hardware + credenziali] ── Engage + Deliver & Support
       |
       v
[Verifica funzionamento con utente] ── Service Desk
       |
       v
[Chiusura ticket + asset registrato in CMDB] ── Service Configuration Management
       |
       v
[Follow-up giorno 3: tutto funziona?] ── Deliver & Support
```

Practices coinvolte: Service Request Management, ITAM, Service Configuration Management, Service Desk, Deployment Management. Tutte operano nel value stream senza una sequenza rigida ma con handoff definiti.

### Template SLA per PMI

Esempio di SLA interno tra IT e business:

```markdown
# Service Level Agreement — Servizi IT Interni

**Versione**: 1.2
**Data**: 2026-05-01
**Validità**: 12 mesi
**Revisione**: semestrale
**Firmatari**: IT Manager + Direzione Generale

## Servizi Coperti

| ID | Servizio | Orario Erogazione | Disponibilità Target |
|---|---|---|---|
| S01 | Postazioni di lavoro | Lun-Ven 8-18 | 98% |
| S02 | Email e collaborazione | 24/7 | 99.5% |
| S03 | ERP gestionale | Lun-Ven 8-20 | 99% |
| S04 | Rete aziendale LAN/WiFi | 24/7 | 99% |
| S05 | Stampa | Lun-Ven 8-18 | 95% |
| S06 | Backup e ripristino | 24/7 | 99.9% |

## Tempi di Risposta e Risoluzione

| Priorità | Risposta | Risoluzione | Escalation |
|---|---|---|---|
| P1 — Critico | 15 min | 4 ore | Immediata a IT Manager |
| P2 — Alto | 30 min | 8 ore business | 2 ore a IT Manager |
| P3 — Medio | 2 ore | 24 ore business | Fine giornata |
| P4 — Basso | 4 ore | 40 ore business | Weekly review |

## Canali di Contatto
- Portale self-service: https://support.azienda.local (preferito)
- Email: support@azienda.it
- Telefono: interno 100 (solo P1/P2 durante orario lavorativo)

## Esclusioni
- Manutenzione programmata comunicata con 48h di anticipo
- Force majeure (blackout elettrico, disastri naturali)
- Software non approvato dall'IT

## Metriche e Reporting
- Report mensile SLA inviato alla Direzione
- Review trimestrale con adeguamento se necessario
- Dashboard live su https://monitoring.azienda.local
```

### Processo di Onboarding IT — Workflow Completo

Un workflow di onboarding ben strutturato è il banco di prova dell'implementazione ITIL. Coinvolge Service Request Management, ITAM, Service Configuration Management, Service Desk, Deployment Management.

**Checklist Onboarding Nuovo Dipendente:**

| Step | Responsabile | SLA | Tool | Note |
|---|---|---|---|---|
| 1. Ricezione comunicazione HR | Service Desk | Giorno -5 | GLPI ticket auto | HR apre ticket via form |
| 2. Verifica disponibilità hardware | ITAM | Giorno -5 | GLPI Asset | Stock check notebook/desktop |
| 3. Preparazione workstation | Sistemista | Giorno -3 | MDT/Autopilot | Immagine standard + join AD |
| 4. Creazione account AD | Sistemista | Giorno -2 | PowerShell/Ansible | Template da ruolo + manager |
| 5. Assegnazione licenze M365 | Sistemista | Giorno -2 | Admin Center | Licenza da template ruolo |
| 6. Creazione casella email | Auto | Giorno -2 | Exchange/M365 | Automatica con account AD |
| 7. Accesso VPN (se remote) | Sistemista | Giorno -1 | FortiClient/WG | Profilo VPN pre-configurato |
| 8. Accesso gestionale ERP | Sistemista | Giorno -1 | Zucchetti/SAP | Profilo ruolo pre-definito |
| 9. Badge/accesso fisico | Facility | Giorno -1 | Sistema badge | Coordinamento con reception |
| 10. Consegna hardware + credenziali | IT / HR | Giorno 0 | Di persona | Kit benvenuto con guida IT |
| 11. Welcome IT (30 min) | Service Desk | Giorno 0 | Meeting | Portale support, password policy, KB |
| 12. Verifica funzionamento | Service Desk | Giorno +1 | GLPI ticket | Tutto funziona? Problemi? |
| 13. Registrazione asset in CMDB | ITAM | Giorno +1 | GLPI | Asset tag + assegnazione utente |
| 14. Follow-up | Service Desk | Giorno +5 | Email | "Tutto bene? Serve altro?" |
| 15. Chiusura ticket onboarding | Service Desk | Giorno +5 | GLPI | Ticket chiuso se tutto OK |

**Checklist Offboarding Dipendente (altrettanto importante):**

| Step | SLA | Note |
|---|---|---|
| Disabilitazione account AD | Giorno 0 (ultimo giorno) | Non eliminare: disabilitare + spostare in OU ex-dipendenti |
| Revoca accessi VPN/ERP/cloud | Giorno 0 | Tutti gli accessi revocati entro EOD |
| Ritiro hardware | Giorno 0 | Notebook, telefono, badge, chiavette, cuffie |
| Backup dati utente | Giorno 0-1 | Backup casella email, OneDrive, cartelle personali |
| Redirect email | Giorno 0 | Forward a manager per 90 giorni |
| Cancellazione licenze | Giorno +1 | Rilascio licenze M365, Adobe, etc. |
| Wipe dispositivo | Giorno +5 | Reset factory, pronto per riassegnazione |
| Aggiornamento CMDB | Giorno +1 | Asset status: disponibile |
| Cancellazione account AD | Giorno +90 | Dopo periodo retention, eliminazione definitiva |

L'offboarding è critico per security: un ex-dipendente con accesso attivo è un rischio GDPR e sicurezza. Automatizzare con Ansible o PowerShell DSC: script che prende in input utente e esegue tutti gli step di disabilitazione.

### Gestione Vendor e Fornitori IT per PMI

La practice Supplier Management in contesto PMI italiano ha specificità legate alla struttura del mercato IT.

**Tipologia fornitori IT PMI italiana:**

| Tipo | Esempi | Gestione |
|---|---|---|
| **ISP/Connectivity** | TIM, Fastweb, Vodafone Business | SLA bandwidth, uptime, escalation 24/7 |
| **Cloud provider** | AWS, Azure, GCP, OVH, Aruba Cloud | SLA compute/storage, support tier, egress costs |
| **Software house gestionale** | Zucchetti, TeamSystem, NTS Informatica | SLA supporto, upgrade, customizzazione |
| **MSP (Managed Service Provider)** | Locale/regionale | SLA copertura, on-call, incident response |
| **Hardware vendor** | Dell, HPE, Lenovo (via distributore) | Garanzia, estensione, RMA, EOL tracking |
| **Cybersecurity** | SOC managed, EDR vendor | SLA detection/response, incident support |
| **Stampanti/MFP** | Kyocera, Ricoh, Canon (noleggio) | Contratto full-service, toner, manutenzione |
| **Telefonia** | VoIP provider, Wildix, 3CX | SLA uptime, support, trunk SIP |

**Template Scorecard Fornitore:**

```markdown
# Scorecard Fornitore — [Nome Fornitore]

**Periodo**: Q[N] [Anno]
**Valutatore**: [Nome IT Manager]

## Performance (0-5 per criterio)

| Criterio | Score | Note |
|---|---|---|
| Rispetto SLA | 4 | 1 breach su 12 ticket |
| Qualità supporto | 3 | Tempo risposta OK, competenza variabile |
| Proattività | 2 | Nessuna comunicazione proattiva |
| Disponibilità | 4 | Reperibili anche fuori orario |
| Value for money | 3 | Prezzi in linea con mercato |
| Documentazione | 2 | Report incompleti |
| **Media** | **3.0** | |

## Incidenti nel periodo
- [Data]: [Descrizione] — SLA rispettato: [Si/No]

## Rinnovo
- Contratto scade: [Data]
- Raccomandazione: [Rinnovo / Rinegoziazione / Sostituzione]
- Note: [Eventuali condizioni]
```

### Continual Improvement — Tecniche Pratiche

**Il Continual Improvement Model ITIL 4 in 7 passi:**

1. **What is the vision?** — Qual è l'obiettivo di alto livello? (es. "IT affidabile che supporta la crescita business")
2. **Where are we now?** — Assessment oggettivo dello stato attuale (metriche, gap, punti di forza)
3. **Where do we want to be?** — Obiettivo specifico e misurabile (es. "MTTR <1 ora per P1")
4. **How do we get there?** — Piano d'azione con step concreti
5. **Take action** — Eseguire il piano
6. **Did we get there?** — Misurare risultati vs target
7. **How do we keep the momentum?** — Consolidare i risultati, identificare prossimo miglioramento

**Kaizen vs Kaikaku:**
- **Kaizen**: miglioramenti piccoli, continui, incrementali. Rischio basso, costo basso, risultati graduali.
- **Kaikaku**: cambiamento radicale, trasformativo. Rischio alto, costo alto, risultati drammatici.

Per PMI: 80% kaizen, 20% kaikaku. Il kaizen costruisce la disciplina; il kaikaku serve per salti di qualità (es. migrazione da email a ticketing, introduzione monitoring).

**5S applicato all'IT:**
Metodologia lean applicata all'ambiente IT:
1. **Seiri (Sort)**: eliminare tool, processi, documenti non necessari
2. **Seiton (Set in Order)**: organizzare ciò che resta (naming convention, folder structure, tagging)
3. **Seiso (Shine)**: pulizia regolare (archiviare ticket vecchi, aggiornare KB, rimuovere alert obsoleti)
4. **Seiketsu (Standardize)**: creare standard per le prime tre (template, checklist, automation)
5. **Shitsuke (Sustain)**: mantenere la disciplina nel tempo (review periodiche, audit, KPI)

---

## Riferimenti

- AXELOS / PeopleCert, "ITIL Foundation: ITIL 4 Edition", 2019. ISBN 978-0113316076.
- AXELOS, "ITIL 4: Direct, Plan and Improve", 2020.
- AXELOS, "ITIL 4: Drive Stakeholder Value", 2020.
- AXELOS, "ITIL 4: Create, Deliver and Support", 2020.
- AXELOS, "ITIL 4: High Velocity IT", 2020.
- AXELOS, "ITIL 4: Digital and IT Strategy", 2020.
- ISACA, "COBIT 2019 Framework: Introduction and Methodology", 2018.
- ISO/IEC 20000-1:2018, "Information technology — Service management — Part 1: Service management system requirements".
- Google SRE Team, "Site Reliability Engineering: How Google Runs Production Systems", O'Reilly, 2016.
- Google SRE Team, "The Site Reliability Workbook: Practical Ways to Implement SRE", O'Reilly, 2018.
- Gene Kim, Patrick Debois, John Willis, Jez Humble, "The DevOps Handbook", IT Revolution Press, 2nd Edition, 2021.
- Documentazione GLPI: https://glpi-project.org/documentation/
- Documentazione FusionInventory: http://fusioninventory.org/documentation/
- Documentazione Zabbix: https://www.zabbix.com/documentation/current/en/manual
- Documentazione ServiceNow ITSM: https://docs.servicenow.com/
- Atlassian Jira Service Management docs: https://support.atlassian.com/jira-service-management/
- BookStack: https://www.bookstackapp.com/docs/
- Ansible Documentation: https://docs.ansible.com/
- AgID — Linee guida acquisizione e riuso software per la PA (riferimento normativo italiano per scelta open source).

**Certificazioni ITIL 4:**
- **ITIL 4 Foundation**: livello base, prerequisito per tutti gli altri. ~€395 esame (PeopleCert). Validità perpetua.
- **ITIL 4 Managing Professional (MP)**: 4 moduli per chi gestisce servizi IT quotidianamente.
- **ITIL 4 Strategic Leader (SL)**: 2 moduli per chi definisce strategia IT.
- **ITIL 4 Practice Manager**: specializzazione su singola practice.

**Risorse gratuite per studio:**
- YouTube: "ITIL 4 Foundation" — corsi completi gratuiti (SimpliLearn, Dion Training preview)
- PeopleCert Official App: materiale di studio e quiz
- ITIL Process Map (wiki.en.it-processmaps.com): mappa dettagliata practices
- AXELOS My ITIL: community ufficiale con articoli e white papers

**Normativa italiana rilevante per ITIL:**
- D.Lgs 82/2005 (CAD - Codice Amministrazione Digitale): per PA
- Piano Triennale informatica PA (AgID): riferimenti a service management
- NIS2 (Direttiva UE 2022/2555): obblighi incident management e risk management
- GDPR (Regolamento UE 2016/679): impatta ITAM, incident, change
- ISO 27001:2022: si integra con practices ITIL

**Community Italia:**
- itSMF Italia: capitolo italiano IT Service Management Forum
- AICA: Associazione Italiana per l'Informatica
- CLUSIT: per aspetti security di ITIL
- DevOps Days Milano/Roma: con tracce ITSM
- LinkedIn groups: "ITIL Italia", "IT Service Management Italia"

**Podcast e blog:**
- "ITSM Podcast" (itSMF UK) — in inglese, ricco di contenuti pratici
- "Beyond ITIL" podcast — approccio critico e pragmatico
- "Joe the IT Guy" (ManageEngine) — blog pratico per IT manager

**Confronto completo ITSM tool per PMI italiana:**

| Criterio | GLPI | Freshservice | Jira SM | Zammad |
|---|---|---|---|---|
| Costo (2 agent) | Gratuito | €456/anno | €408/anno | Gratuito |
| Hosting | Self-hosted | SaaS | SaaS | Self-hosted |
| CMDB integrata | Sì | Sì (da Standard) | Plugin | No |
| Asset Management | Sì | Sì | Plugin | No |
| Knowledge Base | Sì | Sì | Confluence | Sì |
| SLA Management | Sì | Sì | Sì | Sì |
| Change Management | Sì | Sì (da Pro) | Plugin | No |
| Service Catalogue | Sì | Sì | Sì | No |
| API REST | Sì | Sì | Sì | Sì |
| Italiano | Sì | Sì | Sì | Parziale |
| Curva apprendimento | Media | Bassa | Alta | Bassa |
| Scalabilità | Media | Alta | Alta | Media |

**Raccomandazione per contesto:**
- Micro PMI (<20 dip), zero budget → GLPI
- PMI (20-100 dip), self-hosted → GLPI o Zammad
- PMI (20-100 dip), SaaS → Freshservice Starter
- PMI tech-oriented, già Atlassian → Jira Service Management
- Midmarket (100-500 dip) → Freshservice Pro o Jira SM Premium
- Enterprise (500+ dip) → ServiceNow

### Maturity Assessment ITIL 4

Framework per valutare la maturità dell'implementazione ITIL nella propria organizzazione:

**Livello 1 — Iniziale (Caotico)**
- Nessun processo formale
- IT è reattivo al 100%
- Nessun tracking di ticket/incident
- Knowledge nella testa delle persone
- Backup non testati
- Nessun monitoring

**Livello 2 — Ripetibile (Basilare)**
- Ticketing system in uso (anche se non sempre)
- Incident management base (P1-P4)
- Asset inventory esiste (Excel o simile)
- Backup automatizzati
- Monitoring base (ping/uptime)
- SLA definiti informalmente

**Livello 3 — Definito (Strutturato)**
- Processo ticketing universale (tutti i ticket via sistema)
- Change Enablement con Standard/Normal/Emergency
- CMDB con CI critici mappati
- Knowledge Base con >50 articoli attivi
- Monitoring multi-livello (infra + applicativo)
- SLA formali con reporting mensile
- Postmortem dopo P1/P2

**Livello 4 — Gestito (Misurato)**
- KPI definiti e tracciati per ogni practice
- Continual Improvement Register attivo
- Problem Management proattivo
- Analytics su trend incidenti
- Automazione processi comuni
- Service Catalogue completo
- SLA breach <10%

**Livello 5 — Ottimizzato (Eccellenza)**
- Predictive analytics (ML su trend)
- Chaos engineering / game day
- Cross-team learning sistematico
- Value stream mapping e ottimizzazione
- Self-service >50% richieste
- NPS utenti >70
- Zero incident ricorrenti

### Anti-Pattern ITIL da Evitare

**1. ITIL Waterfall**: implementare tutte le 34 practices in sequenza in un progetto di 18 mesi. Risultato: fallimento garantito. Alternativa: iterazione rapida su 6-8 practices critiche.

**2. Process Over People**: processi perfetti su carta ma non adottati dal team. Risultato: shadow IT, bypass, frustrazione. Alternativa: coinvolgere il team nella definizione dei processi.

**3. Tool-First**: acquistare ServiceNow per un team di 3 persone perché "è la best practice". Risultato: tool sovradimensionato, sottoutilizzato, costoso. Alternativa: partire da GLPI o Freshservice Starter.

**4. CMDB-First**: iniziare dall'inventario completo di 5.000 CI prima di avere un ticketing funzionante. Risultato: 6 mesi di lavoro su CMDB, zero valore operativo. Alternativa: Service Desk + Incident Management prima.

**5. KPI Overload**: definire 50 KPI per ogni practice. Risultato: nessuno li legge, nessuno li migliora. Alternativa: 3-5 KPI per practice, tutti con target e owner.

**6. Certification Theater**: certificare tutti in ITIL Foundation senza cambiare nulla operativamente. Risultato: certificati appesi al muro, processi invariati. Alternativa: certificare 1-2 persone chiave e investire il resto in implementazione pratica.

**7. Language Barrier**: usare terminologia ITIL verso utenti business ("please submit a Service Request via the Service Catalogue for Change Enablement"). Risultato: utenti confusi, resistenza. Alternativa: linguaggio business verso utenti, terminologia ITIL solo internamente.

**8. One-Person ITIL**: tutta la responsabilità ITIL su una persona che se ne va e tutto collassa. Risultato: bus factor 1. Alternativa: almeno 2 persone cross-trained, processi documentati.

### Roadmap di Adozione ITIL 4 — Piano 24 Mesi

**Mese 1-3: Foundation (Quick Wins)**
- Deploy ITSM tool (GLPI/Freshservice)
- Configurazione ticketing base (categorie, priorità, SLA)
- Email collector + portale self-service
- 10 articoli KB fondamentali
- Monitoring base (Zabbix/PRTG)
- Comunicazione a utenti: "da oggi support via portale"

**Mese 4-6: Stabilization**
- Asset inventory con discovery automatico
- Change Enablement: catalogo Standard Change
- Knowledge Base: 30+ articoli
- Service Catalogue: 8-10 servizi definiti
- Dashboard SLA: primo report mensile alla direzione
- Training 1 persona ITIL Foundation

**Mese 7-9: Expansion**
- CMDB minima: servizi business + CI critici + relazioni
- Problem Management: registro problemi, RCA per P1
- SLM: SLA formali concordati con business
- Automazione: onboarding utente automatizzato
- Integration: Zabbix → GLPI (auto-ticket da alert)

**Mese 10-12: Consolidation**
- Supplier Management: registro fornitori + SLA + scadenzario
- Continual Improvement Register: prime 10 voci
- Postmortem process per P1/P2
- Service Continuity: DR plan documentato
- Self-service: 25-30% ticket autogestiti
- Review annuale: metriche prima/dopo

**Mese 13-18: Optimization**
- Analytics avanzati: trend, pattern, forecasting
- Automazione: patch management, backup verification
- Capacity Planning base (vedi documento dedicato)
- Change Enablement maturo: CAB solo per alto rischio
- Near-miss reporting
- Cross-training: 2a persona su tutti i processi

**Mese 19-24: Maturity**
- Proactive Problem Management
- Game Day / chaos engineering base
- Service Financial Management: TCO per servizio
- Audit compliance (ISO 27001 / NIS2 mapping)
- Value stream optimization
- Piano strategico IT triennale basato su dati ITIL

### Integrazione ITIL con Automazione (Ansible + n8n)

Per PMI che vogliono automatizzare i processi ITIL senza investire in piattaforme enterprise:

**Ansible per Standard Change automatizzati:**

```yaml
# playbook: standard-change-patch-windows.yml
# Eseguito automaticamente ogni Patch Tuesday +1 settimana
---
- name: Standard Change - Windows Patch Management
  hosts: windows_servers
  vars:
    change_id: "SC-{{ lookup('pipe', 'date +%Y%m%d-%H%M') }}"
  tasks:
    - name: Log inizio change in GLPI via API
      uri:
        url: "https://glpi.azienda.local/apirest.php/Change"
        method: POST
        headers:
          App-Token: "{{ glpi_app_token }}"
          Session-Token: "{{ glpi_session_token }}"
        body_format: json
        body:
          input:
            name: "Standard Change - Patch Windows {{ ansible_hostname }}"
            content: "Applicazione patch sicurezza mensile"
            status: 1
            urgency: 3
            impact: 3

    - name: Install Windows updates
      win_updates:
        category_names:
          - SecurityUpdates
          - CriticalUpdates
        reboot: yes
        reboot_timeout: 600
      register: update_result

    - name: Log completamento in GLPI
      uri:
        url: "https://glpi.azienda.local/apirest.php/Change/{{ change_id }}"
        method: PUT
        body_format: json
        body:
          input:
            status: 6  # Closed
            actiontime: "{{ update_result.elapsed }}"
```

**n8n per workflow automazione ITSM:**

n8n (self-hosted, FOSS) può automatizzare workflow ITIL senza coding:

1. **Auto-categorizzazione ticket**: webhook da GLPI → n8n → analisi testo con regex → aggiornamento categoria ticket
2. **Escalation automatica**: cron ogni 15 min → query GLPI ticket P1 senza assegnazione > 10 min → notifica PagerDuty/Telegram
3. **Report SLA automatico**: cron mensile → query GLPI → calcolo metriche → generazione PDF → invio email direzione
4. **Alert monitoring → ticket**: webhook da Zabbix → n8n → creazione ticket GLPI con severity mappata
5. **Scadenze contratti**: cron settimanale → query GLPI contratti scadenza <90gg → notifica IT manager

---

## Esercizi

1. **Lab — Selezione 10 practices.** Per la tua organizzazione, seleziona le 10 practices ITIL 4 più rilevanti. Per ciascuna, indica: (a) perché è rilevante, (b) forma minima accettabile di implementazione, (c) tool proposto, (d) KPI di successo. Presenta la selezione in una tabella.

2. **Lab — Setup GLPI.** Installa GLPI su una VM di test (Ubuntu 22.04, LAMP). Configura: 5 categorie ticket, priorità P1-P4 con matrice impatto×urgenza, SLA per ogni priorità, email collector, almeno 1 utente LDAP. Crea 5 ticket di test e verificali nel sistema.

3. **Lab — Service Catalogue.** Definisci il catalogo servizi IT per la tua organizzazione. Per ogni servizio indica: nome, descrizione, SLA, owner, canale di richiesta, escalation, dipendenze. Obiettivo: 8-10 servizi.

4. **Lab — Change Enablement.** Definisci il catalogo Standard Change per la tua organizzazione (minimo 8 voci). Per ogni Standard Change documenta: descrizione, frequenza, owner, window di esecuzione, rollback, rischio. Implementa il workflow Normal Change nel tool ITSM.

5. **Lab — Knowledge Base.** Scrivi i primi 10 articoli KB per la tua organizzazione: 5 troubleshooting (sintomo → diagnosi → soluzione), 3 how-to (procedure operative), 2 FAQ. Pubblica su BookStack o Confluence. Misura l'utilizzo dopo 30 giorni.

6. **Stretch — SLA Definition.** Negozia con il management aziendale un SLA formale per i 5 servizi IT più critici. Definisci metriche, target, reporting, esclusioni. Presenta il primo report SLA dopo 30 giorni.

7. **Stretch — Kaizen Review.** Istituisci una review mensile di continual improvement: 30 minuti con il team IT, identifica 1 piccolo miglioramento da implementare nel mese successivo. Traccia nel CIR. Dopo 6 mesi, presenta i 6 miglioramenti realizzati.

8. **Stretch — Value Stream Mapping.** Mappa un value stream end-to-end della tua organizzazione (es. "Onboarding nuovo dipendente" o "Risoluzione incidente P1"). Identifica le practices ITIL coinvolte, i tempi di attraversamento, i colli di bottiglia, le opportunità di automazione.

## Auto-valutazione

1. **SVS**: cos'è il Service Value System? Elenca i 5 componenti.
2. **7 Guiding Principles**: elenca tutti e 7 e per ciascuno fornisci un esempio pratico in contesto PMI.
3. **Continual Improvement**: kaizen vs big bang — quale approccio e perché?
4. **Change Enablement**: qual è la differenza tra Standard, Normal e Emergency Change?
5. **ITIL v3 vs v4**: elenca 5 differenze sostanziali.
6. **Service Value Chain**: elenca le 6 attività e descrivi il loro scopo.
7. **4 Dimensioni**: quali sono e perché servono tutte e 4?
8. **Practices**: quante sono e come sono categorizzate? Quali sono le 6 essenziali per una PMI?
9. **CMDB**: cos'è un CI? Qual è la differenza tra CMDB e asset inventory?
10. **Problem vs Incident**: qual è la differenza fondamentale tra Problem Management e Incident Management?
11. **SLA vs OLA vs UC**: definisci ciascuno e spiega quando si usa.
12. **Error Budget**: cos'è e come si collega con SLO e SLM?
13. **FCR**: cos'è il First Call Resolution e perché è importante?
14. **DORA metrics**: quali sono le 4 metriche DORA e quale practice ITIL le produce?
15. **NIS2**: come si mappano i requisiti NIS2 sulle practices ITIL 4?

## Glossario locale

| Termine | Definizione |
|---|---|
| **SVS** | Service Value System — struttura concettuale di alto livello ITIL 4 che descrive come l'organizzazione crea valore. |
| **SVC** | Service Value Chain — modello operativo a 6 attività (Plan, Improve, Engage, Design & Transition, Obtain/Build, Deliver & Support). |
| **Practice** | Unità di capacità organizzativa in ITIL 4 (34 totali), composta da persone, processi, tecnologia, partner. |
| **Guiding Principle** | Uno dei 7 principi universali ITIL 4 applicabili a qualsiasi decisione e situazione. |
| **CI (Configuration Item)** | Qualsiasi componente gestito per erogare un servizio IT (server, switch, applicazione, contratto, documento). |
| **CMDB** | Configuration Management Database — database dei CI e delle loro relazioni. |
| **Change Enablement** | Practice che massimizza cambiamenti riusciti gestendo rischio, approvazione e tracking. |
| **Standard Change** | Cambiamento pre-approvato, basso rischio, ripetibile (es. patch antivirus, onboarding utente). |
| **Normal Change** | Cambiamento che richiede valutazione rischio caso per caso e approvazione della Change Authority. |
| **Emergency Change** | Cambiamento urgente per risolvere incident critico, approvazione post-hoc. |
| **CAB** | Change Advisory Board — comitato che valuta i Normal Change ad alto rischio. |
| **SLA** | Service Level Agreement — accordo formale tra IT e business su livelli di servizio. |
| **OLA** | Operational Level Agreement — accordo interno tra team IT per supportare gli SLA. |
| **UC** | Underpinning Contract — contratto con fornitore esterno che supporta gli SLA. |
| **SLO** | Service Level Objective — target interno di qualità del servizio. |
| **SLI** | Service Level Indicator — metrica che misura effettivamente il livello di servizio. |
| **FCR** | First Call Resolution — percentuale di ticket risolti al primo contatto. |
| **CSAT** | Customer Satisfaction — misura di soddisfazione utente (tipicamente sondaggio post-ticket). |
| **MTTR** | Mean Time to Recover/Resolve — tempo medio dalla detection alla risoluzione. |
| **MTTA** | Mean Time to Acknowledge — tempo medio dalla segnalazione all'acknowledgment. |
| **CIR** | Continual Improvement Register — registro delle iniziative di miglioramento. |
| **Kaizen** | Approccio giapponese di miglioramento continuo a piccoli passi incrementali. |
| **Value Stream** | Sequenza di attività end-to-end che producono valore per uno stakeholder. |
| **ITSM** | IT Service Management — gestione dei servizi IT come disciplina. |
| **DORA Metrics** | 4 metriche DevOps (Lead Time, Deployment Frequency, Change Failure Rate, MTTR). |
| **NIS2** | Direttiva UE 2022/2555 su cybersecurity con obblighi per organizzazioni essenziali/importanti. |
| **PESTLE** | Framework di analisi fattori esterni (Political, Economic, Social, Technological, Legal, Environmental). |
| **Swarming** | Modello Service Desk senza tier rigidi — l'esperto giusto risponde direttamente. |
| **Known Error** | Problema con root cause identificata e workaround documentato, in attesa di fix permanente. |
| **RFC** | Request for Change — richiesta formale di cambiamento. |
| **RACI** | Matrice Responsible-Accountable-Consulted-Informed per chiarire ruoli e responsabilità. |
| **Westrum Model** | Tipologia di cultura organizzativa (patologica, burocratica, generativa) di Ron Westrum. |
| **Service Desk** | Punto di contatto unico (SPOC) tra utenti e organizzazione IT per incident e richieste. |
| **Problem Record** | Registrazione di un problema con root cause analysis, workaround e piano di fix permanente. |
| **Incident** | Interruzione non pianificata di un servizio IT o riduzione della qualità. |
| **Service Request** | Richiesta pre-definita dall'utente per un servizio standard (password, accesso, hardware). |
| **Error Budget** | Quantità di errore/downtime "accettabile" dato un SLO (es. SLO 99.9% = 43 min/mese di budget errore). |
| **ITAM** | IT Asset Management — gestione ciclo di vita completo degli asset IT. |
| **Service Catalogue** | Lista pubblicata di tutti i servizi IT disponibili con relative informazioni. |
| **Shadow IT** | Uso di sistemi, software o servizi IT senza approvazione o conoscenza del team IT. |
| **Service Owner** | Persona accountable per la fornitura end-to-end di un servizio IT specifico. |
| **Process Owner** | Persona accountable per il design, implementazione e miglioramento di un processo/practice. |
| **Utility** | Funzionalità offerta da un servizio per soddisfare un bisogno specifico ("fit for purpose"). |
| **Warranty** | Assicurazione che un servizio soddisfi requisiti concordati di qualità ("fit for use"). |
| **Four Dimensions** | Le 4 dimensioni di ITIL 4: Organizations & People, Information & Technology, Partners & Suppliers, Value Streams & Processes. |
| **Continual Improvement Model** | Modello ITIL in 7 passi per guidare iniziative di miglioramento a qualsiasi livello. |
| **5S** | Metodologia lean (Sort, Set in Order, Shine, Standardize, Sustain) applicabile a IT. |
| **Kaikaku** | Cambiamento radicale/trasformativo, contrapposto al miglioramento incrementale kaizen. |
| **ADR** | Architecture Decision Record — documentazione delle decisioni architetturali con razionale. |
| **MEPA** | Mercato Elettronico della Pubblica Amministrazione — piattaforma acquisti PA italiana. |
| **CONSIP** | Centrale acquisti PA italiana che stipula convenzioni quadro per categorie merceologiche. |
