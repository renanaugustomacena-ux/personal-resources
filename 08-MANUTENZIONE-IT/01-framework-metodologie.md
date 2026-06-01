# Framework e Metodologie IT --- Guida Completa

> **Modulo:** Operations IT · Posizione: Fase 1 · Modulo 01
> **Prerequisiti:** Concetti generali ITSM
> **Obiettivi:** distinguere Service Request, Incident, Problem, Change; ITIL v4 vocabolario clean; SR vs incident triage wizard.
> **Tempo:** 60-90 min · lab 120 min
> **Livello:** novice → competent
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **Service Request ≠ Incident.** SR e voluto, Incident e non voluto.
2. **Problem != Incident.** Problem e cause root, Incident e sintomo.
3. **Change Enablement (ITIL v4) > Change Management (v3).** Cambio di linguaggio: enablement enfatizza riduzione attrito.
4. **CAB e per cambi alti rischio, non per ogni patch.** Standard change pre-approved.

## Indice

1. [Panoramica](#panoramica)
2. [ITIL Fondamenti per la Manutenzione](#itil-fondamenti-per-la-manutenzione)
3. [Gestione Incidenti (Incident Management)](#gestione-incidenti-incident-management)
4. [Gestione Problemi (Problem Management)](#gestione-problemi-problem-management)
5. [Gestione Cambiamenti (Change Management)](#gestione-cambiamenti-change-management)
6. [Gestione Configurazione e CMDB](#gestione-configurazione-e-cmdb)
7. [Gestione Livelli di Servizio (SLA)](#gestione-livelli-di-servizio-sla)
8. [Documentazione e Procedure Standard](#documentazione-e-procedure-standard)
9. [Miglioramento Continuo (CSI)](#miglioramento-continuo-csi)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Panoramica

La manutenzione dei sistemi IT rappresenta una delle attivita piu critiche all'interno di qualsiasi organizzazione moderna. Senza un approccio strutturato e metodico, il rischio di downtime non pianificato, perdita di dati, violazioni di sicurezza e degradazione delle prestazioni aumenta in modo esponenziale. I framework e le metodologie IT forniscono esattamente quel tessuto connettivo tra le operazioni quotidiane e gli obiettivi strategici dell'organizzazione.

### Perche adottare un framework?

Un framework IT non e un insieme rigido di regole da seguire ciecamente, ma piuttosto una raccolta organizzata di best practices, processi e linee guida che permettono di:

- **Standardizzare le operazioni**: ogni membro del team segue le stesse procedure, riducendo la variabilita e gli errori umani. Un tecnico che interviene alle 3 di notte su un incidente critico deve poter seguire una procedura chiara, non improvvisare.
- **Migliorare la comunicazione**: con un linguaggio comune e processi condivisi, la comunicazione tra team tecnici, management e stakeholder diventa fluida e priva di ambiguita.
- **Ridurre i costi operativi**: un processo ben definito di gestione degli incidenti riduce il tempo medio di risoluzione (MTTR), che si traduce direttamente in risparmi economici. Un'ora di downtime per un sistema critico puo costare da migliaia a milioni di euro.
- **Garantire la conformita normativa**: framework come ITIL, ISO 20000 e COBIT forniscono gli strumenti per dimostrare la conformita a requisiti normativi come GDPR, NIS2 e standard di settore.
- **Abilitare il miglioramento continuo**: senza metriche, processi definiti e revisioni periodiche, il miglioramento resta un concetto astratto. I framework trasformano il miglioramento in un processo misurabile e ripetibile.

### Il panorama dei framework IT

Il panorama dei framework per la gestione IT e vasto e in continua evoluzione:

| Framework | Focus Principale | Ambito |
|-----------|-----------------|--------|
| ITIL v4 | Service Management | Gestione completa dei servizi IT |
| COBIT 2019 | IT Governance | Allineamento IT-business, compliance |
| ISO/IEC 20000 | ITSM Certification | Certificazione gestione servizi |
| ISO 27001 | Information Security | Sicurezza delle informazioni |
| DevOps/SRE | Reliability Engineering | Automazione, affidabilita, velocita |
| TOGAF | Enterprise Architecture | Architettura enterprise |
| MOF (Microsoft) | Operations Framework | Operazioni su piattaforma Microsoft |

In questa guida ci concentreremo prevalentemente su ITIL v4 come framework di riferimento principale per la manutenzione IT, integrandolo con concetti provenienti da DevOps, SRE e standard ISO dove rilevante. La scelta di ITIL come asse portante e motivata dalla sua adozione capillare a livello mondiale, dalla sua completezza e dalla sua evoluzione verso un approccio piu agile e flessibile con la versione 4.

---

## ITIL Fondamenti per la Manutenzione

### ITIL v4 Service Value System (SVS)

ITIL v4, rilasciato nel 2019, rappresenta un cambio di paradigma rispetto alle versioni precedenti. Non si parla piu di "processi" rigidi organizzati in fasi del ciclo di vita del servizio, ma di un **Service Value System (SVS)** che descrive come tutti i componenti e le attivita dell'organizzazione lavorano insieme per creare valore.

Il SVS e composto da cinque elementi fondamentali:

1. **Guiding Principles** --- principi universali che guidano le decisioni in ogni circostanza.
2. **Governance** --- il sistema attraverso cui l'organizzazione dirige e controlla le attivita IT.
3. **Service Value Chain** --- un modello operativo che descrive le attivita chiave per rispondere alla domanda e creare valore.
4. **Practices** --- set di risorse organizzative progettate per eseguire lavoro o raggiungere un obiettivo (sostituiscono i vecchi "processi").
5. **Continual Improvement** --- attivita ricorrente eseguita a tutti i livelli per garantire che le prestazioni soddisfino continuamente le aspettative degli stakeholder.

L'elemento centrale e che l'SVS prende come input le **opportunita e la domanda** e produce come output il **valore**. Tutto cio che si trova nel mezzo esiste per massimizzare la creazione di valore.

### I 7 Principi Guida (Guiding Principles)

I principi guida di ITIL v4 sono applicabili in qualsiasi circostanza e rappresentano la bussola per ogni decisione operativa:

**1. Focus on Value (Concentrarsi sul valore)**
Ogni attivita di manutenzione deve essere collegata al valore che porta all'organizzazione e agli utenti finali. Prima di implementare un aggiornamento o una procedura di manutenzione, chiedersi: "Quale valore porta questo intervento?". Un aggiornamento firmware di uno switch di rete non e fine a se stesso: migliora la sicurezza, la stabilita e le prestazioni, proteggendo il business.

**2. Start Where You Are (Partire da dove ci si trova)**
Non si parte mai da zero. L'organizzazione ha gia processi, strumenti e competenze. Prima di adottare un nuovo framework, e fondamentale valutare lo stato attuale attraverso assessment oggettivi. Misurare, documentare e poi decidere cosa mantenere, cosa migliorare e cosa sostituire.

**3. Progress Iteratively with Feedback (Progredire iterativamente con feedback)**
L'implementazione di un framework completo non avviene in un colpo solo. Si procede per iterazioni piccole e misurabili, raccogliendo feedback ad ogni passo. Implementare prima la gestione incidenti, poi i problemi, poi i cambiamenti --- non tutto simultaneamente.

**4. Collaborate and Promote Visibility (Collaborare e promuovere la visibilita)**
La manutenzione IT non e un'attivita isolata. Coinvolge team di sviluppo, operations, sicurezza, business. Dashboard condivise, stand-up meeting, canali di comunicazione aperti e documentazione accessibile sono strumenti essenziali.

**5. Think and Work Holistically (Pensare e lavorare in modo olistico)**
Un cambiamento su un server puo avere ripercussioni sulla rete, sulle applicazioni, sulla sicurezza. E fondamentale comprendere le interdipendenze e considerare l'impatto end-to-end di ogni intervento.

**6. Keep It Simple and Practical (Mantenere semplicita e praticita)**
Processi troppo complessi vengono ignorati. Documentazione troppo lunga non viene letta. Ogni processo deve avere il minimo numero di passaggi necessari per raggiungere l'obiettivo. Se un modulo di change request ha 50 campi obbligatori, nessuno lo compilera correttamente.

**7. Optimize and Automate (Ottimizzare e automatizzare)**
Prima si ottimizza il processo manuale, poi lo si automatizza. Automatizzare un processo inefficiente produce risultati inefficienti piu velocemente. L'automazione della manutenzione (patch management, backup, monitoring) e un obiettivo chiave.

### Le 4 Dimensioni della Gestione dei Servizi

ITIL v4 identifica quattro dimensioni che devono essere considerate per garantire un approccio olistico:

1. **Organizations and People**: struttura organizzativa, competenze, ruoli, cultura aziendale. Un framework funziona solo se le persone sono formate e motivate.
2. **Information and Technology**: gli strumenti, le piattaforme, i database, i sistemi di monitoring. Include anche la gestione dell'informazione (CMDB, knowledge base, documentazione).
3. **Partners and Suppliers**: fornitori esterni, contratti di manutenzione, SLA con vendor, outsourcing. Nella manutenzione IT, i rapporti con i fornitori hardware e software sono critici.
4. **Value Streams and Processes**: i flussi di lavoro end-to-end che trasformano la domanda in valore. Ogni attivita di manutenzione e parte di un value stream.

### La Service Value Chain

La Service Value Chain e il cuore operativo dell'SVS. Si compone di sei attivita interconnesse:

- **Plan**: pianificazione strategica e tattica della manutenzione.
- **Improve**: identificazione e implementazione di miglioramenti continui.
- **Engage**: interazione con stakeholder, utenti e clienti.
- **Design and Transition**: progettazione di servizi e procedure, transizione in produzione.
- **Obtain/Build**: acquisizione o sviluppo delle risorse necessarie.
- **Deliver and Support**: erogazione dei servizi e supporto operativo quotidiano.

### Practice ITIL Chiave per la Manutenzione

Le practice ITIL piu rilevanti per la manutenzione IT sono:

| Practice | Rilevanza per la Manutenzione |
|----------|------------------------------|
| Incident Management | Gestione quotidiana di guasti e malfunzionamenti |
| Problem Management | Analisi delle cause radice e prevenzione della ricorrenza |
| Change Enablement | Controllo e gestione di modifiche a sistemi e infrastruttura |
| Service Level Management | Definizione e monitoraggio degli SLA |
| IT Asset Management | Tracciamento del ciclo di vita degli asset IT |
| Monitoring and Event Management | Rilevamento proattivo di anomalie e degradazioni |
| Configuration Management | Gestione del CMDB e delle relazioni tra CI |
| Knowledge Management | Gestione della documentazione e della conoscenza operativa |
| Release Management | Gestione dei rilasci software e firmware |
| Service Request Management | Gestione delle richieste di servizio standard |

---

## Gestione Incidenti (Incident Management)

### Definizione e Obiettivo

Un **incidente** e un'interruzione non pianificata di un servizio IT o una riduzione della qualita di un servizio IT. L'obiettivo della gestione incidenti e ripristinare il normale funzionamento del servizio il piu rapidamente possibile, minimizzando l'impatto negativo sulle operazioni di business.

E fondamentale distinguere un incidente da una richiesta di servizio (service request): l'incidente e non pianificato e negativo, la richiesta di servizio e pianificata e standard (ad esempio, la richiesta di un nuovo account utente).

### Ciclo di Vita dell'Incidente

Il ciclo di vita di un incidente segue fasi ben definite:

**1. Rilevamento (Detection)**
L'incidente puo essere rilevato attraverso:
- Sistemi di monitoring automatico (Zabbix, Nagios, Prometheus, Datadog)
- Segnalazione dell'utente (telefono, email, portale self-service, chat)
- Rilevamento da parte del team IT durante attivita ordinarie
- Correlazione di eventi da parte di sistemi SIEM

**2. Registrazione (Logging)**
Ogni incidente deve essere registrato nel sistema di ticketing con le seguenti informazioni minime:
- Data e ora di rilevamento
- Fonte della segnalazione
- Descrizione del sintomo
- Servizio/sistema impattato
- Dati di contatto del segnalante
- Numero univoco del ticket

**3. Classificazione (Classification)**
La classificazione permette di categorizzare l'incidente per facilitare l'instradamento e l'analisi:
- Categoria (Hardware, Software, Rete, Sicurezza, Database, Applicazione)
- Sottocategoria (Server, Workstation, Switch, Firewall, ecc.)
- Tipo (Interruzione totale, Degradazione, Errore intermittente)

**4. Prioritizzazione (Prioritization)**
La priorita viene determinata incrociando due fattori: **Impatto** e **Urgenza**.

**Matrice Impatto x Urgenza:**

| | Urgenza Alta | Urgenza Media | Urgenza Bassa |
|---|---|---|---|
| **Impatto Alto** | P1 --- Critico | P2 --- Alto | P3 --- Medio |
| **Impatto Medio** | P2 --- Alto | P3 --- Medio | P4 --- Basso |
| **Impatto Basso** | P3 --- Medio | P4 --- Basso | P5 --- Pianificato |

Definizione dei livelli di impatto:
- **Alto**: servizio critico completamente non disponibile, impatto su un grande numero di utenti o su processi di business essenziali.
- **Medio**: servizio parzialmente degradato, impatto su un numero significativo di utenti o su processi importanti.
- **Basso**: servizio marginalmente impattato, impatto su singoli utenti o processi non critici.

Definizione dei livelli di urgenza:
- **Alta**: nessun workaround disponibile, la risoluzione e necessaria immediatamente.
- **Media**: workaround disponibile ma con impatto sulla produttivita.
- **Bassa**: workaround efficace disponibile, la risoluzione puo essere pianificata.

**Tempi di risposta e risoluzione target per priorita:**

| Priorita | Tempo di Risposta | Tempo di Risoluzione | Esempio |
|----------|------------------|---------------------|---------|
| P1 --- Critico | 15 minuti | 1 ora | Server ERP in produzione non raggiungibile |
| P2 --- Alto | 30 minuti | 4 ore | Sistema email non funzionante per un dipartimento |
| P3 --- Medio | 2 ore | 8 ore lavorative | Stampante di rete condivisa offline |
| P4 --- Basso | 4 ore | 24 ore lavorative | Problema grafico su un'applicazione non critica |
| P5 --- Pianificato | 8 ore | 5 giorni lavorativi | Richiesta di ottimizzazione prestazioni |

**5. Investigazione e Diagnosi (Investigation and Diagnosis)**
Il team di supporto analizza l'incidente, raccoglie dati diagnostici, consulta la knowledge base e il KEDB (Known Error Database) per identificare soluzioni note.

**6. Risoluzione e Ripristino (Resolution and Recovery)**
Viene applicata la soluzione identificata e si verifica che il servizio sia tornato alla normalita. La verifica deve includere test funzionali e conferma da parte dell'utente.

**7. Chiusura (Closure)**
L'incidente viene chiuso formalmente dopo la conferma della risoluzione. La chiusura include:
- Documentazione della soluzione applicata
- Aggiornamento della knowledge base
- Verifica della soddisfazione dell'utente
- Eventuale apertura di un ticket di problema se la causa radice non e stata identificata

### Livelli di Escalation

La struttura di escalation garantisce che gli incidenti vengano gestiti dal livello di competenza appropriato:

**Livello 1 (L1) --- Service Desk / Help Desk**
- Primo punto di contatto per l'utente
- Registrazione, classificazione e prioritizzazione dell'incidente
- Risoluzione di incidenti noti tramite procedure documentate e knowledge base
- Tasso di risoluzione target: 60-70% degli incidenti
- Competenze: troubleshooting base, conoscenza delle procedure operative, utilizzo degli strumenti di ticketing

**Livello 2 (L2) --- Supporto Tecnico Specializzato**
- Tecnici con competenze approfondite su sistemi specifici
- Analisi diagnostica avanzata
- Risoluzione di incidenti che richiedono accesso amministrativo ai sistemi
- Aree: amministrazione server, networking, database, applicazioni
- Tasso di risoluzione target: 85-90% degli incidenti che arrivano a L2

**Livello 3 (L3) --- Esperti / Architetti**
- Specialisti con competenze profonde su tecnologie specifiche
- Analisi del codice sorgente, debugging avanzato, analisi di packet capture
- Sviluppo di fix e patch personalizzate
- Interazione con il team di sviluppo per bug applicativi

**Vendor / Fornitore Esterno**
- Escalation verso il produttore hardware o software
- Gestione attraverso contratti di supporto (Silver, Gold, Platinum)
- Apertura di case presso il supporto tecnico del vendor
- Tracciamento parallelo nel sistema di ticketing interno

### Processo Major Incident

Un Major Incident e un incidente con il piu alto livello di impatto sul business. Richiede un processo dedicato:

1. **Dichiarazione**: il Major Incident viene dichiarato dal Major Incident Manager o dal Service Desk Manager quando si verificano criteri predefiniti (es. servizio critico completamente non disponibile, impatto su > 50% degli utenti).
2. **Attivazione del team**: viene convocato immediatamente un team dedicato (bridge call) con tutti gli specialisti necessari.
3. **Comunicazione**: viene inviata una comunicazione iniziale a tutti gli stakeholder (management, utenti, clienti) entro 15 minuti dalla dichiarazione.
4. **Aggiornamenti periodici**: comunicazioni di stato ogni 30 minuti fino alla risoluzione.
5. **Risoluzione e conferma**: ripristino del servizio, verifica, conferma.
6. **Post-Incident Review (PIR)**: entro 48 ore dalla risoluzione, viene condotta una revisione formale per identificare cause radice, lezioni apprese e azioni correttive.

### Template Ticket Incidente

```
=== TICKET INCIDENTE ===
ID Ticket:          INC-2026-XXXXX
Data/Ora Apertura:  2026-03-26 08:45:00 CET
Segnalato da:       [Nome Cognome / Sistema Monitoring]
Canale:             [Telefono / Email / Portale / Monitoring]

--- CLASSIFICAZIONE ---
Categoria:          [Hardware | Software | Rete | Sicurezza | Database]
Sottocategoria:     [Server | Workstation | Switch | Firewall | ...]
Servizio Impattato: [Nome del servizio]
CI Coinvolto:       [Configuration Item dal CMDB]

--- PRIORITA ---
Impatto:            [Alto | Medio | Basso]
Urgenza:            [Alta | Media | Bassa]
Priorita:           [P1 | P2 | P3 | P4 | P5]

--- DESCRIZIONE ---
Sintomo:            [Descrizione dettagliata del problema osservato]
Utenti Impattati:   [Numero e/o gruppi di utenti]
Workaround:         [Disponibile Si/No --- descrizione se si]

--- ASSEGNAZIONE ---
Gruppo Assegnato:   [L1 / L2 / L3 / Vendor]
Tecnico Assegnato:  [Nome Cognome]

--- RISOLUZIONE ---
Causa Identificata: [Descrizione della causa]
Soluzione Applicata:[Descrizione dettagliata della soluzione]
Data/Ora Chiusura:  [YYYY-MM-DD HH:MM:SS]
Problema Collegato:  [PRB-XXXXX se applicabile]

--- CONFERMA ---
Confermato da Utente: [Si / No]
Note di Chiusura:     [Eventuali note aggiuntive]
```

### KPI per la Gestione Incidenti

I Key Performance Indicator (KPI) fondamentali per misurare l'efficacia della gestione incidenti sono:

- **MTTR (Mean Time To Resolve)**: tempo medio dalla registrazione dell'incidente alla sua risoluzione. Target: variabile per priorita (vedi tabella sopra).
- **MTTA (Mean Time To Acknowledge)**: tempo medio dalla segnalazione alla presa in carico. Target: < 15 minuti per P1, < 30 minuti per P2.
- **First Call Resolution Rate (FCR)**: percentuale di incidenti risolti al primo contatto dal Service Desk. Target: > 65%.
- **Incident Backlog**: numero di incidenti aperti e non ancora risolti. Un backlog crescente indica un problema di capacita.
- **Reopen Rate**: percentuale di incidenti riaperti dopo la chiusura. Target: < 5%. Un tasso alto indica risoluzioni inadeguate.
- **Customer Satisfaction (CSAT)**: valutazione della soddisfazione dell'utente post-risoluzione. Target: > 4.0/5.0.
- **SLA Compliance Rate**: percentuale di incidenti risolti entro i tempi previsti dall'SLA. Target: > 95%.

### Esempio Pratico

**Scenario**: alle ore 09:15 di lunedi, il sistema di monitoring Zabbix rileva che il server database PostgreSQL `db-prod-01` non risponde piu alle query. Il servizio ERP aziendale diventa inaccessibile per 200 utenti.

1. **Detection**: trigger Zabbix "PostgreSQL connection refused" genera alert.
2. **Logging**: il sistema automatico apre il ticket INC-2026-00142.
3. **Classification**: Categoria=Database, Sottocategoria=PostgreSQL, Servizio=ERP Produzione.
4. **Prioritization**: Impatto=Alto (200 utenti, servizio critico), Urgenza=Alta (nessun workaround) -> **P1 Critico**.
5. **Escalation**: escalation immediata a L2 (DBA team), attivazione procedura Major Incident.
6. **Investigation**: il DBA verifica i log e identifica che il disco del tablespace principale e al 100%. Lo spazio e esaurito per una crescita anomala delle tabelle temporanee.
7. **Resolution**: pulizia delle tabelle temporanee, espansione del volume logico, riavvio controllato di PostgreSQL. Servizio ripristinato alle 09:52.
8. **Closure**: MTTR = 37 minuti. Aperto ticket problema PRB-2026-00089 per investigare la causa della crescita anomala.

---

## Gestione Problemi (Problem Management)

### Definizione e Obiettivo

Un **problema** e la causa o la potenziale causa di uno o piu incidenti. L'obiettivo della gestione problemi e ridurre la probabilita e l'impatto degli incidenti identificando le cause effettive e potenziali degli incidenti e gestendo workaround e known error.

La differenza fondamentale tra gestione incidenti e gestione problemi e temporale e di focus: la gestione incidenti si concentra sul ripristino rapido del servizio (firefighting), la gestione problemi si concentra sull'eliminazione della causa radice (prevenzione).

### Gestione Reattiva vs Proattiva

**Gestione Reattiva dei Problemi:**
- Si attiva dopo che uno o piu incidenti si sono verificati
- Analizza pattern di incidenti ricorrenti
- Identifica la causa radice di incidenti gia avvenuti
- Esempio: dopo il terzo incidente di esaurimento disco sul server database, viene aperto un problema per investigare la causa della crescita anomala

**Gestione Proattiva dei Problemi:**
- Si attiva prima che gli incidenti si verifichino
- Analizza trend e dati di monitoring per identificare potenziali problemi
- Utilizza analisi predittiva e pattern recognition
- Esempio: analizzando i trend di utilizzo disco, si identifica che il server raggiungera il 100% entro 30 giorni e si interviene preventivamente

### Tecniche di Root Cause Analysis (RCA)

**1. I 5 Perche (5 Whys)**

Tecnica semplice e potente: si chiede "perche?" ripetutamente fino a raggiungere la causa radice.

Esempio pratico:
- **Problema**: il server database si e bloccato.
- **Perche 1?** Perche il disco era pieno al 100%.
- **Perche 2?** Perche le tabelle temporanee sono cresciute in modo incontrollato.
- **Perche 3?** Perche una procedura batch non cancella le tabelle temporanee dopo l'uso.
- **Perche 4?** Perche il codice della procedura batch non include la pulizia come step finale.
- **Perche 5?** Perche nella review del codice non era presente un checklist che include la gestione delle risorse temporanee.
- **Causa Radice**: mancanza di standard di coding per la gestione delle risorse temporanee nelle procedure batch.
- **Azione Correttiva**: aggiungere al checklist di code review un punto sulla gestione delle risorse temporanee; implementare un job automatico di pulizia come rete di sicurezza.

**2. Diagramma di Ishikawa (Fishbone / Causa-Effetto)**

Il diagramma a lisca di pesce organizza le possibili cause in categorie:
- **Persone**: competenze, formazione, errori umani, comunicazione.
- **Processi**: procedure mancanti o inadeguate, mancanza di automazione.
- **Tecnologia**: bug software, guasti hardware, incompatibilita, capacita.
- **Ambiente**: temperatura, alimentazione, connettivita, fattori esterni.
- **Dati**: corruzione dati, input errati, migrazione dati.
- **Fornitori**: componenti difettosi, supporto inadeguato, ritardi.

**3. Metodo Kepner-Tregoe**

Approccio strutturato in quattro fasi:
1. **Situation Appraisal**: identificare e separare le preoccupazioni, stabilire le priorita.
2. **Problem Analysis**: descrivere il problema in termini di IS/IS NOT (cosa e/non e, dove e/non e, quando e/non e, quanto e/non e).
3. **Decision Analysis**: valutare le alternative di soluzione in base a criteri pesati.
4. **Potential Problem Analysis**: anticipare i rischi dell'implementazione della soluzione scelta.

### Known Error Database (KEDB)

Il KEDB e un database che contiene tutte le informazioni sui known error --- problemi per i quali e stata identificata la causa radice e per i quali esiste un workaround documentato ma non ancora una fix permanente.

Struttura di un record KEDB:

```
=== KNOWN ERROR ===
ID:                 KE-2026-00045
Problema Collegato: PRB-2026-00089
Data Creazione:     2026-03-26
Stato:              Aperto

Descrizione:        Le procedure batch ERP generano tabelle temporanee
                    nel database PostgreSQL che non vengono eliminate
                    automaticamente al termine dell'esecuzione.

Causa Radice:       Il codice delle procedure batch non include uno
                    step di cleanup delle tabelle temporanee.

Workaround:         Eseguire quotidianamente lo script di pulizia:
                    /opt/scripts/cleanup_temp_tables.sh
                    (schedulato via cron alle 02:00)

Fix Permanente:     Modifica del codice delle procedure batch per
                    includere cleanup automatico. Change Request
                    CHG-2026-00178 in pianificazione.

CI Impattati:       db-prod-01, app-erp-prod
Incidenti Collegati: INC-2026-00142, INC-2026-00098, INC-2026-00067
```

### Workaround vs Fix Permanente

- **Workaround**: soluzione temporanea che riduce o elimina l'impatto del problema senza risolverne la causa radice. E rapido da implementare ma richiede manutenzione continua.
- **Fix Permanente**: soluzione definitiva che elimina la causa radice. Richiede piu tempo e risorse per essere implementata, ma elimina il problema in modo permanente.

La strategia corretta e: implementare il workaround immediatamente per proteggere il servizio, poi pianificare la fix permanente attraverso il processo di change management.

### KPI per la Gestione Problemi

- **Numero di Known Error attivi**: il numero totale di KE aperti nel KEDB. Un numero elevato indica un debito tecnico significativo.
- **Riduzione incidenti ricorrenti**: percentuale di riduzione degli incidenti causati da problemi noti dopo l'implementazione di fix permanenti. Target: -30% annuo.
- **Tempo medio di identificazione causa radice**: dalla apertura del problema alla identificazione della causa radice. Target: < 5 giorni lavorativi per problemi P2.
- **Percentuale di incidenti con problema associato**: quanti incidenti vengono correttamente collegati a un record di problema. Target: > 40%.
- **Backlog problemi**: numero di problemi aperti e non ancora risolti, suddivisi per priorita.

---

## Gestione Cambiamenti (Change Management)

### Definizione e Obiettivo

Un **cambiamento (change)** e l'aggiunta, la modifica o la rimozione di qualsiasi elemento che possa avere un effetto diretto o indiretto sui servizi IT. L'obiettivo della gestione cambiamenti e massimizzare il numero di cambiamenti di successo garantendo che i rischi siano adeguatamente valutati, che i cambiamenti siano autorizzati e che il processo di implementazione sia gestito correttamente.

### Tipi di Cambiamento

**1. Standard Change**
- Cambiamento pre-autorizzato, a basso rischio, ben documentato e ripetitivo.
- Non richiede approvazione individuale per ogni istanza.
- Esempio: aggiunta di memoria RAM a un server seguendo una procedura documentata, reset password utente, creazione mailbox.
- Requisiti: procedura documentata e testata, rischio valutato una volta e accettato, risultato prevedibile.

**2. Normal Change**
- Cambiamento che richiede valutazione, autorizzazione e pianificazione.
- Segue il processo completo con approvazione CAB o del change authority designato.
- Esempio: aggiornamento del firmware di tutti gli switch di rete, migrazione di un database a una nuova versione, installazione di un nuovo servizio.

**3. Emergency Change**
- Cambiamento che deve essere implementato il prima possibile per risolvere un incidente o prevenire un impatto imminente sul business.
- Segue un processo accelerato con approvazione del Emergency CAB (eCAB).
- Esempio: applicazione di una patch di sicurezza critica per una vulnerabilita attivamente sfruttata, fix di emergenza per un bug che causa corruzione dati.
- Attenzione: gli emergency change devono essere l'eccezione, non la regola. Se gli emergency change sono frequenti, il processo di change management ha un problema.

### Change Advisory Board (CAB)

Il CAB e un gruppo di persone che valuta e autorizza i normal change. La composizione tipica include:

- Change Manager (presidente del CAB)
- Rappresentanti dei team tecnici coinvolti
- Rappresentanti del business / service owner
- Rappresentanti della sicurezza IT
- Rappresentanti delle operazioni

Il processo CAB:

1. **Sottomissione**: il change requester sottomette la richiesta di cambiamento con tutta la documentazione.
2. **Revisione tecnica**: valutazione tecnica della fattibilita e dell'impatto.
3. **Valutazione del rischio**: applicazione della matrice di rischio.
4. **Discussione CAB**: presentazione al CAB, domande, chiarimenti.
5. **Decisione**: approvato, respinto, rinviato per maggiori informazioni.
6. **Schedulazione**: inserimento nel change calendar.

### Valutazione del Rischio

La valutazione del rischio per un cambiamento considera molteplici fattori:

**Matrice di Rischio del Cambiamento:**

| Fattore | Peso | Criteri |
|---------|------|---------|
| Complessita tecnica | 25% | Numero di sistemi coinvolti, competenze richieste |
| Impatto potenziale se fallisce | 30% | Numero utenti, criticita del servizio |
| Esperienza precedente | 15% | Cambiamento gia eseguito con successo? |
| Finestra di manutenzione | 10% | Tempo sufficiente per implementazione e rollback? |
| Piano di rollback | 20% | Esiste un piano testato? Tempo di rollback? |

**Livelli di rischio risultanti:**
- **Basso** (score 1-3): approvazione del change manager.
- **Medio** (score 4-6): approvazione del CAB.
- **Alto** (score 7-9): approvazione del CAB + senior management.
- **Critico** (score 10): approvazione del board/CIO.

### Template Change Request

```
=== CHANGE REQUEST ===
ID:                   CHG-2026-00178
Titolo:               Aggiornamento PostgreSQL da 14.8 a 16.2 su db-prod-01
Tipo:                 [Standard | Normal | Emergency]
Richiedente:          [Nome Cognome]
Data Richiesta:       2026-03-26
Stato:                [Draft | In Valutazione | Approvato | Schedulato |
                       In Implementazione | Completato | Rollback | Chiuso]

--- DESCRIZIONE ---
Descrizione:          Aggiornamento della versione di PostgreSQL dal
                      release 14.8 al release 16.2 per beneficiare
                      di miglioramenti di prestazioni, sicurezza e
                      nuove funzionalita.
Motivazione:          PostgreSQL 14 raggiungera l'end-of-life a
                      novembre 2026. Inoltre, la versione 16 include
                      miglioramenti significativi nelle query
                      parallele necessarie per il nuovo modulo ERP.

--- IMPATTO ---
CI Coinvolti:         db-prod-01, app-erp-prod, app-report-prod
Servizi Impattati:    ERP Produzione, Reportistica
Utenti Impattati:     200 utenti ERP, 50 utenti reportistica
Downtime Previsto:    4 ore (sabato 04:00-08:00)

--- VALUTAZIONE RISCHIO ---
Complessita:          Media (upgrade major version)
Impatto se Fallisce:  Alto (servizio ERP non disponibile)
Esperienza:           Si (eseguito su ambiente di staging)
Piano Rollback:       Si (snapshot VM + dump database pre-upgrade)
Tempo Rollback:       45 minuti
Rischio Complessivo:  Medio

--- PIANO DI IMPLEMENTAZIONE ---
Pre-requisiti:
  1. Backup completo del database (verificato)
  2. Snapshot della VM db-prod-01
  3. Test di upgrade completato su staging
  4. Comunicazione agli utenti 5 giorni prima

Passi di Implementazione:
  1. [04:00] Verifica backup notturno completato con successo
  2. [04:15] Creazione snapshot VM
  3. [04:30] Stop applicazioni connesse al database
  4. [04:45] Stop servizio PostgreSQL 14
  5. [05:00] Esecuzione pg_upgrade con --link
  6. [05:30] Verifica integrita dati post-upgrade
  7. [06:00] Start PostgreSQL 16, verifica log errori
  8. [06:15] Esecuzione ANALYZE su tutti i database
  9. [06:45] Start applicazioni, test funzionali
  10. [07:30] Verifica prestazioni, monitoraggio
  11. [08:00] Conferma completamento

--- PIANO DI ROLLBACK ---
Trigger Rollback:     Errori critici durante upgrade, test funzionali
                      falliti, degradazione prestazioni > 20%
Procedura:
  1. Stop PostgreSQL 16
  2. Ripristino snapshot VM
  3. Start PostgreSQL 14
  4. Verifica integrita e funzionamento
  5. Comunicazione agli stakeholder
Tempo stimato:        45 minuti

--- APPROVAZIONE ---
Change Manager:       [Nome] --- [Data] --- [Approvato/Respinto]
CAB:                  [Esito] --- [Data] --- [Note]
```

### Post-Implementation Review (PIR)

Dopo ogni normal e emergency change, si conduce una revisione post-implementazione:

- Il cambiamento e stato implementato come pianificato?
- Ci sono stati problemi imprevisti?
- Il rollback e stato necessario? Se si, ha funzionato?
- I tempi previsti sono stati rispettati?
- Lezioni apprese e azioni di miglioramento.

### Change Calendar

Il change calendar e uno strumento visuale condiviso che mostra tutti i cambiamenti pianificati. Permette di:
- Identificare conflitti tra cambiamenti sulla stessa infrastruttura
- Evitare cambiamenti in periodi critici per il business (chiusure contabili, picchi stagionali)
- Coordinare i cambiamenti tra team diversi
- Definire le finestre di manutenzione (maintenance window)

### Esempi Pratici di Tracking Cambiamenti

Script Bash per registrare i cambiamenti effettuati su un server:

```bash
#!/bin/bash
# /usr/local/bin/log-change.sh
# Script per registrare cambiamenti sul sistema locale

LOGDIR="/var/log/changes"
LOGFILE="${LOGDIR}/changes-$(date +%Y-%m).log"
HOSTNAME=$(hostname -f)
USER=$(whoami)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')

mkdir -p "${LOGDIR}"

if [ -z "$1" ]; then
    echo "Uso: log-change.sh <ID_CHANGE> <DESCRIZIONE>"
    echo "Esempio: log-change.sh CHG-2026-00178 'Upgrade PostgreSQL 14->16'"
    exit 1
fi

CHANGE_ID="$1"
shift
DESCRIPTION="$*"

cat >> "${LOGFILE}" << EOF
---
Timestamp:   ${TIMESTAMP}
Hostname:    ${HOSTNAME}
Change ID:   ${CHANGE_ID}
Operatore:   ${USER}
Descrizione: ${DESCRIPTION}
Kernel:      $(uname -r)
Uptime:      $(uptime -p)
---
EOF

echo "Cambiamento registrato in ${LOGFILE}"
```

Script PowerShell per tracking su sistemi Windows:

```powershell
# Log-Change.ps1
# Script per registrare cambiamenti su sistemi Windows

param(
    [Parameter(Mandatory=$true)]
    [string]$ChangeID,

    [Parameter(Mandatory=$true)]
    [string]$Description,

    [string]$LogPath = "C:\Logs\Changes"
)

$LogFile = Join-Path $LogPath "changes-$(Get-Date -Format 'yyyy-MM').log"

if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

$Entry = @"
---
Timestamp:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')
Hostname:    $($env:COMPUTERNAME)
Change ID:   $ChangeID
Operatore:   $($env:USERNAME)
Descrizione: $Description
OS Version:  $((Get-CimInstance Win32_OperatingSystem).Version)
Uptime:      $((Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime)
---
"@

Add-Content -Path $LogFile -Value $Entry
Write-Host "Cambiamento registrato in $LogFile" -ForegroundColor Green
```

---

## Gestione Configurazione e CMDB

### Definizione e Obiettivo

La gestione della configurazione ha l'obiettivo di garantire che le informazioni accurate e affidabili sulla configurazione dei servizi e sui Configuration Item (CI) che li supportano siano disponibili quando e dove necessario. Il **CMDB (Configuration Management Database)** e il repository centralizzato che contiene queste informazioni.

### Configuration Item (CI)

Un CI e qualsiasi componente che deve essere gestito per erogare un servizio IT. I CI non sono solo asset fisici ma includono:

- **Hardware**: server, switch, router, firewall, storage, workstation, UPS
- **Software**: sistemi operativi, applicazioni, database, middleware, firmware
- **Servizi**: servizi IT composti (es. "Servizio Email", "Servizio ERP")
- **Documenti**: SLA, contratti, procedure operative, architetture
- **Persone e Ruoli**: team di supporto, service owner, fornitori
- **Ambienti**: data center, rack, VLAN, subnet

### Relazioni tra CI

Le relazioni tra CI sono fondamentali per comprendere le dipendenze e valutare l'impatto dei cambiamenti:

- **Runs on**: l'applicazione ERP "runs on" il server app-prod-01.
- **Depends on**: il servizio email "depends on" il server mail-prod-01 e il servizio DNS.
- **Connected to**: il server app-prod-01 "connected to" lo switch sw-core-01.
- **Part of**: il disco SSD da 1TB "part of" il server db-prod-01.
- **Managed by**: il servizio ERP "managed by" il team Application Support.

### Struttura e Data Model del CMDB

Un data model CMDB ben progettato include:

```
CI Base Attributes (comuni a tutti i CI):
  - CI ID (univoco)
  - Nome
  - Tipo/Classe
  - Stato (In uso, In manutenzione, Ritirato, In magazzino)
  - Criticita (Alta, Media, Bassa)
  - Locazione
  - Owner / Responsabile
  - Data creazione / ultima modifica
  - Fornitore
  - Contratto di supporto

Hardware Attributes (aggiuntivi per CI hardware):
  - Marca / Modello
  - Numero di serie
  - Indirizzo IP / MAC Address
  - CPU, RAM, Storage
  - Data installazione
  - Data fine garanzia
  - Rack / Posizione fisica

Software Attributes (aggiuntivi per CI software):
  - Versione
  - Licenza (tipo e scadenza)
  - Piattaforma supportata
  - Data installazione
  - Patch level
  - Dipendenze
```

### Ciclo di Vita del CI

Ogni CI attraversa un ciclo di vita:

1. **Pianificazione**: il CI viene identificato come necessario (es. nuovo server per progetto).
2. **Acquisizione/Sviluppo**: il CI viene acquistato, sviluppato o configurato.
3. **Registrazione nel CMDB**: inserimento di tutti gli attributi e le relazioni.
4. **In Uso / Operativo**: il CI e in produzione e viene monitorato.
5. **Manutenzione**: aggiornamenti, patch, riparazioni vengono tracciati.
6. **Dismissione**: il CI viene ritirato dal servizio.
7. **Smaltimento**: il CI viene fisicamente smaltito secondo le normative (RAEE per hardware).

### Discovery e Riconciliazione

La discovery automatica e il processo di scansione della rete e dei sistemi per identificare automaticamente i CI e i loro attributi. La riconciliazione e il processo di confronto tra i dati scoperti automaticamente e i dati registrati nel CMDB, identificando discrepanze.

Strumenti e metodi di discovery:
- **Network scanning**: Nmap, scansione SNMP per dispositivi di rete.
- **Agent-based**: agenti installati sui server che riportano configurazione e cambiamenti.
- **Agentless**: WMI (Windows), SSH (Linux), API per dispositivi di rete.
- **Cloud API**: AWS Config, Azure Resource Graph, Google Cloud Asset Inventory.

### Panoramica degli Strumenti CMDB

| Strumento | Tipo | Punti di Forza | Licenza |
|-----------|------|----------------|---------|
| GLPI | CMDB + ITSM | Open source, completo, plugin ecosystem | GPL |
| NetBox | DCIM + IPAM | Eccellente per infrastruttura di rete e datacenter | Apache 2.0 |
| i-doit | CMDB | CMDB puro molto flessibile, documentazione IT | AGPL / Commercial |
| ServiceNow CMDB | Enterprise CMDB | Soluzione enterprise completa, discovery avanzata | Commercial |
| Ralph | CMDB + Asset | Asset management data center, semplice | Apache 2.0 |
| iTop | CMDB + ITSM | Buon modello dati, grafico delle dipendenze | AGPL |

### Esempio Pratico: Setup GLPI

GLPI (Gestionnaire Libre de Parc Informatique) e una delle soluzioni open source piu complete per CMDB e ITSM. Ecco un esempio di setup:

```bash
# Installazione GLPI su Ubuntu/Debian con Docker Compose

# Creare la directory del progetto
mkdir -p /opt/glpi && cd /opt/glpi

# docker-compose.yml
cat > docker-compose.yml << 'COMPOSE'
version: '3.8'

services:
  mariadb:
    image: mariadb:10.11
    container_name: glpi-db
    restart: unless-stopped
    environment:
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASS}
      MARIADB_DATABASE: glpi
      MARIADB_USER: glpi
      MARIADB_PASSWORD: ${DB_GLPI_PASS}
    volumes:
      - glpi_db:/var/lib/mysql
    networks:
      - glpi-net

  glpi:
    image: diouxx/glpi:latest
    container_name: glpi-app
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      TIMEZONE: Europe/Rome
    volumes:
      - glpi_data:/var/www/html/glpi
    depends_on:
      - mariadb
    networks:
      - glpi-net

volumes:
  glpi_db:
  glpi_data:

networks:
  glpi-net:
COMPOSE

# Creare il file .env
cat > .env << 'ENV'
DB_ROOT_PASS=ChangeMeRootPassword2026!
DB_GLPI_PASS=ChangeMeGlpiPassword2026!
ENV

# Avviare i container
docker compose up -d
```

Una volta installato GLPI, la configurazione del CMDB include:
1. Definizione delle categorie di CI (Computer, Dispositivi di rete, Software, ecc.)
2. Personalizzazione dei campi per ogni categoria
3. Configurazione dell'agente di inventario (GLPI Agent, ex FusionInventory)
4. Importazione iniziale degli asset esistenti
5. Definizione delle relazioni tra CI
6. Configurazione dei report e delle dashboard

---

## Gestione Livelli di Servizio (SLA)

### SLA vs SLO vs SLI

Questi tre concetti sono spesso confusi ma hanno significati distinti:

- **SLA (Service Level Agreement)**: un accordo formale tra il fornitore del servizio e il cliente che definisce il livello di servizio atteso. E un documento contrattuale con implicazioni legali e commerciali.
- **SLO (Service Level Objective)**: un obiettivo specifico e misurabile all'interno dell'SLA. E il target che si cerca di raggiungere. Esempio: "disponibilita del servizio >= 99.9%".
- **SLI (Service Level Indicator)**: la metrica effettivamente misurata che indica il livello di servizio reale. E il dato numerico. Esempio: "disponibilita misurata nel mese di febbraio: 99.95%".

La relazione e: gli **SLI** misurano le prestazioni reali, gli **SLO** definiscono gli obiettivi target, gli **SLA** formalizzano gli accordi con il cliente includendo penali e condizioni.

### Metriche SLA Comuni

**Disponibilita (Availability):**
La metrica piu comune e fondamentale. Si calcola come:

```
Disponibilita (%) = ((Tempo Totale - Tempo di Downtime) / Tempo Totale) * 100
```

**Tabella di Disponibilita e Downtime Corrispondente:**

| Disponibilita | Downtime Annuo | Downtime Mensile | Downtime Settimanale | Classe |
|---------------|---------------|-----------------|---------------------|--------|
| 99.0% | 3 giorni 15h 36m | 7h 18m 18s | 1h 40m 48s | Due nove |
| 99.5% | 1 giorno 19h 48m | 3h 39m 9s | 50m 24s | |
| 99.9% | 8h 45m 36s | 43m 49.7s | 10m 4.8s | Tre nove |
| 99.95% | 4h 22m 48s | 21m 54.9s | 5m 2.4s | |
| 99.99% | 52m 33.6s | 4m 22.9s | 1m 0.5s | Quattro nove |
| 99.999% | 5m 15.4s | 26.3s | 6.0s | Cinque nove |

**Altre metriche comuni:**

| Metrica | Descrizione | Esempio SLO |
|---------|-------------|-------------|
| Tempo di risposta incidente | Tempo dalla segnalazione alla presa in carico | P1: 15 min, P2: 30 min |
| Tempo di risoluzione incidente | Tempo dalla segnalazione alla risoluzione | P1: 1h, P2: 4h |
| Tempo di risposta applicazione | Latenza percepita dall'utente | < 2 secondi per il 95% delle richieste |
| Throughput | Capacita di elaborazione | > 1000 transazioni/minuto |
| RPO (Recovery Point Objective) | Massima perdita di dati accettabile | < 1 ora |
| RTO (Recovery Time Objective) | Tempo massimo di ripristino dopo un disastro | < 4 ore |

### Esempio di Calcolo SLA

**Scenario**: nel mese di marzo 2026, il servizio email ha avuto i seguenti downtime:
- 12 marzo: 45 minuti (manutenzione pianificata non in finestra)
- 19 marzo: 2 ore 15 minuti (guasto hardware)
- 25 marzo: 30 minuti (aggiornamento di emergenza)

Tempo totale del mese: 31 giorni x 24 ore x 60 minuti = 44.640 minuti
Downtime totale: 45 + 135 + 30 = 210 minuti

Nota: la manutenzione pianificata nelle finestre concordate generalmente non viene conteggiata come downtime. In questo caso la manutenzione del 12 marzo e avvenuta fuori dalla finestra concordata, quindi viene conteggiata.

```
Disponibilita = ((44.640 - 210) / 44.640) * 100 = 99.53%
```

Se l'SLO e 99.9%, il servizio ha violato l'SLA. Il downtime consentito per 99.9% mensile e circa 44 minuti, mentre il downtime effettivo e stato di 210 minuti.

### Strutture di Penale e Escalation

Le penali per violazione SLA sono tipicamente strutturate a livelli crescenti:

| Livello Violazione | Condizione | Penale / Azione |
|--------------------|-----------|--------------------|
| Warning | SLI < SLO per 1 periodo | Notifica al service owner, piano correttivo |
| Livello 1 | SLI < SLO per 2 periodi consecutivi | Credito 5% del canone mensile |
| Livello 2 | SLI < SLO per 3 periodi consecutivi | Credito 10% del canone mensile, escalation a management |
| Livello 3 | SLI < (SLO - 1%) | Credito 20% del canone mensile, review contrattuale |
| Critico | SLI < (SLO - 5%) | Diritto di risoluzione contratto, penale contrattuale |

### Template Report SLA

```
=== REPORT SLA MENSILE ===
Periodo:            Marzo 2026
Servizio:           Servizio ERP Produzione
Service Owner:      [Nome Cognome]
Data Emissione:     2026-04-02

--- DISPONIBILITA ---
SLO Target:         99.9%
SLI Misurato:       99.72%
Stato:              NON CONFORME
Downtime Totale:    2h 05m
Downtime Consentito:43m 49s
Downtime Eccedente: 1h 21m 11s

--- INCIDENTI DEL PERIODO ---
| ID | Data | Durata | Causa | Impatto |
|-----|------|--------|-------|---------|
| INC-142 | 12/03 | 45m | Disco pieno DB | Servizio non disponibile |
| INC-156 | 19/03 | 50m | Bug applicativo | Funzione ordini KO |
| INC-167 | 25/03 | 30m | Patch emergenza | Riavvio pianificato |

--- PRESTAZIONI ---
| Metrica | SLO | SLI | Stato |
|---------|-----|-----|-------|
| Disponibilita | 99.9% | 99.72% | NON CONFORME |
| Tempo risposta P1 | 15 min | 12 min | CONFORME |
| Tempo risoluzione P1 | 1h | 45 min | CONFORME |
| Tempo risoluzione P2 | 4h | 3h 20m | CONFORME |
| First Call Resolution | >65% | 72% | CONFORME |

--- AZIONI CORRETTIVE ---
1. PRB-2026-00089: Investigazione crescita anomala tabelle
   temporanee - fix pianificata per CHG-2026-00178
2. Implementazione monitoring proattivo spazio disco
   con soglie di warning al 80% e critico al 90%
3. Review processo di patching per ridurre downtime

--- NOTE ---
Penale applicata: credito 5% sul canone di marzo per
violazione SLO disponibilita (primo periodo di non conformita).
```

---

## Documentazione e Procedure Standard

### Tipi di Documentazione

La documentazione operativa IT si articola in diverse tipologie, ciascuna con uno scopo specifico:

**1. SOP (Standard Operating Procedure)**
Procedura dettagliata passo-passo per eseguire un'attivita operativa standard. Deve essere sufficientemente dettagliata da permettere a un tecnico con competenze base di eseguire l'operazione.

Caratteristiche: linguaggio chiaro e non ambiguo, passi numerati, screenshot dove utile, precondizioni e postcondizioni esplicite, punti di verifica.

Esempio titoli SOP:
- SOP-001: Procedura di backup giornaliero del database
- SOP-002: Procedura di aggiunta utente al dominio Active Directory
- SOP-003: Procedura di sostituzione disco su server Dell PowerEdge
- SOP-004: Procedura di restart controllato del cluster applicativo

**2. Runbook**
Raccolta di procedure operative specifiche per la gestione di un sistema o servizio. A differenza della SOP (che copre una singola operazione), il runbook e una guida completa che copre tutte le operazioni quotidiane, le risposte agli alert e le procedure di troubleshooting per un sistema specifico.

Struttura tipo di un runbook:
- Panoramica del sistema/servizio
- Architettura e dipendenze
- Procedure di startup/shutdown
- Procedure di backup e restore
- Risposte agli alert di monitoring
- Procedure di troubleshooting comuni
- Contatti e escalation
- Storico delle modifiche

**3. Knowledge Base (KB)**
Archivio di articoli di conoscenza organizzati per facilitare la ricerca e il riutilizzo. Ogni articolo KB risolve un problema specifico e documenta la soluzione.

Struttura articolo KB:
- ID e titolo descrittivo
- Sintomo/problema
- Causa
- Soluzione
- Articoli correlati
- Data di ultima verifica

**4. Diagrammi di Architettura**
Rappresentazioni visuali dell'infrastruttura IT, delle reti, dei flussi di dati e delle dipendenze tra componenti. Devono essere mantenuti aggiornati e versionati.

Tipi di diagrammi:
- Topologia di rete (fisico e logico)
- Architettura applicativa
- Flussi di dati
- Diagramma delle dipendenze dei servizi
- Layout fisico del datacenter (rack diagram)

### Ciclo di Vita della Documentazione

La documentazione ha un proprio ciclo di vita che deve essere gestito:

1. **Creazione**: il documento viene scritto seguendo il template appropriato.
2. **Revisione**: un peer review verifica accuratezza tecnica, chiarezza e completezza.
3. **Approvazione**: il documento viene approvato dal responsabile del team/processo.
4. **Pubblicazione**: il documento viene reso disponibile sulla piattaforma di documentazione.
5. **Utilizzo e Feedback**: il documento viene utilizzato e si raccoglie feedback.
6. **Revisione Periodica**: ogni documento ha una data di revisione (tipicamente ogni 6-12 mesi). Alla scadenza, viene verificato e aggiornato se necessario.
7. **Archiviazione/Ritiro**: quando il documento non e piu applicabile (es. sistema dismesso), viene archiviato con annotazione del motivo.

### Template SOP

```
=== STANDARD OPERATING PROCEDURE ===
ID:             SOP-XXX
Titolo:         [Titolo descrittivo dell'operazione]
Versione:       1.0
Data Creazione: 2026-03-26
Ultima Modifica:2026-03-26
Autore:         [Nome Cognome]
Approvato da:   [Nome Cognome]
Prossima Review:2026-09-26

--- SCOPO ---
[Descrizione dello scopo della procedura]

--- AMBITO ---
[A quali sistemi/servizi si applica]

--- PRECONDIZIONI ---
- [Cosa deve essere verificato prima di iniziare]
- [Accessi necessari]
- [Strumenti richiesti]

--- PROCEDURA ---
1. [Passo 1 --- descrizione dettagliata]
   Verifica: [come verificare che il passo sia completato]

2. [Passo 2 --- descrizione dettagliata]
   Verifica: [come verificare che il passo sia completato]

3. [Passo N...]

--- POSTCONDIZIONI ---
- [Stato atteso del sistema dopo la procedura]
- [Verifiche finali da eseguire]

--- GESTIONE ERRORI ---
- Se al passo X si verifica [errore]: [azione correttiva]
- In caso di problemi non previsti: contattare [ruolo/persona]

--- RIFERIMENTI ---
- [Link a documentazione correlata]
- [KB articles collegati]

--- STORICO MODIFICHE ---
| Versione | Data | Autore | Descrizione |
|----------|------|--------|-------------|
| 1.0 | 2026-03-26 | [Nome] | Creazione iniziale |
```

### Template Runbook

```
=== RUNBOOK ===
Sistema:         [Nome del sistema/servizio]
Versione:        2.1
Ultima Modifica: 2026-03-26
Responsabile:    [Nome Cognome / Team]

--- PANORAMICA ---
[Descrizione del sistema, suo scopo, utenti]

--- ARCHITETTURA ---
[Diagramma o descrizione dell'architettura]
Componenti principali:
- [Componente 1]: [descrizione, hostname, IP]
- [Componente 2]: [descrizione, hostname, IP]

Dipendenze:
- [Servizio/sistema da cui dipende]
- [Database, rete, storage]

--- OPERAZIONI QUOTIDIANE ---

Verifica Stato del Servizio:
  $ systemctl status nome-servizio
  $ curl -s http://localhost:8080/health | jq .

Verifica Log:
  $ journalctl -u nome-servizio --since "1 hour ago" --no-pager
  $ tail -100 /var/log/app/application.log

--- RISPOSTA AGLI ALERT ---

Alert: "CPU Usage > 90%"
  1. Verificare i processi: $ top -bn1 | head -20
  2. Se processo anomalo: $ kill -15 <PID>
  3. Se carico legittimo: valutare scaling

Alert: "Disk Usage > 85%"
  1. Verificare utilizzo: $ df -h
  2. Identificare file grandi: $ du -sh /var/log/* | sort -rh | head
  3. Eseguire pulizia log: $ /opt/scripts/cleanup-logs.sh
  4. Se insufficiente: espandere volume

--- PROCEDURE DI TROUBLESHOOTING ---
[Albero decisionale per i problemi piu comuni]

--- CONTATTI ---
| Ruolo | Nome | Telefono | Email |
|-------|------|----------|-------|
| Service Owner | [Nome] | [Tel] | [Email] |
| DBA | [Nome] | [Tel] | [Email] |
| Vendor Support | [Azienda] | [Tel] | [Case Portal] |
```

### Piattaforme di Documentazione

| Piattaforma | Tipo | Punti di Forza | Ideale Per |
|-------------|------|----------------|------------|
| Confluence | Wiki enterprise | Integrazione Jira, ricerca potente | Aziende medio-grandi |
| BookStack | Wiki open source | Semplice, organizzato per libri/capitoli | PMI, team tecnici |
| Wiki.js | Wiki open source | Moderno, supporto Git, Markdown | Team DevOps |
| MkDocs/Material | Static site + Git | Versionato, docs-as-code | Documentazione tecnica |
| GitBook | Documentazione | Elegante, facile da usare | Documentazione pubblica |
| Notion | Workspace | Versatile, collaborativo | Team piccoli e agili |
| MediaWiki | Wiki | Stessa piattaforma di Wikipedia | Organizzazioni grandi |

### Best Practice di Knowledge Management

- **Write It Down**: se la soluzione a un problema non e documentata, scriverla immediatamente dopo averla trovata. Ogni incidente risolto e un'opportunita per creare un articolo KB.
- **Keep It Simple**: documentazione chiara e concisa. Usare elenchi puntati, formattazione coerente, evitare gergo non necessario.
- **Single Source of Truth**: evitare duplicazioni. Ogni informazione deve avere un'unica fonte autorevole. Link ad essa, non copiarla.
- **Version Control**: utilizzare il versionamento per tracciare le modifiche. Docs-as-code (Markdown in Git) e un approccio eccellente.
- **Review Cycle**: ogni documento ha una data di scadenza per la revisione. Documenti non revisionati diventano inaffidabili.
- **Accessible**: la documentazione deve essere facilmente trovabile e accessibile. Una buona struttura e una ricerca efficace sono essenziali.

---

## Miglioramento Continuo (CSI)

### Il Ciclo Plan-Do-Check-Act (PDCA)

Il ciclo PDCA, noto anche come ciclo di Deming, e il motore del miglioramento continuo:

**Plan (Pianificare)**
- Identificare l'area di miglioramento basandosi su dati e metriche.
- Definire obiettivi SMART (Specifici, Misurabili, Raggiungibili, Rilevanti, Temporizzati).
- Analizzare la situazione attuale (baseline).
- Pianificare le azioni di miglioramento.
- Esempio: "Ridurre l'MTTR per incidenti P1 da 60 minuti a 30 minuti entro 6 mesi."

**Do (Fare)**
- Implementare le azioni pianificate su scala ridotta o in un ambiente controllato.
- Documentare tutto cio che avviene durante l'implementazione.
- Raccogliere dati per la fase successiva.
- Esempio: implementare un nuovo runbook per i 5 scenari di incidente P1 piu frequenti, formare il team L1, testare per 1 mese.

**Check (Verificare)**
- Confrontare i risultati ottenuti con gli obiettivi definiti.
- Analizzare i dati raccolti durante la fase Do.
- Identificare gap e deviazioni.
- Esempio: dopo 1 mese, l'MTTR per P1 e sceso a 42 minuti (miglioramento del 30%, ma non ancora al target di 30 minuti).

**Act (Agire)**
- Se il miglioramento ha avuto successo: standardizzare e implementare su larga scala.
- Se il miglioramento non ha raggiunto l'obiettivo: analizzare le cause e avviare un nuovo ciclo.
- Condividere le lezioni apprese.
- Esempio: estendere l'approccio runbook a tutti gli scenari di incidente, aggiungere automazione per gli scenari piu comuni.

### Miglioramento Basato sulle Metriche

Il miglioramento continuo richiede metriche solide. Le metriche devono essere:

**Metriche di Processo:**
- MTTR, MTTA, FCR (gestione incidenti)
- Numero di incidenti per categoria, trend mensile
- Percentuale di cambiamenti riusciti al primo tentativo
- Compliance SLA per servizio
- Backlog di problemi e known error

**Metriche Operative:**
- Disponibilita dei servizi
- Tempo di risposta delle applicazioni
- Utilizzo delle risorse (CPU, RAM, disco, rete)
- Numero e gravita delle vulnerabilita aperte
- Frequenza e successo dei backup

**Metriche di Business:**
- Costo per incidente
- Costo del downtime per ora
- Soddisfazione utente (CSAT, NPS)
- Produttivita del team IT (incidenti risolti per tecnico)

### Post-Incident Review e Blameless Post-Mortem

La Post-Incident Review (PIR), o blameless post-mortem, e un'analisi strutturata condotta dopo un incidente significativo. L'obiettivo e imparare dall'incidente, non trovare colpevoli.

Principi del blameless post-mortem:
- **Nessuna colpa individuale**: il focus e sui processi e i sistemi, non sulle persone. Se un operatore ha commesso un errore, la domanda e: "Perche il sistema ha permesso che questo errore avesse conseguenze?".
- **Trasparenza totale**: tutti i dettagli dell'incidente sono condivisi apertamente.
- **Focus sulle azioni**: la review deve produrre azioni concrete e misurabili.
- **Tempestivita**: condurre la review entro 48-72 ore dall'incidente, quando i ricordi sono freschi.

Struttura della Post-Incident Review:

```
=== POST-INCIDENT REVIEW ===
Incidente:       INC-2026-00142
Data Review:     2026-03-28
Facilitatore:    [Nome Cognome]
Partecipanti:    [Lista partecipanti]

--- TIMELINE ---
08:45 - Alert Zabbix: PostgreSQL connection refused
08:47 - Service Desk registra INC-2026-00142, P1
08:48 - Escalation a L2 (DBA team)
08:52 - DBA in conferenza, inizia investigazione
09:05 - Identificato: disco tablespace al 100%
09:15 - Pulizia tabelle temporanee iniziata
09:35 - PostgreSQL riavviato, verifica integrita
09:52 - Servizio ripristinato, confermato da utenti

--- COSA HA FUNZIONATO ---
- Alert di monitoring ha rilevato il problema in 2 minuti
- Escalation rapida ed efficace
- DBA ha identificato la causa in 13 minuti
- Comunicazione agli stakeholder tempestiva

--- COSA NON HA FUNZIONATO ---
- Monitoring dello spazio disco non aveva soglie
  preventive (mancava alert al 80% e 90%)
- Le procedure batch non includono cleanup delle
  tabelle temporanee
- Il runbook PostgreSQL non copriva questo scenario

--- AZIONI CORRETTIVE ---
| ID | Azione | Responsabile | Scadenza | Stato |
|----|--------|-------------|----------|-------|
| 1 | Configurare alert Zabbix per disco al 80% e 90% | Ops Team | 2026-04-02 | In corso |
| 2 | Fix codice batch per cleanup tabelle temp | Dev Team | 2026-04-15 | Pianificato |
| 3 | Aggiornare runbook PostgreSQL | DBA Team | 2026-04-05 | In corso |
| 4 | Implementare job cron pulizia come safety net | DBA Team | 2026-04-02 | Completato |
| 5 | Review di tutti i monitoring soglie disco | Ops Team | 2026-04-10 | Pianificato |

--- LEZIONI APPRESE ---
1. Il monitoring reattivo (alert quando il servizio e
   gia impattato) non e sufficiente. Servono soglie
   preventive che permettano di intervenire prima.
2. Le procedure batch devono gestire le risorse
   temporanee in modo esplicito (principio di
   resource cleanup).
3. I runbook devono essere testati regolarmente
   e aggiornati con gli scenari reali.
```

### Maturity Model Assessment

Un modello di maturita permette di valutare il livello attuale delle pratiche IT e definire un percorso di miglioramento:

| Livello | Nome | Caratteristiche |
|---------|------|-----------------|
| 1 | Iniziale | Processi ad hoc, reattivi. Nessuna documentazione. I risultati dipendono dalle competenze individuali. |
| 2 | Ripetibile | Processi base definiti. Documentazione essenziale. Si riesce a ripetere i successi passati. |
| 3 | Definito | Processi documentati, standardizzati e integrati. Formazione del personale. Metriche base. |
| 4 | Gestito | Processi misurati quantitativamente. Decisioni basate sui dati. Miglioramento proattivo. |
| 5 | Ottimizzato | Focus sul miglioramento continuo. Automazione avanzata. Innovazione sistematica. |

Per ogni practice ITIL, si valuta il livello attuale e si definisce il livello target:

```
Practice                  | Attuale | Target 12 mesi | Gap
--------------------------|---------|----------------|-----
Incident Management       |    3    |       4        |  1
Problem Management        |    2    |       3        |  1
Change Management         |    2    |       3        |  1
Configuration Management  |    1    |       3        |  2
Service Level Management  |    2    |       3        |  1
Monitoring                |    3    |       4        |  1
Knowledge Management      |    1    |       2        |  1
Continual Improvement     |    1    |       3        |  2
```

### Esempi Pratici di Miglioramento

**Esempio 1: Riduzione degli incidenti ricorrenti**
- **Situazione attuale**: 40% degli incidenti mensili sono ricorrenti (stesso sintomo, stessa causa).
- **Obiettivo**: ridurre gli incidenti ricorrenti al 15% entro 6 mesi.
- **Azioni**: per ogni incidente ricorrente, aprire un ticket di problema; condurre RCA; implementare fix permanenti o workaround documentati; alimentare il KEDB.
- **Risultato dopo 6 mesi**: incidenti ricorrenti ridotti al 18% (obiettivo quasi raggiunto). Nuovo ciclo PDCA per raggiungere il 15%.

**Esempio 2: Automazione patch management**
- **Situazione attuale**: le patch vengono applicate manualmente, processo che richiede 3 giorni lavorativi per ciclo e frequenti errori.
- **Obiettivo**: automatizzare il 90% del processo di patching entro 3 mesi.
- **Azioni**: implementare Ansible per l'automazione; creare playbook per ogni tipo di sistema; testare in staging; implementazione graduale in produzione.
- **Risultato**: tempo di patching ridotto a 4 ore, errori ridotti del 95%, compliance patch migliorata dal 72% al 98%.

---

## Best Practices

Le seguenti best practice rappresentano principi consolidati per l'eccellenza nella manutenzione IT:

**1. Documentare tutto, ma in modo intelligente**
La documentazione deve essere utile, non burocratica. Ogni procedura documentata deve avere un proprietario e una data di revisione. Utilizzare l'approccio docs-as-code (Markdown versionato in Git) per mantenere la documentazione vicino al codice e all'infrastruttura. Se una procedura non viene aggiornata da piu di 12 mesi, e probabilmente obsoleta.

**2. Automatizzare le operazioni ripetitive**
Ogni operazione eseguita manualmente piu di tre volte deve essere candidata all'automazione. L'automazione non solo riduce gli errori e il tempo di esecuzione, ma crea implicitamente documentazione eseguibile. Strumenti come Ansible, Puppet, Chef, Terraform e script Bash/PowerShell sono fondamentali.

**3. Misurare prima di ottimizzare**
Non si puo migliorare cio che non si misura. Prima di implementare qualsiasi cambiamento, stabilire una baseline misurabile. Definire KPI chiari per ogni processo e monitorarli costantemente. Le decisioni devono essere basate sui dati, non sulle percezioni.

**4. Implementare il monitoring proattivo**
Non aspettare che gli utenti segnalino un problema. Implementare monitoring a livello di infrastruttura (CPU, RAM, disco, rete), applicazione (tempi di risposta, errori, throughput) e business (transazioni completate, SLA compliance). Configurare soglie di warning prima delle soglie critiche per permettere l'intervento preventivo.

**5. Gestire i cambiamenti con disciplina**
Ogni modifica all'infrastruttura di produzione deve passare attraverso il processo di change management, anche le modifiche "piccole". Le statistiche mostrano che oltre il 70% degli incidenti sono causati da cambiamenti non gestiti. Un processo leggero ma strutturato e meglio di nessun processo.

**6. Costruire e mantenere il CMDB**
Un CMDB aggiornato e la base per gestione incidenti efficace (sapere cosa e impattato), change management informato (conoscere le dipendenze) e pianificazione della capacita. Iniziare con i CI critici e espandersi gradualmente. Automatizzare la discovery per mantenerlo aggiornato.

**7. Investire nella formazione del team**
I framework e gli strumenti sono inutili se il team non ha le competenze per utilizzarli. Pianificare formazione regolare su tecnologie, processi e soft skill (comunicazione, problem solving). Le certificazioni ITIL, CompTIA, vendor-specific sono investimenti con ritorno misurabile.

**8. Praticare la gestione proattiva dei problemi**
Non limitarsi a spegnere incendi. Dedicare tempo all'analisi dei trend, alla identificazione proattiva dei potenziali problemi e alla eliminazione delle cause radice. Un'ora investita in analisi proattiva puo risparmiare giorni di firefighting reattivo.

**9. Stabilire SLA realistici e misurabili**
Definire SLA che siano raggiungibili con le risorse disponibili. Un SLA al 99.99% con un team di 3 persone e un datacenter singolo non e credibile. Meglio un SLA al 99.9% rispettato costantemente che un 99.99% frequentemente violato. Misurare e comunicare regolarmente i risultati.

**10. Adottare un approccio iterativo all'implementazione**
Non cercare di implementare tutti i processi ITIL contemporaneamente. Iniziare con gestione incidenti (il piu immediato nel valore), poi aggiungere problem management, change management e cosi via. Ogni iterazione deve produrre valore tangibile prima di passare alla successiva.

---

## Troubleshooting

### Problemi Comuni nell'Implementazione dei Framework

**Problema: Resistenza al cambiamento da parte del team**
- **Sintomo**: il team ignora i nuovi processi, continua a lavorare "come prima", lamentele sulla burocrazia.
- **Causa**: mancanza di coinvolgimento nella fase di pianificazione, percezione che i nuovi processi rallentino il lavoro, assenza di comunicazione sui benefici.
- **Soluzione**: coinvolgere il team nella definizione dei processi fin dall'inizio. Dimostrare i benefici con dati concreti (es. "con il nuovo processo abbiamo ridotto l'MTTR del 30%"). Iniziare con processi semplici e leggeri, poi evolvere. Formare adeguatamente e supportare durante la transizione. Celebrare i successi.

**Problema: Processi troppo burocratici che rallentano le operazioni**
- **Sintomo**: un change request semplice richiede 2 settimane di approvazioni, i tecnici aggirano il processo per le urgenze, backlog di change requests.
- **Causa**: processo non differenziato per tipo/rischio di cambiamento, troppi livelli di approvazione, mancanza di standard change pre-autorizzati.
- **Soluzione**: implementare i tre tipi di change (standard, normal, emergency). Creare un catalogo di standard change pre-autorizzati per le operazioni piu comuni. Semplificare il processo di approvazione per i cambiamenti a basso rischio. Delegare l'autorita di approvazione ai livelli appropriati.

**Problema: CMDB non aggiornato e inaffidabile**
- **Sintomo**: le informazioni nel CMDB non corrispondono alla realta, il team non consulta il CMDB, decisioni prese su dati errati.
- **Causa**: inserimento manuale dei dati senza verifica, mancanza di processi di aggiornamento, nessuna integrazione con discovery automatica.
- **Soluzione**: implementare la discovery automatica per aggiornare il CMDB. Integrare gli aggiornamenti CMDB nel processo di change management (ogni change deve aggiornare il CMDB). Eseguire audit periodici per verificare l'accuratezza. Iniziare con i CI critici, non cercare di catalogare tutto immediatamente.

**Problema: Knowledge base vuota o con contenuti obsoleti**
- **Sintomo**: il team non trova soluzioni nella KB, documenta le soluzioni su fogli personali o post-it, incidenti risolti vengono risolti di nuovo da zero.
- **Causa**: scrivere nella KB non e parte del processo, mancanza di tempo dedicato alla documentazione, piattaforma di KB poco usabile.
- **Soluzione**: inserire la creazione/aggiornamento dell'articolo KB come step obbligatorio nella chiusura dell'incidente. Dedicare tempo settimanale alla documentazione (es. "Documentation Friday" --- un'ora ogni venerdi). Scegliere una piattaforma di KB semplice e veloce da usare. Misurare e premiare la contribuzione alla KB.

**Problema: SLA definiti ma non misurati**
- **Sintomo**: gli SLA esistono nel contratto ma nessuno sa se vengono rispettati, mancanza di report periodici, sorpresa quando un cliente lamenta la violazione.
- **Causa**: mancanza di strumenti di misurazione, SLA definiti in modo non misurabile, nessun processo di reporting.
- **Soluzione**: per ogni SLO, definire chiaramente come viene misurato l'SLI corrispondente. Implementare monitoring e reporting automatizzati. Generare e distribuire report SLA mensili. Includere l'analisi SLA nelle revisioni periodiche del servizio.

**Problema: Escalation inefficace e incidenti che "rimbalzano" tra i team**
- **Sintomo**: gli incidenti vengono passati da un team all'altro senza risoluzione, tempi di risoluzione lunghi, frustrazione degli utenti.
- **Causa**: matrice di escalation non chiara, competenze non mappate correttamente, mancanza di ownership degli incidenti.
- **Soluzione**: definire una matrice di escalation chiara e documentata con criteri oggettivi. Assegnare un "incident owner" che mantiene la responsabilita end-to-end anche durante le escalation. Implementare timer di escalation automatici nel sistema di ticketing. Condurre review periodiche delle escalation per identificare pattern e migliorare l'instradamento.

**Problema: Mancanza di visibilita sullo stato dei servizi**
- **Sintomo**: il management non sa quali servizi hanno problemi, le decisioni vengono prese senza dati, impossibile dimostrare il valore dell'IT.
- **Causa**: mancanza di dashboard e reporting, dati dispersi in piu sistemi, nessuna aggregazione delle metriche.
- **Soluzione**: implementare una dashboard operativa (Grafana, Datadog, ServiceNow) che aggreghi le metriche chiave. Creare report settimanali/mensili per il management con KPI in formato comprensibile. Adottare un approccio "service-centric" mostrando lo stato di salute di ogni servizio, non dei singoli componenti tecnici.

**Problema: Emergency change troppo frequenti**
- **Sintomo**: piu del 20% dei cambiamenti sono classificati come emergency, il processo standard viene aggirato routinariamente.
- **Causa**: pianificazione insufficiente, mancanza di manutenzione preventiva, rilasci software di scarsa qualita, pressione del business per accelerare i tempi.
- **Soluzione**: analizzare le cause degli emergency change e implementare azioni preventive. Rafforzare i processi di testing e quality assurance prima dei rilasci. Pianificare finestre di manutenzione regolari per ridurre la necessita di interventi d'emergenza. Definire criteri stringenti per la classificazione come emergency (solo situazioni che impattano attivamente il business o la sicurezza). Tracciare e revisionare tutti gli emergency change per identificare pattern.

---

## COBIT 2019 --- Governance IT Approfondita

### Architettura del Framework COBIT

COBIT (Control Objectives for Information and Related Technologies) e il framework di governance IT sviluppato da ISACA. A differenza di ITIL, che si concentra sulla gestione operativa dei servizi IT, COBIT opera a livello strategico, fornendo un modello per allineare l'IT agli obiettivi di business, gestire i rischi e garantire la conformita normativa. La versione 2019 rappresenta un'evoluzione significativa, introducendo un approccio modulare e configurabile che permette alle organizzazioni di adattare il framework alle proprie esigenze specifiche.

COBIT 2019 si basa su sei principi fondamentali del sistema di governance:

1. **Soddisfare le esigenze degli stakeholder**: ogni decisione IT deve essere ricondotta alle esigenze di business. Gli stakeholder includono il consiglio di amministrazione, il management esecutivo, i clienti, i fornitori, i dipendenti e gli enti regolatori. COBIT utilizza la cascata degli obiettivi (Goals Cascade) per tradurre le esigenze degli stakeholder in obiettivi di governance specifici e misurabili.

2. **Coprire l'organizzazione end-to-end**: la governance IT non si limita al dipartimento IT. COBIT considera l'intera organizzazione, includendo tutte le funzioni e i processi rilevanti per la gestione delle informazioni e della tecnologia. Questo principio e particolarmente rilevante nella manutenzione IT, dove le decisioni operative hanno impatto trasversale su tutti i dipartimenti.

3. **Applicare un framework unico e integrato**: COBIT si integra con altri standard e framework (ITIL, ISO 27001, ISO 20000, TOGAF, PMBOK) fungendo da orchestratore. Non sostituisce questi framework ma fornisce il livello di governance che li coordina.

4. **Abilitare un approccio olistico**: COBIT identifica sette componenti (enabler) che supportano il sistema di governance: processi, strutture organizzative, principi e policy, informazioni, cultura e comportamenti, persone e competenze, servizi e infrastruttura.

5. **Separare governance e management**: la governance stabilisce la direzione (Evaluate, Direct, Monitor), il management esegue (Plan, Build, Run, Monitor). Questa separazione e critica: il consiglio di amministrazione governa, il management gestisce. La confusione tra i due livelli e una delle cause principali di fallimento nella governance IT.

6. **Adattare il sistema di governance alle esigenze dell'organizzazione**: COBIT 2019 introduce i Design Factor, undici fattori che determinano come configurare il sistema di governance in base alle caratteristiche specifiche dell'organizzazione (dimensione, settore, profilo di rischio, conformita normativa, ruolo dell'IT, modello di sourcing, metodi di sviluppo, strategia di adozione tecnologica, panorama delle minacce, requisiti di compliance, ruolo dell'IT nell'organizzazione).

### I 40 Obiettivi di Governance e Management

COBIT 2019 definisce 40 obiettivi organizzati in cinque domini:

**Dominio EDM --- Evaluate, Direct and Monitor (Governance)**

| Obiettivo | Descrizione | Rilevanza Manutenzione IT |
|-----------|-------------|---------------------------|
| EDM01 | Assicurare la definizione e il mantenimento del framework di governance | Stabilire le regole del gioco per la manutenzione |
| EDM02 | Assicurare la consegna del valore | Verificare che la manutenzione crei valore per il business |
| EDM03 | Assicurare l'ottimizzazione del rischio | Governare il rischio delle attivita di manutenzione |
| EDM04 | Assicurare l'ottimizzazione delle risorse | Garantire risorse adeguate per la manutenzione |
| EDM05 | Assicurare il coinvolgimento degli stakeholder | Comunicazione trasparente sullo stato della manutenzione |

**Dominio APO --- Align, Plan and Organize (Management)**

Questo dominio comprende 14 obiettivi (APO01-APO14) che coprono la gestione del framework IT, la strategia, l'architettura enterprise, l'innovazione, il portafoglio, il budget, le risorse umane, le relazioni, gli accordi di servizio, i fornitori, la qualita, il rischio, la sicurezza e la gestione dei dati. Per la manutenzione IT, gli obiettivi piu critici sono APO09 (Gestione degli accordi di servizio), APO10 (Gestione dei fornitori) e APO12 (Gestione del rischio).

**Dominio BAI --- Build, Acquire and Implement (Management)**

Undici obiettivi (BAI01-BAI11) che coprono la gestione di programmi, progetti, requisiti, soluzioni, disponibilita e capacita, cambiamenti organizzativi, cambiamenti IT, conoscenza, asset, configurazione e progetti. BAI06 (Gestione dei cambiamenti IT) e BAI10 (Gestione della configurazione) hanno correlazione diretta con le practice ITIL di Change Enablement e Configuration Management.

**Dominio DSS --- Deliver, Service and Support (Management)**

Sei obiettivi (DSS01-DSS06) direttamente operativi: gestione delle operazioni, gestione delle richieste di servizio e degli incidenti, gestione dei problemi, gestione della continuita, gestione dei servizi di sicurezza e gestione dei controlli dei processi di business. Questo dominio e il piu vicino alle attivita quotidiane di manutenzione IT.

**Dominio MEA --- Monitor, Evaluate and Assess (Management)**

Quattro obiettivi (MEA01-MEA04) dedicati al monitoraggio, valutazione e assessment delle prestazioni, del sistema di controllo interno, della conformita e dell'assurance. MEA01 (Monitoraggio delle prestazioni e della conformita) e essenziale per misurare l'efficacia della manutenzione.

### COBIT Goals Cascade

La Goals Cascade e il meccanismo che traduce le esigenze degli stakeholder in azioni concrete:

```
Esigenze degli Stakeholder
    |
    v
Obiettivi di Governance (Enterprise Goals)
    |
    v
Obiettivi di Allineamento (Alignment Goals)
    |
    v
Obiettivi di Governance e Management (40 obiettivi)
    |
    v
Componenti del Sistema di Governance (7 enablers)
```

**Esempio pratico per la manutenzione IT:**

- **Esigenza stakeholder**: "I nostri sistemi devono essere sempre disponibili per i clienti"
- **Enterprise Goal**: EG01 --- Portafoglio di prodotti e servizi competitivi
- **Alignment Goal**: AG06 --- Agilita dei servizi IT
- **Obiettivi rilevanti**: DSS01 (Gestione operazioni), DSS02 (Gestione incidenti), APO09 (Accordi di servizio)
- **Azione**: implementare monitoring proattivo, definire SLA con target 99.9%, stabilire processo di incident management con MTTR < 1 ora per P1

### Matrice RACI in COBIT

COBIT utilizza matrici RACI (Responsible, Accountable, Consulted, Informed) per chiarire ruoli e responsabilita. Esempio per la gestione degli incidenti:

| Attivita | CIO | IT Operations Manager | Service Desk Manager | Tecnico L1 | Tecnico L2 |
|----------|-----|----------------------|---------------------|------------|------------|
| Definire politica di gestione incidenti | A | R | C | I | I |
| Rilevare e registrare incidente | I | I | A | R | I |
| Classificare e prioritizzare | I | I | A | R | C |
| Investigare e diagnosticare | I | C | I | R | R |
| Risolvere e ripristinare | I | A | I | R | R |
| Chiudere incidente | I | I | A | R | I |
| Revisionare e migliorare processo | A | R | R | C | C |

(A = Accountable, R = Responsible, C = Consulted, I = Informed)

---

## ISO/IEC 20000 --- Certificazione della Gestione dei Servizi IT

### Struttura dello Standard

ISO/IEC 20000-1:2018 e lo standard internazionale che specifica i requisiti per un sistema di gestione dei servizi IT (SMS --- Service Management System). A differenza di ITIL (che e una raccolta di best practice non prescrittive) e COBIT (che e un framework di governance), ISO 20000 e uno standard certificabile: un'organizzazione puo ottenere una certificazione formale che attesta la conformita del proprio SMS ai requisiti dello standard.

La struttura di ISO 20000-1:2018 segue l'Annex SL, la struttura comune a tutti i sistemi di gestione ISO (come ISO 9001, ISO 27001, ISO 14001), facilitando l'integrazione con altri sistemi di gestione gia presenti nell'organizzazione.

**Le clausole dello standard:**

| Clausola | Titolo | Contenuto |
|----------|--------|-----------|
| 4 | Contesto dell'organizzazione | Comprensione dell'organizzazione, delle parti interessate, dell'ambito dell'SMS |
| 5 | Leadership | Impegno del top management, politica, ruoli e responsabilita |
| 6 | Pianificazione | Gestione dei rischi e delle opportunita, obiettivi di gestione dei servizi |
| 7 | Supporto | Risorse, competenze, consapevolezza, comunicazione, informazioni documentate |
| 8 | Operativita | Pianificazione e controllo operativo, portafoglio dei servizi, gestione delle relazioni, gestione della domanda e della capacita, progettazione e transizione, risoluzione e adempimento |
| 9 | Valutazione delle prestazioni | Monitoraggio, misurazione, analisi, audit interni, riesame della direzione |
| 10 | Miglioramento | Non conformita, azioni correttive, miglioramento continuo |

### Aggiornamenti 2024-2025

Lo standard ha ricevuto aggiornamenti significativi nel biennio 2024-2025:

- **ISO/IEC 20000-1:2018/Amd 1:2024 (Climate Action Changes)**: introduce requisiti per considerare l'impatto dei cambiamenti climatici sulla gestione dei servizi IT. Le organizzazioni devono valutare scenari come interruzioni del data center dovute a ondate di calore, fornitori critici colpiti da eventi climatici estremi e l'impronta ambientale dei servizi IT stessi.

- **ISO/IEC 20000-15:2024**: fornisce indicazioni su come i framework di project management come Agile e i principi di sviluppo software come DevOps possano essere applicati all'interno di un sistema di gestione dei servizi.

- **ISO/IEC TS 20000-16:2025**: guida per l'inclusione della sostenibilita ambientale all'interno di un SMS, collegando la gestione dei servizi IT alla responsabilita ambientale.

### Processo di Certificazione

Il percorso verso la certificazione ISO 20000 segue tipicamente queste fasi:

**Fase 1 --- Gap Analysis (2-4 settimane)**
Valutazione dello stato attuale dell'SMS rispetto ai requisiti dello standard. Si identificano i gap e si crea un piano di remediation. E consigliabile utilizzare un consulente esperto per questa fase, che puo essere lo stesso ente certificatore (pre-audit) o un consulente indipendente.

**Fase 2 --- Implementazione (3-12 mesi)**
Progettazione e implementazione dei processi, delle procedure e della documentazione necessari per colmare i gap identificati. Include la formazione del personale, l'implementazione o la configurazione degli strumenti ITSM, la creazione della documentazione richiesta e l'esecuzione di audit interni.

**Fase 3 --- Audit di Certificazione Stage 1 (1-2 giorni)**
L'ente certificatore esamina la documentazione dell'SMS per verificare che sia completa e conforme ai requisiti dello standard. Non verifica ancora l'implementazione effettiva.

**Fase 4 --- Audit di Certificazione Stage 2 (3-5 giorni)**
L'ente certificatore verifica l'implementazione effettiva dell'SMS attraverso interviste, osservazione dei processi, esame delle evidenze. Vengono identificate eventuali non conformita (maggiori o minori).

**Fase 5 --- Certificazione e Sorveglianza**
Se l'audit ha esito positivo, viene rilasciato il certificato con validita triennale. Ogni anno si svolgono audit di sorveglianza per verificare il mantenimento della conformita. Al terzo anno, si svolge l'audit di rinnovo (ri-certificazione).

### Mappatura ISO 20000 verso ITIL

ISO 20000 e ITIL sono complementari. La tabella seguente mostra la corrispondenza tra le clausole di ISO 20000-1:2018 e le practice ITIL v4:

| ISO 20000-1 Clausola | Requisito | Practice ITIL v4 Corrispondente |
|----------------------|-----------|--------------------------------|
| 8.2 Service Portfolio Management | Gestione del portafoglio servizi | Portfolio Management |
| 8.3.1 Service Level Management | Gestione dei livelli di servizio | Service Level Management |
| 8.3.2 Service Reporting | Reportistica sui servizi | Service Level Management, Monitoring |
| 8.5.1 Change Management | Gestione dei cambiamenti | Change Enablement |
| 8.5.2 Service Design and Transition | Progettazione e transizione | Service Design, Release Management |
| 8.5.3 Release and Deployment Management | Rilascio e distribuzione | Release Management, Deployment Management |
| 8.6.1 Incident Management | Gestione degli incidenti | Incident Management |
| 8.6.2 Service Request Management | Gestione delle richieste | Service Request Management |
| 8.6.3 Problem Management | Gestione dei problemi | Problem Management |
| 8.7.1 Service Availability Management | Gestione della disponibilita | Availability Management |
| 8.7.2 Service Continuity Management | Gestione della continuita | Service Continuity Management |

---

## TOGAF --- Enterprise Architecture per la Manutenzione IT

### Panoramica e Rilevanza

TOGAF (The Open Group Architecture Framework) e il framework di architettura enterprise piu adottato al mondo, utilizzato da oltre l'80% delle aziende Fortune 500. Mentre ITIL e COBIT si concentrano rispettivamente sulla gestione dei servizi e sulla governance, TOGAF fornisce il modello per progettare, pianificare, implementare e governare l'architettura IT dell'organizzazione nel suo complesso.

Per la manutenzione IT, TOGAF e rilevante perche fornisce:
- Una visione completa dell'architettura IT che facilita la comprensione delle dipendenze e dell'impatto dei cambiamenti
- Un metodo strutturato (ADM) per gestire l'evoluzione dell'architettura nel tempo
- Un repository di architettura che documenta lo stato attuale e lo stato target dell'infrastruttura
- Un framework di governance dell'architettura che assicura che i cambiamenti siano allineati alla strategia

### L'Architecture Development Method (ADM)

L'ADM e il cuore di TOGAF: un processo ciclico e iterativo composto da 10 fasi che guidano lo sviluppo e la gestione dell'architettura enterprise.

**Preliminary Phase --- Preparazione**
Definizione del framework organizzativo, dei principi di architettura, degli strumenti e delle governance. Per la manutenzione IT, questa fase include la definizione dei principi di architettura che guideranno le decisioni manutentive (es. "preferire soluzioni standard e supportate", "evitare vendor lock-in", "design for maintainability").

**Phase A --- Architecture Vision**
Definizione della visione architetturale e dell'ambito del progetto. Coinvolgimento degli stakeholder e approvazione della proposta. Per la manutenzione, questa fase stabilisce la visione target dell'infrastruttura e identifica i gap rispetto allo stato attuale.

**Phase B --- Business Architecture**
Sviluppo dell'architettura di business che descrive i processi, le capacita e le strutture organizzative. Nella manutenzione IT, questa fase modella i processi ITSM (incident, problem, change, SLA).

**Phase C --- Information Systems Architecture**
Si divide in due sotto-fasi: architettura dei dati e architettura applicativa. Per la manutenzione, questa fase documenta le applicazioni gestite, i loro flussi di dati e le dipendenze.

**Phase D --- Technology Architecture**
Definizione dell'architettura tecnologica: server, reti, storage, piattaforme, ambienti. Questa e la fase piu direttamente rilevante per la manutenzione IT operativa, poiche descrive l'infrastruttura fisica e virtuale che deve essere mantenuta.

**Phase E --- Opportunities and Solutions**
Identificazione delle opportunita di miglioramento e delle soluzioni per raggiungere lo stato target. Include la pianificazione dei progetti di migrazione, aggiornamento e dismissione.

**Phase F --- Migration Planning**
Pianificazione dettagliata della migrazione dallo stato attuale allo stato target. Per la manutenzione, questa fase pianifica i progetti di upgrade, migrazione e decommissioning.

**Phase G --- Implementation Governance**
Governance dell'implementazione dei progetti di architettura. Assicura che i cambiamenti implementati siano conformi all'architettura definita.

**Phase H --- Architecture Change Management**
Gestione dei cambiamenti all'architettura nel tempo. Questa fase si sovrappone alla gestione dei cambiamenti ITIL ma opera a un livello piu strategico, valutando se i cambiamenti proposti sono coerenti con l'architettura target.

**Requirements Management**
Gestione trasversale dei requisiti durante tutto il ciclo ADM. I requisiti di manutenibilita, disponibilita, sicurezza e prestazioni devono essere tracciati e soddisfatti.

### I Quattro Domini dell'Architettura

TOGAF organizza l'architettura enterprise in quattro domini interconnessi:

| Dominio | Descrizione | Esempi per la Manutenzione IT |
|---------|-------------|-------------------------------|
| Business Architecture | Processi, organizzazione, strategie | Processi ITSM, struttura team supporto, SLA |
| Data Architecture | Struttura e gestione dei dati | CMDB, knowledge base, log management |
| Application Architecture | Applicazioni e integrazioni | Strumenti ITSM, monitoring, automazione |
| Technology Architecture | Infrastruttura e piattaforme | Server, reti, storage, cloud, virtualizzazione |

### Architecture Repository

Il repository di architettura TOGAF e un asset fondamentale per la manutenzione IT. Contiene:

- **Architecture Landscape**: la descrizione corrente dell'architettura a tre livelli (strategico, segmento, capacita). Per la manutenzione, include la mappa completa dell'infrastruttura con le relazioni e le dipendenze.
- **Standards Information Base**: gli standard tecnologici adottati dall'organizzazione (versioni software supportate, piattaforme approvate, protocolli di rete standard). Guida le decisioni di manutenzione e aggiornamento.
- **Reference Library**: modelli di riferimento, pattern di architettura, template riutilizzabili. Include architetture di riferimento per ambienti standard (cluster applicativo, infrastruttura database HA, rete datacenter spine-leaf).
- **Governance Log**: registro delle decisioni di architettura, delle deroghe approvate e delle azioni di conformita. Documenta perche certe scelte architetturali sono state fatte.

---

## Lean IT e Kaizen --- Miglioramento Continuo nelle Operazioni IT

### Principi del Lean IT

Il Lean IT adatta i principi della produzione snella (Lean Manufacturing, originati dal Toyota Production System) al contesto delle operazioni IT. L'obiettivo e eliminare gli sprechi (muda), ridurre la variabilita (mura) e evitare il sovraccarico (muri) nei processi IT.

I cinque principi fondamentali del Lean IT:

**1. Definire il valore dal punto di vista del cliente**
Ogni attivita di manutenzione IT deve essere valutata in base al valore che crea per il cliente (interno o esterno). Un aggiornamento di sicurezza crea valore (protegge il business). Un report di manutenzione che nessuno legge non crea valore ed e uno spreco.

**2. Mappare il flusso del valore (Value Stream Mapping)**
Identificare e documentare tutti i passaggi del processo di manutenzione, distinguendo tra attivita che aggiungono valore, attivita necessarie ma senza valore aggiunto e sprechi puri. Esempio: nel processo di patch management, l'applicazione della patch aggiunge valore, il test della patch e necessario ma non aggiunge valore diretto, l'attesa per l'approvazione CAB di una patch standard e spesso uno spreco eliminabile.

**3. Creare flusso continuo**
Eliminare i colli di bottiglia e le interruzioni nel flusso di lavoro. In un processo di incident management, il flusso ideale e: rilevamento > classificazione > assegnazione > risoluzione > chiusura, senza code, attese o rimbalzi tra team.

**4. Implementare il sistema pull**
Il lavoro viene "tirato" dalla domanda, non "spinto" dall'offerta. I team di manutenzione rispondono agli incidenti e alle richieste (pull) piuttosto che eseguire attivita non richieste (push). La manutenzione preventiva e un'eccezione giustificata, ma deve essere calibrata sui dati di affidabilita.

**5. Perseguire la perfezione (Kaizen)**
Il miglioramento non ha fine. Ogni processo puo essere migliorato, ogni spreco puo essere ridotto. Il Kaizen e la pratica quotidiana di piccoli miglioramenti incrementali, non grandi rivoluzioni periodiche.

### Gli 8 Sprechi (Muda) nelle Operazioni IT

Adattando i sette sprechi tradizionali del Lean Manufacturing al contesto IT, con l'aggiunta di un ottavo spreco specifico:

| Spreco | Descrizione nel Contesto IT | Esempio |
|--------|---------------------------|---------|
| Difetti | Bug, errori di configurazione, dati corrotti nel CMDB | Patch applicata senza test che causa regressione |
| Sovrapproduzione | Report non letti, backup ridondanti, metriche non utilizzate | Dashboard con 50 metriche di cui solo 5 vengono consultate |
| Attesa | Code di approvazione, attesa fornitore, attesa informazioni | Ticket in attesa di approvazione CAB per 5 giorni |
| Talento non utilizzato | Competenze sottoutilizzate, mancanza di formazione | Tecnico L3 che gestisce ticket L1 per mancanza di organico |
| Trasporto | Trasferimento di dati non necessario, escalation inutili | Incidente che rimbalza tra 4 team prima di essere risolto |
| Inventario | Backlog eccessivo di ticket, asset non utilizzati | 500 ticket in backlog mai analizzati |
| Movimento | Context switching, tool switching, procedure ridondanti | Tecnico che deve aggiornare 3 sistemi diversi per ogni incidente |
| Over-processing | Processi troppo complessi, documentazione eccessiva | Change request con 50 campi obbligatori per un cambio standard |

### Il Metodo A3

Il metodo A3 e uno strumento Lean per il problem-solving strutturato e la comunicazione efficace. Il nome deriva dal formato carta A3 (297 x 420 mm) su cui viene documentata l'analisi. Il vincolo fisico del foglio A3 impone concisione e chiarezza.

Struttura di un A3 per la manutenzione IT:

```
=== A3 --- MIGLIORAMENTO PROCESSO ===
Titolo: Riduzione MTTR per incidenti database P1
Autore: [Nome] | Data: 2026-05-15 | Stato: In Corso

--- LATO SINISTRO ---

1. CONTESTO
   Negli ultimi 6 mesi, l'MTTR per incidenti P1
   su database PostgreSQL e stato di 58 minuti
   (target SLA: 30 minuti). 12 incidenti P1 su 18
   hanno violato l'SLA.

2. STATO ATTUALE (con dati)
   - MTTR medio: 58 minuti
   - Tempo medio rilevamento: 5 minuti (OK)
   - Tempo medio escalation a DBA: 18 minuti (CRITICO)
   - Tempo medio diagnosi: 22 minuti (ALTO)
   - Tempo medio risoluzione: 13 minuti (OK)

3. ANALISI CAUSA RADICE
   - Escalation manuale: il Service Desk chiama il
     DBA on-call, ma spesso il numero non e aggiornato
   - Diagnosi lenta: i DBA non hanno accesso diretto
     ai log da remoto, devono connettersi via VPN
   - Runbook incompleto: mancano 5 scenari frequenti

--- LATO DESTRO ---

4. STATO TARGET
   - MTTR medio: < 30 minuti
   - Tempo escalation: < 5 minuti (automatico)
   - Tempo diagnosi: < 15 minuti (strumenti + runbook)

5. CONTROMISURE PROPOSTE
   a) Escalation automatica PagerDuty per alert DB P1
   b) Dashboard Grafana con log e metriche DB in
      tempo reale, accessibile senza VPN
   c) Completamento runbook con i 5 scenari mancanti
   d) Automazione diagnosi: script che raccoglie
      automaticamente info diagnostiche al trigger

6. PIANO DI IMPLEMENTAZIONE
   | Azione | Chi | Quando | Stato |
   |--------|-----|--------|-------|
   | PagerDuty config | Ops | Sett 1 | Done |
   | Dashboard Grafana | DBA | Sett 2 | In corso |
   | Runbook update | DBA | Sett 2 | In corso |
   | Script diagnosi | DBA | Sett 3 | Pianif. |

7. VERIFICA E FOLLOW-UP
   - Misurare MTTR settimanalmente per 8 settimane
   - Review dopo 4 settimane per valutare efficacia
   - Standardizzare se target raggiunto
```

### DMAIC --- Lean Six Sigma nelle Operazioni IT

Il ciclo DMAIC (Define, Measure, Analyze, Improve, Control) e il metodo strutturato di Lean Six Sigma per il miglioramento dei processi. Si distingue dal PDCA per la maggiore enfasi sulla misurazione statistica e la riduzione della variabilita.

**Define (Definire)**
Definire il problema, l'ambito, gli obiettivi e il team. Utilizzare il Project Charter e il SIPOC (Supplier-Input-Process-Output-Customer) per inquadrare il progetto. Esempio: "Ridurre il tasso di incidenti ricorrenti dal 40% al 15% nei prossimi 6 mesi".

**Measure (Misurare)**
Raccogliere dati quantitativi sullo stato attuale del processo. Definire le metriche chiave (CTQ --- Critical to Quality), stabilire la baseline, validare il sistema di misurazione. Esempio: analizzare 12 mesi di dati di incident management, identificare i top-10 incidenti ricorrenti per volume.

**Analyze (Analizzare)**
Analizzare i dati per identificare le cause radice. Utilizzare strumenti statistici (diagramma di Pareto, istogrammi, correlazioni), diagrammi di Ishikawa, 5 Whys. Esempio: il 72% degli incidenti ricorrenti e attribuibile a 3 cause radice: crescita non monitorata dei log (35%), certificati SSL scaduti (22%), pool di connessioni database esaurito (15%).

**Improve (Migliorare)**
Progettare, testare e implementare le soluzioni. Utilizzare il Design of Experiments (DoE) quando possibile, altrimenti test pilota. Esempio: implementare log rotation automatico, monitoring delle scadenze certificati con 30 giorni di anticipo, tuning dei pool di connessioni con alert al 80%.

**Control (Controllare)**
Stabilizzare i miglioramenti e prevenire la regressione. Implementare control chart, documentare il nuovo processo, formare il team, definire i trigger per la revisione. Esempio: dashboard automatizzata che mostra il tasso di incidenti ricorrenti settimanale con soglie di allarme.

---

## DevOps e SRE --- Integrazione con la Gestione dei Servizi IT

### DevOps e ITSM: Complementarieta, non Competizione

Una delle false dicotomie piu diffuse nell'IT e quella tra DevOps e ITSM (ITIL). In realta, i due approcci sono complementari e si rafforzano a vicenda. DevOps porta velocita, automazione e cultura collaborativa; ITSM porta struttura, governance e gestione del rischio. L'obiettivo e combinare la velocita di DevOps con il controllo di ITSM.

**Aree di integrazione chiave:**

| Area | Approccio ITSM Tradizionale | Approccio DevOps/SRE | Integrazione Ottimale |
|------|---------------------------|---------------------|----------------------|
| Change Management | CAB settimanale, approvazioni formali | Deploy continuo, feature flag | Standard change automatizzati, CAB solo per high-risk |
| Incident Management | Ticket, escalation gerarchica | ChatOps, runbook automatizzati, self-healing | Alert automatico con auto-remediation + ticket per audit trail |
| Problem Management | RCA formale post-incidente | Blameless post-mortem, error budget | Post-mortem strutturato con azioni tracciate nel backlog |
| Monitoring | Monitoring infrastrutturale, soglie statiche | Observability (metriche, log, trace), SLO-based | Full-stack observability con SLO allineati agli SLA |
| Knowledge Management | Wiki, procedure documentate | Infrastructure as Code, runbook automatizzati | Docs-as-code versionati + KB per gli utenti |

### Site Reliability Engineering (SRE) nella Manutenzione

Il Site Reliability Engineering, sviluppato da Google, e un approccio all'operations che applica principi di ingegneria del software alla gestione dell'infrastruttura e delle operazioni. SRE non e separato da DevOps; e un'implementazione focalizzata del DevOps con enfasi specifica sull'affidabilita.

**I quattro segnali d'oro del monitoring (Golden Signals):**

1. **Latenza (Latency)**: il tempo necessario per servire una richiesta. Distinguere tra la latenza delle richieste riuscite e quella delle richieste fallite. Una richiesta che fallisce rapidamente puo abbassare la latenza media complessiva, mascherando un problema.

2. **Traffico (Traffic)**: la misura della domanda sul sistema. Per un servizio web, tipicamente richieste HTTP al secondo. Per un database, transazioni o query al secondo. Per un servizio di streaming, sessioni attive o banda utilizzata.

3. **Errori (Errors)**: il tasso di richieste che falliscono, sia esplicitamente (HTTP 5xx) sia implicitamente (risposta HTTP 200 ma contenuto errato) sia per policy (risposte con latenza superiore alla soglia SLO).

4. **Saturazione (Saturation)**: quanto il sistema e "pieno". Le risorse piu vincolate (CPU, RAM, disco, I/O, connessioni) determinano il punto di saturazione. I sistemi degradano significativamente prima di raggiungere il 100% di utilizzo.

**Error Budget e bilanciamento tra affidabilita e innovazione:**

Il concetto di Error Budget e una delle innovazioni piu significative di SRE. Se l'SLO di un servizio e 99.9% di disponibilita, l'error budget e lo 0.1% --- circa 43 minuti al mese. Finche l'error budget non e esaurito, il team puo rilasciare nuove funzionalita. Se l'error budget e esaurito, il focus si sposta sulla stabilita e sull'affidabilita.

```
Error Budget = 1 - SLO

Esempio:
  SLO = 99.9%
  Error Budget = 0.1% = 43 minuti/mese

  Budget consumato questo mese:
    Incidente 1: 15 minuti
    Incidente 2: 10 minuti
    Deploy rollback: 5 minuti
    Totale consumato: 30 minuti

  Budget residuo: 13 minuti
  Azione: cautela nei rilasci, focus su stabilita
```

### Automazione nella Manutenzione --- Il Concetto di Toil

SRE definisce il **toil** come lavoro operativo manuale, ripetitivo, automatizzabile, tattico, privo di valore duraturo e che scala linearmente con la crescita del servizio. L'obiettivo SRE e mantenere il toil sotto il 50% del tempo del team, dedicando il restante 50% a progetti di ingegneria che riducono il toil futuro.

**Esempi di toil nella manutenzione IT:**
- Restart manuale di servizi dopo ogni aggiornamento
- Pulizia manuale dei log quando lo spazio disco e basso
- Applicazione manuale di patch su ogni server singolarmente
- Creazione manuale di account utente seguendo una procedura di 15 passi
- Generazione manuale di report di conformita copiando dati da piu sistemi

**Automazione progressiva del toil:**

| Livello | Descrizione | Esempio |
|---------|-------------|---------|
| 0 | Completamente manuale | Tecnico esegue 15 comandi per applicare una patch |
| 1 | Documentato | Procedura scritta con tutti i comandi |
| 2 | Parzialmente automatizzato | Script che esegue i comandi, ma richiede input manuale |
| 3 | Completamente automatizzato con supervisione | Ansible playbook che applica la patch, tecnico supervisiona |
| 4 | Completamente automatizzato e autonomo | Pipeline CI/CD che applica la patch automaticamente dopo i test, con rollback automatico |
| 5 | Self-healing | Il sistema rileva la necessita di patching, applica la patch, verifica e comunica il risultato |

---

## ITIL Version 5 --- L'Evoluzione del Framework

### Timeline e Struttura

ITIL Version 5 e stato lanciato con il modulo Foundation il 12 febbraio 2026, seguito da moduli avanzati in rapida successione: Product, Service, and Experience (12 marzo 2026), Strategy (9 aprile 2026) e Transformation (9 aprile 2026). Il framework rappresenta l'evoluzione naturale di ITIL 4, non una rottura: il 40% del contenuto e mantenuto invariato da ITIL 4, il 24% e stato aggiornato e ricontestualizzato, e il 36% e completamente nuovo.

### Cambiamenti Strutturali Principali

**Dal Service Value Chain al Product and Service Lifecycle**
Il cambiamento strutturale piu significativo e la sostituzione della Service Value Chain con un nuovo ciclo di vita del prodotto e del servizio in 8 fasi:

| Fase | Descrizione | Corrispondenza ITIL 4 |
|------|-------------|----------------------|
| Discover | Identificazione di opportunita e bisogni | Engage (parziale) |
| Design | Progettazione del prodotto/servizio | Design and Transition (parziale) |
| Acquire | Acquisizione delle risorse necessarie | Obtain/Build (parziale) |
| Build | Costruzione e sviluppo | Obtain/Build (parziale) |
| Transition | Transizione in produzione | Design and Transition (parziale) |
| Operate | Operativita quotidiana | Deliver and Support (parziale) |
| Deliver | Erogazione del valore al cliente | Deliver and Support (parziale) |
| Support | Supporto e assistenza continua | Deliver and Support (parziale) |

**Unificazione di Product Management e Service Management**
ITIL 5 unifica formalmente la gestione del prodotto e la gestione del servizio in un unico ciclo di vita end-to-end. Questo riflette la realta delle organizzazioni moderne, dove la distinzione tra "prodotto" e "servizio" e sempre piu sfumata. Un'applicazione SaaS e simultaneamente un prodotto e un servizio; la sua manutenzione richiede competenze sia di product management sia di service management.

**Governance dell'Intelligenza Artificiale**
ITIL 5 introduce il modello 6C per la governance dell'IA:
- **Commitment**: impegno organizzativo verso l'uso responsabile dell'IA
- **Compliance**: conformita a normative e standard sull'IA (EU AI Act, ISO/IEC 42001)
- **Competence**: sviluppo delle competenze per gestire sistemi basati su IA
- **Control**: controllo sugli output dell'IA, con diritto di override umano
- **Communication**: trasparenza nelle decisioni mediate dall'IA
- **Continuity**: piani di continuita per quando i sistemi IA non sono disponibili

### Continuita con ITIL 4

E importante sottolineare che tutte le 34 practice ITIL 4 sono mantenute in ITIL 5 --- cinque sono state ricategorizzate, ma nessuna eliminata. Change Enablement, Incident Management, Problem Management e le altre practice rimangono la spina dorsale operativa. I 7 principi guida sopravvivono intatti. Per chi gia opera con ITIL 4, la transizione e evolutiva, non rivoluzionaria.

### Percorso di Certificazione

La certificazione ITIL 4 Foundation e pienamente riconosciuta come prerequisito per tutte le qualifiche avanzate ITIL Version 5. Non e necessario ripetere l'esame Foundation. Il nuovo schema di certificazione comprende nove moduli core e un'estensione AI Governance:

1. Foundation (prerequisito)
2. Product, Service, and Experience
3. Strategy
4. Transformation
5. AI Governance Extension

---

## Framework Alternativi e Complementari

### FitSM --- Service Management per Organizzazioni Leggere

FitSM e un framework di service management leggero e gratuito, rilasciato sotto licenza Creative Commons. Definisce 14 processi di gestione dei servizi ed e progettato specificamente per organizzazioni dove un'adozione completa di ITIL sarebbe sproporzionata rispetto alla capacita del team.

**Caratteristiche principali:**
- Tutti i documenti sono disponibili gratuitamente
- Definisce requisiti essenziali, non best practice opzionali
- Particolarmente adatto a team IT piccoli (5-20 persone), dipartimenti IT all'interno di organizzazioni non-IT, organizzazioni accademiche e del settore pubblico, organizzazioni che forniscono servizi IT federati
- Puo essere utilizzato come punto di partenza verso ISO 20000

**I 14 processi FitSM:**

| ID | Processo | Equivalente ITIL |
|----|----------|-----------------|
| SM1 | Service Portfolio Management | Portfolio Management |
| SM2 | Service Level Management | Service Level Management |
| SM3 | Service Reporting Management | Service Level Management (report) |
| SM4 | Service Availability and Continuity Management | Availability + Continuity Management |
| SM5 | Capacity Management | Capacity and Performance Management |
| SM6 | Information Security Management | Information Security Management |
| SM7 | Customer Relationship Management | Relationship Management |
| SM8 | Supplier Relationship Management | Supplier Management |
| SM9 | Incident and Service Request Management | Incident + Service Request Management |
| SM10 | Problem Management | Problem Management |
| SM11 | Configuration Management | Service Configuration Management |
| SM12 | Change Management | Change Enablement |
| SM13 | Release and Deployment Management | Release + Deployment Management |
| SM14 | Continual Service Improvement Management | Continual Improvement |

### VeriSM --- Governance per la Trasformazione Digitale

VeriSM (Value-driven Evolving Responsive Integrated Service Management) e un approccio di gestione dei servizi sviluppato dalla International Foundation for Digital Competences (IFDC). A differenza di altri framework, VeriSM non cerca di sostituire ITIL, COBIT o DevOps, ma fornisce un modello di governance che aiuta le organizzazioni a combinare le pratiche esistenti in modo coerente per la trasformazione digitale.

Il modello VeriSM si basa sul concetto di **Management Mesh**, una rete di risorse, pratiche, ambienti e tecnologie emergenti che l'organizzazione seleziona e combina in base alle esigenze specifiche di ogni prodotto o servizio.

### IT4IT --- Architettura di Riferimento per l'IT

IT4IT e uno standard pubblicato da The Open Group che adotta un approccio a catena del valore (value chain) per definire i building block funzionali della gestione dei servizi IT. Mappa le attivita dell'IT in quattro value stream:

1. **Strategy to Portfolio (S2P)**: dalla strategia al portafoglio di servizi
2. **Requirement to Deploy (R2D)**: dal requisito al rilascio in produzione
3. **Request to Fulfill (R2F)**: dalla richiesta all'erogazione del servizio
4. **Detect to Correct (D2C)**: dal rilevamento alla correzione --- il value stream piu rilevante per la manutenzione IT

IT4IT e tipicamente adottato da grandi organizzazioni che cercano di razionalizzare il proprio panorama di strumenti IT o standardizzare il flusso delle informazioni tra i sistemi.

---

## Matrice Comparativa dei Framework

### Confronto Strategico

La tabella seguente confronta i principali framework IT lungo dimensioni chiave per la manutenzione:

| Dimensione | ITIL 4/5 | COBIT 2019 | ISO 20000 | TOGAF | FitSM | DevOps/SRE |
|------------|----------|------------|-----------|-------|-------|------------|
| **Focus principale** | Service Management | IT Governance | Certificazione SMS | Enterprise Architecture | SM leggero | Affidabilita e velocita |
| **Livello operativo** | Tattico/Operativo | Strategico/Governance | Operativo/Compliance | Strategico/Tattico | Operativo | Operativo/Tattico |
| **Prescrittivita** | Best practice (non prescrittivo) | Framework configurabile | Standard certificabile | Framework metodologico | Requisiti essenziali | Principi e pratiche |
| **Certificazione org.** | No | No (solo individuale) | Si (ISO 20000) | No | No | No |
| **Certificazione individuale** | Si (Foundation, MP, SL) | Si (COBIT Foundation, Design & Implement) | Si (Lead Implementer/Auditor) | Si (Foundation, Certified, Practitioner) | Si (Foundation, Advanced, Expert) | Si (SRE Foundation, DevOps Foundation) |
| **Costo adozione** | Medio-Alto | Alto | Alto (audit + certificazione) | Medio-Alto | Basso (gratuito) | Medio (tooling) |
| **Dimensione org. ideale** | Media-Grande | Grande-Enterprise | Media-Grande | Grande-Enterprise | Piccola-Media | Qualsiasi |
| **Integrazione con Agile** | Nativa in v4/5 | Limitata | Supportata da ISO 20000-15 | Supportata in TOGAF 10 | Nativa | Nativa |
| **Copertura manutenzione** | Completa | Governance-level | Requisiti formali | Architetturale | Essenziale | Operativa avanzata |

### Quando Usare Quale Framework

**Scenario 1: PMI con team IT di 5-10 persone**
- Framework primario: FitSM per la struttura base
- Complemento: principi ITIL v4 dove utile (non adozione completa)
- Automazione: pratiche DevOps per patch management e deployment
- Percorso: FitSM → ITIL selettivo → eventuale ISO 20000

**Scenario 2: Media impresa con 50-200 dipendenti IT**
- Framework primario: ITIL 4/5 per la gestione dei servizi
- Governance: COBIT 2019 per allineamento IT-business
- Compliance: ISO 20000 se richiesto da clienti o normative
- Automazione: DevOps/SRE per i team di operations
- Percorso: ITIL Foundation → COBIT → ISO 20000

**Scenario 3: Grande impresa o enterprise**
- Governance: COBIT 2019 a livello board/CIO
- Architettura: TOGAF per l'architettura enterprise
- Service Management: ITIL 4/5 per le operazioni
- Certificazione: ISO 20000 per i servizi critici
- Operations: SRE per i servizi ad alta affidabilita
- Orchestrazione: VeriSM o IT4IT per l'integrazione

---

## Roadmap di Implementazione

### Piano a 18 Mesi per l'Adozione di un Framework ITSM

La seguente roadmap fornisce un percorso strutturato per implementare un framework di gestione dei servizi IT partendo da una situazione di maturita bassa (livello 1-2). Il piano e basato sull'esperienza di implementazioni reali e sui principi ITIL di progressione iterativa con feedback.

**Fase 0 --- Assessment e Preparazione (Settimane 1-4)**

| Attivita | Deliverable | Chi |
|----------|-------------|-----|
| Assessment dello stato attuale (maturity assessment) | Report di assessment con livelli per ogni practice | Consulente + IT Manager |
| Identificazione degli stakeholder chiave | Mappa degli stakeholder | IT Manager |
| Definizione della visione e degli obiettivi | Documento di visione con obiettivi SMART | IT Manager + CIO |
| Selezione delle practice prioritarie | Lista prioritizzata (max 3-4 practice iniziali) | Team IT |
| Budget e risorse | Business case approvato | CIO + CFO |
| Comunicazione iniziale | Kick-off meeting, comunicazione a tutto il team | IT Manager |

**Fase 1 --- Fondamenta (Mesi 2-4)**

Practice prioritarie: Incident Management + Service Request Management

Attivita:
1. Definire il processo di incident management (classificazione, prioritizzazione, escalation)
2. Implementare o configurare lo strumento di ticketing
3. Definire il catalogo delle richieste di servizio standard
4. Creare la knowledge base iniziale (top-20 soluzioni note)
5. Formare il team L1 sulle nuove procedure
6. Definire i KPI base (MTTR, FCR, CSAT)
7. Avviare la raccolta dati e la misurazione

Risultato atteso: tutti gli incidenti vengono registrati e tracciati, MTTR misurabile, FCR > 50%.

**Fase 2 --- Consolidamento (Mesi 5-8)**

Practice aggiuntive: Change Enablement + Problem Management

Attivita:
1. Definire il processo di change management (standard, normal, emergency)
2. Creare il catalogo degli standard change pre-autorizzati
3. Istituire il CAB con cadenza settimanale/bisettimanale
4. Avviare la gestione reattiva dei problemi (RCA per incidenti ricorrenti)
5. Creare il KEDB iniziale
6. Implementare il change calendar
7. Misurare e comunicare i primi risultati

Risultato atteso: tutti i cambiamenti vengono tracciati, cambio tasso di successo > 90%, riduzione incidenti ricorrenti > 20%.

**Fase 3 --- Maturazione (Mesi 9-14)**

Practice aggiuntive: Service Level Management + Configuration Management + Monitoring

Attivita:
1. Definire gli SLA per i servizi critici
2. Implementare il CMDB partendo dai CI critici
3. Configurare la discovery automatica
4. Implementare il monitoring proattivo con soglie preventive
5. Creare dashboard operative e report SLA mensili
6. Avviare la gestione proattiva dei problemi
7. Condurre assessment di maturita intermedio

Risultato atteso: SLA definiti e misurati per i servizi critici, CMDB operativo con i CI top-50, compliance SLA > 90%.

**Fase 4 --- Ottimizzazione (Mesi 15-18)**

Focus: automazione, integrazione, miglioramento continuo

Attivita:
1. Automatizzare i processi maturi (patch management, provisioning, backup verification)
2. Integrare gli strumenti (ticketing ↔ monitoring ↔ CMDB)
3. Implementare il programma di miglioramento continuo formale
4. Formare il team sulle practice avanzate
5. Condurre assessment di maturita finale
6. Definire il piano per i successivi 12 mesi
7. Valutare la readiness per eventuale certificazione ISO 20000

Risultato atteso: automazione del 60%+ delle operazioni ripetitive, integrazione tool completa, livello di maturita 3+ per le practice core.

---

## Modello di Maturita Dettagliato per la Manutenzione IT

### Framework di Assessment

Il modello di maturita seguente e specificamente progettato per valutare le capacita di manutenzione IT. Combina elementi di CMMI, del modello di maturita ITIL e delle best practice di settore. Ogni practice viene valutata su cinque livelli, con criteri oggettivi e misurabili per ogni livello.

### Criteri di Valutazione per Practice

**Incident Management --- Livelli di Maturita Dettagliati:**

| Livello | Caratteristiche | Metriche Tipiche | Evidenze |
|---------|----------------|-----------------|----------|
| 1 --- Iniziale | Nessun processo formale. Gli incidenti vengono gestiti ad hoc, senza registrazione sistematica. La risoluzione dipende dalla conoscenza individuale. | Non misurabili | Nessun sistema di ticketing, email o telefono come unici canali |
| 2 --- Ripetibile | Sistema di ticketing implementato. Processo base di registrazione e assegnazione. Classificazione inconsistente. | MTTR non affidabile, FCR non misurato | Ticketing attivo, ma classificazione e prioritizzazione inconsistenti |
| 3 --- Definito | Processo documentato e standardizzato. Matrice di prioritizzazione applicata. Knowledge base attiva. Escalation definita. | MTTR < 4h per P2, FCR > 60%, SLA compliance > 85% | Procedure documentate, KB con > 100 articoli, matrice escalation |
| 4 --- Gestito | Processo misurato quantitativamente. Dashboard in tempo reale. Analisi trend. Automazione parziale (auto-assign, auto-escalation). | MTTR < 2h per P2, FCR > 70%, SLA compliance > 95%, CSAT > 4.0 | Dashboard KPI, report automatici, trend analysis, automation rules |
| 5 --- Ottimizzato | Auto-healing per incidenti noti. ML/AI per classificazione e routing. Predictive monitoring. Miglioramento continuo data-driven. | MTTR < 30min per P2, FCR > 80%, SLA > 99%, auto-resolution > 30% | Self-healing scripts, ML classification, predictive alerts |

**Change Enablement --- Livelli di Maturita Dettagliati:**

| Livello | Caratteristiche | Metriche Tipiche | Evidenze |
|---------|----------------|-----------------|----------|
| 1 --- Iniziale | Cambiamenti non tracciati. Nessun processo di approvazione. Rollback non pianificato. | Non misurabili, > 30% emergency | Nessun registro cambiamenti |
| 2 --- Ripetibile | Registro cambiamenti base. Approvazioni informali. Nessuna differenziazione per tipo. | Success rate < 80%, emergency > 25% | Registro presente ma incompleto |
| 3 --- Definito | Processo differenziato (standard/normal/emergency). CAB attivo. Piano rollback obbligatorio. Change calendar. | Success rate > 90%, emergency < 15%, failed < 5% | Processo documentato, CAB meeting notes, change calendar |
| 4 --- Gestito | Pipeline CI/CD per standard change. Analisi rischio automatizzata. Post-implementation review sistematica. | Success rate > 95%, emergency < 10%, MTTR rollback < 30min | CI/CD pipeline, risk scoring automatico, PIR database |
| 5 --- Ottimizzato | Continuous deployment con canary/blue-green. Feature flags. Rollback automatico basato su SLO. Zero-downtime deployment. | Success rate > 99%, emergency < 5%, zero-downtime > 90% | Canary deployment, feature flags, automated rollback |

### Template di Assessment

Il seguente template puo essere utilizzato per condurre un assessment di maturita della manutenzione IT nell'organizzazione:

```
=== ASSESSMENT MATURITA MANUTENZIONE IT ===
Organizzazione:    [Nome]
Data Assessment:   [YYYY-MM-DD]
Assessor:          [Nome/Ruolo]
Metodo:            [Self-assessment | Peer review | Assessment esterno]

--- ISTRUZIONI ---
Per ogni practice, valutare il livello attuale (1-5) basandosi
sulle evidenze oggettive. Definire il livello target a 12 mesi.
Calcolare il gap e la priorita di intervento.

--- VALUTAZIONE ---

| # | Practice | Livello Attuale | Livello Target | Gap | Priorita |
|---|----------|----------------|----------------|-----|----------|
| 1 | Incident Management | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 2 | Service Request Management | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 3 | Problem Management | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 4 | Change Enablement | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 5 | Configuration Management (CMDB) | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 6 | Service Level Management | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 7 | Monitoring & Event Management | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 8 | Knowledge Management | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 9 | Release & Deployment Management | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 10 | IT Asset Management | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 11 | Continual Improvement | ___ | ___ | ___ | [Alta/Media/Bassa] |
| 12 | Capacity & Performance Management | ___ | ___ | ___ | [Alta/Media/Bassa] |

Media Maturita Attuale: ___
Media Maturita Target:  ___

--- EVIDENZE PER PRACTICE ---
(Documentare le evidenze oggettive per ogni valutazione)

Practice 1: Incident Management
  Evidenze livello attuale:
    - [Descrivere le evidenze che supportano il livello assegnato]
    - [Strumenti in uso, processi documentati, metriche disponibili]
  Gap rispetto al target:
    - [Cosa manca per raggiungere il livello target]
  Azioni proposte:
    - [Azioni concrete con responsabile e timeline]

[Ripetere per ogni practice]

--- ANALISI COMPLESSIVA ---
Punti di forza:
  - [Practice con livello >= 3]

Aree critiche:
  - [Practice con livello 1 e gap >= 2]

Dipendenze:
  - [Practice che dipendono da altre per il miglioramento]

--- PIANO D'AZIONE SINTETICO ---
| Priorita | Azione | Responsabile | Timeline | Budget stimato |
|----------|--------|-------------|----------|----------------|
| 1 | [Azione piu urgente] | [Nome] | [Periodo] | [Euro] |
| 2 | [Seconda azione] | [Nome] | [Periodo] | [Euro] |
| ... | ... | ... | ... | ... |

--- PROSSIMO ASSESSMENT ---
Data prevista: [Data a 6 o 12 mesi]
```

---

## Intelligenza Artificiale e AIOps nella Manutenzione IT

### Lo Stato dell'IA nell'ITSM (2025-2026)

L'adozione di capacita basate sull'intelligenza artificiale nella gestione dei servizi IT sta superando qualsiasi altro cambiamento tecnologico o metodologico precedente nel settore ITSM. Secondo le analisi di settore del 2025-2026, la fiducia nell'IA e aumentata per il 62% dei professionisti ITSM, mentre e diminuita solo per il 5%. La governance dell'IA e emersa come il trend numero uno nell'ITSM per il biennio 2025-2026.

### AIOps --- Intelligenza Artificiale per le Operazioni IT

AIOps (Artificial Intelligence for IT Operations) e l'applicazione di tecnologie di machine learning, analisi dei big data e automazione avanzata alle operazioni IT. L'obiettivo e passare da operazioni reattive e manuali a operazioni proattive, predittive e autonome.

**Livelli di maturita AIOps:**

| Livello | Descrizione | Capacita | Esempio |
|---------|-------------|----------|---------|
| 0 --- Manuale | Operazioni completamente manuali, monitoring basato su soglie statiche | Alert basati su regole, investigazione manuale | Tecnico riceve email quando CPU > 90%, investiga manualmente |
| 1 --- Assistito | IA suggerisce azioni, operatore decide ed esegue | Correlazione eventi, suggerimenti di classificazione, KB search intelligente | Il sistema suggerisce "incidente simile a INC-00142, soluzione: riavvio servizio X" |
| 2 --- Semi-autonomo | IA esegue azioni predefinite per scenari noti, con supervisione umana | Auto-remediation per scenari noti, auto-classificazione, routing intelligente | Il sistema rileva disco pieno, esegue cleanup automatico, notifica il tecnico |
| 3 --- Autonomo | IA gestisce autonomamente la maggior parte degli scenari, umano interviene sulle eccezioni | Predictive maintenance, capacity planning automatico, self-healing avanzato | Il sistema prevede che il server raggiungera saturazione CPU tra 48 ore, scala automaticamente le risorse |
| 4 --- Cognitivo | IA apprende continuamente e migliora autonomamente, gestisce scenari nuovi | Apprendimento continuo, adattamento a pattern nuovi, ottimizzazione autonoma | Il sistema identifica un nuovo tipo di attacco DDoS mai visto prima e implementa contromisure autonomamente |

**Casi d'uso AIOps nella manutenzione IT:**

1. **Correlazione intelligente degli eventi**: aggregazione e correlazione di migliaia di eventi da fonti diverse (monitoring, log, metriche, trace) per identificare la causa radice con riduzione del rumore dell'alert fino al 95%.

2. **Classificazione e routing automatico degli incidenti**: modelli di NLP (Natural Language Processing) che analizzano la descrizione dell'incidente e lo classificano, prioritizzano e instradano automaticamente al gruppo di supporto corretto. Accuratezza tipica: 85-92%.

3. **Chatbot e agenti conversazionali per il Service Desk**: IA generativa che gestisce le richieste di primo livello, consulta la knowledge base, guida l'utente nella risoluzione autonoma e apre ticket quando necessario. Tasso di risoluzione autonoma: 30-50% delle richieste L1.

4. **Analisi predittiva per la manutenzione preventiva**: modelli di ML che analizzano i trend di utilizzo delle risorse, i pattern di errore e i dati storici per prevedere guasti prima che si verifichino. Anticipo medio della predizione: 24-72 ore.

5. **Ottimizzazione automatica della capacita**: algoritmi che analizzano i pattern di utilizzo e regolano automaticamente le risorse allocate (CPU, RAM, storage) per ottimizzare costi e prestazioni. Risparmio tipico: 15-30% sui costi infrastrutturali.

### Governance dell'IA nell'ITSM

L'adozione dell'IA nelle operazioni IT richiede una governance robusta:

**Principi di governance IA per la manutenzione IT:**

- **Trasparenza**: le decisioni dell'IA devono essere spiegabili. Quando un sistema AIOps classifica un incidente come P1 e attiva un'escalation automatica, il reasoning deve essere documentato e verificabile.
- **Accountability**: deve sempre esistere un responsabile umano per le azioni dell'IA. L'IA suggerisce o esegue, ma un umano e accountable.
- **Supervisione umana**: per le azioni ad alto impatto (reboot di server di produzione, failover, rollback di cambiamenti), l'approvazione umana deve essere richiesta indipendentemente dal livello di automazione.
- **Bias e fairness**: i modelli di ML devono essere monitorati per bias (es. un modello che prioritizza sistematicamente piu bassi gli incidenti segnalati da certi dipartimenti).
- **Continuita operativa**: deve esistere un piano di fallback per quando i sistemi IA non sono disponibili. I processi manuali devono rimanere operativi e il team deve essere formato per eseguirli.
- **Privacy e sicurezza dei dati**: i dati utilizzati per il training e l'inferenza dei modelli IA devono essere trattati secondo le normative vigenti (GDPR, NIS2) e le policy di sicurezza dell'organizzazione.

### Agentic AI nell'ITSM

Il trend emergente nel 2026 e l'adozione di workflow agentici e sistemi multi-agente nell'ITSM. Un agente IA e un sistema autonomo che puo percepire il proprio ambiente, prendere decisioni e intraprendere azioni per raggiungere obiettivi specifici.

**Esempio di workflow agentico per la risoluzione incidenti:**

```
Trigger: Alert "Database connection pool exhausted"
    |
    v
Agente Triage: analizza l'alert, correla con altri eventi
    recenti, classifica come Incident P2 Database
    |
    v
Agente Diagnostico: esegue query diagnostiche sul
    database, analizza slow query log, verifica
    connection pool status, identifica query bloccante
    |
    v
Agente Decisionale: valuta le opzioni:
    a) Kill della query bloccante (basso rischio)
    b) Resize del connection pool (medio rischio)
    c) Escalation umana (nessun rischio)
    Decisione: opzione (a) - query bloccante identificata
    come report non critico, kill sicuro
    |
    v
Agente Esecutore: esegue pg_terminate_backend()
    sulla query bloccante, verifica il ripristino del
    connection pool, aggiorna il ticket
    |
    v
Agente Verifica: conferma che il servizio e tornato
    operativo, verifica le metriche per 15 minuti,
    chiude l'incidente con documentazione completa
    |
    v
Agente Apprendimento: registra il pattern per
    future occorrenze, aggiorna il KEDB, suggerisce
    azione preventiva (ottimizzazione della query report)
```

---

## Metriche Avanzate e Dashboard Operative

### Framework DORA per le Prestazioni IT

Le metriche DORA (DevOps Research and Assessment), sviluppate dal team di ricerca di Google, sono diventate lo standard de facto per misurare le prestazioni delle organizzazioni IT. Le quattro metriche chiave sono:

| Metrica DORA | Descrizione | Elite | High | Medium | Low |
|-------------|-------------|-------|------|--------|-----|
| Deployment Frequency | Frequenza dei rilasci in produzione | On-demand (piu volte al giorno) | Tra 1/giorno e 1/settimana | Tra 1/settimana e 1/mese | Tra 1/mese e 1/6 mesi |
| Lead Time for Changes | Tempo dal commit al rilascio in produzione | < 1 ora | Tra 1 giorno e 1 settimana | Tra 1 settimana e 1 mese | Tra 1 mese e 6 mesi |
| Change Failure Rate | Percentuale di rilasci che causano un incidente | 0-5% | 5-10% | 10-15% | 15-45% |
| Time to Restore Service | Tempo per ripristinare il servizio dopo un incidente causato da un rilascio | < 1 ora | < 1 giorno | Tra 1 giorno e 1 settimana | Tra 1 settimana e 1 mese |

**Quinta metrica (aggiunta nel 2024):**

| Metrica | Descrizione | Significato |
|---------|-------------|-------------|
| Reliability | Disponibilita complessiva del servizio misurata come SLO achievement | Misura la capacita dell'organizzazione di mantenere i servizi operativi, combinando tutte le cause di downtime |

### Composizione della Dashboard Operativa

Una dashboard operativa efficace per la manutenzione IT deve bilanciare tre livelli di informazione:

**Livello Esecutivo (CIO, IT Director)**
- Disponibilita complessiva dei servizi (semaforo verde/giallo/rosso)
- Compliance SLA percentuale
- Trend incidenti per gravita (ultimo trimestre)
- Costo del downtime (euro)
- Stato progetti di miglioramento

**Livello Management (IT Operations Manager, Service Desk Manager)**
- MTTR per priorita
- Backlog incidenti e problemi
- Change success rate
- FCR rate
- CSAT trend
- Capacita del team (carico vs disponibilita)

**Livello Operativo (Team Lead, Tecnici)**
- Incidenti aperti assegnati
- SLA countdown per ogni ticket
- Stato dei servizi in tempo reale
- Alert attivi
- Deployment in corso
- Change calendar settimanale

---

## Riferimenti e Risorse

### Standard e Framework
- ITIL 4 Foundation --- AXELOS (itil-docs.com)
- ITIL Version 5 Foundation --- PeopleCert (febbraio 2026)
- ISO/IEC 20000-1:2018 --- Service Management System Requirements
- ISO/IEC 20000-1:2018/Amd 1:2024 --- Climate Action Changes
- COBIT 2019 --- ISACA
- ISO 27001:2022 --- Information Security Management
- TOGAF Standard 10th Edition --- The Open Group
- FitSM --- ITEMO (fitsm.eu)
- VeriSM --- IFDC
- IT4IT Reference Architecture 3.0 --- The Open Group
- CMMI V3.0 --- CMMI Institute (ISACA)

### Strumenti Consigliati
- Ticketing/ITSM: GLPI, Zammad, OTRS, ServiceNow, Jira Service Management
- CMDB: GLPI, NetBox, i-doit, Ralph
- Monitoring: Zabbix, Prometheus + Grafana, Nagios, Datadog
- Documentazione: BookStack, Wiki.js, MkDocs, Confluence
- Automazione: Ansible, Terraform, Puppet, Chef
- AIOps: Datadog AI, Dynatrace Davis AI, BigPanda, Moogsoft
- CI/CD: GitLab CI, GitHub Actions, Jenkins, ArgoCD
- Observability: Grafana Stack (Loki, Tempo, Mimir), Elastic Stack, Jaeger

### Certificazioni Rilevanti
- ITIL 4 Foundation, ITIL 4 Managing Professional, ITIL 5 Foundation
- COBIT 2019 Foundation, COBIT 2019 Design and Implementation
- CompTIA A+, Network+, Server+
- ISO 20000 Lead Implementer/Auditor
- ISO 27001 Lead Implementer/Auditor
- TOGAF 10 Foundation, TOGAF 10 Certified
- HDI Support Center Analyst
- SRE Foundation (DevOps Institute)
- DevOps Foundation (DevOps Institute)
- FitSM Foundation, FitSM Advanced
- Lean IT Foundation, Lean IT Kaizen Lead

---

> **Nota**: Questo documento rappresenta una guida di riferimento completa per l'implementazione di framework e metodologie IT nella manutenzione dei sistemi. Deve essere adattato alle specifiche esigenze dell'organizzazione, alle risorse disponibili e al contesto operativo. L'implementazione deve essere graduale, iterativa e guidata dai dati. La versione piu recente di questo documento e mantenuta nella piattaforma di documentazione interna.

---

## Esercizi

1. **Lab — triage 10 ticket.** Categorizza 10 ticket reali (o sintetici): SR / Incident / Problem / Change. Argomenta.
2. **Lab — change matrix.** Definisci 3 categorie change (Standard, Normal, Emergency) per la tua organizzazione; criteri pre-approval.

## Auto-valutazione

1. Service Request vs Incident: differenza con esempio.
2. Problem vs Incident.
3. ITIL v3 → v4: cambi principali.
4. CAB: quando convocare?

## Letture primarie

- ITIL 4 Foundation (Axelos). Vedi `00-BIBLIOGRAFIA.md`.

## Collegamenti incrociati

- Modulo 12 — `12-itil4-deep-dive-pratiche.md`.
- Modulo 23 (NEW) — `23-change-automation-validation.md`.

## Glossario locale

| Termine | Definizione |
|---|---|
| **ITIL** | Information Technology Infrastructure Library. |
| **Service Request (SR)** | Richiesta voluta dall'utente. |
| **Incident** | Disservizio non voluto. |
| **Problem** | Cause root degli incident. |
| **Change Enablement** | ITIL v4 practice (ex Change Management). |
| **CAB** | Change Advisory Board. |
| **Standard change** | Change pre-approvato. |
| **Normal change** | Change che richiede CAB. |
| **Emergency change** | Change urgente, post-CAB review. |
| **COBIT** | IT governance framework. |
