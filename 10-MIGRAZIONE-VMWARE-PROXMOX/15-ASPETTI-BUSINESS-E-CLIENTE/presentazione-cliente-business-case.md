# Presentazione al Cliente: Business Case per la Migrazione da VMware a Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 6 — Business e cliente · Modulo 15.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 01-14 (competenze tecniche complete); concetti di TCO, ROI, payback period; capacita di comunicazione tecnico-business; familiarita con i pricing VMware post-Broadcom 2023.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. costruire un **business case quantitativo** per la migrazione, con numeri concreti su licensing VMware (prima e post-Broadcom), licensing Proxmox (subscription Enterprise vs No-Subscription), TCO 3-5 anni;
> 2. mappare i **rischi tecnici** (compatibilita, downtime cutover, regressioni performance) e organizzativi (formazione team, change resistance) con mitigation;
> 3. presentare il piano in modo strutturato a stakeholder C-level (CFO: numeri; CTO: rischi tecnici; CEO: timing/strategy);
> 4. preparare risposte alle obiezioni comuni: "abbiamo gia VMware skill", "Proxmox e meno enterprise", "support level" — armonizzando con la realta dei fatti;
> 5. modellare lo **scope di una proof-of-concept**: 4-8 settimane, perimetro limitato (10-30 VM non critiche), KPI misurabili (perf, uptime, backup), exit criteria;
> 6. negoziare la timeline e il commitment: pilot → wave migration → cutover finale, con governance e checkpoint definiti.
> **Tempo stimato:** lettura 60-90 min · lab 240 min (preparare e simulare una presentazione completa)
> **Livello:** competent (Dreyfus 3); soft skills + business acumen
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; VMware vSphere 7.x/8.x post-Broadcom 2023.

## Mappa concettuale

