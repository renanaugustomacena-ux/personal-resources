# Pianificazione e Reportistica IT — Guida Completa

> **Modulo 10** · **Tempo:** 60 min · **Aggiornamento:** 2026-04-27

## Idee guida

1. **KPI = numeri actionable, non vanity metrics.** Uptime 99.9% deve attivare azioni.
2. **Report mensile a stakeholder: 1 pagina max.** Executive summary.
3. **Forecasting capacity: trend analysis 3-6 mesi.**
4. **Report automatici > manual.** Cost-effective + consistente.


## Indice

1. [Panoramica](#panoramica)
2. [Pianificazione Upgrade e Migrazione](#pianificazione-upgrade-e-migrazione)
   - [Hardware Refresh Planning](#hardware-refresh-planning)
   - [Software Migration Planning](#software-migration-planning)
   - [Infrastructure Evolution](#infrastructure-evolution)
3. [Capacity Planning](#capacity-planning)
   - [Metodologia](#metodologia)
   - [Metriche per Capacity Planning](#metriche-per-capacity-planning)
   - [Strumenti e Automazione](#strumenti-e-automazione)
4. [Report Mensile IT](#report-mensile-it)
   - [Template Report Mensile](#template-report-mensile)
   - [KPI Dashboard](#kpi-dashboard)
   - [Creazione Dashboard](#creazione-dashboard)
5. [Budget IT](#budget-it)
   - [Budget Planning](#budget-planning)
   - [TCO Calculation](#tco-calculation)
   - [Cost Optimization](#cost-optimization)
6. [Roadmap Tecnologica](#roadmap-tecnologica)
   - [Technology Roadmap Creation](#technology-roadmap-creation)
   - [Example 3-Year Roadmap](#example-3-year-roadmap)
7. [Comunicazione e Stakeholder Management](#comunicazione-e-stakeholder-management)
8. [Finestre di Manutenzione e Calendario Change](#finestre-di-manutenzione-e-calendario-change)
   - [Tipologie di Finestre di Manutenzione](#tipologie-di-finestre-di-manutenzione)
   - [Calendario Change e Collision Detection](#calendario-change-e-collision-detection)
   - [Blackout Window e Freeze Period](#blackout-window-e-freeze-period)
   - [Comunicazione delle Manutenzioni Programmate](#comunicazione-delle-manutenzioni-programmate)
9. [SLA Reporting Avanzato](#sla-reporting-avanzato)
   - [Struttura di un SLA Report](#struttura-di-un-sla-report)
   - [Analisi delle Violazioni SLA](#analisi-delle-violazioni-sla)
   - [OLA e Underpinning Contracts](#ola-e-underpinning-contracts)
   - [SLA Reporting Automatizzato](#sla-reporting-automatizzato)
10. [Strumenti ITSM per la Reportistica](#strumenti-itsm-per-la-reportistica)
    - [ServiceNow Reporting](#servicenow-reporting)
    - [Jira Service Management Reporting](#jira-service-management-reporting)
    - [Confronto Strumenti ITSM](#confronto-strumenti-itsm)
    - [Integrazione Multi-Strumento](#integrazione-multi-strumento)
11. [FinOps e Reportistica Costi Cloud](#finops-e-reportistica-costi-cloud)
    - [Framework FinOps](#framework-finops)
    - [Dashboard dei Costi Cloud](#dashboard-dei-costi-cloud)
    - [Reportistica FinOps Mensile](#reportistica-finops-mensile)
    - [Anomaly Detection sui Costi](#anomaly-detection-sui-costi)
12. [Alerting e Notifiche Automatizzate](#alerting-e-notifiche-automatizzate)
    - [Architettura di Alerting](#architettura-di-alerting)
    - [Regole di Alerting con Prometheus](#regole-di-alerting-con-prometheus)
    - [Escalation Automatica](#escalation-automatica)
    - [Riduzione del Rumore di Alerting](#riduzione-del-rumore-di-alerting)
13. [Miglioramento Continuo della Reportistica](#miglioramento-continuo-della-reportistica)
    - [Modello ITIL 4 di Continual Improvement](#modello-itil-4-di-continual-improvement)
    - [Maturita della Reportistica IT](#maturita-della-reportistica-it)
    - [Ciclo di Revisione dei KPI](#ciclo-di-revisione-dei-kpi)
14. [Reportistica di Sicurezza IT](#reportistica-di-sicurezza-it)
    - [Security Posture Report](#security-posture-report)
    - [Vulnerability Management Reporting](#vulnerability-management-reporting)
    - [Compliance e Audit Reporting](#compliance-e-audit-reporting)
15. [Framework di Governance della Reportistica](#framework-di-governance-della-reportistica)
    - [Data Governance per i Report IT](#data-governance-per-i-report-it)
    - [Catalogo dei Report](#catalogo-dei-report)
    - [Revisione e Ciclo di Vita dei Report](#revisione-e-ciclo-di-vita-dei-report)
16. [Best Practices](#best-practices)
17. [Troubleshooting](#troubleshooting)

---

## Panoramica

La pianificazione strategica e la reportistica operativa rappresentano i pilastri fondamentali di una gestione IT matura e orientata ai risultati. Senza una pianificazione strutturata, i team IT operano in modalità reattiva, affrontando emergenze continue senza una visione chiara delle priorita e delle risorse necessarie. Senza una reportistica efficace, i risultati del lavoro IT restano invisibili al management e agli stakeholder aziendali, rendendo difficile giustificare investimenti e dimostrare il valore generato.

Questa guida copre l'intero ciclo di pianificazione e reportistica per la manutenzione IT:

- **Pianificazione degli upgrade e delle migrazioni**: come programmare l'evoluzione dell'infrastruttura hardware e software in modo ordinato, minimizzando i rischi e i tempi di inattivita.
- **Capacity planning**: come prevedere le necessita future di risorse computazionali, storage e rete, evitando sia il sovradimensionamento (spreco di budget) che il sottodimensionamento (degradazione delle prestazioni).
- **Reportistica mensile**: come costruire report efficaci che comunicano lo stato di salute dell'infrastruttura IT ai diversi livelli aziendali.
- **Budget IT**: come pianificare, gestire e ottimizzare la spesa per la manutenzione IT, distinguendo tra CAPEX e OPEX.
- **Roadmap tecnologica**: come definire una visione a medio-lungo termine dell'evoluzione tecnologica dell'organizzazione.
- **Comunicazione con gli stakeholder**: come tradurre metriche tecniche in informazioni di valore per il business.

L'obiettivo finale e trasformare la funzione IT da centro di costo a partner strategico del business, attraverso una pianificazione proattiva, una misurazione rigorosa e una comunicazione trasparente.

---

## Pianificazione Upgrade e Migrazione

### Hardware Refresh Planning

La pianificazione del rinnovo hardware e un processo critico che richiede un approccio metodico e anticipato. Un hardware obsoleto non solo genera rischi di guasto e downtime, ma comporta costi crescenti di manutenzione, vulnerabilita di sicurezza (fine del supporto firmware) e incompatibilita con il software moderno.

#### Assessment dell'Hardware Attuale

Il primo passo e creare un inventario completo e dettagliato di tutto l'hardware in produzione. Per ogni asset, registrare:

| Campo                  | Descrizione                                      | Esempio                    |
|------------------------|--------------------------------------------------|----------------------------|
| Asset ID               | Identificativo univoco                           | SRV-PROD-042              |
| Tipo                   | Server, switch, firewall, storage, UPS, ecc.     | Server rack 2U             |
| Produttore e modello   | Marca e modello specifico                        | Dell PowerEdge R750        |
| Data di acquisto       | Quando e stato acquistato                        | 2021-03-15                 |
| Data EOL (End of Life) | Fine della vendita da parte del produttore       | 2026-06-30                 |
| Data EOS (End of Support)| Fine del supporto tecnico e delle patch        | 2028-06-30                 |
| Garanzia attiva        | Tipo e scadenza della garanzia                   | ProSupport fino a 2026-03  |
| Utilizzo attuale       | Percentuale di utilizzo medio CPU/RAM/disco      | CPU 65%, RAM 78%, Disco 55%|
| Criticita              | Impatto in caso di guasto (Alta/Media/Bassa)     | Alta                       |
| Stato fisico           | Condizione fisica del dispositivo                | Buono, nessun allarme      |

#### Tracciamento Timeline EOL/EOS

Creare una timeline visiva che mostri le date EOL e EOS di ogni componente critico dell'infrastruttura. Questo consente di pianificare i rinnovi con almeno 6-12 mesi di anticipo:

```
Timeline EOL/EOS — Esempio

2026 Q1  [████] Switch core Cisco 9300 — EOL
2026 Q2  [████] Server Dell R740 (batch 2020) — EOS
2026 Q3  [████] Firewall Fortinet 200F — EOL
2027 Q1  [████] Storage NetApp FAS2750 — EOS
2027 Q2  [████] UPS APC Smart-UPS 3000 — Fine garanzia
2027 Q4  [████] Server Dell R750 (batch 2021) — EOL
```

#### Stima del Budget per il Refresh

Per ogni ciclo di refresh, preparare una stima dettagliata che includa:

- **Costo hardware**: prezzo di acquisto del nuovo equipaggiamento, inclusi accessori e componenti aggiuntivi (RAM extra, dischi, licenze firmware).
- **Costo di migrazione**: ore-uomo necessarie per la configurazione, il test e la messa in produzione.
- **Costo di smaltimento**: dismissione e smaltimento certificato dell'hardware obsoleto (RAEE).
- **Costi indiretti**: eventuale downtime pianificato, costi di formazione su nuove piattaforme.

Esempio di stima per un refresh di 5 server:

```
Voce                                  Costo unitario    Quantita    Totale
-----------------------------------------------------------------------
Server Dell PowerEdge R760            EUR 12.500         5          EUR 62.500
RAM aggiuntiva (64 GB per server)     EUR 800            5          EUR 4.000
Dischi SSD NVMe (2 x 1.92 TB)        EUR 1.200          5          EUR 6.000
Licenze firmware iDRAC Enterprise     EUR 300            5          EUR 1.500
Cablaggio e accessori                 EUR 200            5          EUR 1.000
Manodopera migrazione (40h/server)    EUR 80/h           200h       EUR 16.000
Smaltimento RAEE certificato          EUR 150            5          EUR 750
-----------------------------------------------------------------------
TOTALE STIMATO                                                      EUR 91.750
Contingency (10%)                                                   EUR 9.175
-----------------------------------------------------------------------
BUDGET RICHIESTO                                                    EUR 100.925
```

#### Piano di Migrazione e Timeline

Ogni refresh hardware deve seguire un piano di migrazione strutturato:

1. **Fase di preparazione (settimane 1-2)**: ordine e ricezione hardware, configurazione rack, cablaggio, installazione sistema operativo base.
2. **Fase di configurazione (settimane 3-4)**: installazione e configurazione servizi, replica dati, configurazione monitoring.
3. **Fase di test (settimana 5)**: test funzionali, test di carico, test di failover, validazione backup.
4. **Fase di migrazione (settimana 6)**: migrazione dei carichi di lavoro in produzione, durante la finestra di manutenzione concordata.
5. **Fase di validazione (settimana 7)**: monitoraggio intensivo, verifica prestazioni, conferma stabilita.
6. **Fase di decommissioning (settimana 8)**: dismissione dell'hardware vecchio, aggiornamento documentazione, chiusura progetto.

#### Valutazione dei Rischi

Per ogni progetto di refresh, compilare una matrice dei rischi:

| Rischio                              | Probabilita | Impatto | Mitigazione                                  |
|--------------------------------------|-------------|---------|----------------------------------------------|
| Ritardo nella consegna hardware      | Media       | Alto    | Ordinare con 8 settimane di anticipo         |
| Incompatibilita applicativa          | Bassa       | Alto    | Test in ambiente di staging completo          |
| Perdita dati durante migrazione      | Bassa       | Critico | Backup completo pre-migrazione + verifica     |
| Downtime prolungato                  | Media       | Alto    | Piano di rollback testato, finestra ampia     |
| Competenze insufficienti del team    | Media       | Medio   | Formazione anticipata, supporto vendor         |

#### Piano di Rollback

Ogni migrazione hardware deve prevedere un piano di rollback documentato e testato:

- Mantenere l'hardware vecchio operativo e raggiungibile per almeno 2 settimane dopo la migrazione.
- Documentare i passaggi esatti per ripristinare il servizio sull'hardware precedente.
- Definire i criteri di attivazione del rollback (es. errori critici entro le prime 48 ore).
- Assegnare un responsabile della decisione di rollback (tipicamente il Change Manager o il responsabile IT).

---

### Software Migration Planning

La migrazione software e un processo che richiede ancora piu attenzione del refresh hardware, poiche coinvolge dipendenze applicative, compatibilita, licenze e formazione degli utenti.

#### Valutazione della Versione e Compatibilita

Prima di qualsiasi upgrade software, condurre un assessment completo:

- **Versione attuale e versione target**: documentare le differenze principali (changelog, breaking changes, nuove funzionalita).
- **Matrice di compatibilita**: verificare la compatibilita con tutti i componenti collegati (database, middleware, client, integrazioni).
- **Requisiti di sistema**: confrontare i requisiti hardware/software della nuova versione con l'infrastruttura attuale.
- **Licenze**: verificare che le licenze attuali coprano la nuova versione o calcolare il costo di upgrade.

#### Test di Compatibilita

Costruire un ambiente di test che replichi fedelmente la produzione:

1. Clonare la configurazione di produzione nell'ambiente di staging.
2. Eseguire l'upgrade nell'ambiente di test.
3. Eseguire una batteria di test completa:
   - Test funzionali (tutte le funzionalita principali).
   - Test di integrazione (connessioni con altri sistemi).
   - Test di prestazioni (benchmark prima e dopo).
   - Test di sicurezza (scansione vulnerabilita della nuova versione).
4. Documentare tutti i problemi riscontrati e le soluzioni applicate.

#### Deployment con Gruppo Pilota

Dopo il successo dei test in staging, procedere con un deployment pilota:

- Selezionare un gruppo pilota rappresentativo (10-20% degli utenti o dei server).
- Monitorare intensivamente durante il periodo pilota (minimo 1 settimana).
- Raccogliere feedback strutturato dal gruppo pilota.
- Risolvere eventuali problemi emersi prima del rollout completo.

#### Requisiti di Formazione

Valutare e pianificare la formazione necessaria:

- **Team IT**: formazione tecnica sulla nuova versione (amministrazione, troubleshooting, nuove funzionalita).
- **Utenti finali**: formazione sulle modifiche dell'interfaccia o dei flussi di lavoro.
- **Documentazione**: aggiornamento di tutte le procedure operative e dei runbook.

#### Esempio: Piano di Migrazione Windows Server 2019 a 2025

```
PIANO DI MIGRAZIONE — Windows Server 2019 → 2025
=================================================

FASE 1 — Assessment e Preparazione (Mese 1-2)
  - Inventario completo server Windows Server 2019 (42 server)
  - Verifica compatibilita applicazioni (SAP, SQL Server, IIS, AD)
  - Verifica compatibilita driver e firmware hardware
  - Acquisto licenze Windows Server 2025 Datacenter
  - Preparazione ambiente di test con 3 server rappresentativi
  - Formazione team IT su Windows Server 2025

FASE 2 — Test in Staging (Mese 3)
  - Upgrade dei 3 server di test
  - Test Active Directory (replica, Group Policy, DNS)
  - Test SQL Server su Windows Server 2025
  - Test applicazioni web (IIS, .NET)
  - Test Hyper-V (se applicabile)
  - Benchmark prestazionali
  - Documentazione problemi e soluzioni

FASE 3 — Pilota in Produzione (Mese 4)
  - Upgrade di 5 server non critici
  - Monitoraggio intensivo per 2 settimane
  - Verifica backup e restore
  - Raccolta feedback team operativo

FASE 4 — Rollout Produzione (Mese 5-7)
  - Batch 1 (Mese 5): 12 server — file server, print server, utility
  - Batch 2 (Mese 6): 15 server — application server, web server
  - Batch 3 (Mese 7): 10 server — database server, domain controller
  - Ogni batch include: backup pre-migrazione, upgrade, test, validazione

FASE 5 — Validazione e Chiusura (Mese 8)
  - Verifica completa di tutti i 42 server
  - Decommissioning licenze Windows Server 2019
  - Aggiornamento documentazione
  - Lesson learned e chiusura progetto

CRITERI DI ROLLBACK:
  - Errore critico non risolvibile entro 4 ore
  - Perdita di funzionalita business-critical
  - Degradazione prestazionale superiore al 20%
  - Procedura: restore da backup immagine pre-migrazione (testato)
```

---

### Infrastructure Evolution

#### Cloud Migration Assessment

La valutazione per una migrazione cloud deve considerare molteplici fattori:

**Criteri di valutazione per ogni workload:**

| Criterio                     | On-Premise preferibile          | Cloud preferibile                  |
|------------------------------|----------------------------------|------------------------------------|
| Variabilita del carico       | Costante e prevedibile          | Variabile, picchi stagionali       |
| Requisiti di latenza         | Ultra-bassa latenza richiesta   | Latenza standard accettabile       |
| Requisiti normativi          | Dati che devono restare in sede | Nessun vincolo di residenza dati   |
| Costo a lungo termine        | Ammortamento gia in corso       | Hardware da rinnovare              |
| Necessita di scalabilita     | Crescita lenta e prevedibile    | Crescita rapida o imprevedibile    |
| Competenze del team          | Forti competenze on-premise     | Competenze cloud disponibili       |

**Modelli di migrazione (le 6R):**
- **Rehost** (Lift & Shift): migrazione diretta senza modifiche.
- **Replatform**: migrazione con ottimizzazioni minime (es. database gestito).
- **Refactor**: riscrittura per sfruttare servizi cloud-native.
- **Repurchase**: sostituzione con SaaS equivalente.
- **Retain**: mantenere on-premise (non adatto al cloud).
- **Retire**: dismettere il workload (non piu necessario).

#### Pianificazione Infrastruttura Ibrida

Per la maggior parte delle organizzazioni, l'infrastruttura ibrida rappresenta la scelta piu realistica. Pianificare considerando:

- **Connettivita**: VPN site-to-site o connessione dedicata (ExpressRoute, Direct Connect) verso il cloud provider.
- **Identity management**: integrazione Active Directory con Azure AD o equivalente.
- **Networking**: progettazione della rete ibrida (IP addressing, routing, DNS).
- **Gestione unificata**: strumenti di monitoring e management che coprano sia on-premise che cloud.
- **Backup e DR**: strategia di backup e disaster recovery che sfrutti entrambi gli ambienti.

#### Framework di Valutazione Vendor

Quando si valutano vendor e tecnologie, utilizzare un framework strutturato:

| Criterio              | Peso | Vendor A | Vendor B | Vendor C |
|-----------------------|------|----------|----------|----------|
| Costo TCO 3 anni     | 25%  |    8     |    7     |    9     |
| Funzionalita          | 20%  |    9     |    8     |    7     |
| Supporto e SLA        | 15%  |    7     |    9     |    8     |
| Integrazione          | 15%  |    8     |    7     |    8     |
| Sicurezza             | 10%  |    9     |    8     |    9     |
| Scalabilita           | 10%  |    7     |    9     |    8     |
| Riferimenti/Reputazione| 5%  |    8     |    8     |    7     |
| **Punteggio ponderato**|**100%**| **8.05** | **7.85** | **8.10** |

Ogni criterio viene valutato da 1 a 10, poi moltiplicato per il peso. Il vendor con il punteggio ponderato piu alto risulta il preferito, ma la decisione finale deve considerare anche fattori qualitativi.

---

## Capacity Planning

### Metodologia

Il capacity planning e il processo di determinazione delle risorse IT necessarie per soddisfare le esigenze attuali e future dell'organizzazione. Una metodologia efficace segue cinque fasi cicliche:

**Fase 1 — Raccolta dati di utilizzo attuale**

Raccogliere dati storici di utilizzo per un periodo significativo (minimo 3 mesi, idealmente 12 mesi per catturare la stagionalita):

- Esportare dati dal sistema di monitoring (Zabbix, Prometheus, Datadog, ecc.).
- Calcolare medie, mediane, percentili (P95, P99) e valori di picco.
- Identificare pattern ricorrenti (picchi giornalieri, settimanali, mensili, stagionali).

**Fase 2 — Identificazione dei trend di crescita**

Analizzare i dati storici per identificare i trend:

- Crescita lineare: aumento costante nel tempo (es. +5 GB di storage al mese).
- Crescita esponenziale: accelerazione della crescita (es. raddoppio utenti ogni 6 mesi).
- Crescita a gradini: aumenti improvvisi in corrispondenza di eventi (lancio prodotto, acquisizioni).

**Fase 3 — Previsione delle necessita future**

Utilizzare i trend identificati per proiettare le necessita future, considerando anche:

- Piani di crescita aziendale (nuovi prodotti, nuovi mercati, nuove sedi).
- Progetti IT pianificati (nuove applicazioni, migrazioni).
- Cambiamenti normativi (requisiti di retention dati, compliance).

**Fase 4 — Pianificazione dell'approvvigionamento o dello scaling**

Sulla base delle previsioni, pianificare:

- **On-premise**: ordini di acquisto hardware con tempistiche adeguate (lead time 4-12 settimane).
- **Cloud**: configurazione di auto-scaling, reserved instances, o upgrade dei tier di servizio.
- **Ibrido**: decisione su dove allocare la crescita (on-premise vs cloud).

**Fase 5 — Revisione e aggiustamento**

Il capacity planning non e un esercizio una tantum. Rivedere le previsioni trimestralmente:

- Confrontare le previsioni con i dati reali.
- Aggiustare i modelli in base alle deviazioni.
- Aggiornare le previsioni con nuove informazioni aziendali.

---

### Metriche per Capacity Planning

#### Compute (Calcolo)

| Metrica                  | Descrizione                                    | Soglia di attenzione | Soglia critica |
|--------------------------|------------------------------------------------|---------------------|----------------|
| CPU Utilization %        | Percentuale media di utilizzo CPU              | > 70%               | > 85%         |
| CPU Utilization P95      | 95esimo percentile utilizzo CPU                | > 80%               | > 90%         |
| Memory Utilization %     | Percentuale di RAM utilizzata                  | > 75%               | > 90%         |
| VM Density               | Numero di VM per host fisico                   | > 80% capacita      | > 90% capacita|
| CPU Ready Time           | Tempo di attesa della vCPU per la pCPU         | > 5%                | > 10%         |

#### Storage

| Metrica                  | Descrizione                                    | Soglia di attenzione | Soglia critica |
|--------------------------|------------------------------------------------|---------------------|----------------|
| Capacita utilizzata %    | Spazio disco utilizzato vs totale              | > 75%               | > 85%         |
| Tasso di crescita        | GB/TB aggiunti per mese                        | Trend in accelerazione| Saturazione < 6 mesi|
| IOPS Utilization         | Operazioni I/O vs capacita massima             | > 70%               | > 85%         |
| Latenza I/O              | Tempo di risposta delle operazioni disco       | > 5 ms              | > 15 ms       |
| Throughput               | MB/s di lettura/scrittura vs massimo           | > 70%               | > 85%         |

#### Network (Rete)

| Metrica                  | Descrizione                                    | Soglia di attenzione | Soglia critica |
|--------------------------|------------------------------------------------|---------------------|----------------|
| Bandwidth Utilization %  | Utilizzo banda vs capacita del link            | > 60%               | > 80%         |
| Port Density             | Porte switch utilizzate vs disponibili         | > 80%               | > 90%         |
| Packet Loss              | Percentuale di pacchetti persi                 | > 0.1%              | > 1%          |
| Latenza                  | Round-trip time tra nodi critici               | Aumento trend        | > SLA          |

#### Licenze

| Metrica                  | Descrizione                                    | Soglia di attenzione | Soglia critica |
|--------------------------|------------------------------------------------|---------------------|----------------|
| Seats utilizzati %       | Licenze in uso vs acquistate                   | > 80%               | > 95%         |
| Trend di consumo         | Velocita di consumo delle licenze disponibili  | Esaurimento < 3 mesi| Esaurimento < 1 mese|
| Licenze inutilizzate     | Licenze assegnate ma non utilizzate (> 90gg)   | > 10%               | > 20% (spreco)|

---

### Strumenti e Automazione

#### Dati di Monitoring per i Trend di Capacita

I sistemi di monitoring sono la fonte primaria di dati per il capacity planning. Configurare:

- **Prometheus + Grafana**: query PromQL per estrarre trend di lungo periodo.
  ```promql
  # Trend utilizzo CPU medio ultimi 6 mesi (media giornaliera)
  avg_over_time(
    avg by (instance) (1 - rate(node_cpu_seconds_total{mode="idle"}[5m]))[6m:1d]
  )

  # Previsione spazio disco esaurito (linear prediction)
  predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[30d], 86400 * 90)
  ```

- **Zabbix**: utilizzare i report di trend e le funzioni di previsione integrate.
- **Datadog**: forecast monitors per previsioni automatiche su metriche chiave.

#### Modelli su Foglio di Calcolo

Per organizzazioni che non dispongono di strumenti avanzati, un modello Excel/Calc e un punto di partenza efficace:

```
Foglio: Capacity Planning — Storage

Colonna A: Mese
Colonna B: Capacita totale (TB)
Colonna C: Capacita utilizzata (TB)
Colonna D: % Utilizzo (=C/B)
Colonna E: Crescita mensile (TB) (=C[n] - C[n-1])
Colonna F: Media crescita ultimi 6 mesi (=MEDIA(E[n-5]:E[n]))
Colonna G: Mesi alla saturazione (=(B - C) / F)

Esempio:
Mese        Tot(TB)  Usato(TB)  %Util  Crescita  Media 6m  Mesi a sat.
2026-01     100      68         68%    1.2       1.05      30.5
2026-02     100      69.3       69%    1.3       1.08      28.4
2026-03     100      70.7       71%    1.4       1.13      25.9
...
```

**Formula di previsione lineare:**

```
Capacita necessaria al mese M = Capacita attuale + (Crescita media mensile x M)

Esempio:
  Capacita attuale: 70.7 TB
  Crescita media mensile: 1.13 TB/mese
  Previsione a 12 mesi: 70.7 + (1.13 x 12) = 84.3 TB
  Soglia di intervento (85%): 85 TB
  Tempo stimato al raggiungimento soglia: (85 - 70.7) / 1.13 = 12.7 mesi
```

#### Cloud Cost Calculator

Per workload cloud, utilizzare gli strumenti ufficiali dei provider:

- **AWS Pricing Calculator**: stima dei costi per istanze EC2, S3, RDS, ecc.
- **Azure Pricing Calculator**: stima per VM, Azure SQL, Blob Storage, ecc.
- **Google Cloud Pricing Calculator**: stima per Compute Engine, Cloud SQL, GCS, ecc.

Confrontare sempre il costo di reserved instances (1 anno, 3 anni) con il costo on-demand per workload stabili.

#### Strumenti di Right-Sizing

Il right-sizing consiste nell'adeguare le risorse assegnate all'utilizzo effettivo:

- **vRealize Operations** (VMware): raccomandazioni di right-sizing per VM.
- **AWS Compute Optimizer**: suggerimenti per istanze EC2 sovradimensionate.
- **Azure Advisor**: raccomandazioni di dimensionamento per VM Azure.
- **Kubecost** (Kubernetes): analisi dei costi e right-sizing per container.

---

## Report Mensile IT

### Template Report Mensile

Di seguito un template completo per il report mensile IT. Adattarlo alle esigenze specifiche dell'organizzazione.

```
================================================================
       REPORT MENSILE IT — [MESE] [ANNO]
================================================================

Preparato da: [Nome, Ruolo]
Data di emissione: [GG/MM/AAAA]
Periodo di riferimento: [01/MM/AAAA - 30/MM/AAAA]
Distribuzione: [CTO, IT Manager, CISO, CFO]

----------------------------------------------------------------
1. EXECUTIVE SUMMARY
----------------------------------------------------------------

Sintesi dello stato complessivo dell'infrastruttura IT nel mese
di riferimento. Evidenziare risultati positivi, criticita e azioni
in corso.

  Stato complessivo: [VERDE / GIALLO / ROSSO]

  Punti salienti:
  - [Risultato positivo 1]
  - [Risultato positivo 2]
  - [Criticita 1 e azione correttiva]
  - [Attivita completata rilevante]

----------------------------------------------------------------
2. METRICHE DI DISPONIBILITA (AVAILABILITY)
----------------------------------------------------------------

  Servizio              Target SLA    Disponibilita    Stato
  -----------------------------------------------------------
  Posta elettronica     99.9%         99.95%           OK
  ERP (SAP)             99.9%         99.87%           WARNING
  File Server           99.5%         99.98%           OK
  Sito web aziendale    99.9%         100.00%          OK
  VPN accesso remoto    99.5%         99.60%           OK
  Active Directory      99.99%        99.99%           OK
  Database produzione   99.9%         99.92%           OK

  Downtime totale non pianificato: 2h 15m
  Downtime pianificato (manutenzione): 4h 00m

----------------------------------------------------------------
3. RIEPILOGO INCIDENTI
----------------------------------------------------------------

  Incidenti totali:           42
  Per severita:
    - Critico (P1):           1
    - Alto (P2):              5
    - Medio (P3):             18
    - Basso (P4):             18

  MTTR (Mean Time To Resolve):
    - P1: 45 minuti (target: < 60 min)       OK
    - P2: 2h 10m (target: < 4h)              OK
    - P3: 6h 30m (target: < 8h)              OK
    - P4: 18h (target: < 24h)                OK

  MTTA (Mean Time To Acknowledge):
    - P1: 3 minuti (target: < 5 min)         OK
    - P2: 12 minuti (target: < 15 min)       OK

  Incidenti ricorrenti:
    - Timeout connessione database (3 occorrenze) — Root cause
      identificata: pool connessioni insufficiente. Fix in corso.

----------------------------------------------------------------
4. CHANGE MANAGEMENT
----------------------------------------------------------------

  Change totali implementati:   15
  Change riusciti:              14 (93.3%)
  Change falliti / rollback:    1 (6.7%)
  Change di emergenza:          2

  Dettaglio change fallito:
    - CHG-2026-0342: Upgrade firmware switch core.
      Causa: incompatibilita con modulo SFP+.
      Impatto: rollback completato in 20 minuti, nessun impatto
      su servizi.
      Azione: test SFP+ in lab prima del prossimo tentativo.

----------------------------------------------------------------
5. PATCH COMPLIANCE
----------------------------------------------------------------

  Categoria              Totale host   Patchati    % Compliance
  -----------------------------------------------------------
  Server Windows         45            43          95.6%
  Server Linux           30            29          96.7%
  Workstation            200           188         94.0%
  Network devices        25            23          92.0%

  Compliance complessiva: 94.3% (target: > 95%)   WARNING

  Host non conformi:
    - 2 server Windows: in attesa di finestra di manutenzione SAP
    - 1 server Linux: dipendenza applicativa da risolvere
    - 12 workstation: utenti in ferie/fuori sede
    - 2 switch: patch programmata per prossima settimana

----------------------------------------------------------------
6. BACKUP
----------------------------------------------------------------

  Job di backup totali:         620
  Backup riusciti:              614
  Backup falliti:               6
  Success rate:                 99.0% (target: > 99%)    OK

  Dettaglio fallimenti:
    - 3 fallimenti: agente backup non risponde su SRV-APP-07
      (risolto: riavvio agente, monitoring aggiunto)
    - 2 fallimenti: timeout su backup database HR (risolto:
      ottimizzazione finestra backup)
    - 1 fallimento: spazio insufficiente su target NAS
      (risolto: pulizia retention)

  Test di restore eseguiti nel mese: 3
  Test di restore riusciti: 3 (100%)

----------------------------------------------------------------
7. SICUREZZA
----------------------------------------------------------------

  Vulnerabilita aperte per severita:
    - Critica:    0
    - Alta:       3 (in corso di remediation, ETA 10 giorni)
    - Media:      12
    - Bassa:      28

  Nuove vulnerabilita identificate nel mese: 8
  Vulnerabilita risolte nel mese: 11
  Trend: IN MIGLIORAMENTO

  Eventi di sicurezza rilevanti:
    - Tentativo di phishing bloccato (14 email, 0 utenti compromessi)
    - Aggiornamento regole firewall per nuova policy accesso remoto

----------------------------------------------------------------
8. CAPACITY UTILIZATION
----------------------------------------------------------------

  Risorsa              Utilizzo attuale    Trend      Previsione
  -----------------------------------------------------------
  CPU (media cluster)  62%                 Stabile    OK per 12m
  RAM (media cluster)  74%                 +2%/mese   Attenzione a 6m
  Storage SAN          71%                 +1.2 TB/m  Upgrade a 10m
  Banda Internet       45%                 Stabile    OK per 12m
  Licenze M365         87%                 +3%/mese   Acquisto a 2m

----------------------------------------------------------------
9. STATO PROGETTI
----------------------------------------------------------------

  Progetto                      Stato       % Completamento  ETA
  -----------------------------------------------------------
  Migrazione Windows Server     In corso    45%              2026-09
  Nuovo sistema monitoring      Completato  100%             -
  Upgrade rete campus           Pianificato 0%               2026-12
  Implementazione MFA           In corso    80%              2026-04

----------------------------------------------------------------
10. STATO BUDGET
----------------------------------------------------------------

  Voce                  Budget annuale  Speso (YTD)  % Utilizzato
  -----------------------------------------------------------
  Hardware              EUR 120.000     EUR 45.000    37.5%
  Software/Licenze      EUR 80.000      EUR 62.000    77.5%
  Cloud services        EUR 50.000      EUR 14.500    29.0%
  Servizi esterni       EUR 40.000      EUR 12.000    30.0%
  Formazione            EUR 15.000      EUR 3.500     23.3%
  Contingency           EUR 20.000      EUR 2.000     10.0%
  -----------------------------------------------------------
  TOTALE                EUR 325.000     EUR 139.000   42.8%

  Note: spesa licenze elevata per rinnovo triennale antivirus.

----------------------------------------------------------------
11. ATTIVITA PREVISTE PER IL PROSSIMO MESE
----------------------------------------------------------------

  - Completamento rollout MFA per tutti i dipartimenti
  - Migrazione batch 2 server Windows (12 server)
  - Patch Tuesday Microsoft + patch critica Fortinet
  - Test DR trimestrale
  - Incontro vendor per rinnovo contratto supporto storage

================================================================
```

---

### KPI Dashboard

I Key Performance Indicator (KPI) da monitorare costantemente e presentare nel dashboard operativo:

| KPI                          | Formula / Definizione                                     | Target          | Frequenza    |
|------------------------------|----------------------------------------------------------|-----------------|--------------|
| System Availability          | (Tempo totale - Downtime) / Tempo totale x 100           | >= 99.9%        | Mensile      |
| Incident Count (P1/P2)      | Numero di incidenti critici e alti nel periodo            | Trend in calo   | Mensile      |
| MTTR                         | Somma tempi di risoluzione / Numero incidenti             | P1 < 1h, P2 < 4h| Mensile     |
| MTTA                         | Somma tempi di acknowledgement / Numero incidenti         | P1 < 5 min      | Mensile      |
| Patch Compliance Rate        | Host patchati entro SLA / Host totali x 100               | >= 95%          | Mensile      |
| Backup Success Rate          | Backup riusciti / Backup totali x 100                     | >= 99%          | Settimanale  |
| SLA Compliance               | Servizi entro SLA / Servizi totali x 100                  | 100%            | Mensile      |
| Open Vulnerabilities (Crit.) | Numero vulnerabilita critiche aperte                      | 0               | Settimanale  |
| Open Vulnerabilities (High)  | Numero vulnerabilita alte aperte                          | < 5             | Settimanale  |
| Change Success Rate          | Change riusciti / Change totali x 100                     | >= 95%          | Mensile      |
| Customer Satisfaction (CSAT) | Media punteggi di soddisfazione su ticket chiusi          | >= 4.0/5.0      | Mensile      |
| NPS (Net Promoter Score)     | % Promotori - % Detrattori (survey periodico)             | >= 30           | Trimestrale  |

---

### Creazione Dashboard

#### Dashboard con Grafana

Grafana e lo strumento piu diffuso per la creazione di dashboard IT. Esempio di configurazione per un dashboard di capacity planning:

```json
{
  "dashboard": {
    "title": "IT Operations — Monthly KPI",
    "panels": [
      {
        "title": "System Availability",
        "type": "gauge",
        "targets": [
          {
            "expr": "avg(up{job='node'}) * 100",
            "legendFormat": "Availability %"
          }
        ],
        "thresholds": [
          { "value": 99.0, "color": "red" },
          { "value": 99.5, "color": "yellow" },
          { "value": 99.9, "color": "green" }
        ]
      },
      {
        "title": "Incidents by Severity (Monthly)",
        "type": "barchart",
        "targets": [
          {
            "expr": "count by (severity) (alerts_total{period='current_month'})"
          }
        ]
      },
      {
        "title": "CPU Utilization Trend",
        "type": "timeseries",
        "targets": [
          {
            "expr": "avg(1 - rate(node_cpu_seconds_total{mode='idle'}[1h])) * 100"
          }
        ]
      },
      {
        "title": "Storage Capacity Forecast",
        "type": "timeseries",
        "targets": [
          {
            "expr": "node_filesystem_size_bytes{mountpoint='/'} - node_filesystem_avail_bytes{mountpoint='/'}",
            "legendFormat": "Used"
          },
          {
            "expr": "predict_linear(node_filesystem_avail_bytes{mountpoint='/'}[30d], 86400*90)",
            "legendFormat": "Predicted (90d)"
          }
        ]
      }
    ]
  }
}
```

#### Dashboard con Power BI / Excel

Per ambienti dove Grafana non e disponibile, creare un dashboard in Power BI o Excel:

**Struttura consigliata del file Excel per il dashboard mensile:**

- **Foglio "Dati"**: tabella con tutti i dati grezzi importati dai sistemi di monitoring (un record per servizio per giorno).
- **Foglio "Calcoli"**: formule per calcolare KPI aggregati (disponibilita, MTTR, compliance, ecc.).
- **Foglio "Dashboard"**: grafici e indicatori visivi collegati al foglio Calcoli.
  - Semafori (formattazione condizionale): verde/giallo/rosso per ogni KPI.
  - Grafici a barre per incidenti per severita.
  - Grafici a linee per trend di utilizzo risorse.
  - Tabella riepilogativa con tutti i KPI e i target.

#### Generazione Automatica dei Report

Automatizzare la generazione dei report per risparmiare tempo e ridurre errori:

```bash
#!/bin/bash
# Script per generazione automatica report mensile
# Eseguire il primo giorno lavorativo di ogni mese

MESE_PREC=$(date -d "last month" +"%Y-%m")
OUTPUT_DIR="/reports/monthly/${MESE_PREC}"
mkdir -p "${OUTPUT_DIR}"

# 1. Estrarre metriche di disponibilita da Prometheus
curl -s "http://prometheus:9090/api/v1/query_range?query=avg(up)&start=$(date -d "${MESE_PREC}-01" +%s)&end=$(date -d "${MESE_PREC}-01 +1 month" +%s)&step=3600" \
  | jq '.data.result' > "${OUTPUT_DIR}/availability.json"

# 2. Estrarre incidenti da sistema di ticketing (esempio API)
curl -s "https://itsm.azienda.it/api/incidents?created_after=${MESE_PREC}-01&created_before=${MESE_PREC}-31" \
  -H "Authorization: Bearer ${ITSM_TOKEN}" \
  > "${OUTPUT_DIR}/incidents.json"

# 3. Estrarre dati patch compliance da WSUS/SCCM
python3 /scripts/extract_patch_compliance.py --month "${MESE_PREC}" \
  --output "${OUTPUT_DIR}/patch_compliance.json"

# 4. Generare report PDF
python3 /scripts/generate_monthly_report.py \
  --data-dir "${OUTPUT_DIR}" \
  --template "/templates/monthly_report.html" \
  --output "${OUTPUT_DIR}/Report_IT_${MESE_PREC}.pdf"

# 5. Inviare report via email
python3 /scripts/send_report.py \
  --to "cto@azienda.it,it-manager@azienda.it" \
  --subject "Report IT Mensile — ${MESE_PREC}" \
  --attachment "${OUTPUT_DIR}/Report_IT_${MESE_PREC}.pdf"

echo "Report mensile ${MESE_PREC} generato e inviato."
```

---

## Budget IT

### Budget Planning

La pianificazione del budget IT per la manutenzione richiede una distinzione chiara tra spese in conto capitale (CAPEX) e spese operative (OPEX).

#### CAPEX vs OPEX

| Caratteristica     | CAPEX                                  | OPEX                                    |
|--------------------|----------------------------------------|-----------------------------------------|
| Definizione        | Investimenti in beni durevoli          | Spese operative ricorrenti              |
| Esempi             | Acquisto server, switch, storage       | Licenze SaaS, cloud, manutenzione       |
| Trattamento fiscale| Ammortamento pluriennale               | Deduzione nell'esercizio corrente       |
| Flusso di cassa    | Esborso iniziale elevato               | Pagamenti distribuiti nel tempo         |
| Flessibilita       | Bassa (asset fisso)                    | Alta (scalabilita)                      |

La tendenza generale del settore e lo spostamento da CAPEX a OPEX, grazie al cloud computing e ai modelli di licenza in abbonamento. Tuttavia, per molte organizzazioni il mix ottimale prevede ancora una componente CAPEX significativa.

#### Categorie di Budget per la Manutenzione IT

```
BUDGET MANUTENZIONE IT — ANNO [AAAA]

1. HARDWARE REFRESH                                    CAPEX
   - Server (rinnovo ciclico 5 anni)       EUR 80.000
   - Networking (switch, access point)     EUR 25.000
   - Storage (espansione/rinnovo)          EUR 35.000
   - Workstation e periferiche             EUR 40.000
   - UPS e infrastruttura datacenter       EUR 10.000
   Subtotale Hardware                      EUR 190.000

2. LICENZE SOFTWARE                                    OPEX
   - Microsoft 365 (200 utenti)            EUR 48.000
   - Antivirus/EDR (300 endpoint)          EUR 18.000
   - Software di monitoring                EUR 8.000
   - Licenze server (Windows, SQL)         EUR 15.000
   - Altre licenze applicative             EUR 12.000
   Subtotale Licenze                       EUR 101.000

3. SERVIZI CLOUD                                       OPEX
   - Azure IaaS (VM, storage)             EUR 30.000
   - Azure PaaS (database, app service)   EUR 15.000
   - AWS/GCP (servizi specifici)           EUR 8.000
   - Backup cloud                          EUR 5.000
   Subtotale Cloud                         EUR 58.000

4. FORMAZIONE                                          OPEX
   - Certificazioni team IT (3 persone)    EUR 9.000
   - Corsi e workshop                      EUR 4.000
   - Conferenze e eventi                   EUR 3.000
   Subtotale Formazione                    EUR 16.000

5. STRUMENTI E SERVIZI                                 OPEX
   - Contratti di manutenzione HW          EUR 20.000
   - Servizi di consulenza                 EUR 15.000
   - Strumenti di gestione (ITSM, RMM)    EUR 10.000
   Subtotale Strumenti                     EUR 45.000

6. PERSONALE (costi diretti manutenzione)              OPEX
   - Straordinari e reperibilita           EUR 12.000
   - Personale temporaneo per progetti     EUR 20.000
   Subtotale Personale                     EUR 32.000

7. CONTINGENCY (10% del totale)                        MISTO
   - Imprevisti e emergenze                EUR 44.200
   Subtotale Contingency                   EUR 44.200

================================================================
TOTALE BUDGET MANUTENZIONE IT              EUR 486.200
  di cui CAPEX:                            EUR 190.000
  di cui OPEX:                             EUR 296.200
================================================================
```

---

### TCO Calculation

Il Total Cost of Ownership (TCO) e una metodologia per calcolare il costo complessivo di possesso e gestione di un asset IT nel suo intero ciclo di vita.

#### TCO per Server (Esempio 5 anni)

```
TCO SERVER — Dell PowerEdge R760 (ciclo di vita 5 anni)

COSTI DIRETTI
  Acquisto hardware                     EUR 14.000
  Licenze OS (Windows Server 2025)      EUR 2.500
  Licenze software aggiuntivo           EUR 1.500
  Garanzia estesa (5 anni ProSupport)   EUR 3.000
  Subtotale costi diretti               EUR 21.000

COSTI OPERATIVI (annuali x 5)
  Energia elettrica (500W x 8760h x 0.25 EUR/kWh x PUE 1.5)
                                        EUR 1.642/anno x 5 = EUR 8.210
  Raffreddamento (incluso nel PUE)      Incluso sopra
  Spazio rack (1/4 rack)                EUR 500/anno x 5 = EUR 2.500
  Connettivita di rete                  EUR 200/anno x 5 = EUR 1.000
  Subtotale costi operativi             EUR 11.710

COSTI DI AMMINISTRAZIONE (annuali x 5)
  Ore di amministrazione (2h/settimana x EUR 50/h)
                                        EUR 5.200/anno x 5 = EUR 26.000
  Monitoring e gestione                 EUR 300/anno x 5 = EUR 1.500
  Backup (storage + licenza agente)     EUR 600/anno x 5 = EUR 3.000
  Subtotale amministrazione             EUR 30.500

COSTI DI FINE VITA
  Migrazione a nuovo hardware           EUR 2.000
  Smaltimento RAEE                      EUR 150
  Subtotale fine vita                    EUR 2.150

================================================================
TCO TOTALE (5 ANNI)                     EUR 65.360
TCO ANNUALE                             EUR 13.072
TCO MENSILE                             EUR 1.089
================================================================
```

#### Confronto TCO: Cloud vs On-Premise

```
CONFRONTO TCO — Workload: Application Server (5 anni)
                        On-Premise          Cloud (Azure VM)
----------------------------------------------------------
Hardware                EUR 14.000          EUR 0
Licenze OS              EUR 2.500           EUR 0 (incluso)
Energia + cooling       EUR 8.210           EUR 0 (incluso)
Spazio datacenter       EUR 2.500           EUR 0 (incluso)
Amministrazione         EUR 26.000          EUR 15.000
Costo VM/servizio       EUR 0               EUR 36.000 (D4s_v5, RI 3y)
Backup                  EUR 3.000           EUR 2.400
Networking              EUR 1.000           EUR 1.800 (egress)
Garanzia/Supporto       EUR 3.000           EUR 0 (incluso)
Fine vita               EUR 2.150           EUR 0
----------------------------------------------------------
TCO TOTALE 5 ANNI       EUR 62.360          EUR 55.200
TCO ANNUALE             EUR 12.472          EUR 11.040
----------------------------------------------------------
RISPARMIO CLOUD: EUR 7.160 (11.5%) in 5 anni

NOTE:
- Il calcolo cloud assume Reserved Instance 3 anni.
- On-premise non include costi di ridondanza (serve un secondo server).
- Cloud include alta disponibilita nativa.
- Valutare caso per caso: non sempre il cloud e piu economico.
```

---

### Cost Optimization

#### Audit e Recupero Licenze

Condurre audit periodici (trimestrali) per identificare e recuperare licenze inutilizzate:

1. Estrarre l'elenco di tutte le licenze assegnate dal portale di gestione (Microsoft Admin Center, Adobe Admin Console, ecc.).
2. Confrontare con i dati di utilizzo effettivo (ultimo accesso, attivita negli ultimi 90 giorni).
3. Identificare licenze assegnate a utenti inattivi, dismessi o che non utilizzano il prodotto.
4. Revocare le licenze inutilizzate e riassegnarle o ridurre il numero di abbonamenti.

**Risparmio tipico**: 10-20% del costo licenze annuale.

#### Ottimizzazione Costi Cloud

- **Reserved Instances / Savings Plans**: per workload stabili, l'acquisto di istanze riservate (1 o 3 anni) offre risparmi del 30-60% rispetto al prezzo on-demand.
- **Right-sizing**: ridimensionare le VM sovradimensionate. Il 30-40% delle VM cloud sono tipicamente sovradimensionate.
- **Scheduling**: spegnere le VM di sviluppo/test fuori dall'orario lavorativo (risparmio fino al 65%).
- **Spot/Preemptible instances**: per workload tolleranti alle interruzioni (batch processing, CI/CD), risparmio fino al 90%.
- **Storage tiering**: spostare dati poco acceduti su tier di storage piu economici (Cool, Archive).

#### Calcolo ROI dell'Automazione

Per giustificare investimenti in automazione, calcolare il Return on Investment:

```
ROI AUTOMAZIONE — Esempio: Automazione Patch Management

COSTI (investimento)
  Strumento di automazione (licenza annuale)    EUR 5.000
  Configurazione e implementazione (80h)        EUR 4.000
  Formazione team (16h x 3 persone)             EUR 2.400
  Manutenzione annuale (20h)                    EUR 1.000
  Costo totale primo anno                       EUR 12.400
  Costo annuale successivo                      EUR 6.000

BENEFICI (risparmio annuale)
  Tempo risparmiato patching manuale
    Prima: 200 server x 2h/server x 12 mesi = 4.800h/anno
    Dopo:  200 server x 0.2h/server x 12 mesi = 480h/anno
    Risparmio: 4.320h x EUR 50/h =              EUR 216.000
  Riduzione incidenti da patch mancanti
    Stima: 5 incidenti/anno in meno x EUR 2.000 = EUR 10.000
  Risparmio totale annuale                       EUR 226.000

ROI = (Benefici - Costi) / Costi x 100
ROI Anno 1 = (226.000 - 12.400) / 12.400 x 100 = 1.722%
ROI Anni successivi = (226.000 - 6.000) / 6.000 x 100 = 3.667%

Payback period: meno di 1 mese
```

---

## Roadmap Tecnologica

### Technology Roadmap Creation

La roadmap tecnologica e un documento strategico che definisce l'evoluzione pianificata dell'infrastruttura IT su un orizzonte temporale di 2-3 anni. La sua creazione segue un processo strutturato.

#### Assessment dello Stato Attuale

Documentare lo stato attuale dell'infrastruttura in tutte le sue dimensioni:

- **Inventario completo**: hardware, software, servizi cloud, contratti.
- **Architettura attuale**: diagrammi di rete, diagrammi applicativi, flussi di dati.
- **Punti di forza**: cosa funziona bene, competenze del team, investimenti recenti.
- **Punti deboli**: problemi ricorrenti, tecnologie obsolete, gap di sicurezza.
- **Debito tecnico**: workaround in produzione, configurazioni non standard, documentazione mancante.

#### Definizione dello Stato Target

Definire dove si vuole arrivare, allineandosi con gli obiettivi strategici aziendali:

- **Requisiti di business**: crescita prevista, nuovi prodotti/servizi, espansione geografica.
- **Requisiti tecnici**: prestazioni, disponibilita, sicurezza, scalabilita.
- **Requisiti normativi**: compliance GDPR, certificazioni ISO 27001, requisiti di settore.
- **Requisiti operativi**: livello di automazione, competenze necessarie, modello operativo target.

#### Gap Analysis

Confrontare stato attuale e stato target per identificare i gap da colmare:

```
GAP ANALYSIS — Esempio

Area              Stato Attuale              Stato Target               Gap
---------------------------------------------------------------------------
Monitoring        Monitoring base (Nagios)   Osservabilita completa     ALTO
                                             (metriche, log, trace)
Automazione       Script manuali             IaC + Config Management    ALTO
Sicurezza         Firewall perimetrale       Zero Trust, EDR, SIEM     MEDIO
Cloud             100% on-premise            Ibrido (40% cloud)        ALTO
Backup/DR         Backup locale              DR multi-site, RTO < 4h   MEDIO
Patching          Manuale, mensile           Automatizzato, settimanale MEDIO
Documentazione    Parziale, non aggiornata   Completa, versionata       BASSO
```

#### Prioritizzazione delle Iniziative

Utilizzare una matrice Effort vs Impact per prioritizzare le iniziative:

```
                          IMPATTO
                  Basso           Alto
            ┌──────────────┬──────────────┐
    Basso   │  BASSA       │  QUICK WINS  │
            │  PRIORITA    │  (fare subito│
  EFFORT    │              │   per primi) │
            ├──────────────┼──────────────┤
    Alto    │  EVITARE     │  PROGETTI    │
            │  (non fare   │  STRATEGICI  │
            │  o rimandare)│  (pianificare│
            │              │   con cura)  │
            └──────────────┴──────────────┘
```

Classificare ogni iniziativa:
- **Quick Wins** (basso effort, alto impatto): implementare per primi. Es. automazione backup, hardening base.
- **Progetti strategici** (alto effort, alto impatto): pianificare con attenzione, allocare risorse dedicate. Es. migrazione cloud, implementazione Zero Trust.
- **Bassa priorita** (basso effort, basso impatto): fare quando c'e tempo disponibile. Es. aggiornamento documentazione.
- **Evitare** (alto effort, basso impatto): non investire risorse. Es. migrazione di sistemi legacy che saranno dismissi.

---

### Example 3-Year Roadmap

```
================================================================
     ROADMAP TECNOLOGICA IT — 2026-2028
================================================================

ANNO 1 (2026): STABILIZZAZIONE E FONDAMENTA
================================================================

Q1 2026 — Assessment e Planning
  [x] Inventario completo infrastruttura
  [x] Assessment sicurezza (vulnerability scan, penetration test)
  [x] Definizione standard e policy operative
  [ ] Selezione strumenti di monitoring (Prometheus + Grafana)

Q2 2026 — Monitoring e Visibilita
  [ ] Implementazione sistema di monitoring centralizzato
  [ ] Configurazione alerting per tutti i servizi critici
  [ ] Creazione dashboard operativi e KPI
  [ ] Implementazione log management centralizzato (ELK/Loki)

Q3 2026 — Automazione di Base
  [ ] Implementazione Configuration Management (Ansible)
  [ ] Automazione patch management
  [ ] Automazione provisioning VM (template standardizzati)
  [ ] Implementazione backup automatizzato con test di restore

Q4 2026 — Sicurezza Fondamentale
  [ ] Implementazione MFA per tutti gli accessi amministrativi
  [ ] Deployment EDR su tutti gli endpoint
  [ ] Segmentazione di rete (VLAN, micro-segmentazione)
  [ ] Primo DR test completo

Risultati attesi Anno 1:
  - Disponibilita servizi: da 99.5% a 99.9%
  - Incidenti P1: riduzione del 50%
  - Patch compliance: da 80% a 95%
  - Visibilita completa sull'infrastruttura

================================================================

ANNO 2 (2027): CLOUD IBRIDO E MATURITA OPERATIVA
================================================================

Q1 2027 — Preparazione Cloud
  [ ] Assessment workload per migrazione cloud
  [ ] Progettazione architettura cloud ibrida
  [ ] Implementazione connettivita ibrida (VPN/ExpressRoute)
  [ ] Formazione team su piattaforma cloud scelta

Q2 2027 — Migrazione Cloud Fase 1
  [ ] Migrazione workload non critici (dev/test, file sharing)
  [ ] Implementazione backup cloud (3-2-1 rule)
  [ ] Setup cost management e alerting costi cloud
  [ ] Migrazione DR su cloud

Q3 2027 — Sicurezza Avanzata
  [ ] Implementazione SIEM
  [ ] Avvio programma Zero Trust (identity-based access)
  [ ] Security awareness training per tutti i dipendenti
  [ ] Implementazione DLP (Data Loss Prevention)

Q4 2027 — Self-Service e Efficienza
  [ ] Portale self-service per richieste IT comuni
  [ ] Catalogo servizi IT pubblicato
  [ ] Automazione onboarding/offboarding utenti
  [ ] Knowledge base interna per troubleshooting

Risultati attesi Anno 2:
  - 30% workload migrati su cloud
  - RTO migliorato da 24h a 4h
  - Riduzione ticket ripetitivi del 40% (self-service)
  - Certificazione ISO 27001 avviata

================================================================

ANNO 3 (2028): AUTOMAZIONE COMPLETA E OTTIMIZZAZIONE
================================================================

Q1 2028 — Infrastructure as Code
  [ ] Migrazione completa a IaC (Terraform/Pulumi)
  [ ] Pipeline CI/CD per infrastruttura
  [ ] Drift detection automatico
  [ ] Gestione secrets centralizzata (Vault)

Q2 2028 — Operazioni Predittive
  [ ] Machine learning per anomaly detection
  [ ] Capacity planning predittivo automatizzato
  [ ] Auto-remediation per incidenti comuni
  [ ] ChatOps per operazioni di routine

Q3 2028 — Ottimizzazione Costi
  [ ] Implementazione FinOps per costi cloud
  [ ] Right-sizing automatizzato
  [ ] Consolidamento licenze e contratti vendor
  [ ] Analisi TCO completa e ottimizzazione

Q4 2028 — Maturita e Continuous Improvement
  [ ] Raggiungimento certificazione ISO 27001
  [ ] Audit di maturita ITIL
  [ ] Pianificazione roadmap 2029-2031
  [ ] Documentazione completa e knowledge transfer

Risultati attesi Anno 3:
  - 50%+ workload su cloud
  - Automazione del 80% delle operazioni di routine
  - Riduzione costi operativi del 25% rispetto al 2026
  - RTO < 1h per tutti i servizi critici
  - Team IT focalizzato su innovazione anziche manutenzione

================================================================
```

---

## Comunicazione e Stakeholder Management

La capacita di comunicare efficacemente i risultati e le necessita dell'IT e tanto importante quanto la competenza tecnica. Report tecnici incomprensibili per il management rendono invisibile il lavoro del team IT e complicano l'approvazione di budget e progetti.

### Segmentazione dell'Audience dei Report

Preparare versioni diverse del report per audience diverse:

| Audience          | Contenuto                                         | Frequenza    | Formato           | Livello di dettaglio |
|-------------------|---------------------------------------------------|--------------|--------------------|---------------------|
| Team tecnico      | Metriche dettagliate, log incidenti, azioni       | Settimanale  | Dashboard live     | Molto dettagliato   |
| IT Management     | KPI aggregati, trend, rischi, progetti            | Mensile      | Report + dashboard | Dettagliato         |
| Executive (CTO)   | Stato complessivo, rischi business, budget         | Mensile      | Executive summary  | Sintetico           |
| Board/C-Suite     | Impatto business, ROI, rischi strategici           | Trimestrale  | Presentazione      | Molto sintetico     |

### Frequenza di Comunicazione

```
Frequenza          Tipo di comunicazione                    Destinatari
------------------------------------------------------------------------
Giornaliera        Status operativo (se criticit attive)   Team IT
Settimanale        Weekly operations review                 Team IT + Manager
Mensile            Report mensile IT                        IT Management, CTO
Trimestrale        Business review IT                       C-Suite, Board
Ad-hoc             Notifica incidenti P1                    Tutti gli stakeholder
Ad-hoc             Report post-incidente (RCA)              Management + tecnici
```

### Reporting di Escalation

Per incidenti critici, seguire un protocollo di comunicazione strutturato:

1. **Notifica iniziale** (entro 15 minuti dal rilevamento): cosa e successo, impatto stimato, azioni in corso.
2. **Aggiornamenti periodici** (ogni 30-60 minuti durante l'incidente): stato attuale, progresso della risoluzione, ETA stimato.
3. **Notifica di risoluzione**: conferma del ripristino, impatto effettivo, azioni di follow-up.
4. **Report post-incidente** (entro 48 ore): Root Cause Analysis completa, timeline dell'incidente, azioni correttive, lezioni apprese.

### Consigli per la Scrittura dell'Executive Summary

L'executive summary e la sezione piu letta (e spesso l'unica letta) del report IT. Deve essere:

- **Conciso**: massimo mezza pagina, idealmente 5-8 righe.
- **Orientato al business**: non "il server ha avuto un errore kernel", ma "il sistema di e-commerce ha avuto 2 ore di interruzione, con un impatto stimato di EUR X sulle vendite".
- **Strutturato**: prima le buone notizie, poi i problemi con le relative azioni.
- **Azionabile**: ogni problema menzionato deve avere un'azione associata.

**Esempio di executive summary efficace:**

> *Nel mese di marzo 2026, l'infrastruttura IT ha mantenuto una disponibilita complessiva del 99.94%, superando il target SLA del 99.9%. Il progetto di migrazione Windows Server procede secondo i piani (45% completato). Si segnala un'area di attenzione: la capacita RAM del cluster di virtualizzazione raggiungera la soglia critica entro 6 mesi al tasso di crescita attuale. E stata avviata la procedura di acquisto per l'espansione (EUR 12.000, approvazione richiesta entro aprile). La patch compliance e al 94.3%, leggermente sotto il target del 95%: le azioni correttive sono in corso e il target sara raggiunto entro il prossimo mese.*

### Tradurre Metriche Tecniche in Impatto di Business

| Metrica tecnica           | Traduzione business                                      |
|---------------------------|----------------------------------------------------------|
| Disponibilita 99.9%      | I sistemi sono stati accessibili per il 99.9% del tempo, con solo 43 minuti di interruzione nel mese |
| MTTR 45 min per P1        | I problemi critici vengono risolti in meno di 1 ora      |
| Patch compliance 95%      | Il 95% dei sistemi e protetto contro le vulnerabilita note|
| Backup success rate 99%   | I dati aziendali sono protetti con affidabilita del 99%  |
| Capacita storage 71%      | Abbiamo risorse storage sufficienti per i prossimi 10 mesi|
| 3 vulnerabilita alte      | Esistono 3 punti deboli di sicurezza significativi in corso di risoluzione|

---

## Finestre di Manutenzione e Calendario Change

La gestione strutturata delle finestre di manutenzione e del calendario dei change e un elemento critico della pianificazione IT. Senza un sistema formale, le attivita di manutenzione si sovrappongono ai momenti di picco operativo, generano conflitti tra team e provocano interruzioni non coordinate che danneggiano la produttivita aziendale.

### Tipologie di Finestre di Manutenzione

Le finestre di manutenzione si classificano in base alla loro frequenza, impatto e natura del lavoro previsto. Ogni tipologia richiede un livello diverso di approvazione, comunicazione e pianificazione.

#### Manutenzione Ordinaria Programmata

Sono le finestre ricorrenti stabilite a calendario, durante le quali vengono eseguite attivita di routine:

| Frequenza       | Attivita tipiche                                                      | Finestra consigliata                     |
|-----------------|-----------------------------------------------------------------------|------------------------------------------|
| Settimanale     | Patching workstation, pulizia log, verifica backup                    | Domenica 02:00-06:00                     |
| Mensile         | Patch Tuesday Microsoft, aggiornamenti firmware, riavvio servizi      | Secondo sabato del mese 22:00-06:00      |
| Trimestrale     | Aggiornamenti firmware networking, test DR, pulizia storage           | Ultimo sabato del trimestre 20:00-08:00  |
| Semestrale      | Major upgrade OS, rinnovo certificati, audit configurazione           | Finestra dedicata di 12-16 ore           |
| Annuale         | Refresh hardware, test completo DR, audit sicurezza infrastrutturale  | Weekend lungo pianificato                |

**Esempio di definizione formale di una finestra di manutenzione:**

```
DEFINIZIONE FINESTRA DI MANUTENZIONE — MW-MONTHLY-01
=====================================================

Nome:               Manutenzione Mensile Server Produzione
Codice:             MW-MONTHLY-01
Frequenza:          Mensile (secondo sabato del mese)
Orario:             22:00 (sabato) — 06:00 (domenica)
Durata:             8 ore
Buffer pre/post:    30 minuti prima e dopo

Sistemi coinvolti:
  - Server Windows produzione (cluster A, B)
  - Server Linux applicativi (farm app-prod)
  - Database server (SQL Server, PostgreSQL)

Sistemi ESCLUSI:
  - Domain Controller primario (finestra dedicata)
  - Firewall perimetrale (finestra dedicata)
  - Sistema di posta elettronica (finestra dedicata)

Attivita consentite:
  - Installazione patch di sicurezza approvate
  - Riavvio servizi e sistemi operativi
  - Aggiornamento agenti di monitoring e backup
  - Espansione disco / aggiunta risorse
  - Attivita di change pre-approvate (Standard Change)

Attivita NON consentite:
  - Upgrade major di sistema operativo
  - Modifiche architetturali
  - Migrazione di workload tra host
  - Qualsiasi change non approvato dal CAB

Responsabile:       System Administrator Senior
Approvazione:       IT Manager (pre-approvata per attivita standard)
Notifica a:         Tutti gli stakeholder tecnici (24h prima)
Escalation:         On-call manager reperibile durante la finestra

Procedura di rollback:
  - Snapshot/backup pre-manutenzione obbligatorio
  - Rollback entro 2h dalla fine della finestra se problemi
  - Criteri di rollback: errore critico non risolto entro 1h
```

#### Manutenzione Straordinaria

Le finestre di manutenzione straordinaria vengono richieste quando e necessario intervenire al di fuori del calendario ordinario. Richiedono un processo di approvazione accelerato ma formale:

1. **Richiesta formale**: il richiedente compila un modulo con giustificazione, impatto, finestra proposta e piano di rollback.
2. **Valutazione impatto**: l'IT Manager valuta l'impatto sul business e i rischi.
3. **Approvazione**: per sistemi critici, serve l'approvazione del CAB (Change Advisory Board) anche in modalita accelerata (eCAB via email o chat).
4. **Comunicazione**: notifica agli stakeholder con almeno 4 ore di anticipo (idealmente 24 ore).
5. **Esecuzione e validazione**: esecuzione con monitoraggio attivo e validazione post-intervento.

#### Manutenzione di Emergenza

Per situazioni critiche che richiedono intervento immediato (es. patch zero-day, guasto hardware imminente):

```
PROTOCOLLO MANUTENZIONE DI EMERGENZA
=====================================

Attivazione: Vulnerabilita critica attivamente sfruttata (CVE con CVSS >= 9.0)
            OPPURE guasto hardware imminente (allarmi predittivi disco/memoria)
            OPPURE degrado critico delle prestazioni con impatto utenti

Processo:
  1. Notifica immediata all'IT Manager e al CISO
  2. Approvazione verbale o via chat (documentare ex-post)
  3. Comunicazione a stakeholder tecnici in tempo reale
  4. Comunicazione a stakeholder business (se impatto utenti)
  5. Esecuzione con 2 operatori (4 occhi)
  6. Validazione e ripristino servizio
  7. Documentazione post-intervento entro 24 ore
  8. Emergency Change Record nel sistema ITSM

Limiti:
  - Solo le azioni strettamente necessarie per risolvere l'emergenza
  - Nessuna modifica aggiuntiva "gia che ci siamo"
  - Documentazione dettagliata obbligatoria ex-post
```

### Calendario Change e Collision Detection

Il calendario dei change e lo strumento centrale per visualizzare tutte le attivita di manutenzione pianificate, evitare conflitti e garantire la coordinazione tra team.

#### Struttura del Calendario Change

Un calendario change efficace deve includere:

- **Vista mensile e settimanale**: per la pianificazione a medio termine e il dettaglio operativo.
- **Codifica a colori** per tipo di change: Standard (verde), Normal (blu), Emergency (rosso).
- **Indicatori di impatto**: basso (cerchio piccolo), medio (cerchio medio), alto (cerchio grande).
- **Filtraggio per sistema/servizio**: possibilita di visualizzare solo i change relativi a un servizio specifico.
- **Blackout window evidenziate**: periodi in cui i change sono vietati, chiaramente visibili.

**Esempio di calendario settimanale:**

```
CALENDARIO CHANGE — Settimana 22/2026 (25-31 Maggio)
=====================================================

Lun 25    Mar 26    Mer 27    Gio 28    Ven 29    Sab 30    Dom 31
─────────────────────────────────────────────────────────────────────
          [STD]                                    [MW-MONTHLY-01]
          Aggiorn.                                 Manutenzione
          agente                                   mensile server
          backup                                   22:00-06:00
          (basso)                                  (alto)

                    [NOR]
                    Upgrade
                    switch
                    access
                    (medio)
                    14:00-16:00

                              [STD]
                              Rinnovo
                              certificato
                              SSL web
                              (basso)
                              10:00-10:30

Legenda: [STD]=Standard  [NOR]=Normal  [EMG]=Emergency
         [MW-xxx]=Finestra di manutenzione
```

#### Collision Detection

Il sistema di calendario change deve rilevare automaticamente le collisioni, cioe situazioni in cui due o piu change impattano gli stessi sistemi nella stessa finestra temporale. Le regole di collision detection includono:

| Tipo di collisione                     | Azione                                                    |
|----------------------------------------|-----------------------------------------------------------|
| Stesso sistema, stessa finestra        | BLOCCO: ripianificare uno dei change                      |
| Sistemi dipendenti, stessa finestra    | AVVISO: valutare se compatibili                           |
| Stesso team responsabile, stessa ora   | AVVISO: verificare disponibilita risorse                  |
| Change alto impatto nella stessa notte | BLOCCO: massimo 1 change alto impatto per finestra        |
| Change in periodo di blackout          | BLOCCO: non consentito (solo emergency)                   |

**Regole di buona pratica per la pianificazione dei change:**

1. Non pianificare piu di un change ad alto impatto nella stessa finestra di manutenzione.
2. Prevedere un buffer di 30 minuti tra la fine di un change e l'inizio del successivo.
3. Non pianificare change critici il venerdi pomeriggio (nessun supporto pieno nel weekend).
4. Evitare change complessi nelle settimane di chiusura aziendale o eventi critici di business.
5. Documentare sempre le dipendenze tra change nel sistema ITSM.

### Blackout Window e Freeze Period

Le blackout window (o freeze period) sono periodi durante i quali qualsiasi change all'infrastruttura IT e vietato, salvo emergenze di sicurezza. Servono a proteggere i sistemi durante momenti critici per il business.

#### Periodi di Blackout Tipici

```
CALENDARIO BLACKOUT — Anno 2026
================================

Periodo                          Motivazione                          Durata
──────────────────────────────────────────────────────────────────────────────
15-31 Dicembre                   Chiusura natalizia / picco vendite   17 giorni
28-31 Marzo                      Chiusura trimestrale bilancio        4 giorni
28-30 Giugno                     Chiusura semestrale bilancio         3 giorni
27-30 Settembre                  Chiusura trimestrale bilancio        4 giorni
Black Friday - Cyber Monday      Picco e-commerce (se applicabile)    5 giorni
Primo giorno lavorativo gennaio  Riapertura sistemi                   1 giorno
Date di audit ISO/compliance     Periodo di audit esterno             Variabile

Eccezioni consentite durante blackout:
  - Emergency change per vulnerabilita critica (CVSS >= 9.0)
  - Emergency change per guasto hardware con impatto su servizio critico
  - Approvazione: CTO + CISO (doppia approvazione richiesta)
```

#### Gestione delle Eccezioni

Ogni eccezione al freeze period deve seguire un processo rigoroso:

1. Giustificazione scritta dell'urgenza con evidenza del rischio.
2. Analisi di impatto documentata e piano di rollback testato.
3. Approvazione formale del CTO e del CISO (doppia firma).
4. Esecuzione con supervisione diretta del responsabile IT.
5. Monitoraggio intensivo per le 24 ore successive.
6. Report post-intervento con documentazione completa.

### Comunicazione delle Manutenzioni Programmate

La comunicazione delle manutenzioni e un aspetto spesso sottovalutato che genera frustrazione negli utenti e nei team di business. Un protocollo di comunicazione strutturato previene la maggior parte dei reclami.

#### Template di Notifica Manutenzione Programmata

```
OGGETTO: [MANUTENZIONE PROGRAMMATA] — [Nome servizio] — [Data] [Orario]

Gentili utenti,

Vi informiamo che e stata pianificata una manutenzione programmata
sui seguenti sistemi:

  Servizi interessati:   [Elenco servizi]
  Data e orario:         [GG/MM/AAAA dalle HH:MM alle HH:MM]
  Durata stimata:        [X ore]
  Impatto previsto:      [Descrizione impatto per gli utenti]

  Durante la manutenzione:
  - [Servizio X] sara NON DISPONIBILE
  - [Servizio Y] potrebbe subire rallentamenti
  - [Servizio Z] non sara interessato

  Azioni richieste agli utenti:
  - Salvare il lavoro in corso prima delle [HH:MM]
  - Non tentare di accedere ai sistemi durante la finestra indicata
  - Segnalare eventuali anomalie dopo il ripristino a [email/canale]

  Al termine della manutenzione, verra inviata una comunicazione
  di conferma del ripristino del servizio.

  Per informazioni: [email helpdesk] — [telefono helpdesk]

  Distinti saluti,
  Team IT Operations
```

**Tempistiche di comunicazione:**

| Tipo di manutenzione      | Preavviso minimo    | Canali di comunicazione              |
|---------------------------|---------------------|--------------------------------------|
| Ordinaria (basso impatto) | 48 ore              | Email, portale intranet              |
| Ordinaria (alto impatto)  | 5 giorni lavorativi | Email, intranet, riunione team lead  |
| Straordinaria             | 4-24 ore            | Email, chat aziendale, telefono      |
| Emergenza                 | Immediata           | Chat, telefono, SMS, email           |

---

## SLA Reporting Avanzato

Il reporting sugli SLA (Service Level Agreement) va oltre il semplice calcolo della disponibilita percentuale. Un SLA reporting maturo analizza le tendenze, identifica le cause delle violazioni, misura la qualita percepita del servizio e fornisce indicazioni predittive per prevenire future violazioni.

### Struttura di un SLA Report

Un SLA report completo deve coprire tutte le dimensioni della qualita del servizio, non solo l'uptime. La struttura consigliata comprende le seguenti sezioni.

#### Template SLA Report Mensile

```
================================================================
       SLA REPORT — [SERVIZIO] — [MESE] [ANNO]
================================================================

Preparato da: [Nome, Ruolo]
Data di emissione: [GG/MM/AAAA]
Periodo: [01/MM/AAAA - 30/MM/AAAA]
SLA di riferimento: [Codice SLA, versione, data]

----------------------------------------------------------------
1. RIEPILOGO DISPONIBILITA
----------------------------------------------------------------

  Metrica                  Target SLA    Risultato     Stato
  -----------------------------------------------------------
  Disponibilita servizio   99.9%         99.95%        OK
  Tempo di risposta P1     < 15 min      12 min (avg)  OK
  Tempo di risoluzione P1  < 1 ora       45 min (avg)  OK
  Tempo di risposta P2     < 30 min      22 min (avg)  OK
  Tempo di risoluzione P2  < 4 ore       3h 15m (avg)  OK
  Tempo di risposta P3     < 2 ore       1h 40m (avg)  OK
  Tempo di risoluzione P3  < 8 ore       6h 20m (avg)  OK

  Minuti di downtime non pianificato:   43 min
  Minuti di downtime pianificato:       240 min (manutenzione)
  Finestre SLA escluse:                 Manutenzioni programmate,
                                        disastri naturali (come da SLA)

----------------------------------------------------------------
2. DETTAGLIO INTERRUZIONI
----------------------------------------------------------------

  Data        Inizio   Fine     Durata   Servizio         Causa
  -----------------------------------------------------------
  05/03/2026  14:22    14:50    28 min   Portale web      Errore deploy
  18/03/2026  09:15    09:30    15 min   Database HR      Pool esaurito

  Tempo totale di indisponibilita: 43 minuti
  Disponibilita calcolata: (43.200 - 43) / 43.200 = 99.90%
  (43.200 = minuti totali nel mese escl. manutenzioni programmate)

----------------------------------------------------------------
3. TREND DI DISPONIBILITA (ULTIMI 6 MESI)
----------------------------------------------------------------

  Mese        Disponibilita   Target   Delta    Trend
  -----------------------------------------------------------
  Ottobre     99.87%          99.9%    -0.03%   ↓
  Novembre    99.92%          99.9%    +0.02%   ↑
  Dicembre    99.98%          99.9%    +0.08%   ↑
  Gennaio     99.95%          99.9%    +0.05%   ↑
  Febbraio    99.91%          99.9%    +0.01%   →
  Marzo       99.90%          99.9%    +0.00%   →

  Media 6 mesi: 99.92% — CONFORME AL TARGET

----------------------------------------------------------------
4. PERFORMANCE DEI TEMPI DI RISPOSTA
----------------------------------------------------------------

  Priorita   # Ticket   MTTA      Target    % Entro SLA
  -----------------------------------------------------------
  P1         2          12 min    < 15 min   100%
  P2         8          22 min    < 30 min   100%
  P3         34         1h 40m    < 2h       94.1% (2 fuori SLA)
  P4         86         4h 10m    < 8h       97.7% (2 fuori SLA)

  Ticket fuori SLA (tempo di risposta): 4 su 130 (3.1%)

----------------------------------------------------------------
5. PERFORMANCE DEI TEMPI DI RISOLUZIONE
----------------------------------------------------------------

  Priorita   # Ticket   MTTR      Target    % Entro SLA
  -----------------------------------------------------------
  P1         2          45 min    < 1h       100%
  P2         8          3h 15m    < 4h       87.5% (1 fuori SLA)
  P3         34         6h 20m    < 8h       91.2% (3 fuori SLA)
  P4         86         16h       < 24h      95.3% (4 fuori SLA)

  Ticket fuori SLA (tempo di risoluzione): 8 su 130 (6.2%)

----------------------------------------------------------------
6. ANALISI VIOLAZIONI SLA
----------------------------------------------------------------

  Violazione #1: Ticket INC-2026-1842 (P2)
    Descrizione: Impossibilita di accesso al modulo reportistica SAP
    Tempo di risoluzione: 5h 20m (target: < 4h)
    Causa: Dipendenza da vendor esterno per patch applicativa
    Root cause: Mancanza di competenza interna sul modulo specifico
    Azione correttiva: Formazione interna su modulo SAP BI (Q2 2026)

  Violazione #2-4: Ticket INC-2026-1901, 1923, 1955 (P3)
    Pattern: Tutti relativi a timeout connessione database HR
    Root cause: Pool connessioni sottodimensionato dopo upgrade applicativo
    Azione correttiva: Ampliamento pool connessioni (completato 22/03)
    Verifica: Nessuna recidiva dopo la correzione

----------------------------------------------------------------
7. SODDISFAZIONE UTENTE
----------------------------------------------------------------

  Survey inviate: 130 (a tutti i richiedenti ticket chiusi)
  Survey completate: 78 (tasso di risposta: 60%)
  CSAT medio: 4.2 / 5.0 (target: >= 4.0)    OK

  Distribuzione:
    5 stelle: 35 (44.9%)
    4 stelle: 28 (35.9%)
    3 stelle: 10 (12.8%)
    2 stelle: 4 (5.1%)
    1 stella: 1 (1.3%)

  Commenti negativi ricorrenti:
    - "Tempo di attesa al telefono troppo lungo" (3 menzioni)
    - "Non aggiornato sullo stato del ticket" (2 menzioni)

  Azioni: Implementazione notifiche automatiche stato ticket (Q2)

================================================================
```

### Analisi delle Violazioni SLA

L'analisi delle violazioni SLA e il processo piu importante del SLA reporting, perche trasforma un dato negativo (la violazione) in un'opportunita di miglioramento. L'obiettivo non e assegnare colpe, ma identificare le cause sistemiche e prevenire il ripetersi delle violazioni.

#### Metodologia di Root Cause Analysis per SLA Breach

Per ogni violazione SLA, eseguire un'analisi strutturata secondo tre categorie principali:

**Persone:**
- Competenze insufficienti per gestire il tipo di incidente.
- Personale non disponibile (ferie, malattia, fuori orario).
- Alert fatigue: troppi allarmi rendono il team meno reattivo.
- Mancanza di documentazione o runbook aggiornati.

**Processi:**
- Escalation non attivata o attivata in ritardo.
- OLA (Operational Level Agreement) interni non definiti o non rispettati.
- Processo di approvazione troppo lento per le azioni correttive.
- Timer SLA mal configurato nel sistema ITSM (es. non si ferma durante l'attesa di risposta del cliente).

**Tecnologia:**
- Strumenti di monitoring che non rilevano il problema tempestivamente.
- Sistemi ITSM non integrati (allarme in uno strumento, ticket in un altro).
- Automazione mancante per azioni di remediation note.
- Infrastruttura sottodimensionata che genera incidenti ricorrenti.

#### Report di Trend delle Violazioni SLA

Tracciare le violazioni SLA nel tempo per identificare pattern:

```
TREND VIOLAZIONI SLA — Ultimi 12 Mesi
======================================

Mese         P1 breach   P2 breach   P3 breach   P4 breach   Totale   % Breach
─────────────────────────────────────────────────────────────────────────────────
Apr 2025     1           3           8            12          24       8.2%
Mag 2025     0           2           6            10          18       6.1%
Giu 2025     0           2           5            8           15       5.0%
Lug 2025     1           1           7            9           18       5.8%
Ago 2025     0           1           4            7           12       4.1%
Set 2025     0           2           5            6           13       4.3%
Ott 2025     0           1           4            8           13       4.5%
Nov 2025     0           1           3            5           9        3.0%
Dic 2025     0           0           4            6           10       3.4%
Gen 2026     0           1           3            5           9        3.1%
Feb 2026     0           0           4            4           8        2.7%
Mar 2026     0           1           3            4           8        2.7%
─────────────────────────────────────────────────────────────────────────────────
TREND COMPLESSIVO: IN MIGLIORAMENTO (da 8.2% a 2.7%)

Top 3 cause root delle violazioni:
  1. Dipendenza da vendor esterni (28% delle breach)
  2. Knowledge gap del team (22% delle breach)
  3. Configurazione errata timer SLA nel ITSM (18% delle breach)
```

### OLA e Underpinning Contracts

Gli SLA esterni (verso il business) sono supportati da accordi interni chiamati OLA (Operational Level Agreement) e da contratti con fornitori esterni (Underpinning Contracts — UC). La reportistica deve coprire anche questi livelli.

#### Struttura della Catena di Supporto

```
                    ┌───────────────────┐
                    │    SLA            │
                    │  (verso il        │
                    │   Business)       │
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │   OLA #1   │  │   OLA #2   │  │   OLA #3   │
     │  (Team     │  │  (Team     │  │  (Team     │
     │   Network) │  │   Server)  │  │   Develop) │
     └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
            │               │               │
            ▼               ▼               ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │   UC #1    │  │   UC #2    │  │   UC #3    │
     │  (ISP)     │  │  (Vendor   │  │  (Software │
     │            │  │   HW)      │  │   House)   │
     └────────────┘  └────────────┘  └────────────┘
```

**Esempio di OLA Report:**

```
OLA REPORT — Team Networking — Marzo 2026
==========================================

OLA con Service Desk:
  Tempo di presa in carico escalation:  Target < 15 min   Risultato: 12 min   OK
  Tempo di risoluzione escalation L2:   Target < 2h       Risultato: 1h 45m   OK

OLA con Team Server:
  Provisioning porte switch:            Target < 4h       Risultato: 3h 30m   OK
  Configurazione VLAN nuova:            Target < 8h       Risultato: 7h       OK

OLA con Team Security:
  Apertura regole firewall:             Target < 24h      Risultato: 20h      OK
  Analisi traffico anomalo:             Target < 1h       Risultato: 55 min   OK

Underpinning Contract — ISP Primario:
  Disponibilita link:                   Target 99.95%     Risultato: 99.98%   OK
  Tempo di risposta guasto:             Target < 4h       Risultato: 2h       OK

Underpinning Contract — ISP Secondario:
  Disponibilita link:                   Target 99.9%      Risultato: 99.92%   OK
```

### SLA Reporting Automatizzato

L'automazione del SLA reporting riduce gli errori, assicura la consistenza e libera il team da attivita manuali ripetitive.

#### Script di Estrazione Dati SLA

```python
#!/usr/bin/env python3
"""
Estrattore automatico dati SLA dal sistema ITSM.
Genera report mensile in formato JSON e HTML.
"""

import json
import datetime
from dataclasses import dataclass
from typing import List

@dataclass
class SLAMetric:
    service_name: str
    target_availability: float
    actual_availability: float
    total_downtime_minutes: int
    planned_downtime_minutes: int
    unplanned_downtime_minutes: int
    tickets_total: int
    tickets_within_sla: int
    mttr_minutes: float
    mtta_minutes: float
    csat_score: float

def calculate_sla_compliance(metrics: List[SLAMetric]) -> dict:
    """Calcola la compliance SLA aggregata."""
    results = {}
    for m in metrics:
        sla_breach = m.actual_availability < m.target_availability
        ticket_compliance = (m.tickets_within_sla / m.tickets_total * 100
                            if m.tickets_total > 0 else 100.0)
        results[m.service_name] = {
            "availability_target": m.target_availability,
            "availability_actual": m.actual_availability,
            "availability_met": not sla_breach,
            "ticket_sla_compliance": round(ticket_compliance, 1),
            "mttr_minutes": m.mttr_minutes,
            "mtta_minutes": m.mtta_minutes,
            "csat": m.csat_score,
            "status": "OK" if not sla_breach else "BREACH"
        }
    return results

def generate_sla_report(metrics: List[SLAMetric],
                        month: str,
                        output_path: str) -> None:
    """Genera il report SLA mensile in formato JSON."""
    compliance = calculate_sla_compliance(metrics)
    report = {
        "report_type": "SLA Monthly Report",
        "period": month,
        "generated_at": datetime.datetime.now().isoformat(),
        "services": compliance,
        "summary": {
            "total_services": len(metrics),
            "services_compliant": sum(
                1 for v in compliance.values()
                if v["status"] == "OK"
            ),
            "services_breached": sum(
                1 for v in compliance.values()
                if v["status"] == "BREACH"
            ),
            "overall_compliance": round(
                sum(1 for v in compliance.values()
                    if v["status"] == "OK") / len(metrics) * 100, 1
            ) if metrics else 0.0
        }
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
```

---

## Strumenti ITSM per la Reportistica

La scelta e la configurazione degli strumenti ITSM (IT Service Management) per la reportistica influenza direttamente la qualita, l'affidabilita e l'efficienza dei report prodotti. Di seguito un'analisi comparativa degli strumenti piu diffusi con focus sulle capacita di reporting.

### ServiceNow Reporting

ServiceNow e la piattaforma ITSM enterprise piu diffusa, riconosciuta come leader nel Magic Quadrant di Gartner per l'ITSM dal 2013. Le sue capacita di reporting includono:

**Funzionalita chiave di reporting:**
- **Performance Analytics (PA)**: modulo dedicato con indicatori, scorecard e dashboard interattivi. Supporta benchmark, target, trend e breakdown multidimensionali.
- **Report Builder**: interfaccia drag-and-drop per la creazione di report tabulari, grafici a barre, torte, linee e mappe di calore.
- **Scheduled Reports**: invio automatico di report via email a cadenza programmata (giornaliera, settimanale, mensile).
- **Dashboard personalizzabili**: dashboard role-based con widget interattivi, aggiornamento in tempo reale.
- **AI-powered insights**: dal 2025, ServiceNow integra agenti AI per l'analisi automatica dei dati e la generazione di insight predittivi.

**Esempio di configurazione dashboard ServiceNow per IT Operations:**

```
DASHBOARD: IT Operations Monthly Overview
==========================================

Riga 1 (KPI sintetici — gauge/scorecard):
  [Disponibilita servizi]  [Incident count P1/P2]  [Patch compliance]
  [Backup success rate]    [Change success rate]    [CSAT score]

Riga 2 (Trend — grafici a linea):
  [Trend disponibilita 6 mesi]        [Trend incidenti per severita]

Riga 3 (Dettaglio — tabelle/grafici):
  [Top 10 incidenti per categoria]    [SLA compliance per servizio]

Riga 4 (Operativo):
  [Change in programma questa settimana]  [Ticket aperti per team]
  [Vulnerabilita critiche aperte]

Filtri globali:
  - Periodo (mese corrente / ultimo trimestre / personalizzato)
  - Business unit (tutti / specifico)
  - Localita (tutti / specifico)

Refresh: ogni 5 minuti per dati operativi, ogni ora per KPI aggregati
Accesso: IT Management, CTO (role-based)
```

### Jira Service Management Reporting

Jira Service Management (JSM), parte dell'ecosistema Atlassian, si posiziona come alternativa a ServiceNow con un rapporto qualita-prezzo particolarmente vantaggioso per le organizzazioni di medie dimensioni. Le sue capacita di reporting sono in forte crescita nel periodo 2025-2026.

**Funzionalita chiave di reporting:**
- **Dashboard Jira**: dashboard personalizzabili con gadget (filtri, grafici, tabelle, contatori).
- **JQL (Jira Query Language)**: linguaggio di interrogazione potente per filtrare e aggregare dati di ticket.
- **Report predefiniti**: report su tempo di risoluzione, SLA compliance, workload del team, soddisfazione cliente.
- **Atlassian Analytics**: modulo di analisi avanzata con drill-down, cross-project analytics e integrazione con Confluence per report documentati.
- **Integrazione con Confluence**: possibilita di incorporare dashboard e report in pagine Confluence per la distribuzione ai stakeholder.

**Esempio di query JQL per reportistica SLA:**

```
# Ticket P1 e P2 che hanno violato lo SLA nel mese corrente
project = ITSM
  AND priority in (P1, P2)
  AND "SLA - Time to resolution" = breached()
  AND created >= startOfMonth()
  AND created <= endOfMonth()
  ORDER BY priority ASC, created DESC

# Ticket aperti da piu di 5 giorni senza aggiornamento
project = ITSM
  AND status != Closed
  AND status != Resolved
  AND updated <= "-5d"
  ORDER BY priority ASC, updated ASC

# Volume ticket per categoria nel trimestre corrente
project = ITSM
  AND created >= startOfQuarter()
  AND created <= endOfQuarter()
  ORDER BY category ASC
```

### Confronto Strumenti ITSM

| Criterio                          | ServiceNow                        | Jira Service Management          | ManageEngine ServiceDesk Plus   |
|-----------------------------------|-----------------------------------|----------------------------------|---------------------------------|
| **Dimensione organizzazione**     | Enterprise (1000+ dipendenti)     | PMI e Mid-Market (50-5000)       | PMI (10-1000)                   |
| **Costo indicativo annuale**      | EUR 50.000-500.000+               | EUR 5.000-50.000                 | EUR 2.000-20.000                |
| **Reporting nativo**              | Eccellente (PA module)            | Buono (in evoluzione)            | Buono                           |
| **Dashboard real-time**           | Si, avanzati                      | Si, con gadget                   | Si, base                        |
| **Report schedulati**             | Si, con template                  | Si, con Atlassian Analytics      | Si                              |
| **AI/ML per analytics**           | Si (Now Intelligence, Agenti AI)  | Si (Atlassian Intelligence)      | Limitato                        |
| **Integrazione monitoring**       | Nativa con molti strumenti        | Via marketplace (plugin)         | Integrazione con suite ME       |
| **Curva di apprendimento**        | Alta (3-6 mesi)                   | Media (1-3 mesi)                 | Bassa (2-4 settimane)           |
| **Personalizzazione report**      | Molto alta                        | Alta                             | Media                           |
| **Export formati**                 | PDF, Excel, CSV, API              | PDF, Excel, CSV, API             | PDF, Excel, CSV                 |
| **ITIL 4 alignment**             | Completo                          | Buono                            | Buono                           |

### Integrazione Multi-Strumento

In un ambiente IT reale, i dati per la reportistica provengono da molteplici strumenti. L'architettura di integrazione tipica prevede:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Prometheus  │  │    Zabbix     │  │   Datadog    │  │  Cloud       │
│  (metriche)  │  │  (metriche)  │  │  (APM/Log)   │  │  Monitoring  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       └────────────┬────┴────────────┬────┘                 │
                    ▼                 ▼                       ▼
              ┌──────────┐     ┌──────────┐           ┌──────────┐
              │ Grafana  │     │   ELK    │           │ Cloud    │
              │(dashboard│     │ (log     │           │ Console  │
              │  visual) │     │ analysis)│           │ (costi)  │
              └────┬─────┘     └────┬─────┘           └────┬─────┘
                   │                │                      │
                   └────────────────┼──────────────────────┘
                                    ▼
                            ┌──────────────┐
                            │     ITSM     │
                            │ (ServiceNow/ │
                            │  Jira SM)    │
                            │              │
                            │  ┌────────┐  │
                            │  │CMDB    │  │
                            │  │(asset) │  │
                            │  └────────┘  │
                            └──────┬───────┘
                                   │
                          ┌────────┴────────┐
                          ▼                 ▼
                   ┌──────────┐      ┌──────────┐
                   │ Report   │      │ Power BI │
                   │ Engine   │      │ / Tableau│
                   │ (auto)   │      │ (visual) │
                   └──────────┘      └──────────┘
```

**Metodi di integrazione consigliati:**

1. **API REST**: la maggior parte degli strumenti ITSM espone API REST per l'estrazione automatica dei dati. Preferire le API rispetto all'export manuale.
2. **Webhook**: per eventi in tempo reale (es. creazione incidente -> notifica in Grafana annotation).
3. **Database diretto**: per volumi elevati di dati storici, l'accesso diretto al database del ITSM (se consentito) e piu efficiente delle API.
4. **ETL (Extract-Transform-Load)**: per la creazione di un data warehouse dedicato alla reportistica, utilizzare pipeline ETL che aggreghino i dati da tutte le fonti.

---

## FinOps e Reportistica Costi Cloud

Con la crescente adozione del cloud computing, la reportistica sui costi cloud e diventata una disciplina a se stante, nota come FinOps (Financial Operations). Secondo il report State of FinOps 2026, il 30-35% della spesa cloud viene sprecata a causa di overprovisioning, risorse inutilizzate e governance finanziaria insufficiente. Una reportistica FinOps efficace consente di identificare e recuperare questi sprechi.

### Framework FinOps

Il framework FinOps si articola in tre fasi cicliche:

```
     ┌───────────────────────────────────┐
     │                                   │
     │         1. INFORMARE              │
     │    (Visibilita e allocazione)     │
     │                                   │
     └──────────────┬────────────────────┘
                    │
                    ▼
     ┌───────────────────────────────────┐
     │                                   │
     │         2. OTTIMIZZARE            │
     │    (Riduzione sprechi, right-     │
     │     sizing, reserved instances)   │
     │                                   │
     └──────────────┬────────────────────┘
                    │
                    ▼
     ┌───────────────────────────────────┐
     │                                   │
     │         3. OPERARE                │
     │    (Governance continua, policy,  │
     │     automazione, accountability)  │
     │                                   │
     └──────────────┬────────────────────┘
                    │
                    └─────────────── (ciclo continuo)
```

**Capacita FinOps prioritarie (State of FinOps 2026):**
1. Allocazione dei costi (cost allocation / tagging)
2. Forecasting e budgeting
3. Reporting e analytics
4. Ottimizzazione workload
5. Gestione anomalie di spesa

### Dashboard dei Costi Cloud

Un dashboard FinOps efficace deve fornire visibilita immediata sulla spesa cloud, i trend e le opportunita di ottimizzazione.

**Struttura consigliata del dashboard FinOps:**

```
DASHBOARD FINOPS — Panoramica Mensile
======================================

Riga 1 — KPI principali (scorecard):
  [Spesa mese corrente]     [Variazione vs mese prec.]    [Variazione vs budget]
  [Costo giornaliero medio] [Savings realizzati]          [Waste identificato]

Riga 2 — Trend e previsioni (grafici a linea):
  [Spesa giornaliera mese corrente vs precedente]
  [Forecast fine mese vs budget]

Riga 3 — Breakdown per dimensione (grafici a barre/torta):
  [Spesa per servizio cloud (EC2, RDS, S3...)]
  [Spesa per team/progetto (tag-based)]
  [Spesa per ambiente (prod/staging/dev)]

Riga 4 — Ottimizzazione (tabelle):
  [Top 10 risorse piu costose]
  [Risorse idle da piu di 7 giorni]
  [Suggerimenti di right-sizing]
  [Coverage Reserved Instances / Savings Plans]

Riga 5 — Anomalie (alert):
  [Anomalie di spesa rilevate questa settimana]
  [Risorse con crescita costo > 20% vs media]
```

**Configurazione Grafana per costi cloud (con plugin CloudWatch/Azure Monitor):**

```json
{
  "dashboard": {
    "title": "FinOps — Cloud Cost Overview",
    "panels": [
      {
        "title": "Spesa Cloud Giornaliera (30 giorni)",
        "type": "timeseries",
        "datasource": "CloudWatch",
        "targets": [
          {
            "namespace": "AWS/Billing",
            "metricName": "EstimatedCharges",
            "dimensions": {"Currency": "USD"},
            "period": "86400",
            "stat": "Maximum"
          }
        ]
      },
      {
        "title": "Spesa per Servizio AWS",
        "type": "piechart",
        "datasource": "Athena-CUR",
        "targets": [
          {
            "rawSQL": "SELECT line_item_product_code AS service, SUM(line_item_unblended_cost) AS cost FROM cur_report WHERE month = '${__from:date:M}' GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
          }
        ]
      },
      {
        "title": "Coverage Reserved Instances",
        "type": "gauge",
        "thresholds": [
          {"value": 50, "color": "red"},
          {"value": 70, "color": "yellow"},
          {"value": 80, "color": "green"}
        ]
      }
    ]
  }
}
```

### Reportistica FinOps Mensile

```
================================================================
       REPORT FINOPS MENSILE — [MESE] [ANNO]
================================================================

1. RIEPILOGO SPESA
----------------------------------------------------------------
  Spesa totale cloud:             EUR 18.450
  Budget mensile:                 EUR 20.000
  Variazione vs budget:           -7.8% (sotto budget)         OK
  Variazione vs mese precedente:  +4.2%                         ATTENZIONE
  Forecast fine mese:             EUR 19.100 (entro budget)    OK

2. BREAKDOWN PER PROVIDER
----------------------------------------------------------------
  AWS:                            EUR 12.300  (66.7%)
  Azure:                          EUR 4.850   (26.3%)
  GCP:                            EUR 1.300   (7.0%)

3. BREAKDOWN PER AMBIENTE
----------------------------------------------------------------
  Produzione:                     EUR 13.200  (71.5%)
  Staging:                        EUR 2.800   (15.2%)
  Sviluppo:                       EUR 1.650   (8.9%)
  Test/QA:                        EUR 800     (4.3%)

4. TOP 10 SERVIZI PER COSTO
----------------------------------------------------------------
  1. EC2 Instances (AWS)          EUR 5.200
  2. RDS Database (AWS)           EUR 2.800
  3. Azure Virtual Machines       EUR 2.100
  4. S3 Storage (AWS)             EUR 1.400
  5. Azure Blob Storage           EUR 1.200
  6. EKS Kubernetes (AWS)         EUR 1.100
  7. CloudFront CDN (AWS)         EUR 900
  8. Azure SQL Database           EUR 850
  9. Lambda Functions (AWS)       EUR 500
  10. GCE Instances (GCP)         EUR 480

5. OTTIMIZZAZIONE E RISPARMIO
----------------------------------------------------------------
  Risparmi realizzati questo mese:
    - Right-sizing 8 VM sovradimensionate:    EUR 420/mese
    - Spegnimento ambienti dev fuori orario:  EUR 380/mese
    - Migrazione storage a tier freddo:       EUR 150/mese
    Totale risparmi realizzati:               EUR 950/mese

  Opportunita di risparmio identificate:
    - 12 risorse idle da > 14 giorni:         EUR 680/mese stimati
    - 5 VM con CPU < 5% media:                EUR 350/mese stimati
    - RI non rinnovate su 3 istanze:          EUR 1.200/mese stimati
    Totale opportunita:                       EUR 2.230/mese

  Coverage analisi:
    - Reserved Instances coverage:  72% (target: > 80%)  ATTENZIONE
    - Savings Plans coverage:       65% (target: > 75%)  ATTENZIONE

6. ANOMALIE DI SPESA
----------------------------------------------------------------
  - Picco anomalo su Lambda (12/03): +240% vs media giornaliera
    Causa: loop in funzione di elaborazione batch. Risolto il 13/03.
    Costo aggiuntivo: EUR 85.
  - Crescita progressiva costo RDS: +15% in 3 mesi
    Causa: crescita dati non monitorata. Azione: purge dati obsoleti.

================================================================
```

### Anomaly Detection sui Costi

L'identificazione automatica delle anomalie di spesa e fondamentale per prevenire sforamenti di budget. Le tecniche principali includono:

**Soglie statiche**: definire budget giornalieri e mensili per ogni servizio/team e generare alert quando la soglia viene superata. Semplice ma efficace per la maggior parte dei casi.

**Soglie dinamiche**: utilizzare la media mobile e la deviazione standard per definire soglie che si adattano automaticamente ai pattern di spesa normali. Un alert scatta quando la spesa supera la media + 2 deviazioni standard.

**Machine learning**: i servizi nativi dei cloud provider (AWS Cost Anomaly Detection, Azure Cost Alerts) utilizzano modelli ML per identificare pattern di spesa anomali in modo piu sofisticato. Sono consigliati per ambienti complessi con molti servizi.

**Configurazione alert di esempio:**

```yaml
# Configurazione alert costi cloud (esempio YAML per automazione)
cost_alerts:
  - name: "Budget mensile superato 80%"
    condition: monthly_spend >= monthly_budget * 0.80
    severity: warning
    notify:
      - email: it-manager@azienda.it
      - slack: "#finops-alerts"
    message: |
      ATTENZIONE: La spesa cloud del mese corrente ha raggiunto
      l'80% del budget mensile. Spesa attuale: {current_spend},
      Budget: {monthly_budget}. Verificare e prendere azioni
      correttive se necessario.

  - name: "Budget mensile superato 100%"
    condition: monthly_spend >= monthly_budget
    severity: critical
    notify:
      - email: cto@azienda.it
      - email: it-manager@azienda.it
      - slack: "#finops-alerts"
      - pagerduty: finops-escalation
    message: |
      CRITICO: La spesa cloud del mese corrente ha superato
      il budget mensile. Spesa attuale: {current_spend},
      Budget: {monthly_budget}. Azione immediata richiesta.

  - name: "Spike giornaliero anomalo"
    condition: daily_spend > avg_daily_spend_30d * 2.0
    severity: warning
    notify:
      - slack: "#finops-alerts"
    message: |
      Rilevato spike anomalo nella spesa giornaliera.
      Spesa oggi: {daily_spend}, Media 30 giorni: {avg_daily}.
      Investigare la causa.

  - name: "Risorsa idle > 7 giorni"
    condition: resource_cpu_avg_7d < 1% AND resource_network_7d < 1MB
    severity: info
    notify:
      - email: resource_owner
    message: |
      La risorsa {resource_id} risulta inutilizzata da 7 giorni.
      Costo stimato mensile: {estimated_monthly_cost}.
      Valutare la dismissione o lo spegnimento.
```

---

## Alerting e Notifiche Automatizzate

Un sistema di alerting efficace e il collegamento tra il monitoring passivo e l'azione operativa. Senza alerting, i dati di monitoring restano inutilizzati fino a quando un utente non segnala un problema. Con l'alerting, il team IT viene informato proattivamente, spesso prima che gli utenti percepiscano l'impatto.

### Architettura di Alerting

L'architettura di alerting moderna segue il pattern "monitor → evaluate → route → notify → track":

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│  Metriche  │───>│ Regole di  │───>│  Routing e │───>│  Canali di │
│  (Prom.,   │    │ Valutazione│    │  Grouping  │    │  Notifica  │
│  Zabbix,   │    │ (soglie,   │    │ (silencing,│    │  (email,   │
│  Datadog)  │    │  predict.) │    │  dedup,    │    │  Slack,    │
│            │    │            │    │  escalation│    │  PagerDuty,│
└────────────┘    └────────────┘    │  )         │    │  SMS, tel.)│
                                    └────────────┘    └────────────┘
                                                             │
                                                             ▼
                                                      ┌────────────┐
                                                      │   ITSM     │
                                                      │  (auto-    │
                                                      │  creazione │
                                                      │  ticket)   │
                                                      └────────────┘
```

### Regole di Alerting con Prometheus

Prometheus e il sistema di alerting open-source piu diffuso. Le regole di alerting vengono definite in file YAML e valutate periodicamente.

**Esempio completo di regole di alerting per IT Operations:**

```yaml
# /etc/prometheus/rules/it-operations.yml
groups:
  - name: availability
    interval: 30s
    rules:
      - alert: InstanceDown
        expr: up == 0
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Istanza {{ $labels.instance }} non raggiungibile"
          description: >
            L'istanza {{ $labels.instance }} del job {{ $labels.job }}
            non risponde da oltre 5 minuti. Verificare lo stato
            del server e della rete.
          runbook_url: "https://wiki.azienda.it/runbook/instance-down"

      - alert: HighCPUUsage
        expr: >
          100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
        for: 15m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "CPU elevata su {{ $labels.instance }}"
          description: >
            L'utilizzo CPU su {{ $labels.instance }} supera l'85%
            da oltre 15 minuti (attuale: {{ $value | printf \"%.1f\" }}%).
          runbook_url: "https://wiki.azienda.it/runbook/high-cpu"

      - alert: HighMemoryUsage
        expr: >
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 90
        for: 10m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Memoria critica su {{ $labels.instance }}"
          description: >
            L'utilizzo RAM su {{ $labels.instance }} supera il 90%
            da oltre 10 minuti (attuale: {{ $value | printf \"%.1f\" }}%).

      - alert: DiskSpaceLow
        expr: >
          (1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}
          / node_filesystem_size_bytes) * 100 > 85
        for: 30m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Spazio disco basso su {{ $labels.instance }}:{{ $labels.mountpoint }}"
          description: >
            Lo spazio disco su {{ $labels.instance }} mountpoint
            {{ $labels.mountpoint }} supera l'85%
            (attuale: {{ $value | printf \"%.1f\" }}%).

      - alert: DiskSpaceCritical
        expr: >
          (1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}
          / node_filesystem_size_bytes) * 100 > 95
        for: 10m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Spazio disco CRITICO su {{ $labels.instance }}:{{ $labels.mountpoint }}"

  - name: services
    interval: 30s
    rules:
      - alert: ServiceResponseSlow
        expr: >
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
          team: application
        annotations:
          summary: "Tempo di risposta elevato per {{ $labels.service }}"
          description: >
            Il P95 del tempo di risposta di {{ $labels.service }}
            supera i 2 secondi (attuale: {{ $value | printf \"%.2f\" }}s).

      - alert: HighErrorRate
        expr: >
          rate(http_requests_total{status=~"5.."}[5m])
          / rate(http_requests_total[5m]) * 100 > 5
        for: 5m
        labels:
          severity: critical
          team: application
        annotations:
          summary: "Tasso di errore elevato per {{ $labels.service }}"

  - name: backup
    interval: 60s
    rules:
      - alert: BackupJobFailed
        expr: backup_last_status == 0
        for: 1m
        labels:
          severity: high
          team: infrastructure
        annotations:
          summary: "Backup fallito: {{ $labels.job_name }}"
          description: >
            Il job di backup {{ $labels.job_name }} per il target
            {{ $labels.target }} e fallito. Verificare i log del
            sistema di backup.

      - alert: BackupTooOld
        expr: >
          (time() - backup_last_success_timestamp) > 86400 * 2
        for: 1h
        labels:
          severity: high
          team: infrastructure
        annotations:
          summary: "Backup obsoleto: {{ $labels.job_name }}"
          description: >
            L'ultimo backup riuscito di {{ $labels.job_name }}
            risale a piu di 48 ore fa.

  - name: capacity_forecast
    interval: 300s
    rules:
      - alert: DiskWillFillIn30Days
        expr: >
          predict_linear(
            node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}[7d], 30*86400
          ) < 0
        for: 1h
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Disco esaurito entro 30 giorni su {{ $labels.instance }}"
          description: >
            Secondo la proiezione lineare basata sugli ultimi 7 giorni,
            il disco {{ $labels.mountpoint }} su {{ $labels.instance }}
            si esaurira entro 30 giorni. Pianificare l'espansione.
```

### Escalation Automatica

L'escalation automatica garantisce che gli alert non rimangano senza risposta. La configurazione dell'Alertmanager di Prometheus segue un modello a cascata:

```yaml
# /etc/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.azienda.it:587'
  smtp_from: 'alertmanager@azienda.it'
  smtp_auth_username: 'alertmanager'
  smtp_require_tls: true

route:
  receiver: 'default-receiver'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Alert critici: notifica immediata + escalation
    - match:
        severity: critical
      receiver: 'critical-receiver'
      group_wait: 10s
      repeat_interval: 1h
      routes:
        - match:
            alertname: InstanceDown
          receiver: 'pagerduty-infra'

    # Alert di sicurezza: team security dedicato
    - match:
        team: security
      receiver: 'security-team'
      group_wait: 10s

    # Alert warning: notifica standard
    - match:
        severity: warning
      receiver: 'warning-receiver'
      repeat_interval: 8h

receivers:
  - name: 'default-receiver'
    email_configs:
      - to: 'it-ops@azienda.it'

  - name: 'critical-receiver'
    email_configs:
      - to: 'it-ops@azienda.it'
      - to: 'it-manager@azienda.it'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/xxx'
        channel: '#it-critical'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: 'pagerduty-infra'
    pagerduty_configs:
      - service_key: '<PAGERDUTY_SERVICE_KEY>'
        severity: '{{ .GroupLabels.severity }}'

  - name: 'security-team'
    email_configs:
      - to: 'security@azienda.it'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/yyy'
        channel: '#security-alerts'

  - name: 'warning-receiver'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/zzz'
        channel: '#it-warnings'

inhibit_rules:
  # Se un'istanza e down, sopprimere gli alert di servizio correlati
  - source_match:
      alertname: InstanceDown
    target_match_re:
      alertname: '(HighCPU|HighMemory|DiskSpace).*'
    equal: ['instance']
```

### Riduzione del Rumore di Alerting

L'alert fatigue e uno dei problemi piu gravi nella gestione degli alert IT. Quando il team riceve troppi alert (molti dei quali non azionabili), tende a ignorarli, aumentando il rischio di non rispondere a problemi reali. Le strategie di riduzione del rumore includono:

**Grouping**: raggruppare gli alert correlati in un unico messaggio. Se 10 servizi sullo stesso server generano alert contemporaneamente, il team riceve un unico alert che li elenca tutti, anziche 10 notifiche separate.

**Silencing**: silenziare temporaneamente gli alert durante le finestre di manutenzione programmata. Se si sa che un server verra riavviato durante la manutenzione, gli alert di InstanceDown per quel server devono essere silenziati per la durata della finestra.

**Inhibition**: sopprimere gli alert derivati quando l'alert primario e gia attivo. Se un server e irraggiungibile (InstanceDown), non ha senso ricevere anche gli alert di CPU, memoria e disco per lo stesso server.

**Deduplicazione**: se lo stesso alert scatta piu volte in rapida successione, inviare una sola notifica con un contatore di occorrenze.

**Tuning delle soglie**: rivedere periodicamente le soglie degli alert. Se un alert scatta 50 volte al mese e non genera mai un'azione, la soglia e troppo bassa o l'alert non e utile. Alzare la soglia o rimuovere l'alert.

**Metriche di qualita dell'alerting:**

| Metrica                        | Formula                                         | Target          |
|--------------------------------|-------------------------------------------------|-----------------|
| Alert-to-incident ratio        | Alert totali / Incidenti aperti                 | < 5:1           |
| False positive rate            | Alert senza azione / Alert totali               | < 20%           |
| Alert noise reduction trend    | Variazione % alert mensili dopo tuning          | Decrescente     |
| MTTA (da alert a ack)         | Media tempo tra alert firing e acknowledgement  | < 5 min (P1)    |
| Alert coverage                 | Incidenti con alert preventivo / Incidenti tot. | > 80%           |

---

## Miglioramento Continuo della Reportistica

La reportistica IT non e un prodotto statico: deve evolversi continuamente per rimanere rilevante, accurata e utile. Il modello di miglioramento continuo ITIL 4 fornisce un framework strutturato per questa evoluzione.

### Modello ITIL 4 di Continual Improvement

ITIL 4 definisce un modello di miglioramento continuo in sette fasi, applicabile anche alla reportistica IT. Rispetto a ITIL v3, ITIL 4 aggiunge una fase cruciale ("Agire") tra la pianificazione e la verifica, enfatizzando l'esecuzione concreta dei miglioramenti.

```
1. Qual e la visione?
   └──> Allineare la reportistica agli obiettivi di business

2. Dove siamo ora?
   └──> Assessment della reportistica attuale (completezza,
        accuratezza, tempestivita, utilita percepita)

3. Dove vogliamo arrivare?
   └──> Definire lo stato target della reportistica
        (automazione, copertura, frequenza, integrazione)

4. Come ci arriviamo?
   └──> Piano di miglioramento con azioni concrete,
        priorita, timeline e responsabili

5. Agire (NUOVA in ITIL 4)
   └──> Eseguire le azioni di miglioramento pianificate.
        Questa fase trasforma le buone intenzioni in risultati

6. Ci siamo arrivati?
   └──> Verificare che i miglioramenti abbiano prodotto
        i risultati attesi (metriche prima/dopo)

7. Come manteniamo lo slancio?
   └──> Rendere il miglioramento parte della cultura,
        celebrare i successi, pianificare il prossimo ciclo
```

**Applicazione pratica alla reportistica IT:**

```
PIANO DI MIGLIORAMENTO REPORTISTICA — 2026
============================================

DOVE SIAMO ORA (Assessment Q1 2026):
  - Report mensile: manuale, richiede 2 giorni di lavoro
  - Dashboard: Grafana base, solo metriche infrastrutturali
  - SLA reporting: manuale in Excel, spesso in ritardo
  - Copertura: 60% dei servizi critici monitorati
  - Feedback stakeholder: "report troppo tecnici, poco utili"
  - Score maturita reportistica: Livello 2 (Ripetibile)

DOVE VOGLIAMO ARRIVARE (Target Q4 2026):
  - Report mensile: automatizzato al 80%, revisione in 2h
  - Dashboard: Grafana avanzato con KPI business + tecnici
  - SLA reporting: automatizzato dal sistema ITSM
  - Copertura: 95% dei servizi critici monitorati
  - Feedback stakeholder: "report utili e orientati al business"
  - Score maturita reportistica: Livello 3 (Definito)

AZIONI DI MIGLIORAMENTO:
  Q2 2026:
    - [A1] Automazione estrazione dati per report mensile
    - [A2] Aggiunta metriche business al dashboard Grafana
    - [A3] Ridisegno executive summary con focus business

  Q3 2026:
    - [A4] Integrazione ITSM con monitoring per SLA automatico
    - [A5] Estensione monitoring ai servizi mancanti
    - [A6] Workshop con stakeholder per calibrare i report

  Q4 2026:
    - [A7] Automazione completa generazione e invio report
    - [A8] Implementazione feedback loop strutturato
    - [A9] Assessment maturita e pianificazione 2027
```

### Maturita della Reportistica IT

La maturita della reportistica IT puo essere valutata secondo un modello a 5 livelli, ispirato al CMMI (Capability Maturity Model Integration):

| Livello | Nome           | Caratteristiche                                                                                              |
|---------|----------------|--------------------------------------------------------------------------------------------------------------|
| 1       | Iniziale       | Nessun report strutturato. Dati raccolti ad hoc su richiesta. Nessun dashboard. Nessun KPI definito.        |
| 2       | Ripetibile     | Report mensile manuale. Alcuni KPI definiti. Dashboard base di monitoring. Formati inconsistenti.            |
| 3       | Definito       | Report standardizzati con template. KPI formali con target. Dashboard multi-livello. Processo documentato.   |
| 4       | Gestito        | Report automatizzati. KPI rivisti trimestralmente. Dashboard role-based. Feedback loop con stakeholder.      |
| 5       | Ottimizzato    | Report predittivi (trend, forecast). AI/ML per insight. Continuous improvement integrato. Real-time.         |

**Assessment checklist per ogni livello:**

```
LIVELLO 1 — INIZIALE
  [ ] Nessun report ricorrente strutturato
  [ ] Dati disponibili solo su richiesta specifica
  [ ] Nessun KPI definito formalmente

LIVELLO 2 — RIPETIBILE
  [x] Report mensile prodotto regolarmente
  [x] Almeno 5 KPI definiti con target
  [x] Dashboard di monitoring base operativo
  [ ] Formati e template standardizzati
  [ ] Processo di produzione documentato

LIVELLO 3 — DEFINITO
  [ ] Template di report standardizzati e versionati
  [ ] KPI con definizioni formali (formula, fonte, responsabile)
  [ ] Dashboard multi-livello (tecnico, management, executive)
  [ ] Processo di reporting documentato e assegnato
  [ ] Feedback periodico dagli stakeholder
  [ ] Versioni del report per audience diverse

LIVELLO 4 — GESTITO
  [ ] Automazione >= 80% della raccolta dati
  [ ] Revisione trimestrale dei KPI e delle soglie
  [ ] Dashboard role-based con accesso controllato
  [ ] SLA reporting integrato con il sistema ITSM
  [ ] Analisi trend e confronto con periodi precedenti
  [ ] Report di capacity planning predittivo

LIVELLO 5 — OTTIMIZZATO
  [ ] Report generati automaticamente e inviati senza intervento
  [ ] Forecast predittivi basati su ML/analisi statistica
  [ ] Insight automatici che evidenziano anomalie e opportunita
  [ ] Continuous improvement della reportistica con metriche
  [ ] Real-time dashboard con aggiornamento < 1 minuto
  [ ] Integrazione completa monitoring + ITSM + CMDB + FinOps
```

### Ciclo di Revisione dei KPI

I KPI non sono immutabili. Devono essere rivisti periodicamente per assicurarsi che rimangano rilevanti, misurabili e allineati agli obiettivi di business. Il ciclo di revisione consigliato prevede:

**Revisione trimestrale (operativa):**
- Verificare che i dati per il calcolo del KPI siano accurati e consistenti.
- Controllare che i target siano ancora realistici (ne troppo facili ne irraggiungibili).
- Identificare KPI che non generano mai azioni (candidati alla rimozione).
- Aggiungere KPI temporanei per aree di focus specifico (es. durante un progetto di migrazione).

**Revisione annuale (strategica):**
- Rivalutare l'intero set di KPI alla luce degli obiettivi di business aggiornati.
- Eliminare KPI obsoleti o ridondanti.
- Aggiungere KPI per nuove aree (es. cloud, sicurezza, AI).
- Ricalcolare i target sulla base dei trend storici e dei benchmark di settore.
- Coinvolgere gli stakeholder nella definizione dei nuovi KPI.

**Criteri per la selezione di un buon KPI:**

| Criterio    | Domanda chiave                                                        | Esempio positivo                | Esempio negativo                    |
|-------------|-----------------------------------------------------------------------|----------------------------------|--------------------------------------|
| Specifico   | Misura qualcosa di preciso?                                           | MTTR per incidenti P1            | "Qualita del servizio"              |
| Misurabile  | Puo essere calcolato automaticamente dai dati disponibili?            | % uptime dal monitoring          | "Percezione di affidabilita"        |
| Azionabile  | Un cambiamento nel valore genera un'azione concreta?                  | Patch compliance < 95% -> azione | "Numero totale di server"           |
| Rilevante   | E importante per gli obiettivi di business?                           | SLA compliance per servizio ERP  | "Numero di email inviate dal team"  |
| Temporale   | Ha una frequenza di misurazione definita?                             | Mensile, con trend 6 mesi        | "Quando capita"                     |

---

## Reportistica di Sicurezza IT

La reportistica di sicurezza IT e una componente sempre piu critica del reporting operativo, data la crescente frequenza e sofisticazione degli attacchi informatici. Questa sezione copre i report di sicurezza chiave che il team IT deve produrre regolarmente.

### Security Posture Report

Il Security Posture Report fornisce una fotografia dello stato complessivo della sicurezza dell'infrastruttura IT. Viene prodotto mensilmente e presentato al CISO e al management.

```
================================================================
       SECURITY POSTURE REPORT — [MESE] [ANNO]
================================================================

1. RIEPILOGO STATO SICUREZZA
----------------------------------------------------------------
  Stato complessivo: [GIALLO]

  Indicatori chiave:
    Vulnerabilita critiche aperte:     0          OK
    Vulnerabilita alte aperte:         3          ATTENZIONE
    Patch compliance:                  94.3%      ATTENZIONE (< 95%)
    MFA coverage:                      96%        OK
    Endpoint EDR coverage:             98%        OK
    Backup encryption:                 100%       OK
    Ultimo DR test riuscito:           2026-03-15 OK (< 90 giorni)
    Security awareness training:       85% completato  ATTENZIONE

2. VULNERABILITY MANAGEMENT
----------------------------------------------------------------
  Scanner utilizzato: [Tenable Nessus / Qualys / OpenVAS]
  Ultima scansione completa: [GG/MM/AAAA]
  Prossima scansione: [GG/MM/AAAA]

  Riepilogo vulnerabilita:
    Severita     Aperte   Nuove mese  Risolte mese  Trend
    ──────────────────────────────────────────────────────
    Critica      0        2           2             Stabile
    Alta         3        4           5             ↓ Miglior.
    Media        12       6           8             ↓ Miglior.
    Bassa        28       10          7             ↑ Peggiorm.
    Info         45       15          10            ↑ Peggiorm.
    ──────────────────────────────────────────────────────
    Totale       88       37          32

  MTTR vulnerabilita (Mean Time To Remediate):
    Critica:     3 giorni (target: < 7 giorni)     OK
    Alta:        12 giorni (target: < 30 giorni)   OK
    Media:       45 giorni (target: < 90 giorni)   OK

  Top 5 vulnerabilita piu urgenti:
    1. CVE-2026-XXXX — Apache Log4j RCE (3 server)
       Stato: Patch in test, deployment previsto entro 48h
    2. CVE-2026-YYYY — OpenSSL buffer overflow (5 server)
       Stato: Patch approvata, finestra di manutenzione sabato
    3. CVE-2026-ZZZZ — SQL Server elevation of privilege
       Stato: In valutazione, test in corso

3. EVENTI DI SICUREZZA
----------------------------------------------------------------
  Totale eventi di sicurezza analizzati:     1.245
  False positive:                            1.180 (94.8%)
  True positive (incidenti di sicurezza):    65

  Incidenti di sicurezza per categoria:
    Phishing tentato:                 42
    Malware bloccato:                 12
    Accesso non autorizzato tentato:  8
    Policy violation:                 3
    Data exfiltration tentata:        0

  Incidenti che hanno richiesto intervento:  15
  Incidenti con impatto su dati/servizi:     0

4. COMPLIANCE
----------------------------------------------------------------
  Framework di riferimento: ISO 27001, GDPR

  Area di compliance          Stato       Note
  ──────────────────────────────────────────────
  Access management           Conforme    MFA attivo, review trimestrale
  Data protection             Conforme    Encryption at rest e in transit
  Logging e audit trail       Conforme    Log retention 12 mesi
  Incident response plan      Conforme    Ultimo test: 2026-02
  Business continuity         Parziale    DR test pianificato Q2
  Vendor risk management      Parziale    3 vendor senza valutazione
  Security awareness          In corso    85% dipendenti formati

================================================================
```

### Vulnerability Management Reporting

Il reporting della gestione delle vulnerabilita deve andare oltre il semplice conteggio. Le metriche chiave da tracciare includono:

| Metrica                          | Definizione                                              | Target consigliato    |
|----------------------------------|----------------------------------------------------------|-----------------------|
| Vuln. critiche aperte           | Vulnerabilita con CVSS >= 9.0 non ancora risolte         | 0                     |
| MTTR per severita               | Tempo medio dalla scoperta alla remediation              | Critica < 7 gg, Alta < 30 gg |
| Scan coverage                   | % di asset scansionati almeno una volta nel mese         | > 95%                 |
| Reopen rate                     | % di vulnerabilita risolte che si ripresentano            | < 5%                  |
| Aging delle vulnerabilita       | Distribuzione eta delle vulnerabilita aperte              | Nessuna > 90 gg (alta+) |
| Risk score complessivo          | Score aggregato ponderato per severita e impatto          | Trend decrescente     |
| Remediation velocity            | Numero di vulnerabilita risolte per settimana             | Trend crescente       |
| Exception rate                  | % di vulnerabilita con eccezione approvata (risk accepted)| < 10%                 |

### Compliance e Audit Reporting

I report di compliance documentano la conformita dell'organizzazione a standard, normative e policy interne. Sono particolarmente importanti durante gli audit esterni (ISO 27001, SOC 2, GDPR) e devono essere accurati e completi.

**Template sintetico di compliance report:**

```
COMPLIANCE REPORT — [STANDARD] — [PERIODO]
============================================

Standard di riferimento: ISO/IEC 27001:2022
Periodo di valutazione: Q1 2026 (Gennaio-Marzo)
Valutatore: [Internal Audit / Consulente esterno]

RIEPILOGO:
  Controlli totali valutati:        93
  Controlli conformi:               82 (88.2%)
  Controlli parzialmente conformi:  8 (8.6%)
  Controlli non conformi:           3 (3.2%)

NON CONFORMITA RILEVATE:

  NC-001: A.8.8 — Gestione vulnerabilita tecniche
    Descrizione: Non tutti gli asset sono inclusi nel programma
                 di vulnerability scanning (copertura 89%, target 95%)
    Severita: Minore
    Azione correttiva: Estensione scansioni a tutti gli asset entro Q2
    Responsabile: Security Manager
    Scadenza: 30/06/2026

  NC-002: A.7.2.2 — Consapevolezza sicurezza informazioni
    Descrizione: 15% dei dipendenti non ha completato il training
                 annuale di security awareness
    Severita: Minore
    Azione correttiva: Campagna di sollecito + sessioni aggiuntive
    Responsabile: HR Manager + Security Manager
    Scadenza: 30/04/2026

  NC-003: A.15.1 — Sicurezza nelle relazioni con i fornitori
    Descrizione: 3 fornitori critici senza valutazione di sicurezza
                 aggiornata nell'ultimo anno
    Severita: Maggiore
    Azione correttiva: Avvio assessment di sicurezza vendor
    Responsabile: Procurement + Security Manager
    Scadenza: 31/05/2026
```

---

## Framework di Governance della Reportistica

La governance della reportistica IT definisce chi produce cosa, con quale frequenza, per quale audience e con quali standard di qualita. Senza una governance formale, i report proliferano in modo incontrollato, con duplicazioni, inconsistenze e sprechi di tempo.

### Data Governance per i Report IT

La data governance applicata alla reportistica IT assicura che i dati utilizzati nei report siano accurati, consistenti, tempestivi e affidabili. I principi chiave includono:

**Single Source of Truth (SSOT):** per ogni dato o metrica, deve esistere un'unica fonte autorevole. Se la disponibilita del servizio viene calcolata sia dal monitoring che dal ticketing, una sola fonte deve essere designata come autorevole per il report ufficiale.

**Data Quality Framework:**

| Dimensione          | Definizione                                              | Come verificare                                           |
|---------------------|----------------------------------------------------------|-----------------------------------------------------------|
| Accuratezza         | I dati riflettono la realta                              | Confronto con campione manuale                            |
| Completezza         | Nessun dato mancante                                    | Verifica copertura asset e periodi                        |
| Consistenza         | Stessa metrica = stesso valore in fonti diverse          | Riconciliazione cross-system periodica                    |
| Tempestivita        | I dati sono disponibili quando servono                   | Verifica SLA pipeline dati                                |
| Tracciabilita       | Ogni dato ha una fonte identificabile                    | Metadata di provenienza su ogni dataset                   |
| Validita            | I dati rispettano i formati e i range attesi             | Regole di validazione automatiche                         |

**Processo di riconciliazione dati:**

```
RICONCILIAZIONE DATI TRIMESTRALE
=================================

1. Estrarre la lista di asset dal CMDB
2. Confrontare con la lista di host nel sistema di monitoring
3. Identificare discrepanze:
   - Asset nel CMDB ma non nel monitoring (monitoring gap)
   - Host nel monitoring ma non nel CMDB (CMDB non aggiornato)
4. Verificare la coerenza delle metriche:
   - Disponibilita dal monitoring vs registro incidenti ITSM
   - Conteggio ticket dal ITSM vs report manuale
   - Dati di costo cloud dal provider vs tool FinOps
5. Documentare le discrepanze trovate e le azioni correttive
6. Aggiornare CMDB e monitoring per allineare le fonti
7. Misurare il miglioramento rispetto al trimestre precedente

Metriche di qualita dati:
  - % asset coperti da monitoring: target > 95%
  - % discrepanza CMDB vs monitoring: target < 5%
  - % metriche con varianza cross-system > 2%: target < 3%
```

### Catalogo dei Report

Un catalogo formale dei report IT evita duplicazioni, chiarisce responsabilita e assicura che ogni stakeholder riceva le informazioni necessarie con la frequenza appropriata.

```
CATALOGO REPORT IT — Versione 2.0 (aggiornamento: 2026-04)
============================================================

ID       Nome                         Frequenza   Prodotto da    Audience
─────────────────────────────────────────────────────────────────────────
RPT-001  Report Mensile IT            Mensile     IT Operations  IT Mgmt, CTO
RPT-002  SLA Report                   Mensile     IT Operations  IT Mgmt, Business
RPT-003  Security Posture Report      Mensile     Security Team  CISO, CTO
RPT-004  Compliance Report            Trimest.    Security Team  CISO, Audit, Legal
RPT-005  FinOps Cloud Cost Report     Mensile     Cloud Team     IT Mgmt, CFO
RPT-006  Capacity Planning Forecast   Trimest.    IT Operations  IT Mgmt
RPT-007  Budget Tracking Report       Mensile     IT Mgmt        CFO, CTO
RPT-008  Change Management Report     Mensile     Change Mgr     IT Mgmt, CAB
RPT-009  Incident Trend Analysis      Mensile     Service Desk   IT Mgmt
RPT-010  Executive IT Summary         Trimest.    CTO            Board, CEO
RPT-011  Vulnerability Scan Report    Settimanale Security Team  CISO, IT Ops
RPT-012  Backup Status Report         Settimanale IT Operations  IT Mgmt
RPT-013  Daily Operations Dashboard   Giornaliero IT Operations  Team IT (auto)
RPT-014  Post-Incident Report (RCA)   Ad hoc      Incident Mgr   IT Mgmt, Business
RPT-015  DR Test Report               Semestrale  IT Operations  IT Mgmt, CISO, Board

Per ogni report:
  - Template versionato e archiviato in repository documentale
  - Responsabile designato per produzione e qualita
  - Processo di revisione e approvazione prima della distribuzione
  - Canale di distribuzione definito (email, portale, presentazione)
  - Data di scadenza / prossima revisione template
```

### Revisione e Ciclo di Vita dei Report

Ogni report ha un ciclo di vita che comprende creazione, utilizzo, evoluzione e eventuale dismissione. Gestire attivamente questo ciclo evita la proliferazione incontrollata di report che nessuno legge.

**Fasi del ciclo di vita:**

1. **Proposta**: un nuovo report viene richiesto da uno stakeholder o identificato come necessario dal team IT. Documentare lo scopo, l'audience, la frequenza e il contenuto previsto.

2. **Creazione**: sviluppo del template, configurazione delle fonti dati, automazione della raccolta, test di accuratezza. Review con gli stakeholder prima del rilascio.

3. **Rilascio e feedback**: produzione del primo report e distribuzione agli stakeholder. Raccolta di feedback strutturato entro 30 giorni.

4. **Iterazione**: aggiustamento del contenuto, del formato e della frequenza in base al feedback. Ogni iterazione viene documentata e versionata.

5. **Manutenzione**: produzione regolare del report secondo il calendario. Aggiornamento periodico del template (almeno annuale). Verifica periodica che il report venga effettivamente letto e utilizzato.

6. **Revisione annuale**: valutazione della rilevanza del report. Domande chiave: viene ancora letto? Genera azioni? E duplicato da un altro report? Il contenuto e ancora allineato agli obiettivi di business?

7. **Dismissione**: se un report non e piu utile, viene formalmente dismesso. Documentare la motivazione della dismissione e informare gli stakeholder.

**Metriche di utilizzo dei report:**

| Metrica                             | Come misurare                                               | Target             |
|-------------------------------------|-------------------------------------------------------------|--------------------|
| Open rate                           | % di destinatari che aprono il report/email                 | > 70%              |
| Feedback ricevuto                   | Numero di commenti/domande generati dal report              | > 0 per ciclo      |
| Azioni generate                     | Numero di azioni decise sulla base del report               | > 0 per ciclo      |
| Tempo di produzione                 | Ore-uomo per produrre il report                             | Decrescente        |
| Accuratezza percepita               | Score da survey periodica (1-5)                             | >= 4.0             |
| Tempestivita                        | Giorni di ritardo rispetto alla scadenza prevista           | 0 (on-time)        |

---

## Best Practices

1. **Pianificare con anticipo e iterare regolarmente.** Non aspettare che l'hardware si guasti o che le licenze scadano per pianificare. Mantenere una visione a 12-18 mesi e rivedere i piani trimestralmente. La pianificazione proattiva riduce i costi di emergenza del 40-60% rispetto agli interventi reattivi.

2. **Basare le decisioni sui dati, non sulle sensazioni.** Ogni decisione di capacity planning, ogni richiesta di budget, ogni prioritizzazione di progetto deve essere supportata da dati concreti provenienti dai sistemi di monitoring e dal sistema di ticketing. Dati solidi rendono le richieste di budget molto piu convincenti.

3. **Automatizzare la raccolta dati e la generazione dei report.** Il tempo speso ogni mese a raccogliere manualmente dati per i report e tempo sottratto ad attivita a maggior valore aggiunto. Investire nell'automazione della reportistica: il ROI e immediato e significativo.

4. **Adattare la comunicazione all'audience.** Un report tecnico dettagliato e utile per il team operativo ma incomprensibile per il CFO. Preparare sempre versioni diverse dello stesso contenuto, adattando linguaggio, livello di dettaglio e focus (tecnico vs business) al destinatario.

5. **Includere sempre il contesto di business nelle metriche.** Un downtime di 2 ore e un dato tecnico. Un downtime di 2 ore che ha impattato 500 utenti e causato EUR 50.000 di mancate vendite e un'informazione di business. Tradurre sempre le metriche tecniche in impatto aziendale.

6. **Mantenere una contingency nel budget.** Riservare sempre almeno il 10-15% del budget totale per imprevisti. Guasti hardware inattesi, vulnerabilita zero-day, esigenze di business urgenti: gli imprevisti sono l'unica certezza nella gestione IT. Un budget senza contingency e un budget destinato a sforare.

7. **Documentare le lezioni apprese e riutilizzarle.** Dopo ogni progetto di migrazione, ogni incidente critico, ogni ciclo di budget, condurre una retrospettiva e documentare le lezioni apprese. Creare un archivio accessibile di lesson learned che il team possa consultare per i progetti futuri.

8. **Definire KPI chiari con target realistici.** Non misurare tutto: concentrarsi su 10-15 KPI veramente significativi. Definire target realistici e progressivi (non passare da 95% a 99.99% in un trimestre). Celebrare i miglioramenti e analizzare onestamente i peggioramenti.

9. **Coinvolgere gli stakeholder nella definizione delle priorita.** La roadmap tecnologica non e un documento solo IT. Coinvolgere i responsabili di business nella definizione delle priorita assicura allineamento strategico e facilita l'approvazione dei budget. Organizzare workshop di prioritizzazione almeno annualmente.

10. **Rivedere e aggiornare la roadmap in modo continuo.** Una roadmap statica diventa obsoleta in pochi mesi. Trattarla come un documento vivo: aggiornarla trimestralmente, comunicare le modifiche agli stakeholder e mantenere la tracciabilita delle decisioni e dei cambiamenti.

---

## Troubleshooting

### Problema: I report non vengono letti dal management

**Sintomi:** I report mensili vengono inviati ma non generano feedback, domande o azioni da parte del management. Le richieste di budget vengono ignorate o ritardate.

**Cause probabili:**
- Report troppo tecnici e privi di contesto di business.
- Report troppo lunghi (nessuno legge 30 pagine di metriche).
- Mancanza di un executive summary chiaro e orientato alle azioni.
- Invio a destinatari non appropriati o in formato non adeguato.

**Soluzioni:**
- Ristrutturare il report con l'executive summary in prima pagina (massimo mezza pagina).
- Tradurre ogni metrica in impatto di business (EUR, ore perse, utenti impattati).
- Utilizzare semafori visivi (verde/giallo/rosso) per una lettura immediata.
- Ridurre la lunghezza: il report per il management non dovrebbe superare le 3-4 pagine.
- Presentare il report in un meeting breve (15-20 minuti) anziche inviarlo solo via email.

### Problema: Le previsioni di capacity si rivelano sempre imprecise

**Sintomi:** Le previsioni di crescita si discostano significativamente dalla realta, portando a sovradimensionamento (spreco) o sottodimensionamento (emergenze).

**Cause probabili:**
- Dati storici insufficienti (meno di 6 mesi).
- Non vengono considerati eventi non lineari (lancio prodotti, acquisizioni).
- Modelli troppo semplici per pattern di crescita complessi.
- Mancata comunicazione tra IT e business sulla crescita pianificata.

**Soluzioni:**
- Raccogliere almeno 12 mesi di dati storici prima di fare previsioni affidabili.
- Distinguere tra crescita organica (prevedibile) e crescita per eventi (da pianificare separatamente).
- Utilizzare margini di sicurezza: aggiungere il 20-30% alla previsione base.
- Stabilire un canale di comunicazione regolare con i responsabili di business per conoscere in anticipo le iniziative che impatteranno l'infrastruttura.
- Rivedere e calibrare i modelli trimestralmente confrontando previsioni e dati reali.

### Problema: Il budget viene sempre superato

**Sintomi:** A fine anno il budget IT risulta regolarmente superato, generando tensioni con il CFO e riducendo la credibilita del team IT.

**Cause probabili:**
- Contingency insufficiente o assente.
- Costi cloud non controllati (resource sprawl).
- Emergenze hardware non pianificate.
- Prezzi di rinnovo licenze aumentati senza preavviso.
- Scope creep dei progetti.

**Soluzioni:**
- Prevedere una contingency del 10-15% nel budget iniziale.
- Implementare alerting sui costi cloud con soglie mensili.
- Accelerare il piano di refresh hardware per ridurre i guasti imprevisti.
- Negoziare i rinnovi licenze con 3-6 mesi di anticipo, ottenendo preventivi scritti.
- Definire chiaramente lo scope dei progetti e gestire le richieste aggiuntive tramite il processo di change.
- Presentare un forecast trimestrale aggiornato al CFO, evidenziando rischi di sforamento per tempo.

### Problema: La roadmap tecnologica non viene rispettata

**Sintomi:** I progetti della roadmap vengono continuamente rimandati, le milestone non vengono rispettate, e alla fine dell'anno si e completato meno del 50% di quanto pianificato.

**Cause probabili:**
- Roadmap troppo ambiziosa rispetto alle risorse disponibili.
- Team sovraccarico di attivita operative quotidiane (nessun tempo per i progetti).
- Mancanza di sponsorship da parte del management.
- Priorita che cambiano continuamente.
- Dipendenze tra progetti non gestite.

**Soluzioni:**
- Essere realistici nella pianificazione: e meglio promettere meno e mantenere piu.
- Riservare almeno il 20-30% del tempo del team per attivita progettuali (non solo reattive).
- Ottenere approvazione formale della roadmap dal CTO/CEO e collegare le iniziative a obiettivi di business.
- Limitare i cambiamenti di priorita: ogni nuova richiesta urgente deve essere valutata in termini di impatto su cio che viene rimandato.
- Gestire le dipendenze visivamente (diagramma di Gantt o kanban) e avere un responsabile per ogni iniziativa.

### Problema: Difficolta a giustificare gli investimenti IT al management

**Sintomi:** Le richieste di budget per infrastruttura, strumenti o personale vengono regolarmente ridotte o rifiutate. Il management percepisce l'IT come un costo e non come un investimento.

**Cause probabili:**
- Le richieste sono formulate in termini tecnici anziche in termini di business value.
- Mancanza di dati concreti a supporto delle richieste.
- Assenza di calcoli TCO e ROI nelle proposte.
- Comunicazione insufficiente dei risultati ottenuti con investimenti precedenti.

**Soluzioni:**
- Presentare ogni richiesta con un business case strutturato: problema, soluzione proposta, costi, benefici attesi, ROI, rischi se non si interviene.
- Quantificare il costo del "non fare nulla" (costo dell'inazione): quanto costa un downtime? Quanto costa un breach di sicurezza? Quanto tempo viene perso con processi manuali?
- Dimostrare i risultati: ogni report mensile dovrebbe evidenziare i miglioramenti ottenuti grazie agli investimenti passati.
- Parlare il linguaggio del CFO: CAPEX, OPEX, ROI, TCO, payback period, costo opportunita.
- Proporre alternative a diversi livelli di investimento (buono/migliore/ottimo), consentendo al management di scegliere il livello di rischio accettabile.

### Problema: Dati incoerenti tra sistemi diversi

**Sintomi:** I dati di monitoring, ticketing, asset management e reporting non corrispondono. Lo stesso KPI ha valori diversi a seconda della fonte.

**Cause probabili:**
- Sistemi non integrati, con dati inseriti manualmente.
- Definizioni diverse delle metriche tra sistemi (es. come si calcola il downtime).
- Dati di asset management non aggiornati.
- Mancanza di un "single source of truth".

**Soluzioni:**
- Definire formalmente ogni KPI: formula esatta, fonte dati, periodicita, responsabile.
- Integrare i sistemi tramite API quando possibile (monitoring → ITSM → CMDB).
- Designare un sistema come "single source of truth" per ogni tipo di dato.
- Automatizzare l'estrazione dei dati per eliminare errori di inserimento manuale.
- Eseguire audit periodici (trimestrali) della qualita dei dati tra i sistemi.

---

> **Documento correlato**: Per una panoramica completa del framework di manutenzione IT, consultare il documento `00-panoramica-e-piano-di-studio.md`. Per le procedure operative dettagliate, fare riferimento alla cartella `09-PROCEDURE-OPERATIVE/`.

---

## Esercizi
1. **Lab — KPI dashboard.** 5 KPI essenziali, dashboard Grafana auto-refresh.
2. **Stretch — capacity forecast.** Linear regression su trend 6 mesi.

## Auto-valutazione
1. KPI vs vanity metric: differenza.
2. Executive summary: 1 pagina, contenuto.
3. Forecasting: tecniche.

## Glossario locale
| Termine | Definizione |
|---|---|
| **KPI** | Key Performance Indicator. |
| **Vanity metric** | Metrica impressionante ma non actionable. |
| **Forecasting** | Previsione trend futuro. |
| **Executive summary** | Sintesi 1-pagina per management. |
