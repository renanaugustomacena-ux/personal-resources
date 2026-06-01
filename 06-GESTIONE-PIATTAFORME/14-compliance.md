---
corso: "Gestione Piattaforme e DevOps"
fase: "6 — Sicurezza e Compliance"
modulo: 14
titolo: "Compliance e Normative"
versione: "GDPR 2016/679 · NIS2 2022/2555 · DORA 2022/2554 · ISO 27001:2022"
livello: "Avanzato"
prerequisiti:
  - "13-sicurezza-piattaforme.md"
  - "07-ci-cd.md"
  - "08-monitoring-observability.md"
obiettivi:
  - "Comprendere il quadro normativo europeo (GDPR, NIS2, DORA) e i relativi obblighi tecnici"
  - "Implementare compliance-as-code con OPA, Kyverno e scan automatici nella pipeline"
  - "Progettare processi di audit continuo e gestione delle evidenze per certificazioni SOC 2 e ISO 27001"
  - "Definire procedure di incident response allineate ai termini di notifica di ciascuna normativa"
  - "Integrare data classification, data retention e diritti degli interessati nei sistemi tecnici"
tag: [gdpr, nis2, dora, soc2, iso27001, pci-dss, compliance-as-code, opa, audit]
---

# Compliance e Normative — Documentazione Completa

> **Modulo 14** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Comprendere il quadro normativo europeo (GDPR, NIS2, DORA) e i relativi obblighi tecnici
> 2. Implementare compliance-as-code con OPA, Kyverno e scan automatici nella pipeline
> 3. Progettare processi di audit continuo e gestione delle evidenze per certificazioni SOC 2 e ISO 27001
> 4. Definire procedure di incident response allineate ai termini di notifica di ciascuna normativa
> 5. Integrare data classification, data retention e diritti degli interessati nei sistemi tecnici
>
> **Prerequisiti:** [Sicurezza delle Piattaforme](13-sicurezza-piattaforme.md) · [CI/CD](07-ci-cd.md) · [Monitoring e Observability](08-monitoring-observability.md)
> **Tempo stimato:** 8-12 ore · **Livello:** Avanzato

## Idee guida

1. **Compliance e processo, non checkbox.** Aderenza continua.
2. **GDPR + NIS2 + DORA = trio EU 2024-2025.** Penalty fino a 10M€ o 2% fatturato.
3. **SOC 2, ISO 27001 = trust signal per B2B.**
4. **Compliance-as-code: policy validate via OPA, scan automatici.**


## Indice