```
+============================================================+
|     Business case migrazione: pillars                       |
+============================================================+
|                                                            |
|   1. PERCHE ORA?                                           |
|   - Broadcom acquired VMware 2023-11                       |
|   - Pricing changes: vSAN/NSX/Aria bundled, +200-400%      |
|   - Perpetual licenses → subscription only                 |
|   - Channel program: minimum bundle revenue threshold      |
|                                                            |
|   2. ECONOMICS                                             |
|   - Licensing VMware (now): X €/anno                       |
|   - Licensing Proxmox: 0 (no-sub) o ~840€/socket/anno      |
|     (Enterprise subscription)                              |
|   - Saving 60-90% tipico                                   |
|   - Costo migrazione one-time: 50-200K€                    |
|   - Payback: 6-18 mesi                                     |
|                                                            |
|   3. TECHNICAL READINESS                                   |
|   - Feature parity? 90%+ con eccezioni note                |
|   - Migration tools: virt-v2v, OVA import, qm import       |
|   - Skills: Proxmox = Linux/KVM (skill leverageable)       |
|                                                            |
|   4. RISKS & MITIGATIONS                                   |
|   - Compatibility unknowns → POC su 5-10 VM critiche        |
|   - Team training → 4-6 settimane di onboarding            |
|   - Vendor lock-in (di nuovo)? → no, FOSS                  |
|                                                            |
|   5. ROADMAP                                               |
|   - POC: 4-8 settimane                                     |
|   - Wave 1 (test/dev): 2-3 mesi                            |
|   - Wave 2 (workload non-critical): 3-6 mesi               |
|   - Wave 3 (production critical): 6-12 mesi                |
|   - Decommissioning VMware: 12-18 mesi totali              |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Numeri concreti, non slogan.** "Risparmiamo molto" e debole. "Risparmiamo €420K in 3 anni con payback in 11 mesi" e forte. Ogni assertion deve essere supportata da calcolo verificabile.
2. **Stakeholder hanno priorita diverse.** CFO vuole TCO/payback. CTO vuole risk + technical feasibility. Operations vuole training + support. Adapta la presentazione (o le sezioni) all'audience.
3. **Riconosci i feature gap onestamente.** vSphere DRS, vRealize Operations, NSX-T networking — Proxmox non ha equivalenti diretti. Ammettere upfront e proporre alternative (ProxLB, Prometheus+Grafana, Linux native networking) costruisce credibilita.
4. **POC = de-risk.** Mai chiedere commitment per migrazione completa senza POC. Pochi soldi, scope limitato, KPI chiari, timeline 4-8 settimane → decisione informata.
5. **Vendor lock-in narrative.** Proxmox e FOSS basato su upstream KVM/QEMU/Debian: nessun vendor lock-in proprietario. Quest'argomento risuona forte post-Broadcom.

---

## Indice

1. [Obiettivi della Presentazione](#obiettivi-della-presentazione)
2. [Struttura Slide-by-Slide](#struttura-slide-by-slide)
3. [Note per il Relatore](#note-per-il-relatore)
4. [Gestione delle Obiezioni](#gestione-delle-obiezioni)
5. [Casi di Studio](#casi-di-studio)
6. [Talking Points per la Demo](#talking-points-per-la-demo)
7. [Preparazione Q&A](#preparazione-qa)
8. [Materiali di Supporto](#materiali-di-supporto)

---

## Obiettivi della Presentazione

### Scopo

Questa guida fornisce un framework completo per la preparazione e l'erogazione di una presentazione di business case per la migrazione da VMware vSphere a Proxmox VE. L'obiettivo è convincere i decision-maker aziendali (CTO, IT Director, CFO) della validità tecnica ed economica della migrazione.

### Pubblico Target

| Ruolo | Interessi Principali | Messaggi Chiave |
|---|---|---|
| CTO / IT Director | Affidabilità, roadmap tecnologica, rischio | Funzionalità equivalenti, comunità solida, roadmap attiva |
| CFO / Finance | Costi, ROI, prevedibilità budget | Risparmio 50-80%, modello di costo stabile, ROI rapido |
| CISO / Security | Sicurezza, compliance, supporto | Open source audit, aggiornamenti regolari, compliance |
| IT Operations | Usabilità, migrazione, formazione | Interfaccia intuitiva, formazione inclusa, supporto |
| CEO / Board | Rischio strategico, vendor dependency | Indipendenza, futuro-proof, investimento responsabile |

### Durata Consigliata

| Formato | Durata | Slide | Audience |
|---|---|---|---|
| Pitch rapido | 15 minuti | 8-10 slide | C-Level occupati |
| Presentazione standard | 30-40 minuti | 20-25 slide | IT Management |
| Presentazione estesa | 60-90 minuti | 30-35 slide + demo | Team tecnico + management |

---

## Struttura Slide-by-Slide

### SLIDE 1: Copertina

**Titolo**: Migrazione da VMware a Proxmox VE — Business Case e Piano di Implementazione

**Contenuto**:
- Logo [NOME_AZIENDA]
- Logo [NOME_CLIENTE]
- Data della presentazione
- Classificazione: Riservato

**Note relatore**: Presentarsi brevemente, ringraziare per il tempo, chiarire la durata e la struttura della presentazione.

---

### SLIDE 2: Agenda

**Titolo**: Agenda

**Contenuto**:
1. Il contesto: cosa è cambiato nel mondo VMware (5 min)
2. L'alternativa: Proxmox VE in sintesi (5 min)
3. Analisi economica: i numeri parlano (10 min)
4. L'approccio: come migriamo (5 min)
5. Gestione del rischio (5 min)
6. Demo live (opzionale, 10 min)
7. Domande e discussione (10 min)

**Note relatore**: Chiedere se ci sono aspetti specifici che il pubblico desidera approfondire. Adattare l'enfasi di conseguenza.

---

### SLIDE 3: Il Cambiamento — L'Acquisizione Broadcom

**Titolo**: Il Mondo VMware è Cambiato — Per Sempre

**Contenuto visuale**: Timeline con i cambiamenti chiave post-acquisizione

**Messaggi chiave**:

| Data | Evento | Impatto |
|---|---|---|
| Nov 2023 | Completamento acquisizione Broadcom | Inizio della transizione |
| Dic 2023 | Eliminazione licenze perpetue | Fine del modello tradizionale |
| Gen 2024 | Nuovo pricing per-core | Aumento costi 200-1200% |
| Feb 2024 | Eliminazione programma partner | Riduzione supporto ecosistema |
| Mar 2024 | Fine vendita prodotti standalone | Solo bundle VVF/VCF |
| 2024-2025 | Riduzione personale VMware | Impatto su sviluppo e supporto |

**Note relatore**: "Il cambiamento non è una possibilità, è già avvenuto. La domanda non è SE adattarsi, ma COME e QUANDO."

---

### SLIDE 4: L'Impatto sui Vostri Costi

**Titolo**: Cosa Significa per [NOME_CLIENTE]

**Contenuto**: Tabella comparativa personalizzata

| Voce | Costo Attuale (Annuo) | Costo Nuovo VMware (Annuo) | Incremento |
|---|---|---|---|
| Licenze vSphere | €[X] | €[Y] | +[Z]% |
| Support & Subscription | €[X] | Incluso | — |
| Prodotti aggiuntivi | €[X] | €[Y] (bundle forzato) | +[Z]% |
| **Totale** | **€[TOTALE_ATTUALE]** | **€[TOTALE_NUOVO]** | **+[Z]%** |

**Impatto triennale**: da €[X] a €[Y] = +€[DELTA] in 3 anni

**Note relatore**: Usare i dati reali del cliente, raccolti durante l'assessment. L'impatto visivo dei numeri è il messaggio più forte. Lasciare che il pubblico assorba i numeri prima di procedere.

---

### SLIDE 5: Le Opzioni Strategiche

**Titolo**: Tre Strade Possibili

**Contenuto**: Diagramma a tre colonne

| Opzione | Descrizione | Pro | Contro |
|---|---|---|---|
| **1. Restare con VMware** | Accettare i nuovi costi e condizioni | Nessuna migrazione necessaria | Costi in aumento, vendor lock-in totale, dipendenza da Broadcom |
| **2. Migrare a Hyper-V** | Passare alla piattaforma Microsoft | Ecosistema Microsoft integrato | Microsoft sta discontinuando Hyper-V standalone, costi licenza Windows, diverso vendor lock-in |
| **3. Migrare a Proxmox VE** | Open source enterprise-grade | Risparmio 50-80%, libertà totale, funzionalità complete | Curva di apprendimento, ecosistema più giovane |

**Note relatore**: Presentare le tre opzioni in modo oggettivo, ma evidenziare che l'opzione 3 è quella che offre il miglior bilancio costi/benefici. Menzionare che Microsoft ha annunciato il fine vita di Hyper-V come prodotto standalone, orientandosi verso Azure Stack HCI.

---

### SLIDE 6: Cos'è Proxmox VE

**Titolo**: Proxmox VE — Virtualizzazione Enterprise Open Source

**Contenuto**:

**Numeri chiave** (da aggiornare con dati correnti):
- Oltre 800.000 installazioni attive nel mondo
- Sviluppato dal 2008 da Proxmox Server Solutions GmbH (Austria)
- Basato su Debian Linux, kernel enterprise
- Hypervisor KVM (parte del kernel Linux) + container LXC
- Licenza AGPL v3 — codice sorgente completamente aperto

**Funzionalità enterprise incluse senza costi aggiuntivi**:

| Funzionalità | Inclusa | Equivalente VMware |
|---|---|---|
| High Availability | Sì | vSphere HA |
| Live Migration | Sì | vMotion |
| Software-Defined Storage (Ceph) | Sì | vSAN ($$$) |
| Backup integrato (PBS) | Sì | Necessita Veeam/altro ($$$) |
| Firewall distribuito | Sì | NSX ($$$) |
| Software-Defined Networking | Sì | NSX ($$$) |
| Web management console | Sì | vCenter ($$) |
| API REST completa | Sì | API vSphere |
| Container nativi (LXC) | Sì | Solo con Tanzu |
| Replica e DR | Sì | SRM ($$$) |

**Note relatore**: Enfatizzare che non si tratta di un "prodotto di nicchia" ma di una piattaforma matura usata da aziende di ogni dimensione, incluse università, ISP, enti pubblici e enterprise.

---

### SLIDE 7: Confronto Funzionale Dettagliato

**Titolo**: Feature Parity — Proxmox fa quello che vi serve

**Contenuto**: Matrice di confronto

| Funzionalità | VMware vSphere | Proxmox VE | Note |
|---|---|---|---|
| Hypervisor Type-1 | ESXi | KVM (kernel Linux) | KVM è nel kernel Linux ufficiale |
| Gestione centralizzata | vCenter | Web GUI integrata | Nessun server aggiuntivo necessario |
| VM Linux | Completo | Completo | — |
| VM Windows | Completo | Completo (VirtIO) | Performance eccellenti con VirtIO |
| High Availability | vSphere HA | Proxmox HA | Failover automatico |
| Live Migration | vMotion | Online Migration | Senza downtime |
| Resource Pools | Sì | Sì | — |
| Snapshots | Sì | Sì (QEMU/ZFS) | — |
| Templates | Sì | Sì + Cloud-Init | — |
| Cluster fino a 32 nodi | Sì | Sì | — |
| Storage condiviso | FC, iSCSI, NFS | FC, iSCSI, NFS, Ceph, ZFS, GlusterFS | Più opzioni |
| Software-Defined Storage | vSAN (addon) | Ceph (integrato) | Incluso gratuitamente |
| Backup incrementale | No (solo VADP per terze parti) | PBS (nativo, dedup, encryption) | Enorme vantaggio |
| Container nativi | Solo via Tanzu | LXC nativo | Container leggeri |
| GPU Passthrough | Sì | Sì | — |
| REST API | Sì | Sì | Completa e ben documentata |
| Terraform provider | Sì | Sì (community) | Infrastructure as Code |
| RBAC | Sì | Sì | Role-based access control |
| Two-Factor Auth | Sì | Sì (TOTP, WebAuthn) | — |
| LDAP/AD integration | Sì | Sì | — |

**Note relatore**: Non serve coprire ogni riga. Concentrarsi sulle funzionalità più rilevanti per il cliente specifico. Chiedere "Quali di queste funzionalità usate attualmente?" per focalizzare la discussione.

---

### SLIDE 8: L'Analisi Economica — TCO a 3 Anni

**Titolo**: I Numeri Non Mentono

**Contenuto**: Grafico a barre comparativo

```
TCO 3 Anni — [NOME_CLIENTE]

