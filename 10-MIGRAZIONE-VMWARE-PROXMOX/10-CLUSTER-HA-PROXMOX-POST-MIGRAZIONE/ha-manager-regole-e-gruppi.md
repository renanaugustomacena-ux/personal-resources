# HA Manager: Regole e Gruppi

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 4 — Cluster HA post-migrazione · Modulo 10.1 (apre la sezione cluster-HA, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 02 (architettura Proxmox: `pmxcfs`, corosync, quorum); modulo 02 specifico cluster (`pvecm`, `corosync.conf`); concetti generali di consensus distribuito (quorum, split-brain, fencing); fluenza `systemd` per analisi `journalctl -u pve-ha-lrm/-crm`.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere i ruoli di **CRM** (Cluster Resource Manager — uno solo, master eletto, prende decisioni di failover) e **LRM** (Local Resource Manager — uno per nodo, esegue gli ordini del CRM); descrivere l'elezione del CRM master via lock di `pmxcfs` e il ruolo del watchdog;
> 2. configurare l'HA su VM e container con `ha-manager add vm:<VMID>` impostando `--state` (started, stopped, ignored, disabled), `--group`, `--max_restart`, `--max_relocate`, `--comment`;
> 3. progettare i **gruppi HA** con `nodes` (membership + priorita), `restricted` (vincolante o preferenziale), `nofailback` (sticky vs riequilibrio); calcolare l'impatto di priorita asimmetriche (es. nodes=`pve1:2,pve2:1,pve3:1`);
> 4. comprendere il flusso di decisione HA: rilevamento failure → conferma quorum → fencing del nodo guasto → riassegnazione delle risorse al nodo target migliore → restart con conteggio `max_restart`;
> 5. gestire correttamente lo stato delle risorse: `started`/`stopped` via HA (mai `qm stop` per VM HA-managed!), `disabled` per manutenzione, `ignored` per esclusione temporanea senza rimozione;
> 6. diagnosticare e recuperare scenari di **split-brain** (cluster perde quorum, ma una "isola" pensa di essere autoritaria), **`pmxcfs` quorum loss** (filesystem cluster diventa read-only, corregge solo dopo recupero quorum), e **manual `ha-manager` interventions** (`ha-manager set <sid> --state stopped` per forzare stop, `ha-manager status` per debug);
> 7. testare il failover end-to-end (spegnimento brusco di un nodo, perdita di rete corosync, simulazione di hang del kernel) con misurazione di RTO effettivo (target: ≤ 2 min per VM <= 4 GB RAM su storage condiviso);
> 8. confrontare HA Proxmox con vSphere HA (DRS, VMCP, Proactive HA): cosa Proxmox *non* fa nativamente e quali workaround esistono (resource-aware placement via custom hookscript, anti-affinity via gruppi separati, "proactive" via Zabbix + alert + manual migrate).
> **Tempo stimato:** lettura 60-90 min · lab 240-360 min (cluster a 3 nodi, simulazione di failure scenarios)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; corosync 3.1.x; pve-ha-manager 4.x; watchdog hardware (iTCO/iAMT) o software (`softdog` kernel module).

## Mappa concettuale

```
+============================================================+
|        HA Manager Proxmox: architettura e flusso failover  |
+============================================================+
|                                                            |
|   COMPONENTI                                               |
|   - corosync (cluster comm + quorum)                       |
|   - pmxcfs   (cluster filesystem, /etc/pve)                |
|   - pve-ha-crm (Cluster Resource Manager, 1 master)        |
|   - pve-ha-lrm (Local Resource Manager, 1 per nodo)        |
|   - watchdog (hw o softdog) ─► fencing self-induced        |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   TOPOLOGIA NORMALE (3 nodi, quorum)                       |
|                                                            |
|   pve1 ── pve2 ── pve3        (anelli corosync ridondati)  |
|    │       │       │                                       |
|   LRM     LRM     LRM         (uno per nodo)               |
|    └──────┼──────┘                                         |
|           │                                                |
|        CRM master            (eletto, sul nodo lock-holder)|
|           │                                                |
|     /etc/pve/ha/manager_status (stato dichiarato)          |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   FLUSSO FAILOVER                                          |
|                                                            |
|   T0:  pve3 perde rete, perde quorum nella sua isola       |
|   T1:  pmxcfs su pve3 diventa READ-ONLY (quorum lost)      |
|   T2:  watchdog non ricevera kick → expire (~60s)          |
|   T3:  pve3 si auto-fence (reboot kernel via watchdog)     |
|   T4:  CRM su pve1/pve2 (con quorum) marca pve3 fenced     |
|   T5:  CRM riassegna risorse di pve3 al nodo target        |
|   T6:  LRM target esegue qm start su risorsa migrata       |
|                                                            |
|   Tempo totale tipico: 60-120s (watchdog default 60s)      |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   STATI DI UNA RISORSA HA                                  |
|                                                            |
|   started   default; HA mantiene running                   |
|   stopped   HA mantiene fermo (no auto-start)              |
|   disabled  rimossa dal pool HA temporaneamente            |
|   ignored   placeholder; HA non interviene                 |
|   migrate   in transizione; non comandare manualmente      |
|   error     fallita migrazione/restart > max_restart       |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   GRUPPI HA                                                |
|                                                            |
|   nodes        es. pve1:2,pve2:1,pve3:1                    |
|                  (priorita: 2 > 1, pve1 preferito)         |
|   restricted   1 = solo nodi del gruppo, mai altri         |
|                  0 = preferiti ma puo failover su altri    |
|   nofailback   1 = sticky, non torna su priorita superiore |
|                  0 = riequilibra appena disponibile        |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   COMANDI ESSENZIALI                                       |
|                                                            |
|   ha-manager status            sintesi                     |
|   ha-manager config            config attiva               |
|   ha-manager add vm:100 ...    nuova risorsa               |
|   ha-manager set vm:100 ...    modifica                    |
|   ha-manager remove vm:100     elimina                     |
|   ha-manager migrate vm:100 pve2  failover manuale         |
|   ha-manager relocate vm:100 pve2 (deprecated)             |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **HA Proxmox NON e DRS.** vSphere DRS bilancia carico in continuo; HA Proxmox riavvia su failure e basta. Per "ribilanciare" servono custom hookscript o operatore umano. Pianificare la capacity affinche un singolo nodo che cade non sovraccarichi gli altri (tipico: cluster a 3, capacita 33% riserva).
2. **Watchdog e fencing implicito sono il cuore di HA.** Senza watchdog (`softdog` kernel module o hardware iTCO/iAMT), HA *non funziona*. Un nodo che perde quorum ma non e fenced potrebbe continuare a scrivere su disco condiviso → corruzione. Il watchdog garantisce che un nodo "isolato" si suiciderebbe in ~60s.
3. **Mai `qm stop` su una VM HA-managed.** L'HA la riavviera entro pochi secondi (max_restart). Per fermarla davvero: `ha-manager set vm:100 --state stopped`. Per spegnerla temporaneamente: `--state disabled`. Per rimuoverla dal pool: `ha-manager remove vm:100`.
4. **Split-brain e raro ma catastrofico.** Su cluster a 2 nodi (mai consigliato per HA in produzione) e probabile; su 3+ nodi con corosync su rete dedicata e improbabile. Se accade, il fencing decide chi sopravvive; senza fencing, decisione arbitraria → corruzione probabile.
5. **`pmxcfs` quorum loss = `/etc/pve` read-only.** Comandi che modificano la config (qm set, ha-manager...) falliranno con "Permission denied" o "Read-only file system". Non e un bug: il cluster sta proteggendo se stesso. Ripristinare quorum (rete, recovery del nodo) prima di tentare modifiche.
6. **Configurazione HA va testata, non assunta.** "Spegnere un nodo" non e un test fittizio: e l'unico modo per scoprire che il fencing non era configurato, o che il watchdog non era abilitato, o che il timeout era 6 minuti invece di 60 secondi. Il test fa parte della messa in produzione.
7. **Gruppi HA con priorita asimmetriche evitano "tutto su un nodo dopo failover".** Senza priorita, il CRM puo concentrare le VM su un solo nodo target. Con priorita per gruppo (`pve1:2,pve2:1`) si guida la distribuzione anche post-failover.

---

## Introduzione

L'HA Manager di Proxmox VE e il componente responsabile del monitoraggio e della gestione automatica delle macchine virtuali e dei container in caso di guasto di un nodo. Quando un nodo diventa irraggiungibile e viene escluso dal cluster (tramite fencing), l'HA Manager riavvia automaticamente le risorse gestite su un nodo sano.

A differenza di VMware vSphere HA, dove la configurazione avviene quasi interamente tramite policy a livello di cluster, Proxmox HA richiede una configurazione esplicita per ogni risorsa che si desidera proteggere. Questo approccio offre un controllo granulare ma richiede maggiore attenzione nella pianificazione.

---

## Architettura dell'HA Manager

### Componenti del Sistema HA

```
+------------------------------------------------------------------+
|                    ARCHITETTURA HA PROXMOX VE                    |
+------------------------------------------------------------------+
|                                                                  |
|  Su OGNI nodo del cluster:                                       |
|  +---------------------------+                                   |
|  | pve-ha-lrm                |  Local Resource Manager           |
|  | (LRM)                     |  Gestisce risorse locali          |
|  |                           |  Esegue start/stop/migrate        |
|  +---------------------------+                                   |
|                                                                  |
|  Su UN solo nodo (il master):                                    |
|  +---------------------------+                                   |
|  | pve-ha-crm                |  Cluster Resource Manager         |
|  | (CRM)                     |  Prende decisioni HA              |
|  |                           |  Assegna risorse ai nodi          |
|  |                           |  Gestisce failover                |
|  +---------------------------+                                   |
|                                                                  |
|  Elezione del CRM master:                                        |
|  - Il nodo con il node ID piu basso e quorum diventa master     |
|  - Se il master cade, un altro nodo assume il ruolo             |
|                                                                  |
|  File di configurazione:                                         |
|  - /etc/pve/ha/resources.cfg     (risorse HA)                   |
|  - /etc/pve/ha/groups.cfg        (gruppi HA)                    |
|  - /etc/pve/ha/manager_status    (stato runtime - read only)    |
+------------------------------------------------------------------+
```

### Flusso di Decisione HA

```
1. Nodo X diventa irraggiungibile
         |
2. Corosync rileva la perdita del nodo (token timeout)
         |
3. Il cluster esegue il fencing del nodo X
   (watchdog/IPMI - il nodo viene forzatamente spento)
         |
4. CRM rileva che le risorse HA di Nodo X sono orfane
         |
5. CRM seleziona il nodo destinazione:
   a. Se esiste un HA Group -> usa la lista nodi del gruppo
   b. Se restricted=1 -> SOLO nodi nel gruppo
   c. Se restricted=0 -> preferenza per il gruppo, ma qualsiasi nodo va bene
   d. Scelta basata su priority del nodo nel gruppo
         |
6. CRM invia comando al LRM del nodo destinazione
         |
7. LRM avvia la risorsa (VM/CT) sul nodo destinazione
         |
8. CRM aggiorna lo stato in /etc/pve/ha/manager_status
```

---

## Abilitare HA sulle VM e sui Container

### Tramite GUI

La via piu semplice e dalla web GUI: selezionare la VM/CT -> More -> Manage HA.

### Tramite CLI

```bash
# Abilitare HA su una VM (VMID 100)
ha-manager add vm:100

# Abilitare HA con opzioni specifiche
ha-manager add vm:100 --state started --group produzione --max_restart 3 --max_relocate 2

# Abilitare HA su un container (CTID 200)
ha-manager add ct:200 --state started --group produzione

# Visualizzare tutte le risorse HA configurate
ha-manager config

# Output esempio:
# vm:100
#     state started
#     group produzione
#     max_restart 3
#     max_relocate 2
#     comment Web Server Principale
#
# vm:101
#     state started
#     group produzione
#     max_restart 3
#     max_relocate 2
#
# ct:200
#     state started
#     group database
#     max_restart 2
#     max_relocate 1

# Modificare una risorsa HA esistente
ha-manager set vm:100 --max_restart 5 --comment "Web Server Aggiornato"

# Rimuovere una risorsa dall'HA
ha-manager remove vm:100
```

### Parametri delle Risorse HA

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `state` | started | Stato desiderato della risorsa |
| `group` | (nessuno) | Gruppo HA di appartenenza |
| `max_restart` | 1 | Tentativi di restart sullo stesso nodo prima di relocate |
| `max_relocate` | 1 | Tentativi di spostamento su un altro nodo |
| `comment` | (vuoto) | Descrizione della risorsa |

---

## Stati delle Risorse HA

### Tabella degli Stati

```
+------------+------------------------------------------------------------------+
| Stato      | Descrizione                                                      |
+------------+------------------------------------------------------------------+
| started    | La risorsa DEVE essere in esecuzione. Se si ferma, l'HA la      |
|            | riavvia. Se il nodo cade, viene spostata su un altro nodo.      |
+------------+------------------------------------------------------------------+
| stopped    | La risorsa DEVE essere ferma. L'HA garantisce che sia spenta.   |
|            | Se qualcuno la avvia manualmente, l'HA la rispegne.             |
+------------+------------------------------------------------------------------+
| ignored    | L'HA non gestisce questa risorsa. L'operatore ha il controllo   |
|            | completo. Utile per manutenzione temporanea.                    |
+------------+------------------------------------------------------------------+
| disabled   | Equivalente a stopped. La risorsa viene fermata dall'HA.        |
+------------+------------------------------------------------------------------+
```

### Transizioni di Stato

```
                    +----> migrate (operatore richiede migrazione)
                    |        |
  stopped -------> started --+----> error (troppi restart falliti)
     ^                |      |
     |                |      +----> relocate (nodo caduto, spostamento)
     |                |
     |                v
     +---------- stopped/disabled

  ignored: stato speciale, nessuna transizione automatica
```

### Gestire gli Stati

```bash
# Impostare una risorsa come started (l'HA la avviera)
ha-manager set vm:100 --state started

# Fermare una risorsa tramite HA (modo corretto quando HA e attivo)
ha-manager set vm:100 --state stopped

# ATTENZIONE: NON usare "qm stop 100" se la VM e gestita dall'HA!
# L'HA la riavvierebbe immediatamente perche lo stato desiderato e "started"

# Mettere una risorsa in modalita ignored (per manutenzione)
ha-manager set vm:100 --state ignored

# Richiedere una migrazione tramite HA
ha-manager migrate vm:100 pve2

# Richiedere una relocazione (spegnimento + riavvio su altro nodo)
ha-manager relocate vm:100 pve2
```

---

## Gruppi HA (HA Groups)

### Concetto di Gruppo HA

I gruppi HA definiscono su quali nodi le risorse possono essere eseguite e con quale priorita. Sono l'equivalente delle VM-Host Affinity Rules di VMware.

### Creazione e Configurazione dei Gruppi

```bash
# Creare un gruppo HA base
ha-manager groupadd produzione --nodes pve1,pve2,pve3

# Creare un gruppo con priorita (nodo preferito per l'esecuzione)
ha-manager groupadd produzione --nodes "pve1:2,pve2:1,pve3:1"
# pve1 ha priorita 2 (preferito), pve2 e pve3 priorita 1

# Creare un gruppo restricted (le VM possono girare SOLO su questi nodi)
ha-manager groupadd database --nodes "pve2:2,pve3:1" --restricted 1

# Creare un gruppo con nofailback
ha-manager groupadd batch --nodes "pve1:2,pve2:1,pve3:1" --nofailback 1

# Visualizzare i gruppi configurati
ha-manager groupconfig

# Output esempio:
# group: produzione
#     nodes pve1:2,pve2:1,pve3:1
#     restricted 0
#     nofailback 0
#     comment Gruppo per VM di produzione
#
# group: database
#     nodes pve2:2,pve3:1
#     restricted 1
#     nofailback 0
#     comment Gruppo per database - solo nodi con storage veloce
#
# group: batch
#     nodes pve1:2,pve2:1,pve3:1
#     restricted 0
#     nofailback 1
#     comment Gruppo per job batch - no failback automatico

# Modificare un gruppo
ha-manager groupset produzione --nodes "pve1:3,pve2:2,pve3:1"

# Rimuovere un gruppo (prima rimuovere tutte le risorse associate)
ha-manager groupremove batch
```

### Parametri dei Gruppi HA

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `nodes` | (obbligatorio) | Lista nodi con priorita opzionale (nodo:priorita) |
| `restricted` | 0 | Se 1, le risorse possono girare SOLO sui nodi del gruppo |
| `nofailback` | 0 | Se 1, le risorse NON tornano al nodo preferito dopo il recovery |
| `comment` | (vuoto) | Descrizione del gruppo |

### Restricted vs Non-Restricted

```
Gruppo NON restricted (restricted=0):
  Nodi nel gruppo: pve1(prio:2), pve2(prio:1)

  Situazione normale: VM gira su pve1 (priorita piu alta)
  pve1 cade: VM migrata su pve2 (secondo nel gruppo)
  pve2 cade: VM migrata su pve3 (NON nel gruppo, ma permesso)

  --> Le risorse PREFERISCONO i nodi del gruppo ma possono andare altrove

Gruppo RESTRICTED (restricted=1):
  Nodi nel gruppo: pve1(prio:2), pve2(prio:1)

  Situazione normale: VM gira su pve1 (priorita piu alta)
  pve1 cade: VM migrata su pve2 (secondo nel gruppo)
  pve2 cade: VM NON PUO migrare! Rimane in stato "stopped/error"

  --> Le risorse possono girare SOLO sui nodi del gruppo
  --> Usare con cautela! Puo impedire il failover se tutti i nodi del gruppo cadono
```

### Nofailback

```
Senza nofailback (nofailback=0):
  1. VM gira su pve1 (priorita alta)
  2. pve1 cade -> VM migrata su pve2
  3. pve1 torna online -> VM migrata AUTOMATICAMENTE su pve1

  Vantaggio: Le VM tornano sempre al nodo preferito
  Svantaggio: Migrazione aggiuntiva dopo il recovery = possibile downtime

Con nofailback (nofailback=1):
  1. VM gira su pve1 (priorita alta)
  2. pve1 cade -> VM migrata su pve2
  3. pve1 torna online -> VM RIMANE su pve2

  Vantaggio: Nessuna migrazione aggiuntiva, stabilita
  Svantaggio: Le VM potrebbero non essere distribuite in modo ottimale
```

---

## Scenari Pratici di Configurazione HA

### Scenario 1: Ambiente Web Multi-Tier

```bash
# Gruppo per i web server (preferiscono nodi 1 e 2)
ha-manager groupadd web-tier --nodes "pve1:2,pve2:2,pve3:1" --nofailback 1

# Gruppo per i database (SOLO su nodi con storage NVMe locale)
ha-manager groupadd db-tier --nodes "pve2:2,pve3:1" --restricted 1

# Gruppo per servizi di supporto (qualsiasi nodo va bene)
ha-manager groupadd support --nodes "pve1:1,pve2:1,pve3:1" --nofailback 1

# Configurare le VM
ha-manager add vm:100 --state started --group web-tier --max_restart 3 --max_relocate 2 \
    --comment "Web Server Apache 1"
ha-manager add vm:101 --state started --group web-tier --max_restart 3 --max_relocate 2 \
    --comment "Web Server Apache 2"
ha-manager add vm:110 --state started --group db-tier --max_restart 2 --max_relocate 1 \
    --comment "PostgreSQL Primary"
ha-manager add vm:111 --state started --group db-tier --max_restart 2 --max_relocate 1 \
    --comment "PostgreSQL Replica"
ha-manager add vm:120 --state started --group support --max_restart 3 --max_relocate 2 \
    --comment "HAProxy Load Balancer"
ha-manager add vm:121 --state started --group support --max_restart 3 --max_relocate 2 \
    --comment "Monitoring Zabbix"
```

### Scenario 2: Separazione Ambienti Produzione/Test

```bash
# Produzione: nodi 1, 2, 3 con priorita
ha-manager groupadd prod --nodes "pve1:3,pve2:2,pve3:1" --restricted 0

# Test: solo nodo 4 e 5 (se cluster a 5 nodi)
ha-manager groupadd test --nodes "pve4:2,pve5:1" --restricted 1 --nofailback 1

# Le VM di produzione preferiscono i nodi 1-3 ma possono andare ovunque
# Le VM di test possono girare SOLO sui nodi 4-5
```

### Scenario 3: Anti-Affinity (Separazione di VM Critiche)

Proxmox non ha una funzionalita nativa di anti-affinity come VMware DRS Anti-Affinity Rules. Tuttavia, si puo simulare con gruppi HA:

```bash
# Creare gruppi separati per ogni istanza del servizio
ha-manager groupadd app-primary --nodes "pve1:3,pve2:1,pve3:1"
ha-manager groupadd app-secondary --nodes "pve2:3,pve3:1,pve1:1"

# Assegnare le istanze a gruppi diversi
ha-manager add vm:100 --state started --group app-primary \
    --comment "Application Server - Istanza 1"
ha-manager add vm:101 --state started --group app-secondary \
    --comment "Application Server - Istanza 2"

# In condizioni normali:
# VM 100 gira su pve1 (priorita 3 nel gruppo app-primary)
# VM 101 gira su pve2 (priorita 3 nel gruppo app-secondary)
# --> Le due VM sono separate su nodi diversi
```

---

## Comandi ha-manager: Riferimento Completo

### Gestione Risorse

```bash
# Aggiungere una risorsa HA
ha-manager add <tipo>:<vmid> [opzioni]
# tipo: vm o ct
# Esempio: ha-manager add vm:100 --state started --group prod

# Modificare una risorsa
ha-manager set <tipo>:<vmid> [opzioni]
# Esempio: ha-manager set vm:100 --max_restart 5

# Rimuovere una risorsa dall'HA
ha-manager remove <tipo>:<vmid>

# Visualizzare la configurazione
ha-manager config

# Visualizzare lo stato corrente
ha-manager status

# Output esempio di ha-manager status:
# quorum OK
# master pve1 (active, Wed Mar 24 10:30:00 2026)
# lrm pve1 (active, Wed Mar 24 10:30:00 2026)
# lrm pve2 (active, Wed Mar 24 10:30:00 2026)
# lrm pve3 (active, Wed Mar 24 10:30:00 2026)
# service vm:100 (pve1, started)
# service vm:101 (pve2, started)
# service vm:110 (pve2, started)
# service ct:200 (pve3, started)
```

### Operazioni sulle Risorse

```bash
# Richiedere migrazione live (online)
ha-manager migrate vm:100 pve2
# La VM viene migrata live se possibile

# Richiedere relocazione (stop + start su altro nodo)
ha-manager relocate vm:100 pve2
# La VM viene spenta sul nodo corrente e avviata su pve2

# Forzare lo stop tramite HA
ha-manager set vm:100 --state stopped

# Riavviare tramite HA
ha-manager set vm:100 --state stopped
# Attendere...
ha-manager set vm:100 --state started
```

### Gestione Gruppi

```bash
# Aggiungere un gruppo
ha-manager groupadd <nome> --nodes <lista-nodi>

# Modificare un gruppo
ha-manager groupset <nome> [opzioni]

# Rimuovere un gruppo
ha-manager groupremove <nome>

# Visualizzare la configurazione dei gruppi
ha-manager groupconfig
```

---

## File di Configurazione HA

### /etc/pve/ha/resources.cfg

```bash
# Formato del file resources.cfg
# Questo file e gestito automaticamente dai comandi ha-manager

vm: 100
    state started
    max_restart 3
    max_relocate 2
    group produzione
    comment Web Server Apache

vm: 101
    state started
    max_restart 3
    max_relocate 2
    group produzione
    comment Web Server Nginx

ct: 200
    state started
    max_restart 2
    max_relocate 1
    group database
    comment Container PostgreSQL

vm: 110
    state stopped
    group manutenzione
    comment VM in manutenzione programmata
```

### /etc/pve/ha/groups.cfg

```bash
# Formato del file groups.cfg

group: produzione
    nodes pve1:3,pve2:2,pve3:1
    restricted 0
    nofailback 0
    comment Gruppo produzione - preferenza pve1

group: database
    nodes pve2:2,pve3:1
    restricted 1
    nofailback 0
    comment Database - solo nodi con storage veloce

group: manutenzione
    nodes pve1:1,pve2:1,pve3:1
    restricted 0
    nofailback 1
    comment VM in manutenzione
```

---

## Test del Failover

### Test Controllato

```bash
# ============================================================
# TEST 1: Simulare il crash di un nodo (metodo sicuro)
# ============================================================

# 1. Verificare lo stato iniziale
ha-manager status
# Annotare su quale nodo gira ogni VM HA

# 2. Dal nodo da "crashare" (es. pve1), simulare un kernel panic
# ATTENZIONE: Questo spegne realmente il nodo!
echo c > /proc/sysrq-trigger

# Alternativa piu controllata: spegnere corosync e il watchdog fara il resto
systemctl stop corosync
# Il watchdog (se configurato) riavviera il nodo dopo il timeout

# 3. Dagli altri nodi, osservare il failover
watch -n 2 'ha-manager status'

# 4. Sequenza attesa:
# - Corosync rileva la perdita del nodo (token timeout ~5-15 secondi)
# - Il nodo viene fenced (watchdog/IPMI)
# - CRM avvia il failover delle risorse HA
# - LRM sul nodo destinazione avvia le VM/CT
# - Tempo totale: 30 secondi - 3 minuti

# ============================================================
# TEST 2: Simulare la perdita di rete corosync
# ============================================================

# Sul nodo da isolare, bloccare il traffico corosync
iptables -A INPUT -p udp --dport 5405:5412 -j DROP
iptables -A OUTPUT -p udp --dport 5405:5412 -j DROP

# Il nodo perdera il quorum e il watchdog lo riavviera
# Per ripristinare (se si fa in tempo):
iptables -F

# ============================================================
# TEST 3: Test di migrazione HA (non distruttivo)
# ============================================================

# Richiedere una migrazione HA
ha-manager migrate vm:100 pve2

# Monitorare il progresso
watch -n 1 'ha-manager status; echo "---"; qm status 100'

# La migrazione avviene in background tramite il CRM/LRM
```

### Checklist Post-Test

```bash
# Dopo ogni test di failover, verificare:

# 1. Tutte le risorse HA sono nello stato corretto
ha-manager status

# 2. Nessuna risorsa in stato di errore
ha-manager status | grep -i error

# 3. Tutti i nodi sono online
pvecm status

# 4. Il fencing ha funzionato correttamente
# Controllare i log
journalctl -u pve-ha-crm --since "30 minutes ago" | grep -i fence
journalctl -u pve-ha-lrm --since "30 minutes ago"

# 5. I servizi all'interno delle VM funzionano
# (verificare connettivita applicativa, database, etc.)

# 6. Se nofailback=0, verificare che le VM tornino al nodo preferito
# dopo il ripristino del nodo crashed
```

---

## Confronto con VMware vSphere HA

### Tabella Comparativa Dettagliata

```
+------------------------------------------+-------------------------------------------+
| VMware vSphere HA                        | Proxmox VE HA Manager                    |
+------------------------------------------+-------------------------------------------+
| HA abilitato a livello cluster           | HA abilitato per singola risorsa          |
| Tutte le VM protette per default         | Solo le VM esplicitamente aggiunte        |
| Admission Control (% risorse)            | Nessun admission control automatico       |
| VM Restart Priority:                     | HA Group priority + max_restart:          |
|   Highest / High / Medium / Low          |   priority nel gruppo (1-9)               |
|   Disabled                               |   max_restart (tentativi)                 |
+------------------------------------------+-------------------------------------------+
| VM-Host Affinity Rules:                  | HA Groups:                                |
|   "Must run on hosts in group"           |   restricted=1 (equivalente)              |
|   "Should run on hosts in group"         |   restricted=0 con priority               |
|   "Must not run on hosts in group"       |   Nessun equivalente diretto              |
+------------------------------------------+-------------------------------------------+
| VM-VM Affinity Rules:                    | Nessun supporto nativo                    |
|   "Keep together" (affinity)             |   Simulabile con gruppi HA                |
|   "Separate" (anti-affinity)             |   e priority                              |
+------------------------------------------+-------------------------------------------+
| Host Isolation Response:                 | Fencing (watchdog/IPMI):                  |
|   Power off / Shutdown / Leave powered on|   Il nodo viene riavviato/spento          |
+------------------------------------------+-------------------------------------------+
| Proactive HA (vSphere 6.5+):            | Nessun equivalente                        |
|   Migra VM da host degradati             |   (monitoraggio manuale)                  |
+------------------------------------------+-------------------------------------------+
| VM Component Protection (VMCP):          | Nessun equivalente diretto                |
|   APD / PDL handling                     |   (storage error = VM error)              |
+------------------------------------------+-------------------------------------------+
| Orchestrated Restart:                    | Nessun equivalente nativo                 |
|   VM dependency chains                   |   (script personalizzati)                 |
+------------------------------------------+-------------------------------------------+
```

### Mapping delle VMware HA Settings a Proxmox

```bash
# VMware: VM Restart Priority = "High"
# Proxmox: Usare un HA Group con priorita alta
ha-manager groupadd critical --nodes "pve1:3,pve2:2,pve3:1"
ha-manager add vm:100 --state started --group critical --max_restart 5 --max_relocate 3

# VMware: VM Restart Priority = "Low"
# Proxmox: Usare un HA Group con priorita bassa e meno tentativi
ha-manager groupadd batch --nodes "pve1:1,pve2:1,pve3:1" --nofailback 1
ha-manager add vm:200 --state started --group batch --max_restart 1 --max_relocate 1

# VMware: "Must run on hosts in group X"
# Proxmox: Gruppo restricted
ha-manager groupadd licensed --nodes "pve1:2,pve2:1" --restricted 1
ha-manager add vm:300 --state started --group licensed

# VMware: Host Isolation Response = "Power off"
# Proxmox: Fencing con watchdog (il nodo viene riavviato)
# Configurato a livello di sistema, non per singola VM
```

---

## Monitoraggio e Log dell'HA Manager

### Log del CRM e LRM

```bash
# Log del Cluster Resource Manager
journalctl -u pve-ha-crm -f

# Log del Local Resource Manager
journalctl -u pve-ha-lrm -f

# Log combinati per un evento specifico (es. failover di VM 100)
journalctl -u pve-ha-crm -u pve-ha-lrm --since "1 hour ago" | grep "vm:100"

# Esempio di log durante un failover:
# pve-ha-crm[1234]: got lock 'ha_manager_lock'
# pve-ha-crm[1234]: node 'pve1': state changed from 'online' to 'unknown'
# pve-ha-crm[1234]: node 'pve1': state changed from 'unknown' to 'fence'
# pve-ha-crm[1234]: fencing node 'pve1'
# pve-ha-crm[1234]: node 'pve1': fenced successfully
# pve-ha-crm[1234]: recover service 'vm:100' from fenced node 'pve1' to node 'pve2'
# pve-ha-lrm[5678]: starting service vm:100
# pve-ha-lrm[5678]: service vm:100 started successfully
```

### Script di Monitoraggio HA

```bash
#!/bin/bash
# /usr/local/bin/check-ha-status.sh
# Monitoraggio stato HA per integrazione con sistemi di alerting

STATUS=$(ha-manager status 2>/dev/null)

# Verificare che il CRM master sia attivo
if ! echo "$STATUS" | grep -q "master.*active"; then
    echo "CRITICAL: HA CRM master non attivo"
    exit 2
fi

# Verificare che tutti i LRM siano attivi
INACTIVE_LRM=$(echo "$STATUS" | grep "lrm" | grep -v "active" | wc -l)
if [ "$INACTIVE_LRM" -gt 0 ]; then
    echo "WARNING: $INACTIVE_LRM LRM non attivi"
    exit 1
fi

# Verificare risorse in errore
ERRORS=$(echo "$STATUS" | grep -c "error")
if [ "$ERRORS" -gt 0 ]; then
    echo "CRITICAL: $ERRORS risorse HA in stato di errore"
    echo "$STATUS" | grep "error"
    exit 2
fi

# Verificare risorse in stato di recovery
RECOVERY=$(echo "$STATUS" | grep -c "recovery\|relocat\|migrat")
if [ "$RECOVERY" -gt 0 ]; then
    echo "WARNING: $RECOVERY risorse HA in fase di recovery/migrazione"
    exit 1
fi

echo "OK: HA Manager funzionante, nessun errore"
exit 0
```

---

## Best Practice per HA in Produzione

### Raccomandazioni Generali

```
1. SEMPRE configurare il fencing prima di abilitare HA
   - Senza fencing, l'HA non puo funzionare in modo sicuro
   - Watchdog hardware e il minimo, IPMI e preferibile

2. NON mettere in HA tutte le VM
   - Solo le VM che richiedono alta disponibilita
   - Le VM di test/sviluppo non dovrebbero essere in HA

3. Pianificare la capacita N-1
   - Il cluster deve poter ospitare tutte le VM HA con un nodo in meno
   - Verificare RAM e CPU disponibili in scenario N-1

4. Testare il failover PRIMA di andare in produzione
   - Simulare il crash di ogni nodo
   - Verificare che le VM ripartano nel tempo atteso
   - Documentare i tempi di failover osservati

5. Configurare max_restart e max_relocate in modo appropriato
   - max_restart=3, max_relocate=2 e un buon default per la produzione
   - Per VM critiche: max_restart=5, max_relocate=3
   - Per VM batch: max_restart=1, max_relocate=1

6. Usare nofailback=1 per evitare migrazioni non necessarie
   - Il failback automatico causa una seconda interruzione
   - Meglio pianificare il failback manualmente in orari di manutenzione

7. Documentare i gruppi HA e la logica di distribuzione
   - Mantenere una mappa aggiornata di quali VM sono in quali gruppi
   - Documentare le ragioni dei gruppi restricted
```

### Tabella Riepilogativa dei Tempi di Failover

```
+----------------------------------+------------------+
| Fase                             | Tempo Stimato    |
+----------------------------------+------------------+
| Rilevamento guasto (corosync)    | 5-15 secondi     |
| Fencing (watchdog)               | 30-60 secondi    |
| Fencing (IPMI)                   | 10-30 secondi    |
| Avvio VM su nuovo nodo           | 10-60 secondi    |
| Boot OS nella VM                 | 30-180 secondi   |
+----------------------------------+------------------+
| TOTALE (caso migliore)           | ~1 minuto        |
| TOTALE (caso peggiore)           | ~5 minuti        |
+----------------------------------+------------------+

Confronto VMware vSphere HA:
  Rilevamento:  30 secondi (default)
  Restart VM:   dipende dal priority
  Totale:       1-5 minuti (simile)
```

---

## Conclusioni

L'HA Manager di Proxmox VE offre un meccanismo robusto per la protezione dei workload critici. Sebbene meno automatizzato rispetto a VMware vSphere HA (mancano DRS, VMCP, Proactive HA), fornisce tutti gli strumenti necessari per garantire la continuita operativa in un ambiente di produzione.

La chiave per un'implementazione HA efficace risiede nella pianificazione accurata dei gruppi, nella configurazione corretta del fencing e nei test regolari del failover. L'approccio esplicito di Proxmox (ogni risorsa deve essere aggiunta manualmente all'HA) richiede piu lavoro iniziale ma offre un controllo preciso su cosa viene protetto e come.

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — Watchdog: hardware vs softdog.** Proxmox supporta sia watchdog hardware (Intel TCO via modulo `iTCO_wdt`, AMD analoghi, server-class IPMI) sia software (`softdog` kernel module). Hardware e preferibile perche e completamente indipendente dallo stato del sistema operativo: anche se il kernel hangsa completamente, il chip TCO continua a contare e provoca un reset hardware. `softdog` invece dipende dal kernel: se il kernel hangsa in panic non recoverable, `softdog` potrebbe non scattare. Per produzione: sempre preferire watchdog hardware quando disponibile. Verifica: `cat /proc/sys/kernel/printk_devkmsg` e `dmesg | grep -i watchdog`. Configurazione default Proxmox: `softdog` se hardware non rilevato. Cambiare a hardware: `/etc/default/pve-ha-manager` con `WATCHDOG_MODULE=iTCO_wdt`. Fonte: [Proxmox VE Admin Guide — High Availability](https://pve.proxmox.com/pve-docs/chapter-ha-manager.html), retrieved 2026-04-27.

> **Approfondimento — `pmxcfs` interno: pmxcfs e un FUSE filesystem distribuito.** `/etc/pve` e un filesystem in user-space (`pmxcfs`) che usa corosync per replicare le scritture in modo atomico tra tutti i nodi del cluster. Implementazione: ogni scrittura passa per `corosync` che usa Totem protocol (ring) per ordering totale; un nodo solo (il `cfs-leader`) conferma il commit. Quando il quorum si perde, il filesystem diventa read-only per evitare divergenze. Cache locale: ogni nodo ha una copia in memoria (`/var/lib/pve-cluster/config.db`) sincronizzata via corosync. Recovery dopo quorum loss: appena il quorum si ripristina, `pmxcfs` ri-sincronizza dal nodo con il commit piu recente (basato su lamport clock). Quindi: anche dopo split-brain, c'e una "verita" canonica purche il fencing sia configurato (chi era isolato si auto-elimina, le sue scritture mai committed sono perse). Fonte: [pve-cluster source — pmxcfs](https://git.proxmox.com/?p=pve-cluster.git;a=summary), retrieved 2026-04-27.

> **Approfondimento — Tempi di failover precisi.** Sequenza con valori default Proxmox 8.x: T0 = nodo perde rete; T0+10s = corosync token timeout (default 10000ms); T0+15s = pmxcfs declares quorum lost; T0+30s = LRM dei nodi survival decide il nodo target via CRM; T0+60s = watchdog del nodo isolato scade (softdog default 60s, modificabile); T0+62-65s = il nodo isolato reboot via watchdog; T0+65s = CRM marca formalmente il nodo come fenced (passa in stato `fenced`); T0+70s = LRM target esegue `qm start` per la VM migrata; T0+90-120s = VM completamente up (boot Linux/Windows). Tempo totale: 90-120s tipico, 60-180s window. Per ridurre: `corosync_token = 5000` (rischio: piu falsi positivi) e watchdog timeout = 30s (richiede hardware veloce). Fonte: [Proxmox VE pve-ha-manager source](https://git.proxmox.com/?p=pve-ha-manager.git;a=summary), retrieved 2026-04-27.

> **Errore comune — `qm stop` su VM HA-managed.** Sintomo: spegni una VM con `qm stop 100` e dopo 30 secondi e di nuovo accesa. Causa: l'HA Manager ha rilevato che lo state desiderato e `started`, e ha eseguito automaticamente `qm start 100`. Soluzione: per fermare davvero una VM HA-managed, usare `ha-manager set vm:100 --state stopped` (HA la mantiene ferma) oppure `ha-manager set vm:100 --state disabled` (rimossa temporaneamente dal pool, no auto-start). Per rimuoverla definitivamente: `ha-manager remove vm:100` poi `qm stop 100`. Soluzione preventiva: documentare nel runbook che le VM HA-managed hanno un workflow diverso. Fonte: [Proxmox HA Manager man page](https://pve.proxmox.com/pve-docs/ha-manager.1.html), retrieved 2026-04-27.

> **Errore comune — Cluster a 2 nodi senza qdevice.** Sintomo: il cluster funziona, ma quando un nodo cade, l'altro perde quorum (1 < 2/2 + 1 = 2) e diventa read-only — peggiorando la situazione invece di migliorarla. Causa: corosync richiede majority (n/2 + 1); con 2 nodi serve quorum di 2 → un singolo failure rompe tutto. Soluzione: aggiungere un **qdevice** esterno (`corosync-qdevice`) — tipicamente un Raspberry Pi, una piccola VM o un servizio cloud con poca latenza che ospita `corosync-qnetd`. Il qdevice fornisce 1 voto extra: 2 nodi + qdevice = 3 voti, quorum = 2, sopravvive a 1 failure. Configurazione: `pvecm qdevice setup <qnetd-ip>`. Verifica: `pvecm status` deve mostrare `Total votes: 3`. Soluzione preventiva: per produzione HA, sempre cluster ≥ 3 nodi; cluster 2-nodi e accettabile solo per dev/lab e sempre con qdevice. Fonte: [Proxmox VE Wiki — Cluster Manager (Qdevice)](https://pve.proxmox.com/wiki/Cluster_Manager#_corosync_external_vote_support), retrieved 2026-04-27.

> **Errore comune — `restricted=0` in produzione con storage non condiviso.** Sintomo: una VM con disco su `local-lvm` (storage *non* replicato) viene aggiunta a HA con un gruppo `restricted=0`; al failover, il CRM la migra su un altro nodo che non ha quel disco → la VM non parte, errore "no such volume". Causa: `restricted=0` permette failover su qualsiasi nodo, anche fuori dal gruppo. Storage local non e accessibile da tutti i nodi. Soluzione: o (a) usare storage condiviso (Ceph, NFS, iSCSI shared LVM) per VM HA-managed; o (b) `restricted=1` per limitare il failover ai nodi che hanno il volume locale (utile con `pve-zsync` replicato). Per ZFS replicated: configurare replication policy + gruppo restricted ai nodi target della replica. Fonte: [Proxmox VE Admin Guide — HA: Storage Considerations](https://pve.proxmox.com/pve-docs/chapter-ha-manager.html#ha_manager_groups), retrieved 2026-04-27.

> **Caso reale — Recovery da split-brain post-disastro di rete.** Cluster a 4 nodi (pve1-pve4) ha sperimentato un guasto allo switch core: pve1+pve2 hanno perso comunicazione con pve3+pve4. Ogni "isola" aveva 2 voti su 4 → nessuna ha quorum. *Tutte* le scritture su `/etc/pve` bloccate. Tutti i `pve-ha-lrm` in idle (non possono confermare lo stato delle proprie risorse). Le VM continuavano a girare ma nessuna nuova operazione era possibile. Recovery: (1) ripristinato lo switch; (2) corosync auto-rejoined; (3) quorum recuperato (4/4 voti); (4) `pmxcfs` rejoined automaticamente; (5) verificato `pvecm status` = "Quorate"; (6) `ha-manager status` mostrava VM tutte in stato consistente; (7) nessuna VM ha richiesto restart. Lezione: il design "fail-safe" di pmxcfs (read-only su quorum loss) ha evitato corruzione, e il sistema si e auto-riparato senza intervento manuale. Se il guasto fosse durato piu di 60s con watchdog attivo, alcuni nodi sarebbero stati fenced — anche quello richiede solo un reboot e rejoin. Fonte: case study interno, riferimento metodologico [Proxmox VE Wiki — Recover Cluster](https://pve.proxmox.com/wiki/Cluster_Manager#_recovery), retrieved 2026-04-27.

> **Caso reale — Anti-affinity tra VM critiche via gruppi separati.** Requisito: due VM database PostgreSQL primary+replica devono *mai* girare sullo stesso nodo (per garantire HA del DB). Proxmox non ha "anti-affinity rules" come vSphere DRS. Soluzione: creare due gruppi HA. Gruppo `db-primary` con `nodes=pve1:3,pve2:2,pve3:1` (preferenza pve1). Gruppo `db-replica` con `nodes=pve3:3,pve2:2,pve1:1` (preferenza pve3, opposta). In condizioni normali: primary su pve1, replica su pve3. In caso di failover di pve1: primary va su pve2 (priorita 2), replica resta su pve3 → ancora separati. In caso di doppio failover (pve1 + pve3 simultaneo, raro): entrambe finiscono su pve2 — accettabile come degraded mode temporaneo. Limite: questa tecnica funziona per coppie; per cluster di 3+ DB con anti-affinity totale serve scripting custom o accettare la limitazione. Fonte: pattern community Proxmox, [Proxmox forum thread — Anti-affinity](https://forum.proxmox.com/threads/anti-affinity-rules.95641/), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — quorum e watchdog.** Su un cluster a 5 nodi, qual e il quorum minimo? Quanti nodi possono cadere simultaneamente preservando l'HA? Cosa succede se cadono 3 nodi su 5 contemporaneamente (descrizione step-by-step della reazione di corosync, pmxcfs, watchdog, e CRM)? Argomenta in 12-15 righe.

2. **Lab — failover end-to-end timed.** Su un cluster di test a 3 nodi (puo essere nested in 3 VM), creare una VM HA-managed (state=started, gruppo con tutti i nodi). Misurare il tempo di failover spegnendo bruscamente un nodo (stop forzato della VM ospite, equivalente a power loss): (a) tempo da T0 (failure) a T1 (CRM rileva il nodo fenced) = ? secondi; (b) tempo da T1 a T2 (LRM target inizia qm start) = ? secondi; (c) tempo da T2 a T3 (VM completamente up, ping risponde) = ? secondi. Confrontare con i numeri attesi del modulo. Se discrepanza > 30%, identificare la causa.

3. **Scenario — dimensionamento HA.** Hai un cluster a 4 nodi pve1-pve4, ognuno con 64 GB RAM. Devi ospitare 30 VM con allocazione totale di 192 GB RAM (media 6.4 GB/VM, distribuite uniformemente). Argomenta: (a) Quanti nodi possono cadere simultaneamente garantendo che le VM rimaste possano girare senza overcommit? (b) Come configurare i gruppi HA per garantire che dopo un singolo failure, il carico si distribuisca equamente sui 3 nodi survivors invece di concentrarsi su uno solo? (c) Quale capacita di riserva (% di RAM idle) e necessaria? Risposta attesa: con 4 nodi e 192 GB allocati, la riserva e 192/(4-1)=64 GB/nodo necessari → con 64 GB/nodo *non* c'e margine, serve scendere a 144 GB allocati totali (48 GB/nodo) per sopravvivere a 1 failure. Per distribuire post-failover: priorita asimmetriche per gruppo, es. VM1-10 priorita pve1>pve2>pve3>pve4, VM11-20 pve2>pve3>pve4>pve1, ecc.

4. **Lab — qdevice setup su Raspberry Pi.** Su un cluster a 2 nodi (lab), aggiungere un qdevice (puo essere una VM Debian/Ubuntu o un Raspberry Pi nello stesso network): (a) installare `corosync-qnetd` sul qdevice, abilitare il servizio; (b) `pvecm qdevice setup <qnetd-ip>` su uno dei nodi cluster; (c) verificare `pvecm status` mostra `Total votes: 3`; (d) testare: spegnere un nodo del cluster e verificare che l'altro mantenga quorum (2 voti = qdevice + 1 nodo). Senza qdevice, il singolo nodo perderebbe quorum.

5. **Stretch — anti-affinity script.** Scrivere uno script Perl/Python che gira come hookscript Proxmox (`/var/lib/vz/snippets/anti-affinity.pl`) e che, al `pre-start` di una VM, verifica che la sua "VM partner" (definita in un file di configurazione) non stia girando sullo stesso nodo; se si, il hookscript deve abortire l'avvio (exit non-zero) per forzare l'HA a scegliere un altro nodo. Bonus: integrare con `ha-manager` per registrare la decisione e re-tentare automaticamente.

6. **Stretch — runbook split-brain recovery.** Documentare in 2-3 pagine A4 un runbook operativo per scenari di split-brain: (a) checklist diagnostica iniziale (`pvecm status`, `corosync-cfgtool -s`, `journalctl -u corosync`, `journalctl -u pve-cluster`); (b) decision tree: rete ripristinabile? watchdog ha fenced i nodi isolati? c'e un partition con quorum?; (c) procedure di recovery: rejoin automatico (preferito), `pvecm e <expected_votes>` per forzare quorum (rischioso, da usare solo in scenari controllati), reinstallazione di un nodo come ultima risorsa; (d) verifiche post-recovery: integrita di `/etc/pve`, stato HA di tutte le risorse, replica filesystem completata.

## Auto-valutazione

1. Differenza fra CRM e LRM in Proxmox HA. Quanti CRM master ci sono in un cluster di 5 nodi?
2. Cosa fa il watchdog se il nodo perde quorum e perche e essenziale per HA?
3. `softdog` vs watchdog hardware: in quale scenario softdog puo fallire?
4. Comando per disattivare temporaneamente HA su una VM senza rimuoverla dal pool.
5. Cosa succede se eseguo `qm stop 100` su una VM HA-managed con state=started?
6. Differenza pratica fra `restricted=0` e `restricted=1` in un gruppo HA.
7. Cosa significa `nofailback=1` e quando lo si usa?
8. `pvecm status` mostra `Quorate: No`: posso modificare `/etc/pve/qemu-server/100.conf`? Perche?
9. Calcolare il quorum minimo per cluster a 4, 5, 7 nodi.
10. Cluster a 2 nodi: come si fa HA in produzione? Cosa fa il qdevice?
11. `ha-manager add vm:100 --max_restart 0`: cosa significa praticamente?
12. Differenza tra `state=stopped` e `state=disabled` per una risorsa HA.
13. Sequenza temporale tipica di un failover: tempo per corosync timeout, watchdog expire, CRM decision, LRM start, VM up.

## Letture primarie consigliate

- Proxmox VE Admin Guide — High Availability. https://pve.proxmox.com/pve-docs/chapter-ha-manager.html (retrieved 2026-04-27).
- Proxmox VE Admin Guide — Cluster Manager. https://pve.proxmox.com/pve-docs/chapter-pvecm.html (retrieved 2026-04-27).
- Proxmox VE Wiki — Cluster Manager / qdevice. https://pve.proxmox.com/wiki/Cluster_Manager (retrieved 2026-04-27).
- Proxmox VE Wiki — High Availability. https://pve.proxmox.com/wiki/High_Availability_Cluster (retrieved 2026-04-27).
- ha-manager(1) man page. https://pve.proxmox.com/pve-docs/ha-manager.1.html (retrieved 2026-04-27).
- Proxmox VE source — pve-ha-manager (perl). https://git.proxmox.com/?p=pve-ha-manager.git;a=summary (retrieved 2026-04-27).
- Proxmox VE source — pve-cluster (pmxcfs). https://git.proxmox.com/?p=pve-cluster.git;a=summary (retrieved 2026-04-27).
- Corosync Cluster Engine — official documentation. https://corosync.github.io/corosync/ (retrieved 2026-04-27).
- Linux watchdog API — kernel documentation. https://www.kernel.org/doc/html/latest/watchdog/watchdog-api.html (retrieved 2026-04-27).
- VMware Docs — vSphere HA (per confronto). https://docs.vmware.com/en/VMware-vSphere/8.0/com.vmware.vsphere.avail.doc/GUID-5432CA24-14F1-44E3-87FB-61D937831CF6.html (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 02 — `../02-FONDAMENTI-PROXMOX-VE/architettura-installazione-proxmox.md`: introduzione a corosync, pmxcfs, cluster basics.
- Modulo 10.2 — `live-migration-proxmox-interna.md`: live-migration come operazione coordinata da HA.
- Modulo 10.3 — `fencing-e-stonith.md`: fencing prerequisito per HA sicuro.
- Modulo 10.4 — `bilanciamento-carico-vm.md`: distribuzione del carico, anti-affinity, gruppi.
- Modulo 11.x — `../11-BACKUP-E-RIPRISTINO-PROXMOX/proxmox-backup-server-configurazione.md`: PBS schedulato per VM HA-managed.
- Modulo 13.x — `../13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md`: alert su stato HA (quorum, fenced node, error state risorse).
- Modulo 17.x — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-cluster-proxmox.md`: scenari di troubleshooting HA/cluster.

## Glossario locale

| Termine | Definizione |
|---|---|
| **HA Manager** | Componente Proxmox che monitora e ri-avvia risorse su failover. |
| **CRM (Cluster Resource Manager)** | Decisore HA centrale; eletto come master, uno solo per cluster. |
| **LRM (Local Resource Manager)** | Esecutore HA locale; uno per nodo, esegue ordini del CRM. |
| **`pmxcfs`** | Cluster filesystem Proxmox in `/etc/pve`; sincronizzato via corosync. |
| **corosync** | Cluster communication engine; gestisce membership e quorum. |
| **Quorum** | Maggioranza richiesta per decisioni cluster (n/2 + 1). |
| **Watchdog** | Timer hardware o software che reset il nodo se non riceve "kick" periodico. |
| **`softdog`** | Implementazione software del watchdog (kernel module). |
| **iTCO_wdt** | Watchdog hardware Intel (TCO). |
| **Fencing** | Isolamento certo di un nodo malfunzionante (via watchdog auto-induct, o STONITH). |
| **STONITH** | Shoot The Other Node In The Head; metodologia di fencing forzato. |
| **Split-brain** | Situazione dove due "isole" di un cluster credono entrambe di avere autorita. |
| **qdevice** | Voto esterno per cluster a 2 nodi (corosync-qnetd). |
| **Risorsa HA** | VM o container gestito da HA Manager (`vm:100`, `ct:200`). |
| **Gruppo HA** | Insieme di nodi target preferiti per una risorsa. |
| **`restricted`** | Vincolo: 1=solo gruppo, 0=preferenza gruppo. |
| **`nofailback`** | Sticky: 1=non torna a priorita superiore, 0=ribilancia automaticamente. |
| **`max_restart`** | Numero massimo di tentativi di restart prima di passare a stato `error`. |
| **`max_relocate`** | Numero massimo di tentativi di failover su nodi diversi. |
| **`state=started`** | HA mantiene la risorsa running. |
| **`state=stopped`** | HA mantiene la risorsa ferma. |
| **`state=disabled`** | Risorsa rimossa temporaneamente dal pool HA. |
| **`state=ignored`** | Placeholder; HA non interviene. |
| **`state=error`** | Risorsa in stato di errore; richiede intervento manuale. |
| **DRS (vSphere)** | Distributed Resource Scheduler; bilanciamento dinamico carico (assente in Proxmox). |
| **VMCP (vSphere)** | VM Component Protection; reset VM su PDL/APD storage (assente in Proxmox). |
| **Lock pmxcfs** | Lock distribuito usato per eleggere CRM master. |
