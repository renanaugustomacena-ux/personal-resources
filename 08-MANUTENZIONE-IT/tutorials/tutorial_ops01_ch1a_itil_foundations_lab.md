# Tutorial: ITIL v4 — Fondamenti e Service Value System — Hands-On Lab

> **Documento di riferimento:** `01-framework-metodologie.md` (sezioni 1-2)
> **Dominio:** Framework e Metodologie
> **Ambito:** ITIL v4 fondamenti, SVS, 7 Principi Guida, 4 Dimensioni, Service Value Chain, panoramica delle 34 Practice
> **Durata lab:** 3-4 ore (suddivisibili in 2 sessioni)
> **Livello:** Da principiante (nessuna esperienza IT) ad intermedio (Parti A-C)
> **Prerequisiti:** `tutorial_ops00_ch1_day_one_it_ops_lab.md` (ambiente lab configurato)
> **Ambiente:** Lab isolato — DC-LAB-01, SRV-LINUX-01, WKS-LAB-01 tutti accesi

---

## Lab Environment Setup

L'ambiente lab è quello già configurato nel tutorial ops00. Prima di procedere, verifica che sia operativo.

**Verifica rapida da WKS-LAB-01 (PowerShell):**

```powershell
# Esegui lo script di health check creato nel tutorial ops00
.\lab_healthcheck.ps1
# Atteso: tutti e tre i servizi TcpTestSucceeded: True
```

**Addizioni specifiche per questo tutorial:**

Nessuna VM aggiuntiva necessaria. Questo tutorial è prevalentemente teorico-concettuale con esercizi pratici di documentazione, classificazione e simulazione su carta/file markdown. Nella Part B installeremo GLPI (sistema di ticketing open-source) su SRV-LINUX-01 per mettere in pratica i concetti ITIL.