VMware VVF:   ████████████████████████████████████  €[IMPORTO]
VMware VCF:   ████████████████████████████████████████████  €[IMPORTO]
Proxmox VE:   ████████████                                  €[IMPORTO]

Risparmio 3 anni: €[RISPARMIO] ([PERCENTUALE]%)
```

**Breakdown dettagliato**:

| Voce (3 anni) | VMware | Proxmox | Risparmio |
|---|---|---|---|
| Licenze/sottoscrizioni | €[X] | €[Y] | €[DELTA] |
| Backup solution | €[X] | €0 | €[X] |
| Monitoring | €[X] | €[Y] | €[DELTA] |
| Migrazione (una tantum) | €0 | €[Y] | -€[Y] |
| Formazione | €[X] | €[Y] | ±€[DELTA] |
| **Totale** | **€[TOTALE]** | **€[TOTALE]** | **€[RISPARMIO]** |

**Note relatore**: Questo è il momento clou della presentazione per il CFO. Lasciare tempo per le domande sui numeri. Essere pronti a spiegare ogni voce in dettaglio.

---

### SLIDE 9: ROI e Payback Period

**Titolo**: Il Ritorno sull'Investimento

**Contenuto**:

```
Investimento iniziale migrazione: €[IMPORTO]
Risparmio annuo (a regime):       €[IMPORTO]

Payback Period: [N] mesi

         Cumulativo Risparmio vs Investimento
€        ▲
         │                                    ╱
         │                              ╱╱╱╱
[RISP]   │                        ╱╱╱╱
         │                  ╱╱╱╱
         │            ╱╱╱╱
   0     ├──────╱╱╱╱─────────────────────────→ Anni
         │╱╱╱╱
-[INV]   │╱
         │

         Anno 0     Anno 1     Anno 2     Anno 3