1. [Panoramica e Concetti Fondamentali](#1-panoramica-e-concetti-fondamentali)
2. [ISO 27001 — Sistema di Gestione della Sicurezza delle Informazioni](#2-iso-27001--sistema-di-gestione-della-sicurezza-delle-informazioni)
3. [SOC 2 — Trust Services Criteria](#3-soc-2--trust-services-criteria)
4. [GDPR — Regolamento Generale sulla Protezione dei Dati](#4-gdpr--regolamento-generale-sulla-protezione-dei-dati)
5. [PCI-DSS — Payment Card Industry Data Security Standard](#5-pci-dss--payment-card-industry-data-security-standard)
6. [NIS2 Directive](#6-nis2-directive)
7. [DORA — Digital Operational Resilience Act](#7-dora--digital-operational-resilience-act)
8. [EU AI Act — Regolamento sull'Intelligenza Artificiale](#8-eu-ai-act--regolamento-sullintelligenza-artificiale)
9. [HIPAA — Health Insurance Portability and Accountability Act](#9-hipaa--health-insurance-portability-and-accountability-act)
10. [Audit e Assessment](#10-audit-e-assessment)
11. [Risk Assessment e Management](#11-risk-assessment-e-management)
12. [Compliance Automation](#12-compliance-automation)
13. [Evidence Collection e Documentation](#13-evidence-collection-e-documentation)
14. [Data Residency e Sovranita Digitale](#14-data-residency-e-sovranita-digitale)
15. [Compliance Multi-Cloud](#15-compliance-multi-cloud)
16. [Audit Logging e Immutabilita dei Log](#16-audit-logging-e-immutabilita-dei-log)
17. [Best Practices](#17-best-practices)

---

## 1. Panoramica e Concetti Fondamentali

### Definizione di Compliance IT

La compliance IT rappresenta l'insieme delle attivita, dei processi e dei controlli che un'organizzazione
implementa per garantire la conformita a leggi, regolamenti, standard di settore e politiche interne
relative alla gestione dei sistemi informativi, dei dati e dell'infrastruttura tecnologica.

Non si tratta di un obiettivo statico, ma di un processo continuo che richiede monitoraggio costante,
aggiornamento delle policy e adattamento ai cambiamenti normativi e tecnologici.

### Differenza tra Compliance e Sicurezza

Un errore comune consiste nel sovrapporre compliance e sicurezza informatica. Sebbene correlate,
rappresentano concetti distinti:

| Aspetto | Sicurezza | Compliance |
|---------|-----------|------------|
| **Obiettivo** | Proteggere asset da minacce | Dimostrare conformita a normative |
| **Approccio** | Basato sul rischio reale | Basato sui requisiti normativi |
| **Misura** | Efficacia dei controlli | Presenza e documentazione dei controlli |
| **Driver** | Threat landscape, risk appetite | Leggi, regolamenti, contratti |
| **Frequenza** | Continuo e adattivo | Periodico (audit cycle) |
| **Risultato** | Riduzione del rischio | Attestazione, certificazione |

Un sistema puo essere **compliant ma non sicuro** (soddisfa i requisiti minimi ma ha vulnerabilita
non coperte dallo standard) oppure **sicuro ma non compliant** (implementa controlli robusti ma
non li documenta secondo i requisiti normativi).

### Gerarchia Normativa

Comprendere la gerarchia delle fonti e fondamentale per stabilire le priorita:

```
Legge (Law)
  Normativa vincolante emanata da organi legislativi.
  Esempio: GDPR (Regolamento UE 2016/679), D.Lgs. 196/2003 (Codice Privacy italiano)
  Caratteristica: obbligatoria, con sanzioni legali per inadempienza.

Regolamento (Regulation)
  Atto normativo di dettaglio che implementa una legge.
  Esempio: regolamenti attuativi del Garante Privacy, regole tecniche AgID
  Caratteristica: obbligatorio nell'ambito di applicazione.

Standard
  Documento tecnico pubblicato da enti di normazione riconosciuti.
  Esempio: ISO 27001, ISO 22301, ISO 9001
  Caratteristica: volontario, ma puo diventare obbligatorio per contratto o legge.

Framework
  Raccolta strutturata di linee guida e best practice.
  Esempio: NIST CSF, COBIT, CIS Controls
  Caratteristica: volontario, flessibile nell'adozione.

Policy interna
  Documento aziendale che definisce regole interne.
  Esempio: Acceptable Use Policy, Data Classification Policy
  Caratteristica: obbligatoria per il personale dell'organizzazione.
```

### Risk-Based Approach

L'approccio basato sul rischio e il principio fondante della compliance moderna. Invece di applicare
controlli uniformi a tutti gli asset, si identificano e prioritizzano i rischi piu significativi:

1. **Identificazione degli asset** — Catalogare sistemi, dati e processi critici
2. **Valutazione delle minacce** — Determinare le minacce probabili per ciascun asset
3. **Analisi delle vulnerabilita** — Identificare i punti deboli sfruttabili
4. **Calcolo del rischio** — Rischio = Probabilita x Impatto
5. **Trattamento proporzionato** — Investire nei controlli dove il rischio e maggiore

### Compliance Lifecycle

Il ciclo di vita della compliance segue quattro fasi principali:

```
ASSESS (Valutazione)
  - Gap analysis rispetto allo standard/regolamento target
  - Inventario degli asset e dei flussi di dati
  - Identificazione dei requisiti applicabili
  - Valutazione dei controlli esistenti

IMPLEMENT (Implementazione)
  - Definizione e implementazione dei controlli mancanti
  - Redazione/aggiornamento delle policy e procedure
  - Configurazione tecnica dei sistemi
  - Formazione del personale

MONITOR (Monitoraggio)
  - Verifica continua dell'efficacia dei controlli
  - Raccolta delle evidenze di conformita
  - Gestione delle non-conformita
  - Aggiornamento in base ai cambiamenti normativi

REPORT (Reportistica)
  - Audit interni periodici
  - Report alla direzione e agli stakeholder
  - Preparazione per audit esterni
  - Documentazione per certificazioni e attestazioni
```

### Ruoli Chiave nella Compliance

| Ruolo | Responsabilita | Riporta a |
|-------|----------------|-----------|
| **DPO** (Data Protection Officer) | Supervisione conformita GDPR, consulenza, punto di contatto con l'autorita | Direttamente al top management |
| **CISO** (Chief Information Security Officer) | Strategia di sicurezza, gestione rischi, implementazione controlli | CTO / CEO |
| **Compliance Officer** | Coordinamento programma compliance, monitoraggio normativo, formazione | Legal / CEO |
| **Internal Auditor** | Verifiche indipendenti, valutazione efficacia controlli, reporting | Audit Committee / Board |
| **Risk Manager** | Identificazione e valutazione rischi, risk register, KRI | CISO / CFO |
| **Legal Counsel** | Interpretazione normativa, contratti, supporto regolamentare | CEO / Board |

### Costo della Non-Compliance

Le conseguenze della non-conformita si articolano su piu livelli:

- **Sanzioni dirette**: GDPR fino a 20M EUR o 4% del fatturato globale; PCI-DSS fino a 500.000 USD per incidente
- **Costi legali**: contenziosi, class action, procedimenti giudiziari
- **Danno reputazionale**: perdita di clienti, impatto sul brand, copertura mediatica negativa
- **Costi operativi**: remediation d'emergenza, consulenze esterne, interruzione dei servizi
- **Perdita di business**: impossibilita di operare in determinati mercati, esclusione da gare
- **Responsabilita personale**: in alcuni ordinamenti, i dirigenti possono essere personalmente responsabili

---

## 2. ISO 27001 — Sistema di Gestione della Sicurezza delle Informazioni

### Cos'e ISO 27001

ISO/IEC 27001 e lo standard internazionale che specifica i requisiti per stabilire, implementare,
mantenere e migliorare continuamente un Information Security Management System (ISMS). Pubblicato
congiuntamente da ISO e IEC, la versione corrente e ISO/IEC 27001:2022.

Lo standard adotta un approccio sistematico alla gestione della sicurezza delle informazioni,
considerando persone, processi e tecnologia, e si basa sulla valutazione e sul trattamento del rischio.

### Struttura dello Standard (Clausole 4-10)

Le clausole obbligatorie definiscono i requisiti dell'ISMS:

```
Clausola 4 — Contesto dell'Organizzazione
  4.1 Comprendere l'organizzazione e il suo contesto
      - Fattori interni: cultura, struttura, risorse, conoscenze
      - Fattori esterni: leggi, mercato, tecnologia, stakeholder
  4.2 Comprendere le esigenze e aspettative delle parti interessate
      - Clienti, fornitori, autorita, dipendenti
  4.3 Determinare lo scope dell'ISMS
      - Confini fisici, logici e organizzativi
  4.4 Sistema di gestione della sicurezza delle informazioni
      - Processi necessari e loro interazioni

Clausola 5 — Leadership
  5.1 Leadership e impegno
      - Il top management deve dimostrare commitment
  5.2 Politica per la sicurezza delle informazioni
      - Appropriata allo scopo, fornisce un framework per obiettivi
  5.3 Ruoli, responsabilita e autorita
      - Assegnazione chiara di ruoli ISMS

Clausola 6 — Pianificazione
  6.1 Azioni per affrontare rischi e opportunita
      - Risk assessment process
      - Risk treatment plan
  6.2 Obiettivi di sicurezza e pianificazione per raggiungerli
      - Misurabili, coerenti con la policy
  6.3 Pianificazione dei cambiamenti
      - Change management per l'ISMS

Clausola 7 — Supporto
  7.1 Risorse
  7.2 Competenza
  7.3 Consapevolezza
  7.4 Comunicazione
  7.5 Informazioni documentate
      - Creazione, aggiornamento, controllo

Clausola 8 — Attivita Operative
  8.1 Pianificazione e controllo operativo
  8.2 Valutazione del rischio
  8.3 Trattamento del rischio

Clausola 9 — Valutazione delle Prestazioni
  9.1 Monitoraggio, misurazione, analisi e valutazione
  9.2 Audit interno
  9.3 Riesame della direzione

Clausola 10 — Miglioramento
  10.1 Miglioramento continuo
  10.2 Non-conformita e azioni correttive
```

### Annex A — Controlli di Sicurezza (ISO 27001:2022)

La versione 2022 riorganizza i controlli in 4 temi (rispetto ai 14 domini della versione 2013):

| Tema | Numero Controlli | Esempi |
|------|-----------------|--------|
| **Organizational** (A.5) | 37 | Policy, ruoli, threat intelligence, cloud security |
| **People** (A.6) | 8 | Screening, termination, awareness, remote working |
| **Physical** (A.7) | 14 | Perimetri, accesso fisico, clean desk, cabling |
| **Technological** (A.8) | 34 | User endpoints, access rights, malware, backup, logging |

Controlli chiave frequentemente richiesti in audit:

| Controllo | ID | Descrizione |
|-----------|----|-------------|
| Information security policies | A.5.1 | Definizione e approvazione delle policy di sicurezza |
| Inventory of information assets | A.5.9 | Catalogo aggiornato di tutti gli asset informativi |
| Access control | A.5.15 | Regole per l'accesso fisico e logico |
| Identity management | A.5.16 | Gestione del ciclo di vita delle identita |
| Authentication information | A.5.17 | Gestione credenziali e segreti |
| Threat intelligence | A.5.7 | Raccolta e analisi di informazioni sulle minacce |
| ICT readiness for business continuity | A.5.30 | Preparazione IT per la continuita operativa |
| Data masking | A.8.11 | Mascheramento dati in ambienti non produttivi |
| Data leakage prevention | A.8.12 | Prevenzione della fuga di dati |
| Monitoring activities | A.8.16 | Monitoraggio di reti, sistemi e applicazioni |
| Web filtering | A.8.23 | Filtro dei contenuti web |
| Secure coding | A.8.28 | Sviluppo sicuro del software |

### Statement of Applicability (SoA)

Il SoA e un documento obbligatorio che elenca tutti i controlli dell'Annex A e per ciascuno indica:

- Se il controllo e applicabile o escluso
- Giustificazione dell'inclusione o esclusione
- Stato di implementazione (implementato, parzialmente implementato, pianificato)
- Riferimento alla documentazione del controllo

Esempio di riga del SoA:

```
| A.8.7 | Protection against malware | Applicabile | Implementato |
|       | Giustificazione: sistemi esposti a malware via email e web |
|       | Implementazione: EDR su tutti gli endpoint, email filtering |
|       | Documentazione: POL-SEC-007, PROC-MAL-001 |
```

### Risk Assessment e Risk Treatment

Il processo di risk assessment ISO 27001 prevede:

1. **Definire i criteri di rischio** — Scala di probabilita (1-5), scala di impatto (1-5), livello accettabile
2. **Identificare i rischi** — Asset, minacce, vulnerabilita per ogni asset nello scope
3. **Analizzare i rischi** — Valutare probabilita e impatto per ogni scenario
4. **Valutare i rischi** — Confrontare con i criteri di accettazione
5. **Trattare i rischi** — Selezionare i controlli dall'Annex A o da altre fonti

Il Risk Treatment Plan documenta:

- Rischio identificato e il suo livello
- Controllo/i selezionato/i per il trattamento
- Responsabile dell'implementazione
- Tempistica prevista
- Rischio residuo atteso

### Processo di Certificazione

```
Fase 1: Preparazione (6-12 mesi)
  - Gap analysis iniziale
  - Definizione scope ISMS
  - Risk assessment
  - Implementazione controlli
  - Redazione documentazione

Fase 2: Stage 1 Audit (Document Review)
  - L'ente di certificazione verifica la documentazione
  - Valuta la readiness per lo Stage 2
  - Identifica aree di preoccupazione

Fase 3: Stage 2 Audit (Certification Audit)
  - Verifica on-site dell'implementazione
  - Interviste al personale
  - Verifica delle evidenze
  - Emissione del certificato (validita 3 anni)

Fase 4: Surveillance Audit (annuali)
  - Verifica del mantenimento dell'ISMS
  - Campionamento dei controlli

Fase 5: Re-certification Audit (ogni 3 anni)
  - Audit completo per il rinnovo
```

### Ciclo PDCA per il Miglioramento Continuo

```
PLAN (Pianificare)
  - Stabilire obiettivi ISMS
  - Definire policy e risk assessment
  - Pianificare controlli e risorse

DO (Fare)
  - Implementare i controlli pianificati
  - Eseguire il risk treatment plan
  - Formare il personale

CHECK (Verificare)
  - Monitorare le prestazioni
  - Condurre audit interni
  - Misurare l'efficacia dei controlli

ACT (Agire)
  - Azioni correttive per le non-conformita
  - Implementare miglioramenti
  - Aggiornare il risk assessment
```

---

## 3. SOC 2 — Trust Services Criteria

### Cos'e SOC 2

SOC 2 (System and Organization Controls 2) e un framework di audit sviluppato dall'AICPA
(American Institute of Certified Public Accountants) che valuta i controlli di un'organizzazione
relativi alla sicurezza, disponibilita, integrita del processamento, riservatezza e privacy dei
dati gestiti per conto dei clienti.

E particolarmente rilevante per i service provider (SaaS, cloud, data center, managed services)
che devono dimostrare ai propri clienti l'affidabilita dei propri controlli.

### Differenze tra SOC 1, SOC 2 e SOC 3

| Caratteristica | SOC 1 | SOC 2 | SOC 3 |
|---------------|-------|-------|-------|
| **Focus** | Controlli finanziari (ICFR) | Controlli operativi e di sicurezza | Come SOC 2 (sintesi) |
| **Standard** | SSAE 18 / ISAE 3402 | SSAE 18 (AT-C 205) | SSAE 18 (AT-C 205) |
| **Destinatari** | Auditor, CFO | CISO, clienti enterprise | Pubblico generale |
| **Distribuzione** | Ristretta (NDA) | Ristretta (NDA) | Pubblica (sito web) |
| **Dettaglio** | Controlli specifici ICFR | Controlli dettagliati + test | Opinione sintetica |
| **Uso tipico** | Outsourcing payroll, ERP | Cloud, SaaS, hosting | Marketing, trust |

### Type I vs Type II

| Aspetto | Type I | Type II |
|---------|--------|---------|
| **Cosa valuta** | Design dei controlli a una data specifica | Design e operating effectiveness nel tempo |
| **Periodo** | Point-in-time (un giorno) | Periodo di osservazione (6-12 mesi) |
| **Valore** | Minore (snapshot) | Maggiore (evidenza di funzionamento continuo) |
| **Costo** | Inferiore | Superiore |
| **Uso** | Prima certificazione, clienti meno esigenti | Standard per clienti enterprise |

### I 5 Trust Services Criteria (TSC)

#### Security (Common Criteria — CC)

Il criterio Security e obbligatorio in ogni audit SOC 2. Copre la protezione contro accessi
non autorizzati (fisici e logici):

| Categoria | Criteri | Controlli tipici |
|-----------|---------|-----------------|
| CC1 — Control Environment | CC1.1 - CC1.5 | Governance, etica, struttura organizzativa |
| CC2 — Communication & Information | CC2.1 - CC2.3 | Policy, comunicazione interna/esterna |
| CC3 — Risk Assessment | CC3.1 - CC3.4 | Identificazione rischi, fraud risk |
| CC4 — Monitoring Activities | CC4.1 - CC4.2 | Monitoraggio controlli, remediation |
| CC5 — Control Activities | CC5.1 - CC5.3 | Selezione e deployment controlli |
| CC6 — Logical and Physical Access | CC6.1 - CC6.8 | IAM, MFA, encryption, asset fisici |
| CC7 — System Operations | CC7.1 - CC7.5 | Change management, incident response |
| CC8 — Change Management | CC8.1 | Change management formale |
| CC9 — Risk Mitigation | CC9.1 - CC9.2 | Vendor management, risk mitigation |

#### Availability

Copre l'accessibilita del sistema secondo gli SLA concordati:

- Capacity planning e performance monitoring
- Disaster recovery e business continuity
- Backup e restore testing
- Incident management per outage
- SLA tracking e reporting

#### Processing Integrity

Garantisce che l'elaborazione dei dati sia completa, accurata, tempestiva e autorizzata:

- Input validation e data quality checks
- Processing monitoring e error handling
- Output reconciliation
- Data integrity controls
- Audit trail delle transazioni

#### Confidentiality

Protezione delle informazioni classificate come confidenziali:

- Data classification scheme
- Encryption at rest e in transit
- Access controls basati sulla classificazione
- Secure disposal dei dati
- NDA e accordi di riservatezza

#### Privacy

Gestione dei dati personali secondo i principi privacy (spesso allineati a GDPR):

- Notice e consent
- Data collection limitation
- Use and retention policies
- Access e disclosure controls
- Data quality e individual rights

### Processo di Audit SOC 2

```
1. Scoping (2-4 settimane)
   - Definire i sistemi in scope
   - Selezionare i TSC applicabili
   - Identificare i confini del sistema

2. Readiness Assessment (4-8 settimane)
   - Gap analysis rispetto ai TSC selezionati
   - Remediation dei gap identificati
   - Preparazione della documentazione

3. Observation Period (Type II: 6-12 mesi)
   - Operare i controlli documentati
   - Raccogliere evidenze continuamente
   - Gestire incidenti e change

4. Fieldwork (4-6 settimane)
   - L'auditor testa i controlli
   - Richiede evidenze (inquiry, observation, inspection, re-performance)
   - Documenta le eccezioni

5. Report (2-4 settimane)
   - L'auditor emette il report con opinione
   - Sezioni: management assertion, system description, controls, test results
   - Opinione: unqualified (pulita), qualified (con eccezioni), adverse (negativa)
```

### Bridge Letters

Quando il periodo del report SOC 2 Type II non copre l'intero anno (gap period), il service provider
emette una bridge letter che attesta:

- I controlli non hanno subito modifiche significative
- Non si sono verificati incidenti rilevanti
- Il sistema continua a operare come descritto nel report

La bridge letter non e un sostituto dell'audit, ma colma il gap temporale fino al report successivo.

### SOC 2+

SOC 2+ consente di includere criteri aggiuntivi nell'audit:

- **SOC 2 + HITRUST CSF**: Per organizzazioni healthcare
- **SOC 2 + CSA STAR**: Per cloud service provider
- **SOC 2 + ISO 27001 mapping**: Per organizzazioni con requisiti internazionali
- **SOC 2 + NIST CSF**: Per organizzazioni USA con requisiti governativi

---

## 4. GDPR — Regolamento Generale sulla Protezione dei Dati

### Principi Fondamentali (Articolo 5)

Il Regolamento UE 2016/679 stabilisce sette principi fondamentali per il trattamento dei dati personali:

| Principio | Articolo | Descrizione | Esempio Pratico |
|-----------|----------|-------------|-----------------|
| **Liceita, correttezza, trasparenza** | 5(1)(a) | Trattamento lecito, corretto e trasparente per l'interessato | Informativa privacy chiara e accessibile |
| **Limitazione della finalita** | 5(1)(b) | Dati raccolti per finalita determinate, esplicite e legittime | Non usare email raccolte per un servizio per marketing |
| **Minimizzazione dei dati** | 5(1)(c) | Dati adeguati, pertinenti e limitati al necessario | Non richiedere la data di nascita per una newsletter |
| **Esattezza** | 5(1)(d) | Dati esatti e aggiornati, con rettifica tempestiva | Meccanismo per gli utenti per aggiornare i propri dati |
| **Limitazione della conservazione** | 5(1)(e) | Conservazione per il tempo necessario alla finalita | Data retention policy con cancellazione automatica |
| **Integrita e riservatezza** | 5(1)(f) | Misure tecniche e organizzative adeguate | Encryption, access control, pseudonimizzazione |
| **Accountability** | 5(2) | Il titolare deve dimostrare la conformita | Documentazione, DPIA, registro trattamenti |

### Basi Giuridiche del Trattamento (Articolo 6)

Ogni trattamento deve basarsi su almeno una delle seguenti basi giuridiche:

```
1. Consenso (art. 6.1.a)
   - Deve essere libero, specifico, informato e inequivocabile
   - Deve poter essere revocato con la stessa facilita con cui e stato prestato
   - Per i minori: consenso del genitore/tutore sotto i 16 anni (14 in Italia)
   - Onere della prova: il titolare deve dimostrare che il consenso e stato ottenuto

2. Esecuzione di un contratto (art. 6.1.b)
   - Trattamento necessario per eseguire un contratto con l'interessato
   - Esempio: elaborare un ordine e-commerce richiede nome e indirizzo

3. Obbligo legale (art. 6.1.c)
   - Il titolare e obbligato per legge
   - Esempio: conservazione delle fatture per obblighi fiscali

4. Interessi vitali (art. 6.1.d)
   - Protezione di un interesse essenziale per la vita dell'interessato
   - Esempio: accesso ai dati medici in emergenza

5. Interesse pubblico (art. 6.1.e)
   - Esecuzione di un compito di interesse pubblico o pubblici poteri
   - Esempio: trattamento da parte di enti pubblici

6. Legittimo interesse (art. 6.1.f)
   - Bilanciamento tra interesse del titolare e diritti dell'interessato
   - Richiede un Legitimate Interest Assessment (LIA)
   - Non applicabile alle autorita pubbliche
```

### Diritti dell'Interessato

| Diritto | Articolo | Termine | Dettaglio |
|---------|----------|---------|-----------|
| **Accesso** | Art. 15 | 1 mese | Copia dei dati, finalita, destinatari, periodo di conservazione |
| **Rettifica** | Art. 16 | 1 mese | Correzione dei dati inesatti o incompleti |
| **Cancellazione** (diritto all'oblio) | Art. 17 | 1 mese | Cancellazione quando non piu necessari, revoca consenso |
| **Limitazione** | Art. 18 | 1 mese | Sospensione del trattamento in casi specifici |
| **Portabilita** | Art. 20 | 1 mese | Dati in formato strutturato, leggibile da macchina |
| **Opposizione** | Art. 21 | Senza ritardo | Opposizione al trattamento basato su legittimo interesse |
| **Decisione automatizzata** | Art. 22 | 1 mese | Diritto a non essere soggetto a decisioni puramente automatizzate |

Il termine di 1 mese puo essere prorogato di 2 mesi in caso di richieste complesse o numerose,
con comunicazione all'interessato entro il primo mese.

### DPIA — Data Protection Impact Assessment

La DPIA e obbligatoria quando il trattamento presenta un rischio elevato per i diritti e le liberta
delle persone fisiche. Casi obbligatori:

- Profilazione sistematica con effetti significativi
- Trattamento su larga scala di dati particolari (ex sensibili)
- Sorveglianza sistematica di zona accessibile al pubblico
- Nuove tecnologie con rischio elevato
- Trattamenti inclusi nell'elenco del Garante nazionale

Contenuto minimo della DPIA:

```
1. Descrizione del trattamento
   - Natura, ambito, contesto e finalita
   - Dati trattati e interessati coinvolti
   - Flusso dei dati e sistemi coinvolti

2. Necessita e proporzionalita
   - Valutazione della necessita rispetto alla finalita
   - Base giuridica applicabile
   - Misure di minimizzazione adottate

3. Valutazione dei rischi
   - Rischi per i diritti e le liberta degli interessati
   - Probabilita e gravita di ciascun rischio
   - Fonti di rischio (accesso non autorizzato, perdita, alterazione)

4. Misure di mitigazione
   - Misure tecniche (encryption, pseudonimizzazione, access control)
   - Misure organizzative (policy, formazione, audit)
   - Rischio residuo dopo le misure

5. Parere del DPO
   - Valutazione indipendente del DPO
   - Raccomandazioni eventuali
```

### Registro dei Trattamenti (Articolo 30)

Obbligatorio per organizzazioni con piu di 250 dipendenti, o in ogni caso se il trattamento
presenta rischi, non e occasionale, o include dati particolari. Il registro deve contenere:

| Campo | Titolare (art. 30.1) | Responsabile (art. 30.2) |
|-------|---------------------|-------------------------|
| Nome e contatti | Si | Si |
| Finalita del trattamento | Si | No |
| Categorie di interessati | Si | No |
| Categorie di dati | Si | Si |
| Categorie di destinatari | Si | No |
| Trasferimenti extra-UE | Si | Si |
| Termini di cancellazione | Si | No |
| Misure di sicurezza | Si | Si |
| Categorie di trattamenti | No | Si |

### Data Breach Notification

In caso di violazione dei dati personali:

```
Notifica all'autorita di controllo (art. 33):
  - Entro 72 ore dalla scoperta della violazione
  - Contenuto: natura della violazione, categorie e numero di interessati,
    dati di contatto del DPO, conseguenze probabili, misure adottate
  - Non necessaria se improbabile che comporti rischi per gli interessati

Comunicazione agli interessati (art. 34):
  - Quando la violazione comporta un rischio elevato
  - In linguaggio semplice e chiaro
  - Non necessaria se:
    - I dati erano cifrati o resi incomprensibili
    - Misure successive hanno scongiurato il rischio
    - Richiederebbe sforzi sproporzionati (comunicazione pubblica)
```

### Sanzioni GDPR

| Livello | Importo Massimo | Violazioni |
|---------|-----------------|------------|
| **Inferiore** | 10M EUR o 2% del fatturato globale | Obblighi del titolare/responsabile, organismo di certificazione |
| **Superiore** | 20M EUR o 4% del fatturato globale | Principi fondamentali, diritti degli interessati, trasferimenti |

---

## 5. PCI-DSS — Payment Card Industry Data Security Standard

### I 12 Requisiti nei 6 Obiettivi

PCI DSS definisce 12 requisiti organizzati in 6 obiettivi di sicurezza:

| Obiettivo | Requisito | Descrizione |
|-----------|-----------|-------------|
| **Build and Maintain a Secure Network** | 1 | Install and maintain network security controls |
| | 2 | Apply secure configurations to all system components |
| **Protect Account Data** | 3 | Protect stored account data |
| | 4 | Protect cardholder data with strong cryptography during transmission |
| **Maintain a Vulnerability Management Program** | 5 | Protect all systems and networks from malicious software |
| | 6 | Develop and maintain secure systems and software |
| **Implement Strong Access Control Measures** | 7 | Restrict access to system components by business need to know |
| | 8 | Identify users and authenticate access to system components |
| | 9 | Restrict physical access to cardholder data |
| **Regularly Monitor and Test Networks** | 10 | Log and monitor all access to system components and cardholder data |
| | 11 | Test security of systems and networks regularly |
| **Maintain an Information Security Policy** | 12 | Support information security with organizational policies and programs |

### SAQ vs ROC

| Aspetto | SAQ (Self-Assessment Questionnaire) | ROC (Report on Compliance) |
|---------|-------------------------------------|---------------------------|
| **Chi lo compila** | Il merchant stesso | QSA (Qualified Security Assessor) |
| **Validita** | Merchant livello 2-4 | Merchant livello 1, service provider |
| **Complessita** | Variabile (SAQ A: 22 domande, SAQ D: 329 domande) | Audit completo on-site |
| **Costo** | Basso-medio | Alto (decine di migliaia di EUR) |

Tipi di SAQ:

| SAQ | Applicabilita | Numero domande |
|-----|--------------|----------------|
| **A** | E-commerce con pagamento completamente outsourced (redirect/iframe) | ~22 |
| **A-EP** | E-commerce con elementi della pagina di pagamento sulla propria infrastruttura | ~191 |
| **B** | Solo terminali dial-up o imprint, no storage elettronico | ~41 |
| **B-IP** | Terminali PTS su rete IP isolata | ~82 |
| **C** | Payment application su sistema connesso a Internet | ~160 |
| **C-VT** | Virtual terminal su computer isolato | ~79 |
| **P2PE** | Terminali con Point-to-Point Encryption validata | ~33 |
| **D** | Tutti gli altri merchant e service provider | ~329 |

### Livelli Merchant

| Livello | Volume Transazioni (annuo) | Requisiti |
|---------|---------------------------|-----------|
| **1** | > 6 milioni | ROC da QSA, ASV scan trimestrale |
| **2** | 1-6 milioni | SAQ, ASV scan trimestrale |
| **3** | 20.000 - 1 milione (e-commerce) | SAQ, ASV scan trimestrale |
| **4** | < 20.000 (e-commerce) o < 1 milione (altri) | SAQ (raccomandato), ASV scan |

### Scope e Segmentazione della Rete

Lo scope PCI DSS comprende tutti i componenti del sistema che memorizzano, processano o
trasmettono dati dei titolari di carta (CHD) o dati sensibili di autenticazione (SAD), e tutti
i componenti connessi a tali sistemi.

La segmentazione della rete riduce lo scope dell'audit:

```
Rete Aziendale (fuori scope)
  |
  +-- Firewall / Network Security Controls
  |
  +-- CDE (Cardholder Data Environment) - IN SCOPE
  |     |
  |     +-- Server di pagamento
  |     +-- Database con PAN
  |     +-- Terminali POS
  |
  +-- Connected-to Systems - IN SCOPE
  |     |
  |     +-- Active Directory
  |     +-- Log server
  |     +-- Jump server
  |
  +-- Out-of-scope Systems
        |
        +-- Workstation HR
        +-- Server email
```

### Tokenizzazione e Encryption

**Tokenizzazione**: sostituisce il PAN (Primary Account Number) con un token non reversibile.
Il token non ha valore al di fuori del sistema che lo ha generato. Il token vault che mantiene
la mappatura token-PAN resta in scope PCI DSS.

**Encryption**: protegge i dati del titolare di carta con algoritmi crittografici:

- **At rest**: AES-256 per database e file system
- **In transit**: TLS 1.2+ per tutte le trasmissioni su reti pubbliche
- **Key management**: procedura documentata per generazione, distribuzione, rotazione, distruzione delle chiavi

### PCI DSS v4.0 — Principali Novita

La versione 4.0 (pubblicata marzo 2022, obbligatoria da marzo 2025) introduce:

1. **Customized Approach**: alternativa all'approccio definito, consente controlli personalizzati
   purche raggiungano l'obiettivo di sicurezza dichiarato
2. **Targeted Risk Analysis**: risk analysis specifiche per frequenza di alcune attivita
3. **Enhanced authentication**: MFA per tutti gli accessi al CDE, non solo amministrativi
4. **E-commerce security**: protezione degli script sulle pagine di pagamento (Requirement 6.4.3)
5. **Continuous security**: enfasi su security come processo continuo, non one-time compliance
6. **Expanded scope**: requisiti piu dettagliati per cloud, container, serverless

### ASV Scanning e Penetration Testing

```
ASV (Approved Scanning Vendor) Scan:
  - Scansione trimestrale delle vulnerabilita esterne
  - Eseguita da vendor approvati dal PCI SSC
  - Deve risultare "pass" (nessuna vulnerabilita con CVSS >= 4.0)
  - Obbligatoria per tutti i livelli

Penetration Testing:
  - Annuale (o dopo modifiche significative)
  - Deve coprire network layer e application layer
  - Include test della segmentazione
  - Metodologia documentata (PTES, OWASP Testing Guide)
  - Validazione della remediation dei finding
```

---

## 6. NIS2 Directive

### Cos'e la NIS2

La Direttiva (UE) 2022/2555 (NIS2) sostituisce la Direttiva NIS originale (2016/1148) e rappresenta
il quadro normativo europeo per la sicurezza delle reti e dei sistemi informativi. In Italia e stata
recepita con il D.Lgs. 138/2024 e l'Agenzia per la Cybersicurezza Nazionale (ACN) e l'autorita
competente per la sua applicazione.

### Ambito di Applicazione

La NIS2 classifica le organizzazioni in due categorie:

| Categoria | Settori | Dimensione Minima | Supervisione |
|-----------|---------|-------------------|--------------|
| **Soggetti Essenziali** | Energia, trasporti, banche, infrastrutture mercati finanziari, sanita, acqua potabile, acque reflue, infrastruttura digitale, gestione servizi ICT B2B, PA, spazio | Media impresa+ (>50 dip. o >10M EUR fatturato) | Proattiva (audit, ispezioni) |
| **Soggetti Importanti** | Servizi postali, gestione rifiuti, produzione chimica, produzione alimentare, dispositivi medici, prodotti elettronici, macchinari, veicoli, ricerca, provider digitali | Media impresa+ | Reattiva (post-incidente) |

Indipendentemente dalla dimensione, sono sempre in scope:

- Provider di reti pubbliche di comunicazione elettronica
- Prestatori di servizi fiduciari qualificati
- Registri di nomi di dominio TLD e provider DNS
- Soggetti identificati come critici dalla PA

### Obblighi di Sicurezza (Articolo 21)

Le organizzazioni devono adottare misure tecniche, operative e organizzative adeguate e proporzionate:

```
1. Policy di analisi dei rischi e sicurezza dei sistemi informativi
2. Gestione degli incidenti (prevenzione, rilevamento, risposta)
3. Continuita operativa e gestione delle crisi
   - Gestione dei backup
   - Disaster recovery
   - Gestione delle crisi
4. Sicurezza della catena di approvvigionamento (supply chain)
   - Valutazione dei fornitori
   - Requisiti di sicurezza contrattuali
5. Sicurezza nell'acquisizione, sviluppo e manutenzione dei sistemi
   - Gestione delle vulnerabilita
   - Disclosure coordinata
6. Policy e procedure per valutare l'efficacia delle misure
7. Pratiche di igiene informatica di base e formazione
8. Policy sull'uso della crittografia e della cifratura
9. Sicurezza delle risorse umane
   - Access control
   - Gestione degli asset
10. Autenticazione multi-fattore o autenticazione continua
    - Comunicazioni vocali, video e testuali protette
    - Sistemi di comunicazione di emergenza protetti
```

### Incident Reporting

La NIS2 introduce obblighi di segnalazione stringenti con tempistiche precise:

| Fase | Termine | Contenuto |
|------|---------|-----------|
| **Early warning** | 24 ore dalla scoperta | Notifica preliminare: se l'incidente e sospettato illecito, se potrebbe avere impatto transfrontaliero |
| **Incident notification** | 72 ore dalla scoperta | Aggiornamento con valutazione iniziale: gravita, impatto, indicatori di compromissione |
| **Final report** | 1 mese dalla notifica | Report dettagliato: descrizione dell'incidente, gravita e impatto, tipo di minaccia/causa, misure di mitigazione, impatto transfrontaliero |

In Italia la segnalazione va inoltrata al CSIRT Italia (gestito dall'ACN).

### Supply Chain Security

La NIS2 pone enfasi significativa sulla sicurezza della supply chain:

- Valutazione dei rischi derivanti dai fornitori diretti e dai service provider
- Valutazione della qualita e delle pratiche di sicurezza dei fornitori
- Inclusione di clausole di sicurezza nei contratti con i fornitori
- Considerazione dei risultati delle valutazioni coordinate dei rischi (EU level)
- Monitoraggio continuo della sicurezza della supply chain

### Governance Requirements

- L'organo di gestione (board/CdA) deve approvare le misure di sicurezza
- L'organo di gestione deve supervisionare l'implementazione
- I membri dell'organo di gestione devono seguire formazione sulla cybersecurity
- Responsabilita personale dei dirigenti per la mancata conformita

### Sanzioni

| Categoria | Sanzione Massima |
|-----------|-----------------|
| **Soggetti Essenziali** | Almeno 10M EUR o 2% del fatturato mondiale annuo (il maggiore) |
| **Soggetti Importanti** | Almeno 7M EUR o 1,4% del fatturato mondiale annuo (il maggiore) |

Inoltre, le autorita possono:

- Emettere avvertimenti e istruzioni vincolanti
- Ordinare di cessare comportamenti non conformi
- Ordinare audit di sicurezza a spese del soggetto
- Sospendere temporaneamente certificazioni o autorizzazioni
- Imporre un divieto temporaneo all'esercizio di funzioni dirigenziali

### Differenze con NIS1

| Aspetto | NIS1 (2016) | NIS2 (2022) |
|---------|-------------|-------------|
| **Scope** | Operatori servizi essenziali + provider digitali | Classificazione estesa (essenziali + importanti) |
| **Settori** | 7 settori | 18+ settori |
| **Dimensione** | Identificazione nazionale | Criteri di dimensione uniformi EU |
| **Reporting** | Non armonizzato | 24h/72h/1mese standardizzato |
| **Supply chain** | Limitato | Obbligo esplicito |
| **Governance** | Non specificato | Responsabilita del board |
| **Sanzioni** | A discrezione nazionale | Minimo armonizzato EU |
| **Enforcement** | Variabile | Proattivo (essenziali) + reattivo (importanti) |

### Applicazione in Italia — ACN

L'Agenzia per la Cybersicurezza Nazionale (ACN) e l'autorita competente per NIS2 in Italia:

- Gestisce il CSIRT Italia per la segnalazione degli incidenti
- Definisce le linee guida tecniche per le misure di sicurezza
- Conduce attivita di vigilanza e ispezione
- Irroga sanzioni amministrative
- Coordina la risposta nazionale agli incidenti cyber
- Mantiene il registro dei soggetti NIS2

---

## 7. DORA — Digital Operational Resilience Act

### Cos'e il DORA

Il Regolamento (UE) 2022/2554 — Digital Operational Resilience Act (DORA) — stabilisce requisiti uniformi
per la gestione del rischio ICT nel settore finanziario europeo. Entrato in applicazione il 17 gennaio 2025,
il DORA garantisce che banche, imprese di assicurazione, societa di investimento, istituti di pagamento e
altre entita finanziarie possano resistere, rispondere e riprendersi da interruzioni e minacce ICT,
inclusi attacchi informatici e guasti di sistema.

A differenza della NIS2 (che e una direttiva e richiede trasposizione nazionale), il DORA e un regolamento
direttamente applicabile in tutti gli Stati membri dell'UE senza necessita di recepimento.

### Ambito di Applicazione

Il DORA si applica a un ampio spettro di entita finanziarie:

| Categoria | Entita Incluse |
|-----------|----------------|
| **Settore bancario** | Enti creditizi, istituti di pagamento, istituti di moneta elettronica |
| **Mercati finanziari** | Imprese di investimento, sedi di negoziazione, trade repositories, controparti centrali |
| **Assicurazioni** | Imprese di assicurazione e riassicurazione, intermediari assicurativi |
| **Pensioni** | Enti pensionistici aziendali o professionali |
| **Cripto-asset** | Fornitori di servizi di cripto-asset (ai sensi di MiCA) |
| **Infrastruttura** | Fornitori di servizi di crowdfunding, agenzie di rating del credito |
| **Fornitori ICT critici** | Cloud provider, data center, provider di servizi gestiti designati come critici |

Le microimprese (meno di 10 dipendenti e fatturato/attivo inferiore a 2 milioni EUR) beneficiano di un
regime semplificato con requisiti proporzionati.

### I 5 Pilastri del DORA

Il regolamento si articola in cinque pilastri fondamentali:

```
Pilastro 1 — Gestione del Rischio ICT (Articoli 5-16)
  - Framework di gestione del rischio ICT documentato e aggiornato annualmente
  - Governance a livello di consiglio di amministrazione con responsabilita diretta
  - Identificazione, protezione, rilevamento, risposta e ripristino
  - Politiche di sicurezza ICT per tutti gli asset informativi
  - Gestione delle vulnerabilita e delle patch
  - Cifratura e controllo degli accessi
  - Gestione dei cambiamenti ICT
  - Logging e monitoraggio delle anomalie

Pilastro 2 — Gestione e Segnalazione degli Incidenti ICT (Articoli 17-23)
  - Classificazione degli incidenti secondo criteri definiti
  - Segnalazione degli incidenti maggiori entro 4 ore dalla classificazione
  - Notifica intermedia entro 72 ore
  - Report finale entro 1 mese
  - Registro di tutti gli incidenti ICT (anche non significativi)
  - Analisi post-incidente e lessons learned

Pilastro 3 — Test di Resilienza Operativa Digitale (Articoli 24-27)
  - Programma di test proporzionato alla dimensione e al profilo di rischio
  - Test di base: vulnerability assessment, scansioni, revisione del codice
  - Test avanzato (TLPT): Threat-Led Penetration Testing almeno ogni 3 anni
  - Il TLPT segue il framework TIBER-EU
  - Entita significative devono includere fornitori ICT critici nel TLPT
  - I risultati devono essere condivisi con le autorita competenti

Pilastro 4 — Gestione del Rischio ICT di Terze Parti (Articoli 28-44)
  - Strategia documentata per la gestione dei fornitori ICT
  - Due diligence pre-contrattuale obbligatoria
  - Clausole contrattuali minime obbligatorie per i contratti ICT
  - Registro delle informazioni su tutti gli accordi ICT con terze parti
  - Monitoraggio continuo delle prestazioni e dei rischi dei fornitori
  - Piani di uscita e strategie di transizione documentati
  - Designazione di fornitori ICT critici a livello europeo (CTPPs)

Pilastro 5 — Condivisione delle Informazioni (Articolo 45)
  - Possibilita di scambiare informazioni sulle minacce informatiche
  - Partecipazione volontaria a meccanismi di condivisione
  - Notifica alle autorita competenti della partecipazione
  - Protezione dei dati personali nelle informazioni condivise
```

### Registro delle Informazioni (Register of Information)

Una delle novita piu operative del DORA e l'obbligo di mantenere un registro aggiornato
di tutti gli accordi contrattuali con fornitori ICT di terze parti:

```
Contenuto obbligatorio del Registro:

Identificazione del fornitore:
  - Denominazione, sede legale, identificativo LEI
  - Tipo di fornitore (cloud, software, infrastruttura, etc.)
  - Se designato come CTPP (Critical Third-Party Provider)

Dettagli contrattuali:
  - Data di inizio e termine del contratto
  - Tipo di servizio ICT fornito
  - Funzione aziendale supportata
  - Se il servizio supporta funzioni critiche o importanti

Valutazione del rischio:
  - Livello di criticita del servizio
  - Sostituibilita del fornitore
  - Impatto di un'interruzione del servizio
  - Dipendenze da sub-fornitori (catena di subappalto)

Localizzazione dei dati:
  - Dove vengono elaborati i dati
  - Dove vengono conservati i dati
  - Paesi e regioni coinvolti

Timeline di sottomissione (2026):
  - Finestra di invio: 16 febbraio 2026 — 13 marzo 2026
  - Le autorita competenti trasmettono i registri alle ESA entro il 31 marzo 2026
```

### Clausole Contrattuali Minime (Articolo 30)

Il DORA impone clausole contrattuali specifiche per tutti i contratti con fornitori ICT:

| Clausola | Descrizione | Applicabilita |
|----------|-------------|---------------|
| **Descrizione del servizio** | Descrizione chiara e completa del servizio ICT | Tutti i contratti |
| **Localizzazione dati** | Specifiche su dove i dati saranno elaborati e conservati | Tutti i contratti |
| **Disponibilita e qualita** | SLA per disponibilita, autenticita, integrita, riservatezza | Tutti i contratti |
| **Notifica incidenti** | Obbligo del fornitore di notificare gli incidenti ICT | Tutti i contratti |
| **Diritto di audit** | Diritto dell'entita finanziaria di condurre audit e ispezioni | Tutti i contratti |
| **Cooperazione con autorita** | Obbligo di cooperazione con le autorita competenti | Tutti i contratti |
| **Strategia di uscita** | Piano di uscita e periodo di transizione adeguato | Funzioni critiche |
| **Sub-outsourcing** | Condizioni per il subappalto dei servizi ICT | Funzioni critiche |
| **Partecipazione al TLPT** | Obbligo di partecipare ai test di penetrazione | CTPP |

### CTPP — Fornitori ICT Critici

Il 18 novembre 2025, EBA, EIOPA ed ESMA hanno pubblicato il primo elenco ufficiale di 19 fornitori
ICT critici designati ai sensi del DORA. L'elenco include:

- **Cloud hyperscaler**: AWS, Microsoft Azure, Google Cloud
- **Dati finanziari e tecnologia**: Bloomberg, London Stock Exchange Group, IBM
- **Servizi IT e telecomunicazioni**: Tata Consultancy Services, Orange

I CTPP designati sono soggetti a supervisione diretta da parte delle ESA (Lead Overseer) con poteri di:

- Ispezioni e audit on-site e off-site
- Richieste di informazioni e documentazione
- Raccomandazioni vincolanti
- Sanzioni fino a l'1% del fatturato medio giornaliero mondiale

### Sanzioni DORA

Le sanzioni per la non-conformita al DORA sono definite dalle autorita competenti nazionali,
ma il regolamento stabilisce che devono essere:

- Effettive, proporzionate e dissuasive
- Applicabili sia alle entita finanziarie sia ai loro dirigenti responsabili
- Possono includere la sospensione o la revoca delle autorizzazioni
- Per i CTPP: fino a l'1% del fatturato medio giornaliero mondiale per ogni giorno di inadempienza

### DORA e Complementarieta con NIS2

Il DORA e considerato *lex specialis* rispetto alla NIS2 per il settore finanziario:

| Aspetto | NIS2 | DORA |
|---------|------|------|
| **Tipo** | Direttiva (richiede trasposizione) | Regolamento (direttamente applicabile) |
| **Settore** | Multi-settoriale (18+ settori) | Settore finanziario |
| **Incident reporting** | 24h/72h/1 mese | 4h/72h/1 mese |
| **Test di resilienza** | Non specificato | TLPT obbligatorio (ogni 3 anni) |
| **Fornitori** | Supply chain security generico | Registro dettagliato + CTPP |
| **Prevalenza** | Si applica dove il DORA non si applica | Prevale su NIS2 per il settore finanziario |

---

## 8. EU AI Act — Regolamento sull'Intelligenza Artificiale

### Cos'e l'EU AI Act

Il Regolamento (UE) 2024/1689 (EU AI Act) e il primo quadro normativo completo al mondo
sull'intelligenza artificiale. Pubblicato nella Gazzetta Ufficiale dell'UE il 12 luglio 2024, stabilisce
regole armonizzate per lo sviluppo, l'immissione sul mercato, la messa in servizio e l'uso
dei sistemi di intelligenza artificiale nell'Unione Europea.

L'EU AI Act adotta un approccio basato sul rischio: piu e alto il rischio che un sistema di IA
rappresenta per la sicurezza, i diritti fondamentali e i valori dell'UE, piu rigorosi sono gli obblighi
a cui e soggetto.

### Classificazione del Rischio

L'AI Act classifica i sistemi di IA in quattro livelli di rischio:

```
Rischio Inaccettabile (Pratiche Proibite — Articolo 5)
  Sistemi di IA vietati a partire dal 2 febbraio 2025:
  - Manipolazione subliminale o ingannevole che causa danni
  - Sfruttamento di vulnerabilita legate a eta, disabilita, situazione sociale
  - Social scoring da parte delle autorita pubbliche
  - Profilazione predittiva per la valutazione del rischio di reato individuale
  - Scraping non mirato di immagini facciali da Internet o CCTV
  - Riconoscimento delle emozioni sul posto di lavoro e nelle istituzioni educative
  - Categorizzazione biometrica per inferire dati sensibili (razza, opinioni politiche, etc.)
  - Identificazione biometrica remota in tempo reale in spazi pubblici (con eccezioni)

Rischio Elevato (High-Risk — Articolo 6 e Allegato III)
  Sistemi soggetti a requisiti stringenti (in vigore dal 2 agosto 2026 per Allegato III,
  posticipato al 2 dicembre 2027 dopo il Digital Omnibus del 7 maggio 2026):
  - Identificazione e categorizzazione biometrica
  - Gestione di infrastrutture critiche (energia, trasporti, acqua)
  - Istruzione e formazione professionale (ammissione, valutazione)
  - Occupazione e gestione del personale (recruitment, valutazione prestazioni)
  - Accesso a servizi essenziali (credito, assicurazione, welfare)
  - Applicazione della legge (valutazione del rischio, poligrafo)
  - Migrazione e controllo delle frontiere
  - Amministrazione della giustizia e processi democratici

Rischio Limitato (Articolo 50 — Trasparenza)
  Obblighi di trasparenza per:
  - Chatbot: gli utenti devono sapere di interagire con un'IA
  - Deepfake: contenuto audio/video generato deve essere etichettato
  - Testo generato da IA pubblicato per informare: deve essere marcato come generato artificialmente
  Applicazione: dal 2 dicembre 2026 (posticipato dal Digital Omnibus)

Rischio Minimo
  Nessun obbligo specifico. Esempio: filtri spam, raccomandazioni di contenuti, videogiochi.
  Incoraggiata l'adozione volontaria di codici di condotta.
```

### Obblighi per i Sistemi ad Alto Rischio

I fornitori di sistemi di IA ad alto rischio devono implementare:

| Requisito | Articolo | Descrizione |
|-----------|----------|-------------|
| **Sistema di gestione del rischio** | Art. 9 | Processo iterativo durante l'intero ciclo di vita del sistema |
| **Governance dei dati** | Art. 10 | Qualita, pertinenza, rappresentativita dei dataset di addestramento |
| **Documentazione tecnica** | Art. 11 | Documentazione completa per dimostrare la conformita |
| **Registrazione automatica** | Art. 12 | Logging degli eventi rilevanti durante il funzionamento |
| **Trasparenza** | Art. 13 | Istruzioni d'uso comprensibili per i deployer |
| **Sorveglianza umana** | Art. 14 | Possibilita di supervisione e intervento umano |
| **Accuratezza e robustezza** | Art. 15 | Livelli appropriati di prestazioni e sicurezza informatica |
| **Sistema di gestione qualita** | Art. 17 | QMS documentato per garantire la conformita |
| **Valutazione di conformita** | Art. 43 | Assessment (auto-dichiarazione o ente notificato) prima dell'immissione sul mercato |
| **Marcatura CE** | Art. 48 | Marcatura obbligatoria per sistemi conformi |
| **Registrazione EU Database** | Art. 49 | Registrazione nella banca dati pubblica dell'UE |

### Modelli di IA per Finalita Generali (GPAI)

I fornitori di modelli GPAI (General-Purpose AI), inclusi i large language models, hanno obblighi
specifici in vigore dal 2 agosto 2025:

```
Obblighi per tutti i modelli GPAI:
  - Documentazione tecnica del modello (scheda tecnica)
  - Politica di conformita al diritto d'autore dell'UE
  - Pubblicazione di un riepilogo dettagliato dei dati di addestramento
  - Cooperazione con le autorita e i provider a valle

Obblighi aggiuntivi per modelli GPAI con rischio sistemico:
  (modelli addestrati con potenza di calcolo superiore a 10^25 FLOP)
  - Valutazione del modello secondo protocolli standardizzati
  - Valutazione e mitigazione dei rischi sistemici
  - Tracciamento e segnalazione degli incidenti gravi
  - Protezione adeguata della sicurezza informatica del modello
  - Reporting dell'efficienza energetica del modello
```

### Sanzioni EU AI Act

| Violazione | Sanzione Massima |
|------------|-----------------|
| **Pratiche proibite** | 35M EUR o 7% del fatturato globale annuo |
| **Requisiti per sistemi ad alto rischio** | 15M EUR o 3% del fatturato globale annuo |
| **Obblighi di trasparenza e GPAI** | 7,5M EUR o 1% del fatturato globale annuo |
| **Informazioni false alle autorita** | 7,5M EUR o 1% del fatturato globale annuo |

Per le PMI e le startup, le sanzioni sono calcolate in modo proporzionato per evitare
effetti sproporzionati sulla loro competitivita.

### Intersezione con GDPR e Compliance IT

L'EU AI Act interagisce con il GDPR in diversi ambiti critici:

- **Dati di addestramento**: i dataset devono rispettare i principi di minimizzazione e base giuridica del GDPR
- **Profilazione**: i sistemi di IA che effettuano profilazione sono soggetti sia all'AI Act sia all'Art. 22 GDPR
- **DPIA**: i sistemi ad alto rischio che trattano dati personali richiedono sia la DPIA (GDPR) sia la valutazione di conformita (AI Act)
- **Trasparenza**: obblighi di trasparenza dell'AI Act si sommano all'informativa privacy del GDPR
- **Audit**: gli auditor di sicurezza e compliance devono verificare la conformita a entrambi i regolamenti

---

## 9. HIPAA — Health Insurance Portability and Accountability Act

### Cos'e l'HIPAA

L'Health Insurance Portability and Accountability Act (HIPAA) e una legge federale statunitense
del 1996 che stabilisce requisiti per la protezione delle informazioni sanitarie protette (PHI —
Protected Health Information). Sebbene sia una normativa USA, la sua rilevanza per le organizzazioni
europee e significativa quando trattano dati sanitari di cittadini americani o operano nel mercato
sanitario statunitense.

L'HIPAA si applica alle **covered entity** (fornitori di servizi sanitari, piani sanitari,
clearing house sanitarie) e ai **business associate** (fornitori di servizi che trattano PHI
per conto di una covered entity).

### Le Tre Regole Principali

```
1. Privacy Rule (45 CFR Part 160 e Part 164, Subparts A e E)
   - Definisce quali informazioni sanitarie sono protette (PHI)
   - Stabilisce i diritti dei pazienti sui propri dati
   - Limita l'uso e la divulgazione delle PHI
   - Richiede un avviso sulle pratiche di privacy (Notice of Privacy Practices)
   - Principio del "minimum necessary": accedere solo ai dati necessari

2. Security Rule (45 CFR Part 164, Subpart C)
   - Requisiti per la protezione delle PHI elettroniche (ePHI)
   - Tre categorie di salvaguardie:
     a. Administrative Safeguards
     b. Physical Safeguards
     c. Technical Safeguards
   - Approccio basato sul rischio per l'implementazione
   - Documentazione e revisione periodica dei controlli

3. Breach Notification Rule (45 CFR Part 164, Subpart D)
   - Notifica alle persone interessate entro 60 giorni dalla scoperta
   - Notifica al HHS (Department of Health and Human Services)
   - Se la violazione coinvolge > 500 persone: notifica anche ai media
   - Registro delle violazioni minori (meno di 500 persone) con report annuale
```

### Salvaguardie Tecniche (Technical Safeguards)

Le salvaguardie tecniche sono i controlli IT fondamentali richiesti dall'HIPAA:

| Requisito | Standard | Specifiche di Implementazione |
|-----------|----------|-------------------------------|
| **Controllo degli accessi** | §164.312(a)(1) | ID utente univoco, procedure di emergenza, logout automatico, cifratura e decifratura |
| **Controlli di audit** | §164.312(b) | Meccanismi hardware, software e procedurali per registrare l'accesso alle ePHI |
| **Integrita** | §164.312(c)(1) | Protezione delle ePHI da alterazione o distruzione non autorizzata |
| **Autenticazione** | §164.312(d) | Verifica dell'identita di persone o entita che accedono alle ePHI |
| **Sicurezza delle trasmissioni** | §164.312(e)(1) | Controlli di integrita e cifratura per ePHI trasmesse su reti elettroniche |

### Aggiornamento della Security Rule 2025-2026

Il 6 gennaio 2025, l'HHS ha pubblicato una proposta di revisione significativa della Security Rule,
il cambiamento piu importante per la protezione delle ePHI degli ultimi venti anni.

Principali modifiche proposte:

```
Eliminazione della distinzione "required" vs "addressable":
  - Tutte le specifiche di implementazione diventano obbligatorie
  - Non e piu possibile giustificare la mancata implementazione con analisi di rischio
  - Sei controlli tecnici obbligatori specifici

Nuovi requisiti tecnici obbligatori:
  - MFA (Multi-Factor Authentication) per tutti gli accessi alle ePHI
  - Cifratura obbligatoria delle ePHI at rest e in transit (non piu "addressable")
  - Segmentazione di rete come salvaguardia obbligatoria
  - Vulnerability scanning almeno ogni 6 mesi
  - Penetration testing almeno annuale
  - Restore da backup testato almeno ogni 6 mesi

Audit e verifica:
  - Audit di conformita completo almeno annuale (non piu periodico)
  - Verifica scritta annuale dai business associate
  - Documentazione formale di tutti i controlli e la loro efficacia
  - Inventario aggiornato di tutti gli asset tecnologici che trattano ePHI

Compliance timeline:
  - 240 giorni dalla pubblicazione della regola finale per adeguarsi
  - Pubblicazione attesa nel corso del 2026
  - Conformita stimata per inizio 2027
```

### Sanzioni HIPAA

| Livello | Descrizione | Sanzione per Violazione | Massimo Annuo |
|---------|-------------|------------------------|---------------|
| **Tier 1** | Violazione inconsapevole | 137 - 68.928 USD | 2.067.813 USD |
| **Tier 2** | Causa ragionevole (non negligenza volontaria) | 1.379 - 68.928 USD | 2.067.813 USD |
| **Tier 3** | Negligenza volontaria corretta | 13.785 - 68.928 USD | 2.067.813 USD |
| **Tier 4** | Negligenza volontaria non corretta | 68.928 USD | 2.067.813 USD |

In aggiunta alle sanzioni civili, le violazioni intenzionali possono comportare sanzioni penali
fino a 250.000 USD e 10 anni di reclusione.

---

## 10. Audit e Assessment

### Tipi di Audit

| Tipo | Eseguito da | Obiettivo | Indipendenza |
|------|-------------|-----------|--------------|
| **Audit interno** | Team interno (internal audit) | Verifica conformita, miglioramento | Funzionale (separato dalle operations) |
| **Audit esterno** | Organismo di certificazione (CB) | Certificazione, attestazione | Totale (ente terzo accreditato) |
| **Audit di seconda parte** | Cliente/partner | Due diligence, verifica fornitore | Parziale (interesse commerciale) |
| **Audit di terza parte** | Ente indipendente | Conformita normativa, certificazione | Totale (nessuna relazione commerciale) |
| **Audit regolamentare** | Autorita competente | Verifica conformita legale | Totale (autorita pubblica) |

### Audit Planning

La pianificazione dell'audit segue un processo strutturato:

```
1. Definizione dell'obiettivo
   - Scope dell'audit (sistemi, processi, sedi)
   - Standard/normativa di riferimento
   - Criteri di audit

2. Risk-based planning
   - Aree a maggior rischio ricevono maggiore attenzione
   - Considerare i risultati degli audit precedenti
   - Valutare i cambiamenti significativi

3. Programma di audit
   - Calendario delle attivita
   - Allocazione delle risorse (auditor, tempo, accessi)
   - Comunicazione alle parti coinvolte

4. Audit checklist
   - Lista dei controlli da verificare
   - Evidenze richieste per ciascun controllo
   - Metodi di verifica (intervista, osservazione, test)

5. Pre-audit communication
   - Notifica ai responsabili delle aree in scope
   - Richiesta documentazione preliminare
   - Definizione logistica (sale, accessi, contatti)
```

### Evidence Collection

Le evidenze di audit si raccolgono attraverso quattro modalita principali:

**Documentale**: policy, procedure, registri, log, report, configurazioni, contratti

```
Esempi di evidenze documentali:
  - Information Security Policy approvata e datata
  - Registro dei trattamenti (GDPR art. 30)
  - Change management log degli ultimi 12 mesi
  - Report di vulnerability scan trimestrale
  - Minutes del management review meeting
  - Contratti con clausole di sicurezza
```

**Interviste**: colloqui con personale responsabile dei controlli

```
Esempi di domande d'intervista:
  - "Come viene gestita una richiesta di accesso privilegiato?"
  - "Qual e la procedura in caso di data breach?"
  - "Con quale frequenza vengono testati i backup?"
  - "Come viene notificato il team in caso di incidente critico?"
```

**Osservazione**: verifica diretta del funzionamento dei controlli

```
Esempi di osservazione:
  - Verifica che i badge di accesso funzionino correttamente
  - Osservazione del processo di onboarding di un nuovo dipendente
  - Verifica della presenza di serrature su armadi server
  - Osservazione di un cambio turno nel SOC
```

**Test tecnici**: verifica dell'efficacia dei controlli tecnici

```
Esempi di test tecnici:
  - Tentativo di accesso con credenziali scadute
  - Verifica della cifratura delle connessioni (TLS)
  - Test di restore da backup
  - Verifica delle regole firewall
  - Scansione di vulnerabilita su un campione di sistemi
```

### Classificazione dei Finding

| Classificazione | Definizione | Tempistica Remediation |
|-----------------|-------------|----------------------|
| **Non-conformita maggiore** | Assenza o fallimento totale di un controllo critico; rischio significativo | 30-90 giorni |
| **Non-conformita minore** | Implementazione parziale o debolezza in un controllo | 90-180 giorni |
| **Osservazione** | Opportunita di miglioramento, non una non-conformita | Prossimo ciclo di audit |
| **Nota positiva** | Controllo che supera i requisiti, best practice | N/A |

### Remediation Tracking

```
Per ogni finding:

ID Finding: AUD-2025-042
Classificazione: Non-conformita minore
Controllo: A.8.8 - Management of technical vulnerabilities
Descrizione: Le scansioni di vulnerabilita non vengono eseguite
             con la frequenza prevista dalla procedura (mensile).
             Negli ultimi 6 mesi sono state eseguite solo 3 scansioni.
Evidenza: Report Nessus, log di esecuzione pianificata
Root Cause: Mancanza di automazione, dipendenza da attivita manuale
Azione Correttiva: Implementare scansione automatizzata con scheduling
Responsabile: Security Operations Manager
Scadenza: 2025-09-30
Stato: In corso
Verifica: Audit follow-up pianificato per 2025-10-15
```

### Continuous Auditing

L'audit continuo utilizza la tecnologia per monitorare i controlli in tempo reale:

- Automated control testing con frequenza giornaliera o settimanale
- Dashboard con lo stato di conformita in tempo reale
- Alert automatici per deviazioni dai controlli attesi
- Integrazione con SIEM per il monitoraggio degli eventi di sicurezza
- Automated evidence collection per ridurre il carico manuale

---

## 11. Risk Assessment e Management

### Metodologie Principali

| Metodologia | Origine | Approccio | Uso Tipico |
|-------------|---------|-----------|------------|
| **ISO 27005** | ISO/IEC | Qualitativo/quantitativo, allineato a ISO 27001 | ISMS certification |
| **NIST RMF** | NIST (USA) | 7 step framework, categorize-select-implement-assess-authorize-monitor | Federal systems, enterprise |
| **OCTAVE** | CMU/SEI | Self-directed, asset-based | Organizzazioni con risorse limitate |
| **FAIR** | Factor Analysis of Information Risk | Quantitativo, basato su fattori finanziari | Risk quantification, ROI |
| **CRAMM** | UK Government | Qualitativo/semi-quantitativo | Government, difesa |
| **EBIOS RM** | ANSSI (Francia) | Basato su scenari di minaccia | Critical infrastructure |

### Risk Identification

Processo di identificazione sistematica dei rischi:

```
1. Asset Identification
   - Sistemi informativi (server, database, applicazioni)
   - Dati (classificati per sensibilita)
   - Processi di business
   - Persone (competenze critiche)
   - Infrastruttura fisica

2. Threat Identification
   - Minacce naturali (terremoto, alluvione, incendio)
   - Minacce umane intenzionali (hacker, insider threat, APT)
   - Minacce umane non intenzionali (errore umano, negligenza)
   - Minacce tecniche (guasto hardware, bug software, obsolescenza)
   - Minacce alla supply chain (compromissione fornitore)

3. Vulnerability Identification
   - Vulnerabilita tecniche (CVE, misconfiguration)
   - Vulnerabilita organizzative (mancanza di policy, formazione insufficiente)
   - Vulnerabilita fisiche (accesso non controllato, assenza UPS)
   - Vulnerabilita procedurali (processi non documentati)
```

### Risk Analysis — Qualitativo vs Quantitativo

**Approccio qualitativo** (piu comune, piu semplice):

| Probabilita | Valore | Descrizione |
|-------------|--------|-------------|
| Molto bassa | 1 | Evento raro, meno di una volta ogni 5 anni |
| Bassa | 2 | Evento improbabile, una volta ogni 2-5 anni |
| Media | 3 | Evento possibile, una volta all'anno |
| Alta | 4 | Evento probabile, piu volte all'anno |
| Molto alta | 5 | Evento quasi certo, frequente |

| Impatto | Valore | Descrizione |
|---------|--------|-------------|
| Trascurabile | 1 | Nessun impatto significativo su operazioni o reputazione |
| Basso | 2 | Impatto limitato, gestibile con risorse normali |
| Medio | 3 | Impatto significativo su operazioni, costi moderati |
| Alto | 4 | Impatto grave, interruzione significativa, costi elevati |
| Critico | 5 | Impatto catastrofico, minaccia alla sopravvivenza dell'organizzazione |

**Risk Evaluation Matrix**:

```
              IMPATTO
           1    2    3    4    5
P   5  |  5 | 10 | 15 | 20 | 25 |
R   4  |  4 |  8 | 12 | 16 | 20 |
O   3  |  3 |  6 |  9 | 12 | 15 |
B   2  |  2 |  4 |  6 |  8 | 10 |
.   1  |  1 |  2 |  3 |  4 |  5 |

Livello di rischio:
  1-4   = Basso (accettabile)    -> Accettare, monitorare
  5-9   = Medio (tollerabile)    -> Mitigare quando possibile
  10-15 = Alto (inaccettabile)   -> Azione correttiva richiesta
  16-25 = Critico (intollerabile)-> Azione immediata obbligatoria
```

**Approccio quantitativo (FAIR)**:

```
Single Loss Expectancy (SLE) = Valore dell'asset x Fattore di esposizione
Annual Rate of Occurrence (ARO) = Frequenza annua stimata
Annual Loss Expectancy (ALE) = SLE x ARO

Esempio:
  Asset: Database clienti (valore: 2.000.000 EUR)
  Fattore di esposizione per data breach: 30%
  SLE = 2.000.000 x 0.30 = 600.000 EUR
  ARO = 0.1 (una volta ogni 10 anni)
  ALE = 600.000 x 0.1 = 60.000 EUR/anno

  Se il controllo di mitigazione costa 40.000 EUR/anno
  e riduce l'ARO a 0.02:
  Nuovo ALE = 600.000 x 0.02 = 12.000 EUR/anno
  ROI del controllo = (60.000 - 12.000 - 40.000) = 8.000 EUR/anno
```

### Risk Treatment

Le quattro opzioni di trattamento del rischio:

| Opzione | Descrizione | Quando usarla |
|---------|-------------|---------------|
| **Mitigate** (Mitigare) | Implementare controlli per ridurre probabilita o impatto | Rischio riducibile con costi ragionevoli |
| **Transfer** (Trasferire) | Trasferire il rischio a terzi (assicurazione, outsourcing) | Rischio finanziario, expertise mancante |
| **Accept** (Accettare) | Accettare il rischio consapevolmente e documentarlo | Rischio basso o costo del controllo > impatto |
| **Avoid** (Evitare) | Eliminare l'attivita che genera il rischio | Rischio troppo alto e non mitigabile |

### Template Risk Register

| ID | Asset | Minaccia | Vulnerabilita | Prob. | Impatto | Rischio | Trattamento | Controllo | Owner | Scadenza | Rischio Residuo |
|----|-------|----------|---------------|-------|---------|---------|-------------|-----------|-------|----------|-----------------|
| R-001 | DB Clienti | SQL Injection | Input non validato | 4 | 5 | 20 (Critico) | Mitigare | WAF + input validation + parameterized queries | Dev Lead | 2025-06-30 | 4 (Basso) |
| R-002 | File Server | Ransomware | Patch mancanti | 3 | 4 | 12 (Alto) | Mitigare | Patch management + EDR + backup immutabili | IT Ops | 2025-07-15 | 3 (Basso) |
| R-003 | Email | Phishing | Formazione insufficiente | 4 | 3 | 12 (Alto) | Mitigare | Security awareness + email filtering + MFA | CISO | 2025-05-31 | 6 (Medio) |
| R-004 | Data Center | Alluvione | Zona a rischio idrogeologico | 2 | 5 | 10 (Alto) | Trasferire | Assicurazione + DR site in altra regione | Facility Mgr | 2025-08-31 | 4 (Basso) |
| R-005 | Legacy App | Exploit noto | EOL, no patches | 5 | 3 | 15 (Alto) | Evitare | Migrazione a nuova applicazione | App Owner | 2025-12-31 | 0 |
| R-006 | Wi-Fi Guest | Intercettazione | Traffico non cifrato | 2 | 1 | 2 (Basso) | Accettare | Rete isolata, no accesso a risorse interne | Network Eng | N/A | 2 (Basso) |

### Key Risk Indicators (KRI)

I KRI sono metriche che forniscono segnali precoci sull'aumento del rischio:

| KRI | Soglia Warning | Soglia Critica | Frequenza |
|-----|---------------|----------------|-----------|
| Vulnerabilita critiche non rimediate (>30gg) | > 5 | > 15 | Settimanale |
| Tentativi di accesso falliti | > 100/giorno | > 500/giorno | Giornaliera |
| Tempo medio di rilevamento incidenti (MTTD) | > 4 ore | > 24 ore | Mensile |
| Percentuale sistemi non patchati | > 10% | > 25% | Settimanale |
| Account con privilegi elevati | > 20 | > 50 | Mensile |
| Finding audit aperti oltre scadenza | > 3 | > 10 | Mensile |
| Fornitori senza valutazione sicurezza | > 5 | > 15 | Trimestrale |

---

## 12. Compliance Automation

### Infrastructure as Code per Compliance

L'Infrastructure as Code (IaC) consente di definire l'infrastruttura in modo dichiarativo
e versionato, rendendo la compliance verificabile, ripetibile e auditabile:

```hcl
# Terraform - Esempio: S3 bucket conforme a policy di sicurezza
resource "aws_s3_bucket" "compliant_bucket" {
  bucket = "data-store-prod"
}

resource "aws_s3_bucket_versioning" "compliant_bucket" {
  bucket = aws_s3_bucket.compliant_bucket.id
  versioning_configuration {
    status = "Enabled"    # Requisito: versioning attivo per data recovery
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "compliant_bucket" {
  bucket = aws_s3_bucket.compliant_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"    # Requisito: encryption at rest con KMS
      kms_master_key_id = aws_kms_key.data_key.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "compliant_bucket" {
  bucket = aws_s3_bucket.compliant_bucket.id

  block_public_acls       = true    # Requisito: no accesso pubblico
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "compliant_bucket" {
  bucket        = aws_s3_bucket.compliant_bucket.id
  target_bucket = aws_s3_bucket.log_bucket.id
  target_prefix = "s3-access-logs/"    # Requisito: access logging attivo
}
```

### Policy as Code

#### OPA / Rego (Open Policy Agent)

```rego
# Policy: tutti i container devono avere resource limits
package kubernetes.admission

deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    not container.resources.limits.memory
    msg := sprintf("Container '%v' manca di memory limits", [container.name])
}

deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    not container.resources.limits.cpu
    msg := sprintf("Container '%v' manca di CPU limits", [container.name])
}

# Policy: nessun container puo eseguire come root
deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    container.securityContext.runAsUser == 0
    msg := sprintf("Container '%v' non puo eseguire come root (UID 0)", [container.name])
}
```

#### Kyverno — Policy Native per Kubernetes

Kyverno e un motore di policy nativo per Kubernetes che, a differenza di OPA/Gatekeeper, non richiede
un linguaggio dedicato (Rego) ma utilizza manifest YAML e, dalla versione 1.14+, espressioni CEL
(Common Expression Language) allineate con le ValidatingAdmissionPolicy native di Kubernetes.

```yaml
# Kyverno ClusterPolicy: blocca container privilegiati
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-privileged-containers
  annotations:
    policies.kyverno.io/title: Blocco Container Privilegiati
    policies.kyverno.io/category: Pod Security
    policies.kyverno.io/severity: high
    policies.kyverno.io/description: >-
      I container privilegiati hanno accesso completo all'host e rappresentano
      un rischio di sicurezza inaccettabile. Questa policy impedisce la creazione
      di container con securityContext.privileged impostato su true.
spec:
  validationFailureAction: Enforce
  background: true
  rules:
    - name: deny-privileged
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: >-
          I container privilegiati sono vietati. Impostare
          spec.containers[*].securityContext.privileged su false.
        pattern:
          spec:
            containers:
              - securityContext:
                  privileged: "false"
```

```yaml
# Kyverno ClusterPolicy: obbligo label di compliance su tutti i namespace
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-compliance-labels
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-compliance-labels
      match:
        any:
          - resources:
              kinds:
                - Namespace
      validate:
        message: >-
          I namespace devono avere le label obbligatorie:
          data-classification, owner, compliance-framework.
        pattern:
          metadata:
            labels:
              data-classification: "?*"
              owner: "?*"
              compliance-framework: "?*"
```

```yaml
# Kyverno ValidatingPolicy con CEL (Kyverno 1.14+)
# Richiede che tutte le immagini provengano da un registry approvato
apiVersion: kyverno.io/v2beta1
kind: ValidatingPolicy
metadata:
  name: restrict-image-registries
spec:
  validationFailureAction: Enforce
  rules:
    - name: validate-registries
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        cel:
          expressions:
            - expression: >-
                object.spec.containers.all(c,
                  c.image.startsWith('registry.azurecr.io/') ||
                  c.image.startsWith('gcr.io/my-project/') ||
                  c.image.startsWith('123456789.dkr.ecr.eu-west-1.amazonaws.com/')
                )
              message: >-
                Le immagini devono provenire da un container registry approvato.
                Registry consentiti: registry.azurecr.io, gcr.io/my-project,
                123456789.dkr.ecr.eu-west-1.amazonaws.com.
```

#### Confronto OPA vs Kyverno

| Aspetto | OPA / Gatekeeper | Kyverno |
|---------|------------------|---------|
| **Linguaggio policy** | Rego (linguaggio dedicato) | YAML nativo + CEL (v1.14+) |
| **Curva di apprendimento** | Alta (Rego richiede studio dedicato) | Bassa (YAML familiare per chi usa K8s) |
| **Mutation** | Supporto limitato (webhook separato) | Nativo (regole mutate e generate) |
| **Generazione risorse** | Non supportata | Nativa (genera ConfigMap, NetworkPolicy, etc.) |
| **Policy Reports** | Richiede integrazione esterna | Nativo (PolicyReport CRD) |
| **Scope** | Multi-piattaforma (K8s, Terraform, API, microservizi) | Kubernetes-specifico |
| **Validazione immagini** | Richiede policy personalizzate | Verifica firma Cosign/Notary integrata |
| **Community** | CNCF Graduated | CNCF Graduated |
| **Best practice 2026** | Scenari multi-piattaforma e logica complessa | Governance Kubernetes-native con CEL |

#### Pipeline di Compliance-as-Code nella CI/CD

```yaml
# Esempio di pipeline GitLab CI con compliance gate
stages:
  - lint
  - security
  - compliance
  - deploy

policy-lint:
  stage: lint
  script:
    - kyverno apply policies/ --resource manifests/ --output json > policy-results.json
    - |
      VIOLATIONS=$(jq '[.[] | select(.result == "fail")] | length' policy-results.json)
      if [ "$VIOLATIONS" -gt 0 ]; then
        echo "ERRORE: $VIOLATIONS violazioni delle policy rilevate"
        jq '.[] | select(.result == "fail")' policy-results.json
        exit 1
      fi
    - echo "Tutte le policy soddisfatte"

opa-policy-check:
  stage: compliance
  script:
    - conftest test manifests/ --policy policies/opa/ --output json > opa-results.json
    - conftest test terraform/ --policy policies/terraform/ --output json >> opa-results.json
  artifacts:
    paths:
      - opa-results.json
    expire_in: 1 year

terraform-compliance:
  stage: compliance
  script:
    - terraform plan -out=plan.tfplan
    - terraform show -json plan.tfplan > plan.json
    - conftest test plan.json --policy policies/terraform-compliance/
    - checkov -f plan.json --framework terraform_plan --output json > checkov-results.json
  artifacts:
    paths:
      - checkov-results.json
    expire_in: 1 year
```

#### AWS Config Rules

```yaml
# AWS Config Rule: verifica che EBS volumes siano cifrati
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  EncryptedVolumesRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: encrypted-volumes
      Description: "Verifica che tutti i volumi EBS siano cifrati"
      Source:
        Owner: AWS
        SourceIdentifier: ENCRYPTED_VOLUMES
      Scope:
        ComplianceResourceTypes:
          - "AWS::EC2::Volume"

  S3BucketEncryptionRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: s3-bucket-server-side-encryption-enabled
      Description: "Verifica encryption su S3 buckets"
      Source:
        Owner: AWS
        SourceIdentifier: S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED

  RDSEncryptionRule:
    Type: AWS::Config::ConfigRule
    Properties:
      ConfigRuleName: rds-storage-encrypted
      Description: "Verifica che le istanze RDS abbiano storage cifrato"
      Source:
        Owner: AWS
        SourceIdentifier: RDS_STORAGE_ENCRYPTED
```

#### Azure Policy

```json
{
  "properties": {
    "displayName": "Storage accounts dovrebbero usare customer-managed keys",
    "policyType": "Custom",
    "mode": "All",
    "description": "Policy per garantire che gli storage account usino CMK per encryption",
    "parameters": {},
    "policyRule": {
      "if": {
        "allOf": [
          {
            "field": "type",
            "equals": "Microsoft.Storage/storageAccounts"
          },
          {
            "not": {
              "field": "Microsoft.Storage/storageAccounts/encryption.keySource",
              "equals": "Microsoft.Keyvault"
            }
          }
        ]
      },
      "then": {
        "effect": "deny"
      }
    }
  }
}
```

### Tool per Compliance Automation

#### Prowler (AWS/Azure/GCP Security Assessment)

```bash
# Installazione
pip install prowler

# Scansione completa AWS con output in formato specifico per compliance
prowler aws --compliance cis_2.0_aws

# Scansione specifica per GDPR
prowler aws --compliance gdpr_aws

# Scansione per PCI-DSS
prowler aws --compliance pci_3.2.1_aws

# Scansione specifica di servizi
prowler aws --services s3 ec2 iam rds

# Output in formato CSV per l'analisi
prowler aws --compliance cis_2.0_aws -M csv -o /tmp/prowler-results/

# Scansione Azure
prowler azure --compliance cis_2.0_azure

# Scansione GCP
prowler gcp --compliance cis_2.0_gcp
```

#### Chef InSpec (Infrastructure Testing)

```ruby
# Profilo InSpec per verificare la conformita di un server Linux

# controls/ssh_config.rb
control 'ssh-01' do
  impact 1.0
  title 'SSH deve essere configurato in modo sicuro'
  desc 'Verifica le configurazioni di sicurezza SSH'

  describe sshd_config do
    its('Protocol') { should cmp 2 }
    its('PermitRootLogin') { should eq 'no' }
    its('PasswordAuthentication') { should eq 'no' }
    its('MaxAuthTries') { should cmp <= 4 }
    its('ClientAliveInterval') { should cmp <= 300 }
    its('ClientAliveCountMax') { should cmp <= 3 }
    its('X11Forwarding') { should eq 'no' }
    its('LogLevel') { should eq 'VERBOSE' }
  end
end

control 'ssh-02' do
  impact 0.7
  title 'Chiavi SSH devono avere permessi corretti'
  desc 'Le chiavi private SSH non devono essere leggibili da altri'

  describe file('/etc/ssh/ssh_host_rsa_key') do
    its('mode') { should cmp '0600' }
    its('owner') { should eq 'root' }
    its('group') { should eq 'root' }
  end
end
```

```bash
# Esecuzione profilo InSpec
inspec exec /path/to/profile --reporter cli json:/tmp/inspec-results.json

# Esecuzione su target remoto via SSH
inspec exec /path/to/profile -t ssh://user@host -i /path/to/key

# Esecuzione profilo CIS Benchmark
inspec exec https://github.com/dev-sec/linux-baseline

# Esecuzione con supermarket profile
inspec supermarket exec dev-sec/linux-baseline
```

#### ScoutSuite (Multi-Cloud Security Auditing)

```bash
# Installazione
pip install scoutsuite

# Scansione AWS
scout aws --report-dir /tmp/scoutsuite-report/

# Scansione Azure
scout azure --cli --report-dir /tmp/scoutsuite-report/

# Scansione GCP
scout gcp --user-account --report-dir /tmp/scoutsuite-report/

# Scansione con regole personalizzate
scout aws --ruleset /path/to/custom-rules.json
```

### CIS Benchmarks Automation

```bash
# Esempio: verifica CIS Benchmark per Ubuntu Linux

# CIS 1.1.1.1 - Verifica che il filesystem cramfs sia disabilitato
modprobe -n -v cramfs 2>/dev/null | grep -q "install /bin/true" && \
  echo "PASS: cramfs disabilitato" || echo "FAIL: cramfs non disabilitato"

# CIS 5.2.1 - Verifica configurazione auditd
systemctl is-enabled auditd 2>/dev/null && \
  echo "PASS: auditd abilitato" || echo "FAIL: auditd non abilitato"

# CIS 5.4.1 - Verifica password policy
grep -q "^PASS_MAX_DAYS\s*365" /etc/login.defs && \
  echo "PASS: password max days configurato" || echo "FAIL: password max days non conforme"

# Automazione con script di verifica completa
# (usando InSpec con profilo CIS)
inspec exec https://github.com/dev-sec/cis-ubuntu-linux-benchmark \
  --reporter cli json:/tmp/cis-results.json
```

---

## 13. Evidence Collection e Documentation

### Tipi di Evidenze

Le evidenze di compliance si suddividono in categorie principali, ciascuna con requisiti
specifici di raccolta e conservazione:

| Tipo | Descrizione | Esempi | Formato Tipico |
|------|-------------|--------|----------------|
| **Screenshots** | Catture di schermate di configurazioni e dashboard | Console IAM, firewall rules, dashboard SIEM | PNG, PDF con timestamp |
| **Log** | Registri di eventi dei sistemi | Access log, audit log, change log | Syslog, JSON, CSV |
| **Configurazioni** | Stato attuale delle configurazioni di sistema | Firewall rules, group policy, security settings | Export nativo, JSON, XML |
| **Report** | Output di strumenti di analisi | Vulnerability scan, penetration test, backup report | PDF, HTML, CSV |
| **Documenti** | Policy, procedure, registri organizzativi | Security policy, incident response plan, risk register | PDF firmato, Word |
| **Attestazioni** | Dichiarazioni di conformita firmate | Management assertion, sign-off | PDF firmato digitalmente |

### Archiviazione e Retention delle Evidenze

La conservazione delle evidenze deve rispettare i requisiti normativi applicabili:

| Standard/Normativa | Periodo di Retention Minimo | Note |
|--------------------|-----------------------------|------|
| **ISO 27001** | 3 anni (ciclo di certificazione) | Conservare per l'intero ciclo + 1 anno |
| **SOC 2** | 7 anni (requisito CPA) | 1 anno minimo per Type II, 7 anni per archivio |
| **GDPR** | Durata del trattamento + periodo necessario | Dimostrare conformita anche dopo cessazione |
| **PCI-DSS** | 1 anno (log) / 3 anni (policy) | Log di audit per almeno 1 anno, 3 mesi online |
| **NIS2** | Come definito da ACN | Allineato alla retention degli incidenti |

### Chain of Custody

Per le evidenze che potrebbero essere utilizzate in procedimenti legali o investigazioni:

```
Chain of Custody Record:

Evidence ID:        EV-2025-0142
Description:        Access log del server DB-PROD-01 (2025-01-01 / 2025-03-31)
Format:             Syslog compresso (tar.gz)
Hash (SHA-256):     a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
Date Collected:     2025-04-01 09:15 UTC
Collected By:       Mario Rossi (Security Analyst)
Collection Method:  Export automatico via rsyslog, verificato con checksum
Storage Location:   Evidence vault - NAS-EVIDENCE-01:/evidence/2025/Q1/
Access Log:
  - 2025-04-01 09:15 - Mario Rossi - Raccolta iniziale
  - 2025-04-05 14:30 - Giulia Bianchi (Auditor) - Revisione
  - 2025-04-10 10:00 - External Auditor - Verifica per SOC 2
```

### Documentazione delle Policy e Procedure

Ogni policy e procedura deve seguire una struttura standardizzata:

```
POLICY TEMPLATE:

Titolo:                 [Nome della policy]
ID Documento:           POL-SEC-XXX
Versione:               X.Y
Data di emissione:      YYYY-MM-DD
Data di revisione:      YYYY-MM-DD
Prossima revisione:     YYYY-MM-DD
Classificazione:        Interna / Riservata / Pubblica
Approvato da:           [Nome, Ruolo]
Owner:                  [Nome, Ruolo]

1. Scopo
   [Perche questa policy esiste]

2. Ambito di applicazione
   [A chi e a cosa si applica]

3. Definizioni
   [Termini tecnici utilizzati]

4. Policy Statement
   [Le regole effettive]

5. Ruoli e responsabilita
   [Chi fa cosa]

6. Eccezioni
   [Processo per richiedere eccezioni]

7. Non-conformita
   [Conseguenze della violazione]

8. Riferimenti
   [Standard, leggi, altre policy correlate]

9. Storico delle revisioni
   [Changelog del documento]
```

### Change Management Records

I record di change management sono evidenze critiche per la compliance:

```
CHANGE REQUEST RECORD:

Change ID:          CHG-2025-0089
Titolo:             Aggiornamento firewall rules per nuovo segmento PCI
Priorita:           Alta
Tipo:               Standard / Normale / Emergency
Data richiesta:     2025-03-15
Richiedente:        Network Security Team

Descrizione:
  Aggiunta regole firewall per isolare il nuovo segmento PCI DSS
  per il processing dei pagamenti con carte di credito.

Impatto:
  - Sistemi coinvolti: FW-CORE-01, FW-CORE-02
  - Servizi impattati: Nessuna interruzione prevista
  - Rischio: Medio (possibile impatto se regole errate)

Piano di implementazione:
  1. Backup configurazione attuale
  2. Applicare le regole in modalita test (log-only)
  3. Verificare il traffico per 24 ore
  4. Passare in modalita enforce
  5. Verifica post-implementazione

Piano di rollback:
  Ripristino della configurazione dal backup (tempo stimato: 15 min)

Approvazioni:
  - Change Manager: Approvato (2025-03-16)
  - Security Team: Approvato (2025-03-16)
  - CAB (Change Advisory Board): Approvato (2025-03-17)

Implementazione:
  - Data esecuzione: 2025-03-20 02:00 UTC
  - Eseguito da: Network Engineer (Alessandro Verdi)
  - Risultato: Completato con successo
  - Post-Implementation Review: Superata (2025-03-21)
```

### Access Review Records

```
ACCESS REVIEW RECORD:

Review Period:      Q1 2025 (Gennaio - Marzo)
Reviewer:           IT Security Manager
Review Date:        2025-04-05

Scope:
  - Sistemi: Active Directory, AWS IAM, Database di produzione
  - Account: Tutti gli account con accesso privilegiato

Risultati:

| Account | Sistema | Ruolo | Ultimo Accesso | Azione | Giustificazione |
|---------|---------|-------|----------------|--------|-----------------|
| admin-jrossi | AWS IAM | Admin | 2025-03-28 | Confermato | Sysadmin attivo |
| svc-backup | AD | Service | 2025-03-30 | Confermato | Servizio backup |
| admin-mverdi | AWS IAM | Admin | 2024-11-15 | Revocato | Cambio ruolo |
| dev-lbianchi | DB Prod | DBA | 2024-09-01 | Revocato | Dimesso |
| admin-temp01 | AD | Admin | N/A | Revocato | Account temporaneo scaduto |

Anomalie identificate: 2 account con accesso privilegiato non piu giustificato
Azioni correttive: Account revocati entro 24 ore dalla revisione
Prossima revisione: Q2 2025 (prevista per 2025-07-05)
```

### Automated Evidence Collection Pipeline

```yaml
# Pipeline di raccolta automatica evidenze (esempio con GitLab CI)
stages:
  - collect
  - validate
  - store

collect_vulnerability_scans:
  stage: collect
  script:
    - prowler aws --compliance cis_2.0_aws -M json -o evidence/vuln-scan/
    - DATE=$(date +%Y-%m-%d)
    - mv evidence/vuln-scan/prowler-output*.json evidence/vuln-scan/${DATE}-prowler-cis.json
  artifacts:
    paths:
      - evidence/vuln-scan/
    expire_in: 1 year

collect_access_reviews:
  stage: collect
  script:
    - aws iam generate-credential-report
    - aws iam get-credential-report --output json > evidence/access/iam-credential-report.json
    - aws iam list-users --output json > evidence/access/iam-users.json
    - |
      aws iam list-users --query 'Users[*].UserName' --output text | while read user; do
        aws iam list-attached-user-policies --user-name "$user" --output json \
          >> evidence/access/iam-user-policies.json
      done
  artifacts:
    paths:
      - evidence/access/
    expire_in: 1 year

collect_config_snapshots:
  stage: collect
  script:
    - aws configservice get-compliance-summary-by-config-rule --output json \
        > evidence/config/compliance-summary.json
    - aws configservice get-compliance-details-by-config-rule \
        --config-rule-name encrypted-volumes --output json \
        > evidence/config/encrypted-volumes.json
  artifacts:
    paths:
      - evidence/config/
    expire_in: 1 year

validate_evidence:
  stage: validate
  script:
    - |
      for file in evidence/**/*.json; do
        sha256sum "$file" >> evidence/checksums.sha256
        echo "Validated: $file - $(stat -c %s "$file") bytes"
      done
    - echo "Evidence collection completed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  artifacts:
    paths:
      - evidence/
    expire_in: 1 year

store_evidence:
  stage: store
  script:
    - TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    - tar czf evidence-${TIMESTAMP}.tar.gz evidence/
    - sha256sum evidence-${TIMESTAMP}.tar.gz > evidence-${TIMESTAMP}.tar.gz.sha256
    - aws s3 cp evidence-${TIMESTAMP}.tar.gz s3://compliance-evidence-vault/${TIMESTAMP}/
    - aws s3 cp evidence-${TIMESTAMP}.tar.gz.sha256 s3://compliance-evidence-vault/${TIMESTAMP}/
  only:
    - schedules
```

---

## 14. Data Residency e Sovranita Digitale

### Definizione e Distinzione

La data residency e la sovranita digitale sono concetti correlati ma distinti che assumono
un ruolo sempre piu centrale nel panorama normativo europeo:

```
Data Residency (Residenza dei dati):
  Requisito che i dati siano fisicamente conservati in un server
  all'interno di uno specifico confine geografico (stato o regione).
  Riguarda la localizzazione fisica dello storage.
  Esempio: un database ospitato in un data center a Francoforte.

Data Sovereignty (Sovranita dei dati):
  Requisito piu ampio: i dati sono soggetti esclusivamente alle leggi
  della giurisdizione in cui risiedono. Non basta la localizzazione
  fisica; occorre che nessuna legge extraterritoriale possa imporre
  l'accesso ai dati da parte di autorita straniere.
  Esempio: dati in un data center UE gestito da un provider soggetto
  al US CLOUD Act possono non garantire la sovranita.

Data Localization (Localizzazione dei dati):
  Obbligo normativo esplicito di conservare ed elaborare i dati
  entro i confini di un determinato paese, senza eccezioni.
  Esempio: alcune normative bancarie richiedono che i dati finanziari
  non lascino mai il territorio nazionale.
```

### Quadro Normativo Europeo 2025-2026

Il panorama della sovranita digitale in Europa si articola su diversi livelli normativi:

| Normativa | Data Applicazione | Requisiti Chiave per la Data Residency |
|-----------|-------------------|----------------------------------------|
| **GDPR (Reg. 2016/679)** | Maggio 2018 | Trasferimenti extra-UE solo con garanzie adeguate (decisione di adeguatezza, SCC, BCR) |
| **EU Data Act (Reg. 2023/2854)** | Settembre 2025 | Protezione contro accesso illecito ai dati non personali da parte di governi terzi |
| **EU Data Governance Act** | Settembre 2023 | Condizioni per il riutilizzo di dati del settore pubblico, servizi di intermediazione |
| **NIS2 (Dir. 2022/2555)** | Ottobre 2024 | Misure di sicurezza che includono la protezione del luogo di elaborazione |
| **DORA (Reg. 2022/2554)** | Gennaio 2025 | Registro dettagliato della localizzazione di elaborazione e conservazione dati per fornitori ICT |
| **EU e-Evidence Package** | Agosto 2026 | Regolamento e direttiva sull'accesso transfrontaliero alle prove elettroniche |

### EU Cloud Sovereignty Framework

Nell'ottobre 2025, la Commissione Europea ha pubblicato il Cloud Sovereignty Framework che definisce
otto obiettivi di sovranita per le istituzioni UE che acquisiscono servizi cloud:

```
1. Giurisdizione e controllo legale
   - I dati devono essere soggetti alla giurisdizione UE
   - Il provider deve operare sotto il diritto UE
   - Protezione contro leggi extraterritoriali (es. US CLOUD Act, FISA 702)

2. Protezione dei dati
   - Conformita GDPR per i dati personali
   - Cifratura con chiavi gestite dal cliente (BYOK/HYOK)
   - Accesso ai dati solo da personale con security clearance UE

3. Portabilita e interoperabilita
   - Nessun lock-in del provider
   - Formati standard per l'export dei dati
   - API interoperabili tra provider

4. Trasparenza
   - Visibilita completa su dove i dati vengono elaborati e conservati
   - Notifica in caso di accesso da parte di autorita
   - Audit trail completo degli accessi

5. Resilienza
   - Continuita operativa garantita
   - Backup e disaster recovery in giurisdizione UE
   - Indipendenza da infrastrutture critiche extra-UE

6. Sicurezza della supply chain
   - Componenti hardware e software verificabili
   - Nessuna backdoor o accesso non autorizzato
   - Certificazione della catena di fornitura

7. Capacita e competenza
   - Personale qualificato con competenze in sicurezza UE
   - Centro operativo (SOC/NOC) nell'UE
   - Supporto in lingua e fuso orario europei

8. Sostenibilita
   - Efficienza energetica del data center
   - Utilizzo di energie rinnovabili
   - Reporting sull'impronta carbonica
```

### EUCS — European Cybersecurity Certification Scheme for Cloud Services

L'EUCS e lo schema di certificazione europeo per la sicurezza dei servizi cloud, sviluppato
dall'ENISA ai sensi del Cybersecurity Act (Reg. 2019/881). Lo schema definisce tre livelli di garanzia:

| Livello | Garanzia | Controlli | Destinatari |
|---------|----------|-----------|-------------|
| **Basic** | Base | Controlli di sicurezza minimi, auto-dichiarazione | PMI, servizi non critici |
| **Substantial** | Sostanziale | Controlli intermedi, verifica di terza parte | Servizi aziendali standard |
| **High** | Elevato | Controlli rigorosi, audit approfondito, requisiti di sovranita | PA, infrastrutture critiche, settore finanziario |

Al 2026 l'EUCS e ancora in fase di candidatura e non e stato ancora finalizzato. Il dibattito
si concentra sul livello "High" e sulla possibilita di richiedere che i provider siano soggetti
esclusivamente alla giurisdizione UE (sovereignty requirement).

### Conflitto US CLOUD Act vs Normativa UE

Il conflitto tra il US CLOUD Act (2018) e la normativa europea sulla protezione dei dati rappresenta
una delle sfide principali per la sovranita digitale:

```
US CLOUD Act (Clarifying Lawful Overseas Use of Data Act):
  - Consente alle autorita USA di richiedere dati conservati all'estero
    da aziende soggette alla giurisdizione statunitense
  - Si applica indipendentemente dalla localizzazione fisica dei dati
  - Include i dati conservati in data center europei da provider USA

Normativa UE (GDPR + Data Act):
  - L'Art. 48 GDPR vieta il trasferimento di dati personali basato
    su richieste di autorita di paesi terzi senza accordo internazionale
  - Il Capitolo VII del Data Act protegge i dati non personali dall'accesso
    illecito di governi terzi
  - Obbligo per i provider di adottare misure tecniche, legali e organizzative

Implicazioni pratiche:
  - Un provider USA con data center in UE potrebbe essere obbligato
    a consegnare dati alle autorita USA in violazione del GDPR
  - Le organizzazioni devono valutare il rischio di "government access"
    nella scelta del cloud provider
  - Soluzioni possibili: sovereign cloud europei, cifratura end-to-end
    con chiavi gestite dal cliente, provider non soggetti a leggi extraterritoriali
```

### Implementazione Tecnica della Data Residency

```hcl
# Terraform - Enforcement della data residency su AWS
# Service Control Policy (SCP) per limitare le regioni AWS

resource "aws_organizations_policy" "eu_regions_only" {
  name        = "restrict-to-eu-regions"
  description = "Limita il deployment alle sole regioni EU"
  type        = "SERVICE_CONTROL_POLICY"

  content = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyNonEURegions"
        Effect    = "Deny"
        NotAction = [
          "iam:*",
          "organizations:*",
          "sts:*",
          "support:*",
          "budgets:*"
        ]
        Resource  = "*"
        Condition = {
          StringNotEquals = {
            "aws:RequestedRegion" = [
              "eu-west-1",      # Irlanda
              "eu-west-2",      # Londra
              "eu-west-3",      # Parigi
              "eu-central-1",   # Francoforte
              "eu-central-2",   # Zurigo
              "eu-south-1",     # Milano
              "eu-south-2",     # Spagna
              "eu-north-1"      # Stoccolma
            ]
          }
        }
      }
    ]
  })
}
```

```yaml
# Kyverno - Enforcement data residency su Kubernetes
# Blocca deployment che non specificano la regione EU nei label
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: enforce-eu-data-residency
spec:
  validationFailureAction: Enforce
  rules:
    - name: require-eu-region-label
      match:
        any:
          - resources:
              kinds:
                - Deployment
                - StatefulSet
      validate:
        message: >-
          Tutti i workload devono avere il label 'data-residency' impostato
          su una regione EU approvata (eu-west-1, eu-central-1, eu-south-1).
        pattern:
          metadata:
            labels:
              data-residency: "eu-*"
    - name: block-non-eu-node-affinity
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: >-
          I pod che trattano dati soggetti a requisiti di residenza devono
          specificare node affinity per nodi nella regione EU.
        deny:
          conditions:
            any:
              - key: "{{ request.object.metadata.labels.\"data-classification\" }}"
                operator: In
                value: ["confidential", "restricted"]
              - key: "{{ request.object.spec.affinity.nodeAffinity }}"
                operator: Equals
                value: ""
```

---

## 15. Compliance Multi-Cloud

### Sfide della Compliance Multi-Cloud

L'adozione di piu cloud provider introduce complessita significative per la compliance:

- **Frammentazione dei controlli**: ogni cloud ha strumenti e API diversi per implementare gli stessi controlli
- **Visibilita limitata**: difficolta nel mantenere una vista unificata dello stato di compliance
- **Competenze richieste**: necessita di expertise su piu piattaforme
- **Data residency**: garantire che i dati restino nelle giurisdizioni corrette su piu provider
- **Audit complexity**: gli auditor devono valutare controlli su piattaforme diverse
- **Policy drift**: configurazioni che divergono nel tempo tra i diversi ambienti cloud

### Shared Responsibility Model per Compliance

La responsabilita della compliance e condivisa tra cloud provider e cliente:

```
                    IaaS          PaaS          SaaS
                    ----          ----          ----
Dati                Cliente       Cliente       Cliente
Applicazioni        Cliente       Cliente       Provider
Runtime             Cliente       Provider      Provider
Middleware          Cliente       Provider      Provider
OS                  Cliente       Provider      Provider
Virtualizzazione    Provider      Provider      Provider
Server              Provider      Provider      Provider
Storage             Provider      Provider      Provider
Rete                Provider      Provider      Provider
Facility            Provider      Provider      Provider

La compliance dei controlli segue la stessa suddivisione:
- Il PROVIDER e responsabile della compliance dell'infrastruttura sottostante
- Il CLIENTE e responsabile della compliance di cio che configura e gestisce
```

### AWS — Strumenti per la Compliance

#### AWS Config

```bash
# Verificare lo stato di compliance delle AWS Config Rules
aws configservice get-compliance-summary-by-config-rule

# Dettaglio di una specifica regola
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name s3-bucket-server-side-encryption-enabled \
  --compliance-types NON_COMPLIANT

# Elenco risorse non conformi
aws configservice get-compliance-details-by-resource \
  --resource-type AWS::S3::Bucket \
  --resource-id my-bucket-name

# Creare un conformance pack (insieme di regole)
aws configservice put-conformance-pack \
  --conformance-pack-name "pci-dss-pack" \
  --template-body file://pci-dss-conformance-pack.yaml
```

#### AWS Security Hub

```bash
# Abilitare Security Hub con standard di conformita
aws securityhub enable-security-hub \
  --enable-default-standards

# Abilitare standard specifici
aws securityhub batch-enable-standards \
  --standards-subscription-requests '[
    {"StandardsArn": "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.4.0"},
    {"StandardsArn": "arn:aws:securityhub:::standards/pci-dss/v/3.2.1"},
    {"StandardsArn": "arn:aws:securityhub:::standards/aws-foundational-security-best-practices/v/1.0.0"}
  ]'

# Ottenere lo score di conformita
aws securityhub get-enabled-standards

# Elencare i finding di sicurezza
aws securityhub get-findings \
  --filters '{"ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}]}' \
  --max-items 20
```

#### AWS Artifact

AWS Artifact fornisce accesso ai report di compliance di AWS:

- Report SOC 1, SOC 2, SOC 3
- Report PCI DSS (Attestation of Compliance)
- Certificato ISO 27001
- Report FedRAMP
- Report HIPAA

### Azure — Strumenti per la Compliance

#### Azure Policy

```bash
# Elencare le policy assignment
az policy assignment list --query "[].{name:name, displayName:displayName}" -o table

# Verificare la compliance
az policy state summarize

# Creare un'assegnazione di policy (esempio: richiedi tag su risorse)
az policy assignment create \
  --name "require-cost-center-tag" \
  --display-name "Richiedi tag CostCenter su tutte le risorse" \
  --policy "/providers/Microsoft.Authorization/policyDefinitions/1e30110a-5ceb-460c-a204-c1c3969c6d62" \
  --params '{"tagName": {"value": "CostCenter"}}' \
  --scope "/subscriptions/<subscription-id>"

# Elencare le risorse non conformi
az policy state list \
  --filter "complianceState eq 'NonCompliant'" \
  --query "[].{resource:resourceId, policy:policyAssignmentName}" -o table
```

#### Azure Compliance Manager

Azure Compliance Manager offre:

- Assessment preconfigurati per GDPR, ISO 27001, SOC 2, NIST
- Compliance score basato sulle azioni completate
- Workflow di assegnazione e tracking delle azioni
- Modelli per documentazione e evidenze
- Template personalizzabili per standard interni

#### Azure Blueprints

```bash
# Creare un blueprint per compliance
az blueprint create \
  --name "ISO27001Blueprint" \
  --description "Blueprint per conformita ISO 27001" \
  --target-scope subscription

# Pubblicare il blueprint
az blueprint publish \
  --blueprint-name "ISO27001Blueprint" \
  --version "1.0"

# Assegnare il blueprint a una subscription
az blueprint assignment create \
  --name "ISO27001Assignment" \
  --blueprint-name "ISO27001Blueprint" \
  --subscription "<subscription-id>" \
  --location "westeurope"
```

### GCP — Strumenti per la Compliance

#### Security Command Center (SCC)

```bash
# Elencare i finding di sicurezza
gcloud scc findings list organizations/<org-id> \
  --source=<source-id> \
  --filter="state=\"ACTIVE\" AND category=\"PUBLIC_BUCKET_ACL\""

# Elencare gli asset con vulnerabilita
gcloud scc assets list organizations/<org-id> \
  --filter="securityMarks.marks.compliance_status=\"non_compliant\""

# Ottenere le notifiche di sicurezza
gcloud scc notifications list organizations/<org-id>
```

#### Assured Workloads

```bash
# Creare un workload con requisiti di compliance
gcloud assured workloads create \
  --organization=<org-id> \
  --location=europe-west1 \
  --display-name="EU-Data-Workload" \
  --compliance-regime=EU_REGIONS_AND_SUPPORT \
  --billing-account=<billing-account-id>

# Elencare i workload
gcloud assured workloads list --organization=<org-id> --location=europe-west1

# Verificare le violazioni
gcloud assured workloads violations list \
  --organization=<org-id> \
  --location=europe-west1 \
  --workload=<workload-id>
```

### Confronto Strumenti Cloud per Compliance

| Funzionalita | AWS | Azure | GCP |
|--------------|-----|-------|-----|
| **Policy Engine** | AWS Config Rules | Azure Policy | Organization Policy |
| **Security Posture** | Security Hub | Defender for Cloud | Security Command Center |
| **Compliance Reports** | Artifact | Compliance Manager | Compliance Reports |
| **Guardrails** | Control Tower, SCPs | Blueprints, Management Groups | Assured Workloads |
| **Configuration Audit** | Config | Policy (Guest Config) | Asset Inventory |
| **Vulnerability Scan** | Inspector | Defender Vulnerability Mgmt | Web Security Scanner |
| **Key Management** | KMS | Key Vault | Cloud KMS |
| **Secret Management** | Secrets Manager | Key Vault Secrets | Secret Manager |
| **Audit Logging** | CloudTrail | Activity Log | Cloud Audit Logs |
| **Data Classification** | Macie | Purview | DLP API |

---

## 16. Audit Logging e Immutabilita dei Log

### Requisiti Normativi per il Logging

L'audit logging e un requisito trasversale a tutte le normative di compliance. Ogni framework
stabilisce specifici obblighi in merito alla registrazione, conservazione e integrita dei log:

| Normativa | Requisiti di Logging | Retention Minimo | Immutabilita |
|-----------|---------------------|-----------------|--------------|
| **GDPR** | Log degli accessi ai dati personali, log delle richieste degli interessati | Durata del trattamento | Consigliata |
| **PCI-DSS v4.0** | Req. 10: log di tutti gli accessi a componenti CDE e CHD | 12 mesi (3 mesi online) | Obbligatoria |
| **ISO 27001** | A.8.15: log delle attivita, A.8.16: monitoraggio delle anomalie | Come definito nella policy | Raccomandata |
| **SOC 2** | CC7.2: monitoraggio anomalie, CC7.3: valutazione eventi di sicurezza | Periodo di osservazione + archivio | Obbligatoria |
| **NIS2** | Art. 21: rilevamento e risposta agli incidenti | Come definito da ACN | Obbligatoria |
| **DORA** | Art. 12: policy di logging per tutti i sistemi ICT critici | Come definito dall'autorita finanziaria | Obbligatoria |
| **HIPAA** | §164.312(b): audit controls su sistemi con ePHI | 6 anni | Obbligatoria |

### Architettura di Audit Logging Conforme

Un'architettura di audit logging conforme ai requisiti normativi deve seguire principi fondamentali
di centralizzazione, immutabilita e correlazione:

```
Livello Applicazione
  |
  +-- Structured Logging (JSON)
  |     - Timestamp ISO 8601 UTC
  |     - User ID / Service Account
  |     - Azione eseguita (CRUD)
  |     - Risorsa interessata
  |     - Risultato (successo/fallimento)
  |     - IP sorgente
  |     - Classificazione del dato acceduto
  |
  +-- Livello Infrastruttura
  |     - Accessi SSH/RDP
  |     - Modifiche configurazione
  |     - Deployment e change management
  |     - Accessi a storage e database
  |
  +-- Livello Cloud
        - Cloud audit logs (CloudTrail, Activity Log, Cloud Audit Logs)
        - API calls
        - Console access
        - IAM changes

Tutti i log convergono in:
  +-- Log Aggregator (Fluentd, Fluent Bit, Vector)
        |
        +-- SIEM / Log Analytics
        |     - Correlazione eventi
        |     - Alert in tempo reale
        |     - Dashboard di compliance
        |
        +-- Immutable Storage
        |     - Write-Once-Read-Many (WORM)
        |     - Firma crittografica (hash chain)
        |     - Retention policy automatica
        |
        +-- Long-Term Archive
              - Cold storage cifrato
              - Indicizzazione per audit
              - Chain of custody documentata
```

### Implementazione di Log Immutabili

L'immutabilita dei log e il requisito fondamentale per garantire che le evidenze
di audit non possano essere alterate, cancellate o manipolate:

```bash
# AWS CloudWatch Logs con retention immutabile
aws logs put-retention-policy \
  --log-group-name "/compliance/audit-trail" \
  --retention-in-days 365

# AWS S3 Object Lock per WORM compliance
aws s3api put-object-lock-configuration \
  --bucket compliance-audit-logs \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Days": 365
      }
    }
  }'

# Nota: in modalita COMPLIANCE, nemmeno l'account root puo eliminare
# o sovrascrivere gli oggetti prima della scadenza della retention.

# Verifica integrita con hash chain
# Ogni batch di log include l'hash del batch precedente
openssl dgst -sha256 audit-log-batch-001.json.gz
# Output: SHA2-256(audit-log-batch-001.json.gz)= a3f2b8c9...
# Il digest viene incluso come metadato nel batch successivo
```

### Structured Audit Log Format

Un formato strutturato standardizzato facilita la ricerca, la correlazione e l'analisi:

```json
{
  "timestamp": "2026-05-24T14:32:18.456Z",
  "version": "1.0",
  "level": "INFO",
  "event": {
    "category": "data_access",
    "type": "read",
    "outcome": "success"
  },
  "actor": {
    "user_id": "usr_a1b2c3d4",
    "username": "mario.rossi@company.eu",
    "role": "data_analyst",
    "auth_method": "sso_mfa",
    "source_ip": "10.0.1.42",
    "user_agent": "Mozilla/5.0"
  },
  "resource": {
    "type": "database_record",
    "id": "customers/12345",
    "data_classification": "personal",
    "compliance_scope": ["gdpr", "pci-dss"]
  },
  "context": {
    "service": "customer-api",
    "environment": "production",
    "region": "eu-central-1",
    "trace_id": "abc-123-def-456",
    "request_id": "req_789xyz"
  },
  "compliance": {
    "gdpr_legal_basis": "contract",
    "data_subject_category": "customer",
    "processing_purpose": "order_fulfillment",
    "retention_policy": "36_months"
  }
}
```

### Checklist di Compliance per il Logging

```
Pre-Audit Logging Checklist:

Completezza:
  [ ] Tutti i sistemi in scope generano audit log
  [ ] Login/logout e tentativi falliti sono registrati
  [ ] Accessi ai dati classificati (personali, finanziari, sanitari) sono tracciati
  [ ] Operazioni privilegiate (admin, root, service account) sono registrate
  [ ] Modifiche alle configurazioni di sicurezza sono loggate
  [ ] Operazioni di creazione, modifica e cancellazione dati sono tracciate

Integrita:
  [ ] I log sono conservati in storage immutabile (WORM)
  [ ] Hash chain o firma crittografica applicata a ogni batch
  [ ] Separazione dei privilegi: chi genera i log non puo modificarli
  [ ] Monitoraggio di tentativi di manomissione dei log
  [ ] Backup dei log in location separata

Conservazione:
  [ ] Retention policy documentata per ogni tipo di log
  [ ] Retention conforme ai requisiti normativi (minimo 12 mesi per PCI-DSS)
  [ ] Cancellazione automatica dopo la scadenza della retention
  [ ] Archiviazione a lungo termine per log richiesti da normative specifiche

Monitoraggio:
  [ ] Alert automatici per eventi critici (accessi non autorizzati, escalation)
  [ ] Dashboard di compliance con metriche in tempo reale
  [ ] Correlazione tra log di diverse fonti (SIEM)
  [ ] Revisione periodica dei log da parte del security team
  [ ] Integrazione con il processo di incident response

Accesso:
  [ ] Accesso ai log limitato al personale autorizzato
  [ ] Log degli accessi ai log stessi (meta-logging)
  [ ] Auditor esterni possono accedere ai log in modalita read-only
  [ ] I log non contengono dati sensibili in chiaro (mascheramento/tokenizzazione)
```

### Matrice di Compliance per Audit Logging

La seguente matrice mappa i requisiti di logging di ciascuna normativa ai controlli tecnici:

| Requisito | GDPR | PCI-DSS | ISO 27001 | SOC 2 | NIS2 | DORA | HIPAA |
|-----------|------|---------|-----------|-------|------|------|-------|
| Log accessi utente | Art. 5(1)(f) | Req. 10.2.1 | A.8.15 | CC6.1 | Art. 21 | Art. 12 | §164.312(b) |
| Log accessi privilegiati | Art. 5(2) | Req. 10.2.2 | A.8.15 | CC6.3 | Art. 21 | Art. 12 | §164.312(b) |
| Log modifiche configurazione | - | Req. 10.2.7 | A.8.15 | CC8.1 | Art. 21 | Art. 12 | §164.312(c) |
| Log accessi dati sensibili | Art. 30 | Req. 10.2.1 | A.8.16 | CC6.1 | - | Art. 12 | §164.312(b) |
| Timestamp sincronizzato | - | Req. 10.6 | A.8.17 | CC7.2 | - | Art. 12 | - |
| Immutabilita log | - | Req. 10.3.3 | A.8.15 | CC7.2 | Art. 21 | Art. 12 | §164.312(c) |
| Retention minimo | Variabile | 12 mesi | Policy | Periodo audit | ACN | Autorita | 6 anni |
| Monitoraggio anomalie | - | Req. 10.4 | A.8.16 | CC7.2 | Art. 21 | Art. 10 | §164.312(b) |
| Revisione periodica | Art. 5(2) | Req. 10.4.1 | A.9.3 | CC4.1 | Art. 21 | Art. 13 | §164.308(a)(1) |

---

## 17. Best Practices

### Struttura del Programma di Compliance

Un programma di compliance efficace richiede una struttura organizzata:

```
Compliance Program Structure:

1. Governance
   - Compliance committee con rappresentanza cross-funzionale
   - Charter che definisce mandato, autorita e responsabilita
   - Reporting line diretta al board/top management
   - Budget dedicato e risorse adeguate

2. Regulatory Inventory
   - Catalogo di tutte le normative applicabili
   - Mapping dei requisiti per sistema/processo
   - Monitoraggio delle evoluzioni normative
   - Impact assessment per nuove normative

3. Control Framework
   - Unified control framework (UCF) che mappa i controlli a piu standard
   - Evita duplicazione: un controllo, multiple mappature
   - Esempio: il controllo "MFA per accessi privilegiati" mappa a:
     - ISO 27001 A.8.5
     - SOC 2 CC6.1
     - PCI DSS 8.4
     - NIS2 art. 21(2)(j)

4. Assessment Calendar
   - Pianificazione annuale di audit e assessment
   - Coordinamento con le scadenze di certificazione
   - Risk-based prioritizzazione delle aree da verificare

5. Remediation Program
   - Processo strutturato per gestire i finding
   - SLA per la remediation basati sulla severita
   - Escalation path per ritardi
   - Tracking centralizzato
```

### Top-Down Support

Il supporto del top management e il fattore critico di successo per qualsiasi programma di compliance:

- Il CEO/board deve comunicare l'importanza della compliance
- Budget adeguato deve essere allocato e protetto
- La compliance non deve essere vista come un ostacolo ma come un enabler del business
- I KPI di compliance devono essere inclusi nei report al board
- Le violazioni devono avere conseguenze reali e visibili

### Integrazione con SDLC

La compliance deve essere integrata nel ciclo di sviluppo software, non aggiunta dopo:

```
Requirements Phase:
  - Identificare i requisiti di compliance applicabili
  - Includere requisiti di sicurezza e privacy nel backlog
  - Documentare le basi giuridiche per il trattamento dati

Design Phase:
  - Privacy by Design e Security by Design
  - Threat modeling
  - DPIA per nuove funzionalita con impatto privacy
  - Architettura conforme (es. data residency, encryption)

Development Phase:
  - Secure coding standards
  - Static Application Security Testing (SAST) nella CI/CD
  - Dependency scanning per vulnerabilita note
  - Policy as Code per validare le configurazioni

Testing Phase:
  - Dynamic Application Security Testing (DAST)
  - Penetration testing per release critiche
  - Verifica dei controlli di accesso
  - Test di data handling (minimizzazione, retention)

Deployment Phase:
  - Infrastructure compliance scanning pre-deploy
  - Change management formale
  - Configuration validation
  - Evidence collection automatica

Operations Phase:
  - Continuous compliance monitoring
  - Incident response readiness
  - Log retention e audit trail
  - Periodic access reviews
```

### Training e Awareness

Il personale e il primo livello di difesa e la prima fonte di rischio:

| Tipo di Formazione | Destinatari | Frequenza | Contenuto |
|-------------------|-------------|-----------|-----------|
| **Security Awareness** | Tutti i dipendenti | Annuale + onboarding | Phishing, password, social engineering, policy aziendali |
| **GDPR/Privacy** | Tutti coloro che trattano dati personali | Annuale | Principi GDPR, diritti degli interessati, data breach |
| **Secure Development** | Sviluppatori | Semestrale | OWASP Top 10, secure coding, code review |
| **Compliance Specifico** | Team in scope per standard specifici | Prima della certificazione | Requisiti dello standard, ruoli, evidenze |
| **Incident Response** | Team IR, management | Trimestrale (tabletop) | Procedure IR, escalation, comunicazione |
| **Role-Based** | Ruoli specifici (DPO, admin, auditor) | Come necessario | Competenze specifiche del ruolo |

### Vendor Management

La gestione dei fornitori e un requisito trasversale a tutti gli standard:

```
Processo di Vendor Management per Compliance:

1. Due Diligence Pre-Contratto
   - Questionario di sicurezza (SIG, CAIQ, personalizzato)
   - Verifica certificazioni (ISO 27001, SOC 2)
   - Valutazione del rischio del fornitore
   - Review delle policy di sicurezza del fornitore

2. Requisiti Contrattuali
   - Clausole di sicurezza e compliance
   - Data Processing Agreement (DPA) per GDPR
   - Diritto di audit
   - Obblighi di notifica incidenti
   - SLA di sicurezza
   - Clausole di uscita e restituzione/distruzione dati

3. Monitoraggio Continuo
   - Verifica periodica della conformita (annuale minimo)
   - Monitoraggio delle certificazioni (scadenze, revoche)
   - Review dei report di audit (SOC 2, pentest)
   - Monitoraggio delle vulnerabilita dei prodotti del fornitore

4. Classificazione dei Fornitori
   - Critico: accesso a dati sensibili o sistemi critici
   - Importante: accesso a sistemi ma non a dati sensibili
   - Standard: nessun accesso a sistemi o dati critici

5. Off-boarding
   - Revoca accessi
   - Restituzione o distruzione dei dati
   - Conferma scritta della distruzione
   - Aggiornamento del registro fornitori
```

### Continuous Monitoring

Il monitoraggio continuo e essenziale per mantenere la compliance nel tempo:

```
Elementi del Continuous Compliance Monitoring:

Tecnico:
  - Scansione automatica delle configurazioni (AWS Config, Azure Policy)
  - Vulnerability scanning continuo (non solo trimestrale)
  - Monitoraggio degli accessi e delle anomalie (SIEM/SOAR)
  - Infrastructure compliance scanning post-deploy
  - Certificate e credential expiry monitoring

Organizzativo:
  - Dashboard di compliance con metriche in tempo reale
  - Alert automatici per deviazioni dalla baseline
  - Workflow di remediation con assegnazione automatica
  - Report periodici allo steering committee
  - Integrazione con il processo di change management

KPI:
  - Compliance score per standard/framework
  - Tempo medio di remediation dei finding
  - Percentuale di controlli automatizzati
  - Numero di finding aperti per severita
  - Trend di compliance nel tempo
```

### Compliance Metrics e KPI

| Metrica | Descrizione | Target |
|---------|-------------|--------|
| **Compliance Score** | Percentuale di controlli conformi | > 95% |
| **MTTR (Mean Time to Remediate)** | Tempo medio di risoluzione dei finding | Critico: < 7gg, Alto: < 30gg |
| **Open Findings** | Numero di finding aperti per severita | Critico: 0, Alto: < 5 |
| **Overdue Findings** | Finding oltre la scadenza di remediation | 0 |
| **Control Coverage** | Percentuale di controlli automatizzati | > 70% |
| **Evidence Freshness** | Percentuale di evidenze aggiornate | > 90% |
| **Training Completion** | Percentuale di personale formato | 100% |
| **Vendor Compliance** | Percentuale di fornitori critici valutati | 100% |
| **Policy Review** | Percentuale di policy aggiornate nell'ultimo anno | 100% |
| **Audit Finding Recurrence** | Percentuale di finding ricorrenti tra cicli di audit | < 5% |

### Regulatory Change Management

Il panorama normativo evolve costantemente e richiede un processo strutturato di gestione:

```
1. Monitoraggio
   - Sottoscrizione a newsletter di autorita (Garante, ACN, ENISA)
   - Partecipazione a gruppi di lavoro di settore
   - Consulenza legale specializzata
   - Monitoraggio delle pubblicazioni in Gazzetta Ufficiale e GUUE

2. Impact Assessment
   - Analisi dei nuovi requisiti rispetto ai controlli esistenti
   - Gap analysis tra stato attuale e nuovi requisiti
   - Stima dell'effort di adeguamento
   - Prioritizzazione basata su scadenze e sanzioni

3. Pianificazione
   - Roadmap di adeguamento con milestone
   - Allocazione budget e risorse
   - Comunicazione agli stakeholder
   - Aggiornamento del regulatory inventory

4. Implementazione
   - Aggiornamento policy e procedure
   - Implementazione nuovi controlli tecnici
   - Formazione del personale
   - Test e validazione

5. Verifica
   - Audit di conformita post-implementazione
   - Documentazione delle evidenze
   - Report al management
   - Aggiornamento del programma di compliance
```

### Incident Response Alignment

L'incident response deve essere allineato ai requisiti di compliance:

| Normativa | Termine Notifica | Destinatario | Contenuto Minimo |
|-----------|-----------------|--------------|------------------|
| **GDPR** | 72 ore | Garante Privacy | Natura violazione, interessati, misure adottate |
| **NIS2** | 24h (early warning), 72h (notifica), 1 mese (report) | CSIRT Italia (ACN) | Tipo incidente, impatto, misure mitigazione |
| **PCI-DSS** | Immediatamente | Acquirer, brand di pagamento | Dettaglio della compromissione, scope, remediation |
| **DORA** | 4 ore (classificazione), 72h (notifica intermedia), 1 mese (finale) | Autorita finanziaria competente | Classificazione, impatto, remediation |

La procedura di incident response deve includere:

- Checklist di notifica per ogni normativa applicabile
- Template precompilati per le comunicazioni alle autorita
- Matrice di escalation con i contatti delle autorita
- Processo di valutazione della severita allineato ai criteri normativi
- Simulazioni periodiche (tabletop exercise) che includano la componente di notifica

---

## Esercizi

### Esercizio 1 — Gap Analysis GDPR

Eseguire una gap analysis su un'applicazione web di esempio rispetto ai requisiti GDPR. Verificare: informativa privacy, base giuridica per ogni trattamento, gestione del consenso, diritto alla portabilita, diritto alla cancellazione, registro dei trattamenti. Documentare i gap trovati e proporre un piano di remediation con priorita.

### Esercizio 2 — Compliance-as-Code con OPA

Scrivere 5 policy OPA/Rego per un cluster Kubernetes: blocco container privilegiati, obbligo di resource limits, blocco immagini senza tag specifico, obbligo di label obbligatorie, restrizione namespace. Deployare Gatekeeper e verificare che i pod non conformi vengano rifiutati.

### Esercizio 3 — Audit Trail e Log Retention

Configurare un sistema di audit logging che registri: accessi ai dati personali, modifiche ai permessi, operazioni amministrative. Implementare una policy di retention (12 mesi) con archiviazione automatica e cancellazione sicura. Verificare l'immutabilita dei log con firma digitale o write-once storage.

### Esercizio 4 — NIS2 Incident Notification Simulation

Simulare un incidente di sicurezza che richieda notifica NIS2. Seguire la timeline: early warning entro 24 ore, notifica completa entro 72 ore, report finale entro 1 mese. Compilare i template di notifica per il CSIRT Italia e la relazione finale al management.

### Esercizio 5 — Data Classification e DPIA

Eseguire un Data Protection Impact Assessment (DPIA) per un nuovo sistema che processa dati biometrici. Classificare tutti i dati trattati per livello di sensibilita. Identificare i rischi, valutarne la probabilita e l'impatto, definire le misure di mitigazione. Documentare il risultato nel formato richiesto dal GDPR Art. 35.

### Esercizio 6 — DORA Register of Information

Compilare il registro delle informazioni richiesto dal DORA (Art. 28) per uno scenario simulato di un istituto finanziario che utilizza i seguenti fornitori ICT: un cloud provider (AWS o Azure), un SaaS di CRM, un provider di servizi di pagamento, un fornitore di servizi di posta elettronica e un provider di backup. Per ciascun fornitore, documentare: tipo di servizio, funzione aziendale supportata, classificazione della criticita, localizzazione dei dati, clausole contrattuali chiave, piano di uscita. Valutare quale fornitore potrebbe essere designato come CTPP e le implicazioni.

### Esercizio 7 — EU AI Act Risk Classification

Per un'organizzazione che utilizza i seguenti sistemi di IA, determinare la classificazione del rischio ai sensi dell'EU AI Act e gli obblighi corrispondenti: (a) un chatbot per il servizio clienti, (b) un sistema di screening automatico dei CV per il recruitment, (c) un sistema di credit scoring per la valutazione delle richieste di prestito, (d) un filtro anti-spam per le email, (e) un sistema di riconoscimento facciale per il controllo degli accessi fisici. Per ogni sistema, documentare la classificazione, gli obblighi applicabili, le azioni necessarie per la conformita e la timeline di adeguamento.

### Esercizio 8 — Data Residency Enforcement

Implementare una soluzione tecnica per garantire la data residency UE su un ambiente multi-cloud. Scrivere: (1) una Service Control Policy AWS che limiti il deployment alle regioni europee, (2) una Azure Policy che impedisca la creazione di risorse fuori dall'Europa, (3) una Kyverno ClusterPolicy che imponga label di data residency su tutti i workload Kubernetes. Testare ciascuna policy e documentare i risultati con evidenze (screenshot, log) utilizzabili in un audit.

### Esercizio 9 — Unified Control Framework

Costruire un Unified Control Framework (UCF) che mappi un singolo insieme di controlli a ISO 27001:2022, SOC 2, GDPR, PCI-DSS v4.0 e NIS2. Selezionare almeno 20 controlli (es. MFA, encryption at rest, vulnerability scanning, incident response, access review) e per ciascuno indicare il requisito corrispondente in ogni standard. Calcolare la percentuale di overlap tra gli standard e identificare i controlli specifici per un solo standard.

### Esercizio 10 — SOC 2 Automation Pipeline

Progettare e implementare una pipeline di raccolta automatica delle evidenze per un audit SOC 2 Type II. La pipeline deve raccogliere automaticamente: (1) stato di conformita delle AWS Config Rules, (2) report IAM credential con account non utilizzati, (3) risultati di vulnerability scan con Prowler, (4) stato di cifratura di tutti gli storage (S3, EBS, RDS). Ogni evidenza deve essere firmata con hash SHA-256 e conservata in storage immutabile con Object Lock. Documentare il processo e i risultati come se fosse un'evidenza di audit reale.

---

## Letture e Riferimenti

### Documentazione ufficiale

- Regolamento UE 2016/679 (GDPR) — testo consolidato — <https://eur-lex.europa.eu/eli/reg/2016/679/oj> (consultato: 2026-05-24)
- Direttiva NIS2 2022/2555 — <https://eur-lex.europa.eu/eli/dir/2022/2555/oj> (consultato: 2026-05-24)
- Regolamento DORA 2022/2554 — <https://eur-lex.europa.eu/eli/reg/2022/2554/oj> (consultato: 2026-05-24)
- Open Policy Agent Documentation — <https://www.openpolicyagent.org/docs/latest/> (consultato: 2026-05-24)
- SOC 2 Overview (AICPA) — <https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2> (consultato: 2026-05-24)
- ISO/IEC 27001:2022 — <https://www.iso.org/standard/27001> (consultato: 2026-05-24)
- Garante per la Protezione dei Dati Personali — <https://www.garanteprivacy.it/> (consultato: 2026-05-24)
- EU AI Act — Regolamento UE 2024/1689 — <https://eur-lex.europa.eu/eli/reg/2024/1689/oj> (consultato: 2026-05-24)
- HIPAA Security Rule — HHS — <https://www.hhs.gov/hipaa/for-professionals/security/index.html> (consultato: 2026-05-24)
- Kyverno Documentation — <https://kyverno.io/docs/> (consultato: 2026-05-24)
- ENISA NIS2 Technical Guidance — <https://www.enisa.europa.eu/> (consultato: 2026-05-24)
- PCI DSS v4.0.1 — PCI Security Standards Council — <https://www.pcisecuritystandards.org/> (consultato: 2026-05-24)
- EU Data Act — Regolamento UE 2023/2854 — <https://eur-lex.europa.eu/eli/reg/2023/2854/oj> (consultato: 2026-05-24)

### Libri consigliati

- Calder A., *EU GDPR: A Pocket Guide*, IT Governance Publishing, 2020
- Czerny N., *Cloud Security and Compliance*, Packt, 2023
- Fennessy S., *Practical Cloud Security*, O'Reilly, 2019
- Haber M., *Cloud Attack Vectors*, Apress, 2022
- Kohnke A., Shoemaker D., *The Complete Guide to Cybersecurity Risks and Controls*, CRC Press, 2024

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con Compliance e Normative |
|--------|--------|--------------------------------------|
| [07](07-ci-cd.md) | CI/CD | Compliance gate nella pipeline, policy-as-code, audit dei deployment |
| [08](08-monitoring-observability.md) | Monitoring e Observability | Audit logging, log retention, immutabilita e integrita dei log |
| [11](11-database-management.md) | Database Management | GDPR data retention, anonimizzazione, encryption at rest |
| [13](13-sicurezza-piattaforme.md) | Sicurezza delle Piattaforme | Controlli tecnici mappati ai requisiti normativi, vulnerability management |
| [15](15-secrets-management.md) | Secrets Management | Gestione credenziali conforme, audit trail accessi ai secret |
| [21](21-finops-cost-governance.md) | FinOps e Cost Governance | Governance dei costi, tagging obbligatorio, budget policy |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **GDPR (General Data Protection Regulation)** | Regolamento UE 2016/679 sulla protezione dei dati personali dei cittadini europei |
| **NIS2** | Direttiva UE 2022/2555 sulla sicurezza delle reti e dei sistemi informativi, estende NIS1 |
| **DORA (Digital Operational Resilience Act)** | Regolamento UE 2022/2554 sulla resilienza operativa digitale per il settore finanziario |
| **SOC 2** | Framework di audit dell'AICPA che valuta i controlli di sicurezza, disponibilita e privacy |
| **ISO 27001** | Standard internazionale per i sistemi di gestione della sicurezza delle informazioni (ISMS) |
| **Compliance-as-code** | Pratica di codificare i requisiti normativi come policy automatiche verificabili nella pipeline |
| **OPA (Open Policy Agent)** | Motore di policy open source che consente di definire regole in linguaggio Rego |
| **DPIA (Data Protection Impact Assessment)** | Valutazione d'impatto sulla protezione dei dati richiesta dal GDPR per trattamenti ad alto rischio |
| **Data retention** | Policy che definisce per quanto tempo i dati vengono conservati prima della cancellazione o archiviazione |
| **Gap analysis** | Processo di confronto tra lo stato attuale e i requisiti normativi per identificare le carenze |
| **Audit trail** | Registrazione cronologica e immutabile delle attivita su un sistema per finalita di verifica |
| **PCI-DSS** | Standard di sicurezza per i dati delle carte di pagamento, obbligatorio per chi processa transazioni |
| **Garante Privacy** | Autorita italiana per la protezione dei dati personali, destinatario delle notifiche di data breach |
| **Early warning** | Prima notifica obbligatoria (entro 24 ore per NIS2) al CSIRT dopo un incidente significativo |
| **CTPP (Critical Third-Party Provider)** | Fornitore ICT designato come critico dalle ESA ai sensi del DORA, soggetto a supervisione diretta |
| **TLPT (Threat-Led Penetration Testing)** | Test di penetrazione basato su scenari di minaccia reali, obbligatorio ogni 3 anni per entita DORA significative |
| **TIBER-EU** | Framework europeo per i test di resilienza informatica basati su threat intelligence, adottato come base per il TLPT DORA |
| **EU AI Act** | Regolamento UE 2024/1689 sull'intelligenza artificiale, primo quadro normativo completo al mondo sui sistemi di IA |
| **GPAI (General-Purpose AI)** | Modello di IA per finalita generali, inclusi i large language models, soggetto a obblighi specifici dell'EU AI Act |
| **HIPAA** | Health Insurance Portability and Accountability Act, legge federale USA per la protezione delle informazioni sanitarie (PHI) |
| **ePHI** | Electronic Protected Health Information, informazioni sanitarie protette in formato elettronico ai sensi dell'HIPAA |
| **Data sovereignty** | Principio per cui i dati sono soggetti esclusivamente alle leggi della giurisdizione in cui risiedono |
| **EUCS** | European Cybersecurity Certification Scheme for Cloud Services, schema di certificazione UE per i servizi cloud |
| **Kyverno** | Motore di policy nativo per Kubernetes (CNCF Graduated) che utilizza YAML e CEL per definire regole di governance |
| **CEL (Common Expression Language)** | Linguaggio di espressioni leggero usato in Kubernetes e Kyverno per definire policy di validazione |
| **WORM (Write Once Read Many)** | Tecnologia di storage che consente la scrittura una sola volta e impedisce modifiche o cancellazioni |
| **UCF (Unified Control Framework)** | Framework che mappa un singolo insieme di controlli a piu standard normativi, riducendo la duplicazione |
| **SCC (Standard Contractual Clauses)** | Clausole contrattuali standard approvate dalla Commissione UE per i trasferimenti di dati extra-UE |
| **BCR (Binding Corporate Rules)** | Regole vincolanti d'impresa per il trasferimento di dati personali all'interno di un gruppo multinazionale |
| **US CLOUD Act** | Clarifying Lawful Overseas Use of Data Act (2018), legge USA che consente alle autorita di richiedere dati conservati all'estero |
| **Conftest** | Strumento open source per testare configurazioni strutturate (Kubernetes, Terraform, Dockerfile) contro policy OPA/Rego |
| **Checkov** | Scanner open source per Infrastructure-as-Code che verifica la conformita a best practice di sicurezza e compliance |
| **ASV (Approved Scanning Vendor)** | Vendor approvato dal PCI SSC per eseguire scansioni trimestrali di vulnerabilita esterne per la conformita PCI-DSS |
