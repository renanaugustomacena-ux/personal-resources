# Timeline di Migrazione e Risk Assessment

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 2 — Assessment · Modulo 05.4 (chiude la Fase 2; vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 05.1, 05.2, 05.3 (tutti gli output di assessment precedenti); concetti di project management base, risk management ISO 31000, change management ITIL/Prosci ADKAR.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. costruire una timeline realistica di programma di migrazione (3-6-12 mesi tipici per parchi 50-500 VM), con milestones, dipendenze fra wave e finestre di approvvigionamento hardware;
> 2. produrre una **risk matrix** (probabilita × impatto) categorizzata su rischi tecnici (HW vetusto, snapshot stale, dipendenze), business (downtime non pianificato, perdita dati, SLA breach) e di progetto (skill gap, vendor delays, sovrapposizione con altri progetti IT);
> 3. definire mitigation strategies per ciascun rischio (riduzione probabilita / riduzione impatto / accettazione esplicita / trasferimento), con owner e KPI di chiusura;
> 4. compilare una go/no-go checklist per ogni wave, oggettiva e tracciabile (lista di item PASS/FAIL, no item "sentito di tipo");
> 5. progettare il change management lato umano (ADKAR / ITIL Change Enablement) per coinvolgere owner, end-user e stakeholder business in modo che la migrazione tecnica non si scontri con resistenza organizzativa;
> 6. produrre il Gantt chart finale del programma con dipendenze fra task, percorso critico e buffer espliciti per imprevisti.
> **Tempo stimato:** lettura 60-90 min · pianificazione 240-480 min (su un programma reale)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** ISO 31000:2018; ITIL 4; PMBOK 7th edition; Prosci ADKAR 3.0.

## Mappa concettuale

```
+======================================================+
|  Timeline + Rischio: l'output finale dell'assessment |
+======================================================+
|                                                      |
|   INPUT                                              |
|     +-- 05.1 inventory                               |
|     +-- 05.2 dipendenze + tier                       |
|     +-- 05.3 sizing target + BOM hardware            |
|         |                                            |
|         v                                            |
|   TIMELINE                                           |
|     +-- Wave 0: hardware procurement (4-12 sett.)    |
|     +-- Wave 0.5: install + config target cluster    |
|     +-- Wave 1: pilot (5-10 VM, 2 settimane)         |
|     +-- Wave 2..N: progressive (per tier/dipendenze) |
|     +-- Wave finale: T0 + cleanup VMware             |
|     +-- Decommissioning VMware (1-3 mesi dopo)       |
|         |                                            |
|         v                                            |
|   RISK MATRIX                                        |
|     +-- Tecnici: HW vetusto, snapshot, RDM, ...      |
|     +-- Business: downtime, dati, SLA                |
|     +-- Progetto: skill, fornitori, scope creep      |
|         |                                            |
|         v                                            |
|   MITIGATION STRATEGIES                              |
|     +-- Reduce probability                           |
|     +-- Reduce impact                                |
|     +-- Accept explicitly (con owner)                |
|     +-- Transfer (assicurazione, contractor)         |
|         |                                            |
|         v                                            |
|   GO/NO-GO CHECKLIST per WAVE                        |
|         |                                            |
|         v                                            |
|   CHANGE MANAGEMENT (ADKAR/ITIL)                     |
|     +-- Awareness, Desire, Knowledge, Ability,       |
|         Reinforcement                                |
|         |                                            |
|         v                                            |
|   GANTT FINALE                                       |
|     percorso critico, buffer, ownership              |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **La timeline parte dall'hardware, non dal software.** Approvvigionamento di server enterprise oggi (2026) richiede 4-12 settimane (peggio per CPU di ultima generazione, meglio per stock standard). Pianificare la timeline a partire dalla data di disponibilita hardware, non dalla data di kick-off progetto.
2. **Pilot wave: bassa criticita, alta osservabilita.** Selezionare 5-10 VM stand-alone Tier 3 per il pilot e *misurare tutto*: tempo per VM, tasso di rollback, problemi inattesi, skill gap del team. I dati del pilot ricalibrano le stime per le wave successive.
3. **Risk matrix: 3 categorie, 1 owner per riga.** Ogni riga della matrix ha (a) descrizione concisa, (b) probabilita 1-5, (c) impatto 1-5, (d) score = P*I, (e) mitigation, (f) owner (persona, non team), (g) target date di chiusura. Senza owner, il rischio non viene gestito.
4. **Go/no-go: niente "feeling".** La checklist deve avere 100% PASS prima di procedere. Item tipici: hardware shipped+racked, network configurata e testata, backup pre-migrazione validato (restore di prova fatto), comunicazione inviata >48 h prima, runbook reviewed e approvato, rollback testato, monitoring attivo, on-call team pronto. Item "feeling che vada bene" *non* fa parte della checklist.
5. **Change management e meta del lavoro.** ADKAR: Awareness (perche cambiamo), Desire (perche dovrei volerlo), Knowledge (cosa devo imparare), Ability (mi serve practice), Reinforcement (continuiamo a sostenerlo dopo). Tradotto in pratica: kickoff meeting trasparente, training del team operativo, doc handover a fine wave, post-mortem condivisi, riconoscimento espliciti dei wins.

## Indice
- [Panoramica](#panoramica)
- [Stima della Timeline di Migrazione](#stima-della-timeline-di-migrazione)
- [Approccio per Fasi: Pilot, Wave, Decommission](#approccio-per-fasi-pilot-wave-decommission)
- [Esempio di Gantt Chart](#esempio-di-gantt-chart)
- [Risk Matrix: Rischi Tecnici, Business e di Progetto](#risk-matrix-rischi-tecnici-business-e-di-progetto)
- [Strategie di Mitigazione](#strategie-di-mitigazione)
- [Go/No-Go Checklist](#gono-go-checklist)
- [Change Management Planning](#change-management-planning)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La pianificazione temporale e la gestione del rischio sono i due pilastri che determinano il successo o il fallimento di un progetto di migrazione da VMware a Proxmox. Una timeline irrealistica genera pressione che porta a scorciatoie, test insufficienti e incidenti evitabili. Una gestione del rischio superficiale lascia il team impreparato quando — non se — si verificano problemi.

Questo documento fornisce un framework completo per stimare la durata del progetto, strutturarlo in fasi con gate di approvazione, identificare e classificare i rischi, definire strategie di mitigazione concrete e stabilire processi di change management che garantiscano il controllo dell'operazione. L'approccio è conservativo per design: è molto più facile accelerare un progetto in anticipo sui tempi che recuperare un progetto in ritardo.

La complessità della timeline dipende da tre fattori principali: il numero di VM da migrare, la loro criticità e interdipendenza, e la maturità del team con la piattaforma Proxmox. Un'azienda con 50 VM Tier 2-3 e un team già competente su Proxmox può completare in 6-8 settimane. Un'azienda con 500 VM, workload Tier 0-1 complessi e nessuna esperienza Proxmox deve pianificare 6-12 mesi.

---

## Stima della Timeline di Migrazione

### Fattori che Influenzano la Durata

| Fattore | Impatto sulla Durata | Dettaglio |
|---------|---------------------|-----------|
| Numero di VM | Lineare | ~30-60 minuti per VM (media, inclusi test) |
| Dimensione storage per VM | Significativo | Transfer rate tipico: 50-150 MB/s per VM in migrazione |
| Criticità workload | Alto | VM Tier 0-1 richiedono 3-5× più tempo per test e validazione |
| Complessità rete | Medio | Ogni VLAN/subnet richiede mapping e validazione |
| Esperienza team | Alto | Team esperto: ×1.0, team in formazione: ×1.5-2.0 |
| Disponibilità finestre | Critico | Finestre di manutenzione limitate allungano i tempi |
| Dipendenze esterne | Variabile | Vendor, compliance, contratti possono bloccare |

### Formula di Stima Base

```
Durata_Totale = Fase_Preparazione + Fase_Pilot + Somma(Fase_Wave_i) + Fase_Decommission + Buffer

Dove:
  Fase_Preparazione = 2-4 settimane (assessment, procurement, setup Proxmox)
  Fase_Pilot        = 1-2 settimane (2-5 VM non critiche)
  Fase_Wave_i       = (Num_VM_wave × Tempo_Per_VM + Tempo_Test_Wave) / Ore_Disponibili_Per_Settimana
  Fase_Decommission = 2-4 settimane (verifica, spegnimento VMware, documentazione)
  Buffer            = 20-30% del totale (per imprevisti)

Tempo_Per_VM (tipico):
  VM piccola  (< 100 GB, Tier 3):      30-60 minuti
  VM media   (100-500 GB, Tier 2):     1-3 ore
  VM grande  (500 GB - 2 TB, Tier 1):  3-8 ore
  VM critica (> 2 TB, Tier 0):         8-24 ore + giorno di validazione
```

### Tabella Stima per Dimensione Ambiente

| Dimensione | VM | Durata Stimata | Nota |
|------------|-----|---------------|------|
| Piccolo | 10-30 | 4-8 settimane | 1 wave + pilot |
| Medio | 30-100 | 8-16 settimane | 3-4 wave + pilot |
| Grande | 100-300 | 16-30 settimane | 6-10 wave + pilot |
| Enterprise | 300-1000+ | 6-18 mesi | 15-30 wave, team dedicato |

### Calcolo Tempo di Trasferimento Storage

Il tempo di trasferimento dei dischi virtuali è spesso il bottleneck:

```
Tempo_Trasferimento = Dimensione_Disco / Velocità_Trasferimento

Velocità tipiche:
  Rete 1 GbE:    ~100 MB/s teorico, ~80 MB/s effettivo    → 1 TB in ~3.5 ore
  Rete 10 GbE:   ~1 GB/s teorico, ~800 MB/s effettivo     → 1 TB in ~20 minuti
  Rete 25 GbE:   ~2.5 GB/s teorico, ~2 GB/s effettivo     → 1 TB in ~8 minuti
  USB 3.0:       ~500 MB/s teorico, ~350 MB/s effettivo    → 1 TB in ~48 minuti

Con conversione VMDK → qcow2 (overhead CPU di conversione):
  Aggiungere 20-40% al tempo di trasferimento puro

Esempio:
  50 VM con storage totale usato: 8 TB
  Rete 10 GbE con conversione:
  Tempo = 8 TB / 800 MB/s × 1.3 = ~3.6 ore di trasferimento puro
  Con parallelismo di 3 VM simultanee: ~1.2 ore
  Con overhead di test e configurazione: ~4-6 ore per wave
```

---

## Approccio per Fasi: Pilot, Wave, Decommission

### Fase 0: Preparazione (Settimane 1-4)

**Obiettivo**: Setup dell'ambiente Proxmox, formazione team, definizione processi.

Attività:
1. **Assessment completato** (prerequisito — documentato in file separati)
2. **Procurement hardware** — ordine, consegna, rack & stack dei server Proxmox
3. **Installazione Proxmox VE** — setup cluster, configurazione Ceph/storage
4. **Configurazione networking** — bridge, VLAN, bonding, firewall rules
5. **Setup monitoring** — Prometheus/Grafana, alerting, log aggregation
6. **Formazione team** — training Proxmox VE per il team operativo
7. **Documentazione processi** — runbook migrazione, checklist, procedure rollback
8. **Setup tooling** — script di migrazione, automazione, testing framework

**Gate di uscita**: ambiente Proxmox funzionante, team formato, processi documentati.

### Fase 1: Pilot (Settimane 5-6)

**Obiettivo**: Validare il processo di migrazione end-to-end su VM a basso rischio.

```
Criteri di selezione VM pilot:
  ✓ Tier 3 (basso impatto business)
  ✓ Risk score < 20
  ✓ Nessuna dipendenza critica
  ✓ Owner disponibile per test
  ✓ Rappresentative dei tipi di VM presenti (Linux, Windows, diverse dimensioni)
  ✓ 3-5 VM totali

Processo pilot:
  1. Migrazione della VM (export VMDK → import in Proxmox)
  2. Validazione funzionale completa
  3. Test di performance vs baseline
  4. Test di rollback (tornare a VMware)
  5. Documentazione lesson learned
  6. Aggiornamento runbook con correzioni
```

**Gate di uscita**: 100% VM pilot funzionanti, performance entro tolleranza, rollback testato.

### Fase 2: Wave di Migrazione (Settimane 7-N)

**Obiettivo**: Migrazione progressiva di tutte le VM, dalla meno critica alla più critica.

Struttura di ogni wave:

```
┌──────────────────────────────────────────────────────────┐
│                    STRUTTURA WAVE                         │
├──────────────┬───────────────────────────────────────────┤
│ Pre-Wave     │ • Go/No-Go decision meeting               │
│ (Giorno -1)  │ • Verifica prerequisiti                    │
│              │ • Comunicazione agli stakeholder            │
│              │ • Backup/snapshot VMware pre-migrazione     │
│              │ • Verifica capacità cluster Proxmox         │
├──────────────┼───────────────────────────────────────────┤
│ Migrazione   │ • Export dischi da VMware                  │
│ (Giorno 0)   │ • Conversione formato (VMDK → qcow2/raw)  │
│              │ • Import in Proxmox                        │
│              │ • Configurazione VM (rete, boot, agent)    │
│              │ • Avvio e verifica base                    │
├──────────────┼───────────────────────────────────────────┤
│ Validazione  │ • Test funzionali applicativi             │
│ (Giorno 1-2) │ • Verifica performance vs baseline         │
│              │ • Verifica connettività rete               │
│              │ • Verifica backup funzionante              │
│              │ • Sign-off team applicativo                │
├──────────────┼───────────────────────────────────────────┤
│ Stabiliz.    │ • Monitoraggio intensivo (72 ore)          │
│ (Giorno 2-5) │ • Verifica batch notturni / schedulati     │
│              │ • VM VMware originale in standby (non      │
│              │   cancellata, solo spenta)                 │
├──────────────┼───────────────────────────────────────────┤
│ Chiusura     │ • Conferma stabilità                      │
│ (Giorno 5-7) │ • Aggiornamento CMDB/documentazione        │
│              │ • Lesson learned per wave successiva       │
│              │ • Decisione Go per wave successiva         │
└──────────────┴───────────────────────────────────────────┘
```

### Fase 3: Decommissioning VMware (Ultime 2-4 settimane)

**Obiettivo**: Spegnimento e rimozione sicura dell'infrastruttura VMware.

```
Processo di decommissioning:
  Settimana 1:
    • Verifica che TUTTE le VM siano migrate e funzionanti su Proxmox
    • Le VM VMware originali (spente) sono ancora intatte come safety net
    • Rimozione agent VMware Tools dalle VM migrate (se applicabile)

  Settimana 2:
    • Spegnimento host ESXi (non cancellazione)
    • Verifica nessun impatto sulle VM Proxmox
    • Periodo di osservazione (5 giorni lavorativi)

  Settimana 3:
    • Cancellazione VM VMware (dopo conferma definitiva)
    • Rimozione datastore
    • Rimozione licenze VMware dal vCenter
    • Spegnimento vCenter Server

  Settimana 4:
    • Rimozione fisica hardware (se da dismettere)
    • Oppure riutilizzo hardware come nodi Proxmox aggiuntivi
    • Documentazione finale del progetto
    • Restituzione licenze VMware (se applicabile per EULA)
```

---

## Esempio di Gantt Chart

### Scenario: 127 VM, Ambiente Medio

```
Settimana   1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16
            ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤

FASE 0: PREPARAZIONE
Assessment  ████████
Procurement ░░░░████████
Setup Proxmox    ░░░░░░░░████████
Network/Storage       ░░░░░░░░████████
Monitoring                    ████
Formazione                ████████
Runbook                       ████████

FASE 1: PILOT
Pilot (5 VM)                          ████████
Lesson Learned                                ████
Go/No-Go #1                                      ██

FASE 2: WAVE MIGRAZIONE
Wave 1: Dev/Test (15 VM)                              ████████
Wave 2: Tier 3 (20 VM)                                    ░░░░████████
Wave 3: Tier 2a (25 VM)                                            ████████
Wave 4: Tier 2b (22 VM)                                                ████████
Wave 5: Tier 1 (25 VM)                                                     ████████
Wave 6: Tier 0 (15 VM)                                                          ████████

FASE 3: DECOMMISSION
Verifica finale                                                                      ████
Spegnimento VMware                                                                       ████
Cleanup                                                                                      ████

MILESTONE
◆ Assessment completo          (fine sett. 2)
◆ Ambiente Proxmox pronto      (fine sett. 5)
◆ Pilot completato             (fine sett. 7)
◆ Go/No-Go migrazione massa    (fine sett. 8)
◆ 50% VM migrate               (fine sett. 11)
◆ 100% VM migrate              (fine sett. 14)
◆ Decommission completo        (fine sett. 16)

LEGENDA: ████ Attività principale  ░░░░ Attività preparatoria/parallela  ◆ Milestone
```

### Timeline Dettagliata per Wave

```
WAVE 5: TIER 1 (25 VM business-critical)
Settimana 12-13

  Lunedì (pre-wave):
    09:00  Go/No-Go meeting con management e team applicativi
    10:00  Verifica capacità cluster Proxmox
    11:00  Backup completo VMware (snapshot + backup solution)
    14:00  Comunicazione interna: "migrazione pianificata per martedì sera"
    16:00  Verifica checklist prerequisiti

  Martedì (migrazione — finestra 20:00-06:00):
    20:00  Inizio finestra di manutenzione
    20:15  Spegnimento graceful VM gruppo 1 (8 VM)
    20:30  Avvio export/conversione/import parallelo (3 VM alla volta)
    23:00  Gruppo 1 completato — avvio e verifica base
    23:30  Spegnimento graceful VM gruppo 2 (8 VM)
    23:45  Avvio export/conversione/import parallelo
    02:30  Gruppo 2 completato — avvio e verifica base
    03:00  Spegnimento graceful VM gruppo 3 (9 VM)
    03:15  Avvio export/conversione/import parallelo
    05:45  Gruppo 3 completato — avvio e verifica base
    06:00  Fine finestra di manutenzione

  Mercoledì (validazione):
    08:00  Inizio test funzionali con team applicativi
    12:00  Report intermedio: problemi identificati, azioni correttive
    17:00  Sign-off team applicativi per VM senza problemi

  Giovedì-Venerdì (stabilizzazione):
    Monitoraggio continuo, risoluzione problemi residui,
    verifica batch notturni, verifica performance

  Lunedì successivo (chiusura):
    09:00  Review wave: lesson learned, metriche, problemi
    10:00  Decisione: conferma wave o rollback parziale
    11:00  Aggiornamento documentazione
    14:00  Go/No-Go per wave successiva
```

---

## Risk Matrix: Rischi Tecnici, Business e di Progetto

### Matrice Probabilità × Impatto

```
                    IMPATTO
                    Basso      Medio       Alto       Critico
                 ┌──────────┬───────────┬──────────┬───────────┐
  Quasi certo    │  Medio   │   Alto    │ Critico  │  Critico  │
  (>80%)         │          │           │          │           │
  P              ├──────────┼───────────┼──────────┼───────────┤
  R  Probabile   │  Basso   │   Medio   │  Alto    │  Critico  │
  O  (50-80%)    │          │           │          │           │
  B              ├──────────┼───────────┼──────────┼───────────┤
  A  Possibile   │  Basso   │   Basso   │  Medio   │   Alto    │
  B  (20-50%)    │          │           │          │           │
  I              ├──────────┼───────────┼──────────┼───────────┤
  L  Improbabile │ Trascur. │   Basso   │  Basso   │   Medio   │
  I  (5-20%)     │          │           │          │           │
  T              ├──────────┼───────────┼──────────┼───────────┤
  A  Raro        │ Trascur. │  Trascur. │  Basso   │   Basso   │
     (<5%)       │          │           │          │           │
                 └──────────┴───────────┴──────────┴───────────┘
```

### Registro Rischi Tecnici

| ID | Rischio | Prob. | Impatto | Score | Mitigazione |
|----|---------|-------|---------|-------|-------------|
| T01 | Performance degradate post-migrazione per workload I/O intensive | Possibile | Alto | **Medio** | Benchmark pre/post, Ceph tuning, fallback a storage esterno |
| T02 | Incompatibilità driver guest OS con KVM/virtio | Possibile | Alto | **Medio** | Test pilot per ogni tipo di OS, driver virtio pre-installati |
| T03 | Corruzione dati durante conversione VMDK→qcow2 | Improbabile | Critico | **Medio** | Checksum pre/post conversione, backup prima della migrazione |
| T04 | Failure nodo Proxmox durante migrazione wave | Improbabile | Alto | **Basso** | Cluster N+1, HA abilitato, test failover pre-migrazione |
| T05 | Rete insufficiente per traffico Ceph + VM | Probabile | Medio | **Medio** | Rete dedicata Ceph, monitoring bandwidth, test di carico |
| T06 | Applicazione non funziona su hypervisor KVM | Possibile | Critico | **Alto** | PoC per applicazioni critiche, contatto vendor per supporto |
| T07 | Perdita di snapshot chain durante export VMware | Possibile | Alto | **Medio** | Consolidare snapshot prima, export dal point-in-time corretto |
| T08 | Boot failure dopo migrazione (BIOS vs UEFI) | Probabile | Medio | **Medio** | Verificare firmware type pre-migrazione, OVMF per UEFI |

### Registro Rischi Business

| ID | Rischio | Prob. | Impatto | Score | Mitigazione |
|----|---------|-------|---------|-------|-------------|
| B01 | Downtime non pianificato durante wave production | Possibile | Critico | **Alto** | Piano rollback <30 min, comunicazione proattiva |
| B02 | Impatto SLA con clienti durante migrazione | Possibile | Critico | **Alto** | Migrare fuori orario SLA, dual-stack transitorio |
| B03 | Licenze software legate a hardware/MAC | Probabile | Alto | **Alto** | Inventario licenze, contatto vendor per re-keying |
| B04 | Vendor applicativo non supporta Proxmox/KVM | Possibile | Alto | **Medio** | Verificare supportability matrix vendor prima della migrazione |
| B05 | Costo totale supera budget approvato | Possibile | Medio | **Basso** | Buffer 20% nel budget, monitoraggio costi settimanale |
| B06 | Perdita di compliance (PCI-DSS, GDPR, etc.) | Improbabile | Critico | **Medio** | Audit pre-migrazione, verifica controlli su Proxmox |

### Registro Rischi di Progetto

| ID | Rischio | Prob. | Impatto | Score | Mitigazione |
|----|---------|-------|---------|-------|-------------|
| P01 | Ritardo nella consegna hardware | Probabile | Alto | **Alto** | Ordine anticipato, fornitori alternativi, buffer timeline |
| P02 | Competenze Proxmox insufficienti nel team | Probabile | Alto | **Alto** | Formazione anticipata, engagement consulente esterno |
| P03 | Resistenza al cambiamento del team operativo | Probabile | Medio | **Medio** | Change management, formazione, coinvolgimento precoce |
| P04 | Scope creep: richieste aggiuntive durante migrazione | Quasi certo | Medio | **Alto** | Change control board, scope freeze durante wave |
| P05 | Key person dependency (conoscenza concentrata) | Possibile | Alto | **Medio** | Cross-training, documentazione, pair migration |
| P06 | Finestre di manutenzione insufficienti | Possibile | Alto | **Medio** | Negoziare finestre con il business in anticipo |

---

## Strategie di Mitigazione

### Mitigazione Tecnica: Piano di Rollback

Ogni wave deve avere un piano di rollback testato:

```
PROCEDURA DI ROLLBACK (per singola VM)
════════════════════════════════════════

Tempo stimato: 15-30 minuti per VM

Prerequisiti:
  ✓ VM originale VMware ancora presente (spenta, non cancellata)
  ✓ Snapshot VMware pre-migrazione ancora disponibile
  ✓ Configurazione rete VMware non modificata

Procedura:
  1. STOP: Spegnere la VM su Proxmox
     qm stop <vmid>

  2. RETE: Rimuovere l'IP dalla VM Proxmox per evitare conflitti
     # Se DHCP: nessuna azione
     # Se statico: rimuovere dalla configurazione Proxmox

  3. AVVIO VMWARE: Accendere la VM originale su VMware
     PowerCLI: Start-VM -VM "vm-name"

  4. VERIFICA: Test funzionale di base
     - Ping
     - Login
     - Applicazione raggiungibile
     - Connettività dipendenze

  5. COMUNICAZIONE: Notificare team e stakeholder del rollback

  6. ANALISI: Documentare la causa del rollback per remediation
     - Cosa è andato storto?
     - È risolvibile?
     - Quando riprovare?

CRITERIO PER ROLLBACK WAVE COMPLETA:
  Se più del 30% delle VM della wave hanno problemi non risolvibili
  entro la finestra di stabilizzazione → rollback dell'intera wave.
```

### Mitigazione Business: Approccio Dual-Stack

Per servizi ad alta disponibilità, implementare una fase transitoria dove il servizio è attivo sia su VMware che su Proxmox:

```
FASE TRANSITORIA DUAL-STACK (per servizi Tier 0-1)

  ┌──────────┐                    ┌──────────┐
  │  VMware  │    Load Balancer   │  Proxmox │
  │  VM-old  │◄──────┤ LB ├─────►│  VM-new  │
  │ (attiva) │       │    │       │ (attiva) │
  └──────────┘       └────┘       └──────────┘

Fase 1: VM su VMware (100% traffico)
Fase 2: VM su entrambi, LB 90/10 (smoke test)
Fase 3: VM su entrambi, LB 50/50 (validazione)
Fase 4: VM su entrambi, LB 10/90 (pre-cutover)
Fase 5: VM su Proxmox (100% traffico)
Fase 6: Spegnimento VM VMware dopo periodo di osservazione

Applicabile a: web server, application server con state gestito esternamente
NON applicabile a: database (stato replicato richiede meccanismi specifici)
```

### Mitigazione Progetto: Change Freeze e Scope Control

```
POLICY DI CHANGE FREEZE

  Durante ogni wave di migrazione:
    • Nessuna modifica alle VM in corso di migrazione
    • Nessuna modifica alla rete (VLAN, firewall, routing)
    • Nessun aggiornamento applicativo sulle VM migrata
    • Nessun cambio di configurazione sull'infrastruttura Proxmox

  Eccezioni:
    • Fix critici di sicurezza (con approvazione CAB d'emergenza)
    • Rollback di migrazione (procedura standard)

  Durata: da inizio wave a fine periodo di stabilizzazione (+5 giorni)
```

---

## Go/No-Go Checklist

### Go/No-Go Pre-Progetto (prima della Fase 0)

```
CHECKLIST GO/NO-GO: AVVIO PROGETTO
════════════════════════════════════

□ Budget approvato e allocato
□ Sponsor executive identificato
□ Team di progetto assegnato con ruoli definiti
□ Assessment VMware completato e validato
□ Contratto hardware firmato / hardware ordinato
□ Licenze Proxmox (se subscription) acquisite
□ Piano di progetto approvato dal management
□ Comunicazione agli stakeholder effettuata
□ Rischi principali identificati e mitigazioni definite
□ Criterio di rollback definito e approvato

Decisione: □ GO   □ NO-GO   □ GO CON CONDIZIONI
Approvato da: _______________ Data: _______________
```

### Go/No-Go Pre-Pilot (prima della Fase 1)

```
CHECKLIST GO/NO-GO: AVVIO PILOT
═════════════════════════════════

INFRASTRUTTURA
□ Cluster Proxmox installato e funzionante (3+ nodi)
□ Storage backend configurato e testato (Ceph/NFS/iSCSI)
□ Networking configurato (bridge, VLAN, bonding)
□ HA (High Availability) configurato e testato
□ Backup solution configurata su Proxmox (PBS o altro)
□ Monitoring e alerting operativi
□ DNS e DHCP configurati per il nuovo ambiente

PROCESSI
□ Runbook di migrazione scritto e revisionato
□ Procedura di rollback scritta e testata
□ Checklist di validazione per ogni VM definita
□ Comunicazione piano pilot a team coinvolti
□ Finestra di manutenzione per pilot concordata

COMPETENZE
□ Team formato su Proxmox VE administration
□ Team formato sullo strumento di migrazione scelto
□ Almeno 2 persone capaci di eseguire migrazione e rollback

VM PILOT
□ VM pilot selezionate (3-5 VM Tier 3)
□ Owner delle VM informati e disponibili per test
□ Baseline performance delle VM pilot raccolta
□ Backup delle VM pilot verificato

Decisione: □ GO   □ NO-GO   □ GO CON CONDIZIONI
Approvato da: _______________ Data: _______________
```

### Go/No-Go Pre-Wave (prima di ogni wave)

```
CHECKLIST GO/NO-GO: WAVE N
═══════════════════════════

PREREQUISITI
□ Wave precedente completata con successo
□ Lesson learned della wave precedente incorporate
□ Nessun problema critico aperto dalla wave precedente
□ Capacità sufficiente sul cluster Proxmox per le VM di questa wave

PREPARAZIONE
□ Lista VM della wave confermata e validata
□ Dipendenze delle VM verificate (nessuna dipendenza non migrata critica)
□ Backup pre-migrazione completato per tutte le VM della wave
□ Comunicazione stakeholder inviata (almeno 48 ore prima)
□ Finestra di manutenzione confermata

RISORSE
□ Team di migrazione disponibile per l'intera finestra
□ Team applicativo disponibile per validazione il giorno dopo
□ Supporto infrastrutturale on-call confermato
□ Contatti escalation definiti e raggiungibili

TECHNICAL READINESS
□ Cluster Proxmox health check: OK
□ Storage capacity check: sufficiente
□ Network connectivity test: OK
□ Script/tool di migrazione testati su questa classe di VM

ROLLBACK READINESS
□ VM VMware originali intatte e avviabili
□ Procedura rollback verificata
□ Tempo stimato di rollback calcolato
□ Criterio di attivazione rollback definito

Decisione: □ GO   □ NO-GO   □ GO CON CONDIZIONI
Approvato da: _______________ Data: _______________
Note: _______________________________________________
```

---

## Change Management Planning

### Modello ADKAR per la Migrazione

Il framework ADKAR (Awareness, Desire, Knowledge, Ability, Reinforcement) applicato alla migrazione:

| Fase | Obiettivo | Azioni |
|------|-----------|--------|
| **Awareness** | Tutti comprendono perché si migra | Comunicazione executive, presentazione costi VMware vs Proxmox, timeline licenze VMware |
| **Desire** | Il team vuole partecipare al cambiamento | Coinvolgimento nella pianificazione, benefici per il team (nuove competenze, meno vincoli vendor) |
| **Knowledge** | Il team sa come operare su Proxmox | Training formale, lab hands-on, documentazione, mentoring |
| **Ability** | Il team è capace di operare autonomamente | Pratica su ambiente di test, shadow operations, supporto durante le prime wave |
| **Reinforcement** | Il cambiamento viene consolidato | Celebration successi, feedback loop, ottimizzazione continua, rimozione vecchi processi |

### Piano di Comunicazione

```
MATRICE DI COMUNICAZIONE
═══════════════════════════

Stakeholder         | Frequenza      | Canale         | Contenuto
────────────────────┼────────────────┼────────────────┼───────────────────────
Executive sponsor   | Settimanale    | Report + call  | Status, rischi, budget
IT Management       | Settimanale    | Meeting        | Avanzamento, problemi
Team operativo      | Giornaliera    | Stand-up       | Task, blocchi, supporto
Team applicativi    | Per wave       | Email + call   | Piano wave, impatti, test
Utenti finali       | Per wave       | Email aziendale| Finestre manutenzione
Vendor/fornitori    | Al bisogno     | Email/ticket   | Supporto, compatibilità
Security team       | Bi-settimanale | Meeting        | Compliance, audit
```

### Template di Status Report

```
STATUS REPORT — MIGRAZIONE VMWARE → PROXMOX
Data: _______________
Settimana: ___/___

SEMAFORO GENERALE: 🟢 Verde / 🟡 Giallo / 🔴 Rosso

AVANZAMENTO:
  VM totali:           127
  VM migrate:          45 (35%)
  VM in corso (wave):  22
  VM pianificate:      60
  VM in rollback:      0

  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░ 35%

MILESTONE:
  ✓ Assessment completato                 (completato sett. 2)
  ✓ Ambiente Proxmox pronto               (completato sett. 5)
  ✓ Pilot completato                      (completato sett. 7)
  → Wave 3 in corso                       (previsto: sett. 10)
  ○ 50% VM migrate                        (previsto: sett. 11)
  ○ 100% VM migrate                       (previsto: sett. 14)
  ○ Decommission completo                 (previsto: sett. 16)

PROBLEMI APERTI:
  #1 [ALTO] VM db-oracle-02: performance I/O 40% peggiori
     → Azione: tuning Ceph, possibile switch a LVM-thin locale
     → Owner: Team Infra
     → Scadenza: fine settimana

RISCHI ATTUALIZZATI:
  T06 → Vendor SAP ha confermato supporto KVM: RISCHIO CHIUSO
  B03 → 3 VM con licenze legate a MAC: contattato vendor, in attesa

BUDGET:
  Previsto: €65,000
  Speso:    €48,000
  Forecast: €62,000 (sotto budget)

PROSSIMI PASSI:
  - Completare Wave 3 entro venerdì
  - Go/No-Go Wave 4 lunedì prossimo
  - Risolvere problema performance db-oracle-02
```

### Formazione del Team

| Modulo | Durata | Pubblico | Contenuto |
|--------|--------|----------|-----------|
| Proxmox VE Fundamentals | 2 giorni | Tutto il team IT | Installazione, GUI, CLI, VM management |
| Proxmox Cluster & HA | 1 giorno | Team infrastruttura | Corosync, HA, live migration, fencing |
| Ceph Administration | 2 giorni | Team storage | OSD, MON, pool, tuning, recovery |
| Networking in Proxmox | 1 giorno | Team network | Bridge, VLAN, bonding, SDN, firewall |
| Backup con PBS | 0.5 giorni | Team backup | Proxmox Backup Server, policy, restore |
| Migration Tooling | 1 giorno | Team migrazione | qm importdisk, virt-v2v, script custom |

---

## Best Practices

- **Non comprimere la timeline per pressioni di business**. I risparmi sulle licenze VMware non valgono un outage di produzione causato da una migrazione affrettata. Se il business preme, negoziare il rinnovo a breve termine delle licenze VMware per avere il tempo necessario.
- **Mantenere le VM VMware originali per almeno 2 settimane dopo ogni wave**. Non cancellare mai le VM sorgente immediatamente dopo la migrazione. Il periodo di osservazione è fondamentale per identificare problemi che si manifestano solo sotto carico reale o durante operazioni periodiche.
- **Eseguire sempre un dry-run del rollback prima di ogni wave production**. Il piano di rollback deve essere testato, non solo documentato. Simulare il rollback su una VM non critica prima di ogni wave.
- **Limitare le wave a un massimo di 15-20 VM**. Wave più grandi diventano ingestibili in caso di problemi. È meglio avere più wave piccole che poche wave grandi.
- **Congelare i cambiamenti durante le wave**. Nessuna modifica applicativa, infrastrutturale o di rete durante una wave. Ogni variabile in più aumenta esponenzialmente la complessità del troubleshooting in caso di problemi.
- **Coinvolgere i team applicativi nella validazione, non solo il team infrastruttura**. L'infrastruttura può vedere che la VM è accesa e raggiungibile. Solo il team applicativo può confermare che l'applicazione funziona correttamente end-to-end.
- **Documentare le lesson learned dopo ogni wave**. Creare un registro strutturato dei problemi incontrati e delle soluzioni applicate. Questo registro è prezioso per le wave successive e per future migrazioni.
- **Prevedere buffer temporali generosi**. Aggiungere almeno il 25% di buffer alla stima iniziale. I progetti di migrazione sottostimano sistematicamente la durata reale.
- **Avere un piano B per ogni componente critico**. Se Ceph non performa come atteso, avere pronto il fallback su storage esterno. Se virt-v2v non funziona per certi OS, avere pronto un processo manuale alternativo.

---

## Troubleshooting

### Problema: Wave in ritardo rispetto alla timeline prevista
**Sintomi**: La migrazione delle VM sta richiedendo più tempo del previsto. La finestra di manutenzione non è sufficiente.
**Causa**: Sottostima del tempo di trasferimento storage, problemi di conversione formato, test funzionali più lunghi del previsto, problemi di rete che rallentano il trasferimento.
**Soluzione**: (1) Parallelizzare ulteriormente le migrazioni (più VM simultanee se la rete lo permette); (2) Pre-copiare i dischi in anticipo (cold copy durante orario lavorativo, poi sync finale nella finestra); (3) Ridurre il numero di VM per wave; (4) Estendere la finestra di manutenzione (negoziare con il business).
**Prevenzione**: Testare il tempo reale di migrazione durante il pilot e usare quei dati (non stime teoriche) per pianificare le wave. Aggiungere il 30% di buffer al tempo misurato.

### Problema: Stakeholder rifiuta il Go per la wave
**Sintomi**: Durante il Go/No-Go meeting, uno stakeholder pone il veto sulla wave per motivi non tecnici (paura, incertezza, mancanza di fiducia).
**Causa**: Comunicazione insufficiente, mancato coinvolgimento dello stakeholder nelle fasi precedenti, esperienza negativa con migrazioni passate, rischi percepiti non adeguatamente mitigati.
**Soluzione**: Ascoltare le preoccupazioni specifiche dello stakeholder. Proporre mitigazioni concrete per ogni preoccupazione. Se necessario, ridurre lo scope della wave (meno VM, solo VM meno critiche) per costruire fiducia. Non forzare mai il Go contro la volontà di uno stakeholder chiave.
**Prevenzione**: Coinvolgere tutti gli stakeholder fin dalla fase di assessment. Condividere risultati del pilot e lesson learned. Offrire demo dell'ambiente Proxmox e del processo di migrazione.

### Problema: Rollback necessario ma VM VMware originale non avviabile
**Sintomi**: Si tenta il rollback ma la VM VMware originale non si avvia, o si avvia con dati non aggiornati.
**Causa**: Snapshot VMware corrotto o rimosso, datastore VMware già riutilizzato, disco VMware modificato dopo la migrazione.
**Soluzione**: (1) Ripristinare dal backup pre-migrazione (Veeam, VADP-based); (2) Se il backup non è disponibile, estrarre i dati dalla VM Proxmox e ricostruire su VMware; (3) In caso estremo, mantenere la VM su Proxmox e risolvere i problemi lì.
**Prevenzione**: Verificare l'integrità della VM VMware originale PRIMA di iniziare la migrazione. Non toccare mai la VM VMware originale dopo la migrazione fino al termine del periodo di osservazione. Mantenere backup indipendenti (non solo snapshot).

### Problema: Performance applicative degradate dopo migrazione riuscita
**Sintomi**: La VM è migrata e funzionante ma le performance applicative sono peggiori. Utenti lamentano lentezza. Metriche applicative (response time, throughput) peggiorate rispetto alla baseline.
**Causa**: Molteplici possibilità: driver virtio non installati (emulazione IDE/SATA), NUMA non configurato, CPU type conservative (qemu64 invece di host), storage backend più lento, network MTU non ottimale, memory ballooning attivo indebitamente.
**Soluzione**: Verificare sistematicamente ogni componente:
```bash
# Verificare driver nel guest Linux
lspci | grep -i virtio    # Devono essere presenti virtio-blk o virtio-scsi e virtio-net
lsmod | grep virtio

# Verificare NUMA nel guest
numactl --hardware

# Verificare I/O scheduler
cat /sys/block/vda/queue/scheduler   # Dovrebbe essere 'none' o 'mq-deadline' per virtio

# Benchmark I/O rapido
fio --name=test --ioengine=libaio --iodepth=32 --rw=randread --bs=4k --direct=1 --size=1G --numjobs=4 --runtime=60 --group_reporting
```
**Prevenzione**: Installare driver virtio PRIMA della migrazione quando possibile (specialmente su Windows). Configurare `cpu: host` e NUMA per tutte le VM di produzione. Eseguire benchmark subito dopo la migrazione, non attendere le lamentele degli utenti.

### Problema: Conflitto IP dopo migrazione
**Sintomi**: La VM migrata non è raggiungibile, oppure la raggiungibilità è intermittente. ARP conflict rilevato.
**Causa**: La VM VMware originale è ancora accesa, oppure il DHCP ha assegnato l'IP a un altro dispositivo durante il downtime della migrazione, oppure il MAC address è cambiato e il DHCP ha assegnato un IP diverso.
**Causa**: VM VMware originale non spenta correttamente, o DHCP lease non gestito.
**Soluzione**: (1) Verificare che la VM VMware sia effettivamente spenta; (2) Se IP statico: controllare ARP table sullo switch/router; (3) Se DHCP: verificare la reservation e il lease; (4) Flush ARP cache su gateway: `arp -d <ip>`.
**Prevenzione**: Spegnere SEMPRE la VM VMware prima di avviare la VM Proxmox. Per VM con IP statico, verificare che la configurazione rete nella VM Proxmox sia corretta prima dell'avvio. Per DHCP, creare reservation basate sul nuovo MAC address.

### Problema: Scoperta tardiva di dipendenza non mappata
**Sintomi**: Dopo la migrazione di una wave, un servizio su una VM non migrata smette di funzionare. Il team scopre una dipendenza che non era nella matrice.
**Causa**: Assessment delle dipendenze incompleto. La dipendenza era attiva solo durante operazioni periodiche non coperte dal periodo di osservazione, oppure era una dipendenza indiretta (A → B → C, dove C è migrato ma la dipendenza era documentata solo come A → B).
**Soluzione**: (1) Identificare esattamente la dipendenza mancante; (2) Se la VM dipendente è su VMware: riconfigurare per puntare alla nuova posizione Proxmox (nuovo IP/hostname se cambiato); (3) Se serve rollback: eseguire rollback della VM migrata e aggiornare il piano wave.
**Prevenzione**: Eseguire un monitoring attivo delle connessioni di rete per almeno 48 ore dopo ogni wave. Confrontare i flussi di rete post-migrazione con la baseline per identificare connessioni interrotte.

---

## Riferimenti

- Proxmox VE Administration Guide: https://pve.proxmox.com/pve-docs/pve-admin-guide.html
- Proxmox VE — High Availability: https://pve.proxmox.com/wiki/High_Availability
- PROSCI ADKAR Model: https://www.prosci.com/methodology/adkar
- ITIL 4 — Change Enablement: https://www.axelos.com/best-practice-solutions/itil
- PMI — Risk Management: https://www.pmi.org/learning/library/risk-management-project-7070
- ISO 31000:2018 — Risk Management Guidelines: https://www.iso.org/standard/65694.html
- VMware virt-v2v Migration Tool: https://libguestfs.org/virt-v2v.1.html
- Proxmox Migration Guide: https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — Critical Path Method (CPM) applicato a wave migration.** Per timeline complesse (>3 mesi, >10 wave), modellare le dipendenze fra wave come grafo aciclico orientato e calcolare il critical path con CPM. Strumenti: GanttProject (open source), MS Project, ProjectLibre, o un foglio Excel ben fatto. Il critical path identifica le wave in cui *qualunque* slip impatta la deadline complessiva — meritano buffer doppio. Le wave fuori dal critical path tollerano slip senza impatto sulla deadline. Misurare CPM = sapere dove rinforzare, dove rilassare.

> **Errore comune — Risk matrix "live" che non viene aggiornata.** Una risk matrix prodotta a inizio progetto e non rivisitata diventa documentazione storica, non strumento di gestione. Best practice: review settimanale di 30 min con il team operativo. Item da chiudere: rischi mitigati o accettati esplicitamente; nuovi rischi emersi (skill gap che non avevi previsto, vendor delay, snapshot scoperti durante migrazione, ecc.). Il file `risk-matrix.csv` con colonna `last_updated` puo essere validato automaticamente: se ha rischi `open` con `last_updated > 14 gg`, alert automatico.

> **Caso reale — Decommissioning VMware troppo presto.** Un'azienda ha decommissionato il vecchio cluster VMware 2 settimane dopo la fine della Wave finale, per pressioni di costo (rinnovo licenze in scadenza). Tre settimane dopo, una VM migrata mostrava un comportamento anomalo causato da una corruzione FS al momento della conversione VMDK → qcow2. Sarebbe stato banale ripartire dall'origine VMware se ancora viva. Lesson: lasciare il source cluster operativo (in maintenance mode, accesso solo a operatori) per *almeno* 4-8 settimane dopo l'ultima wave. Il costo di licensing vale come polizza assicurativa.

---

## Esercizi

1. **Concettuale — finestra di approvvigionamento.** Spiegare in 5 righe perche una timeline che parte dalla data di kick-off progetto senza considerare HW lead time e probabilmente sbagliata di 1-3 mesi. Citare 2-3 categorie di componenti che hanno lead time storicamente lunghi nei cicli 2024-2026 (es. CPU EPYC top-bin, NVMe enterprise alta capacita, NIC 100 GbE specifiche).

2. **Lab — risk matrix per il proprio lab.** Compilare una risk matrix per il proprio scenario di lab (anche piccolo): 5 VM, lab a 3 nodi, NFS shared. Identificare almeno 8 rischi (3 tecnici, 3 business simulati, 2 progetto), assegnare P 1-5 e I 1-5, calcolare score, definire mitigation, owner, target. Salvare come `risk-matrix-lab.csv`.

3. **Scenario — go/no-go fail.** Sei al go/no-go della Wave 3 (mid-importance). Checklist al 90% PASS, 10% NO: backup non testato (un restore non e stato fatto), monitoring incompleto (Zabbix non ha trigger su 2 metriche critiche), comunicazione utenti spedita 36 h prima invece di 48 h. Argomenta in massimo 12 righe la decisione: GO con eccezione documentata, RINVIO 24 h, RINVIO 1 settimana? *Risposta attesa:* RINVIO 24 h: backup non testato e show-stopper (rischio dati irreversibile), gli altri due si possono recuperare. La regola e: se anche un solo item della checklist e *show-stopper*, NO-GO; il resto si valuta caso per caso ma con explicit waiver firmato.

4. **Stretch — Gantt completo del programma.** Per il programma di sizing fatto in 05.3 (80 VM, 4 mesi target), produrre un Gantt chart con: 5-7 wave, ognuna con sub-task (preparazione, esecuzione, validazione, report), dipendenze fra wave, percorso critico evidenziato, buffer del 15-20% prima della deadline finale. Strumento: GanttProject open source.

## Auto-valutazione

1. Quanti mesi indicativi per migrare 100 VM eterogenee con team di 2-3 persone full-time?
2. Cos'e il "pilot wave" e cosa serve a misurare?
3. Risk matrix: come si calcola lo score finale e su quale soglia si attiva mitigation?
4. Differenza fra "reduce probability", "reduce impact", "accept", "transfer" come strategie di mitigation?
5. Go/no-go: cosa e un "show-stopper" e cosa fare se ce n'e uno?
6. ADKAR: cosa significa l'acronimo e a cosa serve in change management?
7. Quanto tempo lasciare il vecchio cluster VMware operativo dopo l'ultima wave migrata?
8. Critical Path Method: come si identifica il critical path e perche ottiene buffer doppio?

## Letture primarie consigliate

- ISO 31000:2018 — Risk Management Guidelines. https://www.iso.org/standard/65694.html
- PMI — Risk Management. https://www.pmi.org/learning/library/risk-management-project-7070
- Prosci ADKAR Model. https://www.prosci.com/methodology/adkar
- ITIL 4 — Change Enablement. https://www.axelos.com/best-practice-solutions/itil
- Project Management Body of Knowledge (PMBOK Guide), 7th ed., PMI 2021, ISBN 978-1628256642.
- *Software Engineering at Google* (Beyer, Wright, eds.), O'Reilly 2020 — capitoli su risk e migration. ISBN 978-1492082798.
- [`PVE-MIGRATE-V2V`] Proxmox VE Wiki — Migration of servers. https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE

## Collegamenti incrociati

- Modulo 05.1 — `inventario-vmware-assessment.md`: input per timing.
- Modulo 05.2 — `analisi-dipendenze-e-criticita.md`: input per ordinamento wave e tier.
- Modulo 05.3 — `dimensionamento-proxmox-capacity-planning.md`: BOM hardware e lead time.
- Modulo 06.1 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/strategie-metodi-migrazione.md`: strategie per ogni VM.
- Modulo 16.1, 16.2 — `../16-PROCEDURE-OPERATIVE-E-RUNBOOK/`: i runbook eseguibili dei wave.
- Modulo 18 (nuovo) — `../18-PRODUCTION-CUTOVER-RUNBOOK.md`: runbook orchestrato del cutover di produzione.
- Modulo 19 (nuovo) — `../19-MULTI-SITE-DR-PROXMOX.md`: DR multi-sito post-migrazione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Wave** | Gruppo di VM/servizi migrati assieme in una finestra di tempo (giorni o ore). |
| **Pilot wave** | Prima wave del programma, low-risk, alta osservabilita, finalizzata a calibrare le stime. |
| **Critical path** | Sequenza di wave/task in cui ogni slippage impatta direttamente la deadline finale. |
| **Buffer** | Margine di tempo aggiuntivo tra task per assorbire slippage senza rischiare la deadline. |
| **Risk matrix** | Tabella probabilita × impatto per ogni rischio; identifica priorita di mitigation. |
| **Mitigation strategy** | Azioni per ridurre probabilita o impatto di un rischio (oppure accettarlo, oppure trasferirlo). |
| **Go/no-go** | Decisione formale di procedere o rinviare una wave, basata su una checklist oggettiva. |
| **Show-stopper** | Item della checklist che, se NO, blocca obbligatoriamente il go. |
| **Waiver** | Accettazione formale (con firma) di procedere malgrado un item della checklist NO non show-stopper. |
| **ADKAR** | Modello Prosci: Awareness, Desire, Knowledge, Ability, Reinforcement. |
| **ITIL Change Enablement** | Processo ITIL 4 per autorizzare e tracciare i cambi al servizio. |
| **Lead time** | Tempo fra ordine e disponibilita di un componente hardware. |
| **Decommissioning** | Spegnimento e disinstallazione del vecchio cluster VMware dopo la migrazione. Mai prima di 4-8 settimane dall'ultima wave. |