```

| Metrica | Valore |
|---|---|
| Investimento migrazione | €[IMPORTO] |
| Risparmio Anno 1 | €[IMPORTO] |
| Risparmio Anno 2 | €[IMPORTO] |
| Risparmio Anno 3 | €[IMPORTO] |
| **Risparmio cumulativo 3 anni** | **€[IMPORTO]** |
| **ROI a 3 anni** | **[PERCENTUALE]%** |
| **ROI a 5 anni** | **[PERCENTUALE]%** |

**Note relatore**: Evidenziare il momento di break-even. Sottolineare che dopo il payback, ogni anno rappresenta risparmio netto.

---

### SLIDE 10: Benefici Strategici Oltre il Costo

**Titolo**: Non Solo Risparmio — Vantaggi Strategici

**Contenuto**:

#### 1. Libertà dal Vendor Lock-in
- Nessuna dipendenza da decisioni commerciali di un singolo vendor
- Hardware di qualsiasi produttore (nessuna HCL restrittiva)
- Dati in formati standard (QCOW2, raw) facilmente migrabili

#### 2. Prevedibilità dei Costi
- Modello di pricing stabile (per server, non per core)
- Nessun rischio di aumenti improvvisi come con Broadcom
- Possibilità di usare la versione community senza costi

#### 3. Trasparenza e Sicurezza
- Codice sorgente completamente aperto e auditabile
- Nessun "black box" nel software che gestisce i vostri dati
- Community globale che identifica e corregge vulnerabilità

#### 4. Innovazione Continua
- Release regolari con nuove funzionalità
- Integrazione con le ultime tecnologie Linux
- Community attiva che guida lo sviluppo

#### 5. Flessibilità Operativa
- Stessa piattaforma per VM, container LXC e Kubernetes
- Backup integrato senza licenze aggiuntive
- Storage software-defined incluso

**Note relatore**: Questa slide è fondamentale per il CTO e per chi pensa a lungo termine. I costi si affrontano nella slide precedente; qui si parla di strategia.

---

### SLIDE 11: Chi Usa Proxmox VE

**Titolo**: Proxmox VE in Produzione — Non Siete i Primi

**Contenuto**: Loghi e categorie di utilizzo

| Settore | Esempi di Utilizzo | Scala |
|---|---|---|
| Hosting / Cloud Provider | OVHcloud, Hetzner, Contabo | Migliaia di nodi |
| Telecomunicazioni | ISP europei e globali | Centinaia di nodi |
| Università e Ricerca | CERN, università europee | HPC e ricerca |
| Pubblica Amministrazione | Enti governativi europei | Compliance-critical |
| Finanza | Banche e assicurazioni europee | Mission-critical |
| Sanità | Ospedali e ASL | GDPR-critical |
| Manufacturing | Aziende industriali | Edge + datacenter |
| Education | Scuole e istituti | Budget limitato |

**Numeri della community**:
- Forum: centinaia di migliaia di utenti attivi
- Mailing list: migliaia di messaggi/mese
- GitHub: progetto attivamente sviluppato
- Conferenze: Proxmox VE Summit annuale

**Note relatore**: Adattare gli esempi al settore del cliente. Se possibile, citare aziende dello stesso settore e dimensione.

---

### SLIDE 12: L'Approccio alla Migrazione

**Titolo**: Come Migriamo — Il Nostro Approccio Strutturato

**Contenuto**: Diagramma delle fasi

```
  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │  FASE 1  │──▶│  FASE 2  │──▶│  FASE 3  │──▶│  FASE 4  │──▶│  FASE 5  │
  │Assessment│   │Preparaz. │   │Migrazione│   │Validaz.  │   │ Go-Live  │
  │          │   │Ambiente  │   │ a Wave   │   │  e Test  │   │          │
  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
   2 settimane    2 settimane    4-8 settimane   2 settimane    2 settimane

  Durata totale stimata: [N] settimane