**Software da installare (Part B — lo installiamo step-by-step):**
- GLPI 10.x su SRV-LINUX-01 (ticketing system open-source, analogo a Jira Service Management)
- Docker su SRV-LINUX-01 (per semplificare l'installazione GLPI)

---

## PART A: FONDAMENTI — Capire il Perché e il Cosa di ITIL v4

> Prima di toccare qualsiasi tool, sistema o procedura, è necessario costruire il framework mentale giusto. ITIL v4 non è un software da installare — è un modo di pensare alla gestione dei servizi IT. Questa parte costruisce quella struttura mentale con analogie concrete.

---

### Concetto A1: Cos'è ITIL e Perché Esiste

**Il problema che ITIL risolve.**

Immagina di costruire una casa. Puoi assumere muratori, elettricisti, idraulici e falegnami tutti bravi individualmente — ma se ognuno lavora con metodi propri, senza coordinazione, il risultato sarà una casa dove l'impianto elettrico passa dove doveva passare la tubazione dell'acqua, e il falegname ha bloccato il passaggio che l'idraulico doveva usare.

L'IT nelle aziende funzionava esattamente così prima dei framework: team separati (server, rete, sicurezza, helpdesk, sviluppo) con metodi, linguaggi e priorità diverse. Un incidente che richiedeva 3 team per essere risolto diventava un disastro di comunicazione.

> **ITIL** (Information Technology Infrastructure Library) nasce nel 1986 in UK dal governo britannico come raccolta di best practices per standardizzare la gestione dei servizi IT nella pubblica amministrazione. Oggi è alla versione 4 (2019) e viene usato da aziende in oltre 100 paesi — dal comune di 50 dipendenti alla multinazionale con 300.000 persone.

**Perché non inventare le proprie procedure?**

Si può farlo. Ma un'azienda che inventa tutto da zero:
- Commette gli stessi errori che altre 10.000 aziende hanno già commesso e risolto
- Non può certificarsi (ISO 20000 richiede aderenza a standard)
- Fa fatica ad assumere personale già formato (chi conosce ITIL deve reimparare tutto da zero)
- Non ha un linguaggio comune con i fornitori (tutti parlano "incidente", "SLA", "change request")

**Cosa ITIL NON è:**

| Mito | Realtà |
|---|---|
| ITIL è un software | ITIL è un framework concettuale; gli strumenti (GLPI, Jira, ServiceNow) sono separati |
| ITIL è solo per grandi aziende | Il 70% delle organizzazioni che usano ITIL ha meno di 500 dipendenti |
| Seguire ITIL significa burocrazia | ITIL v4 è esplicitamente flessibile; puoi adottarne solo le parti che servono |
| ITIL risolve i problemi tecnici | ITIL risolve i problemi di *gestione* dei servizi; i problemi tecnici li risolve il tecnico |

**Perché mi interessa?** Se lavorerai in IT Operations in qualsiasi azienda italiana di dimensioni medio-grandi, incontrerai ITIL. I colloqui di lavoro chiedono "conosci ITIL?", i clienti chiedono "siete certificati ISO 20000?", i fornitori parlano di "SLA", "ticket P1", "change window". ITIL è la lingua franca dell'IT professionale.

---

### Concetto A2: Service vs Product — Cosa Vende l'IT?

> **Analogia chiave.** Quando paghi la bolletta dell'elettricità, non compri un generatore — compri *l'accesso all'elettricità quando ti serve*. Non ti preoccupi di come viene prodotta, trasmessa, o regolata la tensione. Paghi per il risultato (luce accesa, lavatrice che gira), non per il macchinario.

L'IT aziendale funziona esattamente così. Gli utenti non comprano server, switch, licenze software — comprano **la capacità di fare il loro lavoro**:

- La contabilità compra "la possibilità di elaborare le buste paga ogni mese puntualmente"
- Le vendite comprano "la possibilità di accedere al CRM da qualsiasi dispositivo, ovunque"
- La logistica compra "la possibilità di tracciare ogni spedizione in tempo reale"

Questi sono **servizi**. I server, i database, la rete, i backup sono **risorse** (componenti interni) che *abilitano* quei servizi. La distinzione è fondamentale:

```
RISORSE (interne, gestite dall'IT):
  Server físici
  Virtual machines
  Database
  Reti
  Software licenze
       |
       | vengono combinate per erogare
       v
SERVIZI (visibili agli utenti):
  "Email sempre disponibile"
  "CRM accessibile da mobile"
  "Backup dati giornaliero garantito"
  "Portale HR sempre raggiungibile"
```

**Quattro concetti ITIL fondamentali:**

| Termine | Definizione | Esempio concreto |
|---|---|---|
| **Service (Servizio)** | Un modo per abilitare il co-creazione di valore facilitando i risultati che i clienti vogliono raggiungere | "Accesso all'email aziendale 24/7" |
| **Value (Valore)** | La percezione dei benefici, dell'utilità e dell'importanza di qualcosa | I commerciali possono rispondere ai clienti da casa la sera |
| **Outcome (Risultato)** | Ciò che i clienti vogliono realmente ottenere grazie al servizio | "Aumentare le vendite chiudendo contratti più velocemente" |
| **Output (Prodotto)** | Il risultato tangibile prodotto dal servizio | "Una email inviata" |

> La trappola comune: i team IT si concentrano sugli *output* ("il server risponde al 99.9%") mentre i business stakeholder vogliono gli *outcome* ("le vendite sono aumentate del 12%"). ITIL v4 insiste che l'IT deve sempre collegare il proprio lavoro ai business outcome.

**Perché mi interessa?** Quando apri un ticket o pianifichi una manutenzione, dovrai sempre chiederti: "Quale servizio sto erogando? Chi è il mio cliente? Quale outcome vuole raggiungere?" Questo cambia completamente come viene percepita l'IT dall'azienda — da "costo da ridurre" a "partner che abilita il business".

---

### Concetto A3: Il Service Value System — La Grande Mappa

> **Analogia.** Immagina un'azienda di consegne (es. Amazon Logistics). Riceve ordini (opportunità/domanda), ha magazzini, corrieri, sistemi IT, procedure operative, fornitori (componenti interni), e consegna i pacchi ai clienti (valore). Il Service Value System è la mappa di come tutto questo si collega, dall'ordine alla consegna.

```
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE VALUE SYSTEM (SVS)                    │
│                                                                  │
│  INPUT ─────────────────────────────────────────────── OUTPUT   │
│  Opportunità                                          VALORE     │
│  Domanda                                                         │
│      │                                                    ↑      │
│      ▼                                                    │      │
│  ┌─────────────────────────────────────────────────────┐ │      │
│  │           GUIDING PRINCIPLES (7 principi)            │ │      │
│  │      (bussola per ogni decisione operativa)          │ │      │
│  └─────────────────────────────────────────────────────┘ │      │
│      │                                                    │      │
│      ▼                                                    │      │
│  ┌─────────────────────────────────────────────────────┐ │      │
│  │              SERVICE VALUE CHAIN                     │ │      │
│  │  Plan → Improve → Engage → Design → Obtain → Deliver │─┘      │
│  └─────────────────────────────────────────────────────┘        │
│      ┌──────────────────────────────────────────────────┐       │
│      │   PRACTICES (34 discipline operative)             │       │
│      │   Incident Mgmt │ Change Enablement │ Problem Mgmt│       │
│      │   Asset Mgmt    │ Config Mgmt       │ Knowledge...│       │
│      └──────────────────────────────────────────────────┘       │
│      ┌──────────────────────────────────────────────────┐       │
│      │   GOVERNANCE (sistema di controllo e direzione)   │       │
│      └──────────────────────────────────────────────────┘       │
│      ┌──────────────────────────────────────────────────┐       │
│      │   CONTINUAL IMPROVEMENT (miglioramento continuo)  │       │
│      └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

I cinque elementi del SVS lavorano insieme — non sono sequenziali ma simultanei e interdipendenti:

1. **Guiding Principles**: la bussola. Orientano *tutte* le decisioni, sempre.
2. **Governance**: il sistema di controllo. Chi decide cosa, con quale autorità, con quale responsabilità.
3. **Service Value Chain**: il motore. Come si trasforma la domanda in valore concreto.
4. **Practices**: gli strumenti. Le 34 discipline operative che si usano per fare il lavoro.
5. **Continual Improvement**: il feedback loop. Come si migliora ogni elemento del sistema nel tempo.

**Perché mi interessa?** Il SVS ti dà la "mappa" per capire dove si inserisce ogni attività che fai in IT. Quando gestisci un incidente, stai usando la Practice "Incident Management" all'interno della attività "Deliver and Support" della Service Value Chain. Avere questa mappa in testa ti aiuta a capire perché alcune procedure esistono e come cambiarle in modo coerente.

---

### Concetto A4: I 7 Principi Guida — La Bussola delle Decisioni

> **Analogia.** I principi guida sono come i principi di un medico: "non nuocere", "il paziente prima di tutto", "basarsi sull'evidenza". Un medico non consulta questi principi per ogni singola azione — li ha interiorizzati e li applica inconsciamente. Un professionista IT ITIL fa lo stesso con i 7 principi.

I 7 principi guida valgono in *qualsiasi* circostanza e si applicano a qualsiasi livello (dal CTO all'helpdesk di primo livello):

**1. Focus on Value (Concentrarsi sul valore)**
Prima di ogni attività, chiediti: "Chi sono i miei stakeholder? Cosa considerano di valore? Questa attività lo crea o lo distrugge?"
- ✓ Applicazione: "Aggiorno i driver video delle workstation → riduco i ticket per problemi grafici → la contabilità lavora senza interruzioni → valore per il business"
- ✗ Errore comune: aggiornare per il gusto di essere "aggiornati", senza legarlo a un beneficio misurabile

**2. Start Where You Are (Partire da dove ci si trova)**
Non buttare via tutto ciò che esiste per ricominciare da zero. Fai un assessment oggettivo: cosa funziona? Cosa va migliorato? Cosa va eliminato?
- ✓ Applicazione: prima di comprare un nuovo sistema di ticketing, analizza i processi attuali — forse bastano procedure migliori sullo stesso strumento
- ✗ Errore comune: "Compriamo ServiceNow e risolviamo tutto" (il tool non risolve problemi di processo)

**3. Progress Iteratively with Feedback (Progredire iterativamente)**
Piccoli passi verificabili > grandi progetti "big bang". Implementa, misura, impara, correggi, ripeti.
- ✓ Applicazione: implementa la gestione incidenti in 4 settimane → misura il MTTR → poi aggiungi la gestione problemi
- ✗ Errore comune: progetto da 18 mesi per implementare "tutto ITIL in una volta"

**4. Collaborate and Promote Visibility (Collaborare)**
L'IT non lavora in silos. Ogni cambiamento impatta altri team.
- ✓ Applicazione: prima di manutenere il server del CRM, avvisa il team vendite con almeno 48 ore di preavviso
- ✗ Errore comune: manutenzione alle 22:00 "perché tanto non ci lavora nessuno" → ma il team americano usa quel CRM di notte

**5. Think and Work Holistically (Pensiero olistico)**
Ogni componente IT è connesso agli altri. Un cambiamento su A può rompere B in modo imprevedibile.
- ✓ Applicazione: prima di aggiornare il database, verifica le applicazioni dipendenti, i backup, il monitoring
- ✗ Errore comune: "Ho aggiornato solo il database, non capisco perché l'applicazione non funziona più"

**6. Keep It Simple and Practical (Semplicità)**
Se un processo non viene seguito perché è troppo complesso, non serve a niente.
- ✓ Applicazione: un modello di change request con 5 campi essenziali compilato correttamente da tutti > un modulo da 30 campi compilato a metà da pochi
- ✗ Errore comune: processi perfetti sulla carta, abbandonati nella pratica

**7. Optimize and Automate (Ottimizzare poi automatizzare)**
Prima rendi efficiente il processo manuale. Poi automatizzalo. Automatizzare il caos produce caos più veloce.
- ✓ Applicazione: ottimizza il processo di backup manuale → poi automatizzalo con script → poi monitorane l'esecuzione
- ✗ Errore comune: automatizzare un processo buggato → i bug si propagano in modo sistemico

**Perché mi interessa?** Quando ti troverai di fronte a una decisione difficile in IT — "devo farlo ora o aspettare la change window?", "devo usare il workaround o aspettare la soluzione corretta?" — i 7 principi ti danno un framework per decidere in modo consistente con gli standard professionali.

---

### Concetto A5: Le 4 Dimensioni — Perché i Processi Perfetti Falliscono

> **Analogia.** Un'orchestra suona una sinfonia perfetta anche se i musicisti sono bravi. Ma cosa succede se il direttore d'orchestra è assente (Organizzazione)? Se gli spartiti sono sbagliati (Informazioni)? Se gli strumenti sono rotti (Tecnologia)? Se il fornitore di strumenti ha consegnato in ritardo (Fornitori)? Una singola dimensione compromessa manda in fumo l'esecuzione.

ITIL v4 identifica quattro dimensioni che devono essere tutte in equilibrio per erogare servizi efficacemente:

```
                    FATTORI POLITICI, ECONOMICI, SOCIALI,
                    TECNOLOGICI, LEGALI, AMBIENTALI (PESTLE)
                              (il contesto esterno)
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
  ┌───────────▼──────────┐  ┌────────▼────────┐  ┌──────────▼──────────┐
  │  1. ORGANIZATIONS    │  │  2. INFORMATION  │  │  3. PARTNERS &      │
  │     AND PEOPLE       │  │     AND          │  │     SUPPLIERS       │
  │                      │  │     TECHNOLOGY   │  │                     │
  │  • Struttura org     │  │  • Dati, CMDB    │  │  • Fornitori HW/SW  │
  │  • Competenze        │  │  • Tool e piatt. │  │  • Contratti SLA    │
  │  • Cultura           │  │  • Knowledge base│  │  • Outsourcing      │
  │  • Formazione        │  │  • Automation    │  │  • Partner cloud    │
  └──────────────────────┘  └─────────────────┘  └─────────────────────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      │
              ┌───────────────────────▼───────────────────────┐
              │         4. VALUE STREAMS AND PROCESSES        │
              │                                               │
              │  • Flussi di lavoro end-to-end               │
              │  • Come la domanda diventa valore             │
              │  • Procedure operative                        │
              │  • Metriche e KPI                            │
              └───────────────────────────────────────────────┘
                                      │
                              SERVIZI EROGATI
```

**Come le 4 dimensioni si manifestano nella pratica:**

| Scenario | Dimensione mancante | Conseguenza |
|---|---|---|
| Il processo di gestione incidenti è perfetto, ma il team helpdesk non è formato | People (Org.) | Incidenti gestiti male nonostante le buone procedure |
| Il CMDB è aggiornato, ma non c'è un tool per consultarlo facilmente | Technology (IT) | Nessuno usa il CMDB; le informazioni esistono ma non sono accessibili |
| Le procedure interne sono ottime, ma il fornitore del server risponde in 48h | Partners | Il SLA verso l'utente non può essere rispettato |
| Il team è bravo e i tool sono ottimi, ma non c'è un processo formale di escalation | Value Streams | Gli incidenti complessi restano senza responsabile chiaro |

**Perché mi interessa?** Quando analizzi un problema operativo ricorrente ("perché i ticket P1 non vengono risolti nel SLA?"), le 4 dimensioni ti danno un framework sistematico per trovare la causa radice invece di dare la colpa "al tool che non funziona" o "alle persone incompetenti".

---

### Concetto A6: La Service Value Chain — Come la Domanda Diventa Valore

> **Analogia.** Immagina una pizzeria. Riceve un ordine (domanda). Lo chef pianifica la produzione, l'addetto agli acquisti procura gli ingredienti, il pizzaiolo crea la pizza, il cameriere la consegna al cliente. Ogni fase trasforma l'input (ordine) in output (pizza) fino al valore finale (cliente soddisfatto). La Service Value Chain è questo processo applicato all'IT.

La Service Value Chain ha 6 attività che interagiscono in modo non lineare — non sono fasi sequenziali, ma attività che si intrecciano:

```
DOMANDA ──────────────────────────────────────────────── VALORE
   │                                                        ↑
   │  ┌─────────────────────────────────────────────────┐  │
   │  │                PLAN (Pianificare)                │  │
   │  │  Direzione strategica e tattica per i servizi   │  │
   │  └──────────────────────┬──────────────────────────┘  │
   │                         │                              │
   │  ┌──────────────────────▼──────────────────────────┐  │
   │  │               IMPROVE (Migliorare)               │  │
   │  │  Identificare e implementare miglioramenti       │  │
   │  └──────────────────────┬──────────────────────────┘  │
   │                         │                              │
   │  ┌──────────────────────▼──────────────────────────┐  │
   │  │               ENGAGE (Coinvolgere)               │  │
   │  │  Interazione con stakeholder, clienti, utenti    │  │
   │  └──────────────────────┬──────────────────────────┘  │
   │                         │                              │
   │  ┌──────────────────────▼──────────────────────────┐  │
   │  │         DESIGN AND TRANSITION (Progettare)       │  │
   │  │  Progettare servizi e portarli in produzione     │  │
   │  └──────────────────────┬──────────────────────────┘  │
   │                         │                              │
   │  ┌──────────────────────▼──────────────────────────┐  │
   │  │            OBTAIN/BUILD (Costruire)              │  │
   │  │  Acquisire o costruire componenti e risorse      │  │
   │  └──────────────────────┬──────────────────────────┘  │
   │                         │                              │
   └──►  ┌───────────────────▼──────────────────────────┐  │
         │        DELIVER AND SUPPORT (Erogare)          ├──┘
         │  Erogare i servizi e supportare gli utenti    │
         └──────────────────────────────────────────────┘
```

**Esempio pratico:** Un'azienda decide di implementare lo smart working (domanda).

| Attività SVC | Cosa succede concretamente |
|---|---|
| **Plan** | IT decide: VPN, laptop aziendali, Microsoft 365, policy di sicurezza |
| **Obtain/Build** | Acquisto 50 laptop, configurazione VPN, licenze M365 |
| **Design/Transition** | Test con 10 utenti pilota, formazione, procedure di supporto |
| **Engage** | Comunicazione agli utenti, raccolta feedback, gestione aspettative |
| **Deliver/Support** | Helpdesk per problemi VPN, supporto tecnico remoto |
| **Improve** | Analisi: il 30% dei ticket riguarda la VPN → migliora client VPN |

**Perché mi interessa?** La SVC spiega perché un cambiamento "semplice" richiede coordinazione tra tanti team. Quando ti chiedono di "aggiungere un server", implicitamente stai attraversando Plan (è nel budget?), Obtain/Build (acquisto/provisioning), Design/Transition (test, documentazione), e Deliver/Support (monitoring, supporto).

---

### Concetto A7: Le 34 Practice ITIL — La Cassetta degli Attrezzi

> **Analogia.** Un idraulico ha una cassetta degli attrezzi con chiavi inglesi, pinze, sigillanti, misuratori di pressione — ogni attrezzo serve per un lavoro specifico. Le 34 Practice ITIL sono la cassetta degli attrezzi dell'IT Operations. Non usi tutti gli attrezzi per ogni lavoro, ma devi sapere cosa c'è nella cassetta e quando usarlo.

ITIL v4 ha 34 practice organizzate in 3 categorie:

**General Management Practices (14)** — applicabili a tutta l'organizzazione, non solo all'IT:

| Practice | Scopo |
|---|---|
| Strategy Management | Direzione strategica dell'organizzazione |
| Portfolio Management | Gestione del portfolio di servizi/progetti |
| Architecture Management | Design dell'architettura enterprise |
| Service Financial Management | Budgeting, accounting, charging |
| **Workforce and Talent Management** | Gestione delle competenze del team IT |
| Continual Improvement | Miglioramento sistematico di servizi e processi |
| Measurement and Reporting | Metriche, KPI, dashboard |
| Risk Management | Identificazione e mitigazione dei rischi |
| Information Security Management | Sicurezza delle informazioni |
| **Knowledge Management** | Knowledge base, documentazione |
| Organizational Change Management | Gestione del cambiamento culturale |
| Project Management | Gestione progetti IT |
| Relationship Management | Relazioni con clienti e stakeholder |
| Supplier Management | Gestione fornitori e contratti |

**Service Management Practices (17)** — specifiche per i servizi IT:

| Practice | Scopo | Priorità per Ops |
|---|---|---|
| **Incident Management** | Ripristino rapido di servizi interrotti | ⭐⭐⭐⭐⭐ |
| **Problem Management** | Eliminare le cause radice degli incidenti | ⭐⭐⭐⭐⭐ |
| **Change Enablement** | Controllo delle modifiche all'infrastruttura | ⭐⭐⭐⭐⭐ |
| **Service Desk** | Punto di contatto singolo con gli utenti | ⭐⭐⭐⭐⭐ |
| **Service Level Management** | Definizione e monitoraggio degli SLA | ⭐⭐⭐⭐ |
| **Monitoring & Event Mgmt** | Rilevamento proattivo di anomalie | ⭐⭐⭐⭐ |
| IT Asset Management | Ciclo di vita degli asset IT | ⭐⭐⭐⭐ |
| Service Configuration Management | Gestione CMDB | ⭐⭐⭐⭐ |
| Service Request Management | Gestione richieste standard | ⭐⭐⭐ |
| Release Management | Gestione rilasci | ⭐⭐⭐ |
| Availability Management | Garantire la disponibilità dei servizi | ⭐⭐⭐ |
| Capacity & Performance Mgmt | Pianificazione capacità | ⭐⭐⭐ |
| Continuity Management | Business continuity e DR | ⭐⭐⭐ |
| Service Design | Progettazione nuovi servizi | ⭐⭐ |
| Service Catalogue Management | Catalogo servizi IT | ⭐⭐ |
| Service Validation & Testing | Test prima del go-live | ⭐⭐ |
| Service Continuity Management | Piani di continuità operativa | ⭐⭐ |

**Technical Management Practices (3)** — specifiche per la tecnologia:

| Practice | Scopo |
|---|---|
| Deployment Management | Deploy di software e infrastruttura |
| Infrastructure and Platform Management | Gestione infrastruttura IT |
| Software Development and Management | Gestione del ciclo di vita del software |

**Quali pratiche studieremo in questo corso?**

Questo corso si concentra sulle practice più rilevanti per un IT Operations engineer in una PMI o PA italiana:

```
TIER 1 (tutorial ops01-ops03):   Incident, Problem, Change, Service Desk
TIER 2 (tutorial ops04-ops07):   Monitoring, Asset, Configuration, SLM
TIER 3 (tutorial ops08-ops12):   Knowledge, Release, Availability, Capacity
TIER 4 (tutorial ops13-ops16):   Security-related practices
```

**Perché mi interessa?** Le 34 practice sono il vocabolario del tuo lavoro futuro. Quando il tuo manager chiede "come gestiamo i problemi ricorrenti?", la risposta corretta non è "lo risolvo ogni volta" — è "implementiamo Problem Management con Root Cause Analysis e Known Error Database". Conoscere le practice ITIL ti permette di dare risposte professionali e strutturate.

---

## PART B: OPERAZIONI — Installare GLPI e Praticare i Concetti ITIL

> In questa sezione installiamo GLPI, il sistema di ticketing open-source più usato nelle PA e PMI italiane, e lo usiamo come "laboratorio pratico" per vedere come i concetti ITIL si traducono in strumenti reali. GLPI implementa nativamente le practice ITIL: incident management, service request, change management, CMDB.

---

### Esercizio B1: Installare Docker su SRV-LINUX-01

**Obiettivo.** Installare Docker su SRV-LINUX-01 — useremo Docker per avviare GLPI in modo rapido senza dover configurare manualmente Apache, PHP, MariaDB e dipendenze.

**Background.** Docker è una piattaforma di containerizzazione: invece di installare un'applicazione direttamente sul sistema operativo (con tutte le sue dipendenze e potenziali conflitti), si esegue l'applicazione in un "container" — un ambiente isolato che contiene tutto il necessario. L'analogia è quella di uno sgabuzzino separato per ogni applicazione: non si toccano, non si disturbano.

> I container Docker verranno approfonditi nel tutorial ops04 (Virtualizzazione). Per ora, trattalo come uno strumento che ti permette di avviare applicazioni complesse con un solo comando.

```bash
# Accedi a SRV-LINUX-01 (da WKS-LAB-01 via SSH, oppure direttamente dalla VM)
ssh lab-admin@192.168.56.20

# Aggiorna i package list
sudo apt-get update

# Installa le dipendenze per HTTPS
sudo apt-get install -y ca-certificates curl gnupg

# Aggiunge la chiave GPG ufficiale Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Aggiunge il repository Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installa Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Aggiungi lab-admin al gruppo docker (per evitare sudo ogni volta)
sudo usermod -aG docker lab-admin

# Applica il cambio di gruppo senza rilogarsi
newgrp docker

# Verifica installazione
docker --version
docker compose version
```

Output atteso:
```
Docker version 26.x.x, build xxxxxxx
Docker Compose version v2.x.x
```

```bash
# Test funzionamento Docker
docker run hello-world
```

Output atteso (ultima parte):
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

**Checkpoint di verifica B1:**
- [ ] `docker --version` mostra versione 26.x o superiore
- [ ] `docker compose version` mostra versione 2.x
- [ ] `docker run hello-world` completa senza errori

---

### Esercizio B2: Avviare GLPI con Docker Compose

**Obiettivo.** Avviare GLPI 10.x usando Docker Compose — lo strumento che gestisce applicazioni multi-container. GLPI richiede un web server (nginx), un database (MariaDB) e PHP.

```bash
# Crea la directory per GLPI
mkdir -p ~/glpi-lab && cd ~/glpi-lab

# Crea il file docker-compose.yml
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  db:
    image: mariadb:10.11
    container_name: glpi-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: GlpiRootPass123!
      MYSQL_DATABASE: glpidb
      MYSQL_USER: glpiuser
      MYSQL_PASSWORD: GlpiDbPass123!
    volumes:
      - glpi-db-data:/var/lib/mysql
    networks:
      - glpi-net

  glpi:
    image: diouxx/glpi:10.0.16
    container_name: glpi-app
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - "8080:80"
    environment:
      MARIADB_HOST: db
      MARIADB_PORT: 3306
      MARIADB_DATABASE: glpidb
      MARIADB_USER: glpiuser
      MARIADB_PASSWORD: GlpiDbPass123!
    volumes:
      - glpi-app-data:/var/www/html/glpi/files
      - glpi-plugins:/var/www/html/glpi/plugins
    networks:
      - glpi-net

volumes:
  glpi-db-data:
  glpi-app-data:
  glpi-plugins:

networks:
  glpi-net:
    driver: bridge
COMPOSE_EOF

# Avvia GLPI
docker compose up -d

# Monitora l'avvio (attendi 60-90 secondi)
docker compose logs -f
# Premi Ctrl+C quando vedi "Apache/2.4.xx Server started"
```

**Verifica che GLPI risponda:**

```bash
# Test da SRV-LINUX-01
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
# Atteso: 200 o 302
```

Da **WKS-LAB-01** (Windows 10), apri il browser e vai a: `http://192.168.56.20:8080/`

Dovresti vedere la schermata di installazione di GLPI.

**Checkpoint di verifica B2:**
- [ ] `docker compose ps` mostra 2 container in stato `running` (glpi-db, glpi-app)
- [ ] Browser su WKS-LAB-01 mostra la schermata di setup di GLPI

**Cosa potrebbe andare storto:**
1. *"Porta 8080 non raggiungibile"* → Verifica il firewall Ubuntu: `sudo ufw status`; se è attivo, aggiungi `sudo ufw allow 8080/tcp`
2. *"glpi-app resta in Restarting"* → Il database impiega più tempo; attendi 2 minuti e riprova `docker compose ps`

---

### Esercizio B3: Configurare GLPI (Setup Iniziale)

**Obiettivo.** Completare la configurazione iniziale di GLPI e adattarla al contesto ITIL del lab.

**Procedura da WKS-LAB-01 (browser):**

1. Vai su `http://192.168.56.20:8080/`
2. Schermata "Benvenuto in GLPI" → clicca **Continue**
3. Schermata database: compila con:
   - SQL Server: `db`
   - SQL User: `glpiuser`
   - SQL Password: `GlpiDbPass123!`
4. Seleziona database: `glpidb` → Continue
5. Installazione completata → clicca il link per accedere a GLPI

**Login iniziale:**
- Username: `glpi`
- Password: `glpi`

> ATTENZIONE: GLPI mostra un avviso di sicurezza perché usi le credenziali di default. Nel lab è accettabile; in produzione cambieresti immediatamente la password.

**Configurazione base (Setup → General):**

1. **Setup → General → General Setup:**
   - URL: `http://192.168.56.20:8080`
   - Default Language: Italiano
2. **Administration → Entities:**
   - Rinomina l'entità root: `Lab IT Corporation`
   - Imposta localizzazione: Italy
3. **Administration → Users → Add User:**

| Campo | Valore |
|---|---|
| Login | it-admin |
| Password | Lab@2024! |
| Email | it-admin@lab.local |
| First name | Admin |
| Surname | IT |
| Profile | Super-Admin |

**Checkpoint di verifica B3:**
- [ ] Login con `glpi`/`glpi` funzionante
- [ ] GLPI mostra dashboard in italiano
- [ ] Utente `it-admin` creato e funzionante
- [ ] Entità root rinominata in "Lab IT Corporation"

---

### Esercizio B4: Classificare Scenari ITIL — SR vs Incident vs Problem vs Change

**Obiettivo.** Applicare le definizioni ITIL per classificare correttamente le richieste — la skill più fondamentale in IT Operations. Una classificazione errata porta al team sbagliato, SLA sbagliati, metriche distorte.

**Le definizioni di riferimento:**

| Tipo | Definizione | Caratteristica chiave |
|---|---|---|
| **Service Request (SR)** | Richiesta formale per qualcosa di predefinito e standard | È VOLUTA, pianificabile, non urgente di default |
| **Incident** | Interruzione non pianificata di un servizio | È NON VOLUTA, impatta la produttività ADESSO |
| **Problem** | Causa radice di uno o più incidenti | È un'analisi: il "perché" si verificano gli incidenti |
| **Change (RFC)** | Proposta di modifica all'infrastruttura IT | Richiede pianificazione, approvazione, rollback plan |

**Esercizio pratico — Classifica questi 12 scenari:**

Per ognuno, decidi il tipo (SR/Incident/Problem/Change) e la priorità (P1/P2/P3/P4) se applicabile. Le risposte corrette sono nella sezione successiva.

```
SCENARIO 01: "Il sito web dell'azienda non risponde da 30 minuti. 
              500 clienti non riescono ad acquistare."
Tipo: ?    Priorità: ?

SCENARIO 02: "Mario Rossi si è trasferito in un altro ufficio 
              e ha bisogno di una nuova porta d'accesso."
Tipo: ?    Priorità: ?

SCENARIO 03: "Il server email va in crash ogni martedì tra le 10:00 
              e le 11:00. Questa settimana è la quarta volta."
Tipo: ?    Priorità: ?

SCENARIO 04: "Dobbiamo aggiornare il firewall dalla versione 7.1 
              alla 8.0 per aggiungere il supporto TLS 1.3."
Tipo: ?    Priorità: ?

SCENARIO 05: "Una stampante di rete dell'ufficio acquisti non stampa. 
              I colleghi usano la stampante vicina temporaneamente."
Tipo: ?    Priorità: ?

SCENARIO 06: "L'ERP aziendale risponde lentamente — 
              operazioni che prima richiedevano 2 sec ora ne richiedono 45."
Tipo: ?    Priorità: ?

SCENARIO 07: "Anna Bianchi, nuova assunta, ha bisogno 
              delle credenziali di accesso al dominio."
Tipo: ?    Priorità: ?

SCENARIO 08: "Il database di produzione è corrotto e 
              il CEO non riesce ad accedere ai report finanziari."
Tipo: ?    Priorità: ?

SCENARIO 09: "5 utenti diversi hanno segnalato 'disco pieno' 
              sui loro PC nelle ultime 2 settimane."
Tipo: ?    Priorità: ?

SCENARIO 10: "Il team DevOps vuole aggiungere 2 TB di storage 
              al server NAS per i backup automatici."
Tipo: ?    Priorità: ?

SCENARIO 11: "Il servizio VPN non funziona. 30 dipendenti 
              in smart working non riescono a connettersi."
Tipo: ?    Priorità: ?

SCENARIO 12: "L'antivirus su 3 workstation ha rilevato malware. 
              Le macchine sono state isolate automaticamente."
Tipo: ?    Priorità: ?
```

**Risposte corrette e motivazioni:**

```
SC01: INCIDENT P1 — Sito web down, impatto diretto sul fatturato. Alta urgenza + alto impatto = P1.

SC02: SERVICE REQUEST — Richiesta standard, pianificabile. Nessuna interruzione di servizio.

SC03: PROBLEM — Un incidente ricorrente con pattern riconoscibile richiede analisi della causa radice (RCA). 
       Il crash del martedì potrebbe essere: job batch, backup, picco di traffico settimanale.

SC04: CHANGE — Modifica pianificata all'infrastruttura. Richiede RFC, CAB review, change window, rollback plan.

SC05: INCIDENT P4 — Servizio degradato (non completamente down), con workaround disponibile. 
       Impatto basso + urgenza bassa = P4.

SC06: INCIDENT P2 — Degradazione significativa di un servizio critico (ERP). 
       Alto impatto + media urgenza (workaround parziale possibile) = P2.

SC07: SERVICE REQUEST — Onboarding standard. Richiesta pianificabile e ripetibile.

SC08: INCIDENT P1 — Database corrotto, CEO impattato, processo di business critico bloccato = P1.

SC09: PROBLEM — 5 segnalazioni simili nel tempo suggeriscono una causa radice sistemica 
       (es. log che non ruotano, software che accumula temp files).

SC10: CHANGE — Aggiunta di storage: modifica pianificata all'infrastruttura. RFC obbligatorio.

SC11: INCIDENT P1 — 30 utenti bloccati in smart working. Alta urgenza + alto impatto = P1/P2 
       (P1 se il servizio è completamente down, P2 se parzialmente funzionante).

SC12: INCIDENT P1 + potenziale PROBLEM — Attacco in corso: P1 immediato per contenimento. 
       Dopo la risoluzione, aprire un Problem per analizzare come il malware è entrato.
```

> **Pattern da ricordare:**
> - **Stesso incidente si ripete** → apri anche un Problem
> - **Più incidenti simili nello stesso periodo** → apri un Problem
> - **Stai per modificare qualcosa** → apri un Change
> - **L'utente chiede qualcosa di standard** → è una SR
> - **Qualcosa è rotto adesso** → è un Incident

**Pratica su GLPI — Crea 3 ticket:**

Accedi a GLPI come `it-admin` e crea:

1. **Ticket #1 — Service Request:**
   - Titolo: "Creazione account per nuovo dipendente - Marco Verdi"
   - Categoria: Gestione Utenti → Nuovo Accesso
   - Tipo: Richiesta
   - Descrizione: "Il dipendente Marco Verdi inizia il 20/07/2026. Necessita: account AD, email, accesso VPN, licenza Office 365."

2. **Ticket #2 — Incident P2:**
   - Titolo: "Sistema email lento - tempi di consegna 5-10 minuti"
   - Categoria: Servizi di Comunicazione → Email
   - Tipo: Incidente
   - Urgenza: Alta
   - Impatto: Alto
   - Priorità: (GLPI la calcola automaticamente) → P2

3. **Ticket #3 — Change:**
   - Titolo: "Aggiornamento firewall Fortinet da 7.2 a 7.4"
   - Categoria: Infrastruttura di Rete → Firewall
   - Tipo: Change
   - Data implementazione: prossimo sabato alle 22:00
   - Descrizione impatto: "Interruzione connettività internet 30-60 minuti durante l'aggiornamento"

**Checkpoint di verifica B4:**
- [ ] Hai classificato correttamente almeno 10 dei 12 scenari
- [ ] Hai creato 3 ticket in GLPI con tipi diversi (SR, Incident, Change)
- [ ] GLPI ha calcolato correttamente la priorità del ticket #2 come P2

---

### Esercizio B5: Applicare i 7 Principi Guida a Decisioni Reali

**Obiettivo.** Trasformare i 7 Principi da concetti astratti a strumenti concreti per prendere decisioni difficili. Questo esercizio presenta dilemmi reali che ogni IT Operations engineer affronta.

Per ogni scenario, identifica quale/i principio/i guidano la decisione corretta e spiega perché.

**Dilemma 01: "Il tecnico veloce vs il tecnico corretto"**

```
Situazione: È venerdì alle 17:45. Un utente segnala che il suo PC non si 
connette alla rete. Il tecnico scopre che il problema è il cavo di rete 
sfila nel patch panel. Può:
A) Cambiare il cavo in 5 minuti e far funzionare tutto
B) Aprire un ticket formale, fare l'analisi, documentare, programmare 
   l'intervento per lunedì

Qual è la risposta ITIL corretta? E quale principio guida?
```

Risposta: La soluzione **A** è quella corretta in questo caso, ma con documentazione.

Principio applicato: *Keep It Simple and Practical* + *Focus on Value*. Il valore per l'utente è avere il PC funzionante. La procedura formale (B) ha senso per sistemi complessi; per un cavo sfila, aggiunge burocrazia senza valore.

**Ma attenzione:** Anche applicando A, si apre il ticket in modo retroattivo per tracciare l'intervento. "Semplicità" non significa "non documentare".

**Dilemma 02: "Il software nuovo vs il processo migliorato"**

```
Situazione: Il team IT sta valutando di comprare ServiceNow Enterprise 
(costo: 50.000€/anno) perché il processo di gestione incidenti è caotico. 
L'attuale tool è GLPI (gratuito). Il consulente dice "vi serve uno strumento 
migliore". Il CTO dice "prima i processi, poi i tool".

Chi ha ragione?
```

Risposta: Il CTO ha ragione.

Principio applicato: *Start Where You Are* + *Keep It Simple*. Il problema non è il tool — se il processo è caotico in GLPI, sarà caotico anche in ServiceNow. Prima si ottimizzano i processi, poi si valuta se lo strumento è il collo di bottiglia. ServiceNow può avere senso per un'organizzazione enterprise con centinaia di tecnici; per una PMI con 10 tecnici, GLPI configurato bene è più che sufficiente.

**Dilemma 03: "La manutenzione programmata vs la richiesta urgente"**

```
Situazione: Hai programmato la manutenzione del server ERP per sabato notte 
(23:00-03:00). Venerdì pomeriggio arriva una richiesta dal CFO: 
"Ho bisogno di un report urgente domani mattina alle 8:00 — 
non posso permettere downtime del server stanotte."

Cosa fai?
```

Risposta: Coinvolgi il CFO nella decisione, presenta le opzioni con i loro rischi, ottieni un'approvazione formale.

Principio applicato: *Collaborate and Promote Visibility*. Non decidere da solo. Le opzioni sono: (1) procrastinare la manutenzione di 1 settimana — rischio: il problema che stavi risolvendo potrebbe peggiorare; (2) procedere con la manutenzione — rischio: il CFO non ha il report alle 8; (3) fare solo la parte non rischiosa della manutenzione e rimandare il resto. Il principio ti dice che questa decisione appartiene al business (CFO), non all'IT.

**Scrivi le tue risposte in GLPI:**

Crea un Knowledge Article in GLPI per documentare le decisioni prese:

GLPI → Tools → Knowledge base → Add an article:
- Titolo: "Decision Framework: 7 Principi Guida ITIL — Esempi Pratici"
- Categoria: ITIL Guidelines
- Contenuto: copia i 3 dilemmi con le tue risposte

**Checkpoint di verifica B5:**
- [ ] Hai analizzato tutti e 3 i dilemmi identificando il principio ITIL applicabile
- [ ] Hai creato il Knowledge Article in GLPI
- [ ] Sai spiegare a parole tue la differenza tra "semplicità" e "non documentare"

---

### Esercizio B6: Costruire il Catalogo dei Servizi

**Obiettivo.** Creare un Service Catalogue elementare — la lista ufficiale dei servizi IT erogati dall'organizzazione. Il Service Catalogue è la "vetrina" dell'IT verso gli utenti: definisce cosa esiste, chi può richiederlo, e con quali garanzie (SLA).

**Perché il Service Catalogue è importante?**

Senza un catalogo servizi:
- Gli utenti non sanno cosa possono chiedere all'IT
- L'IT non sa come priorizzare le richieste
- Non è possibile definire SLA senza sapere quali servizi esistono
- Non è possibile calcolare i costi dell'IT per servizio

**Template Service Catalogue per "Lab IT Corporation":**

Crea il file `service_catalogue_v1.md` in una cartella `docs/` sul WKS-LAB-01:

```markdown
# Service Catalogue — Lab IT Corporation
**Versione:** 1.0  
**Data:** 2026-07-15  
**Proprietario:** IT Operations Team  

---

## Servizi di Produttività

### SRV-001: Email Aziendale (Microsoft 365)
**Descrizione:** Accesso alla posta elettronica, calendario e contatti aziendali.  
**Disponibilità:** 24/7 (esclusa manutenzione programmata)  
**SLA:** 99.5% uptime mensile  
**Tempo di ripristino P1:** 1 ora  
**Come richiedere:** Ticket SR in GLPI → categoria Email  
**In scope:** Account creazione/modifica, configurazione client, accesso mobile  
**Out of scope:** Recupero email cancellate da >30 giorni, migrazione da altri provider  

### SRV-002: Connettività VPN
**Descrizione:** Accesso sicuro alla rete aziendale da remoto.  
**Disponibilità:** 24/7  
**SLA:** 99% uptime mensile  
**Tempo di ripristino P1:** 2 ore  
**Come richiedere:** Ticket SR → categoria VPN  
**In scope:** Creazione account VPN, reset password, configurazione client  
**Out of scope:** Problemi di connettività internet del cliente (responsabilità dell'ISP)  

---

## Servizi Infrastruttura

### SRV-010: Gestione Server e Virtualizzazione
**Descrizione:** Provisioning e gestione VM, monitoring, backup.  
**Disponibilità:** 24/7 (supporto H24 solo P1/P2)  
**SLA:** Server critici 99.9% / Server non critici 99%  
**Tempo di ripristino P1:** 1 ora  
**Come richiedere:** Ticket Change per modifiche, Incident per problemi  
**In scope:** Windows Server, Ubuntu Server, VirtualBox, backup  
**Out of scope:** Hardware fisico (responsabilità del fornitore hardware)  

### SRV-011: Backup e Disaster Recovery
**Descrizione:** Backup giornaliero dei dati critici, restore su richiesta.  
**RTO (Recovery Time Objective):** 4 ore per dati critici  
**RPO (Recovery Point Objective):** 24 ore (backup giornaliero)  
**Come richiedere:** Ticket SR per restore, Incident per failure di backup  

---

## Servizi di Supporto

### SRV-020: Service Desk (Helpdesk)
**Descrizione:** Supporto tecnico agli utenti per problemi e richieste.  
**Orari:** Lun-Ven 08:00-18:00 (supporto P1/P2 H24)  
**Canali:** GLPI (preferito), telefono (solo P1), email  
**SLA SR:** Risposta entro 4 ore lavorative  
**SLA Incident P1:** Risposta entro 15 minuti  

---

## Matrice Responsabilità (RACI semplificata)

| Servizio | IT Ops | Service Desk | Security | Management |
|---|---|---|---|---|
| Email | A | R | C | I |
| VPN | A/R | R | C | I |
| Server | A/R | I | C | I |
| Backup | A/R | I | I | I |
| Helpdesk | C | A/R | I | I |

*R=Responsible (fa il lavoro), A=Accountable (risponde del risultato), C=Consulted, I=Informed*
```

**Inserisci il catalogo in GLPI:**

GLPI → Setup → Dropdowns → ITIL Categories → Add:

Crea queste categorie principali:
- Produttività → Email → Accesso / Configurazione / Problemi
- Produttività → VPN → Accesso / Configurazione / Problemi
- Infrastruttura → Server → Provisioning / Incidenti / Manutenzione
- Infrastruttura → Backup → Richieste Restore / Failure
- Supporto → Helpdesk Generico

**Checkpoint di verifica B6:**
- [ ] File `service_catalogue_v1.md` creato con almeno 3 servizi definiti
- [ ] Categorie create in GLPI riflettono il catalogo
- [ ] Hai identificato per ogni servizio: SLA, RTO/RPO se applicabile, canale di richiesta

---

## PART C: SISTEMATIZZARE — Dall'Apprendimento alla Governance ITIL

> Hai visto i concetti (Part A) e hai praticato con gli strumenti (Part B). In questa sezione costruiamo le strutture di governance che permettono di applicare ITIL in modo sistematico e migliorativo nel tempo — non come knowledge personale, ma come processo organizzativo.

---

### Progetto C1: SOP "Gestione del Ciclo di Vita del Ticket"

**Obiettivo.** Documentare il processo end-to-end dalla segnalazione alla chiusura di un ticket GLPI, in modo che qualsiasi membro del team possa seguirlo senza formazione aggiuntiva.

Questa SOP implementa le Practice ITIL: **Incident Management**, **Service Request Management** e parzialmente **Problem Management**.

```markdown
# SOP ITSM-001: Gestione del Ciclo di Vita del Ticket

**Versione:** 1.0  
**Data:** [data corrente]  
**Scope:** Tutti i ticket aperti su GLPI per Lab IT Corporation  
**Prerequisiti:** Accesso GLPI, training base classificazione SR/Incident/Problem/Change  

---

## 1. Apertura del Ticket

### 1.1 Chi può aprire ticket?
- Qualsiasi utente registrato in GLPI (tramite portale self-service)
- Il Service Desk (per segnalazioni telefoniche o verbali)
- Il sistema di monitoring (ticket automatici da alert Zabbix/Prometheus)

### 1.2 Campi obbligatori all'apertura

| Campo | Descrizione | Esempio |
|---|---|---|
| Tipo | SR / Incident / Problem / Change | Incident |
| Titolo | Breve, descrittivo, specifico | "Email non funziona per reparto vendite" |
| Categoria | Dal Service Catalogue | Produttività → Email → Problemi |
| Urgenza | Alta/Media/Bassa | Alta |
| Impatto | Alto/Medio/Basso | Alto |
| Descrizione | Cosa succede, da quando, quanti utenti impattati | (testo libero) |
| Allegati | Screenshot, log, evidenze | (file allegato) |

### 1.3 La Priorità viene calcolata automaticamente
GLPI calcola la priorità dalla matrice Urgenza × Impatto:

| | Urgenza Alta | Urgenza Media | Urgenza Bassa |
|---|---|---|---|
| Impatto Alto | P1 Critico | P2 Alto | P3 Medio |
| Impatto Medio | P2 Alto | P3 Medio | P4 Basso |
| Impatto Basso | P3 Medio | P4 Basso | P5 Molto basso |

---

## 2. Presa in Carico e Assegnazione

### 2.1 SLA di risposta per priorità

| Priorità | Tempo di Risposta | Tempo di Risoluzione |
|---|---|---|
| P1 Critico | 15 minuti | 1 ora |
| P2 Alto | 30 minuti | 4 ore |
| P3 Medio | 2 ore | 8 ore lavorative |
| P4 Basso | 4 ore | 24 ore lavorative |
| P5 Pianificato | 8 ore | 5 giorni lavorativi |

### 2.2 Criteri di assegnazione

- **Tecnico che risponde per primo** prende in carico il ticket e aggiorna lo stato a "In corso"
- **Escalation automatica**: se P1 non preso in carico in 15 minuti → notifica al team leader
- **Riassegnazione**: se il tecnico non ha le competenze → riassegna con commento motivato

---

## 3. Gestione e Comunicazione

### 3.1 Aggiornamenti obbligatori al ticket

| Evento | Azione richiesta nel ticket |
|---|---|
| Presa in carico | Cambio stato → "In corso", assegnazione al tecnico |
| Workaround trovato | Commento con descrizione workaround, aggiornamento utente |
| Ritardo previsto | Commento con nuovo ETA, notifica utente |
| Escalation | Commento + riassegnazione + motivo |
| Risoluzione | Soluzione applicata documentata nel campo "Soluzione" |

### 3.2 Comunicazione con l'utente

- **P1/P2**: aggiornamento ogni 30 minuti finché non risolto
- **P3/P4**: aggiornamento al cambio di stato significativo
- **SR**: aggiornamento alla presa in carico e alla chiusura

---

## 4. Chiusura del Ticket

### 4.1 Criteri di chiusura

Un ticket può essere chiuso solo quando:
- [ ] Il servizio è ripristinato alla normalità (o la SR è evasa)
- [ ] L'utente ha confermato la risoluzione (o è trascorso il periodo di auto-chiusura: 3 giorni lavorativi)
- [ ] La soluzione è documentata nel campo apposito
- [ ] La Knowledge Base è aggiornata se la soluzione può essere utile in futuro

### 4.2 Auto-chiusura

Dopo 3 giorni lavorativi senza risposta dell'utente alla notifica di risoluzione, il ticket viene chiuso automaticamente con nota "Auto-chiuso per mancata risposta utente entro 3 giorni lavorativi".

---

## 5. Post-Incident Review (per P1/P2)

Entro 24 ore dalla chiusura di un Incident P1 o P2, il tecnico responsabile deve compilare il form PIR (Post-Incident Review):

- Cos'è successo (cronologia con timestamp)
- Causa radice (se identificata)
- Azioni correttive intraprese
- Azioni preventive per il futuro
- Dovrebbe essere aperto un Problem per analisi più approfondita?

---

## 6. Storico Revisioni

| Versione | Data | Modifica |
|---|---|---|
| 1.0 | [data] | Prima versione |
```

---

### Progetto C2: Script di Report KPI ITIL

**Obiettivo.** Creare uno script Python che si connette all'API REST di GLPI ed estrae le metriche ITIL fondamentali — MTTR (Mean Time to Repair), volume ticket per priorità, SLA compliance.

> **Prerequisito:** Python 3.8+ deve essere installato su WKS-LAB-01 o SRV-LINUX-01.

```bash
# Installa Python su SRV-LINUX-01 se non presente
sudo apt-get install -y python3 python3-pip
pip3 install requests tabulate
```

Crea il file `glpi_kpi_report.py` su WKS-LAB-01 o SRV-LINUX-01:

```python
#!/usr/bin/env python3
"""
glpi_kpi_report.py
Estrae metriche ITIL fondamentali dall'API GLPI e genera un report testuale.
"""

import requests
import json
from datetime import datetime, timedelta
from tabulate import tabulate

# --- Configurazione ---
GLPI_URL = "http://192.168.56.20:8080/apirest.php"
APP_TOKEN = ""   # da configurare in GLPI: Setup -> General -> API
USER_TOKEN = ""  # da configurare dopo il login API

HEADERS = {
    "Content-Type": "application/json",
    "App-Token": APP_TOKEN,
    "Session-Token": USER_TOKEN
}


def get_session_token(username: str, password: str) -> str:
    """Ottiene il session token tramite autenticazione GLPI."""
    response = requests.get(
        f"{GLPI_URL}/initSession",
        headers={"App-Token": APP_TOKEN},
        auth=(username, password),
        timeout=10
    )
    response.raise_for_status()
    return response.json()["session_token"]


def get_tickets_summary() -> dict:
    """Recupera il riepilogo dei ticket per priorità e stato."""
    response = requests.get(
        f"{GLPI_URL}/Ticket",
        headers=HEADERS,
        params={
            "range": "0-999",
            "only_id": 0,
            "forcedisplay": json.dumps([1, 3, 10, 12, 14, 15, 17])
            # id, name, priority, status, date, date_mod, solvedate
        },
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def calculate_mttr(tickets: list) -> float:
    """Calcola MTTR (Mean Time To Repair) in ore."""
    resolved = [
        t for t in tickets
        if t.get("status") == 6 and t.get("solvedate")  # status 6 = risolto
    ]
    if not resolved:
        return 0.0

    total_hours = 0.0
    for ticket in resolved:
        created = datetime.fromisoformat(ticket["date"].replace("Z", "+00:00"))
        solved = datetime.fromisoformat(ticket["solvedate"].replace("Z", "+00:00"))
        total_hours += (solved - created).total_seconds() / 3600

    return total_hours / len(resolved)


def print_report(tickets: list) -> None:
    """Stampa il report KPI formattato."""
    priority_names = {1: "P1-Critico", 2: "P2-Alto", 3: "P3-Medio", 4: "P4-Basso", 5: "P5-Pianif."}
    status_names = {1: "Nuovo", 2: "In corso", 3: "In attesa", 4: "In attesa", 5: "Risolto", 6: "Chiuso"}

    print("\n" + "=" * 60)
    print(f"  GLPI KPI REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Distribuzione per priorità
    priority_counts = {}
    for t in tickets:
        p = priority_names.get(t.get("priority", 0), "Sconosciuta")
        priority_counts[p] = priority_counts.get(p, 0) + 1

    print("\n[Ticket per Priorità]")
    print(tabulate(
        [[k, v] for k, v in sorted(priority_counts.items())],
        headers=["Priorità", "Count"],
        tablefmt="grid"
    ))

    # MTTR
    mttr = calculate_mttr(tickets)
    print(f"\n[MTTR (Mean Time To Repair)] {mttr:.1f} ore")
    if mttr > 0:
        if mttr <= 1:
            print("  → Eccellente (< 1 ora)")
        elif mttr <= 4:
            print("  → Buono (1-4 ore)")
        elif mttr <= 8:
            print("  → Nella norma (4-8 ore)")
        else:
            print("  → Attenzione: MTTR elevato (> 8 ore)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("GLPI KPI Reporter")
    print("Nota: configurare APP_TOKEN e USER_TOKEN prima dell'uso.")
    print("Per ora mostriamo un esempio con dati simulati del lab.")

    # Dati esempio (sostituisci con chiamata API reale quando hai il token)
    example_data = [
        {"priority": 1, "status": 6, "date": "2026-07-14T09:00:00Z", "solvedate": "2026-07-14T09:45:00Z"},
        {"priority": 2, "status": 6, "date": "2026-07-14T10:00:00Z", "solvedate": "2026-07-14T13:30:00Z"},
        {"priority": 3, "status": 2, "date": "2026-07-15T08:00:00Z", "solvedate": None},
        {"priority": 4, "status": 1, "date": "2026-07-15T11:00:00Z", "solvedate": None},
        {"priority": 3, "status": 5, "date": "2026-07-13T14:00:00Z", "solvedate": "2026-07-13T20:00:00Z"},
    ]
    print_report(example_data)
```

**Come abilitare l'API GLPI per usarla con dati reali:**

1. GLPI → Setup → General → API:
   - Enable Rest API: YES
   - Enable login with credentials: YES
2. Setup → API clients → Add: IP `192.168.56.0/24` autorizzato
3. Nota l'App Token generato

---

### Progetto C3: Mappa delle Connessioni ITIL nel Lab

**Obiettivo.** Visualizzare come ogni componente del lab corrisponde a un elemento ITIL — così vedi sempre il "perché" dietro ogni strumento.

```
FRAMEWORK ITIL v4               IMPLEMENTAZIONE NEL LAB
═══════════════════              ═══════════════════════════
Service Value System    ←→      Lab IT Corporation (entità GLPI)
  Service Catalogue     ←→      Categorie GLPI configurate in B6
  Service Desk          ←→      GLPI Helpdesk
  
Guiding Principles:
  Focus on Value        ←→      SLA definiti nel Service Catalogue
  Start Where You Are   ←→      GLPI + Excel prima di ServiceNow
  Keep It Simple        ←→      5 categorie, non 50
  
4 Dimensions:
  Organizations+People  ←→      Utenti GLPI, profili, team
  Information+Technology←→      GLPI + API + KPI script
  Partners+Suppliers    ←→      (tutorial ops04: fornitori VirtualBox, MS, Ubuntu)
  Value Streams         ←→      SOP ITSM-001 creata in C1
  
Service Value Chain:
  Plan                  ←→      Service Catalogue, SLA, capacità
  Engage                ←→      Portal self-service GLPI
  Deliver+Support       ←→      Helpdesk, ticket P1-P5
  Improve               ←→      KPI report Python, revisione SLA mensile
  
Practices (in questo tutorial):
  Incident Mgmt         ←→      Ticket tipo Incident in GLPI
  SR Management         ←→      Ticket tipo Richiesta in GLPI
  Knowledge Mgmt        ←→      Knowledge Base GLPI
  Service Level Mgmt    ←→      SLA configurati su ogni ticket
  
(Practices approfondite nei tutorial successivi):
  Problem Management    ←→      tutorial_ops01_ch1b
  Change Enablement     ←→      tutorial_ops01_ch1b
  Asset Management      ←→      tutorial_ops08
  Configuration (CMDB)  ←→      tutorial_ops08_ch1b
  Monitoring+Events     ←→      tutorial_ops07
```

**Come scala da lab a enterprise:**

| Lab (1 tecnico, 3 VM) | Enterprise (50 tecnici, 5000 server) |
|---|---|
| GLPI su Docker (1 container) | GLPI su cluster HA (3 nodi) o ServiceNow SaaS |
| SLA definiti in un file markdown | SLA contrattuali con penali, approvati dal CdA |
| KPI script Python manuale | Dashboard Grafana in tempo reale, alert automatici |
| 5 categorie di servizio | Catalogo di 200+ servizi con versioning |
| 1 SOP Word | Knowledge base strutturata con 500+ articoli |
| Team informale | Struttura ITIL formale: L1/L2/L3, ITIL Manager, Problem Manager |

---

## Checklist di Validazione — Tutorial ops01a Completato

### Fondamenti (Part A)
- [ ] Sai spiegare cos'è ITIL e perché è utile a un principiante
- [ ] Sai disegnare il Service Value System con i suoi 5 elementi
- [ ] Sai elencare i 7 Principi Guida e dare un esempio concreto per ognuno
- [ ] Sai spiegare le 4 Dimensioni con un esempio di cosa succede se una manca
- [ ] Sai distinguere Service Request / Incident / Problem / Change
- [ ] Sai descrivere le 6 attività della Service Value Chain

### Strumenti (Part B)
- [ ] Docker installato su SRV-LINUX-01 (`docker --version` funziona)
- [ ] GLPI accessibile su `http://192.168.56.20:8080/`
- [ ] Login con `it-admin` / `Lab@2024!` funzionante
- [ ] Categorie del Service Catalogue create in GLPI
- [ ] Hai classificato correttamente ≥10/12 scenari dell'esercizio B4
- [ ] 3 ticket di test creati in GLPI (SR, Incident, Change)
- [ ] Knowledge Article sui dilemmi ITIL creato in GLPI

### Governance (Part C)
- [ ] SOP ITSM-001 scritta e salvata (file markdown)
- [ ] Script `glpi_kpi_report.py` creato e testato con dati esempio
- [ ] Mappa di correlazione Lab ↔ ITIL compilata per il tuo contesto

---

## Appendice A: Glossario ITIL v4 Essenziale

| Termine | Definizione |
|---|---|
| **Asset** | Qualsiasi componente che contribuisce alla fornitura di un prodotto o servizio IT |
| **CAB** | Change Advisory Board — comitato che approva i change ad alto rischio |
| **CMDB** | Configuration Management Database — database degli asset e delle loro relazioni |
| **CSI** | Continual Service Improvement — miglioramento continuo dei servizi |
| **KEDB** | Known Error Database — database degli errori noti con workaround documentati |
| **MTBF** | Mean Time Between Failures — tempo medio tra un guasto e il successivo |
| **MTTR** | Mean Time To Repair/Restore — tempo medio per ripristinare un servizio |
| **RFC** | Request for Change — richiesta formale di modifica all'infrastruttura |
| **RCA** | Root Cause Analysis — analisi della causa radice di un problema |
| **RPO** | Recovery Point Objective — massima perdita di dati accettabile (in ore/giorni) |
| **RTO** | Recovery Time Objective — massimo tempo di ripristino accettabile |
| **SLA** | Service Level Agreement — accordo sui livelli di servizio garantiti |
| **SLO** | Service Level Objective — obiettivo di performance interno (es. 99.9% uptime) |
| **SLI** | Service Level Indicator — metrica che misura il performance reale |
| **SVS** | Service Value System — il modello operativo completo di ITIL v4 |
| **Ticket** | Record formale di una SR, Incident, Problem o Change nel sistema di ticketing |
| **Workaround** | Soluzione temporanea che ripristina il servizio senza risolvere la causa radice |

---

## Appendice B: Matrice Tipologie Ticket — Riferimento Rapido

| Caratteristica | Service Request | Incident | Problem | Change |
|---|---|---|---|---|
| **È pianificato?** | Sì | No | No (analisi) | Sì |
| **È urgente?** | Di solito no | Spesso sì | Di solito no | No |
| **Impatta ora?** | No | Sì | Indirettamente | In futuro |
| **Causa root?** | N/A | Sintomo | Causa root | N/A |
| **Richiede approvazione?** | No | No | No | Sì (CAB) |
| **Quando aprire?** | Utente richiede | Servizio rotto | Incidente ricorrente | Prima di una modifica |
| **SLA tipico risposta** | 4 ore | 15 min (P1) | 48 ore | 5 giorni |
| **Esempio** | Nuovo account | Email down | Email sempre giù il lunedì | Aggiornamento firewall |

---

## Appendice C: I 34 Principi ITIL v4 — Indice Completo

**General Management (14):**
Strategy, Portfolio, Architecture, Finance, Workforce, Continual Improvement, Measurement, Risk, Information Security, Knowledge, Organizational Change, Project, Relationship, Supplier

**Service Management (17):**
Availability, Business Analysis, Capacity/Performance, Change Enablement, Incident, IT Asset, Monitoring/Event, Problem, Release, Service Catalogue, Service Configuration, Service Continuity, Service Design, Service Desk, Service Level, Service Request, Service Validation

**Technical Management (3):**
Deployment, Infrastructure/Platform, Software Development

*Tutorial approfonditi per ogni practice: vedi il piano completo in `00-SYLLABUS.md`.*

---

## Riferimenti

| Risorsa | Posizione / URL | Contenuto |
|---|---|---|
| Documento sorgente | `../01-framework-metodologie.md` | Framework completo ITIL, COBIT, ISO 20000 |
| AXELOS ITIL 4 Foundation | axelos.com | Certificazione ufficiale ITIL 4 Foundation |
| GLPI Docs | glpi-project.org/documentation | Documentazione GLPI completa |
| Docker Docs | docs.docker.com | Docker Engine e Docker Compose |
| ISO/IEC 20000-1:2018 | iso.org | Standard certificazione ITSM |
| Tutorial successivo (01b) | `tutorial_ops01_ch1b_incident_problem_change_lab.md` | Incident, Problem e Change in dettaglio |
| Tutorial prerequisito (00) | `tutorial_ops00_ch1_day_one_it_ops_lab.md` | Setup ambiente lab |

---

*Fine tutorial ops01a — Prossimo: `tutorial_ops01_ch1b_incident_problem_change_lab.md`*