```

**Principi guida**:
1. **Migrazione per wave**: dalle VM meno critiche alle più critiche
2. **Rollback sempre possibile**: l'ambiente VMware resta disponibile fino alla validazione
3. **Zero sorprese**: comunicazione continua e reporting settimanale
4. **Downtime minimizzato**: migrazione durante finestre di manutenzione concordate
5. **Qualità garantita**: test automatizzati e manuali dopo ogni wave

**Note relatore**: Rassicurare sul fatto che la migrazione è graduale e reversibile. L'ambiente VMware non viene spento fino a quando tutto è validato.

---

### SLIDE 13: Gestione del Rischio

**Titolo**: Come Gestiamo i Rischi

**Contenuto**:

| Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|
| Incompatibilità applicativa | Bassa | Alto | Test pilota prima della migrazione di massa |
| Performance degradate post-migrazione | Bassa | Medio | Benchmark pre/post, tuning |
| Downtime prolungato durante migrazione | Bassa | Alto | Migrazione a wave, rollback plan |
| Resistenza del team IT al cambiamento | Media | Medio | Formazione, coinvolgimento precoce |
| Problemi con driver hardware | Bassa | Medio | Test hardware preliminare |
| Perdita dati | Molto bassa | Critico | Backup pre-migrazione, verifica integrità |

**Il nostro impegno**:
- Risk register aggiornato settimanalmente
- Escalation immediata per rischi critici
- Rollback plan testato per ogni wave
- Assicurazione RC professionale

**Note relatore**: Questa slide è fondamentale per gestire l'ansia dei decision-maker. Mostrare che ogni rischio è stato identificato e ha una risposta pianificata.

---

### SLIDE 14: Il Team di Progetto

**Titolo**: Chi Lavora al Vostro Progetto

**Contenuto**: Organigramma del team con foto e breve profilo

| Ruolo | Nome | Esperienza | Certificazioni |
|---|---|---|---|
| Project Manager | [NOME] | [N] anni PM, [N] migrazioni | PMP, PRINCE2 |
| Solution Architect | [NOME] | [N] anni infrastruttura | VCP, Proxmox Certified |
| Senior Engineer | [NOME] | [N] anni systems admin | RHCE, CKA |
| Engineer | [NOME] | [N] anni virtualizzazione | Linux+ |

**Note relatore**: Personalizzare con i profili reali del team assegnato. Il cliente vuole sapere chi lavorerà concretamente al progetto.

---

### SLIDE 15: Investimento e Risparmio

**Titolo**: L'Investimento — Sintesi Economica

**Contenuto**:

| Voce | Importo |
|---|---|
| Servizio di migrazione completo | €[IMPORTO] |
| Formazione team (opzionale) | €[IMPORTO] |
| Supporto post-migrazione 3 mesi (opzionale) | €[IMPORTO] |
| **Investimento totale** | **€[TOTALE]** |

**vs. il costo di NON migrare**:

| Voce | Anno 1 | Anno 2 | Anno 3 | Totale |
|---|---|---|---|---|
| Costo VMware (nuovi termini) | €[X] | €[X] | €[X] | €[3X] |
| Costo Proxmox + migrazione | €[Y] | €[Z] | €[Z] | €[Y+2Z] |
| **Risparmio netto** | **€[D]** | **€[D]** | **€[D]** | **€[TOTALE]** |

**Note relatore**: Presentare il costo della migrazione non come una spesa, ma come un investimento con un ritorno misurabile. Confrontare sempre con il costo dell'inazione.

---

### SLIDE 16: Prossimi Passi

**Titolo**: Prossimi Passi Proposti

**Contenuto**:

| Step | Attività | Tempistica | Risultato |
|---|---|---|---|
| 1 | Proof of Concept (opzionale) | 1-2 settimane | Validazione tecnica su 3-5 VM |
| 2 | Assessment dettagliato | 1-2 settimane | Inventario completo, piano dettagliato |
| 3 | Approvazione e contratto | 1 settimana | Avvio del progetto |
| 4 | Kick-off progetto | Settimana [N] | Inizio lavori |

**Offerta speciale** (opzionale):
- Proof of Concept gratuito/scontato per validare la fattibilità
- Assessment iniziale a costo ridotto, scalabile dal progetto completo

**Note relatore**: Chiudere con una chiara call-to-action. Proporre il PoC come primo passo a basso rischio.

---

### SLIDE 17: Contatti e Ringraziamenti

**Titolo**: Grazie — Siamo a Vostra Disposizione

**Contenuto**:
- Dati di contatto del referente commerciale
- Dati di contatto del referente tecnico
- Link alla documentazione Proxmox
- QR code per la proposta commerciale (se applicabile)

---

## Note per il Relatore

### Preparazione Pre-Presentazione

#### Checklist

- [ ] Dati del cliente verificati e aggiornati
- [ ] Calcoli economici validati con dati reali
- [ ] Slide personalizzate con logo e dati del cliente
- [ ] Demo environment preparato e testato
- [ ] Backup delle slide in PDF (in caso di problemi tecnici)
- [ ] Conoscenza dell'audience (chi partecipa, che ruoli hanno)
- [ ] Risposte preparate per le obiezioni più comuni
- [ ] Materiali stampati per i partecipanti (opzionale)
- [ ] Test della connessione e del proiettore
- [ ] Laptop di backup con le slide

#### Consigli per la Presentazione

1. **Iniziare con il "perché"**: non con la tecnologia, ma con il problema di business (costi VMware in aumento)
2. **Usare i numeri del cliente**: niente è più convincente dei loro stessi dati
3. **Essere onesti sulle sfide**: ammettere la curva di apprendimento e i costi di migrazione costruisce fiducia
4. **Raccontare storie**: usare casi reali di clienti che hanno migrato con successo
5. **Coinvolgere il pubblico**: fare domande, chiedere la loro esperienza con VMware
6. **Non parlare male di VMware**: concentrarsi sui vantaggi di Proxmox, non sui difetti di VMware
7. **Adattare il linguaggio**: tecnico con i tecnici, business con il management
8. **Rispettare il tempo**: meglio finire in anticipo che in ritardo

---

## Gestione delle Obiezioni

### Obiezione 1: "Proxmox non ha lo stesso livello di supporto enterprise"

**Risposta strutturata**:

| Punto | Argomentazione |
|---|---|
| Supporto diretto | Proxmox offre supporto enterprise con SLA definiti (Piano Premium: 24/7 per severity 1) |
| Supporto community | Community enorme e attiva, forum con risposte rapide |
| Ecosistema partner | Rete crescente di partner certificati che offrono supporto locale |
| Confronto reale | Molti clienti VMware utilizzano partner per il supporto, non VMware direttamente. Lo stesso modello funziona con Proxmox |
| Esperienza post-Broadcom | Il supporto VMware è peggiorato dopo l'acquisizione (tempi di risposta più lunghi, turnover del personale) |

### Obiezione 2: "Proxmox è meno maturo di VMware"

**Risposta strutturata**:

| Punto | Argomentazione |
|---|---|
| KVM nel kernel Linux | KVM è l'hypervisor del kernel Linux, usato da AWS, Google Cloud, Azure — non è un prodotto di nicchia |
| Proxmox dal 2008 | Oltre 17 anni di sviluppo e deployment in produzione |
| Release regolari | Release maggiori annuali, aggiornamenti di sicurezza tempestivi |
| Casi enterprise | Utilizzato in ambienti mission-critical da organizzazioni di tutte le dimensioni |
| Open source = più occhi | Il codice è ispezionato da migliaia di sviluppatori; bug e vulnerabilità vengono identificati rapidamente |

### Obiezione 3: "Il nostro team non conosce Proxmox"

**Risposta strutturata**:

| Punto | Argomentazione |
|---|---|
| Curva di apprendimento | Proxmox è basato su Linux — se il team ha competenze Linux, la transizione è rapida |
| Interfaccia intuitiva | La Web GUI è moderna e intuitiva, spesso più semplice di vCenter |
| Formazione inclusa | Il nostro pacchetto include formazione completa per il team |
| Documentazione | Documentazione ufficiale eccellente, wiki community ricchissimo |
| Supporto durante transizione | Periodo di supporto post-migrazione per accompagnare il team |
| Certificazione | Esame di certificazione Proxmox disponibile a costo accessibile |

### Obiezione 4: "E se Proxmox chiude o cambia modello?"

**Risposta strutturata**:

| Punto | Argomentazione |
|---|---|
| Open source | Il codice è AGPL v3 — anche se l'azienda cessasse, il software resta disponibile e forkabile |
| Community fork | La community potrebbe continuare lo sviluppo (come è successo con altri progetti open source) |
| No lock-in tecnico | Le VM sono in formato standard, migrabili verso qualsiasi altra piattaforma KVM |
| Azienda stabile | Proxmox Server Solutions GmbH è un'azienda austriaca in crescita costante |
| Confronto ironico | VMware ERA la scelta "sicura" — poi Broadcom ha cambiato tutto. L'open source protegge da questo rischio |

### Obiezione 5: "Le nostre applicazioni certificate solo per VMware"

**Risposta strutturata**:

| Punto | Argomentazione |
|---|---|
| Livello di astrazione | Le applicazioni girano nel sistema operativo guest, non nel hypervisor. Il guest non "vede" se gira su ESXi o KVM |
| Certificazioni SAP | SAP supporta ufficialmente KVM/RHEL-KVM. Proxmox usa lo stesso KVM |
| Certificazioni Oracle | Oracle supporta KVM. Le policy di licensing Oracle funzionano anche su Proxmox |
| Microsoft | Tutti i sistemi Windows funzionano su KVM con driver VirtIO |
| Test nel PoC | Eventuali dubbi si risolvono con un Proof of Concept sulle applicazioni specifiche |

### Obiezione 6: "VMware ha funzionalità avanzate che Proxmox non ha"

**Risposta strutturata**:

| Funzionalità VMware | Alternativa Proxmox | Note |
|---|---|---|
| DRS (Distributed Resource Scheduler) | Manual balancing / script basati su API | In sviluppo, script community disponibili |
| vSAN stretched cluster | Ceph stretched cluster | Funzionalità equivalente |
| NSX micro-segmentation | OVS + firewall distribuito | Diverso approccio, risultato simile |
| Horizon (VDI) | Nessun equivalente diretto | Soluzioni terze parti (Apache Guacamole, etc.) |
| vRealize suite | Prometheus + Grafana + Terraform + Ansible | Stack open source equivalente |
| Fault Tolerance | Non disponibile | Raramente usata, HA è sufficiente per il 99% dei casi |

**Nota**: identificare le funzionalità effettivamente utilizzate dal cliente. Spesso le aziende pagano per funzionalità che non usano.

### Obiezione 7: "I nostri auditor / compliance richiedono VMware"

**Risposta strutturata**:

| Punto | Argomentazione |
|---|---|
| Compliance è sul processo | Gli auditor verificano i processi (backup, HA, sicurezza), non il nome del prodotto |
| Documentazione | Proxmox supporta tutti i controlli di sicurezza richiesti (RBAC, audit log, encryption) |
| Standard internazionali | Proxmox può soddisfare ISO 27001, GDPR, SOC2 con la configurazione corretta |
| Enti pubblici europei | Molti enti pubblici europei usano Proxmox, dimostrando la compliance |
| Supporto all'audit | Possiamo fornire documentazione specifica per gli auditor |

---

## Casi di Studio

### Struttura Consigliata per i Casi di Studio

Per ogni caso di studio, utilizzare la seguente struttura:

#### Template Caso di Studio

```
CASO DI STUDIO: [NOME_AZIENDA o SETTORE]

PROFILO
- Settore: [SETTORE]
- Dimensione: [DIPENDENTI], [FATTURATO]
- Infrastruttura: [N] server, [N] VM

LA SFIDA
[2-3 frasi che descrivono il problema specifico del cliente]
- Aumento costi VMware: +[N]%
- [Altro problema specifico]
- [Altro problema specifico]

LA SOLUZIONE
- Migrazione da VMware vSphere [VERSIONE] a Proxmox VE [VERSIONE]
- [N] server, [N] VM migrate in [N] settimane
- Incluso: [Ceph/ZFS], [PBS], [HA cluster]

I RISULTATI (QUANTIFICATI)
- Risparmio sui costi di licenza: [N]% (€[IMPORTO]/anno)
- Downtime durante migrazione: [N] ore totali
- Performance: [UGUALE/MIGLIORATA] del [N]%
- Payback period: [N] mesi

CITAZIONE DEL CLIENTE
"[Citazione reale o realistica del referente]"
— [Nome], [Ruolo], [Azienda]
```

### Esempio: PMI Manifatturiera

```
CASO DI STUDIO: Azienda Manifatturiera del Nord Italia

PROFILO
- Settore: Manufacturing (componentistica automotive)
- Dimensione: 250 dipendenti, €45M fatturato
- Infrastruttura: 4 server Dell PowerEdge, 35 VM

LA SFIDA
L'azienda utilizzava VMware vSphere Standard con licenze perpetue.
Con il passaggio al nuovo modello Broadcom, i costi sarebbero
passati da €8.000/anno a €32.000/anno — un aumento del 300%.
Il budget IT non poteva assorbire un tale incremento.

LA SOLUZIONE
Migrazione completa a Proxmox VE 8.x in 8 settimane:
- 4 nodi Proxmox in cluster HA
- Storage Ceph per le VM critiche, ZFS per archivio
- Proxmox Backup Server per backup con deduplicazione
- Formazione del team IT (2 persone, 3 giorni)

I RISULTATI
- Risparmio licenze: 95% (da €32.000/anno a €1.400/anno)
- Investimento migrazione: €18.000 (ammortizzato in 7 mesi)
- Downtime totale: 4 ore (durante weekend)
- Performance I/O disco: migliorata del 15% con Ceph
- Soddisfazione team IT: alta, interfaccia più intuitiva

CITAZIONE
"Avevamo paura del cambiamento, ma dopo due settimane
il nostro team era già operativo. Il risparmio economico
è stato il driver iniziale, ma la qualità della piattaforma
ci ha convinto che era la scelta giusta."
```

---

## Talking Points per la Demo

### Ambiente Demo Consigliato

| Componente | Configurazione |
|---|---|
| Cluster Proxmox | 3 nodi (anche VM nested per la demo) |
| VM di esempio | 2-3 Windows, 2-3 Linux, 1 container LXC |
| Storage | Ceph configurato + ZFS |
| PBS | 1 istanza con backup esistenti |
| Monitoring | Prometheus + Grafana (opzionale) |

### Script della Demo (15-20 minuti)

#### Parte 1: Panoramica Interfaccia (3 minuti)

**Mostrare**:
1. Login alla Web GUI — evidenziare la semplicità
2. Dashboard del datacenter — panoramica cluster
3. Lista nodi — stato di ogni server
4. Lista VM — tutte le macchine virtuali
5. Storage — panoramica dello storage disponibile

**Talking point**: "Come vedete, l'interfaccia è pulita e intuitiva. Tutte le informazioni importanti sono a portata di click, senza dover navigare tra mille menu come in vCenter."

#### Parte 2: Gestione VM (5 minuti)

**Mostrare**:
1. Creare una nuova VM — wizard guidato
2. Avviare una VM esistente — console noVNC/SPICE
3. Snapshot di una VM — creazione istantanea
4. Resize risorse (CPU, RAM) a caldo — se supportato dal guest
5. Cloud-Init — provisioning automatizzato

**Talking point**: "La creazione di una VM richiede gli stessi passaggi di VMware, ma l'interfaccia è più diretta. Cloud-Init permette il provisioning automatizzato senza tool aggiuntivi."

#### Parte 3: High Availability (3 minuti)

**Mostrare**:
1. Configurazione HA di una VM
2. Stato del cluster HA
3. Simulazione failure — migrare manualmente per mostrare il concetto
4. Fencing configuration

**Talking point**: "L'HA funziona come vSphere HA. Se un nodo va offline, le VM vengono riavviate automaticamente sugli altri nodi del cluster."

#### Parte 4: Live Migration (3 minuti)

**Mostrare**:
1. Selezionare una VM in esecuzione
2. Avviare la migrazione live verso un altro nodo
3. Mostrare che la VM resta accessibile durante la migrazione
4. Verificare lo spostamento completato

**Talking point**: "La live migration è l'equivalente di vMotion. La VM viene spostata senza downtime, esattamente come siete abituati."

#### Parte 5: Backup con PBS (3 minuti)

**Mostrare**:
1. Interfaccia di Proxmox Backup Server
2. Job di backup configurato
3. Eseguire un backup manuale
4. Mostrare la deduplicazione
5. Restore di una VM (o file singolo)

**Talking point**: "Il backup è integrato e gratuito. PBS offre deduplicazione, compressione e crittografia. Il restore granulare permette di recuperare anche singoli file senza ripristinare l'intera VM."

#### Parte 6: Ceph Storage (3 minuti, se applicabile)

**Mostrare**:
1. Dashboard Ceph integrato in Proxmox
2. Stato dei dischi OSD
3. Pool di storage
4. Performance in tempo reale

**Talking point**: "Ceph è il sostituto di vSAN, completamente integrato e senza costi di licenza. È lo stesso software usato da provider cloud di livello mondiale."

---

## Preparazione Q&A

### Domande Frequenti e Risposte Preparate

#### Domanda: "Quanto dura la migrazione?"

**Risposta**: "La durata dipende dalla complessità dell'ambiente. Per un ambiente di [N] VM su [N] server, stimiamo [N] settimane. L'approccio a wave garantisce che le operazioni quotidiane non vengano interrotte. Le VM più critiche vengono migrate per ultime, quando il team ha già acquisito confidenza con la piattaforma."

#### Domanda: "E se qualcosa va storto durante la migrazione?"

**Risposta**: "Ogni wave di migrazione include un piano di rollback testato. L'ambiente VMware originale non viene dismesso fino a quando tutte le VM sono state migrate, testate e validate. In qualsiasi momento è possibile tornare alla situazione precedente."

#### Domanda: "Come gestirete il downtime?"

**Risposta**: "Il downtime per VM è tipicamente di [5-30] minuti durante la migrazione, pianificato nelle finestre di manutenzione concordate con voi. Per le VM più critiche, utilizziamo tecniche di replica che riducono il downtime a pochi minuti."

#### Domanda: "Il nostro ERP/applicazione X è supportato?"

**Risposta**: "Le applicazioni girano all'interno del sistema operativo guest (Windows o Linux), che funziona identicamente su KVM/Proxmox come su VMware. Detto questo, nel PoC testeremo specificamente le vostre applicazioni critiche per confermare la piena compatibilità."

#### Domanda: "Chi ci supporterà dopo la migrazione?"

**Risposta**: "Offriamo pacchetti di supporto post-migrazione con SLA definiti. Inoltre, con la sottoscrizione Proxmox enterprise, avete accesso al supporto diretto del produttore. Il nostro obiettivo è rendere il vostro team autonomo, grazie alla formazione inclusa nel progetto."

#### Domanda: "Possiamo fare una prova prima di decidere?"

**Risposta**: "Assolutamente sì. Proponiamo un Proof of Concept su [3-5] VM non critiche, della durata di [1-2] settimane. Questo vi permetterà di vedere Proxmox in azione nel vostro ambiente reale, senza alcun rischio."

#### Domanda: "Come si posiziona Proxmox rispetto a Nutanix/OpenStack/oVirt?"

**Risposta breve per categoria**:

| Alternativa | Confronto con Proxmox |
|---|---|
| Nutanix | Eccellente ma costoso (modello simile a VMware). Proxmox offre funzionalità comparabili a costo molto inferiore |
| OpenStack | Potente ma molto complesso da installare e gestire. Proxmox è "opinionated" e funziona out-of-the-box |
| oVirt (Red Hat) | Red Hat ha annunciato la discontinuità. Community ridotta. Proxmox è in forte crescita |
| Hyper-V | Microsoft sta orientandosi verso Azure Stack HCI. Il futuro standalone è incerto |

#### Domanda: "Avete referenze nel nostro settore?"

**Risposta**: "Sì, abbiamo completato [N] progetti di migrazione nel settore [SETTORE]. Con il vostro permesso, posso mettervi in contatto diretto con [NOME_REFERENTE] di [AZIENDA], che ha completato un progetto molto simile al vostro."

---

## Materiali di Supporto

### Materiali da Preparare Prima della Presentazione

| Materiale | Formato | Destinatario | Scopo |
|---|---|---|---|
| Slide deck | PDF / PPTX | Tutti i partecipanti | Presentazione principale |
| Executive summary (1 pagina) | PDF | C-Level | Sintesi per chi non può partecipare |
| Analisi TCO dettagliata | Excel | CFO / Finance | Dati economici completi |
| Confronto funzionale | PDF | IT Operations | Dettaglio tecnico |
| Proposta commerciale | PDF | Decision maker | Offerta formale |
| Case study (1-2 pagine) | PDF | Tutti | Referenze e credibilità |
| FAQ tecniche | PDF | IT Operations | Risposte dettagliate |

### Follow-up Post-Presentazione

| Azione | Tempistica | Responsabile |
|---|---|---|
| Email di ringraziamento con materiali | Entro 24 ore | Account manager |
| Risposta a domande rimaste in sospeso | Entro 48 ore | Solution architect |
| Proposta PoC (se richiesto) | Entro 1 settimana | Team tecnico + commerciale |
| Call di follow-up | Entro 1 settimana | Account manager |
| Proposta commerciale formale | Entro 2 settimane | Account manager |

### Metriche di Successo della Presentazione

| Indicatore | Positivo | Da migliorare |
|---|---|---|
| Domande durante la presentazione | Molte e specifiche | Poche o generiche |
| Interesse per il PoC | Richiesto dal cliente | Nessun interesse |
| Richiesta di referenze | Sì | No |
| Coinvolgimento del CFO | Attento ai numeri | Disinteressato |
| Prossimi passi concordati | Call/meeting pianificato | "Vi faremo sapere" |
| Tempo della presentazione | Andato oltre per le domande | Finito in anticipo senza domande |

---

*Documento guida per la preparazione e l'erogazione di presentazioni di business case per la migrazione da VMware a Proxmox VE. Da personalizzare per ogni cliente e opportunità.*

---

## Esercizi

1. **Concettuale — TCO 3 anni.** Per un cluster vSphere ipotetico (4 nodi dual-socket Xeon, vSphere Standard + vSAN + NSX bundle), calcola: TCO VMware 3 anni post-Broadcom (assumere +250% vs prezzo precedente), TCO Proxmox 3 anni (Enterprise subscription 4 sockets), saving netto, costi migrazione one-time, payback period.

2. **Stretch — preparare presentazione 30 minuti.** Slides + script + Q&A. Audience: CIO + CFO + IT Director di una azienda 200 dipendenti, 80 VM, attualmente vSphere Essentials Plus. Obiettivo: ottenere autorizzazione POC.

## Auto-valutazione

1. Quale evento del 2023 ha cambiato drasticamente il panorama VMware?
2. Differenza tra Proxmox No-Subscription, Community Subscription e Enterprise Subscription.
3. Tipico payback period di una migrazione VMware → Proxmox.
4. Quali sono i 3 stakeholder C-level e come adattare il messaggio?
5. POC scope: cosa includere e cosa escludere?

## Letture primarie consigliate

- Proxmox — Subscription Plans. https://www.proxmox.com/en/proxmox-virtual-environment/pricing (retrieved 2026-04-27).
- Broadcom acquisition of VMware — press release 2023-11-22. https://news.broadcom.com/release-details/broadcom-completes-acquisition-of-vmware/ (retrieved 2026-04-27).
- The Register / Computerworld coverage of post-Broadcom VMware pricing (2024). https://www.theregister.com/Tag/VMware/ (retrieved 2026-04-27).
- Industry reports: Gartner, IDC su hypervisor market shift 2024-2025 (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 99 — `../99-CASE-STUDY/broadcom-vmware-2024.md`: case study dettagliato del cambiamento Broadcom.
- Tutti i moduli tecnici (01-14): substrato di credibilita per il business case.

## Glossario locale

| Termine | Definizione |
|---|---|
| **TCO** | Total Cost of Ownership; somma costi acquisizione + operativi + dismissione su orizzonte definito. |
| **ROI** | Return on Investment. |
| **Payback period** | Tempo necessario per recuperare l'investimento. |
| **POC** | Proof of Concept; pilot scoped per validare un'ipotesi. |
| **Wave migration** | Strategia di migrazione a fasi successive. |
| **Broadcom acquisition** | 2023-11-22, Broadcom acquisisce VMware per ~$61B. |
| **Bundling** | Forzata vendita di prodotti combinati (vSphere + vSAN + NSX). |
| **Channel program** | Modello commerciale per partner/reseller. |
| **Subscription model** | Pagamento annuo invece di acquisto perpetuo. |
| **CFO** | Chief Financial Officer. |
| **CTO** | Chief Technology Officer. |
| **CIO** | Chief Information Officer. |
